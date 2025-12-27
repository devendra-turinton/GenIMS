# GenIMS Platform - Semantic Layer: Databases and Tables

## Database Architecture Overview

GenIMS (Generic Integrated Manufacturing System) is a comprehensive enterprise resource planning platform designed for manufacturing operations. The system consists of 14 integrated modules covering the complete manufacturing lifecycle from human resources and procurement through production, quality control, warehousing, and financial management.

---

## MODULE 1: MASTER DATA

**Module Description:**
The Master Data module serves as the foundational reference data repository for the entire GenIMS platform. It contains static and semi-static data that defines the organizational structure, business entities, materials, products, and relationships that all other modules depend upon. This module establishes the core entities including companies, factories, warehouses, suppliers, customers, materials, products, bills of materials (BOMs), employees, and departments. Master data has low volatility and changes infrequently (quarterly or annually), providing stable reference points for transactional systems.

**Key Relationships:**
- Provides reference data for ALL other modules
- Central to data integrity and consistency
- No dependencies on other modules (foundational)

### Tables in Master Data:

#### 1. `companies`
**Description:** Stores information about the company or group of companies operating the GenIMS system. This is the highest level of the organizational hierarchy. Each company represents a legal entity that may own multiple factories, warehouses, and employ staff. The company table contains legal details, registration numbers, tax identifiers, and financial year definitions that apply across all operations of that company.

**Key Relationships:**
- Parent table for: factories, warehouses, employees
- Used by: All financial and legal reporting modules

#### 2. `factories`
**Description:** Represents physical manufacturing facilities or production plants owned or operated by a company. Each factory is a location where production occurs, containing production lines, machinery, and shop floor operations. Factory records include address, capacity information, operating hours, and operational status. Factories are linked to production work orders, quality inspections, and maintenance activities.

**Key Relationships:**
- Belongs to: companies
- Contains: production_lines, machines
- Related to: work_orders, production_schedules

#### 3. `warehouses`
**Description:** Physical storage facilities for raw materials, work-in-progress inventory, and finished goods. Warehouses can be standalone distribution centers or attached to factories. Each warehouse has a defined layout with zones, aisles, racks, and bin locations for precise inventory positioning. Warehouse records track storage capacity, current utilization, and warehouse management practices (FIFO, LIFO, etc.).

**Key Relationships:**
- Belongs to: companies
- Contains: warehouse_zones, inventory_locations
- Related to: inventory_transactions, receiving_tasks, shipping_tasks

#### 4. `warehouse_zones`
**Description:** Logical or physical divisions within a warehouse for organizing inventory by characteristics such as temperature requirements, product type, velocity (fast/slow moving), or security level. Zones help optimize warehouse operations by grouping similar items and establishing picking strategies. Examples include "Cold Storage Zone", "High-Value Zone", "Bulk Storage Zone".

**Key Relationships:**
- Belongs to: warehouses
- Contains: aisles and storage locations
- Used by: WMS for putaway and picking optimization

#### 5. `suppliers`
**Description:** External business entities that provide raw materials, components, services, or equipment to the company. Supplier records maintain comprehensive information including contact details, payment terms, quality ratings, lead times, certifications, and performance history. Suppliers are critical to procurement and supply chain management.

**Key Relationships:**
- Related to: purchase_orders, supplier_contracts, supplier_quality_metrics
- Receives: RFQs, purchase orders
- Provides: materials, components

#### 6. `customers`
**Description:** External business entities or individuals that purchase products or services from the company. Customer records contain contact information, credit terms, pricing agreements, delivery preferences, and relationship history. Customers are central to sales, order management, and customer service operations.

**Key Relationships:**
- Related to: sales_orders, quotes, service_tickets, customer_complaints
- Source of: demand, revenue
- Receives: products, invoices, shipments

#### 7. `materials`
**Description:** Raw materials, components, sub-assemblies, and consumables used in manufacturing processes. Each material record defines specifications, units of measure, standard costs, lead times, preferred suppliers, storage requirements, and inventory control parameters (reorder points, safety stock). Materials are consumed in production to create products.

**Key Relationships:**
- Used in: BOMs (bill_of_materials)
- Consumed by: production processes (work_orders)
- Tracked in: inventory_transactions
- Purchased via: purchase_orders
- Supplied by: suppliers

#### 8. `products`
**Description:** Finished goods or sellable items manufactured or distributed by the company. Product records define specifications, pricing, production routings, quality standards, packaging requirements, and sales information. Products are the output of manufacturing processes and the subject of sales transactions.

**Key Relationships:**
- Defined by: BOMs (what materials make this product)
- Produced by: work_orders
- Sold via: sales_orders
- Stored in: warehouses as finished goods inventory

#### 9. `bill_of_materials` (BOMs)
**Description:** Hierarchical definition of all materials, components, and sub-assemblies required to manufacture one unit of a product. BOMs specify quantities, relationships (parent-child), sequence, and alternative components. BOMs are the recipe for production and drive material requirements planning (MRP), costing, and production scheduling.

**Key Relationships:**
- Defines: product composition (product → materials)
- Used by: MRP, production planning, costing
- Drives: material requirements and procurement

#### 10. `bom_components`
**Description:** Individual line items within a BOM that specify each material or sub-assembly required, including the quantity needed per parent unit, sequence of assembly, and optional/alternative component indicators. This table implements the many-to-many relationship between BOMs and materials.

**Key Relationships:**
- Belongs to: bill_of_materials
- References: materials
- Defines: parent-child relationships in product structure

#### 11. `employees`
**Description:** Individual workers employed by the company including production operators, supervisors, engineers, administrators, and management. Employee records contain personal details, employment terms, skills, certifications, shift assignments, and access permissions. Employees execute work orders, perform quality inspections, and operate equipment.

**Key Relationships:**
- Belongs to: companies, departments
- Performs: work_orders, quality_inspections, maintenance tasks
- Subject of: HCM data (attendance, payroll, performance)

#### 12. `departments`
**Description:** Organizational units within the company that group employees by function such as Production, Quality, Maintenance, Procurement, Sales, Finance, etc. Departments establish reporting hierarchies, cost centers for accounting, and workflow routing. Each department may have specific responsibilities, budgets, and performance metrics.

**Key Relationships:**
- Contains: employees
- Associated with: cost_centers (financial)
- Owns: processes, responsibilities

#### 13. `production_lines`
**Description:** Sequences of machines and workstations configured to manufacture specific products or product families. Production lines define the flow of materials through manufacturing processes, cycle times, capacity, and staffing requirements. Lines can be dedicated (single product) or flexible (multiple products with changeovers).

**Key Relationships:**
- Located in: factories
- Contains: machines, workstations
- Executes: work_orders
- Measured by: OEE (Overall Equipment Effectiveness)

#### 14. `machines`
**Description:** Individual pieces of production equipment, machine tools, or automation systems used in manufacturing. Machine records track specifications, capabilities, capacity, maintenance schedules, operating status, and performance metrics. Machines are the physical assets that transform materials into products.

**Key Relationships:**
- Located on: production_lines, factories
- Executes: production operations
- Subject of: CMMS (maintenance), downtime tracking
- Produces: output measured in OEE

#### 15. `material_suppliers`
**Description:** Junction table establishing many-to-many relationships between materials and suppliers, indicating which suppliers can provide specific materials. Includes supplier-specific details such as supplier part numbers, lead times, minimum order quantities, and pricing for each material-supplier combination.

**Key Relationships:**
- Links: materials ↔ suppliers
- Used by: procurement for supplier selection
- Supports: multi-sourcing strategies

---

## MODULE 2: CRM (CUSTOMER RELATIONSHIP MANAGEMENT)

**Module Description:**
The CRM module manages the complete customer lifecycle from initial lead capture through opportunity management, quoting, order fulfillment, and ongoing relationship maintenance. It tracks all customer interactions, manages the sales pipeline, forecasts revenue, and provides visibility into customer behavior and preferences. The CRM system integrates with marketing, sales, and customer service to provide a 360-degree view of each customer relationship.

**Key Relationships:**
- Depends on: Master Data (customers, products)
- Feeds into: ERP (sales orders), Customer Service (service tickets)
- Provides: sales pipeline, customer intelligence

### Tables in CRM:

#### 1. `leads`
**Description:** Potential customers or business opportunities identified through marketing campaigns, trade shows, referrals, or inbound inquiries. Leads represent unqualified prospects that require nurturing and qualification before becoming opportunities. Lead records track source, contact information, interest level, lead score, and qualification status.

**Key Relationships:**
- Converts to: opportunities (when qualified)
- Assigned to: employees (sales reps)
- Source of: sales pipeline

#### 2. `opportunities`
**Description:** Qualified sales prospects with identified needs, budget, timeline, and decision-making authority. Opportunities represent potential revenue that progresses through defined sales stages (prospect → qualify → propose → negotiate → close). Each opportunity tracks estimated value, probability of winning, expected close date, and competitive information.

**Key Relationships:**
- Originated from: leads (qualified leads)
- Generates: quotes, sales_orders
- Owned by: employees (sales reps)
- Tracked through: sales_stages

#### 3. `sales_stages`
**Description:** Standardized steps in the sales process that opportunities progress through, such as "Initial Contact", "Needs Analysis", "Proposal Sent", "Negotiation", "Closed Won", "Closed Lost". Each stage has defined entry/exit criteria, typical duration, and probability of closure. Stages provide structure to the sales process and enable pipeline forecasting.

**Key Relationships:**
- Defines: sales process workflow
- Applied to: opportunities
- Drives: sales forecasting and pipeline management

#### 4. `quotes`
**Description:** Formal price proposals provided to customers for specific products or services. Quotes include itemized pricing, terms and conditions, validity period, delivery timelines, and special provisions. Quotes can be versioned (revised quotes) and tracked through approval workflows. Accepted quotes convert to sales orders.

**Key Relationships:**
- Generated from: opportunities
- References: products, customers
- Converts to: sales_orders (when accepted)
- Contains: quote_line_items

#### 5. `quote_line_items`
**Description:** Individual products or services included in a quote with specific quantities, unit prices, discounts, and line-level notes. Line items allow for complex quotes with multiple products, bundle pricing, and tiered discounts.

**Key Relationships:**
- Belongs to: quotes
- References: products
- Becomes: sales_order_lines (when quote accepted)

#### 6. `sales_orders`
**Description:** Confirmed customer purchase commitments that authorize the company to manufacture and deliver specified products. Sales orders are the contract between customer and company, defining what will be delivered, when, at what price, and under what terms. Sales orders trigger production planning, inventory allocation, and revenue recognition.

**Key Relationships:**
- Originates from: quotes, opportunities
- Belongs to: customers
- Triggers: work_orders (production), shipments (delivery)
- Generates: invoices (billing), revenue (financial)

