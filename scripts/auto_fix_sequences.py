#!/usr/bin/env python3
"""
GenIMS Auto-Sequence Fix - Generic Pipeline
Automatically detects and fixes ALL out-of-sync sequences across ALL databases
Run this before starting daemons or as a scheduled task
"""

import os
import psycopg2
from dotenv import load_dotenv
from datetime import datetime
import sys

# Load environment
env_file = os.path.join(os.path.dirname(__file__), 'config.env')
load_dotenv(env_file)

# PostgreSQL configuration
PG_HOST = os.getenv('POSTGRES_HOST', 'localhost')
PG_PORT = int(os.getenv('POSTGRES_PORT', '5432'))
PG_USER = os.getenv('POSTGRES_USER', 'postgres')
PG_PASSWORD = os.getenv('POSTGRES_PASSWORD', '')
PG_SSL_MODE = os.getenv('PG_SSL_MODE', 'require')

# All GenIMS databases
DATABASES = [
    'genims_operations_db',
    'genims_manufacturing_db',
    'genims_erp_db',
    'genims_financial_db',
    'genims_wms_db',
    'genims_tms_db',
    'genims_maintenance_db',
    'genims_crm_db',
    'genims_service_db',
    'genims_hr_db',
    'genims_supplier_db',
    'genims_quality_db',
    'genims_erp_wms_sync_db'
]

def fix_database_sequences(db_name, auto_fix=True):
    """
    Check and optionally fix all sequences in a database
    Returns: (total_checked, total_fixed, errors, connection_success)
    """
    try:
        conn = psycopg2.connect(
            host=PG_HOST,
            port=PG_PORT,
            database=db_name,
            user=PG_USER,
            password=PG_PASSWORD,
            sslmode=PG_SSL_MODE,
            connect_timeout=10
        )
        conn.autocommit = True
        cursor = conn.cursor()
        
        # Find all sequences with their tables and columns
        cursor.execute("""
            SELECT 
                s.sequence_name,
                t.table_name,
                c.column_name
            FROM information_schema.sequences s
            LEFT JOIN information_schema.columns c 
                ON c.column_default LIKE '%' || s.sequence_name || '%'
                AND c.table_schema = 'public'
            LEFT JOIN information_schema.tables t
                ON t.table_name = c.table_name
                AND t.table_schema = 'public'
            WHERE s.sequence_schema = 'public'
            ORDER BY s.sequence_name
        """)
        
        sequences = cursor.fetchall()
        checked = 0
        fixed = 0
        errors = []
        
        for seq_name, table_name, column_name in sequences:
            if not table_name or not column_name:
                continue
            
            checked += 1
            
            try:
                # Get current sequence value
                cursor.execute(f"SELECT last_value FROM {seq_name}")
                seq_value = cursor.fetchone()[0]
                
                # Get max value from table
                cursor.execute(f"SELECT COALESCE(MAX({column_name}), 0) FROM {table_name}")
                max_value = cursor.fetchone()[0]
                
                # Check if out of sync
                if seq_value <= max_value:
                    new_value = max_value + 1
                    
                    if auto_fix:
                        # Fix the sequence
                        cursor.execute(f"SELECT setval('{seq_name}', {new_value}, false)")
                        print(f"   ✓ Fixed {table_name}.{column_name}: {seq_value} → {new_value}")
                        fixed += 1
                    else:
                        print(f"   ⚠️  {table_name}.{column_name}: seq={seq_value}, max={max_value} (would fix to {new_value})")
                
            except Exception as e:
                error_msg = f"Error fixing {seq_name}: {e}"
                errors.append(error_msg)
                print(f"   ❌ {error_msg}")
        
        cursor.close()
        conn.close()
        
        return checked, fixed, errors, True
        
    except Exception as e:
        return 0, 0, [str(e)], False


def main():
    """Main execution"""
    auto_fix = '--check-only' not in sys.argv
    
    print("=" * 100)
    print(f"GenIMS Auto-Sequence Fix - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Mode: {'AUTO-FIX' if auto_fix else 'CHECK ONLY'}")
    print("=" * 100)
    print()
    
    total_checked = 0
    total_fixed = 0
    all_errors = []
    
    for db_name in DATABASES:
        print(f"📊 {db_name}")
        checked, fixed, errors, connected = fix_database_sequences(db_name, auto_fix)
        
        if not connected:
            print(f"   ⏭️  Skipped (connection failed: {errors[0] if errors else 'unknown error'})")
        elif checked == 0:
            print("   ⏭️  Skipped (no sequences found - empty database)")
        elif fixed == 0 and not errors:
            print("   ✅ All sequences synchronized")
        elif fixed > 0:
            print(f"   ✓ Fixed {fixed} sequence(s)")
        
        total_checked += checked
        total_fixed += fixed
        all_errors.extend(errors)
        print()
    
    # Summary
    print("=" * 100)
    print("SUMMARY")
    print("=" * 100)
    print(f"Sequences Checked: {total_checked}")
    print(f"Sequences Fixed: {total_fixed}")
    print(f"Errors: {len(all_errors)}")
    
    if auto_fix:
        if total_fixed > 0:
            print()
            print("✅ All out-of-sync sequences have been fixed!")
            print("   Daemons can now insert records without duplicate key errors.")
        else:
            print()
            print("✅ All sequences were already synchronized!")
    else:
        print()
        print("ℹ️  Run without --check-only to apply fixes automatically")
    
    print("=" * 100)
    
    return 0 if len(all_errors) == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
