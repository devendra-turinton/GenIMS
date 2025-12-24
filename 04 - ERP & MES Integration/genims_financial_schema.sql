-- ============================================================================
-- GenIMS Financial/GL Database Schema
-- Module: Financial Management & General Ledger
-- Database: genims_financial_db
-- Purpose: General Ledger, Financial Reporting, Accounting
-- ============================================================================

-- ============================================================================
-- TABLE 1: Chart of Accounts
-- ============================================================================
CREATE TABLE chart_of_accounts (
    gl_account VARCHAR(20) PRIMARY KEY,
    account_number VARCHAR(20) UNIQUE NOT NULL,
    account_name VARCHAR(200) NOT NULL,
    account_description TEXT,
    
    -- Account Type
    account_type VARCHAR(30), -- asset, liability, equity, revenue, expense, cost_of_sales
    sub_account_type VARCHAR(50), -- fixed_asset, current_asset, etc.
    
    -- Hierarchy
    account_group VARCHAR(50),
    parent_account VARCHAR(20), -- FK to chart_of_accounts
    
    -- Company
    company_code VARCHAR(10) NOT NULL,
    controlling_area VARCHAR(10),
    
    -- Account Status
    is_active BOOLEAN DEFAULT true,
    is_reconciliation_account BOOLEAN DEFAULT false,
    is_memo_account BOOLEAN DEFAULT false,
    is_trading_account BOOLEAN DEFAULT false,
    
    -- Validations
    valid_from DATE,
    valid_to DATE,
    
    -- Budget Info
    budget_available BOOLEAN DEFAULT false,
    cash_flow_relevant BOOLEAN DEFAULT false,
    
    -- Audit
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT fk_coa_parent FOREIGN KEY (parent_account) REFERENCES chart_of_accounts(gl_account)
);

-- ============================================================================
-- TABLE 2: Fiscal Periods
-- ============================================================================
CREATE TABLE fiscal_periods (
    fiscal_period_id VARCHAR(50) PRIMARY KEY,
    fiscal_year INTEGER NOT NULL,
    period_number INTEGER NOT NULL, -- 1-13 or 1-12
    period_name VARCHAR(50), -- January, Q1, etc.
    
    -- Period Range
    period_start_date DATE NOT NULL,
    period_end_date DATE NOT NULL,
    
    -- Quarter
    quarter_number INTEGER,
    
    -- Status
    period_status VARCHAR(20), -- open, locked, archived
    is_posting_period BOOLEAN DEFAULT true,
    posting_locked_date DATE,
    
    -- Company
    company_code VARCHAR(10) NOT NULL,
    
    -- Audit
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT unique_fiscal_period UNIQUE (fiscal_year, period_number, company_code)
);

-- ============================================================================
-- TABLE 3: Cost Centers
-- ============================================================================
CREATE TABLE cost_centers (
    cost_center_id VARCHAR(50) PRIMARY KEY,
    cost_center_code VARCHAR(50) UNIQUE NOT NULL,
    cost_center_name VARCHAR(200) NOT NULL,
    cost_center_description TEXT,
    
    -- Hierarchy
    controlling_area VARCHAR(10),
    cost_center_group VARCHAR(50),
    parent_cost_center_id VARCHAR(50),
    
    -- Assignment
    company_code VARCHAR(10) NOT NULL,
    business_area VARCHAR(10),
    plant_id VARCHAR(50),
    
    -- Responsible Person
    responsible_person_id VARCHAR(50),
    responsible_person_name VARCHAR(100),
    
    -- Category
    cost_center_category VARCHAR(50), -- production, service, admin, marketing, distribution
    
    -- Status
    is_active BOOLEAN DEFAULT true,
    valid_from DATE,
    valid_to DATE,
    
    -- Audit
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT fk_cc_parent FOREIGN KEY (parent_cost_center_id) REFERENCES cost_centers(cost_center_id)
);

