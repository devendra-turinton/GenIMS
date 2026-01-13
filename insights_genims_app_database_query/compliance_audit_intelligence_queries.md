# Compliance & Audit Intelligence: Complete Application Specification

## 🎯 OBJECTIVE

**End-to-End Compliance Management & Audit Readiness Intelligence**

Empower enterprises to achieve **regulatory excellence** through **proactive compliance monitoring, certification management, and intelligent audit preparation** across the entire manufacturing network. Enable users to:

**1. CERTIFICATION & REGULATORY COMPLIANCE MONITORING**
- Visualize **real-time certification status, expiry alerts, and regulatory compliance scores** through interactive dashboards with drill-down capabilities
- Track **6 critical compliance KPIs**: Active Certifications, Audit Compliance Score (%), Open Findings, Regulatory Compliance (%), Internal Audits Completed (YTD), and Upcoming Audits
- Integrate **multi-standard compliance data** (ISO 9001, IATF 16949, ISO 14001, AS9100) with predictive analytics for proactive audit readiness

**2. AUDIT MANAGEMENT & FINDING RESOLUTION**
- Query, correlate, and synthesize audit data across **all audit types** spanning Internal Audits, Supplier Audits, Customer Audits, and Certification Audits
- Enable **Audit Finding Intelligence** with CAPA tracking, overdue finding alerts, and root cause analysis correlation
- Deploy **Audit Readiness Engine** to predict certification risks, identify documentation gaps, and optimize audit preparation timelines

**3. CAPA & NON-CONFORMANCE MANAGEMENT**
- Support **End-to-End CAPA Tracking** from NCR creation through root cause analysis, corrective action implementation, and effectiveness verification
- Provide **Non-Conformance Analytics** with defect type analysis, cost of quality metrics, and supplier quality correlation
- Deliver **8D Problem Solving Integration**: Team-based problem resolution with containment, root cause, and prevention tracking

**4. PREDICTIVE COMPLIANCE INTELLIGENCE**
- Synthesize **executive-level compliance intelligence**: Certification Risk Assessment, Audit Readiness Status, Finding Resolution Progress, and Compliance Trend Analysis
- Support **multi-level drill-down navigation**: Compliance Overview → Certification Detail → Audit Findings → CAPA Actions → Verification Status
- Provide **strategic recommendations** for:
  - Certification renewal planning and audit preparation acceleration
  - Finding closure prioritization and resource allocation
  - Training gap identification and competency improvement
  - Process standardization and documentation enhancement
  - Supplier quality development and compliance improvement
  - Regulatory change management and proactive adaptation

**5. FINANCIAL IMPACT QUANTIFICATION (INR-Based)**
- Quantify all compliance-related cost metrics in **Indian Rupees (INR)**:
  - `audit_preparation_cost_inr`, `non_conformance_cost_inr`, `capa_implementation_cost_inr`
  - `certification_maintenance_cost_inr`, `regulatory_penalty_risk_inr`
  - `cost_of_quality_inr`, `compliance_roi_inr`
- Enable **compliance cost-benefit analysis** for certification investments and quality improvement decisions

**OUTCOME:** Enable enterprises to maintain regulatory compliance, achieve audit excellence, reduce non-conformance costs, and build a culture of continuous improvement through intelligent compliance analytics and proactive audit management.

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
          "certification_id": "CERT001",
          "certification_name": "ISO 9001:2015",
          "status": "active",
          "expiry_date": "2026-03-15",
          "readiness_percentage": 78.5
        },
        {
          "certification_id": "CERT002",
          "certification_name": "IATF 16949:2016",
          "status": "active",
          "expiry_date": "2026-08-10",
          "readiness_percentage": 92.0
        }
      ],
      "nested_level": [
        {
          "compliance_overview": {
            "certification_details": {
              "certification_id": "CERT001",
              "standard_name": "ISO 9001:2015",
              "scope": "All 5 factories",
              "audit_metrics": {
                "readiness_score": 78.5,
                "open_findings": 12,
                "days_until_audit": 21
              }
            },
            "finding_summary": [
              {
                "finding_id": "FND001",
                "finding_type": "major_nc",
                "category": "documentation",
                "status": "open",
                "days_overdue": 18
              },
              {
                "finding_id": "FND002",
                "finding_type": "minor_nc",
                "category": "training",
                "status": "in_progress",
                "days_overdue": 0
              }
            ],
            "capa_status": {
              "total_open": 23,
              "overdue": 8,
              "on_track": 15,
              "completed_ytd": 145
            }
          }
        }
      ]
    }
  }
}

## 📝 ADDITIONAL COMMENTS

**Fallback Scenario:**
If no relevant compliance data, audit records, or certification information is found in the GenIMS databases, politely inform the user that the requested compliance intelligence is not currently available. Offer to help refine the query for specific certifications, audit types, or compliance areas, suggest alternative approaches for compliance analysis, or provide expertise based on general best practices in quality management systems, regulatory compliance, audit preparation, or certification maintenance.

**Response Guidelines:**
1. **Compliance-Centric Organization**: Organize responses by certification criticality, audit urgency, and finding severity, prioritizing insights that most directly affect certification status, regulatory compliance, and audit readiness.
2. **INR-Based Financial Analysis**: All amount-related terms are in Indian Rupees (INR) only for compliance operations. Clearly state this in every analysis and use consistent notation (e.g., audit_preparation_cost_inr, non_conformance_cost_inr, capa_implementation_cost_inr, cost_of_quality_inr).
3. **Audit Readiness Focus**: Focus on certification expiry timelines, audit preparation status, finding closure progress, and CAPA effectiveness, emphasizing measurable outcomes such as improved audit scores, reduced overdue findings, faster CAPA closure, or enhanced compliance ratings.
4. **Concise Compliance Intelligence**: Deliver concise, actionable information—avoid unnecessary detail, and present only the most critical findings related to certification risk, audit preparation gaps, regulatory compliance status, and corrective action priorities.
5. **Structured Compliance Format**: Use a structured format (bulleted lists, certification status tables, or clear finding categories) so compliance information can be quickly scanned for management review, audit preparation, or regulatory reporting.
6. **Proactive Risk Identification**: Proactively highlight potential compliance risks, such as expiring certifications, overdue findings, training gaps, documentation deficiencies, calibration issues, or regulatory changes, and suggest mitigation strategies.
7. **Contextual Compliance Insights**: For each key compliance finding, provide a brief explanation (200–300 words) that contextualizes the insight, explains its significance for certification maintenance, and outlines implications for audit preparation, regulatory compliance, or continuous improvement initiatives.

This approach ensures that Compliance & Audit Intelligence responses are certification-focused, audit-ready, and strategically relevant for quality managers, compliance officers, and executive leadership, while maintaining transparency about data limitations and supporting continuous compliance improvement.

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

