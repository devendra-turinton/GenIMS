# GenIMS Data Sources & Database Architecture

## Overview
The GenIMS (Generic Integrated Manufacturing System) platform integrates 13 PostgreSQL databases organized into 5 logical data groups, creating a unified ecosystem for manufacturing, operations, finance, supply chain, and human resources management.

---

## 1. Data Groups (High-Level Organization)

The 13 databases are organized into **5 primary data groups**:

### **Group 1: Core & Master Data (Foundation)**
- **genims_master_db** - Master data hub
- Provides reference data for all other systems

### **Group 2: Manufacturing & Operations (Production)**
- **genims_operations_db** - Operational intelligence
- **genims_manufacturing_db** - Manufacturing execution
- **genims_maintenance_db** - Asset maintenance & CMMS
- Focuses on production floor, asset management, and real-time operations

### **Group 3: Business Management (Enterprise)**
- **genims_erp_db** - Enterprise resource planning
- **genims_financial_db** - Financial & accounting
- **genims_crm_db** - Customer relationship management
- **genims_hr_db** - Human capital management
- Covers business operations, finance, sales, and people management

### **Group 4: Supply Chain & Logistics (Movement)**
- **genims_wms_db** - Warehouse management
- **genims_tms_db** - Transportation management
- **genims_supplier_db** - Supplier portal
- Manages inventory, logistics, and supplier interactions

### **Group 5: Quality & Service (Compliance & Support)**
- **genims_quality_db** - Quality management system
- **genims_service_db** - Customer service & support
- Ensures product quality and customer satisfaction

---

## 2. Data Access Roles (Per Database)

### **1. genims_master_db**
- **Admin** - Full access, can modify master data and configurations
- **Data Manager** - Can create/edit organizations, products, customers, employees
- **Viewer** - Read-only access to all master data

### **2. genims_operations_db**
- **Plant Manager** - Full access, dashboard creation, alerts configuration
- **Equipment Technician** - Can view sensor data, equipment status, maintenance schedules
- **Supervisor** - Production metrics, downtime tracking, shift analytics
- **Analyst** - Read-only access to historical data and reports

### **3. genims_manufacturing_db**
- **Production Manager** - Full access, work order creation, resource allocation
- **Shift Supervisor** - Can view/update work orders, assign labor, record quality checks
- **Shop Floor Operator** - Can view assigned work orders and record completion
- **Planner** - Read access for scheduling and routing optimization

### **4. genims_maintenance_db**
- **Maintenance Manager** - Full access, schedule creation, work order approval
- **Technician** - Can view/update assigned maintenance orders, record completion
- **Planner** - Can schedule preventive maintenance and view equipment history
- **Analyst** - Read-only access to failure analysis and metrics

### **5. genims_erp_db**
- **Procurement Manager** - Full access, PO creation, vendor management
- **Inventory Manager** - Full access, stock level management, MRP execution
- **Sales Manager** - Full access, sales order creation and shipment tracking
- **Planner** - Can view demand forecasts and inventory levels
- **Viewer** - Read-only access to procurement and sales data

### **6. genims_financial_db**
- **Finance Manager** - Full access, GL management, budget creation, approvals
- **Accountant** - Can create/post journal entries, view GL accounts
- **Approver** - Can approve transactions based on amount thresholds
- **Analyst** - Read-only access to GL, budgets, and financial reports

### **7. genims_wms_db**
- **Warehouse Manager** - Full access, location allocation, cycle count management
- **Supervisor** - Can manage picking/packing operations, view inventory
- **Operator** - Can process GRN, perform putaway, pick and pack operations
- **Planner** - Read access for inventory optimization and layout planning

### **8. genims_tms_db**
- **Logistics Manager** - Full access, shipment planning, carrier contracts
- **Coordinator** - Can create shipments, assign carriers, track deliveries
- **Driver** - Can view assigned shipments and update delivery status
- **Analyst** - Read-only access to logistics metrics and route analysis

### **9. genims_crm_db**
- **Sales Manager** - Full access, pipeline management, quota setting
- **Sales Rep** - Can manage own opportunities, accounts, and activities
- **Customer Service Rep** - Full access, customer management, order tracking
- **Analyst** - Read-only access to sales forecasts and customer analytics