#### 7. `sales_order_lines`
**Description:** Individual line items within a sales order specifying product, quantity, price, delivery date, and shipping instructions. Order lines track fulfillment status, allocated inventory, production status, and delivery confirmation.

**Key Relationships:**
- Belongs to: sales_orders
- References: products
- Allocates: inventory
- Fulfilled by: shipments

#### 8. `customer_contacts`
**Description:** Individual people within customer organizations who serve as points of contact for sales, technical support, billing, or management. Contact records include names, roles, contact preferences, decision-making authority, and relationship history. Multiple contacts may exist for a single customer account.

**Key Relationships:**
- Belongs to: customers
- Participates in: opportunities, interactions
- Receives: communications, quotes

#### 9. `customer_interactions`
**Description:** Log of all touchpoints between the company and customers including phone calls, emails, meetings, demonstrations, and site visits. Interactions capture date, type, participants, discussion topics, outcomes, and follow-up actions. This history provides context for relationship management and service delivery.

**Key Relationships:**
- Associated with: customers, opportunities, sales_orders
- Performed by: employees
- Tracks: relationship history

#### 10. `customer_segments`
**Description:** Classification scheme for grouping customers by shared characteristics such as industry, size, geography, buying behavior, or value. Segments enable targeted marketing, differentiated service levels, and strategic account management. Examples include "Enterprise Automotive", "Small Manufacturers", "Government".

**Key Relationships:**
- Categorizes: customers
- Drives: marketing strategies, pricing policies
- Influences: service levels

#### 11. `sales_territories`
**Description:** Geographic or account-based regions assigned to sales representatives for coverage and accountability. Territories ensure balanced workload distribution, eliminate coverage gaps, and clarify account ownership. Territory definitions include geographic boundaries, account lists, and performance targets.

**Key Relationships:**
- Contains: customers, opportunities
- Assigned to: employees (sales reps)
- Measures: sales performance by region

#### 12. `sales_forecasts`
**Description:** Projected future sales revenue based on pipeline opportunities, historical trends, seasonality, and market conditions. Forecasts are typically generated monthly or quarterly and track expected revenue by product, customer, territory, or time period. Forecasts drive production planning, inventory decisions, and financial planning.

**Key Relationships:**
- Based on: opportunities (pipeline)
- Informs: production planning, financial budgets
- Compared to: actual sales_orders (accuracy tracking)

#### 13. `campaigns`
**Description:** Organized marketing initiatives designed to generate leads, build awareness, or drive sales. Campaigns include email marketing, trade shows, webinars, advertising, and direct mail. Each campaign tracks budget, target audience, execution timeline, lead generation, and ROI.

**Key Relationships:**
- Generates: leads
- Targets: customer_segments
- Measures: marketing effectiveness

#### 14. `campaign_responses`
**Description:** Individual responses or engagements from prospects or customers to marketing campaigns. Responses track who responded, when, response type (clicked, registered, attended), and conversion to leads. This data measures campaign effectiveness and lead quality.

**Key Relationships:**
- Belongs to: campaigns
- Generates: leads
- Measures: campaign performance

#### 15. `sales_activities`
**Description:** Individual tasks and actions performed by sales representatives such as calls, emails, proposals, demos, and negotiations. Activities track what was done, when, outcome, and next steps. Activity tracking ensures systematic follow-up and provides visibility into sales effort.

**Key Relationships:**
- Associated with: opportunities, leads, customers
- Performed by: employees (sales reps)
- Tracks: sales process execution

#### 16. `competitor_analysis`
**Description:** Intelligence about competing companies including their products, pricing, strengths, weaknesses, market positioning, and win/loss data. Competitive analysis helps refine value propositions, pricing strategies, and sales tactics.

**Key Relationships:**
- Referenced in: opportunities (competitive threats)
- Informs: pricing, positioning
- Tracks: win/loss reasons

#### 17. `pricing_rules`
**Description:** Automated or manual pricing guidelines that determine product prices based on factors such as customer segment, order quantity, contract terms, or competitive conditions. Rules can specify list prices, discount percentages, volume breaks, and approval requirements for deviations.

**Key Relationships:**
- Applied to: quotes, sales_orders
- Varies by: customer_segments, products
- Enforces: pricing policies

#### 18. `customer_agreements`
**Description:** Formal contracts or service agreements between the company and customers establishing terms for pricing, volume commitments, service levels, payment terms, and contract duration. Agreements may include framework contracts, blanket orders, or multi-year commitments.

**Key Relationships:**
- Belongs to: customers
- Governs: sales_orders, pricing
- Defines: relationship terms

---

## MODULE 3: CUSTOMER SERVICE

**Module Description:**
The Customer Service module manages post-sale customer support including issue tracking, service request management, warranty claims, returns, and service level agreement (SLA) monitoring. The system provides a structured workflow for receiving, prioritizing, assigning, and resolving customer issues while maintaining complete history and ensuring timely response. Integration with QMS enables quality issues to be escalated to formal complaint management and corrective action processes.

**Key Relationships:**
- Depends on: Master Data (customers, products), CRM (customer history)
- Feeds into: QMS (customer complaints), WMS (returns)
- Provides: customer satisfaction data, service metrics

### Tables in Customer Service:

#### 1. `service_tickets`
**Description:** Individual customer support requests, issues, or inquiries logged by customers or on behalf of customers. Each ticket represents a single unit of work for the service team with defined priority, status, and resolution timeline. Tickets track the complete lifecycle from creation through investigation, resolution, and closure with full audit trail.

**Key Relationships:**
- Belongs to: customers
- May reference: products, sales_orders
- Assigned to: employees (service reps)
- Can escalate to: customer_complaints (QMS)

#### 2. `ticket_types`
**Description:** Classification scheme for categorizing service tickets by nature of the issue such as "Technical Support", "Warranty Claim", "Product Defect", "How-To Question", "Billing Issue", "Return Request". Types enable routing to appropriate teams, SLA assignment, and trend analysis.

**Key Relationships:**
- Categorizes: service_tickets
- Determines: routing, SLA requirements
- Enables: trend analysis by issue type

#### 3. `service_level_agreements` (SLAs)
**Description:** Formal commitments defining expected response and resolution times for customer issues based on priority and customer tier. SLAs specify first response time (e.g., 1 hour for critical issues), resolution time (e.g., 24 hours for high priority), and escalation procedures when SLAs are at risk of breach.

**Key Relationships:**
- Applies to: service_tickets based on priority/customer
- Measures: service team performance
- Triggers: escalations when breached

#### 4. `ticket_interactions`
**Description:** Chronological log of all communications and actions taken on a service ticket including customer calls, emails, internal notes, status updates, and attachments. Interactions provide complete context for issue resolution and maintain audit trail of service delivery.

**Key Relationships:**
- Belongs to: service_tickets
- Performed by: employees or customers
- Documents: resolution process

#### 5. `knowledge_base_articles`
**Description:** Repository of solutions, troubleshooting guides, FAQs, and best practices that help resolve common customer issues. Articles can be searched and linked to tickets, reducing resolution time and enabling customer self-service. Article effectiveness is measured by usage and customer ratings.

**Key Relationships:**
- Referenced by: service_tickets (as solutions)
- Created from: resolved tickets (lessons learned)
- Enables: self-service, faster resolution

#### 6. `warranty_claims`
**Description:** Customer requests for repair or replacement of defective products covered under warranty. Claims track the defective product, failure description, warranty coverage determination, approval process, replacement/repair actions, and costs. Warranty data informs product quality and cost analysis.

**Key Relationships:**
- Associated with: service_tickets, customers, products
- May trigger: returns (RMA), customer_complaints
- Tracked in: quality costs

#### 7. `return_merchandise_authorizations` (RMAs)
**Description:** Authorization for customers to return products for credit, replacement, or repair. RMAs specify return reason, condition requirements, return shipping instructions, and disposition (credit, replace, scrap). RMAs integrate with WMS for receiving and QMS for quality analysis.

**Key Relationships:**
- Generated from: service_tickets, warranty_claims
- Triggers: warehouse receiving (WMS)
- May create: customer_complaints (QMS) if quality issue

#### 8. `service_feedback`
**Description:** Customer satisfaction ratings and comments collected after ticket resolution. Feedback measures service quality via metrics like CSAT (Customer Satisfaction Score), NPS (Net Promoter Score), and qualitative comments. Feedback drives service improvement and agent coaching.

**Key Relationships:**
- Associated with: service_tickets, employees
- Measures: customer satisfaction, agent performance
- Informs: service improvement initiatives

#### 9. `escalations`
**Description:** Process for elevating unresolved or high-severity issues to higher levels of support or management. Escalations track escalation path, responsible parties, escalation reasons, and resolution actions. Proper escalation ensures critical issues receive appropriate attention.

**Key Relationships:**
- Associated with: service_tickets
- Routes to: senior employees, managers
- Triggered by: SLA breaches, severity, customer importance

#### 10. `service_contracts`
**Description:** Agreements between company and customer for extended support, maintenance services, or premium service levels beyond standard warranty. Contracts specify coverage terms, service level commitments, pricing, and renewal conditions.

**Key Relationships:**
- Belongs to: customers
- Governs: service_tickets (determines SLA, coverage)
- Generates: recurring revenue

#### 11. `product_recalls`
**Description:** Formal actions to retrieve products from customers due to safety issues, regulatory violations, or serious quality defects. Recalls track affected product batches, customer notification, return logistics, corrective actions, and regulatory reporting. Recalls are high-priority quality events.

**Key Relationships:**
- Affects: products, customers, sales_orders
- Creates: mass RMAs, service_tickets
- Requires: customer_complaints, NCRs (QMS)

#### 12. `customer_feedback`
**Description:** Broader customer input beyond specific tickets including product feedback, feature requests, usability observations, and general satisfaction. Feedback is analyzed for trends, prioritized, and routed to appropriate teams (product management, quality, sales) for action.

**Key Relationships:**
- Provided by: customers
- Analyzed for: product improvements, quality issues
- Routes to: product management, quality, engineering

---

## MODULE 4: HCM (HUMAN CAPITAL MANAGEMENT)

**Module Description:**
The Human Capital Management module handles all aspects of workforce management including employee records, organizational structure, time and attendance, leave management, training and development, performance management, and payroll. The system maintains comprehensive employee data from hire through retirement, supports workforce planning, ensures labor compliance, and provides analytics for human resource decisions. HCM integrates with production systems to track labor costs and productivity.

**Key Relationships:**
- Depends on: Master Data (employees, departments)
- Feeds into: Financial (payroll costs), MES (labor tracking)
- Provides: workforce data, labor costs

### Tables in HCM:

#### 1. `employee_details`
**Description:** Comprehensive personal and employment information for each worker including biographical data, emergency contacts, employment history, compensation, benefits enrollment, and employment status. This is the single source of truth for all employee-related data.

