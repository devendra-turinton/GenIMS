#!/usr/bin/env python3
"""
GenIMS Quality Management System (QMS) Daemon - Ultra-Fast Batch Generation
Generates 30 days of QMS data: customer complaints, NCRs, CAPAs, quality KPIs,
SPC data points, calibration alerts, and audit findings
"""

import sys
import os
import logging
from datetime import datetime, timedelta
import random
from dotenv import load_dotenv

# Load environment variables
env_file = os.path.join(os.path.dirname(__file__), '..', '..', 'scripts', 'config.env')
if os.path.exists(env_file):
    load_dotenv(env_file)

try:
    import psycopg2
    from psycopg2.extras import execute_batch
    POSTGRES_AVAILABLE = True
except ImportError:
    POSTGRES_AVAILABLE = False
    print("ERROR: psycopg2 not installed")
    sys.exit(1)

# Configuration
PG_HOST = os.getenv('POSTGRES_HOST', 'localhost')
PG_PORT = int(os.getenv('POSTGRES_PORT', '5432'))
PG_DATABASE = 'genims_quality_db'
PG_USER = os.getenv('POSTGRES_USER', 'postgres')
PG_PASSWORD = os.getenv('POSTGRES_PASSWORD', '')
PG_SSL_MODE = os.getenv('PG_SSL_MODE', 'require')

# Logging configuration
log_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'logs')
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, 'qms_daemon.log')
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('QmsDaemon')

pg_connection = None

def get_max_id_counter(cursor, table, id_column='id'):
    """Get the maximum ID counter from a table"""
    try:
        cursor.execute(f"SELECT COALESCE(MAX(CAST(SUBSTRING({id_column} FROM '[0-9]+') AS INTEGER)), 0) FROM {table}")
        return cursor.fetchone()[0]
    except Exception as e:
        logger.warning(f"Could not get max ID for {table}: {e}")
        return 0

def load_master_data(cursor):
    """Load master data from database"""
    logger.info("Loading master data...")
    
    master_data = {}
    
    # Load customers from existing NCR records
    cursor.execute("SELECT DISTINCT customer_id FROM ncr_headers WHERE customer_id IS NOT NULL")
    master_data['customers'] = [row[0] for row in cursor.fetchall()]
    logger.info(f"  Loaded {len(master_data['customers'])} customers (from NCR records)")
    
    # Load products from existing NCR records
    cursor.execute("SELECT DISTINCT product_id FROM ncr_headers WHERE product_id IS NOT NULL")
    master_data['products'] = [row[0] for row in cursor.fetchall()]
    logger.info(f"  Loaded {len(master_data['products'])} products (from NCR records)")
    
    # Load materials from existing NCR records
    cursor.execute("SELECT DISTINCT material_id FROM ncr_headers WHERE material_id IS NOT NULL")
    master_data['materials'] = [row[0] for row in cursor.fetchall()]
    logger.info(f"  Loaded {len(master_data['materials'])} materials (from NCR records)")
    
    # Load suppliers from existing NCR records
    cursor.execute("SELECT DISTINCT supplier_id FROM ncr_headers WHERE supplier_id IS NOT NULL")
    master_data['suppliers'] = [row[0] for row in cursor.fetchall()]
    logger.info(f"  Loaded {len(master_data['suppliers'])} suppliers (from NCR records)")
    
    # Load employees from existing NCR and CAPA records
    cursor.execute("""
        SELECT DISTINCT detected_by FROM ncr_headers WHERE detected_by IS NOT NULL
        UNION
        SELECT DISTINCT responsible_person FROM capa_headers WHERE responsible_person IS NOT NULL
    """)
    master_data['employees'] = [row[0] for row in cursor.fetchall()]
    logger.info(f"  Loaded {len(master_data['employees'])} employees (from NCR/CAPA records)")
    
    # Load measuring equipment
    cursor.execute("SELECT equipment_id, equipment_number, next_calibration_due FROM measuring_equipment WHERE equipment_status = 'active' LIMIT 50")
    master_data['equipment'] = cursor.fetchall()
    logger.info(f"  Loaded {len(master_data['equipment'])} measuring equipment")
    
    # Load SPC control charts (only those with complete numeric data)
    cursor.execute("""
        SELECT chart_id, chart_number, process_name, upper_control_limit, lower_control_limit, target_value 
        FROM spc_control_charts 
        WHERE chart_status = 'active' 
        AND upper_control_limit IS NOT NULL 
        AND lower_control_limit IS NOT NULL 
        AND target_value IS NOT NULL
        LIMIT 30
    """)
    master_data['spc_charts'] = cursor.fetchall()
    logger.info(f"  Loaded {len(master_data['spc_charts'])} SPC charts")
    
    # Load quality audits
    cursor.execute("SELECT audit_id FROM quality_audits WHERE audit_status IN ('scheduled', 'in_progress', 'completed') LIMIT 20")
    master_data['audits'] = [row[0] for row in cursor.fetchall()]
    logger.info(f"  Loaded {len(master_data['audits'])} audits")
    
    # Load existing quality_kpis dates to prevent duplicates
    cursor.execute("SELECT kpi_date FROM quality_kpis")
    master_data['existing_kpi_dates'] = set([row[0] for row in cursor.fetchall()])
    logger.info(f"  Loaded {len(master_data['existing_kpi_dates'])} existing KPI dates")
    
    return master_data

