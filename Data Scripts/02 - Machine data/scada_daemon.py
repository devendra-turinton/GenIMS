#!/usr/bin/env python3
"""
GenIMS PLC/SCADA Daemon
Continuous machine operational data streaming daemon
Simulates PLC data aggregation by SCADA and pushes to Kafka and PostgreSQL
"""

import sys
import os
import time
import json
import random
import signal
import logging
from datetime import datetime, timedelta
from typing import Dict, List

# Load environment variables from parent directory config
from dotenv import load_dotenv
env_file = os.path.join(os.path.dirname(__file__), '..', '..', 'scripts', 'config.env')
if os.path.exists(env_file):
    load_dotenv(env_file)

# Optional dependencies
try:
    from kafka import KafkaProducer
    KAFKA_AVAILABLE = True
except ImportError:
    KAFKA_AVAILABLE = False
    print("WARNING: kafka-python not installed. Install with: pip install kafka-python")

try:
    import psycopg2
    from psycopg2.extras import execute_batch
    POSTGRES_AVAILABLE = True
except ImportError:
    POSTGRES_AVAILABLE = False
    print("WARNING: psycopg2 not installed. Install with: pip install psycopg2-binary")

# ============================================================================
# CONFIGURATION - Environment Variables with Defaults
# ============================================================================

# PostgreSQL configuration (Azure Cloud)
PG_HOST = os.getenv('POSTGRES_HOST', 'insights-db.postgres.database.azure.com')
PG_PORT = int(os.getenv('POSTGRES_PORT', '5432'))
PG_DATABASE = os.getenv('DB_OPERATIONS', 'genims_operations_db')
PG_USER = os.getenv('POSTGRES_USER', 'turintonadmin')
PG_PASSWORD = os.getenv('POSTGRES_PASSWORD', 'Passw0rd123!')
PG_SSL_MODE = os.getenv('PG_SSL_MODE', 'require')
PG_SSL_MODE = os.getenv('PG_SSL_MODE', 'require')  # Azure requires SSL

# Streaming configuration
SCADA_SAMPLING_INTERVAL = int(os.getenv('SCADA_SAMPLING_INTERVAL', '60'))
BATCH_SIZE = int(os.getenv('BATCH_SIZE', '50'))
KAFKA_TOPIC = os.getenv('KAFKA_TOPIC', 'genims.scada.data')
KAFKA_BOOTSTRAP_SERVERS = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092').split(',')

# Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('SCADADaemon')

# ============================================================================
# GLOBAL STATE
# ============================================================================

running = True
kafka_producer = None
pg_connection = None
scada_batch = []
stats = {
    'records_generated': 0,
    'kafka_sent': 0,
    'postgres_inserted': 0,
    'errors': 0,
    'start_time': datetime.now()
}


def signal_handler(sig, frame):
    """Handle shutdown signals gracefully"""
    global running
    logger.info("Shutdown signal received. Stopping daemon...")
    running = False


signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)


