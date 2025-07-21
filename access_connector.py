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
        """Get list of tables in the Access database"""
        if not self.connection:
            return []
        
        try:
            cursor = self.connection.cursor()
            tables = []
            
            # Get user tables (not system tables)
            for table_info in cursor.tables(tableType='TABLE'):
                table_name = table_info.table_name
                if not table_name.startswith('MSys'):  # Skip system tables
                    tables.append(table_name)
            
            return tables
            
        except Exception as e:
            self.logger.error(f"Error getting tables: {str(e)}")
            return []
    
    def get_table_columns(self, table_name: str) -> List[Dict]:
        """Get column information from a table"""
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
        """Close database connection"""
        if self.connection:
            try:
                self.connection.close()
                self.logger.info("Access database connection closed")
            except Exception as e:
                self.logger.error(f"Error closing connection: {str(e)}")
            finally:
                self.connection = None
    
    def auto_detect_fields(self, table_name: str, target_type: str) -> Dict[str, str]:
        """Automatically detect and map fields based on column names and data patterns"""
        try:
            columns = self.get_table_columns(table_name)
            if not columns:
                return {}
            
            field_mapping = {}
            patterns = self.field_mappings.get(target_type, {})
            
            for column in columns:
                col_name = column['name'].lower()
                col_type = column.get('type', '').lower()
                
                # Map fields based on patterns
                for field_key, pattern_list in patterns.items():
                    target_field = field_key.replace('_patterns', '')
                    
                    if target_field not in field_mapping.values():
                        for pattern in pattern_list:
                            if pattern in col_name or col_name in pattern:
                                field_mapping[column['name']] = target_field
                                break
                
                # Special handling for name fields (combine first/last names)
                if target_type == 'customer' and 'name' not in field_mapping.values():
                    if any(x in col_name for x in ['first', 'fname', 'given']):
                        field_mapping[column['name']] = 'first_name'
                    elif any(x in col_name for x in ['last', 'lname', 'surname', 'family']):
                        field_mapping[column['name']] = 'last_name'
            
            return field_mapping
            
        except Exception as e:
            logging.error(f"Error auto-detecting fields: {e}")
            return {}
    
    def get_sample_data_with_analysis(self, table_name: str, rows: int = 10) -> Dict:
        """Get sample data with field analysis for better mapping"""
        try:
            if not self.connection:
                return {}
            
            cursor = self.connection.cursor()
            cursor.execute(f"SELECT TOP {rows} * FROM [{table_name}]")
            
            columns = [desc[0] for desc in cursor.description]
            rows_data = cursor.fetchall()
            
            # Analyze data patterns
            analysis = {
                'columns': columns,
                'sample_data': [],
                'field_analysis': {}
            }
            
            for row in rows_data:
                row_dict = {}
                for i, value in enumerate(row):
                    row_dict[columns[i]] = str(value) if value is not None else ''
                analysis['sample_data'].append(row_dict)
            
            # Analyze each column
            for col in columns:
                col_values = [row.get(col, '') for row in analysis['sample_data']]
                analysis['field_analysis'][col] = self._analyze_column_data(col, col_values)
            
            return analysis
            
        except Exception as e:
            logging.error(f"Error getting sample data with analysis: {e}")
            return {}
    
    def _analyze_column_data(self, col_name: str, values: List[str]) -> Dict:
        """Analyze column data to determine likely field type"""
        import re
        
        analysis = {
            'likely_type': 'text',
            'patterns': [],
            'sample_values': values[:3]
        }
        
        # Email pattern detection
        email_pattern = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
        if any(email_pattern.match(str(v)) for v in values if v):
            analysis['likely_type'] = 'email'
            analysis['patterns'].append('email_format')
        
        # Phone pattern detection
        phone_pattern = re.compile(r'[\d\s\-\(\)\+]{7,}')
        if any(phone_pattern.match(str(v)) for v in values if v):
            analysis['likely_type'] = 'phone'
            analysis['patterns'].append('phone_format')
        
        # Date pattern detection
        date_patterns = [
            re.compile(r'\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4}'),
            re.compile(r'\d{4}[\/\-]\d{1,2}[\/\-]\d{1,2}')
        ]
        if any(any(pattern.match(str(v)) for pattern in date_patterns) for v in values if v):
            analysis['likely_type'] = 'date'
            analysis['patterns'].append('date_format')
        
        # Numeric pattern detection
        if all(str(v).replace('.', '').replace('-', '').isdigit() for v in values if v):
            analysis['likely_type'] = 'numeric'
            analysis['patterns'].append('numeric_format')
        
        return analysis
    
    def __del__(self):
        """Cleanup when object is destroyed"""
        self.close()