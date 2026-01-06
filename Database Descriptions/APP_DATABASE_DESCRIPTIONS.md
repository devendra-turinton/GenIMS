# GenIMS Database Descriptions
## Comprehensive Overview of All 14 Databases (v2.0)

**Document Version:** 2.0  
**Last Updated:** December 27, 2025  
**Total Databases:** 14 (13 PostgreSQL active, 1 MySQL deferred)  
**Total Tables:** 237 loaded (258 schema defined)  
**Total Records:** 412,960  

---

## 1. GENIMS_MASTER_DB

The foundational database serving as the single source of truth for all enterprise master data across the GenIMS (Generative Industrial Managed Services) ecosystem. Contains multi-factory operations data, including factory locations with certifications and capacity, production infrastructure hierarchy (production lines, machines with criticality levels, sensors collecting 10+ measurement types), human resources (employees with roles and certifications), product portfolios (bill of materials, cycle times, quality targets), and customer information (types, volumes, SLA requirements). The data model uses a hierarchical star schema centered on factories: Factories → Production Lines → Machines → Sensors creates a parent-child hierarchy, while line_product_mapping and customer_product_mapping establish many-to-many relationships with line-specific metrics (cycle times, yields) and customer parameters (pricing, volumes, quality requirements). The database maintains referential integrity through foreign key constraints and optimizes query performance with cascading indices on common joins. Serves as the bootstrap data source, ensuring data consistency and enabling seamless enterprise-wide integration across all 13 operational systems.

**Tables:** 10 | **Records:** 13,335 | **Key Relationships:** Hierarchical (Factories → Lines → Machines → Sensors), One-to-Many (Factories → Employees/Shifts), Many-to-Many (Lines ↔ Products, Customers ↔ Products)

| **Data Group** | **Data Access Roles** |
|---|---|
| Master Data | Data Manager, Viewer, Analyst, Supervisor, Planner |

---

## 2. GENIMS_OPERATIONS_DB

Real-time operational intelligence system capturing machine and sensor telemetry from the factory floor at sub-second to minute-level granularity. Ingests high-frequency data streams from 1,781 IoT sensors (temperature, vibration, pressure, current, voltage, speed, torque) deployed across 236 machines on 21 production lines, collecting 90+ daily measurements per sensor type. The SCADA (Supervisory Control and Data Acquisition) layer captures machine state transitions, fault codes, cycle times, power consumption, and OEE (Overall Equipment Effectiveness) components, while sensor_data tables record raw measurements with anomaly detection scores and health status. Integration with machine_faults enables automatic root cause detection through sensor anomaly correlation, identifying bearing failures, overheating, tool wear, and electrical faults hours before breakdown. Provides the data foundation for predictive maintenance models, OEE dashboards, and real-time production control. Time-series data structure (partitioned by date) supports 90-day rolling retention of raw data with automatic aggregation to 1-hour, 1-day, and monthly summaries for long-term trend analysis. Critical dependency: Master_DB for asset hierarchies, Operations for production context.

**Tables:** 6 | **Records:** 372,179 | **Key Relationships:** Star Schema (Factory/Line/Machine → SCADA), Bridge (Sensor → Machine), Temporal (timestamp-partitioned)

| **Data Group** | **Data Access Roles** |
|---|---|
| Manufacturing and Operations | Equipment Technician, Supervisor, Production Manager, Analyst, Planner |

---

## 3. GENIMS_MANUFACTURING_DB

