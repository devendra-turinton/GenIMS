# GenIMS Operational Data Ecosystem

## Overview
Complete machine and sensor data streaming system with realistic fault patterns for GenIMS platform. This package includes PostgreSQL schemas, Python data generators, and streaming daemons that simulate real-time IoT sensor data and PLC/SCADA machine operational data.

---

## 📦 Package Contents

### 1. Database Schemas

#### `genims_operational_schema.sql` (14 KB)
Complete PostgreSQL schema for operational data:
- **scada_machine_data** - Machine-level operational data from PLCs
- **sensor_data** - High-frequency IoT sensor readings
- **machine_faults** - Detected fault events with root cause analysis
- **sensor_health** - Sensor calibration and health tracking
- **production_runs** - Batch/lot production tracking
- **maintenance_events** - Maintenance work history

### 2. Fault Pattern Documentation

#### `FAULT_PATTERNS.md` (20 KB)
Comprehensive fault pattern library documenting 10 failure modes:
1. **Bearing Failures** - Gradual vibration and temperature increase (7-21 days)
2. **Motor Overheating** - Thermal overload (30 min - 4 hours)
3. **Hydraulic Pressure Loss** - Sudden or gradual leak (minutes to weeks)
4. **Tool Wear** - Cutting tool degradation (4-48 hours)
5. **Welding Quality** - Weld parameter drift (1-8 hours)
6. **Pneumatic System Failure** - Air pressure loss (30 min - 24 hours)
7. **Coolant System Failure** - Flow/temperature issues (15 min - 4 hours)
8. **Robot Positioning Error** - Servo/encoder drift (1 hour - 7 days)
9. **Electrical Faults** - Power anomalies (milliseconds - minutes)
10. **Sensor Drift/Failure** - Calibration issues (days - weeks)

Each pattern includes:
- Signature characteristics
- Progression timelines
- Detection queries
- Multi-sensor correlation rules

### 3. Data Generators

#### `generate_operational_data.py` (31 KB)
Historical data generator with realistic fault injection:
- Generates 7 days of SCADA and sensor data
- Implements all 10 fault patterns
- Configurable fault probability (5% default)
- Exports to SQL and JSON

**Usage:**
```bash
python3 generate_operational_data.py
```

**Output:**
- `genims_operational_data_inserts.sql` - Sample SQL inserts
- `genims_operational_data.json` - Sample JSON data

### 4. Streaming Daemons

#### `iot_daemon.py` (17 KB)
Real-time sensor data streaming daemon:
- **Sampling Rate**: 10 seconds per sensor
- **Data Volume**: ~1,700 sensors × 6 readings/min = ~10,200 records/min
- **Kafka Topic**: `genims.sensor.data`
- **Features**:
  - Realistic sensor physics simulation
  - Fault pattern injection
  - Statistical windowing (1-minute rolling stats)
  - Anomaly detection scoring
  - Batch PostgreSQL inserts

#### `scada_daemon.py` (22 KB)
Real-time machine operational data streaming daemon:
- **Sampling Rate**: 60 seconds per machine
- **Data Volume**: ~228 machines × 1 reading/min = ~228 records/min
- **Kafka Topic**: `genims.scada.data`
- **Features**:
  - Machine state simulation (running/idle/fault/maintenance)
  - OEE calculation (availability × performance × quality)
  - Production counting and quality tracking
  - Shift-based operations
  - Tool wear simulation

#### `start_daemons.sh`
Convenience script to start both daemons simultaneously with logging.

---

## 🚀 Quick Start

### Prerequisites

1. **PostgreSQL Database**
```bash
# Create database
createdb genims_db

# Load master data schema
psql -d genims_db -f genims_schema.sql
psql -d genims_db -f genims_master_data_inserts.sql

# Load operational data schema
psql -d genims_db -f genims_operational_schema.sql
```

2. **Python Dependencies**
```bash
pip install psycopg2-binary kafka-python numpy
```

3. **Kafka (Optional but Recommended)**
```bash
# Start Kafka broker on localhost:9092
# Daemons will work without Kafka but only write to PostgreSQL
```

