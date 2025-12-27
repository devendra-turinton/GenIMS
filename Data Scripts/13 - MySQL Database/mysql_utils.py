"""
MySQL Database Utilities
Provides connection management, health checks, and common database operations
"""

import mysql.connector
from mysql.connector import Error, pooling
import logging
from typing import Optional, Dict, List, Tuple
from contextlib import contextmanager
from datetime import datetime
import os

logger = logging.getLogger(__name__)


class MySQLConnectionPool:
    """Manages MySQL connection pooling for efficient resource usage"""
    
    _instance = None
    _pool = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(MySQLConnectionPool, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._pool is None:
            self._initialize_pool()
    
    def _initialize_pool(self):
        """Initialize connection pool with configuration from environment"""
        try:
            config = {
                'host': os.getenv('MYSQL_HOST', 'localhost'),
                'port': int(os.getenv('MYSQL_PORT', 3306)),
                'user': os.getenv('MYSQL_USER', 'root'),
                'password': os.getenv('MYSQL_PASSWORD', ''),
                'autocommit': False,
                'get_warnings': True,
                'raise_on_warnings': False,
                'charset': 'utf8mb4',
            }
            
            self._pool = pooling.MySQLConnectionPool(
                pool_name='genims_pool',
                pool_size=int(os.getenv('MYSQL_POOL_SIZE', 5)),
                pool_reset_session=True,
                **config
            )
            logger.info("MySQL connection pool initialized successfully")
        except Error as e:
            logger.error(f"Failed to initialize connection pool: {e}")
            raise
    
    @contextmanager
    def get_connection(self, database: Optional[str] = None):
        """Context manager to get a database connection from pool"""
        connection = None
        try:
            connection = self._pool.get_connection()
            if database:
                connection.database = database
            yield connection
        except Error as e:
            logger.error(f"Failed to get connection: {e}")
            raise
        finally:
            if connection and connection.is_connected():
                connection.close()
    
    def test_connection(self, database: Optional[str] = None) -> bool:
        """Test database connection"""
        try:
            with self.get_connection(database) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                cursor.fetchone()
                cursor.close()
            logger.info(f"Connection test successful for database: {database}")
            return True
        except Error as e:
            logger.error(f"Connection test failed: {e}")
            return False


class MySQLDatabaseManager:
    """Manages database-level operations (creation, deletion, etc.)"""
    
    def __init__(self):
        self.pool = MySQLConnectionPool()
    
    def database_exists(self, database_name: str) -> bool:
        """Check if database exists"""
        try:
            with self.pool.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT SCHEMA_NAME FROM INFORMATION_SCHEMA.SCHEMATA "
                    "WHERE SCHEMA_NAME = %s",
                    (database_name,)
                )
                exists = cursor.fetchone() is not None
                cursor.close()
                return exists
        except Error as e:
            logger.error(f"Error checking database existence: {e}")
            return False
    
    def create_database(self, database_name: str, charset: str = 'utf8mb4') -> bool:
        """Create a new database"""
        try:
            with self.pool.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    f"CREATE DATABASE IF NOT EXISTS `{database_name}` "
                    f"CHARACTER SET {charset} COLLATE utf8mb4_unicode_ci"
                )
                conn.commit()
                cursor.close()
                logger.info(f"Database '{database_name}' created successfully")
                return True
        except Error as e:
            logger.error(f"Error creating database: {e}")
            return False
    
    def drop_database(self, database_name: str, confirm: bool = False) -> bool:
        """Drop a database (requires explicit confirmation)"""
        if not confirm:
            logger.warning(f"Database drop requires confirmation for '{database_name}'")
            return False
        
        try:
            with self.pool.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(f"DROP DATABASE IF EXISTS `{database_name}`")
                conn.commit()
                cursor.close()
                logger.info(f"Database '{database_name}' dropped successfully")
                return True
        except Error as e:
            logger.error(f"Error dropping database: {e}")
            return False
    
    def get_database_size(self, database_name: str) -> Tuple[int, str]:
        """Get database size in bytes and formatted string"""
        try:
            with self.pool.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT COALESCE(SUM(data_length + index_length), 0) as size "
                    "FROM information_schema.tables "
                    "WHERE table_schema = %s",
                    (database_name,)
                )
                result = cursor.fetchone()
                cursor.close()
                
                size_bytes = result[0] if result else 0
                size_mb = size_bytes / (1024 * 1024)
                size_gb = size_mb / 1024
                
                if size_gb > 1:
                    size_str = f"{size_gb:.2f} GB"
                else:
                    size_str = f"{size_mb:.2f} MB"
                
                return size_bytes, size_str
        except Error as e:
            logger.error(f"Error getting database size: {e}")
            return 0, "Unknown"


