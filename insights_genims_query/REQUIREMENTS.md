QUALITY INTELLIGENCE
ASSET PERFORMANCE
SUPPLY CHAIN INTELLIGENCE
COMPLIANCE & AUDIT
FACTORY VIEW

For each above ai app:-
I need  Objectives, Domains, Additional Comments,Users, Selected Roles, Users, databases needed for it..., give me the corresponding natural langugae query, for each screens, 
So to start with take Factory Overview as of now.
update all the results for factory overview in the factory_overview_geographic_view_queries,md file itself....

start with factory overview, 

### 3. Real-Time Operations Monitor
**Purpose:** Live production status and immediate operational visibility

#### Query 3.1: Live Factory Operations Status
```
Get real-time operational status for all factories showing current production rates, machine states, active work orders, and immediate issues requiring attention
```

**SQL Query:**
```sql
WITH real_time_operations AS (
    SELECT 
        f.factory_id,
        f.factory_name,
        f.city,
        f.country,
        -- Current production metrics
        ROUND(AVG(smd.parts_produced_shift / 8.0), 2) as current_hourly_rate,
        ROUND(AVG(smd.oee_percentage), 2) as current_oee,
        COUNT(DISTINCT pl.line_id) as total_lines,
        COUNT(DISTINCT CASE WHEN smd.machine_state = 'running' THEN pl.line_id END) as running_lines,
        COUNT(DISTINCT CASE WHEN smd.machine_state = 'idle' THEN pl.line_id END) as idle_lines,
        COUNT(DISTINCT CASE WHEN smd.machine_state = 'fault' THEN pl.line_id END) as fault_lines,
        -- Work orders status
        COUNT(DISTINCT wo.work_order_id) as active_work_orders,
        COUNT(DISTINCT CASE WHEN wo.status = 'in_progress' THEN wo.work_order_id END) as in_progress_orders,
        -- Alert summary
        SUM(smd.active_alarms) as total_active_alarms,
        MAX(smd.active_alarms) as max_machine_alarms,
        -- Performance indicators
        CASE 
            WHEN COUNT(DISTINCT CASE WHEN smd.machine_state = 'fault' THEN pl.line_id END) > 0 THEN 'critical'
            WHEN SUM(smd.active_alarms) > 10 THEN 'warning'
            WHEN AVG(smd.oee_percentage) < 75 THEN 'attention'
            ELSE 'normal'
        END as operational_status
    FROM factories f
    JOIN production_lines pl ON f.factory_id = pl.factory_id
    LEFT JOIN scada_machine_data smd ON pl.line_id = smd.line_id
        AND smd.timestamp >= NOW() - INTERVAL '15 minutes'
    LEFT JOIN work_orders wo ON f.factory_id = wo.factory_id
        AND wo.status IN ('in_progress', 'scheduled')
    WHERE f.status = 'active' AND pl.status = 'active'
    GROUP BY f.factory_id, f.factory_name, f.city, f.country
)
SELECT 
    *,
    ROUND(running_lines * 100.0 / NULLIF(total_lines, 0), 2) as line_utilization_percentage,
    CASE 
        WHEN operational_status = 'critical' THEN 1
        WHEN operational_status = 'warning' THEN 2
        WHEN operational_status = 'attention' THEN 3
        ELSE 4
    END as priority_sort
FROM real_time_operations
ORDER BY priority_sort, factory_name;
```

### 4. Production Performance Analytics
**Purpose:** Detailed production analysis and performance trends

#### Query 4.1: Daily Production Performance by Factory
```
Show today's production performance for each factory including output, efficiency, quality metrics, and variance from targets
```

**SQL Query:**
```sql
WITH daily_targets AS (
    SELECT 
        wo.factory_id,
        SUM(wo.planned_quantity) as planned_production,
        COUNT(wo.work_order_id) as planned_orders
    FROM work_orders wo
    WHERE DATE(wo.planned_start_date) = CURRENT_DATE
    GROUP BY wo.factory_id
),
daily_actuals AS (
    SELECT 
        f.factory_id,
        f.factory_name,
        SUM(smd.parts_produced_shift) as actual_production,
        AVG(smd.oee_percentage) as avg_oee,
        AVG(smd.quality_percentage) as avg_quality,
        AVG(smd.availability_percentage) as avg_availability,
        AVG(smd.performance_percentage) as avg_performance,
        SUM(smd.downtime_seconds_shift) / 3600.0 as total_downtime_hours,
        COUNT(DISTINCT smd.machine_id) as active_machines
    FROM factories f
    JOIN production_lines pl ON f.factory_id = pl.factory_id
    JOIN scada_machine_data smd ON pl.line_id = smd.line_id
    WHERE DATE(smd.timestamp) = CURRENT_DATE
        AND f.status = 'active'
    GROUP BY f.factory_id, f.factory_name
)
SELECT 
    da.factory_id,
    da.factory_name,
    da.actual_production,
    COALESCE(dt.planned_production, 0) as planned_production,
    ROUND(da.actual_production * 100.0 / NULLIF(dt.planned_production, 0), 2) as production_efficiency_percentage,
    ROUND(da.avg_oee, 2) as oee_percentage,
    ROUND(da.avg_quality, 2) as quality_percentage,
    ROUND(da.avg_availability, 2) as availability_percentage,
    ROUND(da.avg_performance, 2) as performance_percentage,
    da.total_downtime_hours,
    da.active_machines,
    -- Performance classification
    CASE 
        WHEN da.actual_production >= dt.planned_production * 1.05 THEN 'exceeding'
        WHEN da.actual_production >= dt.planned_production * 0.95 THEN 'on_target'
        WHEN da.actual_production >= dt.planned_production * 0.85 THEN 'below_target'
        ELSE 'significantly_below'
    END as performance_category
FROM daily_actuals da
LEFT JOIN daily_targets dt ON da.factory_id = dt.factory_id
ORDER BY production_efficiency_percentage DESC;
```

### 5. Quality & Compliance Dashboard
**Purpose:** Quality performance and regulatory compliance monitoring

#### Query 5.1: Factory Quality Performance Summary
```
Display quality metrics including defect rates, inspection results, customer complaints, and compliance status for each factory
```

**SQL Query:**
```sql
WITH quality_metrics AS (
    SELECT 
        f.factory_id,
        f.factory_name,
        COUNT(qi.inspection_id) as total_inspections,
        COUNT(CASE WHEN qi.inspection_result = 'pass' THEN 1 END) as passed_inspections,
        COUNT(CASE WHEN qi.inspection_result = 'fail' THEN 1 END) as failed_inspections,
        AVG(CASE WHEN qi.defects_found > 0 THEN qi.defects_found ELSE 0 END) as avg_defects_per_inspection,
        SUM(qi.critical_defects) as total_critical_defects,
        SUM(qi.major_defects) as total_major_defects,
        SUM(qi.minor_defects) as total_minor_defects
    FROM factories f
    LEFT JOIN work_orders wo ON f.factory_id = wo.factory_id
    LEFT JOIN quality_inspections qi ON wo.work_order_id = qi.work_order_id
    WHERE qi.inspection_date >= CURRENT_DATE - INTERVAL '30 days'
        AND f.status = 'active'
    GROUP BY f.factory_id, f.factory_name
)
SELECT 
    qm.factory_id,
    qm.factory_name,
    qm.total_inspections,
    ROUND(qm.passed_inspections * 100.0 / NULLIF(qm.total_inspections, 0), 2) as quality_pass_rate,
    ROUND(qm.failed_inspections * 100.0 / NULLIF(qm.total_inspections, 0), 2) as defect_rate,
    qm.total_critical_defects,
    qm.total_major_defects,
    qm.total_minor_defects,
    ROUND(qm.avg_defects_per_inspection, 2) as avg_defects_per_inspection,
    -- Quality rating
    CASE 
        WHEN (qm.passed_inspections * 100.0 / NULLIF(qm.total_inspections, 0)) >= 98 THEN 'excellent'
        WHEN (qm.passed_inspections * 100.0 / NULLIF(qm.total_inspections, 0)) >= 95 THEN 'good'
        WHEN (qm.passed_inspections * 100.0 / NULLIF(qm.total_inspections, 0)) >= 90 THEN 'fair'
        ELSE 'needs_improvement'
    END as quality_rating
FROM quality_metrics qm
ORDER BY quality_pass_rate DESC;
```

### 6. Asset Performance & Maintenance
**Purpose:** Equipment performance and maintenance status across factories

#### Query 6.1: Factory Asset Performance Overview
```
Show equipment performance, maintenance status, and reliability metrics for critical assets across all factory locations
```