def generate_batch_data(master_data, start_time, run_timestamp):
    """Generate 30 days of QMS data (14,400 5-minute intervals)"""
    logger.info("Generating batch data...")
    
    # Initialize ID counters
    cursor = pg_connection.cursor()
    complaint_counter = get_max_id_counter(cursor, 'customer_complaints', 'complaint_number')
    ncr_counter = get_max_id_counter(cursor, 'ncr_headers', 'ncr_number')
    capa_counter = get_max_id_counter(cursor, 'capa_headers', 'capa_number')
    kpi_counter = get_max_id_counter(cursor, 'quality_kpis', 'kpi_id')
    alert_counter = get_max_id_counter(cursor, 'calibration_alerts', 'alert_id')
    finding_counter = get_max_id_counter(cursor, 'audit_findings', 'finding_id')
    datapoint_counter = get_max_id_counter(cursor, 'spc_data_points', 'data_point_id')
    cursor.close()
    
    # Data containers
    customer_complaints = []
    ncr_headers = []
    ncr_defect_details = []
    capa_headers = []
    capa_actions = []
    quality_kpis = []
    spc_data_points = []
    calibration_alerts = []
    audit_findings = []
    
    # Track unique combinations
    kpi_dates_seen = set(master_data.get('existing_kpi_dates', []))
    
    # Generate data for 30 days (14,400 5-minute intervals)
    num_intervals = 30 * 24 * 12  # 30 days * 24 hours * 12 (5-min intervals)
    
    for i in range(num_intervals):
        current_time = start_time + timedelta(minutes=5 * i)
        current_date = current_time.date()
        
        # Customer Complaints (1 per 100 intervals)
        if i % 100 == 0 and master_data['customers'] and master_data['products']:
            complaint_counter += 1
            complaint_id = f"COMP-{run_timestamp}-{complaint_counter:06d}"
            complaint_number = f"COMP-{complaint_counter:08d}"
            
            customer_complaints.append({
                'complaint_id': complaint_id,
                'complaint_number': complaint_number,
                'customer_id': random.choice(master_data['customers']),
                'product_id': random.choice(master_data['products']),
                'complaint_date': current_date,
                'complaint_description': f'Quality issue reported on {current_date}',
                'complaint_type': random.choice(['quality', 'performance', 'defect', 'safety']),
                'severity': random.choice(['critical', 'major', 'minor', 'cosmetic']),
                'safety_issue': random.choice([True, False]),
                'quantity_affected': random.randint(1, 100),
                'immediate_action': 'Investigation initiated',
                'complaint_status': random.choice(['open', 'investigating', 'resolved']),
                'created_at': current_time
            })
        
        # NCR Headers (1 per 75 intervals)
        if i % 75 == 0 and master_data['materials']:
            ncr_counter += 1
            ncr_id = f"NCR-{run_timestamp}-{ncr_counter:06d}"
            ncr_number = f"NCR-{ncr_counter:08d}"
            
            ncr_headers.append({
                'ncr_id': ncr_id,
                'ncr_number': ncr_number,
                'source_type': random.choice(['in_process', 'receiving', 'final_inspection', 'customer']),
                'detected_date': current_date,
                'detected_by': random.choice(master_data['employees']) if master_data['employees'] else None,
                'material_id': random.choice(master_data['materials']),
                'product_id': random.choice(master_data['products']) if master_data['products'] else None,
                'quantity_inspected': random.randint(100, 1000),
                'quantity_defective': random.randint(1, 50),
                'defect_type': random.choice(['dimensional', 'visual', 'functional', 'material']),
                'defect_description': f'Non-conformance detected on {current_date}',
                'defect_severity': random.choice(['critical', 'major', 'minor']),
                'disposition': random.choice(['rework', 'scrap', 'use_as_is', 'return']),
                'ncr_status': random.choice(['open', 'contained', 'capa_created', 'closed']),
                'priority': random.choice(['critical', 'high', 'medium', 'low']),
                'created_at': current_time
            })
            
            # Add defect detail
            ncr_defect_details.append({
                'defect_detail_id': f"NCRD-{run_timestamp}-{len(ncr_defect_details):06d}",
                'ncr_id': ncr_id,
                'characteristic_name': f"Characteristic-{random.randint(1, 100)}",
                'specification': f"Spec: {random.uniform(50, 100):.2f}",
                'actual_value': f"Actual: {random.uniform(40, 110):.2f}",
                'measurement_method': random.choice(['CMM', 'Caliper', 'Micrometer', 'Gauge']),
                'measuring_equipment': f"MEAS-{random.randint(1, 30):06d}",
                'defect_location': random.choice(['top', 'bottom', 'side', 'internal']),
                'created_at': current_time
            })
        
        # CAPA Headers (1 per 150 intervals)
        if i % 150 == 0 and master_data['employees']:
            capa_counter += 1
            capa_id = f"CAPA-{run_timestamp}-{capa_counter:06d}"
            capa_number = f"CAPA-{capa_counter:08d}"
            
            target_date = current_date + timedelta(days=random.randint(30, 90))
            
            capa_headers.append({
                'capa_id': capa_id,
                'capa_number': capa_number,
                'action_type': random.choice(['corrective', 'preventive']),
                'initiated_from': random.choice(['ncr', 'audit', 'complaint', 'internal_review']),
                'problem_description': f'Issue requiring corrective action - {current_date}',
                'problem_severity': random.choice(['critical', 'major', 'minor']),
                'immediate_actions': 'Containment actions implemented',
                'actions_planned': 'Root cause analysis and corrective actions to be implemented',
                'responsible_person': random.choice(master_data['employees']),
                'responsible_department': random.choice(['quality', 'production', 'engineering']),
                'target_completion_date': target_date,
                'capa_status': random.choice(['open', 'in_progress', 'verification', 'closed']),
                'created_at': current_time
            })
            
            # Add CAPA action
            capa_actions.append({
                'action_id': f"ACT-{run_timestamp}-{len(capa_actions):06d}",
                'capa_id': capa_id,
                'action_sequence': 1,
                'action_description': 'Implement corrective measures',
                'assigned_to': random.choice(master_data['employees']),
                'due_date': target_date,
                'action_status': random.choice(['pending', 'in_progress', 'completed']),
                'created_at': current_time
            })
        
        # Quality KPIs (1 per day at midnight)
        if current_time.hour == 0 and current_time.minute == 0 and current_date not in kpi_dates_seen:
            kpi_dates_seen.add(current_date)
            kpi_counter += 1
            
            quality_kpis.append({
                'kpi_id': f"KPI-{run_timestamp}-{kpi_counter:06d}",
                'kpi_date': current_date,
                'internal_defect_ppm': random.randint(50, 500),
                'first_time_quality_pct': round(random.uniform(95.0, 99.5), 2),
                'customer_complaints': random.randint(0, 5),
                'customer_returns_ppm': random.randint(10, 100),
                'incoming_rejection_pct': round(random.uniform(0.5, 3.0), 2),
                'supplier_defect_ppm': random.randint(100, 1000),
                'processes_in_control': random.randint(25, 30),
                'processes_total': 30,
                'process_capability_avg': round(random.uniform(1.2, 1.8), 3),
                'ncr_opened': random.randint(0, 5),
                'ncr_closed': random.randint(0, 5),
                'ncr_open_count': random.randint(10, 30),
                'capa_overdue': random.randint(0, 3),
                'equipment_calibrated_pct': round(random.uniform(95.0, 100.0), 2),
                'equipment_overdue': random.randint(0, 2),
                'created_at': current_time
            })
        
        # SPC Data Points (1 per 10 intervals)
        if i % 10 == 0 and master_data['spc_charts']:
            chart_id, chart_number, process_name, ucl, lcl, target = random.choice(master_data['spc_charts'])
            
            # Convert to float for calculations
            ucl_float = float(ucl)
            lcl_float = float(lcl)
            target_float = float(target)
            
            # Generate measurement around target with some variation
            variation = (ucl_float - lcl_float) / 6  # Assume 6 sigma spread
            measurement = target_float + random.gauss(0, variation)
            
            # Check if out of control
            out_of_control = measurement > ucl_float or measurement < lcl_float
            
            datapoint_counter += 1
            spc_data_points.append({
                'data_point_id': f"SPC-{run_timestamp}-{datapoint_counter:06d}",
                'chart_id': chart_id,
                'measurement_timestamp': current_time,
                'subgroup_number': i // 10,
                'measurement_value': round(measurement, 3),
                'measured_by': random.choice(master_data['employees']) if master_data['employees'] else None,
                'out_of_control': out_of_control,
                'violation_type': 'beyond_limits' if out_of_control else None,
                'created_at': current_time
            })
        
        # Calibration Alerts (1 per 200 intervals)
        if i % 200 == 0 and master_data['equipment']:
            equipment_id, equipment_number, next_due = random.choice(master_data['equipment'])
            
            days_until_due = (next_due - current_date).days if next_due else 30
            
            alert_counter += 1
            calibration_alerts.append({
                'alert_id': f"ALERT-{run_timestamp}-{alert_counter:06d}",
                'equipment_id': equipment_id,
                'alert_type': 'due_30_days' if days_until_due > 7 else 'due_7_days',
                'alert_date': current_date,
                'days_until_due': days_until_due,
                'notification_sent': True,
                'resolved': False,
                'created_at': current_time
            })
        
        # Audit Findings (1 per 300 intervals)
        if i % 300 == 0 and master_data['audits'] and master_data['employees']:
            finding_counter += 1
            
            audit_findings.append({
                'finding_id': f"FIND-{run_timestamp}-{finding_counter:06d}",
                'audit_id': random.choice(master_data['audits']),
                'finding_number': finding_counter,
                'finding_type': random.choice(['major', 'minor', 'observation', 'opportunity']),
                'finding_category': random.choice(['documentation', 'process', 'training', 'equipment']),
                'finding_description': f'Audit finding identified on {current_date}',
                'requirement_reference': f'ISO-{random.randint(1000, 9999)}',
                'risk_level': random.choice(['high', 'medium', 'low']),
                'corrective_action_required': random.choice([True, False]),
                'responsible_person': random.choice(master_data['employees']),
                'target_closure_date': current_date + timedelta(days=random.randint(30, 90)),
                'finding_status': random.choice(['open', 'in_progress', 'closed']),
                'created_at': current_time
            })
    
    logger.info(f"✓ Generated {len(customer_complaints)} customer complaints")
    logger.info(f"✓ Generated {len(ncr_headers)} NCR headers")
    logger.info(f"✓ Generated {len(ncr_defect_details)} NCR defect details")
    logger.info(f"✓ Generated {len(capa_headers)} CAPA headers")
    logger.info(f"✓ Generated {len(capa_actions)} CAPA actions")
    logger.info(f"✓ Generated {len(quality_kpis)} quality KPIs")
    logger.info(f"✓ Generated {len(spc_data_points)} SPC data points")
    logger.info(f"✓ Generated {len(calibration_alerts)} calibration alerts")
    logger.info(f"✓ Generated {len(audit_findings)} audit findings")
    
    return {
        'customer_complaints': customer_complaints,
        'ncr_headers': ncr_headers,
        'ncr_defect_details': ncr_defect_details,
        'capa_headers': capa_headers,
        'capa_actions': capa_actions,
        'quality_kpis': quality_kpis,
        'spc_data_points': spc_data_points,
        'calibration_alerts': calibration_alerts,
        'audit_findings': audit_findings
    }

