#!/usr/bin/env python3
"""
GenIMS WMS + TMS Historical Data Generator
Generates 30 days of warehouse operations + 60 days of logistics data
"""

import random
import json
from datetime import datetime, timedelta
from typing import List, Dict
import sys
from pathlib import Path

# Add scripts to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))
from generator_helper import get_helper

# Configuration
WMS_DAYS_OF_HISTORY = 30
TMS_DAYS_OF_HISTORY = 60
WAREHOUSES_TO_CREATE = 3
CARRIERS_TO_CREATE = 10

class WMSTMSDataGenerator:
    def __init__(self, master_data_file=None, erp_data_file=None):
        """Initialize with master data, ERP data, and registry"""
        from pathlib import Path
        
        if master_data_file is None:
            master_data_file = Path(__file__).parent.parent / "01 - Base Data" / "genims_master_data.json"
        
        if erp_data_file is None:
            erp_data_file = Path(__file__).parent.parent / "04 - ERP & MES Integration" / "genims_erp_data.json"
        
        print(f"Loading master data from {master_data_file}...")
        print(f"Loading ERP data from {erp_data_file}...")
        
        with open(master_data_file, 'r') as f:
            self.master_data = json.load(f)
        
        with open(erp_data_file, 'r') as f:
            self.erp_data = json.load(f)
        
        # Load helper for FK validation
        self.helper = get_helper()
        self.registry = self.helper.registry
        
        self.factories = self.master_data['factories']
        self.customers = self.master_data['customers']
        self.materials = self.erp_data['materials']
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
        
        # WMS Data
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
        
        # TMS Data
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
        
        # Counters
        self.counters = {
            'warehouse': 1, 'zone': 1, 'bin': 1, 'wh_inv': 1,
            'receiving': 1, 'putaway': 1, 'wave': 1, 'picking': 1,
            'packing': 1, 'shipping': 1, 'worker': 1,
            'carrier': 1, 'service': 1, 'shipment': 1, 'tracking': 1,
            'route': 1, 'delivery': 1, 'pod': 1, 'return': 1, 'aisle': 1, 'slot': 1
        }
        
        print(f"Loaded: {len(self.materials)} materials, {len(self.sales_orders)} sales orders, {len(self.sales_order_lines)} sales order lines")
    
    def generate_id(self, prefix: str, counter_key: str) -> str:
        id_val = f"{prefix}-{str(self.counters[counter_key]).zfill(6)}"
        self.counters[counter_key] += 1
        return id_val
    
    def generate_all_data(self):
        """Generate all WMS and TMS data"""
        print(f"\n{'='*80}")
        print(f"Generating WMS ({WMS_DAYS_OF_HISTORY} days) + TMS ({TMS_DAYS_OF_HISTORY} days) Data")
        print(f"{'='*80}\n")
        
        # WMS Master Data
        self.generate_warehouses()
        self.generate_warehouse_zones()
        self.generate_storage_bins()
        self.generate_warehouse_workers()
        
        # WMS Operations (30 days)
        start_date = datetime.now() - timedelta(days=WMS_DAYS_OF_HISTORY)
        self.generate_warehouse_operations(start_date, WMS_DAYS_OF_HISTORY)
        
        # TMS Master Data
        self.generate_carriers()
        
        # TMS Operations (60 days)
        tms_start = datetime.now() - timedelta(days=TMS_DAYS_OF_HISTORY)
        self.generate_logistics_operations(tms_start, TMS_DAYS_OF_HISTORY)
        
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
        """Generate daily warehouse operations"""
        print(f"Generating {days} days of warehouse operations...")
        
        current_date = start_date
        
        for day in range(days):
            # Inbound: Receiving + Putaway (5-10 per day)
            for _ in range(random.randint(5, 10)):
                self._create_receiving_task(current_date)
            
            # Outbound: Waves + Picking + Packing + Shipping (3-8 per day)
            for _ in range(random.randint(3, 8)):
                self._create_pick_wave(current_date)
            
            current_date += timedelta(days=1)
        
        print(f"Generated warehouse operations: {len(self.receiving_tasks)} receiving, "
              f"{len(self.pick_waves)} waves, {len(self.picking_tasks)} picks")
    
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
    
    def _create_pick_wave(self, date: datetime):
        """Create pick wave for sales orders"""
        if not self.sales_orders:
            return
        
        warehouse = random.choice(self.warehouses)
        wave = {
            'wave_id': self.generate_id('WAVE', 'wave'),
            'wave_number': f"WAVE-{date.strftime('%Y%m%d')}-{self.counters['wave']:04d}",
            'warehouse_id': warehouse['warehouse_id'],
            'wave_type': 'batch',
            'planned_pick_date': date.strftime('%Y-%m-%d'),
            'planned_ship_date': (date + timedelta(days=1)).strftime('%Y-%m-%d'),
            'priority': 'normal',
            'wave_status': 'completed',
            'total_orders': random.randint(3, 10),
            'total_lines': random.randint(10, 30),
            'created_at': date.strftime('%Y-%m-%d %H:%M:%S'),
            'released_at': (date + timedelta(hours=1)).strftime('%Y-%m-%d %H:%M:%S'),
            'completed_at': (date + timedelta(hours=6)).strftime('%Y-%m-%d %H:%M:%S')
        }
        self.pick_waves.append(wave)
        
        # Create picking tasks
        for _ in range(wave['total_lines']):
            self._create_picking_task(wave, date)
        
        # Create packing and shipping
        self._create_packing_task(wave, date)
        self._create_shipping_task(wave, date)
    
    def _create_picking_task(self, wave: dict, date: datetime):
        """Create picking task"""
        available_bins = [b for b in self.bins if b['bin_status'] == 'available']
        if not available_bins:
            return
        
        task = {
            'picking_task_id': self.generate_id('PICK', 'picking'),
            'task_number': f"PICK-{date.strftime('%Y%m%d')}-{self.counters['picking']:04d}",
            'wave_id': wave['wave_id'],
            'sales_order_id': random.choice(self.sales_orders)['sales_order_id'],
            'material_id': random.choice(self.materials)['material_id'],
            'quantity_to_pick': random.randint(10, 100),
            'quantity_picked': random.randint(10, 100),
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
            'task_status': 'packed',
            'created_at': date.strftime('%Y-%m-%d %H:%M:%S'),
            'completed_at': (date + timedelta(hours=5)).strftime('%Y-%m-%d %H:%M:%S')
        }
        self.packing_tasks.append(task)
    
    def _create_shipping_task(self, wave: dict, date: datetime):
        """Create shipping task"""
        task = {
            'shipping_task_id': self.generate_id('SHIP', 'shipping'),
            'task_number': f"SHIP-{date.strftime('%Y%m%d')}-{self.counters['shipping']:04d}",
            'sales_order_id': random.choice(self.sales_orders)['sales_order_id'],
            'warehouse_id': wave['warehouse_id'],
            'shipping_dock': f"DOCK-{random.randint(1, 10)}",
            'number_of_packages': random.randint(1, 5),
            'total_weight_kg': round(random.uniform(10, 100), 2),
            'task_status': 'shipped',
            'scheduled_ship_date': wave['planned_ship_date'],
            'actual_ship_date': wave['planned_ship_date'],
            'bol_number': f"BOL-{date.strftime('%Y%m%d')}-{random.randint(1000, 9999)}",
            'created_at': date.strftime('%Y-%m-%d %H:%M:%S'),
            'completed_at': (date + timedelta(hours=6)).strftime('%Y-%m-%d %H:%M:%S')
        }
        self.shipping_tasks.append(task)
    
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
        """Generate logistics operations"""
        print(f"Generating {days} days of logistics operations...")
        
        current_date = start_date
        
        for day in range(days):
            # Create shipments (3-10 per day)
            for _ in range(random.randint(3, 10)):
                self._create_shipment(current_date)
            
            current_date += timedelta(days=1)
        
        print(f"Generated {len(self.shipments)} shipments with {len(self.tracking_events)} tracking events")
    
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
        
        for i, material in enumerate(self.materials[:50]):
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
        
        for wave in self.pick_waves[:30]:
            for i in range(random.randint(5, 15)):
                line = {
                    'wave_line_id': self.generate_id('WL', 'picking'),
                    'wave_id': wave['wave_id'],
                    'sales_order_id': random.choice(self.sales_orders).get('sales_order_id'),
                    'material_id': random.choice(self.materials).get('material_id') if self.materials else None,
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
        
        for shipment in self.shipments[:40]:
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
        
        for shipment in self.shipments[:35]:
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
                'freight_invoice_id': self.generate_id('FRT', 'shipment'),
                'invoice_number': f"FRT-{random.randint(100000, 999999)}",
                'shipment_id': random.choice(self.shipments)['shipment_id'] if self.shipments else None,
                'carrier_id': random.choice(self.carriers)['carrier_id'],
                'invoice_date': datetime.now().strftime('%Y-%m-%d'),
                'amount': round(random.uniform(1000, 50000), 2),
                'currency': 'USD',
                'status': random.choice(['pending', 'approved', 'paid']),
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
                    'freight_invoice_id': invoice['freight_invoice_id'],
                    'line_number': seq,
                    'charge_type': random.choice(['transportation', 'handling', 'surcharge', 'tax']),
                    'description': f"Freight charge {seq}",
                    'quantity': random.randint(1, 10),
                    'unit_price': round(random.uniform(100, 5000), 2),
                    'amount': round(random.uniform(100, 50000), 2),
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
                'sync_log_id': self.generate_id('SYNC', 'pod'),
                'sync_date': (start_date + timedelta(days=random.randint(0, 60))).strftime('%Y-%m-%d'),
                'sync_time': f"{random.randint(0, 23):02d}:{random.randint(0, 59):02d}:00",
                'source_system': random.choice(['WMS', 'TMS']),
                'target_system': random.choice(['TMS', 'WMS']),
                'record_type': random.choice(['shipment', 'inventory', 'delivery', 'return']),
                'record_count': random.randint(1, 100),
                'status': random.choice(['success', 'success', 'success', 'failed']),
                'error_message': None if random.random() > 0.1 else 'Connection timeout',
                'created_at': (start_date + timedelta(days=random.randint(0, 60))).strftime('%Y-%m-%d %H:%M:%S')
            }
            logs.append(log)
        
        print(f"Generated {len(logs)} WMS-TMS sync logs")
        return logs

    def _print_summary(self):
        print(f"\n{'='*80}")
        print(f"WMS + TMS Data Generation Complete!")
        print(f"{'='*80}")
        print(f"\nWMS Data Summary:")
        print(f"  Warehouses: {len(self.warehouses)}")
        print(f"  Zones: {len(self.zones)}")
        print(f"  Storage Bins: {len(self.bins)}")
        print(f"  Workers: {len(self.warehouse_workers)}")
        print(f"  Receiving Tasks: {len(self.receiving_tasks)}")
        print(f"  Putaway Tasks: {len(self.putaway_tasks)}")
        print(f"  Pick Waves: {len(self.pick_waves)}")
        print(f"  Picking Tasks: {len(self.picking_tasks)}")
        print(f"  Packing Tasks: {len(self.packing_tasks)}")
        print(f"  Shipping Tasks: {len(self.shipping_tasks)}")
        
        print(f"\nTMS Data Summary:")
        print(f"  Carriers: {len(self.carriers)}")
        print(f"  Carrier Services: {len(self.carrier_services)}")
        print(f"  Shipments: {len(self.shipments)}")
        print(f"  Tracking Events: {len(self.tracking_events)}")
        print(f"  Deliveries: {len(self.deliveries)}")
        print(f"  Proof of Delivery: {len(self.pod)}")
    
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
            'storage_bins': self.bins[:100],
            'warehouse_workers': self.warehouse_workers,
            
            # WMS - Inventory
            'warehouse_inventory': warehouse_inventory,
            
            # WMS - Receiving
            'receiving_tasks': self.receiving_tasks[:50],
            
            # WMS - Putaway
            'putaway_tasks': self.putaway_tasks[:50],
            
            # WMS - Picking & Wave
            'pick_waves': self.pick_waves,
            'wave_lines': wave_lines,
            'picking_tasks': self.picking_tasks[:50],
            
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
            'tracking_events': self.tracking_events[:100],
            
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
        
        # Write WMS JSON
        with open(output_file_wms, 'w') as f:
            json.dump(wms_data, f, indent=2)
        print(f"WMS data exported to {output_file_wms}")
        
        # Write TMS JSON
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
