#!/usr/bin/env python3
"""
GenIMS Full Setup Script - REVISED
Orchestrates: Database Creation → Schema Loading → MASTER DATA GENERATION → 
REGISTER IDs → DEPENDENT DATA GENERATION → VALIDATION → DATA LOADING
Ensures referential integrity across all 13 databases and 268 tables
"""

import os
import sys
import json
import psycopg2
import subprocess
from pathlib import Path
from datetime import datetime
import logging
from dotenv import load_dotenv

# Import registry for validation
sys.path.insert(0, str(Path(__file__).parent))
from data_registry import DataRegistry, get_registry

# Load .env file
env_path = Path(__file__).parent.parent / '.env'
if env_path.exists():
    load_dotenv(env_path)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Configuration - Load from .env with fallback defaults
DB_HOST = os.getenv('POSTGRES_HOST', 'localhost')
DB_PORT = int(os.getenv('POSTGRES_PORT', '5432'))
DB_USER = os.getenv('POSTGRES_USERNAME', 'postgres')
DB_PASSWORD = os.getenv('POSTGRES_PASSWORD', 'postgres')
DB_ADMIN = 'postgres'

# Database configurations with generators for all 13 databases
DATABASES = {
    'genims_master_db': {
        'schema_file': 'Data Scripts/01 - Base Data/genims_schema.sql',
        'generators': [
            ('Data Scripts/01 - Base Data/generate_genims_master_data.py', 'Data Scripts/01 - Base Data/genims_master_data.json'),
        ],
        'data_file': 'Data Scripts/01 - Base Data/genims_master_data.json'
    },
    'genims_operations_db': {
        'schema_file': 'Data Scripts/02 - Machine data/genims_operational_schema.sql',
        'generators': [
            ('Data Scripts/02 - Machine data/generate_operational_data_integrated.py', 'Data Scripts/02 - Machine data/genims_operational_data.json'),
        ],
        'data_file': 'Data Scripts/02 - Machine data/genims_operational_data.json'
    },
    'genims_manufacturing_db': {
        'schema_file': 'Data Scripts/03 - MES Data/genims_mes_schema.sql',
        'generators': [
            ('Data Scripts/03 - MES Data/generate_mes_historical_data.py', 'Data Scripts/03 - MES Data/genims_mes_data.json'),
        ],
        'data_file': 'Data Scripts/03 - MES Data/genims_mes_data.json'
    },
    'genims_maintenance_db': {
        'schema_file': 'Data Scripts/06 - CMMS/genims_cmms_schema.sql',
        'generators': [
            ('Data Scripts/06 - CMMS/generate_cmms_historical_data.py', 'Data Scripts/06 - CMMS/genims_cmms_data.json'),
        ],
        'data_file': 'Data Scripts/06 - CMMS/genims_cmms_data.json'
    },
    'genims_erp_db': {
        'schema_file': 'Data Scripts/04 - ERP & MES Integration/genims_erp_schema.sql',
        'generators': [
            ('Data Scripts/04 - ERP & MES Integration/generate_erp_historical_data.py', 'Data Scripts/04 - ERP & MES Integration/genims_erp_data.json'),
        ],
        'data_file': 'Data Scripts/04 - ERP & MES Integration/genims_erp_data.json'
    },
    'genims_financial_db': {
        'schema_file': 'Data Scripts/10 - Financial Accounting & ERP <> WMS Sync/genims_financial_enhanced.sql',
        'generators': [
            ('Data Scripts/10 - Financial Accounting & ERP <> WMS Sync/generate_financial_sync_data.py', 'Data Scripts/10 - Financial Accounting & ERP <> WMS Sync/genims_financial_data.json'),
        ],
        'data_file': 'Data Scripts/10 - Financial Accounting & ERP <> WMS Sync/genims_financial_data.json'
    },
    'genims_erp_wms_sync_db': {
        'schema_file': 'Data Scripts/10 - Financial Accounting & ERP <> WMS Sync/genims_erp_wms_sync.sql',
        'generators': [
            ('Data Scripts/10 - Financial Accounting & ERP <> WMS Sync/generate_financial_sync_data.py', 'Data Scripts/10 - Financial Accounting & ERP <> WMS Sync/genims_inventory_sync_data.json'),
        ],
        'data_file': 'Data Scripts/10 - Financial Accounting & ERP <> WMS Sync/genims_inventory_sync_data.json'
    },
    'genims_wms_db': {
        'schema_file': 'Data Scripts/05 - WMS + TMS/genims_wms_schema.sql',
        'generators': [
            ('Data Scripts/05 - WMS + TMS/generate_wms_tms_historical_data.py', 'Data Scripts/05 - WMS + TMS/genims_wms_data.json'),
        ],
        'data_file': 'Data Scripts/05 - WMS + TMS/genims_wms_data.json'
    },
    'genims_tms_db': {
        'schema_file': 'Data Scripts/05 - WMS + TMS/genims_tms_schema.sql',
        'generators': [
            ('Data Scripts/05 - WMS + TMS/generate_wms_tms_historical_data.py', 'Data Scripts/05 - WMS + TMS/genims_tms_data.json'),
        ],
        'data_file': 'Data Scripts/05 - WMS + TMS/genims_tms_data.json'
    },
    'genims_crm_db': {
        'schema_file': 'Data Scripts/07 - CRM/genims_crm_schema.sql',
        'generators': [
            ('Data Scripts/07 - CRM/generate_crm_historical_data.py', 'Data Scripts/07 - CRM/genims_crm_data.json'),
        ],
        'data_file': 'Data Scripts/07 - CRM/genims_crm_data.json'
    },
    'genims_service_db': {
        'schema_file': 'Data Scripts/08 - Support & Service/genims_service_schema.sql',
        'generators': [
            ('Data Scripts/08 - Support & Service/generate_service_historical_data_updated.py', 'Data Scripts/08 - Support & Service/genims_service_data.json'),
        ],
        'data_file': 'Data Scripts/08 - Support & Service/genims_service_data.json'
    },
    'genims_hr_db': {
        'schema_file': 'Data Scripts/09 - HR-HCM/genims_hcm_schema.sql',
        'generators': [
            ('Data Scripts/09 - HR-HCM/generate_hcm_historical_data.py', 'Data Scripts/09 - HR-HCM/genims_hcm_data.json'),
        ],
        'data_file': 'Data Scripts/09 - HR-HCM/genims_hcm_data.json'
    },
    'genims_quality_db': {
        'schema_file': 'Data Scripts/12 - QMS/genims_qms.sql',
        'generators': [
            ('Data Scripts/12 - QMS/generate_qms_data_fixed.py', 'Data Scripts/12 - QMS/genims_qms_data.json'),
        ],
        'data_file': 'Data Scripts/12 - QMS/genims_qms_data.json'
    },
    'genims_supplier_db': {
        'schema_file': 'Data Scripts/11 - Supplier Portal/genims_supplier_portal.sql',
        'generators': [
            ('Data Scripts/11 - Supplier Portal/generate_supplier_portal_data.py', 'Data Scripts/11 - Supplier Portal/genims_supplier_portal_data.json'),
        ],
        'data_file': 'Data Scripts/11 - Supplier Portal/genims_supplier_portal_data.json'
    }
}

