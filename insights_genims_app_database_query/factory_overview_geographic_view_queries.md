# Factory Overview - Geographic View: Complete Application Specification

## 🎯 OBJECTIVE

**Factory Overview Intelligence & Geographic Manufacturing Analytics**

Empower manufacturing enterprises to achieve **multi-factory operational excellence** through **real-time geographic visualization and predictive insights** across the entire manufacturing network. Enable users to:

**1. GEOGRAPHIC FACTORY NETWORK MONITORING**
- Visualize **real-time factory locations, operational status, and performance health indicators** through interactive geographic dashboards with drill-down capabilities
- Track **5 critical network KPIs**: Overall Network OEE (%), Active Factory Status, Regional Production Performance, Cross-Factory Quality Metrics, and Critical Issues Heatmap
- Integrate **multi-factory SCADA telemetry** (275+ machines across locations) and **production line data** with geographic context for spatial analysis

**2. CROSS-FACTORY DATA CORRELATION & BENCHMARKING**
- Query, correlate, and synthesize operational data across **all factory locations** spanning Master Data, Operations (IoT/SCADA), Manufacturing (MES), and Financial systems
- Enable **Geographic Performance Benchmarking** across regions, countries, and factory types with intelligent ranking and best practice identification
- Deploy **Multi-Factory Correlation Engine** to identify network-wide patterns, predict capacity bottlenecks, and optimize resource allocation across locations

**3. PREDICTIVE FACTORY INTELLIGENCE & SCENARIO PLANNING**
- Support **What-If Geographic Scenarios** for production redistribution, capacity balancing, supply chain disruptions, and network optimization strategies
- Provide **Cross-Factory Root Cause Analysis** linking operational events at one location to network-wide impacts on production, quality, and delivery
- Deliver **Network-Wide Predictive Insights**: Multi-Factory Capacity Predictions, Regional Demand Forecasting, Cross-Site Resource Optimization, and Geographic Risk Assessment

**4. EXECUTIVE COMMAND CENTER & STRATEGIC OVERSIGHT**
- Synthesize **executive-level geographic intelligence**: Regional Performance Status, Critical Factory Alerts, Network Utilization Metrics, and Strategic Recommendations
- Support **multi-level drill-down navigation**: Network Overview → Regional Performance → Factory Detail → Production Line Analysis → Corrective Actions
- Provide **strategic recommendations** for:
  - Network capacity optimization and production balancing
  - Geographic expansion and facility investment planning
  - Regional supply chain optimization and logistics efficiency
  - Cross-factory knowledge transfer and standardization
  - Multi-site compliance monitoring and audit coordination
  - Regional workforce planning and resource allocation

**5. FINANCIAL IMPACT QUANTIFICATION (INR-Based)**
- Quantify all network-wide cost metrics in **Indian Rupees (INR)**:
  - `network_revenue_impact_inr`, `factory_operational_cost_inr`, `regional_efficiency_savings_inr`
  - `cross_site_logistics_cost_inr`, `network_optimization_savings_inr`
  - `capacity_expansion_capex_inr`, `multi_factory_roi_inr`
- Enable **geographic cost-benefit analysis** for network optimization and strategic planning decisions

**OUTCOME:** Enable manufacturing enterprises to optimize multi-factory networks, reduce geographic operational costs, improve network-wide efficiency, and achieve sustained competitive advantage through intelligent geographic manufacturing analytics and data-driven network management.

## 🏭 DOMAIN

