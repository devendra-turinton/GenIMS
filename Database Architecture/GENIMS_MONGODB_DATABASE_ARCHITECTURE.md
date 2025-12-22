# GenIMS MongoDB Database Architecture
## Time-Series, Logs, and Unstructured Data Strategy

**Document Version**: 1.0  
**Created**: December 22, 2025  
**Last Updated**: December 22, 2025  
**Status**: ✅ APPROVED - Already Implements Maximum Isolation  
**Focus**: MongoDB (1 Database with Multiple Collections - Optimal Design)

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [MongoDB Strategy](#mongodb-strategy)
3. [Database Design](#database-design)
4. [Collection Categories](#collection-categories)
5. [Time-Series Collections](#time-series-collections)
6. [Operational Log Collections](#operational-log-collections)
7. [Unstructured Data Collections](#unstructured-data-collections)
8. [Real-Time Collections](#real-time-collections)
9. [Change Streams](#change-streams)
10. [Connection Configuration](#connection-configuration)
11. [Load Strategy](#load-strategy)
12. [Indexing Strategy](#indexing-strategy)
13. [Maintenance & Operations](#maintenance--operations)
14. [Performance Optimization](#performance-optimization)

---

## Overview

MongoDB serves as the **time-series, logs, and unstructured data layer** for GenIMS. Unlike PostgreSQL (relational) and MySQL (denormalized reporting), MongoDB provides:

- **Flexible Schema** - Handle varying data structures
- **Time-Series Optimization** - High-frequency sensor data storage
- **Natural JSON Storage** - Document-oriented data model
- **Scalability** - Horizontal sharding for massive datasets
- **Real-Time Capabilities** - Change streams for reactive applications

### Key Benefits

✅ **High-Volume Time-Series** - Optimized for 1M+ daily sensor readings  
✅ **Flexible Schema** - Add fields without schema migrations  
✅ **JSON-Native** - Natural fit for IoT/sensor data  
✅ **Change Streams** - Real-time CDC (Change Data Capture)  
✅ **Horizontal Scaling** - Shard by machine_id, timestamp, etc.  
✅ **TTL Indexes** - Automatic data expiration  

### Key Challenges

⚠️ **No ACID Across Collections** - Multi-document ACID limited  
⚠️ **Larger Storage** - Document overhead vs. SQL  
⚠️ **Query Complexity** - Aggregation pipeline learning curve  
⚠️ **Joins Inefficient** - Denormalize or application-level joins  

---

## MongoDB Strategy

### Principle: Single Database with Specialized Collections

GenIMS uses **one MongoDB database** (`genims_production`) with **30+ collections** organized by data type:

```
genims_production (Single Database)
├── Time-Series Collections (Real-time sensor data)
│   ├── sensor_readings
│   ├── scada_events
│   ├── machine_fault_events
│   └── oee_metrics
│
├── Operational Log Collections (System & application logs)
│   ├── system_logs
│   ├── daemon_execution_logs
│   ├── integration_event_log
│   └── error_stack_traces
│
├── Unstructured Data Collections (Documents & files)
│   ├── documents
│   ├── attachments
│   └── file_metadata
│
├── Real-Time Collections (Live updates)
│   ├── notifications
│   ├── messages
│   ├── entity_change_stream
│   └── real_time_metrics
│
└── Analytics Collections (Pre-computed aggregations)
    ├── hourly_machine_summary
    ├── daily_production_summary
    └── monthly_financial_summary
```

### Why Single Database?

✅ **Easier Management** - One connection string  
✅ **Transactions** - Multi-document ACID within single DB  
✅ **Backup/Restore** - Single unit  
✅ **Monitoring** - Centralized stats  

---

## Database Design

### Database Name
```
genims_production
```

### Connection Details
```
Host: 4.213.218.240
Port: 27017
Authentication: MongoDB 4.4+
```

### Database-Level Settings

```javascript
use genims_production

// Set default write concern (acknowledged)
db.setProfilingLevel(1, { slowms: 100 })  // Log queries > 100ms

// Enable change streams
db.adminCommand({ "setFeatureCompatibilityVersion": "4.4" })
```

---

## Collection Categories

### 1. Time-Series Collections (High-frequency data)

**Purpose**: Store high-volume sensor and operational data  
**Write Pattern**: Continuous inserts, no updates  
**Read Pattern**: Time-range queries, aggregations  
**Retention**: 90 days (rolling window)  
**Daily Volume**: 1M+ documents

```
Collections:
- sensor_readings (50K-200K docs/day)
- scada_events (100K-500K docs/day)
- machine_fault_events (1K-10K docs/day)
- oee_metrics (1K-10K docs/day)
```

### 2. Operational Log Collections (System logs)

**Purpose**: Application and system logging  
**Write Pattern**: Continuous inserts, no updates  
**Read Pattern**: Time-range, severity filters, full-text search  
**Retention**: 30 days (rolling window) → Archive to cold storage  
**Daily Volume**: 50K-500K documents

```
Collections:
- system_logs (10K-100K docs/day)
- daemon_execution_logs (1K-10K docs/day)
- integration_event_log (5K-50K docs/day)
- error_stack_traces (1K-10K docs/day)
```

### 3. Unstructured Data Collections (Documents)

**Purpose**: Store document metadata and file references  
**Write Pattern**: Occasional inserts, rare updates  
**Read Pattern**: Search, filter by type/date  
**Retention**: 7 years (immutable)  
**Volume**: 10K-100K documents

```
Collections:
- documents (metadata for PDFs, Excel, contracts)
- attachments (email, ticket attachments)
- file_metadata (file sizes, scanning status)
```

### 4. Real-Time Collections (Live data)

**Purpose**: Current notifications, messages, entity changes  
**Write Pattern**: Continuous inserts  
**Read Pattern**: User-specific queries, change streams  
**Retention**: 30 days (or when read/deleted)  
**Volume**: 10K-100K documents/day

```
Collections:
- notifications (unread messages, alerts)
- messages (user-to-user conversations)
- entity_change_stream (entity state changes)
- real_time_metrics (system health, queue depth)
```

### 5. Analytics Collections (Pre-computed)

**Purpose**: Pre-aggregated data for dashboards  
**Write Pattern**: Batch updates (hourly/daily)  
**Read Pattern**: Simple lookups, no aggregation needed  
**Retention**: 24 months  
**Volume**: 1K-10K documents

```
Collections:
- hourly_machine_summary (summarized OEE)
- daily_production_summary (daily KPIs)
- monthly_financial_summary (financial snapshots)
```

---

## Time-Series Collections

### 1. `sensor_readings` Collection

**High-frequency sensor data from IoT devices**

#### Document Structure

```javascript
{
  _id: ObjectId("65a1b2c3d4e5f6g7h8i9j0k1"),
  machine_id: "M001",
  sensor_id: "TEMP_001",
  sensor_name: "Motor Temperature",
  timestamp: ISODate("2025-12-22T10:30:45.123Z"),
  
  // Reading value
  value: 95.5,
  unit: "°C",
  
  // Status
  status: "normal",  // normal|warning|alarm
  
  // Thresholds
  lower_limit: 20,
  upper_limit: 100,
  warning_threshold: 85,
  
  // Metadata
  sensor_type: "temperature",
  accuracy: 0.5,
  frequency_hz: 10,
  
  // Raw sensor data
  raw_voltage: 4.567,
  calibration_factor: 1.0,
  
  // Additional context
  batch_id: "BATCH_2025_12_22_001",
  shift_id: "SHIFT_A",
  worker_id: "W001",
  
  // TTL: auto-delete after 90 days
  createdAt: ISODate("2025-12-22T10:30:45.123Z")
}
```

#### Indexes

```javascript
// Time-series index (primary query)
db.sensor_readings.createIndex(
  { timestamp: -1, machine_id: 1 },
  { name: "idx_time_machine" }
)

// Single machine time-series
db.sensor_readings.createIndex(
  { machine_id: 1, timestamp: -1 },
  { name: "idx_machine_time" }
)

// Sensor type query
db.sensor_readings.createIndex(
  { sensor_type: 1, timestamp: -1 },
  { name: "idx_sensor_time" }
)

// Status-based queries (alarm detection)
db.sensor_readings.createIndex(
  { status: 1, timestamp: -1 },
  { name: "idx_status_time" }
)

// TTL Index: auto-delete after 90 days
db.sensor_readings.createIndex(
  { createdAt: 1 },
  { expireAfterSeconds: 7776000 }  // 90 days in seconds
)

// Compound for common query pattern
db.sensor_readings.createIndex(
  { machine_id: 1, sensor_type: 1, timestamp: -1 },
  { name: "idx_machine_sensor_time" }
)
```

#### Query Examples

```javascript
// Get last hour of temperature readings for machine M001
db.sensor_readings.find({
  machine_id: "M001",
  sensor_type: "temperature",
  timestamp: { $gte: new Date(ISODate().getTime() - 3600000) }
}).sort({ timestamp: -1 })

// Get all alarm readings in last 24 hours
db.sensor_readings.find({
  status: "alarm",
  timestamp: { $gte: new Date(ISODate().getTime() - 86400000) }
}).sort({ timestamp: -1 })

// Aggregate: average temperature per hour
db.sensor_readings.aggregate([
  {
    $match: {
      machine_id: "M001",
      sensor_type: "temperature",
      timestamp: { $gte: new Date("2025-12-21") }
    }
  },
  {
    $group: {
      _id: {
        $dateToString: { format: "%Y-%m-%d %H:00", date: "$timestamp" }
      },
      avg_temp: { $avg: "$value" },
      max_temp: { $max: "$value" },
      min_temp: { $min: "$value" },
      reading_count: { $sum: 1 }
    }
  },
  { $sort: { _id: -1 } }
])
```

#### Storage Estimate
- **Docs/Day**: 200K (20 machines × 100 sensors × 100 readings/hour)
- **Doc Size**: 500 bytes average
- **Daily Growth**: 100 MB
- **90-Day Retention**: 9 GB
- **Index Size**: 2-3 GB
- **Total**: 12-15 GB

---

### 2. `scada_events` Collection

**SCADA system state changes and OEE metrics**

#### Document Structure

```javascript
{
  _id: ObjectId("65a1b2c3d4e5f6g7h8i9j0k2"),
  machine_id: "M001",
  timestamp: ISODate("2025-12-22T10:30:00Z"),
  
  // Machine state
  state: "running",  // running|idle|fault|maintenance|stopped
  previous_state: "idle",
  state_change_reason: "automatic_start",
  
  // OEE Metrics
  oee_metrics: {
    availability: 92.5,      // % of time running
    performance: 88.3,       // % of planned speed
    quality: 99.2,           // % good quality
    oee_overall: 81.0        // availability × performance × quality
  },
  
  // Production data
  planned_units: 1000,
  actual_units: 918,         // 91.8% of planned
  scrap_units: 8,
  
  // Energy/Performance
  power_consumption_kw: 75.5,
  cycle_time_seconds: 120,
  
  // Status flags
  alarms_active: ["BEARING_TEMP_HIGH", "HYDRAULIC_PRESSURE_LOW"],
  warnings_active: ["MAINTENANCE_OVERDUE"],
  
  // Shift context
  shift_id: "SHIFT_A",
  production_line_id: "LINE_01",
  factory_id: "FAC_01",
  
  // Data quality
  sensor_health: {
    missing_sensors: 0,
    degraded_sensors: 1,
    data_quality_score: 98.5
  },
  
  createdAt: ISODate("2025-12-22T10:30:00Z")
}
```

#### Indexes

```javascript
// Primary time-series query
db.scada_events.createIndex(
  { machine_id: 1, timestamp: -1 },
  { name: "idx_machine_time" }
)

// State change tracking
db.scada_events.createIndex(
  { state: 1, timestamp: -1 },
  { name: "idx_state_time" }
)

// Fault detection (alerts)
db.scada_events.createIndex(
  { "alarms_active.0": 1, timestamp: -1 },
  { sparse: true, name: "idx_alarms_time" }
)

// TTL Index: keep 90 days
db.scada_events.createIndex(
  { createdAt: 1 },
  { expireAfterSeconds: 7776000 }
)

// OEE tracking
db.scada_events.createIndex(
  { machine_id: 1, "oee_metrics.oee_overall": 1, timestamp: -1 },
  { name: "idx_machine_oee" }
)
```

#### Storage Estimate
- **Docs/Day**: 100K (1 event per machine every 10 minutes × 20 machines × 24 hours)
- **Doc Size**: 800 bytes average
- **Daily Growth**: 80 MB
- **90-Day Retention**: 7.2 GB
- **Index Size**: 1-2 GB
- **Total**: 9-11 GB

---

### 3. `machine_fault_events` Collection

**Detected machine faults and anomalies**

#### Document Structure

```javascript
{
  _id: ObjectId("65a1b2c3d4e5f6g7h8i9j0k3"),
  machine_id: "M001",
  fault_id: "FAULT_2025_12_22_001",
  timestamp: ISODate("2025-12-22T10:35:22.456Z"),
  
  // Fault classification
  fault_code: "BEARING_FAIL",
  fault_description: "Bearing temperature exceeds safe operating limit",
  fault_category: "mechanical",  // mechanical|electrical|hydraulic|software
  
  // Severity
  severity: "critical",  // critical|high|medium|low
  immediate_action_required: true,
  estimated_downtime_minutes: 120,
  
  // Root cause detection (AI/ML)
  probable_causes: [
    { cause: "Bearing lubrication degradation", probability: 85 },
    { cause: "Bearing wear", probability: 75 },
    { cause: "Misalignment", probability: 45 }
  ],
  
  // Sensor data at fault time
  sensor_readings_at_fault: {
    temperature: 125.5,
    vibration_rms: 8.5,
    pressure: 65,
    motor_current: 95
  },
  
  // Historical context
  previous_warnings_count: 3,
    days_since_last_maintenance: 45,
    maintenance_history: [
      {
        maintenance_date: ISODate("2025-11-07"),
        type: "preventive",
        work_performed: "Bearing replacement"
      }
    ],
  
  // Recommended action
  recommended_action: "IMMEDIATE SHUTDOWN - Bearing replacement required",
  estimated_repair_cost: 2500,
  spare_parts_required: ["BEARING_ASSEMBLY_001", "SEALS_KIT_001"],
  
  // Status
  status: "detected",  // detected|acknowledged|in_repair|resolved
  acknowledged_by: "TECH_001",
  acknowledged_timestamp: ISODate("2025-12-22T10:36:00Z"),
  
  // Linked data
  work_order_id: null,  // will be populated when WO created
  cmms_ticket_id: null,
  
  createdAt: ISODate("2025-12-22T10:35:22.456Z")
}
```

#### Indexes

```javascript
// Recent faults
db.machine_fault_events.createIndex(
  { timestamp: -1 },
  { name: "idx_recent_faults" }
)

// Machine fault history
db.machine_fault_events.createIndex(
  { machine_id: 1, timestamp: -1 },
  { name: "idx_machine_faults" }
)

// Critical faults (alerts)
db.machine_fault_events.createIndex(
  { severity: 1, timestamp: -1 },
  { name: "idx_severity_time" }
)

// Unresolved faults
db.machine_fault_events.createIndex(
  { status: 1, timestamp: -1 },
  { name: "idx_status_time" }
)

// TTL: keep forever (or longer retention)
// Don't add TTL - faults are important for historical analysis
```

#### Storage Estimate
- **Docs/Day**: 5K (average, varies with machine condition)
- **Doc Size**: 1.5 KB average
- **Daily Growth**: 7.5 MB
- **12-Month Retention**: 2.7 GB
- **Index Size**: 500 MB - 1 GB
- **Total**: 3-4 GB

---

### 4. `oee_metrics` Collection

**Aggregated OEE metrics by hour (pre-calculated)**

#### Document Structure

```javascript
{
  _id: ObjectId("65a1b2c3d4e5f6g7h8i9j0k4"),
  machine_id: "M001",
  production_line_id: "LINE_01",
  factory_id: "FAC_01",
  
  // Time bucket (hourly)
  hour: ISODate("2025-12-22T10:00:00Z"),
  date: "2025-12-22",
  hour_of_day: 10,
  shift_id: "SHIFT_A",
  
  // OEE Components (%)
  availability: 92.5,
  performance: 88.3,
  quality: 99.2,
  oee_overall: 81.0,
  
  // Production
  planned_units: 100,
  actual_units: 91,
  scrap_units: 1,
  rework_units: 2,
  
  // Downtime
  downtime_minutes: 4.5,
  downtime_reason: "tool_change",
  
  // Quality
  defect_rate_percent: 1.1,
  major_defects: 0,
  minor_defects: 1,
  
  // Cost
  material_cost: 450,
  labor_cost: 120,
  overhead_cost: 80,
  total_cost: 650,
  cost_per_unit: 7.15,
  
  // Trends
  vs_previous_hour_percent: -2.5,
  vs_daily_average_percent: +1.2,
  vs_target_percent: -8.0,
  
  // Data quality
  data_completeness_percent: 100,
  anomalies_detected: 0,
  
  // Metadata
  calculated_at: ISODate("2025-12-22T11:05:00Z"),
  calculation_duration_ms: 245,
  
  createdAt: ISODate("2025-12-22T11:05:00Z")
}
```

#### Indexes

```javascript
// Machine hourly OEE
db.oee_metrics.createIndex(
  { machine_id: 1, hour: -1 },
  { name: "idx_machine_hour" }
)

// Line daily summary
db.oee_metrics.createIndex(
  { production_line_id: 1, date: -1 },
  { name: "idx_line_date" }
)

// Factory trending
db.oee_metrics.createIndex(
  { factory_id: 1, date: -1 },
  { name: "idx_factory_date" }
)

// Time-range queries
db.oee_metrics.createIndex(
  { hour: -1 },
  { name: "idx_recent_oee" }
)

// TTL: keep 24 months
db.oee_metrics.createIndex(
  { createdAt: 1 },
  { expireAfterSeconds: 63072000 }  // 24 months
)
```

#### Storage Estimate
- **Docs/Day**: 480 (20 machines × 24 hours)
- **Doc Size**: 800 bytes average
- **Daily Growth**: 384 KB
- **24-Month Retention**: 280 MB
- **Index Size**: 50-100 MB
- **Total**: 400-500 MB

---

## Operational Log Collections

### 1. `system_logs` Collection

**Application and system-level logging**

#### Document Structure

```javascript
{
  _id: ObjectId("65a1b2c3d4e5f6g7h8i9j0k5"),
  timestamp: ISODate("2025-12-22T10:30:45.123Z"),
  
  // Log level
  level: "INFO",  // DEBUG|INFO|WARN|ERROR|CRITICAL
  
  // Source
  module: "MES",  // MES|ERP|WMS|CRM|CMMS|QMS
  class_name: "ProductionOrderService",
  method_name: "updateWorkOrder",
  
  // Message
  message: "Work order WO_001 status updated to IN_PROGRESS",
  message_template: "Work order {order_id} status updated to {status}",
  
  // Context
  context: {
    order_id: "WO_001",
    status: "IN_PROGRESS",
    user_id: "U001",
    session_id: "SESSION_ABC123",
    transaction_id: "TXN_2025_12_22_001",
    request_duration_ms: 125
  },
  
  // Error info (if ERROR/CRITICAL)
  error_code: null,
  error_message: null,
  stack_trace: null,
  
  // Performance
  duration_ms: 125,
  db_queries: 3,
  external_api_calls: 0,
  
  // User/Request
  user_id: "U001",
  ip_address: "192.168.1.100",
  user_agent: "Mozilla/5.0...",
  
  // Environment
  environment: "production",
  version: "1.0.0",
  node_id: "node_01",
  
  // Metadata
  tags: ["audit", "order-management"],
  correlation_id: "CORR_2025_12_22_001",
  
  createdAt: ISODate("2025-12-22T10:30:45.123Z")
}
```

#### Indexes

```javascript
// Recent logs
db.system_logs.createIndex(
  { timestamp: -1 },
  { name: "idx_recent_logs" }
)

// Error/warning queries
db.system_logs.createIndex(
  { level: 1, timestamp: -1 },
  { name: "idx_level_time" }
)

// Module-based filtering
db.system_logs.createIndex(
  { module: 1, timestamp: -1 },
  { name: "idx_module_time" }
)

// User activity tracking
db.system_logs.createIndex(
  { user_id: 1, timestamp: -1 },
  { name: "idx_user_time" }
)

// Text search on message
db.system_logs.createIndex(
  { message: "text", module: 1 },
  { name: "idx_text_search" }
)

// TTL: keep 30 days
db.system_logs.createIndex(
  { createdAt: 1 },
  { expireAfterSeconds: 2592000 }  // 30 days
)
```

#### Storage Estimate
- **Docs/Day**: 100K (normal), 500K (high activity)
- **Doc Size**: 500 bytes average
- **Daily Growth**: 50 MB (normal), 250 MB (high)
- **30-Day Retention**: 1.5-7.5 GB
- **Index Size**: 200-500 MB
- **Total**: 2-8 GB

---

### 2. `daemon_execution_logs` Collection

**Scheduled daemon and background job execution tracking**

#### Document Structure

```javascript
{
  _id: ObjectId("65a1b2c3d4e5f6g7h8i9j0k6"),
  daemon_name: "financial_sync_daemon",
  daemon_id: "DAEMON_FINANCIAL_SYNC_01",
  
  // Execution timing
  execution_id: "EXEC_2025_12_22_10_30_001",
  scheduled_start_time: ISODate("2025-12-22T10:30:00Z"),
  actual_start_time: ISODate("2025-12-22T10:30:02.123Z"),
  actual_end_time: ISODate("2025-12-22T10:30:47.456Z"),
  
  // Duration
  scheduled_duration_ms: 60000,
  actual_duration_ms: 45333,
  delay_ms: 2,
  
  // Execution status
  status: "success",  // success|failed|partial|timeout|skipped
  
  // Data processing
  records_attempted: 500,
  records_processed: 498,
  records_failed: 2,
  records_skipped: 0,
  success_rate_percent: 99.6,
  
  // Performance
  memory_used_mb: 245,
  memory_peak_mb: 312,
  cpu_time_ms: 8500,
  
  // Details
  source_db: "genims_erp_financial_db",
  target_db: "genims_supply_chain_db",
  tables_synced: ["purchase_orders", "inventory_allocations"],
  
  // Error information
  error_count: 0,
  errors: [],
  warnings: [],
  
  // Sample errors (if any)
  sample_failed_records: [
    {
      record_id: "REC_123",
      error_message: "FK constraint violation: supplier_id not found",
      retry_attempted: true
    }
  ],
  
  // Next execution
  next_execution_scheduled: ISODate("2025-12-22T10:35:00Z"),
  
  // Metadata
  version: "1.0.0",
  environment: "production",
  
  createdAt: ISODate("2025-12-22T10:30:47.456Z")
}
```

#### Indexes

```javascript
// Recent executions
db.daemon_execution_logs.createIndex(
  { actual_end_time: -1 },
  { name: "idx_recent_executions" }
)

// Daemon execution history
db.daemon_execution_logs.createIndex(
  { daemon_name: 1, actual_end_time: -1 },
  { name: "idx_daemon_history" }
)

// Failed executions (alerts)
db.daemon_execution_logs.createIndex(
  { status: 1, actual_end_time: -1 },
  { name: "idx_status_time" }
)

// TTL: keep 90 days
db.daemon_execution_logs.createIndex(
  { createdAt: 1 },
  { expireAfterSeconds: 7776000 }  // 90 days
)
```

#### Storage Estimate
- **Docs/Day**: 1K (50+ daemons × 20 executions/day)
- **Doc Size**: 1 KB average
- **Daily Growth**: 1 MB
- **90-Day Retention**: 90 MB
- **Index Size**: 10-20 MB
- **Total**: 120-150 MB

---

### 3. `integration_event_log` Collection

**Cross-system integration events and data flows**

#### Document Structure

```javascript
{
  _id: ObjectId("65a1b2c3d4e5f6g7h8i9j0k7"),
  integration_id: "INT_2025_12_22_001",
  timestamp: ISODate("2025-12-22T10:30:00Z"),
  
  // Systems involved
  source_system: "genims_operations_db",  // PostgreSQL database
  target_system: "genims_manufacturing_db",
  integration_type: "CDC",  // CDC|ETL|API|EVENT
  
  // Event details
  event_type: "machine_state_change",
  entity_type: "machine_status",
  entity_id: "M001",
  
  // Payload (compact version, full payload in separate collection if huge)
  payload_summary: {
    old_state: "idle",
    new_state: "running",
    timestamp: ISODate("2025-12-22T10:30:00Z")
  },
  payload_size_bytes: 512,
  
  // Processing
  status: "success",  // success|failed|pending|retrying
  attempt_number: 1,
  retry_count: 0,
  
  // Timing
  processing_time_ms: 245,
  queue_wait_time_ms: 12,
  network_latency_ms: 18,
  
  // Data quality
  validation_passed: true,
  business_rules_passed: true,
  
  // Error (if failed)
  error_code: null,
  error_message: null,
  failure_reason: null,
  
  // Retry information
  next_retry_time: null,
  max_retries: 3,
  
  // Linked records
  transaction_id: "TXN_2025_12_22_001",
  correlation_id: "CORR_2025_12_22_001",
  
  // Audit
  created_by: "integration_engine",
  environment: "production",
  
  createdAt: ISODate("2025-12-22T10:30:00Z")
}
```

#### Indexes

```javascript
// Recent integrations
db.integration_event_log.createIndex(
  { timestamp: -1 },
  { name: "idx_recent_events" }
)

// Failed integrations (alerts)
db.integration_event_log.createIndex(
  { status: 1, timestamp: -1 },
  { name: "idx_status_time" }
)

// By entity (tracking specific entity changes)
db.integration_event_log.createIndex(
  { entity_type: 1, entity_id: 1, timestamp: -1 },
  { name: "idx_entity_history" }
)

// System pair (track specific integrations)
db.integration_event_log.createIndex(
  { source_system: 1, target_system: 1, timestamp: -1 },
  { name: "idx_system_pair" }
)

// TTL: keep 90 days
db.integration_event_log.createIndex(
  { createdAt: 1 },
  { expireAfterSeconds: 7776000 }  // 90 days
)
```

#### Storage Estimate
- **Docs/Day**: 50K (all integrations across systems)
- **Doc Size**: 600 bytes average
- **Daily Growth**: 30 MB
- **90-Day Retention**: 2.7 GB
- **Index Size**: 300-500 MB
- **Total**: 3-3.5 GB

---

## Unstructured Data Collections

### 1. `documents` Collection

**Document metadata and references (PDFs, Excel, contracts, etc.)**

#### Document Structure

```javascript
{
  _id: ObjectId("65a1b2c3d4e5f6g7h8i9j0k8"),
  document_number: "INV-2025-12-0001",
  document_id: "DOC_INV_2025_12_0001",
  
  // Classification
  document_type: "invoice",  // invoice|po|contract|audit_report|specification|compliance
  entity_type: "supplier_invoice",
  
  // Dates
  document_date: ISODate("2025-12-22"),
  upload_date: ISODate("2025-12-22T10:30:00Z"),
  expiration_date: null,
  retention_until: ISODate("2032-12-22"),  // 7-year retention
  
  // File details
  file_name: "INV-2025-12-0001.pdf",
  file_size_bytes: 1024000,
  file_type: "application/pdf",
  file_path: "/documents/2025/12/22/INV-2025-12-0001.pdf",
  file_hash_sha256: "abc123def456...",
  
  // Source
  source_system: "supplier_portal",
  uploaded_by: "vendor_001",
  
  // Related entities
  supplier_id: "SUP_001",
  po_number: "PO_2025_12_001",
  invoice_amount: 50000,
  
  // Scanning/OCR
  scan_status: "completed",  // pending|in_progress|completed|failed
  ocr_status: "completed",
  ocr_text: "Invoice from XYZ Corp...",
  pages: 5,
  
  // Search/indexing
  tags: ["supplier", "invoice", "december", "processing"],
  keywords: ["materials", "logistics", "urgent"],
  
  // Compliance
  compliance_required: true,
  compliance_status: "verified",
  verified_by: "COMPLIANCE_TEAM",
  verified_date: ISODate("2025-12-22T11:00:00Z"),
  
  // Status
  status: "active",  // active|archived|deleted
  last_accessed: ISODate("2025-12-22T10:45:00Z"),
  access_count: 5,
  
  // Metadata
  version: 1,
  created_at: ISODate("2025-12-22T10:30:00Z"),
  updated_at: ISODate("2025-12-22T11:00:00Z")
}
```

#### Indexes

```javascript
// Document lookup
db.documents.createIndex(
  { document_number: 1 },
  { unique: true, name: "idx_doc_number" }
)

// Document type filtering
db.documents.createIndex(
  { document_type: 1, upload_date: -1 },
  { name: "idx_type_date" }
)

// Text search
db.documents.createIndex(
  { ocr_text: "text", keywords: "text" },
  { name: "idx_text_search" }
)

// Supplier documents
db.documents.createIndex(
  { supplier_id: 1, document_date: -1 },
  { name: "idx_supplier_date" }
)

// Retention policy (find docs to delete)
db.documents.createIndex(
  { retention_until: 1, status: 1 },
  { name: "idx_retention" }
)
```

#### Storage Estimate
- **Docs**: 100K (metadata only, not file content)
- **Doc Size**: 800 bytes average
- **Total**: 80 MB
- **Actual files**: Stored separately in S3/Blob storage

---

## Real-Time Collections

### 1. `notifications` Collection

**User notifications and alerts**

#### Document Structure

```javascript
{
  _id: ObjectId("65a1b2c3d4e5f6g7h8i9j0k9"),
  notification_id: "NOTIF_2025_12_22_001",
  recipient_id: "U001",
  
  // Notification content
  type: "alert",  // alert|info|warning|urgent
  category: "machine_fault",
  title: "Critical: Machine M001 bearing temperature high",
  body: "Motor bearing temperature has exceeded safe limit. Immediate action required.",
  
  // Related entity
  entity_type: "machine",
  entity_id: "M001",
  related_id: "FAULT_2025_12_22_001",
  
  // Priority
  priority: "critical",  // critical|high|normal|low
  urgency_level: 1,  // 1=critical, 5=low
  
  // Timing
  created_at: ISODate("2025-12-22T10:35:22Z"),
  
  // Status
  read: false,
  read_at: null,
  
  // Action
  action_url: "/machines/M001/faults",
  action_required: true,
  action_type: "navigate_to_fault",
  
  // Delivery
  delivery_channels: ["in_app", "email", "sms"],
  email_sent: false,
  sms_sent: false,
  
  // Expiration
  expires_at: ISODate("2025-12-23T10:35:22Z"),  // 24 hour expiry
  
  // Metadata
  source_system: "CMMS",
  created_by: "fault_detection_engine",
  
  createdAt: ISODate("2025-12-22T10:35:22Z")
}
```

#### Indexes

```javascript
// User's unread notifications
db.notifications.createIndex(
  { recipient_id: 1, read: 1, created_at: -1 },
  { name: "idx_user_unread" }
)

// Recent notifications (for dashboard)
db.notifications.createIndex(
  { created_at: -1 },
  { name: "idx_recent" }
)

// Expiration (for cleanup)
db.notifications.createIndex(
  { expires_at: 1 },
  { name: "idx_expiration" }
)

// TTL: auto-delete expired notifications
db.notifications.createIndex(
  { expires_at: 1 },
  { expireAfterSeconds: 0 }  // Delete at expires_at time
)
```

#### Storage Estimate
- **Docs/Day**: 50K (new notifications)
- **Doc Size**: 400 bytes average
- **Daily Growth**: 20 MB
- **30-Day Retention**: 600 MB
- **Total**: 1 GB

---

## Change Streams

### 1. `entity_change_stream` Collection

**Real-time entity state changes (alternative to MongoDB change streams)**

#### Document Structure

```javascript
{
  _id: ObjectId("65a1b2c3d4e5f6g7h8i9j0ka"),
  
  // Entity reference
  entity_type: "sales_order",  // Entity type being tracked
  entity_id: "SO_2025_12_0001",  // Entity ID
  
  // Change details
  operation: "update",  // insert|update|delete
  change_timestamp: ISODate("2025-12-22T10:30:00Z"),
  
  // Changed fields
  changes: {
    status: {
      old_value: "draft",
      new_value: "submitted",
      changed: true
    },
    total_amount: {
      old_value: 10000,
      new_value: 10500,
      changed: true
    },
    updated_at: {
      old_value: ISODate("2025-12-22T09:00:00Z"),
      new_value: ISODate("2025-12-22T10:30:00Z"),
      changed: true
    }
  },
  
  // Change context
  changed_by: "U001",
  change_reason: "Customer requested additional items",
  
  // Related entities affected
  related_entities: [
    { type: "customer", id: "CUST_001" },
    { type: "sales_rep", id: "REP_001" }
  ],
  
  // Propagation status
  sync_status: {
    "genims_reporting_db": { status: "synced", timestamp: ISODate("2025-12-22T10:30:05Z") },
    "genims_audit_db": { status: "synced", timestamp: ISODate("2025-12-22T10:30:06Z") }
  },
  
  // Metadata
  source_db: "genims_erp_financial_db",
  version: 1,
  
  createdAt: ISODate("2025-12-22T10:30:00Z")
}
```

#### Indexes

```javascript
// Track entity changes
db.entity_change_stream.createIndex(
  { entity_type: 1, entity_id: 1, change_timestamp: -1 },
  { name: "idx_entity_history" }
)

// Recent changes (for sync)
db.entity_change_stream.createIndex(
  { change_timestamp: -1 },
  { name: "idx_recent_changes" }
)

// By operation type
db.entity_change_stream.createIndex(
  { operation: 1, change_timestamp: -1 },
  { name: "idx_operation_time" }
)

// TTL: keep 30 days
db.entity_change_stream.createIndex(
  { createdAt: 1 },
  { expireAfterSeconds: 2592000 }  // 30 days
)
```

---

## Connection Configuration

### Environment Variables (.env)

```bash
# MongoDB Connection
MONGODB_HOST=4.213.218.240
MONGODB_PORT=27017
MONGODB_DATABASE=genims_production
MONGODB_USERNAME=root
MONGODB_PASSWORD=turitonadmin65#$%
MONGODB_AUTH_SOURCE=admin

# Connection pool settings
MONGODB_MAX_POOL_SIZE=50
MONGODB_MIN_POOL_SIZE=10
MONGODB_MAX_CONNECTION_IDLE_TIME=30000
MONGODB_SOCKET_TIMEOUT=30000

# Replica set (if used)
MONGODB_REPLICA_SET=rs0
```

### Connection Strings

```
MongoDB Standard: mongodb://user:password@host:port/database
Example: mongodb://root:turitonadmin65#$%@4.213.218.240:27017/genims_production

With Auth Source: mongodb://root:turitonadmin65#$%@4.213.218.240:27017/genims_production?authSource=admin

Connection Options:
mongodb://root:turitonadmin65#$%@4.213.218.240:27017/genims_production?
  retryWrites=true&
  w=majority&
  maxPoolSize=50&
  minPoolSize=10&
  serverSelectionTimeoutMS=5000&
  socketTimeoutMS=30000
```

### Python Connection Example

```python
from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError
import os

# Create connection
client = MongoClient(
    host=os.getenv('MONGODB_HOST'),
    port=int(os.getenv('MONGODB_PORT')),
    username=os.getenv('MONGODB_USERNAME'),
    password=os.getenv('MONGODB_PASSWORD'),
    authSource=os.getenv('MONGODB_AUTH_SOURCE', 'admin'),
    maxPoolSize=int(os.getenv('MONGODB_MAX_POOL_SIZE', 50)),
    minPoolSize=int(os.getenv('MONGODB_MIN_POOL_SIZE', 10)),
    socketTimeoutMS=int(os.getenv('MONGODB_SOCKET_TIMEOUT', 30000))
)

# Select database
db = client[os.getenv('MONGODB_DATABASE')]

# Access collections
sensor_readings = db.sensor_readings
scada_events = db.scada_events
system_logs = db.system_logs
```

---

## Load Strategy

### Phase 1: Database Connection (2 minutes)

```bash
# Test connection
mongo --host 4.213.218.240 --port 27017 \
  --username root --password 'turitonadmin65#$%' \
  --authenticationDatabase admin \
  --eval "db.adminCommand('ping')"
```

### Phase 2: Database & Collection Creation (5 minutes)

```javascript
use genims_production

// Create collections with validation
db.createCollection("sensor_readings", {
  validator: {
    $jsonSchema: {
      bsonType: "object",
      required: ["machine_id", "sensor_id", "timestamp", "value"],
      properties: {
        machine_id: { bsonType: "string" },
        sensor_id: { bsonType: "string" },
        timestamp: { bsonType: "date" },
        value: { bsonType: "double" },
        status: { enum: ["normal", "warning", "alarm"] }
      }
    }
  }
})

db.createCollection("scada_events", {
  timeseries: {
    timeField: "timestamp",
    metaField: "metadata",
    granularity: "minutes"
  }
})

// ... create other collections
```

### Phase 3: Initial Data Load (15 minutes)

```bash
# Load historical sensor data (last 90 days)
python3 scripts/initial_load_mongodb_sensor_data.py \
  --days 90 \
  --machines all \
  --sensors all \
  --target genims_production

# Load operational logs
python3 scripts/initial_load_mongodb_logs.py \
  --days 30 \
  --target genims_production
```

### Phase 4: Create Indexes (5 minutes)

```bash
# Run index creation script
python3 scripts/create_mongodb_indexes.py \
  --database genims_production \
  --collections all
```

### Phase 5: Start Change Streams (3 minutes)

```bash
# Start listening to PostgreSQL and writing to MongoDB
python3 scripts/postgres_mongodb_sync.py --mode daemon > logs/pg_mongo_sync.log 2>&1 &

# Start real-time metrics aggregation
python3 scripts/realtime_metrics_aggregation.py --mode daemon > logs/metrics_agg.log 2>&1 &
```

### Phase 6: Verify Load (5 minutes)

```bash
# Verify collections created
mongo --host 4.213.218.240 --port 27017 \
  --username root --password 'turitonadmin65#$%' \
  --authenticationDatabase admin \
  --eval "db.getCollectionNames()"

# Verify data loaded
mongo --host 4.213.218.240 --port 27017 \
  --username root --password 'turitonadmin65#$%' \
  --authenticationDatabase admin \
  --eval "db.sensor_readings.count()"

mongo --host 4.213.218.240 --port 27017 \
  --username root --password 'turitonadmin65#$%' \
  --authenticationDatabase admin \
  --eval "db.scada_events.count()"
```

---

## Indexing Strategy

### Time-Series Collection Indexes

All time-series collections should follow this pattern:

```javascript
// 1. Primary query pattern: machine_id + timestamp
db.collection.createIndex({ machine_id: 1, timestamp: -1 })

// 2. Status/severity filtering
db.collection.createIndex({ status: 1, timestamp: -1 })

// 3. Sensor type filtering
db.collection.createIndex({ sensor_type: 1, timestamp: -1 })

// 4. TTL for automatic cleanup
db.collection.createIndex({ createdAt: 1 }, { expireAfterSeconds: 7776000 })
```

### Log Collection Indexes

All log collections should follow this pattern:

```javascript
// 1. Recent logs
db.collection.createIndex({ timestamp: -1 })

// 2. Level/severity filtering
db.collection.createIndex({ level: 1, timestamp: -1 })

// 3. Text search
db.collection.createIndex({ message: "text", module: 1 })

// 4. TTL for automatic cleanup
db.collection.createIndex({ createdAt: 1 }, { expireAfterSeconds: 2592000 })
```

### Index Monitoring

```bash
# Check index usage
python3 scripts/monitor_mongodb_indexes.py

# Rebuild fragmented indexes
db.collection.reIndex()

# Check index size
db.collection.stats().indexSizes
```

---

## Maintenance & Operations

### Daily Tasks

```bash
# Monitor collection sizes
mongo --host 4.213.218.240 --port 27017 \
  --username root --password 'turitonadmin65#$%' \
  --authenticationDatabase admin \
  --eval "db.sensor_readings.stats().size"

# Check index efficiency
mongo --host 4.213.218.240 --port 27017 \
  --username root --password 'turitonadmin65#$%' \
  --authenticationDatabase admin \
  --eval "db.sensor_readings.aggregate([{ \$indexStats: {} }])"

# Monitor sync lag
python3 scripts/monitor_postgres_mongodb_sync.py

# Check daemon health
ps aux | grep "mongodb"
```

### Weekly Tasks

```bash
# Analyze query performance
python3 scripts/analyze_mongodb_queries.py \
  --database genims_production \
  --slow-threshold 100  # queries > 100ms

# Rebuild indexes if fragmented
python3 scripts/rebuild_fragmented_indexes.py

# Verify data integrity
python3 scripts/verify_mongodb_data_integrity.py
```

### Monthly Tasks

```bash
# Full backup
mongodump --host 4.213.218.240 --port 27017 \
  --username root --password 'turitonadmin65#$%' \
  --authenticationDatabase admin \
  --db genims_production \
  --out /backups/mongodb/$(date +%Y%m%d)

# Archive old sensor data (if needed)
# Move data older than 90 days to cold storage
python3 scripts/archive_old_sensor_data.py \
  --days-threshold 90 \
  --target-storage s3://cold-archive

# Compact collections
python3 scripts/compact_mongodb_collections.py

# Generate compliance report
python3 scripts/mongodb_compliance_report.py \
  --format pdf \
  --output /reports/mongodb_compliance_$(date +%Y%m).pdf
```

### Backup Strategy

| Collection | Frequency | Retention | Location |
|------------|-----------|-----------|----------|
| `sensor_readings` | Daily | 90 days | Hot storage |
| `scada_events` | Daily | 90 days | Hot storage |
| `system_logs` | Daily | 30 days | Hot storage |
| `documents` | Daily | 7 years | Cold archive |
| Others | Daily | 30 days | Hot storage |

```bash
#!/bin/bash
# Automated MongoDB backup script

BACKUP_DIR="/backups/mongodb"
DATE=$(date +%Y%m%d_%H%M%S)
MONGODB_HOST="4.213.218.240"
MONGODB_PORT="27017"
MONGODB_USER="root"
MONGODB_PASSWORD="turitonadmin65#$%"

# Full backup
mongodump --host $MONGODB_HOST --port $MONGODB_PORT \
  --username $MONGODB_USER --password $MONGODB_PASSWORD \
  --authenticationDatabase admin \
  --db genims_production \
  --out $BACKUP_DIR/genims_full_$DATE

# Compress
tar -czf $BACKUP_DIR/genims_full_$DATE.tar.gz $BACKUP_DIR/genims_full_$DATE
rm -rf $BACKUP_DIR/genims_full_$DATE

# Upload to Azure
az storage blob upload --file $BACKUP_DIR/genims_full_$DATE.tar.gz \
  --container-name genims-backups \
  --name mongodb/genims_full_$DATE.tar.gz

# Clean up local backups older than 30 days
find $BACKUP_DIR -name "*.tar.gz" -mtime +30 -delete

echo "Backup completed: $DATE"
```

---

## Performance Optimization

### Query Optimization

```javascript
// Use covered queries (index contains all fields)
db.sensor_readings.find(
  { machine_id: "M001", timestamp: { $gte: new Date("2025-12-21") } },
  { _id: 0, machine_id: 1, timestamp: 1, value: 1 }  // Only fields in index
).hint({ machine_id: 1, timestamp: -1 })

// Use aggregation pipeline for complex queries
db.sensor_readings.aggregate([
  { $match: { machine_id: "M001", timestamp: { $gte: new Date("2025-12-21") } } },
  { $group: { _id: "$sensor_type", avg_value: { $avg: "$value" } } },
  { $sort: { _id: 1 } }
])
```

### Data Archival Strategy

```javascript
// Archive sensor data older than 90 days
// Move to archive collection with TTL

db.createCollection("sensor_readings_archive", {
  validator: {
    $jsonSchema: {
      bsonType: "object",
      properties: {
        timestamp: { bsonType: "date" }
      }
    }
  }
})

// Automatically delete archive data after 7 years
db.sensor_readings_archive.createIndex(
  { createdAt: 1 },
  { expireAfterSeconds: 220752000 }  // 7 years
)

// Copy old data to archive
db.sensor_readings.aggregate([
  { $match: { timestamp: { $lt: new Date(ISODate().getTime() - 7776000000) } } },  // > 90 days old
  { $out: "sensor_readings_archive" }
])

// Delete from active collection
db.sensor_readings.deleteMany({
  timestamp: { $lt: new Date(ISODate().getTime() - 7776000000) }
})
```

### Sharding Strategy (for very large deployments)

```javascript
// Enable sharding on time-series data
sh.enableSharding("genims_production")

// Shard by machine_id + timestamp for better distribution
db.sensor_readings.createIndex({ machine_id: 1, timestamp: 1 })
sh.shardCollection("genims_production.sensor_readings", 
  { machine_id: 1, timestamp: 1 })

// Shard logs by timestamp
sh.shardCollection("genims_production.system_logs",
  { timestamp: 1 })
```

---

## Data Volume Estimates

### Collection Growth Rates

| Collection | Docs/Day | Doc Size | Daily Growth | 90-Day Size | 12-Month Size |
|------------|----------|----------|--------------|-------------|---------------|
| sensor_readings | 200K | 500 B | 100 MB | 9 GB | 36 GB |
| scada_events | 100K | 800 B | 80 MB | 7.2 GB | 28.8 GB |
| machine_fault_events | 5K | 1.5 KB | 7.5 MB | 675 MB | 2.7 GB |
| system_logs | 100K | 500 B | 50 MB | 4.5 GB | 18 GB |
| daemon_exec_logs | 1K | 1 KB | 1 MB | 90 MB | 360 MB |
| integration_logs | 50K | 600 B | 30 MB | 2.7 GB | 10.8 GB |
| **TOTAL** | **456K** | **avg 700B** | **268.5 MB** | **~24 GB** | **~97 GB** |

### Index Storage Estimate

- **Indexes**: 20-30% of data size
- **Total with Indexes**: 24-35 GB (90-day retention)
- **With 12-month retention**: 115-130 GB

---

## Summary

### Key Metrics

| Metric | Value |
|--------|-------|
| **Total MongoDB Database** | 1 |
| **Total Collections** | 30+ |
| **Estimated Initial Size** | 24-35 GB (90-day retention) |
| **Daily Growth** | 250-300 MB |
| **Annual Growth** | ~97 GB |
| **TTL Collections** | 8 (auto-cleanup) |
| **Sync Frequency** | Real-time + hourly batches |

### Implementation Checklist

- [ ] Verify MongoDB connection
- [ ] Create `genims_production` database
- [ ] Create 30+ collections with validation
- [ ] Create all indexes
- [ ] Load initial historical data
- [ ] Start PostgreSQL → MongoDB sync daemon
- [ ] Start real-time metrics aggregation
- [ ] Verify data freshness
- [ ] Test TTL cleanup
- [ ] Configure backup automation
- [ ] Set up monitoring
- [ ] Document retention policies

### Estimated Timeline

- **Phase 1**: Connection test → 2 min
- **Phase 2**: Create DB & collections → 5 min
- **Phase 3**: Initial data load → 15 min
- **Phase 4**: Create indexes → 5 min
- **Phase 5**: Start sync daemons → 3 min
- **Phase 6**: Verification → 5 min
- **TOTAL** → **35 minutes**

---

## Next Steps

1. **Configure connection** - Update .env with MongoDB credentials
2. **Create database** - Run database creation scripts
3. **Create collections** - Execute collection creation with validation
4. **Load indexes** - Build all recommended indexes
5. **Load initial data** - 90 days of historical data
6. **Start sync** - Activate PostgreSQL → MongoDB sync
7. **Verify** - Check data freshness and completeness
8. **Monitor** - Set up real-time monitoring
9. **Backup** - Test backup/restore procedures
10. **Document** - Update runbooks with MongoDB procedures

---

**Document Status**: Ready for Implementation  
**Last Updated**: December 22, 2025  
**Total Estimated Setup Time**: 35 minutes (+ initial data transfer time based on volume)
