#!/usr/bin/env python3
"""
GenIMS MES Hourly Production Daemon
Continuously generates production data every hour simulating real factory operations
"""

import sys
import os
import time
import logging
import signal
from datetime import datetime, timedelta
import random
import json
from dotenv import load_dotenv

# Load environment variables from parent directory config
env_file = os.path.join(os.path.dirname(__file__), '..', '..', 'scripts', 'config.env')
if os.path.exists(env_file):
    load_dotenv(env_file)

try:
    import psycopg2
    from psycopg2.extras import execute_batch
    POSTGRES_AVAILABLE = True
except ImportError:
    POSTGRES_AVAILABLE = False
    print("WARNING: psycopg2 not installed. Install with: pip install psycopg2-binary")

# ============================================================================
# CONFIGURATION - Environment Variables with Defaults
# ============================================================================

# Database Configuration - from Azure Cloud via config.env
PG_HOST = os.getenv('POSTGRES_HOST', 'localhost')
PG_PORT = int(os.getenv('POSTGRES_PORT', '5432'))
PG_DATABASE = os.getenv('FOLDER_03_DATABASE', os.getenv('DB_MANUFACTURING', 'genims_manufacturing_db'))
PG_MASTER_DATABASE = os.getenv('DB_MASTER', 'genims_master_db')  # Master data database
PG_USER = os.getenv('POSTGRES_USER', 'postgres')
PG_PASSWORD = os.getenv('POSTGRES_PASSWORD', '')
PG_SSL_MODE = os.getenv('PG_SSL_MODE', 'require')

# Daemon Configuration
MES_ENABLED = os.getenv('MES_ENABLED', 'true').lower() == 'true'
CYCLE_INTERVAL_SECONDS = int(os.getenv('MES_CYCLE_INTERVAL', '3600'))  # Run every hour
BATCH_SIZE = int(os.getenv('MES_BATCH_SIZE', '50'))  # Records per batch insert

# Production Rates (per hour)
DAY_SHIFT_ORDERS = (4, 5)      # 06:00-14:00
EVENING_SHIFT_ORDERS = (3, 4)   # 14:00-22:00
NIGHT_SHIFT_ORDERS = (1, 2)     # 22:00-06:00
WEEKEND_ORDERS = (1, 2)         # Saturday/Sunday (50% capacity)

# Quality Parameters
FIRST_PASS_YIELD_RANGE = (92, 99.5)
INSPECTION_PASS_RATE = 0.95
DEFECT_PROBABILITY = 0.03
EBR_GENERATION_RATE = 0.5  # 50% of completed orders get eBR

# Material Lists
RAW_MATERIALS = [
    'RM-STEEL-SHEET', 'RM-STEEL-ROD', 'RM-ALUMINUM-BAR', 'RM-COPPER-WIRE',
    'RM-RUBBER-COMPOUND', 'RM-PLASTIC-PELLET', 'RM-PAINT-BASE', 'RM-LUBRICANT'
]

COMPONENTS = [
    'COMP-BOLT-M8', 'COMP-NUT-M8', 'COMP-WASHER-8MM', 'COMP-SPRING-20N',
    'COMP-BEARING-6205', 'COMP-SEAL-RUBBER', 'COMP-GASKET-FIBER', 'COMP-O-RING-10MM'
]

# Logging - use centralized logs directory with fallback
log_dir = os.getenv("DAEMON_LOG_DIR", os.path.join(os.path.dirname(__file__), '..', '..', 'logs'))
os.makedirs(log_dir, exist_ok=True)

# Get log file path from env, expand variables if needed
log_file_env = os.getenv('MES_LOG_FILE', '')
if log_file_env and '$LOGS_DIR' in log_file_env:
    log_file = log_file_env.replace('$LOGS_DIR', log_dir)
elif log_file_env:
    log_file = log_file_env
else:
    log_file = os.path.join(log_dir, 'mes_hourly_daemon.log')

log_level = getattr(logging, os.getenv('DAEMON_LOG_LEVEL', 'INFO').upper(), logging.INFO)

logging.basicConfig(
    level=log_level,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('MESHourlyDaemon')

# ============================================================================
# GLOBAL STATE
# ============================================================================

running = True
pg_connection = None
master_data = {}
counters = {
    'work_order': 1,
    'operation': 1,
    'material': 1,
    'inspection': 1,
    'defect': 1,
    'labor': 1,
    'downtime': 1,
    'changeover': 1,
    'ebr': 1,
    'schedule': 1
}

stats = {
    'cycles_completed': 0,
    'work_orders_created': 0,
    'work_orders_completed': 0,
    'operations_completed': 0,
    'material_transactions': 0,
    'quality_inspections': 0,
    'defects_recorded': 0,
    'labor_entries': 0,
    'downtime_events': 0,
    'changeovers': 0,
    'ebrs_generated': 0,
    'errors': 0,
    'start_time': datetime.now()
}

# Buffers for batch inserts
buffers = {
    'work_orders': [],
    'operations': [],
    'materials': [],
    'inspections': [],
    'defects': [],
    'labor': [],
    'downtime': [],
    'changeovers': [],
    'ebrs': [],
    'schedule': []
}


def signal_handler(sig, frame):
    """Handle shutdown signals gracefully"""
    global running
    logger.info("Shutdown signal received. Stopping daemon...")
    running = False


signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)


# ============================================================================
# DATABASE FUNCTIONS
# ============================================================================

def initialize_database():
    """Initialize PostgreSQL connection with SSL support for Azure"""
    global pg_connection
    
    if not POSTGRES_AVAILABLE:
        logger.error("PostgreSQL library not available. Cannot start daemon.")
        logger.error("Install with: pip install psycopg2-binary")
        return False
    
    try:
        pg_connection = psycopg2.connect(
            host=PG_HOST,
            port=PG_PORT,
            database=PG_DATABASE,
            user=PG_USER,
            password=PG_PASSWORD,
            sslmode=PG_SSL_MODE
        )
        pg_connection.autocommit = False
        logger.info(f"PostgreSQL connection established: {PG_HOST}:{PG_PORT}/{PG_DATABASE} (SSL: {PG_SSL_MODE})")
        return True
    except Exception as e:
        logger.error(f"Failed to connect to PostgreSQL: {e}")
        return False


