# MySQL Implementation Approach for GenIMS
## Analysis & Technical Strategy

**Date**: December 24, 2025  
**Status**: Strategy Document  
**Scope**: MySQL Reporting, Analytics & Audit Layer Integration with PostgreSQL

---

## 1. DOCUMENT ANALYSIS: Key Takeaways

### Architecture Overview
```
PostgreSQL (13 Operational Databases)
    ├─ genims_master_db (Master Data)
    ├─ genims_operational_db (IoT/SCADA)
    ├─ genims_mes_db (Manufacturing)
    ├─ genims_erp_db (Finance/Materials)
    ├─ genims_wms_db (Warehouse)
    ├─ genims_tms_db (Logistics)
    ├─ genims_cmms_db (Maintenance)
    ├─ genims_crm_db (Sales)
    ├─ genims_service_db (Support)
    ├─ genims_hcm_db (HR)
    ├─ genims_supplier_db (Procurement)
    ├─ genims_qms_db (Quality)
    └─ genims_planning_db (Planning)
         ↓ (Hourly ETL + Real-time Audit Sync)
    ├─→ genims_reporting_db (MySQL) - 35 Tables, 1-2 GB, 12-month retention
    └─→ genims_audit_db (MySQL) - 30 Tables, 1-5 GB, 7-year retention
```

### Two Distinct Data Flows

**Flow 1: Reporting (Denormalized)**
- **Frequency**: Hourly ETL
- **Source**: All 13 PostgreSQL DBs (aggregate & transform)
- **Target**: genims_reporting_db (MySQL)
- **Purpose**: Fast dashboards, KPIs, operational analytics
- **Tables**: 35 (machine performance, production summary, sales, financial, inventory)
- **Retention**: 12 months (rolling window)
- **Refresh Strategy**: Complete replacement or delta updates

**Flow 2: Audit (Compliance)**
- **Frequency**: Real-time (continuous)
- **Source**: PostgreSQL change logs/triggers
- **Target**: genims_audit_db (MySQL)
- **Purpose**: Regulatory compliance, audit trails, legal holds
- **Tables**: 30 (system audit, user activity, data changes, SLA tracking)
- **Retention**: 7 years (regulatory requirement)
- **Append Only**: Never delete, only archive

---

## 2. ENVIRONMENT CONFIGURATION REQUIREMENTS

### .env Variables to Add

```ini
# MySQL Reporting Database
MYSQL_REPORTING_HOST=insights-db.mysql.database.azure.com
MYSQL_REPORTING_PORT=3306
MYSQL_REPORTING_DB=genims_reporting_db
MYSQL_REPORTING_USER=turintonadmin
MYSQL_REPORTING_PASSWORD=<password>
MYSQL_REPORTING_CHARSET=utf8mb4
MYSQL_REPORTING_TIMEOUT=30

# MySQL Audit Database
MYSQL_AUDIT_HOST=insights-db.mysql.database.azure.com
MYSQL_AUDIT_PORT=3306
MYSQL_AUDIT_DB=genims_audit_db
MYSQL_AUDIT_USER=turintonadmin
MYSQL_AUDIT_PASSWORD=<password>
MYSQL_AUDIT_CHARSET=utf8mb4
MYSQL_AUDIT_TIMEOUT=30

# ETL Configuration
ETL_REPORTING_INTERVAL=3600  # 1 hour in seconds
ETL_AUDIT_INTERVAL=60       # 1 minute for audit checks
ETL_LOG_DIR=logs/etl/
ETL_ERROR_THRESHOLD=5       # Alert after 5 consecutive failures

# Data Sync Configuration
DATA_SYNC_BATCH_SIZE=1000   # Insert batch size
DATA_SYNC_TIMEOUT=300       # 5 minutes
DATA_SYNC_RETRY_COUNT=3
DATA_SYNC_RETRY_DELAY=5     # seconds

# Backup Configuration
BACKUP_ENABLED=true
BACKUP_DAILY_TIME=02:00     # 2 AM UTC
BACKUP_RETENTION_DAYS=30    # Reporting
BACKUP_AUDIT_RETENTION_DAYS=2555  # 7 years
BACKUP_AZURE_CONTAINER=genims-backups
```

