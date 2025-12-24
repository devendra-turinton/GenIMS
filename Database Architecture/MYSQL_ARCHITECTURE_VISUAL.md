# GenIMS Complete Architecture: PostgreSQL + MySQL Integration
## Visual Overview & Data Flow Diagram

---

## Complete System Architecture

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                    APPLICATION LAYER (Web, Mobile, API)                       │
└──────────────────────────────────────────────────────────────────────────────┘
                                     ↓
                         ┌───────────┴───────────┐
                         ↓                       ↓
        ┌────────────────────────────┐  ┌────────────────────────────┐
        │  OLTP (Real-time Writes)   │  │   OLAP (Analytics/Reports) │
        │    PostgreSQL (13 DBs)     │  │  MySQL (2 DBs)             │
        └────────────────────────────┘  └────────────────────────────┘
                         ↑
        ┌────────────────┼────────────────┐
        │                │                │
        ↓                ↓                ↓
    ┌─────────┐    ┌─────────┐    ┌─────────┐
    │ Master  │    │ Master  │    │ Master  │
    │ Replica │    │ Replica │    │ Replica │
    └─────────┘    └─────────┘    └─────────┘
    (High Avail.)   (Sharding)     (Geo-dist.)
```

---

## PostgreSQL Operational Layer (13 Databases)

```
genims_master_db              genims_operational_db
├─ factories                  ├─ sensor_readings
├─ products                   ├─ scada_points
├─ materials                  ├─ production_run_logs
├─ employees                  └─ equipment_status
├─ customers
├─ suppliers
└─ (20+ master tables)

genims_mes_db                 genims_erp_db
├─ work_orders               ├─ materials
├─ operations                ├─ suppliers
├─ labor_transactions        ├─ sales_orders
├─ defects                   ├─ purchase_orders
├─ quality_inspections       ├─ accounts
└─ (20+ MES tables)          └─ (25+ ERP tables)

genims_wms_db                genims_tms_db
├─ warehouses               ├─ shipments
├─ inventory                ├─ carriers
├─ picking_tasks            ├─ routes
├─ receiving                ├─ tracking_events
└─ (15+ WMS tables)         └─ (15+ TMS tables)

genims_cmms_db               genims_crm_db
├─ assets                    ├─ leads
├─ work_orders               ├─ opportunities
├─ maintenance_history       ├─ accounts
├─ spare_parts               ├─ cases
└─ (15+ CMMS tables)         └─ (20+ CRM tables)

genims_service_db            genims_hcm_db
├─ service_tickets          ├─ employees
├─ field_service            ├─ training
├─ warranties               ├─ performance
├─ returns                  ├─ payroll
└─ (15+ Service tables)     └─ (18+ HR tables)

genims_supplier_db           genims_qms_db
├─ rfqs                      ├─ inspections
├─ contracts                 ├─ non_conformances
├─ invoices                  ├─ corrective_actions
├─ performance               └─ (12+ QMS tables)
└─ (15+ Supplier tables)

genims_planning_db
├─ demand_forecasts
├─ supply_plans
├─ production_schedules
└─ (10+ Planning tables)
```

**Characteristics:**
- ✅ ACID transactions
- ✅ Real-time operational data
- ✅ 1:1 updates (fast writes)
- ✅ Normalized schema
- ⚠️ Complex joins needed for reporting

---

## ETL Layer: Data Pipeline

```
┌──────────────────────────────────────────────────────────────────┐
│                    ETL TRANSFORMATION LAYER                      │
└──────────────────────────────────────────────────────────────────┘
                             ↓
        ┌────────────────────┼────────────────────┐
        │                    │                    │
        ↓                    ↓                    ↓
    
HOURLY REPORTING ETL      REAL-TIME AUDIT ETL    OTHER INTEGRATIONS
(Extract→Transform→Load)  (Trigger→Queue→Load)   (Custom ETL jobs)

