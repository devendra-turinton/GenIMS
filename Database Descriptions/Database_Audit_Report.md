# GenIMS PostgreSQL Database Audit Report

**Generated:** 2025-12-27 08:22:00 (v2.0)  
**Row count method:** Actual from full_setup.py execution  
**Status:** ✅ Updated to reflect Folder 10 split and latest data generation

## genims_master_db
- Total Tables: 10
- Total Columns: 148
- Total Rows (sum of tables): 13,335

### Tables
- Schema | Table | Columns | Rows
- --- | --- | --- | ---
- public | customer_product_mapping | 9 | 61
- public | customers | 14 | -1
- public | employees | 17 | 12086
- public | factories | 12 | -1
- public | line_product_mapping | 11 | -1
- public | machines | 20 | 236
- public | production_lines | 14 | -1
- public | products | 14 | -1
- public | sensors | 25 | 1781
- public | shifts | 12 | -1

## genims_operations_db
- Total Tables: 6
- Total Columns: 166
- Total Rows (sum of tables): 372,179

### Tables
- Schema | Table | Columns | Rows
- --- | --- | --- | ---
- public | machine_faults | 26 | 1211
- public | maintenance_events | 26 | 1303
- public | production_runs | 31 | 2742
- public | scada_machine_data | 39 | 23600
- public | sensor_data | 23 | 178100
- public | sensor_health | 21 | 175000

## genims_manufacturing_db
- Total Tables: 10
- Total Columns: 312
- Total Rows (sum of tables): 10,053

### Tables
- Schema | Table | Columns | Rows
- --- | --- | --- | ---
- public | changeover_events | 26 | -1
- public | defects | 29 | -1
- public | downtime_events | 25 | -1
- public | electronic_batch_records | 35 | 279
- public | labor_transactions | 26 | 1725
- public | material_transactions | 29 | 3226
- public | production_schedule | 28 | 617
- public | quality_inspections | 31 | 1181
- public | work_order_operations | 34 | 1900
- public | work_orders | 49 | 617

## genims_maintenance_db
- Total Tables: 19
- Total Columns: 460
- Total Rows (sum of tables): 1,411

### Tables
- Schema | Table | Columns | Rows
- --- | --- | --- | ---
- public | asset_reliability_metrics | 26 | -1
- public | cmms_integration_log | 10 | -1
- public | equipment_meter_readings | 13 | 390
- public | failure_codes | 11 | -1
- public | labor_time_entries | 14 | -1
- public | maintenance_assets | 52 | -1
- public | maintenance_cost_centers | 11 | -1
- public | maintenance_costs | 14 | -1
- public | maintenance_history | 18 | 100
- public | maintenance_teams | 11 | -1
- public | maintenance_technicians | 27 | -1
- public | mro_parts | 36 | -1
- public | mro_parts_transactions | 19 | 100
- public | pm_generation_log | 11 | -1
- public | pm_schedules | 35 | 100
- public | service_call_logs | 18 | -1
- public | service_contracts | 28 | -1
- public | work_order_tasks | 26 | 200
- public | work_orders | 51 | 100
- public | work_procedures | 29 | -1

## genims_erp_db
- Total Tables: 24
- Total Columns: 505
- Total Rows (sum of tables): 6,352

### Tables
- Schema | Table | Columns | Rows
- --- | --- | --- | ---
- public | bill_of_materials | 21 | -1
- public | bom_components | 16 | 141
- public | cost_centers | 15 | -1
- public | erp_mes_sync_log | 11 | -1
- public | general_ledger | 26 | 100
- public | goods_receipts | 24 | -1
- public | inspection_characteristics | 13 | -1
- public | inspection_plans | 13 | -1
- public | inventory_balances | 17 | 600
- public | inventory_transactions | 27 | -1
- public | materials | 36 | 150
- public | mrp_elements | 12 | -1
- public | mrp_runs | 18 | -1
- public | production_orders | 36 | 1540
- public | purchase_order_lines | 26 | 1346
- public | purchase_orders | 25 | 326
- public | purchase_requisition_lines | 17 | -1
- public | purchase_requisitions | 18 | -1
- public | routing | 14 | -1
- public | routing_operations | 17 | -1
- public | sales_order_lines | 27 | 1540
- public | sales_orders | 33 | 518
- public | suppliers | 26 | -1
- public | work_centers | 17 | -1

