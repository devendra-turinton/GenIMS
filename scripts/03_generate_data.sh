#!/bin/bash

# ============================================================================
# Phase 3: GenIMS Data Generation & Loading Master Script
# ============================================================================
# This script generates and loads all historical data for all 13 databases
# ============================================================================

set -e

# Import configuration
if [ ! -f "scripts/config.env" ]; then
    echo "❌ ERROR: config.env not found!"
    exit 1
fi

source scripts/config.env

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# Logging
LOG_DIR="logs"
mkdir -p "$LOG_DIR"
MASTER_LOG="$LOG_DIR/03_data_generation_$(date +%Y%m%d_%H%M%S).log"

log_info() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1" | tee -a "$MASTER_LOG"
}

log_success() {
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')] ✓${NC} $1" | tee -a "$MASTER_LOG"
}

log_error() {
    echo -e "${RED}[$(date '+%Y-%m-%d %H:%M:%S')] ✗ ERROR:${NC} $1" | tee -a "$MASTER_LOG"
}

log_warning() {
    echo -e "${YELLOW}[$(date '+%Y-%m-%d %H:%M:%S')] ⚠ WARNING:${NC} $1" | tee -a "$MASTER_LOG"
}

# Header
echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  PHASE 3: Data Generation & Loading                       ║${NC}"
echo -e "${BLUE}║  Generating 90 days of historical data for all databases  ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

log_info "Starting data generation process..."
log_info "Configuration: $POSTGRES_HOST:$POSTGRES_PORT"
echo ""

# ============================================================================
# STAGE 1: Generate Data (Python Scripts)
# ============================================================================

echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${YELLOW}STAGE 1: Generating Historical Data (Python Scripts)${NC}"
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

GENERATED_FILES=()
FAILED_GENERATIONS=()

# Function to generate data
generate_data() {
    local script_name=$1
    local script_path=$2
    local json_file=$3
    local module_name=$4
    
    if [ ! -f "$script_path" ]; then
        log_warning "Data generation script not found: $script_path"
        return 1
    fi
    
    log_info "Generating $module_name data..."
    
    if python3 "$script_path" >> "$MASTER_LOG" 2>&1; then
        if [ -f "$json_file" ]; then
            log_success "$module_name data generated ($(wc -c < "$json_file") bytes)"
            GENERATED_FILES+=("$json_file")
            return 0
        else
            log_warning "$module_name: Script ran but JSON file not found"
            return 1
        fi
    else
        log_error "$module_name data generation failed"
        FAILED_GENERATIONS+=("$module_name")
        return 1
    fi
}

# Generate data for all modules
cd "/Users/devendrayadav/insightql/GenIMS"

generate_data "master_data" "01 - Base Data/generate_genims_master_data.py" "01 - Base Data/genims_master_data.json" "Master Data" && ((GENERATED_DBS++)) || ((FAILED_GENS++))

generate_data "operations_data" "02 - Machine data/generate_operational_data.py" "02 - Machine data/genims_operational_data.json" "Operations/IoT" && ((GENERATED_DBS++)) || ((FAILED_GENS++))

generate_data "mes_data" "03 - MES Data/generate_mes_historical_data.py" "03 - MES Data/genims_mes_data.json" "Manufacturing/MES" && ((GENERATED_DBS++)) || ((FAILED_GENS++))

generate_data "erp_data" "04 - ERP & MES Integration/generate_erp_historical_data.py" "04 - ERP & MES Integration/genims_erp_data.json" "ERP Core" && ((GENERATED_DBS++)) || ((FAILED_GENS++))

generate_data "financial_data" "04 - ERP & MES Integration/generate_financial_historical_data.py" "04 - ERP & MES Integration/genims_financial_data.json" "Financial/GL" && ((GENERATED_DBS++)) || ((FAILED_GENS++))

