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
from decimal import Decimal, ROUND_HALF_UP
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

# Import registry helper
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'scripts'))
HELPER_AVAILABLE = True
try:
    from generator_helper import get_helper
except ImportError:
    HELPER_AVAILABLE = False
    
class TimeCoordinator:
    """Manages time coordination and current-date enforcement"""
    def __init__(self):
        # Always use current date for data generation
        current_time = datetime.now()
        self.base_time = current_time.replace(hour=0, minute=0, second=0, microsecond=0)
        
    def get_current_time(self):
        """Get current date enforced time"""
        return self.base_time
        
    def get_timestamp_with_offset(self, offset_seconds):
        """Get timestamp with offset but still on current date"""
        return self.base_time + timedelta(seconds=offset_seconds)
        
    def add_coordination_delay(self, operation_name):
        """Add time coordination delay between operations"""
        delay = random.uniform(2.0, 3.5)
        time.sleep(delay)
        logger.info(f"Time coordination delay for {operation_name}: {delay:.2f}s")
        
    def generate_unique_timestamp(self, base_offset=0):
        """Generate unique timestamp with millisecond precision"""
        current_time = self.base_time + timedelta(seconds=base_offset)
        return current_time.strftime('%Y%m%d%H%M%S') + f"{current_time.microsecond // 1000:03d}"

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

def validate_rfq_response_compliance(rfq_data, response_data):
    """Validate RFQ response meets RFQ requirements"""
    try:
        # Check response is within deadline
        response_date = response_data.get('response_date')
        deadline = rfq_data.get('response_deadline')
        
        if response_date and deadline and response_date > deadline:
            logger.warning(f"RFQ response after deadline: {response_date} > {deadline}")
            return False
            
        # Validate commercial terms
        if response_data.get('total_quoted_value', 0) <= 0:
            logger.warning("Invalid quoted value in RFQ response")
            return False
            
        return True
    except Exception as e:
        logger.error(f"RFQ response validation error: {e}")
        return False

def validate_3_way_matching(po_data, receipt_data, invoice_data):
    """Validate 3-way matching for supplier invoices"""
    try:
        # Quantity matching (with tolerance)
        po_qty = po_data.get('quantity', 0)
        receipt_qty = receipt_data.get('received_quantity', 0)
        invoice_qty = invoice_data.get('invoiced_quantity', 0)
        
        tolerance_pct = 2.0  # 2% tolerance
        
        # Check quantity variances
        receipt_variance = abs(receipt_qty - po_qty) / po_qty * 100 if po_qty > 0 else 0
        invoice_variance = abs(invoice_qty - receipt_qty) / receipt_qty * 100 if receipt_qty > 0 else 0
        
        # Price matching
        po_price = po_data.get('unit_price', 0)
        invoice_price = invoice_data.get('unit_price', 0)
        price_variance = abs(invoice_price - po_price) / po_price * 100 if po_price > 0 else 0
        
        match_result = {
            'quantity_match': receipt_variance <= tolerance_pct and invoice_variance <= tolerance_pct,
            'price_match': price_variance <= tolerance_pct,
            'within_tolerance': receipt_variance <= tolerance_pct and invoice_variance <= tolerance_pct and price_variance <= tolerance_pct,
            'receipt_variance_pct': receipt_variance,
            'invoice_variance_pct': invoice_variance,
            'price_variance_pct': price_variance
        }
        
        return match_result
    except Exception as e:
        logger.error(f"3-way matching validation error: {e}")
        return {'quantity_match': False, 'price_match': False, 'within_tolerance': False}

