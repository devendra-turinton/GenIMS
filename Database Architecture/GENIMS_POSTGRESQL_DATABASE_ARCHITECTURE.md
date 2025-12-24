# GenIMS PostgreSQL Database Architecture
## 13 Separate Databases - Maximum Separation

**Document Version**: 3.0  
**Status**: Production Ready  
**Focus**: 13 PostgreSQL Databases - One Per Module

---

## Quick Reference

| DB # | Database Name | Module | Tables | Size |
|------|---|---|---|---|
| 1 | `genims_master_db` | Master Data | 15 | 100 MB |
| 2 | `genims_operations_db` | Operations/IoT | 6 | 500 MB |
| 3 | `genims_manufacturing_db` | Manufacturing/MES | 10 | 800 MB |
| 4 | `genims_maintenance_db` | CMMS | 23 | 600 MB |
| 5 | `genims_quality_db` | QMS | 30 | 700 MB |
| 6 | `genims_erp_db` | ERP Core | 35+ | 1.2 GB |
| 7 | `genims_financial_db` | Financial GL | 29 | 900 MB |
| 8 | `genims_wms_db` | WMS | 19 | 700 MB |
| 9 | `genims_tms_db` | TMS | 24 | 600 MB |
| 10 | `genims_crm_db` | CRM | 25 | 800 MB |
| 11 | `genims_service_db` | Service | 27 | 900 MB |
| 12 | `genims_hr_db` | HR/HCM | 32 | 1 GB |
| 13 | `genims_supplier_db` | Supplier Portal | 28 | 700 MB |
| **TOTAL** | **13 Databases** | **All Modules** | **343 Tables** | **9.5 GB** |

---

## Setup Instructions

### Run Full Setup (All 4 Steps)
```bash
cd /Users/devendrayadav/insightql/GenIMS
python3 scripts/full_setup.py
```

**What it does:**
1. Creates 13 databases
2. Loads schemas from SQL files
3. Generates historical data
4. Loads data into PostgreSQL
5. Produces comprehensive logs

**Timeline:** ~2-3 hours (first run)

### Configuration
Edit `.env` file with your credentials:
```bash
POSTGRES_HOST=insights-db.postgres.database.azure.com
POSTGRES_PORT=5432
POSTGRES_USERNAME=turintonadmin
POSTGRES_PASSWORD=your_password
```

---

## Connection Strings

```
postgresql://turintonadmin:password@insights-db.postgres.database.azure.com:5432/genims_master_db
postgresql://turintonadmin:password@insights-db.postgres.database.azure.com:5432/genims_operations_db
postgresql://turintonadmin:password@insights-db.postgres.database.azure.com:5432/genims_manufacturing_db
... etc for remaining 10 databases
```

---

## Key Files

| Location | Purpose |
|----------|---------|
| `scripts/full_setup.py` | Main orchestrator - runs all 4 phases |
| `scripts/config.env` | Database connection configuration |
| `.backups/` | Backup folder with alternative/old files |
| `01-12/` folders | Data generators, schemas, JSON files |

---

## Data Dependencies

**Master Data First:**
- `genims_master_db` loads first (contains reference data)
- All other databases reference master tables

**Load Order:**
1. Master → Operations → Manufacturing → Maintenance → Quality → ERP → Financial → WMS → TMS → CRM → Service → HR → Supplier

---

## Verification Commands

```bash
# Check databases exist
psql -h insights-db.postgres.database.azure.com -U turintonadmin -l | grep genims

# Check table counts per database
psql -h insights-db.postgres.database.azure.com -U turintonadmin -d genims_master_db -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='public';"

# Check record counts
psql -h insights-db.postgres.database.azure.com -U turintonadmin -d genims_operations_db -c "SELECT COUNT(*) FROM sensor_data;"

# Database sizes
psql -h insights-db.postgres.database.azure.com -U turintonadmin -c "SELECT datname, pg_size_pretty(pg_database_size(datname)) FROM pg_database WHERE datname LIKE 'genims%' ORDER BY pg_database_size(datname) DESC;"
```

---

## Maintenance

### Daily
- Monitor logs: `tail -f setup_output.log`
- Check database health: Connection counts, sizes

### Weekly  
- Analyze indexes: `ANALYZE` on high-write databases
- Vacuum unused space: `VACUUM ANALYZE`

### Monthly
- Backup all databases to Azure Blob Storage
- Archive old operational data (90+ days)
- Review performance queries

---

## Data Volumes

**Initial Load:** 1.6M records across 343 tables (~9.5 GB)

**Growth (Annual):**
- Operations DB: +36.5M rows (fastest growing)
- Manufacturing: +1.83M rows
- Others: +2.7M rows combined
- **Total 12-month projection:** ~50 GB
