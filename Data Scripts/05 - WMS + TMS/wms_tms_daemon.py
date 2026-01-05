#!/usr/bin/env python3
"""
GenIMS WMS + TMS Daemon - ULTRA FAST MODE
Generates complete warehouse and logistics operations in-memory, then bulk dumps to PostgreSQL
"""

import sys
import os
import time
import logging
import signal
from datetime import datetime, timedelta
import random
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor, as_completed

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

PG_MASTER_DB = os.getenv('DB_MASTER', 'genims_master_db')
PG_WMS_DB = os.getenv('DB_WMS', 'genims_wms_db')
PG_TMS_DB = os.getenv('DB_TMS', 'genims_tms_db')

WMS_BATCH_SIZE = 5000
TMS_BATCH_SIZE = 5000
WMS_TOTAL_RECORDS = 28800
TMS_TOTAL_RECORDS = 5760

# Logging
log_dir = os.getenv('DAEMON_LOG_DIR', os.path.join(os.path.dirname(__file__), '..', '..', 'logs'))
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, 'wms_tms_daemon.log')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('WMSTMSDaemon')

# Global State
pg_wms_connection = None
pg_tms_connection = None
master_data = {}
carrier_ids = []
counters = {'wave': 1, 'receiving_task': 1, 'picking_task': 1, 'packing_task': 1, 'shipping_task': 1,
            'sales_order': 1, 'shipment': 1, 'tracking_event': 1, 'delivery': 1, 'route': 1}

def signal_handler(sig, frame):
    logger.info("Shutdown signal received")
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

def initialize_database():
    global pg_wms_connection, pg_tms_connection
    if not POSTGRES_AVAILABLE:
        return False
    try:
        pg_wms_connection = psycopg2.connect(
            host=PG_HOST, port=PG_PORT, database=PG_WMS_DB,
            user=PG_USER, password=PG_PASSWORD, sslmode=PG_SSL_MODE, connect_timeout=30
        )
        pg_wms_connection.autocommit = False
        logger.info(f"PostgreSQL WMS connection established: {PG_HOST}:{PG_PORT}/{PG_WMS_DB}")
        
        pg_tms_connection = psycopg2.connect(
            host=PG_HOST, port=PG_PORT, database=PG_TMS_DB,
            user=PG_USER, password=PG_PASSWORD, sslmode=PG_SSL_MODE, connect_timeout=30
        )
        pg_tms_connection.autocommit = False
        logger.info(f"PostgreSQL TMS connection established: {PG_HOST}:{PG_PORT}/{PG_TMS_DB}")
        
        return True
    except Exception as e:
        logger.error(f"PostgreSQL connection failed: {e}")
        return False