class MySQLSchemaManager:
    """Manages schema operations (loading, validation, etc.)"""
    
    def __init__(self):
        self.pool = MySQLConnectionPool()
    
    def load_schema_from_file(self, database_name: str, schema_file: str) -> bool:
        """Load SQL schema from file"""
        try:
            if not os.path.exists(schema_file):
                logger.error(f"Schema file not found: {schema_file}")
                return False
            
            with open(schema_file, 'r', encoding='utf-8') as f:
                sql_content = f.read()
            
            return self.execute_schema_sql(database_name, sql_content)
        except Exception as e:
            logger.error(f"Error loading schema from file: {e}")
            return False
    
    def execute_schema_sql(self, database_name: str, sql_content: str) -> bool:
        """Execute schema SQL statements"""
        try:
            with self.pool.get_connection() as conn:
                cursor = conn.cursor()
                
                # Split by ; and filter empty statements
                statements = [s.strip() for s in sql_content.split(';') if s.strip()]
                
                successful = 0
                failed = 0
                
                for statement in statements:
                    try:
                        # Skip comments and empty lines
                        if statement.startswith('--') or not statement:
                            continue
                        
                        cursor.execute(f"USE `{database_name}`")
                        cursor.execute(statement)
                        successful += 1
                    except Error as e:
                        logger.warning(f"Statement failed: {e}")
                        failed += 1
                        continue
                
                conn.commit()
                cursor.close()
                
                logger.info(f"Schema execution complete: {successful} successful, {failed} failed")
                return failed == 0
        except Error as e:
            logger.error(f"Error executing schema: {e}")
            return False
    
    def get_table_count(self, database_name: str) -> int:
        """Get number of tables in database"""
        try:
            with self.pool.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLES "
                    "WHERE TABLE_SCHEMA = %s",
                    (database_name,)
                )
                count = cursor.fetchone()[0]
                cursor.close()
                return count
        except Error as e:
            logger.error(f"Error getting table count: {e}")
            return 0
    
    def get_table_list(self, database_name: str) -> List[str]:
        """Get list of tables in database"""
        try:
            with self.pool.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES "
                    "WHERE TABLE_SCHEMA = %s ORDER BY TABLE_NAME",
                    (database_name,)
                )
                tables = [row[0] for row in cursor.fetchall()]
                cursor.close()
                return tables
        except Error as e:
            logger.error(f"Error getting table list: {e}")
            return []
    
    def validate_table_structure(self, database_name: str, table_name: str, 
                                 expected_columns: Dict[str, str]) -> bool:
        """Validate table has expected columns"""
        try:
            with self.pool.get_connection(database_name) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT COLUMN_NAME, COLUMN_TYPE FROM INFORMATION_SCHEMA.COLUMNS "
                    "WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s "
                    "ORDER BY ORDINAL_POSITION",
                    (database_name, table_name)
                )
                actual_columns = {row[0]: row[1] for row in cursor.fetchall()}
                cursor.close()
                
                missing = set(expected_columns.keys()) - set(actual_columns.keys())
                if missing:
                    logger.warning(f"Missing columns in {table_name}: {missing}")
                    return False
                
                return True
        except Error as e:
            logger.error(f"Error validating table structure: {e}")
            return False


class MySQLHealthCheck:
    """Performs health checks on MySQL databases"""
    
    def __init__(self):
        self.pool = MySQLConnectionPool()
        self.db_manager = MySQLDatabaseManager()
        self.schema_manager = MySQLSchemaManager()
    
    def check_reporting_db_health(self) -> Dict[str, any]:
        """Check genims_reporting_db health"""
        health_status = {
            'database': 'genims_reporting_db',
            'exists': False,
            'connected': False,
            'table_count': 0,
            'expected_tables': 35,
            'size': 'Unknown',
            'status': 'Unknown'
        }
        
        try:
            health_status['exists'] = self.db_manager.database_exists('genims_reporting_db')
            
            if health_status['exists']:
                health_status['connected'] = self.pool.test_connection('genims_reporting_db')
                
                if health_status['connected']:
                    health_status['table_count'] = self.schema_manager.get_table_count('genims_reporting_db')
                    size_bytes, size_str = self.db_manager.get_database_size('genims_reporting_db')
                    health_status['size'] = size_str
                    
                    # Determine overall status
                    if health_status['table_count'] == health_status['expected_tables']:
                        health_status['status'] = 'Healthy'
                    elif health_status['table_count'] > 0:
                        health_status['status'] = 'Partial (Some tables missing)'
                    else:
                        health_status['status'] = 'Schema not loaded'
            else:
                health_status['status'] = 'Database does not exist'
        except Exception as e:
            health_status['status'] = f"Error: {str(e)}"
        
        return health_status
    
    def check_audit_db_health(self) -> Dict[str, any]:
        """Check genims_audit_db health"""
        health_status = {
            'database': 'genims_audit_db',
            'exists': False,
            'connected': False,
            'table_count': 0,
            'expected_tables': 30,
            'size': 'Unknown',
            'status': 'Unknown'
        }
        
        try:
            health_status['exists'] = self.db_manager.database_exists('genims_audit_db')
            
            if health_status['exists']:
                health_status['connected'] = self.pool.test_connection('genims_audit_db')
                
                if health_status['connected']:
                    health_status['table_count'] = self.schema_manager.get_table_count('genims_audit_db')
                    size_bytes, size_str = self.db_manager.get_database_size('genims_audit_db')
                    health_status['size'] = size_str
                    
                    # Determine overall status
                    if health_status['table_count'] == health_status['expected_tables']:
                        health_status['status'] = 'Healthy'
                    elif health_status['table_count'] > 0:
                        health_status['status'] = 'Partial (Some tables missing)'
                    else:
                        health_status['status'] = 'Schema not loaded'
            else:
                health_status['status'] = 'Database does not exist'
        except Exception as e:
            health_status['status'] = f"Error: {str(e)}"
        
        return health_status
    
    def check_all_health(self) -> Dict[str, Dict[str, any]]:
        """Check health of all MySQL databases"""
        return {
            'reporting': self.check_reporting_db_health(),
            'audit': self.check_audit_db_health()
        }


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Test basic functionality
    health_check = MySQLHealthCheck()
    all_health = health_check.check_all_health()
    
    print("\n" + "="*60)
    print("MySQL Health Check Report")
    print("="*60)
    
    for db_type, health in all_health.items():
        print(f"\n{db_type.upper()} Database:")
        for key, value in health.items():
            print(f"  {key}: {value}")
