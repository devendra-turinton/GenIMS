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
import sys
from concurrent.futures import ThreadPoolExecutor
import threading
from multiprocessing import cpu_count

# Add scripts to path for helper access
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

try:
    from generator_helper import get_helper
    HELPER_AVAILABLE = True
except ImportError:
    HELPER_AVAILABLE = False
    print("Warning: Registry helper not available")

try:
    from time_coordinator import TimeCoordinator
except ImportError:
    # Create a simple fallback
    class TimeCoordinator:
        def get_current_time(self):
            return datetime.now()

class FinancialSyncDataGenerator:
    def __init__(self):
        """Initialize data generator with registry helper"""
        print("Initializing Financial & Sync Data Generator...")
        
        # Load registry helper for FK validation
        if HELPER_AVAILABLE:
            try:
                self.helper = get_helper()
                self.registry = self.helper.registry
                print(f"Registry helper loaded with {len(self.helper.registry.registered_ids)} ID types")
            except Exception as e:
                print(f"Warning: Registry helper initialization failed: {e}")
                self.helper = None
                self.registry = None
        else:
            print("Warning: Registry helper not available")
            self.helper = None
            self.registry = None
        
        # Data structures
        self.coa_accounts = []
        self.posting_rules = []
        self.cost_centers = []
        self.fiscal_years = []
        self.fiscal_periods = []
        self.budgets = []
        self.budget_lines = []
        self.exchange_rates = []
        self.financial_statements = []
        self.gl_audit_trail = []
        self.period_close_tasks = []
        
        # Inventory Sync
        self.sync_mappings = []
        self.inventory_snapshot = []
        self.cycle_count_integration = []
        self.inventory_adjustments_sync = []
        self.inventory_allocations = []
        self.inventory_reconciliation_headers = []
        self.inventory_reconciliation_lines = []
        self.inventory_sync_errors = []
        self.inventory_sync_metrics = []
        self.inventory_sync_queue = []
        self.inventory_transaction_log = []
        
        # Counters
        self.counters = {
            'account': 1000, 'rule': 1, 'cc': 1, 'fy': 1, 'period': 1,
            'budget': 1, 'rate': 1, 'mapping': 1, 'snapshot': 1,
            'statement': 1, 'audit': 1, 'task': 1, 'cycle': 1,
            'adjustment': 1, 'allocation': 1, 'recon_header': 1, 
            'recon_line': 1, 'sync_error': 1, 'sync_metric': 1, 
            'sync_queue': 1, 'transaction': 1
        }
        
        # ✅ ULTRA-FAST PARALLEL PROCESSING CONFIGURATION
        self.worker_count = min(8, cpu_count() - 2 if cpu_count() > 2 else 1)
        self.data_lock = threading.Lock()
        self.batch_size = 150000  # Large batch for high performance
        self.time_coord = TimeCoordinator()
        
        print(f"🚀 ULTRA-FAST FINANCIAL PARALLEL MODE: {self.worker_count} workers, batch_size={self.batch_size:,}")
        print(f"   CPU cores available: {cpu_count()}, Using {self.worker_count} for generation")
    
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
        self.generate_financial_statements()
        self.generate_gl_audit_trail()
        self.generate_period_close_tasks()
        
        # Inventory Sync Master Data - PARALLEL PROCESSING
        self.generate_inventory_sync_parallel()
        
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
        """Generate cost centers for 4 factories"""
        print("Generating cost centers for 4 factories...")
        
        # Cost centers for each factory (4 factories)
        factories = ['FAC01', 'FAC02', 'FAC03', 'FAC04']
        cc_types = [
            {'code': 'PROD-ASSY', 'name': 'Production - Assembly', 'type': 'production'},
            {'code': 'PROD-MACH', 'name': 'Production - Machining', 'type': 'production'},
            {'code': 'PROD-PAINT', 'name': 'Production - Painting', 'type': 'production'},
            {'code': 'PROD-QC', 'name': 'Quality Control', 'type': 'production'},
            {'code': 'WH-RECV', 'name': 'Warehouse - Receiving', 'type': 'warehouse'},
            {'code': 'WH-SHIP', 'name': 'Warehouse - Shipping', 'type': 'warehouse'},
            {'code': 'MAINT', 'name': 'Maintenance', 'type': 'production'},
            {'code': 'ENG', 'name': 'Engineering', 'type': 'engineering'},
            {'code': 'ADMIN', 'name': 'Administration', 'type': 'admin'}
        ]
        
        # Generate cost centers for each factory
        for factory in factories:
            for cc_type in cc_types:
                cc = {
                    'cost_center_id': self.generate_id('CC', 'cc'),
                    'cost_center_code': f"{factory}-{cc_type['code']}",
                    'cost_center_name': f"{factory} - {cc_type['name']}",
                    'cost_center_type': cc_type['type'],
                    'factory_code': factory,
                    'is_active': True,
                    'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                self.cost_centers.append(cc)
        
        # Add corporate cost centers
        corporate_centers = [
            {'code': 'CORP-SALES', 'name': 'Corporate Sales & Marketing', 'type': 'sales'},
            {'code': 'CORP-FIN', 'name': 'Corporate Finance', 'type': 'finance'},
            {'code': 'CORP-HR', 'name': 'Corporate HR', 'type': 'admin'},
            {'code': 'CORP-IT', 'name': 'Corporate IT', 'type': 'admin'}
        ]
        
        for cc_type in corporate_centers:
            cc = {
                'cost_center_id': self.generate_id('CC', 'cc'),
                'cost_center_code': cc_type['code'],
                'cost_center_name': cc_type['name'],
                'cost_center_type': cc_type['type'],
                'factory_code': 'CORP',
                'is_active': True,
                'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            self.cost_centers.append(cc)
        
        print(f"Generated {len(self.cost_centers)} cost centers across 4 factories")
    
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
        """Generate sample budgets and budget lines"""
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
        
        # Generate budget lines for each account and period
        print("Generating budget lines...")
        budget_id = budget['budget_id']
        
        # Get revenue and expense accounts for budgeting
        revenue_accounts = [acc for acc in self.coa_accounts if acc['account_type'] == 'revenue']
        expense_accounts = [acc for acc in self.coa_accounts if acc['account_type'] == 'expense']
        
        for month in range(1, 13):  # 12 months
            # Revenue budget lines
            for acc in revenue_accounts:
                budget_line = {
                    'budget_line_id': self.generate_id('BUDGETLINE', 'budget'),
                    'budget_id': budget_id,
                    'account_id': acc['account_id'],
                    'cost_center_id': random.choice([cc['cost_center_id'] for cc in self.cost_centers]) if self.cost_centers else None,
                    'fiscal_year': current_year,
                    'fiscal_period': month,
                    'budget_amount': round(random.uniform(50000, 200000), 2),  # Revenue budget
                    'revised_amount': None,
                    'budget_currency': 'INR',
                    'budget_type': 'revenue',
                    'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                self.budget_lines.append(budget_line)
            
            # Expense budget lines  
            for acc in expense_accounts:
                budget_line = {
                    'budget_line_id': self.generate_id('BUDGETLINE', 'budget'),
                    'budget_id': budget_id,
                    'account_id': acc['account_id'],
                    'cost_center_id': random.choice([cc['cost_center_id'] for cc in self.cost_centers]) if self.cost_centers else None,
                    'fiscal_year': current_year,
                    'fiscal_period': month,
                    'budget_amount': round(random.uniform(10000, 80000), 2),  # Expense budget
                    'revised_amount': None,
                    'budget_currency': 'INR',
                    'budget_type': 'expense',
                    'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                self.budget_lines.append(budget_line)
        
        print(f"Generated {len(self.budgets)} budgets")
        print(f"Generated {len(self.budget_lines)} budget lines")
    
    def generate_financial_statements(self):
        """Generate sample financial statements"""
        print("Generating financial statements...")
        
        statement_types = ['profit_loss', 'balance_sheet', 'cash_flow']
        
        for fiscal_year in [2025, 2026]:
            for quarter in range(1, 5):
                for stmt_type in statement_types:
                    # Calculate date range for quarter
                    start_month = (quarter - 1) * 3 + 1
                    end_month = quarter * 3
                    start_date = f"{fiscal_year}-{start_month:02d}-01"
                    end_date = f"{fiscal_year}-{end_month:02d}-{31 if end_month in [1,3,5,7,8,10,12] else 30 if end_month != 2 else 28}"
                    
                    statement = {
                        'statement_id': self.generate_id('STMT', 'statement'),
                        'statement_type': stmt_type,
                        'fiscal_year': fiscal_year,
                        'fiscal_period': quarter,
                        'start_date': start_date,
                        'end_date': end_date,
                        'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        'generated_by': 'SYS-GENIMS-001',
                        'statement_status': 'finalized',
                        'statement_data': self._generate_statement_data(stmt_type),
                        'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    }
                    self.financial_statements.append(statement)
        
        print(f"Generated {len(self.financial_statements)} financial statements")
    
    def _generate_statement_data(self, stmt_type):
        """Generate sample statement data based on type (returns JSON string)"""
        if stmt_type == 'profit_loss':
            data = {
                'revenue': round(random.uniform(5000000, 10000000), 2),
                'cost_of_goods_sold': round(random.uniform(2000000, 4000000), 2),
                'gross_profit': round(random.uniform(2000000, 6000000), 2),
                'operating_expenses': round(random.uniform(1000000, 3000000), 2),
                'net_income': round(random.uniform(500000, 2500000), 2)
            }
        elif stmt_type == 'balance_sheet':
            data = {
                'total_assets': round(random.uniform(10000000, 50000000), 2),
                'current_assets': round(random.uniform(3000000, 15000000), 2),
                'fixed_assets': round(random.uniform(7000000, 35000000), 2),
                'total_liabilities': round(random.uniform(5000000, 25000000), 2),
                'current_liabilities': round(random.uniform(1000000, 5000000), 2),
                'equity': round(random.uniform(5000000, 25000000), 2)
            }
        else:  # cash_flow
            data = {
                'operating_cash_flow': round(random.uniform(1000000, 5000000), 2),
                'investing_cash_flow': round(random.uniform(-2000000, -500000), 2),
                'financing_cash_flow': round(random.uniform(-1000000, 1000000), 2),
                'net_cash_flow': round(random.uniform(-500000, 3000000), 2),
                'beginning_cash': round(random.uniform(500000, 2000000), 2),
                'ending_cash': round(random.uniform(1000000, 5000000), 2)
            }
        # Convert Python dict to proper JSON string with double quotes
        return json.dumps(data)
    
    def generate_gl_audit_trail(self):
        """Generate GL audit trail records"""
        print("Generating GL audit trail...")
        
        actions = ['insert', 'update', 'delete', 'post', 'reverse']
        tables = ['gl_journal_entries', 'gl_journal_lines', 'chart_of_accounts', 'budget_headers', 'budget_lines']
        users = ['USR-001', 'USR-002', 'USR-003', 'USR-004', 'USR-005']
        
        # Generate audit records for the last 30 days
        base_date = datetime.now()
        
        for i in range(250):  # Generate 250 audit trail entries
            action_date = base_date - timedelta(days=random.randint(0, 30))
            
            audit_entry = {
                'audit_id': self.generate_id('AUDIT', 'audit'),
                'table_name': random.choice(tables),
                'record_id': f"REC-{random.randint(100000, 999999)}",
                'action_type': random.choice(actions),
                'user_id': random.choice(users),
                'action_timestamp': action_date.strftime('%Y-%m-%d %H:%M:%S'),
                'old_values': self._generate_audit_values(),
                'new_values': self._generate_audit_values(),
                'session_id': f"SESS-{random.randint(100000, 999999)}",
                'ip_address': f"{random.randint(192,192)}.{random.randint(168,168)}.{random.randint(1,10)}.{random.randint(1,254)}",
                'application_name': 'GenIMS',
                'created_at': action_date.strftime('%Y-%m-%d %H:%M:%S')
            }
            self.gl_audit_trail.append(audit_entry)
        
        print(f"Generated {len(self.gl_audit_trail)} audit trail entries")
    
    def _generate_audit_values(self):
        """Generate sample audit trail values (returns JSON string)"""
        data = {
            'amount': round(random.uniform(1000, 100000), 2),
            'account_code': f"{random.randint(1000, 9999)}",
            'description': f"GL Entry {random.randint(1000, 9999)}",
            'status': random.choice(['draft', 'posted', 'reversed'])
        }
        # Convert Python dict to proper JSON string with double quotes
        return json.dumps(data)
    
    def generate_period_close_tasks(self):
        """Generate period close task templates"""
        print("Generating period close tasks...")
        
        task_templates = [
            {'name': 'Verify Bank Reconciliations', 'category': 'bank', 'sequence': 1, 'required': True},
            {'name': 'Review AR Aging Reports', 'category': 'receivables', 'sequence': 2, 'required': True},
            {'name': 'Process Depreciation Calculations', 'category': 'fixed_assets', 'sequence': 3, 'required': True},
            {'name': 'Accrue Payroll Expenses', 'category': 'payroll', 'sequence': 4, 'required': True},
            {'name': 'Review Inventory Valuations', 'category': 'inventory', 'sequence': 5, 'required': True},
            {'name': 'Post Month-End Journal Entries', 'category': 'journal', 'sequence': 6, 'required': True},
            {'name': 'Generate Financial Reports', 'category': 'reporting', 'sequence': 7, 'required': True},
            {'name': 'Review and Approve Statements', 'category': 'approval', 'sequence': 8, 'required': True},
            {'name': 'Archive Period Documents', 'category': 'archive', 'sequence': 9, 'required': False},
            {'name': 'Update Budget vs Actual Analysis', 'category': 'analysis', 'sequence': 10, 'required': False}
        ]
        
        # Create tasks for last 6 months
        base_date = datetime.now()
        for month_offset in range(6):
            period_date = base_date - timedelta(days=month_offset * 30)
            period_name = period_date.strftime('%Y-%m')
            fiscal_year = period_date.year
            fiscal_period = period_date.month
            
            for template in task_templates:
                task = {
                    'task_id': self.generate_id('TASK', 'task'),
                    'fiscal_year': fiscal_year,
                    'fiscal_period': fiscal_period,
                    'task_sequence': template['sequence'],
                    'task_name': template['name'],
                    'task_description': f"{template['name']} for period {period_name}",
                    'task_status': random.choice(['completed', 'in_progress', 'pending']),
                    'started_at': (period_date + timedelta(days=1)).strftime('%Y-%m-%d %H:%M:%S') if random.choice([True, False]) else None,
                    'completed_at': (period_date + timedelta(days=random.randint(1, 7))).strftime('%Y-%m-%d %H:%M:%S') if random.choice([True, False, True]) else None,
                    'completed_by': f"USR-{random.randint(1, 5):03d}" if random.choice([True, False]) else None,
                    'result_message': f"Task completed successfully for {period_name}" if random.choice([True, False]) else None,
                    'created_at': period_date.strftime('%Y-%m-%d %H:%M:%S')
                }
                self.period_close_tasks.append(task)
        
        print(f"Generated {len(self.period_close_tasks)} period close tasks")
    
    # ========================================================================
    # INVENTORY SYNC
    # ========================================================================
    
    def generate_sync_mappings(self):
        """Generate ERP-WMS sync mappings"""
        print("Generating inventory sync mappings...")
        
        # Get validated factory IDs if registry available
        if hasattr(self, 'helper') and self.helper and hasattr(self.helper, 'get_valid_factory_ids'):
            try:
                valid_factory_ids = list(self.helper.get_valid_factory_ids())
                if not valid_factory_ids:
                    valid_factory_ids = ['FAC-000001', 'FAC-000002']
            except Exception as e:
                print(f"Warning: Factory validation failed: {e}")
                valid_factory_ids = ['FAC-000001', 'FAC-000002']
        else:
            valid_factory_ids = ['FAC-000001', 'FAC-000002']
        
        # Create sync mappings for each factory
        for idx, factory_id in enumerate(valid_factory_ids):
            m = {
                'mapping_id': self.generate_id('MAP', 'mapping'),
                'erp_location_id': factory_id,
                'erp_location_type': 'factory',
                'wms_warehouse_id': f"WMS-{idx+1:03d}",
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
    
    def generate_cycle_count_integration(self):
        """Generate cycle count integration records"""
        print("Generating cycle count integration...")
        
        for i in range(15):  # Generate 15 cycle count integrations
            integration = {
                'integration_id': self.generate_id('CYCLE', 'cycle'),
                'wms_cycle_count_id': f"CC-{random.randint(100000, 999999)}",
                'wms_warehouse_id': f"WMS-{random.randint(1, 3):03d}",
                'erp_location_id': f"FAC-{random.randint(1, 4):06d}",
                'integration_status': random.choice(['completed', 'pending', 'failed']),
                'items_counted': random.randint(50, 500),
                'discrepancies_found': random.randint(0, 25),
                'value_adjustment': round(random.uniform(-5000, 5000), 2),
                'integration_timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'error_message': None if random.choice([True, True, False]) else "Minor discrepancy in count",
                'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            self.cycle_count_integration.append(integration)
        
        print(f"Generated {len(self.cycle_count_integration)} cycle count integrations")
    
    def generate_inventory_adjustments_sync(self):
        """Generate inventory adjustment sync records"""
        print("Generating inventory adjustment sync...")
        
        for i in range(30):  # Generate 30 adjustment sync records
            adjustment = {
                'sync_id': self.generate_id('ADJ', 'adjustment'),
                'source_system': random.choice(['ERP', 'WMS']),
                'adjustment_document_id': f"ADJDOC-{random.randint(100000, 999999)}",
                'material_id': f"MATERIAL-{random.randint(1, 200):06d}",
                'location_id': f"FAC-{random.randint(1, 4):06d}",
                'adjustment_type': random.choice(['cycle_count', 'physical_count', 'damage', 'obsolescence']),
                'adjustment_date': (datetime.now() - timedelta(days=random.randint(0, 30))).strftime('%Y-%m-%d'),
                'adjustment_quantity': round(random.uniform(-100, 100), 2),
                'unit_cost': round(random.uniform(10, 1000), 2),
                'total_value': 0,  # Will be calculated
                'source_system': random.choice(['ERP', 'WMS']),  # Required field
                'sync_status': random.choice(['synced', 'pending', 'error']),
                'sync_timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            # Calculate total value
            adjustment['total_value'] = round(adjustment['quantity_adjusted'] * adjustment['unit_cost'], 2)
            self.inventory_adjustments_sync.append(adjustment)
        
        print(f"Generated {len(self.inventory_adjustments_sync)} adjustment sync records")
    
    def generate_inventory_allocations(self):
        """Generate inventory allocation records"""
        print("Generating inventory allocations...")
        
        for i in range(40):  # Generate 40 allocation records
            source_types = ['sales_order', 'production_order', 'transfer_order']
            allocation = {
                'allocation_id': self.generate_id('ALLOC', 'allocation'),
                'source_type': random.choice(source_types),
                'source_document_id': f"DOC-{random.randint(100000, 999999)}",
                'material_id': f"MATERIAL-{random.randint(1, 200):06d}",
                'location_id': f"FAC-{random.randint(1, 4):06d}",
                'allocated_quantity': round(random.uniform(10, 500), 2),
                'allocation_status': random.choice(['allocated', 'picked', 'shipped', 'cancelled']),
                'allocation_date': datetime.now().strftime('%Y-%m-%d'),
                'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            self.inventory_allocations.append(allocation)
        
        print(f"Generated {len(self.inventory_allocations)} inventory allocations")
    
    def generate_inventory_reconciliation(self):
        """Generate inventory reconciliation headers and lines"""
        print("Generating inventory reconciliation...")
        
        # Generate reconciliation headers
        for i in range(8):  # 8 reconciliation sessions
            header = {
                'reconciliation_id': self.generate_id('RECON', 'recon_header'),
                'reconciliation_number': f"RECON-{datetime.now().strftime('%Y%m')}-{i+1:03d}",  # Required field
                'reconciliation_date': (datetime.now() - timedelta(days=random.randint(1, 30))).strftime('%Y-%m-%d'),
                'reconciliation_type': random.choice(['monthly', 'quarterly', 'cycle_count', 'audit']),
                'location_id': f"FAC-{random.randint(1, 4):06d}",
                'total_items': random.randint(50, 200),
                'discrepancies_found': random.randint(0, 20),
                'reconciliation_status': random.choice(['completed', 'in_progress', 'approved']),
                'performed_by': f"USR-{random.randint(1, 5):03d}",
                'approved_by': f"USR-{random.randint(1, 5):03d}" if random.choice([True, False]) else None,
                'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            self.inventory_reconciliation_headers.append(header)
            
            # Generate reconciliation lines for each header
            for j in range(random.randint(5, 25)):
                line = {
                    'line_id': self.generate_id('RECONLINE', 'recon_line'),
                    'reconciliation_id': header['reconciliation_id'],
                    'location_id': header['location_id'],
                    'material_id': f"MAT-{random.randint(1, 200):06d}",
                    'system_quantity': random.randint(0, 1000),
                    'physical_quantity': random.randint(0, 1000),
                    'variance_quantity': 0,  # Will be calculated
                    'unit_cost': round(random.uniform(10, 500), 2),
                    'variance_value': 0,  # Will be calculated
                    'variance_reason': random.choice(['count_error', 'system_error', 'theft', 'damage', 'none']) if random.choice([True, False]) else None,
                    'adjustment_required': False,  # Will be set based on variance
                    'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                # Calculate variance
                line['variance_quantity'] = line['physical_quantity'] - line['system_quantity']
                line['variance_value'] = round(line['variance_quantity'] * line['unit_cost'], 2)
                line['adjustment_required'] = abs(line['variance_quantity']) > 0
                self.inventory_reconciliation_lines.append(line)
        
        print(f"Generated {len(self.inventory_reconciliation_headers)} reconciliation headers")
        print(f"Generated {len(self.inventory_reconciliation_lines)} reconciliation lines")
    
    def generate_sync_errors(self):
        """Generate sync error records"""
        print("Generating sync errors...")
        
        error_types = ['connection_timeout', 'data_validation', 'duplicate_key', 'foreign_key', 'network_error']
        
        for i in range(12):  # Generate 12 error records
            error_details_data = {
                'operation': random.choice(['inventory_update', 'order_sync', 'allocation_sync', 'adjustment_sync']),
                'timestamp': datetime.now().isoformat(),
                'affected_records': random.randint(1, 50)
            }
            error = {
                'error_id': self.generate_id('ERR', 'sync_error'),
                'error_type': random.choice(error_types),
                'error_message': f"Sync failed: {random.choice(['Connection timeout', 'Invalid data format', 'Record not found', 'Database constraint violation'])}",
                'error_details': json.dumps(error_details_data),
                'retry_count': random.randint(0, 3),
                'error_status': random.choice(['open', 'investigating', 'resolved', 'ignored']),
                'resolved_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S') if random.choice([True, False]) else None,
                'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            self.inventory_sync_errors.append(error)
        
        print(f"Generated {len(self.inventory_sync_errors)} sync error records")
    
    def generate_sync_metrics(self):
        """Generate sync performance metrics"""
        print("Generating sync metrics...")
        
        # Generate daily metrics for the last 30 days
        base_date = datetime.now()
        for day_offset in range(30):
            metric_date = base_date - timedelta(days=day_offset)
            
            metric = {
                'metric_id': self.generate_id('METRIC', 'sync_metric'),
                'metric_date': metric_date.strftime('%Y-%m-%d'),
                'total_sync_operations': random.randint(500, 2000),
                'successful_syncs': random.randint(450, 1950),
                'failed_syncs': random.randint(0, 50),
                'average_sync_time_ms': round(random.uniform(100, 2000), 2),
                'max_sync_time_ms': round(random.uniform(2000, 10000), 2),
                'throughput_records_per_hour': random.randint(1000, 5000),
                'error_rate_percent': round(random.uniform(0, 5), 2),
                'created_at': metric_date.strftime('%Y-%m-%d %H:%M:%S')
            }
            self.inventory_sync_metrics.append(metric)
        
        print(f"Generated {len(self.inventory_sync_metrics)} sync metrics")
    
    def generate_sync_queue(self):
        """Generate sync queue records"""
        print("Generating sync queue...")
        
        operations = ['inventory_update', 'allocation_create', 'adjustment_sync', 'reconciliation_update']
        
        for i in range(25):  # Generate 25 queue items
            queue_item = {
                'queue_id': self.generate_id('QUEUE', 'sync_queue'),
                'sync_direction': random.choice(['ERP_TO_WMS', 'WMS_TO_ERP']),
                'transaction_type': random.choice(['allocation', 'reservation', 'movement', 'adjustment', 'cycle_count']),
                'transaction_id': f"TXN-{random.randint(100000, 999999)}",
                'material_id': f"MATERIAL-{random.randint(1, 200):06d}",
                'quantity': round(random.uniform(1, 500), 2),
                'sync_status': random.choice(['pending', 'in_progress', 'completed', 'error']),
                'retry_count': random.randint(0, 2),
                'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            self.inventory_sync_queue.append(queue_item)
        
        print(f"Generated {len(self.inventory_sync_queue)} sync queue items")
    
    def generate_transaction_log(self):
        """Generate inventory transaction log"""
        print("Generating inventory transaction log...")
        
        transaction_types = ['receipt', 'issue', 'transfer', 'adjustment', 'allocation', 'consumption']
        
        for i in range(100):  # Generate 100 transaction log entries
            transaction = {
                'log_id': self.generate_id('LOG', 'transaction'),
                'transaction_id': f"TXN-{random.randint(100000, 999999)}",
                'material_id': f"MATERIAL-{random.randint(1, 200):06d}",
                'location_id': f"FAC-{random.randint(1, 4):06d}",
                'transaction_type': random.choice(transaction_types),
                'source_system': random.choice(['ERP', 'WMS', 'MES']),
                'quantity_change': round(random.uniform(-500, 500), 2),
                'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            # Calculate total value
            transaction['total_value'] = round(transaction['quantity'] * transaction['unit_cost'], 2)
            self.inventory_transaction_log.append(transaction)
        
        print(f"Generated {len(self.inventory_transaction_log)} transaction log entries")
    
    def generate_inventory_sync_parallel(self):
        """Generate all inventory sync operations with ULTRA-FAST parallel processing"""
        print(f"\nGenerating inventory sync operations with PARALLEL processing...")
        start_time = datetime.now()
        
        # Generate master sync data first (sequential)
        self.generate_sync_mappings()
        self.generate_inventory_snapshot()
        
        # Generate time-based sync operations in parallel
        days_to_process = 30  # Last 30 days of sync operations
        chunk_size = max(1, days_to_process // self.worker_count)
        chunks = []
        
        for i in range(0, days_to_process, chunk_size):
            end_day = min(i + chunk_size, days_to_process)
            chunks.append((i, end_day))
        
        print(f"  🚀 Processing {len(chunks)} day chunks with {self.worker_count} workers...")
        
        # Thread-safe data collectors
        all_cycle_counts = []
        all_adjustments = []
        all_allocations = []
        all_recon_headers = []
        all_recon_lines = []
        all_sync_errors = []
        all_sync_metrics = []
        all_sync_queue = []
        all_transaction_logs = []
        
        def process_sync_chunk(chunk_info):
            """Process a chunk of days for sync operations"""
            start_day, end_day = chunk_info
            chunk_cycle_counts = []
            chunk_adjustments = []
            chunk_allocations = []
            chunk_recon_headers = []
            chunk_recon_lines = []
            chunk_sync_errors = []
            chunk_sync_metrics = []
            chunk_sync_queue = []
            chunk_transaction_logs = []
            
            # Local counters to avoid ID collision
            local_cycle_counter = start_day * 10 + 1000
            local_adj_counter = start_day * 15 + 2000
            local_alloc_counter = start_day * 8 + 500
            local_recon_header_counter = start_day * 5 + 100
            local_recon_line_counter = start_day * 20 + 3000
            local_error_counter = start_day * 12 + 1500
            local_metric_counter = start_day * 6 + 200
            local_queue_counter = start_day * 25 + 4000
            local_txn_counter = start_day * 30 + 5000
            
            for day_offset in range(start_day, end_day):
                current_date = datetime.now() - timedelta(days=day_offset)
                
                day_data = self._generate_sync_day_data_local(
                    current_date, local_cycle_counter, local_adj_counter,
                    local_alloc_counter, local_recon_header_counter, local_recon_line_counter,
                    local_error_counter, local_metric_counter, local_queue_counter,
                    local_txn_counter
                )
                
                chunk_cycle_counts.extend(day_data['cycle_counts'])
                chunk_adjustments.extend(day_data['adjustments'])
                chunk_allocations.extend(day_data['allocations'])
                chunk_recon_headers.extend(day_data['recon_headers'])
                chunk_recon_lines.extend(day_data['recon_lines'])
                chunk_sync_errors.extend(day_data['sync_errors'])
                chunk_sync_metrics.extend(day_data['sync_metrics'])
                chunk_sync_queue.extend(day_data['sync_queue'])
                chunk_transaction_logs.extend(day_data['transaction_logs'])
                
                # Update counters
                local_cycle_counter += len(day_data['cycle_counts'])
                local_adj_counter += len(day_data['adjustments'])
                local_alloc_counter += len(day_data['allocations'])
                local_recon_header_counter += len(day_data['recon_headers'])
                local_recon_line_counter += len(day_data['recon_lines'])
                local_error_counter += len(day_data['sync_errors'])
                local_metric_counter += len(day_data['sync_metrics'])
                local_queue_counter += len(day_data['sync_queue'])
                local_txn_counter += len(day_data['transaction_logs'])
            
            # Thread-safe data collection
            with self.data_lock:
                all_cycle_counts.extend(chunk_cycle_counts)
                all_adjustments.extend(chunk_adjustments)
                all_allocations.extend(chunk_allocations)
                all_recon_headers.extend(chunk_recon_headers)
                all_recon_lines.extend(chunk_recon_lines)
                all_sync_errors.extend(chunk_sync_errors)
                all_sync_metrics.extend(chunk_sync_metrics)
                all_sync_queue.extend(chunk_sync_queue)
                all_transaction_logs.extend(chunk_transaction_logs)
            
            print(f"    ✓ Sync chunk {start_day+1}-{end_day}/{days_to_process} completed ({len(chunk_transaction_logs)} transactions)")
            return len(chunk_transaction_logs)
        
        # Execute parallel processing
        with ThreadPoolExecutor(max_workers=self.worker_count) as executor:
            futures = [executor.submit(process_sync_chunk, chunk) for chunk in chunks]
            total_records = sum(future.result() for future in futures)
        
        # Assign to class attributes
        self.cycle_count_integration = all_cycle_counts
        self.inventory_adjustments_sync = all_adjustments
        self.inventory_allocations = all_allocations
        self.inventory_reconciliation_headers = all_recon_headers
        self.inventory_reconciliation_lines = all_recon_lines
        self.inventory_sync_errors = all_sync_errors
        self.inventory_sync_metrics = all_sync_metrics
        self.inventory_sync_queue = all_sync_queue
        self.inventory_transaction_log = all_transaction_logs
        
        elapsed = (datetime.now() - start_time).total_seconds()
        print(f"✓ Generated {len(all_transaction_logs)} transaction logs, {len(all_cycle_counts)} cycle counts, "
              f"{len(all_adjustments)} adjustments via PARALLEL processing in {elapsed:.2f}s")
    
    def _generate_sync_day_data_local(self, current_date: datetime, cycle_counter: int,
                                     adj_counter: int, alloc_counter: int, recon_header_counter: int,
                                     recon_line_counter: int, error_counter: int, metric_counter: int,
                                     queue_counter: int, txn_counter: int) -> Dict:
        """Generate all sync data for a single day (local/chunk version)"""
        day_cycle_counts = []
        day_adjustments = []
        day_allocations = []
        day_recon_headers = []
        day_recon_lines = []
        day_sync_errors = []
        day_sync_metrics = []
        day_sync_queue = []
        day_transaction_logs = []
        
        # Generate cycle count integrations (1-3 per day)
        cycle_count_num = random.randint(1, 3)
        for i in range(cycle_count_num):
            integration = {
                'integration_id': f"CYCLE-{str(cycle_counter + i).zfill(6)}",
                'wms_cycle_count_id': f"CC-{random.randint(100000, 999999)}",
                'wms_warehouse_id': f"WMS-{random.randint(1, 3):03d}",
                'erp_location_id': f"FAC-{random.randint(1, 4):06d}",
                'integration_status': random.choice(['completed', 'pending', 'failed']),
                'items_counted': random.randint(50, 500),
                'discrepancies_found': random.randint(0, 25),
                'value_adjustment': round(random.uniform(-5000, 5000), 2),
                'integration_timestamp': current_date.strftime('%Y-%m-%d %H:%M:%S'),
                'error_message': None if random.choice([True, True, False]) else "Minor discrepancy in count",
                'created_at': self.time_coord.get_current_time().strftime('%Y-%m-%d %H:%M:%S')
            }
            day_cycle_counts.append(integration)
        
        # Generate inventory adjustments (2-5 per day)
        adj_num = random.randint(2, 5)
        for i in range(adj_num):
            adjustment = {
                'sync_id': f"ADJ-{str(adj_counter + i).zfill(6)}",
                'source_system': random.choice(['ERP', 'WMS']),
                'adjustment_document_id': f"ADJDOC-{random.randint(100000, 999999)}",
                'material_id': f"MATERIAL-{random.randint(1, 200):06d}",
                'location_id': f"FAC-{random.randint(1, 4):06d}",
                'adjustment_type': random.choice(['cycle_count', 'physical_count', 'damage', 'obsolescence']),
                'adjustment_date': current_date.strftime('%Y-%m-%d'),
                'adjustment_quantity': round(random.uniform(-100, 100), 2),
                'sync_status': random.choice(['pending', 'completed', 'error']),
                'created_at': self.time_coord.get_current_time().strftime('%Y-%m-%d %H:%M:%S')
            }
            day_adjustments.append(adjustment)
        
        # Generate inventory allocations (3-8 per day)
        alloc_num = random.randint(3, 8)
        for i in range(alloc_num):
            source_types = ['sales_order', 'production_order', 'transfer_order']
            allocation = {
                'allocation_id': f"ALLOC-{str(alloc_counter + i).zfill(6)}",
                'source_type': random.choice(source_types),
                'source_document_id': f"DOC-{random.randint(100000, 999999)}",
                'material_id': f"MATERIAL-{random.randint(1, 200):06d}",
                'location_id': f"FAC-{random.randint(1, 4):06d}",
                'allocated_quantity': round(random.uniform(10, 1000), 2),
                'allocation_status': random.choice(['allocated', 'picked', 'shipped', 'cancelled']),
                'allocation_date': current_date.strftime('%Y-%m-%d'),
                'created_at': self.time_coord.get_current_time().strftime('%Y-%m-%d %H:%M:%S')
            }
            day_allocations.append(allocation)
        
        # Generate sync errors (0-5 per day)
        error_num = random.randint(0, 5)
        for i in range(error_num):
            error_details_data = {
                'error_context': 'Sync operation',
                'affected_record': f"REC-{random.randint(100000, 999999)}",
                'timestamp': current_date.isoformat()
            }
            error = {
                'error_id': f"ERR-{str(error_counter + i).zfill(6)}",
                'error_type': random.choice(['data_mismatch', 'connection_timeout', 'validation_error', 'mapping_error']),
                'source_system': random.choice(['ERP', 'WMS']),
                'target_system': random.choice(['ERP', 'WMS']),
                'error_message': f"Sync error occurred at {current_date}",
                'error_details': json.dumps(error_details_data),
                'record_id': f"REC-{random.randint(100000, 999999)}",
                'retry_count': random.randint(0, 3),
                'error_status': random.choice(['resolved', 'pending', 'failed']),
                'occurred_at': current_date.strftime('%Y-%m-%d %H:%M:%S'),
                'resolved_at': (current_date + timedelta(hours=random.randint(1, 24))).strftime('%Y-%m-%d %H:%M:%S') if random.random() > 0.3 else None,
                'created_at': self.time_coord.get_current_time().strftime('%Y-%m-%d %H:%M:%S')
            }
            day_sync_errors.append(error)
        
        # Generate sync metrics (1 per day)
        metric = {
            'metric_id': f"METRIC-{str(metric_counter).zfill(6)}",
            'metric_date': current_date.strftime('%Y-%m-%d'),
            'sync_type': random.choice(['inventory', 'transaction', 'master_data']),
            'records_processed': random.randint(100, 10000),
            'records_successful': random.randint(95, 99),
            'records_failed': random.randint(1, 5),
            'processing_time_seconds': random.randint(30, 3600),
            'throughput_per_second': round(random.uniform(10, 100), 2),
            'error_rate_percent': round(random.uniform(0.1, 5.0), 2),
            'created_at': self.time_coord.get_current_time().strftime('%Y-%m-%d %H:%M:%S')
        }
        day_sync_metrics.append(metric)
        
        # Generate sync queue items (5-25 per day)
        queue_num = random.randint(5, 25)
        for i in range(queue_num):
            queue_item = {
                'queue_id': f"QUEUE-{str(queue_counter + i).zfill(6)}",
                'sync_direction': random.choice(['ERP_TO_WMS', 'WMS_TO_ERP']),
                'transaction_type': random.choice(['allocation', 'reservation', 'movement', 'adjustment', 'cycle_count']),
                'transaction_id': f"TXN-{random.randint(100000, 999999)}",
                'material_id': f"MATERIAL-{random.randint(1, 200):06d}",
                'quantity': round(random.uniform(1, 500), 2),
                'sync_status': random.choice(['pending', 'in_progress', 'completed', 'error']),
                'retry_count': random.randint(0, 2),
                'priority': random.choice(['high', 'medium', 'low']),
                'payload_data': '{"material_id": "MATERIAL-123", "quantity": 100}',
                'retry_count': random.randint(0, 2),
                'queued_at': current_date.strftime('%Y-%m-%d %H:%M:%S'),
                'processed_at': (current_date + timedelta(minutes=random.randint(1, 60))).strftime('%Y-%m-%d %H:%M:%S') if random.random() > 0.2 else None,
                'created_at': self.time_coord.get_current_time().strftime('%Y-%m-%d %H:%M:%S')
            }
            day_sync_queue.append(queue_item)
        
        # Generate transaction logs (10-30 per day)
        txn_num = random.randint(10, 30)
        transaction_types = ['receipt', 'issue', 'transfer', 'adjustment', 'allocation', 'consumption']
        for i in range(txn_num):
            transaction = {
                'log_id': f"LOG-{str(txn_counter + i).zfill(6)}",
                'transaction_id': f"TXN-{str(txn_counter + i).zfill(6)}",
                'material_id': f"MAT-{random.randint(1, 200):06d}",
                'location_id': f"FAC-{random.randint(1, 4):06d}",
                'transaction_type': random.choice(transaction_types),
                'transaction_date': current_date.strftime('%Y-%m-%d'),
                'reference_document': f"DOC-{random.randint(100000, 999999)}",
                'source_system': random.choice(['ERP', 'WMS', 'MES']),
                'quantity_change': round(random.uniform(-500, 500), 2),
                'source_location': f"FAC-{random.randint(1, 4):06d}" if random.choice([True, False]) else None,
                'target_location': f"FAC-{random.randint(1, 4):06d}",
                'quantity': round(random.uniform(1, 500), 2),
                'unit_cost': round(random.uniform(10, 1000), 2),
                'total_value': 0,  # Will be calculated
                'user_id': f"USR-{random.randint(1, 10):03d}",
                'batch_id': f"BATCH-{random.randint(1000, 9999)}" if random.choice([True, False]) else None,
                'created_at': self.time_coord.get_current_time().strftime('%Y-%m-%d %H:%M:%S')
            }
            transaction['total_value'] = round(transaction['quantity'] * transaction['unit_cost'], 2)
            day_transaction_logs.append(transaction)
        
        # Generate inventory reconciliation headers (1-2 per day)
        recon_header_num = random.randint(1, 2)
        for i in range(recon_header_num):
            header = {
                'reconciliation_id': f"RECON-{str(recon_header_counter + i).zfill(6)}",
                'reconciliation_number': f"RECON-{current_date.strftime('%Y%m')}-{str(recon_header_counter + i).zfill(3)}",
                'reconciliation_date': current_date.strftime('%Y-%m-%d'),
                'location_id': f"FAC-{random.randint(1, 4):06d}",
                'reconciliation_status': random.choice(['in_progress', 'completed', 'approved']),
                'total_variance_value': round(random.uniform(-10000, 10000), 2),
                'created_at': self.time_coord.get_current_time().strftime('%Y-%m-%d %H:%M:%S')
            }
            day_recon_headers.append(header)
            
            # Generate reconciliation lines for each header (5-15 lines per header)
            line_num = random.randint(5, 15)
            for j in range(line_num):
                # Use current length of accumulated lines to ensure unique IDs
                line_id_num = recon_line_counter + len(day_recon_lines)
                line = {
                    'line_id': f"RECONLN-{str(line_id_num).zfill(6)}",
                    'reconciliation_id': header['reconciliation_id'],
                    'location_id': header['location_id'],
                    'material_id': f"MATERIAL-{random.randint(1, 200):06d}",
                    'variance_quantity': round(random.uniform(-500, 500), 2),
                    'variance_value': round(random.uniform(-50000, 50000), 2),
                    'variance_reason': random.choice(['Count discrepancy', 'System error', 'Damage', 'Theft']) if random.random() > 0.6 else None,
                    'created_at': self.time_coord.get_current_time().strftime('%Y-%m-%d %H:%M:%S')
                }
                day_recon_lines.append(line)
        
        return {
            'cycle_counts': day_cycle_counts,
            'adjustments': day_adjustments,
            'allocations': day_allocations,
            'recon_headers': day_recon_headers,
            'recon_lines': day_recon_lines,
            'sync_errors': day_sync_errors,
            'sync_metrics': day_sync_metrics,
            'sync_queue': day_sync_queue,
            'transaction_logs': day_transaction_logs
        }
    
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
        print(f"  Budget Lines: {len(self.budget_lines)}")
        print(f"  Financial Statements: {len(self.financial_statements)}")
        print(f"  GL Audit Trail: {len(self.gl_audit_trail)}")
        print(f"  Period Close Tasks: {len(self.period_close_tasks)}")
        
        print(f"\nInventory Sync:")
        print(f"  Sync Mappings: {len(self.sync_mappings)}")
        print(f"  Inventory Snapshots: {len(self.inventory_snapshot)}")
        print(f"  Cycle Count Integration: {len(self.cycle_count_integration)}")
        print(f"  Adjustment Sync: {len(self.inventory_adjustments_sync)}")
        print(f"  Inventory Allocations: {len(self.inventory_allocations)}")
        print(f"  Reconciliation Headers: {len(self.inventory_reconciliation_headers)}")
        print(f"  Reconciliation Lines: {len(self.inventory_reconciliation_lines)}")
        print(f"  Sync Errors: {len(self.inventory_sync_errors)}")
        print(f"  Sync Metrics: {len(self.inventory_sync_metrics)}")
        print(f"  Sync Queue: {len(self.inventory_sync_queue)}")
        print(f"  Transaction Log: {len(self.inventory_transaction_log)}")    
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
            'budget_headers': [b for b in self.budgets],
            'budget_lines': self.budget_lines,
            'financial_statements': self.financial_statements,
            'gl_audit_trail': self.gl_audit_trail,
            'period_close_tasks': self.period_close_tasks
        }
        
        financial_file = Path(__file__).parent / 'genims_financial_data.json'
        with open(financial_file, 'w') as f:
            json.dump(financial_data, f, indent=2)
        print(f"✓ Financial data exported to {financial_file.name}")
        
        # FILE 2: Inventory sync data (for genims_erp_wms_sync_db)
        inventory_sync_data = {
            'inventory_sync_mappings': self.sync_mappings,
            'inventory_snapshot': self.inventory_snapshot,
            'cycle_count_integration': self.cycle_count_integration,
            'inventory_adjustments_sync': self.inventory_adjustments_sync,
            'inventory_allocations': self.inventory_allocations,
            'inventory_reconciliation_headers': self.inventory_reconciliation_headers,
            'inventory_reconciliation_lines': self.inventory_reconciliation_lines,
            'inventory_sync_errors': self.inventory_sync_errors,
            'inventory_sync_metrics': self.inventory_sync_metrics,
            'inventory_sync_queue': self.inventory_sync_queue,
            'inventory_transaction_log': self.inventory_transaction_log
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
