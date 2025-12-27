-- GenIMS HR/HCM (Human Capital Management) Schema
-- Complete people management from hire to retire

-- ============================================================================
-- EMPLOYEE MASTER DATA
-- ============================================================================

CREATE TABLE employees (
    employee_id VARCHAR(50) PRIMARY KEY,
    employee_number VARCHAR(50) UNIQUE NOT NULL,
    
    -- Personal Information
    first_name VARCHAR(100) NOT NULL,
    middle_name VARCHAR(100),
    last_name VARCHAR(100) NOT NULL,
    preferred_name VARCHAR(100),
    
    salutation VARCHAR(10), -- Mr., Ms., Dr., Prof.
    gender VARCHAR(20),
    date_of_birth DATE,
    
    -- Contact Information
    personal_email VARCHAR(100),
    work_email VARCHAR(100),
    mobile_phone VARCHAR(50),
    home_phone VARCHAR(50),
    
    -- Address
    address_line1 VARCHAR(200),
    address_line2 VARCHAR(200),
    city VARCHAR(100),
    state VARCHAR(100),
    country VARCHAR(50) DEFAULT 'India',
    postal_code VARCHAR(20),
    
    -- Emergency Contact
    emergency_contact_name VARCHAR(200),
    emergency_contact_relationship VARCHAR(50),
    emergency_contact_phone VARCHAR(50),
    
    -- Employment Details
    hire_date DATE NOT NULL,
    employment_type VARCHAR(30), -- full_time, part_time, contract, intern
    employment_status VARCHAR(30) DEFAULT 'active',
    -- active, on_leave, suspended, terminated, retired
    
    termination_date DATE,
    termination_reason VARCHAR(200),
    
    -- Assignment
    primary_factory_id VARCHAR(50), -- FK to factories
    primary_department_id VARCHAR(50), -- FK to departments
    primary_position_id VARCHAR(50), -- FK to positions
    reports_to_employee_id VARCHAR(50), -- FK to employees (manager)
    
    -- Work Details
    job_title VARCHAR(200),
    job_level VARCHAR(50), -- entry, intermediate, senior, lead, manager, director, executive
    work_location VARCHAR(200),
    
    -- Shift & Schedule
    shift_type VARCHAR(30), -- day, evening, night, rotating, flexible
    weekly_hours DECIMAL(5,2) DEFAULT 40,
    
    -- Compensation (Basic)
    salary_grade VARCHAR(20),
    annual_salary DECIMAL(15,2),
    currency VARCHAR(3) DEFAULT 'INR',
    
    -- Benefits
    benefits_eligible BOOLEAN DEFAULT true,
    
    -- Identifications
    national_id VARCHAR(50), -- Aadhaar, SSN, etc.
    passport_number VARCHAR(50),
    tax_id VARCHAR(50), -- PAN in India
    
    -- Photo
    photo_url VARCHAR(500),
    
    -- User Account
    user_account_created BOOLEAN DEFAULT false,
    username VARCHAR(100),
    
    -- Status
    is_active BOOLEAN DEFAULT true,
    
    -- Audit
    created_by VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE employee_employment_history (
    history_id VARCHAR(50) PRIMARY KEY,
    employee_id VARCHAR(50) NOT NULL, -- FK to employees
    
    -- Change Type
    change_type VARCHAR(50), -- hire, promotion, transfer, demotion, termination
    
    -- Previous Values
    previous_position_id VARCHAR(50),
    previous_department_id VARCHAR(50),
    previous_job_title VARCHAR(200),
    previous_job_level VARCHAR(50),
    previous_manager_id VARCHAR(50),
    previous_factory_id VARCHAR(50),
    previous_salary DECIMAL(15,2),
    
    -- New Values
    new_position_id VARCHAR(50),
    new_department_id VARCHAR(50),
    new_job_title VARCHAR(200),
    new_job_level VARCHAR(50),
    new_manager_id VARCHAR(50),
    new_factory_id VARCHAR(50),
    new_salary DECIMAL(15,2),
    
    -- Details
    effective_date DATE NOT NULL,
    reason TEXT,
    
    -- Approval
    approved_by VARCHAR(50),
    approved_date DATE,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- ORGANIZATIONAL STRUCTURE
-- ============================================================================

CREATE TABLE departments (
    department_id VARCHAR(50) PRIMARY KEY,
    department_code VARCHAR(50) UNIQUE NOT NULL,
    department_name VARCHAR(200) NOT NULL,
    
    -- Hierarchy
    parent_department_id VARCHAR(50), -- FK to departments
    
    -- Location
    factory_id VARCHAR(50), -- FK to factories
    
    -- Leadership
    department_head_id VARCHAR(50), -- FK to employees
    
    -- Cost Center
    cost_center VARCHAR(50),
    
    -- Description
    description TEXT,
    
    -- Status
    is_active BOOLEAN DEFAULT true,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE job_roles (
    role_id VARCHAR(50) PRIMARY KEY,
    role_code VARCHAR(50) UNIQUE NOT NULL,
    role_name VARCHAR(200) NOT NULL,
    
    -- Classification
    role_category VARCHAR(50), -- technical, managerial, administrative, operational
    role_family VARCHAR(100), -- engineering, sales, operations, support
    
    -- Level
    role_level VARCHAR(50), -- entry, intermediate, senior, lead, manager, director
    
    -- Description
    job_description TEXT,
    key_responsibilities TEXT,
    required_qualifications TEXT,
    
    -- Requirements
    min_education VARCHAR(50), -- high_school, diploma, bachelor, master, phd
    min_experience_years INTEGER,
    
    -- Reporting
    reports_to_role_id VARCHAR(50), -- FK to job_roles
    
    -- Status
    is_active BOOLEAN DEFAULT true,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE positions (
    position_id VARCHAR(50) PRIMARY KEY,
    position_code VARCHAR(50) UNIQUE NOT NULL,
    position_name VARCHAR(200) NOT NULL,
    
    -- Role & Department
    role_id VARCHAR(50) NOT NULL, -- FK to job_roles
    department_id VARCHAR(50) NOT NULL, -- FK to departments
    
    -- Assignment
    employee_id VARCHAR(50), -- FK to employees (current occupant)
    
    -- Status
    position_status VARCHAR(30) DEFAULT 'vacant',
    -- vacant, occupied, frozen, eliminated
    
    -- Budgeted
    is_budgeted BOOLEAN DEFAULT true,
    budget_year INTEGER,
    
    -- Dates
    position_start_date DATE,
    position_end_date DATE,
    
    is_active BOOLEAN DEFAULT true,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- SKILLS & COMPETENCIES
-- ============================================================================

CREATE TABLE skills_catalog (
    skill_id VARCHAR(50) PRIMARY KEY,
    skill_code VARCHAR(50) UNIQUE NOT NULL,
    skill_name VARCHAR(200) NOT NULL,
    
    -- Classification
    skill_category VARCHAR(50), -- technical, soft_skill, language, certification
    skill_type VARCHAR(50), -- equipment_operation, software, process, safety
    
    -- Description
    description TEXT,
    
    -- Proficiency Levels
    has_proficiency_levels BOOLEAN DEFAULT true,
    -- Levels: 1=Beginner, 2=Intermediate, 3=Advanced, 4=Expert, 5=Master
    
    -- Verification
    requires_certification BOOLEAN DEFAULT false,
    certification_body VARCHAR(200),
    
    is_active BOOLEAN DEFAULT true,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE employee_skills (
    employee_skill_id VARCHAR(50) PRIMARY KEY,
    employee_id VARCHAR(50) NOT NULL, -- FK to employees
    skill_id VARCHAR(50) NOT NULL, -- FK to skills_catalog
    
    -- Proficiency
    proficiency_level INTEGER DEFAULT 1, -- 1-5
    proficiency_name VARCHAR(50), -- beginner, intermediate, advanced, expert, master
    
    -- Acquisition
    acquired_date DATE,
    last_used_date DATE,
    years_of_experience DECIMAL(5,2),
    
    -- Verification
    verified BOOLEAN DEFAULT false,
    verified_by VARCHAR(50),
    verified_date DATE,
    
    -- Self-assessment vs Manager Assessment
    self_assessment_level INTEGER,
    manager_assessment_level INTEGER,
    
    notes TEXT,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(employee_id, skill_id)
);

CREATE TABLE role_skill_requirements (
    requirement_id VARCHAR(50) PRIMARY KEY,
    role_id VARCHAR(50) NOT NULL, -- FK to job_roles
    skill_id VARCHAR(50) NOT NULL, -- FK to skills_catalog
    
    -- Requirement Level
    requirement_type VARCHAR(30), -- required, preferred, optional
    min_proficiency_level INTEGER DEFAULT 1, -- Minimum level needed
    
    -- Priority
    priority INTEGER DEFAULT 5, -- 1=critical, 5=nice to have
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(role_id, skill_id)
);

-- ============================================================================
-- TRAINING & DEVELOPMENT
-- ============================================================================

CREATE TABLE training_courses (
    course_id VARCHAR(50) PRIMARY KEY,
    course_code VARCHAR(50) UNIQUE NOT NULL,
    course_name VARCHAR(200) NOT NULL,
    
    -- Classification
    course_category VARCHAR(50), -- technical, safety, compliance, soft_skills, leadership
    course_type VARCHAR(50), -- classroom, online, on_the_job, workshop, certification
    
    -- Description
    description TEXT,
    learning_objectives TEXT,
    
    -- Duration
    duration_hours DECIMAL(5,2),
    
    -- Delivery
    delivery_method VARCHAR(50), -- in_person, virtual, self_paced, blended
    
    -- Provider
    training_provider VARCHAR(200), -- internal, external vendor
    instructor_name VARCHAR(200),
    
    -- Capacity
    max_participants INTEGER,
    
    -- Prerequisites
    prerequisites TEXT,
    
    -- Assessment
    has_assessment BOOLEAN DEFAULT false,
    passing_score INTEGER, -- Minimum % to pass
    
    -- Certification
    provides_certification BOOLEAN DEFAULT false,
    certificate_validity_months INTEGER,
    
    -- Cost
    cost_per_participant DECIMAL(12,2),
    currency VARCHAR(3) DEFAULT 'INR',
    
    -- Materials
    course_materials TEXT, -- JSON array of URLs
    
    -- Status
    course_status VARCHAR(30) DEFAULT 'active', -- active, inactive, retired
    
    is_active BOOLEAN DEFAULT true,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE training_requirements (
    requirement_id VARCHAR(50) PRIMARY KEY,
    
    -- Applicability
    requirement_type VARCHAR(30), -- role_based, location_based, regulatory, equipment_based
    
    -- Role-based
    role_id VARCHAR(50), -- FK to job_roles
    
    -- Location-based
    factory_id VARCHAR(50), -- FK to factories
    department_id VARCHAR(50), -- FK to departments
    
    -- Equipment-based
    equipment_type VARCHAR(100), -- Forklift, CNC machine, etc.
    
    -- Training
    course_id VARCHAR(50) NOT NULL, -- FK to training_courses
    
    -- Requirement Details
    is_mandatory BOOLEAN DEFAULT true,
    
    -- Frequency
    frequency VARCHAR(30), -- one_time, annual, biennial, on_change
    validity_months INTEGER, -- How long training is valid
    
    -- Grace Period
    grace_period_days INTEGER DEFAULT 30, -- Days after expiry before compliance issue
    
    -- Compliance Authority
    regulatory_body VARCHAR(200), -- OSHA, EPA, ISO, etc.
    regulation_reference VARCHAR(200),
    
    is_active BOOLEAN DEFAULT true,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE training_schedules (
    schedule_id VARCHAR(50) PRIMARY KEY,
    course_id VARCHAR(50) NOT NULL, -- FK to training_courses
    
    -- Session Details
    session_name VARCHAR(200),
    
    -- Dates & Times
    start_datetime TIMESTAMP NOT NULL,
    end_datetime TIMESTAMP NOT NULL,
    
    -- Location
    factory_id VARCHAR(50), -- FK to factories
    training_location VARCHAR(200), -- Room/building
    is_virtual BOOLEAN DEFAULT false,
    virtual_meeting_url VARCHAR(500),
    
    -- Instructor
    instructor_id VARCHAR(50), -- FK to employees (internal) or external
    instructor_name VARCHAR(200),
    
    -- Capacity
    max_participants INTEGER,
    current_enrollment INTEGER DEFAULT 0,
    
    -- Status
    schedule_status VARCHAR(30) DEFAULT 'scheduled',
    -- scheduled, in_progress, completed, cancelled
    
    -- Completion
    completed_date DATE,
    
    notes TEXT,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE training_enrollments (
    enrollment_id VARCHAR(50) PRIMARY KEY,
    schedule_id VARCHAR(50) NOT NULL, -- FK to training_schedules
    employee_id VARCHAR(50) NOT NULL, -- FK to employees
    
    -- Enrollment
    enrollment_date DATE NOT NULL,
    enrollment_status VARCHAR(30) DEFAULT 'enrolled',
    -- enrolled, waitlisted, confirmed, attended, no_show, cancelled
    
    -- Attendance
    attended BOOLEAN DEFAULT false,
    attendance_date DATE,
    attendance_hours DECIMAL(5,2),
    
    -- Assessment
    assessment_score DECIMAL(5,2), -- Percentage
    passed BOOLEAN,
    
    -- Completion
    completion_status VARCHAR(30), -- in_progress, completed, failed, incomplete
    completion_date DATE,
    
    -- Certificate
    certificate_issued BOOLEAN DEFAULT false,
    certificate_number VARCHAR(100),
    certificate_issue_date DATE,
    certificate_expiry_date DATE,
    certificate_url VARCHAR(500),
    
    -- Feedback
    feedback_rating INTEGER, -- 1-5
    feedback_comments TEXT,
    
    notes TEXT,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(schedule_id, employee_id)
);

CREATE TABLE employee_certifications (
    certification_id VARCHAR(50) PRIMARY KEY,
    employee_id VARCHAR(50) NOT NULL, -- FK to employees
    
    -- Certification Details
    certification_name VARCHAR(200) NOT NULL,
    certification_type VARCHAR(50), -- professional, safety, equipment, regulatory
    
    -- Issuing Body
    issuing_organization VARCHAR(200),
    certification_number VARCHAR(100),
    
    -- Related Training
    training_enrollment_id VARCHAR(50), -- FK to training_enrollments
    
    -- Dates
    issue_date DATE NOT NULL,
    expiry_date DATE,
    
    -- Renewal
    requires_renewal BOOLEAN DEFAULT true,
    renewal_frequency_months INTEGER,
    renewal_grace_period_days INTEGER DEFAULT 30,
    
    -- Status
    certification_status VARCHAR(30) DEFAULT 'active',
    -- active, expired, suspended, revoked
    
    -- Documents
    certificate_file_url VARCHAR(500),
    
    -- Alerts
    expiry_alert_sent BOOLEAN DEFAULT false,
    
    notes TEXT,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- PERFORMANCE MANAGEMENT
-- ============================================================================

CREATE TABLE performance_kpis (
    kpi_id VARCHAR(50) PRIMARY KEY,
    kpi_code VARCHAR(50) UNIQUE NOT NULL,
    kpi_name VARCHAR(200) NOT NULL,
    
    -- Classification
    kpi_category VARCHAR(50), -- productivity, quality, safety, customer_service, financial
    
    -- Applicability
    role_id VARCHAR(50), -- FK to job_roles
    department_id VARCHAR(50), -- FK to departments
    
    -- Measurement
    measurement_unit VARCHAR(50), -- percentage, number, currency, rating
    measurement_frequency VARCHAR(30), -- daily, weekly, monthly, quarterly, annual
    
    -- Targets
    target_value DECIMAL(15,4),
    threshold_value DECIMAL(15,4), -- Minimum acceptable
    
    -- Calculation
    calculation_method TEXT,
    
    -- Weight
    weight_pct DECIMAL(5,2) DEFAULT 100, -- Weight in overall performance
    
    description TEXT,
    
    is_active BOOLEAN DEFAULT true,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE performance_reviews (
    review_id VARCHAR(50) PRIMARY KEY,
    employee_id VARCHAR(50) NOT NULL, -- FK to employees
    
    -- Review Period
    review_type VARCHAR(30), -- annual, mid_year, quarterly, probation
    review_period_start DATE NOT NULL,
    review_period_end DATE NOT NULL,
    
    -- Reviewer
    reviewer_id VARCHAR(50), -- FK to employees (manager)
    review_date DATE,
    
    -- Ratings
    overall_rating DECIMAL(3,2), -- 1.0 to 5.0
    performance_level VARCHAR(30), -- exceeds, meets, needs_improvement, unsatisfactory
    
    -- Competencies
    technical_competency_rating DECIMAL(3,2),
    behavioral_competency_rating DECIMAL(3,2),
    leadership_rating DECIMAL(3,2),
    
    -- Strengths & Areas for Improvement
    key_strengths TEXT,
    areas_for_improvement TEXT,
    
    -- Goals Review
    goals_achieved INTEGER,
    goals_total INTEGER,
    goals_achievement_pct DECIMAL(5,2),
    
    -- Comments
    manager_comments TEXT,
    employee_comments TEXT,
    
    -- Status
    review_status VARCHAR(30) DEFAULT 'draft',
    -- draft, submitted, acknowledged, finalized
    
    -- Employee Acknowledgement
    acknowledged_by_employee BOOLEAN DEFAULT false,
    acknowledged_date DATE,
    
    -- HR Review
    hr_reviewed BOOLEAN DEFAULT false,
    hr_reviewed_by VARCHAR(50),
    hr_reviewed_date DATE,
    
    -- Development Plan
    development_plan TEXT,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE employee_goals (
    goal_id VARCHAR(50) PRIMARY KEY,
    employee_id VARCHAR(50) NOT NULL, -- FK to employees
    
    -- Goal Details
    goal_title VARCHAR(200) NOT NULL,
    goal_description TEXT,
    
    -- SMART Criteria
    is_specific BOOLEAN DEFAULT true,
    is_measurable BOOLEAN DEFAULT true,
    success_criteria TEXT,
    
    -- Dates
    start_date DATE NOT NULL,
    target_date DATE NOT NULL,
    completed_date DATE,
    
    -- Category
    goal_category VARCHAR(50), -- performance, development, project, strategic
    
    -- Progress
    goal_status VARCHAR(30) DEFAULT 'in_progress',
    -- not_started, in_progress, completed, cancelled, deferred
    
    progress_pct INTEGER DEFAULT 0,
    
    -- Weight
    weight_pct DECIMAL(5,2) DEFAULT 100,
    
    -- Review
    linked_to_review_id VARCHAR(50), -- FK to performance_reviews
    
    -- Manager
    set_by_manager_id VARCHAR(50), -- FK to employees
    
    notes TEXT,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- ATTENDANCE & TIME TRACKING
-- ============================================================================

CREATE TABLE shift_schedules (
    shift_id VARCHAR(50) PRIMARY KEY,
    shift_code VARCHAR(50) UNIQUE NOT NULL,
    shift_name VARCHAR(200) NOT NULL,
    
    -- Timing
    start_time TIME NOT NULL,
    end_time TIME NOT NULL,
    
    -- Break Times
    break_duration_minutes INTEGER DEFAULT 30,
    
    -- Shift Type
    shift_type VARCHAR(30), -- day, evening, night, rotating
    
    -- Factory
    factory_id VARCHAR(50), -- FK to factories
    
    is_active BOOLEAN DEFAULT true,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE employee_shifts (
    employee_shift_id VARCHAR(50) PRIMARY KEY,
    employee_id VARCHAR(50) NOT NULL, -- FK to employees
    shift_id VARCHAR(50) NOT NULL, -- FK to shift_schedules
    
    -- Assignment Period
    effective_date DATE NOT NULL,
    end_date DATE,
    
    -- Days of Week
    monday BOOLEAN DEFAULT true,
    tuesday BOOLEAN DEFAULT true,
    wednesday BOOLEAN DEFAULT true,
    thursday BOOLEAN DEFAULT true,
    friday BOOLEAN DEFAULT true,
    saturday BOOLEAN DEFAULT false,
    sunday BOOLEAN DEFAULT false,
    
    is_active BOOLEAN DEFAULT true,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE attendance_records (
    attendance_id VARCHAR(50) PRIMARY KEY,
    employee_id VARCHAR(50) NOT NULL, -- FK to employees
    
    -- Date
    attendance_date DATE NOT NULL,
    
    -- Shift
    shift_id VARCHAR(50), -- FK to shift_schedules
    
    -- Clock In/Out
    clock_in_time TIMESTAMP,
    clock_out_time TIMESTAMP,
    
    -- Location
    clock_in_location VARCHAR(200),
    clock_out_location VARCHAR(200),
    
    -- Hours
    scheduled_hours DECIMAL(5,2),
    actual_hours DECIMAL(5,2),
    regular_hours DECIMAL(5,2),
    overtime_hours DECIMAL(5,2),
    
    -- Status
    attendance_status VARCHAR(30),
    -- present, absent, late, half_day, on_leave, holiday, weekend
    
    -- Late/Early
    late_minutes INTEGER DEFAULT 0,
    early_departure_minutes INTEGER DEFAULT 0,
    
    -- Approval
    overtime_approved BOOLEAN DEFAULT false,
    approved_by VARCHAR(50),
    
    notes TEXT,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(employee_id, attendance_date)
);

-- ============================================================================
-- LEAVE MANAGEMENT
-- ============================================================================

CREATE TABLE leave_types (
    leave_type_id VARCHAR(50) PRIMARY KEY,
    leave_type_code VARCHAR(50) UNIQUE NOT NULL,
    leave_type_name VARCHAR(200) NOT NULL,
    
    -- Classification
    leave_category VARCHAR(50), -- paid, unpaid, statutory
    
    -- Accrual
    accrual_enabled BOOLEAN DEFAULT true,
    accrual_frequency VARCHAR(30), -- monthly, annual
    accrual_rate DECIMAL(5,2), -- Days per period
    
    -- Maximum
    max_days_per_year DECIMAL(5,2),
    max_carry_forward DECIMAL(5,2), -- Max days to carry to next year
    
    -- Minimum & Maximum per request
    min_days_per_request DECIMAL(5,2) DEFAULT 0.5,
    max_days_per_request DECIMAL(5,2),
    
    -- Notice Period
    min_notice_days INTEGER DEFAULT 7, -- Days of advance notice required
    
    -- Requires Approval
    requires_approval BOOLEAN DEFAULT true,
    
    -- Gender-specific
    applicable_gender VARCHAR(20), -- all, male, female
    
    -- Documents
    requires_documentation BOOLEAN DEFAULT false,
    
    is_active BOOLEAN DEFAULT true,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE employee_leave_balances (
    balance_id VARCHAR(50) PRIMARY KEY,
    employee_id VARCHAR(50) NOT NULL, -- FK to employees
    leave_type_id VARCHAR(50) NOT NULL, -- FK to leave_types
    
    -- Year
    leave_year INTEGER NOT NULL,
    
    -- Balance
    opening_balance DECIMAL(5,2) DEFAULT 0,
    accrued_days DECIMAL(5,2) DEFAULT 0,
    used_days DECIMAL(5,2) DEFAULT 0,
    pending_days DECIMAL(5,2) DEFAULT 0,
    available_balance DECIMAL(5,2) DEFAULT 0,
    
    -- Carry Forward
    carry_forward_from_previous_year DECIMAL(5,2) DEFAULT 0,
    
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(employee_id, leave_type_id, leave_year)
);

CREATE TABLE leave_requests (
    request_id VARCHAR(50) PRIMARY KEY,
    employee_id VARCHAR(50) NOT NULL, -- FK to employees
    leave_type_id VARCHAR(50) NOT NULL, -- FK to leave_types
    
    -- Request Details
    request_date DATE NOT NULL,
    
    -- Leave Period
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    total_days DECIMAL(5,2) NOT NULL,
    
    -- Half Day
    is_half_day BOOLEAN DEFAULT false,
    half_day_session VARCHAR(10), -- morning, afternoon
    
    -- Reason
    reason TEXT,
    
    -- Documents
    supporting_document_url VARCHAR(500),
    
    -- Status
    request_status VARCHAR(30) DEFAULT 'pending',
    -- pending, approved, rejected, cancelled, withdrawn
    
    -- Approval Workflow
    approved_by VARCHAR(50), -- FK to employees (manager)
    approval_date DATE,
    rejection_reason TEXT,
    
    -- HR Approval (if required)
    hr_approved BOOLEAN DEFAULT false,
    hr_approved_by VARCHAR(50),
    hr_approval_date DATE,
    
    -- Cancellation
    cancelled BOOLEAN DEFAULT false,
    cancelled_date DATE,
    cancellation_reason TEXT,
    
    notes TEXT,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- ONBOARDING & OFFBOARDING
-- ============================================================================

CREATE TABLE onboarding_checklists (
    checklist_id VARCHAR(50) PRIMARY KEY,
    checklist_code VARCHAR(50) UNIQUE NOT NULL,
    checklist_name VARCHAR(200) NOT NULL,
    
    -- Applicability
    role_id VARCHAR(50), -- FK to job_roles
    department_id VARCHAR(50), -- FK to departments
    
    -- Description
    description TEXT,
    
    is_active BOOLEAN DEFAULT true,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE onboarding_checklist_items (
    item_id VARCHAR(50) PRIMARY KEY,
    checklist_id VARCHAR(50) NOT NULL, -- FK to onboarding_checklists
    
    -- Item Details
    item_number INTEGER,
    item_title VARCHAR(200) NOT NULL,
    item_description TEXT,
    
    -- Category
    item_category VARCHAR(50), -- documentation, it_setup, facility_access, training, orientation
    
    -- Responsible Party
    responsible_party VARCHAR(50), -- hr, it, manager, facilities
    
    -- Timeline
    due_days_from_hire INTEGER, -- Days after hire date
    
    -- Required
    is_mandatory BOOLEAN DEFAULT true,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE employee_onboarding (
    onboarding_id VARCHAR(50) PRIMARY KEY,
    employee_id VARCHAR(50) NOT NULL, -- FK to employees
    checklist_id VARCHAR(50) NOT NULL, -- FK to onboarding_checklists
    
    -- Start
    onboarding_start_date DATE NOT NULL,
    
    -- Status
    onboarding_status VARCHAR(30) DEFAULT 'in_progress',
    -- not_started, in_progress, completed
    
    completion_date DATE,
    
    -- Progress
    total_items INTEGER,
    completed_items INTEGER,
    completion_pct DECIMAL(5,2),
    
    -- Coordinator
    hr_coordinator_id VARCHAR(50), -- FK to employees
    
    notes TEXT,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(employee_id, checklist_id)
);

CREATE TABLE employee_onboarding_items (
    item_tracking_id VARCHAR(50) PRIMARY KEY,
    onboarding_id VARCHAR(50) NOT NULL, -- FK to employee_onboarding
    item_id VARCHAR(50) NOT NULL, -- FK to onboarding_checklist_items
    
    -- Status
    item_status VARCHAR(30) DEFAULT 'pending',
    -- pending, in_progress, completed, not_applicable, waived
    
    -- Due Date
    due_date DATE,
    
    -- Completion
    completed BOOLEAN DEFAULT false,
    completed_date DATE,
    completed_by VARCHAR(50), -- FK to employees
    
    -- Notes
    notes TEXT,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(onboarding_id, item_id)
);

CREATE TABLE offboarding_records (
    offboarding_id VARCHAR(50) PRIMARY KEY,
    employee_id VARCHAR(50) NOT NULL, -- FK to employees
    
    -- Exit Details
    last_working_date DATE NOT NULL,
    exit_type VARCHAR(50), -- resignation, termination, retirement, contract_end
    exit_reason VARCHAR(200),
    
    -- Notice Period
    notice_period_days INTEGER,
    notice_given_date DATE,
    
    -- Clearance
    clearance_status VARCHAR(30) DEFAULT 'pending',
    -- pending, in_progress, completed
    
    it_clearance BOOLEAN DEFAULT false,
    facility_clearance BOOLEAN DEFAULT false,
    finance_clearance BOOLEAN DEFAULT false,
    hr_clearance BOOLEAN DEFAULT false,
    
    -- Exit Interview
    exit_interview_conducted BOOLEAN DEFAULT false,
    exit_interview_date DATE,
    exit_interview_feedback TEXT,
    
    -- Rehire Eligibility
    eligible_for_rehire BOOLEAN DEFAULT true,
    
    -- Documents
    resignation_letter_url VARCHAR(500),
    full_and_final_settlement_url VARCHAR(500),
    
    notes TEXT,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- CAREER DEVELOPMENT & SUCCESSION
-- ============================================================================

CREATE TABLE career_paths (
    path_id VARCHAR(50) PRIMARY KEY,
    path_code VARCHAR(50) UNIQUE NOT NULL,
    path_name VARCHAR(200) NOT NULL,
    
    -- From Role
    from_role_id VARCHAR(50) NOT NULL, -- FK to job_roles
    
    -- To Role
    to_role_id VARCHAR(50) NOT NULL, -- FK to job_roles
    
    -- Path Type
    path_type VARCHAR(30), -- promotion, lateral, specialization
    
    -- Typical Timeline
    typical_time_years DECIMAL(5,2),
    
    -- Requirements
    required_skills TEXT, -- JSON array of skill_ids
    required_certifications TEXT,
    min_performance_rating DECIMAL(3,2),
    
    -- Description
    description TEXT,
    
    is_active BOOLEAN DEFAULT true,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE succession_planning (
    succession_id VARCHAR(50) PRIMARY KEY,
    
    -- Critical Position
    position_id VARCHAR(50) NOT NULL, -- FK to positions
    current_incumbent_id VARCHAR(50), -- FK to employees
    
    -- Risk
    succession_risk VARCHAR(30), -- high, medium, low
    
    -- Timeline
    expected_vacancy_date DATE,
    
    -- Readiness
    successor_ready BOOLEAN DEFAULT false,
    
    -- Development Plan
    development_plan TEXT,
    
    notes TEXT,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE succession_candidates (
    candidate_id VARCHAR(50) PRIMARY KEY,
    succession_id VARCHAR(50) NOT NULL, -- FK to succession_planning
    employee_id VARCHAR(50) NOT NULL, -- FK to employees
    
    -- Readiness
    readiness_level VARCHAR(30), -- ready_now, ready_1_year, ready_2_years
    
    -- Strengths & Gaps
    strengths TEXT,
    development_needs TEXT,
    
    -- Development Plan
    individual_development_plan TEXT,
    
    -- Assessment
    last_assessment_date DATE,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(succession_id, employee_id)
);

-- ============================================================================
-- SAFETY & COMPLIANCE
-- ============================================================================

CREATE TABLE safety_incidents (
    incident_id VARCHAR(50) PRIMARY KEY,
    incident_number VARCHAR(50) UNIQUE NOT NULL,
    
    -- Employee
    employee_id VARCHAR(50), -- FK to employees (if employee-related)
    
    -- Incident Details
    incident_date DATE NOT NULL,
    incident_time TIME,
    
    -- Location
    factory_id VARCHAR(50), -- FK to factories
    department_id VARCHAR(50), -- FK to departments
    incident_location VARCHAR(200),
    
    -- Classification
    incident_type VARCHAR(50), -- injury, near_miss, property_damage, environmental
    severity VARCHAR(30), -- minor, moderate, serious, fatal
    
    -- Description
    description TEXT NOT NULL,
    immediate_cause TEXT,
    root_cause TEXT,
    
    -- Injury Details (if applicable)
    injury_type VARCHAR(50),
    body_part_affected VARCHAR(100),
    medical_treatment_required BOOLEAN DEFAULT false,
    days_away_from_work INTEGER DEFAULT 0,
    
    -- Investigation
    investigation_status VARCHAR(30) DEFAULT 'pending',
    -- pending, in_progress, completed
    
    investigated_by VARCHAR(50), -- FK to employees
    investigation_date DATE,
    investigation_findings TEXT,
    
    -- Corrective Actions
    corrective_actions TEXT,
    preventive_measures TEXT,
    
    -- OSHA Recordable
    osha_recordable BOOLEAN DEFAULT false,
    
    -- Status
    incident_status VARCHAR(30) DEFAULT 'open',
    -- open, under_investigation, closed
    
    closed_date DATE,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE ppe_requirements (
    ppe_requirement_id VARCHAR(50) PRIMARY KEY,
    
    -- Applicability
    factory_id VARCHAR(50), -- FK to factories
    department_id VARCHAR(50), -- FK to departments
    job_role_id VARCHAR(50), -- FK to job_roles
    
    -- PPE Items
    ppe_items TEXT, -- JSON array: safety_helmet, safety_shoes, gloves, goggles, etc.
    
    -- Description
    description TEXT,
    
    is_active BOOLEAN DEFAULT true,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- HR INTEGRATION LOG
-- ============================================================================

CREATE TABLE hcm_integration_log (
    log_id VARCHAR(50) PRIMARY KEY,
    log_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Integration Direction
    integration_direction VARCHAR(30),
    -- HCM_TO_CRM, HCM_TO_CMMS, HCM_TO_MES, HCM_TO_SERVICE,
    -- CRM_TO_HCM, CMMS_TO_HCM, etc.
    
    -- Document Type
    document_type VARCHAR(50),
    -- employee, training, certification, attendance
    
    document_id VARCHAR(50),
    
    -- Target System
    target_system VARCHAR(50), -- CRM, CMMS, MES, SERVICE, PAYROLL
    
    -- Status
    integration_status VARCHAR(30), -- pending, in_progress, completed, error
    error_message TEXT,
    
    -- Data
    integration_data JSONB,
    
    -- Retry
    retry_count INTEGER DEFAULT 0,
    last_retry_at TIMESTAMP
);

-- ============================================================================
-- INDICES FOR PERFORMANCE
-- ============================================================================

-- Employees
CREATE INDEX idx_employees_status ON employees(employment_status, is_active);
CREATE INDEX idx_employees_dept ON employees(primary_department_id, employment_status);
CREATE INDEX idx_employees_factory ON employees(primary_factory_id, employment_status);
CREATE INDEX idx_employees_manager ON employees(reports_to_employee_id);
CREATE INDEX idx_employees_hire_date ON employees(hire_date);
CREATE INDEX idx_employee_history_emp ON employee_employment_history(employee_id, effective_date);

-- Organization
CREATE INDEX idx_departments_parent ON departments(parent_department_id);
CREATE INDEX idx_departments_factory ON departments(factory_id, is_active);
CREATE INDEX idx_positions_role ON positions(role_id, position_status);
CREATE INDEX idx_positions_dept ON positions(department_id, position_status);
CREATE INDEX idx_positions_employee ON positions(employee_id);

-- Skills
CREATE INDEX idx_employee_skills_emp ON employee_skills(employee_id, proficiency_level);
CREATE INDEX idx_employee_skills_skill ON employee_skills(skill_id);
CREATE INDEX idx_role_skills_role ON role_skill_requirements(role_id);

-- Training
CREATE INDEX idx_training_courses_category ON training_courses(course_category, is_active);
CREATE INDEX idx_training_requirements_role ON training_requirements(role_id, is_mandatory);
CREATE INDEX idx_training_requirements_factory ON training_requirements(factory_id);
CREATE INDEX idx_training_schedules_course ON training_schedules(course_id, start_datetime);
CREATE INDEX idx_training_schedules_status ON training_schedules(schedule_status);
CREATE INDEX idx_training_enrollments_schedule ON training_enrollments(schedule_id);
CREATE INDEX idx_training_enrollments_emp ON training_enrollments(employee_id, completion_status);
CREATE INDEX idx_certifications_emp ON employee_certifications(employee_id, certification_status);
CREATE INDEX idx_certifications_expiry ON employee_certifications(expiry_date, certification_status);

-- Performance
CREATE INDEX idx_reviews_employee ON performance_reviews(employee_id, review_date);
CREATE INDEX idx_reviews_reviewer ON performance_reviews(reviewer_id);
CREATE INDEX idx_goals_employee ON employee_goals(employee_id, goal_status);

-- Attendance
CREATE INDEX idx_attendance_emp ON attendance_records(employee_id, attendance_date);
CREATE INDEX idx_attendance_date ON attendance_records(attendance_date);
CREATE INDEX idx_employee_shifts_emp ON employee_shifts(employee_id, is_active);

-- Leave
CREATE INDEX idx_leave_balances_emp ON employee_leave_balances(employee_id, leave_year);
CREATE INDEX idx_leave_requests_emp ON leave_requests(employee_id, request_status);
CREATE INDEX idx_leave_requests_status ON leave_requests(request_status, start_date);

-- Onboarding
CREATE INDEX idx_employee_onboarding_emp ON employee_onboarding(employee_id, onboarding_status);
CREATE INDEX idx_onboarding_items_onb ON employee_onboarding_items(onboarding_id, item_status);
CREATE INDEX idx_offboarding_emp ON offboarding_records(employee_id);

-- Career & Succession
CREATE INDEX idx_career_paths_from ON career_paths(from_role_id);
CREATE INDEX idx_career_paths_to ON career_paths(to_role_id);
CREATE INDEX idx_succession_position ON succession_planning(position_id);
CREATE INDEX idx_succession_candidates_emp ON succession_candidates(employee_id);

-- Safety
CREATE INDEX idx_safety_incidents_emp ON safety_incidents(employee_id, incident_date);
CREATE INDEX idx_safety_incidents_factory ON safety_incidents(factory_id, incident_date);
CREATE INDEX idx_safety_incidents_status ON safety_incidents(incident_status);

-- Integration
CREATE INDEX idx_hcm_integration_status ON hcm_integration_log(integration_status, log_timestamp);

-- ============================================================================
-- COMMENTS
-- ============================================================================

COMMENT ON TABLE employees IS 'Central employee master data with personal and employment details';
COMMENT ON TABLE departments IS 'Organizational departments with hierarchy';
COMMENT ON TABLE job_roles IS 'Job role definitions with requirements';
COMMENT ON TABLE positions IS 'Budgeted positions mapped to roles and departments';
COMMENT ON TABLE skills_catalog IS 'Master list of skills and competencies';
COMMENT ON TABLE employee_skills IS 'Employee skill inventory with proficiency levels';
COMMENT ON TABLE training_courses IS 'Training course catalog';
COMMENT ON TABLE training_requirements IS 'Mandatory training by role, location, equipment';
COMMENT ON TABLE training_enrollments IS 'Employee training attendance and completion';
COMMENT ON TABLE employee_certifications IS 'Professional certifications with expiry tracking';
COMMENT ON TABLE performance_reviews IS 'Annual and periodic performance evaluations';
COMMENT ON TABLE attendance_records IS 'Daily attendance with clock in/out times';
COMMENT ON TABLE leave_requests IS 'Employee leave applications and approvals';
COMMENT ON TABLE employee_onboarding IS 'New hire onboarding checklist tracking';
COMMENT ON TABLE succession_planning IS 'Critical position succession planning';
COMMENT ON TABLE safety_incidents IS 'Workplace safety incidents and investigations';
COMMENT ON TABLE hcm_integration_log IS 'Integration tracking with other systems';
