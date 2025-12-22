# GenIMS Platform - Semantic Layer: Field-Level Descriptions (Part 1 of 2)

## Purpose
This document provides detailed field-level descriptions for all tables in the GenIMS platform. Each field includes data type, purpose, constraints, relationships, and business context to enable AI agents to understand data semantics and generate intelligent queries.

---

## MODULE 1: MASTER DATA

### Table: `companies`
Core organizational entities representing legal business entities that own factories, warehouses, and employ personnel.

| Field Name | Data Type | Description | Constraints | Relationships |
|-----------|-----------|-------------|-------------|---------------|
| `company_id` | VARCHAR(50) | Unique identifier for the company | PRIMARY KEY | Referenced by: factories, warehouses, employees |
| `company_name` | VARCHAR(200) | Legal registered name of the company | NOT NULL, UNIQUE | Business name for all legal documents |
| `legal_entity_type` | VARCHAR(50) | Type of business entity: corporation, LLC, partnership, sole_proprietorship | - | Affects tax reporting and liability |
| `tax_id` | VARCHAR(50) | Government-issued tax identification number (EIN, GST, VAT number) | UNIQUE | Used for tax filings and reporting |
| `registration_number` | VARCHAR(100) | Company registration or incorporation number | - | Government registration identifier |
| `incorporation_date` | DATE | Date company was legally formed | - | Used for anniversary tracking, compliance |
| `fiscal_year_start_month` | INTEGER | Month when fiscal year begins (1=January, 4=April, etc.) | CHECK (1-12) | Defines financial reporting cycles |
| `base_currency` | VARCHAR(3) | Primary currency for financial reporting (ISO 4217 code: USD, EUR, INR) | NOT NULL | All amounts converted to base currency |
| `address_line1` | VARCHAR(200) | Primary street address | NOT NULL | Physical location for legal correspondence |
| `address_line2` | VARCHAR(200) | Additional address details (suite, building) | - | Optional address details |
| `city` | VARCHAR(100) | City or municipality | NOT NULL | Part of complete address |
| `state_province` | VARCHAR(100) | State, province, or region | - | Jurisdiction for taxes and regulations |
| `postal_code` | VARCHAR(20) | ZIP or postal code | - | Mail delivery and geographic analysis |
| `country` | VARCHAR(100) | Country name | NOT NULL | Determines regulatory jurisdiction |
| `phone` | VARCHAR(50) | Primary contact telephone number | - | Main company phone |
| `email` | VARCHAR(200) | General company email address | - | Primary electronic contact |
| `website` | VARCHAR(200) | Company website URL | - | Public web presence |
| `is_active` | BOOLEAN | Whether company is currently operating | DEFAULT true | Inactive companies excluded from operations |
| `created_at` | TIMESTAMP | Record creation timestamp | DEFAULT CURRENT_TIMESTAMP | Audit trail |
| `updated_at` | TIMESTAMP | Last modification timestamp | DEFAULT CURRENT_TIMESTAMP | Audit trail |

---

### Table: `suppliers`
External business entities that provide raw materials, components, services, or equipment to the company.

