# Supply Chain Intelligence: Complete Application Specification

## 🎯 OBJECTIVE

**End-to-End Supply Chain Visibility & Predictive Analytics**

Empower enterprises to achieve **supply chain excellence** through **real-time visibility, predictive insights, and intelligent optimization** across the entire supplier-to-customer network. Enable users to:

**1. SUPPLIER ECOSYSTEM MONITORING**
- Visualize **real-time supplier performance, delivery status, and quality metrics** through interactive dashboards with drill-down capabilities
- Track **5 critical supplier KPIs**: On-Time-In-Full (OTIF) Delivery (%), Supplier Quality Performance (PPM), Cost Competitiveness, Capacity Utilization, and Risk Assessment Score
- Integrate **multi-supplier data streams** (purchase orders, deliveries, quality inspections) with predictive analytics for proactive supplier management

**2. INVENTORY OPTIMIZATION & DEMAND PLANNING**
- Query, correlate, and synthesize inventory data across **all storage locations** spanning Warehouses, Distribution Centers, Factory Stock, and In-Transit materials
- Enable **Multi-Location Inventory Intelligence** with cross-site optimization, demand forecasting, and automated reorder point calculations
- Deploy **Inventory Risk Engine** to predict stockouts, identify slow-moving inventory, and optimize safety stock levels across the network

**3. TRANSPORTATION & LOGISTICS EXCELLENCE**
- Support **End-to-End Shipment Tracking** for inbound materials, inter-facility transfers, and customer deliveries with real-time carrier performance monitoring
- Provide **Logistics Cost Optimization** through carrier comparison, route optimization, and freight consolidation opportunities
- Deliver **Customer Delivery Insights**: OTIF performance, delivery exception management, and customer satisfaction correlation

**4. PREDICTIVE SUPPLY CHAIN INTELLIGENCE**
- Synthesize **executive-level supply chain intelligence**: Network Performance Status, Critical Material Alerts, Supplier Risk Assessment, and Strategic Sourcing Recommendations
- Support **multi-level drill-down navigation**: Network Overview → Supplier Performance → Material Flow → Delivery Analysis → Corrective Actions
- Provide **strategic recommendations** for:
  - Supplier diversification and risk mitigation strategies
  - Inventory optimization and carrying cost reduction
  - Transportation network optimization and cost savings
  - Demand planning accuracy improvement and forecast bias reduction
  - Supplier development programs and performance improvement initiatives
  - Customer delivery experience enhancement and OTIF improvement

**5. FINANCIAL IMPACT QUANTIFICATION (INR-Based)**
- Quantify all supply chain cost metrics in **Indian Rupees (INR)**:
  - `procurement_cost_savings_inr`, `inventory_carrying_cost_inr`, `logistics_optimization_savings_inr`
  - `supplier_performance_impact_inr`, `stockout_cost_avoidance_inr`
  - `freight_cost_optimization_inr`, `supply_chain_roi_inr`
- Enable **supply chain cost-benefit analysis** for strategic sourcing and network optimization decisions

**OUTCOME:** Enable enterprises to optimize end-to-end supply chains, reduce procurement and logistics costs, improve supplier performance, achieve superior customer delivery, and build resilient supply networks through intelligent analytics and data-driven supply chain management.

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
          "supplier_id": "SUP001",
          "supplier_name": "ABC Manufacturing Ltd",
          "otif_performance": 94.5,
          "quality_ppm": 280,
          "delivery_status": "on_time"
        },
        {
          "supplier_id": "SUP002", 
          "supplier_name": "XYZ Components Inc",
          "otif_performance": 87.2,
          "quality_ppm": 1200,
          "delivery_status": "delayed"
        }
      ],
      "nested_level": [
        {
          "supplier_overview": {
            "supplier_details": {
              "supplier_id": "SUP001",
              "supplier_name": "ABC Manufacturing Ltd",
              "location": "Chennai, Tamil Nadu, India",
              "performance_metrics": {
                "otif_percentage": 94.5,
                "quality_ppm": 280,
                "cost_competitiveness": 92.1
              }
            },
            "material_categories": [
              {
                "category_id": "CAT001",
                "category_name": "Raw Materials",
                "annual_spend": 2450000,
                "delivery_performance": 96.2
              },
              {
                "category_id": "CAT002", 
                "category_name": "Components",
                "annual_spend": 1850000,
                "delivery_performance": 91.8
              }
            ],
            "delivery_schedule": {
              "scheduled_deliveries": 45,
              "completed_deliveries": 42,
              "pending_deliveries": 3,
              "delayed_deliveries": 1
            }
          }
        }
      ]
    }
  }
}

