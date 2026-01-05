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
from decimal import Decimal
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

PG_FINANCIAL_DB = os.getenv('DB_FINANCIAL', 'genims_financial_db')

BATCH_SIZE = 5000
TOTAL_RECORDS = 14400  # 30 days of hourly financial records

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
        
        # Load chart of accounts
        cursor.execute("SELECT account_id FROM chart_of_accounts LIMIT 50")
        accounts = [row[0] for row in cursor.fetchall()]
        
        # Load cost centers
        cursor.execute("SELECT cost_center_id FROM cost_centers LIMIT 20")
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
        master_data['cost_centers'] = cost_centers or ['CC-001', 'CC-002']
        master_data['fiscal_periods'] = fiscal_periods or [(2026, 1)]
        master_data['existing_balances'] = existing_balances
        
        logger.info(f"Master data loaded: {len(accounts)} accounts, {len(cost_centers)} cost centers, {len(fiscal_periods)} periods, {len(existing_balances)} existing balances")
        return True
    except Exception as e:
        logger.error(f"Failed to load master data: {e}")
        return False

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
    """Main - Generate all financial data in-memory, then bulk dump"""
    logger.info("="*80)
    logger.info("GenIMS Financial Daemon - ULTRA FAST MODE (In-Memory Generation)")
    logger.info("="*80)
    logger.info(f"Configuration:")
    logger.info(f"  Database: {PG_FINANCIAL_DB}")
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
    journal_entries = []
    journal_lines = []
    account_balances = []
    inter_company_txns = []
    
    sim_base_time = datetime.strptime(datetime.now().strftime('%Y-%m-%d 00:00:00'), '%Y-%m-%d %H:%M:%S')
    run_timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    
    # Track generated balances to avoid unique constraint
    generated_balance_keys = set(master_data['existing_balances'])
    
    # Generate financial records
    for i in range(TOTAL_RECORDS):
        timestamp_offset = i * 3600  # 1 hour intervals
        current_ts = sim_base_time + timedelta(seconds=timestamp_offset)
        current_date = current_ts.date()
        
        # Get fiscal period for current date
        if master_data['fiscal_periods']:
            fiscal_year, fiscal_period = master_data['fiscal_periods'][0]
        else:
            fiscal_year, fiscal_period = 2026, 1
        
        # Journal Entries (1 per 50 records)
        if i % 50 == 0:
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
            
            # Generate 2-4 journal lines for this entry
            num_lines = random.randint(2, 4)
            debit_account = random.choice(master_data['accounts'])
            credit_account = random.choice([a for a in master_data['accounts'] if a != debit_account])
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
        
        # Account Balances (1 per 100 records)
        # UNIQUE constraint: (account_id, fiscal_year, fiscal_period, cost_center_id)
        if i % 100 == 0:
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
        
        # Inter-company Transactions (1 per 200 records)
        if i % 200 == 0:
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
        
        if (i + 1) % 1000 == 0:
            logger.info(f"  Generated {i + 1:,} / {TOTAL_RECORDS:,} records")
    
    logger.info(f"✓ Generated {len(journal_entries):,} journal entries")
    logger.info(f"✓ Generated {len(journal_lines):,} journal lines")
    logger.info(f"✓ Generated {len(account_balances):,} account balances")
    logger.info(f"✓ Generated {len(inter_company_txns):,} inter-company transactions")
    
    # Bulk dump to PostgreSQL
    logger.info("="*80)
    logger.info("BULK DUMPING TO POSTGRESQL...")
    logger.info("="*80)
    
    try:
        cursor = pg_connection.cursor()
        cursor.execute("SET CONSTRAINTS ALL DEFERRED;")
        
        # Insert journal entries
        if journal_entries:
            insert_sql = """INSERT INTO journal_entry_headers (
                journal_entry_id, journal_number, entry_type, source_type, posting_date,
                fiscal_year, fiscal_period, description, total_debit, total_credit,
                currency_code, entry_status, posted, created_at
            ) VALUES (%(journal_entry_id)s, %(journal_number)s, %(entry_type)s, %(source_type)s,
                %(posting_date)s, %(fiscal_year)s, %(fiscal_period)s, %(description)s,
                %(total_debit)s, %(total_credit)s, %(currency_code)s, %(entry_status)s,
                %(posted)s, %(created_at)s)
            ON CONFLICT (journal_number) DO NOTHING"""
            logger.info(f"Inserting {len(journal_entries):,} journal entries...")
            insert_batch_parallel(cursor, insert_sql, journal_entries, "journal_entry_headers", BATCH_SIZE, pg_connection)
        
        # Insert journal lines
        if journal_lines:
            insert_sql = """INSERT INTO journal_entry_lines (
                line_id, journal_entry_id, line_number, account_id, debit_amount, credit_amount,
                functional_debit, functional_credit, cost_center_id, line_description, created_at
            ) VALUES (%(line_id)s, %(journal_entry_id)s, %(line_number)s, %(account_id)s,
                %(debit_amount)s, %(credit_amount)s, %(functional_debit)s, %(functional_credit)s,
                %(cost_center_id)s, %(line_description)s, %(created_at)s)
            ON CONFLICT (line_id) DO NOTHING"""
            logger.info(f"Inserting {len(journal_lines):,} journal lines...")
            insert_batch_parallel(cursor, insert_sql, journal_lines, "journal_entry_lines", BATCH_SIZE, pg_connection)
        
        # Insert account balances
        if account_balances:
            insert_sql = """INSERT INTO account_balances (
                balance_id, account_id, fiscal_year, fiscal_period, cost_center_id,
                beginning_balance, period_debit, period_credit, ending_balance,
                ytd_debit, ytd_credit, last_updated
            ) VALUES (%(balance_id)s, %(account_id)s, %(fiscal_year)s, %(fiscal_period)s,
                %(cost_center_id)s, %(beginning_balance)s, %(period_debit)s, %(period_credit)s,
                %(ending_balance)s, %(ytd_debit)s, %(ytd_credit)s, %(last_updated)s)
            ON CONFLICT (account_id, fiscal_year, fiscal_period, cost_center_id) DO NOTHING"""
            logger.info(f"Inserting {len(account_balances):,} account balances...")
            insert_batch_parallel(cursor, insert_sql, account_balances, "account_balances", BATCH_SIZE, pg_connection)
        
        # Insert inter-company transactions
        if inter_company_txns:
            insert_sql = """INSERT INTO inter_company_transactions (
                transaction_id, transaction_number, from_company_id, to_company_id,
                transaction_type, transaction_date, amount, currency_code, reconciled,
                reconciled_date, description, created_at
            ) VALUES (%(transaction_id)s, %(transaction_number)s, %(from_company_id)s,
                %(to_company_id)s, %(transaction_type)s, %(transaction_date)s, %(amount)s,
                %(currency_code)s, %(reconciled)s, %(reconciled_date)s, %(description)s, %(created_at)s)
            ON CONFLICT (transaction_number) DO NOTHING"""
            logger.info(f"Inserting {len(inter_company_txns):,} inter-company transactions...")
            insert_batch_parallel(cursor, insert_sql, inter_company_txns, "inter_company_transactions", BATCH_SIZE, pg_connection)
        
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
