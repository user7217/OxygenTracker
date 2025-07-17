"""
Database migration script to update existing customer records to new structure
Converts old customer format to new Access-compatible format
Run this script to update existing customer records with the new field structure
"""

import json
import os
import uuid
from datetime import datetime
from models import Customer

def migrate_customers():
    """
    Migrate existing customer records to new structure
    Old structure: name, email, phone, address, company, notes
    New structure: customer_no, customer_name, customer_address, customer_city, customer_state, customer_phone, customer_apgst, customer_cst
    """
    
    customer_model = Customer()
    data_file = customer_model.db.filepath
    
    print(f"Starting customer migration...")
    print(f"Data file: {data_file}")
    
    if not os.path.exists(data_file):
        print("No existing customer data found. Migration not needed.")
        return
    
    backup_file = f"{data_file}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    try:
        with open(data_file, 'r') as original:
            with open(backup_file, 'w') as backup:
                backup.write(original.read())
        print(f"Backup created: {backup_file}")
    except Exception as e:
        print(f"Error creating backup: {e}")
        return
    
    try:
        with open(data_file, 'r') as f:
            customers = json.load(f)
    except Exception as e:
        print(f"Error loading customer data: {e}")
        return
    
    if not customers:
        print("No customers to migrate.")
        return
    
    print(f"Found {len(customers)} customers to migrate.")
    
    migrated_customers = []
    migration_count = 0
    
    for i, customer in enumerate(customers):
        try:
            if 'customer_no' in customer:
                print(f"Customer {i+1}: Already migrated, skipping.")
                migrated_customers.append(customer)
                continue
            
            new_customer = {}
            
            new_customer['customer_no'] = f"CUST-{str(uuid.uuid4())[:8].upper()}"
            
            new_customer['customer_name'] = customer.get('name', 'Unknown Customer')
            
            old_address = customer.get('address', '')
            if old_address:
                address_parts = old_address.split(',')
                if len(address_parts) >= 3:
                    new_customer['customer_address'] = address_parts[0].strip()
                    new_customer['customer_city'] = address_parts[1].strip()
                    new_customer['customer_state'] = address_parts[2].strip()
                elif len(address_parts) == 2:
                    new_customer['customer_address'] = address_parts[0].strip()
                    new_customer['customer_city'] = address_parts[1].strip()
                    new_customer['customer_state'] = ''
                else:
                    new_customer['customer_address'] = old_address
                    new_customer['customer_city'] = ''
                    new_customer['customer_state'] = ''
            else:
                new_customer['customer_address'] = ''
                new_customer['customer_city'] = ''
                new_customer['customer_state'] = ''
            
            new_customer['customer_phone'] = customer.get('phone', '')
            
            new_customer['customer_apgst'] = ''
            new_customer['customer_cst'] = ''
            
            new_customer['id'] = customer.get('id', f"CUS-{str(uuid.uuid4())[:8].upper()}")
            new_customer['created_at'] = customer.get('created_at', datetime.now().isoformat())
            new_customer['updated_at'] = datetime.now().isoformat()
            
            legacy_notes = []
            if customer.get('email'):
                legacy_notes.append(f"Email: {customer['email']}")
            if customer.get('company'):
                legacy_notes.append(f"Company: {customer['company']}")
            if customer.get('notes'):
                legacy_notes.append(f"Notes: {customer['notes']}")
            
            if legacy_notes:
                new_customer['migration_notes'] = " | ".join(legacy_notes)
            
            migrated_customers.append(new_customer)
            migration_count += 1
            
            print(f"Customer {i+1}: Migrated '{customer.get('name', 'Unknown')}' -> '{new_customer['customer_name']}'")
            
        except Exception as e:
            print(f"Error migrating customer {i+1}: {e}")
            migrated_customers.append(customer)
    
    try:
        with open(data_file, 'w') as f:
            json.dump(migrated_customers, f, indent=2)
        
        print(f"\nMigration completed successfully!")
        print(f"- Total customers: {len(customers)}")
        print(f"- Migrated: {migration_count}")
        print(f"- Already migrated: {len(customers) - migration_count}")
        print(f"- Backup saved: {backup_file}")
        
        if migrated_customers:
            print(f"\nSample migrated customer:")
            sample = migrated_customers[0]
            print(f"  Customer No: {sample.get('customer_no', 'N/A')}")
            print(f"  Name: {sample.get('customer_name', 'N/A')}")
            print(f"  Address: {sample.get('customer_address', 'N/A')}")
            print(f"  City: {sample.get('customer_city', 'N/A')}")
            print(f"  State: {sample.get('customer_state', 'N/A')}")
            print(f"  Phone: {sample.get('customer_phone', 'N/A')}")
            
    except Exception as e:
        print(f"Error saving migrated data: {e}")
        print("Restoring from backup...")
        try:
            with open(backup_file, 'r') as backup:
                with open(data_file, 'w') as original:
                    original.write(backup.read())
            print("Data restored from backup.")
        except Exception as restore_error:
            print(f"Error restoring backup: {restore_error}")

def verify_migration():
    """Verify the migration was successful"""
    customer_model = Customer()
    customers = customer_model.get_all()
    
    print(f"\nVerification:")
    print(f"Total customers in database: {len(customers)}")
    
    new_format_count = 0
    old_format_count = 0
    
    for customer in customers:
        if 'customer_no' in customer:
            new_format_count += 1
        else:
            old_format_count += 1
    
    print(f"New format customers: {new_format_count}")
    print(f"Old format customers: {old_format_count}")
    
    if old_format_count > 0:
        print("Warning: Some customers still in old format!")
    else:
        print("✓ All customers successfully migrated to new format.")

if __name__ == "__main__":
    print("=" * 60)
    print("CUSTOMER DATA MIGRATION SCRIPT")
    print("=" * 60)
    print("This script will convert existing customer data to the new structure.")
    print("A backup will be created before making any changes.")
    print()
    
    response = input("Do you want to proceed with the migration? (yes/no): ").lower().strip()
    
    if response in ['yes', 'y']:
        migrate_customers()
        verify_migration()
        print("\nMigration process completed.")
    else:
        print("Migration cancelled.")