#!/usr/bin/env python3
"""
═══════════════════════════════════════════════════════════════════════════════
GenIMS PostgreSQL Manager - Unified Database & Data Management

Comprehensive script for:
  1. Database Creation & Deletion
  2. Schema Deployment
  3. Fast Data Loading (PostgreSQL COPY command)
  4. Data Verification & Validation

Author: GenIMS Platform
Version: 2.0
═══════════════════════════════════════════════════════════════════════════════
"""

import psycopg2
import psycopg2.extensions
from psycopg2 import sql
import json
import os
import sys
import argparse
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
import traceback

# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════

# PostgreSQL Connection
DB_HOST = "insights-db.postgres.database.azure.com"
DB_PORT = 5432
DB_ADMIN_USER = "turintonadmin"
DB_ADMIN_PASSWORD = "Passw0rd123!"
DB_SSLMODE = "require"

# Base directory
BASE_DIR = Path(__file__).parent

# Database Configuration
DATABASES = {
    "genims_master_data": {
        "schema_file": "01 - Base Data/genims_schema.sql",
        "data_file": "01 - Base Data/genims_master_data.json",
        "display_name": "Master Data"
    },
    "genims_operational_data": {
        "schema_file": "02 - Machine data/genims_operational_schema.sql",
        "data_file": "02 - Machine data/genims_operational_data.json",
        "display_name": "Operations/IoT"
    },
    "genims_manufacturing": {
        "schema_file": "03 - MES Data/genims_mes_schema.sql",
        "data_file": "03 - MES Data/mes_historical_data.json",
        "display_name": "Manufacturing/MES"
    },
    "genims_erp_core": {
        "schema_file": "04 - ERP & MES Integration/genims_erp_schema.sql",
        "data_file": "04 - ERP & MES Integration/erp_historical_data.json",
        "display_name": "ERP Core"
    },
    "genims_financial_gl": {
        "schema_file": "04 - ERP & MES Integration/genims_erp_schema.sql",
        "data_file": "04 - ERP & MES Integration/erp_historical_data.json",
        "display_name": "Financial/GL"
    },
    "genims_quality": {
        "schema_file": "12 - QMS/genims_qms.sql",
        "data_file": "12 - QMS/qms_data.json",
        "display_name": "Quality/QMS"
    },
    "genims_cmms": {
        "schema_file": "06 - CMMS/genims_cmms_schema.sql",
        "data_file": "06 - CMMS/cmms_historical_data.json",
        "display_name": "Maintenance/CMMS"
    },
    "genims_warehouse": {
        "schema_file": "05 - WMS + TMS/genims_wms_schema.sql",
        "data_file": "05 - WMS + TMS/wms_historical_data.json",
        "display_name": "Warehouse/WMS"
    },
    "genims_transportation": {
        "schema_file": "05 - WMS + TMS/genims_tms_schema.sql",
        "data_file": "05 - WMS + TMS/tms_historical_data.json",
        "display_name": "Transportation/TMS"
    },
    "genims_crm": {
        "schema_file": "07 - CRM/genims_crm_schema.sql",
        "data_file": "07 - CRM/crm_historical_data.json",
        "display_name": "CRM"
    },
    "genims_service": {
        "schema_file": "08 - Support & Service/genims_service_schema.sql",
        "data_file": "08 - Support & Service/service_historical_data.json",
        "display_name": "Service/Support"
    },
    "genims_hcm": {
        "schema_file": "09 - HR-HCM/genims_hcm_schema.sql",
        "data_file": "09 - HR-HCM/hcm_historical_data.json",
        "display_name": "HR/HCM"
    },
    "genims_supplier_portal": {
        "schema_file": "11 - Supplier Portal/genims_supplier_portal.sql",
        "data_file": "11 - Supplier Portal/supplier_portal_data.json",
        "display_name": "Supplier Portal"
    }
}

# ═══════════════════════════════════════════════════════════════════════════════
# LOGGING UTILITIES
# ═══════════════════════════════════════════════════════════════════════════════

