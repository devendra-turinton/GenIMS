#!/usr/bin/env python3
"""
GenIMS HR/HCM Daemon - ULTRA FAST MODE
Generates complete HR operations in-memory, then bulk dumps to PostgreSQL
"""

import sys
import os
import time
import logging
import signal
from datetime import datetime, timedelta, time as dt_time
import random
from dotenv import load_dotenv

env_file = os.path.join(os.path.dirname(__file__), '..', '..', 'scripts', 'config.env')
if os.path.exists(env_file):
    load_dotenv(env_file)

# Add scripts to path for helper access
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'scripts'))

try:
    from data_registry import get_helper
    HELPER_AVAILABLE = True
except ImportError:
    HELPER_AVAILABLE = False
    print("Warning: Helper/registry not available")

try:
    import psycopg2
    from psycopg2.extras import execute_batch
    POSTGRES_AVAILABLE = True
except ImportError:
    POSTGRES_AVAILABLE = False

# Configuration
PG_HOST = os.getenv('POSTGRES_HOST', 'localhost')
PG_PORT = int(os.getenv('POSTGRES_PORT', '5432'))
PG_USER = os.getenv('POSTGRES_USER', 'postgres')
PG_PASSWORD = os.getenv('POSTGRES_PASSWORD', '')
PG_SSL_MODE = os.getenv('PG_SSL_MODE', 'require')

PG_HR_DB = os.getenv('DB_HR', 'genims_hr_db')

BATCH_SIZE = 5000
# Daily HR operations: ~11,000 attendance + ~50 leave requests + ~20 reviews + ~30 incidents = ~11,100 total
TOTAL_RECORDS = 11200  # Daily HR operations for 10,984 employees across 4 factories

# Logging
log_dir = os.getenv('DAEMON_LOG_DIR', os.path.join(os.path.dirname(__file__), '..', '..', 'logs'))
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, 'hcm_daemon.log')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('HCMDaemon')

class TimeCoordinator:
    """Manages time coordination and validation for HCM operations"""
    def __init__(self):
        self.base_time = self.get_validated_base_time()
    
    def get_validated_base_time(self):
        """Always return current datetime for today's data generation"""
        # ALWAYS use current datetime for today's generation (no historical continuation)
        current_datetime = datetime.now()
        base_time = current_datetime.replace(hour=0, minute=0, second=0, microsecond=0)
        logger.info(f"Using current date for data generation: {base_time}")
        return base_time
    
    def get_current_time(self):
        """Get the current base time"""
        return self.base_time
    
    def add_time_offset(self, seconds):
        """Add time offset to base time"""
        return self.base_time + timedelta(seconds=seconds)
    
    def coordination_delay(self, operation_name, delay_seconds=2):
        """Add coordination delay between operations"""
        logger.info(f"Time coordination delay for {operation_name}: {delay_seconds}s")
        time.sleep(delay_seconds)

# Global State
pg_connection = None
master_data = {}
counters = {
    'attendance': 1, 'leave_request': 1, 'review': 1, 'enrollment': 1, 'incident': 1
}

def signal_handler(sig, frame):
    logger.info("Shutdown signal received")
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

def initialize_database():
    global pg_connection
    if not POSTGRES_AVAILABLE:
        return False
    try:
        pg_connection = psycopg2.connect(
            host=PG_HOST, port=PG_PORT, database=PG_HR_DB,
            user=PG_USER, password=PG_PASSWORD, sslmode=PG_SSL_MODE, connect_timeout=30
        )
        pg_connection.autocommit = False
        logger.info(f"PostgreSQL connection established: {PG_HOST}:{PG_PORT}/{PG_HR_DB}")
        return True
    except Exception as e:
        logger.error(f"PostgreSQL connection failed: {e}")
        return False

def get_table_count(table_name):
    try:
        conn = psycopg2.connect(host=PG_HOST, port=PG_PORT, database=PG_HR_DB,
            user=PG_USER, password=PG_PASSWORD, sslmode=PG_SSL_MODE, connect_timeout=10)
        cursor = conn.cursor()
        cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
        count = cursor.fetchone()[0]
        cursor.close()
        conn.close()
        return count
    except Exception as e:
        logger.warning(f"Could not get {table_name} count: {e}")
        return None

def get_all_table_counts():
    tables = ['attendance_records', 'leave_requests', 'performance_reviews', 'training_enrollments', 'safety_incidents']
    counts = {}
    for table in tables:
        counts[table] = get_table_count(table)
    return counts

