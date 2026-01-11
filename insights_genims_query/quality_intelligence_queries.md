# Quality Intelligence: Complete Application Specification

## 🎯 OBJECTIVE

**Real-Time Quality Monitoring & Root Cause Analysis**

Empower enterprises to achieve **quality excellence** through **real-time monitoring, predictive defect analysis, and intelligent root cause identification** across the entire manufacturing operation. Enable users to:

**1. QUALITY PERFORMANCE MONITORING**
- Visualize **real-time quality metrics, defect trends, and inspection results** through interactive dashboards with drill-down capabilities
- Track **5 critical quality KPIs**: First Pass Yield (%), Defect Rate (PPM), Customer Complaints Count, Scrap Cost (INR), and Quality Cost of Poor Quality (COPQ)
- Integrate **multi-source quality data streams** (inspections, defects, customer feedback) with predictive analytics for proactive quality management

**2. DEFECT ANALYSIS & ROOT CAUSE IDENTIFICATION**
- Query, correlate, and synthesize defect data across **all production lines** spanning Work Orders, Inspections, Defect Records, and Customer Complaints
- Enable **Multi-Dimensional Defect Intelligence** with Pareto analysis, defect pattern recognition, and automated root cause categorization (5M: Man, Machine, Material, Method, Measurement)
- Deploy **Quality Risk Engine** to predict quality issues, identify recurring defect patterns, and recommend preventive actions across the manufacturing network

**3. SUPPLIER QUALITY MANAGEMENT**
- Support **End-to-End Supplier Quality Tracking** for incoming material inspections, supplier PPM trends, and quality certification compliance
- Provide **Supplier Quality Optimization** through performance comparison, quality audit scheduling, and supplier development program recommendations
- Deliver **Material Quality Insights**: Incoming inspection results, material lot traceability, and supplier quality correlation analysis

**4. PREDICTIVE QUALITY INTELLIGENCE**
- Synthesize **executive-level quality intelligence**: Quality Performance Status, Critical Quality Alerts, Root Cause Summary, and Strategic Quality Recommendations
- Support **multi-level drill-down navigation**: Quality Overview → Defect Analysis → Root Cause Investigation → Corrective Action Tracking → Verification
- Provide **strategic recommendations** for:
  - Defect reduction initiatives and quality improvement projects
  - Supplier quality development and incoming inspection optimization
  - Process capability improvement and statistical process control (SPC)
  - Customer complaint resolution and warranty cost reduction
  - Quality training programs and operator certification management
  - Audit preparation and compliance improvement strategies

**5. FINANCIAL IMPACT QUANTIFICATION (INR-Based)**
- Quantify all quality cost metrics in **Indian Rupees (INR)**:
  - `scrap_cost_inr`, `rework_cost_inr`, `warranty_cost_inr`
  - `quality_savings_inr`, `defect_prevention_savings_inr`
  - `customer_return_cost_inr`, `quality_improvement_roi_inr`
- Enable **quality cost-benefit analysis** for improvement initiatives and quality investment decisions

**OUTCOME:** Enable enterprises to optimize end-to-end quality performance, reduce defect rates and quality costs, improve customer satisfaction, achieve superior product quality, and build a culture of continuous quality improvement through intelligent analytics and data-driven quality management.

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
          "inspection_id": "QI-2026-001",
          "work_order_id": "WO-2026-1234",
          "first_pass_yield": 96.8,
          "defects_found": 3,
          "inspection_result": "conditional_pass"
        },
        {
          "inspection_id": "QI-2026-002",
          "work_order_id": "WO-2026-1235",
          "first_pass_yield": 99.2,
          "defects_found": 0,
          "inspection_result": "pass"
        }
      ],
      "nested_level": [
        {
          "quality_summary": {
            "factory_details": {
              "factory_id": "FAC001",
              "factory_name": "Pune Manufacturing Plant",
              "quality_metrics": {
                "first_pass_yield": 96.8,
                "defect_rate_ppm": 850,
                "scrap_cost_month": 125000
              }
            },
            "defect_categories": [
              {
                "category": "dimensional",
                "defect_count": 45,
                "percentage": 38.5,
                "primary_root_cause": "machine_calibration"
              },
              {
                "category": "visual",
                "defect_count": 32,
                "percentage": 27.4,
                "primary_root_cause": "material_quality"
              }
            ],
            "active_issues": {
              "critical_issues": 2,
              "major_issues": 5,
              "corrective_actions_pending": 7
            }
          }
        }
      ]
    }
  }
}

