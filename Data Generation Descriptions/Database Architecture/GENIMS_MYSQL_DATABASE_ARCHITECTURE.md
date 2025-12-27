# GenIMS MySQL Database Architecture
## Reporting, Analytics & Audit Layer

**Document Version**: 3.0  
**Status**: Production Ready  
**Focus**: MySQL - Reporting, Analytics & Audit (2 Databases)

---

## Quick Reference

| Database | Purpose | Tables | Size | Retention |
|----------|---------|--------|------|-----------|
| `genims_reporting_db` | Dashboards & KPIs | 35 | 1-2 GB | 12 months |
| `genims_audit_db` | Compliance & Audit | 30 | 1-5 GB | 7 years |
| **TOTAL** | **2 Databases** | **65 Tables** | **2-7 GB** | **Mixed** |

---

## Overview

MySQL serves as the **reporting, analytics, and audit layer**, receiving denormalized data from PostgreSQL via hourly ETL syncs. Provides:

- **Fast dashboards** - Denormalized reporting tables
- **Compliance tracking** - 7-year regulatory logs
- **Audit trails** - All changes captured
- **KPI aggregation** - Performance metrics

---

## Architecture

```
PostgreSQL (13 Operational Databases)
    ↓ Hourly ETL Sync
    ├─→ genims_reporting_db (Dashboards & Analytics)
    └─→ genims_audit_db (Compliance & Audit Logs)
```

### Recommended: Option B: Two MySQL Databases ⭐

```
PostgreSQL (13 Operational Databases)
    ↓ ETL Sync (Hourly)
    ├─→ genims_reporting_db (Operational Dashboards & KPIs)
    ├─→ genims_analytics_db (Data Warehouse & Analytics)
    └─→ genims_audit_db (Compliance & Audit Logs)
```
**Why Two Databases?**
- Clear separation: Reporting vs. Compliance
- Independent scaling for read-heavy workloads
- Separate backup/retention policies
- Easier access control (analysts vs. auditors)

---

## Database 1: Reporting

**Purpose:** Operational dashboards, KPIs, analytics  
**Tables:** 35 (performance, sales, financial, inventory)  
**Size:** 1-2 GB initial → 3-4 GB after 12 months  
**Refresh:** Hourly via ETL

**Key Tables:**
- `machine_performance_daily` - OEE, availability, throughput
- `production_summary_daily` - Units, labor, costs
- `sales_order_summary` - Revenue, margin, customer
- `profit_and_loss_daily` - Financial close data
- `inventory_value_summary` - Stock levels, valuation
- And 30+ more reporting tables

**Connection:**
```
mysql://user:pass@insights-db.mysql.database.azure.com:3306/genims_reporting_db
```

---

## Database 2: Audit

**Purpose:** Compliance, audit trails, regulatory logging  
**Tables:** 30 (system audit, compliance, legal holds)  
**Size:** 1-5 GB initial → 28-35 GB after 7 years  
**Retention:** 7 years (regulatory requirement)

**Key Tables:**
- `system_audit_log` - All changes (user, table, values)
- `user_activity_log` - Login, read, write, delete actions
- `data_change_audit` - Before/after values
- `sla_compliance_tracking` - SLA violations
- `gdpr_data_request_log` - GDPR access/delete requests
- And 25+ more compliance tables

**Connection:**
```
mysql://user:pass@insights-db.mysql.database.azure.com:3306/genims_audit_db
```

---

## Setup & Configuration

### Environment Variables (.env)

```bash
MYSQL_REPORTING_HOST=insights-db.mysql.database.azure.com
MYSQL_REPORTING_PORT=3306
MYSQL_REPORTING_DB=genims_reporting_db
MYSQL_REPORTING_USER=turintonadmin
MYSQL_REPORTING_PASSWORD=your_password

MYSQL_AUDIT_HOST=insights-db.mysql.database.azure.com
MYSQL_AUDIT_PORT=3306
MYSQL_AUDIT_DB=genims_audit_db
MYSQL_AUDIT_USER=turintonadmin
MYSQL_AUDIT_PASSWORD=your_password
```

### Create Databases

```bash
# Reporting Database
mysql -h insights-db.mysql.database.azure.com -u turintonadmin -p -e \
  "CREATE DATABASE genims_reporting_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"

# Audit Database
mysql -h insights-db.mysql.database.azure.com -u turintonadmin -p -e \
  "CREATE DATABASE genims_audit_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
```

### Load Schemas

```bash
# Create all tables
mysql -h insights-db.mysql.database.azure.com -u turintonadmin -p genims_reporting_db < schema/mysql_reporting_schema.sql
mysql -h insights-db.mysql.database.azure.com -u turintonadmin -p genims_audit_db < schema/mysql_audit_schema.sql

# Create indexes for fast queries
mysql -h insights-db.mysql.database.azure.com -u turintonadmin -p genims_reporting_db < schema/mysql_reporting_indexes.sql
mysql -h insights-db.mysql.database.azure.com -u turintonadmin -p genims_audit_db < schema/mysql_audit_indexes.sql
```

---

## ETL Data Flow

```
PostgreSQL (Operational)
    ↓
Transform & Aggregate
    ↓
MySQL Reporting (Hourly Sync)
    ├─ machine_performance_daily
    ├─ production_summary_daily
    ├─ sales_order_summary
    ├─ profit_and_loss_daily
    └─ ... (35 tables)

PostgreSQL (Real-time Logs)
    ↓
MySQL Audit (Real-time Sync)
    ├─ system_audit_log
    ├─ user_activity_log
    ├─ data_change_audit
    ├─ sla_compliance_tracking
    └─ ... (30 tables)
```

