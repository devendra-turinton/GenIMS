"""
GenIMS MES Historical Data Generator
Generates 30 days of production execution data
"""

import random
import json
from datetime import datetime, timedelta, time
from typing import List, Dict, Tuple
import string

# ============================================================================
# CONFIGURATION
# ============================================================================

DAYS_OF_HISTORY = 30
WORK_ORDERS_PER_DAY = (15, 30)  # Min/max work orders per day
OPERATIONS_PER_ORDER = (2, 5)  # Routing steps
MATERIALS_PER_ORDER = (3, 8)  # BOM items
INSPECTIONS_PER_ORDER = (1, 3)  # Quality checkpoints
LABOR_ENTRIES_PER_DAY = (300, 600)  # Time entries
DOWNTIME_EVENTS_PER_DAY = (15, 30)
CHANGEOVERS_PER_DAY = (5, 10)

# Quality rates
FIRST_PASS_YIELD_RANGE = (92, 99.5)  # %
INSPECTION_PASS_RATE = 0.95  # 95% pass
DEFECT_RATE = 0.03  # 3% of orders have defects

# Material codes for auto parts manufacturing
RAW_MATERIALS = [
    'RM-STEEL-SHEET', 'RM-STEEL-ROD', 'RM-ALUMINUM-BAR', 'RM-COPPER-WIRE',
    'RM-RUBBER-COMPOUND', 'RM-PLASTIC-PELLET', 'RM-PAINT-BASE', 'RM-LUBRICANT'
]

COMPONENTS = [
    'COMP-BOLT-M8', 'COMP-NUT-M8', 'COMP-WASHER-8MM', 'COMP-SPRING-20N',
    'COMP-BEARING-6205', 'COMP-SEAL-RUBBER', 'COMP-GASKET-FIBER', 'COMP-O-RING-10MM'
]

CONSUMABLES = [
    'CONS-CUTTING-FLUID', 'CONS-GRINDING-WHEEL', 'CONS-WELDING-ROD',
    'CONS-CLEANING-SOLVENT', 'CONS-PACKAGING-TAPE', 'CONS-LABEL-BARCODE'
]


