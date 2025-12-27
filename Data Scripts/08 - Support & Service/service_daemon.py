#!/usr/bin/env python3
"""
GenIMS Customer Service Daemon
Continuous customer service operations
"""

import sys
import time
import logging
import signal
from datetime import datetime, timedelta
import random
import json

try:
    import psycopg2
    from psycopg2.extras import execute_batch
    POSTGRES_AVAILABLE = True
except ImportError:
    POSTGRES_AVAILABLE = False
    print("WARNING: psycopg2 not installed")

# Configuration
PG_HOST = 'localhost'
PG_PORT = 5432
PG_DATABASE = 'genims_db'
PG_USER = 'genims_user'
PG_PASSWORD = 'genims_password'

# Service Configuration
CYCLE_INTERVAL_SECONDS = 1800  # Run every 30 minutes

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/service_daemon.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('ServiceDaemon')

running = True
pg_connection = None
master_data = {}
stats = {
    'cycles': 0,
    'tickets_routed': 0,
    'tickets_escalated': 0,
    'sla_violations_detected': 0,
    'field_appointments_assigned': 0,
    'surveys_sent': 0,
    'warranties_processed': 0,
    'start_time': datetime.now()
}

def signal_handler(sig, frame):
    global running
    logger.info("Shutdown signal received")
    running = False

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

def initialize_database():
    global pg_connection
    if not POSTGRES_AVAILABLE:
        return False
    try:
        pg_connection = psycopg2.connect(
            host=PG_HOST, port=PG_PORT, database=PG_DATABASE,
            user=PG_USER, password=PG_PASSWORD
        )
        pg_connection.autocommit = False
        logger.info("PostgreSQL connected")
        return True
    except Exception as e:
        logger.error(f"DB connection failed: {e}")
        return False

def load_master_data():
    global master_data
    try:
        cursor = pg_connection.cursor()
        
        # Load service agents
        cursor.execute("SELECT * FROM service_agents WHERE is_active = true LIMIT 50")
        master_data['service_agents'] = [dict(zip([d[0] for d in cursor.description], row)) 
                                         for row in cursor.fetchall()]
        
        # Load field technicians
        cursor.execute("SELECT * FROM field_technicians WHERE is_active = true")
        master_data['field_technicians'] = [dict(zip([d[0] for d in cursor.description], row)) 
                                            for row in cursor.fetchall()]
        
        # Load SLA definitions
        cursor.execute("SELECT * FROM sla_definitions WHERE is_active = true")
        master_data['sla_definitions'] = [dict(zip([d[0] for d in cursor.description], row)) 
                                          for row in cursor.fetchall()]
        
        cursor.close()
        logger.info(f"Loaded: {len(master_data.get('service_agents', []))} agents, "
                   f"{len(master_data.get('field_technicians', []))} technicians")
        return True
    except Exception as e:
        logger.error(f"Failed to load master data: {e}")
        return False

def generate_id(prefix: str) -> str:
    return f"{prefix}-{datetime.now().strftime('%Y%m%d%H%M%S')}-{random.randint(1000, 9999)}"

# ============================================================================
# TICKET ROUTING & ASSIGNMENT
# ============================================================================

def route_new_tickets():
    """Route unassigned tickets to agents"""
    logger.info("Routing new tickets...")
    
    if not master_data.get('service_agents'):
        return
    
    try:
        cursor = pg_connection.cursor()
        
        # Get new unassigned tickets
        cursor.execute("""
            SELECT ticket_id, priority, category
            FROM service_tickets
            WHERE ticket_status = 'new'
            AND assigned_to IS NULL
            LIMIT 20
        """)
        
        tickets = cursor.fetchall()
        
        for ticket_id, priority, category in tickets:
            # Simple round-robin assignment to available agents
            available_agents = [a for a in master_data['service_agents'] 
                               if a.get('agent_status') == 'available']
            
            if available_agents:
                agent = random.choice(available_agents)
                
                cursor.execute("""
                    UPDATE service_tickets
                    SET assigned_to = %s,
                        assigned_datetime = %s,
                        ticket_status = 'assigned'
                    WHERE ticket_id = %s
                """, (agent['agent_id'], datetime.now(), ticket_id))
                
                stats['tickets_routed'] += 1
        
        pg_connection.commit()
        cursor.close()
        
        if tickets:
            logger.info(f"Routed {len(tickets)} tickets")
    except Exception as e:
        logger.error(f"Error routing tickets: {e}")
        pg_connection.rollback()