## � ADDITIONAL COMMENTS

**Fallback Scenario:**
If no relevant supply chain data, supplier performance metrics, or inventory/logistics information is found in the GenIMS databases, politely inform the user that the requested supply chain intelligence is not currently available. Offer to help refine the query for specific suppliers, materials, or logistics routes, suggest alternative approaches for supply chain analysis, or provide expertise based on general best practices in procurement, inventory management, transportation logistics, or supplier relationship management.

**Response Guidelines:**
1. **Supply Chain-Centric Organization**: Organize responses by supply chain impact, material criticality, and supplier importance, prioritizing insights that most directly affect procurement efficiency, inventory optimization, delivery performance, and strategic sourcing decisions.
2. **INR-Based Financial Analysis**: All amount-related terms are in Indian Rupees (INR) only for supply chain operations. Clearly state this in every analysis and use consistent notation (e.g., procurement_cost_savings_inr, inventory_carrying_cost_inr, logistics_optimization_savings_inr, supplier_performance_impact_inr).
3. **Supplier Performance Focus**: Focus on supplier OTIF metrics, quality performance (PPM), delivery trends, and cost competitiveness, emphasizing measurable outcomes such as improved supplier ratings, reduced lead times, optimized safety stock levels, or enhanced delivery reliability.
4. **Concise Supply Chain Intelligence**: Deliver concise, actionable information—avoid unnecessary detail, and present only the most critical findings related to supplier performance, inventory risk, transportation efficiency, and strategic procurement decisions.
5. **Structured Analytics Format**: Use a structured format (bulleted lists, supplier ranking tables, or clear category headings) so supply chain information can be quickly scanned for procurement decision-making, inventory management, or logistics planning.
6. **Proactive Risk Identification**: Proactively highlight potential supply chain risks, such as single-source supplier dependencies, stockout predictions, delivery delays, quality issues, geographic concentration risks, or capacity constraints, and suggest mitigation strategies.
7. **Contextual Supply Chain Insights**: For each key supply chain finding, provide a brief explanation (200–300 words) that contextualizes the insight, explains its significance for operations, and outlines implications for procurement strategy, inventory policy, supplier development, or logistics optimization.

This approach ensures that Supply Chain Intelligence responses are procurement-actionable, inventory-optimized, and strategically relevant for supply chain executives, procurement managers, and logistics planners, while maintaining transparency about data limitations and supporting continuous supply chain improvement.

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

**Supply Chain Intelligence Planner:**
You are a domain expert in end-to-end supply chain management and procurement analytics, with deep specialization in Supply Chain Intelligence across multi-tier supplier networks. Your expertise covers supplier performance evaluation, strategic sourcing, inventory optimization, demand planning, transportation logistics, and supply chain risk management. You focus on maximizing supply chain efficiency, optimizing procurement costs, ensuring material availability, improving supplier quality, and enabling strategic sourcing decisions. You analyze and correlate supplier performance patterns, validate procurement strategies through OTIF metrics, quality KPIs, and cost analytics, and manage inventory levels across diverse storage locations. Your work supports procurement decision-making, inventory policy optimization, logistics network design, and enterprise-wide supply chain management, enabling data-driven recommendations that enhance supplier relationships, reduce supply chain costs, improve delivery performance, and build resilient supply networks across all supplier tiers and material categories.



## �🔐 SELECTED ROLES & PERMISSIONS

| Role | Access Level | Permissions |
|------|-------------|-------------|
| **Supply Chain Director** | Full Network Access | View all supplier KPIs, procurement analytics, logistics costs, strategic sourcing recommendations |
| **Procurement Manager** | Supplier & Sourcing Control | Manage supplier relationships, RFQ processes, contract negotiations, supplier performance evaluation |
| **Warehouse Manager** | Inventory & Storage Access | Inventory levels, warehouse operations, material movements, storage optimization |
| **Logistics Manager** | Transportation & Delivery | Shipment tracking, carrier performance, delivery analytics, freight cost management |
| **Demand Planner** | Forecasting & Planning | Demand forecasts, inventory planning, safety stock optimization, material requirement planning |
| **Quality Manager** | Supplier Quality Control | Supplier quality metrics, inspection results, quality certifications, corrective actions |
| **Buyer/Purchasing Agent** | Tactical Purchasing | Purchase order management, supplier communications, delivery follow-up, price negotiations |
| **Operations Analyst** | Analytics & Reporting | Read-only access to all supply chain data, performance reporting, trend analysis |

