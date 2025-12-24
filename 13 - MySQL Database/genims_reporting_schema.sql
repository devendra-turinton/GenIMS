-- ============================================================================
-- GenIMS MySQL Reporting Schema
-- 35 Tables for Analytics, KPIs, and Dashboards
-- Refresh: Hourly from PostgreSQL (denormalized for fast reads)
-- Retention: 12-month rolling window
-- ============================================================================

-- Set session variables
SET SESSION sql_mode='STRICT_TRANS_TABLES';
SET SESSION time_zone='+00:00';

-- ============================================================================
-- PERFORMANCE TABLES (8 tables)
-- ============================================================================

-- Machine Performance Daily (OEE, Availability, Throughput)
CREATE TABLE IF NOT EXISTS machine_performance_daily (
    performance_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    factory_id INT NOT NULL,
    line_id INT NOT NULL,
    machine_id INT NOT NULL,
    performance_date DATE NOT NULL,
    
    -- Availability metrics
    scheduled_time_minutes DECIMAL(10,2),
    downtime_minutes DECIMAL(10,2),
    availability_percent DECIMAL(5,2),
    
    -- Performance metrics
    ideal_cycle_time DECIMAL(10,2),
    actual_cycle_time DECIMAL(10,2),
    performance_percent DECIMAL(5,2),
    
    -- Quality metrics
    total_pieces INT,
    defect_pieces INT,
    quality_percent DECIMAL(5,2),
    
    -- OEE Calculation
    oee_percent DECIMAL(5,2),
    
    -- Additional metrics
    mtbf_hours DECIMAL(10,2),
    mttr_minutes DECIMAL(10,2),
    energy_consumed_kwh DECIMAL(12,2),
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    UNIQUE KEY uk_machine_date (factory_id, line_id, machine_id, performance_date),
    KEY idx_factory_date (factory_id, performance_date),
    KEY idx_oee (oee_percent, performance_date),
    KEY idx_machine (machine_id, performance_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Production Summary Daily (Units, Labor, Costs)
CREATE TABLE IF NOT EXISTS production_summary_daily (
    production_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    factory_id INT NOT NULL,
    line_id INT NOT NULL,
    production_date DATE NOT NULL,
    shift_name VARCHAR(50),
    
    -- Production metrics
    total_work_orders INT,
    completed_work_orders INT,
    units_produced INT,
    units_defective INT,
    
    -- Labor metrics
    total_labor_hours DECIMAL(10,2),
    standard_labor_hours DECIMAL(10,2),
    labor_variance_hours DECIMAL(10,2),
    labor_variance_percent DECIMAL(5,2),
    
    -- Cost metrics
    standard_material_cost DECIMAL(12,2),
    actual_material_cost DECIMAL(12,2),
    material_variance DECIMAL(12,2),
    
    standard_labor_cost DECIMAL(12,2),
    actual_labor_cost DECIMAL(12,2),
    labor_cost_variance DECIMAL(12,2),
    
    standard_overhead_cost DECIMAL(12,2),
    actual_overhead_cost DECIMAL(12,2),
    overhead_variance DECIMAL(12,2),
    
    total_standard_cost DECIMAL(12,2),
    total_actual_cost DECIMAL(12,2),
    total_variance DECIMAL(12,2),
    variance_percent DECIMAL(5,2),
    
    -- Schedule performance
    on_time_delivery_percent DECIMAL(5,2),
    schedule_adherence_percent DECIMAL(5,2),
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    UNIQUE KEY uk_line_date (factory_id, line_id, production_date),
    KEY idx_factory_date (factory_id, production_date),
    KEY idx_variance (variance_percent, production_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Downtime Summary Daily (By Type, MTBF, MTTR)
CREATE TABLE IF NOT EXISTS downtime_summary_daily (
    downtime_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    factory_id INT NOT NULL,
    line_id INT NOT NULL,
    machine_id INT NOT NULL,
    downtime_date DATE NOT NULL,
    
    downtime_type VARCHAR(100),
    downtime_category VARCHAR(100),
    
    total_downtime_minutes DECIMAL(10,2),
    downtime_incidents INT,
    
    avg_incident_duration DECIMAL(10,2),
    mtbf_hours DECIMAL(10,2),
    mttr_minutes DECIMAL(10,2),
    
    -- Root causes
    maintenance_downtime DECIMAL(10,2),
    changeover_downtime DECIMAL(10,2),
    material_downtime DECIMAL(10,2),
    operator_downtime DECIMAL(10,2),
    other_downtime DECIMAL(10,2),
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    UNIQUE KEY uk_machine_date_type (machine_id, downtime_date, downtime_type),
    KEY idx_machine_date (machine_id, downtime_date),
    KEY idx_mttr (mttr_minutes, downtime_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Quality Summary Daily
CREATE TABLE IF NOT EXISTS quality_summary_daily (
    quality_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    factory_id INT NOT NULL,
    product_id INT NOT NULL,
    quality_date DATE NOT NULL,
    
    total_units_inspected INT,
    defect_units INT,
    defect_rate_percent DECIMAL(5,3),
    
    critical_defects INT,
    major_defects INT,
    minor_defects INT,
    
    ppk DECIMAL(5,3),
    cpk DECIMAL(5,3),
    
    -- Quality causes
    material_defects INT,
    process_defects INT,
    operator_defects INT,
    equipment_defects INT,
    
    cost_of_poor_quality DECIMAL(12,2),
    rework_units INT,
    scrap_units INT,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    UNIQUE KEY uk_product_date (factory_id, product_id, quality_date),
    KEY idx_defect_rate (defect_rate_percent, quality_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Labor Efficiency Daily
CREATE TABLE IF NOT EXISTS labor_efficiency_daily (
    labor_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    factory_id INT NOT NULL,
    employee_id INT NOT NULL,
    labor_date DATE NOT NULL,
    shift_name VARCHAR(50),
    
    scheduled_hours DECIMAL(10,2),
    worked_hours DECIMAL(10,2),
    absence_hours DECIMAL(10,2),
    
    units_produced INT,
    productivity_units_per_hour DECIMAL(10,2),
    
    standard_hours_for_output DECIMAL(10,2),
    labor_efficiency_percent DECIMAL(5,2),
    
    quality_score DECIMAL(5,2),
    safety_incidents INT,
    
    overtime_hours DECIMAL(10,2),
    premium_labor_cost DECIMAL(10,2),
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    UNIQUE KEY uk_employee_date (factory_id, employee_id, labor_date),
    KEY idx_efficiency (labor_efficiency_percent, labor_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Energy Consumption Daily
CREATE TABLE IF NOT EXISTS energy_consumption_daily (
    energy_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    factory_id INT NOT NULL,
    line_id INT NOT NULL,
    energy_date DATE NOT NULL,
    
    total_kwh DECIMAL(12,2),
    peak_kw DECIMAL(10,2),
    avg_kw DECIMAL(10,2),
    
    units_produced INT,
    kwh_per_unit DECIMAL(10,3),
    
    standard_kwh DECIMAL(12,2),
    kwh_variance DECIMAL(12,2),
    variance_percent DECIMAL(5,2),
    
    -- By equipment
    compressed_air_kwh DECIMAL(12,2),
    motors_kwh DECIMAL(12,2),
    heating_kwh DECIMAL(12,2),
    lighting_kwh DECIMAL(12,2),
    other_kwh DECIMAL(12,2),
    
    cost_per_kwh DECIMAL(10,4),
    total_energy_cost DECIMAL(12,2),
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    UNIQUE KEY uk_line_date (factory_id, line_id, energy_date),
    KEY idx_consumption (total_kwh, energy_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Safety & Compliance Daily
CREATE TABLE IF NOT EXISTS safety_compliance_daily (
    safety_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    factory_id INT NOT NULL,
    safety_date DATE NOT NULL,
    
    total_employees_worked INT,
    near_miss_incidents INT,
    lost_time_incidents INT,
    recordable_incidents INT,
    
    total_incident_hours INT,
    lti_frequency_rate DECIMAL(5,2),
    trir_rate DECIMAL(5,2),
    
    lost_work_days INT,
    restricted_work_days INT,
    
    safety_audit_score DECIMAL(5,2),
    compliance_issues INT,
    corrective_actions INT,
    
    training_hours INT,
    employees_trained INT,
    
    equipment_maintenance_issues INT,
    environmental_violations INT,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    UNIQUE KEY uk_factory_date (factory_id, safety_date),
    KEY idx_incidents (recordable_incidents, safety_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================================
-- SALES TABLES (7 tables)
-- ============================================================================

-- Sales Order Summary (Revenue, Margin, On-Time %)
CREATE TABLE IF NOT EXISTS sales_order_summary (
    sales_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    factory_id INT NOT NULL,
    customer_id INT NOT NULL,
    summary_date DATE NOT NULL,
    
    total_orders INT,
    delivered_orders INT,
    overdue_orders INT,
    cancelled_orders INT,
    
    on_time_delivery_count INT,
    on_time_percent DECIMAL(5,2),
    
    total_order_qty INT,
    delivered_qty INT,
    
    gross_revenue DECIMAL(14,2),
    returns_amount DECIMAL(14,2),
    net_revenue DECIMAL(14,2),
    
    standard_cost DECIMAL(14,2),
    actual_cost DECIMAL(14,2),
    
    gross_margin DECIMAL(14,2),
    gross_margin_percent DECIMAL(5,2),
    
    operating_expenses DECIMAL(14,2),
    operating_profit DECIMAL(14,2),
    operating_margin_percent DECIMAL(5,2),
    
    -- Additional metrics
    avg_order_value DECIMAL(12,2),
    cycle_time_days DECIMAL(8,2),
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    UNIQUE KEY uk_customer_date (factory_id, customer_id, summary_date),
    KEY idx_revenue (net_revenue, summary_date),
    KEY idx_margin (gross_margin_percent, summary_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Customer Performance YTD
CREATE TABLE IF NOT EXISTS customer_performance_ytd (
    customer_ytd_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    factory_id INT NOT NULL,
    customer_id INT NOT NULL,
    year_month VARCHAR(7) NOT NULL,
    
    ytd_total_orders INT,
    ytd_delivered_orders INT,
    ytd_on_time_percent DECIMAL(5,2),
    ytd_cancelled_orders INT,
    
    ytd_revenue DECIMAL(14,2),
    ytd_margin DECIMAL(14,2),
    ytd_margin_percent DECIMAL(5,2),
    
    ytd_avg_payment_days DECIMAL(8,2),
    ytd_bad_debt_amount DECIMAL(14,2),
    
    -- Trends
    revenue_vs_target_percent DECIMAL(5,2),
    margin_vs_target_percent DECIMAL(5,2),
    
    -- Risk indicators
    churn_risk_score DECIMAL(5,2),
    days_since_last_order INT,
    payment_days_aging INT,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    UNIQUE KEY uk_customer_month (factory_id, customer_id, year_month),
    KEY idx_churn_risk (churn_risk_score, year_month)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Product Sales Performance
CREATE TABLE IF NOT EXISTS product_sales_performance (
    product_sales_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    factory_id INT NOT NULL,
    product_id INT NOT NULL,
    sales_month VARCHAR(7) NOT NULL,
    
    units_sold INT,
    unit_price DECIMAL(10,2),
    revenue DECIMAL(14,2),
    
    standard_cost DECIMAL(12,2),
    actual_cost DECIMAL(12,2),
    cost_variance DECIMAL(12,2),
    
    gross_profit DECIMAL(14,2),
    gross_margin_percent DECIMAL(5,2),
    
    -- Demand metrics
    demand_vs_forecast_percent DECIMAL(5,2),
    stock_outs INT,
    excess_inventory INT,
    
    quality_returns INT,
    return_rate_percent DECIMAL(5,2),
    
    -- Trends
    mom_growth_percent DECIMAL(5,2),
    yoy_growth_percent DECIMAL(5,2),
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    UNIQUE KEY uk_product_month (factory_id, product_id, sales_month),
    KEY idx_revenue (revenue, sales_month)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Delivery Performance
CREATE TABLE IF NOT EXISTS delivery_performance (
    delivery_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    factory_id INT NOT NULL,
    delivery_date DATE NOT NULL,
    
    total_deliveries INT,
    on_time_deliveries INT,
    early_deliveries INT,
    late_deliveries INT,
    
    on_time_percent DECIMAL(5,2),
    
    total_delivery_qty INT,
    total_delivery_cost DECIMAL(12,2),
    avg_delivery_cost DECIMAL(10,2),
    
    -- By region
    domestic_deliveries INT,
    export_deliveries INT,
    
    -- Carrier performance
    carrier_on_time_percent DECIMAL(5,2),
    delivery_damage_count INT,
    delivery_damage_cost DECIMAL(12,2),
    
    customer_satisfaction_score DECIMAL(5,2),
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    UNIQUE KEY uk_delivery_date (factory_id, delivery_date),
    KEY idx_on_time (on_time_percent, delivery_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Cash Flow Daily
CREATE TABLE IF NOT EXISTS cash_flow_daily (
    cash_flow_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    factory_id INT NOT NULL,
    cash_flow_date DATE NOT NULL,
    
    -- Collections
    sales_receipts DECIMAL(14,2),
    other_receipts DECIMAL(14,2),
    total_inflows DECIMAL(14,2),
    
    -- Payments
    material_payments DECIMAL(14,2),
    labor_payments DECIMAL(14,2),
    operational_payments DECIMAL(14,2),
    capital_expenditure DECIMAL(14,2),
    other_payments DECIMAL(14,2),
    total_outflows DECIMAL(14,2),
    
    -- Balance
    net_cash_flow DECIMAL(14,2),
    cumulative_cash_position DECIMAL(14,2),
    
    -- Metrics
    dso_days DECIMAL(8,2),
    dpo_days DECIMAL(8,2),
    cash_conversion_cycle DECIMAL(8,2),
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    UNIQUE KEY uk_factory_date (factory_id, cash_flow_date),
    KEY idx_balance (cumulative_cash_position, cash_flow_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================================
-- FINANCIAL TABLES (8 tables)
-- ============================================================================

-- Profit & Loss Daily
CREATE TABLE IF NOT EXISTS profit_and_loss_daily (
    pnl_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    factory_id INT NOT NULL,
    pnl_date DATE NOT NULL,
    
    -- Revenue
    gross_revenue DECIMAL(14,2),
    returns_and_allowances DECIMAL(14,2),
    net_revenue DECIMAL(14,2),
    
    -- Cost of goods sold
    material_cost DECIMAL(14,2),
    labor_cost DECIMAL(14,2),
    manufacturing_overhead DECIMAL(14,2),
    depreciation DECIMAL(14,2),
    total_cogs DECIMAL(14,2),
    
    gross_profit DECIMAL(14,2),
    gross_profit_margin DECIMAL(5,2),
    
    -- Operating expenses
    selling_expenses DECIMAL(14,2),
    general_expenses DECIMAL(14,2),
    administrative_expenses DECIMAL(14,2),
    total_opex DECIMAL(14,2),
    
    operating_profit DECIMAL(14,2),
    operating_margin DECIMAL(5,2),
    
    -- Other income/expense
    interest_income DECIMAL(14,2),
    interest_expense DECIMAL(14,2),
    other_income DECIMAL(14,2),
    other_expense DECIMAL(14,2),
    
    net_profit DECIMAL(14,2),
    net_margin DECIMAL(5,2),
    
    -- Tax
    tax_provision DECIMAL(14,2),
    net_income_after_tax DECIMAL(14,2),
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    UNIQUE KEY uk_factory_date (factory_id, pnl_date),
    KEY idx_profit (net_profit, pnl_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Cost Analysis Daily (Material, Labor, Overhead)
CREATE TABLE IF NOT EXISTS cost_analysis_daily (
    cost_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    factory_id INT NOT NULL,
    cost_date DATE NOT NULL,
    
    -- Material costs
    raw_material_cost DECIMAL(14,2),
    material_waste_cost DECIMAL(14,2),
    material_variance DECIMAL(14,2),
    material_variance_percent DECIMAL(5,2),
    
    -- Labor costs
    direct_labor_cost DECIMAL(14,2),
    indirect_labor_cost DECIMAL(14,2),
    labor_variance DECIMAL(14,2),
    labor_variance_percent DECIMAL(5,2),
    
    -- Overhead costs
    fixed_overhead DECIMAL(14,2),
    variable_overhead DECIMAL(14,2),
    overhead_variance DECIMAL(14,2),
    overhead_variance_percent DECIMAL(5,2),
    
    -- Cost per unit
    total_units_produced INT,
    material_cost_per_unit DECIMAL(10,2),
    labor_cost_per_unit DECIMAL(10,2),
    overhead_cost_per_unit DECIMAL(10,2),
    total_cost_per_unit DECIMAL(10,2),
    
    -- Actual vs Standard
    total_standard_cost DECIMAL(14,2),
    total_actual_cost DECIMAL(14,2),
    total_variance DECIMAL(14,2),
    total_variance_percent DECIMAL(5,2),
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    UNIQUE KEY uk_factory_date (factory_id, cost_date),
    KEY idx_variance (total_variance_percent, cost_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Budget vs Actual
CREATE TABLE IF NOT EXISTS budget_vs_actual (
    budget_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    factory_id INT NOT NULL,
    budget_month VARCHAR(7) NOT NULL,
    category VARCHAR(100) NOT NULL,
    
    budgeted_amount DECIMAL(14,2),
    actual_amount DECIMAL(14,2),
    variance_amount DECIMAL(14,2),
    variance_percent DECIMAL(5,2),
    
    ytd_budgeted DECIMAL(14,2),
    ytd_actual DECIMAL(14,2),
    ytd_variance DECIMAL(14,2),
    ytd_variance_percent DECIMAL(5,2),
    
    trend_status ENUM('On Track', 'Caution', 'Risk'),
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    UNIQUE KEY uk_factory_category_month (factory_id, category, budget_month),
    KEY idx_variance (variance_percent, budget_month)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Capital Expenditure Tracking
CREATE TABLE IF NOT EXISTS capex_tracking (
    capex_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    factory_id INT NOT NULL,
    asset_id INT NOT NULL,
    capex_date DATE NOT NULL,
    
    capex_description VARCHAR(255),
    budgeted_amount DECIMAL(14,2),
    actual_amount DECIMAL(14,2),
    
    useful_life_years INT,
    depreciation_method VARCHAR(50),
    accumulated_depreciation DECIMAL(14,2),
    book_value DECIMAL(14,2),
    
    roi_percent DECIMAL(5,2),
    payback_period_months INT,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    UNIQUE KEY uk_asset_date (factory_id, asset_id, capex_date),
    KEY idx_capex (actual_amount, capex_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Key Financial Ratios
CREATE TABLE IF NOT EXISTS financial_ratios (
    ratio_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    factory_id INT NOT NULL,
    ratio_date DATE NOT NULL,
    
    -- Profitability
    gross_profit_margin DECIMAL(5,2),
    operating_margin DECIMAL(5,2),
    net_profit_margin DECIMAL(5,2),
    roa_percent DECIMAL(5,2),
    roe_percent DECIMAL(5,2),
    
    -- Liquidity
    current_ratio DECIMAL(5,2),
    quick_ratio DECIMAL(5,2),
    cash_ratio DECIMAL(5,2),
    
    -- Efficiency
    asset_turnover DECIMAL(5,2),
    inventory_turnover DECIMAL(5,2),
    receivables_turnover DECIMAL(5,2),
    
    -- Leverage
    debt_to_equity DECIMAL(5,2),
    debt_to_assets DECIMAL(5,2),
    equity_ratio DECIMAL(5,2),
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    UNIQUE KEY uk_factory_date (factory_id, ratio_date),
    KEY idx_profitability (net_profit_margin, ratio_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================================
-- INVENTORY TABLES (12 tables)
-- ============================================================================

-- Inventory Value Summary
CREATE TABLE IF NOT EXISTS inventory_value_summary (
    inventory_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    factory_id INT NOT NULL,
    inventory_date DATE NOT NULL,
    
    total_inventory_qty INT,
    total_inventory_value DECIMAL(14,2),
    
    -- By classification
    abc_class_a_qty INT,
    abc_class_a_value DECIMAL(14,2),
    abc_class_b_qty INT,
    abc_class_b_value DECIMAL(14,2),
    abc_class_c_qty INT,
    abc_class_c_value DECIMAL(14,2),
    
    -- By category
    raw_material_qty INT,
    raw_material_value DECIMAL(14,2),
    wip_qty INT,
    wip_value DECIMAL(14,2),
    finished_goods_qty INT,
    finished_goods_value DECIMAL(14,2),
    
    -- Metrics
    slow_moving_qty INT,
    slow_moving_value DECIMAL(14,2),
    obsolete_qty INT,
    obsolete_value DECIMAL(14,2),
    inventory_turnover DECIMAL(5,2),
    days_inventory_outstanding INT,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    UNIQUE KEY uk_factory_date (factory_id, inventory_date),
    KEY idx_value (total_inventory_value, inventory_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Material Flow Daily
CREATE TABLE IF NOT EXISTS material_flow_daily (
    flow_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    factory_id INT NOT NULL,
    material_id INT NOT NULL,
    flow_date DATE NOT NULL,
    
    opening_qty INT,
    opening_value DECIMAL(14,2),
    
    receipts_qty INT,
    receipts_value DECIMAL(14,2),
    
    issues_qty INT,
    issues_value DECIMAL(14,2),
    
    scrap_qty INT,
    scrap_value DECIMAL(14,2),
    
    adjustments_qty INT,
    adjustments_value DECIMAL(14,2),
    
    closing_qty INT,
    closing_value DECIMAL(14,2),
    
    unit_cost DECIMAL(10,4),
    
    -- Variance
    qty_variance INT,
    value_variance DECIMAL(14,2),
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    UNIQUE KEY uk_material_date (factory_id, material_id, flow_date),
    KEY idx_variance (value_variance, flow_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Purchase Order Performance
CREATE TABLE IF NOT EXISTS purchase_order_performance (
    po_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    factory_id INT NOT NULL,
    supplier_id INT NOT NULL,
    po_date DATE NOT NULL,
    
    total_pos INT,
    total_qty INT,
    total_amount DECIMAL(14,2),
    
    on_time_pos INT,
    on_time_qty INT,
    on_time_percent DECIMAL(5,2),
    
    quality_acceptable INT,
    quality_defects INT,
    defect_rate_percent DECIMAL(5,3),
    
    price_variance DECIMAL(14,2),
    price_variance_percent DECIMAL(5,2),
    
    avg_lead_time_days DECIMAL(8,2),
    
    -- Supplier metrics
    supplier_rating DECIMAL(5,2),
    supplier_compliance_percent DECIMAL(5,2),
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    UNIQUE KEY uk_supplier_date (factory_id, supplier_id, po_date),
    KEY idx_on_time (on_time_percent, po_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Finished Goods Warehouse
CREATE TABLE IF NOT EXISTS finished_goods_warehouse (
    fg_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    factory_id INT NOT NULL,
    warehouse_id INT NOT NULL,
    product_id INT NOT NULL,
    fg_date DATE NOT NULL,
    
    stock_qty INT,
    stock_value DECIMAL(14,2),
    
    safety_stock_qty INT,
    reorder_qty INT,
    eoq INT,
    
    -- Metrics
    stock_outs_this_month INT,
    overstock_qty INT,
    overstock_value DECIMAL(14,2),
    
    movement_qty_30days INT,
    movement_qty_60days INT,
    movement_qty_90days INT,
    
    aging_0_30_days INT,
    aging_30_90_days INT,
    aging_90plus_days INT,
    
    carrying_cost_monthly DECIMAL(12,2),
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    UNIQUE KEY uk_warehouse_product_date (warehouse_id, product_id, fg_date),
    KEY idx_stock (stock_value, fg_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Raw Material Warehouse
CREATE TABLE IF NOT EXISTS raw_material_warehouse (
    rm_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    factory_id INT NOT NULL,
    warehouse_id INT NOT NULL,
    material_id INT NOT NULL,
    rm_date DATE NOT NULL,
    
    stock_qty INT,
    stock_value DECIMAL(14,2),
    
    -- Par levels
    min_qty INT,
    max_qty INT,
    reorder_point INT,
    reorder_qty INT,
    
    -- Metrics
    stock_outs_this_month INT,
    overstock_qty INT,
    
    receipts_this_month INT,
    issues_this_month INT,
    
    supplier_lead_time_days INT,
    turnover_ratio DECIMAL(5,2),
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    UNIQUE KEY uk_warehouse_material_date (warehouse_id, material_id, rm_date),
    KEY idx_stock (stock_value, rm_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Work In Process
CREATE TABLE IF NOT EXISTS work_in_process (
    wip_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    factory_id INT NOT NULL,
    line_id INT NOT NULL,
    wip_date DATE NOT NULL,
    
    total_wip_qty INT,
    total_wip_value DECIMAL(14,2),
    
    -- By stage
    stage_1_qty INT,
    stage_1_value DECIMAL(14,2),
    stage_2_qty INT,
    stage_2_value DECIMAL(14,2),
    stage_3_qty INT,
    stage_3_value DECIMAL(14,2),
    stage_4_qty INT,
    stage_4_value DECIMAL(14,2),
    
    -- Metrics
    average_cycle_time_hours DECIMAL(8,2),
    material_added_value DECIMAL(14,2),
    labor_added_value DECIMAL(14,2),
    overhead_added_value DECIMAL(14,2),
    
    obsolete_wip_qty INT,
    obsolete_wip_value DECIMAL(14,2),
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    UNIQUE KEY uk_line_date (factory_id, line_id, wip_date),
    KEY idx_value (total_wip_value, wip_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Demand Forecast vs Actual
CREATE TABLE IF NOT EXISTS demand_forecast_vs_actual (
    demand_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    factory_id INT NOT NULL,
    product_id INT NOT NULL,
    forecast_month VARCHAR(7) NOT NULL,
    
    forecasted_qty INT,
    actual_qty INT,
    variance_qty INT,
    variance_percent DECIMAL(5,2),
    
    forecast_accuracy_percent DECIMAL(5,2),
    
    stock_position_eom INT,
    safety_stock_position INT,
    
    stock_outs_prevented INT,
    excess_inventory_qty INT,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    UNIQUE KEY uk_product_month (factory_id, product_id, forecast_month),
    KEY idx_accuracy (forecast_accuracy_percent, forecast_month)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================================
-- INTEGRATION & METADATA TABLES
-- ============================================================================

-- ETL Sync Log (for monitoring)
CREATE TABLE IF NOT EXISTS etl_sync_log (
    sync_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    sync_source VARCHAR(100) NOT NULL,
    sync_target VARCHAR(100) NOT NULL,
    table_name VARCHAR(100) NOT NULL,
    
    sync_start_time TIMESTAMP NOT NULL,
    sync_end_time TIMESTAMP,
    sync_duration_seconds INT,
    
    rows_extracted INT,
    rows_transformed INT,
    rows_loaded INT,
    rows_skipped INT,
    
    status ENUM('Running', 'Success', 'Failed', 'Partial'),
    error_message TEXT,
    
    last_source_update TIMESTAMP,
    last_target_update TIMESTAMP,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    KEY idx_status (status, sync_start_time),
    KEY idx_table (table_name, sync_start_time)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Data Quality Metrics
CREATE TABLE IF NOT EXISTS data_quality_metrics (
    quality_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    table_name VARCHAR(100) NOT NULL,
    check_date DATE NOT NULL,
    
    total_rows INT,
    null_values_count INT,
    null_percent DECIMAL(5,2),
    
    duplicate_rows INT,
    duplicate_percent DECIMAL(5,2),
    
    invalid_date_count INT,
    out_of_range_count INT,
    
    data_quality_score DECIMAL(5,2),
    issues_found INT,
    issues_resolved INT,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    UNIQUE KEY uk_table_date (table_name, check_date),
    KEY idx_quality (data_quality_score, check_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================================
-- INDEXES FOR PERFORMANCE
-- ============================================================================

-- Create composite indexes for common queries
CREATE INDEX idx_factory_date_composite ON machine_performance_daily(factory_id, performance_date, oee_percent);
CREATE INDEX idx_product_date_composite ON product_sales_performance(factory_id, product_id, sales_month);
CREATE INDEX idx_customer_date_composite ON sales_order_summary(factory_id, customer_id, summary_date);
CREATE INDEX idx_material_date_composite ON material_flow_daily(factory_id, material_id, flow_date);

-- ============================================================================
-- END OF REPORTING SCHEMA
-- ============================================================================
