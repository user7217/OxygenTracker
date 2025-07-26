#!/usr/bin/env python3
"""
Migrate data from SQLite to MySQL database
"""
import sqlite3
import pymysql
import os
from datetime import datetime

# MySQL configuration
MYSQL_CONFIG = {
    'host': os.environ.get('MYSQL_HOST', 'localhost'),
    'user': os.environ.get('MYSQL_USER', 'root'),
    'password': os.environ.get('MYSQL_PASSWORD', ''),
    'database': os.environ.get('MYSQL_DATABASE', 'oxygen_tracker'),
    'charset': 'utf8mb4',
    'cursorclass': pymysql.cursors.DictCursor
}

def migrate_data():
    """Migrate all data from SQLite to MySQL"""
    
    # Connect to SQLite
    sqlite_conn = sqlite3.connect('database.db')
    sqlite_conn.row_factory = sqlite3.Row
    sqlite_cursor = sqlite_conn.cursor()
    
    # Connect to MySQL
    try:
        mysql_conn = pymysql.connect(**MYSQL_CONFIG)
        mysql_cursor = mysql_conn.cursor()
        
        # Create database if it doesn't exist
        mysql_cursor.execute(f"CREATE DATABASE IF NOT EXISTS {MYSQL_CONFIG['database']}")
        mysql_cursor.execute(f"USE {MYSQL_CONFIG['database']}")
        
        print("Starting SQLite to MySQL migration...")
        
        # Create MySQL tables first
        create_mysql_tables(mysql_cursor)
        print("✓ MySQL tables created")
        
        # Migrate customers
        customers_migrated = migrate_customers(sqlite_cursor, mysql_cursor)
        print(f"✓ Migrated {customers_migrated} customers")
        
        # Migrate cylinders
        cylinders_migrated = migrate_cylinders(sqlite_cursor, mysql_cursor)
        print(f"✓ Migrated {cylinders_migrated} cylinders")
        
        # Migrate rental history
        history_migrated = migrate_rental_history(sqlite_cursor, mysql_cursor)
        print(f"✓ Migrated {history_migrated} rental history records")
        
        mysql_conn.commit()
        print(f"\n🎉 Migration completed successfully!")
        print(f"Total: {customers_migrated} customers, {cylinders_migrated} cylinders, {history_migrated} history records")
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        if 'mysql_conn' in locals():
            mysql_conn.rollback()
        raise
    finally:
        sqlite_conn.close()
        if 'mysql_conn' in locals():
            mysql_conn.close()