def get_max_id_counter(table_name, id_column):
    """Get the next ID counter for a given table"""
    try:
        cursor = pg_connection.cursor()
        cursor.execute(f"SELECT MAX(CAST(SUBSTRING({id_column}, '\\d+$') AS INTEGER)) FROM {table_name}")
        max_id = cursor.fetchone()[0]
        cursor.close()
        return (max_id or 0) + 1
    except Exception as e:
        logger.debug(f"Could not get max ID from {table_name}.{id_column}: {e}")
        return 1

def initialize_id_counters():
    """Initialize counters from existing data in database"""
    global counters
    try:
        counters['attendance'] = get_max_id_counter('attendance_records', 'attendance_id')
        counters['leave_request'] = get_max_id_counter('leave_requests', 'request_id')
        counters['review'] = get_max_id_counter('performance_reviews', 'review_id')
        counters['enrollment'] = get_max_id_counter('training_enrollments', 'enrollment_id')
        counters['incident'] = get_max_id_counter('safety_incidents', 'incident_id')
        
        logger.info(f"ID Counters initialized: {counters}")
        return True
    except Exception as e:
        logger.error(f"Failed to initialize ID counters: {e}")
        return False

def load_master_data():
    global master_data
    try:
        conn = psycopg2.connect(
            host=PG_HOST, port=PG_PORT, database=PG_HR_DB,
            user=PG_USER, password=PG_PASSWORD, sslmode=PG_SSL_MODE, connect_timeout=30
        )
        cursor = conn.cursor()
        
        # Load employees
        cursor.execute("SELECT employee_id FROM employees LIMIT 200")
        employees = [row[0] for row in cursor.fetchall()]
        
        # Load departments
        cursor.execute("SELECT department_id FROM departments LIMIT 50")
        departments = [row[0] for row in cursor.fetchall()]
        
        # Load shifts
        cursor.execute("SELECT shift_id FROM shift_schedules LIMIT 20")
        shifts = [row[0] for row in cursor.fetchall()]
        
        # Load leave types
        cursor.execute("SELECT leave_type_id FROM leave_types LIMIT 10")
        leave_types = [row[0] for row in cursor.fetchall()]
        
        # Load training schedules
        cursor.execute("SELECT schedule_id FROM training_schedules LIMIT 30")
        training_schedules = [row[0] for row in cursor.fetchall()]
        
        # Load existing enrollment combinations to avoid duplicates
        cursor.execute("SELECT schedule_id, employee_id FROM training_enrollments")
        existing_enrollments = set(cursor.fetchall())
        
        # Load existing attendance combinations (last 60 days only for memory efficiency)
        cursor.execute("SELECT employee_id, attendance_date FROM attendance_records WHERE attendance_date >= CURRENT_DATE - INTERVAL '60 days'")
        existing_attendance = set(cursor.fetchall())
        
        cursor.close()
        conn.close()
        
        master_data['employees'] = employees or ['EMP-000001', 'EMP-000002']
        master_data['departments'] = departments or ['DEPT-000001']
        master_data['shifts'] = shifts or ['SHIFT-DAY']
        master_data['leave_types'] = leave_types or ['LVT-000001']
        master_data['training_schedules'] = training_schedules or ['TS-000001']
        master_data['existing_enrollments'] = existing_enrollments
        master_data['existing_attendance'] = existing_attendance
        
        # Load registry validated employee IDs for assignments
        if HELPER_AVAILABLE:
            try:
                helper = get_helper()
                valid_employee_ids = list(helper.get_valid_employee_ids())
                if valid_employee_ids:
                    master_data['valid_employees'] = valid_employee_ids
                    logger.info(f"Registry validation: {len(valid_employee_ids)} validated employee IDs loaded")
                else:
                    logger.warning("No valid employee IDs from registry, using HR employees")
                    master_data['valid_employees'] = employees
            except Exception as e:
                logger.warning(f"Registry validation failed: {e}, using HR employees")
                master_data['valid_employees'] = employees
        else:
            master_data['valid_employees'] = employees
        
        logger.info(f"Master data loaded: {len(employees)} employees, {len(departments)} departments, {len(shifts)} shifts, {len(leave_types)} leave types, {len(training_schedules)} training schedules")
        logger.info(f"Existing data: {len(existing_enrollments)} enrollments, {len(existing_attendance)} attendance records")
        return True
    except Exception as e:
        logger.error(f"Failed to load master data: {e}")
        return False

