#!/usr/bin/env python3
"""
GenIMS ERP Historical Data Generator
Generates 90 days of ERP data with referential integrity using registry
"""

import random
import json
from datetime import datetime, timedelta
from typing import List, Dict
import sys
from pathlib import Path

# Add scripts to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))
from generator_helper import get_helper  # type: ignore

# Configuration
DAYS_OF_HISTORY = 90
MATERIALS_TO_CREATE = 200
SUPPLIERS_TO_CREATE = 30
SALES_ORDERS_PER_DAY = (3, 8)
PURCHASE_ORDERS_PER_DAY = (2, 5)

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
                'default_supplier_id': f"SUP-{random.randint(1001, 1030):06d}" if self.suppliers else f"SUP-{random.randint(1001, 1030):06d}",
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
                'default_supplier_id': f"SUP-{random.randint(1001, 1030):06d}" if self.suppliers else None,
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
        """Generate sales orders"""
        print(f"Generating sales orders for {days} days...")
        
        finished_goods = [m for m in self.materials if m['material_type'] == 'finished_good']
        current_date = start_date
        
        # Get valid customer IDs from registry (fallback to master data if empty)
        valid_customer_ids = list(self.helper.get_valid_customer_ids())
        if not valid_customer_ids:
            # Fallback to master data customers
            valid_customer_ids = [c['customer_id'] for c in self.customers]
        
        if not valid_customer_ids:
            raise ValueError("No customer IDs available!")
        
        for day in range(days):
            num_orders = random.randint(*SALES_ORDERS_PER_DAY)
            
            for _ in range(num_orders):
                order_date = current_date + timedelta(hours=random.randint(8, 16))
                
                # Use valid customer ID
                customer_id = random.choice(valid_customer_ids)
                
                # Get valid product IDs for the sales order
                valid_product_ids = list(self.helper.get_valid_product_ids())
                primary_product_id = random.choice(valid_product_ids)
                
                sales_order = {
                    'sales_order_id': self.generate_id('SO', 'sales_order'),
                    'sales_order_number': f"SO-{order_date.strftime('%Y%m%d')}-{self.counters['sales_order']:04d}",
                    'customer_id': customer_id,
                    'product_id': primary_product_id,
                    'order_date': order_date.strftime('%Y-%m-%d'),
                    'order_type': 'standard',
                    'currency': 'INR',
                    'requested_delivery_date': (order_date + timedelta(days=random.randint(7, 30))).strftime('%Y-%m-%d'),
                    'order_status': 'open' if (datetime.now() - order_date).days < 15 else random.choice(['delivered', 'closed']),
                    'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                
                # Calculate totals later
                sales_order['total_net_value'] = 0
                sales_order['total_value'] = 0
                
                self.sales_orders.append(sales_order)
                
                # Add lines (1-5 products per order)
                num_lines = random.randint(1, 5)
                total_value = 0
                
                # FK from registry - GUARANTEED VALID
                valid_product_ids = list(self.helper.get_valid_product_ids())
                
                for line_num in range(1, num_lines + 1):
                    material = random.choice(finished_goods)
                    quantity = random.randint(10, 100)
                    unit_price = material['standard_cost'] * random.uniform(1.2, 1.5)
                    net_price = quantity * unit_price
                    
                    # Use valid product_id from registry
                    product_id = random.choice(valid_product_ids) if valid_product_ids else material.get('product_id')
                    
                    line = {
                        'sales_order_line_id': self.generate_id('SOL', 'sales_order'),
                        'sales_order_id': sales_order['sales_order_id'],
                        'line_number': line_num * 10,
                        'material_id': material['material_id'],
                        'product_id': product_id,
                        'order_quantity': quantity,
                        'unit_of_measure': 'EA',
                        'unit_price': round(unit_price, 2),
                        'net_price': round(net_price, 2),
                        'requested_delivery_date': sales_order['requested_delivery_date'],
                        'line_status': sales_order['order_status'],
                        'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    }
                    
                    self.sales_order_lines.append(line)
                    total_value += net_price
                
                # Update order totals
                sales_order['total_net_value'] = round(total_value, 2)
                sales_order['total_value'] = round(total_value * 1.18, 2)  # With tax
            
            current_date += timedelta(days=1)
        
        print(f"Generated {len(self.sales_orders)} sales orders with {len(self.sales_order_lines)} lines")
    
    def generate_production_orders(self):
        """Generate production orders from sales orders"""
        print("Generating production orders...")
        
        # Available work orders for linking (85% will be linked)
        available_work_orders = list(self.work_orders)
        used_work_orders = []
        
        for so in self.sales_orders:
            # Create production order for each sales order line
            so_lines = [l for l in self.sales_order_lines if l['sales_order_id'] == so['sales_order_id']]
            
            for line in so_lines:
                scheduled_start = datetime.strptime(so['order_date'], '%Y-%m-%d') + timedelta(days=random.randint(1, 5))
                scheduled_end = datetime.strptime(line['requested_delivery_date'], '%Y-%m-%d')
                actual_start = scheduled_start + timedelta(hours=random.randint(0, 48)) if random.random() < 0.8 else None
                actual_end = actual_start + timedelta(days=(scheduled_end - scheduled_start).days) if actual_start else None
                
                order_quantity = line['order_quantity']
                delivered_quantity = int(order_quantity * random.uniform(0.8, 1.0)) if actual_end else 0
                scrap_quantity = int(delivered_quantity * random.uniform(0, 0.05))
                
                # Link to work order if available (85% chance - increased from 80%)
                # Allow reuse of work orders if needed
                work_order_id = None
                if self.work_orders and random.random() < 0.85:
                    # Use from available pool, or cycle back if empty
                    if not available_work_orders:
                        available_work_orders = list(self.work_orders)
                    work_order_id = available_work_orders.pop(0)['work_order_id']
                
                prod_order = {
                    'production_order_id': self.generate_id('PROD', 'prod_order'),
                    'production_order_number': f"PROD-{self.counters['prod_order']:06d}",
                    'material_id': line['material_id'],
                    'plant_id': random.choice(self.factories)['factory_id'],
                    'sales_order_id': so['sales_order_id'],
                    'order_quantity': order_quantity,
                    'order_type': 'production',
                    'basic_start_date': so['order_date'],
                    'basic_end_date': line['requested_delivery_date'],
                    'system_status': 'released' if so['order_status'] != 'open' else 'created',
                    # Missing columns
                    'actual_costs': round(order_quantity * random.uniform(50, 200), 2),
                    'actual_finish_date': actual_end.strftime('%Y-%m-%d') if actual_end else None,
                    'actual_start_date': actual_start.strftime('%Y-%m-%d') if actual_start else None,
                    'bom_id': random.choice([b['bom_id'] for b in self.boms if b['parent_material_id'] == line['material_id']]) if any(b['parent_material_id'] == line['material_id'] for b in self.boms) else None,
                    'closed_at': actual_end.strftime('%Y-%m-%d %H:%M:%S') if actual_end and random.random() < 0.85 else None,
                    'created_by': 'SYSTEM',
                    'delivered_quantity': delivered_quantity,
                    'mrp_element': f"MRP-{self.counters['prod_order']}",
                    'planned_costs': round(order_quantity * random.uniform(40, 180), 2),
                    'priority': random.randint(1, 10),
                    'production_version': 1,
                    'released_at': (datetime.now() - timedelta(days=random.randint(0, 30))).strftime('%Y-%m-%d %H:%M:%S'),
                    'released_by': 'SYSTEM',
                    'routing_id': f"ROUTE-{self.counters['prod_order']}",
                    'scheduled_end_date': scheduled_end.strftime('%Y-%m-%d'),
                    'scheduled_start_date': scheduled_start.strftime('%Y-%m-%d'),
                    'scheduling_type': random.choice(['serial', 'parallel']),
                    'scrap_quantity': scrap_quantity,
                    'settlement_receiver': 'COST_CENTER',
                    'settlement_rule': 'material_ledger',
                    'updated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'user_status': random.choice(['create', 'release', 'confirm', 'complete']),
                    'variance_amount': round(random.uniform(-500, 500), 2),
                    'work_order_id': work_order_id,
                    'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                
                self.production_orders.append(prod_order)
        
        print(f"Generated {len(self.production_orders)} production orders")
    
    def generate_purchase_orders(self, start_date: datetime, days: int):
        """Generate purchase orders"""
        print(f"Generating purchase orders for {days} days...")
        
        purchasable_materials = [m for m in self.materials if m['procurement_type'] in ['buy', 'both']]
        current_date = start_date
        
        for day in range(days):
            num_pos = random.randint(*PURCHASE_ORDERS_PER_DAY)
            
            for _ in range(num_pos):
                supplier = random.choice(self.suppliers)
                po_date = current_date + timedelta(hours=random.randint(9, 15))
                
                po = {
                    'purchase_order_id': self.generate_id('PO', 'po'),
                    'po_number': f"PO-{po_date.strftime('%Y%m%d')}-{self.counters['po']:04d}",
                    'supplier_id': supplier['supplier_id'],
                    'po_date': po_date.strftime('%Y-%m-%d'),
                    'po_type': 'standard',
                    'currency': 'INR',
                    'po_status': 'released' if (datetime.now() - po_date).days > 7 else 'created',
                    'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                
                po['total_value'] = 0
                self.purchase_orders.append(po)
                
                # Add lines
                num_lines = random.randint(2, 6)
                total_value = 0
                
                for line_num in range(1, num_lines + 1):
                    material = random.choice(purchasable_materials)
                    quantity = random.randint(100, 1000)
                    unit_price = material['standard_cost'] * random.uniform(0.9, 1.1)
                    net_price = quantity * unit_price
                    
                    line = {
                        'po_line_id': self.generate_id('POL', 'po'),
                        'purchase_order_id': po['purchase_order_id'],
                        'line_number': line_num * 10,
                        'material_id': material['material_id'],
                        'order_quantity': quantity,
                        'unit_of_measure': material['base_unit_of_measure'],
                        'unit_price': round(unit_price, 2),
                        'net_price': round(net_price, 2),
                        'delivery_date': (po_date + timedelta(days=material['lead_time_days'])).strftime('%Y-%m-%d'),
                        'line_status': po['po_status'],
                        'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    }
                    
                    self.purchase_order_lines.append(line)
                    total_value += net_price
                
                po['total_value'] = round(total_value, 2)
            
            current_date += timedelta(days=1)
        
        print(f"Generated {len(self.purchase_orders)} purchase orders with {len(self.purchase_order_lines)} lines")
    
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
        for i, product in enumerate(self.products[:15]):
            created_dt = (datetime.now() - timedelta(days=random.randint(60, 365)))
            valid_from_dt = (datetime.now() - timedelta(days=random.randint(30, 180)))
            
            boms.append({
                'bom_id': f"BOM-{2001+i}",
                'product_id': product['product_id'],
                'bom_number': f"BOM-{product['product_code']}",
                'version': '1.0',
                'status': 'active',
                'valid_from': valid_from_dt.strftime('%Y-%m-%d'),
                'created_date': created_dt.strftime('%Y-%m-%d'),
                'notes': f"BOM for {product['product_id']}"
            })
        return boms
    
    def _generate_routing(self):
        """Generate routing records"""
        routings = []
        for i in range(10):
            valid_from_dt = (datetime.now() - timedelta(days=random.randint(30, 180)))
            
            routings.append({
                'routing_id': f"ROUTE-{3001+i}",
                'routing_number': f"ROUT-{3001+i}",
                'product_id': random.choice(self.products)['product_id'],
                'routing_code': f"ROUT-{3001+i}",
                'routing_status': 'active',
                'valid_from': valid_from_dt.strftime('%Y-%m-%d'),
                'version': '1.0',
                'notes': f"Manufacturing routing {3001+i}"
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
                'operation_number': op_num,
                'routing_operation_id': f"ROUTOP-{4001+i}",
                'routing_id': f"ROUTE-{3001+random.randint(0, 9)}",
                'operation_sequence': random.randint(10, 100),
                'operation_code': f"OP-{op_num:02d}",
                'operation_description': f"Operation step {random.randint(1, 10)}",
                'estimated_duration_hours': duration_hrs,
                'work_center_id': f"WC-{5001+random.randint(0, 9)}",
                'labor_hours': labor_hrs
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
            
            transactions.append({
                'inventory_transaction_id': f"INVTRANS-{8001+i}",
                'transaction_id': f"INVTR-{random.randint(100001, 999999)}",
                'transaction_code': f"INVTRANS-{8001+i}",
                'transaction_date': trans_dt.isoformat(),
                'document_date': trans_dt.strftime('%Y-%m-%d'),
                'posting_date': trans_dt.strftime('%Y-%m-%d'),
                'movement_type': random.choice(['receipt', 'issue', 'adjustment', 'return']),
                'material_id': random.choice(self.materials)['material_id'],
                'unit_of_measure': 'PCS',
                'warehouse_location': f"LOC-{random.randint(100, 500)}",
                'transaction_type': random.choice(['receipt', 'issue', 'adjustment', 'return']),
                'quantity': qty,
                'reference_document': f"REF-{random.randint(1000, 9999)}",
                'notes': f"Inventory transaction {8001+i}"
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
            
            elements.append({
                'mrp_element_id': f"MRPELEM-{11001+i}",
                'plant_id': f"PLANT-{random.randint(1, 5)}",
                'element_type': random.choice(['demand', 'supply', 'receipt', 'order']),
                'element_date': planned_order_dt.strftime('%Y-%m-%d'),
                'mrp_run_id': f"MRP-RUN-{10001+random.randint(0, 9)}",
                'material_id': random.choice(self.materials)['material_id'],
                'gross_requirement': random.randint(100, 5000),
                'scheduled_receipt': random.randint(0, 4000),
                'available_inventory': random.randint(0, 3000),
                'net_requirement': random.randint(0, 3000),
                'planned_order_quantity': random.randint(100, 3000),
                'planned_order_date': planned_order_dt.strftime('%Y-%m-%d'),
                'lead_time_days': random.randint(1, 30)
            })
        return elements
    
    def _generate_inspection_plans(self):
        """Generate inspection plan records"""
        plans = []
        for i, material in enumerate(self.materials[:20]):
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
            characteristics.append({
                'inspection_characteristic_id': f"INSPCHAR-{13001+i}",
                'inspection_plan_id': f"INSP-{12001+random.randint(0, 19)}",
                'characteristic_name': f"Characteristic {random.randint(1, 50)}",
                'specification_lower': round(random.uniform(0, 50), 2),
                'specification_upper': round(random.uniform(50, 100), 2),
                'measurement_unit': random.choice(['mm', 'kg', 'sec', '%', 'ohms']),
                'inspection_method': random.choice(['visual', 'measurement', 'functional', 'attribute'])
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
            entries.append({
                'gl_entry_id': f"GL-{15001+i}",
                'posting_date': entry_dt.strftime('%Y-%m-%d'),
                'document_date': entry_dt.strftime('%Y-%m-%d'),
                'company_code': f"COMP-{random.randint(1, 5):03d}",
                'gl_account': f"{random.randint(1000, 9999)}",
                'account_description': f"GL Account {random.randint(1000, 9999)}",
                'entry_date': entry_dt.strftime('%Y-%m-%d'),
                'debit_amount': round(random.uniform(0, 10000), 2) if random.random() > 0.5 else 0,
                'credit_amount': round(random.uniform(0, 10000), 2) if random.random() > 0.5 else 0,
                'description': f"GL entry {15001+i}",
                'cost_center_id': f"CC-{14001+random.randint(0, 14)}",
                'reference_document': f"DOC-{random.randint(1000, 9999)}"
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
    
    print("\n" + "="*80)
    print("ERP Historical Data Generation Complete!")
    print("="*80)