def check_connection():
    """Check if database connection is alive and reconnect if needed"""
    global pg_connection
    try:
        if pg_connection is None or pg_connection.closed:
            logger.warning("Connection is closed, reconnecting...")
            if not initialize_database():
                logger.error("Failed to reconnect to database")
                return False
            logger.info("Successfully reconnected to database")
            return True
        # Test the connection with a simple query
        cursor = pg_connection.cursor()
        cursor.execute("SELECT 1")
        cursor.close()
        pg_connection.commit()  # Ensure we're not in a failed transaction state
        return True
    except Exception as e:
        logger.warning(f"Connection check failed ({type(e).__name__}: {e}), reconnecting...")
        try:
            if pg_connection and not pg_connection.closed:
                pg_connection.close()
        except:
            pass
        pg_connection = None
        if not initialize_database():
            logger.error("Failed to reconnect after connection check failure")
            return False
        logger.info("Successfully reconnected after connection failure")
        return True
        logger.error(f"Config file: {env_file}")
        logger.error("Verify config.env has correct POSTGRES_HOST, POSTGRES_USER, POSTGRES_PASSWORD, FOLDER_03_DATABASE")
        return False


def load_master_data():
    """Load master data from master database"""
    global master_data
    
    try:
        # Connect to master database to load master data
        master_conn = psycopg2.connect(
            host=PG_HOST,
            port=PG_PORT,
            database=PG_MASTER_DATABASE,
            user=PG_USER,
            password=PG_PASSWORD,
            sslmode=PG_SSL_MODE
        )
        cursor = master_conn.cursor()
        
        # Load factories
        cursor.execute("SELECT * FROM factories")
        master_data['factories'] = [dict(zip([d[0] for d in cursor.description], row)) 
                                    for row in cursor.fetchall()]
        
        # Load production lines
        cursor.execute("SELECT * FROM production_lines")
        master_data['lines'] = [dict(zip([d[0] for d in cursor.description], row)) 
                               for row in cursor.fetchall()]
        
        # Load machines
        cursor.execute("SELECT * FROM machines")
        master_data['machines'] = [dict(zip([d[0] for d in cursor.description], row)) 
                                   for row in cursor.fetchall()]
        
        # Load employees
        cursor.execute("SELECT * FROM employees")
        master_data['employees'] = [dict(zip([d[0] for d in cursor.description], row)) 
                                    for row in cursor.fetchall()]
        
        # Load shifts
        cursor.execute("SELECT * FROM shifts")
        master_data['shifts'] = [dict(zip([d[0] for d in cursor.description], row)) 
                                for row in cursor.fetchall()]
        
        # Load products
        cursor.execute("SELECT * FROM products")
        master_data['products'] = [dict(zip([d[0] for d in cursor.description], row)) 
                                   for row in cursor.fetchall()]
        
        # Load customers
        cursor.execute("SELECT * FROM customers")
        master_data['customers'] = [dict(zip([d[0] for d in cursor.description], row)) 
                                    for row in cursor.fetchall()]
        
        # Load line-product mappings
        cursor.execute("SELECT * FROM line_product_mapping")
        master_data['mappings'] = [dict(zip([d[0] for d in cursor.description], row)) 
                                   for row in cursor.fetchall()]
        
        cursor.close()
        master_conn.close()
        
        logger.info(f"Master data loaded successfully from {PG_MASTER_DATABASE}:")
        logger.info(f"  Factories: {len(master_data.get('factories', []))}")
        logger.info(f"  Production Lines: {len(master_data.get('lines', []))}")
        logger.info(f"  Machines: {len(master_data.get('machines', []))}")
        logger.info(f"  Products: {len(master_data.get('products', []))}")
        logger.info(f"  Line-Product Mappings: {len(master_data.get('mappings', []))}")
        logger.info(f"  Employees: {len(master_data.get('employees', []))}")
        logger.info(f"  Customers: {len(master_data.get('customers', []))}")
        logger.info(f"  Shifts: {len(master_data.get('shifts', []))}")
        
        # Initialize counters based on existing data
        _initialize_counters()
        
        return True
    except Exception as e:
        logger.error(f"Failed to load master data from {PG_MASTER_DATABASE}: {e}")
        logger.error(f"Ensure master data tables exist in database: {PG_MASTER_DATABASE}")
        return False


def _initialize_counters():
    """Initialize counters based on existing data"""
    try:
        cursor = pg_connection.cursor()
        
        # Get max IDs from each table - use MAX of numeric part of ID
        tables = {
            'work_order': ('work_orders', 'work_order_id', 'WO'),
            'operation': ('work_order_operations', 'operation_id', 'OP'),
            'material': ('material_transactions', 'transaction_id', 'MAT'),
            'inspection': ('quality_inspections', 'inspection_id', 'INSP'),
            'defect': ('defects', 'defect_id', 'DEF'),
            'labor': ('labor_transactions', 'labor_transaction_id', 'LAB'),
            'downtime': ('downtime_events', 'downtime_id', 'DOWN'),
            'changeover': ('changeover_events', 'changeover_id', 'CHG'),
            'ebr': ('electronic_batch_records', 'ebr_id', 'EBR'),
            'schedule': ('production_schedule', 'schedule_id', 'SCH')
        }
        
        for key, (table, id_col, prefix) in tables.items():
            try:
                # Get max numeric value from ID column
                cursor.execute(f"""
                    SELECT COALESCE(MAX(CAST(SUBSTRING({id_col} FROM '[0-9]+') AS INTEGER)), 0)
                    FROM {table}
                    WHERE {id_col} LIKE '{prefix}-%'
                """)
                max_id = cursor.fetchone()[0]
                counters[key] = max_id + 1
                logger.info(f"Counter {key}: starting at {counters[key]} (max found: {max_id})")
            except Exception as e:
                logger.warning(f"Could not initialize counter for {key}: {e}")
                counters[key] = 1
        
        cursor.close()
    except Exception as e:
        logger.warning(f"Could not initialize counters: {e}")


