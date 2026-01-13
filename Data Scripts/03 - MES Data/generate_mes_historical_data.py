"""
GenIMS MES Historical Data Generator
Generates 30 days of production execution data with referential integrity
Ultra-Fast Parallel Processing Implementation
"""

import random
import json
from datetime import datetime, timedelta, time
from typing import List, Dict, Tuple
import string
import sys
from pathlib import Path
import threading
import multiprocessing
from concurrent.futures import ThreadPoolExecutor, as_completed

# Add scripts to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))
from generator_helper import get_helper  # type: ignore

# ============================================================================
# CONFIGURATION
# ============================================================================

DAYS_OF_HISTORY = 180
WORK_ORDERS_PER_DAY = (240, 360)  # ~4-6 orders per line per day (60 lines * 4-6 = 240-360)
OPERATIONS_PER_ORDER = (3, 8)  # Routing steps (increased complexity)
MATERIALS_PER_ORDER = (4, 12)  # BOM items (more components per product)
INSPECTIONS_PER_ORDER = (2, 5)  # Quality checkpoints (more rigorous QA)
LABOR_ENTRIES_PER_DAY = (8000, 15000)  # Time entries (~0.8-1.4 per employee - reasonable)
DOWNTIME_EVENTS_PER_DAY = (15, 25)  # ~0.25-0.42 events per line per day (realistic)
CHANGEOVERS_PER_DAY = (30, 50)  # ~0.5-0.8 changeovers per line per day (realistic)

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
    def __init__(self, master_data_file=None):
        """Initialize with master data and registry"""
        from pathlib import Path
        
        if master_data_file is None:
            master_data_file = Path(__file__).parent.parent / "01 - Base Data" / "genims_master_data.json"
        
        print(f"Loading master data from {master_data_file}...")
        with open(master_data_file, 'r') as f:
            self.master_data = json.load(f)
        
        # Load helper for FK validation
        self.helper = get_helper()
        self.registry = self.helper.registry
        
        self.factories = self.master_data['factories']
        self.employees = self.master_data['employees']
        self.products = self.master_data['products']
        self.customers = self.master_data['customers']
        
        # MES-generated master data (generated during __init__)
        self.lines = []
        self.machines = []
        self.shifts = []
        self.line_product_mapping = []
        
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
        
        # 🚀 ULTRA-FAST PARALLEL PROCESSING CONFIGURATION
        self.parallel_enabled = True  # Always enable for maximum performance
        self.worker_count = min(8, max(2, multiprocessing.cpu_count() - 1))  # Use 2-8 workers optimally
        self.batch_size = 150000  # Large batch size for efficiency
        
        # Thread safety for parallel processing
        self.data_lock = threading.Lock()
        
        print(f"🚀 ULTRA-FAST MES PARALLEL MODE: {self.worker_count} workers, batch_size={self.batch_size}")
        print(f"   CPU cores available: {multiprocessing.cpu_count()}, Using {self.worker_count} for generation")
        
        print(f"Loaded: {len(self.products)} products, {len(self.employees)} employees")
        print(f"Registry contains: {len(self.registry.get_registered_ids('product'))} valid product IDs")
    
    def generate_id(self, prefix: str, counter_key: str) -> str:
        """Generate unique ID with auto-increment"""
        if counter_key == 'work_orders':
            id_val = f"{prefix}-{str(self.wo_counter).zfill(6)}"
            self.wo_counter += 1
        elif counter_key == 'operations':
            id_val = f"{prefix}-{str(self.op_counter).zfill(6)}"
            self.op_counter += 1
        elif counter_key == 'material_transactions':
            id_val = f"{prefix}-{str(self.mat_counter).zfill(6)}"
            self.mat_counter += 1
        elif counter_key == 'inspections':
            id_val = f"{prefix}-{str(self.insp_counter).zfill(6)}"
            self.insp_counter += 1
        elif counter_key == 'defects':
            id_val = f"{prefix}-{str(self.defect_counter).zfill(6)}"
            self.defect_counter += 1
        elif counter_key == 'labor_transactions':
            id_val = f"{prefix}-{str(self.labor_counter).zfill(6)}"
            self.labor_counter += 1
        elif counter_key == 'downtime_records':
            id_val = f"{prefix}-{str(self.downtime_counter).zfill(6)}"
            self.downtime_counter += 1
        elif counter_key == 'changeovers':
            id_val = f"{prefix}-{str(self.changeover_counter).zfill(6)}"
            self.changeover_counter += 1
        elif counter_key == 'equipment_batch_records':
            id_val = f"{prefix}-{str(self.ebr_counter).zfill(6)}"
            self.ebr_counter += 1
        elif counter_key == 'schedules':
            id_val = f"{prefix}-{str(self.schedule_counter).zfill(6)}"
            self.schedule_counter += 1
        else:
            id_val = f"{prefix}-{str(self.wo_counter).zfill(6)}"
            self.wo_counter += 1
        return id_val
    
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
        # Get all employees from the factory that have 'operator' role, or pick from active employees
        operators = [e for e in self.employees 
                     if e.get('role') == 'operator' 
                     and e.get('status') == 'active']
        
        # If no operators found, return all active employees (fallback)
        if not operators:
            operators = [e for e in self.employees if e.get('status') == 'active']
        
        return operators
    
    def generate_work_orders(self, start_date: datetime, days: int):
        """Generate work orders with ULTRA-FAST PARALLEL processing"""
        print(f"\nGenerating work orders for {days} days with PARALLEL processing...")
        
        # FK from registry - GUARANTEED VALID
        valid_line_ids = list(self.helper.get_valid_line_ids())
        valid_product_ids = list(self.helper.get_valid_product_ids())
        valid_employee_ids = list(self.helper.get_valid_employee_ids())
        
        if not self.parallel_enabled or days < 20:
            return self._generate_work_orders_sequential(start_date, days, valid_line_ids, valid_product_ids, valid_employee_ids)
        
        # Parallel processing for large datasets
        chunk_size = max(5, days // self.worker_count)  # At least 5 days per chunk
        day_chunks = [(i, min(chunk_size, days - i)) for i in range(0, days, chunk_size)]
        
        print(f"  🚀 Processing {len(day_chunks)} day chunks with {self.worker_count} workers...")
        
        all_work_orders = []
        all_work_order_operations = []
        all_material_transactions = []
        all_quality_inspections = []
        all_defects = []
        all_labor_transactions = []
        all_downtime_events = []
        all_changeover_events = []
        all_electronic_batch_records = []
        all_production_schedule = []
        
        with ThreadPoolExecutor(max_workers=self.worker_count) as executor:
            # Submit chunk processing tasks
            futures = {
                executor.submit(self._generate_work_orders_chunk, 
                    start_date + timedelta(days=start_day), 
                    chunk_days, 
                    chunk_id,
                    valid_line_ids, valid_product_ids, valid_employee_ids): chunk_id 
                for chunk_id, (start_day, chunk_days) in enumerate(day_chunks)
            }
            
            # Collect results as they complete
            for future in as_completed(futures):
                chunk_id = futures[future]
                try:
                    chunk_results = future.result()
                    
                    all_work_orders.extend(chunk_results['work_orders'])
                    all_work_order_operations.extend(chunk_results['work_order_operations'])
                    all_material_transactions.extend(chunk_results['material_transactions'])
                    all_quality_inspections.extend(chunk_results['quality_inspections'])
                    all_defects.extend(chunk_results['defects'])
                    all_labor_transactions.extend(chunk_results['labor_transactions'])
                    all_downtime_events.extend(chunk_results['downtime_events'])
                    all_changeover_events.extend(chunk_results['changeover_events'])
                    all_electronic_batch_records.extend(chunk_results['electronic_batch_records'])
                    all_production_schedule.extend(chunk_results['production_schedule'])
                    
                    print(f"    ✓ Work orders chunk {chunk_id + 1}/{len(day_chunks)} completed ({len(chunk_results['work_orders'])} orders)")
                except Exception as e:
                    print(f"    ✗ Work orders chunk {chunk_id + 1} failed: {e}")
        
        # Store results with thread safety
        with self.data_lock:
            self.work_orders.extend(all_work_orders)
            self.work_order_operations.extend(all_work_order_operations)
            self.material_transactions.extend(all_material_transactions)
            self.quality_inspections.extend(all_quality_inspections)
            self.defects.extend(all_defects)
            self.labor_transactions.extend(all_labor_transactions)
            self.downtime_events.extend(all_downtime_events)
            self.changeover_events.extend(all_changeover_events)
            self.electronic_batch_records.extend(all_electronic_batch_records)
            self.production_schedule.extend(all_production_schedule)
        
        print(f"✓ Generated {len(self.work_orders):,} work orders via PARALLEL processing")
    
    def _generate_work_orders_chunk(self, start_date: datetime, days: int, chunk_id: int, 
                                  valid_line_ids: List[str], valid_product_ids: List[str], valid_employee_ids: List[str]) -> Dict:
        """Generate work orders for a chunk of days (parallel worker method)"""
        
        # Local data storage for this chunk
        chunk_work_orders = []
        chunk_work_order_operations = []
        chunk_material_transactions = []
        chunk_quality_inspections = []
        chunk_defects = []
        chunk_labor_transactions = []
        chunk_downtime_events = []
        chunk_changeover_events = []
        chunk_electronic_batch_records = []
        chunk_production_schedule = []
        
        # Local counters to avoid collision
        local_wo_counter = chunk_id * 10000 + 1
        local_op_counter = chunk_id * 50000 + 1
        local_mat_counter = chunk_id * 100000 + 1
        local_insp_counter = chunk_id * 20000 + 1
        local_defect_counter = chunk_id * 50000 + 1
        local_labor_counter = chunk_id * 200000 + 1
        local_downtime_counter = chunk_id * 10000 + 1
        local_changeover_counter = chunk_id * 10000 + 1
        local_ebr_counter = chunk_id * 10000 + 1
        local_schedule_counter = chunk_id * 20000 + 1
        
        current_date = start_date
        
        for day in range(days):
            num_orders = random.randint(*WORK_ORDERS_PER_DAY)
            
            for _ in range(num_orders):
                # Use valid FKs from registry
                line_id = random.choice(valid_line_ids) if valid_line_ids else random.choice([m['line_id'] for m in self.line_product_mapping])
                product_id = random.choice(valid_product_ids) if valid_product_ids else random.choice([m['product_id'] for m in self.line_product_mapping])
                
                # Get factory from line
                mapping = next((m for m in self.line_product_mapping if m['line_id'] == line_id), None)
                factory_id = mapping['factory_id'] if mapping else random.choice(self.factories)['factory_id']
                
                # Get product and line details (fallback to defaults if not found)
                product = next((p for p in self.products if p['product_id'] == product_id), {
                    'product_id': product_id, 
                    'standard_cycle_time_seconds': 120,
                    'product_category': 'suspension'
                })
                line = next((l for l in self.lines if l['line_id'] == line_id), {'line_id': line_id})
                
                # Customer (always assign a customer from master data)
                customer_id = random.choice(self.customers)['customer_id']
                
                # Quantities
                planned_qty = random.randint(50, 500)
                
                # Timing - start during day shift
                start_hour = random.randint(6, 14)
                planned_start = current_date.replace(hour=start_hour, minute=random.randint(0, 59))
                
                # Duration based on quantity and cycle time
                cycle_time = product.get('standard_cycle_time_seconds', random.randint(30, 300))
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
                
                # Quality logic - optimize this section to reduce complexity
                if status in ['completed', 'closed']:
                    actual_start = planned_start + timedelta(minutes=random.randint(-15, 30))
                    actual_end = actual_start + timedelta(minutes=int(total_minutes * random.uniform(0.95, 1.15)))
                    produced_qty = int(planned_qty * random.uniform(0.95, 1.05))
                    
                    # Simplified quality calculation
                    fpy = random.uniform(*FIRST_PASS_YIELD_RANGE) / 100
                    good_qty = int(produced_qty * fpy)
                    bad_qty = produced_qty - good_qty
                    rejected_qty = int(bad_qty * 0.7)
                    scrapped_qty = int(bad_qty * 0.2)
                    rework_qty = bad_qty - rejected_qty - scrapped_qty
                    
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
                    scrapped_qty = rework_qty = 0
                    yield_pct = fpyield_pct = actual_cycle_time = run_time = None
                    downtime = 0
                else:  # scheduled, released, cancelled
                    actual_start = actual_end = None
                    produced_qty = good_qty = rejected_qty = scrapped_qty = rework_qty = 0
                    yield_pct = fpyield_pct = actual_cycle_time = run_time = None
                    downtime = 0
                
                # Batch/lot numbers using local counter
                batch_number = f"BATCH-{current_date.strftime('%Y%m%d')}-{local_wo_counter:04d}"
                lot_number = f"LOT-{factory_id[-3:] if len(factory_id) >= 3 else factory_id}-{local_wo_counter:05d}"
                
                # Create work order with local counter
                work_order = {
                    'work_order_id': f"WO-{str(local_wo_counter).zfill(6)}",
                    'work_order_number': f"WO-{current_date.strftime('%Y%m%d')}-{local_wo_counter:04d}",
                    'product_id': product_id,
                    'customer_id': customer_id,
                    'sales_order_number': f"SO-{random.randint(10000, 99999)}",
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
                    'status': status,
                    'produced_quantity': produced_qty,
                    'good_quantity': good_qty,
                    'rejected_quantity': rejected_qty,
                    'scrapped_quantity': scrapped_qty,
                    'rework_quantity': rework_qty,
                    'yield_percentage': yield_pct,
                    'first_pass_yield_percentage': fpyield_pct,
                    'batch_number': batch_number,
                    'lot_number': lot_number,
                    'setup_time_minutes': setup_time,
                    'run_time_minutes': run_time,
                    'downtime_minutes': downtime,
                    'actual_cycle_time_seconds': actual_cycle_time,
                    'created_by': random.choice(valid_employee_ids) if valid_employee_ids else 'EMP-000001',
                    'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                
                chunk_work_orders.append(work_order)
                local_wo_counter += 1
                
                # Generate related data for completed/in-progress orders only (optimize performance)
                if status in ['completed', 'in_progress', 'closed']:
                    # Generate operations (limited to reduce data volume)
                    ops_count = random.randint(2, 5)  # Reduced from 3-8
                    for op_seq in range(1, ops_count + 1):
                        operation = {
                            'operation_id': f"OP-{str(local_op_counter).zfill(6)}",
                            'work_order_id': work_order['work_order_id'],
                            'operation_sequence': op_seq,
                            'operation_code': f"OP{op_seq:03d}",
                            'operation_name': f"Operation {op_seq} for {product_id}",
                            'planned_quantity': planned_qty,
                            'status': status,
                            'planned_duration_minutes': total_minutes // ops_count,
                            'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                            'updated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        }
                        chunk_work_order_operations.append(operation)
                        local_op_counter += 1
                    
                    # Generate material transactions (reduced count)
                    mat_count = random.randint(2, 6)  # Reduced from 4-12
                    mat_start_time = datetime.strptime(work_order['actual_start_time'], '%Y-%m-%d %H:%M:%S') if work_order['actual_start_time'] else datetime.strptime(work_order['planned_start_time'], '%Y-%m-%d %H:%M:%S')
                    
                    for _ in range(mat_count):
                        mat_code = random.choice(RAW_MATERIALS + COMPONENTS)
                        if 'RM-' in mat_code:
                            mat_type = 'raw_material'
                            mat_name = mat_code.replace('RM-', '').replace('-', ' ').title()
                        else:
                            mat_type = 'component'
                            mat_name = mat_code.replace('COMP-', '').replace('-', ' ').title()
                        
                        material = {
                            'transaction_id': f"MT-{str(local_mat_counter).zfill(6)}",
                            'transaction_type': random.choice(['issue', 'return']),
                            'transaction_date': mat_start_time.strftime('%Y-%m-%d %H:%M:%S'),
                            'work_order_id': work_order['work_order_id'],
                            'material_code': mat_code,
                            'material_name': mat_name,
                            'material_type': mat_type,
                            'quantity': round(random.uniform(1, 100), 2),
                            'unit_of_measure': 'EA',
                            'unit_cost': round(random.uniform(0.5, 50.0), 2),
                            'total_cost': round(random.uniform(1, 5000), 2),
                            'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        }
                        chunk_material_transactions.append(material)
                        local_mat_counter += 1
                        
                    # Generate quality inspections for completed orders
                    if status == 'completed':
                        quality_inspections = self._generate_quality_inspections_local(work_order, local_insp_counter)
                        chunk_quality_inspections.extend(quality_inspections)
                        local_insp_counter += len(quality_inspections)
                        
                        # Generate defects if quality issues exist
                        if work_order['rejected_quantity'] > 0 or work_order['scrapped_quantity'] > 0:
                            defects = self._generate_defects_local(work_order, local_defect_counter)
                            chunk_defects.extend(defects)
                            local_defect_counter += len(defects)
                    
                    # Generate labor transactions for all active orders
                    labor_transactions = self._generate_labor_transactions_local(work_order, local_labor_counter, valid_employee_ids)
                    chunk_labor_transactions.extend(labor_transactions)
                    local_labor_counter += len(labor_transactions)
                    
                    # Generate production schedule entry
                    schedule_entry = self._generate_schedule_entry_local(work_order, local_schedule_counter)
                    chunk_production_schedule.append(schedule_entry)
                    local_schedule_counter += 1
                    
                    # Generate Electronic Batch Record for completed orders (50% of time)
                    if status == 'completed' and random.random() < 0.5:
                        ebr = self._generate_ebr_local(work_order, local_ebr_counter, valid_employee_ids)
                        chunk_electronic_batch_records.append(ebr)
                        local_ebr_counter += 1
            
            current_date += timedelta(days=1)
        
        # Return all chunk data
        return {
            'work_orders': chunk_work_orders,
            'work_order_operations': chunk_work_order_operations,
            'material_transactions': chunk_material_transactions,
            'quality_inspections': chunk_quality_inspections,
            'defects': chunk_defects,
            'labor_transactions': chunk_labor_transactions,
            'downtime_events': chunk_downtime_events,
            'changeover_events': chunk_changeover_events,
            'electronic_batch_records': chunk_electronic_batch_records,
            'production_schedule': chunk_production_schedule
        }
    
    def _generate_quality_inspections_local(self, work_order: Dict, start_counter: int) -> List[Dict]:
        """Generate quality inspections for a single work order (local/chunk version)"""
        inspections = []
        if work_order['status'] == 'completed':
            inspection = {
                'inspection_id': f"QI-{str(start_counter).zfill(6)}",
                'work_order_id': work_order['work_order_id'],
                'lot_number': work_order['lot_number'],
                'inspection_type': random.choice(['incoming', 'in_process', 'final']),
                'inspection_date': work_order['actual_end_time'],
                'inspector_id': random.choice(['EMP-000001', 'EMP-000002', 'EMP-000003']),
                'inspection_result': 'pass',
                'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'updated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            inspections.append(inspection)
        return inspections
    
    def _generate_defects_local(self, work_order: Dict, start_counter: int) -> List[Dict]:
        """Generate defects for a single work order (local/chunk version)"""
        defects = []
        if work_order['rejected_quantity'] > 0 or work_order['scrapped_quantity'] > 0:
            num_defects = random.randint(1, 3)
            for i in range(num_defects):
                detected_dt = datetime.strptime(work_order['actual_end_time'], '%Y-%m-%d %H:%M:%S') if work_order['actual_end_time'] else datetime.now()
                defect = {
                    'defect_id': f"DEF-{str(start_counter + i).zfill(6)}",
                    'work_order_id': work_order['work_order_id'],
                    'defect_code': f"DEF-{random.randint(100, 999)}",
                    'defect_category': random.choice(['dimensional', 'visual', 'functional', 'material', 'assembly']),
                    'defect_description': f"Quality issue detected in {work_order['product_id']}",
                    'defect_severity': random.choice(['critical', 'major', 'minor']),
                    'detected_date': detected_dt.strftime('%Y-%m-%d %H:%M:%S'),
                    'quantity_affected': random.randint(1, min(10, work_order['rejected_quantity'] or 1)),
                    'root_cause_analysis_complete': False,
                    'action_completed': False,
                    'status': 'open',
                    'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'updated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                defects.append(defect)
        return defects
    
    def _generate_labor_transactions_local(self, work_order: Dict, start_counter: int, valid_employee_ids: List[str]) -> List[Dict]:
        """Generate labor transactions for a single work order (local/chunk version)"""
        transactions = []
        num_transactions = random.randint(1, 4)
        for i in range(num_transactions):
            clock_in = datetime.strptime(work_order['actual_start_time'], '%Y-%m-%d %H:%M:%S') if work_order['actual_start_time'] else datetime.strptime(work_order['planned_start_date'], '%Y-%m-%d %H:%M:%S')
            duration = random.randint(120, 480)
            transaction = {
                'labor_transaction_id': f"LT-{str(start_counter + i).zfill(6)}",
                'transaction_date': clock_in.strftime('%Y-%m-%d %H:%M:%S'),
                'employee_id': random.choice(valid_employee_ids) if valid_employee_ids else 'EMP-000001',
                'activity_code': 'DIRECT_LABOR',
                'activity_type': 'direct_labor',
                'duration_minutes': duration,
                'work_order_id': work_order['work_order_id'],
                'clock_in_time': clock_in.strftime('%Y-%m-%d %H:%M:%S'),
                'clock_out_time': (clock_in + timedelta(minutes=duration)).strftime('%Y-%m-%d %H:%M:%S'),
                'hourly_rate': round(random.uniform(15, 35), 2),
                'labor_cost': round(duration / 60 * random.uniform(15, 35), 2),
                'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'updated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            transactions.append(transaction)
        return transactions
    
    def _generate_schedule_entry_local(self, work_order: Dict, counter: int) -> Dict:
        """Generate production schedule entry for a single work order (local/chunk version)"""
        # Use planned_start_date and planned_end_date (which contain full datetime)
        planned_start = datetime.strptime(work_order['planned_start_date'], '%Y-%m-%d %H:%M:%S')
        planned_end = datetime.strptime(work_order['planned_end_date'], '%Y-%m-%d %H:%M:%S')
        
        return {
            'schedule_id': f"SCH-{str(counter).zfill(6)}",
            'work_order_id': work_order['work_order_id'],
            'factory_id': work_order['factory_id'],
            'line_id': work_order['line_id'],
            'product_id': work_order['product_id'],
            'schedule_date': planned_start.strftime('%Y-%m-%d'),
            'schedule_week': planned_start.isocalendar()[1],
            'shift_id': self.get_shift_for_time(work_order['factory_id'], planned_start)['shift_id'],
            'planned_start_time': work_order['planned_start_date'],
            'planned_end_time': work_order['planned_end_date'],
            'planned_quantity': work_order['planned_quantity'],
            'schedule_status': work_order['status'],
            'priority': work_order['priority'],
            'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
    
    def _generate_ebr_local(self, work_order: Dict, counter: int, valid_employee_ids: List[str]) -> Dict:
        """Generate electronic batch record for a single work order (local/chunk version)"""
        batch_start = datetime.strptime(work_order['actual_start_time'], '%Y-%m-%d %H:%M:%S') if work_order['actual_start_time'] else datetime.strptime(work_order['planned_start_date'], '%Y-%m-%d %H:%M:%S')
        batch_end = datetime.strptime(work_order['actual_end_time'], '%Y-%m-%d %H:%M:%S') if work_order['actual_end_time'] else datetime.strptime(work_order['planned_end_date'], '%Y-%m-%d %H:%M:%S')
        expiry_date = (batch_start + timedelta(days=random.randint(180, 730))).strftime('%Y-%m-%d')
        
        return {
            'ebr_id': f"EBR-{str(counter).zfill(6)}",
            'batch_id': work_order['batch_number'],
            'batch_number': work_order['batch_number'],
            'batch_date': batch_start.strftime('%Y-%m-%d'),
            'batch_quantity': work_order['produced_quantity'],
            'product_id': work_order['product_id'],
            'material_id': f"MAT-{random.randint(1001, 5000):05d}",
            'work_order_id': work_order['work_order_id'],
            'batch_size': work_order['produced_quantity'],
            'formula_id': f"FORM-{random.randint(100, 999)}",
            'formula_version': f"v{random.randint(1, 5)}.{random.randint(0, 9)}",
            'manufacturing_date': batch_start.strftime('%Y-%m-%d'),
            'expiration_date': expiry_date,
            'retest_date': (datetime.strptime(expiry_date, '%Y-%m-%d') - timedelta(days=30)).strftime('%Y-%m-%d'),
            'factory_id': work_order['factory_id'],
            'manufacturing_area': f"AREA-{work_order['line_id'][-3:] if len(work_order['line_id']) >= 3 else work_order['line_id']}",
            'status': 'approved',
            'quality_status': 'approved',
            'record_status': 'approved',
            'prepared_by': random.choice(valid_employee_ids) if valid_employee_ids else 'EMP-000001',
            'prepared_at': batch_end.strftime('%Y-%m-%d %H:%M:%S'),
            'reviewed_by': random.choice(valid_employee_ids) if valid_employee_ids else 'EMP-000002',
            'reviewed_at': (batch_end + timedelta(hours=2)).strftime('%Y-%m-%d %H:%M:%S'),
            'approved_by': random.choice(valid_employee_ids) if valid_employee_ids else 'EMP-000003',
            'approved_at': (batch_end + timedelta(hours=4)).strftime('%Y-%m-%d %H:%M:%S'),
            'release_status': 'released',
            'released_by': random.choice(valid_employee_ids) if valid_employee_ids else 'EMP-000004',
            'released_at': (batch_end + timedelta(hours=6)).strftime('%Y-%m-%d %H:%M:%S'),
            'has_deviations': False,
            'deviation_count': 0,
            'temperature_min_c': round(random.uniform(18, 22), 2),
            'temperature_max_c': round(random.uniform(24, 28), 2),
            'humidity_min_percentage': round(random.uniform(40, 50), 2),
            'humidity_max_percentage': round(random.uniform(55, 65), 2),
            'regulatory_requirement': 'IATF 16949',
            'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

    def _generate_work_orders_sequential(self, start_date: datetime, days: int, 
                                       valid_line_ids: List[str], valid_product_ids: List[str], valid_employee_ids: List[str]):
        """Fallback sequential work orders generation for small datasets"""
        print("Generating work orders (sequential fallback)...")
        
        # Use the original sequential logic for small datasets
        current_date = start_date
        
        for day in range(days):
            num_orders = random.randint(*WORK_ORDERS_PER_DAY)
            
            for _ in range(num_orders):
                # Simplified sequential logic (same as chunk but using instance counters)
                line_id = random.choice(valid_line_ids) if valid_line_ids else random.choice([m['line_id'] for m in self.line_product_mapping])
                product_id = random.choice(valid_product_ids) if valid_product_ids else random.choice([m['product_id'] for m in self.line_product_mapping])
                
                work_order = {
                    'work_order_id': self.generate_id('WO', 'work_orders'),
                    'work_order_number': f"WO-{current_date.strftime('%Y%m%d')}-{self.wo_counter:04d}",
                    'status': 'completed'  # Simplified for sequential
                }
                
                self.work_orders.append(work_order)
                self.wo_counter += 1
            
            current_date += timedelta(days=1)
        
        print(f"✓ Generated {len(self.work_orders)} work orders (sequential)")
    
    def _apply_formula(self, formula: str, work_order: Dict) -> str:
        
        for day in range(days):
            num_orders = random.randint(*WORK_ORDERS_PER_DAY)
            
            for _ in range(num_orders):
                # Use valid FKs from registry
                line_id = random.choice(valid_line_ids) if valid_line_ids else random.choice([m['line_id'] for m in self.line_product_mapping])
                product_id = random.choice(valid_product_ids) if valid_product_ids else random.choice([m['product_id'] for m in self.line_product_mapping])
                
                # Get factory from line
                mapping = next((m for m in self.line_product_mapping if m['line_id'] == line_id), None)
                factory_id = mapping['factory_id'] if mapping else random.choice(self.factories)['factory_id']
                
                # Get product and line details (fallback to defaults if not found)
                product = next((p for p in self.products if p['product_id'] == product_id), {
                    'product_id': product_id, 
                    'standard_cycle_time_seconds': 120,
                    'product_category': 'suspension'
                })
                line = next((l for l in self.lines if l['line_id'] == line_id), {'line_id': line_id})
                
                # Customer (always assign a customer from master data)
                customer_id = random.choice(self.customers)['customer_id']
                
                # Quantities
                planned_qty = random.randint(50, 500)
                
                # Timing - start during day shift
                start_hour = random.randint(6, 14)
                planned_start = current_date.replace(hour=start_hour, minute=random.randint(0, 59))
                
                # Duration based on quantity and cycle time
                # If product doesn't have standard_cycle_time, generate one based on complexity
                cycle_time = product.get('standard_cycle_time_seconds', random.randint(30, 300))
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
                    
                    # Quality - ensure quantities sum correctly
                    fpy = random.uniform(*FIRST_PASS_YIELD_RANGE) / 100
                    good_qty = int(produced_qty * fpy)
                    bad_qty = produced_qty - good_qty
                    
                    # Distribute bad qty: 70% rejected, 20% scrapped, rest rework
                    rejected_qty = int(bad_qty * 0.7)
                    scrapped_qty = int(bad_qty * 0.2)
                    rework_qty = bad_qty - rejected_qty - scrapped_qty
                    
                    # Validate sum
                    if good_qty + rejected_qty + scrapped_qty + rework_qty != produced_qty:
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
                    'work_order_id': self.generate_id('WO', 'work_orders'),
                    'work_order_number': f"WO-{current_date.strftime('%Y%m%d')}-{self.wo_counter:04d}",
                    'product_id': product_id,
                    'customer_id': customer_id,
                    'sales_order_number': f"SO-{random.randint(10000, 99999)}",
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
                    'actual_cost_per_unit': round(random.uniform(10, 100), 2) if status in ['completed', 'closed'] else None,
                    'total_material_cost': round(random.uniform(1000, 10000), 2) if status in ['completed', 'closed'] else None,
                    'total_labor_cost': round(random.uniform(500, 5000), 2) if status in ['completed', 'closed'] else None,
                    'total_overhead_cost': round(random.uniform(200, 2000), 2) if status in ['completed', 'closed'] else None,
                    'batch_number': batch_number,
                    'lot_number': lot_number,
                    'expiry_date': (current_date + timedelta(days=365)).strftime('%Y-%m-%d'),
                    'electronic_batch_record_id': f"EBR-{random.randint(100000, 999999)}" if status in ['completed', 'closed'] else None,
                    'requires_validation': status in ['completed', 'closed'],
                    'validation_status': random.choice(['approved', 'pending', 'failed']) if status in ['completed', 'closed'] else None,
                    'parent_work_order_id': None,  # Will be populated in post-processing
                    'erp_order_id': f"ERP-{random.randint(100000, 999999)}",
                    'created_by': random.choice([e['employee_id'] for e in self.employees if e['role'] in ['supervisor', 'manager']]),
                    'created_at': (current_date - timedelta(days=1)).strftime('%Y-%m-%d %H:%M:%S'),
                    'updated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'completed_by': random.choice([e['employee_id'] for e in self.employees if e['role'] == 'supervisor']) if status == 'completed' else None,
                    'closed_at': actual_end.strftime('%Y-%m-%d %H:%M:%S') if status in ['closed', 'completed'] and actual_end else None
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
        
        # Link parent work orders (55% of work orders reference an earlier work order from same line/day)
        for i, wo in enumerate(self.work_orders):
            if i > 0 and random.random() < 0.55:  # Increased from 45% to 55%
                # Link to a random earlier work order (prefer same line, then same day, then any earlier)
                candidates_same_line = [idx for idx in range(i) if self.work_orders[idx]['line_id'] == wo['line_id']]
                candidates_same_day = [idx for idx in range(i) if self.work_orders[idx]['planned_start_date'][:10] == wo['planned_start_date'][:10]]
                
                if candidates_same_line:
                    parent_idx = random.choice(candidates_same_line)
                elif candidates_same_day:
                    parent_idx = random.choice(candidates_same_day)
                else:
                    parent_idx = random.randint(0, i - 1)
                
                wo['parent_work_order_id'] = self.work_orders[parent_idx]['work_order_id']
        
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
            
            # Get operator and shift (only if work order has actual start time)
            shift = None
            operator = None
            if work_order['actual_start_time']:
                shift = self.get_shift_for_time(work_order['factory_id'], datetime.strptime(work_order['actual_start_time'], '%Y-%m-%d %H:%M:%S'))
                operators = self.get_operators_for_shift(work_order['line_id'], shift.get('shift_name', 'General'))
                operator = random.choice(operators) if operators else None
            else:
                # Default shift if no actual start time
                shift = self.shifts[0] if self.shifts else {'shift_id': 'SHF-000001', 'shift_name': 'General'}
            
            # Timing
            if work_order['actual_start_time']:
                op_start = datetime.strptime(work_order['actual_start_time'], '%Y-%m-%d %H:%M:%S') + timedelta(minutes=seq * 30)
                op_duration = random.randint(30, 120)
                op_end = op_start + timedelta(minutes=op_duration) if work_order['status'] == 'completed' else None
            else:
                op_start = None
                op_end = None
                op_duration = None
            
            planned_duration = random.randint(30, 120)
            planned_setup = random.randint(10, 30)
            
            # Calculate planned times from work order start
            planned_start = work_order.get('planned_start_date') or work_order.get('scheduled_start_time')
            if isinstance(planned_start, str):
                planned_start_dt = datetime.strptime(planned_start, '%Y-%m-%d %H:%M:%S')
            else:
                planned_start_dt = datetime.now()
            
            planned_start_op = (planned_start_dt + timedelta(minutes=seq * planned_duration)).strftime('%Y-%m-%d %H:%M:%S')
            planned_end_op = (planned_start_dt + timedelta(minutes=seq * planned_duration + planned_duration)).strftime('%Y-%m-%d %H:%M:%S')
            
            operation = {
                'operation_id': self.generate_id('OP', 'operations'),
                'work_order_id': work_order['work_order_id'],
                'operation_sequence': seq,
                'operation_code': f"OP-{seq:02d}",
                'operation_name': op_name.replace('_', ' ').title(),
                'line_id': work_order['line_id'],
                'machine_id': machine['machine_id'] if machine else random.choice([m['machine_id'] for m in self.machines]),
                'work_center_code': f"WC-{work_order['line_id'][-3:]}",
                'planned_quantity': work_order['planned_quantity'],
                'planned_duration_minutes': planned_duration,
                'planned_setup_time_minutes': planned_setup,
                'planned_hours': round((planned_duration + planned_setup) / 60, 2),
                'setup_hours': round(planned_setup / 60, 2),
                'standard_time_per_unit_seconds': round(random.uniform(30, 180), 2),
                'planned_start_time': planned_start_op,
                'planned_end_time': planned_end_op,
                'actual_start_time': op_start.strftime('%Y-%m-%d %H:%M:%S') if op_start else None,
                'actual_end_time': op_end.strftime('%Y-%m-%d %H:%M:%S') if op_end else None,
                # Distribute quantities across operations proportionally
                'completed_quantity': int(work_order['produced_quantity'] / num_operations) if work_order['status'] == 'completed' else 0,
                'rejected_quantity': int(work_order['rejected_quantity'] / num_operations) if work_order['status'] == 'completed' else 0,
                'actual_duration_minutes': op_duration,
                'actual_setup_time_minutes': random.randint(10, 30) if op_start else None,
                'status': 'completed' if work_order['status'] == 'completed' else 'in_progress',
                'operation_status': 'completed' if work_order['status'] == 'completed' else 'in_progress',
                'operator_id': operator['employee_id'] if operator else random.choice([e['employee_id'] for e in self.employees if e['role'] == 'operator']),
                'shift_id': shift['shift_id'],
                'labor_hours': round(op_duration / 60, 2) if op_duration else None,
                'requires_inspection': seq == len(selected_ops),
                'inspection_status': 'passed' if work_order['status'] == 'completed' else 'pending',
                'inspection_timestamp': op_end.strftime('%Y-%m-%d %H:%M:%S') if op_end else None,
                'inspector_id': random.choice([e['employee_id'] for e in self.employees if e['role'] == 'quality_inspector']) if seq == len(selected_ops) else random.choice([e['employee_id'] for e in self.employees]),
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
        
        for mat_idx, material_code in enumerate(materials[:num_materials]):
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
            
            supplier_id = f"SUP-{random.randint(1001, 2000)}" if mat_type == 'raw_material' else None
            issued_by_emp = random.choice([e['employee_id'] for e in self.employees] if self.employees else ['EMP-000001'])
            
            # Unit cost and total cost must match
            unit_cost = round(random.uniform(1, 50), 4)
            total_cost = round(quantity * unit_cost, 2)
            
            # Parent lot number - link to previous raw material lots for traceability (components 70%, raw materials 45%)
            parent_lot = None
            if mat_type == 'component':
                # Components get parent lots from previous RM transactions 70% of time
                raw_mat_lots = [t['lot_number'] for t in self.material_transactions if t['material_type'] == 'raw_material']
                if raw_mat_lots and random.random() < 0.70:
                    parent_lot = random.choice(raw_mat_lots)
            elif mat_type == 'raw_material' and random.random() < 0.45:
                # Some raw materials have suppliers as parent (traceability)
                parent_lot = f"PARENT-LOT-{random.randint(10000, 99999)}"
            
            # Get operations for this WO (use first for raw materials, distributed for components)
            ops_for_wo = [op for op in self.work_order_operations if op['work_order_id'] == work_order['work_order_id']]
            if ops_for_wo:
                # Raw materials for setup (operation 1), components/consumables distributed
                assigned_op = ops_for_wo[0] if mat_type == 'raw_material' else ops_for_wo[min(mat_idx % len(ops_for_wo), len(ops_for_wo)-1)]
                assigned_op_id = assigned_op['operation_id']
            else:
                assigned_op_id = None
            
            transaction = {
                'transaction_id': self.generate_id('MT', 'material_transactions'),
                'transaction_type': 'issue',
                'transaction_date': trans_date.strftime('%Y-%m-%d %H:%M:%S'),
                'work_order_id': work_order['work_order_id'],
                'operation_id': assigned_op_id,
                'material_code': material_code,
                'material_name': mat_name,
                'material_description': f"{mat_name} - {mat_type.replace('_', ' ').title()}",
                'material_type': mat_type,
                'quantity_issued': quantity,
                'quantity': quantity,
                'quantity_returned': 0,
                'unit_of_measure': unit,
                'lot_number': f"MAT-LOT-{random.randint(10000, 99999)}",
                'batch_number': f"MAT-BATCH-{random.randint(1000, 9999)}",
                'serial_number': f"SN-{random.randint(100000, 999999)}" if mat_type in ['component', 'finished_good'] else (f"SN-{random.randint(100000, 999999)}" if random.random() < 0.70 else None),
                'expiry_date': (trans_date + timedelta(days=180)).strftime('%Y-%m-%d'),
                'supplier_id': f"SUP-{random.randint(1001, 2000)}",
                'supplier_lot_number': f"SUP-{random.randint(10000, 99999)}",
                'from_location': 'WAREHOUSE-A',
                'to_location': f"LINE-{work_order['line_id'][-3:]}",
                'warehouse_location': f"BIN-{random.choice(['A', 'B', 'C'])}-{random.randint(1, 50):02d}",
                'line_id': work_order['line_id'],
                'factory_id': work_order['factory_id'],
                'issued_at': trans_date.strftime('%Y-%m-%d %H:%M:%S'),
                'issued_by': issued_by_emp,
                'unit_cost': unit_cost,
                'total_cost': total_cost,
                'quality_status': 'approved',
                'inspection_required': mat_type in ['raw_material', 'component'],
                'certificate_of_analysis': f"COA-{random.randint(10000, 99999)}" if mat_type in ['raw_material', 'component'] else None,
                'parent_lot_number': parent_lot,
                'consumed_by_lot_number': work_order['lot_number'],
                'performed_by': issued_by_emp,
                'requires_documentation': mat_type in ['raw_material', 'component'],
                'documentation_complete': True,
                'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'updated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            self.material_transactions.append(transaction)
            self.mat_counter += 1
    
    def _generate_quality_inspections(self, work_order: Dict):
        """Generate quality inspections"""
        num_inspections = random.randint(*INSPECTIONS_PER_ORDER)
        
        inspection_types = ['in_process', 'final']
        
        # Link to work order operations
        operations = [op for op in self.work_order_operations if op['work_order_id'] == work_order['work_order_id']]
        
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
            
            # Results - link to work order quality data
            rejected_total = work_order.get('rejected_quantity', 0)
            
            # Inspection pass rate should align with FPY
            fpy_from_wo = 1.0 - (rejected_total / work_order.get('produced_quantity', 1)) if work_order.get('produced_quantity', 0) > 0 else 1.0
            inspection_passed = random.random() < max(0.5, fpy_from_wo)  # Min 50% to avoid always failing
            
            if inspection_passed:
                result = 'pass'
                disposition = 'accept'
                # Defects should be low if inspection passes
                defects = max(0, random.randint(-1, 1))  # 0-1 defects
                critical = 0
                major = 0
                minor = defects
            else:
                result = random.choice(['fail', 'conditional_pass', 'rework_required'])
                disposition = random.choice(['reject', 'rework', 'use_as_is'])
                # Defects should correlate with rejected quantity
                defects = max(1, int(rejected_total / 10) if rejected_total > 0 else random.randint(1, 3))
                critical = min(1, max(0, defects // 5))
                major = min(2, max(0, (defects - critical) // 3))
                minor = defects - critical - major
            
            sample_inspected = random.randint(5, 20)
            samples_passed = int(sample_inspected * (0.95 if inspection_passed else 0.7))
            samples_failed = sample_inspected - samples_passed
            pass_rate = (samples_passed / sample_inspected * 100) if sample_inspected > 0 else 0
            
            # Populate measurement data
            measured_vals = [round(random.uniform(19.8, 20.2), 2) for _ in range(3)]
            spec_vals = [20.0, 0.5]  # Target +/- tolerance
            
            inspection = {
                'inspection_id': self.generate_id('INS', 'inspections'),
                'inspection_type': insp_type,
                'inspection_date': insp_date.strftime('%Y-%m-%d %H:%M:%S'),
                'work_order_id': work_order['work_order_id'],
                'operation_id': random.choice(operations)['operation_id'] if operations else None,
                'product_id': work_order['product_id'],
                'sample_size': sample_inspected,
                'samples_inspected': sample_inspected,
                'samples_passed': samples_passed,
                'samples_failed': samples_failed,
                'pass_rate_percentage': round(pass_rate, 2),
                'lot_number': work_order['lot_number'],
                'batch_number': work_order['batch_number'],
                'serial_number': f"SN-{random.randint(100000, 999999)}",
                'inspector_id': inspector['employee_id'],
                'shift_id': self.get_shift_for_time(work_order['factory_id'], insp_date)['shift_id'],
                'line_id': work_order['line_id'],
                'factory_id': work_order['factory_id'],
                'inspection_result': result,
                'inspection_status': 'passed' if inspection_passed else 'failed',
                'defects_found': defects,
                'critical_defects': critical,
                'major_defects': major,
                'minor_defects': minor,
                'measured_values': json.dumps(measured_vals),
                'specification_values': json.dumps(spec_vals),
                'disposition': disposition,
                'disposition_reason': 'Quality standards met' if inspection_passed else 'Dimensional non-conformance',
                'disposition_by': inspector['employee_id'],
                'ncr_number': f"NCR-{insp_date.strftime('%Y%m')}-{random.randint(1, 30):04d}" if (not inspection_passed or random.random() < 0.75) else None,  # Increased probability from 65% to 75%
                'corrective_action_required': not inspection_passed,
                'inspection_plan_id': f"IP-{random.randint(100, 999)}",
                'inspection_checklist_id': f"CL-{random.randint(100, 999)}",
                'photos_attached': random.random() < 0.2,
                'approved_by': random.choice(self.employees)['employee_id'],
                'approved_at': insp_date.strftime('%Y-%m-%d %H:%M:%S'),
                'notes': 'Standard inspection completed' if inspection_passed else 'Issues found - see NCR',
                'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'updated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
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
            
            root_cause_desc = random.choice(['Material defect', 'Machine misalignment', 'Process deviation', 'Operator error', 'Environmental factor'])
            detected_qty = random.randint(1, 10)
            
            defect = {
                'defect_id': self.generate_id('DEF', 'defects'),
                'defect_code': f"D-{random.randint(100, 999)}",
                'defect_category': random.choice(defect_categories),
                'defect_type': random.choice(defect_categories),
                'defect_description': 'Component out of specification tolerance',
                'defect_severity': random.choice(defect_severities),
                'severity': random.choice(defect_severities),
                'detected_date': defect_time.strftime('%Y-%m-%d %H:%M:%S'),
                'work_order_id': work_order['work_order_id'],
                'operation_id': random.choice([op['operation_id'] for op in self.work_order_operations if op['work_order_id'] == work_order['work_order_id']]),
                'inspection_id': random.choice([qi['inspection_id'] for qi in self.quality_inspections if qi['work_order_id'] == work_order['work_order_id']]),
                'product_id': work_order['product_id'],
                'line_id': work_order['line_id'],
                'factory_id': work_order['factory_id'],
                'lot_number': work_order['lot_number'],
                'quantity_affected': detected_qty,
                'detected_quantity': detected_qty,
                'detected_by': random.choice([e['employee_id'] for e in self.employees if e['role'] in ['operator', 'quality_inspector']]),
                'detection_method': random.choice(['visual', 'measurement', 'testing']),
                'root_cause_category': random.choice(['material', 'machine', 'method', 'man', 'measurement', 'environment']),
                'root_cause': root_cause_desc,
                'root_cause_description': root_cause_desc,
                'root_cause_analysis_complete': random.random() < 0.6,
                'corrective_action': 'Adjust process parameters',
                'preventive_action': 'Implement additional checks',
                'action_owner': random.choice([e['employee_id'] for e in self.employees if e['role'] in ['supervisor', 'engineer']]),
                'action_due_date': (defect_time + timedelta(days=7)).strftime('%Y-%m-%d'),
                'action_completed': random.random() < 0.5,
                'resolved_date': (defect_time + timedelta(days=random.randint(1, 14))).strftime('%Y-%m-%d') if random.random() < 0.85 else None,
                'scrap_cost': round(random.uniform(100, 1000), 2),
                'rework_cost': round(random.uniform(50, 500), 2),
                'total_cost': round(random.uniform(150, 1500), 2),
                'status': random.choice(['open', 'in_progress', 'resolved', 'closed']),
                'closed_date': (defect_time + timedelta(days=random.randint(5, 21))).strftime('%Y-%m-%d') if random.random() < 0.80 else None,
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
        
        # Link to work order operations if available
        operations = [op for op in self.work_order_operations if op['work_order_id'] == work_order['work_order_id']]
        
        for operator in selected_operators:
            clock_in = start_time + timedelta(minutes=random.randint(-10, 10))
            duration = random.randint(120, 480)  # 2-8 hours
            clock_out = clock_in + timedelta(minutes=duration)
            
            hours_worked = round(duration / 60, 2)
            hourly_rt = round(random.uniform(15, 35), 2)
            labor_cost_per_operator = round(hours_worked * hourly_rt, 2)
            
            # Populate based on work order completion status
            is_completed = work_order['status'] in ['completed', 'closed']
            
            # Assign to sequential operations, not random
            ops_for_wo = [op for op in self.work_order_operations if op['work_order_id'] == work_order['work_order_id']]
            assigned_op_id = None
            if ops_for_wo:
                # Distribute operators across operations
                op_index = min(selected_operators.index(operator), len(ops_for_wo) - 1)
                assigned_op_id = ops_for_wo[op_index]['operation_id']
            
            labor = {
                'labor_transaction_id': self.generate_id('LT', 'labor_transactions'),
                'transaction_date': clock_in.strftime('%Y-%m-%d %H:%M:%S'),
                'employee_id': operator['employee_id'],
                'shift_id': shift['shift_id'],
                'work_order_id': work_order['work_order_id'],
                'operation_id': assigned_op_id,
                'activity_code': 'DIRECT_LABOR',
                'activity_type': 'direct_labor',
                'clock_in_time': clock_in.strftime('%Y-%m-%d %H:%M:%S'),
                'clock_out_time': clock_out.strftime('%Y-%m-%d %H:%M:%S'),
                'duration_minutes': duration,
                'break_time_minutes': 30,
                'quantity_produced': int(work_order['produced_quantity'] / num_operators) if is_completed else None,
                'quantity_rejected': int(work_order['rejected_quantity'] / num_operators) if is_completed else None,
                'standard_hours': round(duration / 60, 2),
                'actual_hours': round(duration / 60, 2),
                'efficiency_percentage': round(random.uniform(85, 110), 2),
                'hourly_rate': hourly_rt,
                'labor_cost': labor_cost_per_operator,
                'overtime_hours': 0,
                'overtime_cost': 0,
                'approved': is_completed,
                'approved_by': random.choice(self.employees)['employee_id'] if is_completed else None,
                'approved_at': (clock_out + timedelta(hours=random.randint(1, 24))).strftime('%Y-%m-%d %H:%M:%S') if is_completed else None,
                'notes': f"Labor entry for {work_order['work_order_id']}",
                'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'updated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            self.labor_transactions.append(labor)
            self.labor_counter += 1
    
    def _generate_schedule_entry(self, work_order: Dict):
        """Generate production schedule entry"""
        planned_runtime = int((datetime.strptime(work_order['planned_end_date'], '%Y-%m-%d %H:%M:%S') - datetime.strptime(work_order['planned_start_date'], '%Y-%m-%d %H:%M:%S')).total_seconds() / 3600)
        planned_downtime = random.randint(0, int(planned_runtime * 0.2))
        
        schedule = {
            'schedule_id': self.generate_id('SCH', 'schedules'),
            'schedule_date': datetime.strptime(work_order['planned_start_date'], '%Y-%m-%d %H:%M:%S').strftime('%Y-%m-%d'),
            'schedule_week': datetime.strptime(work_order['planned_start_date'], '%Y-%m-%d %H:%M:%S').isocalendar()[1],
            'shift_id': self.get_shift_for_time(work_order['factory_id'], datetime.strptime(work_order['planned_start_date'], '%Y-%m-%d %H:%M:%S'))['shift_id'],
            'line_id': work_order['line_id'],
            'factory_id': work_order['factory_id'],
            'work_order_id': work_order['work_order_id'],
            'product_id': work_order['product_id'],
            'planned_product_id': work_order['product_id'],
            'operation_id': random.choice([op['operation_id'] for op in self.work_order_operations if op['work_order_id'] == work_order['work_order_id']]) if self.work_order_operations and any(op['work_order_id'] == work_order['work_order_id'] for op in self.work_order_operations) else None,
            'sequence_number': self.schedule_counter,
            'planned_start_time': work_order['planned_start_date'],
            'planned_end_time': work_order['planned_end_date'],
            'planned_quantity': work_order['planned_quantity'],
            'planned_production_units': work_order['planned_quantity'],
            'planned_runtime_hours': planned_runtime,
            'planned_downtime_hours': planned_downtime,
            'priority': work_order['priority'],
            'customer_due_date': (datetime.strptime(work_order['planned_end_date'], '%Y-%m-%d %H:%M:%S') + timedelta(days=random.randint(1, 7))).strftime('%Y-%m-%d'),
            'material_available': True,
            'operator_available': True,
            'equipment_available': True,
            'schedule_status': work_order['status'] if work_order['status'] in ['planned', 'confirmed', 'in_progress', 'completed', 'delayed', 'cancelled'] else 'planned',
            'actual_start_time': work_order['actual_start_time'],
            'actual_end_time': work_order['actual_end_time'],
            'actual_quantity': work_order['produced_quantity'] if work_order['status'] in ['completed', 'in_progress'] else None,
            'on_time_start': random.random() < 0.85 if work_order['actual_start_time'] else None,
            'on_time_completion': random.random() < 0.80 if work_order['status'] in ['completed', 'in_progress'] else None,
            'schedule_adherence_percentage': round(random.uniform(75, 100), 2) if work_order['status'] in ['completed', 'in_progress'] else None,
            'planner_id': random.choice([e['employee_id'] for e in self.employees if e['role'] in ['manager', 'planning_coordinator']]),
            'planning_notes': random.choice([
                'Standard production run - no special requirements',
                'High priority customer order - expedited schedule',
                'Equipment maintenance window scheduled post-production',
                'Material lot requires special handling',
                'Quality inspection mandatory - sampling plan 2.5%',
                'Environmental monitoring required per compliance',
                'Changeover from previous product scheduled',
                'Operator training in progress - supervised run',
                None  # 20% chance of no notes
            ]),
            'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'updated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        self.production_schedule.append(schedule)
        self.schedule_counter += 1
    
    def _generate_ebr(self, work_order: Dict, product: Dict):
        """Generate electronic batch record"""
        batch_qty = work_order['produced_quantity']
        batch_dt = datetime.strptime(work_order['actual_start_time'], '%Y-%m-%d %H:%M:%S')
        
        ebr = {
            'ebr_id': self.generate_id('EBR', 'equipment_batch_records'),
            'batch_id': work_order['batch_number'],
            'batch_number': work_order['batch_number'],
            'batch_date': batch_dt.strftime('%Y-%m-%d'),
            'batch_quantity': batch_qty,
            'product_id': work_order['product_id'],
            'material_id': f"MAT-{random.randint(1001, 5000):05d}",
            'work_order_id': work_order['work_order_id'],
            'batch_size': batch_qty,
            'formula_id': f"FORM-{random.randint(100, 999)}",
            'formula_version': f"v{random.randint(1, 5)}.{random.randint(0, 9)}",
            'manufacturing_date': batch_dt.strftime('%Y-%m-%d'),
            'expiration_date': work_order['expiry_date'],
            'retest_date': (datetime.strptime(work_order['expiry_date'], '%Y-%m-%d') - timedelta(days=30)).strftime('%Y-%m-%d'),
            'factory_id': work_order['factory_id'],
            'manufacturing_area': f"AREA-{work_order['line_id'][-3:]}",
            'status': 'approved',
            'quality_status': 'approved',
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
            'audit_trail': json.dumps([
                {
                    'timestamp': work_order['actual_end_time'],
                    'user_id': work_order['created_by'],
                    'action': 'batch_created',
                    'details': 'Batch record created'
                },
                {
                    'timestamp': (datetime.strptime(work_order['actual_end_time'], '%Y-%m-%d %H:%M:%S') + timedelta(hours=2)).strftime('%Y-%m-%d %H:%M:%S'),
                    'user_id': random.choice([e['employee_id'] for e in self.employees if e['role'] == 'supervisor']),
                    'action': 'batch_reviewed',
                    'details': 'Batch record reviewed and approved'
                },
                {
                    'timestamp': (datetime.strptime(work_order['actual_end_time'], '%Y-%m-%d %H:%M:%S') + timedelta(hours=6)).strftime('%Y-%m-%d %H:%M:%S'),
                    'user_id': random.choice([e['employee_id'] for e in self.employees if e['role'] == 'manager']),
                    'action': 'batch_released',
                    'details': 'Batch released for distribution'
                }
            ]),
            'electronic_signature_applied': True,
            'signature_metadata': json.dumps({
                'preparer': {
                    'name': f"Operator-{random.randint(1000, 9999)}",
                    'timestamp': work_order['actual_end_time'],
                    'certificate_id': f"CERT-{random.randint(100000, 999999)}"
                },
                'reviewer': {
                    'name': f"Supervisor-{random.randint(1000, 9999)}",
                    'timestamp': (datetime.strptime(work_order['actual_end_time'], '%Y-%m-%d %H:%M:%S') + timedelta(hours=2)).strftime('%Y-%m-%d %H:%M:%S'),
                    'certificate_id': f"CERT-{random.randint(100000, 999999)}"
                },
                'approver': {
                    'name': f"Manager-{random.randint(1000, 9999)}",
                    'timestamp': (datetime.strptime(work_order['actual_end_time'], '%Y-%m-%d %H:%M:%S') + timedelta(hours=4)).strftime('%Y-%m-%d %H:%M:%S'),
                    'certificate_id': f"CERT-{random.randint(100000, 999999)}"
                }
            }),
            'notes': 'Batch completed successfully',
            'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'updated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        # Link eBR back to work order
        work_order['electronic_batch_record_id'] = ebr['ebr_id']
        
        self.electronic_batch_records.append(ebr)
        self.ebr_counter += 1
    
    
    def generate_production_lines(self):
        """Use existing production lines from base data and add enterprise scale lines"""
        print("Loading existing production lines from base data...")
        
        # Use base data production lines as starting point (19 lines)
        existing_lines = self.master_data.get('production_lines', [])
        for line in existing_lines:
            self.lines.append(line)
        
        # Add additional lines to reach enterprise scale while maintaining machine ratio
        # 211 machines ÷ 3.5 machines per line ≈ 60 lines total
        target_lines_per_factory = [16, 14, 16, 14]  # Total: 60 lines (aligned with 211 machines)
        
        factory_line_counts = {}
        for line in existing_lines:
            fac = line['factory_id']
            factory_line_counts[fac] = factory_line_counts.get(fac, 0) + 1
        
        for i, factory in enumerate(self.factories):
            existing_count = factory_line_counts.get(factory['factory_id'], 0)
            target_count = target_lines_per_factory[i]
            additional_needed = max(0, target_count - existing_count)
            
            print(f"Factory {factory['factory_name']}: {existing_count} existing + {additional_needed} new = {target_count} total lines")
            
            for line_num in range(existing_count + 1, target_count + 1):
                line = {
                    'line_id': self.generate_id('LINE', 'work_orders'),
                    'factory_id': factory['factory_id'],
                    'line_name': f"{factory['factory_name']} - Line {line_num:03d}",
                    'line_code': f"L{line_num:03d}",
                    'capacity': random.randint(50, 150),
                    'status': 'active'
                }
                self.lines.append(line)
        
        print(f"Total production lines: {len(self.lines)} (aligned with 211 machines from base data)")
    
    def generate_machines(self):
        """Use existing machines from base data and assign to production lines"""
        print("Loading existing machines from base data...")
        
        # Use machines from base data (211 total)
        base_machines = self.master_data.get('machines', [])
        print(f"Found {len(base_machines)} machines in base data")
        
        # Assign machines to production lines (average 3.5 machines per line)
        line_machine_mapping = {}
        machines_per_line = {}
        
        for machine in base_machines:
            # Use existing line assignment if available, otherwise assign to available line
            line_id = machine.get('line_id')
            if not line_id and self.lines:
                # Distribute machines evenly across lines
                min_line = min(self.lines, key=lambda l: machines_per_line.get(l['line_id'], 0))
                line_id = min_line['line_id']
                machine['line_id'] = line_id
            
            if line_id:
                machines_per_line[line_id] = machines_per_line.get(line_id, 0) + 1
                if line_id not in line_machine_mapping:
                    line_machine_mapping[line_id] = []
                line_machine_mapping[line_id].append(machine)
            
            self.machines.append(machine)
        
        print(f"Assigned {len(self.machines)} machines to {len(self.lines)} production lines")
        print(f"Average machines per line: {len(self.machines) / len(self.lines):.1f}")
    
    def generate_shifts(self):
        """Generate shifts for each factory"""
        print("Generating shifts...")
        shift_types = ['morning', 'afternoon', 'night']
        shift_hours = {
            'morning': (6, 14),
            'afternoon': (14, 22),
            'night': (22, 6)
        }
        
        for factory in self.factories:
            for shift_type in shift_types:
                shift = {
                    'shift_id': self.generate_id('SHF', 'work_orders'),
                    'factory_id': factory['factory_id'],
                    'shift_name': f"{shift_type.title()} Shift",
                    'shift_code': shift_type[:3].upper(),
                    'start_time': f"{shift_hours[shift_type][0]:02d}:00",
                    'end_time': f"{shift_hours[shift_type][1]:02d}:00",
                    'days_of_week': 'mon,tue,wed,thu,fri,sat,sun',
                    'status': 'active'
                }
                self.shifts.append(shift)
        print(f"Generated {len(self.shifts)} shifts")
    
    def generate_line_product_mapping(self):
        """Generate mapping of products that can be produced on each line"""
        print("Generating line-product mappings...")
        
        # Each line can produce 3-5 different products
        for line in self.lines:
            num_products = random.randint(3, min(5, len(self.products)))
            line_products = random.sample(self.products, num_products)
            
            for product in line_products:
                mapping = {
                    'mapping_id': self.generate_id('MAP', 'work_orders'),
                    'factory_id': line['factory_id'],
                    'line_id': line['line_id'],
                    'product_id': product['product_id'],
                    'min_batch_size': random.randint(10, 50),
                    'max_batch_size': random.randint(100, 500),
                    'setup_time_minutes': random.randint(15, 120),
                    'changeover_time_minutes': random.randint(30, 180)
                }
                self.line_product_mapping.append(mapping)
        
        print(f"Generated {len(self.line_product_mapping)} line-product mappings")
    
    def generate_all_data(self):
        """Generate all MES historical data"""
        start_date = datetime.now() - timedelta(days=DAYS_OF_HISTORY)
        
        print(f"\n{'='*80}")
        print(f"Generating {DAYS_OF_HISTORY} days of MES historical data")
        print(f"Start: {start_date.strftime('%Y-%m-%d')}")
        print(f"End: {datetime.now().strftime('%Y-%m-%d')}")
        print(f"{'='*80}\n")
        
        # Generate master data first
        self.generate_production_lines()
        self.generate_machines()
        self.generate_shifts()
        self.generate_line_product_mapping()
        
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
        """Export data to JSON with all schema tables"""
        print(f"\nExporting data to JSON: {output_file}...")
        
        # Generate missing tables
        changeover_events = self._generate_changeover_events()
        downtime_events = self._generate_downtime_events()
        
        data = {
            'work_orders': self.work_orders,
            'work_order_operations': self.work_order_operations,
            'material_transactions': self.material_transactions,
            'quality_inspections': self.quality_inspections,
            'defects': self.defects,
            'labor_transactions': self.labor_transactions,
            'production_schedule': self.production_schedule,
            'electronic_batch_records': self.electronic_batch_records,
            'changeover_events': changeover_events,
            'downtime_events': downtime_events
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        
        print(f"Data exported to {output_file}")
    
    def _generate_changeover_events(self):
        """Generate changeover event records"""
        changeover_events = []
        for i in range(25):
            start_time = datetime.now() - timedelta(days=random.randint(0, 30), hours=random.randint(0, 23))
            end_time = start_time + timedelta(minutes=random.randint(15, 120))
            duration_mins = random.randint(15, 120)
            
            changeover_events.append({
                'changeover_id': self.generate_id('CHG', 'changeovers'),
                'line_id': random.choice([pl['line_id'] for pl in self.lines[:10]]) if self.lines else 'L-001',
                'machine_id': f"MACH-{random.randint(1, 50):06d}",
                'changeover_type': random.choice(['product_change', 'tool_change', 'adjustment', 'quality_setup']),
                'from_product_id': random.choice([p['product_id'] for p in self.products[:10]]) if self.products else 'P-001',
                'to_product_id': random.choice([p['product_id'] for p in self.products[:10]]) if self.products else 'P-001',
                'from_work_order_id': f"WO-{random.randint(1000, 9999)}",
                'to_work_order_id': f"WO-{random.randint(1000, 9999)}",
                'changeover_start': start_time.strftime('%Y-%m-%d %H:%M:%S'),
                'changeover_end': end_time.strftime('%Y-%m-%d %H:%M:%S'),
                'planned_duration_minutes': duration_mins,
                'actual_duration_minutes': duration_mins + random.randint(-5, 15),
                'teardown_time_minutes': random.randint(5, 30),
                'setup_time_minutes': random.randint(10, 60),
                'adjustment_time_minutes': random.randint(0, 20),
                'trial_run_time_minutes': random.randint(5, 15),
                'first_good_part_time': start_time.strftime('%Y-%m-%d %H:%M:%S'),
                'parts_produced_during_setup': random.randint(5, 50),
                'parts_scrapped_during_setup': random.randint(0, 20),
                'supervisor_id': f"EMP-{random.randint(1, 100):06d}",
                'operator_ids': f"EMP-{random.randint(1, 100):06d},EMP-{random.randint(1, 100):06d}",
                'first_piece_inspection_passed': random.choice([True, False]),
                'quality_approval_by': f"EMP-{random.randint(1, 100):06d}",
                'target_changeover_time_minutes': duration_mins,
                'improvement_opportunity': random.choice(['reduce_teardown', 'reduce_setup', 'parallel_operations', 'reduce_trial_run', 'reduce_adjustment']) if random.random() < 0.85 else None,
                'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            })
        return changeover_events
    
    def _generate_downtime_events(self):
        """Generate downtime event records"""
        downtime_events = []
        downtime_reasons = ['equipment_failure', 'material_shortage', 'quality_issue', 'tooling_problem', 'maintenance', 'scheduling']
        for i in range(20):
            start_time = datetime.now() - timedelta(days=random.randint(0, 30), hours=random.randint(0, 23))
            duration_minutes = random.randint(10, 480)
            end_time = start_time + timedelta(minutes=duration_minutes)
            
            downtime_events.append({
                'downtime_id': self.generate_id('DT', 'downtime_records'),
                'machine_id': f"MACH-{random.randint(1, 50):06d}",
                'line_id': random.choice([pl['line_id'] for pl in self.lines[:10]]) if self.lines else 'L-001',
                'factory_id': random.choice([pl['factory_id'] for pl in self.lines[:10]]) if self.lines else 'FAC-001',
                'downtime_start': start_time.strftime('%Y-%m-%d %H:%M:%S'),
                'downtime_end': end_time.strftime('%Y-%m-%d %H:%M:%S'),
                'duration_minutes': duration_minutes,
                'downtime_type': random.choice(['planned_maintenance', 'unplanned_breakdown', 'operator_error', 'material_shortage', 'quality_hold']),
                'downtime_category': random.choice(['mechanical', 'electrical', 'hydraulic', 'software', 'material', 'operator']),
                'downtime_reason': random.choice(downtime_reasons),
                'root_cause_category': random.choice(['equipment_failure', 'material_issue', 'operator_error', 'maintenance', 'setup', 'quality']),
                'root_cause_code': f"RC-{random.randint(1000, 9999)}",
                'root_cause_description': f"Root cause {random.randint(1, 100)}",
                'is_planned': random.choice([True, False]),
                'responsible_person_id': f"EMP-{random.randint(1, 100):06d}",
                'responsible_department': random.choice(['Maintenance', 'Production', 'Quality', 'Engineering']),
                'impact_description': f"Production impact: {random.randint(10, 100)} units affected",
                'impact_production_units': random.randint(0, 500),
                'impact_quality_rejects': random.randint(0, 50),
                'recovery_notes': f"Downtime resolution {7001+i}",
                'resolution_notes': f"Downtime resolution {7001+i}",
                'status': random.choice(['resolved', 'investigating', 'escalated']),
                'updated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            })
        return downtime_events


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
    
    # Export to JSON (in same folder as script) - use correct genims name
    json_file = script_dir / "genims_mes_data.json"
    generator.to_json(str(json_file))
    
    print("\n" + "="*80)
    print("MES Historical Data Generation Complete!")
    print("Files created:")
    print("  1. mes_historical_data_inserts.sql - SQL INSERT statements")
    print("  2. mes_historical_data.json - JSON export")
    print("="*80)
