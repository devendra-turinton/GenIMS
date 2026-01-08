"""
GenIMS Synthetic Master Data Generator
Auto Parts Manufacturing - Global Operations
Integrates with unified data registry for format consistency and referential integrity
"""
import random
import string
from datetime import datetime, timedelta
from typing import List, Dict
import json
import sys
from pathlib import Path

# Add scripts dir to path for importing registry
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))
from data_registry import get_registry  # type: ignore

# Configuration
NUM_FACTORIES = 4
LINES_PER_FACTORY = (4, 6)  # min, max
MACHINES_PER_LINE = (8, 15)
SENSORS_PER_MACHINE = (5, 10)
EMPLOYEES_PER_FACTORY = (2000, 4000)

# Master Reference Data
FACTORY_LOCATIONS = [
    {"country": "Japan", "city": "Yokohama", "region": "Kanto", "timezone": "Asia/Tokyo"},
    {"country": "USA", "city": "Detroit", "region": "Michigan", "timezone": "America/Detroit"},
    {"country": "Germany", "city": "Stuttgart", "region": "Baden-Württemberg", "timezone": "Europe/Berlin"},
    {"country": "India", "city": "Chennai", "region": "Tamil Nadu", "timezone": "Asia/Kolkata"}
]

PRODUCT_CATEGORIES = [
    "suspension", "brake", "electrical", "steering", "transmission", 
    "engine_components", "exhaust", "body_parts"
]

LINE_TYPES = ["assembly", "machining", "testing", "painting", "welding"]

MACHINE_TYPES = {
    "assembly": ["robot_arm", "screw_driver", "press_fit", "conveyor", "pick_place"],
    "machining": ["cnc_mill", "cnc_lathe", "drill_press", "grinding_machine", "boring_machine"],
    "testing": ["leak_tester", "torque_tester", "dimension_scanner", "ultrasonic_tester", "x_ray"],
    "painting": ["spray_booth", "powder_coating", "curing_oven", "surface_prep", "inspection_booth"],
    "welding": ["spot_welder", "arc_welder", "laser_welder", "robot_welder", "mig_welder"]
}

SENSOR_TYPES = {
    "temperature": {"unit": "Celsius", "range": (-20, 150), "normal": (20, 85)},
    "vibration": {"unit": "mm/s", "range": (0, 50), "normal": (0, 15)},
    "pressure": {"unit": "bar", "range": (0, 200), "normal": (5, 150)},
    "current": {"unit": "ampere", "range": (0, 500), "normal": (10, 400)},
    "voltage": {"unit": "volt", "range": (0, 480), "normal": (200, 440)},
    "flow": {"unit": "L/min", "range": (0, 1000), "normal": (10, 800)},
    "speed": {"unit": "rpm", "range": (0, 5000), "normal": (100, 4000)},
    "torque": {"unit": "Nm", "range": (0, 1000), "normal": (50, 800)},
    "force": {"unit": "kN", "range": (0, 500), "normal": (10, 400)},
    "displacement": {"unit": "mm", "range": (0, 100), "normal": (0.1, 50)}
}

EMPLOYEE_ROLES = {
    "operator": 0.45,  # 45% operators
    "technician": 0.15,  # 15% technicians
    "quality_inspector": 0.10,  # 10% QC
    "supervisor": 0.08,  # 8% supervisors
    "maintenance_engineer": 0.07,  # 7% maintenance
    "production_engineer": 0.05,  # 5% production engineers
    "planning_coordinator": 0.04,  # 4% planners
    "logistics_coordinator": 0.03,  # 3% logistics
    "manager": 0.02,  # 2% managers
    "quality_engineer": 0.01  # 1% quality engineers
}

DEPARTMENTS = {
    "production": ["operator", "supervisor", "production_engineer"],
    "maintenance": ["technician", "maintenance_engineer"],
    "quality": ["quality_inspector", "quality_engineer"],
    "planning": ["planning_coordinator"],
    "logistics": ["logistics_coordinator"],
    "management": ["manager"]
}

SHIFTS = [
    {"name": "shift_a", "code": "A", "start": "06:00", "end": "14:00", "hours": 8, "days": "mon,tue,wed,thu,fri"},
    {"name": "shift_b", "code": "B", "start": "14:00", "end": "22:00", "hours": 8, "days": "mon,tue,wed,thu,fri"},
    {"name": "shift_c", "code": "C", "start": "22:00", "end": "06:00", "hours": 8, "days": "mon,tue,wed,thu,fri"},
    {"name": "weekend_a", "code": "WA", "start": "06:00", "end": "18:00", "hours": 12, "days": "sat,sun"},
    {"name": "weekend_b", "code": "WB", "start": "18:00", "end": "06:00", "hours": 12, "days": "sat,sun"},
    {"name": "general", "code": "G", "start": "09:00", "end": "18:00", "hours": 9, "days": "mon,tue,wed,thu,fri"}
]

