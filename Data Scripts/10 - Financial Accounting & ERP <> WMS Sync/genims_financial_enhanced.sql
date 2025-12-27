-- GenIMS Financial Accounting Module (Enhanced)
-- Complete General Ledger with Automated Posting

-- ============================================================================
-- CHART OF ACCOUNTS (ENHANCED)
-- ============================================================================

CREATE TABLE chart_of_accounts (
    account_id VARCHAR(50) PRIMARY KEY,
    account_code VARCHAR(50) UNIQUE NOT NULL,
    account_name VARCHAR(200) NOT NULL,
    
    -- Hierarchy
    parent_account_id VARCHAR(50), -- FK to chart_of_accounts
    account_level INTEGER, -- 1=top level, 2=sub, 3=detail
    
    -- Classification
    account_type VARCHAR(30) NOT NULL,
    -- asset, liability, equity, revenue, expense
    
    account_subtype VARCHAR(50),
    -- asset: current_asset, fixed_asset, other_asset
    -- liability: current_liability, long_term_liability
    -- equity: owners_equity, retained_earnings
    -- revenue: operating_revenue, other_revenue
    -- expense: cogs, operating_expense, other_expense
    
    -- Financial Statement
    financial_statement VARCHAR(30),
    -- balance_sheet, income_statement, cash_flow
    
    -- Normal Balance
    normal_balance VARCHAR(10), -- debit, credit
    
    -- Control Account
    is_control_account BOOLEAN DEFAULT false,
    allow_posting BOOLEAN DEFAULT true, -- False for summary accounts
    
    -- Currency
    currency_code VARCHAR(3) DEFAULT 'INR',
    allow_multi_currency BOOLEAN DEFAULT false,
    
    -- Cost Center Tracking
    requires_cost_center BOOLEAN DEFAULT false,
    
    -- Description
    description TEXT,
    
    -- Status
    is_active BOOLEAN DEFAULT true,
    effective_date DATE,
    inactive_date DATE,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- GL POSTING RULES (AUTOMATED POSTING)
-- ============================================================================

CREATE TABLE gl_posting_rules (
    rule_id VARCHAR(50) PRIMARY KEY,
    rule_code VARCHAR(50) UNIQUE NOT NULL,
    rule_name VARCHAR(200) NOT NULL,
    
    -- Trigger
    transaction_type VARCHAR(50) NOT NULL,
    -- sales_order, purchase_order, production_order, inventory_movement,
    -- payroll, payment, receipt, maintenance, freight, etc.
    
    transaction_subtype VARCHAR(50),
    
    -- Conditions
    condition_rules TEXT, -- JSON: {field: value} conditions
    
    -- Account Mapping
    debit_account_id VARCHAR(50), -- FK to chart_of_accounts
    credit_account_id VARCHAR(50), -- FK to chart_of_accounts
    
    -- Amount Source
    amount_field VARCHAR(100), -- Field to get amount from
    
    -- Description Template
    description_template TEXT,
    
    -- Effective Dates
    effective_from DATE,
    effective_to DATE,
    
    -- Priority
    rule_priority INTEGER DEFAULT 10,
    
    -- Status
    is_active BOOLEAN DEFAULT true,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- ENHANCED JOURNAL ENTRIES
-- ============================================================================

CREATE TABLE journal_entry_headers (
    journal_entry_id VARCHAR(50) PRIMARY KEY,
    journal_number VARCHAR(50) UNIQUE NOT NULL,
    
    -- Entry Type
    entry_type VARCHAR(30) DEFAULT 'standard',
    -- standard, adjusting, closing, reversing, inter_company
    
    -- Source
    source_type VARCHAR(30), -- manual, auto_sales, auto_purchase, auto_production, etc.
    source_document_id VARCHAR(50), -- Original transaction ID
    
    -- Period
    posting_date DATE NOT NULL,
    fiscal_year INTEGER,
    fiscal_period INTEGER, -- 1-12 for months
    
    -- Description
    description TEXT,
    reference VARCHAR(100),
    
    -- Amounts
    total_debit DECIMAL(15,2) DEFAULT 0,
    total_credit DECIMAL(15,2) DEFAULT 0,
    
    -- Currency
    currency_code VARCHAR(3) DEFAULT 'INR',
    exchange_rate DECIMAL(12,6) DEFAULT 1,
    functional_currency_code VARCHAR(3) DEFAULT 'INR',
    
    -- Status
    entry_status VARCHAR(30) DEFAULT 'draft',
    -- draft, posted, approved, reversed
    
    -- Posting
    posted BOOLEAN DEFAULT false,
    posted_by VARCHAR(50),
    posted_at TIMESTAMP,
    
    -- Reversal
    reversed BOOLEAN DEFAULT false,
    reversal_entry_id VARCHAR(50), -- FK to journal_entry_headers
    reversed_date DATE,
    
    -- Approval
    requires_approval BOOLEAN DEFAULT false,
    approved BOOLEAN DEFAULT false,
    approved_by VARCHAR(50),
    approved_at TIMESTAMP,
    
    created_by VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE journal_entry_lines (
    line_id VARCHAR(50) PRIMARY KEY,
    journal_entry_id VARCHAR(50) NOT NULL, -- FK to journal_entry_headers
    line_number INTEGER,
    
    -- Account
    account_id VARCHAR(50) NOT NULL, -- FK to chart_of_accounts
    
    -- Debit/Credit
    debit_amount DECIMAL(15,2) DEFAULT 0,
    credit_amount DECIMAL(15,2) DEFAULT 0,
    
    -- Currency
    currency_code VARCHAR(3) DEFAULT 'INR',
    exchange_rate DECIMAL(12,6) DEFAULT 1,
    functional_debit DECIMAL(15,2) DEFAULT 0,
    functional_credit DECIMAL(15,2) DEFAULT 0,
    
    -- Cost Center
    cost_center_id VARCHAR(50), -- FK to cost_centers
    
    -- Dimensions (optional)
    department_id VARCHAR(50),
    factory_id VARCHAR(50),
    
    -- Description
    line_description TEXT,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- COST CENTERS
-- ============================================================================

CREATE TABLE cost_centers (
    cost_center_id VARCHAR(50) PRIMARY KEY,
    cost_center_code VARCHAR(50) UNIQUE NOT NULL,
    cost_center_name VARCHAR(200) NOT NULL,
    
    -- Hierarchy
    parent_cost_center_id VARCHAR(50), -- FK to cost_centers
    
    -- Classification
    cost_center_type VARCHAR(30),
    -- production, warehouse, sales, admin, r_and_d
    
    -- Responsibility
    responsible_employee_id VARCHAR(50), -- FK to employees
    
    -- Location
    factory_id VARCHAR(50), -- FK to factories
    department_id VARCHAR(50), -- FK to departments
    
    -- Status
    is_active BOOLEAN DEFAULT true,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- FINANCIAL PERIODS
-- ============================================================================

CREATE TABLE fiscal_years (
    fiscal_year_id VARCHAR(50) PRIMARY KEY,
    fiscal_year INTEGER UNIQUE NOT NULL,
    
    -- Dates
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    
    -- Status
    year_status VARCHAR(30) DEFAULT 'open',
    -- open, closed, locked
    
    closed_date DATE,
    closed_by VARCHAR(50),
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE fiscal_periods (
    period_id VARCHAR(50) PRIMARY KEY,
    fiscal_year INTEGER NOT NULL,
    period_number INTEGER NOT NULL, -- 1-12
    
    period_name VARCHAR(50), -- Jan-2025, Feb-2025, etc.
    
    -- Dates
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    
    -- Status
    period_status VARCHAR(30) DEFAULT 'open',
    -- open, closed, locked
    
    -- Closing
    closed_date DATE,
    closed_by VARCHAR(50),
    
    -- Posting Control
    allow_posting BOOLEAN DEFAULT true,
    
    UNIQUE(fiscal_year, period_number),
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- BUDGETS
-- ============================================================================

CREATE TABLE budget_headers (
    budget_id VARCHAR(50) PRIMARY KEY,
    budget_code VARCHAR(50) UNIQUE NOT NULL,
    budget_name VARCHAR(200) NOT NULL,
    
    -- Period
    fiscal_year INTEGER NOT NULL,
    budget_type VARCHAR(30), -- operating, capital, cash_flow
    
    -- Version
    budget_version INTEGER DEFAULT 1,
    is_approved BOOLEAN DEFAULT false,
    
    -- Status
    budget_status VARCHAR(30) DEFAULT 'draft',
    -- draft, submitted, approved, active, closed
    
    approved_by VARCHAR(50),
    approved_date DATE,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE budget_lines (
    budget_line_id VARCHAR(50) PRIMARY KEY,
    budget_id VARCHAR(50) NOT NULL, -- FK to budget_headers
    
    -- Account
    account_id VARCHAR(50) NOT NULL, -- FK to chart_of_accounts
    
    -- Cost Center
    cost_center_id VARCHAR(50), -- FK to cost_centers
    
    -- Period Amounts
    period_01 DECIMAL(15,2) DEFAULT 0, -- January
    period_02 DECIMAL(15,2) DEFAULT 0,
    period_03 DECIMAL(15,2) DEFAULT 0,
    period_04 DECIMAL(15,2) DEFAULT 0,
    period_05 DECIMAL(15,2) DEFAULT 0,
    period_06 DECIMAL(15,2) DEFAULT 0,
    period_07 DECIMAL(15,2) DEFAULT 0,
    period_08 DECIMAL(15,2) DEFAULT 0,
    period_09 DECIMAL(15,2) DEFAULT 0,
    period_10 DECIMAL(15,2) DEFAULT 0,
    period_11 DECIMAL(15,2) DEFAULT 0,
    period_12 DECIMAL(15,2) DEFAULT 0,
    
    annual_total DECIMAL(15,2) DEFAULT 0,
    
    notes TEXT,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- ACCOUNT BALANCES (PERFORMANCE)
-- ============================================================================

CREATE TABLE account_balances (
    balance_id VARCHAR(50) PRIMARY KEY,
    
    -- Account & Period
    account_id VARCHAR(50) NOT NULL, -- FK to chart_of_accounts
    fiscal_year INTEGER NOT NULL,
    fiscal_period INTEGER NOT NULL,
    
    -- Cost Center (optional)
    cost_center_id VARCHAR(50),
    
    -- Balances
    beginning_balance DECIMAL(15,2) DEFAULT 0,
    period_debit DECIMAL(15,2) DEFAULT 0,
    period_credit DECIMAL(15,2) DEFAULT 0,
    ending_balance DECIMAL(15,2) DEFAULT 0,
    
    -- YTD
    ytd_debit DECIMAL(15,2) DEFAULT 0,
    ytd_credit DECIMAL(15,2) DEFAULT 0,
    
    -- Budget
    period_budget DECIMAL(15,2) DEFAULT 0,
    ytd_budget DECIMAL(15,2) DEFAULT 0,
    
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(account_id, fiscal_year, fiscal_period, cost_center_id)
);

-- ============================================================================
-- FINANCIAL STATEMENTS
-- ============================================================================

CREATE TABLE financial_statements (
    statement_id VARCHAR(50) PRIMARY KEY,
    
    -- Statement Type
    statement_type VARCHAR(30) NOT NULL,
    -- income_statement, balance_sheet, cash_flow
    
    -- Period
    fiscal_year INTEGER NOT NULL,
    fiscal_period INTEGER, -- NULL for annual
    
    -- Date Range
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    
    -- Generation
    generated_at TIMESTAMP,
    generated_by VARCHAR(50),
    
    -- Status
    statement_status VARCHAR(30) DEFAULT 'draft',
    -- draft, finalized, published
    
    -- Data (JSON snapshot)
    statement_data JSONB,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- EXCHANGE RATES (MULTI-CURRENCY)
-- ============================================================================

CREATE TABLE exchange_rates (
    rate_id VARCHAR(50) PRIMARY KEY,
    
    -- Currency Pair
    from_currency VARCHAR(3) NOT NULL,
    to_currency VARCHAR(3) NOT NULL,
    
    -- Date
    effective_date DATE NOT NULL,
    
    -- Rates
    exchange_rate DECIMAL(12,6) NOT NULL,
    inverse_rate DECIMAL(12,6),
    
    -- Type
    rate_type VARCHAR(30) DEFAULT 'spot',
    -- spot, average, budget
    
    UNIQUE(from_currency, to_currency, effective_date, rate_type),
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- INTER-COMPANY TRANSACTIONS
-- ============================================================================

CREATE TABLE inter_company_transactions (
    transaction_id VARCHAR(50) PRIMARY KEY,
    transaction_number VARCHAR(50) UNIQUE NOT NULL,
    
    -- Companies
    from_company_id VARCHAR(50), -- Factory/entity ID
    to_company_id VARCHAR(50),
    
    -- Transaction
    transaction_type VARCHAR(50),
    -- goods_transfer, service, loan, expense_allocation
    
    transaction_date DATE NOT NULL,
    
    -- Amount
    amount DECIMAL(15,2) NOT NULL,
    currency_code VARCHAR(3) DEFAULT 'INR',
    
    -- GL Entries
    from_company_journal_id VARCHAR(50), -- FK to journal_entry_headers
    to_company_journal_id VARCHAR(50),
    
    -- Reconciliation
    reconciled BOOLEAN DEFAULT false,
    reconciled_date DATE,
    
    description TEXT,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- FINANCIAL CLOSE PROCEDURES
-- ============================================================================

CREATE TABLE period_close_tasks (
    task_id VARCHAR(50) PRIMARY KEY,
    
    -- Period
    fiscal_year INTEGER NOT NULL,
    fiscal_period INTEGER NOT NULL,
    
    -- Task
    task_sequence INTEGER,
    task_name VARCHAR(200) NOT NULL,
    task_description TEXT,
    
    -- Status
    task_status VARCHAR(30) DEFAULT 'pending',
    -- pending, in_progress, completed, failed
    
    -- Execution
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    completed_by VARCHAR(50),
    
    -- Results
    result_message TEXT,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- AUDIT TRAIL
-- ============================================================================

CREATE TABLE gl_audit_trail (
    audit_id VARCHAR(50) PRIMARY KEY,
    audit_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Action
    action_type VARCHAR(30),
    -- create, update, delete, post, reverse, approve
    
    -- Target
    entity_type VARCHAR(50), -- journal_entry, account_balance, etc.
    entity_id VARCHAR(50),
    
    -- Changes
    old_values JSONB,
    new_values JSONB,
    
    -- User
    user_id VARCHAR(50),
    user_name VARCHAR(200),
    
    -- Context
    ip_address VARCHAR(50),
    session_id VARCHAR(100)
);

-- ============================================================================
-- INDICES
-- ============================================================================

-- Chart of Accounts
CREATE INDEX idx_coa_parent ON chart_of_accounts(parent_account_id);
CREATE INDEX idx_coa_type ON chart_of_accounts(account_type, is_active);

-- Journal Entries
CREATE INDEX idx_je_header_date ON journal_entry_headers(posting_date);
CREATE INDEX idx_je_header_period ON journal_entry_headers(fiscal_year, fiscal_period);
CREATE INDEX idx_je_header_status ON journal_entry_headers(entry_status, posted);
CREATE INDEX idx_je_header_source ON journal_entry_headers(source_type, source_document_id);
CREATE INDEX idx_je_lines_journal ON journal_entry_lines(journal_entry_id);
CREATE INDEX idx_je_lines_account ON journal_entry_lines(account_id);

-- Cost Centers
CREATE INDEX idx_cost_center_parent ON cost_centers(parent_cost_center_id);
CREATE INDEX idx_cost_center_factory ON cost_centers(factory_id, is_active);

-- Periods
CREATE INDEX idx_fiscal_periods_year ON fiscal_periods(fiscal_year, period_number);

-- Budgets
CREATE INDEX idx_budget_lines_budget ON budget_lines(budget_id);
CREATE INDEX idx_budget_lines_account ON budget_lines(account_id);

-- Balances
CREATE INDEX idx_account_bal_account ON account_balances(account_id, fiscal_year, fiscal_period);
CREATE INDEX idx_account_bal_period ON account_balances(fiscal_year, fiscal_period);

-- Exchange Rates
CREATE INDEX idx_exch_rates_date ON exchange_rates(from_currency, to_currency, effective_date);

-- ============================================================================
-- COMMENTS
-- ============================================================================

COMMENT ON TABLE chart_of_accounts IS 'Hierarchical chart of accounts with multi-level structure';
COMMENT ON TABLE gl_posting_rules IS 'Automated GL posting rules by transaction type';
COMMENT ON TABLE journal_entry_headers IS 'Journal entry headers with posting and approval workflow';
COMMENT ON TABLE journal_entry_lines IS 'Journal entry line items with account details';
COMMENT ON TABLE cost_centers IS 'Cost centers for departmental accounting';
COMMENT ON TABLE fiscal_periods IS 'Fiscal periods with open/close status';
COMMENT ON TABLE budget_headers IS 'Annual budget headers';
COMMENT ON TABLE budget_lines IS 'Budget amounts by account and period';
COMMENT ON TABLE account_balances IS 'Pre-calculated account balances for performance';
COMMENT ON TABLE financial_statements IS 'Generated financial statements (P&L, Balance Sheet, Cash Flow)';
COMMENT ON TABLE exchange_rates IS 'Multi-currency exchange rates';
COMMENT ON TABLE inter_company_transactions IS 'Transactions between factories/entities';
COMMENT ON TABLE period_close_tasks IS 'Period-end close task tracking';
COMMENT ON TABLE gl_audit_trail IS 'Complete audit trail of all GL changes';
