"""
GenIMS Operational Data Generator
Generates realistic SCADA and sensor data with fault patterns
"""

import random
import json
import math
from datetime import datetime, timedelta
from typing import List, Dict, Tuple
import numpy as np

# ============================================================================
# CONFIGURATION
# ============================================================================

# Data generation parameters
DAYS_OF_HISTORY = 1  # Generate 1 day of historical data (reduced from 7 for performance)
SCADA_INTERVAL_SECONDS = 120  # SCADA samples every 2 minutes (increased from 60 for performance)
SENSOR_INTERVAL_SECONDS = 120  # Sensor samples every 120 seconds (increased for performance)
MAXIMUM_MACHINES_TO_PROCESS = 50  # Limit machines to first 50 to speed up generation

# Fault injection probability
FAULT_PROBABILITY = 0.05  # 5% of machines will have faults during the period
WARNING_PROBABILITY = 0.15  # 15% will have warning conditions

# ============================================================================
# FAULT PATTERN DEFINITIONS
# ============================================================================

FAULT_PATTERNS = {
    'bearing_failure': {
        'duration_hours': (168, 504),  # 7-21 days
        'progression': 'gradual_then_rapid',
        'affected_sensors': ['vibration', 'temperature'],
        'fault_code': 'BEAR-001',
        'severity': 'critical',
        'category': 'mechanical',
        'description': 'Bearing degradation detected'
    },
    'motor_overheating': {
        'duration_hours': (0.5, 4),  # 30 min to 4 hours
        'progression': 'rapid',
        'affected_sensors': ['temperature', 'current'],
        'fault_code': 'THERM-001',
        'severity': 'major',
        'category': 'electrical',
        'description': 'Motor thermal overload'
    },
    'hydraulic_leak': {
        'duration_hours': (0.1, 72),  # Sudden to gradual
        'progression': 'sudden_or_gradual',
        'affected_sensors': ['pressure', 'flow'],
        'fault_code': 'HYD-001',
        'severity': 'major',
        'category': 'hydraulic',
        'description': 'Hydraulic pressure loss'
    },
    'tool_wear': {
        'duration_hours': (4, 48),  # 4-48 hours
        'progression': 'gradual',
        'affected_sensors': ['vibration', 'current', 'force'],
        'fault_code': 'TOOL-001',
        'severity': 'minor',
        'category': 'mechanical',
        'description': 'Cutting tool wear detected'
    },
    'welding_quality': {
        'duration_hours': (1, 8),  # 1-8 hours
        'progression': 'erratic',
        'affected_sensors': ['current', 'voltage', 'force'],
        'fault_code': 'WELD-001',
        'severity': 'major',
        'category': 'quality',
        'description': 'Weld quality degradation'
    },
    'pneumatic_leak': {
        'duration_hours': (0.5, 24),  # 30 min to 24 hours
        'progression': 'gradual',
        'affected_sensors': ['pressure', 'flow'],
        'fault_code': 'PNEU-001',
        'severity': 'minor',
        'category': 'pneumatic',
        'description': 'Pneumatic pressure loss'
    },
    'coolant_failure': {
        'duration_hours': (0.25, 4),  # 15 min to 4 hours
        'progression': 'rapid',
        'affected_sensors': ['temperature', 'flow'],
        'fault_code': 'COOL-001',
        'severity': 'major',
        'category': 'mechanical',
        'description': 'Coolant system failure'
    },
    'robot_positioning': {
        'duration_hours': (1, 168),  # 1 hour to 7 days
        'progression': 'gradual',
        'affected_sensors': ['displacement', 'current'],
        'fault_code': 'ROBO-001',
        'severity': 'major',
        'category': 'mechanical',
        'description': 'Robot positioning error'
    },
    'electrical_fault': {
        'duration_hours': (0.001, 0.1),  # Milliseconds to minutes
        'progression': 'sudden',
        'affected_sensors': ['voltage', 'current'],
        'fault_code': 'ELEC-001',
        'severity': 'critical',
        'category': 'electrical',
        'description': 'Electrical power fault'
    }
}