# ============================================================================
# SLA MONITORING
# ============================================================================

def monitor_sla_violations():
    """Monitor and flag SLA violations"""
    logger.info("Monitoring SLA violations...")
    
    try:
        cursor = pg_connection.cursor()
        
        # Check response SLA
        cursor.execute("""
            UPDATE service_tickets
            SET response_sla_breached = true
            WHERE ticket_status IN ('new', 'assigned')
            AND response_due_datetime < %s
            AND first_response_datetime IS NULL
            AND response_sla_breached = false
        """, (datetime.now(),))
        
        response_breaches = cursor.rowcount
        
        # Check resolution SLA
        cursor.execute("""
            UPDATE service_tickets
            SET resolution_sla_breached = true
            WHERE ticket_status NOT IN ('resolved', 'closed')
            AND resolution_due_datetime < %s
            AND resolved_datetime IS NULL
            AND resolution_sla_breached = false
        """, (datetime.now(),))
        
        resolution_breaches = cursor.rowcount
        
        stats['sla_violations_detected'] += (response_breaches + resolution_breaches)
        
        pg_connection.commit()
        cursor.close()
        
        if response_breaches + resolution_breaches > 0:
            logger.info(f"Detected {response_breaches + resolution_breaches} SLA violations")
    except Exception as e:
        logger.error(f"Error monitoring SLA: {e}")
        pg_connection.rollback()

# ============================================================================
# ESCALATION MANAGEMENT
# ============================================================================

def escalate_tickets():
    """Escalate tickets based on SLA breach or age"""
    logger.info("Checking for tickets to escalate...")
    
    try:
        cursor = pg_connection.cursor()
        
        # Escalate tickets with SLA violations
        cursor.execute("""
            SELECT ticket_id, escalation_level
            FROM service_tickets
            WHERE (response_sla_breached = true OR resolution_sla_breached = true)
            AND ticket_status NOT IN ('resolved', 'closed')
            AND escalation_level < 3
            LIMIT 10
        """)
        
        tickets = cursor.fetchall()
        
        for ticket_id, current_level in tickets:
            new_level = current_level + 1
            
            # Update ticket escalation
            cursor.execute("""
                UPDATE service_tickets
                SET escalation_level = %s,
                    escalated_datetime = %s
                WHERE ticket_id = %s
            """, (new_level, datetime.now(), ticket_id))
            
            # Log escalation
            cursor.execute("""
                INSERT INTO ticket_escalations (
                    escalation_id, ticket_id, escalation_level,
                    escalation_reason, escalated_at
                ) VALUES (%s, %s, %s, %s, %s)
            """, (generate_id('ESC'), ticket_id, new_level,
                  'SLA breach detected', datetime.now()))
            
            stats['tickets_escalated'] += 1
        
        pg_connection.commit()
        cursor.close()
        
        if tickets:
            logger.info(f"Escalated {len(tickets)} tickets")
    except Exception as e:
        logger.error(f"Error escalating tickets: {e}")
        pg_connection.rollback()

# ============================================================================
# FIELD SERVICE MANAGEMENT
# ============================================================================

