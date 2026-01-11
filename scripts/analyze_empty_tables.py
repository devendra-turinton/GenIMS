#!/usr/bin/env python3
"""
GenIMS Empty Tables Analysis Script
Analyzes why specific tables are empty and provides fixes
"""

import os
import json
from pathlib import Path

def analyze_empty_tables():
    """Analyze each empty table and provide root cause analysis"""
    
    print("=" * 100)
    print("🔍 GenIMS Empty Tables - Root Cause Analysis")
    print("=" * 100)
    
    empty_tables_analysis = {
        "Financial Database (genims_financial_db)": {
            "budget_lines": {
                "root_cause": "Missing Implementation",
                "analysis": "The generator creates budget_headers but does NOT create budget_lines",
                "location": "Data Scripts/10 - Financial Accounting & ERP <> WMS Sync/generate_financial_sync_data.py",
                "evidence": "Line 372-390: Only generates budget_headers, no budget_lines creation",
                "daemon_status": "financial_sync_daemon.py does not populate budget_lines",
                "fix_required": "Add budget_lines generation in generate_budgets() method"
            },
            "financial_statements": {
                "root_cause": "Design Decision - Runtime Generated",
                "analysis": "Financial statements are generated on-demand, not stored",
                "location": "Documentation indicates these are 'Generated P&L, Balance Sheet, Cash Flow'",
                "evidence": "Schema exists but no population logic in generator/daemon",
                "daemon_status": "Daemon does not populate - statements generated via queries",
                "fix_required": "Either populate with sample statements or remove from empty list (by design)"
            },
            "gl_audit_trail": {
                "root_cause": "Missing Implementation",
                "analysis": "Audit trail table exists but no trigger/daemon logic to populate",
                "location": "Schema created but no INSERT logic anywhere",
                "evidence": "Complete audit trail of all GL changes - not implemented",
                "daemon_status": "No audit trail logging in daemon",
                "fix_required": "Add audit trail triggers on GL tables or daemon audit logging"
            },
            "period_close_tasks": {
                "root_cause": "Missing Implementation", 
                "analysis": "Period close task checklist not implemented",
                "location": "Schema exists but no task generation logic",
                "evidence": "Designed for period-end procedures but not populated",
                "daemon_status": "No period close task creation in daemon",
                "fix_required": "Add period close task template generation"
            }
        },
        
        "ERP-WMS Sync Database (genims_erp_wms_sync_db)": {
            "root_cause_summary": "Integration Tables - Most are Runtime/Event-Driven",
            "tables": {
                "cycle_count_integration": {
                    "root_cause": "Event-Driven Integration",
                    "analysis": "Only populated when cycle counts are triggered",
                    "fix_required": "Add sample cycle count integrations to daemon"
                },
                "inventory_adjustments_sync": {
                    "root_cause": "Event-Driven Integration", 
                    "analysis": "Only populated when adjustments occur",
                    "fix_required": "Add sample adjustment sync records"
                },
                "inventory_allocations": {
                    "root_cause": "Missing Implementation",
                    "analysis": "Allocation tracking not implemented in daemon",
                    "fix_required": "Add allocation logic to financial_sync_daemon.py"
                },
                "inventory_reconciliation_headers": {
                    "root_cause": "Missing Implementation",
                    "analysis": "Reconciliation process not implemented",
                    "fix_required": "Add reconciliation header generation"
                },
                "inventory_reconciliation_lines": {
                    "root_cause": "Missing Implementation", 
                    "analysis": "Reconciliation details not implemented",
                    "fix_required": "Add reconciliation line generation"
                },
                "inventory_sync_errors": {
                    "root_cause": "No Errors Generated",
                    "analysis": "Error table empty because sync is working perfectly",
                    "fix_required": "Add sample error scenarios or leave empty (working as intended)"
                },
                "inventory_sync_metrics": {
                    "root_cause": "Missing Implementation",
                    "analysis": "Metrics collection not implemented",
                    "fix_required": "Add sync performance metrics collection"
                },
                "inventory_sync_queue": {
                    "root_cause": "Batch Processing",
                    "analysis": "Queue is processed immediately, no backlog",
                    "fix_required": "Add sample queued items or leave empty (good performance)"
                },
                "inventory_transaction_log": {
                    "root_cause": "Missing Implementation",
                    "analysis": "Transaction logging not implemented",
                    "fix_required": "Add inventory transaction logging to daemon"
                }
            }
        },
        
        "WMS Database (genims_wms_db)": {
            "wave_lines": {
                "root_cause": "Generator Bug - Empty Implementation",
                "analysis": "Method _generate_wave_lines() exists but returns empty list",
                "location": "Data Scripts/05 - WMS + TMS/generate_wms_tms_historical_data.py:869",
                "evidence": "JSON file shows 'wave_lines': [] - generator creates empty list",
                "daemon_status": "wms_tms_daemon.py may not create wave_lines",
                "fix_required": "Implement _generate_wave_lines() method properly"
            }
        },
        
        "HR Database (genims_hr_db)": {
            "employee_onboarding_items": {
                "root_cause": "Generator Bug - Empty Implementation", 
                "analysis": "Method _generate_employee_onboarding_items() exists but returns empty list",
                "location": "Data Scripts/09 - HR-HCM/generate_hcm_historical_data.py:1122",
                "evidence": "JSON file shows 'employee_onboarding_items': [] - generator creates empty list",
                "daemon_status": "hcm_daemon.py may not create onboarding items",
                "fix_required": "Implement _generate_employee_onboarding_items() method properly"
            }
        }
    }
    
    # Print detailed analysis
    for database, tables in empty_tables_analysis.items():
        if database == "ERP-WMS Sync Database (genims_erp_wms_sync_db)":
            print(f"\n🔴 {database}")
            print("=" * 90)
            print(f"📋 Root Cause: {tables['root_cause_summary']}")
            print("\nDetailed Analysis:")
            
            for table_name, details in tables["tables"].items():
                print(f"\n  🔸 {table_name}")
                print(f"     Root Cause: {details['root_cause']}")
                print(f"     Analysis: {details['analysis']}")
                print(f"     Fix: {details['fix_required']}")
        else:
            print(f"\n🔴 {database}")
            print("=" * 90)
            
            for table_name, details in tables.items():
                print(f"\n🔸 {table_name}")
                print(f"   Root Cause: {details['root_cause']}")
                print(f"   Analysis: {details['analysis']}")
                if 'location' in details:
                    print(f"   Location: {details['location']}")
                if 'evidence' in details:
                    print(f"   Evidence: {details['evidence']}")
                print(f"   Fix Required: {details['fix_required']}")
    
    # Summary and Recommendations
    print("\n" + "=" * 100)
    print("📋 SUMMARY & RECOMMENDATIONS")
    print("=" * 100)
    
    print("\n🎯 PRIORITY FIXES (Easy to implement):")
    print("1. 📝 Financial/budget_lines - Add budget line generation to existing budget method")
    print("2. 📝 WMS/wave_lines - Fix empty _generate_wave_lines() implementation")
    print("3. 📝 HR/employee_onboarding_items - Fix empty _generate_employee_onboarding_items() implementation")
    
    print("\n⚡ MEDIUM PRIORITY (Feature Implementation):")
    print("4. 🔧 ERP-WMS sync tables - Add sample sync scenarios to financial_sync_daemon.py")
    print("5. 🔧 Financial/gl_audit_trail - Add audit triggers or daemon audit logging")
    print("6. 🔧 Financial/period_close_tasks - Add period close task templates")
    
    print("\n✅ BY DESIGN (May not need fixes):")
    print("7. 📊 Financial/financial_statements - Runtime generated, storage not required")
    print("8. 📊 ERP-WMS sync error/queue tables - Empty = good performance")
    
    print("\n🏗️ IMPLEMENTATION STRATEGY:")
    print("Phase 1: Fix generator bugs (wave_lines, employee_onboarding_items, budget_lines)")
    print("Phase 2: Add missing daemon features (sync scenarios, audit trails)")
    print("Phase 3: Evaluate runtime vs stored approach for financial statements")
    
    print("\n" + "=" * 100)

def analyze_json_files():
    """Check JSON files for empty arrays to confirm generator issues"""
    print("\n🔍 JSON FILE VERIFICATION")
    print("=" * 80)
    
    json_files = [
        "Data Scripts/05 - WMS + TMS/genims_wms_data.json",
        "Data Scripts/09 - HR-HCM/genims_hcm_data.json",
        "Data Scripts/10 - Financial Accounting & ERP <> WMS Sync/genims_financial_data.json"
    ]
    
    base_path = Path(__file__).parent.parent
    
    for json_file in json_files:
        file_path = base_path / json_file
        if file_path.exists():
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)
                
                print(f"\n📄 {json_file}")
                
                # Check for empty arrays
                empty_arrays = []
                for key, value in data.items():
                    if isinstance(value, list) and len(value) == 0:
                        empty_arrays.append(key)
                
                if empty_arrays:
                    print(f"   🔴 Empty arrays: {', '.join(empty_arrays)}")
                else:
                    print(f"   ✅ No empty arrays found")
                    
            except Exception as e:
                print(f"   ❌ Error reading {json_file}: {e}")
        else:
            print(f"   ❌ File not found: {json_file}")

if __name__ == "__main__":
    analyze_empty_tables()
    analyze_json_files()