class Logger:
    """Structured logging with timestamps and levels"""
    
    LEVELS = {
        "DEBUG": "DEBUG  ",
        "INFO": "INFO   ",
        "SUCCESS": "SUCCESS",
        "WARN": "WARN   ",
        "ERROR": "ERROR  "
    }
    
    COLORS = {
        "DEBUG": "\033[36m",      # Cyan
        "INFO": "\033[0m",        # Default
        "SUCCESS": "\033[92m",    # Green
        "WARN": "\033[93m",       # Yellow
        "ERROR": "\033[91m"       # Red
    }
    
    RESET = "\033[0m"
    
    @staticmethod
    def log(level: str, message: str):
        """Print formatted log message"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        level_str = Logger.LEVELS.get(level, level)
        color = Logger.COLORS.get(level, "")
        print(f"[{timestamp}] {color}{level_str}{Logger.RESET}: {message}")
    
    @staticmethod
    def debug(message: str): Logger.log("DEBUG", message)
    @staticmethod
    def info(message: str): Logger.log("INFO", message)
    @staticmethod
    def success(message: str): Logger.log("SUCCESS", message)
    @staticmethod
    def warn(message: str): Logger.log("WARN", message)
    @staticmethod
    def error(message: str): Logger.log("ERROR", message)

# ═══════════════════════════════════════════════════════════════════════════════
# DATABASE CONNECTION UTILITIES
# ═══════════════════════════════════════════════════════════════════════════════

class DBConnection:
    """Database connection management"""
    
    @staticmethod
    def connect_admin() -> psycopg2.extensions.connection:
        """Connect to PostgreSQL admin connection (no database)"""
        try:
            conn = psycopg2.connect(
                host=DB_HOST,
                port=DB_PORT,
                database="postgres",
                user=DB_ADMIN_USER,
                password=DB_ADMIN_PASSWORD,
                sslmode=DB_SSLMODE
            )
            conn.autocommit = True
            return conn
        except Exception as e:
            Logger.error(f"Failed to connect to PostgreSQL admin: {e}")
            raise
    
    @staticmethod
    def connect_database(db_name: str) -> psycopg2.extensions.connection:
        """Connect to specific database"""
        try:
            conn = psycopg2.connect(
                host=DB_HOST,
                port=DB_PORT,
                database=db_name,
                user=DB_ADMIN_USER,
                password=DB_ADMIN_PASSWORD,
                sslmode=DB_SSLMODE
            )
            conn.autocommit = False
            return conn
        except psycopg2.Error as e:
            Logger.error(f"Failed to connect to {db_name}: {e}")
            raise

# ═══════════════════════════════════════════════════════════════════════════════
# DATABASE MANAGEMENT
# ═══════════════════════════════════════════════════════════════════════════════

class DatabaseManager:
    """Manage database creation, deletion, and schemas"""
    
    @staticmethod
    def create_database(db_name: str) -> bool:
        """Create a PostgreSQL database"""
        try:
            conn = DBConnection.connect_admin()
            with conn.cursor() as cur:
                # Check if database exists
                cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (db_name,))
                if cur.fetchone():
                    Logger.warn(f"Database '{db_name}' already exists, skipping creation")
                    return True
                
                # Create database
                cur.execute(sql.SQL("CREATE DATABASE {} ENCODING 'UTF8' LC_COLLATE 'en_US.utf8' LC_CTYPE 'en_US.utf8'").format(
                    sql.Identifier(db_name)
                ))
                Logger.success(f"Created database: {db_name}")
            conn.close()
            return True
        except Exception as e:
            Logger.error(f"Failed to create database {db_name}: {e}")
            return False
    
    @staticmethod
    def delete_database(db_name: str) -> bool:
        """Delete a PostgreSQL database"""
        try:
            conn = DBConnection.connect_admin()
            with conn.cursor() as cur:
                # Terminate connections
                cur.execute("""
                    SELECT pg_terminate_backend(pg_stat_activity.pid)
                    FROM pg_stat_activity
                    WHERE pg_stat_activity.datname = %s
                    AND pid <> pg_backend_pid()
                """, (db_name,))
                
                # Drop database
                cur.execute(sql.SQL("DROP DATABASE IF EXISTS {}").format(sql.Identifier(db_name)))
                Logger.success(f"Deleted database: {db_name}")
            conn.close()
            return True
        except Exception as e:
            Logger.error(f"Failed to delete database {db_name}: {e}")
            return False
    
    @staticmethod
    def deploy_schema(db_name: str, schema_file: str) -> bool:
        """Deploy schema to database"""
        try:
            schema_path = BASE_DIR / schema_file
            if not schema_path.exists():
                Logger.warn(f"Schema file not found: {schema_file}")
                return False
            
            # Read schema
            with open(schema_path, 'r') as f:
                schema_sql = f.read()
            
            # Deploy schema
            conn = DBConnection.connect_database(db_name)
            with conn.cursor() as cur:
                cur.execute(schema_sql)
            conn.commit()
            conn.close()
            
            Logger.success(f"Deployed schema to {db_name}")
            return True
        except Exception as e:
            Logger.error(f"Failed to deploy schema to {db_name}: {e}")
            return False
    
    @staticmethod
    def get_all_tables(db_name: str) -> List[str]:
        """Get all table names from database"""
        try:
            conn = DBConnection.connect_database(db_name)
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_type = 'BASE TABLE'
                    ORDER BY table_name
                """)
                tables = [row[0] for row in cur.fetchall()]
            conn.close()
            return tables
        except Exception as e:
            Logger.error(f"Failed to get tables from {db_name}: {e}")
            return []