### Step 1: Generate Historical Data (Optional)
```bash
# Generate 7 days of historical operational data
python3 generate_operational_data.py

# This creates sample data with fault patterns injected
# Load into database if desired
```

### Step 2: Start Streaming Daemons
```bash
# Start both daemons
chmod +x start_daemons.sh
./start_daemons.sh

# Or start individually:
python3 iot_daemon.py &
python3 scada_daemon.py &
```

### Step 3: Monitor Data
```bash
# Watch logs
tail -f logs/iot_daemon.log
tail -f logs/scada_daemon.log

# Query real-time data
psql -d genims_db -c "
SELECT 
    machine_id, 
    machine_state, 
    oee_percentage,
    parts_produced_shift
FROM scada_machine_data 
WHERE timestamp > NOW() - INTERVAL '5 minutes'
ORDER BY timestamp DESC 
LIMIT 10;
"

# Check sensor anomalies
psql -d genims_db -c "
SELECT 
    s.sensor_type,
    sd.measurement_value,
    sd.status,
    sd.anomaly_score
FROM sensor_data sd
JOIN sensors s ON sd.sensor_id = s.sensor_id
WHERE sd.is_anomaly = true
  AND sd.timestamp > NOW() - INTERVAL '10 minutes'
ORDER BY sd.anomaly_score DESC
LIMIT 10;
"
```

---

## 📊 Data Characteristics

### SCADA Data (scada_machine_data)

**Sample Rate**: 1 minute per machine  
**Volume**: ~228 machines × 1,440 min/day = ~328,320 records/day

**Key Metrics**:
- **Machine State**: running (88%), idle (10%), setup (2%), fault (<1%)
- **OEE Components**: availability, performance, quality
- **Production Counts**: parts produced, rejected
- **Process Parameters**: temperature, pressure, power
- **Alarms & Warnings**: fault codes, descriptions

**Example Record**:
```json
{
  "machine_id": "MCH-000001",
  "timestamp": "2025-12-19 14:30:00",
  "machine_state": "running",
  "oee_percentage": 82.5,
  "parts_produced_shift": 145,
  "parts_rejected_shift": 3,
  "availability_percentage": 95.0,
  "performance_percentage": 92.0,
  "quality_percentage": 98.0,
  "power_consumption_kw": 85.2,
  "temperature_actual_c": 62.5
}
```

### Sensor Data (sensor_data)

**Sample Rate**: 10 seconds per sensor  
**Volume**: ~1,716 sensors × 8,640 samples/day = ~14.8M records/day

**Sensor Types**: 10 types monitoring different parameters
- Temperature (Celsius)
- Vibration (mm/s)
- Pressure (bar)
- Current (ampere)
- Voltage (volt)
- Flow (L/min)
- Speed (rpm)
- Torque (Nm)
- Force (kN)
- Displacement (mm)

**Example Record**:
```json
{
  "sensor_id": "SNS-000001",
  "sensor_type": "vibration",
  "measurement_value": 12.5,
  "measurement_unit": "mm/s",
  "status": "normal",
  "avg_value_1min": 12.3,
  "std_dev_1min": 0.8,
  "anomaly_score": 0.15,
  "is_anomaly": false
}
```

---

## 🔧 Configuration

### Database Connection

Edit in daemon scripts:
```python
PG_HOST = 'localhost'
PG_PORT = 5432
PG_DATABASE = 'genims_db'
PG_USER = 'genims_user'
PG_PASSWORD = 'genims_password'
```

### Kafka Configuration

Edit in daemon scripts:
```python
KAFKA_BOOTSTRAP_SERVERS = ['localhost:9092']
KAFKA_TOPIC_IOT = 'genims.sensor.data'
KAFKA_TOPIC_SCADA = 'genims.scada.data'
```

### Sampling Rates

Edit in daemon scripts:
```python
# IoT Daemon
SENSOR_SAMPLING_INTERVAL = 10  # seconds

# SCADA Daemon
SCADA_SAMPLING_INTERVAL = 60  # seconds
```

### Fault Injection