PRODUCTS = [
    # Suspension Components
    {"code": "SUSP-001", "name": "Front Suspension Assembly", "category": "suspension", "type": "assembly", "components": 12, "cycle_time": 450, "weight": 15.5},
    {"code": "SUSP-002", "name": "Rear Suspension Assembly", "category": "suspension", "type": "assembly", "components": 10, "cycle_time": 420, "weight": 14.2},
    {"code": "SUSP-003", "name": "Shock Absorber", "category": "suspension", "type": "component", "components": 5, "cycle_time": 180, "weight": 2.8},
    {"code": "SUSP-004", "name": "Coil Spring", "category": "suspension", "type": "component", "components": 1, "cycle_time": 90, "weight": 1.5},
    {"code": "SUSP-005", "name": "Control Arm", "category": "suspension", "type": "component", "components": 3, "cycle_time": 240, "weight": 3.2},
    
    # Brake Components
    {"code": "BRK-001", "name": "Brake Caliper Assembly", "category": "brake", "type": "assembly", "components": 8, "cycle_time": 300, "weight": 4.5},
    {"code": "BRK-002", "name": "Brake Disc", "category": "brake", "type": "component", "components": 1, "cycle_time": 120, "weight": 5.8},
    {"code": "BRK-003", "name": "Brake Pad Set", "category": "brake", "type": "component", "components": 4, "cycle_time": 60, "weight": 0.8},
    {"code": "BRK-004", "name": "Master Cylinder", "category": "brake", "type": "component", "components": 6, "cycle_time": 210, "weight": 1.2},
    {"code": "BRK-005", "name": "ABS Module", "category": "brake", "type": "assembly", "components": 15, "cycle_time": 540, "weight": 2.5},
    
    # Electrical Components
    {"code": "ELEC-001", "name": "Wiring Harness - Engine", "category": "electrical", "type": "assembly", "components": 25, "cycle_time": 600, "weight": 3.5},
    {"code": "ELEC-002", "name": "Wiring Harness - Dashboard", "category": "electrical", "type": "assembly", "components": 30, "cycle_time": 720, "weight": 2.8},
    {"code": "ELEC-003", "name": "Alternator", "category": "electrical", "type": "component", "components": 8, "cycle_time": 300, "weight": 5.2},
    {"code": "ELEC-004", "name": "Starter Motor", "category": "electrical", "type": "component", "components": 10, "cycle_time": 360, "weight": 4.8},
    {"code": "ELEC-005", "name": "ECU Module", "category": "electrical", "type": "assembly", "components": 20, "cycle_time": 480, "weight": 1.5},
    
    # Steering Components
    {"code": "STRG-001", "name": "Steering Rack Assembly", "category": "steering", "type": "assembly", "components": 12, "cycle_time": 480, "weight": 8.5},
    {"code": "STRG-002", "name": "Power Steering Pump", "category": "steering", "type": "component", "components": 7, "cycle_time": 270, "weight": 3.2},
    {"code": "STRG-003", "name": "Tie Rod End", "category": "steering", "type": "component", "components": 3, "cycle_time": 150, "weight": 0.9},
    
    # Transmission Components
    {"code": "TRAN-001", "name": "Clutch Assembly", "category": "transmission", "type": "assembly", "components": 9, "cycle_time": 420, "weight": 6.5},
    {"code": "TRAN-002", "name": "Gear Set", "category": "transmission", "type": "component", "components": 5, "cycle_time": 300, "weight": 4.2},
    
    # Engine Components
    {"code": "ENG-001", "name": "Engine Block Assembly", "category": "engine_components", "type": "assembly", "components": 45, "cycle_time": 1200, "weight": 85.5},
    {"code": "ENG-002", "name": "Cylinder Head", "category": "engine_components", "type": "component", "components": 16, "cycle_time": 480, "weight": 18.2},
    {"code": "ENG-003", "name": "Piston Assembly", "category": "engine_components", "type": "component", "components": 6, "cycle_time": 240, "weight": 1.8},
    {"code": "ENG-004", "name": "Crankshaft", "category": "engine_components", "type": "component", "components": 1, "cycle_time": 600, "weight": 22.5},
    {"code": "ENG-005", "name": "Camshaft", "category": "engine_components", "type": "component", "components": 1, "cycle_time": 450, "weight": 5.2},
    
    # Body Parts
    {"code": "BDY-001", "name": "Door Assembly - Front", "category": "body_parts", "type": "assembly", "components": 25, "cycle_time": 900, "weight": 45.0},
    {"code": "BDY-002", "name": "Door Assembly - Rear", "category": "body_parts", "type": "assembly", "components": 22, "cycle_time": 850, "weight": 42.5},
    {"code": "BDY-003", "name": "Roof Panel", "category": "body_parts", "type": "component", "components": 1, "cycle_time": 600, "weight": 35.0},
    {"code": "BDY-004", "name": "Floor Pan Assembly", "category": "body_parts", "type": "assembly", "components": 8, "cycle_time": 480, "weight": 55.5},
    {"code": "BDY-005", "name": "Trunk Lid", "category": "body_parts", "type": "component", "components": 1, "cycle_time": 300, "weight": 18.2},
    
    # Exhaust System Components
    {"code": "EXH-001", "name": "Exhaust Manifold", "category": "exhaust", "type": "component", "components": 5, "cycle_time": 360, "weight": 8.5},
    {"code": "EXH-002", "name": "Catalytic Converter", "category": "exhaust", "type": "assembly", "components": 6, "cycle_time": 240, "weight": 5.2},
    {"code": "EXH-003", "name": "Muffler Assembly", "category": "exhaust", "type": "assembly", "components": 4, "cycle_time": 300, "weight": 12.0},
    {"code": "EXH-004", "name": "Exhaust Pipe Section", "category": "exhaust", "type": "component", "components": 1, "cycle_time": 180, "weight": 4.2},
    {"code": "EXH-005", "name": "Oxygen Sensor", "category": "exhaust", "type": "component", "components": 2, "cycle_time": 90, "weight": 0.4},
]

