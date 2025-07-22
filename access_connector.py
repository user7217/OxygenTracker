try:
    import pyodbc
    PYODBC_AVAILABLE = True
except ImportError:
    PYODBC_AVAILABLE = False

try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False

import os
from typing import List, Dict, Optional
import logging

class AccessConnector:
    """MS Access database connector for importing data"""
    
    def __init__(self):
        self.connection = None
        self.logger = logging.getLogger(__name__)
    
    def connect(self, access_file_path: str) -> bool:
        """Connect to MS Access database"""
        if not PYODBC_AVAILABLE:
            self.logger.error("pyodbc is not available")
            return False
            
        try:
            # Check if file exists
            if not os.path.exists(access_file_path):
                self.logger.error(f"Access file not found: {access_file_path}")
                return False
            
            # Connection string for MS Access
            conn_str = f"DRIVER={{Microsoft Access Driver (*.mdb, *.accdb)}};DBQ={access_file_path};"
            
            self.connection = pyodbc.connect(conn_str)
            self.logger.info(f"Successfully connected to Access database: {access_file_path}")
            return True
            
        except pyodbc.Error as e:
            self.logger.error(f"Failed to connect to Access database: {str(e)}")
            # Try alternative driver
            try:
                conn_str = f"DRIVER={{Microsoft Access Driver (*.mdb)}};DBQ={access_file_path};"
                self.connection = pyodbc.connect(conn_str)
                self.logger.info(f"Connected using alternative driver: {access_file_path}")
                return True
            except pyodbc.Error as e2:
                self.logger.error(f"Alternative driver also failed: {str(e2)}")
                return False
        except Exception as e:
            self.logger.error(f"Unexpected error connecting to Access: {str(e)}")
            return False
    
    def get_tables(self) -> List[str]:
        """Get list of all tables in the database"""
        if not self.connection:
            return []
        
        try:
            cursor = self.connection.cursor()
            tables = []
            
            for table_info in cursor.tables(tableType='TABLE'):
                table_name = table_info.table_name
                # Skip system tables
                if not table_name.startswith('MSys') and not table_name.startswith('~'):
                    tables.append(table_name)
            
            return tables
            
        except Exception as e:
            self.logger.error(f"Error getting tables: {str(e)}")
            return []
    
    def get_table_columns(self, table_name: str) -> List[Dict]:
        """Get column information for a specific table"""
        if not self.connection:
            return []
        
        try:
            cursor = self.connection.cursor()
            columns = []
            
            for column in cursor.columns(table=table_name):
                columns.append({
                    'name': column.column_name,
                    'type': column.type_name,
                    'size': column.column_size,
                    'nullable': column.nullable == 1
                })
            
            return columns
            
        except Exception as e:
            self.logger.error(f"Error getting columns for table {table_name}: {str(e)}")
            return []
    
    def import_table_data(self, table_name: str, limit: Optional[int] = None) -> List[Dict]:
        """Import data from a specific table"""
        if not self.connection or not PANDAS_AVAILABLE:
            return []
        
        try:
            # Build query using Access syntax (TOP instead of LIMIT)
            if limit:
                query = f"SELECT TOP {limit} * FROM [{table_name}]"
            else:
                query = f"SELECT * FROM [{table_name}]"
            
            # Use pandas for easier data handling with proper connection
            # Suppress pandas warning about non-SQLAlchemy connections
            import warnings
            with warnings.catch_warnings():
                warnings.filterwarnings("ignore", message="pandas only supports SQLAlchemy connectable")
                df = pd.read_sql(query, self.connection)
            
            # Convert to list of dictionaries
            data = df.to_dict('records')
            
            # Clean up data - convert NaN to None
            cleaned_data = []
            for row in data:
                cleaned_row = {}
                for key, value in row.items():
                    if pd.isna(value):
                        cleaned_row[key] = None
                    else:
                        cleaned_row[key] = str(value) if not isinstance(value, (int, float, bool)) else value
                cleaned_data.append(cleaned_row)
            
            return cleaned_data
            
        except Exception as e:
            self.logger.error(f"Error importing data from table {table_name}: {str(e)}")
            return []
    
    def preview_table_data(self, table_name: str, rows: int = 5) -> List[Dict]:
        """Preview first few rows of a table"""
        return self.import_table_data(table_name, limit=rows)
    
    def close(self):
        """Close database connection and release file locks"""
        if self.connection:
            try:
                # Close any active cursors first
                try:
                    self.connection.commit()  # Commit any pending transactions
                except:
                    pass
                
                self.connection.close()
                self.logger.info("Access database connection closed")
                
                # Give Windows time to release the file lock
                import time
                time.sleep(0.5)
                
            except Exception as e:
                self.logger.error(f"Error closing connection: {str(e)}")
            finally:
                self.connection = None