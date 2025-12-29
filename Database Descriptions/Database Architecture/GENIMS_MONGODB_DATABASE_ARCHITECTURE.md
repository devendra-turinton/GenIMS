# GenIMS MongoDB Database Architecture

**Document Version**: 2.0  
**Updated**: December 23, 2025  
**Status**: ✅ PRODUCTION-READY  

MongoDB stores time-series, operational logs, and unstructured data. Single database (`genims_production`) with 30+ specialized collections.

---

## Quick Reference

| Metric | Value |
|--------|-------|
| **Database** | genims_production |
| **Host** | 4.213.218.240 |
| **Port** | 27017 |
| **Collections** | 30+ |
| **Initial Size** | 24-35 GB (90-day retention) |
| **Daily Growth** | 250-300 MB |
| **Annual Growth** | ~97 GB |
| **Sync Frequency** | Real-time + hourly |

---

## Collections Overview

| Category | Collections | Daily Docs | Retention |
|----------|-------------|-----------|-----------|
| **Time-Series** | sensor_readings, scada_events, machine_fault_events, oee_metrics | 305K | 90 days |
| **Operational Logs** | system_logs, daemon_execution_logs, integration_event_log, error_stack_traces | 156K | 30 days |
| **Unstructured** | documents, attachments, file_metadata | 100K | 7 years |
| **Real-Time** | notifications, messages, entity_change_stream | 60K | 30 days |
| **Analytics** | hourly_machine_summary, daily_production_summary, monthly_financial_summary | 2.5K | 24 months |
| **TOTAL** | **30+** | **~620K** | **varies** |

---

## Connection Configuration

### Environment Variables (.env)

```bash
MONGODB_HOST=4.213.218.240
MONGODB_PORT=27017
MONGODB_DATABASE=genims_production
MONGODB_USERNAME=root
MONGODB_PASSWORD=turitonadmin65#$%
MONGODB_AUTH_SOURCE=admin
MONGODB_MAX_POOL_SIZE=50
MONGODB_MIN_POOL_SIZE=10
```

### Connection String

```
mongodb://root:turitonadmin65#$%@4.213.218.240:27017/genims_production?
  authSource=admin&
  retryWrites=true&
  w=majority&
  maxPoolSize=50&
  socketTimeoutMS=30000
```

### Python Connection

```python
from pymongo import MongoClient

client = MongoClient(
    host=os.getenv('MONGODB_HOST'),
    port=int(os.getenv('MONGODB_PORT')),
    username=os.getenv('MONGODB_USERNAME'),
    password=os.getenv('MONGODB_PASSWORD'),
    authSource=os.getenv('MONGODB_AUTH_SOURCE'),
    maxPoolSize=50
)

db = client['genims_production']
```

---

## Time-Series Collections

**Purpose**: High-frequency sensor and operational data

### 1. `sensor_readings`
- **Docs/Day**: 200K  
- **Doc Size**: 500 B  
- **Retention**: 90 days (TTL auto-delete)  
- **Sample Field**: machine_id, sensor_type, timestamp, value, status

**Indexes**:
```javascript
db.sensor_readings.createIndex({ machine_id: 1, timestamp: -1 })
db.sensor_readings.createIndex({ sensor_type: 1, timestamp: -1 })
db.sensor_readings.createIndex({ status: 1, timestamp: -1 })
db.sensor_readings.createIndex({ createdAt: 1 }, { expireAfterSeconds: 7776000 })
```

### 2. `scada_events`
- **Docs/Day**: 100K  
- **Doc Size**: 800 B  
- **Retention**: 90 days  
- **Sample Field**: machine_id, timestamp, state, oee_metrics, alarms_active

**Indexes**:
```javascript
db.scada_events.createIndex({ machine_id: 1, timestamp: -1 })
db.scada_events.createIndex({ state: 1, timestamp: -1 })
db.scada_events.createIndex({ createdAt: 1 }, { expireAfterSeconds: 7776000 })
```

### 3. `machine_fault_events`
- **Docs/Day**: 5K  
- **Doc Size**: 1.5 KB  
- **Retention**: Forever (fault history important)  
- **Sample Field**: machine_id, fault_code, severity, timestamp, recommended_action

**Indexes**:
```javascript
db.machine_fault_events.createIndex({ machine_id: 1, timestamp: -1 })
db.machine_fault_events.createIndex({ severity: 1, timestamp: -1 })
db.machine_fault_events.createIndex({ status: 1, timestamp: -1 })
```