**SQL Query:**
```sql
SELECT 
    f.factory_id,
    f.factory_name,
    COUNT(DISTINCT m.machine_id) as total_machines,
    COUNT(DISTINCT CASE WHEN m.criticality = 'critical' THEN m.machine_id END) as critical_machines,
    -- Current machine status from SCADA
    COUNT(DISTINCT CASE WHEN smd.machine_state = 'running' THEN m.machine_id END) as running_machines,
    COUNT(DISTINCT CASE WHEN smd.machine_state = 'maintenance' THEN m.machine_id END) as maintenance_machines,
    COUNT(DISTINCT CASE WHEN smd.machine_state = 'fault' THEN m.machine_id END) as fault_machines,
    -- Performance metrics
    ROUND(AVG(smd.oee_percentage), 2) as avg_equipment_oee,
    SUM(smd.active_alarms) as total_equipment_alarms,
    ROUND(AVG(smd.power_consumption_kw), 2) as avg_power_consumption,
    -- Availability calculation
    ROUND(COUNT(CASE WHEN smd.machine_state = 'running' THEN 1 END) * 100.0 / 
          NULLIF(COUNT(smd.machine_id), 0), 2) as equipment_availability_percentage,
    -- Asset health score
    CASE 
        WHEN AVG(smd.oee_percentage) >= 85 AND SUM(smd.active_alarms) <= 5 THEN 'excellent'
        WHEN AVG(smd.oee_percentage) >= 75 AND SUM(smd.active_alarms) <= 15 THEN 'good'
        WHEN AVG(smd.oee_percentage) >= 60 AND SUM(smd.active_alarms) <= 25 THEN 'fair'
        ELSE 'poor'
    END as asset_health_score
FROM factories f
JOIN production_lines pl ON f.factory_id = pl.factory_id
JOIN machines m ON pl.line_id = m.line_id
LEFT JOIN (
    SELECT DISTINCT ON (machine_id) 
        machine_id, machine_state, oee_percentage, active_alarms, power_consumption_kw
    FROM scada_machine_data
    WHERE timestamp >= NOW() - INTERVAL '1 hour'
    ORDER BY machine_id, timestamp DESC
) smd ON m.machine_id = smd.machine_id
WHERE f.status = 'active' 
    AND pl.status = 'active'
    AND m.status = 'active'
GROUP BY f.factory_id, f.factory_name
ORDER BY equipment_availability_percentage DESC;
```

### 7. Supply Chain & Logistics Overview
**Purpose:** Material flow, inventory status, and logistics performance

#### Query 7.1: Factory Supply Chain Performance
```
Display inventory levels, supplier performance, material flow, and logistics metrics for each factory location
```

**SQL Query:**
```sql
WITH inventory_status AS (
    SELECT 
        f.factory_id,
        w.warehouse_id,
        SUM(il.current_stock_value) as total_inventory_value,
        COUNT(DISTINCT il.material_id) as unique_materials,
        COUNT(CASE WHEN il.current_stock_quantity = 0 THEN 1 END) as stockout_items,
        COUNT(CASE WHEN il.current_stock_quantity <= il.minimum_stock_level THEN 1 END) as low_stock_items,
        AVG(il.stock_turnover_ratio) as avg_turnover_ratio
    FROM factories f
    JOIN warehouses w ON f.factory_id = w.factory_id
    LEFT JOIN inventory_levels il ON w.warehouse_id = il.warehouse_id
    WHERE il.as_of_date = CURRENT_DATE AND f.status = 'active'
    GROUP BY f.factory_id, w.warehouse_id
),
supplier_performance AS (
    SELECT 
        f.factory_id,
        COUNT(DISTINCT s.shipment_id) as total_shipments,
        COUNT(CASE WHEN s.shipment_status = 'delivered' THEN 1 END) as delivered_shipments,
        ROUND(AVG(EXTRACT(EPOCH FROM (s.actual_delivery_date - s.scheduled_delivery_date))/86400), 2) as avg_delay_days
    FROM factories f
    LEFT JOIN shipments s ON f.factory_id = s.destination_factory_id
    WHERE s.shipment_date >= CURRENT_DATE - INTERVAL '30 days'
        AND s.shipment_type = 'inbound'
    GROUP BY f.factory_id
)
SELECT 
    f.factory_id,
    f.factory_name,
    f.city,
    f.country,
    -- Inventory metrics
    SUM(ins.total_inventory_value) as total_inventory_value,
    SUM(ins.unique_materials) as total_unique_materials,
    SUM(ins.stockout_items) as total_stockout_items,
    SUM(ins.low_stock_items) as total_low_stock_items,
    AVG(ins.avg_turnover_ratio) as avg_inventory_turnover,
    -- Supplier performance
    sp.total_shipments,
    sp.delivered_shipments,
    ROUND(sp.delivered_shipments * 100.0 / NULLIF(sp.total_shipments, 0), 2) as on_time_delivery_rate,
    sp.avg_delay_days,
    -- Supply chain health score
    CASE 
        WHEN (sp.delivered_shipments * 100.0 / NULLIF(sp.total_shipments, 0)) >= 95 
             AND SUM(ins.stockout_items) = 0 THEN 'excellent'
        WHEN (sp.delivered_shipments * 100.0 / NULLIF(sp.total_shipments, 0)) >= 90 
             AND SUM(ins.stockout_items) <= 2 THEN 'good'
        WHEN (sp.delivered_shipments * 100.0 / NULLIF(sp.total_shipments, 0)) >= 80 THEN 'fair'
        ELSE 'needs_improvement'
    END as supply_chain_health
FROM genims_master_db.factories f
LEFT JOIN inventory_status ins ON f.factory_id = ins.factory_id
LEFT JOIN supplier_performance sp ON f.factory_id = sp.factory_id
WHERE f.status = 'active'
GROUP BY f.factory_id, f.factory_name, f.city, f.country, 
         sp.total_shipments, sp.delivered_shipments, sp.avg_delay_days
ORDER BY on_time_delivery_rate DESC;
```

### 8. Financial Performance Dashboard
**Purpose:** Financial impact analysis and cost performance by factory

#### Query 8.1: Factory Financial Performance Summary
```
Show revenue, costs, profitability, and financial KPIs for each factory location with budget variance analysis
```

**SQL Query:**
```sql
WITH factory_financials AS (
    SELECT 
        f.factory_id,
        f.factory_name,
        -- Revenue from completed work orders
        SUM(wo.actual_cost_per_unit * wo.produced_quantity) as actual_revenue,
        SUM(wo.standard_cost_per_unit * wo.planned_quantity) as planned_revenue,
        -- Cost components
        SUM(wo.total_material_cost) as total_material_cost,
        SUM(wo.total_labor_cost) as total_labor_cost,
        SUM(wo.total_overhead_cost) as total_overhead_cost,
        -- Production quantities
        SUM(wo.produced_quantity) as total_production_qty,
        COUNT(wo.work_order_id) as completed_orders
    FROM genims_master_db.factories f
    LEFT JOIN genims_manufacturing_db.work_orders wo ON f.factory_id = wo.factory_id
    WHERE wo.status = 'completed'
        AND wo.actual_end_time >= DATE_TRUNC('month', CURRENT_DATE)
        AND f.status = 'active'
    GROUP BY f.factory_id, f.factory_name
)
SELECT 
    ff.factory_id,
    ff.factory_name,
    -- Revenue metrics
    COALESCE(ff.actual_revenue, 0) as monthly_actual_revenue,
    COALESCE(ff.planned_revenue, 0) as monthly_planned_revenue,
    ROUND((ff.actual_revenue - ff.planned_revenue) * 100.0 / NULLIF(ff.planned_revenue, 0), 2) as revenue_variance_percentage,
    -- Cost metrics
    COALESCE(ff.total_material_cost, 0) as total_material_cost,
    COALESCE(ff.total_labor_cost, 0) as total_labor_cost,
    COALESCE(ff.total_overhead_cost, 0) as total_overhead_cost,
    (COALESCE(ff.total_material_cost, 0) + COALESCE(ff.total_labor_cost, 0) + COALESCE(ff.total_overhead_cost, 0)) as total_production_cost,
    -- Profitability
    (ff.actual_revenue - (ff.total_material_cost + ff.total_labor_cost + ff.total_overhead_cost)) as gross_profit,
    ROUND((ff.actual_revenue - (ff.total_material_cost + ff.total_labor_cost + ff.total_overhead_cost)) * 100.0 / 
          NULLIF(ff.actual_revenue, 0), 2) as gross_profit_margin_percentage,
    -- Efficiency metrics
    ROUND((ff.total_material_cost + ff.total_labor_cost + ff.total_overhead_cost) / NULLIF(ff.total_production_qty, 0), 2) as cost_per_unit,
    ff.completed_orders,
    -- Performance rating
    CASE 
        WHEN (ff.actual_revenue - ff.planned_revenue) / NULLIF(ff.planned_revenue, 0) >= 0.05 THEN 'exceeding'
        WHEN (ff.actual_revenue - ff.planned_revenue) / NULLIF(ff.planned_revenue, 0) >= -0.05 THEN 'on_target'
        WHEN (ff.actual_revenue - ff.planned_revenue) / NULLIF(ff.planned_revenue, 0) >= -0.15 THEN 'below_target'
        ELSE 'significantly_below'
    END as financial_performance_category
FROM factory_financials ff
ORDER BY gross_profit_margin_percentage DESC;
```

### 9. Executive Summary Dashboard
**Purpose:** High-level strategic overview for executive decision-making

#### Query 9.1: Executive Factory Network Summary
```
Provide executive-level summary with key performance indicators, strategic metrics, critical issues, and recommended actions by factory
```