-- ============================================================================
-- TABLE 4: Journal Entry Headers
-- ============================================================================
CREATE TABLE journal_entries (
    journal_entry_id VARCHAR(50) PRIMARY KEY,
    document_number VARCHAR(50) UNIQUE NOT NULL,
    document_type VARCHAR(10) NOT NULL, -- SA (Sales), PA (Purchasing), ZZ (Manual)
    
    -- Posting Details
    posting_date DATE NOT NULL,
    document_date DATE NOT NULL,
    posting_period_id VARCHAR(50) NOT NULL,
    fiscal_year INTEGER NOT NULL,
    fiscal_period INTEGER NOT NULL,
    
    -- Company
    company_code VARCHAR(10) NOT NULL,
    
    -- Description
    document_header_text VARCHAR(500),
    reference_document VARCHAR(50),
    
    -- Amount
    total_debit DECIMAL(15,2),
    total_credit DECIMAL(15,2),
    currency VARCHAR(3) DEFAULT 'INR',
    
    -- Source
    source_system VARCHAR(50), -- ERP, MES, WMS, MANUAL, API
    source_document_id VARCHAR(50),
    source_module VARCHAR(50), -- Sales, Purchasing, Inventory, Payroll
    
    -- Status
    posting_status VARCHAR(20), -- new, posted, reversed, deleted
    is_reversed BOOLEAN DEFAULT false,
    reversal_document_id VARCHAR(50),
    reversal_date DATE,
    
    -- User Info
    posted_by VARCHAR(50),
    approved_by VARCHAR(50),
    approval_date DATE,
    
    -- Audit
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT fk_je_posting_period FOREIGN KEY (posting_period_id) REFERENCES fiscal_periods(fiscal_period_id)
);

-- ============================================================================
-- TABLE 5: Journal Entry Line Items
-- ============================================================================
CREATE TABLE journal_entry_lines (
    entry_line_id VARCHAR(50) PRIMARY KEY,
    journal_entry_id VARCHAR(50) NOT NULL,
    line_number INTEGER NOT NULL,
    
    -- Account
    gl_account VARCHAR(20) NOT NULL,
    account_name VARCHAR(200),
    
    -- Amount
    debit_amount DECIMAL(15,2) DEFAULT 0,
    credit_amount DECIMAL(15,2) DEFAULT 0,
    currency VARCHAR(3) DEFAULT 'INR',
    exchange_rate DECIMAL(10,4) DEFAULT 1.0,
    
    -- Cost Assignment
    cost_center_id VARCHAR(50),
    profit_center VARCHAR(50),
    
    -- Description & Reference
    line_description VARCHAR(500),
    assignment_field VARCHAR(50),
    reference_number VARCHAR(50),
    
    -- Tax
    tax_code VARCHAR(5),
    tax_amount DECIMAL(15,2),
    tax_percentage DECIMAL(5,2),
    
    -- Posting Key
    posting_key VARCHAR(2), -- 40 (debit), 50 (credit) for GL
    
    -- Clearing
    clearing_document_number VARCHAR(50),
    clearing_date DATE,
    
    -- Audit
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT fk_jel_je FOREIGN KEY (journal_entry_id) REFERENCES journal_entries(journal_entry_id) ON DELETE CASCADE,
    CONSTRAINT fk_jel_account FOREIGN KEY (gl_account) REFERENCES chart_of_accounts(gl_account),
    CONSTRAINT fk_jel_cost_center FOREIGN KEY (cost_center_id) REFERENCES cost_centers(cost_center_id)
);

-- ============================================================================
-- TABLE 6: Account Balances (Period Snapshots)
-- ============================================================================
CREATE TABLE account_balances (
    balance_id VARCHAR(50) PRIMARY KEY,
    fiscal_period_id VARCHAR(50) NOT NULL,
    fiscal_year INTEGER NOT NULL,
    period_number INTEGER NOT NULL,
    
    -- Account
    gl_account VARCHAR(20) NOT NULL,
    company_code VARCHAR(10) NOT NULL,
    
    -- Balance
    opening_debit DECIMAL(15,2),
    opening_credit DECIMAL(15,2),
    period_debit DECIMAL(15,2),
    period_credit DECIMAL(15,2),
    closing_debit DECIMAL(15,2),
    closing_credit DECIMAL(15,2),
    
    -- Currency
    currency VARCHAR(3) DEFAULT 'INR',
    
    -- Reconciliation
    is_reconciled BOOLEAN DEFAULT false,
    reconciled_date DATE,
    reconciled_by VARCHAR(50),
    
    -- Audit
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT fk_ab_period FOREIGN KEY (fiscal_period_id) REFERENCES fiscal_periods(fiscal_period_id),
    CONSTRAINT fk_ab_account FOREIGN KEY (gl_account) REFERENCES chart_of_accounts(gl_account),
    CONSTRAINT unique_account_balance UNIQUE (fiscal_period_id, gl_account, company_code)
);

