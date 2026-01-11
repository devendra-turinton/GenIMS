# Asset Performance Intelligence: Complete Application Specification

## 🎯 OBJECTIVE

**End-to-End Asset Management & Maintenance Intelligence**

Empower enterprises to achieve **asset excellence** through **real-time performance monitoring, predictive maintenance, and intelligent asset lifecycle management** across the entire manufacturing network. Enable users to:

**1. ASSET MONITORING & UTILIZATION TRACKING**
- Visualize **real-time asset status, utilization rates, and performance metrics** through interactive dashboards with drill-down capabilities
- Track **4 critical asset KPIs**: Total Assets (245), Asset Utilization (87.3%), MTBF (45.2 days), and Maintenance Cost (Monthly)
- Integrate **asset hierarchy data** (Factory → Line → Machine → Component) with real-time operational status

**2. RELIABILITY & PERFORMANCE ANALYTICS**
- Query, correlate, and synthesize maintenance data across **all maintenance types** spanning Preventive, Corrective, Breakdown, and Predictive Maintenance
- Enable **Reliability Intelligence** with MTBF (Mean Time Between Failures), MTTR (Mean Time To Repair), and OEE (Overall Equipment Effectiveness) tracking
- Deploy **Predictive Maintenance Engine** to forecast equipment failures, optimize PM schedules, and reduce unplanned downtime

**3. WORK ORDER & MAINTENANCE MANAGEMENT**
- Support **End-to-End Work Order Tracking** from request creation through scheduling, execution, and completion
- Provide **PM Schedule Optimization** with calendar-based, meter-based, and condition-based maintenance planning
- Deliver **Technician & Resource Management**: Skills-based assignment, labor utilization, and workforce scheduling

**4. SPARE PARTS & MRO INVENTORY INTELLIGENCE**
- Synthesize **MRO inventory analytics**: Stock levels, reorder points, criticality classification, and stockout risk
- Support **multi-level drill-down navigation**: Asset Overview → Machine Detail → Work Order History → Parts Usage → Cost Analysis
- Provide **strategic recommendations** for:
  - PM schedule optimization and maintenance frequency adjustment
  - Spare parts inventory optimization and critical parts management
  - Technician skill development and resource allocation
  - Asset lifecycle decisions (repair vs. replace analysis)
  - Service contract evaluation and vendor performance
  - Energy efficiency and asset modernization opportunities

**5. FINANCIAL IMPACT QUANTIFICATION (INR-Based)**
- Quantify all maintenance-related cost metrics in **Indian Rupees (INR)**:
  - `maintenance_cost_inr`, `labor_cost_inr`, `parts_cost_inr`
  - `downtime_cost_inr`, `production_loss_inr`
  - `contractor_cost_inr`, `service_contract_cost_inr`
- Enable **maintenance cost-benefit analysis** for repair vs. replace decisions and PM investment ROI

**OUTCOME:** Enable enterprises to maximize asset availability, reduce unplanned downtime, optimize maintenance costs, and extend asset lifecycle through intelligent maintenance analytics and proactive asset management.

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
          "asset_id": "AST001",
          "asset_name": "CNC Machining Center",
          "asset_status": "operational",
          "utilization_percentage": 87.3,
          "mtbf_days": 45.2
        },
        {
          "asset_id": "AST002",
          "asset_name": "Hydraulic Press",
          "asset_status": "under_maintenance",
          "utilization_percentage": 72.5,
          "mtbf_days": 38.1
        }
      ],
      "nested_level": [
        {
          "asset_performance": {
            "asset_details": {
              "asset_id": "AST001",
              "asset_name": "CNC Machining Center",
              "factory": "Factory A - Pune",
              "criticality": "critical"
            },
            "reliability_metrics": {
              "mtbf_hours": 1084.8,
              "mttr_hours": 4.2,
              "availability_pct": 96.5,
              "oee_pct": 82.3
            },
            "maintenance_summary": {
              "open_work_orders": 3,
              "pm_compliance_pct": 94.2,
              "ytd_maintenance_cost": 450000,
              "next_pm_date": "2026-01-15"
            }
          }
        }
      ]
    }
  }
}

## 📝 ADDITIONAL COMMENTS

**Fallback Scenario:**
If no relevant asset data, maintenance records, or performance information is found in the GenIMS databases, politely inform the user that the requested asset intelligence is not currently available. Offer to help refine the query for specific asset types, maintenance categories, or performance metrics, suggest alternative approaches for asset analysis, or provide expertise based on general best practices in asset management, reliability engineering, maintenance optimization, or equipment lifecycle management.

**Response Guidelines:**
1. **Asset-Centric Organization**: Organize responses by asset criticality, maintenance urgency, and performance impact, prioritizing insights that most directly affect production availability, equipment reliability, and maintenance efficiency.
2. **INR-Based Financial Analysis**: All amount-related terms are in Indian Rupees (INR) only for maintenance operations. Clearly state this in every analysis and use consistent notation (e.g., maintenance_cost_inr, labor_cost_inr, parts_cost_inr, downtime_cost_inr).
3. **Reliability Focus**: Focus on MTBF trends, MTTR improvements, availability percentages, and OEE metrics, emphasizing measurable outcomes such as reduced downtime, improved asset utilization, faster repair times, or enhanced equipment reliability.
4. **Concise Maintenance Intelligence**: Deliver concise, actionable information—avoid unnecessary detail, and present only the most critical findings related to equipment failures, PM compliance, work order backlogs, and spare parts availability.
5. **Structured Asset Format**: Use a structured format (bulleted lists, asset status tables, or clear maintenance categories) so asset information can be quickly scanned for operational review, maintenance planning, or management reporting.
6. **Proactive Failure Prediction**: Proactively highlight potential equipment failures, such as degrading MTBF trends, overdue PM schedules, recurring failure patterns, spare parts shortages, or approaching end-of-life assets, and suggest preventive strategies.
7. **Contextual Maintenance Insights**: For each key asset finding, provide a brief explanation (200–300 words) that contextualizes the insight, explains its significance for production continuity, and outlines implications for maintenance planning, reliability improvement, or capital investment decisions.

