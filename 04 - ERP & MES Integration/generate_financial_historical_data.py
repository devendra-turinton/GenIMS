#!/usr/bin/env python3
"""
GenIMS Financial/GL Data Generator
Generates chart of accounts, journal entries, financial statements, and GL data
"""

import json
import random
from datetime import datetime, timedelta
import sys
from pathlib import Path

# Load master data
try:
    master_data_file = Path(__file__).parent.parent / "01 - Base Data" / "genims_master_data.json"
    with open(master_data_file, 'r') as f:
        master_data = json.load(f)
except:
    print("Warning: Could not load master data")
    master_data = {'factories': [], 'employees': []}

# Standard Chart of Accounts
CHART_OF_ACCOUNTS = {
    'assets': [
        ('1001', 'Cash - Bank Account', 'Cash', 'current_asset'),
        ('1010', 'Petty Cash', 'Cash', 'current_asset'),
        ('1100', 'Accounts Receivable', 'Receivables', 'current_asset'),
        ('1110', 'Allowance for Doubtful Debts', 'Receivables', 'current_asset'),
        ('1200', 'Inventory - Raw Materials', 'Inventory', 'current_asset'),
        ('1210', 'Inventory - WIP', 'Inventory', 'current_asset'),
        ('1220', 'Inventory - Finished Goods', 'Inventory', 'current_asset'),
        ('1300', 'Prepaid Expenses', 'Other Current', 'current_asset'),
        ('1400', 'Advances to Suppliers', 'Other Current', 'current_asset'),
        ('1500', 'Fixed Assets - Land', 'Property Plant Equipment', 'fixed_asset'),
        ('1510', 'Fixed Assets - Building', 'Property Plant Equipment', 'fixed_asset'),
        ('1520', 'Fixed Assets - Machinery', 'Property Plant Equipment', 'fixed_asset'),
        ('1530', 'Fixed Assets - Equipment', 'Property Plant Equipment', 'fixed_asset'),
        ('1540', 'Fixed Assets - Vehicles', 'Property Plant Equipment', 'fixed_asset'),
        ('1550', 'Fixed Assets - Furniture', 'Property Plant Equipment', 'fixed_asset'),
        ('1600', 'Accumulated Depreciation', 'Depreciation', 'fixed_asset'),
        ('1700', 'Intangible Assets', 'Intangible', 'fixed_asset'),
        ('1800', 'Investment in Subsidiaries', 'Investment', 'fixed_asset'),
    ],
    'liabilities': [
        ('2001', 'Accounts Payable', 'Payable', 'current_liability'),
        ('2010', 'Accrued Expenses', 'Payable', 'current_liability'),
        ('2100', 'Short-term Borrowings', 'Borrowings', 'current_liability'),
        ('2110', 'Current Portion of Long-term Debt', 'Borrowings', 'current_liability'),
        ('2200', 'Income Tax Payable', 'Tax', 'current_liability'),
        ('2210', 'GST Payable', 'Tax', 'current_liability'),
        ('2220', 'TDS Payable', 'Tax', 'current_liability'),
        ('2300', 'Employee Benefits Payable', 'Payroll', 'current_liability'),
        ('2310', 'Provident Fund Payable', 'Payroll', 'current_liability'),
        ('2400', 'Dividends Payable', 'Other', 'current_liability'),
        ('2500', 'Long-term Borrowings', 'Borrowings', 'long_term_liability'),
        ('2600', 'Deferred Tax Liability', 'Tax', 'long_term_liability'),
    ],
    'equity': [
        ('3001', 'Share Capital', 'Capital', 'equity'),
        ('3100', 'Retained Earnings', 'Earnings', 'equity'),
        ('3110', 'Accumulated Profit', 'Earnings', 'equity'),
        ('3200', 'Reserves', 'Reserve', 'equity'),
    ],
    'revenue': [
        ('4001', 'Sales Revenue - Domestic', 'Revenue', 'revenue'),
        ('4010', 'Sales Revenue - Export', 'Revenue', 'revenue'),
        ('4020', 'Service Revenue', 'Service', 'revenue'),
        ('4100', 'Other Income', 'Other', 'revenue'),
        ('4110', 'Interest Income', 'Finance', 'revenue'),
        ('4120', 'Dividend Income', 'Finance', 'revenue'),
        ('4130', 'Foreign Exchange Gain', 'Finance', 'revenue'),
    ],
    'cost_of_sales': [
        ('5001', 'Raw Material Consumed', 'Material', 'cost_of_sales'),
        ('5010', 'Direct Labor', 'Labor', 'cost_of_sales'),
        ('5020', 'Manufacturing Overhead', 'Overhead', 'cost_of_sales'),
        ('5030', 'Cost of Goods Manufactured', 'COGS', 'cost_of_sales'),
    ],
    'expenses': [
        ('6001', 'Salaries and Wages', 'Personnel', 'operating_expense'),
        ('6010', 'Employee Benefits', 'Personnel', 'operating_expense'),
        ('6020', 'Travel and Transportation', 'Travel', 'operating_expense'),
        ('6030', 'Utilities', 'Utilities', 'operating_expense'),
        ('6040', 'Repairs and Maintenance', 'Maintenance', 'operating_expense'),
        ('6050', 'Depreciation', 'Depreciation', 'operating_expense'),
        ('6060', 'Amortization', 'Depreciation', 'operating_expense'),
        ('6100', 'Advertising and Marketing', 'Marketing', 'operating_expense'),
        ('6110', 'Sales Commission', 'Sales', 'operating_expense'),
        ('6120', 'Freight and Shipping', 'Logistics', 'operating_expense'),
        ('6130', 'Insurance', 'Insurance', 'operating_expense'),
        ('6140', 'Rent', 'Rent', 'operating_expense'),
        ('6150', 'Administrative Expenses', 'Admin', 'operating_expense'),
        ('6160', 'Professional Fees', 'Professional', 'operating_expense'),
        ('6170', 'Communication', 'Utilities', 'operating_expense'),
        ('6180', 'Office Supplies', 'Supplies', 'operating_expense'),
        ('6190', 'Miscellaneous', 'Other', 'operating_expense'),
        ('6200', 'Interest Expense', 'Finance', 'operating_expense'),
        ('6210', 'Foreign Exchange Loss', 'Finance', 'operating_expense'),
        ('6220', 'Bad Debt Expense', 'Credit', 'operating_expense'),
        ('6230', 'Donations and CSR', 'Corporate', 'operating_expense'),
    ]
}