def flush_buffers():
    """Flush all buffers to database"""
    try:
        cursor = pg_connection.cursor()
        
        # Work Orders
        if buffers['work_orders']:
            sql = """
                INSERT INTO work_orders (
                    work_order_id, work_order_number, product_id, customer_id, sales_order_number,
                    factory_id, line_id, planned_quantity, unit_of_measure, priority,
                    planned_start_date, planned_end_date, scheduled_start_time, scheduled_end_time,
                    actual_start_time, actual_end_time, produced_quantity, good_quantity,
                    rejected_quantity, scrapped_quantity, rework_quantity, status, quality_status,
                    quality_hold, planned_cycle_time_seconds, actual_cycle_time_seconds,
                    setup_time_minutes, run_time_minutes, downtime_minutes, yield_percentage,
                    first_pass_yield_percentage, standard_cost_per_unit, actual_cost_per_unit,
                    total_material_cost, total_labor_cost, total_overhead_cost, batch_number,
                    lot_number, expiry_date, electronic_batch_record_id, requires_validation,
                    validation_status, parent_work_order_id, erp_order_id, created_by,
                    created_at, updated_at, completed_by, closed_at
                ) VALUES (
                    %(work_order_id)s, %(work_order_number)s, %(product_id)s, %(customer_id)s, %(sales_order_number)s,
                    %(factory_id)s, %(line_id)s, %(planned_quantity)s, %(unit_of_measure)s, %(priority)s,
                    %(planned_start_date)s, %(planned_end_date)s, %(scheduled_start_time)s, %(scheduled_end_time)s,
                    %(actual_start_time)s, %(actual_end_time)s, %(produced_quantity)s, %(good_quantity)s,
                    %(rejected_quantity)s, %(scrapped_quantity)s, %(rework_quantity)s, %(status)s, %(quality_status)s,
                    %(quality_hold)s, %(planned_cycle_time_seconds)s, %(actual_cycle_time_seconds)s,
                    %(setup_time_minutes)s, %(run_time_minutes)s, %(downtime_minutes)s, %(yield_percentage)s,
                    %(first_pass_yield_percentage)s, %(standard_cost_per_unit)s, %(actual_cost_per_unit)s,
                    %(total_material_cost)s, %(total_labor_cost)s, %(total_overhead_cost)s, %(batch_number)s,
                    %(lot_number)s, %(expiry_date)s, %(electronic_batch_record_id)s, %(requires_validation)s,
                    %(validation_status)s, %(parent_work_order_id)s, %(erp_order_id)s, %(created_by)s,
                    %(created_at)s, %(updated_at)s, %(completed_by)s, %(closed_at)s
                )
            """
            execute_batch(cursor, sql, buffers['work_orders'])
            pg_connection.commit()
            logger.info(f"Flushed {len(buffers['work_orders'])} work orders")
            buffers['work_orders'] = []
        
        # Materials (simplified for brevity - similar pattern for all buffers)
        if buffers['materials']:
            sql = """
                INSERT INTO material_transactions (
                    transaction_id, transaction_type, transaction_date, work_order_id, operation_id,
                    material_code, material_name, material_type, quantity, unit_of_measure,
                    lot_number, batch_number, serial_number, expiry_date, supplier_lot_number,
                    from_location, to_location, warehouse_location, unit_cost, total_cost,
                    quality_status, inspection_required, certificate_of_analysis, parent_lot_number,
                    consumed_by_lot_number, performed_by, requires_documentation, documentation_complete,
                    created_at
                ) VALUES (
                    %(transaction_id)s, %(transaction_type)s, %(transaction_date)s, %(work_order_id)s, %(operation_id)s,
                    %(material_code)s, %(material_name)s, %(material_type)s, %(quantity)s, %(unit_of_measure)s,
                    %(lot_number)s, %(batch_number)s, %(serial_number)s, %(expiry_date)s, %(supplier_lot_number)s,
                    %(from_location)s, %(to_location)s, %(warehouse_location)s, %(unit_cost)s, %(total_cost)s,
                    %(quality_status)s, %(inspection_required)s, %(certificate_of_analysis)s, %(parent_lot_number)s,
                    %(consumed_by_lot_number)s, %(performed_by)s, %(requires_documentation)s, %(documentation_complete)s,
                    %(created_at)s
                )
            """
            execute_batch(cursor, sql, buffers['materials'])
            pg_connection.commit()
            logger.info(f"Flushed {len(buffers['materials'])} material transactions")
            buffers['materials'] = []
        
        # Inspections
        if buffers['inspections']:
            sql = """
                INSERT INTO quality_inspections (
                    inspection_id, inspection_type, inspection_date, work_order_id, operation_id,
                    product_id, sample_size, lot_number, batch_number, serial_number,
                    inspector_id, shift_id, inspection_result, defects_found, critical_defects,
                    major_defects, minor_defects, measured_values, specification_values,
                    disposition, disposition_reason, disposition_by, ncr_number,
                    corrective_action_required, inspection_plan_id, inspection_checklist_id,
                    photos_attached, approved_by, approved_at, notes, created_at
                ) VALUES (
                    %(inspection_id)s, %(inspection_type)s, %(inspection_date)s, %(work_order_id)s, %(operation_id)s,
                    %(product_id)s, %(sample_size)s, %(lot_number)s, %(batch_number)s, %(serial_number)s,
                    %(inspector_id)s, %(shift_id)s, %(inspection_result)s, %(defects_found)s, %(critical_defects)s,
                    %(major_defects)s, %(minor_defects)s, %(measured_values)s, %(specification_values)s,
                    %(disposition)s, %(disposition_reason)s, %(disposition_by)s, %(ncr_number)s,
                    %(corrective_action_required)s, %(inspection_plan_id)s, %(inspection_checklist_id)s,
                    %(photos_attached)s, %(approved_by)s, %(approved_at)s, %(notes)s, %(created_at)s
                )
            """
            execute_batch(cursor, sql, buffers['inspections'])
            pg_connection.commit()
            logger.info(f"Flushed {len(buffers['inspections'])} quality inspections")
            buffers['inspections'] = []
        
        # Labor
        if buffers['labor']:
            sql = """
                INSERT INTO labor_transactions (
                    labor_transaction_id, transaction_date, employee_id, shift_id, work_order_id,
                    operation_id, activity_code, activity_type, clock_in_time, clock_out_time,
                    duration_minutes, break_time_minutes, quantity_produced, quantity_rejected,
                    standard_hours, actual_hours, efficiency_percentage, hourly_rate, labor_cost,
                    overtime_hours, overtime_cost, approved, approved_by, approved_at, notes, created_at
                ) VALUES (
                    %(labor_transaction_id)s, %(transaction_date)s, %(employee_id)s, %(shift_id)s, %(work_order_id)s,
                    %(operation_id)s, %(activity_code)s, %(activity_type)s, %(clock_in_time)s, %(clock_out_time)s,
                    %(duration_minutes)s, %(break_time_minutes)s, %(quantity_produced)s, %(quantity_rejected)s,
                    %(standard_hours)s, %(actual_hours)s, %(efficiency_percentage)s, %(hourly_rate)s, %(labor_cost)s,
                    %(overtime_hours)s, %(overtime_cost)s, %(approved)s, %(approved_by)s, %(approved_at)s, %(notes)s, %(created_at)s
                )
            """
            execute_batch(cursor, sql, buffers['labor'])
            pg_connection.commit()
            logger.info(f"Flushed {len(buffers['labor'])} labor transactions")
            buffers['labor'] = []
        
        # Schedule
        if buffers['schedule']:
            sql = """
                INSERT INTO production_schedule (
                    schedule_id, schedule_date, schedule_week, shift_id, line_id, factory_id,
                    work_order_id, operation_id, sequence_number, planned_start_time, planned_end_time,
                    planned_quantity, priority, customer_due_date, material_available, operator_available,
                    equipment_available, schedule_status, actual_start_time, actual_end_time,
                    actual_quantity, on_time_start, on_time_completion, schedule_adherence_percentage,
                    planner_id, planning_notes, created_at, updated_at
                ) VALUES (
                    %(schedule_id)s, %(schedule_date)s, %(schedule_week)s, %(shift_id)s, %(line_id)s, %(factory_id)s,
                    %(work_order_id)s, %(operation_id)s, %(sequence_number)s, %(planned_start_time)s, %(planned_end_time)s,
                    %(planned_quantity)s, %(priority)s, %(customer_due_date)s, %(material_available)s, %(operator_available)s,
                    %(equipment_available)s, %(schedule_status)s, %(actual_start_time)s, %(actual_end_time)s,
                    %(actual_quantity)s, %(on_time_start)s, %(on_time_completion)s, %(schedule_adherence_percentage)s,
                    %(planner_id)s, %(planning_notes)s, %(created_at)s, %(updated_at)s
                )
            """
            execute_batch(cursor, sql, buffers['schedule'])
            pg_connection.commit()
            logger.info(f"Flushed {len(buffers['schedule'])} schedule entries")
            buffers['schedule'] = []
        
        cursor.close()
        return True
        
    except Exception as e:
        logger.error(f"Error flushing buffers: {e}")
        if pg_connection and not pg_connection.closed:
            pg_connection.rollback()
        return False


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def generate_id(prefix: str, counter_key: str) -> str:
    """Generate unique ID"""
    id_val = f"{prefix}-{str(counters[counter_key]).zfill(6)}"
    counters[counter_key] += 1
    return id_val


