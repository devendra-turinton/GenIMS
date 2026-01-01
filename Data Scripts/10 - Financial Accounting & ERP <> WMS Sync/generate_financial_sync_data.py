#!/usr/bin/env python3
"""
GenIMS Financial & Inventory Sync Data Generator
Generates chart of accounts, GL rules, and inventory sync configuration
"""

import random
import json
from datetime import datetime, timedelta
from typing import List, Dict
from pathlib import Path

class FinancialSyncDataGenerator:
    def __init__(self):
        """Initialize data generator"""
        print("Initializing Financial & Sync Data Generator...")
        
        # Data structures
        self.coa_accounts = []
        self.posting_rules = []
        self.cost_centers = []
        self.fiscal_years = []
        self.fiscal_periods = []
        self.budgets = []
        self.exchange_rates = []
        
        # Inventory Sync
        self.sync_mappings = []
        self.inventory_snapshot = []
        
        # Counters
        self.counters = {
            'account': 1000, 'rule': 1, 'cc': 1, 'fy': 1, 'period': 1,
            'budget': 1, 'rate': 1, 'mapping': 1, 'snapshot': 1
        }
    
    def generate_id(self, prefix: str, counter_key: str) -> str:
        id_val = f"{prefix}-{str(self.counters[counter_key]).zfill(6)}"
        self.counters[counter_key] += 1
        return id_val
    
    def generate_all_data(self):
        """Generate all financial and sync data"""
        print(f"\n{'='*80}")
        print(f"Generating Financial & Sync Configuration Data")
        print(f"{'='*80}\n")
        
        # Financial Master Data
        self.generate_chart_of_accounts()
        self.generate_gl_posting_rules()
        self.generate_cost_centers()
        self.generate_fiscal_calendar()
        self.generate_exchange_rates()
        self.generate_budgets()
        
        # Inventory Sync Master Data
        self.generate_sync_mappings()
        self.generate_inventory_snapshot()
        
        self._print_summary()
    
    # ========================================================================
    # CHART OF ACCOUNTS
    # ========================================================================
    
    def generate_chart_of_accounts(self):
        """Generate complete chart of accounts"""
        print("Generating chart of accounts...")
        
        # Level 1: Main Categories
        assets = self._create_account('1000', 'Assets', 'asset', None, 1, 'balance_sheet', 'debit', False)
        liabilities = self._create_account('2000', 'Liabilities', 'liability', None, 1, 'balance_sheet', 'credit', False)
        equity = self._create_account('3000', 'Equity', 'equity', None, 1, 'balance_sheet', 'credit', False)
        revenue = self._create_account('4000', 'Revenue', 'revenue', None, 1, 'income_statement', 'credit', False)
        expenses = self._create_account('5000', 'Expenses', 'expense', None, 1, 'income_statement', 'debit', False)
        
        # Level 2: Current Assets
        current_assets = self._create_account('1100', 'Current Assets', 'asset', assets['account_id'], 2, 'balance_sheet', 'debit', False)
        fixed_assets = self._create_account('1500', 'Fixed Assets', 'asset', assets['account_id'], 2, 'balance_sheet', 'debit', False)
        
        # Level 3: Cash & Bank
        self._create_account('1110', 'Cash on Hand', 'asset', current_assets['account_id'], 3, 'balance_sheet', 'debit', True)
        self._create_account('1120', 'Bank Account - Operating', 'asset', current_assets['account_id'], 3, 'balance_sheet', 'debit', True)
        self._create_account('1130', 'Bank Account - Payroll', 'asset', current_assets['account_id'], 3, 'balance_sheet', 'debit', True)
        
        # Accounts Receivable
        ar_control = self._create_account('1210', 'Accounts Receivable', 'asset', current_assets['account_id'], 3, 'balance_sheet', 'debit', True, is_control=True)
        
        # Inventory
        raw_materials = self._create_account('1310', 'Raw Materials Inventory', 'asset', current_assets['account_id'], 3, 'balance_sheet', 'debit', True)
        wip = self._create_account('1320', 'Work in Process', 'asset', current_assets['account_id'], 3, 'balance_sheet', 'debit', True)
        finished_goods = self._create_account('1330', 'Finished Goods Inventory', 'asset', current_assets['account_id'], 3, 'balance_sheet', 'debit', True)
        
        # Fixed Assets
        machinery = self._create_account('1510', 'Machinery & Equipment', 'asset', fixed_assets['account_id'], 3, 'balance_sheet', 'debit', True)
        accumulated_dep = self._create_account('1520', 'Accumulated Depreciation', 'asset', fixed_assets['account_id'], 3, 'balance_sheet', 'credit', True)
        
        # Level 2: Liabilities
        current_liabilities = self._create_account('2100', 'Current Liabilities', 'liability', liabilities['account_id'], 2, 'balance_sheet', 'credit', False)
        
        # Level 3: Accounts Payable
        ap_control = self._create_account('2110', 'Accounts Payable', 'liability', current_liabilities['account_id'], 3, 'balance_sheet', 'credit', True, is_control=True)
        self._create_account('2120', 'Accrued Payroll', 'liability', current_liabilities['account_id'], 3, 'balance_sheet', 'credit', True)
        self._create_account('2130', 'Sales Tax Payable', 'liability', current_liabilities['account_id'], 3, 'balance_sheet', 'credit', True)
        
        # Level 2: Equity
        self._create_account('3100', 'Owners Equity', 'equity', equity['account_id'], 2, 'balance_sheet', 'credit', True)
        self._create_account('3200', 'Retained Earnings', 'equity', equity['account_id'], 2, 'balance_sheet', 'credit', True)
        
        # Level 2: Revenue
        sales_revenue = self._create_account('4100', 'Sales Revenue', 'revenue', revenue['account_id'], 2, 'income_statement', 'credit', False)
        self._create_account('4110', 'Product Sales', 'revenue', sales_revenue['account_id'], 3, 'income_statement', 'credit', True)
        self._create_account('4120', 'Service Revenue', 'revenue', sales_revenue['account_id'], 3, 'income_statement', 'credit', True)
        
        # Level 2: Expenses
        cogs = self._create_account('5100', 'Cost of Goods Sold', 'expense', expenses['account_id'], 2, 'income_statement', 'debit', False)
        self._create_account('5110', 'Direct Materials', 'expense', cogs['account_id'], 3, 'income_statement', 'debit', True)
        self._create_account('5120', 'Direct Labor', 'expense', cogs['account_id'], 3, 'income_statement', 'debit', True)
        self._create_account('5130', 'Manufacturing Overhead', 'expense', cogs['account_id'], 3, 'income_statement', 'debit', True)
        
        # Operating Expenses
        opex = self._create_account('5200', 'Operating Expenses', 'expense', expenses['account_id'], 2, 'income_statement', 'debit', False)
        self._create_account('5210', 'Salaries & Wages', 'expense', opex['account_id'], 3, 'income_statement', 'debit', True)
        self._create_account('5220', 'Rent Expense', 'expense', opex['account_id'], 3, 'income_statement', 'debit', True)
        self._create_account('5230', 'Utilities', 'expense', opex['account_id'], 3, 'income_statement', 'debit', True)
        self._create_account('5240', 'Maintenance & Repairs', 'expense', opex['account_id'], 3, 'income_statement', 'debit', True)
        self._create_account('5250', 'Freight & Shipping', 'expense', opex['account_id'], 3, 'income_statement', 'debit', True)
        
        print(f"Generated {len(self.coa_accounts)} GL accounts")
    
    def _create_account(self, code, name, acc_type, parent_id, level, statement, normal_bal, allow_posting, is_control=False):
        account = {
            'account_id': self.generate_id('ACC', 'account'),
            'account_code': code,
            'account_name': name,
            'parent_account_id': parent_id,
            'account_level': level,
            'account_type': acc_type,
            'financial_statement': statement,
            'normal_balance': normal_bal,
            'is_control_account': is_control,
            'allow_posting': allow_posting,
            'is_active': True,
            'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        self.coa_accounts.append(account)
        return account
    
    # ========================================================================
    # GL POSTING RULES
    # ========================================================================
    
    def generate_gl_posting_rules(self):
        """Generate automated GL posting rules"""
        print("Generating GL posting rules...")
        
        # Get account IDs
        ar_account = next((a for a in self.coa_accounts if a['account_code'] == '1210'), None)
        sales_account = next((a for a in self.coa_accounts if a['account_code'] == '4110'), None)
        ap_account = next((a for a in self.coa_accounts if a['account_code'] == '2110'), None)
        raw_mat_account = next((a for a in self.coa_accounts if a['account_code'] == '1310'), None)
        wip_account = next((a for a in self.coa_accounts if a['account_code'] == '1320'), None)
        fg_account = next((a for a in self.coa_accounts if a['account_code'] == '1330'), None)
        cogs_account = next((a for a in self.coa_accounts if a['account_code'] == '5110'), None)
        labor_account = next((a for a in self.coa_accounts if a['account_code'] == '5120'), None)
        
        rules = [
            {
                'code': 'SALES-001',
                'name': 'Sales Order - Revenue Recognition',
                'type': 'sales_order',
                'subtype': 'invoice',
                'debit_account': ar_account['account_id'] if ar_account else None,
                'credit_account': sales_account['account_id'] if sales_account else None,
                'amount_field': 'total_amount',
                'description': 'Sales invoice posted'
            },
            {
                'code': 'PURCH-001',
                'name': 'Purchase Order - Accounts Payable',
                'type': 'purchase_order',
                'subtype': 'receipt',
                'debit_account': raw_mat_account['account_id'] if raw_mat_account else None,
                'credit_account': ap_account['account_id'] if ap_account else None,
                'amount_field': 'total_amount',
                'description': 'Purchase receipt posted'
            },
            {
                'code': 'PROD-001',
                'name': 'Production Start - WIP',
                'type': 'production_order',
                'subtype': 'started',
                'debit_account': wip_account['account_id'] if wip_account else None,
                'credit_account': raw_mat_account['account_id'] if raw_mat_account else None,
                'amount_field': 'material_cost',
                'description': 'Materials issued to production'
            },
            {
                'code': 'PROD-002',
                'name': 'Production Complete - Finished Goods',
                'type': 'production_order',
                'subtype': 'completed',
                'debit_account': fg_account['account_id'] if fg_account else None,
                'credit_account': wip_account['account_id'] if wip_account else None,
                'amount_field': 'total_cost',
                'description': 'Production completed, goods transferred'
            }
        ]
        
        for rule in rules:
            posting_rule = {
                'rule_id': self.generate_id('RULE', 'rule'),
                'rule_code': rule['code'],
                'rule_name': rule['name'],
                'transaction_type': rule['type'],
                'transaction_subtype': rule.get('subtype'),
                'debit_account_id': rule['debit_account'],
                'credit_account_id': rule['credit_account'],
                'amount_field': rule['amount_field'],
                'description_template': rule['description'],
                'is_active': True,
                'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            self.posting_rules.append(posting_rule)
        
        print(f"Generated {len(self.posting_rules)} posting rules")
    
    # ========================================================================
    # COST CENTERS
    # ========================================================================
    
    def generate_cost_centers(self):
        """Generate cost centers"""
        print("Generating cost centers...")
        
        cc_configs = [
            {'code': 'PROD-001', 'name': 'Production - Assembly', 'type': 'production'},
            {'code': 'PROD-002', 'name': 'Production - Machining', 'type': 'production'},
            {'code': 'WH-001', 'name': 'Warehouse Operations', 'type': 'warehouse'},
            {'code': 'SALES-001', 'name': 'Sales & Marketing', 'type': 'sales'},
            {'code': 'ADMIN-001', 'name': 'Administration', 'type': 'admin'},
            {'code': 'MAINT-001', 'name': 'Maintenance', 'type': 'production'}
        ]
        
        for config in cc_configs:
            cc = {
                'cost_center_id': self.generate_id('CC', 'cc'),
                'cost_center_code': config['code'],
                'cost_center_name': config['name'],
                'cost_center_type': config['type'],
                'is_active': True,
                'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            self.cost_centers.append(cc)
        
        print(f"Generated {len(self.cost_centers)} cost centers")
    
    # ========================================================================
    # FISCAL CALENDAR
    # ========================================================================
    
    def generate_fiscal_calendar(self):
        """Generate fiscal years and periods"""
        print("Generating fiscal calendar...")
        
        # Current and next year
        current_year = datetime.now().year
        
        for year in [current_year, current_year + 1]:
            fy = {
                'fiscal_year_id': self.generate_id('FY', 'fy'),
                'fiscal_year': year,
                'start_date': f"{year}-01-01",
                'end_date': f"{year}-12-31",
                'year_status': 'open' if year >= current_year else 'closed',
                'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            self.fiscal_years.append(fy)
            
            # Generate 12 periods
            for month in range(1, 13):
                period = {
                    'period_id': self.generate_id('PERIOD', 'period'),
                    'fiscal_year': year,
                    'period_number': month,
                    'period_name': f"{datetime(year, month, 1).strftime('%b')}-{year}",
                    'start_date': f"{year}-{month:02d}-01",
                    'end_date': f"{year}-{month:02d}-{self._last_day_of_month(year, month)}",
                    'period_status': 'open',
                    'allow_posting': True,
                    'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                self.fiscal_periods.append(period)
        
        print(f"Generated {len(self.fiscal_years)} fiscal years, {len(self.fiscal_periods)} periods")
    
    def _last_day_of_month(self, year, month):
        if month == 12:
            return 31
        next_month = datetime(year, month + 1, 1)
        last_day = next_month - timedelta(days=1)
        return last_day.day
    
    # ========================================================================
    # EXCHANGE RATES
    # ========================================================================
    
    def generate_exchange_rates(self):
        """Generate exchange rates"""
        print("Generating exchange rates...")
        
        # INR to major currencies for last 90 days
        currency_pairs = [
            ('INR', 'USD', 83.0),
            ('INR', 'EUR', 90.0),
            ('INR', 'GBP', 105.0),
            ('USD', 'INR', 0.012),
            ('EUR', 'INR', 0.011),
            ('GBP', 'INR', 0.0095)
        ]
        
        for days_ago in range(0, 90, 7):  # Weekly rates
            rate_date = datetime.now() - timedelta(days=days_ago)
            
            for from_curr, to_curr, base_rate in currency_pairs:
                rate = base_rate * random.uniform(0.98, 1.02)
                
                er = {
                    'rate_id': self.generate_id('RATE', 'rate'),
                    'from_currency': from_curr,
                    'to_currency': to_curr,
                    'effective_date': rate_date.strftime('%Y-%m-%d'),
                    'exchange_rate': round(rate, 6),
                    'inverse_rate': round(1/rate, 6) if rate > 0 else 0,
                    'rate_type': 'spot',
                    'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                self.exchange_rates.append(er)
        
        print(f"Generated {len(self.exchange_rates)} exchange rates")
    
    # ========================================================================
    # BUDGETS
    # ========================================================================
    
    def generate_budgets(self):
        """Generate sample budgets"""
        print("Generating budgets...")
        
        current_year = datetime.now().year
        
        budget = {
            'budget_id': self.generate_id('BUDGET', 'budget'),
            'budget_code': f'BUDGET-{current_year}',
            'budget_name': f'Operating Budget {current_year}',
            'fiscal_year': current_year,
            'budget_type': 'operating',
            'budget_version': 1,
            'is_approved': True,
            'budget_status': 'active',
            'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        self.budgets.append(budget)
        
        print(f"Generated {len(self.budgets)} budgets")
    
    # ========================================================================
    # INVENTORY SYNC
    # ========================================================================
    
    def generate_sync_mappings(self):
        """Generate ERP-WMS sync mappings"""
        print("Generating inventory sync mappings...")
        
        # Sample mappings (would be based on actual factories/warehouses)
        mappings = [
            {'erp_location': 'FACTORY-001', 'wms_warehouse': 'WH-001'},
            {'erp_location': 'FACTORY-002', 'wms_warehouse': 'WH-002'}
        ]
        
        for mapping in mappings:
            m = {
                'mapping_id': self.generate_id('MAP', 'mapping'),
                'erp_location_id': mapping['erp_location'],
                'erp_location_type': 'factory',
                'wms_warehouse_id': mapping['wms_warehouse'],
                'is_active': True,
                'sync_enabled': True,
                'sync_mode': 'real_time',
                'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            self.sync_mappings.append(m)
        
        print(f"Generated {len(self.sync_mappings)} sync mappings")
    
    def generate_inventory_snapshot(self):
        """Generate initial inventory snapshot"""
        print("Generating inventory snapshot...")
        
        # Sample data
        for i in range(50):
            snapshot = {
                'snapshot_id': self.generate_id('SNAP', 'snapshot'),
                'material_id': f'MATERIAL-{i+1:06d}',
                'location_id': random.choice(['FACTORY-001', 'FACTORY-002']),
                'erp_on_hand': round(random.uniform(100, 1000), 2),
                'erp_allocated': round(random.uniform(0, 100), 2),
                'erp_available': 0,  # Calculated
                'wms_on_hand': 0,  # Will be synced
                'sync_status': 'not_synced',
                'last_erp_update': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            snapshot['erp_available'] = snapshot['erp_on_hand'] - snapshot['erp_allocated']
            self.inventory_snapshot.append(snapshot)
        
        print(f"Generated {len(self.inventory_snapshot)} inventory snapshots")
    
    def _print_summary(self):
        print(f"\n{'='*80}")
        print(f"Financial & Sync Data Generation Complete!")
        print(f"{'='*80}")
        print(f"\nFinancial Master Data:")
        print(f"  Chart of Accounts: {len(self.coa_accounts)}")
        print(f"  GL Posting Rules: {len(self.posting_rules)}")
        print(f"  Cost Centers: {len(self.cost_centers)}")
        print(f"  Fiscal Years: {len(self.fiscal_years)}")
        print(f"  Fiscal Periods: {len(self.fiscal_periods)}")
        print(f"  Exchange Rates: {len(self.exchange_rates)}")
        print(f"  Budgets: {len(self.budgets)}")
        
        print(f"\nInventory Sync:")
        print(f"  Sync Mappings: {len(self.sync_mappings)}")
        print(f"  Inventory Snapshots: {len(self.inventory_snapshot)}")
    
    def to_json(self, output_file=None):
        """Export to JSON - TWO separate files for TWO databases"""
        if output_file is None:
            output_file = Path(__file__).parent / 'genims_financial_data.json'
        
        print(f"\nExporting financial data to separate JSON files...")
        
        # FILE 1: Financial data (for genims_financial_db)
        financial_data = {
            'chart_of_accounts': self.coa_accounts,
            'gl_posting_rules': self.posting_rules,
            'cost_centers': self.cost_centers,
            'fiscal_years': self.fiscal_years,
            'fiscal_periods': self.fiscal_periods,
            'exchange_rates': self.exchange_rates,
            'budget_headers': [b for b in self.budgets]
        }
        
        financial_file = Path(__file__).parent / 'genims_financial_data.json'
        with open(financial_file, 'w') as f:
            json.dump(financial_data, f, indent=2)
        print(f"✓ Financial data exported to {financial_file.name}")
        
        # FILE 2: Inventory sync data (for genims_erp_wms_sync_db)
        inventory_sync_data = {
            'inventory_sync_mappings': self.sync_mappings,
            'inventory_snapshot': self.inventory_snapshot
        }
        
        inventory_file = Path(__file__).parent / 'genims_inventory_sync_data.json'
        with open(inventory_file, 'w') as f:
            json.dump(inventory_sync_data, f, indent=2)
        print(f"✓ Inventory sync data exported to {inventory_file.name}")


if __name__ == "__main__":
    generator = FinancialSyncDataGenerator()
    generator.generate_all_data()
    generator.to_json()
    
    print("\n" + "="*80)
    print("Financial & Sync Data Generation Complete!")
    print("="*80)
