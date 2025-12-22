-- GenIMS Base Master Data Schema
-- Auto Parts Manufacturing - Global Operations

-- ============================================================================
-- FACTORY & LOCATION
-- ============================================================================

CREATE TABLE factories (
    factory_id VARCHAR(50) PRIMARY KEY,
    factory_name VARCHAR(200) NOT NULL,
    country VARCHAR(100) NOT NULL,
    city VARCHAR(100) NOT NULL,
    region VARCHAR(100),
    timezone VARCHAR(50),
    total_area_sqm INTEGER,
    operational_since DATE,
    factory_type VARCHAR(50), -- assembly, machining, testing
    certification VARCHAR(200), -- ISO9001, IATF16949, ISO14001
    status VARCHAR(20) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- PRODUCTION LINES
-- ============================================================================

CREATE TABLE production_lines (
    line_id VARCHAR(50) PRIMARY KEY,
    factory_id VARCHAR(50) NOT NULL, -- FK to factories
    line_name VARCHAR(200) NOT NULL,
    line_number INTEGER,
    product_category VARCHAR(100), -- suspension, brake, electrical
    line_type VARCHAR(50), -- assembly, machining, testing, painting
    design_capacity_units_per_hour INTEGER,
    installed_capacity_units_per_hour INTEGER,
    line_length_meters DECIMAL(10,2),
    num_stations INTEGER,
    automation_level VARCHAR(50), -- manual, semi-automated, fully-automated
    commissioning_date DATE,
    status VARCHAR(20) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- MACHINES
-- ============================================================================

CREATE TABLE machines (
    machine_id VARCHAR(50) PRIMARY KEY,
    line_id VARCHAR(50) NOT NULL, -- FK to production_lines
    factory_id VARCHAR(50) NOT NULL, -- FK to factories
    machine_name VARCHAR(200) NOT NULL,
    machine_code VARCHAR(50),
    machine_type VARCHAR(100), -- CNC, press, robot, conveyor, welding, assembly, testing
    manufacturer VARCHAR(100),
    model_number VARCHAR(100),
    serial_number VARCHAR(100),
    installation_date DATE,
    last_major_overhaul DATE,
    design_capacity_units_per_hour INTEGER,
    power_rating_kw DECIMAL(10,2),
    maintenance_schedule VARCHAR(50), -- daily, weekly, monthly, quarterly
    criticality VARCHAR(20), -- critical, high, medium, low
    asset_value_usd DECIMAL(15,2),
    expected_life_years INTEGER,
    current_age_years DECIMAL(5,2),
    status VARCHAR(20) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- SENSORS
-- ============================================================================

CREATE TABLE sensors (
    sensor_id VARCHAR(50) PRIMARY KEY,
    machine_id VARCHAR(50) NOT NULL, -- FK to machines
    line_id VARCHAR(50) NOT NULL, -- FK to production_lines
    factory_id VARCHAR(50) NOT NULL, -- FK to factories
    sensor_name VARCHAR(200) NOT NULL,
    sensor_code VARCHAR(50),
    sensor_type VARCHAR(100), -- temperature, vibration, pressure, current, voltage, flow, speed, torque
    measurement_unit VARCHAR(50),
    measurement_range_min DECIMAL(15,4),
    measurement_range_max DECIMAL(15,4),
    normal_operating_min DECIMAL(15,4),
    normal_operating_max DECIMAL(15,4),
    warning_threshold_min DECIMAL(15,4),
    warning_threshold_max DECIMAL(15,4),
    critical_threshold_min DECIMAL(15,4),
    critical_threshold_max DECIMAL(15,4),
    sampling_frequency_hz DECIMAL(10,2),
    data_protocol VARCHAR(50), -- OPC-UA, Modbus, MQTT, REST
    manufacturer VARCHAR(100),
    model_number VARCHAR(100),
    calibration_date DATE,
    calibration_frequency_days INTEGER,
    accuracy_percentage DECIMAL(5,2),
    status VARCHAR(20) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- EMPLOYEES
-- ============================================================================

CREATE TABLE employees (
    employee_id VARCHAR(50) PRIMARY KEY,
    factory_id VARCHAR(50) NOT NULL, -- FK to factories
    line_id VARCHAR(50), -- FK to production_lines (nullable for non-production staff)
    employee_code VARCHAR(50),
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    email VARCHAR(200),
    phone VARCHAR(50),
    role VARCHAR(100), -- operator, technician, supervisor, engineer, manager, quality_inspector
    department VARCHAR(100), -- production, maintenance, quality, planning, logistics
    skill_level VARCHAR(50), -- trainee, skilled, senior, expert
    shift VARCHAR(20), -- shift_a, shift_b, shift_c, general
    hire_date DATE,
    experience_years DECIMAL(5,2),
    certifications VARCHAR(500),
    status VARCHAR(20) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- SHIFTS
-- ============================================================================

CREATE TABLE shifts (
    shift_id VARCHAR(50) PRIMARY KEY,
    factory_id VARCHAR(50) NOT NULL, -- FK to factories
    shift_name VARCHAR(50), -- shift_a, shift_b, shift_c
    shift_code VARCHAR(20),
    start_time TIME,
    end_time TIME,
    duration_hours DECIMAL(4,2),
    shift_type VARCHAR(50), -- regular, overtime, weekend
    break_duration_minutes INTEGER,
    days_of_week VARCHAR(100), -- mon,tue,wed,thu,fri or sat,sun
    status VARCHAR(20) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- PRODUCTS (Auto Parts)
-- ============================================================================

CREATE TABLE products (
    product_id VARCHAR(50) PRIMARY KEY,
    product_code VARCHAR(50),
    product_name VARCHAR(200) NOT NULL,
    product_category VARCHAR(100), -- suspension, brake, electrical, steering, transmission
    product_type VARCHAR(100), -- assembly, component, sub-assembly
    description TEXT,
    bill_of_material_complexity VARCHAR(50), -- simple, moderate, complex
    number_of_components INTEGER,
    standard_cycle_time_seconds INTEGER,
    target_quality_ppm INTEGER, -- parts per million defect rate
    unit_weight_kg DECIMAL(10,3),
    material_type VARCHAR(100),
    status VARCHAR(20) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- CUSTOMERS
-- ============================================================================

CREATE TABLE customers (
    customer_id VARCHAR(50) PRIMARY KEY,
    customer_code VARCHAR(50),
    customer_name VARCHAR(200) NOT NULL,
    customer_type VARCHAR(50), -- oem, tier1, tier2, aftermarket
    country VARCHAR(100),
    region VARCHAR(100),
    industry_segment VARCHAR(100), -- automotive_oem, commercial_vehicle, two_wheeler
    annual_volume_estimate INTEGER,
    quality_rating VARCHAR(20), -- excellent, good, fair
    payment_terms_days INTEGER,
    sla_on_time_delivery_percentage DECIMAL(5,2),
    sla_quality_ppm_max INTEGER,
    status VARCHAR(20) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- PRODUCT LINE MAPPING (Which lines produce which products)
-- ============================================================================

CREATE TABLE line_product_mapping (
    mapping_id VARCHAR(50) PRIMARY KEY,
    line_id VARCHAR(50) NOT NULL, -- FK to production_lines
    product_id VARCHAR(50) NOT NULL, -- FK to products
    factory_id VARCHAR(50) NOT NULL, -- FK to factories
    is_primary_line BOOLEAN DEFAULT false,
    standard_cycle_time_seconds INTEGER,
    setup_time_minutes INTEGER,
    changeover_time_minutes INTEGER,
    yield_percentage DECIMAL(5,2),
    status VARCHAR(20) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- CUSTOMER PRODUCT MAPPING (Which customers order which products)
-- ============================================================================

CREATE TABLE customer_product_mapping (
    mapping_id VARCHAR(50) PRIMARY KEY,
    customer_id VARCHAR(50) NOT NULL, -- FK to customers
    product_id VARCHAR(50) NOT NULL, -- FK to products
    is_active BOOLEAN DEFAULT true,
    annual_volume INTEGER,
    unit_price_usd DECIMAL(10,2),
    lead_time_days INTEGER,
    quality_requirement_ppm INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- INDICES FOR PERFORMANCE
-- ============================================================================

CREATE INDEX idx_production_lines_factory ON production_lines(factory_id);
CREATE INDEX idx_machines_line ON machines(line_id);
CREATE INDEX idx_machines_factory ON machines(factory_id);
CREATE INDEX idx_sensors_machine ON sensors(machine_id);
CREATE INDEX idx_sensors_line ON sensors(line_id);
CREATE INDEX idx_sensors_factory ON sensors(factory_id);
CREATE INDEX idx_employees_factory ON employees(factory_id);
CREATE INDEX idx_employees_line ON employees(line_id);
CREATE INDEX idx_employees_role ON employees(role);
CREATE INDEX idx_shifts_factory ON shifts(factory_id);
CREATE INDEX idx_line_product_mapping_line ON line_product_mapping(line_id);
CREATE INDEX idx_line_product_mapping_product ON line_product_mapping(product_id);
CREATE INDEX idx_customer_product_mapping_customer ON customer_product_mapping(customer_id);
CREATE INDEX idx_customer_product_mapping_product ON customer_product_mapping(product_id);