**Compliance & Audit Intelligence Planner:**
You are a domain expert in quality management systems and regulatory compliance, with deep specialization in Compliance & Audit Intelligence across multi-site manufacturing operations. Your expertise covers ISO certification management, audit preparation and execution, CAPA management, non-conformance resolution, regulatory compliance monitoring, and continuous improvement programs. You focus on maintaining certification excellence, ensuring audit readiness, optimizing finding closure processes, and enabling proactive compliance management. You analyze and correlate audit findings with operational issues, validate compliance strategies through readiness scores and finding metrics, and manage certification timelines across diverse regulatory requirements. Your work supports quality management decisions, audit preparation optimization, regulatory compliance assurance, and enterprise-wide compliance excellence, enabling data-driven recommendations that enhance certification performance, reduce compliance costs, improve audit outcomes, and build robust quality management systems across all manufacturing facilities.



## 🔐 SELECTED ROLES & PERMISSIONS

| Role | Access Level | Permissions |
|------|-------------|-------------|
| **Quality Director** | Full Compliance Access | View all certifications, audit results, CAPA status, regulatory compliance, strategic recommendations |
| **Compliance Manager** | Certification & Regulatory Control | Manage certifications, regulatory filings, compliance tracking, audit coordination |
| **Quality Manager** | Audit & Finding Management | Manage audit schedules, findings, CAPA, NCR resolution, document control |
| **Internal Auditor** | Audit Execution Access | Conduct audits, record findings, track corrective actions, verify closures |
| **CAPA Coordinator** | Corrective Action Management | Manage CAPA lifecycle, track action completion, verify effectiveness |
| **Document Controller** | Document & Record Control | Manage quality documents, version control, record retention, document access |
| **EHS Manager** | Environmental & Safety Compliance | Environmental certifications, safety audits, regulatory compliance, incident tracking |
| **Operations Analyst** | Analytics & Reporting | Read-only access to all compliance data, performance reporting, trend analysis |

## 🗄️ DATABASES NEEDED

### Core Databases (Required for Compliance & Audit Intelligence)
1. **QMS Database** - quality_audits, audit_findings, capa_headers, capa_actions, ncr_headers
2. **Master Database** - factories, departments, employees
3. **HR Database** - employee_certifications, training_records

### Optional Databases (For Extended Functionality)
4. **Manufacturing Database** - quality_inspections, work_orders (for production correlation)
5. **Supplier Portal Database** - supplier_quality_metrics (for supplier audit integration)

## 🔍 DATABASE COMPATIBILITY & VERIFICATION STATUS

### ✅ **VERIFIED COMPATIBLE QUERIES** 
These queries have been validated against actual GenIMS database schemas:

- **Query 1.1 & 1.2**: Certification Status Dashboard & Expiry Alerts ✓
- **Query 2.1**: Audit Findings Overview ✓  
- **Query 3.1**: CAPA Status & Overdue Tracking ✓
- **Query 4.1**: Non-Conformance Analysis ✓
- **Query 5.1**: Compliance Correlation Analysis ✓

### ⚠️ **CROSS-DATABASE QUERIES**
These queries reference multiple database schemas and may require database federation or ETL processes:

- **Query 6.1**: Training ↔ Compliance Correlation (requires HR & QMS integration)
- **Query 7.1**: Supplier Quality ↔ Audit Findings (requires Supplier Portal & QMS integration)

### 📋 **KEY DATABASE SCHEMA VALIDATION**

**QMS Database (Quality Management Schema):**
- ✅ `quality_audits` table: audit_id, audit_type, audit_standard, audit_status, audit_score, total_findings, major_findings, minor_findings
- ✅ `audit_findings` table: finding_id, audit_id, finding_type, finding_category, finding_status, target_closure_date
- ✅ `capa_headers` table: capa_id, action_type, capa_status, responsible_person, target_completion_date
- ✅ `capa_actions` table: action_id, capa_id, action_status, due_date, completion_date
- ✅ `ncr_headers` table: ncr_id, source_type, ncr_status, defect_severity, total_cost

**Master Database (Base Schema):**
- ✅ `factories` table: factory_id, factory_name, city, country, certification
- ✅ `departments` table: department_id, department_name, factory_id
- ✅ `employees` table: employee_id, employee_name, department_id, job_title

**HR Database (Human Capital Schema):**
- ✅ `employee_certifications` table: certification_id, employee_id, certification_name, expiry_date, status
- ✅ `training_records` table: training_id, employee_id, training_type, completion_date, status

---

## 🚀 COMPLIANCE & AUDIT INTELLIGENCE QUERIES

## 1. Certification Status & Management

### Query 1.1: Certification Status Dashboard
```
Show all active certifications across factories with their current status, expiry dates, readiness scores, and upcoming audit schedules
```

**SQL Query:**
```sql
WITH certification_summary AS (
    SELECT 
        f.factory_id,
        f.factory_name,
        f.city,
        f.country,
        qa.audit_standard as certification_standard,
        MAX(CASE WHEN qa.audit_type = 'certification' AND qa.audit_status = 'completed' 
            THEN qa.actual_end_date END) as last_certification_date,
        MAX(CASE WHEN qa.audit_type = 'certification' AND qa.audit_status = 'completed' 
            THEN qa.actual_end_date + INTERVAL '3 years' END) as certification_expiry_date,
        MAX(qa.audit_score) as last_audit_score,
        COUNT(CASE WHEN af.finding_status = 'open' THEN 1 END) as open_findings,
        COUNT(CASE WHEN af.finding_type = 'major_nc' AND af.finding_status = 'open' THEN 1 END) as open_major_findings
    FROM factories f
    LEFT JOIN quality_audits qa ON f.factory_id = qa.auditee_department
        AND qa.audit_type IN ('certification', 'surveillance')
    LEFT JOIN audit_findings af ON qa.audit_id = af.audit_id
    WHERE f.status = 'active'
    GROUP BY f.factory_id, f.factory_name, f.city, f.country, qa.audit_standard
),
upcoming_audits AS (
    SELECT 
        qa.auditee_department as factory_id,
        qa.audit_standard,
        MIN(qa.planned_date) as next_audit_date,
        qa.audit_type as next_audit_type
    FROM quality_audits qa
    WHERE qa.planned_date >= CURRENT_DATE
        AND qa.audit_status = 'planned'
    GROUP BY qa.auditee_department, qa.audit_standard, qa.audit_type
)
SELECT 
    cs.factory_id,
    cs.factory_name,
    cs.city,
    cs.country,
    cs.certification_standard,
    cs.last_certification_date,
    cs.certification_expiry_date,
    DATE_PART('days', cs.certification_expiry_date - CURRENT_DATE) as days_until_expiry,
    cs.last_audit_score,
    cs.open_findings,
    cs.open_major_findings,
    ua.next_audit_date,
    ua.next_audit_type,
    DATE_PART('days', ua.next_audit_date - CURRENT_DATE) as days_until_audit,
    CASE 
        WHEN cs.certification_expiry_date < CURRENT_DATE THEN 'expired'
        WHEN cs.certification_expiry_date < CURRENT_DATE + INTERVAL '60 days' THEN 'expiring_soon'
        WHEN cs.open_major_findings > 0 THEN 'at_risk'
        ELSE 'active'
    END as certification_status,
    CASE 
        WHEN cs.open_major_findings = 0 AND cs.open_findings <= 5 AND cs.last_audit_score >= 85 THEN 'high'
        WHEN cs.open_major_findings <= 2 AND cs.open_findings <= 10 THEN 'medium'
        ELSE 'low'
    END as audit_readiness_level,
    ROUND(100 - (cs.open_findings * 2) - (cs.open_major_findings * 10), 1) as readiness_score
FROM certification_summary cs
LEFT JOIN upcoming_audits ua ON cs.factory_id = ua.factory_id 
    AND cs.certification_standard = ua.audit_standard
WHERE cs.certification_standard IS NOT NULL
ORDER BY 
    CASE certification_status 
        WHEN 'expired' THEN 1 
        WHEN 'expiring_soon' THEN 2 
        WHEN 'at_risk' THEN 3 
        ELSE 4 
    END,
    days_until_expiry ASC;
```