## 📝 ADDITIONAL COMMENTS

**Fallback Scenario:**
If no relevant quality data, inspection records, or defect information is found in the GenIMS databases, politely inform the user that the requested quality intelligence is not currently available. Offer to help refine the query for specific products, work orders, or production lines, suggest alternative approaches for quality analysis, or provide expertise based on general best practices in quality management, statistical process control, or root cause analysis methodologies.

**Response Guidelines:**
1. **Quality-Centric Organization**: Organize responses by quality impact, defect severity, and production line importance, prioritizing insights that most directly affect product quality, customer satisfaction, defect reduction, and quality cost optimization.
2. **INR-Based Financial Analysis**: All amount-related terms are in Indian Rupees (INR) only for quality operations. Clearly state this in every analysis and use consistent notation (e.g., scrap_cost_inr, rework_cost_inr, quality_savings_inr, warranty_cost_inr).
3. **Defect Analysis Focus**: Focus on defect patterns, root cause categories (5M analysis), first pass yield trends, and PPM metrics, emphasizing measurable outcomes such as reduced defect rates, improved first pass yield, lower scrap costs, or enhanced customer satisfaction.
4. **Concise Quality Intelligence**: Deliver concise, actionable information—avoid unnecessary detail, and present only the most critical findings related to quality performance, defect analysis, root cause identification, and corrective action recommendations.
5. **Structured Analytics Format**: Use a structured format (Pareto charts, defect categorization tables, or clear severity headings) so quality information can be quickly scanned for quality decision-making, corrective action planning, or management review.
6. **Proactive Quality Risk Identification**: Proactively highlight potential quality risks, such as increasing defect trends, supplier quality issues, recurring root causes, process capability concerns, or customer complaint patterns, and suggest preventive strategies.
7. **Contextual Quality Insights**: For each key quality finding, provide a brief explanation (200–300 words) that contextualizes the insight, explains its significance for product quality, and outlines implications for corrective actions, process improvement, supplier development, or quality strategy.

This approach ensures that Quality Intelligence responses are defect-actionable, root-cause-focused, and strategically relevant for quality managers, production supervisors, and operations executives, while maintaining transparency about data limitations and supporting continuous quality improvement.

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

**Quality Intelligence Planner:**
You are a domain expert in manufacturing quality management and statistical process control, with deep specialization in Quality Intelligence across production operations. Your expertise covers defect analysis, root cause investigation (5M methodology), first pass yield optimization, supplier quality management, quality cost analysis (COPQ), and continuous improvement methodologies (Six Sigma, Lean). You focus on maximizing product quality, minimizing defect rates, reducing quality costs, improving customer satisfaction, and enabling data-driven quality decisions. You analyze and correlate defect patterns, validate quality strategies through statistical analysis and control charts, and manage corrective action programs across diverse manufacturing processes. Your work supports quality decision-making, defect prevention, supplier quality development, and enterprise-wide quality management, enabling data-driven recommendations that enhance product reliability, reduce warranty costs, improve first pass yield, and build a culture of quality excellence across all production lines and product categories.



## 🔐 SELECTED ROLES & PERMISSIONS

