"""
Varasicyl JSON Data Importer

Imports customer and cylinder data from JSON files with validation and field mapping.
Supports various JSON formats and provides detailed import feedback.

Author: Development Team
Date: August 2025
Version: 1.0
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Any, Tuple
from db_service import CustomerService, CylinderService, RentalHistoryService


class JSONImporter:
    """JSON data importer with validation and field mapping"""
    
    def __init__(self):
        self.supported_formats = {
            'customers': ['customer_name', 'customer_no', 'customer_phone', 'customer_email', 'customer_address', 'customer_city', 'customer_state', 'customer_apgst', 'customer_cst'],
            'cylinders': ['serial_number', 'custom_id', 'type', 'size', 'status', 'location', 'rented_to', 'date_borrowed', 'date_returned', 'customer_name', 'customer_email'],
            'rental_transactions': ['customer_no', 'customer_name', 'customer_phone', 'customer_address', 'customer_city', 'customer_state', 'cylinder_no', 'cylinder_custom_id', 'cylinder_serial', 'cylinder_type', 'cylinder_size', 'dispatch_date', 'return_date', 'rental_days', 'status'],
            'rental_history': ['customer_id', 'customer_no', 'customer_name', 'customer_phone', 'customer_email', 'customer_address', 'customer_city', 'customer_state', 'cylinder_id', 'cylinder_no', 'cylinder_custom_id', 'cylinder_serial', 'cylinder_type', 'cylinder_size', 'dispatch_date', 'return_date', 'date_borrowed', 'date_returned', 'rental_days', 'location', 'status']
        }
        
    def analyze_json_file(self, file_path: str) -> Dict[str, Any]:
        """Analyze JSON file structure and detect data type"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if not data:
                return {'error': 'File is empty', 'data_type': None, 'records': 0}
            
            # Handle different JSON structures
            if isinstance(data, list):
                if not data:
                    return {'error': 'No records found', 'data_type': None, 'records': 0}
                sample_record = data[0]
                records_count = len(data)
            elif isinstance(data, dict):
                # Check if it's a wrapper object with data arrays
                if 'customers' in data:
                    sample_record = data['customers'][0] if data['customers'] else {}
                    records_count = len(data['customers'])
                    data = data['customers']
                elif 'cylinders' in data:
                    sample_record = data['cylinders'][0] if data['cylinders'] else {}
                    records_count = len(data['cylinders'])
                    data = data['cylinders']
                elif 'rental_history' in data:
                    sample_record = data['rental_history'][0] if data['rental_history'] else {}
                    records_count = len(data['rental_history'])
                    data = data['rental_history']
                else:
                    # Single record
                    sample_record = data
                    records_count = 1
                    data = [data]
            else:
                return {'error': 'Invalid JSON format', 'data_type': None, 'records': 0}
            
            # Detect data type based on fields
            fields = list(sample_record.keys()) if sample_record else []
            data_type = self._detect_data_type(fields)
            
            return {
                'data_type': data_type,
                'records': records_count,
                'fields': fields,
                'sample_record': sample_record,
                'data': data,
                'error': None
            }
            
        except json.JSONDecodeError as e:
            return {'error': f'Invalid JSON format: {str(e)}', 'data_type': None, 'records': 0}
        except Exception as e:
            return {'error': f'Error reading file: {str(e)}', 'data_type': None, 'records': 0}
    
    def _detect_data_type(self, fields: List[str]) -> str:
        """Detect data type based on field names"""
        customer_indicators = ['customer_name', 'customer_no', 'customer_phone', 'name', 'phone', 'email']
        cylinder_indicators = ['serial_number', 'type', 'size', 'cylinder_id', 'custom_id']
        rental_indicators = ['dispatch_date', 'return_date', 'rental_days', 'cylinder_no', 'cylinder_custom_id']
        rental_history_indicators = ['rental_history', 'history', 'completed', 'finished', 'returned']
        
        customer_score = sum(1 for field in fields if any(indicator in field.lower() for indicator in customer_indicators))
        cylinder_score = sum(1 for field in fields if any(indicator in field.lower() for indicator in cylinder_indicators))
        rental_score = sum(1 for field in fields if any(indicator in field.lower() for indicator in rental_indicators))
        history_score = sum(1 for field in fields if any(indicator in field.lower() for indicator in rental_history_indicators))
        
        # Check for specific rental history patterns
        if history_score > 0 or ('dispatch_date' in fields and 'return_date' in fields and 'rental_days' in fields):
            return 'rental_history'
        elif customer_score >= cylinder_score and customer_score >= rental_score:
            return 'customers'
        elif cylinder_score >= rental_score:
            return 'cylinders'
        else:
            return 'rental_transactions'
    
    def map_fields(self, source_fields: List[str], target_type: str) -> Dict[str, str]:
        """Automatic field mapping with manual override support"""
        target_fields = self.supported_formats[target_type]
        mapping = {}
        
        # Automatic mapping based on field name similarity
        for source_field in source_fields:
            best_match = None
            best_score = 0
            
            for target_field in target_fields:
                # Calculate similarity score
                score = self._calculate_field_similarity(source_field.lower(), target_field.lower())
                if score > best_score and score > 0.5:  # Minimum 50% similarity
                    best_match = target_field
                    best_score = score
            
            if best_match:
                mapping[source_field] = best_match
        
        return mapping
    
    def _calculate_field_similarity(self, source: str, target: str) -> float:
        """Calculate field name similarity score"""
        # Simple similarity based on common substrings
        if source == target:
            return 1.0
        
        # Check for exact substring matches
        if source in target or target in source:
            return 0.8
        
        # Check for common keywords
        keywords = {
            'name': ['name', 'nm', 'title'],
            'phone': ['phone', 'tel', 'mobile', 'cell'],
            'email': ['email', 'mail', '@'],
            'address': ['address', 'addr', 'location'],
            'city': ['city', 'town'],
            'state': ['state', 'province', 'region'],
            'serial': ['serial', 'sn', 'number'],
            'type': ['type', 'category', 'kind'],
            'size': ['size', 'capacity', 'volume'],
            'status': ['status', 'state', 'condition'],
            'date': ['date', 'time', 'created', 'modified']
        }
        
        for key, variations in keywords.items():
            if key in target and any(var in source for var in variations):
                return 0.7
        
        return 0.0
    
    def validate_data(self, data: List[Dict], data_type: str, field_mapping: Dict[str, str]) -> Tuple[List[Dict], List[str]]:
        """Validate and transform data for import"""
        valid_records = []
        errors = []
        
        for i, record in enumerate(data):
            try:
                mapped_record = {}
                
                # Apply field mapping
                for source_field, target_field in field_mapping.items():
                    if source_field in record:
                        value = record[source_field]
                        mapped_record[target_field] = self._validate_and_transform_field(target_field, value, data_type)
                
                # Validate required fields
                validation_result = self._validate_required_fields(mapped_record, data_type)
                if validation_result['valid']:
                    valid_records.append(mapped_record)
                else:
                    errors.append(f"Record {i+1}: {validation_result['error']}")
                    
            except Exception as e:
                errors.append(f"Record {i+1}: Error processing - {str(e)}")
        
        return valid_records, errors
    
    def _validate_and_transform_field(self, field_name: str, value: Any, data_type: str) -> Any:
        """Validate and transform individual field values"""
        if value is None or value == '':
            return None
        
        # Convert to string and strip whitespace
        str_value = str(value).strip()
        
        # Date field transformations
        if 'date' in field_name:
            if str_value and str_value.lower() not in ['', 'null', 'none']:
                try:
                    # Try to parse various date formats
                    for fmt in ['%Y-%m-%d', '%m/%d/%Y', '%d/%m/%Y', '%Y-%m-%d %H:%M:%S']:
                        try:
                            dt = datetime.strptime(str_value, fmt)
                            return dt.isoformat()
                        except ValueError:
                            continue
                    # If no format matches, return as-is for manual review
                    return str_value
                except:
                    return None
            return None
        
        # Phone number cleaning
        if 'phone' in field_name:
            # Handle "0.0" phone numbers from exports
            if str_value in ['0.0', '0', 'null', 'NULL']:
                return None
            # Remove common phone number formatting
            cleaned = ''.join(c for c in str_value if c.isdigit() or c in '+- ()')
            return cleaned if cleaned and cleaned != '0' else None
        
        # Email validation
        if 'email' in field_name:
            if '@' in str_value and '.' in str_value:
                return str_value.lower()
            return None
        
        # Status field normalization
        if field_name == 'status':
            status_map = {
                'available': 'Available',
                'rented': 'Rented',
                'maintenance': 'Maintenance',
                'out of service': 'Out of Service',
                'available': 'Available'
            }
            return status_map.get(str_value.lower(), str_value)
        
        return str_value if str_value else None
    
    def _validate_required_fields(self, record: Dict, data_type: str) -> Dict[str, Any]:
        """Validate required fields for each data type"""
        required_fields = {
            'customers': ['customer_name'],
            'cylinders': ['type', 'size'],
            'rental_transactions': ['customer_no', 'cylinder_custom_id', 'dispatch_date'],
            'rental_history': ['customer_name', 'cylinder_custom_id', 'dispatch_date']
        }
        
        missing_fields = []
        for field in required_fields.get(data_type, []):
            if field not in record or not record[field]:
                missing_fields.append(field)
        
        if missing_fields:
            return {'valid': False, 'error': f"Missing required fields: {', '.join(missing_fields)}"}
        
        return {'valid': True, 'error': None}
    
    def import_data(self, valid_records: List[Dict], data_type: str) -> Dict[str, Any]:
        """Import validated data into database"""
        imported_count = 0
        errors = []
        
        try:
            if data_type == 'customers':
                return self._import_customers(valid_records)
            elif data_type == 'cylinders':
                return self._import_cylinders(valid_records)
            elif data_type == 'rental_transactions':
                return self._import_rental_transactions(valid_records)
            elif data_type == 'rental_history':
                return self._import_rental_history(valid_records)
            else:
                return {'success': False, 'error': 'Unknown data type', 'imported': 0}
                
        except Exception as e:
            return {'success': False, 'error': f'Import failed: {str(e)}', 'imported': imported_count}
    
    def _import_customers(self, customers: List[Dict]) -> Dict[str, Any]:
        """Import customer records"""
        imported_count = 0
        errors = []
        
        with CustomerService() as customer_service:
            for customer_data in customers:
                try:
                    # Set defaults for missing fields
                    customer_data.setdefault('customer_city', 'Unknown')
                    customer_data.setdefault('customer_state', 'Unknown')
                    customer_data.setdefault('customer_address', '')
                    
                    # Remove system fields that shouldn't be imported
                    system_fields = ['id', 'created_at', 'updated_at']
                    for field in system_fields:
                        customer_data.pop(field, None)
                    
                    # Handle empty email field
                    if not customer_data.get('customer_email'):
                        customer_data['customer_email'] = None
                    
                    customer_service.create(customer_data)
                    imported_count += 1
                except Exception as e:
                    errors.append(f"Customer '{customer_data.get('customer_name', 'Unknown')}': {str(e)}")
        
        return {
            'success': len(errors) == 0,
            'imported': imported_count,
            'errors': errors,
            'total': len(customers)
        }
    
    def _import_cylinders(self, cylinders: List[Dict]) -> Dict[str, Any]:
        """Import/update cylinder records with exact JSON structure preservation"""
        imported_count = 0
        updated_count = 0
        errors = []
        
        with CylinderService() as cylinder_service:
            for cylinder_data in cylinders:
                try:
                    # Check if cylinder already exists by ID or custom_id
                    existing_cylinder = None
                    cylinder_id = cylinder_data.get('id')
                    custom_id = cylinder_data.get('custom_id')
                    
                    if cylinder_id:
                        existing_cylinder = cylinder_service.find_by_any_identifier(cylinder_id)
                    elif custom_id:
                        existing_cylinder = cylinder_service.find_by_any_identifier(custom_id)
                    
                    # Set defaults only for truly missing required fields
                    cylinder_data.setdefault('status', 'Available')
                    cylinder_data.setdefault('location', 'Warehouse')
                    
                    # Handle empty strings vs None for customer fields
                    for field in ['customer_name', 'customer_email', 'customer_phone', 
                                 'customer_address', 'customer_city', 'customer_state',
                                 'date_returned', 'rental_date', 'date_borrowed']:
                        if field in cylinder_data:
                            value = cylinder_data[field]
                            # Keep empty strings as empty strings, not None
                            if value is None:
                                cylinder_data[field] = ""
                    
                    # Link to customer if customer data exists and cylinder is dispatched/rented
                    if (cylinder_data.get('status', '').lower() in ['rented', 'dispatched'] and 
                        cylinder_data.get('customer_name')):
                        customer_link_id = self._find_or_create_customer_from_cylinder(cylinder_data)
                        if customer_link_id:
                            cylinder_data['rented_to'] = customer_link_id
                    
                    if existing_cylinder:
                        # Update existing cylinder with new data
                        actual_id = existing_cylinder.get('id')
                        success = cylinder_service.update_exact(actual_id, cylinder_data)
                        if success:
                            updated_count += 1
                        else:
                            errors.append(f"Cylinder '{cylinder_id or custom_id}': Failed to update")
                    else:
                        # Create new cylinder
                        if not cylinder_data.get('id') and not cylinder_data.get('custom_id'):
                            cylinder_data['custom_id'] = f"CYL-{datetime.now().strftime('%Y%m%d')}-{imported_count+1:04d}"
                        
                        cylinder_service.create_exact(cylinder_data)
                        imported_count += 1
                        
                except Exception as e:
                    errors.append(f"Cylinder '{cylinder_data.get('id', cylinder_data.get('custom_id', 'Unknown'))}': {str(e)}")
        
        return {
            'success': len(errors) == 0,
            'imported': imported_count,
            'updated': updated_count,
            'errors': errors,
            'total': len(cylinders)
        }
    
    def _find_or_create_customer_from_cylinder(self, cylinder_data: Dict) -> str:
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
    
    def _import_rental_transactions(self, transactions: List[Dict]) -> Dict[str, Any]:
        """Import rental transaction records optimized for 256MB RAM"""
        imported_count = 0
        skipped_count = 0
        errors = []
        batch_size = 10  # Ultra-small batches for memory constraints
        
        print(f"Starting import of {len(transactions)} rental transactions...")
        
        # Import using RentalHistoryService (transactions are just rental history records)
        from db_service import RentalHistoryService
        
        with RentalHistoryService() as rental_service:
            # Skip pre-loading IDs for memory efficiency on 256MB systems
            
            # Process in batches
            for batch_start in range(0, len(transactions), batch_size):
                batch_end = min(batch_start + batch_size, len(transactions))
                batch = transactions[batch_start:batch_end]
                
                print(f"Processing transaction batch {batch_start//batch_size + 1}: records {batch_start+1}-{batch_end}")
                
                batch_records = []
                for i, transaction_data in enumerate(batch):
                    try:
                        processed_data = transaction_data.copy()
                        
                        # Check for duplicates using database query
                        record_id = processed_data.get('id', '')
                        if record_id:
                            from models import RentalHistory
                            existing_record = rental_service.db.query(rental_service.db.query(RentalHistory).filter(RentalHistory.id == record_id).exists()).scalar()
                            if existing_record:
                                skipped_count += 1
                                continue
                        
                        # Remove system fields
                        system_fields = ['created_at', 'updated_at']
                        for field in system_fields:
                            processed_data.pop(field, None)
                        
                        # Convert date fields to proper date objects
                        for date_field in ['dispatch_date', 'return_date']:
                            if date_field in processed_data and processed_data[date_field]:
                                try:
                                    date_str = str(processed_data[date_field])
                                    if 'T' in date_str:  # ISO format
                                        dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                                        processed_data[date_field] = dt.date()
                                    else:
                                        dt = datetime.strptime(date_str[:10], '%Y-%m-%d')
                                        processed_data[date_field] = dt.date()
                                except:
                                    processed_data[date_field] = None
                        
                        # Set default status
                        processed_data.setdefault('status', 'completed')
                        
                        # Generate ID if missing
                        if 'id' not in processed_data or not processed_data['id']:
                            processed_data['id'] = f"RT-{datetime.now().strftime('%Y%m%d%H%M%S')}-{(batch_start + i + 1):04d}"
                        
                        batch_records.append(processed_data)
                        
                    except Exception as e:
                        customer_info = transaction_data.get('customer_name', transaction_data.get('customer_no', 'Unknown'))
                        errors.append(f"Transaction {batch_start + i + 1} for '{customer_info}': {str(e)}")
                
                # Memory-efficient individual inserts
                for record_data in batch_records:
                    try:
                        from models import RentalHistory
                        rental_history = RentalHistory(**record_data)
                        rental_service.db.add(rental_history)
                        rental_service.db.commit()
                        
                        imported_count += 1
                        
                        # Clear from session to free memory
                        rental_service.db.expunge(rental_history)
                        del rental_history
                        
                    except Exception as e:
                        rental_service.db.rollback()
                        customer_info = record_data.get('customer_name', record_data.get('customer_no', 'Unknown'))
                        errors.append(f"Transaction insert failed for '{customer_info}': {str(e)}")
                
                del batch_records
                print(f"Completed transaction batch {batch_start//batch_size + 1}: {imported_count} total imported")
                
                # Force garbage collection every 50 batches
                if (batch_start // batch_size + 1) % 50 == 0:
                    import gc
                    gc.collect()
                    print(f"Memory cleanup after {batch_start//batch_size + 1} transaction batches")
        
        print(f"Transaction import completed: {imported_count} imported, {skipped_count} skipped, {len(errors)} errors")
        
        return {
            'success': len(errors) == 0,
            'imported': imported_count,
            'skipped': skipped_count,
            'errors': errors,
            'total': len(transactions)
        }
    
    def _import_rental_history(self, history_records: List[Dict]) -> Dict[str, Any]:
        """Import rental history records optimized for low-memory environments (256MB RAM)"""
        imported_count = 0
        skipped_count = 0
        errors = []
        batch_size = 10  # Ultra-small batches for 256MB RAM constraint
        
        print(f"Starting import of {len(history_records)} rental history records...")
        
        # For very large imports on 256MB systems, warn user
        if len(history_records) > 10000:
            print(f"WARNING: Large import ({len(history_records)} records) on 256MB system may be slow. Consider splitting file.")
        
        with RentalHistoryService() as rental_service:
            # For 256MB RAM: Skip pre-loading all existing IDs to save memory
            # Instead, check duplicates per-record using database queries
            print(f"Starting memory-optimized import (checking duplicates per-record)")
            
            # Process records in batches
            for batch_start in range(0, len(history_records), batch_size):
                batch_end = min(batch_start + batch_size, len(history_records))
                batch = history_records[batch_start:batch_end]
                
                print(f"Processing batch {batch_start//batch_size + 1}: records {batch_start+1}-{batch_end} of {len(history_records)}")
                
                batch_records = []
                for i, history_data in enumerate(batch):
                    try:
                        # Create a copy to avoid modifying original data
                        processed_data = history_data.copy()
                        
                        # Check for duplicates by ID using database query (memory efficient)
                        record_id = processed_data.get('id', '')
                        if record_id:
                            from models import RentalHistory
                            existing_record = rental_service.db.query(rental_service.db.query(RentalHistory).filter(RentalHistory.id == record_id).exists()).scalar()
                            if existing_record:
                                skipped_count += 1
                                continue
                        
                        # Remove system fields that shouldn't be imported
                        system_fields = ['created_at', 'updated_at']
                        for field in system_fields:
                            processed_data.pop(field, None)
                        
                        # Convert date fields to proper date objects (not datetime to match model)
                        for date_field in ['dispatch_date', 'return_date']:
                            if date_field in processed_data and processed_data[date_field]:
                                try:
                                    date_str = str(processed_data[date_field])
                                    if 'T' in date_str:  # ISO format
                                        dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                                        processed_data[date_field] = dt.date()
                                    else:
                                        # Try to parse as date string
                                        dt = datetime.strptime(date_str[:10], '%Y-%m-%d')
                                        processed_data[date_field] = dt.date()
                                except Exception as e:
                                    # If date parsing fails, set to None
                                    processed_data[date_field] = None
                        
                        # Set default values for missing fields
                        processed_data.setdefault('status', 'completed')
                        
                        # Generate unique ID if not provided
                        if 'id' not in processed_data or not processed_data['id']:
                            processed_data['id'] = f"RT-{datetime.now().strftime('%Y%m%d%H%M%S')}-{(batch_start + i + 1):04d}"
                        
                        batch_records.append(processed_data)
                        
                    except Exception as e:
                        customer_info = history_data.get('customer_name', history_data.get('customer_no', 'Unknown'))
                        errors.append(f"Record {batch_start + i + 1} for '{customer_info}': {str(e)}")
                
                # Ultra-efficient insert for low memory: process records one by one
                for record_data in batch_records:
                    try:
                        # Use direct SQL insert to minimize memory usage
                        from models import RentalHistory
                        rental_history = RentalHistory(**record_data)
                        rental_service.db.add(rental_history)
                        rental_service.db.commit()  # Commit immediately to free memory
                        
                        imported_count += 1
                        
                        # Clear object from session to free memory
                        rental_service.db.expunge(rental_history)
                        del rental_history
                        
                    except Exception as e:
                        rental_service.db.rollback()
                        customer_info = record_data.get('customer_name', record_data.get('customer_no', 'Unknown'))
                        errors.append(f"Insert failed for '{customer_info}': {str(e)}")
                
                # Clear processed batch from memory
                del batch_records
                print(f"Completed batch {batch_start//batch_size + 1}: {imported_count} total imported, {skipped_count} skipped")
                
                # Force garbage collection every 50 batches to manage memory on 256MB systems
                if (batch_start // batch_size + 1) % 50 == 0:
                    import gc
                    gc.collect()
                    print(f"Memory cleanup after {batch_start//batch_size + 1} batches")
        
        print(f"Import completed: {imported_count} imported, {skipped_count} skipped duplicates, {len(errors)} errors")
        
        return {
            'success': len(errors) == 0,
            'imported': imported_count,
            'skipped': skipped_count,
            'errors': errors,
            'total': len(history_records)
        }