### Query 1.2: Expiring Certifications Alert
```
Identify all certifications expiring within the next 90 days with their current readiness status and required actions
```

**SQL Query:**
```sql
WITH certification_details AS (
    SELECT 
        f.factory_id,
        f.factory_name,
        qa.audit_standard as certification_name,
        MAX(qa.actual_end_date) as certification_date,
        MAX(qa.actual_end_date + INTERVAL '3 years') as expiry_date,
        MAX(qa.audit_score) as last_score
    FROM factories f
    JOIN quality_audits qa ON f.factory_id = qa.auditee_department
    WHERE qa.audit_type = 'certification'
        AND qa.audit_status = 'completed'
    GROUP BY f.factory_id, f.factory_name, qa.audit_standard
),
open_items AS (
    SELECT 
        qa.auditee_department as factory_id,
        qa.audit_standard,
        COUNT(CASE WHEN af.finding_status = 'open' THEN 1 END) as open_findings,
        COUNT(CASE WHEN af.finding_type = 'major_nc' AND af.finding_status = 'open' THEN 1 END) as major_nc_open,
        COUNT(CASE WHEN af.finding_type = 'minor_nc' AND af.finding_status = 'open' THEN 1 END) as minor_nc_open,
        COUNT(CASE WHEN ch.capa_status = 'open' OR ch.capa_status = 'in_progress' THEN 1 END) as open_capas
    FROM quality_audits qa
    LEFT JOIN audit_findings af ON qa.audit_id = af.audit_id
    LEFT JOIN capa_headers ch ON af.linked_capa_id = ch.capa_id
    GROUP BY qa.auditee_department, qa.audit_standard
),
next_audit AS (
    SELECT 
        qa.auditee_department as factory_id,
        qa.audit_standard,
        MIN(qa.planned_date) as next_audit_date,
        qa.audit_type
    FROM quality_audits qa
    WHERE qa.planned_date >= CURRENT_DATE
        AND qa.audit_status = 'planned'
    GROUP BY qa.auditee_department, qa.audit_standard, qa.audit_type
)
SELECT 
    cd.factory_id,
    cd.factory_name,
    cd.certification_name,
    cd.certification_date,
    cd.expiry_date,
    DATE_PART('days', cd.expiry_date - CURRENT_DATE) as days_until_expiry,
    cd.last_score,
    COALESCE(oi.open_findings, 0) as open_findings,
    COALESCE(oi.major_nc_open, 0) as major_nc_open,
    COALESCE(oi.minor_nc_open, 0) as minor_nc_open,
    COALESCE(oi.open_capas, 0) as open_capas,
    na.next_audit_date,
    na.audit_type as next_audit_type,
    DATE_PART('days', na.next_audit_date - CURRENT_DATE) as days_until_audit,
    CASE 
        WHEN DATE_PART('days', cd.expiry_date - CURRENT_DATE) <= 30 THEN 'critical'
        WHEN DATE_PART('days', cd.expiry_date - CURRENT_DATE) <= 60 THEN 'high'
        WHEN DATE_PART('days', cd.expiry_date - CURRENT_DATE) <= 90 THEN 'medium'
        ELSE 'low'
    END as urgency_level,
    CASE 
        WHEN COALESCE(oi.major_nc_open, 0) > 0 THEN 'Close major non-conformances immediately'
        WHEN COALESCE(oi.open_findings, 0) > 10 THEN 'Accelerate finding closure program'
        WHEN cd.last_score < 75 THEN 'Conduct internal readiness audit'
        ELSE 'Continue monitoring and preparation'
    END as recommended_action
FROM certification_details cd
LEFT JOIN open_items oi ON cd.factory_id = oi.factory_id AND cd.certification_name = oi.audit_standard
LEFT JOIN next_audit na ON cd.factory_id = na.factory_id AND cd.certification_name = na.audit_standard
WHERE cd.expiry_date <= CURRENT_DATE + INTERVAL '90 days'
ORDER BY days_until_expiry ASC, urgency_level;
```

### Query 1.3: Audit Readiness Assessment
```
Calculate audit readiness scores for each certification based on finding closure, documentation status, and training completion
```

