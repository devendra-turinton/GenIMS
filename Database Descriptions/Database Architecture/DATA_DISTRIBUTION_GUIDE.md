# GenIMS Data Distribution Guide - PostgreSQL, MySQL, MongoDB

## Overview
Complete mapping of all GenIMS data across 3 databases for optimal performance and scalability.

---

## Database Selection Strategy

| Database | Purpose | Data Type | Use Case |
|----------|---------|-----------|----------|
| **PostgreSQL** | Core transactional data | Structured, Relational | Master data, ERP, MES, core operations |
| **MySQL** | Operational & reporting data | Structured, Relational | Analytics, reporting, audit trails |
| **MongoDB** | Unstructured & time-series data | Document, JSON, Logs | Sensor data, logs, flexible schema |

---

## 📊 COMPLETE DATA DISTRIBUTION

### **DATABASE 1: PostgreSQL (Primary Transactional)**
**Connection**: `insights-db.postgres.database.azure.com:5432/GenIMS`  
**User**: `turintonadmin` / `Passw0rd123`

#### ✅ Module 1: MASTER DATA (15 tables)
- `companies` - Company registry
- `factories` - Manufacturing facilities
- `warehouses` - Storage facilities
- `warehouse_zones` - Warehouse divisions
- `suppliers` - Vendor master
- `customers` - Customer master
- `materials` - Raw materials & components
- `products` - Finished goods
- `bill_of_materials` - Product recipes
- `bom_components` - BOM line items
- `employees` - Employee registry
- `departments` - Organizational units
- `production_lines` - Manufacturing lines
- `machines` - Equipment master
- `material_suppliers` - Material-supplier mapping

**Status**: Load from `01 - Base Data/genims_schema.sql` + `01 - Base Data/genims_master_data_inserts.sql`

---

#### ✅ Module 2: OPERATIONAL DATA / IoT (6 tables)
- `scada_machine_data` - Machine state data
- `sensor_data` - High-frequency sensor readings
- `machine_faults` - Detected faults
- `sensor_health` - Sensor calibration tracking
- `production_runs` - Batch tracking
- `maintenance_events` - Maintenance history

**Status**: Load from `02 - Machine data/genims_operational_schema.sql`

**Data Generation**: Run `02 - Machine data/generate_operational_data.py`

---

#### ✅ Module 3: MES (10 tables)
- `work_orders` - Production work orders
- `operations` - Work order operations
- `material_transactions` - Material consumption
- `quality_inspections` - Quality checks
- `labor_time_entries` - Labor tracking
- `downtime_events` - Production downtime
- `production_schedules` - Production planning
- `electronic_batch_records` - Batch records (eBR)
- `work_order_status_history` - Status tracking
- `mes_integration_log` - Integration audit trail

**Status**: Load from `03 - MES Data/genims_mes_schema.sql`

**Data Generation**: Run `03 - MES Data/generate_mes_historical_data.py`

**Daemon**: Run `03 - MES Data/mes_hourly_daemon.py` for continuous updates

---

#### ✅ Module 4: ERP CORE (35+ tables)
- `materials` - Material master (already in Master Data)
- `bill_of_materials` - BOMs (already in Master Data)
- `routing` - Manufacturing routings
- `suppliers` - Supplier master (already in Master Data)
- `purchase_requisitions` - Purchase requests
- `purchase_requisition_lines` - PR line items
- `purchase_orders` - Purchase orders
- `purchase_order_lines` - PO line items
- `goods_receipts` - Material receipts
- `goods_receipt_lines` - GR line items
- `sales_orders` - Customer orders
- `sales_order_lines` - SO line items
- `production_orders` - Production orders (linked to MES)
- `inventory_balances` - Current stock levels
- `inventory_transactions` - Stock movements
- `inventory_variance` - Variances
- `mrp_runs` - MRP planning runs
- `mrp_elements` - MRP requirements
- `cost_centers` - Accounting cost centers
- `general_ledger` - GL chart of accounts
- `journal_entries` - Accounting entries
- `journal_entry_lines` - Entry line items
- `inspection_plans` - Quality inspection plans
- `inspection_plan_characteristics` - Inspection specs
- `erp_mes_sync_log` - ERP-MES integration log