This approach ensures that Asset Performance Intelligence responses are reliability-focused, maintenance-ready, and strategically relevant for maintenance managers, reliability engineers, and plant leadership, while maintaining transparency about data limitations and supporting continuous asset improvement.

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

**Asset Performance Intelligence Planner:**
You are a domain expert in reliability engineering and maintenance management, with deep specialization in Asset Performance Intelligence across multi-site manufacturing operations. Your expertise covers equipment reliability analysis, preventive and predictive maintenance optimization, work order management, spare parts inventory control, and asset lifecycle management. You focus on maximizing asset availability, reducing unplanned downtime, optimizing maintenance costs, and extending equipment useful life. You analyze and correlate equipment failures with operational patterns, validate maintenance strategies through reliability metrics and cost analysis, and manage asset performance across diverse equipment types. Your work supports maintenance decisions, reliability improvement initiatives, capital investment planning, and enterprise-wide asset excellence, enabling data-driven recommendations that enhance equipment performance, reduce maintenance costs, improve production uptime, and build robust maintenance management systems across all manufacturing facilities.



## 🔐 SELECTED ROLES & PERMISSIONS

| Role | Access Level | Permissions |
|------|-------------|-------------|
| **Maintenance Director** | Full Asset Access | View all assets, maintenance costs, reliability metrics, strategic recommendations |
| **Reliability Engineer** | Reliability & Analytics | Analyze failure patterns, MTBF/MTTR trends, predictive maintenance, root cause analysis |
| **Maintenance Manager** | Work Order & Resource Control | Manage work orders, PM schedules, technician assignments, spare parts |
| **Maintenance Planner** | Planning & Scheduling | Create/schedule work orders, manage PM calendars, coordinate resources |
| **Maintenance Technician** | Execution Access | View assigned work orders, record labor time, update task completion |
| **Storekeeper** | MRO Inventory Control | Manage spare parts inventory, issue parts, track stock levels |
| **Operations Manager** | Production Integration | View asset status affecting production, downtime reports, OEE metrics |
| **Finance Analyst** | Cost Analytics | Read-only access to maintenance costs, budgets, cost center analysis |

## 🗄️ DATABASES NEEDED

### Core Databases (Required for Asset Performance Intelligence)
1. **CMMS Database** - maintenance_assets, work_orders, pm_schedules, asset_reliability_metrics
2. **Master Database** - factories, production_lines, machines
3. **Operational Database** - machine_faults, downtime_events

### Optional Databases (For Extended Functionality)
4. **MES Database** - production_runs, quality_inspections (for OEE correlation)
5. **ERP Database** - purchase_orders, suppliers (for spare parts procurement)

## 🔍 DATABASE COMPATIBILITY & VERIFICATION STATUS

### ✅ **VERIFIED COMPATIBLE QUERIES** 
These queries have been validated against actual GenIMS database schemas:

- **Query 1.1 & 1.2**: Asset Overview Dashboard & Critical Assets ✓
- **Query 2.1**: Reliability Metrics (MTBF, MTTR, Availability) ✓  
- **Query 3.1**: Work Order Status & Backlog ✓
- **Query 4.1**: PM Schedule Compliance ✓
- **Query 5.1**: Maintenance Cost Analysis ✓

### ⚠️ **CROSS-DATABASE QUERIES**
These queries reference multiple database schemas and may require database federation or ETL processes:

- **Query 6.1**: Asset ↔ Production Impact (requires CMMS & MES integration)
- **Query 7.1**: Spare Parts ↔ Work Order Correlation (requires CMMS & ERP integration)

### 📋 **KEY DATABASE SCHEMA VALIDATION**

**CMMS Database (Maintenance Management Schema):**
- ✅ `maintenance_assets` table: asset_id, asset_type, asset_status, criticality_rating, downtime_cost_per_hour, maintenance_strategy
- ✅ `work_orders` table: work_order_id, wo_type, priority, wo_status, scheduled_start_date, actual_duration_hours
- ✅ `pm_schedules` table: pm_schedule_id, schedule_type, frequency_type, next_due_date, last_completed_date
- ✅ `asset_reliability_metrics` table: mtbf_hours, mttr_hours, availability_pct, oee_pct, total_maintenance_cost
- ✅ `mro_parts` table: part_number, current_stock, reorder_point, criticality, lead_time_days
- ✅ `maintenance_technicians` table: technician_id, skill_level, trade, certifications

**Master Database (Base Schema):**
- ✅ `factories` table: factory_id, factory_name, city, country
- ✅ `production_lines` table: line_id, line_name, factory_id
- ✅ `machines` table: machine_id, machine_name, machine_type, line_id

**Operational Database (Machine Operations Schema):**
- ✅ `machine_faults` table: fault_id, machine_id, fault_type, fault_severity, downtime_minutes
- ✅ `downtime_events` table: event_id, machine_id, downtime_type, start_time, end_time

---

## 🚀 ASSET PERFORMANCE INTELLIGENCE QUERIES

## 1. Asset Overview & Monitoring

### Query 1.1: Asset Performance Dashboard
```
Show all assets across factories with their current status, utilization rates, criticality, and key performance metrics
```