---

## 3. IMPLEMENTATION PHASES

### Phase 1: Infrastructure Setup (Week 1)

**1.1 Database Creation**
```
Task: Create 2 MySQL databases on Azure
- genims_reporting_db (UTF8MB4 collation)
- genims_audit_db (UTF8MB4 collation)

Validation:
✓ Databases exist and are accessible
✓ Character set is UTF8MB4
✓ Users have appropriate permissions
```

**1.2 Connection Validation**
```
Task: Test connectivity from application servers
- Verify MySQL host is reachable
- Test credentials
- Check firewall rules
- Confirm SSL/TLS connectivity

Scripts:
- test_mysql_connection.py (in scripts/)
```

**1.3 Environment Setup**
```
Task: Configure .env variables
- Add all MySQL connection strings
- Add ETL configuration
- Add backup settings
- Validate env loading in full_setup.py
```

### Phase 2: Schema Design & Creation (Week 1-2)

**2.1 Reporting Schema (35 Tables)**

**Performance & Operations Tables** (8 tables)
```
├─ machine_performance_daily
│  ├ machine_id, factory_id, date
│  ├ oee_percentage, availability, performance, quality
│  ├ total_runtime_minutes, downtime_minutes, uptime_minutes
│  ├ units_produced, units_rejected, scrap_rate
│  └ updated_at (for hourly updates)
│
├─ production_summary_daily
│  ├ factory_id, line_id, date
│  ├ planned_units, actual_units, good_units
│  ├ labor_hours, setup_hours, changeover_hours
│  ├ standard_cost, actual_cost, variance
│  └ shift_breakdown (morning, afternoon, night)
│
├─ downtime_summary_daily
│  ├ machine_id, factory_id, date
│  ├ downtime_minutes_by_category (mechanical, electrical, etc)
│  ├ mtbf, mttr metrics
│  └ top_failure_codes (list)
│
└─ ... (5 more operational tables)
```

**Sales & Revenue Tables** (7 tables)
```
├─ sales_order_summary
│  ├ customer_id, sales_rep_id, period
│  ├ order_count, total_revenue, average_order_value
│  ├ on_time_delivery_pct, quality_acceptance_pct
│  └ margin_dollars, margin_percent
│
├─ customer_performance
│  ├ customer_id, factory_id, product_category
│  ├ ytd_sales, ytd_orders, churn_risk
│  ├ payment_days_average, payment_reliability
│  └ nps_score, return_rate_pct
│
└─ ... (5 more sales tables)
```

**Financial Tables** (8 tables)
```
├─ profit_and_loss_daily
│  ├ factory_id, department, date
│  ├ revenue, cost_of_goods_sold, gross_margin
│  ├ operating_expenses, operating_income
│  ├ other_income, tax, net_income
│  └ variance_from_budget
│
├─ cost_analysis_daily
│  ├ product_id, factory_id, date
│  ├ material_cost, labor_cost, overhead_cost
│  ├ standard_cost, actual_cost, variance_pct
│  └ cost_trend (up/down/stable)
│
└─ ... (6 more financial tables)
```

**Inventory & Materials Tables** (12 tables)
```
├─ inventory_value_summary
│  ├ factory_id, warehouse_id, material_id
│  ├ quantity_on_hand, abc_classification
│  ├ inventory_value, standard_cost_value
│  ├ days_of_inventory, turnover_rate
│  └ reorder_point_status
│
├─ material_flow_daily
│  ├ material_id, factory_id, date
│  ├ receipts_qty, issues_qty, adjustments_qty
│  ├ ending_balance, average_daily_usage
│  └ supplier_performance_rating
│
└─ ... (10 more inventory tables)
```

