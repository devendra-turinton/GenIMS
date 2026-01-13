#!/usr/bin/env python3
"""
GenIMS CMMS Historical Data Generator with ULTRA-FAST PARALLEL Processing
Generates 180 days of maintenance history with referential integrity
Includes ultra-fast parallel processing optimizations
"""

import random
import json
import os
from datetime import datetime, timedelta
from typing import List, Dict
import sys
from pathlib import Path
import logging
import psycopg2
from psycopg2.extras import RealDictCursor
import multiprocessing
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

# Add scripts to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))
from generator_helper import get_helper

# ULTRA-FAST PARALLEL Configuration
cpu_count = multiprocessing.cpu_count()
WORKER_COUNT = min(8, max(4, cpu_count - 2))  # Use 8 workers or available CPUs minus 2
BATCH_SIZE = 150000  # Large batch size for optimal performance

# Configuration
DAYS_OF_HISTORY = 180
ASSETS_PER_FACTORY = 80   # Increased from 20 to 80 per factory (4x)
TECHNICIANS_PER_FACTORY = 40  # Increased from 10 to 40 per factory (4x)
MRO_PARTS_COUNT = 800     # Increased from 200 to 800 (4x parts catalog)
PM_SCHEDULES_PER_ASSET = 4  # More preventive maintenance schedules per asset
WORK_ORDERS_PER_DAY = (150, 300)  # Enterprise maintenance volume (37-75 WOs per factory)

# Database configuration
PG_HOST = os.getenv('POSTGRES_HOST', 'insights-db.postgres.database.azure.com')
PG_PORT = int(os.getenv('POSTGRES_PORT', '5432'))
PG_USER = os.getenv('POSTGRES_USER', 'turintonadmin')
PG_PASSWORD = os.getenv('POSTGRES_PASSWORD', 'Passw0rd123!')
CMMS_DB = os.getenv('DB_MAINTENANCE', 'genims_maintenance_db')
MASTER_DB = os.getenv('DB_MASTER', 'genims_master_db')
ERP_DB = os.getenv('DB_ERP', 'genims_erp_db')
WMS_DB = os.getenv('DB_WMS', 'genims_wms_db')
MES_DB = os.getenv('DB_MANUFACTURING', 'genims_manufacturing_db')