class MachineSimulator:
    """Simulates realistic machine operational behavior"""
    
    MACHINE_STATES = ['running', 'idle', 'stopped', 'fault', 'maintenance', 'setup']
    
    def __init__(self, machine: Dict, operators: List[Dict], shifts: List[Dict]):
        self.machine = machine
        self.machine_id = machine['machine_id']
        self.line_id = machine['line_id']
        self.factory_id = machine['factory_id']
        self.machine_type = machine['machine_type']
        self.operators = operators
        self.shifts = shifts
        
        # State
        self.current_state = 'running'
        self.parts_produced_cumulative = random.randint(100000, 500000)
        self.parts_produced_shift = 0
        self.parts_rejected_shift = 0
        self.downtime_seconds_shift = 0
        self.uptime_seconds_shift = 0
        self.current_tool = random.randint(1, 12)
        self.tool_usage_cycles = 0
        
        # Fault simulation
        self.fault_active = False
        self.fault_start_time = None
        self.fault_duration = 0
        self.fault_code = None
        self.fault_description = None
        
        # Performance baseline
        self.target_cycle_time = 3600 / machine.get('design_capacity_units_per_hour', 60)
        self.rated_power = machine.get('power_rating_kw', 50)
    
    def inject_fault(self, fault_code: str, fault_description: str, duration_seconds=300):
        """Inject a fault condition"""
        self.fault_active = True
        self.fault_start_time = time.time()
        self.fault_duration = duration_seconds
        self.fault_code = fault_code
        self.fault_description = fault_description
        self.current_state = 'fault'
        logger.info(f"Fault injected: {self.machine_id} - {fault_code}: {fault_description}")
    
    def clear_fault(self):
        """Clear fault condition"""
        if self.fault_active:
            self.fault_active = False
            self.current_state = 'running'
            logger.info(f"Fault cleared: {self.machine_id}")
    
    def get_current_shift(self) -> Dict:
        """Get current shift based on time"""
        current_hour = datetime.now().hour
        day_of_week = datetime.now().strftime('%a').lower()
        
        for shift in self.shifts:
            if self.factory_id != shift['factory_id']:
                continue
            
            days = shift['days_of_week'].split(',')
            if day_of_week not in days:
                continue
            
            start_hour = int(shift['start_time'].split(':')[0])
            end_hour = int(shift['end_time'].split(':')[0])
            
            if start_hour <= current_hour < end_hour:
                return shift
        
        # Default
        return next((s for s in self.shifts if s['shift_code'] == 'G'), self.shifts[0])
    
    def get_operator(self, shift_id: str) -> Dict:
        """Get operator for current shift"""
        shift_operators = [op for op in self.operators 
                          if op['line_id'] == self.line_id]
        return random.choice(shift_operators) if shift_operators else None
    
    def determine_state(self) -> str:
        """Determine machine state based on time and conditions"""
        if self.fault_active:
            elapsed = time.time() - self.fault_start_time
            if elapsed > self.fault_duration:
                self.clear_fault()
                return 'running'
            return 'fault'
        
        hour = datetime.now().hour
        
        # Night maintenance window (2-6 AM)
        if 2 <= hour < 6:
            return random.choices(['idle', 'maintenance'], weights=[0.7, 0.3])[0]
        
        # Normal operations - mostly running
        return random.choices(
            ['running', 'idle', 'setup'],
            weights=[0.88, 0.10, 0.02]
        )[0]
    
    def get_next_reading(self) -> Dict:
        """Generate next SCADA reading"""
        # Update state
        self.current_state = self.determine_state()
        
        # Get shift and operator
        shift = self.get_current_shift()
        operator = self.get_operator(shift['shift_id'])
        
        # Production metrics
        is_producing = self.current_state == 'running'
        
        if is_producing:
            # Calculate cycle time (with some variation)
            actual_cycle_time = self.target_cycle_time * random.uniform(0.95, 1.10)
            
            # Tool wear effect (gradual degradation)
            self.tool_usage_cycles += 1
            if self.tool_usage_cycles > 500:  # Tool getting worn
                actual_cycle_time *= 1.1
                if self.tool_usage_cycles > 800:  # Tool very worn
                    actual_cycle_time *= 1.2
                    if random.random() < 0.01:  # 1% chance to trigger tool change
                        self.current_tool = (self.current_tool % 12) + 1
                        self.tool_usage_cycles = 0
                        logger.info(f"Tool change: {self.machine_id} - Tool #{self.current_tool}")
            
            # Parts produced in this interval
            parts_this_interval = int(SCADA_SAMPLING_INTERVAL / actual_cycle_time)
            self.parts_produced_shift += parts_this_interval
            self.parts_produced_cumulative += parts_this_interval
            
            # Quality - reject some parts
            if random.random() < 0.02:  # 2% base reject rate
                self.parts_rejected_shift += random.randint(1, 3)
            
            self.uptime_seconds_shift += SCADA_SAMPLING_INTERVAL
        else:
            actual_cycle_time = 0
            parts_this_interval = 0
            self.downtime_seconds_shift += SCADA_SAMPLING_INTERVAL
        
        # OEE calculation
        availability = 1.0 if is_producing else 0.0
        performance = self.target_cycle_time / actual_cycle_time if actual_cycle_time > 0 else 0.0
        quality = 1.0 - (self.parts_rejected_shift / max(self.parts_produced_shift, 1))
        oee = availability * performance * quality
        
        # Power consumption
        if is_producing:
            power_kw = self.rated_power * random.uniform(0.70, 0.95)
        elif self.current_state == 'idle':
            power_kw = self.rated_power * random.uniform(0.05, 0.15)
        else:
            power_kw = self.rated_power * random.uniform(0.01, 0.05)
        
        # Process parameters
        temp_setpoint = random.uniform(40, 70)
        temp_actual = temp_setpoint + random.uniform(-2, 2)
        if self.fault_active and 'THERM' in self.fault_code:
            temp_actual += 20  # Overheating
        
        pressure_setpoint = random.uniform(100, 150)
        pressure_actual = pressure_setpoint + random.uniform(-5, 5)
        if self.fault_active and 'HYD' in self.fault_code:
            pressure_actual -= 40  # Pressure loss
        
        # Build record
        record = {
            'machine_id': self.machine_id,
            'line_id': self.line_id,
            'factory_id': self.factory_id,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'machine_state': self.current_state,
            'operation_mode': 'auto',
            'fault_code': self.fault_code if self.fault_active else None,
            'fault_description': self.fault_description if self.fault_active else None,
            'parts_produced_cumulative': self.parts_produced_cumulative,
            'parts_produced_shift': self.parts_produced_shift,
            'parts_rejected_shift': self.parts_rejected_shift,
            'target_cycle_time_seconds': int(self.target_cycle_time),
            'actual_cycle_time_seconds': round(actual_cycle_time, 2) if actual_cycle_time > 0 else None,
            'availability_percentage': round(availability * 100, 2),
            'performance_percentage': round(performance * 100, 2),
            'quality_percentage': round(quality * 100, 2),
            'oee_percentage': round(oee * 100, 2),
            'spindle_speed_rpm': random.randint(1000, 4000) if 'cnc' in self.machine_type else None,
            'feed_rate_mm_min': round(random.uniform(100, 500), 2) if 'cnc' in self.machine_type else None,
            'tool_number': self.current_tool if 'cnc' in self.machine_type or 'drill' in self.machine_type else None,
            'program_number': f"NC{random.randint(1000, 9999)}" if 'cnc' in self.machine_type else None,
            'power_consumption_kw': round(power_kw, 2),
            'energy_consumed_kwh': round(random.uniform(1000, 50000), 4),
            'temperature_setpoint_c': round(temp_setpoint, 2),
            'temperature_actual_c': round(temp_actual, 2),
            'pressure_setpoint_bar': round(pressure_setpoint, 2),
            'pressure_actual_bar': round(pressure_actual, 2),
            'downtime_seconds_shift': self.downtime_seconds_shift,
            'last_fault_timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S') if self.fault_active else None,
            'uptime_seconds_shift': self.uptime_seconds_shift,
            'active_alarms': 1 if self.fault_active else 0,
            'alarm_codes': self.fault_code if self.fault_active else None,
            'warning_codes': None,
            'shift_id': shift['shift_id'],
            'operator_id': operator['employee_id'] if operator else None,
            'data_source': 'PLC',
            'data_quality': 'good',
            'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        return record
    
    def reset_shift_counters(self):
        """Reset shift counters (called at shift change)"""
        self.parts_produced_shift = 0
        self.parts_rejected_shift = 0
        self.downtime_seconds_shift = 0
        self.uptime_seconds_shift = 0


