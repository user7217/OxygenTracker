#!/usr/bin/env python3
"""
Fix Render Database Schema
Ensures the rental_history table has the correct structure on Render
"""

import os
import sys
from sqlalchemy import create_engine, text, inspect
from datetime import datetime

def fix_render_database():
    """Fix the Render database schema to match the models"""
    
    # Get database URL from environment
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        print("Error: DATABASE_URL environment variable not found")
        return False
    
    try:
        engine = create_engine(database_url)
        
        print("=" * 60)
        print("RENDER DATABASE SCHEMA FIX")
        print("=" * 60)
        
        with engine.connect() as conn:
            # Check current rental_history table structure
            print("Checking current rental_history table structure...")
            
            inspector = inspect(engine)
            tables = inspector.get_table_names()
            
            if 'rental_history' not in tables:
                print("rental_history table not found, will be created by Flask app")
                return True
            
            # Get current columns
            columns = inspector.get_columns('rental_history')
            column_names = [col['name'] for col in columns]
            
            print(f"Current columns: {column_names}")
            
            # Expected columns based on our model
            expected_columns = [
                'id', 'customer_id', 'customer_no', 'customer_name', 
                'customer_phone', 'customer_email', 'customer_address',
                'customer_city', 'customer_state', 'cylinder_id', 
                'cylinder_no', 'cylinder_custom_id', 'cylinder_serial',
                'cylinder_type', 'cylinder_size', 'dispatch_date',
                'return_date', 'date_borrowed', 'date_returned',
                'rental_days', 'location', 'status', 'created_at'
            ]
            
            missing_columns = [col for col in expected_columns if col not in column_names]
            
            if missing_columns:
                print(f"Missing columns: {missing_columns}")
                
                # Add missing columns
                for col_name in missing_columns:
                    try:
                        if col_name in ['dispatch_date', 'return_date', 'date_borrowed', 'date_returned', 'created_at']:
                            alter_sql = f"ALTER TABLE rental_history ADD COLUMN IF NOT EXISTS {col_name} TIMESTAMP"
                        elif col_name == 'rental_days':
                            alter_sql = f"ALTER TABLE rental_history ADD COLUMN IF NOT EXISTS {col_name} INTEGER"
                        elif col_name == 'customer_address':
                            alter_sql = f"ALTER TABLE rental_history ADD COLUMN IF NOT EXISTS {col_name} TEXT"
                        else:
                            alter_sql = f"ALTER TABLE rental_history ADD COLUMN IF NOT EXISTS {col_name} VARCHAR"
                        
                        conn.execute(text(alter_sql))
                        print(f"  ✓ Added column: {col_name}")
                        
                    except Exception as e:
                        print(f"  ✗ Failed to add column {col_name}: {e}")
                
                conn.commit()
                print("✓ Schema updates completed")
            else:
                print("✓ All expected columns already exist")
            
            # Test a simple query to ensure everything works
            try:
                result = conn.execute(text("SELECT COUNT(*) FROM rental_history"))
                count = result.scalar()
                print(f"✓ Successfully queried rental_history table: {count} records")
            except Exception as e:
                print(f"✗ Query test failed: {e}")
                return False
            
            print("\n" + "=" * 60)
            print("RENDER DATABASE SCHEMA FIX COMPLETED")
            print("=" * 60)
            
            return True
            
    except Exception as e:
        print(f"Error fixing Render database: {e}")
        return False

def main():
    print("Starting Render database schema fix...")
    
    success = fix_render_database()
    
    if success:
        print("\n🎉 Database schema fix completed successfully!")
        print("Your Render app should now work without schema errors.")
    else:
        print("\n❌ Database schema fix failed!")
        print("Check the error messages above for details.")
        sys.exit(1)

if __name__ == "__main__":
    main()