Manufacturing Execution System (MES) providing real-time production floor control, work order lifecycle management, and regulatory compliance documentation. Orchestrates production by translating ERP production orders into MES work orders with detailed operation sequences, routing specifications, and inspection requirements. Tracks material consumption at fine granularity (by lot, batch, serial number) for traceability and genealogy, capturing consumption patterns and scrap statistics. Quality management module integrates incoming, in-process, and final inspections with automated non-conformance (NCR) generation, root cause analysis workflows, and corrective/preventive action (CAPA) tracking. Electronic Batch Records (eBR) tables maintain FDA 21 CFR Part 11 compliant documentation with complete audit trails, electronic signatures, and deviation tracking for regulated manufacturing. Labor transaction module tracks operator time allocation across work orders, operations, and activity types with efficiency metrics and cost allocation. Changeover event tracking implements SMED (Single Minute Exchange of Dies) principles with detailed teardown, setup, adjustment, and trial run timing. Critical for compliance with automotive (IATF 16949), pharmaceutical (FDA), and quality (ISO 9001) standards. Retention: 7+ years per regulatory requirement.

**Tables:** 10 | **Records:** 10,053 | **Key Relationships:** Hierarchical (Work_Orders → Operations → Tasks), Transactional (Material/Labor/Quality), Compliance (eBR with audit trail)

| **Data Group** | **Data Access Roles** |
|---|---|
| Manufacturing and Operations | Production Manager, Shift Supervisor, Shop Floor Operator, Analyst, Planner |

---

## 4. GENIMS_MAINTENANCE_DB

Computerized Maintenance Management System (CMMS) managing complete equipment asset lifecycle across 50+ critical production assets. Maintains asset registry with detailed specifications (manufacturer, model, serial number, installation date, warranty), hierarchical structure (parent-child asset relationships), and lifecycle classification (critical, essential, important, support). Implements multi-strategy preventive maintenance: calendar-based (daily/weekly/monthly/quarterly/yearly), meter-based (operating hours, kilometers, cycles), and condition-based (vibration, temperature, oil quality thresholds). Preventive maintenance scheduling automatically generates work orders at configurable lead times, triggers spare parts procurement, and schedules maintenance windows. Corrective maintenance captures machine faults, breakdown causes, and emergency response times. Integrates with Operations_DB to link maintenance work orders to machine faults and downtime events, enabling impact quantification (production loss in units, estimated cost). Work order task management enforces safety protocols (LOTO, hot work permits, confined space) and verification workflows. Labor tracking captures technician time allocation by skill level and maintenance type. Service contract management tracks warranty coverage, third-party service agreements, and service-level agreements (SLAs). Reliability analytics compute mean time between failures (MTBF), mean time to repair (MTTR), and failure trend analysis for proactive intervention.

**Tables:** 19 | **Records:** 1,411 | **Key Relationships:** Asset Hierarchy (Parent-Child), Work Order Workflow (Pending → In-Progress → Completed), Bi-directional (Maintenance ↔ Operations Faults)

| **Data Group** | **Data Access Roles** |
|---|---|
| Manufacturing and Operations | Maintenance Manager, Technician, Production Manager, Analyst, Planner |

---

## 5. GENIMS_ERP_DB

Enterprise Resource Planning system managing materials planning, inventory management, procurement, and order fulfillment across the supply chain. Materials master maintains 150+ SKUs with specifications, sourcing rules (preferred suppliers, MOQs), standards costs, and lead times. Bill of Materials (BOM) module defines product structures with 15+ product families and component hierarchies (up to 5 levels deep), linking to routing operations for costing and MES planning. Routing module specifies manufacturing sequences with 10 work centers and 30 operation steps, capturing standard times and resource requirements. Sales order processing captures customer orders (518 orders) with line-item details, delivery dates, and special requirements, flowing to production planning. Production order management converts sales demand and inventory plans into manufacturing requirements (1,540 production orders), specifying quantities, due dates, and quality parameters. Purchase requisitions and purchase orders (326 POs with 1,346 lines) manage supplier sourcing with pricing terms and delivery tracking. Inventory balances (600 SKUs with on-hand, reserved, and in-transit quantities) feed demand planning and safety stock calculations. Material requirements planning (MRP) runs generate replenishment recommendations based on sales forecasts and safety stock policies. Goods receipt process validates received materials against purchase orders and quality specifications. Inspection plans and characteristics define supplier quality requirements and acceptance criteria. Cost centers allocate overhead to production orders and departments. General ledger integration captures material costs, labor, and overhead for product costing. Bi-directional integration: sends production orders to MES, receives actual costs and material consumption for variance analysis.