def assign_field_appointments():
    """Assign field service appointments to technicians"""
    logger.info("Assigning field appointments...")
    
    if not master_data.get('field_technicians'):
        return
    
    try:
        cursor = pg_connection.cursor()
        
        # Get unassigned appointments
        cursor.execute("""
            SELECT appointment_id, service_type, appointment_date
            FROM field_service_appointments
            WHERE appointment_status = 'scheduled'
            AND assigned_technician_id IS NULL
            AND appointment_date >= %s
            LIMIT 10
        """, (datetime.now().date(),))
        
        appointments = cursor.fetchall()
        
        for appt_id, service_type, appt_date in appointments:
            # Assign to available technician
            available_techs = [t for t in master_data['field_technicians'] 
                              if t.get('technician_status') == 'available']
            
            if available_techs:
                tech = random.choice(available_techs)
                
                cursor.execute("""
                    UPDATE field_service_appointments
                    SET assigned_technician_id = %s,
                        appointment_status = 'confirmed'
                    WHERE appointment_id = %s
                """, (tech['technician_id'], appt_id))
                
                stats['field_appointments_assigned'] += 1
        
        pg_connection.commit()
        cursor.close()
        
        if appointments:
            logger.info(f"Assigned {len(appointments)} field appointments")
    except Exception as e:
        logger.error(f"Error assigning appointments: {e}")
        pg_connection.rollback()

def complete_field_appointments():
    """Complete in-progress field appointments"""
    logger.info("Completing field appointments...")
    
    try:
        cursor = pg_connection.cursor()
        
        # Complete appointments that should be done
        cursor.execute("""
            UPDATE field_service_appointments
            SET appointment_status = 'completed',
                checked_out_datetime = %s
            WHERE appointment_status = 'in_progress'
            AND checked_in_datetime < %s
            LIMIT 5
        """, (datetime.now(), datetime.now() - timedelta(hours=4)))
        
        pg_connection.commit()
        cursor.close()
    except Exception as e:
        logger.error(f"Error completing appointments: {e}")
        pg_connection.rollback()

# ============================================================================
# WARRANTY & RMA PROCESSING
# ============================================================================

def process_warranty_claims():
    """Process pending warranty claims"""
    logger.info("Processing warranty claims...")
    
    try:
        cursor = pg_connection.cursor()
        
        # Auto-approve claims under certain amount
        cursor.execute("""
            UPDATE warranty_claims
            SET claim_status = 'approved',
                approved = true,
                approved_date = %s
            WHERE claim_status = 'submitted'
            AND total_claim_amount < 10000
            LIMIT 5
        """, (datetime.now().date(),))
        
        rows = cursor.rowcount
        stats['warranties_processed'] += rows
        
        pg_connection.commit()
        cursor.close()
        
        if rows > 0:
            logger.info(f"Processed {rows} warranty claims")
    except Exception as e:
        logger.error(f"Error processing warranties: {e}")
        pg_connection.rollback()

def process_rma_inspections():
    """Process RMA inspections"""
    logger.info("Processing RMA inspections...")
    
    try:
        cursor = pg_connection.cursor()
        
        # Complete inspections for received RMAs
        cursor.execute("""
            UPDATE rma_requests
            SET rma_status = 'processing',
                inspection_status = 'pass',
                condition_on_receipt = 'good'
            WHERE rma_status = 'received'
            AND inspection_status IS NULL
            LIMIT 5
        """)
        
        pg_connection.commit()
        cursor.close()
    except Exception as e:
        logger.error(f"Error processing RMAs: {e}")
        pg_connection.rollback()

# ============================================================================
# CUSTOMER SATISFACTION
# ============================================================================

