-- GenIMS CMMS (Computerized Maintenance Management System) Schema
-- Complete maintenance management from planning to execution

-- ============================================================================
-- ASSET MANAGEMENT
-- ============================================================================

CREATE TABLE maintenance_assets (
    asset_id VARCHAR(50) PRIMARY KEY,
    asset_number VARCHAR(50) UNIQUE NOT NULL,
    asset_name VARCHAR(200) NOT NULL,
    
    -- Asset Classification
    asset_type VARCHAR(50), -- machine, equipment, vehicle, facility, tool, instrument
    asset_category VARCHAR(50), -- production, utility, hvac, electrical, instrumentation
    asset_class VARCHAR(50), -- critical, essential, important, support
    
    -- Hierarchy
    parent_asset_id VARCHAR(50), -- FK to maintenance_assets (for asset hierarchy)
    location_hierarchy VARCHAR(500), -- Full path: Factory > Line > Machine
    
    -- Master Data Links
    machine_id VARCHAR(50), -- FK to machines (if production equipment)
    factory_id VARCHAR(50), -- FK to factories
    line_id VARCHAR(50), -- FK to production_lines
    
    -- Location
    department VARCHAR(100),
    location_description TEXT,
    
    -- Technical Details
    manufacturer VARCHAR(200),
    model_number VARCHAR(100),
    serial_number VARCHAR(100),
    year_manufactured INTEGER,
    
    -- Installation
    installation_date DATE,
    commissioning_date DATE,
    warranty_expiry_date DATE,
    
    -- Specifications
    rated_capacity VARCHAR(100),
    power_rating VARCHAR(100),
    operating_voltage VARCHAR(50),
    operating_pressure VARCHAR(50),
    weight_kg DECIMAL(10,2),
    dimensions VARCHAR(200),
    
    -- Criticality Analysis
    criticality_rating VARCHAR(20), -- critical, high, medium, low
    safety_critical BOOLEAN DEFAULT false,
    production_critical BOOLEAN DEFAULT false,
    environmental_critical BOOLEAN DEFAULT false,
    
    -- Failure Impact
    downtime_cost_per_hour DECIMAL(12,2),
    replacement_cost DECIMAL(15,2),
    
    -- Maintenance Strategy
    maintenance_strategy VARCHAR(50), -- preventive, predictive, corrective, run_to_failure
    pm_frequency_type VARCHAR(30), -- calendar, meter_based, condition_based
    
    -- Meter Information
    has_meter BOOLEAN DEFAULT false,
    meter_unit VARCHAR(20), -- hours, km, cycles, units_produced
    current_meter_reading DECIMAL(15,2),
    meter_reading_date TIMESTAMP,
    
    -- Condition
    asset_condition VARCHAR(30) DEFAULT 'good', -- excellent, good, fair, poor, critical
    
    -- Status
    asset_status VARCHAR(30) DEFAULT 'operational',
    -- operational, under_maintenance, breakdown, standby, retired, disposed
    
    -- Ownership
    owned_leased VARCHAR(20) DEFAULT 'owned', -- owned, leased, rented
    purchase_cost DECIMAL(15,2),
    purchase_date DATE,
    
    -- Documentation
    technical_manual_url VARCHAR(500),
    drawings_url VARCHAR(500),
    photo_url VARCHAR(500),
    
    -- Lifecycle
    expected_life_years INTEGER,
    remaining_life_years INTEGER,
    
    is_active BOOLEAN DEFAULT true,
    
    -- Audit
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    notes TEXT
);

-- ============================================================================
-- WORK ORDERS
-- ============================================================================

