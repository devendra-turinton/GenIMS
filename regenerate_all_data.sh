#!/bin/bash
echo "════════════════════════════════════════════════════════"
echo "Regenerating all 11 data generator JSON files..."
echo "════════════════════════════════════════════════════════"
echo ""

cd /Users/devendrayadav/insightql/GenIMS

echo "[1/11] Master Data..."
python3 "01 - Base Data/generate_genims_master_data.py" > /dev/null 2>&1 && echo "  ✓ Complete"

echo "[2/11] Operational Data..."
python3 "02 - Machine data/generate_operational_data.py" > /dev/null 2>&1 && echo "  ✓ Complete"

echo "[3/11] MES Data..."
python3 "03 - MES Data/generate_mes_historical_data.py" > /dev/null 2>&1 && echo "  ✓ Complete"

echo "[4/11] ERP Data..."
python3 "04 - ERP & MES Integration/generate_erp_historical_data.py" > /dev/null 2>&1 && echo "  ✓ Complete"

echo "[5/11] QMS Data..."
python3 "12 - QMS/generate_qms_data.py" > /dev/null 2>&1 && echo "  ✓ Complete"

echo "[6/11] CMMS Data..."
python3 "06 - CMMS/generate_cmms_historical_data.py" > /dev/null 2>&1 && echo "  ✓ Complete"

echo "[7/11] CRM Data..."
python3 "07 - CRM/generate_crm_historical_data.py" > /dev/null 2>&1 && echo "  ✓ Complete"

echo "[8/11] Service Data..."
python3 "08 - Support & Service/generate_service_historical_data.py" > /dev/null 2>&1 && echo "  ✓ Complete"

echo "[9/11] HCM Data..."
python3 "09 - HR-HCM/generate_hcm_historical_data.py" > /dev/null 2>&1 && echo "  ✓ Complete"

echo "[10/11] WMS+TMS Data..."
python3 "05 - WMS + TMS/generate_wms_tms_historical_data.py" > /dev/null 2>&1 && echo "  ✓ Complete"

echo "[11/11] Supplier Portal Data..."
python3 "11 - Supplier Portal/generate_supplier_portal_data.py" > /dev/null 2>&1 && echo "  ✓ Complete"

echo ""
echo "════════════════════════════════════════════════════════"
echo "All JSON files regenerated successfully!"
echo "════════════════════════════════════════════════════════"
echo ""
echo "Starting full pipeline..."
echo ""
python3 genims_postgres_manager.py
