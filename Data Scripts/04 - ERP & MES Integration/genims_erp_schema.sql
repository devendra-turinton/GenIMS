-- GenIMS ERP (Enterprise Resource Planning) Schema
-- Core business planning and resource management system

-- ============================================================================
-- MATERIAL MASTER DATA
-- ============================================================================

CREATE TABLE materials (
    material_id VARCHAR(50) PRIMARY KEY,
    material_code VARCHAR(50) UNIQUE NOT NULL,
    material_name VARCHAR(200) NOT NULL,
    material_type VARCHAR(50) NOT NULL, 
    -- raw_material, component, sub_assembly, finished_good, consumable, packaging
    
    -- Classification
    material_group VARCHAR(50),
    commodity_code VARCHAR(50),
    product_family VARCHAR(50),
    
    -- Physical Properties
    base_unit_of_measure VARCHAR(20) NOT NULL,
    weight_kg DECIMAL(10,4),
    volume_m3 DECIMAL(10,6),
    dimensions VARCHAR(100), -- LxWxH
    
    -- Procurement
    procurement_type VARCHAR(30), -- make, buy, both
    default_supplier_id VARCHAR(50), -- FK to suppliers
    lead_time_days INTEGER,
    minimum_order_quantity DECIMAL(15,4),
    order_multiple DECIMAL(15,4),
    
    -- Inventory Control
    abc_classification VARCHAR(1), -- A, B, C
    reorder_point DECIMAL(15,4),
    safety_stock DECIMAL(15,4),
    maximum_stock DECIMAL(15,4),
    
    -- Costing
    valuation_class VARCHAR(50),
    standard_cost DECIMAL(15,4),
    moving_average_cost DECIMAL(15,4),
    last_purchase_price DECIMAL(15,4),
    
    -- Quality
    inspection_required BOOLEAN DEFAULT false,
    shelf_life_days INTEGER,
    
    -- Planning
    mrp_type VARCHAR(30), -- reorder_point, lot_for_lot, period_order_quantity
    lot_sizing_procedure VARCHAR(30),
    planning_time_fence_days INTEGER,
    
    -- Status
    material_status VARCHAR(30) DEFAULT 'active', -- active, inactive, obsolete, restricted
    blocked_for_procurement BOOLEAN DEFAULT false,
    blocked_for_production BOOLEAN DEFAULT false,
    
    -- References
    product_id VARCHAR(50), -- FK to products (if finished good)
    
    -- Audit
    created_by VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- BILL OF MATERIALS (BOM)
-- ============================================================================

CREATE TABLE bill_of_materials (
    bom_id VARCHAR(50) PRIMARY KEY,
    bom_number VARCHAR(50) UNIQUE NOT NULL,
    
    -- Parent Material
    parent_material_id VARCHAR(50) NOT NULL, -- FK to materials
    parent_quantity DECIMAL(15,4) DEFAULT 1,
    
    -- BOM Details
    bom_usage VARCHAR(30), -- production, engineering, planning, costing
    bom_status VARCHAR(30) DEFAULT 'active', -- active, inactive, engineering, obsolete
    alternative_bom INTEGER DEFAULT 1,
    
    -- Validity
    valid_from DATE NOT NULL,
    valid_to DATE,
    
    -- Production
    base_quantity DECIMAL(15,4) DEFAULT 1,
    base_unit VARCHAR(20),
    lot_size DECIMAL(15,4),
    scrap_percentage DECIMAL(5,2) DEFAULT 0,
    
    -- References
    plant_id VARCHAR(50), -- FK to factories
    product_id VARCHAR(50), -- FK to products
    
    -- Engineering
    engineering_change_number VARCHAR(50),
    revision VARCHAR(20),
    is_current_revision BOOLEAN DEFAULT true,
    
    -- Audit
    created_by VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE bom_components (
    component_id VARCHAR(50) PRIMARY KEY,
    bom_id VARCHAR(50) NOT NULL, -- FK to bill_of_materials
    item_number INTEGER NOT NULL,
    
    -- Component Material
    material_id VARCHAR(50) NOT NULL, -- FK to materials
    component_quantity DECIMAL(15,4) NOT NULL,
    component_unit VARCHAR(20) NOT NULL,
    
    -- Planning
    component_scrap_percentage DECIMAL(5,2) DEFAULT 0,
    operation_number INTEGER, -- Which operation consumes this
    backflush BOOLEAN DEFAULT false,
    
    -- Procurement
    procurement_indicator VARCHAR(30), -- stock, direct_procurement, phantom
    
    -- Cost Allocation
    cost_relevance BOOLEAN DEFAULT true,
    
    -- Substitutes
    has_substitute BOOLEAN DEFAULT false,
    substitute_material_id VARCHAR(50), -- FK to materials
    
    -- Validity
    valid_from DATE,
    valid_to DATE,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- ROUTING (MANUFACTURING PROCESS)
-- ============================================================================

CREATE TABLE routing (
    routing_id VARCHAR(50) PRIMARY KEY,
    routing_number VARCHAR(50) UNIQUE NOT NULL,
    
    -- Material
    material_id VARCHAR(50) NOT NULL, -- FK to materials
    plant_id VARCHAR(50), -- FK to factories
    
    -- Routing Details
    routing_usage VARCHAR(30), -- production, costing, scheduling
    routing_status VARCHAR(30) DEFAULT 'active',
    
    -- Production
    base_quantity DECIMAL(15,4) DEFAULT 1,
    lot_size_from DECIMAL(15,4),
    lot_size_to DECIMAL(15,4),
    
    -- Validity
    valid_from DATE NOT NULL,
    valid_to DATE,
    
    created_by VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE routing_operations (
    operation_id VARCHAR(50) PRIMARY KEY,
    routing_id VARCHAR(50) NOT NULL, -- FK to routing
    operation_number INTEGER NOT NULL,
    
    -- Operation Details
    operation_short_text VARCHAR(200),
    operation_description TEXT,
    work_center_id VARCHAR(50), -- FK to work_centers
    
    -- Control
    control_key VARCHAR(10), -- PP01 (internal processing), PP02 (external), etc.
    
    -- Times (in minutes)
    setup_time DECIMAL(10,2),
    machine_time DECIMAL(10,2),
    labor_time DECIMAL(10,2),
    
    -- Capacity
    base_quantity DECIMAL(15,4) DEFAULT 1,
    standard_value_unit VARCHAR(20),
    
    -- Costing
    activity_type VARCHAR(50),
    price_per_unit DECIMAL(12,4),
    
    -- Sequencing
    earliest_start_offset INTEGER DEFAULT 0,
    latest_start_offset INTEGER DEFAULT 0,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE work_centers (
    work_center_id VARCHAR(50) PRIMARY KEY,
    work_center_code VARCHAR(50) UNIQUE NOT NULL,
    work_center_name VARCHAR(200) NOT NULL,
    
    -- Location
    plant_id VARCHAR(50), -- FK to factories
    cost_center_id VARCHAR(50), -- FK to cost_centers
    
    -- Category
    work_center_category VARCHAR(50), -- machine, labor, both
    
    -- Capacity
    capacity_category VARCHAR(50), -- machine_hours, labor_hours, units
    available_capacity DECIMAL(10,2), -- per day
    utilization_percentage DECIMAL(5,2),
    
    -- Costing
    hourly_rate DECIMAL(10,2),
    currency VARCHAR(3) DEFAULT 'INR',
    
    -- Scheduling
    queue_time_days DECIMAL(5,2) DEFAULT 0,
    setup_time_minutes DECIMAL(10,2) DEFAULT 0,
    
    -- References
    line_id VARCHAR(50), -- FK to production_lines
    machine_id VARCHAR(50), -- FK to machines
    
    -- Status
    is_active BOOLEAN DEFAULT true,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- PRODUCTION ORDERS (ERP Side)
-- ============================================================================

CREATE TABLE production_orders (
    production_order_id VARCHAR(50) PRIMARY KEY,
    production_order_number VARCHAR(50) UNIQUE NOT NULL,
    
    -- Material
    material_id VARCHAR(50) NOT NULL, -- FK to materials
    plant_id VARCHAR(50) NOT NULL, -- FK to factories
    
    -- Source
    sales_order_id VARCHAR(50), -- FK to sales_orders (make-to-order)
    sales_order_line INTEGER,
    mrp_element VARCHAR(50), -- From MRP run
    
    -- Order Details
    order_type VARCHAR(30), -- production, rework, refurbishment
    production_version INTEGER DEFAULT 1,
    
    -- Quantities
    order_quantity DECIMAL(15,4) NOT NULL,
    delivered_quantity DECIMAL(15,4) DEFAULT 0,
    scrap_quantity DECIMAL(15,4) DEFAULT 0,
    
    -- Scheduling
    basic_start_date DATE NOT NULL,
    basic_end_date DATE NOT NULL,
    scheduled_start_date DATE,
    scheduled_end_date DATE,
    actual_start_date DATE,
    actual_finish_date DATE,
    
    -- Status System
    system_status VARCHAR(30) DEFAULT 'created', 
    -- created, released, partially_released, printed, in_process, partially_confirmed,
    -- confirmed, partially_delivered, delivered, technically_completed, closed
    
    user_status VARCHAR(30),
    
    -- Control
    priority INTEGER DEFAULT 5,
    scheduling_type VARCHAR(30), -- forward, backward, only_capacity
    
    -- References
    bom_id VARCHAR(50), -- FK to bill_of_materials
    routing_id VARCHAR(50), -- FK to routing
    work_order_id VARCHAR(50), -- FK to work_orders (MES link)
    
    -- Costs
    planned_costs DECIMAL(15,2),
    actual_costs DECIMAL(15,2),
    variance_amount DECIMAL(15,2),
    
    -- Settlement
    settlement_rule VARCHAR(50),
    settlement_receiver VARCHAR(50),
    
    -- Audit
    created_by VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    released_by VARCHAR(50),
    released_at TIMESTAMP,
    closed_at TIMESTAMP
);

-- ============================================================================
-- SUPPLIERS
-- ============================================================================

CREATE TABLE suppliers (
    supplier_id VARCHAR(50) PRIMARY KEY,
    supplier_code VARCHAR(50) UNIQUE NOT NULL,
    supplier_name VARCHAR(200) NOT NULL,
    
    -- Contact
    contact_person VARCHAR(100),
    email VARCHAR(100),
    phone VARCHAR(50),
    
    -- Address
    address_line1 VARCHAR(200),
    address_line2 VARCHAR(200),
    city VARCHAR(100),
    state VARCHAR(100),
    country VARCHAR(50),
    postal_code VARCHAR(20),
    
    -- Business Details
    tax_id VARCHAR(50),
    currency VARCHAR(3) DEFAULT 'INR',
    payment_terms VARCHAR(50), -- NET30, NET60, 2/10NET30
    
    -- Performance
    on_time_delivery_percentage DECIMAL(5,2),
    quality_rating DECIMAL(5,2), -- 1-5 scale
    total_orders_count INTEGER DEFAULT 0,
    total_purchase_value DECIMAL(15,2) DEFAULT 0,
    
    -- Compliance
    supplier_type VARCHAR(50), -- raw_material, component, service, packaging
    certification_status VARCHAR(100), -- ISO9001, IATF16949, etc.
    
    -- Status
    supplier_status VARCHAR(30) DEFAULT 'active', -- active, blocked, restricted
    blocked_for_orders BOOLEAN DEFAULT false,
    
    -- Audit
    created_by VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- PURCHASE REQUISITIONS
-- ============================================================================

CREATE TABLE purchase_requisitions (
    requisition_id VARCHAR(50) PRIMARY KEY,
    requisition_number VARCHAR(50) UNIQUE NOT NULL,
    
    -- Request Details
    requisition_type VARCHAR(30), -- stock, non_stock, service
    requisition_date DATE NOT NULL,
    required_date DATE NOT NULL,
    
    -- Requester
    requester_id VARCHAR(50), -- FK to employees
    cost_center_id VARCHAR(50), -- FK to cost_centers
    plant_id VARCHAR(50), -- FK to factories
    
    -- Priority
    priority VARCHAR(30) DEFAULT 'normal', -- urgent, high, normal, low
    
    -- Approval
    approval_status VARCHAR(30) DEFAULT 'pending', 
    -- pending, approved, rejected, partially_approved
    approved_by VARCHAR(50), -- FK to employees
    approved_at TIMESTAMP,
    
    -- Source
    source_type VARCHAR(50), -- mrp, manual, stock_transfer, maintenance
    source_document VARCHAR(50),
    
    -- Status
    overall_status VARCHAR(30) DEFAULT 'open', -- open, in_purchasing, completed, cancelled
    
    -- Notes
    remarks TEXT,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE purchase_requisition_lines (
    requisition_line_id VARCHAR(50) PRIMARY KEY,
    requisition_id VARCHAR(50) NOT NULL, -- FK to purchase_requisitions
    line_number INTEGER NOT NULL,
    
    -- Material
    material_id VARCHAR(50) NOT NULL, -- FK to materials
    material_description VARCHAR(200),
    
    -- Quantity
    quantity DECIMAL(15,4) NOT NULL,
    unit_of_measure VARCHAR(20) NOT NULL,
    
    -- Delivery
    delivery_date DATE NOT NULL,
    delivery_location VARCHAR(100),
    
    -- Pricing
    estimated_price DECIMAL(12,4),
    estimated_total DECIMAL(15,2),
    
    -- Assignment
    assigned_to_po VARCHAR(50), -- FK to purchase_orders
    assigned_quantity DECIMAL(15,4) DEFAULT 0,
    
    -- Accounting
    gl_account VARCHAR(20),
    cost_center_id VARCHAR(50), -- FK to cost_centers
    
    -- Status
    line_status VARCHAR(30) DEFAULT 'open', -- open, assigned, completed
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- PURCHASE ORDERS
-- ============================================================================

CREATE TABLE purchase_orders (
    purchase_order_id VARCHAR(50) PRIMARY KEY,
    po_number VARCHAR(50) UNIQUE NOT NULL,
    
    -- Supplier
    supplier_id VARCHAR(50) NOT NULL, -- FK to suppliers
    
    -- Document Details
    po_date DATE NOT NULL,
    po_type VARCHAR(30), -- standard, subcontracting, consignment, service
    company_code VARCHAR(10),
    purchasing_organization VARCHAR(10),
    purchasing_group VARCHAR(10),
    
    -- Terms
    payment_terms VARCHAR(50),
    incoterms VARCHAR(20),
    currency VARCHAR(3) DEFAULT 'INR',
    exchange_rate DECIMAL(10,6) DEFAULT 1,
    
    -- Amounts
    total_value DECIMAL(15,2),
    tax_amount DECIMAL(15,2),
    freight_charges DECIMAL(15,2),
    
    -- Status
    po_status VARCHAR(30) DEFAULT 'created', 
    -- created, released, in_transit, partially_received, received, invoiced, closed
    
    release_indicator BOOLEAN DEFAULT false,
    
    -- Delivery
    delivery_address_id VARCHAR(50),
    
    -- References
    contract_number VARCHAR(50),
    quotation_number VARCHAR(50),
    
    -- Audit
    created_by VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    released_by VARCHAR(50),
    released_at TIMESTAMP
);

CREATE TABLE purchase_order_lines (
    po_line_id VARCHAR(50) PRIMARY KEY,
    purchase_order_id VARCHAR(50) NOT NULL, -- FK to purchase_orders
    line_number INTEGER NOT NULL,
    
    -- Material
    material_id VARCHAR(50) NOT NULL, -- FK to materials
    material_description VARCHAR(200),
    
    -- Quantity
    order_quantity DECIMAL(15,4) NOT NULL,
    unit_of_measure VARCHAR(20) NOT NULL,
    received_quantity DECIMAL(15,4) DEFAULT 0,
    invoiced_quantity DECIMAL(15,4) DEFAULT 0,
    
    -- Pricing
    unit_price DECIMAL(12,4) NOT NULL,
    net_price DECIMAL(15,2),
    tax_code VARCHAR(20),
    tax_amount DECIMAL(15,2),
    
    -- Delivery
    delivery_date DATE NOT NULL,
    plant_id VARCHAR(50), -- FK to factories
    storage_location VARCHAR(50),
    
    -- Accounting
    gl_account VARCHAR(20),
    cost_center_id VARCHAR(50), -- FK to cost_centers
    
    -- Quality
    goods_receipt_required BOOLEAN DEFAULT true,
    invoice_receipt_required BOOLEAN DEFAULT true,
    quality_inspection_required BOOLEAN DEFAULT false,
    
    -- References
    requisition_id VARCHAR(50), -- FK to purchase_requisitions
    requisition_line INTEGER,
    
    -- Status
    line_status VARCHAR(30) DEFAULT 'open', 
    -- open, in_transit, partially_received, received, closed
    deletion_indicator BOOLEAN DEFAULT false,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- GOODS RECEIPTS
-- ============================================================================

CREATE TABLE goods_receipts (
    goods_receipt_id VARCHAR(50) PRIMARY KEY,
    gr_number VARCHAR(50) UNIQUE NOT NULL,
    gr_date DATE NOT NULL,
    posting_date DATE NOT NULL,
    
    -- Reference
    purchase_order_id VARCHAR(50), -- FK to purchase_orders
    po_line_id VARCHAR(50), -- FK to purchase_order_lines
    supplier_id VARCHAR(50), -- FK to suppliers
    
    -- Material
    material_id VARCHAR(50) NOT NULL, -- FK to materials
    
    -- Quantity
    quantity_received DECIMAL(15,4) NOT NULL,
    unit_of_measure VARCHAR(20) NOT NULL,
    
    -- Location
    plant_id VARCHAR(50), -- FK to factories
    storage_location VARCHAR(50),
    batch_number VARCHAR(50),
    
    -- Quality
    inspection_lot VARCHAR(50),
    quality_status VARCHAR(30), -- unrestricted, quality_inspection, blocked
    
    -- Valuation
    unit_price DECIMAL(12,4),
    total_value DECIMAL(15,2),
    
    -- References
    delivery_note VARCHAR(50),
    bill_of_lading VARCHAR(50),
    
    -- Status
    gr_status VARCHAR(30) DEFAULT 'posted', -- posted, cancelled, reversed
    cancelled BOOLEAN DEFAULT false,
    reversal_gr VARCHAR(50),
    
    -- Audit
    created_by VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- INVENTORY MANAGEMENT
-- ============================================================================

CREATE TABLE inventory_balances (
    balance_id VARCHAR(50) PRIMARY KEY,
    
    -- Material & Location
    material_id VARCHAR(50) NOT NULL, -- FK to materials
    plant_id VARCHAR(50) NOT NULL, -- FK to factories
    storage_location VARCHAR(50) NOT NULL,
    batch_number VARCHAR(50),
    
    -- Stock Types
    unrestricted_stock DECIMAL(15,4) DEFAULT 0,
    quality_inspection_stock DECIMAL(15,4) DEFAULT 0,
    blocked_stock DECIMAL(15,4) DEFAULT 0,
    
    -- Special Stocks
    consignment_stock DECIMAL(15,4) DEFAULT 0,
    in_transit_stock DECIMAL(15,4) DEFAULT 0,
    
    -- Valuation
    stock_value DECIMAL(15,2),
    moving_average_price DECIMAL(12,4),
    
    -- Last Movement
    last_goods_receipt_date DATE,
    last_goods_issue_date DATE,
    
    -- Physical Inventory
    last_count_date DATE,
    cycle_count_indicator VARCHAR(10),
    
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE inventory_transactions (
    transaction_id VARCHAR(50) PRIMARY KEY,
    material_document VARCHAR(50),
    document_item INTEGER,
    
    -- Transaction Details
    transaction_type VARCHAR(50) NOT NULL,
    -- goods_receipt, goods_issue, transfer_posting, physical_inventory,
    -- scrap, return, adjustment
    
    movement_type VARCHAR(10) NOT NULL, -- 101, 261, 311, 551, etc.
    posting_date DATE NOT NULL,
    document_date DATE NOT NULL,
    
    -- Material & Location
    material_id VARCHAR(50) NOT NULL, -- FK to materials
    plant_id VARCHAR(50) NOT NULL, -- FK to factories
    storage_location VARCHAR(50),
    batch_number VARCHAR(50),
    
    -- Quantity & UOM
    quantity DECIMAL(15,4) NOT NULL,
    unit_of_measure VARCHAR(20) NOT NULL,
    
    -- Valuation
    amount DECIMAL(15,2),
    
    -- References
    purchase_order_id VARCHAR(50), -- FK to purchase_orders
    sales_order_id VARCHAR(50), -- FK to sales_orders
    production_order_id VARCHAR(50), -- FK to production_orders
    work_order_id VARCHAR(50), -- FK to work_orders (MES)
    goods_receipt_id VARCHAR(50), -- FK to goods_receipts
    
    -- Destination (for transfers)
    receiving_plant VARCHAR(50),
    receiving_storage_location VARCHAR(50),
    
    -- Reason
    reason_code VARCHAR(20),
    reason_text TEXT,
    
    -- Status
    cancelled BOOLEAN DEFAULT false,
    reversal_indicator BOOLEAN DEFAULT false,
    
    -- Audit
    created_by VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- SALES ORDERS
-- ============================================================================

CREATE TABLE sales_orders (
    sales_order_id VARCHAR(50) PRIMARY KEY,
    sales_order_number VARCHAR(50) UNIQUE NOT NULL,
    
    -- Customer
    customer_id VARCHAR(50) NOT NULL, -- FK to customers
    
    -- Document Details
    order_date DATE NOT NULL,
    order_type VARCHAR(30), -- standard, rush, export, intercompany
    sales_organization VARCHAR(10),
    distribution_channel VARCHAR(10),
    division VARCHAR(10),
    
    -- Pricing
    currency VARCHAR(3) DEFAULT 'INR',
    total_net_value DECIMAL(15,2),
    tax_amount DECIMAL(15,2),
    freight_charges DECIMAL(15,2),
    total_value DECIMAL(15,2),
    
    -- Payment
    payment_terms VARCHAR(50),
    payment_method VARCHAR(30),
    
    -- Delivery
    delivery_priority VARCHAR(30) DEFAULT 'normal', -- urgent, high, normal, low
    requested_delivery_date DATE,
    confirmed_delivery_date DATE,
    incoterms VARCHAR(20),
    
    -- Shipping
    ship_to_party VARCHAR(50),
    shipping_address_id VARCHAR(50),
    shipping_instructions TEXT,
    
    -- Status
    order_status VARCHAR(30) DEFAULT 'open',
    -- open, in_production, partially_delivered, delivered, invoiced, closed, cancelled
    
    overall_delivery_status VARCHAR(30),
    overall_billing_status VARCHAR(30),
    
    -- Credit Control
    credit_check_status VARCHAR(30),
    credit_limit_used DECIMAL(15,2),
    
    -- References
    customer_po_number VARCHAR(50),
    quotation_number VARCHAR(50),
    contract_number VARCHAR(50),
    
    -- Audit
    created_by VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE sales_order_lines (
    sales_order_line_id VARCHAR(50) PRIMARY KEY,
    sales_order_id VARCHAR(50) NOT NULL, -- FK to sales_orders
    line_number INTEGER NOT NULL,
    
    -- Material
    material_id VARCHAR(50) NOT NULL, -- FK to materials
    product_id VARCHAR(50), -- FK to products
    material_description VARCHAR(200),
    
    -- Quantity
    order_quantity DECIMAL(15,4) NOT NULL,
    unit_of_measure VARCHAR(20) NOT NULL,
    delivered_quantity DECIMAL(15,4) DEFAULT 0,
    invoiced_quantity DECIMAL(15,4) DEFAULT 0,
    
    -- Pricing
    unit_price DECIMAL(12,4) NOT NULL,
    discount_percentage DECIMAL(5,2) DEFAULT 0,
    net_price DECIMAL(15,2),
    tax_code VARCHAR(20),
    tax_amount DECIMAL(15,2),
    
    -- Delivery
    requested_delivery_date DATE,
    confirmed_delivery_date DATE,
    plant_id VARCHAR(50), -- FK to factories
    
    -- Availability
    atp_date DATE, -- Available-to-Promise
    atp_quantity DECIMAL(15,4),
    
    -- Production
    make_to_order BOOLEAN DEFAULT false,
    production_order_id VARCHAR(50), -- FK to production_orders
    
    -- Item Category
    item_category VARCHAR(10), -- TAN (standard), TAD (free of charge), etc.
    
    -- Status
    line_status VARCHAR(30) DEFAULT 'open',
    rejection_reason VARCHAR(100),
    deletion_indicator BOOLEAN DEFAULT false,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- MRP (Material Requirements Planning)
-- ============================================================================

CREATE TABLE mrp_runs (
    mrp_run_id VARCHAR(50) PRIMARY KEY,
    run_number VARCHAR(50) UNIQUE NOT NULL,
    
    -- Planning Details
    planning_date DATE NOT NULL,
    planning_horizon_days INTEGER,
    
    -- Scope
    plant_id VARCHAR(50), -- FK to factories
    mrp_controller VARCHAR(50),
    planning_mode VARCHAR(30), -- regenerative, net_change
    
    -- Processing
    create_purchase_requisitions BOOLEAN DEFAULT true,
    create_production_orders BOOLEAN DEFAULT true,
    reschedule_open_orders BOOLEAN DEFAULT true,
    
    -- Results
    materials_planned INTEGER,
    purchase_reqs_created INTEGER,
    production_orders_created INTEGER,
    
    -- Status
    run_status VARCHAR(30), -- running, completed, error
    
    -- Timing
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    
    created_by VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE mrp_elements (
    element_id VARCHAR(50) PRIMARY KEY,
    mrp_run_id VARCHAR(50) NOT NULL, -- FK to mrp_runs
    
    -- Material
    material_id VARCHAR(50) NOT NULL, -- FK to materials
    plant_id VARCHAR(50) NOT NULL, -- FK to factories
    
    -- Element Details
    element_type VARCHAR(30) NOT NULL,
    -- independent_requirement, dependent_requirement, purchase_requisition,
    -- purchase_order, production_order, stock
    
    element_date DATE NOT NULL,
    
    -- Quantities
    requirement_quantity DECIMAL(15,4),
    receipt_quantity DECIMAL(15,4),
    
    -- Source
    source_document VARCHAR(50),
    source_line INTEGER,
    
    -- MRP Controller
    exception_message VARCHAR(200), -- shortage, excess, reschedule
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- FINANCIAL ACCOUNTING
-- ============================================================================

CREATE TABLE cost_centers (
    cost_center_id VARCHAR(50) PRIMARY KEY,
    cost_center_code VARCHAR(50) UNIQUE NOT NULL,
    cost_center_name VARCHAR(200) NOT NULL,
    
    -- Hierarchy
    controlling_area VARCHAR(10),
    cost_center_group VARCHAR(50),
    parent_cost_center_id VARCHAR(50), -- FK to cost_centers
    
    -- Assignment
    company_code VARCHAR(10),
    business_area VARCHAR(10),
    plant_id VARCHAR(50), -- FK to factories
    
    -- Responsible Person
    responsible_person VARCHAR(50), -- FK to employees
    
    -- Category
    cost_center_category VARCHAR(50), -- production, service, admin
    
    -- Status
    is_active BOOLEAN DEFAULT true,
    valid_from DATE,
    valid_to DATE,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE general_ledger (
    gl_transaction_id VARCHAR(50) PRIMARY KEY,
    document_number VARCHAR(50),
    document_type VARCHAR(10),
    posting_date DATE NOT NULL,
    document_date DATE NOT NULL,
    
    -- Account
    gl_account VARCHAR(20) NOT NULL,
    company_code VARCHAR(10) NOT NULL,
    
    -- Amount
    debit_amount DECIMAL(15,2),
    credit_amount DECIMAL(15,2),
    currency VARCHAR(3) DEFAULT 'INR',
    
    -- Cost Assignment
    cost_center_id VARCHAR(50), -- FK to cost_centers
    profit_center VARCHAR(50),
    
    -- References
    reference_document VARCHAR(50),
    assignment VARCHAR(50),
    text TEXT,
    
    -- Posting Details
    posting_key VARCHAR(2),
    transaction_code VARCHAR(10),
    
    -- Source
    source_system VARCHAR(50), -- ERP, MES, EXTERNAL
    source_document_id VARCHAR(50),
    
    -- Period
    fiscal_year INTEGER,
    fiscal_period INTEGER,
    
    -- Status
    cleared BOOLEAN DEFAULT false,
    clearing_document VARCHAR(50),
    clearing_date DATE,
    
    -- Audit
    created_by VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- QUALITY MANAGEMENT (BASIC)
-- ============================================================================

CREATE TABLE inspection_plans (
    inspection_plan_id VARCHAR(50) PRIMARY KEY,
    plan_number VARCHAR(50) UNIQUE NOT NULL,
    
    -- Material
    material_id VARCHAR(50) NOT NULL, -- FK to materials
    plant_id VARCHAR(50), -- FK to factories
    
    -- Plan Details
    plan_usage VARCHAR(30), -- goods_receipt, production, stock_sampling
    inspection_type VARCHAR(30), -- sample, 100_percent, skip_lot
    
    -- Sampling
    sample_size INTEGER,
    sample_unit VARCHAR(20),
    sampling_procedure VARCHAR(50),
    
    -- Control
    inspection_interval_days INTEGER,
    next_inspection_date DATE,
    
    -- Status
    is_active BOOLEAN DEFAULT true,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE inspection_characteristics (
    characteristic_id VARCHAR(50) PRIMARY KEY,
    inspection_plan_id VARCHAR(50) NOT NULL, -- FK to inspection_plans
    
    -- Characteristic Details
    characteristic_name VARCHAR(200) NOT NULL,
    characteristic_type VARCHAR(30), -- quantitative, qualitative
    
    -- Specification
    target_value DECIMAL(15,4),
    lower_spec_limit DECIMAL(15,4),
    upper_spec_limit DECIMAL(15,4),
    unit_of_measure VARCHAR(20),
    
    -- Inspection
    inspection_method VARCHAR(100),
    measurement_device VARCHAR(100),
    
    -- Sampling
    sample_size INTEGER,
    
    -- Classification
    characteristic_class VARCHAR(20), -- critical, major, minor
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- ERP-MES INTEGRATION TABLES
-- ============================================================================

CREATE TABLE erp_mes_sync_log (
    sync_id VARCHAR(50) PRIMARY KEY,
    sync_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Sync Direction
    sync_direction VARCHAR(10), -- ERP_TO_MES, MES_TO_ERP
    
    -- Document Details
    document_type VARCHAR(50), 
    -- production_order, work_order, material_consumption, production_confirmation
    
    document_id VARCHAR(50),
    
    -- Status
    sync_status VARCHAR(30), -- pending, in_progress, completed, error
    error_message TEXT,
    
    -- Data
    sync_data JSONB,
    
    -- Retries
    retry_count INTEGER DEFAULT 0,
    last_retry_at TIMESTAMP,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- INDICES FOR PERFORMANCE
-- ============================================================================

-- Materials
CREATE INDEX idx_materials_type ON materials(material_type, material_status);
CREATE INDEX idx_materials_procurement ON materials(procurement_type, default_supplier_id);
CREATE INDEX idx_materials_product ON materials(product_id);

-- BOM
CREATE INDEX idx_bom_parent ON bill_of_materials(parent_material_id, bom_status);
CREATE INDEX idx_bom_components_bom ON bom_components(bom_id, item_number);
CREATE INDEX idx_bom_components_material ON bom_components(material_id);

-- Production Orders
CREATE INDEX idx_prod_orders_material ON production_orders(material_id, system_status);
CREATE INDEX idx_prod_orders_dates ON production_orders(basic_start_date, basic_end_date);
CREATE INDEX idx_prod_orders_sales ON production_orders(sales_order_id);
CREATE INDEX idx_prod_orders_work ON production_orders(work_order_id);

-- Purchase Orders
CREATE INDEX idx_po_supplier ON purchase_orders(supplier_id, po_status);
CREATE INDEX idx_po_dates ON purchase_orders(po_date);
CREATE INDEX idx_po_lines_po ON purchase_order_lines(purchase_order_id, line_number);
CREATE INDEX idx_po_lines_material ON purchase_order_lines(material_id);

-- Sales Orders
CREATE INDEX idx_so_customer ON sales_orders(customer_id, order_status);
CREATE INDEX idx_so_dates ON sales_orders(order_date, requested_delivery_date);
CREATE INDEX idx_so_lines_so ON sales_order_lines(sales_order_id, line_number);
CREATE INDEX idx_so_lines_material ON sales_order_lines(material_id);

-- Inventory
CREATE INDEX idx_inv_balance_material ON inventory_balances(material_id, plant_id, storage_location);
CREATE INDEX idx_inv_trans_material ON inventory_transactions(material_id, posting_date);
CREATE INDEX idx_inv_trans_type ON inventory_transactions(transaction_type, posting_date);

-- MRP
CREATE INDEX idx_mrp_elements_material ON mrp_elements(material_id, element_date);
CREATE INDEX idx_mrp_elements_run ON mrp_elements(mrp_run_id);

-- Sync
CREATE INDEX idx_sync_status ON erp_mes_sync_log(sync_status, sync_timestamp);
CREATE INDEX idx_sync_document ON erp_mes_sync_log(document_type, document_id);

-- ============================================================================
-- COMMENTS
-- ============================================================================

COMMENT ON TABLE materials IS 'Material master data - raw materials, components, finished goods';
COMMENT ON TABLE bill_of_materials IS 'Product structures and recipes';
COMMENT ON TABLE bom_components IS 'BOM line items - components that make up parent';
COMMENT ON TABLE production_orders IS 'ERP production orders - sent to MES as work orders';
COMMENT ON TABLE purchase_orders IS 'Supplier purchase orders';
COMMENT ON TABLE sales_orders IS 'Customer sales orders - drive production';
COMMENT ON TABLE inventory_balances IS 'Current stock levels by location';
COMMENT ON TABLE mrp_elements IS 'MRP planning results - demand and supply';
COMMENT ON TABLE erp_mes_sync_log IS 'Integration log between ERP and MES systems';