-- ============================================================================
-- TABLE 7: Cost Center Balances (Period Snapshots)
-- ============================================================================
CREATE TABLE cost_center_balances (
    balance_id VARCHAR(50) PRIMARY KEY,
    fiscal_period_id VARCHAR(50) NOT NULL,
    fiscal_year INTEGER NOT NULL,
    period_number INTEGER NOT NULL,
    
    -- Cost Center
    cost_center_id VARCHAR(50) NOT NULL,
    cost_center_code VARCHAR(50) NOT NULL,
    
    -- Balance
    opening_balance DECIMAL(15,2),
    period_charges DECIMAL(15,2),
    period_allocations DECIMAL(15,2),
    closing_balance DECIMAL(15,2),
    
    -- Currency
    currency VARCHAR(3) DEFAULT 'INR',
    
    -- Audit
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT fk_ccb_period FOREIGN KEY (fiscal_period_id) REFERENCES fiscal_periods(fiscal_period_id),
    CONSTRAINT fk_ccb_cost_center FOREIGN KEY (cost_center_id) REFERENCES cost_centers(cost_center_id),
    CONSTRAINT unique_cc_balance UNIQUE (fiscal_period_id, cost_center_id)
);

-- ============================================================================
-- TABLE 8: Exchange Rates
-- ============================================================================
CREATE TABLE exchange_rates (
    exchange_rate_id VARCHAR(50) PRIMARY KEY,
    rate_date DATE NOT NULL,
    from_currency VARCHAR(3) NOT NULL,
    to_currency VARCHAR(3) NOT NULL,
    
    -- Rates
    exchange_rate DECIMAL(10,6) NOT NULL,
    exchange_rate_inverse DECIMAL(10,6),
    
    -- Source
    rate_source VARCHAR(50), -- ECB, Bloomberg, System
    rate_type VARCHAR(10), -- Bid, Ask, Mid
    
    -- Status
    is_active BOOLEAN DEFAULT true,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT unique_exchange_rate UNIQUE (rate_date, from_currency, to_currency)
);

-- ============================================================================
-- TABLE 9: GL Posting Rules
-- ============================================================================
CREATE TABLE gl_posting_rules (
    rule_id VARCHAR(50) PRIMARY KEY,
    rule_name VARCHAR(100) NOT NULL,
    rule_description TEXT,
    
    -- Trigger
    source_system VARCHAR(50), -- ERP, MES, INVENTORY, PAYROLL
    source_document_type VARCHAR(50), -- Purchase Order, Sales Order, etc.
    
    -- Rule Logic
    trigger_event VARCHAR(100), -- document_posted, goods_receipt, invoice
    rule_condition VARCHAR(500),
    
    -- Posting Details
    debit_account VARCHAR(20),
    credit_account VARCHAR(20),
    
    -- Cost Assignment
    cost_center_id VARCHAR(50),
    
    -- Options
    is_automated BOOLEAN DEFAULT true,
    is_mandatory BOOLEAN DEFAULT true,
    allow_manual_override BOOLEAN DEFAULT false,
    
    -- Status
    is_active BOOLEAN DEFAULT true,
    valid_from DATE,
    valid_to DATE,
    
    -- Audit
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT fk_gpr_debit FOREIGN KEY (debit_account) REFERENCES chart_of_accounts(gl_account),
    CONSTRAINT fk_gpr_credit FOREIGN KEY (credit_account) REFERENCES chart_of_accounts(gl_account)
);