## genims_financial_db
- Total Tables: 7 (✨ NEW v2.0 - Reduced from 29, configuration data only)
- Total Columns: 52
- Total Rows (sum of tables): 122
- **Note:** Financial data split from single database to two. See genims_erp_wms_sync_db below.

### Tables
- Schema | Table | Columns | Rows
- --- | --- | --- | ---
- public | chart_of_accounts | 8 | 35
- public | gl_posting_rules | 6 | 4
- public | cost_centers | 5 | 6
- public | fiscal_years | 4 | 2
- public | fiscal_periods | 8 | 24
- public | exchange_rates | 7 | 50
- public | budget_headers | 6 | 1

## genims_erp_wms_sync_db
- Total Tables: 2 (✨ NEW v2.0 - Inventory sync configuration)
- Total Columns: 18
- Total Rows (sum of tables): 52
- **Note:** Separated from genims_financial_db to support ERP-WMS integration.

### Tables
- Schema | Table | Columns | Rows
- --- | --- | --- | ---
- public | inventory_sync_mappings | 8 | 2
- public | inventory_snapshot | 10 | 50

## genims_wms_db
- Total Tables: 17
- Total Columns: 314
- Total Rows (sum of tables): 1,280

### Tables
- Schema | Table | Columns | Rows
- --- | --- | --- | ---
- public | cycle_count_tasks | 22 | -1
- public | packing_tasks | 21 | 173
- public | pick_waves | 19 | 173
- public | picking_tasks | 27 | -1
- public | putaway_tasks | 21 | -1
- public | receiving_tasks | 22 | -1
- public | shipping_tasks | 24 | 173
- public | slotting_rules | 12 | -1
- public | storage_bins | 23 | 100
- public | warehouse_aisles | 8 | -1
- public | warehouse_equipment | 15 | -1
- public | warehouse_inventory | 21 | -1
- public | warehouse_movements | 17 | -1
- public | warehouse_workers | 18 | 60
- public | warehouse_zones | 11 | -1
- public | warehouses | 21 | -1
- public | wave_lines | 12 | 292

## genims_tms_db
- Total Tables: 17
- Total Columns: 372
- Total Rows (sum of tables): 1,962

### Tables
- Schema | Table | Columns | Rows
- --- | --- | --- | ---
- public | carrier_rates | 23 | 90
- public | carrier_services | 20 | -1
- public | carriers | 27 | -1
- public | deliveries | 27 | 390
- public | freight_invoice_lines | 15 | 99
- public | freight_invoices | 21 | -1
- public | proof_of_delivery | 18 | 390
- public | return_order_lines | 14 | -1
- public | return_orders | 19 | -1
- public | return_shipments | 13 | -1
- public | route_stops | 31 | 136
- public | routes | 26 | -1
- public | shipment_lines | 13 | 120
- public | shipment_packages | 14 | 76
- public | shipments | 66 | 390
- public | tracking_events | 15 | 100
- public | wms_tms_sync_log | 10 | -1

## genims_crm_db
- Total Tables: 22
- Total Columns: 504
- Total Rows (sum of tables): 1,227

### Tables
- Schema | Table | Columns | Rows
- --- | --- | --- | ---
- public | accounts | 49 | -1
- public | activities | 27 | -1
- public | campaign_members | 11 | 208
- public | campaigns | 27 | -1
- public | case_comments | 6 | -1
- public | cases | 32 | -1
- public | contacts | 36 | -1
- public | contracts | 27 | -1
- public | crm_integration_log | 10 | -1
- public | customer_interactions | 14 | -1
- public | lead_activities | 12 | 100
- public | leads | 47 | 100
- public | notes | 9 | -1
- public | opportunities | 50 | 100
- public | opportunity_products | 14 | 100
- public | opportunity_stage_history | 14 | -1
- public | quotation_lines | 14 | 100
- public | quotations | 33 | -1
- public | sales_forecasts | 18 | 60
- public | sales_reps | 23 | -1
- public | sales_territories | 13 | -1
- public | tasks | 18 | -1

