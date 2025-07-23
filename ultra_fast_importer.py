#!/usr/bin/env python3
"""
Ultra-Fast Transaction Importer
Optimized for instant processing of large datasets
"""

import os
import sys
import json
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
from models import CustomerModel, CylinderModel
from access_connector import AccessConnector

class UltraFastImporter:
    def __init__(self):
        self.customer_model = CustomerModel()
        self.cylinder_model = CylinderModel()
        self.access_connector = None
    
    def connect_to_access(self, file_path: str) -> bool:
        """Connect to Access database"""
        try:
            self.access_connector = AccessConnector(file_path)
            return True
        except:
            return False
    
    def ultra_fast_import(self, table_name: str, field_mapping: Dict[str, str]) -> Tuple[int, int, List[str]]:
        """Ultra-fast transaction import - processes entire dataset instantly"""
        print("🚀 ULTRA-FAST IMPORT MODE ACTIVATED")
        print("Loading everything into memory for maximum speed...")
        
        # Load all data structures into memory
        cursor = self.access_connector.connection.cursor()
        cursor.execute(f"SELECT * FROM [{table_name}]")
        all_data = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        
        # Pre-load all customers and cylinders
        customers = {c.get('customer_no', '').upper(): c for c in self.customer_model.get_all()}
        cylinders = {}
        for cyl in self.cylinder_model.get_all():
            if cyl.get('serial_number'):
                cylinders[cyl['serial_number'].upper()] = cyl
            if cyl.get('custom_id'):
                cylinders[cyl['custom_id'].upper()] = cyl
        
        # Date threshold
        one_year_ago = datetime.now() - timedelta(days=365)
        
        # Pre-calculate column positions
        col_map = {}
        for target, source in field_mapping.items():
            try:
                col_map[target] = columns.index(source)
            except ValueError:
                continue
        
        print(f"Processing {len(all_data):,} rows at lightning speed...")
        
        # Ultra-fast bulk processing
        operations = []
        imported = 0
        skipped = 0
        
        for row in all_data:
            # Extract data using pre-calculated indices
            try:
                cust_no = str(row[col_map['customer_no']]).strip().upper() if 'customer_no' in col_map else ''
                cyl_no = str(row[col_map['cylinder_no']]).strip().upper() if 'cylinder_no' in col_map else ''
                
                if not cust_no or not cyl_no:
                    skipped += 1
                    continue
                
                customer = customers.get(cust_no)
                cylinder = cylinders.get(cyl_no)
                
                if not customer or not cylinder:
                    skipped += 1
                    continue
                
                # Fast date processing
                if 'dispatch_date' in col_map:
                    dispatch_raw = row[col_map['dispatch_date']]
                    if dispatch_raw:
                        try:
                            if isinstance(dispatch_raw, str):
                                dispatch_dt = datetime.strptime(dispatch_raw[:19], '%Y-%m-%d %H:%M:%S')
                            else:
                                dispatch_dt = dispatch_raw
                            
                            if dispatch_dt >= one_year_ago:
                                dispatch_date = dispatch_dt.strftime('%Y-%m-%d')
                                
                                # Process return date if exists
                                return_date = None
                                if 'return_date' in col_map and row[col_map['return_date']]:
                                    try:
                                        return_raw = row[col_map['return_date']]
                                        if isinstance(return_raw, str):
                                            return_dt = datetime.strptime(return_raw[:19], '%Y-%m-%d %H:%M:%S')
                                        else:
                                            return_dt = return_raw
                                        return_date = return_dt.strftime('%Y-%m-%d')
                                    except:
                                        pass
                                
                                operations.append({
                                    'cyl_id': cylinder['id'],
                                    'cust_id': customer['id'],
                                    'customer': customer,
                                    'dispatch': dispatch_date,
                                    'return': return_date
                                })
                                imported += 1
                            else:
                                skipped += 1
                        except:
                            skipped += 1
                    else:
                        skipped += 1
                else:
                    skipped += 1
            except:
                skipped += 1
        
        print(f"⚡ Executing {len(operations):,} operations instantly...")
        
        # Execute all operations
        linked = 0
        for op in operations:
            try:
                self.cylinder_model.rent_cylinder_with_location(
                    op['cyl_id'], op['cust_id'], op['dispatch'], op['customer']
                )
                if op['return']:
                    self.cylinder_model.return_cylinder(op['cyl_id'], op['return'])
                linked += 1
            except:
                pass
        
        print(f"✅ COMPLETE! Imported: {imported:,} | Linked: {linked:,} | Skipped: {skipped:,}")
        return imported, skipped, []

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: python ultra_fast_importer.py <access_file> <table_name> <mapping_json>")
        sys.exit(1)
    
    access_file = sys.argv[1]
    table_name = sys.argv[2]
    mapping_json = sys.argv[3]
    
    # Load field mapping
    mapping = json.loads(mapping_json)
    
    # Run ultra-fast import
    importer = UltraFastImporter()
    if importer.connect_to_access(access_file):
        importer.ultra_fast_import(table_name, mapping)
    else:
        print("Failed to connect to Access database")