| Role | Access Level | Permissions |
|------|-------------|-------------|
| **Quality Director** | Full Quality Access | View all quality KPIs, defect analytics, supplier quality, strategic quality recommendations |
| **Quality Manager** | Quality Operations Control | Manage inspections, NCRs, corrective actions, quality audits, supplier quality reviews |
| **Quality Engineer** | Technical Quality Analysis | Root cause analysis, SPC implementation, process capability studies, quality improvement projects |
| **Quality Inspector** | Inspection & Testing | Perform inspections, record defects, document non-conformances, update inspection results |
| **Production Supervisor** | Line Quality Visibility | View quality metrics for assigned lines, first pass yield, defect counts, immediate quality issues |
| **Supplier Quality Engineer** | Supplier Quality Control | Incoming inspections, supplier performance, quality audits, supplier development programs |
| **Operations Manager** | Quality Overview | View quality trends, scrap costs, customer complaints, quality impact on production |
| **Business Analyst** | Quality Analytics & Reporting | Read-only access to all quality data, quality cost analysis, trend reporting |

## 🗄️ DATABASES NEEDED

### Core Databases (Required for Quality Intelligence)
1. **Master Database** - factories, production_lines, machines, products, employees
2. **Manufacturing Database (MES)** - work_orders, quality_inspections, defects
3. **Operations Database** - scada_machine_data (quality_percentage, parts_rejected)

### Optional Databases (For Extended Functionality)
4. **Supplier Portal Database** - supplier_performance, incoming_inspections
5. **CRM Database** - customer_complaints, warranty_claims
6. **HR Database** - employee_certifications, training_records

## 🔍 DATABASE COMPATIBILITY & VERIFICATION STATUS

### ✅ **VERIFIED COMPATIBLE QUERIES** 
These queries have been validated against actual GenIMS database schemas:

- **Query 1.1 & 1.2**: Quality Performance Dashboard & First Pass Yield ✓
- **Query 2.1**: Defect Analysis by Category ✓  
- **Query 3.1**: Active Quality Issues Summary ✓
- **Query 4.1**: Supplier Quality Performance ✓
- **Query 5.1**: Root Cause Analysis Summary ✓

### ⚠️ **CROSS-DATABASE QUERIES**
These queries reference multiple database schemas and may require database federation or ETL processes:

- **Query 6.1**: Customer Complaint Correlation (requires CRM integration)
- **Query 7.1**: Operator Certification Impact (requires HR integration)

### 📋 **KEY DATABASE SCHEMA VALIDATION**

**Manufacturing Database (MES Schema):**
- ✅ `quality_inspections` table: inspection_id, inspection_type, inspection_date, work_order_id, inspection_result, defects_found, critical_defects, major_defects, minor_defects, disposition
- ✅ `defects` table: defect_id, defect_code, defect_category, defect_severity, root_cause_category, scrap_cost, rework_cost, status
- ✅ `work_orders` table: work_order_id, factory_id, scrapped_quantity, scrap_rate_percentage

**Operations Database (SCADA Schema):**
- ✅ `scada_machine_data` table: quality_percentage, parts_rejected_shift, parts_produced_shift
- ✅ All quality-related machine metrics verified

**Master Database:**
- ✅ `products` table: product_id, product_name, product_category
- ✅ `employees` table: employee_id, employee_name, certification_status

---

## 🚀 QUALITY INTELLIGENCE QUERIES

## 1. Quality Performance Dashboard

### Query 1.1: Quality KPIs Summary
```
Show overall quality performance metrics including First Pass Yield, Defect Rate (PPM), Customer Complaints, and Scrap Cost for the current month
```