**2.2 Audit Schema (30 Tables)**

**System Audit Tables** (10 tables)
```
├─ system_audit_log
│  ├ audit_id, audit_timestamp, audit_sequence
│  ├ user_id, source_ip, session_id
│  ├ schema_name, table_name, operation_type (INSERT/UPDATE/DELETE)
│  ├ affected_rows_count, status (SUCCESS/FAILED)
│  ├ error_message, duration_ms
│  ├ row_count_before, row_count_after
│  └ indexed: (table_name, audit_timestamp), (user_id, audit_timestamp)
│
├─ user_activity_log
│  ├ activity_id, activity_timestamp, user_id
│  ├ activity_type (LOGIN/READ/WRITE/DELETE/EXPORT)
│  ├ resource_type, resource_id, application_name
│  ├ status, duration_seconds
│  └ indexed: (user_id, activity_timestamp)
│
└─ ... (8 more system tables)
```

**Data Change Audit Tables** (8 tables)
```
├─ data_change_audit
│  ├ change_id, change_timestamp, audit_sequence
│  ├ user_id, table_name, column_name, primary_key_value
│  ├ old_value, new_value, change_type
│  ├ transaction_id, reason_code, approval_id
│  └ indexed: (table_name, change_timestamp)
│
├─ bulk_operation_audit
│  ├ operation_id, operation_timestamp, user_id
│  ├ operation_type, affected_table, rows_affected
│  ├ status, error_message, data_sample
│  └ indexed: (user_id, operation_timestamp)
│
└─ ... (6 more data tables)
```

**Compliance & Legal Tables** (12 tables)
```
├─ sla_compliance_tracking
│  ├ sla_id, sla_timestamp, sla_type
│  ├ threshold_value, actual_value, compliance_status
│  ├ factory_id, department, metric_name
│  └ indexed: (sla_type, sla_timestamp)
│
├─ gdpr_data_request_log
│  ├ request_id, request_timestamp, request_type
│  ├ subject_id, requestor_id, status
│  ├ data_scope, completion_timestamp
│  └ indexed: (request_type, request_timestamp)
│
├─ legal_hold_tracking
│  ├ hold_id, hold_timestamp, case_id
│  ├ data_scope, affected_tables, status
│  ├ reviewer_id, expiry_date
│  └ indexed: (case_id, hold_timestamp)
│
└─ ... (9 more compliance tables)
```

**2.3 Index Strategy**

**Reporting Indexes** (Fast queries)
```
- Date-based: (date, factory_id), (period, department)
- Category: (product_category, factory_id)
- Customer: (customer_id, date)
- Time-series: UNIQUE (date, metric_id) for timeseries queries
```

**Audit Indexes** (Legal compliance)
```
- Timestamp: (table_name, audit_timestamp) - mandatory
- User: (user_id, audit_timestamp) - for user analysis
- Range: Partition by year for 7-year retention
- Activity: (activity_type, activity_timestamp)
```

---

## 4. DATA SYNCHRONIZATION STRATEGY

### 4.1 ETL Reporting Sync (Hourly)

**Source**: PostgreSQL (13 DBs)  
**Target**: genims_reporting_db (MySQL)  
**Frequency**: Every hour at HH:00  
**Process**: Complete table replacement (truncate + insert)

