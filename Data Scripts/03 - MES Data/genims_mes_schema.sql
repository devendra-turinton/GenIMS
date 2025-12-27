-- GenIMS MES (Manufacturing Execution System) Schema
-- Production-level data bridging shop floor and ERP

-- ============================================================================
-- WORK ORDERS (Production Orders from ERP)
-- ============================================================================

CREATE TABLE work_orders (
    work_order_id VARCHAR(50) PRIMARY KEY,
    work_order_number VARCHAR(50) UNIQUE NOT NULL,
    product_id VARCHAR(50) NOT NULL, -- FK to products
    customer_id VARCHAR(50), -- FK to customers (null for stock orders)
    sales_order_number VARCHAR(50),
    
    -- Planning
    factory_id VARCHAR(50) NOT NULL, -- FK to factories
    line_id VARCHAR(50), -- FK to production_lines (assigned when scheduled)
    planned_quantity INTEGER NOT NULL,
    unit_of_measure VARCHAR(20) DEFAULT 'EA',
    
    -- Scheduling
    priority INTEGER DEFAULT 5, -- 1=highest, 10=lowest
    planned_start_date TIMESTAMP,
    planned_end_date TIMESTAMP,
    scheduled_start_time TIMESTAMP,
    scheduled_end_time TIMESTAMP,
    
    -- Execution
    actual_start_time TIMESTAMP,
    actual_end_time TIMESTAMP,
    produced_quantity INTEGER DEFAULT 0,
    good_quantity INTEGER DEFAULT 0,
    rejected_quantity INTEGER DEFAULT 0,
    scrapped_quantity INTEGER DEFAULT 0,
    rework_quantity INTEGER DEFAULT 0,
    
    -- Status
    status VARCHAR(30) NOT NULL DEFAULT 'created', 
    -- created, released, scheduled, in_progress, on_hold, completed, closed, cancelled
    
    -- Quality
    quality_status VARCHAR(30), -- pending, approved, rejected, conditional
    quality_hold BOOLEAN DEFAULT false,
    
    -- Performance Metrics
    planned_cycle_time_seconds INTEGER,
    actual_cycle_time_seconds INTEGER,
    setup_time_minutes INTEGER,
    run_time_minutes INTEGER,
    downtime_minutes INTEGER,
    yield_percentage DECIMAL(5,2),
    first_pass_yield_percentage DECIMAL(5,2),
    
    -- Costs
    standard_cost_per_unit DECIMAL(12,2),
    actual_cost_per_unit DECIMAL(12,2),
    total_material_cost DECIMAL(15,2),
    total_labor_cost DECIMAL(15,2),
    total_overhead_cost DECIMAL(15,2),
    
    -- Batch/Lot
    batch_number VARCHAR(50),
    lot_number VARCHAR(50),
    expiry_date DATE,
    
    -- Compliance
    electronic_batch_record_id VARCHAR(50), -- Link to eBR
    requires_validation BOOLEAN DEFAULT false,
    validation_status VARCHAR(30),
    
    -- References
    parent_work_order_id VARCHAR(50), -- For rework or split orders
    erp_order_id VARCHAR(50),
    
    -- Audit
    created_by VARCHAR(50), -- FK to employees
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_by VARCHAR(50), -- FK to employees
    closed_at TIMESTAMP
);

-- ============================================================================
-- WORK ORDER OPERATIONS (Routing/Process Steps)
-- ============================================================================