def get_shift_for_time(factory_id: str, dt: datetime) -> dict:
    """Get shift for given time"""
    hour = dt.hour
    day_of_week = dt.strftime('%a').lower()
    
    factory_shifts = [s for s in master_data['shifts'] if s['factory_id'] == factory_id]
    
    for shift in factory_shifts:
        days = shift['days_of_week'].split(',')
        if day_of_week in days:
            # Handle both string and datetime.time objects
            if isinstance(shift['start_time'], str):
                start_hour = int(shift['start_time'].split(':')[0])
                end_hour = int(shift['end_time'].split(':')[0])
            else:  # datetime.time object
                start_hour = shift['start_time'].hour
                end_hour = shift['end_time'].hour
            
            if start_hour <= end_hour:
                if start_hour <= hour < end_hour:
                    return shift
            else:  # Crosses midnight
                if hour >= start_hour or hour < end_hour:
                    return shift
    
    # Default to general shift
    return next((s for s in factory_shifts if s['shift_code'] == 'G'), factory_shifts[0])


def get_operators_for_shift(line_id: str, shift_name: str) -> list:
    """Get operators for line and shift"""
    return [e for e in master_data['employees'] 
            if e['line_id'] == line_id 
            and e['shift'] == shift_name 
            and e['role'] == 'operator']


def determine_hourly_capacity() -> int:
    """Determine how many work orders to create this hour"""
    current_hour = datetime.now().hour
    is_weekend = datetime.now().weekday() >= 5
    
    if is_weekend:
        return random.randint(*WEEKEND_ORDERS)
    elif 6 <= current_hour < 14:  # Day shift
        return random.randint(*DAY_SHIFT_ORDERS)
    elif 14 <= current_hour < 22:  # Evening shift
        return random.randint(*EVENING_SHIFT_ORDERS)
    else:  # Night shift
        return random.randint(*NIGHT_SHIFT_ORDERS)
# ============================================================================
# PRODUCTION FUNCTIONS - Part 2 of MES Hourly Daemon
# ============================================================================

def create_new_work_orders(count: int):
    """Create new work orders"""
    logger.info(f"Creating {count} new work orders...")
    
    if not master_data['mappings']:
        logger.error("No line-product mappings available, cannot create work orders")
        return
    
    for i in range(count):
        mapping = None
        product = None
        try:
            # Select random line-product mapping
            mapping = random.choice(master_data['mappings'])
            line_id = mapping['line_id']
            product_id = mapping['product_id']
            factory_id = mapping['factory_id']
            
            # Get product details
            product = next(p for p in master_data['products'] if p['product_id'] == product_id)
            
            # Customer (80% customer orders, 20% stock)
            customer_id = random.choice(master_data['customers'])['customer_id'] if (random.random() < 0.8 and master_data['customers']) else None
            
            # Quantities
            planned_qty = random.randint(50, 500)
            
            # Timing
            now = datetime.now()
            start_hour = random.randint(now.hour, min(now.hour + 2, 23))
            planned_start = now.replace(hour=start_hour, minute=random.randint(0, 59), second=0, microsecond=0)
            
            # Duration
            cycle_time = product['standard_cycle_time_seconds']
            estimated_minutes = (planned_qty * cycle_time) / 60
            setup_time = random.randint(30, 90)
            total_minutes = int(estimated_minutes + setup_time)
            
            planned_end = planned_start + timedelta(minutes=total_minutes)
            
            # Batch/lot numbers
            batch_number = f"BATCH-{now.strftime('%Y%m%d')}-{counters['work_order']:04d}"
            lot_number = f"LOT-{factory_id[-3:]}-{counters['work_order']:05d}"
            
            # Create work order
            work_order = {
                'work_order_id': generate_id('WO', 'work_order'),
                'work_order_number': f"WO-{now.strftime('%Y%m%d')}-{counters['work_order']-1:04d}",
                'product_id': product_id,
                'customer_id': customer_id,
                'sales_order_number': f"SO-{random.randint(10000, 99999)}" if customer_id else None,
                'factory_id': factory_id,
                'line_id': line_id,
                'planned_quantity': planned_qty,
                'unit_of_measure': 'EA',
                'priority': random.randint(1, 10),
                'planned_start_date': planned_start.strftime('%Y-%m-%d %H:%M:%S'),
                'planned_end_date': planned_end.strftime('%Y-%m-%d %H:%M:%S'),
                'scheduled_start_time': planned_start.strftime('%Y-%m-%d %H:%M:%S'),
                'scheduled_end_time': planned_end.strftime('%Y-%m-%d %H:%M:%S'),
                'actual_start_time': None,
                'actual_end_time': None,
                'produced_quantity': 0,
                'good_quantity': 0,
                'rejected_quantity': 0,
                'scrapped_quantity': 0,
                'rework_quantity': 0,
                'status': 'scheduled',
                'quality_status': 'pending',
                'quality_hold': False,
                'planned_cycle_time_seconds': cycle_time,
                'actual_cycle_time_seconds': None,
                'setup_time_minutes': setup_time,
                'run_time_minutes': None,
                'downtime_minutes': 0,
                'yield_percentage': None,
                'first_pass_yield_percentage': None,
                'standard_cost_per_unit': round(random.uniform(10, 100), 2),
                'actual_cost_per_unit': None,
                'total_material_cost': None,
                'total_labor_cost': None,
                'total_overhead_cost': None,
                'batch_number': batch_number,
                'lot_number': lot_number,
                'expiry_date': (now + timedelta(days=365)).strftime('%Y-%m-%d'),
                'electronic_batch_record_id': None,
                'requires_validation': False,
                'validation_status': None,
                'parent_work_order_id': None,
                'erp_order_id': f"ERP-{random.randint(100000, 999999)}",
                'created_by': random.choice(([e['employee_id'] for e in master_data['employees'] if e['role'] in ['supervisor', 'manager']] or [master_data['employees'][0]['employee_id']]) if master_data['employees'] else ['EMP-000001']),
                'created_at': now.strftime('%Y-%m-%d %H:%M:%S'),
                'updated_at': now.strftime('%Y-%m-%d %H:%M:%S'),
                'completed_by': None,
                'closed_at': None
            }
            
            buffers['work_orders'].append(work_order)
            stats['work_orders_created'] += 1
            
            # Create schedule entry
            _create_schedule_entry(work_order)
            
        except IndexError as e:
            logger.error(f"IndexError creating work order {i+1}/{count}: {e}")
            logger.error(f"Mapping: {mapping}, Product: {product}")
            logger.error(f"Employees count: {len(master_data.get('employees', []))}")
            logger.error(f"Supervisors/managers: {len([e for e in master_data.get('employees', []) if e.get('role') in ['supervisor', 'manager']])}")
            continue
        except Exception as e:
            logger.error(f"Error creating work order {i+1}/{count}: {e}", exc_info=True)
            continue
    
    logger.info(f"Created {count} work orders")


