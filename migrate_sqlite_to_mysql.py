"""
Migration script to transfer data from SQLite to MySQL
For Varasai Oxygen Cylinder Tracker
"""
import sqlite3
import pymysql
import os
import uuid
from datetime import datetime

# MySQL configuration for PythonAnywhere
MYSQL_CONFIG = {
    'host': os.environ.get('MYSQL_HOST', 'localhost'),
    'user': os.environ.get('MYSQL_USER', 'root'),
    'password': os.environ.get('MYSQL_PASSWORD', ''),
    'database': os.environ.get('MYSQL_DATABASE', 'oxygen_tracker'),
    'charset': 'utf8mb4'
}

def get_sqlite_connection():
    """Get SQLite database connection"""
    return sqlite3.connect('database.db')

def get_mysql_connection():
    """Get MySQL database connection"""
    try:
        return pymysql.connect(**MYSQL_CONFIG)
    except Exception as e:
        print(f"MySQL connection error: {e}")
        return None

def migrate_data():
    """Migrate all data from SQLite to MySQL"""
    # Connect to both databases
    sqlite_conn = get_sqlite_connection()
    sqlite_conn.row_factory = sqlite3.Row  # This enables column access by name
    mysql_conn = get_mysql_connection()
    
    if not mysql_conn:
        print("❌ Cannot connect to MySQL database")
        return False
    
    try:
        sqlite_cursor = sqlite_conn.cursor()
        mysql_cursor = mysql_conn.cursor()
        
        # Initialize MySQL database first
        print("🔧 Initializing MySQL database...")
        from app_mysql_clean import init_mysql_database
        if not init_mysql_database():
            print("❌ Failed to initialize MySQL database")
            return False
        
        # Migrate customers
        print("📊 Migrating customers...")
        sqlite_cursor.execute("SELECT * FROM customers")
        customers = sqlite_cursor.fetchall()
        
        customer_count = 0
        for customer in customers:
            try:
                mysql_cursor.execute('''
                    INSERT INTO customers (
                        id, customer_no, customer_name, customer_email, customer_phone,
                        customer_address, customer_city, customer_state, customer_apgst, customer_cst
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ''', (
                    customer['id'], customer['customer_no'], customer['customer_name'],
                    customer['customer_email'], customer['customer_phone'], customer['customer_address'],
                    customer['customer_city'], customer['customer_state'], customer['customer_apgst'], customer['customer_cst']
                ))
                customer_count += 1
            except Exception as e:
                print(f"⚠️  Error migrating customer {customer['customer_name']}: {e}")
        
        print(f"✅ Migrated {customer_count} customers")
        
        # Migrate cylinders
        print("📊 Migrating cylinders...")
        sqlite_cursor.execute("SELECT * FROM cylinders")
        cylinders = sqlite_cursor.fetchall()
        
        cylinder_count = 0
        for cylinder in cylinders:
            try:
                mysql_cursor.execute('''
                    INSERT INTO cylinders (
                        id, custom_id, serial_number, type, size, status, location,
                        pressure, last_inspection, next_inspection, notes, rented_to,
                        customer_name, customer_email, customer_phone, customer_no,
                        date_borrowed, date_returned
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ''', (
                    cylinder['id'], cylinder['custom_id'], cylinder['serial_number'],
                    cylinder['type'], cylinder['size'], cylinder['status'], cylinder['location'],
                    cylinder['pressure'], cylinder['last_inspection'], cylinder['next_inspection'],
                    cylinder['notes'], cylinder['rented_to'], cylinder['customer_name'],
                    cylinder['customer_email'], cylinder['customer_phone'], cylinder['customer_no'],
                    cylinder['date_borrowed'], cylinder['date_returned']
                ))
                cylinder_count += 1
            except Exception as e:
                print(f"⚠️  Error migrating cylinder {cylinder['custom_id'] or cylinder['id']}: {e}")
        
        print(f"✅ Migrated {cylinder_count} cylinders")
        
        # Migrate rental history
        print("📊 Migrating rental history...")
        sqlite_cursor.execute("SELECT * FROM rental_history")
        rental_records = sqlite_cursor.fetchall()
        
        rental_count = 0
        for record in rental_records:
            try:
                mysql_cursor.execute('''
                    INSERT INTO rental_history (
                        id, customer_no, customer_name, cylinder_custom_id, cylinder_type,
                        cylinder_size, dispatch_date, return_date, rental_days
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                ''', (
                    record['id'], record['customer_no'], record['customer_name'],
                    record['cylinder_custom_id'], record['cylinder_type'], record['cylinder_size'],
                    record['dispatch_date'], record['return_date'], record['rental_days']
                ))
                rental_count += 1
            except Exception as e:
                print(f"⚠️  Error migrating rental record {record['id']}: {e}")
        
        print(f"✅ Migrated {rental_count} rental history records")
        
        # Commit all changes
        mysql_conn.commit()
        
        # Print summary
        print("\n🎉 Migration completed successfully!")
        print(f"📈 Summary:")
        print(f"   • {customer_count} customers migrated")
        print(f"   • {cylinder_count} cylinders migrated") 
        print(f"   • {rental_count} rental history records migrated")
        
        return True
        
    except Exception as e:
        mysql_conn.rollback()
        print(f"❌ Migration failed: {e}")
        return False
    finally:
        sqlite_conn.close()
        mysql_conn.close()

if __name__ == '__main__':
    print("🚀 Starting SQLite to MySQL migration...")
    print("📋 Configuration:")
    print(f"   • MySQL Host: {MYSQL_CONFIG['host']}")
    print(f"   • MySQL Database: {MYSQL_CONFIG['database']}")
    print(f"   • MySQL User: {MYSQL_CONFIG['user']}")
    print()
    
    if migrate_data():
        print("✅ Migration completed successfully!")
        print("💡 You can now use app_mysql_clean.py for MySQL-based operations")
    else:
        print("❌ Migration failed!")