### **10. genims_hr_db**
- **HR Manager** - Full access, employee lifecycle, payroll, policies
- **HR Specialist** - Can manage recruitment, benefits, performance reviews
- **Employee** - Can view own profile, apply for leave, access payroll
- **Department Manager** - Can view team members and approve leave requests

### **11. genims_quality_db**
- **Quality Manager** - Full access, inspection plan creation, CAPA management
- **Inspector** - Can record inspection results and non-conformances
- **Auditor** - Can conduct internal/supplier audits and document findings
- **Analyst** - Read-only access to quality metrics and trend analysis

### **12. genims_supplier_db**
- **Procurement Manager** - Full access, supplier management, scorecard setting
- **Supplier Coordinator** - Can manage PO visibility, ASN, communications
- **Supplier User** - Can view own POs, shipment status, quality feedback
- **Analyst** - Read-only access to supplier performance metrics

### **13. genims_service_db**
- **Support Manager** - Full access, ticket routing, SLA management, KB administration
- **Support Agent** - Can create/update tickets, log interactions, manage resolutions
- **Customer** - Can create service requests, view ticket status, access KB
- **Analyst** - Read-only access to support metrics and customer satisfaction data

---

## 3. Database Descriptions (13 Databases)

### **1. genims_master_db** (Master Data Hub)

The foundational database serving as the single source of truth for all enterprise master data across the GenIMS (Generative Industrial Managed Services) ecosystem. Contains multi-factory operations data including factory locations with certifications and capacity, production infrastructure hierarchy (production lines, machines with criticality levels, sensors collecting 10+ measurement types), human resources (employees with roles and certifications), product portfolios (bill of materials, cycle times, quality targets), and customer information (types, volumes, SLA requirements). The data model uses a hierarchical star schema centered on factories: Factories → Production Lines → Machines → Sensors creates a parent-child hierarchy, while line_product_mapping and customer_product_mapping establish many-to-many relationships with line-specific metrics (cycle times, yields) and customer parameters (pricing, volumes, quality requirements). The database maintains referential integrity through foreign key constraints and optimizes query performance with cascading indices on common joins. Serves as the bootstrap data source ensuring data consistency and enabling seamless enterprise-wide integration across all 12 operational systems.

**Tables:** 10 | **Records:** 2,500+ | **Key Relationships:** Hierarchical (Factories → Lines → Machines → Sensors), One-to-Many (Factories → Employees/Shifts), Many-to-Many (Lines ↔ Products, Customers ↔ Products)

---

### **2. genims_operations_db** (Operational Intelligence)

Captures real-time and historical production floor data from IoT sensors and SCADA systems. Monitors equipment performance, OEE metrics, downtime incidents, shift performance, and production output. Integrates sensor telemetry with machine status and resource utilization tracking. Enables real-time dashboards, operational alerts, and predictive maintenance planning through anomaly detection. Tracks production efficiency, cycle times, and equipment availability across the factory. Maintains 90+ days of detailed historical data supporting trend analysis and continuous improvement initiatives. Serves as the gateway between physical manufacturing assets and digital systems, enabling data-driven decision-making and root cause analysis of production issues. Relationships link sensor readings to specific machines and production lines from master database, creating unified operational visibility across the organization.

**Tables:** 38+ | **Records:** 150,000+ | **Key Relationships:** Equipment & Sensors (Master DB), Production Lines (Master DB)

---

### **3. genims_manufacturing_db** (Manufacturing Execution - MES)

Manages the complete manufacturing workflow from work order creation to completion. Controls production scheduling, batch management, and shop floor execution with real-time job tracking and resource allocation. Tracks material consumption, labor assignments, and equipment usage throughout production. Records quality checks at multiple manufacturing stages ensuring compliance with product standards. Manages production routings, bill of materials explosion, and inventory allocation to production batches. Supports multiple manufacturing scenarios including make-to-stock, make-to-order, and job shop operations. Integrates product specifications and routing information from master database. Provides production visibility and resource scheduling for shop floor supervisors. Links to operations database for real-time machine feedback and to financial database for labor and material cost tracking.

**Tables:** 52+ | **Records:** 75,000+ | **Key Relationships:** Products & Routes (Master DB), Equipment Usage (Operations DB), Labor & Costs (Finance DB)

