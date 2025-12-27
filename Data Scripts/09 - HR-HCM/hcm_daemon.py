#!/usr/bin/env python3
"""
GenIMS HR/HCM Daemon
Continuous HR operations (training compliance, certifications, leave, etc.)
"""

import sys
import time
import logging
import signal
from datetime import datetime, timedelta
import random
import json

try:
    import psycopg2
    from psycopg2.extras import execute_batch
    POSTGRES_AVAILABLE = True
except ImportError:
    POSTGRES_AVAILABLE = False
    print("WARNING: psycopg2 not installed")

# Configuration
PG_HOST = 'localhost'
PG_PORT = 5432
PG_DATABASE = 'genims_db'
PG_USER = 'genims_user'
PG_PASSWORD = 'genims_password'

# HCM Configuration
CYCLE_INTERVAL_SECONDS = 3600  # Run every hour

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/hcm_daemon.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('HCMDaemon')

running = True
pg_connection = None
master_data = {}
stats = {
    'cycles': 0,
    'certifications_alerted': 0,
    'training_scheduled': 0,
    'leave_requests_processed': 0,
    'onboarding_tracked': 0,
    'performance_reviews_due': 0,
    'safety_incidents_reviewed': 0,
    'start_time': datetime.now()
}

def signal_handler(sig, frame):
    global running
    logger.info("Shutdown signal received")
    running = False

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

def initialize_database():
    global pg_connection
    if not POSTGRES_AVAILABLE:
        return False
    try:
        pg_connection = psycopg2.connect(
            host=PG_HOST, port=PG_PORT, database=PG_DATABASE,
            user=PG_USER, password=PG_PASSWORD
        )
        pg_connection.autocommit = False
        logger.info("PostgreSQL connected")
        return True
    except Exception as e:
        logger.error(f"DB connection failed: {e}")
        return False

def load_master_data():
    global master_data
    try:
        cursor = pg_connection.cursor()
        
        # Load employees
        cursor.execute("SELECT * FROM employees WHERE employment_status = 'active' LIMIT 100")
        master_data['employees'] = [dict(zip([d[0] for d in cursor.description], row)) 
                                    for row in cursor.fetchall()]
        
        # Load training courses
        cursor.execute("SELECT * FROM training_courses WHERE is_active = true")
        master_data['training_courses'] = [dict(zip([d[0] for d in cursor.description], row)) 
                                          for row in cursor.fetchall()]
        
        cursor.close()
        logger.info(f"Loaded: {len(master_data.get('employees', []))} employees, "
                   f"{len(master_data.get('training_courses', []))} courses")
        return True
    except Exception as e:
        logger.error(f"Failed to load master data: {e}")
        return False

def generate_id(prefix: str) -> str:
    return f"{prefix}-{datetime.now().strftime('%Y%m%d%H%M%S')}-{random.randint(1000, 9999)}"

# ============================================================================
# CERTIFICATION MANAGEMENT
# ============================================================================

def monitor_certification_expiry():
    """Monitor and alert on expiring certifications"""
    logger.info("Monitoring certification expiry...")
    
    try:
        cursor = pg_connection.cursor()
        
        # Get certifications expiring in 90, 60, 30 days
        for days in [90, 60, 30]:
            cursor.execute("""
                SELECT certification_id, employee_id, certification_name, expiry_date
                FROM employee_certifications
                WHERE certification_status = 'active'
                AND requires_renewal = true
                AND expiry_date <= %s
                AND expiry_date > CURRENT_DATE
                AND (
                    (expiry_date - CURRENT_DATE) = %s
                    OR (expiry_alert_sent = false AND (expiry_date - CURRENT_DATE) <= %s)
                )
            """, ((datetime.now() + timedelta(days=days)).date(), days, days))
            
            certs = cursor.fetchall()
            
            for cert_id, emp_id, cert_name, expiry_date in certs:
                # Log alert (in production, would send email/notification)
                logger.info(f"ALERT: Certification {cert_name} for employee {emp_id} expires in {days} days")
                
                # Mark alert as sent
                cursor.execute("""
                    UPDATE employee_certifications
                    SET expiry_alert_sent = true
                    WHERE certification_id = %s
                """, (cert_id,))
                
                stats['certifications_alerted'] += 1
        
        # Mark expired certifications
        cursor.execute("""
            UPDATE employee_certifications
            SET certification_status = 'expired'
            WHERE certification_status = 'active'
            AND expiry_date < CURRENT_DATE
        """)
        
        pg_connection.commit()
        cursor.close()
    except Exception as e:
        logger.error(f"Error monitoring certifications: {e}")
        pg_connection.rollback()

