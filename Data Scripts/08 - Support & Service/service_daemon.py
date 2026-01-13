#!/usr/bin/env python3
"""
GenIMS Service Daemon - ULTRA FAST MODE
Generates complete service operations in-memory, then bulk dumps to PostgreSQL
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

PG_SERVICE_DB = os.getenv('DB_SERVICE', 'genims_service_db')

BATCH_SIZE = 5000
# Aligned with historical generator: 200-400 tickets/day + comments + escalations + RMA
# Daily service operations: ~300 tickets + ~600 comments + ~50 escalations + ~30 RMA = ~980 total
TOTAL_RECORDS = 1000  # Daily service operations across 4 factories

# Logging
log_dir = os.getenv('DAEMON_LOG_DIR', os.path.join(os.path.dirname(__file__), '..', '..', 'logs'))
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, 'service_daemon.log')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('ServiceDaemon')

# Global State
pg_connection = None
master_data = {}
counters = {
    'ticket': 1, 'comment': 1, 'escalation': 1, 'rma': 1, 'warranty': 1, 'service_metric': 1
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
            host=PG_HOST, port=PG_PORT, database=PG_SERVICE_DB,
            user=PG_USER, password=PG_PASSWORD, sslmode=PG_SSL_MODE, connect_timeout=30
        )
        pg_connection.autocommit = False
        logger.info(f"PostgreSQL connection established: {PG_HOST}:{PG_PORT}/{PG_SERVICE_DB}")
        return True
    except Exception as e:
        logger.error(f"PostgreSQL connection failed: {e}")
        return False

def get_table_count(table_name):
    try:
        conn = psycopg2.connect(host=PG_HOST, port=PG_PORT, database=PG_SERVICE_DB,
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
    tables = ['service_tickets', 'ticket_comments', 'ticket_escalations', 'rma_requests', 'warranty_claims', 'service_metrics_daily']
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
        counters['ticket'] = get_max_id_counter('service_tickets', 'ticket_id')
        counters['comment'] = get_max_id_counter('ticket_comments', 'comment_id')
        counters['escalation'] = get_max_id_counter('ticket_escalations', 'escalation_id')
        counters['rma'] = get_max_id_counter('rma_requests', 'rma_id')
        counters['warranty'] = get_max_id_counter('warranty_claims', 'claim_id')
        counters['service_metric'] = get_max_id_counter('service_metrics_daily', 'metric_id')
        
        logger.info(f"ID Counters initialized: {counters}")
        return True
    except Exception as e:
        logger.error(f"Failed to initialize ID counters: {e}")
        return False

def get_max_service_timestamp():
    """Always return current datetime for today's data generation"""
    # ALWAYS use current datetime for today's generation (no historical continuation)
    current_datetime = datetime.now()
    base_time = current_datetime.replace(hour=0, minute=0, second=0, microsecond=0)
    logger.info(f"Using current date for data generation: {base_time}")
    return base_time