def batch_insert_data(data):
    """Insert generated data in batches"""
    logger.info("Inserting data into database...")
    
    cursor = pg_connection.cursor()
    cursor.execute("SET CONSTRAINTS ALL DEFERRED")
    
    batch_size = 5000
    
    # Insert customer complaints
    if data['customer_complaints']:
        logger.info(f"Inserting {len(data['customer_complaints'])} customer complaints...")
        for i in range(0, len(data['customer_complaints']), batch_size):
            batch = data['customer_complaints'][i:i+batch_size]
            execute_batch(cursor, """
                INSERT INTO customer_complaints (
                    complaint_id, complaint_number, customer_id, product_id,
                    complaint_date, complaint_description, complaint_type,
                    severity, safety_issue, quantity_affected, immediate_action,
                    complaint_status, created_at
                ) VALUES (
                    %(complaint_id)s, %(complaint_number)s, %(customer_id)s, %(product_id)s,
                    %(complaint_date)s, %(complaint_description)s, %(complaint_type)s,
                    %(severity)s, %(safety_issue)s, %(quantity_affected)s, %(immediate_action)s,
                    %(complaint_status)s, %(created_at)s
                ) ON CONFLICT (complaint_number) DO NOTHING
            """, batch)
    
    # Insert NCR headers
    if data['ncr_headers']:
        logger.info(f"Inserting {len(data['ncr_headers'])} NCR headers...")
        for i in range(0, len(data['ncr_headers']), batch_size):
            batch = data['ncr_headers'][i:i+batch_size]
            execute_batch(cursor, """
                INSERT INTO ncr_headers (
                    ncr_id, ncr_number, source_type, detected_date, detected_by,
                    material_id, product_id, quantity_inspected, quantity_defective,
                    defect_type, defect_description, defect_severity,
                    disposition, ncr_status, priority, created_at
                ) VALUES (
                    %(ncr_id)s, %(ncr_number)s, %(source_type)s, %(detected_date)s, %(detected_by)s,
                    %(material_id)s, %(product_id)s, %(quantity_inspected)s, %(quantity_defective)s,
                    %(defect_type)s, %(defect_description)s, %(defect_severity)s,
                    %(disposition)s, %(ncr_status)s, %(priority)s, %(created_at)s
                ) ON CONFLICT (ncr_number) DO NOTHING
            """, batch)
    
    # Insert NCR defect details
    if data['ncr_defect_details']:
        logger.info(f"Inserting {len(data['ncr_defect_details'])} NCR defect details...")
        for i in range(0, len(data['ncr_defect_details']), batch_size):
            batch = data['ncr_defect_details'][i:i+batch_size]
            execute_batch(cursor, """
                INSERT INTO ncr_defect_details (
                    defect_detail_id, ncr_id, characteristic_name, specification,
                    actual_value, measurement_method, measuring_equipment,
                    defect_location, created_at
                ) VALUES (
                    %(defect_detail_id)s, %(ncr_id)s, %(characteristic_name)s, %(specification)s,
                    %(actual_value)s, %(measurement_method)s, %(measuring_equipment)s,
                    %(defect_location)s, %(created_at)s
                ) ON CONFLICT (defect_detail_id) DO NOTHING
            """, batch)
    
    # Insert CAPA headers
    if data['capa_headers']:
        logger.info(f"Inserting {len(data['capa_headers'])} CAPA headers...")
        for i in range(0, len(data['capa_headers']), batch_size):
            batch = data['capa_headers'][i:i+batch_size]
            execute_batch(cursor, """
                INSERT INTO capa_headers (
                    capa_id, capa_number, action_type, initiated_from,
                    problem_description, problem_severity, immediate_actions,
                    actions_planned, responsible_person, responsible_department,
                    target_completion_date, capa_status, created_at
                ) VALUES (
                    %(capa_id)s, %(capa_number)s, %(action_type)s, %(initiated_from)s,
                    %(problem_description)s, %(problem_severity)s, %(immediate_actions)s,
                    %(actions_planned)s, %(responsible_person)s, %(responsible_department)s,
                    %(target_completion_date)s, %(capa_status)s, %(created_at)s
                ) ON CONFLICT (capa_number) DO NOTHING
            """, batch)
    
    # Insert CAPA actions
    if data['capa_actions']:
        logger.info(f"Inserting {len(data['capa_actions'])} CAPA actions...")
        for i in range(0, len(data['capa_actions']), batch_size):
            batch = data['capa_actions'][i:i+batch_size]
            execute_batch(cursor, """
                INSERT INTO capa_actions (
                    action_id, capa_id, action_sequence, action_description,
                    assigned_to, due_date, action_status, created_at
                ) VALUES (
                    %(action_id)s, %(capa_id)s, %(action_sequence)s, %(action_description)s,
                    %(assigned_to)s, %(due_date)s, %(action_status)s, %(created_at)s
                ) ON CONFLICT (action_id) DO NOTHING
            """, batch)
    
    # Insert quality KPIs
    if data['quality_kpis']:
        logger.info(f"Inserting {len(data['quality_kpis'])} quality KPIs...")
        for i in range(0, len(data['quality_kpis']), batch_size):
            batch = data['quality_kpis'][i:i+batch_size]
            execute_batch(cursor, """
                INSERT INTO quality_kpis (
                    kpi_id, kpi_date, internal_defect_ppm, first_time_quality_pct,
                    customer_complaints, customer_returns_ppm, incoming_rejection_pct,
                    supplier_defect_ppm, processes_in_control, processes_total,
                    process_capability_avg, ncr_opened, ncr_closed, ncr_open_count,
                    capa_overdue, equipment_calibrated_pct, equipment_overdue, created_at
                ) VALUES (
                    %(kpi_id)s, %(kpi_date)s, %(internal_defect_ppm)s, %(first_time_quality_pct)s,
                    %(customer_complaints)s, %(customer_returns_ppm)s, %(incoming_rejection_pct)s,
                    %(supplier_defect_ppm)s, %(processes_in_control)s, %(processes_total)s,
                    %(process_capability_avg)s, %(ncr_opened)s, %(ncr_closed)s, %(ncr_open_count)s,
                    %(capa_overdue)s, %(equipment_calibrated_pct)s, %(equipment_overdue)s, %(created_at)s
                ) ON CONFLICT (kpi_date) DO NOTHING
            """, batch)
    
    # Insert SPC data points
    if data['spc_data_points']:
        logger.info(f"Inserting {len(data['spc_data_points'])} SPC data points...")
        for i in range(0, len(data['spc_data_points']), batch_size):
            batch = data['spc_data_points'][i:i+batch_size]
            execute_batch(cursor, """
                INSERT INTO spc_data_points (
                    data_point_id, chart_id, measurement_timestamp, subgroup_number,
                    measurement_value, measured_by, out_of_control, violation_type, created_at
                ) VALUES (
                    %(data_point_id)s, %(chart_id)s, %(measurement_timestamp)s, %(subgroup_number)s,
                    %(measurement_value)s, %(measured_by)s, %(out_of_control)s, %(violation_type)s, %(created_at)s
                ) ON CONFLICT (data_point_id) DO NOTHING
            """, batch)
    
    # Insert calibration alerts
    if data['calibration_alerts']:
        logger.info(f"Inserting {len(data['calibration_alerts'])} calibration alerts...")
        for i in range(0, len(data['calibration_alerts']), batch_size):
            batch = data['calibration_alerts'][i:i+batch_size]
            execute_batch(cursor, """
                INSERT INTO calibration_alerts (
                    alert_id, equipment_id, alert_type, alert_date,
                    days_until_due, notification_sent, resolved, created_at
                ) VALUES (
                    %(alert_id)s, %(equipment_id)s, %(alert_type)s, %(alert_date)s,
                    %(days_until_due)s, %(notification_sent)s, %(resolved)s, %(created_at)s
                ) ON CONFLICT (alert_id) DO NOTHING
            """, batch)
    
    # Insert audit findings
    if data['audit_findings']:
        logger.info(f"Inserting {len(data['audit_findings'])} audit findings...")
        for i in range(0, len(data['audit_findings']), batch_size):
            batch = data['audit_findings'][i:i+batch_size]
            execute_batch(cursor, """
                INSERT INTO audit_findings (
                    finding_id, audit_id, finding_number, finding_type,
                    finding_category, finding_description, requirement_reference,
                    risk_level, corrective_action_required, responsible_person,
                    target_closure_date, finding_status, created_at
                ) VALUES (
                    %(finding_id)s, %(audit_id)s, %(finding_number)s, %(finding_type)s,
                    %(finding_category)s, %(finding_description)s, %(requirement_reference)s,
                    %(risk_level)s, %(corrective_action_required)s, %(responsible_person)s,
                    %(target_closure_date)s, %(finding_status)s, %(created_at)s
                ) ON CONFLICT (finding_id) DO NOTHING
            """, batch)
    
    cursor.close()
    logger.info("✓ All data inserted")

