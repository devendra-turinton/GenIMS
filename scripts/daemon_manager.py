#!/usr/bin/env python3
"""
GenIMS Daemon Manager

Provides utility classes for managing daemon processes, configuration, and health monitoring.
Used by daemon_setup.py orchestrator.
"""

import os
import sys
import json
import subprocess
import psutil
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from dotenv import load_dotenv

@dataclass
class DaemonConfig:
    """Daemon configuration container"""
    folder_name: str
    folder_path: str
    database: str
    daemons: List[str]
    enabled: bool
    pg_host: str
    pg_port: str
    pg_user: str
    pg_password: str
    pg_ssl_mode: str = "require"
    log_dir: str = ""
    log_level: str = "INFO"
    pid_dir: str = ""

@dataclass
class DaemonStatus:
    """Daemon process status information"""
    name: str
    is_running: bool
    pid: Optional[int] = None
    cpu_percent: float = 0.0
    memory_mb: float = 0.0
    uptime_seconds: float = 0.0
    last_check: str = ""


class DaemonManager:
    """Manages daemon configuration, lifecycle, and monitoring"""
    
    def __init__(self, config_file: str = None, verbose: bool = False):
        """
        Initialize DaemonManager
        
        Args:
            config_file: Path to config.env file
            verbose: Enable verbose logging
        """
        self.verbose = verbose
        self.config = {}
        self.status_cache = {}
        self.pids = {}
        
        # Load environment from config.env
        if config_file and os.path.exists(config_file):
            load_dotenv(config_file)
        else:
            # Look for config.env in scripts directory
            scripts_dir = os.path.dirname(os.path.abspath(__file__))
            default_config = os.path.join(scripts_dir, "config.env")
            if os.path.exists(default_config):
                load_dotenv(default_config)
        
        # Create necessary directories
        self._create_directories()
    
    def _log(self, message: str):
        """Log message if verbose enabled"""
        if self.verbose:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(f"[{timestamp}] {message}")
    
    def _create_directories(self):
        """Create necessary directories from config"""
        # Resolve environment variable paths
        base_dir = os.getenv("BASE_DIR", "/tmp/genims")
        logs_dir = os.getenv("DAEMON_LOG_DIR", os.path.join(base_dir, "logs"))
        pid_dir = os.getenv("DAEMON_PID_DIR", os.path.join(base_dir, ".daemon_pids"))
        
        # Replace variable references
        logs_dir = logs_dir.replace("$BASE_DIR", base_dir).replace("$LOGS_DIR", logs_dir)
        pid_dir = pid_dir.replace("$BASE_DIR", base_dir).replace("$LOGS_DIR", logs_dir)
        
        dirs_to_create = [logs_dir, pid_dir]
        
        for dir_path in dirs_to_create:
            if dir_path:
                os.makedirs(dir_path, exist_ok=True)
                self._log(f"Created directory: {dir_path}")
    
    def load_daemon_config(self, folder_path: str, module_name: str = "operations") -> DaemonConfig:
        """
        Load daemon configuration for a module
        
        Args:
            folder_path: Path to daemon folder
            module_name: Module identifier (e.g., "operations", "manufacturing", "erp")
            
        Returns:
            DaemonConfig object
        """
        config_key = f"{module_name.upper()}_"
        base_dir = os.getenv("BASE_DIR", "/tmp/genims")
        
        daemons_str = os.getenv(f"{config_key}DAEMONS", "")
        daemon_list = daemons_str.split() if daemons_str else []
        
        # Get database name directly (no variable expansion)
        database = os.getenv(f"{config_key}DATABASE", f"genims_{module_name}_db")
        
        # Get and resolve log directory
        log_dir = os.getenv("DAEMON_LOG_DIR", os.path.join(base_dir, "logs"))
        log_dir = log_dir.replace("$BASE_DIR", base_dir).replace("$LOGS_DIR", log_dir)
        
        # Get and resolve pid directory
        pid_dir = os.getenv("DAEMON_PID_DIR", os.path.join(base_dir, ".daemon_pids"))
        pid_dir = pid_dir.replace("$BASE_DIR", base_dir).replace("$LOGS_DIR", log_dir)
        
        config = DaemonConfig(
            folder_name=module_name,
            folder_path=folder_path,
            database=database,
            daemons=daemon_list,
            enabled=os.getenv(f"{config_key}ENABLED", "true").lower() == "true",
            pg_host=os.getenv("POSTGRES_HOST", "localhost"),
            pg_port=os.getenv("POSTGRES_PORT", "5432"),
            pg_user=os.getenv("POSTGRES_USER", "postgres"),
            pg_password=os.getenv("POSTGRES_PASSWORD", ""),
            pg_ssl_mode=os.getenv("PG_SSL_MODE", "require"),
            log_dir=log_dir,
            log_level=os.getenv("DAEMON_LOG_LEVEL", "INFO"),
            pid_dir=pid_dir
        )
        
        self._log(f"Loaded config for {module_name}: {config.daemons}")
        return config
    
    def validate_prerequisites(self, config: DaemonConfig) -> Tuple[bool, List[str]]:
        """
        Validate prerequisites before starting daemons
        
        Args:
            config: DaemonConfig object
            
        Returns:
            Tuple of (success: bool, errors: List[str])
        """
        errors = []
        
        # Check folder exists
        if not os.path.exists(config.folder_path):
            errors.append(f"Folder not found: {config.folder_path}")
        
        # Check daemon scripts exist
        for daemon_name in config.daemons:
            daemon_script = os.path.join(config.folder_path, f"{daemon_name}.py")
            if not os.path.exists(daemon_script):
                errors.append(f"Daemon script not found: {daemon_script}")
        
        # Note: No longer require local .env file - using central scripts/config.env
        
        # Check database connectivity
        try:
            import psycopg2
            conn = psycopg2.connect(
                host=config.pg_host,
                port=config.pg_port,
                user=config.pg_user,
                password=config.pg_password,
                database=config.database,
                sslmode=config.pg_ssl_mode
            )
            conn.close()
            self._log(f"Database connection successful to {config.database}")
        except Exception as e:
            errors.append(f"Database connection failed: {str(e)}")
        
        return len(errors) == 0, errors
    
    def start_daemon(self, config: DaemonConfig, daemon_name: str) -> Tuple[bool, str]:
        """
        Start a daemon process
        
        Args:
            config: DaemonConfig object
            daemon_name: Name of daemon to start
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        daemon_script = os.path.join(config.folder_path, f"{daemon_name}.py")
        
        if not os.path.exists(daemon_script):
            return False, f"Daemon script not found: {daemon_script}"
        
        log_file = os.path.join(config.log_dir, f"{daemon_name}.log")
        pid_file = os.path.join(config.pid_dir, f"{daemon_name}.pid")
        
        try:
            # Use current environment (already loaded from scripts/config.env)
            daemon_env = os.environ.copy()
            
            # Start daemon process
            with open(log_file, "a") as lf:
                process = subprocess.Popen(
                    [sys.executable, daemon_script],
                    cwd=config.folder_path,
                    env=daemon_env,
                    stdout=lf,
                    stderr=subprocess.STDOUT,
                    start_new_session=True
                )
                
                # Save PID
                with open(pid_file, "w") as pf:
                    pf.write(str(process.pid))
                
                self.pids[daemon_name] = process.pid
                time.sleep(2)  # Give daemon time to start
                
                return True, f"Started {daemon_name} (PID: {process.pid})"
        
        except Exception as e:
            return False, f"Failed to start {daemon_name}: {str(e)}"
    
    def stop_daemon(self, daemon_name: str, grace_period: int = 30) -> Tuple[bool, str]:
        """
        Stop a daemon process gracefully
        
        Args:
            daemon_name: Name of daemon to stop
            grace_period: Seconds to wait before killing
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        pid_file = os.path.join(
            os.getenv("DAEMON_PID_DIR", "/tmp/genims_pids"),
            f"{daemon_name}.pid"
        )
        
        if not os.path.exists(pid_file):
            return False, f"PID file not found: {pid_file}"
        
        try:
            with open(pid_file) as f:
                pid = int(f.read().strip())
            
            if not psutil.pid_exists(pid):
                os.remove(pid_file)
                return False, f"Process {pid} not found"
            
            # Terminate gracefully
            process = psutil.Process(pid)
            process.terminate()
            
            # Wait for graceful shutdown
            try:
                process.wait(timeout=grace_period)
                os.remove(pid_file)
                return True, f"Stopped {daemon_name} (PID: {pid})"
            except psutil.TimeoutExpired:
                # Kill if still running
                process.kill()
                process.wait()
                os.remove(pid_file)
                return True, f"Killed {daemon_name} (PID: {pid})"
        
        except Exception as e:
            return False, f"Failed to stop {daemon_name}: {str(e)}"
    
    def get_daemon_status(self, daemon_name: str, config: DaemonConfig) -> DaemonStatus:
        """
        Get status of a daemon process
        
        Args:
            daemon_name: Name of daemon
            config: DaemonConfig object
            
        Returns:
            DaemonStatus object
        """
        pid_file = os.path.join(config.pid_dir, f"{daemon_name}.pid")
        
        status = DaemonStatus(
            name=daemon_name,
            is_running=False,
            last_check=datetime.now().isoformat()
        )
        
        if not os.path.exists(pid_file):
            return status
        
        try:
            with open(pid_file) as f:
                pid = int(f.read().strip())
            
            if psutil.pid_exists(pid):
                process = psutil.Process(pid)
                status.is_running = True
                status.pid = pid
                status.cpu_percent = process.cpu_percent(interval=1)
                status.memory_mb = process.memory_info().rss / 1024 / 1024
                status.uptime_seconds = time.time() - process.create_time()
        
        except Exception as e:
            self._log(f"Error getting status for {daemon_name}: {e}")
        
        return status
    
    def print_status_report(self, config: DaemonConfig, statuses: List[DaemonStatus]):
        """Print formatted status report"""
        print(f"\n{'='*70}")
        print(f"Folder {config.folder_name}: {config.database}")
        print(f"{'='*70}")
        print(f"{'Daemon':<20} {'Status':<12} {'PID':<10} {'CPU %':<8} {'Memory':<10}")
        print(f"{'-'*70}")
        
        for status in statuses:
            status_str = "RUNNING" if status.is_running else "STOPPED"
            pid_str = str(status.pid) if status.pid else "-"
            cpu_str = f"{status.cpu_percent:.1f}" if status.is_running else "-"
            mem_str = f"{status.memory_mb:.1f}MB" if status.is_running else "-"
            
            print(f"{status.name:<20} {status_str:<12} {pid_str:<10} {cpu_str:<8} {mem_str:<10}")
        
        print(f"{'='*70}\n")


def main():
    """Test DaemonManager functionality"""
    manager = DaemonManager(verbose=True)
    
    folder_02_path = "/Users/devendrayadav/insightql/GenIMS/Data Scripts/02 - Machine data"
    config = manager.load_daemon_config(folder_02_path, "02")
    
    print(f"\n{'='*70}")
    print("Configuration Loaded:")
    print(f"{'='*70}")
    for key, value in asdict(config).items():
        print(f"{key:<25}: {value}")
    
    success, errors = manager.validate_prerequisites(config)
    print(f"\n{'='*70}")
    print("Prerequisites Validation:")
    print(f"{'='*70}")
    if success:
        print("✓ All prerequisites met!")
    else:
        print("✗ Validation errors found:")
        for error in errors:
            print(f"  - {error}")


if __name__ == "__main__":
    main()
