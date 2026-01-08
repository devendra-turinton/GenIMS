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

# Streaming configuration - FAST GENERATION MODE
SCADA_SAMPLING_INTERVAL = int(os.getenv('SCADA_SAMPLING_INTERVAL', '60'))
BATCH_SIZE = int(os.getenv('SCADA_BATCH_SIZE', '2000'))
RECORDS_PER_CYCLE = int(os.getenv('SCADA_RECORDS_PER_CYCLE', '100'))
TOTAL_RECORDS = int(os.getenv('SCADA_TOTAL_RECORDS', '144000'))

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
pg_connection = None
scada_batch = []
stats = {
    'records_generated': 0,
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
        self.plant_id = machine.get('plant_id', machine.get('factory_id', 'PLANT-001'))
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
        self.fault_start_time = datetime.now()  # Will be set in main loop with simulated time
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
    
    def get_current_shift(self, simulated_timestamp) -> Dict:
        """Get current shift based on simulated time"""
        current_hour = simulated_timestamp.hour
        day_of_week = simulated_timestamp.strftime('%a').lower()
        
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
    
    def determine_state(self, simulated_timestamp) -> str:
        """Determine machine state based on simulated time and conditions"""
        if self.fault_active and self.fault_start_time is not None:
            elapsed = (simulated_timestamp - self.fault_start_time).total_seconds()
            if elapsed > self.fault_duration:
                self.clear_fault()
                return 'running'
            return 'fault'
        
        hour = simulated_timestamp.hour
        
        # Night maintenance window (2-6 AM)
        if 2 <= hour < 6:
            return random.choices(['idle', 'maintenance'], weights=[0.7, 0.3])[0]
        
        # Normal operations - mostly running
        return random.choices(
            ['running', 'idle', 'setup'],
            weights=[0.88, 0.10, 0.02]
        )[0]
    
    def get_reading(self, timestamp_seconds_into_sim, sim_base_time):
        """Generate reading for given absolute timestamp"""
        current_ts = sim_base_time + timedelta(seconds=timestamp_seconds_into_sim)
        hour = current_ts.hour
        
        # Check fault
        fault_detected = False
        fault_code = None
        fault_desc = None
        
        if self.fault_active and hasattr(self, 'fault_start_offset'):
            fault_start = self.fault_start_offset
            fault_end = self.fault_start_offset + 3600  # 1 hour duration
            
            if fault_start <= timestamp_seconds_into_sim <= fault_end:
                fault_detected = True
                fault_code = self.fault_code
                fault_desc = self.fault_description
        
        # Determine state
        if fault_detected:
            operating_state = 'fault'
        elif 2 <= hour < 6:  # Night maintenance
            operating_state = random.choice(['idle', 'maintenance', 'idle'])
        else:
            operating_state = random.choices(['running', 'idle', 'setup'], weights=[0.88, 0.10, 0.02])[0]
        
        # Calculate metrics
        is_producing = operating_state == 'running'
        
        if is_producing:
            cycle_time = self.target_cycle_time * random.uniform(0.95, 1.10)
            parts = int(SCADA_SAMPLING_INTERVAL / cycle_time)
            availability = 1.0
        else:
            cycle_time = 0
            parts = 0
            availability = 0.0
        
        performance = 0.95 if is_producing else 0.0
        quality = 0.98
        oee = availability * performance * quality
        
        # Shift info
        shift = next((s for s in self.shifts if not (2 <= hour < 6)), self.shifts[0])
        
        return {
            'machine_id': self.machine_id,
            'line_id': self.line_id,
            'factory_id': self.factory_id,
            'timestamp': current_ts,
            'machine_state': operating_state,
            'operation_mode': 'auto',
            'fault_code': fault_code,
            'fault_description': fault_desc,
            'parts_produced_cumulative': random.randint(10000, 500000),
            'parts_produced_shift': random.randint(0, 100),
            'parts_rejected_shift': random.randint(0, 5),
            'target_cycle_time_seconds': int(self.target_cycle_time),
            'actual_cycle_time_seconds': 3600 if is_producing else None,
            'availability_percentage': round(availability * 100, 2),
            'performance_percentage': round(performance * 100, 2),
            'quality_percentage': round(quality * 100, 2),
            'oee_percentage': round(oee * 100, 2),
            'spindle_speed_rpm': random.randint(1000, 4000) if is_producing else None,
            'feed_rate_mm_min': round(random.uniform(100, 500), 2) if is_producing else None,
            'tool_number': self.current_tool,
            'program_number': f"NC{random.randint(1000, 9999)}" if is_producing else None,
            'power_consumption_kw': round(random.uniform(30, 80), 2) if is_producing else round(random.uniform(5, 15), 2),
            'energy_consumed_kwh': round(random.uniform(1000, 50000), 2),
            'temperature_setpoint_c': round(random.uniform(40, 70), 2),
            'temperature_actual_c': round(random.uniform(35, 75), 2),
            'pressure_setpoint_bar': round(random.uniform(100, 150), 2),
            'pressure_actual_bar': round(random.uniform(95, 155), 2),
            'downtime_seconds_shift': 0 if is_producing else SCADA_SAMPLING_INTERVAL,
            'last_fault_timestamp': current_ts if fault_detected else None,
            'uptime_seconds_shift': SCADA_SAMPLING_INTERVAL if is_producing else 0,
            'active_alarms': 1 if fault_detected else 0,
            'alarm_codes': fault_code if fault_detected else None,
            'warning_codes': None,
            'shift_id': shift['shift_id'],
            'operator_id': shift.get('operator_id'),
            'data_source': 'PLC',
            'data_quality': 'good',
            'created_at': datetime.now()
        }


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


def get_scada_data_count():
    """Get current count of scada_machine_data records from PostgreSQL"""
    try:
        conn = psycopg2.connect(
            host=PG_HOST,
            port=PG_PORT,
            database=PG_DATABASE,
            user=PG_USER,
            password=PG_PASSWORD,
            sslmode=PG_SSL_MODE,
            connect_timeout=10
        )
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM scada_machine_data;")
        count = cursor.fetchone()[0]
        cursor.close()
        conn.close()
        return count
    except Exception as e:
        logger.warning(f"Could not get scada_machine_data count: {e}")
        return None


def get_max_scada_timestamp():
    """Get the maximum timestamp from scada_machine_data and start next day for clean append"""
    try:
        conn = psycopg2.connect(
            host=PG_HOST,
            port=PG_PORT,
            database=PG_DATABASE,
            user=PG_USER,
            password=PG_PASSWORD,
            sslmode=PG_SSL_MODE,
            connect_timeout=10
        )
        cursor = conn.cursor()
        cursor.execute("SELECT MAX(timestamp) FROM scada_machine_data;")
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if result and result[0]:
            max_ts = result[0]
            logger.info(f"Found max timestamp in scada_machine_data: {max_ts}")
            
            # CRITICAL FIX: Never use future dates - cap at current date
            current_datetime = datetime.now()
            if max_ts > current_datetime:
                logger.warning(f"Found future timestamp {max_ts}, using current time {current_datetime} instead")
                max_ts = current_datetime
            
            # Start NEXT day at midnight to avoid any overlaps with past data
            next_day = (max_ts + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
            
            # Double-check: if next day is still future, use current time
            if next_day > current_datetime:
                logger.warning(f"Next day {next_day} is in future, using current time instead")
                next_day = current_datetime.replace(minute=0, second=0, microsecond=0)
                
            logger.info(f"Will generate data starting from: {next_day}")
            return next_day
        else:
            logger.info("No existing timestamps found, starting from current time")
            # Start from current time, not future
            current_time = datetime.now().replace(minute=0, second=0, microsecond=0)
            return current_time
    except Exception as e:
        logger.warning(f"Could not get max scada_machine_data timestamp: {e}, using current time")
        current_time = datetime.now().replace(minute=0, second=0, microsecond=0)
        return current_time


def reset_scada_machine_data_sequence():
    """Reset scada_machine_data_scada_id_seq to prevent duplicate key errors on next insert"""
    try:
        conn = psycopg2.connect(
            host=PG_HOST,
            port=PG_PORT,
            database=PG_DATABASE,
            user=PG_USER,
            password=PG_PASSWORD,
            sslmode=PG_SSL_MODE,
            connect_timeout=10
        )
        cursor = conn.cursor()
        
        # Get max ID currently in table
        cursor.execute("SELECT MAX(scada_id) FROM scada_machine_data;")
        max_id = cursor.fetchone()[0]
        
        if max_id is not None:
            # Reset sequence to next available value
            cursor.execute(f"SELECT setval('scada_machine_data_scada_id_seq', {max_id + 1})")
            logger.info(f"✓ Reset scada_machine_data sequence to {max_id + 1}")
        
        cursor.close()
        conn.close()
    except Exception as e:
        logger.warning(f"Could not reset scada_machine_data sequence: {e}")


def main():
    """Main - Generate all data in-memory, then bulk dump"""
    logger.info("="*80)
    logger.info("GenIMS PLC/SCADA Daemon - ULTRA FAST MODE (In-Memory Generation)")
    logger.info("="*80)
    
    start_time = time.time()
    
    # Load master data
    master_data = load_master_data()
    if not master_data:
        logger.error("Failed to load master data")
        return 1
    
    machines = master_data['machines']
    employees = master_data['employees']
    shifts = master_data['shifts']
    
    logger.info(f"Loaded {len(machines):,} machines")
    
    # Create simulators
    simulators = [MachineSimulator(machine, employees, shifts) for machine in machines]
    logger.info(f"Created {len(simulators):,} machine simulators")
    
    # Query database for max timestamp to ensure no overlaps (true APPEND mode)
    sim_base_time = get_max_scada_timestamp()
    logger.info(f"Using base timestamp: {sim_base_time}")
    
    # Inject faults (3% of machines)
    num_faults = int(len(simulators) * 0.03)
    fault_machines = random.sample(simulators, num_faults)
    
    fault_types = [
        ('BEAR-001', 'Bearing degradation'),
        ('THERM-001', 'Motor thermal overload'),
        ('HYD-001', 'Hydraulic pressure loss'),
        ('TOOL-001', 'Tool wear detected')
    ]
    
    for sim in fault_machines:
        fault_code, fault_desc = random.choice(fault_types)
        sim.fault_code = fault_code
        sim.fault_description = fault_desc
        sim.fault_active = True
        sim.fault_start_offset = random.randint(1000, 10000)  # seconds into sim
    
    logger.info(f"✓ Injected {num_faults} fault conditions")
    logger.info(f"Target records: {TOTAL_RECORDS:,}")
    
    # Get baseline count before generation
    count_before = get_scada_data_count()
    if count_before is not None:
        logger.info(f"📊 Baseline: {count_before:,} records already in scada_machine_data")
    
    logger.info("="*80)
    logger.info("GENERATING ALL DATA IN MEMORY...")
    logger.info("="*80)
    
    # Generate ALL records in memory
    all_records = []
    records_per_machine = TOTAL_RECORDS // len(simulators)
    remainder = TOTAL_RECORDS % len(simulators)
    
    for machine_idx, sim in enumerate(simulators):
        num_records = records_per_machine + (1 if machine_idx < remainder else 0)
        
        for record_idx in range(num_records):
            timestamp_offset = record_idx * SCADA_SAMPLING_INTERVAL
            reading = sim.get_reading(timestamp_offset, sim_base_time)
            all_records.append(reading)
        
        if (machine_idx + 1) % 50 == 0:
            logger.info(f"  Generated {machine_idx + 1:,} / {len(simulators):,} machine streams")
    
    logger.info(f"✓ Generated {len(all_records):,} total records in memory")
    
    # Bulk dump to PostgreSQL
    logger.info("="*80)
    logger.info("BULK DUMPING TO POSTGRESQL...")
    logger.info("="*80)
    
    if POSTGRES_AVAILABLE:
        try:
            conn = psycopg2.connect(
                host=PG_HOST,
                port=PG_PORT,
                database=PG_DATABASE,
                user=PG_USER,
                password=PG_PASSWORD,
                sslmode=PG_SSL_MODE,
                connect_timeout=30
            )
            conn.autocommit = False
            cursor = conn.cursor()
            
            # Disable FK checks
            cursor.execute("SET CONSTRAINTS ALL DEFERRED;")
            
            insert_sql = """
                INSERT INTO scada_machine_data (
                    machine_id, line_id, factory_id, timestamp, machine_state, operation_mode,
                    fault_code, fault_description, parts_produced_cumulative, parts_produced_shift,
                    parts_rejected_shift, target_cycle_time_seconds, actual_cycle_time_seconds,
                    availability_percentage, performance_percentage, quality_percentage, oee_percentage,
                    spindle_speed_rpm, feed_rate_mm_min, tool_number, program_number,
                    power_consumption_kw, energy_consumed_kwh, temperature_setpoint_c, temperature_actual_c,
                    pressure_setpoint_bar, pressure_actual_bar, downtime_seconds_shift, last_fault_timestamp,
                    uptime_seconds_shift, active_alarms, alarm_codes, warning_codes,
                    shift_id, operator_id, data_source, data_quality, created_at
                ) VALUES (
                    %(machine_id)s, %(line_id)s, %(factory_id)s, %(timestamp)s, %(machine_state)s, %(operation_mode)s,
                    %(fault_code)s, %(fault_description)s, %(parts_produced_cumulative)s, %(parts_produced_shift)s,
                    %(parts_rejected_shift)s, %(target_cycle_time_seconds)s, %(actual_cycle_time_seconds)s,
                    %(availability_percentage)s, %(performance_percentage)s, %(quality_percentage)s, %(oee_percentage)s,
                    %(spindle_speed_rpm)s, %(feed_rate_mm_min)s, %(tool_number)s, %(program_number)s,
                    %(power_consumption_kw)s, %(energy_consumed_kwh)s, %(temperature_setpoint_c)s, %(temperature_actual_c)s,
                    %(pressure_setpoint_bar)s, %(pressure_actual_bar)s, %(downtime_seconds_shift)s, %(last_fault_timestamp)s,
                    %(uptime_seconds_shift)s, %(active_alarms)s, %(alarm_codes)s, %(warning_codes)s,
                    %(shift_id)s, %(operator_id)s, %(data_source)s, %(data_quality)s, %(created_at)s
                )
            """
            
            logger.info(f"Inserting {len(all_records):,} records in batches of {BATCH_SIZE:,}...")
            
            inserted_count = 0
            for i in range(0, len(all_records), BATCH_SIZE):
                batch = all_records[i:i+BATCH_SIZE]
                try:
                    execute_batch(cursor, insert_sql, batch, page_size=1000)
                    conn.commit()
                    inserted_count += len(batch)
                    logger.info(f"  Flushed {inserted_count:,} / {len(all_records):,} records")
                except psycopg2.IntegrityError as e:
                    logger.warning(f"Integrity error: {str(e)[:80]}... - Skipping batch")
                    conn.rollback()
                    continue
                except Exception as e:
                    logger.error(f"Batch error: {e}")
                    conn.rollback()
                    continue
            
            cursor.close()
            conn.close()
            
            logger.info(f"✓ Inserted {inserted_count:,} records successfully")
            
            # Reset sequence to prevent duplicate key errors on next run
            reset_scada_machine_data_sequence()
            
        except Exception as e:
            logger.error(f"PostgreSQL error: {e}")
            return 1
    
    elapsed = time.time() - start_time
    rate = len(all_records) / elapsed if elapsed > 0 else 0
    
    # Get final count after insertion
    count_after = get_scada_data_count()
    
    logger.info("="*80)
    logger.info("GENERATION COMPLETE")
    logger.info(f"  Total time: {elapsed:.1f} seconds")
    logger.info(f"  Records generated: {len(all_records):,}")
    logger.info(f"  Generation rate: {rate:,.0f} records/sec")
    
    if count_before is not None and count_after is not None:
        inserted = count_after - count_before
        logger.info(f"📊 Database before: {count_before:,} records")
        logger.info(f"📊 Database after:  {count_after:,} records")
        logger.info(f"📊 Records inserted: {inserted:,}")
    
    logger.info("="*80)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
