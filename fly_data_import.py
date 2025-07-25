#!/usr/bin/env python3
"""
Fly.io Data Import Script
Run this locally to upload and import your JSON data to the deployed Fly.io app
"""

import os
import subprocess
import sys
import json
from pathlib import Path

def run_command(cmd, check=True):
    """Run a shell command and return the result"""
    print(f"Running: {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if check and result.returncode != 0:
        print(f"Error: {result.stderr}")
        sys.exit(1)
    return result

def upload_and_import_data(app_name):
    """Upload JSON data files and run migration on Fly.io"""
    
    print("🚀 Starting data import to Fly.io...")
    
    # Check if flyctl is available
    result = run_command("flyctl version", check=False)
    if result.returncode != 0:
        print("❌ flyctl not found. Please install it first:")
        print("   curl -L https://fly.io/install.sh | sh")
        sys.exit(1)
    
    # Check if data directory exists
    if not os.path.exists('data'):
        print("❌ No data directory found. Please ensure your JSON data files are in a 'data' directory.")
        sys.exit(1)
    
    # List available data files
    data_files = list(Path('data').glob('*.json'))
    if not data_files:
        print("❌ No JSON files found in data directory.")
        sys.exit(1)
    
    print(f"📁 Found {len(data_files)} data files:")
    for file in data_files:
        print(f"   - {file}")
    
    # Create a temporary migration script
    migration_script = '''
import os
import json
import sys
from datetime import datetime
import uuid

# Import your models (adjust import path as needed)
sys.path.append('/app')
from db_models import get_db_session, Customer, Cylinder, RentalHistory

def migrate_json_data():
    """Migrate data from JSON files to PostgreSQL"""
    db = get_db_session()
    
    # Migrate customers
    customers_file = '/tmp/customers.json'
    if os.path.exists(customers_file):
        print("📋 Migrating customers...")
        with open(customers_file, 'r') as f:
            customers_data = json.load(f)
        
        for customer_data in customers_data:
            # Check if customer already exists
            existing = db.query(Customer).filter(Customer.customer_no == customer_data.get('customer_no')).first()
            if not existing:
                customer = Customer(
                    id=customer_data.get('id', str(uuid.uuid4())),
                    customer_no=customer_data.get('customer_no', ''),
                    customer_name=customer_data.get('customer_name', customer_data.get('name', '')),
                    customer_email=customer_data.get('customer_email', customer_data.get('email', '')),
                    customer_phone=customer_data.get('customer_phone', customer_data.get('phone', '')),
                    customer_address=customer_data.get('customer_address', customer_data.get('address', '')),
                    customer_city=customer_data.get('customer_city', customer_data.get('city', '')),
                    customer_state=customer_data.get('customer_state', customer_data.get('state', '')),
                    customer_apgst=customer_data.get('customer_apgst', ''),
                    customer_cst=customer_data.get('customer_cst', ''),
                    created_at=datetime.utcnow()
                )
                db.add(customer)
        
        db.commit()
        print(f"✅ Migrated {len(customers_data)} customers")
    
    # Migrate cylinders
    cylinders_file = '/tmp/cylinders.json'
    if os.path.exists(cylinders_file):
        print("🛢️ Migrating cylinders...")
        with open(cylinders_file, 'r') as f:
            cylinders_data = json.load(f)
        
        for cylinder_data in cylinders_data:
            # Check if cylinder already exists
            existing = db.query(Cylinder).filter(Cylinder.custom_id == cylinder_data.get('custom_id')).first()
            if not existing:
                cylinder = Cylinder(
                    id=cylinder_data.get('id', str(uuid.uuid4())),
                    custom_id=cylinder_data.get('custom_id', ''),
                    serial_number=cylinder_data.get('serial_number', ''),
                    type=cylinder_data.get('type', 'Medical Oxygen'),
                    size=cylinder_data.get('size', '40L'),
                    status=cylinder_data.get('status', 'available'),
                    location=cylinder_data.get('location', 'Warehouse'),
                    rented_to=cylinder_data.get('rented_to'),
                    customer_name=cylinder_data.get('customer_name', ''),
                    customer_email=cylinder_data.get('customer_email', ''),
                    customer_phone=cylinder_data.get('customer_phone', ''),
                    customer_no=cylinder_data.get('customer_no', ''),
                    customer_city=cylinder_data.get('customer_city', ''),
                    customer_state=cylinder_data.get('customer_state', ''),
                    date_borrowed=datetime.fromisoformat(cylinder_data['date_borrowed'].replace('Z', '+00:00')) if cylinder_data.get('date_borrowed') else None,
                    rental_date=datetime.fromisoformat(cylinder_data['rental_date'].replace('Z', '+00:00')) if cylinder_data.get('rental_date') else None,
                    date_returned=datetime.fromisoformat(cylinder_data['date_returned'].replace('Z', '+00:00')) if cylinder_data.get('date_returned') else None,
                    created_at=datetime.utcnow()
                )
                db.add(cylinder)
        
        db.commit()
        print(f"✅ Migrated {len(cylinders_data)} cylinders")
    
    # Migrate rental history if exists
    rental_file = '/tmp/rental_history.json'
    if os.path.exists(rental_file):
        print("📚 Migrating rental history...")
        with open(rental_file, 'r') as f:
            rental_data = json.load(f)
        
        for record in rental_data:
            existing = db.query(RentalHistory).filter(
                RentalHistory.cylinder_id == record.get('cylinder_id'),
                RentalHistory.customer_id == record.get('customer_id')
            ).first()
            
            if not existing:
                history = RentalHistory(
                    id=str(uuid.uuid4()),
                    cylinder_id=record.get('cylinder_id'),
                    customer_id=record.get('customer_id'),
                    customer_name=record.get('customer_name', ''),
                    customer_no=record.get('customer_no', ''),
                    cylinder_custom_id=record.get('cylinder_custom_id', ''),
                    rental_date=datetime.fromisoformat(record['rental_date'].replace('Z', '+00:00')) if record.get('rental_date') else datetime.utcnow(),
                    return_date=datetime.fromisoformat(record['return_date'].replace('Z', '+00:00')) if record.get('return_date') else None,
                    created_at=datetime.utcnow()
                )
                db.add(history)
        
        db.commit()
        print(f"✅ Migrated {len(rental_data)} rental history records")
    
    db.close()
    print("🎉 Data migration completed successfully!")

if __name__ == "__main__":
    migrate_json_data()
'''
    
    # Save migration script locally
    with open('temp_migration.py', 'w') as f:
        f.write(migration_script)
    
    print("📤 Uploading data files to Fly.io...")
    
    # Upload each JSON file
    for data_file in data_files:
        cmd = f"flyctl ssh sftp shell --app {app_name}"
        print(f"Upload {data_file} manually using: flyctl ssh sftp --app {app_name}")
    
    # Alternative: Use flyctl ssh console to create files
    print("🔧 Creating migration script on server...")
    
    # Create a comprehensive upload and migrate command
    upload_commands = []
    
    for data_file in data_files:
        # Read the JSON file
        with open(data_file, 'r') as f:
            data_content = f.read().replace("'", "\\'").replace('"', '\\"')
        
        # Create upload command
        filename = data_file.name
        upload_commands.append(f'echo "{data_content}" > /tmp/{filename}')
    
    # Create complete migration command
    migration_command = f'''
cd /app && python3 -c "
{migration_script}
"
'''
    
    # Save commands to a script file
    with open('upload_and_migrate.sh', 'w') as f:
        f.write('#!/bin/bash\n')
        f.write('set -e\n\n')
        f.write('echo "📤 Uploading data files..."\n')
        for cmd in upload_commands:
            f.write(f'{cmd}\n')
        f.write('\necho "🔄 Running migration..."\n')
        f.write(migration_command)
        f.write('\necho "✅ Migration completed!"\n')
    
    print("📋 Migration script created: upload_and_migrate.sh")
    print(f"🚀 To complete the data import, run:")
    print(f"   flyctl ssh console --app {app_name}")
    print(f"   # Then copy and paste the contents of upload_and_migrate.sh")
    print("")
    print("Or manually upload files and run migration:")
    print(f"   flyctl ssh sftp --app {app_name}")
    print(f"   # Upload your JSON files to /tmp/")
    print(f"   flyctl ssh console --app {app_name}")
    print(f"   # Run: python3 temp_migration.py")

def main():
    """Main function"""
    if len(sys.argv) != 2:
        print("Usage: python3 fly_data_import.py <app-name>")
        print("Example: python3 fly_data_import.py my-oxygen-tracker")
        sys.exit(1)
    
    app_name = sys.argv[1]
    upload_and_import_data(app_name)

if __name__ == "__main__":
    main()