PostgreSQL (13 DBs)       PostgreSQL Triggers     Third-party APIs
    ↓ Query               (INSERT/UPDATE/DELETE)  External sources
    ├─ Joins              ↓ Capture               ↓ Custom logic
    ├─ Aggregates         ├─ User ID              ETL processors
    ├─ Calculations       ├─ Timestamp
    └─ Transformations    ├─ Old/New values
                          └─ Transaction ID
                              ↓ Queue
                          (Max 10k events/batch)

        Every Hour (HH:00)      Real-time (< 1 sec)     On-demand
        15-30 minutes           Async daemon            Variable
        1 write per table       Append-only             Schedule

        ↓                       ↓                        ↓
    MySQL Reporting DB      MySQL Audit DB          Data Lake
    (Truncate + Insert)     (Append only)           (Archive)
```

---

## MySQL Reporting Layer (Fast Analytics)

```
genims_reporting_db (35 Tables, 1-2 GB, 12-month rolling)

PERFORMANCE ANALYTICS      SALES & REVENUE           FINANCIAL
├─ machine_perf_daily      ├─ sales_order_summary   ├─ p&l_daily
├─ production_summary_daily├─ customer_performance  ├─ cost_analysis
├─ downtime_summary_daily  ├─ product_sales         ├─ variance_reports
├─ oee_summary_daily       ├─ sales_rep_performance├─ cash_flow
└─ (4 more)                └─ (3 more)              └─ (4 more)

INVENTORY & MATERIALS      QUALITY & COMPLIANCE     KPI SUMMARY
├─ inventory_value         ├─ defect_summary        ├─ factory_kpis
├─ material_flow_daily     ├─ quality_by_product    ├─ shift_kpis
├─ abc_analysis            ├─ sla_tracking          ├─ customer_kpis
├─ supplier_performance    ├─ audit_summary         └─ product_kpis
└─ (4 more)                └─ (4 more)

REFRESH: HOURLY (HH:00)
QUERIES:  < 100ms (pre-aggregated)
USERS:    Dashboards, BI tools, Analysts
```

---

## MySQL Audit Layer (Compliance & Legal)

```
genims_audit_db (30 Tables, 1-5 GB, 7-year immutable)

SYSTEM AUDIT              DATA CHANGE AUDIT          COMPLIANCE
├─ system_audit_log       ├─ data_change_audit      ├─ sla_compliance
├─ user_activity_log      ├─ bulk_operation_audit   ├─ gdpr_requests
├─ login_audit            ├─ sensitive_change_log   ├─ legal_holds
├─ api_audit              ├─ config_change_audit    ├─ retention_policy
└─ (6 more)               └─ (4 more)               └─ (7 more)

CHARACTERISTICS:
- Append-only (no truncate, no delete)
- Every change logged with user/timestamp
- Before/after values captured
- Immutable audit trail
- Partitioned by year
- 7-year retention (regulatory)
- GDPR compliance ready
- Legal hold capable

