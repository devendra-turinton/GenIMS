#!/bin/bash

echo "╔═════════════════════════════════════════════════════════════════════════╗"
echo "║ GenIMS DATA GENERATION - All Modules                                   ║"
echo "╚═════════════════════════════════════════════════════════════════════════╝"
echo ""

FOLDERS=(
    "01 - Base Data"
    "02 - Machine data"
    "03 - MES Data"
    "04 - ERP & MES Integration"
    "05 - WMS + TMS"
    "06 - CMMS"
    "07 - CRM"
    "08 - Support & Service"
    "09 - HR-HCM"
    "11 - Supplier Portal"
    "12 - QMS"
)

GENERATORS=(
    "generate_genims_master_data.py"
    "generate_operational_data.py"
    "generate_mes_historical_data.py"
    "generate_erp_historical_data.py"
    "generate_wms_tms_historical_data.py"
    "generate_cmms_historical_data.py"
    "generate_crm_historical_data.py"
    "generate_service_historical_data.py"
    "generate_hcm_historical_data.py"
    "generate_supplier_portal_data.py"
    "generate_qms_data.py"
)

for i in "${!FOLDERS[@]}"; do
    folder="${FOLDERS[$i]}"
    generator="${GENERATORS[$i]}"
    
    echo "[$(($i + 1))/11] Running $generator in '$folder'..."
    echo ""
    
    cd "$folder"
    python3 "$generator" 2>&1 | tail -5
    echo ""
    
    cd - > /dev/null
    echo ""
done

echo "╔═════════════════════════════════════════════════════════════════════════╗"
echo "✓ All generators completed!"
echo "╚═════════════════════════════════════════════════════════════════════════╝"
echo ""