---

### **4. genims_maintenance_db** (Computerized Maintenance Management - CMMS)

Manages preventive and corrective maintenance operations for all manufacturing equipment and assets. Records maintenance schedules, work orders, spare parts inventory, and complete maintenance history. Tracks equipment downtime incidents, failure patterns, and maintenance costs by equipment and technician. Manages maintenance teams, their skills, and work assignments across factories. Records warranty information, service agreements, and calibration schedules. Supports predictive maintenance analytics through failure trend analysis and MTBF/MTTR calculations. Links equipment from master database with maintenance schedules from operations data to optimize preventive maintenance timing. Integrates with financial systems for maintenance cost tracking and asset depreciation. Enables condition-based maintenance strategies and extends equipment lifecycle through data-driven intervention.

**Tables:** 35+ | **Records:** 45,000+ | **Key Relationships:** Equipment & Machines (Master DB), Downtime Events (Operations DB), Cost Tracking (Finance DB)

---

### **5. genims_erp_db** (Enterprise Resource Planning)

Comprehensive business management system integrating procurement, inventory, production, and sales operations. Manages purchase requisitions, purchase orders, goods receipt, and supplier invoicing with full audit trails. Tracks inventory movements, stock levels, and warehouse locations across multiple facilities. Records sales orders, delivery schedules, and customer shipments. Manages material requirements planning (MRP) with automated order generation based on demand forecasts. Supports inter-company transfers and multiple distribution channels. Provides end-to-end supply chain visibility from procurement through delivery. Integrates with financial systems for real-time cost accounting and variance analysis. Central hub connecting manufacturing operations with finance, sales with inventory, and procurement with supplier relationships. Links customer orders to production scheduling and material purchases.

**Tables:** 68+ | **Records:** 98,000+ | **Key Relationships:** Products (Master DB), Manufacturing (MES DB), Finance (GL DB), Suppliers (Supplier DB)

---

### **6. genims_financial_db** (General Ledger & Accounting)

Comprehensive financial accounting system managing all monetary transactions and statutory reporting. Maintains chart of accounts, cost centers, and GL posting rules across multiple legal entities. Records journal entries, financial transactions, and account balances with complete audit trails. Manages multi-level budget creation, budget vs. actual variance analysis, and financial forecasting for planning. Tracks tax calculations, depreciation schedules, and accrual accounting adjustments. Implements multi-level transaction approval workflows with authorization controls based on amount and transaction type. Generates financial reports including trial balance, income statements, and cash flow analysis. Supports statutory compliance, tax filings, and management reporting. Records all approval workflows and maintains audit trails of all financial activities. Links to ERP for cost allocation, to manufacturing for labor costs, and to payroll for expense tracking.

**Tables:** 27+ | **Records:** 4,634+ | **Key Relationships:** Cost Centers (Master DB), Transactions (ERP DB), Labor (HR DB)

---

### **7. genims_wms_db** (Warehouse Management System)

Manages complete warehouse operations from receiving through shipping including putaway, picking, packing, and cross-docking. Records inbound and outbound shipment details with goods received notes (GRN) linking to POs. Manages warehouse locations, bin allocation, and inventory optimization algorithms for space utilization. Tracks stock movements, cycle counts, and physical inventory audits with variance reporting. Handles returns management, quality holds, and quarantine inventory segregation. Supports multi-location warehousing with inter-warehouse transfers and cross-docking operations. Generates picking lists optimized by location, packing slips, and shipping manifests. Provides real-time inventory visibility and location tracking for customers and internal operations. Integrates with ERP for inventory balances and with TMS for shipment handoff, enabling end-to-end supply chain visibility.

**Tables:** 42+ | **Records:** 88,000+ | **Key Relationships:** Inventory (ERP DB), Shipments (TMS DB)

---

### **8. genims_tms_db** (Transportation Management System)