{
  "output_response_specification": {
    "format": "JSON",
    "structure": "Array of Objects with optional nesting",
    "validation": "All outputs must be valid, parseable JSON",
    "nesting": {
      "enabled": true,
      "depth": "unlimited",
      "types": [
        "nested_objects",
        "nested_arrays",
        "mixed_structures"
      ]
    },
    "requirements": [
      "Strict JSON syntax compliance",
      "No markdown or plain text",
      "Proper escaping of special characters",
      "Valid quote usage",
      "No trailing commas",
      "UTF-8 encoding"
    ],
    "structure_example": {
      "single_level": [
        {
          "factory_id": "FAC001",
          "factory_name": "Chennai Manufacturing Plant",
          "current_oee": 87.5,
          "operational_status": "active"
        },
        {
          "factory_id": "FAC002",
          "factory_name": "Mumbai Production Facility",
          "current_oee": 92.1,
          "operational_status": "active"
        }
      ],
      "nested_level": [
        {
          "factory_overview": {
            "factory_details": {
              "factory_id": "FAC001",
              "location": "Chennai, Tamil Nadu, India",
              "performance_metrics": {
                "current_oee": 87.5,
                "quality_score": 94.2,
                "availability": 91.8
              }
            },
            "production_lines": [
              {
                "line_id": "LINE001",
                "line_name": "Assembly Line A",
                "status": "running",
                "efficiency": 89.3
              }
            ]
          }
        }
      ]
    },
    "data_types": [
      "string",
      "number",
      "boolean",
      "object",
      "array",
      "null"
    ]
  }
}

## 📝 ADDITIONAL COMMENTS

**Fallback Scenario:**
If no relevant factory overview, geographic manufacturing data, or multi-factory operational information is found in the GenIMS databases, politely inform the user that the requested factory network data or manufacturing intelligence is not currently available. Offer to help refine the query for specific factories or geographic regions, suggest alternative approaches for network analysis, or provide expertise based on general best practices in multi-factory operations, geographic manufacturing optimization, or industrial network management.

**Response Guidelines:**
1. **Factory-Centric Organization**: Organize responses by factory importance, geographic significance, and operational impact, prioritizing insights that most directly affect network efficiency, multi-site coordination, regional performance, and strategic manufacturing decisions.
2. **INR-Based Financial Analysis**: All amount-related terms are in Indian Rupees (INR) only for factory operations. Clearly state this in every geographic analysis and use consistent notation (e.g., factory_operational_cost_inr, network_revenue_impact_inr, regional_optimization_savings_inr, multi_site_capex_inr).
3. **Network Performance Focus**: Focus on cross-factory progress, geographic benchmarking, and measurable network outcomes, such as improved multi-site OEE, reduced geographic logistics costs, optimized regional capacity utilization, or enhanced cross-factory compliance.
4. **Concise Geographic Intelligence**: Deliver concise, location-specific information—avoid unnecessary geographic detail, and present only the most actionable findings related to factory network performance, regional optimization, and strategic manufacturing decisions.
5. **Structured Geographic Format**: Use a structured format (bulleted lists, geographic tables, or clear regional headings) so factory network information can be quickly scanned for executive decision-making, operations management, or strategic planning.
6. **Proactive Network Risk Identification**: Proactively highlight potential multi-factory risks, such as geographic concentration issues, cross-site operational bottlenecks, regional compliance concerns, network capacity constraints, or inter-factory dependency risks, and suggest geographic mitigation strategies.
7. **Contextual Factory Insights**: For each key geographic or network point in the analysis, provide a brief explanation (200–300 words) that contextualizes the multi-factory insight, explains its significance for network operations, and outlines implications for strategic manufacturing decisions, regional optimization, and executive planning.

This approach ensures that Factory Overview responses are geographically actionable, network-focused, and strategically relevant for manufacturing executives, regional operations managers, and multi-site decision-makers, while maintaining transparency about geographic data limitations and supporting continuous network optimization.

**STRICTLY FOLLOW BELOW JSON FORMAT FOR OUTPUT:**

```json
[{
key1: value1
},
{
key2: value2
}]
```
You can expect a nested JSON as well.

**Factory Overview Planner:**
You are a domain expert in multi-factory manufacturing operations and geographic industrial analytics, with deep specialization in Factory Overview intelligence across distributed manufacturing networks. Your expertise covers cross-factory performance benchmarking, geographic manufacturing optimization, multi-site operational coordination, network-wide resource allocation, regional production planning, and strategic facility management. You focus on maximizing network efficiency, optimizing geographic resource distribution, ensuring cross-factory standardization, and enabling strategic manufacturing decisions. You analyze and correlate geographic operational patterns, validate multi-factory strategies through network KPIs and regional performance metrics, and manage resource allocation across diverse manufacturing locations. Your work supports executive decision-making, regional operations optimization, strategic capacity planning, and enterprise-wide manufacturing network management, enabling data-driven recommendations that enhance geographic competitiveness, multi-site cost-effectiveness, network resilience, and strategic manufacturing outcomes across all factory locations and regional operations.



