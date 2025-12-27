#!/usr/bin/env python3
"""
GenIMS Unified Data Registry
Single source of truth for all generated data, ID formats, FK relationships, and cross-database references
Ensures: no NULLs in FKs, consistent formats, referential integrity across all 13 databases
"""

import json
import pickle
from pathlib import Path
from typing import Dict, List, Set, Any, Optional, Tuple
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class DataRegistry:
    """
    Unified registry for all GenIMS data generation
    Coordinates ID generation, format consistency, and referential integrity
    """
    
    def __init__(self, root_path: Optional[Path] = None):
        self.root_path = Path(root_path or Path(__file__).parent.parent)
        self.master_dir = self.root_path / "Data Scripts" / "01 - Base Data"
        
        # ID counters for all entities
        self.id_counters = {
            'factory': 0,
            'line': 0,
            'machine': 0,
            'sensor': 0,
            'employee': 0,
            'shift': 0,
            'product': 0,
            'customer': 0,
            'supplier': 0,
            'material': 0,
            'bom': 0,
            'work_order': 0,
            'sales_order': 0,
            'purchase_order': 0,
            'maintenance_event': 0,
            'service_request': 0,
            'quality_check': 0,
        }
        
        # Registered IDs (master data source of truth)
        self.registered_ids = {
            'factory_id': set(),
            'line_id': set(),
            'machine_id': set(),
            'sensor_id': set(),
            'employee_id': set(),
            'shift_id': set(),
            'product_id': set(),
            'customer_id': set(),
            'supplier_id': set(),
            'material_id': set(),
            'bom_id': set(),
            'work_order_id': set(),
            'sales_order_id': set(),
            'purchase_order_id': set(),
            'maintenance_event_id': set(),
            'service_request_id': set(),
            'quality_check_id': set(),
        }
        
        # ID format definitions
        self.id_formats = {
            'factory_id': ('FAC', 6),           # FAC-000001
            'line_id': ('LINE', 6),             # LINE-000001
            'machine_id': ('MCH', 6),           # MCH-000001
            'sensor_id': ('SNS', 6),            # SNS-000001
            'employee_id': ('EMP', 6),          # EMP-000001
            'shift_id': ('SFT', 6),             # SFT-000001
            'product_id': ('PROD', 6),          # PROD-000001
            'customer_id': ('CUST', 6),         # CUST-000001
            'supplier_id': ('SUP', 6),          # SUP-000001
            'material_id': ('MAT', 6),          # MAT-000001
            'bom_id': ('BOM', 6),               # BOM-000001
            'work_order_id': ('WO', 6),         # WO-000001
            'sales_order_id': ('SO', 6),        # SO-000001
            'purchase_order_id': ('PO', 6),     # PO-000001
            'maintenance_event_id': ('MTE', 6), # MTE-000001
            'service_request_id': ('SR', 6),    # SR-000001
            'quality_check_id': ('QC', 6),      # QC-000001
        }
        
        # FK relationships: (source_table, source_col) -> (target_col, required)
        self.fk_mappings = {
            'genims_master_db': {
                'production_lines': {
                    'factory_id': ('factory_id', True),
                },
                'machines': {
                    'line_id': ('line_id', True),
                    'factory_id': ('factory_id', True),
                },
                'sensors': {
                    'machine_id': ('machine_id', True),
                    'line_id': ('line_id', True),
                    'factory_id': ('factory_id', True),
                },
                'employees': {
                    'factory_id': ('factory_id', True),
                    'shift_id': ('shift_id', False),
                },
                'line_product_mapping': {
                    'line_id': ('line_id', True),
                    'product_id': ('product_id', True),
                },
                'customer_product_mapping': {
                    'customer_id': ('customer_id', True),
                    'product_id': ('product_id', True),
                },
            },
            'genims_operations_db': {
                'production_runs': {
                    'machine_id': ('machine_id', True),
                    'product_id': ('product_id', True),
                    'employee_id': ('employee_id', False),
                },
                'maintenance_events': {
                    'machine_id': ('machine_id', True),
                    'employee_id': ('employee_id', False),
                },
                'machine_faults': {
                    'machine_id': ('machine_id', True),
                    'sensor_id': ('sensor_id', False),
                },
            },
            'genims_manufacturing_db': {
                'work_orders': {
                    'product_id': ('product_id', True),
                    'line_id': ('line_id', True),
                    'employee_id': ('employee_id', False),
                },
                'production_batches': {
                    'work_order_id': ('work_order_id', True),
                    'product_id': ('product_id', True),
                },
            },
            'genims_erp_db': {
                'sales_orders': {
                    'customer_id': ('customer_id', True),
                    'product_id': ('product_id', True),
                },
                'purchase_orders': {
                    'supplier_id': ('supplier_id', True),
                },
                'purchase_order_lines': {
                    'material_id': ('material_id', True),
                },
            },
            'genims_maintenance_db': {
                'maintenance_schedules': {
                    'machine_id': ('machine_id', True),
                    'employee_id': ('employee_id', False),
                },
                'maintenance_work_orders': {
                    'maintenance_event_id': ('maintenance_event_id', True),
                    'employee_id': ('employee_id', False),
                },
            },
        }
        
        # Master data cache
        self.master_data_cache = {}
        self.is_finalized = False
    
    def generate_id(self, id_type: str) -> str:
        """Generate next ID for given type"""
        if id_type not in self.id_counters:
            raise ValueError(f"Unknown ID type: {id_type}")
        
        prefix, width = self.id_formats.get(f"{id_type}_id", (id_type.upper(), 6))
        self.id_counters[id_type] += 1
        
        counter_key = f"{id_type}_id"
        return f"{prefix}-{str(self.id_counters[id_type]).zfill(width)}"
    
    def register_master_ids(self, entity_type: str, records: List[Dict]):
        """Register all IDs from master data"""
        if not records:
            return
        
        # Map entity_type to ID column name
        id_column_map = {
            'factory': 'factory_id',
            'line': 'line_id',
            'machine': 'machine_id',
            'sensor': 'sensor_id',
            'employee': 'employee_id',
            'shift': 'shift_id',
            'product': 'product_id',
            'customer': 'customer_id',
            'supplier': 'supplier_id',
            'material': 'material_id',
            'bom': 'bom_id',
            'work_order': 'work_order_id',
            'sales_order': 'sales_order_id',
            'purchase_order': 'purchase_order_id',
            'maintenance_event': 'maintenance_event_id',
            'service_request': 'service_request_id',
            'quality_check': 'quality_check_id',
        }
        
        id_column = id_column_map.get(entity_type)
        if id_column is None:
            raise ValueError(f"Unknown entity type: {entity_type}")
        
        if id_column not in self.registered_ids:
            raise ValueError(f"ID column not in registry: {id_column}")
        
        for record in records:
            id_val = record.get(id_column)
            if id_val is None:
                raise ValueError(f"Record missing {id_column}: {record}")
            
            self.registered_ids[id_column].add(id_val)
    
    def get_registered_ids(self, id_type: str) -> Set[str]:
        """Get all registered IDs of given type"""
        id_column = f"{id_type}_id"
        if id_column not in self.registered_ids:
            raise ValueError(f"Unknown ID type: {id_type}")
        return self.registered_ids[id_column].copy()
    
    def validate_fk(self, db_name: str, table_name: str, column_name: str, value: Any) -> bool:
        """Check if FK value is valid"""
        if value is None:
            return False
        
        # Get the target ID type for this FK
        if db_name not in self.fk_mappings:
            return True  # No mapping defined, skip validation
        
        if table_name not in self.fk_mappings[db_name]:
            return True  # No mappings for this table
        
        if column_name not in self.fk_mappings[db_name][table_name]:
            return True  # No mapping for this column
        
        target_id_type = self.fk_mappings[db_name][table_name][column_name][0]
        target_id_type_base = target_id_type.replace('_id', '')
        
        return value in self.get_registered_ids(target_id_type_base)
    
    def get_random_fk(self, id_type: str) -> Optional[str]:
        """Get random valid FK value"""
        import random
        registered = self.get_registered_ids(id_type)
        if not registered:
            return None
        return random.choice(list(registered))
    
    def ensure_no_null_fk(self, record: Dict, db_name: str, table_name: str) -> Dict:
        """
        Ensure all FK columns have valid values
        If NULL, assign random valid value from registered IDs
        """
        if db_name not in self.fk_mappings:
            return record
        
        if table_name not in self.fk_mappings[db_name]:
            return record
        
        fk_rules = self.fk_mappings[db_name][table_name]
        
        for fk_col, (_, is_required) in fk_rules.items():
            if fk_col not in record or record[fk_col] is None:
                if is_required:
                    # Get target ID type
                    target_id_type = fk_col.replace('_id', '')
                    random_val = self.get_random_fk(target_id_type)
                    
                    if random_val is None:
                        raise ValueError(
                            f"Cannot assign FK {fk_col} in {db_name}.{table_name}: "
                            f"no registered {target_id_type}_id values"
                        )
                    record[fk_col] = random_val
        
        return record
    
    def finalize(self):
        """Finalize registry after master data is registered"""
        self.is_finalized = True
        logger.info(f"Registry finalized with {len(self.registered_ids)} ID types")
        logger.info(f"Total registered IDs: {sum(len(ids) for ids in self.registered_ids.values())}")
    
    def _load_from_json_files(self):
        """Load and register all master data from JSON files.
        
        This replaces pickle persistence with direct JSON loading.
        Registry is always fresh (never stale) since it's rebuilt from source files.
        """
        import json
        
        # Load master data
        master_file = self.master_dir / 'genims_master_data.json'
        if master_file.exists():
            with open(master_file, 'r') as f:
                master_data = json.load(f)
            
            # Register all master data entities
            entity_mapping = {
                'factories': 'factory',
                'production_lines': 'line',
                'machines': 'machine',
                'sensors': 'sensor',
                'employees': 'employee',
                'shifts': 'shift',
                'products': 'product',
                'customers': 'customer'
            }
            
            for json_key, entity_type in entity_mapping.items():
                if json_key in master_data and master_data[json_key]:
                    self.register_master_ids(entity_type, master_data[json_key])
        
        # Load ERP generated data (suppliers, materials, BOMs)
        erp_file = self.root_path / 'Data Scripts' / '04 - ERP & MES Integration' / 'genims_erp_data.json'
        if erp_file.exists():
            try:
                with open(erp_file, 'r') as f:
                    erp_data = json.load(f)
                
                if erp_data.get('suppliers'):
                    self.register_master_ids('supplier', erp_data['suppliers'])
                if erp_data.get('materials'):
                    self.register_master_ids('material', erp_data['materials'])
                
                # BOMs can be under 'boms' or 'bill_of_materials' key
                boms = erp_data.get('boms') or erp_data.get('bill_of_materials', [])
                if boms:
                    self.register_master_ids('bom', boms)
            except Exception as e:
                logger.warning(f"Could not load ERP data for registry: {e}")
        
        self.finalize()
    
    def save(self):
        """Save registry to pickle file (DEPRECATED - kept for backward compatibility)"""
        registry_file = self.master_dir / 'genims_data_registry.pkl'
        with open(registry_file, 'wb') as f:
            pickle.dump(self, f)
        logger.info(f"Registry saved to {registry_file} (deprecated - use JSON files instead)")
    
    @staticmethod
    def load(root_path: Optional[Path] = None) -> 'DataRegistry':
        """Load registry from pickle file"""
        root_path = Path(root_path or Path.cwd())
        master_dir = root_path / "Data Scripts" / "01 - Base Data"
        registry_file = master_dir / 'genims_data_registry.pkl'
        
        if not registry_file.exists():
            raise FileNotFoundError(f"Registry not found: {registry_file}")
        
        with open(registry_file, 'rb') as f:
            return pickle.load(f)
    
    def validate_dataset(self, db_name: str, data: Dict[str, List[Dict]]) -> List[str]:
        """
        Validate entire dataset for FK integrity
        Returns list of validation errors (empty if valid)
        """
        errors = []
        
        if db_name not in self.fk_mappings:
            return errors
        
        db_fk_rules = self.fk_mappings[db_name]
        
        for table_name, fk_rules in db_fk_rules.items():
            if table_name not in data:
                continue
            
            records = data[table_name]
            if not isinstance(records, list):
                continue
            
            for idx, record in enumerate(records):
                for fk_col, (_, is_required) in fk_rules.items():
                    fk_value = record.get(fk_col)
                    
                    if fk_value is None and is_required:
                        errors.append(
                            f"{db_name}.{table_name}[{idx}].{fk_col} is NULL (required FK)"
                        )
                    elif fk_value is not None:
                        target_id_type = fk_col.replace('_id', '')
                        if not self.validate_fk(db_name, table_name, fk_col, fk_value):
                            errors.append(
                                f"{db_name}.{table_name}[{idx}].{fk_col}={fk_value} is invalid "
                                f"(not in registered {target_id_type}_id values)"
                            )
        
        return errors


# Singleton instance
_registry_instance = None


def get_registry(root_path: Optional[Path] = None) -> DataRegistry:
    """Get or create global registry instance.
    
    Registry is always built fresh from master data JSON files to avoid cache invalidation.
    No pickle persistence needed since registry is stateless (derived from data files).
    """
    global _registry_instance
    if _registry_instance is None:
        _registry_instance = DataRegistry(root_path)
        _registry_instance._load_from_json_files()
    return _registry_instance


def reset_registry():
    """Reset registry instance (for testing)"""
    global _registry_instance
    _registry_instance = None