**Tables:** 24 | **Records:** 6,352 | **Key Relationships:** Hierarchical (BOM parent-child), Many-to-Many (Sales Orders → Production Orders → Materials), Process Flow (Sales → Production → Purchase)

| **Data Group** | **Data Access Roles** |
|---|---|
| Business Management | Inventory Manager, Sales Manager, Procurement Manager, Analyst, Planner |

---

## 6. GENIMS_FINANCIAL_DB ✨ NEW v2.0

Financial accounting and general ledger system capturing journal entries, account reconciliations, cost allocations, and financial reporting. Chart of accounts (35 accounts) organized by account type (assets, liabilities, equity, revenues, expenses) with cost center allocations. GL posting rules (4 rules) automate posting logic for transaction types (material receipts, labor, overhead). Fiscal periods (24 periods across 2 fiscal years) define reporting calendars with month/quarter/year boundaries. Cost centers (6 cost centers) organize overhead allocation by manufacturing function (production, maintenance, quality, logistics). Exchange rates (50 rates) manage multi-currency transactions and consolidation. Budget headers (1 budget) define annual budget parameters and variance thresholds. **Configuration data only** — transactional tables (journal_entry_headers, journal_entry_lines, account_balances, budget_lines, depreciation_schedules) are populated by daemon processes, period close batch jobs, and accounting applications at runtime. Integration: receives material costs from ERP, labor costs from MES, and overhead allocations from cost management. Supports financial reporting, variance analysis, and consolidation. **Note:** Separated from genims_erp_wms_sync_db in v2.0 to support clean schema alignment.

**Tables:** 7 | **Records:** 122 | **Key Relationships:** Account Hierarchy (Chart of Accounts), Period Management (Fiscal Periods/Years), Allocation (Cost Centers)

| **Data Group** | **Data Access Roles** |
|---|---|
| Business Management | Finance Manager, Accountant, Approver, Analyst, Auditor |

---

## 7. GENIMS_ERP_WMS_SYNC_DB ✨ NEW v2.0

Inventory synchronization configuration database managing ERP-to-WMS integration rules and real-time inventory snapshots. Inventory sync mappings (2 mappings) define synchronization rules: which WMS inventory locations map to ERP warehouse/bin structures, sync frequency (real-time, hourly, daily), and conflict resolution policies. Inventory snapshot (50 records) captures point-in-time inventory balances by location, lot number, and serial number, enabling reconciliation and discrepancy detection. Serves as the canonical truth for synchronized inventory state across ERP and WMS systems. **Configuration data only** — transactional tables (inventory_sync_queue, inventory_sync_errors, inventory_adjustments_sync, sync_metrics) are populated by the ERP-WMS sync daemon running every 5 minutes. Enables bi-directional synchronization: ERP production orders trigger WMS pick tasks, WMS shipments update ERP inventory, and WMS cycle counts reconcile against ERP balances. Critical for preventing stock-outs and overstock situations. Integration: WMS_DB sends picking/shipping data, ERP_DB sends material requirements and on-hand updates. **Note:** Split from financial_db in v2.0 to support independent scaling and focused database schema.

**Tables:** 2 | **Records:** 52 | **Key Relationships:** Configuration Mapping (ERP Warehouse ↔ WMS Location), Snapshot (temporal inventory state)

| **Data Group** | **Data Access Roles** |
|---|---|
| Supply Chain and Logistics | Inventory Manager, Analyst, Planner, Supervisor, Auditor |

---

## 8. GENIMS_WMS_DB

