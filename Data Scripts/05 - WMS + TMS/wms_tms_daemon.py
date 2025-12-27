#!/usr/bin/env python3
"""
GenIMS WMS + TMS Real-Time Daemon
WMS: Continuous warehouse operations (picking, packing, shipping)
TMS: Daily logistics operations (routing, tracking, delivery confirmation)
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

# WMS Configuration (Continuous)
WMS_CYCLE_INTERVAL_SECONDS = 1800  # Run every 30 minutes
PICK_WAVES_PER_CYCLE = (1, 3)
RECEIVING_TASKS_PER_CYCLE = (2, 5)

# TMS Configuration (Daily at 3 AM)
TMS_RUN_HOUR = 3
SHIPMENTS_PER_DAY = (5, 15)
ROUTES_PER_DAY = (2, 5)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/wms_tms_daemon.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('WMSTMSDaemon')

running = True
pg_connection = None
master_data = {}
counters = {}
stats = {
    'wms_cycles': 0,
    'tms_cycles': 0,
    'waves_created': 0,
    'picks_completed': 0,
    'shipments_created': 0,
    'deliveries_completed': 0,
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
    global master_data, counters
    try:
        cursor = pg_connection.cursor()
        
        # Load warehouses
        cursor.execute("SELECT * FROM warehouses WHERE is_active = true")
        master_data['warehouses'] = [dict(zip([d[0] for d in cursor.description], row)) 
                                     for row in cursor.fetchall()]
        
        # Load carriers
        cursor.execute("SELECT * FROM carriers WHERE carrier_status = 'active'")
        master_data['carriers'] = [dict(zip([d[0] for d in cursor.description], row)) 
                                   for row in cursor.fetchall()]
        
        # Load sales orders
        cursor.execute("SELECT * FROM sales_orders WHERE order_status IN ('open', 'in_production') LIMIT 100")
        master_data['sales_orders'] = [dict(zip([d[0] for d in cursor.description], row)) 
                                       for row in cursor.fetchall()]
        
        cursor.close()
        logger.info(f"Loaded: {len(master_data.get('warehouses', []))} warehouses, "
                   f"{len(master_data.get('carriers', []))} carriers")
        return True
    except Exception as e:
        logger.error(f"Failed to load master data: {e}")
        return False

def generate_id(prefix: str) -> str:
    return f"{prefix}-{datetime.now().strftime('%Y%m%d%H%M%S')}-{random.randint(1000, 9999)}"

# ============================================================================
# WMS OPERATIONS (Every 30 minutes)
# ============================================================================

def run_wms_cycle():
    """Execute WMS warehouse operations cycle"""
    logger.info("=== WMS Cycle Starting ===")
    
    try:
        # 1. Create pick waves for pending orders
        create_pick_waves()
        
        # 2. Process receiving tasks
        process_receiving_tasks()
        
        # 3. Complete picking tasks
        complete_picking_tasks()
        
        # 4. Pack orders
        pack_orders()
        
        # 5. Ship orders
        ship_orders()
        
        stats['wms_cycles'] += 1
        logger.info("=== WMS Cycle Complete ===")
        return True
    except Exception as e:
        logger.error(f"WMS cycle error: {e}")
        return False

def create_pick_waves():
    """Create pick waves from sales orders"""
    if not master_data.get('sales_orders') or not master_data.get('warehouses'):
        return
    
    try:
        cursor = pg_connection.cursor()
        num_waves = random.randint(*PICK_WAVES_PER_CYCLE)
        
        for _ in range(num_waves):
            warehouse = random.choice(master_data['warehouses'])
            wave_id = generate_id('WAVE')
            wave_number = f"WAVE-{datetime.now().strftime('%Y%m%d%H%M')}"
            
            cursor.execute("""
                INSERT INTO pick_waves (
                    wave_id, wave_number, warehouse_id, wave_type,
                    planned_pick_date, wave_status, total_orders, created_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (wave_id, wave_number, warehouse['warehouse_id'], 'batch',
                  datetime.now().date(), 'released', random.randint(3, 10),
                  datetime.now()))
            
            stats['waves_created'] += 1
        
        pg_connection.commit()
        cursor.close()
        logger.info(f"Created {num_waves} pick waves")
    except Exception as e:
        logger.error(f"Error creating waves: {e}")
        pg_connection.rollback()