**SQL Query:**
```sql
WITH factory_summary AS (
    SELECT 
        f.factory_id,
        f.factory_name,
        CONCAT(f.city, ', ', f.country) as location,
        
        -- Operational metrics
        AVG(smd.oee_percentage) as avg_oee,
        SUM(smd.parts_produced_shift) as daily_production,
        COUNT(DISTINCT CASE WHEN smd.machine_state = 'running' THEN smd.machine_id END) as running_machines,
        COUNT(DISTINCT smd.machine_id) as total_machines,
        
        -- Quality metrics
        COUNT(qi.inspection_id) as quality_inspections,
        COUNT(CASE WHEN qi.inspection_result = 'pass' THEN 1 END) as passed_inspections,
        
        -- Critical issues
        SUM(CASE WHEN smd.active_alarms > 5 THEN 1 ELSE 0 END) as critical_equipment_alerts,
        COUNT(CASE WHEN smd.machine_state = 'fault' THEN 1 END) as equipment_failures,
        
        -- Financial impact (approximated)
        AVG(wo.actual_cost_per_unit) as avg_production_cost
        
    FROM factories f
    LEFT JOIN production_lines pl ON f.factory_id = pl.factory_id
    LEFT JOIN scada_machine_data smd ON pl.line_id = smd.line_id 
        AND DATE(smd.timestamp) = CURRENT_DATE
    LEFT JOIN genims_manufacturing_db.quality_inspections qi ON f.factory_id = qi.work_order_id
        AND DATE(qi.inspection_date) = CURRENT_DATE
    LEFT JOIN genims_manufacturing_db.work_orders wo ON f.factory_id = wo.factory_id
        AND DATE(wo.actual_end_time) = CURRENT_DATE
    WHERE f.status = 'active'
    GROUP BY f.factory_id, f.factory_name, f.city, f.country
)
SELECT 
    fs.factory_id,
    fs.factory_name,
    fs.location,
    
    -- Performance indicators
    ROUND(fs.avg_oee, 1) as oee_percentage,
    fs.daily_production,
    ROUND(fs.running_machines * 100.0 / NULLIF(fs.total_machines, 0), 1) as equipment_availability,
    ROUND(fs.passed_inspections * 100.0 / NULLIF(fs.quality_inspections, 0), 1) as quality_score,
    
    -- Critical metrics
    fs.critical_equipment_alerts,
    fs.equipment_failures,
    (fs.critical_equipment_alerts + fs.equipment_failures) as total_critical_issues,
    
    -- Strategic classification
    CASE 
        WHEN fs.avg_oee >= 85 AND fs.passed_inspections * 100.0 / NULLIF(fs.quality_inspections, 0) >= 95 
             AND (fs.critical_equipment_alerts + fs.equipment_failures) = 0 THEN 'star_performer'
        WHEN fs.avg_oee >= 75 AND fs.passed_inspections * 100.0 / NULLIF(fs.quality_inspections, 0) >= 90 
             AND (fs.critical_equipment_alerts + fs.equipment_failures) <= 2 THEN 'good_performer'
        WHEN fs.avg_oee >= 65 OR (fs.critical_equipment_alerts + fs.equipment_failures) <= 5 THEN 'needs_attention'
        ELSE 'immediate_action_required'
    END as strategic_priority,
    
    -- Risk assessment
    CASE 
        WHEN (fs.critical_equipment_alerts + fs.equipment_failures) > 5 THEN 'high_risk'
        WHEN (fs.critical_equipment_alerts + fs.equipment_failures) > 2 THEN 'medium_risk'
        WHEN fs.avg_oee < 70 THEN 'performance_risk'
        ELSE 'low_risk'
    END as risk_level,
    
    -- Recommended action
    CASE 
        WHEN (fs.critical_equipment_alerts + fs.equipment_failures) > 5 THEN 'Emergency maintenance intervention required'
        WHEN fs.avg_oee < 70 THEN 'Production optimization review needed'
        WHEN fs.passed_inspections * 100.0 / NULLIF(fs.quality_inspections, 0) < 90 THEN 'Quality improvement initiative'
        WHEN fs.avg_oee >= 85 THEN 'Best practice documentation and sharing'
        ELSE 'Continue monitoring'
    END as recommended_action
    
FROM factory_summary fs
ORDER BY 
    CASE strategic_priority
        WHEN 'immediate_action_required' THEN 1
        WHEN 'needs_attention' THEN 2
        WHEN 'good_performer' THEN 3
        WHEN 'star_performer' THEN 4
    END,
    fs.avg_oee ASC;
```

## 📊 SCREEN NAVIGATION & USER WORKFLOWS

### Workflow 1: Executive Morning Briefing
1. **Landing**: Geographic Factory Map → Network-Wide KPIs Summary
2. **Drill-Down**: Critical Issues Identification → Factory-Specific Performance Review
3. **Action**: Strategic Priority Assessment → Resource Allocation Decisions

### Workflow 2: Operations Manager Production Review
1. **Real-Time Status**: Live Operations Monitor → Production Performance Analytics
2. **Issue Investigation**: Equipment Performance Review → Quality Analysis
3. **Optimization**: Supply Chain Performance → Financial Impact Assessment

### Workflow 3: Continuous Improvement Analysis
1. **Benchmarking**: Factory Performance Comparison → Best Practice Identification
2. **Root Cause**: Quality & Asset Performance Correlation → Process Improvement Opportunities
3. **Implementation**: Strategic Recommendations → Performance Tracking

---

## 🔄 API INTEGRATION PATTERNS

### Real-Time Data Refresh
- **SCADA Integration**: 15-second refresh for operational metrics
- **Quality Systems**: 5-minute refresh for inspection results  
- **Financial Systems**: Hourly refresh for cost and revenue data

### Data Federation Strategy
- **Primary Sources**: SCADA, MES, ERP systems for live operational data
- **Secondary Sources**: WMS, TMS, CRM for contextual business intelligence
- **Historical Analytics**: Aggregated data marts for trend analysis and forecasting

### Performance Optimization
- **Caching Layer**: Redis for frequently accessed KPIs and dashboard data
- **Data Compression**: Real-time metric aggregation at edge devices
- **Query Optimization**: Indexed views for complex cross-database joins

---

*This specification provides the foundation for implementing a comprehensive Factory Overview - Geographic View application that serves as the command center for multi-factory manufacturing operations.*
```
Show today's production output by factory location, including units produced, OEE metrics, and efficiency percentage
```

**SQL Query:**
```sql
SELECT 
    f.factory_id,
    f.factory_name,
    SUM(smd.parts_produced_shift) as units_produced_today,
    COUNT(DISTINCT pl.line_id) as active_production_lines,
    ROUND(AVG(smd.oee_percentage), 2) as avg_oee_percentage,
    ROUND(AVG(smd.availability_percentage), 2) as avg_availability,
    ROUND(AVG(smd.performance_percentage), 2) as avg_performance,
    ROUND(AVG(smd.quality_percentage), 2) as avg_quality,
    SUM(smd.downtime_seconds_shift) / 3600.0 as total_downtime_hours,
    COUNT(CASE WHEN smd.machine_state = 'running' THEN 1 END) as running_machines,
    COUNT(CASE WHEN smd.machine_state = 'fault' THEN 1 END) as faulted_machines
FROM genims_master_db.factories f
JOIN genims_master_db.production_lines pl ON f.factory_id = pl.factory_id
JOIN genims_operational_db.scada_machine_data smd ON pl.line_id = smd.line_id
WHERE DATE(smd.timestamp) = CURRENT_DATE
    AND f.status = 'active'
    AND pl.status = 'active'
GROUP BY f.factory_id, f.factory_name
ORDER BY avg_oee_percentage DESC;
```

### Query 2.2: Weekly Production Trends
```
Get the last 7 days of production data for each factory showing daily output trends, quality metrics, and downtime hours
```

**SQL Query:**
```sql
SELECT 
    f.factory_id,
    f.factory_name,
    DATE(smd.timestamp) as production_date,
    SUM(smd.parts_produced_shift) as daily_output,
    ROUND(AVG(smd.quality_percentage), 2) as avg_quality_percentage,
    ROUND(SUM(smd.downtime_seconds_shift) / 3600.0, 2) as total_downtime_hours,
    ROUND(AVG(smd.oee_percentage), 2) as daily_oee,
    ROUND(AVG(smd.availability_percentage), 2) as daily_availability,
    COUNT(DISTINCT smd.machine_id) as active_machines
FROM genims_master_db.factories f
JOIN genims_master_db.production_lines pl ON f.factory_id = pl.factory_id
JOIN genims_operational_db.scada_machine_data smd ON pl.line_id = smd.line_id
WHERE smd.timestamp >= CURRENT_DATE - INTERVAL '7 days'
    AND smd.timestamp <= CURRENT_DATE + INTERVAL '1 day'
    AND f.status = 'active'
    AND pl.status = 'active'
GROUP BY f.factory_id, f.factory_name, DATE(smd.timestamp)
ORDER BY f.factory_name, production_date DESC;
```

### Query 2.3: Monthly Performance Comparison
```
Compare this month's production performance across all factory locations with the same month last year, showing percentage changes and trends
```