Manages logistics and transportation operations for inbound and outbound shipments. Plans shipments, optimizes routes using distance and traffic algorithms, and tracks real-time delivery performance. Manages carrier selection, freight rate contracts, and shipping service levels by destination. Records consignments with delivery confirmations and proof of delivery (POD) for audit. Tracks transportation costs including fuel, tolls, and carrier fees with per-unit cost analysis. Manages fleet operations including vehicle assignments, maintenance schedules, and utilization metrics. Provides shipment visibility and real-time GPS tracking for customers. Optimizes logistics network routes to reduce transit time and transportation costs. Integrates with WMS for warehouse-to-carrier handoff and with CRM for customer notifications. Links to finance for freight cost tracking and to supplier database for inbound logistics.

**Tables:** 38+ | **Records:** 62,000+ | **Key Relationships:** Shipments (WMS/ERP DB), Customers (CRM DB), Costs (Finance DB)

---

### **9. genims_crm_db** (Customer Relationship Management)

Manages customer information, interactions, and sales processes across the customer lifecycle. Maintains customer master data including accounts, contacts, and complete communication history. Records sales opportunities with pipeline management tracking deal progression from lead to close. Manages quote generation, proposal creation, and sales order integration with ERP. Tracks all customer interactions including calls, emails, meetings, and support tickets. Manages customer segmentation for targeted campaigns and marketing automation workflows. Records customer feedback, preferences, historical purchases, and satisfaction scores. Supports sales forecasting through opportunity weighting and revenue analytics by customer and product. Provides 360-degree customer view integrating all touchpoints for relationship management. Links to ERP for order fulfillment, to master database for customer master sync, and to service database for support issue tracking.

**Tables:** 44+ | **Records:** 54,000+ | **Key Relationships:** Customers (Master DB), Orders (ERP DB), Service Tickets (Service DB)

---

### **10. genims_hr_db** (Human Capital Management - HCM)

Manages complete employee lifecycle from recruitment through retirement. Maintains employee master data, organizational hierarchy, and role-based access assignments. Records compensation structures including salary bands, bonus plans, and payroll deductions with tax withholding calculations. Tracks attendance records, leave balances, and employee schedules by shift and department. Manages performance reviews, training programs, and skill inventory for workforce planning. Records employee benefits enrollment, insurance coverage, and entitlements by employment contract. Supports recruitment workflows including job postings, candidate tracking, and hiring approval processes. Manages succession planning for critical roles and talent development programs. Provides HR analytics for headcount forecasting, turnover analysis, and labor cost budgeting. Links to master database for organization structure, to operations for shift assignments, and to finance for payroll expense tracking.

**Tables:** 51+ | **Records:** 78,000+ | **Key Relationships:** Organization Structure (Master DB), Shift Assignments (Operations DB), Payroll (Finance DB)

---

### **11. genims_quality_db** (Quality Management System - QMS)

Manages quality assurance and quality control across manufacturing operations. Records product specifications, quality standards, and acceptance criteria by product and customer. Manages inspection plans, scheduling, and quality check results at receiving, in-process, and final stages. Tracks non-conformances with root cause analysis and corrective action (CAPA) tracking to closure. Maintains calibration records for all measuring instruments with due dates and validation certificates. Records internal and supplier audits with findings and follow-up action tracking. Manages supplier quality performance metrics and certifications including ISO compliance. Provides statistical analysis including SPC, capability analysis, and quality cost tracking. Tracks customer complaints with severity, resolution, and preventive actions taken. Enables continuous improvement through trend reporting and quality metrics dashboards. Links to manufacturing database for in-process checks and to supplier database for incoming quality data.

**Tables:** 40+ | **Records:** 71,000+ | **Key Relationships:** Products (Master DB), Manufacturing (MES DB), Suppliers (Supplier DB)

---

### **12. genims_supplier_db** (Supplier Portal)

B2B collaboration platform enabling supplier visibility and supply chain transparency. Maintains supplier master data including capabilities, performance ratings, and contact information. Manages purchase order visibility allowing suppliers to view orders, quantities, and delivery dates. Records supplier shipments with advance shipment notices (ASN) and actual delivery confirmation. Tracks supplier quality metrics including on-time delivery percentage and defect rates with scorecards. Records supplier certifications, compliance documents, and internal audit results. Enables supplier communication through secure messaging and document exchange for specifications and amendments. Manages supplier development programs with collaborative improvement initiatives and performance targets. Provides supplier analytics including cost competitiveness, quality trends, and risk assessments. Enables collaborative forecasting and demand sensing for supply planning. Strengthens supplier relationships and supply chain resilience through transparency.