-- ============================================================================
-- TABLE 10: Budget Templates
-- ============================================================================
CREATE TABLE budget_templates (
    budget_template_id VARCHAR(50) PRIMARY KEY,
    budget_name VARCHAR(100) NOT NULL,
    budget_year INTEGER NOT NULL,
    
    -- Details
    budget_description TEXT,
    budget_type VARCHAR(30), -- static, rolling, flex, zero_based
    budget_basis VARCHAR(50), -- historical, target, negotiated
    
    -- Period
    valid_from DATE,
    valid_to DATE,
    
    -- Responsible Person
    responsible_person_id VARCHAR(50),
    responsible_person_name VARCHAR(100),
    
    -- Status
    budget_status VARCHAR(20), -- draft, submitted, approved, active, archived
    approval_date DATE,
    approved_by VARCHAR(50),
    
    -- Company
    company_code VARCHAR(10),
    
    -- Audit
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- TABLE 11: Budget Lines
-- ============================================================================
CREATE TABLE budget_lines (
    budget_line_id VARCHAR(50) PRIMARY KEY,
    budget_template_id VARCHAR(50) NOT NULL,
    line_number INTEGER,
    
    -- Account
    gl_account VARCHAR(20),
    cost_center_id VARCHAR(50),
    
    -- Budget Amount
    period_1_budget DECIMAL(15,2),
    period_2_budget DECIMAL(15,2),
    period_3_budget DECIMAL(15,2),
    period_4_budget DECIMAL(15,2),
    period_5_budget DECIMAL(15,2),
    period_6_budget DECIMAL(15,2),
    period_7_budget DECIMAL(15,2),
    period_8_budget DECIMAL(15,2),
    period_9_budget DECIMAL(15,2),
    period_10_budget DECIMAL(15,2),
    period_11_budget DECIMAL(15,2),
    period_12_budget DECIMAL(15,2),
    annual_budget DECIMAL(15,2),
    
    -- Currency
    currency VARCHAR(3) DEFAULT 'INR',
    
    -- Notes
    budget_notes TEXT,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT fk_bl_budget FOREIGN KEY (budget_template_id) REFERENCES budget_templates(budget_template_id) ON DELETE CASCADE,
    CONSTRAINT fk_bl_account FOREIGN KEY (gl_account) REFERENCES chart_of_accounts(gl_account)
);

-- ============================================================================
-- TABLE 12: Budget vs Actual
-- ============================================================================
CREATE TABLE budget_vs_actual (
    bva_id VARCHAR(50) PRIMARY KEY,
    fiscal_period_id VARCHAR(50) NOT NULL,
    fiscal_year INTEGER NOT NULL,
    period_number INTEGER NOT NULL,
    
    -- Account
    gl_account VARCHAR(20) NOT NULL,
    cost_center_id VARCHAR(50),
    
    -- Company
    company_code VARCHAR(10),
    
    -- Budget
    budget_amount DECIMAL(15,2),
    
    -- Actual
    actual_amount DECIMAL(15,2),
    
    -- Variance
    variance_amount DECIMAL(15,2),
    variance_percentage DECIMAL(5,2),
    variance_status VARCHAR(20), -- favorable, unfavorable, neutral
    
    -- Currency
    currency VARCHAR(3) DEFAULT 'INR',
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT fk_bva_period FOREIGN KEY (fiscal_period_id) REFERENCES fiscal_periods(fiscal_period_id),
    CONSTRAINT fk_bva_account FOREIGN KEY (gl_account) REFERENCES chart_of_accounts(gl_account)
);

-- ============================================================================
-- TABLE 13: Income Statement Mappings
-- ============================================================================
CREATE TABLE income_statement_mappings (
    mapping_id VARCHAR(50) PRIMARY KEY,
    mapping_name VARCHAR(100) NOT NULL,
    
    -- GL Account
    gl_account VARCHAR(20),
    
    -- Income Statement Line
    income_statement_line VARCHAR(100), -- Revenue, COGS, Operating Expenses, etc.
    income_statement_sequence INTEGER,
    
    -- Sub-line
    sub_line_description VARCHAR(200),
    
    -- Calculation
    calculation_type VARCHAR(30), -- sum, difference, percentage
    
    -- Company
    company_code VARCHAR(10),
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT fk_ism_account FOREIGN KEY (gl_account) REFERENCES chart_of_accounts(gl_account)
);

-- ============================================================================
-- TABLE 14: Balance Sheet Mappings
-- ============================================================================
CREATE TABLE balance_sheet_mappings (
    mapping_id VARCHAR(50) PRIMARY KEY,
    mapping_name VARCHAR(100) NOT NULL,
    
    -- GL Account
    gl_account VARCHAR(20),
    
    -- Balance Sheet Line
    balance_sheet_section VARCHAR(50), -- Assets, Liabilities, Equity
    balance_sheet_line VARCHAR(100),
    balance_sheet_sequence INTEGER,
    
    -- Sub-line
    sub_line_description VARCHAR(200),
    
    -- Company
    company_code VARCHAR(10),
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT fk_bsm_account FOREIGN KEY (gl_account) REFERENCES chart_of_accounts(gl_account)
);

-- ============================================================================
-- TABLE 15: Inter-company Transactions
-- ============================================================================
CREATE TABLE intercompany_transactions (
    ic_transaction_id VARCHAR(50) PRIMARY KEY,
    parent_journal_entry_id VARCHAR(50),
    
    -- Companies
    sending_company VARCHAR(10) NOT NULL,
    receiving_company VARCHAR(10) NOT NULL,
    
    -- Accounts
    sending_account VARCHAR(20),
    receiving_account VARCHAR(20),
    
    -- Amount
    transaction_amount DECIMAL(15,2),
    currency VARCHAR(3) DEFAULT 'INR',
    
    -- Transaction Details
    transaction_date DATE,
    transaction_description TEXT,
    
    -- Settlement
    is_settled BOOLEAN DEFAULT false,
    settlement_date DATE,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT fk_ict_je FOREIGN KEY (parent_journal_entry_id) REFERENCES journal_entries(journal_entry_id)
);

-- ============================================================================
-- TABLE 16: Account Reconciliation
-- ============================================================================
CREATE TABLE account_reconciliations (
    reconciliation_id VARCHAR(50) PRIMARY KEY,
    gl_account VARCHAR(20) NOT NULL,
    fiscal_period_id VARCHAR(50) NOT NULL,
    
    -- GL Balance
    gl_balance DECIMAL(15,2),
    
    -- External Balance
    external_balance DECIMAL(15,2),
    external_source VARCHAR(100), -- Bank, Supplier, Customer
    external_reference VARCHAR(50),
    
    -- Reconciliation
    difference DECIMAL(15,2),
    is_reconciled BOOLEAN DEFAULT false,
    reconciliation_notes TEXT,
    reconciled_by VARCHAR(50),
    reconciliation_date DATE,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT fk_ar_account FOREIGN KEY (gl_account) REFERENCES chart_of_accounts(gl_account),
    CONSTRAINT fk_ar_period FOREIGN KEY (fiscal_period_id) REFERENCES fiscal_periods(fiscal_period_id)
);

-- ============================================================================
-- TABLE 17: Accruals & Deferrals
-- ============================================================================
CREATE TABLE accruals_deferrals (
    accrual_id VARCHAR(50) PRIMARY KEY,
    accrual_type VARCHAR(20), -- accrual, deferral
    accrual_name VARCHAR(100) NOT NULL,
    
    -- GL Accounts
    expense_account VARCHAR(20),
    balance_sheet_account VARCHAR(20),
    
    -- Amount
    accrual_amount DECIMAL(15,2),
    currency VARCHAR(3) DEFAULT 'INR',
    
    -- Period
    accrual_month INTEGER,
    accrual_year INTEGER,
    allocation_months INTEGER,
    
    -- Status
    is_posted BOOLEAN DEFAULT false,
    posting_date DATE,
    
    -- Reversal
    is_reversed BOOLEAN DEFAULT false,
    reversal_date DATE,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT fk_ad_expense FOREIGN KEY (expense_account) REFERENCES chart_of_accounts(gl_account),
    CONSTRAINT fk_ad_balance FOREIGN KEY (balance_sheet_account) REFERENCES chart_of_accounts(gl_account)
);

-- ============================================================================
-- TABLE 18: Depreciation Master
-- ============================================================================
CREATE TABLE depreciation_master (
    depreciation_id VARCHAR(50) PRIMARY KEY,
    fixed_asset_id VARCHAR(50) NOT NULL,
    
    -- Depreciation Details
    depreciation_method VARCHAR(50), -- straight_line, declining_balance, sum_of_years, units_produced
    depreciation_rate DECIMAL(5,2),
    
    -- GL Accounts
    depreciation_expense_account VARCHAR(20),
    accumulated_depreciation_account VARCHAR(20),
    
    -- Period
    depreciation_start_month INTEGER,
    depreciation_start_year INTEGER,
    depreciation_end_month INTEGER,
    depreciation_end_year INTEGER,
    
    -- Amount
    cost_amount DECIMAL(15,2),
    salvage_value DECIMAL(15,2),
    useful_life_months INTEGER,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT fk_dm_expense FOREIGN KEY (depreciation_expense_account) REFERENCES chart_of_accounts(gl_account),
    CONSTRAINT fk_dm_accumulated FOREIGN KEY (accumulated_depreciation_account) REFERENCES chart_of_accounts(gl_account)
);

-- ============================================================================
-- TABLE 19: Depreciation Schedules
-- ============================================================================
CREATE TABLE depreciation_schedules (
    schedule_id VARCHAR(50) PRIMARY KEY,
    depreciation_id VARCHAR(50) NOT NULL,
    fiscal_period_id VARCHAR(50) NOT NULL,
    
    -- Amount
    depreciation_amount DECIMAL(15,2),
    accumulated_depreciation DECIMAL(15,2),
    
    -- Book Value
    book_value DECIMAL(15,2),
    
    -- Posting
    is_posted BOOLEAN DEFAULT false,
    posting_date DATE,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT fk_ds_depreciation FOREIGN KEY (depreciation_id) REFERENCES depreciation_master(depreciation_id),
    CONSTRAINT fk_ds_period FOREIGN KEY (fiscal_period_id) REFERENCES fiscal_periods(fiscal_period_id)
);

-- ============================================================================
-- TABLE 20: Cash Flow Forecast
-- ============================================================================
CREATE TABLE cash_flow_forecast (
    forecast_id VARCHAR(50) PRIMARY KEY,
    forecast_month INTEGER,
    forecast_year INTEGER,
    
    -- Company
    company_code VARCHAR(10),
    
    -- Categories
    operating_cash_in DECIMAL(15,2),
    operating_cash_out DECIMAL(15,2),
    investing_cash_in DECIMAL(15,2),
    investing_cash_out DECIMAL(15,2),
    financing_cash_in DECIMAL(15,2),
    financing_cash_out DECIMAL(15,2),
    
    -- Net
    net_cash_flow DECIMAL(15,2),
    opening_cash_balance DECIMAL(15,2),
    closing_cash_balance DECIMAL(15,2),
    
    -- Status
    is_confirmed BOOLEAN DEFAULT false,
    confirmed_by VARCHAR(50),
    confirmation_date DATE,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- TABLE 21: Tax Calculations
-- ============================================================================
CREATE TABLE tax_calculations (
    tax_calc_id VARCHAR(50) PRIMARY KEY,
    fiscal_period_id VARCHAR(50) NOT NULL,
    fiscal_year INTEGER,
    period_number INTEGER,
    
    -- Company
    company_code VARCHAR(10),
    
    -- Tax Type
    tax_type VARCHAR(50), -- income_tax, gst, sales_tax, vat
    
    -- Calculation
    taxable_amount DECIMAL(15,2),
    tax_percentage DECIMAL(5,2),
    tax_amount DECIMAL(15,2),
    
    -- GL Account
    tax_payable_account VARCHAR(20),
    tax_expense_account VARCHAR(20),
    
    -- Status
    is_calculated BOOLEAN DEFAULT false,
    is_filed BOOLEAN DEFAULT false,
    filing_date DATE,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT fk_tc_period FOREIGN KEY (fiscal_period_id) REFERENCES fiscal_periods(fiscal_period_id)
);

-- ============================================================================
-- TABLE 22: Profitability Analysis
-- ============================================================================
CREATE TABLE profitability_analysis (
    profitability_id VARCHAR(50) PRIMARY KEY,
    fiscal_period_id VARCHAR(50) NOT NULL,
    fiscal_year INTEGER,
    period_number INTEGER,
    
    -- Segment
    business_unit VARCHAR(50),
    product_line VARCHAR(100),
    
    -- Revenue
    revenue DECIMAL(15,2),
    cost_of_goods_sold DECIMAL(15,2),
    gross_profit DECIMAL(15,2),
    gross_profit_margin DECIMAL(5,2),
    
    -- Operating Expenses
    selling_general_admin DECIMAL(15,2),
    operating_profit DECIMAL(15,2),
    operating_margin DECIMAL(5,2),
    
    -- Net
    interest_expense DECIMAL(15,2),
    tax_expense DECIMAL(15,2),
    net_profit DECIMAL(15,2),
    net_profit_margin DECIMAL(5,2),
    
    -- Currency
    currency VARCHAR(3) DEFAULT 'INR',
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- TABLE 23: Financial Statements (Period)
-- ============================================================================
CREATE TABLE financial_statements (
    statement_id VARCHAR(50) PRIMARY KEY,
    fiscal_period_id VARCHAR(50) NOT NULL,
    fiscal_year INTEGER,
    period_number INTEGER,
    
    -- Company
    company_code VARCHAR(10),
    
    -- Statement Type
    statement_type VARCHAR(30), -- income_statement, balance_sheet, cash_flow
    
    -- Currency
    currency VARCHAR(3) DEFAULT 'INR',
    
    -- Total Values
    total_assets DECIMAL(15,2),
    total_liabilities DECIMAL(15,2),
    total_equity DECIMAL(15,2),
    
    total_revenue DECIMAL(15,2),
    total_expenses DECIMAL(15,2),
    net_income DECIMAL(15,2),
    
    -- Status
    statement_status VARCHAR(20), -- draft, reviewed, approved, published
    approved_by VARCHAR(50),
    approval_date DATE,
    
    -- Audit
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- TABLE 24: Transaction Approvals
-- ============================================================================
CREATE TABLE transaction_approvals (
    approval_id VARCHAR(50) PRIMARY KEY,
    transaction_type VARCHAR(50), -- journal_entry, budget, accrual
    transaction_id VARCHAR(50),
    
    -- Approval
    approval_level INTEGER, -- 1, 2, 3 for multi-level approval
    approval_status VARCHAR(20), -- pending, approved, rejected
    
    -- Approver
    approver_id VARCHAR(50),
    approver_name VARCHAR(100),
    approval_date DATE,
    approval_comments TEXT,
    
    -- Transaction Details
    transaction_amount DECIMAL(15,2),
    transaction_date DATE,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- TABLE 25: Audit Trail
-- ============================================================================
CREATE TABLE audit_trail (
    audit_id VARCHAR(50) PRIMARY KEY,
    table_name VARCHAR(100),
    record_id VARCHAR(50),
    
    -- Change Details
    operation VARCHAR(20), -- INSERT, UPDATE, DELETE
    operation_timestamp TIMESTAMP,
    
    -- User
    user_id VARCHAR(50),
    user_name VARCHAR(100),
    
    -- Old and New Values
    old_values TEXT,
    new_values TEXT,
    
    -- IP and System
    ip_address VARCHAR(20),
    system_name VARCHAR(100),
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- TABLE 26: Financial Ratios
-- ============================================================================
CREATE TABLE financial_ratios (
    ratio_id VARCHAR(50) PRIMARY KEY,
    fiscal_period_id VARCHAR(50) NOT NULL,
    fiscal_year INTEGER,
    
    -- Company
    company_code VARCHAR(10),
    
    -- Liquidity Ratios
    current_ratio DECIMAL(10,4),
    quick_ratio DECIMAL(10,4),
    cash_ratio DECIMAL(10,4),
    
    -- Profitability Ratios
    gross_profit_margin DECIMAL(10,4),
    operating_profit_margin DECIMAL(10,4),
    net_profit_margin DECIMAL(10,4),
    roa DECIMAL(10,4), -- Return on Assets
    roe DECIMAL(10,4), -- Return on Equity
    
    -- Leverage Ratios
    debt_to_equity DECIMAL(10,4),
    debt_to_assets DECIMAL(10,4),
    equity_multiplier DECIMAL(10,4),
    
    -- Efficiency Ratios
    asset_turnover DECIMAL(10,4),
    inventory_turnover DECIMAL(10,4),
    receivables_turnover DECIMAL(10,4),
    
    -- Growth Ratios
    revenue_growth_percentage DECIMAL(10,4),
    profit_growth_percentage DECIMAL(10,4),
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- TABLE 27: Bank Reconciliation
-- ============================================================================
CREATE TABLE bank_reconciliations (
    reconciliation_id VARCHAR(50) PRIMARY KEY,
    bank_account_id VARCHAR(50),
    reconciliation_date DATE NOT NULL,
    
    -- Bank Details
    bank_statement_date DATE,
    bank_statement_balance DECIMAL(15,2),
    bank_statement_currency VARCHAR(3) DEFAULT 'INR',
    
    -- GL Balance
    gl_balance DECIMAL(15,2),
    
    -- Outstanding Items
    outstanding_checks DECIMAL(15,2),
    outstanding_deposits DECIMAL(15,2),
    
    -- Differences
    difference_amount DECIMAL(15,2),
    difference_notes TEXT,
    
    -- Status
    is_reconciled BOOLEAN DEFAULT false,
    reconciled_by VARCHAR(50),
    reconciliation_notes TEXT,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- TABLE 28: Ledger Control Accounts
-- ============================================================================
CREATE TABLE ledger_control_accounts (
    control_id VARCHAR(50) PRIMARY KEY,
    gl_account VARCHAR(20) NOT NULL,
    control_subsidiary_ledger VARCHAR(50), -- accounts_receivable, accounts_payable
    
    -- Balance
    gl_control_balance DECIMAL(15,2),
    subsidiary_ledger_balance DECIMAL(15,2),
    
    -- Reconciliation
    difference DECIMAL(15,2),
    is_reconciled BOOLEAN DEFAULT false,
    last_reconciliation_date DATE,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT fk_lca_account FOREIGN KEY (gl_account) REFERENCES chart_of_accounts(gl_account)
);

-- ============================================================================
-- TABLE 29: Financial Document Attachments
-- ============================================================================
CREATE TABLE financial_document_attachments (
    attachment_id VARCHAR(50) PRIMARY KEY,
    document_type VARCHAR(50), -- journal_entry, budget, financial_statement
    document_id VARCHAR(50),
    
    -- File Details
    file_name VARCHAR(255),
    file_path VARCHAR(500),
    file_size INTEGER,
    file_type VARCHAR(20), -- pdf, xlsx, jpg, etc.
    
    -- Description
    attachment_description TEXT,
    
    -- Upload Details
    uploaded_by VARCHAR(50),
    upload_date TIMESTAMP,
    
    -- Status
    is_approved BOOLEAN DEFAULT false,
    approval_comments TEXT,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- INDEXES FOR PERFORMANCE
-- ============================================================================

-- Chart of Accounts Indexes
CREATE INDEX idx_coa_company ON chart_of_accounts(company_code);
CREATE INDEX idx_coa_type ON chart_of_accounts(account_type);
CREATE INDEX idx_coa_active ON chart_of_accounts(is_active);

-- Fiscal Periods Indexes
CREATE INDEX idx_fp_year ON fiscal_periods(fiscal_year);
CREATE INDEX idx_fp_company ON fiscal_periods(company_code);

-- Journal Entries Indexes
CREATE INDEX idx_je_posting_date ON journal_entries(posting_date);
CREATE INDEX idx_je_company ON journal_entries(company_code);
CREATE INDEX idx_je_status ON journal_entries(posting_status);
CREATE INDEX idx_je_source ON journal_entries(source_system);

-- Journal Entry Lines Indexes
CREATE INDEX idx_jel_je ON journal_entry_lines(journal_entry_id);
CREATE INDEX idx_jel_account ON journal_entry_lines(gl_account);
CREATE INDEX idx_jel_cost_center ON journal_entry_lines(cost_center_id);

-- Account Balances Indexes
CREATE INDEX idx_ab_period ON account_balances(fiscal_period_id);
CREATE INDEX idx_ab_account ON account_balances(gl_account);

-- Budget Indexes
CREATE INDEX idx_bt_year ON budget_templates(budget_year);
CREATE INDEX idx_bt_status ON budget_templates(budget_status);

-- Cost Centers Indexes
CREATE INDEX idx_cc_company ON cost_centers(company_code);
CREATE INDEX idx_cc_active ON cost_centers(is_active);

-- ============================================================================
-- SUMMARY
-- ============================================================================
-- Total Tables: 29
-- Purpose: Complete Financial/GL module for GenIMS
-- Features:
--   - Full Chart of Accounts with hierarchies
--   - Journal Entry Management (header + lines)
--   - Period-based financial reporting
--   - Budget planning and variance analysis
--   - Cost center management and allocation
--   - Multi-company support
--   - Reconciliation (accounts, bank)
--   - Financial statements generation
--   - Audit trail and approval workflows
--   - Depreciation and accrual management
--   - Tax calculations
--   - Profitability analysis
-- ============================================================================