def update_in_progress_orders():
    """Update work orders currently in progress"""
    if not check_connection():
        logger.error("Database connection unavailable")
        return
    
    try:
        cursor = pg_connection.cursor()
        
        # Get in-progress orders
        cursor.execute("""
            SELECT * FROM work_orders 
            WHERE status = 'in_progress'
            AND actual_start_time IS NOT NULL
        """)
        
        columns = [d[0] for d in cursor.description]
        in_progress = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        logger.info(f"Updating {len(in_progress)} in-progress orders...")
        
        for wo in in_progress:
            # Calculate progress
            start_time = wo['actual_start_time']
            planned_end = wo['planned_end_date']
            now = datetime.now()
            
            if now >= planned_end:
                # Order should be completed
                continue
            
            # Calculate expected progress
            total_duration = (planned_end - start_time).total_seconds()
            elapsed = (now - start_time).total_seconds()
            progress_pct = elapsed / total_duration
            
            # Update produced quantity
            expected_qty = int(wo['planned_quantity'] * progress_pct)
            current_produced = wo['produced_quantity']
            
            if expected_qty > current_produced:
                new_produced = min(expected_qty, wo['planned_quantity'])
                
                # Calculate good vs rejected
                fpy = random.uniform(*FIRST_PASS_YIELD_RANGE) / 100
                new_good = int(new_produced * fpy)
                new_rejected = new_produced - new_good
                
                # Update work order
                cursor.execute("""
                    UPDATE work_orders 
                    SET produced_quantity = %s,
                        good_quantity = %s,
                        rejected_quantity = %s,
                        updated_at = %s
                    WHERE work_order_id = %s
                """, (new_produced, new_good, new_rejected, 
                      now.strftime('%Y-%m-%d %H:%M:%S'), wo['work_order_id']))
                
                # Record material transaction
                if random.random() < 0.3:  # 30% chance to record material usage
                    _record_material_transaction(wo)
                
                # Record labor
                if random.random() < 0.5:  # 50% chance to record labor
                    _record_labor_transaction(wo)
        
        pg_connection.commit()
        cursor.close()
        
    except Exception as e:
        logger.error(f"Error updating in-progress orders: {e}")
        if pg_connection and not pg_connection.closed:
            pg_connection.rollback()


def start_scheduled_orders():
    """Start orders that are scheduled for now"""
    if not check_connection():
        logger.error("Database connection unavailable")
        return
    
    try:
        cursor = pg_connection.cursor()
        
        # Get scheduled orders that should start
        cursor.execute("""
            SELECT * FROM work_orders 
            WHERE status = 'scheduled'
            AND scheduled_start_time <= %s
            ORDER BY priority ASC, scheduled_start_time ASC
            LIMIT 5
        """, (datetime.now().strftime('%Y-%m-%d %H:%M:%S'),))
        
        columns = [d[0] for d in cursor.description]
        to_start = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        logger.info(f"Starting {len(to_start)} scheduled orders...")
        
        for wo in to_start:
            now = datetime.now()
            
            # Update to in_progress
            cursor.execute("""
                UPDATE work_orders 
                SET status = 'in_progress',
                    actual_start_time = %s,
                    updated_at = %s
                WHERE work_order_id = %s
            """, (now.strftime('%Y-%m-%d %H:%M:%S'), 
                  now.strftime('%Y-%m-%d %H:%M:%S'),
                  wo['work_order_id']))
            
            # Issue initial materials
            _record_material_transaction(wo)
            
            # Record labor start
            _record_labor_transaction(wo)
            
            logger.info(f"Started work order: {wo['work_order_number']}")
        
        pg_connection.commit()
        cursor.close()
        
    except Exception as e:
        logger.error(f"Error starting scheduled orders: {e}")
        if pg_connection and not pg_connection.closed:
            pg_connection.rollback()


