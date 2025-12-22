#!/usr/bin/env python3
"""
GenIMS Supplier Portal Data Generator
Generates RFQs, contracts, performance metrics, invoices, and supplier portal data
"""

import random
import json
from datetime import datetime, timedelta
from typing import List, Dict

class SupplierPortalDataGenerator:
    def __init__(self):
        """Initialize data generator"""
        print("Initializing Supplier Portal Data Generator...")
        
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
        
        # Reference data (would come from existing tables)
        self.suppliers = [f'SUPPLIER-{i:06d}' for i in range(1, 21)]  # 20 suppliers
        self.materials = [f'MATERIAL-{i:06d}' for i in range(1, 101)]  # 100 materials
        self.employees = [f'EMP-{i:06d}' for i in range(1, 51)]  # 50 employees
        self.purchase_orders = [f'PO-{i:06d}' for i in range(1, 201)]  # 200 POs
        
        # Counters
        self.counters = {
            'rfq': 1, 'rfq_line': 1, 'rfq_response': 1, 'response_line': 1,
            'contract': 1, 'pricing': 1, 'metric': 1, 'scorecard': 1,
            'invoice': 1, 'inv_line': 1, 'match': 1, 'qual': 1,
            'doc': 1, 'audit': 1, 'user': 1, 'req': 1, 'req_line': 1
        }
    
    def generate_id(self, prefix: str, counter_key: str) -> str:
        id_val = f"{prefix}-{str(self.counters[counter_key]).zfill(6)}"
        self.counters[counter_key] += 1
        return id_val
    
    def generate_all_data(self):
        """Generate all supplier portal data"""
        print(f"\n{'='*80}")
        print(f"Generating Supplier Portal Data")
        print(f"{'='*80}\n")
        
        # Generate data
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
        """Generate purchase requisitions"""
        print("Generating purchase requisitions...")
        
        statuses = ['draft', 'submitted', 'approved', 'rejected', 'converted_to_rfq']
        
        for i in range(30):
            req_date = datetime.now() - timedelta(days=random.randint(1, 90))
            required_by = req_date + timedelta(days=random.randint(30, 90))
            status = random.choice(statuses)
            
            req = {
                'requisition_id': self.generate_id('REQ', 'req'),
                'requisition_number': f'PR-{datetime.now().year}-{i+1:05d}',
                'requested_by': random.choice(self.employees),
                'requisition_date': req_date.strftime('%Y-%m-%d'),
                'required_by_date': required_by.strftime('%Y-%m-%d'),
                'requisition_type': random.choice(['standard', 'urgent', 'capital']),
                'purpose': 'Material requirement for production',
                'estimated_total': round(random.uniform(50000, 500000), 2),
                'requisition_status': status,
                'created_at': req_date.strftime('%Y-%m-%d %H:%M:%S')
            }
            self.purchase_requisitions.append(req)
            
            # Generate 2-5 lines
            num_lines = random.randint(2, 5)
            for j in range(num_lines):
                line = {
                    'line_id': self.generate_id('REQLINE', 'req_line'),
                    'requisition_id': req['requisition_id'],
                    'line_number': j + 1,
                    'material_id': random.choice(self.materials),
                    'item_description': f'Material item {j+1}',
                    'quantity': round(random.uniform(100, 1000), 2),
                    'unit_of_measure': random.choice(['PC', 'KG', 'M', 'L']),
                    'estimated_unit_price': round(random.uniform(50, 500), 2),
                    'created_at': req_date.strftime('%Y-%m-%d %H:%M:%S')
                }
                line['estimated_total'] = line['quantity'] * line['estimated_unit_price']
                self.req_lines.append(line)
        
        print(f"Generated {len(self.purchase_requisitions)} requisitions, {len(self.req_lines)} lines")
    
    # ========================================================================
    # RFQ - REQUEST FOR QUOTE
    # ========================================================================
    
    def generate_rfqs(self):
        """Generate RFQs with responses"""
        print("Generating RFQs and responses...")
        
        statuses = ['published', 'response_period', 'evaluation', 'awarded']
        
        for i in range(20):
            rfq_date = datetime.now() - timedelta(days=random.randint(1, 60))
            deadline = rfq_date + timedelta(days=random.randint(7, 21))
            status = random.choice(statuses)
            
            rfq = {
                'rfq_id': self.generate_id('RFQ', 'rfq'),
                'rfq_number': f'RFQ-{datetime.now().year}-{i+1:05d}',
                'rfq_title': f'RFQ for {random.choice(["Raw Materials", "Components", "Services", "Equipment"])}',
                'rfq_description': 'Request for quotation for materials',
                'rfq_type': random.choice(['standard', 'urgent', 'blanket']),
                'requested_by': random.choice(self.employees),
                'rfq_date': rfq_date.strftime('%Y-%m-%d'),
                'response_deadline': deadline.strftime('%Y-%m-%d'),
                'total_estimated_value': round(random.uniform(100000, 2000000), 2),
                'rfq_status': status,
                'published_date': rfq_date.strftime('%Y-%m-%d') if status != 'draft' else None,
                'created_at': rfq_date.strftime('%Y-%m-%d %H:%M:%S')
            }
            self.rfq_headers.append(rfq)
            
            # Generate 2-8 line items
            num_lines = random.randint(2, 8)
            for j in range(num_lines):
                line = {
                    'line_id': self.generate_id('RFQLINE', 'rfq_line'),
                    'rfq_id': rfq['rfq_id'],
                    'line_number': j + 1,
                    'item_type': random.choice(['material', 'service']),
                    'material_id': random.choice(self.materials),
                    'item_description': f'Material specification {j+1}',
                    'quantity': round(random.uniform(100, 5000), 2),
                    'unit_of_measure': random.choice(['PC', 'KG', 'M']),
                    'target_price': round(random.uniform(50, 500), 2),
                    'created_at': rfq_date.strftime('%Y-%m-%d %H:%M:%S')
                }
                line['estimated_total'] = line['quantity'] * line['target_price']
                self.rfq_lines.append(line)
            
            # Invite 3-5 suppliers
            invited_suppliers = random.sample(self.suppliers, random.randint(3, 5))
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
                
                # Generate response if supplier responded
                if invitation['response_status'] == 'responded':
                    response_date = rfq_date + timedelta(days=random.randint(1, 14))
                    
                    response = {
                        'response_id': self.generate_id('RFQRESP', 'rfq_response'),
                        'response_number': f'QT-{datetime.now().year}-{self.counters["rfq_response"]:05d}',
                        'rfq_id': rfq['rfq_id'],
                        'supplier_id': supplier_id,
                        'response_date': response_date.strftime('%Y-%m-%d %H:%M:%S'),
                        'valid_until_date': (response_date + timedelta(days=30)).strftime('%Y-%m-%d'),
                        'payment_terms': random.choice(['30 days', '60 days', '90 days']),
                        'response_status': random.choice(['submitted', 'shortlisted', 'awarded']),
                        'created_at': response_date.strftime('%Y-%m-%d %H:%M:%S')
                    }
                    
                    # Generate response lines
                    total_quoted = 0
                    for line in [l for l in self.rfq_lines if l['rfq_id'] == rfq['rfq_id']]:
                        # Quote slightly higher or lower than target
                        variance = random.uniform(-0.15, 0.25)
                        unit_price = line['target_price'] * (1 + variance)
                        
                        resp_line = {
                            'response_line_id': self.generate_id('RESPLINE', 'response_line'),
                            'response_id': response['response_id'],
                            'rfq_line_id': line['line_id'],
                            'line_number': line['line_number'],
                            'unit_price': round(unit_price, 4),
                            'total_price': round(unit_price * line['quantity'], 2),
                            'lead_time_days': random.randint(15, 60),
                            'meets_specifications': random.random() > 0.1,  # 90% meet specs
                            'created_at': response_date.strftime('%Y-%m-%d %H:%M:%S')
                        }
                        self.rfq_response_lines.append(resp_line)
                        total_quoted += resp_line['total_price']
                    
                    response['total_quoted_value'] = round(total_quoted, 2)
                    self.rfq_responses.append(response)
        
        print(f"Generated {len(self.rfq_headers)} RFQs, {len(self.rfq_lines)} lines")
        print(f"  {len(self.rfq_suppliers)} supplier invitations")
        print(f"  {len(self.rfq_responses)} responses, {len(self.rfq_response_lines)} response lines")
    
    # ========================================================================
    # SUPPLIER CONTRACTS
    # ========================================================================
    
    def generate_supplier_contracts(self):
        """Generate supplier contracts and pricing"""
        print("Generating supplier contracts...")
        
        # Create contracts for top 10 suppliers
        for i, supplier_id in enumerate(self.suppliers[:10]):
            start_date = datetime.now() - timedelta(days=random.randint(30, 365))
            end_date = start_date + timedelta(days=365)
            
            contract = {
                'contract_id': self.generate_id('CONTRACT', 'contract'),
                'contract_number': f'CONT-{datetime.now().year}-{i+1:03d}',
                'supplier_id': supplier_id,
                'contract_name': f'Annual Supply Agreement {datetime.now().year}',
                'contract_type': random.choice(['price_agreement', 'blanket_order', 'framework']),
                'start_date': start_date.strftime('%Y-%m-%d'),
                'end_date': end_date.strftime('%Y-%m-%d'),
                'payment_terms': random.choice(['30 days', '45 days', '60 days']),
                'committed_annual_value': round(random.uniform(500000, 5000000), 2),
                'auto_renew': random.random() > 0.5,
                'contract_status': 'active' if end_date > datetime.now() else 'expired',
                'actual_spend_to_date': round(random.uniform(100000, 1000000), 2),
                'orders_placed': random.randint(10, 50),
                'created_at': start_date.strftime('%Y-%m-%d %H:%M:%S')
            }
            self.supplier_contracts.append(contract)
            
            # Generate pricing for 5-10 materials
            num_materials = random.randint(5, 10)
            for j, material_id in enumerate(random.sample(self.materials, num_materials)):
                pricing = {
                    'pricing_id': self.generate_id('PRICING', 'pricing'),
                    'contract_id': contract['contract_id'],
                    'material_id': material_id,
                    'unit_price': round(random.uniform(50, 500), 4),
                    'effective_from': start_date.strftime('%Y-%m-%d'),
                    'effective_to': end_date.strftime('%Y-%m-%d'),
                    'standard_lead_time_days': random.randint(15, 45),
                    'is_active': contract['contract_status'] == 'active',
                    'created_at': start_date.strftime('%Y-%m-%d %H:%M:%S')
                }
                self.contract_pricing.append(pricing)
        
        print(f"Generated {len(self.supplier_contracts)} contracts, {len(self.contract_pricing)} pricing records")
    
    # ========================================================================
    # SUPPLIER PERFORMANCE
    # ========================================================================
    
    def generate_performance_metrics(self):
        """Generate supplier performance metrics and scorecards"""
        print("Generating supplier performance metrics...")
        
        # Last 6 months of data for each supplier
        for supplier_id in self.suppliers:
            for months_ago in range(6):
                metric_date = datetime.now() - timedelta(days=30 * months_ago)
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
                
                # Calculate overall score (weighted average)
                delivery_score = ontime_pct
                quality_score = acceptance_pct
                responsiveness_score = response_rate
                commercial_score = random.uniform(85, 98)
                
                overall_score = (
                    delivery_score * 0.3 +
                    quality_score * 0.4 +
                    responsiveness_score * 0.2 +
                    commercial_score * 0.1
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
                    'total_spend': round(random.uniform(50000, 500000), 2),
                    'invoice_accuracy_pct': round(random.uniform(95, 100), 2),
                    'overall_score': round(overall_score, 2),
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
                    'overall_score': round(overall_score, 2),
                    'supplier_rating': rating,
                    'action_required': overall_score < 75,
                    'published_to_supplier': months_ago < 3,  # Recent ones published
                    'created_at': metric_date.strftime('%Y-%m-%d %H:%M:%S')
                }
                self.scorecards.append(scorecard)
        
        print(f"Generated {len(self.performance_metrics)} performance metrics")
        print(f"Generated {len(self.scorecards)} scorecards")
    
    # ========================================================================
    # SUPPLIER INVOICES
    # ========================================================================
    
    def generate_supplier_invoices(self):
        """Generate supplier invoices with 3-way matching"""
        print("Generating supplier invoices...")
        
        matching_statuses = ['matched', 'variance', 'pending']
        
        for i in range(50):
            invoice_date = datetime.now() - timedelta(days=random.randint(1, 90))
            due_date = invoice_date + timedelta(days=random.choice([30, 45, 60]))
            
            supplier_id = random.choice(self.suppliers)
            po_id = random.choice(self.purchase_orders)
            
            subtotal = round(random.uniform(50000, 500000), 2)
            tax_rate = 0.18  # 18% GST
            tax_amount = round(subtotal * tax_rate, 2)
            total_amount = subtotal + tax_amount
            
            matching_status = random.choice(matching_statuses)
            
            # Introduce realistic variances
            if matching_status == 'variance':
                quantity_var = round(random.uniform(-50, 50), 2)
                price_var = round(random.uniform(-5000, 5000), 2)
            else:
                quantity_var = 0
                price_var = 0
            
            invoice = {
                'invoice_id': self.generate_id('INV', 'invoice'),
                'invoice_number': f'SI-{datetime.now().year}-{i+1:05d}',
                'supplier_invoice_number': f'SUP-INV-{i+1:05d}',
                'supplier_id': supplier_id,
                'purchase_order_id': po_id,
                'invoice_date': invoice_date.strftime('%Y-%m-%d'),
                'due_date': due_date.strftime('%Y-%m-%d'),
                'subtotal': subtotal,
                'tax_amount': tax_amount,
                'total_amount': total_amount,
                'matching_status': matching_status,
                'po_match': matching_status in ['matched', 'variance'],
                'receipt_match': matching_status in ['matched', 'variance'],
                'price_match': matching_status == 'matched',
                'quantity_match': matching_status == 'matched',
                'quantity_variance': quantity_var,
                'price_variance': price_var,
                'total_variance': quantity_var + price_var,
                'invoice_status': random.choice(['received', 'approved', 'paid']) if matching_status == 'matched' else 'under_review',
                'payment_status': 'paid' if random.random() > 0.5 and matching_status == 'matched' else 'pending',
                'submitted_via': random.choice(['portal', 'email']),
                'created_at': invoice_date.strftime('%Y-%m-%d %H:%M:%S')
            }
            self.supplier_invoices.append(invoice)
            
            # Generate 2-5 invoice lines
            num_lines = random.randint(2, 5)
            line_subtotal = 0
            for j in range(num_lines):
                qty = round(random.uniform(100, 1000), 2)
                unit_price = round(random.uniform(50, 500), 4)
                line_total = round(qty * unit_price, 2)
                
                line = {
                    'line_id': self.generate_id('INVLINE', 'inv_line'),
                    'invoice_id': invoice['invoice_id'],
                    'line_number': j + 1,
                    'material_id': random.choice(self.materials),
                    'line_description': f'Material line {j+1}',
                    'invoiced_quantity': qty,
                    'unit_of_measure': random.choice(['PC', 'KG', 'M']),
                    'unit_price': unit_price,
                    'line_total': line_total,
                    'po_quantity': qty if matching_status == 'matched' else qty + random.uniform(-10, 10),
                    'received_quantity': qty if matching_status == 'matched' else qty + random.uniform(-5, 5),
                    'po_unit_price': unit_price if matching_status == 'matched' else unit_price * random.uniform(0.95, 1.05),
                    'match_status': matching_status,
                    'created_at': invoice_date.strftime('%Y-%m-%d %H:%M:%S')
                }
                
                line['quantity_variance'] = line['invoiced_quantity'] - line['received_quantity']
                line['price_variance'] = (line['unit_price'] - line['po_unit_price']) * line['invoiced_quantity']
                
                self.invoice_lines.append(line)
                line_subtotal += line_total
            
            # Generate 3-way match log
            match_log = {
                'log_id': self.generate_id('MATCH', 'match'),
                'invoice_id': invoice['invoice_id'],
                'match_timestamp': invoice_date.strftime('%Y-%m-%d %H:%M:%S'),
                'match_type': 'automatic',
                'po_id': po_id,
                'match_result': matching_status,
                'expected_amount': subtotal if matching_status == 'matched' else subtotal + abs(price_var),
                'actual_amount': subtotal,
                'variance_amount': price_var,
                'variance_pct': round((price_var / subtotal * 100) if subtotal > 0 else 0, 2),
                'within_tolerance': abs(price_var / subtotal * 100) < 2 if subtotal > 0 else True,
                'tolerance_pct': 2.0,
                'action_taken': 'auto_approved' if matching_status == 'matched' else 'pending_review'
            }
            self.three_way_matches.append(match_log)
        
        print(f"Generated {len(self.supplier_invoices)} invoices, {len(self.invoice_lines)} lines")
        print(f"  {len(self.three_way_matches)} 3-way match records")
    
    # ========================================================================
    # SUPPLIER QUALIFICATION
    # ========================================================================
    
    def generate_supplier_qualification(self):
        """Generate supplier qualification records"""
        print("Generating supplier qualification data...")
        
        # Qualification for 10 suppliers (mix of statuses)
        statuses = ['approved', 'under_review', 'sample_testing', 'audit_completed']
        
        for i, supplier_id in enumerate(self.suppliers[:10]):
            qual_date = datetime.now() - timedelta(days=random.randint(30, 180))
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
                'audit_score': round(random.uniform(75, 95), 2) if status in ['approved', 'audit_completed'] else None,
                'sample_approved': status == 'approved',
                'approved_date': qual_date.strftime('%Y-%m-%d') if status == 'approved' else None,
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
            
            # Generate audit record if qualified
            if status in ['approved', 'audit_completed']:
                audit_date = qual_date + timedelta(days=random.randint(15, 45))
                
                audit = {
                    'audit_id': self.generate_id('AUDIT', 'audit'),
                    'audit_number': f'AUD-{datetime.now().year}-{i+1:03d}',
                    'supplier_id': supplier_id,
                    'audit_type': 'initial',
                    'audit_scope': 'quality_system',
                    'planned_date': audit_date.strftime('%Y-%m-%d'),
                    'actual_date': audit_date.strftime('%Y-%m-%d'),
                    'audit_duration_hours': round(random.uniform(4, 8), 1),
                    'lead_auditor': random.choice(self.employees),
                    'audit_score': round(random.uniform(75, 95), 2),
                    'audit_rating': random.choice(['excellent', 'satisfactory', 'needs_improvement']),
                    'major_findings': random.randint(0, 2),
                    'minor_findings': random.randint(0, 5),
                    'observations': random.randint(2, 10),
                    'audit_status': 'completed',
                    'created_at': audit_date.strftime('%Y-%m-%d %H:%M:%S')
                }
                self.supplier_audits.append(audit)
        
        print(f"Generated {len(self.qualification_records)} qualification records")
        print(f"  {len(self.supplier_documents)} supplier documents")
        print(f"  {len(self.supplier_audits)} audit records")
    
    # ========================================================================
    # PORTAL USERS
    # ========================================================================
    
    def generate_portal_users(self):
        """Generate supplier portal user accounts"""
        print("Generating supplier portal users...")
        
        # 1-3 users per supplier
        for supplier_id in self.suppliers:
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
                    'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                self.portal_users.append(user)
        
        print(f"Generated {len(self.portal_users)} portal users")
    
    def _print_summary(self):
        print(f"\n{'='*80}")
        print(f"Supplier Portal Data Generation Complete!")
        print(f"{'='*80}")
        print(f"\nPurchase Requisitions:")
        print(f"  Requisitions: {len(self.purchase_requisitions)}")
        print(f"  Requisition Lines: {len(self.req_lines)}")
        
        print(f"\nRFQ Management:")
        print(f"  RFQs: {len(self.rfq_headers)}")
        print(f"  RFQ Lines: {len(self.rfq_lines)}")
        print(f"  Supplier Invitations: {len(self.rfq_suppliers)}")
        print(f"  Responses: {len(self.rfq_responses)}")
        print(f"  Response Lines: {len(self.rfq_response_lines)}")
        
        print(f"\nContracts & Pricing:")
        print(f"  Supplier Contracts: {len(self.supplier_contracts)}")
        print(f"  Contract Pricing: {len(self.contract_pricing)}")
        
        print(f"\nPerformance Management:")
        print(f"  Performance Metrics: {len(self.performance_metrics)}")
        print(f"  Scorecards: {len(self.scorecards)}")
        
        print(f"\nInvoicing & Matching:")
        print(f"  Supplier Invoices: {len(self.supplier_invoices)}")
        print(f"  Invoice Lines: {len(self.invoice_lines)}")
        print(f"  3-Way Match Logs: {len(self.three_way_matches)}")
        
        print(f"\nQualification:")
        print(f"  Qualification Records: {len(self.qualification_records)}")
        print(f"  Supplier Documents: {len(self.supplier_documents)}")
        print(f"  Supplier Audits: {len(self.supplier_audits)}")
        
        print(f"\nPortal Access:")
        print(f"  Portal Users: {len(self.portal_users)}")
    
    def to_json(self, output_file='supplier_portal_data.json'):
        """Export to JSON with flat structure matching actual table names"""
        print(f"\nExporting to JSON...")
        
        data = {
            # Master Data
            'suppliers': [],
            'supplier_contacts': [],
            
            # Purchase Requisitions
            'requisition_headers': self.purchase_requisitions[:20],
            'requisition_lines': self.req_lines[:50],
            
            # RFQ Management
            'rfq_headers': self.rfq_headers,
            'rfq_lines': self.rfq_lines[:50],
            'rfq_suppliers': self.rfq_suppliers[:30],
            'rfq_responses': self.rfq_responses[:20],
            'rfq_response_lines': self.rfq_response_lines[:50],
            
            # Supplier Contracts
            'supplier_contracts': self.supplier_contracts,
            'contract_pricing': self.contract_pricing[:30],
            'contract_terms': [],
            'contract_amendments': [],
            
            # Performance Management
            'supplier_performance_metrics': self.performance_metrics[:30],
            'supplier_scorecards': self.scorecards[:30],
            'scorecard_items': [],
            'performance_audit_log': [],
            
            # Invoicing & Payments
            'supplier_invoices': self.supplier_invoices,
            'invoice_line_items': self.invoice_lines[:50],
            'invoice_tax_lines': [],
            'three_way_matches': self.three_way_matches[:30],
            'payment_records': [],
            
            # Supplier Qualification
            'supplier_qualification': self.qualification_records,
            'qualification_audits': self.supplier_audits,
            'supplier_documents': self.supplier_documents[:20],
            'document_categories': [],
            
            # Portal & Access
            'portal_users': self.portal_users[:30],
            'user_roles': [],
            'user_permissions': [],
            'portal_activity_log': [],
            
            # Integration & Logging
            'supplier_portal_integration_log': []
        }
        
        with open(output_file, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"Data exported to {output_file}")


if __name__ == "__main__":
    from pathlib import Path
    
    # Get the directory of this script (data folder)
    script_dir = Path(__file__).parent
    
    generator = SupplierPortalDataGenerator()
    generator.generate_all_data()
    
    # Export to JSON (in same folder as script)
    json_file = script_dir / "supplier_portal_data.json"
    generator.to_json(str(json_file))
    
    print("\n" + "="*80)
    print("Supplier Portal Data Generation Complete!")
    print("="*80)