class FinancialDataGenerator:
    def __init__(self):
        self.factories = master_data.get('factories', [])
        self.employees = master_data.get('employees', [])
        
        self.data = {
            'chart_of_accounts': [],
            'fiscal_periods': [],
            'cost_centers': [],
            'journal_entries': [],
            'journal_entry_lines': [],
            'account_balances': [],
            'cost_center_balances': [],
            'exchange_rates': [],
            'gl_posting_rules': [],
            'budget_templates': [],
            'budget_lines': [],
            'budget_vs_actual': [],
            'income_statement_mappings': [],
            'balance_sheet_mappings': [],
            'intercompany_transactions': [],
            'account_reconciliations': [],
            'accruals_deferrals': [],
            'depreciation_master': [],
            'depreciation_schedules': [],
            'cash_flow_forecast': [],
            'tax_calculations': [],
            'profitability_analysis': [],
            'financial_statements': [],
            'transaction_approvals': [],
            'audit_trail': [],
            'financial_ratios': [],
            'bank_reconciliations': [],
            'ledger_control_accounts': [],
            'financial_document_attachments': []
        }
        
        self.gl_entry_counter = 1
    
    def generate(self, days=90):
        """Generate all financial data"""
        print("Generating Financial/GL data...")
        start_date = datetime.now() - timedelta(days=days)
        
        self.generate_chart_of_accounts()
        self.generate_fiscal_periods(days)
        self.generate_cost_centers()
        self.generate_exchange_rates(start_date, days)
        self.generate_gl_posting_rules()
        self.generate_journal_entries(start_date, days)
        self.generate_account_balances()
        self.generate_cost_center_balances()
        self.generate_budget_templates()
        self.generate_budget_lines()
        self.generate_budget_vs_actual()
        self.generate_income_statement_mappings()
        self.generate_balance_sheet_mappings()
        self.generate_intercompany_transactions(start_date, days)
        self.generate_account_reconciliations()
        self.generate_accruals_deferrals(start_date, days)
        self.generate_depreciation()
        self.generate_cash_flow_forecast(start_date, days)
        self.generate_tax_calculations()
        self.generate_profitability_analysis(start_date, days)
        self.generate_financial_statements(start_date, days)
        self.generate_financial_ratios(start_date, days)
        self.generate_bank_reconciliations(start_date, days)
        self.generate_ledger_control_accounts()
        self.generate_transaction_approvals(start_date, days)
        self.generate_audit_trail(start_date, days)
        self.generate_financial_document_attachments(start_date, days)
        
        return self.data
    
    def generate_chart_of_accounts(self):
        """Generate chart of accounts"""
        print("Generating chart of accounts...")
        
        for account_type, accounts in CHART_OF_ACCOUNTS.items():
            for code, name, group, sub_type in accounts:
                coa = {
                    'gl_account': code,
                    'account_number': code,
                    'account_name': name,
                    'account_type': account_type.replace('_', ' ').title(),
                    'sub_account_type': sub_type,
                    'account_group': group,
                    'company_code': '1001',
                    'controlling_area': 'IND',
                    'is_active': True,
                    'is_reconciliation_account': random.choice([True, False]),
                    'valid_from': (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d'),
                    'created_at': (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d %H:%M:%S')
                }
                self.data['chart_of_accounts'].append(coa)
        
        print(f"Generated {len(self.data['chart_of_accounts'])} chart of accounts")
    
    def generate_fiscal_periods(self, days):
        """Generate fiscal periods"""
        print("Generating fiscal periods...")
        
        current_year = datetime.now().year
        current_month = datetime.now().month
        
        # Generate 13 periods (12 months + opening)
        for month in range(1, 14):
            if month == 13:
                period_name = "Opening"
                start_date = datetime(current_year, 1, 1)
                end_date = datetime(current_year, 1, 1)
                quarter = 0
            else:
                start_date = datetime(current_year, month, 1)
                if month == 12:
                    end_date = datetime(current_year, 12, 31)
                else:
                    end_date = datetime(current_year, month + 1, 1) - timedelta(days=1)
                
                month_names = ['', 'January', 'February', 'March', 'April', 'May', 'June',
                              'July', 'August', 'September', 'October', 'November', 'December']
                period_name = month_names[month]
                quarter = (month - 1) // 3 + 1
            
            period = {
                'fiscal_period_id': f"FP-{current_year}-{month:02d}",
                'fiscal_year': current_year,
                'period_number': month,
                'period_name': period_name,
                'period_start_date': start_date.strftime('%Y-%m-%d'),
                'period_end_date': end_date.strftime('%Y-%m-%d'),
                'quarter_number': quarter,
                'period_status': 'open' if month >= current_month else 'locked',
                'company_code': '1001',
                'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            self.data['fiscal_periods'].append(period)
        
        print(f"Generated {len(self.data['fiscal_periods'])} fiscal periods")
    
    def generate_cost_centers(self):
        """Generate cost centers"""
        print("Generating cost centers...")
        
        categories = ['production', 'marketing', 'sales', 'administration', 'research_development']
        
        for i in range(1, 21):
            cost_center = {
                'cost_center_id': f"CC-{i:04d}",
                'cost_center_code': f"CC{i:04d}",
                'cost_center_name': f"{random.choice(categories).replace('_', ' ').title()} Center {i}",
                'controlling_area': 'IND',
                'company_code': '1001',
                'plant_id': random.choice(self.factories)['factory_id'] if self.factories else 'FAC-001',
                'responsible_person_id': random.choice(self.employees)['employee_id'] if self.employees else f"EMP-{i:06d}",
                'cost_center_category': random.choice(categories),
                'parent_cost_center_id': None if i <= 5 else f"CC-{random.randint(1, i-1):04d}",  # Only leaf nodes have no parent
                'is_active': True,
                'valid_from': (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d'),
                'created_at': (datetime.now() - timedelta(days=random.randint(30, 365))).strftime('%Y-%m-%d %H:%M:%S')
            }
            self.data['cost_centers'].append(cost_center)
        
        print(f"Generated {len(self.data['cost_centers'])} cost centers")
    
    def generate_journal_entries(self, start_date, days):
        """Generate journal entries"""
        print(f"Generating {days} days of journal entries...")
        
        current_date = start_date
        document_types = ['SA', 'PA', 'ZZ', 'IV']  # Sales, Purchasing, Manual, Internal
        
        for day in range(days):
            # 3-8 entries per day
            num_entries = random.randint(3, 8)
            
            for _ in range(num_entries):
                entry_date = current_date + timedelta(hours=random.randint(8, 17))
                fiscal_period = (entry_date.month - 1) // 3 + 1
                
                entry = {
                    'journal_entry_id': f"JE-{entry_date.strftime('%Y%m%d')}-{self.gl_entry_counter:05d}",
                    'document_number': f"DOC-{entry_date.strftime('%Y%m%d')}-{self.gl_entry_counter:04d}",
                    'document_type': random.choice(document_types),
                    'posting_date': entry_date.strftime('%Y-%m-%d'),
                    'document_date': entry_date.strftime('%Y-%m-%d'),
                    'posting_period_id': f"FP-{entry_date.year}-{entry_date.month:02d}",
                    'fiscal_year': entry_date.year,
                    'fiscal_period': entry_date.month,
                    'company_code': '1001',
                    'document_header_text': f"Journal entry for {entry_date.strftime('%d-%b-%Y')}",
                    'currency': 'INR',
                    'source_system': random.choice(['ERP', 'MES', 'WMS']),
                    'source_module': random.choice(['Sales', 'Purchasing', 'Inventory', 'Production']),
                    'posting_status': 'posted',
                    'is_reversed': False,
                    'posted_by': f"EMP-{random.randint(1000, 2000):06d}",
                    'created_at': entry_date.strftime('%Y-%m-%d %H:%M:%S')
                }
                
                # Generate line items
                num_lines = random.randint(2, 5)
                total_debit = 0
                total_credit = 0
                lines = []
                
                for line_num in range(1, num_lines + 1):
                    # Alternate debit/credit
                    if line_num % 2 == 1:
                        debit = round(random.uniform(1000, 50000), 2)
                        credit = 0
                    else:
                        debit = 0
                        credit = round(random.uniform(1000, 50000), 2)
                    
                    total_debit += debit
                    total_credit += credit
                    
                    line = {
                        'entry_line_id': f"{entry['journal_entry_id']}-{line_num}",
                        'journal_entry_id': entry['journal_entry_id'],
                        'line_number': line_num,
                        'gl_account': random.choice(self.data['chart_of_accounts'])['gl_account'] if self.data['chart_of_accounts'] else '1001',
                        'account_name': f"Account {random.randint(1, 100)}",
                        'debit_amount': debit,
                        'credit_amount': credit,
                        'currency': 'INR',
                        'exchange_rate': 1.0,
                        'cost_center_id': random.choice(self.data['cost_centers'])['cost_center_id'] if self.data['cost_centers'] else None,
                        'profit_center': None,
                        'line_description': f"Line item {line_num}",
                        'assignment_field': None,
                        'reference_number': None,
                        'tax_code': None,
                        'tax_amount': None,
                        'tax_percentage': None,
                        'posting_key': '40' if debit > 0 else '50',
                        'clearing_document_number': None,
                        'clearing_date': None,
                        'created_at': entry_date.strftime('%Y-%m-%d %H:%M:%S')
                    }
                    lines.append(line)
                
                entry['total_debit'] = total_debit
                entry['total_credit'] = total_credit
                
                self.data['journal_entries'].append(entry)
                self.data['journal_entry_lines'].extend(lines)
                self.gl_entry_counter += 1
            
            current_date += timedelta(days=1)
        
        print(f"Generated {len(self.data['journal_entries'])} journal entries with {len(self.data['journal_entry_lines'])} lines")
    
    def generate_account_balances(self):
        """Generate account balances"""
        print("Generating account balances...")
        
        for period in self.data['fiscal_periods'][1:]:  # Skip opening period
            for account in self.data['chart_of_accounts'][:30]:  # Sample accounts
                balance = {
                    'balance_id': f"AB-{period['fiscal_period_id']}-{account['gl_account']}",
                    'fiscal_period_id': period['fiscal_period_id'],
                    'fiscal_year': period['fiscal_year'],
                    'period_number': period['period_number'],
                    'gl_account': account['gl_account'],
                    'company_code': '1001',
                    'opening_debit': round(random.uniform(0, 100000), 2),
                    'opening_credit': round(random.uniform(0, 100000), 2),
                    'period_debit': round(random.uniform(0, 50000), 2),
                    'period_credit': round(random.uniform(0, 50000), 2),
                    'closing_debit': round(random.uniform(0, 150000), 2),
                    'closing_credit': round(random.uniform(0, 150000), 2),
                    'currency': 'INR',
                    'is_reconciled': random.choice([True, False]),
                    'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                self.data['account_balances'].append(balance)
        
        print(f"Generated {len(self.data['account_balances'])} account balances")
    
    def generate_cost_center_balances(self):
        """Generate cost center balances"""
        print("Generating cost center balances...")
        
        for period in self.data['fiscal_periods'][1:]:
            for cc in self.data['cost_centers']:
                balance = {
                    'balance_id': f"CCB-{period['fiscal_period_id']}-{cc['cost_center_id']}",
                    'fiscal_period_id': period['fiscal_period_id'],
                    'fiscal_year': period['fiscal_year'],
                    'period_number': period['period_number'],
                    'cost_center_id': cc['cost_center_id'],
                    'cost_center_code': cc['cost_center_code'],
                    'opening_balance': round(random.uniform(10000, 100000), 2),
                    'period_charges': round(random.uniform(5000, 50000), 2),
                    'period_allocations': round(random.uniform(0, 30000), 2),
                    'closing_balance': round(random.uniform(15000, 120000), 2),
                    'currency': 'INR',
                    'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                self.data['cost_center_balances'].append(balance)
        
        print(f"Generated {len(self.data['cost_center_balances'])} cost center balances")
    
    def generate_exchange_rates(self, start_date, days):
        """Generate exchange rates"""
        print("Generating exchange rates...")
        
        currency_pairs = [('USD', 'INR'), ('EUR', 'INR'), ('GBP', 'INR'), ('JPY', 'INR')]
        
        current_date = start_date
        for day in range(0, days, 7):  # Weekly rates
            for from_cur, to_cur in currency_pairs:
                rate = {
                    'exchange_rate_id': f"EXR-{(current_date + timedelta(days=day)).strftime('%Y%m%d')}-{from_cur}{to_cur}",
                    'rate_date': (current_date + timedelta(days=day)).strftime('%Y-%m-%d'),
                    'from_currency': from_cur,
                    'to_currency': to_cur,
                    'exchange_rate': round(random.uniform(70, 100), 4),
                    'rate_source': 'Bloomberg',
                    'is_active': True,
                    'created_at': (current_date + timedelta(days=day)).strftime('%Y-%m-%d %H:%M:%S')
                }
                self.data['exchange_rates'].append(rate)
        
        print(f"Generated {len(self.data['exchange_rates'])} exchange rates")
    
    def generate_gl_posting_rules(self):
        """Generate GL posting rules"""
        print("Generating GL posting rules...")
        
        for i in range(10):
            rule = {
                'rule_id': f"RULE-{i+1:04d}",
                'rule_name': f"Posting Rule {i+1}",
                'source_system': random.choice(['ERP', 'MES', 'WMS']),
                'source_document_type': random.choice(['Purchase Order', 'Sales Order', 'Goods Receipt']),
                'trigger_event': random.choice(['document_posted', 'goods_receipt', 'invoice']),
                'debit_account': random.choice(self.data['chart_of_accounts'])['gl_account'] if self.data['chart_of_accounts'] else '1001',
                'credit_account': random.choice(self.data['chart_of_accounts'])['gl_account'] if self.data['chart_of_accounts'] else '2001',
                'cost_center_id': random.choice(self.data['cost_centers'])['cost_center_id'] if self.data['cost_centers'] else 'CC-0001',
                'is_automated': True,
                'is_mandatory': random.choice([True, False]),
                'is_active': True,
                'created_at': (datetime.now() - timedelta(days=random.randint(30, 365))).strftime('%Y-%m-%d %H:%M:%S')
            }
            self.data['gl_posting_rules'].append(rule)
        
        print(f"Generated {len(self.data['gl_posting_rules'])} GL posting rules")
    
    def generate_budget_templates(self):
        """Generate budget templates"""
        print("Generating budget templates...")
        
        for year in [2024, 2025]:
            for quarter in range(1, 5):
                budget = {
                    'budget_template_id': f"BUDGET-{year}-Q{quarter}",
                    'budget_name': f"Operating Budget {year} Q{quarter}",
                    'budget_year': year,
                    'budget_type': random.choice(['static', 'rolling', 'flex']),
                    'valid_from': f"{year}-{(quarter-1)*3+1:02d}-01",
                    'valid_to': f"{year}-{min((quarter)*3+1, 12):02d}-{min(28, 31)}",
                    'responsible_person_id': random.choice(self.employees)['employee_id'] if self.employees else f"EMP-{random.randint(1, 100):06d}",
                    'budget_status': 'approved' if year < 2024 or quarter <= datetime.now().month // 3 else 'draft',
                    'company_code': '1001',
                    'created_at': (datetime(year, (quarter-1)*3+1, 1) - timedelta(days=30)).strftime('%Y-%m-%d %H:%M:%S')
                }
                self.data['budget_templates'].append(budget)
        
        print(f"Generated {len(self.data['budget_templates'])} budget templates")
    
    def generate_budget_lines(self):
        """Generate budget lines"""
        print("Generating budget lines...")
        
        for budget in self.data['budget_templates']:
            for account in self.data['chart_of_accounts'][:15]:
                for cc in self.data['cost_centers'][:5]:
                    line = {
                        'budget_line_id': f"BL-{budget['budget_template_id']}-{account['gl_account']}-{cc['cost_center_id']}",
                        'budget_template_id': budget['budget_template_id'],
                        'gl_account': account['gl_account'],
                        'cost_center_id': cc['cost_center_id'],
                        'period_1_budget': round(random.uniform(1000, 100000), 2),
                        'period_2_budget': round(random.uniform(1000, 100000), 2),
                        'period_3_budget': round(random.uniform(1000, 100000), 2),
                        'period_4_budget': round(random.uniform(1000, 100000), 2),
                        'currency': 'INR',
                        'created_at': budget['created_at']
                    }
                    self.data['budget_lines'].append(line)
        
        print(f"Generated {len(self.data['budget_lines'])} budget lines")
    
    def generate_budget_vs_actual(self):
        """Generate budget vs actual"""
        print("Generating budget vs actual...")
        
        # Ensure we have budget lines and fiscal periods
        if not self.data['budget_lines']:
            print("  ⚠ Skipping: No budget lines generated")
            return
        
        counter = 0
        for period in self.data['fiscal_periods']:
            for budget_line in self.data['budget_lines'][:10]:  # Sample budget lines
                counter += 1
                bva = {
                    'bva_id': f"BVA-{period['fiscal_period_id']}-{budget_line['cost_center_id']}-{counter:04d}",
                    'fiscal_period_id': period['fiscal_period_id'],
                    'fiscal_year': period['fiscal_year'],
                    'period_number': period['period_number'],
                    'cost_center_id': budget_line['cost_center_id'],
                    'gl_account': budget_line['gl_account'],
                    'company_code': '1001',
                    'budget_amount': budget_line['period_1_budget'],
                    'actual_amount': round(random.uniform(budget_line['period_1_budget'] * 0.8, budget_line['period_1_budget'] * 1.2), 2),
                    'currency': 'INR',
                    'variance_status': random.choice(['favorable', 'unfavorable']),
                    'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                bva['variance_amount'] = bva['actual_amount'] - bva['budget_amount']
                bva['variance_percentage'] = round((bva['variance_amount'] / bva['budget_amount'] * 100), 2) if bva['budget_amount'] != 0 else 0
                self.data['budget_vs_actual'].append(bva)
        
        print(f"Generated {len(self.data['budget_vs_actual'])} budget vs actual records")
    
    def generate_income_statement_mappings(self):
        """Generate income statement mappings"""
        print("Generating income statement mappings...")
        
        income_items = [
            'Gross Revenue', 'Cost of Goods Sold', 'Gross Profit',
            'Operating Expenses', 'Operating Profit', 'Finance Costs',
            'Profit Before Tax', 'Income Tax', 'Net Profit'
        ]
        
        for i, item in enumerate(income_items, 1):
            for account in self.data['chart_of_accounts'][:5]:
                mapping = {
                    'mapping_id': f"ISM-{i:02d}-{account['gl_account']}",
                    'mapping_name': f"Income Statement Mapping {i}",
                    'gl_account': account['gl_account'],
                    'income_statement_line': item,
                    'income_statement_sequence': i * 10,
                    'company_code': '1001',
                    'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                self.data['income_statement_mappings'].append(mapping)
        
        print(f"Generated {len(self.data['income_statement_mappings'])} income statement mappings")
    
    def generate_balance_sheet_mappings(self):
        """Generate balance sheet mappings"""
        print("Generating balance sheet mappings...")
        
        bs_sections = {
            'Assets': ['Current Assets', 'Fixed Assets', 'Intangible Assets', 'Investments'],
            'Liabilities': ['Current Liabilities', 'Long-term Liabilities'],
            'Equity': ['Share Capital', 'Retained Earnings', 'Reserves']
        }
        
        sequence = 1
        for section, lines in bs_sections.items():
            for line in lines:
                for account in self.data['chart_of_accounts'][:3]:
                    mapping = {
                        'mapping_id': f"BSM-{sequence:03d}-{account['gl_account']}",
                        'mapping_name': f"Balance Sheet Mapping {sequence}",
                        'gl_account': account['gl_account'],
                        'balance_sheet_section': section,
                        'balance_sheet_line': line,
                        'balance_sheet_sequence': sequence,
                        'company_code': '1001',
                        'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    }
                    self.data['balance_sheet_mappings'].append(mapping)
                    sequence += 1
        
        print(f"Generated {len(self.data['balance_sheet_mappings'])} balance sheet mappings")
    
    def generate_intercompany_transactions(self, start_date, days):
        """Generate intercompany transactions"""
        print("Generating intercompany transactions...")
        
        companies = ['1001', '1002', '1003']
        current_date = start_date
        
        for day in range(0, days, 7):
            for _ in range(random.randint(1, 3)):
                sending = random.choice(companies)
                receiving = random.choice([c for c in companies if c != sending])
                
                # Use actual journal entry IDs if available
                parent_je_id = None
                if self.data['journal_entries']:
                    parent_je_id = random.choice(self.data['journal_entries'])['journal_entry_id']
                
                ic_trans = {
                    'ic_transaction_id': f"ICT-{(current_date + timedelta(days=day)).strftime('%Y%m%d')}-{random.randint(1000, 9999)}",
                    'parent_journal_entry_id': parent_je_id,
                    'sending_company': sending,
                    'receiving_company': receiving,
                    'sending_account': random.choice(self.data['chart_of_accounts'])['gl_account'] if self.data['chart_of_accounts'] else '1001',
                    'receiving_account': random.choice(self.data['chart_of_accounts'])['gl_account'] if self.data['chart_of_accounts'] else '1001',
                    'transaction_amount': round(random.uniform(10000, 500000), 2),
                    'currency': 'INR',
                    'transaction_date': (current_date + timedelta(days=day)).strftime('%Y-%m-%d'),
                    'is_settled': random.choice([True, False]),
                    'created_at': (current_date + timedelta(days=day)).strftime('%Y-%m-%d %H:%M:%S')
                }
                self.data['intercompany_transactions'].append(ic_trans)
        
        print(f"Generated {len(self.data['intercompany_transactions'])} intercompany transactions")
    
    def generate_account_reconciliations(self):
        """Generate account reconciliations"""
        print("Generating account reconciliations...")
        
        for period in self.data['fiscal_periods'][1:5]:
            for account in self.data['chart_of_accounts'][:10]:
                recon = {
                    'reconciliation_id': f"RECON-{period['fiscal_period_id']}-{account['gl_account']}",
                    'gl_account': account['gl_account'],
                    'fiscal_period_id': period['fiscal_period_id'],
                    'gl_balance': round(random.uniform(1000, 100000), 2),
                    'external_balance': round(random.uniform(1000, 100000), 2),
                    'external_source': random.choice(['Bank', 'Supplier', 'Customer']),
                    'difference': 0,
                    'is_reconciled': random.choice([True, False]),
                    'reconciliation_date': (datetime.strptime(period['period_end_date'], '%Y-%m-%d') + timedelta(days=5)).strftime('%Y-%m-%d') if random.random() > 0.2 else None,
                    'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                recon['difference'] = recon['external_balance'] - recon['gl_balance']
                self.data['account_reconciliations'].append(recon)
        
        print(f"Generated {len(self.data['account_reconciliations'])} account reconciliations")
    
    def generate_accruals_deferrals(self, start_date, days):
        """Generate accruals and deferrals"""
        print("Generating accruals and deferrals...")
        
        current_date = start_date
        for day in range(0, days, 30):
            for _ in range(random.randint(1, 3)):
                accrual = {
                    'accrual_id': f"ACR-{(current_date + timedelta(days=day)).strftime('%Y%m%d')}-{random.randint(1000, 9999)}",
                    'accrual_type': random.choice(['accrual', 'deferral']),
                    'accrual_name': f"Accrual {(current_date + timedelta(days=day)).strftime('%d-%b-%Y')}",
                    'expense_account': random.choice(self.data['chart_of_accounts'])['gl_account'] if self.data['chart_of_accounts'] else '6001',
                    'balance_sheet_account': random.choice(self.data['chart_of_accounts'])['gl_account'] if self.data['chart_of_accounts'] else '1300',
                    'accrual_amount': round(random.uniform(5000, 100000), 2),
                    'currency': 'INR',
                    'accrual_month': (current_date + timedelta(days=day)).month,
                    'accrual_year': (current_date + timedelta(days=day)).year,
                    'allocation_months': random.randint(3, 12),
                    'is_posted': True,
                    'is_reversed': False,
                    'created_at': (current_date + timedelta(days=day)).strftime('%Y-%m-%d %H:%M:%S')
                }
                self.data['accruals_deferrals'].append(accrual)
        
        print(f"Generated {len(self.data['accruals_deferrals'])} accruals and deferrals")
    
    def generate_depreciation(self):
        """Generate depreciation master and schedules"""
        print("Generating depreciation data...")
        
        # Depreciation master
        for i in range(1, 11):
            master = {
                'depreciation_id': f"DEPR-{i:04d}",
                'fixed_asset_id': f"ASSET-{i:04d}",
                'depreciation_method': random.choice(['straight_line', 'declining_balance']),
                'depreciation_rate': round(random.uniform(5, 25), 2),
                'depreciation_expense_account': random.choice(self.data['chart_of_accounts'])['gl_account'] if self.data['chart_of_accounts'] else '6050',
                'accumulated_depreciation_account': random.choice(self.data['chart_of_accounts'])['gl_account'] if self.data['chart_of_accounts'] else '1600',
                'cost_amount': round(random.uniform(100000, 1000000), 2),
                'salvage_value': round(random.uniform(10000, 100000), 2),
                'useful_life_months': random.randint(60, 240),
                'created_at': (datetime.now() - timedelta(days=random.randint(30, 365))).strftime('%Y-%m-%d %H:%M:%S')
            }
            self.data['depreciation_master'].append(master)
            
            # Add schedules for each period
            for period in self.data['fiscal_periods'][1:]:
                schedule = {
                    'schedule_id': f"DEPR-SCH-{master['depreciation_id']}-{period['period_number']}",
                    'depreciation_id': master['depreciation_id'],
                    'fiscal_period_id': period['fiscal_period_id'],
                    'depreciation_amount': round(master['cost_amount'] * (master['depreciation_rate'] / 100) / 12, 2),
                    'accumulated_depreciation': round(random.uniform(10000, master['cost_amount']), 2),
                    'book_value': master['cost_amount'] - round(random.uniform(10000, master['cost_amount']), 2),
                    'is_posted': period['period_status'] == 'locked',
                    'created_at': period['period_start_date'] + ' 00:00:00'
                }
                self.data['depreciation_schedules'].append(schedule)
        
        print(f"Generated {len(self.data['depreciation_master'])} depreciation masters with {len(self.data['depreciation_schedules'])} schedules")
    
    def generate_cash_flow_forecast(self, start_date, days):
        """Generate cash flow forecasts"""
        print("Generating cash flow forecasts...")
        
        current_date = start_date
        for month in range(3):
            forecast = {
                'forecast_id': f"CF-{(current_date + timedelta(days=month*30)).strftime('%Y%m')}",
                'forecast_month': (current_date + timedelta(days=month*30)).month,
                'forecast_year': (current_date + timedelta(days=month*30)).year,
                'company_code': '1001',
                'operating_cash_in': round(random.uniform(100000, 500000), 2),
                'operating_cash_out': round(random.uniform(50000, 300000), 2),
                'investing_cash_in': round(random.uniform(0, 100000), 2),
                'investing_cash_out': round(random.uniform(0, 50000), 2),
                'financing_cash_in': round(random.uniform(0, 100000), 2),
                'financing_cash_out': round(random.uniform(0, 50000), 2),
                'opening_cash_balance': round(random.uniform(50000, 500000), 2),
                'is_confirmed': True,
                'created_at': (current_date + timedelta(days=month*30)).strftime('%Y-%m-%d %H:%M:%S')
            }
            
            # Calculate net and closing
            forecast['net_cash_flow'] = (forecast['operating_cash_in'] + forecast['investing_cash_in'] + forecast['financing_cash_in'] -
                                        forecast['operating_cash_out'] - forecast['investing_cash_out'] - forecast['financing_cash_out'])
            forecast['closing_cash_balance'] = forecast['opening_cash_balance'] + forecast['net_cash_flow']
            
            self.data['cash_flow_forecast'].append(forecast)
        
        print(f"Generated {len(self.data['cash_flow_forecast'])} cash flow forecasts")
    
    def generate_tax_calculations(self):
        """Generate tax calculations"""
        print("Generating tax calculations...")
        
        for period in self.data['fiscal_periods'][1:]:
            for tax_type in ['income_tax', 'gst', 'sales_tax']:
                tax_calc = {
                    'tax_calc_id': f"TAX-{period['fiscal_period_id']}-{tax_type[:3].upper()}",
                    'fiscal_period_id': period['fiscal_period_id'],
                    'fiscal_year': period['fiscal_year'],
                    'period_number': period['period_number'],
                    'company_code': '1001',
                    'tax_type': tax_type,
                    'taxable_amount': round(random.uniform(100000, 1000000), 2),
                    'tax_percentage': round(random.uniform(5, 30), 2),
                    'is_calculated': True,
                    'is_filed': period['period_status'] == 'locked',
                    'created_at': period['period_start_date'] + ' 00:00:00'
                }
                tax_calc['tax_amount'] = round(tax_calc['taxable_amount'] * tax_calc['tax_percentage'] / 100, 2)
                self.data['tax_calculations'].append(tax_calc)
        
        print(f"Generated {len(self.data['tax_calculations'])} tax calculations")
    
    def generate_profitability_analysis(self, start_date, days):
        """Generate profitability analysis"""
        print("Generating profitability analysis...")
        
        current_date = start_date
        for month in range(3):
            analysis = {
                'profitability_id': f"PROF-{(current_date + timedelta(days=month*30)).strftime('%Y%m')}",
                'fiscal_period_id': f"FP-{(current_date + timedelta(days=month*30)).year}-{(current_date + timedelta(days=month*30)).month:02d}",
                'fiscal_year': (current_date + timedelta(days=month*30)).year,
                'period_number': (current_date + timedelta(days=month*30)).month,
                'business_unit': f"BU-{random.randint(1, 5)}",
                'product_line': f"PL-{random.randint(1, 10)}",
                'revenue': round(random.uniform(500000, 2000000), 2),
                'cost_of_goods_sold': round(random.uniform(300000, 1000000), 2),
                'selling_general_admin': round(random.uniform(100000, 500000), 2),
                'interest_expense': round(random.uniform(10000, 50000), 2),
                'tax_expense': round(random.uniform(20000, 100000), 2),
                'currency': 'INR',
                'created_at': (current_date + timedelta(days=month*30)).strftime('%Y-%m-%d %H:%M:%S')
            }
            
            # Calculate derived values
            analysis['gross_profit'] = analysis['revenue'] - analysis['cost_of_goods_sold']
            analysis['gross_profit_margin'] = round((analysis['gross_profit'] / analysis['revenue'] * 100), 2)
            analysis['operating_profit'] = analysis['gross_profit'] - analysis['selling_general_admin']
            analysis['operating_margin'] = round((analysis['operating_profit'] / analysis['revenue'] * 100), 2)
            analysis['net_profit'] = analysis['operating_profit'] - analysis['interest_expense'] - analysis['tax_expense']
            analysis['net_profit_margin'] = round((analysis['net_profit'] / analysis['revenue'] * 100), 2)
            
            self.data['profitability_analysis'].append(analysis)
        
        print(f"Generated {len(self.data['profitability_analysis'])} profitability analyses")
    
    def generate_financial_statements(self, start_date, days):
        """Generate financial statements"""
        print("Generating financial statements...")
        
        for period in self.data['fiscal_periods'][1:4]:  # Last 3 periods
            for stmt_type in ['income_statement', 'balance_sheet']:
                stmt = {
                    'statement_id': f"STMT-{period['fiscal_period_id']}-{stmt_type[:2].upper()}",
                    'fiscal_period_id': period['fiscal_period_id'],
                    'fiscal_year': period['fiscal_year'],
                    'period_number': period['period_number'],
                    'company_code': '1001',
                    'statement_type': stmt_type,
                    'currency': 'INR',
                    'total_revenue': round(random.uniform(1000000, 5000000), 2) if stmt_type == 'income_statement' else 0,
                    'total_expenses': round(random.uniform(500000, 3000000), 2) if stmt_type == 'income_statement' else 0,
                    'total_assets': round(random.uniform(5000000, 20000000), 2) if stmt_type == 'balance_sheet' else 0,
                    'total_liabilities': round(random.uniform(1000000, 10000000), 2) if stmt_type == 'balance_sheet' else 0,
                    'total_equity': round(random.uniform(1000000, 10000000), 2) if stmt_type == 'balance_sheet' else 0,
                    'statement_status': random.choice(['draft', 'reviewed', 'approved']) if period['period_status'] == 'locked' else 'draft',
                    'created_at': period['period_end_date'] + ' 00:00:00'
                }
                
                if stmt_type == 'income_statement':
                    stmt['net_income'] = stmt['total_revenue'] - stmt['total_expenses']
                
                self.data['financial_statements'].append(stmt)
        
        print(f"Generated {len(self.data['financial_statements'])} financial statements")
    
    def generate_financial_ratios(self, start_date, days):
        """Generate financial ratios"""
        print("Generating financial ratios...")
        
        for period in self.data['fiscal_periods'][1:]:
            ratios = {
                'ratio_id': f"RATIO-{period['fiscal_period_id']}",
                'fiscal_period_id': period['fiscal_period_id'],
                'fiscal_year': period['fiscal_year'],
                'company_code': '1001',
                'current_ratio': round(random.uniform(1.5, 3.0), 4),
                'quick_ratio': round(random.uniform(1.0, 2.5), 4),
                'debt_to_equity': round(random.uniform(0.5, 2.0), 4),
                'gross_profit_margin': round(random.uniform(20, 50), 4),
                'net_profit_margin': round(random.uniform(5, 25), 4),
                'roa': round(random.uniform(5, 20), 4),
                'roe': round(random.uniform(10, 30), 4),
                'asset_turnover': round(random.uniform(0.5, 2.5), 4),
                'created_at': period['period_start_date'] + ' 00:00:00'
            }
            self.data['financial_ratios'].append(ratios)
        
        print(f"Generated {len(self.data['financial_ratios'])} financial ratios")
    
    def generate_bank_reconciliations(self, start_date, days):
        """Generate bank reconciliations"""
        print("Generating bank reconciliations...")
        
        current_date = start_date
        for month in range(3):
            reconciliation = {
                'reconciliation_id': f"BR-{(current_date + timedelta(days=month*30)).strftime('%Y%m')}",
                'bank_account_id': f"BA-{random.randint(1, 5)}",
                'reconciliation_date': (current_date + timedelta(days=month*30)).strftime('%Y-%m-%d'),
                'bank_statement_date': (current_date + timedelta(days=month*30)).strftime('%Y-%m-%d'),
                'bank_statement_balance': round(random.uniform(100000, 1000000), 2),
                'bank_statement_currency': 'INR',
                'gl_balance': round(random.uniform(100000, 1000000), 2),
                'outstanding_checks': round(random.uniform(10000, 100000), 2),
                'outstanding_deposits': round(random.uniform(0, 50000), 2),
                'is_reconciled': random.choice([True, False]),
                'reconciliation_notes': 'Bank reconciliation notes',
                'created_at': (current_date + timedelta(days=month*30)).strftime('%Y-%m-%d %H:%M:%S')
            }
            reconciliation['difference_amount'] = reconciliation['bank_statement_balance'] - reconciliation['gl_balance']
            self.data['bank_reconciliations'].append(reconciliation)
        
        print(f"Generated {len(self.data['bank_reconciliations'])} bank reconciliations")
    
    def generate_ledger_control_accounts(self):
        """Generate ledger control accounts"""
        print("Generating ledger control accounts...")
        
        for i, account in enumerate(self.data['chart_of_accounts'][:15]):
            control = {
                'control_id': f"CTRL-{account['gl_account']}",
                'gl_account': account['gl_account'],
                'control_subsidiary_ledger': random.choice(['accounts_receivable', 'accounts_payable', 'inventory']),
                'gl_control_balance': round(random.uniform(10000, 500000), 2),
                'subsidiary_ledger_balance': round(random.uniform(10000, 500000), 2),
                'is_reconciled': random.choice([True, False]),
                'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            control['difference'] = control['subsidiary_ledger_balance'] - control['gl_control_balance']
            self.data['ledger_control_accounts'].append(control)
        
        print(f"Generated {len(self.data['ledger_control_accounts'])} ledger control accounts")
    
    def generate_transaction_approvals(self, start_date, days):
        """Generate transaction approvals"""
        print("Generating transaction approvals...")
        
        approval_statuses = ['pending', 'approved', 'rejected', 'draft']
        
        current_date = start_date
        for day in range(0, days, 1):  # Every day
            if random.random() > 0.4:  # 60% chance of approvals on a given day
                for _ in range(random.randint(2, 6)):
                    approval = {
                        'approval_id': f"APR-{(current_date + timedelta(days=day)).strftime('%Y%m%d')}-{random.randint(1000, 9999)}",
                        'transaction_type': random.choice(['journal_entry', 'budget', 'accrual', 'payment']),
                        'transaction_id': f"TXN-{random.randint(100000, 999999)}",
                        'approval_level': random.randint(1, 3),
                        'approval_status': random.choice(approval_statuses),
                        'approver_id': f"EMP-{random.randint(1000, 3000):06d}",
                        'approver_name': f"Approver {random.randint(1, 100)}",
                        'transaction_amount': round(random.uniform(10000, 500000), 2),
                        'transaction_date': (current_date + timedelta(days=day)).strftime('%Y-%m-%d'),
                        'approval_date': (current_date + timedelta(days=day + random.randint(0, 2))).strftime('%Y-%m-%d') if random.random() > 0.3 else None,
                        'approval_comments': f"Approval comment for transaction {random.randint(1000, 9999)}",
                        'created_at': (current_date + timedelta(days=day)).strftime('%Y-%m-%d %H:%M:%S')
                    }
                    self.data['transaction_approvals'].append(approval)
        
        print(f"Generated {len(self.data['transaction_approvals'])} transaction approvals")
    
    def generate_audit_trail(self, start_date, days):
        """Generate audit trail"""
        print("Generating audit trail...")
        
        operation_types = ['INSERT', 'UPDATE', 'DELETE']
        
        current_date = start_date
        for day in range(0, days, 2):
            for _ in range(random.randint(5, 20)):
                audit = {
                    'audit_id': f"AUD-{(current_date + timedelta(days=day)).strftime('%Y%m%d')}-{random.randint(10000, 99999)}",
                    'table_name': random.choice(['journal_entries', 'chart_of_accounts', 'cost_centers', 'budget_templates']),
                    'record_id': f"REC-{random.randint(1000000, 9999999)}",
                    'operation': random.choice(operation_types),
                    'operation_timestamp': (current_date + timedelta(days=day, hours=random.randint(8, 17))).strftime('%Y-%m-%d %H:%M:%S'),
                    'user_id': f"EMP-{random.randint(1000, 2000):06d}",
                    'user_name': f"User {random.randint(1, 100)}",
                    'old_values': f"Old value {random.randint(1, 100)}" if random.random() > 0.5 else None,
                    'new_values': f"New value {random.randint(1, 100)}" if random.random() > 0.5 else None,
                    'ip_address': f"192.168.1.{random.randint(1, 254)}",
                    'system_name': 'ERP System',
                    'created_at': (current_date + timedelta(days=day)).strftime('%Y-%m-%d %H:%M:%S')
                }
                self.data['audit_trail'].append(audit)
        
        print(f"Generated {len(self.data['audit_trail'])} audit trail records")
    
    def generate_financial_document_attachments(self, start_date, days):
        """Generate financial document attachments"""
        print("Generating financial document attachments...")
        
        document_types = ['PDF', 'Excel', 'Word', 'Image', 'JPEG']
        attachment_types = ['invoice', 'receipt', 'statement', 'supporting_document', 'approval_form']
        
        current_date = start_date
        for day in range(0, days, 7):
            for _ in range(random.randint(2, 8)):
                attachment = {
                    'attachment_id': f"ATT-{(current_date + timedelta(days=day)).strftime('%Y%m%d')}-{random.randint(1000, 9999)}",
                    'document_type': random.choice(attachment_types),
                    'journal_entry_id': random.choice(self.data['journal_entries'])['journal_entry_id'] if self.data['journal_entries'] else None,
                    'document_reference': f"DOC-{random.randint(100000, 999999)}",
                    'file_name': f"document_{random.randint(1, 1000)}.{random.choice(['pdf', 'xlsx', 'docx', 'jpg'])}",
                    'file_type': random.choice(document_types),
                    'file_size_kb': random.randint(50, 5000),
                    'upload_date': (current_date + timedelta(days=day)).strftime('%Y-%m-%d'),
                    'uploaded_by': f"EMP-{random.randint(1000, 2000):06d}",
                    'document_description': f"Financial document for {(current_date + timedelta(days=day)).strftime('%d-%b-%Y')}",
                    'is_archived': random.choice([True, False]),
                    'created_at': (current_date + timedelta(days=day)).strftime('%Y-%m-%d %H:%M:%S')
                }
                self.data['financial_document_attachments'].append(attachment)
        
        print(f"Generated {len(self.data['financial_document_attachments'])} financial document attachments")
    
    def save_to_json(self, output_file='genims_financial_data.json'):
        """Save data to JSON file"""
        print(f"\nSaving to {output_file}...")
        with open(output_file, 'w') as f:
            json.dump(self.data, f, indent=2)
        print(f"Financial data saved to {output_file}")
    
    def get_summary(self):
        """Return data summary"""
        summary = {}
        for key, value in self.data.items():
            summary[key] = len(value)
        return summary

if __name__ == '__main__':
    generator = FinancialDataGenerator()
    generator.generate(days=90)
    
    output_file = Path(__file__).parent / 'genims_financial_data.json'
    generator.save_to_json(str(output_file))
    
    summary = generator.get_summary()
    print("\n" + "="*60)
    print("FINANCIAL/GL DATA GENERATION SUMMARY")
    print("="*60)
    total_records = 0
    for table_name, count in summary.items():
        print(f"{table_name:40s}: {count:6d} records")
        total_records += count
    print("-"*60)
    print(f"{'TOTAL':40s}: {total_records:6d} records")
    print("="*60)