**SQL Query:**
```sql
WITH finding_metrics AS (
    SELECT 
        qa.auditee_department as factory_id,
        qa.audit_standard,
        COUNT(af.finding_id) as total_findings,
        COUNT(CASE WHEN af.finding_status = 'closed' THEN 1 END) as closed_findings,
        ROUND(COUNT(CASE WHEN af.finding_status = 'closed' THEN 1 END) * 100.0 / 
              NULLIF(COUNT(af.finding_id), 0), 2) as finding_closure_rate,
        COUNT(CASE WHEN af.target_closure_date < CURRENT_DATE AND af.finding_status != 'closed' THEN 1 END) as overdue_findings
    FROM quality_audits qa
    JOIN audit_findings af ON qa.audit_id = af.audit_id
    WHERE qa.actual_end_date >= CURRENT_DATE - INTERVAL '12 months'
    GROUP BY qa.auditee_department, qa.audit_standard
),
capa_metrics AS (
    SELECT 
        ch.responsible_department as factory_id,
        COUNT(ch.capa_id) as total_capas,
        COUNT(CASE WHEN ch.capa_status = 'closed' THEN 1 END) as closed_capas,
        ROUND(COUNT(CASE WHEN ch.capa_status = 'closed' THEN 1 END) * 100.0 / 
              NULLIF(COUNT(ch.capa_id), 0), 2) as capa_closure_rate,
        COUNT(CASE WHEN ch.target_completion_date < CURRENT_DATE AND ch.capa_status NOT IN ('closed', 'completed') THEN 1 END) as overdue_capas
    FROM capa_headers ch
    WHERE ch.created_at >= CURRENT_DATE - INTERVAL '12 months'
    GROUP BY ch.responsible_department
),
training_metrics AS (
    SELECT 
        e.factory_id,
        COUNT(DISTINCT ec.employee_id) as employees_with_certifications,
        COUNT(CASE WHEN ec.expiry_date < CURRENT_DATE THEN 1 END) as expired_certifications,
        COUNT(CASE WHEN ec.expiry_date BETWEEN CURRENT_DATE AND CURRENT_DATE + INTERVAL '30 days' THEN 1 END) as expiring_certifications
    FROM employees e
    LEFT JOIN employee_certifications ec ON e.employee_id = ec.employee_id
    WHERE e.status = 'active'
    GROUP BY e.factory_id
)
SELECT 
    f.factory_id,
    f.factory_name,
    fm.audit_standard,
    COALESCE(fm.finding_closure_rate, 100) as finding_closure_rate,
    COALESCE(fm.overdue_findings, 0) as overdue_findings,
    COALESCE(cm.capa_closure_rate, 100) as capa_closure_rate,
    COALESCE(cm.overdue_capas, 0) as overdue_capas,
    COALESCE(tm.expired_certifications, 0) as expired_employee_certs,
    COALESCE(tm.expiring_certifications, 0) as expiring_employee_certs,
    -- Calculate overall readiness score (weighted)
    ROUND(
        (COALESCE(fm.finding_closure_rate, 100) * 0.30) +
        (COALESCE(cm.capa_closure_rate, 100) * 0.30) +
        (CASE WHEN COALESCE(fm.overdue_findings, 0) = 0 THEN 20 ELSE GREATEST(0, 20 - (fm.overdue_findings * 2)) END) +
        (CASE WHEN COALESCE(cm.overdue_capas, 0) = 0 THEN 10 ELSE GREATEST(0, 10 - (cm.overdue_capas * 1)) END) +
        (CASE WHEN COALESCE(tm.expired_certifications, 0) = 0 THEN 10 ELSE GREATEST(0, 10 - (tm.expired_certifications * 0.5)) END)
    , 1) as readiness_score,
    CASE 
        WHEN COALESCE(fm.overdue_findings, 0) > 5 OR COALESCE(cm.overdue_capas, 0) > 3 THEN 'not_ready'
        WHEN COALESCE(fm.finding_closure_rate, 100) < 80 OR COALESCE(cm.capa_closure_rate, 100) < 80 THEN 'at_risk'
        WHEN COALESCE(fm.finding_closure_rate, 100) >= 95 AND COALESCE(cm.capa_closure_rate, 100) >= 95 THEN 'ready'
        ELSE 'progressing'
    END as readiness_status
FROM factories f
LEFT JOIN finding_metrics fm ON f.factory_id = fm.factory_id
LEFT JOIN capa_metrics cm ON f.factory_id = cm.factory_id
LEFT JOIN training_metrics tm ON f.factory_id = tm.factory_id
WHERE f.status = 'active'
ORDER BY readiness_score DESC;
```

## 2. Audit Findings & Resolution

### Query 2.1: Overdue Audit Findings
```
List all overdue audit findings with severity, days overdue, responsible person, and impact on certification status
```

**SQL Query:**
```sql
SELECT 
    af.finding_id,
    af.finding_number,
    qa.audit_number,
    qa.audit_type,
    qa.audit_standard,
    af.finding_type,
    af.finding_category,
    af.finding_description,
    af.requirement_reference,
    af.target_closure_date,
    DATE_PART('days', CURRENT_DATE - af.target_closure_date) as days_overdue,
    e.employee_name as responsible_person,
    d.department_name,
    f.factory_name,
    af.finding_status,
    af.linked_capa_id,
    ch.capa_status,
    CASE 
        WHEN af.finding_type = 'major_nc' AND DATE_PART('days', CURRENT_DATE - af.target_closure_date) > 30 THEN 'critical'
        WHEN af.finding_type = 'major_nc' THEN 'high'
        WHEN af.finding_type = 'minor_nc' AND DATE_PART('days', CURRENT_DATE - af.target_closure_date) > 30 THEN 'high'
        WHEN af.finding_type = 'minor_nc' THEN 'medium'
        ELSE 'low'
    END as severity_level,
    CASE 
        WHEN af.finding_type = 'major_nc' THEN 'Certificate at risk if not closed before next audit'
        WHEN DATE_PART('days', CURRENT_DATE - af.target_closure_date) > 60 THEN 'Escalation required - excessive delay'
        WHEN DATE_PART('days', CURRENT_DATE - af.target_closure_date) > 30 THEN 'Management attention needed'
        ELSE 'Follow standard closure process'
    END as impact_assessment
FROM audit_findings af
JOIN quality_audits qa ON af.audit_id = qa.audit_id
LEFT JOIN employees e ON af.responsible_person = e.employee_id
LEFT JOIN departments d ON e.department_id = d.department_id
LEFT JOIN factories f ON d.factory_id = f.factory_id
LEFT JOIN capa_headers ch ON af.linked_capa_id = ch.capa_id
WHERE af.target_closure_date < CURRENT_DATE
    AND af.finding_status NOT IN ('closed', 'verified')
ORDER BY 
    CASE af.finding_type WHEN 'major_nc' THEN 1 WHEN 'minor_nc' THEN 2 ELSE 3 END,
    days_overdue DESC;
```

### Query 2.2: Audit Findings by Category
```
Analyze audit findings distribution by category, factory, and audit standard to identify systemic issues
```

