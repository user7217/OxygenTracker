#!/usr/bin/env python3
"""
Fix JSON File References in routes.py
Removes all references to data/customers.json and updates with PostgreSQL queries
"""

import re

def fix_routes_file():
    """Fix all JSON file references in routes.py"""
    
    # Read the current routes.py file
    with open('routes.py', 'r') as f:
        content = f.read()
    
    # Define the replacement patterns
    replacements = [
        # Pattern 1: Days calculation in dashboard
        {
            'old': '''    # Days since first customer/cylinder
    from datetime import datetime
    import json
    import os
    
    days_active = 1
    try:
        if os.path.exists('data/customers.json'):
            with open('data/customers.json', 'r') as f:
                customer_data = json.load(f)
                if customer_data:
                    oldest_date = min([c.get('created_at', datetime.now().isoformat()) for c in customer_data])
                    if oldest_date:
                        from datetime import datetime
                        oldest = datetime.fromisoformat(oldest_date.replace('Z', '+00:00').split('.')[0])
                        days_active = (datetime.now() - oldest).days + 1
    except:
        pass''',
            'new': '''    # Days since first customer/cylinder - get from PostgreSQL
    from datetime import datetime
    
    days_active = 1
    try:
        with CustomerService() as customer_service:
            # Get the oldest customer creation date from database
            oldest_customer = customer_service.db.execute(
                text("SELECT MIN(created_at) FROM customers WHERE created_at IS NOT NULL")
            ).scalar()
            
            if oldest_customer:
                days_active = (datetime.now().date() - oldest_customer.date()).days + 1
    except:
        # Fallback to 1 day if no data available
        days_active = 1'''
        },
        
        # Pattern 2: Days calculation in metrics
        {
            'old': '''    # Days since first customer/cylinder
    from datetime import datetime
    import json
    import os
    
    days_active = 1
    try:
        if os.path.exists('data/customers.json'):
            with open('data/customers.json', 'r') as f:
                customer_data = json.load(f)
                if customer_data:
                    oldest_date = min([c.get('created_at', datetime.now().isoformat()) for c in customer_data])
                    if oldest_date:
                        from datetime import datetime
                        oldest = datetime.fromisoformat(oldest_date.replace('Z', '+00:00').split('.')[0])
                        days_active = (datetime.now() - oldest).days + 1
    except:
        pass''',
            'new': '''    # Days since first customer/cylinder - get from PostgreSQL
    from datetime import datetime
    
    days_active = 1
    try:
        with CustomerService() as customer_service:
            # Get the oldest customer creation date from database
            oldest_customer = customer_service.db.execute(
                text("SELECT MIN(created_at) FROM customers WHERE created_at IS NOT NULL")
            ).scalar()
            
            if oldest_customer:
                days_active = (datetime.now().date() - oldest_customer.date()).days + 1
    except:
        # Fallback to 1 day if no data available
        days_active = 1'''
        },
        
        # Pattern 3: Days calculation in send_admin_stats
        {
            'old': '''    # Days since first customer/cylinder
    from datetime import datetime
    import json
    
    days_active = 1
    try:
        if os.path.exists('data/customers.json'):
            with open('data/customers.json', 'r') as f:
                customer_data = json.load(f)
                if customer_data:
                    oldest_date = min([c.get('created_at', datetime.now().isoformat()) for c in customer_data])
                    if oldest_date:
                        oldest = datetime.fromisoformat(oldest_date.replace('Z', '+00:00').split('.')[0])
                        days_active = (datetime.now() - oldest).days + 1
    except:
        pass''',
            'new': '''    # Days since first customer/cylinder - get from PostgreSQL
    from datetime import datetime
    
    days_active = 1
    try:
        with CustomerService() as customer_service:
            # Get the oldest customer creation date from database
            oldest_customer = customer_service.db.execute(
                text("SELECT MIN(created_at) FROM customers WHERE created_at IS NOT NULL")
            ).scalar()
            
            if oldest_customer:
                days_active = (datetime.now().date() - oldest_customer.date()).days + 1
    except:
        # Fallback to 1 day if no data available
        days_active = 1'''
        }
    ]
    
    # Apply replacements
    for replacement in replacements:
        content = content.replace(replacement['old'], replacement['new'])
    
    # Remove any remaining JSON import if not needed
    if 'import json' in content and 'json.load' not in content and 'json.dumps' not in content:
        content = re.sub(r'\n\s*import json\n', '\n', content)
    
    # Also fix any customer_model references that might still exist
    content = content.replace('customers = customer_model.get_all()', 
                              '''with CustomerService() as customer_service:
        customers, _ = customer_service.get_all(page=1, per_page=10000)''')
    
    # Write the updated file
    with open('routes.py', 'w') as f:
        f.write(content)
    
    print("✓ Fixed all JSON file references in routes.py")
    print("✓ Updated with PostgreSQL database queries")

def check_other_files():
    """Check other files for SQLite references"""
    import os
    import glob
    
    python_files = glob.glob("*.py")
    sqlite_files = []
    
    for file_path in python_files:
        if 'backup' in file_path or 'legacy' in file_path or 'cleanup' in file_path:
            continue
            
        try:
            with open(file_path, 'r') as f:
                content = f.read()
                if 'sqlite' in content.lower() or 'data/customers.json' in content or 'data/cylinders.json' in content:
                    sqlite_files.append(file_path)
        except:
            pass
    
    if sqlite_files:
        print(f"⚠ Found SQLite references in: {', '.join(sqlite_files)}")
    else:
        print("✓ No more SQLite references found in Python files")

if __name__ == "__main__":
    print("🔧 Fixing JSON file references...")
    fix_routes_file()
    check_other_files()
    print("✅ JSON reference cleanup complete!")