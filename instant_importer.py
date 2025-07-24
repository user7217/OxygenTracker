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
        """Import rental transactions ONLY - no cylinder creation, just rental history"""
        print("🚀 TRANSACTION MODE: Importing rental records only (6-month cutoff)")
        
        # Pre-calculate column indices
        try:
            cust_idx = columns.index(field_mapping['customer_no'])
            cyl_idx = columns.index(field_mapping['cylinder_no'])
            dispatch_idx = columns.index(field_mapping['dispatch_date']) if 'dispatch_date' in field_mapping else None
            return_idx = columns.index(field_mapping['return_date']) if 'return_date' in field_mapping else None
        except (ValueError, KeyError):
            conn.close()
            return 0, 0, ["Required field mapping not found"]
        
        # 6-month cutoff for old rentals
        six_months_ago = datetime.now() - timedelta(days=180)
        
        # Process rows and create rental history entries
        rental_entries = []
        imported = 0
        skipped = 0
        
        for row in rows:
            try:
                # Extract basic data
                cust_no = str(row[cust_idx] or '').strip()
                cyl_no = str(row[cyl_idx] or '').strip()
                
                if not cust_no or not cyl_no:
                    skipped += 1
                    continue
                
                # Process dispatch date
                dispatch_date = None
                if dispatch_idx is not None and row[dispatch_idx]:
                    try:
                        dispatch_raw = row[dispatch_idx]
                        if isinstance(dispatch_raw, str) and len(dispatch_raw) >= 10:
                            dispatch_date = dispatch_raw[:10]  # YYYY-MM-DD
                        elif hasattr(dispatch_raw, 'strftime'):
                            dispatch_date = dispatch_raw.strftime('%Y-%m-%d')
                    except:
                        pass
                
                # Process return date (optional)
                return_date = None
                if return_idx is not None and row[return_idx]:
                    try:
                        return_raw = row[return_idx]
                        if isinstance(return_raw, str) and len(return_raw) >= 10:
                            return_date = return_raw[:10]  # YYYY-MM-DD
                        elif hasattr(return_raw, 'strftime'):
                            return_date = return_raw.strftime('%Y-%m-%d')
                        
                        # Skip if return date is older than 6 months
                        if return_date:
                            return_dt = datetime.strptime(return_date, '%Y-%m-%d')
                            if return_dt < six_months_ago:
                                skipped += 1
                                continue
                    except:
                        pass
                
                if not dispatch_date:
                    skipped += 1
                    continue
                
                # Create rental history entry
                rental_entry = {
                    'id': f"RENT-{datetime.now().strftime('%Y%m%d%H%M%S')}-{len(rental_entries):04d}",
                    'customer_no': cust_no,
                    'cylinder_no': cyl_no,
                    'dispatch_date': dispatch_date,
                    'return_date': return_date or '',
                    'status': 'returned' if return_date else 'active',
                    'created_at': datetime.now().isoformat()
                }
                
                rental_entries.append(rental_entry)
                imported += 1
                
            except Exception:
                skipped += 1
        
        conn.close()
        
        # Save rental history in bulk
        if rental_entries:
            print(f"Saving {len(rental_entries):,} rental history records...")
            try:
                existing_history = self.rental_history._load_data()
                final_history = existing_history + rental_entries
                self.rental_history._save_data(final_history)
            except Exception as e:
                print(f"Rental history save failed: {e}")
        
        print(f"✅ INSTANT TRANSACTION COMPLETE: {imported:,} rental records imported | {skipped:,} skipped")
        return imported, skipped, []

if __name__ == "__main__":
    import sys
    if len(sys.argv) >= 4:
        importer = InstantImporter()
        mapping = json.loads(sys.argv[3])
        import_type = sys.argv[4] if len(sys.argv) > 4 else 'transaction'
        importer.instant_import(sys.argv[1], sys.argv[2], mapping, import_type)