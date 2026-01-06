#!/usr/bin/env python3
"""
GenIMS Daemon Setup & Orchestrator

Unified control center for all daemon processes across GenIMS modules.
Supports all 11 databases with daemon scripts.

Usage:
    python3 scripts/daemon_setup.py GENERATE [--database operations|manufacturing|erp|wms|maintenance|crm|service|hr|financial|supplier|quality|ALL] [--verbose]
    python3 scripts/daemon_setup.py START [--database operations|manufacturing|erp|wms|maintenance|crm|service|hr|financial|supplier|quality|ALL] [--verbose]
    python3 scripts/daemon_setup.py STOP [--database operations|manufacturing|erp|wms|maintenance|crm|service|hr|financial|supplier|quality|ALL] [--verbose]
    python3 scripts/daemon_setup.py RESTART [--database operations|manufacturing|erp|wms|maintenance|crm|service|hr|financial|supplier|quality|ALL] [--verbose]
    python3 scripts/daemon_setup.py STATUS [--database operations|manufacturing|erp|wms|maintenance|crm|service|hr|financial|supplier|quality|ALL]
    
    # Most common: Generate batch data for all databases
    python3 scripts/daemon_setup.py GENERATE --database ALL
"""

import os
import sys
import argparse
import json
import subprocess
from pathlib import Path
from datetime import datetime   
from typing import List, Dict, Tuple
from dotenv import load_dotenv

# Add scripts directory to path
scripts_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, scripts_dir)

from daemon_manager import DaemonManager, DaemonConfig, DaemonStatus