**SQL Query:**
```sql
WITH current_month AS (
    SELECT 
        f.factory_id,
        f.factory_name,
        SUM(smd.parts_produced_shift) as current_output,
        AVG(smd.quality_percentage) as current_quality,
        AVG(smd.oee_percentage) as current_oee
    FROM genims_master_db.factories f
    JOIN genims_master_db.production_lines pl ON f.factory_id = pl.factory_id
    JOIN genims_operational_db.scada_machine_data smd ON pl.line_id = smd.line_id
    WHERE EXTRACT(YEAR FROM smd.timestamp) = EXTRACT(YEAR FROM CURRENT_DATE)
        AND EXTRACT(MONTH FROM smd.timestamp) = EXTRACT(MONTH FROM CURRENT_DATE)
        AND f.status = 'active'
    GROUP BY f.factory_id, f.factory_name
),
last_year_month AS (
    SELECT 
        f.factory_id,
        SUM(smd.parts_produced_shift) as last_year_output,
        AVG(smd.quality_percentage) as last_year_quality,
        AVG(smd.oee_percentage) as last_year_oee
    FROM genims_master_db.factories f
    JOIN genims_master_db.production_lines pl ON f.factory_id = pl.factory_id
    JOIN genims_operational_db.scada_machine_data smd ON pl.line_id = smd.line_id
    WHERE EXTRACT(YEAR FROM smd.timestamp) = EXTRACT(YEAR FROM CURRENT_DATE) - 1
        AND EXTRACT(MONTH FROM smd.timestamp) = EXTRACT(MONTH FROM CURRENT_DATE)
    GROUP BY f.factory_id
)
SELECT 
    cm.factory_id,
    cm.factory_name,
    cm.current_output,
    COALESCE(lym.last_year_output, 0) as last_year_output,
    ROUND((cm.current_output - COALESCE(lym.last_year_output, 0)) * 100.0 / NULLIF(lym.last_year_output, 0), 2) as output_change_percentage,
    ROUND(cm.current_quality, 2) as current_quality,
    ROUND(COALESCE(lym.last_year_quality, 0), 2) as last_year_quality,
    ROUND(cm.current_quality - COALESCE(lym.last_year_quality, 0), 2) as quality_change,
    ROUND(cm.current_oee, 2) as current_oee,
    ROUND(COALESCE(lym.last_year_oee, 0), 2) as last_year_oee
FROM current_month cm
LEFT JOIN last_year_month lym ON cm.factory_id = lym.factory_id
ORDER BY output_change_percentage DESC;
```

### Query 2.4: Top Performing Factories
```
Rank all factories by production efficiency, quality scores, and overall equipment effectiveness (OEE) for the current month
```

**SQL Query:**
```sql
SELECT 
    f.factory_id,
    f.factory_name,
    ROUND(AVG(smd.performance_percentage), 2) as production_efficiency,
    ROUND(AVG(smd.quality_percentage), 2) as avg_quality_percentage,
    ROUND(AVG(smd.oee_percentage), 2) as avg_oee_score,
    ROUND(AVG(smd.availability_percentage), 2) as avg_availability,
    SUM(smd.parts_produced_shift) as total_parts_produced,
    COUNT(CASE WHEN qi.inspection_result = 'pass' THEN 1 END) * 100.0 / NULLIF(COUNT(qi.inspection_id), 0) as quality_pass_rate,
    ROUND((AVG(smd.performance_percentage) + AVG(smd.quality_percentage) + AVG(smd.oee_percentage)) / 3, 2) as overall_performance_score,
    ROW_NUMBER() OVER (ORDER BY (AVG(smd.performance_percentage) + AVG(smd.quality_percentage) + AVG(smd.oee_percentage)) / 3 DESC) as factory_rank
FROM genims_master_db.factories f
JOIN genims_master_db.production_lines pl ON f.factory_id = pl.factory_id
JOIN genims_operational_db.scada_machine_data smd ON pl.line_id = smd.line_id
LEFT JOIN genims_mes_db.quality_inspections qi ON f.factory_id = qi.work_order_id -- Approximate join
WHERE EXTRACT(YEAR FROM smd.timestamp) = EXTRACT(YEAR FROM CURRENT_DATE)
    AND EXTRACT(MONTH FROM smd.timestamp) = EXTRACT(MONTH FROM CURRENT_DATE)
    AND f.status = 'active'
    AND pl.status = 'active'
GROUP BY f.factory_id, f.factory_name
ORDER BY overall_performance_score DESC;
```

## 3. Operational Status & Real-time Monitoring

### Query 3.1: Real-time Factory Status
```
Get current operational status of each factory including active production lines, machine states, maintenance activities, and alert levels
```

**SQL Query:**
```sql
SELECT 
    f.factory_id,
    f.factory_name,
    COUNT(DISTINCT pl.line_id) as total_production_lines,
    COUNT(DISTINCT CASE WHEN smd.machine_state = 'running' THEN pl.line_id END) as active_lines,
    COUNT(DISTINCT CASE WHEN smd.machine_state = 'idle' THEN pl.line_id END) as idle_lines,
    COUNT(DISTINCT CASE WHEN smd.machine_state = 'maintenance' THEN pl.line_id END) as maintenance_lines,
    COUNT(DISTINCT CASE WHEN smd.machine_state = 'fault' THEN pl.line_id END) as fault_lines,
    SUM(smd.active_alarms) as total_active_alarms,
    COUNT(CASE WHEN smd.active_alarms > 5 THEN 1 END) as high_alarm_machines,
    COUNT(CASE WHEN smd.active_alarms > 0 THEN 1 END) as machines_with_alarms,
    CASE 
        WHEN SUM(smd.active_alarms) > 20 THEN 'critical'
        WHEN SUM(smd.active_alarms) > 10 THEN 'high'
        WHEN SUM(smd.active_alarms) > 5 THEN 'medium'
        ELSE 'normal'
    END as overall_alert_level,
    ROUND(AVG(smd.oee_percentage), 2) as avg_oee
FROM genims_master_db.factories f
LEFT JOIN genims_master_db.production_lines pl ON f.factory_id = pl.factory_id AND pl.status = 'active'
LEFT JOIN (
    SELECT DISTINCT ON (line_id, machine_id) 
        line_id, machine_id, machine_state, active_alarms, oee_percentage
    FROM genims_operational_db.scada_machine_data 
    WHERE timestamp >= NOW() - INTERVAL '1 hour'
    ORDER BY line_id, machine_id, timestamp DESC
) smd ON pl.line_id = smd.line_id
WHERE f.status = 'active'
GROUP BY f.factory_id, f.factory_name
ORDER BY 
    CASE overall_alert_level 
        WHEN 'critical' THEN 1 
        WHEN 'high' THEN 2 
        WHEN 'medium' THEN 3 
        ELSE 4 
    END, 
    f.factory_name;
```

### Query 3.2: Equipment Status by Location
```
Show the status of all critical equipment and machines across factory locations, including running, idle, maintenance, and fault states
```

**SQL Query:**
```sql
SELECT 
    f.factory_id,
    f.factory_name,
    m.machine_id,
    m.machine_name,
    m.machine_type,
    smd.machine_state as current_status,
    smd.timestamp as last_status_update,
    CASE 
        WHEN smd.machine_state = 'running' THEN 'operational'
        WHEN smd.machine_state = 'idle' THEN 'standby'
        WHEN smd.machine_state = 'maintenance' THEN 'maintenance'
        WHEN smd.machine_state = 'fault' THEN 'critical'
        WHEN smd.machine_state = 'stopped' THEN 'stopped'
        ELSE 'unknown'
    END as status_category,
    m.criticality,
    smd.active_alarms,
    smd.oee_percentage,
    smd.power_consumption_kw
FROM genims_master_db.factories f
JOIN genims_master_db.production_lines pl ON f.factory_id = pl.factory_id
JOIN genims_master_db.machines m ON pl.line_id = m.line_id
LEFT JOIN (
    SELECT DISTINCT ON (machine_id) 
        machine_id, machine_state, timestamp, active_alarms, oee_percentage, power_consumption_kw
    FROM genims_operational_db.scada_machine_data
    ORDER BY machine_id, timestamp DESC
) smd ON m.machine_id = smd.machine_id
WHERE f.status = 'active' 
    AND m.status = 'active'
    AND m.criticality IN ('high', 'critical')
ORDER BY f.factory_name, status_category DESC, m.machine_name;
```

### Query 3.3: Live Production Metrics
```
Display real-time production metrics for each factory: current production rate, quality rate, downtime percentage, and energy consumption
```

**SQL Query:**
```sql
WITH real_time_metrics AS (
    SELECT 
        f.factory_id,
        f.factory_name,
        AVG(smd.parts_produced_shift / 8.0) as current_production_rate_per_hour,
        AVG(smd.quality_percentage) as avg_quality_rate,
        AVG(smd.power_consumption_kw) as avg_energy_consumption,
        COUNT(DISTINCT pl.line_id) as active_lines,
        AVG(smd.oee_percentage) as avg_oee
    FROM genims_master_db.factories f
    JOIN genims_master_db.production_lines pl ON f.factory_id = pl.factory_id
    JOIN genims_operational_db.scada_machine_data smd ON pl.line_id = smd.line_id
    WHERE smd.timestamp >= NOW() - INTERVAL '15 minutes'
        AND f.status = 'active'
        AND pl.status = 'active'
    GROUP BY f.factory_id, f.factory_name
),
downtime_metrics AS (
    SELECT 
        f.factory_id,
        SUM(smd.downtime_seconds_shift) / 60.0 as total_downtime_minutes,
        COUNT(CASE WHEN smd.machine_state = 'fault' THEN 1 END) as downtime_events
    FROM genims_master_db.factories f
    JOIN genims_master_db.production_lines pl ON f.factory_id = pl.factory_id
    JOIN genims_operational_db.scada_machine_data smd ON pl.line_id = smd.line_id
    WHERE DATE(smd.timestamp) = CURRENT_DATE
        AND smd.machine_state IN ('fault', 'maintenance', 'stopped')
    GROUP BY f.factory_id
)
SELECT 
    rtm.factory_id,
    rtm.factory_name,
    ROUND(rtm.current_production_rate_per_hour, 2) as current_production_rate,
    ROUND(rtm.avg_quality_rate, 2) as quality_rate_percentage,
    ROUND(COALESCE(dm.total_downtime_minutes, 0) * 100.0 / (24 * 60), 2) as downtime_percentage_today,
    ROUND(rtm.avg_energy_consumption, 2) as energy_consumption_kw,
    rtm.active_lines,
    ROUND(rtm.avg_oee, 2) as overall_equipment_effectiveness,
    COALESCE(dm.downtime_events, 0) as downtime_events_today
FROM real_time_metrics rtm
LEFT JOIN downtime_metrics dm ON rtm.factory_id = dm.factory_id
ORDER BY rtm.current_production_rate_per_hour DESC;
```