Modify in daemon code:
```python
# Percentage of sensors/machines with faults
FAULT_PROBABILITY = 0.05  # 5%

# In iot_daemon.py - inject custom faults
simulator.inject_fault(
    duration_seconds=1800,  # 30 minutes
    severity=0.8            # 80% severity
)

# In scada_daemon.py - inject custom faults
simulator.inject_fault(
    fault_code='BEAR-001',
    fault_description='Bearing degradation detected',
    duration_seconds=600
)
```

---

## 🎯 Fault Detection Queries

### 1. Active Machine Faults
```sql
SELECT 
    m.machine_name,
    f.fault_code,
    f.fault_description,
    f.fault_severity,
    f.fault_start_time,
    EXTRACT(EPOCH FROM (NOW() - f.fault_start_time))/60 as duration_minutes
FROM machine_faults f
JOIN machines m ON f.machine_id = m.machine_id
WHERE f.status = 'open'
ORDER BY f.fault_start_time DESC;
```

### 2. Machines with Critical Sensor Readings
```sql
SELECT 
    m.machine_id,
    m.machine_name,
    s.sensor_type,
    sd.measurement_value,
    sd.status,
    s.critical_threshold_max
FROM sensor_data sd
JOIN sensors s ON sd.sensor_id = s.sensor_id
JOIN machines m ON s.machine_id = m.machine_id
WHERE sd.status = 'critical'
  AND sd.timestamp > NOW() - INTERVAL '10 minutes'
ORDER BY sd.timestamp DESC;
```

### 3. Bearing Failure Early Warning
```sql
-- Pattern: Increasing vibration + temperature
WITH vibration_trend AS (
    SELECT 
        machine_id,
        AVG(measurement_value) as avg_vibration,
        MAX(measurement_value) as max_vibration,
        STDDEV(measurement_value) as std_vibration
    FROM sensor_data sd
    JOIN sensors s ON sd.sensor_id = s.sensor_id
    WHERE s.sensor_type = 'vibration'
      AND sd.timestamp > NOW() - INTERVAL '24 hours'
    GROUP BY machine_id
),
temperature_trend AS (
    SELECT 
        machine_id,
        AVG(measurement_value) as avg_temperature
    FROM sensor_data sd
    JOIN sensors s ON sd.sensor_id = s.sensor_id
    WHERE s.sensor_type = 'temperature'
      AND sd.timestamp > NOW() - INTERVAL '24 hours'
    GROUP BY machine_id
)
SELECT 
    m.machine_id,
    m.machine_name,
    v.avg_vibration,
    v.max_vibration,
    t.avg_temperature,
    CASE 
        WHEN v.avg_vibration > 18 AND t.avg_temperature > 70 THEN 'CRITICAL'
        WHEN v.avg_vibration > 15 AND t.avg_temperature > 60 THEN 'WARNING'
        ELSE 'NORMAL'
    END as bearing_health_status
FROM machines m
JOIN vibration_trend v ON m.machine_id = v.machine_id
JOIN temperature_trend t ON m.machine_id = t.machine_id
WHERE v.avg_vibration > 15
ORDER BY v.avg_vibration DESC;
```

### 4. Low OEE Machines (Performance Issues)
```sql
SELECT 
    m.machine_id,
    m.machine_name,
    smd.machine_state,
    AVG(smd.oee_percentage) as avg_oee,
    AVG(smd.availability_percentage) as avg_availability,
    AVG(smd.performance_percentage) as avg_performance,
    AVG(smd.quality_percentage) as avg_quality,
    COUNT(*) as samples
FROM scada_machine_data smd
JOIN machines m ON smd.machine_id = m.machine_id
WHERE smd.timestamp > NOW() - INTERVAL '8 hours'
GROUP BY m.machine_id, m.machine_name, smd.machine_state
HAVING AVG(smd.oee_percentage) < 70
ORDER BY avg_oee ASC;
```

### 5. Sensor Health Monitoring
```sql
SELECT 
    s.sensor_id,
    s.sensor_name,
    s.sensor_type,
    m.machine_name,
    sh.health_score,
    sh.drift_percentage,
    sh.days_since_calibration,
    sh.overall_status
FROM sensor_health sh
JOIN sensors s ON sh.sensor_id = s.sensor_id
JOIN machines m ON s.machine_id = m.machine_id
WHERE sh.timestamp > NOW() - INTERVAL '1 hour'
  AND (sh.health_score < 70 OR sh.drift_percentage > 5)
ORDER BY sh.health_score ASC;
```