# ============================================================================
# TRAINING COMPLIANCE
# ============================================================================

def check_training_compliance():
    """Check training compliance and identify overdue trainings"""
    logger.info("Checking training compliance...")
    
    try:
        cursor = pg_connection.cursor()
        
        # Find employees with overdue mandatory trainings
        cursor.execute("""
            SELECT DISTINCT
                e.employee_id,
                e.first_name || ' ' || e.last_name as employee_name,
                tc.course_name,
                tr.requirement_type,
                tr.frequency
            FROM employees e
            CROSS JOIN training_requirements tr
            JOIN training_courses tc ON tr.course_id = tc.course_id
            WHERE e.employment_status = 'active'
            AND tr.is_mandatory = true
            AND tr.is_active = true
            AND (
                (tr.requirement_type = 'role_based' AND tr.role_id = (
                    SELECT role_id FROM positions WHERE position_id = e.primary_position_id
                ))
                OR (tr.requirement_type = 'location_based' AND tr.factory_id = e.primary_factory_id)
            )
            AND NOT EXISTS (
                SELECT 1 FROM training_enrollments ten
                JOIN training_schedules ts ON ten.schedule_id = ts.schedule_id
                WHERE ten.employee_id = e.employee_id
                AND ts.course_id = tc.course_id
                AND ten.completion_status = 'completed'
                AND (
                    tr.frequency = 'one_time'
                    OR (tr.frequency = 'annual' AND ten.completion_date >= CURRENT_DATE - INTERVAL '1 year')
                    OR (tr.frequency = 'biennial' AND ten.completion_date >= CURRENT_DATE - INTERVAL '2 years')
                )
            )
            LIMIT 20
        """)
        
        overdue = cursor.fetchall()
        
        for emp_id, emp_name, course_name, req_type, frequency in overdue:
            logger.info(f"COMPLIANCE: Employee {emp_name} needs {course_name} ({frequency})")
        
        cursor.close()
        
        if overdue:
            logger.info(f"Found {len(overdue)} overdue training requirements")
    except Exception as e:
        logger.error(f"Error checking training compliance: {e}")

def auto_schedule_mandatory_training():
    """Auto-schedule mandatory training sessions"""
    logger.info("Auto-scheduling mandatory training...")
    
    if not master_data.get('training_courses'):
        return
    
    try:
        cursor = pg_connection.cursor()
        
        # Create training schedules for next month
        for course in random.sample(master_data['training_courses'], 
                                   min(3, len(master_data['training_courses']))):
            
            # Check if already scheduled for next 30 days
            cursor.execute("""
                SELECT COUNT(*) FROM training_schedules
                WHERE course_id = %s
                AND start_datetime >= CURRENT_DATE
                AND start_datetime <= CURRENT_DATE + INTERVAL '30 days'
            """, (course['course_id'],))
            
            if cursor.fetchone()[0] == 0:
                # Schedule new session
                schedule_id = generate_id('SCHED')
                start_datetime = datetime.now() + timedelta(days=random.randint(7, 30))
                
                cursor.execute("""
                    INSERT INTO training_schedules (
                        schedule_id, course_id, session_name,
                        start_datetime, end_datetime,
                        max_participants, schedule_status, created_at
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """, (schedule_id, course['course_id'],
                      f"{course['course_name']} - Auto Scheduled",
                      start_datetime, 
                      start_datetime + timedelta(hours=int(course.get('duration_hours', 8))),
                      20, 'scheduled', datetime.now()))
                
                stats['training_scheduled'] += 1
                logger.info(f"Scheduled: {course['course_name']}")
        
        pg_connection.commit()
        cursor.close()
    except Exception as e:
        logger.error(f"Error scheduling training: {e}")
        pg_connection.rollback()

# ============================================================================
# LEAVE MANAGEMENT
# ============================================================================