# ═══════════════════════════════════════════════════════════════════════════════
# DATA OPERATIONS
# ═══════════════════════════════════════════════════════════════════════════════

class DataManager:
    """Manage data loading and validation"""
    
    @staticmethod
    def truncate_all_tables(db_name: str) -> int:
        """Truncate all tables in a database"""
        try:
            conn = DBConnection.connect_database(db_name)
            tables = DatabaseManager.get_all_tables(db_name)
            
            if not tables:
                return 0
            
            with conn.cursor() as cur:
                # Disable FK constraints
                cur.execute("ALTER TABLE IF EXISTS _any DISABLE TRIGGER ALL")
                
                # Truncate all tables
                for table in tables:
                    try:
                        cur.execute(sql.SQL("TRUNCATE TABLE {} CASCADE").format(sql.Identifier(table)))
                    except Exception as e:
                        Logger.debug(f"Truncate error for {table}: {e}")
                
                # Re-enable FK constraints
                cur.execute("ALTER TABLE IF EXISTS _any ENABLE TRIGGER ALL")
            
            conn.commit()
            conn.close()
            return len(tables)
        except Exception as e:
            Logger.error(f"Failed to truncate tables in {db_name}: {e}")
            return 0
    
    @staticmethod
    def load_data_from_json(db_name: str, data_file: str, batch_size: int = 1000) -> Tuple[int, int]:
        """
        Load data from JSON file using PostgreSQL COPY (fast method)
        Returns: (total_records_loaded, total_tables)
        """
        try:
            data_path = BASE_DIR / data_file
            if not data_path.exists():
                Logger.warn(f"Data file not found: {data_file}")
                return (0, 0)
            
            # Read JSON data
            Logger.debug(f"Reading JSON from {data_file}...")
            with open(data_path, 'r') as f:
                data = json.load(f)
            
            Logger.debug(f"Found {len(data)} tables in JSON")
            
            conn = DBConnection.connect_database(db_name)
            total_records = 0
            tables_loaded = 0
            tables_skipped = 0
            
            # Process each table in JSON
            for idx, (table_name, records) in enumerate(data.items(), 1):
                if not records:
                    Logger.debug(f"  [{idx}/{len(data)}] Skipping {table_name} (empty)")
                    tables_skipped += 1
                    continue
                
                # Normalize table name (remove _sample suffix)
                normalized_table = table_name.replace('_sample', '')
                
                try:
                    # Check if table exists
                    with conn.cursor() as cur:
                        cur.execute("""
                            SELECT 1 FROM information_schema.tables 
                            WHERE table_schema = 'public' AND table_name = %s
                        """, (normalized_table,))
                        
                        if not cur.fetchone():
                            Logger.debug(f"  [{idx}/{len(data)}] Table '{normalized_table}' not found in schema")
                            tables_skipped += 1
                            continue
                    
                    # Use COPY for fast loading
                    Logger.debug(f"  [{idx}/{len(data)}] Loading {normalized_table} ({len(records)} records)...")
                    count = DataManager._copy_load_records(
                        conn, normalized_table, records, batch_size
                    )
                    
                    if count > 0:
                        total_records += count
                        tables_loaded += 1
                        Logger.success(f"  ✓ [{idx}/{len(data)}] {normalized_table:40s} {count:8,} records")
                    else:
                        Logger.debug(f"  ✗ [{idx}/{len(data)}] {normalized_table} failed to load")
                
                except Exception as e:
                    Logger.debug(f"COPY error for {normalized_table}: {e}")
                    tables_skipped += 1
                    continue
            
            conn.commit()
            conn.close()
            
            Logger.debug(f"Load summary: {tables_loaded} loaded, {tables_skipped} skipped")
            return (total_records, tables_loaded)
        
        except Exception as e:
            Logger.error(f"Failed to load data to {db_name}: {e}")
            return (0, 0)
    
    @staticmethod
    def _copy_load_records(conn, table_name: str, records: List[Dict], 
                          batch_size: int = 1000) -> int:
        """Load records using PostgreSQL COPY command"""
        if not records:
            return 0
        
        # Get column names from first record
        columns = list(records[0].keys())
        column_str = ", ".join(columns)
        
        total_loaded = 0
        
        # Load in batches
        for batch_start in range(0, len(records), batch_size):
            batch = records[batch_start:batch_start + batch_size]
            
            # Prepare CSV data for COPY
            csv_data = []
            for record in batch:
                values = []
                for col in columns:
                    val = record.get(col)
                    # Handle NULL values
                    if val is None:
                        values.append(r'\N')
                    else:
                        # Escape special characters
                        str_val = str(val).replace('\\', '\\\\').replace('\n', '\\n').replace('\r', '\\r').replace('\t', '\\t')
                        values.append(str_val)
                csv_data.append('\t'.join(values))
            
            csv_str = '\n'.join(csv_data)
            
            try:
                with conn.cursor() as cur:
                    cur.copy_from(
                        file=__import__('io').StringIO(csv_str),
                        table=table_name,
                        columns=columns,
                        null=r'\N'
                    )
                total_loaded += len(batch)
            except Exception as e:
                Logger.debug(f"COPY batch error: {e}")
                continue
        
        return total_loaded
    
    @staticmethod
    def get_record_count(db_name: str, table_name: str) -> int:
        """Get count of records in a table"""
        try:
            conn = DBConnection.connect_database(db_name)
            with conn.cursor() as cur:
                cur.execute(sql.SQL("SELECT COUNT(*) FROM {}").format(sql.Identifier(table_name)))
                count = cur.fetchone()[0]
            conn.close()
            return count
        except:
            return 0

