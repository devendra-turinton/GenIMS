#!/usr/bin/env python3
"""
GenIMS Quality Management System (QMS) Data Generator
Generates NCRs, CAPAs, audits, control plans, SPC data, calibration records,
customer complaints, 8D reports, and PPAP submissions
"""

import random
import json
from datetime import datetime, timedelta
from typing import List, Dict

class QMSDataGenerator:
    def __init__(self):
        """Initialize data generator"""
        print("Initializing QMS Data Generator...")
        
        # Data structures
        self.ncr_headers = []
        self.ncr_defect_details = []
        self.capa_headers = []
        self.capa_actions = []
        
        self.quality_audits = []
        self.audit_findings = []
        
        self.control_plans = []
        self.control_characteristics = []
        
        self.spc_charts = []
        self.spc_data_points = []
        
        self.measuring_equipment = []
        self.calibration_records = []
        self.calibration_alerts = []
        
        self.quality_documents = []
        self.document_revisions = []
        
        self.customer_complaints = []
        self.eight_d_reports = []
        
        self.ppap_submissions = []
        
        self.supplier_quality_metrics = []
        self.quality_kpis = []
        
        # Reference data (from existing tables)
        self.suppliers = [f'SUPPLIER-{i:06d}' for i in range(1, 21)]
        self.customers = [f'CUSTOMER-{i:06d}' for i in range(1, 51)]
        self.materials = [f'MATERIAL-{i:06d}' for i in range(1, 101)]
        self.products = [f'PRODUCT-{i:06d}' for i in range(1, 51)]
        self.employees = [f'EMP-{i:06d}' for i in range(1, 51)]
        
        # Counters
        self.counters = {
            'ncr': 1, 'ncr_detail': 1, 'capa': 1, 'capa_action': 1,
            'audit': 1, 'finding': 1, 'control_plan': 1, 'char': 1,
            'spc_chart': 1, 'spc_data': 1, 'equipment': 1, 'calibration': 1,
            'alert': 1, 'doc': 1, 'revision': 1, 'complaint': 1,
            'eight_d': 1, 'ppap': 1, 'metric': 1, 'kpi': 1
        }
    
    def generate_id(self, prefix: str, counter_key: str) -> str:
        id_val = f"{prefix}-{str(self.counters[counter_key]).zfill(6)}"
        self.counters[counter_key] += 1
        return id_val
    
    def generate_all_data(self):
        """Generate all QMS data"""
        print(f"\n{'='*80}")
        print(f"Generating QMS Data")
        print(f"{'='*80}\n")
        
        # Generate data
        self.generate_ncrs()
        self.generate_capas()
        self.generate_quality_audits()
        self.generate_control_plans()
        self.generate_spc_data()
        self.generate_calibration_data()
        self.generate_quality_documents()
        self.generate_customer_complaints()
        self.generate_eight_d_reports()
        self.generate_ppap_submissions()
        self.generate_supplier_quality_metrics()
        self.generate_quality_kpis()
        
        self._print_summary()
    
    # ========================================================================
    # NCR - NON-CONFORMANCE REPORTS
    # ========================================================================
    
    def generate_ncrs(self):
        """Generate non-conformance reports"""
        print("Generating NCRs...")
        
        source_types = ['incoming_inspection', 'in_process', 'final_inspection', 
                       'customer_complaint', 'supplier_quality']
        defect_types = ['dimensional', 'visual', 'functional', 'material', 'packaging']
        severities = ['critical', 'major', 'minor']
        dispositions = ['scrap', 'rework', 'use_as_is', 'return_to_supplier', 'sort']
        
        for i in range(50):
            detected_date = datetime.now() - timedelta(days=random.randint(1, 180))
            source_type = random.choice(source_types)
            
            # Determine supplier or customer based on source
            supplier_id = None
            customer_id = None
            if source_type in ['incoming_inspection', 'supplier_quality']:
                supplier_id = random.choice(self.suppliers)
            elif source_type == 'customer_complaint':
                customer_id = random.choice(self.customers)
            
            severity = random.choice(severities)
            disposition = random.choice(dispositions)
            
            # Cost varies by disposition
            if disposition == 'scrap':
                scrap_cost = random.uniform(5000, 50000)
                rework_cost = 0
            elif disposition == 'rework':
                scrap_cost = 0
                rework_cost = random.uniform(2000, 20000)
            else:
                scrap_cost = 0
                rework_cost = 0
            
            ncr = {
                'ncr_id': self.generate_id('NCR', 'ncr'),
                'ncr_number': f'NCR-{datetime.now().year}-{i+1:05d}',
                'source_type': source_type,
                'detected_date': detected_date.strftime('%Y-%m-%d'),
                'detected_by': random.choice(self.employees),
                'material_id': random.choice(self.materials),
                'quantity_inspected': round(random.uniform(100, 1000), 2),
                'quantity_defective': round(random.uniform(1, 50), 2),
                'defect_type': random.choice(defect_types),
                'defect_description': f'{random.choice(defect_types)} defect found during {source_type}',
                'defect_severity': severity,
                'supplier_id': supplier_id,
                'customer_id': customer_id,
                'containment_action': 'Segregated affected inventory',
                'containment_completed': True,
                'containment_date': (detected_date + timedelta(days=1)).strftime('%Y-%m-%d'),
                'disposition': disposition,
                'scrap_cost': round(scrap_cost, 2),
                'rework_cost': round(rework_cost, 2),
                'total_cost': round(scrap_cost + rework_cost, 2),
                'root_cause_method': random.choice(['5_why', 'fishbone', 'fault_tree']),
                'root_cause_description': 'Root cause identified through analysis',
                'root_cause_verified': random.random() > 0.3,
                'ncr_status': random.choice(['open', 'contained', 'capa_created', 'closed']),
                'priority': 'critical' if severity == 'critical' else 'high' if severity == 'major' else 'medium',
                'created_at': detected_date.strftime('%Y-%m-%d %H:%M:%S')
            }
            
            self.ncr_headers.append(ncr)
            
            # Generate 1-3 defect details
            for j in range(random.randint(1, 3)):
                detail = {
                    'defect_detail_id': self.generate_id('NCRDETAIL', 'ncr_detail'),
                    'ncr_id': ncr['ncr_id'],
                    'characteristic_name': f'Dimension {j+1}',
                    'specification': '10.00 ± 0.05 mm',
                    'actual_value': f'{random.uniform(9.90, 10.10):.3f} mm',
                    'measurement_method': 'Micrometer',
                    'measuring_equipment': f'MIC-{random.randint(1, 20):03d}',
                    'defect_location': random.choice(['Top surface', 'Bottom', 'Side', 'Internal']),
                    'created_at': detected_date.strftime('%Y-%m-%d %H:%M:%S')
                }
                self.ncr_defect_details.append(detail)
        
        print(f"Generated {len(self.ncr_headers)} NCRs, {len(self.ncr_defect_details)} defect details")
    
    # ========================================================================
    # CAPA - CORRECTIVE & PREVENTIVE ACTIONS
    # ========================================================================
    
    def generate_capas(self):
        """Generate CAPA records"""
        print("Generating CAPAs...")
        
        # Generate CAPAs for subset of NCRs
        ncrs_with_capa = random.sample(self.ncr_headers, min(30, len(self.ncr_headers)))
        
        for i, ncr in enumerate(ncrs_with_capa):
            initiated_date = datetime.strptime(ncr['detected_date'], '%Y-%m-%d') + timedelta(days=2)
            target_date = initiated_date + timedelta(days=random.randint(30, 90))
            
            action_type = random.choice(['corrective', 'preventive'])
            severity = ncr['defect_severity']
            
            capa = {
                'capa_id': self.generate_id('CAPA', 'capa'),
                'capa_number': f'CAPA-{datetime.now().year}-{i+1:05d}',
                'action_type': action_type,
                'initiated_from': 'ncr',
                'source_document_id': ncr['ncr_id'],
                'problem_description': ncr['defect_description'],
                'problem_severity': severity,
                'immediate_actions': ncr['containment_action'],
                'immediate_actions_completed': True,
                'root_cause_analysis': ncr['root_cause_description'],
                'root_cause_method': ncr['root_cause_method'],
                'root_cause_identified': True,
                'actions_planned': 'Process improvement and training',
                'responsible_person': random.choice(self.employees),
                'target_completion_date': target_date.strftime('%Y-%m-%d'),
                'capa_status': random.choice(['open', 'in_progress', 'completed', 'closed']),
                'implementation_cost': round(random.uniform(5000, 50000), 2),
                'created_at': initiated_date.strftime('%Y-%m-%d %H:%M:%S')
            }
            
            self.capa_headers.append(capa)
            
            # Generate 2-4 action items
            for j in range(random.randint(2, 4)):
                action_due = initiated_date + timedelta(days=random.randint(15, 60))
                
                action = {
                    'action_id': self.generate_id('CAPAACTION', 'capa_action'),
                    'capa_id': capa['capa_id'],
                    'action_sequence': j + 1,
                    'action_description': f'Action item {j+1}: {random.choice(["Process update", "Training", "Equipment upgrade", "Procedure revision"])}',
                    'action_type': random.choice(['process_change', 'training', 'equipment', 'documentation']),
                    'assigned_to': random.choice(self.employees),
                    'due_date': action_due.strftime('%Y-%m-%d'),
                    'action_status': random.choice(['pending', 'in_progress', 'completed']),
                    'created_at': initiated_date.strftime('%Y-%m-%d %H:%M:%S')
                }
                self.capa_actions.append(action)
        
        print(f"Generated {len(self.capa_headers)} CAPAs, {len(self.capa_actions)} action items")
    
    # ========================================================================
    # QUALITY AUDITS
    # ========================================================================
    
    def generate_quality_audits(self):
        """Generate quality audits"""
        print("Generating quality audits...")
        
        audit_types = ['internal', 'supplier', 'customer', 'certification']
        standards = ['ISO_9001', 'IATF_16949', 'ISO_14001', 'AS9100']
        
        for i in range(20):
            planned_date = datetime.now() - timedelta(days=random.randint(1, 180))
            actual_date = planned_date + timedelta(days=random.randint(0, 7))
            
            audit_type = random.choice(audit_types)
            
            # Score and rating
            score = random.uniform(70, 98)
            if score >= 95:
                rating = 'excellent'
            elif score >= 85:
                rating = 'satisfactory'
            elif score >= 70:
                rating = 'needs_improvement'
            else:
                rating = 'unsatisfactory'
            
            major_findings = random.randint(0, 3) if score < 90 else 0
            minor_findings = random.randint(2, 8)
            observations = random.randint(3, 10)
            
            audit = {
                'audit_id': self.generate_id('AUDIT', 'audit'),
                'audit_number': f'AUDIT-{datetime.now().year}-{i+1:05d}',
                'audit_type': audit_type,
                'audit_standard': random.choice(standards),
                'audit_scope': f'{audit_type.title()} audit of quality management system',
                'planned_date': planned_date.strftime('%Y-%m-%d'),
                'actual_start_date': actual_date.strftime('%Y-%m-%d'),
                'actual_end_date': (actual_date + timedelta(days=1)).strftime('%Y-%m-%d'),
                'audit_duration_hours': round(random.uniform(4, 16), 1),
                'lead_auditor': random.choice(self.employees),
                'audit_score': round(score, 2),
                'audit_rating': rating,
                'total_findings': major_findings + minor_findings + observations,
                'major_findings': major_findings,
                'minor_findings': minor_findings,
                'observations': observations,
                'followup_required': major_findings > 0 or minor_findings > 3,
                'audit_status': random.choice(['completed', 'closed']),
                'created_at': planned_date.strftime('%Y-%m-%d %H:%M:%S')
            }
            self.quality_audits.append(audit)
            
            # Generate findings
            total_findings = major_findings + minor_findings + observations
            for j in range(total_findings):
                if j < major_findings:
                    finding_type = 'major_nc'
                    risk = 'high'
                elif j < major_findings + minor_findings:
                    finding_type = 'minor_nc'
                    risk = 'medium'
                else:
                    finding_type = 'observation'
                    risk = 'low'
                
                finding = {
                    'finding_id': self.generate_id('FINDING', 'finding'),
                    'audit_id': audit['audit_id'],
                    'finding_number': j + 1,
                    'finding_type': finding_type,
                    'finding_category': random.choice(['documentation', 'process', 'equipment', 'training']),
                    'finding_description': f'{finding_type.upper()}: {random.choice(["Process not documented", "Missing records", "Equipment not calibrated", "Training incomplete"])}',
                    'requirement_reference': f'ISO 9001:2015 clause {random.randint(4, 10)}.{random.randint(1, 7)}',
                    'risk_level': risk,
                    'corrective_action_required': finding_type in ['major_nc', 'minor_nc'],
                    'responsible_person': random.choice(self.employees),
                    'target_closure_date': (actual_date + timedelta(days=30 if finding_type == 'major_nc' else 60)).strftime('%Y-%m-%d'),
                    'finding_status': random.choice(['open', 'capa_created', 'completed']),
                    'created_at': actual_date.strftime('%Y-%m-%d %H:%M:%S')
                }
                self.audit_findings.append(finding)
        
        print(f"Generated {len(self.quality_audits)} audits, {len(self.audit_findings)} findings")
    
    # ========================================================================
    # CONTROL PLANS
    # ========================================================================
    
    def generate_control_plans(self):
        """Generate control plans"""
        print("Generating control plans...")
        
        # Generate control plans for sample of products
        for i, product_id in enumerate(self.products[:15]):
            created_date = datetime.now() - timedelta(days=random.randint(30, 365))
            
            plan = {
                'control_plan_id': self.generate_id('CP', 'control_plan'),
                'control_plan_number': f'CP-{i+1:05d}',
                'product_id': product_id,
                'process_name': f'Manufacturing Process for {product_id}',
                'control_plan_title': f'Control Plan - {product_id}',
                'control_plan_type': 'production',
                'version': '1.0',
                'revision_date': created_date.strftime('%Y-%m-%d'),
                'prepared_by': random.choice(self.employees),
                'approved_by': random.choice(self.employees),
                'approval_date': created_date.strftime('%Y-%m-%d'),
                'effective_date': created_date.strftime('%Y-%m-%d'),
                'plan_status': 'active',
                'created_at': created_date.strftime('%Y-%m-%d %H:%M:%S')
            }
            self.control_plans.append(plan)
            
            # Generate 5-10 characteristics
            process_steps = ['Machining', 'Assembly', 'Heat Treatment', 'Surface Finish', 'Final Inspection']
            for j, step in enumerate(random.sample(process_steps, min(5, len(process_steps)))):
                char = {
                    'characteristic_id': self.generate_id('CHAR', 'char'),
                    'control_plan_id': plan['control_plan_id'],
                    'sequence_number': j + 1,
                    'process_step': step,
                    'characteristic_name': f'{step} Dimension',
                    'characteristic_type': random.choice(['product', 'process']),
                    'specification': '10.00 ± 0.05 mm',
                    'lower_spec_limit': 9.95,
                    'target_value': 10.00,
                    'upper_spec_limit': 10.05,
                    'unit_of_measure': 'mm',
                    'measurement_technique': random.choice(['Micrometer', 'Caliper', 'CMM', 'Gauge']),
                    'measuring_equipment': f'{random.choice(["MIC", "CAL", "CMM", "GAG"])}-{random.randint(1, 20):03d}',
                    'sample_size': random.choice(['5', '10', '1']),
                    'sample_frequency': random.choice(['Hourly', 'Every shift', 'First/last piece', 'Every batch']),
                    'control_method': random.choice(['spc', '100_percent', 'periodic']),
                    'reaction_plan': 'Stop production, notify supervisor, investigate root cause',
                    'responsible_person': random.choice(self.employees),
                    'created_at': created_date.strftime('%Y-%m-%d %H:%M:%S')
                }
                self.control_characteristics.append(char)
        
        print(f"Generated {len(self.control_plans)} control plans, {len(self.control_characteristics)} characteristics")
    
    # ========================================================================
    # SPC - STATISTICAL PROCESS CONTROL
    # ========================================================================
    
    def generate_spc_data(self):
        """Generate SPC charts and data points"""
        print("Generating SPC data...")
        
        # Generate SPC charts for sample characteristics
        for i, char in enumerate(self.control_characteristics[:10]):
            chart = {
                'chart_id': self.generate_id('SPC', 'spc_chart'),
                'chart_number': f'SPC-{i+1:05d}',
                'process_name': char['process_step'],
                'characteristic_name': char['characteristic_name'],
                'chart_type': 'x_bar_r',
                'specification': char['specification'],
                'lower_spec_limit': char['lower_spec_limit'],
                'target_value': char['target_value'],
                'upper_spec_limit': char['upper_spec_limit'],
                'unit_of_measure': char['unit_of_measure'],
                'upper_control_limit': char['target_value'] + 0.03,
                'center_line': char['target_value'],
                'lower_control_limit': char['target_value'] - 0.03,
                'cpk': round(random.uniform(1.2, 2.0), 3),
                'cp': round(random.uniform(1.3, 2.1), 3),
                'subgroup_size': 5,
                'subgroup_frequency': 'Hourly',
                'chart_status': random.choice(['active', 'active', 'active', 'out_of_control']),
                'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            self.spc_charts.append(chart)
            
            # Generate 50 data points (last 50 hours)
            for j in range(50):
                measurement_time = datetime.now() - timedelta(hours=50-j)
                
                # Generate value with occasional out-of-control points
                if chart['chart_status'] == 'out_of_control' and j > 40:
                    # Trending upward
                    value = chart['target_value'] + (j - 40) * 0.005
                else:
                    # Normal variation
                    value = chart['target_value'] + random.uniform(-0.02, 0.02)
                
                out_of_control = abs(value - chart['target_value']) > 0.03
                
                data_point = {
                    'data_point_id': self.generate_id('SPCDATA', 'spc_data'),
                    'chart_id': chart['chart_id'],
                    'measurement_timestamp': measurement_time.strftime('%Y-%m-%d %H:%M:%S'),
                    'subgroup_number': j + 1,
                    'measurement_value': round(value, 6),
                    'range_value': round(random.uniform(0.005, 0.02), 6),
                    'measured_by': random.choice(self.employees),
                    'out_of_control': out_of_control,
                    'violation_type': 'point_beyond_limits' if out_of_control else None,
                    'action_taken': 'Production stopped, investigation initiated' if out_of_control else None,
                    'created_at': measurement_time.strftime('%Y-%m-%d %H:%M:%S')
                }
                self.spc_data_points.append(data_point)
        
        print(f"Generated {len(self.spc_charts)} SPC charts, {len(self.spc_data_points)} data points")
    
    # ========================================================================
    # CALIBRATION
    # ========================================================================
    
    def generate_calibration_data(self):
        """Generate measuring equipment and calibration records"""
        print("Generating calibration data...")
        
        equipment_types = ['micrometer', 'caliper', 'gauge', 'scale', 'thermometer', 
                          'pressure_gauge', 'cmm', 'hardness_tester']
        
        # Generate 30 pieces of measuring equipment
        for i in range(30):
            purchase_date = datetime.now() - timedelta(days=random.randint(365, 1825))
            last_cal = datetime.now() - timedelta(days=random.randint(1, 180))
            
            freq_days = random.choice([90, 180, 365])
            next_due = last_cal + timedelta(days=freq_days)
            
            # Determine status
            days_until_due = (next_due - datetime.now()).days
            if days_until_due < 0:
                status = 'overdue'
            elif days_until_due <= 7:
                status = 'calibration_due'
            else:
                status = 'active'
            
            equipment = {
                'equipment_id': self.generate_id('EQUIP', 'equipment'),
                'equipment_number': f'{random.choice(["MIC", "CAL", "GAG", "CMM"])}-{i+1:03d}',
                'equipment_name': f'{random.choice(equipment_types).title()} #{i+1}',
                'equipment_type': random.choice(equipment_types),
                'manufacturer': random.choice(['Mitutoyo', 'Starrett', 'Brown & Sharpe', 'Mahr']),
                'model_number': f'MOD-{random.randint(100, 999)}',
                'serial_number': f'SN-{random.randint(10000, 99999)}',
                'measurement_range': '0-25 mm',
                'accuracy': '± 0.001 mm',
                'calibration_frequency_days': freq_days,
                'last_calibration_date': last_cal.strftime('%Y-%m-%d'),
                'next_calibration_due': next_due.strftime('%Y-%m-%d'),
                'equipment_status': status,
                'locked_out': status == 'overdue',
                'lockout_reason': 'Calibration overdue' if status == 'overdue' else None,
                'purchase_date': purchase_date.strftime('%Y-%m-%d'),
                'purchase_cost': round(random.uniform(5000, 50000), 2),
                'created_at': purchase_date.strftime('%Y-%m-%d %H:%M:%S')
            }
            self.measuring_equipment.append(equipment)
            
            # Generate calibration history (last 2-3 calibrations)
            num_cals = random.randint(2, 4)
            for j in range(num_cals):
                cal_date = last_cal - timedelta(days=freq_days * j)
                
                cal_record = {
                    'calibration_id': self.generate_id('CAL', 'calibration'),
                    'calibration_number': f'CAL-{datetime.now().year}-{self.counters["calibration"]:05d}',
                    'equipment_id': equipment['equipment_id'],
                    'calibration_date': cal_date.strftime('%Y-%m-%d'),
                    'next_due_date': (cal_date + timedelta(days=freq_days)).strftime('%Y-%m-%d'),
                    'calibrated_by': random.choice(self.employees) if random.random() > 0.5 else None,
                    'calibration_lab': 'External Calibration Lab' if random.random() > 0.5 else None,
                    'calibration_result': random.choice(['pass', 'pass', 'pass', 'adjusted_and_pass']),
                    'as_found_condition': 'Within tolerance' if random.random() > 0.3 else 'Slight deviation',
                    'as_left_condition': 'Within tolerance',
                    'certificate_number': f'CERT-{random.randint(10000, 99999)}',
                    'calibration_cost': round(random.uniform(1000, 5000), 2),
                    'created_at': cal_date.strftime('%Y-%m-%d %H:%M:%S')
                }
                self.calibration_records.append(cal_record)
            
            # Generate alerts for due/overdue equipment
            if days_until_due <= 30:
                alert = {
                    'alert_id': self.generate_id('ALERT', 'alert'),
                    'equipment_id': equipment['equipment_id'],
                    'alert_type': 'overdue' if days_until_due < 0 else 'due_30_days' if days_until_due <= 30 else 'due_7_days',
                    'alert_date': datetime.now().strftime('%Y-%m-%d'),
                    'days_until_due': days_until_due,
                    'notification_sent': random.random() > 0.3,
                    'resolved': False,
                    'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                self.calibration_alerts.append(alert)
        
        print(f"Generated {len(self.measuring_equipment)} measuring equipment")
        print(f"  {len(self.calibration_records)} calibration records")
        print(f"  {len(self.calibration_alerts)} calibration alerts")
    
    # ========================================================================
    # QUALITY DOCUMENTS
    # ========================================================================
    
    def generate_quality_documents(self):
        """Generate quality documents"""
        print("Generating quality documents...")
        
        doc_types = ['procedure', 'work_instruction', 'form', 'specification', 
                    'control_plan', 'inspection_instruction']
        
        for i in range(20):
            created_date = datetime.now() - timedelta(days=random.randint(30, 730))
            
            doc = {
                'document_id': self.generate_id('DOC', 'doc'),
                'document_number': f'QD-{i+1:05d}',
                'document_title': f'{random.choice(doc_types).replace("_", " ").title()} Document {i+1}',
                'document_type': random.choice(doc_types),
                'version': '1.0',
                'revision_number': random.randint(1, 5),
                'revision_date': created_date.strftime('%Y-%m-%d'),
                'document_description': 'Quality management system document',
                'document_url': f'/documents/quality/QD-{i+1:05d}.pdf',
                'document_owner': random.choice(self.employees),
                'prepared_by': random.choice(self.employees),
                'approved_by': random.choice(self.employees),
                'approval_date': created_date.strftime('%Y-%m-%d'),
                'effective_date': created_date.strftime('%Y-%m-%d'),
                'document_status': random.choice(['active', 'active', 'active', 'under_review']),
                'periodic_review_required': True,
                'review_frequency_months': 12,
                'next_review_date': (created_date + timedelta(days=365)).strftime('%Y-%m-%d'),
                'created_at': created_date.strftime('%Y-%m-%d %H:%M:%S')
            }
            self.quality_documents.append(doc)
        
        print(f"Generated {len(self.quality_documents)} quality documents")
    
    # ========================================================================
    # CUSTOMER COMPLAINTS
    # ========================================================================
    
    def generate_customer_complaints(self):
        """Generate customer complaints"""
        print("Generating customer complaints...")
        
        complaint_types = ['quality', 'delivery', 'documentation', 'damage', 'performance']
        severities = ['critical', 'major', 'minor']
        
        for i in range(30):
            complaint_date = datetime.now() - timedelta(days=random.randint(1, 180))
            customer_id = random.choice(self.customers)
            severity = random.choice(severities)
            
            complaint = {
                'complaint_id': self.generate_id('COMP', 'complaint'),
                'complaint_number': f'COMP-{datetime.now().year}-{i+1:05d}',
                'customer_id': customer_id,
                'product_id': random.choice(self.products),
                'complaint_date': complaint_date.strftime('%Y-%m-%d'),
                'complaint_description': f'Customer complaint regarding {random.choice(complaint_types)}',
                'complaint_type': random.choice(complaint_types),
                'severity': severity,
                'safety_issue': severity == 'critical' and random.random() > 0.5,
                'quantity_affected': round(random.uniform(10, 500), 2),
                'quantity_returned': round(random.uniform(5, 100), 2),
                'immediate_action': 'Replacement provided, investigation initiated',
                'root_cause': 'Root cause identified through investigation',
                'investigation_method': random.choice(['5_why', '8d', 'fishbone']),
                'replacement_cost': round(random.uniform(5000, 50000), 2),
                'credit_issued': round(random.uniform(0, 20000), 2),
                'complaint_status': random.choice(['open', 'investigating', 'resolved', 'closed']),
                'customer_satisfied': random.random() > 0.2,
                'created_at': complaint_date.strftime('%Y-%m-%d %H:%M:%S')
            }
            complaint['total_cost'] = complaint['replacement_cost'] + complaint['credit_issued']
            
            self.customer_complaints.append(complaint)
        
        print(f"Generated {len(self.customer_complaints)} customer complaints")
    
    # ========================================================================
    # 8D REPORTS
    # ========================================================================
    
    def generate_eight_d_reports(self):
        """Generate 8D problem solving reports"""
        print("Generating 8D reports...")
        
        # Generate 8D for subset of customer complaints
        complaints_with_8d = random.sample(self.customer_complaints, 
                                          min(15, len(self.customer_complaints)))
        
        for i, complaint in enumerate(complaints_with_8d):
            initiated_date = datetime.strptime(complaint['complaint_date'], '%Y-%m-%d')
            
            eight_d = {
                'eight_d_id': self.generate_id('8D', 'eight_d'),
                'eight_d_number': f'8D-{datetime.now().year}-{i+1:05d}',
                'source_type': 'customer_complaint',
                'source_document_id': complaint['complaint_id'],
                'team_leader': random.choice(self.employees),
                'team_members': random.sample(self.employees, 4),
                'problem_description': complaint['complaint_description'],
                'is_statement': f'Problem IS affecting {complaint["complaint_type"]}',
                'is_not_statement': f'Problem is NOT affecting other aspects',
                'containment_action': complaint['immediate_action'],
                'containment_date': (initiated_date + timedelta(days=1)).strftime('%Y-%m-%d'),
                'containment_verified': True,
                'root_cause_analysis': complaint['root_cause'],
                'root_cause_method': complaint['investigation_method'],
                'root_cause_verified': True,
                'permanent_actions': 'Process improvements implemented',
                'verification_plan': 'Monitor for 3 months',
                'verification_completed': random.random() > 0.3,
                'preventive_actions': 'Updated procedures and training',
                'eight_d_status': random.choice(['in_progress', 'completed', 'closed']),
                'created_at': initiated_date.strftime('%Y-%m-%d %H:%M:%S')
            }
            self.eight_d_reports.append(eight_d)
        
        print(f"Generated {len(self.eight_d_reports)} 8D reports")
    
    # ========================================================================
    # PPAP SUBMISSIONS
    # ========================================================================
    
    def generate_ppap_submissions(self):
        """Generate PPAP submissions"""
        print("Generating PPAP submissions...")
        
        for i in range(10):
            submission_date = datetime.now() - timedelta(days=random.randint(30, 365))
            ppap_level = random.randint(1, 5)
            
            ppap = {
                'ppap_id': self.generate_id('PPAP', 'ppap'),
                'ppap_number': f'PPAP-{datetime.now().year}-{i+1:05d}',
                'product_id': random.choice(self.products),
                'part_number': f'PN-{random.randint(1000, 9999)}',
                'part_name': f'Component {i+1}',
                'supplier_id': random.choice(self.suppliers) if random.random() > 0.5 else None,
                'customer_id': random.choice(self.customers),
                'ppap_level': ppap_level,
                'submission_date': submission_date.strftime('%Y-%m-%d'),
                'submission_reason': random.choice(['new_part', 'engineering_change', 'process_change']),
                'design_records': True,
                'engineering_change_docs': ppap_level >= 3,
                'customer_approval': ppap_level >= 4,
                'dfmea_completed': ppap_level >= 3,
                'pfmea_completed': ppap_level >= 3,
                'control_plan': True,
                'msa_study': ppap_level >= 4,
                'dimensional_results': True,
                'material_test_results': ppap_level >= 4,
                'initial_process_study': ppap_level >= 4,
                'sample_products': True,
                'psw_signed': True,
                'psw_signed_date': submission_date.strftime('%Y-%m-%d'),
                'ppap_status': random.choice(['submitted', 'under_review', 'approved']),
                'reviewed_by': random.choice(self.employees),
                'review_date': (submission_date + timedelta(days=7)).strftime('%Y-%m-%d'),
                'created_at': submission_date.strftime('%Y-%m-%d %H:%M:%S')
            }
            self.ppap_submissions.append(ppap)
        
        print(f"Generated {len(self.ppap_submissions)} PPAP submissions")
    
    # ========================================================================
    # SUPPLIER QUALITY METRICS
    # ========================================================================
    
    def generate_supplier_quality_metrics(self):
        """Generate supplier quality metrics"""
        print("Generating supplier quality metrics...")
        
        # Last 6 months for each supplier
        for supplier_id in self.suppliers:
            for months_ago in range(6):
                metric_date = datetime.now() - timedelta(days=30 * months_ago)
                metric_period = metric_date.strftime('%Y-%m')
                
                total_qty = random.uniform(1000, 10000)
                acceptance_rate = random.uniform(96, 99.9)
                accepted_qty = total_qty * acceptance_rate / 100
                rejected_qty = total_qty - accepted_qty
                
                defect_ppm = int((rejected_qty / total_qty) * 1000000)
                
                metric = {
                    'metric_id': self.generate_id('SQMETRIC', 'metric'),
                    'supplier_id': supplier_id,
                    'metric_period': metric_period,
                    'total_receipts': random.randint(5, 20),
                    'receipts_inspected': random.randint(5, 20),
                    'receipts_accepted': random.randint(4, 18),
                    'receipts_rejected': random.randint(0, 2),
                    'total_quantity_received': round(total_qty, 4),
                    'quantity_accepted': round(accepted_qty, 4),
                    'quantity_rejected': round(rejected_qty, 4),
                    'total_defects': int(rejected_qty),
                    'defect_ppm': defect_ppm,
                    'critical_defects': random.randint(0, 2),
                    'major_defects': random.randint(0, 5),
                    'minor_defects': random.randint(2, 10),
                    'acceptance_rate_pct': round(acceptance_rate, 2),
                    'quality_score': round(acceptance_rate, 2),
                    'ncr_count': random.randint(0, 3),
                    'capa_count': random.randint(0, 2),
                    'rejection_cost': round(rejected_qty * random.uniform(50, 200), 2),
                    'created_at': metric_date.strftime('%Y-%m-%d %H:%M:%S')
                }
                metric['rework_cost'] = round(random.uniform(0, 10000), 2)
                metric['sorting_cost'] = round(random.uniform(0, 5000), 2)
                metric['total_copq'] = metric['rejection_cost'] + metric['rework_cost'] + metric['sorting_cost']
                
                self.supplier_quality_metrics.append(metric)
        
        print(f"Generated {len(self.supplier_quality_metrics)} supplier quality metrics")
    
    # ========================================================================
    # QUALITY KPIs
    # ========================================================================
    
    def generate_quality_kpis(self):
        """Generate daily quality KPIs"""
        print("Generating quality KPIs...")
        
        # Last 30 days
        for days_ago in range(30):
            kpi_date = datetime.now() - timedelta(days=days_ago)
            
            kpi = {
                'kpi_id': self.generate_id('KPI', 'kpi'),
                'kpi_date': kpi_date.strftime('%Y-%m-%d'),
                'internal_defect_ppm': random.randint(50, 500),
                'first_time_quality_pct': round(random.uniform(95, 99.5), 2),
                'customer_complaints': random.randint(0, 5),
                'customer_returns_ppm': random.randint(10, 100),
                'incoming_rejection_pct': round(random.uniform(0.5, 3), 2),
                'supplier_defect_ppm': random.randint(100, 1000),
                'processes_in_control': random.randint(45, 50),
                'processes_total': 50,
                'process_capability_avg': round(random.uniform(1.2, 1.8), 3),
                'ncr_opened': random.randint(1, 5),
                'ncr_closed': random.randint(1, 5),
                'ncr_open_count': random.randint(10, 30),
                'capa_overdue': random.randint(0, 3),
                'prevention_cost': round(random.uniform(10000, 30000), 2),
                'appraisal_cost': round(random.uniform(15000, 40000), 2),
                'internal_failure_cost': round(random.uniform(5000, 20000), 2),
                'external_failure_cost': round(random.uniform(2000, 15000), 2),
                'equipment_calibrated_pct': round(random.uniform(92, 100), 2),
                'equipment_overdue': random.randint(0, 3),
                'created_at': kpi_date.strftime('%Y-%m-%d %H:%M:%S')
            }
            kpi['total_coq'] = (kpi['prevention_cost'] + kpi['appraisal_cost'] + 
                               kpi['internal_failure_cost'] + kpi['external_failure_cost'])
            
            self.quality_kpis.append(kpi)
        
        print(f"Generated {len(self.quality_kpis)} daily quality KPIs")
    
    def _print_summary(self):
        print(f"\n{'='*80}")
        print(f"QMS Data Generation Complete!")
        print(f"{'='*80}")
        print(f"\nNon-Conformance & CAPA:")
        print(f"  NCRs: {len(self.ncr_headers)}")
        print(f"  NCR Defect Details: {len(self.ncr_defect_details)}")
        print(f"  CAPAs: {len(self.capa_headers)}")
        print(f"  CAPA Actions: {len(self.capa_actions)}")
        
        print(f"\nAudits:")
        print(f"  Quality Audits: {len(self.quality_audits)}")
        print(f"  Audit Findings: {len(self.audit_findings)}")
        
        print(f"\nProcess Control:")
        print(f"  Control Plans: {len(self.control_plans)}")
        print(f"  Control Characteristics: {len(self.control_characteristics)}")
        print(f"  SPC Charts: {len(self.spc_charts)}")
        print(f"  SPC Data Points: {len(self.spc_data_points)}")
        
        print(f"\nCalibration:")
        print(f"  Measuring Equipment: {len(self.measuring_equipment)}")
        print(f"  Calibration Records: {len(self.calibration_records)}")
        print(f"  Calibration Alerts: {len(self.calibration_alerts)}")
        
        print(f"\nDocumentation:")
        print(f"  Quality Documents: {len(self.quality_documents)}")
        
        print(f"\nCustomer & Problem Solving:")
        print(f"  Customer Complaints: {len(self.customer_complaints)}")
        print(f"  8D Reports: {len(self.eight_d_reports)}")
        
        print(f"\nSupplier Quality:")
        print(f"  PPAP Submissions: {len(self.ppap_submissions)}")
        print(f"  Supplier Quality Metrics: {len(self.supplier_quality_metrics)}")
        
        print(f"\nMetrics:")
        print(f"  Quality KPIs: {len(self.quality_kpis)}")
    
    def to_json(self, output_file='qms_data.json'):
        """Export to JSON"""
        print(f"\nExporting to JSON...")
        
        data = {
            'metadata': {
                'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            },
            'ncr': {
                'ncr_headers': self.ncr_headers[:30],  # Sample
                'ncr_defect_details': self.ncr_defect_details[:50]
            },
            'capa': {
                'capa_headers': self.capa_headers,
                'capa_actions': self.capa_actions[:50]
            },
            'audits': {
                'quality_audits': self.quality_audits,
                'audit_findings': self.audit_findings[:50]
            },
            'control_plans': {
                'control_plans': self.control_plans,
                'control_characteristics': self.control_characteristics[:30]
            },
            'spc': {
                'spc_charts': self.spc_charts,
                'spc_data_points': self.spc_data_points[:100]  # Sample
            },
            'calibration': {
                'measuring_equipment': self.measuring_equipment,
                'calibration_records': self.calibration_records[:30],
                'calibration_alerts': self.calibration_alerts
            },
            'documents': {
                'quality_documents': self.quality_documents
            },
            'complaints': {
                'customer_complaints': self.customer_complaints,
                'eight_d_reports': self.eight_d_reports
            },
            'ppap': {
                'ppap_submissions': self.ppap_submissions
            },
            'metrics': {
                'supplier_quality_metrics': self.supplier_quality_metrics[:30],
                'quality_kpis': self.quality_kpis
            }
        }
        
        with open(output_file, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"Data exported to {output_file}")


if __name__ == "__main__":
    generator = QMSDataGenerator()
    generator.generate_all_data()
    generator.to_json()
    
    print("\n" + "="*80)
    print("QMS Data Generation Complete!")
    print("="*80)