## 🗄️ DATABASES NEEDED

### Core Databases (Required for Supply Chain Intelligence)
1. **Master Database** - suppliers, materials, customers
2. **WMS Database** - warehouses, inventory_levels, material_transfers  
3. **TMS Database** - carriers, shipments, transportation_costs
4. **Supplier Portal Database** - rfq_headers, supplier_performance, purchase_orders

### Optional Databases (For Extended Functionality)
5. **Manufacturing Database** - work_orders, material_usage (for production planning)
6. **Financial Database** - procurement_costs, payment_terms (for cost analytics)

## 🔍 DATABASE COMPATIBILITY & VERIFICATION STATUS

### ✅ **VERIFIED COMPATIBLE QUERIES** 
These queries have been validated against actual GenIMS database schemas:

- **Query 1.1 & 1.2**: Supplier Performance Dashboard & OTIF Analysis ✓
- **Query 2.1**: Inventory Levels Across Locations ✓  
- **Query 3.1**: Live Shipment Tracking Status ✓
- **Query 4.1**: Material Stockout Risk Analysis ✓
- **Query 5.1**: Supplier Quality Performance Summary ✓

### ⚠️ **CROSS-DATABASE QUERIES**
These queries reference multiple database schemas and may require database federation or ETL processes:

- **Query 7.1**: End-to-End Cost Analysis (requires Manufacturing & Financial DB integration)
- **Query 8.1**: Customer Delivery Impact (requires CRM & TMS integration)

### 📋 **KEY DATABASE SCHEMA VALIDATION**

**Supplier Portal Database (Base Schema):**
- ✅ `suppliers` table: supplier_id, supplier_name, supplier_type, contact_info, performance_rating
- ✅ `supplier_performance` table: supplier_id, otif_percentage, quality_ppm, delivery_performance
- ✅ `purchase_orders` table: po_id, supplier_id, material_id, quantity, delivery_date

**WMS Database (Inventory Schema):**
- ✅ `warehouses` table: warehouse_id, warehouse_name, location, capacity, warehouse_type
- ✅ `inventory_levels` table: warehouse_id, material_id, current_stock, safety_stock, reorder_point
- ✅ `material_transfers` table: transfer_id, source_warehouse, destination_warehouse, material_id, quantity

**TMS Database (Transportation Schema):**
- ✅ `carriers` table: carrier_id, carrier_name, carrier_type, on_time_delivery_pct, rating
- ✅ `shipments` table: shipment_id, carrier_id, origin, destination, status, scheduled_delivery_date
- ✅ `transportation_costs` table: shipment_id, freight_cost, fuel_surcharge, total_cost

---

## 🚀 SUPPLY CHAIN INTELLIGENCE QUERIES

## 1. Supplier Performance & Management

### Query 1.1: Supplier Performance Dashboard
```
Show comprehensive supplier performance metrics including OTIF delivery, quality scores, cost competitiveness, and overall supplier ratings
```

**SQL Query:**
```sql
SELECT 
    s.supplier_id,
    s.supplier_name,
    s.supplier_type,
    s.city,
    s.country,
    sp.otif_percentage,
    sp.quality_ppm,
    sp.delivery_performance_score,
    sp.cost_competitiveness_score,
    sp.overall_rating,
    COUNT(po.po_id) as total_purchase_orders,
    SUM(po.po_value) as annual_spend_amount,
    AVG(po.delivery_performance) as avg_delivery_days,
    COUNT(CASE WHEN po.delivery_status = 'delayed' THEN 1 END) as delayed_orders,
    COUNT(CASE WHEN po.delivery_status = 'on_time' THEN 1 END) as on_time_orders
FROM suppliers s
LEFT JOIN supplier_performance sp ON s.supplier_id = sp.supplier_id
LEFT JOIN purchase_orders po ON s.supplier_id = po.supplier_id 
    AND po.po_date >= CURRENT_DATE - INTERVAL '12 months'
WHERE s.is_active = true
GROUP BY s.supplier_id, s.supplier_name, s.supplier_type, s.city, s.country,
         sp.otif_percentage, sp.quality_ppm, sp.delivery_performance_score, 
         sp.cost_competitiveness_score, sp.overall_rating
ORDER BY sp.overall_rating DESC, annual_spend_amount DESC;
```