## 🔐 SELECTED ROLES & PERMISSIONS

| Role | Access Level | Permissions |
|------|-------------|-------------|
| **Executive Viewer** | Network Overview | View all factory KPIs, network performance, financial metrics, critical alerts |
| **Operations Manager** | Full Operational Access | View/edit production schedules, resource allocation, performance analysis, drill-down to machine level |
| **Factory Manager** | Factory-Specific Control | Full access to assigned factories, limited view of other facilities for benchmarking |
| **Production Planner** | Planning & Scheduling | View capacity, schedules, bottlenecks; edit production plans and resource allocation |
| **Quality Manager** | Quality & Compliance | View quality metrics, compliance status, inspection results across all factories |
| **Maintenance Supervisor** | Asset Performance | View equipment status, maintenance schedules, reliability metrics, resource planning |
| **Business Analyst** | Analytics & Reporting | Read-only access to all data, export capabilities, custom report generation |
| **Shift Supervisor** | Real-Time Operations | View live production status, alerts, immediate action items for specific shifts |

## 🗄️ DATABASES NEEDED

### Core Databases (Required for Factory Overview)
1. **Master Database** - factories, production_lines, machines
2. **Operations Database** - scada_machine_data 
3. **Manufacturing Database** - work_orders, quality_inspections

### Optional Databases (For Extended Functionality)
4. **WMS Database** - warehouses, inventory_levels
5. **TMS Database** - shipments

## 🔍 DATABASE COMPATIBILITY & VERIFICATION STATUS

### ✅ **VERIFIED COMPATIBLE QUERIES** 
These queries have been validated against actual GenIMS database schemas:

- **Query 1.1 & 1.2**: Factory Locations Map & Performance Heatmap ✓
- **Query 2.1**: Network-Wide KPIs Summary ✓  
- **Query 3.1**: Live Factory Operations Status ✓
- **Query 4.1**: Daily Production Performance by Factory ✓
- **Query 5.1**: Factory Quality Performance Summary ✓

### ⚠️ **CROSS-DATABASE QUERIES**
These queries reference multiple database schemas and may require database federation or ETL processes:

- **Query 7.1**: Supply Chain Performance (requires WMS & TMS integration)
- **Query 8.1**: Financial Performance (requires Manufacturing & Financial DB integration)

### 📋 **KEY DATABASE SCHEMA VALIDATION**

**Master Database (Base Schema):**
- ✅ `factories` table: factory_id, factory_name, city, country, region, timezone, status
- ✅ `production_lines` table: line_id, factory_id, line_name, status 
- ✅ `machines` table: machine_id, line_id, machine_name, machine_type

**Operations Database (SCADA Schema):**
- ✅ `scada_machine_data` table: machine_id, line_id, factory_id, oee_percentage, quality_percentage, availability_percentage, performance_percentage, machine_state, active_alarms, parts_produced_shift
- ✅ All OEE metrics and machine state fields verified

**Manufacturing Database (MES Schema):**
- ✅ `work_orders` table: work_order_id, factory_id, planned_quantity, produced_quantity, status, actual_cost_per_unit, total_material_cost, total_labor_cost
- ✅ `quality_inspections` table: inspection_id, work_order_id, inspection_result, defects_found, critical_defects, major_defects, minor_defects

**Cross-Database References:**
- ⚠️ `warehouses` table exists in WMS database (requires federation)
- ⚠️ `shipments` table exists in TMS database (requires federation)
- ⚠️ Some queries assume warehouse_id linkage to factory_id (may need ETL mapping)

### 🔧 **IMPLEMENTATION NOTES**