CREATE TABLE work_orders (
    work_order_id VARCHAR(50) PRIMARY KEY,
    work_order_number VARCHAR(50) UNIQUE NOT NULL,
    
    -- Asset
    asset_id VARCHAR(50) NOT NULL, -- FK to maintenance_assets
    
    -- Work Order Type
    wo_type VARCHAR(30) NOT NULL,
    -- preventive, corrective, breakdown, predictive, inspection, 
    -- calibration, modification, shutdown, project
    
    -- Priority
    priority VARCHAR(20) DEFAULT 'medium',
    -- emergency, urgent, high, medium, low
    
    -- Planning
    description TEXT NOT NULL,
    problem_description TEXT,
    
    -- Failure Information
    failure_code VARCHAR(50), -- FK to failure_codes
    failure_class VARCHAR(50), -- mechanical, electrical, hydraulic, pneumatic, software
    failure_mode VARCHAR(100), -- breakdown, degradation, malfunction
    downtime_category VARCHAR(50), -- planned, unplanned
    
    -- Scheduling
    requested_date DATE,
    scheduled_start_date DATE,
    scheduled_end_date DATE,
    estimated_duration_hours DECIMAL(8,2),
    
    -- Actual Execution
    actual_start_date TIMESTAMP,
    actual_end_date TIMESTAMP,
    actual_duration_hours DECIMAL(8,2),
    
    -- Status
    wo_status VARCHAR(30) DEFAULT 'created',
    -- created, planned, scheduled, assigned, in_progress, on_hold, 
    -- completed, verified, closed, cancelled
    
    status_history JSONB, -- Track status changes with timestamps
    
    -- Assignment
    assigned_to VARCHAR(50), -- FK to maintenance_technicians
    assigned_team VARCHAR(50), -- FK to maintenance_teams
    
    -- Source
    source_type VARCHAR(50), -- pm_schedule, breakdown, inspection, request, predictive
    source_document_id VARCHAR(50),
    
    -- Integration Links
    downtime_event_id VARCHAR(50), -- FK to downtime_events (MES)
    machine_fault_id VARCHAR(50), -- FK to machine_faults (operational)
    
    -- Safety
    safety_permit_required BOOLEAN DEFAULT false,
    lockout_tagout_required BOOLEAN DEFAULT false,
    confined_space BOOLEAN DEFAULT false,
    hot_work_permit BOOLEAN DEFAULT false,
    
    -- Work Authorization
    approved_by VARCHAR(50),
    approved_at TIMESTAMP,
    
    -- Completion
    work_performed TEXT,
    root_cause TEXT,
    corrective_action TEXT,
    
    completed_by VARCHAR(50),
    completed_at TIMESTAMP,
    
    -- Verification
    verified_by VARCHAR(50),
    verified_at TIMESTAMP,
    verification_notes TEXT,
    
    -- Follow-up
    follow_up_required BOOLEAN DEFAULT false,
    follow_up_wo_id VARCHAR(50), -- FK to work_orders
    
    -- Costs (to be calculated from parts + labor)
    estimated_cost DECIMAL(12,2),
    actual_labor_cost DECIMAL(12,2),
    actual_parts_cost DECIMAL(12,2),
    actual_total_cost DECIMAL(12,2),
    
    -- Reporting
    downtime_minutes INTEGER DEFAULT 0,
    production_loss_units DECIMAL(15,4),
    
    created_by VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE work_order_tasks (
    task_id VARCHAR(50) PRIMARY KEY,
    work_order_id VARCHAR(50) NOT NULL, -- FK to work_orders
    task_sequence INTEGER,
    
    -- Task Details
    task_description TEXT NOT NULL,
    task_type VARCHAR(50), -- inspection, replacement, adjustment, cleaning, lubrication
    
    -- Instructions
    procedure_id VARCHAR(50), -- FK to work_procedures
    special_instructions TEXT,
    
    -- Tools & Equipment Required
    tools_required TEXT, -- JSON array
    special_equipment_required TEXT,
    
    -- Safety
    safety_precautions TEXT,
    ppe_required TEXT, -- JSON array: helmet, gloves, goggles, etc.
    
    -- Execution
    task_status VARCHAR(30) DEFAULT 'pending',
    -- pending, in_progress, completed, skipped, failed
    
    assigned_to VARCHAR(50), -- FK to maintenance_technicians
    
    estimated_duration_minutes INTEGER,
    actual_duration_minutes INTEGER,
    
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    completed_by VARCHAR(50),
    
    -- Verification
    requires_verification BOOLEAN DEFAULT false,
    verified BOOLEAN DEFAULT false,
    verified_by VARCHAR(50),
    verified_at TIMESTAMP,
    
    -- Results
    task_result VARCHAR(30), -- pass, fail, conditional
    measurements TEXT, -- JSON: measurements taken
    observations TEXT,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- PREVENTIVE MAINTENANCE SCHEDULES
-- ============================================================================

CREATE TABLE pm_schedules (
    pm_schedule_id VARCHAR(50) PRIMARY KEY,
    schedule_code VARCHAR(50) UNIQUE NOT NULL,
    schedule_name VARCHAR(200) NOT NULL,
    
    -- Asset
    asset_id VARCHAR(50) NOT NULL, -- FK to maintenance_assets
    
    -- Schedule Type
    schedule_type VARCHAR(30), -- calendar, meter_based, condition_based
    
    -- Calendar-based Settings
    frequency_type VARCHAR(30), -- daily, weekly, monthly, quarterly, yearly
    frequency_value INTEGER, -- e.g., every 3 months
    frequency_unit VARCHAR(20), -- days, weeks, months, years
    
    -- Meter-based Settings
    meter_frequency INTEGER, -- e.g., every 500 hours
    meter_unit VARCHAR(20), -- hours, km, cycles
    meter_tolerance INTEGER, -- +/- tolerance
    
    -- Condition-based Settings
    condition_parameter VARCHAR(100), -- vibration, temperature, oil_quality
    condition_threshold VARCHAR(100),
    
    -- Schedule Details
    pm_type VARCHAR(30), -- inspection, service, overhaul, calibration
    description TEXT,
    estimated_duration_hours DECIMAL(8,2),
    
    -- Work Instructions
    procedure_id VARCHAR(50), -- FK to work_procedures
    standard_tasks TEXT, -- JSON array of standard tasks
    
    -- Resources
    required_skills TEXT, -- JSON array
    required_tools TEXT, -- JSON array
    required_parts TEXT, -- JSON array with quantities
    
    -- Scheduling
    lead_time_days INTEGER, -- How many days before to generate WO
    scheduling_priority VARCHAR(20),
    
    -- Last Execution
    last_wo_id VARCHAR(50), -- FK to work_orders
    last_completed_date DATE,
    last_meter_reading DECIMAL(15,2),
    
    -- Next Due
    next_due_date DATE,
    next_due_meter_reading DECIMAL(15,2),
    
    -- Auto-generation
    auto_generate_wo BOOLEAN DEFAULT true,
    
    -- Status
    schedule_status VARCHAR(30) DEFAULT 'active',
    -- active, inactive, suspended, superseded
    
    effective_date DATE,
    end_date DATE,
    
    is_active BOOLEAN DEFAULT true,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE pm_generation_log (
    log_id VARCHAR(50) PRIMARY KEY,
    pm_schedule_id VARCHAR(50) NOT NULL, -- FK to pm_schedules
    
    -- Generation Details
    generation_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    generation_reason VARCHAR(50), -- calendar_due, meter_due, condition_met, manual
    
    -- Trigger Values
    trigger_date DATE,
    trigger_meter_reading DECIMAL(15,2),
    
    -- Generated Work Order
    work_order_id VARCHAR(50), -- FK to work_orders
    work_order_number VARCHAR(50),
    
    -- Status
    generation_status VARCHAR(30), -- success, failed, skipped
    error_message TEXT,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- WORK PROCEDURES & CHECKLISTS
-- ============================================================================

CREATE TABLE work_procedures (
    procedure_id VARCHAR(50) PRIMARY KEY,
    procedure_code VARCHAR(50) UNIQUE NOT NULL,
    procedure_name VARCHAR(200) NOT NULL,
    
    -- Classification
    procedure_type VARCHAR(50), -- pm, inspection, troubleshooting, calibration, startup, shutdown
    
    -- Applicability
    asset_type VARCHAR(50),
    asset_category VARCHAR(50),
    manufacturer VARCHAR(200),
    model_number VARCHAR(100),
    
    -- Content
    description TEXT,
    objective TEXT,
    
    -- Safety
    safety_precautions TEXT,
    ppe_required TEXT, -- JSON array
    permits_required TEXT, -- JSON array
    
    -- Tools & Materials
    tools_required TEXT, -- JSON array
    parts_required TEXT, -- JSON array
    consumables_required TEXT, -- JSON array
    
    -- Procedure Steps
    procedure_steps TEXT, -- JSON array of steps with details
    
    -- Estimated Time
    estimated_duration_hours DECIMAL(8,2),
    
    -- Skills Required
    required_skill_level VARCHAR(50), -- basic, intermediate, advanced, expert
    required_certifications TEXT, -- JSON array
    
    -- Documentation
    document_url VARCHAR(500),
    video_url VARCHAR(500),
    diagram_url VARCHAR(500),
    
    -- Version Control
    version VARCHAR(20),
    revision_date DATE,
    approved_by VARCHAR(50),
    
    is_active BOOLEAN DEFAULT true,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- MRO SPARE PARTS INVENTORY
-- ============================================================================

CREATE TABLE mro_parts (
    mro_part_id VARCHAR(50) PRIMARY KEY,
    part_number VARCHAR(100) UNIQUE NOT NULL,
    part_name VARCHAR(200) NOT NULL,
    
    -- Classification
    part_category VARCHAR(50), -- spare_part, consumable, tool, safety_item
    part_type VARCHAR(50), -- mechanical, electrical, hydraulic, pneumatic, electronic
    
    -- Specifications
    description TEXT,
    manufacturer VARCHAR(200),
    manufacturer_part_number VARCHAR(100),
    
    -- Inventory
    unit_of_measure VARCHAR(20),
    current_stock DECIMAL(15,4) DEFAULT 0,
    min_stock_level DECIMAL(15,4),
    max_stock_level DECIMAL(15,4),
    reorder_point DECIMAL(15,4),
    reorder_quantity DECIMAL(15,4),
    
    -- Location
    warehouse_id VARCHAR(50), -- FK to warehouses (WMS)
    bin_location VARCHAR(100),
    
    -- Criticality
    criticality VARCHAR(20), -- critical, high, medium, low
    lead_time_days INTEGER,
    
    -- Costing
    standard_cost DECIMAL(12,4),
    last_purchase_cost DECIMAL(12,4),
    last_purchase_date DATE,
    average_cost DECIMAL(12,4),
    total_stock_value DECIMAL(15,2),
    
    -- Supplier
    primary_supplier_id VARCHAR(50), -- FK to suppliers (ERP)
    alternate_suppliers TEXT, -- JSON array of supplier IDs
    
    -- Usage
    annual_usage_quantity DECIMAL(15,4),
    last_issue_date DATE,
    last_receipt_date DATE,
    
    -- Asset Association
    used_on_assets TEXT, -- JSON array of asset_ids
    interchangeable_parts TEXT, -- JSON array of part_numbers
    
    -- Shelf Life
    has_shelf_life BOOLEAN DEFAULT false,
    shelf_life_months INTEGER,
    
    -- Status
    part_status VARCHAR(30) DEFAULT 'active', -- active, obsolete, phased_out, restricted
    
    is_active BOOLEAN DEFAULT true,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE mro_parts_transactions (
    transaction_id VARCHAR(50) PRIMARY KEY,
    transaction_number VARCHAR(50) UNIQUE NOT NULL,
    
    -- Part
    mro_part_id VARCHAR(50) NOT NULL, -- FK to mro_parts
    
    -- Transaction Type
    transaction_type VARCHAR(30),
    -- issue, return, receipt, adjustment, transfer, scrap
    
    transaction_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Quantity
    quantity DECIMAL(15,4),
    unit_of_measure VARCHAR(20),
    
    -- Cost
    unit_cost DECIMAL(12,4),
    total_cost DECIMAL(15,2),
    
    -- Work Order Link
    work_order_id VARCHAR(50), -- FK to work_orders
    asset_id VARCHAR(50), -- FK to maintenance_assets
    
    -- Location
    from_location VARCHAR(100),
    to_location VARCHAR(100),
    
    -- User
    issued_to VARCHAR(50), -- FK to maintenance_technicians
    issued_by VARCHAR(50),
    
    -- Purchase Order (for receipts)
    purchase_order_id VARCHAR(50), -- FK to purchase_orders (ERP)
    
    -- Reason
    reason_code VARCHAR(50),
    notes TEXT,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- MAINTENANCE LABOR
-- ============================================================================

CREATE TABLE maintenance_technicians (
    technician_id VARCHAR(50) PRIMARY KEY,
    employee_id VARCHAR(50), -- FK to employees
    technician_code VARCHAR(50) UNIQUE NOT NULL,
    
    -- Personal
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    email VARCHAR(100),
    phone VARCHAR(50),
    
    -- Employment
    hire_date DATE,
    department VARCHAR(100),
    job_title VARCHAR(100),
    
    -- Skills & Certifications
    skill_level VARCHAR(30), -- apprentice, technician, senior_technician, specialist, expert
    trade VARCHAR(50), -- mechanical, electrical, instrumentation, multi_craft
    
    certifications TEXT, -- JSON array: forklift, welding, electrical_license, etc.
    certifications_expiry JSONB, -- JSON object with cert: expiry_date
    
    specializations TEXT, -- JSON array: HVAC, robotics, PLCs, hydraulics, etc.
    
    -- Shift & Availability
    primary_shift VARCHAR(20), -- day, evening, night, rotating
    available_for_callout BOOLEAN DEFAULT true,
    
    -- Performance
    hourly_rate DECIMAL(10,2),
    overtime_rate DECIMAL(10,2),
    
    -- Metrics
    total_wos_completed INTEGER DEFAULT 0,
    avg_completion_time_hours DECIMAL(8,2),
    quality_rating DECIMAL(3,2), -- 1.0 to 5.0
    
    -- Current Status
    technician_status VARCHAR(30) DEFAULT 'available',
    -- available, assigned, on_break, off_shift, on_leave, training
    
    current_wo_id VARCHAR(50), -- FK to work_orders
    
    is_active BOOLEAN DEFAULT true,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE maintenance_teams (
    team_id VARCHAR(50) PRIMARY KEY,
    team_code VARCHAR(50) UNIQUE NOT NULL,
    team_name VARCHAR(200) NOT NULL,
    
    -- Team Details
    team_type VARCHAR(50), -- mechanical, electrical, multi_craft, shutdown, project
    supervisor_id VARCHAR(50), -- FK to maintenance_technicians
    
    -- Members
    team_members TEXT, -- JSON array of technician_ids
    team_size INTEGER,
    
    -- Shift
    shift VARCHAR(20), -- day, evening, night
    
    -- Specialization
    specialization VARCHAR(100),
    
    is_active BOOLEAN DEFAULT true,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE labor_time_entries (
    entry_id VARCHAR(50) PRIMARY KEY,
    
    -- Work Order
    work_order_id VARCHAR(50) NOT NULL, -- FK to work_orders
    
    -- Technician
    technician_id VARCHAR(50) NOT NULL, -- FK to maintenance_technicians
    
    -- Time
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP,
    duration_hours DECIMAL(8,2),
    
    -- Labor Type
    labor_type VARCHAR(30), -- regular, overtime, emergency, travel
    
    -- Cost
    hourly_rate DECIMAL(10,2),
    labor_cost DECIMAL(12,2),
    
    -- Activity
    activity_description TEXT,
    
    -- Approval
    approved BOOLEAN DEFAULT false,
    approved_by VARCHAR(50),
    approved_at TIMESTAMP,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- EQUIPMENT METERS & READINGS
-- ============================================================================

CREATE TABLE equipment_meter_readings (
    reading_id VARCHAR(50) PRIMARY KEY,
    
    -- Asset
    asset_id VARCHAR(50) NOT NULL, -- FK to maintenance_assets
    
    -- Reading
    reading_date TIMESTAMP NOT NULL,
    meter_value DECIMAL(15,2) NOT NULL,
    meter_unit VARCHAR(20), -- hours, km, cycles, units_produced
    
    -- Delta from last reading
    previous_reading DECIMAL(15,2),
    delta_value DECIMAL(15,2),
    days_since_last_reading INTEGER,
    
    -- Reading Source
    reading_source VARCHAR(30), -- manual, automated, calculated, estimated
    
    -- User
    recorded_by VARCHAR(50),
    
    -- Work Order Link
    work_order_id VARCHAR(50), -- FK to work_orders (if during WO)
    
    notes TEXT,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- FAILURE CODES & ROOT CAUSE ANALYSIS
-- ============================================================================

CREATE TABLE failure_codes (
    failure_code_id VARCHAR(50) PRIMARY KEY,
    failure_code VARCHAR(50) UNIQUE NOT NULL,
    failure_description VARCHAR(200) NOT NULL,
    
    -- Classification
    failure_class VARCHAR(50), -- mechanical, electrical, hydraulic, pneumatic, software, operator_error
    failure_type VARCHAR(50), -- wear, fatigue, corrosion, overload, misalignment, contamination
    
    -- Severity
    severity VARCHAR(20), -- critical, major, moderate, minor
    
    -- Hierarchy
    parent_code VARCHAR(50), -- FK to failure_codes
    
    -- Recommended Actions
    recommended_action TEXT,
    typical_repair_time_hours DECIMAL(8,2),
    
    is_active BOOLEAN DEFAULT true,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- MAINTENANCE COSTS & BUDGETS
-- ============================================================================

CREATE TABLE maintenance_cost_centers (
    cost_center_id VARCHAR(50) PRIMARY KEY,
    cost_center_code VARCHAR(50) UNIQUE NOT NULL,
    cost_center_name VARCHAR(200) NOT NULL,
    
    -- Hierarchy
    parent_cost_center_id VARCHAR(50), -- FK to maintenance_cost_centers
    
    -- Budget
    annual_budget DECIMAL(15,2),
    current_period_budget DECIMAL(15,2),
    
    -- Actuals
    ytd_actual_cost DECIMAL(15,2) DEFAULT 0,
    current_period_actual DECIMAL(15,2) DEFAULT 0,
    
    -- Manager
    manager_id VARCHAR(50),
    
    is_active BOOLEAN DEFAULT true,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE maintenance_costs (
    cost_id VARCHAR(50) PRIMARY KEY,
    
    -- Work Order
    work_order_id VARCHAR(50) NOT NULL, -- FK to work_orders
    asset_id VARCHAR(50) NOT NULL, -- FK to maintenance_assets
    
    -- Cost Type
    cost_type VARCHAR(30), -- labor, parts, contractor, equipment_rental, other
    
    -- Cost Details
    cost_description TEXT,
    cost_amount DECIMAL(12,2),
    currency VARCHAR(3) DEFAULT 'INR',
    
    -- Date
    cost_date DATE,
    
    -- Cost Center
    cost_center_id VARCHAR(50), -- FK to maintenance_cost_centers
    
    -- GL Account
    gl_account VARCHAR(50), -- FK to general_ledger (ERP)
    
    -- Vendor (for external costs)
    vendor_id VARCHAR(50), -- FK to suppliers (ERP)
    
    -- Invoice
    invoice_number VARCHAR(100),
    invoice_date DATE,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- MAINTENANCE HISTORY
-- ============================================================================

CREATE TABLE maintenance_history (
    history_id VARCHAR(50) PRIMARY KEY,
    
    -- Asset
    asset_id VARCHAR(50) NOT NULL, -- FK to maintenance_assets
    
    -- Event Type
    event_type VARCHAR(50),
    -- work_order_completed, breakdown, inspection, meter_reading, 
    -- condition_change, status_change, modification, installation
    
    -- Event Details
    event_date TIMESTAMP NOT NULL,
    event_description TEXT,
    
    -- Related Records
    work_order_id VARCHAR(50), -- FK to work_orders
    pm_schedule_id VARCHAR(50), -- FK to pm_schedules
    
    -- Technical Details
    failure_code VARCHAR(50), -- FK to failure_codes
    root_cause TEXT,
    corrective_action TEXT,
    
    -- Impact
    downtime_hours DECIMAL(8,2),
    production_loss DECIMAL(15,4),
    
    -- Costs
    labor_cost DECIMAL(12,2),
    parts_cost DECIMAL(12,2),
    total_cost DECIMAL(12,2),
    
    -- User
    performed_by VARCHAR(50),
    
    -- Documentation
    attachment_url VARCHAR(500),
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- SERVICE CONTRACTS & VENDORS
-- ============================================================================

CREATE TABLE service_contracts (
    contract_id VARCHAR(50) PRIMARY KEY,
    contract_number VARCHAR(50) UNIQUE NOT NULL,
    contract_name VARCHAR(200) NOT NULL,
    
    -- Vendor
    vendor_id VARCHAR(50) NOT NULL, -- FK to suppliers (ERP)
    vendor_name VARCHAR(200),
    
    -- Contract Type
    contract_type VARCHAR(50), -- full_service, amc, calibration, consulting, warranty_extension
    
    -- Coverage
    coverage_description TEXT,
    covered_assets TEXT, -- JSON array of asset_ids
    
    -- Terms
    contract_start_date DATE NOT NULL,
    contract_end_date DATE NOT NULL,
    contract_value DECIMAL(15,2),
    payment_terms VARCHAR(100),
    
    -- Service Level Agreement
    response_time_hours INTEGER,
    resolution_time_hours INTEGER,
    uptime_guarantee_pct DECIMAL(5,2),
    penalty_clause TEXT,
    
    -- Billing
    billing_frequency VARCHAR(30), -- monthly, quarterly, annually
    next_billing_date DATE,
    
    -- Renewal
    auto_renewal BOOLEAN DEFAULT false,
    renewal_notice_days INTEGER,
    
    -- Status
    contract_status VARCHAR(30) DEFAULT 'active',
    -- active, expired, terminated, suspended
    
    -- Performance
    total_service_calls INTEGER DEFAULT 0,
    avg_response_time_hours DECIMAL(8,2),
    customer_satisfaction_rating DECIMAL(3,2),
    
    -- Documents
    contract_document_url VARCHAR(500),
    
    is_active BOOLEAN DEFAULT true,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE service_call_logs (
    call_log_id VARCHAR(50) PRIMARY KEY,
    call_number VARCHAR(50) UNIQUE NOT NULL,
    
    -- Contract
    contract_id VARCHAR(50) NOT NULL, -- FK to service_contracts
    
    -- Asset
    asset_id VARCHAR(50) NOT NULL, -- FK to maintenance_assets
    
    -- Call Details
    call_date TIMESTAMP NOT NULL,
    problem_description TEXT NOT NULL,
    
    -- Priority
    priority VARCHAR(20), -- emergency, urgent, normal
    
    -- Response
    response_time_hours DECIMAL(8,2),
    resolution_time_hours DECIMAL(8,2),
    
    -- Service Details
    service_performed TEXT,
    parts_used TEXT, -- JSON array
    
    -- Engineer
    service_engineer_name VARCHAR(200),
    service_engineer_contact VARCHAR(100),
    
    -- Status
    call_status VARCHAR(30), -- logged, assigned, in_progress, completed, closed
    
    -- Satisfaction
    customer_rating INTEGER, -- 1-5
    customer_feedback TEXT,
    
    -- Work Order Link
    work_order_id VARCHAR(50), -- FK to work_orders
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- RELIABILITY & PERFORMANCE METRICS
-- ============================================================================

CREATE TABLE asset_reliability_metrics (
    metric_id VARCHAR(50) PRIMARY KEY,
    
    -- Asset
    asset_id VARCHAR(50) NOT NULL, -- FK to maintenance_assets
    
    -- Period
    period_start_date DATE NOT NULL,
    period_end_date DATE NOT NULL,
    period_type VARCHAR(20), -- daily, weekly, monthly, quarterly, yearly
    
    -- Availability Metrics
    total_hours DECIMAL(10,2),
    operating_hours DECIMAL(10,2),
    downtime_hours DECIMAL(10,2),
    planned_downtime_hours DECIMAL(10,2),
    unplanned_downtime_hours DECIMAL(10,2),
    availability_pct DECIMAL(5,2), -- Operating hours / Total hours
    
    -- Reliability Metrics
    number_of_failures INTEGER DEFAULT 0,
    mtbf_hours DECIMAL(10,2), -- Mean Time Between Failures
    mttr_hours DECIMAL(10,2), -- Mean Time To Repair
    
    -- Performance
    oee_pct DECIMAL(5,2), -- Overall Equipment Effectiveness
    
    -- Maintenance Activity
    pm_work_orders INTEGER DEFAULT 0,
    cm_work_orders INTEGER DEFAULT 0, -- Corrective Maintenance
    breakdown_work_orders INTEGER DEFAULT 0,
    
    -- Costs
    total_maintenance_cost DECIMAL(15,2),
    labor_cost DECIMAL(15,2),
    parts_cost DECIMAL(15,2),
    contractor_cost DECIMAL(15,2),
    
    -- Cost Ratios
    maintenance_cost_per_operating_hour DECIMAL(12,4),
    
    -- Production Impact
    production_units DECIMAL(15,4),
    production_loss_units DECIMAL(15,4),
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- CMMS INTEGRATION LOG
-- ============================================================================

CREATE TABLE cmms_integration_log (
    log_id VARCHAR(50) PRIMARY KEY,
    log_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Integration Direction
    integration_direction VARCHAR(20), 
    -- OPERATIONAL_TO_CMMS, MES_TO_CMMS, CMMS_TO_ERP, CMMS_TO_MES
    
    -- Document Type
    document_type VARCHAR(50),
    -- machine_fault, downtime_event, work_order, parts_request, cost_posting
    
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

-- Assets
CREATE INDEX idx_assets_type ON maintenance_assets(asset_type, asset_status);
CREATE INDEX idx_assets_factory ON maintenance_assets(factory_id, is_active);
CREATE INDEX idx_assets_machine ON maintenance_assets(machine_id);
CREATE INDEX idx_assets_criticality ON maintenance_assets(criticality_rating, is_active);
CREATE INDEX idx_assets_parent ON maintenance_assets(parent_asset_id);

-- Work Orders
CREATE INDEX idx_wo_asset ON work_orders(asset_id, wo_status);
CREATE INDEX idx_wo_type ON work_orders(wo_type, wo_status);
CREATE INDEX idx_wo_priority ON work_orders(priority, wo_status);
CREATE INDEX idx_wo_assigned ON work_orders(assigned_to, wo_status);
CREATE INDEX idx_wo_dates ON work_orders(scheduled_start_date, scheduled_end_date);
CREATE INDEX idx_wo_created ON work_orders(created_at);
CREATE INDEX idx_wo_tasks_wo ON work_order_tasks(work_order_id);

-- PM Schedules
CREATE INDEX idx_pm_asset ON pm_schedules(asset_id, schedule_status);
CREATE INDEX idx_pm_next_due ON pm_schedules(next_due_date, schedule_status);
CREATE INDEX idx_pm_type ON pm_schedules(schedule_type, schedule_status);
CREATE INDEX idx_pm_gen_log_schedule ON pm_generation_log(pm_schedule_id, generation_date);

-- MRO Parts
CREATE INDEX idx_mro_category ON mro_parts(part_category, part_status);
CREATE INDEX idx_mro_stock ON mro_parts(current_stock, reorder_point);
CREATE INDEX idx_mro_trans_part ON mro_parts_transactions(mro_part_id, transaction_date);
CREATE INDEX idx_mro_trans_wo ON mro_parts_transactions(work_order_id);

-- Labor
CREATE INDEX idx_tech_status ON maintenance_technicians(technician_status, is_active);
CREATE INDEX idx_tech_shift ON maintenance_technicians(primary_shift, is_active);
CREATE INDEX idx_labor_time_wo ON labor_time_entries(work_order_id);
CREATE INDEX idx_labor_time_tech ON labor_time_entries(technician_id, start_time);

-- Equipment Meters
CREATE INDEX idx_meter_asset ON equipment_meter_readings(asset_id, reading_date);

-- Maintenance History
CREATE INDEX idx_history_asset ON maintenance_history(asset_id, event_date);
CREATE INDEX idx_history_wo ON maintenance_history(work_order_id);

-- Service Contracts
CREATE INDEX idx_contracts_status ON service_contracts(contract_status, contract_end_date);
CREATE INDEX idx_contracts_vendor ON service_contracts(vendor_id);
CREATE INDEX idx_service_calls_contract ON service_call_logs(contract_id, call_date);

-- Reliability Metrics
CREATE INDEX idx_reliability_asset ON asset_reliability_metrics(asset_id, period_start_date);

-- Costs
CREATE INDEX idx_costs_wo ON maintenance_costs(work_order_id);
CREATE INDEX idx_costs_asset ON maintenance_costs(asset_id, cost_date);
CREATE INDEX idx_costs_center ON maintenance_costs(cost_center_id, cost_date);

-- Integration
CREATE INDEX idx_cmms_integration_status ON cmms_integration_log(integration_status, log_timestamp);

-- ============================================================================
-- COMMENTS
-- ============================================================================

COMMENT ON TABLE maintenance_assets IS 'Complete asset registry with hierarchy, criticality, and lifecycle tracking';
COMMENT ON TABLE work_orders IS 'Maintenance work orders - PM, corrective, breakdown, predictive';
COMMENT ON TABLE pm_schedules IS 'Preventive maintenance schedules - calendar, meter, condition-based';
COMMENT ON TABLE mro_parts IS 'MRO spare parts inventory with min/max levels';
COMMENT ON TABLE maintenance_technicians IS 'Maintenance labor force with skills and certifications';
COMMENT ON TABLE equipment_meter_readings IS 'Equipment meter readings for meter-based PM';
COMMENT ON TABLE failure_codes IS 'Standardized failure classification codes';
COMMENT ON TABLE maintenance_history IS 'Complete maintenance history audit trail';
COMMENT ON TABLE service_contracts IS 'External service contracts and AMC agreements';
COMMENT ON TABLE asset_reliability_metrics IS 'MTBF, MTTR, availability, OEE calculations';
COMMENT ON TABLE cmms_integration_log IS 'Integration tracking with operational, MES, ERP systems';