### 6. Multi-Sensor Anomaly Detection
```sql
-- Machines with 3+ sensors showing anomalies
SELECT 
    m.machine_id,
    m.machine_name,
    COUNT(DISTINCT sd.sensor_id) as anomaly_sensor_count,
    STRING_AGG(DISTINCT s.sensor_type, ', ') as affected_sensor_types,
    MAX(sd.anomaly_score) as max_anomaly_score
FROM sensor_data sd
JOIN sensors s ON sd.sensor_id = s.sensor_id
JOIN machines m ON s.machine_id = m.machine_id
WHERE sd.is_anomaly = true
  AND sd.timestamp > NOW() - INTERVAL '30 minutes'
GROUP BY m.machine_id, m.machine_name
HAVING COUNT(DISTINCT sd.sensor_id) >= 3
ORDER BY anomaly_sensor_count DESC;
```

---

## 📈 Performance Optimization

### Database Indexing

The schema includes optimized indices for time-series queries:
- Composite indices on (machine_id, timestamp)
- Indices on status fields for filtering
- Partial indices for fault records

### Partitioning Strategy

For production deployment, consider partitioning large tables by date:

```sql
-- Example: Partition sensor_data by day
CREATE TABLE sensor_data_2025_12_19 PARTITION OF sensor_data
FOR VALUES FROM ('2025-12-19') TO ('2025-12-20');

-- Automate with pg_partman extension
```

### Data Retention

Implement retention policies:
```sql
-- Delete old sensor data (keep 90 days)
DELETE FROM sensor_data 
WHERE timestamp < NOW() - INTERVAL '90 days';

-- Archive to separate table before deletion
INSERT INTO sensor_data_archive 
SELECT * FROM sensor_data 
WHERE timestamp < NOW() - INTERVAL '90 days';
```

---

## 🔬 Testing Fault Patterns

### Inject Test Faults

**While daemons are running**, you can modify the code to inject specific faults:

1. **Bearing Failure Simulation**
```python
# In iot_daemon.py, find vibration sensors on target machine
# Inject gradually increasing vibration over 7 days
simulator.inject_fault(duration_seconds=604800, severity=0.9)
```

2. **Motor Overheating**
```python
# In scada_daemon.py, inject thermal fault
simulator.inject_fault('THERM-001', 'Motor thermal overload', 3600)
```

3. **Hydraulic Leak**
```python
# In iot_daemon.py, for pressure sensors
simulator.inject_fault(duration_seconds=300, severity=0.95)
```

### Verify Fault Detection

Query the database to confirm fault patterns are detectable:
```bash
# Check if vibration is increasing
psql -d genims_db -f detect_bearing_failure.sql

# Check for temperature anomalies
psql -d genims_db -f detect_overheating.sql
```

---

## 📝 Daemon Logs

### Log Format
```
2025-12-19 14:30:45 - IoTDaemon - INFO - Sample: vibration = 12.50 mm/s [normal]
2025-12-19 14:30:45 - IoTDaemon - INFO - Fault injected: SNS-000123 (vibration), severity=0.70, duration=1800s
2025-12-19 14:31:45 - IoTDaemon - INFO - Inserted 100 records to PostgreSQL
2025-12-19 14:32:45 - IoTDaemon - INFO - Statistics: 10,200 records/min, 0 errors
```

### Monitor Logs in Real-Time
```bash
# Follow IoT daemon logs
tail -f logs/iot_daemon.log

# Follow SCADA daemon logs
tail -f logs/scada_daemon.log

# Filter for faults only
tail -f logs/iot_daemon.log | grep "Fault"
tail -f logs/scada_daemon.log | grep "fault"
```

---

## 🎓 Architecture

### Data Flow

```
Physical Sensors → IoT Gateway → iot_daemon.py → Kafka + PostgreSQL
      ↓
PLC Controllers → SCADA System → scada_daemon.py → Kafka + PostgreSQL
      ↓
Knowledge Graph (Data Virtualization Layer)
      ↓
GenIMS Multi-Agent System
      ↓
Impact Cascade Engine → Autonomous Actions
```