### Query 3.4: Critical Alerts and Issues
```
Get all active alerts, alarms, and critical issues across factory locations categorized by machine state and alarm count
```

**SQL Query:**
```sql
SELECT 
    f.factory_id,
    f.factory_name,
    m.machine_id,
    m.machine_name,
    smd.machine_state,
    smd.active_alarms,
    smd.alarm_codes,
    smd.warning_codes,
    smd.fault_code,
    smd.fault_description,
    smd.timestamp as alert_timestamp,
    EXTRACT(EPOCH FROM (NOW() - smd.timestamp))/3600 as hours_since_alert,
    CASE 
        WHEN smd.active_alarms >= 5 OR smd.machine_state = 'fault' THEN 'critical'
        WHEN smd.active_alarms >= 3 THEN 'high'
        WHEN smd.active_alarms >= 1 THEN 'medium'
        ELSE 'normal'
    END as severity_level,
    CASE 
        WHEN smd.machine_state = 'fault' THEN 1
        WHEN smd.active_alarms >= 5 THEN 2
        WHEN smd.active_alarms >= 3 THEN 3
        WHEN smd.active_alarms >= 1 THEN 4
        ELSE 5
    END as severity_priority
FROM genims_master_db.factories f
JOIN genims_master_db.production_lines pl ON f.factory_id = pl.factory_id
JOIN genims_master_db.machines m ON pl.line_id = m.line_id
JOIN genims_operational_db.scada_machine_data smd ON m.machine_id = smd.machine_id
WHERE f.status = 'active'
    AND (smd.active_alarms > 0 OR smd.machine_state = 'fault')
    AND smd.timestamp >= CURRENT_DATE - INTERVAL '24 hours'
ORDER BY severity_priority ASC, smd.timestamp DESC
LIMIT 100;
```

## 4. Quality & Safety Metrics

### Query 4.1: Quality Performance by Factory
```
Show quality metrics for each factory location including defect rates, first-pass yield, customer complaints, and quality score trends
```

**SQL Query:**
```sql
SELECT 
    f.factory_id,
    f.factory_name,
    COUNT(qr.quality_record_id) as total_quality_checks,
    AVG(qr.quality_score) as avg_quality_score,
    COUNT(CASE WHEN qr.defect_count > 0 THEN 1 END) * 100.0 / COUNT(*) as defect_rate_percentage,
    COUNT(CASE WHEN qr.first_pass_yield = true THEN 1 END) * 100.0 / COUNT(*) as first_pass_yield_percentage,
    COUNT(cc.complaint_id) as customer_complaints_count,
    ROUND(AVG(qr.quality_score) - LAG(AVG(qr.quality_score)) OVER (PARTITION BY f.factory_id ORDER BY EXTRACT(MONTH FROM qr.inspection_date)), 2) as quality_trend_change
FROM genims_master_db.factories f
JOIN genims_master_db.production_lines pl ON f.factory_id = pl.factory_id
JOIN genims_operational_db.production_records pr ON pl.production_line_id = pr.production_line_id
LEFT JOIN genims_mes_db.quality_records qr ON pr.production_record_id = qr.production_record_id
LEFT JOIN genims_crm_db.customer_complaints cc ON f.factory_id = cc.factory_id 
    AND cc.complaint_date >= CURRENT_DATE - INTERVAL '30 days'
WHERE qr.inspection_date >= CURRENT_DATE - INTERVAL '30 days'
    AND f.is_active = true
GROUP BY f.factory_id, f.factory_name
ORDER BY avg_quality_score DESC;
```

### Query 4.2: Safety Incidents Tracking
```
Get safety incident reports, near-miss events, and safety scores for each factory location over the past month
```

**SQL Query:**
```sql
SELECT 
    f.factory_id,
    f.factory_name,
    COUNT(CASE WHEN si.incident_type = 'injury' THEN 1 END) as injury_incidents,
    COUNT(CASE WHEN si.incident_type = 'near_miss' THEN 1 END) as near_miss_events,
    COUNT(CASE WHEN si.incident_type = 'property_damage' THEN 1 END) as property_damage_incidents,
    COUNT(si.safety_incident_id) as total_safety_events,
    AVG(sm.safety_score) as avg_safety_score,
    SUM(si.lost_time_days) as total_lost_time_days,
    ROUND(COUNT(si.safety_incident_id) * 200000.0 / NULLIF(SUM(e.total_hours_worked), 0), 2) as incident_rate_per_200k_hours,
    MAX(sm.last_audit_date) as last_safety_audit_date
FROM genims_master_db.factories f
LEFT JOIN genims_hr_db.safety_incidents si ON f.factory_id = si.factory_id 
    AND si.incident_date >= CURRENT_DATE - INTERVAL '30 days'
LEFT JOIN genims_hr_db.safety_metrics sm ON f.factory_id = sm.factory_id
LEFT JOIN (
    SELECT factory_id, SUM(hours_worked) as total_hours_worked
    FROM genims_hr_db.employee_time_logs
    WHERE log_date >= CURRENT_DATE - INTERVAL '30 days'
    GROUP BY factory_id
) e ON f.factory_id = e.factory_id
WHERE f.is_active = true
GROUP BY f.factory_id, f.factory_name
ORDER BY avg_safety_score DESC;
```

### Query 4.3: Compliance Status
```
Display compliance status for environmental regulations, safety standards, and quality certifications for each factory
```

**SQL Query:**
```sql
SELECT 
    f.factory_id,
    f.factory_name,
    cr.regulation_name,
    cr.regulation_type,
    cr.compliance_status,
    cr.last_audit_date,
    cr.next_audit_due_date,
    CASE 
        WHEN cr.next_audit_due_date < CURRENT_DATE THEN 'overdue'
        WHEN cr.next_audit_due_date <= CURRENT_DATE + INTERVAL '30 days' THEN 'due_soon'
        ELSE 'compliant'
    END as audit_status,
    cr.certification_expiry_date,
    CASE 
        WHEN cr.certification_expiry_date < CURRENT_DATE THEN 'expired'
        WHEN cr.certification_expiry_date <= CURRENT_DATE + INTERVAL '90 days' THEN 'expiring_soon'
        ELSE 'valid'
    END as certification_status,
    cr.compliance_score
FROM genims_master_db.factories f
LEFT JOIN genims_qms_db.compliance_records cr ON f.factory_id = cr.factory_id
WHERE f.is_active = true
    AND cr.is_active = true
ORDER BY f.factory_name, cr.regulation_type, audit_status DESC;
```

## 5. Resource Utilization & Efficiency

### Query 5.1: Energy Consumption by Factory
```
Show energy consumption patterns, costs, and efficiency metrics for each factory location with comparison to targets
```

**SQL Query:**
```sql
SELECT 
    f.factory_id,
    f.factory_name,
    SUM(ec.energy_consumed_kwh) as total_energy_consumption_kwh,
    SUM(ec.energy_cost) as total_energy_cost,
    AVG(ec.energy_efficiency_ratio) as avg_energy_efficiency,
    f.energy_target_kwh_per_day * DATE_PART('day', CURRENT_DATE - DATE_TRUNC('month', CURRENT_DATE) + INTERVAL '1 month - 1 day') as monthly_energy_target,
    ROUND(SUM(ec.energy_consumed_kwh) * 100.0 / NULLIF(f.energy_target_kwh_per_day * DATE_PART('day', CURRENT_DATE - DATE_TRUNC('month', CURRENT_DATE) + INTERVAL '1 month - 1 day'), 0), 2) as target_achievement_percentage,
    SUM(ec.renewable_energy_kwh) as renewable_energy_used,
    ROUND(SUM(ec.renewable_energy_kwh) * 100.0 / NULLIF(SUM(ec.energy_consumed_kwh), 0), 2) as renewable_percentage
FROM genims_master_db.factories f
JOIN genims_operational_db.energy_consumption ec ON f.factory_id = ec.factory_id
WHERE ec.consumption_date >= DATE_TRUNC('month', CURRENT_DATE)
    AND ec.consumption_date <= CURRENT_DATE
    AND f.is_active = true
GROUP BY f.factory_id, f.factory_name, f.energy_target_kwh_per_day
ORDER BY avg_energy_efficiency DESC;
```

### Query 5.2: Raw Material Usage
```
Get raw material consumption, inventory levels, and waste generation statistics for each factory location
```

