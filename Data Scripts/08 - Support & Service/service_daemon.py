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
TOTAL_RECORDS = 14400  # 30 days of 8 hourly service records

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

def load_master_data():
    global master_data
    try:
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
        
        # Load accounts (from service related data)
        cursor.execute("SELECT DISTINCT account_id FROM service_tickets LIMIT 50")
        accounts = [row[0] for row in cursor.fetchall()]
        
        # Load contacts
        cursor.execute("SELECT DISTINCT contact_id FROM service_tickets WHERE contact_id IS NOT NULL LIMIT 50")
        contacts = [row[0] for row in cursor.fetchall()]
        
        cursor.close()
        conn.close()
        
        master_data['service_agents'] = service_agents or ['SA-000001', 'SA-000002']
        master_data['service_teams'] = service_teams or ['ST-000001']
        master_data['service_queues'] = service_queues or ['SQ-000001']
        master_data['accounts'] = accounts or ['ACC-000001']
        master_data['contacts'] = contacts or ['CONT-000001']
        
        logger.info(f"Master data loaded: {len(service_agents)} agents, {len(service_teams)} teams, {len(accounts)} accounts, {len(contacts)} contacts")
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
    
    sim_base_time = datetime.strptime(datetime.now().strftime('%Y-%m-%d 00:00:00'), '%Y-%m-%d %H:%M:%S')
    run_timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    
    # Generate service records (multiple per hour)
    for i in range(TOTAL_RECORDS):
        timestamp_offset = i * 300  # 5 minute intervals
        current_ts = sim_base_time + timedelta(seconds=timestamp_offset)
        
        account = random.choice(master_data['accounts'])
        contact = random.choice(master_data['contacts']) if master_data['contacts'] else None
        agent = random.choice(master_data['service_agents'])
        team = random.choice(master_data['service_teams'])
        queue = random.choice(master_data['service_queues'])
        
        # Service Tickets (1 per 50 records)
        if i % 50 == 0:
            ticket_id = f"TICKET-{(counters['ticket'] + i // 50):06d}"
            ticket_num = f"TKT-{run_timestamp}-{i // 50:04d}"
            tickets.append({
                'ticket_id': ticket_id,
                'ticket_number': ticket_num,
                'account_id': account,
                'contact_id': contact,
                'channel': random.choice(['Phone', 'Email', 'Chat', 'Portal', 'Social']),
                'ticket_type': random.choice(['Incident', 'Service Request', 'Question']),
                'category': random.choice(['Technical', 'Billing', 'General', 'Sales']),
                'priority': random.choice(['Low', 'Medium', 'High', 'Critical']),
                'ticket_status': random.choice(['New', 'Open', 'In Progress', 'Waiting', 'Resolved', 'Closed']),
                'subject': f"Service Issue {i // 50}",
                'description': f"Customer reported issue {i // 50}",
                'assigned_to': agent,
                'assigned_team': team,
                'created_at': current_ts,
                'updated_at': current_ts
            })
        
        # Ticket Comments (2 per ticket = 1 per 25 records)
        if i % 25 == 0:
            comment_id = f"COMMENT-{(counters['comment'] + i // 25):06d}"
            comments.append({
                'comment_id': comment_id,
                'ticket_id': tickets[-1]['ticket_id'] if tickets else f"TICKET-000001",
                'comment_text': f"Comment on ticket issue {i // 25}",
                'comment_type': random.choice(['Customer', 'Internal', 'System']),
                'is_public': random.choice([True, False]),
                'created_by': agent,
                'created_at': current_ts
            })
        
        # Ticket Escalations (1 per 200 records)
        if i % 200 == 0:
            esc_id = f"ESC-{(counters['escalation'] + i // 200):06d}"
            escalations.append({
                'escalation_id': esc_id,
                'ticket_id': tickets[-1]['ticket_id'] if tickets else f"TICKET-000001",
                'escalation_level': random.randint(1, 3),
                'escalation_reason': random.choice(['Complex Issue', 'SLA Risk', 'High Priority', 'Manager Request']),
                'escalated_from': agent,
                'escalated_to': random.choice(master_data['service_agents']),
                'escalated_at': current_ts
            })
        
        # RMA Requests (1 per 150 records)
        if i % 150 == 0:
            rma_id = f"RMA-{(counters['rma'] + i // 150):06d}"
            rma_num = f"RMA-{run_timestamp}-{i // 150:04d}"
            rma_requests.append({
                'rma_id': rma_id,
                'rma_number': rma_num,
                'account_id': account,
                'contact_id': contact,
                'ticket_id': tickets[-1]['ticket_id'] if tickets else None,
                'rma_type': random.choice(['Return', 'Repair', 'Replacement', 'Refund']),
                'return_reason': random.choice(['Defective', 'Not as expected', 'Damaged', 'Wrong item']),
                'rma_status': random.choice(['Pending', 'Approved', 'Rejected', 'Completed']),
                'approved': random.choice([True, False]),
                'approved_by': agent if random.random() > 0.3 else None,
                'approved_date': (current_ts + timedelta(days=1)).date() if random.random() > 0.3 else None,
                'created_at': current_ts
            })
        
        # Warranty Claims (1 per 250 records)
        if i % 250 == 0:
            warranty_id = f"WC-{(counters['warranty'] + i // 250):06d}"
            claim_num = f"CLM-{run_timestamp}-{i // 250:04d}"
            warranty_claims.append({
                'claim_id': warranty_id,
                'claim_number': claim_num,
                'warranty_id': f"WAR-{random.randint(1000, 9999)}",
                'ticket_id': tickets[-1]['ticket_id'] if tickets else None,
                'claim_date': current_ts.date(),
                'issue_description': f"Warranty claim for product failure {i // 250}",
                'failure_type': random.choice(['Hardware', 'Software', 'Performance', 'Defect']),
                'claim_status': random.choice(['Pending', 'Approved', 'Rejected', 'Paid']),
                'approved': random.choice([True, False]),
                'approved_by': agent if random.random() > 0.4 else None,
                'approved_date': (current_ts + timedelta(days=3)).date() if random.random() > 0.4 else None,
                'created_at': current_ts
            })
        
        # Service Metrics (1 per 100 records)
        if i % 100 == 0:
            metric_id = f"METRIC-{(counters['service_metric'] + i // 100):06d}"
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
        
        if (i + 1) % 1000 == 0:
            logger.info(f"  Generated {i + 1:,} / {TOTAL_RECORDS:,} records")
    
    logger.info(f"✓ Generated {len(tickets):,} service tickets")
    logger.info(f"✓ Generated {len(comments):,} ticket comments")
    logger.info(f"✓ Generated {len(escalations):,} escalations")
    logger.info(f"✓ Generated {len(rma_requests):,} RMA requests")
    logger.info(f"✓ Generated {len(warranty_claims):,} warranty claims")
    logger.info(f"✓ Generated {len(metrics):,} service metrics")
    
    # Bulk dump to PostgreSQL
    logger.info("="*80)
    logger.info("BULK DUMPING TO POSTGRESQL...")
    logger.info("="*80)
    
    try:
        cursor = pg_connection.cursor()
        cursor.execute("SET CONSTRAINTS ALL DEFERRED;")
        
        # Insert tickets
        if tickets:
            insert_sql = """INSERT INTO service_tickets (
                ticket_id, ticket_number, account_id, contact_id, channel, ticket_type,
                category, priority, ticket_status, subject, description, assigned_to, assigned_team,
                created_at, updated_at
            ) VALUES (%(ticket_id)s, %(ticket_number)s, %(account_id)s, %(contact_id)s,
                %(channel)s, %(ticket_type)s, %(category)s, %(priority)s, %(ticket_status)s,
                %(subject)s, %(description)s, %(assigned_to)s, %(assigned_team)s,
                %(created_at)s, %(updated_at)s)
            ON CONFLICT (ticket_number) DO NOTHING"""
            logger.info(f"Inserting {len(tickets):,} service tickets...")
            insert_batch_parallel(cursor, insert_sql, tickets, "service_tickets", BATCH_SIZE, pg_connection)
        
        # Insert comments
        if comments:
            insert_sql = """INSERT INTO ticket_comments (
                comment_id, ticket_id, comment_text, comment_type, is_public,
                created_by, created_at
            ) VALUES (%(comment_id)s, %(ticket_id)s, %(comment_text)s, %(comment_type)s,
                %(is_public)s, %(created_by)s, %(created_at)s)
            ON CONFLICT (comment_id) DO NOTHING"""
            logger.info(f"Inserting {len(comments):,} ticket comments...")
            insert_batch_parallel(cursor, insert_sql, comments, "ticket_comments", BATCH_SIZE, pg_connection)
        
        # Insert escalations
        if escalations:
            insert_sql = """INSERT INTO ticket_escalations (
                escalation_id, ticket_id, escalation_level, escalation_reason,
                escalated_from, escalated_to, escalated_at
            ) VALUES (%(escalation_id)s, %(ticket_id)s, %(escalation_level)s,
                %(escalation_reason)s, %(escalated_from)s, %(escalated_to)s, %(escalated_at)s)
            ON CONFLICT (escalation_id) DO NOTHING"""
            logger.info(f"Inserting {len(escalations):,} escalations...")
            insert_batch_parallel(cursor, insert_sql, escalations, "ticket_escalations", BATCH_SIZE, pg_connection)
        
        # Insert RMA requests
        if rma_requests:
            insert_sql = """INSERT INTO rma_requests (
                rma_id, rma_number, account_id, contact_id, ticket_id, rma_type,
                return_reason, rma_status, approved, approved_by, approved_date, created_at
            ) VALUES (%(rma_id)s, %(rma_number)s, %(account_id)s, %(contact_id)s,
                %(ticket_id)s, %(rma_type)s, %(return_reason)s, %(rma_status)s,
                %(approved)s, %(approved_by)s, %(approved_date)s, %(created_at)s)
            ON CONFLICT (rma_number) DO NOTHING"""
            logger.info(f"Inserting {len(rma_requests):,} RMA requests...")
            insert_batch_parallel(cursor, insert_sql, rma_requests, "rma_requests", BATCH_SIZE, pg_connection)
        
        # Insert warranty claims
        if warranty_claims:
            insert_sql = """INSERT INTO warranty_claims (
                claim_id, claim_number, warranty_id, ticket_id, claim_date,
                issue_description, failure_type, claim_status, approved, approved_by,
                approved_date, created_at
            ) VALUES (%(claim_id)s, %(claim_number)s, %(warranty_id)s, %(ticket_id)s,
                %(claim_date)s, %(issue_description)s, %(failure_type)s, %(claim_status)s,
                %(approved)s, %(approved_by)s, %(approved_date)s, %(created_at)s)
            ON CONFLICT (claim_number) DO NOTHING"""
            logger.info(f"Inserting {len(warranty_claims):,} warranty claims...")
            insert_batch_parallel(cursor, insert_sql, warranty_claims, "warranty_claims", BATCH_SIZE, pg_connection)
        
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
                %(chat_tickets)s, %(portal_tickets)s, %(critical_tickets)s, %(high_tickets)s, %(medium_tickets)s, %(low_tickets)s, %(created_at)s)
            ON CONFLICT DO NOTHING"""
            logger.info(f"Inserting {len(metrics):,} service metrics...")
            insert_batch_parallel(cursor, insert_sql, metrics, "service_metrics_daily", BATCH_SIZE, pg_connection)
        
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