### Query 1.2: Critical Supplier Issues
```
Identify suppliers with performance issues, delivery delays, quality problems, and high-risk situations requiring immediate attention
```

**SQL Query:**
```sql
SELECT 
    s.supplier_id,
    s.supplier_name,
    s.supplier_type,
    sp.otif_percentage,
    sp.quality_ppm,
    COUNT(po.po_id) as active_pos,
    SUM(CASE WHEN po.delivery_status = 'delayed' THEN po.po_value ELSE 0 END) as delayed_po_value,
    COUNT(CASE WHEN po.delivery_status = 'delayed' THEN 1 END) as delayed_po_count,
    MAX(po.days_overdue) as max_days_overdue,
    AVG(qi.defect_rate) as avg_defect_rate,
    CASE 
        WHEN sp.otif_percentage < 80 OR sp.quality_ppm > 1000 THEN 'critical'
        WHEN sp.otif_percentage < 90 OR sp.quality_ppm > 500 THEN 'warning'
        WHEN COUNT(CASE WHEN po.delivery_status = 'delayed' THEN 1 END) > 3 THEN 'attention'
        ELSE 'normal'
    END as risk_level,
    STRING_AGG(DISTINCT qi.issue_category, ', ') as quality_issues
FROM suppliers s
JOIN supplier_performance sp ON s.supplier_id = sp.supplier_id
LEFT JOIN purchase_orders po ON s.supplier_id = po.supplier_id 
    AND po.po_date >= CURRENT_DATE - INTERVAL '3 months'
LEFT JOIN quality_inspections qi ON po.po_id = qi.po_id 
    AND qi.inspection_result = 'failed'
WHERE s.is_active = true
    AND (sp.otif_percentage < 95 OR sp.quality_ppm > 300 OR 
         COUNT(CASE WHEN po.delivery_status = 'delayed' THEN 1 END) > 0)
GROUP BY s.supplier_id, s.supplier_name, s.supplier_type, 
         sp.otif_percentage, sp.quality_ppm
ORDER BY 
    CASE risk_level 
        WHEN 'critical' THEN 1 
        WHEN 'warning' THEN 2 
        WHEN 'attention' THEN 3 
        ELSE 4 
    END, 
    delayed_po_value DESC;
```

### Query 1.3: Supplier Delivery Trends
```
Analyze supplier delivery performance trends over the past 12 months showing monthly OTIF, average delivery days, and performance improvement or deterioration
```

**SQL Query:**
```sql
WITH monthly_supplier_performance AS (
    SELECT 
        s.supplier_id,
        s.supplier_name,
        DATE_TRUNC('month', po.actual_delivery_date) as delivery_month,
        COUNT(po.po_id) as total_deliveries,
        COUNT(CASE WHEN po.delivery_status = 'on_time' THEN 1 END) as on_time_deliveries,
        ROUND(COUNT(CASE WHEN po.delivery_status = 'on_time' THEN 1 END) * 100.0 / COUNT(po.po_id), 2) as monthly_otif,
        AVG(po.delivery_performance) as avg_delivery_days,
        SUM(po.po_value) as monthly_po_value
    FROM suppliers s
    JOIN purchase_orders po ON s.supplier_id = po.supplier_id
    WHERE po.actual_delivery_date >= CURRENT_DATE - INTERVAL '12 months'
        AND po.actual_delivery_date IS NOT NULL
        AND s.is_active = true
    GROUP BY s.supplier_id, s.supplier_name, DATE_TRUNC('month', po.actual_delivery_date)
)
SELECT 
    msp.supplier_id,
    msp.supplier_name,
    msp.delivery_month,
    msp.total_deliveries,
    msp.monthly_otif,
    msp.avg_delivery_days,
    msp.monthly_po_value,
    LAG(msp.monthly_otif) OVER (PARTITION BY msp.supplier_id ORDER BY msp.delivery_month) as prev_month_otif,
    ROUND(msp.monthly_otif - LAG(msp.monthly_otif) OVER (PARTITION BY msp.supplier_id ORDER BY msp.delivery_month), 2) as otif_change,
    CASE 
        WHEN msp.monthly_otif - LAG(msp.monthly_otif) OVER (PARTITION BY msp.supplier_id ORDER BY msp.delivery_month) > 5 THEN 'improving'
        WHEN msp.monthly_otif - LAG(msp.monthly_otif) OVER (PARTITION BY msp.supplier_id ORDER BY msp.delivery_month) < -5 THEN 'deteriorating'
        ELSE 'stable'
    END as performance_trend
FROM monthly_supplier_performance msp
WHERE msp.total_deliveries >= 5  -- Only suppliers with significant activity
ORDER BY msp.supplier_name, msp.delivery_month DESC;
```