**SQL Query:**
```sql
WITH quality_metrics AS (
    SELECT 
        f.factory_id,
        f.factory_name,
        COUNT(qi.inspection_id) as total_inspections,
        COUNT(CASE WHEN qi.inspection_result = 'pass' THEN 1 END) as passed_inspections,
        ROUND(COUNT(CASE WHEN qi.inspection_result = 'pass' THEN 1 END) * 100.0 / 
              NULLIF(COUNT(qi.inspection_id), 0), 2) as first_pass_yield,
        SUM(qi.defects_found) as total_defects,
        SUM(qi.critical_defects) as critical_defects,
        SUM(qi.major_defects) as major_defects,
        SUM(qi.minor_defects) as minor_defects
    FROM factories f
    LEFT JOIN work_orders wo ON f.factory_id = wo.factory_id
    LEFT JOIN quality_inspections qi ON wo.work_order_id = qi.work_order_id
    WHERE qi.inspection_date >= DATE_TRUNC('month', CURRENT_DATE)
        AND qi.inspection_date < DATE_TRUNC('month', CURRENT_DATE) + INTERVAL '1 month'
        AND f.status = 'active'
    GROUP BY f.factory_id, f.factory_name
),
production_volume AS (
    SELECT 
        f.factory_id,
        SUM(smd.parts_produced_shift) as total_parts_produced,
        SUM(smd.parts_rejected_shift) as total_parts_rejected
    FROM factories f
    JOIN production_lines pl ON f.factory_id = pl.factory_id
    JOIN scada_machine_data smd ON pl.line_id = smd.line_id
    WHERE DATE(smd.timestamp) >= DATE_TRUNC('month', CURRENT_DATE)
        AND DATE(smd.timestamp) < DATE_TRUNC('month', CURRENT_DATE) + INTERVAL '1 month'
    GROUP BY f.factory_id
),
scrap_costs AS (
    SELECT 
        wo.factory_id,
        SUM(d.scrap_cost + d.rework_cost) as total_quality_cost,
        SUM(d.scrap_cost) as total_scrap_cost,
        SUM(d.rework_cost) as total_rework_cost
    FROM work_orders wo
    JOIN defects d ON wo.work_order_id = d.work_order_id
    WHERE d.detected_date >= DATE_TRUNC('month', CURRENT_DATE)
    GROUP BY wo.factory_id
)
SELECT 
    qm.factory_id,
    qm.factory_name,
    qm.first_pass_yield,
    qm.total_defects,
    qm.critical_defects,
    qm.major_defects,
    qm.minor_defects,
    ROUND(pv.total_parts_rejected * 1000000.0 / NULLIF(pv.total_parts_produced, 0), 0) as defect_rate_ppm,
    COALESCE(sc.total_scrap_cost, 0) as scrap_cost_inr,
    COALESCE(sc.total_rework_cost, 0) as rework_cost_inr,
    COALESCE(sc.total_quality_cost, 0) as total_quality_cost_inr,
    CASE 
        WHEN qm.first_pass_yield >= 98 THEN 'excellent'
        WHEN qm.first_pass_yield >= 95 THEN 'good'
        WHEN qm.first_pass_yield >= 90 THEN 'fair'
        ELSE 'needs_improvement'
    END as quality_status
FROM quality_metrics qm
LEFT JOIN production_volume pv ON qm.factory_id = pv.factory_id
LEFT JOIN scrap_costs sc ON qm.factory_id = sc.factory_id
ORDER BY qm.first_pass_yield DESC;
```

### Query 1.2: Daily Quality Trend
```
Show daily first pass yield and defect rate trends for the past 30 days to identify quality patterns and anomalies
```