Warehouse Management System optimizing inventory storage, picking, packing, and shipping operations across 3 warehouses with 18 zones and 100+ storage bins. Warehouse master defines storage policies by zone (fast-moving, slow-moving, hazardous, temperature-controlled) with bin-level capacity and product-family constraints. Receiving process captures inbound shipments, creates putaway tasks based on slotting rules, and validates against purchase orders. Putaway management assigns received materials to storage locations using ABC analysis and velocity-based slotting to minimize pick distances. Wave planning consolidates multiple customer orders into pick waves (173 waves) to optimize labor productivity. Pick task management assigns picks to warehouse workers (60 staff), tracks completion, and manages exceptions (out-of-stock, location errors). Packing operations consolidate picks per customer order, apply shipping labels, and capture package dimensions/weights. Shipping integration with TMS sends freight manifests and triggers shipment tracking. Cycle count management schedules periodic physical counts (25 tasks) for inventory reconciliation, capturing variance reasons (system error, shrinkage, miscount). Warehouse equipment tracking manages asset inventory (forklifts, scanners, etc.) and maintenance schedules. Slotting rules (30 rules) dynamically optimize bin assignments based on sales velocity, product size, and pick frequency. Real-time integration: receives picking requirements from sales orders (via ERP), receives inventory adjustments from manufacturing (WMS_TMS_sync_log captures synchronization events). Performance metrics: inventory turns, pick accuracy, labor productivity.

**Tables:** 17 | **Records:** 1,280 | **Key Relationships:** Hierarchical (Warehouses → Zones → Bins), Process Flow (Receiving → Putaway → Picking → Packing → Shipping), Slotting Rules

| **Data Group** | **Data Access Roles** |
|---|---|
| Supply Chain and Logistics | Warehouse Manager, Supervisor, Operator, Analyst, Planner |

---

## 9. GENIMS_TMS_DB

Transportation Management System orchestrating outbound logistics, carrier management, and delivery operations for 390 shipments across 10 carriers. Carrier master maintains partnerships with 10 carriers offering 30+ service types (ground, air, international) with negotiated rate cards (90 rates covering various dimensions: weight, zone, service level). Shipment creation aggregates customer orders into shipments by carrier and service level, capturing origin/destination, package count, weight/dimensions, and special handling requirements. Route optimization assigns shipments to routes (25 routes) with sequential stop sequences (136 stops), leveraging carrier networks and delivery schedules. Delivery execution tracks carrier operations: pickup times, in-transit tracking events (100 events), and proof of delivery (390 POD records) with recipient signatures. Return logistics manages reverse shipments (20 shipments) for customer returns, capturing return reasons and disposition (restock, repair, scrap). Freight invoice matching (25 invoices with 99 lines) validates carrier charges against shipment parameters and contracted rates. WMS-TMS integration (50 sync logs) coordinates warehouse picking with transportation readiness: WMS confirms pack completion, TMS triggers carrier pickup. Real-time tracking sends shipment status updates to Sales/Customer Service for visibility. Performance analytics: on-time delivery %, cost per shipment, carrier performance scorecards. Integration: receives shipping demands from Sales Orders (ERP), sends delivery confirmations for customer billing.

**Tables:** 17 | **Records:** 1,962 | **Key Relationships:** Carrier Management (Carriers → Services → Rates), Route Planning (Routes → Stops → Shipments), Reverse Logistics (Returns)

| **Data Group** | **Data Access Roles** |
|---|---|
| Supply Chain and Logistics | Logistics Manager, Coordinator, Driver, Analyst, Planner |

---

## 10. GENIMS_CRM_DB