def process_pending_leave_requests():
    """Process pending leave requests (auto-approve if criteria met)"""
    logger.info("Processing pending leave requests...")
    
    try:
        cursor = pg_connection.cursor()
        
        # Auto-approve leave requests meeting criteria
        # (Small requests, sufficient balance, advance notice)
        cursor.execute("""
            SELECT lr.request_id, lr.employee_id, lr.total_days,
                   lr.start_date, elb.available_balance
            FROM leave_requests lr
            JOIN employee_leave_balances elb ON 
                lr.employee_id = elb.employee_id 
                AND lr.leave_type_id = elb.leave_type_id
                AND elb.leave_year = EXTRACT(YEAR FROM lr.start_date)
            WHERE lr.request_status = 'pending'
            AND lr.total_days <= 3
            AND lr.start_date > CURRENT_DATE + INTERVAL '7 days'
            AND elb.available_balance >= lr.total_days
            LIMIT 10
        """)
        
        requests = cursor.fetchall()
        
        for req_id, emp_id, days, start_date, balance in requests:
            # Auto-approve
            cursor.execute("""
                UPDATE leave_requests
                SET request_status = 'approved',
                    approval_date = %s
                WHERE request_id = %s
            """, (datetime.now().date(), req_id))
            
            # Update balance
            cursor.execute("""
                UPDATE employee_leave_balances
                SET used_days = used_days + %s,
                    available_balance = available_balance - %s
                WHERE employee_id = %s
                AND leave_year = EXTRACT(YEAR FROM %s)
            """, (days, days, emp_id, start_date))
            
            stats['leave_requests_processed'] += 1
            logger.info(f"Approved leave request: {req_id}")
        
        pg_connection.commit()
        cursor.close()
        
        if requests:
            logger.info(f"Processed {len(requests)} leave requests")
    except Exception as e:
        logger.error(f"Error processing leave requests: {e}")
        pg_connection.rollback()

def update_leave_balances():
    """Update monthly leave accruals"""
    logger.info("Updating leave balances...")
    
    try:
        cursor = pg_connection.cursor()
        
        # Check if accrual already done this month
        current_year = datetime.now().year
        current_month = datetime.now().month
        
        # For simplicity, update balances for active employees
        cursor.execute("""
            UPDATE employee_leave_balances elb
            SET accrued_days = accrued_days + lt.accrual_rate,
                available_balance = opening_balance + accrued_days - used_days
            FROM leave_types lt, employees e
            WHERE elb.leave_type_id = lt.leave_type_id
            AND elb.employee_id = e.employee_id
            AND e.employment_status = 'active'
            AND lt.accrual_enabled = true
            AND elb.leave_year = %s
        """, (current_year,))
        
        pg_connection.commit()
        cursor.close()
    except Exception as e:
        logger.error(f"Error updating leave balances: {e}")
        pg_connection.rollback()

# ============================================================================
# ONBOARDING TRACKING
# ============================================================================

def track_onboarding_progress():
    """Track and alert on onboarding progress"""
    logger.info("Tracking onboarding progress...")
    
    try:
        cursor = pg_connection.cursor()
        
        # Get onboarding in progress
        cursor.execute("""
            SELECT eo.onboarding_id, e.employee_id,
                   e.first_name || ' ' || e.last_name as employee_name,
                   e.hire_date, eo.completion_pct
            FROM employee_onboarding eo
            JOIN employees e ON eo.employee_id = e.employee_id
            WHERE eo.onboarding_status = 'in_progress'
            AND eo.onboarding_start_date < CURRENT_DATE - INTERVAL '7 days'
            LIMIT 10
        """)
        
        onboardings = cursor.fetchall()
        
        for onb_id, emp_id, emp_name, hire_date, completion_pct in onboardings:
            days_since_hire = (datetime.now().date() - hire_date).days
            
            if completion_pct < 50 and days_since_hire > 14:
                logger.info(f"ALERT: Onboarding delayed for {emp_name} - {completion_pct}% complete")
                stats['onboarding_tracked'] += 1
        
        cursor.close()
    except Exception as e:
        logger.error(f"Error tracking onboarding: {e}")

# ============================================================================
# PERFORMANCE MANAGEMENT
# ============================================================================