**Key Relationships:**
- Extends: employees (master data)
- Referenced by: all HCM tables, payroll
- Used by: MES (labor tracking), CMMS (maintenance assignments)

#### 2. `employment_history`
**Description:** Historical record of an employee's positions, promotions, transfers, and role changes within the company. History tracks dates, positions, departments, reasons for changes, and salary adjustments. Provides audit trail and career progression visibility.

**Key Relationships:**
- Belongs to: employees
- Tracks: career progression, organizational changes
- Used for: succession planning, compliance

#### 3. `attendance_records`
**Description:** Daily records of employee time worked, including clock-in/clock-out times, breaks, shift assignments, and attendance status (present, absent, late). Attendance data drives payroll, identifies attendance issues, and measures labor utilization.

**Key Relationships:**
- Belongs to: employees
- Feeds: payroll calculations
- Integrates with: time_entries, shift_schedules

#### 4. `time_entries`
**Description:** Detailed tracking of hours worked by employees, categorized by project, work order, department, or activity. Time entries enable accurate job costing, labor allocation to production orders, and productivity analysis. Entries can be manual or automatically captured from time clocks.

**Key Relationships:**
- Belongs to: employees
- Allocated to: work_orders (MES), projects, cost_centers
- Drives: labor costing, payroll

#### 5. `leave_requests`
**Description:** Employee requests for time off including vacation, sick leave, personal days, unpaid leave, or other absence types. Requests flow through approval workflow, track leave balance consumption, and integrate with attendance and scheduling systems.

**Key Relationships:**
- Submitted by: employees
- Approved by: managers (employees)
- Affects: attendance_records, shift_schedules
- Tracks: leave balances

#### 6. `leave_balances`
**Description:** Current available and accrued leave balances for each employee by leave type (vacation, sick, etc.). Balances are calculated based on accrual rules, leave taken, and policy limits. Provides real-time visibility into leave entitlements.

**Key Relationships:**
- Belongs to: employees
- Adjusted by: leave_requests (when approved)
- Governed by: leave policies

#### 7. `training_programs`
**Description:** Catalog of available training courses, certifications, and development programs offered to employees. Programs include objectives, duration, prerequisites, cost, delivery method (classroom, online, on-the-job), and competencies developed.

**Key Relationships:**
- Attended by: employees (via training_records)
- Develops: skills, certifications
- Required for: certain roles, compliance

#### 8. `training_records`
**Description:** Individual records of training attended by employees including course name, date completed, score/result, certifications earned, and expiration dates. Training records demonstrate competency, support compliance, and guide development planning.

**Key Relationships:**
- Belongs to: employees, training_programs
- Proves: skills, certifications, compliance
- Triggers: retraining when certifications expire

#### 9. `performance_reviews`
**Description:** Periodic (typically annual or semi-annual) formal evaluations of employee performance against goals and competencies. Reviews include ratings, strengths, areas for improvement, development plans, and compensation recommendations. Reviews support talent management and career development.

**Key Relationships:**
- Evaluates: employees
- Conducted by: managers (employees)
- Informs: compensation decisions, promotions
- Creates: development plans

#### 10. `employee_goals`
**Description:** Specific, measurable objectives set for individual employees aligned with departmental and organizational goals. Goals include targets, timelines, measurement criteria, and achievement status. Goal tracking supports performance management and strategic alignment.

**Key Relationships:**
- Belongs to: employees
- Evaluated in: performance_reviews
- Aligned with: department/company objectives

#### 11. `skills_matrix`
**Description:** Comprehensive catalog of skills, competencies, and certifications relevant to the organization including technical skills, soft skills, equipment operation, quality certifications, etc. The matrix defines proficiency levels and requirements by role.

**Key Relationships:**
- Acquired by: employees (via employee_skills)
- Required by: roles, work_orders
- Developed through: training_programs

#### 12. `employee_skills`
**Description:** Mapping of which skills each employee possesses along with proficiency levels (beginner, intermediate, expert) and certification dates. Enables skills-based work assignment, identifies training gaps, and supports succession planning.

**Key Relationships:**
- Links: employees ↔ skills_matrix
- Used for: work assignment, training planning
- Validated by: training_records, certifications

#### 13. `payroll_data`
**Description:** Compensation information for employees including base salary, overtime, bonuses, deductions, taxes, and net pay. Payroll data is calculated from attendance, time entries, and pay rules, then used to generate paychecks and financial reporting.

**Key Relationships:**
- Calculated for: employees
- Based on: attendance_records, time_entries
- Posted to: financial GL (labor costs)

#### 14. `benefits_enrollment`
**Description:** Employee selections for company-provided benefits such as health insurance, retirement plans, life insurance, and other perks. Enrollment tracks plan choices, coverage levels, dependent information, and enrollment dates.

**Key Relationships:**
- Belongs to: employees
- References: benefits_plans
- Drives: payroll deductions

#### 15. `benefits_plans`
**Description:** Catalog of benefit offerings available to employees including plan details, eligibility requirements, cost, coverage levels, and enrollment periods. Plans may vary by employee category or location.

**Key Relationships:**
- Offered to: employees
- Selected in: benefits_enrollment
- Varies by: employee category, location

#### 16. `shift_schedules`
**Description:** Planned work schedules defining which employees work which shifts on specific dates. Schedules balance labor needs with employee availability, accommodate skill requirements, and ensure proper coverage. Used for production planning and labor cost forecasting.

**Key Relationships:**
- Assigns: employees to shifts/dates
- Considers: leave_requests, skills required
- Drives: attendance tracking, labor planning

#### 17. `employee_certifications`
**Description:** Official certifications, licenses, and credentials held by employees such as forklift operation, quality auditor, welding certification, etc. Certifications have issue dates, expiration dates, and renewal requirements. Certain work may require specific certifications.

**Key Relationships:**
- Held by: employees
- Required for: certain work_orders, equipment operation
- Obtained through: training_programs
- Triggers: retraining when expiring

#### 18. `disciplinary_actions`
**Description:** Formal records of employee performance or conduct issues including verbal warnings, written warnings, suspensions, or terminations. Actions document incidents, corrective expectations, and outcomes. Provides legal protection and guides progressive discipline.

**Key Relationships:**
- Associated with: employees
- Issued by: managers, HR
- Used for: performance management, legal compliance

#### 19. `employee_documents`
**Description:** Repository of employee-related documents such as resumes, offer letters, contracts, performance reviews, I-9 forms, tax forms, and separation documents. Maintains secure document storage with version control and audit trail.

**Key Relationships:**
- Belongs to: employees
- Includes: contracts, reviews, compliance documents
- Required for: legal compliance, audits

#### 20. `succession_plans`
**Description:** Strategic planning for key positions identifying potential successors, readiness levels, development needs, and succession timelines. Plans ensure business continuity and guide talent development for critical roles.

**Key Relationships:**
- Identifies: key positions, potential successors (employees)
- Informs: training_programs, career development
- Supports: organizational resilience

#### 21. `employee_surveys`
**Description:** Periodic assessments of employee satisfaction, engagement, culture, and opinions. Surveys collect feedback on various topics (compensation, management, work environment) and provide insights for HR and management action.

**Key Relationships:**
- Completed by: employees
- Analyzes: engagement, satisfaction, culture
- Drives: HR initiatives, organizational improvements

#### 22. `compensation_history`
**Description:** Historical record of all salary changes, raises, bonuses, and compensation adjustments for each employee. Tracks effective dates, amounts, reasons (merit, promotion, market adjustment), and approval chain. Supports equity analysis and budgeting.

**Key Relationships:**
- Belongs to: employees
- Reflects: performance_reviews, promotions
- Used for: budget planning, equity analysis

---

## MODULE 5: ERP CORE

**Module Description:**
The ERP (Enterprise Resource Planning) Core module is the central transactional system managing procurement, sales, inventory, production planning, and order fulfillment. It orchestrates the flow of materials and information from supplier orders through production to customer delivery. ERP maintains real-time inventory positions, automates material requirements planning (MRP), manages warehouse operations, and coordinates shipping. This module is the operational backbone connecting suppliers, internal operations, and customers.

**Key Relationships:**
- Depends on: Master Data (materials, products, suppliers, customers)
- Integrates with: MES (production), WMS (warehouse), TMS (shipping), Financial (accounting)
- Provides: operational data, inventory positions, order status

### Tables in ERP Core:

#### 1. `purchase_orders`
**Description:** Formal procurement documents authorizing suppliers to deliver specified materials at agreed prices and terms. Purchase orders (POs) are generated from purchase requisitions, RFQs, or automated MRP runs. POs track order status from creation through receipt, quality inspection, and invoice payment. POs are legally binding commitments.

**Key Relationships:**
- Issued to: suppliers
- Orders: materials
- Generated from: purchase_requisitions, RFQs, MRP
- Received via: receiving_tasks (WMS)
- Invoiced via: supplier_invoices

#### 2. `purchase_order_lines`
**Description:** Individual line items within a purchase order specifying material, quantity, unit price, delivery date, and receiving location. Lines track receipt status, quality inspection results, and invoice matching. Partial receipts and over/under deliveries are managed at line level.

**Key Relationships:**
- Belongs to: purchase_orders
- Specifies: materials, quantities, prices
- Tracked by: receiving_task_lines (WMS)
- Matched in: supplier_invoices (3-way matching)

#### 3. `sales_orders` (extends CRM)
**Description:** In the ERP context, sales orders are operational fulfillment documents (whereas in CRM they represent the customer commitment). ERP sales orders trigger production planning, inventory allocation, and shipping. They track production status, inventory reservation, pick/pack/ship operations, and delivery confirmation.

**Key Relationships:**
- Originated in: CRM
- Triggers: work_orders (MES), inventory allocation
- Fulfilled via: shipments (TMS)
- Invoiced via: customer_invoices
- Updates: revenue recognition (Financial)

#### 4. `sales_order_lines` (extends CRM)
**Description:** From an ERP perspective, SO lines track fulfillment details including inventory allocation, production status, pick status, pack status, and shipped quantity. Lines link to work orders, shipments, and invoices for complete order-to-cash visibility.

**Key Relationships:**
- Belongs to: sales_orders
- Allocates: inventory (on-hand or planned)
- Triggers: work_orders if make-to-order
- Fulfilled via: shipping_task_lines (WMS)
- Invoiced via: invoice_lines (Financial)

#### 5. `inventory_transactions`
**Description:** Comprehensive log of all inventory movements including receipts, issues, transfers, adjustments, and cycle count corrections. Each transaction records material, quantity, from/to locations, transaction type, reason code, transaction date, and user. Transactions provide complete inventory audit trail and drive inventory valuation.

**Key Relationships:**
- Affects: materials, warehouses, inventory_locations
- Generated by: receiving, picking, production, adjustments
- Syncs with: WMS (via ERP-WMS sync)
- Posts to: GL for inventory valuation (Financial)