REFRESH: REAL-TIME (< 1 second)
QUERIES:  Compliance reports, audit trails
USERS:    Auditors, Compliance, Legal teams
```

---

## Data Sync Flow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                  WRITE PATH (Real-time)                         │
└─────────────────────────────────────────────────────────────────┘

Application
    ↓
    └─→ PostgreSQL (ACID Transaction)
        ├─ INSERT/UPDATE/DELETE on 13 DBs
        ├─ Trigger captures change
        ├─ Logs to change queue
        └─ Commit (< 1 sec)

        ↓ (Real-time, async)

        Audit Daemon
        ├─ Read change queue
        ├─ Batch events (1000/60sec)
        ├─ INSERT into genims_audit_db
        ├─ Maintain audit_sequence
        └─ Log success/failure

        ↓ Append

        genims_audit_db (MySQL)
        └─ Immutable audit trail


┌─────────────────────────────────────────────────────────────────┐
│                  READ PATH (Reporting)                          │
└─────────────────────────────────────────────────────────────────┘

PostgreSQL (13 DBs)
├─ genims_master_db (customers, products, suppliers)
├─ genims_mes_db (work orders, operations, labor)
├─ genims_erp_db (sales orders, inventory, financials)
├─ genims_wms_db (warehouse inventory, shipments)
├─ genims_tms_db (shipments, tracking, routes)
└─ ... (8 more DBs)

    ↓ (Every hour at HH:00, ~15-30 minutes)

    ETL Transformation Engine
    ├─ Query PostgreSQL (complex JOINs)
    ├─ Aggregate by date/factory/product
    ├─ Calculate KPIs (OEE, margins, etc)
    ├─ Denormalize into reporting format
    └─ Validate data integrity

    ↓ (Truncate + Insert, bulk load)

    genims_reporting_db (MySQL)
    ├─ 35 denormalized tables
    ├─ Pre-aggregated metrics
    ├─ Ready for fast queries
    └─ Updated timestamp

        ↓ (On-demand queries, < 100ms)

        Dashboard / BI Tool / Analyst
        └─ Query MySQL (no JOINs needed)


┌─────────────────────────────────────────────────────────────────┐
│                  BACKUP PATH (Archive)                          │
└─────────────────────────────────────────────────────────────────┘

Daily at 02:00 AM UTC:

genims_reporting_db
    └─→ mysqldump (full schema + data)
        └─→ gzip compression
            └─→ Azure Blob Storage
                └─→ 30-day retention (rolling)

genims_audit_db
    └─→ mysqldump (full schema + data)
        └─→ gzip compression
            ├─→ Azure Blob Storage (hot)
            │   └─→ 2-year retention
            └─→ Azure Archive (cold)
                └─→ 7-year total retention
```

---

## .env Configuration

```ini
# POSTGRESQL CONNECTIONS (13 databases)
PG_MASTER_HOST=postgres.azure.com
PG_MASTER_PORT=5432
PG_MASTER_USER=genims_user
PG_MASTER_PASSWORD=<password>

# PostgreSQL Read Replica (for ETL queries)
PG_REPLICA_HOST=postgres-replica.azure.com
PG_REPLICA_PORT=5432
PG_REPLICA_USER=genims_readonly
PG_REPLICA_PASSWORD=<password>

# MYSQL CONNECTIONS (2 databases)
MYSQL_REPORTING_HOST=insights-db.mysql.database.azure.com
MYSQL_REPORTING_PORT=3306
MYSQL_REPORTING_DB=genims_reporting_db
MYSQL_REPORTING_USER=turintonadmin
MYSQL_REPORTING_PASSWORD=<password>

MYSQL_AUDIT_HOST=insights-db.mysql.database.azure.com
MYSQL_AUDIT_PORT=3306
MYSQL_AUDIT_DB=genims_audit_db
MYSQL_AUDIT_USER=turintonadmin
MYSQL_AUDIT_PASSWORD=<password>

# ETL CONFIGURATION
ETL_REPORTING_INTERVAL=3600          # 1 hour
ETL_AUDIT_INTERVAL=60                # 1 minute check
ETL_BATCH_SIZE=1000                  # Rows per insert
ETL_LOG_DIR=logs/etl/
ETL_ERROR_THRESHOLD=5                # Alert after 5 failures

# DATA SYNC
DATA_SYNC_TIMEOUT=300                # 5 minutes
DATA_SYNC_RETRY_COUNT=3
DATA_SYNC_RETRY_DELAY=5              # seconds

# BACKUP
BACKUP_ENABLED=true
BACKUP_DAILY_TIME=02:00              # 2 AM UTC
BACKUP_RETENTION_DAYS=30             # Reporting
BACKUP_AUDIT_RETENTION_DAYS=2555     # 7 years
BACKUP_AZURE_CONTAINER=genims-backups
```

---

## Data Volume & Growth