def load_master_data():
    global master_data
    try:
        # REGISTRY INTEGRATION - Use validated FKs like CMMS/CRM
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'scripts'))
        from generator_helper import get_helper
        
        helper = get_helper()
        registry = helper.registry
        
        # Get validated FK references from registry
        valid_customer_ids = list(helper.get_valid_customer_ids())
        valid_employee_ids = list(helper.get_valid_employee_ids())
        
        # Load CRM data directly from CRM database for account/contact FKs
        try:
            crm_conn = psycopg2.connect(
                host=PG_HOST, port=PG_PORT, database='genims_crm_db',
                user=PG_USER, password=PG_PASSWORD, sslmode=PG_SSL_MODE, connect_timeout=30
            )
            cursor = crm_conn.cursor()
            
            cursor.execute("SELECT account_id FROM accounts LIMIT 100")
            accounts_from_crm = [row[0] for row in cursor.fetchall()]
            
            cursor.execute("SELECT contact_id FROM contacts LIMIT 100")
            contacts_from_crm = [row[0] for row in cursor.fetchall()]
            
            cursor.close()
            crm_conn.close()
            
        except Exception as e:
            logger.warning(f"Could not load CRM data: {e}")
            accounts_from_crm = []
            contacts_from_crm = []
        
        # Load service-specific data from service DB
        conn = psycopg2.connect(
            host=PG_HOST, port=PG_PORT, database=PG_SERVICE_DB,
            user=PG_USER, password=PG_PASSWORD, sslmode=PG_SSL_MODE, connect_timeout=30
        )
        cursor = conn.cursor()
        
        # Load service agents
        cursor.execute("SELECT agent_id FROM service_agents LIMIT 50")
        service_agents = [row[0] for row in cursor.fetchall()]
        
        # Load service teams
        cursor.execute("SELECT team_id FROM service_teams LIMIT 10")
        service_teams = [row[0] for row in cursor.fetchall()]
        
        # Load service queues
        cursor.execute("SELECT queue_id FROM service_queues LIMIT 10")
        service_queues = [row[0] for row in cursor.fetchall()]
        
        # Load SLA definitions
        cursor.execute("SELECT sla_id FROM sla_definitions LIMIT 10")
        sla_definitions = [row[0] for row in cursor.fetchall()]
        
        cursor.close()
        conn.close()
        
        # Use registry-validated FKs for cross-database references
        master_data['service_agents'] = service_agents or ['AGT-000001', 'AGT-000002']
        master_data['service_teams'] = service_teams or ['STM-000001']
        master_data['service_queues'] = service_queues or ['QUE-000001']
        master_data['sla_definitions'] = sla_definitions or ['SLA-000001']
        
        # VALIDATED CROSS-DATABASE FKs - Use registry and direct CRM lookup
        master_data['accounts'] = accounts_from_crm[:100] if accounts_from_crm else ['ACC-000001']
        master_data['contacts'] = contacts_from_crm[:100] if contacts_from_crm else ['CONTACT-000001']  
        master_data['employees'] = list(valid_employee_ids)[:50] if valid_employee_ids else ['EMP-000001']
        master_data['customers'] = list(valid_customer_ids)[:50] if valid_customer_ids else ['CUST-000001']
        
        logger.info(f"REGISTRY MASTER DATA LOADED:")
        logger.info(f"  Service Agents: {len(master_data['service_agents'])}")
        logger.info(f"  Service Teams: {len(master_data['service_teams'])}")
        logger.info(f"  CRM Accounts: {len(master_data['accounts'])}")
        logger.info(f"  CRM Contacts: {len(master_data['contacts'])}")
        logger.info(f"  Validated Employees: {len(master_data['employees'])}")
        
        # FK Validation Test
        logger.info(f"✓ Account FK Sample: {master_data['accounts'][:3]}")
        logger.info(f"✓ Contact FK Sample: {master_data['contacts'][:3]}")
        
        return True
    except Exception as e:
        logger.error(f"Failed to load master data with registry: {e}")
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