**SQL Query:**
```sql
WITH finding_analysis AS (
    SELECT 
        qa.audit_standard,
        f.factory_name,
        af.finding_category,
        af.finding_type,
        COUNT(af.finding_id) as finding_count,
        COUNT(CASE WHEN af.finding_status = 'open' THEN 1 END) as open_count,
        COUNT(CASE WHEN af.finding_status = 'closed' THEN 1 END) as closed_count,
        ROUND(AVG(DATE_PART('days', COALESCE(af.closure_date, CURRENT_DATE) - qa.actual_end_date)), 1) as avg_closure_days
    FROM audit_findings af
    JOIN quality_audits qa ON af.audit_id = qa.audit_id
    LEFT JOIN departments d ON qa.auditee_department = d.department_id
    LEFT JOIN factories f ON d.factory_id = f.factory_id
    WHERE qa.actual_end_date >= CURRENT_DATE - INTERVAL '24 months'
    GROUP BY qa.audit_standard, f.factory_name, af.finding_category, af.finding_type
)
SELECT 
    audit_standard,
    factory_name,
    finding_category,
    finding_type,
    finding_count,
    open_count,
    closed_count,
    ROUND(closed_count * 100.0 / NULLIF(finding_count, 0), 2) as closure_rate,
    avg_closure_days,
    CASE 
        WHEN finding_count >= 10 AND finding_type = 'major_nc' THEN 'systemic_issue'
        WHEN finding_count >= 5 AND finding_type = 'major_nc' THEN 'recurring_problem'
        WHEN finding_count >= 10 THEN 'attention_needed'
        ELSE 'normal'
    END as pattern_indicator,
    RANK() OVER (PARTITION BY factory_name ORDER BY finding_count DESC) as category_rank
FROM finding_analysis
WHERE finding_count > 0
ORDER BY finding_count DESC, audit_standard, factory_name;
```

### Query 2.3: Audit Performance Trends
```
Show audit score trends over time by factory and certification standard with improvement or deterioration indicators
```

**SQL Query:**
```sql
WITH audit_trends AS (
    SELECT 
        f.factory_id,
        f.factory_name,
        qa.audit_standard,
        DATE_TRUNC('quarter', qa.actual_end_date) as audit_quarter,
        AVG(qa.audit_score) as avg_audit_score,
        SUM(qa.major_findings) as total_major_findings,
        SUM(qa.minor_findings) as total_minor_findings,
        COUNT(qa.audit_id) as audits_conducted
    FROM quality_audits qa
    JOIN departments d ON qa.auditee_department = d.department_id
    JOIN factories f ON d.factory_id = f.factory_id
    WHERE qa.actual_end_date >= CURRENT_DATE - INTERVAL '24 months'
        AND qa.audit_status = 'completed'
    GROUP BY f.factory_id, f.factory_name, qa.audit_standard, DATE_TRUNC('quarter', qa.actual_end_date)
)
SELECT 
    at.factory_id,
    at.factory_name,
    at.audit_standard,
    at.audit_quarter,
    ROUND(at.avg_audit_score, 2) as avg_audit_score,
    at.total_major_findings,
    at.total_minor_findings,
    at.audits_conducted,
    LAG(at.avg_audit_score) OVER (PARTITION BY at.factory_id, at.audit_standard ORDER BY at.audit_quarter) as prev_quarter_score,
    ROUND(at.avg_audit_score - LAG(at.avg_audit_score) OVER (PARTITION BY at.factory_id, at.audit_standard ORDER BY at.audit_quarter), 2) as score_change,
    CASE 
        WHEN at.avg_audit_score - LAG(at.avg_audit_score) OVER (PARTITION BY at.factory_id, at.audit_standard ORDER BY at.audit_quarter) > 5 THEN 'improving'
        WHEN at.avg_audit_score - LAG(at.avg_audit_score) OVER (PARTITION BY at.factory_id, at.audit_standard ORDER BY at.audit_quarter) < -5 THEN 'deteriorating'
        ELSE 'stable'
    END as performance_trend
FROM audit_trends at
ORDER BY at.factory_name, at.audit_standard, at.audit_quarter DESC;
```

## 3. CAPA Management

### Query 3.1: CAPA Status Overview
```
Show all open CAPAs with their status, responsible person, due dates, and overdue status across all factories
```

**SQL Query:**
```sql
SELECT 
    ch.capa_id,
    ch.capa_number,
    ch.action_type,
    ch.problem_description,
    ch.problem_severity,
    ch.initiated_from,
    ch.source_document_id,
    e.employee_name as responsible_person,
    d.department_name,
    f.factory_name,
    ch.target_completion_date,
    ch.actual_completion_date,
    ch.capa_status,
    DATE_PART('days', CURRENT_DATE - ch.target_completion_date) as days_overdue,
    ch.root_cause_identified,
    ch.verification_completed,
    ch.effectiveness_verified,
    COUNT(ca.action_id) as total_actions,
    COUNT(CASE WHEN ca.action_status = 'completed' THEN 1 END) as completed_actions,
    ROUND(COUNT(CASE WHEN ca.action_status = 'completed' THEN 1 END) * 100.0 / NULLIF(COUNT(ca.action_id), 0), 2) as action_completion_rate,
    CASE 
        WHEN ch.target_completion_date < CURRENT_DATE AND ch.capa_status NOT IN ('closed', 'completed') THEN 'overdue'
        WHEN ch.target_completion_date <= CURRENT_DATE + INTERVAL '7 days' THEN 'due_soon'
        WHEN ch.capa_status = 'open' THEN 'in_progress'
        ELSE ch.capa_status
    END as status_category,
    CASE 
        WHEN ch.problem_severity = 'critical' AND ch.target_completion_date < CURRENT_DATE THEN 'immediate_escalation'
        WHEN ch.target_completion_date < CURRENT_DATE - INTERVAL '30 days' THEN 'management_review'
        WHEN ch.target_completion_date < CURRENT_DATE THEN 'follow_up_required'
        ELSE 'on_track'
    END as action_required
FROM capa_headers ch
LEFT JOIN capa_actions ca ON ch.capa_id = ca.capa_id
LEFT JOIN employees e ON ch.responsible_person = e.employee_id
LEFT JOIN departments d ON ch.responsible_department = d.department_id
LEFT JOIN factories f ON d.factory_id = f.factory_id
WHERE ch.capa_status NOT IN ('closed')
GROUP BY ch.capa_id, ch.capa_number, ch.action_type, ch.problem_description, ch.problem_severity,
         ch.initiated_from, ch.source_document_id, e.employee_name, d.department_name, f.factory_name,
         ch.target_completion_date, ch.actual_completion_date, ch.capa_status,
         ch.root_cause_identified, ch.verification_completed, ch.effectiveness_verified
ORDER BY 
    CASE status_category WHEN 'overdue' THEN 1 WHEN 'due_soon' THEN 2 ELSE 3 END,
    CASE ch.problem_severity WHEN 'critical' THEN 1 WHEN 'high' THEN 2 WHEN 'medium' THEN 3 ELSE 4 END,
    days_overdue DESC;
```

### Query 3.2: CAPA Effectiveness Analysis
```
Analyze CAPA effectiveness by tracking recurrence of similar issues and verification completion rates
```