#### 6. `inventory_locations`
**Description:** Specific storage positions within warehouses identified by warehouse, zone, aisle, rack, and bin coordinates. Locations track current inventory on-hand by material, lot, and serial number. Supports bin-level accuracy and directed putaway/picking.

**Key Relationships:**
- Located in: warehouses, warehouse_zones
- Contains: materials (inventory)
- Used by: WMS for putaway/picking
- Synchronized with: ERP inventory positions

#### 7. `inventory_on_hand`
**Description:** Current quantity of each material available in each location. Represents the aggregated, real-time inventory position used for Available-to-Promise (ATP) calculations, MRP planning, and allocation decisions. Updated by all inventory transactions.

**Key Relationships:**
- Aggregates: inventory_transactions
- Tracked by: material, warehouse, location, lot
- Used for: ATP, MRP, allocation
- Synchronized with: WMS snapshots

#### 8. `inventory_allocations`
**Description:** Reservations of inventory for specific sales orders, work orders, or other demands. Allocations "earmark" inventory so it's not available for other purposes. Tracks allocated quantity, source (sales order/work order), and allocation date. Prevents overselling and ensures promised delivery.

**Key Relationships:**
- Reserves: inventory_on_hand
- For: sales_orders, work_orders
- Consumed by: picking operations (WMS)
- Synced with: WMS bin reservations

#### 9. `receiving_tasks` (WMS integration)
**Description:** Warehouse receiving operations for inbound materials from suppliers or production. Tasks track expected receipts, actual quantities received, quality inspection status, and putaway completion. Links purchase orders to physical inventory receipt.

**Key Relationships:**
- Receives against: purchase_orders
- Creates: inventory_transactions (receipt)
- Triggers: quality_inspections
- Completes: putaway_tasks

#### 10. `putaway_tasks` (WMS integration)
**Description:** Warehouse operations to move received materials from receiving dock to storage locations. Tasks specify material, quantity, source location (staging), destination location (storage), and putaway strategy (FIFO, FEFO, directed). Completion updates inventory locations.

**Key Relationships:**
- Follows: receiving_tasks
- Moves: materials to inventory_locations
- Creates: inventory_transactions (transfer)
- Updates: inventory_on_hand by location

#### 11. `picking_tasks` (WMS integration)
**Description:** Warehouse operations to retrieve materials from storage for production or shipping. Tasks specify what to pick, from which locations, in what sequence, and quantity. Picking strategies include wave picking, batch picking, and zone picking. Completion allocates inventory to destination.

**Key Relationships:**
- Fulfills: sales_orders, work_orders (material issues)
- Picks from: inventory_locations
- Creates: inventory_transactions (issue)
- Reduces: inventory_on_hand

#### 12. `shipping_tasks` (WMS integration)
**Description:** Warehouse operations to pack and load orders for shipment to customers. Tasks consolidate picked items, generate packing lists, assign carriers, print labels, and confirm loading. Completion updates order fulfillment status.

**Key Relationships:**
- Fulfills: sales_orders
- Follows: picking_tasks
- Creates: shipments (TMS)
- Confirms: delivery initiation

#### 13. `stock_transfers`
**Description:** Movement of inventory between warehouses, between factories, or between locations within a warehouse. Transfers maintain inventory custody and traceability during inter-site moves. Includes transfer orders, in-transit inventory, and receipt confirmation.

**Key Relationships:**
- Moves: materials between warehouses/locations
- Creates: inventory_transactions (issue and receipt)
- Tracks: in-transit inventory
- Used for: rebalancing inventory

#### 14. `cycle_counts`
**Description:** Regular physical inventory verification programs where portions of inventory are counted on rotating schedules. Cycle counts replace annual physical inventories, maintain accuracy, and identify systemic issues. Counts compare physical vs system quantities and generate adjustments.

**Key Relationships:**
- Counts: inventory_on_hand by location
- Generates: inventory_adjustments (discrepancies)
- Integrated with: WMS cycle count programs
- Measures: inventory accuracy

#### 15. `inventory_adjustments`
**Description:** Corrections to inventory records for errors, damages, shrinkage, obsolescence, or cycle count discrepancies. Adjustments document reason, authority, quantity change, and financial impact. Each adjustment creates inventory transaction and GL posting for inventory value change.

**Key Relationships:**
- Corrects: inventory_on_hand
- Created by: cycle_counts, physical audits, damages
- Creates: inventory_transactions
- Posts to: GL (inventory variance accounts)

#### 16. `material_requirements_planning` (MRP runs)
**Description:** Automated calculation of material needs based on sales orders, production forecasts, current inventory, open purchase orders, and lead times. MRP generates planned purchase orders and production orders to meet demand while minimizing inventory. Runs periodically (daily/weekly).

**Key Relationships:**
- Analyzes: sales_orders, forecasts, BOMs, inventory
- Generates: planned_orders (purchase and production)
- Considers: lead_times, safety_stock, lot sizes
- Drives: procurement, production planning

#### 17. `planned_orders`
**Description:** MRP-generated recommendations to purchase or produce materials to meet future demand. Planned orders are suggestions (not commitments) that planners review, adjust, and convert to actual purchase orders or work orders. Include quantity, due date, and source.

**Key Relationships:**
- Generated by: MRP
- Converts to: purchase_orders or work_orders
- Based on: demand, lead times, BOMs
- Reviewed by: planners

#### 18. `safety_stock_levels`
**Description:** Minimum inventory buffers maintained to protect against demand variability, supply disruptions, or lead time uncertainty. Safety stock levels are set by material, location, and replenishment strategy. MRP plans to maintain inventory above safety stock.

**Key Relationships:**
- Set for: materials by location
- Used by: MRP calculations
- Determines: reorder points
- Balances: service level vs inventory cost

#### 19. `reorder_points`
**Description:** Inventory trigger levels that automatically initiate replenishment when on-hand quantity falls below threshold. Reorder points consider lead time demand and safety stock. Used for consumables and continuous replenishment items.

**Key Relationships:**
- Set for: materials
- Calculates from: lead_time, demand_rate, safety_stock
- Triggers: purchase_requisitions or planned_orders
- Maintains: availability

#### 20. `lot_tracking`
**Description:** Traceability system tracking materials by production lot, batch, or serial numbers. Enables forward traceability (where did this lot go?) and backward traceability (where did this come from?). Critical for quality investigations, recalls, and compliance.

**Key Relationships:**
- Tracks: materials by lot/batch
- Recorded in: inventory_transactions
- Used for: recalls, quality investigations
- Required for: regulated industries

#### 21. `serial_number_tracking`
**Description:** Unit-level traceability for individual items identified by unique serial numbers. Tracks each serialized item through receipt, production, storage, and customer delivery. Essential for warranty tracking, service history, and recalls of specific units.

**Key Relationships:**
- Tracks: individual product units
- Recorded in: inventory_transactions, sales_orders
- Enables: warranty tracking, recall precision
- Required for: high-value or regulated products

#### 22. `inventory_reservations`
**Description:** Soft allocations of inventory for anticipated demand such as quotes, forecasted orders, or kit staging. Reservations don't commit inventory but flag it as potentially needed, helping planners understand total demand picture.

**Key Relationships:**
- Reserves: inventory_on_hand (soft hold)
- For: quotes, forecasts, staging
- Converts to: allocations when firm orders received
- Informs: ATP calculations

#### 23. `backorders`
**Description:** Sales order lines that cannot be fulfilled immediately due to insufficient inventory. Backorders track unfulfilled quantity, original promise date, revised promise date, and fulfillment priority. Managed through allocation rules and expediting.

**Key Relationships:**
- Associated with: sales_order_lines
- Caused by: insufficient inventory_on_hand
- Resolved by: replenishment (purchase/production)
- Prioritized for: allocation when stock available

#### 24. `inventory_valuation_methods`
**Description:** Configuration defining how inventory costs are calculated (FIFO, LIFO, Weighted Average, Standard Cost). Method affects financial reporting, profitability analysis, and tax liability. Typically set by location and material category.

**Key Relationships:**
- Applies to: materials, warehouses
- Drives: GL postings, COGS calculations
- Affects: financial statements
- Set per: accounting policies

#### 25. `abc_classification`
**Description:** Categorization of materials by value importance using Pareto principle. 'A' items are high-value (tight control), 'B' items are medium-value (moderate control), 'C' items are low-value (simple control). Drives inventory policies, count frequencies, and stocking strategies.

**Key Relationships:**
- Classifies: materials
- Based on: annual usage value
- Determines: cycle count frequency, safety stock policies
- Optimizes: inventory management effort

#### 26. `demand_forecasts`
**Description:** Predicted future demand for materials and products based on historical sales, market trends, seasonality, and business intelligence. Forecasts drive production planning, procurement, and capacity decisions. Can be statistical, judgmental, or collaborative.

**Key Relationships:**
- Forecasts: materials, products by period
- Feeds: MRP, production planning
- Based on: sales_history, trends, promotions
- Reviewed and adjusted by: planners

#### 27. `shipping_methods`
**Description:** Available transportation options including carriers, service levels (ground, air, overnight), and cost structures. Shipping methods define delivery speeds, geographic coverage, and freight calculations.

**Key Relationships:**
- Selected for: sales_orders, shipments
- Determines: delivery time, freight cost
- Provided by: carriers (TMS)
- Affects: customer satisfaction, logistics cost

#### 28. `incoterms`
**Description:** International commercial terms defining responsibilities for shipping, insurance, customs, and risk transfer between buyer and seller. Common terms include FOB (Free On Board), CIF (Cost Insurance Freight), DDP (Delivered Duty Paid).

**Key Relationships:**
- Applies to: purchase_orders, sales_orders
- Defines: responsibility for freight, risk
- Affects: inventory valuation, freight accrual
- Required for: international transactions

#### 29. `customs_documentation`
**Description:** Records required for international shipments including commercial invoices, packing lists, certificates of origin, and customs declarations. Tracks harmonized tariff codes, duties paid, and regulatory compliance.

**Key Relationships:**
- Required for: international shipments
- References: sales_orders, materials, customers
- Supports: customs clearance
- Archives: compliance documentation

#### 30. `freight_costs`
**Description:** Actual and accrued costs for inbound (from suppliers) and outbound (to customers) transportation. Tracks carrier charges, fuel surcharges, accessorial fees, and customs duties. Used for cost allocation and freight reconciliation.

**Key Relationships:**
- Associated with: purchase_orders, sales_orders, shipments
- Invoiced by: carriers
- Allocated to: orders, products
- Posted to: GL (freight expense/revenue)

#### 31. `inventory_aging`
**Description:** Analysis of how long inventory has been on-hand, typically categorized into age buckets (0-30 days, 31-60 days, 61-90 days, 90+ days). Identifies slow-moving and obsolete inventory for disposition decisions and financial write-downs.