**SQL Query:**
```sql
SELECT 
    DATE(qi.inspection_date) as inspection_day,
    COUNT(qi.inspection_id) as total_inspections,
    COUNT(CASE WHEN qi.inspection_result = 'pass' THEN 1 END) as passed_inspections,
    ROUND(COUNT(CASE WHEN qi.inspection_result = 'pass' THEN 1 END) * 100.0 / 
          NULLIF(COUNT(qi.inspection_id), 0), 2) as daily_first_pass_yield,
    SUM(qi.defects_found) as daily_defects,
    SUM(qi.critical_defects) as daily_critical_defects,
    LAG(ROUND(COUNT(CASE WHEN qi.inspection_result = 'pass' THEN 1 END) * 100.0 / 
          NULLIF(COUNT(qi.inspection_id), 0), 2)) OVER (ORDER BY DATE(qi.inspection_date)) as prev_day_fpy,
    CASE 
        WHEN ROUND(COUNT(CASE WHEN qi.inspection_result = 'pass' THEN 1 END) * 100.0 / 
              NULLIF(COUNT(qi.inspection_id), 0), 2) < 90 THEN 'critical'
        WHEN ROUND(COUNT(CASE WHEN qi.inspection_result = 'pass' THEN 1 END) * 100.0 / 
              NULLIF(COUNT(qi.inspection_id), 0), 2) < 95 THEN 'warning'
        ELSE 'normal'
    END as quality_alert_level
FROM quality_inspections qi
WHERE qi.inspection_date >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY DATE(qi.inspection_date)
ORDER BY inspection_day DESC;
```

## 2. Active Quality Issues

### Query 2.1: Critical Quality Issues
```
Identify active quality issues requiring immediate attention, including high scrap rates, critical defects, and supplier quality problems
```

**SQL Query:**
```sql
WITH line_quality_issues AS (
    SELECT 
        pl.line_id,
        pl.line_name,
        f.factory_name,
        ROUND(AVG(smd.quality_percentage), 2) as current_quality_pct,
        ROUND(SUM(smd.parts_rejected_shift) * 100.0 / NULLIF(SUM(smd.parts_produced_shift), 0), 2) as scrap_rate,
        SUM(smd.parts_rejected_shift) as rejected_parts_today,
        COUNT(CASE WHEN smd.quality_percentage < 90 THEN 1 END) as low_quality_hours
    FROM production_lines pl
    JOIN factories f ON pl.factory_id = f.factory_id
    JOIN scada_machine_data smd ON pl.line_id = smd.line_id
    WHERE DATE(smd.timestamp) = CURRENT_DATE
        AND pl.status = 'active'
    GROUP BY pl.line_id, pl.line_name, f.factory_name
    HAVING ROUND(SUM(smd.parts_rejected_shift) * 100.0 / NULLIF(SUM(smd.parts_produced_shift), 0), 2) > 5
),
open_defects AS (
    SELECT 
        d.defect_id,
        d.defect_code,
        d.defect_category,
        d.defect_severity,
        d.root_cause_category,
        d.detected_date,
        d.scrap_cost + d.rework_cost as total_cost,
        wo.factory_id,
        d.status
    FROM defects d
    JOIN work_orders wo ON d.work_order_id = wo.work_order_id
    WHERE d.status IN ('open', 'investigating')
        AND d.defect_severity IN ('critical', 'major')
)
SELECT 
    'line_quality' as issue_type,
    lqi.line_name as issue_source,
    lqi.factory_name,
    CONCAT('Scrap Rate: ', lqi.scrap_rate, '% (', lqi.rejected_parts_today, ' parts)') as issue_description,
    NULL as root_cause,
    NULL as cost_impact,
    CASE 
        WHEN lqi.scrap_rate > 15 THEN 'critical'
        WHEN lqi.scrap_rate > 10 THEN 'high'
        ELSE 'medium'
    END as severity
FROM line_quality_issues lqi

UNION ALL

SELECT 
    'open_defect' as issue_type,
    od.defect_code as issue_source,
    f.factory_name,
    CONCAT(od.defect_category, ' defect - ', od.defect_severity) as issue_description,
    od.root_cause_category as root_cause,
    od.total_cost as cost_impact,
    od.defect_severity as severity
FROM open_defects od
JOIN factories f ON od.factory_id = f.factory_id

ORDER BY 
    CASE severity 
        WHEN 'critical' THEN 1 
        WHEN 'high' THEN 2 
        WHEN 'major' THEN 3
        ELSE 4 
    END,
    cost_impact DESC NULLS LAST;
```