Customer Relationship Management system capturing the complete customer lifecycle from lead generation through opportunity management, quote execution, and contract administration. Sales organization structure defines 15 sales representatives organized by 5 territories covering geographic or customer-segment-based boundaries. Accounts (10 master accounts) represent corporate customers with parent-child relationships for multi-subsidiary organizations. Contacts (39 contacts) capture stakeholder information at customer accounts with roles (purchasing, engineering, finance) and communication preferences. Lead management (100 leads) tracks marketing-qualified leads through qualification pipeline with activity tracking (100+ lead activities) capturing email, phone, meeting interactions. Opportunity management (100 opportunities) converts qualified leads into sales opportunities with product offerings (100 opportunity_product lines), competitive analysis, and stage progression (proposal, negotiation, closed). Quote generation captures customer-specific pricing and terms, with quote comparison tools tracking competitive wins/losses. Case management (50 support cases with 40 comments) handles customer escalations and issue resolution with SLA tracking. Activities (35 generic activities) track all customer touches across the organization. Notes (45 records) capture key customer intelligence and preference data. Campaigns (6 campaigns with 208 members) track marketing initiatives, lead sources, and program effectiveness. Sales forecasting (60 forecasts) predicts quarterly revenue by sales rep and opportunity stage. Contracts (10 contracts) formalize customer relationships with renewal dates and commercial terms. Integration: sends customer shipments to Finance for AR billing, imports installed base from Service_DB for upsell targeting. CRM serves as the customer master for all downstream systems, ensuring consistent customer identification and communication.

**Tables:** 22 | **Records:** 1,227 | **Key Relationships:** Account Hierarchy (Parent/Child), Opportunity Pipeline (Stages), Activity Audit Trail, Sales Organization (Rep-Territory)

| **Data Group** | **Data Access Roles** |
|---|---|
| Business Management | Sales Manager, Sales Representative, Analyst, Customer Service Rep, Planner |

---

## 11. GENIMS_SERVICE_DB

Customer Service and Support system managing the complete customer support lifecycle from ticket creation through resolution and customer satisfaction. Service ticket management (100 tickets) captures customer issues with priority levels, SLA definitions (6 SLAs by issue type: severity 1 = 4-hour response, severity 2 = 8-hour, severity 3 = 24-hour), and escalation workflows. Ticket comments (100 entries) maintain detailed resolution history with full text search capability. Ticket attachments and photos document problem details, symptoms, and evidence. Escalation rules (1 automated rule) define automatic escalation triggers when SLAs breach. Knowledge base (50 articles organized in 5 categories) provides customers with self-service solutions and troubleshooting guides. KB ratings (421 customer ratings) drive continuous improvement of support articles. Warranty management (35 warranty registrations) tracks product warranty coverage by customer, product, and expiration date. Warranty claims (30 claims) process customer claims against warranty policies with approval workflows. RMA (Return Material Authorization) management (25 RMA requests with 40 line items) coordinates product returns, repair, and refurbishment. Field service appointments (50 appointments) schedule on-site visits for complex issues, tracking technician assignments and travel time. Field technicians (10 technicians) maintain certifications, availability, and customer assignment preferences. Service parts inventory (100 spare parts) maintains on-hand inventory of replacement components used during service calls. Customer surveys (3 surveys with 55 responses) measure satisfaction and identify improvement opportunities. Integration: receives warranty information from Sales_DB, receives product failure data from Operations_DB, sends customer feedback to CRM and Manufacturing for quality improvement. Analytics: first contact resolution rate, average resolution time, customer satisfaction score (CSAT).

**Tables:** 27 | **Records:** 1,351 | **Key Relationships:** Ticket Lifecycle (Ticket → Comments → Escalations), Knowledge Base (Categories → Articles), Warranty Hierarchy (Registration → Claims → RMA), Field Service Scheduling

| **Data Group** | **Data Access Roles** |
|---|---|
| Quality and Service | Support Manager, Support Agent, Analyst, Customer, Technician |

---

## 12. GENIMS_HR_DB

