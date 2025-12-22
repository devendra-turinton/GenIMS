#!/usr/bin/env python3
"""
GenIMS Customer Service Historical Data Generator
Generates 180 days of customer service data
"""

import random
import json
from datetime import datetime, timedelta
from typing import List, Dict

# Configuration
DAYS_OF_HISTORY = 180
SERVICE_AGENTS_COUNT = 20
FIELD_TECHNICIANS_COUNT = 10
KB_ARTICLES_COUNT = 50
TICKETS_PER_DAY = (5, 20)
FIELD_APPOINTMENTS_PER_WEEK = (10, 30)

class ServiceDataGenerator:
    def __init__(self, master_data_file=None, crm_data_file=None):
        """Initialize with master data and CRM data"""
        from pathlib import Path
        
        if master_data_file is None:
            master_data_file = Path(__file__).parent.parent / "01 - Base Data" / "genims_master_data.json"
        
        if crm_data_file is None:
            crm_data_file = Path(__file__).parent.parent / "07 - CRM" / "crm_historical_data.json"
        
        print("Loading existing data...")
        
        with open(master_data_file, 'r') as f:
            self.master_data = json.load(f)
        
        with open(crm_data_file, 'r') as f:
            self.crm_data = json.load(f)
        
        self.customers = self.master_data['customers']
        self.accounts = self.crm_data['accounts']
        self.contacts = self.crm_data['contacts']
        
        # Service Data
        self.service_agents = []
        self.service_teams = []
        self.field_technicians = []
        self.kb_categories = []
        self.kb_articles = []
        self.sla_definitions = []
        self.service_tickets = []
        self.ticket_comments = []
        self.warranties = []
        self.warranty_claims = []
        self.rma_requests = []
        self.field_appointments = []
        self.service_parts = []
        self.parts_usage = []
        self.surveys = []
        self.survey_responses = []
        self.customer_feedback = []
        self.escalation_rules = []
        self.resolution_codes = []
        
        # Counters
        self.counters = {
            'agent': 1, 'team': 1, 'tech': 1, 'kb_cat': 1, 'kb_art': 1,
            'sla': 1, 'ticket': 1, 'comment': 1, 'warranty': 1,
            'claim': 1, 'rma': 1, 'appt': 1, 'part': 1, 'usage': 1,
            'survey': 1, 'response': 1, 'feedback': 1, 'esc_rule': 1,
            'res_code': 1
        }
        
        print(f"Loaded: {len(self.accounts)} accounts, {len(self.contacts)} contacts")
    
    def generate_id(self, prefix: str, counter_key: str) -> str:
        id_val = f"{prefix}-{str(self.counters[counter_key]).zfill(6)}"
        self.counters[counter_key] += 1
        return id_val
    
    def generate_all_data(self):
        """Generate all service data"""
        print(f"\n{'='*80}")
        print(f"Generating Customer Service Data ({DAYS_OF_HISTORY} days)")
        print(f"{'='*80}\n")
        
        # Master Data
        self.generate_service_teams()
        self.generate_service_agents()
        self.generate_field_technicians()
        self.generate_sla_definitions()
        self.generate_escalation_rules()
        self.generate_resolution_codes()
        self.generate_kb_categories()
        self.generate_kb_articles()
        self.generate_service_parts()
        self.generate_surveys()
        self.generate_warranties()
        
        # Historical Operations (180 days)
        start_date = datetime.now() - timedelta(days=DAYS_OF_HISTORY)
        self.generate_service_operations(start_date, DAYS_OF_HISTORY)
        
        self._print_summary()
    
    # ========================================================================
    # MASTER DATA
    # ========================================================================
    
    def generate_service_teams(self):
        """Generate service teams"""
        print("Generating service teams...")
        
        team_configs = [
            {'code': 'TECH', 'name': 'Technical Support', 'type': 'technical'},
            {'code': 'BILL', 'name': 'Billing Support', 'type': 'billing'},
            {'code': 'GEN', 'name': 'General Support', 'type': 'general'},
            {'code': 'FIELD', 'name': 'Field Service', 'type': 'field_service'},
            {'code': 'VIP', 'name': 'VIP Support', 'type': 'vip'}
        ]
        
        for config in team_configs:
            team = {
                'team_id': self.generate_id('TEAM', 'team'),
                'team_code': config['code'],
                'team_name': config['name'],
                'team_type': config['type'],
                'team_size': random.randint(3, 8),
                'service_hours': '24x7' if config['code'] in ['TECH', 'VIP'] else 'business_hours',
                'is_active': True,
                'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            self.service_teams.append(team)
        
        print(f"Generated {len(self.service_teams)} service teams")
    
    def generate_service_agents(self):
        """Generate service agents"""
        print("Generating service agents...")
        
        for i in range(SERVICE_AGENTS_COUNT):
            team = random.choice(self.service_teams) if self.service_teams else None
            
            agent = {
                'agent_id': self.generate_id('AGENT', 'agent'),
                'agent_code': f"AGT{self.counters['agent']-1:04d}",
                'first_name': f"Agent{i+1}",
                'last_name': "Support",
                'email': f"agent{i+1}@service.com",
                'team_id': team['team_id'] if team else None,
                'skill_areas': json.dumps(['technical', 'customer_service']),
                'avg_csat_rating': round(random.uniform(3.5, 5.0), 2),
                'total_tickets_resolved': random.randint(100, 500),
                'agent_status': 'available',
                'max_concurrent_tickets': random.randint(3, 7),
                'hire_date': (datetime.now() - timedelta(days=random.randint(365, 1825))).strftime('%Y-%m-%d'),
                'is_active': True,
                'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            self.service_agents.append(agent)
        
        print(f"Generated {len(self.service_agents)} service agents")
    
    def generate_field_technicians(self):
        """Generate field service technicians"""
        print("Generating field technicians...")
        
        for i in range(FIELD_TECHNICIANS_COUNT):
            tech = {
                'technician_id': self.generate_id('FTECH', 'tech'),
                'technician_code': f"FTECH{self.counters['tech']-1:04d}",
                'first_name': f"Tech{i+1}",
                'last_name': "Field",
                'email': f"tech{i+1}@field.com",
                'skill_areas': json.dumps(['installation', 'repair', 'maintenance']),
                'service_territory': random.choice(['North', 'South', 'East', 'West', 'Central']),
                'avg_job_rating': round(random.uniform(4.0, 5.0), 2),
                'total_jobs_completed': random.randint(50, 300),
                'technician_status': 'available',
                'is_active': True,
                'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            self.field_technicians.append(tech)
        
        print(f"Generated {len(self.field_technicians)} field technicians")
    
    def generate_sla_definitions(self):
        """Generate SLA definitions"""
        print("Generating SLA definitions...")
        
        sla_configs = [
            {'tier': 'strategic', 'priority': 'critical', 'response': 15, 'resolution': 240},
            {'tier': 'strategic', 'priority': 'high', 'response': 30, 'resolution': 480},
            {'tier': 'key', 'priority': 'critical', 'response': 30, 'resolution': 480},
            {'tier': 'key', 'priority': 'high', 'response': 60, 'resolution': 960},
            {'tier': 'standard', 'priority': 'critical', 'response': 60, 'resolution': 960},
            {'tier': 'standard', 'priority': 'high', 'response': 120, 'resolution': 1920}
        ]
        
        for config in sla_configs:
            sla = {
                'sla_id': self.generate_id('SLA', 'sla'),
                'sla_code': f"SLA-{config['tier'][:3].upper()}-{config['priority'][:4].upper()}",
                'sla_name': f"{config['tier'].title()} - {config['priority'].title()} SLA",
                'customer_tier': config['tier'],
                'priority': config['priority'],
                'response_time_minutes': config['response'],
                'resolution_time_minutes': config['resolution'],
                'service_hours': '24x7' if config['tier'] == 'strategic' else 'business_hours',
                'is_active': True,
                'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            self.sla_definitions.append(sla)
        
        print(f"Generated {len(self.sla_definitions)} SLA definitions")
    
    def generate_escalation_rules(self):
        """Generate escalation rules"""
        print("Generating escalation rules...")
        
        rule = {
            'rule_id': self.generate_id('ESCRULE', 'esc_rule'),
            'rule_code': 'ESC-001',
            'rule_name': 'Standard Escalation',
            'priority': 'all',
            'sla_breach_threshold_pct': 80,
            'level_1_threshold_minutes': 60,
            'level_2_threshold_minutes': 240,
            'level_3_threshold_minutes': 960,
            'is_active': True,
            'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        self.escalation_rules.append(rule)
        
        print(f"Generated {len(self.escalation_rules)} escalation rules")
    
    def generate_resolution_codes(self):
        """Generate resolution codes"""
        print("Generating resolution codes...")
        
        codes = [
            {'code': 'TECH-001', 'desc': 'Configuration Fixed', 'cat': 'technical'},
            {'code': 'TECH-002', 'desc': 'Software Updated', 'cat': 'technical'},
            {'code': 'USER-001', 'desc': 'User Training Provided', 'cat': 'user_error'},
            {'code': 'BILL-001', 'desc': 'Billing Corrected', 'cat': 'billing'},
            {'code': 'REPL-001', 'desc': 'Part Replaced', 'cat': 'hardware'}
        ]
        
        for c in codes:
            code = {
                'code_id': self.generate_id('RCODE', 'res_code'),
                'code': c['code'],
                'description': c['desc'],
                'category': c['cat'],
                'typical_resolution_minutes': random.randint(30, 480),
                'is_active': True,
                'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            self.resolution_codes.append(code)
        
        print(f"Generated {len(self.resolution_codes)} resolution codes")
    
    def generate_kb_categories(self):
        """Generate knowledge base categories"""
        print("Generating KB categories...")
        
        categories = ['Getting Started', 'Troubleshooting', 'Installation', 'Configuration', 'FAQs']
        
        for cat in categories:
            category = {
                'category_id': self.generate_id('KBCAT', 'kb_cat'),
                'category_code': f"KB-{cat.replace(' ', '').upper()[:10]}",
                'category_name': cat,
                'display_order': self.counters['kb_cat'] - 1,
                'is_active': True,
                'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            self.kb_categories.append(category)
        
        print(f"Generated {len(self.kb_categories)} KB categories")
    
    def generate_kb_articles(self):
        """Generate knowledge base articles"""
        print("Generating KB articles...")
        
        for i in range(KB_ARTICLES_COUNT):
            category = random.choice(self.kb_categories) if self.kb_categories else None
            
            article = {
                'article_id': self.generate_id('KBART', 'kb_art'),
                'article_number': f"KB{self.counters['kb_art']-1:05d}",
                'title': f"How to {['Setup', 'Configure', 'Troubleshoot', 'Install', 'Use'][i % 5]} Product Feature {i+1}",
                'summary': f"Step-by-step guide for feature {i+1}",
                'content': f"Detailed instructions for feature {i+1}...",
                'category_id': category['category_id'] if category else None,
                'article_type': random.choice(['how_to', 'troubleshooting', 'faq']),
                'article_status': 'published',
                'published_date': (datetime.now() - timedelta(days=random.randint(30, 180))).strftime('%Y-%m-%d'),
                'view_count': random.randint(10, 1000),
                'helpful_count': random.randint(5, 100),
                'not_helpful_count': random.randint(0, 20),
                'avg_rating': round(random.uniform(3.5, 5.0), 2),
                'is_active': True,
                'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            self.kb_articles.append(article)
        
        print(f"Generated {len(self.kb_articles)} KB articles")
    
    def generate_service_parts(self):
        """Generate service parts"""
        print("Generating service parts...")
        
        for i in range(100):
            part = {
                'service_part_id': self.generate_id('SPART', 'part'),
                'part_number': f"SP{self.counters['part']-1:06d}",
                'part_name': f"Service Part {i+1}",
                'part_category': random.choice(['consumable', 'repairable', 'replacement']),
                'part_type': random.choice(['mechanical', 'electrical', 'electronic']),
                'unit_of_measure': 'EA',
                'current_stock': random.randint(10, 200),
                'min_stock_level': random.randint(5, 20),
                'reorder_point': random.randint(10, 30),
                'standard_cost': round(random.uniform(50, 5000), 2),
                'service_price': round(random.uniform(75, 7500), 2),
                'is_active': True,
                'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            self.service_parts.append(part)
        
        print(f"Generated {len(self.service_parts)} service parts")
    
    def generate_surveys(self):
        """Generate customer surveys"""
        print("Generating surveys...")
        
        surveys_config = [
            {'type': 'csat', 'name': 'Customer Satisfaction Survey', 'trigger': 'ticket_closed'},
            {'type': 'nps', 'name': 'Net Promoter Score', 'trigger': 'periodic'},
            {'type': 'ces', 'name': 'Customer Effort Score', 'trigger': 'appointment_completed'}
        ]
        
        for config in surveys_config:
            survey = {
                'survey_id': self.generate_id('SURVEY', 'survey'),
                'survey_code': f"SUR-{config['type'].upper()}",
                'survey_name': config['name'],
                'survey_type': config['type'],
                'trigger_event': config['trigger'],
                'survey_status': 'active',
                'is_active': True,
                'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            self.surveys.append(survey)
        
        print(f"Generated {len(self.surveys)} surveys")
    
    def generate_warranties(self):
        """Generate warranty registrations"""
        print("Generating warranty registrations...")
        
        for account in self.accounts[:30]:  # Warranties for first 30 accounts
            warranty = {
                'warranty_id': self.generate_id('WARR', 'warranty'),
                'warranty_number': f"W-{self.counters['warranty']-1:06d}",
                'account_id': account['account_id'],
                'product_name': f"Product {random.randint(1, 20)}",
                'serial_number': f"SN{random.randint(100000, 999999)}",
                'purchase_date': (datetime.now() - timedelta(days=random.randint(30, 730))).strftime('%Y-%m-%d'),
                'warranty_type': random.choice(['standard', 'extended']),
                'warranty_start_date': (datetime.now() - timedelta(days=random.randint(30, 730))).strftime('%Y-%m-%d'),
                'warranty_end_date': (datetime.now() + timedelta(days=random.randint(30, 365))).strftime('%Y-%m-%d'),
                'warranty_duration_months': random.choice([12, 24, 36]),
                'coverage_type': random.choice(['parts_only', 'parts_and_labor', 'comprehensive']),
                'warranty_status': 'active',
                'registered_date': (datetime.now() - timedelta(days=random.randint(1, 730))).strftime('%Y-%m-%d'),
                'is_active': True,
                'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            self.warranties.append(warranty)
        
        print(f"Generated {len(self.warranties)} warranty registrations")
    
    # ========================================================================
    # SERVICE OPERATIONS
    # ========================================================================
    
    def generate_service_operations(self, start_date: datetime, days: int):
        """Generate daily service operations"""
        print(f"Generating {days} days of service operations...")
        
        current_date = start_date
        
        for day in range(days):
            # Daily: Create service tickets
            for _ in range(random.randint(*TICKETS_PER_DAY)):
                self._create_service_ticket(current_date)
            
            # Weekly: Create field service appointments
            if day % 7 == 0:
                for _ in range(random.randint(*FIELD_APPOINTMENTS_PER_WEEK)):
                    self._create_field_appointment(current_date)
            
            current_date += timedelta(days=1)
        
        print(f"Generated: {len(self.service_tickets)} tickets, "
              f"{len(self.field_appointments)} appointments")
    
    def _create_service_ticket(self, date: datetime):
        """Create service ticket"""
        if not self.accounts:
            return
        
        account = random.choice(self.accounts)
        account_contacts = [c for c in self.contacts if c['account_id'] == account['account_id']]
        contact = random.choice(account_contacts) if account_contacts else None
        agent = random.choice(self.service_agents) if self.service_agents else None
        
        priority = random.choice(['critical', 'urgent', 'high', 'medium', 'low'])
        ticket_type = random.choice(['incident', 'service_request', 'question', 'complaint'])
        
        ticket = {
            'ticket_id': self.generate_id('TKT', 'ticket'),
            'ticket_number': f"TKT-{date.strftime('%Y%m%d')}-{self.counters['ticket']:05d}",
            'account_id': account['account_id'],
            'contact_id': contact['contact_id'] if contact else None,
            'channel': random.choice(['phone', 'email', 'chat', 'web_portal']),
            'ticket_type': ticket_type,
            'category': random.choice(['technical', 'billing', 'delivery', 'quality']),
            'subject': f"{ticket_type.title()} - {random.choice(['Installation', 'Configuration', 'Performance', 'Error'])} Issue",
            'description': f"Customer reported issue with {random.choice(['product', 'service', 'delivery'])}",
            'priority': priority,
            'ticket_status': random.choice(['new', 'assigned', 'in_progress', 'resolved', 'closed']),
            'assigned_to': agent['agent_id'] if agent else None,
            'created_at': date.strftime('%Y-%m-%d %H:%M:%S')
        }
        self.service_tickets.append(ticket)
        
        # Create comments
        self._create_ticket_comments(ticket, date)
        
        # Some tickets generate RMA or warranty claims
        if random.random() > 0.9 and ticket['ticket_type'] == 'complaint':
            self._create_rma_request(ticket, date)
        
        if random.random() > 0.85 and self.warranties:
            warranty = random.choice(self.warranties)
            self._create_warranty_claim(ticket, warranty, date)
    
    def _create_ticket_comments(self, ticket: dict, date: datetime):
        """Create comments for ticket"""
        for _ in range(random.randint(1, 4)):
            comment = {
                'comment_id': self.generate_id('TCOM', 'comment'),
                'ticket_id': ticket['ticket_id'],
                'comment_text': f"Update on ticket {ticket['ticket_number']}",
                'comment_type': random.choice(['note', 'solution', 'customer_response']),
                'is_public': True,
                'created_at': (date + timedelta(hours=random.randint(1, 48))).strftime('%Y-%m-%d %H:%M:%S')
            }
            self.ticket_comments.append(comment)
    
    def _create_rma_request(self, ticket: dict, date: datetime):
        """Create RMA request"""
        rma = {
            'rma_id': self.generate_id('RMA', 'rma'),
            'rma_number': f"RMA-{date.strftime('%Y%m%d')}-{self.counters['rma']:04d}",
            'account_id': ticket['account_id'],
            'contact_id': ticket.get('contact_id'),
            'ticket_id': ticket['ticket_id'],
            'rma_type': random.choice(['return', 'repair', 'exchange']),
            'return_reason': random.choice(['defective', 'wrong_item', 'damaged_in_transit']),
            'reason_description': 'Customer requested return',
            'rma_status': random.choice(['requested', 'approved', 'received', 'processing']),
            'approved': True,
            'approved_date': date.strftime('%Y-%m-%d'),
            'refund_amount': round(random.uniform(1000, 50000), 2),
            'created_at': date.strftime('%Y-%m-%d %H:%M:%S')
        }
        self.rma_requests.append(rma)
    
    def _create_warranty_claim(self, ticket: dict, warranty: dict, date: datetime):
        """Create warranty claim"""
        claim = {
            'claim_id': self.generate_id('WCLAIM', 'claim'),
            'claim_number': f"WC-{date.strftime('%Y%m%d')}-{self.counters['claim']:04d}",
            'warranty_id': warranty['warranty_id'],
            'ticket_id': ticket['ticket_id'],
            'claim_date': date.strftime('%Y-%m-%d'),
            'issue_description': 'Product malfunction under warranty',
            'failure_type': random.choice(['defect', 'malfunction']),
            'claim_status': random.choice(['submitted', 'approved', 'processed']),
            'approved': True,
            'approved_date': date.strftime('%Y-%m-%d'),
            'resolution_type': random.choice(['repair', 'replacement']),
            'total_claim_amount': round(random.uniform(500, 5000), 2),
            'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        self.warranty_claims.append(claim)
    
    def _create_field_appointment(self, date: datetime):
        """Create field service appointment"""
        if not self.accounts or not self.field_technicians:
            return
        
        account = random.choice(self.accounts)
        account_contacts = [c for c in self.contacts if c['account_id'] == account['account_id']]
        contact = random.choice(account_contacts) if account_contacts else None
        technician = random.choice(self.field_technicians)
        
        appt = {
            'appointment_id': self.generate_id('APPT', 'appt'),
            'appointment_number': f"FSA-{date.strftime('%Y%m%d')}-{self.counters['appt']:04d}",
            'account_id': account['account_id'],
            'contact_id': contact['contact_id'] if contact else None,
            'service_type': random.choice(['installation', 'repair', 'maintenance', 'inspection']),
            'appointment_date': (date + timedelta(days=random.randint(1, 14))).strftime('%Y-%m-%d'),
            'scheduled_start_time': f"{random.randint(8, 16):02d}:00:00",
            'estimated_duration_minutes': random.choice([60, 120, 180, 240]),
            'appointment_status': random.choice(['scheduled', 'confirmed', 'completed']),
            'assigned_technician_id': technician['technician_id'],
            'labor_charges': round(random.uniform(500, 5000), 2),
            'parts_charges': round(random.uniform(200, 3000), 2),
            'created_at': date.strftime('%Y-%m-%d %H:%M:%S')
        }
        self.field_appointments.append(appt)
    
    def _print_summary(self):
        print(f"\n{'='*80}")
        print(f"Customer Service Data Generation Complete!")
        print(f"{'='*80}")
        print(f"\nTeams & Agents:")
        print(f"  Service Teams: {len(self.service_teams)}")
        print(f"  Service Agents: {len(self.service_agents)}")
        print(f"  Field Technicians: {len(self.field_technicians)}")
        
        print(f"\nKnowledge Base:")
        print(f"  KB Categories: {len(self.kb_categories)}")
        print(f"  KB Articles: {len(self.kb_articles)}")
        
        print(f"\nSLAs & Rules:")
        print(f"  SLA Definitions: {len(self.sla_definitions)}")
        print(f"  Escalation Rules: {len(self.escalation_rules)}")
        print(f"  Resolution Codes: {len(self.resolution_codes)}")
        
        print(f"\nOperational Data:")
        print(f"  Service Tickets: {len(self.service_tickets)}")
        print(f"  Ticket Comments: {len(self.ticket_comments)}")
        print(f"  Field Appointments: {len(self.field_appointments)}")
        print(f"  Warranties: {len(self.warranties)}")
        print(f"  Warranty Claims: {len(self.warranty_claims)}")
        print(f"  RMA Requests: {len(self.rma_requests)}")
        print(f"  Service Parts: {len(self.service_parts)}")
    
    def to_json(self, output_file='service_historical_data.json'):
        """Export to JSON with flat structure matching actual table names from genims_service schema"""
        print(f"\nExporting to JSON...")
        
        data = {
            # Service Tickets (Primary)
            'service_tickets': self.service_tickets[:100],
            'ticket_comments': self.ticket_comments[:100],
            'ticket_attachments': [],
            
            # Knowledge Base
            'kb_categories': self.kb_categories,
            'kb_articles': self.kb_articles[:50],
            'kb_article_ratings': [],
            
            # SLA & Escalation
            'sla_definitions': self.sla_definitions,
            'escalation_rules': self.escalation_rules,
            'ticket_escalations': [],
            
            # Warranty & RMA
            'warranty_registrations': [],
            'warranty_claims': self.warranty_claims,
            'rma_requests': self.rma_requests,
            'rma_line_items': [],
            
            # Field Service
            'field_service_appointments': self.field_appointments[:50],
            'field_technicians': self.field_technicians,
            
            # Service Parts
            'service_parts': self.service_parts[:50],
            'service_parts_usage': [],
            
            # Surveys & Feedback
            'customer_surveys': self.surveys,
            'survey_responses': [],
            'customer_feedback': [],
            
            # Service Organization
            'service_teams': self.service_teams,
            
            # Integration & Logging
            'service_integration_log': []
        }
        
        with open(output_file, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"Data exported to {output_file}")


if __name__ == "__main__":
    from pathlib import Path
    
    # Get the directory of this script (data folder)
    script_dir = Path(__file__).parent
    
    generator = ServiceDataGenerator()
    generator.generate_all_data()
    
    # Export to JSON (in same folder as script)
    json_file = script_dir / "service_historical_data.json"
    generator.to_json(str(json_file))
    
    print("\n" + "="*80)
    print("Customer Service Historical Data Generation Complete!")
    print("="*80)
