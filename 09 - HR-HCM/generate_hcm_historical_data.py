#!/usr/bin/env python3
"""
GenIMS HR/HCM Historical Data Generator
Generates 180 days of HR data (employees, training, performance, attendance)
"""

import random
import json
from datetime import datetime, timedelta
from typing import List, Dict

# Configuration
DAYS_OF_HISTORY = 180
EMPLOYEES_PER_FACTORY = 50
TRAINING_COURSES_COUNT = 30
DEPARTMENTS_PER_FACTORY = 8

class HCMDataGenerator:
    def __init__(self, master_data_file=None):
        """Initialize with master data"""
        if master_data_file is None:
            from pathlib import Path
            master_data_file = Path(__file__).parent.parent / "01 - Base Data" / "genims_master_data.json"
        
        print("Loading existing data...")
        
        with open(master_data_file, 'r') as f:
            self.master_data = json.load(f)
        
        self.factories = self.master_data['factories']
        
        # HCM Data
        self.departments = []
        self.job_roles = []
        self.positions = []
        self.employees = []
        self.employment_history = []
        self.skills_catalog = []
        self.employee_skills = []
        self.role_skill_requirements = []
        self.training_courses = []
        self.training_requirements = []
        self.training_schedules = []
        self.training_enrollments = []
        self.certifications = []
        self.performance_reviews = []
        self.goals = []
        self.shift_schedules = []
        self.employee_shifts = []
        self.attendance_records = []
        self.leave_types = []
        self.leave_balances = []
        self.leave_requests = []
        self.onboarding_checklists = []
        self.employee_onboarding = []
        self.safety_incidents = []
        
        # Counters
        self.counters = {
            'dept': 1, 'role': 1, 'pos': 1, 'emp': 1, 'hist': 1,
            'skill': 1, 'emp_skill': 1, 'role_skill': 1,
            'course': 1, 'req': 1, 'schedule': 1, 'enroll': 1,
            'cert': 1, 'review': 1, 'goal': 1, 'shift': 1,
            'emp_shift': 1, 'attend': 1, 'leave_type': 1,
            'balance': 1, 'leave_req': 1, 'checklist': 1,
            'onboard': 1, 'incident': 1
        }
        
        print(f"Loaded: {len(self.factories)} factories")
    
    def generate_id(self, prefix: str, counter_key: str) -> str:
        id_val = f"{prefix}-{str(self.counters[counter_key]).zfill(6)}"
        self.counters[counter_key] += 1
        return id_val
    
    def generate_all_data(self):
        """Generate all HCM data"""
        print(f"\n{'='*80}")
        print(f"Generating HR/HCM Data ({DAYS_OF_HISTORY} days)")
        print(f"{'='*80}\n")
        
        # Master Data
        self.generate_skills_catalog()
        self.generate_job_roles()
        self.generate_departments()
        self.generate_positions()
        self.generate_training_courses()
        self.generate_training_requirements()
        self.generate_shift_schedules()
        self.generate_leave_types()
        self.generate_onboarding_checklists()
        
        # Employees
        self.generate_employees()
        
        # Employee Data
        self.assign_employee_skills()
        self.generate_training_schedules_and_enrollments()
        self.generate_certifications()
        self.assign_employee_shifts()
        
        # Historical Operations (180 days)
        start_date = datetime.now() - timedelta(days=DAYS_OF_HISTORY)
        self.generate_attendance_records(start_date, DAYS_OF_HISTORY)
        self.generate_leave_requests(start_date, DAYS_OF_HISTORY)
        self.generate_performance_reviews()
        self.generate_safety_incidents(start_date, DAYS_OF_HISTORY)
        
        self._print_summary()
    
    # ========================================================================
    # MASTER DATA
    # ========================================================================
    
    def generate_skills_catalog(self):
        """Generate skills catalog"""
        print("Generating skills catalog...")
        
        skills = [
            # Technical Skills
            {'name': 'CNC Machine Operation', 'category': 'technical', 'type': 'equipment_operation'},
            {'name': 'Quality Inspection', 'category': 'technical', 'type': 'process'},
            {'name': 'Lean Manufacturing', 'category': 'technical', 'type': 'process'},
            {'name': 'Six Sigma', 'category': 'technical', 'type': 'process'},
            {'name': 'Welding', 'category': 'technical', 'type': 'equipment_operation'},
            {'name': 'Forklift Operation', 'category': 'technical', 'type': 'equipment_operation'},
            {'name': 'ERP Software', 'category': 'technical', 'type': 'software'},
            {'name': 'AutoCAD', 'category': 'technical', 'type': 'software'},
            {'name': 'PLC Programming', 'category': 'technical', 'type': 'software'},
            {'name': 'Maintenance & Repair', 'category': 'technical', 'type': 'process'},
            # Soft Skills
            {'name': 'Leadership', 'category': 'soft_skill', 'type': 'process'},
            {'name': 'Communication', 'category': 'soft_skill', 'type': 'process'},
            {'name': 'Problem Solving', 'category': 'soft_skill', 'type': 'process'},
            {'name': 'Teamwork', 'category': 'soft_skill', 'type': 'process'},
            # Safety
            {'name': 'Workplace Safety', 'category': 'certification', 'type': 'safety'},
            {'name': 'Lockout-Tagout', 'category': 'certification', 'type': 'safety'},
            {'name': 'Hazmat Handling', 'category': 'certification', 'type': 'safety'}
        ]
        
        for skill in skills:
            s = {
                'skill_id': self.generate_id('SKILL', 'skill'),
                'skill_code': f"SK{self.counters['skill']-1:04d}",
                'skill_name': skill['name'],
                'skill_category': skill['category'],
                'skill_type': skill['type'],
                'has_proficiency_levels': True,
                'requires_certification': skill['category'] == 'certification',
                'is_active': True,
                'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            self.skills_catalog.append(s)
        
        print(f"Generated {len(self.skills_catalog)} skills")
    
    def generate_job_roles(self):
        """Generate job roles"""
        print("Generating job roles...")
        
        roles = [
            {'name': 'Production Operator', 'category': 'operational', 'family': 'operations', 'level': 'entry'},
            {'name': 'Senior Operator', 'category': 'operational', 'family': 'operations', 'level': 'intermediate'},
            {'name': 'Production Supervisor', 'category': 'managerial', 'family': 'operations', 'level': 'lead'},
            {'name': 'Quality Inspector', 'category': 'technical', 'family': 'quality', 'level': 'entry'},
            {'name': 'Maintenance Technician', 'category': 'technical', 'family': 'maintenance', 'level': 'intermediate'},
            {'name': 'Warehouse Associate', 'category': 'operational', 'family': 'logistics', 'level': 'entry'},
            {'name': 'Materials Coordinator', 'category': 'administrative', 'family': 'logistics', 'level': 'intermediate'},
            {'name': 'Plant Manager', 'category': 'managerial', 'family': 'operations', 'level': 'manager'},
            {'name': 'Safety Officer', 'category': 'technical', 'family': 'safety', 'level': 'lead'},
            {'name': 'HR Coordinator', 'category': 'administrative', 'family': 'support', 'level': 'intermediate'}
        ]
        
        for role in roles:
            r = {
                'role_id': self.generate_id('ROLE', 'role'),
                'role_code': f"ROLE{self.counters['role']-1:04d}",
                'role_name': role['name'],
                'role_category': role['category'],
                'role_family': role['family'],
                'role_level': role['level'],
                'job_description': f"Responsible for {role['name'].lower()} duties",
                'min_experience_years': random.randint(0, 5),
                'is_active': True,
                'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            self.job_roles.append(r)
        
        print(f"Generated {len(self.job_roles)} job roles")
    
    def generate_departments(self):
        """Generate departments"""
        print("Generating departments...")
        
        dept_names = ['Production', 'Quality', 'Maintenance', 'Warehouse', 
                     'Planning', 'Engineering', 'Safety', 'HR']
        
        for factory in self.factories:
            # Generate factory code if not present
            factory_code = factory.get('factory_code', f"FAC-{factory['factory_id'][-4:]}")
            for dept_name in dept_names:
                dept = {
                    'department_id': self.generate_id('DEPT', 'dept'),
                    'department_code': f"{factory_code}-{dept_name.upper()[:4]}",
                    'department_name': f"{dept_name} - {factory['factory_name']}",
                    'factory_id': factory['factory_id'],
                    'cost_center': f"CC-{self.counters['dept']-1:04d}",
                    'is_active': True,
                    'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                self.departments.append(dept)
        
        print(f"Generated {len(self.departments)} departments")
    
    def generate_positions(self):
        """Generate positions"""
        print("Generating positions...")
        
        for dept in self.departments:
            # 3-10 positions per department
            for _ in range(random.randint(3, 10)):
                role = random.choice(self.job_roles)
                
                pos = {
                    'position_id': self.generate_id('POS', 'pos'),
                    'position_code': f"POS-{self.counters['pos']-1:05d}",
                    'position_name': f"{role['role_name']} - {dept['department_name']}",
                    'role_id': role['role_id'],
                    'department_id': dept['department_id'],
                    'position_status': 'vacant',  # Will assign later
                    'is_budgeted': True,
                    'budget_year': datetime.now().year,
                    'is_active': True,
                    'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                self.positions.append(pos)
        
        print(f"Generated {len(self.positions)} positions")
    
    def generate_training_courses(self):
        """Generate training courses"""
        print("Generating training courses...")
        
        courses = [
            {'name': 'New Employee Orientation', 'category': 'compliance', 'hours': 4, 'cert': False},
            {'name': 'Workplace Safety Basics', 'category': 'safety', 'hours': 8, 'cert': True},
            {'name': 'Lockout-Tagout Procedures', 'category': 'safety', 'hours': 4, 'cert': True},
            {'name': 'Quality Management Systems', 'category': 'technical', 'hours': 16, 'cert': False},
            {'name': 'Lean Manufacturing Principles', 'category': 'technical', 'hours': 24, 'cert': True},
            {'name': 'Forklift Operation Certification', 'category': 'safety', 'hours': 8, 'cert': True},
            {'name': 'First Aid & CPR', 'category': 'safety', 'hours': 8, 'cert': True},
            {'name': 'Hazardous Materials Handling', 'category': 'safety', 'hours': 16, 'cert': True},
            {'name': 'Leadership Development', 'category': 'soft_skills', 'hours': 40, 'cert': False},
            {'name': 'Communication Skills', 'category': 'soft_skills', 'hours': 16, 'cert': False}
        ]
        
        for course in courses:
            c = {
                'course_id': self.generate_id('COURSE', 'course'),
                'course_code': f"TRN{self.counters['course']-1:04d}",
                'course_name': course['name'],
                'course_category': course['category'],
                'course_type': 'classroom',
                'duration_hours': course['hours'],
                'delivery_method': random.choice(['in_person', 'virtual', 'blended']),
                'has_assessment': True,
                'passing_score': 70,
                'provides_certification': course['cert'],
                'certificate_validity_months': 24 if course['cert'] else None,
                'cost_per_participant': round(random.uniform(500, 5000), 2),
                'course_status': 'active',
                'is_active': True,
                'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            self.training_courses.append(c)
        
        print(f"Generated {len(self.training_courses)} training courses")
    
    def generate_training_requirements(self):
        """Generate training requirements"""
        print("Generating training requirements...")
        
        # Role-based requirements
        for role in self.job_roles:
            # Each role requires 1-3 mandatory trainings
            for _ in range(random.randint(1, 3)):
                course = random.choice(self.training_courses)
                
                req = {
                    'requirement_id': self.generate_id('TREQ', 'req'),
                    'requirement_type': 'role_based',
                    'role_id': role['role_id'],
                    'course_id': course['course_id'],
                    'is_mandatory': True,
                    'frequency': random.choice(['one_time', 'annual', 'biennial']),
                    'validity_months': 24 if course.get('provides_certification') else None,
                    'is_active': True,
                    'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                self.training_requirements.append(req)
        
        print(f"Generated {len(self.training_requirements)} training requirements")
    
    def generate_shift_schedules(self):
        """Generate shift schedules"""
        print("Generating shift schedules...")
        
        shifts = [
            {'name': 'Day Shift', 'type': 'day', 'start': '08:00', 'end': '16:00'},
            {'name': 'Evening Shift', 'type': 'evening', 'start': '16:00', 'end': '00:00'},
            {'name': 'Night Shift', 'type': 'night', 'start': '00:00', 'end': '08:00'}
        ]
        
        for factory in self.factories:
            factory_code = factory.get('factory_code', f"FAC-{factory['factory_id'][-4:]}")
            for shift in shifts:
                s = {
                    'shift_id': self.generate_id('SHIFT', 'shift'),
                    'shift_code': f"{factory_code}-{shift['type'].upper()[:3]}",
                    'shift_name': f"{shift['name']} - {factory['factory_name']}",
                    'start_time': shift['start'],
                    'end_time': shift['end'],
                    'shift_type': shift['type'],
                    'factory_id': factory['factory_id'],
                    'is_active': True,
                    'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                self.shift_schedules.append(s)
        
        print(f"Generated {len(self.shift_schedules)} shift schedules")
    
    def generate_leave_types(self):
        """Generate leave types"""
        print("Generating leave types...")
        
        leave_types_config = [
            {'name': 'Paid Time Off', 'category': 'paid', 'accrual': 1.67, 'max': 20},
            {'name': 'Sick Leave', 'category': 'paid', 'accrual': 0.83, 'max': 10},
            {'name': 'Casual Leave', 'category': 'paid', 'accrual': 0.67, 'max': 8},
            {'name': 'Maternity Leave', 'category': 'statutory', 'accrual': 0, 'max': 180},
            {'name': 'Paternity Leave', 'category': 'statutory', 'accrual': 0, 'max': 15}
        ]
        
        for lt_config in leave_types_config:
            lt = {
                'leave_type_id': self.generate_id('LTYPE', 'leave_type'),
                'leave_type_code': f"LT{self.counters['leave_type']-1:02d}",
                'leave_type_name': lt_config['name'],
                'leave_category': lt_config['category'],
                'accrual_enabled': lt_config['accrual'] > 0,
                'accrual_frequency': 'monthly' if lt_config['accrual'] > 0 else None,
                'accrual_rate': lt_config['accrual'],
                'max_days_per_year': lt_config['max'],
                'requires_approval': True,
                'is_active': True,
                'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            self.leave_types.append(lt)
        
        print(f"Generated {len(self.leave_types)} leave types")
    
    def generate_onboarding_checklists(self):
        """Generate onboarding checklists"""
        print("Generating onboarding checklists...")
        
        checklist = {
            'checklist_id': self.generate_id('ONBCL', 'checklist'),
            'checklist_code': 'ONB-STANDARD',
            'checklist_name': 'Standard Employee Onboarding',
            'is_active': True,
            'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        self.onboarding_checklists.append(checklist)
        
        print(f"Generated {len(self.onboarding_checklists)} onboarding checklists")
    
    # ========================================================================
    # EMPLOYEES
    # ========================================================================
    
    def generate_employees(self):
        """Generate employees"""
        print("Generating employees...")
        
        # Generate employees and assign to positions
        positions_to_fill = self.positions.copy()
        random.shuffle(positions_to_fill)
        
        for i, pos in enumerate(positions_to_fill[:len(positions_to_fill)//2]):  # Fill 50% of positions
            factory = next((f for f in self.factories if any(d['department_id'] == pos['department_id'] 
                           for d in self.departments if d['factory_id'] == f['factory_id'])), None)
            
            dept = next((d for d in self.departments if d['department_id'] == pos['department_id']), None)
            role = next((r for r in self.job_roles if r['role_id'] == pos['role_id']), None)
            
            emp = {
                'employee_id': self.generate_id('EMP', 'emp'),
                'employee_number': f"EMP{self.counters['emp']-1:05d}",
                'first_name': f"Employee{i+1}",
                'last_name': f"LastName{i+1}",
                'work_email': f"emp{i+1}@company.com",
                'mobile_phone': f"+91 {random.randint(7000000000, 9999999999)}",
                'hire_date': (datetime.now() - timedelta(days=random.randint(30, 1825))).strftime('%Y-%m-%d'),
                'employment_type': random.choice(['full_time', 'full_time', 'full_time', 'contract']),
                'employment_status': 'active',
                'primary_factory_id': factory['factory_id'] if factory else None,
                'primary_department_id': dept['department_id'] if dept else None,
                'primary_position_id': pos['position_id'],
                'job_title': role['role_name'] if role else 'Employee',
                'job_level': role.get('role_level', 'entry') if role else 'entry',
                'shift_type': random.choice(['day', 'evening', 'night', 'rotating']),
                'annual_salary': round(random.uniform(300000, 2000000), 2),
                'is_active': True,
                'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            self.employees.append(emp)
            
            # Mark position as occupied
            pos['position_status'] = 'occupied'
            pos['employee_id'] = emp['employee_id']
        
        print(f"Generated {len(self.employees)} employees")
    
    def assign_employee_skills(self):
        """Assign skills to employees (no duplicates)"""
        print("Assigning skills to employees...")
        
        seen = set()  # Track (employee_id, skill_id) pairs to avoid duplicates
        
        for emp in self.employees:
            # Assign 3-8 unique skills per employee
            skills_to_assign = random.sample(self.skills_catalog, min(random.randint(3, 8), len(self.skills_catalog)))
            
            for skill in skills_to_assign:
                emp_id = emp['employee_id']
                skill_id = skill['skill_id']
                key = (emp_id, skill_id)
                
                # Skip if already assigned
                if key in seen:
                    continue
                
                seen.add(key)
                emp_skill = {
                    'employee_skill_id': self.generate_id('EMPSKL', 'emp_skill'),
                    'employee_id': emp_id,
                    'skill_id': skill_id,
                    'proficiency_level': random.randint(2, 4),
                    'proficiency_name': random.choice(['intermediate', 'advanced', 'expert']),
                    'acquired_date': (datetime.now() - timedelta(days=random.randint(30, 730))).strftime('%Y-%m-%d'),
                    'years_of_experience': round(random.uniform(0.5, 5), 1),
                    'verified': random.choice([True, False]),
                    'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                self.employee_skills.append(emp_skill)
        
        print(f"Assigned {len(self.employee_skills)} unique skills to employees")
    
    def generate_training_schedules_and_enrollments(self):
        """Generate training schedules and enroll employees"""
        print("Generating training schedules and enrollments...")
        
        # Track (schedule_id, employee_id) pairs to prevent duplicates
        seen_enrollments = set()
        
        # Generate schedules for past 180 days
        for i in range(20):  # 20 training sessions
            course = random.choice(self.training_courses)
            factory = random.choice(self.factories)
            
            start_date = datetime.now() - timedelta(days=random.randint(7, 150))
            
            schedule = {
                'schedule_id': self.generate_id('SCHED', 'schedule'),
                'course_id': course['course_id'],
                'session_name': f"{course['course_name']} - Session {i+1}",
                'start_datetime': start_date.strftime('%Y-%m-%d 09:00:00'),
                'end_datetime': (start_date + timedelta(hours=int(course['duration_hours']))).strftime('%Y-%m-%d %H:%M:%S'),
                'factory_id': factory['factory_id'],
                'max_participants': random.randint(15, 30),
                'schedule_status': 'completed',
                'completed_date': (start_date + timedelta(days=1)).strftime('%Y-%m-%d'),
                'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            self.training_schedules.append(schedule)
            
            # Enroll 5-15 unique employees per schedule
            enrolled_count = random.randint(5, 15)
            selected_employees = random.sample(self.employees, min(enrolled_count, len(self.employees)))
            
            for emp in selected_employees:
                # Check if we already have this combination
                enrollment_key = (schedule['schedule_id'], emp['employee_id'])
                if enrollment_key in seen_enrollments:
                    continue
                
                seen_enrollments.add(enrollment_key)
                
                passed = random.random() > 0.1  # 90% pass rate
                
                enrollment = {
                    'enrollment_id': self.generate_id('ENROLL', 'enroll'),
                    'schedule_id': schedule['schedule_id'],
                    'employee_id': emp['employee_id'],
                    'enrollment_date': (start_date - timedelta(days=7)).strftime('%Y-%m-%d'),
                    'enrollment_status': 'attended',
                    'attended': True,
                    'attendance_date': start_date.strftime('%Y-%m-%d'),
                    'assessment_score': round(random.uniform(70, 100), 2) if passed else round(random.uniform(40, 69), 2),
                    'passed': passed,
                    'completion_status': 'completed' if passed else 'failed',
                    'completion_date': start_date.strftime('%Y-%m-%d'),
                    'certificate_issued': passed and course.get('provides_certification', False),
                    'feedback_rating': random.randint(3, 5),
                    'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                self.training_enrollments.append(enrollment)
        
        print(f"Generated {len(self.training_schedules)} training schedules")
        print(f"Generated {len(self.training_enrollments)} training enrollments (all unique)")
    
    def generate_certifications(self):
        """Generate employee certifications"""
        print("Generating certifications...")
        
        # Generate certifications for some employees
        for emp in random.sample(self.employees, len(self.employees)//2):
            # 1-3 certifications per employee
            for _ in range(random.randint(1, 3)):
                issue_date = datetime.now() - timedelta(days=random.randint(30, 730))
                
                cert = {
                    'certification_id': self.generate_id('CERT', 'cert'),
                    'employee_id': emp['employee_id'],
                    'certification_name': random.choice(['Safety Certification', 'Quality Certification', 
                                                        'Forklift License', 'First Aid', 'Lean Six Sigma']),
                    'certification_type': random.choice(['professional', 'safety', 'equipment']),
                    'issuing_organization': random.choice(['ISO', 'OSHA', 'Internal', 'ASQ']),
                    'certification_number': f"CERT-{random.randint(100000, 999999)}",
                    'issue_date': issue_date.strftime('%Y-%m-%d'),
                    'expiry_date': (issue_date + timedelta(days=730)).strftime('%Y-%m-%d'),
                    'requires_renewal': True,
                    'renewal_frequency_months': 24,
                    'certification_status': 'active',
                    'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                self.certifications.append(cert)
        
        print(f"Generated {len(self.certifications)} certifications")
    
    def assign_employee_shifts(self):
        """Assign shifts to employees"""
        print("Assigning shifts to employees...")
        
        for emp in self.employees:
            # Find shifts for employee's factory
            factory_shifts = [s for s in self.shift_schedules 
                            if s['factory_id'] == emp.get('primary_factory_id')]
            
            if factory_shifts:
                shift = random.choice(factory_shifts)
                
                emp_shift = {
                    'employee_shift_id': self.generate_id('EMPSHFT', 'emp_shift'),
                    'employee_id': emp['employee_id'],
                    'shift_id': shift['shift_id'],
                    'effective_date': emp['hire_date'],
                    'monday': True,
                    'tuesday': True,
                    'wednesday': True,
                    'thursday': True,
                    'friday': True,
                    'saturday': random.choice([True, False]),
                    'sunday': False,
                    'is_active': True,
                    'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                self.employee_shifts.append(emp_shift)
        
        print(f"Assigned {len(self.employee_shifts)} shifts")
    
    # ========================================================================
    # HISTORICAL OPERATIONS
    # ========================================================================
    
    def generate_attendance_records(self, start_date: datetime, days: int):
        """Generate daily attendance records"""
        print(f"Generating {days} days of attendance records...")
        
        current_date = start_date
        
        for day in range(days):
            # Skip weekends (simplified)
            if current_date.weekday() < 5:  # Monday-Friday
                for emp in self.employees:
                    # 95% attendance rate
                    if random.random() < 0.95:
                        attendance = {
                            'attendance_id': self.generate_id('ATT', 'attend'),
                            'employee_id': emp['employee_id'],
                            'attendance_date': current_date.strftime('%Y-%m-%d'),
                            'clock_in_time': current_date.strftime(f'%Y-%m-%d {random.randint(7,9):02d}:{random.randint(0,59):02d}:00'),
                            'clock_out_time': current_date.strftime(f'%Y-%m-%d {random.randint(16,18):02d}:{random.randint(0,59):02d}:00'),
                            'scheduled_hours': 8,
                            'actual_hours': round(random.uniform(7.5, 9), 2),
                            'regular_hours': 8,
                            'overtime_hours': round(random.uniform(0, 2), 2) if random.random() > 0.7 else 0,
                            'attendance_status': 'present',
                            'late_minutes': random.randint(0, 30) if random.random() > 0.8 else 0,
                            'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        }
                        self.attendance_records.append(attendance)
            
            current_date += timedelta(days=1)
        
        print(f"Generated {len(self.attendance_records)} attendance records")
    
    def generate_leave_requests(self, start_date: datetime, days: int):
        """Generate leave requests"""
        print("Generating leave requests...")
        
        for emp in self.employees:
            # Each employee takes 1-3 leaves
            for _ in range(random.randint(1, 3)):
                leave_type = random.choice(self.leave_types)
                leave_start = start_date + timedelta(days=random.randint(0, days-5))
                leave_days = random.randint(1, 5)
                
                leave_req = {
                    'request_id': self.generate_id('LREQ', 'leave_req'),
                    'employee_id': emp['employee_id'],
                    'leave_type_id': leave_type['leave_type_id'],
                    'request_date': (leave_start - timedelta(days=7)).strftime('%Y-%m-%d'),
                    'start_date': leave_start.strftime('%Y-%m-%d'),
                    'end_date': (leave_start + timedelta(days=leave_days)).strftime('%Y-%m-%d'),
                    'total_days': leave_days,
                    'reason': 'Personal reasons',
                    'request_status': random.choice(['approved', 'approved', 'approved', 'pending']),
                    'approval_date': leave_start.strftime('%Y-%m-%d'),
                    'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                self.leave_requests.append(leave_req)
        
        print(f"Generated {len(self.leave_requests)} leave requests")
    
    def generate_performance_reviews(self):
        """Generate performance reviews"""
        print("Generating performance reviews...")
        
        # Annual reviews for employees hired > 1 year ago
        for emp in self.employees:
            hire_date = datetime.strptime(emp['hire_date'], '%Y-%m-%d')
            if (datetime.now() - hire_date).days > 365:
                review = {
                    'review_id': self.generate_id('REV', 'review'),
                    'employee_id': emp['employee_id'],
                    'review_type': 'annual',
                    'review_period_start': (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d'),
                    'review_period_end': datetime.now().strftime('%Y-%m-%d'),
                    'review_date': datetime.now().strftime('%Y-%m-%d'),
                    'overall_rating': round(random.uniform(3.0, 5.0), 2),
                    'performance_level': random.choice(['exceeds', 'meets', 'meets']),
                    'technical_competency_rating': round(random.uniform(3.0, 5.0), 2),
                    'behavioral_competency_rating': round(random.uniform(3.0, 5.0), 2),
                    'goals_achievement_pct': round(random.uniform(70, 100), 2),
                    'review_status': 'finalized',
                    'acknowledged_by_employee': True,
                    'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                self.performance_reviews.append(review)
        
        print(f"Generated {len(self.performance_reviews)} performance reviews")
    
    def generate_safety_incidents(self, start_date: datetime, days: int):
        """Generate safety incidents"""
        print("Generating safety incidents...")
        
        # 1-3 incidents per month
        for _ in range(random.randint(6, 18)):
            emp = random.choice(self.employees)
            incident_date = start_date + timedelta(days=random.randint(0, days))
            
            incident = {
                'incident_id': self.generate_id('INC', 'incident'),
                'incident_number': f"INC-{self.counters['incident']-1:05d}",
                'employee_id': emp['employee_id'],
                'incident_date': incident_date.strftime('%Y-%m-%d'),
                'factory_id': emp.get('primary_factory_id'),
                'department_id': emp.get('primary_department_id'),
                'incident_type': random.choice(['injury', 'near_miss', 'property_damage']),
                'severity': random.choice(['minor', 'moderate', 'serious']),
                'description': 'Safety incident description',
                'investigation_status': random.choice(['completed', 'in_progress']),
                'incident_status': random.choice(['closed', 'open']),
                'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            self.safety_incidents.append(incident)
        
        print(f"Generated {len(self.safety_incidents)} safety incidents")
    
    def _print_summary(self):
        print(f"\n{'='*80}")
        print(f"HR/HCM Data Generation Complete!")
        print(f"{'='*80}")
        print(f"\nOrganization:")
        print(f"  Departments: {len(self.departments)}")
        print(f"  Job Roles: {len(self.job_roles)}")
        print(f"  Positions: {len(self.positions)}")
        
        print(f"\nWorkforce:")
        print(f"  Employees: {len(self.employees)}")
        print(f"  Employee Skills: {len(self.employee_skills)}")
        
        print(f"\nTraining & Development:")
        print(f"  Training Courses: {len(self.training_courses)}")
        print(f"  Training Schedules: {len(self.training_schedules)}")
        print(f"  Training Enrollments: {len(self.training_enrollments)}")
        print(f"  Certifications: {len(self.certifications)}")
        
        print(f"\nOperational Data:")
        print(f"  Attendance Records: {len(self.attendance_records)}")
        print(f"  Leave Requests: {len(self.leave_requests)}")
        print(f"  Performance Reviews: {len(self.performance_reviews)}")
        print(f"  Safety Incidents: {len(self.safety_incidents)}")
    
    def to_json(self, output_file='hcm_historical_data.json'):
        """Export to JSON with flat structure matching actual table names"""
        print(f"\nExporting to JSON...")
        
        data = {
            # Organization Structure
            'departments': self.departments[:20],
            'job_roles': self.job_roles,
            'positions': self.positions[:50],
            
            # Workforce
            'employees': self.employees[:100],
            'employee_employment_history': [],
            'employee_skills': self.employee_skills[:100],
            'employee_certifications': self.certifications[:50],
            
            # Assignments & Shifts
            'employee_shifts': [],
            'shift_schedules': [],
            'employee_goals': [],
            
            # Training & Development
            'training_courses': self.training_courses,
            'training_schedules': self.training_schedules,
            'training_enrollments': self.training_enrollments[:100],
            'training_requirements': [],
            'career_paths': [],
            
            # Performance & Reviews
            'performance_reviews': self.performance_reviews[:30],
            'performance_kpis': [],
            'succession_planning': [],
            'succession_candidates': [],
            
            # Leave & Attendance
            'leave_types': [],
            'leave_requests': self.leave_requests[:50],
            'employee_leave_balances': [],
            'attendance_records': self.attendance_records[:200],
            
            # Safety & Onboarding
            'safety_incidents': self.safety_incidents,
            'ppe_requirements': [],
            'employee_onboarding': [],
            'employee_onboarding_items': [],
            'onboarding_checklists': [],
            'onboarding_checklist_items': [],
            'offboarding_records': [],
            
            # Skill Management
            'skills_catalog': [],
            'role_skill_requirements': [],
            
            # Integration & Logging
            'hcm_integration_log': []
        }
        
        with open(output_file, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"Data exported to {output_file}")


if __name__ == "__main__":
    from pathlib import Path
    
    # Get the directory of this script (data folder)
    script_dir = Path(__file__).parent
    
    generator = HCMDataGenerator()
    generator.generate_all_data()
    
    # Export to JSON (in same folder as script)
    json_file = script_dir / "hcm_historical_data.json"
    generator.to_json(str(json_file))
    
    print("\n" + "="*80)
    print("HR/HCM Historical Data Generation Complete!")
    print("="*80)
