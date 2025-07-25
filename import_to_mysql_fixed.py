#!/usr/bin/env python3
"""
Import data from JSON files to MySQL database for PythonAnywhere deployment
Uses the fixed app configuration
"""
import os
import json
import sys
from datetime import datetime, timezone

def import_all_data():
    """Import all data from JSON files to MySQL"""
    try:
        # Import Flask app and models from the fixed version
        from app_mysql_fixed import app, db, Customer, Cylinder, RentalHistory
        
        with app.app_context():
            print("Starting MySQL data import...")
            
            # Create tables if they don't exist
            db.create_all()
            print("✓ MySQL database tables ready")
            
            # Import customers
            customers_imported = import_customers(db, Customer)
            print(f"✓ Imported {customers_imported} customers")
            
            # Import cylinders
            cylinders_imported = import_cylinders(db, Cylinder)
            print(f"✓ Imported {cylinders_imported} cylinders")
            
            # Import rental history
            history_imported = import_rental_history(db, RentalHistory)
            print(f"✓ Imported {history_imported} rental history records")
            
            print("\n🎉 MySQL data import completed successfully!")
            print(f"Total: {customers_imported} customers, {cylinders_imported} cylinders, {history_imported} rental records")
            
    except Exception as e:
        print(f"❌ Error during import: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

def import_customers(db, Customer):
    """Import customers from JSON file"""
    json_file = os.path.join('data', 'customers.json')
    if not os.path.exists(json_file):
        print(f"⚠️  No customers.json found at {json_file}")
        return 0
    
    count = 0
    with open(json_file, 'r', encoding='utf-8') as f:
        customers_data = json.load(f)
        
        for customer_data in customers_data:
            # Check if customer already exists
            existing = Customer.query.filter_by(id=customer_data.get('id')).first()
            if existing:
                continue
                
            customer = Customer(
                id=customer_data.get('id'),
                customer_no=customer_data.get('customer_no', ''),
                customer_name=customer_data.get('customer_name', ''),
                customer_email=customer_data.get('customer_email', ''),
                customer_phone=customer_data.get('customer_phone', ''),
                customer_address=customer_data.get('customer_address', ''),
                customer_city=customer_data.get('customer_city', ''),
                customer_state=customer_data.get('customer_state', ''),
                customer_apgst=customer_data.get('customer_apgst', ''),
                customer_cst=customer_data.get('customer_cst', ''),
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc)
            )
            db.session.add(customer)
            count += 1
    
    db.session.commit()
    return count

def import_cylinders(db, Cylinder):
    """Import cylinders from JSON file"""
    json_file = os.path.join('data', 'cylinders.json')
    if not os.path.exists(json_file):
        print(f"⚠️  No cylinders.json found at {json_file}")
        return 0
    
    count = 0
    with open(json_file, 'r', encoding='utf-8') as f:
        cylinders_data = json.load(f)
        
        for cylinder_data in cylinders_data:
            # Check if cylinder already exists
            existing = Cylinder.query.filter_by(id=cylinder_data.get('id')).first()
            if existing:
                continue
                
            # Parse dates
            date_borrowed = None
            date_returned = None
            
            if cylinder_data.get('date_borrowed'):
                try:
                    date_borrowed = datetime.fromisoformat(cylinder_data['date_borrowed'].replace('Z', '+00:00'))
                except:
                    pass
                    
            if cylinder_data.get('date_returned'):
                try:
                    date_returned = datetime.fromisoformat(cylinder_data['date_returned'].replace('Z', '+00:00'))
                except:
                    pass
            
            cylinder = Cylinder(
                id=cylinder_data.get('id'),
                custom_id=cylinder_data.get('custom_id', ''),
                serial_number=cylinder_data.get('serial_number', ''),
                type=cylinder_data.get('type', 'Medical Oxygen'),
                size=cylinder_data.get('size', '40L'),
                status=cylinder_data.get('status', 'available'),
                location=cylinder_data.get('location', 'Warehouse'),
                pressure=cylinder_data.get('pressure'),
                last_inspection=cylinder_data.get('last_inspection'),
                next_inspection=cylinder_data.get('next_inspection'),
                notes=cylinder_data.get('notes', ''),
                rented_to=cylinder_data.get('rented_to'),
                customer_name=cylinder_data.get('customer_name', ''),
                customer_email=cylinder_data.get('customer_email', ''),
                customer_phone=cylinder_data.get('customer_phone', ''),
                customer_no=cylinder_data.get('customer_no', ''),
                date_borrowed=date_borrowed,
                date_returned=date_returned,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc)
            )
            db.session.add(cylinder)
            count += 1
    
    db.session.commit()
    return count

def import_rental_history(db, RentalHistory):
    """Import rental history from JSON file"""
    json_file = os.path.join('data', 'rental_history.json')
    if not os.path.exists(json_file):
        print(f"⚠️  No rental_history.json found at {json_file}")
        return 0
    
    count = 0
    with open(json_file, 'r', encoding='utf-8') as f:
        history_data = json.load(f)
        
        for record in history_data:
            # Check if record already exists
            existing = RentalHistory.query.filter_by(id=record.get('id')).first()
            if existing:
                continue
                
            # Parse dates
            dispatch_date = None
            return_date = None
            
            if record.get('dispatch_date'):
                try:
                    dispatch_date = datetime.fromisoformat(record['dispatch_date'].replace('Z', '+00:00'))
                except:
                    pass
                    
            if record.get('return_date'):
                try:
                    return_date = datetime.fromisoformat(record['return_date'].replace('Z', '+00:00'))
                except:
                    pass
            
            rental_record = RentalHistory(
                id=record.get('id'),
                customer_no=record.get('customer_no', ''),
                customer_name=record.get('customer_name', ''),
                cylinder_custom_id=record.get('cylinder_custom_id', ''),
                cylinder_type=record.get('cylinder_type', ''),
                cylinder_size=record.get('cylinder_size', ''),
                dispatch_date=dispatch_date,
                return_date=return_date,
                rental_days=record.get('rental_days', 0),
                created_at=datetime.now(timezone.utc)
            )
            db.session.add(rental_record)
            count += 1
    
    db.session.commit()
    return count

if __name__ == '__main__':
    import_all_data()