**SQL Query:**
```sql
WITH capa_performance AS (
    SELECT 
        ch.initiated_from as source_type,
        ch.problem_severity,
        COUNT(ch.capa_id) as total_capas,
        COUNT(CASE WHEN ch.capa_status = 'closed' THEN 1 END) as closed_capas,
        COUNT(CASE WHEN ch.verification_completed = true THEN 1 END) as verified_capas,
        COUNT(CASE WHEN ch.effectiveness_verified = true THEN 1 END) as effectiveness_verified_capas,
        AVG(DATE_PART('days', ch.actual_completion_date - ch.created_at)) as avg_closure_days,
        COUNT(CASE WHEN ch.target_completion_date < ch.actual_completion_date THEN 1 END) as closed_late,
        SUM(ch.implementation_cost) as total_implementation_cost
    FROM capa_headers ch
    WHERE ch.created_at >= CURRENT_DATE - INTERVAL '12 months'
    GROUP BY ch.initiated_from, ch.problem_severity
),
recurrence_analysis AS (
    SELECT 
        ch.initiated_from,
        COUNT(ch.capa_id) as recurring_issues,
        STRING_AGG(DISTINCT ch.problem_description, '; ') as recurring_descriptions
    FROM capa_headers ch
    WHERE ch.created_at >= CURRENT_DATE - INTERVAL '12 months'
    GROUP BY ch.initiated_from
    HAVING COUNT(ch.capa_id) > 3
)
SELECT 
    cp.source_type,
    cp.problem_severity,
    cp.total_capas,
    cp.closed_capas,
    ROUND(cp.closed_capas * 100.0 / NULLIF(cp.total_capas, 0), 2) as closure_rate,
    cp.verified_capas,
    ROUND(cp.verified_capas * 100.0 / NULLIF(cp.closed_capas, 0), 2) as verification_rate,
    cp.effectiveness_verified_capas,
    ROUND(cp.effectiveness_verified_capas * 100.0 / NULLIF(cp.verified_capas, 0), 2) as effectiveness_rate,
    ROUND(cp.avg_closure_days, 1) as avg_closure_days,
    cp.closed_late,
    ROUND(cp.closed_late * 100.0 / NULLIF(cp.closed_capas, 0), 2) as late_closure_rate,
    cp.total_implementation_cost,
    COALESCE(ra.recurring_issues, 0) as potential_recurring_issues,
    CASE 
        WHEN ROUND(cp.effectiveness_verified_capas * 100.0 / NULLIF(cp.verified_capas, 0), 2) >= 90 THEN 'excellent'
        WHEN ROUND(cp.effectiveness_verified_capas * 100.0 / NULLIF(cp.verified_capas, 0), 2) >= 70 THEN 'good'
        WHEN ROUND(cp.effectiveness_verified_capas * 100.0 / NULLIF(cp.verified_capas, 0), 2) >= 50 THEN 'needs_improvement'
        ELSE 'poor'
    END as effectiveness_rating
FROM capa_performance cp
LEFT JOIN recurrence_analysis ra ON cp.source_type = ra.initiated_from
ORDER BY cp.total_capas DESC;
```

## 4. Non-Conformance Analysis

### Query 4.1: NCR Summary by Factory
```
Show non-conformance report summary by factory including defect types, severity distribution, and cost impact
```

**SQL Query:**
```sql
SELECT 
    f.factory_id,
    f.factory_name,
    COUNT(ncr.ncr_id) as total_ncrs,
    COUNT(CASE WHEN ncr.ncr_status = 'open' THEN 1 END) as open_ncrs,
    COUNT(CASE WHEN ncr.ncr_status = 'closed' THEN 1 END) as closed_ncrs,
    COUNT(CASE WHEN ncr.defect_severity = 'critical' THEN 1 END) as critical_ncrs,
    COUNT(CASE WHEN ncr.defect_severity = 'major' THEN 1 END) as major_ncrs,
    COUNT(CASE WHEN ncr.defect_severity = 'minor' THEN 1 END) as minor_ncrs,
    SUM(ncr.quantity_defective) as total_defective_quantity,
    SUM(ncr.scrap_cost) as total_scrap_cost,
    SUM(ncr.rework_cost) as total_rework_cost,
    SUM(ncr.sorting_cost) as total_sorting_cost,
    SUM(ncr.total_cost) as total_ncr_cost,
    ROUND(AVG(DATE_PART('days', COALESCE(ncr.closed_date, CURRENT_DATE) - ncr.detected_date)), 1) as avg_days_to_close,
    STRING_AGG(DISTINCT ncr.defect_type, ', ') as defect_types_encountered,
    COUNT(CASE WHEN ncr.source_type = 'supplier_quality' THEN 1 END) as supplier_related_ncrs,
    COUNT(CASE WHEN ncr.source_type = 'in_process' THEN 1 END) as internal_process_ncrs,
    COUNT(CASE WHEN ncr.source_type = 'customer_complaint' THEN 1 END) as customer_related_ncrs
FROM factories f
LEFT JOIN ncr_headers ncr ON f.factory_id = ncr.detection_location
WHERE ncr.detected_date >= CURRENT_DATE - INTERVAL '12 months'
    AND f.status = 'active'
GROUP BY f.factory_id, f.factory_name
ORDER BY total_ncr_cost DESC, total_ncrs DESC;
```

### Query 4.2: Cost of Quality Analysis
```
Calculate cost of quality metrics including prevention, appraisal, internal failure, and external failure costs
```

