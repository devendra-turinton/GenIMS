#!/usr/bin/env python3
"""
GenIMS CMMS Daemon - ULTRA FAST MODE
Generates complete maintenance operations in-memory, then bulk dumps to PostgreSQL
"""

import sys
import os
import time
import logging
import signal
from datetime import datetime, timedelta
import random
from dotenv import load_dotenv

env_file = os.path.join(os.path.dirname(__file__), '..', '..', 'scripts', 'config.env')
if os.path.exists(env_file):
    load_dotenv(env_file)

try:
    import psycopg2
    from psycopg2.extras import execute_batch
    POSTGRES_AVAILABLE = True
except ImportError:
    POSTGRES_AVAILABLE = False

# Configuration
PG_HOST = os.getenv('POSTGRES_HOST', 'localhost')
PG_PORT = int(os.getenv('POSTGRES_PORT', '5432'))
PG_USER = os.getenv('POSTGRES_USER', 'postgres')
PG_PASSWORD = os.getenv('POSTGRES_PASSWORD', '')
PG_SSL_MODE = os.getenv('PG_SSL_MODE', 'require')

PG_MAINTENANCE_DB = os.getenv('DB_MAINTENANCE', 'genims_maintenance_db')
PG_MASTER_DB = os.getenv('DB_MASTER', 'genims_master_db')
PG_ERP_DB = os.getenv('DB_ERP', 'genims_erp_db')
PG_WMS_DB = os.getenv('DB_WMS', 'genims_wms_db')
PG_MES_DB = os.getenv('DB_MANUFACTURING', 'genims_manufacturing_db')

BATCH_SIZE = 5000
TOTAL_RECORDS = 14400  # 10 days of hourly maintenance records

# Logging
log_dir = os.getenv('DAEMON_LOG_DIR', os.path.join(os.path.dirname(__file__), '..', '..', 'logs'))
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, 'cmms_daemon.log')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('CMMSDaemon')

# Global State
pg_connection = None
pg_master_connection = None
pg_erp_connection = None
pg_wms_connection = None
master_data = {}
valid_asset_ids = set()
valid_technician_ids = set()
valid_machine_ids = set()
valid_warehouse_ids = set()
valid_supplier_ids = set()
counters = {
    'work_order': 1, 'task': 1, 'pm_schedule': 1, 'labor_entry': 1, 'meter_reading': 1
}

def signal_handler(sig, frame):
    logger.info("Shutdown signal received")
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

def _get_max_timestamp():
    """Get maximum timestamp from maintenance transactions and prevent future dates"""
    try:
        cursor = pg_connection.cursor()
        cursor.execute("""
            SELECT MAX(GREATEST(
                COALESCE(actual_end_date, '1900-01-01'::timestamp),
                COALESCE(created_at, '1900-01-01'::timestamp)
            )) FROM work_orders
        """)
        max_ts = cursor.fetchone()[0]
        cursor.close()
        
        # Prevent future dates
        current_time = datetime.now()
        if max_ts and max_ts > current_time:
            logger.warning(f"Found future timestamp {max_ts}, using current date instead")
            return current_time
        return max_ts or current_time
    except Exception as e:
        logger.warning(f"Could not get max timestamp: {e}, using current time")
        return datetime.now()