Human Capital Management system managing the complete employee lifecycle: recruitment, onboarding, development, performance management, compensation, benefits, and offboarding. Organizational structure defines 20 departments, 10 job roles, and 50 positions with reporting hierarchies and span of control analysis. Employee master (100 employees as of latest run) captures core HR data including employment history (50 records showing movement between roles/departments), skills inventory (100 skill records: CNC operation, quality auditing, maintenance certifications), and professional certifications (50 certs: ISO, welding, electrical). Shift assignment management (60 assignments) allocates employees to work shifts with shift schedules (12 scheduling patterns covering 3-shift and weekend operations). Goals management (148 goals) aligns individual employee objectives with company strategy using OKR (Objectives and Key Results) framework. Training management defines 10 training courses (CNC operation, quality inspection, safety, leadership) with scheduling of 20+ training classes annually, enrollment tracking (100 enrollments), and completion records. Competency assessment tracks proficiency levels and identifies training needs. Career path planning (10 career paths) defines progression tracks from entry-level to senior roles with skill requirements (30 skill-to-role mappings). Performance management (30 annual reviews) documents employee evaluations with feedback and development plans. Performance KPIs (60 metrics) track individual contribution to department/company goals: production efficiency, quality metrics, safety incidents. Succession planning (10 open positions identified) identifies and develops replacement candidates (30 candidates) for critical roles. Leave management defines 6 leave types (vacation, sick, personal, unpaid, sabbatical, parental) with carry-forward rules. Leave requests (50 approved requests) flow through approval workflows. Leave balances (320 employee records) track year-to-date utilization. Attendance tracking (200 records) monitors punctuality and identifies patterns. Safety incident management (16 incidents) documents workplace injuries, near-misses, and corrective actions, driving continuous safety improvement. PPE (Personal Protective Equipment) requirements define equipment by role/department. Onboarding management (40 records) orchestrates new hire workflows: background checks, equipment setup, training schedules. Offboarding tracking (15 records) manages exit procedures: badge revocation, knowledge transfer, exit interviews. HCM integration: receives labor costs and hours from MES for payroll, sends employee roster to Operations for shift planning. Analytics: turnover rate, training ROI, performance distribution, succession readiness.

**Tables:** 33 | **Records:** 1,673 | **Key Relationships:** Organizational Hierarchy (Departments → Jobs → Positions → Employees), Learning Management (Courses → Enrollments → Completions), Competency Framework (Skills → Roles → Requirements), Career Pathing, Performance Cycle

| **Data Group** | **Data Access Roles** |
|---|---|
| Business Management | HR Manager, HR Specialist, Department Manager, Analyst, Auditor |

---

## 13. GENIMS_QUALITY_DB

Quality Management System implementing enterprise-wide quality control, compliance, and continuous improvement. Quality audits (9 audits) assess manufacturing process compliance with internal standards and customer requirements, discovering 9 audit findings. Quality documents (20 documents) maintain control plans, work instructions, test methods, and acceptance criteria. Quality KPIs (90 metrics) track leading indicators: incoming inspection pass rates, process capability (Cpk/Ppk), first-pass yield, defect rates (ppm), by product, line, and supplier. Non-conformance Reports (69 NCR headers with 36 defect details) document quality deviations, root cause analysis, and corrective actions. CAPA (Corrective and Preventive Action) management (13 CAPA headers with 42 action items) drives closure of NCRs with systemic improvements. Control plans (20 plans with 54 characteristics) define manufacturing operations, control points, and acceptance criteria by product. Supplier quality metrics (19 metrics by supplier) track incoming material quality: defect rates, on-time delivery, documentation completeness. Calibration management (30 measuring instruments with 90 calibration records) ensures measurement system accuracy with 3-year audit trail (3 alerts for calibration overdue). SPC (Statistical Process Control) charts (15 control charts with 517 data points) monitor process stability and trend detection. PPAP (Production Part Approval Process) submissions (10 submissions) track supplier approval of production parts with dimensional data, material certs, and initial run data. Eight-D reports (5 reports) formalize customer complaint investigation and resolution. Integration: receives defect data from Manufacturing_DB (quality inspections), sends quality metrics to CRM for customer visibility, links to Supplier_DB for supplier CAPA tracking. Compliance: automotive (IATF 16949), pharmaceutical (FDA 21 CFR Part 11), general (ISO 9001). Analytics: process capability by line/product, defect Pareto charts, supplier performance trending.

**Tables:** 20 | **Records:** 1,286 | **Key Relationships:** Quality Framework (Audits → Findings → CAPA), Control Planning (Plans → Characteristics → Data Points), Supplier Quality (Metrics → Performance Trending)

