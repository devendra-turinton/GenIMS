#!/bin/bash
#
# GenIMS Streaming Daemons Startup Script
# Starts both IoT and SCADA daemons for continuous data streaming
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_DIR="${SCRIPT_DIR}/logs"

# Create log directory
mkdir -p "${LOG_DIR}"

echo "================================================================================"
echo "GenIMS Streaming Daemons"
echo "================================================================================"
echo ""
echo "This script will start two daemons:"
echo "  1. IoT Daemon - Sensor data streaming (every 10 seconds)"
echo "  2. SCADA Daemon - Machine operational data streaming (every 60 seconds)"
echo ""
echo "Logs will be written to: ${LOG_DIR}"
echo ""
echo "Prerequisites:"
echo "  - PostgreSQL database 'genims_db' created and schema loaded"
echo "  - Kafka broker running on localhost:9092 (optional)"
echo "  - Python packages: psycopg2-binary, kafka-python, numpy"
echo ""
echo "Install dependencies:"
echo "  pip install psycopg2-binary kafka-python numpy"
echo ""
echo "Press Ctrl+C to stop both daemons"
echo "================================================================================"
echo ""

# Check if master data exists
if [ ! -f "${SCRIPT_DIR}/genims_master_data.json" ]; then
    echo "ERROR: Master data file not found!"
    echo "Please run generate_genims_master_data.py first to create master data."
    exit 1
fi

# Function to handle cleanup
cleanup() {
    echo ""
    echo "Stopping daemons..."
    kill $IOT_PID $SCADA_PID 2>/dev/null || true
    wait
    echo "Daemons stopped"
    exit 0
}

trap cleanup SIGINT SIGTERM

# Start IoT Daemon
echo "Starting IoT Daemon..."
python3 "${SCRIPT_DIR}/iot_daemon.py" > "${LOG_DIR}/iot_daemon.log" 2>&1 &
IOT_PID=$!
echo "  PID: ${IOT_PID}"
echo "  Log: ${LOG_DIR}/iot_daemon.log"

sleep 2

# Start SCADA Daemon  
echo "Starting SCADA Daemon..."
python3 "${SCRIPT_DIR}/scada_daemon.py" > "${LOG_DIR}/scada_daemon.log" 2>&1 &
SCADA_PID=$!
echo "  PID: ${SCADA_PID}"
echo "  Log: ${LOG_DIR}/scada_daemon.log"

echo ""
echo "Both daemons are now running!"
echo ""
echo "Monitor logs with:"
echo "  tail -f ${LOG_DIR}/iot_daemon.log"
echo "  tail -f ${LOG_DIR}/scada_daemon.log"
echo ""
echo "Press Ctrl+C to stop"
echo "================================================================================"

# Wait for both processes
wait $IOT_PID $SCADA_PID