def get_table_count(table_name, database=None):
    if database is None:
        database = PG_WMS_DB
    try:
        conn = psycopg2.connect(host=PG_HOST, port=PG_PORT, database=database,
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
    wms_tables = ['pick_waves', 'receiving_tasks', 'picking_tasks', 'packing_tasks', 'shipping_tasks']
    tms_tables = ['shipments', 'tracking_events', 'deliveries', 'routes']
    counts = {}
    for table in wms_tables:
        counts[table] = get_table_count(table, PG_WMS_DB)
    for table in tms_tables:
        counts[table] = get_table_count(table, PG_TMS_DB)
    return counts

def load_master_data():
    global master_data, carrier_ids
    try:
        # Load warehouses from WMS database
        wms_conn = psycopg2.connect(
            host=PG_HOST, port=PG_PORT, database=PG_WMS_DB,
            user=PG_USER, password=PG_PASSWORD, sslmode=PG_SSL_MODE, connect_timeout=30
        )
        wms_cursor = wms_conn.cursor()
        
        wms_cursor.execute("SELECT warehouse_id FROM warehouses WHERE is_active = true LIMIT 10")
        warehouses = [row[0] for row in wms_cursor.fetchall()]
        wms_cursor.close()
        wms_conn.close()
        
        # Load carriers from TMS database (for shipments.carrier_id NOT NULL constraint)
        tms_conn = psycopg2.connect(
            host=PG_HOST, port=PG_PORT, database=PG_TMS_DB,
            user=PG_USER, password=PG_PASSWORD, sslmode=PG_SSL_MODE, connect_timeout=30
        )
        tms_cursor = tms_conn.cursor()
        
        tms_cursor.execute("SELECT carrier_id FROM carriers LIMIT 20")
        carrier_ids = [row[0] for row in tms_cursor.fetchall()]
        tms_cursor.close()
        tms_conn.close()
        
        # Load products from Folder 01 master data JSON (use as materials)
        import json
        folder_01_path = os.path.join(os.path.dirname(__file__), '..', '01 - Base Data', 'genims_master_data.json')
        master_data_path = os.path.abspath(folder_01_path)
        
        with open(master_data_path, 'r') as f:
            master_json = json.load(f)
        
        # Use products as materials, and get customers for delivery info
        products = master_json.get('products', [])
        customers = master_json.get('customers', [])
        
        materials = [{'material_id': p['product_id'], 'product_name': p.get('product_name', 'Unknown')} 
                     for p in products]
        
        master_data['warehouses'] = warehouses or ['WH-000001', 'WH-000002', 'WH-000003']
        master_data['materials'] = materials or []
        master_data['customers'] = customers or []
        
        logger.info(f"Master data loaded: {len(warehouses)} warehouses, {len(materials)} materials, {len(customers)} customers, {len(carrier_ids)} carriers")
        return True
    except Exception as e:
        logger.error(f"Failed to load master data: {e}")
        return False


def get_max_id_counter(table_name, id_column, connection):
    """Get the next ID counter for a given table"""
    try:
        cursor = connection.cursor()
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
        # WMS counters
        counters['wave'] = get_max_id_counter('pick_waves', 'wave_id', pg_wms_connection)
        counters['receiving_task'] = get_max_id_counter('receiving_tasks', 'receiving_task_id', pg_wms_connection)
        counters['picking_task'] = get_max_id_counter('picking_tasks', 'picking_task_id', pg_wms_connection)
        counters['packing_task'] = get_max_id_counter('packing_tasks', 'packing_task_id', pg_wms_connection)
        counters['shipping_task'] = get_max_id_counter('shipping_tasks', 'shipping_task_id', pg_wms_connection)
        
        # TMS counters
        counters['shipment'] = get_max_id_counter('shipments', 'shipment_id', pg_tms_connection)
        counters['tracking_event'] = get_max_id_counter('tracking_events', 'event_id', pg_tms_connection)
        counters['delivery'] = get_max_id_counter('deliveries', 'delivery_id', pg_tms_connection)
        counters['route'] = get_max_id_counter('routes', 'route_id', pg_tms_connection)
        
        # Sales order counter (synthetic - use max from any previous run or start at 1)
        counters['sales_order'] = 1
        
        logger.info(f"ID Counters initialized: {counters}")
        return True
    except Exception as e:
        logger.error(f"Failed to initialize ID counters: {e}")
        return False

def insert_batch_parallel(cursor, insert_sql, data, table_name, batch_size, connection=None, max_workers=3):
    """Insert data in parallel batches with sequential execution (PostgreSQL thread safety)"""
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
        except psycopg2.IntegrityError:
            logger.warning(f"  Batch {batch_idx + 1}/{total_batches} - Integrity error, skipping")
            if connection:
                connection.rollback()
        except Exception as e:
            logger.error(f"  Batch {batch_idx + 1}/{total_batches} error: {e}")
            if connection:
                connection.rollback()

def main():
    """Main - Generate all WMS + TMS data in-memory, then bulk dump"""
    logger.info("="*80)
    logger.info("GenIMS WMS + TMS Daemon - ULTRA FAST MODE (In-Memory Generation)")
    logger.info("="*80)
    logger.info(f"Configuration:")
    logger.info(f"  Databases: {PG_WMS_DB} (WMS), {PG_TMS_DB} (TMS)")
    logger.info(f"  WMS Batch Size: {WMS_BATCH_SIZE}")
    logger.info(f"  TMS Batch Size: {TMS_BATCH_SIZE}")
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
    
    # Generate WMS data
    pick_waves = []
    receiving_tasks = []
    picking_tasks = []
    packing_tasks = []
    shipping_tasks = []
    
    # Generate TMS data
    shipments = []
    tracking_events = []
    deliveries = []
    routes = []
    
    sim_base_time = datetime.strptime(datetime.now().strftime('%Y-%m-%d 00:00:00'), '%Y-%m-%d %H:%M:%S')
    run_timestamp = datetime.now().strftime('%Y%m%d%H%M%S')  # Unique per run
    
    # Generate WMS records
    for i in range(WMS_TOTAL_RECORDS):
        timestamp_offset = i * 300  # 5 minutes per record
        current_ts = sim_base_time + timedelta(seconds=timestamp_offset)
        
        warehouse_id = random.choice(master_data['warehouses'])
        material = random.choice(master_data['materials'])
        
        # Pick waves (1 per 100 records)
        if i % 100 == 0:
            wave_id = f"WAVE-{(counters['wave'] + i // 100):06d}"
            pick_waves.append({
                'wave_id': wave_id,
                'wave_number': f"WAVE-{run_timestamp}-{i // 100:04d}",
                'warehouse_id': warehouse_id,
                'wave_type': 'batch',
                'planned_pick_date': current_ts.date(),
                'priority': random.choice(['urgent', 'high', 'normal', 'low']),
                'wave_status': 'created',
                'total_orders': random.randint(3, 10),
                'created_at': current_ts
            })
        
        # Receiving tasks (1 per 200 records)
        if i % 200 == 0:
            task_id = f"RCV-{(counters['receiving_task'] + i // 200):06d}"
            receiving_tasks.append({
                'receiving_task_id': task_id,
                'task_number': f"RCV-{run_timestamp}-{i // 200:04d}",
                'warehouse_id': warehouse_id,
                'material_id': material['material_id'],
                'expected_quantity': random.randint(100, 1000),
                'received_quantity': random.randint(50, 1000),
                'unit_of_measure': 'EA',
                'task_status': 'completed',
                'created_at': current_ts
            })
        
        # Picking tasks (1 per 50 records)
        if i % 50 == 0:
            task_id = f"PICK-{(counters['picking_task'] + i // 50):06d}"
            picking_tasks.append({
                'picking_task_id': task_id,
                'task_number': f"PICK-{run_timestamp}-{i // 50:04d}",
                'warehouse_id': warehouse_id,
                'material_id': material['material_id'],
                'quantity_to_pick': random.randint(10, 100),
                'quantity_picked': random.randint(10, 100),
                'unit_of_measure': 'EA',
                'task_status': random.choice(['pending', 'picked', 'completed']),
                'created_at': current_ts
            })
        
        # Packing tasks (1 per 75 records)
        if i % 75 == 0:
            task_id = f"PACK-{(counters['packing_task'] + i // 75):06d}"
            sales_order_id = f"SO-{(counters['sales_order'] + i // 75):06d}"
            packing_tasks.append({
                'packing_task_id': task_id,
                'task_number': f"PACK-{run_timestamp}-{i // 75:04d}",
                'sales_order_id': sales_order_id,
                'warehouse_id': warehouse_id,
                'packing_station': f"Station-{random.randint(1, 5)}",
                'package_type': random.choice(['box', 'envelope', 'pallet']),
                'package_weight_kg': round(random.uniform(1, 50), 2),
                'task_status': random.choice(['pending', 'packed', 'shipped']),
                'created_at': current_ts
            })
        
        # Shipping tasks (1 per 150 records)
        if i % 150 == 0:
            task_id = f"SHIP-{(counters['shipping_task'] + i // 150):06d}"
            sales_order_id = f"SO-{(counters['sales_order'] + i // 150):06d}"
            shipping_tasks.append({
                'shipping_task_id': task_id,
                'task_number': f"SHIP-{run_timestamp}-{i // 150:04d}",
                'sales_order_id': sales_order_id,
                'warehouse_id': warehouse_id,
                'shipping_dock': f"Dock-{random.randint(1, 3)}",
                'number_of_packages': random.randint(1, 5),
                'total_weight_kg': round(random.uniform(5, 100), 2),
                'task_status': random.choice(['pending', 'shipped', 'in_transit']),
                'scheduled_ship_date': current_ts.date(),
                'actual_ship_date': current_ts.date() if random.random() < 0.7 else None,
                'created_at': current_ts
            })
        
        if (i + 1) % 1000 == 0:
            logger.info(f"  Generated {i + 1:,} / {WMS_TOTAL_RECORDS:,} WMS records")
    
    # Generate TMS records
    for i in range(TMS_TOTAL_RECORDS):
        timestamp_offset = i * 15  # 15 second intervals
        current_ts = sim_base_time + timedelta(seconds=timestamp_offset)
        
        # Shipments (1 per 10 records)
        shipment_id = None
        if i % 10 == 0:
            shipment_id = f"SHPM-{(counters['shipment'] + i // 10):06d}"
            carrier_id = random.choice(carrier_ids) if carrier_ids else 'CAR-000001'
            shipments.append({
                'shipment_id': shipment_id,
                'shipment_number': f"SHPM-{run_timestamp}-{i // 10:04d}",
                'warehouse_id': warehouse_id,
                'carrier_id': carrier_id,
                'tracking_number': f"TRK-{current_ts.strftime('%Y%m%d%H%M%S')}-{i // 10:04d}",
                'bol_number': f"BOL-{current_ts.strftime('%Y%m%d')}-{i // 10:04d}",
                'origin_warehouse_id': warehouse_id,
                'origin_name': f"Warehouse {warehouse_id}",
                'origin_city': random.choice(['Delhi', 'Mumbai', 'Bangalore', 'Chennai', 'Pune']),
                'origin_state': random.choice(['DL', 'MH', 'KA', 'TN', 'MH']),
                'origin_country': 'India',
                'origin_postal_code': f"{random.randint(100000, 999999)}",
                'created_at': current_ts
            })
        else:
            # Link to most recent shipment
            shipment_idx = (i // 10)
            if shipment_idx < len(shipments):
                shipment_id = shipments[shipment_idx]['shipment_id']
        
        # Tracking events (1 per 5 records)
        if i % 5 == 0:
            event_id = f"TRK-{(counters['tracking_event'] + i // 5):06d}"
            tracking_events.append({
                'event_id': event_id,
                'shipment_id': shipment_id or f"SHPM-{(counters['shipment'] + i // 5):06d}",
                'event_type': random.choice(['created', 'picked_up', 'in_transit', 'out_for_delivery', 'delivered']),
                'event_description': 'Shipment status updated',
                'event_timestamp': current_ts,
                'created_at': current_ts
            })
        
        # Deliveries (1 per 20 records)
        if i % 20 == 0:
            delivery_id = f"DEL-{(counters['delivery'] + i // 20):06d}"
            deliveries.append({
                'delivery_id': delivery_id,
                'delivery_number': f"DEL-{run_timestamp}-{i // 20:04d}",
                'shipment_id': shipment_id or f"SHPM-{(counters['shipment'] + i // 20):06d}",
                'actual_delivery_date': current_ts.date() if random.random() < 0.8 else None,
                'delivery_status': random.choice(['pending', 'out_for_delivery', 'delivered']),
                'created_at': current_ts
            })
        
        # Routes (1 per 50 records)
        if i % 50 == 0:
            route_id = f"ROUTE-{(counters['route'] + i // 50):06d}"
            routes.append({
                'route_id': route_id,
                'route_number': f"ROUTE-{run_timestamp}-{i // 50:04d}",
                'route_date': current_ts.date(),
                'route_type': random.choice(['delivery', 'pickup', 'mixed']),
                'number_of_stops': random.randint(5, 25),
                'route_status': random.choice(['planned', 'in_progress', 'completed']),
                'created_at': current_ts
            })
        
        if (i + 1) % 1000 == 0:
            logger.info(f"  Generated {i + 1:,} / {TMS_TOTAL_RECORDS:,} TMS records")
    
    logger.info(f"✓ Generated {len(pick_waves):,} pick waves")
    logger.info(f"✓ Generated {len(receiving_tasks):,} receiving tasks")
    logger.info(f"✓ Generated {len(picking_tasks):,} picking tasks")
    logger.info(f"✓ Generated {len(packing_tasks):,} packing tasks")
    logger.info(f"✓ Generated {len(shipping_tasks):,} shipping tasks")
    logger.info(f"✓ Generated {len(shipments):,} shipments")
    logger.info(f"✓ Generated {len(tracking_events):,} tracking events")
    logger.info(f"✓ Generated {len(deliveries):,} deliveries")
    logger.info(f"✓ Generated {len(routes):,} routes")
    
    # Bulk dump to PostgreSQL
    logger.info("="*80)
    logger.info("BULK DUMPING TO POSTGRESQL...")
    logger.info("="*80)
    
    try:
        # WMS inserts
        wms_cursor = pg_wms_connection.cursor()
        wms_cursor.execute("SET CONSTRAINTS ALL DEFERRED;")
        
        # Insert pick_waves
        if pick_waves:
            insert_sql = """INSERT INTO pick_waves (
                wave_id, wave_number, warehouse_id, wave_type, planned_pick_date,
                wave_status, total_orders, created_at
            ) VALUES (%(wave_id)s, %(wave_number)s, %(warehouse_id)s, %(wave_type)s,
                %(planned_pick_date)s, %(wave_status)s, %(total_orders)s, %(created_at)s)
            ON CONFLICT (wave_number) DO NOTHING"""
            logger.info(f"Inserting {len(pick_waves):,} pick waves...")
            insert_batch_parallel(wms_cursor, insert_sql, pick_waves, "pick waves", WMS_BATCH_SIZE, pg_wms_connection)
        
        # Insert receiving_tasks
        if receiving_tasks:
            insert_sql = """INSERT INTO receiving_tasks (
                receiving_task_id, task_number, warehouse_id, material_id,
                expected_quantity, received_quantity, unit_of_measure, task_status, created_at
            ) VALUES (%(receiving_task_id)s, %(task_number)s, %(warehouse_id)s, %(material_id)s,
                %(expected_quantity)s, %(received_quantity)s, %(unit_of_measure)s, %(task_status)s, %(created_at)s)
            ON CONFLICT (task_number) DO NOTHING"""
            logger.info(f"Inserting {len(receiving_tasks):,} receiving tasks...")
            insert_batch_parallel(wms_cursor, insert_sql, receiving_tasks, "receiving tasks", WMS_BATCH_SIZE, pg_wms_connection)
        
        # Insert picking_tasks
        if picking_tasks:
            insert_sql = """INSERT INTO picking_tasks (
                picking_task_id, task_number, warehouse_id, material_id,
                quantity_to_pick, quantity_picked, task_status, created_at
            ) VALUES (%(picking_task_id)s, %(task_number)s, %(warehouse_id)s, %(material_id)s,
                %(quantity_to_pick)s, %(quantity_picked)s, %(task_status)s, %(created_at)s)
            ON CONFLICT (task_number) DO NOTHING"""
            logger.info(f"Inserting {len(picking_tasks):,} picking tasks...")
            insert_batch_parallel(wms_cursor, insert_sql, picking_tasks, "picking tasks", WMS_BATCH_SIZE, pg_wms_connection)
        
        # Insert packing_tasks
        if packing_tasks:
            insert_sql = """INSERT INTO packing_tasks (
                packing_task_id, task_number, sales_order_id, warehouse_id, packing_station,
                package_type, package_weight_kg, task_status, created_at
            ) VALUES (%(packing_task_id)s, %(task_number)s, %(sales_order_id)s, %(warehouse_id)s,
                %(packing_station)s, %(package_type)s, %(package_weight_kg)s, %(task_status)s, %(created_at)s)
            ON CONFLICT (task_number) DO NOTHING"""
            logger.info(f"Inserting {len(packing_tasks):,} packing tasks...")
            insert_batch_parallel(wms_cursor, insert_sql, packing_tasks, "packing tasks", WMS_BATCH_SIZE, pg_wms_connection)
        
        # Insert shipping_tasks
        if shipping_tasks:
            insert_sql = """INSERT INTO shipping_tasks (
                shipping_task_id, task_number, sales_order_id, warehouse_id, shipping_dock,
                number_of_packages, total_weight_kg, task_status, scheduled_ship_date,
                actual_ship_date, created_at
            ) VALUES (%(shipping_task_id)s, %(task_number)s, %(sales_order_id)s, %(warehouse_id)s,
                %(shipping_dock)s, %(number_of_packages)s, %(total_weight_kg)s, %(task_status)s,
                %(scheduled_ship_date)s, %(actual_ship_date)s, %(created_at)s)
            ON CONFLICT (task_number) DO NOTHING"""
            logger.info(f"Inserting {len(shipping_tasks):,} shipping tasks...")
            insert_batch_parallel(wms_cursor, insert_sql, shipping_tasks, "shipping tasks", WMS_BATCH_SIZE, pg_wms_connection)
        
        wms_cursor.close()
        
        # TMS inserts
        tms_cursor = pg_tms_connection.cursor()
        tms_cursor.execute("SET CONSTRAINTS ALL DEFERRED;")
        
        # Insert shipments
        if shipments:
            insert_sql = """INSERT INTO shipments (
                shipment_id, shipment_number, warehouse_id, carrier_id, tracking_number,
                bol_number, origin_warehouse_id, origin_name, origin_city, origin_state,
                origin_country, origin_postal_code, created_at
            ) VALUES (%(shipment_id)s, %(shipment_number)s, %(warehouse_id)s, %(carrier_id)s,
                %(tracking_number)s, %(bol_number)s, %(origin_warehouse_id)s, %(origin_name)s,
                %(origin_city)s, %(origin_state)s, %(origin_country)s, %(origin_postal_code)s, %(created_at)s)
            ON CONFLICT (shipment_number) DO NOTHING"""
            logger.info(f"Inserting {len(shipments):,} shipments...")
            insert_batch_parallel(tms_cursor, insert_sql, shipments, "shipments", TMS_BATCH_SIZE, pg_tms_connection)
        
        # Insert tracking_events
        if tracking_events:
            insert_sql = """INSERT INTO tracking_events (
                event_id, shipment_id, event_type, event_description, event_timestamp, created_at
            ) VALUES (%(event_id)s, %(shipment_id)s, %(event_type)s, %(event_description)s, %(event_timestamp)s, %(created_at)s)
            ON CONFLICT (event_id) DO NOTHING"""
            logger.info(f"Inserting {len(tracking_events):,} tracking events...")
            insert_batch_parallel(tms_cursor, insert_sql, tracking_events, "tracking events", TMS_BATCH_SIZE, pg_tms_connection)
        
        # Insert deliveries
        if deliveries:
            insert_sql = """INSERT INTO deliveries (
                delivery_id, delivery_number, shipment_id, actual_delivery_date, delivery_status, created_at
            ) VALUES (%(delivery_id)s, %(delivery_number)s, %(shipment_id)s, %(actual_delivery_date)s, %(delivery_status)s, %(created_at)s)
            ON CONFLICT (delivery_number) DO NOTHING"""
            logger.info(f"Inserting {len(deliveries):,} deliveries...")
            insert_batch_parallel(tms_cursor, insert_sql, deliveries, "deliveries", TMS_BATCH_SIZE, pg_tms_connection)
        
        # Insert routes
        if routes:
            insert_sql = """INSERT INTO routes (
                route_id, route_number, route_date, route_type, number_of_stops, route_status, created_at
            ) VALUES (%(route_id)s, %(route_number)s, %(route_date)s, %(route_type)s, %(number_of_stops)s, %(route_status)s, %(created_at)s)
            ON CONFLICT (route_number) DO NOTHING"""
            logger.info(f"Inserting {len(routes):,} routes...")
            insert_batch_parallel(tms_cursor, insert_sql, routes, "routes", TMS_BATCH_SIZE, pg_tms_connection)
        
        tms_cursor.close()
        
        # CRITICAL: Commit both connections to persist data
        pg_wms_connection.commit()
        pg_tms_connection.commit()
        
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
    
    tables_list = ['pick_waves', 'receiving_tasks', 'picking_tasks', 'packing_tasks', 'shipping_tasks',
                   'shipments', 'tracking_events', 'deliveries', 'routes']
    for table in tables_list:
        before = counts_before.get(table)
        after = counts_after.get(table)
        
        if before is not None and after is not None:
            inserted = after - before
            logger.info(f"{table:.<35} Before: {before:>10,} | After: {after:>10,} | Inserted: {inserted:>10,}")
    
    logger.info("="*80)
    
    if pg_wms_connection:
        pg_wms_connection.close()
    if pg_tms_connection:
        pg_tms_connection.close()
    
    return 0

if __name__ == "__main__":
    os.makedirs('logs', exist_ok=True)
    sys.exit(main())
