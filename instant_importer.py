#!/usr/bin/env python3
"""
INSTANT Transaction Importer
Zero overhead, direct memory operations
"""

import json
import pyodbc
from datetime import datetime, timedelta
from models import Customer, Cylinder
from models_rental_history import RentalHistory

class InstantImporter:
    def __init__(self):
        self.customer_model = Customer()
        self.cylinder_model = Cylinder()
        self.rental_history = RentalHistory()
    
    def instant_import(self, access_file: str, table_name: str, field_mapping: dict, import_type: str = 'transaction') -> tuple:
        """Import data with zero processing overhead - supports transactions, customers, and cylinders"""
        print(f"🚀 INSTANT MODE: Direct memory operations for {import_type}")
        
        # Direct connection without wrapper overhead
        conn = pyodbc.connect(f'DRIVER={{Microsoft Access Driver (*.mdb, *.accdb)}};DBQ={access_file};')
        cursor = conn.cursor()
        
        # Get all data in one shot - no batching, no streaming
        cursor.execute(f"SELECT * FROM [{table_name}]")
        rows = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        
        print(f"Loaded {len(rows):,} rows - processing instantly...")
        
        if import_type == 'customer':
            return self._instant_import_customers(rows, columns, field_mapping, conn)
        elif import_type == 'cylinder':
            return self._instant_import_cylinders(rows, columns, field_mapping, conn)
        else:  # transaction
            return self._instant_import_transactions(rows, columns, field_mapping, conn)
    
    def _instant_import_customers(self, rows, columns, field_mapping, conn):
        """Instant customer import"""
        # Build field mapping indices
        field_indices = {}
        for target_field, source_field in field_mapping.items():
            if source_field and source_field in columns:
                field_indices[target_field] = columns.index(source_field)
        
        # Get existing customers for duplicate checking
        existing_customers = self.customer_model.get_all()
        existing_customer_nos = {c.get('customer_no', '').upper() for c in existing_customers}
        
        imported = 0
        skipped = 0
        
        for row in rows:
            try:
                # Extract customer data using direct array access
                customer_data = {
                    'created_at': datetime.now().isoformat(),
                    'updated_at': datetime.now().isoformat()
                }
                
                # Map fields from row data
                for target_field, col_idx in field_indices.items():
                    if col_idx < len(row) and row[col_idx] is not None:
                        value = str(row[col_idx]).strip()
                        if value:
                            customer_data[target_field] = value
                
                # Validate required fields
                if not customer_data.get('customer_no') or not customer_data.get('customer_name'):
                    skipped += 1
                    continue
                
                # Check for duplicates
                if customer_data['customer_no'].upper() in existing_customer_nos:
                    skipped += 1
                    continue
                
                # Add customer
                self.customer_model.add(customer_data)
                existing_customer_nos.add(customer_data['customer_no'].upper())
                imported += 1
                
            except Exception:
                skipped += 1
        
        conn.close()
        print(f"✅ INSTANT CUSTOMER COMPLETE: {imported:,} imported | {skipped:,} skipped")
        return imported, skipped, []
    
    def _instant_import_cylinders(self, rows, columns, field_mapping, conn):
        """Instant cylinder import"""
        # Build field mapping indices
        field_indices = {}
        for target_field, source_field in field_mapping.items():
            if source_field and source_field in columns:
                field_indices[target_field] = columns.index(source_field)
        
        # Get existing cylinders for duplicate checking
        existing_cylinders = self.cylinder_model.get_all()
        existing_custom_ids = {c.get('custom_id', '').upper() for c in existing_cylinders if c.get('custom_id')}
        
        imported = 0
        skipped = 0
        
        for row in rows:
            try:
                # Extract cylinder data using direct array access
                cylinder_data = {
                    'type': 'Medical Oxygen',  # Default type
                    'size': '40L',             # Default size
                    'status': 'available',     # Default status
                    'location': 'Warehouse',   # Default location
                    'created_at': datetime.now().isoformat(),
                    'updated_at': datetime.now().isoformat()
                }
                
                # Map fields from row data
                for target_field, col_idx in field_indices.items():
                    if col_idx < len(row) and row[col_idx] is not None:
                        value = str(row[col_idx]).strip()
                        if value:
                            cylinder_data[target_field] = value
                
                # Validate required fields - custom_id is required
                if not cylinder_data.get('custom_id'):
                    skipped += 1
                    continue
                
                # Check for duplicates by custom_id
                if cylinder_data['custom_id'].upper() in existing_custom_ids:
                    skipped += 1
                    continue
                
                # Add cylinder
                self.cylinder_model.add(cylinder_data)
                existing_custom_ids.add(cylinder_data['custom_id'].upper())
                imported += 1
                
            except Exception:
                skipped += 1
        
        conn.close()
        print(f"✅ INSTANT CYLINDER COMPLETE: {imported:,} imported | {skipped:,} skipped")
        return imported, skipped, []
    
    def _instant_import_transactions(self, rows, columns, field_mapping, conn):
        """Simple transaction linking - connect customers and cylinders from transaction data"""
        print("🚀 INSTANT TRANSACTION LINKING: Connect customers with cylinders")
        
        # Pre-load data for lookups
        customers_raw = self.customer_model.get_all()
        cylinders_raw = self.cylinder_model.get_all()
        
        # Build lookup tables
        customers = {}
        for c in customers_raw:
            key = str(c.get('customer_no', '')).upper()
            if key:
                customers[key] = c
        
        cylinders = {}
        for cyl in cylinders_raw:
            # Multiple lookup keys for cylinders
            sn = str(cyl.get('serial_number', '')).upper()
            cid = str(cyl.get('custom_id', '')).upper()
            
            if sn: cylinders[sn] = cyl
            if cid: cylinders[cid] = cyl
        
        # Get column indices
        try:
            cust_idx = columns.index(field_mapping['customer_no'])
            cyl_idx = columns.index(field_mapping['cylinder_no'])
            dispatch_idx = columns.index(field_mapping['dispatch_date']) if 'dispatch_date' in field_mapping else None
            return_idx = columns.index(field_mapping['return_date']) if 'return_date' in field_mapping else None
        except (ValueError, KeyError):
            conn.close()
            return 0, 0, ["Required field mapping not found"]
        
        # Process transactions for linking
        linked = 0
        skipped = 0
        cylinders_to_update = {}
        
        for row in rows:
            try:
                # Extract basic data
                cust_no = str(row[cust_idx] or '').strip().upper()
                cyl_no = str(row[cyl_idx] or '').strip().upper()
                
                if not cust_no or not cyl_no:
                    skipped += 1
                    continue
                
                customer = customers.get(cust_no)
                cylinder = cylinders.get(cyl_no)
                
                if not customer or not cylinder:
                    skipped += 1
                    continue
                
                # Get dates
                dispatch_date = ''
                return_date = ''
                
                if dispatch_idx is not None and row[dispatch_idx]:
                    try:
                        dispatch_raw = row[dispatch_idx]
                        if isinstance(dispatch_raw, str):
                            dispatch_date = dispatch_raw[:10] if len(dispatch_raw) >= 10 else dispatch_raw
                        elif hasattr(dispatch_raw, 'strftime'):
                            dispatch_date = dispatch_raw.strftime('%Y-%m-%d')
                    except:
                        pass
                
                if return_idx is not None and row[return_idx]:
                    try:
                        return_raw = row[return_idx]
                        if isinstance(return_raw, str):
                            return_date = return_raw[:10] if len(return_raw) >= 10 else return_raw
                        elif hasattr(return_raw, 'strftime'):
                            return_date = return_raw.strftime('%Y-%m-%d')
                    except:
                        pass
                
                # Update cylinder with most recent transaction info
                cyl_id = cylinder['id']
                if cyl_id not in cylinders_to_update:
                    cylinders_to_update[cyl_id] = cylinder.copy()
                
                cyl_update = cylinders_to_update[cyl_id]
                
                # Link customer to cylinder
                cyl_update['customer_name'] = customer.get('customer_name') or customer.get('name', '')
                cyl_update['customer_phone'] = customer.get('customer_phone') or customer.get('phone', '')
                cyl_update['customer_address'] = customer.get('customer_address') or customer.get('address', '')
                cyl_update['customer_city'] = customer.get('customer_city', '')
                cyl_update['customer_state'] = customer.get('customer_state', '')
                
                # Set status based on return date
                if return_date:
                    cyl_update['status'] = 'available'
                    cyl_update['location'] = 'Warehouse'
                    cyl_update['rented_to'] = None
                    cyl_update['date_returned'] = return_date
                else:
                    cyl_update['status'] = 'rented'
                    cyl_update['rented_to'] = customer['id']
                    cyl_update['location'] = customer.get('customer_address') or customer.get('address', 'Customer Location')
                    cyl_update['date_returned'] = ''
                
                cyl_update['rental_date'] = dispatch_date
                cyl_update['date_borrowed'] = dispatch_date
                cyl_update['updated_at'] = datetime.now().isoformat()
                
                linked += 1
                
            except Exception:
                skipped += 1
        
        conn.close()
        
        # Update cylinders
        if cylinders_to_update:
            print(f"📊 Updating {len(cylinders_to_update):,} cylinders with customer links...")
            all_cylinders = self.cylinder_model.get_all()
            
            # Replace updated cylinders in the full list
            updated_ids = set(cylinders_to_update.keys())
            final_data = [c for c in all_cylinders if c['id'] not in updated_ids] + list(cylinders_to_update.values())
            
            self.cylinder_model.db.save_data(final_data)
            print(f"✅ Updated {len(cylinders_to_update):,} cylinders")
        
        print(f"✅ LINKING COMPLETE: {linked:,} linked | {skipped:,} skipped")
        return linked, skipped, []

if __name__ == "__main__":
    import sys
    if len(sys.argv) >= 4:
        importer = InstantImporter()
        mapping = json.loads(sys.argv[3])
        import_type = sys.argv[4] if len(sys.argv) > 4 else 'transaction'
        importer.instant_import(sys.argv[1], sys.argv[2], mapping, import_type)