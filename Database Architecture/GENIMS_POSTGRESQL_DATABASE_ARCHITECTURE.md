# GenIMS PostgreSQL Database Architecture
## Separate Databases per Functionality Strategy

**Document Version**: 2.0  
**Created**: December 22, 2025  
**Last Updated**: December 22, 2025  
**Status**: Ready for Implementation  
**Focus**: PostgreSQL Only (13 Separate Databases - Maximum Separation)

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Database Separation Strategy](#database-separation-strategy)
3. [Database Options Analysis](#database-options-analysis)
4. [Recommended Architecture (Option 1 - Maximum)](#recommended-architecture-option-1---maximum)
5. [Detailed Database Specifications](#detailed-database-specifications)
6. [Cross-Database Dependencies](#cross-database-dependencies)
7. [Data Flow Architecture](#data-flow-architecture)
8. [Connection Configuration](#connection-configuration)
9. [Load Strategy](#load-strategy)
10. [Maintenance & Operations](#maintenance--operations)

---

## Overview

The GenIMS platform consists of **13 integrated modules** across manufacturing, supply chain, customer management, and operations. This architecture implements **maximum database separation with 13 separate PostgreSQL databases** (one per module), providing maximum isolation, scalability, and independent operations management.

### Key Benefits

✅ **Complete Functional Isolation** - Each database owns its data domain  
✅ **Maximum Scalability** - Scale high-volume databases independently  
✅ **Clear Ownership** - Teams own their functional database  
✅ **Easier Maintenance** - Backup/restore at module level  
✅ **Better Performance** - Optimize indexes per specific workload  
✅ **Flexible Deployment** - Deploy databases on different servers by criticality  

### Key Challenges

⚠️ **No Native Cross-DB Foreign Keys** - PostgreSQL doesn't support cross-DB FKs  
⚠️ **Application-Level Joins** - App must handle cross-DB relationships  
⚠️ **Distributed Transactions** - Complex multi-DB transactions need careful handling  
⚠️ **Data Consistency** - Requires ETL/sync between databases  

---

## Database Separation Strategy

### Principle: Maximum Separation - One Database Per Module

We implement complete functional isolation with a dedicated database for each module:

- **Master Data Database** → Shared reference data (foundation)
- **Operations/IoT Database** → Real-time sensor & SCADA data
- **Manufacturing/MES Database** → Production execution system
- **Maintenance/CMMS Database** → Asset & maintenance management
- **Quality/QMS Database** → Quality management & compliance
- **ERP Core Database** → Enterprise resource planning
- **Financial/GL Database** → General ledger & accounting
- **Warehouse/WMS Database** → Warehouse operations
- **Transport/TMS Database** → Logistics & transportation
- **CRM Database** → Customer relationship management
- **Service/Support Database** → Customer service & support
- **HR/HCM Database** → Human capital management
- **Supplier Portal Database** → Vendor collaboration

Each database is **independently deployable**, **independently scalable**, **independently manageable**, and **owned by dedicated team**.

---

## Database Options Analysis

### OPTION 1: Maximum Separation (13 Databases) ⭐ RECOMMENDED

**Description**: One database per module, maximum isolation, clear ownership

| # | Database Name | Module(s) | Tables | Size |
|---|---|---|---|---|
| 1 | `genims_master_db` | Master Data | 15 | 100 MB |
| 2 | `genims_operations_db` | Operational Data | 6 | 500 MB |
| 3 | `genims_manufacturing_db` | MES | 10 | 800 MB |
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

**Total**: 13 Databases | 343 Tables | ~9.5 GB  
**Pros**: Maximum isolation, complete independence, clear ownership, optimal scalability  
**Cons**: More operational complexity, but manageable with automation

---

### OPTION 2: Recommended Balance (8 Databases) ⭐

**Description**: Balanced separation with related modules grouped

| # | Database Name | Module(s) | Tables | Size | Purpose |
|---|---|---|---|---|---|
| 1 | `genims_master_db` | Master Data | 15 | 100 MB | Shared reference data |
| 2 | `genims_operations_db` | IoT/Operational Data | 6 | 500 MB | Real-time machine data |
| 3 | `genims_manufacturing_db` | MES + CMMS + QMS | 63 | 2.1 GB | Manufacturing hub |
| 4 | `genims_erp_financial_db` | ERP + Financial GL | 64 | 2.1 GB | Business operations |
| 5 | `genims_supply_chain_db` | WMS + TMS | 43 | 1.3 GB | Warehouse & logistics |
| 6 | `genims_crm_db` | CRM + Service | 52 | 1.7 GB | Customer interactions |
| 7 | `genims_hr_db` | HR/HCM | 32 | 1 GB | People management |
| 8 | `genims_supplier_db` | Supplier Portal | 28 | 700 MB | Vendor collaboration |

**Total**: 8 Databases | 303 Tables | ~9.5 GB  
**Pros**: Balanced, manageable, clear functional boundaries  
**Cons**: Requires some ETL between related databases

---

### OPTION 3: Minimal Consolidation (5 Databases)

**Description**: Highly consolidated, maximum throughput

| # | Database Name | Module(s) | Tables | Size |
|---|---|---|---|---|
| 1 | `genims_master_db` | Master Data | 15 | 100 MB |
| 2 | `genims_operations_db` | IoT + MES + CMMS + QMS | 83 | 3.2 GB |
| 3 | `genims_planning_db` | ERP + Financial + WMS + TMS | 136+ | 3.5 GB |
| 4 | `genims_customer_db` | CRM + Service + HR | 84 | 2.7 GB |
| 5 | `genims_ecosystem_db` | Supplier Portal | 28 | 700 MB |

**Total**: 5 Databases | 346 Tables | ~10.2 GB  
**Pros**: Simple, fewer connections to manage  
**Cons**: Monolithic, harder to scale individual functions

---

## Recommended Architecture (Option 1 - Maximum)

### Why Option 1 - Maximum Separation?

✅ **Complete Functional Isolation**
- Each module has its own database with full independence
- No cross-database schema dependencies
- Teams have complete control over their data
- Clear ownership boundaries

✅ **Maximum Scalability**
- Each database scales independently
- High-volume operations DB can be optimized separately
- Manufacturing/CMMS/QMS can scale as needed
- No bottlenecks between modules

✅ **Clear Ownership & Accountability**
- Operations team owns `genims_operations_db`
- Manufacturing team owns `genims_manufacturing_db`, `genims_maintenance_db`, `genims_quality_db`
- Finance team owns `genims_erp_db`, `genims_financial_db`
- Supply chain team owns `genims_wms_db`, `genims_tms_db`
- Customer success owns `genims_crm_db`, `genims_service_db`
- HR team owns `genims_hr_db`
- Supplier management owns `genims_supplier_db`

✅ **Performance Optimization**
- Indexes optimized per module workload
- Query patterns tailored to specific needs
- No contention for database locks
- Parallel processing across databases

✅ **Easier Disaster Recovery**
- Recover single module without affecting others
- Shorter RTO per database
- Independent backup/restore schedules

✅ **Technology Alignment**
- Each database configured for its specific use case
- Operations DB optimized for write-heavy workloads
- CRM/Service optimized for transactional reads
- CMMS optimized for historical data
- QMS optimized for compliance queries

---

## Detailed Database Specifications

### Database 1: `genims_master_db` (CORE)

**Purpose**: Shared reference data for all other databases  
**Table Count**: 15  
**Estimated Size**: 100 MB  
**Update Frequency**: Daily (batch updates)  
**Connection String**: `postgresql://user:pass@host/genims_master_db`

#### Tables

```
companies              - Company registry (1-10 rows)
factories             - Manufacturing facilities (1-50 rows)
warehouses           - Storage facilities (1-20 rows)
warehouse_zones      - Warehouse divisions (10-100 rows)
suppliers            - Vendor master (100-1000 rows)
customers            - Customer master (100-5000 rows)
materials            - Raw materials (500-5000 rows)
products             - Finished goods (100-2000 rows)
bill_of_materials    - Product recipes (100-1000 rows)
bom_components       - BOM line items (1000-10000 rows)
employees            - Employee registry (50-500 rows)
departments          - Organizational units (5-50 rows)
production_lines     - Manufacturing lines (5-50 rows)
machines             - Equipment master (20-200 rows)
material_suppliers   - Material-supplier mapping (100-1000 rows)
```

#### Load Command

```bash
psql -h insights-db.postgres.database.azure.com -U turintonadmin -d genims_master_db < 01\ -\ Base\ Data/genims_schema.sql
psql -h insights-db.postgres.database.azure.com -U turintonadmin -d genims_master_db < 01\ -\ Base\ Data/genims_master_data_inserts.sql
```

#### Dependencies
- **None** - This is the foundation database
- **Used by**: All other databases reference this

---

### Database 2: `genims_operations_db` (REAL-TIME)

**Purpose**: Real-time IoT, SCADA, and machine operational data  
**Table Count**: 6  
**Estimated Size**: 500 MB - 2 GB (grows with sensor data)  
**Update Frequency**: Real-time (continuous writes)  
**Write Intensity**: Very High  
**Connection String**: `postgresql://user:pass@host/genims_operations_db`

#### Tables

```
scada_machine_data         - Machine state (100K+ rows/day)
sensor_data               - High-frequency readings (1M+ rows/day)
machine_faults            - Detected faults (10K+ rows/day)
sensor_health             - Sensor calibration (10K rows)
production_runs           - Batch tracking (10K+ rows/day)
maintenance_events        - Maintenance history (1K rows/day)
```

#### Load Command

```bash
psql -h insights-db.postgres.database.azure.com -U turintonadmin -d genims_operations_db < 02\ -\ Machine\ data/genims_operational_schema.sql
python3 02\ -\ Machine\ data/generate_operational_data.py --db genims_operations_db
```

#### Daemons Running

```bash
python3 02\ -\ Machine\ data/iot_daemon.py &        # Continuous IoT data ingestion
python3 02\ -\ Machine\ data/scada_daemon.py &      # Continuous SCADA monitoring
```

#### Dependencies
- **References**: `genims_master_db` (machines, factories)
- **Used by**: `genims_manufacturing_db` (work order linking)

---

### Database 3: `genims_manufacturing_db` (OPERATIONS HUB)

**Purpose**: Production execution, maintenance, and quality management  
**Table Count**: 63 (MES 10 + CMMS 23 + QMS 30)  
**Estimated Size**: 1.5 - 2.5 GB  
**Update Frequency**: Real-time (high writes)  
**Connection String**: `postgresql://user:pass@host/genims_manufacturing_db`

#### Module Breakdown

**MES (10 tables)**
```
work_orders                   - Production work orders
operations                    - Work order operations
material_transactions         - Material consumption
quality_inspections          - Quality checks
labor_time_entries           - Labor tracking
downtime_events              - Production downtime
production_schedules         - Production planning
electronic_batch_records     - Batch records (eBR)
work_order_status_history    - Status tracking
mes_integration_log          - Integration audit trail
```

**CMMS (23 tables)**
```
maintenance_assets           - Equipment registry
equipment_meter_readings     - Meter tracking
work_orders                  - Maintenance work orders
work_order_tasks             - Work order tasks
labor_time_entries           - Labor tracking
pm_schedules                 - Preventive maintenance
pm_generation_log            - PM generation history
work_procedures              - Standard procedures
mro_parts                    - Spare parts
mro_parts_transactions       - Parts movements
maintenance_technicians      - Technician registry
maintenance_teams            - Team assignments
failure_codes                - Failure classification
maintenance_cost_centers     - Cost tracking
maintenance_costs            - Cost records
service_contracts            - AMC/Warranty contracts
service_call_logs            - External service calls
asset_reliability_metrics    - MTBF/MTTR
maintenance_history          - Audit trail
cmms_integration_log         - Integration log
```

**QMS (30 tables)**
```
ncr_headers                  - Non-conformance reports
ncr_defect_details           - Defect details
capa_headers                 - Corrective actions
capa_actions                 - Action items
quality_audits               - Audit records
audit_findings               - Audit findings
control_plans                - Control plans
control_plan_characteristics - Inspection specs
spc_control_charts           - SPC charts
spc_data_points              - SPC measurements
measuring_equipment          - Equipment registry
calibration_records          - Calibration history
calibration_alerts           - Due date alerts
quality_documents            - Documents
document_revisions           - Revision history
customer_complaints          - Customer complaints
eight_d_reports              - 8D problem solving
ppap_submissions             - PPAP records
supplier_quality_metrics     - Supplier quality
quality_kpis                 - Quality KPIs
qms_integration_log          - Integration log
```

#### Load Commands

```bash
# MES Schema
psql -h insights-db.postgres.database.azure.com -U turintonadmin -d genims_manufacturing_db < 03\ -\ MES\ Data/genims_mes_schema.sql
python3 03\ -\ MES\ Data/generate_mes_historical_data.py --db genims_manufacturing_db

# CMMS Schema
psql -h insights-db.postgres.database.azure.com -U turintonadmin -d genims_manufacturing_db < 06\ -\ CMMS/genims_cmms_schema.sql
python3 06\ -\ CMMS/generate_cmms_historical_data.py --db genims_manufacturing_db

# QMS Schema
psql -h insights-db.postgres.database.azure.com -U turintonadmin -d genims_manufacturing_db < 12\ -\ QMS/genims_qms.sql
python3 12\ -\ QMS/generate_qms_data.py --db genims_manufacturing_db
```

#### Daemons Running

```bash
python3 03\ -\ MES\ Data/mes_hourly_daemon.py --db genims_manufacturing_db &
python3 06\ -\ CMMS/cmms_daemon.py --db genims_manufacturing_db &
python3 12\ -\ QMS/qms_daemon.py --db genims_manufacturing_db &
```

#### Dependencies
- **References**: `genims_master_db` (products, materials, employees)
- **References**: `genims_operations_db` (machine state, sensor data)
- **Used by**: `genims_erp_financial_db` (cost tracking)

---

### Database 4: `genims_erp_financial_db` (BUSINESS HUB)

**Purpose**: Enterprise resource planning and financial operations  
**Table Count**: 64 (ERP 35 + Financial 29)  
**Estimated Size**: 1.5 - 2.5 GB  
**Update Frequency**: Hourly (medium writes)  
**Connection String**: `postgresql://user:pass@host/genims_erp_financial_db`

#### Module Breakdown

**ERP Core (35 tables)**
```
routing                      - Manufacturing routings
purchase_requisitions        - Purchase requests
purchase_requisition_lines   - PR line items
purchase_orders              - Purchase orders
purchase_order_lines         - PO line items
goods_receipts               - Material receipts
goods_receipt_lines          - GR line items
sales_orders                 - Customer orders
sales_order_lines            - SO line items
production_orders            - Production orders (linked to MES)
inventory_balances           - Current stock levels
inventory_transactions       - Stock movements
inventory_variance           - Variances
mrp_runs                     - MRP planning runs
mrp_elements                 - MRP requirements
cost_centers                 - Accounting cost centers
general_ledger               - GL chart of accounts
journal_entries              - Accounting entries
journal_entry_lines          - Entry line items
inspection_plans             - Quality inspection plans
inspection_plan_characteristics - Inspection specs
erp_mes_sync_log             - ERP-MES integration log
```

**Financial GL + Sync (29 tables)**
```
chart_of_accounts            - Account structure
account_balances             - Account balances by period
cost_center_balances         - Cost center balances
fiscal_periods               - Accounting periods
budget_templates             - Budget setup
exchange_rates               - Currency rates
gl_posting_rules             - Posting rules
erp_wms_location_mappings    - Location mapping
erp_wms_sync_queue           - Sync requests
erp_wms_sync_log             - Sync audit trail
inventory_allocations        - Allocation tracking
reconciliation_templates     - Recon templates
snapshot_data                - Inventory snapshots
(Plus 15+ GL and sync tables)
```

#### Load Commands

```bash
# ERP Schema
psql -h insights-db.postgres.database.azure.com -U turintonadmin -d genims_erp_financial_db < 04\ -\ ERP\ \&\ MES\ Integration/genims_erp_schema.sql
python3 04\ -\ ERP\ \&\ MES\ Integration/generate_erp_historical_data.py --db genims_erp_financial_db
```

#### Daemons Running

```bash
python3 04\ -\ ERP\ \&\ MES\ Integration/erp_daily_daemon.py --db genims_erp_financial_db &
python3 04\ -\ ERP\ \&\ MES\ Integration/financial_sync_daemon.py --db genims_erp_financial_db &
```

#### Dependencies
- **References**: `genims_master_db` (suppliers, customers, materials)
- **References**: `genims_manufacturing_db` (production orders)
- **References**: `genims_operations_db` (cost data)
- **Used by**: `genims_supply_chain_db` (WMS sync)
- **Used by**: `genims_crm_db` (sales orders)

---

### Database 5: `genims_supply_chain_db` (SUPPLY CHAIN HUB)

**Purpose**: Warehouse and transportation management  
**Table Count**: 43 (WMS 19 + TMS 24)  
**Estimated Size**: 1 - 1.5 GB  
**Update Frequency**: Real-time (high writes)  
**Connection String**: `postgresql://user:pass@host/genims_supply_chain_db`

#### Module Breakdown

**WMS (19 tables)**
```
warehouse_aisles             - Aisle layout
storage_bins                 - Bin locations
warehouse_inventory          - Bin-level inventory
receiving_tasks              - Inbound tasks
putaway_tasks                - Putaway operations
pick_waves                   - Wave picking
wave_lines                   - Wave line items
picking_tasks                - Pick operations
packing_tasks                - Packing operations
shipping_tasks               - Shipping operations
cycle_count_tasks            - Cycle counting
warehouse_equipment          - Equipment registry
warehouse_workers            - Labor assignments
warehouse_movements          - Movement audit trail
slotting_rules               - Bin assignment rules
wms_tms_sync_log             - WMS-TMS integration
```

**TMS (24 tables)**
```
carriers                     - Shipping carriers
carrier_services             - Service levels
carrier_rates                - Rate cards
shipments                    - Shipment headers
shipment_lines               - Shipment line items
shipment_packages            - Package details
tracking_events              - Tracking updates
routes                       - Delivery routes
route_stops                  - Route stops
deliveries                   - Final delivery
proof_of_delivery            - POD records
return_orders                - Return authorizations
return_order_lines           - Return line items
return_shipments             - Return shipments
freight_invoices             - Carrier invoices
freight_invoice_lines        - Invoice lines
wms_tms_sync_log             - Integration log
```

#### Load Commands

```bash
# WMS Schema
psql -h insights-db.postgres.database.azure.com -U turintonadmin -d genims_supply_chain_db < 05\ -\ WMS\ \+\ TMS/genims_wms_schema.sql

# TMS Schema
psql -h insights-db.postgres.database.azure.com -U turintonadmin -d genims_supply_chain_db < 05\ -\ WMS\ \+\ TMS/genims_tms_schema.sql

# Data Generation
python3 05\ -\ WMS\ \+\ TMS/generate_wms_tms_historical_data.py --db genims_supply_chain_db
```

#### Daemons Running

```bash
python3 05\ -\ WMS\ \+\ TMS/wms_tms_daemon.py --db genims_supply_chain_db &
```

#### Dependencies
- **References**: `genims_master_db` (warehouses, materials)
- **References**: `genims_erp_financial_db` (purchase orders, sales orders)
- **Used by**: `genims_crm_db` (shipment tracking)

---

### Database 6: `genims_crm_db` (CUSTOMER HUB)

**Purpose**: Customer relationship management and support  
**Table Count**: 52 (CRM 25 + Service 27)  
**Estimated Size**: 1 - 1.5 GB  
**Update Frequency**: Hourly (medium writes)  
**Connection String**: `postgresql://user:pass@host/genims_crm_db`

#### Module Breakdown

**CRM (25 tables)**
```
leads                        - Lead registry
lead_activities              - Lead interactions
accounts                     - Customer accounts
contacts                     - Contact persons
customer_interactions        - Interaction history
opportunities                - Sales opportunities
opportunity_stage_history    - Stage tracking
opportunity_products         - Opportunity products
sales_forecasts              - Pipeline forecasts
activities                   - Call/meeting logs
tasks                        - Follow-up tasks
notes                        - Internal notes
quotations                   - Price quotes
quotation_lines              - Quote line items
campaigns                    - Marketing campaigns
campaign_members             - Campaign recipients
cases                        - Support cases
case_comments                - Case discussions
contracts                    - Customer contracts
sales_reps                   - Sales team
sales_territories            - Territory definitions
crm_integration_log          - Integration log
```

**Service (27 tables)**
```
service_tickets              - Support tickets
ticket_comments              - Ticket discussions
ticket_attachments           - Attachments
kb_categories                - Knowledge base categories
kb_articles                  - Help articles
kb_article_ratings           - Article feedback
sla_definitions              - SLA agreements
warranty_registrations       - Warranty records
warranty_claims              - Warranty claims
rma_requests                 - Return authorizations
rma_line_items               - RMA line items
field_service_appointments   - Service appointments
field_technicians            - Field technician registry
service_parts                - Service parts inventory
service_parts_usage          - Parts usage tracking
customer_surveys             - Survey templates
survey_responses             - Survey responses
customer_feedback            - Feedback records
escalation_rules             - Escalation config
ticket_escalations           - Escalation tracking
service_teams                - Support teams
service_queues               - Ticket queues
service_agents               - Agent registry
resolution_codes             - Resolution taxonomy
service_metrics_daily        - Daily KPIs
portal_users                 - Portal access
service_integration_log      - Integration log
```

#### Load Commands

```bash
# CRM Schema
psql -h insights-db.postgres.database.azure.com -U turintonadmin -d genims_crm_db < 07\ -\ CRM/genims_crm_schema.sql
python3 07\ -\ CRM/generate_crm_historical_data.py --db genims_crm_db

# Service Schema
psql -h insights-db.postgres.database.azure.com -U turintonadmin -d genims_crm_db < 08\ -\ Support\ \&\ Service/genims_service_schema.sql
python3 08\ -\ Support\ \&\ Service/generate_service_historical_data.py --db genims_crm_db
```

#### Daemons Running

```bash
python3 07\ -\ CRM/crm_daemon.py --db genims_crm_db &
python3 08\ -\ Support\ \&\ Service/service_daemon.py --db genims_crm_db &
```

#### Dependencies
- **References**: `genims_master_db` (customers, employees)
- **References**: `genims_erp_financial_db` (sales orders)
- **References**: `genims_supply_chain_db` (shipments)

---

### Database 7: `genims_hr_db` (HR HUB)

**Purpose**: Human capital management  
**Table Count**: 32  
**Estimated Size**: 500 MB - 1 GB  
**Update Frequency**: Daily (low-medium writes)  
**Connection String**: `postgresql://user:pass@host/genims_hr_db`

#### Tables

```
employee_employment_history  - Career history
job_roles                    - Job definitions
positions                    - Budgeted positions
skills_catalog               - Skills master
employee_skills              - Employee skills
role_skill_requirements      - Role requirements
training_courses             - Course catalog
training_requirements        - Mandatory training
training_schedules           - Training sessions
training_enrollments         - Attendance records
employee_certifications      - Certifications
performance_kpis             - Performance metrics
performance_reviews          - Review records
employee_goals               - Goal tracking
shift_schedules              - Shift definitions
employee_shifts              - Shift assignments
attendance_records           - Daily attendance
leave_types                  - Leave classifications
employee_leave_balances      - Leave accruals
leave_requests               - Leave applications
onboarding_checklists        - Onboarding templates
onboarding_checklist_items   - Checklist items
employee_onboarding          - Employee onboarding
employee_onboarding_items    - Progress tracking
offboarding_records          - Exit procedures
career_paths                 - Career progression
succession_planning          - Succession plans
succession_candidates        - Backup candidates
safety_incidents             - OSHA incidents
ppe_requirements             - PPE requirements
hcm_integration_log          - Integration log
```

#### Load Commands

```bash
psql -h insights-db.postgres.database.azure.com -U turintonadmin -d genims_hr_db < 09\ -\ HR-HCM/genims_hcm_schema.sql
python3 09\ -\ HR-HCM/generate_hcm_historical_data.py --db genims_hr_db
```

#### Daemons Running

```bash
python3 09\ -\ HR-HCM/hcm_daemon.py --db genims_hr_db &
```

#### Dependencies
- **References**: `genims_master_db` (employees, departments)
- **Used by**: `genims_crm_db` (service agents)

---

### Database 8: `genims_supplier_db` (SUPPLIER HUB)

**Purpose**: Supplier portal and vendor management  
**Table Count**: 28  
**Estimated Size**: 500 MB - 1 GB  
**Update Frequency**: Daily (low-medium writes)  
**Connection String**: `postgresql://user:pass@host/genims_supplier_db`

#### Tables

```
rfq_headers                  - Request for Quote
rfq_lines                    - RFQ line items
rfq_suppliers                - Supplier invitations
rfq_responses                - Supplier responses
rfq_response_lines           - Response line items
quote_comparison             - Multi-supplier comparison
supplier_contracts           - Supplier agreements
contract_pricing             - Pricing data
supplier_performance_metrics - Performance tracking
supplier_scorecards          - Monthly scorecards
supplier_rating_history      - Rating history
supplier_invoices            - Invoice headers
supplier_invoice_lines       - Invoice line items
three_way_match_log          - Matching audit trail
supplier_qualification       - Qualification status
supplier_documents           - Document management
supplier_audits              - Audit records
audit_findings               - Audit findings
supplier_portal_users        - User accounts
supplier_communications      - Messaging
supplier_notifications       - Alerts
purchase_requisitions        - Internal requests
purchase_requisition_lines   - PR line items
supplier_portal_integration_log - Integration log
```

#### Load Commands

```bash
psql -h insights-db.postgres.database.azure.com -U turintonadmin -d genims_supplier_db < 11\ -\ Supplier\ Portal/genims_supplier_portal.sql
python3 11\ -\ Supplier\ Portal/generate_supplier_portal_data.py --db genims_supplier_db
```

#### Daemons Running

```bash
python3 11\ -\ Supplier\ Portal/supplier_portal_daemon.py --db genims_supplier_db &
```

#### Dependencies
- **References**: `genims_master_db` (suppliers)
- **References**: `genims_erp_financial_db` (purchase requisitions)

---

## Cross-Database Dependencies

### Dependency Matrix

```
                    ↓ References
                    
genims_master_db               (Foundation)
    ↑
    └─← All 7 other databases reference master data
    
genims_operations_db           (Real-time)
    ↓
    └─→ genims_manufacturing_db
    
genims_manufacturing_db        (Production)
    ↓
    └─→ genims_erp_financial_db (cost tracking)
    
genims_erp_financial_db        (ERP)
    ├─→ genims_supply_chain_db (WMS sync)
    ├─→ genims_crm_db (sales orders)
    └─→ genims_supplier_db (purchase orders)
    
genims_supply_chain_db         (Supply Chain)
    ├─→ genims_crm_db (shipments)
    └─→ genims_erp_financial_db (inventory)
    
genims_crm_db                  (Customers)
    ├─→ genims_hr_db (service agents)
    └─→ genims_supply_chain_db (shipments)
    
genims_hr_db                   (HR)
    └─← referenced by CRM
    
genims_supplier_db             (Suppliers)
    └─→ genims_erp_financial_db (purchase orders)
```

### Master Data References

All databases reference these tables in `genims_master_db`:

| Table | Used By | Purpose |
|-------|---------|---------|
| `companies` | All databases | Company context |
| `factories` | Operations, Manufacturing, ERP | Factory context |
| `warehouses` | Supply Chain, ERP | Warehouse context |
| `warehouse_zones` | Supply Chain | Warehouse divisions |
| `suppliers` | ERP, Supplier | Vendor master |
| `customers` | CRM, ERP | Customer master |
| `materials` | ERP, Supply Chain | Material master |
| `products` | ERP, CRM | Product master |
| `employees` | HR, CRM, Manufacturing | Employee master |
| `departments` | HR, Manufacturing | Department master |
| `production_lines` | Manufacturing, Operations | Line master |
| `machines` | Operations, Manufacturing | Machine master |

---

## Data Flow Architecture

### High-Level Data Flow Diagram

```
IoT/SCADA Devices
    ↓
genims_operations_db (Real-time sensor data)
    ↓
genims_manufacturing_db (Process machine data)
    ↓
genims_erp_financial_db (Record costs, allocate resources)
    ↓
genims_supply_chain_db (Material allocation, warehouse)
    ↓
genims_crm_db (Customer shipment tracking)
    ↓
End Customer

Suppliers
    ↓
genims_supplier_db (Portal activity)
    ↓
genims_erp_financial_db (Purchase orders)
    ↓
genims_supply_chain_db (Receiving, putaway)
    ↓
genims_manufacturing_db (Material consumption)

HR System
    ↓
genims_hr_db (Employee data)
    ↓
genims_manufacturing_db (Labor allocation)
    ↓
genims_crm_db (Service agent assignment)
```

### ETL/Sync Requirements

| From DB | To DB | Data | Frequency | Volume |
|---------|-------|------|-----------|--------|
| operations | manufacturing | machine state | Real-time | 100K+ rows/day |
| manufacturing | erp_financial | cost data | Hourly | 1K+ rows/day |
| erp_financial | supply_chain | inventory allocations | Real-time | 10K+ rows/day |
| erp_financial | crm | sales orders | Real-time | 100+ rows/day |
| erp_financial | supplier | POs | Real-time | 50+ rows/day |
| supply_chain | crm | shipments | Real-time | 100+ rows/day |
| hr | crm | agent data | Daily | 10+ rows/day |
| supplier | erp_financial | RFQ responses | Daily | 50+ rows/day |

---

## Connection Configuration

### Environment Variables (.env)

```bash
# Master Database (Reference Data)
POSTGRES_MASTER_HOST=insights-db.postgres.database.azure.com
POSTGRES_MASTER_PORT=5432
POSTGRES_MASTER_DB=genims_master_db
POSTGRES_MASTER_USER=turintonadmin
POSTGRES_MASTER_PASSWORD=Passw0rd123

# Operations Database (Real-time)
POSTGRES_OPS_HOST=insights-db.postgres.database.azure.com
POSTGRES_OPS_PORT=5432
POSTGRES_OPS_DB=genims_operations_db
POSTGRES_OPS_USER=turintonadmin
POSTGRES_OPS_PASSWORD=Passw0rd123

# Manufacturing Database (Production)
POSTGRES_MFG_HOST=insights-db.postgres.database.azure.com
POSTGRES_MFG_PORT=5432
POSTGRES_MFG_DB=genims_manufacturing_db
POSTGRES_MFG_USER=turintonadmin
POSTGRES_MFG_PASSWORD=Passw0rd123

# ERP/Financial Database (Business)
POSTGRES_ERP_HOST=insights-db.postgres.database.azure.com
POSTGRES_ERP_PORT=5432
POSTGRES_ERP_DB=genims_erp_financial_db
POSTGRES_ERP_USER=turintonadmin
POSTGRES_ERP_PASSWORD=Passw0rd123

# Supply Chain Database (Logistics)
POSTGRES_SC_HOST=insights-db.postgres.database.azure.com
POSTGRES_SC_PORT=5432
POSTGRES_SC_DB=genims_supply_chain_db
POSTGRES_SC_USER=turintonadmin
POSTGRES_SC_PASSWORD=Passw0rd123

# CRM Database (Customers)
POSTGRES_CRM_HOST=insights-db.postgres.database.azure.com
POSTGRES_CRM_PORT=5432
POSTGRES_CRM_DB=genims_crm_db
POSTGRES_CRM_USER=turintonadmin
POSTGRES_CRM_PASSWORD=Passw0rd123

# HR Database (People)
POSTGRES_HR_HOST=insights-db.postgres.database.azure.com
POSTGRES_HR_PORT=5432
POSTGRES_HR_DB=genims_hr_db
POSTGRES_HR_USER=turintonadmin
POSTGRES_HR_PASSWORD=Passw0rd123

# Supplier Database (Vendors)
POSTGRES_SUPPLIER_HOST=insights-db.postgres.database.azure.com
POSTGRES_SUPPLIER_PORT=5432
POSTGRES_SUPPLIER_DB=genims_supplier_db
POSTGRES_SUPPLIER_USER=turintonadmin
POSTGRES_SUPPLIER_PASSWORD=Passw0rd123
```

### Connection Strings (Format)

```
PostgreSQL Standard: postgresql://user:password@host:port/database
Example: postgresql://turintonadmin:Passw0rd123@insights-db.postgres.database.azure.com:5432/genims_master_db
```

---

## Load Strategy

### Phase 1: Database Creation (5 minutes)

```bash
# For each database, create it:
createdb -h insights-db.postgres.database.azure.com -U turintonadmin genims_master_db
createdb -h insights-db.postgres.database.azure.com -U turintonadmin genims_operations_db
createdb -h insights-db.postgres.database.azure.com -U turintonadmin genims_manufacturing_db
createdb -h insights-db.postgres.database.azure.com -U turintonadmin genims_erp_financial_db
createdb -h insights-db.postgres.database.azure.com -U turintonadmin genims_supply_chain_db
createdb -h insights-db.postgres.database.azure.com -U turintonadmin genims_crm_db
createdb -h insights-db.postgres.database.azure.com -U turintonadmin genims_hr_db
createdb -h insights-db.postgres.database.azure.com -U turintonadmin genims_supplier_db
```

### Phase 2: Schema Loading (15 minutes)

**Load Master Data First** (dependency foundation)
```bash
psql -h insights-db.postgres.database.azure.com -U turintonadmin -d genims_master_db < "01 - Base Data/genims_schema.sql"
```

**Load Other Schemas in Parallel**
```bash
# Operations
psql -h insights-db.postgres.database.azure.com -U turintonadmin -d genims_operations_db < "02 - Machine data/genims_operational_schema.sql" &

# Manufacturing (MES+CMMS+QMS)
psql -h insights-db.postgres.database.azure.com -U turintonadmin -d genims_manufacturing_db < "03 - MES Data/genims_mes_schema.sql" &
psql -h insights-db.postgres.database.azure.com -U turintonadmin -d genims_manufacturing_db < "06 - CMMS/genims_cmms_schema.sql" &
psql -h insights-db.postgres.database.azure.com -U turintonadmin -d genims_manufacturing_db < "12 - QMS/genims_qms.sql" &

# ERP/Financial
psql -h insights-db.postgres.database.azure.com -U turintonadmin -d genims_erp_financial_db < "04 - ERP & MES Integration/genims_erp_schema.sql" &

# Supply Chain (WMS+TMS)
psql -h insights-db.postgres.database.azure.com -U turintonadmin -d genims_supply_chain_db < "05 - WMS + TMS/genims_wms_schema.sql" &
psql -h insights-db.postgres.database.azure.com -U turintonadmin -d genims_supply_chain_db < "05 - WMS + TMS/genims_tms_schema.sql" &

# CRM + Service
psql -h insights-db.postgres.database.azure.com -U turintonadmin -d genims_crm_db < "07 - CRM/genims_crm_schema.sql" &
psql -h insights-db.postgres.database.azure.com -U turintonadmin -d genims_crm_db < "08 - Support & Service/genims_service_schema.sql" &

# HR
psql -h insights-db.postgres.database.azure.com -U turintonadmin -d genims_hr_db < "09 - HR-HCM/genims_hcm_schema.sql" &

# Supplier
psql -h insights-db.postgres.database.azure.com -U turintonadmin -d genims_supplier_db < "11 - Supplier Portal/genims_supplier_portal.sql" &

# Wait for all to complete
wait
```

### Phase 3: Historical Data Generation (30 minutes)

**Load Master Data** (required first)
```bash
psql -h insights-db.postgres.database.azure.com -U turintonadmin -d genims_master_db < "01 - Base Data/genims_master_data_inserts.sql"
```

**Generate and Load Data in Parallel**
```bash
# Operations
python3 "02 - Machine data/generate_operational_data.py" --db genims_operations_db &

# Manufacturing
python3 "03 - MES Data/generate_mes_historical_data.py" --db genims_manufacturing_db &
python3 "06 - CMMS/generate_cmms_historical_data.py" --db genims_manufacturing_db &
python3 "12 - QMS/generate_qms_data.py" --db genims_manufacturing_db &

# ERP
python3 "04 - ERP & MES Integration/generate_erp_historical_data.py" --db genims_erp_financial_db &

# Supply Chain
python3 "05 - WMS + TMS/generate_wms_tms_historical_data.py" --db genims_supply_chain_db &

# CRM
python3 "07 - CRM/generate_crm_historical_data.py" --db genims_crm_db &
python3 "08 - Support & Service/generate_service_historical_data.py" --db genims_crm_db &

# HR
python3 "09 - HR-HCM/generate_hcm_historical_data.py" --db genims_hr_db &

# Supplier
python3 "11 - Supplier Portal/generate_supplier_portal_data.py" --db genims_supplier_db &

# Wait for all to complete
wait
```

### Phase 4: Daemon Activation (Continuous)

```bash
# Operations (Real-time IoT)
python3 "02 - Machine data/iot_daemon.py" --db genims_operations_db > logs/iot_daemon.log 2>&1 &
python3 "02 - Machine data/scada_daemon.py" --db genims_operations_db > logs/scada_daemon.log 2>&1 &

# Manufacturing
python3 "03 - MES Data/mes_hourly_daemon.py" --db genims_manufacturing_db > logs/mes_daemon.log 2>&1 &
python3 "06 - CMMS/cmms_daemon.py" --db genims_manufacturing_db > logs/cmms_daemon.log 2>&1 &
python3 "12 - QMS/qms_daemon.py" --db genims_manufacturing_db > logs/qms_daemon.log 2>&1 &

# ERP
python3 "04 - ERP & MES Integration/erp_daily_daemon.py" --db genims_erp_financial_db > logs/erp_daemon.log 2>&1 &
python3 "04 - ERP & MES Integration/financial_sync_daemon.py" --db genims_erp_financial_db > logs/financial_sync_daemon.log 2>&1 &

# Supply Chain
python3 "05 - WMS + TMS/wms_tms_daemon.py" --db genims_supply_chain_db > logs/wms_tms_daemon.log 2>&1 &

# CRM
python3 "07 - CRM/crm_daemon.py" --db genims_crm_db > logs/crm_daemon.log 2>&1 &
python3 "08 - Support & Service/service_daemon.py" --db genims_crm_db > logs/service_daemon.log 2>&1 &

# HR
python3 "09 - HR-HCM/hcm_daemon.py" --db genims_hr_db > logs/hcm_daemon.log 2>&1 &

# Supplier
python3 "11 - Supplier Portal/supplier_portal_daemon.py" --db genims_supplier_db > logs/supplier_daemon.log 2>&1 &

# Start sync daemons
python3 scripts/sync_operations_to_manufacturing.py > logs/sync_ops_mfg.log 2>&1 &
python3 scripts/sync_manufacturing_to_erp.py > logs/sync_mfg_erp.log 2>&1 &
python3 scripts/sync_erp_to_supply_chain.py > logs/sync_erp_sc.log 2>&1 &
python3 scripts/sync_erp_to_crm.py > logs/sync_erp_crm.log 2>&1 &
```

### Phase 5: Verification (10 minutes)

```bash
# Verify all databases created
psql -h insights-db.postgres.database.azure.com -U turintonadmin -l | grep genims

# Verify schemas loaded
psql -h insights-db.postgres.database.azure.com -U turintonadmin -d genims_master_db -c "\dt"
psql -h insights-db.postgres.database.azure.com -U turintonadmin -d genims_operations_db -c "\dt"
psql -h insights-db.postgres.database.azure.com -U turintonadmin -d genims_manufacturing_db -c "\dt"
psql -h insights-db.postgres.database.azure.com -U turintonadmin -d genims_erp_financial_db -c "\dt"
psql -h insights-db.postgres.database.azure.com -U turintonadmin -d genims_supply_chain_db -c "\dt"
psql -h insights-db.postgres.database.azure.com -U turintonadmin -d genims_crm_db -c "\dt"
psql -h insights-db.postgres.database.azure.com -U turintonadmin -d genims_hr_db -c "\dt"
psql -h insights-db.postgres.database.azure.com -U turintonadmin -d genims_supplier_db -c "\dt"

# Verify data loaded
psql -h insights-db.postgres.database.azure.com -U turintonadmin -d genims_master_db -c "SELECT COUNT(*) FROM companies;"
psql -h insights-db.postgres.database.azure.com -U turintonadmin -d genims_operations_db -c "SELECT COUNT(*) FROM sensor_data;"

# Verify daemons running
ps aux | grep daemon
```

---

## Maintenance & Operations

### Daily Tasks

```bash
# Monitor daemon health
tail -f logs/*.log

# Check database sizes
psql -h insights-db.postgres.database.azure.com -U turintonadmin -c "SELECT datname, pg_size_pretty(pg_database_size(datname)) FROM pg_database WHERE datname LIKE 'genims%' ORDER BY pg_database_size(datname) DESC;"

# Monitor active connections
psql -h insights-db.postgres.database.azure.com -U turintonadmin -c "SELECT datname, COUNT(*) FROM pg_stat_activity GROUP BY datname;"
```

### Weekly Tasks

```bash
# Analyze query performance
psql -h insights-db.postgres.database.azure.com -U turintonadmin -d genims_manufacturing_db -c "ANALYZE;"

# Check index usage
psql -h insights-db.postgres.database.azure.com -U turintonadmin -d genims_operations_db -c "SELECT schemaname, tablename, indexname, idx_scan FROM pg_stat_user_indexes ORDER BY idx_scan;"

# Vacuum (cleanup)
psql -h insights-db.postgres.database.azure.com -U turintonadmin -d genims_operations_db -c "VACUUM ANALYZE;"
```

### Monthly Tasks

```bash
# Full backup all databases
for db in genims_master_db genims_operations_db genims_manufacturing_db genims_erp_financial_db genims_supply_chain_db genims_crm_db genims_hr_db genims_supplier_db; do
  pg_dump -h insights-db.postgres.database.azure.com -U turintonadmin -d $db > backup_$db_$(date +%Y%m%d).sql
done

# Archive old sensor data
psql -h insights-db.postgres.database.azure.com -U turintonadmin -d genims_operations_db -c "DELETE FROM sensor_data WHERE timestamp < NOW() - INTERVAL '90 days';"

# Performance tuning review
psql -h insights-db.postgres.database.azure.com -U turintonadmin -d genims_manufacturing_db -c "SELECT * FROM pg_stat_statements ORDER BY total_time DESC LIMIT 10;"
```

### Backup Strategy

| Database | Frequency | Retention | Location |
|----------|-----------|-----------|----------|
| `genims_master_db` | Daily | 30 days | Azure Blob Storage |
| `genims_operations_db` | Daily | 7 days | Azure Blob Storage |
| `genims_manufacturing_db` | Daily | 30 days | Azure Blob Storage |
| `genims_erp_financial_db` | Daily | 90 days | Azure Blob Storage + Archive |
| `genims_supply_chain_db` | Daily | 30 days | Azure Blob Storage |
| `genims_crm_db` | Daily | 30 days | Azure Blob Storage |
| `genims_hr_db` | Daily | 365 days | Azure Blob Storage + Archive |
| `genims_supplier_db` | Daily | 90 days | Azure Blob Storage + Archive |

---

## Data Volume Estimates

### Initial Load

| Database | Tables | Est. Rows | Est. Size |
|----------|--------|-----------|-----------|
| `genims_master_db` | 15 | 10K | 100 MB |
| `genims_operations_db` | 6 | 100K | 500 MB |
| `genims_manufacturing_db` | 63 | 500K | 2 GB |
| `genims_erp_financial_db` | 64 | 400K | 1.5 GB |
| `genims_supply_chain_db` | 43 | 300K | 1 GB |
| `genims_crm_db` | 52 | 200K | 1 GB |
| `genims_hr_db` | 32 | 50K | 500 MB |
| `genims_supplier_db` | 28 | 50K | 500 MB |
| **TOTAL** | **303** | **1.6M** | **~7.6 GB** |

### Growth Projections (12 months)

| Database | Daily Growth | Annual Growth | Total (12m) |
|----------|--------------|---------------|------------|
| `genims_operations_db` | 100K rows | 36.5M rows | 37 GB |
| `genims_manufacturing_db` | 10K rows | 3.65M rows | 5.5 GB |
| `genims_erp_financial_db` | 5K rows | 1.83M rows | 3 GB |
| `genims_supply_chain_db` | 5K rows | 1.83M rows | 2.5 GB |
| Others | 1K rows | 365K rows | 2 GB |
| **TOTAL** | **121K rows** | **44M rows** | **~50 GB** |

---

## Summary

### Key Metrics

| Metric | Value |
|--------|-------|
| **Total PostgreSQL Databases** | 8 |
| **Total Tables** | 303 |
| **Total Initial Size** | 7.6 GB |
| **Running Daemons** | 15+ |
| **Cross-DB Sync Points** | 8 |
| **Master Data References** | 12 core tables |

### Implementation Checklist

- [ ] Create 8 PostgreSQL databases
- [ ] Update .env with 8 connection strings
- [ ] Load `genims_master_db` schema and data
- [ ] Load all other database schemas
- [ ] Generate historical data for all databases
- [ ] Verify all schemas and row counts
- [ ] Start all 15+ daemons
- [ ] Verify cross-database ETL working
- [ ] Test backup procedures
- [ ] Document backup/recovery procedures
- [ ] Set up monitoring alerts
- [ ] Set up capacity planning alerts

### Estimated Timeline

- **Phase 1**: Database Creation → 5 min
- **Phase 2**: Schema Loading → 15 min
- **Phase 3**: Data Generation → 30 min
- **Phase 4**: Daemon Activation → 5 min
- **Phase 5**: Verification → 10 min
- **TOTAL** → **65 minutes** (~1 hour)

---

## Next Steps

1. **Update Azure PostgreSQL Firewall** - Add your local IP (14.96.208.122)
2. **Create .env file** - Add all 8 database connection strings
3. **Create databases** - Run creation script
4. **Load schemas** - Execute in order: Master → Others
5. **Generate data** - Run all data generators
6. **Start daemons** - Activate all sync processes
7. **Monitor** - Watch logs and verify data flow

---

**Document Status**: Ready for Implementation  
**Last Updated**: December 22, 2025  
**Total Estimated Setup Time**: 1-2 hours (including Azure firewall update)
