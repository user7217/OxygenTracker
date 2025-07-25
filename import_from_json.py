#!/usr/bin/env python3
"""
JSON to PostgreSQL Import Utility
Imports existing JSON data files into PostgreSQL database
"""
import os
import json
import sys
from datetime import datetime
from pathlib import Path

# Set up environment for database connection
os.environ.setdefault('DATABASE_URL', 'postgresql://postgres:password@localhost:5432/oxygen_tracker')
os.environ.setdefault('SESSION_SECRET', 'dev-secret-key')

def load_json_file(file_path):
    """Load data from JSON file"""
    try:
        if not Path(file_path).exists():
            print(f"File not found: {file_path}")
            return None
            
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            print(f"Loaded {len(data)} records from {file_path}")
            return data
    except Exception as e:
        print(f"Error loading {file_path}: {e}")
        return None

def import_customers(json_data):
    """Import customers from JSON to PostgreSQL"""
    if not json_data:
        return 0
        
    from models_postgres import Customer
    customer_model = Customer()
    imported = 0
    
    print("\nImporting customers...")
    for customer_data in json_data:
        try:
            # Map JSON fields to new PostgreSQL structure
            mapped_data = {
                'customer_no': customer_data.get('customer_no') or customer_data.get('id', ''),
                'customer_name': customer_data.get('customer_name') or customer_data.get('name', ''),
                'customer_email': customer_data.get('customer_email') or customer_data.get('email', ''),
                'customer_phone': customer_data.get('customer_phone') or customer_data.get('phone', ''),
                'customer_address': customer_data.get('customer_address') or customer_data.get('address', ''),
                'customer_city': customer_data.get('customer_city', ''),
                'customer_state': customer_data.get('customer_state', ''),
                'customer_apgst': customer_data.get('customer_apgst', ''),
                'customer_cst': customer_data.get('customer_cst', ''),
            }
            
            # Check if customer already exists
            existing = customer_model.get_by_customer_no(mapped_data['customer_no'])
            if existing:
                print(f"  Skipping duplicate customer: {mapped_data['customer_name']}")
                continue
                
            # Create customer
            customer = customer_model.create(mapped_data)
            if customer:
                imported += 1
                print(f"  ✓ Imported: {mapped_data['customer_name']}")
            else:
                print(f"  ✗ Failed to import: {mapped_data['customer_name']}")
                
        except Exception as e:
            print(f"  ✗ Error importing customer {customer_data.get('name', 'Unknown')}: {e}")
    
    return imported

def import_cylinders(json_data):
    """Import cylinders from JSON to PostgreSQL"""
    if not json_data:
        return 0
        
    from models_postgres import Cylinder, Customer
    cylinder_model = Cylinder()
    customer_model = Customer()
    imported = 0
    
    print("\nImporting cylinders...")
    for cylinder_data in json_data:
        try:
            # Map JSON fields to PostgreSQL structure
            mapped_data = {
                'custom_id': cylinder_data.get('custom_id') or cylinder_data.get('id', ''),
                'serial_number': cylinder_data.get('serial_number', ''),
                'type': cylinder_data.get('type', 'Medical Oxygen'),
                'size': cylinder_data.get('size', '40L'),
                'status': cylinder_data.get('status', 'available').lower(),
                'location': cylinder_data.get('location', 'Warehouse'),
                'date_borrowed': cylinder_data.get('date_borrowed'),
                'date_returned': cylinder_data.get('date_returned'),
                'customer_name': cylinder_data.get('customer_name', ''),
                'customer_phone': cylinder_data.get('customer_phone', ''),
                'customer_address': cylinder_data.get('customer_address', ''),
                'customer_city': cylinder_data.get('customer_city', ''),
                'customer_state': cylinder_data.get('customer_state', ''),
            }
            
            # Handle rented_to field - link to customer if exists
            rented_to = cylinder_data.get('rented_to')
            if rented_to:
                # Try to find customer by ID or customer_no
                customer = customer_model.get_by_id(rented_to) or customer_model.get_by_customer_no(rented_to)
                if customer:
                    mapped_data['rented_to'] = customer.get('id')
                else:
                    mapped_data['rented_to'] = None
            else:
                mapped_data['rented_to'] = None
            
            # Check if cylinder already exists
            existing = cylinder_model.get_by_custom_id(mapped_data['custom_id'])
            if existing:
                print(f"  Skipping duplicate cylinder: {mapped_data['custom_id']}")
                continue
                
            # Create cylinder
            cylinder = cylinder_model.create(mapped_data)
            if cylinder:
                imported += 1
                status_display = f"({mapped_data['status']})"
                print(f"  ✓ Imported: {mapped_data['custom_id']} {status_display}")
            else:
                print(f"  ✗ Failed to import: {mapped_data['custom_id']}")
                
        except Exception as e:
            print(f"  ✗ Error importing cylinder {cylinder_data.get('custom_id', 'Unknown')}: {e}")
    
    return imported

