# db_migration.py - Migrate data from JSON to PostgreSQL
import json
import os
from datetime import datetime
from db_models import create_tables, get_db_session, Customer, Cylinder, RentalHistory
from sqlalchemy.exc import IntegrityError

def migrate_json_to_postgresql():
    """Migrate all data from JSON files to PostgreSQL"""
    print("Starting migration from JSON to PostgreSQL...")
    
    # Create database tables
    create_tables()
    db = get_db_session()
    
    try:
        # Migrate customers
        print("Migrating customers...")
        migrate_customers(db)
        
        # Migrate cylinders
        print("Migrating cylinders...")
        migrate_cylinders(db)
        
        # Migrate rental history
        print("Migrating rental history...")
        migrate_rental_history(db)
        
        db.commit()
        print("Migration completed successfully!")
        
        # Print migration statistics
        print_migration_stats(db)
        
    except Exception as e:
        print(f"Migration failed: {e}")
        db.rollback()
        raise
    finally:
        db.close()

def migrate_customers(db):
    """Migrate customers from JSON to PostgreSQL"""
    if not os.path.exists('data/customers.json'):
        print("No customers.json file found, skipping customer migration")
        return
    
    with open('data/customers.json', 'r') as f:
        customers_data = json.load(f)
    
    migrated = 0
    for customer_data in customers_data:
        try:
            # Convert datetime strings
            created_at = None
            updated_at = None
            if customer_data.get('created_at'):
                try:
                    created_at = datetime.fromisoformat(customer_data['created_at'].replace('Z', '+00:00'))
                except:
                    created_at = datetime.utcnow()
            
            if customer_data.get('updated_at'):
                try:
                    updated_at = datetime.fromisoformat(customer_data['updated_at'].replace('Z', '+00:00'))
                except:
                    updated_at = datetime.utcnow()
            
            customer = Customer(
                id=customer_data.get('id', ''),
                customer_no=customer_data.get('customer_no', ''),
                customer_name=customer_data.get('customer_name', '') or customer_data.get('name', ''),
                customer_email=customer_data.get('customer_email', '') or customer_data.get('email', ''),
                customer_phone=customer_data.get('customer_phone', '') or customer_data.get('phone', ''),
                customer_address=customer_data.get('customer_address', '') or customer_data.get('address', ''),
                customer_city=customer_data.get('customer_city', '') or customer_data.get('city', ''),
                customer_state=customer_data.get('customer_state', '') or customer_data.get('state', ''),
                customer_apgst=customer_data.get('customer_apgst', ''),
                customer_cst=customer_data.get('customer_cst', ''),
                created_at=created_at or datetime.utcnow(),
                updated_at=updated_at or datetime.utcnow()
            )
            
            db.add(customer)
            migrated += 1
            
        except IntegrityError as e:
            print(f"Skipping duplicate customer: {customer_data.get('customer_no', 'Unknown')}")
            db.rollback()
            db = get_db_session()
        except Exception as e:
            print(f"Error migrating customer {customer_data.get('customer_no', 'Unknown')}: {e}")
    
    print(f"Migrated {migrated} customers")

def migrate_cylinders(db):
    """Migrate cylinders from JSON to PostgreSQL"""
    if not os.path.exists('data/cylinders.json'):
        print("No cylinders.json file found, skipping cylinder migration")
        return
    
    with open('data/cylinders.json', 'r') as f:
        cylinders_data = json.load(f)
    
    migrated = 0
    for cylinder_data in cylinders_data:
        try:
            # Convert datetime strings
            date_borrowed = None
            rental_date = None
            date_returned = None
            created_at = None
            updated_at = None
            
            if cylinder_data.get('date_borrowed'):
                try:
                    date_borrowed = datetime.fromisoformat(cylinder_data['date_borrowed'].replace('Z', '+00:00'))
                except:
                    pass
                    
            if cylinder_data.get('rental_date'):
                try:
                    rental_date = datetime.fromisoformat(cylinder_data['rental_date'].replace('Z', '+00:00'))
                except:
                    pass
                    
            if cylinder_data.get('date_returned'):
                try:
                    date_returned = datetime.fromisoformat(cylinder_data['date_returned'].replace('Z', '+00:00'))
                except:
                    pass
            
            if cylinder_data.get('created_at'):
                try:
                    created_at = datetime.fromisoformat(cylinder_data['created_at'].replace('Z', '+00:00'))
                except:
                    created_at = datetime.utcnow()
                    
            if cylinder_data.get('updated_at'):
                try:
                    updated_at = datetime.fromisoformat(cylinder_data['updated_at'].replace('Z', '+00:00'))
                except:
                    updated_at = datetime.utcnow()
            
            # Handle foreign key constraint - only set rented_to if it's a valid customer ID
            rented_to_value = cylinder_data.get('rented_to', '')
            if rented_to_value is None or (isinstance(rented_to_value, str) and not rented_to_value.strip()):
                rented_to_value = None
            
            cylinder = Cylinder(
                id=cylinder_data.get('id', ''),
                custom_id=cylinder_data.get('custom_id', ''),
                serial_number=cylinder_data.get('serial_number', ''),
                type=cylinder_data.get('type', 'Medical Oxygen'),
                size=cylinder_data.get('size', '40L'),
                status=cylinder_data.get('status', 'available'),
                location=cylinder_data.get('location', 'Warehouse'),
                rented_to=rented_to_value,
                customer_name=cylinder_data.get('customer_name', ''),
                customer_email=cylinder_data.get('customer_email', ''),
                customer_phone=cylinder_data.get('customer_phone', ''),
                customer_no=cylinder_data.get('customer_no', ''),
                customer_city=cylinder_data.get('customer_city', ''),
                customer_state=cylinder_data.get('customer_state', ''),
                date_borrowed=date_borrowed,
                rental_date=rental_date,
                date_returned=date_returned,
                created_at=created_at or datetime.utcnow(),
                updated_at=updated_at or datetime.utcnow()
            )
            
            db.add(cylinder)
            migrated += 1
            
        except Exception as e:
            print(f"Error migrating cylinder {cylinder_data.get('id', 'Unknown')}: {e}")
    
    print(f"Migrated {migrated} cylinders")