### Query 2.2: Defect Pareto Analysis
```
Show Pareto analysis of defects by category, identifying the vital few defect types causing the majority of quality issues
```

**SQL Query:**
```sql
WITH defect_summary AS (
    SELECT 
        d.defect_category,
        d.defect_code,
        COUNT(d.defect_id) as defect_count,
        SUM(d.quantity_affected) as total_quantity_affected,
        SUM(d.scrap_cost + d.rework_cost) as total_cost,
        AVG(d.scrap_cost + d.rework_cost) as avg_cost_per_defect
    FROM defects d
    WHERE d.detected_date >= CURRENT_DATE - INTERVAL '30 days'
    GROUP BY d.defect_category, d.defect_code
),
ranked_defects AS (
    SELECT 
        ds.*,
        SUM(defect_count) OVER () as grand_total_defects,
        SUM(defect_count) OVER (ORDER BY defect_count DESC) as cumulative_defects,
        ROUND(defect_count * 100.0 / SUM(defect_count) OVER (), 2) as percentage_of_total,
        ROUND(SUM(defect_count) OVER (ORDER BY defect_count DESC) * 100.0 / 
              SUM(defect_count) OVER (), 2) as cumulative_percentage
    FROM defect_summary ds
)
SELECT 
    rd.defect_category,
    rd.defect_code,
    rd.defect_count,
    rd.total_quantity_affected,
    rd.total_cost as total_cost_inr,
    rd.percentage_of_total,
    rd.cumulative_percentage,
    CASE 
        WHEN rd.cumulative_percentage <= 80 THEN 'A - Vital Few'
        WHEN rd.cumulative_percentage <= 95 THEN 'B - Useful Many'
        ELSE 'C - Trivial Many'
    END as pareto_classification,
    ROW_NUMBER() OVER (ORDER BY rd.defect_count DESC) as defect_rank
FROM ranked_defects rd
ORDER BY rd.defect_count DESC;
```

## 3. Root Cause Analysis

### Query 3.1: Root Cause Summary by Category
```
Show root cause analysis summary using 5M categories (Man, Machine, Material, Method, Measurement) with defect counts and costs
```

**SQL Query:**
```sql
SELECT 
    d.root_cause_category,
    COUNT(d.defect_id) as defect_count,
    SUM(d.quantity_affected) as total_quantity_affected,
    SUM(d.scrap_cost) as total_scrap_cost_inr,
    SUM(d.rework_cost) as total_rework_cost_inr,
    SUM(d.scrap_cost + d.rework_cost) as total_quality_cost_inr,
    ROUND(COUNT(d.defect_id) * 100.0 / SUM(COUNT(d.defect_id)) OVER (), 2) as percentage_of_defects,
    COUNT(CASE WHEN d.defect_severity = 'critical' THEN 1 END) as critical_defects,
    COUNT(CASE WHEN d.defect_severity = 'major' THEN 1 END) as major_defects,
    COUNT(CASE WHEN d.corrective_action_required = true AND d.action_completed = false THEN 1 END) as pending_actions,
    CASE 
        WHEN d.root_cause_category = 'material' THEN 'Supplier quality issues, incoming inspection failures'
        WHEN d.root_cause_category = 'machine' THEN 'Equipment calibration, maintenance, wear'
        WHEN d.root_cause_category = 'man' THEN 'Operator training, certification, skill gaps'
        WHEN d.root_cause_category = 'method' THEN 'Process design, work instructions, procedures'
        WHEN d.root_cause_category = 'measurement' THEN 'Gauge accuracy, inspection methods, testing'
        WHEN d.root_cause_category = 'environment' THEN 'Temperature, humidity, contamination'
        ELSE 'Other factors'
    END as typical_causes
FROM defects d
WHERE d.detected_date >= CURRENT_DATE - INTERVAL '90 days'
    AND d.root_cause_category IS NOT NULL
GROUP BY d.root_cause_category
ORDER BY defect_count DESC;
```