**SQL Query:**
```sql
WITH asset_metrics AS (
    SELECT 
        ma.asset_id,
        ma.asset_number,
        ma.asset_name,
        ma.asset_type,
        ma.asset_category,
        ma.criticality_rating,
        ma.asset_status,
        ma.factory_id,
        f.factory_name,
        ma.line_id,
        pl.line_name,
        ma.maintenance_strategy,
        ma.downtime_cost_per_hour,
        ma.replacement_cost,
        -- Get latest reliability metrics
        arm.availability_pct,
        arm.mtbf_hours,
        arm.mttr_hours,
        arm.oee_pct,
        arm.total_maintenance_cost as period_maintenance_cost,
        arm.unplanned_downtime_hours,
        arm.number_of_failures
    FROM maintenance_assets ma
    LEFT JOIN factories f ON ma.factory_id = f.factory_id
    LEFT JOIN production_lines pl ON ma.line_id = pl.line_id
    LEFT JOIN asset_reliability_metrics arm ON ma.asset_id = arm.asset_id
        AND arm.period_type = 'monthly'
        AND arm.period_end_date = (
            SELECT MAX(period_end_date) 
            FROM asset_reliability_metrics 
            WHERE asset_id = ma.asset_id AND period_type = 'monthly'
        )
    WHERE ma.is_active = true
),
work_order_summary AS (
    SELECT 
        wo.asset_id,
        COUNT(CASE WHEN wo.wo_status NOT IN ('completed', 'closed', 'cancelled') THEN 1 END) as open_work_orders,
        COUNT(CASE WHEN wo.wo_type = 'breakdown' AND wo.wo_status NOT IN ('completed', 'closed') THEN 1 END) as open_breakdowns,
        COUNT(CASE WHEN wo.priority IN ('emergency', 'urgent') AND wo.wo_status NOT IN ('completed', 'closed') THEN 1 END) as urgent_work_orders
    FROM work_orders wo
    WHERE wo.created_at >= CURRENT_DATE - INTERVAL '30 days'
    GROUP BY wo.asset_id
)
SELECT 
    am.asset_id,
    am.asset_number,
    am.asset_name,
    am.asset_type,
    am.asset_category,
    am.criticality_rating,
    am.asset_status,
    am.factory_name,
    am.line_name,
    am.maintenance_strategy,
    am.downtime_cost_per_hour,
    am.replacement_cost,
    ROUND(am.availability_pct, 2) as availability_pct,
    ROUND(am.mtbf_hours / 24, 1) as mtbf_days,
    ROUND(am.mttr_hours, 2) as mttr_hours,
    ROUND(am.oee_pct, 2) as oee_pct,
    am.period_maintenance_cost,
    am.unplanned_downtime_hours,
    am.number_of_failures,
    COALESCE(wos.open_work_orders, 0) as open_work_orders,
    COALESCE(wos.open_breakdowns, 0) as open_breakdowns,
    COALESCE(wos.urgent_work_orders, 0) as urgent_work_orders,
    CASE 
        WHEN am.asset_status = 'breakdown' THEN 'critical'
        WHEN COALESCE(wos.open_breakdowns, 0) > 0 THEN 'attention_required'
        WHEN am.availability_pct < 85 THEN 'underperforming'
        WHEN am.availability_pct >= 95 THEN 'excellent'
        ELSE 'normal'
    END as health_status
FROM asset_metrics am
LEFT JOIN work_order_summary wos ON am.asset_id = wos.asset_id
ORDER BY 
    CASE am.criticality_rating WHEN 'critical' THEN 1 WHEN 'high' THEN 2 WHEN 'medium' THEN 3 ELSE 4 END,
    am.availability_pct ASC;
```

### Query 1.2: Critical Assets Requiring Attention
```
Identify high-value critical assets that need immediate attention based on performance degradation, open breakdowns, or overdue maintenance
```

