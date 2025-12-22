#!/usr/bin/env python3
"""
GenIMS WMS + TMS Historical Data Generator
Generates 30 days of warehouse operations + 60 days of logistics data
"""

import random
import json
from datetime import datetime, timedelta
from typing import List, Dict

# Configuration
WMS_DAYS_OF_HISTORY = 30
TMS_DAYS_OF_HISTORY = 60
WAREHOUSES_TO_CREATE = 3
CARRIERS_TO_CREATE = 10

class WMSTMSDataGenerator:
    def __init__(self, master_data_file='genims_master_data.json',
                 erp_data_file='erp_historical_data.json'):
        """Initialize with master data and ERP data"""
        print("Loading existing data...")
        
        with open(master_data_file, 'r') as f:
            self.master_data = json.load(f)
        
        with open(erp_data_file, 'r') as f:
            self.erp_data = json.load(f)
        
        self.factories = self.master_data['factories']
        self.customers = self.master_data['customers']
        self.materials = self.erp_data['materials']
        self.sales_orders = self.erp_data['sales_orders']
        self.purchase_orders = self.erp_data['purchase_orders']
        
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
            'route': 1, 'delivery': 1, 'pod': 1, 'return': 1
        }
        
        print(f"Loaded: {len(self.materials)} materials, {len(self.sales_orders)} sales orders")
    
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
                'state': factory['state'],
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
            'sales_order_id': random.choice(self.sales_orders)['sales_order_id'] if self.sales_orders else None,
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
            'sales_order_id': random.choice(self.sales_orders)['sales_order_id'] if self.sales_orders else None,
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
            'sales_order_id': random.choice(self.sales_orders)['sales_order_id'] if self.sales_orders else None,
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
        
        shipment = {
            'shipment_id': self.generate_id('SHPM', 'shipment'),
            'shipment_number': f"SHPM-{date.strftime('%Y%m%d')}-{self.counters['shipment']:05d}",
            'sales_order_id': so['sales_order_id'],
            'warehouse_id': random.choice(self.warehouses)['warehouse_id'] if self.warehouses else None,
            'carrier_id': carrier['carrier_id'],
            'service_id': service['service_id'] if service else None,
            'tracking_number': f"TRK{date.strftime('%Y%m%d')}{random.randint(100000, 999999)}",
            'customer_id': so['customer_id'],
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
    
    def to_json(self, output_file='wms_tms_historical_data.json'):
        """Export to JSON"""
        print(f"\nExporting to JSON...")
        
        data = {
            'metadata': {
                'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'wms_days': WMS_DAYS_OF_HISTORY,
                'tms_days': TMS_DAYS_OF_HISTORY
            },
            'wms': {
                'warehouses': self.warehouses,
                'zones': self.zones,
                'bins': self.bins[:100],  # Sample
                'workers': self.warehouse_workers,
                'receiving_tasks': self.receiving_tasks[:50],
                'putaway_tasks': self.putaway_tasks[:50],
                'pick_waves': self.pick_waves,
                'picking_tasks': self.picking_tasks[:50],
                'packing_tasks': self.packing_tasks,
                'shipping_tasks': self.shipping_tasks
            },
            'tms': {
                'carriers': self.carriers,
                'carrier_services': self.carrier_services,
                'shipments': self.shipments,
                'tracking_events': self.tracking_events[:100],
                'deliveries': self.deliveries,
                'pod': self.pod
            }
        }
        
        with open(output_file, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"Data exported to {output_file}")


if __name__ == "__main__":
    generator = WMSTMSDataGenerator()
    generator.generate_all_data()
    generator.to_json()
    
    print("\n" + "="*80)
    print("WMS + TMS Historical Data Generation Complete!")
    print("="*80)
