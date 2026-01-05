#!/usr/bin/env python3
"""
GenIMS ERP Daily Business Cycle Daemon
Runs complete ERP business operations daily
"""

import sys
import os
import time
import logging
import signal
from datetime import datetime, timedelta, time as datetime_time
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

from concurrent.futures import ThreadPoolExecutor, as_completed

# ============================================================================
# CONFIGURATION - Environment Variables with Defaults
# ============================================================================

# Database Configuration - from Azure Cloud via config.env
PG_HOST = os.getenv('POSTGRES_HOST', 'localhost')
PG_PORT = int(os.getenv('POSTGRES_PORT', '5432'))
PG_DATABASE = os.getenv('DB_ERP', 'genims_erp_db')
PG_USER = os.getenv('POSTGRES_USER', 'postgres')
PG_PASSWORD = os.getenv('POSTGRES_PASSWORD', '')
PG_SSL_MODE = os.getenv('PG_SSL_MODE', 'require')
PG_MASTER_DATABASE = os.getenv('DB_MASTER', 'genims_master_db')

# Daemon Configuration
CYCLE_INTERVAL_SECONDS = int(os.getenv('ERP_CYCLE_INTERVAL', '86400'))  # Run every 24 hours (daily)
RUN_TIME_HOUR = int(os.getenv('ERP_RUN_TIME_HOUR', '2'))  # 2 AM daily run

# Business Volumes (per day)
SALES_ORDERS_PER_DAY = (3, 8)
PURCHASE_ORDERS_PER_DAY = (2, 5)
GOODS_RECEIPTS_PER_DAY = (5, 10)
NEW_MATERIALS_PER_WEEK = (0, 2)

# MRP Configuration
MRP_PLANNING_HORIZON_DAYS = 90
MRP_SAFETY_STOCK_DAYS = 7

# Logging - use centralized logs directory with fallback
log_dir = os.getenv("DAEMON_LOG_DIR", os.path.join(os.path.dirname(__file__), '..', '..', 'logs'))
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, 'erp_daily_daemon.log')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('ERPDailyDaemon')

# ============================================================================
# GLOBAL STATE
# ============================================================================

running = True
pg_connection = None
master_data = {}
counters = {
    'material': 1,
    'supplier': 1,
    'bom': 1,
    'sales_order': 1,
    'prod_order': 1,
    'purchase_req': 1,
    'purchase_order': 1,
    'goods_receipt': 1,
    'inv_transaction': 1,
    'mrp_run': 1,
    'gl_transaction': 1
}