def complete_finished_orders():
    """Complete orders that have reached their end time"""
    if not check_connection():
        logger.error("Database connection unavailable")
        return
    
    try:
        cursor = pg_connection.cursor()
        
        # Get orders that should be completed
        cursor.execute("""
            SELECT * FROM work_orders 
            WHERE status = 'in_progress'
            AND actual_start_time IS NOT NULL
            AND planned_end_date <= %s
        """, (datetime.now().strftime('%Y-%m-%d %H:%M:%S'),))
        
        columns = [d[0] for d in cursor.description]
        to_complete = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        logger.info(f"Completing {len(to_complete)} finished orders...")
        
        for wo in to_complete:
            now = datetime.now()
            
            # Calculate final metrics
            start_time = wo['actual_start_time']
            actual_duration = (now - start_time).total_seconds() / 60
            
            # Final quantities
            produced_qty = int(wo['planned_quantity'] * random.uniform(0.98, 1.02))
            fpy = random.uniform(*FIRST_PASS_YIELD_RANGE) / 100
            good_qty = int(produced_qty * fpy)
            rejected_qty = int((produced_qty - good_qty) * 0.7)
            scrapped_qty = int((produced_qty - good_qty) * 0.2)
            rework_qty = produced_qty - good_qty - rejected_qty - scrapped_qty
            
            yield_pct = (good_qty / produced_qty * 100) if produced_qty > 0 else 0
            fpyield_pct = fpy * 100
            
            actual_cycle_time = int(((now - start_time).total_seconds()) / produced_qty) if produced_qty > 0 else wo['planned_cycle_time_seconds']
            run_time = int(actual_duration) - wo['setup_time_minutes']
            downtime = random.randint(0, int(actual_duration * 0.05))
            
            # Costs
            material_cost = round(produced_qty * random.uniform(5, 20), 2)
            labor_cost = round(actual_duration / 60 * random.uniform(100, 300), 2)
            overhead_cost = round((material_cost + labor_cost) * random.uniform(0.1, 0.3), 2)
            total_cost = material_cost + labor_cost + overhead_cost
            actual_cost_per_unit = round(total_cost / produced_qty, 2) if produced_qty > 0 else 0
            
            # Update work order
            cursor.execute("""
                UPDATE work_orders 
                SET status = 'completed',
                    actual_end_time = %s,
                    produced_quantity = %s,
                    good_quantity = %s,
                    rejected_quantity = %s,
                    scrapped_quantity = %s,
                    rework_quantity = %s,
                    yield_percentage = %s,
                    first_pass_yield_percentage = %s,
                    actual_cycle_time_seconds = %s,
                    run_time_minutes = %s,
                    downtime_minutes = %s,
                    actual_cost_per_unit = %s,
                    total_material_cost = %s,
                    total_labor_cost = %s,
                    total_overhead_cost = %s,
                    quality_status = 'approved',
                    completed_by = %s,
                    updated_at = %s
                WHERE work_order_id = %s
            """, (now.strftime('%Y-%m-%d %H:%M:%S'), produced_qty, good_qty, 
                  rejected_qty, scrapped_qty, rework_qty, round(yield_pct, 2), 
                  round(fpyield_pct, 2), actual_cycle_time, run_time, downtime,
                  actual_cost_per_unit, material_cost, labor_cost, overhead_cost,
                  random.choice([e['employee_id'] for e in master_data['employees'] if e['role'] == 'supervisor'] or [master_data['employees'][0]['employee_id']]),
                  now.strftime('%Y-%m-%d %H:%M:%S'), wo['work_order_id']))
            
            # Final quality inspection
            _perform_final_inspection(wo, produced_qty, good_qty)
            
            # Generate eBR (50% of orders)
            if random.random() < EBR_GENERATION_RATE:
                _generate_ebr(wo)
            
            # Complete labor entries
            _complete_labor_for_order(wo)
            
            stats['work_orders_completed'] += 1
            logger.info(f"Completed work order: {wo['work_order_number']} ({produced_qty} units, {yield_pct:.1f}% yield)")
        
        pg_connection.commit()
        cursor.close()
        
    except Exception as e:
        logger.error(f"Error completing orders: {e}")
        if pg_connection and not pg_connection.closed:
            pg_connection.rollback()


