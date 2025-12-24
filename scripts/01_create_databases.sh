#!/bin/bash

################################################################################
# GenIMS PostgreSQL Database Creation Script
# Purpose: Drop existing databases (if exist) and create fresh databases
# Focus: Database creation phase only
# Version: 1.0
# Date: December 23, 2025
################################################################################

set -e  # Exit on error

# ============================================================================
# Configuration
# ============================================================================

# PostgreSQL Connection Parameters
POSTGRES_HOST="${POSTGRES_HOST:-insights-db.postgres.database.azure.com}"
POSTGRES_PORT="${POSTGRES_PORT:-5432}"
POSTGRES_USER="${POSTGRES_USER:-turintonadmin}"
POSTGRES_PASSWORD="${POSTGRES_PASSWORD:-}"

# Database Names - 13 Separate Databases per Module
DATABASES=(
    "genims_master_db"
    "genims_operations_db"
    "genims_manufacturing_db"
    "genims_maintenance_db"
    "genims_quality_db"
    "genims_erp_db"
    "genims_financial_db"
    "genims_wms_db"
    "genims_tms_db"
    "genims_crm_db"
    "genims_service_db"
    "genims_hr_db"
    "genims_supplier_db"
)

# ============================================================================
# Colors for Output
# ============================================================================

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# ============================================================================
# Functions
# ============================================================================

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if PostgreSQL connection is valid
check_postgres_connection() {
    log_info "Checking PostgreSQL connection..."
    
    if ! PGPASSWORD="$POSTGRES_PASSWORD" psql \
        -h "$POSTGRES_HOST" \
        -p "$POSTGRES_PORT" \
        -U "$POSTGRES_USER" \
        -d "postgres" \
        -c "SELECT 1" > /dev/null 2>&1; then
        log_error "Cannot connect to PostgreSQL at $POSTGRES_HOST:$POSTGRES_PORT"
        log_error "Check your connection parameters and ensure PostgreSQL is running"
        exit 1
    fi
    
    log_success "PostgreSQL connection successful"
}

# Drop database if it exists
drop_database() {
    local db_name=$1
    
    log_info "Checking if database '$db_name' exists..."
    
    # Check if database exists
    if PGPASSWORD="$POSTGRES_PASSWORD" psql \
        -h "$POSTGRES_HOST" \
        -p "$POSTGRES_PORT" \
        -U "$POSTGRES_USER" \
        -d "postgres" \
        -tc "SELECT 1 FROM pg_database WHERE datname = '$db_name'" | grep -q 1; then
        
        log_warning "Database '$db_name' exists. Dropping..."
        
        # Terminate all connections to the database
        PGPASSWORD="$POSTGRES_PASSWORD" psql \
            -h "$POSTGRES_HOST" \
            -p "$POSTGRES_PORT" \
            -U "$POSTGRES_USER" \
            -d "postgres" \
            -c "SELECT pg_terminate_backend(pg_stat_activity.pid) 
                FROM pg_stat_activity 
                WHERE pg_stat_activity.datname = '$db_name' 
                AND pid <> pg_backend_pid();" > /dev/null 2>&1
        
        # Drop the database
        PGPASSWORD="$POSTGRES_PASSWORD" dropdb \
            -h "$POSTGRES_HOST" \
            -p "$POSTGRES_PORT" \
            -U "$POSTGRES_USER" \
            "$db_name" 2>/dev/null
        
        log_success "Database '$db_name' dropped"
    else
        log_info "Database '$db_name' does not exist (no action needed)"
    fi
}

# Create database
create_database() {
    local db_name=$1
    
    log_info "Creating database '$db_name'..."
    
    PGPASSWORD="$POSTGRES_PASSWORD" createdb \
        -h "$POSTGRES_HOST" \
        -p "$POSTGRES_PORT" \
        -U "$POSTGRES_USER" \
        -E UTF8 \
        "$db_name"
    
    log_success "Database '$db_name' created successfully"
}

# ============================================================================
# Main Script
# =========================13 Separate Databases==============================

