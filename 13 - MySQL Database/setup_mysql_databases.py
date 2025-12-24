"""
Setup MySQL Databases for GenIMS
Creates genims_reporting_db and genims_audit_db with proper configuration
"""

import os
import sys
import logging
from pathlib import Path
from datetime import datetime
import argparse

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from mysql_utils import MySQLDatabaseManager, MySQLSchemaManager, MySQLHealthCheck

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'logs/mysql_setup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class MySQLSetup:
    """Orchestrates MySQL database setup"""
    
    def __init__(self):
        self.db_manager = MySQLDatabaseManager()
        self.schema_manager = MySQLSchemaManager()
        self.health_check = MySQLHealthCheck()
        
        # Get script directory for schema files
        self.script_dir = Path(__file__).parent
        self.reporting_schema_file = self.script_dir / 'genims_reporting_schema.sql'
        self.audit_schema_file = self.script_dir / 'genims_audit_schema.sql'
    
    def validate_schema_files(self) -> bool:
        """Verify schema files exist"""
        logger.info("Validating schema files...")
        
        files_ok = True
        
        if not self.reporting_schema_file.exists():
            logger.error(f"Reporting schema file not found: {self.reporting_schema_file}")
            files_ok = False
        else:
            logger.info(f"✓ Reporting schema file found: {self.reporting_schema_file}")
        
        if not self.audit_schema_file.exists():
            logger.error(f"Audit schema file not found: {self.audit_schema_file}")
            files_ok = False
        else:
            logger.info(f"✓ Audit schema file found: {self.audit_schema_file}")
        
        return files_ok
    
    def setup_reporting_database(self, drop_existing: bool = False) -> bool:
        """Setup genims_reporting_db"""
        db_name = 'genims_reporting_db'
        logger.info(f"\n{'='*60}")
        logger.info(f"Setting up {db_name}...")
        logger.info(f"{'='*60}")
        
        try:
            # Check if database exists
            if self.db_manager.database_exists(db_name):
                logger.warning(f"Database '{db_name}' already exists")
                
                if drop_existing:
                    logger.info(f"Dropping existing database '{db_name}'...")
                    if not self.db_manager.drop_database(db_name, confirm=True):
                        logger.error(f"Failed to drop existing database '{db_name}'")
                        return False
                    logger.info(f"✓ Database '{db_name}' dropped")
                else:
                    logger.info(f"Using existing database '{db_name}' (not dropping)")
            
            # Create database if it doesn't exist
            if not self.db_manager.database_exists(db_name):
                logger.info(f"Creating database '{db_name}'...")
                if not self.db_manager.create_database(db_name):
                    logger.error(f"Failed to create database '{db_name}'")
                    return False
                logger.info(f"✓ Database '{db_name}' created")
            
            # Load schema
            logger.info(f"Loading schema for '{db_name}'...")
            if not self.schema_manager.load_schema_from_file(db_name, str(self.reporting_schema_file)):
                logger.error(f"Failed to load schema for '{db_name}'")
                return False
            logger.info(f"✓ Schema loaded for '{db_name}'")
            
            # Verify
            table_count = self.schema_manager.get_table_count(db_name)
            logger.info(f"✓ {db_name} has {table_count} tables")
            
            return True
        except Exception as e:
            logger.error(f"Error setting up {db_name}: {e}")
            return False
    
    def setup_audit_database(self, drop_existing: bool = False) -> bool:
        """Setup genims_audit_db"""
        db_name = 'genims_audit_db'
        logger.info(f"\n{'='*60}")
        logger.info(f"Setting up {db_name}...")
        logger.info(f"{'='*60}")
        
        try:
            # Check if database exists
            if self.db_manager.database_exists(db_name):
                logger.warning(f"Database '{db_name}' already exists")
                
                if drop_existing:
                    logger.info(f"Dropping existing database '{db_name}'...")
                    if not self.db_manager.drop_database(db_name, confirm=True):
                        logger.error(f"Failed to drop existing database '{db_name}'")
                        return False
                    logger.info(f"✓ Database '{db_name}' dropped")
                else:
                    logger.info(f"Using existing database '{db_name}' (not dropping)")
            
            # Create database if it doesn't exist
            if not self.db_manager.database_exists(db_name):
                logger.info(f"Creating database '{db_name}'...")
                if not self.db_manager.create_database(db_name):
                    logger.error(f"Failed to create database '{db_name}'")
                    return False
                logger.info(f"✓ Database '{db_name}' created")
            
            # Load schema
            logger.info(f"Loading schema for '{db_name}'...")
            if not self.schema_manager.load_schema_from_file(db_name, str(self.audit_schema_file)):
                logger.error(f"Failed to load schema for '{db_name}'")
                return False
            logger.info(f"✓ Schema loaded for '{db_name}'")
            
            # Verify
            table_count = self.schema_manager.get_table_count(db_name)
            logger.info(f"✓ {db_name} has {table_count} tables")
            
            return True
        except Exception as e:
            logger.error(f"Error setting up {db_name}: {e}")
            return False
    
    def run_health_checks(self) -> bool:
        """Run comprehensive health checks"""
        logger.info(f"\n{'='*60}")
        logger.info("Running Health Checks...")
        logger.info(f"{'='*60}")
        
        health_status = self.health_check.check_all_health()
        
        all_healthy = True
        
        for db_type, health in health_status.items():
            logger.info(f"\n{db_type.upper()} Database Health:")
            for key, value in health.items():
                status_str = f"  {key}: {value}"
                
                if db_type == 'reporting':
                    if (key == 'status' and value != 'Healthy'):
                        logger.warning(status_str)
                        all_healthy = False
                    else:
                        logger.info(status_str)
                else:  # audit
                    if (key == 'status' and value != 'Healthy'):
                        logger.warning(status_str)
                        all_healthy = False
                    else:
                        logger.info(status_str)
        
        return all_healthy
    
    def setup_all(self, drop_existing: bool = False) -> bool:
        """Setup all MySQL databases"""
        logger.info("\n" + "="*60)
        logger.info("GenIMS MySQL Database Setup")
        logger.info("="*60)
        logger.info(f"Timestamp: {datetime.now().isoformat()}")
        
        # Validate schema files
        if not self.validate_schema_files():
            logger.error("Schema file validation failed")
            return False
        
        # Setup reporting database
        if not self.setup_reporting_database(drop_existing=drop_existing):
            logger.error("Reporting database setup failed")
            return False
        
        # Setup audit database
        if not self.setup_audit_database(drop_existing=drop_existing):
            logger.error("Audit database setup failed")
            return False
        
        # Run health checks
        if not self.run_health_checks():
            logger.warning("Some health checks failed")
            return False
        
        logger.info("\n" + "="*60)
        logger.info("✓ MySQL Setup Completed Successfully!")
        logger.info("="*60)
        
        return True


