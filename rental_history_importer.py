#!/usr/bin/env python3
"""
Customer Rental History Importer
Imports transaction data and stores rental history directly in customer records
"""

import json
import pyodbc
from datetime import datetime, timedelta
from models import Customer, Cylinder

class RentalHistoryImporter:
    def __init__(self):
        self.customer_model = Customer()
        self.cylinder_model = Cylinder()
    
    def import_rental_history(self, access_file: str, table_name: str, field_mapping: dict) -> tuple:
        """Import rental history from Access database and store in customer records"""
        print("🚀 RENTAL HISTORY IMPORT: 6-month filter for customer display")
        
        # Connect to Access database
        conn = pyodbc.connect(f'DRIVER={{Microsoft Access Driver (*.mdb, *.accdb)}};DBQ={access_file};')
        cursor = conn.cursor()
        
        # Get all transaction data
        cursor.execute(f"SELECT * FROM [{table_name}]")
        rows = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        
        print(f"Processing {len(rows):,} transaction records...")
        
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
        
        # 6-month cutoff for display
        six_months_ago = datetime.now() - timedelta(days=180)
        
        # Process transactions and group by customer
        customer_histories = {}
        processed = 0
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
                
                # Apply 6-month filter - only include recent activity
                include_record = False
                
                # Check if dispatch is within 6 months
                if dispatch_date:
                    try:
                        dispatch_dt = datetime.strptime(dispatch_date, '%Y-%m-%d')
                        if dispatch_dt >= six_months_ago:
                            include_record = True
                    except:
                        pass
                
                # Check if return is within 6 months
                if return_date and not include_record:
                    try:
                        return_dt = datetime.strptime(return_date, '%Y-%m-%d')
                        if return_dt >= six_months_ago:
                            include_record = True
                    except:
                        pass
                
                # Only include records with recent activity
                if include_record:
                    customer_id = customer['id']
                    
                    if customer_id not in customer_histories:
                        customer_histories[customer_id] = []
                    
                    # Calculate rental duration
                    rental_days = 0
                    if dispatch_date and return_date:
                        try:
                            dispatch_dt = datetime.strptime(dispatch_date, '%Y-%m-%d')
                            return_dt = datetime.strptime(return_date, '%Y-%m-%d')
                            rental_days = max(0, (return_dt - dispatch_dt).days)
                        except:
                            pass
                    
                    # Create rental history entry
                    history_entry = {
                        'id': f"RH-{datetime.now().strftime('%Y%m%d%H%M%S')}-{len(customer_histories[customer_id]):04d}",
                        'cylinder_id': cylinder.get('id', ''),
                        'cylinder_custom_id': cylinder.get('custom_id', ''),
                        'cylinder_serial': cylinder.get('serial_number', ''),
                        'cylinder_type': cylinder.get('type', ''),
                        'cylinder_size': cylinder.get('size', ''),
                        'dispatch_date': dispatch_date,
                        'return_date': return_date,
                        'rental_days': rental_days,
                        'status': 'returned' if return_date else 'active',
                        'created_at': datetime.now().isoformat()
                    }
                    
                    customer_histories[customer_id].append(history_entry)
                    processed += 1
                else:
                    skipped += 1
                
            except Exception:
                skipped += 1
        
        conn.close()
        
        # Update customers with rental history
        if customer_histories:
            print(f"📝 Updating {len(customer_histories):,} customers with rental history...")
            
            all_customers = self.customer_model.get_all()
            customers_by_id = {c['id']: c for c in all_customers}
            
            customers_updated = []
            
            for customer_id, history in customer_histories.items():
                if customer_id in customers_by_id:
                    customer = customers_by_id[customer_id]
                    
                    # Sort history by dispatch date (newest first)
                    history.sort(key=lambda x: x.get('dispatch_date', ''), reverse=True)
                    
                    # Store rental history in customer record
                    customer['rental_history'] = history
                    customer['rental_history_count'] = len(history)
                    customer['last_rental_update'] = datetime.now().isoformat()
                    customer['updated_at'] = datetime.now().isoformat()
                    
                    customers_updated.append(customer)
            
            # Bulk update customers
            if customers_updated:
                updated_ids = {c['id'] for c in customers_updated}
                final_customers = [c for c in all_customers if c['id'] not in updated_ids] + customers_updated
                self.customer_model.db.save_data(final_customers)
                print(f"✅ Updated {len(customers_updated):,} customers with rental history")
        
        print(f"✅ RENTAL HISTORY COMPLETE: {processed:,} records processed | {skipped:,} skipped")
        return processed, skipped, []

if __name__ == "__main__":
    import sys
    if len(sys.argv) >= 4:
        importer = RentalHistoryImporter()
        mapping = json.loads(sys.argv[3])
        importer.import_rental_history(sys.argv[1], sys.argv[2], mapping)