### 4. `oee_metrics`
- **Docs/Day**: 480 (20 machines × 24 hours)  
- **Doc Size**: 800 B  
- **Retention**: 24 months  
- **Sample Field**: machine_id, hour, availability, performance, quality, oee_overall

**Indexes**:
```javascript
db.oee_metrics.createIndex({ machine_id: 1, hour: -1 })
db.oee_metrics.createIndex({ production_line_id: 1, date: -1 })
db.oee_metrics.createIndex({ createdAt: 1 }, { expireAfterSeconds: 63072000 })
```

---

## Operational Log Collections

**Purpose**: Application and system logging

### 1. `system_logs`
- **Docs/Day**: 50-500K (varies with activity)  
- **Doc Size**: 500 B  
- **Retention**: 30 days (TTL)  
- **Sample Field**: timestamp, level, module, message, user_id, context

**Indexes**:
```javascript
db.system_logs.createIndex({ timestamp: -1 })
db.system_logs.createIndex({ level: 1, timestamp: -1 })
db.system_logs.createIndex({ module: 1, timestamp: -1 })
db.system_logs.createIndex({ message: "text" })
db.system_logs.createIndex({ createdAt: 1 }, { expireAfterSeconds: 2592000 })
```

### 2. `daemon_execution_logs`
- **Docs/Day**: 1K  
- **Doc Size**: 1 KB  
- **Retention**: 90 days  
- **Sample Field**: daemon_name, execution_id, status, records_processed, duration_ms

**Indexes**:
```javascript
db.daemon_execution_logs.createIndex({ daemon_name: 1, actual_end_time: -1 })
db.daemon_execution_logs.createIndex({ status: 1, actual_end_time: -1 })
db.daemon_execution_logs.createIndex({ createdAt: 1 }, { expireAfterSeconds: 7776000 })
```

### 3. `integration_event_log`
- **Docs/Day**: 50K  
- **Doc Size**: 600 B  
- **Retention**: 90 days  
- **Sample Field**: source_system, target_system, event_type, status, timestamp

**Indexes**:
```javascript
db.integration_event_log.createIndex({ timestamp: -1 })
db.integration_event_log.createIndex({ status: 1, timestamp: -1 })
db.integration_event_log.createIndex({ entity_type: 1, entity_id: 1, timestamp: -1 })
db.integration_event_log.createIndex({ createdAt: 1 }, { expireAfterSeconds: 7776000 })
```

---

## Unstructured Data Collections

### 1. `documents`
- **Docs**: 100K (metadata only, files in S3/Blob)  
- **Doc Size**: 800 B  
- **Retention**: 7 years  
- **Sample Field**: document_number, document_type, upload_date, file_name, file_size_bytes, ocr_text

**Indexes**:
```javascript
db.documents.createIndex({ document_number: 1 }, { unique: true })
db.documents.createIndex({ document_type: 1, upload_date: -1 })
db.documents.createIndex({ ocr_text: "text", keywords: "text" })
db.documents.createIndex({ supplier_id: 1, document_date: -1 })
```

---

## Real-Time Collections

### 1. `notifications`
- **Docs/Day**: 50K  
- **Doc Size**: 400 B  
- **Retention**: 30 days (expires_at TTL)  
- **Sample Field**: recipient_id, type, title, body, priority, read, created_at

**Indexes**:
```javascript
db.notifications.createIndex({ recipient_id: 1, read: 1, created_at: -1 })
db.notifications.createIndex({ expires_at: 1 }, { expireAfterSeconds: 0 })
```

### 2. `entity_change_stream`
- **Docs/Day**: 100K  
- **Doc Size**: 600 B  
- **Retention**: 30 days  
- **Sample Field**: entity_type, entity_id, operation, changes, changed_by, change_timestamp

**Indexes**:
```javascript
db.entity_change_stream.createIndex({ entity_type: 1, entity_id: 1, change_timestamp: -1 })
db.entity_change_stream.createIndex({ change_timestamp: -1 })
db.entity_change_stream.createIndex({ createdAt: 1 }, { expireAfterSeconds: 2592000 })
```

---

## Setup & Configuration

### Phase 1: Connection Test (2 min)