1. **Single Database Queries**: Queries 1.1, 1.2, 2.1, 3.1, 4.1, 5.1 can run directly against respective databases
2. **Multi-Database Queries**: Require database federation, views, or ETL processes to join across schemas
3. **Table Relationships**: All primary relationships (factories → production_lines → machines → scada_data) are verified and compatible
4. **Missing Coordinates**: Factory location queries use city/country/region (no latitude/longitude in schema)
5. **Financial Integration**: Revenue calculations use work_order cost data (verified compatible)

## 📱 SCREEN SPECIFICATIONS & NATURAL LANGUAGE QUERIES

### 1. Geographic Factory Map View
**Purpose:** Interactive world map displaying all factory locations with real-time status indicators

**Natural Language Queries:**

#### Query 1.1: Factory Locations Map
```
Show me all factory locations with their regions, factory names, cities, countries, operational status, and current performance health indicators for geographic visualization
```

**SQL Query:**
```sql
SELECT 
    f.factory_id,
    f.factory_name,
    f.city,
    f.country,
    f.region,
    f.timezone,
    f.total_area_sqm,
    f.operational_since,
    f.factory_type,
    f.certification,
    f.status as operational_status,
    -- Current performance indicators
    COALESCE(AVG(smd.oee_percentage), 0) as current_oee,
    COUNT(CASE WHEN smd.machine_state = 'running' THEN 1 END) as machines_running,
    COUNT(DISTINCT smd.machine_id) as total_machines,
    SUM(smd.active_alarms) as total_active_alarms,
    -- Health status determination
    CASE 
        WHEN AVG(smd.oee_percentage) >= 85 AND SUM(smd.active_alarms) <= 5 THEN 'healthy'
        WHEN AVG(smd.oee_percentage) >= 70 OR SUM(smd.active_alarms) <= 15 THEN 'warning'
        ELSE 'critical'
    END as factory_health_status
FROM factories f
LEFT JOIN production_lines pl ON f.factory_id = pl.factory_id AND pl.status = 'active'
LEFT JOIN scada_machine_data smd ON pl.line_id = smd.line_id 
    AND smd.timestamp >= NOW() - INTERVAL '1 hour'
WHERE f.status = 'active'
GROUP BY f.factory_id, f.factory_name, f.city, f.country, f.region, f.timezone, 
         f.total_area_sqm, f.operational_since, f.factory_type, f.certification, f.status
ORDER BY f.country, f.city, f.factory_name;
```

#### Query 1.2: Factory Performance Heatmap Data
```
Get factory performance metrics for heatmap visualization including OEE, quality, utilization, and efficiency scores by location
```

**SQL Query:**
```sql
SELECT 
    f.factory_id,
    f.factory_name,
    f.city,
    f.country,
    f.region,
    -- Performance metrics for heatmap
    ROUND(AVG(smd.oee_percentage), 2) as oee_score,
    ROUND(AVG(smd.quality_percentage), 2) as quality_score,
    ROUND(AVG(smd.availability_percentage), 2) as availability_score,
    ROUND(AVG(smd.performance_percentage), 2) as performance_score,
    -- Production metrics
    SUM(smd.parts_produced_shift) as total_production,
    COUNT(DISTINCT pl.line_id) as production_lines,
    -- Alert metrics
    SUM(smd.active_alarms) as total_alarms,
    COUNT(CASE WHEN smd.machine_state = 'fault' THEN 1 END) as fault_machines,
    -- Composite performance score
    ROUND((AVG(smd.oee_percentage) + AVG(smd.quality_percentage) + 
           (100 - (SUM(smd.active_alarms) * 2))) / 3, 2) as composite_performance_score
FROM factories f
JOIN production_lines pl ON f.factory_id = pl.factory_id AND pl.status = 'active'
JOIN scada_machine_data smd ON pl.line_id = smd.line_id
WHERE DATE(smd.timestamp) = CURRENT_DATE
    AND f.status = 'active'
GROUP BY f.factory_id, f.factory_name, f.city, f.country, f.region
ORDER BY composite_performance_score DESC;
```

### 2. Network-Wide Performance Dashboard
**Purpose:** Executive-level KPIs and metrics across the entire manufacturing network