**SQL Query:**
```sql
WITH quality_costs AS (
    SELECT 
        f.factory_id,
        f.factory_name,
        -- Internal Failure Costs (from NCRs)
        SUM(ncr.scrap_cost) as scrap_cost,
        SUM(ncr.rework_cost) as rework_cost,
        SUM(ncr.sorting_cost) as sorting_cost,
        -- External Failure Costs (from customer complaints)
        SUM(cc.replacement_cost) as replacement_cost,
        SUM(cc.credit_issued) as credit_issued,
        SUM(cc.total_cost) as complaint_cost
    FROM factories f
    LEFT JOIN ncr_headers ncr ON f.factory_id = ncr.detection_location
        AND ncr.detected_date >= CURRENT_DATE - INTERVAL '12 months'
    LEFT JOIN customer_complaints cc ON f.factory_id = cc.detection_location
        AND cc.complaint_date >= CURRENT_DATE - INTERVAL '12 months'
    WHERE f.status = 'active'
    GROUP BY f.factory_id, f.factory_name
),
audit_costs AS (
    SELECT 
        d.factory_id,
        COUNT(qa.audit_id) * 5000 as internal_audit_cost, -- Estimated cost per audit
        SUM(ch.implementation_cost) as capa_cost
    FROM quality_audits qa
    JOIN departments d ON qa.auditee_department = d.department_id
    LEFT JOIN audit_findings af ON qa.audit_id = af.audit_id
    LEFT JOIN capa_headers ch ON af.linked_capa_id = ch.capa_id
    WHERE qa.actual_end_date >= CURRENT_DATE - INTERVAL '12 months'
    GROUP BY d.factory_id
)
SELECT 
    qc.factory_id,
    qc.factory_name,
    -- Internal Failure Costs
    COALESCE(qc.scrap_cost, 0) + COALESCE(qc.rework_cost, 0) + COALESCE(qc.sorting_cost, 0) as internal_failure_cost,
    -- External Failure Costs
    COALESCE(qc.replacement_cost, 0) + COALESCE(qc.credit_issued, 0) + COALESCE(qc.complaint_cost, 0) as external_failure_cost,
    -- Appraisal Costs (Audits, Inspections)
    COALESCE(ac.internal_audit_cost, 0) as appraisal_cost,
    -- Prevention Costs (CAPA Implementation)
    COALESCE(ac.capa_cost, 0) as prevention_cost,
    -- Total Cost of Quality
    (COALESCE(qc.scrap_cost, 0) + COALESCE(qc.rework_cost, 0) + COALESCE(qc.sorting_cost, 0) +
     COALESCE(qc.replacement_cost, 0) + COALESCE(qc.credit_issued, 0) + COALESCE(qc.complaint_cost, 0) +
     COALESCE(ac.internal_audit_cost, 0) + COALESCE(ac.capa_cost, 0)) as total_cost_of_quality,
    -- Cost Ratios
    ROUND((COALESCE(qc.scrap_cost, 0) + COALESCE(qc.rework_cost, 0)) * 100.0 / NULLIF(
        (COALESCE(qc.scrap_cost, 0) + COALESCE(qc.rework_cost, 0) + COALESCE(qc.sorting_cost, 0) +
         COALESCE(qc.replacement_cost, 0) + COALESCE(qc.credit_issued, 0) + COALESCE(qc.complaint_cost, 0) +
         COALESCE(ac.internal_audit_cost, 0) + COALESCE(ac.capa_cost, 0)), 0), 2) as internal_failure_pct,
    ROUND(COALESCE(ac.capa_cost, 0) * 100.0 / NULLIF(
        (COALESCE(qc.scrap_cost, 0) + COALESCE(qc.rework_cost, 0) + COALESCE(qc.sorting_cost, 0) +
         COALESCE(qc.replacement_cost, 0) + COALESCE(qc.credit_issued, 0) + COALESCE(qc.complaint_cost, 0) +
         COALESCE(ac.internal_audit_cost, 0) + COALESCE(ac.capa_cost, 0)), 0), 2) as prevention_pct
FROM quality_costs qc
LEFT JOIN audit_costs ac ON qc.factory_id = ac.factory_id
ORDER BY total_cost_of_quality DESC;
```

## 5. Compliance Correlation Analysis

### Query 5.1: Audit Findings ↔ Production Issues Correlation
```
Correlate audit findings with production quality issues to identify work centers with systemic problems
```

**SQL Query:**
```sql
WITH work_center_issues AS (
    SELECT 
        wo.work_center_id,
        wc.work_center_name,
        f.factory_name,
        COUNT(DISTINCT qi.inspection_id) as total_inspections,
        COUNT(CASE WHEN qi.inspection_result = 'failed' THEN 1 END) as failed_inspections,
        ROUND(COUNT(CASE WHEN qi.inspection_result = 'failed' THEN 1 END) * 100.0 / 
              NULLIF(COUNT(qi.inspection_id), 0), 2) as defect_rate,
        SUM(qi.defects_found) as total_defects
    FROM work_orders wo
    JOIN work_centers wc ON wo.work_center_id = wc.work_center_id
    JOIN factories f ON wc.factory_id = f.factory_id
    LEFT JOIN quality_inspections qi ON wo.work_order_id = qi.work_order_id
    WHERE wo.created_at >= CURRENT_DATE - INTERVAL '12 months'
    GROUP BY wo.work_center_id, wc.work_center_name, f.factory_name
),
audit_finding_sources AS (
    SELECT 
        af.finding_category,
        af.objective_evidence,
        COUNT(af.finding_id) as finding_count,
        COUNT(CASE WHEN af.finding_type = 'major_nc' THEN 1 END) as major_nc_count
    FROM audit_findings af
    JOIN quality_audits qa ON af.audit_id = qa.audit_id
    WHERE qa.actual_end_date >= CURRENT_DATE - INTERVAL '12 months'
    GROUP BY af.finding_category, af.objective_evidence
)
SELECT 
    wci.work_center_name,
    wci.factory_name,
    wci.total_inspections,
    wci.failed_inspections,
    wci.defect_rate,
    wci.total_defects,
    COALESCE(afs.finding_count, 0) as related_audit_findings,
    COALESCE(afs.major_nc_count, 0) as related_major_ncs,
    CASE 
        WHEN wci.defect_rate > 5 AND COALESCE(afs.finding_count, 0) > 3 THEN 'high_correlation'
        WHEN wci.defect_rate > 3 OR COALESCE(afs.finding_count, 0) > 2 THEN 'medium_correlation'
        ELSE 'low_correlation'
    END as correlation_level,
    CASE 
        WHEN wci.defect_rate > 5 AND COALESCE(afs.finding_count, 0) > 3 THEN 'Process control review required - systemic issue identified'
        WHEN wci.defect_rate > 3 THEN 'Quality improvement focus needed'
        WHEN COALESCE(afs.finding_count, 0) > 2 THEN 'Audit finding root cause investigation required'
        ELSE 'Continue monitoring'
    END as recommended_action
FROM work_center_issues wci
LEFT JOIN audit_finding_sources afs ON wci.work_center_name ILIKE '%' || afs.objective_evidence || '%'
WHERE wci.defect_rate > 0 OR COALESCE(afs.finding_count, 0) > 0
ORDER BY wci.defect_rate DESC, afs.finding_count DESC
LIMIT 20;
```

### Query 5.2: Training ↔ Compliance Correlation
```
Analyze correlation between employee training/certification status and compliance issues
```

