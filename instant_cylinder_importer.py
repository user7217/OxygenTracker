#!/usr/bin/env python3
"""
Instant Cylinder Importer - Ultra-fast cylinder data import system
Direct cylinder imports with zero overhead processing
"""

import json
import pyodbc
from datetime import datetime
from models import CylinderModel

class InstantCylinderImporter:
    def __init__(self):
        self.cylinder_model = CylinderModel()
    
    def instant_cylinder_import(self, access_file: str, table_name: str, field_mapping: dict) -> tuple:
        """Import cylinders with zero processing overhead"""
        print("🚀 INSTANT CYLINDER MODE: Direct memory operations")
        
        # Direct connection without wrapper overhead
        conn = pyodbc.connect(f'DRIVER={{Microsoft Access Driver (*.mdb, *.accdb)}};DBQ={access_file};')
        cursor = conn.cursor()
        
        # Get all data in one shot
        cursor.execute(f"SELECT * FROM [{table_name}]")
        rows = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        
        print(f"Loaded {len(rows):,} cylinder rows - processing instantly...")
        
        # Build field mapping indices
        field_indices = {}
        for target_field, source_field in field_mapping.items():
            if source_field and source_field in columns:
                field_indices[target_field] = columns.index(source_field)
        
        # Process all rows with minimal overhead
        cylinders_to_add = []
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
                            if target_field == 'custom_id':
                                cylinder_data['custom_id'] = value
                            elif target_field == 'serial_number':
                                cylinder_data['serial_number'] = value
                            elif target_field == 'type':
                                cylinder_data['type'] = value
                            elif target_field == 'size':
                                cylinder_data['size'] = value
                            elif target_field == 'location':
                                cylinder_data['location'] = value
                            elif target_field == 'pressure':
                                cylinder_data['pressure'] = value
                            elif target_field == 'notes':
                                cylinder_data['notes'] = value
                
                # Validate required fields - custom_id is required
                if not cylinder_data.get('custom_id'):
                    skipped += 1
                    continue
                
                # Check for duplicates by custom_id
                existing_cylinders = self.cylinder_model.get_all()
                duplicate_found = False
                for existing in existing_cylinders:
                    if existing.get('custom_id') == cylinder_data['custom_id']:
                        duplicate_found = True
                        break
                
                if duplicate_found:
                    skipped += 1
                    continue
                
                cylinders_to_add.append(cylinder_data)
                imported += 1
                
            except Exception as e:
                skipped += 1
                print(f"Error processing cylinder row: {e}")
        
        conn.close()
        
        # Bulk add all cylinders
        print(f"Adding {len(cylinders_to_add):,} cylinders to database...")
        for cylinder_data in cylinders_to_add:
            try:
                self.cylinder_model.add(cylinder_data)
            except Exception as e:
                print(f"Error adding cylinder {cylinder_data.get('custom_id', 'Unknown')}: {e}")
                imported -= 1
                skipped += 1
        
        print(f"✅ INSTANT CYLINDER COMPLETE: {imported:,} imported | {skipped:,} skipped")
        return imported, skipped, []

if __name__ == "__main__":
    import sys
    if len(sys.argv) >= 4:
        importer = InstantCylinderImporter()
        mapping = json.loads(sys.argv[3])
        importer.instant_cylinder_import(sys.argv[1], sys.argv[2], mapping)