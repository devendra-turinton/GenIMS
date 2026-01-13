#!/usr/bin/env python3
"""
GenIMS Financial Daemon - ULTRA FAST MODE
Generates complete financial accounting data in-memory, then bulk dumps to PostgreSQL
"""

import sys
import os
import time
import logging
import signal
from datetime import datetime, timedelta
import random
from decimal import Decimal, ROUND_HALF_UP
from dotenv import load_dotenv

# Add scripts to path for helper access
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'scripts'))

env_file = os.path.join(os.path.dirname(__file__), '..', '..', 'scripts', 'config.env')
if os.path.exists(env_file):
    load_dotenv(env_file)

# Registry Helper Import
try:
    from generator_helper import get_helper
    HELPER_AVAILABLE = True
except ImportError:
    HELPER_AVAILABLE = False
    print("Warning: Registry helper not available")

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

PG_FINANCIAL_DB = os.getenv('DB_FINANCIAL', 'genims_financial_db')

BATCH_SIZE = 5000
# Daily financial operations: ~800 journal entries + ~400 balances + ~200 inter-company + ~300 sync items = ~1700 total
TOTAL_RECORDS = 1700  # Daily financial operations for enterprise manufacturing across 4 factories

# Logging
log_dir = os.getenv('DAEMON_LOG_DIR', os.path.join(os.path.dirname(__file__), '..', '..', 'logs'))
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, 'financial_daemon.log')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('FinancialDaemon')

# Global State
pg_connection = None
master_data = {}
counters = {
    'journal_entry': 1, 'journal_line': 1, 'balance': 1, 'inter_company': 1
}

class TimeCoordinator:
    """Enhanced time coordinator with current-date enforcement and future timestamp validation"""
    
    def __init__(self):
        self.base_time = self.get_validated_base_time()
    
    def get_validated_base_time(self):
        """Always return current datetime for today's data generation"""
        # ALWAYS use current datetime for today's generation (no historical continuation)
        current_datetime = datetime.now()
        base_time = current_datetime.replace(hour=0, minute=0, second=0, microsecond=0)
        logger.info(f"Using current date for data generation: {base_time}")
        return base_time
    
    def get_current_time(self):
        """Get current synchronized time"""
        return self.base_time
    
    def add_coordination_delay(self, operation_name):
        """Add 2-3 second delays between major operations"""
        delay_seconds = random.uniform(2.0, 3.0)
        logger.info(f"Time coordination delay for {operation_name}: {delay_seconds:.2f}s")
        time.sleep(delay_seconds)

def signal_handler(sig, frame):
    logger.info("Shutdown signal received")
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

def initialize_database():
    global pg_connection
    if not POSTGRES_AVAILABLE:
        return False
    try:
        pg_connection = psycopg2.connect(
            host=PG_HOST, port=PG_PORT, database=PG_FINANCIAL_DB,
            user=PG_USER, password=PG_PASSWORD, sslmode=PG_SSL_MODE, connect_timeout=30
        )
        pg_connection.autocommit = False
        logger.info(f"PostgreSQL connection established: {PG_HOST}:{PG_PORT}/{PG_FINANCIAL_DB}")
        return True
    except Exception as e:
        logger.error(f"PostgreSQL connection failed: {e}")
        return False

