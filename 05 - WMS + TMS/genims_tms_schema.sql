-- GenIMS TMS (Transportation Management System) Schema
-- Complete logistics from warehouse to customer delivery

-- ============================================================================
-- CARRIERS & SERVICES
-- ============================================================================

CREATE TABLE carriers (
    carrier_id VARCHAR(50) PRIMARY KEY,
    carrier_code VARCHAR(50) UNIQUE NOT NULL,
    carrier_name VARCHAR(200) NOT NULL,
    
    -- Contact
    contact_person VARCHAR(100),
    email VARCHAR(100),
    phone VARCHAR(50),
    website VARCHAR(200),
    
    -- Address
    address_line1 VARCHAR(200),
    city VARCHAR(100),
    state VARCHAR(100),
    country VARCHAR(50),
    postal_code VARCHAR(20),
    
    -- Business Details
    tax_id VARCHAR(50),
    
    -- Carrier Type
    carrier_type VARCHAR(50), -- courier, ltl, ftl, parcel, air_freight, ocean_freight, 3pl
    
    -- Integration
    api_integration BOOLEAN DEFAULT false,
    tracking_url_template VARCHAR(500),
    
    -- Performance Metrics
    on_time_delivery_pct DECIMAL(5,2),
    damage_rate_pct DECIMAL(5,2),
    total_shipments INTEGER DEFAULT 0,
    total_freight_spend DECIMAL(15,2) DEFAULT 0,
    
    -- Insurance
    cargo_insurance_available BOOLEAN DEFAULT false,
    max_insurance_value DECIMAL(15,2),
    
    -- Status
    carrier_status VARCHAR(30) DEFAULT 'active', -- active, inactive, blacklisted
    approved_for_shipments BOOLEAN DEFAULT true,
    
    -- Rating
    carrier_rating DECIMAL(3,2), -- 1.0 to 5.0
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE carrier_services (
    service_id VARCHAR(50) PRIMARY KEY,
    carrier_id VARCHAR(50) NOT NULL, -- FK to carriers
    service_code VARCHAR(50) NOT NULL,
    service_name VARCHAR(200) NOT NULL,
    
    -- Service Type
    service_type VARCHAR(50), -- standard, express, overnight, same_day, economy
    
    -- Transit Time
    transit_days_min INTEGER,
    transit_days_max INTEGER,
    
    -- Capabilities
    signature_required BOOLEAN DEFAULT false,
    saturday_delivery BOOLEAN DEFAULT false,
    sunday_delivery BOOLEAN DEFAULT false,
    hazmat_capable BOOLEAN DEFAULT false,
    temperature_controlled BOOLEAN DEFAULT false,
    
    -- Weight/Size Limits
    max_weight_kg DECIMAL(10,2),
    max_length_cm DECIMAL(8,2),
    max_width_cm DECIMAL(8,2),
    max_height_cm DECIMAL(8,2),
    
    -- Coverage
    domestic BOOLEAN DEFAULT true,
    international BOOLEAN DEFAULT false,
    
    -- Status
    is_active BOOLEAN DEFAULT true,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE carrier_rates (
    rate_id VARCHAR(50) PRIMARY KEY,
    carrier_id VARCHAR(50) NOT NULL, -- FK to carriers
    service_id VARCHAR(50) NOT NULL, -- FK to carrier_services
    
    -- Geographic
    origin_country VARCHAR(50),
    origin_state VARCHAR(100),
    origin_postal_code VARCHAR(20),
    destination_country VARCHAR(50),
    destination_state VARCHAR(100),
    destination_postal_code VARCHAR(20),
    zone VARCHAR(20),
    
    -- Weight Tiers
    min_weight_kg DECIMAL(10,2),
    max_weight_kg DECIMAL(10,2),
    
    -- Pricing
    base_rate DECIMAL(12,4),
    per_kg_rate DECIMAL(12,4),
    fuel_surcharge_pct DECIMAL(5,2),
    currency VARCHAR(3) DEFAULT 'INR',
    
    -- Accessorials
    residential_delivery_charge DECIMAL(10,2),
    signature_charge DECIMAL(10,2),
    insurance_rate_pct DECIMAL(5,2),
    
    -- Validity
    effective_date DATE NOT NULL,
    expiry_date DATE,
    
    is_active BOOLEAN DEFAULT true,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- SHIPMENTS
-- ============================================================================

CREATE TABLE shipments (
    shipment_id VARCHAR(50) PRIMARY KEY,
    shipment_number VARCHAR(50) UNIQUE NOT NULL,
    
    -- References
    sales_order_id VARCHAR(50), -- FK to sales_orders
    shipping_task_id VARCHAR(50), -- FK to shipping_tasks (WMS)
    warehouse_id VARCHAR(50), -- FK to warehouses
    
    -- Carrier
    carrier_id VARCHAR(50) NOT NULL, -- FK to carriers
    service_id VARCHAR(50), -- FK to carrier_services
    carrier_service_name VARCHAR(200),
    
    -- Tracking
    tracking_number VARCHAR(100),
    master_tracking_number VARCHAR(100), -- For consolidated shipments
    bol_number VARCHAR(100), -- Bill of Lading
    pro_number VARCHAR(100), -- Progressive/Professional Number (LTL)
    
    -- Origin
    origin_warehouse_id VARCHAR(50), -- FK to warehouses
    origin_name VARCHAR(200),
    origin_address_line1 VARCHAR(200),
    origin_city VARCHAR(100),
    origin_state VARCHAR(100),
    origin_country VARCHAR(50),
    origin_postal_code VARCHAR(20),
    
    -- Destination
    customer_id VARCHAR(50), -- FK to customers
    destination_name VARCHAR(200),
    destination_contact VARCHAR(100),
    destination_phone VARCHAR(50),
    destination_email VARCHAR(100),
    destination_address_line1 VARCHAR(200),
    destination_address_line2 VARCHAR(200),
    destination_city VARCHAR(100),
    destination_state VARCHAR(100),
    destination_country VARCHAR(50),
    destination_postal_code VARCHAR(20),
    
    -- Shipment Details
    shipment_type VARCHAR(50), -- parcel, ltl, ftl, intermodal
    incoterms VARCHAR(20), -- FOB, CIF, DDP, etc.
    
    -- Packages
    number_of_packages INTEGER,
    total_weight_kg DECIMAL(10,2),
    total_volume_m3 DECIMAL(10,4),
    declared_value DECIMAL(15,2),
    
    -- Special Handling
    signature_required BOOLEAN DEFAULT false,
    insurance_required BOOLEAN DEFAULT false,
    insurance_value DECIMAL(15,2),
    temperature_controlled BOOLEAN DEFAULT false,
    hazmat BOOLEAN DEFAULT false,
    fragile BOOLEAN DEFAULT false,
    
    -- Timing
    ship_date DATE,
    scheduled_pickup_date DATE,
    actual_pickup_date DATE,
    estimated_delivery_date DATE,
    actual_delivery_date DATE,
    transit_days INTEGER,
    
    -- Status
    shipment_status VARCHAR(30) DEFAULT 'created',
    -- created, booked, picked_up, in_transit, out_for_delivery, delivered, 
    -- delayed, exception, cancelled, returned
    
    -- Costs
    freight_cost DECIMAL(15,2),
    fuel_surcharge DECIMAL(15,2),
    accessorial_charges DECIMAL(15,2),
    insurance_cost DECIMAL(15,2),
    total_cost DECIMAL(15,2),
    currency VARCHAR(3) DEFAULT 'INR',
    
    -- Invoice
    freight_invoice_id VARCHAR(50), -- FK to freight_invoices
    invoiced BOOLEAN DEFAULT false,
    invoice_approved BOOLEAN DEFAULT false,
    
    -- Delivery
    delivered_to_name VARCHAR(200),
    delivery_signature VARCHAR(200),
    delivery_notes TEXT,
    
    -- Documents
    bol_document_url VARCHAR(500),
    pod_document_url VARCHAR(500), -- Proof of Delivery
    
    -- Audit
    created_by VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE shipment_lines (
    shipment_line_id VARCHAR(50) PRIMARY KEY,
    shipment_id VARCHAR(50) NOT NULL, -- FK to shipments
    line_number INTEGER,
    
    -- Order Reference
    sales_order_id VARCHAR(50), -- FK to sales_orders
    sales_order_line_id VARCHAR(50), -- FK to sales_order_lines
    
    -- Material
    material_id VARCHAR(50) NOT NULL, -- FK to materials
    material_description VARCHAR(200),
    quantity DECIMAL(15,4),
    unit_of_measure VARCHAR(20),
    
    -- Package
    package_number INTEGER,
    
    -- Serial/Batch
    serial_numbers TEXT, -- JSON array
    batch_numbers TEXT, -- JSON array
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE shipment_packages (
    package_id VARCHAR(50) PRIMARY KEY,
    shipment_id VARCHAR(50) NOT NULL, -- FK to shipments
    package_number INTEGER,
    
    -- Tracking
    tracking_number VARCHAR(100),
    
    -- Dimensions
    package_type VARCHAR(50), -- box, pallet, crate, envelope, drum
    weight_kg DECIMAL(10,2),
    length_cm DECIMAL(8,2),
    width_cm DECIMAL(8,2),
    height_cm DECIMAL(8,2),
    volume_m3 DECIMAL(10,4),
    
    -- Contents
    description TEXT,
    declared_value DECIMAL(15,2),
    
    -- Status
    package_status VARCHAR(30), -- in_transit, delivered, damaged, lost
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- TRACKING & EVENTS
-- ============================================================================

CREATE TABLE tracking_events (
    event_id VARCHAR(50) PRIMARY KEY,
    shipment_id VARCHAR(50) NOT NULL, -- FK to shipments
    tracking_number VARCHAR(100),
    
    -- Event Details
    event_type VARCHAR(50),
    -- picked_up, departed_facility, in_transit, out_for_delivery, delivered,
    -- delivery_attempted, exception, delayed, damaged, lost, returned
    
    event_code VARCHAR(20),
    event_description TEXT,
    
    -- Location
    location_city VARCHAR(100),
    location_state VARCHAR(100),
    location_country VARCHAR(50),
    facility_name VARCHAR(200),
    
    -- Timing
    event_timestamp TIMESTAMP NOT NULL,
    
    -- Additional Info
    signed_by VARCHAR(200),
    exception_reason TEXT,
    
    -- Source
    data_source VARCHAR(50), -- carrier_api, manual_entry, edi
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- ROUTES & OPTIMIZATION
-- ============================================================================

CREATE TABLE routes (
    route_id VARCHAR(50) PRIMARY KEY,
    route_number VARCHAR(50) UNIQUE NOT NULL,
    
    -- Planning
    route_date DATE NOT NULL,
    planned_start_time TIME,
    planned_end_time TIME,
    actual_start_time TIME,
    actual_end_time TIME,
    
    -- Vehicle/Carrier
    carrier_id VARCHAR(50), -- FK to carriers
    vehicle_id VARCHAR(50), -- If using own fleet
    driver_id VARCHAR(50), -- FK to employees
    
    -- Route Details
    origin_warehouse_id VARCHAR(50), -- FK to warehouses
    route_type VARCHAR(50), -- delivery, pickup, milk_run
    
    -- Optimization
    optimization_type VARCHAR(50), -- time_optimized, distance_optimized, cost_optimized
    total_distance_km DECIMAL(10,2),
    total_duration_minutes INTEGER,
    
    -- Stops
    number_of_stops INTEGER,
    completed_stops INTEGER DEFAULT 0,
    
    -- Capacity
    total_weight_kg DECIMAL(10,2),
    total_volume_m3 DECIMAL(10,4),
    vehicle_capacity_kg DECIMAL(10,2),
    vehicle_capacity_m3 DECIMAL(10,4),
    
    -- Status
    route_status VARCHAR(30) DEFAULT 'planned',
    -- planned, dispatched, in_progress, completed, cancelled
    
    -- Costs
    estimated_cost DECIMAL(15,2),
    actual_cost DECIMAL(15,2),
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE route_stops (
    stop_id VARCHAR(50) PRIMARY KEY,
    route_id VARCHAR(50) NOT NULL, -- FK to routes
    stop_sequence INTEGER NOT NULL,
    
    -- Type
    stop_type VARCHAR(30), -- pickup, delivery
    
    -- Reference
    shipment_id VARCHAR(50), -- FK to shipments
    sales_order_id VARCHAR(50), -- FK to sales_orders
    
    -- Location
    stop_name VARCHAR(200),
    address_line1 VARCHAR(200),
    address_line2 VARCHAR(200),
    city VARCHAR(100),
    state VARCHAR(100),
    postal_code VARCHAR(20),
    latitude DECIMAL(10,7),
    longitude DECIMAL(10,7),
    
    -- Contact
    contact_name VARCHAR(100),
    contact_phone VARCHAR(50),
    
    -- Timing
    planned_arrival_time TIME,
    planned_departure_time TIME,
    actual_arrival_time TIME,
    actual_departure_time TIME,
    service_time_minutes INTEGER, -- Time to load/unload
    
    -- Delivery
    packages_to_deliver INTEGER,
    packages_delivered INTEGER,
    weight_kg DECIMAL(10,2),
    
    -- Status
    stop_status VARCHAR(30) DEFAULT 'pending',
    -- pending, en_route, arrived, completed, failed, skipped
    
    -- Proof of Delivery
    signature VARCHAR(200),
    delivered_to VARCHAR(200),
    photo_url VARCHAR(500),
    notes TEXT,
    
    -- Geofence
    geofence_radius_m INTEGER DEFAULT 100,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- DELIVERIES & PROOF OF DELIVERY
-- ============================================================================

CREATE TABLE deliveries (
    delivery_id VARCHAR(50) PRIMARY KEY,
    delivery_number VARCHAR(50) UNIQUE NOT NULL,
    
    -- References
    shipment_id VARCHAR(50) NOT NULL, -- FK to shipments
    route_stop_id VARCHAR(50), -- FK to route_stops
    sales_order_id VARCHAR(50), -- FK to sales_orders
    
    -- Customer
    customer_id VARCHAR(50), -- FK to customers
    delivery_contact VARCHAR(100),
    
    -- Delivery Address
    delivery_address_line1 VARCHAR(200),
    delivery_address_line2 VARCHAR(200),
    delivery_city VARCHAR(100),
    delivery_state VARCHAR(100),
    delivery_postal_code VARCHAR(20),
    
    -- Timing
    scheduled_delivery_date DATE,
    scheduled_time_window_start TIME,
    scheduled_time_window_end TIME,
    actual_delivery_date DATE,
    actual_delivery_time TIME,
    
    -- Delivery Details
    delivery_type VARCHAR(50), -- attended, unattended, signature_required
    
    -- Status
    delivery_status VARCHAR(30) DEFAULT 'scheduled',
    -- scheduled, dispatched, out_for_delivery, delivered, failed, rescheduled
    
    delivery_attempt_count INTEGER DEFAULT 0,
    
    -- Failure Reason
    failure_reason VARCHAR(200),
    rescheduled_date DATE,
    
    -- Success
    delivered_to_name VARCHAR(200),
    relationship_to_recipient VARCHAR(50), -- self, family, neighbor, receptionist
    
    -- Special Instructions
    delivery_instructions TEXT,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE proof_of_delivery (
    pod_id VARCHAR(50) PRIMARY KEY,
    delivery_id VARCHAR(50) NOT NULL, -- FK to deliveries
    shipment_id VARCHAR(50) NOT NULL, -- FK to shipments
    
    -- Recipient
    received_by_name VARCHAR(200),
    signature TEXT, -- Base64 encoded signature
    signature_url VARCHAR(500),
    
    -- Photos
    photo1_url VARCHAR(500),
    photo2_url VARCHAR(500),
    photo3_url VARCHAR(500),
    
    -- Packages
    packages_delivered INTEGER,
    packages_condition VARCHAR(50), -- good, damaged, missing
    
    -- Location
    delivery_latitude DECIMAL(10,7),
    delivery_longitude DECIMAL(10,7),
    geo_verified BOOLEAN DEFAULT false,
    
    -- Timing
    delivery_timestamp TIMESTAMP NOT NULL,
    
    -- Notes
    delivery_notes TEXT,
    
    -- Documents
    pod_document_url VARCHAR(500),
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- RETURNS / REVERSE LOGISTICS
-- ============================================================================

CREATE TABLE return_orders (
    return_order_id VARCHAR(50) PRIMARY KEY,
    return_number VARCHAR(50) UNIQUE NOT NULL,
    rma_number VARCHAR(50), -- Return Merchandise Authorization
    
    -- Original Order
    sales_order_id VARCHAR(50), -- FK to sales_orders
    original_shipment_id VARCHAR(50), -- FK to shipments
    
    -- Customer
    customer_id VARCHAR(50) NOT NULL, -- FK to customers
    
    -- Return Reason
    return_reason VARCHAR(50), -- defective, wrong_item, damaged, not_needed, quality_issue
    return_reason_details TEXT,
    
    -- Return Type
    return_type VARCHAR(50), -- refund, exchange, repair, credit
    
    -- Authorization
    authorized_by VARCHAR(50),
    authorization_date DATE,
    
    -- Return Location
    return_to_warehouse_id VARCHAR(50), -- FK to warehouses
    
    -- Status
    return_status VARCHAR(30) DEFAULT 'pending',
    -- pending, authorized, label_sent, in_transit, received, inspected, 
    -- processed, refunded, closed
    
    -- Financial
    refund_amount DECIMAL(15,2),
    restocking_fee DECIMAL(15,2),
    refund_processed BOOLEAN DEFAULT false,
    
    -- Disposition
    disposition VARCHAR(50), -- restock, repair, scrap, return_to_vendor
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE return_order_lines (
    return_line_id VARCHAR(50) PRIMARY KEY,
    return_order_id VARCHAR(50) NOT NULL, -- FK to return_orders
    line_number INTEGER,
    
    -- Original Order Line
    sales_order_line_id VARCHAR(50), -- FK to sales_order_lines
    
    -- Material
    material_id VARCHAR(50) NOT NULL, -- FK to materials
    material_description VARCHAR(200),
    
    -- Quantity
    quantity_to_return DECIMAL(15,4),
    quantity_received DECIMAL(15,4) DEFAULT 0,
    unit_of_measure VARCHAR(20),
    
    -- Condition
    condition_on_receipt VARCHAR(50), -- good, damaged, defective, missing_parts
    
    -- Serial/Batch
    serial_number VARCHAR(50),
    batch_number VARCHAR(50),
    
    -- Disposition
    disposition VARCHAR(50), -- restock, repair, scrap, return_to_vendor
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE return_shipments (
    return_shipment_id VARCHAR(50) PRIMARY KEY,
    return_order_id VARCHAR(50) NOT NULL, -- FK to return_orders
    
    -- Carrier
    carrier_id VARCHAR(50), -- FK to carriers
    service_id VARCHAR(50), -- FK to carrier_services
    tracking_number VARCHAR(100),
    
    -- Label
    return_label_url VARCHAR(500),
    label_cost DECIMAL(15,2),
    
    -- Pickup
    pickup_scheduled BOOLEAN DEFAULT false,
    pickup_date DATE,
    
    -- Status
    shipment_status VARCHAR(30) DEFAULT 'created',
    -- created, label_sent, picked_up, in_transit, delivered
    
    -- Timing
    shipped_date DATE,
    received_date DATE,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- FREIGHT BILLING
-- ============================================================================

CREATE TABLE freight_invoices (
    invoice_id VARCHAR(50) PRIMARY KEY,
    invoice_number VARCHAR(50) UNIQUE NOT NULL,
    
    -- Carrier
    carrier_id VARCHAR(50) NOT NULL, -- FK to carriers
    
    -- Invoice Details
    invoice_date DATE NOT NULL,
    due_date DATE,
    
    -- Amounts
    freight_charges DECIMAL(15,2),
    fuel_surcharge DECIMAL(15,2),
    accessorial_charges DECIMAL(15,2),
    total_amount DECIMAL(15,2),
    currency VARCHAR(3) DEFAULT 'INR',
    
    -- Status
    invoice_status VARCHAR(30) DEFAULT 'received',
    -- received, under_audit, approved, disputed, paid
    
    -- Audit
    audit_status VARCHAR(30), -- pending, approved, disputed
    variance_amount DECIMAL(15,2),
    dispute_reason TEXT,
    
    -- Payment
    payment_terms VARCHAR(50), -- NET30, NET60
    paid BOOLEAN DEFAULT false,
    payment_date DATE,
    payment_reference VARCHAR(100),
    
    -- Reconciliation
    reconciled BOOLEAN DEFAULT false,
    reconciliation_date DATE,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE freight_invoice_lines (
    invoice_line_id VARCHAR(50) PRIMARY KEY,
    invoice_id VARCHAR(50) NOT NULL, -- FK to freight_invoices
    line_number INTEGER,
    
    -- Shipment Reference
    shipment_id VARCHAR(50), -- FK to shipments
    shipment_number VARCHAR(50),
    tracking_number VARCHAR(100),
    
    -- Charges
    charge_type VARCHAR(50), -- freight, fuel, residential, signature, insurance
    charge_description VARCHAR(200),
    charge_amount DECIMAL(15,2),
    
    -- Expected vs Actual
    expected_amount DECIMAL(15,2),
    variance_amount DECIMAL(15,2),
    
    -- Audit
    approved BOOLEAN DEFAULT false,
    disputed BOOLEAN DEFAULT false,
    dispute_reason TEXT,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- INTEGRATION TABLES
-- ============================================================================

CREATE TABLE wms_tms_sync_log (
    sync_id VARCHAR(50) PRIMARY KEY,
    sync_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Sync Direction
    sync_direction VARCHAR(10), -- WMS_TO_TMS, TMS_TO_WMS
    
    -- Document Details
    document_type VARCHAR(50), 
    -- shipping_task, shipment, delivery_confirmation, tracking_update
    
    document_id VARCHAR(50),
    
    -- Status
    sync_status VARCHAR(30), -- pending, in_progress, completed, error
    error_message TEXT,
    
    -- Data
    sync_data JSONB,
    
    -- Retries
    retry_count INTEGER DEFAULT 0,
    last_retry_at TIMESTAMP
);

-- ============================================================================
-- INDICES FOR PERFORMANCE
-- ============================================================================

-- Carriers
CREATE INDEX idx_carriers_status ON carriers(carrier_status);
CREATE INDEX idx_carrier_services_carrier ON carrier_services(carrier_id, is_active);
CREATE INDEX idx_carrier_rates_carrier ON carrier_rates(carrier_id, service_id);

-- Shipments
CREATE INDEX idx_shipments_carrier ON shipments(carrier_id, shipment_status);
CREATE INDEX idx_shipments_tracking ON shipments(tracking_number);
CREATE INDEX idx_shipments_customer ON shipments(customer_id, shipment_status);
CREATE INDEX idx_shipments_warehouse ON shipments(warehouse_id, ship_date);
CREATE INDEX idx_shipments_order ON shipments(sales_order_id);
CREATE INDEX idx_shipment_lines_shipment ON shipment_lines(shipment_id);

-- Tracking
CREATE INDEX idx_tracking_shipment ON tracking_events(shipment_id, event_timestamp);
CREATE INDEX idx_tracking_number ON tracking_events(tracking_number, event_timestamp);

-- Routes
CREATE INDEX idx_routes_date ON routes(route_date, route_status);
CREATE INDEX idx_routes_carrier ON routes(carrier_id);
CREATE INDEX idx_route_stops_route ON route_stops(route_id, stop_sequence);

-- Deliveries
CREATE INDEX idx_deliveries_shipment ON deliveries(shipment_id);
CREATE INDEX idx_deliveries_customer ON deliveries(customer_id, delivery_status);
CREATE INDEX idx_deliveries_date ON deliveries(scheduled_delivery_date);
CREATE INDEX idx_pod_delivery ON proof_of_delivery(delivery_id);

-- Returns
CREATE INDEX idx_returns_customer ON return_orders(customer_id, return_status);
CREATE INDEX idx_returns_order ON return_orders(sales_order_id);
CREATE INDEX idx_return_lines_return ON return_order_lines(return_order_id);

-- Freight Billing
CREATE INDEX idx_freight_inv_carrier ON freight_invoices(carrier_id, invoice_status);
CREATE INDEX idx_freight_inv_date ON freight_invoices(invoice_date);
CREATE INDEX idx_freight_inv_lines_inv ON freight_invoice_lines(invoice_id);

-- Sync
CREATE INDEX idx_wms_tms_sync_status ON wms_tms_sync_log(sync_status, sync_timestamp);

-- ============================================================================
-- COMMENTS
-- ============================================================================

COMMENT ON TABLE carriers IS 'Shipping carrier master - courier, LTL, FTL, parcel services';
COMMENT ON TABLE shipments IS 'Shipment headers - link to sales orders and WMS';
COMMENT ON TABLE tracking_events IS 'Real-time shipment tracking events from carriers';
COMMENT ON TABLE routes IS 'Delivery routes with multi-stop optimization';
COMMENT ON TABLE deliveries IS 'Final delivery to customer with POD';
COMMENT ON TABLE return_orders IS 'Customer returns and reverse logistics';
COMMENT ON TABLE freight_invoices IS 'Carrier invoices and freight audit';
COMMENT ON TABLE wms_tms_sync_log IS 'Integration log between WMS and TMS';