def main():
    parser = argparse.ArgumentParser(
        description='Setup GenIMS MySQL Databases',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  python3 setup_mysql_databases.py                    # Setup with existing databases
  python3 setup_mysql_databases.py --drop-existing    # Drop and recreate databases
  python3 setup_mysql_databases.py --reporting-only   # Setup only reporting database
  python3 setup_mysql_databases.py --audit-only       # Setup only audit database
        '''
    )
    
    parser.add_argument(
        '--drop-existing',
        action='store_true',
        help='Drop existing databases before setup (WARNING: Data will be lost!)'
    )
    
    parser.add_argument(
        '--reporting-only',
        action='store_true',
        help='Setup only reporting database'
    )
    
    parser.add_argument(
        '--audit-only',
        action='store_true',
        help='Setup only audit database'
    )
    
    args = parser.parse_args()
    
    # Create logs directory if it doesn't exist
    logs_dir = Path(__file__).parent / 'logs'
    logs_dir.mkdir(exist_ok=True)
    
    setup = MySQLSetup()
    
    try:
        if args.reporting_only:
            success = setup.setup_reporting_database(drop_existing=args.drop_existing)
        elif args.audit_only:
            success = setup.setup_audit_database(drop_existing=args.drop_existing)
        else:
            success = setup.setup_all(drop_existing=args.drop_existing)
        
        return 0 if success else 1
    except KeyboardInterrupt:
        logger.info("\nSetup interrupted by user")
        return 1
    except Exception as e:
        logger.exception(f"Unexpected error during setup: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())
