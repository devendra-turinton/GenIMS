#!/usr/bin/env python3
"""
GenIMS QMS Data Generator - Enterprise-grade
Generates data that matches the actual PostgreSQL schema with ALL required fields
"""

import json
import random
import time
from datetime import datetime, timedelta
from pathlib import Path
import uuid
import sys

# Add scripts to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))
from generator_helper import get_helper


class TimeCoordinator:
    """Manages time coordination and current-date enforcement"""
    def __init__(self):
        # Always use current date for data generation
        current_time = datetime.now()
        self.base_time = current_time.replace(hour=0, minute=0, second=0, microsecond=0)
        
    def get_current_time(self):
        """Get current date enforced time"""
        return self.base_time
    
    def get_current_date(self):
        """Get current date"""
        return self.base_time.date()
        
    def get_timestamp_with_offset(self, offset_seconds):
        """Get timestamp with offset but still on current date"""
        return self.base_time + timedelta(seconds=offset_seconds)
        
    def add_coordination_delay(self, operation_name):
        """Add time coordination delay between operations"""
        delay = random.uniform(2.0, 3.5)
        time.sleep(delay)
        
    def generate_unique_timestamp(self, base_offset=0):
        """Generate unique timestamp with millisecond precision"""
        current_time = self.base_time + timedelta(seconds=base_offset)
        return current_time.strftime('%Y%m%d%H%M%S') + f"{current_time.microsecond // 1000:03d}"


# Load master data for references
try:
    master_data_file = Path(__file__).parent.parent / "01 - Base Data" / "genims_master_data.json"
    with open(master_data_file, 'r') as f:
        master_data = json.load(f)
except:
    print("Warning: Could not load master data")
    master_data = {'products': [], 'factories': [], 'employees': [], 'suppliers': []}