**Status**: Load from `04 - ERP & MES Integration/genims_erp_schema.sql`

**Data Generation**: Run `04 - ERP & MES Integration/generate_erp_historical_data.py`

**Daemon**: Run `04 - ERP & MES Integration/erp_daily_daemon.py` daily at 2 AM

---

#### ✅ Module 5: FINANCIAL GL + ERP-WMS Sync (29 tables)
**GL Tables (17)**:
- `chart_of_accounts` - Account structure
- `account_balances` - Account balances by period
- `cost_center_balances` - Cost center balances
- `fiscal_periods` - Accounting periods
- `budget_templates` - Budget setup
- `exchange_rates` - Currency rates
- `gl_posting_rules` - Posting rules
- (Plus 10 more GL tables)

**ERP-WMS Sync Tables (12)**:
- `erp_wms_location_mappings` - Location mapping
- `erp_wms_sync_queue` - Sync requests
- `erp_wms_sync_log` - Sync audit trail
- `inventory_allocations` - Allocation tracking
- `reconciliation_templates` - Recon templates
- `snapshot_data` - Inventory snapshots
- (Plus 6 more sync tables)

**Status**: Load from `04 - ERP & MES Integration/genims_erp_schema.sql`

**Daemon**: Run `04 - ERP & MES Integration/financial_sync_daemon.py` every 5 minutes

---

#### ✅ Module 6: WMS (19 tables)
- `warehouses` - Warehouse master (already in Master Data)
- `warehouse_zones` - Zone definitions (already in Master Data)
- `warehouse_aisles` - Aisle layout
- `storage_bins` - Bin locations
- `warehouse_inventory` - Bin-level inventory
- `receiving_tasks` - Inbound tasks
- `putaway_tasks` - Putaway operations
- `pick_waves` - Wave picking
- `wave_lines` - Wave line items
- `picking_tasks` - Pick operations
- `packing_tasks` - Packing operations
- `shipping_tasks` - Shipping operations
- `cycle_count_tasks` - Cycle counting
- `warehouse_equipment` - Equipment registry
- `warehouse_workers` - Labor assignments
- `warehouse_movements` - Movement audit trail
- `slotting_rules` - Bin assignment rules
- `wms_tms_sync_log` - WMS-TMS integration

**Status**: Load from `05 - WMS + TMS/genims_wms_schema.sql`

**Data Generation**: Run `05 - WMS + TMS/generate_wms_tms_historical_data.py`

**Daemon**: Run `05 - WMS + TMS/wms_tms_daemon.py` continuously

---

#### ✅ Module 7: TMS (24 tables)
- `carriers` - Shipping carriers
- `carrier_services` - Service levels
- `carrier_rates` - Rate cards
- `shipments` - Shipment headers
- `shipment_lines` - Shipment line items
- `shipment_packages` - Package details
- `tracking_events` - Tracking updates
- `routes` - Delivery routes
- `route_stops` - Route stops
- `deliveries` - Final delivery
- `proof_of_delivery` - POD records
- `return_orders` - Return authorizations
- `return_order_lines` - Return line items
- `return_shipments` - Return shipments
- `freight_invoices` - Carrier invoices
- `freight_invoice_lines` - Invoice lines
- `wms_tms_sync_log` - Integration log

**Status**: Load from `05 - WMS + TMS/genims_tms_schema.sql`

**Data Generation**: Run `05 - WMS + TMS/generate_wms_tms_historical_data.py`

**Daemon**: Run `05 - WMS + TMS/wms_tms_daemon.py` continuously

---