def calculate_supplier_rating(performance_metrics):
    """Calculate overall supplier rating from performance metrics"""
    try:
        # Weight factors
        delivery_weight = 0.3
        quality_weight = 0.3
        responsiveness_weight = 0.2
        commercial_weight = 0.2
        
        # Calculate weighted score - ensure all values are float
        delivery_score = float(performance_metrics.get('ontime_delivery_pct', 0))
        quality_score = float(performance_metrics.get('quality_acceptance_pct', 0))
        response_score = float(performance_metrics.get('response_rate_pct', 0))
        commercial_score = float(performance_metrics.get('invoice_accuracy_pct', 0))
        
        overall_score = (
            delivery_score * delivery_weight +
            quality_score * quality_weight +
            response_score * responsiveness_weight +
            commercial_score * commercial_weight
        )
        
        # Determine rating category
        if overall_score >= 90:
            rating = 'excellent'
        elif overall_score >= 75:
            rating = 'good'
        elif overall_score >= 60:
            rating = 'acceptable'
        elif overall_score >= 40:
            rating = 'needs_improvement'
        else:
            rating = 'poor'
            
        return overall_score, rating
    except Exception as e:
        logger.error(f"Supplier rating calculation error: {e}")
        return 0, 'poor'

def validate_contract_pricing(contract_data, material_id, pricing_data):
    """Validate contract pricing against contract terms"""
    try:
        # Check contract is active
        if contract_data.get('contract_status') != 'active':
            return False
            
        # Check pricing effective dates
        current_date = datetime.now().date()
        effective_from = pricing_data.get('effective_from')
        effective_to = pricing_data.get('effective_to')
        
        if effective_from and current_date < effective_from:
            return False
            
        if effective_to and current_date > effective_to:
            return False
            
        # Validate price is reasonable (basic check)
        unit_price = pricing_data.get('unit_price', 0)
        if unit_price <= 0:
            return False
            
        return True
    except Exception as e:
        logger.error(f"Contract pricing validation error: {e}")
        return False

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

def reset_supplier_portal_sequences():
    """Reset all supplier portal sequences to prevent duplicate key errors"""
    try:
        conn = psycopg2.connect(
            host=PG_HOST,
            port=PG_PORT,
            database=PG_SUPPLIER_DB,
            user=PG_USER,
            password=PG_PASSWORD,
            sslmode=PG_SSL_MODE,
            connect_timeout=10
        )
        cursor = conn.cursor()
        
        # Reset sequences for tables with auto-increment IDs (only tables with actual SERIAL columns)
        sequences_to_reset = [
            # Note: supplier_invoices and supplier_performance_metrics use custom ID patterns, not sequences
            # Only add actual SERIAL column sequences here if any exist
        ]
        
        for table_name, id_column, sequence_name in sequences_to_reset:
            try:
                cursor.execute(f"SELECT MAX({id_column}) FROM {table_name};")
                max_id = cursor.fetchone()[0]
                
                if max_id is not None:
                    next_val = max_id + 1
                    cursor.execute(f"SELECT setval('{sequence_name}', {next_val})")
                    logger.info(f"✓ Reset {sequence_name} to {next_val}")
            except Exception as e:
                logger.warning(f"Could not reset sequence {sequence_name}: {e}")
        
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        logger.warning(f"Could not reset supplier portal sequences: {e}")

def get_max_id_counter(table_name, id_column, id_prefix):
    """Get the next ID counter for a given table"""
    try:
        cursor = pg_connection.cursor()
        # Handle different ID patterns:
        # - METRIC-000180 (no year)
        # - PR-2026-00030, RFQ-2026-00020, SI-2026-00050, AUD-2026-030 (with year)
        if id_prefix == 'METRIC':
            # Pattern: METRIC-000180 - extract last numeric part
            cursor.execute(f"""
                SELECT COALESCE(MAX(CAST(SUBSTRING({id_column} FROM 'METRIC-([0-9]+)$') AS INTEGER)), 0)
                FROM {table_name}
                WHERE {id_column} LIKE 'METRIC-%'
            """)
        else:
            # Pattern: PREFIX-YEAR-SEQUENCE - extract sequence part (last numeric part)
            cursor.execute(f"""
                SELECT COALESCE(MAX(CAST(SUBSTRING({id_column} FROM '.*-([0-9]+)$') AS INTEGER)), 0)
                FROM {table_name}
                WHERE {id_column} LIKE '{id_prefix}-%'
            """)
        max_id = cursor.fetchone()[0]
        cursor.close()
        return (max_id or 0) + 1
    except Exception as e:
        logger.debug(f"Could not get max ID from {table_name}.{id_column}: {e}")
        return 1