```bash
mongo --host 4.213.218.240 --port 27017 \
  --username root --password 'turitonadmin65#$%' \
  --authenticationDatabase admin \
  --eval "db.adminCommand('ping')"
```

### Phase 2: Create Database & Collections (5 min)

```bash
python3 scripts/create_mongodb_collections.py \
  --host 4.213.218.240 \
  --port 27017 \
  --database genims_production
```

### Phase 3: Load Indexes (5 min)

```bash
python3 scripts/create_mongodb_indexes.py \
  --database genims_production \
  --collections all
```

### Phase 4: Initial Data Load (15 min)

```bash
python3 scripts/initial_load_mongodb.py \
  --mode full-load \
  --days 90
```

### Phase 5: Start Sync Daemons (3 min)

```bash
python3 scripts/postgres_mongodb_sync.py --mode daemon > logs/pg_mongo_sync.log 2>&1 &
python3 scripts/realtime_metrics_aggregation.py --mode daemon > logs/metrics_agg.log 2>&1 &
```

### Phase 6: Verification (5 min)

```bash
mongo --host 4.213.218.240 --port 27017 \
  --username root --password 'turitonadmin65#$%' \
  --authenticationDatabase admin \
  --eval "db.getCollectionNames()"

mongo --host 4.213.218.240 --port 27017 \
  --username root --password 'turitonadmin65#$%' \
  --authenticationDatabase admin \
  --eval "db.sensor_readings.countDocuments()"
```

---

## Verification Commands

```bash
# Database size
mongo --host 4.213.218.240 --port 27017 \
  --username root --password 'turitonadmin65#$%' \
  --authenticationDatabase admin \
  --eval "db.stats()"

# Collection counts
mongo --host 4.213.218.240 --port 27017 \
  --username root --password 'turitonadmin65#$%' \
  --authenticationDatabase admin \
  --eval "db.getCollectionNames().forEach(c => print(c + ': ' + db[c].countDocuments()))"

# Recent sensor data
mongo --host 4.213.218.240 --port 27017 \
  --username root --password 'turitonadmin65#$%' \
  --authenticationDatabase admin \
  --eval "db.sensor_readings.findOne({}, {sort: {timestamp: -1}})"
```

---

## Maintenance & Operations

### Daily

```bash
# Monitor collection sizes
mongo --host 4.213.218.240 --port 27017 \
  --username root --password 'turitonadmin65#$%' \
  --authenticationDatabase admin \
  --eval "db.sensor_readings.stats().size"

# Check daemon health
ps aux | grep "postgres_mongodb_sync"
ps aux | grep "realtime_metrics"

# Monitor sync lag
python3 scripts/monitor_mongodb_sync.py --lag-threshold 60
```

### Weekly

```bash
# Analyze query performance
python3 scripts/analyze_mongodb_queries.py --slow-threshold 100

# Check index efficiency
mongo --host 4.213.218.240 --port 27017 \
  --username root --password 'turitonadmin65#$%' \
  --authenticationDatabase admin \
  --eval "db.sensor_readings.aggregate([{\$indexStats: {}}])"

# Verify TTL cleanup
mongo --host 4.213.218.240 --port 27017 \
  --username root --password 'turitonadmin65#$%' \
  --authenticationDatabase admin \
  --eval "db.system_logs.stats().count"
```

### Monthly

```bash
# Full backup
mongodump --host 4.213.218.240 --port 27017 \
  --username root --password 'turitonadmin65#$%' \
  --authenticationDatabase admin \
  --db genims_production \
  --out /backups/mongodb/$(date +%Y%m%d)

# Archive old sensor data
python3 scripts/archive_mongodb_data.py \
  --collection sensor_readings \
  --days-threshold 90

# Compact collections
db.runCommand({ compact: 'sensor_readings' })
db.runCommand({ compact: 'scada_events' })

# Generate compliance report
python3 scripts/mongodb_compliance_report.py \
  --output /reports/mongodb_compliance_$(date +%Y%m).pdf
```

### Backup Strategy

| Collection | Frequency | Retention | Location |
|------------|-----------|-----------|----------|
| Time-Series | Daily | 90 days | Hot |
| Operational Logs | Daily | 30 days | Hot |
| Unstructured | Daily | 7 years | Cold Archive |
| Real-Time | Daily | 30 days | Hot |