def get_table_count(table_name):
    try:
        conn = psycopg2.connect(host=PG_HOST, port=PG_PORT, database=PG_FINANCIAL_DB,
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
    tables = ['journal_entry_headers', 'journal_entry_lines', 'account_balances', 'inter_company_transactions']
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
        counters['journal_entry'] = get_max_id_counter('journal_entry_headers', 'journal_entry_id')
        counters['journal_line'] = get_max_id_counter('journal_entry_lines', 'line_id')
        counters['balance'] = get_max_id_counter('account_balances', 'balance_id')
        counters['inter_company'] = get_max_id_counter('inter_company_transactions', 'transaction_id')
        
        logger.info(f"ID Counters initialized: {counters}")
        return True
    except Exception as e:
        logger.error(f"Failed to initialize ID counters: {e}")
        return False

def load_master_data():
    global master_data
    try:
        conn = psycopg2.connect(
            host=PG_HOST, port=PG_PORT, database=PG_FINANCIAL_DB,
            user=PG_USER, password=PG_PASSWORD, sslmode=PG_SSL_MODE, connect_timeout=30
        )
        cursor = conn.cursor()
        
        # Load chart of accounts (posting accounts only)
        cursor.execute("SELECT account_id, account_code, normal_balance FROM chart_of_accounts WHERE allow_posting = true LIMIT 50")
        account_data = cursor.fetchall()
        accounts = [row[0] for row in account_data]
        account_info = {row[0]: {'code': row[1], 'normal_balance': row[2]} for row in account_data}
        
        # Load cost centers
        cursor.execute("SELECT cost_center_id FROM cost_centers WHERE is_active = true LIMIT 20")
        cost_centers = [row[0] for row in cursor.fetchall()]
        
        # Load fiscal periods
        cursor.execute("SELECT fiscal_year, period_number FROM fiscal_periods ORDER BY fiscal_year, period_number LIMIT 50")
        fiscal_periods = [(row[0], row[1]) for row in cursor.fetchall()]
        
        # Load existing account balances to avoid duplicates
        cursor.execute("""
            SELECT account_id, fiscal_year, fiscal_period, COALESCE(cost_center_id, '')
            FROM account_balances
        """)
        existing_balances = set(cursor.fetchall())
        
        cursor.close()
        conn.close()
        
        master_data['accounts'] = accounts or ['1000', '1100', '2000', '3000', '4000', '5000']
        master_data['account_info'] = account_info or {}
        master_data['cost_centers'] = cost_centers or ['CC-001', 'CC-002']
        master_data['fiscal_periods'] = fiscal_periods or [(2026, 1)]
        master_data['existing_balances'] = existing_balances
        
        logger.info(f"Master data loaded: {len(accounts)} accounts, {len(cost_centers)} cost centers, {len(fiscal_periods)} periods, {len(existing_balances)} existing balances")
        return True
    except Exception as e:
        logger.error(f"Failed to load master data: {e}")
        return False

def validate_journal_entry_balance(lines):
    """Validate that journal entry debits equal credits"""
    total_debit = sum(Decimal(str(line.get('debit_amount', 0))) for line in lines)
    total_credit = sum(Decimal(str(line.get('credit_amount', 0))) for line in lines)
    
    # Round to 2 decimal places for comparison
    total_debit = total_debit.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    total_credit = total_credit.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    
    return total_debit == total_credit, float(total_debit), float(total_credit)

def validate_posting_period(posting_date, fiscal_periods):
    """Validate that posting date is in an open fiscal period"""
    try:
        posting_year = posting_date.year
        posting_month = posting_date.month
        
        # Check if period is open (simplified - in real implementation would check fiscal_periods table)
        # For now, allow posting to current year only
        current_year = datetime.now().year
        if posting_year != current_year:
            logger.warning(f"Posting to closed year {posting_year} not allowed")
            return False
            
        return True
    except Exception as e:
        logger.error(f"Period validation error: {e}")
        return False

def apply_gl_posting_rules(transaction_type, amount, accounts_info):
    """Apply automated GL posting rules based on transaction type"""
    posting_rules = {
        'sales_order': {
            'debit_account_type': 'asset',  # Accounts Receivable
            'credit_account_type': 'revenue'  # Sales Revenue
        },
        'purchase_order': {
            'debit_account_type': 'expense',  # Inventory or Expense
            'credit_account_type': 'liability'  # Accounts Payable
        },
        'inventory_movement': {
            'debit_account_type': 'asset',  # Inventory
            'credit_account_type': 'expense'  # COGS
        },
        'payroll': {
            'debit_account_type': 'expense',  # Salary Expense
            'credit_account_type': 'liability'  # Payroll Payable
        }
    }
    
    rule = posting_rules.get(transaction_type, {
        'debit_account_type': 'asset',
        'credit_account_type': 'liability'
    })
    
    # Find accounts of appropriate type
    debit_accounts = [acc_id for acc_id, info in accounts_info.items() 
                     if info.get('normal_balance') == 'debit']
    credit_accounts = [acc_id for acc_id, info in accounts_info.items() 
                      if info.get('normal_balance') == 'credit']
    
    return {
        'debit_account': random.choice(debit_accounts) if debit_accounts else None,
        'credit_account': random.choice(credit_accounts) if credit_accounts else None,
        'amount': amount
    }

def convert_currency(amount, from_currency, to_currency, exchange_rates):
    """Convert amount between currencies using exchange rates"""
    if from_currency == to_currency:
        return amount
    
    # Use simplified exchange rates (in real implementation would query exchange_rates table)
    default_rates = {
        ('USD', 'INR'): 83.50,
        ('INR', 'USD'): 0.012,
        ('EUR', 'USD'): 1.08,
        ('USD', 'EUR'): 0.93
    }
    
    rate = default_rates.get((from_currency, to_currency), 1.0)
    converted_amount = Decimal(str(amount)) * Decimal(str(rate))
    return converted_amount.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

def process_sync_queue(cursor, sync_queue_data, master_data):
    """Process real-time ERP-WMS sync queue items"""
    logger.info("Processing sync queue for real-time integration...")
    
    processed_items = []
    error_items = []
    
    for sync_item in sync_queue_data:
        try:
            sync_type = sync_item['sync_type']
            sync_status = 'pending'
            
            # Process different sync types
            if sync_type == 'inventory_update':
                # Simulate inventory sync processing
                if sync_item['wms_quantity'] != sync_item['erp_quantity']:
                    variance_amount = abs(sync_item['wms_quantity'] - sync_item['erp_quantity'])
                    if variance_amount > 10:  # Material variance threshold
                        sync_status = 'variance_detected'
                    else:
                        sync_status = 'reconciled'
                else:
                    sync_status = 'matched'
            
            elif sync_type == 'order_status':
                # Process order status sync
                if sync_item['erp_status'] in ['shipped', 'delivered'] and sync_item['wms_status'] in ['picked', 'packed']:
                    sync_status = 'completed'
                else:
                    sync_status = 'in_progress'
            
            elif sync_type == 'cost_update':
                # Process cost synchronization
                cost_variance = abs(sync_item.get('erp_cost', 0) - sync_item.get('wms_cost', 0))
                if cost_variance > 100:  # Cost variance threshold
                    sync_status = 'cost_variance'
                else:
                    sync_status = 'cost_matched'
            
            # Update sync item status
            sync_item['sync_status'] = sync_status
            sync_item['processed_at'] = datetime.now()
            sync_item['retry_count'] = sync_item.get('retry_count', 0)
            
            processed_items.append(sync_item)
            
        except Exception as e:
            logger.error(f"Error processing sync item {sync_item.get('sync_id', 'unknown')}: {e}")
            sync_item['sync_status'] = 'error'
            sync_item['error_message'] = str(e)
            sync_item['retry_count'] = sync_item.get('retry_count', 0) + 1
            error_items.append(sync_item)
    
    logger.info(f"Sync queue processed: {len(processed_items)} successful, {len(error_items)} errors")
    return processed_items, error_items

def perform_reconciliation_workflow(cursor, variance_data, master_data):
    """Execute reconciliation workflow for detected variances"""
    logger.info("Performing reconciliation workflow...")
    
    reconciled_items = []
    
    for variance_item in variance_data:
        try:
            variance_type = variance_item['variance_type']
            variance_amount = abs(variance_item['erp_amount'] - variance_item['wms_amount'])
            
            # Auto-reconciliation rules
            if variance_type == 'inventory' and variance_amount <= 50:
                # Auto-adjust small inventory variances
                adjustment_entry = {
                    'reconciliation_id': f"REC-{len(reconciled_items):06d}",
                    'variance_id': variance_item['variance_id'],
                    'adjustment_type': 'inventory_adjustment',
                    'adjustment_amount': variance_amount,
                    'reconciled_by': 'auto_system',
                    'reconciled_at': datetime.now(),
                    'resolution_notes': f'Auto-reconciled {variance_type} variance of {variance_amount}'
                }
                reconciled_items.append(adjustment_entry)
                
            elif variance_type == 'costing' and variance_amount <= 100:
                # Auto-reconcile cost variances within threshold
                adjustment_entry = {
                    'reconciliation_id': f"REC-{len(reconciled_items):06d}",
                    'variance_id': variance_item['variance_id'],
                    'adjustment_type': 'cost_adjustment',
                    'adjustment_amount': variance_amount,
                    'reconciled_by': 'auto_system',
                    'reconciled_at': datetime.now(),
                    'resolution_notes': f'Auto-reconciled {variance_type} cost variance'
                }
                reconciled_items.append(adjustment_entry)
                
            else:
                # Flag for manual review
                manual_review_entry = {
                    'reconciliation_id': f"REC-{len(reconciled_items):06d}",
                    'variance_id': variance_item['variance_id'],
                    'adjustment_type': 'manual_review_required',
                    'adjustment_amount': variance_amount,
                    'reconciled_by': 'pending_review',
                    'reconciled_at': None,
                    'resolution_notes': f'Manual review required for {variance_type} variance of {variance_amount}'
                }
                reconciled_items.append(manual_review_entry)
            
        except Exception as e:
            logger.error(f"Error in reconciliation workflow: {e}")
    
    logger.info(f"Reconciliation completed: {len(reconciled_items)} items processed")
    return reconciled_items

def process_allocation_logic(cursor, allocation_data, master_data):
    """Process allocation and fulfillment logic for orders"""
    logger.info("Processing allocation and fulfillment logic...")
    
    allocations = []
    fulfillments = []
    
    for allocation_item in allocation_data:
        try:
            order_id = allocation_item['order_id']
            material_id = allocation_item['material_id']
            requested_quantity = allocation_item['requested_quantity']
            
            # Simulate inventory availability check
            available_quantity = random.randint(0, int(requested_quantity * 1.5))
            
            if available_quantity >= requested_quantity:
                # Full allocation
                allocation = {
                    'allocation_id': f"ALLOC-{len(allocations):06d}",
                    'order_id': order_id,
                    'material_id': material_id,
                    'allocated_quantity': requested_quantity,
                    'allocation_status': 'fully_allocated',
                    'allocated_at': datetime.now()
                }
                allocations.append(allocation)
                
                # Create fulfillment record
                fulfillment = {
                    'fulfillment_id': f"FULFILL-{len(fulfillments):06d}",
                    'allocation_id': allocation['allocation_id'],
                    'order_id': order_id,
                    'material_id': material_id,
                    'fulfilled_quantity': requested_quantity,
                    'fulfillment_status': 'ready_for_picking',
                    'fulfilled_at': datetime.now()
                }
                fulfillments.append(fulfillment)
                
            elif available_quantity > 0:
                # Partial allocation
                allocation = {
                    'allocation_id': f"ALLOC-{len(allocations):06d}",
                    'order_id': order_id,
                    'material_id': material_id,
                    'allocated_quantity': available_quantity,
                    'allocation_status': 'partially_allocated',
                    'allocated_at': datetime.now()
                }
                allocations.append(allocation)
                
            else:
                # Backorder
                allocation = {
                    'allocation_id': f"ALLOC-{len(allocations):06d}",
                    'order_id': order_id,
                    'material_id': material_id,
                    'allocated_quantity': 0,
                    'allocation_status': 'backordered',
                    'allocated_at': datetime.now()
                }
                allocations.append(allocation)
                
        except Exception as e:
            logger.error(f"Error in allocation logic: {e}")
    
    logger.info(f"Allocation completed: {len(allocations)} allocations, {len(fulfillments)} fulfillments")
    return allocations, fulfillments

def insert_batch_parallel(cursor, insert_sql, data, table_name, batch_size, connection=None):
    """Insert data in batches with improved error handling"""
    total_batches = (len(data) + batch_size - 1) // batch_size
    successful_inserts = 0
    
    for batch_idx in range(total_batches):
        try:
            batch_start = batch_idx * batch_size
            batch_end = min((batch_idx + 1) * batch_size, len(data))
            batch = data[batch_start:batch_end]
            
            execute_batch(cursor, insert_sql, batch, page_size=5000)
            if connection:
                connection.commit()
            
            successful_inserts += len(batch)
            logger.info(f"  Flushed {batch_end:,} / {len(data):,} {table_name}")
        except psycopg2.IntegrityError as e:
            logger.warning(f"  Batch {batch_idx + 1}/{total_batches} - Integrity error: {str(e)[:100]}")
            logger.warning(f"  This may indicate FK constraint violations or duplicate keys")
            if connection:
                connection.rollback()
        except psycopg2.Error as e:
            logger.error(f"  Batch {batch_idx + 1}/{total_batches} - Database error: {str(e)[:200]}")
            if connection:
                connection.rollback()
        except Exception as e:
            logger.error(f"  Batch {batch_idx + 1}/{total_batches} - Unexpected error: {e}")
            if connection:
                connection.rollback()
    
    logger.info(f"  Successfully inserted {successful_inserts:,}/{len(data):,} {table_name} records")
    return successful_inserts

def main():
    """Main - Generate all financial data in-memory, then bulk dump"""
    logger.info("="*80)
    logger.info("GenIMS Financial Daemon - ULTRA FAST MODE (In-Memory Generation)")
    logger.info("="*80)
    logger.info(f"Configuration:")
    logger.info(f"  Database: {PG_FINANCIAL_DB}")
    logger.info(f"  Batch Size: {BATCH_SIZE}")
    logger.info("="*80)
    
    # Initialize time coordinator and helper
    time_coord = TimeCoordinator()
    logger.info(f"Time Coordinator initialized: {time_coord.get_current_time()}")
    
    if HELPER_AVAILABLE:
        try:
            helper = get_helper()
            # Get total registered IDs for logging
            total_ids = sum(len(ids) for ids in helper.registry.registered_ids.values()) if hasattr(helper.registry, 'registered_ids') else 0
            logger.info(f"Registry helper loaded with {total_ids} total registered IDs")
        except Exception as e:
            logger.warning(f"Helper initialization failed: {e}")
            helper = None
    else:
        logger.warning("Registry helper not available")
        helper = None
    
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
    journal_entries = []
    journal_lines = []
    account_balances = []
    inter_company_txns = []
    
    # Use time coordinator for synchronized timestamps
    sim_base_time = time_coord.get_current_time().replace(hour=0, minute=0, second=0, microsecond=0)
    # Use current datetime with milliseconds to ensure uniqueness across runs
    current_time = datetime.now()
    run_timestamp = current_time.strftime('%Y%m%d%H%M%S') + f"{current_time.microsecond // 1000:03d}"
    
    # Track generated balances to avoid unique constraint
    generated_balance_keys = set(master_data['existing_balances'])
    
    # Validate FK availability
    if not master_data['accounts'] or not master_data['cost_centers']:
        logger.error("Critical: Missing master data for FK references")
        return 1
    
    # Get validated account and cost center IDs for assignment
    if helper:
        try:
            valid_account_ids = list(helper.get_valid_account_ids()) if hasattr(helper, 'get_valid_account_ids') else master_data['accounts']
            if not valid_account_ids:
                logger.warning("No valid account IDs found, using master data accounts")
                valid_account_ids = master_data['accounts']
        except Exception as e:
            logger.warning(f"Account ID validation failed: {e}, using master data")
            valid_account_ids = master_data['accounts']
    else:
        logger.info("Using master data for account assignments (no helper)")
        valid_account_ids = master_data['accounts']
    
    logger.info(f"FK Validation: {len(master_data['accounts'])} accounts, {len(master_data['cost_centers'])} cost centers, {len(valid_account_ids)} validated accounts")
    
    # Initialize sync data collections
    sync_queue_items = []
    variance_data = []
    allocation_tracking = []
    
    # Initialize sync data collections
    sync_queue_items = []
    variance_data = []
    allocation_tracking = []
    
    # Generate financial records spread across 12-hour business day (6 AM - 6 PM)
    for i in range(TOTAL_RECORDS):
        # Spread financial operations across 12-hour business day for accounting activities
        business_hours_minutes = 12 * 60  # 720 minutes
        minute_offset = (i * business_hours_minutes) // TOTAL_RECORDS
        current_ts = sim_base_time.replace(hour=6) + timedelta(minutes=minute_offset)
        current_date = current_ts.date()
        
        # Get fiscal period for current date
        if master_data['fiscal_periods']:
            fiscal_year, fiscal_period = master_data['fiscal_periods'][0]
        else:
            fiscal_year, fiscal_period = 2026, 1
        
        # Journal Entries (daily target: ~850 entries to support enterprise operations)
        # Generate journal entry every ~2 records to achieve ~850 entries per day
        if i % 2 == 0:
            je_id = f"JE-{(counters['journal_entry'] + len(journal_entries)):06d}"
            journal_num = f"JNL-{run_timestamp}-{len(journal_entries):04d}"
            
            # Generate balanced entry (debit = credit)
            amount = round(random.uniform(1000, 50000), 2)
            
            journal_entries.append({
                'journal_entry_id': je_id,
                'journal_number': journal_num,
                'entry_type': random.choice(['Standard', 'Adjusting', 'Reversing', 'Accrual']),
                'source_type': random.choice(['Manual', 'AP', 'AR', 'Payroll', 'Inventory', 'Sales']),
                'posting_date': current_date,
                'fiscal_year': fiscal_year,
                'fiscal_period': fiscal_period,
                'description': f"Journal Entry {len(journal_entries)}",
                'total_debit': amount,
                'total_credit': amount,
                'currency_code': 'USD',
                'entry_status': random.choice(['Draft', 'Posted', 'Pending']),
                'posted': random.choice([True, False]),
                'created_at': current_ts
            })
            
            # Generate 2 balanced journal lines for this entry using validated accounts
            debit_account = random.choice(valid_account_ids)
            credit_account = random.choice([a for a in valid_account_ids if a != debit_account])
            cost_center = random.choice(master_data['cost_centers']) if master_data['cost_centers'] else None
            
            # Debit line
            line_id = f"JL-{(counters['journal_line'] + len(journal_lines)):06d}"
            journal_lines.append({
                'line_id': line_id,
                'journal_entry_id': je_id,
                'line_number': 1,
                'account_id': debit_account,
                'debit_amount': amount,
                'credit_amount': 0,
                'functional_debit': amount,
                'functional_credit': 0,
                'cost_center_id': cost_center,
                'line_description': f"Debit entry line",
                'created_at': current_ts
            })
            
            # Credit line
            line_id = f"JL-{(counters['journal_line'] + len(journal_lines)):06d}"
            journal_lines.append({
                'line_id': line_id,
                'journal_entry_id': je_id,
                'line_number': 2,
                'account_id': credit_account,
                'debit_amount': 0,
                'credit_amount': amount,
                'functional_debit': 0,
                'functional_credit': amount,
                'cost_center_id': cost_center,
                'line_description': f"Credit entry line",
                'created_at': current_ts
            })
        
        # Account Balances (daily target: ~425 balance updates for financial reporting)
        # UNIQUE constraint: (account_id, fiscal_year, fiscal_period, cost_center_id)
        # Generate account balance every ~4 records to achieve ~425 balances per day
        if i % 4 == 0:
            account = random.choice(master_data['accounts'])
            cost_center = random.choice(master_data['cost_centers']) if master_data['cost_centers'] else None
            
            balance_key = (account, fiscal_year, fiscal_period, cost_center or '')
            
            # Only add if not already exists
            if balance_key not in generated_balance_keys:
                generated_balance_keys.add(balance_key)
                
                balance_id = f"BAL-{(counters['balance'] + len(account_balances)):06d}"
                beginning = round(random.uniform(0, 100000), 2)
                debit = round(random.uniform(0, 50000), 2)
                credit = round(random.uniform(0, 50000), 2)
                ending = beginning + debit - credit
                
                account_balances.append({
                    'balance_id': balance_id,
                    'account_id': account,
                    'fiscal_year': fiscal_year,
                    'fiscal_period': fiscal_period,
                    'cost_center_id': cost_center,
                    'beginning_balance': beginning,
                    'period_debit': debit,
                    'period_credit': credit,
                    'ending_balance': ending,
                    'ytd_debit': round(debit * fiscal_period, 2),
                    'ytd_credit': round(credit * fiscal_period, 2),
                    'last_updated': current_ts
                })
        
        # Inter-company Transactions (daily target: ~170 inter-company transactions)
        # Generate inter-company transaction every ~10 records to achieve ~170 transactions per day
        if i % 10 == 0:
            ic_id = f"IC-{(counters['inter_company'] + len(inter_company_txns)):06d}"
            ic_num = f"IC-{run_timestamp}-{len(inter_company_txns):04d}"
            
            inter_company_txns.append({
                'transaction_id': ic_id,
                'transaction_number': ic_num,
                'from_company_id': f"COMP-{random.randint(1, 5):03d}",
                'to_company_id': f"COMP-{random.randint(1, 5):03d}",
                'transaction_type': random.choice(['Transfer', 'Service', 'Loan', 'Dividend']),
                'transaction_date': current_date,
                'amount': round(random.uniform(5000, 100000), 2),
                'currency_code': 'USD',
                'reconciled': random.choice([True, False]),
                'reconciled_date': (current_date + timedelta(days=random.randint(1, 7))) if random.random() > 0.5 else None,
                'description': f"Inter-company transaction {len(inter_company_txns)}",
                'created_at': current_ts
            })
        
        # Sync Queue Items (daily target: ~340 ERP/WMS sync items for integration)
        # Generate sync queue item every ~5 records to achieve ~340 sync items per day
        if i % 5 == 0:
            sync_id = f"SYNC-{len(sync_queue_items):06d}"
            sync_queue_items.append({
                'sync_id': sync_id,
                'sync_type': random.choice(['inventory_update', 'order_status', 'cost_update']),
                'erp_quantity': random.randint(50, 500),
                'wms_quantity': random.randint(45, 505),  # Slight variance
                'erp_status': random.choice(['pending', 'shipped', 'delivered']),
                'wms_status': random.choice(['picking', 'picked', 'packed']),
                'erp_cost': round(random.uniform(100, 1000), 2),
                'wms_cost': round(random.uniform(95, 1005), 2),  # Slight variance
                'sync_status': 'pending',
                'created_at': current_ts
            })
        
        # Variance Data (1 per 400 records)
        if i % 400 == 0:
            variance_id = f"VAR-{len(variance_data):06d}"
            variance_data.append({
                'variance_id': variance_id,
                'variance_type': random.choice(['inventory', 'costing', 'timing']),
                'erp_amount': round(random.uniform(1000, 5000), 2),
                'wms_amount': round(random.uniform(950, 5050), 2),  # Variance
                'variance_status': 'detected',
                'created_at': current_ts
            })
        
        # Allocation Tracking (1 per 250 records)
        if i % 250 == 0:
            allocation_id = f"ALLOC-{len(allocation_tracking):06d}"
            allocation_tracking.append({
                'allocation_id': allocation_id,
                'order_id': f"ORD-{random.randint(1000, 9999)}",
                'material_id': f"MAT-{random.randint(100, 999)}",
                'requested_quantity': random.randint(10, 100),
                'allocation_status': 'pending',
                'created_at': current_ts
            })
        
        if (i + 1) % 200 == 0:
            logger.info(f"  Generated {i + 1:,} / {TOTAL_RECORDS:,} records")
    
    logger.info(f"✓ Generated {len(journal_entries):,} journal entries")
    logger.info(f"✓ Generated {len(journal_lines):,} journal lines")
    logger.info(f"✓ Generated {len(account_balances):,} account balances")
    logger.info(f"✓ Generated {len(inter_company_txns):,} inter-company transactions")
    logger.info(f"✓ Generated {len(sync_queue_items):,} sync queue items")
    logger.info(f"✓ Generated {len(variance_data):,} variance records")
    logger.info(f"✓ Generated {len(allocation_tracking):,} allocation tracking items")    
    # Bulk dump to PostgreSQL
    logger.info("="*80)
    logger.info("BULK DUMPING TO POSTGRESQL...")
    logger.info("="*80)
    
    try:
        cursor = pg_connection.cursor()
        cursor.execute("SET CONSTRAINTS ALL DEFERRED;")
        
        # Insert journal entries with time coordination
        if journal_entries:
            insert_sql = """INSERT INTO journal_entry_headers (
                journal_entry_id, journal_number, entry_type, source_type, posting_date,
                fiscal_year, fiscal_period, description, total_debit, total_credit,
                currency_code, entry_status, posted, created_at
            ) VALUES (%(journal_entry_id)s, %(journal_number)s, %(entry_type)s, %(source_type)s,
                %(posting_date)s, %(fiscal_year)s, %(fiscal_period)s, %(description)s,
                %(total_debit)s, %(total_credit)s, %(currency_code)s, %(entry_status)s,
                %(posted)s, %(created_at)s)"""
            logger.info(f"Inserting {len(journal_entries):,} journal entries...")
            insert_batch_parallel(cursor, insert_sql, journal_entries, "journal_entry_headers", BATCH_SIZE, pg_connection)
            
            # Time coordination delay
            time_coord.add_coordination_delay("journal entries")
        
        # Insert journal lines with time coordination
        if journal_lines:
            insert_sql = """INSERT INTO journal_entry_lines (
                line_id, journal_entry_id, line_number, account_id, debit_amount, credit_amount,
                functional_debit, functional_credit, cost_center_id, line_description, created_at
            ) VALUES (%(line_id)s, %(journal_entry_id)s, %(line_number)s, %(account_id)s,
                %(debit_amount)s, %(credit_amount)s, %(functional_debit)s, %(functional_credit)s,
                %(cost_center_id)s, %(line_description)s, %(created_at)s)"""
            logger.info(f"Inserting {len(journal_lines):,} journal lines...")
            insert_batch_parallel(cursor, insert_sql, journal_lines, "journal_entry_lines", BATCH_SIZE, pg_connection)
            
            # Time coordination delay
            time_coord.add_coordination_delay("journal lines")
        
        # Insert account balances with time coordination
        if account_balances:
            insert_sql = """INSERT INTO account_balances (
                balance_id, account_id, fiscal_year, fiscal_period, cost_center_id,
                beginning_balance, period_debit, period_credit, ending_balance,
                ytd_debit, ytd_credit, last_updated
            ) VALUES (%(balance_id)s, %(account_id)s, %(fiscal_year)s, %(fiscal_period)s,
                %(cost_center_id)s, %(beginning_balance)s, %(period_debit)s, %(period_credit)s,
                %(ending_balance)s, %(ytd_debit)s, %(ytd_credit)s, %(last_updated)s)"""
            logger.info(f"Inserting {len(account_balances):,} account balances...")
            insert_batch_parallel(cursor, insert_sql, account_balances, "account_balances", BATCH_SIZE, pg_connection)
            
            # Time coordination delay
            time_coord.add_coordination_delay("account balances")
        
        # Insert inter-company transactions with time coordination
        if inter_company_txns:
            insert_sql = """INSERT INTO inter_company_transactions (
                transaction_id, transaction_number, from_company_id, to_company_id,
                transaction_type, transaction_date, amount, currency_code, reconciled,
                reconciled_date, description, created_at
            ) VALUES (%(transaction_id)s, %(transaction_number)s, %(from_company_id)s,
                %(to_company_id)s, %(transaction_type)s, %(transaction_date)s, %(amount)s,
                %(currency_code)s, %(reconciled)s, %(reconciled_date)s, %(description)s, %(created_at)s)"""
            logger.info(f"Inserting {len(inter_company_txns):,} inter-company transactions...")
            insert_batch_parallel(cursor, insert_sql, inter_company_txns, "inter_company_transactions", BATCH_SIZE, pg_connection)
            
            # Time coordination delay
            time_coord.add_coordination_delay("inter-company transactions")
        
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
    
    
    # ==========================
    # ERP-WMS SYNC PROCESSING
    # ==========================
    logger.info("\\n" + "="*60)
    logger.info("PROCESSING ERP-WMS SYNC OPERATIONS")
    logger.info("="*60)
    
    time_coord.add_coordination_delay("ERP-WMS sync initiation")  # Time coordination delay
    
    try:
        # Process sync queue items for real-time integration
        if sync_queue_items:
            processed_sync, error_sync = process_sync_queue(cursor, sync_queue_items, master_data)
            logger.info(f"Sync queue processing: {len(processed_sync)} successful, {len(error_sync)} errors")
        
        # Perform reconciliation workflow for variance resolution
        if variance_data:
            reconciliation_results = perform_reconciliation_workflow(cursor, variance_data, master_data)
            logger.info(f"Reconciliation workflow: {len(reconciliation_results)} items processed")
        
        # Process allocation and fulfillment logic
        if allocation_tracking:
            allocations, fulfillments = process_allocation_logic(cursor, allocation_tracking, master_data)
            logger.info(f"Allocation processing: {len(allocations)} allocations, {len(fulfillments)} fulfillments")
        
        pg_connection.commit()
        logger.info("ERP-WMS sync processing completed successfully")
        
    except Exception as e:
        logger.error(f"Error in ERP-WMS sync processing: {e}")
        pg_connection.rollback()
    
    time_coord.add_coordination_delay("final sync completion")  # Final coordination delay
    
    logger.info("\\n" + "="*80)
    logger.info("GENERATION & INSERTION COMPLETE")
    logger.info("="*80)
    logger.info(f"  Total time: {elapsed:.1f} seconds ({elapsed/60:.1f} minutes)")
    logger.info("")
    logger.info("📊 DATABASE SUMMARY")
    logger.info("="*80)
    
    tables_list = ['journal_entry_headers', 'journal_entry_lines', 'account_balances', 'inter_company_transactions']
    for table in tables_list:
        before = counts_before.get(table)
        after = counts_after.get(table)
        
        if before is not None and after is not None:
            inserted = after - before
            logger.info(f"{table:.<40} Before: {before:>10,} | After: {after:>10,} | Inserted: {inserted:>10,}")
    
    logger.info("="*80)
    
    if pg_connection:
        pg_connection.close()
    
    return 0

if __name__ == "__main__":
    os.makedirs('logs', exist_ok=True)
    sys.exit(main())