**Tables:** 36+ | **Records:** 51,000+ | **Key Relationships:** Suppliers (Master DB), POs (ERP DB), Quality (Quality DB)

---

### **13. genims_service_db** (Customer Service & Support)

Manages complete customer service operations and support ticket lifecycle. Records customer inquiries, complaints, and service requests with categorization by issue type. Manages service ticket routing based on expertise, assignment to support agents, and real-time resolution tracking. Records all customer interactions including communication history, resolution notes, and follow-up actions. Manages service level agreements (SLA) with compliance tracking and escalation protocols for breached tickets. Tracks customer satisfaction scores through post-resolution surveys and feedback collection. Maintains knowledge base articles, FAQs, and troubleshooting guides accessible to customers and support staff. Supports multi-channel support including phone, email, live chat, and self-service portal for 24/7 availability. Provides support analytics including ticket volume, resolution time, and agent performance metrics. Integrates with CRM for customer context and master database for product information, enabling personalized support and reducing resolution time.

**Tables:** 38+ | **Records:** 68,000+ | **Key Relationships:** Customers (CRM DB), Products (Master DB), Issues (Manufacturing DB)

---

## 3. Database Integration Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     GenIMS Master Data Hub                      │
│                    (genims_master_db)                           │
└────────────────┬────────────────────────────────────────────────┘
                 │
    ┌────────────┼────────────┬──────────┬──────────┬──────────┐
    │            │            │          │          │          │
    ▼            ▼            ▼          ▼          ▼          ▼
┌──────────┐  ┌─────────┐  ┌──────────┐ ┌───────┐ ┌─────┐  ┌──────┐
│Operations│  │Mfg/MES  │  │Maintenance│ │ERP    │ │Finance
│          │  │         │  │(CMMS)     │ │       │ │
└──────────┘  └─────────┘  └──────────┘ └───────┘ └─────┘  └──────┘
                                          │
                ┌────────────────────┬────┴──────┬──────────┐
                │                    │           │          │
                ▼                    ▼           ▼          ▼
            ┌─────────┐        ┌──────┐    ┌──────┐   ┌──────────┐
            │CRM      │        │WMS   │    │TMS   │   │Supplier  │
            │         │        │      │    │      │   │Portal    │
            └─────────┘        └──────┘    └──────┘   └──────────┘

            Quality (QMS)     HR (HCM)     Service Support
```

---

## 4. Data Flow & Integration Points

### **Upstream Sources (External)**
- IoT/SCADA Systems → Operations DB
- ERP Legacy Systems → ERP DB
- Supplier Systems → Supplier Portal DB
- E-commerce Platforms → CRM DB

### **Key Integration Flows**
1. **Master → All**: Reference data flows from master DB to all other systems
2. **Operations → MES → ERP**: Production data flows up through manufacturing to enterprise
3. **CRM ↔ Sales Orders → ERP → Finance**: Sales transactions flow through business systems
4. **Procurement → ERP ↔ Supplier DB**: Bidirectional collaboration
5. **WMS ↔ TMS**: Inventory-to-logistics integration
6. **Quality → Finance & CRM**: Quality metrics feed into cost and customer systems
7. **HR → All Systems**: Employee data accessible across organization

---

## 5. Technology Stack

- **Database**: PostgreSQL 13+
- **Data Format**: JSON (staging layer before database load)
- **Data Generation**: Python 3.9+
- **Integration**: Python scripts with SQL connectors
- **Orchestration**: Full Setup Script (scripts/full_setup.py)
- **Schema Management**: SQL migration scripts per database
- **Total Records**: 700,000+ across 13 databases
- **Total Tables**: 500+

---

## 6. Getting Started

### Setup All 13 Databases
```bash
python3 scripts/full_setup.py
```

### Load Specific Database
```bash
python3 [database_folder]/generate_*.py
```

### Verify Installation
```bash
psql -l  # List all databases
```

---

## 7. Support & Documentation

For detailed information about each database:
- See README files in respective folders (01-12)
- Review SQL schema files for table structures
- Check data generators for field definitions
- Refer to Database Architecture documents for detailed ERD diagrams

**Last Updated:** December 24, 2025  
**Version:** 1.0  
**Status:** Production Ready