class DaemonOrchestrator:
    """Orchestrates daemon lifecycle across all folders"""
    
    def __init__(self, verbose: bool = False):
        """Initialize orchestrator"""
        self.verbose = verbose
        self.base_path = Path(scripts_dir).parent.absolute()
        self.manager = DaemonManager(
            config_file=os.path.join(scripts_dir, "config.env"),
            verbose=verbose
        )
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "action": None,
            "folder": None,
            "started": [],
            "stopped": [],
            "failed": [],
            "status": []
        }
    
    def _log(self, message: str, level: str = "INFO"):
        """Log message with timestamp"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        prefix = {
            "INFO": "ℹ️  ",
            "SUCCESS": "✓ ",
            "ERROR": "✗ ",
            "WARN": "⚠️  "
        }.get(level, "")
        print(f"[{timestamp}] {prefix}{message}")
    
    def _load_config(self, database: str) -> Tuple[bool, DaemonConfig, List[str]]:
        """Load configuration for a database module"""
        
        # Database to folder mapping with daemon scripts
        database_mapping = {
            "operations": ("operations", "/Users/devendrayadav/insightql/GenIMS/Data Scripts/02 - Machine data", ["iot_daemon.py", "scada_daemon.py"]),
            "manufacturing": ("manufacturing", "/Users/devendrayadav/insightql/GenIMS/Data Scripts/03 - MES Data", ["mes_hourly_daemon.py"]),
            "erp": ("erp", "/Users/devendrayadav/insightql/GenIMS/Data Scripts/04 - ERP & MES Integration", ["erp_daily_daemon.py"]),
            "wms": ("wms", "/Users/devendrayadav/insightql/GenIMS/Data Scripts/05 - WMS + TMS", ["wms_tms_daemon.py"]),
            "maintenance": ("maintenance", "/Users/devendrayadav/insightql/GenIMS/Data Scripts/06 - CMMS", ["cmms_daemon.py"]),
            "crm": ("crm", "/Users/devendrayadav/insightql/GenIMS/Data Scripts/07 - CRM", ["crm_daemon.py"]),
            "service": ("service", "/Users/devendrayadav/insightql/GenIMS/Data Scripts/08 - Support & Service", ["service_daemon.py"]),
            "hr": ("hr", "/Users/devendrayadav/insightql/GenIMS/Data Scripts/09 - HR-HCM", ["hcm_daemon.py"]),
            "financial": ("financial", "/Users/devendrayadav/insightql/GenIMS/Data Scripts/10 - Financial Accounting & ERP <> WMS Sync", ["financial_sync_daemon.py"]),
            "supplier": ("supplier", "/Users/devendrayadav/insightql/GenIMS/Data Scripts/11 - Supplier Portal", ["supplier_portal_daemon.py"]),
            "quality": ("quality", "/Users/devendrayadav/insightql/GenIMS/Data Scripts/12 - QMS", ["qms_daemon.py"]),
            # Legacy folder number support
            "02": ("operations", "/Users/devendrayadav/insightql/GenIMS/Data Scripts/02 - Machine data", ["iot_daemon.py", "scada_daemon.py"]),
            "03": ("manufacturing", "/Users/devendrayadav/insightql/GenIMS/Data Scripts/03 - MES Data", ["mes_hourly_daemon.py"]),
            "04": ("erp", "/Users/devendrayadav/insightql/GenIMS/Data Scripts/04 - ERP & MES Integration", ["erp_daily_daemon.py"]),
            "05": ("wms", "/Users/devendrayadav/insightql/GenIMS/Data Scripts/05 - WMS + TMS", ["wms_tms_daemon.py"]),
            "06": ("maintenance", "/Users/devendrayadav/insightql/GenIMS/Data Scripts/06 - CMMS", ["cmms_daemon.py"]),
            "07": ("crm", "/Users/devendrayadav/insightql/GenIMS/Data Scripts/07 - CRM", ["crm_daemon.py"]),
            "08": ("service", "/Users/devendrayadav/insightql/GenIMS/Data Scripts/08 - Support & Service", ["service_daemon.py"]),
            "09": ("hr", "/Users/devendrayadav/insightql/GenIMS/Data Scripts/09 - HR-HCM", ["hcm_daemon.py"]),
            "10": ("financial", "/Users/devendrayadav/insightql/GenIMS/Data Scripts/10 - Financial Accounting & ERP <> WMS Sync", ["financial_sync_daemon.py"]),
            "11": ("supplier", "/Users/devendrayadav/insightql/GenIMS/Data Scripts/11 - Supplier Portal", ["supplier_portal_daemon.py"]),
            "12": ("quality", "/Users/devendrayadav/insightql/GenIMS/Data Scripts/12 - QMS", ["qms_daemon.py"])
        }
        
        db_key = database.lower()
        if db_key not in database_mapping:
            return False, None, [f"Database '{database}' not found in mapping"]
        
        module_name, folder_path, daemon_scripts = database_mapping[db_key]
        self.current_scripts = daemon_scripts
        self.current_folder = folder_path
        config = self.manager.load_daemon_config(folder_path, module_name)
        
        if not config.enabled:
            return False, config, [f"Database '{database}' is disabled in configuration"]
        
        return True, config, []
    
    def _get_all_databases(self) -> List[str]:
        """Get list of all supported database modules"""
        return ["operations", "manufacturing", "erp", "wms", "maintenance", "crm", "service", "hr", "financial", "supplier", "quality"]
    
    def _execute_script(self, script_path: str, script_name: str) -> Dict:
        """Execute a daemon script and parse its output"""
        import re
        from datetime import datetime
        
        result = {
            "script": script_name,
            "success": False,
            "execution_time": 0.0,
            "tables": {},
            "total_records": 0,
            "exit_code": -1,
            "error": None
        }
        
        self._log(f"\n>>> Executing: {script_name}", "INFO")
        start_time = datetime.now()
        
        try:
            # Run the script with real-time output streaming
            process = subprocess.Popen(
                [sys.executable, script_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                cwd=os.path.dirname(script_path),
                bufsize=1,  # Line buffered
                universal_newlines=True
            )
            
            output_lines = []
            # Stream output in real-time
            for line in process.stdout:
                line = line.rstrip()
                if line:  # Only print non-empty lines
                    print(f"    {line}")
                    output_lines.append(line)
            
            # Wait for completion
            return_code = process.wait(timeout=600)
            result["exit_code"] = return_code
            output = "\n".join(output_lines)
            
            # Parse execution time
            time_match = re.search(r'Execution Time:\s*([\d.]+)\s*seconds', output)
            if time_match:
                result["execution_time"] = float(time_match.group(1))
            else:
                result["execution_time"] = (datetime.now() - start_time).total_seconds()
            
            # Parse records inserted - try multiple patterns
            # Pattern 1: Table format with padding (Before: X | After: Y | Inserted: Z)
            records_pattern = r'(\w+).*?Before:\s*([\d,]+)\s*\|\s*After:\s*([\d,]+)\s*\|\s*Inserted:\s*([\d,]+)'
            for match in re.finditer(records_pattern, output):
                table, before, after, inserted = match.groups()
                # Convert comma-separated numbers to integers
                inserted_count = int(inserted.replace(',', ''))
                result["tables"][table] = inserted_count
                result["total_records"] += inserted_count
            
            # Pattern 2: Direct records inserted (from daemon scripts)
            # Matches: "📊 Records inserted: 86,400" or "Records inserted: 86400"
            if result["total_records"] == 0:  # Only if not already found
                records_direct_pattern = r'Records inserted:\s*([\d,]+)'
                for match in re.finditer(records_direct_pattern, output):
                    inserted_str = match.group(1).replace(',', '')
                    result["total_records"] += int(inserted_str)
            
            # Check success
            if return_code == 0:
                result["success"] = True
                self._log(f"\n✓ {script_name} completed in {result['execution_time']:.2f}s ({result['total_records']} records)", "SUCCESS")
            else:
                result["error"] = "Script failed with non-zero exit code"
                self._log(f"\n✗ {script_name} failed with exit code {return_code}", "ERROR")
        
        except subprocess.TimeoutExpired:
            result["error"] = "Script execution timeout (10 minutes)"
            self._log(f"\n✗ {script_name} timed out", "ERROR")
            if process:
                process.kill()
        except Exception as e:
            result["error"] = str(e)
            self._log(f"\n✗ {script_name} error: {e}", "ERROR")
        
        return result
    
    def generate(self, database: str = "operations") -> bool:
        """Execute batch generation for a database module or ALL databases"""
        if database.upper() == "ALL":
            self._log(f"\n{'='*70}", "INFO")
            self._log(f"Batch Data Generation - ALL Databases", "INFO")
            self._log(f"{'='*70}", "INFO")
            return self._generate_all()
        
        return self._generate_single(database)
    
    def _generate_single(self, database: str) -> bool:
        """Execute batch generation for a single database"""
        self.results["action"] = "GENERATE"
        self.results["folder"] = database
        
        self._log(f"\n{'='*70}", "INFO")
        self._log(f"Batch Data Generation - {database.upper()}", "INFO")
        self._log(f"{'='*70}", "INFO")
        
        # Load configuration
        success, config, errors = self._load_config(database)
        if not success:
            for error in errors:
                self._log(error, "ERROR")
                self.results["failed"].append(error)
            return False
        
        # Execute each script
        db_results = []
        for script_name in self.current_scripts:
            script_path = os.path.join(self.current_folder, script_name)
            
            if not os.path.exists(script_path):
                self._log(f"✗ Script not found: {script_path}", "ERROR")
                continue
            
            result = self._execute_script(script_path, script_name)
            db_results.append(result)
        
        # Store results
        self.results["scripts"] = db_results
        self.results["total_time"] = sum(r["execution_time"] for r in db_results)
        self.results["total_records"] = sum(r["total_records"] for r in db_results)
        self.results["status"] = "SUCCESS" if all(r["success"] for r in db_results) else "PARTIAL" if any(r["success"] for r in db_results) else "FAILED"
        
        # Print summary
        self._print_generate_summary(database, db_results)
        
        return self.results["status"] in ["SUCCESS", "PARTIAL"]
    
    def _generate_all(self) -> bool:
        """Execute batch generation for all databases"""
        all_databases = self._get_all_databases()
        all_results = {}
        overall_start = datetime.now()
        
        for db in all_databases:
            self._log(f"\n{'='*70}", "INFO")
            self._log(f"Processing: {db.upper()}", "INFO")
            self._log(f"{'='*70}", "INFO")
            
            # Reset results for each database
            self.results = {
                "timestamp": datetime.now().isoformat(),
                "action": "GENERATE",
                "folder": db,
                "started": [],
                "stopped": [],
                "failed": [],
                "status": []
            }
            
            success = self._generate_single(db)
            all_results[db] = {
                "success": success,
                "scripts": self.results.get("scripts", []),
                "total_time": self.results.get("total_time", 0),
                "total_records": self.results.get("total_records", 0),
                "status": self.results.get("status", "FAILED")
            }
        
        # Print overall summary
        overall_time = (datetime.now() - overall_start).total_seconds()
        self._print_overall_summary(all_results, overall_time)
        
        return any(r["success"] for r in all_results.values())
    
    def _print_generate_summary(self, database: str, results: List[Dict]):
        """Print summary for single database generation"""
        self._log(f"\n{'='*70}", "INFO")
        self._log(f"Generation Summary - {database.upper()}", "INFO")
        self._log(f"{'='*70}", "INFO")
        
        total_time = sum(r["execution_time"] for r in results)
        total_records = sum(r["total_records"] for r in results)
        success_count = sum(1 for r in results if r["success"])
        
        for result in results:
            status_icon = "✓" if result["success"] else "✗"
            self._log(f"{status_icon} {result['script']}: {result['total_records']} records in {result['execution_time']:.2f}s", 
                     "SUCCESS" if result["success"] else "ERROR")
            
            if self.verbose and result["tables"]:
                for table, count in result["tables"].items():
                    self._log(f"    {table}: {count}", "INFO")
        
        self._log(f"\nTotal Execution Time: {total_time:.2f}s", "INFO")
        self._log(f"Total Records Inserted: {total_records:,}", "INFO")
        self._log(f"Scripts: {success_count}/{len(results)} successful", 
                 "SUCCESS" if success_count == len(results) else "WARN")
        self._log(f"{'='*70}\n", "INFO")
    
    def _print_overall_summary(self, all_results: Dict, overall_time: float):
        """Print overall summary for all databases"""
        self._log(f"\n{'='*80}", "INFO")
        self._log(f"OVERALL BATCH GENERATION SUMMARY", "INFO")
        self._log(f"{'='*80}", "INFO")
        
        total_records = 0
        total_scripts = 0
        success_scripts = 0
        
        for db, result in all_results.items():
            status_icon = "✓" if result["status"] == "SUCCESS" else "⚠️" if result["status"] == "PARTIAL" else "✗"
            self._log(f"{status_icon} {db.upper()}: {result['total_records']:,} records in {result['total_time']:.2f}s", 
                     "SUCCESS" if result["status"] == "SUCCESS" else "WARN")
            
            total_records += result["total_records"]
            total_scripts += len(result["scripts"])
            success_scripts += sum(1 for s in result["scripts"] if s["success"])
        
        self._log(f"\n{'='*80}", "INFO")
        self._log(f"Total Execution Time: {overall_time:.2f}s ({overall_time/60:.2f} minutes)", "INFO")
        self._log(f"Total Records Inserted: {total_records:,}", "SUCCESS")
        self._log(f"Total Scripts Executed: {success_scripts}/{total_scripts} successful", 
                 "SUCCESS" if success_scripts == total_scripts else "WARN")
        self._log(f"Databases Processed: {len(all_results)}", "INFO")
        self._log(f"{'='*80}\n", "INFO")
    
    def _run_sequence_fix(self) -> None:
        """Run automated sequence synchronization before starting daemons"""
        self._log(f"\n{'='*70}", "INFO")
        self._log("Running Sequence Synchronization Check...", "INFO")
        self._log(f"{'='*70}", "INFO")
        
        try:
            # Path to auto_fix_sequences.py
            fix_script = os.path.join(self.base_path, "scripts", "auto_fix_sequences.py")
            
            if not os.path.exists(fix_script):
                self._log(f"Sequence fix script not found: {fix_script}", "WARNING")
                return
            
            # Run the auto-fix script
            result = subprocess.run(
                [sys.executable, fix_script],
                capture_output=True,
                text=True,
                cwd=self.base_path
            )
            
            if result.returncode == 0:
                # Parse output for summary
                output_lines = result.stdout.strip().split('\n')
                for line in output_lines:
                    if "Total sequences checked:" in line or "Total sequences fixed:" in line or "Successfully fixed" in line:
                        self._log(line, "SUCCESS")
                    elif "WARNING" in line or "Error" in line:
                        self._log(line, "WARNING")
                    elif line.strip() and not line.startswith("Checking") and not line.startswith("---"):
                        self._log(line, "INFO")
            else:
                self._log(f"Sequence fix script failed with return code {result.returncode}", "ERROR")
                if result.stderr:
                    self._log(f"Error output: {result.stderr}", "ERROR")
                    
        except Exception as e:
            self._log(f"Error running sequence fix: {e}", "WARNING")
            self._log("Continuing with daemon startup...", "INFO")
    
    def _process_databases(self, databases: List[str], action_func) -> bool:
        """Process action for multiple databases"""
        all_success = True
        for database in databases:
            try:
                success = action_func(database)
                if not success:
                    all_success = False
            except Exception as e:
                self._log(f"Error processing database {database}: {e}", "ERROR")
                all_success = False
        return all_success
    
    def start(self, database: str = "operations") -> bool:
        """Start all daemons for a database module or ALL databases"""
        # Run sequence synchronization check/fix before starting daemons
        self._run_sequence_fix()
        
        # Handle ALL databases
        if database.upper() == "ALL":
            self._log(f"\n{'='*70}", "INFO")
            self._log(f"Starting ALL Daemon Services (All Databases)", "INFO")
            self._log(f"{'='*70}", "INFO")
            return self._process_databases(self._get_all_databases(), self._start_single)
        
        return self._start_single(database)
    
    def _start_single(self, database: str) -> bool:
        """Start all daemons for a single database module"""
        self.results["action"] = "START"
        self.results["folder"] = database
        
        self._log(f"\n{'='*70}", "INFO")
        self._log(f"Starting Daemon Services - {database.upper()}", "INFO")
        self._log(f"{'='*70}", "INFO")
        
        # Load configuration
        success, config, errors = self._load_config(database)
        if not success:
            for error in errors:
                self._log(error, "ERROR")
                self.results["failed"].append(error)
            return False
        
        # Validate prerequisites
        self._log(f"\n>>> Validating prerequisites...", "INFO")
        prereq_success, prereq_errors = self.manager.validate_prerequisites(config)
        
        if not prereq_success:
            self._log("Prerequisites validation FAILED:", "ERROR")
            for error in prereq_errors:
                self._log(f"  ✗ {error}", "ERROR")
                self.results["failed"].append(error)
            return False
        else:
            self._log("Prerequisites validation PASSED", "SUCCESS")
        
        # Start each daemon
        self._log(f"\n>>> Starting daemons...", "INFO")
        for daemon_name in config.daemons:
            success, message = self.manager.start_daemon(config, daemon_name)
            
            if success:
                self._log(message, "SUCCESS")
                self.results["started"].append({
                    "daemon": daemon_name,
                    "status": "started",
                    "timestamp": datetime.now().isoformat()
                })
            else:
                self._log(message, "ERROR")
                self.results["failed"].append(message)
        
        # Verify health
        self._log(f"\n>>> Verifying daemon health...", "INFO")
        self._verify_health(config)
        
        # Print summary
        self._print_summary()
        return len(self.results["failed"]) == 0
    
    def stop(self, database: str = "operations") -> bool:
        """Stop all daemons for a database module or ALL databases"""
        # Handle ALL databases
        if database.upper() == "ALL":
            self._log(f"\n{'='*70}", "INFO")
            self._log(f"Stopping ALL Daemon Services (All Databases)", "INFO")
            self._log(f"{'='*70}", "INFO")
            return self._process_databases(self._get_all_databases(), self._stop_single)
        
        return self._stop_single(database)
    
    def _stop_single(self, database: str) -> bool:
        """Stop all daemons for a single database module"""
        self.results["action"] = "STOP"
        self.results["folder"] = database
        
        self._log(f"\n{'='*70}", "INFO")
        self._log(f"Stopping Daemon Services - {database.upper()}", "INFO")
        self._log(f"{'='*70}", "INFO")
        
        # Load configuration
        success, config, errors = self._load_config(database)
        if not success:
            for error in errors:
                self._log(error, "ERROR")
                self.results["failed"].append(error)
            return False
        
        grace_period = int(os.getenv("DAEMON_GRACE_PERIOD", "30"))
        
        # Stop each daemon
        self._log(f"\n>>> Stopping daemons (grace period: {grace_period}s)...", "INFO")
        for daemon_name in config.daemons:
            success, message = self.manager.stop_daemon(daemon_name, grace_period)
            
            if success:
                self._log(message, "SUCCESS")
                self.results["stopped"].append({
                    "daemon": daemon_name,
                    "status": "stopped",
                    "timestamp": datetime.now().isoformat()
                })
            else:
                self._log(message, "WARN")
                self.results["failed"].append(message)
        
        # Print summary
        self._print_summary()
        return len(self.results["failed"]) == 0
    
    def restart(self, database: str = "operations") -> bool:
        """Restart all daemons for a database module or ALL databases"""
        # Handle ALL databases
        if database.upper() == "ALL":
            self._log(f"\n{'='*70}", "INFO")
            self._log(f"Restarting ALL Daemon Services (All Databases)", "INFO")
            self._log(f"{'='*70}", "INFO")
            
            # Stop all first
            self._log("\n>>> Phase 1: Stopping all daemons...", "INFO")
            stop_success = self._process_databases(self._get_all_databases(), self._stop_single)
            
            # Wait between stop and start
            import time
            restart_delay = int(os.getenv("DAEMON_RESTART_DELAY", "5"))
            self._log(f"\n>>> Waiting {restart_delay} seconds before restart...", "INFO")
            time.sleep(restart_delay)
            
            # Start all
            self._log("\n>>> Phase 2: Starting all daemons...", "INFO")
            start_success = self._process_databases(self._get_all_databases(), self._start_single)
            
            return stop_success and start_success
        
        self.results["action"] = "RESTART"
        self.results["folder"] = database
        
        self._log(f"\n{'='*70}", "INFO")
        self._log(f"Restarting Daemon Services - {database.upper()}", "INFO")
        self._log(f"{'='*70}", "INFO")
        
        # Stop
        self._log("\n>>> Phase 1: Stopping...", "INFO")
        stop_success = self.stop(database)
        
        # Wait between stop and start
        import time
        restart_delay = int(os.getenv("DAEMON_RESTART_DELAY", "5"))
        self._log(f"\n>>> Waiting {restart_delay} seconds before restart...", "INFO")
        time.sleep(restart_delay)
        
        # Start
        self._log("\n>>> Phase 2: Starting...", "INFO")
        start_success = self.start(database)
        
        return stop_success and start_success
    
    def status(self, database: str = "operations") -> bool:
        """Get status of all daemons for a database module or ALL databases"""
        # Handle ALL databases
        if database.upper() == "ALL":
            self._log(f"\n{'='*70}", "INFO")
            self._log(f"Status of ALL Daemon Services (All Databases)", "INFO")
            self._log(f"{'='*70}", "INFO")
            return self._process_databases(self._get_all_databases(), self._status_single)
        
        return self._status_single(database)
    
    def _status_single(self, database: str) -> bool:
        """Get status of all daemons for a single database module"""
        self.results["action"] = "STATUS"
        self.results["folder"] = database
        
        # Load configuration
        success, config, errors = self._load_config(database)
        if not success:
            for error in errors:
                self._log(error, "ERROR")
            return False
        
        # Get status for each daemon
        statuses = []
        for daemon_name in config.daemons:
            status = self.manager.get_daemon_status(daemon_name, config)
            statuses.append(status)
            self.results["status"].append({
                "daemon": daemon_name,
                "is_running": status.is_running,
                "pid": status.pid,
                "cpu_percent": status.cpu_percent,
                "memory_mb": status.memory_mb,
                "uptime_seconds": status.uptime_seconds
            })
        
        # Print report
        self.manager.print_status_report(config, statuses)
        return True
    
    def _verify_health(self, config: DaemonConfig):
        """Verify health of daemons after startup"""
        import time
        time.sleep(2)  # Give daemons time to stabilize
        
        statuses = []
        for daemon_name in config.daemons:
            status = self.manager.get_daemon_status(daemon_name, config)
            statuses.append(status)
            
            if status.is_running:
                self._log(f"{daemon_name}: RUNNING (PID: {status.pid})", "SUCCESS")
            else:
                self._log(f"{daemon_name}: NOT RUNNING", "ERROR")
                self.results["failed"].append(f"{daemon_name} failed to start")
        
        self.results["status"] = [
            {
                "daemon": s.name,
                "is_running": s.is_running,
                "pid": s.pid,
                "cpu_percent": s.cpu_percent,
                "memory_mb": s.memory_mb
            }
            for s in statuses
        ]
    
    def _print_summary(self):
        """Print operation summary"""
        self._log(f"\n{'='*70}", "INFO")
        self._log(f"Operation Summary: {self.results['action']}", "INFO")
        self._log(f"{'='*70}", "INFO")
        
        action = self.results["action"]
        
        if action in ["START", "RESTART"]:
            self._log(f"Started:  {len(self.results['started'])} daemons", 
                     "SUCCESS" if len(self.results["started"]) > 0 else "WARN")
            for item in self.results["started"]:
                self._log(f"  ✓ {item['daemon']}", "INFO")
        
        if action in ["STOP", "RESTART"]:
            self._log(f"Stopped:  {len(self.results['stopped'])} daemons", 
                     "SUCCESS" if len(self.results["stopped"]) > 0 else "WARN")
            for item in self.results["stopped"]:
                self._log(f"  ✓ {item['daemon']}", "INFO")
        
        if self.results["failed"]:
            self._log(f"Failed:   {len(self.results['failed'])} operations", "ERROR")
            for error in self.results["failed"]:
                self._log(f"  ✗ {error}", "INFO")
        else:
            self._log(f"Failed:   0 operations", "SUCCESS")
        
        self._log(f"{'='*70}\n", "INFO")


def main():
    """Main entry point"""
    # Load config.env before processing
    config_env = os.path.join(scripts_dir, "config.env")
    if os.path.exists(config_env):
        load_dotenv(config_env)
    
    parser = argparse.ArgumentParser(
        description="GenIMS Daemon Setup & Orchestrator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Batch Data Generation (Most Common):
  python3 scripts/daemon_setup.py GENERATE --database ALL
  python3 scripts/daemon_setup.py GENERATE --database operations
  python3 scripts/daemon_setup.py GENERATE --database wms --verbose
  
  # Daemon Management (Legacy):
  python3 scripts/daemon_setup.py START --database operations
  python3 scripts/daemon_setup.py STOP --database manufacturing
  python3 scripts/daemon_setup.py STATUS --database ALL
  
  # Legacy folder number support:
  python3 scripts/daemon_setup.py GENERATE --folder 02
  python3 scripts/daemon_setup.py GENERATE --folder ALL
        """
    )
    
    parser.add_argument(
        "action",
        choices=["GENERATE", "START", "STOP", "RESTART", "STATUS"],
        help="Action to perform (GENERATE for batch data generation, others for daemon management)"
    )
    
    parser.add_argument(
        "--database",
        default=None,
        help="Database module to target (operations|manufacturing|erp|wms|maintenance|crm|service|hr|financial|supplier|quality|ALL)"
    )
    
    parser.add_argument(
        "--folder",
        default=None,
        help="Legacy: Folder number to target (02-12|ALL). Use --database instead."
    )
    
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose output"
    )
    
    args = parser.parse_args()
    
    # Determine target (database takes precedence, folder is legacy fallback)
    target = args.database if args.database else (args.folder if args.folder else "operations")
    
    # Create orchestrator
    orchestrator = DaemonOrchestrator(verbose=args.verbose)
    
    # Execute action
    action = args.action.lower()
    
    if action == "generate":
        success = orchestrator.generate(target)
    elif action == "start":
        success = orchestrator.start(target)
    elif action == "stop":
        success = orchestrator.stop(target)
    elif action == "restart":
        success = orchestrator.restart(target)
    elif action == "status":
        success = orchestrator.status(target)
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
