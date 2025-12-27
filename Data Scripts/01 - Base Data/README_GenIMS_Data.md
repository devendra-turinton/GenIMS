# GenIMS Synthetic Master Data - README

## Overview
This package contains synthetic master data for the GenIMS (Generative Industrial Managed Services) platform for a global auto parts manufacturer.

## Generated Data Summary

### Global Manufacturing Operations
- **4 Factories** across 4 continents:
  - Yokohama, Japan (Asia-Pacific)
  - Detroit, USA (North America)
  - Stuttgart, Germany (Europe)
  - Chennai, India (Asia)

### Production Infrastructure
- **20 Production Lines** (4-6 per factory)
- **228 Machines** (8-15 per line)
- **1,716 Sensors** (5-10 per machine)
- **24 Shift Configurations** (6 shifts per factory)

### Human Resources
- **11,948 Employees** (2,000-4,000 per factory)
- Role Distribution:
  - 45% Operators
  - 15% Technicians
  - 10% Quality Inspectors
  - 8% Supervisors
  - 7% Maintenance Engineers
  - 15% Other roles (engineers, planners, managers)

### Products & Customers
- **20 Products** across 5 categories:
  - Suspension Components (5 products)
  - Brake Components (5 products)
  - Electrical Components (5 products)
  - Steering Components (3 products)
  - Transmission Components (2 products)

- **10 Major OEM Customers**:
  - Toyota, Honda, Subaru, Isuzu, Nissan (Japan)
  - Ford, General Motors (USA)
  - BMW, Mercedes-Benz, Volkswagen (Germany)

- **27 Line-Product Mappings** (which lines produce which products)
- **45 Customer-Product Mappings** (which customers order which products)

## Files Included

### 1. genims_schema.sql (9.7 KB)
Complete PostgreSQL schema with 12 tables:
- factories
- production_lines
- machines
- sensors
- employees
- shifts
- products
- customers
- line_product_mapping
- customer_product_mapping

**Key Features:**
- No foreign key constraints (as requested)
- Field names designed for easy relationship identification
- Comprehensive indices for query performance
- Support for multi-dimensional operational data

### 2. genims_master_data_inserts.sql (7.0 MB)
Ready-to-execute SQL INSERT statements for all master data.
Can be directly executed against PostgreSQL database after schema creation.

### 3. genims_master_data.json (8.6 MB)
Complete dataset in JSON format for:
- API testing
- Data validation
- Integration with other systems
- Quick data exploration

### 4. generate_genims_master_data.py
Python script used to generate all synthetic data.
Can be re-run to generate new datasets with different parameters.

## Database Schema Highlights

### Factories Table
- Global locations with timezone support
- ISO certifications (ISO9001, IATF16949, ISO14001)
- Operational history and facility details

### Production Lines Table
- Line-specific capacity metrics
- Automation levels (manual, semi-automated, fully-automated)
- Product category assignments
- Line types (assembly, machining, testing, painting, welding)

### Machines Table
- Detailed asset information (manufacturer, model, serial number)
- Criticality ratings for maintenance prioritization
- Power consumption data
- Maintenance schedules
- Remaining useful life calculations

### Sensors Table
- Multi-type sensor support (temperature, vibration, pressure, current, voltage, flow, speed, torque)
- Operating ranges and threshold definitions
- Data protocols (OPC-UA, Modbus-TCP, MQTT, REST-API)
- Calibration tracking

### Employees Table
- Multi-shift workforce (3 regular shifts + 2 weekend shifts + general day shift)
- 5M1E metrics support (Man, Machine, Material, Method, Measurement, Environment)
- Skill levels and certifications
- Department and line assignments

## Data Characteristics

### Realistic Distributions
- Employee roles follow typical manufacturing distributions
- Machine criticality weighted toward operational importance
- Sensor types matched to machine types
- Product complexity varies by category

### Temporal Data
- Installation dates spanning 2010-2026
- Maintenance overhaul history for aging equipment
- Employee hire dates and experience levels
- Product lead times and quality metrics

### Business Relationships
- Each line produces 1-3 products from its category
- Each customer orders 3-8 different products
- Annual volumes range from 5,000 to 500,000 units
- Quality requirements (PPM) vary by customer and product

## Usage Instructions

### Loading into PostgreSQL

```bash
# Create database
createdb genims_db

# Load schema
psql -d genims_db -f genims_schema.sql

# Load data
psql -d genims_db -f genims_master_data_inserts.sql

# Verify data
psql -d genims_db -c "SELECT COUNT(*) FROM factories;"
```

### Working with JSON

```python
import json

with open('genims_master_data.json', 'r') as f:
    data = json.load(f)

# Access factories
factories = data['factories']
print(f"Total factories: {len(factories)}")

# Access machines for a specific factory
factory_id = 'FAC-000001'
machines = [m for m in data['machines'] if m['factory_id'] == factory_id]
print(f"Machines in {factory_id}: {len(machines)}")
```

## Data Validation

### Key Metrics
- All foreign key relationships are valid (field names match)
- All status fields set to 'active'
- No NULL values in required fields
- Timestamps in consistent format (YYYY-MM-DD HH:MM:SS)
- Numeric ranges are realistic and industry-appropriate

### Cross-References Validated
✓ All production lines reference valid factories
✓ All machines reference valid lines and factories
✓ All sensors reference valid machines, lines, and factories
✓ All employees reference valid factories (and lines where applicable)
✓ All line-product mappings reference valid lines, products, and factories
✓ All customer-product mappings reference valid customers and products

## Next Steps for Agent Domain Data

This base master data provides the foundation for:
1. **Asset & Equipment Management** - Maintenance schedules, failure predictions
2. **Factory Operations** - Production schedules, OEE calculations
3. **Supply Chain** - Inventory levels, disruption scenarios
4. **Customer Success** - Order fulfillment, delivery tracking
5. **Energy Management** - Consumption patterns, optimization
6. **Quality Assurance** - Defect tracking, compliance monitoring
7. **Planning & Scheduling** - MRP/APS data, capacity planning

## Data Generation Parameters

```python
NUM_FACTORIES = 4
LINES_PER_FACTORY = (4, 6)
MACHINES_PER_LINE = (8, 15)
SENSORS_PER_MACHINE = (5, 10)
EMPLOYEES_PER_FACTORY = (2000, 4000)
```

These parameters can be adjusted in the Python script to generate different dataset sizes.

## Support for GenIMS Architecture

This data structure supports the core GenIMS architecture:

1. **Data Virtualization Layer** ✓
   - All systems represented (MES, SCADA, ERP, CMMS, etc.)
   - Unified access patterns

2. **Knowledge Graph Foundation** ✓
   - Hierarchical relationships (Factory → Line → Machine → Sensor)
   - Cross-domain connections (Line → Product → Customer)
   - Temporal data for causal analysis

3. **Multi-Agent Orchestration** ✓
   - Domain-specific data for each agent type
   - Shared entities for cross-domain coordination
   - Real-time operational state tracking

## Notes

- All data is synthetic and randomly generated
- Geographic locations are real, but facility details are fictional
- Customer names are real companies, but relationships are fictional
- Product codes and specifications are realistic but not actual parts
- This data is suitable for development, testing, and demonstration purposes

---

**Generated:** December 19, 2025
**Version:** 1.0
**Platform:** GenIMS (Generative Industrial Managed Services)
**Company:** Turinton AI Private Limited