def process_receiving_tasks():
    """Process inbound receiving"""
    if not master_data.get('warehouses'):
        return
    
    try:
        cursor = pg_connection.cursor()
        num_tasks = random.randint(*RECEIVING_TASKS_PER_CYCLE)
        
        for _ in range(num_tasks):
            warehouse = random.choice(master_data['warehouses'])
            task_id = generate_id('RCV')
            
            cursor.execute("""
                INSERT INTO receiving_tasks (
                    receiving_task_id, task_number, warehouse_id,
                    material_id, expected_quantity, task_status, created_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (task_id, f"RCV-{task_id}", warehouse['warehouse_id'],
                  f"MAT-{random.randint(1, 200):06d}", random.randint(100, 1000),
                  'completed', datetime.now()))
        
        pg_connection.commit()
        cursor.close()
    except Exception as e:
        logger.error(f"Error processing receiving: {e}")
        pg_connection.rollback()

def complete_picking_tasks():
    """Complete picking tasks"""
    try:
        cursor = pg_connection.cursor()
        
        # Get pending picking tasks
        cursor.execute("""
            SELECT picking_task_id FROM picking_tasks
            WHERE task_status = 'assigned'
            LIMIT 10
        """)
        
        tasks = cursor.fetchall()
        for (task_id,) in tasks:
            cursor.execute("""
                UPDATE picking_tasks
                SET task_status = 'picked',
                    quantity_picked = quantity_to_pick,
                    completed_at = %s
                WHERE picking_task_id = %s
            """, (datetime.now(), task_id))
            
            stats['picks_completed'] += 1
        
        pg_connection.commit()
        cursor.close()
    except Exception as e:
        logger.error(f"Error completing picks: {e}")
        pg_connection.rollback()

def pack_orders():
    """Pack picked orders"""
    try:
        cursor = pg_connection.cursor()
        
        # Get picked waves ready for packing
        cursor.execute("""
            SELECT wave_id, warehouse_id FROM pick_waves
            WHERE wave_status = 'picked'
            LIMIT 5
        """)
        
        waves = cursor.fetchall()
        for wave_id, warehouse_id in waves:
            pack_id = generate_id('PACK')
            
            cursor.execute("""
                INSERT INTO packing_tasks (
                    packing_task_id, task_number, wave_id, warehouse_id,
                    package_type, tracking_number, task_status, created_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (pack_id, f"PACK-{pack_id}", wave_id, warehouse_id,
                  'box', f"TRK{datetime.now().strftime('%Y%m%d%H%M%S')}",
                  'packed', datetime.now()))
            
            # Update wave status
            cursor.execute("""
                UPDATE pick_waves SET wave_status = 'packed'
                WHERE wave_id = %s
            """, (wave_id,))
        
        pg_connection.commit()
        cursor.close()
    except Exception as e:
        logger.error(f"Error packing: {e}")
        pg_connection.rollback()

def ship_orders():
    """Ship packed orders"""
    try:
        cursor = pg_connection.cursor()
        
        # Get packed waves
        cursor.execute("""
            SELECT wave_id, warehouse_id FROM pick_waves
            WHERE wave_status = 'packed'
            LIMIT 5
        """)
        
        waves = cursor.fetchall()
        for wave_id, warehouse_id in waves:
            ship_id = generate_id('SHIP')
            
            cursor.execute("""
                INSERT INTO shipping_tasks (
                    shipping_task_id, task_number, warehouse_id,
                    number_of_packages, task_status, 
                    scheduled_ship_date, actual_ship_date, created_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (ship_id, f"SHIP-{ship_id}", warehouse_id,
                  random.randint(1, 5), 'shipped',
                  datetime.now().date(), datetime.now().date(),
                  datetime.now()))
            
            # Update wave
            cursor.execute("""
                UPDATE pick_waves SET wave_status = 'shipped'
                WHERE wave_id = %s
            """, (wave_id,))
        
        pg_connection.commit()
        cursor.close()
    except Exception as e:
        logger.error(f"Error shipping: {e}")
        pg_connection.rollback()

# ============================================================================
# TMS OPERATIONS (Daily at 3 AM)
# ============================================================================

def run_tms_cycle():
    """Execute TMS logistics operations"""
    logger.info("=== TMS Daily Cycle Starting ===")
    
    try:
        # 1. Create shipments from warehouse
        create_shipments()
        
        # 2. Update tracking events
        update_tracking_events()
        
        # 3. Confirm deliveries
        confirm_deliveries()
        
        # 4. Optimize routes
        optimize_routes()
        
        stats['tms_cycles'] += 1
        logger.info("=== TMS Cycle Complete ===")
        return True
    except Exception as e:
        logger.error(f"TMS cycle error: {e}")
        return False

def create_shipments():
    """Create shipments from shipped orders"""
    if not master_data.get('carriers'):
        return
    
    try:
        cursor = pg_connection.cursor()
        num_shipments = random.randint(*SHIPMENTS_PER_DAY)
        
        for _ in range(num_shipments):
            carrier = random.choice(master_data['carriers'])
            shipment_id = generate_id('SHPM')
            
            cursor.execute("""
                INSERT INTO shipments (
                    shipment_id, shipment_number, carrier_id,
                    tracking_number, shipment_type, number_of_packages,
                    ship_date, estimated_delivery_date, shipment_status,
                    freight_cost, total_cost, created_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (shipment_id, f"SHPM-{shipment_id}", carrier['carrier_id'],
                  f"TRK{datetime.now().strftime('%Y%m%d%H%M%S')}",
                  'parcel', random.randint(1, 5),
                  datetime.now().date(),
                  (datetime.now() + timedelta(days=random.randint(2, 5))).date(),
                  'in_transit', round(random.uniform(200, 2000), 2),
                  round(random.uniform(250, 2500), 2), datetime.now()))
            
            stats['shipments_created'] += 1
        
        pg_connection.commit()
        cursor.close()
        logger.info(f"Created {num_shipments} shipments")
    except Exception as e:
        logger.error(f"Error creating shipments: {e}")
        pg_connection.rollback()

def update_tracking_events():
    """Update tracking for in-transit shipments"""
    try:
        cursor = pg_connection.cursor()
        
        # Get in-transit shipments
        cursor.execute("""
            SELECT shipment_id, tracking_number FROM shipments
            WHERE shipment_status = 'in_transit'
            LIMIT 20
        """)
        
        shipments = cursor.fetchall()
        for shipment_id, tracking_number in shipments:
            event_id = generate_id('TRK')
            event_type = random.choice(['departed_facility', 'in_transit', 'out_for_delivery'])
            
            cursor.execute("""
                INSERT INTO tracking_events (
                    event_id, shipment_id, tracking_number,
                    event_type, event_description, event_timestamp, created_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (event_id, shipment_id, tracking_number,
                  event_type, event_type.replace('_', ' ').title(),
                  datetime.now(), datetime.now()))
        
        pg_connection.commit()
        cursor.close()
    except Exception as e:
        logger.error(f"Error updating tracking: {e}")
        pg_connection.rollback()

def confirm_deliveries():
    """Confirm deliveries for completed shipments"""
    try:
        cursor = pg_connection.cursor()
        
        # Get shipments ready for delivery
        cursor.execute("""
            SELECT shipment_id FROM shipments
            WHERE shipment_status = 'out_for_delivery'
            AND actual_delivery_date IS NULL
            LIMIT 10
        """)
        
        shipments = cursor.fetchall()
        for (shipment_id,) in shipments:
            delivery_id = generate_id('DEL')
            
            cursor.execute("""
                INSERT INTO deliveries (
                    delivery_id, delivery_number, shipment_id,
                    actual_delivery_date, delivery_status, created_at
                ) VALUES (%s, %s, %s, %s, %s, %s)
            """, (delivery_id, f"DEL-{delivery_id}", shipment_id,
                  datetime.now().date(), 'delivered', datetime.now()))
            
            # Update shipment
            cursor.execute("""
                UPDATE shipments
                SET shipment_status = 'delivered',
                    actual_delivery_date = %s
                WHERE shipment_id = %s
            """, (datetime.now().date(), shipment_id))
            
            stats['deliveries_completed'] += 1
        
        pg_connection.commit()
        cursor.close()
        logger.info(f"Confirmed {len(shipments)} deliveries")
    except Exception as e:
        logger.error(f"Error confirming deliveries: {e}")
        pg_connection.rollback()

def optimize_routes():
    """Create optimized delivery routes"""
    try:
        cursor = pg_connection.cursor()
        num_routes = random.randint(*ROUTES_PER_DAY)
        
        for _ in range(num_routes):
            route_id = generate_id('ROUTE')
            
            cursor.execute("""
                INSERT INTO routes (
                    route_id, route_number, route_date,
                    route_type, number_of_stops, route_status, created_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (route_id, f"ROUTE-{route_id}", datetime.now().date(),
                  'delivery', random.randint(5, 15), 'planned', datetime.now()))
        
        pg_connection.commit()
        cursor.close()
    except Exception as e:
        logger.error(f"Error optimizing routes: {e}")
        pg_connection.rollback()

def print_stats():
    """Print daemon statistics"""
    elapsed = (datetime.now() - stats['start_time']).total_seconds()
    hours = elapsed / 3600
    
    logger.info("="*80)
    logger.info(f"WMS + TMS Daemon Statistics")
    logger.info(f"  Uptime: {hours:.1f} hours")
    logger.info(f"  WMS Cycles: {stats['wms_cycles']}")
    logger.info(f"  TMS Cycles: {stats['tms_cycles']}")
    logger.info(f"  Waves Created: {stats['waves_created']}")
    logger.info(f"  Picks Completed: {stats['picks_completed']}")
    logger.info(f"  Shipments Created: {stats['shipments_created']}")
    logger.info(f"  Deliveries Completed: {stats['deliveries_completed']}")
    logger.info("="*80)

def main():
    """Main daemon loop"""
    logger.info("="*80)
    logger.info("GenIMS WMS + TMS Daemon Starting")
    logger.info("WMS: Every 30 minutes | TMS: Daily at 3 AM")
    logger.info("="*80)
    
    if not initialize_database():
        return 1
    
    if not load_master_data():
        return 1
    
    logger.info("Press Ctrl+C to stop")
    
    last_wms_run = datetime.now() - timedelta(hours=1)
    last_tms_run = datetime.now().replace(hour=0, minute=0, second=0)
    
    while running:
        try:
            now = datetime.now()
            
            # WMS: Run every 30 minutes
            if (now - last_wms_run).total_seconds() >= WMS_CYCLE_INTERVAL_SECONDS:
                run_wms_cycle()
                last_wms_run = now
            
            # TMS: Run daily at 3 AM
            if now.hour == TMS_RUN_HOUR and (now - last_tms_run).total_seconds() >= 86400:
                run_tms_cycle()
                last_tms_run = now
            
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
    logger.info("WMS + TMS Daemon stopped")
    return 0

if __name__ == "__main__":
    import os
    os.makedirs('logs', exist_ok=True)
    sys.exit(main())
