"""
GenIMS Operations Module (Integrated)
Uses unified master registry - no independent master data creation
Generates: sensor_data, scada_machine_data, production_runs, maintenance_events, machine_faults, sensor_health
"""

import json
import pickle
import random
from datetime import datetime, timedelta
from typing import Dict, List

class OperationsDataGenerator:
    """Generate operations data using master registry"""
    
    def __init__(self):
        """Load master registry and initialize"""
        from pathlib import Path
        
        project_root = Path(__file__).parent.parent
        master_dir = project_root / "01 - Base Data"
        
        print("Loading master registry...")
        registry_file = master_dir / 'genims_master_registry.pkl'
        master_json_file = master_dir / 'genims_master_data.json'
        
        if not registry_file.exists():
            raise FileNotFoundError(f"Master registry not found: {registry_file}")
        if not master_json_file.exists():
            raise FileNotFoundError(f"Master data JSON not found: {master_json_file}")
        
        with open(registry_file, 'rb') as f:
            self.registry = pickle.load(f)
        
        # Get references from master data
        with open(master_json_file, 'r') as f:
            master_data = json.load(f)
        
        self.factories = {f['factory_id']: f for f in master_data['factories']}
        self.products = {p['product_id']: p for p in master_data['products']}
        self.employees = {e['employee_id']: e for e in master_data['employees']}
        
        # For operations, create production lines, machines, sensors from scratch
        # (since they're not in master data)
        self.production_lines = []
        self.machines = []
        self.sensors = []
        
        # Operational data only (NOT master data)
        self.data = {
            'sensor_data': [],
            'scada_machine_data': [],
            'production_runs': [],
            'maintenance_events': [],
            'machine_faults': [],
            'sensor_health': [],
        }
        
        self.counters = self.registry['id_counters'].copy()
    
    def get_next_id(self, prefix: str) -> str:
        """Get next ID"""
        if prefix not in self.counters:
            self.counters[prefix] = 1
        id_val = self.counters[prefix]
        self.counters[prefix] += 1
        return f"{prefix}-{id_val:06d}"
    
    def generate_production_lines(self):
        """Generate production lines (tied to factories)"""
        print("Generating production lines...")
        
        for factory_id in self.factories.keys():
            num_lines = random.randint(3, 5)
            for _ in range(num_lines):
                line = {
                    'line_id': self.get_next_id('LINE'),
                    'line_name': f"Line {len(self.production_lines)+1}",
                    'factory_id': factory_id,
                    'line_type': random.choice(['assembly', 'machining', 'testing', 'packaging']),
                    'status': 'active',
                    'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                self.production_lines.append(line)
        
        print(f"✓ Generated {len(self.production_lines)} production lines")
    
    def generate_machines(self):
        """Generate machines for each production line"""
        print("Generating machines...")
        
        for line in self.production_lines:
            num_machines = random.randint(5, 12)
            for _ in range(num_machines):
                machine = {
                    'machine_id': self.get_next_id('MACH'),
                    'machine_name': f"Machine {len(self.machines)+1}",
                    'line_id': line['line_id'],
                    'factory_id': line['factory_id'],
                    'machine_type': random.choice(['robot_arm', 'cnc_mill', 'conveyor', 'press']),
                    'status': 'active',
                    'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                self.machines.append(machine)
        
        print(f"✓ Generated {len(self.machines)} machines")
    
    def generate_sensors(self):
        """Generate sensors for each machine"""
        print("Generating sensors...")
        
        sensor_types = ['temperature', 'vibration', 'pressure', 'current', 'voltage', 'flow', 'speed', 'torque']
        
        for machine in self.machines:
            num_sensors = random.randint(3, 8)
            sensor_list = random.sample(sensor_types, min(num_sensors, len(sensor_types)))
            
            for sensor_type in sensor_list:
                sensor = {
                    'sensor_id': self.get_next_id('SEN'),
                    'sensor_name': f"{sensor_type.title()} Sensor",
                    'machine_id': machine['machine_id'],
                    'line_id': machine['line_id'],
                    'factory_id': machine['factory_id'],
                    'sensor_type': sensor_type,
                    'status': 'active',
                    'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                self.sensors.append(sensor)
        
        print(f"✓ Generated {len(self.sensors)} sensors")
    
    def generate_sensor_data(self):
        """Generate sensor measurements"""
        print("Generating sensor data...")
        
        end_time = datetime.now()
        start_time = end_time - timedelta(days=7)
        
        for sensor in self.sensors:
            # ~100 records per sensor
            for _ in range(100):
                timestamp = start_time + timedelta(seconds=random.randint(0, int((end_time-start_time).total_seconds())))
                measurement_value = round(random.uniform(10, 100), 4)
                
                record = {
                    'sensor_id': sensor['sensor_id'],
                    'machine_id': sensor['machine_id'],
                    'line_id': sensor['line_id'],
                    'factory_id': sensor['factory_id'],
                    'timestamp': timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                    'measurement_value': measurement_value,
                    'measurement_unit': random.choice(['°C', 'mm/s', 'bar', 'A', 'V', 'L/min', 'rpm', 'Nm']),
                    'status': random.choice(['normal', 'warning', 'critical', 'fault']),
                    'quality': random.choice(['good', 'uncertain', 'bad', 'out_of_range']),
                    'is_below_warning': random.random() < 0.05,
                    'is_above_warning': random.random() < 0.05,
                    'is_below_critical': random.random() < 0.02,
                    'is_above_critical': random.random() < 0.02,
                    'min_value_1min': round(measurement_value - random.uniform(1, 5), 4),
                    'max_value_1min': round(measurement_value + random.uniform(1, 5), 4),
                    'avg_value_1min': round(measurement_value + random.uniform(-2, 2), 4),
                    'std_dev_1min': round(random.uniform(0.1, 2), 4),
                    'anomaly_score': round(random.uniform(0, 1), 4),
                    'is_anomaly': random.random() < 0.1,
                    'data_source': random.choice(['IoT', 'Edge', 'Gateway']),
                    'protocol': random.choice(['OPC-UA', 'Modbus', 'MQTT']),
                    'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                self.data['sensor_data'].append(record)
        
        print(f"✓ Generated {len(self.data['sensor_data'])} sensor data records")
    
    def generate_scada_data(self):
        """Generate SCADA machine data"""
        print("Generating SCADA data...")
        
        end_time = datetime.now()
        start_time = end_time - timedelta(days=7)
        
        for machine in self.machines:
            # ~100 records per machine
            for _ in range(100):
                timestamp = start_time + timedelta(seconds=random.randint(0, int((end_time-start_time).total_seconds())))
                actual_cycle = round(random.uniform(15, 45), 2)
                availability = round(random.uniform(70, 99), 2)
                
                record = {
                    'machine_id': machine['machine_id'],
                    'line_id': machine['line_id'],
                    'factory_id': machine['factory_id'],
                    'timestamp': timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                    'machine_state': random.choice(['running', 'idle', 'stopped', 'fault', 'maintenance', 'setup']),
                    'operation_mode': random.choice(['auto', 'manual', 'test']),
                    'fault_code': None if random.random() > 0.1 else f"ERR-{random.randint(100, 999)}",
                    'fault_description': None if random.random() > 0.1 else 'Machine fault detected',
                    'parts_produced_cumulative': random.randint(10000, 100000),
                    'parts_produced_shift': random.randint(100, 1000),
                    'parts_rejected_shift': random.randint(0, 50),
                    'target_cycle_time_seconds': 30,
                    'actual_cycle_time_seconds': actual_cycle,
                    'availability_percentage': availability,
                    'performance_percentage': round(random.uniform(75, 95), 2),
                    'quality_percentage': round(random.uniform(90, 99), 2),
                    'oee_percentage': round((availability * random.uniform(0.7, 0.95) * random.uniform(0.8, 0.98)) / 100, 2),
                    'spindle_speed_rpm': random.randint(500, 5000),
                    'feed_rate_mm_min': round(random.uniform(50, 500), 2),
                    'tool_number': random.randint(1, 20),
                    'program_number': f"PROG-{random.randint(1000, 9999)}",
                    'power_consumption_kw': round(random.uniform(5, 50), 2),
                    'energy_consumed_kwh': round(random.uniform(10, 500), 4),
                    'temperature_setpoint_c': round(random.uniform(20, 80), 2),
                    'temperature_actual_c': round(random.uniform(20, 85), 2),
                    'pressure_setpoint_bar': round(random.uniform(5, 10), 2),
                    'pressure_actual_bar': round(random.uniform(5, 11), 2),
                    'downtime_seconds_shift': random.randint(0, 3600),
                    'last_fault_timestamp': timestamp.strftime('%Y-%m-%d %H:%M:%S') if random.random() > 0.9 else None,
                    'uptime_seconds_shift': random.randint(3600, 28800),
                    'active_alarms': random.randint(0, 5),
                    'alarm_codes': ','.join([f"ALM-{random.randint(100, 999)}" for _ in range(random.randint(0, 3))]) or None,
                    'warning_codes': ','.join([f"WRN-{random.randint(100, 999)}" for _ in range(random.randint(0, 2))]) or None,
                    'shift_id': random.choice(['SHIFT-001', 'SHIFT-002', 'SHIFT-003']),
                    'operator_id': random.choice(list(self.employees.keys())),
                    'data_source': 'PLC',
                    'data_quality': random.choice(['good', 'uncertain', 'bad']),
                    'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                self.data['scada_machine_data'].append(record)
        
        print(f"✓ Generated {len(self.data['scada_machine_data'])} SCADA records")
    
    def generate_production_runs(self):
        """Generate production runs"""
        print("Generating production runs...")
        
        product_list = list(self.products.keys())
        
        for machine in self.machines:
            num_runs = random.randint(8, 15)
            for _ in range(num_runs):
                start = datetime.now() - timedelta(days=random.randint(1, 7))
                end = start + timedelta(hours=random.randint(2, 24))
                
                run = {
                    'run_id': self.get_next_id('RUN'),
                    'line_id': machine['line_id'],
                    'factory_id': machine['factory_id'],
                    'product_id': random.choice(product_list),
                    'run_number': random.randint(1000, 9999),
                    'batch_number': f"BATCH-{random.randint(100000, 999999)}",
                    'work_order_number': f"WO-{random.randint(100000, 999999)}",
                    'customer_id': None,
                    'run_start_time': start.strftime('%Y-%m-%d %H:%M:%S'),
                    'run_end_time': end.strftime('%Y-%m-%d %H:%M:%S'),
                    'planned_duration_minutes': random.randint(120, 720),
                    'actual_duration_minutes': int((end - start).total_seconds() / 60),
                    'target_quantity': random.randint(100, 1000),
                    'actual_quantity': random.randint(80, 950),
                    'rejected_quantity': random.randint(0, 50),
                    'scrapped_quantity': random.randint(0, 20),
                    'rework_quantity': random.randint(0, 30),
                    'first_pass_yield_percentage': round(random.uniform(70, 99), 2),
                    'defect_rate_ppm': random.randint(0, 5000),
                    'quality_grade': random.choice(['A', 'B', 'C']),
                    'oee_percentage': round(random.uniform(50, 95), 2),
                    'availability_percentage': round(random.uniform(70, 99), 2),
                    'performance_percentage': round(random.uniform(75, 95), 2),
                    'quality_percentage': round(random.uniform(90, 99), 2),
                    'previous_product_id': None,
                    'changeover_time_minutes': random.randint(5, 60),
                    'shift_id': random.choice(['SHIFT-001', 'SHIFT-002', 'SHIFT-003']),
                    'supervisor_id': random.choice(list(self.employees.keys())),
                    'status': random.choice(['completed', 'in_progress', 'paused', 'aborted']),
                    'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'updated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                self.data['production_runs'].append(run)
        
        print(f"✓ Generated {len(self.data['production_runs'])} production runs")
    
    def generate_machine_faults(self):
        """Generate machine faults"""
        print("Generating machine faults...")
        
        employee_list = list(self.employees.keys())
        
        for machine in self.machines:
            num_faults = random.randint(2, 8)
            for _ in range(num_faults):
                start_time = datetime.now() - timedelta(days=random.randint(0, 7))
                duration_hours = random.uniform(0.5, 24)
                end_time = start_time + timedelta(hours=duration_hours)
                
                fault = {
                    'machine_id': machine['machine_id'],
                    'line_id': machine['line_id'],
                    'factory_id': machine['factory_id'],
                    'fault_code': f"ERR-{random.randint(100, 999)}",
                    'fault_category': random.choice(['mechanical', 'electrical', 'hydraulic', 'pneumatic', 'control', 'quality']),
                    'fault_severity': random.choice(['critical', 'major', 'minor', 'warning']),
                    'fault_description': f"Machine fault detected",
                    'fault_start_time': start_time.strftime('%Y-%m-%d %H:%M:%S'),
                    'fault_end_time': end_time.strftime('%Y-%m-%d %H:%M:%S') if random.random() > 0.2 else None,
                    'fault_duration_seconds': int(duration_hours * 3600) if random.random() > 0.2 else None,
                    'production_loss_units': random.randint(0, 500),
                    'downtime_minutes': int(duration_hours * 60),
                    'estimated_cost_usd': round(random.uniform(100, 10000), 2),
                    'root_cause_category': random.choice(['bearing_failure', 'overheating', 'tool_wear', 'misalignment', 'power_issue', 'sensor_fault']),
                    'root_cause_description': 'Root cause analysis pending',
                    'contributing_sensors': ','.join([s['sensor_id'] for s in random.sample(self.sensors, min(3, len(self.sensors)))]),
                    'resolution_action': 'Maintenance scheduled' if random.random() > 0.5 else 'Repaired on-site',
                    'maintenance_ticket_id': f"MNT-{random.randint(100000, 999999)}",
                    'resolved_by': random.choice(employee_list) if random.random() > 0.2 else None,
                    'detection_method': random.choice(['sensor_threshold', 'predictive_model', 'operator_report', 'automatic']),
                    'predicted_in_advance': random.random() < 0.3,
                    'advance_warning_hours': round(random.uniform(0.5, 48), 2) if random.random() < 0.3 else None,
                    'status': random.choice(['open', 'acknowledged', 'in_progress', 'resolved', 'closed']),
                    'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'updated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                self.data['machine_faults'].append(fault)
        
        print(f"✓ Generated {len(self.data['machine_faults'])} machine faults")
    
    def generate_sensor_health(self):
        """Generate sensor health metrics"""
        print("Generating sensor health metrics...")
        
        end_time = datetime.now()
        start_time = end_time - timedelta(days=7)
        
        for sensor in self.sensors:
            # ~100 records per sensor
            for _ in range(100):
                timestamp = start_time + timedelta(seconds=random.randint(0, int((end_time-start_time).total_seconds())))
                
                record = {
                    'sensor_id': sensor['sensor_id'],
                    'machine_id': sensor['machine_id'],
                    'line_id': sensor['line_id'],
                    'factory_id': sensor['factory_id'],
                    'timestamp': timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                    'health_score': round(random.uniform(50, 100), 2),
                    'drift_percentage': round(random.uniform(-5, 5), 4),
                    'noise_level': round(random.uniform(0.1, 10), 4),
                    'days_since_calibration': random.randint(1, 365),
                    'is_calibration_due': random.random() < 0.1,
                    'calibration_drift_detected': random.random() < 0.05,
                    'packet_loss_percentage': round(random.uniform(0, 5), 2),
                    'average_latency_ms': round(random.uniform(10, 500), 2),
                    'last_communication': timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                    'communication_failures_24h': random.randint(0, 10),
                    'battery_percentage': round(random.uniform(20, 100), 2),
                    'is_low_battery': random.random() < 0.1,
                    'stuck_value_detected': random.random() < 0.02,
                    'erratic_readings_detected': random.random() < 0.05,
                    'out_of_range_readings_24h': random.randint(0, 20),
                    'overall_status': random.choice(['healthy', 'degraded', 'critical', 'failed']),
                    'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                self.data['sensor_health'].append(record)
        
        print(f"✓ Generated {len(self.data['sensor_health'])} sensor health records")
    
    def generate_maintenance_events(self):
        """Generate maintenance events"""
        print("Generating maintenance events...")
        
        employee_list = list(self.employees.keys())
        
        for machine in self.machines:
            num_events = random.randint(3, 8)
            for _ in range(num_events):
                event_start = datetime.now() - timedelta(days=random.randint(0, 30))
                event_duration = timedelta(hours=random.uniform(0.5, 8))
                event_end = event_start + event_duration
                
                event = {
                    'maintenance_id': self.get_next_id('MEVT'),
                    'machine_id': machine['machine_id'],
                    'line_id': machine['line_id'],
                    'factory_id': machine['factory_id'],
                    'event_type': random.choice(['preventive', 'corrective', 'breakdown', 'inspection', 'replacement']),
                    'event_date': event_start.strftime('%Y-%m-%d'),
                    'status': random.choice(['completed', 'in_progress', 'cancelled', 'pending']),
                    'event_description': f"Maintenance event for {machine['machine_name']}",
                    'maintenance_type': random.choice(['routine', 'predictive', 'emergency', 'upgrade']),
                    'parts_used': random.randint(0, 10),
                    'labor_hours': round(random.uniform(0.5, 16), 2),
                    'actual_start': event_start.strftime('%Y-%m-%d %H:%M:%S'),
                    'actual_end': event_end.strftime('%Y-%m-%d %H:%M:%S') if random.random() > 0.1 else None,
                    'completion_status': random.choice(['completed', 'partial', 'failed', 'postponed']),
                    'performed_by': random.choice(employee_list),
                    'work_order_id': f"WO-{random.randint(100000, 999999)}",
                    'estimated_cost': round(random.uniform(100, 5000), 2),
                    'actual_cost': round(random.uniform(100, 5000), 2),
                    'follow_up_required': random.random() < 0.2,
                    'follow_up_date': (event_end + timedelta(days=random.randint(7, 30))).strftime('%Y-%m-%d') if random.random() < 0.2 else None,
                    'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                self.data['maintenance_events'].append(event)
        
        print(f"✓ Generated {len(self.data['maintenance_events'])} maintenance events")
    
    def generate_all(self):
        """Generate all operations data"""
        print("\n" + "=" * 80)
        print("OPERATIONS MODULE DATA GENERATION (Using Master Registry)")
        print("=" * 80)
        
        self.generate_production_lines()
        self.generate_machines()
        self.generate_sensors()
        self.generate_sensor_data()
        self.generate_scada_data()
        self.generate_production_runs()
        self.generate_maintenance_events()
        self.generate_machine_faults()
        self.generate_sensor_health()
        
        total_records = sum(len(v) for v in self.data.values())
        print(f"\n✓ Generated {total_records:,d} records across {len(self.data)} tables")
        
        return self.data
    
    def save(self, filepath='genims_operational_data.json'):
        """Save generated data"""
        from pathlib import Path
        
        # Save in script directory
        if not filepath.startswith('/'):
            output_dir = Path(__file__).parent
            filepath = str(output_dir / filepath)
        
        print(f"\nSaving operational data to {filepath}...")
        with open(filepath, 'w') as f:
            json.dump(self.data, f, indent=2)
        print(f"✓ Saved {filepath}")
        
        # Also save production_lines, machines, sensors to master data
        # (they are master data, not transactional)
        master_dir = Path(__file__).parent.parent / "01 - Base Data"
        master_file = master_dir / 'genims_master_data.json'
        
        print(f"\nUpdating master data with production lines, machines, sensors...")
        with open(master_file, 'r') as f:
            master_data = json.load(f)
        
        # Add or update the master data
        master_data['production_lines'] = self.production_lines
        master_data['machines'] = self.machines
        master_data['sensors'] = self.sensors
        
        with open(master_file, 'w') as f:
            json.dump(master_data, f, indent=2)
        print(f"✓ Updated {master_file}")

def main():
    generator = OperationsDataGenerator()
    generator.generate_all()
    generator.save()

if __name__ == '__main__':
    main()