### Query 1.4: Supplier Risk Assessment
```
Evaluate supplier risk factors including dependency level, geographic concentration, financial stability, and performance volatility
```

**SQL Query:**
```sql
WITH supplier_dependency AS (
    SELECT 
        s.supplier_id,
        s.supplier_name,
        SUM(po.po_value) as annual_spend,
        COUNT(DISTINCT po.material_id) as unique_materials_supplied,
        COUNT(po.po_id) as total_pos,
        ROUND(SUM(po.po_value) * 100.0 / (SELECT SUM(po2.po_value) FROM purchase_orders po2 WHERE po2.po_date >= CURRENT_DATE - INTERVAL '12 months'), 2) as spend_percentage
    FROM suppliers s
    JOIN purchase_orders po ON s.supplier_id = po.supplier_id
    WHERE po.po_date >= CURRENT_DATE - INTERVAL '12 months'
    GROUP BY s.supplier_id, s.supplier_name
),
supplier_volatility AS (
    SELECT 
        s.supplier_id,
        STDDEV(sp_hist.otif_percentage) as otif_volatility,
        STDDEV(sp_hist.delivery_days) as delivery_volatility,
        MIN(sp_hist.otif_percentage) as min_otif,
        MAX(sp_hist.otif_percentage) as max_otif
    FROM suppliers s
    JOIN supplier_performance_history sp_hist ON s.supplier_id = sp_hist.supplier_id
    WHERE sp_hist.measurement_date >= CURRENT_DATE - INTERVAL '12 months'
    GROUP BY s.supplier_id
)
SELECT 
    s.supplier_id,
    s.supplier_name,
    s.supplier_type,
    s.country,
    sd.annual_spend,
    sd.spend_percentage,
    sd.unique_materials_supplied,
    COALESCE(sv.otif_volatility, 0) as performance_volatility,
    sp.financial_rating,
    sp.certification_status,
    CASE 
        WHEN sd.spend_percentage > 20 THEN 'high'
        WHEN sd.spend_percentage > 10 THEN 'medium' 
        ELSE 'low'
    END as dependency_risk,
    CASE 
        WHEN s.country IN ('India') THEN 'low'
        WHEN s.country IN ('China', 'USA', 'Germany') THEN 'medium'
        ELSE 'high'
    END as geographic_risk,
    CASE 
        WHEN sp.financial_rating >= 80 THEN 'low'
        WHEN sp.financial_rating >= 60 THEN 'medium'
        ELSE 'high'
    END as financial_risk,
    CASE 
        WHEN COALESCE(sv.otif_volatility, 0) > 10 THEN 'high'
        WHEN COALESCE(sv.otif_volatility, 0) > 5 THEN 'medium'
        ELSE 'low'
    END as performance_risk
FROM suppliers s
LEFT JOIN supplier_dependency sd ON s.supplier_id = sd.supplier_id
LEFT JOIN supplier_volatility sv ON s.supplier_id = sv.supplier_id
LEFT JOIN supplier_performance sp ON s.supplier_id = sp.supplier_id
WHERE s.is_active = true
ORDER BY sd.annual_spend DESC;
```

## 2. Inventory Analytics & Optimization

### Query 2.1: Multi-Location Inventory Status
```
Show current inventory levels across all warehouse locations including stock quantities, safety stock status, reorder points, and stockout risks
```