#### ✅ Module 8: CMMS (23 tables)
- `maintenance_assets` - Equipment registry
- `equipment_meter_readings` - Meter tracking
- `work_orders` - Maintenance work orders
- `work_order_tasks` - Work order tasks
- `labor_time_entries` - Labor tracking
- `pm_schedules` - Preventive maintenance
- `pm_generation_log` - PM generation history
- `work_procedures` - Standard procedures
- `mro_parts` - Spare parts
- `mro_parts_transactions` - Parts movements
- `maintenance_technicians` - Technician registry
- `maintenance_teams` - Team assignments
- `failure_codes` - Failure classification
- `maintenance_cost_centers` - Cost tracking
- `maintenance_costs` - Cost records
- `service_contracts` - AMC/Warranty contracts
- `service_call_logs` - External service calls
- `asset_reliability_metrics` - MTBF/MTTR
- `maintenance_history` - Audit trail
- `cmms_integration_log` - Integration log

**Status**: Load from `06 - CMMS/genims_cmms_schema.sql`

**Data Generation**: Run `06 - CMMS/generate_cmms_historical_data.py`

**Daemon**: Run `06 - CMMS/cmms_daemon.py` continuously

---

#### ✅ Module 9: CRM (25 tables)
- `leads` - Lead registry
- `lead_activities` - Lead interactions
- `accounts` - Customer accounts
- `contacts` - Contact persons
- `customer_interactions` - Interaction history
- `opportunities` - Sales opportunities
- `opportunity_stage_history` - Stage tracking
- `opportunity_products` - Opportunity products
- `sales_forecasts` - Pipeline forecasts
- `activities` - Call/meeting logs
- `tasks` - Follow-up tasks
- `notes` - Internal notes
- `quotations` - Price quotes
- `quotation_lines` - Quote line items
- `campaigns` - Marketing campaigns
- `campaign_members` - Campaign recipients
- `cases` - Support cases
- `case_comments` - Case discussions
- `contracts` - Customer contracts
- `sales_reps` - Sales team
- `sales_territories` - Territory definitions
- `crm_integration_log` - Integration log

**Status**: Load from `07 - CRM/genims_crm_schema.sql`

**Data Generation**: Run `07 - CRM/generate_crm_historical_data.py`

**Daemon**: Run `07 - CRM/crm_daemon.py` continuously

---

#### ✅ Module 10: CUSTOMER SERVICE (27 tables)
- `service_tickets` - Support tickets
- `ticket_comments` - Ticket discussions
- `ticket_attachments` - Attachments
- `kb_categories` - Knowledge base categories
- `kb_articles` - Help articles
- `kb_article_ratings` - Article feedback
- `sla_definitions` - SLA agreements
- `warranty_registrations` - Warranty records
- `warranty_claims` - Warranty claims
- `rma_requests` - Return authorizations
- `rma_line_items` - RMA line items
- `field_service_appointments` - Service appointments
- `field_technicians` - Field technician registry
- `service_parts` - Service parts inventory
- `service_parts_usage` - Parts usage tracking
- `customer_surveys` - Survey templates
- `survey_responses` - Survey responses
- `customer_feedback` - Feedback records
- `escalation_rules` - Escalation config
- `ticket_escalations` - Escalation tracking
- `service_teams` - Support teams
- `service_queues` - Ticket queues
- `service_agents` - Agent registry
- `resolution_codes` - Resolution taxonomy
- `service_metrics_daily` - Daily KPIs
- `portal_users` - Portal access
- `service_integration_log` - Integration log

**Status**: Load from `08 - Support & Service/genims_service_schema.sql`

**Data Generation**: Run `08 - Support & Service/generate_service_historical_data.py`

**Daemon**: Run `08 - Support & Service/service_daemon.py` continuously

---

