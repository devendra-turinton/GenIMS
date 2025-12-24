#!/bin/bash

################################################################################
# GenIMS PostgreSQL Schema Loading Script
# Purpose: Load schemas into all 13 databases
# Focus: Schema loading phase only (Phase 2)
# Version: 1.0
# Date: December 23, 2025
################################################################################

set -e

# ============================================================================
# Configuration
# ============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_FILE="$SCRIPT_DIR/config.env"
BASE_DIR="$(dirname "$SCRIPT_DIR")"

if [ -f "$CONFIG_FILE" ]; then
    source "$CONFIG_FILE"
else
    echo "Error: config.env not found at $CONFIG_FILE"
    exit 1
fi

# Logging directory
LOGS_DIR="$BASE_DIR/logs"
mkdir -p "$LOGS_DIR"

# ============================================================================
# Colors
# ============================================================================

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# ============================================================================
# Functions
# ============================================================================

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[✓]${NC} $1"
}

log_error() {
    echo -e "${RED}[✗]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

# Load schema function
load_schema() {
    local db_name=$1
    local schema_file=$2
    local description=$3
    
    if [ ! -f "$schema_file" ]; then
        log_error "Schema file not found: $schema_file"
        return 1
    fi
    
    log_info "Loading schema for $db_name from $(basename "$schema_file")..."
    
    if PGPASSWORD="$POSTGRES_PASSWORD" psql \
        -h "$POSTGRES_HOST" \
        -p "$POSTGRES_PORT" \
        -U "$POSTGRES_USER" \
        -d "$db_name" \
        -f "$schema_file" > "$LOGS_DIR/${db_name}_schema.log" 2>&1; then
        
        # Count tables
        table_count=$(PGPASSWORD="$POSTGRES_PASSWORD" psql \
            -h "$POSTGRES_HOST" \
            -p "$POSTGRES_PORT" \
            -U "$POSTGRES_USER" \
            -d "$db_name" \
            -tc "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='public'")
        
        log_success "$db_name loaded ($description) - $table_count tables"
        return 0
    else
        log_error "Failed to load schema for $db_name"
        tail -20 "$LOGS_DIR/${db_name}_schema.log"
        return 1
    fi
}

# ============================================================================
# Main Script
# ============================================================================

echo ""
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║          GenIMS PostgreSQL Schema Loading Script              ║"
echo "║                   Load Schemas Phase 2                         ║"
echo "║                                                                ║"
echo "║  Action: Load database schemas from SQL files                 ║"
echo "║  Databases: 13 (Master + 12 modules)                          ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Display configuration
echo -e "${CYAN}Configuration:${NC}"
echo "  PostgreSQL Host:  $POSTGRES_HOST"
echo "  PostgreSQL Port:  $POSTGRES_PORT"
echo "  PostgreSQL User:  $POSTGRES_USER"
echo "  Base Directory:   $BASE_DIR"
echo "  Logs Directory:   $LOGS_DIR"
echo ""

# Verify connection
log_info "Verifying PostgreSQL connection..."
if ! PGPASSWORD="$POSTGRES_PASSWORD" psql \
    -h "$POSTGRES_HOST" \
    -p "$POSTGRES_PORT" \
    -U "$POSTGRES_USER" \
    -d "postgres" \
    -c "SELECT 1" > /dev/null 2>&1; then
    log_error "Cannot connect to PostgreSQL"
    exit 1
fi
log_success "PostgreSQL connection verified"
echo ""

# Schema loading sequence
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}PHASE 1: Loading Master Data Schema (Foundation)${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo ""

# Master data schema (must be first)
if ! load_schema "$DB_MASTER" "$BASE_DIR/01 - Base Data/genims_schema.sql" "Master Data"; then
    log_error "Failed to load master database schema. Aborting."
    exit 1
fi

echo ""
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}PHASE 2: Loading All Module Schemas (Parallel)${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo ""

# Counter for tracking
TOTAL_DBS=12
LOADED_DBS=0
FAILED_DBS=0

# Load all other schemas in parallel
(
    load_schema "$DB_OPERATIONS" "$BASE_DIR/02 - Machine data/genims_operational_schema.sql" "Operations/IoT" && ((LOADED_DBS++)) || ((FAILED_DBS++))
) &
PID1=$!

(
    load_schema "$DB_MANUFACTURING" "$BASE_DIR/03 - MES Data/genims_mes_schema.sql" "Manufacturing (MES)" && ((LOADED_DBS++)) || ((FAILED_DBS++))
) &
PID2=$!

(
    load_schema "$DB_MAINTENANCE" "$BASE_DIR/06 - CMMS/genims_cmms_schema.sql" "Maintenance (CMMS)" && ((LOADED_DBS++)) || ((FAILED_DBS++))
) &
PID3=$!

(
    load_schema "$DB_QUALITY" "$BASE_DIR/12 - QMS/genims_qms.sql" "Quality (QMS)" && ((LOADED_DBS++)) || ((FAILED_DBS++))
) &
PID4=$!

(
    load_schema "$DB_ERP" "$BASE_DIR/04 - ERP & MES Integration/genims_erp_schema.sql" "ERP Core" && ((LOADED_DBS++)) || ((FAILED_DBS++))
) &
PID5=$!

(
    load_schema "$DB_FINANCIAL" "$BASE_DIR/04 - ERP & MES Integration/genims_financial_schema.sql" "Financial GL" && ((LOADED_DBS++)) || ((FAILED_DBS++))
) &
PID6=$!

(
    load_schema "$DB_WMS" "$BASE_DIR/05 - WMS + TMS/genims_wms_schema.sql" "Warehouse (WMS)" && ((LOADED_DBS++)) || ((FAILED_DBS++))
) &
PID7=$!

(
    load_schema "$DB_TMS" "$BASE_DIR/05 - WMS + TMS/genims_tms_schema.sql" "Transportation (TMS)" && ((LOADED_DBS++)) || ((FAILED_DBS++))
) &
PID8=$!

(
    load_schema "$DB_CRM" "$BASE_DIR/07 - CRM/genims_crm_schema.sql" "CRM Sales" && ((LOADED_DBS++)) || ((FAILED_DBS++))
) &
PID9=$!

(
    load_schema "$DB_SERVICE" "$BASE_DIR/08 - Support & Service/genims_service_schema.sql" "Service/Support" && ((LOADED_DBS++)) || ((FAILED_DBS++))
) &
PID10=$!

(
    load_schema "$DB_HR" "$BASE_DIR/09 - HR-HCM/genims_hcm_schema.sql" "HR/HCM" && ((LOADED_DBS++)) || ((FAILED_DBS++))
) &
PID11=$!

(
    load_schema "$DB_SUPPLIER" "$BASE_DIR/11 - Supplier Portal/genims_supplier_portal.sql" "Supplier Portal" && ((LOADED_DBS++)) || ((FAILED_DBS++))
) &
PID12=$!

# Wait for all background jobs
wait $PID1 $PID2 $PID3 $PID4 $PID5 $PID6 $PID7 $PID8 $PID9 $PID10 $PID11 $PID12

echo ""
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}PHASE 3: Verification${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo ""

log_info "Verifying all schemas loaded..."
echo ""

# Verify each database has tables
VERIFY_FAILED=0

for db_name in "$DB_MASTER" "$DB_OPERATIONS" "$DB_MANUFACTURING" "$DB_MAINTENANCE" "$DB_QUALITY" "$DB_ERP" "$DB_FINANCIAL" "$DB_WMS" "$DB_TMS" "$DB_CRM" "$DB_SERVICE" "$DB_HR" "$DB_SUPPLIER"; do
    table_count=$(PGPASSWORD="$POSTGRES_PASSWORD" psql \
        -h "$POSTGRES_HOST" \
        -p "$POSTGRES_PORT" \
        -U "$POSTGRES_USER" \
        -d "$db_name" \
        -tc "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='public'" 2>/dev/null || echo "0")
    
    if [ "$table_count" -gt 0 ]; then
        log_success "$db_name - $table_count tables"
    else
        log_error "$db_name - NO TABLES (schema load may have failed)"
        VERIFY_FAILED=$((VERIFY_FAILED + 1))
    fi
done

echo ""

if [ $VERIFY_FAILED -eq 0 ]; then
    echo -e "${GREEN}╔════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║  All schemas loaded successfully!                            ║${NC}"
    echo -e "${GREEN}║  13 databases ready for data generation                      ║${NC}"
    echo -e "${GREEN}╚════════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo "Next Steps:"
    echo "  1. Run: ./scripts/03_generate_data.sh"
    echo "  2. Run: ./scripts/04_start_daemons.sh"
    echo ""
    exit 0
else
    echo -e "${RED}╔════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${RED}║  Some schemas failed to load!                                 ║${NC}"
    echo -e "${RED}║  Check logs in $LOGS_DIR for details              ║${NC}"
    echo -e "${RED}╚════════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    exit 1
fi