**SQL Query:**
```sql
SELECT 
    f.factory_id,
    f.factory_name,
    SUM(mu.quantity_used) as total_material_consumed,
    COUNT(DISTINCT mu.material_id) as unique_materials_used,
    SUM(il.current_stock_quantity) as current_inventory_value,
    AVG(il.stock_turnover_ratio) as avg_stock_turnover,
    SUM(wr.waste_quantity) as total_waste_generated,
    ROUND(SUM(wr.waste_quantity) * 100.0 / NULLIF(SUM(mu.quantity_used), 0), 2) as waste_percentage,
    SUM(wr.recycled_quantity) as total_recycled_waste,
    ROUND(SUM(wr.recycled_quantity) * 100.0 / NULLIF(SUM(wr.waste_quantity), 0), 2) as recycling_percentage
FROM genims_master_db.factories f
JOIN genims_master_db.production_lines pl ON f.factory_id = pl.factory_id
LEFT JOIN genims_mes_db.material_usage mu ON pl.production_line_id = mu.production_line_id 
    AND mu.usage_date >= CURRENT_DATE - INTERVAL '30 days'
LEFT JOIN genims_wms_db.inventory_levels il ON f.factory_id = il.factory_id
LEFT JOIN genims_operational_db.waste_records wr ON f.factory_id = wr.factory_id 
    AND wr.waste_date >= CURRENT_DATE - INTERVAL '30 days'
WHERE f.is_active = true
GROUP BY f.factory_id, f.factory_name
ORDER BY waste_percentage ASC;
```

### Query 5.3: Workforce Utilization
```
Display workforce statistics for each factory: total employees, shifts coverage, overtime hours, and productivity metrics
```

**SQL Query:**
```sql
SELECT 
    f.factory_id,
    f.factory_name,
    COUNT(DISTINCT e.employee_id) as total_employees,
    COUNT(DISTINCT CASE WHEN e.shift_type = 'day' THEN e.employee_id END) as day_shift_employees,
    COUNT(DISTINCT CASE WHEN e.shift_type = 'night' THEN e.employee_id END) as night_shift_employees,
    COUNT(DISTINCT CASE WHEN e.shift_type = 'rotating' THEN e.employee_id END) as rotating_shift_employees,
    ROUND(AVG(etl.hours_worked), 2) as avg_hours_per_employee,
    SUM(etl.overtime_hours) as total_overtime_hours,
    ROUND(SUM(etl.overtime_hours) * 100.0 / NULLIF(SUM(etl.hours_worked), 0), 2) as overtime_percentage,
    ROUND(SUM(pr.actual_output) / NULLIF(SUM(etl.hours_worked), 0), 2) as productivity_units_per_hour,
    AVG(e.performance_rating) as avg_performance_rating
FROM genims_master_db.factories f
JOIN genims_master_db.employees e ON f.factory_id = e.factory_id AND e.is_active = true
LEFT JOIN genims_hr_db.employee_time_logs etl ON e.employee_id = etl.employee_id 
    AND etl.log_date >= CURRENT_DATE - INTERVAL '30 days'
LEFT JOIN genims_master_db.production_lines pl ON f.factory_id = pl.factory_id
LEFT JOIN genims_operational_db.production_records pr ON pl.production_line_id = pr.production_line_id 
    AND pr.production_date >= CURRENT_DATE - INTERVAL '30 days'
WHERE f.is_active = true
GROUP BY f.factory_id, f.factory_name
ORDER BY productivity_units_per_hour DESC;
```

### Query 5.4: Machine Utilization Rates
```
Show machine and equipment utilization rates, capacity utilization, and idle time analysis for each factory location
```

**SQL Query:**
```sql
SELECT 
    f.factory_id,
    f.factory_name,
    COUNT(DISTINCT m.machine_id) as total_machines,
    AVG(ml.utilization_percentage) as avg_machine_utilization,
    AVG(ml.oee_score) as avg_oee_score,
    SUM(ml.running_hours) as total_running_hours,
    SUM(ml.idle_hours) as total_idle_hours,
    SUM(ml.maintenance_hours) as total_maintenance_hours,
    ROUND(SUM(ml.running_hours) * 100.0 / NULLIF(SUM(ml.running_hours + ml.idle_hours + ml.maintenance_hours), 0), 2) as operational_efficiency,
    ROUND(SUM(ml.idle_hours) * 100.0 / NULLIF(SUM(ml.running_hours + ml.idle_hours + ml.maintenance_hours), 0), 2) as idle_time_percentage,
    COUNT(CASE WHEN ml.utilization_percentage > 85 THEN 1 END) as high_utilization_machines,
    COUNT(CASE WHEN ml.utilization_percentage < 50 THEN 1 END) as low_utilization_machines
FROM genims_master_db.factories f
JOIN genims_master_db.production_lines pl ON f.factory_id = pl.factory_id
JOIN genims_master_db.machines m ON pl.production_line_id = m.production_line_id
JOIN genims_operational_db.machine_logs ml ON m.machine_id = ml.machine_id
WHERE ml.log_date >= CURRENT_DATE - INTERVAL '30 days'
    AND f.is_active = true
    AND m.is_active = true
GROUP BY f.factory_id, f.factory_name
ORDER BY avg_machine_utilization DESC;
```

## 6. Supply Chain & Logistics

### Query 6.1: Inbound Logistics Status
```
Get incoming shipments, raw material deliveries, and supplier performance metrics for each factory location
```

**SQL Query:**
```sql
SELECT 
    f.factory_id,
    f.factory_name,
    COUNT(s.shipment_id) as total_incoming_shipments,
    COUNT(CASE WHEN s.shipment_status = 'delivered' THEN 1 END) as delivered_shipments,
    COUNT(CASE WHEN s.shipment_status = 'in_transit' THEN 1 END) as in_transit_shipments,
    COUNT(CASE WHEN s.shipment_status = 'delayed' THEN 1 END) as delayed_shipments,
    AVG(sp.delivery_performance_score) as avg_supplier_performance,
    COUNT(DISTINCT s.supplier_id) as unique_suppliers,
    SUM(s.shipment_value) as total_shipment_value,
    ROUND(AVG(EXTRACT(EPOCH FROM (s.actual_delivery_date - s.scheduled_delivery_date))/86400), 2) as avg_delivery_delay_days,
    COUNT(CASE WHEN s.actual_delivery_date <= s.scheduled_delivery_date THEN 1 END) * 100.0 / COUNT(*) as on_time_delivery_percentage
FROM factories f
JOIN shipments s ON f.factory_id = s.destination_factory_id 
    AND s.shipment_type = 'inbound'
    AND s.shipment_date >= CURRENT_DATE - INTERVAL '30 days'
LEFT JOIN supplier_performance sp ON s.supplier_id = sp.supplier_id
WHERE f.is_active = true
GROUP BY f.factory_id, f.factory_name
ORDER BY on_time_delivery_percentage DESC;
```

### Query 6.2: Outbound Shipments Tracking
```
Show outbound shipments, delivery schedules, and logistics performance for products from each factory
```

**SQL Query:**
```sql
SELECT 
    f.factory_id,
    f.factory_name,
    COUNT(s.shipment_id) as total_outbound_shipments,
    COUNT(CASE WHEN s.shipment_status = 'shipped' THEN 1 END) as shipped_orders,
    COUNT(CASE WHEN s.shipment_status = 'delivered' THEN 1 END) as delivered_orders,
    COUNT(CASE WHEN s.shipment_status = 'pending' THEN 1 END) as pending_shipments,
    SUM(s.shipment_value) as total_shipment_value,
    AVG(tc.cost_per_km) as avg_transportation_cost,
    COUNT(DISTINCT s.customer_id) as unique_customers_served,
    ROUND(AVG(EXTRACT(EPOCH FROM (s.actual_delivery_date - s.shipment_date))/86400), 2) as avg_delivery_time_days,
    COUNT(CASE WHEN s.delivery_priority = 'urgent' THEN 1 END) as urgent_deliveries,
    COUNT(CASE WHEN s.actual_delivery_date <= s.promised_delivery_date THEN 1 END) * 100.0 / COUNT(*) as delivery_promise_fulfillment_percentage
FROM factories f
JOIN shipments s ON f.factory_id = s.source_factory_id 
    AND s.shipment_type = 'outbound'
    AND s.shipment_date >= CURRENT_DATE - INTERVAL '30 days'
LEFT JOIN transportation_costs tc ON s.shipment_id = tc.shipment_id
WHERE f.is_active = true
GROUP BY f.factory_id, f.factory_name
ORDER BY delivery_promise_fulfillment_percentage DESC;
```

### Query 6.3: Inter-factory Material Flow
```
Display material transfers, components flow, and logistics connections between different factory locations
```

**SQL Query:**
```sql
SELECT 
    f1.factory_id as source_factory_id,
    f1.factory_name as source_factory_name,
    f2.factory_id as destination_factory_id,
    f2.factory_name as destination_factory_name,
    COUNT(mt.material_transfer_id) as total_transfers,
    SUM(mt.quantity_transferred) as total_quantity_transferred,
    SUM(mt.transfer_value) as total_transfer_value,
    AVG(EXTRACT(EPOCH FROM (mt.actual_arrival_date - mt.transfer_date))/86400) as avg_transfer_time_days,
    COUNT(CASE WHEN mt.transfer_status = 'completed' THEN 1 END) as completed_transfers,
    COUNT(CASE WHEN mt.transfer_status = 'in_transit' THEN 1 END) as in_transit_transfers,
    COUNT(DISTINCT mt.material_id) as unique_materials_transferred,
    MAX(mt.transfer_date) as last_transfer_date
FROM factories f1
JOIN material_transfers mt ON f1.factory_id = mt.source_factory_id
JOIN factories f2 ON mt.destination_factory_id = f2.factory_id
WHERE mt.transfer_date >= CURRENT_DATE - INTERVAL '90 days'
    AND f1.is_active = true 
    AND f2.is_active = true
    AND f1.factory_id != f2.factory_id
GROUP BY f1.factory_id, f1.factory_name, f2.factory_id, f2.factory_name
HAVING COUNT(mt.material_transfer_id) > 0
ORDER BY total_transfer_value DESC;
```

