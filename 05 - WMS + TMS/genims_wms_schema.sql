-- GenIMS WMS (Warehouse Management System) Schema
-- Complete warehouse operations from receiving to shipping

-- ============================================================================
-- WAREHOUSE STRUCTURE
-- ============================================================================

CREATE TABLE warehouses (
    warehouse_id VARCHAR(50) PRIMARY KEY,
    warehouse_code VARCHAR(50) UNIQUE NOT NULL,
    warehouse_name VARCHAR(200) NOT NULL,
    
    -- Location
    plant_id VARCHAR(50), -- FK to factories
    address_line1 VARCHAR(200),
    city VARCHAR(100),
    state VARCHAR(100),
    country VARCHAR(50),
    postal_code VARCHAR(20),
    
    -- Type
    warehouse_type VARCHAR(50), -- distribution_center, manufacturing_warehouse, cross_dock
    
    -- Capacity
    total_area_sqm DECIMAL(12,2),
    storage_capacity_pallets INTEGER,
    dock_doors INTEGER,
    
    -- Operations
    operates_24x7 BOOLEAN DEFAULT false,
    operating_hours VARCHAR(100),
    
    -- Temperature Control
    temperature_controlled BOOLEAN DEFAULT false,
    min_temperature_celsius DECIMAL(5,2),
    max_temperature_celsius DECIMAL(5,2),
    
    -- Status
    is_active BOOLEAN DEFAULT true,
    
    -- Audit
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE warehouse_zones (
    zone_id VARCHAR(50) PRIMARY KEY,
    warehouse_id VARCHAR(50) NOT NULL, -- FK to warehouses
    zone_code VARCHAR(50) NOT NULL,
    zone_name VARCHAR(200) NOT NULL,
    
    -- Zone Type
    zone_type VARCHAR(50), -- receiving, storage, picking, packing, shipping, staging, quarantine
    
    -- Physical
    area_sqm DECIMAL(10,2),
    capacity_pallets INTEGER,
    
    -- Temperature
    temperature_zone VARCHAR(30), -- ambient, refrigerated, frozen
    
    -- Access Control
    restricted_access BOOLEAN DEFAULT false,
    
    -- Status
    is_active BOOLEAN DEFAULT true,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE warehouse_aisles (
    aisle_id VARCHAR(50) PRIMARY KEY,
    zone_id VARCHAR(50) NOT NULL, -- FK to warehouse_zones
    aisle_code VARCHAR(50) NOT NULL,
    
    -- Physical
    aisle_length_m DECIMAL(8,2),
    aisle_width_m DECIMAL(8,2),
    
    -- Configuration
    single_deep BOOLEAN DEFAULT true,
    double_deep BOOLEAN DEFAULT false,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE storage_bins (
    bin_id VARCHAR(50) PRIMARY KEY,
    warehouse_id VARCHAR(50) NOT NULL, -- FK to warehouses
    zone_id VARCHAR(50), -- FK to warehouse_zones
    aisle_id VARCHAR(50), -- FK to warehouse_aisles
    
    -- Location
    bin_code VARCHAR(50) UNIQUE NOT NULL,
    level INTEGER, -- 1=ground, 2=second level, etc.
    position INTEGER, -- Position in aisle
    
    -- Addressing
    full_location VARCHAR(100), -- e.g., "WH01-A01-01-05" (Warehouse-Aisle-Level-Position)
    
    -- Characteristics
    bin_type VARCHAR(50), -- pallet, shelf, floor, bulk
    length_cm DECIMAL(8,2),
    width_cm DECIMAL(8,2),
    height_cm DECIMAL(8,2),
    weight_capacity_kg DECIMAL(10,2),
    
    -- Usage
    dedicated_material_id VARCHAR(50), -- FK to materials (if dedicated)
    mixed_storage BOOLEAN DEFAULT true,
    
    -- ABC Classification
    velocity_class VARCHAR(1), -- A=fast, B=medium, C=slow
    
    -- Constraints
    hazmat_approved BOOLEAN DEFAULT false,
    temperature_controlled BOOLEAN DEFAULT false,
    
    -- Status
    bin_status VARCHAR(30) DEFAULT 'available', -- available, occupied, blocked, damaged
    current_occupancy_pct DECIMAL(5,2) DEFAULT 0,
    
    -- Last Activity
    last_putaway_date TIMESTAMP,
    last_pick_date TIMESTAMP,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- WAREHOUSE INVENTORY (BIN LEVEL)
-- ============================================================================

CREATE TABLE warehouse_inventory (
    inventory_id VARCHAR(50) PRIMARY KEY,
    
    -- Location
    warehouse_id VARCHAR(50) NOT NULL, -- FK to warehouses
    bin_id VARCHAR(50) NOT NULL, -- FK to storage_bins
    
    -- Material
    material_id VARCHAR(50) NOT NULL, -- FK to materials
    batch_number VARCHAR(50),
    serial_number VARCHAR(50),
    
    -- Quantity
    quantity_on_hand DECIMAL(15,4) DEFAULT 0,
    unit_of_measure VARCHAR(20),
    
    -- Quality Status
    stock_status VARCHAR(30) DEFAULT 'available', -- available, quarantine, blocked, reserved
    
    -- Lot Information
    lot_number VARCHAR(50),
    manufacture_date DATE,
    expiry_date DATE,
    retest_date DATE,
    
    -- Handling Unit
    pallet_id VARCHAR(50),
    lpn VARCHAR(50), -- License Plate Number
    
    -- Physical State
    damaged BOOLEAN DEFAULT false,
    
    -- Reservation
    reserved_quantity DECIMAL(15,4) DEFAULT 0,
    available_quantity DECIMAL(15,4) DEFAULT 0, -- on_hand - reserved
    
    -- Last Activity
    last_movement_date TIMESTAMP,
    last_cycle_count_date TIMESTAMP,
    
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- INBOUND OPERATIONS
-- ============================================================================

CREATE TABLE receiving_tasks (
    receiving_task_id VARCHAR(50) PRIMARY KEY,
    task_number VARCHAR(50) UNIQUE NOT NULL,
    
    -- Source Document
    purchase_order_id VARCHAR(50), -- FK to purchase_orders
    po_line_id VARCHAR(50), -- FK to purchase_order_lines
    goods_receipt_id VARCHAR(50), -- FK to goods_receipts
    
    -- Warehouse
    warehouse_id VARCHAR(50) NOT NULL, -- FK to warehouses
    receiving_dock VARCHAR(50),
    
    -- Material
    material_id VARCHAR(50) NOT NULL, -- FK to materials
    expected_quantity DECIMAL(15,4),
    received_quantity DECIMAL(15,4) DEFAULT 0,
    unit_of_measure VARCHAR(20),
    
    -- Batch/Lot
    batch_number VARCHAR(50),
    supplier_lot_number VARCHAR(50),
    
    -- Inspection
    quality_inspection_required BOOLEAN DEFAULT false,
    inspection_status VARCHAR(30), -- pending, passed, failed, waived
    
    -- Task Status
    task_status VARCHAR(30) DEFAULT 'pending', 
    -- pending, in_progress, completed, cancelled
    
    -- Assignment
    assigned_to VARCHAR(50), -- FK to warehouse_workers
    
    -- Timing
    scheduled_date TIMESTAMP,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    
    -- Notes
    notes TEXT,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE putaway_tasks (
    putaway_task_id VARCHAR(50) PRIMARY KEY,
    task_number VARCHAR(50) UNIQUE NOT NULL,
    
    -- Source
    receiving_task_id VARCHAR(50), -- FK to receiving_tasks
    
    -- Material
    material_id VARCHAR(50) NOT NULL, -- FK to materials
    quantity DECIMAL(15,4),
    unit_of_measure VARCHAR(20),
    batch_number VARCHAR(50),
    lpn VARCHAR(50),
    
    -- Location
    warehouse_id VARCHAR(50) NOT NULL, -- FK to warehouses
    from_location VARCHAR(50), -- Staging location
    to_bin_id VARCHAR(50), -- FK to storage_bins (destination)
    
    -- Strategy
    putaway_strategy VARCHAR(50), -- fixed_bin, nearest_empty, abc_slotting, fifo
    
    -- Task Status
    task_status VARCHAR(30) DEFAULT 'pending',
    -- pending, assigned, in_progress, completed, cancelled
    
    -- Assignment
    assigned_to VARCHAR(50), -- FK to warehouse_workers
    
    -- Priority
    priority INTEGER DEFAULT 5,
    
    -- Timing
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    assigned_at TIMESTAMP,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    
    -- Equipment
    equipment_used VARCHAR(50), -- forklift, pallet_jack, manual
    
    notes TEXT
);

-- ============================================================================
-- OUTBOUND OPERATIONS - WAVE MANAGEMENT
-- ============================================================================

CREATE TABLE pick_waves (
    wave_id VARCHAR(50) PRIMARY KEY,
    wave_number VARCHAR(50) UNIQUE NOT NULL,
    
    -- Warehouse
    warehouse_id VARCHAR(50) NOT NULL, -- FK to warehouses
    
    -- Wave Type
    wave_type VARCHAR(50), -- batch, discrete, zone, cluster
    
    -- Planning
    planned_pick_date DATE,
    planned_ship_date DATE,
    
    -- Priority
    priority VARCHAR(30) DEFAULT 'normal', -- urgent, high, normal, low
    
    -- Status
    wave_status VARCHAR(30) DEFAULT 'created',
    -- created, released, picking, picked, packing, packed, shipped, completed
    
    -- Metrics
    total_orders INTEGER DEFAULT 0,
    total_lines INTEGER DEFAULT 0,
    total_units DECIMAL(15,4) DEFAULT 0,
    
    picked_orders INTEGER DEFAULT 0,
    picked_lines INTEGER DEFAULT 0,
    picked_units DECIMAL(15,4) DEFAULT 0,
    
    -- Timing
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    released_at TIMESTAMP,
    completed_at TIMESTAMP,
    
    -- User
    created_by VARCHAR(50),
    released_by VARCHAR(50)
);

CREATE TABLE wave_lines (
    wave_line_id VARCHAR(50) PRIMARY KEY,
    wave_id VARCHAR(50) NOT NULL, -- FK to pick_waves
    line_number INTEGER,
    
    -- Source Order
    sales_order_id VARCHAR(50), -- FK to sales_orders
    sales_order_line_id VARCHAR(50), -- FK to sales_order_lines
    
    -- Material
    material_id VARCHAR(50) NOT NULL, -- FK to materials
    ordered_quantity DECIMAL(15,4),
    allocated_quantity DECIMAL(15,4) DEFAULT 0,
    picked_quantity DECIMAL(15,4) DEFAULT 0,
    unit_of_measure VARCHAR(20),
    
    -- Status
    line_status VARCHAR(30) DEFAULT 'pending',
    -- pending, allocated, picking, picked, short, cancelled
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE picking_tasks (
    picking_task_id VARCHAR(50) PRIMARY KEY,
    task_number VARCHAR(50) UNIQUE NOT NULL,
    
    -- Wave
    wave_id VARCHAR(50), -- FK to pick_waves
    wave_line_id VARCHAR(50), -- FK to wave_lines
    
    -- Order Reference
    sales_order_id VARCHAR(50), -- FK to sales_orders
    
    -- Material
    material_id VARCHAR(50) NOT NULL, -- FK to materials
    quantity_to_pick DECIMAL(15,4),
    quantity_picked DECIMAL(15,4) DEFAULT 0,
    unit_of_measure VARCHAR(20),
    
    -- Location
    warehouse_id VARCHAR(50) NOT NULL, -- FK to warehouses
    pick_from_bin_id VARCHAR(50), -- FK to storage_bins
    pick_from_location VARCHAR(100),
    stage_to_location VARCHAR(100),
    
    -- Batch/Serial
    batch_number VARCHAR(50),
    serial_numbers TEXT, -- JSON array for multiple serials
    
    -- Task Details
    task_type VARCHAR(30), -- single_order, batch, zone, wave
    pick_sequence INTEGER, -- Order in which to pick
    
    -- Status
    task_status VARCHAR(30) DEFAULT 'pending',
    -- pending, assigned, in_progress, picked, short, cancelled
    
    -- Assignment
    assigned_to VARCHAR(50), -- FK to warehouse_workers
    
    -- Timing
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    assigned_at TIMESTAMP,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    
    -- Verification
    requires_verification BOOLEAN DEFAULT false,
    verified_by VARCHAR(50),
    verified_at TIMESTAMP,
    
    notes TEXT
);

CREATE TABLE packing_tasks (
    packing_task_id VARCHAR(50) PRIMARY KEY,
    task_number VARCHAR(50) UNIQUE NOT NULL,
    
    -- Order
    sales_order_id VARCHAR(50) NOT NULL, -- FK to sales_orders
    wave_id VARCHAR(50), -- FK to pick_waves
    
    -- Packing Station
    warehouse_id VARCHAR(50) NOT NULL, -- FK to warehouses
    packing_station VARCHAR(50),
    
    -- Package Information
    package_type VARCHAR(50), -- box, pallet, crate, envelope
    package_weight_kg DECIMAL(10,2),
    package_length_cm DECIMAL(8,2),
    package_width_cm DECIMAL(8,2),
    package_height_cm DECIMAL(8,2),
    
    -- Tracking
    tracking_number VARCHAR(100),
    shipment_id VARCHAR(50), -- FK to shipments
    
    -- Status
    task_status VARCHAR(30) DEFAULT 'pending',
    -- pending, in_progress, packed, labeled, shipped
    
    -- Assignment
    assigned_to VARCHAR(50), -- FK to warehouse_workers
    
    -- Timing
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    
    -- Packing Materials
    box_id VARCHAR(50),
    packing_materials TEXT, -- JSON: bubble wrap, foam, etc.
    
    notes TEXT
);

CREATE TABLE shipping_tasks (
    shipping_task_id VARCHAR(50) PRIMARY KEY,
    task_number VARCHAR(50) UNIQUE NOT NULL,
    
    -- Order
    sales_order_id VARCHAR(50) NOT NULL, -- FK to sales_orders
    
    -- Warehouse
    warehouse_id VARCHAR(50) NOT NULL, -- FK to warehouses
    shipping_dock VARCHAR(50),
    
    -- Shipment
    shipment_id VARCHAR(50), -- FK to shipments (TMS)
    carrier_id VARCHAR(50), -- FK to carriers (TMS)
    carrier_service VARCHAR(50),
    
    -- Packages
    number_of_packages INTEGER,
    total_weight_kg DECIMAL(10,2),
    total_volume_m3 DECIMAL(10,4),
    
    -- Status
    task_status VARCHAR(30) DEFAULT 'pending',
    -- pending, staged, loading, loaded, shipped
    
    -- Timing
    scheduled_ship_date DATE,
    actual_ship_date DATE,
    scheduled_ship_time TIME,
    actual_ship_time TIME,
    
    -- Assignment
    assigned_to VARCHAR(50), -- FK to warehouse_workers
    
    -- BOL (Bill of Lading)
    bol_number VARCHAR(100),
    bol_generated BOOLEAN DEFAULT false,
    
    -- Carrier Pickup
    carrier_pickup_confirmed BOOLEAN DEFAULT false,
    carrier_pickup_time TIMESTAMP,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    
    notes TEXT
);

-- ============================================================================
-- CYCLE COUNTING
-- ============================================================================

CREATE TABLE cycle_count_tasks (
    cycle_count_id VARCHAR(50) PRIMARY KEY,
    task_number VARCHAR(50) UNIQUE NOT NULL,
    
    -- Location
    warehouse_id VARCHAR(50) NOT NULL, -- FK to warehouses
    bin_id VARCHAR(50), -- FK to storage_bins (NULL for full warehouse count)
    
    -- Count Type
    count_type VARCHAR(30), -- full, abc, spot, physical_inventory
    
    -- Material
    material_id VARCHAR(50), -- FK to materials (NULL for bin count)
    
    -- Expected vs Actual
    expected_quantity DECIMAL(15,4),
    counted_quantity DECIMAL(15,4),
    variance_quantity DECIMAL(15,4),
    variance_percentage DECIMAL(5,2),
    
    -- Status
    task_status VARCHAR(30) DEFAULT 'pending',
    -- pending, assigned, counting, completed, variance_approved
    
    -- Assignment
    assigned_to VARCHAR(50), -- FK to warehouse_workers
    
    -- Timing
    scheduled_date DATE,
    count_date DATE,
    count_time TIMESTAMP,
    
    -- Recount
    recount_required BOOLEAN DEFAULT false,
    recount_threshold_pct DECIMAL(5,2) DEFAULT 5.0,
    
    -- Approval (for variances)
    variance_approved BOOLEAN DEFAULT false,
    approved_by VARCHAR(50),
    approved_at TIMESTAMP,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    notes TEXT
);

-- ============================================================================
-- WAREHOUSE EQUIPMENT & LABOR
-- ============================================================================

CREATE TABLE warehouse_equipment (
    equipment_id VARCHAR(50) PRIMARY KEY,
    equipment_code VARCHAR(50) UNIQUE NOT NULL,
    equipment_name VARCHAR(200),
    
    -- Type
    equipment_type VARCHAR(50), -- forklift, pallet_jack, reach_truck, order_picker, AGV
    
    -- Location
    warehouse_id VARCHAR(50) NOT NULL, -- FK to warehouses
    
    -- Specifications
    capacity_kg DECIMAL(10,2),
    max_lift_height_m DECIMAL(5,2),
    
    -- Status
    equipment_status VARCHAR(30) DEFAULT 'available',
    -- available, in_use, maintenance, out_of_service
    
    -- Current Assignment
    assigned_to VARCHAR(50), -- FK to warehouse_workers
    
    -- Maintenance
    last_maintenance_date DATE,
    next_maintenance_date DATE,
    maintenance_hours INTEGER,
    
    -- Usage
    total_hours DECIMAL(10,2) DEFAULT 0,
    
    is_active BOOLEAN DEFAULT true,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE warehouse_workers (
    worker_id VARCHAR(50) PRIMARY KEY,
    worker_code VARCHAR(50) UNIQUE NOT NULL,
    
    -- Personal
    employee_id VARCHAR(50), -- FK to employees
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    
    -- Assignment
    warehouse_id VARCHAR(50) NOT NULL, -- FK to warehouses
    primary_zone_id VARCHAR(50), -- FK to warehouse_zones
    
    -- Role
    worker_role VARCHAR(50), -- receiver, picker, packer, shipper, supervisor, forklift_operator
    
    -- Certifications
    forklift_certified BOOLEAN DEFAULT false,
    hazmat_certified BOOLEAN DEFAULT false,
    
    -- Performance
    pick_rate_units_per_hour DECIMAL(8,2),
    accuracy_percentage DECIMAL(5,2),
    
    -- Shift
    current_shift VARCHAR(20), -- day, evening, night
    
    -- Status
    worker_status VARCHAR(30) DEFAULT 'available',
    -- available, busy, on_break, off_shift, absent
    
    -- Current Activity
    current_task_id VARCHAR(50),
    current_task_type VARCHAR(50),
    
    is_active BOOLEAN DEFAULT true,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- WAREHOUSE MOVEMENTS LOG
-- ============================================================================

CREATE TABLE warehouse_movements (
    movement_id VARCHAR(50) PRIMARY KEY,
    movement_number VARCHAR(50) UNIQUE NOT NULL,
    
    -- Material
    material_id VARCHAR(50) NOT NULL, -- FK to materials
    quantity DECIMAL(15,4),
    unit_of_measure VARCHAR(20),
    batch_number VARCHAR(50),
    lpn VARCHAR(50),
    
    -- Movement Type
    movement_type VARCHAR(50),
    -- receiving, putaway, pick, replenishment, transfer, cycle_count_adjustment, shipment
    
    -- Location
    warehouse_id VARCHAR(50) NOT NULL, -- FK to warehouses
    from_bin_id VARCHAR(50), -- FK to storage_bins
    to_bin_id VARCHAR(50), -- FK to storage_bins
    
    -- Reference
    reference_document_type VARCHAR(50), -- receiving_task, picking_task, etc.
    reference_document_id VARCHAR(50),
    
    -- User
    performed_by VARCHAR(50), -- FK to warehouse_workers
    
    -- Timing
    movement_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Equipment
    equipment_used VARCHAR(50), -- FK to warehouse_equipment
    
    notes TEXT
);

-- ============================================================================
-- SLOTTING & OPTIMIZATION
-- ============================================================================

CREATE TABLE slotting_rules (
    rule_id VARCHAR(50) PRIMARY KEY,
    rule_name VARCHAR(200) NOT NULL,
    
    -- Warehouse
    warehouse_id VARCHAR(50) NOT NULL, -- FK to warehouses
    
    -- Material Criteria
    material_type VARCHAR(50),
    velocity_class VARCHAR(1), -- A, B, C
    product_family VARCHAR(50),
    
    -- Location Criteria
    zone_type VARCHAR(50),
    zone_id VARCHAR(50), -- FK to warehouse_zones
    
    -- Strategy
    strategy_type VARCHAR(50), -- abc_slotting, fifo, dedicated, random
    
    -- Priority
    priority INTEGER DEFAULT 5,
    
    is_active BOOLEAN DEFAULT true,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- INDICES FOR PERFORMANCE
-- ============================================================================

-- Warehouses & Structure
CREATE INDEX idx_zones_warehouse ON warehouse_zones(warehouse_id);
CREATE INDEX idx_aisles_zone ON warehouse_aisles(zone_id);
CREATE INDEX idx_bins_warehouse ON storage_bins(warehouse_id, bin_status);
CREATE INDEX idx_bins_location ON storage_bins(zone_id, aisle_id);

-- Inventory
CREATE INDEX idx_wh_inv_warehouse ON warehouse_inventory(warehouse_id, material_id);
CREATE INDEX idx_wh_inv_bin ON warehouse_inventory(bin_id, stock_status);
CREATE INDEX idx_wh_inv_material ON warehouse_inventory(material_id, stock_status);

-- Inbound
CREATE INDEX idx_receiving_warehouse ON receiving_tasks(warehouse_id, task_status);
CREATE INDEX idx_receiving_po ON receiving_tasks(purchase_order_id);
CREATE INDEX idx_putaway_warehouse ON putaway_tasks(warehouse_id, task_status);

-- Outbound
CREATE INDEX idx_waves_warehouse ON pick_waves(warehouse_id, wave_status);
CREATE INDEX idx_wave_lines_wave ON wave_lines(wave_id);
CREATE INDEX idx_picking_wave ON picking_tasks(wave_id, task_status);
CREATE INDEX idx_picking_warehouse ON picking_tasks(warehouse_id, task_status);
CREATE INDEX idx_packing_warehouse ON packing_tasks(warehouse_id, task_status);
CREATE INDEX idx_shipping_warehouse ON shipping_tasks(warehouse_id, task_status);

-- Cycle Counting
CREATE INDEX idx_cycle_count_warehouse ON cycle_count_tasks(warehouse_id, task_status);
CREATE INDEX idx_cycle_count_bin ON cycle_count_tasks(bin_id);

-- Labor & Equipment
CREATE INDEX idx_workers_warehouse ON warehouse_workers(warehouse_id, worker_status);
CREATE INDEX idx_equipment_warehouse ON warehouse_equipment(warehouse_id, equipment_status);

-- Movements
CREATE INDEX idx_movements_warehouse ON warehouse_movements(warehouse_id, movement_timestamp);
CREATE INDEX idx_movements_material ON warehouse_movements(material_id, movement_timestamp);

-- ============================================================================
-- COMMENTS
-- ============================================================================

COMMENT ON TABLE warehouses IS 'Warehouse master data - distribution centers, manufacturing warehouses';
COMMENT ON TABLE storage_bins IS 'Bin-level storage locations with addressing (Aisle-Level-Position)';
COMMENT ON TABLE warehouse_inventory IS 'Bin-level inventory tracking';
COMMENT ON TABLE receiving_tasks IS 'Inbound receiving from purchase orders';
COMMENT ON TABLE putaway_tasks IS 'Material putaway to storage bins';
COMMENT ON TABLE pick_waves IS 'Wave management for batch picking';
COMMENT ON TABLE picking_tasks IS 'Individual pick tasks with bin locations';
COMMENT ON TABLE packing_tasks IS 'Order packing operations';
COMMENT ON TABLE shipping_tasks IS 'Outbound shipping to carriers';
COMMENT ON TABLE cycle_count_tasks IS 'Physical inventory cycle counting';
COMMENT ON TABLE warehouse_movements IS 'Complete audit trail of material movements';
