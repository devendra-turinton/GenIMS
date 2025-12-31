#!/usr/bin/env python3
"""
GenIMS CRM Daemon
Continuous customer relationship management operations
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
PG_DATABASE = os.getenv('DB_CRM', 'genims_crm_db')
PG_USER = os.getenv('POSTGRES_USER', 'postgres')
PG_PASSWORD = os.getenv('POSTGRES_PASSWORD', '')
PG_SSL_MODE = os.getenv('PG_SSL_MODE', 'require')

# CRM Configuration
CYCLE_INTERVAL_SECONDS = 900  # Run every 15 minutes

# Logging configuration
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
logger = logging.getLogger('Crm')



running = True
pg_connection = None
master_data = {}
stats = {
    'cycles': 0,
    'leads_scored': 0,
    'opportunities_progressed': 0,
    'quotes_generated': 0,
    'quotes_converted': 0,
    'cases_resolved': 0,
    'contracts_renewed': 0,
    'start_time': datetime.now()
}

def signal_handler(sig, frame):
    global running
    logger.info("Shutdown signal received")
    running = False

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

def initialize_database():
    global pg_connection
    if not POSTGRES_AVAILABLE:
        return False
    try:
        pg_connection = psycopg2.connect(
            host=PG_HOST, port=PG_PORT, database=PG_DATABASE,
            user=PG_USER, password=PG_PASSWORD,
            sslmode=PG_SSL_MODE
        )
        pg_connection.autocommit = False
        logger.info("PostgreSQL connected")
        return True
    except Exception as e:
        logger.error(f"DB connection failed: {e}")
        return False

def load_master_data():
    global master_data
    try:
        cursor = pg_connection.cursor()
        
        # Load sales reps
        cursor.execute("SELECT * FROM sales_reps WHERE rep_status = 'active' LIMIT 50")
        master_data['sales_reps'] = [dict(zip([d[0] for d in cursor.description], row)) 
                                     for row in cursor.fetchall()]
        
        # Load accounts
        cursor.execute("SELECT * FROM accounts WHERE is_active = true LIMIT 100")
        master_data['accounts'] = [dict(zip([d[0] for d in cursor.description], row)) 
                                   for row in cursor.fetchall()]
        
        cursor.close()
        logger.info(f"Loaded: {len(master_data.get('sales_reps', []))} sales reps, "
                   f"{len(master_data.get('accounts', []))} accounts")
        return True
    except Exception as e:
        logger.error(f"Failed to load master data: {e}")
        return False

def generate_id(prefix: str) -> str:
    return f"{prefix}-{datetime.now().strftime('%Y%m%d%H%M%S')}-{random.randint(1000, 9999)}"

# ============================================================================
# LEAD MANAGEMENT
# ============================================================================

def score_and_qualify_leads():
    """Score leads and auto-qualify high-scoring ones"""
    logger.info("Scoring and qualifying leads...")
    
    try:
        cursor = pg_connection.cursor()
        
        # Get new leads
        cursor.execute("""
            SELECT lead_id, lead_score, has_budget, is_decision_maker,
                   has_identified_need, has_timeline
            FROM leads
            WHERE lead_status = 'new'
            AND is_active = true
            LIMIT 20
        """)
        
        leads = cursor.fetchall()
        
        for lead_id, score, budget, decision_maker, need, timeline in leads:
            # Calculate score
            new_score = score + random.randint(-5, 15)
            
            # BANT scoring boost
            if budget:
                new_score += 10
            if decision_maker:
                new_score += 10
            if need:
                new_score += 10
            if timeline:
                new_score += 10
            
            new_score = min(100, max(0, new_score))
            
            # Determine status
            new_status = 'qualified' if new_score >= LEAD_SCORE_THRESHOLD else 'contacted'
            
            cursor.execute("""
                UPDATE leads
                SET lead_score = %s,
                    lead_status = %s,
                    last_contact_date = %s
                WHERE lead_id = %s
            """, (new_score, new_status, datetime.now(), lead_id))
            
            stats['leads_scored'] += 1
        
        pg_connection.commit()
        cursor.close()
        
        if leads:
            logger.info(f"Scored {len(leads)} leads")
    except Exception as e:
        logger.error(f"Error scoring leads: {e}")
        pg_connection.rollback()

def convert_qualified_leads():
    """Convert qualified leads to opportunities"""
    logger.info("Converting qualified leads...")
    
    if not master_data.get('sales_reps'):
        return
    
    try:
        cursor = pg_connection.cursor()
        
        # Get qualified leads ready for conversion
        cursor.execute("""
            SELECT l.lead_id, l.company_name, l.estimated_deal_value, l.assigned_to
            FROM leads l
            WHERE l.lead_status = 'qualified'
            AND l.converted = false
            AND l.lead_score >= %s
            LIMIT 5
        """, (LEAD_SCORE_THRESHOLD,))
        
        leads = cursor.fetchall()
        
        for lead_id, company_name, deal_value, assigned_to in leads:
            # Create account
            account_id = generate_id('ACC')
            cursor.execute("""
                INSERT INTO accounts (
                    account_id, account_number, account_name,
                    account_type, account_owner, relationship_status,
                    is_active, created_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (account_id, f"ACC-{account_id}", company_name,
                  'prospect', assigned_to, 'prospect', True, datetime.now()))
            
            # Create opportunity
            opp_id = generate_id('OPP')
            cursor.execute("""
                INSERT INTO opportunities (
                    opportunity_id, opportunity_number, opportunity_name,
                    account_id, opportunity_type, amount, stage,
                    probability_pct, close_date, opportunity_owner,
                    source_lead_id, is_active, created_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (opp_id, f"OPP-{opp_id}", f"{company_name} - New Business",
                  account_id, 'new_business', deal_value or random.randint(1000000, 10000000),
                  'prospecting', 10, (datetime.now() + timedelta(days=90)).date(),
                  assigned_to, lead_id, True, datetime.now()))
            
            # Mark lead as converted
            cursor.execute("""
                UPDATE leads
                SET converted = true,
                    converted_date = %s,
                    converted_to_account_id = %s,
                    converted_to_opportunity_id = %s
                WHERE lead_id = %s
            """, (datetime.now(), account_id, opp_id, lead_id))
            
            # Log integration
            cursor.execute("""
                INSERT INTO crm_integration_log (
                    log_id, integration_direction, document_type,
                    document_id, integration_status, log_timestamp
                ) VALUES (%s, %s, %s, %s, %s, %s)
            """, (generate_id('INTLOG'), 'CRM_TO_CRM',
                  'lead_conversion', lead_id, 'completed', datetime.now()))
        
        pg_connection.commit()
        cursor.close()
        
        if leads:
            logger.info(f"Converted {len(leads)} leads to opportunities")
    except Exception as e:
        logger.error(f"Error converting leads: {e}")
        pg_connection.rollback()

# ============================================================================
# OPPORTUNITY MANAGEMENT
# ============================================================================

def progress_opportunities():
    """Progress opportunities through pipeline stages"""
    logger.info("Progressing opportunities...")
    
    try:
        cursor = pg_connection.cursor()
        
        # Get opportunities ready to progress
        cursor.execute("""
            SELECT opportunity_id, stage, amount, probability_pct, close_date
            FROM opportunities
            WHERE is_active = true
            AND stage NOT IN ('closed_won', 'closed_lost')
            AND created_at < %s
            LIMIT 10
        """, (datetime.now() - timedelta(days=7),))
        
        opportunities = cursor.fetchall()
        columns = ['opportunity_id', 'stage', 'amount', 'probability_pct', 'close_date']
        
        for opp_row in opportunities:
            opp = dict(zip(columns, opp_row))
            
            # Random chance to progress
            if random.random() > 0.6:  # 40% chance
                old_stage = opp['stage']
                new_stage = get_next_stage(old_stage)
                
                if new_stage != old_stage:
                    new_prob = get_probability_for_stage(new_stage)
                    
                    cursor.execute("""
                        UPDATE opportunities
                        SET stage = %s,
                            probability_pct = %s,
                            updated_at = %s
                        WHERE opportunity_id = %s
                    """, (new_stage, new_prob, datetime.now(), opp['opportunity_id']))
                    
                    # Record stage history
                    cursor.execute("""
                        INSERT INTO opportunity_stage_history (
                            history_id, opportunity_id, from_stage, to_stage,
                            from_probability, to_probability, changed_at
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """, (generate_id('OPPHIST'), opp['opportunity_id'],
                          old_stage, new_stage, opp['probability_pct'], new_prob,
                          datetime.now()))
                    
                    stats['opportunities_progressed'] += 1
                    
                    # Generate quote if reached proposal stage
                    if new_stage == 'proposal':
                        generate_quotation(opp, cursor)
        
        pg_connection.commit()
        cursor.close()
        
        if opportunities:
            logger.info(f"Progressed {len(opportunities)} opportunities")
    except Exception as e:
        logger.error(f"Error progressing opportunities: {e}")
        pg_connection.rollback()

def get_next_stage(current_stage: str) -> str:
    """Get next stage in pipeline"""
    stage_flow = {
        'prospecting': 'qualification',
        'qualification': 'needs_analysis',
        'needs_analysis': 'proposal',
        'proposal': 'negotiation',
        'negotiation': random.choice(['closed_won', 'closed_lost', 'negotiation'])
    }
    return stage_flow.get(current_stage, current_stage)

def get_probability_for_stage(stage: str) -> int:
    """Get probability % for stage"""
    stage_probs = {
        'prospecting': 10,
        'qualification': 20,
        'needs_analysis': 40,
        'proposal': 60,
        'negotiation': 80,
        'closed_won': 100,
        'closed_lost': 0
    }
    return stage_probs.get(stage, 10)

# ============================================================================
# QUOTATION MANAGEMENT
# ============================================================================

def generate_quotation(opp: dict, cursor):
    """Generate quotation from opportunity"""
    try:
        quote_id = generate_id('QUOTE')
        
        cursor.execute("""
            INSERT INTO quotations (
                quotation_id, quotation_number, quotation_name,
                opportunity_id, account_id, quotation_date,
                valid_until_date, total_amount, quotation_status,
                payment_terms, created_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (quote_id, f"QUOTE-{quote_id}",
              f"Quote for {opp.get('opportunity_id')}",
              opp['opportunity_id'], None,  # Would need account_id
              datetime.now().date(),
              (datetime.now() + timedelta(days=30)).date(),
              opp.get('amount', 0), 'draft', 'NET30', datetime.now()))
        
        stats['quotes_generated'] += 1
        logger.info(f"Generated quote: {quote_id}")
    except Exception as e:
        logger.error(f"Error generating quote: {e}")

def process_quote_approvals():
    """Process quotes needing approval"""
    logger.info("Processing quote approvals...")
    
    try:
        cursor = pg_connection.cursor()
        
        # Auto-approve quotes under threshold
        cursor.execute("""
            UPDATE quotations
            SET quotation_status = 'sent',
                updated_at = %s
            WHERE quotation_status = 'draft'
            AND total_amount < 5000000
            AND quotation_date >= %s
            LIMIT 10
        """, (datetime.now(), (datetime.now() - timedelta(days=7)).date()))
        
        pg_connection.commit()
        cursor.close()
    except Exception as e:
        logger.error(f"Error processing quotes: {e}")
        pg_connection.rollback()

def check_quote_expiry():
    """Check for expired quotes"""
    logger.info("Checking quote expiry...")
    
    try:
        cursor = pg_connection.cursor()
        
        cursor.execute("""
            UPDATE quotations
            SET quotation_status = 'expired'
            WHERE quotation_status IN ('sent', 'under_review')
            AND valid_until_date < %s
        """, (datetime.now().date(),))
        
        pg_connection.commit()
        cursor.close()
    except Exception as e:
        logger.error(f"Error checking quote expiry: {e}")
        pg_connection.rollback()

def convert_accepted_quotes():
    """Convert accepted quotes to sales orders (ERP integration)"""
    logger.info("Converting accepted quotes to orders...")
    
    try:
        cursor = pg_connection.cursor()
        
        # Check if sales_orders table exists (ERP integration)
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'sales_orders'
            )
        """)
        
        if not cursor.fetchone()[0]:
            cursor.close()
            return
        
        # Get accepted quotes not yet converted
        cursor.execute("""
            SELECT quotation_id, opportunity_id, account_id, total_amount
            FROM quotations
            WHERE quotation_status = 'accepted'
            AND converted = false
            LIMIT 5
        """)
        
        quotes = cursor.fetchall()
        
        for quote_id, opp_id, account_id, amount in quotes:
            # Would create sales order in ERP here
            # For now, just mark as converted
            
            cursor.execute("""
                UPDATE quotations
                SET converted = true,
                    converted_date = %s
                WHERE quotation_id = %s
            """, (datetime.now().date(), quote_id))
            
            # Update opportunity to closed won
            if opp_id:
                cursor.execute("""
                    UPDATE opportunities
                    SET stage = 'closed_won',
                        probability_pct = 100,
                        is_closed = true,
                        actual_close_date = %s
                    WHERE opportunity_id = %s
                """, (datetime.now().date(), opp_id))
            
            # Log integration
            cursor.execute("""
                INSERT INTO crm_integration_log (
                    log_id, integration_direction, document_type,
                    document_id, integration_status, log_timestamp
                ) VALUES (%s, %s, %s, %s, %s, %s)
            """, (generate_id('INTLOG'), 'CRM_TO_ERP',
                  'quotation', quote_id, 'completed', datetime.now()))
            
            stats['quotes_converted'] += 1
        
        pg_connection.commit()
        cursor.close()
        
        if quotes:
            logger.info(f"Converted {len(quotes)} quotes to orders")
    except Exception as e:
        logger.error(f"Error converting quotes: {e}")
        pg_connection.rollback()

# ============================================================================
# CASE MANAGEMENT
# ============================================================================

def monitor_case_sla():
    """Monitor case SLA violations"""
    logger.info("Monitoring case SLAs...")
    
    try:
        cursor = pg_connection.cursor()
        
        # Check for SLA violations
        cursor.execute("""
            UPDATE cases
            SET sla_violated = true
            WHERE case_status IN ('new', 'in_progress')
            AND (
                (response_due_date IS NOT NULL AND response_due_date < %s 
                 AND first_response_date IS NULL)
                OR
                (resolution_due_date IS NOT NULL AND resolution_due_date < %s 
                 AND resolved_date IS NULL)
            )
        """, (datetime.now(), datetime.now()))
        
        pg_connection.commit()
        cursor.close()
    except Exception as e:
        logger.error(f"Error monitoring SLA: {e}")
        pg_connection.rollback()

def auto_resolve_cases():
    """Auto-resolve simple cases"""
    logger.info("Auto-resolving cases...")
    
    try:
        cursor = pg_connection.cursor()
        
        # Auto-resolve low priority cases after 30 days
        cursor.execute("""
            UPDATE cases
            SET case_status = 'resolved',
                resolved_date = %s
            WHERE case_status = 'pending_customer'
            AND priority = 'low'
            AND created_at < %s
            LIMIT 5
        """, (datetime.now(), datetime.now() - timedelta(days=30)))
        
        rows = cursor.rowcount
        stats['cases_resolved'] += rows
        
        pg_connection.commit()
        cursor.close()
        
        if rows > 0:
            logger.info(f"Auto-resolved {rows} cases")
    except Exception as e:
        logger.error(f"Error auto-resolving cases: {e}")
        pg_connection.rollback()

# ============================================================================
# CONTRACT MANAGEMENT
# ============================================================================

def check_contract_renewals():
    """Check for contracts due for renewal"""
    logger.info("Checking contract renewals...")
    
    try:
        cursor = pg_connection.cursor()
        
        # Get contracts due for renewal in next 60 days
        cursor.execute("""
            SELECT contract_id, account_id, contract_value
            FROM contracts
            WHERE contract_status = 'active'
            AND auto_renewal = true
            AND contract_end_date <= %s
            AND contract_end_date >= %s
            LIMIT 5
        """, ((datetime.now() + timedelta(days=60)).date(),
              datetime.now().date()))
        
        contracts = cursor.fetchall()
        
        for contract_id, account_id, value in contracts:
            # Create renewal contract
            new_contract_id = generate_id('CONT')
            
            cursor.execute("""
                INSERT INTO contracts (
                    contract_id, contract_number, contract_name,
                    account_id, contract_type, contract_start_date,
                    contract_end_date, contract_value, contract_status,
                    auto_renewal, parent_contract_id, created_at
                )
                SELECT %s, %s, contract_name || ' - Renewal',
                       account_id, contract_type,
                       contract_end_date + INTERVAL '1 day',
                       contract_end_date + INTERVAL '1 year',
                       %s, 'draft', auto_renewal, %s, %s
                FROM contracts
                WHERE contract_id = %s
            """, (new_contract_id, f"CONT-{new_contract_id}",
                  value, contract_id, datetime.now(), contract_id))
            
            stats['contracts_renewed'] += 1
        
        pg_connection.commit()
        cursor.close()
        
        if contracts:
            logger.info(f"Created {len(contracts)} renewal contracts")
    except Exception as e:
        logger.error(f"Error checking renewals: {e}")
        pg_connection.rollback()

# ============================================================================
# MAIN CYCLE
# ============================================================================

def run_crm_cycle():
    """Execute complete CRM cycle"""
    logger.info("=== CRM Cycle Starting ===")
    
    try:
        # 1. Lead Management
        score_and_qualify_leads()
        convert_qualified_leads()
        
        # 2. Opportunity Management
        progress_opportunities()
        
        # 3. Quotation Management
        process_quote_approvals()
        check_quote_expiry()
        convert_accepted_quotes()
        
        # 4. Case Management
        monitor_case_sla()
        auto_resolve_cases()
        
        # 5. Contract Management
        check_contract_renewals()
        
        stats['cycles'] += 1
        logger.info("=== CRM Cycle Complete ===")
        return True
    except Exception as e:
        logger.error(f"CRM cycle error: {e}")
        return False

def print_stats():
    """Print daemon statistics"""
    elapsed = (datetime.now() - stats['start_time']).total_seconds()
    hours = elapsed / 3600
    
    logger.info("="*80)
    logger.info(f"CRM Daemon Statistics")
    logger.info(f"  Uptime: {hours:.1f} hours")
    logger.info(f"  Cycles: {stats['cycles']}")
    logger.info(f"  Leads Scored: {stats['leads_scored']}")
    logger.info(f"  Opportunities Progressed: {stats['opportunities_progressed']}")
    logger.info(f"  Quotes Generated: {stats['quotes_generated']}")
    logger.info(f"  Quotes Converted: {stats['quotes_converted']}")
    logger.info(f"  Cases Resolved: {stats['cases_resolved']}")
    logger.info(f"  Contracts Renewed: {stats['contracts_renewed']}")
    logger.info("="*80)

def main():
    """Main daemon loop"""
    logger.info("="*80)
    logger.info("GenIMS CRM Daemon Starting")
    logger.info("Cycle Interval: Every 30 minutes")
    logger.info("="*80)
    
    if not initialize_database():
        return 1
    
    if not load_master_data():
        return 1
    
    logger.info("Press Ctrl+C to stop")
    
    last_cycle = datetime.now() - timedelta(hours=1)
    
    while running:
        try:
            now = datetime.now()
            
            # Run every 30 minutes
            if (now - last_cycle).total_seconds() >= CYCLE_INTERVAL_SECONDS:
                run_crm_cycle()
                last_cycle = now
            
            # Print stats every hour
            if now.minute == 0:
                print_stats()
            
            time.sleep(60)  # Check every minute
            
        except Exception as e:
            logger.error(f"Error in main loop: {e}", exc_info=True)
            time.sleep(60)
    
    logger.info("Shutting down...")
    if pg_connection:
        pg_connection.close()
    
    print_stats()
    logger.info("CRM Daemon stopped")
    return 0

if __name__ == "__main__":
    import os
    os.makedirs('logs', exist_ok=True)
    sys.exit(main())
