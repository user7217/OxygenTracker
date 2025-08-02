#!/usr/bin/env python3
"""
Varasicyl Database Migration Tool
Migrates data from Replit PostgreSQL to Render PostgreSQL

Usage:
python replit_to_render_migrator.py --source "postgresql://..." --target "postgresql://..."

Or set environment variables:
SOURCE_DATABASE_URL=postgresql://...
TARGET_DATABASE_URL=postgresql://...
python replit_to_render_migrator.py
"""

import os
import sys
import json
import argparse
from datetime import datetime
from sqlalchemy import create_engine, text, inspect, and_
from sqlalchemy.exc import SQLAlchemyError

class DatabaseMigrator:
    def __init__(self, source_url, target_url):
        self.source_url = source_url
        self.target_url = target_url
        self.source_engine = None
        self.target_engine = None
        
    def connect(self):
        """Establish connections to both databases"""
        try:
            print("Connecting to source database...")
            self.source_engine = create_engine(self.source_url)
            
            print("Connecting to target database...")
            self.target_engine = create_engine(self.target_url)
            
            # Test connections
            with self.source_engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            print("✓ Source database connection successful")
            
            with self.target_engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            print("✓ Target database connection successful")
            
            return True
        except Exception as e:
            print(f"✗ Connection failed: {e}")
            return False
    
    def verify_schema(self):
        """Verify that both databases have the required tables"""
        required_tables = ['customers', 'cylinders', 'rental_history']
        
        try:
            # Check source tables
            source_inspector = inspect(self.source_engine)
            source_tables = source_inspector.get_table_names()
            
            # Check target tables  
            target_inspector = inspect(self.target_engine)
            target_tables = target_inspector.get_table_names()
            
            print(f"Source tables: {source_tables}")
            print(f"Target tables: {target_tables}")
            
            missing_source = [t for t in required_tables if t not in source_tables]
            missing_target = [t for t in required_tables if t not in target_tables]
            
            if missing_source:
                print(f"✗ Missing tables in source: {missing_source}")
                return False
                
            if missing_target:
                print(f"✗ Missing tables in target: {missing_target}")
                return False
                
            print("✓ All required tables found in both databases")
            return True
            
        except Exception as e:
            print(f"✗ Schema verification failed: {e}")
            return False
    
    def get_table_data(self, table_name):
        """Get all data from a table in the source database"""
        try:
            with self.source_engine.connect() as conn:
                query = text(f"SELECT * FROM {table_name}")
                result = conn.execute(query)
                columns = result.keys()
                records = [dict(zip(columns, row)) for row in result.fetchall()]
                print(f"✓ Retrieved {len(records)} records from {table_name}")
                return records
        except Exception as e:
            print(f"✗ Failed to get data from {table_name}: {e}")
            return []
    
    def clear_table(self, table_name):
        """Clear all data from a table in the target database"""
        try:
            with self.target_engine.connect() as conn:
                # Handle foreign key constraints by clearing in proper order
                if table_name == 'customers':
                    # First clear dependent tables
                    conn.execute(text("DELETE FROM rental_history"))
                    conn.execute(text("UPDATE cylinders SET rented_to = NULL WHERE rented_to IS NOT NULL"))
                    conn.execute(text("DELETE FROM customers"))
                elif table_name == 'cylinders':
                    conn.execute(text("DELETE FROM rental_history"))
                    conn.execute(text("DELETE FROM cylinders"))
                elif table_name == 'rental_history':
                    conn.execute(text("DELETE FROM rental_history"))
                
                conn.commit()
                print(f"✓ Cleared {table_name} table")
                return True
        except Exception as e:
            print(f"✗ Failed to clear {table_name}: {e}")
            return False
    
    def insert_data(self, table_name, records):
        """Insert records into target database table"""
        if not records:
            print(f"No records to insert for {table_name}")
            return True
            
        try:
            with self.target_engine.connect() as conn:
                # Convert None values and handle data types
                processed_records = []
                for record in records:
                    processed_record = {}
                    for key, value in record.items():
                        # Convert datetime objects to strings
                        if hasattr(value, 'isoformat'):
                            processed_record[key] = value.isoformat()
                        else:
                            processed_record[key] = value
                    
                    # Handle rental_history specific NULL constraints
                    if table_name == 'rental_history':
                        # If cylinder_id is NULL, use cylinder_no or generate a placeholder
                        if not processed_record.get('cylinder_id'):
                            if processed_record.get('cylinder_no'):
                                processed_record['cylinder_id'] = f"CYL-{processed_record['cylinder_no']}"
                            else:
                                processed_record['cylinder_id'] = f"MIGRATED-{processed_record.get('id', 'UNKNOWN')}"
                        
                        # If customer_id is NULL, use customer_no or generate a placeholder
                        if not processed_record.get('customer_id'):
                            if processed_record.get('customer_no'):
                                processed_record['customer_id'] = f"CUST-{processed_record['customer_no']}"
                            else:
                                processed_record['customer_id'] = f"MIGRATED-{processed_record.get('id', 'UNKNOWN')}"
                        
                        # Ensure required fields have non-NULL values
                        if not processed_record.get('customer_name'):
                            processed_record['customer_name'] = 'Unknown Customer'
                        if not processed_record.get('cylinder_type'):
                            processed_record['cylinder_type'] = 'Unknown Type'
                        if not processed_record.get('cylinder_size'):
                            processed_record['cylinder_size'] = 'Unknown Size'
                        if not processed_record.get('location'):
                            processed_record['location'] = 'Unknown Location'
                        if not processed_record.get('status'):
                            processed_record['status'] = 'completed'
                    
                    processed_records.append(processed_record)
                
                # Build insert statement
                if processed_records:
                    columns = list(processed_records[0].keys())
                    placeholders = ', '.join([f":{col}" for col in columns])
                    query = text(f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({placeholders})")
                    
                    # Insert in large batches for maximum speed
                    batch_size = 1000  # Large batch size for local execution
                    total_inserted = 0
                    
                    # Try to insert all records at once for maximum speed
                    try:
                        conn.execute(query, processed_records)
                        total_inserted = len(processed_records)
                        print(f"  ✓ Bulk inserted all {total_inserted} records")
                    except Exception as bulk_error:
                        print(f"  Bulk insert failed, using batches...")
                        # Fall back to batch processing
                        for i in range(0, len(processed_records), batch_size):
                            batch = processed_records[i:i + batch_size]
                            try:
                                conn.execute(query, batch)
                                total_inserted += len(batch)
                                if i % (batch_size * 5) == 0:  # Progress every 5000 records
                                    print(f"  → {total_inserted}/{len(processed_records)} records")
                            except Exception as batch_error:
                                # Try smaller batches or individual inserts
                                print(f"  Large batch failed, trying smaller batches...")
                                for j in range(i, min(i + batch_size, len(processed_records)), 100):
                                    small_batch = processed_records[j:j + 100]
                                    try:
                                        conn.execute(query, small_batch)
                                        total_inserted += len(small_batch)
                                    except Exception as small_error:
                                        # Last resort: individual inserts
                                        for single_record in small_batch:
                                            try:
                                                conn.execute(query, [single_record])
                                                total_inserted += 1
                                            except Exception as single_error:
                                                print(f"  ✗ Failed record {single_record.get('id', 'unknown')}: {single_error}")
                    
                    conn.commit()
                    print(f"✓ Successfully inserted {total_inserted} records into {table_name}")
                    return True
                    
        except Exception as e:
            print(f"✗ Failed to insert data into {table_name}: {e}")
            return False
    
    def create_backup(self, filename=None):
        """Create a backup of all source data"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"replit_backup_{timestamp}.json"
        
        backup_data = {}
        tables = ['customers', 'cylinders', 'rental_history']
        
        try:
            for table in tables:
                records = self.get_table_data(table)
                # Convert datetime objects to strings for JSON serialization
                json_records = []
                for record in records:
                    json_record = {}
                    for key, value in record.items():
                        if hasattr(value, 'isoformat'):
                            json_record[key] = value.isoformat()
                        else:
                            json_record[key] = value
                    json_records.append(json_record)
                backup_data[table] = json_records
            
            with open(filename, 'w') as f:
                json.dump(backup_data, f, indent=2, default=str)
            
            print(f"✓ Complete backup created: {filename}")
            return filename
            
        except Exception as e:
            print(f"✗ Backup failed: {e}")
            return None
    
    def create_rental_history_backup(self, filename=None):
        """Create a backup of rental history data only"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"rental_history_backup_{timestamp}.json"
        
        try:
            records = self.get_table_data('rental_history')
            # Convert datetime objects to strings for JSON serialization
            json_records = []
            for record in records:
                json_record = {}
                for key, value in record.items():
                    if hasattr(value, 'isoformat'):
                        json_record[key] = value.isoformat()
                    else:
                        json_record[key] = value
                json_records.append(json_record)
            
            backup_data = {
                'rental_history': json_records,
                'backup_info': {
                    'created_at': datetime.now().isoformat(),
                    'record_count': len(json_records),
                    'backup_type': 'rental_history_only'
                }
            }
            
            with open(filename, 'w') as f:
                json.dump(backup_data, f, indent=2, default=str)
            
            print(f"✓ Rental history backup created: {filename}")
            return filename
            
        except Exception as e:
            print(f"✗ Rental history backup failed: {e}")
            return None
    
    def migrate_rental_history_only(self, create_backup=True):
        """Migrate only rental history data (skip customers and cylinders)"""
        print("=" * 60)
        print("VARASICYL RENTAL HISTORY MIGRATION")
        print("(Customers and Cylinders tables will be preserved)")
        print("=" * 60)
        
        # Step 1: Connect to databases
        if not self.connect():
            return False
        
        # Step 2: Verify that rental_history table exists in both databases
        required_tables = ['rental_history']
        try:
            source_inspector = inspect(self.source_engine)
            target_inspector = inspect(self.target_engine)
            
            source_tables = source_inspector.get_table_names()
            target_tables = target_inspector.get_table_names()
            
            if 'rental_history' not in source_tables:
                print("✗ rental_history table not found in source database")
                return False
            
            if 'rental_history' not in target_tables:
                print("✗ rental_history table not found in target database")
                return False
                
            print("✓ rental_history table found in both databases")
            
        except Exception as e:
            print(f"✗ Table verification failed: {e}")
            return False
        
        # Step 3: Create backup of rental history only
        if create_backup:
            print("\nCreating rental history backup...")
            backup_file = self.create_rental_history_backup()
            if backup_file:
                print(f"✓ Backup created: {backup_file}")
            else:
                print("Backup failed, but continuing with migration...")
        
        # Step 4: Migrate rental history data only
        print(f"\nStarting rental history migration...")
        print(f"\n--- Migrating rental_history ---")
        
        # Get source data
        records = self.get_table_data('rental_history')
        if records:
            print(f"Found {len(records)} rental history records to migrate")
            
            # Clear target rental_history table only
            if not self.clear_table('rental_history'):
                print(f"Failed to clear rental_history table, aborting migration")
                return False
            
            # Insert data
            if not self.insert_data('rental_history', records):
                print(f"Failed to insert rental history data, aborting migration")
                return False
        else:
            print(f"No rental history data found in source database")
        
        print("\n" + "=" * 60)
        print("RENTAL HISTORY MIGRATION COMPLETED SUCCESSFULLY!")
        print("Customer and cylinder data preserved.")
        print("=" * 60)
        
        # Step 5: Verify migration
        print("\nVerifying migration...")
        with self.target_engine.connect() as conn:
            # Check rental_history count
            result = conn.execute(text(f"SELECT COUNT(*) FROM rental_history"))
            rental_count = result.scalar()
            print(f"  rental_history: {rental_count} records")
            
            # Check that other tables are preserved
            for table in ['customers', 'cylinders']:
                try:
                    result = conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
                    count = result.scalar()
                    print(f"  {table}: {count} records (preserved)")
                except:
                    print(f"  {table}: table not found (skipped)")
        
        return True
    
    def migrate_all(self, create_backup=True):
        """Perform complete migration (all tables)"""
        print("=" * 60)
        print("VARASICYL COMPLETE DATABASE MIGRATION")
        print("=" * 60)
        
        # Step 1: Connect to databases
        if not self.connect():
            return False
        
        # Step 2: Verify schema
        if not self.verify_schema():
            return False
        
        # Step 3: Create backup
        if create_backup:
            print("\nCreating complete backup...")
            backup_file = self.create_backup()
            if not backup_file:
                print("Backup failed, but continuing with migration...")
        
        # Step 4: Migrate data in correct order (handle foreign keys)
        tables_order = ['customers', 'cylinders', 'rental_history']
        
        print(f"\nStarting complete migration...")
        for table in tables_order:
            print(f"\n--- Migrating {table} ---")
            
            # Get source data
            records = self.get_table_data(table)
            if records:
                # Clear target table
                if not self.clear_table(table):
                    print(f"Failed to clear {table}, aborting migration")
                    return False
                
                # Insert data
                if not self.insert_data(table, records):
                    print(f"Failed to insert data into {table}, aborting migration")
                    return False
            else:
                print(f"No data found in {table}")
        
        print("\n" + "=" * 60)
        print("COMPLETE MIGRATION COMPLETED SUCCESSFULLY!")
        print("=" * 60)
        
        # Step 5: Verify migration
        print("\nVerifying migration...")
        with self.target_engine.connect() as conn:
            for table in tables_order:
                result = conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
                count = result.scalar()
                print(f"  {table}: {count} records")
        
        return True

def main():
    parser = argparse.ArgumentParser(description='Migrate Varasicyl data from Replit to Render')
    parser.add_argument('--source', help='Source database URL (Replit)')
    parser.add_argument('--target', help='Target database URL (Render)')
    parser.add_argument('--no-backup', action='store_true', help='Skip creating backup')
    parser.add_argument('--rental-history-only', action='store_true', 
                       help='Migrate only rental history data (preserve customers and cylinders)')
    parser.add_argument('--complete', action='store_true', 
                       help='Migrate all data (customers, cylinders, and rental history)')
    
    args = parser.parse_args()
    
    # Get database URLs
    source_url = args.source or os.environ.get('SOURCE_DATABASE_URL')
    target_url = args.target or os.environ.get('DATABASE_URL') or os.environ.get('TARGET_DATABASE_URL')
    
    if not source_url:
        print("Error: Source database URL not provided")
        print("Use --source argument or set SOURCE_DATABASE_URL environment variable")
        sys.exit(1)
    
    if not target_url:
        print("Error: Target database URL not provided")
        print("Use --target argument or set DATABASE_URL or TARGET_DATABASE_URL environment variable")
        sys.exit(1)
    
    print(f"Source: {source_url[:20]}...")
    print(f"Target: {target_url[:20]}...")
    
    # Determine migration type
    if args.rental_history_only and args.complete:
        print("Error: Cannot specify both --rental-history-only and --complete")
        sys.exit(1)
    
    migration_type = "rental history only"
    if args.complete:
        migration_type = "complete database"
    elif not args.rental_history_only:
        # Default behavior: ask user what they want
        print("\nMigration options:")
        print("1. Rental history only (preserve existing customers and cylinders)")
        print("2. Complete database (overwrite all data)")
        choice = input("Choose migration type (1 or 2): ").strip()
        
        if choice == "2":
            args.complete = True
            migration_type = "complete database"
        else:
            args.rental_history_only = True
            migration_type = "rental history only"
    
    # Confirm migration
    warning_msg = (
        f"\nThis will perform a {migration_type} migration."
        f"\n{'All data will be overwritten' if args.complete else 'Only rental history will be overwritten. Customers and cylinders will be preserved'}."
        f"\nContinue? (yes/no): "
    )
    response = input(warning_msg)
    if response.lower() not in ['yes', 'y']:
        print("Migration cancelled")
        sys.exit(0)
    
    # Perform migration
    migrator = DatabaseMigrator(source_url, target_url)
    
    if args.rental_history_only:
        success = migrator.migrate_rental_history_only(create_backup=not args.no_backup)
        success_msg = "Rental history migration completed successfully!"
        error_msg = "Rental history migration failed!"
    else:
        success = migrator.migrate_all(create_backup=not args.no_backup)
        success_msg = "Complete migration completed successfully!"
        error_msg = "Complete migration failed!"
    
    if success:
        print(f"\n🎉 {success_msg}")
        if args.rental_history_only:
            print("Your rental history has been transferred. Customer and cylinder data preserved.")
        else:
            print("Your Replit data has been transferred to Render.")
    else:
        print(f"\n❌ {error_msg}")
        print("Check the error messages above for details.")
        sys.exit(1)

if __name__ == "__main__":
    main()