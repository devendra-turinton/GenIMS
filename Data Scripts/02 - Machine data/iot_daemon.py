#!/usr/bin/env python3
"""
GenIMS IoT Daemon - ULTRA FAST MODE
Generates complete synthetic sensor data in-memory, then bulk dumps to PostgreSQL
No streaming delays - pure speed generation with graceful error handling
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
import numpy as np
from dotenv import load_dotenv

# Load environment variables
env_file = os.path.join(os.path.dirname(__file__), '..', '..', 'scripts', 'config.env')
if os.path.exists(env_file):
    load_dotenv(env_file)

# PostgreSQL
try:
    import psycopg2
    from psycopg2.extras import execute_batch
    POSTGRES_AVAILABLE = True
except ImportError:
    POSTGRES_AVAILABLE = False
    print("WARNING: psycopg2 not installed")

# ============================================================================
# CONFIGURATION
# ============================================================================

# Streaming configuration - Aligned with 14-day coverage  
# 1599 sensors * 14 days * 24 hours * 360 samples/hour = 193,415,040 total samples
# For demo efficiency: 1599 sensors * 100 samples = 159,900 records (matches generation script)
SENSOR_SAMPLING_INTERVAL = int(os.getenv('IOT_SAMPLING_INTERVAL', '10'))
BATCH_SIZE = int(os.getenv('IOT_BATCH_SIZE', '5000'))  # Larger batch for sensor volume
RECORDS_PER_CYCLE = int(os.getenv('IOT_RECORDS_PER_CYCLE', '2000'))  # More records per cycle
TOTAL_RECORDS = int(os.getenv('IOT_TOTAL_RECORDS', '159900'))  # 1599 sensors * 100 samples = 14 days

# PostgreSQL configuration - from Azure Cloud via config.env
PG_HOST = os.getenv('POSTGRES_HOST', 'localhost')
PG_PORT = int(os.getenv('POSTGRES_PORT', '5432'))
PG_DATABASE = os.getenv('DB_OPERATIONS', 'genims_operations_db')
PG_USER = os.getenv('POSTGRES_USER', 'postgres')
PG_PASSWORD = os.getenv('POSTGRES_PASSWORD', '')
PG_SSL_MODE = os.getenv('PG_SSL_MODE', 'require')

# Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('IoTDaemon')

# ============================================================================
# GLOBAL STATE
# ============================================================================

running = True
pg_connection = None
sensor_batch = []
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


class SensorSimulator:
    """Simulates realistic sensor behavior with fault patterns"""
    
    def __init__(self, sensor: Dict):
        self.sensor = sensor
        self.sensor_id = sensor['sensor_id']
        self.machine_id = sensor['machine_id']
        self.sensor_type = sensor['sensor_type']
        self.measurement_unit = sensor['measurement_unit']
        self.line_id = sensor.get('line_id', 'LINE-001')
        self.factory_id = sensor.get('factory_id', 'FAC-001')
        
        # Operating ranges
        self.normal_min = sensor['normal_operating_min']
        self.normal_max = sensor['normal_operating_max']
        self.warning_min = sensor['warning_threshold_min']
        self.warning_max = sensor['warning_threshold_max']
        self.critical_min = sensor['critical_threshold_min']
        self.critical_max = sensor['critical_threshold_max']
        
        # State
        self.current_value = random.uniform(self.normal_min, self.normal_max)
        self.fault_active = False
        self.fault_start_time = None
        self.fault_duration = 0
        self.fault_severity = 0.0
        
        # Fast generation mode: Use simulated time instead of wall-clock
        self.simulated_time = None  # Will be set externally
        self.last_history_timestamp = None
        self.history_window_seconds = 60  # 1 minute window
        self.history = []  # Will store (timestamp, value) tuples
    
    def set_simulated_time(self, timestamp):
        """Set the current simulated time"""
        self.simulated_time = timestamp
    
    def inject_fault(self, start_offset_seconds, duration_seconds, severity):
        """Pre-inject fault with absolute time offset"""
        self.fault_active = True
        self.fault_start_offset = start_offset_seconds
        self.fault_duration = duration_seconds
        self.fault_severity = severity
    
    def get_reading(self, timestamp_seconds_into_sim, sim_base_time):
        """Generate reading for given absolute timestamp"""
        current_ts = sim_base_time + timedelta(seconds=timestamp_seconds_into_sim)
        current_value = random.uniform(self.normal_min, self.normal_max)
        
        # Check if in fault window
        fault_factor = 0.0
        if self.fault_active and hasattr(self, 'fault_start_offset'):
            fault_start = self.fault_start_offset
            fault_end = self.fault_start_offset + self.fault_duration
            
            if fault_start <= timestamp_seconds_into_sim <= fault_end:
                progress = (timestamp_seconds_into_sim - fault_start) / self.fault_duration
                fault_factor = self.fault_severity * (0.3 + 0.7 * progress)
        
        # Apply fault effects
        if fault_factor > 0:
            if self.sensor_type == 'vibration':
                current_value = current_value + fault_factor * (self.critical_max - self.normal_max)
            elif self.sensor_type == 'temperature':
                current_value = current_value + fault_factor * (self.critical_max - self.normal_max)
            elif self.sensor_type == 'pressure':
                current_value = current_value - fault_factor * (self.normal_min - self.critical_min)
            elif self.sensor_type == 'current':
                current_value = current_value * (1.0 + fault_factor * 0.5)
            elif self.sensor_type == 'flow':
                current_value = current_value * (0.7 if fault_factor > 0.5 else 1.3)
            else:
                current_value = current_value * (1.0 + random.uniform(-0.2, 0.2) * fault_factor)
        
        current_value = max(self.critical_min, min(self.critical_max, current_value))
        
        # Determine status
        status = 'normal'
        is_below_warning = current_value < self.warning_min
        is_above_warning = current_value > self.warning_max
        is_below_critical = current_value < self.critical_min
        is_above_critical = current_value > self.critical_max
        
        if is_below_critical or is_above_critical:
            status = 'critical'
        elif is_below_warning or is_above_warning:
            status = 'warning'
        
        quality = 95 if status == 'normal' else (85 if status == 'warning' else 50)
        
        return {
            'sensor_id': self.sensor_id,
            'machine_id': self.machine_id,
            'line_id': self.line_id,
            'factory_id': self.factory_id,
            'timestamp': current_ts,
            'measurement_value': round(current_value, 2),
            'measurement_unit': self.measurement_unit,
            'status': status,
            'quality': quality,
            'is_below_warning': is_below_warning,
            'is_above_warning': is_above_warning,
            'is_below_critical': is_below_critical,
            'is_above_critical': is_above_critical,
            'min_value_1min': round(current_value * 0.95, 2),
            'max_value_1min': round(current_value * 1.05, 2),
            'avg_value_1min': round(current_value, 2),
            'std_dev_1min': round(current_value * 0.02, 2),
            'anomaly_score': random.uniform(0, 0.1) if status != 'normal' else random.uniform(0, 0.02),
            'is_anomaly': status != 'normal',
            'data_source': 'IOT_SENSOR',
            'protocol': 'MQTT',
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
            sslmode=PG_SSL_MODE,
            connect_timeout=10
        )
        pg_connection.autocommit = False
        logger.info(f"PostgreSQL connection established: {PG_HOST}:{PG_PORT}/{PG_DATABASE}")
        return True
    except Exception as e:
        logger.error(f"Failed to connect to PostgreSQL: {e}")
        logger.info("Daemon will continue without database writes")
        return False


def is_connection_alive():
    """Check if PostgreSQL connection is still alive"""
    global pg_connection
    
    if not pg_connection:
        return False
    
    try:
        cursor = pg_connection.cursor()
        cursor.execute("SELECT 1")
        cursor.close()
        return True
    except Exception:
        return False


def reconnect_postgres():
    """Reconnect to PostgreSQL if connection is lost"""
    global pg_connection
    
    try:
        if pg_connection:
            try:
                pg_connection.close()
            except:
                pass
        
        pg_connection = psycopg2.connect(
            host=PG_HOST,
            port=PG_PORT,
            database=PG_DATABASE,
            user=PG_USER,
            password=PG_PASSWORD,
            sslmode=PG_SSL_MODE,
            connect_timeout=10
        )
        pg_connection.autocommit = False
        logger.info("PostgreSQL connection re-established")
        return True
    except Exception as e:
        logger.error(f"Failed to reconnect to PostgreSQL: {e}")
        return False


def flush_to_postgres():
    """Batch insert records to PostgreSQL"""
    global sensor_batch, pg_connection
    
    if not sensor_batch:
        return
    
    max_retries = 3
    retry_count = 0
    
    while retry_count < max_retries:
        # Check and reconnect if needed
        if not is_connection_alive():
            logger.warning(f"PostgreSQL connection lost (retry {retry_count + 1}/{max_retries}), attempting reconnect...")
            if not reconnect_postgres():
                retry_count += 1
                if retry_count < max_retries:
                    time.sleep(2)  # Wait before retry
                    continue
                else:
                    logger.error("Failed to reconnect to PostgreSQL after retries, skipping batch")
                    sensor_batch = []
                    return
        
        try:
            cursor = pg_connection.cursor()
            
            # Prepare batch insert
            insert_sql = """
                INSERT INTO sensor_data (
                    sensor_id, machine_id, line_id, factory_id, timestamp,
                    measurement_value, measurement_unit, status, quality,
                    is_below_warning, is_above_warning, is_below_critical, is_above_critical,
                    min_value_1min, max_value_1min, avg_value_1min, std_dev_1min,
                    anomaly_score, is_anomaly, data_source, protocol, created_at
                ) VALUES (
                    %(sensor_id)s, %(machine_id)s, %(line_id)s, %(factory_id)s, %(timestamp)s,
                    %(measurement_value)s, %(measurement_unit)s, %(status)s, %(quality)s,
                    %(is_below_warning)s, %(is_above_warning)s, %(is_below_critical)s, %(is_above_critical)s,
                    %(min_value_1min)s, %(max_value_1min)s, %(avg_value_1min)s, %(std_dev_1min)s,
                    %(anomaly_score)s, %(is_anomaly)s, %(data_source)s, %(protocol)s, %(created_at)s
                )
            """
            
            execute_batch(cursor, insert_sql, sensor_batch)
            pg_connection.commit()
            
            stats['postgres_inserted'] += len(sensor_batch)
            logger.info(f"Inserted {len(sensor_batch)} records to PostgreSQL")
            
            sensor_batch = []
            cursor.close()
            return  # Success - break retry loop
            
        except Exception as e:
            logger.error(f"Failed to insert to PostgreSQL: {e}")
            try:
                pg_connection.rollback()
            except:
                pass  # Connection may already be closed
            stats['errors'] += 1
            retry_count += 1
            if retry_count < max_retries:
                time.sleep(1)  # Wait before retry
            else:
                sensor_batch = []
                return


def print_stats():
    """Print daemon statistics"""
    elapsed = (datetime.now() - stats['start_time']).total_seconds()
    rate = stats['records_generated'] / elapsed if elapsed > 0 else 0
    
    logger.info("="*80)
    logger.info(f"IoT Daemon Statistics")
    logger.info(f"  Uptime: {elapsed:.1f} seconds")
    logger.info(f"  Records Generated: {stats['records_generated']:,}")
    logger.info(f"  PostgreSQL Inserted: {stats['postgres_inserted']:,}")
    logger.info(f"  Errors: {stats['errors']}")
    logger.info(f"  Rate: {rate:.2f} records/sec")
    logger.info("="*80)


def load_sensors() -> List[Dict]:
    """Load sensor master data from Folder 01"""
    try:
        import os
        # Read from Folder 01 - Base Data
        folder_01_path = os.path.join(os.path.dirname(__file__), '..', '01 - Base Data', 'genims_master_data.json')
        master_data_path = os.path.abspath(folder_01_path)
        
        with open(master_data_path, 'r') as f:
            master_data = json.load(f)
        return master_data['sensors']
    except Exception as e:
        logger.error(f"Failed to load sensors: {e}")
        return []


def get_sensor_data_count():
    """Get current count of sensor_data records from PostgreSQL"""
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
        cursor.execute("SELECT COUNT(*) FROM sensor_data;")
        count = cursor.fetchone()[0]
        cursor.close()
        conn.close()
        return count
    except Exception as e:
        logger.warning(f"Could not get sensor_data count: {e}")
        return None


def get_max_sensor_timestamp():
    """Get the maximum timestamp from sensor_data and start next day for clean append"""
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
        cursor.execute("SELECT MAX(timestamp) FROM sensor_data;")
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if result and result[0]:
            max_ts = result[0]
            logger.info(f"Found max timestamp in sensor_data: {max_ts}")
            
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
        logger.warning(f"Could not get max sensor_data timestamp: {e}, using current time")
        current_time = datetime.now().replace(minute=0, second=0, microsecond=0)
        return current_time


def reset_sensor_data_sequence():
    """Reset sensor_data_sensor_data_id_seq to prevent duplicate key errors on next insert"""
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
        cursor.execute("SELECT MAX(sensor_data_id) FROM sensor_data;")
        max_id = cursor.fetchone()[0]
        
        if max_id is not None:
            # Reset sequence to next available value
            cursor.execute(f"SELECT setval('sensor_data_sensor_data_id_seq', {max_id + 1})")
            logger.info(f"✓ Reset sensor_data sequence to {max_id + 1}")
        
        cursor.close()
        conn.close()
    except Exception as e:
        logger.warning(f"Could not reset sensor_data sequence: {e}")


def main():
    """Main - Generate all data in-memory, then bulk dump"""
    logger.info("="*80)
    logger.info("GenIMS IoT Daemon - ULTRA FAST MODE (In-Memory Generation)")
    logger.info("="*80)
    
    start_time = time.time()
    
    # Load sensors
    sensors = load_sensors()
    if not sensors:
        logger.error("No sensors loaded!")
        return 1
    
    logger.info(f"Loaded {len(sensors):,} sensors")
    
    # Create simulators
    simulators = [SensorSimulator(s) for s in sensors]
    logger.info(f"Created {len(simulators):,} sensor simulators")
    
    # Inject faults (5% of sensors)
    num_faults = int(len(simulators) * 0.05)
    fault_sensors = random.sample(simulators, num_faults)
    
    # Query database for max timestamp to ensure no overlaps (true APPEND mode)
    sim_base_time = get_max_sensor_timestamp()
    logger.info(f"Using base timestamp: {sim_base_time}")
    
    fault_count = 0
    for sim in fault_sensors:
        offset = random.randint(100, max(2000, TOTAL_RECORDS // len(simulators) // 2))
        duration = random.randint(300, 3600)
        severity = random.uniform(0.5, 0.9)
        sim.inject_fault(offset, duration, severity)
        fault_count += 1
    
    logger.info(f"✓ Injected {fault_count} fault conditions")
    logger.info(f"Target records: {TOTAL_RECORDS:,}")
    
    # Get baseline count before generation
    count_before = get_sensor_data_count()
    if count_before is not None:
        logger.info(f"📊 Baseline: {count_before:,} records already in sensor_data")
    
    logger.info("="*80)
    logger.info("GENERATING ALL DATA IN MEMORY...")
    logger.info("="*80)
    
    # Generate ALL records in memory
    all_records = []
    records_per_sensor = TOTAL_RECORDS // len(simulators)
    remainder = TOTAL_RECORDS % len(simulators)
    
    for sensor_idx, sim in enumerate(simulators):
        num_records = records_per_sensor + (1 if sensor_idx < remainder else 0)
        
        for record_idx in range(num_records):
            timestamp_offset = record_idx * SENSOR_SAMPLING_INTERVAL
            reading = sim.get_reading(timestamp_offset, sim_base_time)
            all_records.append(reading)
        
        if (sensor_idx + 1) % 200 == 0:
            logger.info(f"  Generated {sensor_idx + 1:,} / {len(simulators):,} sensor streams")
    
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
            
            # Disable FK checks for synthetic data
            cursor.execute("SET CONSTRAINTS ALL DEFERRED;")
            
            insert_sql = """
                INSERT INTO sensor_data (
                    sensor_id, machine_id, line_id, factory_id, timestamp,
                    measurement_value, measurement_unit, status, quality,
                    is_below_warning, is_above_warning, is_below_critical, is_above_critical,
                    min_value_1min, max_value_1min, avg_value_1min, std_dev_1min,
                    anomaly_score, is_anomaly, data_source, protocol, created_at
                ) VALUES (
                    %(sensor_id)s, %(machine_id)s, %(line_id)s, %(factory_id)s, %(timestamp)s,
                    %(measurement_value)s, %(measurement_unit)s, %(status)s, %(quality)s,
                    %(is_below_warning)s, %(is_above_warning)s, %(is_below_critical)s, %(is_above_critical)s,
                    %(min_value_1min)s, %(max_value_1min)s, %(avg_value_1min)s, %(std_dev_1min)s,
                    %(anomaly_score)s, %(is_anomaly)s, %(data_source)s, %(protocol)s, %(created_at)s
                )
            """
            
            logger.info(f"Inserting {len(all_records):,} records in batches of {BATCH_SIZE:,}...")
            
            # Batch insert with error handling
            inserted_count = 0
            for i in range(0, len(all_records), BATCH_SIZE):
                batch = all_records[i:i+BATCH_SIZE]
                try:
                    execute_batch(cursor, insert_sql, batch, page_size=1000)
                    conn.commit()
                    inserted_count += len(batch)
                    logger.info(f"  Flushed {inserted_count:,} / {len(all_records):,} records")
                except psycopg2.IntegrityError as e:
                    logger.warning(f"Integrity error (duplicate/FK): {str(e)[:80]}... - Skipping batch")
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
            reset_sensor_data_sequence()
            
        except Exception as e:
            logger.error(f"PostgreSQL error: {e}")
            return 1
    
    elapsed = time.time() - start_time
    rate = len(all_records) / elapsed if elapsed > 0 else 0
    
    # Get final count after insertion
    count_after = get_sensor_data_count()
    
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
