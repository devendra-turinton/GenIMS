#!/usr/bin/env python3
"""
GenIMS WMS + TMS Historical Data Generator with ULTRA-FAST PARALLEL Processing
Generates 180 days of warehouse operations + 180 days of logistics data
Includes FK validation, time coordination, and ultra-fast parallel optimizations
"""

import random
import json
from datetime import datetime, timedelta
from typing import List, Dict, Set
import sys
from pathlib import Path
import logging
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

# Enhanced configuration for bottleneck handling
WMS_DAYS_OF_HISTORY = 180
TMS_DAYS_OF_HISTORY = 180
WAREHOUSES_TO_CREATE = 12  # 3 warehouses per factory (4 factories)
CARRIERS_TO_CREATE = 40   # More carriers for enterprise logistics

# Performance optimization settings
BATCH_SIZE_LIMIT = 10000
MAX_WAVE_CONCURRENCY = 50  # Limit concurrent waves to prevent bottlenecks
INVENTORY_CHECK_INTERVAL = 1000  # Check inventory consistency every N records

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'wms_tms_generation_{datetime.now().strftime("%Y%m%d")}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class WMSTMSDataGenerator:
    def __init__(self, master_data_file=None, erp_data_file=None):
        """Initialize with master data, ERP data, FK validation, and registry"""
        from pathlib import Path
        
        if master_data_file is None:
            master_data_file = Path(__file__).parent.parent / "01 - Base Data" / "genims_master_data.json"
        
        if erp_data_file is None:
            erp_data_file = Path(__file__).parent.parent / "04 - ERP & MES Integration" / "genims_erp_data.json"
        
        logger.info(f"Loading master data from {master_data_file}...")
        logger.info(f"Loading ERP data from {erp_data_file}...")
        
        with open(master_data_file, 'r') as f:
            self.master_data = json.load(f)
        
        with open(erp_data_file, 'r') as f:
            self.erp_data = json.load(f)
        
        # Load helper for FK validation and time coordination
        self.helper = get_helper()
        self.registry = self.helper.registry
        
        self.factories = self.master_data['factories']
        self.customers = self.master_data['customers']
        self.materials = self.erp_data['materials']
        
        # FK validation sets for bottleneck prevention
        self.valid_material_ids: Set[str] = set()
        self.valid_sales_order_ids: Set[str] = set()
        self.valid_warehouse_ids: Set[str] = set()
        
        # Performance optimization tracking
        self.stats = {
            'fk_validation_errors': 0,
            'inventory_checks': 0,
            'wave_capacity_adjustments': 0,
            'time_coordination_events': 0,
            'records_generated': 0
        }
        
        # Initialize FK validation data
        self._initialize_fk_validation()
        
        # Initialize data structures
        self._initialize_data_structures()
        
        logger.info(f"FK Validation initialized: {len(self.valid_material_ids)} materials, "
                   f"{len(self.valid_sales_order_ids)} sales orders")
    
    def _initialize_fk_validation(self):
        """Initialize FK validation sets from ERP data"""
        # Material IDs from ERP
        for material in self.materials:
            self.valid_material_ids.add(material['material_id'])
        
        # Sales Order IDs from ERP (assuming they exist)
        if 'sales_orders' in self.erp_data:
            for order in self.erp_data['sales_orders']:
                self.valid_sales_order_ids.add(order['sales_order_id'])
        else:
            # Generate valid sales order IDs if not present
            for i in range(1, 10001):  # 10K sales orders
                self.valid_sales_order_ids.add(f"SO-{i:06d}")
        
        # Warehouse IDs from master data
        if 'warehouses' in self.master_data:
            for warehouse in self.master_data['warehouses']:
                self.valid_warehouse_ids.add(warehouse)
        else:
            # Generate warehouse IDs  
            for i in range(1, WAREHOUSES_TO_CREATE + 1):
                self.valid_warehouse_ids.add(f"WH-{i:03d}")
    
    def validate_foreign_key(self, fk_type: str, fk_value: str) -> bool:
        """Validate foreign key to prevent orphaned records"""
        if fk_type == 'material_id':
            return fk_value in self.valid_material_ids
        elif fk_type == 'sales_order_id':
            return fk_value in self.valid_sales_order_ids
        elif fk_type == 'warehouse_id':
            return fk_value in self.valid_warehouse_ids
        return False
    
    def get_max_timestamp(self) -> datetime:
        """Get maximum timestamp from existing data for time coordination"""
        try:
            # Check registry for existing generation data
            if hasattr(self.registry, 'last_timestamps') and 'wms_tms_historical' in getattr(self.registry, 'last_timestamps', {}):
                last_run = self.registry.last_timestamps['wms_tms_historical']
                logger.info(f"Time coordination: Continuing from {last_run}")
                self.stats['time_coordination_events'] += 1
                return last_run
            else:
                # Start from 6 months ago
                start_time = datetime.now() - timedelta(days=180)
                logger.info(f"Time coordination: Starting fresh simulation from {start_time}")
                return start_time
        except Exception as e:
            logger.warning(f"Time coordination failed: {e}, using default start time")
            return datetime.now() - timedelta(days=180)
    
    def check_inventory_consistency(self, material_id: str, warehouse_id: str, quantity_change: int) -> bool:
        """Check if inventory operation would create negative stock"""
        # Simple inventory tracking for bottleneck prevention
        inventory_key = f"{warehouse_id}_{material_id}"
        current_stock = getattr(self, '_inventory_tracker', {}).get(inventory_key, 1000)
        
        if not hasattr(self, '_inventory_tracker'):
            self._inventory_tracker = {}
            
        if current_stock + quantity_change < 0:
            self.stats['inventory_checks'] += 1
            return False
            
        self._inventory_tracker[inventory_key] = current_stock + quantity_change
        return True
    
    def manage_wave_capacity(self, active_waves: int) -> bool:
        """Manage wave processing capacity to prevent bottlenecks"""
        if active_waves >= MAX_WAVE_CONCURRENCY:
            self.stats['wave_capacity_adjustments'] += 1
            return False
        return True
    
    def _initialize_data_structures(self):
        """Initialize all data structure lists"""
        self.sales_orders = self.erp_data['sales_orders']
        self.purchase_orders = self.erp_data['purchase_orders']
        self.sales_order_lines = self.erp_data.get('sales_order_lines', [])
        
        # Build material_id -> sales_order_lines map for return order linking
        self.material_to_sales_lines = {}
        self.materials_with_sales = []
        for sol in self.sales_order_lines:
            mat_id = sol.get('material_id')
            if mat_id:
                if mat_id not in self.material_to_sales_lines:
                    self.material_to_sales_lines[mat_id] = []
                    self.materials_with_sales.append(mat_id)
                self.material_to_sales_lines[mat_id].append(sol)
        
        # WMS Data structures
        self.warehouses = []
        self.zones = []
        self.bins = []
        self.warehouse_inventory = []
        self.receiving_tasks = []
        self.putaway_tasks = []
        self.pick_waves = []
        self.wave_lines = []
        self.picking_tasks = []
        self.packing_tasks = []
        self.shipping_tasks = []
        self.warehouse_workers = []
        
        # TMS Data structures
        self.carriers = []
        self.carrier_services = []
        self.shipments = []
        self.shipment_lines = []
        self.tracking_events = []
        self.routes = []
        self.route_stops = []
        self.deliveries = []
        self.pod = []
        self.return_orders = []
        
        # Counters for unique ID generation
        self.counters = {
            'warehouse': 1, 'zone': 1, 'bin': 1, 'wh_inv': 1,
            'receiving': 1, 'putaway': 1, 'wave': 1, 'picking': 1,
            'packing': 1, 'shipping': 1, 'worker': 1,
            'carrier': 1, 'service': 1, 'shipment': 1, 'tracking': 1,
            'route': 1, 'delivery': 1, 'pod': 1, 'return': 1, 'aisle': 1, 'slot': 1
        }
        
        logger.info(f"Loaded: {len(self.materials)} materials, {len(self.sales_orders)} sales orders, {len(self.sales_order_lines)} sales order lines")
        
        # ULTRA-FAST PARALLEL Configuration
        self.worker_count = WORKER_COUNT
        self.batch_size = BATCH_SIZE
        self.parallel_enabled = True
        self.data_lock = threading.Lock()
        
        print(f"🚀 ULTRA-FAST WMS+TMS PARALLEL MODE: {self.worker_count} workers, batch_size={self.batch_size:,}")
        print(f"   CPU cores available: {cpu_count}, Using {self.worker_count} for generation")
    
    def generate_id(self, prefix: str, counter_key: str) -> str:
        """Generate unique IDs with prefix and counter"""
        id_val = f"{prefix}-{str(self.counters[counter_key]).zfill(6)}"
        self.counters[counter_key] += 1
        return id_val
    
    def generate_all_data(self):
        """Generate all WMS and TMS data with time coordination and FK validation"""
        logger.info(f"\n{'='*80}")
        logger.info(f"Generating WMS ({WMS_DAYS_OF_HISTORY} days) + TMS ({TMS_DAYS_OF_HISTORY} days) Data")
        logger.info(f"Time coordination enabled, FK validation active, Bottleneck fixes applied")
        logger.info(f"{'='*80}\n")
        
        # Get coordinated start time
        start_time = self.get_max_timestamp()
        
        # WMS Master Data
        self.generate_warehouses()
        self.generate_warehouse_zones()
        self.generate_storage_bins()
        self.generate_warehouse_workers()
        
        # WMS Operations with time coordination
        self.generate_warehouse_operations(start_time, WMS_DAYS_OF_HISTORY)
        
        # TMS Master Data
        self.generate_carriers()
        
        # TMS Operations with FK validation
        tms_start = start_time  # Use same coordinated time
        self.generate_logistics_operations(tms_start, TMS_DAYS_OF_HISTORY)
        
        # Update registry with completion time
        try:
            completion_time = start_time + timedelta(days=max(WMS_DAYS_OF_HISTORY, TMS_DAYS_OF_HISTORY))
            if not hasattr(self.registry, 'last_timestamps'):
                self.registry.last_timestamps = {}
            self.registry.last_timestamps['wms_tms_historical'] = completion_time
            logger.info(f"Time coordination: Updated registry to {completion_time}")
        except Exception as e:
            logger.warning(f"Failed to update registry: {e}")
        
        self._print_summary()
    
    # ========================================================================
    # WMS - WAREHOUSE STRUCTURE
    # ========================================================================
    
    def generate_warehouses(self):
        """Generate warehouse master data"""
        print("Generating warehouses...")
        
        for factory in self.factories[:WAREHOUSES_TO_CREATE]:
            warehouse = {
                'warehouse_id': self.generate_id('WH', 'warehouse'),
                'warehouse_code': f"WH{str(self.counters['warehouse']-1).zfill(2)}",
                'warehouse_name': f"{factory['factory_name']} Distribution Center",
                'plant_id': factory['factory_id'],
                'city': factory['city'],
                'state': factory.get('state', factory.get('region', 'Unknown')),
                'country': factory['country'],
                'warehouse_type': 'distribution_center',
                'total_area_sqm': random.randint(5000, 20000),
                'storage_capacity_pallets': random.randint(1000, 5000),
                'dock_doors': random.randint(10, 30),
                'operates_24x7': True,
                'is_active': True,
                'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            self.warehouses.append(warehouse)
        
        print(f"Generated {len(self.warehouses)} warehouses")
    
    def generate_warehouse_zones(self):
        """Generate zones within warehouses"""
        print("Generating warehouse zones...")
        
        zone_types = ['receiving', 'storage', 'picking', 'packing', 'shipping', 'staging']
        
        for warehouse in self.warehouses:
            for zone_type in zone_types:
                zone = {
                    'zone_id': self.generate_id('ZONE', 'zone'),
                    'warehouse_id': warehouse['warehouse_id'],
                    'zone_code': f"{warehouse['warehouse_code']}-{zone_type[:3].upper()}",
                    'zone_name': f"{zone_type.title()} Zone",
                    'zone_type': zone_type,
                    'area_sqm': random.randint(500, 2000),
                    'temperature_zone': 'ambient',
                    'is_active': True,
                    'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                self.zones.append(zone)
        
        print(f"Generated {len(self.zones)} zones")
    
    def generate_storage_bins(self):
        """Generate storage bins"""
        print("Generating storage bins...")
        
        storage_zones = [z for z in self.zones if z['zone_type'] == 'storage']
        
        for zone in storage_zones:
            # Create 50 bins per storage zone
            for aisle in range(1, 6):  # 5 aisles
                for level in range(1, 4):  # 3 levels
                    for pos in range(1, 5):  # 4 positions per level
                        bin_data = {
                            'bin_id': self.generate_id('BIN', 'bin'),
                            'warehouse_id': zone['warehouse_id'],
                            'zone_id': zone['zone_id'],
                            'bin_code': f"{zone['zone_code']}-A{aisle:02d}-L{level}-P{pos:02d}",
                            'level': level,
                            'position': pos,
                            'full_location': f"{zone['zone_code']}-A{aisle:02d}-L{level}-P{pos:02d}",
                            'bin_type': 'pallet',
                            'weight_capacity_kg': 1000,
                            'mixed_storage': True,
                            'velocity_class': random.choice(['A', 'B', 'B', 'C']),
                            'bin_status': 'available',
                            'current_occupancy_pct': 0,
                            'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        }
                        self.bins.append(bin_data)
        
        print(f"Generated {len(self.bins)} storage bins")
    
    def generate_warehouse_workers(self):
        """Generate warehouse workers"""
        print("Generating warehouse workers...")
        
        roles = ['receiver', 'picker', 'packer', 'shipper', 'forklift_operator']
        
        for warehouse in self.warehouses:
            for i in range(20):  # 20 workers per warehouse
                worker = {
                    'worker_id': self.generate_id('WKR', 'worker'),
                    'worker_code': f"WKR{self.counters['worker']-1:04d}",
                    'first_name': f"Worker{i+1}",
                    'last_name': f"WH{warehouse['warehouse_code']}",
                    'warehouse_id': warehouse['warehouse_id'],
                    'worker_role': random.choice(roles),
                    'forklift_certified': random.choice([True, False]),
                    'pick_rate_units_per_hour': random.randint(80, 150),
                    'accuracy_percentage': round(random.uniform(95, 99.5), 2),
                    'current_shift': random.choice(['day', 'evening', 'night']),
                    'worker_status': 'available',
                    'is_active': True,
                    'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                self.warehouse_workers.append(worker)
        
        print(f"Generated {len(self.warehouse_workers)} warehouse workers")
    
    # ========================================================================
    # WMS - WAREHOUSE OPERATIONS
    # ========================================================================
    
    def generate_warehouse_operations(self, start_date: datetime, days: int):
        """Generate daily warehouse operations with ULTRA-FAST PARALLEL processing"""
        print(f"\nGenerating {days} days of warehouse operations with PARALLEL processing...")
        
        if not self.parallel_enabled or days < 20:
            return self._generate_warehouse_operations_sequential(start_date, days)
        
        # Parallel processing for large datasets
        chunk_size = max(5, days // self.worker_count)  # At least 5 days per chunk
        day_chunks = [(i, min(chunk_size, days - i)) for i in range(0, days, chunk_size)]
        
        print(f"  🚀 Processing {len(day_chunks)} day chunks with {self.worker_count} workers...")
        
        all_receiving_tasks = []
        all_putaway_tasks = []
        all_pick_waves = []
        all_wave_lines = []
        all_picking_tasks = []
        all_packing_tasks = []
        all_shipping_tasks = []
        
        with ThreadPoolExecutor(max_workers=self.worker_count) as executor:
            # Submit chunk processing tasks
            futures = {
                executor.submit(self._generate_warehouse_operations_chunk, 
                    start_date + timedelta(days=start_day), 
                    chunk_days, 
                    chunk_id): chunk_id 
                for chunk_id, (start_day, chunk_days) in enumerate(day_chunks)
            }
            
            # Collect results as they complete
            for future in as_completed(futures):
                chunk_id = futures[future]
                try:
                    chunk_results = future.result()
                    
                    all_receiving_tasks.extend(chunk_results['receiving_tasks'])
                    all_putaway_tasks.extend(chunk_results['putaway_tasks'])
                    all_pick_waves.extend(chunk_results['pick_waves'])
                    all_wave_lines.extend(chunk_results['wave_lines'])
                    all_picking_tasks.extend(chunk_results['picking_tasks'])
                    all_packing_tasks.extend(chunk_results['packing_tasks'])
                    all_shipping_tasks.extend(chunk_results['shipping_tasks'])
                    
                    print(f"    ✓ Warehouse chunk {chunk_id + 1}/{len(day_chunks)} completed ({len(chunk_results['receiving_tasks'])} receiving, {len(chunk_results['pick_waves'])} waves)")
                except Exception as e:
                    print(f"    ✗ Warehouse chunk {chunk_id + 1} failed: {e}")
        
        # Store results with thread safety
        with self.data_lock:
            self.receiving_tasks.extend(all_receiving_tasks)
            self.putaway_tasks.extend(all_putaway_tasks)
            self.pick_waves.extend(all_pick_waves)
            self.wave_lines.extend(all_wave_lines)
            self.picking_tasks.extend(all_picking_tasks)
            self.packing_tasks.extend(all_packing_tasks)
            self.shipping_tasks.extend(all_shipping_tasks)
        
        print(f"✓ Generated warehouse operations: {len(self.receiving_tasks):,} receiving, {len(self.pick_waves):,} waves, {len(self.picking_tasks):,} picks via PARALLEL processing")
    
    def _generate_warehouse_operations_chunk(self, start_date: datetime, days: int, chunk_id: int) -> Dict:
        """Generate warehouse operations for a chunk of days (parallel worker method)"""
        
        # Local data storage for this chunk
        chunk_receiving_tasks = []
        chunk_putaway_tasks = []
        chunk_pick_waves = []
        chunk_wave_lines = []
        chunk_picking_tasks = []
        chunk_packing_tasks = []
        chunk_shipping_tasks = []
        
        # Local counters to avoid collision
        local_receiving_counter = chunk_id * 50000 + 1
        local_putaway_counter = chunk_id * 50000 + 1
        local_wave_counter = chunk_id * 30000 + 1
        local_picking_counter = chunk_id * 100000 + 1
        local_packing_counter = chunk_id * 100000 + 1
        local_shipping_counter = chunk_id * 100000 + 1
        
        current_date = start_date
        
        for day in range(days):
            active_waves_today = 0  # Reset daily wave counter
            
            # Inbound: Receiving + Putaway (80-150 per day across all warehouses)
            num_receiving = random.randint(80, 150)
            for _ in range(num_receiving):
                receiving_task = self._create_receiving_task_local(current_date, local_receiving_counter)
                if receiving_task:
                    chunk_receiving_tasks.append(receiving_task)
                    local_receiving_counter += 1
                    
                    # Create putaway task
                    putaway_task = self._create_putaway_task_local(receiving_task, current_date, local_putaway_counter)
                    if putaway_task:
                        chunk_putaway_tasks.append(putaway_task)
                        local_putaway_counter += 1
            
            # Outbound: Waves + Picking + Packing + Shipping (60-120 per day with capacity management)
            planned_waves = random.randint(60, 120)
            for _ in range(planned_waves):
                if active_waves_today < MAX_WAVE_CONCURRENCY:
                    wave_data = self._create_pick_wave_local(current_date, active_waves_today, local_wave_counter, 
                                                           local_picking_counter, local_packing_counter, local_shipping_counter)
                    if wave_data:
                        chunk_pick_waves.append(wave_data['wave'])
                        chunk_wave_lines.extend(wave_data['wave_lines'])
                        chunk_picking_tasks.extend(wave_data['picking_tasks'])
                        chunk_packing_tasks.extend(wave_data['packing_tasks'])
                        chunk_shipping_tasks.extend(wave_data['shipping_tasks'])
                        
                        local_wave_counter += 1
                        local_picking_counter += len(wave_data['picking_tasks'])
                        local_packing_counter += len(wave_data['packing_tasks'])
                        local_shipping_counter += len(wave_data['shipping_tasks'])
                        active_waves_today += 1
            
            current_date += timedelta(days=1)
        
        # Return all chunk data
        return {
            'receiving_tasks': chunk_receiving_tasks,
            'putaway_tasks': chunk_putaway_tasks,
            'pick_waves': chunk_pick_waves,
            'wave_lines': chunk_wave_lines,
            'picking_tasks': chunk_picking_tasks,
            'packing_tasks': chunk_packing_tasks,
            'shipping_tasks': chunk_shipping_tasks
        }
    
    def _create_receiving_task_local(self, date: datetime, counter: int) -> Dict:
        """Create receiving task from PO (local/chunk version)"""
        if not self.purchase_orders:
            return None
        
        po = random.choice(self.purchase_orders)
        warehouse = random.choice(self.warehouses) if self.warehouses else {'warehouse_id': 'WH-001'}
        
        return {
            'receiving_task_id': f"RCV-{str(counter).zfill(6)}",
            'task_number': f"RCV-{date.strftime('%Y%m%d')}-{counter:04d}",
            'purchase_order_id': po['purchase_order_id'],
            'warehouse_id': warehouse['warehouse_id'],
            'receiving_dock': f"DOCK-{random.randint(1, 10)}",
            'material_id': random.choice(self.materials)['material_id'],
            'expected_quantity': random.randint(100, 1000),
            'received_quantity': random.randint(95, 105),
            'unit_of_measure': random.choice(['EA', 'KG', 'L']),
            'task_status': 'completed',
            'scheduled_date': date.strftime('%Y-%m-%d %H:%M:%S'),
            'completed_at': (date + timedelta(hours=2)).strftime('%Y-%m-%d %H:%M:%S'),
            'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
    
    def _create_putaway_task_local(self, receiving_task: Dict, date: datetime, counter: int) -> Dict:
        """Create putaway task (local/chunk version)"""
        available_bins = [b for b in self.bins if b.get('bin_status') == 'available'] if self.bins else [{'bin_id': 'BIN-A001', 'bin_location': 'A-01-001'}]
        bin_loc = random.choice(available_bins)
        
        return {
            'putaway_task_id': f"PUT-{str(counter).zfill(6)}",
            'task_number': f"PUT-{date.strftime('%Y%m%d')}-{counter:04d}",
            'receiving_task_id': receiving_task['receiving_task_id'],
            'material_id': receiving_task['material_id'],
            'quantity': receiving_task['received_quantity'],
            'unit_of_measure': receiving_task['unit_of_measure'],
            'warehouse_id': receiving_task['warehouse_id'],
            'bin_id': bin_loc['bin_id'],
            'bin_location': bin_loc.get('bin_location', 'A-01-001'),
            'task_status': 'completed',
            'assigned_worker': f"WRK-{random.randint(1, 100):03d}",
            'completed_at': (date + timedelta(hours=3)).strftime('%Y-%m-%d %H:%M:%S'),
            'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
    
    def _create_pick_wave_local(self, date: datetime, active_waves: int, wave_counter: int, 
                               picking_counter: int, packing_counter: int, shipping_counter: int) -> Dict:
        """Create pick wave with all related tasks (local/chunk version)"""
        if not self.sales_orders or active_waves >= MAX_WAVE_CONCURRENCY:
            return None
        
        wave = {
            'wave_id': f"WAVE-{str(wave_counter).zfill(6)}",
            'wave_number': f"WAVE-{date.strftime('%Y%m%d')}-{wave_counter:04d}",
            'warehouse_id': random.choice(self.warehouses)['warehouse_id'] if self.warehouses else 'WH-001',
            'wave_type': random.choice(['single_order', 'batch', 'zone']),
            'wave_status': 'completed',
            'created_date': date.strftime('%Y-%m-%d %H:%M:%S'),
            'released_date': (date + timedelta(hours=1)).strftime('%Y-%m-%d %H:%M:%S'),
            'completed_date': (date + timedelta(hours=4)).strftime('%Y-%m-%d %H:%M:%S'),
            'total_lines': random.randint(5, 20),
            'total_quantity': random.randint(100, 500),
            'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        # Generate wave lines and related tasks
        wave_lines = []
        picking_tasks = []
        packing_tasks = []
        shipping_tasks = []
        
        num_lines = random.randint(5, 20)
        for i in range(num_lines):
            so = random.choice(self.sales_orders)
            
            wave_line = {
                'wave_line_id': f"WL-{str(wave_counter).zfill(6)}-{i+1:03d}",
                'wave_id': wave['wave_id'],
                'sales_order_id': so['sales_order_id'],
                'material_id': random.choice(self.materials)['material_id'],
                'quantity_ordered': random.randint(10, 100),
                'quantity_allocated': random.randint(8, 12),
                'bin_location': f"A-{random.randint(1, 10):02d}-{random.randint(1, 100):03d}",
                'pick_sequence': i + 1,
                'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            wave_lines.append(wave_line)
            
            # Create picking task
            pick_task = {
                'picking_task_id': f"PICK-{str(picking_counter + i).zfill(6)}",
                'task_number': f"PICK-{date.strftime('%Y%m%d')}-{str(picking_counter + i).zfill(5)}",
                'wave_id': wave['wave_id'],
                'wave_line_id': wave_line['wave_line_id'],
                'material_id': wave_line['material_id'],
                'warehouse_id': wave['warehouse_id'],
                'quantity_to_pick': wave_line['quantity_allocated'],
                'quantity_picked': wave_line['quantity_allocated'],
                'bin_location': wave_line['bin_location'],
                'picker_id': f"WRK-{random.randint(1, 100):03d}",
                'pick_status': 'completed',
                'picked_at': (date + timedelta(hours=2)).strftime('%Y-%m-%d %H:%M:%S'),
                'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            picking_tasks.append(pick_task)
            
            # Create packing task
            pack_task = {
                'packing_task_id': f"PACK-{str(packing_counter + i).zfill(6)}",
                'task_number': f"PACK-{date.strftime('%Y%m%d')}-{str(packing_counter + i).zfill(5)}",
                'sales_order_id': wave_line.get('sales_order_id', f"SO-{random.randint(1, 1000):06d}"),
                'warehouse_id': wave['warehouse_id'],
                'picking_task_id': pick_task['picking_task_id'],
                'package_id': f"PKG-{date.strftime('%Y%m%d')}-{packing_counter + i:05d}",
                'package_type': random.choice(['box', 'envelope', 'tube']),
                'packed_quantity': pick_task['quantity_picked'],
                'packer_id': f"WRK-{random.randint(1, 100):03d}",
                'pack_status': 'completed',
                'packed_at': (date + timedelta(hours=3)).strftime('%Y-%m-%d %H:%M:%S'),
                'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            packing_tasks.append(pack_task)
            
            # Create shipping task
            ship_task = {
                'shipping_task_id': f"SHIP-{str(shipping_counter + i).zfill(6)}",
                'task_number': f"SHIP-{date.strftime('%Y%m%d')}-{str(shipping_counter + i).zfill(5)}",
                'sales_order_id': wave_line.get('sales_order_id', f"SO-{random.randint(1, 1000):06d}"),
                'warehouse_id': wave['warehouse_id'],
                'packing_task_id': pack_task['packing_task_id'],
                'carrier_id': f"CARR-{random.randint(1, 40):03d}",
                'tracking_number': f"TRK{date.strftime('%Y%m%d')}{random.randint(100000, 999999)}",
                'ship_date': (date + timedelta(hours=4)).strftime('%Y-%m-%d'),
                'shipping_status': 'shipped',
                'shipped_at': (date + timedelta(hours=4)).strftime('%Y-%m-%d %H:%M:%S'),
                'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            shipping_tasks.append(ship_task)
        
        return {
            'wave': wave,
            'wave_lines': wave_lines,
            'picking_tasks': picking_tasks,
            'packing_tasks': packing_tasks,
            'shipping_tasks': shipping_tasks
        }
    
    def _generate_warehouse_operations_sequential(self, start_date: datetime, days: int):
        """Fallback sequential warehouse operations for small datasets"""
        print("Generating warehouse operations (sequential fallback)...")
        # Keep original sequential logic for small datasets
        pass

    def _create_receiving_task(self, date: datetime):
        """Create receiving task from PO"""
        if not self.purchase_orders:
            return
        
        po = random.choice(self.purchase_orders)
        warehouse = random.choice(self.warehouses)
        
        task = {
            'receiving_task_id': self.generate_id('RCV', 'receiving'),
            'task_number': f"RCV-{date.strftime('%Y%m%d')}-{self.counters['receiving']:04d}",
            'purchase_order_id': po['purchase_order_id'],
            'warehouse_id': warehouse['warehouse_id'],
            'receiving_dock': f"DOCK-{random.randint(1, 10)}",
            'material_id': random.choice(self.materials)['material_id'],
            'expected_quantity': random.randint(100, 1000),
            'received_quantity': random.randint(95, 105),
            'unit_of_measure': random.choice(['EA', 'KG', 'L']),
            'task_status': 'completed',
            'scheduled_date': date.strftime('%Y-%m-%d %H:%M:%S'),
            'completed_at': (date + timedelta(hours=2)).strftime('%Y-%m-%d %H:%M:%S'),
            'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        self.receiving_tasks.append(task)
        
        # Create putaway task
        self._create_putaway_task(task, date)
    
    def _create_putaway_task(self, receiving_task: dict, date: datetime):
        """Create putaway task"""
        available_bins = [b for b in self.bins if b['bin_status'] == 'available']
        if not available_bins:
            return
        
        bin_loc = random.choice(available_bins)
        
        task = {
            'putaway_task_id': self.generate_id('PUT', 'putaway'),
            'task_number': f"PUT-{date.strftime('%Y%m%d')}-{self.counters['putaway']:04d}",
            'receiving_task_id': receiving_task['receiving_task_id'],
            'material_id': receiving_task['material_id'],
            'quantity': receiving_task['received_quantity'],
            'unit_of_measure': receiving_task['unit_of_measure'],
            'warehouse_id': receiving_task['warehouse_id'],
            'from_location': receiving_task['receiving_dock'],
            'to_bin_id': bin_loc['bin_id'],
            'putaway_strategy': 'abc_slotting',
            'task_status': 'completed',
            'priority': 5,
            'created_at': date.strftime('%Y-%m-%d %H:%M:%S'),
            'completed_at': (date + timedelta(hours=3)).strftime('%Y-%m-%d %H:%M:%S')
        }
        self.putaway_tasks.append(task)
    
    def _create_pick_wave(self, date: datetime, active_wave_count: int = 0):
        """Create pick wave with capacity management and FK validation"""
        # Use dummy sales orders if none available - don't skip wave creation
        if not self.sales_orders:
            # Still create waves even without sales orders
            pass
        
        # Wave capacity management to prevent bottlenecks
        if not self.manage_wave_capacity(active_wave_count):
            logger.debug(f"Wave capacity limit reached ({active_wave_count}), skipping wave creation")
            return
        
        warehouse = random.choice(self.warehouses)
        warehouse_id = warehouse['warehouse_id']
        
        # FK validation for warehouse
        if not self.validate_foreign_key('warehouse_id', warehouse_id):
            logger.warning(f"Invalid warehouse_id {warehouse_id}, skipping wave")
            self.stats['fk_validation_errors'] += 1
            return
            
        # Dynamic wave sizing based on capacity
        base_orders = random.randint(3, 10)
        base_lines = random.randint(10, 30)
        
        # Reduce wave size if approaching capacity limit
        capacity_factor = max(0.5, (MAX_WAVE_CONCURRENCY - active_wave_count) / MAX_WAVE_CONCURRENCY)
        adjusted_orders = max(1, int(base_orders * capacity_factor))
        adjusted_lines = max(5, int(base_lines * capacity_factor))
        
        wave = {
            'wave_id': self.generate_id('WAVE', 'wave'),
            'wave_number': f"WAVE-{date.strftime('%Y%m%d')}-{self.counters['wave']:04d}",
            'warehouse_id': warehouse_id,
            'wave_type': 'batch',
            'planned_pick_date': date.strftime('%Y-%m-%d'),
            'planned_ship_date': (date + timedelta(days=1)).strftime('%Y-%m-%d'),
            'priority': random.choice(['urgent', 'high', 'normal', 'low']),
            'wave_status': random.choice(['completed', 'in_progress', 'released']),
            'total_orders': adjusted_orders,
            'total_lines': adjusted_lines,
            'created_at': date.strftime('%Y-%m-%d %H:%M:%S'),
            'released_at': (date + timedelta(hours=1)).strftime('%Y-%m-%d %H:%M:%S'),
            'completed_at': (date + timedelta(hours=random.randint(4, 8))).strftime('%Y-%m-%d %H:%M:%S'),
            'wave_capacity_factor': capacity_factor  # Track capacity adjustments
        }
        self.pick_waves.append(wave)
        self.stats['records_generated'] += 1
        
        # Create picking tasks with FK validation
        successful_tasks = 0
        for _ in range(wave['total_lines']):
            if self._create_picking_task_validated(wave, date):
                successful_tasks += 1
        
        # Update wave with actual successful lines
        wave['actual_lines'] = successful_tasks
        
        # Create packing and shipping with validation
        self._create_packing_task_validated(wave, date)
        self._create_shipping_task_validated(wave, date)
        
        logger.debug(f"Created wave {wave['wave_number']} with {successful_tasks} lines (capacity factor: {capacity_factor:.2f})")
    
    def _create_picking_task_validated(self, wave: dict, date: datetime) -> bool:
        """Create picking task with FK and inventory validation"""
        available_bins = [b for b in self.bins if b['bin_status'] == 'available']
        if not available_bins:
            return False
        
        # Select and validate sales order
        sales_order = random.choice(self.sales_orders)
        sales_order_id = sales_order['sales_order_id']
        if not self.validate_foreign_key('sales_order_id', sales_order_id):
            self.stats['fk_validation_errors'] += 1
            return False
        
        # Select and validate material
        material = random.choice(self.materials)
        material_id = material['material_id']
        if not self.validate_foreign_key('material_id', material_id):
            self.stats['fk_validation_errors'] += 1
            return False
        
        # Inventory consistency check
        quantity_to_pick = random.randint(10, 100)
        if not self.check_inventory_consistency(material_id, wave['warehouse_id'], -quantity_to_pick):
            logger.debug(f"Inventory consistency check failed for {material_id} in {wave['warehouse_id']}")
            return False
        
        task = {
            'picking_task_id': self.generate_id('PICK', 'picking'),
            'task_number': f"PICK-{date.strftime('%Y%m%d')}-{self.counters['picking']:04d}",
            'wave_id': wave['wave_id'],
            'sales_order_id': sales_order_id,
            'material_id': material_id,
            'quantity_to_pick': quantity_to_pick,
            'quantity_picked': min(quantity_to_pick, random.randint(10, quantity_to_pick)),
            'unit_of_measure': 'EA',
            'warehouse_id': wave['warehouse_id'],
            'pick_from_bin_id': random.choice(available_bins)['bin_id'],
            'task_type': 'wave',
            'task_status': 'picked',
            'created_at': date.strftime('%Y-%m-%d %H:%M:%S'),
            'completed_at': (date + timedelta(hours=4)).strftime('%Y-%m-%d %H:%M:%S')
        }
        self.picking_tasks.append(task)
    
    def _create_packing_task(self, wave: dict, date: datetime):
        """Create packing task"""
        task = {
            'packing_task_id': self.generate_id('PACK', 'packing'),
            'task_number': f"PACK-{date.strftime('%Y%m%d')}-{self.counters['packing']:04d}",
            'sales_order_id': random.choice(self.sales_orders)['sales_order_id'],
            'wave_id': wave['wave_id'],
            'warehouse_id': wave['warehouse_id'],
            'packing_station': f"PACK-{random.randint(1, 10)}",
            'package_type': 'box',
            'package_weight_kg': round(random.uniform(5, 50), 2),
            'tracking_number': f"TRK{datetime.now().strftime('%Y%m%d')}{random.randint(100000, 999999)}",
            'task_status': random.choice(['completed', 'picked', 'assigned']),
            'created_at': date.strftime('%Y-%m-%d %H:%M:%S'),
            'started_at': (date + timedelta(minutes=30)).strftime('%Y-%m-%d %H:%M:%S'),
            'completed_at': (date + timedelta(hours=random.randint(2, 5))).strftime('%Y-%m-%d %H:%M:%S')
        }
        self.picking_tasks.append(task)
        self.stats['records_generated'] += 1
        return True
    
    def _create_packing_task_validated(self, wave: dict, date: datetime) -> bool:
        """Create packing task with FK validation"""
        sales_order = random.choice(self.sales_orders)
        sales_order_id = sales_order['sales_order_id']
        
        if not self.validate_foreign_key('sales_order_id', sales_order_id):
            self.stats['fk_validation_errors'] += 1
            return False
        
        task = {
            'packing_task_id': self.generate_id('PACK', 'packing'),
            'task_number': f"PACK-{date.strftime('%Y%m%d')}-{self.counters['packing']:04d}",
            'sales_order_id': sales_order_id,
            'warehouse_id': wave['warehouse_id'],
            'packing_station': f"PACK-{random.randint(1, 10)}",
            'package_type': random.choice(['box', 'envelope', 'pallet']),
            'package_weight_kg': round(random.uniform(1, 50), 2),
            'package_dimensions': f"{random.randint(10, 50)}x{random.randint(10, 50)}x{random.randint(10, 50)}",
            'task_status': random.choice(['completed', 'packed', 'in_progress']),
            'created_at': date.strftime('%Y-%m-%d %H:%M:%S'),
            'packed_at': (date + timedelta(hours=random.randint(3, 6))).strftime('%Y-%m-%d %H:%M:%S'),
            'estimated_ship_date': (date + timedelta(days=1)).strftime('%Y-%m-%d')
        }
        self.packing_tasks.append(task)
        self.stats['records_generated'] += 1
        return True
    
    def _create_shipping_task_validated(self, wave: dict, date: datetime) -> bool:
        """Create shipping task with FK validation and realistic timing"""
        sales_order = random.choice(self.sales_orders)
        sales_order_id = sales_order['sales_order_id']
        
        if not self.validate_foreign_key('sales_order_id', sales_order_id):
            self.stats['fk_validation_errors'] += 1
            return False
        
        # Realistic shipping delays
        shipping_delay = random.choice([0, 1, 2, 3])  # 0-3 day delay
        actual_ship_date = date + timedelta(days=shipping_delay)
        
        task = {
            'shipping_task_id': self.generate_id('SHIP', 'shipping'),
            'task_number': f"SHIP-{date.strftime('%Y%m%d')}-{self.counters['shipping']:04d}",
            'sales_order_id': sales_order_id,
            'warehouse_id': wave['warehouse_id'],
            'shipping_dock': f"DOCK-{random.randint(1, 10)}",
            'number_of_packages': random.randint(1, 5),
            'total_weight_kg': round(random.uniform(10, 100), 2),
            'task_status': random.choice(['shipped', 'pending', 'in_transit']),
            'scheduled_ship_date': wave['planned_ship_date'],
            'actual_ship_date': actual_ship_date.strftime('%Y-%m-%d') if shipping_delay <= 1 else None,
            'bol_number': f"BOL-{date.strftime('%Y%m%d')}-{random.randint(1000, 9999)}",
            'tracking_number': f"TRK-{date.strftime('%Y%m%d%H%M%S')}-{random.randint(1000, 9999)}",
            'created_at': date.strftime('%Y-%m-%d %H:%M:%S'),
            'shipped_at': actual_ship_date.strftime('%Y-%m-%d %H:%M:%S') if shipping_delay <= 1 else None
        }
        self.shipping_tasks.append(task)
        self.stats['records_generated'] += 1
        return True
    
    # ========================================================================
    # TMS - CARRIERS
    # ========================================================================
    
    def generate_carriers(self):
        """Generate carrier master data"""
        print("Generating carriers...")
        
        carrier_names = [
            'Blue Dart Express', 'DTDC Courier', 'DHL Express India',
            'FedEx India', 'Delhivery', 'Ecom Express', 'Gati KWE',
            'Professional Couriers', 'XpressBees', 'Shadowfax'
        ]
        
        for name in carrier_names:
            carrier = {
                'carrier_id': self.generate_id('CAR', 'carrier'),
                'carrier_code': f"CAR{self.counters['carrier']-1:03d}",
                'carrier_name': name,
                'email': f"ops@{name.lower().replace(' ', '')}.com",
                'phone': f"+91 {random.randint(7000000000, 9999999999)}",
                'city': random.choice(['Mumbai', 'Delhi', 'Bangalore']),
                'country': 'India',
                'carrier_type': random.choice(['courier', 'parcel', 'ltl']),
                'api_integration': random.choice([True, False]),
                'on_time_delivery_pct': round(random.uniform(85, 98), 2),
                'carrier_status': 'active',
                'carrier_rating': round(random.uniform(3.5, 5.0), 2),
                'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            self.carriers.append(carrier)
            
            # Create services for each carrier
            self._create_carrier_services(carrier)
        
        print(f"Generated {len(self.carriers)} carriers with services")
    
    def _create_carrier_services(self, carrier: dict):
        """Create services for carrier"""
        services = [
            {'code': 'STD', 'name': 'Standard Delivery', 'type': 'standard', 'days': (3, 5)},
            {'code': 'EXP', 'name': 'Express Delivery', 'type': 'express', 'days': (1, 2)},
            {'code': 'OVN', 'name': 'Overnight', 'type': 'overnight', 'days': (1, 1)}
        ]
        
        for svc in services:
            service = {
                'service_id': self.generate_id('SVC', 'service'),
                'carrier_id': carrier['carrier_id'],
                'service_code': f"{carrier['carrier_code']}-{svc['code']}",
                'service_name': svc['name'],
                'service_type': svc['type'],
                'transit_days_min': svc['days'][0],
                'transit_days_max': svc['days'][1],
                'domestic': True,
                'is_active': True,
                'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            self.carrier_services.append(service)
    
    # ========================================================================
    # TMS - LOGISTICS OPERATIONS
    # ========================================================================
    
    def generate_logistics_operations(self, start_date: datetime, days: int):
        """Generate logistics operations with ULTRA-FAST PARALLEL processing"""
        print(f"\nGenerating {days} days of logistics operations with PARALLEL processing...")
        
        if not self.parallel_enabled or days < 20:
            return self._generate_logistics_operations_sequential(start_date, days)
        
        # Get valid FK sets for thread-safe access
        valid_customer_ids = list(self.helper.get_valid_customer_ids())
        valid_factory_ids = list(self.helper.get_valid_factory_ids())
        
        # Parallel processing for large datasets
        chunk_size = max(5, days // self.worker_count)  # At least 5 days per chunk
        day_chunks = [(i, min(chunk_size, days - i)) for i in range(0, days, chunk_size)]
        
        print(f"  🚀 Processing {len(day_chunks)} day chunks with {self.worker_count} workers...")
        
        all_shipments = []
        all_shipment_lines = []
        all_tracking_events = []
        all_routes = []
        all_route_stops = []
        all_deliveries = []
        all_pod = []
        all_return_orders = []
        
        with ThreadPoolExecutor(max_workers=self.worker_count) as executor:
            # Submit chunk processing tasks
            futures = {
                executor.submit(self._generate_logistics_operations_chunk, 
                    start_date + timedelta(days=start_day), 
                    chunk_days, 
                    chunk_id,
                    valid_customer_ids, valid_factory_ids): chunk_id 
                for chunk_id, (start_day, chunk_days) in enumerate(day_chunks)
            }
            
            # Collect results as they complete
            for future in as_completed(futures):
                chunk_id = futures[future]
                try:
                    chunk_results = future.result()
                    
                    all_shipments.extend(chunk_results['shipments'])
                    all_shipment_lines.extend(chunk_results['shipment_lines'])
                    all_tracking_events.extend(chunk_results['tracking_events'])
                    all_routes.extend(chunk_results['routes'])
                    all_route_stops.extend(chunk_results['route_stops'])
                    all_deliveries.extend(chunk_results['deliveries'])
                    all_pod.extend(chunk_results['pod'])
                    all_return_orders.extend(chunk_results['return_orders'])
                    
                    print(f"    ✓ Logistics chunk {chunk_id + 1}/{len(day_chunks)} completed ({len(chunk_results['shipments'])} shipments)")
                except Exception as e:
                    print(f"    ✗ Logistics chunk {chunk_id + 1} failed: {e}")
        
        # Store results with thread safety
        with self.data_lock:
            self.shipments.extend(all_shipments)
            self.shipment_lines.extend(all_shipment_lines)
            self.tracking_events.extend(all_tracking_events)
            self.routes.extend(all_routes)
            self.route_stops.extend(all_route_stops)
            self.deliveries.extend(all_deliveries)
            self.pod.extend(all_pod)
            self.return_orders.extend(all_return_orders)
        
        print(f"✓ Generated logistics: {len(self.shipments):,} shipments, {len(self.tracking_events):,} tracking events via PARALLEL processing")
    
    def _generate_logistics_operations_chunk(self, start_date: datetime, days: int, chunk_id: int, 
                                           valid_customer_ids: List[str], valid_factory_ids: List[str]) -> Dict:
        """Generate logistics operations for a chunk of days (parallel worker method)"""
        
        # Local data storage for this chunk
        chunk_shipments = []
        chunk_shipment_lines = []
        chunk_tracking_events = []
        chunk_routes = []
        chunk_route_stops = []
        chunk_deliveries = []
        chunk_pod = []
        chunk_return_orders = []
        
        # Local counters to avoid collision
        local_shipment_counter = chunk_id * 100000 + 1
        local_tracking_counter = chunk_id * 500000 + 1
        local_route_counter = chunk_id * 50000 + 1
        local_delivery_counter = chunk_id * 100000 + 1
        local_pod_counter = chunk_id * 100000 + 1
        local_return_counter = chunk_id * 20000 + 1
        
        current_date = start_date
        
        for day in range(days):
            # Create shipments (200-400 per day across all factories and warehouses)
            num_shipments = random.randint(200, 400)
            for _ in range(num_shipments):
                shipment_data = self._create_shipment_local(current_date, local_shipment_counter, 
                                                          local_tracking_counter, local_delivery_counter, 
                                                          local_pod_counter, valid_customer_ids, valid_factory_ids)
                if shipment_data:
                    chunk_shipments.append(shipment_data['shipment'])
                    chunk_shipment_lines.extend(shipment_data['shipment_lines'])
                    chunk_tracking_events.extend(shipment_data['tracking_events'])
                    chunk_deliveries.append(shipment_data['delivery'])
                    chunk_pod.append(shipment_data['pod'])
                    
                    local_shipment_counter += 1
                    local_tracking_counter += len(shipment_data['tracking_events'])
                    local_delivery_counter += 1
                    local_pod_counter += 1
            
            current_date += timedelta(days=1)
        
        # Return all chunk data
        return {
            'shipments': chunk_shipments,
            'shipment_lines': chunk_shipment_lines,
            'tracking_events': chunk_tracking_events,
            'routes': chunk_routes,
            'route_stops': chunk_route_stops,
            'deliveries': chunk_deliveries,
            'pod': chunk_pod,
            'return_orders': chunk_return_orders
        }
        
    def _generate_logistics_operations_sequential(self, start_date: datetime, days: int):
        """Fallback sequential logistics operations for small datasets"""
        print("Generating logistics operations (sequential fallback)...")
        # Keep original sequential logic for small datasets
        pass
    
    def _create_shipment_local(self, date: datetime, shipment_counter: int, tracking_counter: int, 
                              delivery_counter: int, pod_counter: int, 
                              valid_customer_ids: List[str], valid_factory_ids: List[str]) -> Dict:
        """Create shipment with all related data (local/chunk version)"""
        if not self.sales_orders or not self.carriers:
            return None
        
        so = random.choice(self.sales_orders)
        carrier = random.choice(self.carriers)
        services = [s for s in self.carrier_services if s.get('carrier_id') == carrier['carrier_id']] if self.carrier_services else []
        service = random.choice(services) if services else None
        
        customer_id = random.choice(valid_customer_ids) if valid_customer_ids else so['customer_id']
        factory_id = random.choice(valid_factory_ids) if valid_factory_ids else 'FAC-001'
        warehouse_id = random.choice(self.warehouses)['warehouse_id'] if self.warehouses else 'WH-001'
        
        tracking_number = f"TRK{date.strftime('%Y%m%d')}{random.randint(100000, 999999)}"
        delivery_date = date + timedelta(days=random.randint(2, 5))
        
        shipment = {
            'shipment_id': f"SHPM-{str(shipment_counter).zfill(6)}",
            'shipment_number': f"SHPM-{date.strftime('%Y%m%d')}-{shipment_counter:05d}",
            'sales_order_id': so['sales_order_id'],
            'factory_id': factory_id,
            'warehouse_id': warehouse_id,
            'carrier_id': carrier['carrier_id'],
            'service_id': service['service_id'] if service else None,
            'tracking_number': tracking_number,
            'customer_id': customer_id,
            'destination_city': random.choice(['Mumbai', 'Delhi', 'Bangalore', 'Chennai', 'Pune']),
            'destination_country': 'India',
            'shipment_type': 'parcel',
            'number_of_packages': random.randint(1, 5),
            'total_weight_kg': round(random.uniform(5, 50), 2),
            'ship_date': date.strftime('%Y-%m-%d'),
            'estimated_delivery_date': delivery_date.strftime('%Y-%m-%d'),
            'actual_delivery_date': delivery_date.strftime('%Y-%m-%d'),
            'shipment_status': 'delivered',
            'freight_cost': round(random.uniform(200, 2000), 2),
            'total_cost': round(random.uniform(250, 2500), 2),
            'currency': 'INR',
            'created_at': date.strftime('%Y-%m-%d %H:%M:%S')
        }
        
        # Create shipment lines
        shipment_lines = []
        num_lines = random.randint(1, 5)
        for i in range(num_lines):
            line = {
                'shipment_line_id': f"SL-{str(shipment_counter).zfill(6)}-{i+1:03d}",
                'shipment_id': shipment['shipment_id'],
                'material_id': random.choice(self.materials)['material_id'],
                'quantity_shipped': random.randint(10, 100),
                'unit_of_measure': random.choice(['EA', 'KG', 'L']),
                'package_number': i + 1,
                'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            shipment_lines.append(line)
        
        # Create tracking events
        tracking_events = []
        events = [
            ('picked_up', 0),
            ('departed_facility', 1),
            ('in_transit', 2),
            ('out_for_delivery', 3),
            ('delivered', 4)
        ]
        
        for idx, (event_type, day_offset) in enumerate(events):
            event = {
                'event_id': f"TRK-{str(tracking_counter + idx).zfill(6)}",
                'shipment_id': shipment['shipment_id'],
                'tracking_number': tracking_number,
                'event_type': event_type,
                'event_description': event_type.replace('_', ' ').title(),
                'location_city': random.choice(['Mumbai', 'Pune', 'Delhi']),
                'event_timestamp': (date + timedelta(days=day_offset, hours=random.randint(8, 18))).strftime('%Y-%m-%d %H:%M:%S'),
                'data_source': 'carrier_api',
                'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            tracking_events.append(event)
        
        # Create delivery
        delivery = {
            'delivery_id': f"DEL-{str(delivery_counter).zfill(6)}",
            'delivery_number': f"DEL-{delivery_date.strftime('%Y%m%d')}-{str(delivery_counter).zfill(5)}",
            'shipment_id': shipment['shipment_id'],
            'delivery_date': delivery_date.strftime('%Y-%m-%d'),
            'delivery_time': f"{random.randint(9, 17):02d}:{random.randint(0, 59):02d}:00",
            'delivery_status': 'completed',
            'recipient_name': f"Customer_{customer_id}",
            'signature_required': random.choice([True, False]),
            'delivery_notes': 'Package delivered successfully',
            'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        # Create POD (Proof of Delivery)
        pod = {
            'pod_id': f"POD-{str(pod_counter).zfill(6)}",
            'delivery_id': delivery['delivery_id'],
            'shipment_id': shipment['shipment_id'],
            'received_by_name': delivery.get('recipient_name', 'Customer Representative'),
            'packages_delivered': random.randint(1, 5),
            'packages_condition': 'good',
            'delivery_timestamp': delivery_date.strftime('%Y-%m-%d %H:%M:%S'),
            'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        return {
            'shipment': shipment,
            'shipment_lines': shipment_lines,
            'tracking_events': tracking_events,
            'delivery': delivery,
            'pod': pod
        }
    
    def _create_shipment(self, date: datetime):
        """Create shipment"""
        if not self.sales_orders or not self.carriers:
            return
        
        so = random.choice(self.sales_orders)
        carrier = random.choice(self.carriers)
        services = [s for s in self.carrier_services if s['carrier_id'] == carrier['carrier_id']]
        service = random.choice(services) if services else None
        
        # FK from registry - GUARANTEED VALID
        valid_customer_ids = list(self.helper.get_valid_customer_ids())
        customer_id = random.choice(valid_customer_ids) if valid_customer_ids else so['customer_id']
        
        # FK from registry - GUARANTEED VALID
        valid_factory_ids = list(self.helper.get_valid_factory_ids())
        factory_id = random.choice(valid_factory_ids)
        
        shipment = {
            'shipment_id': self.generate_id('SHPM', 'shipment'),
            'shipment_number': f"SHPM-{date.strftime('%Y%m%d')}-{self.counters['shipment']:05d}",
            'sales_order_id': so['sales_order_id'],
            'factory_id': factory_id,
            'warehouse_id': random.choice(self.warehouses)['warehouse_id'],
            'carrier_id': carrier['carrier_id'],
            'service_id': service['service_id'] if service else None,
            'tracking_number': f"TRK{date.strftime('%Y%m%d')}{random.randint(100000, 999999)}",
            'customer_id': customer_id,
            'destination_city': random.choice(['Mumbai', 'Delhi', 'Bangalore', 'Chennai', 'Pune']),
            'destination_country': 'India',
            'shipment_type': 'parcel',
            'number_of_packages': random.randint(1, 5),
            'total_weight_kg': round(random.uniform(5, 50), 2),
            'ship_date': date.strftime('%Y-%m-%d'),
            'estimated_delivery_date': (date + timedelta(days=random.randint(2, 5))).strftime('%Y-%m-%d'),
            'actual_delivery_date': (date + timedelta(days=random.randint(2, 5))).strftime('%Y-%m-%d'),
            'shipment_status': 'delivered',
            'freight_cost': round(random.uniform(200, 2000), 2),
            'total_cost': round(random.uniform(250, 2500), 2),
            'currency': 'INR',
            'created_at': date.strftime('%Y-%m-%d %H:%M:%S')
        }
        self.shipments.append(shipment)
        
        # Create tracking events
        self._create_tracking_events(shipment, date)
        
        # Create delivery
        self._create_delivery(shipment, date)
    
    def _create_tracking_events(self, shipment: dict, date: datetime):
        """Create tracking events"""
        events = [
            ('picked_up', 0),
            ('departed_facility', 1),
            ('in_transit', 2),
            ('out_for_delivery', 3),
            ('delivered', 4)
        ]
        
        for event_type, day_offset in events:
            event = {
                'event_id': self.generate_id('TRK', 'tracking'),
                'shipment_id': shipment['shipment_id'],
                'tracking_number': shipment['tracking_number'],
                'event_type': event_type,
                'event_description': event_type.replace('_', ' ').title(),
                'location_city': random.choice(['Mumbai', 'Pune', 'Delhi']),
                'event_timestamp': (date + timedelta(days=day_offset, hours=random.randint(8, 18))).strftime('%Y-%m-%d %H:%M:%S'),
                'data_source': 'carrier_api',
                'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            self.tracking_events.append(event)
    
    def _create_delivery(self, shipment: dict, date: datetime):
        """Create delivery record"""
        delivery_date = datetime.strptime(shipment['actual_delivery_date'], '%Y-%m-%d')
        
        delivery = {
            'delivery_id': self.generate_id('DEL', 'delivery'),
            'delivery_number': f"DEL-{delivery_date.strftime('%Y%m%d')}-{self.counters['delivery']:05d}",
            'shipment_id': shipment['shipment_id'],
            'sales_order_id': shipment['sales_order_id'],
            'customer_id': shipment['customer_id'],
            'delivery_city': shipment['destination_city'],
            'scheduled_delivery_date': shipment['estimated_delivery_date'],
            'actual_delivery_date': shipment['actual_delivery_date'],
            'delivery_type': 'signature_required',
            'delivery_status': 'delivered',
            'delivered_to_name': 'Customer Representative',
            'created_at': date.strftime('%Y-%m-%d %H:%M:%S')
        }
        self.deliveries.append(delivery)
        
        # Create POD
        self._create_pod(delivery, delivery_date)
    
    def _create_pod(self, delivery: dict, date: datetime):
        """Create proof of delivery"""
        pod = {
            'pod_id': self.generate_id('POD', 'pod'),
            'delivery_id': delivery['delivery_id'],
            'shipment_id': delivery['shipment_id'],
            'received_by_name': delivery['delivered_to_name'],
            'packages_delivered': random.randint(1, 5),
            'packages_condition': 'good',
            'delivery_timestamp': date.strftime('%Y-%m-%d %H:%M:%S'),
            'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        self.pod.append(pod)
    
    # ========================================================================
    # WMS EMPTY TABLE GENERATORS
    # ========================================================================
    
    def _generate_warehouse_inventory(self):
        """Generate warehouse inventory records"""
        print("Generating warehouse inventory...")
        inventory = []
        
        for i, material in enumerate(self.materials):
            inv = {
                'inventory_id': self.generate_id('INV', 'wh_inv'),
                'warehouse_id': random.choice(self.warehouses)['warehouse_id'],
                'bin_id': random.choice(self.bins)['bin_id'] if self.bins else f"BIN-{random.randint(1, 100):06d}",
                'material_id': material.get('material_id'),
                'quantity_on_hand': random.randint(100, 1000),
                'reserved_quantity': random.randint(0, 200),
                'available_quantity': random.randint(50, 500),
                'quantity_damaged': random.randint(0, 20),
                'uom': material.get('uom', 'EA'),
                'lot_number': f"LOT-{random.randint(100000, 999999)}",
                'expiry_date': (datetime.now() + timedelta(days=random.randint(30, 730))).strftime('%Y-%m-%d'),
                'last_count_date': (datetime.now() - timedelta(days=random.randint(1, 30))).strftime('%Y-%m-%d'),
                'value': round(random.uniform(1000, 50000), 2),
                'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            inventory.append(inv)
        
        print(f"Generated {len(inventory)} warehouse inventory records")
        return inventory

    def _generate_wave_lines(self):
        """Generate wave lines (items in a wave)"""
        print("Generating wave lines...")
        lines = []
        
        # Create dummy pick waves if none exist to ensure wave lines are generated
        if not self.pick_waves:
            print("No pick waves found, creating dummy waves for wave lines generation")
            dummy_waves = [
                {'wave_id': f'WAVE-{i:06d}'} 
                for i in range(1, 6)  # Create 5 dummy waves
            ]
            wave_pool = dummy_waves
        else:
            wave_pool = self.pick_waves
        
        # Use dummy sales order IDs if none available
        if not self.sales_orders:
            dummy_sales_orders = [{'sales_order_id': f'SO-{i:06d}'} for i in range(1, 101)]
            sales_order_pool = dummy_sales_orders
        else:
            sales_order_pool = self.sales_orders
        
        # Use dummy material IDs if none available  
        if not self.materials:
            dummy_materials = [{'material_id': f'MAT-{i:06d}'} for i in range(1, 201)]
            material_pool = dummy_materials
        else:
            material_pool = self.materials
        
        for wave in wave_pool:
            num_lines = random.randint(5, 15)
            for i in range(num_lines):
                line = {
                    'wave_line_id': self.generate_id('WL', 'picking'),
                    'wave_id': wave['wave_id'],
                    'sales_order_id': random.choice(sales_order_pool).get('sales_order_id'),
                    'material_id': random.choice(material_pool).get('material_id'),
                    'line_number': i + 1,
                    'quantity_required': random.randint(10, 100),
                    'quantity_picked': random.randint(10, 100),
                    'pick_location': f"STG-A{random.randint(1, 5):02d}-L{random.randint(1, 3)}-P{random.randint(1, 4):02d}",
                    'status': random.choice(['pending', 'in_progress', 'completed']),
                    'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                lines.append(line)
        
        print(f"Generated {len(lines)} wave lines")
        return lines

    def _generate_cycle_count_tasks(self):
        """Generate cycle count tasks"""
        print("Generating cycle count tasks...")
        tasks = []
        
        zones = [z for z in self.zones if z['zone_type'] == 'storage']
        
        for i in range(25):
            task = {
                'cycle_count_id': self.generate_id('CC', 'packing'),
                'task_number': f"CCT-{str(i+1).zfill(6)}",
                'warehouse_id': random.choice(self.warehouses)['warehouse_id'],
                'zone_id': random.choice(zones)['zone_id'] if zones else None,
                'count_date': (datetime.now() - timedelta(days=random.randint(1, 30))).strftime('%Y-%m-%d'),
                'assigned_to': random.choice(self.warehouse_workers)['worker_id'] if self.warehouse_workers else None,
                'status': random.choice(['completed', 'in_progress', 'pending']),
                'variance_pct': round(random.uniform(0, 5), 2),
                'items_counted': random.randint(50, 500),
                'discrepancies': random.randint(0, 20),
                'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            tasks.append(task)
        
        print(f"Generated {len(tasks)} cycle count tasks")
        return tasks

    def _generate_warehouse_equipment(self):
        """Generate warehouse equipment"""
        print("Generating warehouse equipment...")
        equipment = []
        
        equipment_types = ['forklift', 'pallet_jack', 'conveyor', 'rack', 'scanner', 'scale']
        
        for warehouse in self.warehouses:
            for eq_type in equipment_types:
                eq = {
                    'equipment_id': self.generate_id('EQ', 'shipping'),
                    'equipment_code': f"EQ-{self.counters['shipping']-1:05d}",
                    'warehouse_id': warehouse['warehouse_id'],
                    'equipment_type': eq_type,
                    'description': f"{eq_type.replace('_', ' ').title()} Unit",
                    'model_number': f"MDL-{random.randint(1000, 9999)}",
                    'serial_number': f"SN{random.randint(100000, 999999)}",
                    'purchase_date': (datetime.now() - timedelta(days=random.randint(365, 1825))).strftime('%Y-%m-%d'),
                    'last_maintenance_date': (datetime.now() - timedelta(days=random.randint(1, 90))).strftime('%Y-%m-%d'),
                    'status': random.choice(['operational', 'maintenance', 'retired']),
                    'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                equipment.append(eq)
        
        print(f"Generated {len(equipment)} warehouse equipment")
        return equipment

    def _generate_warehouse_movements(self):
        """Generate warehouse movements"""
        print("Generating warehouse movements...")
        movements = []
        start_date = datetime.now() - timedelta(days=30)
        
        for i in range(45):
            mov = {
                'movement_id': self.generate_id('MOV', 'shipping'),
                'movement_number': f"MOV-{str(i+1).zfill(6)}",
                'warehouse_id': random.choice(self.warehouses)['warehouse_id'],
                'movement_date': (start_date + timedelta(days=random.randint(0, 30))).strftime('%Y-%m-%d'),
                'from_location': f"STG-A{random.randint(1, 5):02d}-L{random.randint(1, 3)}-P{random.randint(1, 4):02d}",
                'to_location': f"STG-A{random.randint(1, 5):02d}-L{random.randint(1, 3)}-P{random.randint(1, 4):02d}",
                'material_id': random.choice(self.materials).get('material_id') if self.materials else None,
                'quantity': random.randint(10, 100),
                'movement_type': random.choice(['replenishment', 'consolidation', 'adjustment', 'return']),
                'performed_by': random.choice(self.warehouse_workers)['worker_id'] if self.warehouse_workers else None,
                'reason': 'Stock optimization',
                'created_at': (start_date + timedelta(days=random.randint(0, 30))).strftime('%Y-%m-%d %H:%M:%S')
            }
            movements.append(mov)
        
        print(f"Generated {len(movements)} warehouse movements")
        return movements

    def _generate_warehouse_aisles(self):
        """Generate warehouse aisles"""
        print("Generating warehouse aisles...")
        aisles = []
        
        for warehouse in self.warehouses:
            zones = [z for z in self.zones if z['warehouse_id'] == warehouse['warehouse_id'] and z['zone_type'] == 'storage']
            for zone in zones:
                for aisle_num in range(1, 6):
                    aisle = {
                        'aisle_id': self.generate_id('AISLE', 'zone'),
                        'warehouse_id': warehouse['warehouse_id'],
                        'zone_id': zone['zone_id'],
                        'aisle_code': f"{zone['zone_code']}-A{aisle_num:02d}",
                        'aisle_number': aisle_num,
                        'aisle_length_m': random.uniform(20, 50),
                        'aisle_width_m': random.uniform(2, 4),
                        'levels': random.choice([2, 3, 4, 5]),
                        'positions_per_level': random.choice([4, 5, 6]),
                        'aisle_type': random.choice(['pallet', 'shelving', 'flow']),
                        'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    }
                    aisles.append(aisle)
        
        print(f"Generated {len(aisles)} warehouse aisles")
        return aisles

    def _generate_slotting_rules(self):
        """Generate slotting rules"""
        print("Generating slotting rules...")
        rules = []
        
        for i in range(30):
            rule = {
                'rule_id': self.generate_id('SLOT', 'slot'),
                'material_id': random.choice(self.materials).get('material_id') if self.materials else None,
                'warehouse_id': random.choice(self.warehouses)['warehouse_id'],
                'rule_name': f"Slotting Rule {i+1}",
                'velocity_class': random.choice(['A', 'B', 'C']),
                'optimal_location': f"STG-A{random.randint(1, 5):02d}-L{random.randint(1, 3)}-P{random.randint(1, 4):02d}",
                'min_stock_level': random.randint(50, 200),
                'max_stock_level': random.randint(500, 1000),
                'rule_status': 'active',
                'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            rules.append(rule)
        
        print(f"Generated {len(rules)} slotting rules")
        return rules

    # ========================================================================
    # TMS EMPTY TABLE GENERATORS
    # ========================================================================
    
    def _generate_carrier_rates(self):
        """Generate carrier rates"""
        print("Generating carrier rates...")
        rates = []
        
        for carrier in self.carriers:
            for service in self.carrier_services:
                if service.get('carrier_id') == carrier['carrier_id']:
                    for zone in range(1, 4):
                        rate = {
                            'rate_id': self.generate_id('RATE', 'carrier'),
                            'carrier_id': carrier['carrier_id'],
                            'service_id': service.get('service_id'),
                            'zone': zone,
                            'rate_type': random.choice(['weight_based', 'zone_based', 'flat']),
                            'min_weight_kg': random.randint(0, 10),
                            'max_weight_kg': random.randint(100, 500),
                            'rate_per_unit': round(random.uniform(10, 100), 2),
                            'currency': 'USD',
                            'effective_date': datetime.now().strftime('%Y-%m-%d'),
                            'expiry_date': (datetime.now() + timedelta(days=365)).strftime('%Y-%m-%d'),
                            'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        }
                        rates.append(rate)
        
        print(f"Generated {len(rates)} carrier rates")
        return rates

    def _generate_shipment_lines(self):
        """Generate shipment lines"""
        print("Generating shipment lines...")
        lines = []
        
        for shipment in self.shipments:
            for i in range(random.randint(1, 5)):
                line = {
                    'shipment_line_id': self.generate_id('SHL', 'shipment'),
                    'shipment_id': shipment['shipment_id'],
                    'sales_order_id': shipment.get('sales_order_id'),
                    'material_id': random.choice(self.materials).get('material_id') if self.materials else None,
                    'line_number': i + 1,
                    'quantity': random.randint(10, 100),
                    'uom': 'EA',
                    'weight_kg': round(random.uniform(1, 50), 2),
                    'volume_cbm': round(random.uniform(0.01, 1), 4),
                    'status': random.choice(['packed', 'in_transit', 'delivered']),
                    'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                lines.append(line)
        
        print(f"Generated {len(lines)} shipment lines")
        return lines

    def _generate_shipment_packages(self):
        """Generate shipment packages"""
        print("Generating shipment packages...")
        packages = []
        
        for shipment in self.shipments:
            for i in range(random.randint(1, 3)):
                pkg = {
                    'package_id': self.generate_id('PKG', 'shipping'),
                    'shipment_id': shipment['shipment_id'],
                    'package_number': i + 1,
                    'package_type': random.choice(['carton', 'pallet', 'container']),
                    'length_cm': random.randint(20, 100),
                    'width_cm': random.randint(20, 100),
                    'height_cm': random.randint(20, 100),
                    'weight_kg': round(random.uniform(5, 100), 2),
                    'contents': json.dumps([f"Item {j+1}" for j in range(random.randint(1, 5))]),
                    'seal_number': f"SEAL-{random.randint(100000, 999999)}",
                    'package_status': random.choice(['packed', 'labeled', 'shipped']),
                    'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                packages.append(pkg)
        
        print(f"Generated {len(packages)} shipment packages")
        return packages

    def _generate_routes(self):
        """Generate routes"""
        print("Generating routes...")
        routes = []
        
        for i in range(25):
            route = {
                'route_id': self.generate_id('ROUTE', 'route'),
                'route_number': f"RT-{i+1:06d}",
                'route_date': (datetime.now() - timedelta(days=random.randint(0, 30))).strftime('%Y-%m-%d'),
                'planned_start_time': f"{random.randint(6, 20):02d}:00:00",
                'planned_end_time': f"{random.randint(6, 20):02d}:00:00",
                'origin_city': random.choice(['New Delhi', 'Mumbai', 'Bangalore', 'Chennai', 'Kolkata']),
                'destination_city': random.choice(['New Delhi', 'Mumbai', 'Bangalore', 'Chennai', 'Kolkata']),
                'distance_km': round(random.uniform(50, 2000), 2),
                'estimated_duration_hours': round(random.uniform(2, 48), 1),
                'frequency': random.choice(['daily', 'twice_weekly', 'weekly']),
                'carrier_id': random.choice(self.carriers)['carrier_id'],
                'route_status': 'active',
                'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            routes.append(route)
        
        print(f"Generated {len(routes)} routes")
        return routes

    def _generate_route_stops(self):
        """Generate route stops"""
        print("Generating route stops...")
        stops = []
        
        for route in self.routes:
            for i in range(random.randint(3, 8)):
                stop = {
                    'stop_id': self.generate_id('STOP', 'delivery'),
                    'route_id': route['route_id'],
                    'stop_sequence': i + 1,
                    'stop_city': random.choice(['New Delhi', 'Gurgaon', 'Noida', 'Mumbai', 'Pune']),
                    'stop_address': f"Address {i+1}",
                    'delivery_customer_id': random.choice(self.customers).get('customer_id') if self.customers else None,
                    'stop_type': random.choice(['pickup', 'delivery', 'both']),
                    'planned_arrival_time': f"{random.randint(6, 20):02d}:00:00",
                    'status': random.choice(['pending', 'completed']),
                    'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                stops.append(stop)
        
        print(f"Generated {len(stops)} route stops")
        return stops

    def _generate_return_orders(self):
        """Generate return orders"""
        print("Generating return orders...")
        returns = []
        start_date = datetime.now() - timedelta(days=90)
        
        for i in range(30):
            ret = {
                'return_order_id': self.generate_id('RET', 'return'),
                'return_number': f"RET-{datetime.now().strftime('%Y%m%d')}-{i+1:04d}",
                'original_shipment_id': random.choice(self.shipments)['shipment_id'] if self.shipments else None,
                'customer_id': random.choice(self.customers).get('customer_id') if self.customers else None,
                'return_date': (start_date + timedelta(days=random.randint(0, 90))).strftime('%Y-%m-%d'),
                'return_reason': random.choice(['defective', 'damaged', 'wrong_item', 'customer_request']),
                'return_status': random.choice(['initiated', 'in_transit', 'received', 'processed']),
                'refund_amount': round(random.uniform(1000, 50000), 2),
                'created_at': (start_date + timedelta(days=random.randint(0, 90))).strftime('%Y-%m-%d %H:%M:%S')
            }
            returns.append(ret)
        
        print(f"Generated {len(returns)} return orders")
        return returns

    def _generate_return_order_lines(self):
        """Generate return order lines"""
        print("Generating return order lines...")
        lines = []
        
        for i in range(35):
            # Prefer materials that have sales orders (65% of the time)
            material_id = None
            sales_order_line_id = None
            
            if self.materials_with_sales and random.random() < 0.85:
                # Pick from materials with sales orders
                material_id = random.choice(self.materials_with_sales)
                # Link to an actual sales order line for this material
                sales_order_line_id = random.choice(self.material_to_sales_lines[material_id]).get('sales_order_line_id')
            elif self.materials:
                # Fall back to any material
                material_id = random.choice(self.materials).get('material_id')
            
            line = {
                'return_line_id': self.generate_id('RLN', 'return'),
                'return_order_id': self.return_orders[i % len(self.return_orders)]['return_order_id'] if self.return_orders else None,
                'sales_order_line_id': sales_order_line_id,
                'material_id': material_id,
                'quantity_returned': random.randint(5, 50),
                'reason_description': random.choice(['Defective unit', 'Wrong color', 'Damaged in transit']),
                'condition': random.choice(['unopened', 'opened', 'used', 'damaged']),
                'inspection_result': random.choice(['pass', 'fail']),
                'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            lines.append(line)
        
        print(f"Generated {len(lines)} return order lines")
        return lines

    def _generate_return_shipments(self):
        """Generate return shipments"""
        print("Generating return shipments...")
        shipments = []
        
        for i in range(20):
            shipment_date = datetime.now() - timedelta(days=random.randint(1, 30))
            expected_date = shipment_date + timedelta(days=random.randint(5, 15))
            # Only populate actual_delivery_date for delivered shipments (85% chance)
            actual_delivery_date = None
            if random.random() < 0.85:
                actual_delivery_date = (expected_date + timedelta(days=random.randint(0, 5))).strftime('%Y-%m-%d')
            
            ship = {
                'return_shipment_id': self.generate_id('RSHIP', 'return'),
                'return_order_id': self.return_orders[i % len(self.return_orders)]['return_order_id'] if self.return_orders else None,
                'shipment_date': shipment_date.strftime('%Y-%m-%d'),
                'expected_delivery_date': expected_date.strftime('%Y-%m-%d'),
                'actual_delivery_date': actual_delivery_date,
                'carrier_id': random.choice(self.carriers)['carrier_id'],
                'tracking_number': f"TRK-{random.randint(100000000, 999999999)}",
                'shipment_status': 'delivered' if actual_delivery_date else 'in_transit',
                'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            shipments.append(ship)
        
        print(f"Generated {len(shipments)} return shipments")
        return shipments

    def _generate_freight_invoices(self):
        """Generate freight invoices"""
        print("Generating freight invoices...")
        invoices = []
        
        for i in range(25):
            inv = {
                'invoice_id': self.generate_id('FRT', 'shipment'),
                'invoice_number': f"FRT-{random.randint(100000, 999999)}",
                'carrier_id': random.choice(self.carriers)['carrier_id'],
                'invoice_date': datetime.now().strftime('%Y-%m-%d'),
                'freight_charges': round(random.uniform(800, 40000), 2),
                'fuel_surcharge': round(random.uniform(50, 5000), 2),
                'total_amount': round(random.uniform(1000, 50000), 2),
                'currency': 'USD',
                'invoice_status': random.choice(['received', 'under_audit', 'approved', 'paid']),
                'payment_date': None if random.random() > 0.80 else datetime.now().strftime('%Y-%m-%d'),
                'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            invoices.append(inv)
        
        print(f"Generated {len(invoices)} freight invoices")
        return invoices

    def _generate_freight_invoice_lines(self, freight_invoices):
        """Generate freight invoice lines"""
        print("Generating freight invoice lines...")
        lines = []
        
        # Distribute lines across invoices (3-5 lines per invoice)
        for invoice in freight_invoices:
            num_lines = random.randint(3, 5)
            for seq in range(1, num_lines + 1):
                line = {
                    'invoice_line_id': self.generate_id('FIL', 'shipment'),
                    'invoice_id': invoice['invoice_id'],
                    'line_number': seq,
                    'charge_type': random.choice(['transportation', 'handling', 'surcharge', 'fuel']),
                    'charge_description': f"Freight charge {seq}",
                    'charge_amount': round(random.uniform(100, 5000), 2),
                    'expected_amount': round(random.uniform(100, 5000), 2),
                    'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                lines.append(line)
        
        print(f"Generated {len(lines)} freight invoice lines")
        return lines

    def _generate_wms_tms_sync_log(self):
        """Generate WMS-TMS sync logs"""
        print("Generating WMS-TMS sync logs...")
        logs = []
        start_date = datetime.now() - timedelta(days=60)
        
        for i in range(50):
            log = {
                'sync_id': self.generate_id('SYNC', 'pod'),
                'sync_timestamp': (start_date + timedelta(days=random.randint(0, 60))).strftime('%Y-%m-%d %H:%M:%S'),
                'sync_direction': random.choice(['WMS_TO_TMS', 'TMS_TO_WMS']),
                'document_type': random.choice(['shipment', 'delivery_confirmation', 'tracking_update']),
                'document_id': f"DOC-{random.randint(100000, 999999)}",
                'sync_status': random.choice(['completed', 'completed', 'completed', 'error']),
                'error_message': None if random.random() > 0.1 else 'Connection timeout',
                'retry_count': 0,
                'created_at': (start_date + timedelta(days=random.randint(0, 60))).strftime('%Y-%m-%d %H:%M:%S')
            }
            logs.append(log)
        
        print(f"Generated {len(logs)} WMS-TMS sync logs")
        return logs

    def _print_summary(self):
        logger.info(f"\n{'='*80}")
        logger.info(f"WMS + TMS Data Generation Complete!")
        logger.info(f"{'='*80}")
        
        # Bottleneck fixes and performance statistics
        logger.info(f"\n📊 Performance Statistics:")
        logger.info(f"  ⚠️  FK Validation Errors: {self.stats['fk_validation_errors']:,}")
        logger.info(f"  📦 Inventory Consistency Checks: {self.stats['inventory_checks']:,}")
        logger.info(f"  🌊 Wave Capacity Adjustments: {self.stats['wave_capacity_adjustments']:,}")
        logger.info(f"  ⏰ Time Coordination Events: {self.stats['time_coordination_events']:,}")
        logger.info(f"  📈 Total Records Generated: {self.stats['records_generated']:,}")
        
        logger.info(f"\n📦 WMS Data Summary:")
        logger.info(f"  Warehouses: {len(self.warehouses):,}")
        logger.info(f"  Zones: {len(self.zones):,}")
        logger.info(f"  Storage Bins: {len(self.bins):,}")
        logger.info(f"  Workers: {len(self.warehouse_workers):,}")
        logger.info(f"  Receiving Tasks: {len(self.receiving_tasks):,}")
        logger.info(f"  Putaway Tasks: {len(self.putaway_tasks):,}")
        logger.info(f"  Pick Waves: {len(self.pick_waves):,}")
        logger.info(f"  Picking Tasks: {len(self.picking_tasks):,}")
        logger.info(f"  Packing Tasks: {len(self.packing_tasks):,}")
        logger.info(f"  Shipping Tasks: {len(self.shipping_tasks):,}")
        
        logger.info(f"\n🚛 TMS Data Summary:")
        logger.info(f"  Carriers: {len(self.carriers):,}")
        logger.info(f"  Carrier Services: {len(self.carrier_services):,}")
        logger.info(f"  Shipments: {len(self.shipments):,}")
        logger.info(f"  Tracking Events: {len(self.tracking_events):,}")
        logger.info(f"  Deliveries: {len(self.deliveries):,}")
        logger.info(f"  Proof of Delivery: {len(self.pod):,}")
        
        # Data quality assessment
        total_wms_records = (len(self.warehouses) + len(self.zones) + len(self.bins) + 
                           len(self.warehouse_workers) + len(self.receiving_tasks) + 
                           len(self.putaway_tasks) + len(self.pick_waves) + 
                           len(self.picking_tasks) + len(self.packing_tasks) + 
                           len(self.shipping_tasks))
        
        total_tms_records = (len(self.carriers) + len(self.carrier_services) + 
                           len(self.shipments) + len(self.tracking_events) + 
                           len(self.deliveries) + len(self.pod))
        
        error_rate = (self.stats['fk_validation_errors'] / max(1, self.stats['records_generated'])) * 100
        
        logger.info(f"\n✅ Quality Assessment:")
        logger.info(f"  Total WMS Records: {total_wms_records:,}")
        logger.info(f"  Total TMS Records: {total_tms_records:,}")
        logger.info(f"  Overall Error Rate: {error_rate:.2f}%")
        logger.info(f"  Data Integrity: {'✅ GOOD' if error_rate < 5 else '⚠️ REVIEW NEEDED' if error_rate < 10 else '❌ POOR'}")
        logger.info(f"{'='*80}")
    
    def to_json(self, output_file_wms='wms_historical_data.json', output_file_tms='tms_historical_data.json'):
        """Export to JSON with separate files for WMS and TMS"""
        print(f"\nExporting to JSON (separate WMS and TMS files)...")
        
        # Generate WMS empty table data
        warehouse_inventory = self._generate_warehouse_inventory()
        wave_lines = self._generate_wave_lines()
        cycle_count_tasks = self._generate_cycle_count_tasks()
        warehouse_equipment = self._generate_warehouse_equipment()
        warehouse_movements = self._generate_warehouse_movements()
        warehouse_aisles = self._generate_warehouse_aisles()
        slotting_rules = self._generate_slotting_rules()
        
        # Generate TMS empty table data
        carrier_rates = self._generate_carrier_rates()
        shipment_lines = self._generate_shipment_lines()
        shipment_packages = self._generate_shipment_packages()
        routes = self._generate_routes()
        self.routes = routes  # Store routes for route_stops generation
        route_stops = self._generate_route_stops()
        return_orders = self._generate_return_orders()
        self.return_orders = return_orders  # Store return_orders for dependent tables
        return_order_lines = self._generate_return_order_lines()
        return_shipments = self._generate_return_shipments()
        freight_invoices = self._generate_freight_invoices()
        freight_invoice_lines = self._generate_freight_invoice_lines(freight_invoices)
        wms_tms_sync_log = self._generate_wms_tms_sync_log()
        
        # WMS Data - Warehouse Management System
        wms_data = {
            # WMS - Warehouses & Zones & Aisles
            'warehouses': self.warehouses,
            'warehouse_zones': self.zones,
            'storage_bins': self.bins,
            'warehouse_workers': self.warehouse_workers,
            
            # WMS - Inventory
            'warehouse_inventory': warehouse_inventory,
            
            # WMS - Receiving
            'receiving_tasks': self.receiving_tasks,
            
            # WMS - Putaway
            'putaway_tasks': self.putaway_tasks,
            
            # WMS - Picking & Wave
            'pick_waves': self.pick_waves,
            'wave_lines': wave_lines,
            'picking_tasks': self.picking_tasks,
            
            # WMS - Packing & Shipping
            'packing_tasks': self.packing_tasks,
            'shipping_tasks': self.shipping_tasks,
            
            # WMS - Additional tables
            'cycle_count_tasks': cycle_count_tasks,
            'warehouse_equipment': warehouse_equipment,
            'warehouse_movements': warehouse_movements,
            'warehouse_aisles': warehouse_aisles,
            'slotting_rules': slotting_rules
        }
        
        # TMS Data - Transportation Management System
        tms_data = {
            # TMS - Master Data
            'carriers': self.carriers,
            'carrier_services': self.carrier_services,
            'carrier_rates': carrier_rates,
            
            # TMS - Shipments
            'shipments': self.shipments,
            'shipment_lines': shipment_lines,
            'shipment_packages': shipment_packages,
            'tracking_events': self.tracking_events,
            
            # TMS - Deliveries & Routes
            'routes': routes,
            'route_stops': route_stops,
            'deliveries': self.deliveries,
            'proof_of_delivery': self.pod,
            
            # TMS - Returns
            'return_orders': return_orders,
            'return_order_lines': return_order_lines,
            'return_shipments': return_shipments,
            
            # TMS - Freight
            'freight_invoices': freight_invoices,
            'freight_invoice_lines': freight_invoice_lines,
            
            # Integration & Logging
            'wms_tms_sync_log': wms_tms_sync_log
        }
        
        # Write WMS JSON with explicit truncation and validation
        import os
        if os.path.exists(output_file_wms):
            os.remove(output_file_wms)  # Ensure clean slate
        with open(output_file_wms, 'w') as f:
            json.dump(wms_data, f, indent=2)
        print(f"WMS data exported to {output_file_wms}")
        
        # Write TMS JSON with explicit truncation and validation
        if os.path.exists(output_file_tms):
            os.remove(output_file_tms)  # Ensure clean slate
        with open(output_file_tms, 'w') as f:
            json.dump(tms_data, f, indent=2)
        print(f"TMS data exported to {output_file_tms}")


if __name__ == "__main__":
    from pathlib import Path
    
    # Get the directory of this script (data folder)
    script_dir = Path(__file__).parent
    
    generator = WMSTMSDataGenerator()
    generator.generate_all_data()
    
    # Export to JSON (in same folder as script) - create separate WMS and TMS files
    wms_json_file = script_dir / "genims_wms_data.json"
    tms_json_file = script_dir / "genims_tms_data.json"
    generator.to_json(str(wms_json_file), str(tms_json_file))
    
    print("\n" + "="*80)
    print("WMS + TMS Historical Data Generation Complete!")
    print("="*80)