# ═══════════════════════════════════════════════════════════════════════════════
# VERIFICATION & REPORTING
# ═══════════════════════════════════════════════════════════════════════════════

class DataVerifier:
    """Verify and report on database data"""
    
    @staticmethod
    def verify_all_databases() -> Dict[str, Dict]:
        """Verify all databases and return summary"""
        summary = {}
        
        for db_name, config in DATABASES.items():
            display_name = config.get('display_name', db_name)
            
            try:
                tables = DatabaseManager.get_all_tables(db_name)
                total_records = 0
                table_data = {}
                
                for table in tables:
                    count = DataManager.get_record_count(db_name, table)
                    if count > 0:
                        table_data[table] = count
                        total_records += count
                
                summary[db_name] = {
                    'display_name': display_name,
                    'status': 'success',
                    'tables': table_data,
                    'total_records': total_records,
                    'table_count': len(tables)
                }
            except Exception as e:
                summary[db_name] = {
                    'display_name': display_name,
                    'status': 'error',
                    'error': str(e),
                    'total_records': 0,
                    'table_count': 0
                }
        
        return summary
    
    @staticmethod
    def print_verification_report(summary: Dict):
        """Print verification report"""
        Logger.info("")
        Logger.info("╔═════════════════════════════════════════════════════════════════════════════════╗")
        Logger.info("║ DATABASE VERIFICATION REPORT                                                    ║")
        Logger.info("╚═════════════════════════════════════════════════════════════════════════════════╝")
        Logger.info("")
        
        grand_total = 0
        fully_loaded = 0
        empty_dbs = 0
        
        for db_name, config in DATABASES.items():
            result = summary[db_name]
            display_name = config['display_name']
            total = result['total_records']
            
            grand_total += total
            
            if result['status'] == 'error':
                status_symbol = "✗"
                status_text = f"ERROR: {result['error']}"
            elif total == 0:
                status_symbol = "⚠"
                status_text = "EMPTY - No data"
                empty_dbs += 1
            else:
                status_symbol = "✓"
                status_text = f"{total:,} records in {result['table_count']} tables"
                fully_loaded += 1
            
            print(f"  {status_symbol} {display_name:40s} {status_text}")
        
        Logger.info("")
        Logger.success(f"Total records across all databases: {grand_total:,}")
        Logger.success(f"Databases with data: {fully_loaded}/13")
        if empty_dbs > 0:
            Logger.warn(f"Empty databases: {empty_dbs}/13")
        Logger.info("")

