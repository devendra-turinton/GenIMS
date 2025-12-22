-- GenIMS Supplier Portal / Advanced Procurement Module
-- Integrated with Master Data, ERP, WMS, Financial, and Quality systems

-- ============================================================================
-- RFQ - REQUEST FOR QUOTE
-- ============================================================================

CREATE TABLE rfq_headers (
    rfq_id VARCHAR(50) PRIMARY KEY,
    rfq_number VARCHAR(50) UNIQUE NOT NULL,
    
    -- Request Details
    rfq_title VARCHAR(200) NOT NULL,
    rfq_description TEXT,
    
    -- Category
    rfq_type VARCHAR(30) DEFAULT 'standard',
    -- standard, urgent, blanket, spot_buy
    
    -- Requestor
    requested_by VARCHAR(50), -- FK to employees
    department_id VARCHAR(50), -- FK to departments
    
    -- Dates
    rfq_date DATE NOT NULL,
    response_deadline DATE NOT NULL,
    expected_delivery_date DATE,
    
    -- Requirements
    total_estimated_value DECIMAL(15,2),
    currency_code VARCHAR(3) DEFAULT 'INR',
    
    -- Quality Requirements
    quality_requirements TEXT,
    technical_specifications TEXT,
    
    -- Delivery Terms
    delivery_location VARCHAR(50), -- FK to factories/warehouses
    payment_terms VARCHAR(100),
    incoterms VARCHAR(20), -- FOB, CIF, DDP, etc.
    
    -- Status
    rfq_status VARCHAR(30) DEFAULT 'draft',
    -- draft, published, response_period, evaluation, awarded, cancelled
    
    -- Publishing
    published_date DATE,
    published_by VARCHAR(50),
    
    -- Award
    awarded_date DATE,
    awarded_to VARCHAR(50), -- FK to suppliers
    award_notes TEXT,
    
    -- Documents
    attachment_urls TEXT[], -- Array of document URLs
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE rfq_lines (
    line_id VARCHAR(50) PRIMARY KEY,
    rfq_id VARCHAR(50) NOT NULL, -- FK to rfq_headers
    line_number INTEGER NOT NULL,
    
    -- Material/Service
    item_type VARCHAR(20) DEFAULT 'material',
    -- material, service, tooling
    
    material_id VARCHAR(50), -- FK to materials (if material)
    item_description TEXT NOT NULL,
    
    -- Quantity
    quantity DECIMAL(15,4) NOT NULL,
    unit_of_measure VARCHAR(20),
    
    -- Target
    target_price DECIMAL(15,2),
    estimated_total DECIMAL(15,2),
    
    -- Specifications
    technical_specs TEXT,
    quality_requirements TEXT,
    
    -- Delivery
    required_by_date DATE,
    delivery_schedule TEXT, -- JSON: delivery milestones
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE rfq_suppliers (
    rfq_supplier_id VARCHAR(50) PRIMARY KEY,
    rfq_id VARCHAR(50) NOT NULL, -- FK to rfq_headers
    supplier_id VARCHAR(50) NOT NULL, -- FK to suppliers
    
    -- Invitation
    invited_date TIMESTAMP,
    invited_by VARCHAR(50),
    invitation_method VARCHAR(30), -- email, portal, both
    
    -- Response
    response_status VARCHAR(30) DEFAULT 'pending',
    -- pending, viewed, responded, declined, no_response
    
    viewed_date TIMESTAMP,
    responded_date TIMESTAMP,
    
    -- Decline Reason
    decline_reason TEXT,
    
    -- Evaluation
    is_shortlisted BOOLEAN DEFAULT false,
    shortlist_notes TEXT,
    
    UNIQUE(rfq_id, supplier_id),
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE rfq_responses (
    response_id VARCHAR(50) PRIMARY KEY,
    response_number VARCHAR(50) UNIQUE NOT NULL,
    
    rfq_id VARCHAR(50) NOT NULL, -- FK to rfq_headers
    supplier_id VARCHAR(50) NOT NULL, -- FK to suppliers
    
    -- Response Details
    response_date TIMESTAMP NOT NULL,
    valid_until_date DATE,
    
    -- Commercial Terms
    currency_code VARCHAR(3) DEFAULT 'INR',
    payment_terms VARCHAR(100),
    delivery_terms TEXT,
    
    -- Totals
    total_quoted_value DECIMAL(15,2),
    
    -- Additional Info
    remarks TEXT,
    alternate_proposal TEXT,
    
    -- Documents
    attachment_urls TEXT[],
    
    -- Status
    response_status VARCHAR(30) DEFAULT 'submitted',
    -- submitted, under_evaluation, shortlisted, awarded, rejected
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE rfq_response_lines (
    response_line_id VARCHAR(50) PRIMARY KEY,
    response_id VARCHAR(50) NOT NULL, -- FK to rfq_responses
    rfq_line_id VARCHAR(50) NOT NULL, -- FK to rfq_lines
    line_number INTEGER,
    
    -- Quote
    unit_price DECIMAL(15,4) NOT NULL,
    total_price DECIMAL(15,2),
    
    -- Delivery
    lead_time_days INTEGER,
    delivery_date DATE,
    
    -- Compliance
    meets_specifications BOOLEAN DEFAULT true,
    deviation_notes TEXT,
    
    -- Alternate Offer
    alternate_material_id VARCHAR(50),
    alternate_description TEXT,
    alternate_unit_price DECIMAL(15,4),
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE quote_comparison (
    comparison_id VARCHAR(50) PRIMARY KEY,
    rfq_id VARCHAR(50) NOT NULL, -- FK to rfq_headers
    
    -- Comparison Details
    comparison_date DATE NOT NULL,
    compared_by VARCHAR(50), -- FK to employees
    
    -- Criteria Weights
    price_weight DECIMAL(5,2) DEFAULT 40.0,
    quality_weight DECIMAL(5,2) DEFAULT 30.0,
    delivery_weight DECIMAL(5,2) DEFAULT 20.0,
    service_weight DECIMAL(5,2) DEFAULT 10.0,
    
    -- Recommendation
    recommended_supplier_id VARCHAR(50), -- FK to suppliers
    recommendation_notes TEXT,
    
    -- Approval
    approved_by VARCHAR(50),
    approved_date DATE,
    
    -- Comparison Data (JSON)
    comparison_data JSONB,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- SUPPLIER CONTRACTS & AGREEMENTS
-- ============================================================================

CREATE TABLE supplier_contracts (
    contract_id VARCHAR(50) PRIMARY KEY,
    contract_number VARCHAR(50) UNIQUE NOT NULL,
    
    -- Supplier
    supplier_id VARCHAR(50) NOT NULL, -- FK to suppliers
    
    -- Contract Details
    contract_name VARCHAR(200) NOT NULL,
    contract_type VARCHAR(30),
    -- price_agreement, blanket_order, framework, service_contract
    
    -- Dates
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    
    -- Commercial Terms
    currency_code VARCHAR(3) DEFAULT 'INR',
    payment_terms VARCHAR(100),
    
    -- Volume Commitment
    minimum_order_quantity DECIMAL(15,4),
    maximum_order_quantity DECIMAL(15,4),
    committed_annual_value DECIMAL(15,2),
    
    -- Terms & Conditions
    delivery_terms TEXT,
    quality_terms TEXT,
    warranty_terms TEXT,
    return_policy TEXT,
    
    -- Penalties & Incentives
    penalty_for_delay DECIMAL(15,2),
    incentive_for_early DECIMAL(15,2),
    
    -- Auto-Renewal
    auto_renew BOOLEAN DEFAULT false,
    renewal_notice_days INTEGER DEFAULT 60,
    
    -- Status
    contract_status VARCHAR(30) DEFAULT 'draft',
    -- draft, active, expired, terminated, renewed
    
    -- Approvals
    approved_by VARCHAR(50),
    approved_date DATE,
    
    -- Documents
    contract_document_url TEXT,
    
    -- Performance Tracking
    actual_spend_to_date DECIMAL(15,2) DEFAULT 0,
    orders_placed INTEGER DEFAULT 0,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE contract_pricing (
    pricing_id VARCHAR(50) PRIMARY KEY,
    contract_id VARCHAR(50) NOT NULL, -- FK to supplier_contracts
    
    -- Material
    material_id VARCHAR(50) NOT NULL, -- FK to materials
    
    -- Pricing
    unit_price DECIMAL(15,4) NOT NULL,
    currency_code VARCHAR(3) DEFAULT 'INR',
    
    -- Validity
    effective_from DATE NOT NULL,
    effective_to DATE,
    
    -- Volume Breaks
    min_order_quantity DECIMAL(15,4),
    max_order_quantity DECIMAL(15,4),
    
    -- Lead Time
    standard_lead_time_days INTEGER,
    
    -- Price Revision
    price_revision_date DATE,
    previous_unit_price DECIMAL(15,4),
    price_change_pct DECIMAL(5,2),
    
    -- Status
    is_active BOOLEAN DEFAULT true,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- SUPPLIER PERFORMANCE TRACKING
-- ============================================================================

CREATE TABLE supplier_performance_metrics (
    metric_id VARCHAR(50) PRIMARY KEY,
    
    -- Supplier & Period
    supplier_id VARCHAR(50) NOT NULL, -- FK to suppliers
    metric_period VARCHAR(7) NOT NULL, -- YYYY-MM format
    
    -- Delivery Performance
    total_pos_issued INTEGER DEFAULT 0,
    pos_delivered_ontime INTEGER DEFAULT 0,
    ontime_delivery_pct DECIMAL(5,2),
    average_lead_time_days DECIMAL(5,1),
    
    -- Quality Performance
    total_quantity_received DECIMAL(15,4) DEFAULT 0,
    quantity_accepted DECIMAL(15,4) DEFAULT 0,
    quantity_rejected DECIMAL(15,4) DEFAULT 0,
    defect_ppm INTEGER DEFAULT 0, -- Parts Per Million
    quality_acceptance_pct DECIMAL(5,2),
    
    -- Responsiveness
    rfqs_sent INTEGER DEFAULT 0,
    rfqs_responded INTEGER DEFAULT 0,
    response_rate_pct DECIMAL(5,2),
    avg_response_time_hours DECIMAL(6,2),
    
    -- Commercial
    total_spend DECIMAL(15,2) DEFAULT 0,
    invoice_accuracy_pct DECIMAL(5,2),
    payment_disputes INTEGER DEFAULT 0,
    
    -- Compliance
    certifications_valid BOOLEAN DEFAULT true,
    documentation_complete BOOLEAN DEFAULT true,
    audit_score DECIMAL(5,2),
    
    -- Overall Score
    overall_score DECIMAL(5,2), -- 0-100
    performance_rating VARCHAR(20), -- excellent, good, acceptable, needs_improvement, poor
    
    -- Trends
    previous_period_score DECIMAL(5,2),
    score_change DECIMAL(5,2),
    trend VARCHAR(20), -- improving, stable, declining
    
    UNIQUE(supplier_id, metric_period),
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE supplier_scorecards (
    scorecard_id VARCHAR(50) PRIMARY KEY,
    
    -- Supplier
    supplier_id VARCHAR(50) NOT NULL, -- FK to suppliers
    
    -- Period
    scorecard_period VARCHAR(7) NOT NULL, -- YYYY-MM
    scorecard_type VARCHAR(30) DEFAULT 'monthly',
    -- monthly, quarterly, annual
    
    -- Scoring Categories (0-100 each)
    delivery_score DECIMAL(5,2),
    quality_score DECIMAL(5,2),
    responsiveness_score DECIMAL(5,2),
    commercial_score DECIMAL(5,2),
    sustainability_score DECIMAL(5,2),
    
    -- Weighted Overall Score
    overall_score DECIMAL(5,2),
    
    -- Rating
    supplier_rating VARCHAR(20),
    -- excellent (90-100), good (75-89), acceptable (60-74),
    -- needs_improvement (40-59), poor (<40)
    
    -- Status/Actions
    action_required BOOLEAN DEFAULT false,
    action_plan TEXT,
    improvement_plan_due_date DATE,
    
    -- Review
    reviewed_by VARCHAR(50),
    review_date DATE,
    review_notes TEXT,
    
    -- Published to Supplier
    published_to_supplier BOOLEAN DEFAULT false,
    published_date DATE,
    
    UNIQUE(supplier_id, scorecard_period),
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE supplier_rating_history (
    history_id VARCHAR(50) PRIMARY KEY,
    supplier_id VARCHAR(50) NOT NULL, -- FK to suppliers
    
    -- Rating Change
    rating_date DATE NOT NULL,
    previous_rating VARCHAR(20),
    new_rating VARCHAR(20),
    
    -- Reason
    change_reason TEXT,
    changed_by VARCHAR(50),
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- SUPPLIER INVOICES & 3-WAY MATCHING
-- ============================================================================

CREATE TABLE supplier_invoices (
    invoice_id VARCHAR(50) PRIMARY KEY,
    invoice_number VARCHAR(50) NOT NULL,
    supplier_invoice_number VARCHAR(50) NOT NULL, -- Supplier's invoice #
    
    -- Supplier & PO
    supplier_id VARCHAR(50) NOT NULL, -- FK to suppliers
    purchase_order_id VARCHAR(50), -- FK to purchase_orders
    
    -- Invoice Details
    invoice_date DATE NOT NULL,
    due_date DATE NOT NULL,
    
    -- Amounts
    subtotal DECIMAL(15,2) NOT NULL,
    tax_amount DECIMAL(15,2) DEFAULT 0,
    freight_charges DECIMAL(15,2) DEFAULT 0,
    other_charges DECIMAL(15,2) DEFAULT 0,
    discount_amount DECIMAL(15,2) DEFAULT 0,
    total_amount DECIMAL(15,2) NOT NULL,
    
    currency_code VARCHAR(3) DEFAULT 'INR',
    exchange_rate DECIMAL(12,6) DEFAULT 1.0,
    
    -- Payment Terms
    payment_terms VARCHAR(100),
    
    -- 3-Way Matching
    matching_status VARCHAR(30) DEFAULT 'pending',
    -- pending, matched, variance, approved, rejected
    
    po_match BOOLEAN DEFAULT false,
    receipt_match BOOLEAN DEFAULT false,
    price_match BOOLEAN DEFAULT false,
    quantity_match BOOLEAN DEFAULT false,
    
    -- Variances
    quantity_variance DECIMAL(15,4) DEFAULT 0,
    price_variance DECIMAL(15,2) DEFAULT 0,
    total_variance DECIMAL(15,2) DEFAULT 0,
    
    variance_reason TEXT,
    variance_approved_by VARCHAR(50),
    variance_approved_date DATE,
    
    -- Approval
    invoice_status VARCHAR(30) DEFAULT 'received',
    -- received, under_review, approved, rejected, paid, cancelled
    
    approved_by VARCHAR(50),
    approved_date DATE,
    approval_notes TEXT,
    
    -- Payment
    payment_status VARCHAR(30) DEFAULT 'pending',
    -- pending, scheduled, paid, overdue
    
    payment_id VARCHAR(50), -- FK to payments (ERP)
    paid_date DATE,
    paid_amount DECIMAL(15,2),
    
    -- GL Posting
    gl_journal_entry_id VARCHAR(50), -- FK to journal_entry_headers
    gl_posted BOOLEAN DEFAULT false,
    
    -- Documents
    invoice_document_url TEXT,
    
    -- Submission
    submitted_via VARCHAR(30) DEFAULT 'portal',
    -- portal, email, manual_entry
    
    submitted_by VARCHAR(50), -- Supplier user who submitted
    submitted_at TIMESTAMP,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE supplier_invoice_lines (
    line_id VARCHAR(50) PRIMARY KEY,
    invoice_id VARCHAR(50) NOT NULL, -- FK to supplier_invoices
    line_number INTEGER NOT NULL,
    
    -- Reference
    po_line_id VARCHAR(50), -- FK to purchase order lines
    receipt_line_id VARCHAR(50), -- FK to WMS receiving task lines
    
    -- Material/Service
    material_id VARCHAR(50), -- FK to materials
    line_description TEXT NOT NULL,
    
    -- Quantity
    invoiced_quantity DECIMAL(15,4) NOT NULL,
    unit_of_measure VARCHAR(20),
    
    -- Pricing
    unit_price DECIMAL(15,4) NOT NULL,
    line_total DECIMAL(15,2) NOT NULL,
    
    -- Matching
    po_quantity DECIMAL(15,4),
    received_quantity DECIMAL(15,4),
    po_unit_price DECIMAL(15,4),
    
    quantity_variance DECIMAL(15,4) DEFAULT 0,
    price_variance DECIMAL(15,2) DEFAULT 0,
    
    match_status VARCHAR(30) DEFAULT 'pending',
    -- matched, variance, approved
    
    -- GL Account
    expense_account_id VARCHAR(50), -- FK to chart_of_accounts
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE three_way_match_log (
    log_id VARCHAR(50) PRIMARY KEY,
    invoice_id VARCHAR(50) NOT NULL, -- FK to supplier_invoices
    
    -- Matching Process
    match_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    match_type VARCHAR(30),
    -- automatic, manual, override
    
    -- Components
    po_id VARCHAR(50),
    receipt_id VARCHAR(50),
    
    -- Results
    match_result VARCHAR(30),
    -- matched, quantity_variance, price_variance, multiple_variances, failed
    
    -- Details
    expected_amount DECIMAL(15,2),
    actual_amount DECIMAL(15,2),
    variance_amount DECIMAL(15,2),
    variance_pct DECIMAL(5,2),
    
    -- Tolerance
    within_tolerance BOOLEAN DEFAULT false,
    tolerance_pct DECIMAL(5,2) DEFAULT 2.0,
    
    -- Action
    action_taken VARCHAR(30),
    -- auto_approved, pending_review, rejected, escalated
    
    notes TEXT
);

-- ============================================================================
-- SUPPLIER QUALIFICATION & ONBOARDING
-- ============================================================================

CREATE TABLE supplier_qualification (
    qualification_id VARCHAR(50) PRIMARY KEY,
    supplier_id VARCHAR(50) NOT NULL, -- FK to suppliers
    
    -- Qualification Status
    qualification_status VARCHAR(30) DEFAULT 'initiated',
    -- initiated, documents_pending, under_review, audit_scheduled,
    -- audit_completed, sample_testing, trial_order, approved, rejected
    
    -- Documentation
    business_license_verified BOOLEAN DEFAULT false,
    tax_registration_verified BOOLEAN DEFAULT false,
    bank_details_verified BOOLEAN DEFAULT false,
    iso_certificate_verified BOOLEAN DEFAULT false,
    
    -- Financial Assessment
    financial_health_score DECIMAL(5,2),
    credit_rating VARCHAR(20),
    payment_capacity_assessment TEXT,
    
    -- Capability Assessment
    production_capacity_verified BOOLEAN DEFAULT false,
    quality_system_verified BOOLEAN DEFAULT false,
    technical_capability_score DECIMAL(5,2),
    
    -- Audit
    audit_scheduled_date DATE,
    audit_completed_date DATE,
    audit_score DECIMAL(5,2),
    audit_report_url TEXT,
    
    -- Sample Approval
    sample_submitted BOOLEAN DEFAULT false,
    sample_approved BOOLEAN DEFAULT false,
    sample_test_results TEXT,
    
    -- Trial Order
    trial_order_placed BOOLEAN DEFAULT false,
    trial_order_id VARCHAR(50), -- FK to purchase_orders
    trial_order_success BOOLEAN DEFAULT false,
    
    -- Final Decision
    approved_by VARCHAR(50),
    approved_date DATE,
    rejection_reason TEXT,
    
    -- Validity
    approval_valid_until DATE,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE supplier_documents (
    document_id VARCHAR(50) PRIMARY KEY,
    supplier_id VARCHAR(50) NOT NULL, -- FK to suppliers
    
    -- Document Details
    document_type VARCHAR(50) NOT NULL,
    -- business_license, tax_certificate, iso_9001, iso_14001,
    -- bank_statement, insurance, quality_certificate, test_report
    
    document_name VARCHAR(200) NOT NULL,
    document_number VARCHAR(100),
    
    -- Dates
    issue_date DATE,
    expiry_date DATE,
    
    -- Verification
    verified BOOLEAN DEFAULT false,
    verified_by VARCHAR(50),
    verified_date DATE,
    
    -- Status
    document_status VARCHAR(30) DEFAULT 'pending',
    -- pending, verified, expired, rejected
    
    -- Alert
    expiry_alert_sent BOOLEAN DEFAULT false,
    days_to_expiry INTEGER,
    
    -- File
    document_url TEXT NOT NULL,
    file_size_kb INTEGER,
    
    -- Notes
    notes TEXT,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE supplier_audits (
    audit_id VARCHAR(50) PRIMARY KEY,
    audit_number VARCHAR(50) UNIQUE NOT NULL,
    
    -- Supplier
    supplier_id VARCHAR(50) NOT NULL, -- FK to suppliers
    
    -- Audit Details
    audit_type VARCHAR(30) NOT NULL,
    -- initial, periodic, special, post_incident
    
    audit_scope VARCHAR(50),
    -- quality_system, production, warehouse, management
    
    -- Schedule
    planned_date DATE,
    actual_date DATE,
    audit_duration_hours DECIMAL(5,1),
    
    -- Team
    lead_auditor VARCHAR(50), -- FK to employees
    audit_team TEXT[], -- Array of employee IDs
    
    -- Location
    audit_location VARCHAR(200),
    
    -- Results
    audit_score DECIMAL(5,2), -- 0-100
    audit_rating VARCHAR(20),
    -- excellent, satisfactory, needs_improvement, unsatisfactory
    
    -- Findings
    major_findings INTEGER DEFAULT 0,
    minor_findings INTEGER DEFAULT 0,
    observations INTEGER DEFAULT 0,
    
    -- Follow-up
    followup_required BOOLEAN DEFAULT false,
    followup_date DATE,
    
    -- Reports
    audit_report_url TEXT,
    
    -- Status
    audit_status VARCHAR(30) DEFAULT 'planned',
    -- planned, in_progress, completed, report_pending, closed
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE audit_findings (
    finding_id VARCHAR(50) PRIMARY KEY,
    audit_id VARCHAR(50) NOT NULL, -- FK to supplier_audits
    
    -- Finding Details
    finding_number INTEGER,
    finding_type VARCHAR(30),
    -- major_nc, minor_nc, observation, positive
    
    finding_category VARCHAR(50),
    -- documentation, process, equipment, training, management
    
    finding_description TEXT NOT NULL,
    evidence TEXT,
    
    -- Requirement
    requirement_reference VARCHAR(100),
    -- ISO 9001:2015 clause 8.5.1
    
    -- Corrective Action
    corrective_action_required BOOLEAN DEFAULT false,
    corrective_action TEXT,
    responsible_person VARCHAR(200),
    target_date DATE,
    
    -- Closure
    finding_status VARCHAR(30) DEFAULT 'open',
    -- open, in_progress, completed, verified, closed
    
    closed_date DATE,
    closure_verified_by VARCHAR(50),
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- SUPPLIER COLLABORATION & PORTAL
-- ============================================================================

CREATE TABLE supplier_portal_users (
    portal_user_id VARCHAR(50) PRIMARY KEY,
    supplier_id VARCHAR(50) NOT NULL, -- FK to suppliers
    
    -- User Details
    user_email VARCHAR(200) UNIQUE NOT NULL,
    user_name VARCHAR(200) NOT NULL,
    user_phone VARCHAR(50),
    
    -- Role
    user_role VARCHAR(30),
    -- admin, sales, accounts, quality
    
    -- Permissions
    can_view_rfqs BOOLEAN DEFAULT true,
    can_submit_quotes BOOLEAN DEFAULT true,
    can_view_pos BOOLEAN DEFAULT true,
    can_submit_invoices BOOLEAN DEFAULT false,
    can_view_payments BOOLEAN DEFAULT false,
    can_view_performance BOOLEAN DEFAULT false,
    
    -- Status
    is_active BOOLEAN DEFAULT true,
    last_login TIMESTAMP,
    login_count INTEGER DEFAULT 0,
    
    -- Password (hashed)
    password_hash VARCHAR(200),
    password_reset_required BOOLEAN DEFAULT true,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE supplier_communications (
    communication_id VARCHAR(50) PRIMARY KEY,
    
    -- Parties
    supplier_id VARCHAR(50) NOT NULL, -- FK to suppliers
    from_party VARCHAR(20), -- buyer, supplier
    
    -- Message
    subject VARCHAR(200) NOT NULL,
    message_body TEXT NOT NULL,
    
    -- Reference
    reference_type VARCHAR(30),
    -- rfq, purchase_order, invoice, quality_issue, general
    
    reference_id VARCHAR(50), -- ID of referenced document
    
    -- Status
    message_status VARCHAR(30) DEFAULT 'sent',
    -- sent, read, replied, archived
    
    read_at TIMESTAMP,
    
    -- Attachments
    attachment_urls TEXT[],
    
    -- Threading
    parent_message_id VARCHAR(50), -- FK to supplier_communications
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE supplier_notifications (
    notification_id VARCHAR(50) PRIMARY KEY,
    supplier_id VARCHAR(50) NOT NULL, -- FK to suppliers
    
    -- Notification
    notification_type VARCHAR(50) NOT NULL,
    -- new_rfq, po_issued, payment_made, performance_review,
    -- document_expiring, audit_scheduled
    
    notification_title VARCHAR(200) NOT NULL,
    notification_message TEXT NOT NULL,
    
    -- Reference
    reference_type VARCHAR(30),
    reference_id VARCHAR(50),
    
    -- Priority
    priority VARCHAR(20) DEFAULT 'normal',
    -- low, normal, high, urgent
    
    -- Status
    notification_status VARCHAR(30) DEFAULT 'unread',
    -- unread, read, actioned, dismissed
    
    read_at TIMESTAMP,
    
    -- Delivery
    sent_via_email BOOLEAN DEFAULT true,
    sent_via_portal BOOLEAN DEFAULT true,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- PURCHASE REQUISITIONS (Integration with ERP)
-- ============================================================================

CREATE TABLE purchase_requisitions (
    requisition_id VARCHAR(50) PRIMARY KEY,
    requisition_number VARCHAR(50) UNIQUE NOT NULL,
    
    -- Requestor
    requested_by VARCHAR(50) NOT NULL, -- FK to employees
    department_id VARCHAR(50), -- FK to departments
    cost_center_id VARCHAR(50), -- FK to cost_centers
    
    -- Request Details
    requisition_date DATE NOT NULL,
    required_by_date DATE NOT NULL,
    
    requisition_type VARCHAR(30) DEFAULT 'standard',
    -- standard, urgent, capital, service
    
    -- Purpose
    purpose TEXT,
    justification TEXT,
    
    -- Budget
    budget_code VARCHAR(50),
    estimated_total DECIMAL(15,2),
    
    -- Status
    requisition_status VARCHAR(30) DEFAULT 'draft',
    -- draft, submitted, approved, rejected, converted_to_rfq,
    -- converted_to_po, cancelled
    
    -- Approval Workflow
    approval_level INTEGER DEFAULT 0,
    approved_by VARCHAR(50),
    approved_date DATE,
    rejection_reason TEXT,
    
    -- Conversion
    converted_to_rfq_id VARCHAR(50), -- FK to rfq_headers
    converted_to_po_id VARCHAR(50), -- FK to purchase_orders
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE purchase_requisition_lines (
    line_id VARCHAR(50) PRIMARY KEY,
    requisition_id VARCHAR(50) NOT NULL, -- FK to purchase_requisitions
    line_number INTEGER NOT NULL,
    
    -- Material/Service
    material_id VARCHAR(50), -- FK to materials
    item_description TEXT NOT NULL,
    
    -- Quantity
    quantity DECIMAL(15,4) NOT NULL,
    unit_of_measure VARCHAR(20),
    
    -- Estimated Cost
    estimated_unit_price DECIMAL(15,4),
    estimated_total DECIMAL(15,2),
    
    -- Preferred Supplier
    preferred_supplier_id VARCHAR(50), -- FK to suppliers
    
    -- Delivery
    delivery_location VARCHAR(50), -- FK to factories/warehouses
    required_by_date DATE,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- INTEGRATION LOGS
-- ============================================================================

CREATE TABLE supplier_portal_integration_log (
    log_id VARCHAR(50) PRIMARY KEY,
    log_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Integration Type
    integration_type VARCHAR(50) NOT NULL,
    -- rfq_to_suppliers, quote_to_po, po_to_erp, invoice_to_ap,
    -- performance_to_dashboard, contract_to_pricing
    
    -- Source & Target
    source_system VARCHAR(30), -- portal, erp, wms, financial
    target_system VARCHAR(30),
    
    -- Document
    source_document_type VARCHAR(50),
    source_document_id VARCHAR(50),
    target_document_type VARCHAR(50),
    target_document_id VARCHAR(50),
    
    -- Status
    integration_status VARCHAR(30) DEFAULT 'success',
    -- success, partial, failed
    
    error_message TEXT,
    
    -- Data
    integration_data JSONB
);

-- ============================================================================
-- INDICES
-- ============================================================================

-- RFQ
CREATE INDEX idx_rfq_headers_status ON rfq_headers(rfq_status, rfq_date);
CREATE INDEX idx_rfq_headers_deadline ON rfq_headers(response_deadline);
CREATE INDEX idx_rfq_lines_rfq ON rfq_lines(rfq_id);
CREATE INDEX idx_rfq_suppliers_rfq ON rfq_suppliers(rfq_id, response_status);
CREATE INDEX idx_rfq_responses_supplier ON rfq_responses(supplier_id, response_date);

-- Contracts
CREATE INDEX idx_supplier_contracts_supplier ON supplier_contracts(supplier_id, contract_status);
CREATE INDEX idx_supplier_contracts_dates ON supplier_contracts(start_date, end_date);
CREATE INDEX idx_contract_pricing_material ON contract_pricing(material_id, is_active);

-- Performance
CREATE INDEX idx_perf_metrics_supplier ON supplier_performance_metrics(supplier_id, metric_period);
CREATE INDEX idx_scorecards_supplier ON supplier_scorecards(supplier_id, scorecard_period);

-- Invoices
CREATE INDEX idx_supplier_invoices_supplier ON supplier_invoices(supplier_id, invoice_status);
CREATE INDEX idx_supplier_invoices_po ON supplier_invoices(purchase_order_id);
CREATE INDEX idx_supplier_invoices_matching ON supplier_invoices(matching_status);
CREATE INDEX idx_supplier_invoices_payment ON supplier_invoices(payment_status, due_date);

-- Qualification
CREATE INDEX idx_supplier_qual_status ON supplier_qualification(qualification_status);
CREATE INDEX idx_supplier_docs_expiry ON supplier_documents(supplier_id, expiry_date);
CREATE INDEX idx_supplier_audits_supplier ON supplier_audits(supplier_id, actual_date);

-- Portal
CREATE INDEX idx_portal_users_supplier ON supplier_portal_users(supplier_id, is_active);
CREATE INDEX idx_supplier_comms_supplier ON supplier_communications(supplier_id, created_at);
CREATE INDEX idx_supplier_notifs_status ON supplier_notifications(supplier_id, notification_status);

-- Requisitions
CREATE INDEX idx_purchase_reqs_status ON purchase_requisitions(requisition_status, requisition_date);
CREATE INDEX idx_purchase_reqs_requestor ON purchase_requisitions(requested_by);

-- ============================================================================
-- COMMENTS
-- ============================================================================

COMMENT ON TABLE rfq_headers IS 'Request for Quote headers';
COMMENT ON TABLE rfq_responses IS 'Supplier responses to RFQs';
COMMENT ON TABLE quote_comparison IS 'Multi-supplier quote comparison and recommendation';
COMMENT ON TABLE supplier_contracts IS 'Supplier contracts and pricing agreements';
COMMENT ON TABLE supplier_performance_metrics IS 'Monthly supplier performance tracking';
COMMENT ON TABLE supplier_scorecards IS 'Supplier performance scorecards';
COMMENT ON TABLE supplier_invoices IS 'Supplier invoices with 3-way matching';
COMMENT ON TABLE three_way_match_log IS 'Audit trail of invoice matching process';
COMMENT ON TABLE supplier_qualification IS 'Supplier onboarding and qualification process';
COMMENT ON TABLE supplier_audits IS 'Supplier audit tracking and results';
COMMENT ON TABLE supplier_portal_users IS 'Supplier portal user accounts';
COMMENT ON TABLE purchase_requisitions IS 'Internal purchase requisitions (pre-RFQ/PO)';
COMMENT ON TABLE supplier_portal_integration_log IS 'Integration tracking between supplier portal and other systems';