| Field Name | Data Type | Description | Constraints | Relationships |
|-----------|-----------|-------------|-------------|---------------|
| `supplier_id` | VARCHAR(50) | Unique identifier for the supplier | PRIMARY KEY | Referenced by: purchase_orders, supplier_contracts |
| `supplier_code` | VARCHAR(50) | Short alphanumeric code for supplier | UNIQUE, NOT NULL | Used in transactions and reports |
| `supplier_name` | VARCHAR(200) | Full legal business name of supplier | NOT NULL | Official supplier name |
| `supplier_type` | VARCHAR(30) | Classification: manufacturer, distributor, service_provider, contractor | - | Indicates supplier role in supply chain |
| `tax_id` | VARCHAR(50) | Supplier's tax identification number | - | For 1099 reporting and tax compliance |
| `payment_terms` | VARCHAR(100) | Standard payment terms: Net 30, Net 60, 2/10 Net 30, etc. | - | Defines when payment is due |
| `currency_code` | VARCHAR(3) | Supplier's invoicing currency (ISO 4217) | DEFAULT 'USD' | Currency for transactions |
| `credit_limit` | DECIMAL(15,2) | Maximum outstanding payables allowed | - | Credit risk management |
| `lead_time_days` | INTEGER | Typical delivery time in days from order to receipt | - | Used in MRP and planning |
| `minimum_order_quantity` | DECIMAL(15,4) | Minimum order quantity supplier requires | - | Purchase order sizing constraint |
| `quality_rating` | VARCHAR(20) | Overall quality performance: A/B/C/D/F | - | Derived from supplier_quality_metrics |
| `on_time_delivery_pct` | DECIMAL(5,2) | Historical percentage of on-time deliveries | - | Delivery reliability metric |
| `is_approved` | BOOLEAN | Whether supplier is approved for orders | DEFAULT false | Only approved suppliers can receive POs |
| `is_preferred` | BOOLEAN | Preferred supplier status | DEFAULT false | Given priority in sourcing decisions |
| `address_line1` | VARCHAR(200) | Primary street address | NOT NULL | Supplier physical location |
| `address_line2` | VARCHAR(200) | Additional address details | - | Optional address supplement |
| `city` | VARCHAR(100) | City or municipality | NOT NULL | Supplier location city |
| `state_province` | VARCHAR(100) | State, province, or region | - | Supplier location state |
| `postal_code` | VARCHAR(20) | ZIP or postal code | - | Supplier mailing code |
| `country` | VARCHAR(100) | Country name | NOT NULL | Supplier country location |
| `phone` | VARCHAR(50) | Primary contact phone | - | Main supplier phone |
| `email` | VARCHAR(200) | General supplier email | - | Primary supplier email |
| `website` | VARCHAR(200) | Supplier website URL | - | Supplier web presence |
| `contact_name` | VARCHAR(200) | Primary contact person | - | Main supplier contact |
| `contact_title` | VARCHAR(100) | Contact person's role/title | - | Contact's position |
| `contact_phone` | VARCHAR(50) | Direct phone for primary contact | - | Contact's direct line |
| `contact_email` | VARCHAR(200) | Email for primary contact | - | Contact's email |
| `certifications` | TEXT | Quality certifications held: ISO 9001, AS9100, etc. | - | Quality system credentials |
| `is_active` | BOOLEAN | Whether supplier is active | DEFAULT true | Inactive suppliers cannot receive new POs |
| `inactivation_reason` | TEXT | Reason for supplier inactivation | - | Documents why supplier was deactivated |
| `created_at` | TIMESTAMP | Record creation timestamp | DEFAULT CURRENT_TIMESTAMP | Audit trail |
| `updated_at` | TIMESTAMP | Last modification timestamp | DEFAULT CURRENT_TIMESTAMP | Audit trail |

---

### Table: `customers`
External business entities or individuals that purchase products or services from the company.

| Field Name | Data Type | Description | Constraints | Relationships |
|-----------|-----------|-------------|-------------|---------------|
| `customer_id` | VARCHAR(50) | Unique identifier for the customer | PRIMARY KEY | Referenced by: sales_orders, service_tickets |
| `customer_code` | VARCHAR(50) | Short alphanumeric code for customer | UNIQUE, NOT NULL | Used in transactions and reports |
| `customer_name` | VARCHAR(200) | Full name or business name | NOT NULL | Official customer name |
| `customer_type` | VARCHAR(30) | Classification: individual, small_business, enterprise, government | - | Determines service level and pricing |
| `industry` | VARCHAR(100) | Customer's industry sector: automotive, aerospace, electronics, etc. | - | Market segment for analysis |
| `tax_id` | VARCHAR(50) | Customer's tax ID or VAT number | - | For tax-exempt sales and reporting |
| `payment_terms` | VARCHAR(100) | Standard payment terms offered to customer | - | When payment is due |
| `currency_code` | VARCHAR(3) | Customer's invoicing currency | DEFAULT 'USD' | Transaction currency |
| `credit_limit` | DECIMAL(15,2) | Maximum outstanding receivables allowed | - | Credit risk management |
| `credit_status` | VARCHAR(30) | Current credit standing: good, hold, collections | DEFAULT 'good' | Controls order acceptance |
| `price_level` | VARCHAR(30) | Pricing tier: retail, wholesale, volume, contract | - | Determines product pricing |
| `sales_territory` | VARCHAR(50) | Geographic or account-based territory assignment | - | Links to sales_territories |
| `account_manager` | VARCHAR(50) | Employee responsible for account | FK to employees | Primary sales contact |
| `payment_method` | VARCHAR(30) | Preferred payment method: check, wire, credit_card, ACH | - | How customer pays |
| `shipping_method` | VARCHAR(50) | Default shipping carrier and service level | - | Standard delivery method |
| `tax_exempt` | BOOLEAN | Whether customer is exempt from sales tax | DEFAULT false | Affects invoice tax calculation |
| `tax_exempt_certificate` | VARCHAR(100) | Tax exemption certificate number | - | Documentation for tax exemption |
| `address_line1` | VARCHAR(200) | Primary street address | NOT NULL | Customer location |
| `address_line2` | VARCHAR(200) | Additional address details | - | Optional address details |
| `city` | VARCHAR(100) | City or municipality | NOT NULL | Customer city |
| `state_province` | VARCHAR(100) | State, province, or region | - | Customer state |
| `postal_code` | VARCHAR(20) | ZIP or postal code | - | Customer postal code |
| `country` | VARCHAR(100) | Country name | NOT NULL | Customer country |
| `phone` | VARCHAR(50) | Primary contact phone | - | Main customer phone |
| `email` | VARCHAR(200) | General customer email | - | Primary customer email |
| `website` | VARCHAR(200) | Customer website URL | - | Customer web presence |
| `is_active` | BOOLEAN | Whether customer account is active | DEFAULT true | Inactive customers can't place orders |
| `inactivation_reason` | TEXT | Reason for customer inactivation | - | Why customer was deactivated |
| `customer_since` | DATE | Date customer relationship began | - | Customer tenure tracking |
| `lifetime_value` | DECIMAL(15,2) | Total historical revenue from customer | - | Calculated customer value |
| `created_at` | TIMESTAMP | Record creation timestamp | DEFAULT CURRENT_TIMESTAMP | Audit trail |
| `updated_at` | TIMESTAMP | Last modification timestamp | DEFAULT CURRENT_TIMESTAMP | Audit trail |

