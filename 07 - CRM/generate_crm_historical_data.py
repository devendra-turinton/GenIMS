#!/usr/bin/env python3
"""
GenIMS CRM Historical Data Generator
Generates 180 days of CRM data (leads, opportunities, quotes, cases)
"""

import random
import json
from datetime import datetime, timedelta
from typing import List, Dict

# Configuration
DAYS_OF_HISTORY = 180
SALES_REPS_COUNT = 15
TERRITORIES_COUNT = 5
LEADS_PER_DAY = (2, 8)
OPPORTUNITIES_PER_MONTH = (10, 25)
CASES_PER_WEEK = (5, 15)

class CRMDataGenerator:
    def __init__(self, master_data_file=None, erp_data_file=None):
        """Initialize with master data and ERP data"""
        from pathlib import Path
        
        if master_data_file is None:
            master_data_file = Path(__file__).parent.parent / "01 - Base Data" / "genims_master_data.json"
        
        if erp_data_file is None:
            erp_data_file = Path(__file__).parent.parent / "04 - ERP & MES Integration" / "erp_historical_data.json"
        
        print("Loading existing data...")
        
        with open(master_data_file, 'r') as f:
            self.master_data = json.load(f)
        
        # Try to load ERP data, use minimal data if not available
        try:
            with open(erp_data_file, 'r') as f:
                self.erp_data = json.load(f)
        except FileNotFoundError:
            print(f"Note: {erp_data_file} not found, using minimal product/material data")
            self.erp_data = {'materials': [], 'products': []}
        
        self.customers = self.master_data.get('customers', [])
        self.materials = self.erp_data.get('materials', [])
        self.factories = self.master_data.get('factories', [])
        
        # CRM Data
        self.sales_reps = []
        self.territories = []
        self.leads = []
        self.lead_activities = []
        self.accounts = []
        self.contacts = []
        self.opportunities = []
        self.opp_history = []
        self.opp_products = []
        self.quotations = []
        self.quote_lines = []
        self.campaigns = []
        self.cases = []
        self.contracts = []
        self.activities = []
        self.tasks = []
        self.interactions = []
        self.forecasts = []
        
        # Counters
        self.counters = {
            'rep': 1, 'territory': 1, 'lead': 1, 'lead_act': 1,
            'account': 1, 'contact': 1, 'opp': 1, 'opp_hist': 1,
            'opp_prod': 1, 'quote': 1, 'quote_line': 1,
            'campaign': 1, 'case': 1, 'contract': 1,
            'activity': 1, 'task': 1, 'interaction': 1, 'forecast': 1
        }
        
        print(f"Loaded: {len(self.customers)} customers, {len(self.materials)} materials")
    
    def generate_id(self, prefix: str, counter_key: str) -> str:
        id_val = f"{prefix}-{str(self.counters[counter_key]).zfill(6)}"
        self.counters[counter_key] += 1
        return id_val
    
    def generate_all_data(self):
        """Generate all CRM data"""
        print(f"\n{'='*80}")
        print(f"Generating CRM Data ({DAYS_OF_HISTORY} days of history)")
        print(f"{'='*80}\n")
        
        # Master Data
        self.generate_territories()
        self.generate_sales_reps()
        self.generate_campaigns()
        
        # Accounts from existing customers
        self.generate_accounts_from_customers()
        
        # Historical Operations (180 days)
        start_date = datetime.now() - timedelta(days=DAYS_OF_HISTORY)
        self.generate_crm_operations(start_date, DAYS_OF_HISTORY)
        
        # Generate forecasts
        self.generate_sales_forecasts()
        
        self._print_summary()
    
    # ========================================================================
    # MASTER DATA
    # ========================================================================
    
    def generate_territories(self):
        """Generate sales territories"""
        print("Generating sales territories...")
        
        territory_configs = [
            {'code': 'NORTH', 'name': 'North India', 'states': ['Delhi', 'Punjab', 'Haryana', 'UP']},
            {'code': 'WEST', 'name': 'West India', 'states': ['Maharashtra', 'Gujarat', 'Goa']},
            {'code': 'SOUTH', 'name': 'South India', 'states': ['Karnataka', 'Tamil Nadu', 'Kerala', 'AP']},
            {'code': 'EAST', 'name': 'East India', 'states': ['West Bengal', 'Bihar', 'Odisha']},
            {'code': 'CENTRAL', 'name': 'Central India', 'states': ['MP', 'Chhattisgarh', 'Rajasthan']}
        ]
        
        for config in territory_configs:
            territory = {
                'territory_id': self.generate_id('TERR', 'territory'),
                'territory_code': config['code'],
                'territory_name': config['name'],
                'states': json.dumps(config['states']),
                'territory_quota': round(random.uniform(50000000, 150000000), 2),
                'is_active': True,
                'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            self.territories.append(territory)
        
        print(f"Generated {len(self.territories)} territories")
    
    def generate_sales_reps(self):
        """Generate sales representatives"""
        print("Generating sales reps...")
        
        roles = ['SDR', 'AE', 'AM', 'SE']
        
        for i in range(SALES_REPS_COUNT):
            territory = random.choice(self.territories) if self.territories else None
            
            rep = {
                'sales_rep_id': self.generate_id('REP', 'rep'),
                'rep_code': f"REP{self.counters['rep']-1:04d}",
                'first_name': f"Sales{i+1}",
                'last_name': f"Rep",
                'email': f"salesrep{i+1}@company.com",
                'sales_role': random.choice(roles),
                'territory_id': territory['territory_id'] if territory else None,
                'annual_quota': round(random.uniform(10000000, 30000000), 2),
                'ytd_revenue': round(random.uniform(5000000, 20000000), 2),
                'win_rate_pct': round(random.uniform(15, 45), 2),
                'rep_status': 'active',
                'hire_date': (datetime.now() - timedelta(days=random.randint(365, 1825))).strftime('%Y-%m-%d'),
                'is_active': True,
                'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            self.sales_reps.append(rep)
        
        print(f"Generated {len(self.sales_reps)} sales reps")
    
    def generate_campaigns(self):
        """Generate marketing campaigns"""
        print("Generating campaigns...")
        
        campaign_names = [
            'Manufacturing Excellence 2024',
            'Digital Transformation Summit',
            'Industry 4.0 Webinar Series',
            'Trade Show - IMTEX',
            'LinkedIn Campaign - Smart Factory',
            'Email - Year End Offer'
        ]
        
        for name in campaign_names:
            start = datetime.now() - timedelta(days=random.randint(30, 150))
            
            campaign = {
                'campaign_id': self.generate_id('CAMP', 'campaign'),
                'campaign_code': f"CAMP-{self.counters['campaign']-1:03d}",
                'campaign_name': name,
                'campaign_type': random.choice(['email', 'webinar', 'trade_show', 'social']),
                'campaign_status': random.choice(['completed', 'in_progress']),
                'start_date': start.strftime('%Y-%m-%d'),
                'end_date': (start + timedelta(days=random.randint(30, 90))).strftime('%Y-%m-%d'),
                'budgeted_cost': round(random.uniform(100000, 1000000), 2),
                'actual_cost': round(random.uniform(80000, 900000), 2),
                'total_leads': random.randint(50, 500),
                'qualified_leads': random.randint(10, 100),
                'campaign_owner': random.choice(self.sales_reps)['sales_rep_id'] if self.sales_reps else None,
                'is_active': True,
                'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            self.campaigns.append(campaign)
        
        print(f"Generated {len(self.campaigns)} campaigns")
    
    def generate_accounts_from_customers(self):
        """Generate accounts from existing customers"""
        print("Generating accounts from customers...")
        
        for customer in self.customers:
            account = {
                'account_id': self.generate_id('ACC', 'account'),
                'account_number': f"ACC-{self.counters['account']-1:06d}",
                'customer_id': customer['customer_id'],
                'account_name': customer['customer_name'],
                'account_type': 'customer',
                'industry': random.choice(['Automotive', 'Electronics', 'Aerospace', 'Heavy Machinery']),
                'account_tier': random.choice(['strategic', 'key', 'standard']),
                'company_size': random.choice(['small', 'medium', 'large', 'enterprise']),
                'billing_city': customer.get('city'),
                'billing_state': customer.get('state'),
                'billing_country': customer.get('country', 'India'),
                'account_owner': random.choice(self.sales_reps)['sales_rep_id'] if self.sales_reps else None,
                'relationship_status': 'active',
                'customer_since': (datetime.now() - timedelta(days=random.randint(365, 2555))).strftime('%Y-%m-%d'),
                'lifetime_value': round(random.uniform(1000000, 50000000), 2),
                'health_score': random.randint(60, 95),
                'is_active': True,
                'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            self.accounts.append(account)
            
            # Generate contacts for each account
            self._generate_contacts_for_account(account)
        
        print(f"Generated {len(self.accounts)} accounts from customers")
    
    def _generate_contacts_for_account(self, account: dict):
        """Generate contacts for an account"""
        num_contacts = random.randint(2, 5)
        
        roles = ['decision_maker', 'influencer', 'champion', 'user']
        titles = ['CEO', 'CTO', 'VP Operations', 'Plant Manager', 'Purchase Manager', 'Engineer']
        
        for i in range(num_contacts):
            contact = {
                'contact_id': self.generate_id('CONT', 'contact'),
                'contact_number': f"CONT-{self.counters['contact']-1:06d}",
                'account_id': account['account_id'],
                'first_name': f"Contact{i+1}",
                'last_name': account['account_name'].split()[0],
                'job_title': random.choice(titles),
                'contact_role': random.choice(roles),
                'email': f"contact{i+1}@{account['account_name'].lower().replace(' ', '')}.com",
                'phone': f"+91 {random.randint(7000000000, 9999999999)}",
                'is_primary': (i == 0),
                'contact_status': 'active',
                'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            self.contacts.append(contact)
    
    # ========================================================================
    # CRM OPERATIONS
    # ========================================================================
    
    def generate_crm_operations(self, start_date: datetime, days: int):
        """Generate daily CRM operations"""
        print(f"Generating {days} days of CRM operations...")
        
        current_date = start_date
        
        for day in range(days):
            # Daily: Generate leads
            for _ in range(random.randint(*LEADS_PER_DAY)):
                self._create_lead(current_date)
            
            # Weekly: Generate opportunities
            if day % 7 == 0:
                for _ in range(random.randint(3, 8)):
                    self._create_opportunity(current_date)
            
            # Weekly: Generate cases
            if day % 7 == 0:
                for _ in range(random.randint(*CASES_PER_WEEK)):
                    self._create_case(current_date)
            
            # Progress opportunities
            self._progress_opportunities(current_date)
            
            current_date += timedelta(days=1)
        
        print(f"Generated CRM operations: {len(self.leads)} leads, "
              f"{len(self.opportunities)} opportunities, {len(self.cases)} cases")
    
    def _create_lead(self, date: datetime):
        """Create a lead"""
        campaign = random.choice(self.campaigns) if self.campaigns else None
        rep = random.choice(self.sales_reps) if self.sales_reps else None
        
        lead = {
            'lead_id': self.generate_id('LEAD', 'lead'),
            'lead_number': f"LEAD-{date.strftime('%Y%m%d')}-{self.counters['lead']:04d}",
            'company_name': f"Prospect Company {self.counters['lead']-1}",
            'lead_source': random.choice(['website', 'referral', 'trade_show', 'cold_call', 'social_media']),
            'source_campaign_id': campaign['campaign_id'] if campaign else None,
            'contact_first_name': f"Lead{self.counters['lead']-1}",
            'contact_last_name': "Contact",
            'email': f"lead{self.counters['lead']-1}@prospect.com",
            'phone': f"+91 {random.randint(7000000000, 9999999999)}",
            'industry': random.choice(['Automotive', 'Electronics', 'Aerospace', 'Packaging']),
            'company_size': random.choice(['small', 'medium', 'large']),
            'lead_score': random.randint(0, 100),
            'lead_status': random.choice(['new', 'contacted', 'qualified', 'unqualified', 'converted']),
            'estimated_deal_value': round(random.uniform(500000, 10000000), 2),
            'assigned_to': rep['sales_rep_id'] if rep else None,
            'converted': random.choice([True, False]),
            'is_active': True,
            'created_at': date.strftime('%Y-%m-%d %H:%M:%S')
        }
        self.leads.append(lead)
        
        # Create lead activities
        if lead['lead_status'] in ['contacted', 'qualified']:
            self._create_lead_activity(lead, date)
    
    def _create_lead_activity(self, lead: dict, date: datetime):
        """Create lead activity"""
        activity = {
            'activity_id': self.generate_id('LACT', 'lead_act'),
            'lead_id': lead['lead_id'],
            'activity_type': random.choice(['call', 'email', 'meeting']),
            'subject': f"Follow-up with {lead['company_name']}",
            'activity_date': date.strftime('%Y-%m-%d %H:%M:%S'),
            'outcome': random.choice(['completed', 'scheduled_follow_up']),
            'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        self.lead_activities.append(activity)
    
    def _create_opportunity(self, date: datetime):
        """Create opportunity"""
        if not self.accounts:
            return
        
        account = random.choice(self.accounts)
        account_contacts = [c for c in self.contacts if c['account_id'] == account['account_id']]
        contact = random.choice(account_contacts) if account_contacts else None
        rep = random.choice(self.sales_reps) if self.sales_reps else None
        
        stages = ['prospecting', 'qualification', 'needs_analysis', 'proposal', 'negotiation']
        stage = random.choice(stages)
        
        opp = {
            'opportunity_id': self.generate_id('OPP', 'opp'),
            'opportunity_number': f"OPP-{date.strftime('%Y%m%d')}-{self.counters['opp']:04d}",
            'opportunity_name': f"{account['account_name']} - New Project",
            'account_id': account['account_id'],
            'primary_contact_id': contact['contact_id'] if contact else None,
            'opportunity_type': random.choice(['new_business', 'existing_customer', 'upsell']),
            'amount': round(random.uniform(1000000, 25000000), 2),
            'stage': stage,
            'probability_pct': self._get_probability_for_stage(stage),
            'close_date': (date + timedelta(days=random.randint(30, 180))).strftime('%Y-%m-%d'),
            'opportunity_owner': rep['sales_rep_id'] if rep else None,
            'is_active': True,
            'created_at': date.strftime('%Y-%m-%d %H:%M:%S')
        }
        self.opportunities.append(opp)
        
        # Add products
        self._add_opportunity_products(opp)
        
        # Create quotation if in proposal stage
        if stage in ['proposal', 'negotiation']:
            self._create_quotation(opp, date)
    
    def _get_probability_for_stage(self, stage: str) -> int:
        """Get probability % for stage"""
        stage_probs = {
            'prospecting': 10,
            'qualification': 20,
            'needs_analysis': 40,
            'proposal': 60,
            'negotiation': 80,
            'closed_won': 100,
            'closed_lost': 0
        }
        return stage_probs.get(stage, 10)
    
    def _add_opportunity_products(self, opp: dict):
        """Add products to opportunity"""
        num_products = random.randint(1, 3)
        
        for line_num in range(1, num_products + 1):
            material = random.choice(self.materials) if self.materials else None
            if not material:
                continue
            
            qty = random.randint(100, 5000)
            unit_price = round(random.uniform(100, 5000), 2)
            
            opp_prod = {
                'opp_product_id': self.generate_id('OPPPROD', 'opp_prod'),
                'opportunity_id': opp['opportunity_id'],
                'line_number': line_num,
                'material_id': material['material_id'],
                'product_name': material['material_name'],
                'quantity': qty,
                'unit_of_measure': material.get('base_uom', 'EA'),
                'unit_price': unit_price,
                'line_total': round(qty * unit_price, 2),
                'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            self.opp_products.append(opp_prod)
    
    def _create_quotation(self, opp: dict, date: datetime):
        """Create quotation"""
        quote = {
            'quotation_id': self.generate_id('QUOTE', 'quote'),
            'quotation_number': f"QUOTE-{date.strftime('%Y%m%d')}-{self.counters['quote']:04d}",
            'quotation_name': f"Quote for {opp['opportunity_name']}",
            'opportunity_id': opp['opportunity_id'],
            'account_id': opp['account_id'],
            'quotation_date': date.strftime('%Y-%m-%d'),
            'valid_until_date': (date + timedelta(days=30)).strftime('%Y-%m-%d'),
            'quotation_status': random.choice(['sent', 'under_review', 'accepted']),
            'total_amount': opp['amount'],
            'payment_terms': random.choice(['NET30', 'NET60', 'advance']),
            'created_at': date.strftime('%Y-%m-%d %H:%M:%S')
        }
        self.quotations.append(quote)
        
        # Add quote lines from opp products
        opp_products = [p for p in self.opp_products if p['opportunity_id'] == opp['opportunity_id']]
        for prod in opp_products:
            quote_line = {
                'quote_line_id': self.generate_id('QLINE', 'quote_line'),
                'quotation_id': quote['quotation_id'],
                'line_number': prod['line_number'],
                'material_id': prod['material_id'],
                'product_name': prod['product_name'],
                'quantity': prod['quantity'],
                'unit_price': prod['unit_price'],
                'line_total': prod['line_total'],
                'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            self.quote_lines.append(quote_line)
    
    def _progress_opportunities(self, date: datetime):
        """Progress opportunities through stages"""
        # Randomly progress some opportunities
        active_opps = [o for o in self.opportunities if o.get('is_active', True) 
                      and o['stage'] not in ['closed_won', 'closed_lost']]
        
        for opp in random.sample(active_opps, min(3, len(active_opps))):
            if random.random() > 0.7:  # 30% chance to progress
                old_stage = opp['stage']
                new_stage = self._get_next_stage(old_stage)
                
                if new_stage != old_stage:
                    opp['stage'] = new_stage
                    opp['probability_pct'] = self._get_probability_for_stage(new_stage)
                    
                    # Record stage history
                    history = {
                        'history_id': self.generate_id('OPPHIST', 'opp_hist'),
                        'opportunity_id': opp['opportunity_id'],
                        'from_stage': old_stage,
                        'to_stage': new_stage,
                        'from_probability': self._get_probability_for_stage(old_stage),
                        'to_probability': self._get_probability_for_stage(new_stage),
                        'changed_at': date.strftime('%Y-%m-%d %H:%M:%S')
                    }
                    self.opp_history.append(history)
    
    def _get_next_stage(self, current_stage: str) -> str:
        """Get next stage in pipeline"""
        stage_flow = {
            'prospecting': 'qualification',
            'qualification': 'needs_analysis',
            'needs_analysis': 'proposal',
            'proposal': 'negotiation',
            'negotiation': random.choice(['closed_won', 'closed_lost'])
        }
        return stage_flow.get(current_stage, current_stage)
    
    def _create_case(self, date: datetime):
        """Create customer support case"""
        if not self.accounts:
            return
        
        account = random.choice(self.accounts)
        account_contacts = [c for c in self.contacts if c['account_id'] == account['account_id']]
        contact = random.choice(account_contacts) if account_contacts else None
        
        case = {
            'case_id': self.generate_id('CASE', 'case'),
            'case_number': f"CASE-{date.strftime('%Y%m%d')}-{self.counters['case']:04d}",
            'account_id': account['account_id'],
            'contact_id': contact['contact_id'] if contact else None,
            'subject': random.choice([
                'Product Quality Issue',
                'Delivery Delay',
                'Technical Support Request',
                'Billing Question',
                'Feature Request'
            ]),
            'description': 'Customer reported issue needs investigation',
            'case_type': random.choice(['question', 'problem', 'complaint']),
            'case_category': random.choice(['technical', 'billing', 'delivery', 'quality']),
            'priority': random.choice(['critical', 'high', 'medium', 'low']),
            'case_status': random.choice(['new', 'in_progress', 'resolved']),
            'created_at': date.strftime('%Y-%m-%d %H:%M:%S')
        }
        self.cases.append(case)
    
    def generate_sales_forecasts(self):
        """Generate quarterly sales forecasts"""
        print("Generating sales forecasts...")
        
        current_year = datetime.now().year
        
        for quarter in range(1, 5):
            for rep in self.sales_reps:
                # Calculate forecast from opportunities
                rep_opps = [o for o in self.opportunities 
                           if o.get('opportunity_owner') == rep['sales_rep_id']]
                
                pipeline = sum(o['amount'] for o in rep_opps if o['probability_pct'] <= 25)
                best_case = sum(o['amount'] for o in rep_opps if 25 < o['probability_pct'] <= 75)
                commit = sum(o['amount'] for o in rep_opps if 75 < o['probability_pct'] < 100)
                closed = sum(o['amount'] for o in rep_opps if o['probability_pct'] == 100)
                
                forecast = {
                    'forecast_id': self.generate_id('FCST', 'forecast'),
                    'forecast_period': 'quarterly',
                    'forecast_year': current_year,
                    'forecast_quarter': quarter,
                    'sales_rep_id': rep['sales_rep_id'],
                    'pipeline_amount': round(pipeline, 2),
                    'best_case_amount': round(best_case, 2),
                    'commit_amount': round(commit, 2),
                    'closed_amount': round(closed, 2),
                    'total_forecast': round(pipeline + best_case + commit + closed, 2),
                    'quota_amount': rep.get('quarterly_quota', rep.get('annual_quota', 0) / 4),
                    'snapshot_date': datetime.now().strftime('%Y-%m-%d'),
                    'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                self.forecasts.append(forecast)
        
        print(f"Generated {len(self.forecasts)} forecasts")
    
    def _print_summary(self):
        print(f"\n{'='*80}")
        print(f"CRM Data Generation Complete!")
        print(f"{'='*80}")
        print(f"\nMaster Data:")
        print(f"  Sales Reps: {len(self.sales_reps)}")
        print(f"  Territories: {len(self.territories)}")
        print(f"  Campaigns: {len(self.campaigns)}")
        
        print(f"\nAccounts & Contacts:")
        print(f"  Accounts: {len(self.accounts)}")
        print(f"  Contacts: {len(self.contacts)}")
        
        print(f"\nSales Pipeline:")
        print(f"  Leads: {len(self.leads)}")
        print(f"  Lead Activities: {len(self.lead_activities)}")
        print(f"  Opportunities: {len(self.opportunities)}")
        print(f"  Opportunity Products: {len(self.opp_products)}")
        print(f"  Stage History: {len(self.opp_history)}")
        
        print(f"\nQuotations:")
        print(f"  Quotations: {len(self.quotations)}")
        print(f"  Quote Lines: {len(self.quote_lines)}")
        
        print(f"\nCustomer Support:")
        print(f"  Cases: {len(self.cases)}")
        
        print(f"\nForecasting:")
        print(f"  Sales Forecasts: {len(self.forecasts)}")
    
    def to_json(self, output_file='crm_historical_data.json'):
        """Export to JSON with flat structure matching actual table names"""
        print(f"\nExporting to JSON...")
        
        data = {
            # Master Data
            'sales_reps': self.sales_reps,
            'sales_territories': self.territories,
            
            # Accounts & Contacts
            'accounts': self.accounts[:50],
            'contacts': self.contacts[:100],
            
            # Leads & Activities
            'leads': self.leads[:100],
            'lead_activities': self.lead_activities[:100],
            'activities': [],
            
            # Opportunities
            'opportunities': self.opportunities[:100],
            'opportunity_products': self.opp_products[:100],
            'opportunity_stage_history': self.opp_history[:50],
            
            # Quotations
            'quotations': self.quotations[:50],
            'quotation_lines': self.quote_lines[:100],
            
            # Cases & Notes
            'cases': self.cases[:50],
            'case_comments': [],
            'notes': [],
            'tasks': [],
            
            # Campaigns & Forecasting
            'campaigns': self.campaigns,
            'campaign_members': [],
            'sales_forecasts': self.forecasts,
            
            # Contracts & Integration
            'contracts': [],
            'crm_integration_log': [],
            
            # Customer Interactions
            'customer_interactions': []
        }
        
        with open(output_file, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"Data exported to {output_file}")


if __name__ == "__main__":
    from pathlib import Path
    
    # Get the directory of this script (data folder)
    script_dir = Path(__file__).parent
    
    generator = CRMDataGenerator()
    generator.generate_all_data()
    
    # Export to JSON (in same folder as script)
    json_file = script_dir / "crm_historical_data.json"
    generator.to_json(str(json_file))
    
    print("\n" + "="*80)
    print("CRM Historical Data Generation Complete!")
    print("="*80)