echo ""
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║        GenIMS PostgreSQL Database Creation Script             ║"
echo "║                                                                ║"
echo "║  Action: Drop existing databases + Create fresh databases     ║"
echo "║  Scope: Database creation only (Phase 1)                      ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Display configuration
echo -e "${BLUE}Configuration:${NC}"
echo "  PostgreSQL Host:  $POSTGRES_HOST"
echo "  PostgreSQL Port:  $POSTGRES_PORT"
echo "  PostgreSQL User:  $POSTGRES_USER"
echo "  Databases Count:  ${#DATABASES[@]}"
echo ""

# Check connection
check_postgres_connection

# Ask for confirmation
echo -e "${YELLOW}WARNING: This will DROP all existing GenIMS databases!${NC}"
echo ""
echo "Databases to be dropped and recreated:"
for db in "${DATABASES[@]}"; do
    echo "  - $db"
done
echo ""
read -p "Do you want to proceed? (yes/no): " confirmation

if [[ "$confirmation" != "yes" ]]; then
    log_warning "Operation cancelled by user"
    exit 0
fi

echo ""
log_info "Starting database creation process..."
echo ""

# Phase 1: Drop existing databases
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}PHASE 1: Dropping existing databases (if present)${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo ""

dropped_count=0
skipped_count=0

for db in "${DATABASES[@]}"; do
    if PGPASSWORD="$POSTGRES_PASSWORD" psql \
        -h "$POSTGRES_HOST" \
        -p "$POSTGRES_PORT" \
        -U "$POSTGRES_USER" \
        -d "postgres" \
        -tc "SELECT 1 FROM pg_database WHERE datname = '$db'" | grep -q 1; then
        
        drop_database "$db"
        ((dropped_count++))
    else
        log_info "Database '$db' does not exist (skipping)"
        ((skipped_count++))
    fi
done

echo ""
log_success "Phase 1 Complete: Dropped $dropped_count databases, Skipped $skipped_count"
echo ""

# Phase 2: Create new databases
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}PHASE 2: Creating new databases${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo ""

created_count=0

for db in "${DATABASES[@]}"; do
    create_database "$db"
    ((created_count++))
done

echo ""
log_success "Phase 2 Complete: Created $created_count databases"
echo ""

# Verification
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}PHASE 3: Verification${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo ""

log_info "Verifying all databases exist..."
echo ""

all_exist=true

for db in "${DATABASES[@]}"; do
    if PGPASSWORD="$POSTGRES_PASSWORD" psql \
        -h "$POSTGRES_HOST" \
        -p "$POSTGRES_PORT" \
        -U "$POSTGRES_USER" \
        -d "postgres" \
        -tc "SELECT 1 FROM pg_database WHERE datname = '$db'" | grep -q 1; then
        
        # Get database size
        size=$(PGPASSWORD="$POSTGRES_PASSWORD" psql \
            -h "$POSTGRES_HOST" \
            -p "$POSTGRES_PORT" \
            -U "$POSTGRES_USER" \
            -d "$db" \
            -tc "SELECT pg_size_pretty(pg_database_size('$db'))")
        
        log_success "✓ $db (Size: $size)"
    else
        log_error "✗ $db (MISSING)"
        all_exist=false
    fi
done

echo ""

if [ "$all_exist" = true ]; then
    log_success "All databases created successfully!"
    echo ""
    echo -e "${GREEN}═══════════════════════════════════════════════════════════════${NC}"
    echo -e "${GREEN}Database Creation Complete!${NC}"
    echo -e "${GREEN}═══════════════════════════════════════════════════════════════${NC}"
    echo ""
    echo "Next Steps:"
    echo "  1. Run: ./scripts/02_load_schemas.sh"
    echo "  2. Run: ./scripts/03_generate_data.sh"
    echo "  3. Run: ./scripts/04_start_daemons.sh"
    echo ""
    exit 0
else
    log_error "Some databases are missing!"
    echo ""
    echo -e "${RED}═══════════════════════════════════════════════════════════════${NC}"
    echo -e "${RED}Database Creation FAILED!${NC}"
    echo -e "${RED}═══════════════════════════════════════════════════════════════${NC}"
    echo ""
    exit 1
fi