---

### Table: `materials`
Raw materials, components, sub-assemblies, and consumables used in manufacturing processes.

| Field Name | Data Type | Description | Constraints | Relationships |
|-----------|-----------|-------------|-------------|---------------|
| `material_id` | VARCHAR(50) | Unique identifier for the material | PRIMARY KEY | Referenced by: BOMs, purchase_orders, inventory |
| `material_code` | VARCHAR(50) | Short alphanumeric SKU or part number | UNIQUE, NOT NULL | Used in all transactions |
| `material_name` | VARCHAR(200) | Descriptive name of the material | NOT NULL | Human-readable material name |
| `material_type` | VARCHAR(30) | Category: raw_material, component, sub_assembly, consumable, packaging | NOT NULL | Classification for planning |
| `material_category` | VARCHAR(100) | Higher-level grouping: metals, plastics, electronics, chemicals | - | Product family classification |
| `description` | TEXT | Detailed material description and specifications | - | Full specification details |
| `unit_of_measure` | VARCHAR(20) | Base unit: EA (each), KG, LBS, M (meters), L (liters), etc. | NOT NULL | Measurement standard |
| `alternate_uom` | VARCHAR(20) | Secondary unit of measure if applicable | - | Alternate measurement unit |
| `conversion_factor` | DECIMAL(15,6) | Conversion rate from alternate UOM to base UOM | - | Unit conversion multiplier |
| `standard_cost` | DECIMAL(15,4) | Expected cost per unit for inventory valuation | - | Used in cost calculations |
| `average_cost` | DECIMAL(15,4) | Weighted average cost based on receipts | - | FIFO/LIFO cost basis |
| `last_purchase_price` | DECIMAL(15,4) | Most recent purchase price paid | - | Latest actual cost |
| `list_price` | DECIMAL(15,4) | Supplier's published list price | - | Reference pricing |
| `lead_time_days` | INTEGER | Typical procurement lead time from order to receipt | NOT NULL | Used in MRP calculations |
| `safety_stock_quantity` | DECIMAL(15,4) | Minimum buffer stock to maintain | DEFAULT 0 | Safety stock for availability |
| `reorder_point` | DECIMAL(15,4) | Inventory level triggering replenishment | - | Automatic reorder trigger |
| `reorder_quantity` | DECIMAL(15,4) | Standard order quantity when reordering | - | Economic order quantity |
| `minimum_order_quantity` | DECIMAL(15,4) | Smallest quantity that can be ordered | - | Supplier or packaging constraint |
| `lot_size_multiple` | DECIMAL(15,4) | Orders must be multiples of this quantity | - | Packaging or handling constraint |
| `preferred_supplier_id` | VARCHAR(50) | Default supplier for this material | FK to suppliers | Primary sourcing |
| `abc_classification` | VARCHAR(1) | Value importance: A (high), B (medium), C (low) | CHECK ('A','B','C') | Inventory control strategy |
| `shelf_life_days` | INTEGER | Days material remains usable after receipt | - | Expiration management |
| `storage_temperature` | VARCHAR(50) | Required storage conditions: ambient, refrigerated, frozen | - | Storage requirements |
| `hazardous_material` | BOOLEAN | Whether material is hazardous | DEFAULT false | Safety and regulatory handling |
| `tariff_code` | VARCHAR(20) | Harmonized tariff classification for customs | - | Import/export classification |
| `country_of_origin` | VARCHAR(100) | Where material is manufactured or sourced | - | Trade compliance |
| `weight_per_unit` | DECIMAL(15,6) | Weight in base weight UOM | - | Shipping and handling |
| `weight_uom` | VARCHAR(20) | Weight unit of measure: KG, LBS | - | Weight measurement standard |
| `dimensions` | VARCHAR(100) | Length x Width x Height in specified UOM | - | Physical size for storage |
| `is_active` | BOOLEAN | Whether material can be used in new orders/BOMs | DEFAULT true | Active material flag |
| `obsolete_date` | DATE | When material was discontinued | - | End of life tracking |
| `replacement_material_id` | VARCHAR(50) | Superseding material if obsolete | FK to materials | Replacement part reference |
| `lot_tracking_required` | BOOLEAN | Whether lot/batch numbers must be tracked | DEFAULT false | Traceability requirement |
| `serial_tracking_required` | BOOLEAN | Whether serial numbers must be tracked | DEFAULT false | Unit-level traceability |
| `created_at` | TIMESTAMP | Record creation timestamp | DEFAULT CURRENT_TIMESTAMP | Audit trail |
| `updated_at` | TIMESTAMP | Last modification timestamp | DEFAULT CURRENT_TIMESTAMP | Audit trail |

