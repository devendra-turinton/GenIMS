-- GenIMS Operational Data Schema
-- Machine & Sensor Operational Data Ecosystem

-- ============================================================================
-- SCADA DATA (Machine-level operational data from PLCs)
-- ============================================================================

CREATE TABLE scada_machine_data (
    scada_id BIGSERIAL PRIMARY KEY,
    machine_id VARCHAR(50) NOT NULL, -- FK to machines
    line_id VARCHAR(50) NOT NULL, -- FK to production_lines
    factory_id VARCHAR(50) NOT NULL, -- FK to factories
    timestamp TIMESTAMP NOT NULL,
    
    -- Machine State
    machine_state VARCHAR(50) NOT NULL, -- running, idle, stopped, fault, maintenance, setup
    operation_mode VARCHAR(50), -- auto, manual, test
    fault_code VARCHAR(50), -- null if no fault
    fault_description TEXT,
    
    -- Production Metrics
    parts_produced_cumulative BIGINT, -- lifetime counter
    parts_produced_shift INTEGER, -- current shift counter
    parts_rejected_shift INTEGER, -- defects in current shift
    target_cycle_time_seconds INTEGER,
    actual_cycle_time_seconds DECIMAL(10,2),
    
    -- OEE Components
    availability_percentage DECIMAL(5,2), -- rolling calculation
    performance_percentage DECIMAL(5,2), -- actual vs target speed
    quality_percentage DECIMAL(5,2), -- good parts vs total parts
    oee_percentage DECIMAL(5,2), -- availability * performance * quality
    
    -- Operating Parameters
    spindle_speed_rpm INTEGER, -- for machining equipment
    feed_rate_mm_min DECIMAL(10,2), -- for machining equipment
    tool_number INTEGER, -- current tool in use
    program_number VARCHAR(50), -- CNC program number
    
    -- Power & Energy
    power_consumption_kw DECIMAL(10,2),
    energy_consumed_kwh DECIMAL(15,4), -- cumulative
    
    -- Process Parameters (varies by machine type)
    temperature_setpoint_c DECIMAL(8,2),
    temperature_actual_c DECIMAL(8,2),
    pressure_setpoint_bar DECIMAL(8,2),
    pressure_actual_bar DECIMAL(8,2),
    
    -- Downtime Tracking
    downtime_seconds_shift INTEGER, -- accumulated downtime current shift
    last_fault_timestamp TIMESTAMP,
    uptime_seconds_shift INTEGER, -- accumulated uptime current shift
    
    -- Alarms & Warnings
    active_alarms INTEGER, -- count of active alarms
    alarm_codes VARCHAR(500), -- comma-separated alarm codes
    warning_codes VARCHAR(500), -- comma-separated warning codes
    
    -- Shift & Operator
    shift_id VARCHAR(50), -- FK to shifts
    operator_id VARCHAR(50), -- FK to employees
    
    -- Data Quality
    data_source VARCHAR(50) DEFAULT 'PLC', -- PLC, SCADA, MES
    data_quality VARCHAR(20) DEFAULT 'good', -- good, uncertain, bad
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- SENSOR DATA (High-frequency IoT sensor readings)
-- ============================================================================

CREATE TABLE sensor_data (
    sensor_data_id BIGSERIAL PRIMARY KEY,
    sensor_id VARCHAR(50) NOT NULL, -- FK to sensors
    machine_id VARCHAR(50) NOT NULL, -- FK to machines
    line_id VARCHAR(50) NOT NULL, -- FK to production_lines
    factory_id VARCHAR(50) NOT NULL, -- FK to factories
    timestamp TIMESTAMP NOT NULL,
    
    -- Sensor Reading
    measurement_value DECIMAL(15,4) NOT NULL,
    measurement_unit VARCHAR(50) NOT NULL,
    
    -- Status Flags
    status VARCHAR(20) DEFAULT 'normal', -- normal, warning, critical, fault
    quality VARCHAR(20) DEFAULT 'good', -- good, uncertain, bad, out_of_range
    
    -- Threshold Checks (computed at edge)
    is_below_warning BOOLEAN DEFAULT false,
    is_above_warning BOOLEAN DEFAULT false,
    is_below_critical BOOLEAN DEFAULT false,
    is_above_critical BOOLEAN DEFAULT false,
    
    -- Statistical Window (rolling 1-minute calculations)
    min_value_1min DECIMAL(15,4),
    max_value_1min DECIMAL(15,4),
    avg_value_1min DECIMAL(15,4),
    std_dev_1min DECIMAL(15,4),
    
    -- Anomaly Detection
    anomaly_score DECIMAL(8,4), -- 0.0 to 1.0, higher = more anomalous
    is_anomaly BOOLEAN DEFAULT false,
    
    -- Data Source
    data_source VARCHAR(50) DEFAULT 'IoT', -- IoT, Edge, Gateway
    protocol VARCHAR(50), -- OPC-UA, Modbus, MQTT
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- MACHINE FAULTS (Detected fault events)
-- ============================================================================

CREATE TABLE machine_faults (
    fault_id BIGSERIAL PRIMARY KEY,
    machine_id VARCHAR(50) NOT NULL, -- FK to machines
    line_id VARCHAR(50) NOT NULL, -- FK to production_lines
    factory_id VARCHAR(50) NOT NULL, -- FK to factories
    
    -- Fault Details
    fault_code VARCHAR(50) NOT NULL,
    fault_category VARCHAR(50), -- mechanical, electrical, hydraulic, pneumatic, control, quality
    fault_severity VARCHAR(20), -- critical, major, minor, warning
    fault_description TEXT,
    
    -- Timing
    fault_start_time TIMESTAMP NOT NULL,
    fault_end_time TIMESTAMP,
    fault_duration_seconds INTEGER,
    
    -- Impact
    production_loss_units INTEGER,
    downtime_minutes INTEGER,
    estimated_cost_usd DECIMAL(12,2),
    
    -- Root Cause
    root_cause_category VARCHAR(100), -- bearing_failure, overheating, tool_wear, etc.
    root_cause_description TEXT,
    contributing_sensors VARCHAR(500), -- comma-separated sensor_ids
    
    -- Resolution
    resolution_action TEXT,
    maintenance_ticket_id VARCHAR(50),
    resolved_by VARCHAR(50), -- FK to employees
    
    -- Detection Method
    detection_method VARCHAR(50), -- sensor_threshold, predictive_model, operator_report, automatic
    predicted_in_advance BOOLEAN DEFAULT false,
    advance_warning_hours DECIMAL(8,2),
    
    -- Status
    status VARCHAR(20) DEFAULT 'open', -- open, acknowledged, in_progress, resolved, closed
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- SENSOR HEALTH (Sensor calibration and health tracking)
-- ============================================================================

CREATE TABLE sensor_health (
    health_id BIGSERIAL PRIMARY KEY,
    sensor_id VARCHAR(50) NOT NULL, -- FK to sensors
    machine_id VARCHAR(50) NOT NULL, -- FK to machines
    timestamp TIMESTAMP NOT NULL,
    
    -- Health Metrics
    health_score DECIMAL(5,2), -- 0-100, lower = worse
    drift_percentage DECIMAL(8,4), -- deviation from expected
    noise_level DECIMAL(8,4), -- signal-to-noise ratio
    
    -- Calibration Status
    days_since_calibration INTEGER,
    is_calibration_due BOOLEAN DEFAULT false,
    calibration_drift_detected BOOLEAN DEFAULT false,
    
    -- Communication Health
    packet_loss_percentage DECIMAL(5,2),
    average_latency_ms DECIMAL(10,2),
    last_communication TIMESTAMP,
    communication_failures_24h INTEGER,
    
    -- Battery/Power (for wireless sensors)
    battery_percentage DECIMAL(5,2),
    is_low_battery BOOLEAN DEFAULT false,
    
    -- Quality Indicators
    stuck_value_detected BOOLEAN DEFAULT false, -- sensor reading same value repeatedly
    erratic_readings_detected BOOLEAN DEFAULT false, -- wildly fluctuating values
    out_of_range_readings_24h INTEGER,
    
    -- Status
    overall_status VARCHAR(20) DEFAULT 'healthy', -- healthy, degraded, critical, failed
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- PRODUCTION RUNS (Batch/lot tracking)
-- ============================================================================

CREATE TABLE production_runs (
    run_id VARCHAR(50) PRIMARY KEY,
    line_id VARCHAR(50) NOT NULL, -- FK to production_lines
    factory_id VARCHAR(50) NOT NULL, -- FK to factories
    product_id VARCHAR(50) NOT NULL, -- FK to products
    
    -- Run Details
    run_number INTEGER,
    batch_number VARCHAR(50),
    work_order_number VARCHAR(50),
    customer_id VARCHAR(50), -- FK to customers
    
    -- Timing
    run_start_time TIMESTAMP NOT NULL,
    run_end_time TIMESTAMP,
    planned_duration_minutes INTEGER,
    actual_duration_minutes INTEGER,
    
    -- Targets & Actuals
    target_quantity INTEGER,
    actual_quantity INTEGER,
    rejected_quantity INTEGER,
    scrapped_quantity INTEGER,
    rework_quantity INTEGER,
    
    -- Quality Metrics
    first_pass_yield_percentage DECIMAL(5,2),
    defect_rate_ppm INTEGER,
    quality_grade VARCHAR(20), -- A, B, C
    
    -- OEE Metrics (for this run)
    oee_percentage DECIMAL(5,2),
    availability_percentage DECIMAL(5,2),
    performance_percentage DECIMAL(5,2),
    quality_percentage DECIMAL(5,2),
    
    -- Changeover
    previous_product_id VARCHAR(50), -- FK to products
    changeover_time_minutes INTEGER,
    
    -- Shift & Crew
    shift_id VARCHAR(50), -- FK to shifts
    supervisor_id VARCHAR(50), -- FK to employees
    
    -- Status
    status VARCHAR(20) DEFAULT 'in_progress', -- scheduled, in_progress, completed, aborted
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- MACHINE MAINTENANCE EVENTS
-- ============================================================================

CREATE TABLE maintenance_events (
    maintenance_id VARCHAR(50) PRIMARY KEY,
    machine_id VARCHAR(50) NOT NULL, -- FK to machines
    line_id VARCHAR(50) NOT NULL, -- FK to production_lines
    factory_id VARCHAR(50) NOT NULL, -- FK to factories
    
    -- Event Details
    maintenance_type VARCHAR(50), -- preventive, predictive, corrective, breakdown
    maintenance_category VARCHAR(50), -- mechanical, electrical, hydraulic, lubrication, calibration
    priority VARCHAR(20), -- critical, high, medium, low
    
    -- Timing
    scheduled_start TIMESTAMP,
    actual_start TIMESTAMP,
    actual_end TIMESTAMP,
    duration_minutes INTEGER,
    
    -- Work Performed
    work_description TEXT,
    parts_replaced VARCHAR(500), -- comma-separated part numbers
    parts_cost_usd DECIMAL(12,2),
    labor_hours DECIMAL(8,2),
    labor_cost_usd DECIMAL(12,2),
    total_cost_usd DECIMAL(12,2),
    
    -- Personnel
    technician_id VARCHAR(50), -- FK to employees
    supervisor_id VARCHAR(50), -- FK to employees
    
    -- Related Fault
    related_fault_id BIGINT, -- FK to machine_faults
    
    -- Outcome
    completion_status VARCHAR(20), -- completed, partial, deferred, cancelled
    notes TEXT,
    follow_up_required BOOLEAN DEFAULT false,
    next_maintenance_due DATE,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- INDICES FOR PERFORMANCE
-- ============================================================================

-- SCADA Data Indices
CREATE INDEX idx_scada_machine_timestamp ON scada_machine_data(machine_id, timestamp DESC);
CREATE INDEX idx_scada_line_timestamp ON scada_machine_data(line_id, timestamp DESC);
CREATE INDEX idx_scada_factory_timestamp ON scada_machine_data(factory_id, timestamp DESC);
CREATE INDEX idx_scada_state ON scada_machine_data(machine_state, timestamp DESC);
CREATE INDEX idx_scada_fault ON scada_machine_data(fault_code) WHERE fault_code IS NOT NULL;
CREATE INDEX idx_scada_timestamp ON scada_machine_data(timestamp DESC);

-- Sensor Data Indices
CREATE INDEX idx_sensor_data_sensor_timestamp ON sensor_data(sensor_id, timestamp DESC);
CREATE INDEX idx_sensor_data_machine_timestamp ON sensor_data(machine_id, timestamp DESC);
CREATE INDEX idx_sensor_data_line_timestamp ON sensor_data(line_id, timestamp DESC);
CREATE INDEX idx_sensor_data_status ON sensor_data(status, timestamp DESC);
CREATE INDEX idx_sensor_data_anomaly ON sensor_data(is_anomaly, timestamp DESC);
CREATE INDEX idx_sensor_data_timestamp ON sensor_data(timestamp DESC);

-- Machine Faults Indices
CREATE INDEX idx_faults_machine ON machine_faults(machine_id, fault_start_time DESC);
CREATE INDEX idx_faults_line ON machine_faults(line_id, fault_start_time DESC);
CREATE INDEX idx_faults_factory ON machine_faults(factory_id, fault_start_time DESC);
CREATE INDEX idx_faults_status ON machine_faults(status, fault_start_time DESC);
CREATE INDEX idx_faults_severity ON machine_faults(fault_severity, fault_start_time DESC);
CREATE INDEX idx_faults_category ON machine_faults(fault_category, fault_start_time DESC);

-- Sensor Health Indices
CREATE INDEX idx_sensor_health_sensor ON sensor_health(sensor_id, timestamp DESC);
CREATE INDEX idx_sensor_health_status ON sensor_health(overall_status, timestamp DESC);

-- Production Runs Indices
CREATE INDEX idx_production_runs_line ON production_runs(line_id, run_start_time DESC);
CREATE INDEX idx_production_runs_product ON production_runs(product_id, run_start_time DESC);
CREATE INDEX idx_production_runs_status ON production_runs(status, run_start_time DESC);

-- Maintenance Events Indices
CREATE INDEX idx_maintenance_machine ON maintenance_events(machine_id, scheduled_start DESC);
CREATE INDEX idx_maintenance_type ON maintenance_events(maintenance_type, scheduled_start DESC);
CREATE INDEX idx_maintenance_status ON maintenance_events(completion_status, scheduled_start DESC);

-- ============================================================================
-- PARTITIONING STRATEGY (for time-series data)
-- ============================================================================

-- Note: For production deployment, consider partitioning by date:
-- - scada_machine_data: Partition by day or week
-- - sensor_data: Partition by day (high volume)
-- - Retention policy: Keep raw data for 90 days, aggregated data longer

-- Example (PostgreSQL 12+):
-- CREATE TABLE scada_machine_data_2025_12 PARTITION OF scada_machine_data
-- FOR VALUES FROM ('2025-12-01') TO ('2026-01-01');
