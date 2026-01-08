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
                'first_name': f"Agent",
                'last_name': f"{i+1}",
                'email': f"agent{i+1}@company.com",
                'phone': f"+91 {random.randint(7000000000, 9999999999)}",
                'team_id': random.choice(self.service_teams)['team_id'],
                'skill_areas': '["technical", "billing", "sales"]',
                'product_expertise': '["manufacturing", "automation"]',
                'language_skills': '["English", "Hindi"]',
                'avg_csat_rating': round(random.uniform(3.5, 5.0), 2),
                'total_tickets_resolved': random.randint(10, 100),
                'avg_resolution_time_hours': round(random.uniform(0.5, 4.0), 2),
                'first_contact_resolution_rate': round(random.uniform(60, 95), 2),
                'agent_status': 'available',
                'current_ticket_count': random.randint(0, 5),
                'max_concurrent_tickets': 5,
                'hire_date': (datetime.now() - timedelta(days=random.randint(365, 1825))).strftime('%Y-%m-%d'),
                'is_active': True,
                'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            self.service_agents.append(agent)
        
        print(f"Generated {len(self.service_agents)} service agents")
    
    def generate_field_technicians(self):
        """Generate field technicians"""
        print("Generating field technicians...")
        
        first_names = ['John', 'Mike', 'Sarah', 'David', 'Emma', 'Robert', 'Lisa', 'James', 'Maria', 'Chris']
        last_names = ['Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia', 'Miller', 'Davis', 'Rodriguez', 'Martinez']
        skill_areas = ['Hydraulics', 'Pneumatics', 'Electrical', 'Mechanical', 'PLC Programming', 'HMI', 'Network', 'Safety Systems']
        
        for i in range(FIELD_TECHNICIANS_COUNT):
            first_name = random.choice(first_names)
            last_name = random.choice(last_names)
            # Generate certification expiry dates as list of dicts for JSON
            cert_expiry_dates = [
                {"cert": f"CERT-{random.randint(100, 999)}", "expiry": (datetime.now() + timedelta(days=random.randint(30, 365))).strftime('%Y-%m-%d')}
                for _ in range(random.randint(1, 3))
            ]
            tech = {
                'technician_id': self.generate_id('TECH', 'tech'),
                'technician_code': f"TECH{i+1:04d}",
                'employee_id': random.choice(self.employees)['employee_id'] if self.employees else f"EMP-{random.randint(1000, 9999)}",
                'first_name': first_name,
                'last_name': last_name,
                'email': f"tech{i+1}@company.com",
                'phone': f"+91 {random.randint(7000000000, 9999999999)}",
                'mobile': f"+91 {random.randint(7000000000, 9999999999)}",
                'skill_areas': json.dumps(random.sample(skill_areas, random.randint(2, 5))),
                'certifications': json.dumps([f"CERT-{random.randint(100, 999)}" for _ in range(random.randint(1, 3))]),
                'certification_expiry': json.dumps(cert_expiry_dates),
                'service_territory': f"Zone {random.choice('ABCDE')}",
                'home_base_location': f"Depot {random.choice('12345')}",
                'available_for_dispatch': random.choice([True, True, True, False]),
                'current_location_gps': f"({random.uniform(10, 30):.4f},{random.uniform(70, 90):.4f})",
                'last_location_update': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'avg_job_rating': round(random.uniform(3.5, 5.0), 2),
                'total_jobs_completed': random.randint(10, 500),
                'technician_status': random.choice(['active', 'on_leave', 'training']),
                'is_active': True,
                'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'updated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
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
                'code_id': self.generate_id('RES', 'res_code'),
                'code': f"RES{self.counters['res_code']-1:02d}",
                'description': res,
                'category': 'technical' if 'Technical' in res else 'user_error',
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
        
        article_types = ['Troubleshooting', 'How-To', 'Best Practices', 'FAQ', 'Reference']
        
        for i in range(KB_ARTICLES_COUNT):
            title = f"{random.choice(titles)} - {i+1}"
            article = {
                'article_id': self.generate_id('KBART', 'kb_art'),
                'article_number': f"KBART-{i+1:05d}",
                'title': title,
                'summary': f"Summary for {title}",
                'content': f"Detailed content for article {i+1}. This article provides comprehensive information about the topic.",
                'category_id': random.choice(self.kb_categories)['category_id'],
                'article_type': random.choice(article_types),
                'products': json.dumps(random.sample([p['product_id'] for p in self.products], min(2, len(self.products))) if self.products else []),
                'product_categories': json.dumps(['Hardware', 'Software', 'Services']),
                'keywords': json.dumps(['troubleshooting', 'howto', 'guide', f'topic{i+1}']),
                'tags': json.dumps(random.sample(['urgent', 'common', 'advanced', 'beginner'], random.randint(1, 3))),
                'article_status': 'published',
                'published_date': (datetime.now() - timedelta(days=random.randint(30, 365))).strftime('%Y-%m-%d'),
                'published_by': random.choice(self.service_agents)['agent_id'] if self.service_agents else 'AGT-000001',
                'version': '1.0',
                'previous_version_id': None,
                'view_count': random.randint(10, 1000),
                'helpful_count': random.randint(5, 500),
                'not_helpful_count': random.randint(0, 100),
                'avg_rating': round(random.uniform(3.5, 5.0), 2),
                'times_used_in_tickets': random.randint(0, 100),
                'last_used_date': (datetime.now() - timedelta(days=random.randint(1, 30))).strftime('%Y-%m-%d'),
                'attachments': json.dumps([]),
                'meta_description': f"Meta description for {title}",
                'author_id': random.choice(self.service_agents)['agent_id'] if self.service_agents else 'AGT-000001',
                'is_active': True,
                'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'updated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
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
        
        global_ticket_counter = 0  # Global counter for unique ticket numbers
        
        for day in range(DAYS_OF_HISTORY):
            for _ in range(random.randint(5, 15)):
                ticket_date = start_date + timedelta(days=day)
                selected_queue = random.choice(self.service_queues) if self.service_queues else {'queue_id': 'QUE-000001'}
                queue_id = selected_queue['queue_id']
                
                global_ticket_counter += 1
                
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
                
                # FIXED ESCALATION LOGIC - Use escalation rules properly
                escalation_level = 0
                escalated_to = None
                escalated_datetime = None
                escalation_reason = None
                
                # Determine escalation based on priority and SLA breaches
                should_escalate = False
                escalation_trigger = None
                
                # Priority-based escalation
                if priority == 'critical':
                    should_escalate = random.random() < 0.85  # 85% for critical
                    escalation_trigger = 'critical_priority'
                elif priority == 'urgent':
                    should_escalate = random.random() < 0.70  # 70% for urgent  
                    escalation_trigger = 'urgent_priority'
                elif priority == 'high':
                    should_escalate = random.random() < 0.50  # 50% for high
                    escalation_trigger = 'high_priority'
                elif response_sla_breached or resolution_sla_breached:
                    should_escalate = random.random() < 0.90  # 90% for SLA breach
                    escalation_trigger = 'sla_breach'
                else:
                    should_escalate = random.random() < 0.25  # 25% for normal cases
                    escalation_trigger = 'wait_time'
                
                if should_escalate:
                    # Set escalation level based on trigger
                    if escalation_trigger in ['critical_priority', 'sla_breach']:
                        escalation_level = random.choice([2, 3])  # Skip level 1 for critical
                    elif escalation_trigger == 'urgent_priority':
                        escalation_level = random.choice([1, 2])
                    else:
                        escalation_level = 1
                    
                    escalated_to = random.choice(valid_employee_ids)
                    escalation_hours = random.randint(1, 3) if escalation_trigger == 'critical_priority' else random.randint(2, 6)
                    escalated_datetime = (ticket_date + timedelta(hours=escalation_hours)).strftime('%Y-%m-%d %H:%M:%S')
                    
                    # Proper escalation reasons based on trigger
                    if escalation_trigger == 'critical_priority':
                        escalation_reason = random.choice(['Critical Business Impact', 'System Down', 'Data Loss Risk'])
                    elif escalation_trigger == 'sla_breach':
                        escalation_reason = random.choice(['SLA Response Breach', 'SLA Resolution Breach', 'Customer Escalation'])
                    elif escalation_trigger == 'urgent_priority':
                        escalation_reason = random.choice(['High Priority Issue', 'Customer VIP', 'Technical Complexity'])
                    else:
                        escalation_reason = random.choice(['Long Wait Time', 'Customer Request', 'Complexity Analysis'])
                else:
                    # Non-escalated tickets should have minimal escalation metadata
                    escalation_level = 0
                    escalated_to = None
                    escalated_datetime = None
                    escalation_reason = None
                
                # IMPROVED KB ARTICLE LINKAGE - Based on category and resolution
                kb_article = None
                if resolved_datetime:  # Only resolved tickets can reference KB articles
                    # Higher chance for technical tickets to use KB
                    if category == 'technical':
                        kb_article = f"KB-{random.randint(100000, 999999)}" if random.random() < 0.95 else None
                    elif category in ['installation', 'training']:
                        kb_article = f"KB-{random.randint(100000, 999999)}" if random.random() < 0.85 else None
                    else:
                        kb_article = f"KB-{random.randint(100000, 999999)}" if random.random() < 0.60 else None
                else:
                    # Open tickets might reference KB during troubleshooting
                    kb_article = f"KB-{random.randint(100000, 999999)}" if random.random() < 0.30 else None
                
                # Handle time based on complexity and resolution
                if resolved_datetime:
                    base_time = 15 if priority == 'low' else 30 if priority == 'medium' else 60 if priority == 'high' else 90
                    handle_time = random.randint(base_time, base_time * 8)
                else:
                    handle_time = random.randint(5, 60)  # Shorter for unresolved
                
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
                    'ticket_number': f"TKT-{global_ticket_counter:08d}",
                    
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
                    'resolution_code': random.choice(self.resolution_codes)['code_id'] if self.resolution_codes else 'RES-000001',
                    
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
            escalation_datetime = ticket.get('escalated_datetime', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            escalation_dt = datetime.strptime(escalation_datetime, '%Y-%m-%d %H:%M:%S')
            
            # 85% of escalations are de-escalated/resolved
            is_resolved = random.random() < 0.85
            de_escalated_dt = escalation_dt + timedelta(days=random.randint(1, 3)) if is_resolved else None
            
            escalation = {
                'escalation_id': self.generate_id('ESC', 'esc'),
                'ticket_id': ticket['ticket_id'],
                'escalation_level': ticket.get('escalation_level', '1'),
                'escalation_reason': ticket.get('escalation_reason', 'SLA breach or customer request'),
                'escalated_from': random.choice(self.service_agents)['agent_id'] if self.service_agents else 'AGT-000001',
                'escalated_to': ticket.get('escalated_to'),
                'escalated_at': escalation_datetime,
                'de_escalated': is_resolved,
                'de_escalated_at': de_escalated_dt.strftime('%Y-%m-%d %H:%M:%S') if de_escalated_dt else None,
                'de_escalation_reason': random.choice(['Resolved successfully', 'Customer satisfied', 'Timeout']) if is_resolved else None
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
            product = random.choice(self.products) if self.products else None
            product_name = product['product_name'] if product else f"Product {i+1}"
            purchase_date = datetime.now() - timedelta(days=random.randint(30, 730))
            warranty_duration = random.choice([12, 24, 36])
            
            reg = {
                'warranty_id': self.generate_id('WAREG', 'reg'),
                'warranty_number': f"WAR-{i+1:06d}",
                'account_id': random.choice(self.customers)['customer_id'] if self.customers else f"CUST-{random.randint(1000, 9999)}",
                'contact_id': random.choice(self.contacts)['contact_id'] if self.contacts else f"CONTACT-{random.randint(1000, 9999)}",
                'product_name': product_name,
                'product_category': product.get('product_category', 'General') if product else 'General',
                'serial_number': f"SN-{random.randint(100000, 999999)}",
                'model_number': f"MOD-{random.randint(1000, 9999)}",
                'sales_order_id': f"SO-{random.randint(10000, 99999)}",
                'purchase_date': purchase_date.strftime('%Y-%m-%d'),
                'invoice_number': f"INV-{random.randint(100000, 999999)}",
                'warranty_type': random.choice(['standard', 'extended', 'premium']),
                'warranty_start_date': purchase_date.strftime('%Y-%m-%d'),
                'warranty_end_date': (purchase_date + timedelta(days=warranty_duration*30)).strftime('%Y-%m-%d'),
                'warranty_duration_months': warranty_duration,
                'coverage_type': random.choice(['Full Coverage', 'Parts Only', 'Labor Only']),
                'coverage_details': json.dumps({'includes': ['defect', 'manufacturing'], 'excludes': ['accidental', 'misuse']}),
                'terms_conditions': 'Standard warranty terms and conditions apply',
                'warranty_status': random.choice(['active', 'expired', 'claimed']),
                'registered_date': datetime.now().strftime('%Y-%m-%d'),
                'registered_by': random.choice(self.service_agents)['agent_id'] if self.service_agents else 'AGT-000001',
                'transferred_to_account_id': None,
                'transfer_date': None,
                'is_active': True,
                'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'updated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            self.warranty_registrations.append(reg)
        
        print(f"Generated {len(self.warranty_registrations)} warranty registrations")
    
    def generate_warranty_claims(self):
        """Generate warranty claims"""
        print("Generating warranty claims...")
        
        failure_types = ['Hardware Failure', 'Defective Part', 'Manufacturing Defect', 'Malfunction']
        failure_categories = ['Mechanical', 'Electrical', 'Software', 'Component']
        
        for reg in random.sample(self.warranty_registrations, min(len(self.warranty_registrations)//3, 50)):
            claim_status = random.choice(['approved', 'rejected', 'pending'])
            claim_date = datetime.now() - timedelta(days=random.randint(1, 180))
            
            claim = {
                'claim_id': self.generate_id('WACLAIM', 'claim'),
                'claim_number': f"WCL-{self.counters['claim']-1:06d}",
                'warranty_id': reg['warranty_id'],
                'ticket_id': random.choice([t['ticket_id'] for t in self.service_tickets]) if self.service_tickets else None,
                'claim_date': claim_date.strftime('%Y-%m-%d'),
                'issue_description': 'Product failure or defect reported by customer',
                'failure_type': random.choice(failure_types),
                'failure_category': random.choice(failure_categories),
                'claim_status': claim_status,
                'approved': claim_status == 'approved',
                'approved_by': random.choice(self.service_agents)['agent_id'] if self.service_agents else 'AGT-000001' if claim_status != 'pending' else None,
                'approved_date': (claim_date + timedelta(days=random.randint(1, 10))).strftime('%Y-%m-%d') if claim_status != 'pending' else None,
                'rejection_reason': random.choice(['Not covered', 'Out of warranty', 'User damage']) if claim_status == 'rejected' else None,
                'resolution_type': random.choice(['Repair', 'Replace', 'Refund']) if claim_status == 'approved' else None,
                'labor_cost': round(random.uniform(1000, 5000), 2) if claim_status == 'approved' else 0,
                'parts_cost': round(random.uniform(5000, 20000), 2) if claim_status == 'approved' else 0,
                'total_claim_amount': round(random.uniform(5000, 50000), 2),
                'customer_responsibility': round(random.uniform(0, 5000), 2),
                'warranty_coverage': round(random.uniform(0, 50000), 2),
                'processed_date': (claim_date + timedelta(days=random.randint(5, 30))).strftime('%Y-%m-%d'),
                'processed_by': random.choice(self.service_agents)['agent_id'] if self.service_agents else 'AGT-000001',
                'notes': f'Warranty claim for {reg.get("product_name", "Product")}',
                'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'updated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
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
    
    json_file = script_dir / "genims_service_data.json"
    generator.to_json(str(json_file))
    
    print("\n" + "="*80)
    print("Customer Service Data Generation Complete!")
    print("="*80)