---

### Table: `products`
Finished goods or sellable items manufactured or distributed by the company.

| Field Name | Data Type | Description | Constraints | Relationships |
|-----------|-----------|-------------|-------------|---------------|
| `product_id` | VARCHAR(50) | Unique identifier for the product | PRIMARY KEY | Referenced by: BOMs, sales_orders, work_orders |
| `product_code` | VARCHAR(50) | Short alphanumeric SKU or model number | UNIQUE, NOT NULL | Used in sales and production |
| `product_name` | VARCHAR(200) | Marketing or descriptive product name | NOT NULL | Customer-facing product name |
| `product_family` | VARCHAR(100) | Product line or family grouping | - | High-level product classification |
| `product_category` | VARCHAR(100) | Category for reporting and analysis | - | Product segment |
| `description` | TEXT | Detailed product description and features | - | Full product specifications |
| `unit_of_measure` | VARCHAR(20) | Selling unit: EA, BOX, CASE, SET, etc. | NOT NULL | Sales transaction unit |
| `standard_cost` | DECIMAL(15,4) | Expected cost to manufacture one unit | - | Cost basis for profitability |
| `list_price` | DECIMAL(15,4) | Published selling price before discounts | - | Reference pricing |
| `minimum_price` | DECIMAL(15,4) | Floor price below which approvals needed | - | Pricing governance |
| `weight_per_unit` | DECIMAL(15,6) | Product weight for shipping calculations | - | Freight calculation |
| `weight_uom` | VARCHAR(20) | Weight unit of measure | - | Weight measurement standard |
| `dimensions` | VARCHAR(100) | Product dimensions for shipping and storage | - | Physical size specifications |
| `bom_id` | VARCHAR(50) | Primary bill of materials for this product | FK to bill_of_materials | Production recipe reference |
| `routing_id` | VARCHAR(50) | Manufacturing routing/process | FK to routings | Production process definition |
| `production_lead_time_days` | INTEGER | Typical time to manufacture from start to finish | - | Production planning duration |
| `make_or_buy` | VARCHAR(20) | Strategy: make (manufacture), buy (purchase) | CHECK: make, buy | Sourcing strategy |
| `is_sellable` | BOOLEAN | Whether product can be sold to customers | DEFAULT true | Sales eligibility |
| `is_manufactured` | BOOLEAN | Whether product is produced in-house | DEFAULT true | Production flag |
| `is_active` | BOOLEAN | Whether product is active for new orders | DEFAULT true | Active product status |
| `introduction_date` | DATE | When product was launched | - | Product lifecycle tracking |
| `discontinuation_date` | DATE | When product was discontinued | - | End of life date |
| `replacement_product_id` | VARCHAR(50) | Superseding product if discontinued | FK to products | Replacement product reference |
| `warranty_period_months` | INTEGER | Standard warranty duration in months | - | Warranty terms |
| `shelf_life_days` | INTEGER | Days product remains usable/sellable | - | Expiration management |
| `quality_specifications` | TEXT | Quality requirements and acceptance criteria | - | Quality control standards |
| `packaging_requirements` | TEXT | How product must be packaged for shipment | - | Packaging specifications |
| `tariff_code` | VARCHAR(20) | Harmonized tariff code for exports | - | Trade compliance |
| `country_of_origin` | VARCHAR(100) | Where product is manufactured | - | Made in country designation |
| `regulatory_certifications` | TEXT | Required certifications: UL, CE, FDA, etc. | - | Compliance credentials |
| `created_at` | TIMESTAMP | Record creation timestamp | DEFAULT CURRENT_TIMESTAMP | Audit trail |
| `updated_at` | TIMESTAMP | Last modification timestamp | DEFAULT CURRENT_TIMESTAMP | Audit trail |