#### ✅ Module 11: HR/HCM (32 tables)
- `employees` - Employee records (already in Master Data)
- `departments` - Departments (already in Master Data)
- `employee_employment_history` - Career history
- `job_roles` - Job definitions
- `positions` - Budgeted positions
- `skills_catalog` - Skills master
- `employee_skills` - Employee skills
- `role_skill_requirements` - Role requirements
- `training_courses` - Course catalog
- `training_requirements` - Mandatory training
- `training_schedules` - Training sessions
- `training_enrollments` - Attendance records
- `employee_certifications` - Certifications
- `performance_kpis` - Performance metrics
- `performance_reviews` - Review records
- `employee_goals` - Goal tracking
- `shift_schedules` - Shift definitions
- `employee_shifts` - Shift assignments
- `attendance_records` - Daily attendance
- `leave_types` - Leave classifications
- `employee_leave_balances` - Leave accruals
- `leave_requests` - Leave applications
- `onboarding_checklists` - Onboarding templates
- `onboarding_checklist_items` - Checklist items
- `employee_onboarding` - Employee onboarding
- `employee_onboarding_items` - Progress tracking
- `offboarding_records` - Exit procedures
- `career_paths` - Career progression
- `succession_planning` - Succession plans
- `succession_candidates` - Backup candidates
- `safety_incidents` - OSHA incidents
- `ppe_requirements` - PPE requirements
- `hcm_integration_log` - Integration log

**Status**: Load from `09 - HR-HCM/genims_hcm_schema.sql`

**Data Generation**: Run `09 - HR-HCM/generate_hcm_historical_data.py`

**Daemon**: Run `09 - HR-HCM/hcm_daemon.py` continuously

---

#### ✅ Module 12: SUPPLIER PORTAL (28 tables)
- `rfq_headers` - Request for Quote
- `rfq_lines` - RFQ line items
- `rfq_suppliers` - Supplier invitations
- `rfq_responses` - Supplier responses
- `rfq_response_lines` - Response line items
- `quote_comparison` - Multi-supplier comparison
- `supplier_contracts` - Supplier agreements
- `contract_pricing` - Pricing data
- `supplier_performance_metrics` - Performance tracking
- `supplier_scorecards` - Monthly scorecards
- `supplier_rating_history` - Rating history
- `supplier_invoices` - Invoice headers
- `supplier_invoice_lines` - Invoice line items
- `three_way_match_log` - Matching audit trail
- `supplier_qualification` - Qualification status
- `supplier_documents` - Document management
- `supplier_audits` - Audit records
- `audit_findings` - Audit findings
- `supplier_portal_users` - User accounts
- `supplier_communications` - Messaging
- `supplier_notifications` - Alerts
- `purchase_requisitions` - Internal requests
- `purchase_requisition_lines` - PR line items
- `supplier_portal_integration_log` - Integration log

**Status**: Load from `11 - Supplier Portal/genims_supplier_portal.sql`

**Data Generation**: Run `11 - Supplier Portal/generate_supplier_portal_data.py`

**Daemon**: Run `11 - Supplier Portal/supplier_portal_daemon.py` every 5 minutes

---

#### ✅ Module 13: QMS (30 tables)
- `ncr_headers` - Non-conformance reports
- `ncr_defect_details` - Defect details
- `capa_headers` - Corrective actions
- `capa_actions` - Action items
- `quality_audits` - Audit records
- `audit_findings` - Audit findings
- `control_plans` - Control plans
- `control_plan_characteristics` - Inspection specs
- `spc_control_charts` - SPC charts
- `spc_data_points` - SPC measurements
- `measuring_equipment` - Equipment registry
- `calibration_records` - Calibration history
- `calibration_alerts` - Due date alerts
- `quality_documents` - Documents
- `document_revisions` - Revision history
- `customer_complaints` - Customer complaints
- `eight_d_reports` - 8D problem solving
- `ppap_submissions` - PPAP records
- `supplier_quality_metrics` - Supplier quality
- `quality_kpis` - Quality KPIs
- `qms_integration_log` - Integration log

