#!/usr/bin/env python3
"""
GenIMS IoT Daemon
Continuous sensor data streaming daemon
Simulates real IoT sensor data and pushes to Kafka and PostgreSQL
"""

import sys
import time
import json
import random
import signal
import logging
from datetime import datetime
from typing import Dict, List
import math
import numpy as np

# Optional dependencies - will work without them but log warnings
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
# CONFIGURATION
# ============================================================================

# Streaming configuration
SENSOR_SAMPLING_INTERVAL = 10  # seconds between sensor readings
BATCH_SIZE = 100  # records to batch before database insert
KAFKA_TOPIC = 'genims.sensor.data'
KAFKA_BOOTSTRAP_SERVERS = ['localhost:9092']

# PostgreSQL configuration
PG_HOST = 'localhost'
PG_PORT = 5432
PG_DATABASE = 'genims_db'
PG_USER = 'genims_user'
PG_PASSWORD = 'genims_password'

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
kafka_producer = None
pg_connection = None
sensor_batch = []
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


class SensorSimulator:
    """Simulates realistic sensor behavior with fault patterns"""
    
    def __init__(self, sensor: Dict):
        self.sensor = sensor
        self.sensor_id = sensor['sensor_id']
        self.machine_id = sensor['machine_id']
        self.sensor_type = sensor['sensor_type']
        
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
        
        # History for statistical calculations
        self.history = []
        self.history_size = 6  # 1 minute of history at 10-second intervals
    
    def inject_fault(self, duration_seconds=300, severity=0.7):
        """Inject a fault condition"""
        self.fault_active = True
        self.fault_start_time = time.time()
        self.fault_duration = duration_seconds
        self.fault_severity = severity
        logger.info(f"Fault injected: {self.sensor_id} ({self.sensor_type}), "
                   f"severity={severity:.2f}, duration={duration_seconds}s")
    
    def get_next_reading(self) -> Dict:
        """Generate next sensor reading"""
        current_time = time.time()
        
        # Check if fault is still active
        fault_factor = 0.0
        if self.fault_active:
            elapsed = current_time - self.fault_start_time
            if elapsed > self.fault_duration:
                self.fault_active = False
                logger.info(f"Fault ended: {self.sensor_id}")
            else:
                # Calculate fault progression
                progress = elapsed / self.fault_duration
                fault_factor = self.fault_severity * (0.3 + 0.7 * progress)  # Gradual increase
        
        # Generate base value
        target_value = random.uniform(self.normal_min, self.normal_max)
        
        # Apply smooth transition (avoid sudden jumps)
        if self.current_value:
            max_change = (self.normal_max - self.normal_min) * 0.1  # Max 10% change per reading
            target_value = self.current_value + np.clip(
                target_value - self.current_value, 
                -max_change, 
                max_change
            )
        
        # Apply fault effects
        if fault_factor > 0:
            if self.sensor_type == 'vibration':
                value = target_value + fault_factor * (self.critical_max - self.normal_max)
            elif self.sensor_type == 'temperature':
                value = target_value + fault_factor * (self.critical_max - self.normal_max)
            elif self.sensor_type == 'pressure':
                value = target_value - fault_factor * (self.normal_min - self.critical_min)
            elif self.sensor_type == 'current':
                value = target_value * (1.0 + fault_factor * 0.5)
            elif self.sensor_type == 'flow':
                value = target_value * random.choice([0.7, 1.3]) if fault_factor > 0.5 else target_value
            else:
                value = target_value * (1.0 + random.uniform(-0.2, 0.2) * fault_factor)
        else:
            # Small random variation
            value = target_value + random.gauss(0, (self.normal_max - self.normal_min) * 0.02)
        
        # Ensure physical limits
        value = max(self.critical_min, min(self.critical_max, value))
        self.current_value = value
        
        # Update history
        self.history.append(value)
        if len(self.history) > self.history_size:
            self.history.pop(0)
        
        # Calculate statistics
        if len(self.history) >= 2:
            min_1min = min(self.history)
            max_1min = max(self.history)
            avg_1min = sum(self.history) / len(self.history)
            std_1min = np.std(self.history)
        else:
            min_1min = max_1min = avg_1min = value
            std_1min = 0.0
        
        # Determine status
        if value < self.critical_min or value > self.critical_max:
            status = 'critical'
        elif value < self.warning_min or value > self.warning_max:
            status = 'warning'
        else:
            status = 'normal'
        
        # Anomaly detection
        anomaly_score = fault_factor * random.uniform(0.7, 1.0) if fault_factor > 0.5 else random.uniform(0, 0.3)
        is_anomaly = anomaly_score > 0.7
        
        # Build record
        record = {
            'sensor_id': self.sensor_id,
            'machine_id': self.machine_id,
            'line_id': self.sensor['line_id'],
            'factory_id': self.sensor['factory_id'],
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3],
            'measurement_value': round(value, 4),
            'measurement_unit': self.sensor['measurement_unit'],
            'status': status,
            'quality': 'good',
            'is_below_warning': value < self.warning_min,
            'is_above_warning': value > self.warning_max,
            'is_below_critical': value < self.critical_min,
            'is_above_critical': value > self.critical_max,
            'min_value_1min': round(min_1min, 4),
            'max_value_1min': round(max_1min, 4),
            'avg_value_1min': round(avg_1min, 4),
            'std_dev_1min': round(std_1min, 4),
            'anomaly_score': round(anomaly_score, 4),
            'is_anomaly': is_anomaly,
            'data_source': 'IoT',
            'protocol': self.sensor['data_protocol'],
            'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
        }
        
        return record


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
            password=PG_PASSWORD
        )
        pg_connection.autocommit = False
        logger.info(f"PostgreSQL connection established: {PG_HOST}:{PG_PORT}/{PG_DATABASE}")
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
        future.get(timeout=10)  # Wait for confirmation
        stats['kafka_sent'] += 1
        return True
    except Exception as e:
        logger.error(f"Failed to send to Kafka: {e}")
        stats['errors'] += 1
        return False


