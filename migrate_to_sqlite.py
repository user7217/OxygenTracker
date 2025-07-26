#!/usr/bin/env python3
"""
Migrate data from PostgreSQL to SQLite for the oxygen cylinder tracker
"""
import os
import sqlite3
import psycopg2
from datetime import datetime

def migrate_data():
    """Migrate all data from PostgreSQL to SQLite"""
    
    # Connect to PostgreSQL
    pg_conn = psycopg2.connect(os.environ['DATABASE_URL'])
    pg_cursor = pg_conn.cursor()
    
    # Connect to SQLite
    sqlite_conn = sqlite3.connect('database.db')
    sqlite_cursor = sqlite_conn.cursor()
    
    try:
        print("Starting PostgreSQL to SQLite migration...")
        
        # Create SQLite tables
        create_sqlite_tables(sqlite_cursor)
        print("✓ SQLite tables created")
        
        # Migrate customers
        customers_migrated = migrate_customers(pg_cursor, sqlite_cursor)
        print(f"✓ Migrated {customers_migrated} customers")
        
        # Migrate cylinders  
        cylinders_migrated = migrate_cylinders(pg_cursor, sqlite_cursor)
        print(f"✓ Migrated {cylinders_migrated} cylinders")
        
        # Migrate rental history
        history_migrated = migrate_rental_history(pg_cursor, sqlite_cursor)
        print(f"✓ Migrated {history_migrated} rental history records")
        
        sqlite_conn.commit()
        print(f"\n🎉 Migration completed successfully!")
        print(f"Total: {customers_migrated} customers, {cylinders_migrated} cylinders, {history_migrated} history records")
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        sqlite_conn.rollback()
        raise
    finally:
        pg_conn.close()
        sqlite_conn.close()

def create_sqlite_tables(cursor):
    """Create SQLite tables"""
    
    # Create customers table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS customers (
            id TEXT PRIMARY KEY,
            customer_no TEXT UNIQUE,
            customer_name TEXT NOT NULL,
            customer_email TEXT,
            customer_phone TEXT,
            customer_address TEXT,
            customer_city TEXT,
            customer_state TEXT,
            customer_apgst TEXT,
            customer_cst TEXT,
            created_at DATETIME,
            updated_at DATETIME
        )
    ''')
    
    # Create cylinders table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS cylinders (
            id TEXT PRIMARY KEY,
            custom_id TEXT UNIQUE,
            serial_number TEXT,
            type TEXT DEFAULT 'Medical Oxygen',
            size TEXT DEFAULT '40L',
            status TEXT DEFAULT 'available',
            location TEXT DEFAULT 'Warehouse',
            pressure TEXT,
            last_inspection TEXT,
            next_inspection TEXT,
            notes TEXT,
            rented_to TEXT,
            customer_name TEXT,
            customer_email TEXT,
            customer_phone TEXT,
            customer_no TEXT,
            date_borrowed DATETIME,
            date_returned DATETIME,
            created_at DATETIME,
            updated_at DATETIME
        )
    ''')
    
    # Create rental_history table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS rental_history (
            id TEXT PRIMARY KEY,
            customer_no TEXT,
            customer_name TEXT,
            cylinder_custom_id TEXT,
            cylinder_type TEXT,
            cylinder_size TEXT,
            dispatch_date DATETIME,
            return_date DATETIME,
            rental_days INTEGER DEFAULT 0,
            created_at DATETIME
        )
    ''')

def migrate_customers(pg_cursor, sqlite_cursor):
    """Migrate customers from PostgreSQL to SQLite"""
    pg_cursor.execute("""
        SELECT id, customer_no, customer_name, customer_email, customer_phone,
               customer_address, customer_city, customer_state, customer_apgst,
               customer_cst, created_at, updated_at
        FROM customers
    """)
    
    customers = pg_cursor.fetchall()
    count = 0
    
    for customer in customers:
        try:
            sqlite_cursor.execute('''
                INSERT OR REPLACE INTO customers 
                (id, customer_no, customer_name, customer_email, customer_phone,
                 customer_address, customer_city, customer_state, customer_apgst,
                 customer_cst, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', customer)
            count += 1
        except Exception as e:
            print(f"Error migrating customer {customer[0]}: {e}")
    
    return count

def migrate_cylinders(pg_cursor, sqlite_cursor):
    """Migrate cylinders from PostgreSQL to SQLite"""
    pg_cursor.execute("""
        SELECT id, custom_id, serial_number, type, size, status, location,
               rented_to, customer_name, customer_email, customer_phone, customer_no,
               date_borrowed, date_returned, created_at, updated_at
        FROM cylinders
    """)
    
    cylinders = pg_cursor.fetchall()
    count = 0
    
    for cylinder in cylinders:
        try:
            sqlite_cursor.execute('''
                INSERT OR REPLACE INTO cylinders 
                (id, custom_id, serial_number, type, size, status, location,
                 rented_to, customer_name, customer_email, customer_phone, customer_no,
                 date_borrowed, date_returned, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', cylinder)
            count += 1
        except Exception as e:
            print(f"Error migrating cylinder {cylinder[0]}: {e}")
    
    return count

def migrate_rental_history(pg_cursor, sqlite_cursor):
    """Migrate rental history from PostgreSQL to SQLite"""
    pg_cursor.execute("""
        SELECT id, customer_no, customer_name, cylinder_custom_id,
               cylinder_type, cylinder_size, dispatch_date, return_date,
               rental_days, created_at
        FROM rental_history
        LIMIT 10000
    """)
    
    history = pg_cursor.fetchall()
    count = 0
    
    for record in history:
        try:
            sqlite_cursor.execute('''
                INSERT OR REPLACE INTO rental_history 
                (id, customer_no, customer_name, cylinder_custom_id,
                 cylinder_type, cylinder_size, dispatch_date, return_date,
                 rental_days, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', record)
            count += 1
        except Exception as e:
            print(f"Error migrating rental history {record[0]}: {e}")
    
    return count

if __name__ == '__main__':
    migrate_data()