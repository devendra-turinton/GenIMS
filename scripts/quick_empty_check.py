#!/usr/bin/env python3
"""
GenIMS Quick Empty Tables Check
Fast analysis using pg_stat_user_tables for quick counts
"""

import os
import sys
import psycopg2
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables
env_file = os.path.join(os.path.dirname(__file__), 'config.env')
if os.path.exists(env_file):
    load_dotenv(env_file)

# Database Configuration
PG_HOST = os.getenv('POSTGRES_HOST')
PG_PORT = int(os.getenv('POSTGRES_PORT', '5432'))
PG_USER = os.getenv('POSTGRES_USER')
PG_PASSWORD = os.getenv('POSTGRES_PASSWORD')
PG_SSL_MODE = 'require'

# All databases
DATABASES = {
    'Master': os.getenv('DB_MASTER'),
    'Operations': os.getenv('DB_OPERATIONS'), 
    'MES': os.getenv('DB_MANUFACTURING'),
    'CMMS': os.getenv('DB_MAINTENANCE'),
    'QMS': os.getenv('DB_QUALITY'),
    'ERP': os.getenv('DB_ERP'),
    'Financial': os.getenv('DB_FINANCIAL'),
    'ERP-WMS': os.getenv('DB_ERP_WMS_SYNC'),
    'WMS': os.getenv('DB_WMS'),
    'TMS': os.getenv('DB_TMS'),
    'CRM': os.getenv('DB_CRM'),
    'Service': os.getenv('DB_SERVICE'),
    'HR': os.getenv('DB_HR'),
    'Supplier': os.getenv('DB_SUPPLIER')
}

def quick_analyze_database(db_name):
    """Quick analysis using pg_stat_user_tables"""
    try:
        conn = psycopg2.connect(
            host=PG_HOST, port=PG_PORT, database=db_name,
            user=PG_USER, password=PG_PASSWORD, sslmode=PG_SSL_MODE,
            connect_timeout=5
        )
        cursor = conn.cursor()
        
        # Get table stats efficiently
        cursor.execute("""
            SELECT 
                schemaname,
                relname as table_name,
                n_tup_ins as inserts,
                n_tup_upd as updates,
                n_tup_del as deletes,
                n_live_tup as live_tuples,
                n_dead_tup as dead_tuples
            FROM pg_stat_user_tables 
            ORDER BY relname
        """)
        
        stats = cursor.fetchall()
        cursor.close()
        conn.close()
        
        return stats
        
    except Exception as e:
        print(f"❌ {db_name}: {e}")
        return None

def main():
    print("=" * 100)
    print(f"🚀 GenIMS Comprehensive Database Analysis - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 100)
    
    total_databases = 0
    total_tables = 0
    empty_tables = 0
    populated_tables = 0
    total_records = 0
    all_empty_tables = []
    all_populated_tables = []
    database_stats = {}
    
    for module, db_name in DATABASES.items():
        if not db_name:
            continue
            
        print(f"\n📊 {module:<15} ({db_name})")
        print("-" * 90)
        
        stats = quick_analyze_database(db_name)
        if not stats:
            continue
            
        total_databases += 1
        db_empty = 0
        db_populated = 0
        db_total_records = 0
        db_empty_tables = []
        db_populated_tables = []
        
        for schema, table, inserts, updates, deletes, live_tuples, dead_tuples in stats:
            total_tables += 1
            total_records += live_tuples
            db_total_records += live_tuples
            
            # Check if table has any data (live tuples)
            if live_tuples == 0:
                empty_tables += 1
                db_empty += 1
                all_empty_tables.append(f"{module}.{table}")
                db_empty_tables.append(table)
                print(f"🔴 {table:<40} EMPTY")
            else:
                populated_tables += 1
                db_populated += 1
                all_populated_tables.append((f"{module}.{table}", live_tuples))
                db_populated_tables.append((table, live_tuples))
                print(f"🟢 {table:<40} {live_tuples:>15,} records")
        
        # Store database statistics
        database_stats[module] = {
            'db_name': db_name,
            'total_tables': len(stats),
            'populated_tables': db_populated,
            'empty_tables': db_empty,
            'total_records': db_total_records,
            'empty_table_list': db_empty_tables,
            'populated_table_list': db_populated_tables
        }
        
        print(f"📈 {module}: {len(stats)} tables | {db_populated} populated | {db_empty} empty | {db_total_records:,} total records")
    
    # Comprehensive Summary
    print("\n" + "=" * 100)
    print("📋 COMPREHENSIVE ANALYSIS SUMMARY")
    print("=" * 100)
    
    # Overall Statistics
    print(f"🏢 Total Databases Analyzed: {total_databases}/14")
    print(f"📊 Total Tables Found: {total_tables}")
    print(f"📈 Total Records Across All Tables: {total_records:,}")
    print(f"🟢 Populated Tables: {populated_tables}")
    print(f"🔴 Empty Tables: {empty_tables}")
    
    if total_tables > 0:
        empty_pct = (empty_tables / total_tables * 100)
        populated_pct = (populated_tables / total_tables * 100)
        print(f"📊 Empty Tables Percentage: {empty_pct:.1f}%")
        print(f"📊 Populated Tables Percentage: {populated_pct:.1f}%")
    
    # Database-wise breakdown
    print(f"\n📋 DATABASE-WISE BREAKDOWN:")
    print("-" * 100)
    print(f"{'Database':<15} | {'Tables':<7} | {'Populated':<10} | {'Empty':<6} | {'Total Records':<15}")
    print("-" * 100)
    
    for module, stats in database_stats.items():
        print(f"{module:<15} | {stats['total_tables']:>7} | {stats['populated_tables']:>10} | {stats['empty_tables']:>6} | {stats['total_records']:>15,}")
    
    # Empty tables by database
    print(f"\n🔴 EMPTY TABLES BY DATABASE:")
    print("-" * 100)
    empty_db_count = 0
    for module, stats in database_stats.items():
        if stats['empty_tables'] > 0:
            empty_db_count += 1
            print(f"\n{module} ({stats['empty_tables']} empty tables):")
            for i, table in enumerate(stats['empty_table_list'], 1):
                print(f"  {i:>2}. {table}")
    
    if empty_db_count == 0:
        print("🎉 No empty tables found in any database!")
    
    # Top 10 largest tables
    print(f"\n🏆 TOP 10 LARGEST TABLES:")
    print("-" * 100)
    sorted_tables = sorted(all_populated_tables, key=lambda x: x[1], reverse=True)[:10]
    for i, (table, count) in enumerate(sorted_tables, 1):
        print(f"{i:>2}. {table:<50} {count:>15,} records")
    
    # All empty tables list
    if empty_tables > 0:
        print(f"\n🔴 COMPLETE LIST OF EMPTY TABLES ({empty_tables} total):")
        print("-" * 100)
        for i, table in enumerate(sorted(all_empty_tables), 1):
            print(f"{i:>3}. {table}")
    
    print("\n" + "=" * 100)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())