# Machine type to fault pattern mapping
MACHINE_FAULT_MAPPING = {
    'cnc_mill': ['bearing_failure', 'tool_wear', 'coolant_failure', 'electrical_fault'],
    'cnc_lathe': ['bearing_failure', 'tool_wear', 'coolant_failure', 'electrical_fault'],
    'grinding_machine': ['bearing_failure', 'coolant_failure', 'electrical_fault'],
    'robot_arm': ['robot_positioning', 'electrical_fault'],
    'robot_welder': ['welding_quality', 'robot_positioning', 'electrical_fault'],
    'spot_welder': ['welding_quality', 'electrical_fault'],
    'arc_welder': ['welding_quality', 'electrical_fault'],
    'laser_welder': ['welding_quality', 'electrical_fault'],
    'mig_welder': ['welding_quality', 'electrical_fault'],
    'press_fit': ['hydraulic_leak', 'electrical_fault'],
    'conveyor': ['motor_overheating', 'electrical_fault'],
    'pick_place': ['pneumatic_leak', 'robot_positioning', 'electrical_fault'],
    'screw_driver': ['pneumatic_leak', 'electrical_fault'],
    'drill_press': ['tool_wear', 'coolant_failure', 'electrical_fault'],
    'boring_machine': ['tool_wear', 'coolant_failure', 'electrical_fault'],
    'leak_tester': ['pneumatic_leak', 'electrical_fault'],
    'torque_tester': ['electrical_fault'],
    'dimension_scanner': ['electrical_fault'],
    'ultrasonic_tester': ['electrical_fault'],
    'x_ray': ['electrical_fault'],
    'spray_booth': ['pneumatic_leak', 'electrical_fault'],
    'powder_coating': ['electrical_fault'],
    'curing_oven': ['motor_overheating', 'electrical_fault'],
    'surface_prep': ['pneumatic_leak', 'electrical_fault'],
    'inspection_booth': ['electrical_fault']
}