---

### Table: `employees`
Individual workers employed by the company across all functions and locations.

| Field Name | Data Type | Description | Constraints | Relationships |
|-----------|-----------|-------------|-------------|---------------|
| `employee_id` | VARCHAR(50) | Unique identifier for the employee | PRIMARY KEY | Referenced by: work_orders, service_tickets, approvals |
| `employee_number` | VARCHAR(50) | Company-assigned employee number | UNIQUE, NOT NULL | Payroll and HR identifier |
| `first_name` | VARCHAR(100) | Employee's given name | NOT NULL | Legal first name |
| `last_name` | VARCHAR(100) | Employee's family name | NOT NULL | Legal last name |
| `full_name` | VARCHAR(200) | Complete name (first + middle + last) | - | Display name |
| `email` | VARCHAR(200) | Company email address | UNIQUE | Primary electronic contact |
| `phone` | VARCHAR(50) | Work phone number | - | Contact phone |
| `mobile_phone` | VARCHAR(50) | Mobile phone number | - | Mobile contact |
| `job_title` | VARCHAR(100) | Current position or role | - | Position title |
| `department_id` | VARCHAR(50) | Department assignment | FK to departments | Organizational unit |
| `reports_to_employee_id` | VARCHAR(50) | Direct manager/supervisor | FK to employees | Reporting hierarchy |
| `hire_date` | DATE | Date employee started employment | NOT NULL | Employment start date |
| `termination_date` | DATE | Date employment ended | - | Employment end date |
| `employment_status` | VARCHAR(30) | Current status: active, leave, terminated, retired | NOT NULL | Employment state |
| `employment_type` | VARCHAR(30) | Classification: full_time, part_time, contractor, temporary | - | Employment category |
| `pay_type` | VARCHAR(20) | Compensation method: hourly, salaried | - | Payroll classification |
| `hourly_rate` | DECIMAL(10,2) | Hourly pay rate if hourly employee | - | Hourly compensation |
| `annual_salary` | DECIMAL(15,2) | Annual salary if salaried employee | - | Salary compensation |
| `shift` | VARCHAR(20) | Regular shift assignment: day, evening, night, rotating | - | Work schedule |
| `location` | VARCHAR(100) | Primary work location or facility | - | Work site |
| `is_supervisor` | BOOLEAN | Whether employee manages others | DEFAULT false | Supervisory role flag |
| `is_active` | BOOLEAN | Whether employee is currently active | DEFAULT true | Active employee status |
| `skills` | TEXT[] | Array of employee skills and certifications | - | Competency tracking |
| `certifications` | TEXT[] | Professional certifications held | - | Credential tracking |
| `created_at` | TIMESTAMP | Record creation timestamp | DEFAULT CURRENT_TIMESTAMP | Audit trail |
| `updated_at` | TIMESTAMP | Last modification timestamp | DEFAULT CURRENT_TIMESTAMP | Audit trail |

---

## MODULE 2: CRM

### Table: `sales_orders`
Confirmed customer purchase commitments authorizing manufacture and delivery of products.

