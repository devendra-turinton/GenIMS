#!/usr/bin/env python3
"""
GenIMS Financial & Inventory Sync Daemon
Handles automated GL posting and real-time ERP-WMS inventory synchronization
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

# Load environment variables
env_file = os.path.join(os.path.dirname(__file__), '..', '..', 'scripts', 'config.env')
if os.path.exists(env_file):
    load_dotenv(env_file)

try:
    import psycopg2
    from psycopg2.extras import execute_batch
    POSTGRES_AVAILABLE = True
except ImportError:
    POSTGRES_AVAILABLE = False
    print("WARNING: psycopg2 not installed")

# Configuration
PG_HOST = os.getenv('POSTGRES_HOST', 'localhost')
PG_PORT = int(os.getenv('POSTGRES_PORT', '5432'))
PG_DATABASE = os.getenv('DB_FINANCIAL', 'genims_financial_db')
PG_SYNC_DATABASE = os.getenv('DB_ERP_WMS_SYNC', 'genims_erp_wms_sync_db')
PG_USER = os.getenv('POSTGRES_USER', 'postgres')
PG_PASSWORD = os.getenv('POSTGRES_PASSWORD', '')
PG_SSL_MODE = os.getenv('PG_SSL_MODE', 'require')

# Logging configuration
log_dir = os.getenv('DAEMON_LOG_DIR', os.path.join(os.path.dirname(__file__), '..', '..', 'logs'))
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, 'financial_sync_daemon.log')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('FinancialSync')

running = True
pg_connection = None
pg_sync_connection = None
posting_rules = {}
sync_mappings = {}
stats = {
    'cycles': 0,
    'journal_entries_posted': 0,
    'inventory_syncs': 0,
    'reconciliations_performed': 0,
    'sync_errors': 0,
    'start_time': datetime.now()
}

def signal_handler(sig, frame):
    global running
    logger.info("Shutdown signal received")
    running = False

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

def initialize_database():
    global pg_connection, pg_sync_connection
    if not POSTGRES_AVAILABLE:
        return False
    try:
        # Connect to financial database
        pg_connection = psycopg2.connect(
            host=PG_HOST, port=PG_PORT, database=PG_DATABASE,
            user=PG_USER, password=PG_PASSWORD,
            sslmode=PG_SSL_MODE
        )
        pg_connection.autocommit = False
        logger.info(f"PostgreSQL connected to {PG_DATABASE}")
        
        # Connect to sync database
        pg_sync_connection = psycopg2.connect(
            host=PG_HOST, port=PG_PORT, database=PG_SYNC_DATABASE,
            user=PG_USER, password=PG_PASSWORD,
            sslmode=PG_SSL_MODE
        )
        pg_sync_connection.autocommit = False
        logger.info(f"PostgreSQL connected to {PG_SYNC_DATABASE}")
        return True
    except Exception as e:
        logger.error(f"DB connection failed: {e}")
        return False

def load_configuration():
    """Load GL posting rules and sync mappings"""
    global posting_rules, sync_mappings
    try:
        # Load GL posting rules from financial database
        cursor = pg_connection.cursor()
        cursor.execute("""
            SELECT rule_id, transaction_type, transaction_subtype,
                   debit_account_id, credit_account_id, amount_field
            FROM gl_posting_rules
            WHERE is_active = true
        """)
        
        for row in cursor.fetchall():
            key = f"{row[1]}:{row[2] or 'default'}"
            posting_rules[key] = {
                'rule_id': row[0],
                'debit_account': row[3],
                'credit_account': row[4],
                'amount_field': row[5]
            }
        cursor.close()
        
        # Load sync mappings from sync database
        sync_cursor = pg_sync_connection.cursor()
        sync_cursor.execute("""
            SELECT mapping_id, erp_location_id, wms_warehouse_id
            FROM inventory_sync_mappings
            WHERE is_active = true AND sync_enabled = true
        """)
        
        for row in sync_cursor.fetchall():
            sync_mappings[row[1]] = {
                'mapping_id': row[0],
                'wms_warehouse': row[2]
            }
        sync_cursor.close()
        
        logger.info(f"Loaded {len(posting_rules)} posting rules, {len(sync_mappings)} sync mappings")
        return True
    except Exception as e:
        logger.error(f"Failed to load configuration: {e}")
        return False

def generate_id(prefix: str) -> str:
    return f"{prefix}-{datetime.now().strftime('%Y%m%d%H%M%S')}-{random.randint(1000, 9999)}"

# ============================================================================
# FINANCIAL AUTO-POSTING
# ============================================================================

def process_sales_order_posting():
    """Auto-post GL entries for invoiced sales orders"""
    logger.info("Processing sales order GL posting...")
    
    try:
        cursor = pg_connection.cursor()
        
        # Find invoiced sales orders without GL posting
        cursor.execute("""
            SELECT so.sales_order_id, so.total_amount, so.currency_code
            FROM sales_orders so
            WHERE so.order_status = 'invoiced'
            AND NOT EXISTS (
                SELECT 1 FROM journal_entry_headers jeh
                WHERE jeh.source_type = 'auto_sales'
                AND jeh.source_document_id = so.sales_order_id
                AND jeh.posted = true
            )
            LIMIT 20
        """)
        
        orders = cursor.fetchall()
        
        for order_id, amount, currency in orders:
            # Get posting rule
            rule_key = 'sales_order:invoice'
            if rule_key not in posting_rules:
                continue
            
            rule = posting_rules[rule_key]
            
            # Create journal entry
            je_id = generate_id('JE')
            je_number = f"JE-{datetime.now().strftime('%Y%m%d')}-{random.randint(1000, 9999)}"
            
            cursor.execute("""
                INSERT INTO journal_entry_headers (
                    journal_entry_id, journal_number, entry_type,
                    source_type, source_document_id, posting_date,
                    fiscal_year, fiscal_period, description,
                    total_debit, total_credit, entry_status,
                    posted, posted_by, posted_at, created_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (je_id, je_number, 'standard', 'auto_sales', order_id,
                  datetime.now().date(), datetime.now().year, datetime.now().month,
                  f"Sales invoice {order_id}", amount, amount, 'posted',
                  True, 'system', datetime.now(), datetime.now()))
            
            # Debit: AR
            cursor.execute("""
                INSERT INTO journal_entry_lines (
                    line_id, journal_entry_id, line_number, account_id,
                    debit_amount, credit_amount, line_description, created_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (generate_id('JELINE'), je_id, 1, rule['debit_account'],
                  amount, 0, 'Accounts Receivable', datetime.now()))
            
            # Credit: Revenue
            cursor.execute("""
                INSERT INTO journal_entry_lines (
                    line_id, journal_entry_id, line_number, account_id,
                    debit_amount, credit_amount, line_description, created_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (generate_id('JELINE'), je_id, 2, rule['credit_account'],
                  0, amount, 'Sales Revenue', datetime.now()))
            
            stats['journal_entries_posted'] += 1
        
        pg_connection.commit()
        cursor.close()
        
        if orders:
            logger.info(f"Posted {len(orders)} sales order GL entries")
    except Exception as e:
        logger.error(f"Error posting sales orders: {e}")
        pg_connection.rollback()

def process_production_posting():
    """Auto-post GL entries for production orders"""
    logger.info("Processing production order GL posting...")
    
    try:
        cursor = pg_connection.cursor()
        
        # Find completed production orders without GL posting
        cursor.execute("""
            SELECT po.production_order_id, po.total_cost
            FROM production_orders po
            WHERE po.order_status = 'completed'
            AND NOT EXISTS (
                SELECT 1 FROM journal_entry_headers jeh
                WHERE jeh.source_type = 'auto_production'
                AND jeh.source_document_id = po.production_order_id
                AND jeh.posted = true
            )
            LIMIT 10
        """)
        
        orders = cursor.fetchall()
        
        for order_id, cost in orders:
            # Get posting rule
            rule_key = 'production_order:completed'
            if rule_key not in posting_rules:
                continue
            
            rule = posting_rules[rule_key]
            
            # Create journal entry: Debit FG, Credit WIP
            je_id = generate_id('JE')
            je_number = f"JE-{datetime.now().strftime('%Y%m%d')}-{random.randint(1000, 9999)}"
            
            cursor.execute("""
                INSERT INTO journal_entry_headers (
                    journal_entry_id, journal_number, entry_type,
                    source_type, source_document_id, posting_date,
                    fiscal_year, fiscal_period, description,
                    total_debit, total_credit, entry_status,
                    posted, posted_by, posted_at, created_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (je_id, je_number, 'standard', 'auto_production', order_id,
                  datetime.now().date(), datetime.now().year, datetime.now().month,
                  f"Production completed {order_id}", cost, cost, 'posted',
                  True, 'system', datetime.now(), datetime.now()))
            
            # Lines
            cursor.execute("""
                INSERT INTO journal_entry_lines (
                    line_id, journal_entry_id, line_number, account_id,
                    debit_amount, credit_amount, created_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (generate_id('JELINE'), je_id, 1, rule['debit_account'],
                  cost, 0, datetime.now()))
            
            cursor.execute("""
                INSERT INTO journal_entry_lines (
                    line_id, journal_entry_id, line_number, account_id,
                    debit_amount, credit_amount, created_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (generate_id('JELINE'), je_id, 2, rule['credit_account'],
                  0, cost, datetime.now()))
            
            stats['journal_entries_posted'] += 1
        
        pg_connection.commit()
        cursor.close()
        
        if orders:
            logger.info(f"Posted {len(orders)} production GL entries")
    except Exception as e:
        logger.error(f"Error posting production: {e}")
        pg_connection.rollback()

def update_account_balances():
    """Update account balances from journal entries"""
    logger.info("Updating account balances...")
    
    try:
        cursor = pg_connection.cursor()
        
        current_year = datetime.now().year
        current_period = datetime.now().month
        
        # Get all accounts
        cursor.execute("SELECT account_id FROM chart_of_accounts WHERE is_active = true")
        accounts = cursor.fetchall()
        
        for (account_id,) in accounts:
            # Calculate period activity
            cursor.execute("""
                SELECT 
                    COALESCE(SUM(debit_amount), 0) as period_debit,
                    COALESCE(SUM(credit_amount), 0) as period_credit
                FROM journal_entry_lines jel
                JOIN journal_entry_headers jeh ON jel.journal_entry_id = jeh.journal_entry_id
                WHERE jel.account_id = %s
                AND jeh.fiscal_year = %s
                AND jeh.fiscal_period = %s
                AND jeh.posted = true
            """, (account_id, current_year, current_period))
            
            period_debit, period_credit = cursor.fetchone()
            
            # Upsert balance
            cursor.execute("""
                INSERT INTO account_balances (
                    balance_id, account_id, fiscal_year, fiscal_period,
                    period_debit, period_credit, last_updated
                ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (account_id, fiscal_year, fiscal_period, cost_center_id)
                DO UPDATE SET
                    period_debit = EXCLUDED.period_debit,
                    period_credit = EXCLUDED.period_credit,
                    last_updated = EXCLUDED.last_updated
            """, (generate_id('BAL'), account_id, current_year, current_period,
                  period_debit, period_credit, datetime.now()))
        
        pg_connection.commit()
        cursor.close()
    except Exception as e:
        logger.error(f"Error updating balances: {e}")
        pg_connection.rollback()

# ============================================================================
# INVENTORY SYNCHRONIZATION
# ============================================================================

def process_inventory_sync_queue():
    """Process pending inventory sync transactions"""
    logger.info("Processing inventory sync queue...")
    
    try:
        cursor = pg_connection.cursor()
        
        # Get pending sync items
        cursor.execute("""
            SELECT queue_id, sync_direction, transaction_type, transaction_id,
                   material_id, quantity, from_location, to_location
            FROM inventory_sync_queue
            WHERE sync_status = 'pending'
            AND retry_count < max_retries
            ORDER BY created_at
            LIMIT 50
        """)
        
        items = cursor.fetchall()
        
        for queue_id, direction, trans_type, trans_id, material, qty, from_loc, to_loc in items:
            try:
                if direction == 'ERP_TO_WMS':
                    # Sync ERP transaction to WMS
                    _sync_erp_to_wms(cursor, queue_id, trans_type, material, qty, from_loc, to_loc)
                elif direction == 'WMS_TO_ERP':
                    # Sync WMS transaction to ERP
                    _sync_wms_to_erp(cursor, queue_id, trans_type, material, qty, from_loc, to_loc)
                
                # Mark as completed
                cursor.execute("""
                    UPDATE inventory_sync_queue
                    SET sync_status = 'completed',
                        processed_at = %s,
                        acknowledged = true,
                        acknowledged_at = %s
                    WHERE queue_id = %s
                """, (datetime.now(), datetime.now(), queue_id))
                
                stats['inventory_syncs'] += 1
                
            except Exception as e:
                # Mark as error
                cursor.execute("""
                    UPDATE inventory_sync_queue
                    SET sync_status = 'error',
                        error_message = %s,
                        retry_count = retry_count + 1
                    WHERE queue_id = %s
                """, (str(e), queue_id))
                
                stats['sync_errors'] += 1
                logger.error(f"Sync error for queue {queue_id}: {e}")
        
        pg_connection.commit()
        cursor.close()
        
        if items:
            logger.info(f"Processed {len(items)} sync items")
    except Exception as e:
        logger.error(f"Error processing sync queue: {e}")
        pg_connection.rollback()

def _sync_erp_to_wms(cursor, queue_id, trans_type, material, qty, from_loc, to_loc):
    """Sync ERP transaction to WMS"""
    # In production, would call WMS API
    # For now, just log
    logger.debug(f"ERP→WMS: {trans_type} {material} qty {qty}")
    
    # Update WMS inventory snapshot
    cursor.execute("""
        UPDATE inventory_snapshot
        SET wms_on_hand = wms_on_hand + %s,
            last_wms_update = %s,
            last_sync_timestamp = %s
        WHERE material_id = %s
        AND location_id = %s
    """, (qty, datetime.now(), datetime.now(), material, to_loc or from_loc))

def _sync_wms_to_erp(cursor, queue_id, trans_type, material, qty, from_loc, to_loc):
    """Sync WMS transaction to ERP"""
    # In production, would update ERP inventory
    logger.debug(f"WMS→ERP: {trans_type} {material} qty {qty}")
    
    # Update ERP inventory snapshot
    cursor.execute("""
        UPDATE inventory_snapshot
        SET erp_on_hand = erp_on_hand + %s,
            last_erp_update = %s,
            last_sync_timestamp = %s
        WHERE material_id = %s
        AND location_id = %s
    """, (qty, datetime.now(), datetime.now(), material, to_loc or from_loc))

def reconcile_inventory():
    """Perform inventory reconciliation between ERP and WMS"""
    logger.info("Performing inventory reconciliation...")
    
    try:
        cursor = pg_connection.cursor()
        
        # Find materials with variances
        cursor.execute("""
            SELECT material_id, location_id, erp_on_hand, wms_on_hand,
                   (erp_on_hand - wms_on_hand) as variance
            FROM inventory_snapshot
            WHERE ABS(erp_on_hand - wms_on_hand) > 0.01
            AND sync_status != 'variance_major'
            LIMIT 10
        """)
        
        variances = cursor.fetchall()
        
        for material, location, erp_qty, wms_qty, variance in variances:
            # Determine variance severity
            variance_pct = abs(variance / erp_qty * 100) if erp_qty > 0 else 100
            
            if variance_pct > 10:
                status = 'variance_major'
            elif variance_pct > 2:
                status = 'variance_minor'
            else:
                status = 'synced'
            
            # Update status
            cursor.execute("""
                UPDATE inventory_snapshot
                SET variance_quantity = %s,
                    sync_status = %s
                WHERE material_id = %s
                AND location_id = %s
            """, (variance, status, material, location))
            
            if status == 'variance_major':
                logger.warning(f"Major variance: {material} at {location} - ERP:{erp_qty}, WMS:{wms_qty}")
        
        pg_connection.commit()
        cursor.close()
        
        if variances:
            stats['reconciliations_performed'] += 1
            logger.info(f"Reconciled {len(variances)} inventory items")
    except Exception as e:
        logger.error(f"Error reconciling inventory: {e}")
        pg_connection.rollback()

# ============================================================================
# MAIN CYCLE
# ============================================================================

def run_financial_sync_cycle():
    """Execute complete financial and sync cycle"""
    logger.info("=== Financial & Sync Cycle Starting ===")
    
    try:
        # Financial Operations
        process_sales_order_posting()
        process_production_posting()
        
        # Update balances every 10 cycles
        if stats['cycles'] % 10 == 0:
            update_account_balances()
        
        # Inventory Sync Operations
        process_inventory_sync_queue()
        
        # Reconciliation every 20 cycles
        if stats['cycles'] % 20 == 0:
            reconcile_inventory()
        
        stats['cycles'] += 1
        logger.info("=== Financial & Sync Cycle Complete ===")
        return True
    except Exception as e:
        logger.error(f"Cycle error: {e}")
        return False

def print_stats():
    """Print daemon statistics"""
    elapsed = (datetime.now() - stats['start_time']).total_seconds()
    hours = elapsed / 3600
    
    logger.info("="*80)
    logger.info(f"Financial & Sync Daemon Statistics")
    logger.info(f"  Uptime: {hours:.1f} hours")
    logger.info(f"  Cycles: {stats['cycles']}")
    logger.info(f"  Journal Entries Posted: {stats['journal_entries_posted']}")
    logger.info(f"  Inventory Syncs: {stats['inventory_syncs']}")
    logger.info(f"  Reconciliations: {stats['reconciliations_performed']}")
    logger.info(f"  Sync Errors: {stats['sync_errors']}")
    logger.info("="*80)

def main():
    """Main daemon loop"""
    logger.info("="*80)
    logger.info("GenIMS Financial & Inventory Sync Daemon Starting")
    logger.info("Cycle Interval: Every 5 minutes")
    logger.info("="*80)
    
    if not initialize_database():
        return 1
    
    if not load_configuration():
        return 1
    
    logger.info("Press Ctrl+C to stop")
    
    last_cycle = datetime.now() - timedelta(hours=1)
    
    while running:
        try:
            now = datetime.now()
            
            # Run every 5 minutes
            if (now - last_cycle).total_seconds() >= CYCLE_INTERVAL_SECONDS:
                run_financial_sync_cycle()
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
    logger.info("Financial & Sync Daemon stopped")
    return 0

if __name__ == "__main__":
    import os
    os.makedirs('logs', exist_ok=True)
    sys.exit(main())