def validate_insertions():
    """Validate data was inserted correctly"""
    logger.info("\nValidating insertions...")
    
    cursor = pg_connection.cursor()
    
    tables = [
        'customer_complaints',
        'ncr_headers',
        'ncr_defect_details',
        'capa_headers',
        'capa_actions',
        'quality_kpis',
        'spc_data_points',
        'calibration_alerts',
        'audit_findings'
    ]
    
    results = {}
    for table in tables:
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]
        results[table] = count
        logger.info(f"  {table}: {count} records")
    
    cursor.close()
    return results

def main():
    """Main execution"""
    global pg_connection
    
    start_time_total = datetime.now()
    logger.info("="*80)
    logger.info("GenIMS QMS Daemon - Ultra-Fast Batch Generation")
    logger.info(f"Start Time: {start_time_total}")
    logger.info("="*80)
    
    try:
        # Connect to database
        logger.info("Connecting to PostgreSQL...")
        pg_connection = psycopg2.connect(
            host=PG_HOST, port=PG_PORT, database=PG_DATABASE,
            user=PG_USER, password=PG_PASSWORD, sslmode=PG_SSL_MODE
        )
        pg_connection.autocommit = False
        logger.info("✓ Connected to PostgreSQL")
        
        # Get counts before
        logger.info("\n--- Counts BEFORE ---")
        counts_before = validate_insertions()
        
        # Load master data
        cursor = pg_connection.cursor()
        master_data = load_master_data(cursor)
        cursor.close()
        
        # Generate batch data (30 days from now)
        run_timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        start_time = datetime.now()
        
        batch_data = generate_batch_data(master_data, start_time, run_timestamp)
        
        # Insert data
        batch_insert_data(batch_data)
        
        # Commit transaction
        logger.info("\nCommitting transaction...")
        pg_connection.commit()
        logger.info("✓ Transaction committed")
        
        # Validate
        logger.info("\n--- Counts AFTER ---")
        counts_after = validate_insertions()
        
        # Calculate inserted records
        logger.info("\n--- Records INSERTED ---")
        for table in counts_before.keys():
            inserted = counts_after[table] - counts_before[table]
            logger.info(f"  {table}: Before: {counts_before[table]} | After: {counts_after[table]} | Inserted: {inserted}")
        
        # Report completion
        elapsed = (datetime.now() - start_time_total).total_seconds()
        logger.info("\n" + "="*80)
        logger.info(f"✓ QMS batch generation completed successfully")
        logger.info(f"Execution Time: {elapsed:.2f} seconds")
        logger.info("="*80)
        
        return 0
        
    except Exception as e:
        logger.error(f"\n✗ Error: {e}", exc_info=True)
        if pg_connection:
            pg_connection.rollback()
        return 1
    finally:
        if pg_connection:
            pg_connection.close()
            logger.info("Database connection closed")

if __name__ == "__main__":
    sys.exit(main())