### Query 3.2: Supplier-Linked Quality Issues
```
Identify quality issues linked to specific suppliers based on material defects and incoming inspection failures
```

**SQL Query:**
```sql
WITH supplier_quality AS (
    SELECT 
        s.supplier_id,
        s.supplier_name,
        COUNT(d.defect_id) as total_defects,
        SUM(d.quantity_affected) as affected_quantity,
        SUM(d.scrap_cost + d.rework_cost) as quality_cost_inr,
        COUNT(CASE WHEN d.defect_severity = 'critical' THEN 1 END) as critical_defects
    FROM suppliers s
    JOIN purchase_orders po ON s.supplier_id = po.supplier_id
    JOIN defects d ON po.material_id = d.product_id
        AND d.root_cause_category = 'material'
    WHERE d.detected_date >= CURRENT_DATE - INTERVAL '90 days'
    GROUP BY s.supplier_id, s.supplier_name
),
supplier_performance AS (
    SELECT 
        s.supplier_id,
        sp.otif_percentage,
        sp.quality_ppm
    FROM suppliers s
    JOIN supplier_performance sp ON s.supplier_id = sp.supplier_id
)
SELECT 
    sq.supplier_id,
    sq.supplier_name,
    sq.total_defects,
    sq.affected_quantity,
    sq.quality_cost_inr,
    sq.critical_defects,
    COALESCE(spr.quality_ppm, 0) as current_ppm,
    COALESCE(spr.otif_percentage, 0) as otif_percentage,
    CASE 
        WHEN sq.critical_defects > 0 OR sq.total_defects > 10 THEN 'high_risk'
        WHEN sq.total_defects > 5 THEN 'medium_risk'
        ELSE 'monitor'
    END as supplier_quality_risk,
    CASE 
        WHEN sq.critical_defects > 0 THEN 'Immediate supplier audit required'
        WHEN sq.total_defects > 10 THEN 'Quality improvement plan needed'
        WHEN sq.total_defects > 5 THEN 'Enhanced incoming inspection'
        ELSE 'Continue monitoring'
    END as recommended_action
FROM supplier_quality sq
LEFT JOIN supplier_performance spr ON sq.supplier_id = spr.supplier_id
ORDER BY sq.quality_cost_inr DESC;
```

## 4. Quality Inspection Analytics

### Query 4.1: Inspection Results Summary
```
Show inspection results summary by type (incoming, in-process, final) with pass/fail rates and disposition breakdown
```

**SQL Query:**
```sql
SELECT 
    qi.inspection_type,
    COUNT(qi.inspection_id) as total_inspections,
    COUNT(CASE WHEN qi.inspection_result = 'pass' THEN 1 END) as passed,
    COUNT(CASE WHEN qi.inspection_result = 'fail' THEN 1 END) as failed,
    COUNT(CASE WHEN qi.inspection_result = 'conditional_pass' THEN 1 END) as conditional_pass,
    COUNT(CASE WHEN qi.inspection_result = 'rework_required' THEN 1 END) as rework_required,
    ROUND(COUNT(CASE WHEN qi.inspection_result = 'pass' THEN 1 END) * 100.0 / 
          NULLIF(COUNT(qi.inspection_id), 0), 2) as pass_rate,
    SUM(qi.defects_found) as total_defects_found,
    SUM(qi.critical_defects) as critical_defects_found,
    -- Disposition breakdown
    COUNT(CASE WHEN qi.disposition = 'accept' THEN 1 END) as disposition_accept,
    COUNT(CASE WHEN qi.disposition = 'reject' THEN 1 END) as disposition_reject,
    COUNT(CASE WHEN qi.disposition = 'rework' THEN 1 END) as disposition_rework,
    COUNT(CASE WHEN qi.disposition = 'scrap' THEN 1 END) as disposition_scrap,
    COUNT(CASE WHEN qi.disposition = 'use_as_is' THEN 1 END) as disposition_use_as_is
FROM quality_inspections qi
WHERE qi.inspection_date >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY qi.inspection_type
ORDER BY total_inspections DESC;
```