def initialize_database():
    global pg_connection, pg_master_connection, pg_erp_connection, pg_wms_connection
    if not POSTGRES_AVAILABLE:
        return False
    try:
        # Main CMMS database connection
        pg_connection = psycopg2.connect(
            host=PG_HOST, port=PG_PORT, database=PG_MAINTENANCE_DB,
            user=PG_USER, password=PG_PASSWORD, sslmode=PG_SSL_MODE, connect_timeout=30
        )
        pg_connection.autocommit = False
        logger.info(f"PostgreSQL CMMS connection established: {PG_HOST}:{PG_PORT}/{PG_MAINTENANCE_DB}")
        
        # Cross-database connections for FK validation
        try:
            pg_master_connection = psycopg2.connect(
                host=PG_HOST, port=PG_PORT, database=PG_MASTER_DB,
                user=PG_USER, password=PG_PASSWORD, sslmode=PG_SSL_MODE, connect_timeout=30
            )
            logger.info(f"Master DB connection established: {PG_MASTER_DB}")
        except Exception as e:
            logger.warning(f"Master DB connection failed: {e}")
            
        try:
            pg_erp_connection = psycopg2.connect(
                host=PG_HOST, port=PG_PORT, database=PG_ERP_DB,
                user=PG_USER, password=PG_PASSWORD, sslmode=PG_SSL_MODE, connect_timeout=30
            )
            logger.info(f"ERP DB connection established: {PG_ERP_DB}")
        except Exception as e:
            logger.warning(f"ERP DB connection failed: {e}")
            
        try:
            pg_wms_connection = psycopg2.connect(
                host=PG_HOST, port=PG_PORT, database=PG_WMS_DB,
                user=PG_USER, password=PG_PASSWORD, sslmode=PG_SSL_MODE, connect_timeout=30
            )
            logger.info(f"WMS DB connection established: {PG_WMS_DB}")
        except Exception as e:
            logger.warning(f"WMS DB connection failed: {e}")
        
        # Initialize time coordination
        _get_max_timestamp()
        
        return True
    except Exception as e:
        logger.error(f"PostgreSQL connection failed: {e}")
        return False

def get_table_count(table_name):
    try:
        conn = psycopg2.connect(host=PG_HOST, port=PG_PORT, database=PG_MAINTENANCE_DB,
            user=PG_USER, password=PG_PASSWORD, sslmode=PG_SSL_MODE, connect_timeout=10)
        cursor = conn.cursor()
        cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
        count = cursor.fetchone()[0]
        cursor.close()
        conn.close()
        return count
    except Exception as e:
        logger.warning(f"Could not get {table_name} count: {e}")
        return None

def get_all_table_counts():
    tables = ['work_orders', 'work_order_tasks', 'pm_schedules', 'labor_time_entries', 'equipment_meter_readings']
    counts = {}
    for table in tables:
        counts[table] = get_table_count(table)
    return counts

def get_max_id_counter(table_name, id_column):
    """Get the next ID counter for a given table"""
    try:
        cursor = pg_connection.cursor()
        cursor.execute(f"SELECT MAX(CAST(SUBSTRING({id_column}, '\\d+$') AS INTEGER)) FROM {table_name}")
        max_id = cursor.fetchone()[0]
        cursor.close()
        return (max_id or 0) + 1
    except Exception as e:
        logger.debug(f"Could not get max ID from {table_name}.{id_column}: {e}")
        return 1

def initialize_id_counters():
    """Initialize counters from existing data in database"""
    global counters
    try:
        counters['work_order'] = get_max_id_counter('work_orders', 'work_order_id')
        counters['task'] = get_max_id_counter('work_order_tasks', 'task_id')
        counters['pm_schedule'] = get_max_id_counter('pm_schedules', 'pm_schedule_id')
        counters['labor_entry'] = get_max_id_counter('labor_time_entries', 'entry_id')
        counters['meter_reading'] = get_max_id_counter('equipment_meter_readings', 'reading_id')
        
        logger.info(f"ID Counters initialized: {counters}")
        return True
    except Exception as e:
        logger.error(f"Failed to initialize ID counters: {e}")
        return False

