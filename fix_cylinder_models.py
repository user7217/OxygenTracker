#!/usr/bin/env python3
"""
Quick script to fix all cylinder_model references in routes.py
"""

import re

def fix_cylinder_model_references():
    """Replace all cylinder_model references with PostgreSQL service calls"""
    
    with open('routes.py', 'r') as f:
        content = f.read()
    
    # Dictionary of replacements
    replacements = {
        # Simple get_all calls
        r'cylinders = cylinder_model\.get_all\(\)': 
        r'with CylinderService() as cylinder_service:\n        cylinders, _ = cylinder_service.get_all(page=1, per_page=1000)',
        
        # get_by_id calls
        r'cylinder = cylinder_model\.get_by_id\(([^)]+)\)':
        r'with CylinderService() as cylinder_service:\n        cylinder = cylinder_service.get_by_id(\1)',
        
        # get_display_id calls
        r"cylinder\['display_serial'\] = cylinder_model\.get_display_id\(cylinder\)":
        r"cylinder['display_serial'] = cylinder.get('custom_id') or cylinder.get('serial_number') or f\"ID-{cylinder['id'][:8]}\"",
        
        # get_rental_days calls  
        r"cylinder\['rental_days'\] = cylinder_model\.get_rental_days\(cylinder\)":
        r"cylinder['rental_days'] = (datetime.utcnow() - datetime.fromisoformat(cylinder['date_borrowed'])).days if cylinder.get('date_borrowed') else 0",
        
        # add and update calls
        r'cylinder_model\.add\(([^)]+)\)':
        r'cylinder_service.create(\1)',
        
        r'cylinder_model\.update\(([^,]+),\s*([^)]+)\)':
        r'cylinder_service.update(\1, \2)',
        
        # Wrap single-line calls in with statements
        r'existing_cylinders, _ = cylinder_model\.get_all\(\)':
        r'with CylinderService() as cylinder_service:\n            existing_cylinders, _ = cylinder_service.get_all(page=1, per_page=1000)',
        
        r'new_cylinder = cylinder_model\.add\(([^)]+)\)':
        r'with CylinderService() as cylinder_service:\n                new_cylinder = cylinder_service.create(\1)',
        
        r'updated_cylinder = cylinder_model\.update\(([^,]+),\s*([^)]+)\)':
        r'with CylinderService() as cylinder_service:\n                updated_cylinder = cylinder_service.update(\1, \2)',
    }
    
    # Apply replacements
    for pattern, replacement in replacements.items():
        content = re.sub(pattern, replacement, content)
    
    # Write back the file
    with open('routes.py', 'w') as f:
        f.write(content)
    
    print("Fixed cylinder_model references in routes.py")

if __name__ == '__main__':
    fix_cylinder_model_references()