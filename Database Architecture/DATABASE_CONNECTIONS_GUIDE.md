# GenIMS Environment Configuration - Database Connections

## Overview

This file documents the connection strings required for the new maximum separation database architecture.

**Total Databases**: 17 (13 PostgreSQL + 3 MySQL + 1 MongoDB)

---

## PostgreSQL Connection Strings (13 Databases)

```env
# Master Data Database (Foundation)
POSTGRES_MASTER_HOST=your-postgres-server.postgres.database.azure.com
POSTGRES_MASTER_PORT=5432
POSTGRES_MASTER_USER=your_username
POSTGRES_MASTER_PASSWORD=your_password
POSTGRES_MASTER_DB=genims_master_db

# Operations/IoT Database (Real-time data)
POSTGRES_OPERATIONS_HOST=your-postgres-server.postgres.database.azure.com
POSTGRES_OPERATIONS_PORT=5432
POSTGRES_OPERATIONS_USER=your_username
POSTGRES_OPERATIONS_PASSWORD=your_password
POSTGRES_OPERATIONS_DB=genims_operations_db

# Manufacturing/MES Database
POSTGRES_MANUFACTURING_HOST=your-postgres-server.postgres.database.azure.com
POSTGRES_MANUFACTURING_PORT=5432
POSTGRES_MANUFACTURING_USER=your_username
POSTGRES_MANUFACTURING_PASSWORD=your_password
POSTGRES_MANUFACTURING_DB=genims_manufacturing_db

# Maintenance/CMMS Database
POSTGRES_MAINTENANCE_HOST=your-postgres-server.postgres.database.azure.com
POSTGRES_MAINTENANCE_PORT=5432
POSTGRES_MAINTENANCE_USER=your_username
POSTGRES_MAINTENANCE_PASSWORD=your_password
POSTGRES_MAINTENANCE_DB=genims_maintenance_db

# Quality/QMS Database
POSTGRES_QUALITY_HOST=your-postgres-server.postgres.database.azure.com
POSTGRES_QUALITY_PORT=5432
POSTGRES_QUALITY_USER=your_username
POSTGRES_QUALITY_PASSWORD=your_password
POSTGRES_QUALITY_DB=genims_quality_db

# ERP Core Database
POSTGRES_ERP_HOST=your-postgres-server.postgres.database.azure.com
POSTGRES_ERP_PORT=5432
POSTGRES_ERP_USER=your_username
POSTGRES_ERP_PASSWORD=your_password
POSTGRES_ERP_DB=genims_erp_db

# Financial/GL Database
POSTGRES_FINANCIAL_HOST=your-postgres-server.postgres.database.azure.com
POSTGRES_FINANCIAL_PORT=5432
POSTGRES_FINANCIAL_USER=your_username
POSTGRES_FINANCIAL_PASSWORD=your_password
POSTGRES_FINANCIAL_DB=genims_financial_db

# Warehouse/WMS Database
POSTGRES_WMS_HOST=your-postgres-server.postgres.database.azure.com
POSTGRES_WMS_PORT=5432
POSTGRES_WMS_USER=your_username
POSTGRES_WMS_PASSWORD=your_password
POSTGRES_WMS_DB=genims_wms_db

# Transportation/TMS Database
POSTGRES_TMS_HOST=your-postgres-server.postgres.database.azure.com
POSTGRES_TMS_PORT=5432
POSTGRES_TMS_USER=your_username
POSTGRES_TMS_PASSWORD=your_password
POSTGRES_TMS_DB=genims_tms_db

# CRM Database
POSTGRES_CRM_HOST=your-postgres-server.postgres.database.azure.com
POSTGRES_CRM_PORT=5432
POSTGRES_CRM_USER=your_username
POSTGRES_CRM_PASSWORD=your_password
POSTGRES_CRM_DB=genims_crm_db

# Service/Support Database
POSTGRES_SERVICE_HOST=your-postgres-server.postgres.database.azure.com
POSTGRES_SERVICE_PORT=5432
POSTGRES_SERVICE_USER=your_username
POSTGRES_SERVICE_PASSWORD=your_password
POSTGRES_SERVICE_DB=genims_service_db

# HR/HCM Database
POSTGRES_HR_HOST=your-postgres-server.postgres.database.azure.com
POSTGRES_HR_PORT=5432
POSTGRES_HR_USER=your_username
POSTGRES_HR_PASSWORD=your_password
POSTGRES_HR_DB=genims_hr_db

# Supplier Portal Database
POSTGRES_SUPPLIER_HOST=your-postgres-server.postgres.database.azure.com
POSTGRES_SUPPLIER_PORT=5432
POSTGRES_SUPPLIER_USER=your_username
POSTGRES_SUPPLIER_PASSWORD=your_password
POSTGRES_SUPPLIER_DB=genims_supplier_db
```

---

## MySQL Connection Strings (3 Databases)

```env
# Reporting Database (Dashboards & KPIs)
MYSQL_REPORTING_HOST=your-mysql-server.mysql.database.azure.com
MYSQL_REPORTING_PORT=3306
MYSQL_REPORTING_USER=your_username
MYSQL_REPORTING_PASSWORD=your_password
MYSQL_REPORTING_DB=genims_reporting_db

# Analytics Database (Data Warehouse)
MYSQL_ANALYTICS_HOST=your-mysql-server.mysql.database.azure.com
MYSQL_ANALYTICS_PORT=3306
MYSQL_ANALYTICS_USER=your_username
MYSQL_ANALYTICS_PASSWORD=your_password
MYSQL_ANALYTICS_DB=genims_analytics_db

# Audit Database (Compliance & Logs)
MYSQL_AUDIT_HOST=your-mysql-server.mysql.database.azure.com
MYSQL_AUDIT_PORT=3306
MYSQL_AUDIT_USER=your_username
MYSQL_AUDIT_PASSWORD=your_password
MYSQL_AUDIT_DB=genims_audit_db
```

---

## MongoDB Connection String (1 Database)

```env
# MongoDB - Time-series, Logs, and Unstructured Data
MONGODB_HOST=4.213.218.240
MONGODB_PORT=27017
MONGODB_USER=your_username
MONGODB_PASSWORD=your_password
MONGODB_DB=genims_production
MONGODB_URI=mongodb://your_username:your_password@4.213.218.240:27017/genims_production?authSource=admin
```

---

## Connection Summary

| Database System | Count | Purpose | Update Status |
|-----------------|-------|---------|---|
| PostgreSQL | 13 | Operational (OLTP) | ✅ Updated to max separation |
| MySQL | 3 | Reporting/Analytics (OLAP) | ✅ Updated to max separation |
| MongoDB | 1 | Time-Series & Logs | ✅ Already optimal |
| **TOTAL** | **17** | Full Platform | **✅ READY** |

---

## Notes for Implementation

1. **Firewall Configuration** (Azure)
   - Add your client IP to PostgreSQL server firewall rules
   - Add your client IP to MySQL server firewall rules
   - MongoDB should allow direct connections (verify security group)

2. **Connection Pooling**
   - For Python: Use `psycopg2` with connection pooling
   - For MySQL: Use `mysql-connector-python` with pooling
   - For MongoDB: Use PyMongo with connection pooling

3. **High Availability**
   - Consider read replicas for reporting databases
   - Consider failover replicas for operational databases
   - MongoDB replica sets recommended for production

4. **Security**
   - Never commit credentials to git (use .env with .gitignore)
   - Use environment variables for all connection strings
   - Consider using Azure Key Vault for production

5. **Testing**
   - Test each database connection individually
   - Verify schema deployment to each database
   - Check cross-database dependencies work correctly
