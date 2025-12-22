# GenIMS MySQL Database Architecture
## Reporting, Analytics & Audit Database Strategy

**Document Version**: 2.0  
**Created**: December 22, 2025  
**Last Updated**: December 22, 2025  
**Status**: Ready for Implementation  
**Focus**: MySQL (3 Databases for Reporting, Analytics & Audit - Maximum Isolation)

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [MySQL Strategy](#mysql-strategy)
3. [Database Options](#database-options)
4. [Recommended Architecture](#recommended-architecture)
5. [Database 1: GenIMS Reporting](#database-1-genims-reporting)
6. [Database 2: GenIMS Analytics (Optional)](#database-2-genims-analytics-optional)
7. [Database 3: GenIMS Audit (Optional)](#database-3-genims-audit-optional)
8. [ETL Strategy](#etl-strategy)
9. [Connection Configuration](#connection-configuration)
10. [Load Strategy](#load-strategy)
11. [Maintenance & Operations](#maintenance--operations)

---

## Overview

While PostgreSQL stores operational data across 13 functional databases, **MySQL serves as the reporting, analytics, and audit layer with 3 separate databases**. MySQL receives data from PostgreSQL via ETL processes and provides:

- **Fast reporting queries** (denormalized tables optimized for reads)
- **Advanced analytics** (data warehouse with dimensional models)
- **Compliance & audit trails** (immutable logs for regulatory)
- **Dashboard data** (aggregated views and KPIs)
- **Analytics snapshots** (time-series and historical trends)

### Key Benefits

✅ **Optimized for Reporting** - Denormalized schemas for fast queries  
✅ **Lower Query Cost** - Simplified queries vs. normalized PostgreSQL  
✅ **Data Archival** - Separate storage for historical data  
✅ **Compliance** - Audit trail and regulatory logging  
✅ **Scalability** - Horizontal scaling for read-heavy workloads  
✅ **Analytics** - Time-series and dimensional data models  

### Key Differences from PostgreSQL

| Aspect | PostgreSQL | MySQL |
|--------|-----------|-------|
| **Purpose** | Operational data | Reporting & Analytics |
| **Normalization** | Highly normalized | Denormalized |
| **Update Pattern** | Real-time inserts/updates | Batch ETL syncs |
| **Query Type** | OLTP (Online Transaction Processing) | OLAP (Online Analytical Processing) |
| **Data Freshness** | Real-time | Hourly/Daily |
| **Storage** | Optimized for writes | Optimized for reads |

---

## MySQL Strategy

### Principle: Single Analytics Database (or 2-3 logical separations)

Instead of multiple operational databases, MySQL consolidates reporting data into:

**Option A: Single Database** (Simple, 50-60 tables)
- `genims_reporting_db` - All reporting/analytics/audit tables

**Option B: Two Databases** (Better isolation, 30-30 tables)
- `genims_reporting_db` - Dashboards & reporting
- `genims_audit_db` - Compliance & audit logs

**Option C: Three Databases - Maximum Isolation** ⭐ RECOMMENDED (20-25 tables each)
- `genims_reporting_db` - KPI dashboards & operational reporting
- `genims_analytics_db` - Data warehouse & advanced analytics
- `genims_audit_db` - Compliance & regulatory audit logs

**Recommended: Option C (Three Databases - Maximum Isolation)**

---

## Database Options

### OPTION A: Single Database (Simplest)

| Database | Purpose | Tables | Size |
|----------|---------|--------|------|
| `genims_reporting_db` | All reporting, analytics, audit | 60+ | 2-3 GB |

**Pros**: Simple setup, easy to manage  
**Cons**: Mixed concerns, harder to scale separately

---

### OPTION B: Two Databases (Recommended) ⭐

| Database | Purpose | Tables | Size |
|----------|---------|--------|------|
| `genims_reporting_db` | Dashboards & KPI reporting | 30-35 | 1-1.5 GB |
| `genims_audit_db` | Compliance, audit, event logs | 25-30 | 1-1.5 GB |

**Total**: 2 Databases | 60-65 Tables | 2-3 GB  
**Pros**: Clear separation of concerns, independent scaling  
**Cons**: Need to sync between databases

---

### OPTION C: Three Databases (Maximum Isolation)

| Database | Purpose | Tables | Size |
|----------|---------|--------|------|
| `genims_reporting_db` | Operational dashboards | 20 | 800 MB |
| `genims_analytics_db` | Data warehouse & analytics | 25 | 1 GB |
| `genims_audit_db` | Compliance & regulatory logs | 20 | 700 MB |

**Total**: 3 Databases | 65 Tables | 2.5 GB  
**Pros**: Maximum isolation, specialized storage, independent scaling, clear ownership  
**Cons**: Complex ETL (manageable with automation), more connections

---

## Recommended Architecture

### Option C: Three MySQL Databases (Maximum Isolation) ⭐

```
PostgreSQL (13 Operational Databases)
    ↓ ETL Sync (Hourly)
    ├─→ genims_reporting_db (Operational Dashboards & KPIs)
    ├─→ genims_analytics_db (Data Warehouse & Analytics)
    └─→ genims_audit_db (Compliance & Audit Logs)
```

#### Why Option C - Maximum Isolation?

✅ **Complete Functional Separation**
- Reporting DB: Real-time dashboards & KPIs
- Analytics DB: Historical analysis & data warehouse
- Audit DB: Compliance & regulatory logging

✅ **Independent Scaling & Optimization**
- Reporting DB: Optimized for fast reads (dashboards)
- Analytics DB: Optimized for complex queries (analytics)
- Audit DB: Optimized for append-only workloads (immutable logs)

✅ **Specialized Data Retention**
- Reporting: 12-24 months (recent trends)
- Analytics: 5-7 years (historical analysis)
- Audit: 7-10 years (regulatory requirement)

✅ **Security & Access Control**
- Reporting: Business users, sales, operations
- Analytics: Data analysts, scientists, executives
- Audit: Compliance, security, legal teams

✅ **Independent Backup & Recovery**
- Reporting: Daily snapshots (can lose recent data)
- Analytics: Weekly full backups (important historical data)
- Audit: Continuous replication (critical for compliance)

✅ **Technology Specialization**
- Reporting: Row-based storage, fast single-table queries
- Analytics: Columnar storage, efficient OLAP queries
- Audit: Immutable append-only, bloom filters for searching

---

## Database 1: GenIMS Reporting

### Purpose
Fast operational reporting and business intelligence dashboards

### Connection
```
mysql://user:pass@insights-db.mysql.database.azure.com:3306/genims_reporting_db
```

### Estimated Size
1-1.5 GB (initial) → 2-3 GB (after 12 months)

### Table Categories (35 tables)

#### 1. Daily Performance Summary Tables (8 tables)

```sql
-- Machine Performance
machine_performance_daily
  - machine_id, date, availability%, performance%, quality%
  - oee_overall, downtime_minutes, fault_count
  - updated_at (TIMESTAMP)
  
line_performance_daily
  - production_line_id, date, line_utilization%, throughput
  - oee_daily, defect_count, labor_hours
  - updated_at

factory_performance_daily
  - factory_id, date, factory_utilization%
  - total_units_produced, total_revenue, cost_of_goods
  - updated_at

oee_daily_summary
  - machine_id, date
  - availability, performance, quality
  - oee_calculated, trend_vs_yesterday
  - updated_at
```

#### 2. Production Reporting (6 tables)

```sql
production_summary_daily
  - date, factory_id, line_id
  - planned_quantity, actual_quantity, variance%
  - labor_hours, material_cost, overhead_cost
  - updated_at

work_order_summary
  - work_order_id, date_started, date_completed
  - sku, quantity_planned, quantity_completed, quantity_scrap
  - labor_hours_actual, cost_actual, status
  - updated_at

material_consumption_daily
  - date, material_id, plant_location
  - quantity_consumed, cost_consumed, unit_cost
  - scrap_quantity, scrap_cost
  - updated_at

production_schedule_performance
  - date, production_line_id
  - schedule_compliance%, on_time_delivery%
  - delay_minutes_total, root_causes
  - updated_at

quality_summary_daily
  - date, factory_id, product_id
  - units_inspected, units_passed, defect_rate%
  - major_defects, minor_defects, rework_cost
  - updated_at

downtime_summary_daily
  - date, machine_id, production_line_id
  - downtime_minutes, planned_downtime, unplanned_downtime
  - primary_reason, secondary_reason
  - updated_at
```

#### 3. Sales & Revenue Reporting (6 tables)

```sql
sales_order_summary
  - date, order_date, delivery_date
  - customer_id, salesperson_id, region
  - total_amount, margin%, margin_amount
  - status, payment_status
  - updated_at

sales_by_product
  - date, product_id, product_name, category
  - units_sold, revenue_total, average_price
  - margin_percentage, trend_vs_month_ago%
  - updated_at

sales_by_customer
  - date, customer_id, customer_name
  - total_orders, total_revenue, average_order_value
  - order_frequency, growth_rate%
  - updated_at

sales_forecast_actuals
  - period_month, product_id
  - forecast_units, forecast_revenue
  - actual_units, actual_revenue, variance%
  - accuracy_metric
  - updated_at

sales_rep_performance
  - date, salesperson_id, rep_name
  - total_sales, target_vs_actual%, commission_amount
  - customer_count, win_rate%
  - updated_at

customer_segment_analysis
  - date, segment, customer_count
  - total_revenue, average_revenue_per_customer
  - churn_rate%, growth_rate%
  - updated_at
```

#### 4. Financial Reporting (8 tables)

```sql
profit_and_loss_daily
  - date, accounting_period
  - revenue_total, cost_of_goods_sold, gross_margin
  - operating_expenses, operating_income
  - interest_expense, taxes, net_income
  - updated_at

balance_sheet_summary
  - date, accounting_period
  - current_assets, fixed_assets, total_assets
  - current_liabilities, long_term_liabilities, total_liabilities
  - shareholders_equity
  - updated_at

cash_flow_summary
  - date, accounting_period
  - operating_cash_flow, investing_cash_flow, financing_cash_flow
  - net_change_in_cash, cash_balance_beginning, cash_balance_ending
  - updated_at

budget_vs_actual
  - period_month, cost_center_id, cost_center_name
  - budget_amount, actual_amount, variance_amount, variance_%
  - status (under/over budget)
  - updated_at

revenue_by_product
  - date, product_id, product_name
  - units_sold, revenue, cost_of_goods, gross_margin
  - margin_percentage
  - updated_at

revenue_by_geography
  - date, country, region, city
  - total_revenue, total_cost, total_margin
  - customer_count, order_count
  - updated_at

operating_metrics
  - date
  - gross_margin%, operating_margin%, net_margin%
  - return_on_assets%, return_on_equity%
  - asset_turnover, inventory_turnover
  - updated_at

cost_analysis
  - date, cost_center_id
  - material_cost, labor_cost, overhead_cost, total_cost
  - cost_per_unit, cost_trend%
  - updated_at
```

#### 5. Inventory Reporting (5 tables)

```sql
inventory_value_summary
  - date, warehouse_id, location
  - quantity_on_hand, value_at_cost, value_at_market
  - inventory_turnover_days, aging_status
  - updated_at

slow_moving_inventory
  - material_id, material_name
  - quantity_on_hand, cost_value, last_movement_date
  - days_since_movement, recommended_action
  - updated_at

inventory_variance_analysis
  - date, material_id, warehouse_id
  - system_quantity, physical_count, variance_quantity, variance_%
  - variance_cost, root_cause
  - updated_at

stock_level_summary
  - date, material_id, warehouse_id
  - reorder_point, safety_stock, current_stock
  - days_of_supply, stockout_risk%
  - updated_at

inventory_aging_report
  - date, material_id
  - age_0_30_days_qty, age_31_60_days_qty, age_61_90_days_qty, age_90plus_qty
  - total_quantity, total_value
  - updated_at
```

#### 6. Procurement Reporting (4 tables)

```sql
purchase_order_summary
  - date, order_date, due_date
  - supplier_id, buyer_id, cost_center
  - total_amount, status, payment_status
  - on_time_delivery%, cost_variance%
  - updated_at

supplier_performance_summary
  - date, supplier_id, supplier_name
  - total_orders, total_spent, payment_terms
  - on_time_delivery%, quality_rating
  - price_competitiveness, responsiveness_rating
  - updated_at

purchase_price_variance
  - date, material_id, supplier_id
  - standard_price, actual_price, unit_price_variance%
  - quantity_ordered, total_variance_amount
  - updated_at

delivery_performance_summary
  - date, supplier_id
  - total_deliveries, on_time_deliveries
  - on_time_delivery%, average_days_late
  - quality_acceptance_rate%
  - updated_at
```

### Load Strategy for GenIMS Reporting

#### Step 1: Create Schema

```bash
mysql -h insights-db.mysql.database.azure.com -u turintonadmin -p genims_reporting_db < schema/mysql_reporting_schema.sql
```

#### Step 2: Initialize Tables (Empty)

All tables created with structure but no data initially.

#### Step 3: ETL Sync Process

```bash
# Hourly sync from PostgreSQL → MySQL
python3 scripts/etl_postgres_to_mysql_reporting.py --frequency hourly

# Or start as daemon
python3 scripts/etl_postgres_to_mysql_reporting.py --mode daemon &
```

#### Step 3: Create Indexes for Performance

```sql
-- Machine Performance
CREATE INDEX idx_machine_perf_machine_date ON machine_performance_daily(machine_id, date DESC);
CREATE INDEX idx_line_perf_line_date ON line_performance_daily(production_line_id, date DESC);

-- Production
CREATE INDEX idx_prod_summary_date ON production_summary_daily(date DESC);
CREATE INDEX idx_work_order_date ON work_order_summary(date_started DESC);

-- Sales
CREATE INDEX idx_sales_order_date ON sales_order_summary(order_date DESC);
CREATE INDEX idx_sales_product ON sales_by_product(date DESC, product_id);

-- Financial
CREATE INDEX idx_pl_period ON profit_and_loss_daily(accounting_period DESC);
CREATE INDEX idx_budget_period ON budget_vs_actual(period_month DESC);

-- Inventory
CREATE INDEX idx_inventory_value_date ON inventory_value_summary(date DESC);
CREATE INDEX idx_slow_moving_movement ON slow_moving_inventory(last_movement_date);
```

---

## Database 2: GenIMS Audit (Optional)

### Purpose
Compliance, audit trails, and regulatory logging (7-year retention)

### Connection
```
mysql://user:pass@insights-db.mysql.database.azure.com:3306/genims_audit_db
```

### Estimated Size
1-1.5 GB (initial) → 5-10 GB (after 7 years)

### Table Categories (30 tables)

#### 1. System Audit Tables (8 tables)

```sql
-- Track all system changes
system_audit_log
  - audit_id (PRIMARY KEY), audit_timestamp
  - entity_type (TABLE NAME), entity_id, operation (INSERT/UPDATE/DELETE)
  - old_values (JSON), new_values (JSON)
  - user_id, session_id, ip_address
  - timestamp_created (IMMUTABLE)

user_activity_log
  - activity_id (PRIMARY KEY), activity_timestamp
  - user_id, user_email, action (LOGIN/LOGOUT/READ/WRITE/DELETE)
  - resource_type, resource_id
  - ip_address, user_agent
  - success (YES/NO), error_message

data_change_audit
  - change_id (PRIMARY KEY), change_timestamp
  - table_name, column_name, primary_key
  - old_value, new_value, change_type
  - user_id, change_reason
  - approved_by, approval_timestamp

exception_log
  - exception_id (PRIMARY KEY), exception_timestamp
  - exception_type, module_name
  - message, stack_trace
  - severity (CRITICAL/HIGH/MEDIUM/LOW)
  - user_id, session_id

integration_audit_log
  - integration_id (PRIMARY KEY), integration_timestamp
  - source_system, target_system, event_type
  - record_count, success (YES/NO), error_message
  - duration_seconds

batch_job_execution_log
  - job_id (PRIMARY KEY), execution_timestamp
  - job_name, job_type, status (COMPLETED/FAILED/PARTIAL)
  - records_processed, records_failed
  - execution_time_seconds, next_run_timestamp

financial_transaction_audit
  - transaction_id (PRIMARY KEY), transaction_timestamp
  - transaction_type, amount, account_id
  - user_id, approval_status, approved_by
  - reversal_transaction_id (if reversed)

security_event_log
  - event_id (PRIMARY KEY), event_timestamp
  - event_type (AUTH_FAILURE/PERMISSION_DENIED/SUSPICIOUS_ACTIVITY)
  - user_id, resource_accessed
  - severity (CRITICAL/HIGH), action_taken
```

#### 2. Compliance & Regulatory Tables (12 tables)

```sql
sla_compliance_tracking
  - sla_id (PRIMARY KEY), tracking_date
  - sla_type (DELIVERY/RESPONSE/RESOLUTION), target_metric
  - target_value, actual_value, compliance_status
  - compliant (YES/NO), violation_count

gdpr_data_request_log
  - request_id (PRIMARY KEY), request_date
  - data_subject_id, request_type (ACCESS/DELETE/PORTABILITY)
  - status (PENDING/COMPLETED/DENIED)
  - completion_date, fulfilled_by, notes

data_retention_schedule
  - retention_id (PRIMARY KEY)
  - table_name, retention_period_years
  - deletion_date_calculated, deletion_status
  - last_review_date, next_review_date

regulatory_compliance_checklist
  - checklist_id (PRIMARY KEY), review_date
  - regulation_name (HIPAA/GDPR/SOX/PCI-DSS)
  - requirement_item, status (COMPLIANT/NON_COMPLIANT/NOT_APPLICABLE)
  - evidence, remediation_plan

audit_trail_integrity
  - audit_id (PRIMARY KEY), verification_timestamp
  - audit_log_id, hash_sha256, previous_hash_sha256
  - verification_status (VALID/TAMPERED)
  - verified_by

legal_hold_records
  - hold_id (PRIMARY KEY), hold_date
  - case_name, legal_matter_id
  - affected_entities (JSON), hold_reason
  - hold_expiration_date, released_date

document_retention_log
  - document_id (PRIMARY KEY), retention_date
  - document_type, retention_requirement
  - deletion_scheduled_date, deletion_executed_date
  - archived_location

privacy_incident_report
  - incident_id (PRIMARY KEY), incident_date
  - incident_description, affected_records_count
  - severity_level, root_cause
  - remediation_taken, regulatory_notification_date

third_party_access_log
  - access_id (PRIMARY KEY), access_date
  - third_party_name, data_accessed
  - access_justification, duration
  - access_approved_by, access_revoked_date

compliance_gap_analysis
  - gap_id (PRIMARY KEY), analysis_date
  - regulation, gap_description, severity
  - remediation_plan, target_completion_date
  - actual_completion_date, verification_status

vendor_compliance_status
  - vendor_id (PRIMARY KEY), assessment_date
  - vendor_name, compliance_score
  - certifications, last_audit_date
  - next_audit_required_date

change_management_log
  - change_id (PRIMARY KEY), change_date
  - change_description, change_type
  - approved_by, approval_date
  - implementation_date, rollback_if_failed
```

#### 3. Business Rules & Validation Tables (10 tables)

```sql
validation_rule_execution
  - validation_id (PRIMARY KEY), execution_timestamp
  - rule_name, entity_type, validation_result
  - records_passed, records_failed, failure_reason

approval_workflow_history
  - workflow_id (PRIMARY KEY), workflow_timestamp
  - document_id, workflow_status (SUBMITTED/APPROVED/REJECTED)
  - approver_id, approval_date, comments

contract_milestone_tracking
  - milestone_id (PRIMARY KEY), tracking_date
  - contract_id, milestone_description
  - planned_date, actual_date, status_complete
  - responsible_party, completion_evidence

quality_hold_records
  - hold_id (PRIMARY KEY), hold_date
  - material_id, reason_on_hold
  - released_date, released_by
  - analysis_performed, root_cause_identified

dispute_resolution_log
  - dispute_id (PRIMARY KEY), dispute_date
  - dispute_type, party_1, party_2
  - amount_in_dispute, status (OPEN/RESOLVED)
  - resolution_date, resolution_method, settlement_amount

warranty_claim_audit
  - claim_id (PRIMARY KEY), claim_date
  - product_id, customer_id, claim_amount
  - claim_status, approval_date, approved_by
  - payout_date, settlement_amount

product_recall_log
  - recall_id (PRIMARY KEY), recall_date
  - product_id, recall_reason
  - units_recalled, units_returned, units_destroyed
  - regulatory_authority, completion_date

customer_complaint_tracking
  - complaint_id (PRIMARY KEY), complaint_date
  - customer_id, complaint_category
  - severity_level, status (OPEN/RESOLVED)
  - resolution_date, compensation_amount

supplier_performance_violation
  - violation_id (PRIMARY KEY), violation_date
  - supplier_id, violation_type
  - severity, impact_on_operations
  - remediation_required, corrective_action_plan

internal_audit_findings
  - finding_id (PRIMARY KEY), audit_date
  - finding_description, severity
  - responsible_department, corrective_action
  - target_completion_date, actual_completion_date
```

### Load Strategy for GenIMS Audit

#### Step 1: Create Audit Schema

```bash
mysql -h insights-db.mysql.database.azure.com -u turintonadmin -p genims_audit_db < schema/mysql_audit_schema.sql
```

#### Step 2: Configure Audit Triggers (PostgreSQL side)

PostgreSQL databases send ALL changes to MySQL audit tables via triggers/daemons.

#### Step 3: Start Audit Collection

```bash
# Real-time audit sync from PostgreSQL
python3 scripts/audit_collection_daemon.py --target mysql &

# Compliance reporting
python3 scripts/compliance_report_generator.py --frequency daily &
```

#### Step 4: Configure Data Retention

```sql
-- Auto-delete logs older than 7 years (except financial/legal holds)
CREATE EVENT auto_archive_audit_logs
ON SCHEDULE EVERY 1 DAY
DO
  DELETE FROM system_audit_log 
  WHERE timestamp_created < DATE_SUB(NOW(), INTERVAL 7 YEAR)
  AND NOT EXISTS (SELECT 1 FROM legal_hold_records WHERE affected_entities LIKE CONCAT('%"audit_id":', audit_id, '%'));
```

---

## ETL Strategy

### Data Flow: PostgreSQL → MySQL

```
PostgreSQL (Operational Databases)
    ↓ Real-time CDC (Change Data Capture)
    ├─→ Aggregation & Transformation
    └─→ MySQL (Reporting & Analytics)
         ├─→ genims_reporting_db (Dashboards)
         └─→ genims_audit_db (Compliance)
```

### ETL Processes

#### 1. Hourly Reporting Sync

```python
# Load from all PostgreSQL databases → MySQL Reporting
ETL Process: hourly_reporting_sync
├─ Source: genims_operations_db, genims_manufacturing_db, genims_erp_financial_db, genims_supply_chain_db, genims_crm_db
├─ Transform:
│   ├─ Aggregate hourly metrics
│   ├─ Calculate KPIs (OEE, efficiency, etc.)
│   ├─ Denormalize for reporting
│   └─ Apply business rules
├─ Load: genims_reporting_db
│   ├─ machine_performance_daily
│   ├─ production_summary_daily
│   ├─ sales_order_summary
│   ├─ inventory_value_summary
│   └─ ... (all reporting tables)
└─ Schedule: Every hour (HH:00)
```

#### 2. Real-time Audit Sync

```python
# Capture all changes in real-time → MySQL Audit
ETL Process: real_time_audit_sync
├─ Source: All PostgreSQL databases (triggers/logs)
├─ Transform:
│   ├─ Parse change records
│   ├─ Enrich with context (user, IP, timestamp)
│   ├─ Validate integrity
│   └─ Apply compliance rules
├─ Load: genims_audit_db
│   ├─ system_audit_log
│   ├─ user_activity_log
│   ├─ data_change_audit
│   └─ ... (all audit tables)
└─ Schedule: Real-time (continuous)
```

#### 3. Daily Financial Close

```python
# Close previous day's financial data
ETL Process: daily_financial_close
├─ Source: genims_erp_financial_db
├─ Transform:
│   ├─ Finalize P&L for the day
│   ├─ Verify balanced GL
│   ├─ Calculate margins
│   └─ Archive previous period
├─ Load: genims_reporting_db
│   ├─ profit_and_loss_daily
│   ├─ budget_vs_actual
│   ├─ cash_flow_summary
│   └─ balance_sheet_summary
└─ Schedule: Daily (02:00 AM)
```

### ETL Configuration

```yaml
etl_jobs:
  - name: hourly_reporting_sync
    schedule: "0 * * * *"  # Every hour
    sources:
      - genims_operations_db
      - genims_manufacturing_db
      - genims_erp_financial_db
      - genims_supply_chain_db
      - genims_crm_db
    target: genims_reporting_db
    error_handling: retry 3 times, then alert
    
  - name: real_time_audit_sync
    schedule: continuous
    sources:
      - all PostgreSQL databases
    target: genims_audit_db
    error_handling: critical alert on failure
    
  - name: daily_financial_close
    schedule: "0 2 * * *"  # 2:00 AM daily
    sources:
      - genims_erp_financial_db
    target: genims_reporting_db
    error_handling: retry 3 times, escalate to CFO if failed
    
  - name: compliance_report_generation
    schedule: "0 3 * * *"  # 3:00 AM daily
    sources:
      - genims_audit_db
    target: /reports/compliance
    error_handling: alert compliance team
```

---

## Connection Configuration

### Environment Variables (.env)

```bash
# MySQL Reporting Database
MYSQL_REPORTING_HOST=insights-db.mysql.database.azure.com
MYSQL_REPORTING_PORT=3306
MYSQL_REPORTING_DB=genims_reporting_db
MYSQL_REPORTING_USER=turintonadmin
MYSQL_REPORTING_PASSWORD=Passw0rd123!

# MySQL Audit Database
MYSQL_AUDIT_HOST=insights-db.mysql.database.azure.com
MYSQL_AUDIT_PORT=3306
MYSQL_AUDIT_DB=genims_audit_db
MYSQL_AUDIT_USER=turintonadmin
MYSQL_AUDIT_PASSWORD=Passw0rd123!
```

### Connection Strings

```
MySQL Standard: mysql://user:password@host:port/database
Example: mysql://turintonadmin:Passw0rd123!@insights-db.mysql.database.azure.com:3306/genims_reporting_db
```

### Python Connection Example

```python
import mysql.connector

# Reporting Database Connection
reporting_conn = mysql.connector.connect(
    host=os.getenv('MYSQL_REPORTING_HOST'),
    port=os.getenv('MYSQL_REPORTING_PORT'),
    user=os.getenv('MYSQL_REPORTING_USER'),
    password=os.getenv('MYSQL_REPORTING_PASSWORD'),
    database=os.getenv('MYSQL_REPORTING_DB')
)

# Audit Database Connection
audit_conn = mysql.connector.connect(
    host=os.getenv('MYSQL_AUDIT_HOST'),
    port=os.getenv('MYSQL_AUDIT_PORT'),
    user=os.getenv('MYSQL_AUDIT_USER'),
    password=os.getenv('MYSQL_AUDIT_PASSWORD'),
    database=os.getenv('MYSQL_AUDIT_DB')
)
```

---

## Load Strategy

### Phase 1: Database Creation (2 minutes)

```bash
# Create Reporting Database
mysql -h insights-db.mysql.database.azure.com -u turintonadmin -p -e "CREATE DATABASE genims_reporting_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"

# Create Audit Database
mysql -h insights-db.mysql.database.azure.com -u turintonadmin -p -e "CREATE DATABASE genims_audit_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
```

### Phase 2: Schema Creation (5 minutes)

```bash
# Load Reporting Schema
mysql -h insights-db.mysql.database.azure.com -u turintonadmin -p genims_reporting_db < schema/mysql_reporting_schema.sql

# Load Audit Schema
mysql -h insights-db.mysql.database.azure.com -u turintonadmin -p genims_audit_db < schema/mysql_audit_schema.sql
```

### Phase 3: Initialize with Historical Data (10 minutes)

```bash
# Initial data load from PostgreSQL (one-time full load)
python3 scripts/initial_load_postgres_to_mysql.py \
  --source-dbs all \
  --target-db genims_reporting_db \
  --mode full-load

# Generates initial snapshots of:
# - Daily performance metrics (last 90 days)
# - Sales summaries (last 12 months)
# - Financial data (last 3 periods)
# - Audit logs (last 30 days)
```

### Phase 4: Start ETL Daemons (3 minutes)

```bash
# Start hourly reporting sync
python3 scripts/etl_postgres_to_mysql_reporting.py --mode daemon > logs/etl_reporting.log 2>&1 &

# Start real-time audit sync
python3 scripts/audit_collection_daemon.py > logs/audit_collection.log 2>&1 &

# Start compliance report generator
python3 scripts/compliance_report_generator.py --mode daemon > logs/compliance.log 2>&1 &
```

### Phase 5: Verify Load (5 minutes)

```bash
# Verify Reporting Database
mysql -h insights-db.mysql.database.azure.com -u turintonadmin -p genims_reporting_db -e "SHOW TABLES;"
mysql -h insights-db.mysql.database.azure.com -u turintonadmin -p genims_reporting_db -e "SELECT COUNT(*) FROM machine_performance_daily;"

# Verify Audit Database
mysql -h insights-db.mysql.database.azure.com -u turintonadmin -p genims_audit_db -e "SHOW TABLES;"
mysql -h insights-db.mysql.database.azure.com -u turintonadmin -p genims_audit_db -e "SELECT COUNT(*) FROM system_audit_log;"

# Check ETL daemon status
ps aux | grep "etl_postgres_to_mysql"
ps aux | grep "audit_collection"
```

---

## Maintenance & Operations

### Daily Tasks

```bash
# Monitor ETL daemons
tail -f logs/etl_reporting.log logs/audit_collection.log logs/compliance.log

# Check database sizes
mysql -h insights-db.mysql.database.azure.com -u turintonadmin -p -e "
  SELECT table_schema, 
         ROUND(SUM(data_length+index_length)/1024/1024, 2) AS size_mb
  FROM information_schema.tables 
  WHERE table_schema IN ('genims_reporting_db', 'genims_audit_db')
  GROUP BY table_schema;
"

# Verify data freshness
mysql -h insights-db.mysql.database.azure.com -u turintonadmin -p genims_reporting_db -e "
  SELECT MAX(updated_at) as last_update FROM machine_performance_daily;
"

# Check audit log volume
mysql -h insights-db.mysql.database.azure.com -u turintonadmin -p genims_audit_db -e "
  SELECT COUNT(*) as audit_records FROM system_audit_log 
  WHERE audit_timestamp > DATE_SUB(NOW(), INTERVAL 1 DAY);
"
```

### Weekly Tasks

```bash
# Analyze tables for optimization
mysql -h insights-db.mysql.database.azure.com -u turintonadmin -p genims_reporting_db -e "
  ANALYZE TABLE machine_performance_daily, 
              production_summary_daily, 
              sales_order_summary;
"

# Check for slow queries
mysql -h insights-db.mysql.database.azure.com -u turintonadmin -p -e "
  SELECT query_time, lock_time, sql_text 
  FROM mysql.slow_log 
  ORDER BY query_time DESC LIMIT 10;
"

# Review ETL success rate
mysql -h insights-db.mysql.database.azure.com -u turintonadmin -p genims_audit_db -e "
  SELECT DATE(integration_timestamp), 
         COUNT(*), 
         SUM(IF(success='YES', 1, 0)) as succeeded,
         SUM(IF(success='NO', 1, 0)) as failed
  FROM integration_audit_log
  WHERE integration_timestamp > DATE_SUB(NOW(), INTERVAL 7 DAY)
  GROUP BY DATE(integration_timestamp);
"
```

### Monthly Tasks

```bash
# Full backup of both databases
mysqldump -h insights-db.mysql.database.azure.com -u turintonadmin -p genims_reporting_db > backup_reporting_$(date +%Y%m%d).sql
mysqldump -h insights-db.mysql.database.azure.com -u turintonadmin -p genims_audit_db > backup_audit_$(date +%Y%m%d).sql

# Archive old audit logs (if configured retention)
mysql -h insights-db.mysql.database.azure.com -u turintonadmin -p genims_audit_db -e "
  DELETE FROM system_audit_log 
  WHERE audit_timestamp < DATE_SUB(NOW(), INTERVAL 7 YEAR)
  AND legal_hold_status = 'RELEASED';
"

# Generate compliance report
python3 scripts/compliance_report_generator.py \
  --format pdf \
  --output /reports/compliance_$(date +%Y%m).pdf \
  --send-to compliance@company.com

# Review index usage and rebuild fragmented indexes
mysql -h insights-db.mysql.database.azure.com -u turintonadmin -p genims_reporting_db -e "
  SELECT object_schema, object_name, count_read, count_write, count_delete, count_update 
  FROM performance_schema.table_io_waits_summary_by_table 
  WHERE object_schema = 'genims_reporting_db'
  ORDER BY count_read DESC;
"

# Optimize reporting queries
mysql -h insights-db.mysql.database.azure.com -u turintonadmin -p genims_reporting_db -e "
  OPTIMIZE TABLE machine_performance_daily,
               production_summary_daily,
               sales_order_summary,
               inventory_value_summary;
"
```

### Backup Strategy

| Database | Frequency | Retention | Location |
|----------|-----------|-----------|----------|
| `genims_reporting_db` | Daily | 30 days | Azure Blob Storage |
| `genims_audit_db` | Daily | 7 years | Azure Blob Storage + Cold Archive |

```bash
# Automated backup script
#!/bin/bash
BACKUP_DIR="/backups/mysql"
DATE=$(date +%Y%m%d_%H%M%S)

# Backup Reporting
mysqldump -h insights-db.mysql.database.azure.com \
  -u turintonadmin -p$MYSQL_PASSWORD \
  genims_reporting_db | gzip > $BACKUP_DIR/reporting_$DATE.sql.gz

# Backup Audit
mysqldump -h insights-db.mysql.database.azure.com \
  -u turintonadmin -p$MYSQL_PASSWORD \
  genims_audit_db | gzip > $BACKUP_DIR/audit_$DATE.sql.gz

# Upload to Azure
az storage blob upload --file $BACKUP_DIR/reporting_$DATE.sql.gz \
  --container-name genims-backups --name mysql/reporting_$DATE.sql.gz

az storage blob upload --file $BACKUP_DIR/audit_$DATE.sql.gz \
  --container-name genims-backups --name mysql/audit_$DATE.sql.gz

# Clean up local backups older than 7 days
find $BACKUP_DIR -name "*.sql.gz" -mtime +7 -delete
```

---

## Performance Optimization

### Query Optimization

```sql
-- Add covering indexes for common queries
CREATE INDEX idx_machine_perf_covering 
ON machine_performance_daily(machine_id, date DESC) 
INCLUDE (availability, performance, quality, oee_overall);

CREATE INDEX idx_prod_summary_covering 
ON production_summary_daily(factory_id, date DESC) 
INCLUDE (planned_quantity, actual_quantity, variance_percent);

CREATE INDEX idx_sales_covering 
ON sales_order_summary(order_date DESC, customer_id) 
INCLUDE (total_amount, margin_percent, status);
```

### Partitioning Strategy

```sql
-- Partition reporting tables by date for faster queries
ALTER TABLE machine_performance_daily 
PARTITION BY RANGE (YEAR(date) * 100 + MONTH(date)) (
  PARTITION p_2024_01 VALUES LESS THAN (202401),
  PARTITION p_2024_02 VALUES LESS THAN (202402),
  -- ... more partitions
  PARTITION p_future VALUES LESS THAN MAXVALUE
);

-- Partition audit tables by year (7-year retention)
ALTER TABLE system_audit_log 
PARTITION BY RANGE (YEAR(audit_timestamp)) (
  PARTITION p_2018 VALUES LESS THAN (2019),
  PARTITION p_2019 VALUES LESS THAN (2020),
  -- ... more partitions
  PARTITION p_2025 VALUES LESS THAN (2026)
);
```

### Storage Engine

```sql
-- Use InnoDB for reporting (ACID compliance)
ALTER TABLE machine_performance_daily ENGINE=InnoDB;

-- Consider Archive engine for old audit logs
ALTER TABLE system_audit_log PARTITION p_2018 ENGINE=Archive;
```

---

## Data Volume Estimates

### Reporting Database

| Table | Rows/Day | Rows/Month | Size/Month |
|-------|----------|-----------|-----------|
| machine_performance_daily | 50 | 1.5K | 5 MB |
| production_summary_daily | 100 | 3K | 10 MB |
| sales_order_summary | 200 | 6K | 15 MB |
| Other reporting tables | 500 | 15K | 40 MB |
| **TOTAL** | **850** | **25.5K** | **70 MB/month** |

**Annual Growth**: 840 MB  
**3-Year Retention**: 2.5 GB  
**Estimated Total (with indexes)**: 3-4 GB

### Audit Database

| Table | Rows/Day | Rows/Month | Size/Month |
|-------|----------|-----------|-----------|
| system_audit_log | 10K | 300K | 150 MB |
| user_activity_log | 5K | 150K | 75 MB |
| data_change_audit | 2K | 60K | 30 MB |
| Other audit tables | 5K | 150K | 75 MB |
| **TOTAL** | **22K** | **660K** | **330 MB/month** |

**Annual Growth**: 3.96 GB  
**7-Year Retention**: ~28 GB  
**Estimated Total (with indexes)**: 30-35 GB

---

## Summary

### Key Metrics

| Metric | Value |
|--------|-------|
| **Total MySQL Databases** | 2 (Option B) |
| **Reporting Tables** | 35 |
| **Audit Tables** | 30 |
| **Total MySQL Tables** | 65 |
| **ETL Frequency** | Hourly (reporting), Real-time (audit) |
| **Data Retention** | 12-24 months (reporting), 7 years (audit) |

### Implementation Checklist

- [ ] Create 2 MySQL databases
- [ ] Update .env with connection strings
- [ ] Load reporting schema
- [ ] Load audit schema
- [ ] Create all indexes
- [ ] Configure ETL daemons
- [ ] Start hourly reporting sync
- [ ] Start real-time audit sync
- [ ] Verify data freshness
- [ ] Test backup procedures
- [ ] Set up monitoring
- [ ] Configure compliance reports

### Estimated Timeline

- **Phase 1**: Database Creation → 2 min
- **Phase 2**: Schema Loading → 5 min
- **Phase 3**: Historical Data → 10 min
- **Phase 4**: Start Daemons → 3 min
- **Phase 5**: Verification → 5 min
- **TOTAL** → **25 minutes**

---

## Next Steps

1. **Create .env entries** - Add MySQL connection strings
2. **Create databases** - Run creation commands
3. **Load schemas** - Execute schema SQL files
4. **Create indexes** - Optimize for reporting queries
5. **Start ETL** - Begin hourly sync from PostgreSQL
6. **Start audit collection** - Capture all changes
7. **Verify data** - Check freshness and row counts
8. **Set up monitoring** - Alert on ETL failures
9. **Configure backups** - Daily automated backups
10. **Test compliance reports** - Generate initial reports

---

**Document Status**: Ready for Implementation  
**Last Updated**: December 22, 2025  
**Total Estimated Setup Time**: 25 minutes (excluding initial data transfer time)
