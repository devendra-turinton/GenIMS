-- GenIMS Customer Service & Support Schema
-- Complete customer service from ticketing to field service

-- ============================================================================
-- SERVICE TICKETS (ENHANCED)
-- ============================================================================

CREATE TABLE service_tickets (
    ticket_id VARCHAR(50) PRIMARY KEY,
    ticket_number VARCHAR(50) UNIQUE NOT NULL,
    
    -- Customer Information
    account_id VARCHAR(50) NOT NULL, -- FK to accounts (CRM)
    contact_id VARCHAR(50), -- FK to contacts (CRM)
    
    -- Ticket Source
    channel VARCHAR(30), -- phone, email, chat, web_portal, social_media, walk_in
    source_reference VARCHAR(200), -- Email ID, chat session ID, etc.
    
    -- Classification
    ticket_type VARCHAR(50), -- incident, service_request, question, complaint, feedback
    category VARCHAR(100), -- technical, billing, delivery, quality, installation, training
    subcategory VARCHAR(100),
    product_category VARCHAR(100),
    
    -- Issue Details
    subject VARCHAR(200) NOT NULL,
    description TEXT NOT NULL,
    
    -- Priority (Dynamic)
    priority VARCHAR(20) DEFAULT 'medium',
    -- critical, urgent, high, medium, low
    
    priority_reason VARCHAR(200), -- Why this priority was assigned
    
    -- Status
    ticket_status VARCHAR(30) DEFAULT 'new',
    -- new, assigned, in_progress, pending_customer, pending_vendor,
    -- on_hold, resolved, closed, cancelled
    
    status_reason VARCHAR(200),
    
    -- Related Records
    related_order_id VARCHAR(50), -- FK to sales_orders (ERP)
    related_product VARCHAR(200),
    related_serial_number VARCHAR(100),
    
    -- SLA Tracking
    sla_id VARCHAR(50), -- FK to sla_definitions
    response_due_datetime TIMESTAMP,
    resolution_due_datetime TIMESTAMP,
    
    first_response_datetime TIMESTAMP,
    resolved_datetime TIMESTAMP,
    closed_datetime TIMESTAMP,
    
    response_sla_breached BOOLEAN DEFAULT false,
    resolution_sla_breached BOOLEAN DEFAULT false,
    
    -- Assignment
    assigned_to VARCHAR(50), -- FK to service_agents
    assigned_team VARCHAR(50), -- FK to service_teams
    assigned_datetime TIMESTAMP,
    
    -- Routing
    routed_to_queue VARCHAR(50), -- FK to service_queues
    
    -- Escalation
    escalation_level INTEGER DEFAULT 0, -- 0=none, 1=L1, 2=L2, 3=L3
    escalated_to VARCHAR(50), -- FK to service_agents
    escalated_datetime TIMESTAMP,
    escalation_reason TEXT,
    
    -- Resolution
    resolution_summary TEXT,
    root_cause VARCHAR(200),
    resolution_code VARCHAR(50), -- FK to resolution_codes
    
    -- Customer Satisfaction
    csat_rating INTEGER, -- 1-5
    csat_comment TEXT,
    csat_survey_sent BOOLEAN DEFAULT false,
    csat_survey_sent_datetime TIMESTAMP,
    
    -- Knowledge Base Link
    kb_article_used VARCHAR(50), -- FK to kb_articles
    
    -- Metrics
    first_response_time_minutes INTEGER,
    resolution_time_minutes INTEGER,
    handle_time_minutes INTEGER, -- Total active time
    reopened_count INTEGER DEFAULT 0,
    
    -- Tags
    tags TEXT, -- JSON array for categorization
    
    created_by VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE ticket_comments (
    comment_id VARCHAR(50) PRIMARY KEY,
    ticket_id VARCHAR(50) NOT NULL, -- FK to service_tickets
    
    -- Comment Details
    comment_text TEXT NOT NULL,
    comment_type VARCHAR(30), -- note, solution, customer_response, internal_note
    
    -- Visibility
    is_public BOOLEAN DEFAULT true, -- Visible to customer
    is_internal BOOLEAN DEFAULT false,
    
    -- Attachments
    attachments TEXT, -- JSON array of URLs
    
    -- User
    created_by VARCHAR(50),
    created_by_type VARCHAR(20), -- agent, customer, system
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE ticket_attachments (
    attachment_id VARCHAR(50) PRIMARY KEY,
    ticket_id VARCHAR(50) NOT NULL, -- FK to service_tickets
    
    -- File Details
    file_name VARCHAR(200),
    file_size_bytes BIGINT,
    file_type VARCHAR(50),
    file_url VARCHAR(500),
    
    -- Metadata
    uploaded_by VARCHAR(50),
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- KNOWLEDGE BASE
-- ============================================================================

CREATE TABLE kb_categories (
    category_id VARCHAR(50) PRIMARY KEY,
    category_code VARCHAR(50) UNIQUE NOT NULL,
    category_name VARCHAR(200) NOT NULL,
    
    -- Hierarchy
    parent_category_id VARCHAR(50), -- FK to kb_categories
    
    -- Display
    display_order INTEGER,
    icon_url VARCHAR(500),
    
    description TEXT,
    
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE kb_articles (
    article_id VARCHAR(50) PRIMARY KEY,
    article_number VARCHAR(50) UNIQUE NOT NULL,
    
    -- Article Details
    title VARCHAR(200) NOT NULL,
    summary TEXT,
    content TEXT NOT NULL, -- HTML or Markdown
    
    -- Classification
    category_id VARCHAR(50), -- FK to kb_categories
    article_type VARCHAR(30), -- how_to, troubleshooting, faq, best_practice, announcement
    
    -- Product Association
    products TEXT, -- JSON array of product names
    product_categories TEXT, -- JSON array
    
    -- Keywords & Tags
    keywords TEXT,
    tags TEXT, -- JSON array
    
    -- Status
    article_status VARCHAR(30) DEFAULT 'draft',
    -- draft, under_review, published, archived
    
    -- Publishing
    published_date DATE,
    published_by VARCHAR(50),
    
    -- Versioning
    version VARCHAR(20),
    previous_version_id VARCHAR(50), -- FK to kb_articles
    
    -- Metrics
    view_count INTEGER DEFAULT 0,
    helpful_count INTEGER DEFAULT 0,
    not_helpful_count INTEGER DEFAULT 0,
    avg_rating DECIMAL(3,2), -- 1.0 to 5.0
    
    -- Usage
    times_used_in_tickets INTEGER DEFAULT 0,
    last_used_date TIMESTAMP,
    
    -- Attachments
    attachments TEXT, -- JSON array of URLs
    
    -- SEO
    meta_description TEXT,
    
    -- Author
    author_id VARCHAR(50),
    
    is_active BOOLEAN DEFAULT true,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE kb_article_ratings (
    rating_id VARCHAR(50) PRIMARY KEY,
    article_id VARCHAR(50) NOT NULL, -- FK to kb_articles
    
    -- Rating
    rating INTEGER, -- 1-5
    is_helpful BOOLEAN,
    
    -- Feedback
    feedback_text TEXT,
    
    -- User
    rated_by VARCHAR(50),
    rated_by_type VARCHAR(20), -- customer, agent
    
    rated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- SLA DEFINITIONS
-- ============================================================================

CREATE TABLE sla_definitions (
    sla_id VARCHAR(50) PRIMARY KEY,
    sla_code VARCHAR(50) UNIQUE NOT NULL,
    sla_name VARCHAR(200) NOT NULL,
    
    -- Applicability
    customer_tier VARCHAR(20), -- strategic, key, standard, all
    priority VARCHAR(20), -- critical, urgent, high, medium, low, all
    ticket_type VARCHAR(50), -- incident, service_request, all
    category VARCHAR(100), -- technical, billing, all
    
    -- Service Hours
    service_hours VARCHAR(30) DEFAULT '24x7',
    -- 24x7, business_hours_only, extended_hours
    
    -- Response Time SLA
    response_time_minutes INTEGER,
    response_time_unit VARCHAR(20), -- minutes, hours
    
    -- Resolution Time SLA
    resolution_time_minutes INTEGER,
    resolution_time_unit VARCHAR(20),
    
    -- Escalation Rules
    escalation_enabled BOOLEAN DEFAULT true,
    escalation_threshold_pct INTEGER DEFAULT 80, -- Escalate at 80% of SLA
    
    -- Notification
    notify_customer BOOLEAN DEFAULT true,
    notify_manager BOOLEAN DEFAULT true,
    
    -- Status
    is_active BOOLEAN DEFAULT true,
    effective_date DATE,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- WARRANTY MANAGEMENT
-- ============================================================================

CREATE TABLE warranty_registrations (
    warranty_id VARCHAR(50) PRIMARY KEY,
    warranty_number VARCHAR(50) UNIQUE NOT NULL,
    
    -- Customer & Product
    account_id VARCHAR(50) NOT NULL, -- FK to accounts
    contact_id VARCHAR(50), -- FK to contacts
    
    product_name VARCHAR(200) NOT NULL,
    product_category VARCHAR(100),
    serial_number VARCHAR(100),
    model_number VARCHAR(100),
    
    -- Purchase Information
    sales_order_id VARCHAR(50), -- FK to sales_orders
    purchase_date DATE NOT NULL,
    invoice_number VARCHAR(100),
    
    -- Warranty Terms
    warranty_type VARCHAR(50), -- standard, extended, lifetime
    warranty_start_date DATE NOT NULL,
    warranty_end_date DATE NOT NULL,
    warranty_duration_months INTEGER,
    
    -- Coverage
    coverage_type VARCHAR(50), -- parts_only, labor_only, parts_and_labor, comprehensive
    coverage_details TEXT,
    terms_conditions TEXT,
    
    -- Status
    warranty_status VARCHAR(30) DEFAULT 'active',
    -- active, expired, cancelled, transferred
    
    -- Registration
    registered_date DATE,
    registered_by VARCHAR(50),
    
    -- Transfer (if sold to another customer)
    transferred_to_account_id VARCHAR(50), -- FK to accounts
    transfer_date DATE,
    
    is_active BOOLEAN DEFAULT true,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE warranty_claims (
    claim_id VARCHAR(50) PRIMARY KEY,
    claim_number VARCHAR(50) UNIQUE NOT NULL,
    
    -- Warranty Link
    warranty_id VARCHAR(50) NOT NULL, -- FK to warranty_registrations
    
    -- Ticket Link
    ticket_id VARCHAR(50), -- FK to service_tickets
    
    -- Claim Details
    claim_date DATE NOT NULL,
    issue_description TEXT NOT NULL,
    
    -- Classification
    failure_type VARCHAR(50), -- defect, malfunction, damage, wear_tear
    failure_category VARCHAR(50), -- mechanical, electrical, software
    
    -- Claim Status
    claim_status VARCHAR(30) DEFAULT 'submitted',
    -- submitted, under_review, approved, rejected, processed, closed
    
    -- Approval
    approved BOOLEAN DEFAULT false,
    approved_by VARCHAR(50),
    approved_date DATE,
    rejection_reason TEXT,
    
    -- Resolution
    resolution_type VARCHAR(50), -- repair, replacement, refund, credit
    
    -- Costs
    labor_cost DECIMAL(12,2) DEFAULT 0,
    parts_cost DECIMAL(12,2) DEFAULT 0,
    total_claim_amount DECIMAL(12,2) DEFAULT 0,
    
    customer_responsibility DECIMAL(12,2) DEFAULT 0, -- Amount customer pays
    warranty_coverage DECIMAL(12,2) DEFAULT 0, -- Amount covered by warranty
    
    -- Processing
    processed_date DATE,
    processed_by VARCHAR(50),
    
    notes TEXT,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- RMA (RETURN MERCHANDISE AUTHORIZATION)
-- ============================================================================

CREATE TABLE rma_requests (
    rma_id VARCHAR(50) PRIMARY KEY,
    rma_number VARCHAR(50) UNIQUE NOT NULL,
    
    -- Customer & Order
    account_id VARCHAR(50) NOT NULL, -- FK to accounts
    contact_id VARCHAR(50), -- FK to contacts
    sales_order_id VARCHAR(50), -- FK to sales_orders
    
    -- Ticket Link
    ticket_id VARCHAR(50), -- FK to service_tickets
    
    -- RMA Type
    rma_type VARCHAR(50), -- return, repair, exchange, credit
    
    -- Reason
    return_reason VARCHAR(50),
    -- defective, wrong_item, damaged_in_transit, not_as_described,
    -- no_longer_needed, ordered_by_mistake
    
    reason_description TEXT,
    
    -- Status
    rma_status VARCHAR(30) DEFAULT 'requested',
    -- requested, approved, rejected, shipped_by_customer, received,
    -- inspecting, processing, completed, cancelled
    
    -- Approval
    approved BOOLEAN DEFAULT false,
    approved_by VARCHAR(50),
    approved_date DATE,
    rejection_reason TEXT,
    
    -- Return Instructions
    return_instructions TEXT,
    return_address TEXT,
    
    -- Shipping
    customer_shipment_tracking VARCHAR(100),
    customer_ship_date DATE,
    
    received_date DATE,
    received_by VARCHAR(50),
    
    -- Inspection
    inspection_status VARCHAR(30), -- pending, pass, fail
    inspection_notes TEXT,
    condition_on_receipt VARCHAR(50), -- new, good, damaged, defective
    
    -- Resolution
    resolution_type VARCHAR(50), -- refund, replacement, repair, credit, reject
    
    refund_amount DECIMAL(12,2) DEFAULT 0,
    refund_method VARCHAR(50), -- original_payment, store_credit, check
    refund_processed_date DATE,
    
    replacement_order_id VARCHAR(50), -- FK to sales_orders
    
    -- Restocking
    restocking_fee DECIMAL(12,2) DEFAULT 0,
    restocking_fee_pct DECIMAL(5,2) DEFAULT 0,
    
    -- Warehouse Integration
    warehouse_receipt_id VARCHAR(50), -- FK to WMS receiving_tasks
    
    notes TEXT,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE rma_line_items (
    rma_line_id VARCHAR(50) PRIMARY KEY,
    rma_id VARCHAR(50) NOT NULL, -- FK to rma_requests
    line_number INTEGER,
    
    -- Product
    material_id VARCHAR(50), -- FK to materials
    product_name VARCHAR(200),
    serial_number VARCHAR(100),
    
    -- Quantity
    quantity_returned DECIMAL(15,4),
    unit_of_measure VARCHAR(20),
    
    -- Pricing
    original_unit_price DECIMAL(12,4),
    refund_unit_price DECIMAL(12,4),
    line_total_refund DECIMAL(15,2),
    
    -- Condition
    condition_on_return VARCHAR(50),
    
    -- Disposition
    disposition VARCHAR(50),
    -- restock, repair, scrap, return_to_vendor, donate
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- FIELD SERVICE MANAGEMENT
-- ============================================================================

CREATE TABLE field_service_appointments (
    appointment_id VARCHAR(50) PRIMARY KEY,
    appointment_number VARCHAR(50) UNIQUE NOT NULL,
    
    -- Customer
    account_id VARCHAR(50) NOT NULL, -- FK to accounts
    contact_id VARCHAR(50), -- FK to contacts
    
    -- Ticket Link
    ticket_id VARCHAR(50), -- FK to service_tickets
    
    -- Service Type
    service_type VARCHAR(50),
    -- installation, repair, maintenance, inspection, training, consultation
    
    -- Scheduling
    appointment_date DATE NOT NULL,
    scheduled_start_time TIME,
    scheduled_end_time TIME,
    estimated_duration_minutes INTEGER,
    
    -- Status
    appointment_status VARCHAR(30) DEFAULT 'scheduled',
    -- scheduled, confirmed, in_progress, completed, cancelled, no_show
    
    -- Assignment
    assigned_technician_id VARCHAR(50), -- FK to field_technicians
    
    -- Location
    service_location_address TEXT,
    service_location_city VARCHAR(100),
    service_location_state VARCHAR(100),
    service_location_postal_code VARCHAR(20),
    service_location_gps POINT, -- PostGIS point (latitude, longitude)
    
    -- Check-in / Check-out
    checked_in_datetime TIMESTAMP,
    checked_out_datetime TIMESTAMP,
    actual_duration_minutes INTEGER,
    
    -- Travel
    travel_time_minutes INTEGER,
    travel_distance_km DECIMAL(10,2),
    
    -- Work Performed
    work_performed TEXT,
    parts_used TEXT, -- JSON array
    
    -- Equipment/Asset
    equipment_serial_number VARCHAR(100),
    asset_id VARCHAR(50), -- FK to maintenance_assets (CMMS)
    
    -- Customer Signature
    customer_signature_url VARCHAR(500),
    customer_signature_datetime TIMESTAMP,
    
    -- Follow-up
    follow_up_required BOOLEAN DEFAULT false,
    follow_up_appointment_id VARCHAR(50), -- FK to field_service_appointments
    
    -- Billing
    labor_charges DECIMAL(12,2) DEFAULT 0,
    parts_charges DECIMAL(12,2) DEFAULT 0,
    travel_charges DECIMAL(12,2) DEFAULT 0,
    total_charges DECIMAL(12,2) DEFAULT 0,
    
    notes TEXT,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE field_technicians (
    technician_id VARCHAR(50) PRIMARY KEY,
    employee_id VARCHAR(50), -- FK to employees
    technician_code VARCHAR(50) UNIQUE NOT NULL,
    
    -- Personal
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    email VARCHAR(100),
    phone VARCHAR(50),
    mobile VARCHAR(50),
    
    -- Skills & Certifications
    skill_areas TEXT, -- JSON array: HVAC, electrical, mechanical
    certifications TEXT, -- JSON array
    certification_expiry JSONB, -- JSON object with cert: expiry_date
    
    -- Service Area
    service_territory VARCHAR(100),
    home_base_location VARCHAR(200),
    
    -- Availability
    available_for_dispatch BOOLEAN DEFAULT true,
    current_location_gps POINT,
    last_location_update TIMESTAMP,
    
    -- Performance
    avg_job_rating DECIMAL(3,2), -- 1.0 to 5.0
    total_jobs_completed INTEGER DEFAULT 0,
    
    -- Status
    technician_status VARCHAR(30) DEFAULT 'available',
    -- available, on_job, in_transit, on_break, off_duty
    
    is_active BOOLEAN DEFAULT true,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- SERVICE PARTS INVENTORY
-- ============================================================================

CREATE TABLE service_parts (
    service_part_id VARCHAR(50) PRIMARY KEY,
    part_number VARCHAR(100) UNIQUE NOT NULL,
    part_name VARCHAR(200) NOT NULL,
    
    -- Classification
    part_category VARCHAR(50), -- consumable, repairable, replacement
    part_type VARCHAR(50), -- mechanical, electrical, electronic, accessory
    
    -- Specifications
    description TEXT,
    manufacturer VARCHAR(200),
    manufacturer_part_number VARCHAR(100),
    
    -- Compatibility
    compatible_products TEXT, -- JSON array of product names
    compatible_models TEXT, -- JSON array
    
    -- Inventory
    unit_of_measure VARCHAR(20),
    current_stock DECIMAL(15,4) DEFAULT 0,
    min_stock_level DECIMAL(15,4),
    reorder_point DECIMAL(15,4),
    
    -- Locations
    warehouse_locations TEXT, -- JSON array of warehouse_id:bin_location
    
    -- Technician Stock
    stock_allocated_to_technicians DECIMAL(15,4) DEFAULT 0,
    
    -- Pricing
    standard_cost DECIMAL(12,4),
    service_price DECIMAL(12,4), -- Price charged to customer
    
    -- Usage
    annual_usage_quantity DECIMAL(15,4),
    last_used_date DATE,
    
    -- Obsolescence
    is_obsolete BOOLEAN DEFAULT false,
    replacement_part_id VARCHAR(50), -- FK to service_parts
    
    is_active BOOLEAN DEFAULT true,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE service_parts_usage (
    usage_id VARCHAR(50) PRIMARY KEY,
    
    -- Service Part
    service_part_id VARCHAR(50) NOT NULL, -- FK to service_parts
    
    -- Quantity
    quantity_used DECIMAL(15,4),
    unit_of_measure VARCHAR(20),
    
    -- Cost
    unit_cost DECIMAL(12,4),
    total_cost DECIMAL(15,2),
    
    -- Usage Context
    usage_type VARCHAR(30), -- field_service, repair, warranty, internal
    
    ticket_id VARCHAR(50), -- FK to service_tickets
    appointment_id VARCHAR(50), -- FK to field_service_appointments
    warranty_claim_id VARCHAR(50), -- FK to warranty_claims
    
    -- Technician
    used_by_technician_id VARCHAR(50), -- FK to field_technicians
    
    usage_date DATE,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- CUSTOMER FEEDBACK & SATISFACTION
-- ============================================================================

CREATE TABLE customer_surveys (
    survey_id VARCHAR(50) PRIMARY KEY,
    survey_code VARCHAR(50) UNIQUE NOT NULL,
    survey_name VARCHAR(200) NOT NULL,
    
    -- Survey Type
    survey_type VARCHAR(30), -- csat, nps, ces, custom
    
    -- Trigger
    trigger_event VARCHAR(50),
    -- ticket_closed, appointment_completed, order_delivered, periodic
    
    -- Questions
    questions TEXT, -- JSON array of questions
    
    -- Status
    survey_status VARCHAR(30) DEFAULT 'active', -- active, inactive, archived
    
    is_active BOOLEAN DEFAULT true,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE survey_responses (
    response_id VARCHAR(50) PRIMARY KEY,
    
    -- Survey
    survey_id VARCHAR(50) NOT NULL, -- FK to customer_surveys
    
    -- Customer
    account_id VARCHAR(50), -- FK to accounts
    contact_id VARCHAR(50), -- FK to contacts
    
    -- Context
    ticket_id VARCHAR(50), -- FK to service_tickets
    appointment_id VARCHAR(50), -- FK to field_service_appointments
    
    -- CSAT (Customer Satisfaction Score)
    csat_rating INTEGER, -- 1-5
    
    -- NPS (Net Promoter Score)
    nps_score INTEGER, -- 0-10
    
    -- CES (Customer Effort Score)
    ces_score INTEGER, -- 1-7
    
    -- Responses
    responses TEXT, -- JSON object with question_id: answer
    
    -- Feedback
    general_feedback TEXT,
    
    -- Sentiment
    sentiment VARCHAR(20), -- positive, neutral, negative
    sentiment_score DECIMAL(5,2), -- -1.0 to 1.0
    
    -- Response Date
    responded_at TIMESTAMP,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE customer_feedback (
    feedback_id VARCHAR(50) PRIMARY KEY,
    
    -- Customer
    account_id VARCHAR(50) NOT NULL, -- FK to accounts
    contact_id VARCHAR(50), -- FK to contacts
    
    -- Feedback Type
    feedback_type VARCHAR(30), -- compliment, complaint, suggestion, review
    
    -- Context
    ticket_id VARCHAR(50), -- FK to service_tickets
    product_name VARCHAR(200),
    
    -- Feedback
    subject VARCHAR(200),
    feedback_text TEXT NOT NULL,
    
    -- Rating
    overall_rating INTEGER, -- 1-5
    
    -- Status
    feedback_status VARCHAR(30) DEFAULT 'submitted',
    -- submitted, acknowledged, under_review, addressed, closed
    
    -- Response
    response_text TEXT,
    responded_by VARCHAR(50),
    responded_at TIMESTAMP,
    
    -- Sentiment Analysis
    sentiment VARCHAR(20), -- positive, neutral, negative
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- ESCALATION MANAGEMENT
-- ============================================================================

CREATE TABLE escalation_rules (
    rule_id VARCHAR(50) PRIMARY KEY,
    rule_code VARCHAR(50) UNIQUE NOT NULL,
    rule_name VARCHAR(200) NOT NULL,
    
    -- Trigger Conditions
    priority VARCHAR(20), -- critical, urgent, high, all
    category VARCHAR(100),
    
    -- SLA Threshold
    sla_breach_threshold_pct INTEGER DEFAULT 80, -- Escalate at 80% of SLA
    
    -- Escalation Levels
    level_1_escalate_to VARCHAR(50), -- Team lead
    level_1_threshold_minutes INTEGER,
    
    level_2_escalate_to VARCHAR(50), -- Manager
    level_2_threshold_minutes INTEGER,
    
    level_3_escalate_to VARCHAR(50), -- Director
    level_3_threshold_minutes INTEGER,
    
    -- Notification
    notify_customer BOOLEAN DEFAULT true,
    notify_management BOOLEAN DEFAULT true,
    
    -- Status
    is_active BOOLEAN DEFAULT true,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE ticket_escalations (
    escalation_id VARCHAR(50) PRIMARY KEY,
    ticket_id VARCHAR(50) NOT NULL, -- FK to service_tickets
    
    -- Escalation Details
    escalation_level INTEGER, -- 1, 2, 3
    escalation_reason VARCHAR(200),
    
    escalated_from VARCHAR(50), -- Agent/team it was escalated from
    escalated_to VARCHAR(50), -- Agent/team it was escalated to
    
    escalated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Resolution
    de_escalated BOOLEAN DEFAULT false,
    de_escalated_at TIMESTAMP,
    de_escalation_reason TEXT
);

-- ============================================================================
-- SERVICE TEAMS & QUEUES
-- ============================================================================

CREATE TABLE service_teams (
    team_id VARCHAR(50) PRIMARY KEY,
    team_code VARCHAR(50) UNIQUE NOT NULL,
    team_name VARCHAR(200) NOT NULL,
    
    -- Team Type
    team_type VARCHAR(50), -- technical, billing, general, field_service
    
    -- Specialization
    specialization VARCHAR(100), -- Product line, category, etc.
    
    -- Team Lead
    team_lead_id VARCHAR(50), -- FK to service_agents
    
    -- Members
    team_members TEXT, -- JSON array of agent_ids
    team_size INTEGER,
    
    -- Service Hours
    service_hours VARCHAR(30), -- 24x7, business_hours
    
    is_active BOOLEAN DEFAULT true,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE service_queues (
    queue_id VARCHAR(50) PRIMARY KEY,
    queue_code VARCHAR(50) UNIQUE NOT NULL,
    queue_name VARCHAR(200) NOT NULL,
    
    -- Queue Type
    queue_type VARCHAR(50), -- general, technical, billing, vip, escalation
    
    -- Assignment
    assigned_team_id VARCHAR(50), -- FK to service_teams
    
    -- Routing Rules
    auto_assign BOOLEAN DEFAULT true,
    assignment_method VARCHAR(30), -- round_robin, least_busy, skill_based
    
    -- Priority
    queue_priority INTEGER DEFAULT 5, -- Lower number = higher priority
    
    -- Metrics
    current_ticket_count INTEGER DEFAULT 0,
    avg_wait_time_minutes INTEGER,
    
    is_active BOOLEAN DEFAULT true,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE service_agents (
    agent_id VARCHAR(50) PRIMARY KEY,
    employee_id VARCHAR(50), -- FK to employees
    agent_code VARCHAR(50) UNIQUE NOT NULL,
    
    -- Personal
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    email VARCHAR(100),
    phone VARCHAR(50),
    
    -- Team Assignment
    team_id VARCHAR(50), -- FK to service_teams
    
    -- Skills
    skill_areas TEXT, -- JSON array: technical, billing, installation
    product_expertise TEXT, -- JSON array of product categories
    language_skills TEXT, -- JSON array: English, Hindi, etc.
    
    -- Performance
    avg_csat_rating DECIMAL(3,2), -- 1.0 to 5.0
    total_tickets_resolved INTEGER DEFAULT 0,
    avg_resolution_time_hours DECIMAL(8,2),
    first_contact_resolution_rate DECIMAL(5,2), -- Percentage
    
    -- Availability
    agent_status VARCHAR(30) DEFAULT 'available',
    -- available, busy, on_break, in_meeting, offline
    
    current_ticket_count INTEGER DEFAULT 0,
    max_concurrent_tickets INTEGER DEFAULT 5,
    
    -- Employment
    hire_date DATE,
    
    is_active BOOLEAN DEFAULT true,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- RESOLUTION CODES & ROOT CAUSES
-- ============================================================================

CREATE TABLE resolution_codes (
    code_id VARCHAR(50) PRIMARY KEY,
    code VARCHAR(50) UNIQUE NOT NULL,
    description VARCHAR(200) NOT NULL,
    
    -- Category
    category VARCHAR(100), -- technical, user_error, system_issue, configuration
    
    -- Typical Resolution Time
    typical_resolution_minutes INTEGER,
    
    is_active BOOLEAN DEFAULT true,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- SERVICE ANALYTICS & METRICS
-- ============================================================================

CREATE TABLE service_metrics_daily (
    metric_id VARCHAR(50) PRIMARY KEY,
    
    -- Date
    metric_date DATE NOT NULL,
    
    -- Ticket Metrics
    tickets_created INTEGER DEFAULT 0,
    tickets_resolved INTEGER DEFAULT 0,
    tickets_closed INTEGER DEFAULT 0,
    tickets_reopened INTEGER DEFAULT 0,
    
    backlog_count INTEGER DEFAULT 0,
    
    -- Response Metrics
    avg_first_response_time_minutes INTEGER,
    response_sla_met_count INTEGER DEFAULT 0,
    response_sla_breached_count INTEGER DEFAULT 0,
    response_sla_compliance_pct DECIMAL(5,2),
    
    -- Resolution Metrics
    avg_resolution_time_minutes INTEGER,
    resolution_sla_met_count INTEGER DEFAULT 0,
    resolution_sla_breached_count INTEGER DEFAULT 0,
    resolution_sla_compliance_pct DECIMAL(5,2),
    
    -- FCR (First Contact Resolution)
    fcr_count INTEGER DEFAULT 0,
    fcr_rate_pct DECIMAL(5,2),
    
    -- Customer Satisfaction
    csat_responses_count INTEGER DEFAULT 0,
    avg_csat_rating DECIMAL(3,2),
    csat_5_count INTEGER DEFAULT 0, -- Excellent ratings
    csat_1_2_count INTEGER DEFAULT 0, -- Poor ratings
    
    -- Channel Distribution
    phone_tickets INTEGER DEFAULT 0,
    email_tickets INTEGER DEFAULT 0,
    chat_tickets INTEGER DEFAULT 0,
    portal_tickets INTEGER DEFAULT 0,
    
    -- Priority Distribution
    critical_tickets INTEGER DEFAULT 0,
    high_tickets INTEGER DEFAULT 0,
    medium_tickets INTEGER DEFAULT 0,
    low_tickets INTEGER DEFAULT 0,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- SELF-SERVICE PORTAL
-- ============================================================================

CREATE TABLE portal_users (
    portal_user_id VARCHAR(50) PRIMARY KEY,
    
    -- Account & Contact
    account_id VARCHAR(50) NOT NULL, -- FK to accounts
    contact_id VARCHAR(50), -- FK to contacts
    
    -- Login
    username VARCHAR(100) UNIQUE NOT NULL,
    email VARCHAR(100) NOT NULL,
    
    -- Password (hashed)
    password_hash VARCHAR(255),
    password_salt VARCHAR(100),
    
    -- Status
    user_status VARCHAR(30) DEFAULT 'active', -- active, locked, suspended
    
    -- Activity
    last_login_datetime TIMESTAMP,
    login_count INTEGER DEFAULT 0,
    
    -- Verification
    email_verified BOOLEAN DEFAULT false,
    verification_token VARCHAR(100),
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- SERVICE INTEGRATION LOG
-- ============================================================================

CREATE TABLE service_integration_log (
    log_id VARCHAR(50) PRIMARY KEY,
    log_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Integration Direction
    integration_direction VARCHAR(30),
    -- SERVICE_TO_CRM, SERVICE_TO_ERP, SERVICE_TO_WMS, 
    -- SERVICE_TO_CMMS, CRM_TO_SERVICE, ERP_TO_SERVICE
    
    -- Document Type
    document_type VARCHAR(50),
    -- ticket, warranty, rma, field_service, survey
    
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

-- Service Tickets
CREATE INDEX idx_tickets_status ON service_tickets(ticket_status, priority);
CREATE INDEX idx_tickets_account ON service_tickets(account_id, ticket_status);
CREATE INDEX idx_tickets_assigned ON service_tickets(assigned_to, ticket_status);
CREATE INDEX idx_tickets_created ON service_tickets(created_at);
CREATE INDEX idx_tickets_sla ON service_tickets(resolution_sla_breached, ticket_status);
CREATE INDEX idx_tickets_channel ON service_tickets(channel, created_at);
CREATE INDEX idx_ticket_comments_ticket ON ticket_comments(ticket_id, created_at);

-- Knowledge Base
CREATE INDEX idx_kb_articles_status ON kb_articles(article_status, is_active);
CREATE INDEX idx_kb_articles_category ON kb_articles(category_id);
CREATE INDEX idx_kb_articles_published ON kb_articles(published_date DESC);
CREATE INDEX idx_kb_articles_views ON kb_articles(view_count DESC);
CREATE INDEX idx_kb_ratings_article ON kb_article_ratings(article_id);

-- SLA
CREATE INDEX idx_sla_tier_priority ON sla_definitions(customer_tier, priority);

-- Warranty
CREATE INDEX idx_warranty_account ON warranty_registrations(account_id, warranty_status);
CREATE INDEX idx_warranty_serial ON warranty_registrations(serial_number);
CREATE INDEX idx_warranty_dates ON warranty_registrations(warranty_end_date);
CREATE INDEX idx_warranty_claims_warranty ON warranty_claims(warranty_id, claim_status);

-- RMA
CREATE INDEX idx_rma_account ON rma_requests(account_id, rma_status);
CREATE INDEX idx_rma_ticket ON rma_requests(ticket_id);
CREATE INDEX idx_rma_order ON rma_requests(sales_order_id);
CREATE INDEX idx_rma_lines_rma ON rma_line_items(rma_id);

-- Field Service
CREATE INDEX idx_appointments_date ON field_service_appointments(appointment_date, appointment_status);
CREATE INDEX idx_appointments_technician ON field_service_appointments(assigned_technician_id, appointment_date);
CREATE INDEX idx_appointments_account ON field_service_appointments(account_id);
CREATE INDEX idx_technicians_status ON field_technicians(technician_status, is_active);

-- Service Parts
CREATE INDEX idx_service_parts_stock ON service_parts(current_stock, reorder_point);
CREATE INDEX idx_parts_usage_part ON service_parts_usage(service_part_id, usage_date);
CREATE INDEX idx_parts_usage_ticket ON service_parts_usage(ticket_id);

-- Feedback
CREATE INDEX idx_surveys_type ON customer_surveys(survey_type, survey_status);
CREATE INDEX idx_survey_responses_survey ON survey_responses(survey_id, responded_at);
CREATE INDEX idx_feedback_account ON customer_feedback(account_id, created_at);
CREATE INDEX idx_feedback_status ON customer_feedback(feedback_status);

-- Escalations
CREATE INDEX idx_escalation_rules_active ON escalation_rules(is_active);
CREATE INDEX idx_ticket_escalations_ticket ON ticket_escalations(ticket_id, escalated_at);

-- Teams & Agents
CREATE INDEX idx_service_teams_active ON service_teams(is_active);
CREATE INDEX idx_service_agents_team ON service_agents(team_id, agent_status);
CREATE INDEX idx_service_agents_status ON service_agents(agent_status, is_active);

-- Analytics
CREATE INDEX idx_metrics_date ON service_metrics_daily(metric_date DESC);

-- Portal
CREATE INDEX idx_portal_users_account ON portal_users(account_id);
CREATE INDEX idx_portal_users_username ON portal_users(username);

-- Integration
CREATE INDEX idx_service_integration_status ON service_integration_log(integration_status, log_timestamp);

-- ============================================================================
-- COMMENTS
-- ============================================================================

COMMENT ON TABLE service_tickets IS 'Enhanced multi-channel service tickets with SLA tracking';
COMMENT ON TABLE kb_articles IS 'Self-service knowledge base articles';
COMMENT ON TABLE sla_definitions IS 'Service level agreement rules by customer tier and priority';
COMMENT ON TABLE warranty_registrations IS 'Product warranty registrations';
COMMENT ON TABLE warranty_claims IS 'Warranty claim processing';
COMMENT ON TABLE rma_requests IS 'Return merchandise authorization for product returns';
COMMENT ON TABLE field_service_appointments IS 'On-site service appointments with GPS tracking';
COMMENT ON TABLE service_parts IS 'Service parts inventory for repairs';
COMMENT ON TABLE customer_surveys IS 'CSAT, NPS, CES surveys';
COMMENT ON TABLE survey_responses IS 'Customer survey responses and satisfaction scores';
COMMENT ON TABLE escalation_rules IS 'Automatic escalation rules';
COMMENT ON TABLE service_teams IS 'Support teams with specializations';
COMMENT ON TABLE service_agents IS 'Customer service agents with performance tracking';
COMMENT ON TABLE service_metrics_daily IS 'Daily service KPI dashboard metrics';
COMMENT ON TABLE service_integration_log IS 'Integration tracking with CRM, ERP, WMS, CMMS';
