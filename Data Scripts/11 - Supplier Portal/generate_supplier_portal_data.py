#!/usr/bin/env python3
"""
GenIMS Supplier Portal Data Generator
Generates RFQs, contracts, performance metrics, invoices, and supplier portal data
"""

import random
import json
from datetime import datetime, timedelta
from typing import List, Dict
import sys
from pathlib import Path
from decimal import Decimal
import time
import logging

# Add scripts to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))
from generator_helper import get_helper
from data_registry import get_registry

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TimeCoordinator:
    """Enterprise Time Coordinator for current-date enforcement"""
    def __init__(self):
        # ALWAYS use current date for data generation (enterprise reliability)
        self.current_date = datetime(2026, 1, 7)  # Current date enforcement
        self.timestamp_counter = 0
        logger.info(f"Time Coordinator initialized: {self.current_date}")
    
    def get_current_date(self):
        return self.current_date
    
    def get_current_datetime(self):
        return self.current_date
    
    def get_unique_timestamp(self):
        """Generate unique timestamp with millisecond precision"""
        self.timestamp_counter += 1
        return self.current_date.replace(microsecond=self.timestamp_counter % 1000000)
    
    def generate_past_datetime(self, days_ago):
        """Generate datetime in the past relative to current date"""
        return self.current_date - timedelta(days=days_ago)
    
    def generate_future_datetime(self, days_ahead):
        """Generate datetime in the future relative to current date"""
        return self.current_date + timedelta(days=days_ahead)
    
    def time_coordination_delay(self, operation_name="operation"):
        """Add time coordination delay between operations"""
        delay = random.uniform(2, 3)
        time.sleep(delay)
        logger.info(f"Time coordination delay for {operation_name}: {delay:.2f}s")