```python
# Pseudo-code: Full sync process
ETL_HOURLY_REPORTING:
    1. Start transaction on PostgreSQL
    
    2. Extract & Transform:
       - machine_performance_daily:
         * Group by machine_id, factory_id, date
         * Calculate OEE = Availability × Performance × Quality
         * Sum downtimes, runtimes, production
       
       - production_summary_daily:
         * Join WO + Operations + Labor from genims_mes_db
         * Group by factory_id, line_id, date
         * Calculate standard vs actual costs
       
       - sales_order_summary:
         * Join SO + SOL from genims_erp_db
         * Aggregate by customer, period
         * Calculate margins, on-time delivery %
       
       - profit_and_loss_daily:
         * Aggregate from financial tables
         * Calculate expenses, taxes, net income
       
       - inventory_value_summary:
         * Join materials + GL from genims_erp_db
         * Calculate ABC classification
         * Trend analysis

    3. Load to MySQL (batch insert):
       - TRUNCATE target tables
       - INSERT new data in batches (1000 rows)
       - UPDATE last_updated_at
    
    4. Validate:
       - Row count comparison
       - Data integrity checks
       - Null value checks
    
    5. Log success/failure
       - Duration, rows affected
       - Error details if failed
       - Alert if threshold exceeded

TIME: ~15-30 minutes per sync
COST: Minimal (read-only PostgreSQL)
```

### 4.2 Audit Sync (Real-time)

**Source**: PostgreSQL change triggers  
**Target**: genims_audit_db (MySQL)  
**Frequency**: Real-time (triggers on write)  
**Process**: Append-only (never truncate)

```python
# Pseudo-code: Real-time audit capture
AUDIT_TRIGGER_ON_WRITE:
    1. PostgreSQL trigger captures:
       - Operation type (INSERT/UPDATE/DELETE)
       - User ID, timestamp, table name
       - Old values, new values (for UPDATE)
       - Transaction ID
    
    2. Write to audit queue (in-memory buffer)
       - Batch audit events (every 60 seconds or 1000 events)
    
    3. Async daemon pushes to MySQL:
       - INSERT into system_audit_log
       - INSERT into data_change_audit (for sensitive tables)
       - Maintain audit_sequence (non-reusable counter)
    
    4. Archive strategy:
       - Current year: Hot data (MySQL)
       - Previous 6 years: Cold data (Archive partition)
       - 7+ years: Delete (after compliance period)

LATENCY: <1 second to audit_db
THROUGHPUT: 1000-5000 events/minute
RETENTION: 7 years
```

### 4.3 Sensitive Table Auditing

**Audit every change on these tables:**
- All customer data (genims_crm_db)
- All financial data (genims_erp_db)
- All personnel data (genims_hcm_db)
- All supplier data (genims_supplier_db)
- Configuration changes (all DBs)

**Capture**: Before & After values, user, timestamp, reason

---

## 5. FULL_SETUP.PY INTEGRATION

### Current PostgreSQL Setup Flow
```python
setup_genims.py:
    ├─ Master data generation (genims_master_data.json)
    ├─ Operational data generation (genims_operational_data.json)
    ├─ Module data generation (MES, ERP, WMS, etc.)
    ├─ PostgreSQL database creation & schema loading
    ├─ PostgreSQL data loading
    └─ Validation & summary report
```