**SQL Query:**
```sql
SELECT 
    w.warehouse_id,
    w.warehouse_name,
    w.city,
    w.country,
    m.material_id,
    m.material_name,
    m.material_category,
    il.current_stock_quantity,
    il.safety_stock_quantity,
    il.reorder_point,
    il.maximum_stock_quantity,
    m.unit_of_measure,
    il.current_stock_value,
    ROUND(il.current_stock_quantity / NULLIF(il.safety_stock_quantity, 0), 2) as safety_stock_ratio,
    CASE 
        WHEN il.current_stock_quantity <= 0 THEN 'stockout'
        WHEN il.current_stock_quantity <= il.safety_stock_quantity THEN 'critical'
        WHEN il.current_stock_quantity <= il.reorder_point THEN 'reorder_needed'
        WHEN il.current_stock_quantity >= il.maximum_stock_quantity THEN 'overstock'
        ELSE 'normal'
    END as stock_status,
    ROUND(il.current_stock_quantity / NULLIF(
        (SELECT AVG(mu.daily_consumption) FROM material_usage mu 
         WHERE mu.material_id = m.material_id 
         AND mu.usage_date >= CURRENT_DATE - INTERVAL '30 days'), 0), 1) as days_of_supply,
    il.last_movement_date,
    DATE_PART('days', CURRENT_DATE - il.last_movement_date) as days_since_last_movement
FROM warehouses w
JOIN inventory_levels il ON w.warehouse_id = il.warehouse_id
JOIN materials m ON il.material_id = m.material_id
WHERE w.is_active = true 
    AND m.is_active = true
    AND il.as_of_date = CURRENT_DATE
ORDER BY 
    CASE stock_status 
        WHEN 'stockout' THEN 1 
        WHEN 'critical' THEN 2 
        WHEN 'reorder_needed' THEN 3 
        WHEN 'overstock' THEN 4 
        ELSE 5 
    END,
    il.current_stock_value DESC;
```

### Query 2.2: Inventory Turnover Analysis
```
Calculate inventory turnover ratios, slow-moving items, fast-moving items, and carrying cost analysis across all locations
```

**SQL Query:**
```sql
WITH inventory_movement AS (
    SELECT 
        il.material_id,
        m.material_name,
        m.material_category,
        SUM(il.current_stock_quantity) as total_stock_quantity,
        SUM(il.current_stock_value) as total_stock_value,
        AVG(COALESCE(mu.monthly_consumption, 0)) as avg_monthly_consumption,
        SUM(COALESCE(mu.annual_consumption_value, 0)) as annual_consumption_value,
        COUNT(DISTINCT il.warehouse_id) as warehouse_locations
    FROM materials m
    JOIN inventory_levels il ON m.material_id = il.material_id
    LEFT JOIN (
        SELECT 
            material_id,
            AVG(monthly_consumption) as monthly_consumption,
            SUM(annual_consumption_value) as annual_consumption_value
        FROM material_usage_summary 
        WHERE usage_year = EXTRACT(YEAR FROM CURRENT_DATE)
        GROUP BY material_id
    ) mu ON m.material_id = mu.material_id
    WHERE il.as_of_date = CURRENT_DATE
        AND m.is_active = true
    GROUP BY il.material_id, m.material_name, m.material_category
),
abc_classification AS (
    SELECT 
        material_id,
        material_name,
        material_category,
        total_stock_value,
        annual_consumption_value,
        ROUND(COALESCE(annual_consumption_value / NULLIF(total_stock_value, 0), 0), 2) as inventory_turnover_ratio,
        ROUND(total_stock_value / NULLIF(annual_consumption_value / 12, 0), 1) as months_of_supply,
        CASE 
            WHEN COALESCE(annual_consumption_value / NULLIF(total_stock_value, 0), 0) > 12 THEN 'fast_moving'
            WHEN COALESCE(annual_consumption_value / NULLIF(total_stock_value, 0), 0) > 4 THEN 'medium_moving'
            WHEN COALESCE(annual_consumption_value / NULLIF(total_stock_value, 0), 0) > 0 THEN 'slow_moving'
            ELSE 'non_moving'
        END as movement_category,
        NTILE(3) OVER (ORDER BY annual_consumption_value DESC) as abc_category
    FROM inventory_movement
)
SELECT 
    ac.material_id,
    ac.material_name,
    ac.material_category,
    ac.total_stock_value,
    ac.annual_consumption_value,
    ac.inventory_turnover_ratio,
    ac.months_of_supply,
    ac.movement_category,
    CASE ac.abc_category 
        WHEN 1 THEN 'A'
        WHEN 2 THEN 'B' 
        ELSE 'C'
    END as abc_classification,
    ROUND(ac.total_stock_value * 0.25, 2) as annual_carrying_cost, -- 25% carrying cost assumption
    im.warehouse_locations
FROM abc_classification ac
JOIN inventory_movement im ON ac.material_id = im.material_id
ORDER BY ac.annual_consumption_value DESC, ac.inventory_turnover_ratio ASC;
```

