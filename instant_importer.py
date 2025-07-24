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
        """Import transactions with 6-month filter - update cylinders + customer rental history"""
        print("🚀 INSTANT TRANSACTION MODE: 6-month filter + customer rental history")
        
        # Pre-load ALL data for fast lookups
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
            sid = str(cyl.get('id', '')).upper()
            
            if sn: cylinders[sn] = cyl
            if cid: cylinders[cid] = cyl  
            if sid: cylinders[sid] = cyl
        
        # Pre-calculate column indices
        try:
            cust_idx = columns.index(field_mapping['customer_no'])
            cyl_idx = columns.index(field_mapping['cylinder_no'])
            dispatch_idx = columns.index(field_mapping['dispatch_date']) if 'dispatch_date' in field_mapping else None
            return_idx = columns.index(field_mapping['return_date']) if 'return_date' in field_mapping else None
        except (ValueError, KeyError):
            conn.close()
            return 0, 0, ["Required field mapping not found"]
        
        # 6-month cutoff filter
        six_months_ago = datetime.now() - timedelta(days=180)
        
        # Process transactions with 6-month filter
        operations = []
        rental_entries = []
        customer_rentals = {}  # Group by customer for embedding
        imported = 0
        skipped = 0
        
        for row in rows:
            try:
                # Extract data
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
                
                # Queue cylinder update operation - ALL data for active dispatches/available cylinders
                operations.append((cylinder['id'], customer['id'], customer, dispatch_date, return_date))
                
                # Create rental history entry - apply 6-month filter ONLY for rental history
                include_in_history = True
                if return_date:
                    try:
                        return_dt = datetime.strptime(return_date, '%Y-%m-%d')
                        if return_dt < six_months_ago:
                            include_in_history = False
                    except:
                        pass
                
                # Only add to rental history if within 6-month filter
                if include_in_history:
                    rental_entry = {
                        'id': f"TXN-{datetime.now().strftime('%Y%m%d%H%M%S')}-{len(rental_entries):04d}",
                        'customer_no': cust_no,
                        'cylinder_no': cyl_no,
                        'customer_name': customer.get('customer_name') or customer.get('name', ''),
                        'cylinder_custom_id': cylinder.get('custom_id', ''),
                        'dispatch_date': dispatch_date,
                        'return_date': return_date,
                        'status': 'returned' if return_date else 'active',
                        'created_at': datetime.now().isoformat()
                    }
                    rental_entries.append(rental_entry)
                    
                    # Group by customer for embedding in customer records
                    if customer['id'] not in customer_rentals:
                        customer_rentals[customer['id']] = []
                    customer_rentals[customer['id']].append(rental_entry)
                
                imported += 1
                
            except Exception:
                skipped += 1
        
        conn.close()
        
        # Update cylinders with ALL transaction data for active dispatches/available status
        if operations:
            print(f"📊 Updating {len(operations):,} cylinders with active dispatches...")
            all_cylinders = self.cylinder_model.get_all()
            cylinders_by_id = {c['id']: c for c in all_cylinders}
            
            cylinders_updated = []
            linked = 0
            
            for cyl_id, cust_id, customer, dispatch, return_dt in operations:
                if cyl_id in cylinders_by_id:
                    cylinder = cylinders_by_id[cyl_id]
                    
                    # Update cylinder with customer info
                    cylinder['rented_to'] = cust_id
                    cylinder['rental_date'] = dispatch
                    cylinder['date_borrowed'] = dispatch
                    cylinder['status'] = 'rented'
                    
                    # Add customer details
                    cylinder['customer_name'] = customer.get('customer_name') or customer.get('name', '')
                    cylinder['customer_phone'] = customer.get('customer_phone') or customer.get('phone', '')
                    cylinder['customer_address'] = customer.get('customer_address') or customer.get('address', '')
                    cylinder['customer_city'] = customer.get('customer_city', '')
                    cylinder['customer_state'] = customer.get('customer_state', '')
                    cylinder['location'] = customer.get('customer_address') or customer.get('address', 'Customer Location')
                    
                    # Handle returns
                    if return_dt:
                        cylinder['date_returned'] = return_dt
                        cylinder['status'] = 'available'
                        cylinder['location'] = 'Warehouse'
                        cylinder['rented_to'] = None
                        # Clear customer info on return
                        cylinder['customer_name'] = ''
                        cylinder['customer_phone'] = ''
                        cylinder['customer_address'] = ''
                        cylinder['customer_city'] = ''
                        cylinder['customer_state'] = ''
                    else:
                        cylinder['date_returned'] = ''
                    
                    cylinder['updated_at'] = datetime.now().isoformat()
                    cylinders_updated.append(cylinder)
                    linked += 1
            
            # Single bulk write to cylinders.json
            if cylinders_updated:
                updated_ids = {c['id'] for c in cylinders_updated}
                final_data = [c for c in all_cylinders if c['id'] not in updated_ids] + cylinders_updated
                self.cylinder_model.db.save_data(final_data)
                print(f"✅ Updated {len(cylinders_updated):,} cylinders")
        
        # Update customers with embedded rental history (6-month filter applied)
        if customer_rentals:
            print(f"📝 Updating {len(customer_rentals):,} customers with rental history...")
            all_customers = self.customer_model.get_all()
            customers_by_id = {c['id']: c for c in all_customers}
            
            customers_updated = []
            for cust_id, rentals in customer_rentals.items():
                if cust_id in customers_by_id:
                    customer = customers_by_id[cust_id]
                    customer['rental_history'] = rentals
                    customer['updated_at'] = datetime.now().isoformat()
                    customers_updated.append(customer)
            
            # Bulk write customers with rental history
            if customers_updated:
                updated_ids = {c['id'] for c in customers_updated}
                final_customers = [c for c in all_customers if c['id'] not in updated_ids] + customers_updated
                self.customer_model.db.save_data(final_customers)
                print(f"✅ Updated {len(customers_updated):,} customers with rental history")
        
        # Save rental history
        if rental_entries:
            print(f"📝 Saving {len(rental_entries):,} rental history records...")
            try:
                import json
                import os
                
                rental_file = 'data/rental_history.json'
                existing_data = []
                
                if os.path.exists(rental_file):
                    try:
                        with open(rental_file, 'r') as f:
                            existing_data = json.load(f)
                    except:
                        existing_data = []
                
                all_data = existing_data + rental_entries
                
                os.makedirs('data', exist_ok=True)
                with open(rental_file, 'w') as f:
                    json.dump(all_data, f, indent=2)
                
                print(f"✅ Saved rental history records")
                
            except Exception as e:
                print(f"❌ Rental history save failed: {e}")
        
        print(f"✅ INSTANT COMPLETE: {imported:,} imported | {linked if 'linked' in locals() else 0:,} linked | {skipped:,} skipped")
        return imported, skipped, []

if __name__ == "__main__":
    import sys
    if len(sys.argv) >= 4:
        importer = InstantImporter()
        mapping = json.loads(sys.argv[3])
        import_type = sys.argv[4] if len(sys.argv) > 4 else 'transaction'
        importer.instant_import(sys.argv[1], sys.argv[2], mapping, import_type)