### Extended: MySQL Setup Integration
```python
full_setup.py (NEW):
    ├─ PostgreSQL Setup
    │  ├─ Master data generation
    │  ├─ Operational data generation
    │  ├─ Module data generation
    │  ├─ PostgreSQL database creation & schema loading
    │  ├─ PostgreSQL data loading
    │  └─ PostgreSQL validation
    │
    ├─ MySQL Reporting Database Setup (NEW)
    │  ├─ Read .env for MySQL connection strings
    │  ├─ Test MySQL connectivity
    │  ├─ Create genims_reporting_db database
    │  ├─ Load 35-table reporting schema
    │  ├─ Create reporting indexes
    │  ├─ Trigger initial ETL (hourly reporting sync)
    │  ├─ Populate machine_performance_daily
    │  ├─ Populate production_summary_daily
    │  ├─ Populate sales_order_summary
    │  ├─ Populate profit_and_loss_daily
    │  ├─ Populate inventory_value_summary
    │  ├─ ... (30 more reporting tables)
    │  └─ Validate data freshness
    │
    ├─ MySQL Audit Database Setup (NEW)
    │  ├─ Create genims_audit_db database
    │  ├─ Load 30-table audit schema
    │  ├─ Create audit indexes (especially timestamp)
    │  ├─ Set up partition strategy (by year)
    │  ├─ Set up retention policy (7 years)
    │  ├─ Initialize audit log from PostgreSQL changes
    │  └─ Validate audit log readiness
    │
    ├─ ETL Daemon Setup (NEW)
    │  ├─ Start hourly reporting ETL daemon
    │  │  └─ Runs at HH:00 every hour
    │  │  └─ Syncs all 35 reporting tables
    │  │  └─ Logs to logs/etl_reporting_*.log
    │  │
    │  └─ Start real-time audit daemon
    │     └─ Monitors PostgreSQL change log
    │     └─ Pushes changes to genims_audit_db
    │     └─ Logs to logs/etl_audit_*.log
    │
    ├─ Backup Configuration (NEW)
    │  ├─ Schedule daily reporting backup (30-day retention)
    │  ├─ Schedule daily audit backup (7-year retention)
    │  ├─ Configure Azure Blob Storage upload
    │  └─ Create backup rotation script
    │
    └─ Final Validation
       ├─ Verify both MySQL databases exist
       ├─ Verify all 65 tables created
       ├─ Verify ETL daemons running
       ├─ Verify initial data sync complete
       ├─ Verify audit logging working
       └─ Generate setup summary report
```

### Code Structure for full_setup.py
```
scripts/full_setup.py
├─ Class: PostgreSQLSetup (existing)
├─ Class: MySQLSetup (NEW)
│  ├─ __init__(env_config)
│  ├─ test_connectivity()
│  ├─ create_databases()
│  ├─ create_reporting_schema()
│  ├─ create_audit_schema()
│  ├─ create_indexes()
│  └─ validate_setup()
│
├─ Class: ETLDaemon (NEW)
│  ├─ ReportingETL (hourly)
│  └─ AuditETL (real-time)
│
└─ main():
    ├─ PostgreSQL setup (existing)
    ├─ MySQL setup (new)
    ├─ ETL daemon startup (new)
    └─ Final validation
```

---

## 6. DATA SYNC & CONNECTIVITY

### Bidirectional Sync Strategy

**Read Direction: PostgreSQL → MySQL**
```
Use Case: Operational reporting needs daily snapshots
Frequency: Hourly (every hour on the hour)
Scope: All 13 PostgreSQL DBs → 35 reporting tables

Pull model:
1. Query PostgreSQL for latest data (joins, aggregations)
2. Transform into denormalized format
3. Load to MySQL (truncate + insert)
4. Update metadata (last_synced_at)
```

**Read Direction: MySQL → Application (Dashboards)**
```
Use Case: Real-time dashboards need fast queries
Frequency: On-demand (HTTP requests)
Scope: MySQL reporting tables → REST API → Dashboard UI

Query model:
1. Dashboard calls API endpoint
2. API queries MySQL (pre-aggregated data)
3. Returns JSON response (<100ms)
```

**Write Direction: Applications → PostgreSQL**
```
Use Case: All writes go to operational databases
Frequency: Real-time
Scope: OLTP transactions on 13 PostgreSQL DBs

Write model:
1. Application writes to PostgreSQL (ACID guaranteed)
2. PostgreSQL triggers capture changes
3. Triggers queue events for audit
4. ETL picks up changes in next hourly sync
```

**Audit Direction: PostgreSQL → MySQL (Compliance)**
```
Use Case: Regulatory compliance requires audit trails
Frequency: Real-time (triggers)
Scope: Sensitive table changes → audit tables

Audit model:
1. PostgreSQL trigger fires on change
2. Captures user, timestamp, old/new values
3. Queue to audit daemon
4. Async push to genims_audit_db (batched)
5. Never delete, only archive to cold storage
```

### Connection Pool Architecture

