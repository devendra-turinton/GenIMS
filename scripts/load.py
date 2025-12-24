#!/usr/bin/env python3
"""
GenIMS PostgreSQL Data Loader - Batch Dump Version (Ultra Fast)
Uses multi-row INSERT statements for maximum speed
"""

import json
import os
import psycopg2
from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime
import sys

load_dotenv()

DB_CONFIG = {
    'host': os.getenv('POSTGRES_HOST'),
    'port': int(os.getenv('POSTGRES_PORT')),
    'user': os.getenv('POSTGRES_USERNAME'),
    'password': os.getenv('POSTGRES_PASSWORD'),
    'sslmode': 'require'
}

BASE_PATH = Path(__file__).parent.parent
LOG_FILE = BASE_PATH / 'load_progress.log'

DATABASES = {
    # Existing 10 databases (from before)
    'genims_operations_db': BASE_PATH / '02 - Machine data' / 'genims_operational_data.json',
    'genims_manufacturing_db': BASE_PATH / '03 - MES Data' / 'genims_mes_data.json',
    'genims_maintenance_db': BASE_PATH / '06 - CMMS' / 'genims_cmms_data.json',
    'genims_erp_db': BASE_PATH / '04 - ERP & MES Integration' / 'genims_erp_data.json',
    'genims_financial_db': BASE_PATH / '04 - ERP & MES Integration' / 'genims_financial_data.json',
    'genims_wms_db': BASE_PATH / '05 - WMS + TMS' / 'genims_wms_data.json',
    'genims_tms_db': BASE_PATH / '05 - WMS + TMS' / 'genims_tms_data.json',
    'genims_crm_db': BASE_PATH / '07 - CRM' / 'genims_crm_data.json',
    'genims_service_db': BASE_PATH / '08 - Support & Service' / 'genims_service_data.json',
    'genims_hr_db': BASE_PATH / '09 - HR-HCM' / 'genims_hcm_data.json',
    
    # 3 New databases
    'genims_master_db': BASE_PATH / '01 - Base Data' / 'genims_master_data.json',
    'genims_quality_db': BASE_PATH / '12 - QMS' / 'genims_qms_data.json',
    'genims_supplier_db': BASE_PATH / '11 - Supplier Portal' / 'genims_supplier_portal_data.json',
}

def log(msg, end='\n'):
    """Log to file and console with timestamp"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    msg_with_ts = f"[{timestamp}] {msg}"
    print(msg_with_ts, end=end, flush=True)
    with open(LOG_FILE, 'a') as f:
        f.write(msg_with_ts + end)

def format_value(val):
    """Format value for SQL"""
    if val is None:
        return 'NULL'
    if isinstance(val, bool):
        return 'true' if val else 'false'
    if isinstance(val, str):
        return "'" + val.replace("'", "''") + "'"
    return str(val)

class FastLoader:
    def __init__(self):
        self.total_tables = 0
        self.loaded_tables = 0
        self.total_records = 0
        
    def load_table(self, cursor, table_name, records):
        """Load table using multi-row INSERT (batch dump)"""
        if not records:
            return 0
        
        # TRUNCATE table before loading (cascade for foreign keys)
        try:
            cursor.execute(f"TRUNCATE TABLE {table_name} CASCADE")
        except:
            pass  # Table might not exist or have no cascade
        
        cols = list(records[0].keys())
        
        # Get DB columns to check for missing IDs
        cursor.execute(f"SELECT column_name FROM information_schema.columns WHERE table_name = %s", (table_name,))
        db_cols = [row[0] for row in cursor.fetchall()]
        
        # Filter to only columns that exist in database
        safe_cols = [c for c in cols if c in db_cols]
        
        # Check if table has an ID column that's missing from data
        id_col = None
        for col in db_cols:
            if col.endswith('_id') and col not in safe_cols:
                id_col = col
                break
        
        loaded = 0
        batch_size = 5000
        id_counter = 1
        
        for batch_idx in range(0, len(records), batch_size):
            batch = records[batch_idx:batch_idx+batch_size]
            
            # Add ID if missing
            if id_col:
                for i, rec in enumerate(batch):
                    rec[id_col] = id_counter + i
                id_counter += len(batch)
                if id_col not in safe_cols:
                    safe_cols.append(id_col)
            
            # Build multi-row INSERT with safe columns only
            values_list = []
            for rec in batch:
                row_vals = [format_value(rec.get(c)) for c in safe_cols]
                values_list.append(f"({', '.join(row_vals)})")
            
            sql = f"INSERT INTO {table_name} ({', '.join(safe_cols)}) VALUES {', '.join(values_list)}"
            
            try:
                cursor.execute(sql)
                loaded += len(batch)
            except Exception as e:
                error_msg = str(e)
                # Show first part of SQL for debugging
                if 'syntax error' in error_msg.lower():
                    log(f"    ! Error: {error_msg[:120]}")
                    log(f"    ! SQL: {sql[:150]}")
                else:
                    log(f"    ! Error: {error_msg[:120]}")
        
        return loaded
    
    def load_db(self, dbname, json_file):
        """Load all tables from database"""
        log(f"\n{'='*70}")
        log(f"Loading: {dbname}")
        log(f"{'='*70}")
        
        if not json_file.exists():
            log(f"  ✗ File not found")
            return 0, 0
        
        try:
            with open(json_file) as f:
                data = json.load(f)
            log(f"  ✓ Loaded JSON")
        except:
            log(f"  ✗ JSON error")
            return 0, 0
        
        try:
            cfg = DB_CONFIG.copy()
            cfg['database'] = dbname
            conn = psycopg2.connect(**cfg)
            conn.autocommit = True  # Auto-commit each statement
            cursor = conn.cursor()
            log(f"  ✓ Connected")
        except:
            log(f"  ✗ Connection failed")
            return 0, 0
        
        db_tables = 0
        db_records = 0
        
        for table_name, records in data.items():
            self.total_tables += 1
            
            if not records:
                continue
            
            log(f"  {table_name}...", end=' ')
            sys.stdout.flush()
            
            try:
                loaded = self.load_table(cursor, table_name, records)
                
                if loaded > 0:
                    log(f"✓ {loaded:,d}")
                    self.loaded_tables += 1
                    db_tables += 1
                    db_records += loaded
                    self.total_records += loaded
                else:
                    log(f"✗ 0")
            except:
                log(f"✗ Error")
        
        try:
            cursor.close()
            conn.close()
        except:
            pass
        
        log(f"  → {db_tables} tables, {db_records:,d} records")
        return db_tables, db_records
    
    def run(self):
        """Load all databases"""
        log("\n" + "=" * 80)
        log("GENIMS DATA LOADER - BATCH DUMP (Ultra Fast)")
        log("=" * 80)
        log(f"Mode: Multi-row INSERT (batch size: 5000)")
        
        for dbname, json_file in DATABASES.items():
            self.load_db(dbname, json_file)
        
        log("\n" + "=" * 80)
        log(f"COMPLETE: {self.loaded_tables} tables, {self.total_records:,d} records")
        log("=" * 80)

if __name__ == '__main__':
    with open(LOG_FILE, 'w') as f:
        f.write('')
    
    loader = FastLoader()
    loader.run()