stats = {
    'cycles_completed': 0,
    'sales_orders_created': 0,
    'production_orders_created': 0,
    'purchase_orders_created': 0,
    'goods_receipts_processed': 0,
    'mrp_runs_executed': 0,
    'inventory_transactions': 0,
    'gl_postings': 0,
    'erp_mes_syncs': 0,
    'errors': 0,
    'start_time': datetime.now()
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
    """Initialize PostgreSQL connection"""
    global pg_connection
    
    if not POSTGRES_AVAILABLE:
        logger.error("PostgreSQL library not available. Cannot start daemon.")
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
        logger.info("Verify config.env has correct POSTGRES_HOST, POSTGRES_USER, POSTGRES_PASSWORD, and PG_SSL_MODE")
        return False


def load_master_data():
    """Load master data from master_db and ERP data from ERP db"""
    global master_data
    
    try:
        # Connect to master database for shared data
        master_conn = psycopg2.connect(
            host=PG_HOST,
            port=PG_PORT,
            database=PG_MASTER_DATABASE,
            user=PG_USER,
            password=PG_PASSWORD,
            sslmode=PG_SSL_MODE
        )
        master_cursor = master_conn.cursor()
        
        # Load from master_db
        master_cursor.execute("SELECT * FROM customers")
        master_data['customers'] = [dict(zip([d[0] for d in master_cursor.description], row)) 
                                    for row in master_cursor.fetchall()]
        
        master_cursor.execute("SELECT * FROM factories")
        master_data['factories'] = [dict(zip([d[0] for d in master_cursor.description], row)) 
                                    for row in master_cursor.fetchall()]
        
        master_cursor.execute("SELECT * FROM products")
        master_data['products'] = [dict(zip([d[0] for d in master_cursor.description], row)) 
                                  for row in master_cursor.fetchall()]
        
        master_cursor.close()
        master_conn.close()
        
        # Load from ERP database
        cursor = pg_connection.cursor()
        
        cursor.execute("SELECT * FROM materials WHERE material_status = 'active'")
        master_data['materials'] = [dict(zip([d[0] for d in cursor.description], row)) 
                                    for row in cursor.fetchall()]
        
        cursor.execute("SELECT * FROM suppliers WHERE supplier_status = 'active'")
        master_data['suppliers'] = [dict(zip([d[0] for d in cursor.description], row)) 
                                    for row in cursor.fetchall()]
        
        cursor.execute("SELECT * FROM bill_of_materials WHERE bom_status = 'active'")
        master_data['boms'] = [dict(zip([d[0] for d in cursor.description], row)) 
                              for row in cursor.fetchall()]
        
        cursor.close()
        
        logger.info(f"Master data loaded successfully:")
        logger.info(f"  Materials: {len(master_data['materials'])}")
        logger.info(f"  Suppliers: {len(master_data['suppliers'])}")
        logger.info(f"  Customers: {len(master_data['customers'])}")
        logger.info(f"  Products: {len(master_data['products'])}")
        logger.info(f"  Factories: {len(master_data['factories'])}")
        
        # Initialize counters
        _initialize_counters()
        
        return True
    except Exception as e:
        logger.error(f"Failed to load master data: {e}")
        return False


def _initialize_counters():
    """Initialize counters based on existing data - use MAX ID to avoid duplicates"""
    try:
        cursor = pg_connection.cursor()
        
        # Define tables with their ID columns and prefixes
        tables = {
            'material': ('materials', 'material_id', 'MAT'),
            'supplier': ('suppliers', 'supplier_id', 'SUP'),
            'bom': ('bill_of_materials', 'bom_id', 'BOM'),
            'sales_order': ('sales_orders', 'sales_order_id', 'SO'),
            'prod_order': ('production_orders', 'production_order_id', 'PROD'),
            'purchase_req': ('purchase_requisitions', 'requisition_id', 'PR'),
            'purchase_order': ('purchase_orders', 'purchase_order_id', 'PO'),
            'goods_receipt': ('goods_receipts', 'goods_receipt_id', 'GR'),
            'inv_transaction': ('inventory_transactions', 'transaction_id', 'INVT'),
            'mrp_run': ('mrp_runs', 'run_number', 'MRP'),
            'gl_transaction': ('general_ledger', 'gl_transaction_id', 'GL')
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


def generate_id(prefix: str, counter_key: str) -> str:
    """Generate unique ID"""
    id_val = f"{prefix}-{str(counters[counter_key]).zfill(6)}"
    counters[counter_key] += 1
    return id_val


# ============================================================================
# SALES ORDER PROCESSING
# ============================================================================

def process_new_sales_orders():
    """Create new customer sales orders"""
    num_orders = random.randint(*SALES_ORDERS_PER_DAY)
    logger.info(f"Processing {num_orders} new sales orders...")
    
    try:
        cursor = pg_connection.cursor()
        
        # Get finished goods
        finished_goods = [m for m in master_data['materials'] if m['material_type'] == 'finished_good']
        
        for _ in range(num_orders):
            customer = random.choice(master_data['customers'])
            order_date = datetime.now()
            
            # Create sales order header
            so_id = generate_id('SO', 'sales_order')
            so_number = f"SO-{order_date.strftime('%Y%m%d')}-{counters['sales_order']-1:04d}"
            
            delivery_date = order_date + timedelta(days=random.randint(7, 30))
            
            so_data = {
                'sales_order_id': so_id,
                'sales_order_number': so_number,
                'customer_id': customer['customer_id'],
                'order_date': order_date.strftime('%Y-%m-%d'),
                'order_type': 'standard',
                'currency': 'INR',
                'requested_delivery_date': delivery_date.strftime('%Y-%m-%d'),
                'order_status': 'open',
                'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            # Insert header
            cols = list(so_data.keys())
            vals = [so_data[c] for c in cols]
            placeholders = ','.join(['%s'] * len(cols))
            
            cursor.execute(
                f"INSERT INTO sales_orders ({','.join(cols)}) VALUES ({placeholders})",
                vals
            )
            
            # Create order lines (1-5 products)
            num_lines = random.randint(1, 5)
            total_value = 0
            
            for line_num in range(1, num_lines + 1):
                material = random.choice(finished_goods)
                quantity = random.randint(10, 100)
                unit_price = material['standard_cost'] * random.uniform(1.2, 1.5)
                net_price = quantity * unit_price
                
                sol_data = {
                    'sales_order_line_id': generate_id('SOL', 'sales_order'),
                    'sales_order_id': so_id,
                    'line_number': line_num * 10,
                    'material_id': material['material_id'],
                    'product_id': material.get('product_id'),
                    'material_description': material['material_name'],
                    'order_quantity': quantity,
                    'unit_of_measure': 'EA',
                    'unit_price': round(unit_price, 2),
                    'net_price': round(net_price, 2),
                    'requested_delivery_date': delivery_date.strftime('%Y-%m-%d'),
                    'line_status': 'open',
                    'make_to_order': True,
                    'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                
                cols = list(sol_data.keys())
                vals = [sol_data[c] for c in cols]
                placeholders = ','.join(['%s'] * len(cols))
                
                cursor.execute(
                    f"INSERT INTO sales_order_lines ({','.join(cols)}) VALUES ({placeholders})",
                    vals
                )
                
                total_value += net_price
            
            # Update order totals
            cursor.execute("""
                UPDATE sales_orders 
                SET total_net_value = %s,
                    total_value = %s
                WHERE sales_order_id = %s
            """, (round(total_value, 2), round(total_value * 1.18, 2), so_id))
            
            stats['sales_orders_created'] += 1
            logger.info(f"Created sales order: {so_number} (₹{total_value:,.2f})")
        
        pg_connection.commit()
        cursor.close()
        
        logger.info(f"Created {num_orders} sales orders")
        return True
        
    except Exception as e:
        logger.error(f"Error processing sales orders: {e}")
        pg_connection.rollback()
        stats['errors'] += 1
        return False


# ============================================================================
# MRP (MATERIAL REQUIREMENTS PLANNING)
# ============================================================================

def run_mrp():
    """Execute Material Requirements Planning"""
    logger.info("Running MRP (Material Requirements Planning)...")
    
    try:
        cursor = pg_connection.cursor()
        
        # Create MRP run
        mrp_run_id = generate_id('MRP', 'mrp_run')
        run_number = f"MRP-{datetime.now().strftime('%Y%m%d')}"
        
        cursor.execute("""
            INSERT INTO mrp_runs (
                mrp_run_id, run_number, planning_date, planning_horizon_days,
                planning_mode, create_purchase_requisitions, create_production_orders,
                run_status, started_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (mrp_run_id, run_number, datetime.now().date(), MRP_PLANNING_HORIZON_DAYS,
              'net_change', True, True, 'running', datetime.now()))
        
        # Get open sales order lines
        cursor.execute("""
            SELECT sol.*, m.* 
            FROM sales_order_lines sol
            JOIN materials m ON sol.material_id = m.material_id
            WHERE sol.line_status IN ('open', 'in_production')
            AND sol.requested_delivery_date <= %s
        """, ((datetime.now() + timedelta(days=MRP_PLANNING_HORIZON_DAYS)).date(),))
        
        columns = [d[0] for d in cursor.description]
        demand_lines = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        logger.info(f"Processing {len(demand_lines)} demand lines...")
        
        materials_planned = 0
        purchase_reqs_created = 0
        production_orders_created = 0
        
        for demand in demand_lines:
            material_id = demand['material_id']
            required_qty = demand['order_quantity'] - demand['delivered_quantity']
            required_date = demand['requested_delivery_date']
            
            # Check inventory
            cursor.execute("""
                SELECT SUM(unrestricted_stock) as available
                FROM inventory_balances
                WHERE material_id = %s
            """, (material_id,))
            
            result = cursor.fetchone()
            available_stock = result[0] if result and result[0] else 0
            
            # Calculate net requirement
            net_requirement = required_qty - available_stock
            
            if net_requirement > 0:
                materials_planned += 1
                
                # Create MRP element
                cursor.execute("""
                    INSERT INTO mrp_elements (
                        element_id, mrp_run_id, material_id, plant_id,
                        element_type, element_date, requirement_quantity,
                        source_document, source_line
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    generate_id('MRPE', 'mrp_run'),
                    mrp_run_id,
                    material_id,
                    random.choice(master_data['factories'])['factory_id'],
                    'dependent_requirement',
                    required_date,
                    net_requirement,
                    demand['sales_order_id'],
                    demand['line_number']
                ))
                
                # Check procurement type
                if demand['procurement_type'] == 'buy':
                    # Create purchase requisition
                    _create_purchase_requisition(material_id, net_requirement, required_date, cursor)
                    purchase_reqs_created += 1
                    
                elif demand['procurement_type'] == 'make':
                    # Create production order
                    _create_production_order_from_mrp(demand, net_requirement, required_date, cursor)
                    production_orders_created += 1
        
        # Update MRP run status
        cursor.execute("""
            UPDATE mrp_runs
            SET run_status = 'completed',
                completed_at = %s,
                materials_planned = %s,
                purchase_reqs_created = %s,
                production_orders_created = %s
            WHERE mrp_run_id = %s
        """, (datetime.now(), materials_planned, purchase_reqs_created,
              production_orders_created, mrp_run_id))
        
        pg_connection.commit()
        cursor.close()
        
        stats['mrp_runs_executed'] += 1
        logger.info(f"MRP complete: {materials_planned} materials planned, "
                   f"{purchase_reqs_created} PRs, {production_orders_created} prod orders")
        
        return True
        
    except Exception as e:
        logger.error(f"Error running MRP: {e}")
        pg_connection.rollback()
        stats['errors'] += 1
        return False


def _create_purchase_requisition(material_id: str, quantity: float, required_date, cursor):
    """Create purchase requisition for material"""
    pr_id = generate_id('PR', 'purchase_req')
    pr_number = f"PR-{datetime.now().strftime('%Y%m%d')}-{counters['purchase_req']-1:04d}"
    
    cursor.execute("""
        INSERT INTO purchase_requisitions (
            requisition_id, requisition_number, requisition_type,
            requisition_date, required_date, priority, approval_status,
            overall_status, source_type, source_document
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, (pr_id, pr_number, 'stock', datetime.now().date(), required_date,
          'normal', 'approved', 'open', 'mrp', 'MRP'))
    
    # Create PR line
    cursor.execute("""
        INSERT INTO purchase_requisition_lines (
            requisition_line_id, requisition_id, line_number, material_id,
            quantity, unit_of_measure, delivery_date, line_status
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """, (generate_id('PRL', 'purchase_req'), pr_id, 10, material_id,
          quantity, 'EA', required_date, 'open'))


def _create_production_order_from_mrp(demand: dict, quantity: float, required_date, cursor):
    """Create production order from MRP"""
    prod_order_id = generate_id('PROD', 'prod_order')
    prod_number = f"PROD-{counters['prod_order']-1:06d}"
    
    start_date = required_date - timedelta(days=demand['lead_time_days'])
    
    cursor.execute("""
        INSERT INTO production_orders (
            production_order_id, production_order_number, material_id,
            plant_id, sales_order_id, order_type, order_quantity,
            basic_start_date, basic_end_date, system_status, priority
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, (prod_order_id, prod_number, demand['material_id'],
          random.choice(master_data['factories'])['factory_id'],
          demand['sales_order_id'], 'production', quantity,
          start_date, required_date, 'created', 5))
    
    stats['production_orders_created'] += 1


# ============================================================================
# PROCUREMENT PROCESSING
# ============================================================================

def process_purchase_orders():
    """Convert approved PRs to POs and create new POs"""
    logger.info("Processing purchase orders...")
    
    try:
        cursor = pg_connection.cursor()
        
        # Get approved PRs not yet assigned
        cursor.execute("""
            SELECT pr.*, prl.*
            FROM purchase_requisitions pr
            JOIN purchase_requisition_lines prl ON pr.requisition_id = prl.requisition_id
            WHERE pr.approval_status = 'approved'
            AND prl.assigned_to_po IS NULL
            LIMIT 10
        """)
        
        columns = [d[0] for d in cursor.description]
        pr_lines = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        # Group by supplier (get material's default supplier)
        pos_created = 0
        
        for pr_line in pr_lines:
            # Get material supplier
            material = next((m for m in master_data['materials'] 
                           if m['material_id'] == pr_line['material_id']), None)
            
            if not material or not material.get('default_supplier_id'):
                continue
            
            supplier_id = material['default_supplier_id']
            
            # Create PO
            po_id = generate_id('PO', 'purchase_order')
            po_number = f"PO-{datetime.now().strftime('%Y%m%d')}-{counters['purchase_order']-1:04d}"
            
            cursor.execute("""
                INSERT INTO purchase_orders (
                    purchase_order_id, po_number, supplier_id, po_date,
                    po_type, currency, po_status
                ) VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (po_id, po_number, supplier_id, datetime.now().date(),
                  'standard', 'INR', 'released'))
            
            # Create PO line
            unit_price = material['standard_cost'] * random.uniform(0.9, 1.1)
            net_price = pr_line['quantity'] * unit_price
            
            cursor.execute("""
                INSERT INTO purchase_order_lines (
                    po_line_id, purchase_order_id, line_number, material_id,
                    material_description, order_quantity, unit_of_measure,
                    unit_price, net_price, delivery_date, line_status,
                    requisition_id, requisition_line
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (generate_id('POL', 'purchase_order'), po_id, 10,
                  pr_line['material_id'], material['material_name'],
                  pr_line['quantity'], pr_line['unit_of_measure'],
                  round(unit_price, 2), round(net_price, 2),
                  pr_line['delivery_date'], 'open',
                  pr_line['requisition_id'], pr_line['line_number']))
            
            # Update PR line as assigned
            cursor.execute("""
                UPDATE purchase_requisition_lines
                SET assigned_to_po = %s,
                    assigned_quantity = %s,
                    line_status = 'assigned'
                WHERE requisition_line_id = %s
            """, (po_id, pr_line['quantity'], pr_line['requisition_line_id']))
            
            # Update PO total
            cursor.execute("""
                UPDATE purchase_orders
                SET total_value = %s
                WHERE purchase_order_id = %s
            """, (round(net_price, 2), po_id))
            
            pos_created += 1
            stats['purchase_orders_created'] += 1
            
            logger.info(f"Created PO: {po_number} (₹{net_price:,.2f})")
        
        pg_connection.commit()
        cursor.close()
        
        logger.info(f"Processed {pos_created} purchase orders")
        return True
        
    except Exception as e:
        logger.error(f"Error processing purchase orders: {e}")
        pg_connection.rollback()
        stats['errors'] += 1
        return False
# ============================================================================
# GOODS RECEIPT PROCESSING - Part 2 of ERP Daily Daemon
# ============================================================================

def process_goods_receipts():
    """Process goods receipts for delivered POs"""
    logger.info("Processing goods receipts...")
    
    try:
        cursor = pg_connection.cursor()
        
        # Get PO lines ready for GR (delivery date passed, not fully received)
        cursor.execute("""
            SELECT pol.*, po.supplier_id, m.material_name
            FROM purchase_order_lines pol
            JOIN purchase_orders po ON pol.purchase_order_id = po.purchase_order_id
            JOIN materials m ON pol.material_id = m.material_id
            WHERE pol.delivery_date <= %s
            AND pol.received_quantity < pol.order_quantity
            AND pol.line_status != 'closed'
            LIMIT 10
        """, (datetime.now().date(),))
        
        columns = [d[0] for d in cursor.description]
        po_lines = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        for pol in po_lines:
            # Receive full quantity or partial
            receive_qty = pol['order_quantity'] - pol['received_quantity']
            if random.random() < 0.3:  # 30% partial receipt
                receive_qty = receive_qty * random.uniform(0.5, 0.9)
            
            receive_qty = round(receive_qty, 2)
            
            # Create goods receipt
            gr_id = generate_id('GR', 'goods_receipt')
            gr_number = f"GR-{datetime.now().strftime('%Y%m%d')}-{counters['goods_receipt']-1:05d}"
            
            batch_number = f"BATCH-{datetime.now().strftime('%Y%m%d')}-{random.randint(1000, 9999)}"
            
            cursor.execute("""
                INSERT INTO goods_receipts (
                    goods_receipt_id, gr_number, gr_date, posting_date,
                    purchase_order_id, po_line_id, supplier_id, material_id,
                    quantity_received, unit_of_measure, plant_id,
                    storage_location, batch_number, quality_status,
                    unit_price, total_value, gr_status
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (gr_id, gr_number, datetime.now().date(), datetime.now().date(),
                  pol['purchase_order_id'], pol['po_line_id'], pol['supplier_id'],
                  pol['material_id'], receive_qty, pol['unit_of_measure'],
                  random.choice(master_data['factories'])['factory_id'],
                  'WH01', batch_number, 'unrestricted', pol['unit_price'],
                  round(receive_qty * pol['unit_price'], 2), 'posted'))
            
            # Update PO line received quantity
            new_received = pol['received_quantity'] + receive_qty
            new_status = 'received' if new_received >= pol['order_quantity'] else 'partially_received'
            
            cursor.execute("""
                UPDATE purchase_order_lines
                SET received_quantity = %s,
                    line_status = %s
                WHERE po_line_id = %s
            """, (new_received, new_status, pol['po_line_id']))
            
            # Create inventory transaction (goods receipt)
            _post_inventory_transaction(
                'goods_receipt', '101', pol['material_id'], receive_qty,
                pol['unit_of_measure'], pol['unit_price'] * receive_qty,
                purchase_order_id=pol['purchase_order_id'],
                goods_receipt_id=gr_id,
                cursor=cursor
            )
            
            # Update inventory balance
            _update_inventory_balance(
                pol['material_id'], 
                random.choice(master_data['factories'])['factory_id'],
                'WH01', receive_qty, cursor
            )
            
            # Post to GL (debit inventory, credit GR/IR clearing)
            _post_to_gl(
                'DR', '1400', receive_qty * pol['unit_price'],
                f"GR {gr_number} - {pol['material_name']}", cursor
            )
            _post_to_gl(
                'CR', '2110', receive_qty * pol['unit_price'],
                f"GR {gr_number} - GR/IR Clearing", cursor
            )
            
            stats['goods_receipts_processed'] += 1
            logger.info(f"Goods receipt: {gr_number} - {receive_qty} {pol['unit_of_measure']}")
        
        pg_connection.commit()
        cursor.close()
        
        logger.info(f"Processed {len(po_lines)} goods receipts")
        return True
        
    except Exception as e:
        logger.error(f"Error processing goods receipts: {e}")
        pg_connection.rollback()
        stats['errors'] += 1
        return False


# ============================================================================
# PRODUCTION ORDER PROCESSING
# ============================================================================

def release_production_orders():
    """Release production orders to MES"""
    logger.info("Releasing production orders to MES...")
    
    try:
        cursor = pg_connection.cursor()
        
        # Get created production orders ready for release
        cursor.execute("""
            SELECT po.*, m.material_code, m.material_name
            FROM production_orders po
            JOIN materials m ON po.material_id = m.material_id
            WHERE po.system_status = 'created'
            AND po.basic_start_date <= %s
            LIMIT 5
        """, (datetime.now().date(),))
        
        columns = [d[0] for d in cursor.description]
        prod_orders = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        for po in prod_orders:
            # Release production order
            cursor.execute("""
                UPDATE production_orders
                SET system_status = 'released',
                    released_by = 'SYSTEM',
                    released_at = %s
                WHERE production_order_id = %s
            """, (datetime.now(), po['production_order_id']))
            
            # Sync to MES - create work order
            _sync_production_order_to_mes(po, cursor)
            
            logger.info(f"Released production order: {po['production_order_number']}")
        
        pg_connection.commit()
        cursor.close()
        
        logger.info(f"Released {len(prod_orders)} production orders to MES")
        return True
        
    except Exception as e:
        logger.error(f"Error releasing production orders: {e}")
        pg_connection.rollback()
        stats['errors'] += 1
        return False


def _sync_production_order_to_mes(prod_order: dict, cursor):
    """Sync production order to MES as work order"""
    try:
        # Check if work_orders table exists (MES might not be set up yet)
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'work_orders'
            )
        """)
        
        if not cursor.fetchone()[0]:
            logger.warning("MES work_orders table not found. Skipping sync.")
            return
        
        # Create work order in MES
        wo_id = f"WO-{prod_order['production_order_id']}"
        
        # Get line mapping for this material/plant
        cursor.execute("""
            SELECT line_id, factory_id
            FROM line_product_mapping
            WHERE factory_id = %s
            LIMIT 1
        """, (prod_order['plant_id'],))
        
        result = cursor.fetchone()
        if not result:
            logger.warning(f"No line mapping found for {prod_order['plant_id']}")
            return
        
        line_id, factory_id = result
        
        # Insert work order
        cursor.execute("""
            INSERT INTO work_orders (
                work_order_id, work_order_number, product_id, factory_id,
                line_id, planned_quantity, status, erp_order_id,
                planned_start_date, planned_end_date
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (work_order_id) DO NOTHING
        """, (wo_id, prod_order['production_order_number'],
              prod_order.get('product_id'), factory_id, line_id,
              prod_order['order_quantity'], 'scheduled',
              prod_order['production_order_id'],
              prod_order['basic_start_date'], prod_order['basic_end_date']))
        
        # Link work order back to production order
        cursor.execute("""
            UPDATE production_orders
            SET work_order_id = %s
            WHERE production_order_id = %s
        """, (wo_id, prod_order['production_order_id']))
        
        # Log sync
        cursor.execute("""
            INSERT INTO erp_mes_sync_log (
                sync_id, sync_direction, document_type, document_id,
                sync_status, sync_data
            ) VALUES (%s, %s, %s, %s, %s, %s)
        """, (generate_id('SYNC', 'gl_transaction'), 'ERP_TO_MES',
              'production_order', prod_order['production_order_id'],
              'completed', json.dumps({'work_order_id': wo_id})))
        
        stats['erp_mes_syncs'] += 1
        
    except Exception as e:
        logger.error(f"Error syncing to MES: {e}")


def receive_mes_confirmations():
    """Receive production confirmations from MES"""
    logger.info("Receiving production confirmations from MES...")
    
    try:
        cursor = pg_connection.cursor()
        
        # Check if work_orders table exists
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'work_orders'
            )
        """)
        
        if not cursor.fetchone()[0]:
            return True
        
        # Get completed work orders not yet confirmed in ERP
        cursor.execute("""
            SELECT wo.*, po.production_order_id
            FROM work_orders wo
            JOIN production_orders po ON wo.work_order_id = po.work_order_id
            WHERE wo.status = 'completed'
            AND po.system_status = 'released'
        """)
        
        columns = [d[0] for d in cursor.description]
        completed_wos = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        for wo in completed_wos:
            # Update production order with actuals
            cursor.execute("""
                UPDATE production_orders
                SET system_status = 'confirmed',
                    delivered_quantity = %s,
                    scrap_quantity = %s,
                    actual_start_date = %s,
                    actual_finish_date = %s
                WHERE production_order_id = %s
            """, (wo['good_quantity'], wo['scrapped_quantity'],
                  wo['actual_start_time'], wo['actual_end_time'],
                  wo['production_order_id']))
            
            # Create goods receipt for finished goods
            _receive_finished_goods(wo, cursor)
            
            # Log sync
            cursor.execute("""
                INSERT INTO erp_mes_sync_log (
                    sync_id, sync_direction, document_type, document_id,
                    sync_status, sync_data
                ) VALUES (%s, %s, %s, %s, %s, %s)
            """, (generate_id('SYNC', 'gl_transaction'), 'MES_TO_ERP',
                  'production_confirmation', wo['production_order_id'],
                  'completed', json.dumps({'good_quantity': wo['good_quantity']})))
            
            stats['erp_mes_syncs'] += 1
            logger.info(f"Received confirmation: {wo['work_order_number']}")
        
        pg_connection.commit()
        cursor.close()
        
        logger.info(f"Processed {len(completed_wos)} MES confirmations")
        return True
        
    except Exception as e:
        logger.error(f"Error receiving MES confirmations: {e}")
        pg_connection.rollback()
        stats['errors'] += 1
        return False


def _receive_finished_goods(work_order: dict, cursor):
    """Receive finished goods from completed work order"""
    # Create inventory transaction for finished goods receipt
    cursor.execute("""
        SELECT material_id FROM production_orders 
        WHERE production_order_id = %s
    """, (work_order['production_order_id'],))
    
    result = cursor.fetchone()
    if not result:
        return
    
    material_id = result[0]
    
    # Get material cost
    cursor.execute("""
        SELECT standard_cost FROM materials WHERE material_id = %s
    """, (material_id,))
    
    cost_result = cursor.fetchone()
    standard_cost = cost_result[0] if cost_result else 100.0
    
    _post_inventory_transaction(
        'production_receipt', '101', material_id,
        work_order['good_quantity'], 'EA',
        work_order['good_quantity'] * standard_cost,
        production_order_id=work_order['production_order_id'],
        work_order_id=work_order['work_order_id'],
        cursor=cursor
    )
    
    # Update inventory balance
    _update_inventory_balance(
        material_id, work_order['factory_id'], 'WH01',
        work_order['good_quantity'], cursor
    )


# ============================================================================
# INVENTORY MANAGEMENT
# ============================================================================

def _post_inventory_transaction(trans_type: str, movement_type: str, 
                               material_id: str, quantity: float,
                               uom: str, amount: float,
                               purchase_order_id=None, goods_receipt_id=None,
                               production_order_id=None, work_order_id=None,
                               cursor=None):
    """Post inventory transaction"""
    trans_id = generate_id('INVT', 'inv_transaction')
    mat_doc = f"MAT-{datetime.now().strftime('%Y%m%d')}-{counters['inv_transaction']:05d}"
    
    cursor.execute("""
        INSERT INTO inventory_transactions (
            transaction_id, material_document, document_item, transaction_type,
            movement_type, posting_date, document_date, material_id,
            plant_id, storage_location, quantity, unit_of_measure, amount,
            purchase_order_id, goods_receipt_id, production_order_id,
            work_order_id, created_by
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, (trans_id, mat_doc, 1, trans_type, movement_type,
          datetime.now().date(), datetime.now().date(), material_id,
          random.choice(master_data['factories'])['factory_id'], 'WH01',
          quantity, uom, amount, purchase_order_id, goods_receipt_id,
          production_order_id, work_order_id, 'SYSTEM'))
    
    stats['inventory_transactions'] += 1


def _update_inventory_balance(material_id: str, plant_id: str, 
                              storage_loc: str, quantity: float, cursor):
    """Update inventory balance"""
    # Check if balance exists
    cursor.execute("""
        SELECT balance_id, unrestricted_stock
        FROM inventory_balances
        WHERE material_id = %s
        AND plant_id = %s
        AND storage_location = %s
    """, (material_id, plant_id, storage_loc))
    
    result = cursor.fetchone()
    
    if result:
        balance_id, current_stock = result
        new_stock = current_stock + quantity
        
        cursor.execute("""
            UPDATE inventory_balances
            SET unrestricted_stock = %s,
                updated_at = %s,
                last_goods_receipt_date = %s
            WHERE balance_id = %s
        """, (new_stock, datetime.now(), datetime.now().date(), balance_id))
    else:
        # Create new balance
        cursor.execute("""
            INSERT INTO inventory_balances (
                balance_id, material_id, plant_id, storage_location,
                unrestricted_stock, updated_at, last_goods_receipt_date
            ) VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (generate_id('INV', 'inv_transaction'), material_id, plant_id,
              storage_loc, quantity, datetime.now(), datetime.now().date()))


# ============================================================================
# FINANCIAL POSTING
# ============================================================================

def _post_to_gl(debit_credit: str, gl_account: str, amount: float, 
               description: str, cursor):
    """Post to general ledger"""
    trans_id = generate_id('GL', 'gl_transaction')
    doc_number = f"GL-{datetime.now().strftime('%Y%m%d')}-{counters['gl_transaction']:05d}"
    
    debit_amt = amount if debit_credit == 'DR' else 0
    credit_amt = amount if debit_credit == 'CR' else 0
    
    cursor.execute("""
        INSERT INTO general_ledger (
            gl_transaction_id, document_number, document_type,
            posting_date, document_date, gl_account, company_code,
            debit_amount, credit_amount, currency, text,
            source_system, fiscal_year, fiscal_period
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, (trans_id, doc_number, 'SA', datetime.now().date(),
          datetime.now().date(), gl_account, 'C001',
          debit_amt, credit_amt, 'INR', description, 'ERP',
          datetime.now().year, datetime.now().month))
    
    stats['gl_postings'] += 1


def post_period_end_entries():
    """Post month-end/period-end entries"""
    logger.info("Posting period-end entries...")
    
    try:
        cursor = pg_connection.cursor()
        
        # Cost center allocations
        # Production variance postings
        # Inventory valuation
        # Accruals
        
        # Example: Post manufacturing overhead
        cursor.execute("""
            SELECT COUNT(*) * 1000 as overhead
            FROM production_orders
            WHERE system_status = 'confirmed'
            AND actual_finish_date >= %s
        """, ((datetime.now() - timedelta(days=1)).date(),))
        
        result = cursor.fetchone()
        if result and result[0] > 0:
            overhead = result[0]
            _post_to_gl('DR', '5100', overhead, 'Manufacturing Overhead', cursor)
            _post_to_gl('CR', '2500', overhead, 'Overhead Applied', cursor)
        
        pg_connection.commit()
        cursor.close()
        
        return True
        
    except Exception as e:
        logger.error(f"Error posting period entries: {e}")
        pg_connection.rollback()
        return False


# ============================================================================
# STATISTICS AND REPORTING
# ============================================================================

def print_daily_stats():
    """Print daily cycle statistics"""
    elapsed = (datetime.now() - stats['start_time']).total_seconds()
    days = elapsed / 86400
    
    logger.info("="*80)
    logger.info(f"Daily ERP Cycle Statistics")
    logger.info(f"  Uptime: {days:.1f} days")
    logger.info(f"  Cycles Completed: {stats['cycles_completed']}")
    logger.info(f"  Sales Orders: {stats['sales_orders_created']}")
    logger.info(f"  Production Orders: {stats['production_orders_created']}")
    logger.info(f"  Purchase Orders: {stats['purchase_orders_created']}")
    logger.info(f"  Goods Receipts: {stats['goods_receipts_processed']}")
    logger.info(f"  MRP Runs: {stats['mrp_runs_executed']}")
    logger.info(f"  Inventory Transactions: {stats['inventory_transactions']}")
    logger.info(f"  GL Postings: {stats['gl_postings']}")
    logger.info(f"  ERP-MES Syncs: {stats['erp_mes_syncs']}")
    logger.info(f"  Errors: {stats['errors']}")
    logger.info("="*80)


# ============================================================================
# MAIN DAEMON LOOP
# ============================================================================

def wait_until_next_run():
    """Sleep until next scheduled run time"""
    now = datetime.now()
    next_run = now.replace(hour=RUN_TIME_HOUR, minute=0, second=0, microsecond=0)
    
    if now >= next_run:
        next_run += timedelta(days=1)
    
    sleep_seconds = (next_run - now).total_seconds()
    logger.info(f"Next run scheduled for: {next_run.strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"Sleeping for {sleep_seconds/3600:.1f} hours...")
    
    time.sleep(sleep_seconds)



def get_table_count(table_name):
    """Get current count from any table in PostgreSQL"""
    try:
        conn = psycopg2.connect(
            host=PG_HOST,
            port=PG_PORT,
            database=PG_DATABASE,
            user=PG_USER,
            password=PG_PASSWORD,
            sslmode=PG_SSL_MODE,
            connect_timeout=10
        )
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
    """Get baseline counts for all ERP tables"""
    tables = ['sales_orders', 'sales_order_lines', 'purchase_orders', 
              'purchase_order_lines', 'goods_receipts', 'mrp_runs',
              'purchase_requisitions', 'production_orders', 'inventory_transactions',
              'general_ledger']
    counts = {}
    for table in tables:
        counts[table] = get_table_count(table)
    return counts


def main():
    """Main daemon loop - ULTRA FAST MODE (In-Memory Generation)"""
    logger.info("="*80)
    logger.info("GenIMS ERP Daily Business Cycle Daemon - ULTRA FAST MODE")
    logger.info("="*80)
    
def main():
    """Main daemon loop - ULTRA FAST MODE (In-Memory Generation)"""
    logger.info("="*80)
    logger.info("GenIMS ERP Daily Business Cycle Daemon - ULTRA FAST MODE")
    logger.info("="*80)
    
    # Initialize
    if not initialize_database():
        return 1
    
    if not load_master_data():
        return 1
    
    start_time = time.time()
    
    # Get baseline counts before generation
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
    
    # Generate all data for single cycle in memory
    sales_orders_list = []
    sales_order_lines_list = []
    purchase_orders_list = []
    purchase_order_lines_list = []
    goods_receipts_list = []
    mrp_runs_list = []
    purchase_requisitions_list = []
    production_orders_list = []
    inventory_transactions_list = []
    general_ledger_list = []
    
    # Simulate current date
    current_date = datetime.now().strftime('%Y-%m-%d')
    
    # Generate Sales Orders
    num_so = random.randint(*SALES_ORDERS_PER_DAY)
    logger.info(f"Generating {num_so} sales orders...")
    
    finished_goods = [m for m in master_data['materials'] if m.get('material_type') == 'finished_good']
    if not finished_goods:
        finished_goods = master_data['materials'][:5] if master_data['materials'] else []
    
    for i in range(num_so):
        customer = random.choice(master_data['customers'])
        so_id = f"SO-{(counters['sales_order'] + i):06d}"
        so_number = f"SO-{datetime.now().strftime('%Y%m%d')}-{i:04d}"
        
        delivery_date = (datetime.now() + timedelta(days=random.randint(5, 30))).date()
        
        so_data = {
            'sales_order_id': so_id,
            'sales_order_number': so_number,
            'customer_id': customer.get('customer_id', 'CUST-001'),
            'customer_po_number': f"CUS-PO-{random.randint(10000, 99999)}",
            'sales_organization': 'S001',
            'distribution_channel': 'DC01',
            'division': 'DIV01',
            'order_date': datetime.now().date(),
            'requested_delivery_date': delivery_date,
            'order_status': 'open',
            'total_net_value': 0,
            'total_value': 0,
            'currency': 'INR',
            'created_by': 'SYSTEM',
            'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        sales_orders_list.append(so_data)
        
        # Create SO lines (1-5 products)
        num_lines = random.randint(1, 5)
        total_value = 0
        
        for line_num in range(1, num_lines + 1):
            material = random.choice(finished_goods) if finished_goods else {'material_id': 'PROD-001', 'material_name': 'Default', 'standard_cost': 100}
            quantity = random.randint(10, 100)
            unit_price = float(material.get('standard_cost', 100)) * random.uniform(1.2, 1.5)
            net_price = quantity * unit_price
            
            sol_data = {
                'sales_order_line_id': f"SOL-{(counters['sales_order'] + i):06d}-{line_num}",
                'sales_order_id': so_id,
                'line_number': line_num * 10,
                'material_id': material.get('material_id', 'PROD-001'),
                'product_id': material.get('product_id', 'PROD-001'),
                'material_description': material.get('material_name', 'Default Product'),
                'order_quantity': quantity,
                'unit_of_measure': 'EA',
                'unit_price': round(unit_price, 2),
                'net_price': round(net_price, 2),
                'requested_delivery_date': delivery_date.strftime('%Y-%m-%d'),
                'line_status': 'open',
                'make_to_order': True,
                'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            sales_order_lines_list.append(sol_data)
            total_value += net_price
        
        # Update SO totals
        so_data['total_net_value'] = round(total_value, 2)
        so_data['total_value'] = round(total_value * 1.18, 2)
    
    logger.info(f"✓ Generated {len(sales_orders_list)} sales orders")
    logger.info(f"✓ Generated {len(sales_order_lines_list)} sales order lines")
    
    # Generate Purchase Requisitions and Orders
    num_pr = num_so * random.randint(2, 4)
    logger.info(f"Generating {num_pr} purchase requisitions...")
    
    raw_materials = [m for m in master_data['materials'] if m.get('material_type') in ['raw_material', 'component']]
    if not raw_materials:
        raw_materials = master_data['materials'][5:10] if len(master_data['materials']) > 5 else []
    
    for i in range(num_pr):
        material = random.choice(raw_materials) if raw_materials else {'material_id': 'MAT-001', 'material_name': 'Default Material'}
        required_date = (datetime.now() + timedelta(days=random.randint(10, 60))).date()
        quantity = random.randint(50, 500)
        
        pr_id = f"PR-{(counters['purchase_req'] + i):06d}"
        pr_number = f"PR-{datetime.now().strftime('%Y%m%d')}-{i:04d}"
        
        pr_data = {
            'requisition_id': pr_id,
            'requisition_number': pr_number,
            'requisition_type': 'stock',
            'requisition_date': datetime.now().date(),
            'required_date': required_date,
            'requester_id': master_data['employees'][0]['employee_id'] if master_data.get('employees') else 'EMP-001',
            'cost_center_id': 'CC-001',
            'plant_id': master_data['factories'][0]['factory_id'] if master_data.get('factories') else 'FAC-001',
            'priority': 'normal',
            'approval_status': 'approved',
            'overall_status': 'open',
            'source_type': 'mrp',
            'source_document': 'MRP',
            'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        purchase_requisitions_list.append(pr_data)
        
        # Create PR line
        prl_data = {
            'requisition_line_id': f"PRL-{(counters['purchase_req'] + i):06d}-01",
            'requisition_id': pr_id,
            'line_number': 10,
            'material_id': material.get('material_id', 'MAT-001'),
            'quantity': quantity,
            'unit_of_measure': 'EA',
            'delivery_date': required_date,
            'line_status': 'open',
            'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        # Create PO from PR
        supplier = random.choice(master_data['suppliers']) if master_data.get('suppliers') else {'supplier_id': 'SUP-001', 'supplier_name': 'Default Supplier'}
        po_id = f"PO-{(counters['purchase_order'] + i):06d}"
        po_number = f"PO-{datetime.now().strftime('%Y%m%d')}-{i:04d}"
        
        unit_price = float(material.get('standard_cost', 50)) * random.uniform(0.9, 1.1)
        net_price = quantity * unit_price
        
        po_data = {
            'purchase_order_id': po_id,
            'po_number': po_number,
            'supplier_id': supplier.get('supplier_id', 'SUP-001'),
            'po_date': datetime.now().date(),
            'po_type': 'standard',
            'currency': 'INR',
            'po_status': 'released',
            'total_value': round(net_price, 2),
            'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        purchase_orders_list.append(po_data)
        
        pol_data = {
            'po_line_id': f"POL-{(counters['purchase_order'] + i):06d}-01",
            'purchase_order_id': po_id,
            'line_number': 10,
            'material_id': material.get('material_id', 'MAT-001'),
            'material_description': material.get('material_name', 'Default Material'),
            'order_quantity': quantity,
            'unit_of_measure': 'EA',
            'unit_price': round(unit_price, 2),
            'net_price': round(net_price, 2),
            'delivery_date': required_date,
            'line_status': 'open',
            'requisition_id': pr_id,
            'requisition_line': 10,
            'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        purchase_order_lines_list.append(pol_data)
    
    logger.info(f"✓ Generated {len(purchase_requisitions_list)} purchase requisitions")
    logger.info(f"✓ Generated {len(purchase_orders_list)} purchase orders")
    logger.info(f"✓ Generated {len(purchase_order_lines_list)} PO lines")
    
    # Generate Goods Receipts for some POs
    num_gr = max(1, len(purchase_order_lines_list) // 3)
    logger.info(f"Generating {num_gr} goods receipts...")
    
    for i in range(min(num_gr, len(purchase_order_lines_list))):
        pol = purchase_order_lines_list[i]
        receive_qty = pol['order_quantity'] * random.uniform(0.5, 1.0)
        
        gr_id = f"GR-{(counters['goods_receipt'] + i):06d}"
        gr_number = f"GR-{datetime.now().strftime('%Y%m%d')}-{i:05d}"
        batch_number = f"BATCH-{datetime.now().strftime('%Y%m%d')}-{random.randint(1000, 9999)}"
        
        gr_data = {
            'goods_receipt_id': gr_id,
            'gr_number': gr_number,
            'gr_date': datetime.now().date(),
            'posting_date': datetime.now().date(),
            'purchase_order_id': pol['purchase_order_id'],
            'po_line_id': pol['po_line_id'],
            'supplier_id': 'SUP-001',
            'material_id': pol['material_id'],
            'quantity_received': round(receive_qty, 2),
            'unit_of_measure': 'EA',
            'plant_id': 'FAC-001',
            'storage_location': 'WH01',
            'batch_number': batch_number,
            'quality_status': 'unrestricted',
            'unit_price': pol['unit_price'],
            'total_value': round(receive_qty * pol['unit_price'], 2),
            'gr_status': 'posted',
            'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        goods_receipts_list.append(gr_data)
        
        # Create inventory transaction
        invt_data = {
            'transaction_id': f"INVT-{(counters['inv_transaction'] + i):08d}",
            'material_document': f"MAT-{datetime.now().strftime('%Y%m%d')}-{i:05d}",
            'document_item': 1,
            'transaction_type': 'goods_receipt',
            'movement_type': '101',
            'posting_date': datetime.now().date(),
            'document_date': datetime.now().date(),
            'material_id': pol['material_id'],
            'plant_id': 'FAC-001',
            'storage_location': 'WH01',
            'quantity': round(receive_qty, 2),
            'unit_of_measure': 'EA',
            'amount': round(receive_qty * pol['unit_price'], 2),
            'purchase_order_id': pol['purchase_order_id'],
            'goods_receipt_id': gr_id,
            'created_by': 'SYSTEM',
            'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        inventory_transactions_list.append(invt_data)
        
        # Create GL posting
        gl_data_dr = {
            'gl_transaction_id': f"GL-{(counters['gl_transaction'] + i*2):08d}",
            'document_number': f"GL-{datetime.now().strftime('%Y%m%d')}-{i*2:05d}",
            'document_type': 'SA',
            'posting_date': datetime.now().date(),
            'document_date': datetime.now().date(),
            'gl_account': '1400',
            'company_code': 'C001',
            'debit_amount': round(receive_qty * pol['unit_price'], 2),
            'credit_amount': 0,
            'currency': 'INR',
            'text': f"GR {gr_number} - {pol['material_description']}",
            'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        general_ledger_list.append(gl_data_dr)
        
        gl_data_cr = {
            'gl_transaction_id': f"GL-{(counters['gl_transaction'] + i*2 + 1):08d}",
            'document_number': f"GL-{datetime.now().strftime('%Y%m%d')}-{i*2+1:05d}",
            'document_type': 'SA',
            'posting_date': datetime.now().date(),
            'document_date': datetime.now().date(),
            'gl_account': '2110',
            'company_code': 'C001',
            'debit_amount': 0,
            'credit_amount': round(receive_qty * pol['unit_price'], 2),
            'currency': 'INR',
            'text': f"GR {gr_number} - GR/IR Clearing",
            'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        general_ledger_list.append(gl_data_cr)
    
    logger.info(f"✓ Generated {len(goods_receipts_list)} goods receipts")
    logger.info(f"✓ Generated {len(inventory_transactions_list)} inventory transactions")
    logger.info(f"✓ Generated {len(general_ledger_list)} GL transactions")
    
    # Generate MRP run
    mrp_run_id = f"MRP-{(counters['mrp_run']):06d}"
    mrp_data = {
        'mrp_run_id': mrp_run_id,
        'run_number': f"MRP-{datetime.now().strftime('%Y%m%d')}",
        'planning_date': datetime.now().date(),
        'planning_horizon_days': MRP_PLANNING_HORIZON_DAYS,
        'planning_mode': 'net_change',
        'create_purchase_requisitions': True,
        'create_production_orders': True,
        'run_status': 'completed',
        'started_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'completed_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'materials_planned': len(purchase_requisitions_list),
        'purchase_reqs_created': len(purchase_requisitions_list),
        'production_orders_created': len(purchase_requisitions_list) // 2,
        'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    
    mrp_runs_list.append(mrp_data)
    
    logger.info(f"✓ Generated 1 MRP run")
    
    # Generate Production Orders
    num_prod = len(purchase_requisitions_list) // 2
    logger.info(f"Generating {num_prod} production orders...")
    
    for i in range(num_prod):
        material = random.choice(finished_goods) if finished_goods else {'material_id': 'PROD-001', 'material_name': 'Default'}
        po_id = f"PROD-{(counters['prod_order'] + i):06d}"
        po_number = f"PROD-{(counters['prod_order'] + i):08d}"
        
        required_date = (datetime.now() + timedelta(days=random.randint(15, 45))).date()
        start_date = required_date - timedelta(days=random.randint(5, 15))
        quantity = random.randint(50, 200)
        
        prod_data = {
            'production_order_id': po_id,
            'production_order_number': po_number,
            'material_id': material.get('material_id', 'PROD-001'),
            'plant_id': 'FAC-001',
            'sales_order_id': None,
            'order_type': 'production',
            'order_quantity': quantity,
            'basic_start_date': start_date,
            'basic_end_date': required_date,
            'system_status': 'created',
            'priority': 5,
            'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        production_orders_list.append(prod_data)
    
    logger.info(f"✓ Generated {len(production_orders_list)} production orders")
    
    # Bulk dump to PostgreSQL
    logger.info("="*80)
    logger.info("BULK DUMPING TO POSTGRESQL...")
    logger.info("="*80)
    
    if POSTGRES_AVAILABLE:
        try:
            conn = psycopg2.connect(
                host=PG_HOST,
                port=PG_PORT,
                database=PG_DATABASE,
                user=PG_USER,
                password=PG_PASSWORD,
                sslmode=PG_SSL_MODE,
                connect_timeout=30
            )
            conn.autocommit = False
            cursor = conn.cursor()
            
            # Disable FK checks for synthetic data
            cursor.execute("SET CONSTRAINTS ALL DEFERRED;")
            
            # Insert sales orders
            if sales_orders_list:
                insert_sql = """
                    INSERT INTO sales_orders (
                        sales_order_id, sales_order_number, customer_id, customer_po_number,
                        sales_organization, distribution_channel, division, order_date,
                        requested_delivery_date, order_status, currency, total_net_value,
                        total_value, created_by, created_at
                    ) VALUES (
                        %(sales_order_id)s, %(sales_order_number)s, %(customer_id)s, %(customer_po_number)s,
                        %(sales_organization)s, %(distribution_channel)s, %(division)s, %(order_date)s,
                        %(requested_delivery_date)s, %(order_status)s, %(currency)s, %(total_net_value)s,
                        %(total_value)s, %(created_by)s, %(created_at)s
                    )
                    ON CONFLICT (sales_order_number) DO NOTHING
                """
                
                logger.info(f"Inserting {len(sales_orders_list):,} sales orders...")
                execute_batch(cursor, insert_sql, sales_orders_list, page_size=5000)
                conn.commit()
                logger.info(f"  ✓ Flushed {len(sales_orders_list):,} sales orders")
            
            # Insert sales order lines
            if sales_order_lines_list:
                insert_sql = """
                    INSERT INTO sales_order_lines (
                        sales_order_line_id, sales_order_id, line_number, material_id,
                        product_id, material_description, order_quantity, unit_of_measure,
                        unit_price, net_price, requested_delivery_date, line_status,
                        make_to_order, created_at
                    ) VALUES (
                        %(sales_order_line_id)s, %(sales_order_id)s, %(line_number)s, %(material_id)s,
                        %(product_id)s, %(material_description)s, %(order_quantity)s, %(unit_of_measure)s,
                        %(unit_price)s, %(net_price)s, %(requested_delivery_date)s, %(line_status)s,
                        %(make_to_order)s, %(created_at)s
                    )
                    ON CONFLICT (sales_order_line_id) DO NOTHING
                """
                
                logger.info(f"Inserting {len(sales_order_lines_list):,} sales order lines...")
                execute_batch(cursor, insert_sql, sales_order_lines_list, page_size=5000)
                conn.commit()
                logger.info(f"  ✓ Flushed {len(sales_order_lines_list):,} sales order lines")
            
            # Insert purchase requisitions
            if purchase_requisitions_list:
                insert_sql = """
                    INSERT INTO purchase_requisitions (
                        requisition_id, requisition_number, requisition_type, requisition_date,
                        required_date, requester_id, cost_center_id, plant_id, priority,
                        approval_status, overall_status, source_type, source_document, created_at
                    ) VALUES (
                        %(requisition_id)s, %(requisition_number)s, %(requisition_type)s, %(requisition_date)s,
                        %(required_date)s, %(requester_id)s, %(cost_center_id)s, %(plant_id)s, %(priority)s,
                        %(approval_status)s, %(overall_status)s, %(source_type)s, %(source_document)s, %(created_at)s
                    )
                    ON CONFLICT (requisition_number) DO NOTHING
                """
                
                logger.info(f"Inserting {len(purchase_requisitions_list):,} purchase requisitions...")
                execute_batch(cursor, insert_sql, purchase_requisitions_list, page_size=5000)
                conn.commit()
                logger.info(f"  ✓ Flushed {len(purchase_requisitions_list):,} purchase requisitions")
            
            # Insert purchase orders
            if purchase_orders_list:
                insert_sql = """
                    INSERT INTO purchase_orders (
                        purchase_order_id, po_number, supplier_id, po_date, po_type,
                        currency, po_status, total_value, created_at
                    ) VALUES (
                        %(purchase_order_id)s, %(po_number)s, %(supplier_id)s, %(po_date)s, %(po_type)s,
                        %(currency)s, %(po_status)s, %(total_value)s, %(created_at)s
                    )
                    ON CONFLICT (po_number) DO NOTHING
                """
                
                logger.info(f"Inserting {len(purchase_orders_list):,} purchase orders...")
                execute_batch(cursor, insert_sql, purchase_orders_list, page_size=5000)
                conn.commit()
                logger.info(f"  ✓ Flushed {len(purchase_orders_list):,} purchase orders")
            
            # Insert PO lines
            if purchase_order_lines_list:
                insert_sql = """
                    INSERT INTO purchase_order_lines (
                        po_line_id, purchase_order_id, line_number, material_id, material_description,
                        order_quantity, unit_of_measure, unit_price, net_price, delivery_date,
                        line_status, requisition_id, requisition_line, created_at
                    ) VALUES (
                        %(po_line_id)s, %(purchase_order_id)s, %(line_number)s, %(material_id)s, %(material_description)s,
                        %(order_quantity)s, %(unit_of_measure)s, %(unit_price)s, %(net_price)s, %(delivery_date)s,
                        %(line_status)s, %(requisition_id)s, %(requisition_line)s, %(created_at)s
                    )
                    ON CONFLICT (po_line_id) DO NOTHING
                """
                
                logger.info(f"Inserting {len(purchase_order_lines_list):,} PO lines...")
                execute_batch(cursor, insert_sql, purchase_order_lines_list, page_size=5000)
                conn.commit()
                logger.info(f"  ✓ Flushed {len(purchase_order_lines_list):,} PO lines")
            
            # Insert goods receipts
            if goods_receipts_list:
                insert_sql = """
                    INSERT INTO goods_receipts (
                        goods_receipt_id, gr_number, gr_date, posting_date, purchase_order_id,
                        po_line_id, supplier_id, material_id, quantity_received, unit_of_measure,
                        plant_id, storage_location, batch_number, quality_status, unit_price,
                        total_value, gr_status, created_at
                    ) VALUES (
                        %(goods_receipt_id)s, %(gr_number)s, %(gr_date)s, %(posting_date)s, %(purchase_order_id)s,
                        %(po_line_id)s, %(supplier_id)s, %(material_id)s, %(quantity_received)s, %(unit_of_measure)s,
                        %(plant_id)s, %(storage_location)s, %(batch_number)s, %(quality_status)s, %(unit_price)s,
                        %(total_value)s, %(gr_status)s, %(created_at)s
                    )
                    ON CONFLICT (gr_number) DO NOTHING
                """
                
                logger.info(f"Inserting {len(goods_receipts_list):,} goods receipts...")
                execute_batch(cursor, insert_sql, goods_receipts_list, page_size=5000)
                conn.commit()
                logger.info(f"  ✓ Flushed {len(goods_receipts_list):,} goods receipts")
            
            # Insert MRP runs
            if mrp_runs_list:
                insert_sql = """
                    INSERT INTO mrp_runs (
                        mrp_run_id, run_number, planning_date, planning_horizon_days,
                        planning_mode, create_purchase_requisitions, create_production_orders,
                        run_status, started_at, completed_at, materials_planned,
                        purchase_reqs_created, production_orders_created, created_at
                    ) VALUES (
                        %(mrp_run_id)s, %(run_number)s, %(planning_date)s, %(planning_horizon_days)s,
                        %(planning_mode)s, %(create_purchase_requisitions)s, %(create_production_orders)s,
                        %(run_status)s, %(started_at)s, %(completed_at)s, %(materials_planned)s,
                        %(purchase_reqs_created)s, %(production_orders_created)s, %(created_at)s
                    )
                    ON CONFLICT (run_number) DO NOTHING
                """
                
                logger.info(f"Inserting {len(mrp_runs_list):,} MRP runs...")
                execute_batch(cursor, insert_sql, mrp_runs_list, page_size=5000)
                conn.commit()
                logger.info(f"  ✓ Flushed {len(mrp_runs_list):,} MRP runs")
            
            # Insert production orders
            if production_orders_list:
                insert_sql = """
                    INSERT INTO production_orders (
                        production_order_id, production_order_number, material_id, plant_id,
                        sales_order_id, order_type, order_quantity, basic_start_date,
                        basic_end_date, system_status, priority, created_at
                    ) VALUES (
                        %(production_order_id)s, %(production_order_number)s, %(material_id)s, %(plant_id)s,
                        %(sales_order_id)s, %(order_type)s, %(order_quantity)s, %(basic_start_date)s,
                        %(basic_end_date)s, %(system_status)s, %(priority)s, %(created_at)s
                    )
                    ON CONFLICT (production_order_number) DO NOTHING
                """
                
                logger.info(f"Inserting {len(production_orders_list):,} production orders...")
                execute_batch(cursor, insert_sql, production_orders_list, page_size=5000)
                conn.commit()
                logger.info(f"  ✓ Flushed {len(production_orders_list):,} production orders")
            
            # Insert inventory transactions
            if inventory_transactions_list:
                insert_sql = """
                    INSERT INTO inventory_transactions (
                        transaction_id, material_document, document_item, transaction_type,
                        movement_type, posting_date, document_date, material_id, plant_id,
                        storage_location, quantity, unit_of_measure, amount, purchase_order_id,
                        goods_receipt_id, created_by, created_at
                    ) VALUES (
                        %(transaction_id)s, %(material_document)s, %(document_item)s, %(transaction_type)s,
                        %(movement_type)s, %(posting_date)s, %(document_date)s, %(material_id)s, %(plant_id)s,
                        %(storage_location)s, %(quantity)s, %(unit_of_measure)s, %(amount)s, %(purchase_order_id)s,
                        %(goods_receipt_id)s, %(created_by)s, %(created_at)s
                    )
                    ON CONFLICT (transaction_id) DO NOTHING
                """
                
                logger.info(f"Inserting {len(inventory_transactions_list):,} inventory transactions...")
                execute_batch(cursor, insert_sql, inventory_transactions_list, page_size=5000)
                conn.commit()
                logger.info(f"  ✓ Flushed {len(inventory_transactions_list):,} inventory transactions")
            
            # Insert GL transactions
            if general_ledger_list:
                insert_sql = """
                    INSERT INTO general_ledger (
                        gl_transaction_id, document_number, document_type, posting_date,
                        document_date, gl_account, company_code, debit_amount, credit_amount,
                        currency, text, created_at
                    ) VALUES (
                        %(gl_transaction_id)s, %(document_number)s, %(document_type)s, %(posting_date)s,
                        %(document_date)s, %(gl_account)s, %(company_code)s, %(debit_amount)s, %(credit_amount)s,
                        %(currency)s, %(text)s, %(created_at)s
                    )
                    ON CONFLICT (gl_transaction_id) DO NOTHING
                """
                
                logger.info(f"Inserting {len(general_ledger_list):,} GL transactions...")
                execute_batch(cursor, insert_sql, general_ledger_list, page_size=5000)
                conn.commit()
                logger.info(f"  ✓ Flushed {len(general_ledger_list):,} GL transactions")
            
            cursor.close()
            conn.close()
            
            logger.info(f"✓ All records inserted successfully")
            
        except Exception as e:
            logger.error(f"PostgreSQL error: {e}")
            return 1
    
    elapsed = time.time() - start_time
    
    # Get final counts after insertion
    counts_after = get_all_table_counts()
    
    logger.info("="*80)
    logger.info("GENERATION & INSERTION COMPLETE")
    logger.info("="*80)
    logger.info(f"  Total time: {elapsed:.1f} seconds ({elapsed/60:.1f} minutes)")
    logger.info("")
    logger.info("📊 DATABASE SUMMARY")
    logger.info("="*80)
    
    # Show before/after for all tables
    tables_list = ['sales_orders', 'sales_order_lines', 'purchase_orders', 
                   'purchase_order_lines', 'goods_receipts', 'mrp_runs',
                   'purchase_requisitions', 'production_orders', 'inventory_transactions',
                   'general_ledger']
    
    for table in tables_list:
        before = counts_before.get(table)
        after = counts_after.get(table)
        
        if before is not None and after is not None:
            inserted = after - before
            logger.info(f"{table:.<40} Before: {before:>10,} | After: {after:>10,} | Inserted: {inserted:>10,}")
        else:
            logger.info(f"{table:.<40} [Count unavailable]")
    
    logger.info("="*80)
    
    return 0


if __name__ == "__main__":
    os.makedirs('logs', exist_ok=True)
    sys.exit(main())
