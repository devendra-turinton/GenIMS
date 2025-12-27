#!/usr/bin/env python3
"""
GenIMS Quality Management System (QMS) Daemon
Handles automated QMS operations: calibration alerts, CAPA monitoring,
SPC tracking, NCR management, and quality metrics calculation
"""

import sys
import time
import logging
import signal
from datetime import datetime, timedelta
import random

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

# Daemon Configuration
CYCLE_INTERVAL_SECONDS = 300  # Run every 5 minutes

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/qms_daemon.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('QMSDaemon')

running = True
pg_connection = None
stats = {
    'cycles': 0,
    'calibration_alerts': 0,
    'capa_escalations': 0,
    'ncr_updates': 0,
    'spc_checks': 0,
    'kpi_calculations': 0,
    'mes_integrations': 0,
    'service_integrations': 0,
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

def generate_id(prefix: str) -> str:
    return f"{prefix}-{datetime.now().strftime('%Y%m%d%H%M%S')}-{random.randint(1000, 9999)}"

# ============================================================================
# CALIBRATION MANAGEMENT
# ============================================================================

def check_calibration_due():
    """Check for calibration due dates and generate alerts"""
    logger.info("Checking calibration due dates...")
    
    try:
        cursor = pg_connection.cursor()
        
        # Find equipment with calibration due in next 30 days
        cursor.execute("""
            SELECT equipment_id, equipment_number, equipment_name,
                   next_calibration_due,
                   next_calibration_due - CURRENT_DATE as days_until_due
            FROM measuring_equipment
            WHERE equipment_status = 'active'
            AND next_calibration_due <= CURRENT_DATE + INTERVAL '30 days'
            AND NOT EXISTS (
                SELECT 1 FROM calibration_alerts
                WHERE equipment_id = measuring_equipment.equipment_id
                AND alert_date = CURRENT_DATE
                AND resolved = false
            )
        """)
        
        equipment_list = cursor.fetchall()
        
        for equip_id, equip_num, equip_name, due_date, days_until in equipment_list:
            # Determine alert type
            if days_until < 0:
                alert_type = 'overdue'
                priority = 'critical'
            elif days_until <= 7:
                alert_type = 'due_7_days'
                priority = 'high'
            else:
                alert_type = 'due_30_days'
                priority = 'medium'
            
            # Create alert
            cursor.execute("""
                INSERT INTO calibration_alerts (
                    alert_id, equipment_id, alert_type,
                    alert_date, days_until_due, notification_sent,
                    resolved, created_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (generate_id('ALERT'), equip_id, alert_type,
                  datetime.now().date(), days_until, True, False, datetime.now()))
            
            # Update equipment status if overdue
            if days_until < 0:
                cursor.execute("""
                    UPDATE measuring_equipment
                    SET equipment_status = 'overdue',
                        locked_out = true,
                        lockout_reason = 'Calibration overdue'
                    WHERE equipment_id = %s
                """, (equip_id,))
            elif days_until <= 7:
                cursor.execute("""
                    UPDATE measuring_equipment
                    SET equipment_status = 'calibration_due'
                    WHERE equipment_id = %s
                """, (equip_id,))
            
            stats['calibration_alerts'] += 1
            logger.warning(f"{alert_type.upper()}: {equip_num} - {equip_name} (due: {due_date})")
        
        pg_connection.commit()
        cursor.close()
        
        if equipment_list:
            logger.info(f"Generated {len(equipment_list)} calibration alerts")
    except Exception as e:
        logger.error(f"Error checking calibration: {e}")
        pg_connection.rollback()

# ============================================================================
# CAPA MANAGEMENT
# ============================================================================

def monitor_capa_due_dates():
    """Monitor CAPA due dates and escalate overdue items"""
    logger.info("Monitoring CAPA due dates...")
    
    try:
        cursor = pg_connection.cursor()
        
        # Find overdue CAPAs
        cursor.execute("""
            SELECT capa_id, capa_number, problem_description,
                   responsible_person, target_completion_date,
                   CURRENT_DATE - target_completion_date as days_overdue
            FROM capa_headers
            WHERE capa_status IN ('open', 'in_progress')
            AND target_completion_date < CURRENT_DATE
        """)
        
        overdue_capas = cursor.fetchall()
        
        for capa_id, capa_num, description, responsible, target, days_overdue in overdue_capas:
            logger.warning(f"CAPA OVERDUE: {capa_num} - {days_overdue} days past due")
            
            # Update priority if significantly overdue
            if days_overdue > 30:
                cursor.execute("""
                    UPDATE capa_headers
                    SET problem_severity = 'critical'
                    WHERE capa_id = %s
                """, (capa_id,))
            
            stats['capa_escalations'] += 1
        
        # Check for CAPA actions past due
        cursor.execute("""
            UPDATE capa_actions
            SET action_status = 'overdue'
            WHERE due_date < CURRENT_DATE
            AND action_status IN ('pending', 'in_progress')
        """)
        
        pg_connection.commit()
        cursor.close()
        
        if overdue_capas:
            logger.info(f"Found {len(overdue_capas)} overdue CAPAs")
    except Exception as e:
        logger.error(f"Error monitoring CAPAs: {e}")
        pg_connection.rollback()

def update_ncr_from_capa():
    """Update NCR status based on linked CAPA completion"""
    logger.info("Updating NCR statuses from CAPA...")
    
    try:
        cursor = pg_connection.cursor()
        
        # Find completed CAPAs and update linked NCRs
        cursor.execute("""
            UPDATE ncr_headers
            SET ncr_status = 'closed',
                closed_date = CURRENT_DATE,
                verified_effective = true
            WHERE ncr_status = 'capa_created'
            AND EXISTS (
                SELECT 1 FROM capa_headers
                WHERE source_document_id = ncr_headers.ncr_id
                AND capa_status = 'closed'
                AND effectiveness_verified = true
            )
            RETURNING ncr_id, ncr_number
        """)
        
        updated_ncrs = cursor.fetchall()
        
        pg_connection.commit()
        cursor.close()
        
        if updated_ncrs:
            stats['ncr_updates'] += len(updated_ncrs)
            logger.info(f"Updated {len(updated_ncrs)} NCRs to closed status")
    except Exception as e:
        logger.error(f"Error updating NCRs: {e}")
        pg_connection.rollback()

# ============================================================================
# SPC MONITORING
# ============================================================================

def monitor_spc_charts():
    """Monitor SPC charts for out-of-control conditions"""
    logger.info("Monitoring SPC charts...")
    
    try:
        cursor = pg_connection.cursor()
        
        # Find charts with recent out-of-control points
        cursor.execute("""
            SELECT DISTINCT sc.chart_id, sc.chart_number, sc.process_name,
                   COUNT(*) FILTER (WHERE sd.out_of_control = true) as ooc_count
            FROM spc_control_charts sc
            JOIN spc_data_points sd ON sc.chart_id = sd.chart_id
            WHERE sd.measurement_timestamp >= CURRENT_TIMESTAMP - INTERVAL '24 hours'
            AND sc.chart_status = 'active'
            GROUP BY sc.chart_id, sc.chart_number, sc.process_name
            HAVING COUNT(*) FILTER (WHERE sd.out_of_control = true) > 0
        """)
        
        ooc_charts = cursor.fetchall()
        
        for chart_id, chart_num, process_name, ooc_count in ooc_charts:
            # Update chart status
            cursor.execute("""
                UPDATE spc_control_charts
                SET chart_status = 'out_of_control'
                WHERE chart_id = %s
            """, (chart_id,))
            
            logger.warning(f"SPC OUT OF CONTROL: {chart_num} - {process_name} ({ooc_count} points in 24h)")
            
            # Check if NCR already exists for this
            cursor.execute("""
                SELECT 1 FROM ncr_headers
                WHERE source_type = 'in_process'
                AND defect_description LIKE %s
                AND detected_date = CURRENT_DATE
            """, (f'%SPC%{chart_num}%',))
            
            if not cursor.fetchone():
                # Create NCR for persistent out-of-control
                if ooc_count >= 3:
                    ncr_id = generate_id('NCR')
                    cursor.execute("""
                        INSERT INTO ncr_headers (
                            ncr_id, ncr_number, source_type, detected_date,
                            detected_by, defect_type, defect_description,
                            defect_severity, ncr_status, priority, created_at
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, (ncr_id, f'NCR-{datetime.now().strftime("%Y%m%d")}-SPC',
                          'in_process', datetime.now().date(), 'SYSTEM',
                          'process', f'SPC out of control: {chart_num} - {process_name}',
                          'major', 'open', 'high', datetime.now()))
                    
                    logger.info(f"Created NCR for out-of-control SPC chart: {chart_num}")
            
            stats['spc_checks'] += 1
        
        pg_connection.commit()
        cursor.close()
        
        if ooc_charts:
            logger.info(f"Found {len(ooc_charts)} SPC charts out of control")
    except Exception as e:
        logger.error(f"Error monitoring SPC: {e}")
        pg_connection.rollback()

# ============================================================================
# MES INTEGRATION
# ============================================================================

def integrate_mes_quality_inspections():
    """Create NCRs from failed MES quality inspections"""
    logger.info("Integrating MES quality inspections...")
    
    try:
        cursor = pg_connection.cursor()
        
        # Find failed quality inspections without NCR
        cursor.execute("""
            SELECT qi.inspection_id, qi.work_order_id, qi.material_id,
                   qi.inspection_result, qi.defect_count, qi.defect_type,
                   qi.inspection_date
            FROM quality_inspections qi
            WHERE qi.inspection_result = 'fail'
            AND qi.defect_count > 0
            AND qi.inspection_date >= CURRENT_DATE - INTERVAL '7 days'
            AND NOT EXISTS (
                SELECT 1 FROM ncr_headers
                WHERE source_document_id = qi.inspection_id
            )
            LIMIT 10
        """)
        
        failed_inspections = cursor.fetchall()
        
        for insp_id, wo_id, material_id, result, defect_count, defect_type, insp_date in failed_inspections:
            # Create NCR
            ncr_id = generate_id('NCR')
            cursor.execute("""
                INSERT INTO ncr_headers (
                    ncr_id, ncr_number, source_type, source_document_id,
                    detected_date, detected_by, material_id,
                    quantity_defective, defect_type, defect_description,
                    defect_severity, disposition, ncr_status,
                    priority, created_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (ncr_id, f'NCR-{datetime.now().strftime("%Y%m%d")}-{self.counters.get("ncr", 1):04d}',
                  'in_process', insp_id, insp_date, 'MES_SYSTEM',
                  material_id, defect_count, defect_type or 'quality',
                  f'Failed quality inspection from MES (WO: {wo_id})',
                  'major', 'rework', 'open', 'high', datetime.now()))
            
            # Log integration
            cursor.execute("""
                INSERT INTO qms_integration_log (
                    log_id, log_timestamp, integration_type,
                    source_system, target_system,
                    source_document_id, target_document_id,
                    integration_status
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (generate_id('LOG'), datetime.now(), 'mes_inspection_to_ncr',
                  'mes', 'qms', insp_id, ncr_id, 'success'))
            
            stats['mes_integrations'] += 1
            logger.info(f"Created NCR {ncr_id} from MES inspection {insp_id}")
        
        pg_connection.commit()
        cursor.close()
        
        if failed_inspections:
            logger.info(f"Integrated {len(failed_inspections)} MES inspections")
    except Exception as e:
        logger.error(f"Error integrating MES inspections: {e}")
        pg_connection.rollback()

# ============================================================================
# CUSTOMER SERVICE INTEGRATION
# ============================================================================

def integrate_service_tickets():
    """Create customer complaints from service tickets"""
    logger.info("Integrating customer service tickets...")
    
    try:
        cursor = pg_connection.cursor()
        
        # Find quality-related service tickets without complaints
        cursor.execute("""
            SELECT st.ticket_id, st.customer_id, st.product_id,
                   st.issue_description, st.priority, st.created_at
            FROM service_tickets st
            WHERE st.ticket_type IN ('quality', 'defect', 'malfunction')
            AND st.ticket_status NOT IN ('resolved', 'closed')
            AND st.created_at >= CURRENT_TIMESTAMP - INTERVAL '30 days'
            AND NOT EXISTS (
                SELECT 1 FROM customer_complaints
                WHERE service_ticket_id = st.ticket_id
            )
            LIMIT 10
        """)
        
        quality_tickets = cursor.fetchall()
        
        for ticket_id, customer_id, product_id, description, priority, created in quality_tickets:
            # Determine severity from priority
            severity_map = {'critical': 'critical', 'high': 'major', 'medium': 'minor', 'low': 'minor'}
            severity = severity_map.get(priority, 'minor')
            
            # Create customer complaint
            complaint_id = generate_id('COMP')
            cursor.execute("""
                INSERT INTO customer_complaints (
                    complaint_id, complaint_number, service_ticket_id,
                    customer_id, product_id, complaint_date,
                    complaint_description, complaint_type,
                    severity, immediate_action, complaint_status, created_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (complaint_id, f'COMP-{datetime.now().strftime("%Y%m%d")}-{random.randint(1, 9999):04d}',
                  ticket_id, customer_id, product_id, created.date(),
                  description, 'quality', severity,
                  'Investigating issue', 'open', datetime.now()))
            
            # Log integration
            cursor.execute("""
                INSERT INTO qms_integration_log (
                    log_id, log_timestamp, integration_type,
                    source_system, target_system,
                    source_document_id, target_document_id,
                    integration_status
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (generate_id('LOG'), datetime.now(), 'ticket_to_complaint',
                  'customer_service', 'qms', ticket_id, complaint_id, 'success'))
            
            stats['service_integrations'] += 1
            logger.info(f"Created complaint {complaint_id} from ticket {ticket_id}")
        
        pg_connection.commit()
        cursor.close()
        
        if quality_tickets:
            logger.info(f"Integrated {len(quality_tickets)} service tickets")
    except Exception as e:
        logger.error(f"Error integrating service tickets: {e}")
        pg_connection.rollback()

# ============================================================================
# QUALITY KPI CALCULATION
# ============================================================================

def calculate_daily_quality_kpis():
    """Calculate daily quality KPIs"""
    logger.info("Calculating daily quality KPIs...")
    
    try:
        cursor = pg_connection.cursor()
        
        # Check if already calculated for today
        cursor.execute("""
            SELECT 1 FROM quality_kpis WHERE kpi_date = CURRENT_DATE
        """)
        
        if cursor.fetchone():
            logger.info("KPIs already calculated for today")
            return
        
        # Calculate various metrics
        
        # NCR metrics
        cursor.execute("""
            SELECT 
                COUNT(*) FILTER (WHERE detected_date = CURRENT_DATE) as opened,
                COUNT(*) FILTER (WHERE closed_date = CURRENT_DATE) as closed,
                COUNT(*) FILTER (WHERE ncr_status IN ('open', 'contained', 'capa_created')) as open_count
            FROM ncr_headers
        """)
        ncr_opened, ncr_closed, ncr_open_count = cursor.fetchone()
        
        # CAPA overdue
        cursor.execute("""
            SELECT COUNT(*) FROM capa_headers
            WHERE target_completion_date < CURRENT_DATE
            AND capa_status IN ('open', 'in_progress')
        """)
        capa_overdue = cursor.fetchone()[0]
        
        # Customer complaints today
        cursor.execute("""
            SELECT COUNT(*) FROM customer_complaints
            WHERE complaint_date = CURRENT_DATE
        """)
        customer_complaints = cursor.fetchone()[0]
        
        # Calibration status
        cursor.execute("""
            SELECT 
                COUNT(*) FILTER (WHERE equipment_status = 'active') as calibrated,
                COUNT(*) as total
            FROM measuring_equipment
        """)
        cal_active, cal_total = cursor.fetchone()
        calibrated_pct = (cal_active / cal_total * 100) if cal_total > 0 else 0
        
        cursor.execute("""
            SELECT COUNT(*) FROM measuring_equipment
            WHERE equipment_status = 'overdue'
        """)
        equipment_overdue = cursor.fetchone()[0]
        
        # SPC process control
        cursor.execute("""
            SELECT 
                COUNT(*) FILTER (WHERE chart_status = 'active') as in_control,
                COUNT(*) as total
            FROM spc_control_charts
        """)
        in_control, total_processes = cursor.fetchone()
        
        # Insert KPI record
        cursor.execute("""
            INSERT INTO quality_kpis (
                kpi_id, kpi_date,
                internal_defect_ppm, first_time_quality_pct,
                customer_complaints, customer_returns_ppm,
                incoming_rejection_pct, supplier_defect_ppm,
                processes_in_control, processes_total,
                process_capability_avg,
                ncr_opened, ncr_closed, ncr_open_count,
                capa_overdue,
                equipment_calibrated_pct, equipment_overdue,
                created_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (generate_id('KPI'), datetime.now().date(),
              random.randint(50, 500),  # Would calculate from actual data
              round(random.uniform(95, 99.5), 2),
              customer_complaints, random.randint(10, 100),
              round(random.uniform(0.5, 3), 2), random.randint(100, 1000),
              in_control or 0, total_processes or 0,
              round(random.uniform(1.2, 1.8), 3),
              ncr_opened or 0, ncr_closed or 0, ncr_open_count or 0,
              capa_overdue or 0,
              round(calibrated_pct, 2), equipment_overdue or 0,
              datetime.now()))
        
        pg_connection.commit()
        cursor.close()
        
        stats['kpi_calculations'] += 1
        logger.info("Calculated daily quality KPIs")
    except Exception as e:
        logger.error(f"Error calculating KPIs: {e}")
        pg_connection.rollback()

# ============================================================================
# DOCUMENT REVIEW ALERTS
# ============================================================================

def check_document_reviews():
    """Check for documents due for periodic review"""
    logger.info("Checking document review dates...")
    
    try:
        cursor = pg_connection.cursor()
        
        # Find documents due for review in next 30 days
        cursor.execute("""
            SELECT document_id, document_number, document_title,
                   next_review_date,
                   next_review_date - CURRENT_DATE as days_until_review
            FROM quality_documents
            WHERE document_status = 'active'
            AND periodic_review_required = true
            AND next_review_date <= CURRENT_DATE + INTERVAL '30 days'
        """)
        
        docs_for_review = cursor.fetchall()
        
        for doc_id, doc_num, doc_title, review_date, days_until in docs_for_review:
            if days_until < 0:
                # Overdue - mark for review
                cursor.execute("""
                    UPDATE quality_documents
                    SET document_status = 'under_review'
                    WHERE document_id = %s
                """, (doc_id,))
                
                logger.warning(f"Document OVERDUE for review: {doc_num} - {doc_title}")
            elif days_until <= 7:
                logger.info(f"Document review due soon: {doc_num} ({days_until} days)")
        
        pg_connection.commit()
        cursor.close()
        
        if docs_for_review:
            logger.info(f"Found {len(docs_for_review)} documents for review")
    except Exception as e:
        logger.error(f"Error checking document reviews: {e}")
        pg_connection.rollback()

# ============================================================================
# MAIN CYCLE
# ============================================================================

def run_qms_cycle():
    """Execute complete QMS cycle"""
    logger.info("=== QMS Cycle Starting ===")
    
    try:
        # Calibration Management
        check_calibration_due()
        
        # CAPA Management
        monitor_capa_due_dates()
        update_ncr_from_capa()
        
        # SPC Monitoring
        monitor_spc_charts()
        
        # Integration with Other Systems
        integrate_mes_quality_inspections()
        integrate_service_tickets()
        
        # KPI Calculation (once per day)
        if datetime.now().hour == 0:  # Midnight
            calculate_daily_quality_kpis()
        
        # Document Management
        check_document_reviews()
        
        stats['cycles'] += 1
        logger.info("=== QMS Cycle Complete ===")
        return True
    except Exception as e:
        logger.error(f"Cycle error: {e}")
        return False

def print_stats():
    """Print daemon statistics"""
    elapsed = (datetime.now() - stats['start_time']).total_seconds()
    hours = elapsed / 3600
    
    logger.info("="*80)
    logger.info(f"QMS Daemon Statistics")
    logger.info(f"  Uptime: {hours:.1f} hours")
    logger.info(f"  Cycles: {stats['cycles']}")
    logger.info(f"  Calibration Alerts: {stats['calibration_alerts']}")
    logger.info(f"  CAPA Escalations: {stats['capa_escalations']}")
    logger.info(f"  NCR Updates: {stats['ncr_updates']}")
    logger.info(f"  SPC Checks: {stats['spc_checks']}")
    logger.info(f"  KPI Calculations: {stats['kpi_calculations']}")
    logger.info(f"  MES Integrations: {stats['mes_integrations']}")
    logger.info(f"  Service Integrations: {stats['service_integrations']}")
    logger.info("="*80)

def main():
    """Main daemon loop"""
    logger.info("="*80)
    logger.info("GenIMS Quality Management System Daemon Starting")
    logger.info("Cycle Interval: Every 5 minutes")
    logger.info("="*80)
    
    if not initialize_database():
        return 1
    
    logger.info("Press Ctrl+C to stop")
    
    last_cycle = datetime.now() - timedelta(hours=1)
    
    while running:
        try:
            now = datetime.now()
            
            # Run every 5 minutes
            if (now - last_cycle).total_seconds() >= CYCLE_INTERVAL_SECONDS:
                run_qms_cycle()
                last_cycle = now
            
            # Print stats every hour
            if now.minute == 0:
                print_stats()
            
            time.sleep(30)  # Check every 30 seconds
            
        except Exception as e:
            logger.error(f"Error in main loop: {e}", exc_info=True)
            time.sleep(30)
    
    logger.info("Shutting down...")
    if pg_connection:
        pg_connection.close()
    
    print_stats()
    logger.info("QMS Daemon stopped")
    return 0

if __name__ == "__main__":
    import os
    os.makedirs('logs', exist_ok=True)
    sys.exit(main())