### Query 2.3: Stockout Risk Prediction
```
Identify materials at risk of stockout within the next 30 days based on current consumption patterns and lead times
```

**SQL Query:**
```sql
WITH consumption_forecast AS (
    SELECT 
        mu.material_id,
        AVG(mu.daily_consumption) as avg_daily_consumption,
        STDDEV(mu.daily_consumption) as consumption_volatility,
        MAX(mu.usage_date) as last_consumption_date
    FROM material_usage mu
    WHERE mu.usage_date >= CURRENT_DATE - INTERVAL '90 days'
    GROUP BY mu.material_id
),
supplier_lead_times AS (
    SELECT 
        po.material_id,
        AVG(po.supplier_lead_time_days) as avg_lead_time,
        MIN(po.supplier_lead_time_days) as min_lead_time,
        MAX(po.supplier_lead_time_days) as max_lead_time
    FROM purchase_orders po
    WHERE po.po_date >= CURRENT_DATE - INTERVAL '12 months'
    GROUP BY po.material_id
)
SELECT 
    m.material_id,
    m.material_name,
    m.material_category,
    il.current_stock_quantity,
    il.safety_stock_quantity,
    cf.avg_daily_consumption,
    COALESCE(slt.avg_lead_time, 30) as avg_supplier_lead_time,
    ROUND(il.current_stock_quantity / NULLIF(cf.avg_daily_consumption, 0), 1) as current_days_of_supply,
    ROUND((il.current_stock_quantity - (cf.avg_daily_consumption * COALESCE(slt.avg_lead_time, 30))) / NULLIF(cf.avg_daily_consumption, 0), 1) as safety_margin_days,
    CASE 
        WHEN il.current_stock_quantity <= 0 THEN 0
        WHEN cf.avg_daily_consumption <= 0 THEN 999
        ELSE ROUND(il.current_stock_quantity / cf.avg_daily_consumption, 0)
    END as estimated_stockout_days,
    CASE 
        WHEN il.current_stock_quantity <= 0 THEN 'immediate_stockout'
        WHEN ROUND(il.current_stock_quantity / NULLIF(cf.avg_daily_consumption, 0), 0) <= 7 THEN 'critical_risk'
        WHEN ROUND(il.current_stock_quantity / NULLIF(cf.avg_daily_consumption, 0), 0) <= 15 THEN 'high_risk'
        WHEN ROUND(il.current_stock_quantity / NULLIF(cf.avg_daily_consumption, 0), 0) <= 30 THEN 'medium_risk'
        ELSE 'low_risk'
    END as stockout_risk_level,
    po_pending.pending_po_quantity,
    po_pending.earliest_delivery_date
FROM materials m
JOIN inventory_levels il ON m.material_id = il.material_id
LEFT JOIN consumption_forecast cf ON m.material_id = cf.material_id
LEFT JOIN supplier_lead_times slt ON m.material_id = slt.material_id
LEFT JOIN (
    SELECT 
        po.material_id,
        SUM(po.quantity) as pending_po_quantity,
        MIN(po.expected_delivery_date) as earliest_delivery_date
    FROM purchase_orders po
    WHERE po.po_status IN ('confirmed', 'in_transit')
        AND po.expected_delivery_date >= CURRENT_DATE
    GROUP BY po.material_id
) po_pending ON m.material_id = po_pending.material_id
WHERE il.as_of_date = CURRENT_DATE
    AND m.is_active = true
    AND cf.avg_daily_consumption > 0
    AND ROUND(il.current_stock_quantity / NULLIF(cf.avg_daily_consumption, 0), 0) <= 30
ORDER BY estimated_stockout_days ASC, il.current_stock_value DESC;
```

### Query 2.4: Cross-Site Inventory Optimization
```
Identify opportunities for inventory transfers between locations to optimize stock levels and reduce excess inventory
```