| Field Name | Data Type | Description | Constraints | Relationships |
|-----------|-----------|-------------|-------------|---------------|
| `sales_order_id` | VARCHAR(50) | Unique identifier for the sales order | PRIMARY KEY | Referenced by: shipments, invoices, work_orders |
| `order_number` | VARCHAR(50) | Human-readable order number | UNIQUE, NOT NULL | Displayed to customers |
| `customer_id` | VARCHAR(50) | Customer placing the order | FK to customers, NOT NULL | Order owner |
| `customer_po_number` | VARCHAR(100) | Customer's purchase order reference | - | Customer's internal PO number |
| `order_date` | DATE | Date order was placed | NOT NULL | Order creation date |
| `requested_delivery_date` | DATE | Date customer wants delivery | - | Delivery target |
| `promised_delivery_date` | DATE | Date company committed to deliver | - | Confirmed delivery date |
| `actual_delivery_date` | DATE | Actual completion date | - | When delivered |
| `order_type` | VARCHAR(30) | Classification: standard, rush, sample, warranty | - | Order category |
| `order_status` | VARCHAR(30) | Current state: draft, submitted, approved, in_production, shipped, invoiced, closed | NOT NULL | Order lifecycle stage |
| `payment_terms` | VARCHAR(100) | Payment terms for this order | - | When payment due |
| `payment_status` | VARCHAR(30) | Payment state: unpaid, partial, paid | DEFAULT 'unpaid' | Payment tracking |
| `subtotal` | DECIMAL(15,2) | Sum of line items before tax/freight | - | Order subtotal |
| `tax_amount` | DECIMAL(15,2) | Sales tax charged | DEFAULT 0 | Tax calculation |
| `freight_charges` | DECIMAL(15,2) | Shipping charges | DEFAULT 0 | Freight cost |
| `total_amount` | DECIMAL(15,2) | Grand total (subtotal + tax + freight) | NOT NULL | Total order value |
| `currency_code` | VARCHAR(3) | Transaction currency | DEFAULT 'USD' | Order currency |
| `exchange_rate` | DECIMAL(12,6) | Exchange rate to base currency | DEFAULT 1.0 | Currency conversion rate |
| `sales_rep_id` | VARCHAR(50) | Sales representative handling order | FK to employees | Account owner |
| `commission_rate` | DECIMAL(5,2) | Commission percentage for sales rep | - | Commission calculation |
| `shipping_address_line1` | VARCHAR(200) | Delivery street address | - | Ship-to address |
| `shipping_city` | VARCHAR(100) | Delivery city | - | Ship-to city |
| `shipping_state` | VARCHAR(100) | Delivery state/province | - | Ship-to state |
| `shipping_postal_code` | VARCHAR(20) | Delivery postal code | - | Ship-to postal code |
| `shipping_country` | VARCHAR(100) | Delivery country | - | Ship-to country |
| `shipping_method` | VARCHAR(50) | Carrier and service level | - | How to ship |
| `shipping_instructions` | TEXT | Special delivery instructions | - | Delivery notes |
| `incoterm` | VARCHAR(20) | International shipping terms: FOB, CIF, DDP | - | Trade terms |
| `priority` | VARCHAR(20) | Urgency: low, normal, high, rush | DEFAULT 'normal' | Scheduling priority |
| `customer_notes` | TEXT | Special requirements or notes from customer | - | Customer instructions |
| `internal_notes` | TEXT | Internal notes not visible to customer | - | Internal coordination notes |
| `created_by` | VARCHAR(50) | Employee who created order | FK to employees | Order creator |
| `approved_by` | VARCHAR(50) | Employee who approved order | FK to employees | Approval authority |
| `approval_date` | DATE | When order was approved | - | Approval timestamp |
| `invoiced_date` | DATE | When invoice was generated | - | Billing date |
| `closed_date` | DATE | When order was closed/completed | - | Order completion date |
| `cancelled` | BOOLEAN | Whether order was cancelled | DEFAULT false | Cancellation flag |
| `cancellation_reason` | TEXT | Why order was cancelled | - | Cancellation justification |
| `created_at` | TIMESTAMP | Record creation timestamp | DEFAULT CURRENT_TIMESTAMP | Audit trail |
| `updated_at` | TIMESTAMP | Last modification timestamp | DEFAULT CURRENT_TIMESTAMP | Audit trail |

---

*[This document continues with detailed field descriptions for key tables across all modules. Due to length, Part 2 will cover remaining critical tables.]*

---

**END OF PART 1**

This document provides semantic field-level understanding for the GenIMS platform enabling AI agents to:
- Understand field purposes and constraints
- Generate appropriate SQL queries
- Interpret data relationships
- Validate data integrity
- Create meaningful reports and analyses

**Part 2 will continue with detailed field descriptions for:**
- Module 3-5: Customer Service, HCM, ERP Core
- Module 6-8: Financial, Sync, MES
- Module 9-14: WMS, TMS, CMMS, IoT, Supplier Portal, QMS

---
