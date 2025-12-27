-- GenIMS Quality Management System (QMS) Module
-- Comprehensive quality management integrated with MES, Customer Service, Supplier Portal

-- ============================================================================
-- NON-CONFORMANCE REPORTS (NCR)
-- ============================================================================

CREATE TABLE ncr_headers (
    ncr_id VARCHAR(50) PRIMARY KEY,
    ncr_number VARCHAR(50) UNIQUE NOT NULL,
    
    -- Source
    source_type VARCHAR(30) NOT NULL,
    -- incoming_inspection, in_process, final_inspection, 
    -- customer_complaint, supplier_quality, internal_audit
    
    source_document_id VARCHAR(50), -- Quality inspection, ticket, etc.
    
    -- Detection
    detected_date DATE NOT NULL,
    detected_by VARCHAR(50), -- FK to employees
    detection_location VARCHAR(50), -- Factory/warehouse
    
    -- Material/Product
    material_id VARCHAR(50), -- FK to materials
    product_id VARCHAR(50), -- FK to products
    batch_number VARCHAR(50),
    lot_number VARCHAR(50),
    serial_numbers TEXT, -- Comma-separated if multiple
    
    -- Quantity
    quantity_inspected DECIMAL(15,4),
    quantity_defective DECIMAL(15,4),
    unit_of_measure VARCHAR(20),
    
    -- Defect Details
    defect_type VARCHAR(50),
    -- dimensional, visual, functional, material, packaging, documentation
    
    defect_description TEXT NOT NULL,
    defect_severity VARCHAR(30),
    -- critical, major, minor
    
    -- Supplier (if applicable)
    supplier_id VARCHAR(50), -- FK to suppliers
    purchase_order_id VARCHAR(50), -- FK to purchase_orders
    
    -- Customer (if applicable)
    customer_id VARCHAR(50), -- FK to customers
    sales_order_id VARCHAR(50), -- FK to sales_orders
    
    -- Containment Actions
    containment_action TEXT,
    containment_completed BOOLEAN DEFAULT false,
    containment_date DATE,
    
    -- Disposition
    disposition VARCHAR(30),
    -- scrap, rework, use_as_is, return_to_supplier, sort
    
    disposition_quantity DECIMAL(15,4),
    disposition_notes TEXT,
    
    -- Cost Impact
    scrap_cost DECIMAL(15,2) DEFAULT 0,
    rework_cost DECIMAL(15,2) DEFAULT 0,
    sorting_cost DECIMAL(15,2) DEFAULT 0,
    total_cost DECIMAL(15,2) DEFAULT 0,
    
    -- Root Cause Analysis
    root_cause_method VARCHAR(30),
    -- 5_why, fishbone, fault_tree, 8d
    
    root_cause_description TEXT,
    root_cause_verified BOOLEAN DEFAULT false,
    
    -- Status
    ncr_status VARCHAR(30) DEFAULT 'open',
    -- open, contained, root_cause_identified, capa_created, 
    -- verification_pending, closed
    
    -- Closure
    closed_date DATE,
    closed_by VARCHAR(50),
    
    -- Verification
    verified_effective BOOLEAN DEFAULT false,
    verification_date DATE,
    verified_by VARCHAR(50),
    
    -- Priority
    priority VARCHAR(20) DEFAULT 'medium',
    -- low, medium, high, critical
    
    -- Photos/Documents
    attachment_urls TEXT[],
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE ncr_defect_details (
    defect_detail_id VARCHAR(50) PRIMARY KEY,
    ncr_id VARCHAR(50) NOT NULL, -- FK to ncr_headers
    
    -- Defect Characteristics
    characteristic_name VARCHAR(200) NOT NULL,
    specification VARCHAR(200),
    actual_value VARCHAR(200),
    
    -- Measurement
    measurement_method VARCHAR(100),
    measuring_equipment VARCHAR(100),
    
    -- Location on Part
    defect_location VARCHAR(200),
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- CORRECTIVE & PREVENTIVE ACTIONS (CAPA)
-- ============================================================================

CREATE TABLE capa_headers (
    capa_id VARCHAR(50) PRIMARY KEY,
    capa_number VARCHAR(50) UNIQUE NOT NULL,
    
    -- Type
    action_type VARCHAR(30) NOT NULL,
    -- corrective (fix problem), preventive (prevent occurrence)
    
    -- Source
    initiated_from VARCHAR(30),
    -- ncr, audit_finding, customer_complaint, risk_assessment, 
    -- management_review, continuous_improvement
    
    source_document_id VARCHAR(50), -- NCR ID, Audit ID, etc.
    
    -- Problem Description
    problem_description TEXT NOT NULL,
    problem_severity VARCHAR(30),
    -- low, medium, high, critical
    
    -- Immediate Actions (Containment)
    immediate_actions TEXT,
    immediate_actions_completed BOOLEAN DEFAULT false,
    
    -- Root Cause Analysis
    root_cause_analysis TEXT,
    root_cause_method VARCHAR(30),
    root_cause_identified BOOLEAN DEFAULT false,
    
    -- Corrective/Preventive Actions
    actions_planned TEXT NOT NULL,
    implementation_plan TEXT,
    
    -- Responsibility
    responsible_person VARCHAR(50) NOT NULL, -- FK to employees
    responsible_department VARCHAR(50), -- FK to departments
    
    -- Timeline
    target_completion_date DATE NOT NULL,
    actual_completion_date DATE,
    
    -- Verification
    verification_plan TEXT,
    verification_completed BOOLEAN DEFAULT false,
    verification_date DATE,
    verified_by VARCHAR(50),
    verification_result TEXT,
    
    -- Effectiveness Review
    effectiveness_review_date DATE,
    effectiveness_verified BOOLEAN DEFAULT false,
    effectiveness_notes TEXT,
    
    -- Status
    capa_status VARCHAR(30) DEFAULT 'open',
    -- open, in_progress, completed, verification_pending, 
    -- effectiveness_review, closed
    
    -- Closure
    closed_date DATE,
    closed_by VARCHAR(50),
    
    -- Cost
    implementation_cost DECIMAL(15,2) DEFAULT 0,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE capa_actions (
    action_id VARCHAR(50) PRIMARY KEY,
    capa_id VARCHAR(50) NOT NULL, -- FK to capa_headers
    action_sequence INTEGER,
    
    -- Action Details
    action_description TEXT NOT NULL,
    action_type VARCHAR(30),
    -- process_change, training, equipment, documentation, procedure
    
    -- Responsibility
    assigned_to VARCHAR(50) NOT NULL, -- FK to employees
    
    -- Timeline
    due_date DATE NOT NULL,
    completion_date DATE,
    
    -- Status
    action_status VARCHAR(30) DEFAULT 'pending',
    -- pending, in_progress, completed, overdue
    
    -- Evidence
    completion_evidence TEXT,
    attachment_urls TEXT[],
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- QUALITY AUDITS
-- ============================================================================

CREATE TABLE quality_audits (
    audit_id VARCHAR(50) PRIMARY KEY,
    audit_number VARCHAR(50) UNIQUE NOT NULL,
    
    -- Audit Type
    audit_type VARCHAR(30) NOT NULL,
    -- internal, supplier, customer, certification, process, product
    
    audit_standard VARCHAR(50),
    -- ISO_9001, IATF_16949, ISO_14001, AS9100, customer_specific
    
    -- Scope
    audit_scope TEXT NOT NULL,
    auditee_department VARCHAR(50), -- FK to departments
    auditee_supplier_id VARCHAR(50), -- FK to suppliers (if supplier audit)
    
    -- Schedule
    planned_date DATE NOT NULL,
    actual_start_date DATE,
    actual_end_date DATE,
    audit_duration_hours DECIMAL(5,1),
    
    -- Audit Team
    lead_auditor VARCHAR(50) NOT NULL, -- FK to employees
    audit_team TEXT[], -- Array of employee IDs
    
    -- Location
    audit_location VARCHAR(200),
    
    -- Results
    audit_score DECIMAL(5,2), -- 0-100
    audit_rating VARCHAR(30),
    -- excellent, satisfactory, needs_improvement, unsatisfactory
    
    -- Findings Summary
    total_findings INTEGER DEFAULT 0,
    major_findings INTEGER DEFAULT 0,
    minor_findings INTEGER DEFAULT 0,
    observations INTEGER DEFAULT 0,
    positive_findings INTEGER DEFAULT 0,
    
    -- Follow-up
    followup_required BOOLEAN DEFAULT false,
    followup_date DATE,
    
    -- Status
    audit_status VARCHAR(30) DEFAULT 'planned',
    -- planned, in_progress, report_pending, completed, closed
    
    -- Reports
    audit_report_url TEXT,
    
    -- Closure
    closed_date DATE,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE audit_findings (
    finding_id VARCHAR(50) PRIMARY KEY,
    audit_id VARCHAR(50) NOT NULL, -- FK to quality_audits
    finding_number INTEGER NOT NULL,
    
    -- Finding Type
    finding_type VARCHAR(30) NOT NULL,
    -- major_nc (non-conformance), minor_nc, observation, opportunity, positive
    
    -- Category
    finding_category VARCHAR(50),
    -- documentation, process, equipment, training, management, 
    -- measurement, material_handling
    
    -- Details
    finding_description TEXT NOT NULL,
    requirement_reference VARCHAR(200), -- e.g., ISO 9001:2015 clause 8.5.1
    objective_evidence TEXT,
    
    -- Impact
    impact_assessment TEXT,
    risk_level VARCHAR(20),
    -- low, medium, high
    
    -- Corrective Action
    corrective_action_required BOOLEAN DEFAULT false,
    linked_capa_id VARCHAR(50), -- FK to capa_headers
    
    responsible_person VARCHAR(50), -- FK to employees
    target_closure_date DATE,
    
    -- Status
    finding_status VARCHAR(30) DEFAULT 'open',
    -- open, capa_created, in_progress, completed, verified, closed
    
    -- Closure
    closure_date DATE,
    closure_verified_by VARCHAR(50),
    closure_notes TEXT,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- CONTROL PLANS
-- ============================================================================

CREATE TABLE control_plans (
    control_plan_id VARCHAR(50) PRIMARY KEY,
    control_plan_number VARCHAR(50) UNIQUE NOT NULL,
    
    -- Product/Process
    product_id VARCHAR(50), -- FK to products
    material_id VARCHAR(50), -- FK to materials
    process_name VARCHAR(200) NOT NULL,
    
    -- Details
    control_plan_title VARCHAR(200) NOT NULL,
    control_plan_type VARCHAR(30),
    -- prototype, pre_launch, production
    
    -- Version Control
    version VARCHAR(20) NOT NULL,
    revision_date DATE NOT NULL,
    supersedes_plan_id VARCHAR(50), -- FK to control_plans
    
    -- Responsibility
    prepared_by VARCHAR(50), -- FK to employees
    approved_by VARCHAR(50),
    approval_date DATE,
    
    -- Effectivity
    effective_date DATE NOT NULL,
    obsolete_date DATE,
    
    -- Status
    plan_status VARCHAR(30) DEFAULT 'draft',
    -- draft, approved, active, superseded, obsolete
    
    -- Documents
    document_url TEXT,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE control_plan_characteristics (
    characteristic_id VARCHAR(50) PRIMARY KEY,
    control_plan_id VARCHAR(50) NOT NULL, -- FK to control_plans
    sequence_number INTEGER,
    
    -- Process Step
    process_step VARCHAR(200) NOT NULL,
    
    -- Characteristic
    characteristic_name VARCHAR(200) NOT NULL,
    characteristic_type VARCHAR(30),
    -- product, process
    
    -- Specification
    specification VARCHAR(200) NOT NULL,
    lower_spec_limit DECIMAL(15,6),
    target_value DECIMAL(15,6),
    upper_spec_limit DECIMAL(15,6),
    unit_of_measure VARCHAR(20),
    
    -- Evaluation Method
    measurement_technique VARCHAR(200),
    measuring_equipment VARCHAR(200),
    
    -- Sample Plan
    sample_size VARCHAR(50),
    sample_frequency VARCHAR(100),
    
    -- Control Method
    control_method VARCHAR(30),
    -- spc, 100_percent, periodic, first_last_piece
    
    -- Reaction Plan
    reaction_plan TEXT,
    
    -- Responsible
    responsible_person VARCHAR(50), -- FK to employees
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- STATISTICAL PROCESS CONTROL (SPC)
-- ============================================================================

CREATE TABLE spc_control_charts (
    chart_id VARCHAR(50) PRIMARY KEY,
    chart_number VARCHAR(50) UNIQUE NOT NULL,
    
    -- Process
    process_name VARCHAR(200) NOT NULL,
    characteristic_name VARCHAR(200) NOT NULL,
    
    -- Chart Type
    chart_type VARCHAR(30) NOT NULL,
    -- x_bar_r, x_bar_s, x_mr, p, np, c, u
    
    -- Specification
    specification VARCHAR(200),
    lower_spec_limit DECIMAL(15,6),
    target_value DECIMAL(15,6),
    upper_spec_limit DECIMAL(15,6),
    unit_of_measure VARCHAR(20),
    
    -- Control Limits (calculated)
    upper_control_limit DECIMAL(15,6),
    center_line DECIMAL(15,6),
    lower_control_limit DECIMAL(15,6),
    
    -- Capability
    cpk DECIMAL(5,3),
    cp DECIMAL(5,3),
    ppk DECIMAL(5,3),
    pp DECIMAL(5,3),
    
    -- Subgroup
    subgroup_size INTEGER,
    subgroup_frequency VARCHAR(100),
    
    -- Status
    chart_status VARCHAR(30) DEFAULT 'active',
    -- active, out_of_control, under_review, inactive
    
    -- Last Update
    last_data_point_date TIMESTAMP,
    last_calculation_date TIMESTAMP,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE spc_data_points (
    data_point_id VARCHAR(50) PRIMARY KEY,
    chart_id VARCHAR(50) NOT NULL, -- FK to spc_control_charts
    
    -- Measurement
    measurement_timestamp TIMESTAMP NOT NULL,
    subgroup_number INTEGER,
    
    -- Values
    measurement_value DECIMAL(15,6) NOT NULL,
    range_value DECIMAL(15,6), -- For X-bar R charts
    
    -- Operator
    measured_by VARCHAR(50), -- FK to employees
    
    -- Out of Control
    out_of_control BOOLEAN DEFAULT false,
    violation_type VARCHAR(50),
    -- point_beyond_limits, run_above_center, run_below_center, trend, cycle
    
    -- Action Taken
    action_taken TEXT,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- CALIBRATION MANAGEMENT
-- ============================================================================

CREATE TABLE measuring_equipment (
    equipment_id VARCHAR(50) PRIMARY KEY,
    equipment_number VARCHAR(50) UNIQUE NOT NULL,
    
    -- Equipment Details
    equipment_name VARCHAR(200) NOT NULL,
    equipment_type VARCHAR(50),
    -- micrometer, caliper, gauge, scale, thermometer, pressure_gauge, etc.
    
    manufacturer VARCHAR(200),
    model_number VARCHAR(100),
    serial_number VARCHAR(100),
    
    -- Location
    location VARCHAR(50), -- FK to factories/departments
    responsible_person VARCHAR(50), -- FK to employees
    
    -- Specification
    measurement_range VARCHAR(100),
    accuracy VARCHAR(100),
    resolution VARCHAR(50),
    
    -- Calibration
    calibration_frequency_days INTEGER NOT NULL, -- e.g., 90, 180, 365
    last_calibration_date DATE,
    next_calibration_due DATE NOT NULL,
    
    calibration_method VARCHAR(100),
    calibration_standard VARCHAR(200),
    
    -- Status
    equipment_status VARCHAR(30) DEFAULT 'active',
    -- active, calibration_due, overdue, out_of_service, retired
    
    -- Lockout
    locked_out BOOLEAN DEFAULT false,
    lockout_reason TEXT,
    
    -- Purchase Info
    purchase_date DATE,
    purchase_cost DECIMAL(15,2),
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE calibration_records (
    calibration_id VARCHAR(50) PRIMARY KEY,
    calibration_number VARCHAR(50) UNIQUE NOT NULL,
    
    equipment_id VARCHAR(50) NOT NULL, -- FK to measuring_equipment
    
    -- Calibration Details
    calibration_date DATE NOT NULL,
    next_due_date DATE NOT NULL,
    
    -- Performed By
    calibrated_by VARCHAR(50), -- FK to employees (if internal)
    calibration_lab VARCHAR(200), -- External lab name
    
    -- Results
    calibration_result VARCHAR(30),
    -- pass, fail, adjusted_and_pass, out_of_tolerance
    
    as_found_condition TEXT,
    as_left_condition TEXT,
    
    -- Measurements
    measurement_results JSONB, -- JSON: array of measurement points
    
    -- Certificate
    certificate_number VARCHAR(100),
    certificate_url TEXT,
    
    -- Standards Used
    standard_equipment TEXT, -- Reference standards used
    standard_traceability TEXT,
    
    -- Cost
    calibration_cost DECIMAL(15,2),
    
    -- Notes
    notes TEXT,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE calibration_alerts (
    alert_id VARCHAR(50) PRIMARY KEY,
    equipment_id VARCHAR(50) NOT NULL, -- FK to measuring_equipment
    
    -- Alert Details
    alert_type VARCHAR(30),
    -- due_30_days, due_7_days, overdue
    
    alert_date DATE NOT NULL,
    days_until_due INTEGER,
    
    -- Notification
    notification_sent BOOLEAN DEFAULT false,
    notification_date TIMESTAMP,
    notified_users TEXT[], -- Employee IDs
    
    -- Resolution
    resolved BOOLEAN DEFAULT false,
    resolved_date DATE,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- DOCUMENT CONTROL
-- ============================================================================

CREATE TABLE quality_documents (
    document_id VARCHAR(50) PRIMARY KEY,
    document_number VARCHAR(50) UNIQUE NOT NULL,
    
    -- Document Details
    document_title VARCHAR(200) NOT NULL,
    document_type VARCHAR(50),
    -- procedure, work_instruction, form, specification, 
    -- control_plan, inspection_instruction
    
    -- Version Control
    version VARCHAR(20) NOT NULL,
    revision_number INTEGER DEFAULT 1,
    revision_date DATE NOT NULL,
    supersedes_document_id VARCHAR(50), -- FK to quality_documents
    
    -- Content
    document_description TEXT,
    document_url TEXT NOT NULL,
    
    -- Ownership
    document_owner VARCHAR(50), -- FK to employees
    department_id VARCHAR(50), -- FK to departments
    
    -- Approval Workflow
    prepared_by VARCHAR(50),
    reviewed_by VARCHAR(50),
    approved_by VARCHAR(50),
    approval_date DATE,
    
    -- Effectivity
    effective_date DATE NOT NULL,
    obsolete_date DATE,
    
    -- Status
    document_status VARCHAR(30) DEFAULT 'draft',
    -- draft, under_review, approved, active, obsolete
    
    -- Distribution
    distribution_list TEXT[], -- Employee IDs or department IDs
    
    -- Review
    periodic_review_required BOOLEAN DEFAULT true,
    review_frequency_months INTEGER DEFAULT 12,
    next_review_date DATE,
    
    -- Change Control
    change_reason TEXT,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE document_revisions (
    revision_id VARCHAR(50) PRIMARY KEY,
    document_id VARCHAR(50) NOT NULL, -- FK to quality_documents
    
    -- Revision Details
    revision_number INTEGER NOT NULL,
    revision_date DATE NOT NULL,
    
    -- Changes
    changes_summary TEXT NOT NULL,
    sections_affected TEXT,
    
    -- Responsibility
    revised_by VARCHAR(50), -- FK to employees
    approved_by VARCHAR(50),
    
    -- Version
    document_url TEXT,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- CUSTOMER COMPLAINTS (Integrated with Customer Service)
-- ============================================================================

CREATE TABLE customer_complaints (
    complaint_id VARCHAR(50) PRIMARY KEY,
    complaint_number VARCHAR(50) UNIQUE NOT NULL,
    
    -- Customer Service Link
    service_ticket_id VARCHAR(50), -- FK to service_tickets
    
    -- Customer
    customer_id VARCHAR(50) NOT NULL, -- FK to customers
    customer_contact VARCHAR(200),
    
    -- Product
    product_id VARCHAR(50), -- FK to products
    sales_order_id VARCHAR(50), -- FK to sales_orders
    batch_number VARCHAR(50),
    serial_number VARCHAR(50),
    
    -- Complaint Details
    complaint_date DATE NOT NULL,
    complaint_description TEXT NOT NULL,
    complaint_type VARCHAR(50),
    -- quality, delivery, documentation, damage, performance
    
    -- Severity
    severity VARCHAR(30),
    -- critical, major, minor
    
    safety_issue BOOLEAN DEFAULT false,
    
    -- Quantity
    quantity_affected DECIMAL(15,4),
    quantity_returned DECIMAL(15,4),
    
    -- Response
    immediate_action TEXT,
    customer_response TEXT,
    
    -- Investigation
    root_cause TEXT,
    investigation_method VARCHAR(30), -- 5_why, 8d, fishbone
    
    -- Linked Records
    linked_ncr_id VARCHAR(50), -- FK to ncr_headers
    linked_capa_id VARCHAR(50), -- FK to capa_headers
    
    -- Resolution
    resolution TEXT,
    resolution_date DATE,
    
    -- Cost
    replacement_cost DECIMAL(15,2) DEFAULT 0,
    credit_issued DECIMAL(15,2) DEFAULT 0,
    total_cost DECIMAL(15,2) DEFAULT 0,
    
    -- Customer Satisfaction
    customer_satisfied BOOLEAN,
    customer_feedback TEXT,
    
    -- Status
    complaint_status VARCHAR(30) DEFAULT 'open',
    -- open, investigating, capa_created, resolved, closed
    
    -- Closure
    closed_date DATE,
    closed_by VARCHAR(50),
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- 8D PROBLEM SOLVING
-- ============================================================================

CREATE TABLE eight_d_reports (
    eight_d_id VARCHAR(50) PRIMARY KEY,
    eight_d_number VARCHAR(50) UNIQUE NOT NULL,
    
    -- Source
    source_type VARCHAR(30),
    -- customer_complaint, internal_ncr, supplier_issue
    
    source_document_id VARCHAR(50), -- Complaint ID, NCR ID, etc.
    
    -- Team
    team_leader VARCHAR(50) NOT NULL, -- FK to employees
    team_members TEXT[], -- Array of employee IDs
    
    -- D0: Prepare
    problem_preparation TEXT,
    
    -- D1: Team
    team_established_date DATE,
    
    -- D2: Problem Description
    problem_description TEXT NOT NULL,
    is_statement TEXT, -- What IS the problem
    is_not_statement TEXT, -- What is NOT the problem
    
    -- D3: Containment
    containment_action TEXT,
    containment_date DATE,
    containment_verified BOOLEAN DEFAULT false,
    
    -- D4: Root Cause
    root_cause_analysis TEXT,
    root_cause_method VARCHAR(30), -- 5_why, fishbone, fault_tree
    root_cause_identified DATE,
    root_cause_verified BOOLEAN DEFAULT false,
    
    -- D5: Permanent Corrective Actions
    permanent_actions TEXT,
    pca_implementation_date DATE,
    
    -- D6: Verification
    verification_plan TEXT,
    verification_completed BOOLEAN DEFAULT false,
    verification_date DATE,
    
    -- D7: Prevention
    preventive_actions TEXT,
    systems_updated TEXT,
    prevention_completed BOOLEAN DEFAULT false,
    
    -- D8: Team Recognition
    team_recognition TEXT,
    lessons_learned TEXT,
    
    -- Status
    eight_d_status VARCHAR(30) DEFAULT 'in_progress',
    -- in_progress, completed, closed
    
    -- Closure
    closed_date DATE,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- PPAP (PRODUCTION PART APPROVAL PROCESS)
-- ============================================================================

CREATE TABLE ppap_submissions (
    ppap_id VARCHAR(50) PRIMARY KEY,
    ppap_number VARCHAR(50) UNIQUE NOT NULL,
    
    -- Part Details
    product_id VARCHAR(50), -- FK to products
    material_id VARCHAR(50), -- FK to materials
    part_number VARCHAR(100) NOT NULL,
    part_name VARCHAR(200) NOT NULL,
    
    -- Supplier (if applicable)
    supplier_id VARCHAR(50), -- FK to suppliers
    
    -- Customer
    customer_id VARCHAR(50), -- FK to customers
    
    -- Submission Details
    ppap_level INTEGER NOT NULL, -- 1, 2, 3, 4, or 5
    submission_date DATE NOT NULL,
    submission_reason VARCHAR(50),
    -- new_part, engineering_change, process_change, supplier_change
    
    -- Required Documents (Checklist)
    design_records BOOLEAN DEFAULT false,
    engineering_change_docs BOOLEAN DEFAULT false,
    customer_approval BOOLEAN DEFAULT false,
    dfmea_completed BOOLEAN DEFAULT false,
    pfmea_completed BOOLEAN DEFAULT false,
    control_plan BOOLEAN DEFAULT false,
    msa_study BOOLEAN DEFAULT false,
    dimensional_results BOOLEAN DEFAULT false,
    material_test_results BOOLEAN DEFAULT false,
    initial_process_study BOOLEAN DEFAULT false,
    qualified_lab_docs BOOLEAN DEFAULT false,
    appearance_approval BOOLEAN DEFAULT false,
    sample_products BOOLEAN DEFAULT false,
    master_sample BOOLEAN DEFAULT false,
    checking_aids BOOLEAN DEFAULT false,
    
    -- PSW (Part Submission Warrant)
    psw_signed BOOLEAN DEFAULT false,
    psw_signed_by VARCHAR(50),
    psw_signed_date DATE,
    
    -- Status
    ppap_status VARCHAR(30) DEFAULT 'in_preparation',
    -- in_preparation, submitted, under_review, approved, 
    -- rejected, interim_approval
    
    -- Review
    reviewed_by VARCHAR(50), -- FK to employees
    review_date DATE,
    review_comments TEXT,
    
    -- Approval
    approval_date DATE,
    approved_by VARCHAR(50),
    approval_expiry_date DATE,
    
    -- Documents
    submission_package_url TEXT,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- SUPPLIER QUALITY PERFORMANCE
-- ============================================================================

CREATE TABLE supplier_quality_metrics (
    metric_id VARCHAR(50) PRIMARY KEY,
    
    -- Supplier & Period
    supplier_id VARCHAR(50) NOT NULL, -- FK to suppliers
    metric_period VARCHAR(7) NOT NULL, -- YYYY-MM format
    
    -- Receipt Quality
    total_receipts INTEGER DEFAULT 0,
    receipts_inspected INTEGER DEFAULT 0,
    receipts_accepted INTEGER DEFAULT 0,
    receipts_rejected INTEGER DEFAULT 0,
    
    -- Quantity Quality
    total_quantity_received DECIMAL(15,4) DEFAULT 0,
    quantity_accepted DECIMAL(15,4) DEFAULT 0,
    quantity_rejected DECIMAL(15,4) DEFAULT 0,
    
    -- Defect Metrics
    total_defects INTEGER DEFAULT 0,
    defect_ppm INTEGER DEFAULT 0, -- Parts Per Million
    
    -- Defect Categories
    critical_defects INTEGER DEFAULT 0,
    major_defects INTEGER DEFAULT 0,
    minor_defects INTEGER DEFAULT 0,
    
    -- Quality Score
    acceptance_rate_pct DECIMAL(5,2),
    quality_score DECIMAL(5,2), -- 0-100
    
    -- NCRs & CAPAs
    ncr_count INTEGER DEFAULT 0,
    capa_count INTEGER DEFAULT 0,
    capa_effectiveness_pct DECIMAL(5,2),
    
    -- Cost of Poor Quality
    rejection_cost DECIMAL(15,2) DEFAULT 0,
    rework_cost DECIMAL(15,2) DEFAULT 0,
    sorting_cost DECIMAL(15,2) DEFAULT 0,
    total_copq DECIMAL(15,2) DEFAULT 0,
    
    UNIQUE(supplier_id, metric_period),
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- QUALITY METRICS & DASHBOARDS
-- ============================================================================

CREATE TABLE quality_kpis (
    kpi_id VARCHAR(50) PRIMARY KEY,
    kpi_date DATE NOT NULL,
    
    -- Internal Quality
    internal_defect_ppm INTEGER DEFAULT 0,
    first_time_quality_pct DECIMAL(5,2),
    
    -- Customer Quality
    customer_complaints INTEGER DEFAULT 0,
    customer_returns_ppm INTEGER DEFAULT 0,
    
    -- Supplier Quality
    incoming_rejection_pct DECIMAL(5,2),
    supplier_defect_ppm INTEGER DEFAULT 0,
    
    -- Process Control
    processes_in_control INTEGER DEFAULT 0,
    processes_total INTEGER DEFAULT 0,
    process_capability_avg DECIMAL(5,3),
    
    -- NCR & CAPA
    ncr_opened INTEGER DEFAULT 0,
    ncr_closed INTEGER DEFAULT 0,
    ncr_open_count INTEGER DEFAULT 0,
    capa_overdue INTEGER DEFAULT 0,
    
    -- Cost of Quality
    prevention_cost DECIMAL(15,2) DEFAULT 0,
    appraisal_cost DECIMAL(15,2) DEFAULT 0,
    internal_failure_cost DECIMAL(15,2) DEFAULT 0,
    external_failure_cost DECIMAL(15,2) DEFAULT 0,
    total_coq DECIMAL(15,2) DEFAULT 0,
    
    -- Calibration
    equipment_calibrated_pct DECIMAL(5,2),
    equipment_overdue INTEGER DEFAULT 0,
    
    UNIQUE(kpi_date),
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- INTEGRATION LOGS
-- ============================================================================

CREATE TABLE qms_integration_log (
    log_id VARCHAR(50) PRIMARY KEY,
    log_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Integration Type
    integration_type VARCHAR(50) NOT NULL,
    -- mes_inspection_to_ncr, ticket_to_complaint, supplier_quality,
    -- capa_to_production, ncr_to_financial
    
    -- Source & Target
    source_system VARCHAR(30),
    target_system VARCHAR(30),
    
    -- Documents
    source_document_id VARCHAR(50),
    target_document_id VARCHAR(50),
    
    -- Status
    integration_status VARCHAR(30) DEFAULT 'success',
    error_message TEXT,
    
    -- Data
    integration_data JSONB
);

-- ============================================================================
-- INDICES
-- ============================================================================

-- NCR
CREATE INDEX idx_ncr_status ON ncr_headers(ncr_status, detected_date);
CREATE INDEX idx_ncr_supplier ON ncr_headers(supplier_id, detected_date);
CREATE INDEX idx_ncr_customer ON ncr_headers(customer_id, detected_date);
CREATE INDEX idx_ncr_material ON ncr_headers(material_id);

-- CAPA
CREATE INDEX idx_capa_status ON capa_headers(capa_status, target_completion_date);
CREATE INDEX idx_capa_responsible ON capa_headers(responsible_person, capa_status);
CREATE INDEX idx_capa_source ON capa_headers(initiated_from, source_document_id);

-- Audits
CREATE INDEX idx_audits_type ON quality_audits(audit_type, planned_date);
CREATE INDEX idx_audits_status ON quality_audits(audit_status);
CREATE INDEX idx_audit_findings_status ON audit_findings(finding_status);

-- Control Plans
CREATE INDEX idx_control_plans_product ON control_plans(product_id, plan_status);
CREATE INDEX idx_control_chars_plan ON control_plan_characteristics(control_plan_id);

-- SPC
CREATE INDEX idx_spc_charts_status ON spc_control_charts(chart_status);
CREATE INDEX idx_spc_data_chart ON spc_data_points(chart_id, measurement_timestamp);

-- Calibration
CREATE INDEX idx_measuring_equipment_status ON measuring_equipment(equipment_status, next_calibration_due);
CREATE INDEX idx_calibration_records_equipment ON calibration_records(equipment_id, calibration_date);

-- Documents
CREATE INDEX idx_quality_docs_status ON quality_documents(document_status);
CREATE INDEX idx_quality_docs_review ON quality_documents(next_review_date);

-- Complaints
CREATE INDEX idx_complaints_customer ON customer_complaints(customer_id, complaint_date);
CREATE INDEX idx_complaints_status ON customer_complaints(complaint_status);

-- PPAP
CREATE INDEX idx_ppap_supplier ON ppap_submissions(supplier_id, ppap_status);
CREATE INDEX idx_ppap_customer ON ppap_submissions(customer_id, ppap_status);

-- ============================================================================
-- COMMENTS
-- ============================================================================

COMMENT ON TABLE ncr_headers IS 'Non-Conformance Reports with root cause analysis';
COMMENT ON TABLE capa_headers IS 'Corrective and Preventive Actions';
COMMENT ON TABLE quality_audits IS 'Internal, supplier, customer, and certification audits';
COMMENT ON TABLE control_plans IS 'Process control plans with characteristics';
COMMENT ON TABLE spc_control_charts IS 'Statistical Process Control charts';
COMMENT ON TABLE measuring_equipment IS 'Measuring equipment with calibration tracking';
COMMENT ON TABLE quality_documents IS 'Document control with version management';
COMMENT ON TABLE customer_complaints IS 'Customer complaints integrated with service tickets';
COMMENT ON TABLE eight_d_reports IS '8D problem solving methodology';
COMMENT ON TABLE ppap_submissions IS 'Production Part Approval Process submissions';
COMMENT ON TABLE supplier_quality_metrics IS 'Supplier quality performance tracking';
COMMENT ON TABLE quality_kpis IS 'Daily quality KPIs and cost of quality';