```
INITIAL STATE:
┌─────────────────┬──────────┬──────────┬────────────┐
│ Database        │ Tables   │ Rows     │ Size       │
├─────────────────┼──────────┼──────────┼────────────┤
│ PostgreSQL (13) │ 500+     │ 2-3M     │ 20-30 GB   │
│ MySQL Report    │ 35       │ 100K     │ 1-2 GB     │
│ MySQL Audit     │ 30       │ 50K      │ 500 MB     │
└─────────────────┴──────────┴──────────┴────────────┘

12-MONTH PROJECTION:
┌─────────────────┬──────────┬──────────┬────────────┐
│ Database        │ Growth   │ New Rows │ Size       │
├─────────────────┼──────────┼──────────┼────────────┤
│ PostgreSQL (13) │ +50%     │ +1.5M    │ 30-45 GB   │
│ MySQL Report    │ +100%    │ +365K    │ 3-4 GB     │
│ MySQL Audit     │ +300%    │ +8M      │ 5-10 GB    │
└─────────────────┴──────────┴──────────┴────────────┘

7-YEAR PROJECTION (Audit):
├─ Year 1: 5-10 GB
├─ Year 2: 10-15 GB
├─ Year 3: 15-20 GB
├─ Year 4: 20-25 GB
├─ Year 5: 23-28 GB
├─ Year 6: 26-31 GB
└─ Year 7: 28-35 GB (stable, auto-archive)
```

---

## Setup Sequence

```
PHASE 1: DATABASE CREATION (5 min)
    ↓
    Create genims_reporting_db (MySQL) ✓
    Create genims_audit_db (MySQL)     ✓

PHASE 2: SCHEMA CREATION (10 min)
    ↓
    Load 35-table reporting schema     ✓
    Load 30-table audit schema         ✓
    Create indexes                     ✓

PHASE 3: INITIAL DATA LOAD (20 min)
    ↓
    PostgreSQL → MySQL Reporting       ✓
    Initialize audit schema            ✓

PHASE 4: DAEMON STARTUP (5 min)
    ↓
    Start hourly reporting ETL         ✓
    Start real-time audit ETL          ✓

PHASE 5: VALIDATION (10 min)
    ↓
    Verify data freshness              ✓
    Verify audit logging               ✓
    Check performance metrics          ✓

TOTAL SETUP TIME: ~50 minutes
```

---

## Key Integration Points

```
full_setup.py orchestrates:

1. PostgreSQL Setup (existing)
   ├─ Master data generation
   ├─ Operational data generation
   ├─ Module data generation
   └─ PostgreSQL database creation

2. MySQL Setup (new)
   ├─ Read .env for MySQL credentials
   ├─ Create reporting database
   ├─ Create audit database
   └─ Load schemas & indexes

3. ETL Setup (new)
   ├─ Initialize reporting ETL
   ├─ Initialize audit ETL
   └─ Start both daemons

4. Backup Setup (new)
   ├─ Configure daily backups
   ├─ Set retention policies
   └─ Test backup/restore

5. Monitoring Setup (new)
   ├─ Initialize logging
   ├─ Start health checks
   └─ Configure alerts

6. Final Validation
   ├─ Verify all services running
   ├─ Check data freshness
   ├─ Test end-to-end sync
   └─ Generate setup report
```

---

## Success Metrics

✅ **Infrastructure**
- [ ] 2 MySQL databases operational
- [ ] 65 tables created successfully
- [ ] Connection pooling configured
- [ ] Network latency < 50ms

✅ **Data Sync**
- [ ] Hourly ETL success rate > 99%
- [ ] Data freshness < 1 hour
- [ ] No data loss / gaps
- [ ] Row counts match source

✅ **Audit**
- [ ] Real-time capture < 1 second
- [ ] All changes logged
- [ ] 7-year retention enforced
- [ ] No data deleted prematurely

✅ **Performance**
- [ ] Dashboard queries < 100ms
- [ ] Reporting ETL < 30 minutes
- [ ] Audit daemon throughput 1000+ events/min
- [ ] Zero PostgreSQL impact

✅ **Monitoring**
- [ ] All metrics tracked
- [ ] Alerts firing correctly
- [ ] Dashboards operational
- [ ] Compliance reports auto-generated

---

**Status**: Strategy & Architecture Defined  
**Next**: Implement MySQL schemas and ETL daemons  
**Timeline**: 4 weeks to production

