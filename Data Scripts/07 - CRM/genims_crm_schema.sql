-- GenIMS CRM (Customer Relationship Management) Schema
-- Complete B2B CRM from lead to customer lifecycle

-- ============================================================================
-- LEADS MANAGEMENT
-- ============================================================================

CREATE TABLE leads (
    lead_id VARCHAR(50) PRIMARY KEY,
    lead_number VARCHAR(50) UNIQUE NOT NULL,
    
    -- Lead Information
    company_name VARCHAR(200) NOT NULL,
    lead_source VARCHAR(50), -- website, referral, trade_show, cold_call, social_media, partner
    source_campaign_id VARCHAR(50), -- FK to campaigns
    
    -- Contact Details
    contact_first_name VARCHAR(100),
    contact_last_name VARCHAR(100),
    contact_title VARCHAR(100),
    email VARCHAR(100),
    phone VARCHAR(50),
    mobile VARCHAR(50),
    
    -- Company Details
    industry VARCHAR(100),
    company_size VARCHAR(30), -- startup, small, medium, large, enterprise
    annual_revenue_range VARCHAR(50),
    number_of_employees INTEGER,
    
    -- Address
    address_line1 VARCHAR(200),
    address_line2 VARCHAR(200),
    city VARCHAR(100),
    state VARCHAR(100),
    country VARCHAR(50) DEFAULT 'India',
    postal_code VARCHAR(20),
    
    -- Lead Quality
    lead_score INTEGER DEFAULT 0, -- 0-100
    lead_grade VARCHAR(1), -- A, B, C, D
    
    -- Qualification
    lead_status VARCHAR(30) DEFAULT 'new',
    -- new, contacted, qualified, unqualified, nurturing, converted, lost
    
    qualification_status VARCHAR(30),
    -- not_started, in_progress, qualified, disqualified
    
    -- BANT (Budget, Authority, Need, Timeline)
    has_budget BOOLEAN DEFAULT false,
    is_decision_maker BOOLEAN DEFAULT false,
    has_identified_need BOOLEAN DEFAULT false,
    has_timeline BOOLEAN DEFAULT false,
    
    -- Requirements
    product_interest VARCHAR(200),
    estimated_deal_value DECIMAL(15,2),
    expected_close_date DATE,
    
    -- Assignment
    assigned_to VARCHAR(50), -- FK to sales_reps
    assigned_date TIMESTAMP,
    
    -- Conversion
    converted BOOLEAN DEFAULT false,
    converted_date TIMESTAMP,
    converted_to_account_id VARCHAR(50), -- FK to accounts
    converted_to_opportunity_id VARCHAR(50), -- FK to opportunities
    
    -- Tracking
    first_contact_date TIMESTAMP,
    last_contact_date TIMESTAMP,
    contact_attempts INTEGER DEFAULT 0,
    
    -- Additional Info
    description TEXT,
    notes TEXT,
    
    -- Status
    is_active BOOLEAN DEFAULT true,
    
    -- Audit
    created_by VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE lead_activities (
    activity_id VARCHAR(50) PRIMARY KEY,
    lead_id VARCHAR(50) NOT NULL, -- FK to leads
    
    -- Activity Type
    activity_type VARCHAR(30), -- call, email, meeting, demo, site_visit, follow_up
    
    -- Details
    subject VARCHAR(200),
    description TEXT,
    
    -- Timing
    activity_date TIMESTAMP NOT NULL,
    duration_minutes INTEGER,
    
    -- Outcome
    outcome VARCHAR(30), -- completed, no_answer, left_message, scheduled_follow_up
    
    -- Next Action
    next_action VARCHAR(200),
    next_action_date DATE,
    
    -- User
    performed_by VARCHAR(50), -- FK to sales_reps
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- ACCOUNTS (ENHANCED CUSTOMERS)
-- ============================================================================

CREATE TABLE accounts (
    account_id VARCHAR(50) PRIMARY KEY,
    account_number VARCHAR(50) UNIQUE NOT NULL,
    
    -- Link to Master Data
    customer_id VARCHAR(50), -- FK to customers (master data)
    
    -- Account Information
    account_name VARCHAR(200) NOT NULL,
    account_type VARCHAR(50), -- prospect, customer, partner, competitor, former_customer
    
    -- Account Classification
    industry VARCHAR(100),
    industry_segment VARCHAR(100),
    account_tier VARCHAR(20), -- strategic, key, standard
    company_size VARCHAR(30), -- startup, small, medium, large, enterprise
    
    -- Financial Information
    annual_revenue DECIMAL(18,2),
    employee_count INTEGER,
    credit_limit DECIMAL(15,2),
    payment_terms VARCHAR(50), -- NET30, NET60, COD
    
    -- Hierarchy
    parent_account_id VARCHAR(50), -- FK to accounts (for subsidiaries)
    
    -- Address (Corporate HQ)
    billing_address_line1 VARCHAR(200),
    billing_address_line2 VARCHAR(200),
    billing_city VARCHAR(100),
    billing_state VARCHAR(100),
    billing_country VARCHAR(50) DEFAULT 'India',
    billing_postal_code VARCHAR(20),
    
    shipping_address_line1 VARCHAR(200),
    shipping_address_line2 VARCHAR(200),
    shipping_city VARCHAR(100),
    shipping_state VARCHAR(100),
    shipping_country VARCHAR(50) DEFAULT 'India',
    shipping_postal_code VARCHAR(20),
    
    -- Contact Information
    phone VARCHAR(50),
    fax VARCHAR(50),
    website VARCHAR(200),
    
    -- Account Team
    account_owner VARCHAR(50), -- FK to sales_reps (primary sales rep)
    account_manager VARCHAR(50), -- FK to sales_reps (account manager)
    
    -- Relationship Status
    relationship_status VARCHAR(30) DEFAULT 'prospect',
    -- prospect, active, inactive, at_risk, churned
    
    customer_since DATE,
    last_purchase_date DATE,
    
    -- Value Metrics
    lifetime_value DECIMAL(18,2) DEFAULT 0,
    ytd_revenue DECIMAL(18,2) DEFAULT 0,
    last_year_revenue DECIMAL(18,2) DEFAULT 0,
    
    -- Health Score
    health_score INTEGER DEFAULT 50, -- 0-100
    churn_risk VARCHAR(20), -- low, medium, high
    
    -- Preferences
    preferred_contact_method VARCHAR(30), -- email, phone, in_person
    communication_frequency VARCHAR(30), -- daily, weekly, monthly, quarterly
    
    -- Social Media
    linkedin_url VARCHAR(200),
    twitter_handle VARCHAR(100),
    
    -- Description
    description TEXT,
    notes TEXT,
    
    -- Status
    is_active BOOLEAN DEFAULT true,
    
    -- Audit
    created_by VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- CONTACTS
-- ============================================================================

CREATE TABLE contacts (
    contact_id VARCHAR(50) PRIMARY KEY,
    contact_number VARCHAR(50) UNIQUE NOT NULL,
    
    -- Account Link
    account_id VARCHAR(50) NOT NULL, -- FK to accounts
    
    -- Personal Information
    salutation VARCHAR(10), -- Mr., Ms., Dr., Prof.
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    middle_name VARCHAR(100),
    
    -- Position
    job_title VARCHAR(100),
    department VARCHAR(100),
    
    -- Role in Decision Making
    contact_role VARCHAR(50), -- decision_maker, influencer, champion, gatekeeper, user
    decision_authority VARCHAR(50), -- final_decision, recommends, approves, uses
    
    -- Contact Information
    email VARCHAR(100),
    email_opted_out BOOLEAN DEFAULT false,
    phone VARCHAR(50),
    mobile VARCHAR(50),
    
    -- Reporting
    reports_to_contact_id VARCHAR(50), -- FK to contacts
    
    -- Address (if different from account)
    mailing_address_line1 VARCHAR(200),
    mailing_city VARCHAR(100),
    mailing_state VARCHAR(100),
    mailing_country VARCHAR(50),
    mailing_postal_code VARCHAR(20),
    
    -- Social Media
    linkedin_url VARCHAR(200),
    twitter_handle VARCHAR(100),
    
    -- Relationship
    relationship_strength VARCHAR(30), -- strong, moderate, weak
    last_contact_date TIMESTAMP,
    contact_frequency INTEGER, -- times per month
    
    -- Preferences
    preferred_contact_method VARCHAR(30), -- email, phone, linkedin
    best_time_to_contact VARCHAR(50),
    
    -- Personal
    birthday DATE,
    interests TEXT,
    
    -- Description
    notes TEXT,
    
    -- Status
    contact_status VARCHAR(30) DEFAULT 'active', -- active, inactive, left_company
    
    is_primary BOOLEAN DEFAULT false,
    
    -- Audit
    created_by VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- OPPORTUNITIES (SALES PIPELINE)
-- ============================================================================

CREATE TABLE opportunities (
    opportunity_id VARCHAR(50) PRIMARY KEY,
    opportunity_number VARCHAR(50) UNIQUE NOT NULL,
    opportunity_name VARCHAR(200) NOT NULL,
    
    -- Account & Contact
    account_id VARCHAR(50) NOT NULL, -- FK to accounts
    primary_contact_id VARCHAR(50), -- FK to contacts
    
    -- Lead Source
    lead_source VARCHAR(50),
    source_lead_id VARCHAR(50), -- FK to leads (if converted from lead)
    source_campaign_id VARCHAR(50), -- FK to campaigns
    
    -- Opportunity Details
    opportunity_type VARCHAR(50), -- new_business, existing_customer, renewal, upsell
    
    -- Product/Solution
    product_category VARCHAR(100),
    solution_description TEXT,
    
    -- Financial
    amount DECIMAL(15,2) NOT NULL,
    expected_revenue DECIMAL(15,2), -- Weighted by probability
    cost_estimate DECIMAL(15,2),
    margin_pct DECIMAL(5,2),
    
    -- Probability & Stage
    stage VARCHAR(50) DEFAULT 'prospecting',
    -- prospecting, qualification, needs_analysis, proposal, negotiation, 
    -- closed_won, closed_lost
    
    probability_pct INTEGER DEFAULT 10, -- 0-100
    
    -- Dates
    close_date DATE NOT NULL,
    expected_close_date DATE,
    actual_close_date DATE,
    
    -- Forecast Category
    forecast_category VARCHAR(30),
    -- pipeline, best_case, commit, closed
    
    -- Assignment
    opportunity_owner VARCHAR(50), -- FK to sales_reps
    sales_team TEXT, -- JSON array of sales_rep_ids
    
    -- Competition
    competitors TEXT, -- JSON array of competitor names
    competitive_position VARCHAR(30), -- leading, competitive, behind
    
    -- Decision Criteria
    decision_criteria TEXT,
    key_success_factors TEXT,
    
    -- Requirements
    customer_requirements TEXT,
    technical_requirements TEXT,
    
    -- Budget & Authority
    budget_confirmed BOOLEAN DEFAULT false,
    budget_amount DECIMAL(15,2),
    decision_maker_identified BOOLEAN DEFAULT false,
    
    -- Timeline
    customer_timeline VARCHAR(100),
    next_step VARCHAR(200),
    next_step_date DATE,
    
    -- Win/Loss Analysis
    win_loss_status VARCHAR(20), -- won, lost, pending
    win_loss_reason VARCHAR(200),
    win_loss_notes TEXT,
    lost_to_competitor VARCHAR(200),
    
    -- Conversion
    converted_to_quote_id VARCHAR(50), -- FK to quotations
    converted_to_order_id VARCHAR(50), -- FK to sales_orders (ERP)
    
    -- Description
    description TEXT,
    notes TEXT,
    
    -- Status
    is_active BOOLEAN DEFAULT true,
    is_closed BOOLEAN DEFAULT false,
    
    -- Audit
    created_by VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    closed_by VARCHAR(50),
    closed_at TIMESTAMP
);

CREATE TABLE opportunity_stage_history (
    history_id VARCHAR(50) PRIMARY KEY,
    opportunity_id VARCHAR(50) NOT NULL, -- FK to opportunities
    
    -- Stage Change
    from_stage VARCHAR(50),
    to_stage VARCHAR(50) NOT NULL,
    
    -- Amount Change
    from_amount DECIMAL(15,2),
    to_amount DECIMAL(15,2),
    
    -- Probability Change
    from_probability INTEGER,
    to_probability INTEGER,
    
    -- Date Change
    from_close_date DATE,
    to_close_date DATE,
    
    -- Reason
    change_reason TEXT,
    
    -- Duration in Previous Stage
    stage_duration_days INTEGER,
    
    -- User
    changed_by VARCHAR(50),
    changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE opportunity_products (
    opp_product_id VARCHAR(50) PRIMARY KEY,
    opportunity_id VARCHAR(50) NOT NULL, -- FK to opportunities
    line_number INTEGER,
    
    -- Product
    material_id VARCHAR(50), -- FK to materials
    product_name VARCHAR(200),
    product_description TEXT,
    
    -- Quantity & Pricing
    quantity DECIMAL(15,4),
    unit_of_measure VARCHAR(20),
    list_price DECIMAL(12,4),
    discount_pct DECIMAL(5,2) DEFAULT 0,
    unit_price DECIMAL(12,4), -- After discount
    
    -- Total
    line_total DECIMAL(15,2),
    
    -- Dates
    required_date DATE,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- SALES ACTIVITIES & TASKS
-- ============================================================================

CREATE TABLE activities (
    activity_id VARCHAR(50) PRIMARY KEY,
    activity_number VARCHAR(50) UNIQUE NOT NULL,
    
    -- Activity Type
    activity_type VARCHAR(30), -- call, email, meeting, demo, presentation, site_visit
    
    -- Related Records
    related_to_type VARCHAR(30), -- lead, account, contact, opportunity
    related_to_id VARCHAR(50),
    
    lead_id VARCHAR(50), -- FK to leads
    account_id VARCHAR(50), -- FK to accounts
    contact_id VARCHAR(50), -- FK to contacts
    opportunity_id VARCHAR(50), -- FK to opportunities
    
    -- Activity Details
    subject VARCHAR(200) NOT NULL,
    description TEXT,
    
    -- Scheduling
    activity_date TIMESTAMP NOT NULL,
    duration_minutes INTEGER DEFAULT 30,
    location VARCHAR(200),
    
    -- Status
    activity_status VARCHAR(30) DEFAULT 'planned',
    -- planned, completed, cancelled, no_show
    
    -- Priority
    priority VARCHAR(20) DEFAULT 'medium', -- high, medium, low
    
    -- Outcome
    outcome VARCHAR(30), -- successful, follow_up_needed, no_decision, lost_interest
    outcome_notes TEXT,
    
    -- Follow-up
    follow_up_required BOOLEAN DEFAULT false,
    follow_up_date DATE,
    
    -- Attendees
    attendees TEXT, -- JSON array of contact_ids
    
    -- Assignment
    assigned_to VARCHAR(50), -- FK to sales_reps
    
    -- Reminders
    reminder_enabled BOOLEAN DEFAULT false,
    reminder_datetime TIMESTAMP,
    
    created_by VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE tasks (
    task_id VARCHAR(50) PRIMARY KEY,
    task_number VARCHAR(50) UNIQUE NOT NULL,
    
    -- Task Details
    subject VARCHAR(200) NOT NULL,
    description TEXT,
    
    -- Related Records
    related_to_type VARCHAR(30), -- lead, account, opportunity, case
    related_to_id VARCHAR(50),
    
    -- Task Type
    task_type VARCHAR(50), -- follow_up, send_quote, schedule_demo, contract_review
    
    -- Priority
    priority VARCHAR(20) DEFAULT 'medium', -- urgent, high, medium, low
    
    -- Status
    task_status VARCHAR(30) DEFAULT 'not_started',
    -- not_started, in_progress, completed, cancelled
    
    -- Dates
    due_date DATE NOT NULL,
    completed_date DATE,
    
    -- Assignment
    assigned_to VARCHAR(50), -- FK to sales_reps
    
    -- Reminders
    reminder_enabled BOOLEAN DEFAULT true,
    reminder_date DATE,
    
    -- Completion
    completion_notes TEXT,
    
    created_by VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- QUOTATIONS / PROPOSALS
-- ============================================================================

CREATE TABLE quotations (
    quotation_id VARCHAR(50) PRIMARY KEY,
    quotation_number VARCHAR(50) UNIQUE NOT NULL,
    quotation_name VARCHAR(200) NOT NULL,
    
    -- Links
    opportunity_id VARCHAR(50), -- FK to opportunities
    account_id VARCHAR(50) NOT NULL, -- FK to accounts
    contact_id VARCHAR(50), -- FK to contacts
    
    -- Quotation Details
    quotation_date DATE NOT NULL,
    valid_until_date DATE NOT NULL,
    
    -- Status
    quotation_status VARCHAR(30) DEFAULT 'draft',
    -- draft, sent, acknowledged, under_review, accepted, rejected, expired
    
    -- Financial
    subtotal DECIMAL(15,2),
    discount_amount DECIMAL(15,2) DEFAULT 0,
    tax_amount DECIMAL(15,2) DEFAULT 0,
    shipping_cost DECIMAL(15,2) DEFAULT 0,
    total_amount DECIMAL(15,2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'INR',
    
    -- Terms
    payment_terms VARCHAR(50), -- NET30, NET60, advance, milestone
    delivery_terms VARCHAR(100),
    warranty_terms TEXT,
    
    -- Approval
    requires_approval BOOLEAN DEFAULT false,
    approval_status VARCHAR(30), -- pending, approved, rejected
    approved_by VARCHAR(50),
    approved_at TIMESTAMP,
    
    -- Conversion
    converted BOOLEAN DEFAULT false,
    converted_date DATE,
    converted_to_order_id VARCHAR(50), -- FK to sales_orders (ERP)
    
    -- Revision
    revision_number INTEGER DEFAULT 1,
    parent_quotation_id VARCHAR(50), -- FK to quotations (for revisions)
    
    -- Additional Terms
    special_terms TEXT,
    notes TEXT,
    
    -- Documents
    document_url VARCHAR(500),
    
    -- Assignment
    prepared_by VARCHAR(50), -- FK to sales_reps
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE quotation_lines (
    quote_line_id VARCHAR(50) PRIMARY KEY,
    quotation_id VARCHAR(50) NOT NULL, -- FK to quotations
    line_number INTEGER,
    
    -- Product
    material_id VARCHAR(50), -- FK to materials
    product_name VARCHAR(200) NOT NULL,
    product_description TEXT,
    
    -- Quantity & Pricing
    quantity DECIMAL(15,4),
    unit_of_measure VARCHAR(20),
    list_price DECIMAL(12,4),
    discount_pct DECIMAL(5,2) DEFAULT 0,
    unit_price DECIMAL(12,4),
    line_total DECIMAL(15,2),
    
    -- Delivery
    delivery_lead_time_days INTEGER,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- CAMPAIGNS
-- ============================================================================

CREATE TABLE campaigns (
    campaign_id VARCHAR(50) PRIMARY KEY,
    campaign_code VARCHAR(50) UNIQUE NOT NULL,
    campaign_name VARCHAR(200) NOT NULL,
    
    -- Campaign Type
    campaign_type VARCHAR(50), -- email, webinar, trade_show, content, social, partner
    
    -- Status
    campaign_status VARCHAR(30) DEFAULT 'planned',
    -- planned, in_progress, completed, cancelled
    
    -- Dates
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    
    -- Target Audience
    target_audience VARCHAR(200),
    target_industry VARCHAR(100),
    target_company_size VARCHAR(50),
    expected_response_pct DECIMAL(5,2),
    
    -- Budget & Costs
    budgeted_cost DECIMAL(15,2),
    actual_cost DECIMAL(15,2) DEFAULT 0,
    
    -- Results
    total_leads INTEGER DEFAULT 0,
    qualified_leads INTEGER DEFAULT 0,
    opportunities_created INTEGER DEFAULT 0,
    deals_won INTEGER DEFAULT 0,
    total_revenue DECIMAL(18,2) DEFAULT 0,
    
    -- ROI
    roi_pct DECIMAL(8,2), -- (Revenue - Cost) / Cost * 100
    cost_per_lead DECIMAL(12,2),
    conversion_rate_pct DECIMAL(5,2),
    
    -- Description
    description TEXT,
    objectives TEXT,
    
    -- Owner
    campaign_owner VARCHAR(50), -- FK to sales_reps
    
    is_active BOOLEAN DEFAULT true,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE campaign_members (
    member_id VARCHAR(50) PRIMARY KEY,
    campaign_id VARCHAR(50) NOT NULL, -- FK to campaigns
    
    -- Member Type
    member_type VARCHAR(30), -- lead, contact
    
    lead_id VARCHAR(50), -- FK to leads
    contact_id VARCHAR(50), -- FK to contacts
    
    -- Status
    member_status VARCHAR(30) DEFAULT 'sent',
    -- sent, opened, clicked, responded, bounced, opted_out
    
    -- Response
    has_responded BOOLEAN DEFAULT false,
    response_date TIMESTAMP,
    
    -- Outcome
    lead_created BOOLEAN DEFAULT false,
    opportunity_created BOOLEAN DEFAULT false,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- CASES (CUSTOMER SUPPORT)
-- ============================================================================

CREATE TABLE cases (
    case_id VARCHAR(50) PRIMARY KEY,
    case_number VARCHAR(50) UNIQUE NOT NULL,
    
    -- Account & Contact
    account_id VARCHAR(50) NOT NULL, -- FK to accounts
    contact_id VARCHAR(50), -- FK to contacts
    
    -- Case Details
    subject VARCHAR(200) NOT NULL,
    description TEXT NOT NULL,
    
    -- Classification
    case_type VARCHAR(50), -- question, problem, feature_request, complaint
    case_category VARCHAR(50), -- technical, billing, delivery, quality, other
    
    -- Priority
    priority VARCHAR(20) DEFAULT 'medium', -- critical, high, medium, low
    
    -- Status
    case_status VARCHAR(30) DEFAULT 'new',
    -- new, in_progress, escalated, pending_customer, resolved, closed
    
    -- SLA
    sla_response_hours INTEGER, -- Time to first response
    sla_resolution_hours INTEGER, -- Time to resolution
    
    response_due_date TIMESTAMP,
    resolution_due_date TIMESTAMP,
    
    first_response_date TIMESTAMP,
    resolved_date TIMESTAMP,
    closed_date TIMESTAMP,
    
    sla_violated BOOLEAN DEFAULT false,
    
    -- Assignment
    assigned_to VARCHAR(50), -- FK to support reps
    assigned_team VARCHAR(50),
    
    -- Escalation
    escalated BOOLEAN DEFAULT false,
    escalated_to VARCHAR(50),
    escalated_at TIMESTAMP,
    
    -- Resolution
    resolution TEXT,
    root_cause VARCHAR(200),
    
    -- Related Records
    related_product VARCHAR(200),
    related_order_id VARCHAR(50), -- FK to sales_orders
    
    -- Customer Satisfaction
    satisfaction_rating INTEGER, -- 1-5
    customer_feedback TEXT,
    
    created_by VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE case_comments (
    comment_id VARCHAR(50) PRIMARY KEY,
    case_id VARCHAR(50) NOT NULL, -- FK to cases
    
    -- Comment Details
    comment_text TEXT NOT NULL,
    
    -- Visibility
    is_public BOOLEAN DEFAULT true, -- Visible to customer
    
    -- User
    created_by VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- CONTRACTS
-- ============================================================================

CREATE TABLE contracts (
    contract_id VARCHAR(50) PRIMARY KEY,
    contract_number VARCHAR(50) UNIQUE NOT NULL,
    contract_name VARCHAR(200) NOT NULL,
    
    -- Account
    account_id VARCHAR(50) NOT NULL, -- FK to accounts
    
    -- Contract Details
    contract_type VARCHAR(50), -- sales, service, maintenance, subscription
    
    -- Dates
    contract_start_date DATE NOT NULL,
    contract_end_date DATE NOT NULL,
    contract_term_months INTEGER,
    
    -- Status
    contract_status VARCHAR(30) DEFAULT 'draft',
    -- draft, sent_for_signature, signed, active, expired, terminated
    
    signed_date DATE,
    
    -- Financial
    contract_value DECIMAL(18,2) NOT NULL,
    billing_frequency VARCHAR(30), -- one_time, monthly, quarterly, annually
    
    -- Renewal
    auto_renewal BOOLEAN DEFAULT false,
    renewal_term_months INTEGER,
    renewal_notice_days INTEGER DEFAULT 60,
    renewal_date DATE,
    
    -- Termination
    termination_notice_days INTEGER,
    early_termination_penalty DECIMAL(15,2),
    
    -- Terms
    payment_terms VARCHAR(50),
    service_level_agreement TEXT,
    special_terms TEXT,
    
    -- Owner
    contract_owner VARCHAR(50), -- FK to sales_reps
    
    -- Documents
    contract_document_url VARCHAR(500),
    
    -- Parent Contract (for renewals)
    parent_contract_id VARCHAR(50), -- FK to contracts
    
    created_by VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- SALES TEAM & TERRITORIES
-- ============================================================================

CREATE TABLE sales_reps (
    sales_rep_id VARCHAR(50) PRIMARY KEY,
    employee_id VARCHAR(50), -- FK to employees (if exists)
    rep_code VARCHAR(50) UNIQUE NOT NULL,
    
    -- Personal
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    email VARCHAR(100),
    phone VARCHAR(50),
    mobile VARCHAR(50),
    
    -- Role
    sales_role VARCHAR(50), -- SDR, AE, AM, SE, Manager, Director, VP
    job_title VARCHAR(100),
    
    -- Assignment
    territory_id VARCHAR(50), -- FK to sales_territories
    manager_id VARCHAR(50), -- FK to sales_reps
    
    -- Quota
    annual_quota DECIMAL(18,2),
    quarterly_quota DECIMAL(18,2),
    
    -- Performance
    ytd_revenue DECIMAL(18,2) DEFAULT 0,
    ytd_deals_closed INTEGER DEFAULT 0,
    win_rate_pct DECIMAL(5,2),
    avg_deal_size DECIMAL(15,2),
    
    -- Status
    rep_status VARCHAR(30) DEFAULT 'active', -- active, inactive, on_leave
    hire_date DATE,
    
    is_active BOOLEAN DEFAULT true,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE sales_territories (
    territory_id VARCHAR(50) PRIMARY KEY,
    territory_code VARCHAR(50) UNIQUE NOT NULL,
    territory_name VARCHAR(200) NOT NULL,
    
    -- Geography
    countries TEXT, -- JSON array
    states TEXT, -- JSON array
    cities TEXT, -- JSON array
    
    -- Industry Focus
    industries TEXT, -- JSON array
    
    -- Account Segmentation
    account_tiers TEXT, -- JSON array: strategic, key, standard
    company_size TEXT, -- JSON array
    
    -- Quota
    territory_quota DECIMAL(18,2),
    
    -- Manager
    territory_manager VARCHAR(50), -- FK to sales_reps
    
    is_active BOOLEAN DEFAULT true,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- SALES FORECASTING
-- ============================================================================

CREATE TABLE sales_forecasts (
    forecast_id VARCHAR(50) PRIMARY KEY,
    
    -- Period
    forecast_period VARCHAR(20), -- monthly, quarterly, yearly
    forecast_year INTEGER NOT NULL,
    forecast_quarter INTEGER, -- 1, 2, 3, 4
    forecast_month INTEGER, -- 1-12
    
    -- Territory / Rep
    territory_id VARCHAR(50), -- FK to sales_territories
    sales_rep_id VARCHAR(50), -- FK to sales_reps
    
    -- Forecast Categories
    pipeline_amount DECIMAL(18,2) DEFAULT 0, -- Probability 0-25%
    best_case_amount DECIMAL(18,2) DEFAULT 0, -- Probability 26-75%
    commit_amount DECIMAL(18,2) DEFAULT 0, -- Probability 76-99%
    closed_amount DECIMAL(18,2) DEFAULT 0, -- Probability 100%
    
    total_forecast DECIMAL(18,2) DEFAULT 0,
    
    -- Quota
    quota_amount DECIMAL(18,2),
    quota_attainment_pct DECIMAL(5,2),
    
    -- Actual
    actual_revenue DECIMAL(18,2) DEFAULT 0,
    forecast_accuracy_pct DECIMAL(5,2),
    
    -- Snapshot Date
    snapshot_date DATE NOT NULL,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- CUSTOMER INTERACTIONS & NOTES
-- ============================================================================

CREATE TABLE customer_interactions (
    interaction_id VARCHAR(50) PRIMARY KEY,
    
    -- Related Records
    account_id VARCHAR(50), -- FK to accounts
    contact_id VARCHAR(50), -- FK to contacts
    opportunity_id VARCHAR(50), -- FK to opportunities
    case_id VARCHAR(50), -- FK to cases
    
    -- Interaction Details
    interaction_type VARCHAR(50), -- call, email, meeting, chat, social_media
    interaction_date TIMESTAMP NOT NULL,
    
    subject VARCHAR(200),
    description TEXT,
    
    -- Direction
    direction VARCHAR(20), -- inbound, outbound
    
    -- Duration
    duration_minutes INTEGER,
    
    -- Sentiment
    sentiment VARCHAR(20), -- positive, neutral, negative
    
    -- User
    performed_by VARCHAR(50),
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE notes (
    note_id VARCHAR(50) PRIMARY KEY,
    
    -- Related To
    related_to_type VARCHAR(30), -- lead, account, contact, opportunity, case
    related_to_id VARCHAR(50),
    
    -- Note Content
    title VARCHAR(200),
    note_text TEXT NOT NULL,
    
    -- Privacy
    is_private BOOLEAN DEFAULT false,
    
    -- User
    created_by VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- CRM INTEGRATION LOG
-- ============================================================================

CREATE TABLE crm_integration_log (
    log_id VARCHAR(50) PRIMARY KEY,
    log_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Integration Direction
    integration_direction VARCHAR(20),
    -- CRM_TO_ERP, ERP_TO_CRM, CRM_TO_MASTER
    
    -- Document Type
    document_type VARCHAR(50),
    -- quotation, sales_order, customer, contact, opportunity
    
    document_id VARCHAR(50),
    
    -- Status
    integration_status VARCHAR(30), -- pending, in_progress, completed, error
    error_message TEXT,
    
    -- Data
    integration_data JSONB,
    
    -- Retry
    retry_count INTEGER DEFAULT 0,
    last_retry_at TIMESTAMP
);

-- ============================================================================
-- INDICES FOR PERFORMANCE
-- ============================================================================

-- Leads
CREATE INDEX idx_leads_status ON leads(lead_status, is_active);
CREATE INDEX idx_leads_assigned ON leads(assigned_to, lead_status);
CREATE INDEX idx_leads_source ON leads(lead_source, created_at);
CREATE INDEX idx_leads_score ON leads(lead_score DESC);
CREATE INDEX idx_lead_activities_lead ON lead_activities(lead_id, activity_date);

-- Accounts
CREATE INDEX idx_accounts_type ON accounts(account_type, is_active);
CREATE INDEX idx_accounts_owner ON accounts(account_owner, is_active);
CREATE INDEX idx_accounts_parent ON accounts(parent_account_id);
CREATE INDEX idx_accounts_customer ON accounts(customer_id);
CREATE INDEX idx_accounts_tier ON accounts(account_tier, relationship_status);

-- Contacts
CREATE INDEX idx_contacts_account ON contacts(account_id, contact_status);
CREATE INDEX idx_contacts_primary ON contacts(account_id, is_primary);
CREATE INDEX idx_contacts_email ON contacts(email);

-- Opportunities
CREATE INDEX idx_opps_stage ON opportunities(stage, is_active);
CREATE INDEX idx_opps_account ON opportunities(account_id, is_active);
CREATE INDEX idx_opps_owner ON opportunities(opportunity_owner, is_active);
CREATE INDEX idx_opps_close_date ON opportunities(close_date, stage);
CREATE INDEX idx_opps_amount ON opportunities(amount DESC);
CREATE INDEX idx_opp_history_opp ON opportunity_stage_history(opportunity_id, changed_at);
CREATE INDEX idx_opp_products_opp ON opportunity_products(opportunity_id);

-- Activities & Tasks
CREATE INDEX idx_activities_date ON activities(activity_date);
CREATE INDEX idx_activities_assigned ON activities(assigned_to, activity_status);
CREATE INDEX idx_activities_related ON activities(related_to_type, related_to_id);
CREATE INDEX idx_tasks_due ON tasks(due_date, task_status);
CREATE INDEX idx_tasks_assigned ON tasks(assigned_to, task_status);

-- Quotations
CREATE INDEX idx_quotes_status ON quotations(quotation_status, valid_until_date);
CREATE INDEX idx_quotes_account ON quotations(account_id);
CREATE INDEX idx_quotes_opp ON quotations(opportunity_id);
CREATE INDEX idx_quote_lines_quote ON quotation_lines(quotation_id);

-- Campaigns
CREATE INDEX idx_campaigns_status ON campaigns(campaign_status, is_active);
CREATE INDEX idx_campaigns_dates ON campaigns(start_date, end_date);
CREATE INDEX idx_campaign_members_campaign ON campaign_members(campaign_id);

-- Cases
CREATE INDEX idx_cases_status ON cases(case_status, priority);
CREATE INDEX idx_cases_account ON cases(account_id, case_status);
CREATE INDEX idx_cases_assigned ON cases(assigned_to, case_status);
CREATE INDEX idx_cases_sla ON cases(sla_violated, case_status);
CREATE INDEX idx_case_comments_case ON case_comments(case_id, created_at);

-- Contracts
CREATE INDEX idx_contracts_status ON contracts(contract_status);
CREATE INDEX idx_contracts_account ON contracts(account_id, contract_status);
CREATE INDEX idx_contracts_renewal ON contracts(renewal_date, auto_renewal);

-- Sales Team
CREATE INDEX idx_sales_reps_status ON sales_reps(rep_status, is_active);
CREATE INDEX idx_sales_reps_territory ON sales_reps(territory_id);
CREATE INDEX idx_sales_reps_manager ON sales_reps(manager_id);

-- Forecasting
CREATE INDEX idx_forecasts_period ON sales_forecasts(forecast_year, forecast_quarter, forecast_month);
CREATE INDEX idx_forecasts_rep ON sales_forecasts(sales_rep_id, forecast_year);

-- Interactions & Notes
CREATE INDEX idx_interactions_account ON customer_interactions(account_id, interaction_date);
CREATE INDEX idx_notes_related ON notes(related_to_type, related_to_id);

-- Integration
CREATE INDEX idx_crm_integration_status ON crm_integration_log(integration_status, log_timestamp);

-- ============================================================================
-- COMMENTS
-- ============================================================================

COMMENT ON TABLE leads IS 'Lead management with qualification and conversion tracking';
COMMENT ON TABLE accounts IS 'Enhanced customer accounts with hierarchy and health scoring';
COMMENT ON TABLE contacts IS 'Individual contacts within accounts with decision-making roles';
COMMENT ON TABLE opportunities IS 'Sales pipeline with stages, probability, and forecasting';
COMMENT ON TABLE quotations IS 'Price quotes and proposals with approval workflow';
COMMENT ON TABLE campaigns IS 'Marketing campaigns with ROI tracking';
COMMENT ON TABLE cases IS 'Customer support cases with SLA management';
COMMENT ON TABLE contracts IS 'Customer contracts with renewal tracking';
COMMENT ON TABLE sales_reps IS 'Sales team members with quota and performance tracking';
COMMENT ON TABLE sales_forecasts IS 'Sales forecasting by period, territory, and rep';
COMMENT ON TABLE crm_integration_log IS 'Integration tracking with ERP and master data';
