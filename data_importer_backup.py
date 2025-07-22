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
            # Cylinder field mappings (custom_id is now REQUIRED, serial_number is optional)
            field_suggestions = {
                'custom_id': ['id', 'custom_id', 'cylinder_number', 'cylinder_no', 'cylinder_id', 'ref_number'],
                'serial_number': ['serial_number', 'serial', 'cylinder_serial', 'manufacturer_serial'],
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
        
        # Get existing cylinders once at the start for performance
        existing_cylinders = self.cylinder_model.get_all() if skip_duplicates else []
        existing_custom_ids = [c.get('custom_id', '').lower() for c in existing_cylinders if c.get('custom_id')]
        
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
                
                # Set default type if not provided
                if not cylinder_data.get('type'):
                    cylinder_data['type'] = 'Medical Oxygen'
                
                # Set default size if not provided
                if not cylinder_data.get('size'):
                    cylinder_data['size'] = '40L'
                
                # Check required fields - only custom_id is REQUIRED, type, size, serial_number are optional
                required_fields = ['custom_id']
                missing_fields = [f for f in required_fields if not cylinder_data.get(f)]
                
                if missing_fields:
                    errors.append(f"Row skipped - missing required fields: {', '.join(missing_fields)}")
                    skipped_count += 1
                    continue
                
                # Check for duplicates based on custom_id (performance optimized)
                if skip_duplicates and cylinder_data['custom_id'].lower() in existing_custom_ids:
                    skipped_count += 1
                    continue
                
                # Add to existing custom_ids list to prevent duplicates within this import batch
                existing_custom_ids.append(cylinder_data['custom_id'].lower())
                
                # Add cylinder
                self.cylinder_model.add(cylinder_data)
                imported_count += 1
                
            except Exception as e:
                errors.append(f"Error importing row: {str(e)}")
                skipped_count += 1
        
        return imported_count, skipped_count, errors
    
    def import_transactions(self, table_name: str, field_mapping: Dict[str, str], 
                           skip_duplicates: bool = True) -> Tuple[int, int, List[str]]:
        """
        Import transactions from Access table and link customers to cylinders
        Expected fields: customer_no, cylinder_no, transaction_date, transaction_type, etc.
        Optimized for large datasets (292k+ rows) with memory-efficient processing
        """
        print(f"Starting optimized transaction import from table: {table_name}")
        print("Processing large dataset with memory optimization...")
        
        imported_count = 0
        skipped_count = 0
        errors = []
        linked_count = 0
        
        # Get row count first for progress tracking
        try:
            cursor = self.access_connector.connection.cursor()
            cursor.execute(f"SELECT COUNT(*) FROM [{table_name}]")
            total_rows = cursor.fetchone()[0]
            print(f"Total rows to process: {total_rows:,}")
        except Exception as e:
            print(f"Could not get row count: {e}")
            total_rows = 0
        
        # Get existing customers and cylinders for validation (fetch once for performance)
        print("Loading existing customers and cylinders for transaction import...")
        existing_customers = self.customer_model.get_all()
        existing_cylinders = self.cylinder_model.get_all()
        
        # Create optimized lookup dictionaries for faster searching
        customer_lookup = {c.get('customer_no', '').upper(): c for c in existing_customers}
        cylinder_lookup = {}
        
        # Build cylinder lookup with multiple identifiers (serial_number, custom_id)
        for cyl in existing_cylinders:
            # Add by serial number
            if cyl.get('serial_number'):
                cylinder_lookup[cyl.get('serial_number', '').upper()] = cyl
            
            # Add by custom_id (cylinder number)
            if cyl.get('custom_id'):
                cylinder_lookup[cyl.get('custom_id', '').upper()] = cyl
            
            # Also add by system ID as fallback
            if cyl.get('id'):
                cylinder_lookup[cyl.get('id', '').upper()] = cyl
        
        print(f"Found {len(customer_lookup)} customers and {len(cylinder_lookup)} cylinders for linking")
        
        # Process data using cursor streaming for memory efficiency
        print("Processing transactions with memory-optimized streaming...")
        
        try:
            # Use cursor to stream data instead of loading all into memory
            cursor = self.access_connector.connection.cursor()
            cursor.execute(f"SELECT * FROM [{table_name}]")
            
            # Get column names
            columns = [desc[0] for desc in cursor.description]
            
            row_num = 0
            while True:
                # Fetch rows in batches to avoid memory overload
                rows = cursor.fetchmany(1000)  # Process 1000 rows at a time
                if not rows:
                    break
                
                for row in rows:
                    row_num += 1
                    
                    # Progress reporting every 1000 rows
                    if row_num % 1000 == 0 and total_rows > 0:
                        progress_pct = (row_num / total_rows) * 100
                        print(f"Progress: {row_num:,}/{total_rows:,} rows ({progress_pct:.1f}%)")
                        print(f"  Imported: {imported_count:,}, Linked: {linked_count:,}, Skipped: {skipped_count:,}, Errors: {len(errors)}")
                    
                    # Early termination check - stop if too many errors or skips
                    if len(errors) > 5000 or (total_rows > 0 and skipped_count > total_rows * 0.5):
                        print(f"Stopping early: {len(errors)} errors, {skipped_count:,} skipped rows")
                        print("This often happens when customer/cylinder IDs in transactions don't match imported data")
                        break
                    
                    try:
                        # Convert row to dictionary
                        row_dict = {}
                        for i, value in enumerate(row):
                            row_dict[columns[i]] = str(value).strip() if value is not None else ''
                        
                        # Map fields from Access table
                        transaction_data = {}
                        for target_field, source_field in field_mapping.items():
                            if source_field in row_dict and row_dict[source_field]:
                                transaction_data[target_field] = row_dict[source_field]
                        
                        # Check required fields for transaction processing
                        required_fields = ['customer_no', 'cylinder_no']
                        missing_fields = [f for f in required_fields if not transaction_data.get(f)]
                        
                        if missing_fields:
                            # Only log first few missing field errors to prevent spam
                            if len(errors) < 100:
                                errors.append(f"Row {row_num}: Missing required fields: {', '.join(missing_fields)}")
                            skipped_count += 1
                            continue
                        
                        customer_no = transaction_data['customer_no'].upper()
                        cylinder_no = transaction_data['cylinder_no'].upper()
                        
                        # Find customer by customer_no
                        customer = customer_lookup.get(customer_no)
                        if not customer:
                            # Only log first few customer not found errors to prevent spam
                            if len(errors) < 500:
                                errors.append(f"Row {row_num}: Customer '{customer_no}' not found")
                            skipped_count += 1
                            continue
                        
                        # Find cylinder by cylinder_no (could be serial_number or custom_id)
                        cylinder = cylinder_lookup.get(cylinder_no)
                        if not cylinder:
                            # Only log first few cylinder not found errors to prevent spam
                            if len(errors) < 500:
                                errors.append(f"Row {row_num}: Cylinder '{cylinder_no}' not found")
                            skipped_count += 1
                            continue
                        
                        # Process the transaction (same logic as before but inline for performance)
                        dispatch_date = transaction_data.get('dispatch_date', '')
                        return_date = transaction_data.get('return_date', '')
                        
                        # Process transaction based on data
                        if dispatch_date and return_date:
                            # Complete rental cycle
                            try:
                                self.cylinder_model.rent_cylinder_with_location(
                                    cylinder['id'], 
                                    customer['id'], 
                                    customer,
                                    dispatch_date
                                )
                                self.cylinder_model.return_cylinder(cylinder['id'], return_date)
                                linked_count += 1
                            except Exception as e:
                                if len(errors) < 5000:
                                    errors.append(f"Row {row_num}: Failed to process complete rental cycle: {str(e)}")
                        elif dispatch_date:
                            # Only dispatch
                            try:
                                self.cylinder_model.rent_cylinder_with_location(
                                    cylinder['id'], 
                                    customer['id'], 
                                    customer,
                                    dispatch_date
                                )
                                linked_count += 1
                            except Exception as e:
                                if len(errors) < 5000:
                                    errors.append(f"Row {row_num}: Failed to rent cylinder: {str(e)}")
                        
                        imported_count += 1
                        
                    except Exception as e:
                        # Limit errors stored to prevent memory issues with large datasets
                        if len(errors) < 5000:
                            errors.append(f"Row {row_num}: Error processing transaction: {str(e)}")
                        skipped_count += 1
                
                # Check if we need to break from outer loop
                if len(errors) > 5000 or (total_rows > 0 and skipped_count > total_rows * 0.5):
                    break
                        
        except Exception as e:
            print(f"Error during transaction import: {e}")
            if len(errors) < 5000:
                errors.append(f"Database error: {str(e)}")
                        cylinder['id'], 
                        customer['id'], 
                        default_date,  # Use current date as fallback
                        customer
                    )
                    if success_rent:
                        success_return = self.cylinder_model.return_cylinder(
                            cylinder['id'], 
                            return_date
                        )
                        if success_return:
                            linked_count += 1
                            # Reduced console output for performance
                        else:
                            errors.append(f"Row {row_num}: Failed to return cylinder {cylinder_no}")
                    else:
                        errors.append(f"Row {row_num}: Failed to establish rental for cylinder {cylinder_no}")
                        
                else:
                    # No specific dates - determine status based on transaction type or default behavior
                    if transaction_type in ['return', 'returned', 'in', 'receive']:
                        # Return operation
                        success = self.cylinder_model.return_cylinder(cylinder['id'])
                        if success:
                            linked_count += 1
                            # Reduced console output for performance
                        else:
                            errors.append(f"Row {row_num}: Failed to return cylinder {cylinder_no}")
                    else:
                        # Default to rental with customer location update
                        # Use a default date if no date specified
                        from datetime import datetime
                        default_date = datetime.now().isoformat()
                        success = self.cylinder_model.rent_cylinder_with_location(
                            cylinder['id'], 
                            customer['id'],
                            default_date,  # Use current date as fallback
                            customer  # Pass customer data for location
                        )
                        if success:
                            linked_count += 1
                            # Reduced console output for performance
                        else:
                            errors.append(f"Row {row_num}: Failed to rent cylinder {cylinder_no}")
                
                imported_count += 1
                
            except Exception as e:
                # Limit errors stored to prevent memory issues with large datasets
                if len(errors) < 5000:
                    errors.append(f"Row {row_num}: Error processing transaction: {str(e)}")
                skipped_count += 1
        
        # Final summary with detailed statistics
        processed_rows = imported_count + skipped_count
        print(f"\n=== Transaction Import Summary ===")
        print(f"Total rows in table: {total_rows}")
        print(f"Rows processed: {processed_rows} ({processed_rows/total_rows*100:.1f}%)")
        print(f"Successfully imported: {imported_count}")
        print(f"Successfully linked: {linked_count}")
        print(f"Skipped: {skipped_count}")
        print(f"Errors stored: {len(errors)}")
        
        if processed_rows < total_rows:
            print(f"WARNING: Only processed {processed_rows} out of {total_rows} rows!")
            print("This could be due to:")
            print("- Too many customer/cylinder ID mismatches")
            print("- Memory limitations with large dataset")
            print("- Data quality issues in transaction table")
        
        return imported_count, skipped_count, errors
    
    def suggest_transaction_field_mapping(self, table_name: str) -> Dict[str, str]:
        """Suggest field mapping for transaction table"""
        columns = self.access_connector.get_table_columns(table_name)
        column_names = [col['name'].lower() for col in columns]
        
        mapping = {}
        
        # Transaction field mappings for dispatch and return dates
        field_suggestions = {
            'customer_no': ['customer_no', 'customer_number', 'cust_no', 'customer_id', 'customer_code'],
            'cylinder_no': ['cylinder_no', 'cylinder_number', 'cylinder_id', 'serial_number', 'cylinder_serial', 'custom_id'],
            'dispatch_date': ['dispatch_date', 'date_out', 'issue_date', 'rental_date', 'date_dispatched', 'out_date'],
            'return_date': ['return_date', 'date_in', 'received_date', 'date_returned', 'in_date'],
            'transaction_type': ['transaction_type', 'type', 'trans_type', 'operation', 'action'],
            'quantity': ['quantity', 'qty', 'amount', 'count'],
            'notes': ['notes', 'comments', 'remarks', 'description', 'details']
        }
        
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
    
    def close_connection(self):
        """Close Access database connection"""
        self.access_connector.close()