**Status**: Load from `12 - QMS/genims_qms.sql`

**Data Generation**: Run `12 - QMS/generate_qms_data.py`

**Daemon**: Run `12 - QMS/qms_daemon.py` every 5 minutes

---

### **SUMMARY: PostgreSQL Tables**
- **Total Tables**: ~250+
- **Schema Files**: 13 SQL files
- **Data Generators**: 13 Python scripts
- **Running Daemons**: 8+ continuous processes
- **Load Time Estimate**: 30-60 minutes for all schemas + historical data

---

---

## DATABASE 2: MySQL (Operational & Reporting Data)
**Connection**: `insights-db.mysql.database.azure.com:3306/GenIMS`  
**User**: `turintonadmin` / `Passw0rd123!`

### ✅ Data to Store in MySQL

#### 1. **Operational Dashboards & Reporting Tables**
Create denormalized views for faster reporting:

```sql
-- Machine Performance Reporting
- machine_performance_daily
- line_performance_daily
- factory_performance_daily
- oee_daily_summary

-- Sales & Revenue Reporting
- sales_order_summary
- sales_by_product
- sales_by_customer
- sales_forecast_actuals

-- Production Reporting
- production_summary_daily
- work_order_summary
- material_consumption_daily
- quality_summary_daily

-- Financial Reporting
- profit_and_loss_daily
- balance_sheet_summary
- cash_flow_summary
- budget_vs_actual

-- Inventory Reporting
- inventory_value_summary
- slow_moving_inventory
- inventory_variance_analysis
- stock_level_summary

-- Procurement Reporting
- purchase_order_summary
- supplier_performance_summary
- purchase_price_variance
- delivery_performance_summary
```

#### 2. **Audit & Compliance Tables**
```sql
- system_audit_log          -- All system changes
- user_activity_log         -- User actions
- data_change_audit         -- Change tracking
- exception_log             -- Business exceptions
- sla_compliance_tracking   -- SLA monitoring
- regulatory_compliance_log -- Compliance tracking
```

#### 3. **Cache Tables (for faster queries)**
```sql
- customer_summary_cache
- product_summary_cache
- supplier_summary_cache
- employee_summary_cache
- department_summary_cache
```

#### 4. **Event & Alert Tables**
```sql
- system_events             -- System-wide events
- business_alerts          -- Alert queue
- escalation_queue         -- Escalations
- notification_log         -- Notification history
```

#### 5. **Integration & Sync Tables**
```sql
- integration_queue        -- Pending integrations
- integration_log          -- Completed integrations
- error_log               -- Integration errors
- data_sync_status        -- Sync monitoring
```

### **Load Strategy for MySQL**

1. **Create schema first**:
```bash
mysql -h insights-db.mysql.database.azure.com -u turintonadmin -p GenIMS < mysql_reporting_schema.sql
```

2. **Generate initial reporting data**:
```bash
python3 generate_mysql_reporting_data.py
```

3. **Set up automated views** from PostgreSQL (using ETL):
```bash
python3 etl_postgres_to_mysql.py  # Sync data every 1 hour
```

### **SUMMARY: MySQL Data**
- **Tables**: 30-40 reporting & operational tables
- **Purpose**: Analytics, dashboards, audit trails
- **Update Frequency**: Hourly via ETL from PostgreSQL
- **Load Time Estimate**: 10-15 minutes initial + hourly syncs

---

---

## DATABASE 3: MongoDB (Time-Series, Logs, Unstructured Data)
**Connection**: `mongodb://root:turitonadmin65#$%@4.213.218.240:27017/GenIMS`

### ✅ Collections to Store in MongoDB