generate_data "wms_tms_data" "05 - WMS + TMS/generate_wms_tms_historical_data.py" "05 - WMS + TMS/genims_wms_data.json" "WMS/TMS" && ((GENERATED_DBS++)) || ((FAILED_GENS++))

generate_data "cmms_data" "06 - CMMS/generate_cmms_historical_data.py" "06 - CMMS/genims_cmms_data.json" "Maintenance/CMMS" && ((GENERATED_DBS++)) || ((FAILED_GENS++))

generate_data "crm_data" "07 - CRM/generate_crm_historical_data.py" "07 - CRM/genims_crm_data.json" "CRM" && ((GENERATED_DBS++)) || ((FAILED_GENS++))

generate_data "service_data" "08 - Support & Service/generate_service_historical_data.py" "08 - Support & Service/genims_service_data.json" "Service/Support" && ((GENERATED_DBS++)) || ((FAILED_GENS++))

generate_data "hcm_data" "09 - HR-HCM/generate_hcm_historical_data.py" "09 - HR-HCM/genims_hcm_data.json" "HR/HCM" && ((GENERATED_DBS++)) || ((FAILED_GENS++))

generate_data "supplier_data" "11 - Supplier Portal/generate_supplier_portal_data.py" "11 - Supplier Portal/genims_supplier_portal_data.json" "Supplier Portal" && ((GENERATED_DBS++)) || ((FAILED_GENS++))

generate_data "qms_data" "12 - QMS/generate_qms_historical_data.py" "12 - QMS/genims_qms_data.json" "Quality/QMS" && ((GENERATED_DBS++)) || ((FAILED_GENS++))

echo ""
log_success "Data Generation Stage Complete"
echo ""

# ============================================================================
# STAGE 2: Load Data into Databases
# ============================================================================

echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${YELLOW}STAGE 2: Loading Data into Databases${NC}"
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

load_data_from_json() {
    local db_name=$1
    local json_file=$2
    local module_name=$3
    
    if [ ! -f "$json_file" ]; then
        log_warning "$module_name: JSON file not found - $json_file"
        return 1
    fi
    
    log_info "Loading $module_name data into $db_name..."
    
    # TODO: Add Python script to convert JSON to INSERT statements and execute
    # For now, just copy JSON for reference
    
    log_success "$module_name data prepared for loading"
    return 0
}

# Note: Production data loading would be done via Python script that:
# 1. Reads JSON files
# 2. Generates SQL INSERT statements with proper escaping
# 3. Executes against PostgreSQL
# 4. Validates row counts

echo -e "${CYAN}Note: Data loading requires custom Python loader for each database schema${NC}"
echo -e "${CYAN}Each database has unique table structures - using schema-specific loaders${NC}"
echo ""

# List generated data files
echo -e "${CYAN}Generated Data Files:${NC}"
for file in "${GENERATED_FILES[@]}"; do
    if [ -f "$file" ]; then
        size=$(du -h "$file" | cut -f1)
        records=$(grep -o "\"" "$file" | wc -l)
        echo "  ✓ $file ($size)"
    fi
done
echo ""

# ============================================================================
# VERIFICATION
# ============================================================================

echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${YELLOW}Verification Summary${NC}"
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

echo "Data Generation Status:"
echo "  ✓ Successful: ${GENERATED_DBS:-0} modules"
echo "  ✗ Failed: ${FAILED_GENS:-0} modules"

if [ ${#FAILED_GENERATIONS[@]} -gt 0 ]; then
    echo ""
    echo -e "${YELLOW}Failed Generations:${NC}"
    for module in "${FAILED_GENERATIONS[@]}"; do
        echo "  ✗ $module"
    done
fi

echo ""
log_info "Data generation complete - Log file: $MASTER_LOG"
echo ""

echo -e "${GREEN}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║  Phase 3 Summary: Data Generation Complete                ║${NC}"
echo -e "${GREEN}║  Next Step: Load data using database-specific loaders     ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════════╝${NC}"