# ═══════════════════════════════════════════════════════════════════════════════
# ORCHESTRATION
# ═══════════════════════════════════════════════════════════════════════════════

class GenIMSOrchestrator:
    """Orchestrate all database and data operations"""
    
    @staticmethod
    def setup_all_databases(verbose: bool = False) -> bool:
        """Setup all databases: create + deploy schemas"""
        Logger.info("╔═════════════════════════════════════════════════════════════════════════════════╗")
        Logger.info("║ PHASE 1: DATABASE CREATION & SCHEMA DEPLOYMENT                                 ║")
        Logger.info("╚═════════════════════════════════════════════════════════════════════════════════╝")
        Logger.info("")
        
        success_count = 0
        
        for i, (db_name, config) in enumerate(DATABASES.items(), 1):
            display_name = config['display_name']
            Logger.info(f"[{i}/13] Setting up {display_name}...")
            
            # Create database
            if not DatabaseManager.create_database(db_name):
                continue
            
            # Deploy schema
            if not DatabaseManager.deploy_schema(db_name, config['schema_file']):
                continue
            
            Logger.success(f"  ✓ {display_name} setup complete")
            success_count += 1
            Logger.info("")
        
        Logger.success(f"✓ Phase 1 Complete: {success_count}/13 databases ready")
        Logger.info("")
        return success_count == 13
    
    @staticmethod
    def clean_all_databases(verbose: bool = False) -> int:
        """Truncate all tables in all databases"""
        Logger.info("╔═════════════════════════════════════════════════════════════════════════════════╗")
        Logger.info("║ PHASE 1: TRUNCATE ALL TABLES IN ALL DATABASES                                  ║")
        Logger.info("╚═════════════════════════════════════════════════════════════════════════════════╝")
        Logger.info("")
        
        total_cleaned = 0
        
        for i, (db_name, config) in enumerate(DATABASES.items(), 1):
            display_name = config['display_name']
            Logger.info(f"[{i}/13] Cleaning {display_name}...")
            
            count = DataManager.truncate_all_tables(db_name)
            if count > 0:
                Logger.success(f"  ✓ Truncated {count} tables")
                total_cleaned += count
            
            Logger.info("")
        
        Logger.success(f"✓ Phase 1 Complete: Cleaned all tables")
        Logger.info("")
        return total_cleaned
    
    @staticmethod
    def load_all_data(verbose: bool = False) -> Dict:
        """Load data into all databases"""
        Logger.info("╔═════════════════════════════════════════════════════════════════════════════════╗")
        Logger.info("║ PHASE 2: LOAD ALL DATA                                                         ║")
        Logger.info("╚═════════════════════════════════════════════════════════════════════════════════╝")
        Logger.info("")
        
        phase_start = time.time()
        results = {}
        grand_total_records = 0
        grand_total_tables = 0
        
        for i, (db_name, config) in enumerate(DATABASES.items(), 1):
            display_name = config['display_name']
            db_start = time.time()
            Logger.info(f"[{i}/13] Loading {display_name}...")
            Logger.info("")
            
            records, tables = DataManager.load_data_from_json(db_name, config['data_file'])
            
            db_elapsed = time.time() - db_start
            
            if records == 0:
                Logger.warn(f"  ✗ No data loaded ({db_elapsed:.1f}s)")
            else:
                Logger.success(f"  ═ {display_name}: {records:,} records in {tables} tables ({db_elapsed:.1f}s)")
                grand_total_records += records
                grand_total_tables += tables
            
            results[db_name] = {'records': records, 'tables': tables}
            Logger.info("")
        
        phase_elapsed = time.time() - phase_start
        Logger.success(f"✓ Phase 2 Complete: {grand_total_records:,} records loaded in {grand_total_tables} tables")
        Logger.success(f"  Total load time: {phase_elapsed:.1f} seconds")
        Logger.info("")
        return results
    
    @staticmethod
    def full_pipeline(verbose: bool = False):
        """Execute complete pipeline: delete -> create -> load -> verify"""
        start_time = time.time()
        
        Logger.info("═" * 88)
        Logger.info("GenIMS POSTGRES MANAGER - COMPLETE PIPELINE")
        Logger.info("═" * 88)
        Logger.info("")
        
        # Phase 1: Delete existing databases
        Logger.info("Phase 1: Deleting existing databases...")
        Logger.info("")
        for db_name in DATABASES.keys():
            DatabaseManager.delete_database(db_name)
        Logger.info("")
        
        # Phase 2: Create databases and deploy schemas
        Logger.info("Phase 2: Creating databases and deploying schemas...")
        GenIMSOrchestrator.setup_all_databases(verbose)
        
        # Phase 3: Load data
        Logger.info("Phase 3: Loading all data...")
        load_results = GenIMSOrchestrator.load_all_data(verbose)
        
        # Phase 4: Verify
        Logger.info("Phase 4: Verifying data...")
        summary = DataVerifier.verify_all_databases()
        DataVerifier.print_verification_report(summary)
        
        elapsed = time.time() - start_time
        Logger.success(f"✓✓✓ PIPELINE COMPLETE - Total time: {elapsed:.1f} seconds ✓✓✓")
        Logger.info("")

# ═══════════════════════════════════════════════════════════════════════════════
# CLI INTERFACE
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    """Main CLI interface"""
    parser = argparse.ArgumentParser(
        description="GenIMS PostgreSQL Manager - Complete Pipeline (Delete → Create → Load → Verify)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run full pipeline
  python3 genims_postgres_manager.py
  
  # Run with verbose logging
  python3 genims_postgres_manager.py --verbose
        """
    )
    
    parser.add_argument('--verbose', action='store_true', help='Verbose output')
    
    args = parser.parse_args()
    
    try:
        GenIMSOrchestrator.full_pipeline(verbose=args.verbose)
    
    except KeyboardInterrupt:
        Logger.warn("\nOperation cancelled by user")
        sys.exit(1)
    except Exception as e:
        Logger.error(f"Fatal error: {e}")
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