def migrate_rental_history(db):
    """Migrate rental history from JSON to PostgreSQL"""
    if not os.path.exists('data/rental_history.json'):
        print("No rental_history.json file found, skipping rental history migration")
        return
    
    with open('data/rental_history.json', 'r') as f:
        history_data = json.load(f)
    
    migrated = 0
    for history_record in history_data:
        try:
            # Convert datetime strings
            dispatch_date = None
            return_date = None
            date_borrowed = None
            date_returned = None
            created_at = None
            
            if history_record.get('dispatch_date'):
                try:
                    dispatch_date = datetime.fromisoformat(history_record['dispatch_date'].replace('Z', '+00:00'))
                except:
                    try:
                        dispatch_date = datetime.strptime(history_record['dispatch_date'], '%Y-%m-%d')
                    except:
                        pass
                        
            if history_record.get('return_date'):
                try:
                    return_date = datetime.fromisoformat(history_record['return_date'].replace('Z', '+00:00'))
                except:
                    try:
                        return_date = datetime.strptime(history_record['return_date'], '%Y-%m-%d')
                    except:
                        pass
                        
            if history_record.get('date_borrowed'):
                try:
                    date_borrowed = datetime.fromisoformat(history_record['date_borrowed'].replace('Z', '+00:00'))
                except:
                    pass
                    
            if history_record.get('date_returned'):
                try:
                    date_returned = datetime.fromisoformat(history_record['date_returned'].replace('Z', '+00:00'))
                except:
                    pass
            
            if history_record.get('created_at'):
                try:
                    created_at = datetime.fromisoformat(history_record['created_at'].replace('Z', '+00:00'))
                except:
                    created_at = datetime.utcnow()
            
            # Handle foreign key for customer_id - set to None if empty
            customer_id_value = history_record.get('customer_id', '')
            if not customer_id_value or customer_id_value.strip() == '':
                customer_id_value = None
            
            rental_history = RentalHistory(
                id=history_record.get('id', ''),
                customer_id=customer_id_value,
                customer_no=history_record.get('customer_no', ''),
                customer_name=history_record.get('customer_name', ''),
                customer_phone=history_record.get('customer_phone', ''),
                customer_email=history_record.get('customer_email', ''),
                customer_address=history_record.get('customer_address', ''),
                customer_city=history_record.get('customer_city', ''),
                customer_state=history_record.get('customer_state', ''),
                cylinder_id=history_record.get('cylinder_id', ''),
                cylinder_no=history_record.get('cylinder_no', ''),
                cylinder_custom_id=history_record.get('cylinder_custom_id', ''),
                cylinder_serial=history_record.get('cylinder_serial', ''),
                cylinder_type=history_record.get('cylinder_type', ''),
                cylinder_size=history_record.get('cylinder_size', ''),
                dispatch_date=dispatch_date,
                return_date=return_date,
                date_borrowed=date_borrowed,
                date_returned=date_returned,
                rental_days=history_record.get('rental_days', 0),
                location=history_record.get('location', ''),
                status=history_record.get('status', 'completed'),
                created_at=created_at or datetime.utcnow()
            )
            
            db.add(rental_history)
            migrated += 1
            
        except Exception as e:
            print(f"Error migrating rental history record {history_record.get('id', 'Unknown')}: {e}")
    
    print(f"Migrated {migrated} rental history records")

def print_migration_stats(db):
    """Print migration statistics"""
    customers_count = db.query(Customer).count()
    cylinders_count = db.query(Cylinder).count()
    history_count = db.query(RentalHistory).count()
    
    print(f"\nMigration Statistics:")
    print(f"- Customers: {customers_count}")
    print(f"- Cylinders: {cylinders_count}")
    print(f"- Rental History: {history_count}")

if __name__ == '__main__':
    migrate_json_to_postgresql()