CUSTOMERS = [
    {"code": "TOYO-JP", "name": "Toyota Motor Corporation", "type": "oem", "country": "Japan", "region": "Asia-Pacific", "segment": "automotive_oem"},
    {"code": "HOND-JP", "name": "Honda Motor Co., Ltd.", "type": "oem", "country": "Japan", "region": "Asia-Pacific", "segment": "automotive_oem"},
    {"code": "SUBA-JP", "name": "Subaru Corporation", "type": "oem", "country": "Japan", "region": "Asia-Pacific", "segment": "automotive_oem"},
    {"code": "ISUZ-JP", "name": "Isuzu Motors Ltd.", "type": "oem", "country": "Japan", "region": "Asia-Pacific", "segment": "commercial_vehicle"},
    {"code": "NISS-JP", "name": "Nissan Motor Corporation", "type": "oem", "country": "Japan", "region": "Asia-Pacific", "segment": "automotive_oem"},
    {"code": "FORD-US", "name": "Ford Motor Company", "type": "oem", "country": "USA", "region": "North America", "segment": "automotive_oem"},
    {"code": "GM-US", "name": "General Motors", "type": "oem", "country": "USA", "region": "North America", "segment": "automotive_oem"},
    {"code": "BMW-DE", "name": "BMW Group", "type": "oem", "country": "Germany", "region": "Europe", "segment": "automotive_oem"},
    {"code": "MERC-DE", "name": "Mercedes-Benz Group", "type": "oem", "country": "Germany", "region": "Europe", "segment": "automotive_oem"},
    {"code": "VOLK-DE", "name": "Volkswagen AG", "type": "oem", "country": "Germany", "region": "Europe", "segment": "automotive_oem"},
]


# Machine type to required sensor types mapping
MACHINE_TYPE_SENSORS = {
    "robot_arm": ["temperature", "current", "vibration", "force", "torque"],
    "cnc_mill": ["temperature", "vibration", "force", "pressure", "speed"],
    "cnc_lathe": ["temperature", "vibration", "speed", "torque", "pressure"],
    "drill_press": ["temperature", "vibration", "force", "torque"],
    "press_fit": ["force", "pressure", "displacement", "temperature"],
    "conveyor": ["temperature", "speed", "vibration", "current"],
    "screw_driver": ["torque", "current", "force"],
    "pick_place": ["temperature", "vibration", "force", "current"],
    "spray_booth": ["temperature", "pressure", "flow", "voltage"],
    "powder_coating": ["temperature", "voltage", "current"],
    "curing_oven": ["temperature", "flow", "pressure"],
    "inspection_booth": ["temperature", "voltage", "current"],
    "spot_welder": ["current", "voltage", "force", "temperature"],
    "arc_welder": ["current", "voltage", "temperature"],
    "laser_welder": ["temperature", "voltage"],
    "leak_tester": ["pressure", "flow", "temperature"],
    "torque_tester": ["torque", "force", "temperature"],
    "dimension_scanner": ["displacement", "temperature"],
    "x_ray": ["voltage", "temperature"],
    "ultrasonic_tester": ["temperature", "voltage", "current"],
    "grinding_machine": ["temperature", "vibration", "speed"],
    "boring_machine": ["temperature", "vibration", "speed", "torque"],
    "surface_prep": ["temperature", "pressure", "flow"],
    "mig_welder": ["current", "voltage", "temperature"],
    "robot_welder": ["current", "voltage", "temperature", "force"]
}

# Customer type to product category preferences
CUSTOMER_PRODUCT_PREFERENCES = {
    "oem": ["suspension", "brake", "electrical", "steering", "transmission", "engine_components", "body_parts", "exhaust"],
    "aftermarket": ["suspension", "brake", "electrical"],
    "commercial": ["engine_components", "transmission", "steering", "electrical"]
}

MACHINE_MANUFACTURERS = {
    "robot_arm": ["Fanuc", "Kuka", "ABB", "Yaskawa"],
    "cnc_mill": ["Haas", "Mazak", "DMG Mori", "Makino"],
    "cnc_lathe": ["Okuma", "Doosan", "Mazak", "Hardinge"],
    "press_fit": ["Promess", "Schmidt", "Kistler"],
    "leak_tester": ["ATEQ", "Cosmo Instruments", "InterTech"],
    "default": ["Siemens", "Mitsubishi", "Bosch Rexroth", "Parker"]
}