**SQL Query:**
```sql
WITH critical_asset_issues AS (
    SELECT 
        ma.asset_id,
        ma.asset_number,
        ma.asset_name,
        ma.criticality_rating,
        ma.asset_status,
        ma.downtime_cost_per_hour,
        f.factory_name,
        -- Check for open breakdown work orders
        COUNT(DISTINCT CASE WHEN wo.wo_type = 'breakdown' AND wo.wo_status NOT IN ('completed', 'closed') 
            THEN wo.work_order_id END) as open_breakdowns,
        -- Check for overdue PM
        COUNT(DISTINCT CASE WHEN ps.next_due_date < CURRENT_DATE 
            THEN ps.pm_schedule_id END) as overdue_pm_count,
        -- Recent failures
        COUNT(DISTINCT CASE WHEN mf.fault_timestamp >= CURRENT_DATE - INTERVAL '7 days' 
            THEN mf.fault_id END) as recent_failures_7d,
        -- Downtime in last 30 days
        COALESCE(SUM(de.duration_minutes), 0) / 60.0 as downtime_hours_30d
    FROM maintenance_assets ma
    JOIN factories f ON ma.factory_id = f.factory_id
    LEFT JOIN work_orders wo ON ma.asset_id = wo.asset_id
    LEFT JOIN pm_schedules ps ON ma.asset_id = ps.asset_id AND ps.schedule_status = 'active'
    LEFT JOIN machine_faults mf ON ma.machine_id = mf.machine_id
    LEFT JOIN downtime_events de ON ma.machine_id = de.machine_id
        AND de.start_time >= CURRENT_DATE - INTERVAL '30 days'
    WHERE ma.is_active = true
        AND ma.criticality_rating IN ('critical', 'high')
    GROUP BY ma.asset_id, ma.asset_number, ma.asset_name, ma.criticality_rating, 
             ma.asset_status, ma.downtime_cost_per_hour, f.factory_name
)
SELECT 
    cai.asset_id,
    cai.asset_number,
    cai.asset_name,
    cai.criticality_rating,
    cai.asset_status,
    cai.factory_name,
    cai.downtime_cost_per_hour,
    cai.open_breakdowns,
    cai.overdue_pm_count,
    cai.recent_failures_7d,
    ROUND(cai.downtime_hours_30d, 1) as downtime_hours_30d,
    ROUND(cai.downtime_hours_30d * cai.downtime_cost_per_hour, 0) as estimated_downtime_cost,
    -- Determine issue type and priority
    CASE 
        WHEN cai.asset_status = 'breakdown' THEN 'Current Breakdown - Immediate Action Required'
        WHEN cai.open_breakdowns > 0 THEN 'Open Breakdown Work Order - Expedite Repair'
        WHEN cai.overdue_pm_count > 0 THEN 'Overdue PM - Schedule Immediately'
        WHEN cai.recent_failures_7d >= 3 THEN 'Recurring Failures - Root Cause Investigation'
        WHEN cai.downtime_hours_30d > 24 THEN 'High Downtime - Reliability Review Needed'
        ELSE 'Monitor - Trending Issues'
    END as issue_description,
    CASE 
        WHEN cai.asset_status = 'breakdown' OR cai.open_breakdowns > 0 THEN 'critical'
        WHEN cai.overdue_pm_count > 0 OR cai.recent_failures_7d >= 3 THEN 'high'
        WHEN cai.downtime_hours_30d > 24 THEN 'medium'
        ELSE 'low'
    END as priority_level
FROM critical_asset_issues cai
WHERE cai.asset_status = 'breakdown'
    OR cai.open_breakdowns > 0
    OR cai.overdue_pm_count > 0
    OR cai.recent_failures_7d >= 2
    OR cai.downtime_hours_30d > 24
ORDER BY 
    CASE 
        WHEN cai.asset_status = 'breakdown' THEN 1
        WHEN cai.open_breakdowns > 0 THEN 2
        WHEN cai.overdue_pm_count > 0 THEN 3
        ELSE 4
    END,
    cai.downtime_cost_per_hour DESC;
```

### Query 1.3: Asset Utilization by Factory
```
Calculate asset utilization rates by factory showing operating hours vs. available hours with efficiency trends
```

**SQL Query:**
```sql
SELECT 
    f.factory_id,
    f.factory_name,
    f.city,
    COUNT(DISTINCT ma.asset_id) as total_assets,
    COUNT(DISTINCT CASE WHEN ma.asset_status = 'operational' THEN ma.asset_id END) as operational_assets,
    COUNT(DISTINCT CASE WHEN ma.asset_status = 'under_maintenance' THEN ma.asset_id END) as under_maintenance,
    COUNT(DISTINCT CASE WHEN ma.asset_status = 'breakdown' THEN ma.asset_id END) as in_breakdown,
    SUM(arm.operating_hours) as total_operating_hours,
    SUM(arm.total_hours) as total_available_hours,
    ROUND(SUM(arm.operating_hours) * 100.0 / NULLIF(SUM(arm.total_hours), 0), 2) as utilization_pct,
    ROUND(AVG(arm.availability_pct), 2) as avg_availability_pct,
    ROUND(AVG(arm.oee_pct), 2) as avg_oee_pct,
    SUM(arm.unplanned_downtime_hours) as total_unplanned_downtime,
    SUM(arm.planned_downtime_hours) as total_planned_downtime,
    SUM(arm.total_maintenance_cost) as total_maintenance_cost,
    SUM(arm.number_of_failures) as total_failures,
    ROUND(AVG(arm.mtbf_hours), 1) as avg_mtbf_hours,
    ROUND(AVG(arm.mttr_hours), 1) as avg_mttr_hours
FROM factories f
JOIN maintenance_assets ma ON f.factory_id = ma.factory_id
LEFT JOIN asset_reliability_metrics arm ON ma.asset_id = arm.asset_id
    AND arm.period_type = 'monthly'
    AND arm.period_end_date >= CURRENT_DATE - INTERVAL '30 days'
WHERE f.status = 'active'
    AND ma.is_active = true
GROUP BY f.factory_id, f.factory_name, f.city
ORDER BY utilization_pct DESC;
```

## 2. Reliability Metrics & Analysis

### Query 2.1: MTBF/MTTR Trends by Asset
```
Show MTBF and MTTR trends over time for critical assets to identify reliability improvements or degradation
```