def send_csat_surveys():
    """Send CSAT surveys for closed tickets"""
    logger.info("Sending CSAT surveys...")
    
    try:
        cursor = pg_connection.cursor()
        
        # Check if surveys table exists
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'customer_surveys'
            )
        """)
        
        if not cursor.fetchone()[0]:
            cursor.close()
            return
        
        # Get recently closed tickets without surveys
        cursor.execute("""
            SELECT ticket_id, account_id, contact_id
            FROM service_tickets
            WHERE ticket_status = 'closed'
            AND csat_survey_sent = false
            AND closed_datetime >= %s
            LIMIT 10
        """, (datetime.now() - timedelta(days=7),))
        
        tickets = cursor.fetchall()
        
        for ticket_id, account_id, contact_id in tickets:
            # Mark survey as sent
            cursor.execute("""
                UPDATE service_tickets
                SET csat_survey_sent = true,
                    csat_survey_sent_datetime = %s
                WHERE ticket_id = %s
            """, (datetime.now(), ticket_id))
            
            stats['surveys_sent'] += 1
        
        pg_connection.commit()
        cursor.close()
        
        if tickets:
            logger.info(f"Sent {len(tickets)} CSAT surveys")
    except Exception as e:
        logger.error(f"Error sending surveys: {e}")
        pg_connection.rollback()

# ============================================================================
# KNOWLEDGE BASE UPDATES
# ============================================================================

def update_kb_metrics():
    """Update knowledge base article metrics"""
    logger.info("Updating KB metrics...")
    
    try:
        cursor = pg_connection.cursor()
        
        # Update avg ratings from recent ratings
        cursor.execute("""
            UPDATE kb_articles ka
            SET avg_rating = (
                SELECT AVG(rating)
                FROM kb_article_ratings
                WHERE article_id = ka.article_id
            )
            WHERE article_status = 'published'
        """)
        
        pg_connection.commit()
        cursor.close()
    except Exception as e:
        logger.error(f"Error updating KB metrics: {e}")
        pg_connection.rollback()

# ============================================================================
# SERVICE ANALYTICS
# ============================================================================

def generate_daily_metrics():
    """Generate daily service metrics"""
    logger.info("Generating daily metrics...")
    
    try:
        cursor = pg_connection.cursor()
        
        today = datetime.now().date()
        
        # Check if metrics already exist for today
        cursor.execute("""
            SELECT EXISTS (
                SELECT 1 FROM service_metrics_daily WHERE metric_date = %s
            )
        """, (today,))
        
        if cursor.fetchone()[0]:
            cursor.close()
            return
        
        # Calculate today's metrics
        cursor.execute("""
            INSERT INTO service_metrics_daily (
                metric_id, metric_date,
                tickets_created, tickets_resolved, tickets_closed,
                backlog_count,
                avg_first_response_time_minutes,
                avg_resolution_time_minutes,
                created_at
            )
            SELECT
                %s,
                %s,
                COUNT(CASE WHEN DATE(created_at) = %s THEN 1 END),
                COUNT(CASE WHEN DATE(resolved_datetime) = %s THEN 1 END),
                COUNT(CASE WHEN DATE(closed_datetime) = %s THEN 1 END),
                COUNT(CASE WHEN ticket_status NOT IN ('resolved', 'closed') THEN 1 END),
                AVG(first_response_time_minutes),
                AVG(resolution_time_minutes),
                %s
            FROM service_tickets
        """, (generate_id('MET'), today, today, today, today, datetime.now()))
        
        pg_connection.commit()
        cursor.close()
        
        logger.info(f"Generated metrics for {today}")
    except Exception as e:
        logger.error(f"Error generating metrics: {e}")
        pg_connection.rollback()

# ============================================================================
# INTEGRATION
# ============================================================================

def sync_with_crm():
    """Sync tickets with CRM cases"""
    logger.info("Syncing with CRM...")
    
    try:
        cursor = pg_connection.cursor()
        
        # Check if cases table exists (CRM)
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'cases'
            )
        """)
        
        if not cursor.fetchone()[0]:
            cursor.close()
            return
        
        # Sync high priority tickets to CRM cases
        cursor.execute("""
            SELECT ticket_id, account_id, subject, priority
            FROM service_tickets
            WHERE priority IN ('critical', 'urgent')
            AND ticket_status = 'new'
            AND NOT EXISTS (
                SELECT 1 FROM cases WHERE ticket_id = service_tickets.ticket_id
            )
            LIMIT 5
        """)
        
        tickets = cursor.fetchall()
        
        for ticket_id, account_id, subject, priority in tickets:
            # Create CRM case
            case_id = generate_id('CASE')
            cursor.execute("""
                INSERT INTO cases (
                    case_id, case_number, account_id,
                    subject, description, case_type, priority,
                    case_status, created_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (case_id, f"CASE-{case_id}", account_id,
                  subject, f"From ticket: {ticket_id}",
                  'problem', priority, 'new', datetime.now()))
            
            # Log integration
            cursor.execute("""
                INSERT INTO service_integration_log (
                    log_id, integration_direction, document_type,
                    document_id, integration_status, log_timestamp
                ) VALUES (%s, %s, %s, %s, %s, %s)
            """, (generate_id('INTLOG'), 'SERVICE_TO_CRM',
                  'ticket', ticket_id, 'completed', datetime.now()))
        
        pg_connection.commit()
        cursor.close()
        
        if tickets:
            logger.info(f"Synced {len(tickets)} tickets to CRM")
    except Exception as e:
        logger.error(f"Error syncing with CRM: {e}")
        pg_connection.rollback()

# ============================================================================
# MAIN CYCLE
# ============================================================================

def run_service_cycle():
    """Execute complete service cycle"""
    logger.info("=== Service Cycle Starting ===")
    
    try:
        # 1. Ticket Management
        route_new_tickets()
        monitor_sla_violations()
        escalate_tickets()
        
        # 2. Field Service
        assign_field_appointments()
        complete_field_appointments()
        
        # 3. Warranty & RMA
        process_warranty_claims()
        process_rma_inspections()
        
        # 4. Customer Satisfaction
        send_csat_surveys()
        
        # 5. Knowledge Base
        update_kb_metrics()
        
        # 6. Analytics
        generate_daily_metrics()
        
        # 7. Integration
        sync_with_crm()
        
        stats['cycles'] += 1
        logger.info("=== Service Cycle Complete ===")
        return True
    except Exception as e:
        logger.error(f"Service cycle error: {e}")
        return False

def print_stats():
    """Print daemon statistics"""
    elapsed = (datetime.now() - stats['start_time']).total_seconds()
    hours = elapsed / 3600
    
    logger.info("="*80)
    logger.info(f"Service Daemon Statistics")
    logger.info(f"  Uptime: {hours:.1f} hours")
    logger.info(f"  Cycles: {stats['cycles']}")
    logger.info(f"  Tickets Routed: {stats['tickets_routed']}")
    logger.info(f"  Tickets Escalated: {stats['tickets_escalated']}")
    logger.info(f"  SLA Violations Detected: {stats['sla_violations_detected']}")
    logger.info(f"  Field Appointments Assigned: {stats['field_appointments_assigned']}")
    logger.info(f"  Surveys Sent: {stats['surveys_sent']}")
    logger.info(f"  Warranties Processed: {stats['warranties_processed']}")
    logger.info("="*80)

def main():
    """Main daemon loop"""
    logger.info("="*80)
    logger.info("GenIMS Customer Service Daemon Starting")
    logger.info("Cycle Interval: Every 30 minutes")
    logger.info("="*80)
    
    if not initialize_database():
        return 1
    
    if not load_master_data():
        return 1
    
    logger.info("Press Ctrl+C to stop")
    
    last_cycle = datetime.now() - timedelta(hours=1)
    
    while running:
        try:
            now = datetime.now()
            
            # Run every 30 minutes
            if (now - last_cycle).total_seconds() >= CYCLE_INTERVAL_SECONDS:
                run_service_cycle()
                last_cycle = now
            
            # Print stats every hour
            if now.minute == 0:
                print_stats()
            
            time.sleep(60)  # Check every minute
            
        except Exception as e:
            logger.error(f"Error in main loop: {e}", exc_info=True)
            time.sleep(60)
    
    logger.info("Shutting down...")
    if pg_connection:
        pg_connection.close()
    
    print_stats()
    logger.info("Service Daemon stopped")
    return 0

if __name__ == "__main__":
    import os
    os.makedirs('logs', exist_ok=True)
    sys.exit(main())
