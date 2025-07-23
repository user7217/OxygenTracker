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
        from datetime import datetime, timedelta
        
        print(f"Starting optimized transaction import from table: {table_name}")
        print("Processing large dataset with memory optimization...")
        print("Only importing transactions from the past year")
        
        imported_count = 0
        skipped_count = 0
        errors = []
        linked_count = 0
        
        # Calculate date threshold for past year
        one_year_ago = datetime.now() - timedelta(days=365)
        print(f"Date filter: Only importing transactions from {one_year_ago.strftime('%Y-%m-%d')} onwards")
        
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
        
        # Ultra-fast bulk processing - load all data at once for maximum speed
        print("Loading all data for ultra-fast bulk processing...")
        
        try:
            # Load entire table into memory for fastest processing
            cursor = self.access_connector.connection.cursor()
            cursor.execute(f"SELECT * FROM [{table_name}]")
            all_rows = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]
            
            print(f"Processing {len(all_rows):,} rows with ultra-fast bulk operations...")
            
            # Pre-calculate column indices for maximum speed
            col_indices = {}
            for target_field, source_field in field_mapping.items():
                try:
                    col_indices[target_field] = columns.index(source_field)
                except ValueError:
                    continue
            
            customer_col = col_indices.get('customer_no')
            cylinder_col = col_indices.get('cylinder_no')
            dispatch_col = col_indices.get('dispatch_date')
            return_col = col_indices.get('return_date')
            
            # Bulk process all transactions in batches
            batch_operations = []
            
            for row_num, row in enumerate(all_rows, 1):
                # Ultra-fast field extraction
                if customer_col is None or cylinder_col is None:
                    skipped_count += 1
                    continue
                    
                customer_no = str(row[customer_col]).strip().upper() if row[customer_col] else ''
                cylinder_no = str(row[cylinder_col]).strip().upper() if row[cylinder_col] else ''
                
                if not customer_no or not cylinder_no:
                    skipped_count += 1
                    continue
                
                # Fast lookups
                customer = customer_lookup.get(customer_no)
                cylinder = cylinder_lookup.get(cylinder_no)
                
                if not customer or not cylinder:
                    skipped_count += 1
                    continue
                
                # Ultra-fast date processing
                dispatch_date = None
                if dispatch_col is not None and row[dispatch_col]:
                    try:
                        date_val = row[dispatch_col]
                        if isinstance(date_val, str) and len(date_val) >= 10:
                            dispatch_dt = datetime.strptime(date_val[:19] if len(date_val) >= 19 else date_val[:10], 
                                                          '%Y-%m-%d %H:%M:%S' if len(date_val) >= 19 else '%Y-%m-%d')
                        else:
                            dispatch_dt = date_val
                        
                        if dispatch_dt >= one_year_ago:
                            dispatch_date = dispatch_dt.strftime('%Y-%m-%d')
                        else:
                            skipped_count += 1
                            continue
                    except:
                        skipped_count += 1
                        continue
                
                return_date = None
                if return_col is not None and row[return_col]:
                    try:
                        date_val = row[return_col]
                        if isinstance(date_val, str) and len(date_val) >= 10:
                            return_dt = datetime.strptime(date_val[:19] if len(date_val) >= 19 else date_val[:10], 
                                                        '%Y-%m-%d %H:%M:%S' if len(date_val) >= 19 else '%Y-%m-%d')
                        else:
                            return_dt = date_val
                        return_date = return_dt.strftime('%Y-%m-%d')
                    except:
                        pass
                
                # Queue operations for bulk processing
                if dispatch_date:
                    batch_operations.append({
                        'action': 'rent',
                        'cylinder_id': cylinder['id'],
                        'customer_id': customer['id'],
                        'customer': customer,
                        'date': dispatch_date,
                        'return_date': return_date
                    })
                    imported_count += 1
                
                # Progress every 50k rows
                if row_num % 50000 == 0:
                    print(f"Processed: {row_num:,}/{len(all_rows):,} rows ({row_num/len(all_rows)*100:.1f}%)")
            
            # Execute all operations in bulk
            print(f"Executing {len(batch_operations):,} operations in bulk...")
            for i, op in enumerate(batch_operations):
                try:
                    self.cylinder_model.rent_cylinder_with_location(
                        op['cylinder_id'], op['customer_id'], op['date'], op['customer']
                    )
                    if op['return_date']:
                        self.cylinder_model.return_cylinder(op['cylinder_id'], op['return_date'])
                    linked_count += 1
                except:
                    pass
                
                # Ultra-minimal progress for bulk operations
                if i % 10000 == 0 and i > 0:
                    print(f"Operations: {i:,}/{len(batch_operations):,}")
            
            print(f"Bulk processing complete!")
                        
        except Exception as e:
            print(f"Error during transaction import: {e}")
            if len(errors) < 5000:
                errors.append(f"Database error: {str(e)}")
        finally:
            # Always close the connection to release file locks
            if hasattr(self, 'access_connector') and self.access_connector:
                try:
                    self.access_connector.close()
                    print("Database connection closed and file locks released")
                except Exception as e:
                    print(f"Warning: Could not properly close database connection: {e}")
        
        # Ultra-fast summary
        print(f"\n=== ULTRA-FAST Import Complete ===")
        print(f"Processed: {imported_count + skipped_count:,}/{total_rows:,} rows")
        print(f"Imported: {imported_count:,} | Linked: {linked_count:,} | Skipped: {skipped_count:,}")
        
        # Minimal summary for speed
        
        return imported_count, skipped_count, errors
    
    def suggest_transaction_field_mapping(self, table_name: str) -> Dict[str, str]:
        """Suggest field mapping for transaction table"""
        # Get column information from Access table
        columns = self.access_connector.get_table_columns(table_name)
        column_names = [col['name'].lower() for col in columns]
        
        mapping = {}
        
        # Customer number mapping
        for col in ['customer_no', 'customerno', 'customer_number', 'cust_no', 'custno']:
            if col in column_names:
                mapping['customer_no'] = col
                break
        
        # Cylinder number mapping
        for col in ['cylinder_no', 'cylinderno', 'cylinder_number', 'cyl_no', 'cylno', 'serial', 'serial_no']:
            if col in column_names:
                mapping['cylinder_no'] = col
                break
                
        # Dispatch date mapping
        for col in ['dispatch_date', 'dispatchdate', 'out_date', 'outdate', 'rental_date', 'rentaldate']:
            if col in column_names:
                mapping['dispatch_date'] = col
                break
                
        # Return date mapping
        for col in ['return_date', 'returndate', 'in_date', 'indate', 'received_date', 'receiveddate']:
            if col in column_names:
                mapping['return_date'] = col
                break
                
        # Transaction type mapping
        for col in ['transaction_type', 'transactiontype', 'type', 'action', 'operation']:
            if col in column_names:
                mapping['transaction_type'] = col
                break
        
        return mapping
    
    def close_connection(self):
        """Close Access database connection and release file locks"""
        if hasattr(self, 'access_connector') and self.access_connector:
            try:
                self.access_connector.close()
                print("Access database connection closed")
            except Exception as e:
                print(f"Warning: Error closing database connection: {e}")
            finally:
                self.access_connector = None