```
┌─────────────────────────────────────────────┐
│     Application Server (Python)             │
└─────────────────────────────────────────────┘
    ↓
┌──────────────────────┬──────────────────────┐
│ PostgreSQL Pool      │ MySQL Pool           │
│ (13 connections)     │ (4 connections)      │
└──────────────────────┴──────────────────────┘
    ↓                      ↓
┌─ PostgreSQL ─────────┐ ┌─ MySQL ────────────┐
│ (13 DBs)             │ │ (2 DBs)            │
│ ├─ master            │ │ ├─ reporting       │
│ ├─ operational       │ │ └─ audit           │
│ ├─ mes               │ └────────────────────┘
│ ├─ erp               │
│ └─ ... (8 more)      │
└─────────────────────┘

Connection Settings:
PostgreSQL: min=2, max=20 per DB (per ETL daemon)
MySQL Reporting: min=1, max=5 (read-heavy)
MySQL Audit: min=1, max=3 (append-heavy)
```

---

## 7. MONITORING & ALERTING

### Key Metrics to Monitor

**Reporting Sync Health**
```
- Hourly ETL success rate (target: 99.9%)
- Data freshness (last updated_at < 1 hour)
- Row counts before/after (delta < 5%)
- Sync duration (target: < 30 minutes)
- Error rate per sync
```

**Audit Log Health**
```
- Events per minute (trend analysis)
- Audit latency (target: < 1 second)
- Queue depth (target: < 1000 events)
- Compliance rule violations
- Legal hold status
```

**Database Health**
```
MySQL Reporting:
- Disk usage (target: < 2 GB monthly)
- Query performance (P95 < 100ms)
- Index fragmentation (target: < 10%)

MySQL Audit:
- Storage growth rate (trend: 2-3 GB/year)
- Archive success rate (100%)
- Compliance data integrity (weekly checks)
```

### Alerting Rules

```
ALERT: ETL sync fails 2+ times in a row
→ Action: Page on-call DBA, check logs

ALERT: Data freshness > 2 hours
→ Action: Check PostgreSQL, restart ETL daemon

ALERT: Audit events queue > 10k
→ Action: Check MySQL audit DB performance

ALERT: Disk usage > 80%
→ Action: Schedule cleanup, check retention

ALERT: Audit log compliance violation detected
→ Action: Escalate to compliance officer
```

---

## 8. TESTING STRATEGY

### Unit Tests

```python
test_mysql_schema.py:
- Verify all 35 reporting tables exist
- Verify all 30 audit tables exist
- Verify indexes are created
- Verify foreign keys are correct
- Verify constraints are applied

test_etl_reporting.py:
- Test PostgreSQL → MySQL data transformation
- Test data aggregation logic
- Test null handling
- Test boundary conditions (time zones, etc)
- Test concurrent sync attempts

test_etl_audit.py:
- Test trigger capture on INSERT/UPDATE/DELETE
- Test before/after value comparison
- Test user/timestamp capture
- Test audit sequence integrity
```

### Integration Tests

```python
test_data_sync.py:
- End-to-end ETL: PostgreSQL → MySQL
- Verify row counts match
- Verify aggregations are correct
- Verify no data loss
- Test with large datasets (100k+ rows)

test_audit_sync.py:
- Generate changes on sensitive tables
- Verify audit log capture
- Verify before/after values
- Test compliance scenarios
```

### Performance Tests

```python
test_etl_performance.py:
- ETL duration with 1M+ rows
- Query performance on reporting tables
- Audit daemon throughput (events/second)
- Concurrent user impact
```

---

## 9. IMPLEMENTATION ROADMAP

### Week 1: Infrastructure & Schema
- [ ] Configure .env for MySQL
- [ ] Create databases (reporting + audit)
- [ ] Create schemas (35 + 30 tables)
- [ ] Create indexes
- [ ] Validate database connectivity