def initialize_kafka():
    """Initialize Kafka producer"""
    global kafka_producer
    
    if not KAFKA_AVAILABLE:
        logger.warning("Kafka not available - skipping Kafka initialization")
        return False
    
    try:
        kafka_producer = KafkaProducer(
            bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
            value_serializer=lambda v: json.dumps(v).encode('utf-8'),
            acks='all',
            retries=3
        )
        logger.info(f"Kafka producer initialized: {KAFKA_BOOTSTRAP_SERVERS}")
        return True
    except Exception as e:
        logger.error(f"Failed to initialize Kafka: {e}")
        return False


def initialize_postgres():
    """Initialize PostgreSQL connection"""
    global pg_connection
    
    if not POSTGRES_AVAILABLE:
        logger.warning("PostgreSQL not available - skipping database initialization")
        return False
    
    try:
        pg_connection = psycopg2.connect(
            host=PG_HOST,
            port=PG_PORT,
            database=PG_DATABASE,
            user=PG_USER,
            password=PG_PASSWORD,
            sslmode=PG_SSL_MODE
        )
        pg_connection.autocommit = False
        logger.info(f"PostgreSQL connection established: {PG_HOST}:{PG_PORT}/{PG_DATABASE}")
        logger.info(f"SSL Mode: {PG_SSL_MODE}")
        return True
    except Exception as e:
        logger.error(f"Failed to connect to PostgreSQL: {e}")
        logger.info("Daemon will continue without database writes")
        return False