# Logging setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class CMMSDataGenerator:
    def __init__(self, master_data_file=None):
        """Initialize with master data and registry"""
        from pathlib import Path
        
        # Initialize master data
        self.factories = []
        self.employees = []
        self.production_lines = []
        self.machines = []
        self.warehouses = []
        self.suppliers = []
        
        # Try to load from JSON file first (preferred during setup)
        if master_data_file is None:
            master_data_file = Path(__file__).parent.parent / "01 - Base Data" / "genims_master_data.json"
        
        # Load master data: prioritize JSON file, fallback to database
        if Path(master_data_file).exists():
            self.load_master_data_from_json(master_data_file)
        else:
            logger.info("JSON master data not found, attempting database connections...")
            self.load_master_data_from_databases()
        
        # Load helper for FK validation
        self.helper = get_helper()
        self.registry = self.helper.registry
        
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
        
        # ULTRA-FAST PARALLEL Configuration
        self.worker_count = WORKER_COUNT
        self.batch_size = BATCH_SIZE
        self.parallel_enabled = True
        self.data_lock = threading.Lock()
        
        logger.info(f"Loaded: {len(self.factories)} factories, {len(self.machines)} machines, {len(self.production_lines)} lines")
        
        print(f"🚀 ULTRA-FAST CMMS PARALLEL MODE: {self.worker_count} workers, batch_size={self.batch_size:,}")
        print(f"   CPU cores available: {cpu_count}, Using {self.worker_count} for generation")
    
    def load_master_data_from_json(self, master_data_file):
        """Load master data from JSON file (preferred during setup)"""
        try:
            logger.info(f"Loading master data from JSON: {master_data_file}")
            
            with open(master_data_file, 'r') as f:
                master_data = json.load(f)
            
            # Load core data
            self.factories = master_data.get('factories', [])
            self.employees = master_data.get('employees', [])
            self.production_lines = master_data.get('production_lines', [])
            self.machines = master_data.get('machines', [])
            
            # Generate minimal external data if not available
            self.warehouses = master_data.get('warehouses', [
                {'warehouse_id': 'WH-000001', 'warehouse_name': 'Main Warehouse', 'warehouse_type': 'finished_goods'},
                {'warehouse_id': 'WH-000002', 'warehouse_name': 'Parts Warehouse', 'warehouse_type': 'raw_materials'}
            ])
            
            self.suppliers = master_data.get('suppliers', [
                {'supplier_id': 'SUP-000001', 'supplier_name': 'Main Parts Supplier', 'supplier_type': 'spare_parts'},
                {'supplier_id': 'SUP-000002', 'supplier_name': 'Equipment Supplier', 'supplier_type': 'equipment'}
            ])
            
            logger.info(f"Successfully loaded from JSON: {len(self.factories)} factories, {len(self.machines)} machines, {len(self.production_lines)} lines")
            
        except Exception as e:
            logger.error(f"Failed to load from JSON: {e}")
            logger.info("Attempting database connections as fallback...")
            self.load_master_data_from_databases()
    
    def load_master_data_from_databases(self):
        """Load master data from source databases"""
        try:
            logger.info(f"Attempting to connect to databases on {PG_HOST}...")
            
            # Connect to master_db for factories and machines
            master_conn = psycopg2.connect(
                host=PG_HOST, port=PG_PORT, database=MASTER_DB, 
                user=PG_USER, password=PG_PASSWORD,
                sslmode='require', cursor_factory=RealDictCursor
            )
            
            with master_conn.cursor() as master_cursor:
                # Load factories
                master_cursor.execute("SELECT * FROM factories LIMIT 100")
                self.factories = [dict(row) for row in master_cursor.fetchall()]
                
                # Load machines
                master_cursor.execute("SELECT * FROM machines LIMIT 500")
                self.machines = [dict(row) for row in master_cursor.fetchall()]
                
                # Load production lines
                master_cursor.execute("SELECT * FROM production_lines LIMIT 100")
                self.production_lines = [dict(row) for row in master_cursor.fetchall()]
                
                # Load employees (for technicians base)
                master_cursor.execute("SELECT * FROM employees WHERE department = 'maintenance' LIMIT 100")
                self.employees = [dict(row) for row in master_cursor.fetchall()]
                
                logger.info(f"Loaded from master_db: {len(self.factories)} factories, {len(self.machines)} machines")
            
            # Try to load suppliers and warehouses from other databases
            try:
                # Connect to ERP for suppliers
                erp_conn = psycopg2.connect(
                    host=PG_HOST, port=PG_PORT, database=ERP_DB,
                    user=PG_USER, password=PG_PASSWORD,
                    sslmode='require', cursor_factory=RealDictCursor
                )
                
                with erp_conn.cursor() as erp_cursor:
                    erp_cursor.execute("SELECT supplier_id, supplier_name, supplier_type FROM suppliers WHERE supplier_type = 'spare_parts' AND is_active = true LIMIT 50")
                    self.suppliers = [dict(row) for row in erp_cursor.fetchall()]
                
                erp_conn.close()
                logger.info(f"Loaded {len(self.suppliers)} suppliers from ERP")
                
            except Exception as e:
                logger.warning(f"Could not load from ERP database: {e}. Using default suppliers.")
                self.suppliers = [
                    {'supplier_id': 'SUP-000001', 'supplier_name': 'Main Parts Supplier', 'supplier_type': 'spare_parts'},
                    {'supplier_id': 'SUP-000002', 'supplier_name': 'Equipment Supplier', 'supplier_type': 'equipment'}
                ]
                
            try:
                # Connect to WMS for warehouses
                wms_conn = psycopg2.connect(
                    host=PG_HOST, port=PG_PORT, database=WMS_DB,
                    user=PG_USER, password=PG_PASSWORD,
                    sslmode='require', cursor_factory=RealDictCursor
                )
                
                with wms_conn.cursor() as wms_cursor:
                    wms_cursor.execute("SELECT warehouse_id, warehouse_name, warehouse_type FROM warehouses WHERE is_active = true LIMIT 50")
                    self.warehouses = [dict(row) for row in wms_cursor.fetchall()]
                
                wms_conn.close()
                logger.info(f"Loaded {len(self.warehouses)} warehouses from WMS")
                
            except Exception as e:
                logger.warning(f"Could not load from WMS database: {e}. Using default warehouses.")
                self.warehouses = [
                    {'warehouse_id': 'WH-000001', 'warehouse_name': 'Main Warehouse', 'warehouse_type': 'finished_goods'},
                    {'warehouse_id': 'WH-000002', 'warehouse_name': 'Parts Warehouse', 'warehouse_type': 'raw_materials'}
                ]
                
        except Exception as e:
            logger.error(f"Error loading master data: {e}")
            # Fallback to default data
            self._load_fallback_data()
        finally:
            if 'master_conn' in locals():
                master_conn.close()
    
    def _load_fallback_data(self):
        """Load fallback data if databases are not available"""
        logger.warning("Using fallback master data")
        
        # Minimal fallback factories
        self.factories = [
            {'factory_id': 'FAC-000001', 'factory_name': 'Main Plant', 'factory_code': 'MP'},
            {'factory_id': 'FAC-000002', 'factory_name': 'Secondary Plant', 'factory_code': 'SP'}
        ]
        
        # Generate basic machines
        machine_types = ['pump', 'compressor', 'motor', 'conveyor']
        for factory in self.factories:
            for i in range(5):  # 5 machines per factory
                self.machines.append({
                    'machine_id': f"MCH-{factory['factory_code']}-{i+1:03d}",
                    'factory_id': factory['factory_id'],
                    'machine_name': f"{factory['factory_name']} Equipment {i+1}",
                    'machine_type': random.choice(machine_types)
                })
    
    def generate_id(self, prefix: str, counter_key: str) -> str:
        id_val = f"{prefix}-{str(self.counters[counter_key]).zfill(6)}"
        self.counters[counter_key] += 1
        return id_val
    
    def generate_all_data(self):
        """Generate all CMMS data"""
        logger.info(f"\n{'='*80}")
        logger.info(f"Generating CMMS Data ({DAYS_OF_HISTORY} days of history)")
        logger.info(f"{'='*80}\n")
        
        # Master Data
        self.generate_machines()
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
    
    def generate_machines(self):
        """Use machines from master database - no generation needed"""
        logger.info(f"Using {len(self.machines)} machines from master database")
        
        # If no machines loaded, generate minimal ones
        if not self.machines:
            logger.warning("No machines found in master database, generating basic ones")
            machine_types = ['pump', 'compressor', 'motor', 'conveyor', 'press']
            
            for factory in self.factories:
                for i in range(ASSETS_PER_FACTORY):
                    machine = {
                        'machine_id': self.generate_id('MCH', 'asset'),
                        'factory_id': factory['factory_id'],
                        'line_id': random.choice(self.production_lines)['line_id'] if self.production_lines else None,
                        'machine_name': f"{factory['factory_name']} - Equipment {i+1}",
                        'machine_type': random.choice(machine_types),
                        'manufacturer': random.choice(['Siemens', 'ABB', 'Mitsubishi', 'FANUC', 'Bosch']),
                        'model': f"MD-{random.randint(100, 999)}",
                        'serial_number': f"SN-{factory['factory_id']}-{i+1:04d}",
                        'install_date': (datetime.now() - timedelta(days=random.randint(365, 1825))).strftime('%Y-%m-%d'),
                        'status': random.choice(['operational', 'under_maintenance', 'idle'])
                    }
                    self.machines.append(machine)
    
    def generate_failure_codes(self):
        """Generate failure classification codes"""
        logger.info("Generating failure codes...")
        
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
        
        logger.info(f"Generated {len(self.failure_codes)} failure codes")
    
    def generate_assets(self):
        """Generate maintenance assets"""
        logger.info("Generating maintenance assets...")
        
        asset_types = ['machine', 'equipment', 'vehicle', 'facility', 'instrument']
        
        # Ensure we have machines to create assets from
        if not self.machines:
            logger.warning("No machines available for asset generation")
            return
        
        for factory in self.factories:
            # Link production machines
            factory_machines = [m for m in self.machines if m.get('factory_id') == factory['factory_id']]
            
            for machine in factory_machines[:ASSETS_PER_FACTORY]:
                asset = {
                    'asset_id': self.generate_id('AST', 'asset'),
                    'asset_number': f"AST-{self.counters['asset']-1:05d}",
                    'asset_name': machine.get('machine_name', f"Asset {self.counters['asset']}"),
                    'asset_type': 'machine',
                    'asset_category': 'production',
                    'asset_class': random.choice(['critical', 'essential', 'important']),
                    'machine_id': machine['machine_id'],
                    'factory_id': factory['factory_id'],
                    'line_id': machine.get('line_id'),
                    'manufacturer': machine.get('manufacturer', 'Unknown'),
                    'model_number': machine.get('model', f"MDL-{random.randint(1000, 9999)}"),
                    'serial_number': machine.get('serial_number', f"SN{random.randint(100000, 999999)}"),
                    'installation_date': machine.get('install_date', (datetime.now() - timedelta(days=random.randint(365, 3650))).strftime('%Y-%m-%d')),
                    'criticality_rating': random.choice(['critical', 'high', 'medium']),
                    'safety_critical': random.choice([True, False]),
                    'production_critical': True,
                    'maintenance_strategy': random.choice(['preventive', 'predictive', 'corrective']),
                    'pm_frequency_type': 'calendar',
                    'has_meter': True,
                    'meter_unit': 'hours',
                    'current_meter_reading': round(random.uniform(5000, 50000), 2),
                    'asset_condition': random.choice(['excellent', 'good', 'fair']),
                    'asset_status': machine.get('status', 'operational'),
                    'downtime_cost_per_hour': round(random.uniform(5000, 50000), 2),
                    'is_active': True,
                    'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                self.assets.append(asset)
        
        logger.info(f"Generated {len(self.assets)} maintenance assets")
    
    def generate_technicians(self):
        """Generate maintenance technicians based on employees"""
        logger.info("Generating maintenance technicians...")
        
        trades = ['mechanical', 'electrical', 'instrumentation', 'multi_craft']
        skill_levels = ['technician', 'senior_technician', 'specialist']
        
        # Use existing employees if available, otherwise generate
        if self.employees:
            for employee in self.employees[:len(self.factories) * TECHNICIANS_PER_FACTORY]:
                tech = {
                    'technician_id': self.generate_id('TECH', 'tech'),
                    'employee_id': employee.get('employee_id'),
                    'technician_code': f"TECH{self.counters['tech']-1:04d}",
                    'first_name': employee.get('first_name', f"Tech{self.counters['tech']}"),
                    'last_name': employee.get('last_name', 'Maintenance'),
                    'hire_date': employee.get('hire_date', (datetime.now() - timedelta(days=random.randint(365, 3650))).strftime('%Y-%m-%d')),
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
        else:
            # Generate basic technicians if no employees found
            for factory in self.factories:
                factory_code = factory.get('factory_code', f"FAC-{factory['factory_id'][-4:]}")
                for i in range(TECHNICIANS_PER_FACTORY):
                    tech = {
                        'technician_id': self.generate_id('TECH', 'tech'),
                        'employee_id': None,
                        'technician_code': f"TECH{self.counters['tech']-1:04d}",
                        'first_name': f"Tech{i+1}",
                        'last_name': factory_code,
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
        
        logger.info(f"Generated {len(self.technicians)} technicians")
    
    def generate_mro_parts(self):
        """Generate MRO spare parts with supplier validation"""
        logger.info("Generating MRO spare parts...")
        
        part_types = ['mechanical', 'electrical', 'hydraulic', 'pneumatic', 'electronic']
        part_categories = ['spare_part', 'consumable']
        
        for i in range(MRO_PARTS_COUNT):
            # Select supplier if available
            supplier_id = None
            if self.suppliers:
                supplier_id = random.choice(self.suppliers)['supplier_id']
            
            # Select warehouse if available
            warehouse_id = None
            if self.warehouses:
                warehouse_id = random.choice(self.warehouses)['warehouse_id']
            
            part = {
                'mro_part_id': self.generate_id('MRO', 'part'),
                'part_id': self.generate_id('MRO', 'part'),  # Add this for compatibility
                'part_number': f"MRO-{self.counters['part']-1:05d}",
                'part_name': f"Spare Part {i+1}",
                'part_category': random.choice(part_categories),
                'part_type': random.choice(part_types),
                'primary_supplier_id': supplier_id,
                'warehouse_id': warehouse_id,
                'unit_of_measure': random.choice(['EA', 'SET', 'L', 'KG']),
                'current_stock': random.randint(0, 100),
                'min_stock_level': random.randint(5, 20),
                'max_stock_level': random.randint(50, 150),
                'reorder_point': random.randint(10, 30),
                'reorder_quantity': random.randint(20, 50),
                'criticality': random.choice(['critical', 'high', 'medium', 'low']),
                'lead_time_days': random.randint(7, 60),
                'unit_price': round(random.uniform(100, 10000), 2),  # Add unit_price for compatibility
                'standard_cost': round(random.uniform(100, 10000), 2),
                'part_status': 'active',
                'is_active': True,
                'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            self.mro_parts.append(part)
        
        logger.info(f"Generated {len(self.mro_parts)} MRO parts")
    
    def generate_pm_schedules(self):
        """Generate PM schedules"""
        logger.info("Generating PM schedules...")
        
        for asset in self.assets:
            for pm_num in range(PM_SCHEDULES_PER_ASSET):
                schedule_type = random.choice(['calendar', 'meter_based'])
                schedule = {
                    'pm_schedule_id': self.generate_id('PM', 'pm'),
                    'schedule_code': f"PM-{asset['asset_number']}-{pm_num+1:02d}",
                    'schedule_name': f"{asset['asset_name']} - Schedule {pm_num+1}",
                    'asset_id': asset['asset_id'],
                    'schedule_type': schedule_type,
                    'frequency_type': random.choice(['weekly', 'monthly', 'quarterly']),
                    'frequency_value': random.choice([1, 2, 3, 6]),
                    'frequency_unit': 'months',
                    'meter_frequency': random.randint(500, 2000) if schedule_type == 'meter_based' else (random.randint(500, 2000) if random.random() < 0.10 else None),
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
        
        logger.info(f"Generated {len(self.pm_schedules)} PM schedules")
    
    # ========================================================================
    # MAINTENANCE OPERATIONS
    # ========================================================================
    
    def generate_maintenance_operations(self, start_date: datetime, days: int):
        """Generate daily maintenance operations with ULTRA-FAST PARALLEL processing"""
        print(f"\nGenerating {days} days of maintenance operations with PARALLEL processing...")
        
        # Get valid FK sets for thread-safe access
        valid_machine_ids = list(self.helper.get_valid_machine_ids())
        valid_employee_ids = list(self.helper.get_valid_employee_ids())
        
        if not self.parallel_enabled or days < 20:
            return self._generate_maintenance_operations_sequential(start_date, days, valid_machine_ids, valid_employee_ids)
        
        # Parallel processing for large datasets
        chunk_size = max(5, days // self.worker_count)  # At least 5 days per chunk
        day_chunks = [(i, min(chunk_size, days - i)) for i in range(0, days, chunk_size)]
        
        print(f"  🚀 Processing {len(day_chunks)} day chunks with {self.worker_count} workers...")
        
        all_work_orders = []
        all_wo_tasks = []
        all_parts_transactions = []
        all_labor_entries = []
        all_meter_readings = []
        all_maintenance_history = []
        
        with ThreadPoolExecutor(max_workers=self.worker_count) as executor:
            # Submit chunk processing tasks
            futures = {
                executor.submit(self._generate_maintenance_operations_chunk, 
                    start_date + timedelta(days=start_day), 
                    chunk_days, 
                    chunk_id,
                    valid_machine_ids, valid_employee_ids): chunk_id 
                for chunk_id, (start_day, chunk_days) in enumerate(day_chunks)
            }
            
            # Collect results as they complete
            for future in as_completed(futures):
                chunk_id = futures[future]
                try:
                    chunk_results = future.result()
                    
                    all_work_orders.extend(chunk_results['work_orders'])
                    all_wo_tasks.extend(chunk_results['wo_tasks'])
                    all_parts_transactions.extend(chunk_results['parts_transactions'])
                    all_labor_entries.extend(chunk_results['labor_entries'])
                    all_meter_readings.extend(chunk_results['meter_readings'])
                    all_maintenance_history.extend(chunk_results['maintenance_history'])
                    
                    print(f"    ✓ CMMS chunk {chunk_id + 1}/{len(day_chunks)} completed ({len(chunk_results['work_orders'])} work orders)")
                except Exception as e:
                    print(f"    ✗ CMMS chunk {chunk_id + 1} failed: {e}")
        
        # Store results with thread safety
        with self.data_lock:
            self.work_orders.extend(all_work_orders)
            self.wo_tasks.extend(all_wo_tasks)
            self.parts_transactions.extend(all_parts_transactions)
            self.labor_entries.extend(all_labor_entries)
            self.meter_readings.extend(all_meter_readings)
            self.maintenance_history.extend(all_maintenance_history)
        
        print(f"✓ Generated CMMS operations: {len(self.work_orders):,} work orders, {len(self.wo_tasks):,} tasks via PARALLEL processing")
    
    def _generate_maintenance_operations_chunk(self, start_date: datetime, days: int, chunk_id: int, 
                                             valid_machine_ids: List[str], valid_employee_ids: List[str]) -> Dict:
        """Generate maintenance operations for a chunk of days (parallel worker method)"""
        
        # Local data storage for this chunk
        chunk_work_orders = []
        chunk_wo_tasks = []
        chunk_parts_transactions = []
        chunk_labor_entries = []
        chunk_meter_readings = []
        chunk_maintenance_history = []
        
        # Local counters to avoid collision
        local_wo_counter = chunk_id * 100000 + 1
        local_task_counter = chunk_id * 500000 + 1
        local_trans_counter = chunk_id * 300000 + 1
        local_labor_counter = chunk_id * 200000 + 1
        local_meter_counter = chunk_id * 100000 + 1
        local_history_counter = chunk_id * 100000 + 1
        
        current_date = start_date
        
        for day in range(days):
            num_wos = random.randint(*WORK_ORDERS_PER_DAY)
            
            for _ in range(num_wos):
                wo_data = self._create_work_order_local(current_date, local_wo_counter, 
                                                       local_task_counter, local_trans_counter,
                                                       local_labor_counter, local_meter_counter, 
                                                       local_history_counter,
                                                       valid_machine_ids, valid_employee_ids)
                if wo_data:
                    chunk_work_orders.append(wo_data['work_order'])
                    chunk_wo_tasks.extend(wo_data['wo_tasks'])
                    chunk_parts_transactions.extend(wo_data['parts_transactions'])
                    chunk_labor_entries.extend(wo_data['labor_entries'])
                    chunk_meter_readings.extend(wo_data['meter_readings'])
                    chunk_maintenance_history.append(wo_data['maintenance_history'])
                    
                    local_wo_counter += 1
                    local_task_counter += len(wo_data['wo_tasks'])
                    local_trans_counter += len(wo_data['parts_transactions'])
                    local_labor_counter += len(wo_data['labor_entries'])
                    local_meter_counter += len(wo_data['meter_readings'])
                    local_history_counter += 1
            
            current_date += timedelta(days=1)
        
        # Return all chunk data
        return {
            'work_orders': chunk_work_orders,
            'wo_tasks': chunk_wo_tasks,
            'parts_transactions': chunk_parts_transactions,
            'labor_entries': chunk_labor_entries,
            'meter_readings': chunk_meter_readings,
            'maintenance_history': chunk_maintenance_history
        }
    
    def _generate_maintenance_operations_sequential(self, start_date: datetime, days: int, 
                                                   valid_machine_ids: List[str], valid_employee_ids: List[str]):
        """Fallback sequential maintenance operations for small datasets"""
        print("Generating maintenance operations (sequential fallback)...")
        # Keep original sequential logic for small datasets
        current_date = start_date
        
        for day in range(days):
            num_wos = random.randint(*WORK_ORDERS_PER_DAY)
            for _ in range(num_wos):
                self._create_work_order(current_date)
            current_date += timedelta(days=1)
        
        print(f"Generated {len(self.work_orders)} work orders with {len(self.wo_tasks)} tasks (sequential)")
    
    def _create_work_order_local(self, date: datetime, wo_counter: int, task_counter: int, 
                                trans_counter: int, labor_counter: int, meter_counter: int, 
                                history_counter: int, valid_machine_ids: List[str], valid_employee_ids: List[str]) -> Dict:
        """Create work order with all related data (local/chunk version)"""
        if not self.assets:
            return None
        
        asset = random.choice(self.assets)
        wo_type = random.choice(['preventive', 'corrective', 'breakdown', 'inspection'])
        
        machine_id = random.choice(valid_machine_ids) if valid_machine_ids else asset['asset_id']
        assigned_to = random.choice(valid_employee_ids) if valid_employee_ids else 'EMP-000001'
        
        actual_start = date + timedelta(hours=random.randint(8, 16))
        duration_hours = round(random.uniform(2, 8), 2)
        actual_end = actual_start + timedelta(hours=duration_hours)
        
        work_order = {
            'work_order_id': f"WO-{str(wo_counter).zfill(6)}",
            'work_order_number': f"WO-{date.strftime('%Y%m%d')}-{wo_counter:04d}",
            'asset_id': asset['asset_id'],
            'machine_id': machine_id,
            'wo_type': wo_type,
            'priority': random.choice(['emergency', 'urgent', 'high', 'medium', 'low']),
            'description': f"{wo_type.title()} maintenance for {asset['asset_name']}",
            'problem_description': f"Routine {wo_type} work",
            'failure_code': random.choice(self.failure_codes)['failure_code'] if self.failure_codes else f"FC-{random.randint(100, 999)}",
            'scheduled_start_date': date.strftime('%Y-%m-%d'),
            'scheduled_end_date': (date + timedelta(hours=random.randint(4, 24))).strftime('%Y-%m-%d'),
            'estimated_duration_hours': round(random.uniform(2, 8), 2),
            'actual_start_date': actual_start.strftime('%Y-%m-%d %H:%M:%S'),
            'actual_end_date': actual_end.strftime('%Y-%m-%d %H:%M:%S'),
            'actual_duration_hours': duration_hours,
            'wo_status': random.choice(['completed', 'completed', 'completed', 'in_progress']),
            'assigned_to': assigned_to,
            'downtime_minutes': random.randint(0, 480) if wo_type == 'breakdown' else 0,
            'estimated_cost': round(random.uniform(1000, 20000), 2),
            'actual_total_cost': round(random.uniform(1000, 20000), 2),
            'created_at': date.strftime('%Y-%m-%d %H:%M:%S')
        }
        
        # Create tasks
        wo_tasks = []
        num_tasks = random.randint(2, 5)
        task_types = ['inspection', 'replacement', 'adjustment', 'cleaning', 'lubrication']
        
        for seq in range(1, num_tasks + 1):
            task = {
                'task_id': f"TASK-{str(task_counter + seq - 1).zfill(6)}",
                'work_order_id': work_order['work_order_id'],
                'task_sequence': seq,
                'task_description': f"Task {seq}: {random.choice(task_types).title()}",
                'task_type': random.choice(task_types),
                'estimated_duration_minutes': random.randint(30, 180),
                'actual_duration_minutes': random.randint(30, 180),
                'task_status': 'completed' if work_order['wo_status'] == 'completed' else 'pending',
                'task_result': 'pass',
                'created_at': date.strftime('%Y-%m-%d %H:%M:%S')
            }
            wo_tasks.append(task)
        
        # Create parts transactions
        parts_transactions = []
        if self.mro_parts:
            num_parts = random.randint(1, 3)
            for i in range(num_parts):
                part = random.choice(self.mro_parts)
                qty = random.randint(1, 5)
                
                trans = {
                    'transaction_id': f"PTRANS-{str(trans_counter + i).zfill(6)}",
                    'transaction_number': f"TN-{str(trans_counter + i).zfill(8)}",
                    'work_order_id': work_order['work_order_id'],
                    'mro_part_id': part['part_id'],
                    'transaction_type': 'issued',
                    'quantity': qty,
                    'unit_cost': part['unit_price'],
                    'total_cost': qty * part['unit_price'],
                    'warehouse_id': random.choice(self.warehouses)['warehouse_id'] if self.warehouses else 'WH-000001',
                    'transaction_date': actual_start.strftime('%Y-%m-%d %H:%M:%S'),
                    'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                parts_transactions.append(trans)
        
        # Create labor entries
        labor_entries = []
        num_laborers = random.randint(1, 3)
        for i in range(num_laborers):
            labor = {
                'entry_id': f"LABOR-{str(labor_counter + i).zfill(6)}",
                'work_order_id': work_order['work_order_id'],
                'technician_id': random.choice(valid_employee_ids) if valid_employee_ids else assigned_to,
                'work_date': actual_start.strftime('%Y-%m-%d'),
                'start_time': actual_start.strftime('%Y-%m-%d %H:%M:%S'),
                'end_time': actual_end.strftime('%Y-%m-%d %H:%M:%S'),
                'hours_worked': round(duration_hours / num_laborers, 2),
                'hourly_rate': round(random.uniform(25, 85), 2),
                'total_cost': round((duration_hours / num_laborers) * random.uniform(25, 85), 2),
                'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            labor_entries.append(labor)
        
        # Create meter readings
        meter_readings = []
        if random.random() < 0.7:  # 70% chance of meter reading
            reading = {
                'reading_id': f"METER-{str(meter_counter).zfill(6)}",
                'asset_id': asset['asset_id'],
                'meter_type': random.choice(['hours', 'cycles', 'distance', 'volume']),
                'reading_value': round(random.uniform(1000, 50000), 2),
                'reading_date': actual_end.strftime('%Y-%m-%d %H:%M:%S'),
                'recorded_by': assigned_to,
                'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            meter_readings.append(reading)
        
        # Create maintenance history - use schema field names
        maintenance_history = {
            'history_id': f"HIST-{str(history_counter).zfill(6)}",
            'asset_id': asset['asset_id'],
            'event_type': 'work_order_completed',
            'event_date': actual_end.strftime('%Y-%m-%d %H:%M:%S'),
            'event_description': work_order['description'],
            'work_order_id': work_order['work_order_id'],
            'failure_code': work_order.get('failure_code'),
            'downtime_hours': round(work_order.get('downtime_minutes', 0) / 60, 2),
            'total_cost': work_order.get('actual_total_cost'),
            'performed_by': assigned_to,
            'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        return {
            'work_order': work_order,
            'wo_tasks': wo_tasks,
            'parts_transactions': parts_transactions,
            'labor_entries': labor_entries,
            'meter_readings': meter_readings,
            'maintenance_history': maintenance_history
        }
    
    def _create_work_order(self, date: datetime):
        """Create work order"""
        if not self.assets:
            return
        
        asset = random.choice(self.assets)
        wo_type = random.choice(['preventive', 'corrective', 'breakdown', 'inspection'])
        
        # FK from registry - GUARANTEED VALID
        valid_machine_ids = list(self.helper.get_valid_machine_ids())
        machine_id = random.choice(valid_machine_ids) if valid_machine_ids else asset['asset_id']
        
        # FK from registry - GUARANTEED VALID
        valid_employee_ids = list(self.helper.get_valid_employee_ids())
        assigned_to = random.choice(valid_employee_ids)
        
        wo = {
            'work_order_id': self.generate_id('WO', 'wo'),
            'work_order_number': f"WO-{date.strftime('%Y%m%d')}-{self.counters['wo']:04d}",
            'asset_id': asset['asset_id'],
            'machine_id': machine_id,
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
            'assigned_to': assigned_to,
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
                'work_order_id': wo['work_order_id'],
                'mro_part_id': part['part_id'],
                'transaction_type': 'issue',
                'transaction_date': date.strftime('%Y-%m-%d %H:%M:%S'),
                'quantity': qty,
                'unit_of_measure': part['unit_of_measure'],
                'unit_cost': part['standard_cost'],
                'total_cost': round(qty * part['standard_cost'], 2),
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
        
        hours = wo.get('actual_duration_hours', 0)
        
        entry = {
            'entry_id': self.generate_id('LABOR', 'labor'),
            'work_order_id': wo['work_order_id'],
            'technician_id': tech['technician_id'],
            'work_date': wo.get('actual_start_date', date.strftime('%Y-%m-%d'))[:10],
            'start_time': wo.get('actual_start_date', date.strftime('%Y-%m-%d %H:%M:%S')),
            'end_time': wo.get('actual_end_date', (date + timedelta(hours=hours)).strftime('%Y-%m-%d %H:%M:%S')),
            'hours_worked': hours,
            'hourly_rate': tech.get('hourly_rate', 50.0),
            'total_cost': round(hours * tech.get('hourly_rate', 50.0), 2),
            'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        self.labor_entries.append(entry)
    
    def _create_maintenance_history(self, wo: dict, asset: dict, date: datetime):
        """Create maintenance history record"""
        # Ensure event_date is NEVER null - use multiple fallbacks
        event_date = (
            wo.get('actual_end_date') or 
            wo.get('scheduled_end_date') or 
            wo.get('actual_start_date') or 
            wo.get('scheduled_start_date') or 
            date.strftime('%Y-%m-%d %H:%M:%S')
        )
        
        # If event_date is just a date without time, add time component
        if event_date and len(event_date) == 10:
            event_date = f"{event_date} 12:00:00"
        
        history = {
            'history_id': self.generate_id('HIST', 'history'),
            'asset_id': asset['asset_id'],
            'event_type': 'work_order_completed',
            'event_date': event_date,
            'event_description': wo.get('description', 'Maintenance work completed'),
            'work_order_id': wo['work_order_id'],
            'failure_code': wo.get('failure_code'),
            'downtime_hours': round(wo.get('downtime_minutes', 0) / 60, 2),
            'total_cost': wo.get('actual_total_cost'),
            'performed_by': wo.get('assigned_to'),
            'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        self.maintenance_history.append(history)
    
    # ========================================================================
    # EMPTY TABLE GENERATORS
    # ========================================================================
    
    def _generate_maintenance_teams(self):
        """Generate maintenance teams"""
        print("Generating maintenance teams...")
        teams = []
        
        team_names = ['Day Shift Team', 'Evening Shift Team', 'Night Shift Team', 
                     'Mechanical Team', 'Electrical Team', 'Rotating Equipment Team']
        
        for factory in self.factories:
            for team_name in team_names:
                team = {
                    'team_id': self.generate_id('TM', 'team'),
                    'team_code': f"TM-{self.counters['team']-1:04d}",
                    'team_name': team_name,
                    'team_lead_id': random.choice(self.technicians)['technician_id'],
                    'member_count': random.randint(3, 8),
                    'shift': random.choice(['day', 'evening', 'night']),
                    'specialization': random.choice(['mechanical', 'electrical', 'mixed']),
                    'team_status': 'active',
                    'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                teams.append(team)
        
        print(f"Generated {len(teams)} maintenance teams")
        return teams

    def _generate_pm_generation_log(self):
        """Generate PM generation log entries"""
        print("Generating PM generation logs...")
        pm_logs = []
        
        for pm_schedule in self.pm_schedules:
            log = {
                'log_id': self.generate_id('PMLOG', 'history'),
                'pm_schedule_id': pm_schedule['pm_schedule_id'],
                'generated_work_order_id': random.choice(self.work_orders)['work_order_id'] if self.work_orders else None,
                'generation_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'next_due_date': (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d'),
                'status': 'generated',
                'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            pm_logs.append(log)
        
        print(f"Generated {len(pm_logs)} PM generation logs")
        return pm_logs

    def _generate_work_procedures(self):
        """Generate work procedures"""
        print("Generating work procedures...")
        procedures = []
        
        for pm_schedule in self.pm_schedules:
            proc = {
                'procedure_id': self.generate_id('PROC', 'failure'),
                'procedure_code': f"PROC-{self.counters['failure']-1:05d}",
                'procedure_name': f"Procedure for {pm_schedule['schedule_name']}",
                'pm_schedule_id': pm_schedule['pm_schedule_id'],
                'procedure_steps': json.dumps([
                    "Visual inspection",
                    "Measurement and testing",
                    "Lubrication",
                    "Component replacement if needed",
                    "Performance verification"
                ]),
                'estimated_duration_hours': round(random.uniform(2, 6), 2),
                'required_skills': json.dumps([random.choice(['mechanical', 'electrical', 'instrumentation'])]),
                'required_tools': json.dumps(['Wrench Set', 'Multimeter', 'Pressure Gauge']),
                'safety_precautions': json.dumps(['Lockout/Tagout', 'Safety Harness', 'PPE Required']),
                'procedure_status': 'active',
                'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            procedures.append(proc)
        
        print(f"Generated {len(procedures)} work procedures")
        return procedures

    def _generate_maintenance_costs(self):
        """Generate maintenance cost records"""
        print("Generating maintenance cost records...")
        costs = []
        
        for wo in self.work_orders:
            cost = {
                'cost_id': self.generate_id('COST', 'failure'),
                'work_order_id': wo['work_order_id'],
                'asset_id': wo['asset_id'],
                'cost_type': random.choice(['labor', 'parts', 'contractor', 'equipment_rental', 'other']),
                'cost_description': random.choice(['Labor', 'Parts', 'Contractor Service', 'Equipment Rental']),
                'cost_amount': round(random.uniform(100, 10000), 2),
                'currency': 'INR',
                'cost_date': datetime.now().strftime('%Y-%m-%d'),
                'cost_center_id': f"CC-{random.randint(1, 12):06d}",
                'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            costs.append(cost)
        
        print(f"Generated {len(costs)} maintenance cost records")
        return costs

    def _generate_maintenance_cost_centers(self):
        """Generate maintenance cost centers"""
        print("Generating maintenance cost centers...")
        cost_centers = []
        
        for factory in self.factories:
            for i in range(3):
                cc = {
                    'cost_center_id': self.generate_id('CC', 'failure'),
                    'cost_center_code': f"CC-{self.counters['failure']-1:04d}",
                    'cost_center_name': f"{factory['factory_name']} - Maintenance CC-{i+1}",
                    'factory_id': factory['factory_id'],
                    'cost_center_manager': f"Manager {i+1}",
                    'budget_annual': round(random.uniform(100000, 500000), 2),
                    'ytd_spending': round(random.uniform(50000, 250000), 2),
                    'is_active': True,
                    'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                cost_centers.append(cc)
        
        print(f"Generated {len(cost_centers)} maintenance cost centers")
        return cost_centers

    def _generate_equipment_meter_readings(self):
        """Generate equipment meter readings"""
        print("Generating equipment meter readings...")
        readings = []
        start_date = datetime.now() - timedelta(days=90)
        
        for asset in self.assets:
            current_reading = asset['current_meter_reading']
            for day in range(0, 90, 7):  # Weekly readings
                reading = {
                    'reading_id': self.generate_id('MR', 'meter'),
                    'asset_id': asset['asset_id'],
                    'reading_date': (start_date + timedelta(days=day)).strftime('%Y-%m-%d %H:%M:%S'),
                    'meter_value': round(current_reading + (day * 40), 2),
                    'meter_unit': asset['meter_unit'],
                    'previous_reading': round(current_reading + ((day - 7) * 40), 2) if day > 0 else None,
                    'delta_value': 280.0 if day > 0 else None,
                    'reading_source': 'manual',
                    'recorded_by': random.choice(self.technicians)['technician_id'],
                    'created_at': (start_date + timedelta(days=day)).strftime('%Y-%m-%d %H:%M:%S')
                }
                readings.append(reading)
        
        print(f"Generated {len(readings)} equipment meter readings")
        return readings

    def _generate_service_contracts(self):
        """Generate service contracts"""
        print("Generating service contracts...")
        contracts = []
        
        for i, asset in enumerate(self.assets):
            contract = {
                'contract_id': self.generate_id('SC', 'failure'),
                'contract_number': f"SC-{i+1:06d}",
                'contract_name': f"Service Contract for {asset['asset_name']}",
                'vendor_id': f"VEN-{random.randint(1, 100):06d}",
                'vendor_name': random.choice(['Siemens Service', 'Fanuc Support', 'DMG Mori Service']),
                'contract_type': random.choice(['full_service', 'amc', 'calibration', 'consulting']),
                'covered_assets': json.dumps([asset['asset_id']]),
                'contract_start_date': (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d'),
                'contract_end_date': (datetime.now() + timedelta(days=365)).strftime('%Y-%m-%d'),
                'contract_value': round(random.uniform(10000, 100000), 2),
                'billing_frequency': 'monthly',
                'response_time_hours': random.choice([4, 8, 24]),
                'contract_status': 'active',
                'is_active': True,
                'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            contracts.append(contract)
        
        print(f"Generated {len(contracts)} service contracts")
        return contracts

    def _generate_service_call_logs(self):
        """Generate service call logs"""
        print("Generating service call logs...")
        call_logs = []
        start_date = datetime.now() - timedelta(days=90)
        
        for i in range(35):
            call = {
                'call_log_id': self.generate_id('CALL', 'meter'),
                'call_number': f"CALL-{i+1:06d}",
                'contract_id': f"SC-{random.randint(1, 25):06d}",
                'asset_id': random.choice(self.assets)['asset_id'],
                'call_date': (start_date + timedelta(days=random.randint(0, 90))).strftime('%Y-%m-%d %H:%M:%S'),
                'problem_description': random.choice(['Performance degradation', 'Error code detected', 'Routine inspection', 'Breakdown']),
                'priority': random.choice(['normal', 'urgent', 'emergency']),
                'service_engineer_name': f"Tech{random.randint(1, 10)}",
                'service_engineer_contact': f"tech{random.randint(1, 10)}@service.com",
                'service_performed': 'Maintenance completed',
                'parts_used': json.dumps(['Bearing', 'Seal', 'Oil']),
                'call_status': 'closed',
                'created_at': (start_date + timedelta(days=random.randint(0, 90))).strftime('%Y-%m-%d %H:%M:%S')
            }
            call_logs.append(call)
        
        print(f"Generated {len(call_logs)} service call logs")
        return call_logs

    def _generate_cmms_integration_log(self):
        """Generate CMMS integration logs"""
        print("Generating CMMS integration logs...")
        logs = []
        start_date = datetime.now() - timedelta(days=90)
        
        for i in range(50):
            log = {
                'log_id': self.generate_id('ILOG', 'meter'),
                'log_date': (start_date + timedelta(days=random.randint(0, 90))).strftime('%Y-%m-%d'),
                'log_time': f"{random.randint(0, 23):02d}:{random.randint(0, 59):02d}:00",
                'source_system': random.choice(['ERP', 'MES', 'IoT', 'API']),
                'target_system': 'CMMS',
                'operation_type': random.choice(['sync', 'update', 'create', 'delete']),
                'record_count': random.randint(1, 100),
                'status': random.choice(['success', 'success', 'success', 'failed']),
                'error_message': None if random.random() > 0.1 else 'Connection timeout',
                'created_at': (start_date + timedelta(days=random.randint(0, 90))).strftime('%Y-%m-%d %H:%M:%S')
            }
            logs.append(log)
        
        print(f"Generated {len(logs)} CMMS integration logs")
        return logs

    def _generate_asset_reliability_metrics(self):
        """Generate asset reliability metrics"""
        print("Generating asset reliability metrics...")
        metrics = []
        
        for asset in self.assets:
            start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
            end_date = datetime.now().strftime('%Y-%m-%d')
            metric = {
                'metric_id': self.generate_id('ARM', 'meter'),
                'asset_id': asset['asset_id'],
                'period_start_date': start_date,
                'period_end_date': end_date,
                'period_type': 'monthly',
                'total_hours': round(random.uniform(500, 744), 2),
                'operating_hours': round(random.uniform(400, 700), 2),
                'downtime_hours': round(random.uniform(0, 100), 2),
                'planned_downtime_hours': round(random.uniform(0, 50), 2),
                'unplanned_downtime_hours': round(random.uniform(0, 50), 2),
                'availability_pct': round(random.uniform(85, 99.9), 2),
                'number_of_failures': random.randint(0, 10),
                'mtbf_hours': round(random.uniform(500, 5000), 2),
                'mttr_hours': round(random.uniform(2, 20), 2),
                'oee_pct': round(random.uniform(65, 95), 2),
                'pm_work_orders': random.randint(5, 20),
                'cm_work_orders': random.randint(0, 10),
                'breakdown_work_orders': random.randint(0, 5),
                'total_maintenance_cost': round(random.uniform(5000, 50000), 2),
                'labor_cost': round(random.uniform(2000, 20000), 2),
                'parts_cost': round(random.uniform(1000, 15000), 2),
                'contractor_cost': round(random.uniform(0, 10000), 2),
                'maintenance_cost_per_operating_hour': round(random.uniform(10, 100), 4),
                'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            metrics.append(metric)
        
        print(f"Generated {len(metrics)} asset reliability metrics")
        return metrics

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
        """Export to JSON with flat structure matching actual table names"""
        logger.info(f"\nExporting to JSON...")
        
        # Generate data for empty tables
        maintenance_teams = self._generate_maintenance_teams()
        pm_generation_log = self._generate_pm_generation_log()
        work_procedures = self._generate_work_procedures()
        maintenance_costs = self._generate_maintenance_costs()
        maintenance_cost_centers = self._generate_maintenance_cost_centers()
        equipment_meter_readings = self._generate_equipment_meter_readings()
        service_contracts = self._generate_service_contracts()
        service_call_logs = self._generate_service_call_logs()
        cmms_integration_log = self._generate_cmms_integration_log()
        asset_reliability_metrics = self._generate_asset_reliability_metrics()
        
        data = {
            # Assets & Teams
            'maintenance_assets': self.assets,
            'maintenance_technicians': self.technicians,
            'maintenance_teams': maintenance_teams,
            'failure_codes': self.failure_codes,
            
            # MRO Parts
            'mro_parts': self.mro_parts,
            'mro_parts_transactions': self.parts_transactions,
            
            # Maintenance Planning
            'pm_schedules': self.pm_schedules,
            'pm_generation_log': pm_generation_log,
            
            # Work Orders
            'work_orders': self.work_orders,
            'work_order_tasks': self.wo_tasks,
            'work_procedures': work_procedures,
            
            # Labor & Costs
            'labor_time_entries': self.labor_entries,
            'maintenance_costs': maintenance_costs,
            'maintenance_cost_centers': maintenance_cost_centers,
            
            # Maintenance History
            'maintenance_history': self.maintenance_history,
            'equipment_meter_readings': equipment_meter_readings,
            'service_contracts': service_contracts,
            'service_call_logs': service_call_logs,
            
            # Integration & Logging
            'cmms_integration_log': cmms_integration_log,
            'asset_reliability_metrics': asset_reliability_metrics
        }
        
        with open(output_file, 'w') as f:
            json.dump(data, f, indent=2)
        
        logger.info(f"Data exported to {output_file}")


if __name__ == "__main__":
    from pathlib import Path
    import sys
    
    try:
        # Get the directory of this script (data folder)
        script_dir = Path(__file__).parent
        
        # Load master data from the same folder structure
        master_data_file = script_dir.parent / "01 - Base Data" / "genims_master_data.json"
        
        generator = CMMSDataGenerator(str(master_data_file))
        generator.generate_all_data()
        
        # Export to JSON (in same folder as script)
        json_file = script_dir / "genims_cmms_data.json"
        generator.to_json(str(json_file))
        
        logger.info("\n" + "="*80)
        logger.info("CMMS Historical Data Generation Complete!")
        logger.info("="*80)
        
        # Explicit success exit
        sys.exit(0)
        
    except Exception as e:
        logger.error(f"CMMS generation failed: {e}")
        sys.exit(1)