def _create_schedule_entry(wo: dict):
    """Create production schedule entry"""
    # Handle both string and datetime objects for planned_start_date
    if isinstance(wo['planned_start_date'], str):
        planned_start = datetime.strptime(wo['planned_start_date'], '%Y-%m-%d %H:%M:%S')
    else:
        planned_start = wo['planned_start_date']
    
    schedule = {
        'schedule_id': generate_id('SCH', 'schedule'),
        'schedule_date': planned_start.strftime('%Y-%m-%d'),
        'schedule_week': planned_start.isocalendar()[1],
        'shift_id': get_shift_for_time(wo['factory_id'], planned_start)['shift_id'],
        'line_id': wo['line_id'],
        'factory_id': wo['factory_id'],
        'work_order_id': wo['work_order_id'],
        'operation_id': None,
        'sequence_number': counters['schedule'] - 1,
        'planned_start_time': wo['planned_start_date'],
        'planned_end_time': wo['planned_end_date'],
        'planned_quantity': wo['planned_quantity'],
        'priority': wo['priority'],
        'customer_due_date': None,
        'material_available': True,
        'operator_available': True,
        'equipment_available': True,
        'schedule_status': 'planned',
        'actual_start_time': None,
        'actual_end_time': None,
        'actual_quantity': None,
        'on_time_start': None,
        'on_time_completion': None,
        'schedule_adherence_percentage': None,
        'planner_id': wo['created_by'],
        'planning_notes': None,
        'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'updated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    
    buffers['schedule'].append(schedule)


def _record_material_transaction(wo: dict):
    """Record material consumption"""
    # Select random materials
    materials = random.sample(RAW_MATERIALS + COMPONENTS, random.randint(2, 5))
    
    for material_code in materials:
        # Determine material type
        if material_code in RAW_MATERIALS:
            mat_type = 'raw_material'
            mat_name = material_code.replace('RM-', '').replace('-', ' ').title()
            quantity = round(random.uniform(10, 100), 2)
            unit = 'KG'
        else:
            mat_type = 'component'
            mat_name = material_code.replace('COMP-', '').replace('-', ' ').title()
            quantity = wo['planned_quantity'] * random.randint(1, 4)
            unit = 'EA'
        
        transaction = {
            'transaction_id': generate_id('MAT', 'material'),
            'transaction_type': 'issue',
            'transaction_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'work_order_id': wo['work_order_id'],
            'operation_id': None,
            'material_code': material_code,
            'material_name': mat_name,
            'material_type': mat_type,
            'quantity': quantity,
            'unit_of_measure': unit,
            'lot_number': f"MAT-LOT-{random.randint(10000, 99999)}",
            'batch_number': f"MAT-BATCH-{random.randint(1000, 9999)}",
            'serial_number': None,
            'expiry_date': (datetime.now() + timedelta(days=180)).strftime('%Y-%m-%d'),
            'supplier_lot_number': f"SUP-{random.randint(10000, 99999)}",
            'from_location': 'WAREHOUSE-A',
            'to_location': f"LINE-{wo['line_id'][-3:]}",
            'warehouse_location': f"BIN-{random.choice(['A', 'B', 'C'])}-{random.randint(1, 50):02d}",
            'unit_cost': round(random.uniform(1, 50), 4),
            'total_cost': round(quantity * random.uniform(1, 50), 2),
            'quality_status': 'approved',
            'inspection_required': mat_type == 'raw_material',
            'certificate_of_analysis': f"COA-{random.randint(10000, 99999)}" if mat_type == 'raw_material' else None,
            'parent_lot_number': None,
            'consumed_by_lot_number': wo['lot_number'],
            'performed_by': random.choice([e['employee_id'] for e in master_data['employees'] if e['role'] == 'operator'] or [master_data['employees'][0]['employee_id']]),
            'requires_documentation': mat_type == 'raw_material',
            'documentation_complete': True,
            'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        buffers['materials'].append(transaction)
        stats['material_transactions'] += 1


def _record_labor_transaction(wo: dict):
    """Record labor time entry"""
    shift = get_shift_for_time(wo['factory_id'], datetime.now())
    operators = get_operators_for_shift(wo['line_id'], shift['shift_name'])
    
    if not operators:
        logger.warning(f"No operators found for line {wo['line_id']}, shift {shift['shift_name']}")
        return
    
    operator = random.choice(operators)
    now = datetime.now()
    
    labor = {
        'labor_transaction_id': generate_id('LAB', 'labor'),
        'transaction_date': now.strftime('%Y-%m-%d %H:%M:%S'),
        'employee_id': operator['employee_id'],
        'shift_id': shift['shift_id'],
        'work_order_id': wo['work_order_id'],
        'operation_id': None,
        'activity_code': 'DIRECT',
        'activity_type': 'direct_labor',
        'clock_in_time': now.strftime('%Y-%m-%d %H:%M:%S'),
        'clock_out_time': None,
        'duration_minutes': None,
        'break_time_minutes': 0,
        'quantity_produced': None,
        'quantity_rejected': None,
        'standard_hours': None,
        'actual_hours': None,
        'efficiency_percentage': None,
        'hourly_rate': round(random.uniform(15, 35), 2),
        'labor_cost': None,
        'overtime_hours': 0,
        'overtime_cost': 0,
        'approved': False,
        'approved_by': None,
        'approved_at': None,
        'notes': None,
        'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    
    buffers['labor'].append(labor)
    stats['labor_entries'] += 1


def _complete_labor_for_order(wo: dict):
    """Complete labor entries for finished order"""
    try:
        cursor = pg_connection.cursor()
        
        # Get open labor entries for this order
        cursor.execute("""
            SELECT * FROM labor_transactions
            WHERE work_order_id = %s
            AND clock_out_time IS NULL
        """, (wo['work_order_id'],))
        
        columns = [d[0] for d in cursor.description]
        open_labor = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        now = datetime.now()
        
        for labor in open_labor:
            clock_in = labor['clock_in_time']
            duration = int((now - clock_in).total_seconds() / 60)
            
            cursor.execute("""
                UPDATE labor_transactions
                SET clock_out_time = %s,
                    duration_minutes = %s,
                    actual_hours = %s,
                    labor_cost = %s,
                    approved = true
                WHERE labor_transaction_id = %s
            """, (now.strftime('%Y-%m-%d %H:%M:%S'), duration,
                  round(duration / 60, 2),
                  round((duration / 60) * labor['hourly_rate'], 2),
                  labor['labor_transaction_id']))
        
        cursor.close()
        
    except Exception as e:
        logger.error(f"Error completing labor: {e}")


def _perform_final_inspection(wo: dict, produced_qty: int, good_qty: int):
    """Perform final quality inspection"""
    inspection_passed = random.random() < INSPECTION_PASS_RATE
    
    if inspection_passed:
        result = 'pass'
        disposition = 'accept'
        defects = 0
        critical = 0
        major = 0
        minor = 0
    else:
        result = random.choice(['fail', 'conditional_pass'])
        disposition = random.choice(['reject', 'rework'])
        defects = random.randint(1, 5)
        critical = random.randint(0, 1)
        major = random.randint(0, 2)
        minor = defects - critical - major
    
    inspection = {
        'inspection_id': generate_id('INSP', 'inspection'),
        'inspection_type': 'final',
        'inspection_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'work_order_id': wo['work_order_id'],
        'operation_id': None,
        'product_id': wo['product_id'],
        'sample_size': min(random.randint(10, 30), produced_qty),
        'lot_number': wo['lot_number'],
        'batch_number': wo['batch_number'],
        'serial_number': None,
        'inspector_id': random.choice([e['employee_id'] for e in master_data['employees'] if e['role'] == 'quality_inspector'] or [master_data['employees'][0]['employee_id']]),
        'shift_id': get_shift_for_time(wo['factory_id'], datetime.now())['shift_id'],
        'inspection_result': result,
        'defects_found': defects,
        'critical_defects': critical,
        'major_defects': major,
        'minor_defects': minor,
        'measured_values': None,
        'specification_values': None,
        'disposition': disposition,
        'disposition_reason': 'Quality standards met' if inspection_passed else 'Dimensional non-conformance',
        'disposition_by': random.choice([e['employee_id'] for e in master_data['employees'] if e['role'] == 'quality_inspector'] or [master_data['employees'][0]['employee_id']]),
        'ncr_number': f"NCR-{random.randint(1000, 9999)}" if not inspection_passed else None,
        'corrective_action_required': not inspection_passed,
        'inspection_plan_id': f"IP-{random.randint(100, 999)}",
        'inspection_checklist_id': f"CL-{random.randint(100, 999)}",
        'photos_attached': False,
        'approved_by': None,
        'approved_at': None,
        'notes': 'Final inspection completed',
        'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    
    buffers['inspections'].append(inspection)
    stats['quality_inspections'] += 1


def _generate_ebr(wo: dict):
    """Generate electronic batch record"""
    now = datetime.now()
    
    # Handle datetime objects
    if isinstance(wo['actual_start_time'], str):
        manufacturing_date = datetime.strptime(wo['actual_start_time'], '%Y-%m-%d %H:%M:%S').strftime('%Y-%m-%d')
    else:
        manufacturing_date = wo['actual_start_time'].strftime('%Y-%m-%d')
    
    if isinstance(wo['expiry_date'], str):
        expiry_date = wo['expiry_date']
        retest_date = (datetime.strptime(wo['expiry_date'], '%Y-%m-%d') - timedelta(days=30)).strftime('%Y-%m-%d')
    else:
        expiry_date = wo['expiry_date'].strftime('%Y-%m-%d')
        retest_date = (wo['expiry_date'] - timedelta(days=30)).strftime('%Y-%m-%d')
    
    ebr = {
        'ebr_id': generate_id('EBR', 'ebr'),
        'batch_number': wo['batch_number'],
        'product_id': wo['product_id'],
        'work_order_id': wo['work_order_id'],
        'batch_size': wo['produced_quantity'],
        'formula_id': f"FORM-{random.randint(100, 999)}",
        'formula_version': f"v{random.randint(1, 5)}.{random.randint(0, 9)}",
        'manufacturing_date': manufacturing_date,
        'expiration_date': expiry_date,
        'retest_date': retest_date,
        'factory_id': wo['factory_id'],
        'manufacturing_area': f"AREA-{wo['line_id'][-3:]}",
        'record_status': 'approved',
        'prepared_by': wo['created_by'],
        'prepared_at': now.strftime('%Y-%m-%d %H:%M:%S'),
        'reviewed_by': random.choice([e['employee_id'] for e in master_data['employees'] if e['role'] == 'supervisor'] or [master_data['employees'][0]['employee_id']]),
        'reviewed_at': (now + timedelta(hours=1)).strftime('%Y-%m-%d %H:%M:%S'),
        'approved_by': random.choice([e['employee_id'] for e in master_data['employees'] if e['role'] == 'manager'] or [master_data['employees'][0]['employee_id']]),
        'approved_at': (now + timedelta(hours=2)).strftime('%Y-%m-%d %H:%M:%S'),
        'release_status': 'released',
        'released_by': random.choice([e['employee_id'] for e in master_data['employees'] if e['role'] == 'manager'] or [master_data['employees'][0]['employee_id']]),
        'released_at': (now + timedelta(hours=3)).strftime('%Y-%m-%d %H:%M:%S'),
        'has_deviations': False,
        'deviation_count': 0,
        'temperature_min_c': round(random.uniform(18, 22), 2),
        'temperature_max_c': round(random.uniform(24, 28), 2),
        'humidity_min_percentage': round(random.uniform(40, 50), 2),
        'humidity_max_percentage': round(random.uniform(55, 65), 2),
        'regulatory_requirement': 'IATF 16949',
        'audit_trail': None,
        'electronic_signature_applied': True,
        'signature_metadata': None,
        'notes': 'Batch completed successfully',
        'created_at': now.strftime('%Y-%m-%d %H:%M:%S'),
        'updated_at': now.strftime('%Y-%m-%d %H:%M:%S')
    }
    
    buffers['ebrs'].append(ebr)
    stats['ebrs_generated'] += 1


def print_hourly_stats():
    """Print hourly cycle statistics"""
    elapsed = (datetime.now() - stats['start_time']).total_seconds()
    hours = elapsed / 3600
    
    logger.info("="*80)
    logger.info(f"Hourly Cycle Statistics")
    logger.info(f"  Uptime: {hours:.1f} hours")
    logger.info(f"  Cycles Completed: {stats['cycles_completed']}")
    logger.info(f"  Work Orders Created: {stats['work_orders_created']}")
    logger.info(f"  Work Orders Completed: {stats['work_orders_completed']}")
    logger.info(f"  Material Transactions: {stats['material_transactions']}")
    logger.info(f"  Quality Inspections: {stats['quality_inspections']}")
    logger.info(f"  Labor Entries: {stats['labor_entries']}")
    logger.info(f"  eBRs Generated: {stats['ebrs_generated']}")
    logger.info(f"  Errors: {stats['errors']}")
    logger.info("="*80)


# ============================================================================
# MAIN DAEMON LOOP
# ============================================================================

def main():
    """Main daemon loop"""
    logger.info("="*80)
    logger.info("GenIMS MES Hourly Production Daemon Starting")
    logger.info("="*80)
    logger.info(f"Configuration:")
    logger.info(f"  Database: {PG_DATABASE}")
    logger.info(f"  Host: {PG_HOST}:{PG_PORT}")
    logger.info(f"  SSL Mode: {PG_SSL_MODE}")
    logger.info(f"  Cycle Interval: {CYCLE_INTERVAL_SECONDS}s")
    logger.info(f"  Batch Size: {BATCH_SIZE}")
    logger.info(f"  Log File: {log_file}")
    logger.info("="*80)
    
    # Initialize
    if not initialize_database():
        return 1
    
    if not load_master_data():
        logger.error("Failed to load master data. Cannot start daemon.")
        logger.error("Please ensure master data is populated by running: python3 scripts/full_setup.py")
        return 1
    
    # Validate critical master data
    if not master_data.get('products'):
        logger.error("No products found in master data. Cannot create work orders.")
        logger.error("Please populate products table in genims_master_db.")
        return 1
    
    if not master_data.get('mappings'):
        logger.error("No line-product mappings found. Cannot assign products to lines.")
        logger.error("Please populate line_product_mapping table in genims_master_db.")
        return 1
    
    if not master_data.get('employees'):
        logger.warning("No employees found in master data. Some features may be limited.")
    
    logger.info(f"Master data validation passed.")
    logger.info(f"Cycle interval: {CYCLE_INTERVAL_SECONDS} seconds (1 hour)")
    logger.info("Press Ctrl+C to stop")
    logger.info("="*80)
    
    last_cycle = datetime.now() - timedelta(hours=2)  # Force initial run
    
    while running:
        try:
            now = datetime.now()
            
            # Run cycle every hour
            if (now - last_cycle).total_seconds() >= CYCLE_INTERVAL_SECONDS:
                current_time = now.strftime('%Y-%m-%d %H:%M:%S')
                
                logger.info(f"\n{'='*80}")
                logger.info(f"Hourly Production Cycle - {current_time}")
                logger.info(f"Hour: {now.hour:02d}:00")
                logger.info(f"{'='*80}")
                
                # Ensure connection is alive
                if not check_connection():
                    logger.error("Failed to establish database connection for this cycle")
                    time.sleep(60)  # Wait 1 minute before retrying
                    continue
                
                # Determine activity level
                new_orders = determine_hourly_capacity()
                logger.info(f"Activity level: {new_orders} new orders this hour")
                
                # Execute production cycle
                create_new_work_orders(new_orders)
                start_scheduled_orders()
                update_in_progress_orders()
                complete_finished_orders()
                
                # Flush all buffers
                flush_buffers()
                
                stats['cycles_completed'] += 1
                last_cycle = now
                
                logger.info(f"Cycle complete. Next cycle in {CYCLE_INTERVAL_SECONDS}s")
                
                # Print stats every 6 hours
                if stats['cycles_completed'] % 6 == 0:
                    print_hourly_stats()
            
            # Check every minute (keeps connection alive)
            time.sleep(60)
            
        except Exception as e:
            logger.error(f"Error in main loop: {e}", exc_info=True)
            stats['errors'] += 1
            time.sleep(60)  # Wait 1 minute before retrying
    
    # Cleanup
    logger.info("Shutting down...")
    flush_buffers()
    
    if pg_connection:
        pg_connection.close()
        logger.info("PostgreSQL connection closed")
    
    print_hourly_stats()
    logger.info("MES Hourly Daemon stopped")
    
    return 0


if __name__ == "__main__":
    import os
    os.makedirs('logs', exist_ok=True)
    sys.exit(main())