def send_to_kafka(record: Dict):
    """Send record to Kafka"""
    if not kafka_producer:
        return False
    
    try:
        future = kafka_producer.send(KAFKA_TOPIC, record)
        future.get(timeout=10)
        stats['kafka_sent'] += 1
        return True
    except Exception as e:
        logger.error(f"Failed to send to Kafka: {e}")
        stats['errors'] += 1
        return False


def flush_to_postgres():
    """Batch insert records to PostgreSQL"""
    global scada_batch
    
    if not pg_connection or not scada_batch:
        return
    
    try:
        cursor = pg_connection.cursor()
        
        # Prepare batch insert
        insert_sql = """
            INSERT INTO scada_machine_data (
                machine_id, line_id, factory_id, timestamp, machine_state, operation_mode,
                fault_code, fault_description, parts_produced_cumulative, parts_produced_shift,
                parts_rejected_shift, target_cycle_time_seconds, actual_cycle_time_seconds,
                availability_percentage, performance_percentage, quality_percentage, oee_percentage,
                spindle_speed_rpm, feed_rate_mm_min, tool_number, program_number,
                power_consumption_kw, energy_consumed_kwh, temperature_setpoint_c, temperature_actual_c,
                pressure_setpoint_bar, pressure_actual_bar, downtime_seconds_shift,
                last_fault_timestamp, uptime_seconds_shift, active_alarms, alarm_codes,
                warning_codes, shift_id, operator_id, data_source, data_quality, created_at
            ) VALUES (
                %(machine_id)s, %(line_id)s, %(factory_id)s, %(timestamp)s, %(machine_state)s, %(operation_mode)s,
                %(fault_code)s, %(fault_description)s, %(parts_produced_cumulative)s, %(parts_produced_shift)s,
                %(parts_rejected_shift)s, %(target_cycle_time_seconds)s, %(actual_cycle_time_seconds)s,
                %(availability_percentage)s, %(performance_percentage)s, %(quality_percentage)s, %(oee_percentage)s,
                %(spindle_speed_rpm)s, %(feed_rate_mm_min)s, %(tool_number)s, %(program_number)s,
                %(power_consumption_kw)s, %(energy_consumed_kwh)s, %(temperature_setpoint_c)s, %(temperature_actual_c)s,
                %(pressure_setpoint_bar)s, %(pressure_actual_bar)s, %(downtime_seconds_shift)s,
                %(last_fault_timestamp)s, %(uptime_seconds_shift)s, %(active_alarms)s, %(alarm_codes)s,
                %(warning_codes)s, %(shift_id)s, %(operator_id)s, %(data_source)s, %(data_quality)s, %(created_at)s
            )
        """
        
        execute_batch(cursor, insert_sql, scada_batch)
        pg_connection.commit()
        
        stats['postgres_inserted'] += len(scada_batch)
        logger.info(f"Inserted {len(scada_batch)} records to PostgreSQL")
        
        scada_batch = []
        cursor.close()
        return True
    
    except Exception as e:
        logger.error(f"Failed to insert to PostgreSQL: {e}")
        pg_connection.rollback()
        stats['errors'] += 1
        scada_batch = []
        return False


def print_stats():
    """Print daemon statistics"""
    elapsed = (datetime.now() - stats['start_time']).total_seconds()
    rate = stats['records_generated'] / elapsed if elapsed > 0 else 0
    
    logger.info("="*80)
    logger.info(f"SCADA Daemon Statistics")
    logger.info(f"  Uptime: {elapsed:.1f} seconds")
    logger.info(f"  Records Generated: {stats['records_generated']:,}")
    logger.info(f"  Kafka Sent: {stats['kafka_sent']:,}")
    logger.info(f"  PostgreSQL Inserted: {stats['postgres_inserted']:,}")
    logger.info(f"  Errors: {stats['errors']}")
    logger.info(f"  Rate: {rate:.2f} records/sec")
    logger.info("="*80)