class GenIMSSetup:
    """Master setup orchestrator"""
    
    def __init__(self, root_path=None):
        self.root_path = Path(root_path or Path(__file__).parent.parent)
        self.start_time = datetime.now()
        self.stats = {
            'databases_created': 0,
            'schemas_loaded': 0,
            'data_generated': 0,
            'records_loaded': 0,
            'tables_loaded': 0,
            'errors': []
        }
    
    def log_section(self, title):
        """Log section header"""
        logger.info("\n" + "="*80)
        logger.info(f"  {title}")
        logger.info("="*80)
    
    # ========================================================================
    # STEP 1: CREATE DATABASES
    # ========================================================================
    
    def create_databases(self):
        """Create all required databases"""
        self.log_section("STEP 1: Creating Databases")
        
        try:
            conn = psycopg2.connect(
                host=DB_HOST,
                port=DB_PORT,
                user=DB_USER,
                password=DB_PASSWORD,
                dbname=DB_ADMIN
            )
            conn.autocommit = True
            cursor = conn.cursor()
            
            for db_name in DATABASES.keys():
                try:
                    cursor.execute(f"DROP DATABASE IF EXISTS {db_name};")
                    logger.info(f"  ✓ Dropped existing: {db_name}")
                except:
                    pass
                
                try:
                    cursor.execute(f"CREATE DATABASE {db_name};")
                    logger.info(f"  ✓ Created: {db_name}")
                    self.stats['databases_created'] += 1
                except psycopg2.Error as e:
                    if 'already exists' not in str(e):
                        raise
                    logger.info(f"  ✓ Already exists: {db_name}")
                    self.stats['databases_created'] += 1
            
            cursor.close()
            conn.close()
            logger.info(f"\n✓ Created {self.stats['databases_created']} databases")
            
        except Exception as e:
            logger.error(f"✗ Database creation failed: {e}")
            self.stats['errors'].append(f"Database creation: {e}")
            return False
        
        return True
    
    # ========================================================================
    # STEP 2: LOAD SCHEMAS
    # ========================================================================
    
    def load_schemas(self):
        """Load database schemas from SQL files"""
        self.log_section("STEP 2: Loading Schemas")
        
        for db_name, config in DATABASES.items():
            schema_file = config.get('schema_file')
            if not schema_file:
                logger.info(f"  ⊘ Skipping schema: {db_name} (no schema file)")
                continue
            
            schema_path = self.root_path / schema_file
            if not schema_path.exists():
                logger.warning(f"  ✗ Schema file not found: {schema_path}")
                self.stats['errors'].append(f"Schema file missing: {schema_file}")
                continue
            
            try:
                conn = psycopg2.connect(
                    host=DB_HOST,
                    port=DB_PORT,
                    user=DB_USER,
                    password=DB_PASSWORD,
                    dbname=db_name
                )
                cursor = conn.cursor()
                
                with open(schema_path, 'r') as f:
                    sql_content = f.read()
                
                # Execute schema
                cursor.execute(sql_content)
                conn.commit()
                cursor.close()
                conn.close()
                
                logger.info(f"  ✓ Loaded schema: {db_name}")
                self.stats['schemas_loaded'] += 1
                
            except Exception as e:
                logger.warning(f"  ✗ Error loading schema for {db_name}: {e}")
                self.stats['errors'].append(f"Schema load {db_name}: {str(e)[:100]}")
        
        logger.info(f"\n✓ Loaded {self.stats['schemas_loaded']} schemas")
        return True
    
    # ========================================================================
    # STEP 3: GENERATE DATA
    # ========================================================================
    
    def generate_master_data(self):
        """Generate MASTER data first (all base entities)"""
        self.log_section("STEP 3a: Generating MASTER Data (Base Entities)")
        
        gen_script = 'Data Scripts/01 - Base Data/generate_genims_master_data.py'
        gen_path = self.root_path / gen_script
        
        if not gen_path.exists():
            logger.warning(f"  ✗ Generator not found: {gen_path}")
            self.stats['errors'].append(f"Generator missing: {gen_script}")
            return False
        
        try:
            logger.info(f"  → Running master data generator: {gen_script}")
            
            result = subprocess.run(
                ['python3', str(gen_path)],
                cwd=str(self.root_path),
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if result.returncode == 0:
                output = result.stdout + result.stderr
                logger.info(f"    ✓ Master data generated successfully")
                self.stats['data_generated'] += 1
                return True
            else:
                logger.warning(f"    ✗ Master data generator failed: {result.stderr[:200]}")
                self.stats['errors'].append(f"Master generator: {result.stderr[:100]}")
                return False
        
        except subprocess.TimeoutExpired:
            logger.warning(f"    ✗ Master generator timeout: {gen_script}")
            self.stats['errors'].append(f"Master generator timeout")
            return False
        except Exception as e:
            logger.warning(f"    ✗ Master generator error: {e}")
            self.stats['errors'].append(f"Master generator: {str(e)[:100]}")
            return False
    
    def register_master_ids(self):
        """Register all master IDs with the registry"""
        self.log_section("STEP 3b: Registering Master IDs with Registry")
        
        master_file = self.root_path / 'Data Scripts/01 - Base Data/genims_master_data.json'
        
        if not master_file.exists():
            logger.error(f"  ✗ Master data file not found: {master_file}")
            self.stats['errors'].append("Master data JSON missing")
            return False
        
        try:
            with open(master_file, 'r') as f:
                master_data = json.load(f)
            
            registry = get_registry(self.root_path)
            
            # Map JSON keys to entity type names (singular) for registry
            entity_mapping = {
                'factories': 'factory',
                'production_lines': 'line',
                'machines': 'machine',
                'sensors': 'sensor',
                'employees': 'employee',
                'shifts': 'shift',
                'products': 'product',
                'customers': 'customer'
            }
            
            for json_key, entity_type in entity_mapping.items():
                if json_key in master_data:
                    records = master_data[json_key]
                    registry.register_master_ids(entity_type, records)
                    logger.info(f"  ✓ Registered {len(records)} {json_key}")
            
            registry.finalize()
            registry.save()
            logger.info(f"  ✓ Registry finalized and saved")
            return True
        
        except Exception as e:
            logger.error(f"  ✗ Registry registration failed: {e}")
            self.stats['errors'].append(f"Registry: {str(e)[:100]}")
            return False
    
    def generate_dependent_data(self):
        """Generate DEPENDENT data using registered master IDs"""
        self.log_section("STEP 3c: Generating Dependent Data (Using Master Registry)")
        
        # Skip master data generator, only run dependent ones
        for db_name, config in DATABASES.items():
            if db_name == 'genims_master_db':
                continue  # Already generated in step 3a
            
            generators = config.get('generators', [])
            
            for gen_script, expected_output in generators:
                gen_path = self.root_path / gen_script
                if not gen_path.exists():
                    logger.warning(f"  ✗ Generator not found: {gen_path}")
                    self.stats['errors'].append(f"Generator missing: {gen_script}")
                    continue
                
                try:
                    logger.info(f"  → Running generator: {gen_script}")
                    
                    result = subprocess.run(
                        ['python3', str(gen_path)],
                        cwd=str(self.root_path),
                        capture_output=True,
                        text=True,
                        timeout=300
                    )
                    
                    if result.returncode == 0:
                        output = result.stdout + result.stderr
                        if 'TOTAL' in output:
                            lines = output.split('\n')
                            for line in lines[-10:]:
                                if 'TOTAL' in line:
                                    logger.info(f"      {line.strip()}")
                        logger.info(f"    ✓ Generated data for {db_name}")
                        self.stats['data_generated'] += 1
                    else:
                        logger.warning(f"    ✗ Generator failed: {result.stderr[:200]}")
                        self.stats['errors'].append(f"Generator {gen_script}: {result.stderr[:100]}")
                
                except subprocess.TimeoutExpired:
                    logger.warning(f"    ✗ Generator timeout: {gen_script}")
                    self.stats['errors'].append(f"Generator timeout: {gen_script}")
                except Exception as e:
                    logger.warning(f"    ✗ Generator error: {e}")
                    self.stats['errors'].append(f"Generator {gen_script}: {str(e)[:100]}")
        
        logger.info(f"\n✓ Generated data for {self.stats['data_generated']} dependent databases")
        return True
    
    def validate_referential_integrity(self):
        """Validate all FK relationships before loading"""
        self.log_section("STEP 3d: Validating Referential Integrity")
        
        registry = get_registry(self.root_path)
        total_errors = 0
        
        for db_name, config in DATABASES.items():
            data_file = config.get('data_file')
            if not data_file:
                continue
            
            data_path = self.root_path / data_file
            if not data_path.exists():
                continue
            
            try:
                with open(data_path, 'r') as f:
                    data = json.load(f)
                
                errors = registry.validate_dataset(db_name, data)
                
                if errors:
                    total_errors += len(errors)
                    logger.warning(f"  ✗ {db_name}: {len(errors)} FK validation errors")
                    for err in errors[:5]:
                        logger.warning(f"      - {err}")
                    if len(errors) > 5:
                        logger.warning(f"      ... and {len(errors)-5} more")
                else:
                    logger.info(f"  ✓ {db_name}: All FKs valid")
            
            except Exception as e:
                logger.warning(f"  ✗ Validation failed for {db_name}: {str(e)[:100]}")
                self.stats['errors'].append(f"FK validation {db_name}: {str(e)[:100]}")
                total_errors += 1
        
        if total_errors == 0:
            logger.info(f"\n✓ Referential integrity validation passed")
            return True
        else:
            logger.warning(f"\n⚠ {total_errors} FK validation errors found")
            return False
    
    # ========================================================================
    # STEP 4: LOAD DATA (Optimized Batch Dump)
    # ========================================================================
    
    def format_value(self, val):
        """Format value for SQL"""
        if val is None:
            return 'NULL'
        if isinstance(val, bool):
            return 'true' if val else 'false'
        if isinstance(val, list):
            # Convert JSON array to PostgreSQL array format: {val1,val2,val3}
            escaped = [str(v).replace("'", "''") for v in val]
            return "'{" + ",".join(escaped) + "}'"
        if isinstance(val, str):
            return "'" + val.replace("'", "''") + "'"
        return str(val)
    
    def load_table(self, cursor, table_name, records):
        """Load table using multi-row INSERT (batch dump) - Ultra fast"""
        if not records:
            return 0
        
        try:
            cursor.execute(f"TRUNCATE TABLE {table_name} CASCADE")
        except:
            pass
        
        cols = list(records[0].keys())
        
        # Get DB columns including NOT NULL constraints and data types
        try:
            cursor.execute(f"""
                SELECT column_name, is_nullable, data_type, udt_name
                FROM information_schema.columns 
                WHERE table_name = %s
                ORDER BY ordinal_position
            """, (table_name,))
            # Store as dict: column_name -> (is_nullable, data_type)
            db_col_info = {row[0]: (row[1], row[2], row[3]) for row in cursor.fetchall()}
            
            # Filter to columns that:
            # 1. Exist in DB
            # 2. Have non-NULL values in records OR are nullable in DB
            safe_cols = []
            for c in cols:
                if c not in db_col_info:
                    continue
                is_nullable = db_col_info[c][0] == 'YES'
                has_value = any(rec.get(c) is not None for rec in records)
                if has_value or is_nullable:
                    safe_cols.append(c)
            
            # Also add any NOT NULL columns that are missing - we'll need to provide defaults
            for col, (is_nullable, data_type, udt_name) in db_col_info.items():
                if col not in safe_cols and col not in cols and is_nullable == 'NO':
                    # This is a NOT NULL column not in JSON - try to add if reasonable
                    if col.endswith('_id'):
                        safe_cols.append(col)
        except:
            safe_cols = cols
        
        loaded = 0
        batch_size = 5000
        
        for batch_idx in range(0, len(records), batch_size):
            batch = records[batch_idx:batch_idx+batch_size]
            
            # Build multi-row INSERT
            values_list = []
            skip_batch = False
            
            for idx, rec in enumerate(batch):
                row_vals = []
                
                for c in safe_cols:
                    val = rec.get(c)
                    
                    # Check if this column is NOT NULL and value is missing
                    if val is None and c in db_col_info:
                        is_nullable, data_type, udt_name = db_col_info[c]
                        if is_nullable == 'NO':
                            # Generate sensible default based on data type
                            if c.endswith('_id') or c == 'id':
                                val = batch_idx + idx + 1
                            # For date/timestamp columns
                            elif data_type in ['date', 'timestamp', 'timestamp without time zone', 'timestamp with time zone']:
                                val = '2025-01-01' if data_type == 'date' else '2025-01-01 00:00:00'
                            # For numeric columns
                            elif data_type in ['integer', 'bigint', 'smallint', 'numeric', 'decimal', 'real', 'double precision']:
                                val = 1 if 'frequency' in c.lower() or 'days' in c.lower() else 0
                            # For boolean columns
                            elif data_type in ['boolean']:
                                val = False
                            # For string/text columns
                            else:
                                val = f'{c}_default'
                    
                    row_vals.append(self.format_value(val))
                
                values_list.append(f"({', '.join(row_vals)})")
            
            if values_list:
                sql = f"INSERT INTO {table_name} ({', '.join(safe_cols)}) VALUES {', '.join(values_list)}"
                
                try:
                    cursor.execute(sql)
                    loaded += len(values_list)
                except Exception as e:
                    error_msg = str(e)
                    if len(error_msg) > 200:
                        error_msg = error_msg[:200]
        
        return loaded
    
    def load_data(self):
        """Load all generated data into databases (Optimized)"""
        self.log_section("STEP 4: Loading Data (Optimized Batch Dump)")
        
        for db_name, config in DATABASES.items():
            data_file = config.get('data_file')
            if not data_file:
                logger.info(f"  ⊘ Skipping: {db_name} (no data file)")
                continue
            
            data_path = self.root_path / data_file
            if not data_path.exists():
                logger.warning(f"  ⊘ File not found: {data_path}")
                continue
            
            logger.info(f"\n  Loading: {db_name}")
            logger.info(f"  File: {data_file}")
            
            try:
                # Load JSON
                with open(data_path, 'r') as f:
                    data = json.load(f)
                
                # Connect to database
                conn = psycopg2.connect(
                    host=DB_HOST,
                    port=DB_PORT,
                    user=DB_USER,
                    password=DB_PASSWORD,
                    dbname=db_name
                )
                conn.autocommit = True
                cursor = conn.cursor()
                
                # Load all tables
                db_tables = 0
                db_records = 0
                
                for table_name, records in data.items():
                    if not isinstance(records, list) or not records:
                        continue
                    
                    try:
                        loaded = self.load_table(cursor, table_name, records)
                        if loaded > 0:
                            logger.info(f"    ✓ {table_name}: {loaded} records")
                            db_tables += 1
                            db_records += loaded
                            self.stats['records_loaded'] += loaded
                        else:
                            logger.warning(f"    ✗ {table_name}: 0 records")
                    except Exception as e:
                        logger.warning(f"    ✗ {table_name}: {str(e)[:80]}")
                        self.stats['errors'].append(f"{db_name}.{table_name}")
                
                cursor.close()
                conn.close()
                
                logger.info(f"  → {db_tables} tables, {db_records} records")
                self.stats['tables_loaded'] += db_tables
                
            except Exception as e:
                logger.error(f"  ✗ Error: {str(e)[:100]}")
                self.stats['errors'].append(f"{db_name}: {str(e)[:100]}")
        
        logger.info(f"\n✓ Loaded {self.stats['tables_loaded']} tables, {self.stats['records_loaded']:,} records")
        return True
    
    # ========================================================================
    # EXECUTION
    # ========================================================================
    
    def execute(self):
        """Execute full setup pipeline"""
        logger.info("\n" + "="*80)
        logger.info("  GenIMS FULL SETUP - Database Creation to Data Loading")
        logger.info("  With Referential Integrity Validation & Registry Coordination")
        logger.info("="*80)
        logger.info(f"  Host: {DB_HOST}:{DB_PORT}")
        logger.info(f"  User: {DB_USER}")
        logger.info(f"  Root: {self.root_path}")
        
        success = True
        
        # Step 1: Create databases
        if not self.create_databases():
            success = False
        
        # Step 2: Load schemas
        if not self.load_schemas():
            success = False
        
        # Step 3a: Generate MASTER data first
        if not self.generate_master_data():
            success = False
        
        # Step 3b: Register master IDs with registry
        if not self.register_master_ids():
            success = False
        
        # Step 3c: Generate dependent data using registry
        if not self.generate_dependent_data():
            success = False
        
        # Step 3d: Validate referential integrity
        if not self.validate_referential_integrity():
            logger.warning("  ⚠ Validation warnings - continuing anyway")
        
        # Step 4: Load data
        if not self.load_data():
            success = False
        
        # Summary
        self.print_summary(success)
        return success
    
    def print_summary(self, success):
        """Print execution summary"""
        elapsed = datetime.now() - self.start_time
        
        logger.info("\n" + "="*80)
        logger.info("  EXECUTION SUMMARY")
        logger.info("="*80)
        logger.info(f"  Databases Created:     {self.stats['databases_created']}")
        logger.info(f"  Schemas Loaded:        {self.stats['schemas_loaded']}")
        logger.info(f"  Data Generators Run:   {self.stats['data_generated']}")
        logger.info(f"  Tables Loaded:         {self.stats['tables_loaded']}")
        logger.info(f"  Records Loaded:        {self.stats['records_loaded']:,}")
        logger.info(f"  Errors:                {len(self.stats['errors'])}")
        logger.info(f"  Elapsed Time:          {elapsed}")
        
        if self.stats['errors']:
            logger.info(f"\n  Errors encountered:")
            for err in self.stats['errors'][:10]:
                logger.info(f"    - {err}")
            if len(self.stats['errors']) > 10:
                logger.info(f"    ... and {len(self.stats['errors'])-10} more")
        
        status = "✓ SUCCESS" if success and not self.stats['errors'] else "⚠ COMPLETED WITH ISSUES"
        logger.info(f"\n  Status: {status}")
        logger.info("="*80 + "\n")


def main():
    """Main entry point"""
    setup = GenIMSSetup()
    success = setup.execute()
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
