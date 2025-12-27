-- ============================================================================
-- GenIMS MySQL Audit Schema
-- 30 Tables for Compliance, Legal Hold, and Data Change Tracking
-- Refresh: Real-time from PostgreSQL triggers
-- Retention: 7-year immutable archive with partitioning
-- ============================================================================

SET SESSION sql_mode='STRICT_TRANS_TABLES';
SET SESSION time_zone='+00:00';

-- ============================================================================
-- SYSTEM AUDIT TABLES (10 tables)
-- ============================================================================

-- System Audit Log (All Changes, User, Timestamp)
CREATE TABLE IF NOT EXISTS system_audit_log (
    audit_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    audit_sequence BIGINT UNIQUE NOT NULL,  -- Never reused, for gap detection
    
    audit_timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    audit_date DATE NOT NULL,
    audit_hour INT NOT NULL,
    
    user_id INT,
    username VARCHAR(100),
    user_role VARCHAR(100),
    
    action_type ENUM('INSERT', 'UPDATE', 'DELETE', 'CREATE', 'DROP', 'ALTER', 'TRUNCATE'),
    object_type VARCHAR(100),  -- table/view/procedure/function
    object_name VARCHAR(255),
    object_schema VARCHAR(100),
    
    -- Source system
    source_system VARCHAR(100),  -- PostgreSQL, Application, API
    
    -- Session info
    session_id VARCHAR(255),
    ip_address VARCHAR(45),
    application_name VARCHAR(100),
    
    -- Record counts
    affected_rows INT,
    
    -- Error tracking
    error_code VARCHAR(100),
    error_message TEXT,
    
    -- Status
    audit_status ENUM('Success', 'Error', 'Rollback'),
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    KEY idx_audit_date (audit_date, audit_hour),
    KEY idx_user (user_id, audit_timestamp),
    KEY idx_action (action_type, audit_timestamp),
    KEY idx_object (object_name, audit_timestamp),
    KEY idx_sequence (audit_sequence),
    CONSTRAINT uk_sequence UNIQUE KEY (audit_sequence)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
PARTITION BY RANGE (YEAR(audit_timestamp)) (
    PARTITION p2024 VALUES LESS THAN (2025),
    PARTITION p2025 VALUES LESS THAN (2026),
    PARTITION p2026 VALUES LESS THAN (2027),
    PARTITION p2027 VALUES LESS THAN (2028),
    PARTITION p2028 VALUES LESS THAN (2029),
    PARTITION p2029 VALUES LESS THAN (2030),
    PARTITION p2030 VALUES LESS THAN (2031),
    PARTITION p2031 VALUES LESS THAN (2032)
);

-- User Activity Log
CREATE TABLE IF NOT EXISTS user_activity_log (
    activity_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    activity_sequence BIGINT UNIQUE NOT NULL,
    
    activity_timestamp TIMESTAMP NOT NULL,
    activity_date DATE NOT NULL,
    
    user_id INT NOT NULL,
    username VARCHAR(100),
    user_role VARCHAR(100),
    
    activity_type ENUM('Login', 'Logout', 'Read', 'Write', 'Delete', 'Export', 'Report'),
    activity_description VARCHAR(255),
    
    resource_type VARCHAR(100),
    resource_id BIGINT,
    resource_name VARCHAR(255),
    
    session_id VARCHAR(255),
    ip_address VARCHAR(45),
    device_info VARCHAR(255),
    
    -- Result
    status ENUM('Success', 'Failed', 'Denied'),
    failure_reason VARCHAR(255),
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    KEY idx_user_date (user_id, activity_date),
    KEY idx_activity_type (activity_type, activity_timestamp),
    KEY idx_timestamp (activity_timestamp),
    KEY idx_sequence (activity_sequence),
    CONSTRAINT uk_activity_sequence UNIQUE KEY (activity_sequence)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
PARTITION BY RANGE (YEAR(activity_timestamp)) (
    PARTITION p2024 VALUES LESS THAN (2025),
    PARTITION p2025 VALUES LESS THAN (2026),
    PARTITION p2026 VALUES LESS THAN (2027),
    PARTITION p2027 VALUES LESS THAN (2028),
    PARTITION p2028 VALUES LESS THAN (2029),
    PARTITION p2029 VALUES LESS THAN (2030),
    PARTITION p2030 VALUES LESS THAN (2031),
    PARTITION p2031 VALUES LESS THAN (2032)
);

-- Login Audit
CREATE TABLE IF NOT EXISTS login_audit (
    login_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    login_sequence BIGINT UNIQUE NOT NULL,
    
    user_id INT NOT NULL,
    username VARCHAR(100),
    
    login_timestamp TIMESTAMP NOT NULL,
    login_date DATE NOT NULL,
    logout_timestamp TIMESTAMP,
    
    login_status ENUM('Success', 'Failed'),
    failure_reason VARCHAR(255),
    
    ip_address VARCHAR(45),
    device_id VARCHAR(255),
    device_name VARCHAR(255),
    device_os VARCHAR(100),
    device_browser VARCHAR(100),
    
    location VARCHAR(255),
    
    session_duration_minutes INT,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    KEY idx_user_date (user_id, login_date),
    KEY idx_timestamp (login_timestamp),
    KEY idx_sequence (login_sequence)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
PARTITION BY RANGE (YEAR(login_timestamp)) (
    PARTITION p2024 VALUES LESS THAN (2025),
    PARTITION p2025 VALUES LESS THAN (2026),
    PARTITION p2026 VALUES LESS THAN (2027),
    PARTITION p2027 VALUES LESS THAN (2028),
    PARTITION p2028 VALUES LESS THAN (2029),
    PARTITION p2029 VALUES LESS THAN (2030),
    PARTITION p2030 VALUES LESS THAN (2031),
    PARTITION p2031 VALUES LESS THAN (2032)
);

-- Database Changes
CREATE TABLE IF NOT EXISTS database_changes (
    db_change_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    db_change_sequence BIGINT UNIQUE NOT NULL,
    
    change_timestamp TIMESTAMP NOT NULL,
    change_date DATE NOT NULL,
    
    user_id INT,
    username VARCHAR(100),
    
    database_name VARCHAR(100),
    change_type ENUM('DDL', 'Backup', 'Restore', 'Permission', 'Configuration'),
    
    -- DDL details
    ddl_statement TEXT,  -- CREATE, ALTER, DROP
    object_type VARCHAR(100),
    object_name VARCHAR(255),
    
    -- Before/after
    status ENUM('Success', 'Failed'),
    error_message TEXT,
    
    execution_time_seconds DECIMAL(10,3),
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    KEY idx_database_date (database_name, change_date),
    KEY idx_user_date (user_id, change_date),
    KEY idx_timestamp (change_timestamp),
    KEY idx_sequence (db_change_sequence)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
PARTITION BY RANGE (YEAR(change_timestamp)) (
    PARTITION p2024 VALUES LESS THAN (2025),
    PARTITION p2025 VALUES LESS THAN (2026),
    PARTITION p2026 VALUES LESS THAN (2027),
    PARTITION p2027 VALUES LESS THAN (2028),
    PARTITION p2028 VALUES LESS THAN (2029),
    PARTITION p2029 VALUES LESS THAN (2030),
    PARTITION p2030 VALUES LESS THAN (2031),
    PARTITION p2031 VALUES LESS THAN (2032)
);

-- Permission Changes
CREATE TABLE IF NOT EXISTS permission_changes (
    permission_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    permission_sequence BIGINT UNIQUE NOT NULL,
    
    change_timestamp TIMESTAMP NOT NULL,
    change_date DATE NOT NULL,
    
    user_id INT NOT NULL,
    username VARCHAR(100),
    
    modified_by INT,
    modified_by_username VARCHAR(100),
    
    permission_type VARCHAR(100),
    permission_resource VARCHAR(255),
    
    old_permission VARCHAR(100),
    new_permission VARCHAR(100),
    
    reason VARCHAR(255),
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    KEY idx_user_date (user_id, change_date),
    KEY idx_timestamp (change_timestamp),
    KEY idx_sequence (permission_sequence)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
PARTITION BY RANGE (YEAR(change_timestamp)) (
    PARTITION p2024 VALUES LESS THAN (2025),
    PARTITION p2025 VALUES LESS THAN (2026),
    PARTITION p2026 VALUES LESS THAN (2027),
    PARTITION p2027 VALUES LESS THAN (2028),
    PARTITION p2028 VALUES LESS THAN (2029),
    PARTITION p2029 VALUES LESS THAN (2030),
    PARTITION p2030 VALUES LESS THAN (2031),
    PARTITION p2031 VALUES LESS THAN (2032)
);

-- Configuration Changes
CREATE TABLE IF NOT EXISTS configuration_changes (
    config_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    config_sequence BIGINT UNIQUE NOT NULL,
    
    change_timestamp TIMESTAMP NOT NULL,
    change_date DATE NOT NULL,
    
    config_module VARCHAR(100),
    config_key VARCHAR(255),
    
    old_value TEXT,
    new_value TEXT,
    
    changed_by INT,
    changed_by_username VARCHAR(100),
    
    approval_required BOOLEAN,
    approval_by INT,
    approval_timestamp TIMESTAMP,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    KEY idx_config_module (config_module, change_date),
    KEY idx_timestamp (change_timestamp),
    KEY idx_sequence (config_sequence)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
PARTITION BY RANGE (YEAR(change_timestamp)) (
    PARTITION p2024 VALUES LESS THAN (2025),
    PARTITION p2025 VALUES LESS THAN (2026),
    PARTITION p2026 VALUES LESS THAN (2027),
    PARTITION p2027 VALUES LESS THAN (2028),
    PARTITION p2028 VALUES LESS THAN (2029),
    PARTITION p2029 VALUES LESS THAN (2030),
    PARTITION p2030 VALUES LESS THAN (2031),
    PARTITION p2031 VALUES LESS THAN (2032)
);

-- Security Events
CREATE TABLE IF NOT EXISTS security_events (
    event_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    event_sequence BIGINT UNIQUE NOT NULL,
    
    event_timestamp TIMESTAMP NOT NULL,
    event_date DATE NOT NULL,
    
    event_type ENUM('Failed Login', 'Unauthorized Access', 'Permission Violation', 'Data Export', 'Suspicious Activity'),
    event_severity ENUM('Critical', 'High', 'Medium', 'Low'),
    
    user_id INT,
    username VARCHAR(100),
    
    resource_type VARCHAR(100),
    resource_name VARCHAR(255),
    
    description TEXT,
    ip_address VARCHAR(45),
    
    action_taken VARCHAR(255),
    action_by INT,
    action_timestamp TIMESTAMP,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    KEY idx_severity_date (event_severity, event_date),
    KEY idx_user_date (user_id, event_date),
    KEY idx_timestamp (event_timestamp),
    KEY idx_sequence (event_sequence)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
PARTITION BY RANGE (YEAR(event_timestamp)) (
    PARTITION p2024 VALUES LESS THAN (2025),
    PARTITION p2025 VALUES LESS THAN (2026),
    PARTITION p2026 VALUES LESS THAN (2027),
    PARTITION p2027 VALUES LESS THAN (2028),
    PARTITION p2028 VALUES LESS THAN (2029),
    PARTITION p2029 VALUES LESS THAN (2030),
    PARTITION p2030 VALUES LESS THAN (2031),
    PARTITION p2031 VALUES LESS THAN (2032)
);

-- Backup & Recovery
CREATE TABLE IF NOT EXISTS backup_recovery (
    backup_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    backup_sequence BIGINT UNIQUE NOT NULL,
    
    backup_timestamp TIMESTAMP NOT NULL,
    backup_date DATE NOT NULL,
    
    database_name VARCHAR(100),
    backup_type ENUM('Full', 'Incremental', 'Differential'),
    
    backup_location VARCHAR(255),
    backup_size_bytes BIGINT,
    
    backup_duration_minutes INT,
    
    initiated_by INT,
    initiated_by_username VARCHAR(100),
    
    backup_status ENUM('Success', 'Failed', 'Partial'),
    error_message TEXT,
    
    -- Recovery info
    recovery_attempted BOOLEAN,
    recovery_timestamp TIMESTAMP,
    recovery_status ENUM('Success', 'Failed', 'In Progress'),
    recovery_by INT,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    KEY idx_database_date (database_name, backup_date),
    KEY idx_status (backup_status, backup_date),
    KEY idx_sequence (backup_sequence)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
PARTITION BY RANGE (YEAR(backup_timestamp)) (
    PARTITION p2024 VALUES LESS THAN (2025),
    PARTITION p2025 VALUES LESS THAN (2026),
    PARTITION p2026 VALUES LESS THAN (2027),
    PARTITION p2027 VALUES LESS THAN (2028),
    PARTITION p2028 VALUES LESS THAN (2029),
    PARTITION p2029 VALUES LESS THAN (2030),
    PARTITION p2030 VALUES LESS THAN (2031),
    PARTITION p2031 VALUES LESS THAN (2032)
);

-- ============================================================================
-- DATA CHANGE AUDIT TABLES (8 tables)
-- ============================================================================

-- Data Change Audit (Before/After Values)
CREATE TABLE IF NOT EXISTS data_change_audit (
    change_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    change_sequence BIGINT UNIQUE NOT NULL,
    
    change_timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    change_date DATE NOT NULL,
    
    -- Source
    source_table VARCHAR(100),
    record_id BIGINT,
    
    -- Change details
    change_type ENUM('INSERT', 'UPDATE', 'DELETE'),
    column_name VARCHAR(100),
    
    old_value TEXT,
    new_value TEXT,
    
    -- Changed by
    user_id INT,
    username VARCHAR(100),
    
    -- Linked to system audit
    system_audit_id BIGINT,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    KEY idx_table_date (source_table, change_date),
    KEY idx_record (record_id, change_timestamp),
    KEY idx_user_date (user_id, change_date),
    KEY idx_sequence (change_sequence),
    KEY idx_change_type (change_type, change_timestamp)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
PARTITION BY RANGE (YEAR(change_timestamp)) (
    PARTITION p2024 VALUES LESS THAN (2025),
    PARTITION p2025 VALUES LESS THAN (2026),
    PARTITION p2026 VALUES LESS THAN (2027),
    PARTITION p2027 VALUES LESS THAN (2028),
    PARTITION p2028 VALUES LESS THAN (2029),
    PARTITION p2029 VALUES LESS THAN (2030),
    PARTITION p2030 VALUES LESS THAN (2031),
    PARTITION p2031 VALUES LESS THAN (2032)
);

-- Bulk Operation Audit
CREATE TABLE IF NOT EXISTS bulk_operation_audit (
    bulk_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    bulk_sequence BIGINT UNIQUE NOT NULL,
    
    operation_timestamp TIMESTAMP NOT NULL,
    operation_date DATE NOT NULL,
    
    operation_type ENUM('Bulk Update', 'Bulk Delete', 'Bulk Insert', 'Bulk Import'),
    target_table VARCHAR(100),
    
    records_affected INT,
    records_processed INT,
    records_failed INT,
    
    executed_by INT,
    executed_by_username VARCHAR(100),
    
    -- SQL
    bulk_sql_statement TEXT,
    
    execution_time_seconds DECIMAL(10,3),
    
    status ENUM('Success', 'Failed', 'Partial'),
    error_details TEXT,
    
    approved_by INT,
    approval_timestamp TIMESTAMP,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    KEY idx_table_date (target_table, operation_date),
    KEY idx_user_date (executed_by, operation_date),
    KEY idx_sequence (bulk_sequence)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
PARTITION BY RANGE (YEAR(operation_timestamp)) (
    PARTITION p2024 VALUES LESS THAN (2025),
    PARTITION p2025 VALUES LESS THAN (2026),
    PARTITION p2026 VALUES LESS THAN (2027),
    PARTITION p2027 VALUES LESS THAN (2028),
    PARTITION p2028 VALUES LESS THAN (2029),
    PARTITION p2029 VALUES LESS THAN (2030),
    PARTITION p2030 VALUES LESS THAN (2031),
    PARTITION p2031 VALUES LESS THAN (2032)
);

-- Financial Data Changes (Critical)
CREATE TABLE IF NOT EXISTS financial_data_changes (
    financial_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    financial_sequence BIGINT UNIQUE NOT NULL,
    
    change_timestamp TIMESTAMP NOT NULL,
    change_date DATE NOT NULL,
    
    transaction_type VARCHAR(100),
    transaction_amount DECIMAL(14,2),
    
    old_amount DECIMAL(14,2),
    new_amount DECIMAL(14,2),
    amount_difference DECIMAL(14,2),
    
    changed_by INT,
    changed_by_username VARCHAR(100),
    
    reason_code VARCHAR(100),
    reason_description VARCHAR(255),
    
    approval_required BOOLEAN,
    approved_by INT,
    approval_timestamp TIMESTAMP,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    KEY idx_date (change_date),
    KEY idx_user_date (changed_by, change_date),
    KEY idx_amount (amount_difference, change_date),
    KEY idx_sequence (financial_sequence)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
PARTITION BY RANGE (YEAR(change_timestamp)) (
    PARTITION p2024 VALUES LESS THAN (2025),
    PARTITION p2025 VALUES LESS THAN (2026),
    PARTITION p2026 VALUES LESS THAN (2027),
    PARTITION p2027 VALUES LESS THAN (2028),
    PARTITION p2028 VALUES LESS THAN (2029),
    PARTITION p2029 VALUES LESS THAN (2030),
    PARTITION p2030 VALUES LESS THAN (2031),
    PARTITION p2031 VALUES LESS THAN (2032)
);

-- Master Data Changes
CREATE TABLE IF NOT EXISTS master_data_changes (
    master_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    master_sequence BIGINT UNIQUE NOT NULL,
    
    change_timestamp TIMESTAMP NOT NULL,
    change_date DATE NOT NULL,
    
    entity_type VARCHAR(100),  -- Product, Customer, Supplier, Employee
    entity_id INT,
    entity_name VARCHAR(255),
    
    change_type ENUM('CREATE', 'UPDATE', 'DELETE', 'Reactivate'),
    
    old_values JSON,
    new_values JSON,
    
    changed_by INT,
    changed_by_username VARCHAR(100),
    
    business_justification VARCHAR(255),
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    KEY idx_entity_date (entity_type, change_date),
    KEY idx_user_date (changed_by, change_date),
    KEY idx_sequence (master_sequence)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
PARTITION BY RANGE (YEAR(change_timestamp)) (
    PARTITION p2024 VALUES LESS THAN (2025),
    PARTITION p2025 VALUES LESS THAN (2026),
    PARTITION p2026 VALUES LESS THAN (2027),
    PARTITION p2027 VALUES LESS THAN (2028),
    PARTITION p2028 VALUES LESS THAN (2029),
    PARTITION p2029 VALUES LESS THAN (2030),
    PARTITION p2030 VALUES LESS THAN (2031),
    PARTITION p2031 VALUES LESS THAN (2032)
);

-- Price & Cost Changes
CREATE TABLE IF NOT EXISTS price_cost_changes (
    price_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    price_sequence BIGINT UNIQUE NOT NULL,
    
    change_timestamp TIMESTAMP NOT NULL,
    change_date DATE NOT NULL,
    
    entity_type ENUM('Product', 'Material', 'Service'),
    entity_id INT,
    entity_name VARCHAR(255),
    
    price_type VARCHAR(100),  -- Selling Price, Cost Price, Standard Cost
    
    old_price DECIMAL(12,2),
    new_price DECIMAL(12,2),
    price_change_percent DECIMAL(6,2),
    
    effective_date DATE,
    
    changed_by INT,
    changed_by_username VARCHAR(100),
    
    approval_required BOOLEAN,
    approved_by INT,
    approval_timestamp TIMESTAMP,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    KEY idx_entity_date (entity_type, change_date),
    KEY idx_user_date (changed_by, change_date),
    KEY idx_sequence (price_sequence)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
PARTITION BY RANGE (YEAR(change_timestamp)) (
    PARTITION p2024 VALUES LESS THAN (2025),
    PARTITION p2025 VALUES LESS THAN (2026),
    PARTITION p2026 VALUES LESS THAN (2027),
    PARTITION p2027 VALUES LESS THAN (2028),
    PARTITION p2028 VALUES LESS THAN (2029),
    PARTITION p2029 VALUES LESS THAN (2030),
    PARTITION p2030 VALUES LESS THAN (2031),
    PARTITION p2031 VALUES LESS THAN (2032)
);

-- ============================================================================
-- COMPLIANCE & LEGAL TABLES (12 tables)
-- ============================================================================

-- SLA Compliance Tracking
CREATE TABLE IF NOT EXISTS sla_compliance_tracking (
    sla_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    sla_sequence BIGINT UNIQUE NOT NULL,
    
    check_timestamp TIMESTAMP NOT NULL,
    check_date DATE NOT NULL,
    
    sla_type VARCHAR(100),  -- On-time Delivery, Quality, Response Time
    sla_target_percent DECIMAL(5,2),
    
    actual_compliance_percent DECIMAL(5,2),
    compliance_status ENUM('Met', 'At Risk', 'Breached'),
    
    violations_count INT,
    critical_violations INT,
    
    affected_customers INT,
    impact_revenue DECIMAL(14,2),
    
    remediation_required BOOLEAN,
    remediation_plan VARCHAR(255),
    remediation_by_date DATE,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    KEY idx_sla_type (sla_type, check_date),
    KEY idx_status (compliance_status, check_date),
    KEY idx_sequence (sla_sequence)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
PARTITION BY RANGE (YEAR(check_timestamp)) (
    PARTITION p2024 VALUES LESS THAN (2025),
    PARTITION p2025 VALUES LESS THAN (2026),
    PARTITION p2026 VALUES LESS THAN (2027),
    PARTITION p2027 VALUES LESS THAN (2028),
    PARTITION p2028 VALUES LESS THAN (2029),
    PARTITION p2029 VALUES LESS THAN (2030),
    PARTITION p2030 VALUES LESS THAN (2031),
    PARTITION p2031 VALUES LESS THAN (2032)
);

-- GDPR Data Request Log
CREATE TABLE IF NOT EXISTS gdpr_data_request_log (
    gdpr_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    gdpr_sequence BIGINT UNIQUE NOT NULL,
    
    request_timestamp TIMESTAMP NOT NULL,
    request_date DATE NOT NULL,
    
    request_type ENUM('Access', 'Rectification', 'Erasure', 'Restriction', 'Portability', 'Objection'),
    request_status ENUM('Pending', 'Processing', 'Completed', 'Denied', 'Expired'),
    
    data_subject_id INT,
    data_subject_name VARCHAR(255),
    
    requestor_type VARCHAR(100),  -- Data Subject, Authorized Representative, Legal
    
    personal_data_scope TEXT,
    affected_systems TEXT,
    
    requested_by INT,
    requested_by_username VARCHAR(100),
    
    -- Processing
    processing_started TIMESTAMP,
    processing_completed TIMESTAMP,
    processing_duration_days INT,
    
    processed_by INT,
    processed_by_username VARCHAR(100),
    
    -- Fulfillment
    delivery_method VARCHAR(100),
    delivery_date TIMESTAMP,
    
    -- Legal hold
    legal_hold BOOLEAN,
    legal_hold_reason VARCHAR(255),
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    KEY idx_data_subject (data_subject_id, request_date),
    KEY idx_status (request_status, request_date),
    KEY idx_type (request_type, request_date),
    KEY idx_sequence (gdpr_sequence)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
PARTITION BY RANGE (YEAR(request_timestamp)) (
    PARTITION p2024 VALUES LESS THAN (2025),
    PARTITION p2025 VALUES LESS THAN (2026),
    PARTITION p2026 VALUES LESS THAN (2027),
    PARTITION p2027 VALUES LESS THAN (2028),
    PARTITION p2028 VALUES LESS THAN (2029),
    PARTITION p2029 VALUES LESS THAN (2030),
    PARTITION p2030 VALUES LESS THAN (2031),
    PARTITION p2031 VALUES LESS THAN (2032)
);

-- Legal Hold Tracking
CREATE TABLE IF NOT EXISTS legal_hold_tracking (
    hold_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    hold_sequence BIGINT UNIQUE NOT NULL,
    
    hold_timestamp TIMESTAMP NOT NULL,
    hold_date DATE NOT NULL,
    
    case_id VARCHAR(100),
    case_name VARCHAR(255),
    case_type VARCHAR(100),  -- Litigation, Investigation, Regulatory
    
    hold_scope VARCHAR(255),  -- Data range, Systems affected
    
    -- Hold status
    hold_status ENUM('Active', 'Suspended', 'Released'),
    
    hold_issued_by INT,
    hold_issued_by_name VARCHAR(255),
    
    -- Duration
    hold_start_date DATE,
    hold_expected_end_date DATE,
    hold_actual_end_date DATE,
    
    -- Affected data
    data_locations TEXT,
    estimated_data_size_gb DECIMAL(10,2),
    
    -- Compliance
    compliance_verified BOOLEAN,
    verification_timestamp TIMESTAMP,
    
    release_authorized_by INT,
    release_reason VARCHAR(255),
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    KEY idx_case_date (case_id, hold_date),
    KEY idx_status (hold_status, hold_date),
    KEY idx_sequence (hold_sequence)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
PARTITION BY RANGE (YEAR(hold_timestamp)) (
    PARTITION p2024 VALUES LESS THAN (2025),
    PARTITION p2025 VALUES LESS THAN (2026),
    PARTITION p2026 VALUES LESS THAN (2027),
    PARTITION p2027 VALUES LESS THAN (2028),
    PARTITION p2028 VALUES LESS THAN (2029),
    PARTITION p2029 VALUES LESS THAN (2030),
    PARTITION p2030 VALUES LESS THAN (2031),
    PARTITION p2031 VALUES LESS THAN (2032)
);

-- SOX Compliance Log
CREATE TABLE IF NOT EXISTS sox_compliance_log (
    sox_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    sox_sequence BIGINT UNIQUE NOT NULL,
    
    check_timestamp TIMESTAMP NOT NULL,
    check_date DATE NOT NULL,
    
    control_id VARCHAR(100),
    control_name VARCHAR(255),
    control_category VARCHAR(100),
    
    control_status ENUM('Compliant', 'Non-Compliant', 'In Progress', 'Waived'),
    
    tested_by INT,
    tested_by_username VARCHAR(100),
    
    -- Issues
    issues_found INT,
    critical_issues INT,
    
    evidence_collected BOOLEAN,
    evidence_location VARCHAR(255),
    
    remediation_required BOOLEAN,
    remediation_plan VARCHAR(255),
    remediation_due_date DATE,
    
    auditor_reviewed BOOLEAN,
    auditor_name VARCHAR(255),
    auditor_comments TEXT,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    KEY idx_control_date (control_id, check_date),
    KEY idx_status (control_status, check_date),
    KEY idx_sequence (sox_sequence)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
PARTITION BY RANGE (YEAR(check_timestamp)) (
    PARTITION p2024 VALUES LESS THAN (2025),
    PARTITION p2025 VALUES LESS THAN (2026),
    PARTITION p2026 VALUES LESS THAN (2027),
    PARTITION p2027 VALUES LESS THAN (2028),
    PARTITION p2028 VALUES LESS THAN (2029),
    PARTITION p2029 VALUES LESS THAN (2030),
    PARTITION p2030 VALUES LESS THAN (2031),
    PARTITION p2031 VALUES LESS THAN (2032)
);

-- HIPAA Compliance (if healthcare related)
CREATE TABLE IF NOT EXISTS hipaa_compliance_log (
    hipaa_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    hipaa_sequence BIGINT UNIQUE NOT NULL,
    
    check_timestamp TIMESTAMP NOT NULL,
    check_date DATE NOT NULL,
    
    safeguard_type VARCHAR(100),
    safeguard_name VARCHAR(255),
    
    compliance_status ENUM('Compliant', 'Non-Compliant', 'Remediation In Progress'),
    
    breach_detected BOOLEAN,
    breach_scope VARCHAR(255),
    breach_notification_sent BOOLEAN,
    
    checked_by INT,
    checked_by_username VARCHAR(100),
    
    issues_found INT,
    corrective_actions INT,
    actions_completed INT,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    KEY idx_date (check_date),
    KEY idx_status (compliance_status, check_date),
    KEY idx_sequence (hipaa_sequence)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
PARTITION BY RANGE (YEAR(check_timestamp)) (
    PARTITION p2024 VALUES LESS THAN (2025),
    PARTITION p2025 VALUES LESS THAN (2026),
    PARTITION p2026 VALUES LESS THAN (2027),
    PARTITION p2027 VALUES LESS THAN (2028),
    PARTITION p2028 VALUES LESS THAN (2029),
    PARTITION p2029 VALUES LESS THAN (2030),
    PARTITION p2030 VALUES LESS THAN (2031),
    PARTITION p2031 VALUES LESS THAN (2032)
);

-- Audit Trail Completeness Check
CREATE TABLE IF NOT EXISTS audit_trail_completeness (
    completeness_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    check_timestamp TIMESTAMP NOT NULL,
    check_date DATE NOT NULL,
    
    source_system VARCHAR(100),
    table_name VARCHAR(100),
    
    expected_sequence_start BIGINT,
    expected_sequence_end BIGINT,
    actual_sequence_count BIGINT,
    
    gap_found BOOLEAN,
    gap_details TEXT,
    
    checked_by INT,
    checked_by_username VARCHAR(100),
    
    remediation_executed BOOLEAN,
    remediation_details TEXT,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    KEY idx_check_date (check_date),
    KEY idx_gap (gap_found, check_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Audit Report Schedule
CREATE TABLE IF NOT EXISTS audit_report_schedule (
    report_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    
    report_name VARCHAR(255) NOT NULL,
    report_type VARCHAR(100),
    report_frequency VARCHAR(50),  -- Daily, Weekly, Monthly
    
    report_template VARCHAR(255),
    
    generated_by INT,
    generated_by_username VARCHAR(100),
    
    scheduled_time VARCHAR(10),
    is_active BOOLEAN,
    
    recipients TEXT,  -- Email list
    
    last_generated TIMESTAMP,
    next_scheduled TIMESTAMP,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    UNIQUE KEY uk_report_name (report_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================================
-- AUDIT METADATA TABLES
-- ============================================================================

-- Audit Sequence Manager (for gap detection)
CREATE TABLE IF NOT EXISTS audit_sequence_manager (
    manager_id INT AUTO_INCREMENT PRIMARY KEY,
    audit_type VARCHAR(100) UNIQUE NOT NULL,
    
    last_sequence BIGINT NOT NULL DEFAULT 0,
    next_sequence BIGINT NOT NULL DEFAULT 1,
    
    sequence_gaps INT DEFAULT 0,
    max_allowed_gap INT DEFAULT 100,
    
    alert_on_gap BOOLEAN DEFAULT TRUE,
    
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Audit ETL Sync Log
CREATE TABLE IF NOT EXISTS audit_etl_sync_log (
    sync_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    sync_sequence BIGINT UNIQUE NOT NULL,
    
    sync_timestamp TIMESTAMP NOT NULL,
    sync_date DATE NOT NULL,
    
    source_system VARCHAR(100),
    source_table VARCHAR(100),
    target_table VARCHAR(100),
    
    rows_extracted INT,
    rows_transformed INT,
    rows_loaded INT,
    rows_failed INT,
    
    sync_duration_seconds INT,
    
    sync_status ENUM('Success', 'Failed', 'Partial'),
    error_message TEXT,
    
    last_sync_id BIGINT,
    current_sync_id BIGINT,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    KEY idx_source_date (source_table, sync_date),
    KEY idx_status (sync_status, sync_date),
    KEY idx_sequence (sync_sequence)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================================
-- END OF AUDIT SCHEMA
-- ============================================================================