### Week 2: ETL Development
- [ ] Develop reporting ETL
- [ ] Develop audit ETL
- [ ] Create logging/monitoring
- [ ] Test with initial data

### Week 3: Integration & Testing
- [ ] Integrate with full_setup.py
- [ ] Run end-to-end tests
- [ ] Performance testing
- [ ] Compliance validation

### Week 4: Deployment & Monitoring
- [ ] Deploy to production
- [ ] Monitor for 1 week
- [ ] Tune indexes if needed
- [ ] Setup backups & retention

---

## 10. SUCCESS CRITERIA

✅ **Setup Success**
- [ ] Both MySQL databases created
- [ ] All 65 tables exist with correct structure
- [ ] All indexes created
- [ ] .env properly configured

✅ **Data Sync Success**
- [ ] Hourly reporting sync runs successfully
- [ ] Data freshness < 1 hour
- [ ] Row counts match expectations
- [ ] No data loss during sync

✅ **Audit Success**
- [ ] Real-time audit capture working
- [ ] All changes logged with user/timestamp
- [ ] Audit log integrity (no gaps)
- [ ] 7-year retention policy enforced

✅ **Performance Success**
- [ ] Dashboard queries complete < 100ms
- [ ] ETL sync completes in < 30 minutes
- [ ] Audit latency < 1 second
- [ ] No impact on PostgreSQL performance

✅ **Monitoring Success**
- [ ] Alerting system operational
- [ ] All key metrics tracked
- [ ] Dashboards showing real-time data
- [ ] Compliance reports auto-generated

---

## 11. RISK MITIGATION

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|-----------|
| MySQL outage | Low | High | Master-slave replication, connection pooling |
| Data sync lag | Medium | Medium | Increase frequency, add monitoring alerts |
| Audit log full | Low | High | Implement partitioning, archive old data |
| Performance degradation | Medium | Medium | Index optimization, query tuning, caching |
| Compliance violation | Low | Critical | Audit trail integrity checks, legal holds |

---

## 12. DELIVERABLES

1. **MySQL Schema Files**
   - `schema/mysql_reporting_schema.sql` (35 tables)
   - `schema/mysql_audit_schema.sql` (30 tables)
   - `schema/mysql_reporting_indexes.sql`
   - `schema/mysql_audit_indexes.sql`

2. **ETL Daemons**
   - `scripts/etl_reporting_daemon.py` (hourly)
   - `scripts/etl_audit_daemon.py` (real-time)

3. **Setup Script**
   - `scripts/full_setup.py` (integrated PostgreSQL + MySQL)

4. **Utilities**
   - `scripts/test_mysql_connection.py`
   - `scripts/backup_mysql.py`
   - `scripts/archive_audit_logs.py`
   - `scripts/verify_mysql_setup.py`

5. **Documentation**
   - This approach document
   - Operational runbooks
   - Troubleshooting guide
   - Compliance audit guide

---

## SUMMARY

The MySQL implementation follows a **two-tier architecture**:

1. **Reporting Tier** (Hot Data)
   - Denormalized 35 tables
   - Hourly refresh from PostgreSQL
   - 12-month retention
   - Optimized for fast dashboards

2. **Audit Tier** (Compliance Data)
   - Append-only 30 tables
   - Real-time capture from PostgreSQL
   - 7-year retention
   - Immutable audit trail

**Integration approach**: Extend existing `setup_genims.py` → `full_setup.py` that orchestrates:
- PostgreSQL setup (existing)
- MySQL setup (new)
- ETL daemon startup (new)
- Backup automation (new)
- End-to-end validation (enhanced)

**Key success factor**: Separate read (reporting) and write (PostgreSQL) layers with real-time audit capture for compliance.

---

**Next Steps:**
1. Review this approach with stakeholders
2. Create MySQL schema files (35+30 tables)
3. Develop ETL transformation logic
4. Integrate into full_setup.py
5. Execute implementation roadmap