def initialize_id_counters():
    """Initialize ID counters based on existing data"""
    global counters
    try:
        counters['requisition'] = get_max_id_counter('purchase_requisitions', 'requisition_number', 'PR')
        counters['rfq'] = get_max_id_counter('rfq_headers', 'rfq_number', 'RFQ')
        counters['invoice'] = get_max_id_counter('supplier_invoices', 'invoice_number', 'SI')
        counters['audit'] = get_max_id_counter('supplier_audits', 'audit_number', 'AUD')
        counters['performance'] = get_max_id_counter('supplier_performance_metrics', 'metric_id', 'METRIC')
        
        logger.info(f"ID Counters initialized: {counters}")
        return True
    except Exception as e:
        logger.error(f"Failed to initialize ID counters: {e}")
        return False

def load_master_data(helper=None):
    global master_data
    try:
        conn = psycopg2.connect(
            host=PG_HOST, port=PG_PORT, database=PG_SUPPLIER_DB,
            user=PG_USER, password=PG_PASSWORD, sslmode=PG_SSL_MODE, connect_timeout=30
        )
        cursor = conn.cursor()
        
        # Load suppliers using registry if available
        if helper and hasattr(helper, 'get_valid_supplier_ids'):
            suppliers = list(helper.get_valid_supplier_ids())
            if not suppliers:
                # Fallback to database query
                cursor.execute("SELECT DISTINCT supplier_id FROM supplier_contracts LIMIT 50")
                suppliers = [row[0] for row in cursor.fetchall()]
        else:
            cursor.execute("SELECT DISTINCT supplier_id FROM supplier_contracts LIMIT 50")
            suppliers = [row[0] for row in cursor.fetchall()]
        
        # Load employees using registry if available
        if helper and hasattr(helper, 'get_valid_employee_ids'):
            employees = list(helper.get_valid_employee_ids())
            if not employees:
                # Use fallback employee IDs
                employees = [f"EMP-{i:06d}" for i in range(1, 31)]
        else:
            employees = [f"EMP-{i:06d}" for i in range(1, 31)]
        
        # Load departments using registry if available
        if helper and hasattr(helper, 'get_valid_department_ids'):
            departments = list(helper.get_valid_department_ids())
            if not departments:
                departments = [f"DEPT-{i:03d}" for i in range(1, 11)]
        else:
            departments = [f"DEPT-{i:03d}" for i in range(1, 11)]
        
        # Load materials using registry if available
        if helper and hasattr(helper, 'get_valid_material_ids'):
            materials = list(helper.get_valid_material_ids())
            if not materials:
                materials = [f"MAT-{i:06d}" for i in range(1, 101)]
        else:
            materials = [f"MAT-{i:06d}" for i in range(1, 101)]
        
        # Load users
        cursor.execute("SELECT portal_user_id FROM supplier_portal_users WHERE is_active = true LIMIT 30")
        users = [row[0] for row in cursor.fetchall()]
        if not users:
            users = employees[:10]  # Use some employees as portal users
        
        # Load existing performance metrics to avoid duplicates
        cursor.execute("""
            SELECT supplier_id, metric_period
            FROM supplier_performance_metrics
        """)
        existing_metrics = set(cursor.fetchall())
        
        # Load existing contracts for pricing validation
        cursor.execute("""
            SELECT contract_id, supplier_id, contract_status, start_date, end_date
            FROM supplier_contracts
            WHERE contract_status = 'active'
        """)
        active_contracts = {row[0]: {
            'supplier_id': row[1],
            'contract_status': row[2],
            'start_date': row[3],
            'end_date': row[4]
        } for row in cursor.fetchall()}
        
        cursor.close()
        conn.close()
        
        master_data['suppliers'] = suppliers or ['SUP-000001', 'SUP-000002']
        master_data['employees'] = employees
        master_data['departments'] = departments
        master_data['materials'] = materials
        master_data['users'] = users
        master_data['existing_metrics'] = existing_metrics
        master_data['active_contracts'] = active_contracts
        
        logger.info(f"Master data loaded: {len(suppliers)} suppliers, {len(employees)} employees, {len(materials)} materials, {len(users)} users")
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
    """Main - Generate all supplier portal data in-memory, then bulk dump"""
    logger.info("="*80)
    logger.info("GenIMS Supplier Portal Daemon - ULTRA FAST MODE (In-Memory Generation)")
    logger.info("="*80)
    logger.info(f"Configuration:")
    logger.info(f"  Database: {PG_SUPPLIER_DB}")
    logger.info(f"  Batch Size: {BATCH_SIZE}")
    logger.info("="*80)
    
    # Initialize time coordinator and helper
    time_coord = TimeCoordinator()
    logger.info(f"Using current date for data generation: {time_coord.get_current_time()}")
    logger.info(f"Time Coordinator initialized: {time_coord.get_current_time()}")
    
    if HELPER_AVAILABLE:
        try:
            helper = get_helper()
            # Get total registered IDs for logging
            total_ids = sum(len(ids) for ids in helper.registry.registered_ids.values()) if hasattr(helper.registry, 'registered_ids') else 0
            logger.info(f"Registry helper loaded with {total_ids} total registered IDs")
        except Exception as e:
            logger.warning(f"Registry helper failed to load: {e}")
            helper = None
    else:
        logger.warning("Registry helper not available, using fallback data")
        helper = None
    
    start_time = time.time()
    
    # Initialize
    if not initialize_database():
        return 1
    
    if not initialize_id_counters():
        return 1
    
    if not load_master_data(helper):
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
    
    # FK Validation
    if not master_data['suppliers'] or not master_data['employees']:
        logger.error("Critical: Missing master data for FK references")
        return 1
    
    # Get validated IDs for assignment
    if helper:
        try:
            valid_supplier_ids = list(helper.get_valid_supplier_ids()) if hasattr(helper, 'get_valid_supplier_ids') else master_data['suppliers']
            valid_employee_ids = list(helper.get_valid_employee_ids()) if hasattr(helper, 'get_valid_employee_ids') else master_data['employees']
            valid_material_ids = list(helper.get_valid_material_ids()) if hasattr(helper, 'get_valid_material_ids') else master_data['materials']
            
            if not valid_supplier_ids:
                logger.warning("No valid supplier IDs found, using master data")
                valid_supplier_ids = master_data['suppliers']
            if not valid_employee_ids:
                logger.warning("No valid employee IDs found, using master data")
                valid_employee_ids = master_data['employees']
            if not valid_material_ids:
                logger.warning("No valid material IDs found, using master data")
                valid_material_ids = master_data['materials']
        except Exception as e:
            logger.warning(f"Registry validation failed: {e}, using master data")
            valid_supplier_ids = master_data['suppliers']
            valid_employee_ids = master_data['employees']
            valid_material_ids = master_data['materials']
    else:
        logger.info("Using master data for FK assignments (no helper)")
        valid_supplier_ids = master_data['suppliers']
        valid_employee_ids = master_data['employees']
        valid_material_ids = master_data['materials']
    
    logger.info(f"FK Validation: {len(valid_supplier_ids)} suppliers, {len(valid_employee_ids)} employees, {len(valid_material_ids)} materials")
    
    # Generate data
    requisitions = []
    rfq_headers = []
    invoices = []
    audits = []
    performance_metrics = []
    
    # Use current date from TimeCoordinator
    sim_base_time = time_coord.get_current_time()
    run_timestamp = time_coord.generate_unique_timestamp()
    
    # Track unique combinations to avoid UNIQUE constraint violations
    performance_metrics_seen = set(master_data.get('existing_metrics', []))
    
    # Generate supplier portal records with enhanced validation
    for i in range(TOTAL_RECORDS):
        timestamp_offset = i * 300  # 5 minute intervals
        current_ts = time_coord.get_timestamp_with_offset(timestamp_offset)
        current_date = current_ts.date()
        
        # Use validated IDs
        supplier = random.choice(valid_supplier_ids)
        employee = random.choice(valid_employee_ids)
        material = random.choice(valid_material_ids)
        department = random.choice(master_data['departments'])
        
        # Purchase Requisitions (1 per 100 records) with enhanced validation
        if i % 100 == 0:
            req_counter = counters['requisition'] + i // 100
            req_id = f"REQ-{req_counter:06d}"
            req_num = f"PR-{time_coord.get_current_time().year}-{req_counter:06d}"
            
            # Business logic: required_by_date must be future from requisition_date
            required_by_date = current_date + timedelta(days=random.randint(7, 30))
            estimated_total = Decimal(str(random.uniform(1000, 50000))).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            
            requisitions.append({
                'requisition_id': req_id,
                'requisition_number': req_num,
                'requested_by': employee,
                'department_id': department,
                'requisition_date': current_date,
                'required_by_date': required_by_date,
                'requisition_type': random.choice(['standard', 'urgent', 'capital', 'service']),
                'requisition_status': random.choice(['draft', 'submitted', 'approved', 'rejected', 'converted_to_rfq']),
                'estimated_total': float(estimated_total),
                'created_at': current_ts
            })
        
        # RFQ Headers (1 per 150 records) with deadline validation
        if i % 150 == 0:
            rfq_counter = counters['rfq'] + i // 150
            rfq_id = f"RFQ-{time_coord.get_current_time().year}-{rfq_counter:05d}"
            rfq_num = rfq_id  # Use same format for both ID and number
            
            # Business logic: response_deadline must be future, delivery date after deadline
            response_deadline = current_date + timedelta(days=random.randint(5, 15))
            expected_delivery_date = response_deadline + timedelta(days=random.randint(15, 45))
            
            rfq_headers.append({
                'rfq_id': rfq_id,
                'rfq_number': rfq_num,
                'rfq_title': f"RFQ for {material} and related items",
                'rfq_type': random.choice(['standard', 'urgent', 'blanket', 'spot_buy']),
                'requested_by': employee,
                'department_id': department,
                'rfq_date': current_date,
                'response_deadline': response_deadline,
                'expected_delivery_date': expected_delivery_date,
                'rfq_status': random.choice(['draft', 'published', 'response_period', 'evaluation', 'awarded']),
                'total_estimated_value': float(Decimal(str(random.uniform(5000, 100000))).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)),
                'currency_code': 'USD',
                'created_at': current_ts
            })
        
        # Supplier Invoices (1 per 75 records) with 3-way matching logic
        if i % 75 == 0:
            inv_id = f"INV-{(counters['invoice'] + i // 75):06d}"
            inv_num = f"SI-{time_coord.get_current_time().year}-{(counters['invoice'] + i // 75):05d}"
            supplier_inv_num = f"SUPINV-{random.randint(100000, 999999)}"
            
            # Enhanced invoice generation with proper decimal handling
            subtotal = Decimal(str(random.uniform(1000, 50000))).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            tax_rate = Decimal('0.10')  # 10% tax
            tax_amount = (subtotal * tax_rate).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            total_amount = subtotal + tax_amount
            
            # 3-way matching simulation
            po_quantity = Decimal(str(random.uniform(10, 100))).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            received_quantity = po_quantity + Decimal(str(random.uniform(-2, 2))).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)  # Small variance
            
            # Simulate 3-way matching validation
            mock_po_data = {'quantity': float(po_quantity), 'unit_price': float(subtotal / po_quantity)}
            mock_receipt_data = {'received_quantity': float(received_quantity)}
            mock_invoice_data = {'invoiced_quantity': float(received_quantity), 'unit_price': float(subtotal / received_quantity)}
            
            match_result = validate_3_way_matching(mock_po_data, mock_receipt_data, mock_invoice_data)
            
            invoices.append({
                'invoice_id': inv_id,
                'invoice_number': inv_num,
                'supplier_invoice_number': supplier_inv_num,
                'supplier_id': supplier,
                'invoice_date': current_date,
                'due_date': current_date + timedelta(days=random.randint(15, 45)),
                'subtotal': float(subtotal),
                'tax_amount': float(tax_amount),
                'total_amount': float(total_amount),
                'currency_code': 'USD',
                'matching_status': 'matched' if match_result['within_tolerance'] else 'variance',
                'po_match': True,
                'receipt_match': match_result['quantity_match'],
                'price_match': match_result['price_match'],
                'quantity_variance': random.uniform(-5, 5) if not match_result['quantity_match'] else 0,
                'price_variance': random.uniform(-100, 100) if not match_result['price_match'] else 0,
                'invoice_status': random.choice(['received', 'under_review', 'approved', 'rejected']),
                'payment_status': random.choice(['pending', 'scheduled', 'paid']),
                'paid_date': current_date + timedelta(days=random.randint(20, 50)) if random.random() > 0.5 else None,
                'created_at': current_ts
            })
        
        # Supplier Audits (1 per 200 records) with enhanced audit logic
        if i % 200 == 0:
            audit_counter = counters['audit'] + i // 200
            audit_id = f"AUD-{audit_counter:06d}"
            audit_num = f"AUD-{time_coord.get_current_time().year}-{audit_counter:03d}"
            
            # Enhanced audit scoring with validation
            audit_score = Decimal(str(random.uniform(60, 100))).quantize(Decimal('0.1'), rounding=ROUND_HALF_UP)
            
            # Determine audit rating based on score
            if audit_score >= 90:
                audit_rating = 'excellent'
            elif audit_score >= 75:
                audit_rating = 'satisfactory'
            elif audit_score >= 60:
                audit_rating = 'needs_improvement'
            else:
                audit_rating = 'unsatisfactory'
                
            audits.append({
                'audit_id': audit_id,
                'audit_number': audit_num,
                'supplier_id': supplier,
                'audit_type': random.choice(['initial', 'periodic', 'special', 'post_incident']),
                'audit_scope': random.choice(['quality_system', 'production', 'warehouse', 'management']),
                'actual_date': current_date,
                'lead_auditor': employee,
                'audit_status': random.choice(['completed', 'report_pending', 'closed']),
                'audit_score': float(audit_score),
                'audit_rating': audit_rating,
                'major_findings': random.randint(0, 3),
                'minor_findings': random.randint(0, 8),
                'followup_required': audit_score < 85,
                'followup_date': current_date + timedelta(days=random.randint(90, 365)) if audit_score < 85 else None,
                'created_at': current_ts
            })
        
        # Supplier Performance Metrics (every 200 records for guaranteed generation) with enhanced calculation
        if i % 200 == 0:
            # Generate unique period for each supplier to avoid constraint violations
            # Use current counter to create unique periods
            months_offset = (i // 200) + 1  # Start from 1 month offset
            metric_date = current_date - timedelta(days=30 * months_offset)
            metric_period = f"{metric_date.year}-{metric_date.month:02d}"
            metric_key = (supplier, metric_period)
            
            # Only generate if this combination doesn't exist in database or seen set
            if metric_key not in master_data['existing_metrics'] and metric_key not in performance_metrics_seen:
                performance_metrics_seen.add(metric_key)
                metric_id = f"METRIC-{(counters['performance'] + len(performance_metrics)):06d}"
                
                # Generate realistic performance data
                total_pos = random.randint(10, 100)
                pos_ontime = random.randint(max(1, int(total_pos * 0.8)), total_pos)
                ontime_delivery_pct = round((pos_ontime / total_pos) * 100, 1) if total_pos > 0 else 0
                
                total_qty_received = Decimal(str(random.uniform(1000, 10000))).quantize(Decimal('0.1'), rounding=ROUND_HALF_UP)
                qty_accepted = total_qty_received - Decimal(str(random.uniform(0, float(total_qty_received) * 0.05))).quantize(Decimal('0.1'), rounding=ROUND_HALF_UP)
                quality_acceptance_pct = round(float(qty_accepted / total_qty_received) * 100, 1) if total_qty_received > 0 else 0
                
                rfqs_sent = random.randint(5, 20)
                rfqs_responded = random.randint(max(1, int(rfqs_sent * 0.7)), rfqs_sent)
                response_rate_pct = round((rfqs_responded / rfqs_sent) * 100, 1) if rfqs_sent > 0 else 0
                
                # Calculate overall score using the rating function
                perf_data = {
                    'ontime_delivery_pct': ontime_delivery_pct,
                    'quality_acceptance_pct': quality_acceptance_pct,
                    'response_rate_pct': response_rate_pct,
                    'invoice_accuracy_pct': round(random.uniform(90, 100), 1)
                }
                overall_score, performance_rating = calculate_supplier_rating(perf_data)
                
                performance_metrics.append({
                    'metric_id': metric_id,
                    'supplier_id': supplier,
                    'metric_period': metric_period,
                    'total_pos_issued': total_pos,
                    'pos_delivered_ontime': pos_ontime,
                    'ontime_delivery_pct': ontime_delivery_pct,
                    'average_lead_time_days': round(random.uniform(5, 30), 1),
                    'total_quantity_received': float(total_qty_received),
                    'quantity_accepted': float(qty_accepted),
                    'quality_acceptance_pct': quality_acceptance_pct,
                    'defect_ppm': random.randint(0, 100),
                    'rfqs_sent': rfqs_sent,
                    'rfqs_responded': rfqs_responded,
                    'response_rate_pct': response_rate_pct,
                    'total_spend': float(Decimal(str(random.uniform(10000, 500000))).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)),
                    'invoice_accuracy_pct': perf_data['invoice_accuracy_pct'],
                    'overall_score': round(overall_score, 1),
                    'performance_rating': performance_rating,
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
        
        # Insert requisitions with time coordination
        if requisitions:
            insert_sql = """INSERT INTO purchase_requisitions (
                requisition_id, requisition_number, requested_by, department_id, requisition_date,
                required_by_date, requisition_type, requisition_status, estimated_total, created_at
            ) VALUES (%(requisition_id)s, %(requisition_number)s, %(requested_by)s, %(department_id)s,
                %(requisition_date)s, %(required_by_date)s, %(requisition_type)s, %(requisition_status)s,
                %(estimated_total)s, %(created_at)s)"""
            logger.info(f"Inserting {len(requisitions):,} purchase requisitions...")
            insert_batch_parallel(cursor, insert_sql, requisitions, "purchase_requisitions", BATCH_SIZE, pg_connection)
            
            # Time coordination delay
            time_coord.add_coordination_delay("purchase requisitions")
        
        # Insert RFQ headers with time coordination
        if rfq_headers:
            insert_sql = """INSERT INTO rfq_headers (
                rfq_id, rfq_number, rfq_title, rfq_type, requested_by, department_id,
                rfq_date, response_deadline, expected_delivery_date, rfq_status,
                total_estimated_value, currency_code, created_at
            ) VALUES (%(rfq_id)s, %(rfq_number)s, %(rfq_title)s, %(rfq_type)s, %(requested_by)s,
                %(department_id)s, %(rfq_date)s, %(response_deadline)s, %(expected_delivery_date)s,
                %(rfq_status)s, %(total_estimated_value)s, %(currency_code)s, %(created_at)s)
            """
            logger.info(f"Inserting {len(rfq_headers):,} RFQ headers...")
            insert_batch_parallel(cursor, insert_sql, rfq_headers, "rfq_headers", BATCH_SIZE, pg_connection)
            
            # Time coordination delay
            time_coord.add_coordination_delay("RFQ headers")
        
        # Insert invoices with time coordination
        if invoices:
            insert_sql = """INSERT INTO supplier_invoices (
                invoice_id, invoice_number, supplier_invoice_number, supplier_id, invoice_date,
                due_date, subtotal, tax_amount, total_amount, currency_code, 
                matching_status, po_match, receipt_match, price_match, quantity_variance, price_variance,
                invoice_status, payment_status, paid_date, created_at
            ) VALUES (%(invoice_id)s, %(invoice_number)s, %(supplier_invoice_number)s, %(supplier_id)s,
                %(invoice_date)s, %(due_date)s, %(subtotal)s, %(tax_amount)s, %(total_amount)s,
                %(currency_code)s, %(matching_status)s, %(po_match)s, %(receipt_match)s, %(price_match)s,
                %(quantity_variance)s, %(price_variance)s, %(invoice_status)s, %(payment_status)s, 
                %(paid_date)s, %(created_at)s)
            """
            logger.info(f"Inserting {len(invoices):,} supplier invoices...")
            insert_batch_parallel(cursor, insert_sql, invoices, "supplier_invoices", BATCH_SIZE, pg_connection)
            
            # Time coordination delay
            time_coord.add_coordination_delay("supplier invoices")
        
        # Insert audits with time coordination
        if audits:
            insert_sql = """INSERT INTO supplier_audits (
                audit_id, audit_number, supplier_id, audit_type, audit_scope, actual_date, lead_auditor,
                audit_status, audit_score, audit_rating, major_findings, minor_findings, 
                followup_required, followup_date, created_at
            ) VALUES (%(audit_id)s, %(audit_number)s, %(supplier_id)s, %(audit_type)s, %(audit_scope)s,
                %(actual_date)s, %(lead_auditor)s, %(audit_status)s, %(audit_score)s,
                %(audit_rating)s, %(major_findings)s, %(minor_findings)s, %(followup_required)s,
                %(followup_date)s, %(created_at)s)
            """
            logger.info(f"Inserting {len(audits):,} supplier audits...")
            insert_batch_parallel(cursor, insert_sql, audits, "supplier_audits", BATCH_SIZE, pg_connection)
            
            # Time coordination delay
            time_coord.add_coordination_delay("supplier audits")
        
        # Insert performance metrics with time coordination
        if performance_metrics:
            insert_sql = """INSERT INTO supplier_performance_metrics (
                metric_id, supplier_id, metric_period, total_pos_issued, pos_delivered_ontime,
                ontime_delivery_pct, average_lead_time_days, total_quantity_received, quantity_accepted,
                quality_acceptance_pct, defect_ppm, rfqs_sent, rfqs_responded, response_rate_pct, 
                total_spend, invoice_accuracy_pct, overall_score, performance_rating, created_at
            ) VALUES (%(metric_id)s, %(supplier_id)s, %(metric_period)s, %(total_pos_issued)s,
                %(pos_delivered_ontime)s, %(ontime_delivery_pct)s, %(average_lead_time_days)s,
                %(total_quantity_received)s, %(quantity_accepted)s, %(quality_acceptance_pct)s,
                %(defect_ppm)s, %(rfqs_sent)s, %(rfqs_responded)s, %(response_rate_pct)s,
                %(total_spend)s, %(invoice_accuracy_pct)s, %(overall_score)s, %(performance_rating)s, %(created_at)s)
            """
            logger.info(f"Inserting {len(performance_metrics):,} performance metrics...")
            insert_batch_parallel(cursor, insert_sql, performance_metrics, "supplier_performance_metrics", BATCH_SIZE, pg_connection)
        
        cursor.close()
        
        # Commit all data
        pg_connection.commit()
        
        logger.info(f"✓ All records inserted successfully")
        
        # Reset sequences to prevent duplicate key errors on next run
        reset_supplier_portal_sequences()
        
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
