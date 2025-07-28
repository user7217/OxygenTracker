"""
Sample data loader for SQLite database
Creates sample customers and cylinders for testing
"""
import sqlite3
import uuid
from datetime import datetime, timedelta
import random
from app import get_db_connection, init_sqlite_database

def create_sample_data():
    """Create sample customers and cylinders for testing"""
    # Initialize database first
    if not init_sqlite_database():
        print("Failed to initialize database")
        return False
    
    connection = get_db_connection()
    if not connection:
        print("Failed to connect to database")
        return False
    
    try:
        cursor = connection.cursor()
        
        # Sample customers
        customers = [
            ('CUST001', 'ABC Healthcare Ltd', 'admin@abchealthcare.com', '+91-9876543210', '123 Medical Street', 'Mumbai', 'Maharashtra', 'GSTIN123', 'CST123'),
            ('CUST002', 'XYZ Hospital', 'contact@xyzhospital.com', '+91-9876543211', '456 Hospital Road', 'Delhi', 'Delhi', 'GSTIN456', 'CST456'),
            ('CUST003', 'Medical Supply Co', 'info@medsupply.com', '+91-9876543212', '789 Supply Avenue', 'Bangalore', 'Karnataka', 'GSTIN789', 'CST789'),
            ('CUST004', 'City Clinic', 'admin@cityclinic.com', '+91-9876543213', '321 Clinic Lane', 'Chennai', 'Tamil Nadu', 'GSTIN321', 'CST321'),
            ('CUST005', 'Metro Hospital', 'contact@metrohospital.com', '+91-9876543214', '654 Metro Street', 'Pune', 'Maharashtra', 'GSTIN654', 'CST654'),
        ]
        
        print("Creating sample customers...")
        for customer_no, name, email, phone, address, city, state, apgst, cst in customers:
            customer_id = str(uuid.uuid4())
            cursor.execute('''
                INSERT INTO customers (id, customer_no, customer_name, customer_email, customer_phone,
                                     customer_address, customer_city, customer_state, customer_apgst, customer_cst)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ''', (customer_id, customer_no, name, email, phone, address, city, state, apgst, cst))
        
        # Sample cylinders
        cylinder_types = ['Medical Oxygen', 'Industrial Oxygen', 'CO2', 'Argon', 'Nitrogen']
        cylinder_sizes = ['40L', '10L', '20L', '50L']
        
        print("Creating sample cylinders...")
        for i in range(1, 26):  # Create 25 cylinders
            cylinder_id = str(uuid.uuid4())
            custom_id = f"CYL{i:03d}"
            serial_number = f"SER{i:06d}"
            cylinder_type = random.choice(cylinder_types)
            size = random.choice(cylinder_sizes)
            
            # Some cylinders are rented, some available
            if i <= 10:  # First 10 are available
                status = 'available'
                location = 'Warehouse'
                rented_to = None
                customer_name = None
                date_borrowed = None
            else:  # Rest are rented
                status = 'rented'
                location = 'Customer Site'
                rented_to = customers[i % len(customers)][0]  # Customer number
                customer_name = customers[i % len(customers)][1]  # Customer name
                # Random date in last 6 months
                days_ago = random.randint(1, 180)
                date_borrowed = datetime.now() - timedelta(days=days_ago)
            
            cursor.execute('''
                INSERT INTO cylinders (id, custom_id, serial_number, type, size, status, location,
                                     rented_to, customer_name, date_borrowed)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ''', (cylinder_id, custom_id, serial_number, cylinder_type, size, status, location,
                  rented_to, customer_name, date_borrowed))
        
        # Sample rental history
        print("Creating sample rental history...")
        for i in range(1, 11):  # Create 10 rental history records
            history_id = str(uuid.uuid4())
            customer = customers[i % len(customers)]
            customer_no = customer[0]
            customer_name = customer[1]
            cylinder_custom_id = f"CYL{i:03d}"
            cylinder_type = random.choice(cylinder_types)
            cylinder_size = random.choice(cylinder_sizes)
            
            # Random dates for completed rentals
            return_date = datetime.now() - timedelta(days=random.randint(1, 30))
            dispatch_date = return_date - timedelta(days=random.randint(10, 90))
            rental_days = (return_date - dispatch_date).days
            
            cursor.execute('''
                INSERT INTO rental_history (id, customer_no, customer_name, cylinder_custom_id,
                                          cylinder_type, cylinder_size, dispatch_date, return_date, rental_days)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            ''', (history_id, customer_no, customer_name, cylinder_custom_id,
                  cylinder_type, cylinder_size, dispatch_date, return_date, rental_days))
        
        connection.commit()
        
        print("✅ Sample data created successfully!")
        print(f"📊 Created:")
        print(f"   • {len(customers)} customers")
        print(f"   • 25 cylinders (10 available, 15 rented)")
        print(f"   • 10 rental history records")
        
        return True
        
    except Exception as e:
        connection.rollback()
        print(f"❌ Error creating sample data: {e}")
        return False
    finally:
        connection.close()

if __name__ == '__main__':
    print("🚀 Creating sample data for SQLite database...")
    print("📋 Database: oxygen_tracker.db")
    print()
    
    if create_sample_data():
        print("✅ Sample data creation completed successfully!")
        print("💡 You can now test the application with sample data")
    else:
        print("❌ Sample data creation failed!")