**SQL Query:**
```sql
WITH monthly_trends AS (
    SELECT 
        arm.asset_id,
        ma.asset_name,
        ma.criticality_rating,
        f.factory_name,
        arm.period_start_date,
        DATE_TRUNC('month', arm.period_start_date) as trend_month,
        arm.mtbf_hours,
        arm.mttr_hours,
        arm.availability_pct,
        arm.number_of_failures,
        arm.unplanned_downtime_hours,
        arm.total_maintenance_cost
    FROM asset_reliability_metrics arm
    JOIN maintenance_assets ma ON arm.asset_id = ma.asset_id
    JOIN factories f ON ma.factory_id = f.factory_id
    WHERE arm.period_type = 'monthly'
        AND arm.period_start_date >= CURRENT_DATE - INTERVAL '12 months'
        AND ma.criticality_rating IN ('critical', 'high')
)
SELECT 
    mt.asset_id,
    mt.asset_name,
    mt.criticality_rating,
    mt.factory_name,
    mt.trend_month,
    ROUND(mt.mtbf_hours, 1) as mtbf_hours,
    ROUND(mt.mtbf_hours / 24, 1) as mtbf_days,
    ROUND(mt.mttr_hours, 2) as mttr_hours,
    ROUND(mt.availability_pct, 2) as availability_pct,
    mt.number_of_failures,
    ROUND(mt.unplanned_downtime_hours, 1) as unplanned_downtime_hours,
    mt.total_maintenance_cost,
    -- Calculate trend vs previous month
    LAG(mt.mtbf_hours) OVER (PARTITION BY mt.asset_id ORDER BY mt.trend_month) as prev_mtbf,
    ROUND(mt.mtbf_hours - LAG(mt.mtbf_hours) OVER (PARTITION BY mt.asset_id ORDER BY mt.trend_month), 1) as mtbf_change,
    LAG(mt.mttr_hours) OVER (PARTITION BY mt.asset_id ORDER BY mt.trend_month) as prev_mttr,
    ROUND(mt.mttr_hours - LAG(mt.mttr_hours) OVER (PARTITION BY mt.asset_id ORDER BY mt.trend_month), 2) as mttr_change,
    CASE 
        WHEN mt.mtbf_hours > LAG(mt.mtbf_hours) OVER (PARTITION BY mt.asset_id ORDER BY mt.trend_month) * 1.1 THEN 'improving'
        WHEN mt.mtbf_hours < LAG(mt.mtbf_hours) OVER (PARTITION BY mt.asset_id ORDER BY mt.trend_month) * 0.9 THEN 'degrading'
        ELSE 'stable'
    END as reliability_trend
FROM monthly_trends mt
ORDER BY mt.asset_id, mt.trend_month DESC;
```

### Query 2.2: Failure Pattern Analysis
```
Analyze failure patterns by failure type, asset category, and time to identify recurring issues
```

**SQL Query:**
```sql
WITH failure_analysis AS (
    SELECT 
        ma.asset_id,
        ma.asset_name,
        ma.asset_category,
        ma.asset_type,
        f.factory_name,
        fc.failure_class,
        fc.failure_type,
        fc.failure_description,
        wo.failure_mode,
        COUNT(wo.work_order_id) as failure_count,
        SUM(wo.downtime_minutes) as total_downtime_minutes,
        AVG(wo.actual_duration_hours) as avg_repair_hours,
        SUM(wo.actual_total_cost) as total_repair_cost,
        MAX(wo.created_at) as last_failure_date,
        MIN(wo.created_at) as first_failure_date
    FROM work_orders wo
    JOIN maintenance_assets ma ON wo.asset_id = ma.asset_id
    JOIN factories f ON ma.factory_id = f.factory_id
    LEFT JOIN failure_codes fc ON wo.failure_code = fc.failure_code
    WHERE wo.wo_type IN ('breakdown', 'corrective')
        AND wo.created_at >= CURRENT_DATE - INTERVAL '12 months'
    GROUP BY ma.asset_id, ma.asset_name, ma.asset_category, ma.asset_type,
             f.factory_name, fc.failure_class, fc.failure_type, fc.failure_description, wo.failure_mode
)
SELECT 
    fa.asset_name,
    fa.asset_category,
    fa.factory_name,
    fa.failure_class,
    fa.failure_type,
    fa.failure_description,
    fa.failure_count,
    ROUND(fa.total_downtime_minutes / 60.0, 1) as total_downtime_hours,
    ROUND(fa.avg_repair_hours, 2) as avg_repair_hours,
    fa.total_repair_cost,
    fa.first_failure_date,
    fa.last_failure_date,
    DATE_PART('days', fa.last_failure_date - fa.first_failure_date) / NULLIF(fa.failure_count - 1, 0) as avg_days_between_failures,
    CASE 
        WHEN fa.failure_count >= 5 THEN 'chronic_issue'
        WHEN fa.failure_count >= 3 THEN 'recurring_problem'
        WHEN fa.failure_count >= 2 THEN 'repeat_failure'
        ELSE 'isolated_incident'
    END as failure_pattern,
    CASE 
        WHEN fa.failure_count >= 5 THEN 'Root cause analysis and design modification required'
        WHEN fa.failure_count >= 3 THEN 'Review PM tasks and add predictive monitoring'
        WHEN fa.failure_count >= 2 THEN 'Verify repair quality and parts used'
        ELSE 'Document and monitor'
    END as recommended_action
FROM failure_analysis fa
WHERE fa.failure_count >= 2
ORDER BY fa.failure_count DESC, fa.total_downtime_minutes DESC;
```

## 3. Work Order Management

### Query 3.1: Work Order Status Overview
```
Show work order status summary by type, priority, and factory with backlog and aging analysis
```