**Key Relationships:**
- Analyzes: inventory_on_hand by receipt date
- Identifies: slow-moving, obsolete inventory
- Drives: disposition decisions, write-offs
- Reports: aging for financial reserves

#### 32. `inventory_velocity`
**Description:** Measurement of how quickly inventory turns over (issues/receipts per period). Velocity classifications (fast/medium/slow) drive storage location assignment, replenishment frequencies, and stocking policies.

**Key Relationships:**
- Measures: materials by turnover rate
- Drives: warehouse slotting, stocking policies
- Identifies: fast vs slow movers
- Optimizes: warehouse efficiency

#### 33. `min_max_inventory_levels`
**Description:** Inventory control parameters defining minimum (trigger reorder) and maximum (order up to) quantities for each material by location. Used in min/max replenishment strategies for continuous availability without excess inventory.

**Key Relationships:**
- Set for: materials by location
- Used by: replenishment logic
- Alternatives to: MRP for simple items
- Balances: service vs inventory cost

#### 34. `vendor_managed_inventory` (VMI)
**Description:** Arrangements where suppliers monitor and replenish inventory at customer locations based on usage visibility. VMI tracks consignment inventory, usage reporting, supplier-triggered replenishment, and periodic settlements.

**Key Relationships:**
- Involves: suppliers managing customer inventory
- Tracks: consignment stock, usage, replenishment
- Transfers: ownership at usage point
- Benefits: reduced inventory, improved availability

#### 35. `consignment_inventory`
**Description:** Materials stored at company facilities but still owned by suppliers until consumed. Consignment tracking monitors quantities on-hand, usage, and periodic settlements with suppliers. Improves cash flow by deferring payment until use.

**Key Relationships:**
- Owned by: suppliers (until consumed)
- Stored in: company warehouses
- Tracked separately from: owned inventory
- Settled periodically with: supplier_invoices

---

*[Note: This completes Modules 1-5. The document continues with the remaining modules 6-14 in the same detailed format. Would you like me to continue with the remaining modules, or would you prefer to proceed to the second document (field-level descriptions)?]*

---


## MODULE 6: FINANCIAL GL (GENERAL LEDGER)

**Module Description:**
The Financial General Ledger module is the core accounting system that records all financial transactions in a double-entry bookkeeping framework. It automatically posts transactions from operational modules (sales, purchases, production, inventory) to the appropriate GL accounts based on configurable posting rules. The system maintains the chart of accounts hierarchy, tracks account balances by period, supports multi-currency operations, manages fiscal periods and year-end closing, and generates financial statements including balance sheet, income statement, and cash flow statement. Integration with operational modules ensures real-time financial visibility and eliminates manual accounting entries.

**Key Relationships:**
- Depends on: All operational modules (ERP, MES, WMS) for transaction data
- Integrates with: ERP-WMS Sync for inventory valuation
- Provides: Financial statements, cost accounting, audit trails

### Tables in Financial GL:

#### 1. `chart_of_accounts`
**Description:** Hierarchical structure of all general ledger accounts organized into categories (Assets, Liabilities, Equity, Revenue, Expenses). Each account has a unique number, name, type, and parent-child relationships enabling roll-up reporting. The chart of accounts is the foundation of financial reporting and cost tracking.

#### 2. `gl_posting_rules`
**Description:** Automated mapping rules that determine which GL accounts to debit and credit for specific transaction types (sales orders, purchase orders, production completion, etc.). Rules eliminate manual journal entries, ensure consistency, and enable real-time financial posting from operational events.

#### 3. `journal_entry_headers`
**Description:** Headers for double-entry accounting transactions that document debits and credits affecting GL accounts. Each journal entry has a unique number, date, source (manual, automated), description, status, and approval workflow. Entries provide complete audit trail of financial activity.

#### 4. `journal_entry_lines`
**Description:** Individual debit and credit lines within journal entries specifying account, amount, cost center, reference document, and narrative. Lines implement double-entry bookkeeping where total debits equal total credits. Lines link operational transactions to financial records.

#### 5. `cost_centers`
**Description:** Organizational units (departments, production lines, projects) used for cost tracking and management reporting. Cost centers enable profit/loss analysis by segment, support activity-based costing, and facilitate budget management at granular levels.

#### 6. `fiscal_years`
**Description:** Annual accounting periods defining company financial years with start/end dates and year-end closing status. Fiscal years may align with calendar years or differ based on business cycles and regulatory requirements.

#### 7. `fiscal_periods`
**Description:** Monthly or quarterly subdivisions of fiscal years used for period-based financial reporting and closing. Periods track open/closed status, control transaction posting dates, and support management reporting cycles.

#### 8. `budget_headers`
**Description:** Annual or multi-year financial plans defining expected revenues and expenses by account and period. Budgets support planning, enable variance analysis, and provide spending controls through budget checking workflows.

#### 9. `budget_lines`
**Description:** Detailed budget allocations by GL account, cost center, and period (monthly). Lines specify planned amounts, enable period-to-period comparisons, and support budget vs actual variance reporting.

#### 10. `account_balances`
**Description:** Pre-calculated running balances for each GL account by fiscal period, optimized for fast financial reporting. Balances aggregate journal entry lines and track beginning balance, period activity, and ending balance.

#### 11. `financial_statements`
**Description:** Structured financial reports including Balance Sheet (assets, liabilities, equity), Income Statement (P&L: revenues, expenses), and Cash Flow Statement. Statements are generated from account balances and conform to accounting standards (GAAP, IFRS).

#### 12. `exchange_rates`
**Description:** Currency conversion rates for multi-currency operations enabling translation of foreign currency transactions to base currency. Rates track date, currency pairs, and rate types (spot, average, period-end).

#### 13. `inter_company_transactions`
**Description:** Financial transactions between related companies within a corporate group. Tracks transfers of goods, services, or funds between legal entities requiring elimination entries in consolidated financial statements.

#### 14. `period_close_tasks`
**Description:** Checklist of procedures required to close each fiscal period including reconciliations, accruals, adjustments, and approvals. Tasks ensure orderly closing process and complete financial records.

#### 15. `gl_audit_trail`
**Description:** Complete history of all changes to financial records including original entry, modifications, who made changes, when, and why. Provides forensic capability for audits, investigations, and compliance.

#### 16. `bank_reconciliations`
**Description:** Process of matching company's cash account records against bank statements to identify discrepancies, timing differences, errors, and unauthorized transactions. Ensures cash balance accuracy.

#### 17. `accruals`
**Description:** Accounting adjustments for expenses incurred but not yet paid (accrued expenses) or revenue earned but not yet received (accrued revenue). Ensures matching principle compliance.

---

## MODULE 7: ERP-WMS INVENTORY SYNC

**Module Description:**
The ERP-WMS Inventory Synchronization module maintains real-time consistency between Enterprise Resource Planning (location-level) and Warehouse Management System (bin-level) inventory data. ERP tracks aggregate inventory by warehouse for planning and allocation, while WMS manages detailed bin locations for physical operations. The sync module bridges these granularities through bidirectional queue-based synchronization with retry logic, variance detection, and automatic reconciliation. This ensures both systems have accurate, consistent inventory positions enabling reliable ATP (Available-to-Promise) and preventing stockouts or overselling.

**Key Relationships:**
- Bridges: ERP (aggregate) ↔ WMS (detailed)
- Enables: Financial inventory valuation accuracy
- Provides: Consolidated inventory view, variance alerts

### Tables in ERP-WMS Sync:

#### 1. `inventory_sync_mappings`
**Description:** Configuration mapping ERP warehouse locations to WMS warehouses and zones establishing the relationship between aggregate (ERP) and detailed (WMS) inventory views. Mappings enable synchronized data interpretation.

#### 2. `inventory_sync_queue`
**Description:** Transactional queue processing real-time inventory movements between ERP and WMS with retry logic for failed syncs. Queue entries track sync direction (ERP→WMS or WMS→ERP), transaction type (allocation, movement, adjustment), status, and retry count.

#### 3. `inventory_allocations`
**Description:** Reservation of inventory for sales orders or production needs that must be synchronized between ERP (order allocation) and WMS (bin reservation). Ensures both systems agree on what's available vs committed.

#### 4. `inventory_reconciliation_headers`
**Description:** Periodic comparison process between ERP and WMS inventory positions to identify discrepancies. Reconciliation sessions generate variance reports categorizing differences by severity (matched, minor, major).

#### 5. `inventory_reconciliation_lines`
**Description:** Line-by-line comparison details showing material, ERP quantity, WMS quantity, variance amount, variance percentage, and classification. Used to investigate and resolve discrepancies.

#### 6. `inventory_adjustments_sync`
**Description:** Synchronization of inventory adjustments (cycle count corrections, damages, write-offs) ensuring both systems reflect physical inventory corrections. Tracks which system originated the adjustment.

#### 7. `cycle_count_integration`
**Description:** WMS-initiated cycle counts that must update ERP inventory when discrepancies are found. Ensures ERP reflects physical counts performed in warehouse.

#### 8. `inventory_snapshot`
**Description:** Consolidated real-time view combining ERP and WMS data showing on-hand, allocated, and available quantities with variance indicators. Provides single source of truth for inventory positions.

#### 9. `inventory_transaction_log`
**Description:** Complete audit trail of all inventory movements across both systems with timestamps, users, reasons, and sync status. Enables traceability and troubleshooting.

#### 10. `inventory_sync_errors`
**Description:** Log of failed sync attempts with error messages, retry attempts, and resolution status. Enables monitoring and troubleshooting of integration issues.

#### 11. `inventory_sync_metrics`
**Description:** Daily performance metrics for sync operations including success rate, average latency, variance counts, and retry statistics. Monitors integration health.

#### 12. `bin_location_mappings`
**Description:** Detailed mapping of WMS bin locations to ERP locations supporting drill-down from aggregate to detailed inventory views for investigation and traceability.

---

## MODULE 8: MES (MANUFACTURING EXECUTION SYSTEM)

**Module Description:**
The Manufacturing Execution System (MES) bridges the gap between ERP planning and shop floor execution by managing real-time production operations. MES tracks work orders from release through completion, records material consumption and labor hours, monitors machine utilization and downtime, enforces production sequences, captures quality inspection results, and calculates Overall Equipment Effectiveness (OEE). The system provides real-time visibility into production status, identifies bottlenecks, ensures quality compliance, and feeds actual data back to ERP for inventory, costing, and planning updates.

**Key Relationships:**
- Executes: work orders from ERP
- Integrates with: WMS (material pulls), QMS (quality), CMMS (maintenance)
- Provides: production actuals, labor data, OEE metrics

### Tables in MES:

#### 1. `work_orders`
**Description:** Production jobs instructing the shop floor to manufacture specified quantities of products. Work orders define what to make, how many, by when, using which BOM and routing. Track status from released → in-progress → completed with actual start/end times.