def import_rental_history(json_data):
    """Import rental history from JSON to PostgreSQL"""
    if not json_data:
        return 0
        
    try:
        from models_rental_history import RentalHistory
        rental_model = RentalHistory()
        imported = 0
        
        print("\nImporting rental history...")
        for rental_data in json_data:
            try:
                # Map JSON fields to PostgreSQL structure
                mapped_data = {
                    'customer_no': rental_data.get('customer_no', ''),
                    'customer_name': rental_data.get('customer_name', ''),
                    'cylinder_no': rental_data.get('cylinder_no', ''),
                    'cylinder_id': rental_data.get('cylinder_id', ''),
                    'date_borrowed': rental_data.get('date_borrowed'),
                    'date_returned': rental_data.get('date_returned'),
                    'rental_days': rental_data.get('rental_days', 0),
                    'cylinder_type': rental_data.get('cylinder_type', 'Medical Oxygen'),
                    'cylinder_size': rental_data.get('cylinder_size', '40L'),
                }
                
                # Create rental history record
                rental = rental_model.create(mapped_data)
                if rental:
                    imported += 1
                    print(f"  ✓ Imported rental: {mapped_data['customer_name']} - {mapped_data['cylinder_id']}")
                else:
                    print(f"  ✗ Failed to import rental: {mapped_data['customer_name']} - {mapped_data['cylinder_id']}")
                    
            except Exception as e:
                print(f"  ✗ Error importing rental {rental_data.get('customer_name', 'Unknown')}: {e}")
        
        return imported
    except ImportError:
        print("Rental history model not available, skipping...")
        return 0

def main():
    """Main import function"""
    print("="*60)
    print("JSON to PostgreSQL Import Utility")
    print("="*60)
    
    # Check if data directory exists
    data_dir = Path('data')
    if not data_dir.exists():
        print("Error: 'data' directory not found!")
        print("Please ensure your JSON files are in a 'data' directory")
        sys.exit(1)
    
    # Define JSON files to import
    json_files = {
        'customers': 'data/customers.json',
        'cylinders': 'data/cylinders.json',
        'rental_history': 'data/rental_history.json',
        'rental_transactions': 'data/rental_transactions.json'
    }
    
    # Check which files exist
    available_files = {}
    for name, path in json_files.items():
        if Path(path).exists():
            available_files[name] = path
            print(f"Found: {path}")
        else:
            print(f"Not found: {path}")
    
    if not available_files:
        print("\nNo JSON files found to import!")
        print("Expected files in 'data' directory:")
        for name, path in json_files.items():
            print(f"  - {path}")
        sys.exit(1)
    
    print(f"\nFound {len(available_files)} JSON file(s) to import")
    
    # Confirm import
    response = input("\nProceed with import? (y/N): ").strip().lower()
    if response != 'y':
        print("Import cancelled.")
        sys.exit(0)
    
    # Test database connection
    try:
        from models_postgres import Customer
        customer_model = Customer()
        print("✓ Database connection successful")
    except Exception as e:
        print(f"✗ Database connection failed: {e}")
        print("Please ensure PostgreSQL is running and DATABASE_URL is correct")
        sys.exit(1)
    
    # Import data
    total_imported = 0
    
    # Import customers first (other tables may reference them)
    if 'customers' in available_files:
        customers_data = load_json_file(available_files['customers'])
        total_imported += import_customers(customers_data)
    
    # Import cylinders
    if 'cylinders' in available_files:
        cylinders_data = load_json_file(available_files['cylinders'])
        total_imported += import_cylinders(cylinders_data)
    
    # Import rental history
    for history_file in ['rental_history', 'rental_transactions']:
        if history_file in available_files:
            history_data = load_json_file(available_files[history_file])
            total_imported += import_rental_history(history_data)
    
    print("\n" + "="*60)
    print(f"Import Complete! Total records imported: {total_imported}")
    print("="*60)
    
    if total_imported > 0:
        print("\nYou can now run the application with:")
        print("python run_local.py")
        print("\nOr start the server directly:")
        print("python main.py")

if __name__ == '__main__':
    main()