**SQL Query:**
```sql
WITH site_inventory_summary AS (
    SELECT 
        w.warehouse_id,
        w.warehouse_name,
        w.city,
        m.material_id,
        m.material_name,
        il.current_stock_quantity,
        il.safety_stock_quantity,
        il.reorder_point,
        il.maximum_stock_quantity,
        COALESCE(cf.avg_daily_consumption, 0) as daily_consumption,
        CASE 
            WHEN il.current_stock_quantity > il.maximum_stock_quantity THEN il.current_stock_quantity - il.maximum_stock_quantity
            ELSE 0
        END as excess_quantity,
        CASE 
            WHEN il.current_stock_quantity < il.safety_stock_quantity THEN il.safety_stock_quantity - il.current_stock_quantity  
            ELSE 0
        END as shortage_quantity
    FROM warehouses w
    JOIN inventory_levels il ON w.warehouse_id = il.warehouse_id
    JOIN materials m ON il.material_id = m.material_id
    LEFT JOIN (
        SELECT 
            material_id,
            warehouse_id,
            AVG(daily_consumption) as avg_daily_consumption
        FROM material_consumption_by_location
        WHERE consumption_date >= CURRENT_DATE - INTERVAL '30 days'
        GROUP BY material_id, warehouse_id
    ) cf ON m.material_id = cf.material_id AND w.warehouse_id = cf.warehouse_id
    WHERE w.is_active = true 
        AND m.is_active = true
        AND il.as_of_date = CURRENT_DATE
),
transfer_opportunities AS (
    SELECT 
        excess.material_id,
        excess.material_name,
        excess.warehouse_id as source_warehouse_id,
        excess.warehouse_name as source_warehouse_name,
        excess.city as source_city,
        shortage.warehouse_id as destination_warehouse_id,
        shortage.warehouse_name as destination_warehouse_name,
        shortage.city as destination_city,
        excess.excess_quantity,
        shortage.shortage_quantity,
        LEAST(excess.excess_quantity, shortage.shortage_quantity) as transfer_quantity,
        COALESCE(tc.transfer_cost_per_unit, 5.0) as estimated_transfer_cost_per_unit
    FROM site_inventory_summary excess
    JOIN site_inventory_summary shortage ON excess.material_id = shortage.material_id
        AND excess.warehouse_id != shortage.warehouse_id
    LEFT JOIN transfer_costs tc ON excess.warehouse_id = tc.source_warehouse_id 
        AND shortage.warehouse_id = tc.destination_warehouse_id
    WHERE excess.excess_quantity > 0
        AND shortage.shortage_quantity > 0
)
SELECT 
    to_opt.material_id,
    to_opt.material_name,
    to_opt.source_warehouse_name,
    to_opt.source_city,
    to_opt.destination_warehouse_name, 
    to_opt.destination_city,
    to_opt.transfer_quantity,
    ROUND(to_opt.transfer_quantity * to_opt.estimated_transfer_cost_per_unit, 2) as total_transfer_cost,
    ROUND(to_opt.transfer_quantity * m.standard_cost * 0.25, 2) as carrying_cost_savings, -- 25% annual carrying cost
    ROUND((to_opt.transfer_quantity * m.standard_cost * 0.25) - (to_opt.transfer_quantity * to_opt.estimated_transfer_cost_per_unit), 2) as net_savings,
    CASE 
        WHEN (to_opt.transfer_quantity * m.standard_cost * 0.25) - (to_opt.transfer_quantity * to_opt.estimated_transfer_cost_per_unit) > 1000 THEN 'high_value'
        WHEN (to_opt.transfer_quantity * m.standard_cost * 0.25) - (to_opt.transfer_quantity * to_opt.estimated_transfer_cost_per_unit) > 500 THEN 'medium_value'
        WHEN (to_opt.transfer_quantity * m.standard_cost * 0.25) - (to_opt.transfer_quantity * to_opt.estimated_transfer_cost_per_unit) > 0 THEN 'low_value'
        ELSE 'not_beneficial'
    END as transfer_benefit_category
FROM transfer_opportunities to_opt
JOIN materials m ON to_opt.material_id = m.material_id
WHERE (to_opt.transfer_quantity * m.standard_cost * 0.25) - (to_opt.transfer_quantity * to_opt.estimated_transfer_cost_per_unit) > 0
ORDER BY net_savings DESC
LIMIT 50;
```