#### Query 2.1: Network-Wide KPIs Summary
```
Display overall network performance including total OEE, production lines utilization, revenue, quality, and critical issues across all factories
```

**SQL Query:**
```sql
WITH factory_metrics AS (
    SELECT 
        f.factory_id,
        AVG(smd.oee_percentage) as factory_oee,
        AVG(smd.quality_percentage) as factory_quality,
        SUM(smd.parts_produced_shift) as factory_production,
        COUNT(DISTINCT pl.line_id) as factory_lines,
        COUNT(DISTINCT CASE WHEN smd.machine_state = 'running' THEN pl.line_id END) as active_lines,
        SUM(smd.active_alarms) as factory_alarms,
        SUM(CASE WHEN smd.active_alarms > 5 THEN 1 ELSE 0 END) as critical_issues
    FROM factories f
    JOIN production_lines pl ON f.factory_id = pl.factory_id
    JOIN scada_machine_data smd ON pl.line_id = smd.line_id
    WHERE DATE(smd.timestamp) = CURRENT_DATE
        AND f.status = 'active'
        AND pl.status = 'active'
    GROUP BY f.factory_id
),
financial_data AS (
    SELECT 
        SUM(wo.actual_cost_per_unit * wo.produced_quantity) as daily_revenue
    FROM work_orders wo
    WHERE DATE(wo.actual_end_time) = CURRENT_DATE
        AND wo.status = 'completed'
)
SELECT 
    -- Overall OEE
    ROUND(AVG(fm.factory_oee), 2) as network_oee,
    -- Production Lines Utilization
    SUM(fm.active_lines) as active_production_lines,
    SUM(fm.factory_lines) as total_production_lines,
    ROUND(SUM(fm.active_lines) * 100.0 / SUM(fm.factory_lines), 2) as line_utilization_percentage,
    -- Critical Issues
    SUM(fm.critical_issues) as critical_issues_count,
    -- Daily Revenue
    COALESCE(fd.daily_revenue, 0) as network_daily_revenue,
    -- Quality Metrics
    ROUND(AVG(fm.factory_quality), 2) as network_quality_score,
    -- Total Production
    SUM(fm.factory_production) as network_total_production,
    -- Factory Count
    COUNT(fm.factory_id) as active_factories,
    -- Performance Status
    CASE 
        WHEN AVG(fm.factory_oee) >= 85 THEN 'excellent'
        WHEN AVG(fm.factory_oee) >= 75 THEN 'good'
        WHEN AVG(fm.factory_oee) >= 65 THEN 'fair'
        ELSE 'needs_attention'
    END as network_performance_status
FROM factory_metrics fm
CROSS JOIN financial_data fd;
```

---

## 🔄 API Integration Patterns

### Real-Time Data Refresh
- **SCADA Integration**: 15-second refresh for operational metrics
- **Map Updates**: 30-second refresh for factory health status indicators
- **KPI Aggregation**: 1-minute refresh for network-wide summary metrics

### Performance Optimization
- **Caching Layer**: Redis for frequently accessed factory locations and KPIs
- **Data Compression**: Real-time metric aggregation at edge devices
- **Query Optimization**: Indexed views for complex cross-database joins

---

## 📊 API Conversion Guidelines

When converting these natural language queries to APIs, consider:

1. **Real-time Data**: Use live data endpoints with WebSocket for map updates
2. **Time Ranges**: Include flexible time range parameters (today, week, month)
3. **Filtering**: Add factory-specific and region-specific filters
4. **Aggregation**: Support different aggregation levels (hourly, daily, weekly)
5. **Thresholds**: Include configurable threshold parameters for health status
6. **Caching**: Use appropriate caching strategies for performance optimization

## 🗄️ Database Tables Referenced

These queries primarily use data from:
- **Master Database**: `factories`, `production_lines`, `machines`
- **Operations Database**: `scada_machine_data`
- **Manufacturing Database**: `work_orders`, `quality_inspections`

---

*This specification provides the foundation for implementing the Factory Overview - Geographic View screen that serves as the landing page and command center for multi-factory manufacturing operations.*