def insert_batch_parallel(cursor, insert_sql, data, table_name, batch_size, connection=None):
    """Insert data in batches with proper error handling"""
    total_batches = (len(data) + batch_size - 1) // batch_size
    successful_inserts = 0
    
    for batch_idx in range(total_batches):
        try:
            batch_start = batch_idx * batch_size
            batch_end = min((batch_idx + 1) * batch_size, len(data))
            batch = data[batch_start:batch_end]
            
            execute_batch(cursor, insert_sql, batch, page_size=5000)
            if connection:
                connection.commit()
            
            successful_inserts += len(batch)
            logger.info(f"  Flushed {batch_end:,} / {len(data):,} {table_name}")
        except psycopg2.IntegrityError as e:
            logger.warning(f"  Batch {batch_idx + 1}/{total_batches} - Integrity error: {str(e)[:100]}")
            logger.warning(f"  This may indicate FK constraint violations or duplicate keys")
            if connection:
                connection.rollback()
        except psycopg2.Error as e:
            logger.error(f"  Batch {batch_idx + 1}/{total_batches} - Database error: {str(e)[:200]}")
            if connection:
                connection.rollback()
        except Exception as e:
            logger.error(f"  Batch {batch_idx + 1}/{total_batches} - Unexpected error: {e}")
            if connection:
                connection.rollback()
    
    logger.info(f"  Successfully inserted {successful_inserts:,}/{len(data):,} {table_name} records")
    return successful_inserts