def check_performance_reviews_due():
    """Check for performance reviews due"""
    logger.info("Checking performance reviews due...")
    
    try:
        cursor = pg_connection.cursor()
        
        # Find employees due for annual review
        cursor.execute("""
            SELECT e.employee_id, 
                   e.first_name || ' ' || e.last_name as employee_name,
                   e.hire_date
            FROM employees e
            WHERE e.employment_status = 'active'
            AND e.hire_date <= CURRENT_DATE - INTERVAL '1 year'
            AND NOT EXISTS (
                SELECT 1 FROM performance_reviews pr
                WHERE pr.employee_id = e.employee_id
                AND pr.review_period_end >= CURRENT_DATE - INTERVAL '13 months'
            )
            LIMIT 10
        """)
        
        due_reviews = cursor.fetchall()
        
        for emp_id, emp_name, hire_date in due_reviews:
            logger.info(f"REVIEW DUE: {emp_name} - hired {hire_date}")
            stats['performance_reviews_due'] += 1
        
        cursor.close()
        
        if due_reviews:
            logger.info(f"Found {len(due_reviews)} employees due for review")
    except Exception as e:
        logger.error(f"Error checking reviews: {e}")

# ============================================================================
# SAFETY COMPLIANCE
# ============================================================================

def review_safety_incidents():
    """Review open safety incidents"""
    logger.info("Reviewing safety incidents...")
    
    try:
        cursor = pg_connection.cursor()
        
        # Get open incidents older than 7 days
        cursor.execute("""
            SELECT incident_id, incident_number, severity,
                   incident_date, investigation_status
            FROM safety_incidents
            WHERE incident_status = 'open'
            AND incident_date < CURRENT_DATE - INTERVAL '7 days'
            LIMIT 10
        """)
        
        incidents = cursor.fetchall()
        
        for inc_id, inc_num, severity, inc_date, inv_status in incidents:
            logger.info(f"SAFETY: Incident {inc_num} ({severity}) - investigation {inv_status}")
            stats['safety_incidents_reviewed'] += 1
            
            # Auto-close minor incidents after investigation
            if severity == 'minor' and inv_status == 'completed':
                cursor.execute("""
                    UPDATE safety_incidents
                    SET incident_status = 'closed',
                        closed_date = %s
                    WHERE incident_id = %s
                """, (datetime.now().date(), inc_id))
        
        pg_connection.commit()
        cursor.close()
        
        if incidents:
            logger.info(f"Reviewed {len(incidents)} safety incidents")
    except Exception as e:
        logger.error(f"Error reviewing incidents: {e}")
        pg_connection.rollback()

# ============================================================================
# SKILL GAP ANALYSIS
# ============================================================================

def identify_skill_gaps():
    """Identify skill gaps for employees"""
    logger.info("Identifying skill gaps...")
    
    try:
        cursor = pg_connection.cursor()
        
        # Find employees missing required skills for their role
        cursor.execute("""
            SELECT e.employee_id,
                   e.first_name || ' ' || e.last_name as employee_name,
                   sc.skill_name,
                   rsr.min_proficiency_level
            FROM employees e
            JOIN positions p ON e.primary_position_id = p.position_id
            JOIN role_skill_requirements rsr ON p.role_id = rsr.role_id
            JOIN skills_catalog sc ON rsr.skill_id = sc.skill_id
            WHERE e.employment_status = 'active'
            AND rsr.requirement_type = 'required'
            AND NOT EXISTS (
                SELECT 1 FROM employee_skills es
                WHERE es.employee_id = e.employee_id
                AND es.skill_id = sc.skill_id
                AND es.proficiency_level >= rsr.min_proficiency_level
            )
            LIMIT 20
        """)
        
        gaps = cursor.fetchall()
        
        for emp_id, emp_name, skill, min_level in gaps:
            logger.info(f"SKILL GAP: {emp_name} needs {skill} (level {min_level})")
        
        cursor.close()
        
        if gaps:
            logger.info(f"Found {len(gaps)} skill gaps")
    except Exception as e:
        logger.error(f"Error identifying skill gaps: {e}")

# ============================================================================
# INTEGRATION WITH OTHER SYSTEMS
# ============================================================================