class QMSDataGenerator:
    def __init__(self):
        # Load helper for FK validation
        self.helper = get_helper()
        self.registry = self.helper.registry
        
        # Initialize TimeCoordinator for consistent enterprise time
        self.time_coordinator = TimeCoordinator()
        self.enterprise_date = self.time_coordinator.get_current_date()
        
        self.products = master_data.get('products', [])
        self.factories = master_data.get('factories', [])
        self.employees = master_data.get('employees', [])
        self.suppliers = master_data.get('suppliers', [])
        
        # Load ERP data for PO linking
        self.purchase_orders = []
        self.purchase_order_lines = []
        self.sales_orders = []
        self.sales_order_lines = []
        try:
            erp_file = Path(__file__).parent.parent / "04 - ERP & MES Integration" / "genims_erp_data.json"
            if erp_file.exists():
                with open(erp_file, 'r') as f:
                    erp_data = json.load(f)
                    self.purchase_orders = erp_data.get('purchase_orders', [])
                    self.purchase_order_lines = erp_data.get('purchase_order_lines', [])
                    self.sales_orders = erp_data.get('sales_orders', [])
                    self.sales_order_lines = erp_data.get('sales_order_lines', [])
        except:
            pass
        
        self.data = {
            'customer_complaints': [],
            'quality_audits': [],
            'audit_findings': [],
            'quality_documents': [],
            'quality_kpis': [],
            'ncr_headers': [],
            'ncr_defect_details': [],
            'capa_headers': [],
            'capa_actions': [],
            'control_plans': [],
            'control_plan_characteristics': [],
            'supplier_quality_metrics': [],
            'calibration_records': [],
            'calibration_alerts': [],
            'measuring_equipment': [],
            'spc_control_charts': [],
            'spc_data_points': [],
            'ppap_submissions': [],
            'document_revisions': [],
            'eight_d_reports': [],
            'qms_integration_log': [],
        }
    
    def generate(self, days=90):
        """Generate all QMS data"""
        print("Generating QMS data...")
        start_date = datetime.now() - timedelta(days=days)
        
        self.generate_measuring_equipment()
        self.generate_customer_complaints(start_date, days)
        self.generate_quality_audits(start_date, days)
        self.generate_audit_findings()
        self.generate_ncr_headers(start_date, days)
        self.generate_ncr_defect_details()
        self.generate_capa_headers(start_date, days)
        self.generate_capa_actions()
        self.generate_control_plans()
        self.generate_control_plan_characteristics()
        self.generate_supplier_quality_metrics()
        self.generate_calibration_records(start_date, days)
        self.generate_calibration_alerts()
        self.generate_spc_control_charts()
        self.generate_spc_data_points()
        self.generate_ppap_submissions(start_date, days)
        self.generate_quality_documents()
        self.generate_quality_kpis(start_date, days)
        self.generate_document_revisions()
        self.generate_eight_d_reports()
        self.generate_qms_integration_log(start_date, days)
        
        return self.data
    
    def generate_customer_complaints(self, start_date, days):
        """Generate customer complaints"""
        print("Generating customer complaints...")
        current_date = start_date
        complaint_counter = 1
        
        # Load customers from CRM if available
        customers = []
        try:
            crm_file = Path(__file__).parent.parent / "07 - CRM" / "genims_crm_data.json"
            if crm_file.exists():
                with open(crm_file, 'r') as f:
                    crm_data = json.load(f)
                    customers = crm_data.get('customers', [])
        except:
            customers = []
        
        # Fallback customer IDs
        if not customers:
            customers = [{'customer_id': f'CUST-{i:06d}'} for i in range(1, 11)]
        
        customer_ids = [c.get('customer_id', f'CUST-{i:06d}') for i, c in enumerate(customers[:50], 1)]
        product_ids = [p.get('product_id', f'PROD-{i:06d}') for i, p in enumerate(self.products[:50], 1)] if self.products else [f'PROD-{i:06d}' for i in range(1, 11)]
        
        for _ in range(days // 15):  # ~2 complaints every 15 days
            current_date += timedelta(days=random.randint(5, 15))
            
            complaint = {
                'complaint_id': f"COMP-{complaint_counter:06d}",
                'complaint_number': f"COMP-{self.enterprise_date.strftime('%Y%m%d')}-{complaint_counter:04d}",
                'customer_id': random.choice(customer_ids) if customer_ids else 'CUST-000001',
                'product_id': random.choice(product_ids) if product_ids else 'PROD-000001',
                'complaint_date': current_date.strftime('%Y-%m-%d'),
                'complaint_description': random.choice([
                    'Product does not meet specifications',
                    'Defective delivery quality',
                    'Missing components in shipment',
                    'Dimensional tolerances exceeded',
                    'Surface finish not acceptable'
                ]),
                'complaint_type': random.choice(['quality', 'delivery', 'documentation', 'service']),
                'severity': random.choice(['critical', 'major', 'minor']),
                'safety_issue': random.choice([True, False]),
                'quantity_affected': random.randint(10, 500),
                'immediate_action': random.choice(['product_recall', 'supplier_corrective_action', 'redesign', 'none']),
                'complaint_status': random.choice(['open', 'in_review', 'resolved', 'closed']),
                'created_at': f"{current_date.strftime('%Y-%m-%d')} {random.randint(0, 23):02d}:{random.randint(0, 59):02d}:{random.randint(0, 59):02d}"
            }
            self.data['customer_complaints'].append(complaint)
            complaint_counter += 1
        
        print(f"Generated {len(self.data['customer_complaints'])} customer complaints")
    
    def generate_quality_audits(self, start_date, days):
        """Generate quality audit records"""
        print("Generating quality audits...")
        current_date = start_date
        audit_counter = 1
        
        for day in range(days):
            if random.random() < 0.15:
                audit = {
                    'audit_id': f"AUDIT-{audit_counter:06d}",
                    'audit_number': f"AUDIT-{current_date.strftime('%Y%m%d')}-{audit_counter:03d}",
                    'audit_type': random.choice(['internal', 'supplier', 'customer', 'certification']),
                    'audit_standard': random.choice(['ISO_9001', 'IATF_16949', 'ISO_14001']),
                    'audit_scope': f"Audit of {random.choice(['Production', 'Quality', 'Maintenance', 'Planning'])} department",
                    'auditee_department': random.choice(['Production', 'Quality', 'Maintenance', 'Planning']),
                    'auditee_supplier_id': random.choice([s.get('supplier_id', f'SUP-{random.randint(1001, 2000):06d}') for s in self.suppliers] + [f'SUP-{random.randint(1001, 2000):06d}']),  # Now populated
                    'planned_date': current_date.strftime('%Y-%m-%d'),
                    'actual_start_date': current_date.strftime('%Y-%m-%d'),
                    'actual_end_date': (current_date + timedelta(days=1)).strftime('%Y-%m-%d'),
                    'audit_duration_hours': round(random.uniform(4, 16), 1),
                    'lead_auditor': random.choice([e.get('employee_id', 'EMP-000001') for e in self.employees] + ['EMP-000001']),
                    'audit_team': [e.get('employee_id', 'EMP-000001') for e in random.sample(self.employees if len(self.employees) >= 3 else self.employees + [{'employee_id': 'EMP-000002'}, {'employee_id': 'EMP-000003'}], min(3, len(self.employees) + 2))][:3],  # Safe sample with bounds
                    'audit_location': random.choice([f.get('factory_id', 'FAC-000001') for f in self.factories] + ['FAC-000001']),
                    'audit_score': round(random.uniform(60, 100), 2),
                    'audit_rating': random.choice(['excellent', 'satisfactory', 'needs_improvement']),
                    'total_findings': random.randint(0, 5),
                    'major_findings': random.randint(0, 2),
                    'minor_findings': random.randint(0, 3),
                    'observations': random.randint(0, 2),
                    'positive_findings': random.randint(0, 2),
                    'followup_required': random.choice([True, False]),
                    'followup_date': (current_date + timedelta(days=30)).strftime('%Y-%m-%d') if random.random() > 0.5 else (current_date + timedelta(days=15)).strftime('%Y-%m-%d'),  # Now always set
                    'audit_status': random.choice(['completed', 'in_progress']),
                    'audit_report_url': f"https://docs.company.com/audits/audit-{audit_counter:06d}.pdf",  # Now always set
                    'closed_date': (current_date + timedelta(days=7)).strftime('%Y-%m-%d'),  # Now always set
                    'created_at': current_date.strftime('%Y-%m-%d %H:%M:%S'),
                    'updated_at': current_date.strftime('%Y-%m-%d %H:%M:%S')
                }
                self.data['quality_audits'].append(audit)
                audit_counter += 1
            
            current_date += timedelta(days=1)
        
        print(f"Generated {len(self.data['quality_audits'])} quality audits")
    
    def generate_audit_findings(self):
        """Generate audit findings"""
        print("Generating audit findings...")
        finding_counter = 1
        
        for audit in self.data['quality_audits']:
            for idx in range(random.randint(0, audit['total_findings'])):
                # 85% of findings are closed
                is_closed = random.random() < 0.85
                finding_status = 'closed' if is_closed else random.choice(['open', 'in_progress'])
                
                finding = {
                    'finding_id': f"FIND-{finding_counter:06d}",
                    'audit_id': audit['audit_id'],
                    'finding_number': idx + 1,
                    'finding_type': random.choice(['major_nc', 'minor_nc', 'observation']),
                    'finding_category': random.choice(['documentation', 'process', 'equipment']),
                    'finding_description': f"Finding: {random.choice(['Document issue', 'Process issue', 'Equipment issue'])}",
                    'requirement_reference': f"ISO clause {random.randint(4, 10)}",
                    'objective_evidence': 'Evidence documented',
                    'impact_assessment': 'Impact assessed',
                    'risk_level': random.choice(['low', 'medium', 'high']),
                    'corrective_action_required': random.choice([True, False]),
                    'responsible_person': random.choice([e.get('employee_id', 'EMP-000001') for e in self.employees] + ['EMP-000001']),
                    'target_closure_date': (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d'),
                    'finding_status': finding_status,
                    'closure_date': (datetime.now() + timedelta(days=15+idx*5)).strftime('%Y-%m-%d') if is_closed else None,
                    'closure_verified_by': random.choice([e.get('employee_id', 'EMP-000001') for e in self.employees if e.get('role') == 'manager'] + ['EMP-000001']) if is_closed else random.choice([e.get('employee_id', 'EMP-000001') for e in self.employees if e.get('role') == 'manager'] + ['EMP-000001']),
                    'closure_notes': f"Closure note for finding {idx+1}" if is_closed else f"In progress on finding {idx+1}",
                    'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                self.data['audit_findings'].append(finding)
                finding_counter += 1
        
        print(f"Generated {len(self.data['audit_findings'])} audit findings")
    
    def generate_ncr_headers(self, start_date, days):
        """Generate NCR headers"""
        print("Generating NCR headers...")
        current_date = start_date
        ncr_counter = 1
        
        # Build lookup maps from PO/SO lines
        po_lines_by_material = {}
        so_lines_by_material = {}
        supplier_by_po = {}
        customer_by_so = {}
        
        if hasattr(self, 'purchase_order_lines'):
            for pol in self.purchase_order_lines:
                mat_id = pol.get('material_id')
                if mat_id and mat_id not in po_lines_by_material:
                    po_lines_by_material[mat_id] = []
                if mat_id:
                    po_lines_by_material[mat_id].append(pol)
        
        if hasattr(self, 'sales_order_lines'):
            for sol in self.sales_order_lines:
                mat_id = sol.get('material_id')
                if mat_id and mat_id not in so_lines_by_material:
                    so_lines_by_material[mat_id] = []
                if mat_id:
                    so_lines_by_material[mat_id].append(sol)
        
        # Map PO/SO headers
        if hasattr(self, 'purchase_orders'):
            for po in self.purchase_orders:
                supplier_by_po[po['purchase_order_id']] = po.get('supplier_id')
        
        if hasattr(self, 'sales_orders'):
            for so in self.sales_orders:
                customer_by_so[so['sales_order_id']] = so.get('customer_id')
        
        for day in range(days):
            if random.random() < 0.75:  # Increased from 0.25 to 0.75 (75% probability)
                source_type = random.choice(['incoming_inspection', 'in_process', 'final_inspection'])
                
                # Link to source document based on source_type
                source_document_id = None
                supplier_id = None
                purchase_order_id = None
                customer_id = None
                sales_order_id = None
                material_id = None
                lot_number = None
                serial_numbers = None
                
                if source_type == 'incoming_inspection' and po_lines_by_material:
                    # Pick a material from PO lines
                    material_id = random.choice(list(po_lines_by_material.keys()))
                    pol = random.choice(po_lines_by_material[material_id])
                    purchase_order_id = pol.get('purchase_order_id')
                    source_document_id = purchase_order_id
                    supplier_id = supplier_by_po.get(purchase_order_id)
                    lot_number = f"LOT-{random.randint(10000, 99999)}"
                elif source_type == 'final_inspection' and so_lines_by_material:
                    # Pick a material from SO lines
                    material_id = random.choice(list(so_lines_by_material.keys()))
                    sol = random.choice(so_lines_by_material[material_id])
                    sales_order_id = sol.get('sales_order_id')
                    source_document_id = sales_order_id
                    customer_id = customer_by_so.get(sales_order_id)
                    lot_number = f"LOT-{random.randint(10000, 99999)}"
                else:
                    # Fallback to any product - but also try to link SO/PO if available
                    material_id = random.choice([p.get('product_id', f'PRD-{random.randint(1, 100):06d}') for p in self.products] + ['PRD-000001'])
                    lot_number = f"LOT-{random.randint(10000, 99999)}"
                    # Still try to link SO/PO for non-specific source types (60% for SO, 40% for PO)
                    if so_lines_by_material and random.random() < 0.60:
                        material_id = random.choice(list(so_lines_by_material.keys()))
                        sol = random.choice(so_lines_by_material[material_id])
                        sales_order_id = sol.get('sales_order_id')
                        customer_id = customer_by_so.get(sales_order_id)
                    elif po_lines_by_material and random.random() < 0.40:
                        material_id = random.choice(list(po_lines_by_material.keys()))
                        pol = random.choice(po_lines_by_material[material_id])
                        purchase_order_id = pol.get('purchase_order_id')
                        supplier_id = supplier_by_po.get(purchase_order_id)
                
                # 75% of NCRs are closed/verified
                is_closed = random.random() < 0.75
                
                ncr = {
                    'ncr_id': f"NCR-{ncr_counter:06d}",
                    'ncr_number': f"NCR-{current_date.strftime('%Y%m')}-{ncr_counter:04d}",
                    'source_type': source_type,
                    'source_document_id': source_document_id,
                    'detected_date': current_date.strftime('%Y-%m-%d'),
                    'detected_by': random.choice([e.get('employee_id', 'EMP-000001') for e in self.employees] + ['EMP-000001']),
                    'detection_location': random.choice([f.get('factory_id', 'FAC-000001') for f in self.factories] + ['FAC-000001']),
                    'material_id': material_id,
                    'product_id': material_id,
                    'batch_number': f"BATCH-{current_date.strftime('%Y%m%d')}-{random.randint(100, 999)}",
                    'lot_number': lot_number,
                    'serial_numbers': f"SN-{random.randint(100000, 999999)}" if random.random() < 0.6 else None,
                    'quantity_inspected': round(random.uniform(100, 1000), 2),
                    'quantity_defective': round(random.uniform(1, 100), 2),
                    'unit_of_measure': 'PCS',
                    'defect_type': random.choice(['dimensional', 'visual', 'functional']),
                    'defect_description': f"Defect in {random.choice(['dimension', 'surface'])}",
                    'defect_severity': random.choice(['critical', 'major', 'minor']),
                    'supplier_id': supplier_id if supplier_id else random.choice([s.get('supplier_id', f'SUP-{random.randint(1001, 2000):06d}') for s in self.suppliers] + [f'SUP-{random.randint(1001, 2000):06d}']),
                    'purchase_order_id': purchase_order_id,
                    'customer_id': customer_id if customer_id else f'CUST-{random.randint(1, 99):05d}',
                    'sales_order_id': sales_order_id,
                    'containment_action': 'Containment action implemented',
                    'containment_completed': True,
                    'containment_date': (current_date + timedelta(hours=4)).strftime('%Y-%m-%d'),
                    'disposition': random.choice(['scrap', 'rework', 'use_as_is']),
                    'disposition_quantity': round(random.uniform(1, 50), 2),
                    'disposition_notes': 'Disposition set',
                    'scrap_cost': round(random.uniform(100, 5000), 2) if random.random() > 0.5 else 0,
                    'rework_cost': round(random.uniform(500, 10000), 2) if random.random() > 0.5 else 0,
                    'sorting_cost': round(random.uniform(100, 5000), 2) if random.random() > 0.5 else 0,
                    'total_cost': round(random.uniform(1000, 20000), 2),
                    'root_cause_method': random.choice(['5_why', 'fishbone']),
                    'root_cause_description': 'Root cause analysis completed',
                    'root_cause_verified': is_closed,
                    'ncr_status': 'closed' if is_closed else random.choice(['open', 'contained']),
                    'closed_date': (current_date + timedelta(days=random.randint(5, 20))).strftime('%Y-%m-%d') if is_closed else None,  # Now populated
                    'closed_by': random.choice([e.get('employee_id', 'EMP-000001') for e in self.employees if e.get('role') in ['manager', 'supervisor']] + ['EMP-000001']) if is_closed else random.choice([e.get('employee_id', 'EMP-000001') for e in self.employees if e.get('role') in ['manager', 'supervisor']] + ['EMP-000001']),  # Now populated
                    'verified_effective': is_closed,
                    'verification_date': (current_date + timedelta(days=random.randint(15, 30))).strftime('%Y-%m-%d') if is_closed else None,  # Now populated
                    'verified_by': random.choice([e.get('employee_id', 'EMP-000001') for e in self.employees if e.get('role') in ['manager', 'supervisor']] + ['EMP-000001']) if is_closed else random.choice([e.get('employee_id', 'EMP-000001') for e in self.employees if e.get('role') in ['manager', 'supervisor']] + ['EMP-000001']),  # Now populated
                    'priority': random.choice(['low', 'medium', 'high']),
                    'attachment_urls': [f"https://docs.company.com/ncr-{ncr_counter:06d}.pdf", f"https://docs.company.com/ncr-{ncr_counter:06d}-evidence.pdf"] if random.random() < 0.7 else [f"https://docs.company.com/ncr-{ncr_counter:06d}.pdf"],  # Array format
                    'created_at': current_date.strftime('%Y-%m-%d %H:%M:%S'),
                    'updated_at': current_date.strftime('%Y-%m-%d %H:%M:%S')
                }
                self.data['ncr_headers'].append(ncr)
                ncr_counter += 1
            
            current_date += timedelta(days=1)
        
        print(f"Generated {len(self.data['ncr_headers'])} NCR headers")
    
    def generate_ncr_defect_details(self):
        """Generate NCR defect details"""
        print("Generating NCR defect details...")
        
        for ncr in self.data['ncr_headers']:
            for i in range(random.randint(1, 3)):
                detail = {
                    'defect_detail_id': f"DEFDET-{ncr['ncr_id']}-{i}",
                    'ncr_id': ncr['ncr_id'],
                    'characteristic_name': f"Characteristic {i}",
                    'specification': f"Spec: {random.uniform(50, 100):.2f}",
                    'actual_value': f"Actual: {random.uniform(45, 105):.2f}",
                    'measurement_method': random.choice(['Caliper', 'Gauge', 'Visual']),
                    'measuring_equipment': f"Equipment-{random.randint(1, 20)}",
                    'defect_location': f"Location {random.randint(1, 10)}",
                    'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                self.data['ncr_defect_details'].append(detail)
        
        print(f"Generated {len(self.data['ncr_defect_details'])} NCR defect details")
    
    def generate_capa_headers(self, start_date, days):
        """Generate CAPA headers"""
        print("Generating CAPA headers...")
        current_date = start_date
        capa_counter = 1
        
        for day in range(0, days, 7):
            if len(self.data['ncr_headers']) > 0:
                source_ncr = random.choice(self.data['ncr_headers'])
                
                # 70% of CAPAs are completed/verified (improve from previous 40%)
                is_completed = random.random() < 0.70
                completion_date = (current_date + timedelta(days=day+15)).strftime('%Y-%m-%d') if is_completed else None
                verification_date = (current_date + timedelta(days=day+25)).strftime('%Y-%m-%d') if is_completed else None
                verification_person = random.choice([e.get('employee_id', 'EMP-000001') for e in self.employees if e.get('role') in ['manager', 'supervisor']] + ['EMP-000001']) if is_completed else random.choice([e.get('employee_id', 'EMP-000001') for e in self.employees if e.get('role') in ['manager', 'supervisor']] + ['EMP-000001'])
                effectiveness_date = (current_date + timedelta(days=day+40)).strftime('%Y-%m-%d') if is_completed else (current_date + timedelta(days=day+30)).strftime('%Y-%m-%d')
                closed_date = (current_date + timedelta(days=day+45)).strftime('%Y-%m-%d') if is_completed else None
                closed_person = random.choice([e.get('employee_id', 'EMP-000001') for e in self.employees if e.get('role') == 'manager'] + ['EMP-000001']) if is_completed else random.choice([e.get('employee_id', 'EMP-000001') for e in self.employees if e.get('role') == 'manager'] + ['EMP-000001'])
                
                capa = {
                    'capa_id': f"CAPA-{capa_counter:06d}",
                    'capa_number': f"CAPA-{(current_date + timedelta(days=day)).strftime('%Y%m')}-{capa_counter:04d}",
                    'action_type': random.choice(['corrective', 'preventive']),
                    'initiated_from': 'ncr',
                    'source_document_id': source_ncr['ncr_id'],
                    'problem_description': f"Problem: {source_ncr['defect_description']}",
                    'problem_severity': source_ncr['defect_severity'],
                    'immediate_actions': 'Containment completed',
                    'immediate_actions_completed': True,
                    'root_cause_analysis': 'Root cause identified',
                    'root_cause_method': 'fishbone',
                    'root_cause_identified': True,
                    'actions_planned': 'Corrective actions planned',
                    'implementation_plan': 'Implementation in progress',
                    'responsible_person': random.choice([e.get('employee_id', 'EMP-000001') for e in self.employees] + ['EMP-000001']),
                    'responsible_department': random.choice(['Production', 'Quality']),
                    'target_completion_date': (current_date + timedelta(days=day+30)).strftime('%Y-%m-%d'),
                    'actual_completion_date': completion_date,  # Now always set if completed
                    'verification_plan': 'Verification to be done',
                    'verification_completed': is_completed,
                    'verification_date': verification_date,  # Now always set
                    'verified_by': verification_person,  # Now always set
                    'verification_result': random.choice(['passed', 'failed']) if is_completed else None,
                    'effectiveness_review_date': effectiveness_date,  # Now always set
                    'effectiveness_verified': is_completed,
                    'effectiveness_notes': 'CAPA is effective' if is_completed else 'Under review',  # Now always set
                    'capa_status': 'closed' if is_completed else random.choice(['open', 'in_progress']),
                    'closed_date': closed_date,  # Now always set
                    'closed_by': closed_person,  # Now always set
                    'implementation_cost': round(random.uniform(1000, 50000), 2),
                    'created_at': (current_date + timedelta(days=day)).strftime('%Y-%m-%d %H:%M:%S'),
                    'updated_at': (current_date + timedelta(days=day)).strftime('%Y-%m-%d %H:%M:%S')
                }
                self.data['capa_headers'].append(capa)
                capa_counter += 1
        
        print(f"Generated {len(self.data['capa_headers'])} CAPA headers")
    
    def generate_capa_actions(self):
        """Generate CAPA actions"""
        print("Generating CAPA actions...")
        action_counter = 1
        
        for capa in self.data['capa_headers']:
            # Actions more likely to be completed if CAPA is closed
            is_capa_completed = capa.get('capa_status') == 'closed'
            num_actions = random.randint(2, 4)
            
            for seq in range(1, num_actions + 1):
                # 80% of actions are completed if CAPA is closed, 30% otherwise
                is_completed = random.random() < (0.80 if is_capa_completed else 0.30)
                
                action = {
                    'action_id': f"CAPAACT-{action_counter:06d}",
                    'capa_id': capa['capa_id'],
                    'action_sequence': seq,
                    'action_description': f"Corrective action {seq} for {capa['problem_description'][:50]}",
                    'assigned_to': random.choice([e.get('employee_id', 'EMP-000001') for e in self.employees] + ['EMP-000001']),
                    'target_completion_date': (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d'),
                    'due_date': (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d'),
                    'actual_completion_date': (datetime.now() + timedelta(days=15+seq*5)).strftime('%Y-%m-%d') if is_completed else None,
                    'action_status': 'completed' if is_completed else random.choice(['assigned', 'in_progress']),
                    'effectiveness_check_date': (datetime.now() + timedelta(days=25+seq*5)).strftime('%Y-%m-%d') if is_completed else None,
                    'is_effective': random.choice([True, False]) if is_completed else None,
                    'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'updated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                self.data['capa_actions'].append(action)
                action_counter += 1
        
        print(f"Generated {len(self.data['capa_actions'])} CAPA actions")
    
    def generate_control_plans(self):
        """Generate control plans"""
        print("Generating control plans...")
        
        for i, product in enumerate(self.products):
            plan = {
                'control_plan_id': f"CTRLPLAN-{i+1:06d}",
                'control_plan_number': f"CP-{product.get('product_code', f'PRD{i+1}')}",
                'control_plan_title': f"Control Plan {i+1}",
                'version': '1',
                'product_id': product.get('product_id'),
                'material_id': product.get('product_id'),
                'process_name': f"Process {i+1}",
                'plan_status': 'active',
                'control_plan_type': 'SPC',
                'prepared_by': 'QA-001',
                'approved_by': 'QM-001',
                'approval_date': (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'),
                'effective_date': (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'),
                'revision_date': (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'),
                'document_url': f'https://docs.company.com/cp-{i+1:06d}.pdf',
                'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'updated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            self.data['control_plans'].append(plan)
        
        print(f"Generated {len(self.data['control_plans'])} control plans")
    
    def generate_control_plan_characteristics(self):
        """Generate control plan characteristics"""
        print("Generating control plan characteristics...")
        char_counter = 1
        
        for plan in self.data['control_plans']:
            for i in range(random.randint(2, 4)):
                char = {
                    'characteristic_id': f"CTRLCHAR-{char_counter:06d}",
                    'control_plan_id': plan['control_plan_id'],
                    'characteristic_sequence': i,
                    'characteristic_name': f"Characteristic {i}",
                    'characteristic_description': f"Quality characteristic",
                    'process_step': f"Step {i}",
                    'specification': f"Spec: {random.uniform(70, 90):.2f} ± {random.uniform(1, 5):.2f}",
                    'specification_lower': round(random.uniform(40, 60), 2),
                    'specification_upper': round(random.uniform(80, 100), 2),
                    'unit_of_measure': 'mm',
                    'measurement_method': 'Caliper',
                    'measurement_equipment': f"Equipment {random.randint(1, 20)}",
                    'sampling_size': random.randint(5, 30),
                    'sampling_frequency': 'per batch',
                    'control_limits_lower': round(random.uniform(42, 62), 2),
                    'control_limits_upper': round(random.uniform(78, 98), 2),
                    'reaction_plan': 'Investigate',
                    'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                self.data['control_plan_characteristics'].append(char)
                char_counter += 1
        
        print(f"Generated {len(self.data['control_plan_characteristics'])} control plan characteristics")
    
    def generate_supplier_quality_metrics(self):
        """Generate supplier quality metrics for historical periods (3 months)"""
        print("Generating supplier quality metrics...")
        
        # Generate metrics for last 3 months to ensure historical data
        current_date = self.enterprise_date
        month_offset = 3
        
        for month_back in range(month_offset):
            metric_date = current_date - timedelta(days=30 * month_back)
            metric_period = metric_date.strftime('%Y-%m')
            
            for i in range(1, 20):
                metric = {
                    'metric_id': f"SUPM-{metric_period.replace('-', '')}-{i:03d}",
                    'supplier_id': f"SUP-{i:05d}",
                    'metric_period': metric_period,  # UNIQUE constraint key
                    'total_receipts': random.randint(10, 100),
                    'receipts_inspected': random.randint(5, 100),
                    'receipts_accepted': random.randint(4, 95),
                    'receipts_rejected': random.randint(0, 10),
                    'total_quantity_received': round(random.uniform(1000, 100000), 2),
                    'quantity_accepted': round(random.uniform(900, 95000), 2),
                    'quantity_rejected': round(random.uniform(0, 10000), 2),
                    'total_defects': random.randint(0, 100),
                    'defect_ppm': random.randint(0, 5000),
                    'critical_defects': random.randint(0, 5),
                    'major_defects': random.randint(0, 30),
                    'minor_defects': random.randint(0, 50),
                    'acceptance_rate_pct': round(random.uniform(85, 99.9), 2),
                    'quality_score': round(random.uniform(80, 100), 2),
                    'ncr_count': random.randint(0, 5),
                    'capa_count': random.randint(0, 3),
                    'capa_effectiveness_pct': round(random.uniform(80, 100), 2),
                    'rejection_cost': round(random.uniform(0, 50000), 2),
                    'rework_cost': round(random.uniform(0, 30000), 2),
                    'created_at': metric_date.strftime('%Y-%m-%d %H:%M:%S'),
                    'updated_at': metric_date.strftime('%Y-%m-%d %H:%M:%S')
                }
                self.data['supplier_quality_metrics'].append(metric)
        
        print(f"Generated {len(self.data['supplier_quality_metrics'])} supplier quality metrics")
    
    def generate_measuring_equipment(self):
        """Generate measuring equipment records"""
        print("Generating measuring equipment...")
        
        equipment_types = ['Caliper', 'Micrometer', 'Gauge', 'Scale', 'Hardness Tester', 'Analyzer']
        for i in range(30):
            equip = {
                'equipment_id': f"MEAS-{i+1:06d}",
                'equipment_number': f"EQ-{i+1:05d}",
                'equipment_name': f"{equipment_types[i % len(equipment_types)]} #{i+1}",
                'equipment_type': equipment_types[i % len(equipment_types)],
                'model_number': f"MODEL-{random.randint(100000, 999999)}",
                'serial_number': f"SN-{random.randint(100000, 999999)}",
                'manufacturer': random.choice(['Precision Corp', 'Global Tools']),
                'purchase_date': (datetime.now() - timedelta(days=random.randint(365, 1825))).strftime('%Y-%m-%d'),
                'calibration_frequency_days': random.choice([90, 180, 365]),
                'last_calibration_date': (datetime.now() - timedelta(days=random.randint(1, 89))).strftime('%Y-%m-%d'),
                'next_calibration_due': (datetime.now() + timedelta(days=random.randint(1, 90))).strftime('%Y-%m-%d'),
                'calibration_method': random.choice(['Block Gauge', 'Master Gauge', 'Standard']),
                'calibration_standard': 'NIST',
                'measurement_range': f'{random.randint(1, 100)}-{random.randint(101, 200)} mm',
                'resolution': f'{random.choice([0.01, 0.05, 0.1])} mm',
                'accuracy': f'±{random.choice([0.01, 0.05, 0.1])} mm',
                'location': random.choice([f.get('factory_id', 'FAC-001') for f in self.factories] + ['FAC-001']),
                'equipment_status': 'active',
                'responsible_person': random.choice([e.get('employee_id', 'EMP-000001') for e in self.employees] + ['EMP-000001']),
                'locked_out': False,
                'purchase_cost': round(random.uniform(500, 5000), 2),
                'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'updated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            self.data['measuring_equipment'].append(equip)
        
        print(f"Generated {len(self.data['measuring_equipment'])} measuring equipment records")
    
    def generate_calibration_records(self, start_date, days):
        """Generate calibration records"""
        print("Generating calibration records...")
        current_date = start_date
        cal_counter = 1
        
        for equipment in self.data['measuring_equipment']:
            for month in range(days // 30):
                cal_date = current_date + timedelta(days=month*30)
                record = {
                    'calibration_id': f"CAL-{cal_counter:06d}",
                    'calibration_number': f"CAL-{cal_date.strftime('%Y%m')}-{cal_counter:04d}",
                    'equipment_id': equipment['equipment_id'],
                    'calibration_date': cal_date.strftime('%Y-%m-%d'),
                    'next_due_date': (cal_date + timedelta(days=90)).strftime('%Y-%m-%d'),
                    'calibrated_by': random.choice([e.get('employee_id', 'EMP-000001') for e in self.employees] + ['EMP-000001']),
                    'calibration_result': random.choice(['pass', 'fail', 'adjusted_and_pass']),
                    'as_found_condition': f"{random.uniform(95, 105):.2f}",
                    'as_left_condition': f"{random.uniform(98, 102):.2f}",
                    'certificate_number': f"CERT-{cal_counter:07d}",
                    'certificate_url': f"https://docs.company.com/certs/cert-{cal_counter:07d}.pdf",
                    'standard_equipment': 'NIST',
                    'standard_traceability': 'NIST',
                    'calibration_cost': round(random.uniform(500, 5000), 2),
                    'notes': f"Calibration completed",
                    'created_at': cal_date.strftime('%Y-%m-%d %H:%M:%S'),
                    'updated_at': cal_date.strftime('%Y-%m-%d %H:%M:%S')
                }
                self.data['calibration_records'].append(record)
                cal_counter += 1
        
        print(f"Generated {len(self.data['calibration_records'])} calibration records")
    
    def generate_calibration_alerts(self):
        """Generate calibration alerts"""
        print("Generating calibration alerts...")
        alert_counter = 1
        
        for equipment in self.data['measuring_equipment']:
            if random.random() > 0.6:
                alert = {
                    'alert_id': f"ALERT-{alert_counter:06d}",
                    'equipment_id': equipment['equipment_id'],
                    'alert_type': random.choice(['calibration_due', 'overdue']),
                    'alert_date': datetime.now().strftime('%Y-%m-%d'),
                    'due_date': equipment['next_calibration_due'],
                    'resolved_date': None,
                    'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                self.data['calibration_alerts'].append(alert)
                alert_counter += 1
        
        print(f"Generated {len(self.data['calibration_alerts'])} calibration alerts")
    
    def generate_spc_control_charts(self):
        """Generate SPC control charts"""
        print("Generating SPC control charts...")
        
        for i, plan in enumerate(self.data['control_plans']):
            chart = {
                'chart_id': f"SPC-{i+1:06d}",
                'chart_number': f"CHART-{i+1:05d}",
                'control_plan_id': plan['control_plan_id'],
                'product_id': plan['product_id'],
                'process_name': f"Process {i+1}",
                'chart_type': random.choice(['X-bar', 'R']),
                'characteristic_name': f"Characteristic {i+1}",
                'lower_control_limit': round(random.uniform(40, 50), 2),
                'center_line': round(random.uniform(70, 80), 2),
                'upper_control_limit': round(random.uniform(90, 100), 2),
                'sampling_interval': 'daily',
                'sample_size': random.randint(5, 30),
                'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'updated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            self.data['spc_control_charts'].append(chart)
        
        print(f"Generated {len(self.data['spc_control_charts'])} SPC control charts")
    
    def generate_spc_data_points(self):
        """Generate SPC data points"""
        print("Generating SPC data points...")
        point_counter = 1
        
        for chart in self.data['spc_control_charts']:
            for i in range(random.randint(20, 50)):
                sample_date = datetime.now() - timedelta(days=random.randint(1, 30))
                point = {
                    'data_point_id': f"SPCPT-{point_counter:06d}",
                    'chart_id': chart['chart_id'],
                    'data_point_sequence': i + 1,
                    'sample_date': sample_date.strftime('%Y-%m-%d'),
                    'measurement_timestamp': sample_date.strftime('%Y-%m-%d %H:%M:%S'),
                    'measured_value': round(random.uniform(chart['lower_control_limit'], chart['upper_control_limit']), 2),
                    'measurement_value': round(random.uniform(chart['lower_control_limit'], chart['upper_control_limit']), 2),
                    'sample_size': chart['sample_size'],
                    'subgroup_average': round(random.uniform(chart['center_line']-5, chart['center_line']+5), 2),
                    'subgroup_range': round(random.uniform(5, 15), 2),
                    'notes': None,
                    'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                self.data['spc_data_points'].append(point)
                point_counter += 1
        
        print(f"Generated {len(self.data['spc_data_points'])} SPC data points")
    
    def generate_ppap_submissions(self, start_date, days):
        """Generate PPAP submissions"""
        print("Generating PPAP submissions...")
        current_date = start_date
        ppap_counter = 1
        
        for i in range(min(10, len(self.products))):
            # Generate more PPAP submissions (was only 50% chance)
            ppap = {
                'ppap_id': f"PPAP-{ppap_counter:06d}",
                'ppap_number': f"PPAP-{ppap_counter:06d}",
                'part_name': self.products[i].get('product_name', f'Part {i+1}'),
                'part_number': self.products[i].get('product_code', f'PART-{i+1}'),
                'product_id': self.products[i].get('product_id'),
                'supplier_id': random.choice([s.get('supplier_id', f'SUP-{random.randint(1, 99):05d}') for s in self.suppliers] + ['SUP-000001']),
                'customer_id': f'CUST-{random.randint(1, 99):05d}',
                'material_id': self.products[i].get('product_id'),
                'ppap_level': random.choice([1, 2, 3]),
                'ppap_status': random.choice(['in_preparation', 'submitted', 'approved']),
                'submission_date': current_date.strftime('%Y-%m-%d'),
                'approval_date': (current_date + timedelta(days=random.randint(5, 30))).strftime('%Y-%m-%d') if random.random() < 0.7 else None,  # Only if likely to be approved
                'approval_expiry_date': (current_date + timedelta(days=random.randint(180, 730))).strftime('%Y-%m-%d') if random.random() < 0.7 else None,
                'approved_by': random.choice([e.get('employee_id', 'EMP-000001') for e in self.employees if e.get('role') in ['manager', 'supervisor']] + ['EMP-000001']) if random.random() < 0.7 else None,
                'submission_reason': random.choice(['Initial Release', 'Engineering Change', 'Supplier Change', 'Specification Change']),
                'design_records': random.choice([True, False]),
                'dimensional_results': random.choice([True, False]),
                'material_test_results': random.choice([True, False]),
                'initial_process_study': random.choice([True, False]),
                'msa_study': random.choice([True, False]),
                'dfmea_completed': random.choice([True, False]),
                'pfmea_completed': random.choice([True, False]),
                'control_plan': random.choice([True, False]),
                'appearance_approval': random.choice([True, False]),
                'sample_products': random.choice([True, False]),
                'master_sample': random.choice([True, False]),
                'checking_aids': random.choice([True, False]),
                'qualified_lab_docs': random.choice([True, False]),
                'engineering_change_docs': random.choice([True, False]),
                'psw_signed': random.choice([True, False]),
                'psw_signed_by': random.choice([e.get('employee_id', 'EMP-000001') for e in self.employees] + ['EMP-000001']),  # Now always set
                'psw_signed_date': (current_date - timedelta(days=random.randint(1, 30))).strftime('%Y-%m-%d'),  # Now always set
                'submission_package_url': f'https://docs.company.com/ppap-{ppap_counter:06d}.pdf',
                'review_date': (current_date + timedelta(days=random.randint(10, 40))).strftime('%Y-%m-%d'),  # Now always set
                'reviewed_by': random.choice([e.get('employee_id', 'EMP-000001') for e in self.employees if e.get('role') in ['manager', 'supervisor']] + ['EMP-000001']),  # Now always set
                'review_comments': f'Reviewed PPAP submission #{ppap_counter}: Approved with comments',  # Now always set
                'created_at': current_date.strftime('%Y-%m-%d %H:%M:%S'),
                'updated_at': current_date.strftime('%Y-%m-%d %H:%M:%S')
            }
            self.data['ppap_submissions'].append(ppap)
            ppap_counter += 1
        
        print(f"Generated {len(self.data['ppap_submissions'])} PPAP submissions")
    
    def generate_quality_documents(self):
        """Generate quality documents"""
        print("Generating quality documents...")
        doc_types = ['Procedure', 'Work Instruction', 'Form', 'Report', 'Control Plan']
        
        for i in range(20):
            doc = {
                'document_id': f"DOC-{i+1:06d}",
                'document_number': f"QMS-DOC-{i+1:04d}",
                'document_type': random.choice(doc_types),
                'version': i % 5,
                'document_title': f"Document {i+1}",
                'document_description': f"Quality document",
                'current_revision': f"Rev. {i % 5}",
                'current_revision_date': (datetime.now() - timedelta(days=random.randint(1, 365))).strftime('%Y-%m-%d'),
                'revision_date': (datetime.now() - timedelta(days=random.randint(1, 180))).strftime('%Y-%m-%d'),
                'document_owner': random.choice([e.get('employee_id', 'EMP-000001') for e in self.employees] + ['EMP-000001']),
                'approval_status': random.choice(['draft', 'approved']),
                'effective_date': (datetime.now() - timedelta(days=random.randint(1, 180))).strftime('%Y-%m-%d'),
                'obsolete_date': None,
                'document_url': f"https://docs.company.com/qms/doc-{i+1:06d}.pdf",
                'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'updated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            self.data['quality_documents'].append(doc)
        
        print(f"Generated {len(self.data['quality_documents'])} quality documents")
    
    def generate_quality_kpis(self, start_date, days):
        """Generate quality KPIs"""
        print("Generating quality KPIs...")
        current_date = start_date
        
        for day in range(days):
            kpi = {
                'kpi_id': f"KPI-{current_date.strftime('%Y%m%d')}",
                'kpi_date': current_date.strftime('%Y-%m-%d'),
                'kpi_type': random.choice(['defect_rate', 'yield']),
                'kpi_name': f"Quality Metric",
                'kpi_value': round(random.uniform(80, 99.9), 2),
                'kpi_target': 95.0,
                'kpi_unit': '%',
                'kpi_status': 'on_track',
                'created_at': current_date.strftime('%Y-%m-%d %H:%M:%S'),
                'updated_at': current_date.strftime('%Y-%m-%d %H:%M:%S')
            }
            self.data['quality_kpis'].append(kpi)
            current_date += timedelta(days=1)
        
        print(f"Generated {len(self.data['quality_kpis'])} quality KPIs")
    
    def generate_document_revisions(self):
        """Generate document revisions"""
        print("Generating document revisions...")
        rev_counter = 1
        
        for doc in self.data['quality_documents']:
            for rev_num in range(1, random.randint(2, 4)):
                # 85% of revisions are approved
                is_approved = random.random() < 0.85
                approval_date = (datetime.now() - timedelta(days=random.randint(1, 200))).strftime('%Y-%m-%d') if is_approved else None
                
                revision = {
                    'revision_id': f"REV-{rev_counter:06d}",
                    'document_id': doc['document_id'],
                    'revision_number': rev_num,
                    'revision_date': (datetime.now() - timedelta(days=random.randint(1, 365))).strftime('%Y-%m-%d'),
                    'revised_by': random.choice([e.get('employee_id', 'EMP-000001') for e in self.employees] + ['EMP-000001']),
                    'change_description': f"Update to section {random.randint(1, 10)}",
                    'changes_summary': f"Revision {rev_num} updates document content",
                    'approval_status': 'approved' if is_approved else random.choice(['pending', 'in_review']),
                    'approved_by': random.choice([e.get('employee_id', 'EMP-000001') for e in self.employees if e.get('role') in ['manager', 'supervisor']] + ['EMP-000001']) if is_approved else random.choice([e.get('employee_id', 'EMP-000001') for e in self.employees if e.get('role') in ['manager', 'supervisor']] + ['EMP-000001']),  # Now always set
                    'approval_date': approval_date,  # Now always set
                    'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                self.data['document_revisions'].append(revision)
                rev_counter += 1
        
        print(f"Generated {len(self.data['document_revisions'])} document revisions")
    
    def generate_eight_d_reports(self):
        """Generate 8D reports"""
        print("Generating 8D reports...")
        
        for i in range(min(5, len(self.data['ncr_headers']))):
            ncr = self.data['ncr_headers'][i]
            
            # Build team members list (80% of reports have it) - as array of employee IDs
            team_members = None
            if random.random() < 0.8 and self.employees:
                team_size = random.randint(3, 8)
                team = random.sample(self.employees, min(team_size, len(self.employees)))
                team_members = [member.get('employee_id', f'EMP-{i:06d}') for member in team]
            
            report = {
                'eight_d_id': f"8D-{i+1:06d}",
                'eight_d_number': f"8D-{i+1:06d}",
                'team_leader': random.choice([e.get('employee_id', 'EMP-000001') for e in self.employees] + ['EMP-000001']),
                'problem_description': ncr['defect_description'],
                'problem_preparation': 'Problem statement prepared',
                'is_statement': 'Clear IS statement',
                'is_not_statement': 'Clear IS NOT statement',
                'team_established_date': (datetime.now() - timedelta(days=random.randint(1, 30))).strftime('%Y-%m-%d'),
                'team_members': team_members,
                'containment_date': (datetime.now() - timedelta(days=random.randint(1, 20))).strftime('%Y-%m-%d'),
                'containment_action': 'Immediate containment action taken',
                'containment_verified': random.choice([True, False]),
                'root_cause_analysis': 'Root cause analysis completed',
                'root_cause_identified': (datetime.now() - timedelta(days=random.randint(1, 15))).strftime('%Y-%m-%d'),
                'root_cause_method': random.choice(['5 Why', 'Fishbone', 'FMEA', 'Fault Tree']),
                'root_cause_verified': random.choice([True, False]),
                'preventive_actions': 'Preventive actions defined',
                'permanent_actions': 'Permanent corrective actions implemented',
                'pca_implementation_date': (datetime.now() - timedelta(days=random.randint(1, 10))).strftime('%Y-%m-%d'),
                'prevention_completed': random.choice([True, False]),
                'verification_plan': 'Verification plan established',
                'verification_date': (datetime.now() - timedelta(days=random.randint(1, 5))).strftime('%Y-%m-%d'),
                'verification_completed': random.choice([True, False]),
                'lessons_learned': 'Lessons learned documented',
                'systems_updated': 'Systems and documentation updated',
                'team_recognition': 'Team recognized for efforts',
                'eight_d_status': random.choice(['open', 'in_review', 'closed']),
                'source_type': 'NCR',
                'source_document_id': ncr['ncr_id'],
                'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'updated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            self.data['eight_d_reports'].append(report)
        
        print(f"Generated {len(self.data['eight_d_reports'])} 8D reports")
    
    def generate_qms_integration_log(self, start_date, days):
        """Generate QMS integration logs"""
        print("Generating QMS integration logs...")
        current_date = start_date
        log_counter = 1
        
        for day in range(0, days, 3):
            for sync_type in ['audit_sync', 'ncr_sync', 'metrics_sync']:
                log = {
                    'integration_log_id': f"QMSLOG-{log_counter:06d}",
                    'sync_timestamp': (current_date + timedelta(days=day)).strftime('%Y-%m-%d %H:%M:%S'),
                    'integration_type': sync_type,
                    'sync_type': sync_type,
                    'source_system': 'QMS',
                    'target_system': random.choice(['ERP', 'CRM']),
                    'records_synced': random.randint(10, 100),
                    'sync_status': 'completed',
                    'error_message': None,
                    'created_at': (current_date + timedelta(days=day)).strftime('%Y-%m-%d %H:%M:%S')
                }
                self.data['qms_integration_log'].append(log)
                log_counter += 1
        
        print(f"Generated {len(self.data['qms_integration_log'])} QMS integration logs")
    
    def save_to_json(self, output_file='genims_qms_data.json'):
        """Save data to JSON file"""
        print(f"\nSaving to {output_file}...")
        with open(output_file, 'w') as f:
            json.dump(self.data, f, indent=2)
        print(f"QMS data saved to {output_file}")
    
    def get_summary(self):
        """Return data summary"""
        return {table: len(records) for table, records in self.data.items() if records}

if __name__ == '__main__':
    generator = QMSDataGenerator()
    generator.generate(days=90)
    
    output_file = Path(__file__).parent / 'genims_qms_data.json'
    generator.save_to_json(str(output_file))
    
    summary = generator.get_summary()
    print("\n" + "="*60)
    print("QMS DATA GENERATION SUMMARY")
    print("="*60)
    total_records = 0
    for table_name, count in sorted(summary.items()):
        if count > 0:
            print(f"{table_name:40s}: {count:6d} records")
            total_records += count
    print("-"*60)
    print(f"{'TOTAL':40s}: {total_records:6d} records")
    print("="*60)