| **Data Group** | **Data Access Roles** |
|---|---|
| Quality and Service | Quality Manager, Inspector, Auditor, Plant Manager, Analyst |

---

## 14. GENIMS_SUPPLIER_DB

Supplier Management Portal and vendor management system for strategic sourcing, contract negotiation, and supplier performance monitoring. RFQ (Request for Quote) management (20 RFQ headers with 50 lines, 30 suppliers solicited, 20 responses received) drives competitive bidding for material requirements. Supplier contracts (10 contracts) formalize ongoing supplier relationships with pricing, payment terms (net 30/60), volume commitments, and quality requirements. Contract pricing (30 price records) maintains negotiated rates by part number, volume tier, and effective date. Quote comparison (15 comparisons) supports supplier selection with total cost of ownership analysis: unit price, lead time, quality history, logistics costs. Supplier performance metrics (30 metrics by supplier) track KPIs: on-time delivery %, defect rates (ppm), quote responsiveness, engineering support quality. Supplier scorecards (30 scorecards) aggregate performance across dimensions (quality, delivery, cost, service) with annual ratings (excellent, good, satisfactory, needs improvement). Supplier audits (7 audits) document on-site assessments of supplier capabilities, processes, and quality systems. Supplier qualification (10 qualifications) manages supplier approval process: sample validation, capacity verification, capability certifications. Purchase requisitions (20 requisitions with 50 lines) originate from manufacturing demand planning, flowing to Supplier_Portal for RFQ generation. Supplier documents (20 documents) store certs of conformance (CoC), technical data sheets, quality agreements. Supplier communications (20 records) maintain correspondence history. Portal users (30 portal accounts) grant supplier employees access to order status, shipment tracking, and technical data. Audit findings (25 findings) document supplier non-conformances discovered during audits with action request (CAR) tracking. Notifications (25 notifications) alert suppliers of quality issues, delivery problems, and process changes. Three-way match (30 match logs) validates purchase orders, receipts, and invoices for payment authorization. Integration: receives purchase requisitions from ERP, provides received material quality data to Quality_DB, sends qualified supplier list to Procurement for sourcing decisions. Analytics: supplier cost trends, quality performance, supply chain risk assessment by supplier concentration.

**Tables:** 24 | **Records:** 677 | **Key Relationships:** RFQ Lifecycle (RFQ → Quotes → Selection), Supplier Hierarchy (Organization → Locations → Contacts → Users), Performance Management (Metrics → Scorecard → Audits → CAPA)

| **Data Group** | **Data Access Roles** |
|---|---|
| Supply Chain and Logistics | Procurement Manager, Supplier Coordinator, Supplier User, Analyst, Auditor |

---

## Summary Matrix

| # | Database | Type | Tables | Records | Key Purpose | Status |
|---|----------|------|--------|---------|-------------|--------|
| 1 | MASTER_DB | Master Data | 10 | 13,335 | Single source of truth | ✅ Active |
| 2 | OPERATIONS_DB | Time-Series | 6 | 372,179 | Real-time monitoring | ✅ Active |
| 3 | MANUFACTURING_DB | Transactional | 10 | 10,053 | Production execution | ✅ Active |
| 4 | ERP_DB | Planning | 24 | 6,352 | Materials & supply chain | ✅ Active |
| 5 | FINANCIAL_DB | GL & Accounting | 7 | 122 | Financial control | ✅ Active |
| 5b | ERP_WMS_SYNC_DB | Sync Config | 2 | 52 | Inventory sync | ✅ Active |
| 6 | WMS_DB | Warehouse | 17 | 1,280 | Inventory operations | ✅ Active |
| 7 | TMS_DB | Logistics | 17 | 1,962 | Transportation ops | ✅ Active |
| 8 | MAINTENANCE_DB | Asset Mgmt | 19 | 1,411 | Equipment lifecycle | ✅ Active |
| 9 | CRM_DB | Customer Mgmt | 22 | 1,227 | Sales pipeline | ✅ Active |
| 10 | SERVICE_DB | Support | 27 | 1,351 | Customer support | ✅ Active |
| 11 | HR_DB | Human Capital | 33 | 1,673 | Employee mgmt | ✅ Active |
| 12 | QUALITY_DB | Quality Control | 20 | 1,286 | Quality compliance | ✅ Active |
| 13 | SUPPLIER_DB | Vendor Mgmt | 24 | 677 | Supplier relations | ✅ Active |