#### 1. **Sensor & IoT Data (Time-Series)**
```javascript
db.sensor_readings
  {
    _id: ObjectId(),
    machine_id: "M001",
    sensor_id: "S001",
    timestamp: ISODate("2025-12-22T10:30:00Z"),
    value: 95.5,
    unit: "°C",
    status: "normal|warning|alarm",
    raw_data: {...}
  }

db.scada_events
  {
    _id: ObjectId(),
    machine_id: "M001",
    timestamp: ISODate("2025-12-22T10:30:00Z"),
    state: "running|idle|fault|maintenance",
    oee_metrics: {
      availability: 92.5,
      performance: 88.3,
      quality: 99.2
    },
    raw_payload: {...}
  }

db.machine_fault_events
  {
    _id: ObjectId(),
    machine_id: "M001",
    timestamp: ISODate("2025-12-22T10:30:00Z"),
    fault_code: "BEARING_FAIL",
    severity: "critical|high|medium|low",
    description: "...",
    sensor_readings: [{...}],
    recommended_action: "..."
  }
```

#### 2. **Operational Logs**
```javascript
db.system_logs
  {
    _id: ObjectId(),
    timestamp: ISODate(),
    level: "INFO|WARN|ERROR|DEBUG",
    module: "MES|ERP|WMS|CRM",
    message: "...",
    stack_trace: "...",
    user_id: "U001",
    session_id: "..."
  }

db.daemon_execution_logs
  {
    _id: ObjectId(),
    daemon_name: "financial_sync_daemon",
    execution_timestamp: ISODate(),
    start_time: ISODate(),
    end_time: ISODate(),
    duration_ms: 1234,
    status: "success|failed|partial",
    records_processed: 500,
    errors: [{...}]
  }

db.integration_event_log
  {
    _id: ObjectId(),
    timestamp: ISODate(),
    source_system: "ERP",
    target_system: "WMS",
    event_type: "order_created|order_updated",
    payload: {...},
    status: "success|failed",
    error_message: "..."
  }
```

#### 3. **Unstructured Documents**
```javascript
db.documents
  {
    _id: ObjectId(),
    document_type: "invoice|po|contract|audit_report",
    document_number: "INV-2025-001",
    upload_date: ISODate(),
    file_path: "/documents/2025/12/...",
    file_type: "pdf|xlsx|docx",
    metadata: {
      size_bytes: 1024000,
      pages: 10,
      scan_status: "completed|pending"
    },
    tags: ["supplier", "invoice", "december"],
    content_text: "OCR extracted text..." // For searchability
  }

db.attachments
  {
    _id: ObjectId(),
    entity_type: "ticket|case|lead",
    entity_id: "T001",
    file_name: "screenshot.png",
    file_size: 512000,
    mime_type: "image/png",
    upload_date: ISODate(),
    uploaded_by: "U001"
  }
```

#### 4. **Notifications & Messages**
```javascript
db.notifications
  {
    _id: ObjectId(),
    recipient_id: "U001",
    timestamp: ISODate(),
    type: "order|shipment|alert|reminder",
    title: "...",
    body: "...",
    read: false,
    read_at: ISODate(),
    priority: "high|normal|low"
  }

db.messages
  {
    _id: ObjectId(),
    conversation_id: "C001",
    sender_id: "U001",
    recipient_id: "U002",
    timestamp: ISODate(),
    message_text: "...",
    attachment_ids: ["A001"],
    read: false
  }
```

#### 5. **Performance Metrics & Analytics**
```javascript
db.analytics_events
  {
    _id: ObjectId(),
    timestamp: ISODate(),
    event_type: "page_view|button_click|form_submit",
    user_id: "U001",
    module: "CRM",
    details: {...}
  }

db.performance_metrics
  {
    _id: ObjectId(),
    timestamp: ISODate(),
    component: "api_endpoint|database_query|calculation",
    duration_ms: 150,
    success: true,
    error: null
  }

db.search_index
  {
    _id: ObjectId(),
    entity_type: "supplier|customer|product",
    entity_id: "SUP001",
    entity_name: "Supplier Name",
    searchable_text: "...",
    last_updated: ISODate()
  }
```