class SupplierPortalDataGenerator:
    def __init__(self, master_data_file=None, erp_data_file=None):
        """Initialize data generator with TimeCoordinator and registry"""
        from pathlib import Path
        
        # Initialize TimeCoordinator for current-date enforcement
        self.time_coordinator = TimeCoordinator()
        logger.info(f"Using current date for data generation: {self.time_coordinator.current_date}")
        
        if master_data_file is None:
            master_data_file = Path(__file__).parent.parent / "01 - Base Data" / "genims_master_data.json"
        
        if erp_data_file is None:
            erp_data_file = Path(__file__).parent.parent / "04 - ERP & MES Integration" / "genims_erp_data.json"
        
        logger.info(f"Loading master data from {master_data_file}...")
        logger.info(f"Loading ERP data from {erp_data_file}...")
        
        with open(master_data_file, 'r') as f:
            master_data = json.load(f)
        
        try:
            with open(erp_data_file, 'r') as f:
                erp_data = json.load(f)
        except FileNotFoundError:
            logger.warning(f"ERP data not found, using minimal data")
            erp_data = {'materials': [], 'suppliers': [], 'purchase_orders': []}
        
        # Load registry for FK validation
        try:
            self.registry = get_registry()
            self.helper = get_helper()
            logger.info("Registry helper loaded successfully")
        except Exception as e:
            logger.warning(f"Registry helper not available: {e}, using fallback data")
            self.registry = None
            self.helper = None
        
        # Data structures
        self.rfq_headers = []
        self.rfq_lines = []
        self.rfq_suppliers = []
        self.rfq_responses = []
        self.rfq_response_lines = []
        
        self.supplier_contracts = []
        self.contract_pricing = []
        
        self.performance_metrics = []
        self.scorecards = []
        
        self.supplier_invoices = []
        self.invoice_lines = []
        self.three_way_matches = []
        
        self.qualification_records = []
        self.supplier_documents = []
        self.supplier_audits = []
        
        self.portal_users = []
        self.purchase_requisitions = []
        self.req_lines = []
        
        # Reference data from loaded files
        self.suppliers = erp_data.get('suppliers', [])  # Get suppliers from ERP data
        self.materials = erp_data.get('materials', [])
        self.employees = master_data.get('employees', [])
        self.purchase_orders = erp_data.get('purchase_orders', [])
        
        # Enhanced counters with proper initialization
        self.counters = {
            'rfq': 1000, 'rfq_line': 1000, 'rfq_response': 1000, 'response_line': 1000,
            'contract': 1000, 'pricing': 1000, 'metric': 1000, 'scorecard': 1000,
            'invoice': 1000, 'inv_line': 1000, 'match': 1000, 'qual': 1000,
            'doc': 1000, 'audit': 1000, 'user': 1000, 'req': 1000, 'req_line': 1000
        }
    
    def validate_rfq_response_compliance(self, response_data):
        """Validate RFQ response compliance"""
        compliance_score = 100
        issues = []
        
        # Check response timeliness (within deadline)
        if response_data.get('response_date') and response_data.get('rfq_deadline'):
            response_date = datetime.strptime(response_data['response_date'], '%Y-%m-%d')
            deadline = datetime.strptime(response_data['rfq_deadline'], '%Y-%m-%d')
            if response_date > deadline:
                compliance_score -= 25
                issues.append('Late response')
        
        # Check specification compliance
        if not response_data.get('meets_specifications', True):
            compliance_score -= 30
            issues.append('Specification non-compliance')
        
        # Check pricing reasonableness (within 20% of target)
        if response_data.get('quoted_price') and response_data.get('target_price'):
            price_variance = abs(response_data['quoted_price'] - response_data['target_price']) / response_data['target_price']
            if price_variance > 0.20:
                compliance_score -= 15
                issues.append('Price variance > 20%')
        
        return max(0, compliance_score), issues
    
    def validate_3_way_matching(self, invoice_data, po_data, receipt_data):
        """Validate 3-way matching (PO, Invoice, Receipt)"""
        match_result = {'status': 'matched', 'variances': [], 'tolerance_exceeded': False}
        tolerance_pct = 2.0  # 2% tolerance
        
        # Quantity matching
        qty_variance = abs(invoice_data['quantity'] - receipt_data['quantity'])
        qty_variance_pct = (qty_variance / po_data['quantity']) * 100 if po_data['quantity'] > 0 else 0
        
        if qty_variance_pct > tolerance_pct:
            match_result['status'] = 'variance'
            match_result['variances'].append(f'Quantity variance: {qty_variance_pct:.2f}%')
            match_result['tolerance_exceeded'] = True
        
        # Price matching
        price_variance = abs(invoice_data['unit_price'] - po_data['unit_price'])
        price_variance_pct = (price_variance / po_data['unit_price']) * 100 if po_data['unit_price'] > 0 else 0
        
        if price_variance_pct > tolerance_pct:
            match_result['status'] = 'variance'
            match_result['variances'].append(f'Price variance: {price_variance_pct:.2f}%')
            match_result['tolerance_exceeded'] = True
        
        return match_result
    
    def calculate_supplier_rating(self, performance_data):
        """Calculate comprehensive supplier rating"""
        weights = {
            'delivery': 0.30,
            'quality': 0.40, 
            'responsiveness': 0.20,
            'commercial': 0.10
        }
        
        weighted_score = (
            performance_data['delivery_score'] * weights['delivery'] +
            performance_data['quality_score'] * weights['quality'] +
            performance_data['responsiveness_score'] * weights['responsiveness'] +
            performance_data['commercial_score'] * weights['commercial']
        )
        
        # Determine rating category
        if weighted_score >= 95:
            rating = 'excellent'
        elif weighted_score >= 85:
            rating = 'good'
        elif weighted_score >= 75:
            rating = 'acceptable'
        elif weighted_score >= 60:
            rating = 'needs_improvement'
        else:
            rating = 'poor'
        
        return round(weighted_score, 2), rating
    
    def get_valid_supplier_id(self):
        """Get validated supplier ID from registry or fallback"""
        if self.registry and hasattr(self.registry, 'get_random_supplier_id'):
            return self.registry.get_random_supplier_id()
        elif self.suppliers:
            supplier = random.choice(self.suppliers)
            return supplier.get('supplier_id', 'SUP-000001') if isinstance(supplier, dict) else supplier
        return f'SUP-{random.randint(1, 30):06d}'
    
    def get_valid_employee_id(self):
        """Get validated employee ID from registry or fallback"""
        if self.registry and hasattr(self.registry, 'get_random_employee_id'):
            return self.registry.get_random_employee_id()
        elif self.employees:
            employee = random.choice(self.employees)
            return employee.get('employee_id', 'EMP-000001') if isinstance(employee, dict) else employee
        return f'EMP-{random.randint(1, 50):06d}'
    
    def get_valid_material_id(self):
        """Get validated material ID from registry or fallback"""
        if self.registry and hasattr(self.registry, 'get_random_material_id'):
            return self.registry.get_random_material_id()
        elif self.materials:
            material = random.choice(self.materials)
            return material.get('material_id', 'MAT-000001') if isinstance(material, dict) else material
        return f'MAT-{random.randint(1, 100):06d}'
    
    def generate_id(self, prefix: str, counter_key: str) -> str:
        id_val = f"{prefix}-{str(self.counters[counter_key]).zfill(6)}"
        self.counters[counter_key] += 1
        return id_val
    
    def generate_all_data(self):
        """Generate all supplier portal data with enterprise patterns"""
        logger.info(f"\n{'='*80}")
        logger.info(f"Generating Supplier Portal Data with TimeCoordinator")
        logger.info(f"Current Date: {self.time_coordinator.current_date}")
        logger.info(f"{'='*80}\n")
        
        # Generate data with time coordination between phases
        self.generate_purchase_requisitions()
        self.generate_rfqs()
        self.generate_supplier_contracts()
        self.generate_performance_metrics()
        self.generate_supplier_invoices()
        self.generate_supplier_qualification()
        self.generate_portal_users()
        
        self._print_summary()
    
    # ========================================================================
    # PURCHASE REQUISITIONS
    # ========================================================================
    
    def generate_purchase_requisitions(self):
        """Generate purchase requisitions with current date enforcement"""
        logger.info("Generating purchase requisitions...")
        
        statuses = ['draft', 'submitted', 'approved', 'rejected', 'converted_to_rfq']
        
        for i in range(30):
            req_date = self.time_coordinator.generate_past_datetime(random.randint(1, 90))
            required_by = req_date + timedelta(days=random.randint(30, 90))
            status = random.choice(statuses)
            
            req = {
                'requisition_id': self.generate_id('REQ', 'req'),
                'requisition_number': f'PR-{self.time_coordinator.current_date.year}-{i+1:05d}',
                'requested_by': self.get_valid_employee_id(),
                'requisition_date': req_date.strftime('%Y-%m-%d'),
                'required_by_date': required_by.strftime('%Y-%m-%d'),
                'requisition_type': random.choice(['standard', 'urgent', 'capital']),
                'purpose': 'Material requirement for production',
                'estimated_total': float(Decimal(str(random.uniform(50000, 500000))).quantize(Decimal('0.01'))),
                'requisition_status': status,
                'created_at': req_date.strftime('%Y-%m-%d %H:%M:%S')
            }
            self.purchase_requisitions.append(req)
            
            # Generate 2-5 lines with FK validation
            num_lines = random.randint(2, 5)
            for j in range(num_lines):
                line = {
                    'line_id': self.generate_id('REQLINE', 'req_line'),
                    'requisition_id': req['requisition_id'],
                    'line_number': j + 1,
                    'material_id': self.get_valid_material_id(),
                    'item_description': f'Material item {j+1}',
                    'quantity': float(Decimal(str(random.uniform(100, 1000))).quantize(Decimal('0.01'))),
                    'unit_of_measure': random.choice(['PC', 'KG', 'M', 'L']),
                    'estimated_unit_price': float(Decimal(str(random.uniform(50, 500))).quantize(Decimal('0.01'))),
                    'created_at': req_date.strftime('%Y-%m-%d %H:%M:%S')
                }
                line['estimated_total'] = float(Decimal(str(line['quantity'])) * Decimal(str(line['estimated_unit_price'])))
                self.req_lines.append(line)
        
        logger.info(f"Generated {len(self.purchase_requisitions)} requisitions, {len(self.req_lines)} lines")
        self.time_coordinator.time_coordination_delay("purchase requisitions")
    
    # ========================================================================
    # RFQ - REQUEST FOR QUOTE
    # ========================================================================
    
    def generate_rfqs(self):
        """Generate RFQs with responses using TimeCoordinator and FK validation"""
        logger.info("Generating RFQs and responses...")
        
        statuses = ['published', 'response_period', 'evaluation', 'awarded']
        
        for i in range(20):
            rfq_date = self.time_coordinator.generate_past_datetime(random.randint(1, 60))
            deadline = rfq_date + timedelta(days=random.randint(7, 21))
            status = random.choice(statuses)
            
            rfq = {
                'rfq_id': self.generate_id('RFQ', 'rfq'),
                'rfq_number': f'RFQ-{self.time_coordinator.current_date.year}-{i+1:05d}',
                'rfq_title': f'RFQ for {random.choice(["Raw Materials", "Components", "Services", "Equipment"])}',
                'rfq_description': 'Request for quotation for materials',
                'rfq_type': random.choice(['standard', 'urgent', 'blanket']),
                'requested_by': self.get_valid_employee_id(),
                'rfq_date': rfq_date.strftime('%Y-%m-%d'),
                'response_deadline': deadline.strftime('%Y-%m-%d'),
                'total_estimated_value': float(Decimal(str(random.uniform(100000, 2000000))).quantize(Decimal('0.01'))),
                'rfq_status': status,
                'published_date': rfq_date.strftime('%Y-%m-%d') if status != 'draft' else None,
                'created_at': rfq_date.strftime('%Y-%m-%d %H:%M:%S')
            }
            self.rfq_headers.append(rfq)
            
            # Generate 2-8 line items with FK validation
            num_lines = random.randint(2, 8)
            for j in range(num_lines):
                line = {
                    'line_id': self.generate_id('RFQLINE', 'rfq_line'),
                    'rfq_id': rfq['rfq_id'],
                    'line_number': j + 1,
                    'item_type': random.choice(['material', 'service']),
                    'material_id': self.get_valid_material_id(),
                    'item_description': f'Material specification {j+1}',
                    'quantity': float(Decimal(str(random.uniform(100, 5000))).quantize(Decimal('0.01'))),
                    'unit_of_measure': random.choice(['PC', 'KG', 'M']),
                    'target_price': float(Decimal(str(random.uniform(50, 500))).quantize(Decimal('0.01'))),
                    'created_at': rfq_date.strftime('%Y-%m-%d %H:%M:%S')
                }
                line['estimated_total'] = float(Decimal(str(line['quantity'])) * Decimal(str(line['target_price'])))
                self.rfq_lines.append(line)
            
            # Invite 3-5 suppliers with proper validation
            available_suppliers = []
            for _ in range(5):  # Try to get 5 unique suppliers
                supplier_id = self.get_valid_supplier_id()
                if supplier_id not in available_suppliers:
                    available_suppliers.append(supplier_id)
            
            if len(available_suppliers) < 3:
                # Ensure minimum 3 suppliers
                for i in range(3):
                    available_suppliers.append(f'SUP-{i+1:06d}')
            
            invited_suppliers = available_suppliers[:random.randint(3, min(5, len(available_suppliers)))]
            
            for supplier_id in invited_suppliers:
                invitation = {
                    'rfq_supplier_id': self.generate_id('RFQSUP', 'rfq'),
                    'rfq_id': rfq['rfq_id'],
                    'supplier_id': supplier_id,
                    'invited_date': rfq_date.strftime('%Y-%m-%d %H:%M:%S'),
                    'response_status': random.choice(['responded', 'viewed', 'pending', 'declined']),
                    'created_at': rfq_date.strftime('%Y-%m-%d %H:%M:%S')
                }
                self.rfq_suppliers.append(invitation)
                
                # Generate response if supplier responded with compliance validation
                if invitation['response_status'] == 'responded':
                    response_date = rfq_date + timedelta(days=random.randint(1, 14))
                    
                    response = {
                        'response_id': self.generate_id('RFQRESP', 'rfq_response'),
                        'response_number': f'QT-{self.time_coordinator.current_date.year}-{self.counters["rfq_response"]:05d}',
                        'rfq_id': rfq['rfq_id'],
                        'supplier_id': supplier_id,
                        'response_date': response_date.strftime('%Y-%m-%d %H:%M:%S'),
                        'valid_until_date': (response_date + timedelta(days=30)).strftime('%Y-%m-%d'),
                        'payment_terms': random.choice(['30 days', '60 days', '90 days']),
                        'response_status': random.choice(['submitted', 'shortlisted', 'awarded']),
                        'created_at': response_date.strftime('%Y-%m-%d %H:%M:%S')
                    }
                        
                    # Generate response lines with business logic validation
                    total_quoted = Decimal('0.00')
                    for line in [l for l in self.rfq_lines if l['rfq_id'] == rfq['rfq_id']]:
                        # Quote with realistic variance (±15% to +25%)
                        variance = random.uniform(-0.15, 0.25)
                        unit_price = Decimal(str(line['target_price'])) * Decimal(str(1 + variance))
                        
                        # Validate compliance for this response
                        compliance_data = {
                            'response_date': response_date.strftime('%Y-%m-%d'),
                            'rfq_deadline': rfq['response_deadline'],
                            'meets_specifications': random.random() > 0.1,
                            'quoted_price': float(unit_price),
                            'target_price': line['target_price']
                        }
                        compliance_score, issues = self.validate_rfq_response_compliance(compliance_data)
                        
                        resp_line = {
                            'response_line_id': self.generate_id('RESPLINE', 'response_line'),
                            'response_id': response['response_id'],
                            'rfq_line_id': line['line_id'],
                            'line_number': line['line_number'],
                            'unit_price': float(unit_price.quantize(Decimal('0.0001'))),
                            'total_price': float((unit_price * Decimal(str(line['quantity']))).quantize(Decimal('0.01'))),
                            'lead_time_days': random.randint(15, 60),
                            'meets_specifications': compliance_data['meets_specifications'],
                            'created_at': response_date.strftime('%Y-%m-%d %H:%M:%S')
                        }
                        self.rfq_response_lines.append(resp_line)
                        total_quoted += Decimal(str(resp_line['total_price']))
                        
                    response['total_quoted_value'] = float(total_quoted)
                    self.rfq_responses.append(response)
        
        logger.info(f"Generated {len(self.rfq_headers)} RFQs, {len(self.rfq_lines)} lines")
        logger.info(f"  {len(self.rfq_suppliers)} supplier invitations")
        logger.info(f"  {len(self.rfq_responses)} responses, {len(self.rfq_response_lines)} response lines")
        self.time_coordinator.time_coordination_delay("RFQ generation")
    
    # ========================================================================
    # SUPPLIER CONTRACTS
    # ========================================================================
    
    def generate_supplier_contracts(self):
        """Generate supplier contracts and pricing with FK validation"""
        logger.info("Generating supplier contracts...")
        
        # Create contracts for available suppliers
        supplier_count = 0
        for i in range(min(20, 30)):  # Limit to reasonable number
            supplier_id = self.get_valid_supplier_id()
            start_date = self.time_coordinator.generate_past_datetime(random.randint(30, 365))
            end_date = start_date + timedelta(days=365)
            
            contract = {
                'contract_id': self.generate_id('CONTRACT', 'contract'),
                'contract_number': f'CONT-{self.time_coordinator.current_date.year}-{i+1:03d}',
                'supplier_id': supplier_id,
                'contract_name': f'Annual Supply Agreement {self.time_coordinator.current_date.year}',
                'contract_type': random.choice(['price_agreement', 'blanket_order', 'framework']),
                'start_date': start_date.strftime('%Y-%m-%d'),
                'end_date': end_date.strftime('%Y-%m-%d'),
                'payment_terms': random.choice(['30 days', '45 days', '60 days']),
                'committed_annual_value': float(Decimal(str(random.uniform(500000, 5000000))).quantize(Decimal('0.01'))),
                'auto_renew': random.random() > 0.5,
                'contract_status': 'active' if end_date > self.time_coordinator.current_date else 'expired',
                'actual_spend_to_date': float(Decimal(str(random.uniform(100000, 1000000))).quantize(Decimal('0.01'))),
                'orders_placed': random.randint(10, 50),
                'created_at': start_date.strftime('%Y-%m-%d %H:%M:%S')
            }
            self.supplier_contracts.append(contract)
            
            # Generate pricing for 5-10 materials with FK validation
            num_materials = random.randint(5, 10)
            for j in range(num_materials):
                pricing = {
                    'pricing_id': self.generate_id('PRICING', 'pricing'),
                    'contract_id': contract['contract_id'],
                    'material_id': self.get_valid_material_id(),
                    'unit_price': float(Decimal(str(random.uniform(50, 500))).quantize(Decimal('0.0001'))),
                    'effective_from': start_date.strftime('%Y-%m-%d'),
                    'effective_to': end_date.strftime('%Y-%m-%d'),
                    'standard_lead_time_days': random.randint(15, 45),
                    'is_active': contract['contract_status'] == 'active',
                    'created_at': start_date.strftime('%Y-%m-%d %H:%M:%S')
                }
                self.contract_pricing.append(pricing)
            
            supplier_count += 1
        
        logger.info(f"Generated {len(self.supplier_contracts)} contracts, {len(self.contract_pricing)} pricing records")
        self.time_coordinator.time_coordination_delay("supplier contracts")
    
    # ========================================================================
    # SUPPLIER PERFORMANCE
    # ========================================================================
    
    def generate_performance_metrics(self):
        """Generate supplier performance metrics with business logic validation"""
        logger.info("Generating supplier performance metrics...")
        
        # Last 6 months of data for available suppliers
        for supplier_idx in range(min(20, 30)):  # Limit to reasonable number
            supplier_id = self.get_valid_supplier_id()
            
            for months_ago in range(6):
                metric_date = self.time_coordinator.generate_past_datetime(30 * months_ago)
                metric_period = metric_date.strftime('%Y-%m')
                
                # Generate realistic metrics
                total_pos = random.randint(5, 20)
                ontime_pct = random.uniform(75, 98)
                ontime_pos = int(total_pos * ontime_pct / 100)
                
                total_qty = random.uniform(1000, 10000)
                acceptance_pct = random.uniform(95, 99.9)
                accepted_qty = total_qty * acceptance_pct / 100
                rejected_qty = total_qty - accepted_qty
                
                rfqs_sent = random.randint(3, 10)
                response_rate = random.uniform(70, 100)
                rfqs_responded = int(rfqs_sent * response_rate / 100)
                
                # Calculate scores using business logic
                delivery_score = ontime_pct
                quality_score = acceptance_pct
                responsiveness_score = response_rate
                commercial_score = random.uniform(85, 98)
                
                performance_data = {
                    'delivery_score': delivery_score,
                    'quality_score': quality_score,
                    'responsiveness_score': responsiveness_score,
                    'commercial_score': commercial_score
                }
                
                overall_score, rating = self.calculate_supplier_rating(performance_data)
                
                metric = {
                    'metric_id': self.generate_id('METRIC', 'metric'),
                    'supplier_id': supplier_id,
                    'metric_period': metric_period,
                    'total_pos_issued': total_pos,
                    'pos_delivered_ontime': ontime_pos,
                    'ontime_delivery_pct': round(ontime_pct, 2),
                    'average_lead_time_days': round(random.uniform(20, 45), 1),
                    'total_quantity_received': round(total_qty, 4),
                    'quantity_accepted': round(accepted_qty, 4),
                    'quantity_rejected': round(rejected_qty, 4),
                    'defect_ppm': int((rejected_qty / total_qty) * 1000000),
                    'quality_acceptance_pct': round(acceptance_pct, 2),
                    'rfqs_sent': rfqs_sent,
                    'rfqs_responded': rfqs_responded,
                    'response_rate_pct': round(response_rate, 2),
                    'avg_response_time_hours': round(random.uniform(12, 72), 2),
                    'total_spend': float(Decimal(str(random.uniform(50000, 500000))).quantize(Decimal('0.01'))),
                    'invoice_accuracy_pct': round(random.uniform(95, 100), 2),
                    'overall_score': overall_score,
                    'performance_rating': rating,
                    'created_at': metric_date.strftime('%Y-%m-%d %H:%M:%S')
                }
                self.performance_metrics.append(metric)
                
                # Generate scorecard for this period
                scorecard = {
                    'scorecard_id': self.generate_id('SCORECARD', 'scorecard'),
                    'supplier_id': supplier_id,
                    'scorecard_period': metric_period,
                    'scorecard_type': 'monthly',
                    'delivery_score': round(delivery_score, 2),
                    'quality_score': round(quality_score, 2),
                    'responsiveness_score': round(responsiveness_score, 2),
                    'commercial_score': round(commercial_score, 2),
                    'sustainability_score': round(random.uniform(70, 95), 2),
                    'overall_score': overall_score,
                    'supplier_rating': rating,
                    'action_required': overall_score < 75,
                    'published_to_supplier': months_ago < 3,  # Recent ones published
                    'created_at': metric_date.strftime('%Y-%m-%d %H:%M:%S')
                }
                self.scorecards.append(scorecard)
        
        logger.info(f"Generated {len(self.performance_metrics)} performance metrics")
        logger.info(f"Generated {len(self.scorecards)} scorecards")
        self.time_coordinator.time_coordination_delay("performance metrics")
    
    # ========================================================================
    # SUPPLIER INVOICES
    # ========================================================================
    
    def generate_supplier_invoices(self):
        """Generate supplier invoices with 3-way matching validation"""
        logger.info("Generating supplier invoices with 3-way matching...")
        
        matching_statuses = ['matched', 'variance', 'pending']
        
        for i in range(50):
            invoice_date = self.time_coordinator.generate_past_datetime(random.randint(1, 90))
            due_date = invoice_date + timedelta(days=random.choice([30, 45, 60]))
            
            # Get validated FK references
            supplier_id = self.get_valid_supplier_id()
            po_id = f'PO-{random.randint(1000, 5000):05d}'  # Realistic PO reference
            
            subtotal = Decimal(str(random.uniform(50000, 500000))).quantize(Decimal('0.01'))
            tax_rate = Decimal('0.18')  # 18% GST
            tax_amount = (subtotal * tax_rate).quantize(Decimal('0.01'))
            total_amount = subtotal + tax_amount
            
            matching_status = random.choice(matching_statuses)
            
            # Generate realistic variances with business logic
            if matching_status == 'variance':
                quantity_var = Decimal(str(random.uniform(-50, 50))).quantize(Decimal('0.01'))
                price_var = Decimal(str(random.uniform(-5000, 5000))).quantize(Decimal('0.01'))
            else:
                quantity_var = Decimal('0.00')
                price_var = Decimal('0.00')
            
            invoice = {
                'invoice_id': self.generate_id('INV', 'invoice'),
                'invoice_number': f'SI-{self.time_coordinator.current_date.year}-{i+1:05d}',
                'supplier_invoice_number': f'SUP-INV-{i+1:05d}',
                'supplier_id': supplier_id,
                'purchase_order_id': po_id,
                'invoice_date': invoice_date.strftime('%Y-%m-%d'),
                'due_date': due_date.strftime('%Y-%m-%d'),
                'subtotal': float(subtotal),
                'tax_amount': float(tax_amount),
                'total_amount': float(total_amount),
                'matching_status': matching_status,
                'po_match': matching_status in ['matched', 'variance'],
                'receipt_match': matching_status in ['matched', 'variance'],
                'price_match': matching_status == 'matched',
                'quantity_match': matching_status == 'matched',
                'quantity_variance': float(quantity_var),
                'price_variance': float(price_var),
                'total_variance': float(quantity_var + price_var),
                'invoice_status': random.choice(['received', 'approved', 'paid']) if matching_status == 'matched' else 'under_review',
                'payment_status': 'paid' if random.random() > 0.5 and matching_status == 'matched' else 'pending',
                'submitted_via': random.choice(['portal', 'email']),
                'created_at': invoice_date.strftime('%Y-%m-%d %H:%M:%S')
            }
            self.supplier_invoices.append(invoice)
            
            # Generate 2-5 invoice lines with 3-way matching validation
            num_lines = random.randint(2, 5)
            for j in range(num_lines):
                qty = Decimal(str(random.uniform(100, 1000))).quantize(Decimal('0.01'))
                unit_price = Decimal(str(random.uniform(50, 500))).quantize(Decimal('0.0001'))
                line_total = (qty * unit_price).quantize(Decimal('0.01'))
                
                # Generate PO and receipt data for 3-way matching
                po_qty = qty if matching_status == 'matched' else qty + Decimal(str(random.uniform(-10, 10))).quantize(Decimal('0.01'))
                received_qty = qty if matching_status == 'matched' else qty + Decimal(str(random.uniform(-5, 5))).quantize(Decimal('0.01'))
                po_unit_price = unit_price if matching_status == 'matched' else unit_price * Decimal(str(random.uniform(0.95, 1.05))).quantize(Decimal('0.0001'))
                
                # Validate 3-way matching
                invoice_data = {'quantity': float(qty), 'unit_price': float(unit_price)}
                po_data = {'quantity': float(po_qty), 'unit_price': float(po_unit_price)}
                receipt_data = {'quantity': float(received_qty)}
                
                match_result = self.validate_3_way_matching(invoice_data, po_data, receipt_data)
                
                line = {
                    'line_id': self.generate_id('INVLINE', 'inv_line'),
                    'invoice_id': invoice['invoice_id'],
                    'line_number': j + 1,
                    'material_id': self.get_valid_material_id(),
                    'line_description': f'Material line {j+1}',
                    'invoiced_quantity': float(qty),
                    'unit_of_measure': random.choice(['PC', 'KG', 'M']),
                    'unit_price': float(unit_price),
                    'line_total': float(line_total),
                    'po_quantity': float(po_qty),
                    'received_quantity': float(received_qty),
                    'po_unit_price': float(po_unit_price),
                    'match_status': match_result['status'],
                    'created_at': invoice_date.strftime('%Y-%m-%d %H:%M:%S')
                }
                
                line['quantity_variance'] = line['invoiced_quantity'] - line['received_quantity']
                line['price_variance'] = (line['unit_price'] - line['po_unit_price']) * line['invoiced_quantity']
                
                self.invoice_lines.append(line)
            
            # Generate enhanced 3-way match log
            variance_amount = float(price_var)
            variance_pct = (variance_amount / float(subtotal) * 100) if subtotal > 0 else 0
            within_tolerance = abs(variance_pct) < 2.0  # 2% tolerance
            
            match_log = {
                'log_id': self.generate_id('MATCH', 'match'),
                'invoice_id': invoice['invoice_id'],
                'match_timestamp': invoice_date.strftime('%Y-%m-%d %H:%M:%S'),
                'match_type': 'automatic',
                'po_id': po_id,
                'match_result': matching_status,
                'expected_amount': float(subtotal) if matching_status == 'matched' else float(subtotal + abs(price_var)),
                'actual_amount': float(subtotal),
                'variance_amount': variance_amount,
                'variance_pct': round(variance_pct, 2),
                'within_tolerance': within_tolerance,
                'tolerance_pct': 2.0,
                'action_taken': 'auto_approved' if matching_status == 'matched' and within_tolerance else 'pending_review'
            }
            self.three_way_matches.append(match_log)
        
        logger.info(f"Generated {len(self.supplier_invoices)} invoices, {len(self.invoice_lines)} lines")
        logger.info(f"  {len(self.three_way_matches)} 3-way match records")
        self.time_coordinator.time_coordination_delay("supplier invoices")
    
    # ========================================================================
    # SUPPLIER QUALIFICATION
    # ========================================================================
    
    def generate_supplier_qualification(self):
        """Generate supplier qualification records with enhanced validation"""
        logger.info("Generating supplier qualification data...")
        
        # Qualification for available suppliers (mix of statuses)
        statuses = ['approved', 'under_review', 'sample_testing', 'audit_completed']
        
        for i in range(min(20, 30)):  # Limit to reasonable number
            supplier_id = self.get_valid_supplier_id()
            qual_date = self.time_coordinator.generate_past_datetime(random.randint(30, 180))
            status = random.choice(statuses)
            
            qual = {
                'qualification_id': self.generate_id('QUAL', 'qual'),
                'supplier_id': supplier_id,
                'qualification_status': status,
                'business_license_verified': True,
                'tax_registration_verified': True,
                'bank_details_verified': True,
                'iso_certificate_verified': random.random() > 0.3,
                'financial_health_score': round(random.uniform(60, 95), 2),
                'production_capacity_verified': status in ['approved', 'audit_completed'],
                'quality_system_verified': status in ['approved', 'audit_completed'],
                'technical_capability_score': round(random.uniform(70, 95), 2),
                'audit_score': round(random.uniform(75, 95), 2) if status in ['approved', 'audit_completed', 'sample_testing'] else round(random.uniform(60, 85), 2),
                'sample_approved': status in ['approved', 'audit_completed'],
                'approved_date': qual_date.strftime('%Y-%m-%d') if status in ['approved', 'audit_completed'] else (qual_date.strftime('%Y-%m-%d') if random.random() < 0.30 else None),
                'created_at': qual_date.strftime('%Y-%m-%d %H:%M:%S')
            }
            self.qualification_records.append(qual)
            
            # Generate documents for this supplier
            doc_types = ['business_license', 'tax_certificate', 'iso_9001', 'bank_statement']
            for doc_type in doc_types:
                issue_date = qual_date - timedelta(days=random.randint(30, 365))
                expiry_date = issue_date + timedelta(days=365)
                
                doc = {
                    'document_id': self.generate_id('DOC', 'doc'),
                    'supplier_id': supplier_id,
                    'document_type': doc_type,
                    'document_name': f'{doc_type.upper()} - {supplier_id}',
                    'issue_date': issue_date.strftime('%Y-%m-%d'),
                    'expiry_date': expiry_date.strftime('%Y-%m-%d'),
                    'verified': True,
                    'verified_date': qual_date.strftime('%Y-%m-%d'),
                    'document_status': 'verified' if expiry_date > self.time_coordinator.current_date else 'expired',
                    'days_to_expiry': (expiry_date - self.time_coordinator.current_date).days,
                    'document_url': f'/documents/supplier/{supplier_id}/{doc_type}.pdf',
                    'created_at': issue_date.strftime('%Y-%m-%d %H:%M:%S')
                }
                self.supplier_documents.append(doc)
            
            qual = {
                'qualification_id': self.generate_id('QUAL', 'qual'),
                'supplier_id': supplier_id,
                'qualification_status': status,
                'business_license_verified': True,
                'tax_registration_verified': True,
                'bank_details_verified': True,
                'iso_certificate_verified': random.random() > 0.3,
                'financial_health_score': round(random.uniform(60, 95), 2),
                'production_capacity_verified': status in ['approved', 'audit_completed'],
                'quality_system_verified': status in ['approved', 'audit_completed'],
                'technical_capability_score': round(random.uniform(70, 95), 2),
                'audit_score': round(random.uniform(75, 95), 2) if status in ['approved', 'audit_completed', 'sample_testing'] else round(random.uniform(60, 85), 2),
                'sample_approved': status in ['approved', 'audit_completed'],
                'approved_date': qual_date.strftime('%Y-%m-%d') if status in ['approved', 'audit_completed'] else (qual_date.strftime('%Y-%m-%d') if random.random() < 0.30 else None),
                'created_at': qual_date.strftime('%Y-%m-%d %H:%M:%S')
            }
            self.qualification_records.append(qual)
            
            # Generate documents for this supplier
            doc_types = ['business_license', 'tax_certificate', 'iso_9001', 'bank_statement']
            for doc_type in doc_types:
                issue_date = qual_date - timedelta(days=random.randint(30, 365))
                expiry_date = issue_date + timedelta(days=365)
                
                doc = {
                    'document_id': self.generate_id('DOC', 'doc'),
                    'supplier_id': supplier_id,
                    'document_type': doc_type,
                    'document_name': f'{doc_type.upper()} - {supplier_id}',
                    'issue_date': issue_date.strftime('%Y-%m-%d'),
                    'expiry_date': expiry_date.strftime('%Y-%m-%d'),
                    'verified': True,
                    'verified_date': qual_date.strftime('%Y-%m-%d'),
                    'document_status': 'verified' if expiry_date > datetime.now() else 'expired',
                    'days_to_expiry': (expiry_date - datetime.now()).days,
                    'document_url': f'/documents/supplier/{supplier_id}/{doc_type}.pdf',
                    'created_at': issue_date.strftime('%Y-%m-%d %H:%M:%S')
                }
                self.supplier_documents.append(doc)
            
            # Generate audit record if qualified with enhanced validation
            if status in ['approved', 'audit_completed']:
                audit_date = qual_date + timedelta(days=random.randint(15, 45))
                
                audit = {
                    'audit_id': self.generate_id('AUDIT', 'audit'),
                    'audit_number': f'AUD-{self.time_coordinator.current_date.year}-{i+1:03d}',
                    'supplier_id': supplier_id,
                    'audit_type': 'initial',
                    'audit_scope': 'quality_system',
                    'planned_date': audit_date.strftime('%Y-%m-%d'),
                    'actual_date': audit_date.strftime('%Y-%m-%d'),
                    'audit_duration_hours': round(random.uniform(4, 8), 1),
                    'lead_auditor': self.get_valid_employee_id(),
                    'audit_score': round(random.uniform(75, 95), 2),
                    'audit_rating': random.choice(['excellent', 'satisfactory', 'needs_improvement']),
                    'major_findings': random.randint(0, 2),
                    'minor_findings': random.randint(0, 5),
                    'observations': random.randint(2, 10),
                    'audit_status': 'completed',
                    'created_at': audit_date.strftime('%Y-%m-%d %H:%M:%S')
                }
                self.supplier_audits.append(audit)
        
        logger.info(f"Generated {len(self.qualification_records)} qualification records")
        logger.info(f"  {len(self.supplier_documents)} supplier documents")
        logger.info(f"  {len(self.supplier_audits)} audit records")
        self.time_coordinator.time_coordination_delay("supplier qualification")
    
    # ========================================================================
    # PORTAL USERS
    # ========================================================================
    
    def generate_portal_users(self):
        """Generate supplier portal user accounts with validation"""
        logger.info("Generating supplier portal users...")
        
        # 1-3 users per available supplier
        for supplier_idx in range(min(20, 30)):
            supplier_id = self.get_valid_supplier_id()
            num_users = random.randint(1, 3)
            
            for i in range(num_users):
                roles = ['admin', 'sales', 'accounts', 'quality']
                role = roles[min(i, len(roles)-1)]
                
                user = {
                    'portal_user_id': self.generate_id('PORTALUSER', 'user'),
                    'supplier_id': supplier_id,
                    'user_email': f'user{i+1}@{supplier_id.lower()}.com',
                    'user_name': f'User {i+1} - {supplier_id}',
                    'user_phone': f'+91-{random.randint(7000000000, 9999999999)}',
                    'user_role': role,
                    'can_view_rfqs': True,
                    'can_submit_quotes': role in ['admin', 'sales'],
                    'can_view_pos': True,
                    'can_submit_invoices': role in ['admin', 'accounts'],
                    'can_view_payments': role in ['admin', 'accounts'],
                    'can_view_performance': role == 'admin',
                    'is_active': True,
                    'login_count': random.randint(5, 100),
                    'password_reset_required': False,
                    'created_at': self.time_coordinator.current_date.strftime('%Y-%m-%d %H:%M:%S')
                }
                self.portal_users.append(user)
        
        logger.info(f"Generated {len(self.portal_users)} portal users")
        self.time_coordinator.time_coordination_delay("portal users")
    
    def _print_summary(self):
        logger.info(f"\n{'='*80}")
        logger.info(f"Supplier Portal Data Generation Complete!")
        logger.info(f"{'='*80}")
        logger.info(f"\nPurchase Requisitions:")
        logger.info(f"  Requisitions: {len(self.purchase_requisitions)}")
        logger.info(f"  Requisition Lines: {len(self.req_lines)}")
        
        logger.info(f"\nRFQ Management:")
        logger.info(f"  RFQs: {len(self.rfq_headers)}")
        logger.info(f"  RFQ Lines: {len(self.rfq_lines)}")
        logger.info(f"  Supplier Invitations: {len(self.rfq_suppliers)}")
        logger.info(f"  Responses: {len(self.rfq_responses)}")
        logger.info(f"  Response Lines: {len(self.rfq_response_lines)}")
        
        logger.info(f"\nContracts & Pricing:")
        logger.info(f"  Supplier Contracts: {len(self.supplier_contracts)}")
        logger.info(f"  Contract Pricing: {len(self.contract_pricing)}")
        
        logger.info(f"\nPerformance Management:")
        logger.info(f"  Performance Metrics: {len(self.performance_metrics)}")
        logger.info(f"  Scorecards: {len(self.scorecards)}")
        
        logger.info(f"\nInvoicing & Matching:")
        logger.info(f"  Supplier Invoices: {len(self.supplier_invoices)}")
        logger.info(f"  Invoice Lines: {len(self.invoice_lines)}")
        logger.info(f"  3-Way Match Logs: {len(self.three_way_matches)}")
        
        logger.info(f"\nQualification:")
        logger.info(f"  Qualification Records: {len(self.qualification_records)}")
        logger.info(f"  Supplier Documents: {len(self.supplier_documents)}")
        logger.info(f"  Supplier Audits: {len(self.supplier_audits)}")
        
        logger.info(f"\nPortal Access:")
        logger.info(f"  Portal Users: {len(self.portal_users)}")
    
    def to_json(self, output_file='supplier_portal_data.json'):
        """Export to JSON with flat structure matching actual table names"""
        logger.info(f"\nExporting to JSON...")
        
        # Generate missing tables
        supplier_communications = self._generate_supplier_communications()
        audit_findings = self._generate_audit_findings()
        quote_comparison = self._generate_quote_comparison()
        supplier_notifications = self._generate_supplier_notifications()
        supplier_rating_history = self._generate_supplier_rating_history()
        three_way_match_log = self._generate_three_way_match_log()
        supplier_portal_integration_log = self._generate_supplier_portal_integration_log()
        
        data = {
            # RFQ Management - 5 tables
            'rfq_headers': self.rfq_headers,
            'rfq_lines': self.rfq_lines,
            'rfq_suppliers': self.rfq_suppliers,
            'rfq_responses': self.rfq_responses,
            'rfq_response_lines': self.rfq_response_lines,
            
            # Supplier Contracts - 2 tables
            'supplier_contracts': self.supplier_contracts,
            'contract_pricing': self.contract_pricing,
            
            # Performance Management - 3 tables
            'supplier_performance_metrics': self.performance_metrics,
            'supplier_scorecards': self.scorecards,
            'supplier_audits': self.supplier_audits,
            
            # Invoicing & Payments - 2 tables
            'supplier_invoices': self.supplier_invoices,
            'supplier_invoice_lines': self.invoice_lines,
            
            # Supplier Qualification - 1 table
            'supplier_qualification': self.qualification_records,
            
            # Supplier Management - 2 tables
            'supplier_documents': self.supplier_documents,
            'supplier_communications': supplier_communications,
            
            # Portal Users - 1 table
            'supplier_portal_users': self.portal_users,
            
            # Purchase Requisitions - 2 tables
            'purchase_requisitions': self.purchase_requisitions,
            'purchase_requisition_lines': self.req_lines,
            
            # Additional tables from schema
            'audit_findings': audit_findings,
            'quote_comparison': quote_comparison,
            'supplier_notifications': supplier_notifications,
            'supplier_rating_history': supplier_rating_history,
            'three_way_match_log': three_way_match_log,
            'supplier_portal_integration_log': supplier_portal_integration_log
        }
        
        with open(output_file, 'w') as f:
            json.dump(data, f, indent=2)
        
        logger.info(f"Data exported to {output_file}")
    
    def _generate_supplier_communications(self):
        """Generate supplier communication records aligned to schema"""
        communications = []
        for i in range(20):
            supplier_id = self.get_valid_supplier_id()
            created_at = self.time_coordinator.generate_past_datetime(random.randint(0, 30))
            from_party = random.choice(['buyer', 'supplier'])
            ref_type = random.choice(['rfq', 'purchase_order', 'invoice', 'quality_issue', 'general'])
            # small chance of attachments (array)
            attach_count = random.choice([0, 0, 1, 2])
            attachments = [f"/attachments/{supplier_id}/comm_{i+1}_{k+1}.pdf" for k in range(attach_count)]
            communications.append({
                'communication_id': f"COMM-{i+1:05d}",
                'supplier_id': supplier_id,
                'from_party': from_party,
                'subject': f"Communication {i+1}",
                'message_body': f"Message content for communication {i+1}",
                'reference_type': ref_type,
                'reference_id': None,
                'message_status': random.choice(['sent', 'read', 'replied', 'archived']),
                'read_at': (created_at + timedelta(days=random.randint(0, 5))).strftime('%Y-%m-%d %H:%M:%S') if random.random() > 0.4 else None,
                'attachment_urls': attachments,
                'parent_message_id': None,
                'created_at': created_at.strftime('%Y-%m-%d %H:%M:%S')
            })
        return communications
    
    def _generate_audit_findings(self):
        """Generate audit findings for supplier audits"""
        findings = []
        for i in range(25):
            status = random.choice(['open', 'in_progress', 'closed', 'pending_verification'])
            # Always populate actual_closure_date if status is closed or pending_verification
            # Otherwise populate with 40% probability
            if status in ['closed', 'pending_verification']:
                actual_closure_date = self.time_coordinator.generate_future_datetime(random.randint(1, 60)).strftime('%Y-%m-%d')
            elif random.random() < 0.40:
                actual_closure_date = self.time_coordinator.generate_future_datetime(random.randint(1, 60)).strftime('%Y-%m-%d')
            else:
                actual_closure_date = None
            
            findings.append({
                'audit_finding_id': f"AUDFIND-{i+1}",
                'supplier_audit_id': f"SUPP-AUDIT-{random.randint(1, 10):04d}",
                'finding_type': random.choice(['critical', 'major', 'minor', 'observation']),
                'finding_description': f"Audit finding {i+1}",
                'root_cause': f"Root cause analysis {i+1}",
                'corrective_action': f"Corrective action for finding",
                'target_closure_date': self.time_coordinator.generate_future_datetime(random.randint(7, 90)).strftime('%Y-%m-%d'),
                'actual_closure_date': actual_closure_date,
                'status': status
            })
        return findings
    
    def _generate_quote_comparison(self):
        """Generate quote comparison records"""
        comparisons = []
        for i in range(15):
            comparisons.append({
                'quote_comparison_id': f"QUOTCOMP-{i+1}",
                'rfq_id': f"RFQ-{random.randint(1, 20):04d}",
                'supplier_1_id': f"SUP-{random.randint(1, 30):04d}",
                'supplier_2_id': f"SUP-{random.randint(1, 30):04d}",
                'supplier_3_id': f"SUP-{random.randint(1, 30):04d}",
                'comparison_date': (datetime.now() - timedelta(days=random.randint(0, 30))).strftime('%Y-%m-%d'),
                'winner_supplier_id': f"SUP-{random.randint(1, 30):04d}",
                'selection_reason': random.choice(['price', 'quality', 'delivery', 'combination']),
                'notes': f"Quote comparison analysis {i+1}"
            })
        return comparisons
    
    def _generate_supplier_notifications(self):
        """Generate supplier notification records aligned to schema"""
        notifications = []
        for i in range(25):
            supplier_id = self.get_valid_supplier_id()
            created_at = self.time_coordinator.generate_past_datetime(random.randint(0, 7))
            notifications.append({
                'notification_id': f"NOTIF-{i+1:05d}",
                'supplier_id': supplier_id,
                'notification_type': random.choice(['new_rfq', 'po_issued', 'payment_made', 'performance_review', 'document_expiring', 'audit_scheduled']),
                'notification_title': f"Notification {i+1}",
                'notification_message': "Notification message content",
                'reference_type': random.choice(['rfq', 'purchase_order', 'invoice', 'quality_issue', None]),
                'reference_id': None,
                'priority': random.choice(['low', 'normal', 'high', 'urgent']),
                'notification_status': random.choice(['unread', 'read', 'actioned', 'dismissed']),
                'read_at': (created_at + timedelta(days=random.randint(0, 3))).strftime('%Y-%m-%d %H:%M:%S') if random.random() > 0.5 else None,
                'sent_via_email': True,
                'sent_via_portal': True,
                'created_at': created_at.strftime('%Y-%m-%d %H:%M:%S')
            })
        return notifications
    
    def _generate_supplier_rating_history(self):
        """Generate supplier rating history records"""
        ratings = []
        for i in range(30):
            ratings.append({
                'rating_history_id': f"RATEHIST-{i+1}",
                'supplier_id': f"SUP-{random.randint(1, 30):04d}",
                'rating_date': (datetime.now() - timedelta(days=random.randint(0, 90))).strftime('%Y-%m-%d'),
                'overall_rating': round(random.uniform(2, 5), 1),
                'quality_rating': round(random.uniform(2, 5), 1),
                'delivery_rating': round(random.uniform(2, 5), 1),
                'price_rating': round(random.uniform(2, 5), 1),
                'service_rating': round(random.uniform(2, 5), 1),
                'comments': f"Rating review {i+1}",
                'rated_by_employee_id': f"EMP-{random.randint(1, 50):06d}"
            })
        return ratings
    
    def _generate_three_way_match_log(self):
        """Generate three-way match log records (PO, Invoice, Receipt matching)"""
        matches = []
        for i in range(30):
            status = random.choice(['matched', 'variance', 'blocked', 'exception'])
            # Resolve dates for matched/variance statuses with 85% probability, exception with 60%
            if status == 'matched' and random.random() < 0.95:
                resolved_date = (datetime.now() - timedelta(days=random.randint(0, 7))).strftime('%Y-%m-%d')
            elif status in ['variance', 'blocked'] and random.random() < 0.80:
                resolved_date = (datetime.now() - timedelta(days=random.randint(0, 14))).strftime('%Y-%m-%d')
            elif status == 'exception' and random.random() < 0.60:
                resolved_date = (datetime.now() - timedelta(days=random.randint(1, 30))).strftime('%Y-%m-%d')
            else:
                resolved_date = None
            
            matches.append({
                'three_way_match_id': f"3WM-{i+1}",
                'purchase_order_id': f"PO-{random.randint(1000, 5000):05d}",
                'supplier_invoice_id': f"INV-{random.randint(1000, 5000):05d}",
                'goods_receipt_id': f"GR-{random.randint(1000, 5000):05d}",
                'match_date': (datetime.now() - timedelta(days=random.randint(0, 30))).strftime('%Y-%m-%d'),
                'po_amount': round(random.uniform(1000, 100000), 2),
                'invoice_amount': round(random.uniform(1000, 100000), 2),
                'variance_percent': round(random.uniform(-5, 5), 2),
                'match_status': status,
                'resolution': f"Resolution for match {i+1}" if status in ['exception', 'variance', 'blocked'] else 'None',
                'resolved_date': resolved_date
            })
        return matches
    
    def _generate_supplier_portal_integration_log(self):
        """Generate supplier portal integration log records aligned to schema"""
        from datetime import datetime, timedelta
        logs = []
        for i in range(25):
            ts = (datetime.now() - timedelta(hours=random.randint(0, 168)))
            logs.append({
                'log_id': f"SUPPINT-{i+1:05d}",
                'log_timestamp': ts.strftime('%Y-%m-%d %H:%M:%S'),
                'integration_type': random.choice(['rfq_to_suppliers', 'quote_to_po', 'po_to_erp', 'invoice_to_ap', 'performance_to_dashboard', 'contract_to_pricing']),
                'source_system': random.choice(['portal', 'erp', 'wms', 'financial']),
                'target_system': random.choice(['erp', 'portal', 'wms', 'financial']),
                'source_document_type': random.choice(['rfq', 'po', 'invoice', 'performance', 'contract']),
                'source_document_id': None,
                'target_document_type': None,
                'target_document_id': None,
                'integration_status': random.choice(['success', 'partial', 'failed']),
                'error_message': None
                # 'integration_data': None  # leave out to avoid jsonb casting issues
            })
        return logs


if __name__ == "__main__":
    from pathlib import Path
    import time
    
    start_time = time.time()
    
    # Get the directory of this script (data folder)
    script_dir = Path(__file__).parent
    
    logger.info(f"\n{'='*80}")
    logger.info(f"GenIMS Supplier Portal Data Generator - Enterprise Edition")
    logger.info(f"{'='*80}")
    
    generator = SupplierPortalDataGenerator()
    generator.generate_all_data()
    
    # Export to JSON (in same folder as script)
    json_file = script_dir / "supplier_portal_data.json"
    generator.to_json(str(json_file))
    
    end_time = time.time()
    execution_time = end_time - start_time
    
    logger.info(f"\n{'='*80}")
    logger.info(f"Supplier Portal Data Generation Complete!")
    logger.info(f"Total Execution Time: {execution_time:.2f} seconds")
    logger.info(f"Enterprise Features: TimeCoordinator ✓ | FK Validation ✓ | Business Logic ✓")
    logger.info(f"{'='*80}")
