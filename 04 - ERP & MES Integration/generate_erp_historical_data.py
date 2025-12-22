#!/usr/bin/env python3
"""
GenIMS ERP Historical Data Generator
Generates 90 days of ERP data (materials, BOMs, suppliers, orders, inventory)
"""

import random
import json
from datetime import datetime, timedelta
from typing import List, Dict

# Configuration
DAYS_OF_HISTORY = 90
MATERIALS_TO_CREATE = 200  # Raw materials, components, finished goods
SUPPLIERS_TO_CREATE = 30
SALES_ORDERS_PER_DAY = (3, 8)
PURCHASE_ORDERS_PER_DAY = (2, 5)

class ERPDataGenerator:
    def __init__(self, master_data_file='genims_master_data.json'):
        """Initialize with master data"""
        print("Loading master data...")
        with open(master_data_file, 'r') as f:
            self.master_data = json.load(f)
        
        self.products = self.master_data['products']
        self.customers = self.master_data['customers']
        self.factories = self.master_data['factories']
        
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
    
    def generate_id(self, prefix: str, counter_key: str) -> str:
        id_val = f"{prefix}-{str(self.counters[counter_key]).zfill(6)}"
        self.counters[counter_key] += 1
        return id_val
    
    def generate_all_data(self):
        """Generate all ERP data"""
        print(f"\n{'='*80}")
        print(f"Generating {DAYS_OF_HISTORY} days of ERP historical data")
        print(f"{'='*80}\n")
        
        # Master data first
        self.generate_materials()
        self.generate_suppliers()
        self.generate_boms()
        
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
            material = {
                'material_id': self.generate_id('MAT', 'material'),
                'material_code': f"RM-{self.counters['material']:05d}",
                'material_name': f"{base_name} Grade {random.choice(['A', 'B', 'C'])}",
                'material_type': 'raw_material',
                'material_group': 'RAW',
                'base_unit_of_measure': random.choice(['KG', 'L', 'M']),
                'procurement_type': 'buy',
                'default_supplier_id': None,  # Will assign later
                'lead_time_days': random.randint(7, 30),
                'reorder_point': random.randint(100, 500),
                'safety_stock': random.randint(50, 200),
                'standard_cost': round(random.uniform(10, 200), 2),
                'material_status': 'active',
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
                'standard_cost': round(random.uniform(1, 50), 2),
                'material_status': 'active',
                'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            self.materials.append(material)
        
        # Finished goods (link to products)
        for product in self.products:
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
                'standard_cost': round(random.uniform(100, 2000), 2),
                'material_status': 'active',
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
                'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            self.boms.append(bom)
            
            # Add components (5-10 per BOM)
            num_components = random.randint(5, 10)
            selected_materials = random.sample(raw_materials + components, num_components)
            
            for idx, comp_mat in enumerate(selected_materials, 1):
                component = {
                    'component_id': self.generate_id('BOMC', 'bom'),
                    'bom_id': bom['bom_id'],
                    'item_number': idx * 10,
                    'material_id': comp_mat['material_id'],
                    'component_quantity': round(random.uniform(1, 10), 2),
                    'component_unit': comp_mat['base_unit_of_measure'],
                    'component_scrap_percentage': round(random.uniform(0, 5), 2),
                    'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                self.bom_components.append(component)
        
        print(f"Generated {len(self.boms)} BOMs with {len(self.bom_components)} components")
    
    def generate_sales_orders(self, start_date: datetime, days: int):
        """Generate sales orders"""
        print(f"Generating sales orders for {days} days...")
        
        finished_goods = [m for m in self.materials if m['material_type'] == 'finished_good']
        current_date = start_date
        
        for day in range(days):
            num_orders = random.randint(*SALES_ORDERS_PER_DAY)
            
            for _ in range(num_orders):
                customer = random.choice(self.customers)
                order_date = current_date + timedelta(hours=random.randint(8, 16))
                
                sales_order = {
                    'sales_order_id': self.generate_id('SO', 'sales_order'),
                    'sales_order_number': f"SO-{order_date.strftime('%Y%m%d')}-{self.counters['sales_order']:04d}",
                    'customer_id': customer['customer_id'],
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
                
                for line_num in range(1, num_lines + 1):
                    material = random.choice(finished_goods)
                    quantity = random.randint(10, 100)
                    unit_price = material['standard_cost'] * random.uniform(1.2, 1.5)
                    net_price = quantity * unit_price
                    
                    line = {
                        'sales_order_line_id': self.generate_id('SOL', 'sales_order'),
                        'sales_order_id': sales_order['sales_order_id'],
                        'line_number': line_num * 10,
                        'material_id': material['material_id'],
                        'product_id': material.get('product_id'),
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
        
        for so in self.sales_orders:
            # Create production order for each sales order line
            so_lines = [l for l in self.sales_order_lines if l['sales_order_id'] == so['sales_order_id']]
            
            for line in so_lines:
                prod_order = {
                    'production_order_id': self.generate_id('PROD', 'prod_order'),
                    'production_order_number': f"PROD-{self.counters['prod_order']:06d}",
                    'material_id': line['material_id'],
                    'plant_id': random.choice(self.factories)['factory_id'],
                    'sales_order_id': so['sales_order_id'],
                    'order_quantity': line['order_quantity'],
                    'order_type': 'production',
                    'basic_start_date': so['order_date'],
                    'basic_end_date': line['requested_delivery_date'],
                    'system_status': 'released' if so['order_status'] != 'open' else 'created',
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
        
        data = {
            # Materials & Suppliers
            'materials': self.materials,
            'suppliers': self.suppliers,
            
            # BOM - boms table doesn't exist in schema, only bom_components
            'bom_components': self.bom_components,
            
            # Sales Orders
            'sales_orders': self.sales_orders,
            'sales_order_lines': self.sales_order_lines,
            
            # Production Orders
            'production_orders': self.production_orders,
            
            # Purchase Orders
            'purchase_orders': self.purchase_orders,
            'purchase_order_lines': self.purchase_order_lines,
            
            # Inventory
            'inventory_balances': self.inventory_balances
        }
        
        with open(output_file, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"Data exported to {output_file}")


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
    json_file = script_dir / "erp_historical_data.json"
    generator.to_json(str(json_file))
    
    print("\n" + "="*80)
    print("ERP Historical Data Generation Complete!")
    print("="*80)
