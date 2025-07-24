#!/usr/bin/env python3
"""
INSTANT Transaction Importer
Zero overhead, direct memory operations
"""

import json
import pyodbc
from datetime import datetime, timedelta
from models import CustomerModel, CylinderModel
from models_rental_history import RentalHistory

class InstantImporter:
    def __init__(self):
        self.customer_model = CustomerModel()
        self.cylinder_model = CylinderModel()
        self.rental_history = RentalHistory()
    
    def instant_import(self, access_file: str, table_name: str, field_mapping: dict) -> tuple:
        """Import transactions with zero processing overhead"""
        print("🚀 INSTANT MODE: Direct memory operations")
        
        # Direct connection without wrapper overhead
        conn = pyodbc.connect(f'DRIVER={{Microsoft Access Driver (*.mdb, *.accdb)}};DBQ={access_file};')
        cursor = conn.cursor()
        
        # Get all data in one shot - no batching, no streaming
        cursor.execute(f"SELECT * FROM [{table_name}]")
        rows = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        
        print(f"Loaded {len(rows):,} rows - processing instantly...")
        
        # Pre-load ALL data structures
        customers_raw = self.customer_model.get_all()
        cylinders_raw = self.cylinder_model.get_all()
        
        # Build ultra-fast lookup tables
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
        
        # Pre-calculate ALL column indices
        try:
            cust_idx = columns.index(field_mapping['customer_no'])
            cyl_idx = columns.index(field_mapping['cylinder_no'])
            dispatch_idx = columns.index(field_mapping['dispatch_date']) if 'dispatch_date' in field_mapping else None
            return_idx = columns.index(field_mapping['return_date']) if 'return_date' in field_mapping else None
        except (ValueError, KeyError):
            conn.close()
            return 0, 0, ["Required field mapping not found"]
        
        # Import with 6-month cutoff for completed rentals
        six_months_ago = datetime.now() - timedelta(days=180)
        
        # Process ALL rows with minimal overhead
        operations = []
        imported = 0
        skipped = 0
        
        for row in rows:
            # Direct array access - no dictionaries
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
            
            # Fast date processing
            if dispatch_idx is not None:
                dispatch_raw = row[dispatch_idx]
                if dispatch_raw:
                    try:
                        if isinstance(dispatch_raw, str):
                            # Parse only what we need
                            if len(dispatch_raw) >= 10:
                                date_part = dispatch_raw[:10]
                                dispatch_dt = datetime.strptime(date_part, '%Y-%m-%d')
                            else:
                                skipped += 1
                                continue
                        else:
                            dispatch_dt = dispatch_raw
                        
                        dispatch_date = dispatch_dt.strftime('%Y-%m-%d')
                        
                        # Return date (optional)
                        return_date = None
                        if return_idx is not None and row[return_idx]:
                            try:
                                return_raw = row[return_idx]
                                if isinstance(return_raw, str) and len(return_raw) >= 10:
                                    return_dt = datetime.strptime(return_raw[:10], '%Y-%m-%d')
                                    return_date = return_dt.strftime('%Y-%m-%d')
                                elif not isinstance(return_raw, str):
                                    return_date = return_raw.strftime('%Y-%m-%d')
                                
                                # Skip if return date is older than 6 months
                                if return_date:
                                    return_dt_check = datetime.strptime(return_date, '%Y-%m-%d')
                                    if return_dt_check < six_months_ago:
                                        skipped += 1
                                        continue
                            except:
                                pass
                        
                        # Queue operation
                        operations.append((cylinder['id'], customer['id'], customer, dispatch_date, return_date))
                        imported += 1
                        
                    except:
                        skipped += 1
                else:
                    skipped += 1
            else:
                skipped += 1
        
        conn.close()
        
        # Execute ALL operations without any overhead
        print(f"Executing {len(operations):,} operations...")
        linked = 0
        
        for cyl_id, cust_id, customer, dispatch, return_dt in operations:
            try:
                self.cylinder_model.rent_cylinder_with_location(cyl_id, cust_id, dispatch, customer)
                if return_dt:
                    self.cylinder_model.return_cylinder(cyl_id, return_dt)
                linked += 1
            except:
                pass
        
        print(f"✅ INSTANT COMPLETE: {imported:,} imported | {linked:,} linked | {skipped:,} skipped")
        return imported, skipped, []

if __name__ == "__main__":
    import sys
    if len(sys.argv) >= 4:
        importer = InstantImporter()
        mapping = json.loads(sys.argv[3])
        importer.instant_import(sys.argv[1], sys.argv[2], mapping)