### Multi-Agent Consumption

Different GenIMS agents consume different data streams:

1. **Asset Management Agent**: sensor_data + machine_faults
2. **Factory Operations Agent**: scada_machine_data + production_runs
3. **Quality Agent**: sensor_data (quality-related) + scada_machine_data
4. **Energy Agent**: scada_machine_data (power metrics)
5. **Predictive Maintenance Agent**: sensor_data + sensor_health + machine_faults

---

## 🐛 Troubleshooting

### Daemon Won't Start

**Error**: `Failed to connect to PostgreSQL`
```bash
# Check PostgreSQL is running
pg_isready -h localhost -p 5432

# Check database exists
psql -l | grep genims_db

# Check connection parameters in daemon
```

**Error**: `Failed to load sensors`
```bash
# Ensure master data exists
ls -lh genims_master_data.json

# Regenerate if needed
python3 generate_genims_master_data.py
```

### Low Data Throughput

**Issue**: Daemons falling behind sampling rate

**Solutions**:
1. Increase batch size: `BATCH_SIZE = 200`
2. Reduce logging frequency
3. Optimize PostgreSQL:
```sql
-- Increase shared_buffers in postgresql.conf
shared_buffers = 2GB
work_mem = 64MB
```

### Kafka Connection Issues

**Issue**: Kafka not available

**Impact**: Daemons will log warnings but continue writing to PostgreSQL only.

**Solution**: Either install Kafka or disable Kafka in configuration.

---

## 📊 Sample Queries for GenIMS Agents

### Asset Management - Predictive Maintenance
```sql
-- RUL (Remaining Useful Life) calculation
WITH bearing_health AS (
    SELECT 
        m.machine_id,
        AVG(sd.measurement_value) as current_vibration,
        (s.critical_threshold_max - AVG(sd.measurement_value)) as margin_to_failure
    FROM sensor_data sd
    JOIN sensors s ON sd.sensor_id = s.sensor_id
    JOIN machines m ON s.machine_id = m.machine_id
    WHERE s.sensor_type = 'vibration'
      AND sd.timestamp > NOW() - INTERVAL '1 hour'
    GROUP BY m.machine_id, s.critical_threshold_max
)
SELECT 
    machine_id,
    current_vibration,
    margin_to_failure,
    CASE 
        WHEN margin_to_failure < 5 THEN '< 24 hours'
        WHEN margin_to_failure < 10 THEN '1-3 days'
        WHEN margin_to_failure < 20 THEN '1-2 weeks'
        ELSE '> 2 weeks'
    END as estimated_rul
FROM bearing_health
WHERE margin_to_failure < 20
ORDER BY margin_to_failure ASC;
```

### Factory Operations - Production Monitoring
```sql
-- Real-time line performance
SELECT 
    l.line_name,
    COUNT(DISTINCT smd.machine_id) as total_machines,
    SUM(CASE WHEN smd.machine_state = 'running' THEN 1 ELSE 0 END) as running_machines,
    AVG(smd.oee_percentage) as avg_oee,
    SUM(smd.parts_produced_shift) as total_parts_produced,
    SUM(smd.parts_rejected_shift) as total_parts_rejected
FROM scada_machine_data smd
JOIN machines m ON smd.machine_id = m.machine_id
JOIN production_lines l ON m.line_id = l.line_id
WHERE smd.timestamp > NOW() - INTERVAL '5 minutes'
GROUP BY l.line_id, l.line_name
ORDER BY avg_oee DESC;
```

---

## 📚 References

- **Fault Patterns**: See `FAULT_PATTERNS.md` for detailed signature characteristics
- **Schema Documentation**: See inline comments in `genims_operational_schema.sql`
- **Master Data**: See `README_GenIMS_Data.md` for factory/machine/sensor setup

---

## 🤝 Support

For questions or issues:
1. Check troubleshooting section above
2. Review daemon logs in `logs/` directory
3. Verify database connectivity and schema
4. Ensure all dependencies are installed

---

**Generated**: December 19, 2025  
**Version**: 1.0  
**Platform**: GenIMS (Generative Industrial Managed Services)  
**Company**: Turinton AI Private Limited
