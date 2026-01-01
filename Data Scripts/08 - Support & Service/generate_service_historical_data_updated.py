#!/usr/bin/env python3
"""
GenIMS Customer Service Historical Data Generator
Generates all 27 service-related tables with complete coverage
"""

import random
import json
from datetime import datetime, timedelta
from typing import List, Dict
import sys
from pathlib import Path

# Add scripts to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))
from generator_helper import get_helper

DAYS_OF_HISTORY = 180
SERVICE_AGENTS_COUNT = 20
FIELD_TECHNICIANS_COUNT = 15
KB_ARTICLES_COUNT = 80
TICKETS_PER_DAY = 10

class ServiceDataGenerator:
    def __init__(self, master_data_file=None, crm_data_file=None):
        """Initialize with master, CRM data, and registry"""
        from pathlib import Path
        
        if master_data_file is None:
            master_data_file = Path(__file__).parent.parent / "01 - Base Data" / "genims_master_data.json"
        if crm_data_file is None:
            crm_data_file = Path(__file__).parent.parent / "07 - CRM" / "genims_crm_data.json"
        
        with open(master_data_file, 'r') as f:
            self.master_data = json.load(f)
        
        try:
            with open(crm_data_file, 'r') as f:
                self.crm_data = json.load(f)
        except:
            self.crm_data = {'accounts': [], 'contacts': []}
        
        # Load helper for FK validation
        self.helper = get_helper()
        self.registry = self.helper.registry
        
        self.factories = self.master_data.get('factories', [])
        self.employees = self.master_data.get('employees', [])
        self.customers = self.master_data.get('customers', [])
        self.accounts = self.crm_data.get('accounts', [])
        self.contacts = self.crm_data.get('contacts', [])
        self.products = self.master_data.get('products', [])
        
        # All tables
        self.service_agents = []
        self.service_teams = []
        self.field_technicians = []
        self.kb_categories = []
        self.kb_articles = []
        self.kb_article_ratings = []
        self.sla_definitions = []
        self.service_queues = []
        self.service_tickets = []
        self.ticket_comments = []
        self.ticket_attachments = []
        self.ticket_escalations = []
        self.warranties = []
        self.warranty_claims = []
        self.warranty_registrations = []
        self.rma_requests = []
        self.rma_line_items = []
        self.field_appointments = []
        self.service_parts = []
        self.service_parts_usage = []
        self.surveys = []
        self.survey_responses = []
        self.customer_feedback = []
        self.escalation_rules = []
        self.resolution_codes = []
        self.service_integration_log = []
        self.service_metrics_daily = []
        self.portal_users = []
        
        self.counters = {
            'agent': 1, 'team': 1, 'tech': 1, 'kb_cat': 1, 'kb_art': 1,
            'kb_rating': 1, 'sla': 1, 'queue': 1, 'ticket': 1,
            'comment': 1, 'attach': 1, 'esc': 1, 'warranty': 1,
            'claim': 1, 'reg': 1, 'rma': 1, 'rma_line': 1,
            'appt': 1, 'part': 1, 'usage': 1, 'survey': 1,
            'response': 1, 'feedback': 1, 'esc_rule': 1,
            'res_code': 1, 'int_log': 1, 'metric': 1, 'portal': 1
        }
        
    def generate_id(self, prefix: str, counter_key: str) -> str:
        id_val = f"{prefix}-{str(self.counters[counter_key]).zfill(6)}"
        self.counters[counter_key] += 1
        return id_val
    
    def generate_all_data(self):
        """Generate all service data"""
        print(f"\n{'='*80}")
        print(f"Generating Customer Service Data (All 27 Tables)")
        print(f"{'='*80}\n")
        
        # Infrastructure
        self.generate_service_teams()
        self.generate_service_agents()
        self.generate_field_technicians()
        self.generate_service_queues()
        self.generate_sla_definitions()
        self.generate_escalation_rules()
        self.generate_resolution_codes()
        
        # Knowledge Management
        self.generate_kb_categories()
        self.generate_kb_articles()
        self.generate_kb_article_ratings()
        
        # Service Operations
        self.generate_service_parts()
        self.generate_portal_users()
        
        # Ticket Processing
        self.generate_service_tickets()
        self.generate_ticket_comments()
        self.generate_ticket_attachments()
        self.generate_ticket_escalations()
        
        # Warranty Management
        self.generate_warranty_registrations()
        self.generate_warranty_claims()
        
        # RMA Processing
        self.generate_rma_requests()
        self.generate_rma_line_items()
        
        # Field Service
        self.generate_field_appointments()
        self.generate_service_parts_usage()
        
        # Surveys & Feedback
        self.generate_surveys()
        self.generate_survey_responses()
        self.generate_customer_feedback()
        
        # Metrics & Logs
        self.generate_service_integration_log()
        self.generate_service_metrics_daily()
        
        self._print_summary()
    
    # ========================================================================
    # INFRASTRUCTURE
    # ========================================================================
    
    def generate_service_teams(self):
        """Generate service teams"""
        print("Generating service teams...")
        
        teams = ['Level 1 Support', 'Level 2 Support', 'Level 3 Technical', 'Field Service', 'RMA Processing']
        
        for team_name in teams:
            team = {
                'team_id': self.generate_id('STM', 'team'),
                'team_code': f"STM-{self.counters['team']-1:03d}",
                'team_name': team_name,
                'team_type': 'support' if 'Support' in team_name else 'field' if 'Field' in team_name else 'rma',
                'team_lead': random.choice(self.employees)['employee_id'] if self.employees else f"EMP-{random.randint(1000, 9999)}",
                'member_count': random.randint(5, 15),
                'availability_hours': '24/7' if 'Level' in team_name else '09:00-17:00',
                'is_active': True,
                'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            self.service_teams.append(team)
        
        print(f"Generated {len(self.service_teams)} service teams")
    
    def generate_service_agents(self):
        """Generate service agents"""
        print("Generating service agents...")
        
        for i in range(SERVICE_AGENTS_COUNT):
            agent = {
                'agent_id': self.generate_id('AGT', 'agent'),
                'agent_code': f"AGT{i+1:04d}",
                'employee_id': random.choice(self.employees)['employee_id'] if self.employees else f"EMP-{random.randint(1000, 9999)}",
                'agent_name': f"Agent {i+1}",
                'email': f"agent{i+1}@company.com",
                'phone': f"+91 {random.randint(7000000000, 9999999999)}",
                'team_id': random.choice(self.service_teams)['team_id'],
                'agent_level': random.choice(['L1', 'L2', 'L3']),
                'expertise_areas': 'Technical Support, Sales, Billing',
                'availability_status': 'available',
                'is_active': True,
                'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            self.service_agents.append(agent)
        
        print(f"Generated {len(self.service_agents)} service agents")
    
    def generate_field_technicians(self):
        """Generate field technicians"""
        print("Generating field technicians...")
        
        for i in range(FIELD_TECHNICIANS_COUNT):
            tech = {
                'technician_id': self.generate_id('TECH', 'tech'),
                'technician_code': f"TECH{i+1:04d}",
                'employee_id': random.choice(self.employees)['employee_id'] if self.employees else f"EMP-{random.randint(1000, 9999)}",
                'technician_name': f"Technician {i+1}",
                'email': f"tech{i+1}@company.com",
                'phone': f"+91 {random.randint(7000000000, 9999999999)}",
                'team_id': random.choice(self.service_teams)['team_id'],
                'certification_level': random.choice(['Level 1', 'Level 2', 'Level 3']),
                'assigned_zone': f"Zone {random.choice('ABCDE')}",
                'availability': 'on_field',
                'is_active': True,
                'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            self.field_technicians.append(tech)
        
        print(f"Generated {len(self.field_technicians)} field technicians")
    
    def generate_service_queues(self):
        """Generate service queues"""
        print("Generating service queues...")
        
        queue_names = ['Support Queue', 'Escalation Queue', 'Dispatch Queue', 'Callback Queue']
        
        for queue_name in queue_names:
            queue = {
                'queue_id': self.generate_id('QUE', 'queue'),
                'queue_code': f"QUE-{self.counters['queue']-1:03d}",
                'queue_name': queue_name,
                'queue_type': 'standard',
                'priority': random.choice(['high', 'normal', 'low']),
                'max_wait_time_minutes': random.choice([5, 10, 30]),
                'current_queue_length': random.randint(0, 20),
                'is_active': True,
                'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            self.service_queues.append(queue)
        
        print(f"Generated {len(self.service_queues)} service queues")
    
    def generate_sla_definitions(self):
        """Generate SLA definitions"""
        print("Generating SLA definitions...")
        
        sla_types = [
            {'name': 'Critical - 4 Hour Response', 'response': 4, 'resolution': 8},
            {'name': 'High - 8 Hour Response', 'response': 8, 'resolution': 24},
            {'name': 'Medium - 24 Hour Response', 'response': 24, 'resolution': 72},
            {'name': 'Low - 48 Hour Response', 'response': 48, 'resolution': 168}
        ]
        
        for sla_type in sla_types:
            sla = {
                'sla_id': self.generate_id('SLA', 'sla'),
                'sla_code': f"SLA-{self.counters['sla']-1:03d}",
                'sla_name': sla_type['name'],
                'sla_category': 'support',
                'priority_level': ['critical', 'high', 'medium', 'low'][self.counters['sla']-2],
                'response_time_hours': sla_type['response'],
                'resolution_time_hours': sla_type['resolution'],
                'breach_penalty_percent': random.uniform(5, 20),
                'is_active': True,
                'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            self.sla_definitions.append(sla)
        
        print(f"Generated {len(self.sla_definitions)} SLA definitions")
    
    def generate_escalation_rules(self):
        """Generate escalation rules"""
        print("Generating escalation rules...")
        
        rules = [
            {'name': 'High Priority Escalation', 'trigger': 'priority_high', 'escalate_after': 2},
            {'name': 'SLA Breach Escalation', 'trigger': 'sla_breach', 'escalate_after': 1},
            {'name': 'Wait Time Escalation', 'trigger': 'wait_time', 'escalate_after': 30},
            {'name': 'Customer Complaint Escalation', 'trigger': 'complaint', 'escalate_after': 1}
        ]
        
        for rule in rules:
            esc_rule = {
                'rule_id': self.generate_id('ESC', 'esc_rule'),
                'rule_code': f"ESC-{self.counters['esc_rule']-1:03d}",
                'rule_name': rule['name'],
                'trigger_condition': rule['trigger'],
                'escalate_after_minutes': rule['escalate_after'],
                'escalate_to_level': random.choice(['L2', 'L3', 'Manager']),
                'notification_method': 'email',
                'is_active': True,
                'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            self.escalation_rules.append(esc_rule)
        
        print(f"Generated {len(self.escalation_rules)} escalation rules")
    
    def generate_resolution_codes(self):
        """Generate resolution codes"""
        print("Generating resolution codes...")
        
        resolutions = [
            'Resolved - Technical Solution',
            'Resolved - Procedural Guidance',
            'Resolved - Replacement Issued',
            'Resolved - Escalated to Engineering',
            'Closed - Duplicate',
            'Closed - Invalid Request',
            'Closed - Timeout'
        ]
        
        for res in resolutions:
            res_code = {
                'resolution_code_id': self.generate_id('RES', 'res_code'),
                'resolution_code': f"RES{self.counters['res_code']-1:02d}",
                'resolution_description': res,
                'resolution_type': 'resolved' if 'Resolved' in res else 'closed',
                'requires_followup': 'Resolved' in res,
                'customer_satisfaction_required': random.choice([True, False]),
                'is_active': True,
                'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            self.resolution_codes.append(res_code)
        
        print(f"Generated {len(self.resolution_codes)} resolution codes")
    
    # ========================================================================
    # KNOWLEDGE MANAGEMENT
    # ========================================================================
    
    def generate_kb_categories(self):
        """Generate KB categories"""
        print("Generating KB categories...")
        
        categories = ['Troubleshooting', 'How-To Guides', 'FAQs', 'Installation', 'Maintenance', 'Account Management']
        
        for cat_name in categories:
            cat = {
                'category_id': self.generate_id('KBCAT', 'kb_cat'),
                'category_code': f"KBCAT-{self.counters['kb_cat']-1:02d}",
                'category_name': cat_name,
                'description': f"Knowledge base category for {cat_name}",
                'article_count': random.randint(5, 25),
                'category_status': 'active',
                'is_active': True,
                'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            self.kb_categories.append(cat)
        
        print(f"Generated {len(self.kb_categories)} KB categories")
    
    def generate_kb_articles(self):
        """Generate KB articles"""
        print("Generating KB articles...")
        
        titles = [
            'How to reset your password', 'Troubleshooting connectivity issues',
            'Installation guide step by step', 'Common error codes and solutions',
            'Frequently asked questions', 'Performance optimization tips',
            'Security best practices', 'Backup and recovery procedures'
        ]
        
        for i in range(KB_ARTICLES_COUNT):
            article = {
                'article_id': self.generate_id('KBART', 'kb_art'),
                'article_code': f"KBART-{i+1:05d}",
                'article_title': random.choice(titles),
                'category_id': random.choice(self.kb_categories)['category_id'],
                'article_content': f"Detailed content for article {i+1}",
                'author_id': random.choice(self.service_agents)['agent_id'] if self.service_agents else 'AGT-000001',
                'publication_date': (datetime.now() - timedelta(days=random.randint(30, 365))).strftime('%Y-%m-%d'),
                'last_updated_date': datetime.now().strftime('%Y-%m-%d'),
                'views_count': random.randint(10, 1000),
                'helpful_count': random.randint(5, 500),
                'article_status': 'published',
                'is_active': True,
                'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            self.kb_articles.append(article)
        
        print(f"Generated {len(self.kb_articles)} KB articles")
    
    def generate_kb_article_ratings(self):
        """Generate KB article ratings"""
        print("Generating KB article ratings...")
        
        for article in random.sample(self.kb_articles, len(self.kb_articles)//2):
            # 1-5 ratings per article
            for _ in range(random.randint(1, 5)):
                rating = {
                    'rating_id': self.generate_id('KBRAT', 'kb_rating'),
                    'article_id': article['article_id'],
                    'rating_value': random.randint(1, 5),
                    'rating_comment': random.choice(['Helpful', 'Very helpful', 'Not clear', 'Missing info']),
                    'user_id': random.choice(self.contacts)['contact_id'] if self.contacts else f"CONTACT-{random.randint(1000, 9999)}",
                    'rating_date': (datetime.now() - timedelta(days=random.randint(1, 180))).strftime('%Y-%m-%d'),
                    'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                self.kb_article_ratings.append(rating)
        
        print(f"Generated {len(self.kb_article_ratings)} KB article ratings")
    
    # ========================================================================
    # TICKET MANAGEMENT
    # ========================================================================
    
    def generate_service_tickets(self):
        """Generate service tickets - Complete with all schema columns"""
        print("Generating service tickets...")
        
        start_date = datetime.now() - timedelta(days=DAYS_OF_HISTORY)
        
        # FK from registry - GUARANTEED VALID
        valid_customer_ids = list(self.helper.get_valid_customer_ids())
        valid_employee_ids = list(self.helper.get_valid_employee_ids())
        
        ticket_counters = {t['queue_id']: 0 for t in self.service_queues} if self.service_queues else {'DEFAULT': 0}
        
        for day in range(DAYS_OF_HISTORY):
            for _ in range(random.randint(5, 15)):
                ticket_date = start_date + timedelta(days=day)
                selected_queue = random.choice(self.service_queues) if self.service_queues else {'queue_id': 'QUE-000001'}
                queue_id = selected_queue['queue_id']
                
                if queue_id not in ticket_counters:
                    ticket_counters[queue_id] = 0
                ticket_counters[queue_id] += 1
                
                priority = random.choice(['critical', 'urgent', 'high', 'medium', 'low'])
                status = random.choice(['new', 'assigned', 'in_progress', 'pending_customer', 'on_hold', 'resolved', 'closed'])
                
                # SLA based on priority
                sla_hours = {'critical': 4, 'urgent': 6, 'high': 8, 'medium': 24, 'low': 48}[priority]
                
                # Response and resolution timestamps
                response_due = ticket_date + timedelta(hours=1)
                resolution_due = ticket_date + timedelta(hours=sla_hours)
                
                first_response_datetime = None
                resolved_datetime = None
                closed_datetime = None
                response_sla_breached = False
                resolution_sla_breached = False
                
                # Simulate response time
                if random.random() > 0.15:  # 85% get first response
                    first_response_minutes = random.randint(5, sla_hours * 30)
                    first_response_datetime = (ticket_date + timedelta(minutes=first_response_minutes)).strftime('%Y-%m-%d %H:%M:%S')
                    response_sla_breached = first_response_minutes > 60
                
                # Simulate resolution - 75% of all tickets get resolution data
                # This ensures rich data for analytics even for open tickets
                if random.random() < 0.75 or status in ['resolved', 'closed']:
                    resolution_minutes = random.randint(30, sla_hours * 120)
                    resolved_datetime = (ticket_date + timedelta(minutes=resolution_minutes)).strftime('%Y-%m-%d %H:%M:%S')
                    resolution_sla_breached = resolution_minutes > (sla_hours * 60)
                    
                    # 85% of resolved tickets also get closed
                    if status == 'closed' or (resolved_datetime and random.random() < 0.85):
                        closed_datetime = (ticket_date + timedelta(minutes=resolution_minutes + random.randint(60, 480))).strftime('%Y-%m-%d %H:%M:%S')
                else:
                    resolved_datetime = None
                    closed_datetime = None
                    resolution_sla_breached = False
                
                # All tickets can be escalated - increase escalation rate significantly
                escalation_level = 0
                escalated_to = None
                escalated_datetime = None
                escalation_reason = None
                
                if random.random() < 0.60:  # 60% escalation rate (increased from 40%)
                    escalation_level = random.choice([1, 2, 3])
                    escalated_to = random.choice(valid_employee_ids)
                    escalated_datetime = (ticket_date + timedelta(hours=random.randint(1, 4))).strftime('%Y-%m-%d %H:%M:%S')
                    escalation_reason = random.choice(['Complexity', 'Customer Insistence', 'SLA Risk', 'Technical Expertise Required', 'Vendor Contact Required'])
                else:
                    # Even non-escalated tickets get escalation metadata with lower values
                    escalated_to = random.choice(valid_employee_ids) if random.random() < 0.3 else random.choice(valid_employee_ids)
                    escalated_datetime = (ticket_date + timedelta(hours=random.randint(2, 6))).strftime('%Y-%m-%d %H:%M:%S')
                    escalation_reason = random.choice(['Routine Reassignment', 'Load Balancing'])
                
                # Always generate handle time and KB articles
                handle_time = random.randint(15, 480)
                kb_article = f"KB-{random.randint(100000, 999999)}" if random.random() < 0.85 else None
                
                # Satisfaction rating for all resolved records - significantly increased
                csat_rating = None
                csat_comment = None
                csat_survey_sent = False
                csat_survey_sent_datetime = None
                
                if resolved_datetime:  # Always send survey for resolved tickets
                    csat_rating = random.choices([1, 2, 3, 4, 5], weights=[0.05, 0.10, 0.20, 0.30, 0.35])[0]  # Weighted toward higher ratings
                    csat_comment = random.choice(['Great support!', 'Problem solved quickly', 'Very helpful', 'Good service', 'Acceptable', 'Met expectations', 'Professional handling'])
                    csat_survey_sent = True
                    # resolved_datetime is already a string, add hours to ticket_date instead
                    csat_survey_sent_datetime = (datetime.strptime(resolved_datetime, '%Y-%m-%d %H:%M:%S') + timedelta(hours=2)).strftime('%Y-%m-%d %H:%M:%S')
                
                # Increase related serial number generation
                related_serial = f"SN-{random.randint(100000, 999999)}" if random.random() < 0.80 else None
                related_order = f"ORD-{random.randint(100000, 999999)}" if random.random() < 0.85 else None
                
                reopened_count = 0
                if status in ['resolved', 'closed'] and random.random() < 0.08:  # 8% reopen rate
                    reopened_count = random.randint(1, 3)
                
                ticket = {
                    'ticket_id': self.generate_id('TKT', 'ticket'),
                    'ticket_number': f"TKT-{ticket_date.strftime('%Y%m%d')}-{ticket_counters[queue_id]:04d}",
                    
                    # Customer Information
                    'account_id': random.choice(self.accounts)['account_id'] if self.accounts else f"ACC-{random.randint(1000, 9999)}",
                    'contact_id': random.choice(self.contacts)['contact_id'] if self.contacts else f"CONTACT-{random.randint(1000, 9999)}",
                    
                    # Ticket Source
                    'channel': random.choice(['phone', 'email', 'chat', 'web_portal', 'social_media', 'walk_in']),
                    'source_reference': f"REF-{random.randint(100000, 999999)}",
                    
                    # Classification
                    'ticket_type': random.choice(['incident', 'service_request', 'question', 'complaint', 'feedback']),
                    'category': random.choice(['technical', 'billing', 'delivery', 'quality', 'installation', 'training']),
                    'subcategory': random.choice(['software', 'hardware', 'documentation', 'account', 'performance']),
                    'product_category': random.choice(['Electronics', 'Machinery', 'Software', 'Consumables']),
                    
                    # Issue Details
                    'subject': random.choice(['Product defect', 'Technical issue', 'Billing inquiry', 'Installation help', 'Performance concern']),
                    'description': 'Detailed problem description with context and troubleshooting steps attempted',
                    
                    # Priority
                    'priority': priority,
                    'priority_reason': f"Priority set based on {['impact', 'urgency', 'customer_value', 'sla'][random.randint(0,3)]}",
                    
                    # Status
                    'ticket_status': status,
                    'status_reason': random.choice(['In Queue', 'Being Resolved', 'Awaiting Customer', 'On Hold', 'Resolved Successfully']) if status != 'new' else None,
                    
                    # Related Records
                    'related_order_id': related_order,
                    'related_product': random.choice(self.products)['product_name'] if self.products else 'Product A',
                    'related_serial_number': related_serial,
                    
                    # SLA Tracking
                    'sla_id': random.choice(self.sla_definitions)['sla_id'] if self.sla_definitions else 'SLA-000001',
                    'response_due_datetime': response_due.strftime('%Y-%m-%d %H:%M:%S'),
                    'resolution_due_datetime': resolution_due.strftime('%Y-%m-%d %H:%M:%S'),
                    
                    'first_response_datetime': first_response_datetime,
                    'resolved_datetime': resolved_datetime,
                    'closed_datetime': closed_datetime,
                    
                    'response_sla_breached': response_sla_breached,
                    'resolution_sla_breached': resolution_sla_breached,
                    
                    # Assignment
                    'assigned_to': random.choice(valid_employee_ids),
                    'assigned_team': random.choice(self.service_teams)['team_id'] if self.service_teams else 'STM-000001',
                    'assigned_datetime': (ticket_date + timedelta(minutes=random.randint(5, 120))).strftime('%Y-%m-%d %H:%M:%S'),
                    
                    # Routing
                    'routed_to_queue': queue_id,
                    
                    # Escalation
                    'escalation_level': escalation_level,
                    'escalated_to': escalated_to,
                    'escalated_datetime': escalated_datetime,
                    'escalation_reason': escalation_reason,
                    
                    # Resolution
                    'resolution_summary': 'Issue was resolved by...' if resolved_datetime else None,
                    'root_cause': random.choice(['Hardware Failure', 'Configuration Error', 'User Error', 'Software Bug']) if resolved_datetime else None,
                    'resolution_code': random.choice(self.resolution_codes)['resolution_code_id'] if self.resolution_codes else 'RES-000001',
                    
                    # Customer Satisfaction
                    'csat_rating': csat_rating,
                    'csat_comment': csat_comment,
                    'csat_survey_sent': csat_survey_sent,
                    'csat_survey_sent_datetime': csat_survey_sent_datetime,
                    
                    # Knowledge Base Link
                    'kb_article_used': kb_article,
                    
                    # Metrics
                    'first_response_time_minutes': int((datetime.fromisoformat(first_response_datetime.replace(' ', 'T')) - ticket_date).total_seconds() / 60) if first_response_datetime else None,
                    'resolution_time_minutes': int((datetime.fromisoformat(resolved_datetime.replace(' ', 'T')) - ticket_date).total_seconds() / 60) if resolved_datetime else None,
                    'handle_time_minutes': handle_time,
                    'reopened_count': reopened_count,
                    
                    # Tags
                    'tags': json.dumps(random.sample(['urgent', 'vip', 'external', 'internal', 'escalated'], random.randint(1, 3))),
                    
                    'created_by': random.choice(self.contacts)['contact_id'] if self.contacts else f"CONTACT-{random.randint(1000, 9999)}",
                    'created_at': ticket_date.strftime('%Y-%m-%d %H:%M:%S'),
                    'updated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                self.service_tickets.append(ticket)
        
        print(f"Generated {len(self.service_tickets)} service tickets")
    
    def generate_ticket_comments(self):
        """Generate ticket comments"""
        print("Generating ticket comments...")
        
        for ticket in self.service_tickets:  # Comments for all tickets
            # 1-3 comments per ticket
            for _ in range(random.randint(1, 3)):
                ticket_create_time = datetime.strptime(ticket['created_at'], '%Y-%m-%d %H:%M:%S')
                comment = {
                    'comment_id': self.generate_id('CMMNT', 'comment'),
                    'ticket_id': ticket['ticket_id'],
                    'comment_text': 'Technical troubleshooting step or customer response',
                    'comment_type': random.choice(['note', 'solution', 'customer_response', 'internal_note']),
                    'is_public': random.choice([True, False]),
                    'is_internal': random.choice([True, False]),
                    'attachments': json.dumps([]) if random.random() > 0.7 else json.dumps([]),
                    'created_by': random.choice(self.service_agents)['agent_id'] if self.service_agents else 'AGT-000001',
                    'created_by_type': random.choice(['agent', 'customer', 'system']),
                    'created_at': (ticket_create_time + timedelta(hours=random.randint(1, 48))).strftime('%Y-%m-%d %H:%M:%S')
                }
                self.ticket_comments.append(comment)
        
        print(f"Generated {len(self.ticket_comments)} ticket comments")
    
    def generate_ticket_attachments(self):
        """Generate ticket attachments"""
        print("Generating ticket attachments...")
        
        for ticket in self.service_tickets:  # Attachments for all tickets
            if random.random() > 0.6:
                attachment = {
                    'attachment_id': self.generate_id('ATTACH', 'attach'),
                    'ticket_id': ticket['ticket_id'],
                    'file_name': f"error_log_{random.randint(1, 999)}.txt",
                    'file_size_bytes': random.randint(1000, 5000000),
                    'file_type': random.choice(['text', 'image', 'pdf', 'log']),
                    'file_url': f"https://storage.example.com/tickets/{ticket['ticket_id']}/attachment_{random.randint(1000, 9999)}",
                    'uploaded_by': random.choice(self.service_agents)['agent_id'] if self.service_agents else 'AGT-000001',
                    'uploaded_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                self.ticket_attachments.append(attachment)
        
        print(f"Generated {len(self.ticket_attachments)} ticket attachments")
    
    def generate_ticket_escalations(self):
        """Generate ticket escalations"""
        print("Generating ticket escalations...")
        
        # Escalations for escalated tickets
        escalated_tickets = [t for t in self.service_tickets if t.get('escalated_to')]
        
        for ticket in escalated_tickets:
            # Create an escalation record for each escalated ticket
            escalation_date = ticket.get('escalated_datetime', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            
            escalation = {
                'escalation_id': self.generate_id('ESC', 'esc'),
                'ticket_id': ticket['ticket_id'],
                'escalation_rule_id': random.choice(self.escalation_rules)['rule_id'] if self.escalation_rules else 'ESC-000001',
                'escalated_from': random.choice(self.service_agents)['agent_id'] if self.service_agents else 'AGT-000001',
                'escalated_to': ticket.get('escalated_to'),
                'escalation_date': escalation_date,
                'escalation_reason': ticket.get('escalation_reason', 'SLA breach or customer request'),
                'escalation_level': random.choice(['L2', 'L3']),
                # Populate resolution_date for resolved escalations (85% of time)
                'resolution_date': (datetime.strptime(escalation_date, '%Y-%m-%d %H:%M:%S') + timedelta(days=random.randint(1, 3))).strftime('%Y-%m-%d') if random.random() < 0.85 else None,
                'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            self.ticket_escalations.append(escalation)
        
        print(f"Generated {len(self.ticket_escalations)} ticket escalations")
    
    # ========================================================================
    # WARRANTY MANAGEMENT
    # ========================================================================
    
    def generate_warranty_registrations(self):
        """Generate warranty registrations"""
        print("Generating warranty registrations...")
        
        for i in range(150):
            reg = {
                'registration_id': self.generate_id('WAREG', 'reg'),
                'registration_number': f"WAR-REG-{i+1:05d}",
                'customer_id': random.choice(self.customers)['customer_id'] if self.customers else f"CUST-{random.randint(1000, 9999)}",
                'product_id': random.choice(self.products)['product_id'] if self.products else f"PRD-{random.randint(1000, 9999)}",
                'serial_number': f"SN-{random.randint(100000, 999999)}",
                'purchase_date': (datetime.now() - timedelta(days=random.randint(30, 730))).strftime('%Y-%m-%d'),
                'warranty_start_date': (datetime.now() - timedelta(days=random.randint(30, 720))).strftime('%Y-%m-%d'),
                'warranty_end_date': (datetime.now() + timedelta(days=random.randint(30, 730))).strftime('%Y-%m-%d'),
                'warranty_type': random.choice(['standard', 'extended', 'premium']),
                'warranty_status': random.choice(['active', 'expired', 'claimed']),
                'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            self.warranty_registrations.append(reg)
        
        print(f"Generated {len(self.warranty_registrations)} warranty registrations")
    
    def generate_warranty_claims(self):
        """Generate warranty claims"""
        print("Generating warranty claims...")
        
        for reg in random.sample(self.warranty_registrations, len(self.warranty_registrations)//3):
            claim = {
                'claim_id': self.generate_id('WACLAIM', 'claim'),
                'claim_number': f"WCL-{self.counters['claim']-1:06d}",
                'registration_id': reg['registration_id'],
                'claim_date': (datetime.now() - timedelta(days=random.randint(1, 180))).strftime('%Y-%m-%d'),
                'claim_description': 'Product failure or defect',
                'claim_type': random.choice(['defect', 'breakdown', 'malfunction']),
                'claim_amount': round(random.uniform(5000, 50000), 2),
                'claim_status': random.choice(['approved', 'rejected', 'pending']),
                'approval_date': (datetime.now() - timedelta(days=random.randint(1, 30))).strftime('%Y-%m-%d'),
                'payment_date': (datetime.now() - timedelta(days=random.randint(1, 30))).strftime('%Y-%m-%d'),
                'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            self.warranty_claims.append(claim)
        
        print(f"Generated {len(self.warranty_claims)} warranty claims")
    
    # ========================================================================
    # RMA PROCESSING
    # ========================================================================
    
    def generate_rma_requests(self):
        """Generate RMA requests"""
        print("Generating RMA requests...")
        
        for i in range(80):
            rma = {
                'rma_id': self.generate_id('RMA', 'rma'),
                'rma_number': f"RMA-{i+1:06d}",
                'customer_id': random.choice(self.customers)['customer_id'] if self.customers else f"CUST-{random.randint(1000, 9999)}",
                'request_date': (datetime.now() - timedelta(days=random.randint(1, 90))).strftime('%Y-%m-%d'),
                'return_reason': random.choice(['Defective', 'Wrong item', 'Not working', 'Damaged']),
                'status': random.choice(['approved', 'pending', 'completed']),
                'approval_date': (datetime.now() - timedelta(days=random.randint(1, 30))).strftime('%Y-%m-%d'),
                'rma_status': random.choice(['open', 'in_transit', 'received', 'closed']),
                'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            self.rma_requests.append(rma)
        
        print(f"Generated {len(self.rma_requests)} RMA requests")
    
    def generate_rma_line_items(self):
        """Generate RMA line items"""
        print("Generating RMA line items...")
        
        for rma in self.rma_requests:
            # 1-3 items per RMA
            for _ in range(random.randint(1, 3)):
                item = {
                    'line_item_id': self.generate_id('RMALI', 'rma_line'),
                    'rma_id': rma['rma_id'],
                    'product_id': random.choice(self.products)['product_id'] if self.products else f"PRD-{random.randint(1000, 9999)}",
                    'quantity': random.randint(1, 5),
                    'unit_price': round(random.uniform(1000, 50000), 2),
                    'total_value': round(random.uniform(5000, 100000), 2),
                    'condition': random.choice(['damaged', 'defective', 'working']),
                    'inspection_notes': 'Product inspection results',
                    'replacement_status': random.choice(['pending', 'shipped', 'completed']),
                    'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                self.rma_line_items.append(item)
        
        print(f"Generated {len(self.rma_line_items)} RMA line items")
    
    # ========================================================================
    # FIELD SERVICE
    # ========================================================================
    
    def generate_field_appointments(self):
        """Generate field service appointments"""
        print("Generating field service appointments...")
        
        start_date = datetime.now() - timedelta(days=DAYS_OF_HISTORY)
        
        for day in range(DAYS_OF_HISTORY):
            for _ in range(random.randint(2, 8)):
                appt_date = start_date + timedelta(days=day)
                
                appointment = {
                    'appointment_id': self.generate_id('APPT', 'appt'),
                    'appointment_number': f"APPT-{self.counters['appt']-1:06d}",
                    'customer_id': random.choice(self.customers)['customer_id'] if self.customers else f"CUST-{random.randint(1000, 9999)}",
                    'ticket_id': random.choice(self.service_tickets)['ticket_id'] if self.service_tickets else f"TKT-{random.randint(1000, 9999)}",
                    'technician_id': random.choice(self.field_technicians)['technician_id'] if self.field_technicians else 'TECH-000001',
                    'appointment_date': appt_date.strftime('%Y-%m-%d'),
                    'appointment_time': f"{random.randint(8, 17):02d}:{random.randint(0, 59):02d}",
                    'duration_minutes': random.choice([30, 60, 90, 120]),
                    'appointment_status': random.choice(['scheduled', 'completed', 'no_show']),
                    'service_location': 'Customer location',
                    'notes': 'Service appointment notes',
                    'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                self.field_appointments.append(appointment)
        
        print(f"Generated {len(self.field_appointments)} field appointments")
    
    def generate_service_parts(self):
        """Generate service parts"""
        print("Generating service parts...")
        
        parts = [
            'Bearing Unit', 'Pump Assembly', 'Control Module', 'Motor',
            'Sensor', 'Valve', 'Hydraulic Hose', 'Electrical Connector',
            'Gearbox', 'Drive Belt'
        ]
        
        for part in parts:
            for i in range(random.randint(3, 8)):
                sp = {
                    'part_id': self.generate_id('PART', 'part'),
                    'part_number': f"SP-{self.counters['part']-1:06d}",
                    'part_name': f"{part} - Variant {i+1}",
                    'part_category': 'mechanical' if 'Bearing' in part or 'Pump' in part else 'electrical',
                    'unit_cost': round(random.uniform(500, 50000), 2),
                    'stock_quantity': random.randint(5, 100),
                    'reorder_level': random.randint(5, 20),
                    'supplier': random.choice(['Supplier A', 'Supplier B', 'Supplier C']),
                    'part_status': 'active',
                    'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                self.service_parts.append(sp)
        
        print(f"Generated {len(self.service_parts)} service parts")
    
    def generate_service_parts_usage(self):
        """Generate service parts usage"""
        print("Generating service parts usage...")
        
        for appointment in self.field_appointments:
            if random.random() > 0.5:
                # 1-2 parts used per appointment
                for _ in range(random.randint(1, 2)):
                    usage = {
                        'usage_id': self.generate_id('USAGE', 'usage'),
                        'appointment_id': appointment['appointment_id'],
                        'part_id': random.choice(self.service_parts)['part_id'],
                        'quantity_used': random.randint(1, 5),
                        'usage_date': appointment['appointment_date'],
                        'usage_status': 'issued',
                        'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    }
                    self.service_parts_usage.append(usage)
        
        print(f"Generated {len(self.service_parts_usage)} service parts usage records")
    
    # ========================================================================
    # SURVEYS & FEEDBACK
    # ========================================================================
    
    def generate_surveys(self):
        """Generate service surveys"""
        print("Generating service surveys...")
        
        survey_types = [
            'Post-Ticket Survey',
            'Field Service Feedback',
            'Product Satisfaction',
            'Support Quality Review'
        ]
        
        for survey_type in survey_types:
            survey = {
                'survey_id': self.generate_id('SURV', 'survey'),
                'survey_code': f"SURV-{self.counters['survey']-1:04d}",
                'survey_name': survey_type,
                'survey_type': survey_type,
                'question_count': random.randint(5, 15),
                'survey_status': 'active',
                'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            self.surveys.append(survey)
        
        print(f"Generated {len(self.surveys)} surveys")
    
    def generate_survey_responses(self):
        """Generate survey responses"""
        print("Generating survey responses...")
        
        for survey in self.surveys:
            for _ in range(random.randint(20, 50)):
                response = {
                    'response_id': self.generate_id('SRESP', 'response'),
                    'survey_id': survey['survey_id'],
                    'respondent_id': random.choice(self.contacts)['contact_id'] if self.contacts else f"CONTACT-{random.randint(1000, 9999)}",
                    'response_date': (datetime.now() - timedelta(days=random.randint(1, 180))).strftime('%Y-%m-%d'),
                    'satisfaction_score': random.randint(1, 5),
                    'quality_score': random.randint(1, 5),
                    'response_text': 'Feedback comments from customer',
                    'response_status': 'submitted',
                    'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                self.survey_responses.append(response)
        
        print(f"Generated {len(self.survey_responses)} survey responses")
    
    def generate_customer_feedback(self):
        """Generate customer feedback"""
        print("Generating customer feedback...")
        
        for i in range(100):
            feedback = {
                'feedback_id': self.generate_id('FBCK', 'feedback'),
                'feedback_number': f"FBCK-{i+1:06d}",
                'customer_id': random.choice(self.customers)['customer_id'] if self.customers else f"CUST-{random.randint(1000, 9999)}",
                'feedback_date': (datetime.now() - timedelta(days=random.randint(1, 180))).strftime('%Y-%m-%d'),
                'feedback_type': random.choice(['product', 'service', 'support']),
                'feedback_sentiment': random.choice(['positive', 'neutral', 'negative']),
                'feedback_text': 'Detailed customer feedback',
                'rating': random.randint(1, 5),
                'action_taken': random.choice(['Yes', 'No', 'Pending']),
                'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            self.customer_feedback.append(feedback)
        
        print(f"Generated {len(self.customer_feedback)} customer feedback records")
    
    # ========================================================================
    # PORTAL & LOGGING
    # ========================================================================
    
    def generate_portal_users(self):
        """Generate portal users"""
        print("Generating portal users...")
        
        for i in range(50):
            user = {
                'user_id': self.generate_id('PUSER', 'portal'),
                'username': f"user{i+1}",
                'email': f"user{i+1}@company.com",
                'contact_id': random.choice(self.contacts)['contact_id'] if self.contacts else f"CONTACT-{random.randint(1000, 9999)}",
                'account_id': random.choice(self.accounts)['account_id'] if self.accounts else f"ACC-{random.randint(1000, 9999)}",
                'user_role': random.choice(['customer', 'admin', 'technician']),
                'last_login_date': (datetime.now() - timedelta(days=random.randint(1, 30))).strftime('%Y-%m-%d'),
                'user_status': random.choice(['active', 'inactive']),
                'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            self.portal_users.append(user)
        
        print(f"Generated {len(self.portal_users)} portal users")
    
    def generate_service_integration_log(self):
        """Generate service integration logs"""
        print("Generating service integration logs...")
        
        start_date = datetime.now() - timedelta(days=180)
        
        for i in range(90):
            log = {
                'log_id': self.generate_id('SLOG', 'int_log'),
                'sync_date': (start_date + timedelta(days=random.randint(0, 180))).strftime('%Y-%m-%d'),
                'sync_time': f"{random.randint(0, 23):02d}:{random.randint(0, 59):02d}:00",
                'source_system': random.choice(['CRM', 'ERP', 'API', 'Manual']),
                'target_system': 'Service',
                'operation_type': random.choice(['sync', 'create', 'update']),
                'record_type': random.choice(['ticket', 'customer', 'appointment', 'feedback']),
                'record_count': random.randint(1, 100),
                'status': random.choice(['success', 'success', 'success', 'failed']),
                'error_message': None if random.random() > 0.05 else 'Sync error occurred',
                'created_at': (start_date + timedelta(days=random.randint(0, 180))).strftime('%Y-%m-%d %H:%M:%S')
            }
            self.service_integration_log.append(log)
        
        print(f"Generated {len(self.service_integration_log)} service integration logs")
    
    def generate_service_metrics_daily(self):
        """Generate daily service metrics"""
        print("Generating daily service metrics...")
        
        start_date = datetime.now() - timedelta(days=DAYS_OF_HISTORY)
        
        for day in range(DAYS_OF_HISTORY):
            metric_date = start_date + timedelta(days=day)
            
            metric = {
                'metric_id': self.generate_id('SMET', 'metric'),
                'metric_date': metric_date.strftime('%Y-%m-%d'),
                'tickets_created': random.randint(5, 20),
                'tickets_resolved': random.randint(3, 15),
                'avg_resolution_time_minutes': random.randint(30, 300),
                'avg_first_response_time_minutes': random.randint(5, 120),
                'customer_satisfaction_score': round(random.uniform(3.5, 5.0), 2),
                'sla_compliance_percent': round(random.uniform(85, 100), 2),
                'avg_handle_time_minutes': random.randint(10, 60),
                'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            self.service_metrics_daily.append(metric)
        
        print(f"Generated {len(self.service_metrics_daily)} daily service metrics")
    
    def _print_summary(self):
        print(f"\n{'='*80}")
        print(f"Customer Service Data Generation Complete!")
        print(f"{'='*80}\n")
        
        print(f"Infrastructure: {len(self.service_teams)} teams, {len(self.service_agents)} agents, {len(self.field_technicians)} technicians")
        print(f"Tickets: {len(self.service_tickets)} tickets, {len(self.ticket_comments)} comments, {len(self.ticket_escalations)} escalations")
        print(f"Warranty: {len(self.warranty_registrations)} registrations, {len(self.warranty_claims)} claims")
        print(f"RMA: {len(self.rma_requests)} requests, {len(self.rma_line_items)} line items")
        print(f"Field Service: {len(self.field_appointments)} appointments, {len(self.service_parts_usage)} parts used")
        print(f"Knowledge: {len(self.kb_articles)} articles, {len(self.kb_article_ratings)} ratings")
        print(f"Feedback: {len(self.survey_responses)} survey responses, {len(self.customer_feedback)} customer feedback")
        print(f"Metrics: {len(self.service_metrics_daily)} daily metrics records")
    
    def to_json(self, output_file='service_data.json'):
        """Export to JSON"""
        print(f"\nExporting to JSON...")
        
        data = {
            # Infrastructure
            'service_teams': self.service_teams,
            'service_agents': self.service_agents,
            'service_queues': self.service_queues,
            'field_technicians': self.field_technicians,
            'sla_definitions': self.sla_definitions,
            'escalation_rules': self.escalation_rules,
            'resolution_codes': self.resolution_codes,
            
            # Knowledge Management
            'kb_categories': self.kb_categories,
            'kb_articles': self.kb_articles,
            'kb_article_ratings': self.kb_article_ratings,
            
            # Ticket Management
            'service_tickets': self.service_tickets,
            'ticket_comments': self.ticket_comments,
            'ticket_attachments': self.ticket_attachments,
            'ticket_escalations': self.ticket_escalations,
            
            # Warranty
            'warranty_registrations': self.warranty_registrations,
            'warranty_claims': self.warranty_claims,
            
            # RMA
            'rma_requests': self.rma_requests,
            'rma_line_items': self.rma_line_items,
            
            # Field Service
            'field_service_appointments': self.field_appointments,
            'service_parts': self.service_parts,
            'service_parts_usage': self.service_parts_usage,
            
            # Surveys & Feedback
            'customer_surveys': self.surveys,
            'survey_responses': self.survey_responses,
            'customer_feedback': self.customer_feedback,
            
            # Portal & Logging
            'portal_users': self.portal_users,
            'service_integration_log': self.service_integration_log,
            'service_metrics_daily': self.service_metrics_daily
        }
        
        with open(output_file, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"Data exported to {output_file}")


if __name__ == "__main__":
    from pathlib import Path
    
    script_dir = Path(__file__).parent
    generator = ServiceDataGenerator()
    generator.generate_all_data()
    
    json_file = script_dir / "service_data.json"
    generator.to_json(str(json_file))
    
    print("\n" + "="*80)
    print("Customer Service Data Generation Complete!")
    print("="*80)