def create_mysql_tables(cursor):
    """Create MySQL tables"""
    
    # Create customers table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS customers (
            id VARCHAR(50) PRIMARY KEY,
            customer_no VARCHAR(50) UNIQUE,
            customer_name VARCHAR(200) NOT NULL,
            customer_email VARCHAR(200),
            customer_phone VARCHAR(50),
            customer_address TEXT,
            customer_city VARCHAR(100),
            customer_state VARCHAR(100),
            customer_apgst VARCHAR(50),
            customer_cst VARCHAR(50),
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            INDEX idx_customer_no (customer_no),
            INDEX idx_customer_name (customer_name)
        )
    ''')
    
    # Create cylinders table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS cylinders (
            id VARCHAR(50) PRIMARY KEY,
            custom_id VARCHAR(50) UNIQUE,
            serial_number VARCHAR(100),
            type VARCHAR(50) DEFAULT 'Medical Oxygen',
            size VARCHAR(20) DEFAULT '40L',
            status VARCHAR(20) DEFAULT 'available',
            location VARCHAR(200) DEFAULT 'Warehouse',
            pressure VARCHAR(50),
            last_inspection VARCHAR(50),
            next_inspection VARCHAR(50),
            notes TEXT,
            rented_to VARCHAR(50),
            customer_name VARCHAR(200),
            customer_email VARCHAR(200),
            customer_phone VARCHAR(50),
            customer_no VARCHAR(50),
            date_borrowed DATETIME,
            date_returned DATETIME,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            INDEX idx_custom_id (custom_id),
            INDEX idx_status (status),
            INDEX idx_customer_no (customer_no)
        )
    ''')
    
    # Create rental_history table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS rental_history (
            id VARCHAR(50) PRIMARY KEY,
            customer_no VARCHAR(50),
            customer_name VARCHAR(200),
            cylinder_custom_id VARCHAR(50),
            cylinder_type VARCHAR(50),
            cylinder_size VARCHAR(20),
            dispatch_date DATETIME,
            return_date DATETIME,
            rental_days INT DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_customer_no (customer_no),
            INDEX idx_cylinder_id (cylinder_custom_id),
            INDEX idx_dispatch_date (dispatch_date)
        )
    ''')

def migrate_customers(sqlite_cursor, mysql_cursor):
    """Migrate customers from SQLite to MySQL"""
    sqlite_cursor.execute("SELECT * FROM customers")
    customers = sqlite_cursor.fetchall()
    count = 0
    
    for customer in customers:
        try:
            mysql_cursor.execute('''
                INSERT IGNORE INTO customers 
                (id, customer_no, customer_name, customer_email, customer_phone,
                 customer_address, customer_city, customer_state, customer_apgst,
                 customer_cst, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ''', (
                customer['id'], customer['customer_no'], customer['customer_name'],
                customer['customer_email'], customer['customer_phone'], customer['customer_address'],
                customer['customer_city'], customer['customer_state'], customer['customer_apgst'],
                customer['customer_cst'], customer['created_at'], customer['updated_at']
            ))
            count += 1
        except Exception as e:
            print(f"Error migrating customer {customer['id']}: {e}")
    
    return count

def migrate_cylinders(sqlite_cursor, mysql_cursor):
    """Migrate cylinders from SQLite to MySQL"""
    sqlite_cursor.execute("SELECT * FROM cylinders")
    cylinders = sqlite_cursor.fetchall()
    count = 0
    
    for cylinder in cylinders:
        try:
            mysql_cursor.execute('''
                INSERT IGNORE INTO cylinders 
                (id, custom_id, serial_number, type, size, status, location,
                 pressure, last_inspection, next_inspection, notes, rented_to,
                 customer_name, customer_email, customer_phone, customer_no,
                 date_borrowed, date_returned, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ''', (
                cylinder['id'], cylinder['custom_id'], cylinder['serial_number'],
                cylinder['type'], cylinder['size'], cylinder['status'], cylinder['location'],
                cylinder['pressure'], cylinder['last_inspection'], cylinder['next_inspection'],
                cylinder['notes'], cylinder['rented_to'], cylinder['customer_name'],
                cylinder['customer_email'], cylinder['customer_phone'], cylinder['customer_no'],
                cylinder['date_borrowed'], cylinder['date_returned'], cylinder['created_at'], cylinder['updated_at']
            ))
            count += 1
        except Exception as e:
            print(f"Error migrating cylinder {cylinder['id']}: {e}")
    
    return count

def migrate_rental_history(sqlite_cursor, mysql_cursor):
    """Migrate rental history from SQLite to MySQL"""
    sqlite_cursor.execute("SELECT * FROM rental_history LIMIT 10000")
    history = sqlite_cursor.fetchall()
    count = 0
    
    for record in history:
        try:
            mysql_cursor.execute('''
                INSERT IGNORE INTO rental_history 
                (id, customer_no, customer_name, cylinder_custom_id,
                 cylinder_type, cylinder_size, dispatch_date, return_date,
                 rental_days, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ''', (
                record['id'], record['customer_no'], record['customer_name'],
                record['cylinder_custom_id'], record['cylinder_type'], record['cylinder_size'],
                record['dispatch_date'], record['return_date'], record['rental_days'], record['created_at']
            ))
            count += 1
        except Exception as e:
            print(f"Error migrating rental history {record['id']}: {e}")
    
    return count

if __name__ == '__main__':
    migrate_data()