**SQL Query:**
```sql
WITH wo_summary AS (
    SELECT 
        f.factory_id,
        f.factory_name,
        wo.wo_type,
        wo.priority,
        wo.wo_status,
        COUNT(wo.work_order_id) as wo_count,
        SUM(wo.estimated_duration_hours) as total_estimated_hours,
        SUM(wo.estimated_cost) as total_estimated_cost,
        AVG(DATE_PART('days', CURRENT_DATE - wo.created_at::date)) as avg_age_days,
        COUNT(CASE WHEN wo.scheduled_start_date < CURRENT_DATE AND wo.wo_status NOT IN ('completed', 'closed', 'cancelled') 
            THEN 1 END) as overdue_count
    FROM work_orders wo
    JOIN maintenance_assets ma ON wo.asset_id = ma.asset_id
    JOIN factories f ON ma.factory_id = f.factory_id
    WHERE wo.created_at >= CURRENT_DATE - INTERVAL '90 days'
    GROUP BY f.factory_id, f.factory_name, wo.wo_type, wo.priority, wo.wo_status
)
SELECT 
    ws.factory_name,
    ws.wo_type,
    ws.priority,
    ws.wo_status,
    ws.wo_count,
    ROUND(ws.total_estimated_hours, 1) as total_estimated_hours,
    ws.total_estimated_cost,
    ROUND(ws.avg_age_days, 1) as avg_age_days,
    ws.overdue_count,
    CASE 
        WHEN ws.wo_status IN ('created', 'planned') AND ws.avg_age_days > 14 THEN 'backlog_aging'
        WHEN ws.wo_status = 'on_hold' AND ws.avg_age_days > 7 THEN 'stuck'
        WHEN ws.overdue_count > 0 THEN 'overdue'
        ELSE 'normal'
    END as status_concern
FROM wo_summary ws
ORDER BY 
    CASE ws.priority WHEN 'emergency' THEN 1 WHEN 'urgent' THEN 2 WHEN 'high' THEN 3 WHEN 'medium' THEN 4 ELSE 5 END,
    ws.wo_count DESC;
```

### Query 3.2: Work Order Backlog Analysis
```
Identify work order backlog by priority and calculate required resources to clear backlog
```

**SQL Query:**
```sql
SELECT 
    f.factory_name,
    wo.priority,
    wo.wo_type,
    COUNT(wo.work_order_id) as backlog_count,
    SUM(wo.estimated_duration_hours) as total_hours_required,
    SUM(wo.estimated_cost) as total_estimated_cost,
    MIN(wo.created_at) as oldest_wo_date,
    MAX(DATE_PART('days', CURRENT_DATE - wo.created_at::date)) as max_age_days,
    AVG(DATE_PART('days', CURRENT_DATE - wo.created_at::date)) as avg_age_days,
    -- Calculate technician-days to clear (assuming 8 hours per day)
    ROUND(SUM(wo.estimated_duration_hours) / 8, 1) as technician_days_required,
    -- Count overdue items
    COUNT(CASE WHEN wo.scheduled_start_date < CURRENT_DATE THEN 1 END) as overdue_count,
    STRING_AGG(DISTINCT ma.asset_name, ', ' ORDER BY ma.asset_name) as affected_assets
FROM work_orders wo
JOIN maintenance_assets ma ON wo.asset_id = ma.asset_id
JOIN factories f ON ma.factory_id = f.factory_id
WHERE wo.wo_status NOT IN ('completed', 'closed', 'cancelled')
GROUP BY f.factory_name, wo.priority, wo.wo_type
HAVING COUNT(wo.work_order_id) > 0
ORDER BY 
    CASE wo.priority WHEN 'emergency' THEN 1 WHEN 'urgent' THEN 2 WHEN 'high' THEN 3 WHEN 'medium' THEN 4 ELSE 5 END,
    backlog_count DESC;
```

## 4. Preventive Maintenance

### Query 4.1: PM Schedule Compliance
```
Calculate PM schedule compliance rates by factory and asset category showing on-time, late, and missed PMs
```

**SQL Query:**
```sql
WITH pm_execution AS (
    SELECT 
        ps.pm_schedule_id,
        ps.schedule_name,
        ma.asset_id,
        ma.asset_name,
        ma.asset_category,
        f.factory_id,
        f.factory_name,
        ps.next_due_date,
        ps.last_completed_date,
        wo.actual_end_date as execution_date,
        wo.wo_status,
        CASE 
            WHEN wo.actual_end_date <= ps.next_due_date THEN 'on_time'
            WHEN wo.actual_end_date <= ps.next_due_date + INTERVAL '7 days' THEN 'late'
            WHEN wo.actual_end_date IS NULL AND ps.next_due_date < CURRENT_DATE THEN 'overdue'
            ELSE 'pending'
        END as compliance_status
    FROM pm_schedules ps
    JOIN maintenance_assets ma ON ps.asset_id = ma.asset_id
    JOIN factories f ON ma.factory_id = f.factory_id
    LEFT JOIN work_orders wo ON ps.last_wo_id = wo.work_order_id
    WHERE ps.schedule_status = 'active'
        AND ps.is_active = true
)
SELECT 
    pe.factory_name,
    pe.asset_category,
    COUNT(DISTINCT pe.pm_schedule_id) as total_pm_schedules,
    COUNT(CASE WHEN pe.compliance_status = 'on_time' THEN 1 END) as on_time_count,
    COUNT(CASE WHEN pe.compliance_status = 'late' THEN 1 END) as late_count,
    COUNT(CASE WHEN pe.compliance_status = 'overdue' THEN 1 END) as overdue_count,
    COUNT(CASE WHEN pe.compliance_status = 'pending' THEN 1 END) as pending_count,
    ROUND(COUNT(CASE WHEN pe.compliance_status = 'on_time' THEN 1 END) * 100.0 / 
          NULLIF(COUNT(CASE WHEN pe.compliance_status IN ('on_time', 'late') THEN 1 END), 0), 2) as on_time_compliance_pct,
    ROUND(COUNT(CASE WHEN pe.compliance_status IN ('on_time', 'late') THEN 1 END) * 100.0 / 
          NULLIF(COUNT(CASE WHEN pe.compliance_status != 'pending' THEN 1 END), 0), 2) as total_compliance_pct
FROM pm_execution pe
GROUP BY pe.factory_name, pe.asset_category
ORDER BY on_time_compliance_pct DESC;
```

### Query 4.2: Upcoming PM Schedule
```
Show upcoming preventive maintenance activities for the next 30 days with resource requirements
```

