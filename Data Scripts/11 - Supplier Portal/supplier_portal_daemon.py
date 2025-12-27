#!/usr/bin/env python3
"""
GenIMS Supplier Portal Daemon
Handles automated operations for supplier management, RFQ processing,
performance tracking, invoice matching, and supplier notifications
"""

import sys
import time
import logging
import signal
from datetime import datetime, timedelta
import random

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

# Daemon Configuration
CYCLE_INTERVAL_SECONDS = 300  # Run every 5 minutes

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/supplier_portal_daemon.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('SupplierPortalDaemon')

running = True
pg_connection = None
stats = {
    'cycles': 0,
    'rfq_notifications': 0,
    'performance_calculations': 0,
    'scorecards_generated': 0,
    'invoices_matched': 0,
    'document_alerts': 0,
    'contract_updates': 0,
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

def generate_id(prefix: str) -> str:
    return f"{prefix}-{datetime.now().strftime('%Y%m%d%H%M%S')}-{random.randint(1000, 9999)}"

# ============================================================================
# RFQ MANAGEMENT
# ============================================================================

def monitor_rfq_deadlines():
    """Monitor RFQ response deadlines and send reminders"""
    logger.info("Monitoring RFQ deadlines...")
    
    try:
        cursor = pg_connection.cursor()
        
        # Find RFQs with upcoming deadlines (3 days)
        cursor.execute("""
            SELECT rh.rfq_id, rh.rfq_number, rh.rfq_title,
                   rh.response_deadline, rs.supplier_id
            FROM rfq_headers rh
            JOIN rfq_suppliers rs ON rh.rfq_id = rs.rfq_id
            WHERE rh.rfq_status = 'response_period'
            AND rs.response_status = 'pending'
            AND rh.response_deadline BETWEEN CURRENT_DATE AND CURRENT_DATE + INTERVAL '3 days'
        """)
        
        pending_responses = cursor.fetchall()
        
        for rfq_id, rfq_number, title, deadline, supplier_id in pending_responses:
            # Create notification
            cursor.execute("""
                INSERT INTO supplier_notifications (
                    notification_id, supplier_id, notification_type,
                    notification_title, notification_message,
                    reference_type, reference_id, priority, created_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (generate_id('NOTIF'), supplier_id, 'rfq_deadline_reminder',
                  f'RFQ Response Deadline Approaching: {rfq_number}',
                  f'Please submit your response for RFQ "{title}" by {deadline}',
                  'rfq', rfq_id, 'high', datetime.now()))
            
            stats['rfq_notifications'] += 1
        
        pg_connection.commit()
        cursor.close()
        
        if pending_responses:
            logger.info(f"Sent {len(pending_responses)} RFQ deadline reminders")
    except Exception as e:
        logger.error(f"Error monitoring RFQ deadlines: {e}")
        pg_connection.rollback()

def close_expired_rfqs():
    """Close RFQs that have passed deadline"""
    logger.info("Checking for expired RFQs...")
    
    try:
        cursor = pg_connection.cursor()
        
        # Find RFQs past deadline
        cursor.execute("""
            UPDATE rfq_headers
            SET rfq_status = 'evaluation'
            WHERE rfq_status = 'response_period'
            AND response_deadline < CURRENT_DATE
            RETURNING rfq_id, rfq_number
        """)
        
        closed_rfqs = cursor.fetchall()
        
        # Mark pending suppliers as 'no_response'
        for rfq_id, rfq_number in closed_rfqs:
            cursor.execute("""
                UPDATE rfq_suppliers
                SET response_status = 'no_response'
                WHERE rfq_id = %s
                AND response_status = 'pending'
            """, (rfq_id,))
            
            logger.info(f"Closed RFQ {rfq_number}")
        
        pg_connection.commit()
        cursor.close()
        
        if closed_rfqs:
            logger.info(f"Closed {len(closed_rfqs)} expired RFQs")
    except Exception as e:
        logger.error(f"Error closing expired RFQs: {e}")
        pg_connection.rollback()

# ============================================================================
# SUPPLIER PERFORMANCE
# ============================================================================

def calculate_monthly_performance():
    """Calculate supplier performance metrics for last month"""
    logger.info("Calculating supplier performance metrics...")
    
    try:
        cursor = pg_connection.cursor()
        
        # Check if we need to calculate (1st day of month)
        if datetime.now().day != 1:
            return
        
        last_month = (datetime.now().replace(day=1) - timedelta(days=1))
        metric_period = last_month.strftime('%Y-%m')
        
        # Get all active suppliers
        cursor.execute("SELECT supplier_id FROM suppliers WHERE is_active = true")
        suppliers = cursor.fetchall()
        
        for (supplier_id,) in suppliers:
            # Calculate delivery performance
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_pos,
                    COUNT(*) FILTER (WHERE actual_delivery_date <= promised_delivery_date) as ontime
                FROM purchase_orders
                WHERE supplier_id = %s
                AND order_date >= %s AND order_date < %s
                AND order_status IN ('delivered', 'completed')
            """, (supplier_id, last_month.replace(day=1), last_month.replace(day=1) + timedelta(days=32)))
            
            delivery_data = cursor.fetchone()
            total_pos = delivery_data[0] if delivery_data[0] else 0
            ontime_pos = delivery_data[1] if delivery_data[1] else 0
            ontime_pct = (ontime_pos / total_pos * 100) if total_pos > 0 else 0
            
            # Calculate quality performance (would integrate with WMS/Quality tables)
            # Simplified for demonstration
            defect_ppm = random.randint(50, 500)  # Parts per million
            quality_pct = 100 - (defect_ppm / 10000)
            
            # Calculate responsiveness (from RFQs)
            cursor.execute("""
                SELECT 
                    COUNT(*) as rfqs_sent,
                    COUNT(*) FILTER (WHERE response_status = 'responded') as responded
                FROM rfq_suppliers
                WHERE supplier_id = %s
                AND invited_date >= %s AND invited_date < %s
            """, (supplier_id, last_month.replace(day=1), last_month.replace(day=1) + timedelta(days=32)))
            
            rfq_data = cursor.fetchone()
            rfqs_sent = rfq_data[0] if rfq_data[0] else 0
            rfqs_responded = rfq_data[1] if rfq_data[1] else 0
            response_rate = (rfqs_responded / rfqs_sent * 100) if rfqs_sent > 0 else 0
            
            # Calculate overall score
            overall_score = (
                ontime_pct * 0.3 +
                quality_pct * 0.4 +
                response_rate * 0.2 +
                95.0 * 0.1  # Commercial score placeholder
            )
            
            # Determine rating
            if overall_score >= 95:
                rating = 'excellent'
            elif overall_score >= 85:
                rating = 'good'
            elif overall_score >= 75:
                rating = 'acceptable'
            elif overall_score >= 60:
                rating = 'needs_improvement'
            else:
                rating = 'poor'
            
            # Insert metric
            cursor.execute("""
                INSERT INTO supplier_performance_metrics (
                    metric_id, supplier_id, metric_period,
                    total_pos_issued, pos_delivered_ontime, ontime_delivery_pct,
                    defect_ppm, quality_acceptance_pct,
                    rfqs_sent, rfqs_responded, response_rate_pct,
                    overall_score, performance_rating, created_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (supplier_id, metric_period) DO NOTHING
            """, (generate_id('METRIC'), supplier_id, metric_period,
                  total_pos, ontime_pos, round(ontime_pct, 2),
                  defect_ppm, round(quality_pct, 2),
                  rfqs_sent, rfqs_responded, round(response_rate, 2),
                  round(overall_score, 2), rating, datetime.now()))
            
            stats['performance_calculations'] += 1
        
        pg_connection.commit()
        cursor.close()
        
        logger.info(f"Calculated performance for {len(suppliers)} suppliers")
    except Exception as e:
        logger.error(f"Error calculating performance: {e}")
        pg_connection.rollback()

def generate_supplier_scorecards():
    """Generate monthly supplier scorecards"""
    logger.info("Generating supplier scorecards...")
    
    try:
        cursor = pg_connection.cursor()
        
        # Only on 1st of month
        if datetime.now().day != 1:
            return
        
        last_month = (datetime.now().replace(day=1) - timedelta(days=1))
        scorecard_period = last_month.strftime('%Y-%m')
        
        # Get performance metrics for last month
        cursor.execute("""
            SELECT supplier_id, ontime_delivery_pct, quality_acceptance_pct,
                   response_rate_pct, overall_score, performance_rating
            FROM supplier_performance_metrics
            WHERE metric_period = %s
        """, (scorecard_period,))
        
        metrics = cursor.fetchall()
        
        for supplier_id, delivery_score, quality_score, resp_score, overall_score, rating in metrics:
            # Generate scorecard
            cursor.execute("""
                INSERT INTO supplier_scorecards (
                    scorecard_id, supplier_id, scorecard_period,
                    scorecard_type, delivery_score, quality_score,
                    responsiveness_score, commercial_score, sustainability_score,
                    overall_score, supplier_rating, action_required,
                    published_to_supplier, published_date, created_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (supplier_id, scorecard_period) DO NOTHING
            """, (generate_id('SCORECARD'), supplier_id, scorecard_period,
                  'monthly', delivery_score, quality_score, resp_score,
                  95.0,  # Commercial score
                  85.0,  # Sustainability score
                  overall_score, rating,
                  overall_score < 75,  # Action required if < 75
                  True, datetime.now(), datetime.now()))
            
            # Send notification to supplier
            cursor.execute("""
                INSERT INTO supplier_notifications (
                    notification_id, supplier_id, notification_type,
                    notification_title, notification_message,
                    reference_type, priority, created_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (generate_id('NOTIF'), supplier_id, 'performance_review',
                  f'Performance Scorecard - {scorecard_period}',
                  f'Your performance scorecard for {scorecard_period} is available. Overall rating: {rating}',
                  'scorecard', 'normal', datetime.now()))
            
            stats['scorecards_generated'] += 1
        
        pg_connection.commit()
        cursor.close()
        
        logger.info(f"Generated {len(metrics)} scorecards")
    except Exception as e:
        logger.error(f"Error generating scorecards: {e}")
        pg_connection.rollback()

# ============================================================================
# INVOICE 3-WAY MATCHING
# ============================================================================

def process_invoice_matching():
    """Process 3-way matching for new invoices"""
    logger.info("Processing invoice 3-way matching...")
    
    try:
        cursor = pg_connection.cursor()
        
        # Get pending invoices
        cursor.execute("""
            SELECT si.invoice_id, si.supplier_id, si.purchase_order_id,
                   si.total_amount, si.subtotal
            FROM supplier_invoices si
            WHERE si.matching_status = 'pending'
            AND si.invoice_status = 'received'
            LIMIT 20
        """)
        
        pending_invoices = cursor.fetchall()
        
        for invoice_id, supplier_id, po_id, total_amount, subtotal in pending_invoices:
            try:
                # Get PO total
                cursor.execute("""
                    SELECT total_amount FROM purchase_orders
                    WHERE purchase_order_id = %s
                """, (po_id,))
                
                po_data = cursor.fetchone()
                if not po_data:
                    continue
                
                po_total = po_data[0]
                
                # Calculate variance
                variance_amount = total_amount - po_total
                variance_pct = (variance_amount / po_total * 100) if po_total > 0 else 0
                
                # Determine if within tolerance (2%)
                within_tolerance = abs(variance_pct) <= 2.0
                
                # Determine matching result
                if abs(variance_pct) < 0.1:
                    match_result = 'matched'
                    match_status = 'matched'
                    action = 'auto_approved'
                elif within_tolerance:
                    match_result = 'matched'
                    match_status = 'matched'
                    action = 'auto_approved'
                else:
                    match_result = 'variance'
                    match_status = 'variance'
                    action = 'pending_review'
                
                # Update invoice
                cursor.execute("""
                    UPDATE supplier_invoices
                    SET matching_status = %s,
                        po_match = true,
                        price_match = %s,
                        total_variance = %s,
                        invoice_status = CASE 
                            WHEN %s = 'matched' THEN 'approved'
                            ELSE 'under_review'
                        END
                    WHERE invoice_id = %s
                """, (match_status, abs(variance_pct) < 2, variance_amount,
                      match_status, invoice_id))
                
                # Create 3-way match log
                cursor.execute("""
                    INSERT INTO three_way_match_log (
                        log_id, invoice_id, match_timestamp, match_type,
                        po_id, match_result, expected_amount, actual_amount,
                        variance_amount, variance_pct, within_tolerance,
                        tolerance_pct, action_taken
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (generate_id('MATCH'), invoice_id, datetime.now(), 'automatic',
                      po_id, match_result, po_total, total_amount,
                      variance_amount, round(variance_pct, 2), within_tolerance,
                      2.0, action))
                
                # If variance, send notification
                if match_status == 'variance':
                    cursor.execute("""
                        INSERT INTO supplier_notifications (
                            notification_id, supplier_id, notification_type,
                            notification_title, notification_message,
                            reference_type, reference_id, priority, created_at
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, (generate_id('NOTIF'), supplier_id, 'invoice_variance',
                          'Invoice Variance Detected',
                          f'Invoice variance of {variance_pct:.2f}% requires review',
                          'invoice', invoice_id, 'high', datetime.now()))
                
                stats['invoices_matched'] += 1
                
            except Exception as e:
                logger.error(f"Error matching invoice {invoice_id}: {e}")
                continue
        
        pg_connection.commit()
        cursor.close()
        
        if pending_invoices:
            logger.info(f"Processed {len(pending_invoices)} invoice matches")
    except Exception as e:
        logger.error(f"Error processing invoice matching: {e}")
        pg_connection.rollback()

# ============================================================================
# DOCUMENT EXPIRY MONITORING
# ============================================================================

def check_document_expiry():
    """Check for expiring supplier documents"""
    logger.info("Checking document expiry...")
    
    try:
        cursor = pg_connection.cursor()
        
        # Find documents expiring in next 60 days
        cursor.execute("""
            SELECT sd.document_id, sd.supplier_id, sd.document_type,
                   sd.document_name, sd.expiry_date,
                   sd.expiry_date - CURRENT_DATE as days_to_expiry
            FROM supplier_documents sd
            WHERE sd.document_status = 'verified'
            AND sd.expiry_date BETWEEN CURRENT_DATE AND CURRENT_DATE + INTERVAL '60 days'
            AND sd.expiry_alert_sent = false
        """)
        
        expiring_docs = cursor.fetchall()
        
        for doc_id, supplier_id, doc_type, doc_name, expiry_date, days_to_expiry in expiring_docs:
            # Determine priority
            if days_to_expiry <= 30:
                priority = 'urgent'
            else:
                priority = 'high'
            
            # Send notification
            cursor.execute("""
                INSERT INTO supplier_notifications (
                    notification_id, supplier_id, notification_type,
                    notification_title, notification_message,
                    reference_type, priority, created_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (generate_id('NOTIF'), supplier_id, 'document_expiring',
                  f'Document Expiring: {doc_type}',
                  f'{doc_name} will expire on {expiry_date} ({days_to_expiry} days)',
                  'document', priority, datetime.now()))
            
            # Mark alert sent
            cursor.execute("""
                UPDATE supplier_documents
                SET expiry_alert_sent = true,
                    days_to_expiry = %s
                WHERE document_id = %s
            """, (days_to_expiry, doc_id))
            
            stats['document_alerts'] += 1
        
        # Mark expired documents
        cursor.execute("""
            UPDATE supplier_documents
            SET document_status = 'expired'
            WHERE expiry_date < CURRENT_DATE
            AND document_status = 'verified'
        """)
        
        pg_connection.commit()
        cursor.close()
        
        if expiring_docs:
            logger.info(f"Sent {len(expiring_docs)} document expiry alerts")
    except Exception as e:
        logger.error(f"Error checking document expiry: {e}")
        pg_connection.rollback()

# ============================================================================
# CONTRACT MANAGEMENT
# ============================================================================

def update_contract_status():
    """Update contract status based on dates"""
    logger.info("Updating contract status...")
    
    try:
        cursor = pg_connection.cursor()
        
        # Mark expired contracts
        cursor.execute("""
            UPDATE supplier_contracts
            SET contract_status = 'expired'
            WHERE end_date < CURRENT_DATE
            AND contract_status = 'active'
            RETURNING contract_id, supplier_id, contract_number
        """)
        
        expired_contracts = cursor.fetchall()
        
        for contract_id, supplier_id, contract_number in expired_contracts:
            # Send notification
            cursor.execute("""
                INSERT INTO supplier_notifications (
                    notification_id, supplier_id, notification_type,
                    notification_title, notification_message,
                    reference_type, reference_id, priority, created_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (generate_id('NOTIF'), supplier_id, 'contract_expired',
                  f'Contract Expired: {contract_number}',
                  f'Contract {contract_number} has expired. Please contact us for renewal.',
                  'contract', contract_id, 'high', datetime.now()))
            
            # Mark pricing as inactive
            cursor.execute("""
                UPDATE contract_pricing
                SET is_active = false
                WHERE contract_id = %s
            """, (contract_id,))
            
            stats['contract_updates'] += 1
        
        # Notify about contracts expiring in 60 days
        cursor.execute("""
            SELECT sc.contract_id, sc.supplier_id, sc.contract_number, sc.end_date
            FROM supplier_contracts sc
            WHERE sc.contract_status = 'active'
            AND sc.end_date BETWEEN CURRENT_DATE + INTERVAL '55 days' 
                                AND CURRENT_DATE + INTERVAL '65 days'
            AND NOT EXISTS (
                SELECT 1 FROM supplier_notifications
                WHERE supplier_id = sc.supplier_id
                AND reference_id = sc.contract_id
                AND notification_type = 'contract_expiring'
                AND created_at > CURRENT_DATE - INTERVAL '30 days'
            )
        """)
        
        expiring_contracts = cursor.fetchall()
        
        for contract_id, supplier_id, contract_number, end_date in expiring_contracts:
            cursor.execute("""
                INSERT INTO supplier_notifications (
                    notification_id, supplier_id, notification_type,
                    notification_title, notification_message,
                    reference_type, reference_id, priority, created_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (generate_id('NOTIF'), supplier_id, 'contract_expiring',
                  f'Contract Expiring Soon: {contract_number}',
                  f'Contract {contract_number} will expire on {end_date}. Please initiate renewal discussions.',
                  'contract', contract_id, 'high', datetime.now()))
        
        pg_connection.commit()
        cursor.close()
        
        if expired_contracts or expiring_contracts:
            logger.info(f"Updated {len(expired_contracts)} expired contracts, notified {len(expiring_contracts)} expiring")
    except Exception as e:
        logger.error(f"Error updating contract status: {e}")
        pg_connection.rollback()

# ============================================================================
# MAIN CYCLE
# ============================================================================

def run_supplier_portal_cycle():
    """Execute complete supplier portal cycle"""
    logger.info("=== Supplier Portal Cycle Starting ===")
    
    try:
        # RFQ Management
        monitor_rfq_deadlines()
        close_expired_rfqs()
        
        # Performance Management (monthly on 1st)
        calculate_monthly_performance()
        generate_supplier_scorecards()
        
        # Invoice Processing
        process_invoice_matching()
        
        # Document & Contract Management
        check_document_expiry()
        update_contract_status()
        
        stats['cycles'] += 1
        logger.info("=== Supplier Portal Cycle Complete ===")
        return True
    except Exception as e:
        logger.error(f"Cycle error: {e}")
        return False

def print_stats():
    """Print daemon statistics"""
    elapsed = (datetime.now() - stats['start_time']).total_seconds()
    hours = elapsed / 3600
    
    logger.info("="*80)
    logger.info(f"Supplier Portal Daemon Statistics")
    logger.info(f"  Uptime: {hours:.1f} hours")
    logger.info(f"  Cycles: {stats['cycles']}")
    logger.info(f"  RFQ Notifications: {stats['rfq_notifications']}")
    logger.info(f"  Performance Calculations: {stats['performance_calculations']}")
    logger.info(f"  Scorecards Generated: {stats['scorecards_generated']}")
    logger.info(f"  Invoices Matched: {stats['invoices_matched']}")
    logger.info(f"  Document Alerts: {stats['document_alerts']}")
    logger.info(f"  Contract Updates: {stats['contract_updates']}")
    logger.info("="*80)

def main():
    """Main daemon loop"""
    logger.info("="*80)
    logger.info("GenIMS Supplier Portal Daemon Starting")
    logger.info("Cycle Interval: Every 5 minutes")
    logger.info("="*80)
    
    if not initialize_database():
        return 1
    
    logger.info("Press Ctrl+C to stop")
    
    last_cycle = datetime.now() - timedelta(hours=1)
    
    while running:
        try:
            now = datetime.now()
            
            # Run every 5 minutes
            if (now - last_cycle).total_seconds() >= CYCLE_INTERVAL_SECONDS:
                run_supplier_portal_cycle()
                last_cycle = now
            
            # Print stats every hour
            if now.minute == 0:
                print_stats()
            
            time.sleep(30)  # Check every 30 seconds
            
        except Exception as e:
            logger.error(f"Error in main loop: {e}", exc_info=True)
            time.sleep(30)
    
    logger.info("Shutting down...")
    if pg_connection:
        pg_connection.close()
    
    print_stats()
    logger.info("Supplier Portal Daemon stopped")
    return 0

if __name__ == "__main__":
    import os
    os.makedirs('logs', exist_ok=True)
    sys.exit(main())
