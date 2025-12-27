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
        self.customers = master_data['customers']
        
        # Load master data that was already generated
        self.production_lines = master_data.get('production_lines', [])
        self.machines = master_data.get('machines', [])
        self.sensors = master_data.get('sensors', [])
        
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
        sensor_data_id = 1  # Track BIGSERIAL primary key
        
        for sensor in self.sensors:
            # ~100 records per sensor
            for _ in range(100):
                timestamp = start_time + timedelta(seconds=random.randint(0, int((end_time-start_time).total_seconds())))
                measurement_value = round(random.uniform(10, 100), 4)
                
                record = {
                    'sensor_data_id': sensor_data_id,  # BIGSERIAL primary key
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
                sensor_data_id += 1
        
        print(f"✓ Generated {len(self.data['sensor_data'])} sensor data records")
    
    def generate_scada_data(self):
        """Generate SCADA machine data"""
        print("Generating SCADA data...")
        
        end_time = datetime.now()
        start_time = end_time - timedelta(days=7)
        scada_id = 1  # Track BIGSERIAL primary key
        
        # Build machine-indexed fault list for fast lookup
        machine_faults_by_id = {}
        for fault in self.data.get('machine_faults', []):
            mid = fault['machine_id']
            if mid not in machine_faults_by_id:
                machine_faults_by_id[mid] = []
            machine_faults_by_id[mid].append(fault)
        
        for machine in self.machines:
            machine_faults = machine_faults_by_id.get(machine['machine_id'], [])
            
            # ~100 records per machine
            for _ in range(100):
                timestamp = start_time + timedelta(seconds=random.randint(0, int((end_time-start_time).total_seconds())))
                actual_cycle = round(random.uniform(15, 45), 2)
                availability = round(random.uniform(70, 99), 2)
                
                # Determine if machine has faults (50% of records - increased from 45%)
                # Weighted random selection to increase 'fault' and 'maintenance' states
                machine_state = random.choices(
                    ['running', 'idle', 'stopped', 'fault', 'maintenance', 'setup'],
                    weights=[0.20, 0.10, 0.05, 0.50, 0.10, 0.05]  # 50% fault + 10% maintenance = 60%
                )[0]
                has_fault = machine_state in ['fault', 'maintenance']
                
                # Smart fault code/description linking
                fault_code = None
                fault_description = None
                
                # Strategy: Always populate fault code when state is 'fault' or 'maintenance'
                # Prefer linking to existing machine faults (70% if available), else generate
                if has_fault:
                    if machine_faults and random.random() < 0.70:
                        # Try to link to a nearby fault record
                        matching_faults = []
                        for fault in machine_faults:
                            fault_start = datetime.strptime(fault['fault_start_time'], '%Y-%m-%d %H:%M:%S')
                            fault_end_str = fault['fault_end_time']
                            fault_end = datetime.strptime(fault_end_str, '%Y-%m-%d %H:%M:%S') if fault_end_str else fault_start + timedelta(hours=24)
                            # Liberal window: ±4 hours around fault period
                            if fault_start - timedelta(hours=4) <= timestamp <= fault_end + timedelta(hours=4):
                                matching_faults.append(fault)
                        
                        # If found a matching fault, use it
                        if matching_faults:
                            selected_fault = random.choice(matching_faults)
                            fault_code = selected_fault['fault_code']
                            fault_description = selected_fault['fault_description']
                        else:
                            # No matching fault in time window, pick a random one
                            selected_fault = random.choice(machine_faults)
                            fault_code = selected_fault['fault_code']
                            fault_description = selected_fault['fault_description']
                    else:
                        # Generate a new fault code (30% when faults exist, or when no faults at all)
                        fault_code = f"ERR-{random.randint(100, 999)}"
                        fault_description = random.choice([
                            'Bearing temperature high',
                            'Spindle misalignment detected',
                            'Lubrication pressure low',
                            'Motor overcurrent condition',
                            'Tool wear threshold exceeded',
                            'Conveyor jam detected'
                        ])
                
                record = {
                    'scada_id': scada_id,  # BIGSERIAL primary key
                    'machine_id': machine['machine_id'],
                    'line_id': machine['line_id'],
                    'factory_id': machine['factory_id'],
                    'timestamp': timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                    'machine_state': machine_state,
                    'operation_mode': random.choice(['auto', 'manual', 'test']),
                    'fault_code': fault_code,
                    'fault_description': fault_description,
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
                    'last_fault_timestamp': (timestamp - timedelta(hours=random.randint(1, 48))).strftime('%Y-%m-%d %H:%M:%S') if (has_fault or random.random() < 0.50) else None,
                    'uptime_seconds_shift': random.randint(3600, 28800),
                    'active_alarms': random.randint(0, 5),
                    'alarm_codes': ','.join([f"ALM-{random.randint(100, 999)}" for _ in range(random.randint(1, 4))]) if random.random() < 0.75 else None,
                    'warning_codes': ','.join([f"WRN-{random.randint(100, 999)}" for _ in range(random.randint(1, 3))]) if random.random() < 0.70 else None,
                    'shift_id': random.choice(['SHIFT-001', 'SHIFT-002', 'SHIFT-003']),
                    'operator_id': random.choice(list(self.employees.keys())),
                    'data_source': 'PLC',
                    'data_quality': random.choice(['good', 'uncertain', 'bad']),
                    'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                self.data['scada_machine_data'].append(record)
                scada_id += 1
        
        print(f"✓ Generated {len(self.data['scada_machine_data'])} SCADA records")
    
    def generate_production_runs(self):
        """Generate production runs"""
        print("Generating production runs...")
        
        product_list = list(self.products.keys())
        
        for machine in self.machines:
            num_runs = random.randint(8, 15)
            for idx in range(num_runs):
                start = datetime.now() - timedelta(days=random.randint(1, 7))
                end = start + timedelta(hours=random.randint(2, 24))
                
                # Use product_id from product_list (guaranteed to exist from master data)
                selected_product_id = random.choice(product_list)
                # Use previous product from list if available, otherwise use same product
                previous_product_id = random.choice(product_list) if idx > 0 else selected_product_id
                # Use valid customer_id from registry (guaranteed from master data)
                customer_id = random.choice([c['customer_id'] for c in self.customers])
                
                run = {
                    'run_id': self.get_next_id('RUN'),
                    'machine_id': machine['machine_id'],
                    'line_id': machine['line_id'],
                    'factory_id': machine['factory_id'],
                    'product_id': selected_product_id,
                    'run_number': random.randint(1000, 9999),
                    'batch_number': f"BATCH-{random.randint(100000, 999999)}",
                    'work_order_number': f"WO-{random.randint(100000, 999999)}",
                    'customer_id': customer_id,
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
                    'previous_product_id': previous_product_id,
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
        fault_id = 1  # Track BIGSERIAL primary key
        
        for machine in self.machines:
            num_faults = random.randint(2, 8)
            for _ in range(num_faults):
                start_time = datetime.now() - timedelta(days=random.randint(0, 7))
                duration_hours = random.uniform(0.5, 24)
                end_time = start_time + timedelta(hours=duration_hours)
                fault_status = random.choice(['open', 'acknowledged', 'in_progress', 'resolved', 'closed'])
                
                # Higher probability for end_time/duration when resolved or closed
                has_end_time = fault_status in ['resolved', 'closed'] or random.random() < 0.85
                has_resolved_by = fault_status in ['resolved', 'closed'] or random.random() < 0.80
                
                fault = {
                    'fault_id': fault_id,  # BIGSERIAL primary key
                    'machine_id': machine['machine_id'],
                    'line_id': machine['line_id'],
                    'factory_id': machine['factory_id'],
                    'fault_code': f"ERR-{random.randint(100, 999)}",
                    'fault_category': random.choice(['mechanical', 'electrical', 'hydraulic', 'pneumatic', 'control', 'quality']),
                    'fault_severity': random.choice(['critical', 'major', 'minor', 'warning']),
                    'fault_description': f"Machine fault detected",
                    'fault_start_time': start_time.strftime('%Y-%m-%d %H:%M:%S'),
                    'fault_end_time': end_time.strftime('%Y-%m-%d %H:%M:%S') if has_end_time else None,
                    'fault_duration_seconds': int(duration_hours * 3600) if has_end_time else None,
                    'production_loss_units': random.randint(0, 500),
                    'downtime_minutes': int(duration_hours * 60),
                    'estimated_cost_usd': round(random.uniform(100, 10000), 2),
                    'root_cause_category': random.choice(['bearing_failure', 'overheating', 'tool_wear', 'misalignment', 'power_issue', 'sensor_fault']),
                    'root_cause_description': 'Root cause analysis pending',
                    'contributing_sensors': ','.join([s['sensor_id'] for s in random.sample(self.sensors, min(3, len(self.sensors)))]),
                    'resolution_action': 'Maintenance scheduled' if random.random() > 0.5 else 'Repaired on-site',
                    'maintenance_ticket_id': f"MNT-{random.randint(100000, 999999)}",
                    'resolved_by': random.choice(employee_list) if has_resolved_by else None,
                    'detection_method': random.choice(['sensor_threshold', 'predictive_model', 'operator_report', 'automatic']),
                    'predicted_in_advance': random.random() < 0.75,  # 75% have advance warnings
                    'advance_warning_hours': round(random.uniform(1, 72), 2) if random.random() < 0.80 else None,
                    'status': fault_status,
                    'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'updated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                self.data['machine_faults'].append(fault)
                fault_id += 1
        
        print(f"✓ Generated {len(self.data['machine_faults'])} machine faults")
    
    def generate_sensor_health(self):
        """Generate sensor health metrics"""
        print("Generating sensor health metrics...")
        
        end_time = datetime.now()
        start_time = end_time - timedelta(days=7)
        health_id = 1  # Track BIGSERIAL primary key
        
        for sensor in self.sensors:
            # ~100 records per sensor
            for _ in range(100):
                timestamp = start_time + timedelta(seconds=random.randint(0, int((end_time-start_time).total_seconds())))
                
                record = {
                    'health_id': health_id,  # BIGSERIAL primary key
                    'sensor_id': sensor['sensor_id'],
                    'machine_id': sensor['machine_id'],
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
                health_id += 1
        
        print(f"✓ Generated {len(self.data['sensor_health'])} sensor health records")
    
    def generate_maintenance_events(self):
        """Generate maintenance events linked to machine faults"""
        print("Generating maintenance events...")
        
        employee_list = list(self.employees.keys())
        
        # Build lookup of faults by machine for linking
        faults_by_machine = {}
        for fault in self.data['machine_faults']:
            machine_id = fault['machine_id']
            if machine_id not in faults_by_machine:
                faults_by_machine[machine_id] = []
            faults_by_machine[machine_id].append(fault['fault_id'])
        
        for machine in self.machines:
            num_events = random.randint(3, 8)
            for idx, _ in enumerate(range(num_events)):
                event_start = datetime.now() - timedelta(days=random.randint(0, 30))
                event_duration = timedelta(hours=random.uniform(0.5, 8))
                event_end = event_start + event_duration
                
                # Choose maintenance category
                maintenance_category = random.choice(['mechanical', 'electrical', 'hydraulic', 'lubrication', 'calibration'])
                maintenance_type = random.choice(['preventive', 'corrective', 'breakdown', 'inspection', 'replacement'])
                
                # Generate realistic data based on type
                if maintenance_type == 'preventive':
                    parts_cost = round(random.uniform(50, 500), 2)
                    labor_hours = round(random.uniform(1, 4), 2)
                elif maintenance_type == 'breakdown':
                    parts_cost = round(random.uniform(500, 3000), 2)
                    labor_hours = round(random.uniform(4, 16), 2)
                else:
                    parts_cost = round(random.uniform(100, 1500), 2)
                    labor_hours = round(random.uniform(1, 8), 2)
                
                labor_cost = labor_hours * round(random.uniform(75, 150), 2)  # hourly rate
                total_cost = parts_cost + labor_cost
                
                # Link to fault if available - higher probability for corrective/breakdown (increased)
                related_fault_id = None
                if machine['machine_id'] in faults_by_machine:
                    if maintenance_type in ['corrective', 'breakdown']:
                        # 95% for reactive maintenance (up from 85%)
                        if random.random() < 0.95:
                            related_fault_id = random.choice(faults_by_machine[machine['machine_id']])
                    elif maintenance_type == 'replacement':
                        # 75% for replacement (up from 50%)
                        if random.random() < 0.75:
                            related_fault_id = random.choice(faults_by_machine[machine['machine_id']])
                    elif maintenance_type == 'inspection':
                        # 30% for inspection
                        if random.random() < 0.30:
                            related_fault_id = random.choice(faults_by_machine[machine['machine_id']])
                
                event = {
                    'maintenance_id': self.get_next_id('MEVT'),
                    'machine_id': machine['machine_id'],
                    'line_id': machine['line_id'],
                    'factory_id': machine['factory_id'],
                    'maintenance_type': maintenance_type,
                    'maintenance_category': maintenance_category,
                    'priority': random.choice(['critical', 'high', 'medium', 'low']),
                    'scheduled_start': (event_start - timedelta(days=random.randint(1, 7))).strftime('%Y-%m-%d %H:%M:%S'),
                    'actual_start': event_start.strftime('%Y-%m-%d %H:%M:%S'),
                    'actual_end': event_end.strftime('%Y-%m-%d %H:%M:%S') if random.random() > 0.1 else None,
                    'duration_minutes': int(event_duration.total_seconds() / 60),
                    'work_description': f"{maintenance_category.capitalize()} maintenance for {machine['machine_name']}",
                    'parts_replaced': ', '.join([f"PART-{random.randint(1000, 9999)}" for _ in range(random.randint(0, 5))]) or None,
                    'parts_cost_usd': parts_cost,
                    'labor_hours': labor_hours,
                    'labor_cost_usd': labor_cost,
                    'total_cost_usd': total_cost,
                    'technician_id': random.choice(employee_list),
                    'supervisor_id': random.choice(employee_list),
                    'related_fault_id': related_fault_id,  # Now linked to actual faults
                    'completion_status': random.choice(['completed', 'partial', 'deferred', 'cancelled']),
                    'notes': f"Maintenance performed on {event_start.strftime('%Y-%m-%d')}",
                    'follow_up_required': random.random() < 0.2,
                    'next_maintenance_due': (event_end + timedelta(days=random.randint(30, 180))).strftime('%Y-%m-%d'),
                    'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'updated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                self.data['maintenance_events'].append(event)
        
        print(f"✓ Generated {len(self.data['maintenance_events'])} maintenance events")
    
    def generate_all(self):
        """Generate all operations data"""
        print("\n" + "=" * 80)
        print("OPERATIONS MODULE DATA GENERATION (Using Master Registry)")
        print("=" * 80)
        
        print(f"Loaded {len(self.production_lines)} production lines from master data")
        print(f"Loaded {len(self.machines)} machines from master data")
        print(f"Loaded {len(self.sensors)} sensors from master data")
        
        self.generate_sensor_data()
        self.generate_machine_faults()  # Generate faults FIRST for SCADA linking
        self.generate_scada_data()  # SCADA links to faults
        self.generate_production_runs()
        self.generate_maintenance_events()  # Then maintenance can reference faults
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

def main():
    generator = OperationsDataGenerator()
    generator.generate_all()
    generator.save()

if __name__ == '__main__':
    main()