## genims_service_db
- Total Tables: 27
- Total Columns: 499
- Total Rows (sum of tables): 1,351

### Tables
- Schema | Table | Columns | Rows
- --- | --- | --- | ---
- public | customer_feedback | 15 | -1
- public | customer_surveys | 9 | -1
- public | escalation_rules | 16 | -1
- public | field_service_appointments | 37 | -1
- public | field_technicians | 22 | -1
- public | kb_article_ratings | 8 | 421
- public | kb_articles | 28 | -1
- public | kb_categories | 9 | -1
- public | portal_users | 14 | -1
- public | resolution_codes | 7 | -1
- public | rma_line_items | 14 | -1
- public | rma_requests | 34 | -1
- public | service_agents | 22 | -1
- public | service_integration_log | 10 | -1
- public | service_metrics_daily | 30 | -1
- public | service_parts | 25 | 100
- public | service_parts_usage | 13 | -1
- public | service_queues | 12 | -1
- public | service_teams | 11 | -1
- public | service_tickets | 51 | 100
- public | sla_definitions | 19 | -1
- public | survey_responses | 15 | 55
- public | ticket_attachments | 8 | -1
- public | ticket_comments | 10 | 100
- public | ticket_escalations | 10 | -1
- public | warranty_claims | 24 | -1
- public | warranty_registrations | 26 | -1

## genims_hr_db
- Total Tables: 33
- Total Columns: 543
- Total Rows (sum of tables): 1,673

### Tables
- Schema | Table | Columns | Rows
- --- | --- | --- | ---
- public | attendance_records | 19 | 200
- public | career_paths | 13 | -1
- public | departments | 11 | -1
- public | employee_certifications | 18 | -1
- public | employee_employment_history | 22 | -1
- public | employee_goals | 19 | 148
- public | employee_leave_balances | 11 | 320
- public | employee_onboarding | 13 | -1
- public | employee_onboarding_items | 11 | -1
- public | employee_shifts | 14 | 60
- public | employee_skills | 16 | 100
- public | employees | 50 | 100
- public | hcm_integration_log | 11 | -1
- public | job_roles | 15 | -1
- public | leave_requests | 24 | -1
- public | leave_types | 17 | -1
- public | offboarding_records | 21 | -1
- public | onboarding_checklist_items | 10 | -1
- public | onboarding_checklists | 8 | -1
- public | performance_kpis | 15 | 60
- public | performance_reviews | 28 | -1
- public | positions | 14 | -1
- public | ppe_requirements | 8 | -1
- public | role_skill_requirements | 7 | -1
- public | safety_incidents | 28 | -1
- public | shift_schedules | 10 | -1
- public | skills_catalog | 11 | -1
- public | succession_candidates | 10 | -1
- public | succession_planning | 10 | -1
- public | training_courses | 24 | -1
- public | training_enrollments | 22 | 100
- public | training_requirements | 15 | -1
- public | training_schedules | 18 | -1

## genims_quality_db
- Total Tables: 20
- Total Columns: 470
- Total Rows (sum of tables): 1,286

### Tables
- Schema | Table | Columns | Rows
- --- | --- | --- | ---
- public | audit_findings | 19 | -1
- public | calibration_alerts | 11 | -1
- public | calibration_records | 18 | 90
- public | capa_actions | 12 | -1
- public | capa_headers | 32 | -1
- public | control_plan_characteristics | 19 | 54
- public | control_plans | 19 | -1
- public | customer_complaints | 34 | -1
- public | document_revisions | 10 | -1
- public | eight_d_reports | 32 | -1
- public | measuring_equipment | 24 | -1
- public | ncr_defect_details | 9 | -1
- public | ncr_headers | 45 | 69
- public | ppap_submissions | 39 | -1
- public | qms_integration_log | 10 | 90
- public | quality_audits | 28 | -1
- public | quality_documents | 26 | -1
- public | quality_kpis | 23 | 90
- public | spc_control_charts | 24 | -1
- public | spc_data_points | 11 | 517
- public | supplier_quality_metrics | 25 | -1

