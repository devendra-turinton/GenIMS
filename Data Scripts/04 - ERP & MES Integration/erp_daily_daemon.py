#!/usr/bin/env python3
"""
GenIMS ERP Daily Business Cycle Daemon
Runs complete ERP business operations daily
"""

import sys
import time
import logging
import signal
from datetime import datetime, timedelta, time as datetime_time
import random
import json

try:
    import psycopg2
    from psycopg2.extras import execute_batch
    POSTGRES_AVAILABLE = True
except ImportError:
    POSTGRES_AVAILABLE = False
    print("WARNING: psycopg2 not installed. Install with: pip install psycopg2-binary")

# ============================================================================
# CONFIGURATION
# ============================================================================

# Database Configuration
PG_HOST = 'localhost'
PG_PORT = 5432
PG_DATABASE = 'genims_db'
PG_USER = 'genims_user'
PG_PASSWORD = 'genims_password'

# Daemon Configuration
CYCLE_INTERVAL_SECONDS = 86400  # Run every 24 hours (daily)
RUN_TIME_HOUR = 2  # 2 AM daily run

# Business Volumes (per day)
SALES_ORDERS_PER_DAY = (3, 8)
PURCHASE_ORDERS_PER_DAY = (2, 5)
GOODS_RECEIPTS_PER_DAY = (5, 10)
NEW_MATERIALS_PER_WEEK = (0, 2)

# MRP Configuration
MRP_PLANNING_HORIZON_DAYS = 90
MRP_SAFETY_STOCK_DAYS = 7

# Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/erp_daemon.log'),
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
            password=PG_PASSWORD
        )
        pg_connection.autocommit = False
        logger.info(f"PostgreSQL connection established: {PG_HOST}:{PG_PORT}/{PG_DATABASE}")
        return True
    except Exception as e:
        logger.error(f"Failed to connect to PostgreSQL: {e}")
        return False


def load_master_data():
    """Load master data from database"""
    global master_data
    
    try:
        cursor = pg_connection.cursor()
        
        # Load materials
        cursor.execute("SELECT * FROM materials WHERE material_status = 'active'")
        master_data['materials'] = [dict(zip([d[0] for d in cursor.description], row)) 
                                    for row in cursor.fetchall()]
        
        # Load suppliers
        cursor.execute("SELECT * FROM suppliers WHERE supplier_status = 'active'")
        master_data['suppliers'] = [dict(zip([d[0] for d in cursor.description], row)) 
                                    for row in cursor.fetchall()]
        
        # Load BOMs
        cursor.execute("SELECT * FROM bill_of_materials WHERE bom_status = 'active'")
        master_data['boms'] = [dict(zip([d[0] for d in cursor.description], row)) 
                              for row in cursor.fetchall()]
        
        # Load customers
        cursor.execute("SELECT * FROM customers WHERE customer_status = 'active'")
        master_data['customers'] = [dict(zip([d[0] for d in cursor.description], row)) 
                                    for row in cursor.fetchall()]
        
        # Load factories
        cursor.execute("SELECT * FROM factories WHERE is_active = true")
        master_data['factories'] = [dict(zip([d[0] for d in cursor.description], row)) 
                                    for row in cursor.fetchall()]
        
        # Load products
        cursor.execute("SELECT * FROM products WHERE is_active = true")
        master_data['products'] = [dict(zip([d[0] for d in cursor.description], row)) 
                                  for row in cursor.fetchall()]
        
        cursor.close()
        
        logger.info(f"Master data loaded: {len(master_data['materials'])} materials, "
                   f"{len(master_data['suppliers'])} suppliers, "
                   f"{len(master_data['customers'])} customers")
        
        # Initialize counters
        _initialize_counters()
        
        return True
    except Exception as e:
        logger.error(f"Failed to load master data: {e}")
        return False


def _initialize_counters():
    """Initialize counters based on existing data"""
    try:
        cursor = pg_connection.cursor()
        
        tables = {
            'material': 'materials',
            'supplier': 'suppliers',
            'bom': 'bill_of_materials',
            'sales_order': 'sales_orders',
            'prod_order': 'production_orders',
            'purchase_req': 'purchase_requisitions',
            'purchase_order': 'purchase_orders',
            'goods_receipt': 'goods_receipts',
            'inv_transaction': 'inventory_transactions',
            'mrp_run': 'mrp_runs',
            'gl_transaction': 'general_ledger'
        }
        
        for key, table in tables.items():
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                counters[key] = count + 1
            except:
                pass
        
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


def main():
    """Main daemon loop"""
    logger.info("="*80)
    logger.info("GenIMS ERP Daily Business Cycle Daemon Starting")
    logger.info(f"Scheduled run time: {RUN_TIME_HOUR:02d}:00 daily")
    logger.info("="*80)
    
    # Initialize
    if not initialize_database():
        return 1
    
    if not load_master_data():
        return 1
    
    logger.info("Press Ctrl+C to stop")
    logger.info("="*80)
    
    while running:
        try:
            cycle_start = time.time()
            current_date = datetime.now().strftime('%Y-%m-%d')
            
            logger.info(f"\n{'='*80}")
            logger.info(f"Daily ERP Business Cycle - {current_date}")
            logger.info(f"{'='*80}")
            
            # Execute daily ERP operations
            logger.info("\n1. Processing Sales Orders...")
            process_new_sales_orders()
            
            logger.info("\n2. Running MRP...")
            run_mrp()
            
            logger.info("\n3. Processing Purchase Orders...")
            process_purchase_orders()
            
            logger.info("\n4. Processing Goods Receipts...")
            process_goods_receipts()
            
            logger.info("\n5. Releasing Production Orders to MES...")
            release_production_orders()
            
            logger.info("\n6. Receiving MES Confirmations...")
            receive_mes_confirmations()
            
            logger.info("\n7. Posting Period-End Entries...")
            post_period_end_entries()
            
            stats['cycles_completed'] += 1
            
            # Print stats every cycle
            print_daily_stats()
            
            elapsed = time.time() - cycle_start
            logger.info(f"\nCycle completed in {elapsed:.1f} seconds")
            
            # Wait until next scheduled run
            wait_until_next_run()
            
        except Exception as e:
            logger.error(f"Error in main loop: {e}", exc_info=True)
            stats['errors'] += 1
            time.sleep(3600)  # Wait 1 hour before retrying
    
    # Cleanup
    logger.info("Shutting down...")
    
    if pg_connection:
        pg_connection.close()
        logger.info("PostgreSQL connection closed")
    
    print_daily_stats()
    logger.info("ERP Daily Daemon stopped")
    
    return 0


if __name__ == "__main__":
    import os
    os.makedirs('logs', exist_ok=True)
    sys.exit(main())
