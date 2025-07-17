#!/usr/bin/env python3
"""
Database migration script to add custom_id field to existing cylinders
Run this script to update existing cylinder records with the new custom_id field
"""

import json
import os
from datetime import datetime

def migrate_cylinders():
    """Add custom_id field to existing cylinder records"""
    
    # Ensure data directory exists
    data_dir = 'data'
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
    
    cylinders_file = os.path.join(data_dir, 'cylinders.json')
    
    # Load existing data
    if os.path.exists(cylinders_file):
        try:
            with open(cylinders_file, 'r') as f:
                cylinders = json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            cylinders = []
    else:
        cylinders = []
    
    # Check if migration is needed
    migration_needed = False
    updated_count = 0
    
    for i, cylinder in enumerate(cylinders):
        if 'custom_id' not in cylinder:
            cylinder['custom_id'] = ''  # Add empty custom_id field
            cylinder['updated_at'] = datetime.now().isoformat()
            cylinders[i] = cylinder
            migration_needed = True
            updated_count += 1
    
    if migration_needed:
        # Create backup first
        backup_file = f"{cylinders_file}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        if os.path.exists(cylinders_file):
            with open(backup_file, 'w') as f:
                json.dump(cylinders, f, indent=2)
            print(f"✓ Created backup: {backup_file}")
        
        # Save updated data
        with open(cylinders_file, 'w') as f:
            json.dump(cylinders, f, indent=2)
        
        print(f"✓ Migration completed: Updated {updated_count} cylinder records")
        print(f"✓ Added 'custom_id' field to all existing cylinders")
    else:
        print("✓ No migration needed - all cylinders already have 'custom_id' field")

if __name__ == '__main__':
    print("Varasai Oxygen - Cylinder Custom ID Migration")
    print("=" * 50)
    migrate_cylinders()
    print("=" * 50)
    print("Migration complete!")