def load_master_data():
    global master_data, valid_asset_ids, valid_technician_ids, valid_machine_ids, valid_warehouse_ids, valid_supplier_ids
    try:
        # Load assets from CMMS (these should exist from historical generation)
        cmms_cursor = pg_connection.cursor()
        try:
            cmms_cursor.execute("SELECT asset_id FROM maintenance_assets WHERE is_active = true LIMIT 100")
            assets = [row[0] for row in cmms_cursor.fetchall()]
            valid_asset_ids = set(assets)
            
            # Load technicians from CMMS
            cmms_cursor.execute("SELECT technician_id FROM maintenance_technicians WHERE is_active = true LIMIT 50")
            technicians = [row[0] for row in cmms_cursor.fetchall()]
            valid_technician_ids = set(technicians)
        except Exception as e:
            logger.error(f"Error loading CMMS data: {e}")
            # Rollback the transaction if there's an error
            pg_connection.rollback()
            assets, technicians = [], []
            valid_asset_ids, valid_technician_ids = set(), set()
        finally:
            cmms_cursor.close()
        
        # Load machines from Master DB for FK validation
        if pg_master_connection:
            try:
                master_cursor = pg_master_connection.cursor()
                master_cursor.execute("SELECT machine_id FROM machines LIMIT 1000")
                machines = [row[0] for row in master_cursor.fetchall()]
                valid_machine_ids = set(machines)
                master_cursor.close()
                logger.info(f"Loaded {len(machines)} machines from master DB")
            except Exception as e:
                logger.warning(f"Could not load from master DB: {e}")
                valid_machine_ids = set()
        
        # Load warehouses from WMS for FK validation
        if pg_wms_connection:
            try:
                wms_cursor = pg_wms_connection.cursor()
                wms_cursor.execute("SELECT warehouse_id FROM warehouses WHERE is_active = true")
                warehouses = [row[0] for row in wms_cursor.fetchall()]
                valid_warehouse_ids = set(warehouses)
                wms_cursor.close()
                logger.info(f"Loaded {len(warehouses)} warehouses from WMS DB")
            except Exception as e:
                logger.warning(f"Could not load from WMS DB: {e}")
                valid_warehouse_ids = set()
        
        # Load suppliers from ERP for FK validation
        if pg_erp_connection:
            try:
                erp_cursor = pg_erp_connection.cursor()
                erp_cursor.execute("SELECT supplier_id FROM suppliers WHERE supplier_status = 'active'")
                suppliers = [row[0] for row in erp_cursor.fetchall()]
                valid_supplier_ids = set(suppliers)
                erp_cursor.close()
                logger.info(f"Loaded {len(suppliers)} suppliers from ERP DB")
            except Exception as e:
                logger.warning(f"Could not load from ERP DB: {e}")
                valid_supplier_ids = set()
        
        # Create fallbacks if external connections failed
        if not valid_asset_ids:
            valid_asset_ids = set([f"ASSET-{i:06d}" for i in range(1, 101)])
            assets = list(valid_asset_ids)
        if not valid_technician_ids:
            valid_technician_ids = set([f"TECH-{i:06d}" for i in range(1, 21)])
            technicians = list(valid_technician_ids)
        if not valid_machine_ids:
            valid_machine_ids = set([f"MACH-{i:06d}" for i in range(1, 51)])
        if not valid_warehouse_ids:
            valid_warehouse_ids = set([f"WH-{i:06d}" for i in range(1, 11)])
        if not valid_supplier_ids:
            valid_supplier_ids = set([f"SUP-{i:06d}" for i in range(1, 31)])
        
        master_data['assets'] = assets
        master_data['technicians'] = technicians
        
        logger.info(f"Master data loaded: {len(assets)} assets, {len(technicians)} technicians")
        logger.info(f"FK validation sets: {len(valid_machine_ids)} machines, {len(valid_warehouse_ids)} warehouses, {len(valid_supplier_ids)} suppliers")
        return True
    except Exception as e:
        logger.error(f"Failed to load master data: {e}")
        return False

def validate_foreign_key(fk_type: str, fk_value: str) -> str:
    """Validate foreign key and return valid value or fallback"""
    if fk_type == 'asset_id' and fk_value in valid_asset_ids:
        return fk_value
    elif fk_type == 'technician_id' and fk_value in valid_technician_ids:
        return fk_value
    elif fk_type == 'machine_id' and fk_value in valid_machine_ids:
        return fk_value
    elif fk_type == 'warehouse_id' and fk_value in valid_warehouse_ids:
        return fk_value
    elif fk_type == 'supplier_id' and fk_value in valid_supplier_ids:
        return fk_value
    else:
        # Return fallback valid value
        if fk_type == 'asset_id' and valid_asset_ids:
            return random.choice(list(valid_asset_ids))
        elif fk_type == 'technician_id' and valid_technician_ids:
            return random.choice(list(valid_technician_ids))
        elif fk_type == 'machine_id' and valid_machine_ids:
            return random.choice(list(valid_machine_ids))
        elif fk_type == 'warehouse_id' and valid_warehouse_ids:
            return random.choice(list(valid_warehouse_ids))
        elif fk_type == 'supplier_id' and valid_supplier_ids:
            return random.choice(list(valid_supplier_ids))
        return fk_value  # Return original if no fallback available

