"""
Direct Database Import Feature
Connect directly to existing PostgreSQL databases and import data without JSON intermediary
"""

import os
import psycopg2
import pandas as pd
from typing import Dict, List, Any, Optional
from datetime import datetime
from db_service import CustomerService, CylinderService

class DirectDatabaseImporter:
    """Import data directly from external PostgreSQL databases"""
    
    def __init__(self):
        self.connection = None
        self.cursor = None
    
    def connect_to_external_db(self, connection_string: str) -> bool:
        """Connect to external PostgreSQL database"""
        try:
            self.connection = psycopg2.connect(connection_string)
            self.cursor = self.connection.cursor()
            return True
        except Exception as e:
            print(f"Database connection error: {e}")
            return False
    
    def list_tables(self) -> List[str]:
        """List all tables in the connected database"""
        if not self.cursor:
            return []
        
        try:
            self.cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name
            """)
            return [row[0] for row in self.cursor.fetchall()]
        except Exception as e:
            print(f"Error listing tables: {e}")
            return []
    
    def preview_table(self, table_name: str, limit: int = 5) -> Dict[str, Any]:
        """Preview table structure and sample data"""
        if not self.cursor:
            return {'error': 'No database connection'}
        
        try:
            # Get column information
            self.cursor.execute("""
                SELECT column_name, data_type, is_nullable 
                FROM information_schema.columns 
                WHERE table_name = %s
                ORDER BY ordinal_position
            """, (table_name,))
            
            columns = self.cursor.fetchall()
            
            # Get sample data
            self.cursor.execute(f"SELECT * FROM {table_name} LIMIT %s", (limit,))
            sample_data = self.cursor.fetchall()
            
            return {
                'columns': columns,
                'sample_data': sample_data,
                'total_rows': self.get_row_count(table_name)
            }
        except Exception as e:
            return {'error': str(e)}
    
    def get_row_count(self, table_name: str) -> int:
        """Get total row count for a table"""
        try:
            self.cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            return self.cursor.fetchone()[0]
        except:
            return 0
    
    def import_customers_from_table(self, table_name: str, field_mapping: Dict[str, str]) -> Dict[str, Any]:
        """Import customers directly from database table"""
        if not self.cursor:
            return {'success': False, 'error': 'No database connection'}
        
        try:
            # Build the SQL query with field mapping
            source_fields = list(field_mapping.keys())
            target_fields = list(field_mapping.values())
            
            query = f"SELECT {', '.join(source_fields)} FROM {table_name}"
            self.cursor.execute(query)
            
            imported_count = 0
            updated_count = 0
            errors = []
            
            with CustomerService() as customer_service:
                for row in self.cursor.fetchall():
                    try:
                        # Map row data to target fields
                        customer_data = {}
                        for i, source_field in enumerate(source_fields):
                            target_field = field_mapping[source_field]
                            customer_data[target_field] = row[i]
                        
                        # Check if customer already exists
                        existing_customer = None
                        if customer_data.get('customer_name'):
                            customers, _ = customer_service.get_all(page=1, per_page=10000)
                            for customer in customers:
                                customer_name_check = customer.customer_name if hasattr(customer, 'customer_name') else customer.get('customer_name', '')
                                if customer_name_check.strip().lower() == customer_data['customer_name'].strip().lower():
                                    existing_customer = customer
                                    break
                        
                        if existing_customer:
                            # Update existing customer
                            customer_id = existing_customer.id if hasattr(existing_customer, 'id') else existing_customer.get('id')
                            customer_service.update(customer_id, customer_data)
                            updated_count += 1
                        else:
                            # Create new customer
                            customer_service.create(customer_data)
                            imported_count += 1
                            
                    except Exception as e:
                        errors.append(f"Row error: {str(e)}")
            
            return {
                'success': len(errors) == 0,
                'imported': imported_count,
                'updated': updated_count,
                'errors': errors,
                'total': imported_count + updated_count
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def import_cylinders_from_table(self, table_name: str, field_mapping: Dict[str, str]) -> Dict[str, Any]:
        """Import cylinders directly from database table"""
        if not self.cursor:
            return {'success': False, 'error': 'No database connection'}
        
        try:
            # Build the SQL query with field mapping
            source_fields = list(field_mapping.keys())
            target_fields = list(field_mapping.values())
            
            query = f"SELECT {', '.join(source_fields)} FROM {table_name}"
            self.cursor.execute(query)
            
            imported_count = 0
            updated_count = 0
            errors = []
            
            with CylinderService() as cylinder_service:
                for row in self.cursor.fetchall():
                    try:
                        # Map row data to target fields
                        cylinder_data = {}
                        for i, source_field in enumerate(source_fields):
                            target_field = field_mapping[source_field]
                            cylinder_data[target_field] = row[i]
                        
                        # Set defaults
                        cylinder_data.setdefault('status', 'Available')
                        cylinder_data.setdefault('location', 'Warehouse')
                        
                        # Check if cylinder already exists
                        existing_cylinder = None
                        cylinder_id = cylinder_data.get('id') or cylinder_data.get('custom_id')
                        if cylinder_id:
                            existing_cylinder = cylinder_service.find_by_any_identifier(cylinder_id)
                        
                        # Link to customer if customer data exists and cylinder is dispatched/rented
                        if (cylinder_data.get('status', '').lower() in ['rented', 'dispatched'] and 
                            cylinder_data.get('customer_name')):
                            customer_link_id = self._find_or_create_customer_from_cylinder(cylinder_data)
                            if customer_link_id:
                                cylinder_data['rented_to'] = customer_link_id
                        
                        if existing_cylinder:
                            # Update existing cylinder
                            actual_id = existing_cylinder.get('id')
                            success = cylinder_service.update_exact(actual_id, cylinder_data)
                            if success:
                                updated_count += 1
                            else:
                                errors.append(f"Cylinder '{cylinder_id}': Failed to update")
                        else:
                            # Create new cylinder
                            cylinder_service.create_exact(cylinder_data)
                            imported_count += 1
                            
                    except Exception as e:
                        errors.append(f"Row error: {str(e)}")
            
            return {
                'success': len(errors) == 0,
                'imported': imported_count,
                'updated': updated_count,
                'errors': errors,
                'total': imported_count + updated_count
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _find_or_create_customer_from_cylinder(self, cylinder_data: Dict) -> Optional[str]:
        """Find existing customer or create new one based on cylinder customer data"""
        try:
            customer_name = cylinder_data.get('customer_name', '').strip()
            if not customer_name:
                return None
                
            # Try to find existing customer by name first
            with CustomerService() as customer_service:
                customers, _ = customer_service.get_all(page=1, per_page=10000)
                
                for customer in customers:
                    # Handle both dict and object customer data
                    if hasattr(customer, 'customer_name'):
                        customer_name_check = customer.customer_name or ''
                        customer_id = customer.id
                    else:
                        customer_name_check = customer.get('customer_name', '')
                        customer_id = customer.get('id')
                        
                    if customer_name_check.strip().lower() == customer_name.lower():
                        return customer_id
                
                # If not found, create new customer from cylinder data
                customer_data = {
                    'customer_name': customer_name,
                    'customer_email': cylinder_data.get('customer_email', ''),
                    'customer_phone': cylinder_data.get('customer_phone', ''),
                    'customer_address': cylinder_data.get('customer_address', ''),
                    'customer_city': cylinder_data.get('customer_city', ''),
                    'customer_state': cylinder_data.get('customer_state', ''),
                    'customer_no': f"AUTO-{datetime.now().strftime('%Y%m%d')}-{customer_name[:3].upper()}"
                }
                
                # Clean up phone number
                if customer_data['customer_phone'] in ['0.0', '0', '', None]:
                    customer_data['customer_phone'] = None
                    
                new_customer = customer_service.create(customer_data)
                return new_customer.id if new_customer else None
                
        except Exception as e:
            print(f"Error finding/creating customer: {e}")
            return None
    
    def close_connection(self):
        """Close database connection"""
        if self.cursor:
            self.cursor.close()
        if self.connection:
            self.connection.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close_connection()