CREATE TABLE work_order_operations (
    operation_id VARCHAR(50) PRIMARY KEY,
    work_order_id VARCHAR(50) NOT NULL, -- FK to work_orders
    operation_sequence INTEGER NOT NULL,
    operation_code VARCHAR(50),
    operation_name VARCHAR(200) NOT NULL,
    
    -- Resource Assignment
    line_id VARCHAR(50), -- FK to production_lines
    machine_id VARCHAR(50), -- FK to machines
    work_center_code VARCHAR(50),
    
    -- Planning
    planned_quantity INTEGER NOT NULL,
    planned_duration_minutes INTEGER,
    planned_setup_time_minutes INTEGER,
    standard_time_per_unit_seconds DECIMAL(10,2),
    
    -- Scheduling
    planned_start_time TIMESTAMP,
    planned_end_time TIMESTAMP,
    
    -- Execution
    actual_start_time TIMESTAMP,
    actual_end_time TIMESTAMP,
    completed_quantity INTEGER DEFAULT 0,
    rejected_quantity INTEGER DEFAULT 0,
    actual_duration_minutes INTEGER,
    actual_setup_time_minutes INTEGER,
    
    -- Status
    status VARCHAR(30) NOT NULL DEFAULT 'pending',
    -- pending, ready, in_progress, completed, skipped, on_hold
    
    -- Labor
    operator_id VARCHAR(50), -- FK to employees (primary operator)
    shift_id VARCHAR(50), -- FK to shifts
    labor_hours DECIMAL(8,2),
    
    -- Quality Control Points
    requires_inspection BOOLEAN DEFAULT false,
    inspection_status VARCHAR(30), -- pending, passed, failed
    inspection_timestamp TIMESTAMP,
    inspector_id VARCHAR(50), -- FK to employees
    
    -- Performance
    efficiency_percentage DECIMAL(5,2),
    scrap_rate_percentage DECIMAL(5,2),
    
    -- Instructions
    work_instructions TEXT,
    safety_notes TEXT,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- MATERIAL TRANSACTIONS (BOM Consumption & Genealogy)
-- ============================================================================

CREATE TABLE material_transactions (
    transaction_id VARCHAR(50) PRIMARY KEY,
    transaction_type VARCHAR(30) NOT NULL, 
    -- issue, return, scrap, adjustment, transfer
    transaction_date TIMESTAMP NOT NULL,
    
    -- Work Order Context
    work_order_id VARCHAR(50), -- FK to work_orders
    operation_id VARCHAR(50), -- FK to work_order_operations
    
    -- Material Details
    material_code VARCHAR(50) NOT NULL,
    material_name VARCHAR(200),
    material_type VARCHAR(50), -- raw_material, component, sub_assembly, consumable
    
    -- Quantity
    quantity DECIMAL(15,4) NOT NULL,
    unit_of_measure VARCHAR(20),
    
    -- Lot/Batch Traceability
    lot_number VARCHAR(50),
    batch_number VARCHAR(50),
    serial_number VARCHAR(50),
    expiry_date DATE,
    supplier_lot_number VARCHAR(50),
    
    -- Location
    from_location VARCHAR(100),
    to_location VARCHAR(100),
    warehouse_location VARCHAR(100),
    
    -- Cost
    unit_cost DECIMAL(12,4),
    total_cost DECIMAL(15,2),
    
    -- Quality
    quality_status VARCHAR(30), -- approved, quarantine, rejected
    inspection_required BOOLEAN DEFAULT false,
    certificate_of_analysis VARCHAR(100), -- COA reference
    
    -- Genealogy (Parent-Child Relationships)
    parent_lot_number VARCHAR(50), -- For traceability
    consumed_by_lot_number VARCHAR(50), -- Which finished goods lot used this
    
    -- User
    performed_by VARCHAR(50), -- FK to employees
    
    -- Compliance
    requires_documentation BOOLEAN DEFAULT false,
    documentation_complete BOOLEAN DEFAULT false,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- QUALITY INSPECTIONS
-- ============================================================================

CREATE TABLE quality_inspections (
    inspection_id VARCHAR(50) PRIMARY KEY,
    inspection_type VARCHAR(50) NOT NULL, 
    -- incoming, in_process, final, patrol, audit
    inspection_date TIMESTAMP NOT NULL,
    
    -- Context
    work_order_id VARCHAR(50), -- FK to work_orders
    operation_id VARCHAR(50), -- FK to work_order_operations
    product_id VARCHAR(50), -- FK to products
    
    -- Sample
    sample_size INTEGER,
    lot_number VARCHAR(50),
    batch_number VARCHAR(50),
    serial_number VARCHAR(50),
    
    -- Inspector
    inspector_id VARCHAR(50) NOT NULL, -- FK to employees
    shift_id VARCHAR(50), -- FK to shifts
    
    -- Results
    inspection_result VARCHAR(30) NOT NULL, 
    -- pass, fail, conditional_pass, hold, rework_required
    defects_found INTEGER DEFAULT 0,
    critical_defects INTEGER DEFAULT 0,
    major_defects INTEGER DEFAULT 0,
    minor_defects INTEGER DEFAULT 0,
    
    -- Measurements
    measured_values JSONB, -- Store measurement data as JSON
    specification_values JSONB, -- Specification limits
    
    -- Disposition
    disposition VARCHAR(50), 
    -- accept, reject, rework, use_as_is, scrap, return_to_vendor
    disposition_reason TEXT,
    disposition_by VARCHAR(50), -- FK to employees
    
    -- Non-Conformance
    ncr_number VARCHAR(50), -- Non-Conformance Report
    corrective_action_required BOOLEAN DEFAULT false,
    
    -- Documentation
    inspection_plan_id VARCHAR(50),
    inspection_checklist_id VARCHAR(50),
    photos_attached BOOLEAN DEFAULT false,
    
    -- Approval
    approved_by VARCHAR(50), -- FK to employees
    approved_at TIMESTAMP,
    
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- DEFECT TRACKING
-- ============================================================================

CREATE TABLE defects (
    defect_id VARCHAR(50) PRIMARY KEY,
    defect_code VARCHAR(50),
    defect_category VARCHAR(50), -- dimensional, visual, functional, material, assembly
    defect_description TEXT NOT NULL,
    defect_severity VARCHAR(20), -- critical, major, minor
    
    -- Occurrence
    detected_date TIMESTAMP NOT NULL,
    work_order_id VARCHAR(50), -- FK to work_orders
    operation_id VARCHAR(50), -- FK to work_order_operations
    inspection_id VARCHAR(50), -- FK to quality_inspections
    
    -- Product Context
    product_id VARCHAR(50), -- FK to products
    lot_number VARCHAR(50),
    quantity_affected INTEGER,
    
    -- Detection
    detected_by VARCHAR(50), -- FK to employees
    detection_method VARCHAR(50), -- visual, measurement, testing, customer_complaint
    
    -- Root Cause
    root_cause_category VARCHAR(100), -- material, machine, method, man, measurement, environment
    root_cause_description TEXT,
    root_cause_analysis_complete BOOLEAN DEFAULT false,
    
    -- Corrective Action
    corrective_action TEXT,
    preventive_action TEXT,
    action_owner VARCHAR(50), -- FK to employees
    action_due_date DATE,
    action_completed BOOLEAN DEFAULT false,
    
    -- Cost Impact
    scrap_cost DECIMAL(12,2),
    rework_cost DECIMAL(12,2),
    total_cost DECIMAL(12,2),
    
    -- Status
    status VARCHAR(30) DEFAULT 'open', -- open, investigating, action_pending, closed
    closed_date TIMESTAMP,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- LABOR TRACKING (Time & Attendance for Production)
-- ============================================================================

CREATE TABLE labor_transactions (
    labor_transaction_id VARCHAR(50) PRIMARY KEY,
    transaction_date TIMESTAMP NOT NULL,
    
    -- Employee
    employee_id VARCHAR(50) NOT NULL, -- FK to employees
    shift_id VARCHAR(50), -- FK to shifts
    
    -- Work Order Context
    work_order_id VARCHAR(50), -- FK to work_orders
    operation_id VARCHAR(50), -- FK to work_order_operations
    
    -- Activity
    activity_code VARCHAR(50),
    activity_type VARCHAR(50), 
    -- direct_labor, indirect_labor, setup, training, maintenance, meeting, break
    
    -- Time
    clock_in_time TIMESTAMP,
    clock_out_time TIMESTAMP,
    duration_minutes INTEGER,
    break_time_minutes INTEGER DEFAULT 0,
    
    -- Production
    quantity_produced INTEGER,
    quantity_rejected INTEGER,
    
    -- Performance
    standard_hours DECIMAL(8,2),
    actual_hours DECIMAL(8,2),
    efficiency_percentage DECIMAL(5,2),
    
    -- Cost
    hourly_rate DECIMAL(10,2),
    labor_cost DECIMAL(12,2),
    overtime_hours DECIMAL(8,2),
    overtime_cost DECIMAL(12,2),
    
    -- Approval
    approved BOOLEAN DEFAULT false,
    approved_by VARCHAR(50), -- FK to employees
    approved_at TIMESTAMP,
    
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- DOWNTIME TRACKING (Machine/Line Downtime Events)
-- ============================================================================

CREATE TABLE downtime_events (
    downtime_id VARCHAR(50) PRIMARY KEY,
    
    -- Equipment
    machine_id VARCHAR(50), -- FK to machines
    line_id VARCHAR(50), -- FK to production_lines
    factory_id VARCHAR(50) NOT NULL, -- FK to factories
    
    -- Timing
    downtime_start TIMESTAMP NOT NULL,
    downtime_end TIMESTAMP,
    duration_minutes INTEGER,
    
    -- Classification
    downtime_category VARCHAR(50) NOT NULL,
    -- breakdown, changeover, material_shortage, quality_hold, maintenance, no_operator, 
    -- no_orders, waiting_for_approval, power_failure, tool_change
    
    downtime_reason_code VARCHAR(50),
    downtime_reason_description TEXT,
    
    -- Impact
    work_order_id VARCHAR(50), -- FK to work_orders (affected order)
    operation_id VARCHAR(50), -- FK to work_order_operations
    production_loss_units INTEGER,
    estimated_cost DECIMAL(12,2),
    
    -- Response
    reported_by VARCHAR(50), -- FK to employees
    responded_by VARCHAR(50), -- FK to employees (maintenance/supervisor)
    response_time_minutes INTEGER, -- MTTR
    
    -- Resolution
    resolution_action TEXT,
    root_cause TEXT,
    preventive_action TEXT,
    
    -- Maintenance Link
    maintenance_work_order VARCHAR(50),
    spare_parts_used TEXT,
    
    -- Status
    status VARCHAR(30) DEFAULT 'active', -- active, resolved, pending_parts, escalated
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP
);

-- ============================================================================
-- EQUIPMENT CHANGEOVERS (Setup/Changeover Tracking)
-- ============================================================================

CREATE TABLE changeover_events (
    changeover_id VARCHAR(50) PRIMARY KEY,
    
    -- Equipment
    line_id VARCHAR(50) NOT NULL, -- FK to production_lines
    machine_id VARCHAR(50), -- FK to machines
    
    -- Changeover Details
    changeover_type VARCHAR(50), -- product_change, tool_change, material_change, format_change
    from_product_id VARCHAR(50), -- FK to products
    to_product_id VARCHAR(50), -- FK to products
    from_work_order_id VARCHAR(50), -- FK to work_orders
    to_work_order_id VARCHAR(50), -- FK to work_orders
    
    -- Timing
    changeover_start TIMESTAMP NOT NULL,
    changeover_end TIMESTAMP,
    planned_duration_minutes INTEGER,
    actual_duration_minutes INTEGER,
    
    -- Activities
    teardown_time_minutes INTEGER,
    setup_time_minutes INTEGER,
    adjustment_time_minutes INTEGER,
    trial_run_time_minutes INTEGER,
    
    -- Performance
    first_good_part_time TIMESTAMP, -- Time to first quality part
    parts_produced_during_setup INTEGER,
    parts_scrapped_during_setup INTEGER,
    
    -- Team
    supervisor_id VARCHAR(50), -- FK to employees
    operator_ids TEXT, -- Comma-separated employee_ids
    
    -- Quality
    first_piece_inspection_passed BOOLEAN,
    quality_approval_by VARCHAR(50), -- FK to employees
    
    -- Efficiency
    target_changeover_time_minutes INTEGER,
    improvement_opportunity TEXT,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- ELECTRONIC BATCH RECORDS (Compliance Documentation)
-- ============================================================================

CREATE TABLE electronic_batch_records (
    ebr_id VARCHAR(50) PRIMARY KEY,
    batch_number VARCHAR(50) UNIQUE NOT NULL,
    
    -- Product & Order
    product_id VARCHAR(50) NOT NULL, -- FK to products
    work_order_id VARCHAR(50) NOT NULL, -- FK to work_orders
    batch_size INTEGER NOT NULL,
    
    -- Formula/Recipe
    formula_id VARCHAR(50),
    formula_version VARCHAR(20),
    
    -- Manufacturing
    manufacturing_date DATE NOT NULL,
    expiration_date DATE,
    retest_date DATE,
    
    -- Location
    factory_id VARCHAR(50) NOT NULL, -- FK to factories
    manufacturing_area VARCHAR(100),
    
    -- Status
    record_status VARCHAR(30) DEFAULT 'in_progress',
    -- in_progress, under_review, approved, rejected
    
    -- Approval Workflow
    prepared_by VARCHAR(50), -- FK to employees
    prepared_at TIMESTAMP,
    reviewed_by VARCHAR(50), -- FK to employees
    reviewed_at TIMESTAMP,
    approved_by VARCHAR(50), -- FK to employees
    approved_at TIMESTAMP,
    
    -- Quality
    release_status VARCHAR(30), -- pending, released, rejected, on_hold
    released_by VARCHAR(50), -- FK to employees
    released_at TIMESTAMP,
    
    -- Deviations
    has_deviations BOOLEAN DEFAULT false,
    deviation_count INTEGER DEFAULT 0,
    
    -- Environmental Conditions
    temperature_min_c DECIMAL(5,2),
    temperature_max_c DECIMAL(5,2),
    humidity_min_percentage DECIMAL(5,2),
    humidity_max_percentage DECIMAL(5,2),
    
    -- Compliance
    regulatory_requirement VARCHAR(100), -- FDA, ISO, IATF, etc.
    audit_trail JSONB, -- Complete audit trail in JSON
    
    -- Digital Signature
    electronic_signature_applied BOOLEAN DEFAULT false,
    signature_metadata JSONB,
    
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- PRODUCTION SCHEDULE (Daily/Weekly Schedule)
-- ============================================================================

CREATE TABLE production_schedule (
    schedule_id VARCHAR(50) PRIMARY KEY,
    
    -- Schedule Period
    schedule_date DATE NOT NULL,
    schedule_week INTEGER, -- Week number
    shift_id VARCHAR(50), -- FK to shifts
    
    -- Resources
    line_id VARCHAR(50) NOT NULL, -- FK to production_lines
    factory_id VARCHAR(50) NOT NULL, -- FK to factories
    
    -- Work Order
    work_order_id VARCHAR(50) NOT NULL, -- FK to work_orders
    operation_id VARCHAR(50), -- FK to work_order_operations
    sequence_number INTEGER, -- Order sequence for the day
    
    -- Planning
    planned_start_time TIMESTAMP NOT NULL,
    planned_end_time TIMESTAMP NOT NULL,
    planned_quantity INTEGER NOT NULL,
    
    -- Constraints
    priority INTEGER DEFAULT 5,
    customer_due_date DATE,
    material_available BOOLEAN DEFAULT true,
    operator_available BOOLEAN DEFAULT true,
    equipment_available BOOLEAN DEFAULT true,
    
    -- Status
    schedule_status VARCHAR(30) DEFAULT 'planned',
    -- planned, confirmed, in_progress, completed, delayed, cancelled
    
    -- Actual Execution
    actual_start_time TIMESTAMP,
    actual_end_time TIMESTAMP,
    actual_quantity INTEGER,
    
    -- Performance
    on_time_start BOOLEAN,
    on_time_completion BOOLEAN,
    schedule_adherence_percentage DECIMAL(5,2),
    
    -- Planning Info
    planner_id VARCHAR(50), -- FK to employees
    planning_notes TEXT,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- INDICES FOR PERFORMANCE
-- ============================================================================

-- Work Orders
CREATE INDEX idx_work_orders_status ON work_orders(status, planned_start_date);
CREATE INDEX idx_work_orders_product ON work_orders(product_id, status);
CREATE INDEX idx_work_orders_customer ON work_orders(customer_id, status);
CREATE INDEX idx_work_orders_line ON work_orders(line_id, actual_start_time);
CREATE INDEX idx_work_orders_batch ON work_orders(batch_number);
CREATE INDEX idx_work_orders_dates ON work_orders(actual_start_time, actual_end_time);

-- Work Order Operations
CREATE INDEX idx_operations_work_order ON work_order_operations(work_order_id, operation_sequence);
CREATE INDEX idx_operations_line ON work_order_operations(line_id, actual_start_time);
CREATE INDEX idx_operations_status ON work_order_operations(status, planned_start_time);

-- Material Transactions
CREATE INDEX idx_material_work_order ON material_transactions(work_order_id, transaction_date);
CREATE INDEX idx_material_lot ON material_transactions(lot_number, transaction_date);
CREATE INDEX idx_material_type ON material_transactions(transaction_type, transaction_date);

-- Quality Inspections
CREATE INDEX idx_inspections_work_order ON quality_inspections(work_order_id, inspection_date);
CREATE INDEX idx_inspections_result ON quality_inspections(inspection_result, inspection_date);
CREATE INDEX idx_inspections_product ON quality_inspections(product_id, inspection_date);

-- Defects
CREATE INDEX idx_defects_work_order ON defects(work_order_id, detected_date);
CREATE INDEX idx_defects_status ON defects(status, detected_date);
CREATE INDEX idx_defects_severity ON defects(defect_severity, detected_date);

-- Labor Transactions
CREATE INDEX idx_labor_employee ON labor_transactions(employee_id, transaction_date);
CREATE INDEX idx_labor_work_order ON labor_transactions(work_order_id, transaction_date);
CREATE INDEX idx_labor_activity ON labor_transactions(activity_type, transaction_date);

-- Downtime
CREATE INDEX idx_downtime_machine ON downtime_events(machine_id, downtime_start);
CREATE INDEX idx_downtime_line ON downtime_events(line_id, downtime_start);
CREATE INDEX idx_downtime_category ON downtime_events(downtime_category, downtime_start);
CREATE INDEX idx_downtime_status ON downtime_events(status, downtime_start);

-- Changeovers
CREATE INDEX idx_changeover_line ON changeover_events(line_id, changeover_start);
CREATE INDEX idx_changeover_product ON changeover_events(to_product_id, changeover_start);

-- Electronic Batch Records
CREATE INDEX idx_ebr_batch ON electronic_batch_records(batch_number);
CREATE INDEX idx_ebr_product ON electronic_batch_records(product_id, manufacturing_date);
CREATE INDEX idx_ebr_status ON electronic_batch_records(record_status, manufacturing_date);

-- Production Schedule
CREATE INDEX idx_schedule_date ON production_schedule(schedule_date, line_id);
CREATE INDEX idx_schedule_work_order ON production_schedule(work_order_id, schedule_date);
CREATE INDEX idx_schedule_line ON production_schedule(line_id, planned_start_time);
CREATE INDEX idx_schedule_status ON production_schedule(schedule_status, schedule_date);

-- ============================================================================
-- COMMENTS FOR DOCUMENTATION
-- ============================================================================

COMMENT ON TABLE work_orders IS 'Production orders from ERP - master record for manufacturing execution';
COMMENT ON TABLE work_order_operations IS 'Individual routing steps/operations for each work order';
COMMENT ON TABLE material_transactions IS 'Material consumption and genealogy tracking for traceability';
COMMENT ON TABLE quality_inspections IS 'Quality control checkpoints and inspection results';
COMMENT ON TABLE defects IS 'Defect tracking and root cause analysis';
COMMENT ON TABLE labor_transactions IS 'Labor time tracking and efficiency monitoring';
COMMENT ON TABLE downtime_events IS 'Equipment downtime tracking for OEE calculation';
COMMENT ON TABLE changeover_events IS 'Setup and changeover time tracking for SMED analysis';
COMMENT ON TABLE electronic_batch_records IS 'Regulatory compliance documentation (eBR)';
COMMENT ON TABLE production_schedule IS 'Daily/weekly production schedule and execution tracking';