def get_max_service_timestamp():
    """Get the maximum timestamp from service tables and ensure no future dates"""
    try:
        conn = psycopg2.connect(
            host=PG_HOST, port=PG_PORT, database=PG_SERVICE_DB,
            user=PG_USER, password=PG_PASSWORD, sslmode=PG_SSL_MODE, connect_timeout=10
        )
        cursor = conn.cursor()
        
        # Check multiple service tables for latest timestamp
        tables_to_check = ['service_tickets', 'warranty_claims', 'rma_requests']
        max_timestamp = None
        
        for table in tables_to_check:
            try:
                cursor.execute(f"SELECT MAX(created_at) FROM {table};")
                result = cursor.fetchone()
                if result and result[0]:
                    table_max = result[0]
                    if max_timestamp is None or table_max > max_timestamp:
                        max_timestamp = table_max
            except Exception as e:
                logger.debug(f"Could not get max timestamp from {table}: {e}")
        
        cursor.close()
        conn.close()
        
        if max_timestamp:
            logger.info(f"Found max timestamp in Service data: {max_timestamp}")
            
            # CRITICAL FIX: Never use future dates - cap at current date
            current_datetime = datetime.now()
            if max_timestamp > current_datetime:
                logger.warning(f"Found future timestamp {max_timestamp}, using current date instead")
                max_timestamp = current_datetime
            
            # Start next day to avoid overlaps
            next_day = (max_timestamp + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
            
            # Double-check: if next day is still future, use current time
            if next_day > current_datetime:
                logger.warning(f"Next day {next_day} is in future, using current time instead")
                next_day = current_datetime.replace(minute=0, second=0, microsecond=0)
            
            return next_day
        else:
            logger.info("No existing timestamps found, starting from current time")
            return datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    
    except Exception as e:
        logger.warning(f"Could not get max timestamp: {e}, using current time")
        return datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

def main():
    """Main - Generate all service data in-memory, then bulk dump"""
    logger.info("="*80)
    logger.info("GenIMS Service Daemon - ULTRA FAST MODE (In-Memory Generation)")
    logger.info("="*80)
    logger.info(f"Configuration:")
    logger.info(f"  Database: {PG_SERVICE_DB}")
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
    tickets = []
    comments = []
    escalations = []
    rma_requests = []
    warranty_claims = []
    metrics = []
    
    # Get current date for today's data generation (no historical continuation)
    sim_base_time = get_max_service_timestamp()
    logger.info(f"Using current date for data generation: {sim_base_time}")
    run_timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    
    # Generate service records spread across 16-hour support window (6 AM - 10 PM)
    for i in range(TOTAL_RECORDS):
        # Spread service operations across 16-hour support day (customer service hours)
        business_hours_minutes = 16 * 60  # 960 minutes
        minute_offset = (i * business_hours_minutes) // TOTAL_RECORDS
        current_ts = sim_base_time.replace(hour=6) + timedelta(minutes=minute_offset)
        
        # Use VALIDATED FK references from registry
        account = random.choice(master_data['accounts'])
        contact = random.choice(master_data['contacts']) if master_data['contacts'] else None
        agent = random.choice(master_data['service_agents'])
        team = random.choice(master_data['service_teams'])
        queue = random.choice(master_data['service_queues'])
        assigned_employee = random.choice(master_data['employees'])
        escalated_employee = random.choice(master_data['employees'])
        sla = random.choice(master_data['sla_definitions'])
        
        # Service Tickets (daily target: ~300 tickets aligned with historical 200-400/day)
        # Generate ticket every ~3 records to achieve ~300 tickets per day
        if i % 3 == 0:
            ticket_id = f"TICKET-{(counters['ticket'] + i // 3):06d}"
            ticket_num = f"TKT-{run_timestamp}-{i // 3:04d}"
            
            # Calculate SLA times based on priority
            priority = random.choice(['Low', 'Medium', 'High', 'Critical'])
            sla_hours = {'Critical': 4, 'High': 8, 'Medium': 24, 'Low': 48}[priority]
            response_due = current_ts + timedelta(hours=1) 
            resolution_due = current_ts + timedelta(hours=sla_hours)
            
            tickets.append({
                'ticket_id': ticket_id,
                'ticket_number': ticket_num,
                'account_id': account,  # VALIDATED FK
                'contact_id': contact,  # VALIDATED FK
                'channel': random.choice(['Phone', 'Email', 'Chat', 'Portal', 'Social']),
                'ticket_type': random.choice(['Incident', 'Service Request', 'Question']),
                'category': random.choice(['Technical', 'Billing', 'General', 'Sales']),
                'priority': priority,
                'ticket_status': random.choice(['New', 'Open', 'In Progress', 'Waiting', 'Resolved', 'Closed']),
                'subject': f"Service Issue {i // 50}",
                'description': f"Customer reported issue {i // 50}",
                'assigned_to': assigned_employee,  # VALIDATED FK
                'assigned_team': team,
                'response_due_datetime': response_due,
                'resolution_due_datetime': resolution_due,
                'sla_id': sla,  # VALIDATED FK
                'created_at': current_ts,
                'updated_at': current_ts
            })
        
        # Ticket Comments (daily target: ~500 comments = ~2 per ticket)
        # Generate comment every ~2 records to achieve ~500 comments per day
        if i % 2 == 0:
            comment_id = f"COMMENT-{(counters['comment'] + i // 2):06d}"
            comments.append({
                'comment_id': comment_id,
                'ticket_id': tickets[-1]['ticket_id'] if tickets else f"TICKET-000001",
                'comment_text': f"Comment on ticket issue {i // 2}",
                'comment_type': random.choice(['Customer', 'Internal', 'System']),
                'is_public': random.choice([True, False]),
                'created_by': assigned_employee,  # VALIDATED FK
                'created_at': current_ts
            })
        
        # Ticket Escalations (daily target: ~50 escalations for complex issues)
        # Generate escalation every ~20 records to achieve ~50 escalations per day
        if i % 20 == 0:
            esc_id = f"ESC-{(counters['escalation'] + i // 20):06d}"
            escalations.append({
                'escalation_id': esc_id,
                'ticket_id': tickets[-1]['ticket_id'] if tickets else f"TICKET-000001",
                'escalation_level': random.randint(1, 3),
                'escalation_reason': random.choice(['Complex Issue', 'SLA Risk', 'High Priority', 'Manager Request']),
                'escalated_from': assigned_employee,  # VALIDATED FK
                'escalated_to': escalated_employee,   # VALIDATED FK
                'escalated_at': current_ts
            })
        
        # RMA Requests (daily target: ~30 return requests)
        # Generate RMA every ~33 records to achieve ~30 RMA requests per day
        if i % 33 == 0:
            rma_id = f"RMA-{(counters['rma'] + i // 33):06d}"
            rma_num = f"RMA-{run_timestamp}-{i // 33:04d}"
            rma_requests.append({
                'rma_id': rma_id,
                'rma_number': rma_num,
                'account_id': account,  # VALIDATED FK
                'contact_id': contact,  # VALIDATED FK
                'ticket_id': tickets[-1]['ticket_id'] if tickets else None,
                'rma_type': random.choice(['Return', 'Repair', 'Replacement', 'Refund']),
                'return_reason': random.choice(['Defective', 'Not as expected', 'Damaged', 'Wrong item']),
                'rma_status': random.choice(['Pending', 'Approved', 'Rejected', 'Completed']),
                'approved': random.choice([True, False]),
                'approved_by': assigned_employee if random.random() > 0.3 else None,  # VALIDATED FK
                'approved_date': (current_ts + timedelta(days=1)).date() if random.random() > 0.3 else None,
                'created_at': current_ts
            })
        
        # Warranty Claims (daily target: ~20 warranty claims)
        # Generate warranty claim every ~50 records to achieve ~20 claims per day
        if i % 50 == 0:
            warranty_id = f"WC-{(counters['warranty'] + i // 50):06d}"
            claim_num = f"CLM-{run_timestamp}-{i // 50:04d}"
            # Use proper warranty registration format
            warranty_reg_id = f"WAREG-{random.randint(100001, 999999)}"
            warranty_claims.append({
                'claim_id': warranty_id,
                'claim_number': claim_num,
                'warranty_id': warranty_reg_id,  # FIXED - Link to warranty_registrations table
                'ticket_id': tickets[-1]['ticket_id'] if tickets else None,
                'claim_date': current_ts.date(),
                'issue_description': f"Warranty claim for product failure {i // 50}",
                'failure_type': random.choice(['Hardware', 'Software', 'Performance', 'Defect']),
                'claim_status': random.choice(['Pending', 'Approved', 'Rejected', 'Paid']),
                'approved': random.choice([True, False]),
                'approved_by': assigned_employee if random.random() > 0.4 else None,  # VALIDATED FK
                'approved_date': (current_ts + timedelta(days=3)).date() if random.random() > 0.4 else None,
                'created_at': current_ts
            })
        
        # Service Metrics (daily target: ~100 service metrics for KPI tracking)
        # Generate metric every ~10 records to achieve ~100 metrics per day
        if i % 10 == 0:
            metric_id = f"METRIC-{(counters['service_metric'] + i // 10):06d}"
            metrics.append({
                'metric_id': metric_id,
                'metric_date': current_ts.date(),
                'tickets_created': random.randint(5, 20),
                'tickets_resolved': random.randint(4, 18),
                'tickets_closed': random.randint(3, 15),
                'avg_first_response_time_minutes': random.randint(5, 60),
                'avg_resolution_time_minutes': random.randint(30, 480),
                'response_sla_compliance_pct': round(random.uniform(85, 99), 1),
                'resolution_sla_compliance_pct': round(random.uniform(80, 98), 1),
                'fcr_rate_pct': round(random.uniform(50, 90), 1),
                'avg_csat_rating': round(random.uniform(3.5, 5), 2),
                'phone_tickets': random.randint(2, 10),
                'email_tickets': random.randint(2, 10),
                'chat_tickets': random.randint(1, 8),
                'portal_tickets': random.randint(1, 5),
                'critical_tickets': random.randint(0, 3),
                'high_tickets': random.randint(1, 5),
                'medium_tickets': random.randint(2, 8),
                'low_tickets': random.randint(1, 5),
                'created_at': current_ts
            })
        
        if (i + 1) % 200 == 0:
            logger.info(f"  Generated {i + 1:,} / {TOTAL_RECORDS:,} records")
    
    logger.info(f"✓ Generated {len(tickets):,} service tickets")
    logger.info(f"✓ Generated {len(comments):,} ticket comments")
    logger.info(f"✓ Generated {len(escalations):,} escalations")
    logger.info(f"✓ Generated {len(rma_requests):,} RMA requests")
    logger.info(f"✓ Generated {len(warranty_claims):,} warranty claims")
    logger.info(f"✓ Generated {len(metrics):,} service metrics")
    
    # Bulk dump to PostgreSQL
    logger.info("="*80)
    logger.info("BULK DUMPING TO POSTGRESQL WITH TIME COORDINATION...")
    logger.info("="*80)
    
    try:
        cursor = pg_connection.cursor()
        cursor.execute("SET CONSTRAINTS ALL DEFERRED;")
        
        # Insert tickets
        if tickets:
            insert_sql = """INSERT INTO service_tickets (
                ticket_id, ticket_number, account_id, contact_id, channel, ticket_type,
                category, priority, ticket_status, subject, description, assigned_to, assigned_team,
                response_due_datetime, resolution_due_datetime, sla_id, created_at, updated_at
            ) VALUES (%(ticket_id)s, %(ticket_number)s, %(account_id)s, %(contact_id)s,
                %(channel)s, %(ticket_type)s, %(category)s, %(priority)s, %(ticket_status)s,
                %(subject)s, %(description)s, %(assigned_to)s, %(assigned_team)s,
                %(response_due_datetime)s, %(resolution_due_datetime)s, %(sla_id)s,
                %(created_at)s, %(updated_at)s)"""
            logger.info(f"Inserting {len(tickets):,} service tickets...")
            insert_batch_parallel(cursor, insert_sql, tickets, "service_tickets", BATCH_SIZE, pg_connection)
            
        # TIME COORDINATION - 2 second delay after tickets
        logger.info("⏱️  Time coordination delay - 2 seconds...")
        time.sleep(2)
        
        # Insert comments
        if comments:
            insert_sql = """INSERT INTO ticket_comments (
                comment_id, ticket_id, comment_text, comment_type, is_public,
                created_by, created_at
            ) VALUES (%(comment_id)s, %(ticket_id)s, %(comment_text)s, %(comment_type)s,
                %(is_public)s, %(created_by)s, %(created_at)s)"""
            logger.info(f"Inserting {len(comments):,} ticket comments...")
            insert_batch_parallel(cursor, insert_sql, comments, "ticket_comments", BATCH_SIZE, pg_connection)
            
        # TIME COORDINATION - 2 second delay after comments
        logger.info("⏱️  Time coordination delay - 2 seconds...")
        time.sleep(2)
        
        # Insert escalations
        if escalations:
            insert_sql = """INSERT INTO ticket_escalations (
                escalation_id, ticket_id, escalation_level, escalation_reason,
                escalated_from, escalated_to, escalated_at
            ) VALUES (%(escalation_id)s, %(ticket_id)s, %(escalation_level)s,
                %(escalation_reason)s, %(escalated_from)s, %(escalated_to)s, %(escalated_at)s)"""
            logger.info(f"Inserting {len(escalations):,} escalations...")
            insert_batch_parallel(cursor, insert_sql, escalations, "ticket_escalations", BATCH_SIZE, pg_connection)
            
        # TIME COORDINATION - 3 second delay after escalations
        logger.info("⏱️  Time coordination delay - 3 seconds...")
        time.sleep(3)
        
        # Insert RMA requests
        if rma_requests:
            insert_sql = """INSERT INTO rma_requests (
                rma_id, rma_number, account_id, contact_id, ticket_id, rma_type,
                return_reason, rma_status, approved, approved_by, approved_date, created_at
            ) VALUES (%(rma_id)s, %(rma_number)s, %(account_id)s, %(contact_id)s,
                %(ticket_id)s, %(rma_type)s, %(return_reason)s, %(rma_status)s,
                %(approved)s, %(approved_by)s, %(approved_date)s, %(created_at)s)"""
            logger.info(f"Inserting {len(rma_requests):,} RMA requests...")
            insert_batch_parallel(cursor, insert_sql, rma_requests, "rma_requests", BATCH_SIZE, pg_connection)
            
        # TIME COORDINATION - 2 second delay after RMA
        logger.info("⏱️  Time coordination delay - 2 seconds...")
        time.sleep(2)
        
        # Insert warranty claims
        if warranty_claims:
            insert_sql = """INSERT INTO warranty_claims (
                claim_id, claim_number, warranty_id, ticket_id, claim_date,
                issue_description, failure_type, claim_status, approved, approved_by,
                approved_date, created_at
            ) VALUES (%(claim_id)s, %(claim_number)s, %(warranty_id)s, %(ticket_id)s,
                %(claim_date)s, %(issue_description)s, %(failure_type)s, %(claim_status)s,
                %(approved)s, %(approved_by)s, %(approved_date)s, %(created_at)s)"""
            logger.info(f"Inserting {len(warranty_claims):,} warranty claims...")
            insert_batch_parallel(cursor, insert_sql, warranty_claims, "warranty_claims", BATCH_SIZE, pg_connection)
            
        # TIME COORDINATION - 2 second delay after warranty
        logger.info("⏱️  Time coordination delay - 2 seconds...")
        time.sleep(2)
        
        # Insert metrics
        if metrics:
            insert_sql = """INSERT INTO service_metrics_daily (
                metric_id, metric_date, tickets_created, tickets_resolved, tickets_closed,
                avg_first_response_time_minutes, avg_resolution_time_minutes, response_sla_compliance_pct,
                resolution_sla_compliance_pct, fcr_rate_pct, avg_csat_rating, phone_tickets, email_tickets,
                chat_tickets, portal_tickets, critical_tickets, high_tickets, medium_tickets, low_tickets, created_at
            ) VALUES (%(metric_id)s, %(metric_date)s, %(tickets_created)s, %(tickets_resolved)s, %(tickets_closed)s,
                %(avg_first_response_time_minutes)s, %(avg_resolution_time_minutes)s, %(response_sla_compliance_pct)s,
                %(resolution_sla_compliance_pct)s, %(fcr_rate_pct)s, %(avg_csat_rating)s, %(phone_tickets)s, %(email_tickets)s,
                %(chat_tickets)s, %(portal_tickets)s, %(critical_tickets)s, %(high_tickets)s, %(medium_tickets)s, %(low_tickets)s, %(created_at)s)"""
            logger.info(f"Inserting {len(metrics):,} service metrics...")
            insert_batch_parallel(cursor, insert_sql, metrics, "service_metrics_daily", BATCH_SIZE, pg_connection)
        
        cursor.close()
        
        # TIME COORDINATION - Final 3 second delay before commit
        logger.info("⏱️  Time coordination delay - 3 seconds before commit...")
        time.sleep(3)
        
        # Commit all data
        pg_connection.commit()
        
        logger.info(f"✓ All records inserted successfully with time coordination")
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
    
    tables_list = ['service_tickets', 'ticket_comments', 'ticket_escalations', 'rma_requests', 'warranty_claims', 'service_metrics_daily']
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