#### 6. **Real-Time Updates & Changes**
```javascript
db.entity_change_stream
  {
    _id: ObjectId(),
    entity_type: "sales_order",
    entity_id: "SO001",
    operation: "insert|update|delete",
    timestamp: ISODate(),
    changes: {
      before: {...},
      after: {...}
    },
    changed_by: "U001"
  }

db.real_time_metrics
  {
    _id: ObjectId(),
    metric_type: "active_users|system_health|queue_depth",
    timestamp: ISODate(),
    value: 45,
    timestamp_minute: NumberInt(202512221030)
  }
```

### **Load Strategy for MongoDB**

1. **Create collections**:
```bash
python3 setup_mongodb_collections.py
```

2. **Generate time-series sensor data**:
```bash
python3 generate_mongodb_sensor_data.py --days 30
```

3. **Set up change streams** from PostgreSQL:
```bash
python3 sync_postgres_to_mongodb.py  # Real-time sync
```

4. **Set up indexes for performance**:
```javascript
db.sensor_readings.createIndex({ "timestamp": -1, "machine_id": 1 })
db.system_logs.createIndex({ "timestamp": -1, "level": 1 })
db.notifications.createIndex({ "recipient_id": 1, "read": 1 })
```

### **SUMMARY: MongoDB Collections**
- **Collections**: 20-30 collections
- **Total Documents**: 1M+ time-series data points
- **Purpose**: Logs, metrics, real-time data, flexible schema
- **Update Frequency**: Real-time (change streams)
- **Load Time Estimate**: 15-20 minutes initial + continuous streaming

---

---

## 📋 COMPLETE LOAD CHECKLIST

### Phase 1: Database Preparation (5 minutes)
```bash
[ ] Create PostgreSQL database: GenIMS
[ ] Create MySQL database: GenIMS
[ ] Create MongoDB database: GenIMS
[ ] Verify all 3 connections from .env
```

### Phase 2: Schema & Master Data (20 minutes)
```bash
[ ] Load PostgreSQL Master Data schema (01 - Base Data/)
[ ] Load PostgreSQL Operational schema (02 - Machine data/)
[ ] Load PostgreSQL MES schema (03 - MES Data/)
[ ] Load PostgreSQL ERP schema (04 - ERP & MES Integration/)
[ ] Load PostgreSQL WMS schema (05 - WMS + TMS/)
[ ] Load PostgreSQL TMS schema (05 - WMS + TMS/)
[ ] Load PostgreSQL CMMS schema (06 - CMMS/)
[ ] Load PostgreSQL CRM schema (07 - CRM/)
[ ] Load PostgreSQL Service schema (08 - Support & Service/)
[ ] Load PostgreSQL HCM schema (09 - HR-HCM/)
[ ] Load PostgreSQL Supplier Portal schema (11 - Supplier Portal/)
[ ] Load PostgreSQL QMS schema (12 - QMS/)
```

### Phase 3: Historical Data Generation (30 minutes)
```bash
[ ] Generate & load Master Data (01 - Base Data/)
[ ] Generate & load Operational Data (02 - Machine data/)
[ ] Generate & load MES Data (03 - MES Data/)
[ ] Generate & load ERP Data (04 - ERP & MES Integration/)
[ ] Generate & load WMS/TMS Data (05 - WMS + TMS/)
[ ] Generate & load CMMS Data (06 - CMMS/)
[ ] Generate & load CRM Data (07 - CRM/)
[ ] Generate & load Service Data (08 - Support & Service/)
[ ] Generate & load HCM Data (09 - HR-HCM/)
[ ] Generate & load Supplier Portal Data (11 - Supplier Portal/)
[ ] Generate & load QMS Data (12 - QMS/)
```

### Phase 4: MySQL Reporting (15 minutes)
```bash
[ ] Create MySQL reporting schema
[ ] Generate reporting views
[ ] Set up hourly ETL sync
[ ] Verify reporting tables populated
```