```bash
#!/bin/bash
BACKUP_DIR="/backups/mongodb"
DATE=$(date +%Y%m%d_%H%M%S)

mongodump --host 4.213.218.240 --port 27017 \
  --username root --password 'turitonadmin65#$%' \
  --authenticationDatabase admin \
  --db genims_production \
  --out $BACKUP_DIR/genims_$DATE

tar -czf $BACKUP_DIR/genims_$DATE.tar.gz $BACKUP_DIR/genims_$DATE
rm -rf $BACKUP_DIR/genims_$DATE

az storage blob upload --file $BACKUP_DIR/genims_$DATE.tar.gz \
  --container-name genims-backups \
  --name mongodb/genims_$DATE.tar.gz

find $BACKUP_DIR -name "*.tar.gz" -mtime +30 -delete
```

---

## Query Examples

```javascript
// Get last hour of sensor readings
db.sensor_readings.find({
  machine_id: "M001",
  timestamp: { $gte: new Date(Date.now() - 3600000) }
}).sort({ timestamp: -1 }).limit(100)

// Get all active alarms
db.scada_events.find({
  "alarms_active": { $exists: true, $ne: [] },
  timestamp: { $gte: new Date(Date.now() - 86400000) }
}).sort({ timestamp: -1 })

// Aggregate: Average temperature per hour
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
      _id: { $dateToString: { format: "%Y-%m-%d %H:00", date: "$timestamp" } },
      avg_temp: { $avg: "$value" },
      max_temp: { $max: "$value" },
      min_temp: { $min: "$value" }
    }
  },
  { $sort: { _id: -1 } }
])

// Get recent system errors
db.system_logs.find({
  level: "ERROR",
  timestamp: { $gte: new Date(Date.now() - 86400000) }
}).sort({ timestamp: -1 })

// Find unresolved faults
db.machine_fault_events.find({
  status: { $in: ["detected", "acknowledged"] },
  severity: "critical"
}).sort({ timestamp: -1 })
```

---

## Data Volume Estimates

### Daily Growth

| Collection | Docs/Day | Doc Size | Daily Growth |
|------------|----------|----------|--------------|
| sensor_readings | 200K | 500 B | 100 MB |
| scada_events | 100K | 800 B | 80 MB |
| machine_fault_events | 5K | 1.5 KB | 7.5 MB |
| system_logs | 100K | 500 B | 50 MB |
| daemon_exec_logs | 1K | 1 KB | 1 MB |
| integration_logs | 50K | 600 B | 30 MB |
| **TOTAL** | **~456K** | **~700B avg** | **~268.5 MB** |

### Storage by Retention

| Retention Period | Size | Collections |
|-----------------|------|-------------|
| 90 Days (Hot) | 24-28 GB | sensor_readings, scada_events, daemon_logs, integration_logs |
| 30 Days (Hot) | 8-12 GB | system_logs, notifications, real_time |
| 24 Months | 2-3 GB | oee_metrics, analytics |
| 7 Years | 10-15 GB | documents |
| **TOTAL WITH INDEXES** | **45-60 GB** | All |

---

## Summary

| Metric | Value |
|--------|-------|
| **Database** | 1 (genims_production) |
| **Collections** | 30+ |
| **Initial Size (90-day)** | 24-35 GB |
| **Daily Growth** | 250-300 MB |
| **Annual Growth** | ~97 GB |
| **TTL Collections** | 8 |
| **Sync Frequency** | Real-time + hourly |

### Implementation Checklist

- [ ] Test MongoDB connection
- [ ] Create genims_production database
- [ ] Create 30+ collections with validation
- [ ] Create all indexes
- [ ] Load 90 days historical data
- [ ] Start PostgreSQL → MongoDB sync
- [ ] Start real-time metrics aggregation
- [ ] Verify data freshness
- [ ] Test TTL cleanup
- [ ] Configure backup automation
- [ ] Set up monitoring alerts
- [ ] Document collection schemas

### Timeline

- **Phase 1**: Connection test → 2 min
- **Phase 2**: Create DB & collections → 5 min
- **Phase 3**: Create indexes → 5 min
- **Phase 4**: Initial data load → 15 min
- **Phase 5**: Start daemons → 3 min
- **Phase 6**: Verification → 5 min
- **TOTAL** → **35 minutes**

---

**Status**: Production Ready  
**Last Updated**: December 23, 2025  
**Total Setup Time**: 35 minutes (+ initial data transfer)

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