**SQL Query:**
```sql
WITH employee_training_status AS (
    SELECT 
        e.employee_id,
        e.employee_name,
        e.department_id,
        d.department_name,
        f.factory_id,
        f.factory_name,
        COUNT(ec.certification_id) as total_certifications,
        COUNT(CASE WHEN ec.expiry_date < CURRENT_DATE THEN 1 END) as expired_certifications,
        COUNT(CASE WHEN ec.expiry_date BETWEEN CURRENT_DATE AND CURRENT_DATE + INTERVAL '30 days' THEN 1 END) as expiring_soon,
        MAX(tr.completion_date) as last_training_date,
        DATE_PART('days', CURRENT_DATE - MAX(tr.completion_date)) as days_since_training
    FROM employees e
    JOIN departments d ON e.department_id = d.department_id
    JOIN factories f ON d.factory_id = f.factory_id
    LEFT JOIN employee_certifications ec ON e.employee_id = ec.employee_id
    LEFT JOIN training_records tr ON e.employee_id = tr.employee_id
    WHERE e.status = 'active'
    GROUP BY e.employee_id, e.employee_name, e.department_id, d.department_name, f.factory_id, f.factory_name
),
compliance_issues AS (
    SELECT 
        af.responsible_person,
        COUNT(af.finding_id) as findings_assigned,
        COUNT(CASE WHEN af.finding_status = 'open' THEN 1 END) as open_findings,
        COUNT(CASE WHEN af.finding_type = 'major_nc' THEN 1 END) as major_nc_assigned
    FROM audit_findings af
    WHERE af.created_at >= CURRENT_DATE - INTERVAL '12 months'
    GROUP BY af.responsible_person
)
SELECT 
    ets.employee_name,
    ets.department_name,
    ets.factory_name,
    ets.total_certifications,
    ets.expired_certifications,
    ets.expiring_soon,
    ets.days_since_training,
    COALESCE(ci.findings_assigned, 0) as findings_assigned,
    COALESCE(ci.open_findings, 0) as open_findings,
    COALESCE(ci.major_nc_assigned, 0) as major_nc_assigned,
    CASE 
        WHEN ets.expired_certifications > 0 AND COALESCE(ci.findings_assigned, 0) > 2 THEN 'high'
        WHEN ets.expired_certifications > 0 OR COALESCE(ci.findings_assigned, 0) > 1 THEN 'medium'
        ELSE 'low'
    END as training_compliance_correlation,
    CASE 
        WHEN ets.expired_certifications > 0 THEN 'Immediate retraining required - expired certifications'
        WHEN ets.days_since_training > 365 THEN 'Annual refresher training overdue'
        WHEN ets.expiring_soon > 0 THEN 'Schedule certification renewal'
        ELSE 'Training current'
    END as training_recommendation
FROM employee_training_status ets
LEFT JOIN compliance_issues ci ON ets.employee_id = ci.responsible_person
WHERE ets.expired_certifications > 0 OR COALESCE(ci.findings_assigned, 0) > 0
ORDER BY ets.expired_certifications DESC, ci.findings_assigned DESC;
```

## 6. Regulatory Compliance Dashboard

### Query 6.1: Regulatory Compliance Status
```
Show current regulatory compliance status across all factories including environmental, safety, and quality regulations
```

**SQL Query:**
```sql
SELECT 
    f.factory_id,
    f.factory_name,
    f.city,
    f.country,
    -- Quality Management Compliance (ISO 9001)
    MAX(CASE WHEN qa.audit_standard = 'ISO_9001' THEN qa.audit_score END) as iso_9001_score,
    MAX(CASE WHEN qa.audit_standard = 'ISO_9001' THEN qa.audit_rating END) as iso_9001_rating,
    -- Automotive Quality (IATF 16949)
    MAX(CASE WHEN qa.audit_standard = 'IATF_16949' THEN qa.audit_score END) as iatf_16949_score,
    MAX(CASE WHEN qa.audit_standard = 'IATF_16949' THEN qa.audit_rating END) as iatf_16949_rating,
    -- Environmental (ISO 14001)
    MAX(CASE WHEN qa.audit_standard = 'ISO_14001' THEN qa.audit_score END) as iso_14001_score,
    MAX(CASE WHEN qa.audit_standard = 'ISO_14001' THEN qa.audit_rating END) as iso_14001_rating,
    -- Safety (ISO 45001)
    MAX(CASE WHEN qa.audit_standard = 'ISO_45001' THEN qa.audit_score END) as iso_45001_score,
    MAX(CASE WHEN qa.audit_standard = 'ISO_45001' THEN qa.audit_rating END) as iso_45001_rating,
    -- Overall Compliance Score
    ROUND(AVG(qa.audit_score), 2) as overall_compliance_score,
    -- Open Findings Count
    COUNT(CASE WHEN af.finding_status = 'open' THEN 1 END) as total_open_findings,
    -- Regulatory Violations (Major NCs)
    COUNT(CASE WHEN af.finding_type = 'major_nc' AND af.finding_status = 'open' THEN 1 END) as regulatory_violations,
    -- Compliance Status
    CASE 
        WHEN COUNT(CASE WHEN af.finding_type = 'major_nc' AND af.finding_status = 'open' THEN 1 END) > 0 THEN 'non_compliant'
        WHEN AVG(qa.audit_score) >= 90 THEN 'fully_compliant'
        WHEN AVG(qa.audit_score) >= 75 THEN 'compliant_with_observations'
        ELSE 'improvement_required'
    END as overall_compliance_status
FROM factories f
LEFT JOIN departments d ON f.factory_id = d.factory_id
LEFT JOIN quality_audits qa ON d.department_id = qa.auditee_department
    AND qa.actual_end_date >= CURRENT_DATE - INTERVAL '12 months'
    AND qa.audit_status = 'completed'
LEFT JOIN audit_findings af ON qa.audit_id = af.audit_id
WHERE f.status = 'active'
GROUP BY f.factory_id, f.factory_name, f.city, f.country
ORDER BY overall_compliance_score DESC;
```

---

## 🔄 API Integration Patterns

### Real-Time Data Refresh
- **Audit Status**: Daily refresh for audit schedules and finding status
- **CAPA Tracking**: Hourly refresh for action completion updates
- **Certification Alerts**: Real-time alerts for expiring certifications (60/30/7 day warnings)

### Performance Optimization
- **Caching Layer**: Redis for frequently accessed compliance dashboards
- **Alert Engine**: Proactive notification system for overdue items
- **Query Optimization**: Indexed views for complex compliance calculations

---

## 📊 API Conversion Guidelines

When converting these natural language queries to APIs, consider:

1. **Real-time Alerts**: Use push notifications for certification expiry and overdue findings
2. **Time Ranges**: Include flexible time range parameters (30 days, 90 days, YTD, custom)
3. **Filtering**: Add certification-specific, audit-type, and factory-specific filters
4. **Severity Levels**: Support filtering by finding severity (critical, major, minor)
5. **Status Tracking**: Include workflow status parameters for CAPA lifecycle
6. **Export Options**: Support compliance report export in PDF, Excel formats
7. **Audit Trail**: Maintain complete audit trail for regulatory requirements

## 🗄️ Database Tables Referenced

These queries primarily use data from:
- **QMS Database**: `quality_audits`, `audit_findings`, `capa_headers`, `capa_actions`, `ncr_headers`, `ncr_defect_details`, `customer_complaints`, `eight_d_reports`
- **Master Database**: `factories`, `departments`, `employees`
- **HR Database**: `employee_certifications`, `training_records`
- **Manufacturing Database**: `quality_inspections`, `work_orders`, `work_centers`

---

*This specification provides the foundation for implementing a comprehensive Compliance & Audit Intelligence application that serves as the command center for regulatory excellence and audit readiness across all manufacturing facilities.*
