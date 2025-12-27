#!/usr/bin/env python3
"""
GenIMS Generator Utilities
Shared utility functions for all data generators to ensure consistency and referential integrity
"""

import sys
import random
from pathlib import Path
from typing import List, Dict, Optional, Set

# Add scripts dir to path
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
from data_registry import get_registry


class GeneratorHelper:
    """Helper functions for consistent data generation across all modules"""
    
    def __init__(self, root_path: Optional[Path] = None):
        if root_path is None:
            # Try to infer root path from script location
            root_path = Path(__file__).parent.parent
        self.registry = get_registry(root_path)
        self.master_data = {}
    
    def load_master_data(self):
        """Load master data from JSON for reference"""
        master_dir = Path(__file__).parent / "01 - Base Data"
        master_file = master_dir / "genims_master_data.json"
        
        if master_file.exists():
            import json
            with open(master_file, 'r') as f:
                self.master_data = json.load(f)
            return True
        return False
    
    def get_valid_factory_ids(self) -> Set[str]:
        """Get all valid factory IDs from master"""
        return self.registry.get_registered_ids('factory')
    
    def get_valid_line_ids(self) -> Set[str]:
        """Get all valid line IDs from master"""
        return self.registry.get_registered_ids('line')
    
    def get_valid_machine_ids(self) -> Set[str]:
        """Get all valid machine IDs from master"""
        return self.registry.get_registered_ids('machine')
    
    def get_valid_sensor_ids(self) -> Set[str]:
        """Get all valid sensor IDs from master"""
        return self.registry.get_registered_ids('sensor')
    
    def get_valid_product_ids(self) -> Set[str]:
        """Get all valid product IDs from master"""
        return self.registry.get_registered_ids('product')
    
    def get_valid_customer_ids(self) -> Set[str]:
        """Get all valid customer IDs from master"""
        return self.registry.get_registered_ids('customer')
    
    def get_valid_employee_ids(self) -> Set[str]:
        """Get all valid employee IDs from master"""
        return self.registry.get_registered_ids('employee')
    
    def get_valid_supplier_ids(self) -> Set[str]:
        """Get all valid supplier IDs from master"""
        return self.registry.get_registered_ids('supplier')
    
    def get_random_factory_id(self) -> Optional[str]:
        """Get random valid factory ID"""
        return self.registry.get_random_fk('factory')
    
    def get_random_line_id(self) -> Optional[str]:
        """Get random valid line ID"""
        return self.registry.get_random_fk('line')
    
    def get_random_machine_id(self) -> Optional[str]:
        """Get random valid machine ID"""
        return self.registry.get_random_fk('machine')
    
    def get_random_product_id(self) -> Optional[str]:
        """Get random valid product ID"""
        return self.registry.get_random_fk('product')
    
    def get_random_customer_id(self) -> Optional[str]:
        """Get random valid customer ID"""
        return self.registry.get_random_fk('customer')
    
    def get_random_employee_id(self) -> Optional[str]:
        """Get random valid employee ID"""
        return self.registry.get_random_fk('employee')
    
    def get_random_supplier_id(self) -> Optional[str]:
        """Get random valid supplier ID"""
        return self.registry.get_random_fk('supplier')
    
    def validate_record_fks(self, db_name: str, table_name: str, record: Dict) -> Dict:
        """
        Ensure all FK columns in record have valid values
        If NULL or invalid, assign random valid FK
        Returns the validated record
        """
        return self.registry.ensure_no_null_fk(record, db_name, table_name)
    
    def validate_dataset(self, db_name: str, data: Dict[str, List[Dict]]) -> List[str]:
        """
        Validate entire dataset for FK integrity
        Returns list of errors (empty if valid)
        """
        return self.registry.validate_dataset(db_name, data)


# Singleton instance
_helper_instance = None


def get_helper(root_path: Optional[Path] = None) -> GeneratorHelper:
    """Get or create global helper instance"""
    global _helper_instance
    if _helper_instance is None:
        _helper_instance = GeneratorHelper(root_path)
        _helper_instance.load_master_data()
    return _helper_instance