def load_master_data():
    """Load master data from Folder 01"""
    try:
        import os
        # Read from Folder 01 - Base Data
        folder_01_path = os.path.join(os.path.dirname(__file__), '..', '01 - Base Data', 'genims_master_data.json')
        master_data_path = os.path.abspath(folder_01_path)
        
        with open(master_data_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to load master data: {e}")
        return None


def main():
    """Main daemon loop"""
    logger.info("="*80)
    logger.info("GenIMS PLC/SCADA Daemon Starting")
    logger.info("="*80)
    
    # Load master data
    master_data = load_master_data()
    if not master_data:
        logger.error("Failed to load master data. Exiting.")
        return 1
    
    machines = master_data['machines']
    employees = master_data['employees']
    shifts = master_data['shifts']
    
    logger.info(f"Loaded {len(machines)} machines")
    
    # Initialize connections
    kafka_enabled = initialize_kafka()
    postgres_enabled = initialize_postgres()
    
    if not kafka_enabled and not postgres_enabled:
        logger.warning("Neither Kafka nor PostgreSQL available - daemon will only log to console")
    
    # Create machine simulators
    simulators = [MachineSimulator(machine, employees, shifts) for machine in machines]
    logger.info(f"Created {len(simulators)} machine simulators")
    
    # Inject some faults for demonstration
    num_faults = int(len(simulators) * 0.03)  # 3% of machines
    fault_machines = random.sample(simulators, num_faults)
    
    fault_types = [
        ('BEAR-001', 'Bearing degradation detected'),
        ('THERM-001', 'Motor thermal overload'),
        ('HYD-001', 'Hydraulic pressure loss'),
        ('TOOL-001', 'Cutting tool wear detected')
    ]
    
    for sim in fault_machines:
        fault_code, fault_desc = random.choice(fault_types)
        sim.inject_fault(fault_code, fault_desc, random.randint(300, 1800))
    
    logger.info(f"Injected {num_faults} fault conditions")
    logger.info(f"Streaming interval: {SCADA_SAMPLING_INTERVAL} seconds")
    logger.info("Press Ctrl+C to stop")
    logger.info("="*80)
    
    # Main loop
    iteration = 0
    last_stats_time = time.time()
    
    while running:
        try:
            loop_start = time.time()
            
            # Generate readings from all machines
            for simulator in simulators:
                record = simulator.get_next_reading()
                stats['records_generated'] += 1
                
                # Send to Kafka
                if kafka_enabled:
                    send_to_kafka(record)
                
                # Add to batch for PostgreSQL
                if postgres_enabled:
                    scada_batch.append(record)
                
                # Sample log
                if random.random() < 0.01:  # 1% sampling
                    logger.info(f"Sample: {simulator.machine_id} - State: {record['machine_state']}, "
                              f"OEE: {record['oee_percentage']:.1f}%, "
                              f"Parts: {record['parts_produced_shift']}")
            
            # Flush to PostgreSQL if batch is full
            if len(scada_batch) >= BATCH_SIZE and postgres_enabled:
                flush_to_postgres()
            
            # Print stats every 60 seconds
            if time.time() - last_stats_time > 60:
                print_stats()
                last_stats_time = time.time()
            
            # Sleep to maintain interval
            elapsed = time.time() - loop_start
            sleep_time = max(0, SCADA_SAMPLING_INTERVAL - elapsed)
            
            if sleep_time > 0:
                time.sleep(sleep_time)
            else:
                logger.warning(f"Loop took {elapsed:.2f}s - falling behind sampling rate!")
            
            iteration += 1
        
        except Exception as e:
            logger.error(f"Error in main loop: {e}", exc_info=True)
            stats['errors'] += 1
            time.sleep(1)
    
    # Cleanup
    logger.info("Shutting down...")
    
    # Flush remaining records
    if postgres_enabled and scada_batch:
        flush_to_postgres()
    
    # Close connections
    if kafka_producer:
        kafka_producer.close()
        logger.info("Kafka producer closed")
    
    if pg_connection:
        pg_connection.close()
        logger.info("PostgreSQL connection closed")
    
    print_stats()
    logger.info("SCADA Daemon stopped")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
