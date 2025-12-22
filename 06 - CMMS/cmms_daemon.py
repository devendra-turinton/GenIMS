#!/usr/bin/env python3
"""
GenIMS CMMS Daemon
Continuous maintenance management operations
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

# CMMS Configuration
CYCLE_INTERVAL_SECONDS = 1800  # Run every 30 minutes
PM_GENERATION_LOOKAHEAD_DAYS = 14  # Generate PMs 14 days in advance

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/cmms_daemon.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('CMMSDaemon')

running = True
pg_connection = None
master_data = {}
stats = {
    'cycles': 0,
    'pm_wos_generated': 0,
    'corrective_wos_created': 0,
    'wos_completed': 0,
    'parts_issued': 0,
    'meter_readings_recorded': 0,
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
        
        # Load assets
        cursor.execute("SELECT * FROM maintenance_assets WHERE is_active = true LIMIT 100")
        master_data['assets'] = [dict(zip([d[0] for d in cursor.description], row)) 
                                 for row in cursor.fetchall()]
        
        # Load technicians
        cursor.execute("SELECT * FROM maintenance_technicians WHERE is_active = true")
        master_data['technicians'] = [dict(zip([d[0] for d in cursor.description], row)) 
                                      for row in cursor.fetchall()]
        
        # Load PM schedules
        cursor.execute("SELECT * FROM pm_schedules WHERE schedule_status = 'active' LIMIT 100")
        master_data['pm_schedules'] = [dict(zip([d[0] for d in cursor.description], row)) 
                                       for row in cursor.fetchall()]
        
        # Load MRO parts
        cursor.execute("SELECT * FROM mro_parts WHERE part_status = 'active' LIMIT 100")
        master_data['mro_parts'] = [dict(zip([d[0] for d in cursor.description], row)) 
                                    for row in cursor.fetchall()]
        
        cursor.close()
        logger.info(f"Loaded: {len(master_data.get('assets', []))} assets, "
                   f"{len(master_data.get('technicians', []))} technicians, "
                   f"{len(master_data.get('pm_schedules', []))} PM schedules")
        return True
    except Exception as e:
        logger.error(f"Failed to load master data: {e}")
        return False

def generate_id(prefix: str) -> str:
    return f"{prefix}-{datetime.now().strftime('%Y%m%d%H%M%S')}-{random.randint(1000, 9999)}"

# ============================================================================
# PM WORK ORDER GENERATION
# ============================================================================

def generate_pm_work_orders():
    """Auto-generate PM work orders when due"""
    logger.info("Checking for due PM schedules...")
    
    try:
        cursor = pg_connection.cursor()
        
        # Find PM schedules due within lookahead window
        cursor.execute("""
            SELECT * FROM pm_schedules
            WHERE schedule_status = 'active'
            AND auto_generate_wo = true
            AND next_due_date IS NOT NULL
            AND next_due_date <= %s
            AND (last_completed_date IS NULL 
                 OR last_completed_date < next_due_date - INTERVAL '7 days')
            LIMIT 20
        """, ((datetime.now() + timedelta(days=PM_GENERATION_LOOKAHEAD_DAYS)).date(),))
        
        due_schedules = cursor.fetchall()
        columns = [d[0] for d in cursor.description]
        
        for schedule_row in due_schedules:
            schedule = dict(zip(columns, schedule_row))
            
            # Create PM work order
            wo_id = generate_id('WO')
            wo_number = f"PM-{datetime.now().strftime('%Y%m%d%H%M')}"
            
            cursor.execute("""
                INSERT INTO work_orders (
                    work_order_id, work_order_number, asset_id,
                    wo_type, priority, description,
                    scheduled_start_date, scheduled_end_date,
                    estimated_duration_hours, wo_status,
                    source_type, source_document_id, created_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (wo_id, wo_number, schedule['asset_id'],
                  'preventive', 'medium', schedule['schedule_name'],
                  schedule['next_due_date'],
                  (datetime.strptime(schedule['next_due_date'], '%Y-%m-%d') + 
                   timedelta(hours=schedule.get('estimated_duration_hours', 4))).date(),
                  schedule.get('estimated_duration_hours', 4),
                  'planned', 'pm_schedule', schedule['pm_schedule_id'],
                  datetime.now()))
            
            # Log PM generation
            cursor.execute("""
                INSERT INTO pm_generation_log (
                    log_id, pm_schedule_id, generation_date,
                    generation_reason, trigger_date, work_order_id,
                    work_order_number, generation_status, created_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (generate_id('PMLOG'), schedule['pm_schedule_id'],
                  datetime.now(), 'calendar_due', schedule['next_due_date'],
                  wo_id, wo_number, 'success', datetime.now()))
            
            # Update PM schedule next due date
            next_due = calculate_next_due_date(schedule)
            cursor.execute("""
                UPDATE pm_schedules
                SET last_wo_id = %s,
                    next_due_date = %s
                WHERE pm_schedule_id = %s
            """, (wo_id, next_due, schedule['pm_schedule_id']))
            
            stats['pm_wos_generated'] += 1
            logger.info(f"Generated PM work order: {wo_number}")
        
        pg_connection.commit()
        cursor.close()
        
        if due_schedules:
            logger.info(f"Generated {len(due_schedules)} PM work orders")
    except Exception as e:
        logger.error(f"Error generating PM work orders: {e}")
        pg_connection.rollback()

def calculate_next_due_date(schedule: dict):
    """Calculate next PM due date"""
    current_due = datetime.strptime(schedule['next_due_date'], '%Y-%m-%d')
    
    if schedule['schedule_type'] == 'calendar':
        freq_value = schedule.get('frequency_value', 1)
        freq_unit = schedule.get('frequency_unit', 'months')
        
        if freq_unit == 'days':
            next_due = current_due + timedelta(days=freq_value)
        elif freq_unit == 'weeks':
            next_due = current_due + timedelta(weeks=freq_value)
        elif freq_unit == 'months':
            next_due = current_due + timedelta(days=freq_value * 30)  # Approximate
        elif freq_unit == 'years':
            next_due = current_due + timedelta(days=freq_value * 365)
        else:
            next_due = current_due + timedelta(days=30)  # Default monthly
        
        return next_due.date()
    
    return (current_due + timedelta(days=30)).date()  # Default

# ============================================================================
# CORRECTIVE MAINTENANCE FROM FAULTS
# ============================================================================

def create_corrective_work_orders():
    """Create work orders from machine faults"""
    logger.info("Checking for machine faults...")
    
    try:
        cursor = pg_connection.cursor()
        
        # Check if machine_faults table exists
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'machine_faults'
            )
        """)
        
        if not cursor.fetchone()[0]:
            cursor.close()
            return
        
        # Get unaddressed critical faults
        cursor.execute("""
            SELECT mf.*, ma.asset_id
            FROM machine_faults mf
            LEFT JOIN maintenance_assets ma ON mf.machine_id = ma.machine_id
            WHERE mf.severity IN ('critical', 'high')
            AND mf.resolved = false
            AND NOT EXISTS (
                SELECT 1 FROM work_orders wo 
                WHERE wo.machine_fault_id = mf.fault_id
            )
            AND ma.asset_id IS NOT NULL
            LIMIT 10
        """)
        
        faults = cursor.fetchall()
        columns = [d[0] for d in cursor.description]
        
        for fault_row in faults:
            fault = dict(zip(columns, fault_row))
            
            # Create corrective work order
            wo_id = generate_id('WO')
            wo_number = f"CM-{datetime.now().strftime('%Y%m%d%H%M')}"
            priority = 'emergency' if fault['severity'] == 'critical' else 'urgent'
            
            cursor.execute("""
                INSERT INTO work_orders (
                    work_order_id, work_order_number, asset_id,
                    wo_type, priority, description, problem_description,
                    scheduled_start_date, wo_status,
                    source_type, machine_fault_id, created_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (wo_id, wo_number, fault['asset_id'],
                  'corrective', priority, f"Fault: {fault['fault_code']}",
                  fault.get('fault_description'),
                  datetime.now().date(), 'created',
                  'machine_fault', fault['fault_id'], datetime.now()))
            
            # Log integration
            cursor.execute("""
                INSERT INTO cmms_integration_log (
                    log_id, integration_direction, document_type,
                    document_id, integration_status, created_at
                ) VALUES (%s, %s, %s, %s, %s, %s)
            """, (generate_id('INTLOG'), 'OPERATIONAL_TO_CMMS',
                  'machine_fault', fault['fault_id'], 'completed',
                  datetime.now()))
            
            stats['corrective_wos_created'] += 1
            logger.info(f"Created corrective WO from fault: {wo_number}")
        
        pg_connection.commit()
        cursor.close()
        
        if faults:
            logger.info(f"Created {len(faults)} corrective work orders")
    except Exception as e:
        logger.error(f"Error creating corrective WOs: {e}")
        pg_connection.rollback()

# ============================================================================
# WORK ORDER EXECUTION
# ============================================================================

def assign_work_orders():
    """Assign pending work orders to technicians"""
    logger.info("Assigning work orders...")
    
    if not master_data.get('technicians'):
        return
    
    try:
        cursor = pg_connection.cursor()
        
        # Get unassigned work orders
        cursor.execute("""
            SELECT work_order_id FROM work_orders
            WHERE wo_status IN ('created', 'planned', 'scheduled')
            AND assigned_to IS NULL
            ORDER BY priority DESC, created_at
            LIMIT 10
        """)
        
        wos = cursor.fetchall()
        
        for (wo_id,) in wos:
            # Assign to available technician
            available_techs = [t for t in master_data['technicians'] 
                              if t.get('technician_status') == 'available']
            
            if available_techs:
                tech = random.choice(available_techs)
                
                cursor.execute("""
                    UPDATE work_orders
                    SET assigned_to = %s,
                        wo_status = 'assigned'
                    WHERE work_order_id = %s
                """, (tech['technician_id'], wo_id))
        
        pg_connection.commit()
        cursor.close()
    except Exception as e:
        logger.error(f"Error assigning work orders: {e}")
        pg_connection.rollback()

def complete_work_orders():
    """Complete in-progress work orders"""
    logger.info("Completing work orders...")
    
    try:
        cursor = pg_connection.cursor()
        
        # Get in-progress work orders that should be completed
        cursor.execute("""
            SELECT work_order_id, asset_id, actual_start_date
            FROM work_orders
            WHERE wo_status = 'in_progress'
            AND actual_start_date < %s
            LIMIT 5
        """, (datetime.now() - timedelta(hours=2),))
        
        wos = cursor.fetchall()
        
        for wo_id, asset_id, start_date in wos:
            # Complete work order
            cursor.execute("""
                UPDATE work_orders
                SET wo_status = 'completed',
                    actual_end_date = %s,
                    actual_duration_hours = EXTRACT(EPOCH FROM (%s - actual_start_date))/3600,
                    completed_at = %s
                WHERE work_order_id = %s
            """, (datetime.now(), datetime.now(), datetime.now(), wo_id))
            
            # Create maintenance history
            cursor.execute("""
                INSERT INTO maintenance_history (
                    history_id, asset_id, event_type, event_date,
                    event_description, work_order_id, created_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (generate_id('HIST'), asset_id, 'work_order_completed',
                  datetime.now(), 'Work order completed', wo_id, datetime.now()))
            
            stats['wos_completed'] += 1
        
        pg_connection.commit()
        cursor.close()
        
        if wos:
            logger.info(f"Completed {len(wos)} work orders")
    except Exception as e:
        logger.error(f"Error completing work orders: {e}")
        pg_connection.rollback()

# ============================================================================
# PARTS & INVENTORY
# ============================================================================

def issue_parts():
    """Issue parts for active work orders"""
    if not master_data.get('mro_parts'):
        return
    
    try:
        cursor = pg_connection.cursor()
        
        # Get active work orders needing parts
        cursor.execute("""
            SELECT wo.work_order_id, wo.asset_id
            FROM work_orders wo
            WHERE wo.wo_status IN ('assigned', 'in_progress')
            AND NOT EXISTS (
                SELECT 1 FROM mro_parts_transactions mpt
                WHERE mpt.work_order_id = wo.work_order_id
            )
            LIMIT 5
        """)
        
        wos = cursor.fetchall()
        
        for wo_id, asset_id in wos:
            # Issue 1-2 random parts
            for _ in range(random.randint(1, 2)):
                part = random.choice(master_data['mro_parts'])
                qty = random.randint(1, 3)
                
                cursor.execute("""
                    INSERT INTO mro_parts_transactions (
                        transaction_id, transaction_number, mro_part_id,
                        transaction_type, quantity, unit_of_measure,
                        unit_cost, total_cost, work_order_id,
                        asset_id, transaction_date, created_at
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (generate_id('PTRANS'), f"PT-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                      part['mro_part_id'], 'issue', qty, part['unit_of_measure'],
                      part['standard_cost'], qty * part['standard_cost'],
                      wo_id, asset_id, datetime.now(), datetime.now()))
                
                # Update part stock
                cursor.execute("""
                    UPDATE mro_parts
                    SET current_stock = current_stock - %s
                    WHERE mro_part_id = %s
                    AND current_stock >= %s
                """, (qty, part['mro_part_id'], qty))
                
                stats['parts_issued'] += 1
        
        pg_connection.commit()
        cursor.close()
    except Exception as e:
        logger.error(f"Error issuing parts: {e}")
        pg_connection.rollback()

# ============================================================================
# METER READINGS
# ============================================================================

def record_meter_readings():
    """Record equipment meter readings"""
    if not master_data.get('assets'):
        return
    
    try:
        cursor = pg_connection.cursor()
        
        # Record readings for 5 random metered assets
        metered_assets = [a for a in master_data['assets'] if a.get('has_meter')]
        
        for asset in random.sample(metered_assets, min(5, len(metered_assets))):
            # Increment meter
            new_reading = asset.get('current_meter_reading', 0) + random.uniform(10, 100)
            
            cursor.execute("""
                INSERT INTO equipment_meter_readings (
                    reading_id, asset_id, reading_date, meter_value,
                    meter_unit, reading_source, created_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (generate_id('METER'), asset['asset_id'],
                  datetime.now(), round(new_reading, 2),
                  asset.get('meter_unit', 'hours'), 'automated', datetime.now()))
            
            # Update asset current reading
            cursor.execute("""
                UPDATE maintenance_assets
                SET current_meter_reading = %s,
                    meter_reading_date = %s
                WHERE asset_id = %s
            """, (round(new_reading, 2), datetime.now(), asset['asset_id']))
            
            stats['meter_readings_recorded'] += 1
        
        pg_connection.commit()
        cursor.close()
    except Exception as e:
        logger.error(f"Error recording meters: {e}")
        pg_connection.rollback()

# ============================================================================
# MAIN CYCLE
# ============================================================================

def run_cmms_cycle():
    """Execute complete CMMS cycle"""
    logger.info("=== CMMS Cycle Starting ===")
    
    try:
        # 1. Generate PM work orders
        generate_pm_work_orders()
        
        # 2. Create corrective WOs from faults
        create_corrective_work_orders()
        
        # 3. Assign work orders
        assign_work_orders()
        
        # 4. Complete in-progress work orders
        complete_work_orders()
        
        # 5. Issue parts
        issue_parts()
        
        # 6. Record meter readings
        record_meter_readings()
        
        stats['cycles'] += 1
        logger.info("=== CMMS Cycle Complete ===")
        return True
    except Exception as e:
        logger.error(f"CMMS cycle error: {e}")
        return False

def print_stats():
    """Print daemon statistics"""
    elapsed = (datetime.now() - stats['start_time']).total_seconds()
    hours = elapsed / 3600
    
    logger.info("="*80)
    logger.info(f"CMMS Daemon Statistics")
    logger.info(f"  Uptime: {hours:.1f} hours")
    logger.info(f"  Cycles: {stats['cycles']}")
    logger.info(f"  PM WOs Generated: {stats['pm_wos_generated']}")
    logger.info(f"  Corrective WOs Created: {stats['corrective_wos_created']}")
    logger.info(f"  WOs Completed: {stats['wos_completed']}")
    logger.info(f"  Parts Issued: {stats['parts_issued']}")
    logger.info(f"  Meter Readings: {stats['meter_readings_recorded']}")
    logger.info("="*80)

def main():
    """Main daemon loop"""
    logger.info("="*80)
    logger.info("GenIMS CMMS Daemon Starting")
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
                run_cmms_cycle()
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
    logger.info("CMMS Daemon stopped")
    return 0

if __name__ == "__main__":
    import os
    os.makedirs('logs', exist_ok=True)
    sys.exit(main())
