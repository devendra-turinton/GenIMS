#!/usr/bin/env python3
"""
GenIMS Supplier Portal Daemon - ULTRA FAST MODE
Generates complete supplier portal operations in-memory, then bulk dumps to PostgreSQL
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

PG_SUPPLIER_DB = os.getenv('DB_SUPPLIER', 'genims_supplier_db')

BATCH_SIZE = 5000
TOTAL_RECORDS = 14400  # 30 days worth

# Logging
log_dir = os.getenv('DAEMON_LOG_DIR', os.path.join(os.path.dirname(__file__), '..', '..', 'logs'))
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, 'supplier_portal_daemon.log')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('SupplierPortalDaemon')

# Global State
pg_connection = None
master_data = {}
counters = {
    'requisition': 1, 'rfq': 1, 'invoice': 1, 'audit': 1, 'performance': 1
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
            host=PG_HOST, port=PG_PORT, database=PG_SUPPLIER_DB,
            user=PG_USER, password=PG_PASSWORD, sslmode=PG_SSL_MODE, connect_timeout=30
        )
        pg_connection.autocommit = False
        logger.info(f"PostgreSQL connection established: {PG_HOST}:{PG_PORT}/{PG_SUPPLIER_DB}")
        return True
    except Exception as e:
        logger.error(f"PostgreSQL connection failed: {e}")
        return False

def get_table_count(table_name):
    try:
        conn = psycopg2.connect(host=PG_HOST, port=PG_PORT, database=PG_SUPPLIER_DB,
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
    tables = ['purchase_requisitions', 'rfq_headers', 'supplier_invoices', 'supplier_audits', 'supplier_performance_metrics']
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
        counters['requisition'] = get_max_id_counter('purchase_requisitions', 'requisition_id')
        counters['rfq'] = get_max_id_counter('rfq_headers', 'rfq_id')
        counters['invoice'] = get_max_id_counter('supplier_invoices', 'invoice_id')
        counters['audit'] = get_max_id_counter('supplier_audits', 'audit_id')
        counters['performance'] = get_max_id_counter('supplier_performance_metrics', 'metric_id')
        
        logger.info(f"ID Counters initialized: {counters}")
        return True
    except Exception as e:
        logger.error(f"Failed to initialize ID counters: {e}")
        return False

def load_master_data():
    global master_data
    try:
        conn = psycopg2.connect(
            host=PG_HOST, port=PG_PORT, database=PG_SUPPLIER_DB,
            user=PG_USER, password=PG_PASSWORD, sslmode=PG_SSL_MODE, connect_timeout=30
        )
        cursor = conn.cursor()
        
        # Load suppliers from supplier_contracts or other tables
        cursor.execute("SELECT DISTINCT supplier_id FROM supplier_contracts LIMIT 50")
        suppliers = [row[0] for row in cursor.fetchall()]
        
        # Load users
        cursor.execute("SELECT portal_user_id FROM supplier_portal_users LIMIT 30")
        users = [row[0] for row in cursor.fetchall()]
        
        # Load departments (might be in another DB, use placeholders)
        departments = [f"DEPT-{i:03d}" for i in range(1, 11)]
        
        # Load existing performance metrics to avoid duplicates on (supplier_id, metric_period)
        cursor.execute("""
            SELECT supplier_id, metric_period
            FROM supplier_performance_metrics
        """)
        existing_metrics = set(cursor.fetchall())
        
        cursor.close()
        conn.close()
        
        master_data['suppliers'] = suppliers or ['SUP-000001', 'SUP-000002']
        master_data['users'] = users or ['USER-000001']
        master_data['departments'] = departments
        master_data['existing_metrics'] = existing_metrics
        
        logger.info(f"Master data loaded: {len(suppliers)} suppliers, {len(users)} users")
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
    """Main - Generate all supplier portal data in-memory, then bulk dump"""
    logger.info("="*80)
    logger.info("GenIMS Supplier Portal Daemon - ULTRA FAST MODE (In-Memory Generation)")
    logger.info("="*80)
    logger.info(f"Configuration:")
    logger.info(f"  Database: {PG_SUPPLIER_DB}")
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
    requisitions = []
    rfq_headers = []
    invoices = []
    audits = []
    performance_metrics = []
    
    sim_base_time = datetime.strptime(datetime.now().strftime('%Y-%m-%d 00:00:00'), '%Y-%m-%d %H:%M:%S')
    run_timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    
    # Track unique combinations to avoid UNIQUE constraint violations
    # Load existing combinations from database
    performance_metrics_seen = set(master_data.get('existing_metrics', []))
    
    # Generate supplier portal records
    for i in range(TOTAL_RECORDS):
        timestamp_offset = i * 300  # 5 minute intervals
        current_ts = sim_base_time + timedelta(seconds=timestamp_offset)
        current_date = current_ts.date()
        
        supplier = random.choice(master_data['suppliers'])
        user = random.choice(master_data['users'])
        department = random.choice(master_data['departments'])
        
        # Purchase Requisitions (1 per 100 records)
        if i % 100 == 0:
            req_id = f"REQ-{(counters['requisition'] + i // 100):06d}"
            req_num = f"PR-{run_timestamp}-{i // 100:04d}"
            requisitions.append({
                'requisition_id': req_id,
                'requisition_number': req_num,
                'requested_by': user,
                'department_id': department,
                'requisition_date': current_date,
                'required_by_date': current_date + timedelta(days=random.randint(7, 30)),
                'requisition_type': random.choice(['Standard', 'Emergency', 'Blanket', 'Capital']),
                'requisition_status': random.choice(['Draft', 'Submitted', 'Approved', 'Rejected', 'Converted']),
                'estimated_total': round(random.uniform(1000, 50000), 2),
                'created_at': current_ts
            })
        
        # RFQ Headers (1 per 150 records)
        if i % 150 == 0:
            rfq_id = f"RFQ-{(counters['rfq'] + i // 150):06d}"
            rfq_num = f"RFQ-{run_timestamp}-{i // 150:04d}"
            rfq_headers.append({
                'rfq_id': rfq_id,
                'rfq_number': rfq_num,
                'rfq_title': f"RFQ for Items {i // 150}",
                'rfq_type': random.choice(['Standard', 'Spot Buy', 'Contract', 'Service']),
                'requested_by': user,
                'department_id': department,
                'rfq_date': current_date,
                'response_deadline': current_date + timedelta(days=random.randint(5, 15)),
                'expected_delivery_date': current_date + timedelta(days=random.randint(20, 60)),
                'rfq_status': random.choice(['Draft', 'Published', 'Responses Received', 'Evaluated', 'Awarded', 'Cancelled']),
                'total_estimated_value': round(random.uniform(5000, 100000), 2),
                'currency_code': 'USD',
                'created_at': current_ts
            })
        
        # Supplier Invoices (1 per 75 records)
        if i % 75 == 0:
            inv_id = f"INV-{(counters['invoice'] + i // 75):06d}"
            inv_num = f"SI-{run_timestamp}-{i // 75:04d}"
            supplier_inv_num = f"SUPINV-{random.randint(100000, 999999)}"
            
            subtotal = round(random.uniform(1000, 50000), 2)
            tax = round(subtotal * 0.1, 2)
            total = subtotal + tax
            
            invoices.append({
                'invoice_id': inv_id,
                'invoice_number': inv_num,
                'supplier_invoice_number': supplier_inv_num,
                'supplier_id': supplier,
                'invoice_date': current_date,
                'due_date': current_date + timedelta(days=random.randint(15, 45)),
                'subtotal': subtotal,
                'tax_amount': tax,
                'total_amount': total,
                'currency_code': 'USD',
                'invoice_status': random.choice(['Pending', 'Approved', 'Paid', 'Disputed', 'Rejected']),
                'payment_status': random.choice(['Unpaid', 'Partially Paid', 'Paid']),
                'paid_date': current_date + timedelta(days=random.randint(20, 50)) if random.random() > 0.5 else None,
                'created_at': current_ts
            })
        
        # Supplier Audits (1 per 200 records)
        if i % 200 == 0:
            audit_id = f"AUD-{(counters['audit'] + i // 200):06d}"
            audit_num = f"AUDIT-{run_timestamp}-{i // 200:04d}"
            audits.append({
                'audit_id': audit_id,
                'audit_number': audit_num,
                'supplier_id': supplier,
                'audit_type': random.choice(['Quality', 'Financial', 'Compliance', 'Security', 'Performance']),
                'actual_date': current_date,
                'lead_auditor': user,
                'audit_status': random.choice(['Scheduled', 'In Progress', 'Completed', 'Reported']),
                'audit_score': round(random.uniform(60, 100), 1),
                'audit_rating': random.choice(['Pass', 'Conditional Pass', 'Fail']),
                'followup_date': current_date + timedelta(days=random.randint(180, 365)),
                'created_at': current_ts
            })
        
        # Supplier Performance Metrics (1 per 50 records)
        # UNIQUE constraint: (supplier_id, metric_period)
        if i % 50 == 0:
            # Use year-month format for metric_period (natural business requirement)
            metric_period = f"{current_date.year}-{current_date.month:02d}"
            metric_key = (supplier, metric_period)
            
            # Only add if this supplier+period combination hasn't been seen
            if metric_key not in performance_metrics_seen:
                performance_metrics_seen.add(metric_key)
                metric_id = f"METRIC-{(counters['performance'] + len(performance_metrics)):06d}"
                performance_metrics.append({
                    'metric_id': metric_id,
                    'supplier_id': supplier,
                    'metric_period': metric_period,
                    'total_pos_issued': random.randint(10, 100),
                    'pos_delivered_ontime': random.randint(8, 95),
                    'ontime_delivery_pct': round(random.uniform(85, 100), 1),
                    'average_lead_time_days': round(random.uniform(5, 30), 1),
                    'quality_acceptance_pct': round(random.uniform(95, 100), 1),
                    'defect_ppm': random.randint(0, 100),
                    'rfqs_sent': random.randint(5, 20),
                    'rfqs_responded': random.randint(3, 18),
                    'response_rate_pct': round(random.uniform(70, 100), 1),
                    'total_spend': round(random.uniform(10000, 500000), 2),
                    'invoice_accuracy_pct': round(random.uniform(90, 100), 1),
                    'overall_score': round(random.uniform(70, 100), 1),
                    'performance_rating': random.choice(['Excellent', 'Good', 'Fair', 'Poor']),
                    'created_at': current_ts
                })
        
        if (i + 1) % 1000 == 0:
            logger.info(f"  Generated {i + 1:,} / {TOTAL_RECORDS:,} records")
    
    logger.info(f"✓ Generated {len(requisitions):,} purchase requisitions")
    logger.info(f"✓ Generated {len(rfq_headers):,} RFQ headers")
    logger.info(f"✓ Generated {len(invoices):,} supplier invoices")
    logger.info(f"✓ Generated {len(audits):,} supplier audits")
    logger.info(f"✓ Generated {len(performance_metrics):,} performance metrics")
    
    # Bulk dump to PostgreSQL
    logger.info("="*80)
    logger.info("BULK DUMPING TO POSTGRESQL...")
    logger.info("="*80)
    
    try:
        cursor = pg_connection.cursor()
        cursor.execute("SET CONSTRAINTS ALL DEFERRED;")
        
        # Insert requisitions
        if requisitions:
            insert_sql = """INSERT INTO purchase_requisitions (
                requisition_id, requisition_number, requested_by, department_id, requisition_date,
                required_by_date, requisition_type, requisition_status, estimated_total, created_at
            ) VALUES (%(requisition_id)s, %(requisition_number)s, %(requested_by)s, %(department_id)s,
                %(requisition_date)s, %(required_by_date)s, %(requisition_type)s, %(requisition_status)s,
                %(estimated_total)s, %(created_at)s)
            ON CONFLICT (requisition_number) DO NOTHING"""
            logger.info(f"Inserting {len(requisitions):,} purchase requisitions...")
            insert_batch_parallel(cursor, insert_sql, requisitions, "purchase_requisitions", BATCH_SIZE, pg_connection)
        
        # Insert RFQ headers
        if rfq_headers:
            insert_sql = """INSERT INTO rfq_headers (
                rfq_id, rfq_number, rfq_title, rfq_type, requested_by, department_id,
                rfq_date, response_deadline, expected_delivery_date, rfq_status,
                total_estimated_value, currency_code, created_at
            ) VALUES (%(rfq_id)s, %(rfq_number)s, %(rfq_title)s, %(rfq_type)s, %(requested_by)s,
                %(department_id)s, %(rfq_date)s, %(response_deadline)s, %(expected_delivery_date)s,
                %(rfq_status)s, %(total_estimated_value)s, %(currency_code)s, %(created_at)s)
            ON CONFLICT (rfq_number) DO NOTHING"""
            logger.info(f"Inserting {len(rfq_headers):,} RFQ headers...")
            insert_batch_parallel(cursor, insert_sql, rfq_headers, "rfq_headers", BATCH_SIZE, pg_connection)
        
        # Insert invoices
        if invoices:
            insert_sql = """INSERT INTO supplier_invoices (
                invoice_id, invoice_number, supplier_invoice_number, supplier_id, invoice_date,
                due_date, subtotal, tax_amount, total_amount, currency_code, invoice_status,
                payment_status, paid_date, created_at
            ) VALUES (%(invoice_id)s, %(invoice_number)s, %(supplier_invoice_number)s, %(supplier_id)s,
                %(invoice_date)s, %(due_date)s, %(subtotal)s, %(tax_amount)s, %(total_amount)s,
                %(currency_code)s, %(invoice_status)s, %(payment_status)s, %(paid_date)s, %(created_at)s)
            ON CONFLICT (invoice_id) DO NOTHING"""
            logger.info(f"Inserting {len(invoices):,} supplier invoices...")
            insert_batch_parallel(cursor, insert_sql, invoices, "supplier_invoices", BATCH_SIZE, pg_connection)
        
        # Insert audits
        if audits:
            insert_sql = """INSERT INTO supplier_audits (
                audit_id, audit_number, supplier_id, audit_type, actual_date, lead_auditor,
                audit_status, audit_score, audit_rating, followup_date, created_at
            ) VALUES (%(audit_id)s, %(audit_number)s, %(supplier_id)s, %(audit_type)s,
                %(actual_date)s, %(lead_auditor)s, %(audit_status)s, %(audit_score)s,
                %(audit_rating)s, %(followup_date)s, %(created_at)s)
            ON CONFLICT (audit_number) DO NOTHING"""
            logger.info(f"Inserting {len(audits):,} supplier audits...")
            insert_batch_parallel(cursor, insert_sql, audits, "supplier_audits", BATCH_SIZE, pg_connection)
        
        # Insert performance metrics
        if performance_metrics:
            insert_sql = """INSERT INTO supplier_performance_metrics (
                metric_id, supplier_id, metric_period, total_pos_issued, pos_delivered_ontime,
                ontime_delivery_pct, average_lead_time_days, quality_acceptance_pct, defect_ppm,
                rfqs_sent, rfqs_responded, response_rate_pct, total_spend, invoice_accuracy_pct,
                overall_score, performance_rating, created_at
            ) VALUES (%(metric_id)s, %(supplier_id)s, %(metric_period)s, %(total_pos_issued)s,
                %(pos_delivered_ontime)s, %(ontime_delivery_pct)s, %(average_lead_time_days)s,
                %(quality_acceptance_pct)s, %(defect_ppm)s, %(rfqs_sent)s, %(rfqs_responded)s,
                %(response_rate_pct)s, %(total_spend)s, %(invoice_accuracy_pct)s, %(overall_score)s,
                %(performance_rating)s, %(created_at)s)
            ON CONFLICT (supplier_id, metric_period) DO NOTHING"""
            logger.info(f"Inserting {len(performance_metrics):,} performance metrics...")
            insert_batch_parallel(cursor, insert_sql, performance_metrics, "supplier_performance_metrics", BATCH_SIZE, pg_connection)
        
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
    
    tables_list = ['purchase_requisitions', 'rfq_headers', 'supplier_invoices', 'supplier_audits', 'supplier_performance_metrics']
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