def main():
    """Main - Generate all HR data in-memory, then bulk dump"""
    logger.info("="*80)
    logger.info("GenIMS HR/HCM Daemon - ULTRA FAST MODE (In-Memory Generation)")
    logger.info("="*80)
    logger.info(f"Configuration:")
    logger.info(f"  Database: {PG_HR_DB}")
    logger.info(f"  Batch Size: {BATCH_SIZE}")
    logger.info("="*80)
    
    # Initialize time coordinator and helper
    time_coord = TimeCoordinator()
    logger.info(f"Time Coordinator initialized: {time_coord.get_current_time()}")
    
    if HELPER_AVAILABLE:
        try:
            helper = get_helper()
            # Get total registered IDs for logging
            total_ids = sum(len(ids) for ids in helper.registry.registered_ids.values()) if hasattr(helper.registry, 'registered_ids') else 0
            logger.info(f"Registry helper loaded with {total_ids} total registered IDs")
        except Exception as e:
            logger.warning(f"Helper initialization failed: {e}")
            helper = None
    
    start_time = time.time()
    
    # Initialize
    if not initialize_database():
        return 1
    
    if not initialize_id_counters():
        return 1
    
    if not load_master_data():
        return 1
    
    logger.info("="*80)
    logger.info("📊 BASELINE DATABASE COUNTS (Before Generation)")
    logger.info("="*80)
    counts_before = get_all_table_counts()
    for table, count in counts_before.items():
        if count is not None:
            logger.info(f"  {table:.<40} {count:>10,} records")
    logger.info("="*80)
    
    logger.info("="*80)
    logger.info("GENERATING ALL DATA IN MEMORY...")
    logger.info("="*80)
    
    # Generate data
    attendance_records = []
    leave_requests = []
    performance_reviews = []
    training_enrollments = []
    safety_incidents = []
    
    # Use time coordinator for synchronized timestamps
    sim_base_time = time_coord.get_current_time().replace(hour=0, minute=0, second=0, microsecond=0)
    # Use current datetime with milliseconds to ensure uniqueness across runs
    current_time = datetime.now()
    run_timestamp = current_time.strftime('%Y%m%d%H%M%S') + f"{current_time.microsecond // 1000:03d}"
    
    # Validate FK availability
    if not master_data['employees'] or not master_data['departments'] or not master_data['shifts']:
        logger.error("Critical: Missing master data for FK references")
        return 1
    
    # Get validated employee IDs for assignment
    valid_employee_ids = master_data.get('valid_employees', master_data['employees'])
    logger.info(f"FK Validation: {len(master_data['employees'])} employees, {len(master_data['departments'])} departments, {len(valid_employee_ids)} validated employees")
    
    # Track unique combinations to avoid UNIQUE constraint violations
    # Initialize with existing database data
    attendance_seen = set(master_data.get('existing_attendance', set()))
    enrollment_seen = set(master_data.get('existing_enrollments', set()))
    
    # Generate HR records for single business day
    for i in range(TOTAL_RECORDS):
        # Spread records throughout business day for HR operations  
        timestamp_offset = i * 300  # 5 minute intervals
        current_ts = time_coord.add_time_offset(timestamp_offset)
        current_date = current_ts.date()
        
        # Validated FK selection
        try:
            employee = random.choice(master_data['employees'])
            department = random.choice(master_data['departments'])
            shift = random.choice(master_data['shifts'])
            assigned_employee = random.choice(valid_employee_ids)
        except IndexError:
            logger.error(f"FK reference error at record {i}")
            continue
        
        # Attendance Records (generate for most employees daily - ~98% attendance rate)
        # Generate attendance record for almost every iteration to cover 10,984 employees
        # UNIQUE constraint: (employee_id, attendance_date)
        attendance_key = (employee, current_date)
        if attendance_key not in attendance_seen and random.random() < 0.98:  # 98% attendance rate
            attendance_seen.add(attendance_key)
            attendance_id = f"ATT-{(counters['attendance'] + len(attendance_records)):06d}"
            clock_in = current_ts.replace(hour=8, minute=random.randint(0, 30))
            clock_out = current_ts.replace(hour=17, minute=random.randint(0, 30))
            actual_hrs = round((clock_out - clock_in).seconds / 3600, 2)
            
            attendance_records.append({
                'attendance_id': attendance_id,
                'employee_id': employee,
                'attendance_date': current_date,
                'shift_id': shift,
                'clock_in_time': clock_in,
                'clock_out_time': clock_out,
                'scheduled_hours': 8.0,
                'actual_hours': actual_hrs,
                'regular_hours': min(actual_hrs, 8.0),
                'overtime_hours': max(0, actual_hrs - 8.0),
                'attendance_status': random.choice(['Present', 'Absent', 'Late', 'Half Day']),
                'late_minutes': random.randint(0, 30) if random.random() > 0.7 else 0,
                'created_at': current_ts
            })
        
        # Leave Requests (daily target: ~110 leave requests for 10,984 employees)
        # Generate leave request every ~100 records to achieve ~110 requests per day
        if i % 100 == 0:
            request_id = f"LR-{(counters['leave_request'] + i // 100):06d}"
            leave_type = random.choice(master_data['leave_types'])
            start_date = current_date + timedelta(days=random.randint(1, 30))
            end_date = start_date + timedelta(days=random.randint(1, 5))
            total_days = (end_date - start_date).days + 1
            
            leave_requests.append({
                'request_id': request_id,
                'employee_id': employee,
                'leave_type_id': leave_type,
                'request_date': current_date,
                'start_date': start_date,
                'end_date': end_date,
                'total_days': total_days,
                'is_half_day': random.choice([True, False]) if total_days == 1 else False,
                'request_status': random.choice(['Pending', 'Approved', 'Rejected', 'Cancelled']),
                'approved_by': assigned_employee if random.random() > 0.3 else None,
                'approval_date': current_date + timedelta(days=1) if random.random() > 0.3 else None,
                'created_at': current_ts
            })
        
        # Performance Reviews (daily target: ~50 performance reviews)
        # Generate performance review every ~224 records to achieve ~50 reviews per day
        if i % 224 == 0:
            review_id = f"REV-{(counters['review'] + i // 224):06d}"
            review_start = current_date - timedelta(days=90)
            review_end = current_date
            
            performance_reviews.append({
                'review_id': review_id,
                'employee_id': employee,
                'review_type': random.choice(['Annual', 'Mid-Year', 'Quarterly', 'Probation']),
                'review_period_start': review_start,
                'review_period_end': review_end,
                'reviewer_id': assigned_employee,
                'review_date': current_date,
                'overall_rating': round(random.uniform(2.5, 5.0), 1),
                'performance_level': random.choice(['Exceeds', 'Meets', 'Below', 'Outstanding']),
                'technical_competency_rating': round(random.uniform(2.5, 5.0), 1),
                'behavioral_competency_rating': round(random.uniform(2.5, 5.0), 1),
                'goals_achieved': random.randint(1, 5),
                'created_at': current_ts
            })
        
        # Training Enrollments (daily target: ~150 training enrollments)
        # UNIQUE constraint: (schedule_id, employee_id)
        # Generate training enrollment every ~75 records to achieve ~150 enrollments per day
        if i % 75 == 0:
            schedule = random.choice(master_data['training_schedules'])
            enrollment_key = (schedule, employee)
            
            # Only add if not already enrolled
            if enrollment_key not in enrollment_seen:
                enrollment_seen.add(enrollment_key)
                enrollment_id = f"ENR-{(counters['enrollment'] + len(training_enrollments)):06d}"
                
                training_enrollments.append({
                    'enrollment_id': enrollment_id,
                    'schedule_id': schedule,
                    'employee_id': employee,
                    'enrollment_date': current_date,
                    'enrollment_status': random.choice(['Enrolled', 'Completed', 'Cancelled', 'No-Show']),
                    'attended': random.choice([True, False]),
                    'attendance_date': current_date + timedelta(days=random.randint(1, 7)) if random.random() > 0.3 else None,
                    'attendance_hours': round(random.uniform(2, 8), 1) if random.random() > 0.3 else None,
                    'assessment_score': round(random.uniform(50, 100), 1) if random.random() > 0.4 else None,
                    'passed': random.choice([True, False]) if random.random() > 0.4 else None,
                    'completion_status': random.choice(['Completed', 'In Progress', 'Not Started']),
                    'completion_date': current_date + timedelta(days=random.randint(1, 14)) if random.random() > 0.5 else None,
                    'created_at': current_ts
                })
        
        # Safety Incidents (daily target: ~22 safety incidents)
        # Generate safety incident every ~500 records to achieve ~22 incidents per day
        if i % 500 == 0:
            incident_id = f"INC-{(counters['incident'] + i // 500):06d}"
            incident_num = f"SI-{run_timestamp}-{i // 500:04d}"
            
            safety_incidents.append({
                'incident_id': incident_id,
                'incident_number': incident_num,
                'employee_id': employee,
                'incident_date': current_date,
                'incident_time': dt_time(random.randint(8, 17), random.randint(0, 59)),
                'department_id': department,
                'incident_type': random.choice(['Injury', 'Near Miss', 'Property Damage', 'Equipment Failure']),
                'severity': random.choice(['Minor', 'Moderate', 'Serious', 'Critical']),
                'description': f"Safety incident {i // 500}",
                'injury_type': random.choice(['Cut', 'Burn', 'Strain', 'Fracture', 'None']) if random.random() > 0.3 else None,
                'body_part_affected': random.choice(['Hand', 'Foot', 'Back', 'Head', 'Leg']) if random.random() > 0.3 else None,
                'created_at': current_ts
            })
        
        if (i + 1) % 2000 == 0:
            logger.info(f"  Generated {i + 1:,} / {TOTAL_RECORDS:,} records")
    
    logger.info(f"✓ Generated {len(attendance_records):,} attendance records")
    logger.info(f"✓ Generated {len(leave_requests):,} leave requests")
    logger.info(f"✓ Generated {len(performance_reviews):,} performance reviews")
    logger.info(f"✓ Generated {len(training_enrollments):,} training enrollments")
    logger.info(f"✓ Generated {len(safety_incidents):,} safety incidents")
    
    # Bulk dump to PostgreSQL
    logger.info("="*80)
    logger.info("BULK DUMPING TO POSTGRESQL...")
    logger.info("="*80)
    
    try:
        cursor = pg_connection.cursor()
        cursor.execute("SET CONSTRAINTS ALL DEFERRED;")
        
        # Insert attendance records
        if attendance_records:
            insert_sql = """INSERT INTO attendance_records (
                attendance_id, employee_id, attendance_date, shift_id, clock_in_time,
                clock_out_time, scheduled_hours, actual_hours, regular_hours, overtime_hours,
                attendance_status, late_minutes, created_at
            ) VALUES (%(attendance_id)s, %(employee_id)s, %(attendance_date)s, %(shift_id)s,
                %(clock_in_time)s, %(clock_out_time)s, %(scheduled_hours)s, %(actual_hours)s,
                %(regular_hours)s, %(overtime_hours)s, %(attendance_status)s, %(late_minutes)s,
                %(created_at)s)"""
            logger.info(f"Inserting {len(attendance_records):,} attendance records...")
            insert_batch_parallel(cursor, insert_sql, attendance_records, "attendance_records", BATCH_SIZE, pg_connection)
            time_coord.coordination_delay("attendance_records")
        
        # Insert leave requests
        if leave_requests:
            insert_sql = """INSERT INTO leave_requests (
                request_id, employee_id, leave_type_id, request_date, start_date, end_date,
                total_days, is_half_day, request_status, approved_by, approval_date, created_at
            ) VALUES (%(request_id)s, %(employee_id)s, %(leave_type_id)s, %(request_date)s,
                %(start_date)s, %(end_date)s, %(total_days)s, %(is_half_day)s, %(request_status)s,
                %(approved_by)s, %(approval_date)s, %(created_at)s)"""
            logger.info(f"Inserting {len(leave_requests):,} leave requests...")
            insert_batch_parallel(cursor, insert_sql, leave_requests, "leave_requests", BATCH_SIZE, pg_connection)
            time_coord.coordination_delay("leave_requests")
        
        # Insert performance reviews
        if performance_reviews:
            insert_sql = """INSERT INTO performance_reviews (
                review_id, employee_id, review_type, review_period_start, review_period_end,
                reviewer_id, review_date, overall_rating, performance_level,
                technical_competency_rating, behavioral_competency_rating, goals_achieved, created_at
            ) VALUES (%(review_id)s, %(employee_id)s, %(review_type)s, %(review_period_start)s,
                %(review_period_end)s, %(reviewer_id)s, %(review_date)s, %(overall_rating)s,
                %(performance_level)s, %(technical_competency_rating)s,
                %(behavioral_competency_rating)s, %(goals_achieved)s, %(created_at)s)"""
            logger.info(f"Inserting {len(performance_reviews):,} performance reviews...")
            insert_batch_parallel(cursor, insert_sql, performance_reviews, "performance_reviews", BATCH_SIZE, pg_connection)
            time_coord.coordination_delay("performance_reviews")
        
        # Insert training enrollments
        if training_enrollments:
            insert_sql = """INSERT INTO training_enrollments (
                enrollment_id, schedule_id, employee_id, enrollment_date, enrollment_status,
                attended, attendance_date, attendance_hours, assessment_score, passed,
                completion_status, completion_date, created_at
            ) VALUES (%(enrollment_id)s, %(schedule_id)s, %(employee_id)s, %(enrollment_date)s,
                %(enrollment_status)s, %(attended)s, %(attendance_date)s, %(attendance_hours)s,
                %(assessment_score)s, %(passed)s, %(completion_status)s, %(completion_date)s,
                %(created_at)s)"""
            logger.info(f"Inserting {len(training_enrollments):,} training enrollments...")
            insert_batch_parallel(cursor, insert_sql, training_enrollments, "training_enrollments", BATCH_SIZE, pg_connection)
            time_coord.coordination_delay("training_enrollments")
        
        # Insert safety incidents
        if safety_incidents:
            insert_sql = """INSERT INTO safety_incidents (
                incident_id, incident_number, employee_id, incident_date, incident_time,
                department_id, incident_type, severity, description, injury_type,
                body_part_affected, created_at
            ) VALUES (%(incident_id)s, %(incident_number)s, %(employee_id)s, %(incident_date)s,
                %(incident_time)s, %(department_id)s, %(incident_type)s, %(severity)s,
                %(description)s, %(injury_type)s, %(body_part_affected)s, %(created_at)s)"""
            logger.info(f"Inserting {len(safety_incidents):,} safety incidents...")
            insert_batch_parallel(cursor, insert_sql, safety_incidents, "safety_incidents", BATCH_SIZE, pg_connection)
            time_coord.coordination_delay("safety_incidents")
        
        cursor.close()
        
        # Commit all data
        pg_connection.commit()
        
        logger.info(f"✓ All records inserted successfully")
    except Exception as e:
        logger.error(f"PostgreSQL error: {e}")
        return 1
    
    elapsed = time.time() - start_time
    
    # Get final counts
    counts_after = get_all_table_counts()
    
    logger.info("="*80)
    logger.info("GENERATION & INSERTION COMPLETE")
    logger.info("="*80)
    logger.info(f"  Total time: {elapsed:.1f} seconds ({elapsed/60:.1f} minutes)")
    logger.info("")
    logger.info("📊 DATABASE SUMMARY")
    logger.info("="*80)
    
    tables_list = ['attendance_records', 'leave_requests', 'performance_reviews', 'training_enrollments', 'safety_incidents']
    for table in tables_list:
        before = counts_before.get(table)
        after = counts_after.get(table)
        
        if before is not None and after is not None:
            inserted = after - before
            logger.info(f"{table:.<40} Before: {before:>10,} | After: {after:>10,} | Inserted: {inserted:>10,}")
    
    logger.info("="*80)
    
    if pg_connection:
        pg_connection.close()
    
    return 0

if __name__ == "__main__":
    os.makedirs('logs', exist_ok=True)
    sys.exit(main())
