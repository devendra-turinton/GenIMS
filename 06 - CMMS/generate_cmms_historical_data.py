#!/usr/bin/env python3
"""
GenIMS CMMS Historical Data Generator
Generates 90 days of maintenance history
"""

import random
import json
from datetime import datetime, timedelta
from typing import List, Dict

# Configuration
DAYS_OF_HISTORY = 90
ASSETS_PER_FACTORY = 20
TECHNICIANS_PER_FACTORY = 10
MRO_PARTS_COUNT = 200
PM_SCHEDULES_PER_ASSET = 2
WORK_ORDERS_PER_DAY = (3, 10)

class CMM

SDataGenerator:
    def __init__(self, master_data_file='genims_master_data.json'):
        """Initialize with master data"""
        print("Loading master data...")
        
        with open(master_data_file, 'r') as f:
            self.master_data = json.load(f)
        
        self.factories = self.master_data['factories']
        self.machines = self.master_data['machines']
        
        # CMMS Data
        self.assets = []
        self.technicians = []
        self.teams = []
        self.mro_parts = []
        self.pm_schedules = []
        self.work_orders = []
        self.wo_tasks = []
        self.parts_transactions = []
        self.labor_entries = []
        self.meter_readings = []
        self.failure_codes = []
        self.maintenance_history = []
        
        # Counters
        self.counters = {
            'asset': 1, 'tech': 1, 'team': 1, 'part': 1,
            'pm': 1, 'wo': 1, 'task': 1, 'trans': 1,
            'labor': 1, 'meter': 1, 'failure': 1, 'history': 1
        }
        
        print(f"Loaded: {len(self.factories)} factories, {len(self.machines)} machines")
    
    def generate_id(self, prefix: str, counter_key: str) -> str:
        id_val = f"{prefix}-{str(self.counters[counter_key]).zfill(6)}"
        self.counters[counter_key] += 1
        return id_val
    
    def generate_all_data(self):
        """Generate all CMMS data"""
        print(f"\n{'='*80}")
        print(f"Generating CMMS Data ({DAYS_OF_HISTORY} days of history)")
        print(f"{'='*80}\n")
        
        # Master Data
        self.generate_failure_codes()
        self.generate_assets()
        self.generate_technicians()
        self.generate_mro_parts()
        self.generate_pm_schedules()
        
        # Historical Operations (90 days)
        start_date = datetime.now() - timedelta(days=DAYS_OF_HISTORY)
        self.generate_maintenance_operations(start_date, DAYS_OF_HISTORY)
        
        self._print_summary()
    
    # ========================================================================
    # MASTER DATA
    # ========================================================================
    
    def generate_failure_codes(self):
        """Generate failure classification codes"""
        print("Generating failure codes...")
        
        failures = [
            {'class': 'mechanical', 'type': 'wear', 'desc': 'Bearing Wear'},
            {'class': 'mechanical', 'type': 'fatigue', 'desc': 'Metal Fatigue'},
            {'class': 'mechanical', 'type': 'misalignment', 'desc': 'Shaft Misalignment'},
            {'class': 'electrical', 'type': 'overload', 'desc': 'Motor Overload'},
            {'class': 'electrical', 'type': 'short_circuit', 'desc': 'Electrical Short'},
            {'class': 'hydraulic', 'type': 'leak', 'desc': 'Hydraulic Leak'},
            {'class': 'hydraulic', 'type': 'contamination', 'desc': 'Oil Contamination'},
            {'class': 'pneumatic', 'type': 'leak', 'desc': 'Air Leak'},
            {'class': 'software', 'type': 'malfunction', 'desc': 'PLC Error'},
            {'class': 'operator_error', 'type': 'improper_use', 'desc': 'Operator Mistake'}
        ]
        
        for f in failures:
            code = {
                'failure_code_id': self.generate_id('FC', 'failure'),
                'failure_code': f"FC-{self.counters['failure']-1:03d}",
                'failure_description': f['desc'],
                'failure_class': f['class'],
                'failure_type': f['type'],
                'severity': random.choice(['critical', 'major', 'moderate', 'minor']),
                'typical_repair_time_hours': round(random.uniform(1, 24), 2),
                'is_active': True,
                'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            self.failure_codes.append(code)
        
        print(f"Generated {len(self.failure_codes)} failure codes")
    
    def generate_assets(self):
        """Generate maintenance assets"""
        print("Generating maintenance assets...")
        
        asset_types = ['machine', 'equipment', 'vehicle', 'facility', 'instrument']
        
        for factory in self.factories:
            # Link production machines
            factory_machines = [m for m in self.machines if m.get('factory_id') == factory['factory_id']]
            
            for machine in factory_machines[:ASSETS_PER_FACTORY]:
                asset = {
                    'asset_id': self.generate_id('AST', 'asset'),
                    'asset_number': f"AST-{self.counters['asset']-1:05d}",
                    'asset_name': machine['machine_name'],
                    'asset_type': 'machine',
                    'asset_category': 'production',
                    'asset_class': random.choice(['critical', 'essential', 'important']),
                    'machine_id': machine['machine_id'],
                    'factory_id': factory['factory_id'],
                    'line_id': machine.get('line_id'),
                    'manufacturer': random.choice(['Siemens', 'Fanuc', 'Haas', 'DMG Mori']),
                    'model_number': f"MDL-{random.randint(1000, 9999)}",
                    'serial_number': f"SN{random.randint(100000, 999999)}",
                    'installation_date': (datetime.now() - timedelta(days=random.randint(365, 3650))).strftime('%Y-%m-%d'),
                    'criticality_rating': random.choice(['critical', 'high', 'medium']),
                    'safety_critical': random.choice([True, False]),
                    'production_critical': True,
                    'maintenance_strategy': random.choice(['preventive', 'predictive', 'corrective']),
                    'pm_frequency_type': 'calendar',
                    'has_meter': True,
                    'meter_unit': 'hours',
                    'current_meter_reading': round(random.uniform(5000, 50000), 2),
                    'asset_condition': random.choice(['excellent', 'good', 'fair']),
                    'asset_status': 'operational',
                    'downtime_cost_per_hour': round(random.uniform(5000, 50000), 2),
                    'is_active': True,
                    'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                self.assets.append(asset)
        
        print(f"Generated {len(self.assets)} maintenance assets")
    
    def generate_technicians(self):
        """Generate maintenance technicians"""
        print("Generating maintenance technicians...")
        
        trades = ['mechanical', 'electrical', 'instrumentation', 'multi_craft']
        skill_levels = ['technician', 'senior_technician', 'specialist']
        
        for factory in self.factories:
            for i in range(TECHNICIANS_PER_FACTORY):
                tech = {
                    'technician_id': self.generate_id('TECH', 'tech'),
                    'technician_code': f"TECH{self.counters['tech']-1:04d}",
                    'first_name': f"Tech{i+1}",
                    'last_name': factory['factory_code'],
                    'hire_date': (datetime.now() - timedelta(days=random.randint(365, 3650))).strftime('%Y-%m-%d'),
                    'skill_level': random.choice(skill_levels),
                    'trade': random.choice(trades),
                    'certifications': json.dumps(['forklift', 'electrical_license']),
                    'primary_shift': random.choice(['day', 'evening', 'night']),
                    'hourly_rate': round(random.uniform(500, 2000), 2),
                    'overtime_rate': round(random.uniform(750, 3000), 2),
                    'technician_status': 'available',
                    'is_active': True,
                    'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                self.technicians.append(tech)
        
        print(f"Generated {len(self.technicians)} technicians")
    
    def generate_mro_parts(self):
        """Generate MRO spare parts"""
        print("Generating MRO spare parts...")
        
        part_types = ['mechanical', 'electrical', 'hydraulic', 'pneumatic', 'electronic']
        part_categories = ['spare_part', 'consumable']
        
        for i in range(MRO_PARTS_COUNT):
            part = {
                'mro_part_id': self.generate_id('MRO', 'part'),
                'part_number': f"MRO-{self.counters['part']-1:05d}",
                'part_name': f"Spare Part {i+1}",
                'part_category': random.choice(part_categories),
                'part_type': random.choice(part_types),
                'unit_of_measure': random.choice(['EA', 'SET', 'L', 'KG']),
                'current_stock': random.randint(0, 100),
                'min_stock_level': random.randint(5, 20),
                'max_stock_level': random.randint(50, 150),
                'reorder_point': random.randint(10, 30),
                'reorder_quantity': random.randint(20, 50),
                'criticality': random.choice(['critical', 'high', 'medium', 'low']),
                'lead_time_days': random.randint(7, 60),
                'standard_cost': round(random.uniform(100, 10000), 2),
                'part_status': 'active',
                'is_active': True,
                'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            self.mro_parts.append(part)
        
        print(f"Generated {len(self.mro_parts)} MRO parts")
    
    def generate_pm_schedules(self):
        """Generate PM schedules"""
        print("Generating PM schedules...")
        
        for asset in self.assets[:50]:  # PM for first 50 assets
            for pm_num in range(PM_SCHEDULES_PER_ASSET):
                schedule = {
                    'pm_schedule_id': self.generate_id('PM', 'pm'),
                    'schedule_code': f"PM-{asset['asset_number']}-{pm_num+1:02d}",
                    'schedule_name': f"{asset['asset_name']} - Schedule {pm_num+1}",
                    'asset_id': asset['asset_id'],
                    'schedule_type': random.choice(['calendar', 'meter_based']),
                    'frequency_type': random.choice(['weekly', 'monthly', 'quarterly']),
                    'frequency_value': random.choice([1, 2, 3, 6]),
                    'frequency_unit': 'months',
                    'meter_frequency': random.randint(500, 2000) if random.random() > 0.5 else None,
                    'pm_type': random.choice(['inspection', 'service', 'calibration']),
                    'estimated_duration_hours': round(random.uniform(2, 8), 2),
                    'lead_time_days': random.randint(3, 14),
                    'auto_generate_wo': True,
                    'next_due_date': (datetime.now() + timedelta(days=random.randint(1, 60))).strftime('%Y-%m-%d'),
                    'schedule_status': 'active',
                    'is_active': True,
                    'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                self.pm_schedules.append(schedule)
        
        print(f"Generated {len(self.pm_schedules)} PM schedules")
    
    # ========================================================================
    # MAINTENANCE OPERATIONS
    # ========================================================================
    
    def generate_maintenance_operations(self, start_date: datetime, days: int):
        """Generate daily maintenance operations"""
        print(f"Generating {days} days of maintenance operations...")
        
        current_date = start_date
        
        for day in range(days):
            num_wos = random.randint(*WORK_ORDERS_PER_DAY)
            
            for _ in range(num_wos):
                self._create_work_order(current_date)
            
            current_date += timedelta(days=1)
        
        print(f"Generated {len(self.work_orders)} work orders with {len(self.wo_tasks)} tasks")
    
    def _create_work_order(self, date: datetime):
        """Create work order"""
        if not self.assets:
            return
        
        asset = random.choice(self.assets)
        wo_type = random.choice(['preventive', 'corrective', 'breakdown', 'inspection'])
        
        wo = {
            'work_order_id': self.generate_id('WO', 'wo'),
            'work_order_number': f"WO-{date.strftime('%Y%m%d')}-{self.counters['wo']:04d}",
            'asset_id': asset['asset_id'],
            'wo_type': wo_type,
            'priority': random.choice(['emergency', 'urgent', 'high', 'medium', 'low']),
            'description': f"{wo_type.title()} maintenance for {asset['asset_name']}",
            'problem_description': f"Routine {wo_type} work",
            'failure_code': random.choice(self.failure_codes)['failure_code'] if self.failure_codes else None,
            'scheduled_start_date': date.strftime('%Y-%m-%d'),
            'scheduled_end_date': (date + timedelta(hours=random.randint(4, 24))).strftime('%Y-%m-%d'),
            'estimated_duration_hours': round(random.uniform(2, 8), 2),
            'actual_start_date': date.strftime('%Y-%m-%d %H:%M:%S'),
            'actual_end_date': (date + timedelta(hours=random.randint(2, 8))).strftime('%Y-%m-%d %H:%M:%S'),
            'actual_duration_hours': round(random.uniform(2, 8), 2),
            'wo_status': random.choice(['completed', 'completed', 'completed', 'in_progress']),
            'assigned_to': random.choice(self.technicians)['technician_id'] if self.technicians else None,
            'downtime_minutes': random.randint(0, 480) if wo_type == 'breakdown' else 0,
            'estimated_cost': round(random.uniform(1000, 20000), 2),
            'actual_total_cost': round(random.uniform(1000, 20000), 2),
            'created_at': date.strftime('%Y-%m-%d %H:%M:%S')
        }
        self.work_orders.append(wo)
        
        # Create tasks
        self._create_wo_tasks(wo, date)
        
        # Create parts usage
        self._create_parts_transaction(wo, date)
        
        # Create labor entry
        self._create_labor_entry(wo, date)
        
        # Create history
        self._create_maintenance_history(wo, asset, date)
    
    def _create_wo_tasks(self, wo: dict, date: datetime):
        """Create work order tasks"""
        num_tasks = random.randint(2, 5)
        
        task_types = ['inspection', 'replacement', 'adjustment', 'cleaning', 'lubrication']
        
        for seq in range(1, num_tasks + 1):
            task = {
                'task_id': self.generate_id('TASK', 'task'),
                'work_order_id': wo['work_order_id'],
                'task_sequence': seq,
                'task_description': f"Task {seq}: {random.choice(task_types).title()}",
                'task_type': random.choice(task_types),
                'estimated_duration_minutes': random.randint(30, 180),
                'actual_duration_minutes': random.randint(30, 180),
                'task_status': 'completed' if wo['wo_status'] == 'completed' else 'pending',
                'task_result': 'pass',
                'created_at': date.strftime('%Y-%m-%d %H:%M:%S')
            }
            self.wo_tasks.append(task)
    
    def _create_parts_transaction(self, wo: dict, date: datetime):
        """Create parts transaction"""
        if not self.mro_parts:
            return
        
        # Use 1-3 parts per WO
        for _ in range(random.randint(1, 3)):
            part = random.choice(self.mro_parts)
            qty = random.randint(1, 5)
            
            trans = {
                'transaction_id': self.generate_id('PTRANS', 'trans'),
                'transaction_number': f"PT-{date.strftime('%Y%m%d')}-{self.counters['trans']:05d}",
                'mro_part_id': part['mro_part_id'],
                'transaction_type': 'issue',
                'transaction_date': date.strftime('%Y-%m-%d %H:%M:%S'),
                'quantity': qty,
                'unit_of_measure': part['unit_of_measure'],
                'unit_cost': part['standard_cost'],
                'total_cost': round(qty * part['standard_cost'], 2),
                'work_order_id': wo['work_order_id'],
                'asset_id': wo['asset_id'],
                'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            self.parts_transactions.append(trans)
    
    def _create_labor_entry(self, wo: dict, date: datetime):
        """Create labor time entry"""
        if not self.technicians or not wo.get('assigned_to'):
            return
        
        tech = next((t for t in self.technicians if t['technician_id'] == wo['assigned_to']), None)
        if not tech:
            return
        
        hours = wo['actual_duration_hours']
        
        entry = {
            'entry_id': self.generate_id('LABOR', 'labor'),
            'work_order_id': wo['work_order_id'],
            'technician_id': tech['technician_id'],
            'start_time': wo['actual_start_date'],
            'end_time': wo['actual_end_date'],
            'duration_hours': hours,
            'labor_type': 'regular',
            'hourly_rate': tech['hourly_rate'],
            'labor_cost': round(hours * tech['hourly_rate'], 2),
            'approved': True,
            'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        self.labor_entries.append(entry)
    
    def _create_maintenance_history(self, wo: dict, asset: dict, date: datetime):
        """Create maintenance history record"""
        history = {
            'history_id': self.generate_id('HIST', 'history'),
            'asset_id': asset['asset_id'],
            'event_type': 'work_order_completed',
            'event_date': wo['actual_end_date'],
            'event_description': wo['description'],
            'work_order_id': wo['work_order_id'],
            'failure_code': wo.get('failure_code'),
            'downtime_hours': round(wo.get('downtime_minutes', 0) / 60, 2),
            'total_cost': wo.get('actual_total_cost'),
            'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        self.maintenance_history.append(history)
    
    def _print_summary(self):
        print(f"\n{'='*80}")
        print(f"CMMS Data Generation Complete!")
        print(f"{'='*80}")
        print(f"\nMaster Data:")
        print(f"  Assets: {len(self.assets)}")
        print(f"  Technicians: {len(self.technicians)}")
        print(f"  MRO Parts: {len(self.mro_parts)}")
        print(f"  PM Schedules: {len(self.pm_schedules)}")
        print(f"  Failure Codes: {len(self.failure_codes)}")
        
        print(f"\nOperational Data ({DAYS_OF_HISTORY} days):")
        print(f"  Work Orders: {len(self.work_orders)}")
        print(f"  Work Order Tasks: {len(self.wo_tasks)}")
        print(f"  Parts Transactions: {len(self.parts_transactions)}")
        print(f"  Labor Entries: {len(self.labor_entries)}")
        print(f"  Maintenance History: {len(self.maintenance_history)}")
    
    def to_json(self, output_file='cmms_historical_data.json'):
        """Export to JSON"""
        print(f"\nExporting to JSON...")
        
        data = {
            'metadata': {
                'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'days_of_history': DAYS_OF_HISTORY
            },
            'master_data': {
                'assets': self.assets[:50],  # Sample
                'technicians': self.technicians,
                'mro_parts': self.mro_parts[:50],  # Sample
                'pm_schedules': self.pm_schedules,
                'failure_codes': self.failure_codes
            },
            'operational_data': {
                'work_orders': self.work_orders[:100],  # Sample
                'wo_tasks': self.wo_tasks[:200],  # Sample
                'parts_transactions': self.parts_transactions[:100],
                'labor_entries': self.labor_entries[:100],
                'maintenance_history': self.maintenance_history[:100]
            }
        }
        
        with open(output_file, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"Data exported to {output_file}")


if __name__ == "__main__":
    generator = CMM SDataGenerator()
    generator.generate_all_data()
    generator.to_json()
    
    print("\n" + "="*80)
    print("CMMS Historical Data Generation Complete!")
    print("="*80)