#### 2. `work_order_operations`
**Description:** Individual manufacturing steps within a work order corresponding to routing operations (machining, assembly, inspection, packaging). Operations track sequence, machine assignment, labor hours, status, and completion.

#### 3. `production_schedules`
**Description:** Time-phased plan assigning work orders to production lines/machines with start and end times. Schedules balance capacity, sequence work for efficiency, and provide shop floor execution plan.

#### 4. `material_consumption`
**Description:** Record of raw materials and components actually consumed in production, compared to planned BOM quantities. Tracks material issues, lot traceability, scrap, and yield variances.

#### 5. `production_output`
**Description:** Finished goods and work-in-progress produced by work orders with quantities, lot numbers, timestamps, and quality status. Output triggers inventory transactions and moves product through production stages.

#### 6. `quality_inspections`
**Description:** Inspection checkpoints within production process verifying conformance to specifications. Records inspection type (first article, in-process, final), characteristics measured, results, pass/fail status, and defect data.

#### 7. `labor_tracking`
**Description:** Actual time spent by employees on work orders and operations. Labor data drives job costing, efficiency measurement, payroll, and capacity analysis. Links to HCM time entries.

#### 8. `machine_utilization`
**Description:** Usage statistics for production equipment showing run time, idle time, setup time, and downtime. Utilization metrics identify capacity constraints and improvement opportunities.

#### 9. `downtime_events`
**Description:** Unplanned stoppages of production equipment or lines with downtime type (breakdown, no material, no operator, changeover), duration, root cause, and resolution. Enables loss analysis and improvement.

#### 10. `oee_metrics`
**Description:** Overall Equipment Effectiveness calculations measuring production efficiency as Availability × Performance × Quality. OEE identifies losses and benchmarks performance against world-class standards (85%+).

#### 11. `production_batches`
**Description:** Grouping of production output into lots for traceability, quality control, and inventory management. Batches track production date, raw material lots consumed, expiration dates, and quality status.

#### 12. `routings`
**Description:** Sequence of operations required to manufacture a product defining the production process flow. Routings specify operations, machines, standard times, and sequence providing the "how to make" instructions.

#### 13. `routing_operations`
**Description:** Individual steps within a routing detailing work centers, setup times, run times, labor requirements, and tooling. Operations drive scheduling, costing, and shop floor instructions.

#### 14. `work_centers`
**Description:** Logical or physical production resources (machines, cells, assembly lines) where operations are performed. Work centers define capacity, shifts, efficiency, and cost rates.

#### 15. `setup_time_tracking`
**Description:** Time required to changeover equipment from one product to another including cleaning, tool changes, and first article approval. Setup time reduction is key lean manufacturing focus.

#### 16. `scrap_tracking`
**Description:** Materials or products rejected during production due to defects, errors, or damage. Scrap tracking quantifies waste by cause, operation, and material for cost visibility and loss reduction.

#### 17. `yield_variance`
**Description:** Difference between planned and actual output accounting for normal scrap, rework, and process losses. Yield variance affects material requirements, costing, and capacity planning.

#### 18. `production_kpi_dashboard`
**Description:** Real-time summary of key performance indicators including OEE, yield, on-time completion, quality defect rate, and throughput. Dashboard provides shop floor visibility and management escalation.

#### 19. `shift_production_summary`
**Description:** Aggregated production results by shift showing work orders completed, quantities produced, downtime, quality issues, and efficiency. Supports shift handovers and daily management.

#### 20. `production_variance`
**Description:** Comparison of planned vs actual for materials consumed, labor hours, production time, and output quantity. Variances drive continuous improvement and validate standard costs.

#### 21. `work_order_status_log`
**Description:** Audit trail of all status changes for work orders (released, started, held, completed, closed) with timestamps and reasons. Provides production execution visibility and metrics.

#### 22. `production_exceptions`
**Description:** Abnormal events during production such as material shortages, quality holds, equipment failures, or safety incidents. Exceptions require resolution before production continues.

#### 23. `standard_work_instructions`
**Description:** Documented procedures for performing operations including setup instructions, operating parameters, safety precautions, and quality checkpoints. Ensures consistent, safe production.

#### 24. `tool_tracking`
**Description:** Management of cutting tools, fixtures, molds, and other tooling used in production. Tracks tool location, usage cycles, wear limits, and replacement schedules.

#### 25. `first_article_inspection`
**Description:** Comprehensive inspection of the first part produced after setup to verify process is capable before full production run. FAI results authorize continued production or require adjustment.

#### 26. `production_capacity_analysis`
**Description:** Calculation of available capacity by work center considering shifts, efficiency, and scheduled downtime. Capacity analysis supports feasibility checking and realistic scheduling.

#### 27. `production_cost_tracking`
**Description:** Accumulation of actual costs (material, labor, overhead) by work order for job costing and profitability analysis. Costs are posted to GL upon work order completion.

#### 28. `production_reporting`
**Description:** Structured reports for management including production volume, efficiency trends, quality metrics, cost performance, and on-time completion rates. Supports performance management and continuous improvement.

---

## MODULE 9: WMS (WAREHOUSE MANAGEMENT SYSTEM)

**Module Description:**
The Warehouse Management System (WMS) optimizes physical warehouse operations through directed putaway, efficient picking strategies, cycle counting, and real-time inventory visibility. WMS manages bin-level inventory accuracy, uses barcoding/RFID for transactions, implements FIFO/FEFO/LIFO logic, supports wave picking and cross-docking, and integrates with material handling equipment. The system maximizes warehouse space utilization, minimizes travel distance, ensures inventory accuracy, and provides real-time status for customer service and planning.

**Key Relationships:**
- Executes: warehouse tasks from ERP orders
- Syncs with: ERP (inventory positions), TMS (shipments)
- Provides: bin-level accuracy, picking efficiency

### Tables in WMS:

#### 1. `warehouse_layout`
**Description:** Physical structure definition of warehouse including zones, aisles, racks, and bins with location coordinates. Layout supports directed putaway/picking and space utilization analysis.

#### 2. `bin_locations`
**Description:** Individual storage positions (bins) within warehouse identified by zone-aisle-rack-bin coordinates. Bins have size specifications, material compatibility, and current occupancy status.

#### 3. `receiving_tasks`
**Description:** Inbound operations receiving materials from suppliers or production. Tasks verify quantities, check quality, generate labels, and stage materials for putaway.

#### 4. `receiving_task_lines`
**Description:** Detail lines for receiving tasks specifying material, expected quantity, received quantity, lot numbers, and discrepancy notes. Lines update inventory upon completion.

#### 5. `putaway_tasks`
**Description:** Movement of received materials from staging to storage locations using directed putaway strategies (fixed locations, random, ABC zones). Tasks optimize space and retrieval efficiency.

#### 6. `putaway_strategies`
**Description:** Rules determining where to store materials considering factors like velocity (fast movers near shipping), product compatibility, lot rotation (FIFO), and space utilization.

#### 7. `picking_tasks`
**Description:** Retrieval of materials from storage for production kits or customer shipments. Picking tasks specify locations, quantities, sequence, and collection methods (piece, case, pallet).

#### 8. `picking_strategies`
**Description:** Methods for efficient order fulfillment including wave picking (batch similar orders), zone picking (pickers stay in zones), and cluster picking (pick multiple orders simultaneously).

#### 9. `packing_tasks`
**Description:** Assembly of picked items into shipping containers with appropriate protection, labeling, and documentation. Packing optimizes carton utilization and ensures damage-free delivery.

#### 10. `shipping_tasks`
**Description:** Final warehouse operations loading packed orders onto carriers with bill of lading generation, seal application, and shipment confirmation. Links to TMS for transportation.

#### 11. `shipping_task_lines`
**Description:** Detail lines for shipping tasks listing each item shipped with quantities, serial numbers, and destination. Lines confirm sales order fulfillment.

#### 12. `wave_picking_batches`
**Description:** Grouping of multiple orders released simultaneously for efficient picking. Waves group orders by zone, route, or priority to optimize picker productivity.

#### 13. `cycle_counts`
**Description:** Ongoing physical count program rotating through warehouse locations to verify inventory accuracy. Counts replace annual physical inventory with frequent partial counts.

#### 14. `cycle_count_results`
**Description:** Comparison of system (expected) vs physical (counted) quantities with variance analysis. Results trigger inventory adjustments when discrepancies exceed tolerance.

#### 15. `physical_inventory_counts`
**Description:** Comprehensive annual counts of all warehouse inventory requiring operations freeze. Used for financial reporting and inventory record correction.

#### 16. `bin_replenishment`
**Description:** Movement of materials from bulk storage to picking faces maintaining adequate forward stock. Replenishment minimizes picker travel and prevents stockouts in pick zones.

#### 17. `cross_dock_operations`
**Description:** Direct transfer of inbound materials to outbound shipments without storage. Cross-docking reduces handling, storage time, and space requirements for fast-moving items.

#### 18. `kitting_tasks`
**Description:** Assembly of component materials into kits for production or customer orders. Kitting pre-stages materials reducing production line downtime and improving quality.

#### 19. `quality_holds`
**Description:** Inventory blocked from use pending quality inspection or disposition decision. Holds prevent shipment or usage of suspect materials until cleared.

#### 20. `damaged_inventory`
**Description:** Tracking of inventory with physical damage, contamination, or defects. Damaged materials are segregated pending disposition (repair, scrap, return to supplier).

#### 21. `warehouse_tasks_assignment`
**Description:** Allocation of warehouse tasks to specific workers or equipment considering skills, workload, and zone assignments. Assignment optimization maximizes throughput.

#### 22. `material_handling_equipment`
**Description:** Forklifts, conveyors, AS/RS systems, and other equipment used in warehouse operations. Tracks equipment status, utilization, and maintenance requirements.

#### 23. `slotting_optimization`
**Description:** Strategic placement of materials in warehouse based on velocity, size, compatibility, and seasonality. Slotting reduces travel distance and improves efficiency.

#### 24. `warehouse_performance_metrics`
**Description:** KPIs measuring warehouse efficiency including picks per hour, putaway accuracy, order cycle time, space utilization, and inventory accuracy. Drives continuous improvement.

---

## MODULE 10: TMS (TRANSPORTATION MANAGEMENT SYSTEM)

**Module Description:**
The Transportation Management System (TMS) optimizes freight operations including carrier selection, route planning, shipment tracking, freight payment, and delivery confirmation. TMS manages outbound shipments to customers and inbound receipts from suppliers, consolidates orders for cost savings, tracks shipments in-transit with real-time visibility, and manages carrier relationships including performance measurement and freight audit. The system reduces transportation costs, improves delivery reliability, and provides customer delivery notifications.

**Key Relationships:**
- Executes: shipments from ERP/WMS
- Manages: carrier relationships, routes
- Provides: delivery tracking, freight costs

### Tables in TMS:

#### 1. `shipments`
**Description:** Individual outbound deliveries to customers or transfers between facilities. Shipments consolidate sales order lines, assign carriers, track delivery status, and confirm proof of delivery.

#### 2. `shipment_lines`
**Description:** Detail lines within shipments specifying items shipped, quantities, weights, dimensions, and handling requirements. Lines link to sales order fulfillment.

#### 3. `carriers`
**Description:** Transportation service providers (trucking, air freight, ocean freight, courier) with capabilities, service areas, and performance ratings. Carriers are selected for shipments based on requirements and performance.

#### 4. `carrier_contracts`
**Description:** Rate agreements with carriers defining pricing by lane (origin-destination), service level, fuel surcharges, and accessorial charges. Contracts enable cost-effective shipping.

#### 5. `routes`
**Description:** Optimized delivery paths visiting multiple stops for pickup or delivery. Routes balance cost minimization with delivery window compliance and vehicle capacity.

#### 6. `route_stops`
**Description:** Individual pickup or delivery locations within a route with stop sequence, arrival window, service time, and completion status. Enables delivery execution and tracking.

#### 7. `vehicles`
**Description:** Company-owned or leased delivery trucks, trailers, and fleet equipment. Vehicle records track registration, capacity, maintenance status, and driver assignments.

#### 8. `drivers`
**Description:** Individuals licensed and authorized to operate delivery vehicles. Driver records track certifications, hours of service compliance, performance, and availability.

#### 9. `freight_bills`
**Description:** Carrier invoices for transportation services rendered. Freight bills are audited against contracted rates, matched to shipments, and approved for payment.

#### 10. `proof_of_delivery` (POD)
**Description:** Documentation confirming successful delivery including recipient signature, delivery timestamp, condition notes, and photos. PODs resolve delivery disputes.

#### 11. `shipment_tracking`
**Description:** Real-time location and status updates for in-transit shipments. Tracking data is obtained from carriers and provided to customers for delivery visibility.

#### 12. `delivery_appointments`
**Description:** Scheduled time windows for pickup or delivery at customer or supplier locations. Appointments coordinate logistics with customer receiving operations.

#### 13. `freight_audit`
**Description:** Validation of carrier invoices against contract rates and shipment details. Audit identifies overcharges, rating errors, and duplicate invoices ensuring accurate payment.

#### 14. `carrier_performance_metrics`
**Description:** Measurement of carrier reliability including on-time delivery percentage, damage rates, invoice accuracy, and responsiveness. Metrics drive carrier selection and relationship management.

#### 15. `load_planning`
**Description:** Optimization of vehicle loading considering weight distribution, cube utilization, sequencing for delivery order, and product compatibility. Load planning maximizes asset utilization.

#### 16. `transportation_costs`
**Description:** Actual freight expenses by shipment, lane, carrier, and customer. Cost data supports freight budget management, customer billing, and carrier negotiation.

---

## MODULE 11: CMMS (COMPUTERIZED MAINTENANCE MANAGEMENT SYSTEM)

**Module Description:**
The Computerized Maintenance Management System (CMMS) manages equipment maintenance programs including preventive maintenance scheduling, corrective maintenance work orders, spare parts inventory, maintenance cost tracking, and equipment performance analysis. CMMS ensures production equipment reliability through systematic maintenance, reduces unplanned downtime, extends asset life, and optimizes maintenance costs. The system integrates with MES to capture equipment downtime and with procurement for spare parts management.

**Key Relationships:**
- Maintains: machines (master data), production equipment
- Integrates with: MES (downtime), procurement (spare parts)
- Provides: maintenance schedules, equipment reliability data

### Tables in CMMS:

#### 1. `equipment_registry`
**Description:** Master record of all maintainable assets including production machines, utilities, facility systems, and vehicles. Equipment records track specifications, location, criticality, purchase info, and warranty.

#### 2. `preventive_maintenance_plans`
**Description:** Scheduled maintenance programs defining recurring tasks to prevent equipment failures. PM plans specify frequency (time-based or usage-based), task lists, duration, required skills, and parts.

#### 3. `maintenance_work_orders`
**Description:** Jobs requesting or documenting maintenance work including corrective (breakdown repairs), preventive (scheduled), predictive, and improvement. Work orders track priority, status, labor, parts, and costs.

#### 4. `work_order_tasks`
**Description:** Individual activities within maintenance work orders such as "Replace bearings", "Lubricate chain", "Test operation". Tasks provide detailed execution instructions and track completion.

#### 5. `maintenance_schedules`
**Description:** Calendar-based schedule of when PM work orders are due considering equipment runtime, maintenance windows, and resource availability. Schedules prevent conflicts and ensure timely execution.

#### 6. `spare_parts_inventory`
**Description:** Maintenance-specific inventory of replacement parts, consumables, and supplies. Spare parts inventory management balances availability needs against carrying costs.

#### 7. `spare_parts_usage`
**Description:** Record of parts consumed in maintenance work linking to equipment and work orders. Usage data drives reordering, cost allocation, and failure analysis.

#### 8. `equipment_downtime_log`
**Description:** Comprehensive record of all equipment stoppages with downtime type, duration, failure mode, and repair actions. Log supports reliability analysis and improvement prioritization.

#### 9. `maintenance_costs`
**Description:** Labor, parts, and contractor expenses associated with maintaining each asset. Cost tracking enables maintenance budget management and justifies equipment replacement decisions.

#### 10. `equipment_performance_metrics`
**Description:** Reliability metrics including Mean Time Between Failures (MTBF), Mean Time To Repair (MTTR), and availability percentage. Metrics benchmark equipment health and maintenance effectiveness.

#### 11. `failure_modes`
**Description:** Classification of equipment failures by type (mechanical, electrical, operator error, etc.). Failure mode analysis identifies recurring problems and guides maintenance strategies.

#### 12. `maintenance_history`
**Description:** Complete record of all maintenance performed on each asset providing context for troubleshooting, warranty claims, and replacement decisions.

#### 13. `condition_monitoring`
**Description:** Sensor-based or inspection-based data tracking equipment health indicators (vibration, temperature, oil analysis). Condition monitoring enables predictive maintenance.

#### 14. `equipment_manuals`
**Description:** Technical documentation including operating manuals, maintenance procedures, parts diagrams, and troubleshooting guides. Manuals support effective maintenance execution.

#### 15. `maintenance_skills_matrix`
**Description:** Definition of technical competencies required for maintenance tasks (electrical, hydraulics, PLC programming, etc.). Skills matrix guides technician assignment and training.

#### 16. `maintenance_contractors`
**Description:** External service providers used for specialized maintenance, major overhauls, or capacity augmentation. Contractor management includes performance tracking and contract administration.

#### 17. `equipment_calibration_schedule`
**Description:** Subset of PM plans specifically for measuring equipment requiring periodic calibration. Schedule ensures measurement accuracy and regulatory compliance. Links to QMS calibration management.

#### 18. `maintenance_kpis`
**Description:** Dashboard metrics including PM compliance percentage, emergency work orders, backlog, cost per unit produced, and scheduled vs unscheduled maintenance ratio.

#### 19. `equipment_replacement_planning`
**Description:** Analysis of aging equipment considering maintenance costs, reliability, obsolescence, and capacity needs. Planning supports capital budgeting for asset replacement.

#### 20. `safety_permits`
**Description:** Documentation and authorization for high-risk maintenance work such as hot work, confined space entry, or lockout/tagout. Permits ensure safety protocol compliance.

---

## MODULE 12: OPERATIONAL / IoT

**Module Description:**
The Operational/IoT (Internet of Things) module collects real-time telemetry from sensors, PLCs, and connected equipment across the manufacturing facility. Sensor data includes machine operating parameters (speed, temperature, pressure), energy consumption, environmental conditions, and production counts. The system detects anomalies, generates alerts for out-of-range conditions, provides real-time dashboards, and enables predictive analytics. Integration with MES and CMMS enables automated downtime capture and condition-based maintenance triggering.

**Key Relationships:**
- Monitors: production equipment, facility systems
- Feeds: MES (production data), CMMS (condition monitoring)
- Provides: real-time visibility, predictive insights

### Tables in Operational/IoT:

#### 1. `sensor_registry`
**Description:** Catalog of all IoT devices and sensors deployed including sensor type (temperature, vibration, pressure), installation location, equipment association, and communication protocol. Registry manages sensor lifecycle.

#### 2. `sensor_data`
**Description:** Time-series storage of raw sensor readings with timestamp, sensor ID, measurement value, and units. High-volume data is aggregated or archived to manage storage.

#### 3. `machine_telemetry`
**Description:** Real-time operating data from production equipment including cycle counts, speeds, pressures, temperatures, and error codes. Telemetry provides production visibility and diagnostics.

#### 4. `iot_alerts`
**Description:** Notifications generated when sensor readings exceed thresholds indicating potential problems. Alerts specify severity, condition detected, and recommended actions.

#### 5. `anomaly_detection`
**Description:** Machine learning-based identification of unusual patterns in sensor data that may indicate developing failures or quality issues. Enables proactive intervention.

#### 6. `equipment_health_scores`
**Description:** Aggregated health indicators calculated from multiple sensors showing equipment condition on 0-100 scale. Health scores prioritize maintenance attention and predict failures.

#### 7. `energy_consumption_monitoring`
**Description:** Tracking of electricity, gas, compressed air, and water usage by equipment, line, or facility. Energy data supports cost allocation, sustainability reporting, and efficiency improvement.

#### 8. `iot_device_management`
**Description:** Administration of IoT infrastructure including device provisioning, firmware updates, connectivity status, and security. Ensures reliable data collection.

---

## MODULE 13: SUPPLIER PORTAL / ADVANCED PROCUREMENT

**Module Description:**
The Supplier Portal / Advanced Procurement module enables collaborative supplier relationships through self-service portals, RFQ management, supplier performance tracking, electronic invoicing, and 3-way matching. The system streamlines procurement processes, improves supplier communication, automates invoice processing, measures supplier quality and delivery performance, and manages supplier qualification and contracts. Integration with purchasing, quality, and finance creates closed-loop supplier lifecycle management from onboarding through continuous improvement.

**Key Relationships:**
- Depends on: Master Data (suppliers), ERP (purchase orders)
- Integrates with: QMS (supplier quality), Financial (invoice matching)
- Provides: supplier collaboration, procurement automation

### Tables in Supplier Portal:

#### 1. `rfq_headers`
**Description:** Request for Quote documents soliciting pricing from multiple suppliers for specified materials or services. RFQs define requirements, evaluation criteria, and response deadlines.

#### 2. `rfq_lines`
**Description:** Individual items within RFQs specifying materials, quantities, delivery requirements, and technical specifications. Lines enable detailed supplier responses.

#### 3. `rfq_suppliers`
**Description:** Suppliers invited to respond to specific RFQs with invitation status and response tracking. Manages which suppliers see which opportunities.