def insert_batch_parallel(cursor, insert_sql, data, table_name, batch_size, connection=None):
    """Insert data in batches"""
    total_batches = (len(data) + batch_size - 1) // batch_size
    
    for batch_idx in range(total_batches):
        try:
            batch_start = batch_idx * batch_size
            batch_end = min((batch_idx + 1) * batch_size, len(data))
            batch = data[batch_start:batch_end]
            
            execute_batch(cursor, insert_sql, batch, page_size=5000)
            if connection:
                connection.commit()
            
            logger.info(f"  Flushed {batch_end:,} / {len(data):,} {table_name}")
        except psycopg2.IntegrityError as e:
            logger.warning(f"  Batch {batch_idx + 1}/{total_batches} - Integrity error, skipping")
            if connection:
                connection.rollback()
        except Exception as e:
            logger.error(f"  Batch {batch_idx + 1}/{total_batches} error: {e}")
            if connection:
                connection.rollback()

def main():
    """Main - Generate all CMMS data in-memory, then bulk dump"""
    logger.info("="*80)
    logger.info("GenIMS CMMS Daemon - ULTRA FAST MODE (In-Memory Generation)")
    logger.info("="*80)
    logger.info(f"Configuration:")
    logger.info(f"  Database: {PG_MAINTENANCE_DB}")
    logger.info(f"  Batch Size: {BATCH_SIZE}")
    logger.info("="*80)
    
    start_time = time.time()
    
    # Initialize
    if not initialize_database():
        return 1
    
    if not initialize_id_counters():
        return 1
    
    if not load_master_data():
        return 1
    
    logger.info("="*80)
    logger.info("📊 BASELINE DATABASE COUNTS (Before Generation)")
    logger.info("="*80)
    counts_before = get_all_table_counts()
    for table, count in counts_before.items():
        if count is not None:
            logger.info(f"  {table:.<40} {count:>10,} records")
    logger.info("="*80)
    
    logger.info("="*80)
    logger.info("GENERATING ALL DATA IN MEMORY...")
    logger.info("="*80)
    
    # Generate data
    work_orders = []
    work_order_tasks = []
    labor_entries = []
    meter_readings = []
    
    # Time coordination: Start from last transaction or current time
    base_time = _get_max_timestamp()
    sim_base_time = base_time.replace(minute=0, second=0, microsecond=0)  # Round to hour
    run_timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    
    logger.info(f"CMMS simulation will start from: {sim_base_time}")
    
    # Generate CMMS records (1 per hour = 14,400 records over 600 days)
    for i in range(TOTAL_RECORDS):
        timestamp_offset = i * 3600  # 1 hour per record
        current_ts = sim_base_time + timedelta(seconds=timestamp_offset)
        
        # Validate and get asset
        asset = random.choice(master_data['assets'])
        asset = validate_foreign_key('asset_id', asset)
        
        # Work orders (1 per 50 records = ~288/10 days)
        if i % 50 == 0:
            wo_id = f"WO-{(counters['work_order'] + i // 50):06d}"
            
            # Assign technician if available
            assigned_technician = None
            if master_data.get('technicians'):
                assigned_technician = validate_foreign_key('technician_id', random.choice(master_data['technicians']))
            
            # Enhanced work order with FK validation
            work_order = {
                'work_order_id': wo_id,
                'work_order_number': f"WO-{run_timestamp}-{i // 50:04d}",
                'asset_id': asset,
                'wo_type': random.choice(['preventive', 'corrective', 'predictive', 'breakdown']),
                'priority': random.choice(['low', 'medium', 'high', 'urgent', 'emergency']),
                'description': f"Maintenance work for {asset} - {random.choice(['Inspection', 'Repair', 'Service', 'Calibration'])}",
                'scheduled_start_date': current_ts.date(),
                'scheduled_end_date': (current_ts + timedelta(days=random.randint(1, 3))).date(),
                'estimated_duration_hours': round(random.uniform(1, 16), 2),
                'wo_status': random.choice(['created', 'planned', 'in_progress', 'completed']),
                'assigned_to': assigned_technician,
                'created_at': current_ts
            }
            work_orders.append(work_order)
        
        # Work order tasks (1 per 20 records)
        if i % 20 == 0:
            # Find recent WO for this task
            wo_idx = (i // 50) if (i // 50) < len(work_orders) else len(work_orders) - 1
            wo_id = work_orders[wo_idx]['work_order_id'] if work_orders else f"WO-{(counters['work_order'] + i // 50):06d}"
            
            task_id = f"TASK-{(counters['task'] + i // 20):06d}"
            task = {
                'task_id': task_id,
                'work_order_id': wo_id,
                'task_sequence': (i % 20) // 5 + 1,
                'task_description': f"{random.choice(['Inspect', 'Lubricate', 'Replace', 'Adjust', 'Test', 'Calibrate'])} {random.choice(['bearing', 'motor', 'sensor', 'valve', 'filter'])}",
                'task_type': random.choice(['inspection', 'preventive', 'corrective', 'calibration']),
                'task_status': random.choice(['pending', 'in_progress', 'completed', 'verified']),
                'estimated_duration_minutes': random.randint(15, 240),
                'created_at': current_ts,
                'started_at': current_ts + timedelta(minutes=random.randint(0, 30)),
                'completed_at': current_ts + timedelta(hours=random.randint(1, 4)) if random.random() < 0.7 else None
            }
            work_order_tasks.append(task)
        
        # Labor entries (1 per 100 records)
        if i % 100 == 0 and master_data.get('technicians'):
            entry_id = f"LABOR-{(counters['labor_entry'] + i // 100):06d}"
            wo_idx = (i // 50) if (i // 50) < len(work_orders) else len(work_orders) - 1
            wo_id = work_orders[wo_idx]['work_order_id'] if work_orders else f"WO-{(counters['work_order'] + i // 50):06d}"
            
            # Validate technician FK
            technician_id = random.choice(master_data['technicians'])
            technician_id = validate_foreign_key('technician_id', technician_id)
            
            duration = round(random.uniform(1, 8), 2)
            hourly_rate = round(random.uniform(500, 1500), 2)
            
            labor_entry = {
                'entry_id': entry_id,
                'work_order_id': wo_id,
                'technician_id': technician_id,
                'start_time': current_ts,
                'end_time': current_ts + timedelta(hours=duration),
                'duration_hours': duration,
                'labor_type': random.choice(['regular', 'overtime', 'emergency', 'specialist']),
                'hourly_rate': hourly_rate,
                'labor_cost': round(duration * hourly_rate, 2),
                'approved': random.choice([True, False]),
                'created_at': current_ts
            }
            labor_entries.append(labor_entry)
        
        # Meter readings (1 per 10 records)
        if i % 10 == 0:
            reading_id = f"MTR-{(counters['meter_reading'] + i // 10):06d}"
            
            # Validate asset FK
            asset_for_reading = validate_foreign_key('asset_id', asset)
            
            # More realistic meter progression
            base_reading = 1000 + (i * 0.5)  # Progressive reading
            delta = round(random.uniform(0.5, 10), 2)
            
            meter_reading = {
                'reading_id': reading_id,
                'asset_id': asset_for_reading,
                'reading_date': current_ts,
                'meter_value': round(base_reading + delta, 2),
                'meter_unit': random.choice(['hours', 'km', 'cycles', 'units_produced']),
                'previous_reading': round(base_reading, 2),
                'delta_value': delta,
                'days_since_last_reading': 1 if i > 0 else 0,
                'reading_source': random.choice(['manual', 'automated', 'iot', 'calculated']),
                'created_at': current_ts
            }
            meter_readings.append(meter_reading)
        
        if (i + 1) % 1000 == 0:
            logger.info(f"  Generated {i + 1:,} / {TOTAL_RECORDS:,} records")
    
    logger.info(f"✓ Generated {len(work_orders):,} work orders")
    logger.info(f"✓ Generated {len(work_order_tasks):,} work order tasks")
    logger.info(f"✓ Generated {len(labor_entries):,} labor entries")
    logger.info(f"✓ Generated {len(meter_readings):,} meter readings")
    
    # Bulk dump to PostgreSQL
    logger.info("="*80)
    logger.info("BULK DUMPING TO POSTGRESQL...")
    logger.info("="*80)
    
    try:
        cursor = pg_connection.cursor()
        cursor.execute("SET CONSTRAINTS ALL DEFERRED;")
        
        # Insert work_orders
        if work_orders:
            insert_sql = """INSERT INTO work_orders (
                work_order_id, work_order_number, asset_id, wo_type, priority,
                description, scheduled_start_date, scheduled_end_date,
                estimated_duration_hours, wo_status, assigned_to, created_at
            ) VALUES (%(work_order_id)s, %(work_order_number)s, %(asset_id)s, %(wo_type)s,
                %(priority)s, %(description)s, %(scheduled_start_date)s,
                %(scheduled_end_date)s, %(estimated_duration_hours)s, %(wo_status)s, 
                %(assigned_to)s, %(created_at)s)"""
            logger.info(f"Inserting {len(work_orders):,} work orders...")
            insert_batch_parallel(cursor, insert_sql, work_orders, "work orders", BATCH_SIZE, pg_connection)
        
        # Insert work_order_tasks
        if work_order_tasks:
            insert_sql = """INSERT INTO work_order_tasks (
                task_id, work_order_id, task_sequence, task_description,
                task_type, task_status, estimated_duration_minutes, created_at,
                started_at, completed_at
            ) VALUES (%(task_id)s, %(work_order_id)s, %(task_sequence)s,
                %(task_description)s, %(task_type)s, %(task_status)s,
                %(estimated_duration_minutes)s, %(created_at)s,
                %(started_at)s, %(completed_at)s)"""
            logger.info(f"Inserting {len(work_order_tasks):,} work order tasks...")
            insert_batch_parallel(cursor, insert_sql, work_order_tasks, "work order tasks", BATCH_SIZE, pg_connection)
        
        # Insert labor_entries
        if labor_entries:
            insert_sql = """INSERT INTO labor_time_entries (
                entry_id, work_order_id, technician_id, start_time, end_time,
                duration_hours, labor_type, hourly_rate, labor_cost, approved, created_at
            ) VALUES (%(entry_id)s, %(work_order_id)s, %(technician_id)s, %(start_time)s,
                %(end_time)s, %(duration_hours)s, %(labor_type)s, %(hourly_rate)s,
                %(labor_cost)s, %(approved)s, %(created_at)s)"""
            logger.info(f"Inserting {len(labor_entries):,} labor entries...")
            insert_batch_parallel(cursor, insert_sql, labor_entries, "labor entries", BATCH_SIZE, pg_connection)
        
        # Insert meter_readings
        if meter_readings:
            insert_sql = """INSERT INTO equipment_meter_readings (
                reading_id, asset_id, reading_date, meter_value, meter_unit,
                previous_reading, delta_value, days_since_last_reading, reading_source, 
                created_at
            ) VALUES (%(reading_id)s, %(asset_id)s, %(reading_date)s, %(meter_value)s,
                %(meter_unit)s, %(previous_reading)s, %(delta_value)s, %(days_since_last_reading)s,
                %(reading_source)s, %(created_at)s)"""
            logger.info(f"Inserting {len(meter_readings):,} meter readings...")
            insert_batch_parallel(cursor, insert_sql, meter_readings, "meter readings", BATCH_SIZE, pg_connection)
        
        cursor.close()
        
        # Commit all data
        pg_connection.commit()
        
        logger.info(f"✓ All records inserted successfully")
    except Exception as e:
        logger.error(f"PostgreSQL error: {e}")
        return 1
    
    elapsed = time.time() - start_time
    
    # Get final counts
    counts_after = get_all_table_counts()
    
    logger.info("="*80)
    logger.info("GENERATION & INSERTION COMPLETE")
    logger.info("="*80)
    logger.info(f"  Total time: {elapsed:.1f} seconds ({elapsed/60:.1f} minutes)")
    logger.info("")
    logger.info("📊 DATABASE SUMMARY")
    logger.info("="*80)
    
    tables_list = ['work_orders', 'work_order_tasks', 'labor_time_entries', 'equipment_meter_readings']
    for table in tables_list:
        before = counts_before.get(table)
        after = counts_after.get(table)
        
        if before is not None and after is not None:
            inserted = after - before
            logger.info(f"{table:.<35} Before: {before:>10,} | After: {after:>10,} | Inserted: {inserted:>10,}")
    
    logger.info("="*80)
    
    # Close all connections
    if pg_connection:
        pg_connection.close()
    if pg_master_connection:
        pg_master_connection.close()
    if pg_erp_connection:
        pg_erp_connection.close()
    if pg_wms_connection:
        pg_wms_connection.close()
    
    return 0

if __name__ == "__main__":
    os.makedirs('logs', exist_ok=True)
    sys.exit(main())