### ETL Processes

| Job | Source | Target | Schedule | Frequency |
|-----|--------|--------|----------|-----------|
| Hourly Reporting Sync | PostgreSQL (all 13 DBs) | genims_reporting_db | Every hour | HH:00 |
| Real-time Audit Sync | PostgreSQL (triggers/logs) | genims_audit_db | Continuous | Real-time |
| Daily Financial Close | genims_erp_db | genims_reporting_db | Daily | 02:00 AM |
| Compliance Report Gen | genims_audit_db | /reports/ | Daily | 03:00 AM |

---

## Verification Commands

```bash
# Check databases exist
mysql -h insights-db.mysql.database.azure.com -u turintonadmin -p -e "SHOW DATABASES LIKE 'genims_%';"

# Check table counts
mysql -h insights-db.mysql.database.azure.com -u turintonadmin -p genims_reporting_db -e "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='genims_reporting_db';"
mysql -h insights-db.mysql.database.azure.com -u turintonadmin -p genims_audit_db -e "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='genims_audit_db';"

# Check data freshness
mysql -h insights-db.mysql.database.azure.com -u turintonadmin -p genims_reporting_db -e "SELECT MAX(updated_at) FROM machine_performance_daily;"

# Check audit log volume
mysql -h insights-db.mysql.database.azure.com -u turintonadmin -p genims_audit_db -e "SELECT COUNT(*) FROM system_audit_log WHERE audit_timestamp > DATE_SUB(NOW(), INTERVAL 1 DAY);"

# Database sizes
mysql -h insights-db.mysql.database.azure.com -u turintonadmin -p -e "
  SELECT table_schema, 
         ROUND(SUM(data_length+index_length)/1024/1024, 2) AS size_mb
  FROM information_schema.tables 
  WHERE table_schema IN ('genims_reporting_db', 'genims_audit_db')
  GROUP BY table_schema;
"
```

---

## Maintenance

### Daily
- Monitor ETL daemons: `tail -f logs/etl_*.log`
- Check data freshness: Last `updated_at` in reporting tables
- Monitor audit log growth

### Weekly
- Analyze tables: `ANALYZE TABLE machine_performance_daily, ...`
- Check slow queries: Review `mysql.slow_log`
- Verify ETL success rate

### Monthly
- Full backup: `mysqldump` both databases to Azure
- Archive old audit logs (older than 7 years)
- Generate compliance reports
- Optimize fragmented indexes: `OPTIMIZE TABLE ...`

### Backup Strategy

| Database | Frequency | Retention | Location |
|----------|-----------|-----------|----------|
| genims_reporting_db | Daily | 30 days | Azure Blob Storage |
| genims_audit_db | Daily | 7 years | Azure Blob Storage + Cold Archive |

```bash
# Daily automated backup
mysqldump -h insights-db.mysql.database.azure.com -u turintonadmin -p genims_reporting_db | gzip > backup_reporting_$(date +%Y%m%d).sql.gz
mysqldump -h insights-db.mysql.database.azure.com -u turintonadmin -p genims_audit_db | gzip > backup_audit_$(date +%Y%m%d).sql.gz

# Upload to Azure
az storage blob upload --file backup_reporting_*.sql.gz --container-name genims-backups
az storage blob upload --file backup_audit_*.sql.gz --container-name genims-backups

# Clean up local backups older than 7 days
find backup_*.sql.gz -mtime +7 -delete
```

---

## Data Volumes

### Initial Load

| Database | Tables | Rows | Size |
|----------|--------|------|------|
| genims_reporting_db | 35 | 100K | 1 GB |
| genims_audit_db | 30 | 50K | 500 MB |
| **TOTAL** | **65** | **150K** | **1.5 GB** |

### Annual Growth

| Database | Daily Growth | Annual | 12-Month Total |
|----------|--------------|--------|-----------------|
| genims_reporting_db | 1K rows | 365K rows | 2-3 GB |
| genims_audit_db | 22K rows | 8M rows | 5-10 GB |
| **TOTAL** | **23K rows** | **8.4M rows** | **7-13 GB** |

### 7-Year Retention (Audit)

```
Year 1: 5-10 GB
Year 2: 10-15 GB
Year 3: 15-20 GB
...
Year 7: 28-35 GB (total)
```

---

## Summary

| Metric | Value |
|--------|-------|
| **MySQL Databases** | 2 |
| **Total Tables** | 65 |
| **ETL Frequency** | Hourly (reporting), Real-time (audit) |
| **Data Retention** | 12 months (reporting), 7 years (audit) |
| **Initial Size** | 1.5 GB |
| **12-Month Size** | 7-13 GB |

### Implementation Checklist

- [ ] Create 2 MySQL databases
- [ ] Update .env with connection strings
- [ ] Load reporting schema
- [ ] Load audit schema
- [ ] Create indexes
- [ ] Start hourly ETL sync daemon
- [ ] Start real-time audit daemon
- [ ] Verify data freshness
- [ ] Set up automated backups
- [ ] Configure monitoring alerts

### Timeline

- **Database Creation:** 2 min
- **Schema Loading:** 5 min
- **Index Creation:** 3 min
- **ETL Setup:** 5 min
- **Verification:** 5 min
- **TOTAL:** 20 minutes

---

**Status**: Production Ready  
**Last Updated**: December 23, 2025