**SQL Query:**
```sql
SELECT 
    ps.pm_schedule_id,
    ps.schedule_code,
    ps.schedule_name,
    ps.pm_type,
    ma.asset_id,
    ma.asset_number,
    ma.asset_name,
    ma.criticality_rating,
    f.factory_name,
    pl.line_name,
    ps.schedule_type,
    ps.next_due_date,
    DATE_PART('days', ps.next_due_date - CURRENT_DATE) as days_until_due,
    ps.estimated_duration_hours,
    ps.required_skills,
    ps.required_tools,
    ps.required_parts,
    ps.last_completed_date,
    DATE_PART('days', CURRENT_DATE - ps.last_completed_date) as days_since_last_pm,
    CASE 
        WHEN ps.next_due_date < CURRENT_DATE THEN 'overdue'
        WHEN ps.next_due_date <= CURRENT_DATE + INTERVAL '7 days' THEN 'due_this_week'
        WHEN ps.next_due_date <= CURRENT_DATE + INTERVAL '14 days' THEN 'due_next_week'
        ELSE 'scheduled'
    END as urgency_status
FROM pm_schedules ps
JOIN maintenance_assets ma ON ps.asset_id = ma.asset_id
JOIN factories f ON ma.factory_id = f.factory_id
LEFT JOIN production_lines pl ON ma.line_id = pl.line_id
WHERE ps.schedule_status = 'active'
    AND ps.is_active = true
    AND ps.next_due_date <= CURRENT_DATE + INTERVAL '30 days'
ORDER BY 
    CASE 
        WHEN ps.next_due_date < CURRENT_DATE THEN 1
        WHEN ps.next_due_date <= CURRENT_DATE + INTERVAL '7 days' THEN 2
        ELSE 3
    END,
    ps.next_due_date ASC,
    ma.criticality_rating;
```

## 5. Maintenance Cost Analysis

### Query 5.1: Maintenance Cost Summary
```
Analyze maintenance costs by factory, asset category, and cost type showing budget vs. actual
```

**SQL Query:**
```sql
WITH cost_summary AS (
    SELECT 
        f.factory_id,
        f.factory_name,
        ma.asset_category,
        mc.cost_type,
        SUM(mc.cost_amount) as actual_cost,
        COUNT(DISTINCT mc.work_order_id) as work_order_count
    FROM maintenance_costs mc
    JOIN work_orders wo ON mc.work_order_id = wo.work_order_id
    JOIN maintenance_assets ma ON mc.asset_id = ma.asset_id
    JOIN factories f ON ma.factory_id = f.factory_id
    WHERE mc.cost_date >= DATE_TRUNC('year', CURRENT_DATE)
    GROUP BY f.factory_id, f.factory_name, ma.asset_category, mc.cost_type
),
budget_data AS (
    SELECT 
        mcc.cost_center_id,
        f.factory_id,
        mcc.annual_budget,
        mcc.ytd_actual_cost
    FROM maintenance_cost_centers mcc
    JOIN factories f ON mcc.cost_center_code LIKE f.factory_id || '%'
    WHERE mcc.is_active = true
)
SELECT 
    cs.factory_name,
    cs.asset_category,
    cs.cost_type,
    cs.actual_cost,
    cs.work_order_count,
    ROUND(cs.actual_cost / NULLIF(cs.work_order_count, 0), 2) as avg_cost_per_wo,
    SUM(cs.actual_cost) OVER (PARTITION BY cs.factory_name) as factory_total_cost,
    ROUND(cs.actual_cost * 100.0 / NULLIF(SUM(cs.actual_cost) OVER (PARTITION BY cs.factory_name), 0), 2) as pct_of_factory_total
FROM cost_summary cs
ORDER BY cs.factory_name, cs.actual_cost DESC;
```

### Query 5.2: Asset Cost vs. Value Analysis
```
Compare maintenance costs against asset value to identify candidates for replacement
```

**SQL Query:**
```sql
WITH asset_costs AS (
    SELECT 
        ma.asset_id,
        ma.asset_number,
        ma.asset_name,
        ma.asset_type,
        ma.criticality_rating,
        f.factory_name,
        ma.purchase_cost,
        ma.replacement_cost,
        ma.installation_date,
        DATE_PART('years', AGE(CURRENT_DATE, ma.installation_date)) as asset_age_years,
        ma.expected_life_years,
        ma.remaining_life_years,
        SUM(mc.cost_amount) as total_maintenance_cost,
        SUM(CASE WHEN mc.cost_date >= CURRENT_DATE - INTERVAL '12 months' THEN mc.cost_amount ELSE 0 END) as last_12m_cost,
        COUNT(DISTINCT wo.work_order_id) as total_work_orders,
        COUNT(DISTINCT CASE WHEN wo.wo_type = 'breakdown' THEN wo.work_order_id END) as breakdown_count
    FROM maintenance_assets ma
    JOIN factories f ON ma.factory_id = f.factory_id
    LEFT JOIN maintenance_costs mc ON ma.asset_id = mc.asset_id
    LEFT JOIN work_orders wo ON ma.asset_id = wo.asset_id
    WHERE ma.is_active = true
    GROUP BY ma.asset_id, ma.asset_number, ma.asset_name, ma.asset_type, ma.criticality_rating,
             f.factory_name, ma.purchase_cost, ma.replacement_cost, ma.installation_date,
             ma.expected_life_years, ma.remaining_life_years
)
SELECT 
    ac.asset_id,
    ac.asset_number,
    ac.asset_name,
    ac.asset_type,
    ac.criticality_rating,
    ac.factory_name,
    ac.purchase_cost,
    ac.replacement_cost,
    ac.asset_age_years,
    ac.expected_life_years,
    ac.remaining_life_years,
    ac.total_maintenance_cost,
    ac.last_12m_cost,
    ac.total_work_orders,
    ac.breakdown_count,
    ROUND(ac.total_maintenance_cost * 100.0 / NULLIF(ac.purchase_cost, 0), 2) as maintenance_to_purchase_pct,
    ROUND(ac.last_12m_cost * 100.0 / NULLIF(ac.replacement_cost, 0), 2) as annual_cost_to_replacement_pct,
    CASE 
        WHEN ac.last_12m_cost > ac.replacement_cost * 0.3 THEN 'replacement_candidate'
        WHEN ac.total_maintenance_cost > ac.purchase_cost * 0.8 THEN 'high_maintenance_asset'
        WHEN ac.remaining_life_years <= 1 THEN 'end_of_life'
        WHEN ac.breakdown_count > 5 THEN 'reliability_concern'
        ELSE 'normal'
    END as asset_status_flag,
    CASE 
        WHEN ac.last_12m_cost > ac.replacement_cost * 0.3 THEN 'Evaluate replacement - maintenance cost exceeds 30% of replacement'
        WHEN ac.remaining_life_years <= 1 THEN 'Plan capital replacement - approaching end of life'
        WHEN ac.breakdown_count > 5 THEN 'Reliability improvement program needed'
        ELSE 'Continue current maintenance strategy'
    END as recommendation
FROM asset_costs ac
WHERE ac.total_maintenance_cost > 0
ORDER BY ac.last_12m_cost DESC;
```