class OperationalDataGenerator:
    def __init__(self, master_data_file=None):
        """Initialize with master data"""
        if master_data_file is None:
            from pathlib import Path
            master_data_file = Path(__file__).parent.parent / "01 - Base Data" / "genims_master_data.json"
        
        print("Loading master data...")
        with open(master_data_file, 'r') as f:
            self.master_data = json.load(f)
        
        self.factories = self.master_data['factories']
        self.lines = self.master_data['production_lines']
        self.machines = self.master_data['machines'][:MAXIMUM_MACHINES_TO_PROCESS]  # Limit machines for performance
        machine_ids = {m['machine_id'] for m in self.machines}
        self.sensors = [s for s in self.master_data['sensors'] if s['machine_id'] in machine_ids]
        self.employees = self.master_data['employees']
        self.shifts = self.master_data['shifts']
        self.products = self.master_data['products']
        
        # Operational data storage
        self.scada_data = []
        self.sensor_data = []
        self.faults = []
        self.sensor_health = []
        
        # Fault tracking
        self.active_faults = {}  # machine_id -> fault info
        
        print(f"Loaded: {len(self.machines)} machines, {len(self.sensors)} sensors")
    
    def generate_all_data(self, start_date=None, days=DAYS_OF_HISTORY):
        """Generate all operational data"""
        if start_date is None:
            start_date = datetime.now() - timedelta(days=days)
        
        print(f"\n{'='*80}")
        print(f"Generating {days} days of operational data")
        print(f"Start: {start_date.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*80}\n")
        
        # Assign faults to machines
        self._assign_faults(start_date, days)
        
        # Generate time-series data
        current_time = start_date
        end_time = start_date + timedelta(days=days)
        
        interval = timedelta(seconds=SCADA_INTERVAL_SECONDS)
        iteration = 0
        
        while current_time < end_time:
            if iteration % 100 == 0:
                progress = (current_time - start_date).total_seconds() / (end_time - start_date).total_seconds()
                print(f"Progress: {progress*100:.1f}% - {current_time.strftime('%Y-%m-%d %H:%M:%S')}")
            
            # Generate SCADA data for all machines
            for machine in self.machines:
                self._generate_scada_record(machine, current_time)
            
            # Generate sensor data (higher frequency)
            sensor_ratio = max(1, SENSOR_INTERVAL_SECONDS // SCADA_INTERVAL_SECONDS)
            if iteration % sensor_ratio == 0:
                for sensor in self.sensors:
                    self._generate_sensor_record(sensor, current_time)
            
            current_time += interval
            iteration += 1
        
        print(f"\n{'='*80}")
        print("Data Generation Complete!")
        print(f"{'='*80}")
        self._print_summary()
    
    def _assign_faults(self, start_date, days):
        """Assign fault patterns to machines"""
        print("Assigning fault patterns to machines...")
        
        num_faults = int(len(self.machines) * FAULT_PROBABILITY)
        num_warnings = int(len(self.machines) * WARNING_PROBABILITY)
        
        # Select random machines for faults
        machines_with_faults = random.sample(self.machines, num_faults)
        
        for machine in machines_with_faults:
            machine_type = machine['machine_type']
            
            # Get applicable fault patterns
            applicable_faults = MACHINE_FAULT_MAPPING.get(machine_type, ['electrical_fault'])
            fault_type = random.choice(applicable_faults)
            fault_pattern = FAULT_PATTERNS[fault_type]
            
            # Determine fault timing
            duration_hours = random.uniform(*fault_pattern['duration_hours'])
            fault_end = start_date + timedelta(days=random.uniform(0, days))
            fault_start = fault_end - timedelta(hours=duration_hours)
            
            # Ensure fault is within data generation window
            if fault_start < start_date:
                fault_start = start_date
            
            self.active_faults[machine['machine_id']] = {
                'fault_type': fault_type,
                'pattern': fault_pattern,
                'start_time': fault_start,
                'end_time': fault_end,
                'duration_hours': duration_hours,
                'progression': fault_pattern['progression'],
                'affected_sensors': fault_pattern['affected_sensors']
            }
        
        print(f"Assigned {len(self.active_faults)} fault patterns to machines")
        
        # Print fault summary
        fault_types_count = {}
        for fault_info in self.active_faults.values():
            fault_type = fault_info['fault_type']
            fault_types_count[fault_type] = fault_types_count.get(fault_type, 0) + 1
        
        print("\nFault Type Distribution:")
        for fault_type, count in sorted(fault_types_count.items()):
            print(f"  {fault_type}: {count}")
    
    def _get_shift_info(self, factory_id, timestamp):
        """Get current shift for timestamp"""
        hour = timestamp.hour
        day_of_week = timestamp.strftime('%a').lower()
        
        # Find applicable shift
        factory_shifts = [s for s in self.shifts if s['factory_id'] == factory_id]
        
        for shift in factory_shifts:
            days = shift['days_of_week'].split(',')
            if day_of_week in days:
                start_hour = int(shift['start_time'].split(':')[0])
                end_hour = int(shift['end_time'].split(':')[0])
                
                if start_hour <= hour < end_hour:
                    return shift
        
        # Default to general shift
        return next((s for s in factory_shifts if s['shift_code'] == 'G'), factory_shifts[0])
    
    def _get_fault_factor(self, machine_id, timestamp, sensor_type):
        """Calculate fault factor for machine at timestamp"""
        if machine_id not in self.active_faults:
            return 0.0
        
        fault_info = self.active_faults[machine_id]
        
        # Check if sensor is affected
        if sensor_type not in fault_info['affected_sensors']:
            return 0.0
        
        # Check if we're in the fault window
        if timestamp < fault_info['start_time'] or timestamp > fault_info['end_time']:
            return 0.0
        
        # Calculate progression
        total_duration = (fault_info['end_time'] - fault_info['start_time']).total_seconds()
        elapsed = (timestamp - fault_info['start_time']).total_seconds()
        progress = elapsed / total_duration
        
        progression_type = fault_info['progression']
        
        if progression_type == 'gradual':
            # Linear increase
            return progress
        
        elif progression_type == 'gradual_then_rapid':
            # Slow for 80%, then rapid
            if progress < 0.8:
                return progress * 0.3  # 30% of fault at 80% time
            else:
                return 0.3 + (progress - 0.8) * 3.5  # Rapid to 100%
        
        elif progression_type == 'rapid':
            # Exponential increase
            return math.pow(progress, 0.5)
        
        elif progression_type == 'sudden':
            # Step function
            return 1.0 if progress > 0.9 else 0.0
        
        elif progression_type == 'sudden_or_gradual':
            # 50% chance of each
            if random.random() < 0.5:
                return 1.0 if progress > 0.9 else 0.0
            else:
                return progress
        
        elif progression_type == 'erratic':
            # Random fluctuations
            base = progress * 0.5
            variation = random.uniform(-0.3, 0.5)
            return max(0, min(1, base + variation))
        
        return 0.0
    
    def _generate_scada_record(self, machine, timestamp):
        """Generate SCADA data record for machine"""
        machine_id = machine['machine_id']
        line_id = machine['line_id']
        factory_id = machine['factory_id']
        
        # Get shift information
        shift_info = self._get_shift_info(factory_id, timestamp)
        
        # Get operator for this machine/shift
        line_employees = [e for e in self.employees 
                         if e['line_id'] == line_id and e['shift'] == shift_info['shift_name']]
        operator = random.choice(line_employees) if line_employees else None
        
        # Check for fault
        has_fault = machine_id in self.active_faults
        fault_factor = 0.0
        machine_state = 'running'
        fault_code = None
        fault_description = None
        
        if has_fault:
            fault_info = self.active_faults[machine_id]
            if fault_info['start_time'] <= timestamp <= fault_info['end_time']:
                fault_factor = self._get_fault_factor(machine_id, timestamp, 'general')
                
                if fault_factor > 0.8:
                    machine_state = 'fault'
                    fault_code = fault_info['pattern']['fault_code']
                    fault_description = fault_info['pattern']['description']
                elif fault_factor > 0.5:
                    machine_state = 'running'  # Still running but degraded
        
        # Determine machine state based on time of day
        hour = timestamp.hour
        if machine_state != 'fault':
            if 2 <= hour < 6:  # Night maintenance window
                machine_state = random.choices(['idle', 'maintenance'], weights=[0.7, 0.3])[0]
            elif random.random() < 0.05:  # 5% idle time during day
                machine_state = 'idle'
            elif random.random() < 0.02:  # 2% setup time
                machine_state = 'setup'
        
        # Production metrics
        is_producing = machine_state == 'running'
        
        target_cycle_time = machine.get('design_capacity_units_per_hour', 60)
        target_cycle_seconds = 3600 / target_cycle_time if target_cycle_time > 0 else 60
        
        # Apply fault impact
        if fault_factor > 0:
            cycle_time_impact = 1.0 + (fault_factor * 0.5)  # Up to 50% slower
            actual_cycle_seconds = target_cycle_seconds * cycle_time_impact
        else:
            actual_cycle_seconds = target_cycle_seconds * random.uniform(0.95, 1.05)
        
        parts_this_interval = int((SCADA_INTERVAL_SECONDS / actual_cycle_seconds)) if is_producing else 0
        
        # Quality impact from faults
        if fault_factor > 0.5:
            reject_rate = fault_factor * 0.2  # Up to 20% rejection
            parts_rejected = int(parts_this_interval * reject_rate)
        else:
            parts_rejected = random.choices([0, 1], weights=[0.98, 0.02])[0]
        
        # OEE calculation
        availability = 1.0 if is_producing else 0.0
        if fault_factor > 0:
            availability *= (1.0 - fault_factor * 0.3)  # Reduce by up to 30%
        
        performance = target_cycle_seconds / actual_cycle_seconds if is_producing else 0.0
        quality = 1.0 - (parts_rejected / parts_this_interval) if parts_this_interval > 0 else 1.0
        oee = availability * performance * quality
        
        # Power consumption
        rated_power = machine.get('power_rating_kw', 50)
        if is_producing:
            power_kw = rated_power * random.uniform(0.7, 0.95)
            if fault_factor > 0:
                power_kw *= (1.0 + fault_factor * 0.2)  # Increased power draw
        else:
            power_kw = rated_power * random.uniform(0.05, 0.15)  # Idle power
        
        # Process parameters
        temp_setpoint = random.uniform(40, 70)
        temp_actual = temp_setpoint + random.uniform(-2, 2)
        if fault_factor > 0.3 and machine_id in self.active_faults:
            if 'temperature' in self.active_faults[machine_id]['affected_sensors']:
                temp_actual += fault_factor * 30  # Up to 30°C increase
        
        pressure_setpoint = random.uniform(100, 150)
        pressure_actual = pressure_setpoint + random.uniform(-5, 5)
        if fault_factor > 0.3 and machine_id in self.active_faults:
            if 'pressure' in self.active_faults[machine_id]['affected_sensors']:
                pressure_actual -= fault_factor * 50  # Up to 50 bar drop
        
        record = {
            'machine_id': machine_id,
            'line_id': line_id,
            'factory_id': factory_id,
            'timestamp': timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            'machine_state': machine_state,
            'operation_mode': 'auto',
            'fault_code': fault_code,
            'fault_description': fault_description,
            'parts_produced_cumulative': random.randint(100000, 500000),
            'parts_produced_shift': random.randint(0, 500),
            'parts_rejected_shift': parts_rejected,
            'target_cycle_time_seconds': int(target_cycle_seconds),
            'actual_cycle_time_seconds': round(actual_cycle_seconds, 2),
            'availability_percentage': round(availability * 100, 2),
            'performance_percentage': round(performance * 100, 2),
            'quality_percentage': round(quality * 100, 2),
            'oee_percentage': round(oee * 100, 2),
            'spindle_speed_rpm': random.randint(1000, 4000) if machine['machine_type'].startswith('cnc') else None,
            'feed_rate_mm_min': round(random.uniform(100, 500), 2) if machine['machine_type'].startswith('cnc') else None,
            'tool_number': random.randint(1, 12) if machine['machine_type'].startswith('cnc') else None,
            'program_number': f"NC{random.randint(1000, 9999)}" if machine['machine_type'].startswith('cnc') else None,
            'power_consumption_kw': round(power_kw, 2),
            'energy_consumed_kwh': round(random.uniform(1000, 50000), 4),
            'temperature_setpoint_c': round(temp_setpoint, 2),
            'temperature_actual_c': round(temp_actual, 2),
            'pressure_setpoint_bar': round(pressure_setpoint, 2),
            'pressure_actual_bar': round(pressure_actual, 2),
            'downtime_seconds_shift': random.randint(0, 3600) if not is_producing else 0,
            'last_fault_timestamp': timestamp.strftime('%Y-%m-%d %H:%M:%S') if machine_state == 'fault' else None,
            'uptime_seconds_shift': random.randint(0, 28800) if is_producing else 0,
            'active_alarms': random.randint(0, 3) if fault_factor > 0.5 else 0,
            'alarm_codes': fault_code if fault_code else None,
            'warning_codes': None,
            'shift_id': shift_info['shift_id'],
            'operator_id': operator['employee_id'] if operator else None,
            'data_source': 'PLC',
            'data_quality': 'good',
            'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        self.scada_data.append(record)
        
        # Create fault record if fault just started
        if machine_state == 'fault' and fault_code:
            if not any(f['machine_id'] == machine_id and f['fault_code'] == fault_code 
                      for f in self.faults):
                self._create_fault_record(machine, timestamp, fault_info['pattern'])
    
    def _create_fault_record(self, machine, timestamp, fault_pattern):
        """Create a fault event record"""
        fault_record = {
            'machine_id': machine['machine_id'],
            'line_id': machine['line_id'],
            'factory_id': machine['factory_id'],
            'fault_code': fault_pattern['fault_code'],
            'fault_category': fault_pattern['category'],
            'fault_severity': fault_pattern['severity'],
            'fault_description': fault_pattern['description'],
            'fault_start_time': timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            'fault_end_time': None,
            'fault_duration_seconds': None,
            'production_loss_units': random.randint(10, 200),
            'downtime_minutes': random.randint(30, 480),
            'estimated_cost_usd': round(random.uniform(500, 10000), 2),
            'root_cause_category': fault_pattern['description'],
            'root_cause_description': f"Detailed analysis of {fault_pattern['description']}",
            'contributing_sensors': ','.join([s['sensor_id'] for s in self.sensors 
                                             if s['machine_id'] == machine['machine_id'] 
                                             and s['sensor_type'] in fault_pattern['affected_sensors']][:3]),
            'resolution_action': None,
            'maintenance_ticket_id': None,
            'resolved_by': None,
            'detection_method': 'sensor_threshold',
            'predicted_in_advance': random.random() < 0.7,  # 70% predicted
            'advance_warning_hours': round(random.uniform(1, 48), 2),
            'status': 'open',
            'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'updated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        self.faults.append(fault_record)

    def _generate_sensor_record(self, sensor, timestamp):
        """Generate sensor data record"""
        sensor_id = sensor['sensor_id']
        machine_id = sensor['machine_id']
        line_id = sensor['line_id']
        factory_id = sensor['factory_id']
        sensor_type = sensor['sensor_type']
        
        # Get normal operating range
        normal_min = sensor['normal_operating_min']
        normal_max = sensor['normal_operating_max']
        warning_min = sensor['warning_threshold_min']
        warning_max = sensor['warning_threshold_max']
        critical_min = sensor['critical_threshold_min']
        critical_max = sensor['critical_threshold_max']
        
        # Check for fault factor
        fault_factor = self._get_fault_factor(machine_id, timestamp, sensor_type)
        
        # Generate base value in normal range
        base_value = random.uniform(normal_min, normal_max)
        
        # Apply fault effects
        if fault_factor > 0:
            if sensor_type == 'vibration':
                # Vibration increases with fault
                value = base_value + fault_factor * (critical_max - normal_max)
            elif sensor_type == 'temperature':
                # Temperature increases with fault
                value = base_value + fault_factor * (critical_max - normal_max)
            elif sensor_type == 'pressure':
                # Pressure decreases with fault
                value = base_value - fault_factor * (normal_min - critical_min)
            elif sensor_type == 'current':
                # Current may increase or fluctuate
                value = base_value * (1.0 + fault_factor * 0.5)
            elif sensor_type == 'flow':
                # Flow may increase (leak) or decrease (blockage)
                value = base_value * random.choice([0.7, 1.3]) if fault_factor > 0.5 else base_value
            else:
                value = base_value * (1.0 + random.uniform(-0.2, 0.2) * fault_factor)
        else:
            # Small random variation in normal operation
            value = base_value + random.uniform(-0.05, 0.05) * (normal_max - normal_min)
        
        # Ensure value is within physical limits
        value = max(critical_min, min(critical_max, value))
        
        # Determine status
        if value < critical_min or value > critical_max:
            status = 'critical'
        elif value < warning_min or value > warning_max:
            status = 'warning'
        else:
            status = 'normal'
        
        # Statistical window (simulate rolling calculations)
        window_values = [value + random.uniform(-2, 2) for _ in range(6)]  # Last 1 minute
        min_1min = min(window_values)
        max_1min = max(window_values)
        avg_1min = sum(window_values) / len(window_values)
        std_1min = np.std(window_values)
        
        # Anomaly detection
        anomaly_score = fault_factor * random.uniform(0.7, 1.0) if fault_factor > 0.5 else random.uniform(0, 0.3)
        is_anomaly = anomaly_score > 0.7
        
        record = {
            'sensor_id': sensor_id,
            'machine_id': machine_id,
            'line_id': line_id,
            'factory_id': factory_id,
            'timestamp': timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            'measurement_value': round(value, 4),
            'measurement_unit': sensor['measurement_unit'],
            'status': status,
            'quality': 'good',
            'is_below_warning': value < warning_min,
            'is_above_warning': value > warning_max,
            'is_below_critical': value < critical_min,
            'is_above_critical': value > critical_max,
            'min_value_1min': round(min_1min, 4),
            'max_value_1min': round(max_1min, 4),
            'avg_value_1min': round(avg_1min, 4),
            'std_dev_1min': round(std_1min, 4),
            'anomaly_score': round(anomaly_score, 4),
            'is_anomaly': is_anomaly,
            'data_source': 'IoT',
            'protocol': sensor['data_protocol'],
            'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        self.sensor_data.append(record)
    
    def _print_summary(self):
        """Print generation summary"""
        print(f"\nData Summary:")
        print(f"  SCADA Records: {len(self.scada_data):,}")
        print(f"  Sensor Records: {len(self.sensor_data):,}")
        print(f"  Fault Events: {len(self.faults)}")
        
        # Fault statistics
        if self.faults:
            fault_severities = {}
            for fault in self.faults:
                sev = fault['fault_severity']
                fault_severities[sev] = fault_severities.get(sev, 0) + 1
            
            print(f"\n  Fault Severity Breakdown:")
            for severity, count in sorted(fault_severities.items()):
                print(f"    {severity}: {count}")
    
    def to_sql_inserts(self, output_file='genims_operational_data_inserts.sql'):
        """Generate SQL INSERT statements"""
        print(f"\nGenerating SQL INSERT statements to {output_file}...")
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("-- GenIMS Operational Data INSERT Statements\n")
            f.write("-- Generated: " + datetime.now().strftime('%Y-%m-%d %H:%M:%S') + "\n\n")
            
            # SCADA Data (sample - too large to write all)
            f.write("-- SCADA MACHINE DATA (Sample of first 1000 records)\n")
            for record in self.scada_data[:1000]:
                cols = ", ".join(record.keys())
                vals = ", ".join([f"'{v}'" if v is not None and not isinstance(v, (int, float)) 
                                 else str(v) if v is not None else "NULL" for v in record.values()])
                f.write(f"INSERT INTO scada_machine_data ({cols}) VALUES ({vals});\n")
            
            f.write(f"\n-- NOTE: Full dataset contains {len(self.scada_data):,} SCADA records\n")
            f.write("-- Use CSV or JSON export for complete data\n\n")
            
            # Sensor Data (sample)
            f.write("-- SENSOR DATA (Sample of first 1000 records)\n")
            for record in self.sensor_data[:1000]:
                cols = ", ".join(record.keys())
                vals = ", ".join([f"'{v}'" if v is not None and not isinstance(v, (int, float, bool)) 
                                 else str(v).lower() if isinstance(v, bool)
                                 else str(v) if v is not None else "NULL" for v in record.values()])
                f.write(f"INSERT INTO sensor_data ({cols}) VALUES ({vals});\n")
            
            f.write(f"\n-- NOTE: Full dataset contains {len(self.sensor_data):,} sensor records\n")
            f.write("-- Use CSV or JSON export for complete data\n\n")
            
            # Faults (all records - small dataset)
            f.write("-- MACHINE FAULTS\n")
            for fault in self.faults:
                cols = ", ".join(fault.keys())
                vals = ", ".join([f"'{v}'" if v is not None and not isinstance(v, (int, float, bool)) 
                                 else str(v).lower() if isinstance(v, bool)
                                 else str(v) if v is not None else "NULL" for v in fault.values()])
                f.write(f"INSERT INTO machine_faults ({cols}) VALUES ({vals});\n")
        
        print(f"SQL INSERT statements written to {output_file}")
    
    def to_json(self, output_file='genims_operational_data.json'):
        """Export data to JSON with flat structure matching actual table names from genims_operational_data schema"""
        print(f"\nExporting data to JSON: {output_file}...")
        
        data = {
            # Operational data - only tables that exist in schema
            'sensor_data': self.sensor_data[:100],
            'faults': self.faults
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        
        print(f"Data exported to {output_file}")


if __name__ == "__main__":
    import os
    from pathlib import Path
    
    # Get the directory of this script (data folder)
    script_dir = Path(__file__).parent
    
    # Load master data from the same folder structure
    master_data_file = script_dir.parent / "01 - Base Data" / "genims_master_data.json"
    
    # Generate operational data
    generator = OperationalDataGenerator(str(master_data_file))
    generator.generate_all_data(days=DAYS_OF_HISTORY)  # Use configured days
    
    # Export to SQL (in same folder as script)
    sql_file = script_dir / "genims_operational_data_inserts.sql"
    generator.to_sql_inserts(str(sql_file))
    
    # Export to JSON (in same folder as script)
    json_file = script_dir / "genims_operational_data.json"
    generator.to_json(str(json_file))
    
    # Generate operational data
    generator = OperationalDataGenerator(str(master_data_file))
    generator.generate_all_data(days=DAYS_OF_HISTORY)  # Use configured days
    
    # Export to SQL (in same folder as script)
    sql_file = script_dir / "genims_operational_data_inserts.sql"
    generator.to_sql_inserts(str(sql_file))
    
    # Export to JSON (in same folder as script)
    json_file = script_dir / "genims_operational_data.json"
    generator.to_json(str(json_file))
    
    print("\n" + "="*80)
    print("Data generation complete!")
    print("Files created:")
    print("  1. genims_operational_data_inserts.sql - SQL INSERT statements (sample)")
    print("  2. genims_operational_data.json - JSON export (sample)")
    print("="*80)
