-- GenIMS ERP-WMS Inventory Synchronization
-- Real-time bidirectional inventory sync between ERP and WMS

-- ============================================================================
-- INVENTORY SYNC CONFIGURATION
-- ============================================================================

CREATE TABLE inventory_sync_mappings (
    mapping_id VARCHAR(50) PRIMARY KEY,
    
    -- ERP Side
    erp_location_id VARCHAR(50) NOT NULL, -- FK to factories/warehouses
    erp_location_type VARCHAR(30), -- factory, warehouse
    
    -- WMS Side
    wms_warehouse_id VARCHAR(50) NOT NULL, -- FK to warehouses (WMS)
    
    -- Mapping
    is_active BOOLEAN DEFAULT true,
    sync_enabled BOOLEAN DEFAULT true,
    
    -- Sync Frequency
    sync_mode VARCHAR(30) DEFAULT 'real_time',
    -- real_time, batch_hourly, batch_daily
    
    -- Last Sync
    last_sync_timestamp TIMESTAMP,
    last_sync_status VARCHAR(30),
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(erp_location_id, wms_warehouse_id)
);

-- ============================================================================
-- INVENTORY SYNC QUEUE (REAL-TIME)
-- ============================================================================

CREATE TABLE inventory_sync_queue (
    queue_id VARCHAR(50) PRIMARY KEY,
    
    -- Direction
    sync_direction VARCHAR(30) NOT NULL,
    -- ERP_TO_WMS, WMS_TO_ERP
    
    -- Transaction
    transaction_type VARCHAR(50) NOT NULL,
    -- allocation, reservation, movement, adjustment, cycle_count
    
    transaction_id VARCHAR(50) NOT NULL, -- Original transaction ID
    transaction_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Material
    material_id VARCHAR(50) NOT NULL,
    
    -- Quantity
    quantity DECIMAL(15,4) NOT NULL,
    unit_of_measure VARCHAR(20),
    
    -- Locations
    from_location VARCHAR(50),
    to_location VARCHAR(50),
    
    -- WMS Bin Details (if from WMS)
    from_bin_location VARCHAR(50),
    to_bin_location VARCHAR(50),
    
    -- Sync Status
    sync_status VARCHAR(30) DEFAULT 'pending',
    -- pending, in_progress, completed, error, retry
    
    -- Processing
    processed_at TIMESTAMP,
    retry_count INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 3,
    
    -- Error Handling
    error_message TEXT,
    
    -- Acknowledgement
    acknowledged BOOLEAN DEFAULT false,
    acknowledged_at TIMESTAMP,
    
    -- Data Payload
    sync_data JSONB,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- INVENTORY ALLOCATION & RESERVATION
-- ============================================================================

CREATE TABLE inventory_allocations (
    allocation_id VARCHAR(50) PRIMARY KEY,
    
    -- Source Document
    source_type VARCHAR(30) NOT NULL,
    -- sales_order, production_order, transfer_order
    
    source_document_id VARCHAR(50) NOT NULL,
    source_line_number INTEGER,
    
    -- Material
    material_id VARCHAR(50) NOT NULL,
    
    -- Quantity
    allocated_quantity DECIMAL(15,4) NOT NULL,
    unit_of_measure VARCHAR(20),
    
    -- Location (ERP Level)
    location_id VARCHAR(50) NOT NULL, -- FK to factories/warehouses
    
    -- WMS Reservation (if available)
    wms_reservation_id VARCHAR(50), -- FK to WMS reservation
    bin_location VARCHAR(50), -- Specific bin in WMS
    
    -- Status
    allocation_status VARCHAR(30) DEFAULT 'allocated',
    -- allocated, picked, shipped, cancelled
    
    -- Dates
    allocation_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    required_date DATE,
    
    -- Fulfillment
    picked_quantity DECIMAL(15,4) DEFAULT 0,
    shipped_quantity DECIMAL(15,4) DEFAULT 0,
    
    -- Sync Status
    synced_to_wms BOOLEAN DEFAULT false,
    wms_sync_timestamp TIMESTAMP,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- INVENTORY RECONCILIATION
-- ============================================================================

CREATE TABLE inventory_reconciliation_headers (
    reconciliation_id VARCHAR(50) PRIMARY KEY,
    reconciliation_number VARCHAR(50) UNIQUE NOT NULL,
    
    -- Period
    reconciliation_date DATE NOT NULL,
    fiscal_year INTEGER,
    fiscal_period INTEGER,
    
    -- Scope
    location_id VARCHAR(50), -- NULL = all locations
    
    -- Status
    reconciliation_status VARCHAR(30) DEFAULT 'in_progress',
    -- in_progress, completed, adjustments_posted
    
    -- Counts
    total_items_compared INTEGER DEFAULT 0,
    items_matched INTEGER DEFAULT 0,
    items_with_variance INTEGER DEFAULT 0,
    
    -- Totals
    total_variance_value DECIMAL(15,2) DEFAULT 0,
    
    -- Process
    started_by VARCHAR(50),
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    
    notes TEXT
);

CREATE TABLE inventory_reconciliation_lines (
    line_id VARCHAR(50) PRIMARY KEY,
    reconciliation_id VARCHAR(50) NOT NULL, -- FK to inventory_reconciliation_headers
    line_number INTEGER,
    
    -- Material
    material_id VARCHAR(50) NOT NULL,
    
    -- Location
    location_id VARCHAR(50) NOT NULL,
    
    -- ERP Quantities
    erp_quantity DECIMAL(15,4) DEFAULT 0,
    erp_value DECIMAL(15,2) DEFAULT 0,
    
    -- WMS Quantities (aggregated from bins)
    wms_quantity DECIMAL(15,4) DEFAULT 0,
    wms_value DECIMAL(15,2) DEFAULT 0,
    
    -- Variance
    variance_quantity DECIMAL(15,4) DEFAULT 0,
    variance_value DECIMAL(15,2) DEFAULT 0,
    variance_pct DECIMAL(5,2),
    
    -- Bin Details (if available)
    wms_bin_details JSONB, -- Array of {bin, quantity}
    
    -- Variance Reason
    variance_reason VARCHAR(200),
    
    -- Status
    variance_status VARCHAR(30),
    -- matched, minor_variance, major_variance, investigated
    
    -- Resolution
    adjustment_posted BOOLEAN DEFAULT false,
    adjustment_journal_id VARCHAR(50), -- FK to journal_entry_headers
    
    notes TEXT,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- INVENTORY ADJUSTMENT INTEGRATION
-- ============================================================================

CREATE TABLE inventory_adjustments_sync (
    sync_id VARCHAR(50) PRIMARY KEY,
    
    -- Source System
    source_system VARCHAR(10) NOT NULL, -- ERP, WMS
    
    -- Adjustment
    adjustment_type VARCHAR(30),
    -- cycle_count, physical_count, damage, obsolescence, reconciliation
    
    adjustment_document_id VARCHAR(50) NOT NULL,
    adjustment_date DATE NOT NULL,
    
    -- Material & Location
    material_id VARCHAR(50) NOT NULL,
    location_id VARCHAR(50) NOT NULL,
    bin_location VARCHAR(50), -- If from WMS
    
    -- Quantity Change
    quantity_before DECIMAL(15,4),
    quantity_after DECIMAL(15,4),
    adjustment_quantity DECIMAL(15,4) NOT NULL,
    
    -- Value
    value_before DECIMAL(15,2),
    value_after DECIMAL(15,2),
    adjustment_value DECIMAL(15,2),
    
    -- Reason
    adjustment_reason VARCHAR(200),
    
    -- Sync Status
    sync_status VARCHAR(30) DEFAULT 'pending',
    -- pending, completed, error
    
    synced_to_system VARCHAR(10), -- ERP or WMS (opposite of source)
    synced_at TIMESTAMP,
    
    -- Target Transaction ID
    target_transaction_id VARCHAR(50),
    
    error_message TEXT,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- CYCLE COUNT INTEGRATION
-- ============================================================================

CREATE TABLE cycle_count_integration (
    integration_id VARCHAR(50) PRIMARY KEY,
    
    -- WMS Cycle Count
    wms_cycle_count_id VARCHAR(50) NOT NULL,
    
    -- ERP Reconciliation
    erp_reconciliation_id VARCHAR(50), -- FK to inventory_reconciliation_headers
    
    -- Status
    integration_status VARCHAR(30) DEFAULT 'pending',
    -- pending, reconciled, adjustments_posted
    
    -- Summary
    items_counted INTEGER,
    items_with_variance INTEGER,
    total_variance_value DECIMAL(15,2),
    
    -- Processing
    processed_at TIMESTAMP,
    
    notes TEXT,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- REAL-TIME INVENTORY VIEW (CONSOLIDATED)
-- ============================================================================

CREATE TABLE inventory_snapshot (
    snapshot_id VARCHAR(50) PRIMARY KEY,
    
    -- Material & Location
    material_id VARCHAR(50) NOT NULL,
    location_id VARCHAR(50) NOT NULL,
    
    -- ERP Quantities
    erp_on_hand DECIMAL(15,4) DEFAULT 0,
    erp_allocated DECIMAL(15,4) DEFAULT 0,
    erp_available DECIMAL(15,4) DEFAULT 0,
    
    -- WMS Quantities (if sync enabled)
    wms_on_hand DECIMAL(15,4) DEFAULT 0,
    wms_allocated DECIMAL(15,4) DEFAULT 0,
    wms_available DECIMAL(15,4) DEFAULT 0,
    
    -- Variance
    variance_quantity DECIMAL(15,4) DEFAULT 0,
    
    -- Status
    sync_status VARCHAR(30),
    -- synced, variance_minor, variance_major, not_synced
    
    -- Last Update
    last_erp_update TIMESTAMP,
    last_wms_update TIMESTAMP,
    last_sync_timestamp TIMESTAMP,
    
    UNIQUE(material_id, location_id)
);

-- ============================================================================
-- INVENTORY TRANSACTION LOG
-- ============================================================================

CREATE TABLE inventory_transaction_log (
    log_id VARCHAR(50) PRIMARY KEY,
    log_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Transaction
    transaction_type VARCHAR(50) NOT NULL,
    transaction_id VARCHAR(50) NOT NULL,
    
    -- System
    source_system VARCHAR(10) NOT NULL, -- ERP, WMS
    
    -- Material & Location
    material_id VARCHAR(50) NOT NULL,
    location_id VARCHAR(50) NOT NULL,
    bin_location VARCHAR(50), -- If WMS
    
    -- Quantity Change
    quantity_change DECIMAL(15,4) NOT NULL,
    unit_of_measure VARCHAR(20),
    
    -- Balances
    balance_before DECIMAL(15,4),
    balance_after DECIMAL(15,4),
    
    -- Sync
    sync_required BOOLEAN DEFAULT true,
    synced BOOLEAN DEFAULT false,
    sync_timestamp TIMESTAMP,
    
    -- Data
    transaction_data JSONB
);

-- ============================================================================
-- SYNC ERROR LOG
-- ============================================================================

CREATE TABLE inventory_sync_errors (
    error_id VARCHAR(50) PRIMARY KEY,
    error_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Error Details
    error_type VARCHAR(50),
    -- sync_failure, data_mismatch, connection_error, validation_error
    
    error_message TEXT,
    error_details JSONB,
    
    -- Context
    queue_id VARCHAR(50), -- FK to inventory_sync_queue
    material_id VARCHAR(50),
    location_id VARCHAR(50),
    
    -- Resolution
    error_status VARCHAR(30) DEFAULT 'open',
    -- open, investigating, resolved, ignored
    
    resolved_at TIMESTAMP,
    resolved_by VARCHAR(50),
    resolution_notes TEXT,
    
    -- Retry
    retry_attempted BOOLEAN DEFAULT false,
    retry_count INTEGER DEFAULT 0
);

-- ============================================================================
-- SYNC PERFORMANCE METRICS
-- ============================================================================

CREATE TABLE inventory_sync_metrics (
    metric_id VARCHAR(50) PRIMARY KEY,
    metric_date DATE NOT NULL,
    
    -- Volume
    total_sync_transactions INTEGER DEFAULT 0,
    erp_to_wms_transactions INTEGER DEFAULT 0,
    wms_to_erp_transactions INTEGER DEFAULT 0,
    
    -- Success Rate
    successful_syncs INTEGER DEFAULT 0,
    failed_syncs INTEGER DEFAULT 0,
    success_rate_pct DECIMAL(5,2),
    
    -- Performance
    avg_sync_time_seconds DECIMAL(10,2),
    max_sync_time_seconds DECIMAL(10,2),
    
    -- Errors
    total_errors INTEGER DEFAULT 0,
    unresolved_errors INTEGER DEFAULT 0,
    
    -- Reconciliation
    reconciliations_completed INTEGER DEFAULT 0,
    total_variance_value DECIMAL(15,2) DEFAULT 0,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(metric_date)
);

-- ============================================================================
-- INDICES
-- ============================================================================

-- Sync Queue
CREATE INDEX idx_sync_queue_status ON inventory_sync_queue(sync_status, sync_direction);
CREATE INDEX idx_sync_queue_material ON inventory_sync_queue(material_id, created_at);
CREATE INDEX idx_sync_queue_transaction ON inventory_sync_queue(transaction_id, transaction_type);

-- Allocations
CREATE INDEX idx_allocations_source ON inventory_allocations(source_type, source_document_id);
CREATE INDEX idx_allocations_material ON inventory_allocations(material_id, allocation_status);
CREATE INDEX idx_allocations_location ON inventory_allocations(location_id, allocation_status);

-- Reconciliation
CREATE INDEX idx_recon_header_date ON inventory_reconciliation_headers(reconciliation_date);
CREATE INDEX idx_recon_lines_header ON inventory_reconciliation_lines(reconciliation_id);
CREATE INDEX idx_recon_lines_material ON inventory_reconciliation_lines(material_id, location_id);

-- Adjustments
CREATE INDEX idx_adj_sync_source ON inventory_adjustments_sync(source_system, sync_status);
CREATE INDEX idx_adj_sync_material ON inventory_adjustments_sync(material_id, adjustment_date);

-- Snapshot
CREATE INDEX idx_snapshot_material ON inventory_snapshot(material_id);
CREATE INDEX idx_snapshot_location ON inventory_snapshot(location_id);
CREATE INDEX idx_snapshot_status ON inventory_snapshot(sync_status);

-- Transaction Log
CREATE INDEX idx_trans_log_material ON inventory_transaction_log(material_id, log_timestamp);
CREATE INDEX idx_trans_log_sync ON inventory_transaction_log(synced, sync_required);

-- Errors
CREATE INDEX idx_sync_errors_status ON inventory_sync_errors(error_status, error_timestamp);
CREATE INDEX idx_sync_errors_material ON inventory_sync_errors(material_id);

-- ============================================================================
-- COMMENTS
-- ============================================================================

COMMENT ON TABLE inventory_sync_mappings IS 'Configuration for ERP-WMS location mappings';
COMMENT ON TABLE inventory_sync_queue IS 'Real-time queue for inventory transactions to sync';
COMMENT ON TABLE inventory_allocations IS 'ERP allocations with WMS bin reservations';
COMMENT ON TABLE inventory_reconciliation_headers IS 'Periodic reconciliation between ERP and WMS';
COMMENT ON TABLE inventory_reconciliation_lines IS 'Line-level variance analysis';
COMMENT ON TABLE inventory_adjustments_sync IS 'Sync adjustments between systems';
COMMENT ON TABLE cycle_count_integration IS 'WMS cycle count integration with ERP';
COMMENT ON TABLE inventory_snapshot IS 'Real-time consolidated inventory view';
COMMENT ON TABLE inventory_transaction_log IS 'Complete audit trail of all inventory movements';
COMMENT ON TABLE inventory_sync_errors IS 'Sync error tracking and resolution';
COMMENT ON TABLE inventory_sync_metrics IS 'Daily sync performance metrics';
