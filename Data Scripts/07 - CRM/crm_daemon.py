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

# Add scripts to path for helper functions
script_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'scripts')
if script_dir not in sys.path:
    sys.path.insert(0, script_dir)

try:
    from generator_helper import get_helper
    HELPER_AVAILABLE = True
except ImportError:
    HELPER_AVAILABLE = False

# Simple Time Coordinator Class
class TimeCoordinator:
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
        return self.base_time

# Configuration
PG_HOST = os.getenv('POSTGRES_HOST', 'localhost')
PG_PORT = int(os.getenv('POSTGRES_PORT', '5432'))
PG_USER = os.getenv('POSTGRES_USER', 'postgres')
PG_PASSWORD = os.getenv('POSTGRES_PASSWORD', '')
PG_SSL_MODE = os.getenv('PG_SSL_MODE', 'require')

PG_CRM_DB = os.getenv('DB_CRM', 'genims_crm_db')

BATCH_SIZE = 5000
# Aligned with historical generator: 80-200 leads/day + opportunities + activities + cases
# Daily CRM operations: ~120 leads + ~30 opportunities + ~80 activities + ~40 cases = ~270 total
TOTAL_RECORDS = 400  # Daily CRM operations across 4 factories

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
        counters['lead'] = get_max_id_counter('leads', 'lead_id')
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
    """Main - Generate all CRM data in-memory, then bulk dump"""
    logger.info("="*80)
    logger.info("GenIMS CRM Daemon - ULTRA FAST MODE (In-Memory Generation)")
    logger.info("="*80)
    logger.info(f"Configuration:")
    logger.info(f"  Database: {PG_CRM_DB}")
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
        logger.warning("Helper not available, FK validation disabled")
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
    leads = []
    opportunities = []
    activities = []
    tasks = []
    cases = []
    interactions = []
    
    # Use time coordinator for synchronized timestamps
    sim_base_time = time_coord.get_current_time().replace(hour=0, minute=0, second=0, microsecond=0)
    # Use current datetime with milliseconds to ensure uniqueness across runs
    current_time = datetime.now()
    run_timestamp = current_time.strftime('%Y%m%d%H%M%S') + f"{current_time.microsecond // 1000:03d}"
    
    # Validate FK availability
    if not master_data['accounts'] or not master_data['contacts'] or not master_data['sales_reps']:
        logger.error("Critical: Missing master data for FK references")
        return 1
    
    # Get validated employee IDs for assignment
    if helper:
        try:
            valid_employee_ids = list(helper.get_valid_employee_ids())
            if not valid_employee_ids:
                logger.warning("No valid employee IDs found, using sales reps as fallback")
                valid_employee_ids = master_data['sales_reps']
        except Exception as e:
            logger.warning(f"Employee ID validation failed: {e}, using sales reps")
            valid_employee_ids = master_data['sales_reps']
    else:
        logger.info("Using sales reps for employee assignments (no helper)")
        valid_employee_ids = master_data['sales_reps']
    
    logger.info(f"FK Validation: {len(master_data['accounts'])} accounts, {len(master_data['contacts'])} contacts, {len(valid_employee_ids)} employees")
    
    # Generate CRM records spread across 10-hour business day (8 AM - 6 PM)
    for i in range(TOTAL_RECORDS):
        # Spread CRM operations across 10-hour business day
        business_hours_minutes = 10 * 60  # 600 minutes
        minute_offset = (i * business_hours_minutes) // TOTAL_RECORDS
        current_ts = sim_base_time.replace(hour=8) + timedelta(minutes=minute_offset)
        
        # Validated FK selection
        try:
            account = random.choice(master_data['accounts'])
            contact = random.choice(master_data['contacts'])
            sales_rep = random.choice(master_data['sales_reps'])
            assigned_employee = random.choice(valid_employee_ids)
        except IndexError:
            logger.error(f"FK reference error at record {i}")
            continue
        
        # Leads (daily target: ~120 leads aligned with historical 80-200/day)
        # Generate lead every ~3 records to achieve ~130 leads per day
        if i % 3 == 0:
            lead_id = f"LEAD-{counters['lead']:06d}"
            counters['lead'] += 1
            leads.append({
                'lead_id': lead_id,
                'lead_number': f"LEAD-{run_timestamp}-{i // 3:04d}",
                'contact_first_name': f"Lead{i // 3}",
                'contact_last_name': "Prospect",
                'email': f"lead{i // 3}@example.com",
                'company_name': f"Company-{i // 3}",
                'phone': f"+1-555-{random.randint(1000, 9999)}",
                'lead_source': random.choice(['website', 'trade_show', 'referral', 'cold_call', 'social_media']),
                'lead_status': random.choice(['new', 'contacted', 'qualified', 'unqualified', 'converted']),
                'industry': random.choice(['manufacturing', 'automotive', 'electronics', 'pharmaceuticals']),
                'lead_grade': random.choice(['A', 'B', 'C', 'D']),
                'assigned_to': sales_rep,
                'created_at': current_ts
            })

        # Opportunities (daily target: ~30 opportunities aligned with sales orders)
        # Generate opportunity every ~13 records to achieve ~30 opportunities per day
        if i % 13 == 0:
            opp_id = f"OPP-{(counters['opportunity'] + i // 13):06d}"
            stage = random.choice(['prospecting', 'qualification', 'proposal', 'negotiation', 'closed_won'])
            
            # Calculate probability based on stage
            stage_probability = {
                'prospecting': 10, 'qualification': 20, 'proposal': 60,
                'negotiation': 80, 'closed_won': 100
            }
            
            opportunities.append({
                'opportunity_id': opp_id,
                'opportunity_number': f"OPP-{run_timestamp}-{i // 13:04d}",
                'account_id': account,
                'opportunity_name': f"Opportunity-{i // 100}",
                'opportunity_type': random.choice(['new_business', 'expansion', 'renewal', 'upsell']),
                'stage': stage,
                'close_date': (current_ts + timedelta(days=random.randint(1, 7))).date(),
                'expected_close_date': (current_ts + timedelta(days=random.randint(7, 90))).date(),
                'probability_pct': stage_probability.get(stage, 10),
                'amount': round(random.uniform(10000, 500000), 2),
                'opportunity_owner': sales_rep,
                'is_closed': stage == 'closed_won',
                'created_at': time_coord.get_current_time()
            })
        
        # Activities (daily target: ~80 sales activities)
        # Generate activity every ~5 records to achieve ~80 activities per day
        if i % 5 == 0:
            act_id = f"ACT-{(counters['activity'] + i // 5):06d}"
            activities.append({
                'activity_id': act_id,
                'activity_number': f"ACT-{run_timestamp}-{i // 5:04d}",
                'account_id': account,
                'contact_id': contact,
                'activity_type': random.choice(['call', 'meeting', 'email', 'demo', 'site_visit']),
                'activity_status': random.choice(['completed', 'scheduled', 'cancelled']),
                'activity_date': time_coord.get_current_time(),
                'subject': f"Activity for {account}",
                'assigned_to': assigned_employee,
                'created_at': time_coord.get_current_time()
            })
        
        # Tasks (daily target: ~40 follow-up tasks)
        # Generate task every ~10 records to achieve ~40 tasks per day
        if i % 10 == 0:
            task_id = f"TASK-{(counters['task'] + i // 10):06d}"
            tasks.append({
                'task_id': task_id,
                'task_number': f"TASK-{run_timestamp}-{i // 10:04d}",
                'subject': f"Task-{i // 75}",
                'task_type': random.choice(['follow_up', 'proposal', 'quote', 'demo', 'review']),
                'priority': random.choice(['low', 'medium', 'high']),
                'task_status': random.choice(['open', 'in_progress', 'completed']),
                'due_date': (time_coord.get_current_time() + timedelta(days=random.randint(1, 30))).date(),
                'assigned_to': assigned_employee,
                'created_at': time_coord.get_current_time()
            })
        
        # Cases (daily target: ~25 customer service cases)
        # Generate case every ~16 records to achieve ~25 cases per day
        if i % 16 == 0:
            case_id = f"CASE-{(counters['case'] + i // 16):06d}"
            case_priority = random.choice(['low', 'medium', 'high', 'critical'])
            
            cases.append({
                'case_id': case_id,
                'case_number': f"CASE-{run_timestamp}-{i // 16:04d}",
                'account_id': account,
                'contact_id': contact,
                'case_type': random.choice(['question', 'problem', 'feature_request', 'complaint']),
                'priority': case_priority,
                'case_status': random.choice(['new', 'in_progress', 'pending_customer', 'resolved', 'closed']),
                'subject': f"Case {i // 200}",
                'description': f"Issue reported for {account}",
                'assigned_to': assigned_employee,
                'created_at': time_coord.get_current_time()
            })
        
        # Customer Interactions (daily target: ~50 customer touchpoints)
        # Generate interaction every ~8 records to achieve ~50 interactions per day
        if i % 8 == 0:
            inter_id = f"INTER-{(counters['interaction'] + i // 8):06d}"
            interactions.append({
                'interaction_id': inter_id,
                'account_id': account,
                'contact_id': contact,
                'interaction_type': random.choice(['phone', 'email', 'chat', 'in_person', 'video']),
                'interaction_date': time_coord.get_current_time(),
                'duration_minutes': random.randint(5, 120),
                'subject': f"Interaction {i // 20}",
                'description': f"Interaction with {contact}",
                'direction': random.choice(['inbound', 'outbound']),
                'created_at': time_coord.get_current_time()
            })
        
        if (i + 1) % 100 == 0:
            logger.info(f"  Generated {i + 1:,} / {TOTAL_RECORDS:,} records")
    
    logger.info(f"✓ Generated {len(leads):,} leads")
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
        
        # Insert leads
        if leads:
            insert_sql = """INSERT INTO leads (
                lead_id, lead_number, contact_first_name, contact_last_name, email, company_name,
                phone, lead_source, lead_status, industry, lead_grade,
                assigned_to, created_at
            ) VALUES (%(lead_id)s, %(lead_number)s, %(contact_first_name)s,
                %(contact_last_name)s, %(email)s, %(company_name)s, %(phone)s,
                %(lead_source)s, %(lead_status)s, %(industry)s,
                %(lead_grade)s, %(assigned_to)s, %(created_at)s)"""
            logger.info(f"Inserting {len(leads):,} leads...")
            insert_batch_parallel(cursor, insert_sql, leads, "leads", BATCH_SIZE, pg_connection)
        
        # Insert opportunities
        if opportunities:
            insert_sql = """INSERT INTO opportunities (
                opportunity_id, opportunity_number, account_id, opportunity_name,
                opportunity_type, stage, close_date, expected_close_date, probability_pct,
                amount, opportunity_owner, is_closed, created_at
            ) VALUES (%(opportunity_id)s, %(opportunity_number)s, %(account_id)s,
                %(opportunity_name)s, %(opportunity_type)s, %(stage)s,
                %(close_date)s, %(expected_close_date)s, %(probability_pct)s, %(amount)s,
                %(opportunity_owner)s, %(is_closed)s, %(created_at)s)"""
            logger.info(f"Inserting {len(opportunities):,} opportunities...")
            insert_batch_parallel(cursor, insert_sql, opportunities, "opportunities", BATCH_SIZE, pg_connection)
        
        # Insert activities
        if activities:
            insert_sql = """INSERT INTO activities (
                activity_id, activity_number, account_id, contact_id, activity_type,
                activity_status, activity_date, subject, assigned_to, created_at
            ) VALUES (%(activity_id)s, %(activity_number)s, %(account_id)s, %(contact_id)s,
                %(activity_type)s, %(activity_status)s, %(activity_date)s,
                %(subject)s, %(assigned_to)s, %(created_at)s)"""
            logger.info(f"Inserting {len(activities):,} activities...")
            insert_batch_parallel(cursor, insert_sql, activities, "activities", BATCH_SIZE, pg_connection)
        
        # Insert tasks
        if tasks:
            insert_sql = """INSERT INTO tasks (
                task_id, task_number, subject, task_type, priority,
                task_status, due_date, assigned_to, created_at
            ) VALUES (%(task_id)s, %(task_number)s, %(subject)s, %(task_type)s,
                %(priority)s, %(task_status)s, %(due_date)s,
                %(assigned_to)s, %(created_at)s)"""
            logger.info(f"Inserting {len(tasks):,} tasks...")
            insert_batch_parallel(cursor, insert_sql, tasks, "tasks", BATCH_SIZE, pg_connection)
        
        # Insert cases
        if cases:
            insert_sql = """INSERT INTO cases (
                case_id, case_number, account_id, contact_id, case_type, priority,
                case_status, subject, description, assigned_to, created_at
            ) VALUES (%(case_id)s, %(case_number)s, %(account_id)s, %(contact_id)s,
                %(case_type)s, %(priority)s, %(case_status)s, %(subject)s, %(description)s,
                %(assigned_to)s, %(created_at)s)"""
            logger.info(f"Inserting {len(cases):,} cases...")
            insert_batch_parallel(cursor, insert_sql, cases, "cases", BATCH_SIZE, pg_connection)
        
        # Insert interactions
        if interactions:
            insert_sql = """INSERT INTO customer_interactions (
                interaction_id, account_id, contact_id, interaction_type,
                interaction_date, duration_minutes, subject, description, direction, created_at
            ) VALUES (%(interaction_id)s, %(account_id)s,
                %(contact_id)s, %(interaction_type)s, %(interaction_date)s,
                %(duration_minutes)s, %(subject)s, %(description)s, %(direction)s, %(created_at)s)"""
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
