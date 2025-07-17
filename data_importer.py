from access_connector import AccessConnector
from models import Customer, Cylinder
from typing import List, Dict, Optional, Tuple
import logging
import uuid
from datetime import datetime

class DataImporter:
    """Import data from MS Access to JSON databases"""
    
    def __init__(self):
        self.access_connector = AccessConnector()
        self.customer_model = Customer()
        self.cylinder_model = Cylinder()
        self.logger = logging.getLogger(__name__)
    
    def connect_to_access(self, file_path: str) -> bool:
        """Connect to Access database"""
        return self.access_connector.connect(file_path)
    
    def get_available_tables(self) -> List[str]:
        """Get list of available tables"""
        return self.access_connector.get_tables()
    
    def preview_table(self, table_name: str, rows: int = 5) -> Tuple[List[Dict], List[Dict]]:
        """Preview table data and structure"""
        columns = self.access_connector.get_table_columns(table_name)
        data = self.access_connector.preview_table_data(table_name, rows)
        return columns, data
    
    def suggest_field_mapping(self, table_name: str, target_type: str) -> Dict[str, str]:
        """Suggest field mapping based on column names"""
        columns = self.access_connector.get_table_columns(table_name)
        column_names = [col['name'].lower() for col in columns]
        
        mapping = {}
        
        if target_type == 'customer':
            # Customer field mappings - Updated to match Access database structure
            field_suggestions = {
                'customer_no': ['customer_no', 'customer_number', 'cust_no', 'customer_id', 'customer_code'],
                'customer_name': ['customer_name', 'name', 'fullname', 'full_name', 'client_name'],
                'customer_address': ['customer_address', 'address', 'street_address', 'full_address'],
                'customer_city': ['customer_city', 'city', 'town', 'location_city'],
                'customer_state': ['customer_state', 'state', 'province', 'location_state'],
                'customer_phone': ['customer_phone', 'phone', 'telephone', 'mobile', 'phone_number', 'contact'],
                'customer_apgst': ['customer_apgst', 'apgst', 'ap_gst', 'gst_number', 'gst_no'],
                'customer_cst': ['customer_cst', 'cst', 'cst_number', 'cst_no', 'central_tax']
            }
        elif target_type == 'cylinder':
            # Cylinder field mappings
            field_suggestions = {
                'serial_number': ['serial_number', 'serial', 'cylinder_serial', 'number'],
                'type': ['type', 'gas_type', 'cylinder_type', 'gas'],
                'size': ['size', 'capacity', 'volume', 'cylinder_size'],
                'status': ['status', 'state', 'condition', 'availability'],
                'location': ['location', 'position', 'storage_location', 'warehouse'],
                'pressure': ['pressure', 'current_pressure', 'psi'],
                'last_inspection': ['last_inspection', 'inspection_date', 'last_check'],
                'next_inspection': ['next_inspection', 'due_inspection', 'inspection_due'],
                'notes': ['notes', 'comments', 'remarks', 'description']
            }
        else:
            return mapping
        
        # Find best matches
        for target_field, suggestions in field_suggestions.items():
            for suggestion in suggestions:
                if suggestion in column_names:
                    # Find the actual column name (with original case)
                    for col in columns:
                        if col['name'].lower() == suggestion:
                            mapping[target_field] = col['name']
                            break
                    break
        
        return mapping
    
    def import_customers(self, table_name: str, field_mapping: Dict[str, str], 
                        skip_duplicates: bool = True) -> Tuple[int, int, List[str]]:
        """Import customers from Access table"""
        data = self.access_connector.import_table_data(table_name)
        imported_count = 0
        skipped_count = 0
        errors = []
        
        # Get existing customers for duplicate checking
        existing_customers = []
        if skip_duplicates:
            existing_customers = self.customer_model.get_all()
        
        for row in data:
            try:
                # Map fields
                customer_data = {}
                for target_field, source_field in field_mapping.items():
                    if source_field in row and row[source_field] is not None:
                        customer_data[target_field] = str(row[source_field]).strip()
                
                # Check required fields for new customer structure
                # Required: customer_no, customer_name, customer_address, customer_city, customer_state, customer_phone
                # Optional: customer_apgst, customer_cst
                required_fields = ['customer_no', 'customer_name', 'customer_address', 'customer_city', 'customer_state', 'customer_phone']
                missing_fields = [f for f in required_fields if not customer_data.get(f)]
                
                if missing_fields:
                    errors.append(f"Row skipped - missing required fields: {', '.join(missing_fields)}")
                    skipped_count += 1
                    continue
                
                # Set default values for optional fields
                if not customer_data.get('customer_apgst'):
                    customer_data['customer_apgst'] = ''
                if not customer_data.get('customer_cst'):
                    customer_data['customer_cst'] = ''
                
                # Check for duplicates using customer_no (unique identifier)
                existing_customer_nos = [c.get('customer_no', '').lower() for c in existing_customers] if skip_duplicates else []
                if skip_duplicates and customer_data['customer_no'].lower() in existing_customer_nos:
                    skipped_count += 1
                    continue
                
                # Add customer
                self.customer_model.add(customer_data)
                imported_count += 1
                
            except Exception as e:
                errors.append(f"Error importing row: {str(e)}")
                skipped_count += 1
        
        return imported_count, skipped_count, errors
    
    def import_cylinders(self, table_name: str, field_mapping: Dict[str, str], 
                        skip_duplicates: bool = True) -> Tuple[int, int, List[str]]:
        """Import cylinders from Access table"""
        data = self.access_connector.import_table_data(table_name)
        imported_count = 0
        skipped_count = 0
        errors = []
        
        existing_serials = []
        if skip_duplicates:
            existing_cylinders = self.cylinder_model.get_all()
            existing_serials = [c.get('serial_number', '').lower() for c in existing_cylinders]
        
        for row in data:
            try:
                # Map fields
                cylinder_data = {}
                for target_field, source_field in field_mapping.items():
                    if source_field in row and row[source_field] is not None:
                        value = str(row[source_field]).strip()
                        
                        # Special handling for certain fields
                        if target_field == 'status':
                            # Normalize status values
                            value_lower = value.lower()
                            if value_lower in ['available', 'in stock', 'ready']:
                                value = 'Available'
                            elif value_lower in ['rented', 'out', 'in use']:
                                value = 'Rented'
                            elif value_lower in ['maintenance', 'repair', 'servicing']:
                                value = 'Maintenance'
                            elif value_lower in ['out of service', 'retired', 'damaged']:
                                value = 'Out of Service'
                        
                        cylinder_data[target_field] = value
                
                # Set default values for optional fields
                if not cylinder_data.get('location'):
                    cylinder_data['location'] = 'Warehouse'
                
                if not cylinder_data.get('status'):
                    cylinder_data['status'] = 'Available'
                
                # Check required fields (location and status now have defaults)
                required_fields = ['serial_number', 'type', 'size']
                missing_fields = [f for f in required_fields if not cylinder_data.get(f)]
                
                if missing_fields:
                    errors.append(f"Row skipped - missing required fields: {', '.join(missing_fields)}")
                    skipped_count += 1
                    continue
                
                # Check for duplicates
                if skip_duplicates and cylinder_data['serial_number'].lower() in existing_serials:
                    skipped_count += 1
                    continue
                
                # Add cylinder
                self.cylinder_model.add(cylinder_data)
                existing_serials.append(cylinder_data['serial_number'].lower())
                imported_count += 1
                
            except Exception as e:
                errors.append(f"Error importing row: {str(e)}")
                skipped_count += 1
        
        return imported_count, skipped_count, errors
    
    def close_connection(self):
        """Close Access database connection"""
        self.access_connector.close()