---

## Integration Matrix

**Data Flows:**
- **ERP_DB** → MES (Production Orders), Finance (Material Costs), Procurement (POs), Sales (Orders)
- **OPERATIONS_DB** ← Sensors/IoT, → Predictive Analytics, → Maintenance (Fault Events)
- **MANUFACTURING_DB** ← ERP (Orders), → Quality (Inspections), → Maintenance (Labor/Costs), → Finance (Labor Costs)
- **MAINTENANCE_DB** ← Operations (Faults/Downtime), → Finance (Maintenance Costs), → ERP (Spare Parts)
- **WMS_DB** ← ERP (Inventory), → TMS (Shipments), ↔ ERP_WMS_SYNC_DB (Sync Coordination)
- **TMS_DB** ← WMS (Picking/Packing), → CRM/Service (Delivery Status)
- **CRM_DB** → Service (Installed Base), ← Service (Customer Feedback), ← Quality (Issues)
- **HR_DB** → Operations (Shift Planning), ← Manufacturing (Labor Tracking), ← Finance (Payroll)
- **QUALITY_DB** ← Manufacturing (Inspections/Defects), ← Operations (Machine Issues), → Supplier_DB (CAR Requests)
- **SUPPLIER_DB** ← ERP (RFQs), → Quality (Incoming Quality), ← Finance (Invoice Matching)

**Master Data Sources:**
- All systems reference **MASTER_DB** for Factory/Line/Machine/Employee/Product dimensions
- **ERP_DB** is authoritative for customer and material masters
- **SUPPLIER_DB** is authoritative for supplier masters

---

## Users by Role

| Role | Email |
|------|-------|
| Data Manager | datamanager@genims.com |
| Shift Supervisor | shift_supervisor@genims.com |
| Shop Floor Operator | shopfloor_operator@genims.com |
| Maintenance Manager | maintenance_manager@genims.com |
| Maintenance Technician | maintenance_tech@genims.com |
| Inventory Manager | inventory_manager@genims.com |
| Sales Manager | sales_manager@genims.com |
| Procurement Manager | procurement_manager@genims.com |
| Finance Manager | finance_manager@genims.com |
| Accountant | accountant@genims.com |
| Finance Approver | finance_approver@genims.com |
| Warehouse Manager | warehouse_manager@genims.com |
| Warehouse Supervisor | warehouse_supervisor@genims.com |
| Warehouse Operator | warehouse_operator@genims.com |
| Logistics Manager | logistics_manager@genims.com |
| Logistics Coordinator | logistics_coordinator@genims.com |
| Driver | driver@genims.com |
| Sales Representative | sales_rep@genims.com |
| Customer Service Rep | cust_service_rep@genims.com |
| Support Manager | support_manager@genims.com |
| Support Agent | support_agent@genims.com |
| Service Technician | service_tech@genims.com |
| HR Manager | hr_manager@genims.com |
| HR Specialist | hr_specialist@genims.com |
| Department Manager | dept_manager@genims.com |
| Quality Manager | quality_manager@genims.com |
| Quality Inspector | quality_inspector@genims.com |
| Quality Auditor | quality_auditor@genims.com |
| Plant Manager | plant_manager@genims.com |
| Supplier Coordinator | supplier_coordinator@genims.com |
| Supplier User | supplier_user@genims.com |
| Data Analyst | data_analyst@genims.com |
| Auditor | auditor@genims.com |

---

**Document Version:** 2.0 (December 27, 2025)  
**Status:** Complete — All 14 databases documented with comprehensive descriptions and user accounts