### Query 6.4: Inventory Levels by Location
```
Get current inventory levels, stock turnover rates, and warehouse capacity utilization for each factory location
```

**SQL Query:**
```sql
SELECT 
    f.factory_id,
    f.factory_name,
    w.warehouse_id,
    w.warehouse_name,
    SUM(il.current_stock_quantity) as total_inventory_quantity,
    SUM(il.current_stock_value) as total_inventory_value,
    AVG(il.stock_turnover_ratio) as avg_stock_turnover_ratio,
    COUNT(DISTINCT il.material_id) as unique_materials_in_stock,
    COUNT(CASE WHEN il.current_stock_quantity = 0 THEN 1 END) as out_of_stock_items,
    COUNT(CASE WHEN il.current_stock_quantity <= il.minimum_stock_level THEN 1 END) as low_stock_items,
    COUNT(CASE WHEN il.current_stock_quantity >= il.maximum_stock_level THEN 1 END) as excess_stock_items,
    ROUND(SUM(il.current_stock_quantity) * 100.0 / NULLIF(w.total_capacity, 0), 2) as warehouse_utilization_percentage,
    SUM(CASE WHEN il.material_category = 'raw_materials' THEN il.current_stock_value ELSE 0 END) as raw_materials_value,
    SUM(CASE WHEN il.material_category = 'finished_goods' THEN il.current_stock_value ELSE 0 END) as finished_goods_value,
    SUM(CASE WHEN il.material_category = 'work_in_progress' THEN il.current_stock_value ELSE 0 END) as wip_value
FROM factories f
JOIN warehouses w ON f.factory_id = w.factory_id
JOIN inventory_levels il ON w.warehouse_id = il.warehouse_id
WHERE f.is_active = true 
    AND w.is_active = true
    AND il.as_of_date = CURRENT_DATE
GROUP BY f.factory_id, f.factory_name, w.warehouse_id, w.warehouse_name, w.total_capacity
ORDER BY total_inventory_value DESC;
```

## 7. Financial Performance

### Query 7.1: Production Costs by Factory
```
Show production costs, cost per unit, and cost efficiency trends for each factory location over the past quarter
```

**SQL Query:**
```sql
SELECT 
    f.factory_id,
    f.factory_name,
    SUM(pc.labor_cost + pc.material_cost + pc.overhead_cost + pc.energy_cost) as total_production_cost,
    SUM(pc.labor_cost) as total_labor_cost,
    SUM(pc.material_cost) as total_material_cost,
    SUM(pc.overhead_cost) as total_overhead_cost,
    SUM(pc.energy_cost) as total_energy_cost,
    SUM(pr.actual_output) as total_units_produced,
    ROUND(SUM(pc.labor_cost + pc.material_cost + pc.overhead_cost + pc.energy_cost) / NULLIF(SUM(pr.actual_output), 0), 2) as cost_per_unit,
    ROUND(AVG(pc.cost_efficiency_score), 2) as avg_cost_efficiency_score,
    LAG(ROUND(SUM(pc.labor_cost + pc.material_cost + pc.overhead_cost + pc.energy_cost) / NULLIF(SUM(pr.actual_output), 0), 2)) OVER (PARTITION BY f.factory_id ORDER BY DATE_TRUNC('month', pc.cost_date)) as prev_month_cost_per_unit
FROM factories f
JOIN production_lines pl ON f.factory_id = pl.factory_id
JOIN production_records pr ON pl.production_line_id = pr.production_line_id
JOIN production_costs pc ON pr.production_record_id = pc.production_record_id
WHERE pc.cost_date >= DATE_TRUNC('quarter', CURRENT_DATE)
    AND f.is_active = true
GROUP BY f.factory_id, f.factory_name
ORDER BY avg_cost_efficiency_score DESC;
```

### Query 7.2: Revenue Generation by Location
```
Get revenue generated, profit margins, and return on investment for each factory location
```

**SQL Query:**
```sql
SELECT 
    f.factory_id,
    f.factory_name,
    SUM(fs.revenue) as total_revenue,
    SUM(fs.cost_of_goods_sold) as total_cogs,
    SUM(fs.revenue - fs.cost_of_goods_sold) as gross_profit,
    ROUND((SUM(fs.revenue - fs.cost_of_goods_sold) * 100.0 / NULLIF(SUM(fs.revenue), 0)), 2) as gross_profit_margin_percentage,
    SUM(fs.operating_expenses) as total_operating_expenses,
    SUM(fs.revenue - fs.cost_of_goods_sold - fs.operating_expenses) as operating_profit,
    ROUND((SUM(fs.revenue - fs.cost_of_goods_sold - fs.operating_expenses) * 100.0 / NULLIF(SUM(fs.revenue), 0)), 2) as operating_profit_margin_percentage,
    f.total_investment as factory_investment,
    ROUND((SUM(fs.revenue - fs.cost_of_goods_sold - fs.operating_expenses) * 100.0 / NULLIF(f.total_investment, 0)), 2) as roi_percentage,
    COUNT(DISTINCT fs.financial_period_id) as reporting_periods
FROM factories f
JOIN financial_statements fs ON f.factory_id = fs.factory_id
WHERE fs.statement_period >= DATE_TRUNC('year', CURRENT_DATE)
    AND f.is_active = true
GROUP BY f.factory_id, f.factory_name, f.total_investment
ORDER BY roi_percentage DESC;
```

### Query 7.3: Budget vs Actual Analysis
```
Compare budgeted vs actual expenses for operations, maintenance, and capital expenditure by factory location
```

**SQL Query:**
```sql
SELECT 
    f.factory_id,
    f.factory_name,
    bl.cost_center_name,
    bl.budget_category,
    SUM(bl.budgeted_amount) as budgeted_amount,
    SUM(bl.actual_amount) as actual_amount,
    SUM(bl.actual_amount - bl.budgeted_amount) as variance_amount,
    ROUND((SUM(bl.actual_amount - bl.budgeted_amount) * 100.0 / NULLIF(SUM(bl.budgeted_amount), 0)), 2) as variance_percentage,
    CASE 
        WHEN SUM(bl.actual_amount) <= SUM(bl.budgeted_amount) THEN 'under_budget'
        WHEN SUM(bl.actual_amount) <= SUM(bl.budgeted_amount) * 1.05 THEN 'within_tolerance'
        ELSE 'over_budget'
    END as budget_status,
    COUNT(*) as budget_line_items
FROM factories f
JOIN cost_centers cc ON f.factory_id = cc.factory_id
JOIN budget_lines bl ON cc.cost_center_id = bl.cost_center_id
WHERE bl.budget_period >= DATE_TRUNC('year', CURRENT_DATE)
    AND f.is_active = true
GROUP BY f.factory_id, f.factory_name, bl.cost_center_name, bl.budget_category
ORDER BY variance_percentage DESC;
```

## 8. Environmental & Sustainability

### Query 8.1: Environmental Impact Metrics
```
Display carbon footprint, water usage, waste generation, and environmental compliance scores for each factory
```

**SQL Query:**
```sql
SELECT 
    f.factory_id,
    f.factory_name,
    SUM(em.carbon_emissions_tons) as total_carbon_emissions,
    SUM(em.water_consumption_liters) as total_water_consumption,
    SUM(em.waste_generated_kg) as total_waste_generated,
    SUM(em.recyclable_waste_kg) as total_recyclable_waste,
    ROUND(SUM(em.recyclable_waste_kg) * 100.0 / NULLIF(SUM(em.waste_generated_kg), 0), 2) as recycling_rate_percentage,
    AVG(em.environmental_score) as avg_environmental_score,
    COUNT(CASE WHEN em.compliance_violations > 0 THEN 1 END) as compliance_violations_count,
    SUM(em.energy_renewable_kwh) as total_renewable_energy,
    ROUND(SUM(em.energy_renewable_kwh) * 100.0 / NULLIF(SUM(em.energy_total_kwh), 0), 2) as renewable_energy_percentage,
    ROUND(SUM(em.carbon_emissions_tons) / NULLIF(SUM(pr.actual_output), 0), 4) as carbon_intensity_per_unit
FROM factories f
JOIN environmental_metrics em ON f.factory_id = em.factory_id
LEFT JOIN production_lines pl ON f.factory_id = pl.factory_id
LEFT JOIN production_records pr ON pl.production_line_id = pr.production_line_id 
    AND pr.production_date = em.measurement_date
WHERE em.measurement_date >= CURRENT_DATE - INTERVAL '90 days'
    AND f.is_active = true
GROUP BY f.factory_id, f.factory_name
ORDER BY avg_environmental_score DESC;
```

### Query 8.2: Sustainability KPIs
```
Show sustainability key performance indicators including energy efficiency, renewable energy usage, and waste reduction achievements
```

### Query 8.3: Environmental Alerts
```
Get active environmental monitoring alerts, emission levels, and compliance status for each factory location
```

## 9. Maintenance & Asset Management

### Query 9.1: Maintenance Status Overview
```
Show scheduled maintenance, preventive maintenance completion rates, and asset health scores for each factory
```

### Query 9.2: Equipment Reliability Metrics
```
Get mean time between failures (MTBF), mean time to repair (MTTR), and overall equipment reliability by factory location
```

