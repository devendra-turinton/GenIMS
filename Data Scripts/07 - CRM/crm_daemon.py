#!/usr/bin/env python3
"""
GenIMS CRM Daemon - ULTRA FAST MODE
Generates complete CRM operations in-memory, then bulk dumps to PostgreSQL
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

PG_CRM_DB = os.getenv('DB_CRM', 'genims_crm_db')

BATCH_SIZE = 5000
TOTAL_RECORDS = 14400  # 30 days of 8 hourly CRM records

# Logging
log_dir = os.getenv('DAEMON_LOG_DIR', os.path.join(os.path.dirname(__file__), '..', '..', 'logs'))
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, 'crm_daemon.log')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('CRMDaemon')

# Global State
pg_connection = None
master_data = {}
counters = {
    'opportunity': 1, 'activity': 1, 'task': 1, 'case': 1, 'interaction': 1
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
            host=PG_HOST, port=PG_PORT, database=PG_CRM_DB,
            user=PG_USER, password=PG_PASSWORD, sslmode=PG_SSL_MODE, connect_timeout=30
        )
        pg_connection.autocommit = False
        logger.info(f"PostgreSQL connection established: {PG_HOST}:{PG_PORT}/{PG_CRM_DB}")
        return True
    except Exception as e:
        logger.error(f"PostgreSQL connection failed: {e}")
        return False

def get_table_count(table_name):
    try:
        conn = psycopg2.connect(host=PG_HOST, port=PG_PORT, database=PG_CRM_DB,
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
    tables = ['opportunities', 'activities', 'tasks', 'cases', 'customer_interactions']
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
        counters['opportunity'] = get_max_id_counter('opportunities', 'opportunity_id')
        counters['activity'] = get_max_id_counter('activities', 'activity_id')
        counters['task'] = get_max_id_counter('tasks', 'task_id')
        counters['case'] = get_max_id_counter('cases', 'case_id')
        counters['interaction'] = get_max_id_counter('customer_interactions', 'interaction_id')
        
        logger.info(f"ID Counters initialized: {counters}")
        return True
    except Exception as e:
        logger.error(f"Failed to initialize ID counters: {e}")
        return False

def load_master_data():
    global master_data
    try:
        conn = psycopg2.connect(
            host=PG_HOST, port=PG_PORT, database=PG_CRM_DB,
            user=PG_USER, password=PG_PASSWORD, sslmode=PG_SSL_MODE, connect_timeout=30
        )
        cursor = conn.cursor()
        
        # Load accounts
        cursor.execute("SELECT account_id FROM accounts LIMIT 50")
        accounts = [row[0] for row in cursor.fetchall()]
        
        # Load contacts
        cursor.execute("SELECT contact_id FROM contacts LIMIT 100")
        contacts = [row[0] for row in cursor.fetchall()]
        
        # Load sales reps
        cursor.execute("SELECT sales_rep_id FROM sales_reps LIMIT 20")
        sales_reps = [row[0] for row in cursor.fetchall()]
        
        cursor.close()
        conn.close()
        
        master_data['accounts'] = accounts or ['ACC-000001', 'ACC-000002']
        master_data['contacts'] = contacts or ['CONT-000001', 'CONT-000002']
        master_data['sales_reps'] = sales_reps or ['SREP-000001']
        
        logger.info(f"Master data loaded: {len(accounts)} accounts, {len(contacts)} contacts, {len(sales_reps)} sales reps")
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
    """Main - Generate all CRM data in-memory, then bulk dump"""
    logger.info("="*80)
    logger.info("GenIMS CRM Daemon - ULTRA FAST MODE (In-Memory Generation)")
    logger.info("="*80)
    logger.info(f"Configuration:")
    logger.info(f"  Database: {PG_CRM_DB}")
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
    opportunities = []
    activities = []
    tasks = []
    cases = []
    interactions = []
    
    sim_base_time = datetime.strptime(datetime.now().strftime('%Y-%m-%d 00:00:00'), '%Y-%m-%d %H:%M:%S')
    run_timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    
    # Generate CRM records (multiple per hour)
    for i in range(TOTAL_RECORDS):
        timestamp_offset = i * 300  # 5 minute intervals
        current_ts = sim_base_time + timedelta(seconds=timestamp_offset)
        
        account = random.choice(master_data['accounts'])
        contact = random.choice(master_data['contacts'])
        sales_rep = random.choice(master_data['sales_reps'])
        
        # Opportunities (1 per 100 records)
        if i % 100 == 0:
            opp_id = f"OPP-{(counters['opportunity'] + i // 100):06d}"
            opportunities.append({
                'opportunity_id': opp_id,
                'opportunity_number': f"OPP-{run_timestamp}-{i // 100:04d}",
                'account_id': account,
                'opportunity_name': f"Opportunity-{i // 100}",
                'opportunity_type': random.choice(['New Business', 'Expansion', 'Renewal', 'Add-on']),
                'stage': random.choice(['Prospecting', 'Qualification', 'Proposal', 'Negotiation', 'Closed Won']),
                'close_date': (current_ts + timedelta(days=random.randint(1, 7))).date(),
                'expected_close_date': (current_ts + timedelta(days=random.randint(7, 90))).date(),
                'probability_pct': random.randint(10, 100),
                'amount': round(random.uniform(10000, 500000), 2),
                'opportunity_owner': sales_rep,
                'is_closed': random.choice([True, False]),
                'created_at': current_ts
            })
        
        # Activities (1 per 50 records)
        if i % 50 == 0:
            act_id = f"ACT-{(counters['activity'] + i // 50):06d}"
            activities.append({
                'activity_id': act_id,
                'activity_number': f"ACT-{run_timestamp}-{i // 50:04d}",
                'account_id': account,
                'contact_id': contact,
                'activity_type': random.choice(['Call', 'Meeting', 'Email', 'Task', 'Note']),
                'activity_status': random.choice(['Completed', 'Scheduled', 'Cancelled']),
                'activity_date': current_ts,
                'subject': f"Activity for {account}",
                'assigned_to': sales_rep,
                'created_at': current_ts
            })
        
        # Tasks (1 per 75 records)
        if i % 75 == 0:
            task_id = f"TASK-{(counters['task'] + i // 75):06d}"
            tasks.append({
                'task_id': task_id,
                'task_number': f"TASK-{run_timestamp}-{i // 75:04d}",
                'subject': f"Task-{i // 75}",
                'task_type': random.choice(['Follow-up', 'Proposal', 'Quote', 'Demo', 'Review']),
                'task_priority': random.choice(['Low', 'Medium', 'High']),
                'priority': random.choice(['Low', 'Medium', 'High']),
                'task_status': random.choice(['Open', 'In Progress', 'Completed']),
                'due_date': (current_ts + timedelta(days=random.randint(1, 30))).date(),
                'assigned_to': sales_rep,
                'created_at': current_ts
            })
        
        # Cases (1 per 200 records)
        if i % 200 == 0:
            case_id = f"CASE-{(counters['case'] + i // 200):06d}"
            cases.append({
                'case_id': case_id,
                'case_number': f"CASE-{run_timestamp}-{i // 200:04d}",
                'account_id': account,
                'contact_id': contact,
                'case_type': random.choice(['Bug', 'Feature Request', 'Service Issue', 'Billing']),
                'priority': random.choice(['Low', 'Medium', 'High', 'Critical']),
                'case_status': random.choice(['New', 'In Progress', 'Waiting for Customer', 'Resolved', 'Closed']),
                'subject': f"Case {i // 200}",
                'description': f"Issue reported for {account}",
                'assigned_to': sales_rep,
                'created_at': current_ts
            })
        
        # Customer Interactions (1 per 20 records)
        if i % 20 == 0:
            inter_id = f"INTER-{(counters['interaction'] + i // 20):06d}"
            interactions.append({
                'interaction_id': inter_id,
                'account_id': account,
                'contact_id': contact,
                'interaction_type': random.choice(['Phone', 'Email', 'Chat', 'In-person', 'Video']),
                'interaction_date': current_ts,
                'duration_minutes': random.randint(5, 120),
                'subject': f"Interaction {i // 20}",
                'description': f"Interaction with {contact}",
                'direction': random.choice(['Inbound', 'Outbound']),
                'created_at': current_ts
            })
        
        if (i + 1) % 1000 == 0:
            logger.info(f"  Generated {i + 1:,} / {TOTAL_RECORDS:,} records")
    
    logger.info(f"✓ Generated {len(opportunities):,} opportunities")
    logger.info(f"✓ Generated {len(activities):,} activities")
    logger.info(f"✓ Generated {len(tasks):,} tasks")
    logger.info(f"✓ Generated {len(cases):,} cases")
    logger.info(f"✓ Generated {len(interactions):,} customer interactions")
    
    # Bulk dump to PostgreSQL
    logger.info("="*80)
    logger.info("BULK DUMPING TO POSTGRESQL...")
    logger.info("="*80)
    
    try:
        cursor = pg_connection.cursor()
        cursor.execute("SET CONSTRAINTS ALL DEFERRED;")
        
        # Insert opportunities
        if opportunities:
            insert_sql = """INSERT INTO opportunities (
                opportunity_id, opportunity_number, account_id, opportunity_name,
                opportunity_type, stage, close_date, expected_close_date, probability_pct,
                amount, opportunity_owner, is_closed, created_at
            ) VALUES (%(opportunity_id)s, %(opportunity_number)s, %(account_id)s,
                %(opportunity_name)s, %(opportunity_type)s, %(stage)s,
                %(close_date)s, %(expected_close_date)s, %(probability_pct)s, %(amount)s,
                %(opportunity_owner)s, %(is_closed)s, %(created_at)s)
            ON CONFLICT (opportunity_number) DO NOTHING"""
            logger.info(f"Inserting {len(opportunities):,} opportunities...")
            insert_batch_parallel(cursor, insert_sql, opportunities, "opportunities", BATCH_SIZE, pg_connection)
        
        # Insert activities
        if activities:
            insert_sql = """INSERT INTO activities (
                activity_id, activity_number, account_id, contact_id, activity_type,
                activity_status, activity_date, subject, assigned_to, created_at
            ) VALUES (%(activity_id)s, %(activity_number)s, %(account_id)s, %(contact_id)s,
                %(activity_type)s, %(activity_status)s, %(activity_date)s,
                %(subject)s, %(assigned_to)s, %(created_at)s)
            ON CONFLICT (activity_number) DO NOTHING"""
            logger.info(f"Inserting {len(activities):,} activities...")
            insert_batch_parallel(cursor, insert_sql, activities, "activities", BATCH_SIZE, pg_connection)
        
        # Insert tasks
        if tasks:
            insert_sql = """INSERT INTO tasks (
                task_id, task_number, subject, task_type, priority,
                task_status, due_date, assigned_to, created_at
            ) VALUES (%(task_id)s, %(task_number)s, %(subject)s, %(task_type)s,
                %(priority)s, %(task_status)s, %(due_date)s,
                %(assigned_to)s, %(created_at)s)
            ON CONFLICT (task_number) DO NOTHING"""
            logger.info(f"Inserting {len(tasks):,} tasks...")
            insert_batch_parallel(cursor, insert_sql, tasks, "tasks", BATCH_SIZE, pg_connection)
        
        # Insert cases
        if cases:
            insert_sql = """INSERT INTO cases (
                case_id, case_number, account_id, contact_id, case_type, priority,
                case_status, subject, description, assigned_to, created_at
            ) VALUES (%(case_id)s, %(case_number)s, %(account_id)s, %(contact_id)s,
                %(case_type)s, %(priority)s, %(case_status)s, %(subject)s, %(description)s,
                %(assigned_to)s, %(created_at)s)
            ON CONFLICT (case_number) DO NOTHING"""
            logger.info(f"Inserting {len(cases):,} cases...")
            insert_batch_parallel(cursor, insert_sql, cases, "cases", BATCH_SIZE, pg_connection)
        
        # Insert interactions
        if interactions:
            insert_sql = """INSERT INTO customer_interactions (
                interaction_id, account_id, contact_id, interaction_type,
                interaction_date, duration_minutes, subject, description, direction, created_at
            ) VALUES (%(interaction_id)s, %(account_id)s,
                %(contact_id)s, %(interaction_type)s, %(interaction_date)s,
                %(duration_minutes)s, %(subject)s, %(description)s, %(direction)s, %(created_at)s)
            ON CONFLICT DO NOTHING"""
            logger.info(f"Inserting {len(interactions):,} customer interactions...")
            insert_batch_parallel(cursor, insert_sql, interactions, "customer interactions", BATCH_SIZE, pg_connection)
        
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
    
    tables_list = ['opportunities', 'activities', 'tasks', 'cases', 'customer_interactions']
    for table in tables_list:
        before = counts_before.get(table)
        after = counts_after.get(table)
        
        if before is not None and after is not None:
            inserted = after - before
            logger.info(f"{table:.<35} Before: {before:>10,} | After: {after:>10,} | Inserted: {inserted:>10,}")
    
    logger.info("="*80)
    
    if pg_connection:
        pg_connection.close()
    
    return 0

if __name__ == "__main__":
    os.makedirs('logs', exist_ok=True)
    sys.exit(main())