def sync_with_other_systems():
    """Sync employee data with CRM, CMMS, Service"""
    logger.info("Syncing with other systems...")
    
    try:
        cursor = pg_connection.cursor()
        
        # Check if sales_reps table exists (CRM)
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'sales_reps'
            )
        """)
        
        if cursor.fetchone()[0]:
            # Sync sales reps from employees
            cursor.execute("""
                SELECT e.employee_id, e.first_name, e.last_name, e.work_email
                FROM employees e
                JOIN positions p ON e.primary_position_id = p.position_id
                JOIN job_roles jr ON p.role_id = jr.role_id
                WHERE jr.role_family = 'sales'
                AND e.employment_status = 'active'
                AND NOT EXISTS (
                    SELECT 1 FROM sales_reps sr 
                    WHERE sr.employee_id = e.employee_id
                )
                LIMIT 5
            """)
            
            new_sales_reps = cursor.fetchall()
            
            for emp_id, first_name, last_name, email in new_sales_reps:
                # Would create sales rep record
                logger.info(f"SYNC: Would create sales rep for {first_name} {last_name}")
                
                # Log integration
                cursor.execute("""
                    INSERT INTO hcm_integration_log (
                        log_id, integration_direction, document_type,
                        document_id, target_system, integration_status, log_timestamp
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (generate_id('INTLOG'), 'HCM_TO_CRM', 'employee',
                      emp_id, 'CRM', 'completed', datetime.now()))
        
        pg_connection.commit()
        cursor.close()
    except Exception as e:
        logger.error(f"Error syncing systems: {e}")
        pg_connection.rollback()

# ============================================================================
# MAIN CYCLE
# ============================================================================

def run_hcm_cycle():
    """Execute complete HCM cycle"""
    logger.info("=== HCM Cycle Starting ===")
    
    try:
        # 1. Certification Management
        monitor_certification_expiry()
        
        # 2. Training Compliance
        check_training_compliance()
        auto_schedule_mandatory_training()
        
        # 3. Leave Management
        process_pending_leave_requests()
        if datetime.now().day == 1:  # First of month
            update_leave_balances()
        
        # 4. Onboarding
        track_onboarding_progress()
        
        # 5. Performance
        check_performance_reviews_due()
        
        # 6. Safety
        review_safety_incidents()
        
        # 7. Skills
        identify_skill_gaps()
        
        # 8. Integration
        sync_with_other_systems()
        
        stats['cycles'] += 1
        logger.info("=== HCM Cycle Complete ===")
        return True
    except Exception as e:
        logger.error(f"HCM cycle error: {e}")
        return False

def print_stats():
    """Print daemon statistics"""
    elapsed = (datetime.now() - stats['start_time']).total_seconds()
    hours = elapsed / 3600
    
    logger.info("="*80)
    logger.info(f"HCM Daemon Statistics")
    logger.info(f"  Uptime: {hours:.1f} hours")
    logger.info(f"  Cycles: {stats['cycles']}")
    logger.info(f"  Certifications Alerted: {stats['certifications_alerted']}")
    logger.info(f"  Training Scheduled: {stats['training_scheduled']}")
    logger.info(f"  Leave Requests Processed: {stats['leave_requests_processed']}")
    logger.info(f"  Onboarding Tracked: {stats['onboarding_tracked']}")
    logger.info(f"  Performance Reviews Due: {stats['performance_reviews_due']}")
    logger.info(f"  Safety Incidents Reviewed: {stats['safety_incidents_reviewed']}")
    logger.info("="*80)

def main():
    """Main daemon loop"""
    logger.info("="*80)
    logger.info("GenIMS HR/HCM Daemon Starting")
    logger.info("Cycle Interval: Every hour")
    logger.info("="*80)
    
    if not initialize_database():
        return 1
    
    if not load_master_data():
        return 1
    
    logger.info("Press Ctrl+C to stop")
    
    last_cycle = datetime.now() - timedelta(hours=2)
    
    while running:
        try:
            now = datetime.now()
            
            # Run every hour
            if (now - last_cycle).total_seconds() >= CYCLE_INTERVAL_SECONDS:
                run_hcm_cycle()
                last_cycle = now
            
            # Print stats every 4 hours
            if now.hour % 4 == 0 and now.minute == 0:
                print_stats()
            
            time.sleep(60)  # Check every minute
            
        except Exception as e:
            logger.error(f"Error in main loop: {e}", exc_info=True)
            time.sleep(60)
    
    logger.info("Shutting down...")
    if pg_connection:
        pg_connection.close()
    
    print_stats()
    logger.info("HCM Daemon stopped")
    return 0

if __name__ == "__main__":
    import os
    os.makedirs('logs', exist_ok=True)
    sys.exit(main())