#### 4. `rfq_responses`
**Description:** Supplier quotes submitted through portal including pricing, delivery terms, and compliance statements. Responses enable online quote comparison and award decision.

#### 5. `rfq_response_lines`
**Description:** Detailed pricing and compliance information for each RFQ line item. Enables apples-to-apples comparison across suppliers.

#### 6. `quote_comparison`
**Description:** Side-by-side analysis of supplier quotes considering price, delivery, quality, and terms. Comparison supports objective supplier selection and negotiation.

#### 7. `supplier_contracts`
**Description:** Master agreements with suppliers defining commercial terms, pricing, volume commitments, and contract duration. Contracts govern procurement relationships.

#### 8. `contract_pricing`
**Description:** Material-specific pricing agreed in contracts with validity dates and terms. Contract pricing provides cost certainty and enables automated PO pricing.

#### 9. `supplier_performance_metrics`
**Description:** Monthly measurement of supplier delivery reliability (on-time %), quality (defect PPM), responsiveness (quote rate), and cost competitiveness. Metrics drive supplier management.

#### 10. `supplier_scorecards`
**Description:** Comprehensive quarterly or annual supplier ratings combining multiple performance dimensions into overall score and rating (A/B/C/D). Scorecards inform sourcing strategy.

#### 11. `supplier_rating_history`
**Description:** Longitudinal view of supplier performance trends over time. Historical ratings show improvement or decline patterns guiding relationship decisions.

#### 12. `supplier_invoices`
**Description:** Supplier bills received through portal with line-item detail for validation. Invoices undergo 3-way matching (PO, receipt, invoice) before payment approval.

#### 13. `supplier_invoice_lines`
**Description:** Individual items on supplier invoices matched to purchase order lines and receiving records. Line-level matching enables precise payment accuracy.

#### 14. `three_way_match_log`
**Description:** Audit trail of invoice matching process comparing PO authorization, goods receipt, and invoice amount. Matching ensures payment only for materials received at agreed prices.

#### 15. `supplier_qualification`
**Description:** Supplier onboarding and approval process including documentation review, financial assessment, capability evaluation, quality audit, and sample approval.

#### 16. `supplier_documents`
**Description:** Repository of supplier certifications, licenses, insurance, quality certificates, and compliance documents with expiration tracking. Ensures supplier qualifications remain current.

#### 17. `supplier_audits`
**Description:** Periodic assessments of supplier facilities, quality systems, and capabilities. Audits verify supplier capability and drive improvement.

#### 18. `audit_findings`
**Description:** Specific deficiencies or observations identified during supplier audits with corrective actions and follow-up tracking.

#### 19. `supplier_portal_users`
**Description:** Supplier employee accounts with portal access permissions. Users can view POs, submit invoices, respond to RFQs, and view performance metrics.

#### 20. `supplier_communications`
**Description:** Message threading between company buyers and supplier contacts providing audit trail of discussions, agreements, and issue resolution.

#### 21. `supplier_notifications`
**Description:** Automated alerts to suppliers for events like new RFQs, PO changes, payment made, performance reviews, or document expiration.

#### 22. `purchase_requisitions`
**Description:** Internal requests for procurement of materials or services initiating the buying process. Requisitions flow through approval workflow before conversion to RFQs or POs.

#### 23. `purchase_requisition_lines`
**Description:** Individual items requested in requisitions with justification, budget, and preferred suppliers. Lines drive procurement activities.

#### 24. `supplier_portal_integration_log`
**Description:** Audit trail of data exchanges between supplier portal and other systems (ERP, finance, quality). Logs enable troubleshooting integration issues.

#### 25. `supplier_capacity_planning`
**Description:** Supplier-provided information on production capacity, lead times, and constraints. Capacity data informs sourcing decisions and supply risk management.

#### 26. `supplier_development_programs`
**Description:** Initiatives to improve supplier capabilities in quality, cost, delivery, or technology. Programs track objectives, activities, and improvement results.

#### 27. `supplier_diversity_tracking`
**Description:** Classification of suppliers by ownership (minority, women, veteran-owned) supporting diversity spend goals and reporting requirements.

#### 28. `early_payment_discounts`
**Description:** Programs offering suppliers early payment in exchange for price reductions. Discount management optimizes working capital and procurement costs.

---

## MODULE 14: QMS (QUALITY MANAGEMENT SYSTEM)

**Module Description:**
The Quality Management System (QMS) provides comprehensive quality control and compliance management including non-conformance tracking (NCR), corrective and preventive action (CAPA), quality audits, statistical process control (SPC), calibration management, document control, customer complaint management, and supplier quality monitoring. QMS ensures product quality, regulatory compliance (ISO 9001, IATF 16949), continuous improvement, and customer satisfaction. Integration with MES captures quality data at source, integration with suppliers tracks incoming quality, and integration with customers manages complaints and returns.

**Key Relationships:**
- Integrates with: MES (inspections), Supplier Portal (supplier quality), Customer Service (complaints)
- Provides: quality compliance, continuous improvement, audit readiness

### Tables in QMS:

#### 1. `ncr_headers`
**Description:** Non-Conformance Reports documenting defects found in materials or products with root cause analysis, containment actions, disposition, and cost impact. NCRs drive corrective action and quality improvement.

#### 2. `ncr_defect_details`
**Description:** Specific characteristics that failed to meet specifications within NCRs including measured values, specification limits, and deviation magnitude. Details support root cause analysis.

#### 3. `capa_headers`
**Description:** Corrective and Preventive Action plans addressing root causes of problems to prevent recurrence. CAPAs include immediate actions, root cause investigation, permanent solutions, and effectiveness verification.

#### 4. `capa_actions`
**Description:** Individual tasks within CAPA plans assigned to responsible persons with due dates and completion tracking. Actions implement solutions and verify effectiveness.

#### 5. `quality_audits`
**Description:** Systematic examinations of quality systems, processes, or suppliers to verify compliance with standards (ISO 9001) and identify improvement opportunities. Audits can be internal, supplier, customer, or certification.

#### 6. `audit_findings`
**Description:** Specific non-conformances, observations, or recommendations identified during audits with severity classification and corrective action requirements.

#### 7. `control_plans`
**Description:** Process control documentation defining inspection characteristics, specifications, measurement methods, sample plans, and reaction plans. Control plans prevent defects through systematic monitoring.

#### 8. `control_plan_characteristics`
**Description:** Individual inspection points within control plans specifying what to measure, how, how often, and what action to take if out of specification.

#### 9. `spc_control_charts`
**Description:** Statistical process control charts tracking process parameters over time to detect out-of-control conditions before defects occur. Charts calculate control limits and process capability indices (Cpk).

#### 10. `spc_data_points`
**Description:** Individual measurements plotted on SPC charts with timestamps. Data points enable trend analysis, variation identification, and statistical process validation.

#### 11. `measuring_equipment`
**Description:** Registry of all gauges, meters, and inspection equipment with calibration schedules and status. Ensures measurement accuracy through calibration management.

#### 12. `calibration_records`
**Description:** History of equipment calibrations with as-found/as-left readings, calibration certificates, and next due dates. Records prove measurement traceability.

#### 13. `calibration_alerts`
**Description:** Notifications when measuring equipment calibration is approaching due or overdue. Alerts prevent use of uncalibrated equipment ensuring measurement validity.

#### 14. `quality_documents`
**Description:** Version-controlled repository of quality procedures, work instructions, specifications, and forms. Document control ensures current procedures are used and obsolete versions are removed.

#### 15. `document_revisions`
**Description:** Change history for quality documents tracking what changed, why, when, and who approved. Revision control maintains document integrity and audit trail.

#### 16. `customer_complaints`
**Description:** External quality issues reported by customers with detailed problem descriptions, root cause investigations, corrective actions, and customer communication. Complaints link to CAPAs and NCRs.

#### 17. `eight_d_reports`
**Description:** Structured 8-discipline problem-solving methodology for customer complaints including team formation, problem description, containment, root cause, corrective action, verification, and prevention.

#### 18. `ppap_submissions`
**Description:** Production Part Approval Process documentation for automotive customers demonstrating process capability before production. PPAP includes control plans, process studies, MSA, and sample inspection results.

#### 19. `supplier_quality_metrics`
**Description:** Monthly tracking of supplier incoming quality including defect rates, PPM, rejection costs, and CAPA counts. Metrics drive supplier improvement and sourcing decisions.

#### 20. `quality_kpis`
**Description:** Daily or weekly quality dashboard showing defect rates, first-time quality, customer complaints, scrap costs, and process capability trends. KPIs provide management visibility and drive improvement.

#### 21. `fmea_analyses`
**Description:** Failure Mode and Effects Analysis identifying potential product or process failures, their causes, effects, and risk priority. FMEA guides risk mitigation through design or process changes.

#### 22. `root_cause_analysis`
**Description:** Systematic investigation using 5-Why, Fishbone, or Fault Tree methods to identify underlying causes of quality problems. RCA ensures corrective actions address true causes.

#### 23. `quality_cost_tracking`
**Description:** Cost of Quality measurement including prevention costs, appraisal costs, internal failure costs, and external failure costs. COQ quantifies quality improvement ROI.

#### 24. `gage_r&r_studies`
**Description:** Measurement System Analysis evaluating whether gauges can adequately distinguish between parts. Studies ensure measurement variation doesn't mask true process variation.

#### 25. `first_article_inspections`
**Description:** Complete dimensional and functional inspection of first production parts verifying manufacturing process setup. FAI authorizes continued production or requires adjustment.

#### 26. `in_process_inspections`
**Description:** Quality checks performed during production to detect deviations early preventing defect propagation. In-process inspections enable real-time corrections.

#### 27. `final_inspections`
**Description:** Complete verification of finished products before shipment ensuring customer requirements are met. Final inspection is last defense against shipping defective products.

#### 28. `product_recalls`
**Description:** Formal retrieval of products from customers due to safety or quality issues. Recalls require batch traceability, customer notification, logistics, and regulatory reporting.

#### 29. `quality_training_records`
**Description:** Documentation of quality-specific training including inspection techniques, SPC interpretation, audit procedures, and standards requirements. Training ensures competency.

#### 30. `management_review_meetings`
**Description:** Periodic executive reviews of quality system performance including metrics, audit results, customer feedback, and improvement initiatives. Reviews ensure quality objectives are met and resources allocated.

---

## CONCLUSION

This semantic layer documentation provides comprehensive descriptions of all 14 modules and 298 tables in the GenIMS platform. Each description explains the purpose, key relationships, and business context enabling AI agents to understand the database structure and generate appropriate queries, reports, and analyses.

---

**END OF DOCUMENT**

Database count: 14 modules
Table count: 298 tables
Prepared for: Agentic AI Applications
Purpose: Semantic understanding and intelligent query generation

---