class MESDataGenerator:
    def __init__(self, master_data_file='genims_master_data.json'):
        """Initialize with master data"""
        print("Loading master data...")
        with open(master_data_file, 'r') as f:
            self.master_data = json.load(f)
        
        self.factories = self.master_data['factories']
        self.lines = self.master_data['production_lines']
        self.machines = self.master_data['machines']
        self.employees = self.master_data['employees']
        self.shifts = self.master_data['shifts']
        self.products = self.master_data['products']
        self.customers = self.master_data['customers']
        self.line_product_mapping = self.master_data['line_product_mapping']
        
        # MES data storage
        self.work_orders = []
        self.work_order_operations = []
        self.material_transactions = []
        self.quality_inspections = []
        self.defects = []
        self.labor_transactions = []
        self.downtime_events = []
        self.changeover_events = []
        self.electronic_batch_records = []
        self.production_schedule = []
        
        # Counters
        self.wo_counter = 1
        self.op_counter = 1
        self.mat_counter = 1
        self.insp_counter = 1
        self.defect_counter = 1
        self.labor_counter = 1
        self.downtime_counter = 1
        self.changeover_counter = 1
        self.ebr_counter = 1
        self.schedule_counter = 1
        
        print(f"Loaded: {len(self.products)} products, {len(self.lines)} lines, {len(self.employees)} employees")
    
    def generate_id(self, prefix: str, counter: int) -> str:
        """Generate unique ID"""
        return f"{prefix}-{str(counter).zfill(6)}"
    
    def random_date(self, start: datetime, end: datetime) -> datetime:
        """Generate random datetime between start and end"""
        delta = end - start
        random_seconds = random.randint(0, int(delta.total_seconds()))
        return start + timedelta(seconds=random_seconds)
    
    def get_shift_for_time(self, factory_id: str, dt: datetime) -> Dict:
        """Get shift for given time"""
        hour = dt.hour
        day_of_week = dt.strftime('%a').lower()
        
        factory_shifts = [s for s in self.shifts if s['factory_id'] == factory_id]
        
        for shift in factory_shifts:
            days = shift['days_of_week'].split(',')
            if day_of_week in days:
                start_hour = int(shift['start_time'].split(':')[0])
                end_hour = int(shift['end_time'].split(':')[0])
                
                if start_hour <= end_hour:
                    if start_hour <= hour < end_hour:
                        return shift
                else:  # Crosses midnight
                    if hour >= start_hour or hour < end_hour:
                        return shift
        
        # Default to general shift
        return next((s for s in factory_shifts if s['shift_code'] == 'G'), factory_shifts[0])
    
    def get_operators_for_shift(self, line_id: str, shift_name: str) -> List[Dict]:
        """Get operators for line and shift"""
        return [e for e in self.employees 
                if e['line_id'] == line_id 
                and e['shift'] == shift_name 
                and e['role'] == 'operator']
    
    def generate_work_orders(self, start_date: datetime, days: int):
        """Generate work orders for the period"""
        print(f"\nGenerating work orders for {days} days...")
        
        current_date = start_date
        
        for day in range(days):
            num_orders = random.randint(*WORK_ORDERS_PER_DAY)
            
            for _ in range(num_orders):
                # Select random line-product mapping
                mapping = random.choice(self.line_product_mapping)
                line_id = mapping['line_id']
                product_id = mapping['product_id']
                factory_id = mapping['factory_id']
                
                # Get product and line details
                product = next(p for p in self.products if p['product_id'] == product_id)
                line = next(l for l in self.lines if l['line_id'] == line_id)
                
                # Customer (80% customer orders, 20% stock)
                customer_id = random.choice(self.customers)['customer_id'] if random.random() < 0.8 else None
                
                # Quantities
                planned_qty = random.randint(50, 500)
                
                # Timing - start during day shift
                start_hour = random.randint(6, 14)
                planned_start = current_date.replace(hour=start_hour, minute=random.randint(0, 59))
                
                # Duration based on quantity and cycle time
                cycle_time = product['standard_cycle_time_seconds']
                estimated_minutes = (planned_qty * cycle_time) / 60
                setup_time = random.randint(30, 90)
                total_minutes = int(estimated_minutes + setup_time)
                
                planned_end = planned_start + timedelta(minutes=total_minutes)
                
                # Execution status (past orders are mostly completed)
                days_from_now = (datetime.now() - current_date).days
                if days_from_now > 2:
                    # Old orders - mostly completed
                    status = random.choices(
                        ['completed', 'closed', 'cancelled'],
                        weights=[0.85, 0.10, 0.05]
                    )[0]
                elif days_from_now > 0:
                    # Recent orders - mix
                    status = random.choices(
                        ['completed', 'in_progress', 'on_hold'],
                        weights=[0.60, 0.30, 0.10]
                    )[0]
                else:
                    # Future/today - scheduled or in progress
                    status = random.choices(
                        ['scheduled', 'in_progress', 'released'],
                        weights=[0.50, 0.30, 0.20]
                    )[0]
                
                # Actual times based on status
                if status in ['completed', 'closed']:
                    actual_start = planned_start + timedelta(minutes=random.randint(-15, 30))
                    actual_end = actual_start + timedelta(minutes=int(total_minutes * random.uniform(0.95, 1.15)))
                    
                    # Actual quantities
                    produced_qty = int(planned_qty * random.uniform(0.95, 1.05))
                    
                    # Quality
                    fpy = random.uniform(*FIRST_PASS_YIELD_RANGE) / 100
                    good_qty = int(produced_qty * fpy)
                    rejected_qty = int((produced_qty - good_qty) * 0.7)
                    scrapped_qty = int((produced_qty - good_qty) * 0.2)
                    rework_qty = produced_qty - good_qty - rejected_qty - scrapped_qty
                    
                    yield_pct = (good_qty / produced_qty * 100) if produced_qty > 0 else 0
                    fpyield_pct = fpy * 100
                    
                    actual_cycle_time = int(((actual_end - actual_start).total_seconds()) / produced_qty) if produced_qty > 0 else cycle_time
                    run_time = int((actual_end - actual_start).total_seconds() / 60) - setup_time
                    downtime = random.randint(0, int(total_minutes * 0.1))
                    
                elif status == 'in_progress':
                    actual_start = planned_start
                    actual_end = None
                    produced_qty = int(planned_qty * random.uniform(0.3, 0.7))
                    good_qty = int(produced_qty * random.uniform(0.95, 0.98))
                    rejected_qty = produced_qty - good_qty
                    scrapped_qty = 0
                    rework_qty = 0
                    yield_pct = None
                    fpyield_pct = None
                    actual_cycle_time = None
                    run_time = None
                    downtime = 0
                    
                else:  # scheduled, released, cancelled
                    actual_start = None
                    actual_end = None
                    produced_qty = 0
                    good_qty = 0
                    rejected_qty = 0
                    scrapped_qty = 0
                    rework_qty = 0
                    yield_pct = None
                    fpyield_pct = None
                    actual_cycle_time = None
                    run_time = None
                    downtime = 0
                
                # Batch/lot numbers
                batch_number = f"BATCH-{current_date.strftime('%Y%m%d')}-{self.wo_counter:04d}"
                lot_number = f"LOT-{factory_id[-3:]}-{self.wo_counter:05d}"
                
                # Create work order
                work_order = {
                    'work_order_id': self.generate_id('WO', self.wo_counter),
                    'work_order_number': f"WO-{current_date.strftime('%Y%m%d')}-{self.wo_counter:04d}",
                    'product_id': product_id,
                    'customer_id': customer_id,
                    'sales_order_number': f"SO-{random.randint(10000, 99999)}" if customer_id else None,
                    'factory_id': factory_id,
                    'line_id': line_id,
                    'planned_quantity': planned_qty,
                    'unit_of_measure': 'EA',
                    'priority': random.randint(1, 10),
                    'planned_start_date': planned_start.strftime('%Y-%m-%d %H:%M:%S'),
                    'planned_end_date': planned_end.strftime('%Y-%m-%d %H:%M:%S'),
                    'scheduled_start_time': planned_start.strftime('%Y-%m-%d %H:%M:%S'),
                    'scheduled_end_time': planned_end.strftime('%Y-%m-%d %H:%M:%S'),
                    'actual_start_time': actual_start.strftime('%Y-%m-%d %H:%M:%S') if actual_start else None,
                    'actual_end_time': actual_end.strftime('%Y-%m-%d %H:%M:%S') if actual_end else None,
                    'produced_quantity': produced_qty,
                    'good_quantity': good_qty,
                    'rejected_quantity': rejected_qty,
                    'scrapped_quantity': scrapped_qty,
                    'rework_quantity': rework_qty,
                    'status': status,
                    'quality_status': 'approved' if status == 'completed' else 'pending',
                    'quality_hold': False,
                    'planned_cycle_time_seconds': cycle_time,
                    'actual_cycle_time_seconds': actual_cycle_time,
                    'setup_time_minutes': setup_time,
                    'run_time_minutes': run_time,
                    'downtime_minutes': downtime,
                    'yield_percentage': round(yield_pct, 2) if yield_pct else None,
                    'first_pass_yield_percentage': round(fpyield_pct, 2) if fpyield_pct else None,
                    'standard_cost_per_unit': round(random.uniform(10, 100), 2),
                    'actual_cost_per_unit': round(random.uniform(10, 100), 2) if status == 'completed' else None,
                    'total_material_cost': round(random.uniform(1000, 10000), 2) if status == 'completed' else None,
                    'total_labor_cost': round(random.uniform(500, 5000), 2) if status == 'completed' else None,
                    'total_overhead_cost': round(random.uniform(200, 2000), 2) if status == 'completed' else None,
                    'batch_number': batch_number,
                    'lot_number': lot_number,
                    'expiry_date': (current_date + timedelta(days=365)).strftime('%Y-%m-%d'),
                    'electronic_batch_record_id': None,  # Will link later
                    'requires_validation': False,
                    'validation_status': None,
                    'parent_work_order_id': None,
                    'erp_order_id': f"ERP-{random.randint(100000, 999999)}",
                    'created_by': random.choice([e['employee_id'] for e in self.employees if e['role'] in ['supervisor', 'manager']]),
                    'created_at': (current_date - timedelta(days=1)).strftime('%Y-%m-%d %H:%M:%S'),
                    'updated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'completed_by': random.choice([e['employee_id'] for e in self.employees if e['role'] == 'supervisor']) if status == 'completed' else None,
                    'closed_at': actual_end.strftime('%Y-%m-%d %H:%M:%S') if status == 'closed' and actual_end else None
                }
                
                self.work_orders.append(work_order)
                
                # Generate related data
                if status in ['in_progress', 'completed', 'closed']:
                    self._generate_operations(work_order, product)
                    self._generate_material_transactions(work_order, product)
                    self._generate_quality_inspections(work_order)
                    
                    if random.random() < DEFECT_RATE:
                        self._generate_defects(work_order)
                    
                    self._generate_labor_transactions(work_order)
                
                # Generate schedule entry
                self._generate_schedule_entry(work_order)
                
                # Generate eBR for completed orders (50% of time)
                if status in ['completed', 'closed'] and random.random() < 0.5:
                    self._generate_ebr(work_order, product)
                
                self.wo_counter += 1
            
            current_date += timedelta(days=1)
            
            if day % 5 == 0:
                print(f"  Day {day+1}/{days}: Generated {len(self.work_orders)} work orders...")
        
        print(f"Generated {len(self.work_orders)} work orders")
    
    def _generate_operations(self, work_order: Dict, product: Dict):
        """Generate operations for work order"""
        num_operations = random.randint(*OPERATIONS_PER_ORDER)
        
        operation_types = {
            'suspension': ['machining', 'assembly', 'testing', 'packaging'],
            'brake': ['machining', 'assembly', 'testing', 'packaging'],
            'electrical': ['wire_cutting', 'crimping', 'assembly', 'testing'],
            'steering': ['machining', 'assembly', 'testing', 'packaging'],
            'transmission': ['machining', 'heat_treatment', 'assembly', 'testing']
        }
        
        ops = operation_types.get(product['product_category'], ['machining', 'assembly', 'testing'])
        selected_ops = random.sample(ops, min(num_operations, len(ops)))
        
        for seq, op_name in enumerate(selected_ops, 1):
            # Get machine for this line
            line_machines = [m for m in self.machines if m['line_id'] == work_order['line_id']]
            machine = random.choice(line_machines) if line_machines else None
            
            # Get operator
            shift = self.get_shift_for_time(work_order['factory_id'], datetime.strptime(work_order['actual_start_time'], '%Y-%m-%d %H:%M:%S'))
            operators = self.get_operators_for_shift(work_order['line_id'], shift['shift_name'])
            operator = random.choice(operators) if operators else None
            
            # Timing
            if work_order['actual_start_time']:
                op_start = datetime.strptime(work_order['actual_start_time'], '%Y-%m-%d %H:%M:%S') + timedelta(minutes=seq * 30)
                op_duration = random.randint(30, 120)
                op_end = op_start + timedelta(minutes=op_duration) if work_order['status'] == 'completed' else None
            else:
                op_start = None
                op_end = None
                op_duration = None
            
            operation = {
                'operation_id': self.generate_id('OP', self.op_counter),
                'work_order_id': work_order['work_order_id'],
                'operation_sequence': seq,
                'operation_code': f"OP-{seq:02d}",
                'operation_name': op_name.replace('_', ' ').title(),
                'line_id': work_order['line_id'],
                'machine_id': machine['machine_id'] if machine else None,
                'work_center_code': f"WC-{work_order['line_id'][-3:]}",
                'planned_quantity': work_order['planned_quantity'],
                'planned_duration_minutes': random.randint(30, 120),
                'planned_setup_time_minutes': random.randint(10, 30),
                'standard_time_per_unit_seconds': round(random.uniform(30, 180), 2),
                'planned_start_time': None,
                'planned_end_time': None,
                'actual_start_time': op_start.strftime('%Y-%m-%d %H:%M:%S') if op_start else None,
                'actual_end_time': op_end.strftime('%Y-%m-%d %H:%M:%S') if op_end else None,
                'completed_quantity': work_order['produced_quantity'] if work_order['status'] == 'completed' else 0,
                'rejected_quantity': work_order['rejected_quantity'] if work_order['status'] == 'completed' else 0,
                'actual_duration_minutes': op_duration,
                'actual_setup_time_minutes': random.randint(10, 30) if op_start else None,
                'status': 'completed' if work_order['status'] == 'completed' else 'in_progress',
                'operator_id': operator['employee_id'] if operator else None,
                'shift_id': shift['shift_id'],
                'labor_hours': round(op_duration / 60, 2) if op_duration else None,
                'requires_inspection': seq == len(selected_ops),  # Final operation requires inspection
                'inspection_status': 'passed' if work_order['status'] == 'completed' else 'pending',
                'inspection_timestamp': op_end.strftime('%Y-%m-%d %H:%M:%S') if op_end else None,
                'inspector_id': None,
                'efficiency_percentage': round(random.uniform(85, 105), 2) if work_order['status'] == 'completed' else None,
                'scrap_rate_percentage': round(random.uniform(0.5, 5), 2) if work_order['status'] == 'completed' else None,
                'work_instructions': f"Standard work instructions for {op_name}",
                'safety_notes': "Wear PPE. Follow lockout/tagout procedures.",
                'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'updated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            self.work_order_operations.append(operation)
            self.op_counter += 1
    
    def _generate_material_transactions(self, work_order: Dict, product: Dict):
        """Generate material transactions"""
        num_materials = random.randint(*MATERIALS_PER_ORDER)
        
        # Mix of material types
        materials = []
        materials.extend(random.sample(RAW_MATERIALS, min(2, len(RAW_MATERIALS))))
        materials.extend(random.sample(COMPONENTS, min(num_materials - 2, len(COMPONENTS))))
        
        if random.random() < 0.3:
            materials.append(random.choice(CONSUMABLES))
        
        for material_code in materials[:num_materials]:
            # Determine material type
            if material_code in RAW_MATERIALS:
                mat_type = 'raw_material'
                mat_name = material_code.replace('RM-', '').replace('-', ' ').title()
            elif material_code in COMPONENTS:
                mat_type = 'component'
                mat_name = material_code.replace('COMP-', '').replace('-', ' ').title()
            else:
                mat_type = 'consumable'
                mat_name = material_code.replace('CONS-', '').replace('-', ' ').title()
            
            # Quantity
            if mat_type == 'raw_material':
                quantity = round(random.uniform(10, 100), 2)
                unit = 'KG'
            elif mat_type == 'component':
                quantity = work_order['planned_quantity'] * random.randint(1, 4)
                unit = 'EA'
            else:
                quantity = round(random.uniform(1, 10), 2)
                unit = 'L'
            
            # Transaction date
            trans_date = datetime.strptime(work_order['actual_start_time'], '%Y-%m-%d %H:%M:%S') if work_order['actual_start_time'] else datetime.now()
            
            transaction = {
                'transaction_id': self.generate_id('MAT', self.mat_counter),
                'transaction_type': 'issue',
                'transaction_date': trans_date.strftime('%Y-%m-%d %H:%M:%S'),
                'work_order_id': work_order['work_order_id'],
                'operation_id': None,
                'material_code': material_code,
                'material_name': mat_name,
                'material_type': mat_type,
                'quantity': quantity,
                'unit_of_measure': unit,
                'lot_number': f"MAT-LOT-{random.randint(10000, 99999)}",
                'batch_number': f"MAT-BATCH-{random.randint(1000, 9999)}",
                'serial_number': None,
                'expiry_date': (trans_date + timedelta(days=180)).strftime('%Y-%m-%d'),
                'supplier_lot_number': f"SUP-{random.randint(10000, 99999)}",
                'from_location': 'WAREHOUSE-A',
                'to_location': f"LINE-{work_order['line_id'][-3:]}",
                'warehouse_location': f"BIN-{random.choice(['A', 'B', 'C'])}-{random.randint(1, 50):02d}",
                'unit_cost': round(random.uniform(1, 50), 4),
                'total_cost': round(quantity * random.uniform(1, 50), 2),
                'quality_status': 'approved',
                'inspection_required': mat_type == 'raw_material',
                'certificate_of_analysis': f"COA-{random.randint(10000, 99999)}" if mat_type == 'raw_material' else None,
                'parent_lot_number': None,
                'consumed_by_lot_number': work_order['lot_number'],
                'performed_by': random.choice([e['employee_id'] for e in self.employees if e['role'] == 'operator']),
                'requires_documentation': mat_type == 'raw_material',
                'documentation_complete': True,
                'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            self.material_transactions.append(transaction)
            self.mat_counter += 1
    
    def _generate_quality_inspections(self, work_order: Dict):
        """Generate quality inspections"""
        num_inspections = random.randint(*INSPECTIONS_PER_ORDER)
        
        inspection_types = ['in_process', 'final']
        
        for i in range(num_inspections):
            insp_type = inspection_types[min(i, len(inspection_types)-1)]
            
            # Inspector
            inspectors = [e for e in self.employees if e['role'] == 'quality_inspector']
            inspector = random.choice(inspectors) if inspectors else random.choice(self.employees)
            
            # Timing
            if work_order['actual_start_time']:
                insp_date = datetime.strptime(work_order['actual_start_time'], '%Y-%m-%d %H:%M:%S') + timedelta(hours=i+1)
            else:
                continue
            
            # Results
            inspection_passed = random.random() < INSPECTION_PASS_RATE
            
            if inspection_passed:
                result = 'pass'
                disposition = 'accept'
                defects = 0
                critical = 0
                major = 0
                minor = 0
            else:
                result = random.choice(['fail', 'conditional_pass', 'rework_required'])
                disposition = random.choice(['reject', 'rework', 'use_as_is'])
                defects = random.randint(1, 5)
                critical = random.randint(0, 1)
                major = random.randint(0, 2)
                minor = defects - critical - major
            
            inspection = {
                'inspection_id': self.generate_id('INSP', self.insp_counter),
                'inspection_type': insp_type,
                'inspection_date': insp_date.strftime('%Y-%m-%d %H:%M:%S'),
                'work_order_id': work_order['work_order_id'],
                'operation_id': None,
                'product_id': work_order['product_id'],
                'sample_size': random.randint(5, 20),
                'lot_number': work_order['lot_number'],
                'batch_number': work_order['batch_number'],
                'serial_number': None,
                'inspector_id': inspector['employee_id'],
                'shift_id': self.get_shift_for_time(work_order['factory_id'], insp_date)['shift_id'],
                'inspection_result': result,
                'defects_found': defects,
                'critical_defects': critical,
                'major_defects': major,
                'minor_defects': minor,
                'measured_values': None,
                'specification_values': None,
                'disposition': disposition,
                'disposition_reason': 'Quality standards met' if inspection_passed else 'Dimensional non-conformance',
                'disposition_by': inspector['employee_id'],
                'ncr_number': f"NCR-{random.randint(1000, 9999)}" if not inspection_passed else None,
                'corrective_action_required': not inspection_passed,
                'inspection_plan_id': f"IP-{random.randint(100, 999)}",
                'inspection_checklist_id': f"CL-{random.randint(100, 999)}",
                'photos_attached': random.random() < 0.2,
                'approved_by': None,
                'approved_at': None,
                'notes': 'Standard inspection completed' if inspection_passed else 'Issues found - see NCR',
                'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            self.quality_inspections.append(inspection)
            self.insp_counter += 1
    
    def _generate_defects(self, work_order: Dict):
        """Generate defect records"""
        defect_categories = ['dimensional', 'visual', 'functional', 'material', 'assembly']
        defect_severities = ['critical', 'major', 'minor']
        
        num_defects = random.randint(1, 3)
        
        for _ in range(num_defects):
            defect_time = datetime.strptime(work_order['actual_start_time'], '%Y-%m-%d %H:%M:%S') + timedelta(hours=random.randint(1, 4))
            
            defect = {
                'defect_id': self.generate_id('DEF', self.defect_counter),
                'defect_code': f"D-{random.randint(100, 999)}",
                'defect_category': random.choice(defect_categories),
                'defect_description': 'Component out of specification tolerance',
                'defect_severity': random.choice(defect_severities),
                'detected_date': defect_time.strftime('%Y-%m-%d %H:%M:%S'),
                'work_order_id': work_order['work_order_id'],
                'operation_id': None,
                'inspection_id': None,
                'product_id': work_order['product_id'],
                'lot_number': work_order['lot_number'],
                'quantity_affected': random.randint(1, 10),
                'detected_by': random.choice([e['employee_id'] for e in self.employees if e['role'] in ['operator', 'quality_inspector']]),
                'detection_method': random.choice(['visual', 'measurement', 'testing']),
                'root_cause_category': random.choice(['material', 'machine', 'method', 'man', 'measurement', 'environment']),
                'root_cause_description': 'Root cause analysis in progress',
                'root_cause_analysis_complete': False,
                'corrective_action': 'Adjust process parameters',
                'preventive_action': 'Implement additional checks',
                'action_owner': random.choice([e['employee_id'] for e in self.employees if e['role'] in ['supervisor', 'engineer']]),
                'action_due_date': (defect_time + timedelta(days=7)).strftime('%Y-%m-%d'),
                'action_completed': False,
                'scrap_cost': round(random.uniform(100, 1000), 2),
                'rework_cost': round(random.uniform(50, 500), 2),
                'total_cost': round(random.uniform(150, 1500), 2),
                'status': 'open',
                'closed_date': None,
                'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'updated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            self.defects.append(defect)
            self.defect_counter += 1
    
    def _generate_labor_transactions(self, work_order: Dict):
        """Generate labor time entries"""
        if not work_order['actual_start_time']:
            return
        
        start_time = datetime.strptime(work_order['actual_start_time'], '%Y-%m-%d %H:%M:%S')
        
        # Get operators for this line/shift
        shift = self.get_shift_for_time(work_order['factory_id'], start_time)
        operators = self.get_operators_for_shift(work_order['line_id'], shift['shift_name'])
        
        if not operators:
            return
        
        # 2-4 operators per work order
        num_operators = min(random.randint(2, 4), len(operators))
        selected_operators = random.sample(operators, num_operators)
        
        for operator in selected_operators:
            clock_in = start_time + timedelta(minutes=random.randint(-10, 10))
            duration = random.randint(120, 480)  # 2-8 hours
            clock_out = clock_in + timedelta(minutes=duration)
            
            labor = {
                'labor_transaction_id': self.generate_id('LAB', self.labor_counter),
                'transaction_date': clock_in.strftime('%Y-%m-%d %H:%M:%S'),
                'employee_id': operator['employee_id'],
                'shift_id': shift['shift_id'],
                'work_order_id': work_order['work_order_id'],
                'operation_id': None,
                'activity_code': 'DIRECT',
                'activity_type': 'direct_labor',
                'clock_in_time': clock_in.strftime('%Y-%m-%d %H:%M:%S'),
                'clock_out_time': clock_out.strftime('%Y-%m-%d %H:%M:%S') if work_order['status'] == 'completed' else None,
                'duration_minutes': duration if work_order['status'] == 'completed' else None,
                'break_time_minutes': 30,
                'quantity_produced': int(work_order['produced_quantity'] / num_operators) if work_order['status'] == 'completed' else None,
                'quantity_rejected': int(work_order['rejected_quantity'] / num_operators) if work_order['status'] == 'completed' else None,
                'standard_hours': round(duration / 60, 2),
                'actual_hours': round(duration / 60, 2) if work_order['status'] == 'completed' else None,
                'efficiency_percentage': round(random.uniform(85, 110), 2) if work_order['status'] == 'completed' else None,
                'hourly_rate': round(random.uniform(15, 35), 2),
                'labor_cost': round((duration / 60) * random.uniform(15, 35), 2) if work_order['status'] == 'completed' else None,
                'overtime_hours': 0,
                'overtime_cost': 0,
                'approved': work_order['status'] == 'completed',
                'approved_by': None,
                'approved_at': None,
                'notes': None,
                'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            self.labor_transactions.append(labor)
            self.labor_counter += 1
    
    def _generate_schedule_entry(self, work_order: Dict):
        """Generate production schedule entry"""
        schedule = {
            'schedule_id': self.generate_id('SCH', self.schedule_counter),
            'schedule_date': datetime.strptime(work_order['planned_start_date'], '%Y-%m-%d %H:%M:%S').strftime('%Y-%m-%d'),
            'schedule_week': datetime.strptime(work_order['planned_start_date'], '%Y-%m-%d %H:%M:%S').isocalendar()[1],
            'shift_id': self.get_shift_for_time(work_order['factory_id'], datetime.strptime(work_order['planned_start_date'], '%Y-%m-%d %H:%M:%S'))['shift_id'],
            'line_id': work_order['line_id'],
            'factory_id': work_order['factory_id'],
            'work_order_id': work_order['work_order_id'],
            'operation_id': None,
            'sequence_number': self.schedule_counter,
            'planned_start_time': work_order['planned_start_date'],
            'planned_end_time': work_order['planned_end_date'],
            'planned_quantity': work_order['planned_quantity'],
            'priority': work_order['priority'],
            'customer_due_date': None,
            'material_available': True,
            'operator_available': True,
            'equipment_available': True,
            'schedule_status': work_order['status'] if work_order['status'] in ['planned', 'confirmed', 'in_progress', 'completed', 'delayed', 'cancelled'] else 'planned',
            'actual_start_time': work_order['actual_start_time'],
            'actual_end_time': work_order['actual_end_time'],
            'actual_quantity': work_order['produced_quantity'] if work_order['status'] == 'completed' else None,
            'on_time_start': random.random() < 0.85 if work_order['actual_start_time'] else None,
            'on_time_completion': random.random() < 0.80 if work_order['status'] == 'completed' else None,
            'schedule_adherence_percentage': round(random.uniform(75, 100), 2) if work_order['status'] == 'completed' else None,
            'planner_id': random.choice([e['employee_id'] for e in self.employees if e['role'] in ['manager', 'planning_coordinator']]),
            'planning_notes': None,
            'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'updated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        self.production_schedule.append(schedule)
        self.schedule_counter += 1
    
    def _generate_ebr(self, work_order: Dict, product: Dict):
        """Generate electronic batch record"""
        ebr = {
            'ebr_id': self.generate_id('EBR', self.ebr_counter),
            'batch_number': work_order['batch_number'],
            'product_id': work_order['product_id'],
            'work_order_id': work_order['work_order_id'],
            'batch_size': work_order['produced_quantity'],
            'formula_id': f"FORM-{random.randint(100, 999)}",
            'formula_version': f"v{random.randint(1, 5)}.{random.randint(0, 9)}",
            'manufacturing_date': datetime.strptime(work_order['actual_start_time'], '%Y-%m-%d %H:%M:%S').strftime('%Y-%m-%d'),
            'expiration_date': work_order['expiry_date'],
            'retest_date': (datetime.strptime(work_order['expiry_date'], '%Y-%m-%d') - timedelta(days=30)).strftime('%Y-%m-%d'),
            'factory_id': work_order['factory_id'],
            'manufacturing_area': f"AREA-{work_order['line_id'][-3:]}",
            'record_status': 'approved',
            'prepared_by': random.choice([e['employee_id'] for e in self.employees if e['role'] in ['operator', 'supervisor']]),
            'prepared_at': work_order['actual_end_time'],
            'reviewed_by': random.choice([e['employee_id'] for e in self.employees if e['role'] == 'supervisor']),
            'reviewed_at': (datetime.strptime(work_order['actual_end_time'], '%Y-%m-%d %H:%M:%S') + timedelta(hours=2)).strftime('%Y-%m-%d %H:%M:%S'),
            'approved_by': random.choice([e['employee_id'] for e in self.employees if e['role'] == 'manager']),
            'approved_at': (datetime.strptime(work_order['actual_end_time'], '%Y-%m-%d %H:%M:%S') + timedelta(hours=4)).strftime('%Y-%m-%d %H:%M:%S'),
            'release_status': 'released',
            'released_by': random.choice([e['employee_id'] for e in self.employees if e['role'] == 'manager']),
            'released_at': (datetime.strptime(work_order['actual_end_time'], '%Y-%m-%d %H:%M:%S') + timedelta(hours=6)).strftime('%Y-%m-%d %H:%M:%S'),
            'has_deviations': False,
            'deviation_count': 0,
            'temperature_min_c': round(random.uniform(18, 22), 2),
            'temperature_max_c': round(random.uniform(24, 28), 2),
            'humidity_min_percentage': round(random.uniform(40, 50), 2),
            'humidity_max_percentage': round(random.uniform(55, 65), 2),
            'regulatory_requirement': 'IATF 16949',
            'audit_trail': None,
            'electronic_signature_applied': True,
            'signature_metadata': None,
            'notes': 'Batch completed successfully',
            'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'updated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        # Link eBR back to work order
        work_order['electronic_batch_record_id'] = ebr['ebr_id']
        
        self.electronic_batch_records.append(ebr)
        self.ebr_counter += 1
    
    def generate_all_data(self):
        """Generate all MES historical data"""
        start_date = datetime.now() - timedelta(days=DAYS_OF_HISTORY)
        
        print(f"\n{'='*80}")
        print(f"Generating {DAYS_OF_HISTORY} days of MES historical data")
        print(f"Start: {start_date.strftime('%Y-%m-%d')}")
        print(f"End: {datetime.now().strftime('%Y-%m-%d')}")
        print(f"{'='*80}\n")
        
        # Generate work orders and related data
        self.generate_work_orders(start_date, DAYS_OF_HISTORY)
        
        print(f"\n{'='*80}")
        print("Data Generation Complete!")
        print(f"{'='*80}")
        self._print_summary()
    
    def _print_summary(self):
        """Print generation summary"""
        print(f"\nMES Data Summary:")
        print(f"  Work Orders: {len(self.work_orders):,}")
        print(f"  Operations: {len(self.work_order_operations):,}")
        print(f"  Material Transactions: {len(self.material_transactions):,}")
        print(f"  Quality Inspections: {len(self.quality_inspections):,}")
        print(f"  Defects: {len(self.defects):,}")
        print(f"  Labor Transactions: {len(self.labor_transactions):,}")
        print(f"  Production Schedule: {len(self.production_schedule):,}")
        print(f"  Electronic Batch Records: {len(self.electronic_batch_records):,}")
        
        # Status breakdown
        status_counts = {}
        for wo in self.work_orders:
            status = wo['status']
            status_counts[status] = status_counts.get(status, 0) + 1
        
        print(f"\n  Work Order Status:")
        for status, count in sorted(status_counts.items()):
            print(f"    {status}: {count}")
    
    def to_sql_inserts(self, output_file='mes_historical_data_inserts.sql'):
        """Generate SQL INSERT statements"""
        print(f"\nGenerating SQL INSERT statements to {output_file}...")
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("-- GenIMS MES Historical Data INSERT Statements\n")
            f.write("-- Generated: " + datetime.now().strftime('%Y-%m-%d %H:%M:%S') + "\n\n")
            
            # Helper function
            def format_value(v):
                if v is None:
                    return "NULL"
                elif isinstance(v, bool):
                    return str(v).lower()
                elif isinstance(v, (int, float)):
                    return str(v)
                else:
                    escaped = str(v).replace("'", "''")
                    return f"'{escaped}'".replace('\n', ' ')
            
            # Work Orders
            f.write("-- WORK ORDERS\n")
            for wo in self.work_orders:
                cols = ", ".join(wo.keys())
                vals = ", ".join([format_value(v) for v in wo.values()])
                f.write(f"INSERT INTO work_orders ({cols}) VALUES ({vals});\n")
            f.write(f"\n-- Total: {len(self.work_orders)} work orders\n\n")
            
            # Operations
            f.write("-- WORK ORDER OPERATIONS\n")
            for op in self.work_order_operations:
                cols = ", ".join(op.keys())
                vals = ", ".join([format_value(v) for v in op.values()])
                f.write(f"INSERT INTO work_order_operations ({cols}) VALUES ({vals});\n")
            f.write(f"\n-- Total: {len(self.work_order_operations)} operations\n\n")
            
            # Material Transactions
            f.write("-- MATERIAL TRANSACTIONS\n")
            for mat in self.material_transactions:
                cols = ", ".join(mat.keys())
                vals = ", ".join([format_value(v) for v in mat.values()])
                f.write(f"INSERT INTO material_transactions ({cols}) VALUES ({vals});\n")
            f.write(f"\n-- Total: {len(self.material_transactions)} material transactions\n\n")
            
            # Quality Inspections
            f.write("-- QUALITY INSPECTIONS\n")
            for insp in self.quality_inspections:
                cols = ", ".join(insp.keys())
                vals = ", ".join([format_value(v) for v in insp.values()])
                f.write(f"INSERT INTO quality_inspections ({cols}) VALUES ({vals});\n")
            f.write(f"\n-- Total: {len(self.quality_inspections)} inspections\n\n")
            
            # Defects
            f.write("-- DEFECTS\n")
            for defect in self.defects:
                cols = ", ".join(defect.keys())
                vals = ", ".join([format_value(v) for v in defect.values()])
                f.write(f"INSERT INTO defects ({cols}) VALUES ({vals});\n")
            f.write(f"\n-- Total: {len(self.defects)} defects\n\n")
            
            # Labor Transactions
            f.write("-- LABOR TRANSACTIONS\n")
            for labor in self.labor_transactions:
                cols = ", ".join(labor.keys())
                vals = ", ".join([format_value(v) for v in labor.values()])
                f.write(f"INSERT INTO labor_transactions ({cols}) VALUES ({vals});\n")
            f.write(f"\n-- Total: {len(self.labor_transactions)} labor entries\n\n")
            
            # Production Schedule
            f.write("-- PRODUCTION SCHEDULE\n")
            for sched in self.production_schedule:
                cols = ", ".join(sched.keys())
                vals = ", ".join([format_value(v) for v in sched.values()])
                f.write(f"INSERT INTO production_schedule ({cols}) VALUES ({vals});\n")
            f.write(f"\n-- Total: {len(self.production_schedule)} schedule entries\n\n")
            
            # Electronic Batch Records
            f.write("-- ELECTRONIC BATCH RECORDS\n")
            for ebr in self.electronic_batch_records:
                cols = ", ".join(ebr.keys())
                vals = ", ".join([format_value(v) for v in ebr.values()])
                f.write(f"INSERT INTO electronic_batch_records ({cols}) VALUES ({vals});\n")
            f.write(f"\n-- Total: {len(self.electronic_batch_records)} eBRs\n\n")
        
        print(f"SQL INSERT statements written to {output_file}")
    
    def to_json(self, output_file='mes_historical_data.json'):
        """Export data to JSON"""
        print(f"\nExporting data to JSON: {output_file}...")
        
        data = {
            'metadata': {
                'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'days_of_data': DAYS_OF_HISTORY,
                'total_work_orders': len(self.work_orders),
                'total_operations': len(self.work_order_operations),
                'total_material_transactions': len(self.material_transactions),
                'total_quality_inspections': len(self.quality_inspections),
                'total_defects': len(self.defects),
                'total_labor_transactions': len(self.labor_transactions),
                'total_schedule_entries': len(self.production_schedule),
                'total_ebrs': len(self.electronic_batch_records)
            },
            'work_orders': self.work_orders,
            'work_order_operations': self.work_order_operations,
            'material_transactions': self.material_transactions,
            'quality_inspections': self.quality_inspections,
            'defects': self.defects,
            'labor_transactions': self.labor_transactions,
            'production_schedule': self.production_schedule,
            'electronic_batch_records': self.electronic_batch_records
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        
        print(f"Data exported to {output_file}")


if __name__ == "__main__":
    import os
    from pathlib import Path
    
    # Get the directory of this script (data folder)
    script_dir = Path(__file__).parent
    
    # Load master data from the same folder structure
    master_data_file = script_dir.parent / "01 - Base Data" / "genims_master_data.json"
    
    # Generate MES historical data
    generator = MESDataGenerator(str(master_data_file))
    generator.generate_all_data()
    
    # Export to SQL (in same folder as script)
    sql_file = script_dir / "mes_historical_data_inserts.sql"
    generator.to_sql_inserts(str(sql_file))
    
    # Export to JSON (in same folder as script)
    json_file = script_dir / "mes_historical_data.json"
    generator.to_json(str(json_file))
    
    print("\n" + "="*80)
    print("MES Historical Data Generation Complete!")
    print("Files created:")
    print("  1. mes_historical_data_inserts.sql - SQL INSERT statements")
    print("  2. mes_historical_data.json - JSON export")
    print("="*80)