def flush_to_postgres():
    """Batch insert records to PostgreSQL"""
    global sensor_batch
    
    if not pg_connection or not sensor_batch:
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
        return True
    
    except Exception as e:
        logger.error(f"Failed to insert to PostgreSQL: {e}")
        pg_connection.rollback()
        stats['errors'] += 1
        sensor_batch = []
        return False


def print_stats():
    """Print daemon statistics"""
    elapsed = (datetime.now() - stats['start_time']).total_seconds()
    rate = stats['records_generated'] / elapsed if elapsed > 0 else 0
    
    logger.info("="*80)
    logger.info(f"IoT Daemon Statistics")
    logger.info(f"  Uptime: {elapsed:.1f} seconds")
    logger.info(f"  Records Generated: {stats['records_generated']:,}")
    logger.info(f"  Kafka Sent: {stats['kafka_sent']:,}")
    logger.info(f"  PostgreSQL Inserted: {stats['postgres_inserted']:,}")
    logger.info(f"  Errors: {stats['errors']}")
    logger.info(f"  Rate: {rate:.2f} records/sec")
    logger.info("="*80)


def load_sensors() -> List[Dict]:
    """Load sensor master data"""
    try:
        with open('genims_master_data.json', 'r') as f:
            master_data = json.load(f)
        return master_data['sensors']
    except Exception as e:
        logger.error(f"Failed to load sensors: {e}")
        return []


def main():
    """Main daemon loop"""
    logger.info("="*80)
    logger.info("GenIMS IoT Daemon Starting")
    logger.info("="*80)
    
    # Load sensors
    sensors = load_sensors()
    if not sensors:
        logger.error("No sensors loaded. Exiting.")
        return 1
    
    logger.info(f"Loaded {len(sensors)} sensors")
    
    # Initialize connections
    kafka_enabled = initialize_kafka()
    postgres_enabled = initialize_postgres()
    
    if not kafka_enabled and not postgres_enabled:
        logger.warning("Neither Kafka nor PostgreSQL available - daemon will only log to console")
    
    # Create sensor simulators
    simulators = [SensorSimulator(sensor) for sensor in sensors]
    logger.info(f"Created {len(simulators)} sensor simulators")
    
    # Randomly inject some faults for demonstration
    num_faults = int(len(simulators) * 0.05)  # 5% of sensors
    fault_sensors = random.sample(simulators, num_faults)
    for sim in fault_sensors:
        sim.inject_fault(
            duration_seconds=random.randint(300, 3600),
            severity=random.uniform(0.5, 0.9)
        )
    
    logger.info(f"Injected {num_faults} fault conditions")
    logger.info(f"Streaming interval: {SENSOR_SAMPLING_INTERVAL} seconds")
    logger.info("Press Ctrl+C to stop")
    logger.info("="*80)
    
    # Main loop
    iteration = 0
    last_stats_time = time.time()
    
    while running:
        try:
            loop_start = time.time()
            
            # Generate readings from all sensors
            for simulator in simulators:
                record = simulator.get_next_reading()
                stats['records_generated'] += 1
                
                # Send to Kafka
                if kafka_enabled:
                    send_to_kafka(record)
                
                # Add to batch for PostgreSQL
                if postgres_enabled:
                    sensor_batch.append(record)
                
                # Sample log (don't log every record)
                if random.random() < 0.001:  # 0.1% sampling
                    logger.info(f"Sample: {simulator.sensor_type} = {record['measurement_value']:.2f} "
                              f"{record['measurement_unit']} [{record['status']}]")
            
            # Flush to PostgreSQL if batch is full
            if len(sensor_batch) >= BATCH_SIZE and postgres_enabled:
                flush_to_postgres()
            
            # Print stats every 60 seconds
            if time.time() - last_stats_time > 60:
                print_stats()
                last_stats_time = time.time()
            
            # Sleep to maintain interval
            elapsed = time.time() - loop_start
            sleep_time = max(0, SENSOR_SAMPLING_INTERVAL - elapsed)
            
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
    if postgres_enabled and sensor_batch:
        flush_to_postgres()
    
    # Close connections
    if kafka_producer:
        kafka_producer.close()
        logger.info("Kafka producer closed")
    
    if pg_connection:
        pg_connection.close()
        logger.info("PostgreSQL connection closed")
    
    print_stats()
    logger.info("IoT Daemon stopped")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
