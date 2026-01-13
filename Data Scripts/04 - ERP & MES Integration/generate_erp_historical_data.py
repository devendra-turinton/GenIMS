#!/usr/bin/env python3
"""
GenIMS ERP Historical Data Generator
Generates 90 days of ERP data with referential integrity using registry
Ultra-Fast Parallel Processing Implementation
"""

import random
import json
from datetime import datetime, timedelta
from typing import List, Dict
import sys
from pathlib import Path
import threading
import multiprocessing
from concurrent.futures import ThreadPoolExecutor, as_completed

# Add scripts to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))
from generator_helper import get_helper  # type: ignore

# Configuration
DAYS_OF_HISTORY = 180
MATERIALS_TO_CREATE = 800  # Expanded material catalog for enterprise manufacturing
SUPPLIERS_TO_CREATE = 120  # More suppliers for complex supply chain
SALES_ORDERS_PER_DAY = (150, 300)  # Enterprise sales volume (37-75 orders per factory)
PURCHASE_ORDERS_PER_DAY = (40, 100)  # Adjusted for 1.5-7.5 sales:purchase ratio (realistic range)

class ERPDataGenerator:
    def __init__(self, master_data_file=None):
        """Initialize with master data and registry"""
        from pathlib import Path
        
        if master_data_file is None:
            master_data_file = Path(__file__).parent.parent / "01 - Base Data" / "genims_master_data.json"
        
        print(f"Loading master data from {master_data_file}...")
        with open(master_data_file, 'r') as f:
            self.master_data = json.load(f)
        
        # Load MES data for work order linking
        mes_data_file = Path(__file__).parent.parent / "03 - MES Data" / "genims_mes_data.json"
        self.mes_data = {}
        if mes_data_file.exists():
            print(f"Loading MES data from {mes_data_file}...")
            with open(mes_data_file, 'r') as f:
                self.mes_data = json.load(f)
        
        # Load helper for FK validation
        self.helper = get_helper()
        self.registry = self.helper.registry
        
        self.products = self.master_data['products']
        self.customers = self.master_data['customers']
        self.factories = self.master_data['factories']
        self.work_orders = self.mes_data.get('work_orders', [])
        
        # ERP data
        self.materials = []
        self.suppliers = []
        self.boms = []
        self.bom_components = []
        self.production_orders = []
        self.sales_orders = []
        self.sales_order_lines = []
        self.purchase_orders = []
        self.purchase_order_lines = []
        self.inventory_balances = []
        self.inventory_transactions = []
        
        # Counters
        self.counters = {
            'material': 1,
            'supplier': 1,
            'bom': 1,
            'prod_order': 1,
            'sales_order': 1,
            'po': 1,
            'inv_trans': 1
        }
        
        # 🚀 ULTRA-FAST PARALLEL PROCESSING CONFIGURATION
        self.parallel_enabled = True  # Always enable for maximum performance
        self.worker_count = min(8, max(2, multiprocessing.cpu_count() - 1))  # Use 2-8 workers optimally
        self.batch_size = 150000  # Large batch size for efficiency
        
        # Thread safety for parallel processing
        self.data_lock = threading.Lock()
        
        print(f"🚀 ULTRA-FAST ERP PARALLEL MODE: {self.worker_count} workers, batch_size={self.batch_size}")
        print(f"   CPU cores available: {multiprocessing.cpu_count()}, Using {self.worker_count} for generation")
        
        print(f"Loaded: {len(self.products)} products, {len(self.customers)} customers")
        print(f"Loaded: {len(self.work_orders)} work orders from MES")
        print(f"Registry contains: {len(self.registry.get_registered_ids('product'))} valid product IDs")
    
    def generate_id(self, prefix: str, counter_key: str) -> str:
        id_val = f"{prefix}-{str(self.counters[counter_key]).zfill(6)}"
        self.counters[counter_key] += 1
        return id_val
    
    def generate_all_data(self):
        """Generate all ERP data"""
        print(f"\n{'='*80}")
        print(f"Generating {DAYS_OF_HISTORY} days of ERP historical data")
        print(f"{'='*80}\n")
        
        # Master data first - suppliers before materials
        self.generate_suppliers()
        self.generate_materials()
        self.generate_boms()
        
        # Register suppliers, materials, and BOMs with registry
        self.registry.register_master_ids('supplier', self.suppliers)
        self.registry.register_master_ids('material', self.materials)
        self.registry.register_master_ids('bom', self.boms)
        
        # Transactional data
        start_date = datetime.now() - timedelta(days=DAYS_OF_HISTORY)
        self.generate_sales_orders(start_date, DAYS_OF_HISTORY)
        self.generate_production_orders()
        self.generate_purchase_orders(start_date, DAYS_OF_HISTORY)
        self.generate_inventory()
        
        print(f"\n{'='*80}")
        print("ERP Data Generation Complete!")
        print(f"{'='*80}")
        self._print_summary()
    
    def generate_materials(self):
        """Generate material master data"""
        print("Generating materials...")
        
        # Material types distribution
        material_types = {
            'raw_material': 50,
            'component': 80,
            'finished_good': len(self.products),
            'consumable': 20,
            'packaging': 15
        }
        
        # Raw materials
        raw_materials = [
            'Steel Sheet', 'Steel Rod', 'Aluminum Bar', 'Copper Wire',
            'Rubber Compound', 'Plastic Pellet', 'Paint Base', 'Lubricant Oil',
            'Adhesive', 'Sealant', 'Grease', 'Thread Compound'
        ]
        
        for _ in range(material_types['raw_material']):
            base_name = random.choice(raw_materials)
            standard_cost = round(random.uniform(10, 200), 2)
            material = {
                'material_id': self.generate_id('MAT', 'material'),
                'material_code': f"RM-{self.counters['material']:05d}",
                'material_name': f"{base_name} Grade {random.choice(['A', 'B', 'C'])}",
                'material_type': 'raw_material',
                'material_group': 'RAW',
                'base_unit_of_measure': random.choice(['KG', 'L', 'M']),
                'procurement_type': 'buy',
                'default_supplier_id': None,  # Will be assigned after suppliers are generated
                'lead_time_days': random.randint(7, 30),
                'reorder_point': random.randint(100, 500),
                'safety_stock': random.randint(50, 200),
                'standard_cost': standard_cost,
                'material_status': 'active',
                # Missing columns
                'abc_classification': random.choice(['A', 'B', 'C']),  # Inventory importance
                'blocked_for_procurement': False,
                'blocked_for_production': False,
                'commodity_code': f"COMM-{random.randint(10000, 99999)}",
                'created_by': 'SYSTEM',
                'dimensions': f"{random.randint(1, 100)}x{random.randint(1, 100)}x{random.randint(1, 100)}mm",
                'inspection_required': random.random() < 0.3,
                'last_purchase_price': standard_cost * random.uniform(0.9, 1.1),
                'lot_sizing_procedure': random.choice(['fixed_lot', 'period_lot', 'period_batch']),
                'maximum_stock': random.randint(2000, 10000),
                'minimum_order_quantity': random.randint(50, 500),
                'moving_average_cost': standard_cost * random.uniform(0.95, 1.05),
                'mrp_type': random.choice(['planned', 'forecast', 'make-to-stock']),
                'order_multiple': random.choice([1, 5, 10, 25, 50, 100]),
                'planning_time_fence_days': random.randint(14, 90),
                'product_family': random.choice(['RAW_METALS', 'RAW_PLASTICS', 'RAW_CHEMICALS', 'RAW_OILS']),
                'product_id': None,  # Only for finished goods
                'shelf_life_days': random.randint(90, 1095),  # 3 years
                'updated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'valuation_class': random.choice(['STANDARD', 'MOVING_AVG', 'FIFO', 'LIFO']),
                'volume_m3': round(random.uniform(0.001, 10), 6),
                'weight_kg': round(random.uniform(0.1, 1000), 4),
                'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            self.materials.append(material)
        
        # Components
        components = [
            'Bolt M8', 'Nut M8', 'Washer 8mm', 'Spring 20N',
            'Bearing 6205', 'Seal Rubber', 'Gasket Fiber', 'O-Ring 10mm',
            'Clip Metal', 'Pin Steel', 'Bushing Bronze', 'Bracket Steel'
        ]
        
        for _ in range(material_types['component']):
            base_name = random.choice(components)
            standard_cost = round(random.uniform(1, 50), 2)
            material = {
                'material_id': self.generate_id('MAT', 'material'),
                'material_code': f"COMP-{self.counters['material']:05d}",
                'material_name': f"{base_name}",
                'material_type': 'component',
                'material_group': 'COMP',
                'base_unit_of_measure': 'EA',
                'procurement_type': random.choice(['buy', 'make']),
                'lead_time_days': random.randint(5, 21),
                'reorder_point': random.randint(500, 2000),
                'safety_stock': random.randint(200, 1000),
                'standard_cost': standard_cost,
                'material_status': 'active',
                # Missing columns
                'abc_classification': random.choice(['A', 'B', 'C']),
                'blocked_for_procurement': False,
                'blocked_for_production': False,
                'commodity_code': f"COMM-{random.randint(10000, 99999)}",
                'created_by': 'SYSTEM',
                'default_supplier_id': None,  # Will be assigned after suppliers are generated
                'dimensions': f"{random.randint(1, 50)}x{random.randint(1, 50)}x{random.randint(1, 50)}mm",
                'inspection_required': random.random() < 0.5,
                'last_purchase_price': standard_cost * random.uniform(0.9, 1.1),
                'lot_sizing_procedure': random.choice(['fixed_lot', 'period_lot']),
                'maximum_stock': random.randint(5000, 20000),
                'minimum_order_quantity': random.randint(100, 1000),
                'moving_average_cost': standard_cost * random.uniform(0.95, 1.05),
                'mrp_type': random.choice(['planned', 'forecast']),
                'order_multiple': random.choice([1, 5, 10, 25, 50]),
                'planning_time_fence_days': random.randint(7, 45),
                'product_family': random.choice(['FASTENERS', 'BEARINGS', 'SEALS', 'CLIPS']),
                'product_id': None,
                'shelf_life_days': random.randint(365, 3650),
                'updated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'valuation_class': random.choice(['STANDARD', 'MOVING_AVG']),
                'volume_m3': round(random.uniform(0.0001, 1), 6),
                'weight_kg': round(random.uniform(0.01, 100), 4),
                'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            self.materials.append(material)
        
        # Finished goods (link to products)
        for product in self.products:
            standard_cost = round(random.uniform(100, 2000), 2)
            material = {
                'material_id': self.generate_id('MAT', 'material'),
                'material_code': product['product_code'],
                'material_name': product['product_name'],
                'material_type': 'finished_good',
                'material_group': 'FG',
                'product_id': product['product_id'],
                'base_unit_of_measure': 'EA',
                'procurement_type': 'make',
                'lead_time_days': random.randint(1, 5),
                'reorder_point': random.randint(50, 200),
                'safety_stock': random.randint(20, 100),
                'standard_cost': standard_cost,
                'material_status': 'active',
                # Missing columns
                'abc_classification': 'A',  # Finished goods are always important
                'blocked_for_procurement': False,
                'blocked_for_production': False,
                'commodity_code': f"COMM-FG-{product['product_id']}",
                'created_by': 'SYSTEM',
                'dimensions': f"{random.randint(10, 500)}x{random.randint(10, 500)}x{random.randint(10, 500)}mm",
                'inspection_required': random.random() < 0.7,  # Most FGs require inspection
                'last_purchase_price': None,  # Manufactured, not purchased
                'lot_sizing_procedure': 'period_lot',
                'maximum_stock': random.randint(1000, 5000),
                'minimum_order_quantity': 1,
                'moving_average_cost': standard_cost * random.uniform(0.95, 1.05),
                'mrp_type': 'make-to-stock',
                'order_multiple': 1,
                'planning_time_fence_days': random.randint(30, 90),
                'product_family': product['product_name'],
                'shelf_life_days': random.randint(90, 730),  # 2 years for finished goods
                'updated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'valuation_class': 'STANDARD',
                'volume_m3': round(random.uniform(0.01, 50), 6),
                'weight_kg': round(random.uniform(0.5, 500), 4),
                'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            self.materials.append(material)
        
        # Consumables
        consumables = [
            'Gloves Nitrile', 'Safety Glasses', 'Ear Plugs', 'Face Mask',
            'Cleaning Solvent', 'Degreaser', 'Wipes Industrial', 'Rags Cotton',
            'Tape Masking', 'Tape Duct', 'Marker Permanent', 'Labels Barcode'
        ]
        
        for _ in range(material_types['consumable']):
            base_name = random.choice(consumables)
            standard_cost = round(random.uniform(5, 100), 2)
            material = {
                'material_id': self.generate_id('MAT', 'material'),
                'material_code': f"CONS-{self.counters['material']:05d}",
                'material_name': f"{base_name}",
                'material_type': 'consumable',
                'material_group': 'CONS',
                'base_unit_of_measure': random.choice(['EA', 'BOX', 'PKG']),
                'procurement_type': 'buy',
                'lead_time_days': random.randint(3, 14),
                'reorder_point': random.randint(50, 200),
                'safety_stock': random.randint(25, 100),
                'standard_cost': standard_cost,
                'material_status': 'active',
                'abc_classification': random.choice(['B', 'C']),
                'blocked_for_procurement': False,
                'blocked_for_production': False,
                'commodity_code': f"COMM-{random.randint(10000, 99999)}",
                'created_by': 'SYSTEM',
                'default_supplier_id': None,  # Will be assigned after suppliers are generated
                'dimensions': f"{random.randint(5, 50)}x{random.randint(5, 50)}x{random.randint(5, 50)}mm",
                'inspection_required': False,
                'last_purchase_price': standard_cost * random.uniform(0.9, 1.1),
                'lot_sizing_procedure': 'fixed_lot',
                'maximum_stock': random.randint(500, 2000),
                'minimum_order_quantity': random.randint(10, 100),
                'moving_average_cost': standard_cost * random.uniform(0.95, 1.05),
                'mrp_type': 'forecast',
                'order_multiple': random.choice([1, 5, 10, 25]),
                'planning_time_fence_days': random.randint(7, 30),
                'product_family': random.choice(['SAFETY', 'CLEANING', 'OFFICE']),
                'product_id': None,
                'shelf_life_days': random.randint(180, 730),
                'updated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'valuation_class': 'MOVING_AVG',
                'volume_m3': round(random.uniform(0.0001, 0.1), 6),
                'weight_kg': round(random.uniform(0.01, 10), 4),
                'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            self.materials.append(material)
        
        # Packaging
        packaging = [
            'Box Cardboard Small', 'Box Cardboard Medium', 'Box Cardboard Large',
            'Pallet Wood', 'Stretch Film', 'Bubble Wrap', 'Foam Insert',
            'Corner Protector', 'Strapping Plastic', 'Tape Packing'
        ]
        
        for _ in range(material_types['packaging']):
            base_name = random.choice(packaging)
            standard_cost = round(random.uniform(2, 50), 2)
            material = {
                'material_id': self.generate_id('MAT', 'material'),
                'material_code': f"PKG-{self.counters['material']:05d}",
                'material_name': f"{base_name}",
                'material_type': 'packaging',
                'material_group': 'PKG',
                'base_unit_of_measure': random.choice(['EA', 'ROLL', 'SHEET']),
                'procurement_type': 'buy',
                'lead_time_days': random.randint(5, 21),
                'reorder_point': random.randint(100, 500),
                'safety_stock': random.randint(50, 250),
                'standard_cost': standard_cost,
                'material_status': 'active',
                'abc_classification': 'C',
                'blocked_for_procurement': False,
                'blocked_for_production': False,
                'commodity_code': f"COMM-{random.randint(10000, 99999)}",
                'created_by': 'SYSTEM',
                'default_supplier_id': None,  # Will be assigned after suppliers are generated
                'dimensions': f"{random.randint(10, 200)}x{random.randint(10, 200)}x{random.randint(10, 200)}mm",
                'inspection_required': False,
                'last_purchase_price': standard_cost * random.uniform(0.9, 1.1),
                'lot_sizing_procedure': 'fixed_lot',
                'maximum_stock': random.randint(1000, 5000),
                'minimum_order_quantity': random.randint(50, 200),
                'moving_average_cost': standard_cost * random.uniform(0.95, 1.05),
                'mrp_type': 'forecast',
                'order_multiple': random.choice([1, 5, 10, 25, 50]),
                'planning_time_fence_days': random.randint(7, 30),
                'product_family': 'PACKAGING',
                'product_id': None,
                'shelf_life_days': None,  # Packaging doesn't expire
                'updated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'valuation_class': 'MOVING_AVG',
                'volume_m3': round(random.uniform(0.01, 5), 6),
                'weight_kg': round(random.uniform(0.1, 50), 4),
                'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            self.materials.append(material)
        
        print(f"Generated {len(self.materials)} materials")
    
    def generate_suppliers(self):
        """Generate supplier master data"""
        print("Generating suppliers...")
        
        supplier_names = [
            'ABC Steel Industries', 'XYZ Components Ltd', 'PQR Manufacturing',
            'Global Auto Parts', 'Premium Fasteners Inc', 'Quality Bearings Co',
            'Precision Tools Ltd', 'Industrial Supply Corp', 'Metro Hardware',
            'Eastern Components', 'Western Steel Works', 'Northern Metals'
        ]
        
        for _ in range(SUPPLIERS_TO_CREATE):
            supplier = {
                'supplier_id': self.generate_id('SUP', 'supplier'),
                'supplier_code': f"S{self.counters['supplier']:05d}",
                'supplier_name': random.choice(supplier_names),
                'contact_person': f"Contact Person {self.counters['supplier']}",
                'email': f"supplier{self.counters['supplier']}@example.com",
                'phone': f"+91 {random.randint(7000000000, 9999999999)}",
                'city': random.choice(['Mumbai', 'Pune', 'Delhi', 'Bangalore', 'Chennai']),
                'state': 'Maharashtra',
                'country': 'India',
                'currency': 'INR',
                'payment_terms': random.choice(['NET30', 'NET45', 'NET60']),
                'on_time_delivery_percentage': round(random.uniform(85, 98), 2),
                'quality_rating': round(random.uniform(3.5, 5.0), 2),
                'supplier_status': 'active',
                # Missing columns
                'address_line1': f"{random.randint(1, 999)} Industrial Area",
                'address_line2': f"Sector {random.randint(1, 50)}, {random.choice(supplier_names).split()[0]}",
                'blocked_for_orders': False,
                'certification_status': random.choice(['ISO_9001', 'ISO_14001', 'Not_Certified']),
                'created_by': 'SYSTEM',
                'postal_code': f"{random.randint(100000, 999999)}",
                'supplier_type': random.choice(['Raw_Materials', 'Components', 'Finished_Goods', 'Consumables']),
                'tax_id': f"TAX{random.randint(1000000, 9999999)}",
                'total_orders_count': random.randint(10, 500),
                'total_purchase_value': round(random.uniform(50000, 5000000), 2),
                'updated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            self.suppliers.append(supplier)
        
        # Assign suppliers to raw materials
        raw_materials = [m for m in self.materials if m['material_type'] == 'raw_material']
        for mat in raw_materials:
            mat['default_supplier_id'] = random.choice(self.suppliers)['supplier_id']
        
        print(f"Generated {len(self.suppliers)} suppliers")
    
    def generate_boms(self):
        """Generate Bills of Materials"""
        print("Generating BOMs...")
        
        finished_goods = [m for m in self.materials if m['material_type'] == 'finished_good']
        raw_materials = [m for m in self.materials if m['material_type'] == 'raw_material']
        components = [m for m in self.materials if m['material_type'] == 'component']
        
        for fg in finished_goods:
            bom = {
                'bom_id': self.generate_id('BOM', 'bom'),
                'bom_number': f"BOM-{fg['material_code']}",
                'parent_material_id': fg['material_id'],
                'bom_usage': 'production',
                'bom_status': 'active',
                'valid_from': (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d'),
                'base_quantity': 1,
                'base_unit': 'EA',
                # Missing columns
                'alternative_bom': 0,
                'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'created_by': 'SYSTEM',
                'engineering_change_number': f"ECN-{random.randint(1000, 9999)}" if random.random() < 0.1 else None,
                'is_current_revision': True,
                'lot_size': random.randint(10, 100),
                'parent_quantity': 1,
                'plant_id': random.choice([f['factory_id'] for f in self.factories]),
                'revision': '1.0',
                'scrap_percentage': round(random.uniform(0.5, 5), 2),
                'updated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'valid_to': None
            }
            self.boms.append(bom)
            
            # Add components (5-10 per BOM)
            num_components = random.randint(5, 10)
            selected_materials = random.sample(raw_materials + components, num_components)
            
            for idx, comp_mat in enumerate(selected_materials, 1):
                # Determine if component has a substitute (20% of components)
                has_substitute = random.random() < 0.2
                substitute_material_id = None
                valid_to = None
                
                if has_substitute:
                    # Pick a substitute from remaining materials
                    all_mats = raw_materials + components
                    available_for_sub = [m for m in all_mats if m['material_id'] != comp_mat['material_id']]
                    if available_for_sub:
                        substitute_material_id = random.choice(available_for_sub)['material_id']
                        # Substitute valid for 1-3 years
                        valid_to = (datetime.now() + timedelta(days=random.randint(365, 1095))).strftime('%Y-%m-%d')
                
                component = {
                    'component_id': self.generate_id('BOMC', 'bom'),
                    'bom_id': bom['bom_id'],
                    'item_number': idx * 10,
                    'material_id': comp_mat['material_id'],
                    'component_quantity': round(random.uniform(1, 10), 2),
                    'component_unit': comp_mat['base_unit_of_measure'],
                    'component_scrap_percentage': round(random.uniform(0, 5), 2),
                    # Missing columns
                    'backflush': random.choice([True, False]),
                    'cost_relevance': True,
                    'has_substitute': has_substitute,
                    'operation_number': idx,
                    'procurement_indicator': random.choice(['buy', 'make', 'transfer']),
                    'substitute_material_id': substitute_material_id,
                    'valid_from': datetime.now().strftime('%Y-%m-%d'),
                    'valid_to': valid_to,
                    'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                self.bom_components.append(component)
        
        print(f"Generated {len(self.boms)} BOMs with {len(self.bom_components)} components")
    
    def generate_sales_orders(self, start_date: datetime, days: int):
        """Generate sales orders with ULTRA-FAST PARALLEL processing"""
        print(f"Generating sales orders for {days} days with PARALLEL processing...")
        
        # Pre-validate data
        finished_goods = [m for m in self.materials if m['material_type'] == 'finished_good']
        valid_customer_ids = list(self.helper.get_valid_customer_ids())
        if not valid_customer_ids:
            valid_customer_ids = [c['customer_id'] for c in self.customers]
        valid_product_ids = list(self.helper.get_valid_product_ids())
        
        if not valid_customer_ids:
            raise ValueError("No customer IDs available!")
        
        if not self.parallel_enabled or days < 20:
            return self._generate_sales_orders_sequential(start_date, days, valid_customer_ids, valid_product_ids)
        
        # Parallel processing for large datasets  
        chunk_size = max(5, days // self.worker_count)  # At least 5 days per chunk
        day_chunks = [(i, min(chunk_size, days - i)) for i in range(0, days, chunk_size)]
        
        print(f"  🚀 Processing {len(day_chunks)} day chunks with {self.worker_count} workers...")
        
        all_sales_orders = []
        all_sales_order_lines = []
        
        with ThreadPoolExecutor(max_workers=self.worker_count) as executor:
            # Submit chunk processing tasks
            futures = {
                executor.submit(self._generate_sales_orders_chunk, 
                    start_date + timedelta(days=start_day), 
                    chunk_days, 
                    chunk_id,
                    valid_customer_ids, valid_product_ids): chunk_id 
                for chunk_id, (start_day, chunk_days) in enumerate(day_chunks)
            }
            
            # Collect results as they complete
            for future in as_completed(futures):
                chunk_id = futures[future]
                try:
                    chunk_results = future.result()
                    all_sales_orders.extend(chunk_results['sales_orders'])
                    all_sales_order_lines.extend(chunk_results['sales_order_lines'])
                    
                    print(f"    ✓ Sales orders chunk {chunk_id + 1}/{len(day_chunks)} completed ({len(chunk_results['sales_orders'])} orders)")
                except Exception as e:
                    print(f"    ✗ Sales orders chunk {chunk_id + 1} failed: {e}")
        
        # Store results with thread safety
        with self.data_lock:
            self.sales_orders.extend(all_sales_orders)
            self.sales_order_lines.extend(all_sales_order_lines)
        
        print(f"✓ Generated {len(self.sales_orders):,} sales orders via PARALLEL processing")
    
    def _generate_sales_orders_chunk(self, start_date: datetime, days: int, chunk_id: int,
                                   valid_customer_ids: List[str], valid_product_ids: List[str]) -> Dict:
        """Generate sales orders for a chunk of days (parallel worker method)"""
        
        chunk_sales_orders = []
        chunk_sales_order_lines = []
        
        # Local counters to avoid collision
        local_so_counter = chunk_id * 10000 + 1
        local_line_counter = chunk_id * 50000 + 1
        
        current_date = start_date
        
        for day in range(days):
            num_orders = random.randint(*SALES_ORDERS_PER_DAY)
            
            for _ in range(num_orders):
                order_date = current_date + timedelta(hours=random.randint(8, 16))
                customer_id = random.choice(valid_customer_ids)
                primary_product_id = random.choice(valid_product_ids)
                
                sales_order = {
                    'sales_order_id': f"SO-{str(local_so_counter).zfill(6)}",
                    'sales_order_number': f"SO-{order_date.strftime('%Y%m%d')}-{local_so_counter:04d}",
                    'customer_id': customer_id,
                    'product_id': primary_product_id,
                    'order_date': order_date.strftime('%Y-%m-%d'),
                    'order_type': 'standard',
                    'currency': 'INR',
                    'requested_delivery_date': (order_date + timedelta(days=random.randint(7, 30))).strftime('%Y-%m-%d'),
                    'order_status': 'open' if (datetime.now() - order_date).days < 15 else random.choice(['delivered', 'closed']),
                    'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'total_net_value': 0,
                    'total_value': 0
                }
                
                chunk_sales_orders.append(sales_order)
                
                # Add sales order lines (reduced for performance)
                num_lines = random.randint(2, 5)  # Reduced from 2-8
                total_value = 0
                
                for line_no in range(1, num_lines + 1):
                    product_id = random.choice(valid_product_ids)
                    # Find the finished good material for this product
                    fg_material = next((m for m in self.materials if m.get('product_id') == product_id), None)
                    quantity = random.randint(1, 100)
                    unit_price = round(random.uniform(10, 1000), 2)
                    line_total = quantity * unit_price
                    total_value += line_total
                    
                    line = {
                        'sales_order_line_id': f"SOL-{str(local_line_counter).zfill(6)}",
                        'sales_order_id': sales_order['sales_order_id'],
                        'line_number': line_no,
                        'material_id': fg_material['material_id'] if fg_material else None,  # Required: FK to materials
                        'product_id': product_id,
                        'order_quantity': quantity,  # Required: Schema field name
                        'unit_of_measure': fg_material['base_unit_of_measure'] if fg_material else 'EA',  # Required
                        'unit_price': unit_price,
                        'line_status': sales_order['order_status'],
                        'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    }
                    
                    chunk_sales_order_lines.append(line)
                    local_line_counter += 1
                
                # Update sales order totals
                sales_order['total_net_value'] = total_value
                sales_order['total_value'] = total_value * 1.18  # Including 18% GST
                local_so_counter += 1
            
            current_date += timedelta(days=1)
        
        return {
            'sales_orders': chunk_sales_orders,
            'sales_order_lines': chunk_sales_order_lines
        }
    
    def _generate_sales_orders_sequential(self, start_date: datetime, days: int,
                                        valid_customer_ids: List[str], valid_product_ids: List[str]):
        """Fallback sequential sales orders generation"""
        print("Generating sales orders (sequential fallback)...")
        
        current_date = start_date
        for day in range(days):
            num_orders = random.randint(*SALES_ORDERS_PER_DAY)
            for _ in range(num_orders):
                # Simplified sequential logic
                sales_order = {
                    'sales_order_id': self.generate_id('SO', 'sales_order'),
                    'order_status': 'open'
                }
                self.sales_orders.append(sales_order)
            current_date += timedelta(days=1)
        
        print(f"✓ Generated {len(self.sales_orders)} sales orders (sequential)")
    
    def generate_production_orders(self):
        """Generate production orders from sales orders with PARALLEL processing"""
        print("Generating production orders with PARALLEL processing...")
        
        if not self.parallel_enabled or len(self.sales_orders) < 1000:
            return self._generate_production_orders_sequential()
        
        # Parallel processing for large datasets
        chunk_size = max(100, len(self.sales_orders) // self.worker_count)
        order_chunks = [self.sales_orders[i:i + chunk_size] for i in range(0, len(self.sales_orders), chunk_size)]
        
        print(f"  🚀 Processing {len(order_chunks)} sales order chunks with {self.worker_count} workers...")
        
        all_production_orders = []
        
        with ThreadPoolExecutor(max_workers=self.worker_count) as executor:
            futures = {
                executor.submit(self._generate_production_orders_chunk, chunk, chunk_id): chunk_id 
                for chunk_id, chunk in enumerate(order_chunks)
            }
            
            for future in as_completed(futures):
                chunk_id = futures[future]
                try:
                    chunk_orders = future.result()
                    all_production_orders.extend(chunk_orders)
                    print(f"    ✓ Production orders chunk {chunk_id + 1}/{len(order_chunks)} completed ({len(chunk_orders)} orders)")
                except Exception as e:
                    print(f"    ✗ Production orders chunk {chunk_id + 1} failed: {e}")
        
        with self.data_lock:
            self.production_orders.extend(all_production_orders)
        
        print(f"✓ Generated {len(self.production_orders):,} production orders via PARALLEL processing")
    
    def _generate_production_orders_chunk(self, sales_orders_chunk: List[Dict], chunk_id: int) -> List[Dict]:
        """Generate production orders for a chunk of sales orders (parallel worker method)"""
        chunk_production_orders = []
        available_work_orders = list(self.work_orders)
        local_counter = chunk_id * 50000 + 1
        
        for so in sales_orders_chunk:
            so_lines = [l for l in self.sales_order_lines if l['sales_order_id'] == so['sales_order_id']]
            
            for line in so_lines:
                scheduled_start = datetime.strptime(so['order_date'], '%Y-%m-%d') + timedelta(days=random.randint(1, 5))
                # Use order_date + random days for delivery since we don't have requested_delivery_date in our lines
                scheduled_end = scheduled_start + timedelta(days=random.randint(7, 21))
                actual_start = scheduled_start + timedelta(hours=random.randint(0, 48)) if random.random() < 0.8 else None
                actual_end = actual_start + timedelta(days=(scheduled_end - scheduled_start).days) if actual_start else None
                
                order_quantity = line.get('order_quantity', line.get('quantity', 1))
                delivered_quantity = int(order_quantity * random.uniform(0.8, 1.0)) if actual_end else 0
                scrap_quantity = int(delivered_quantity * random.uniform(0, 0.05))
                
                # Link to work order if available (85% chance)
                work_order_id = None
                if self.work_orders and random.random() < 0.85:
                    # Reuse work orders if we run out
                    if not available_work_orders:
                        available_work_orders = list(self.work_orders)
                    work_order_id = available_work_orders.pop(0)['work_order_id']
                
                # Get material_id from the sales order line
                material_id = line.get('material_id')
                if not material_id:
                    # Fallback: find material for this product
                    product_id = line.get('product_id')
                    fg_material = next((m for m in self.materials if m.get('product_id') == product_id), None)
                    material_id = fg_material['material_id'] if fg_material else None
                
                if not material_id:
                    continue  # Skip if no material found
                
                # Find the factory for this material
                material_obj = next((m for m in self.materials if m['material_id'] == material_id), None)
                plant_id = random.choice([f['factory_id'] for f in self.factories]) if self.factories else 'PLANT-1'
                
                prod_order = {
                    'production_order_id': self.generate_id('PROD', 'prod_order'),
                    'production_order_number': f"PROD-{local_counter:06d}",  # Required: Unique number
                    'material_id': material_id,  # Required: FK to materials
                    'plant_id': plant_id,  # Required: FK to factories
                    'sales_order_id': so['sales_order_id'],
                    'work_order_id': work_order_id,  # MES integration
                    'order_type': 'make_to_order',
                    'order_quantity': order_quantity,
                    'delivered_quantity': delivered_quantity,
                    'scrap_quantity': scrap_quantity,
                    'basic_start_date': scheduled_start.strftime('%Y-%m-%d'),  # Required
                    'basic_end_date': scheduled_end.strftime('%Y-%m-%d'),  # Required
                    'scheduled_start_date': scheduled_start.strftime('%Y-%m-%d'),
                    'scheduled_end_date': scheduled_end.strftime('%Y-%m-%d'),
                    'actual_start_date': actual_start.strftime('%Y-%m-%d') if actual_start else None,
                    'system_status': 'completed' if actual_end else 'created',
                    'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                
                chunk_production_orders.append(prod_order)
                local_counter += 1
        
        return chunk_production_orders
    
    def _generate_production_orders_sequential(self):
        """Fallback sequential production orders generation"""
        print("Generating production orders (sequential fallback)...")
        
        available_work_orders = list(self.work_orders)
        
        for so in self.sales_orders:
            so_lines = [l for l in self.sales_order_lines if l['sales_order_id'] == so['sales_order_id']]
            
            for line in so_lines:
                scheduled_start = datetime.strptime(so['order_date'], '%Y-%m-%d') + timedelta(days=random.randint(1, 5))
                scheduled_end = scheduled_start + timedelta(days=random.randint(7, 21))
                
                prod_order = {
                    'production_order_id': self.generate_id('PROD', 'prod_order'),
                    'sales_order_id': so['sales_order_id'],
                    'product_id': line['product_id'],
                    'order_quantity': line['quantity'],
                    'order_status': 'completed' if random.random() < 0.8 else 'planned',
                    'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                
                self.production_orders.append(prod_order)
        
        print(f"✓ Generated {len(self.production_orders)} production orders (sequential)")
    
    def generate_purchase_orders(self, start_date: datetime, days: int):
        """Generate purchase orders with ULTRA-FAST PARALLEL processing"""
        print(f"Generating purchase orders for {days} days with PARALLEL processing...")
        
        # Pre-validate data
        purchasable_materials = [m for m in self.materials if m['procurement_type'] in ['buy', 'both']]
        if not purchasable_materials:
            print("WARNING: No purchasable materials found, using first 10 materials")
            purchasable_materials = self.materials[:10] if self.materials else []
        
        print(f"Using {len(purchasable_materials)} purchasable materials from {len(self.materials)} total materials")
        
        if not self.parallel_enabled or days < 20:
            return self._generate_purchase_orders_sequential(start_date, days, purchasable_materials)
        
        # Parallel processing for large datasets  
        chunk_size = max(5, days // self.worker_count)
        day_chunks = [(i, min(chunk_size, days - i)) for i in range(0, days, chunk_size)]
        
        print(f"  🚀 Processing {len(day_chunks)} day chunks with {self.worker_count} workers...")
        
        all_purchase_orders = []
        all_purchase_order_lines = []
        
        with ThreadPoolExecutor(max_workers=self.worker_count) as executor:
            futures = {
                executor.submit(self._generate_purchase_orders_chunk, 
                    start_date + timedelta(days=start_day), 
                    chunk_days, 
                    chunk_id,
                    purchasable_materials): chunk_id 
                for chunk_id, (start_day, chunk_days) in enumerate(day_chunks)
            }
            
            for future in as_completed(futures):
                chunk_id = futures[future]
                try:
                    chunk_results = future.result()
                    all_purchase_orders.extend(chunk_results['purchase_orders'])
                    all_purchase_order_lines.extend(chunk_results['purchase_order_lines'])
                    
                    print(f"    ✓ Purchase orders chunk {chunk_id + 1}/{len(day_chunks)} completed ({len(chunk_results['purchase_orders'])} orders)")
                except Exception as e:
                    print(f"    ✗ Purchase orders chunk {chunk_id + 1} failed: {e}")
        
        # Store results with thread safety
        with self.data_lock:
            self.purchase_orders.extend(all_purchase_orders)
            self.purchase_order_lines.extend(all_purchase_order_lines)
        
        print(f"✓ Generated {len(self.purchase_orders):,} purchase orders via PARALLEL processing")
    
    def _generate_purchase_orders_chunk(self, start_date: datetime, days: int, chunk_id: int,
                                      purchasable_materials: List[Dict]) -> Dict:
        """Generate purchase orders for a chunk of days (parallel worker method)"""
        
        chunk_purchase_orders = []
        chunk_purchase_order_lines = []
        
        local_po_counter = chunk_id * 10000 + 1
        local_line_counter = chunk_id * 30000 + 1
        
        current_date = start_date
        
        for day in range(days):
            num_pos = random.randint(*PURCHASE_ORDERS_PER_DAY)
            
            for _ in range(num_pos):
                supplier = random.choice(self.suppliers)
                po_date = current_date + timedelta(hours=random.randint(9, 15))
                
                po = {
                    'purchase_order_id': f"PO-{str(local_po_counter).zfill(6)}",
                    'po_number': f"PO-{po_date.strftime('%Y%m%d')}-{local_po_counter:04d}",
                    'supplier_id': supplier['supplier_id'],
                    'po_date': po_date.strftime('%Y-%m-%d'),
                    'po_type': 'standard',
                    'currency': 'INR',
                    'po_status': 'released' if (datetime.now() - po_date).days > 7 else 'created',
                    'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'total_value': 0
                }
                
                chunk_purchase_orders.append(po)
                
                # Add purchase order lines (reduced for performance)
                num_lines = random.randint(2, 4)  # Reduced from 2-6
                total_value = 0
                
                for line_no in range(1, num_lines + 1):
                    material = random.choice(purchasable_materials)
                    quantity = random.randint(10, 500)
                    unit_price = round(random.uniform(5, 200), 2)
                    line_total = quantity * unit_price
                    total_value += line_total
                    delivery_date = po_date + timedelta(days=random.randint(7, 30))
                    
                    line = {
                        'po_line_id': f"POL-{str(local_line_counter).zfill(6)}",
                        'purchase_order_id': po['purchase_order_id'],
                        'line_number': line_no,
                        'material_id': material['material_id'],
                        'order_quantity': quantity,
                        'unit_of_measure': material['base_unit_of_measure'],
                        'delivery_date': delivery_date.strftime('%Y-%m-%d'),
                       
                        'unit_price': unit_price,
                        'total_amount': line_total,
                        'line_status': po['po_status'],
                        'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    }
                    
                    chunk_purchase_order_lines.append(line)
                    local_line_counter += 1
                
                po['total_value'] = total_value
                local_po_counter += 1
            
            current_date += timedelta(days=1)
        
        return {
            'purchase_orders': chunk_purchase_orders,
            'purchase_order_lines': chunk_purchase_order_lines
        }
    
    def _generate_purchase_orders_sequential(self, start_date: datetime, days: int, purchasable_materials: List[Dict]):
        """Fallback sequential purchase orders generation"""
        print("Generating purchase orders (sequential fallback)...")
        
        current_date = start_date
        for day in range(days):
            num_pos = random.randint(*PURCHASE_ORDERS_PER_DAY)
            for _ in range(num_pos):
                po = {
                    'purchase_order_id': self.generate_id('PO', 'po'),
                    'po_status': 'released'
                }
                self.purchase_orders.append(po)
            current_date += timedelta(days=1)
        
        print(f"✓ Generated {len(self.purchase_orders)} purchase orders (sequential)")
    
    def generate_inventory(self):
        """Generate inventory balances"""
        print("Generating inventory balances...")
        
        for material in self.materials:
            for factory in self.factories:
                balance = {
                    'balance_id': f"INV-{material['material_id']}-{factory['factory_id']}",
                    'material_id': material['material_id'],
                    'plant_id': factory['factory_id'],
                    'storage_location': 'WH01',
                    'unrestricted_stock': random.randint(100, 5000) if material['material_type'] != 'finished_good' else random.randint(10, 100),
                    'reserved_stock': random.randint(0, 50),
                    'blocked_stock': random.randint(0, 10),
                    'unit_of_measure': material['base_unit_of_measure'],
                    'last_goods_receipt': (datetime.now() - timedelta(days=random.randint(1, 30))).strftime('%Y-%m-%d'),
                    'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                self.inventory_balances.append(balance)
        
        print(f"Generated {len(self.inventory_balances)} inventory balance records")
    
    def _generate_purchase_orders_chunk_DUPLICATE_REMOVED(self, start_date: datetime, days: int, chunk_id: int,
                                      purchasable_materials: List[Dict]) -> Dict:
        """Generate purchase orders for a chunk of days (parallel worker method)"""
        
        chunk_purchase_orders = []
        chunk_purchase_order_lines = []
        
        local_po_counter = chunk_id * 10000 + 1
        local_line_counter = chunk_id * 30000 + 1
        
        current_date = start_date
        
        for day in range(days):
            num_pos = random.randint(*PURCHASE_ORDERS_PER_DAY)
            
            for _ in range(num_pos):
                supplier = random.choice(self.suppliers)
                po_date = current_date + timedelta(hours=random.randint(9, 15))
                
                po = {
                    'purchase_order_id': f"PO-{str(local_po_counter).zfill(6)}",
                    'po_number': f"PO-{po_date.strftime('%Y%m%d')}-{local_po_counter:04d}",
                    'supplier_id': supplier['supplier_id'],
                    'po_date': po_date.strftime('%Y-%m-%d'),
                    'po_type': 'standard',
                    'currency': 'INR',
                    'po_status': 'released' if (datetime.now() - po_date).days > 7 else 'created',
                    'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'total_value': 0
                }
                
                chunk_purchase_orders.append(po)
                
                # Add purchase order lines (reduced for performance)
                num_lines = random.randint(2, 4)  # Reduced from 2-6
                total_value = 0
                
                for line_no in range(1, num_lines + 1):
                    material = random.choice(purchasable_materials)
                    quantity = random.randint(10, 500)
                    unit_price = round(random.uniform(5, 200), 2)
                    line_total = quantity * unit_price
                    total_value += line_total
                    delivery_date = po_date + timedelta(days=random.randint(7, 30))
                    
                    line = {
                        'po_line_id': f"POL-{str(local_line_counter).zfill(6)}",
                        'purchase_order_id': po['purchase_order_id'],
                        'line_number': line_no,
                        'material_id': material['material_id'],
                        'order_quantity': quantity,
                        'unit_of_measure': material['base_unit_of_measure'],
                        'delivery_date': delivery_date.strftime('%Y-%m-%d'),
                       
                        'unit_price': unit_price,
                        'total_amount': line_total,
                        'line_status': po['po_status'],
                        'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    }
                    
                    chunk_purchase_order_lines.append(line)
                    local_line_counter += 1
                
                po['total_value'] = total_value
                local_po_counter += 1
            
            current_date += timedelta(days=1)
        
        return {
            'purchase_orders': chunk_purchase_orders,
            'purchase_order_lines': chunk_purchase_order_lines
        }
    
    def _generate_purchase_orders_sequential(self, start_date: datetime, days: int, purchasable_materials: List[Dict]):
        """Fallback sequential purchase orders generation"""
        print("Generating purchase orders (sequential fallback)...")
        
        current_date = start_date
        for day in range(days):
            num_pos = random.randint(*PURCHASE_ORDERS_PER_DAY)
            for _ in range(num_pos):
                po = {
                    'purchase_order_id': self.generate_id('PO', 'po'),
                    'po_status': 'released'
                }
                self.purchase_orders.append(po)
            current_date += timedelta(days=1)
        
        print(f"✓ Generated {len(self.purchase_orders)} purchase orders (sequential)")
    
    def generate_inventory(self):
        """Generate inventory balances"""
        print("Generating inventory balances...")
        
        for material in self.materials:
            for factory in self.factories:
                balance = {
                    'balance_id': f"INV-{material['material_id']}-{factory['factory_id']}",
                    'material_id': material['material_id'],
                    'plant_id': factory['factory_id'],
                    'storage_location': 'WH01',
                    'unrestricted_stock': random.randint(100, 5000) if material['material_type'] != 'finished_good' else random.randint(10, 100),
                    'stock_value': 0,  # Calculate based on cost
                    'updated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                
                balance['stock_value'] = round(balance['unrestricted_stock'] * material['standard_cost'], 2)
                self.inventory_balances.append(balance)
        
        print(f"Generated {len(self.inventory_balances)} inventory balance records")
    
    def _print_summary(self):
        print(f"\nERP Data Summary:")
        print(f"  Materials: {len(self.materials)}")
        print(f"  Suppliers: {len(self.suppliers)}")
        print(f"  BOMs: {len(self.boms)} ({len(self.bom_components)} components)")
        print(f"  Sales Orders: {len(self.sales_orders)} ({len(self.sales_order_lines)} lines)")
        print(f"  Production Orders: {len(self.production_orders)}")
        print(f"  Purchase Orders: {len(self.purchase_orders)} ({len(self.purchase_order_lines)} lines)")
        print(f"  Inventory Balances: {len(self.inventory_balances)}")
    
    def to_sql_inserts(self, output_file='erp_historical_data_inserts.sql'):
        """Generate SQL INSERT statements"""
        print(f"\nGenerating SQL INSERT statements...")
        
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
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("-- GenIMS ERP Historical Data\n\n")
            
            # Materials
            f.write("-- MATERIALS\n")
            for mat in self.materials[:100]:  # Sample for size
                cols = ['material_id', 'material_code', 'material_name', 'material_type',
                       'base_unit_of_measure', 'procurement_type', 'lead_time_days',
                       'standard_cost', 'material_status']
                vals = [format_value(mat.get(c)) for c in cols]
                f.write(f"INSERT INTO materials ({', '.join(cols)}) VALUES ({', '.join(vals)});\n")
            f.write(f"\n-- Total: {len(self.materials)} materials\n\n")
            
            # Similar for other tables...
            f.write("-- See full data in JSON export\n")
        
        print(f"SQL sample written to {output_file}")
    
    def to_json(self, output_file='erp_historical_data.json'):
        """Export to JSON with flat structure matching actual table names"""
        print(f"\nExporting to JSON...")
        
        # Generate missing data tables
        bill_of_materials = self._generate_bill_of_materials()
        routing = self._generate_routing()
        routing_operations = self._generate_routing_operations()
        work_centers = self._generate_work_centers()
        purchase_requisitions = self._generate_purchase_requisitions()
        purchase_requisition_lines = self._generate_purchase_requisition_lines()
        inventory_transactions = self._generate_inventory_transactions()
        goods_receipts = self._generate_goods_receipts()
        mrp_runs = self._generate_mrp_runs()
        mrp_elements = self._generate_mrp_elements()
        inspection_plans = self._generate_inspection_plans()
        inspection_characteristics = self._generate_inspection_characteristics()
        cost_centers = self._generate_cost_centers()
        general_ledger = self._generate_general_ledger()
        erp_mes_sync_log = self._generate_erp_mes_sync_log()
        
        data = {
            # Materials & Suppliers
            'materials': self.materials,
            'suppliers': self.suppliers,
            'bill_of_materials': bill_of_materials,
            'bom_components': self.bom_components,
            'routing': routing,
            'routing_operations': routing_operations,
            'work_centers': work_centers,
            
            # Sales Orders
            'sales_orders': self.sales_orders,
            'sales_order_lines': self.sales_order_lines,
            
            # Production Orders
            'production_orders': self.production_orders,
            
            # Purchase Orders & Requisitions
            'purchase_orders': self.purchase_orders,
            'purchase_order_lines': self.purchase_order_lines,
            'purchase_requisitions': purchase_requisitions,
            'purchase_requisition_lines': purchase_requisition_lines,
            
            # Inventory & Goods
            'inventory_balances': self.inventory_balances,
            'inventory_transactions': inventory_transactions,
            'goods_receipts': goods_receipts,
            
            # MRP & Planning
            'mrp_runs': mrp_runs,
            'mrp_elements': mrp_elements,
            
            # Quality & Inspection
            'inspection_plans': inspection_plans,
            'inspection_characteristics': inspection_characteristics,
            
            # Cost & Finance
            'cost_centers': cost_centers,
            'general_ledger': general_ledger,
            
            # Integration
            'erp_mes_sync_log': erp_mes_sync_log
        }
        
        with open(output_file, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"Data exported to {output_file}")
    
    def _generate_bill_of_materials(self):
        """Generate BOM records"""
        boms = []
        for i, product in enumerate(self.products):
            created_dt = (datetime.now() - timedelta(days=random.randint(60, 365)))
            valid_from_dt = (datetime.now() - timedelta(days=random.randint(30, 180)))
            
            # Find corresponding finished good material for this product
            fg_material = next((m for m in self.materials if m.get('product_id') == product['product_id']), None)
            if not fg_material:
                continue  # Skip if no material found for this product
            
            boms.append({
                'bom_id': f"BOM-{2001+i}",
                'bom_number': f"BOM-{product['product_code']}",
                'parent_material_id': fg_material['material_id'],  # Required: FK to materials
                'product_id': product['product_id'],
                'bom_status': 'active',
                'valid_from': valid_from_dt.strftime('%Y-%m-%d'),
                'created_at': created_dt.strftime('%Y-%m-%d')
            })
        return boms
    
    def _generate_routing(self):
        """Generate routing records"""
        routings = []
        for i in range(10):
            valid_from_dt = (datetime.now() - timedelta(days=random.randint(30, 180)))
            
            # Select a finished good material for this routing
            fg_materials = [m for m in self.materials if m['material_type'] == 'finished_good']
            if not fg_materials:
                continue
            
            material = random.choice(fg_materials)
            
            routings.append({
                'routing_id': f"ROUTE-{3001+i}",
                'routing_number': f"ROUT-{3001+i}",
                'material_id': material['material_id'],  # Required: FK to materials
                'plant_id': random.choice(self.factories)['factory_id'] if self.factories else None,
                'routing_status': 'active',
                'valid_from': valid_from_dt.strftime('%Y-%m-%d')
            })
        return routings
    
    def _generate_routing_operations(self):
        """Generate routing operation records"""
        operations = []
        for i in range(30):
            labor_hrs = round(random.uniform(0.5, 4), 2)
            duration_hrs = round(random.uniform(0.5, 8), 2)
            op_num = random.randint(1, 50)
            
            operations.append({
                'operation_id': f"ROUTOP-{4001+i}",  # Required: Primary key
                'routing_id': f"ROUTE-{3001+random.randint(0, 9)}",
                'operation_number': op_num,
                'operation_description': f"Operation step {random.randint(1, 10)}",
                'work_center_id': f"WC-{5001+random.randint(0, 9)}",
                'setup_time': round(random.uniform(5, 30), 2),
                'machine_time': duration_hrs * 60,  # Convert hours to minutes
                'labor_time': labor_hrs * 60  # Convert hours to minutes
            })
        return operations
    
    def _generate_work_centers(self):
        """Generate work center records"""
        work_centers = []
        for i in range(10):
            work_centers.append({
                'work_center_id': f"WC-{5001+i}",
                'work_center_code': f"WC-{5001+i}",
                'work_center_name': f"Work Center {i+1}",
                'factory_id': random.choice(self.factories)['factory_id'],
                'department': random.choice(['Assembly', 'Machining', 'Welding', 'Painting', 'Testing']),
                'capacity_units_per_hour': random.randint(50, 500),
                'work_center_type': 'production',
                'status': 'active'
            })
        return work_centers
    
    def _generate_purchase_requisitions(self):
        """Generate purchase requisition records"""
        prereqs = []
        for i in range(15):
            req_dt = (datetime.now() - timedelta(days=random.randint(0, 30)))
            needed_dt = (datetime.now() + timedelta(days=random.randint(7, 60)))
            
            prereqs.append({
                'purchase_requisition_id': f"PREREQ-{6001+i}",
                'requisition_number': f"PREQ-{6001+i}",
                'requisition_id': f"PREQ-{random.randint(100001, 999999)}",
                'requisition_code': f"PREREQ-{6001+i}",
                'requisition_date': req_dt.strftime('%Y-%m-%d'),
                'required_date': needed_dt.strftime('%Y-%m-%d'),
                'requested_by_employee_id': f"EMP-{random.randint(1, 100):06d}",
                'needed_date': needed_dt.strftime('%Y-%m-%d'),
                'status': random.choice(['draft', 'submitted', 'approved', 'rejected']),
                'priority': random.choice(['low', 'medium', 'high', 'urgent']),
                'notes': f"Purchase requisition {6001+i}"
            })
        return prereqs
    
    def _generate_purchase_requisition_lines(self):
        """Generate purchase requisition line records"""
        lines = []
        for i in range(50):
            req_qty = random.randint(50, 1000)
            unit_price = round(random.uniform(10, 1000), 2)
            delivery_dt = (datetime.now() + timedelta(days=random.randint(7, 60)))
            
            lines.append({
                'purchase_requisition_line_id': f"PREQL-{7001+i}",
                'requisition_id': f"PREQ-{6001+random.randint(0, 14)}",
                'requisition_line_id': f"PREQL-{random.randint(100001, 999999)}",
                'line_number': random.randint(1, 10),
                'purchase_requisition_id': f"PREREQ-{6001+random.randint(0, 14)}",
                'material_id': random.choice(self.materials)['material_id'],
                'quantity': req_qty,
                'requested_quantity': req_qty,
                'delivery_date': delivery_dt.strftime('%Y-%m-%d'),
                'unit_of_measure': 'PCS',
                'estimated_unit_price': unit_price,
                'notes': f"Line for requisition item"
            })
        return lines
    
    def _generate_inventory_transactions(self):
        """Generate inventory transaction records"""
        transactions = []
        for i in range(40):
            trans_dt = (datetime.now() - timedelta(days=random.randint(0, 60)))
            qty = random.randint(-500, 1000)
            
            material = random.choice(self.materials)
            factory = random.choice(self.factories) if self.factories else None
            
            transactions.append({
                'transaction_id': f"INVTR-{random.randint(100001, 999999)}",  # Required: Primary key
                'material_id': material['material_id'],
                'plant_id': factory['factory_id'] if factory else 'PLANT-1',  # Required: FK to factories
                'storage_location': f"LOC-{random.randint(100, 500)}",
                'posting_date': trans_dt.strftime('%Y-%m-%d'),
                'document_date': trans_dt.strftime('%Y-%m-%d'),
                'movement_type': random.choice(['101', '261', '311', '551']),  # Use movement type codes
                'transaction_type': random.choice(['goods_receipt', 'goods_issue', 'adjustment', 'return']),
                'quantity': abs(qty),  # Ensure positive quantity
                'unit_of_measure': material['base_unit_of_measure'],
                'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            })
        return transactions
    
    def _generate_goods_receipts(self):
        """Generate goods receipt records"""
        receipts = []
        for i in range(20):
            receipt_dt = (datetime.now() - timedelta(days=random.randint(0, 30)))
            receipt_tm = f"{random.randint(8, 17):02d}:{random.randint(0, 59):02d}:00"
            qty = random.randint(100, 5000)
            
            receipts.append({
                'goods_receipt_id': f"GOODSRC-{9001+i}",
                'gr_number': f"GR-{9001+i}",
                'gr_date': receipt_dt.strftime('%Y-%m-%d'),
                'posting_date': receipt_dt.strftime('%Y-%m-%d'),
                'material_id': random.choice(self.materials)['material_id'],
                'quantity_received': qty,
                'unit_of_measure': 'PCS',
                'goods_receipt_code': f"GOODSRC-{9001+i}",
                'purchase_order_id': random.choice(self.purchase_orders)['purchase_order_id'] if self.purchase_orders else f"PO-{random.randint(1001, 1020)}",
                'receipt_date': receipt_dt.strftime('%Y-%m-%d'),
                'receipt_time': receipt_tm,
                'received_by_employee_id': f"EMP-{random.randint(1, 100):06d}",
                'status': random.choice(['pending_inspection', 'inspected', 'accepted', 'rejected']),
                'total_weight_kg': round(random.uniform(10, 10000), 2),
                'notes': f"Goods receipt {9001+i}"
            })
        return receipts
    
    def _generate_mrp_runs(self):
        """Generate MRP run records"""
        mrp_runs = []
        for i in range(10):
            run_dt = (datetime.now() - timedelta(days=random.randint(0, 30)))
            
            mrp_runs.append({
                'mrp_run_id': f"MRP-RUN-{10001+i}",
                'run_number': f"RUN-{10001+i}",
                'planning_date': run_dt.strftime('%Y-%m-%d'),
                'run_date': run_dt.strftime('%Y-%m-%d'),
                'planning_horizon_days': random.randint(30, 180),
                'status': random.choice(['completed', 'in_progress', 'scheduled']),
                'total_demands': random.randint(100, 1000),
                'planned_orders': random.randint(50, 500),
                'notes': f"MRP run {10001+i}"
            })
        return mrp_runs
    
    def _generate_mrp_elements(self):
        """Generate MRP element records"""
        elements = []
        for i in range(50):
            planned_order_dt = (datetime.now() + timedelta(days=random.randint(1, 60)))
            
            plant_id = f"PLANT-{random.randint(1, 5)}"
            element_type = random.choice(['independent_requirement', 'dependent_requirement', 'purchase_order', 'production_order'])
            req_qty = random.randint(100, 5000) if 'requirement' in element_type else 0
            rcpt_qty = random.randint(100, 4000) if element_type in ['purchase_order', 'production_order'] else 0
            
            elements.append({
                'element_id': f"MRPELEM-{11001+i}",  # Required: Primary key
                'mrp_run_id': f"MRP-RUN-{10001+random.randint(0, 9)}",
                'material_id': random.choice(self.materials)['material_id'],
                'plant_id': plant_id,
                'element_type': element_type,
                'element_date': planned_order_dt.strftime('%Y-%m-%d'),
                'requirement_quantity': req_qty,
                'receipt_quantity': rcpt_qty,
                'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            })
        return elements
    
    def _generate_inspection_plans(self):
        """Generate inspection plan records"""
        plans = []
        # Generate inspection plans for all materials that require inspection
        for i, material in enumerate(self.materials):
            plans.append({
                'inspection_plan_id': f"INSP-{12001+i}",
                'plan_number': f"PLAN-{12001+i}",
                'material_id': material['material_id'],
                'inspection_type': random.choice(['incoming', 'in_process', 'final']),
                'sampling_method': random.choice(['100%', '5%', '10%', 'AQL']),
                'aql_percent': round(random.uniform(0.5, 5), 1),
                'status': 'active',
                'created_date': (datetime.now() - timedelta(days=random.randint(30, 365))).strftime('%Y-%m-%d')
            })
        return plans
    
    def _generate_inspection_characteristics(self):
        """Generate inspection characteristic records"""
        characteristics = []
        for i in range(40):
            lower_spec = round(random.uniform(0, 50), 2)
            upper_spec = round(random.uniform(lower_spec + 10, 100), 2)
            
            characteristics.append({
                'characteristic_id': f"INSPCHAR-{13001+i}",  # Required: Primary key
                'inspection_plan_id': f"INSP-{12001+random.randint(0, 19)}",
                'characteristic_name': f"Characteristic {random.randint(1, 50)}",
                'lower_spec_limit': lower_spec,
                'upper_spec_limit': upper_spec,
                'unit_of_measure': random.choice(['mm', 'kg', 'sec', '%', 'ohms']),
                'inspection_method': random.choice(['visual', 'measurement', 'functional', 'attribute']),
                'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            })
        return characteristics
    
    def _generate_cost_centers(self):
        """Generate cost center records"""
        cost_centers = []
        for i in range(15):
            cost_centers.append({
                'cost_center_id': f"CC-{14001+i}",
                'cost_center_code': f"CC-{14001+i}",
                'cost_center_name': f"Cost Center {i+1}",
                'factory_id': random.choice(self.factories)['factory_id'],
                'cost_type': random.choice(['manufacturing', 'service', 'administrative', 'sales']),
                'department': f"Dept-{i+1}",
                'manager_employee_id': f"EMP-{random.randint(1, 50):06d}",
                'budget_amount': round(random.uniform(100000, 1000000), 2),
                'status': 'active'
            })
        return cost_centers
    
    def _generate_general_ledger(self):
        """Generate general ledger entries"""
        entries = []
        for i in range(100):
            entry_dt = (datetime.now() - timedelta(days=random.randint(0, 90)))
            debit_amt = round(random.uniform(0, 10000), 2) if random.random() > 0.5 else 0
            credit_amt = round(random.uniform(0, 10000), 2) if random.random() > 0.5 else 0
            
            entries.append({
                'gl_transaction_id': f"GL-{15001+i}",  # Required: Primary key
                'posting_date': entry_dt.strftime('%Y-%m-%d'),
                'document_date': entry_dt.strftime('%Y-%m-%d'),
                'company_code': f"COMP-{random.randint(1, 5):03d}",
                'gl_account': f"{random.randint(1000, 9999)}",
                'debit_amount': debit_amt,
                'credit_amount': credit_amt,
                'cost_center_id': f"CC-{14001+random.randint(0, 14)}",
                'reference_document': f"DOC-{random.randint(1000, 9999)}",
                'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            })
        return entries
    
    def _generate_erp_mes_sync_log(self):
        """Generate ERP-MES sync log records"""
        sync_logs = []
        for i in range(30):
            sync_logs.append({
                'sync_log_id': f"SYNC-{16001+i}",
                'sync_id': f"SYNC-{random.randint(100001, 999999)}",
                'sync_timestamp': (datetime.now() - timedelta(hours=random.randint(0, 168))).isoformat(),
                'sync_type': random.choice(['production_orders', 'material_movements', 'quality_data', 'labor_data']),
                'source_system': 'MES',
                'target_system': 'ERP',
                'records_synced': random.randint(10, 500),
                'status': random.choice(['success', 'partial', 'failed']),
                'error_message': 'None' if random.random() > 0.2 else f"Sync error {random.randint(1000, 9999)}",
                'notes': f"Sync operation {16001+i}"
            })
        return sync_logs


if __name__ == "__main__":
    import os
    from pathlib import Path
    
    # Get the directory of this script (data folder)
    script_dir = Path(__file__).parent
    
    # Load master data from the same folder structure
    master_data_file = script_dir.parent / "01 - Base Data" / "genims_master_data.json"
    
    generator = ERPDataGenerator(str(master_data_file))
    generator.generate_all_data()
    
    # Export to SQL (in same folder as script)
    sql_file = script_dir / "erp_historical_data_inserts.sql"
    generator.to_sql_inserts(str(sql_file))
    
    # Export to JSON (in same folder as script)
    json_file = script_dir / "genims_erp_data.json"
    generator.to_json(str(json_file))
    
    # Validate data consistency
    print("\n" + "="*50)
    print("PERFORMING DATA CONSISTENCY VALIDATION")
    print("="*50)
    
    # Check FK references
    material_ids = set(m['material_id'] for m in generator.materials)
    supplier_ids = set(s['supplier_id'] for s in generator.suppliers)
    
    # Validate sales order lines reference valid products
    invalid_products = 0
    for so_line in generator.sales_order_lines:
        if so_line['product_id'] not in [p['product_id'] for p in generator.products]:
            invalid_products += 1
    
    # Validate purchase orders reference valid suppliers
    invalid_suppliers = 0
    for po in generator.purchase_orders:
        if po['supplier_id'] not in supplier_ids:
            invalid_suppliers += 1
    
    # Validate purchase order lines reference valid materials
    invalid_po_materials = 0
    for po_line in generator.purchase_order_lines:
        if po_line['material_id'] not in material_ids:
            invalid_po_materials += 1
            print(f"Invalid PO line material: {po_line['material_id']}")
    
    print(f"✓ Product references in SO lines: {len(generator.sales_order_lines) - invalid_products}/{len(generator.sales_order_lines)} valid")
    print(f"✓ Material references in PO lines: {len(generator.purchase_order_lines) - invalid_po_materials}/{len(generator.purchase_order_lines)} valid")
    print(f"✓ Supplier references: {len(generator.purchase_orders) - invalid_suppliers}/{len(generator.purchase_orders)} valid")
    
    if invalid_products > 0 or invalid_suppliers > 0 or invalid_po_materials > 0:
        print("⚠️  WARNING: Some FK references are invalid - check data quality")
    else:
        print("✅ All FK references are valid")
    
    print("\n" + "="*80)
    print("ERP Historical Data Generation Complete!")
    print("="*80)