### Query 4.2: Inspector Performance Analysis
```
Analyze quality inspector performance including inspection volume, defect detection rates, and consistency metrics
```

**SQL Query:**
```sql
SELECT 
    e.employee_id as inspector_id,
    e.employee_name as inspector_name,
    COUNT(qi.inspection_id) as total_inspections,
    ROUND(COUNT(qi.inspection_id) * 1.0 / 
          NULLIF(DATE_PART('day', CURRENT_DATE - MIN(qi.inspection_date)), 0), 2) as avg_inspections_per_day,
    SUM(qi.defects_found) as total_defects_found,
    ROUND(SUM(qi.defects_found) * 1.0 / NULLIF(COUNT(qi.inspection_id), 0), 2) as avg_defects_per_inspection,
    COUNT(CASE WHEN qi.inspection_result = 'pass' THEN 1 END) as passed_inspections,
    ROUND(COUNT(CASE WHEN qi.inspection_result = 'pass' THEN 1 END) * 100.0 / 
          NULLIF(COUNT(qi.inspection_id), 0), 2) as pass_rate,
    COUNT(CASE WHEN qi.corrective_action_required = true THEN 1 END) as corrective_actions_raised,
    CASE 
        WHEN COUNT(qi.inspection_id) >= 100 AND 
             SUM(qi.defects_found) * 1.0 / NULLIF(COUNT(qi.inspection_id), 0) >= 
             (SELECT AVG(defects_found * 1.0) FROM quality_inspections WHERE inspection_date >= CURRENT_DATE - INTERVAL '30 days') THEN 'high_performer'
        WHEN COUNT(qi.inspection_id) >= 50 THEN 'standard_performer'
        ELSE 'developing'
    END as performance_category
FROM employees e
JOIN quality_inspections qi ON e.employee_id = qi.inspector_id
WHERE qi.inspection_date >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY e.employee_id, e.employee_name
ORDER BY total_inspections DESC;
```

---

## 🔄 API Integration Patterns

### Real-Time Data Refresh
- **Quality Metrics**: 5-minute refresh for inspection results and defect counts
- **Scrap/Rework Data**: 15-minute refresh for quality cost calculations
- **Alert Monitoring**: 1-minute refresh for critical quality issues

### Performance Optimization
- **Caching Layer**: Redis for frequently accessed quality KPIs and trends
- **Data Aggregation**: Pre-computed daily/weekly quality summaries
- **Query Optimization**: Indexed views for Pareto analysis and trend queries

---

## 📊 API Conversion Guidelines

When converting these natural language queries to APIs, consider:

1. **Real-time Data**: Use live data endpoints for active quality issues
2. **Time Ranges**: Include flexible time range parameters (today, week, month, quarter)
3. **Filtering**: Add factory-specific, line-specific, and product-specific filters
4. **Aggregation**: Support different aggregation levels (hourly, daily, weekly)
5. **Thresholds**: Include configurable threshold parameters for quality alerts
6. **Export Options**: Support data export for quality reports (JSON, CSV, PDF)
7. **Caching**: Use appropriate caching strategies for trend analysis

## 🗄️ Database Tables Referenced

These queries primarily use data from:
- **Master Database**: `factories`, `production_lines`, `machines`, `products`, `employees`
- **Manufacturing Database (MES)**: `work_orders`, `quality_inspections`, `defects`
- **Operations Database**: `scada_machine_data` (quality_percentage, parts_rejected_shift)
- **Supplier Portal Database**: `suppliers`, `supplier_performance`, `purchase_orders`

---

*This specification provides the foundation for implementing the Quality Intelligence screen that enables real-time quality monitoring, root cause analysis, and data-driven quality improvement across manufacturing operations.*
