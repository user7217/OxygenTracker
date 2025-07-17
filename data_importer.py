from access_connector import AccessConnector
from models import Customer, Cylinder
from typing import List, Dict, Optional, Tuple
import logging
import uuid
from datetime import datetime

class DataImporter:

    def __init__(self):
        self.access_connector = AccessConnector()
        self.customer_model = Customer()
        self.cylinder_model = Cylinder()
        self.logger = logging.getLogger(__name__)
    
    def connect_to_access(self, file_path: str) -> bool:
        
        return self.access_connector.connect(file_path)
    
    def get_available_tables(self) -> List[str]:
        
        return self.access_connector.get_tables()
    
    def preview_table(self, table_name: str, rows: int = 5) -> Tuple[List[Dict], List[Dict]]:
        
        columns = self.access_connector.get_table_columns(table_name)
        data = self.access_connector.preview_table_data(table_name, rows)
        return columns, data
    
    def suggest_field_mapping(self, table_name: str, target_type: str) -> Dict[str, str]:
        
        columns = self.access_connector.get_table_columns(table_name)
        column_names = [col['name'].lower() for col in columns]
        
        mapping = {}
        
        if target_type == 'customer':
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
            field_suggestions = {
                'serial_number': ['serial_number', 'serial', 'cylinder_serial', 'number'],
                'custom_id': ['custom_id', 'cylinder_number', 'cylinder_no', 'id', 'ref_number'],
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
        
        for target_field, suggestions in field_suggestions.items():
            for suggestion in suggestions:
                if suggestion in column_names:
                    for col in columns:
                        if col['name'].lower() == suggestion:
                            mapping[target_field] = col['name']
                            break
                    break
        
        return mapping
    
    def import_customers(self, table_name: str, field_mapping: Dict[str, str], 
                        skip_duplicates: bool = True) -> Tuple[int, int, List[str]]:
        
        data = self.access_connector.import_table_data(table_name)
        imported_count = 0
        skipped_count = 0
        errors = []
        
        existing_customers = []
        if skip_duplicates:
            existing_customers = self.customer_model.get_all()
        
        for row in data:
            try:
                customer_data = {}
                for target_field, source_field in field_mapping.items():
                    if source_field in row and row[source_field] is not None:
                        customer_data[target_field] = str(row[source_field]).strip()
                
                required_fields = ['customer_no', 'customer_name', 'customer_address', 'customer_city', 'customer_state', 'customer_phone']
                missing_fields = [f for f in required_fields if not customer_data.get(f)]
                
                if missing_fields:
                    errors.append(f"Row skipped - missing required fields: {', '.join(missing_fields)}")
                    skipped_count += 1
                    continue
                
                if not customer_data.get('customer_apgst'):
                    customer_data['customer_apgst'] = ''
                if not customer_data.get('customer_cst'):
                    customer_data['customer_cst'] = ''
                
                existing_customer_nos = [c.get('customer_no', '').lower() for c in existing_customers] if skip_duplicates else []
                if skip_duplicates and customer_data['customer_no'].lower() in existing_customer_nos:
                    skipped_count += 1
                    continue
                
                self.customer_model.add(customer_data)
                imported_count += 1
                
            except Exception as e:
                errors.append(f"Error importing row: {str(e)}")
                skipped_count += 1
        
        return imported_count, skipped_count, errors
    
    def import_cylinders(self, table_name: str, field_mapping: Dict[str, str], 
                        skip_duplicates: bool = True) -> Tuple[int, int, List[str]]:
        
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
                cylinder_data = {}
                for target_field, source_field in field_mapping.items():
                    if source_field in row and row[source_field] is not None:
                        value = str(row[source_field]).strip()
                        
                        if target_field == 'status':
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
                
                if not cylinder_data.get('location'):
                    cylinder_data['location'] = 'Warehouse'
                
                if not cylinder_data.get('status'):
                    cylinder_data['status'] = 'Available'
                
                required_fields = ['serial_number', 'type', 'size']
                missing_fields = [f for f in required_fields if not cylinder_data.get(f)]
                
                if missing_fields:
                    errors.append(f"Row skipped - missing required fields: {', '.join(missing_fields)}")
                    skipped_count += 1
                    continue
                
                if skip_duplicates and cylinder_data['serial_number'].lower() in existing_serials:
                    skipped_count += 1
                    continue
                
                self.cylinder_model.add(cylinder_data)
                existing_serials.append(cylinder_data['serial_number'].lower())
                imported_count += 1
                
            except Exception as e:
                errors.append(f"Error importing row: {str(e)}")
                skipped_count += 1
        
        return imported_count, skipped_count, errors
    
    def import_transactions(self, table_name: str, field_mapping: Dict[str, str], 
                           skip_duplicates: bool = True) -> Tuple[int, int, List[str]]:
        
        data = self.access_connector.import_table_data(table_name)
        imported_count = 0
        skipped_count = 0
        errors = []
        linked_count = 0
        
        existing_customers = self.customer_model.get_all()
        existing_cylinders = self.cylinder_model.get_all()
        
        customer_lookup = {c.get('customer_no', '').upper(): c for c in existing_customers}
        cylinder_lookup = {}
        
        for cyl in existing_cylinders:
            if cyl.get('serial_number'):
                cylinder_lookup[cyl.get('serial_number', '').upper()] = cyl
            
            if cyl.get('custom_id'):
                cylinder_lookup[cyl.get('custom_id', '').upper()] = cyl
            
            if cyl.get('id'):
                cylinder_lookup[cyl.get('id', '').upper()] = cyl
        
        print(f"Found {len(customer_lookup)} customers and {len(cylinder_lookup)} cylinders for linking")
        
        for row_num, row in enumerate(data, 1):
            try:
                transaction_data = {}
                for target_field, source_field in field_mapping.items():
                    if source_field in row and row[source_field] is not None:
                        transaction_data[target_field] = str(row[source_field]).strip()
                
                required_fields = ['customer_no', 'cylinder_no']
                missing_fields = [f for f in required_fields if not transaction_data.get(f)]
                
                if missing_fields:
                    errors.append(f"Row {row_num}: Missing required fields: {', '.join(missing_fields)}")
                    skipped_count += 1
                    continue
                
                customer_no = transaction_data['customer_no'].upper()
                cylinder_no = transaction_data['cylinder_no'].upper()
                
                customer = customer_lookup.get(customer_no)
                if not customer:
                    errors.append(f"Row {row_num}: Customer '{customer_no}' not found")
                    skipped_count += 1
                    continue
                
                cylinder = cylinder_lookup.get(cylinder_no)
                if not cylinder:
                    errors.append(f"Row {row_num}: Cylinder '{cylinder_no}' not found")
                    skipped_count += 1
                    continue
                
                dispatch_date = transaction_data.get('dispatch_date', '')
                return_date = transaction_data.get('return_date', '')
                transaction_type = transaction_data.get('transaction_type', '').lower()
                
                if dispatch_date and return_date:
                    success_rent = self.cylinder_model.rent_cylinder_with_location(
                        cylinder['id'], 
                        customer['id'], 
                        dispatch_date,
                        customer
                    )
                    if success_rent:
                        success_return = self.cylinder_model.return_cylinder(
                            cylinder['id'], 
                            return_date
                        )
                        if success_return:
                            linked_count += 1
                            print(f"Row {row_num}: Complete cycle - rented {cylinder_no} to {customer_no} on {dispatch_date}, returned on {return_date}")
                        else:
                            errors.append(f"Row {row_num}: Failed to return cylinder {cylinder_no}")
                    else:
                        errors.append(f"Row {row_num}: Failed to rent cylinder {cylinder_no}")
                        
                elif dispatch_date and not return_date:
                    success = self.cylinder_model.rent_cylinder_with_location(
                        cylinder['id'], 
                        customer['id'], 
                        dispatch_date,
                        customer
                    )
                    if success:
                        linked_count += 1
                        print(f"Row {row_num}: Currently rented - {cylinder_no} to {customer_no} since {dispatch_date} (no return date - still with customer)")
                    else:
                        errors.append(f"Row {row_num}: Failed to rent cylinder {cylinder_no}")
                        
                elif return_date and not dispatch_date:
                    success_rent = self.cylinder_model.rent_cylinder_with_location(
                        cylinder['id'], 
                        customer['id'], 
                        None,
                        customer
                    )
                    if success_rent:
                        success_return = self.cylinder_model.return_cylinder(
                            cylinder['id'], 
                            return_date
                        )
                        if success_return:
                            linked_count += 1
                            print(f"Row {row_num}: Returned cylinder {cylinder_no} on {return_date}")
                        else:
                            errors.append(f"Row {row_num}: Failed to return cylinder {cylinder_no}")
                    else:
                        errors.append(f"Row {row_num}: Failed to establish rental for cylinder {cylinder_no}")
                        
                else:
                    if transaction_type in ['return', 'returned', 'in', 'receive']:
                        success = self.cylinder_model.return_cylinder(cylinder['id'])
                        if success:
                            linked_count += 1
                            print(f"Row {row_num}: Returned cylinder {cylinder_no}")
                        else:
                            errors.append(f"Row {row_num}: Failed to return cylinder {cylinder_no}")
                    else:
                        success = self.cylinder_model.rent_cylinder_with_location(
                            cylinder['id'], 
                            customer['id'],
                            None,
                            customer
                        )
                        if success:
                            linked_count += 1
                            print(f"Row {row_num}: Rented cylinder {cylinder_no} to customer {customer_no} (location updated to customer address)")
                        else:
                            errors.append(f"Row {row_num}: Failed to rent cylinder {cylinder_no}")
                
                imported_count += 1
                
            except Exception as e:
                errors.append(f"Row {row_num}: Error processing transaction: {str(e)}")
                skipped_count += 1
        
        print(f"Transaction import completed: {imported_count} processed, {linked_count} linked, {skipped_count} skipped")
        return imported_count, skipped_count, errors
    
    def suggest_transaction_field_mapping(self, table_name: str) -> Dict[str, str]:
        
        columns = self.access_connector.get_table_columns(table_name)
        column_names = [col['name'].lower() for col in columns]
        
        mapping = {}
        
        field_suggestions = {
            'customer_no': ['customer_no', 'customer_number', 'cust_no', 'customer_id', 'customer_code'],
            'cylinder_no': ['cylinder_no', 'cylinder_number', 'cylinder_id', 'serial_number', 'cylinder_serial', 'custom_id'],
            'dispatch_date': ['dispatch_date', 'date_out', 'issue_date', 'rental_date', 'date_dispatched', 'out_date'],
            'return_date': ['return_date', 'date_in', 'received_date', 'date_returned', 'in_date'],
            'transaction_type': ['transaction_type', 'type', 'trans_type', 'operation', 'action'],
            'quantity': ['quantity', 'qty', 'amount', 'count'],
            'notes': ['notes', 'comments', 'remarks', 'description', 'details']
        }
        
        for target_field, suggestions in field_suggestions.items():
            for suggestion in suggestions:
                if suggestion in column_names:
                    for col in columns:
                        if col['name'].lower() == suggestion:
                            mapping[target_field] = col['name']
                            break
                    break
        
        return mapping
    
    def close_connection(self):
        
        self.access_connector.close()