### Query 9.3: Spare Parts Inventory
```
Display spare parts availability, critical parts stock levels, and maintenance inventory status for each factory
```

## 10. Comparative Analysis

### Query 10.1: Factory Performance Benchmarking
```
Compare key performance indicators across all factory locations including production efficiency, quality, costs, and safety metrics
```

**SQL Query:**
```sql
WITH factory_metrics AS (
    SELECT 
        f.factory_id,
        f.factory_name,
        AVG(pr.actual_output * 100.0 / NULLIF(pr.target_output, 0)) as production_efficiency,
        AVG(qr.quality_score) as quality_score,
        AVG(pc.cost_per_unit) as cost_per_unit,
        AVG(sm.safety_score) as safety_score,
        AVG(ml.oee_score) as oee_score
    FROM genims_master_db.factories f
    LEFT JOIN genims_master_db.production_lines pl ON f.factory_id = pl.factory_id
    LEFT JOIN genims_operational_db.production_records pr ON pl.production_line_id = pr.production_line_id 
        AND pr.production_date >= CURRENT_DATE - INTERVAL '30 days'
    LEFT JOIN genims_mes_db.quality_records qr ON pr.production_record_id = qr.production_record_id
    LEFT JOIN genims_financial_db.production_costs pc ON pr.production_record_id = pc.production_record_id
    LEFT JOIN genims_hr_db.safety_metrics sm ON f.factory_id = sm.factory_id
    LEFT JOIN genims_operational_db.machine_logs ml ON pl.production_line_id = ml.production_line_id 
        AND ml.log_date >= CURRENT_DATE - INTERVAL '30 days'
    WHERE f.is_active = true
    GROUP BY f.factory_id, f.factory_name
),
industry_benchmarks AS (
    SELECT 
        AVG(production_efficiency) as avg_production_efficiency,
        AVG(quality_score) as avg_quality_score,
        AVG(cost_per_unit) as avg_cost_per_unit,
        AVG(safety_score) as avg_safety_score,
        AVG(oee_score) as avg_oee_score
    FROM factory_metrics
)
SELECT 
    fm.factory_id,
    fm.factory_name,
    ROUND(fm.production_efficiency, 2) as production_efficiency,
    ROUND(fm.quality_score, 2) as quality_score,
    ROUND(fm.cost_per_unit, 2) as cost_per_unit,
    ROUND(fm.safety_score, 2) as safety_score,
    ROUND(fm.oee_score, 2) as oee_score,
    ROUND((fm.production_efficiency - ib.avg_production_efficiency), 2) as efficiency_vs_avg,
    ROUND((fm.quality_score - ib.avg_quality_score), 2) as quality_vs_avg,
    ROUND((fm.cost_per_unit - ib.avg_cost_per_unit), 2) as cost_vs_avg,
    ROUND((fm.safety_score - ib.avg_safety_score), 2) as safety_vs_avg,
    RANK() OVER (ORDER BY (fm.production_efficiency + fm.quality_score + fm.safety_score + fm.oee_score - fm.cost_per_unit) DESC) as overall_rank
FROM factory_metrics fm
CROSS JOIN industry_benchmarks ib
ORDER BY overall_rank;
```

### Query 10.2: Best Practices Identification
```
Identify top-performing factories and their best practices in production efficiency, quality management, and cost optimization
```

### Query 10.3: Regional Performance Analysis
```
Analyze performance trends by geographic region, identifying regional strengths and improvement opportunities
```

## 11. Predictive Analytics & Forecasting

### Query 11.1: Production Forecasting
```
Get production forecasts for the next 30 days for each factory location based on historical trends and current capacity
```

### Query 11.2: Demand Planning by Location
```
Show demand forecasts and capacity planning recommendations for each factory based on market trends and historical data
```

### Query 11.3: Predictive Maintenance Alerts
```
Get predictive maintenance recommendations and equipment failure predictions for critical assets across all factories
```

## 12. Executive Dashboard Queries

### Query 12.1: Executive Summary by Location
```
Provide executive-level summary including overall factory performance, key metrics, critical issues, and strategic recommendations by location
```

**SQL Query:**
```sql
SELECT 
    f.factory_id,
    f.factory_name,
    CONCAT(f.city, ', ', f.country) as location,
    
    -- Production Metrics
    ROUND(AVG(pr.actual_output * 100.0 / NULLIF(pr.target_output, 0)), 2) as production_efficiency_percentage,
    SUM(pr.actual_output) as total_units_produced_today,
    
    -- Quality Metrics
    ROUND(AVG(qr.quality_score), 2) as quality_score,
    COUNT(CASE WHEN qr.defect_count > 0 THEN 1 END) as quality_issues_today,
    
    -- Financial Performance
    SUM(fs.revenue) as monthly_revenue,
    ROUND((SUM(fs.revenue - fs.cost_of_goods_sold) * 100.0 / NULLIF(SUM(fs.revenue), 0)), 2) as profit_margin_percentage,
    
    -- Critical Issues
    COUNT(CASE WHEN al.severity = 'critical' AND al.is_resolved = false THEN 1 END) as critical_alerts,
    COUNT(CASE WHEN si.incident_type = 'injury' AND si.incident_date = CURRENT_DATE THEN 1 END) as safety_incidents_today,
    
    -- Operational Status
    COUNT(DISTINCT CASE WHEN ml.status = 'running' THEN m.machine_id END) as machines_running,
    COUNT(DISTINCT m.machine_id) as total_machines,
    ROUND(AVG(ml.oee_score), 2) as overall_equipment_effectiveness,
    
    -- Strategic Indicators
    CASE 
        WHEN AVG(pr.actual_output * 100.0 / NULLIF(pr.target_output, 0)) >= 95 AND AVG(qr.quality_score) >= 95 THEN 'excellent'
        WHEN AVG(pr.actual_output * 100.0 / NULLIF(pr.target_output, 0)) >= 85 AND AVG(qr.quality_score) >= 90 THEN 'good'
        WHEN AVG(pr.actual_output * 100.0 / NULLIF(pr.target_output, 0)) >= 75 THEN 'satisfactory'
        ELSE 'needs_attention'
    END as performance_status,
    
    CASE 
        WHEN COUNT(CASE WHEN al.severity = 'critical' AND al.is_resolved = false THEN 1 END) > 0 THEN 'immediate_action_required'
        WHEN COUNT(CASE WHEN al.severity = 'high' AND al.is_resolved = false THEN 1 END) > 3 THEN 'attention_needed'
        ELSE 'stable'
    END as risk_level
    
FROM genims_master_db.factories f
LEFT JOIN genims_master_db.production_lines pl ON f.factory_id = pl.factory_id
LEFT JOIN genims_operational_db.production_records pr ON pl.production_line_id = pr.production_line_id 
    AND pr.production_date = CURRENT_DATE
LEFT JOIN genims_mes_db.quality_records qr ON pr.production_record_id = qr.production_record_id
LEFT JOIN genims_financial_db.financial_statements fs ON f.factory_id = fs.factory_id 
    AND EXTRACT(MONTH FROM fs.statement_period) = EXTRACT(MONTH FROM CURRENT_DATE)
LEFT JOIN genims_operational_db.alerts al ON f.factory_id = al.factory_id
LEFT JOIN genims_hr_db.safety_incidents si ON f.factory_id = si.factory_id
LEFT JOIN genims_master_db.machines m ON pl.production_line_id = m.production_line_id
LEFT JOIN genims_operational_db.machine_logs ml ON m.machine_id = ml.machine_id 
    AND ml.log_timestamp >= CURRENT_DATE
WHERE f.is_active = true
GROUP BY f.factory_id, f.factory_name, f.city, f.country
ORDER BY 
    CASE performance_status 
        WHEN 'excellent' THEN 1
        WHEN 'good' THEN 2
        WHEN 'satisfactory' THEN 3
        ELSE 4
    END,
    risk_level,
    f.factory_name;
```

### Query 12.2: Month-over-Month Trends
```
Show month-over-month performance trends for production, quality, costs, and efficiency across all factory locations
```

### Query 12.3: Strategic KPI Dashboard
```
Display strategic KPIs including overall equipment effectiveness, quality index, cost efficiency, and safety performance by factory
```

---

## API Conversion Guidelines

When converting these natural language queries to APIs, consider:

1. **Real-time Data**: Queries marked for real-time should use live data endpoints
2. **Time Ranges**: Include flexible time range parameters (today, week, month, quarter, year)
3. **Filtering**: Add factory-specific, region-specific, and department-specific filters
4. **Aggregation**: Support different aggregation levels (hourly, daily, weekly, monthly)
5. **Thresholds**: Include configurable threshold parameters for alerts and performance metrics
6. **Export Options**: Support data export in multiple formats (JSON, CSV, Excel)
7. **Pagination**: Implement pagination for large datasets
8. **Caching**: Use appropriate caching strategies for performance optimization

## Database Tables Referenced

These queries will primarily use data from:
- **Core Tables**: factories, production_lines, machines, employees
- **Operational Data**: production_records, machine_logs, sensor_readings, scada_machine_data
- **Manufacturing**: work_orders, quality_records, material_usage
- **Financial**: cost_centers, budget_lines, financial_statements
- **Warehouse**: inventory_levels, warehouse_operations
- **Transportation**: shipments, deliveries, transportation_costs
- **Human Resources**: employee_records, safety_incidents, training_records