### Phase 5: MongoDB Collections (20 minutes)
```bash
[ ] Create MongoDB collections
[ ] Generate sensor/IoT data (30 days)
[ ] Set up indexes for performance
[ ] Verify change streams active
```

### Phase 6: Daemon Activation (Continuous)
```bash
[ ] Start PostgreSQL daemons:
    [ ] financial_sync_daemon.py (every 5 min)
    [ ] supplier_portal_daemon.py (every 5 min)
    [ ] qms_daemon.py (every 5 min)
    [ ] erp_daily_daemon.py (daily 2 AM)
    [ ] mes_hourly_daemon.py (hourly)
    [ ] iot_daemon.py (continuous)
    [ ] scada_daemon.py (continuous)
[ ] Start MySQL sync processes (hourly)
[ ] Start MongoDB change streams (real-time)
```

---

## 🚀 Quick Start Commands

### PostgreSQL Setup
```bash
# Create database
createdb -h insights-db.postgres.database.azure.com -U turintonadmin GenIMS

# Load all schemas
for file in 0*/*.sql; do
  psql -h insights-db.postgres.database.azure.com -U turintonadmin GenIMS < "$file"
done

# Generate all data
for file in 0*/generate_*.py; do
  python3 "$file"
done

# Load all generated data
for file in 0*/*_inserts.sql; do
  psql -h insights-db.postgres.database.azure.com -U turintonadmin GenIMS < "$file"
done
```

### MySQL Setup
```bash
# Create database
mysql -h insights-db.mysql.database.azure.com -u turintonadmin -p -e "CREATE DATABASE GenIMS;"

# Load reporting schema
mysql -h insights-db.mysql.database.azure.com -u turintonadmin -p GenIMS < mysql_reporting_schema.sql

# Start ETL sync
python3 etl_postgres_to_mysql.py &
```

### MongoDB Setup
```bash
# Create collections
python3 setup_mongodb_collections.py

# Load sensor data
python3 generate_mongodb_sensor_data.py --days 30

# Start change streams
python3 sync_postgres_to_mongodb.py &
```

---

## 📊 Data Volume Summary

| Database | Tables | Records (Est.) | Size (Est.) | Update Frequency |
|----------|--------|----------------|-------------|------------------|
| **PostgreSQL** | 250+ | 100K - 500K | 2-5 GB | Real-time (daemons) |
| **MySQL** | 40 | 50K - 100K | 500MB - 1GB | Hourly (ETL) |
| **MongoDB** | 25 | 1M+ | 5-10 GB | Real-time (streams) |
| **TOTAL** | 315 | 1.2M - 1.6M | 7.5-16 GB | Mixed |

---

## ✅ Validation Checklist After Load

```bash
[ ] PostgreSQL: All 250+ tables created and populated
[ ] PostgreSQL: All 8+ daemons running without errors
[ ] PostgreSQL: Data integrity checks passed
[ ] MySQL: All reporting tables populated
[ ] MySQL: Daily ETL sync working
[ ] MongoDB: All collections created
[ ] MongoDB: Sensor data flowing in real-time
[ ] MongoDB: Indexes optimized
[ ] Cross-database: Sync validation passed
[ ] Backup: All 3 databases backed up
[ ] Documentation: Updated with actual row counts
```

---

## 🔄 Ongoing Maintenance

### Daily Tasks
```bash
- Monitor all daemon processes (logs)
- Verify database backup completion
- Check MySQL ETL sync status
- Monitor MongoDB document growth
```

### Weekly Tasks
```bash
- Database performance analysis
- Index optimization
- Storage capacity review
- Sync lag monitoring
```

### Monthly Tasks
```bash
- Data archival (old logs/sensor data)
- Compliance audit
- Disaster recovery testing
- Capacity planning
```

---

**Document Created**: December 22, 2025  
**Status**: Ready for Implementation  
**Total Estimated Time**: 2-3 hours for complete setup