## 6. Spare Parts & MRO Inventory

### Query 6.1: Critical Spare Parts Status
```
Show critical spare parts inventory status with stockout risk and reorder recommendations
```

**SQL Query:**
```sql
SELECT 
    mp.mro_part_id,
    mp.part_number,
    mp.part_name,
    mp.part_category,
    mp.criticality,
    mp.current_stock,
    mp.min_stock_level,
    mp.reorder_point,
    mp.reorder_quantity,
    mp.unit_of_measure,
    mp.lead_time_days,
    mp.standard_cost,
    mp.current_stock * mp.standard_cost as stock_value,
    mp.last_issue_date,
    DATE_PART('days', CURRENT_DATE - mp.last_issue_date) as days_since_last_issue,
    mp.annual_usage_quantity,
    ROUND(mp.annual_usage_quantity / 365, 2) as daily_usage_rate,
    ROUND(mp.current_stock / NULLIF(mp.annual_usage_quantity / 365, 0), 0) as days_of_stock,
    CASE 
        WHEN mp.current_stock <= 0 THEN 'out_of_stock'
        WHEN mp.current_stock <= mp.min_stock_level THEN 'below_minimum'
        WHEN mp.current_stock <= mp.reorder_point THEN 'reorder_required'
        WHEN mp.current_stock > mp.max_stock_level THEN 'overstocked'
        ELSE 'adequate'
    END as stock_status,
    CASE 
        WHEN mp.current_stock <= 0 AND mp.criticality = 'critical' THEN 'emergency_order'
        WHEN mp.current_stock <= mp.reorder_point THEN 'place_order'
        WHEN mp.current_stock > mp.max_stock_level THEN 'review_excess'
        ELSE 'no_action'
    END as recommended_action,
    mp.used_on_assets
FROM mro_parts mp
WHERE mp.is_active = true
    AND mp.part_status = 'active'
ORDER BY 
    CASE mp.criticality WHEN 'critical' THEN 1 WHEN 'high' THEN 2 WHEN 'medium' THEN 3 ELSE 4 END,
    CASE 
        WHEN mp.current_stock <= 0 THEN 1
        WHEN mp.current_stock <= mp.min_stock_level THEN 2
        WHEN mp.current_stock <= mp.reorder_point THEN 3
        ELSE 4
    END;
```

---

## 🔄 API Integration Patterns

### Real-Time Data Refresh
- **Asset Status**: Real-time updates for equipment status changes
- **Work Order Tracking**: Hourly refresh for work order progress
- **Reliability Metrics**: Daily calculation of MTBF/MTTR metrics

### Performance Optimization
- **Caching Layer**: Redis for frequently accessed asset dashboards
- **Alert Engine**: Proactive notification for equipment failures and PM due dates
- **Query Optimization**: Indexed views for complex reliability calculations

---

## 📊 API Conversion Guidelines

When converting these natural language queries to APIs, consider:

1. **Real-time Alerts**: Use push notifications for equipment failures and critical PM due dates
2. **Time Ranges**: Include flexible time range parameters (7 days, 30 days, YTD, custom)
3. **Filtering**: Add asset-type, criticality, factory, and maintenance-type filters
4. **Hierarchy Navigation**: Support drill-down from factory → line → asset → work order
5. **Status Tracking**: Include workflow status parameters for work order lifecycle
6. **Export Options**: Support maintenance reports in PDF, Excel formats
7. **Mobile Access**: Optimize for technician mobile access with offline capability

## 🗄️ Database Tables Referenced

These queries primarily use data from:
- **CMMS Database**: `maintenance_assets`, `work_orders`, `work_order_tasks`, `pm_schedules`, `asset_reliability_metrics`, `mro_parts`, `maintenance_technicians`, `failure_codes`, `maintenance_history`, `maintenance_costs`
- **Master Database**: `factories`, `production_lines`, `machines`
- **Operational Database**: `machine_faults`, `downtime_events`

---

*This specification provides the foundation for implementing a comprehensive Asset Performance Intelligence application that serves as the command center for maintenance excellence and asset reliability across all manufacturing facilities.*