class DataGenerator:
    def __init__(self):
        # Get registry
        self.registry = get_registry()
        
        # Local ID counters for non-critical IDs (like mapping tables)
        self.local_counters = {
            'mapping': 0
        }
        
        self.factories = []
        self.production_lines = []
        self.machines = []
        self.sensors = []
        self.employees = []
        self.shifts = []
        self.products = []
        self.customers = []
        self.line_product_mapping = []
        self.customer_product_mapping = []
        self.shift_map = {}  # Map factory_id -> {shift_name: shift_id}
        
    def generate_id(self, prefix: str, index: int) -> str:
        """Generate unique ID with prefix using registry"""
        id_type = prefix.lower()
        
        # Use local counter for non-registry IDs (mapping tables)
        if id_type == 'mapping':
            self.local_counters['mapping'] += 1
            return f"MAP-{self.local_counters['mapping']:06d}"
        
        # Use registry for critical IDs
        return self.registry.generate_id(id_type)
    
    def random_date(self, start_year: int, end_year: int) -> str:
        """Generate random date between years"""
        start = datetime(start_year, 1, 1)
        end = datetime(end_year, 12, 31)
        random_date = start + timedelta(days=random.randint(0, (end - start).days))
        return random_date.strftime('%Y-%m-%d')
    
    def generate_factories(self):
        """Generate factory master data"""
        print("Generating factories...")
        for i in range(NUM_FACTORIES):
            location = FACTORY_LOCATIONS[i]
            factory = {
                "factory_id": self.generate_id("factory", i + 1),
                "factory_name": f"{location['city']} Auto Parts Manufacturing Plant",
                "country": location["country"],
                "city": location["city"],
                "region": location["region"],
                "timezone": location["timezone"],
                "total_area_sqm": random.randint(50000, 150000),
                "operational_since": self.random_date(2005, 2018),
                "factory_type": random.choice(["integrated", "assembly", "machining"]),
                "certification": "ISO9001:2015, IATF16949:2016, ISO14001:2015",
                "status": "active",
                "created_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            self.factories.append(factory)
        
        # Register factory IDs with registry
        self.registry.register_master_ids('factory', self.factories)
        print(f"Generated {len(self.factories)} factories")
    
    def generate_production_lines(self):
        """Generate production line master data"""
        print("Generating production lines...")
        line_counter = 1
        for factory in self.factories:
            num_lines = random.randint(*LINES_PER_FACTORY)
            for j in range(num_lines):
                line_type = random.choice(LINE_TYPES)
                product_cat = random.choice(PRODUCT_CATEGORIES)
                
                line = {
                    "line_id": self.generate_id("line", line_counter),
                    "factory_id": factory["factory_id"],  # FK - now guaranteed valid
                    "line_name": f"{product_cat.title()} {line_type.title()} Line {j + 1}",
                    "line_number": j + 1,
                    "product_category": product_cat,
                    "line_type": line_type,
                    "design_capacity_units_per_hour": random.randint(50, 300),
                    "installed_capacity_units_per_hour": random.randint(40, 280),
                    "line_length_meters": round(random.uniform(50, 200), 2),
                    "num_stations": random.randint(8, 25),
                    "automation_level": random.choice(["manual", "semi-automated", "fully-automated"]),
                    "commissioning_date": self.random_date(2010, 2023),
                    "status": "active",
                    "created_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                self.production_lines.append(line)
                line_counter += 1
        
        # Register line IDs with registry
        self.registry.register_master_ids('line', self.production_lines)
        print(f"Generated {len(self.production_lines)} production lines")
    
    def generate_machines(self):
        """Generate machine master data"""
        print("Generating machines...")
        machine_counter = 1
        for line in self.production_lines:
            num_machines = random.randint(*MACHINES_PER_LINE)
            line_type = line["line_type"]
            machine_types = MACHINE_TYPES.get(line_type, MACHINE_TYPES["assembly"])
            
            for k in range(num_machines):
                machine_type = random.choice(machine_types)
                manufacturer = MACHINE_MANUFACTURERS.get(machine_type, MACHINE_MANUFACTURERS["default"])
                
                install_year = int(line["commissioning_date"].split('-')[0])
                current_year = datetime.now().year
                age = current_year - install_year
                
                # Calculate last overhaul year ensuring it's before current year
                overhaul_start_year = max(install_year + 2, 2020)
                overhaul_end_year = min(current_year - 1, 2024)
                if overhaul_start_year > overhaul_end_year:
                    overhaul_start_year = overhaul_end_year - 1
                
                machine = {
                    "machine_id": self.generate_id("machine", machine_counter),
                    "line_id": line["line_id"],  # FK - valid from registry
                    "factory_id": line["factory_id"],  # FK - valid from registry
                    "machine_name": f"{machine_type.replace('_', ' ').title()} - Station {k + 1}",
                    "machine_code": f"{line['line_id'][-3:]}-M{str(k + 1).zfill(2)}",
                    "machine_type": machine_type,
                    "manufacturer": random.choice(manufacturer),
                    "model_number": f"{''.join(random.choices(string.ascii_uppercase, k=3))}-{random.randint(1000, 9999)}",
                    "serial_number": f"SN-{''.join(random.choices(string.ascii_uppercase + string.digits, k=10))}",
                    "installation_date": self.random_date(install_year, install_year + 3),
                    "last_major_overhaul": self.random_date(overhaul_start_year, overhaul_end_year),
                    "design_capacity_units_per_hour": random.randint(30, 200),
                    "power_rating_kw": round(random.uniform(5, 150), 2),
                    "maintenance_schedule": random.choice(["daily", "weekly", "monthly", "quarterly"]),
                    "criticality": random.choices(["critical", "high", "medium", "low"], weights=[0.15, 0.35, 0.35, 0.15])[0],
                    "asset_value_usd": round(random.uniform(50000, 1500000), 2),
                    "expected_life_years": random.randint(15, 25),
                    "current_age_years": round(age + random.uniform(0, 0.9), 2),
                    "status": "active",
                    "created_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                self.machines.append(machine)
                machine_counter += 1
        
        # Register machine IDs with registry
        self.registry.register_master_ids('machine', self.machines)
        print(f"Generated {len(self.machines)} machines")
    
    def generate_sensors(self):
        """Generate sensor master data - machine-type aware assignment"""
        print("Generating sensors...")
        sensor_counter = 1
        
        for machine in self.machines:
            machine_type = machine["machine_type"]
            
            # Get required sensors for this machine type
            required_sensors = MACHINE_TYPE_SENSORS.get(machine_type, ["temperature", "vibration"])
            # Limit to available sensors for this machine
            num_sensors = min(random.randint(*SENSORS_PER_MACHINE), len(SENSOR_TYPES))
            
            # Ensure at least required sensors, then add random ones
            selected_sensors = list(required_sensors[:min(len(required_sensors), num_sensors)])
            remaining_needed = num_sensors - len(selected_sensors)
            if remaining_needed > 0:
                extra_sensors = [s for s in SENSOR_TYPES.keys() if s not in selected_sensors]
                selected_sensors.extend(random.sample(extra_sensors, min(remaining_needed, len(extra_sensors))))
            
            for idx, sensor_type in enumerate(selected_sensors):
                sensor_config = SENSOR_TYPES[sensor_type]
                range_min, range_max = sensor_config["range"]
                normal_min, normal_max = sensor_config["normal"]
                
                # Calculate thresholds
                warning_min = normal_min - (normal_min * 0.1)
                warning_max = normal_max + (normal_max * 0.1)
                critical_min = range_min
                critical_max = range_max
                
                sensor = {
                    "sensor_id": self.generate_id("sensor", sensor_counter),
                    "machine_id": machine["machine_id"],  # FK - valid from registry
                    "line_id": machine["line_id"],  # FK - valid from registry
                    "factory_id": machine["factory_id"],  # FK - valid from registry
                    "sensor_name": f"{sensor_type.replace('_', ' ').title()} Sensor - {machine['machine_code']}-S{idx + 1}",
                    "sensor_code": f"{machine['machine_code']}-S{str(idx + 1).zfill(2)}",
                    "sensor_type": sensor_type,
                    "measurement_unit": sensor_config["unit"],
                    "measurement_range_min": range_min,
                    "measurement_range_max": range_max,
                    "normal_operating_min": normal_min,
                    "normal_operating_max": normal_max,
                    "warning_threshold_min": round(warning_min, 4),
                    "warning_threshold_max": round(warning_max, 4),
                    "critical_threshold_min": critical_min,
                    "critical_threshold_max": critical_max,
                    "sampling_frequency_hz": random.choice([0.1, 0.5, 1, 5, 10, 50, 100]),
                    "data_protocol": random.choice(["OPC-UA", "Modbus-TCP", "MQTT", "REST-API"]),
                    "manufacturer": random.choice(["Honeywell", "Siemens", "Omron", "Schneider", "Rockwell"]),
                    "model_number": f"{''.join(random.choices(string.ascii_uppercase, k=2))}{random.randint(100, 999)}",
                    "calibration_date": self.random_date(2023, 2024),
                    "calibration_frequency_days": random.choice([90, 180, 365]),
                    "accuracy_percentage": round(random.uniform(0.1, 2.0), 2),
                    "status": "active",
                    "created_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                self.sensors.append(sensor)
                sensor_counter += 1
        
        # Register sensor IDs with registry
        self.registry.register_master_ids('sensor', self.sensors)
        print(f"Generated {len(self.sensors)} sensors (machine-type aware)")
    
    def generate_employees(self):
        """Generate employee master data with role distribution per line type"""
        print("Generating employees...")
        employee_counter = 1
        
        first_names = ["Akira", "Yuki", "Haruto", "Sakura", "John", "Mary", "James", "Lisa", 
                      "Michael", "Sarah", "David", "Emma", "Hans", "Anna", "Klaus", "Maria",
                      "Raj", "Priya", "Amit", "Anjali", "Vikram", "Deepa", "Arjun", "Kavya"]
        last_names = ["Tanaka", "Suzuki", "Smith", "Johnson", "Williams", "Brown", "Schmidt", 
                     "Mueller", "Kumar", "Sharma", "Patel", "Singh", "Chen", "Wong", "Lee"]
        
        for factory in self.factories:
            num_employees = random.randint(*EMPLOYEES_PER_FACTORY)
            factory_lines = [line for line in self.production_lines if line["factory_id"] == factory["factory_id"]]
            factory_shifts = [s for s in self.shifts if s["factory_id"] == factory["factory_id"]]
            
            for _ in range(num_employees):
                # Select line and adjust role weights based on line type
                line = random.choice(factory_lines) if factory_lines else None
                line_type = line["line_type"] if line else "assembly"
                
                # Vary employee roles by line type
                role_weights = EMPLOYEE_ROLES.copy()
                if line_type == "testing":
                    # Testing lines need more QC inspectors
                    role_weights["quality_inspector"] = 0.25
                    role_weights["quality_engineer"] = 0.05
                    role_weights["operator"] = 0.30
                elif line_type == "assembly":
                    # Assembly lines need more operators
                    role_weights["operator"] = 0.55
                    role_weights["quality_inspector"] = 0.08
                elif line_type == "machining":
                    # Machining lines need more technicians and engineers
                    role_weights["technician"] = 0.25
                    role_weights["production_engineer"] = 0.08
                    role_weights["operator"] = 0.35
                
                # Normalize weights
                total_weight = sum(role_weights.values())
                role_weights = {k: v/total_weight for k, v in role_weights.items()}
                
                role = random.choices(list(role_weights.keys()), weights=list(role_weights.values()))[0]
                
                # Determine department
                department = None
                for dept, roles in DEPARTMENTS.items():
                    if role in roles:
                        department = dept
                        break
                if not department:
                    department = "production"
                
                # Generate employee data
                first_name = random.choice(first_names)
                last_name = random.choice(last_names)
                experience_years = round(random.uniform(0.5, 25), 2)
                
                # Get shift_id from factory's shifts (FK reference instead of string)
                shift_id = None
                if factory_shifts:
                    if role in ["operator", "technician", "quality_inspector", "supervisor"]:
                        # Shift workers get actual shifts
                        shift_id = random.choice(factory_shifts)["shift_id"]
                    else:
                        # Office workers get general shift
                        general_shifts = [s for s in factory_shifts if s["shift_name"] == "general"]
                        shift_id = general_shifts[0]["shift_id"] if general_shifts else random.choice(factory_shifts)["shift_id"]
                
                skill_level = "trainee" if experience_years < 2 else \
                             "skilled" if experience_years < 5 else \
                             "senior" if experience_years < 10 else "expert"
                
                employee = {
                    "employee_id": self.generate_id("employee", employee_counter),
                    "factory_id": factory["factory_id"],  # FK - valid from registry
                    "line_id": line["line_id"] if line else None,  # FK to production line
                    "shift_id": shift_id,  # FK to shifts (not string)
                    "employee_code": f"{factory['factory_id'][-3:]}-{str(employee_counter).zfill(5)}",
                    "first_name": first_name,
                    "last_name": last_name,
                    "email": f"{first_name.lower()}.{last_name.lower()}{employee_counter}@autoparts.com",
                    "phone": f"+{random.randint(1, 99)}-{''.join(random.choices(string.digits, k=10))}",
                    "role": role,
                    "department": department,
                    "skill_level": skill_level,
                    "hire_date": self.random_date(2010, 2024),
                    "experience_years": experience_years,
                    "certifications": random.choices([
                        "ISO9001 Auditor, Six Sigma Green Belt",
                        "Lean Manufacturing, 5S Practitioner",
                        "CMMS Certified, Predictive Maintenance",
                        "Quality Control Level 2, Statistical Analysis",
                        "Basic Safety Certification"
                    ], weights=[0.25, 0.25, 0.20, 0.20, 0.10])[0],
                    "status": "active",
                    "created_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                self.employees.append(employee)
                employee_counter += 1
        
        # Register employee IDs with registry
        self.registry.register_master_ids('employee', self.employees)
        print(f"Generated {len(self.employees)} employees")
    
    def generate_shifts(self):
        """Generate shift master data"""
        print("Generating shifts...")
        shift_counter = 1
        for factory in self.factories:
            for shift_template in SHIFTS:
                shift = {
                    "shift_id": self.generate_id("shift", shift_counter),
                    "factory_id": factory["factory_id"],  # FK - valid from registry
                    "shift_name": shift_template["name"],
                    "shift_code": shift_template["code"],
                    "start_time": shift_template["start"],
                    "end_time": shift_template["end"],
                    "duration_hours": shift_template["hours"],
                    "shift_type": "regular" if shift_template["code"] in ["A", "B", "C"] else "overtime",
                    "break_duration_minutes": 30 if shift_template["hours"] <= 8 else 60,
                    "days_of_week": shift_template["days"],
                    "status": "active",
                    "created_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                self.shifts.append(shift)
                shift_counter += 1
        
        # Register shift IDs with registry
        self.registry.register_master_ids('shift', self.shifts)
        print(f"Generated {len(self.shifts)} shifts")
    
    def generate_products(self):
        """Generate product master data"""
        print("Generating products...")
        for idx, product in enumerate(PRODUCTS):
            prod = {
                "product_id": self.generate_id("product", idx + 1),
                "product_code": product["code"],
                "product_name": product["name"],
                "product_category": product["category"],
                "product_type": product["type"],
                "description": f"High-quality {product['name'].lower()} for automotive applications",
                "bill_of_material_complexity": "simple" if product["components"] <= 5 else \
                                               "moderate" if product["components"] <= 15 else "complex",
                "number_of_components": product["components"],
                "standard_cycle_time_seconds": product["cycle_time"],
                "target_quality_ppm": random.randint(50, 500),
                "unit_weight_kg": product["weight"],
                "material_type": random.choice(["steel", "aluminum", "composite", "plastic", "copper"]),
                "status": "active",
                "created_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            self.products.append(prod)
        
        # Register product IDs with registry
        self.registry.register_master_ids('product', self.products)
        print(f"Generated {len(self.products)} products")
    
    def generate_customers(self):
        """Generate customer master data"""
        print("Generating customers...")
        for idx, customer in enumerate(CUSTOMERS):
            cust = {
                "customer_id": self.generate_id("customer", idx + 1),
                "customer_code": customer["code"],
                "customer_name": customer["name"],
                "customer_type": customer["type"],
                "country": customer["country"],
                "region": customer["region"],
                "industry_segment": customer["segment"],
                "annual_volume_estimate": random.randint(50000, 500000),
                "quality_rating": random.choice(["excellent", "good"]),
                "payment_terms_days": random.choice([30, 45, 60, 90]),
                "sla_on_time_delivery_percentage": round(random.uniform(95, 99.5), 2),
                "sla_quality_ppm_max": random.randint(100, 1000),
                "status": "active",
                "created_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            self.customers.append(cust)
        
        # Register customer IDs with registry
        self.registry.register_master_ids('customer', self.customers)
        print(f"Generated {len(self.customers)} customers")
    
    def generate_line_product_mapping(self):
        """Generate line-product mapping ensuring 100% line coverage"""
        print("Generating line-product mappings (ensuring full coverage)...")
        mapping_counter = 1
        
        # Ensure every line gets at least one product
        for line in self.production_lines:
            # Match products by product_category
            line_products = [p for p in self.products if p["product_category"] == line["product_category"]]
            
            if not line_products:
                # If no exact category match, assign from any category as fallback
                line_products = random.sample(self.products, min(random.randint(1, 3), len(self.products)))
            else:
                # Ensure 1-3 products per line, all from matching category
                num_products = min(random.randint(1, 3), len(line_products))
                line_products = random.sample(line_products, num_products)
            
            # Create mappings for assigned products
            for idx, product in enumerate(line_products):
                mapping = {
                    "mapping_id": self.generate_id("mapping", mapping_counter),
                    "line_id": line["line_id"],  # FK - valid from registry
                    "product_id": product["product_id"],  # FK - valid from registry
                    "factory_id": line["factory_id"],  # FK - valid from registry
                    "is_primary_line": idx == 0,
                    "standard_cycle_time_seconds": product["standard_cycle_time_seconds"],
                    "setup_time_minutes": random.randint(15, 60),
                    "changeover_time_minutes": random.randint(30, 120),
                    "yield_percentage": round(random.uniform(94, 99.5), 2),
                    "status": "active",
                    "created_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                self.line_product_mapping.append(mapping)
                mapping_counter += 1
        
        print(f"Generated {len(self.line_product_mapping)} line-product mappings (all {len(self.production_lines)} lines covered)")
    
    def generate_customer_product_mapping(self):
        """Generate customer-product mapping with business logic"""
        print("Generating customer-product mappings (business logic based)...")
        mapping_counter = 1
        
        for customer in self.customers:
            # Get preferred product categories based on customer type
            customer_type = customer["customer_type"]
            preferred_categories = CUSTOMER_PRODUCT_PREFERENCES.get(customer_type, ["suspension", "brake", "electrical"])
            
            # Filter products based on customer preferences
            eligible_products = [p for p in self.products if p["product_category"] in preferred_categories]
            
            if not eligible_products:
                # Fallback to random products if no matches
                eligible_products = random.sample(self.products, min(random.randint(3, 8), len(self.products)))
            
            # Select 3-8 products based on customer type
            if customer_type == "oem":
                num_products = random.randint(6, 8)  # OEM orders many types
            else:
                num_products = random.randint(3, 5)  # Aftermarket/Commercial order fewer
            
            selected_products = random.sample(eligible_products, min(num_products, len(eligible_products)))
            
            for product in selected_products:
                mapping = {
                    "mapping_id": self.generate_id("mapping", mapping_counter),
                    "customer_id": customer["customer_id"],  # FK - valid from registry
                    "product_id": product["product_id"],  # FK - valid from registry
                    "is_active": True,
                    "annual_volume": random.randint(10000, 500000) if customer_type == "oem" else random.randint(5000, 100000),
                    "unit_price_usd": round(random.uniform(10, 500), 2),
                    "lead_time_days": random.randint(15, 45) if customer_type == "oem" else random.randint(30, 90),
                    "quality_requirement_ppm": random.randint(50, 500) if customer_type == "oem" else random.randint(200, 1000),
                    "created_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                self.customer_product_mapping.append(mapping)
                mapping_counter += 1
        
        print(f"Generated {len(self.customer_product_mapping)} customer-product mappings (business logic based)")
    
    def generate_all(self):
        """Generate all master data"""
        print("=" * 80)
        print("GenIMS Master Data Generation Started")
        print("=" * 80)
        
        self.generate_factories()
        self.generate_production_lines()
        self.generate_machines()
        self.generate_sensors()
        self.generate_shifts()
        self.generate_employees()
        self.generate_products()
        self.generate_customers()
        self.generate_line_product_mapping()
        self.generate_customer_product_mapping()
        
        print("=" * 80)
        print("Master Data Generation Complete!")
        print("=" * 80)
        self.print_summary()
    
    def print_summary(self):
        """Print generation summary"""
        print(f"\nData Summary:")
        print(f"  Factories: {len(self.factories)}")
        print(f"  Production Lines: {len(self.production_lines)}")
        print(f"  Machines: {len(self.machines)}")
        print(f"  Sensors: {len(self.sensors)}")
        print(f"  Employees: {len(self.employees)}")
        print(f"  Shifts: {len(self.shifts)}")
        print(f"  Products: {len(self.products)}")
        print(f"  Customers: {len(self.customers)}")
        print(f"  Line-Product Mappings: {len(self.line_product_mapping)}")
        print(f"  Customer-Product Mappings: {len(self.customer_product_mapping)}")
    
    def to_sql_inserts(self, output_file: str = "genims_master_data_inserts.sql"):
        """Generate SQL INSERT statements"""
        print(f"\nGenerating SQL INSERT statements to {output_file}...")
        
        with open(output_file, 'w', encoding='utf-8') as f:
            # Header
            f.write("-- GenIMS Master Data INSERT Statements\n")
            f.write("-- Generated: " + datetime.now().strftime('%Y-%m-%d %H:%M:%S') + "\n\n")
            
            # Factories
            f.write("-- FACTORIES\n")
            for factory in self.factories:
                cols = ", ".join(factory.keys())
                vals = ", ".join([f"'{v}'" if v is not None else "NULL" for v in factory.values()])
                f.write(f"INSERT INTO factories ({cols}) VALUES ({vals});\n")
            f.write("\n")
            
            # Production Lines
            f.write("-- PRODUCTION LINES\n")
            for line in self.production_lines:
                cols = ", ".join(line.keys())
                vals = ", ".join([f"'{v}'" if v is not None else "NULL" for v in line.values()])
                f.write(f"INSERT INTO production_lines ({cols}) VALUES ({vals});\n")
            f.write("\n")
            
            # Machines
            f.write("-- MACHINES\n")
            for machine in self.machines:
                cols = ", ".join(machine.keys())
                vals = ", ".join([f"'{v}'" if v is not None else "NULL" for v in machine.values()])
                f.write(f"INSERT INTO machines ({cols}) VALUES ({vals});\n")
            f.write("\n")
            
            # Sensors
            f.write("-- SENSORS\n")
            for sensor in self.sensors:
                cols = ", ".join(sensor.keys())
                vals = ", ".join([f"'{v}'" if v is not None else "NULL" for v in sensor.values()])
                f.write(f"INSERT INTO sensors ({cols}) VALUES ({vals});\n")
            f.write("\n")
            
            # Shifts
            f.write("-- SHIFTS\n")
            for shift in self.shifts:
                cols = ", ".join(shift.keys())
                vals = ", ".join([f"'{v}'" if v is not None else "NULL" for v in shift.values()])
                f.write(f"INSERT INTO shifts ({cols}) VALUES ({vals});\n")
            f.write("\n")
            
            # Employees
            f.write("-- EMPLOYEES\n")
            for employee in self.employees:
                cols = ", ".join(employee.keys())
                vals = ", ".join([f"'{v}'" if v is not None else "NULL" for v in employee.values()])
                f.write(f"INSERT INTO employees ({cols}) VALUES ({vals});\n")
            f.write("\n")
            
            # Products
            f.write("-- PRODUCTS\n")
            for product in self.products:
                cols = ", ".join(product.keys())
                vals = ", ".join([f"'{v}'" if v is not None else "NULL" for v in product.values()])
                f.write(f"INSERT INTO products ({cols}) VALUES ({vals});\n")
            f.write("\n")
            
            # Customers
            f.write("-- CUSTOMERS\n")
            for customer in self.customers:
                cols = ", ".join(customer.keys())
                vals = ", ".join([f"'{v}'" if v is not None else "NULL" for v in customer.values()])
                f.write(f"INSERT INTO customers ({cols}) VALUES ({vals});\n")
            f.write("\n")
            
            # Line Product Mapping
            f.write("-- LINE PRODUCT MAPPING\n")
            for mapping in self.line_product_mapping:
                cols = ", ".join(mapping.keys())
                vals = ", ".join([f"'{v}'" if v is not None and not isinstance(v, bool) else str(v) if isinstance(v, bool) else "NULL" for v in mapping.values()])
                f.write(f"INSERT INTO line_product_mapping ({cols}) VALUES ({vals});\n")
            f.write("\n")
            
            # Customer Product Mapping
            f.write("-- CUSTOMER PRODUCT MAPPING\n")
            for mapping in self.customer_product_mapping:
                cols = ", ".join(mapping.keys())
                vals = ", ".join([f"'{v}'" if v is not None and not isinstance(v, bool) else str(v) if isinstance(v, bool) else "NULL" for v in mapping.values()])
                f.write(f"INSERT INTO customer_product_mapping ({cols}) VALUES ({vals});\n")
            
        print(f"SQL INSERT statements written to {output_file}")
    
    def to_json(self, output_file: str = "genims_master_data.json"):
        """Export all data to JSON"""
        print(f"\nExporting data to JSON: {output_file}...")
        data = {
            "factories": self.factories,
            "production_lines": self.production_lines,
            "machines": self.machines,
            "sensors": self.sensors,
            "employees": self.employees,
            "shifts": self.shifts,
            "products": self.products,
            "customers": self.customers,
            "line_product_mapping": self.line_product_mapping,
            "customer_product_mapping": self.customer_product_mapping
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        
        print(f"Data exported to {output_file}")


if __name__ == "__main__":
    import os
    from pathlib import Path
    
    # Get the directory of this script (data folder)
    script_dir = Path(__file__).parent
    
    # Generate all master data
    generator = DataGenerator()
    generator.generate_all()
    
    # Finalize and save registry
    generator.registry.finalize()
    generator.registry.save()
    
    # Export to SQL (in same folder as script)
    sql_file = script_dir / "genims_master_data_inserts.sql"
    generator.to_sql_inserts(str(sql_file))
    
    # Export to JSON (in same folder as script)
    json_file = script_dir / "genims_master_data.json"
    generator.to_json(str(json_file))
    
    print("\n" + "=" * 80)
    print("Master Data Generation & Registry Complete!")
    print("Files created:")
    print("  1. genims_master_data_inserts.sql - SQL INSERT statements")
    print("  2. genims_master_data.json - JSON export")
    print("  3. genims_data_registry.pkl - Unified data registry (all ID mappings)")
    print("=" * 80)