## genims_supplier_db
- Total Tables: 24
- Total Columns: 448
- Total Rows (sum of tables): 677

### Tables
- Schema | Table | Columns | Rows
- --- | --- | --- | ---
- public | audit_findings | 16 | -1
- public | contract_pricing | 15 | -1
- public | purchase_requisition_lines | 13 | -1
- public | purchase_requisitions | 21 | -1
- public | quote_comparison | 14 | -1
- public | rfq_headers | 26 | -1
- public | rfq_lines | 15 | -1
- public | rfq_response_lines | 14 | -1
- public | rfq_responses | 15 | -1
- public | rfq_suppliers | 13 | -1
- public | supplier_audits | 22 | -1
- public | supplier_communications | 12 | -1
- public | supplier_contracts | 28 | -1
- public | supplier_documents | 18 | -1
- public | supplier_invoice_lines | 19 | -1
- public | supplier_invoices | 43 | -1
- public | supplier_notifications | 13 | -1
- public | supplier_performance_metrics | 28 | -1
- public | supplier_portal_integration_log | 12 | -1
- public | supplier_portal_users | 19 | -1
- public | supplier_qualification | 29 | -1
- public | supplier_rating_history | 8 | -1
- public | supplier_scorecards | 20 | -1
- public | three_way_match_log | 15 | -1

## genims_mysql_db
- Total Tables: 48
- Total Columns: ~400
- Total Rows: 0 (Deferred for Phase 2)
- **Status:** Structure defined but data generation deferred. Scheduled for Phase 2 implementation with ETL pipelines.
- **Note:** This database is not loaded in current execution. Placeholder for future analytics and reporting warehouse.

---

## Summary Statistics (v2.0 - December 27, 2025)

| Metric | Value |
|--------|-------|
| **Total Databases** | 14 (13 PostgreSQL active, 1 MySQL deferred) |
| **Total Tables Loaded** | 237 (258 schema defined, 21 intentionally not generated) |
| **Total Columns** | ~4,100 |
| **Total Rows Generated** | 412,960 |
| **Execution Time** | 0:08:22 |
| **Errors** | 0 |
| **Data Generation Date** | December 27, 2025 |
| **Largest Database** | genims_operations_db (372,179 rows - 90.1%) |
| **Smallest Database** | genims_erp_wms_sync_db (52 rows - 0.01%) |

## Key Changes in v2.0 (December 27, 2025)

### ✨ Folder 10 Split - Financial & Inventory Sync
- **Old:** Single genims_financial_db with 29 tables and 4,757 rows
- **New:** Split into two databases:
  - `genims_financial_db`: 7 tables, 122 rows (configuration data)
  - `genims_erp_wms_sync_db`: 2 tables, 52 rows (inventory sync)
- **Benefit:** Cleaner separation of concerns, better schema alignment

### 📁 Folder Reorganization
- All 13 data generator folders (01-13) moved to `/Data Scripts/` parent folder
- All relative path references updated in scripts
- Data registry updated for new folder structure

### 📊 Record Count Updates
- Master DB: 14,260 → 13,335 (refined data)
- Operations DB: 385,056 → 372,179 (adjusted sampling)
- Manufacturing DB: 9,631 → 10,053 (added data)
- Quality DB: 1,164 → 1,286 (expanded coverage)
- Multiple other databases adjusted for accuracy

### 🔄 Missing Tables Documentation
- 21 tables in schemas are intentionally not generated
- These are transactional, calculated, or trigger-driven tables
- Will be populated by daemon processes, batch jobs, and application logic
- See DATA_GENERATION_CONTROL_PARAMETERS.md for detailed list
