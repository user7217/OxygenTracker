#!/usr/bin/env python3
"""
Standalone Data Importer for Varasai Oxygen Cylinder Tracker

This script provides command-line access to the same data import functionality
as the web application. It can import customers, cylinders, and transactions
from MS Access databases with the same field mapping and validation logic.

Usage:
    python standalone_importer.py import_customers access_file.accdb table_name
    python standalone_importer.py import_cylinders access_file.accdb table_name
    python standalone_importer.py import_transactions access_file.accdb table_name
    python standalone_importer.py list_tables access_file.accdb

Requirements:
    - pyodbc (for MS Access connectivity)
    - pandas (for data processing)
    - Same data directory structure as main application

Author: Development Team
Date: July 21, 2025
"""

import os
import sys
import json
import argparse
from datetime import datetime
from typing import List, Dict, Optional, Any

# Import the same models and utilities from the main application
from models import Customer, Cylinder, JSONDatabase
from access_connector import AccessConnector


class StandaloneImporter:
    """Standalone data importer with same functionality as web application"""
    
    def __init__(self):
        """Initialize importer with models"""
        self.customer_model = Customer()
        self.cylinder_model = Cylinder()
        self.access_connector = None
    
    def connect_to_access(self, access_file: str) -> bool:
        """Connect to MS Access database file"""
        try:
            self.access_connector = AccessConnector(access_file)
            return True
        except Exception as e:
            print(f"❌ Failed to connect to Access database: {e}")
            return False
    
    def list_tables(self, access_file: str) -> None:
        """List all tables in the Access database"""
        if not self.connect_to_access(access_file):
            return
        
        try:
            tables = self.access_connector.get_tables()
            print(f"📋 Tables in {access_file}:")
            for i, table in enumerate(tables, 1):
                print(f"  {i}. {table}")
            print(f"\n💡 Use preview_table command to examine table structure before importing")
        except Exception as e:
            print(f"❌ Error listing tables: {e}")
    
    def show_current_data_summary(self) -> None:
        """Show summary of current data in the system"""
        try:
            customers = self.customer_model.get_all()
            cylinders = self.cylinder_model.get_all()
            
            print(f"📊 Current Data Summary:")
            print(f"   👥 Total Customers: {len(customers)}")
            print(f"   🏺 Total Cylinders: {len(cylinders)}")
            
            # Show cylinder status breakdown
            available = len([c for c in cylinders if c.get('status', '').lower() == 'available'])
            rented = len([c for c in cylinders if c.get('status', '').lower() == 'rented'])
            maintenance = len([c for c in cylinders if c.get('status', '').lower() == 'maintenance'])
            
            print(f"   📈 Cylinder Status:")
            print(f"      🟢 Available: {available}")
            print(f"      🔴 Rented: {rented}")
            print(f"      🟡 Maintenance: {maintenance}")
            
        except Exception as e:
            print(f"❌ Error getting data summary: {e}")
    
    def preview_table(self, access_file: str, table_name: str, limit: int = 5) -> None:
        """Preview table structure and data"""
        if not self.connect_to_access(access_file):
            return
        
        try:
            # Get table structure
            columns = self.access_connector.get_table_columns(table_name)
            print(f"📋 Table Structure for '{table_name}':")
            for i, col in enumerate(columns, 1):
                print(f"  {i}. {col}")
            
            # Preview data
            preview_data = self.access_connector.get_table_data(table_name, limit=limit)
            if preview_data:
                print(f"\n📊 Preview Data (first {limit} rows):")
                for i, row in enumerate(preview_data, 1):
                    print(f"  Row {i}: {dict(row)}")
            else:
                print("\n📊 No data found in table")
                
        except Exception as e:
            print(f"❌ Error previewing table: {e}")
    
    def import_customers(self, access_file: str, table_name: str, field_mapping: Dict[str, str] = None) -> None:
        """Import customers from Access database with field mapping"""
        if not self.connect_to_access(access_file):
            return
        
        try:
            # Default field mapping for customers
            if not field_mapping:
                field_mapping = self._get_default_customer_mapping()
            
            print(f"🔄 Starting customer import from '{table_name}'...")
            
            # Get all data from table
            data = self.access_connector.get_table_data(table_name)
            
            imported_count = 0
            duplicate_count = 0
            error_count = 0
            
            for row_data in data:
                try:
                    # Map fields according to mapping
                    customer_data = self._map_customer_fields(dict(row_data), field_mapping)
                    
                    # Check for duplicates
                    existing_customers = self.customer_model.get_all()
                    is_duplicate = self._check_customer_duplicate(customer_data, existing_customers)
                    
                    if is_duplicate:
                        duplicate_count += 1
                        print(f"⚠️  Skipping duplicate customer: {customer_data.get('customer_name', 'Unknown')}")
                        continue
                    
                    # Add customer (this will generate a proper unique ID)
                    added_customer = self.customer_model.add(customer_data)
                    imported_count += 1
                    customer_id = added_customer.get('id', 'Unknown')
                    customer_name = customer_data.get('customer_name', 'Unknown')
                    print(f"✅ Imported customer: {customer_name} (ID: {customer_id})")
                    
                except Exception as e:
                    error_count += 1
                    print(f"❌ Error importing customer row: {e}")
            
            print(f"\n📊 Customer Import Summary:")
            print(f"   ✅ Successfully imported: {imported_count}")
            print(f"   ⚠️  Duplicates skipped: {duplicate_count}")
            print(f"   ❌ Errors: {error_count}")
            print(f"   🆔 Each customer received a unique system ID (CUST-XXXXXXXX format)")
            
        except Exception as e:
            print(f"❌ Error during customer import: {e}")
    
    def import_cylinders(self, access_file: str, table_name: str, field_mapping: Dict[str, str] = None) -> None:
        """Import cylinders from Access database with field mapping"""
        if not self.connect_to_access(access_file):
            return
        
        try:
            # Default field mapping for cylinders
            if not field_mapping:
                field_mapping = self._get_default_cylinder_mapping()
            
            print(f"🔄 Starting cylinder import from '{table_name}'...")
            
            # Get all data from table
            data = self.access_connector.get_table_data(table_name)
            
            imported_count = 0
            duplicate_count = 0
            error_count = 0
            
            for row_data in data:
                try:
                    # Map fields according to mapping
                    cylinder_data = self._map_cylinder_fields(dict(row_data), field_mapping)
                    
                    # Check for duplicates
                    existing_cylinders = self.cylinder_model.get_all()
                    is_duplicate = self._check_cylinder_duplicate(cylinder_data, existing_cylinders)
                    
                    if is_duplicate:
                        duplicate_count += 1
                        print(f"⚠️  Skipping duplicate cylinder: {cylinder_data.get('serial_number', 'Unknown')}")
                        continue
                    
                    # Add cylinder (this will generate a proper unique ID)
                    added_cylinder = self.cylinder_model.add(cylinder_data)
                    imported_count += 1
                    cylinder_id = added_cylinder.get('id', 'Unknown')
                    serial_number = cylinder_data.get('serial_number', 'Unknown')
                    custom_id = cylinder_data.get('custom_id', '')
                    display_id = custom_id if custom_id else serial_number
                    print(f"✅ Imported cylinder: {display_id} (System ID: {cylinder_id})")
                    
                except Exception as e:
                    error_count += 1
                    print(f"❌ Error importing cylinder row: {e}")
            
            print(f"\n📊 Cylinder Import Summary:")
            print(f"   ✅ Successfully imported: {imported_count}")
            print(f"   ⚠️  Duplicates skipped: {duplicate_count}")
            print(f"   ❌ Errors: {error_count}")
            print(f"   🆔 Each cylinder received a unique system ID (CYL-XXXXXXXX format)")
            print(f"   📝 Custom IDs and serial numbers preserved for easy identification")
            
        except Exception as e:
            print(f"❌ Error during cylinder import: {e}")
    
    def import_transactions(self, access_file: str, table_name: str, field_mapping: Dict[str, str] = None) -> None:
        """Import transactions from Access database linking customers and cylinders"""
        if not self.connect_to_access(access_file):
            return
        
        try:
            # Default field mapping for transactions
            if not field_mapping:
                field_mapping = self._get_default_transaction_mapping()
            
            print(f"🔄 Starting transaction import from '{table_name}'...")
            
            # Get all data from table
            data = self.access_connector.get_table_data(table_name)
            
            # Load existing customers and cylinders for lookup
            customers = self.customer_model.get_all()
            cylinders = self.cylinder_model.get_all()
            
            # Create lookup dictionaries
            customer_lookup = {c.get('customer_no', ''): c for c in customers}
            cylinder_lookup = {c.get('serial_number', ''): c for c in cylinders}
            
            imported_count = 0
            error_count = 0
            
            for row_data in data:
                try:
                    # Map fields according to mapping
                    transaction_data = self._map_transaction_fields(dict(row_data), field_mapping)
                    
                    # Process transaction (rent/return cylinder)
                    success = self._process_transaction(transaction_data, customer_lookup, cylinder_lookup)
                    
                    if success:
                        imported_count += 1
                        print(f"✅ Processed transaction: {transaction_data.get('customer_no', 'Unknown')} -> {transaction_data.get('cylinder_no', 'Unknown')}")
                    else:
                        error_count += 1
                    
                except Exception as e:
                    error_count += 1
                    print(f"❌ Error processing transaction row: {e}")
            
            print(f"\n📊 Transaction Import Summary:")
            print(f"   ✅ Successfully processed: {imported_count}")
            print(f"   ❌ Errors: {error_count}")
            
        except Exception as e:
            print(f"❌ Error during transaction import: {e}")
    
    def _get_default_customer_mapping(self) -> Dict[str, str]:
        """Get default field mapping for customers"""
        return {
            'customer_no': 'customer_no',
            'customer_name': 'customer_name', 
            'customer_address': 'customer_address',
            'customer_city': 'customer_city',
            'customer_state': 'customer_state',
            'customer_phone': 'customer_phone',
            'customer_apgst': 'customer_apgst',
            'customer_cst': 'customer_cst',
            'customer_email': 'customer_email'
        }
    
    def _get_default_cylinder_mapping(self) -> Dict[str, str]:
        """Get default field mapping for cylinders"""
        return {
            'serial_number': 'serial_number',
            'type': 'type',
            'size': 'size',
            'location': 'location',
            'status': 'status',
            'custom_id': 'custom_id'
        }
    
    def _get_default_transaction_mapping(self) -> Dict[str, str]:
        """Get default field mapping for transactions"""
        return {
            'customer_no': 'customer_no',
            'cylinder_no': 'cylinder_no',
            'rental_date': 'rental_date',
            'return_date': 'return_date'
        }
    
    def _map_customer_fields(self, row_data: Dict, mapping: Dict[str, str]) -> Dict[str, Any]:
        """Map Access database fields to customer model fields"""
        customer_data = {}
        
        for model_field, access_field in mapping.items():
            if access_field in row_data and row_data[access_field] is not None:
                customer_data[model_field] = str(row_data[access_field]).strip()
        
        # Set defaults for missing fields
        customer_data.setdefault('customer_email', '')
        
        # Generate unique ID (will be overridden by model.add() but good to have)
        customer_data['id'] = self.customer_model.generate_id()
        customer_data['created_at'] = datetime.now().isoformat()
        customer_data['updated_at'] = datetime.now().isoformat()
        
        return customer_data
    
    def _map_cylinder_fields(self, row_data: Dict, mapping: Dict[str, str]) -> Dict[str, Any]:
        """Map Access database fields to cylinder model fields"""
        cylinder_data = {}
        
        for model_field, access_field in mapping.items():
            if access_field in row_data and row_data[access_field] is not None:
                cylinder_data[model_field] = str(row_data[access_field]).strip()
        
        # Set defaults for missing fields
        cylinder_data.setdefault('location', 'Warehouse')
        cylinder_data.setdefault('status', 'Available')
        cylinder_data.setdefault('type', 'Medical Oxygen')
        cylinder_data.setdefault('custom_id', '')
        
        # Generate unique ID (will be overridden by model.add() but good to have)
        cylinder_data['id'] = self.cylinder_model.generate_id()
        cylinder_data['created_at'] = datetime.now().isoformat()
        cylinder_data['updated_at'] = datetime.now().isoformat()
        
        return cylinder_data
    
    def _map_transaction_fields(self, row_data: Dict, mapping: Dict[str, str]) -> Dict[str, Any]:
        """Map Access database fields to transaction fields"""
        transaction_data = {}
        
        for model_field, access_field in mapping.items():
            if access_field in row_data and row_data[access_field] is not None:
                value = row_data[access_field]
                # Handle date fields
                if 'date' in model_field.lower() and value:
                    try:
                        # Convert to datetime if it's not already
                        if isinstance(value, str):
                            transaction_data[model_field] = datetime.strptime(value, '%Y-%m-%d').isoformat()
                        else:
                            transaction_data[model_field] = value.isoformat()
                    except:
                        transaction_data[model_field] = str(value)
                else:
                    transaction_data[model_field] = str(value).strip()
        
        return transaction_data
    
    def _check_customer_duplicate(self, customer_data: Dict, existing_customers: List[Dict]) -> bool:
        """Check if customer already exists"""
        customer_no = customer_data.get('customer_no', '')
        customer_name = customer_data.get('customer_name', '')
        customer_phone = customer_data.get('customer_phone', '')
        
        for existing in existing_customers:
            if (customer_no and existing.get('customer_no') == customer_no) or \
               (customer_name and existing.get('customer_name') == customer_name) or \
               (customer_phone and existing.get('customer_phone') == customer_phone):
                return True
        
        return False
    
    def _check_cylinder_duplicate(self, cylinder_data: Dict, existing_cylinders: List[Dict]) -> bool:
        """Check if cylinder already exists"""
        serial_number = cylinder_data.get('serial_number', '')
        custom_id = cylinder_data.get('custom_id', '')
        
        for existing in existing_cylinders:
            if (serial_number and existing.get('serial_number') == serial_number) or \
               (custom_id and existing.get('custom_id') == custom_id):
                return True
        
        return False
    
    def _process_transaction(self, transaction_data: Dict, customer_lookup: Dict, cylinder_lookup: Dict) -> bool:
        """Process transaction by linking customer and cylinder"""
        try:
            customer_no = transaction_data.get('customer_no', '')
            cylinder_no = transaction_data.get('cylinder_no', '')
            rental_date = transaction_data.get('rental_date')
            return_date = transaction_data.get('return_date')
            
            # Find customer and cylinder
            customer = customer_lookup.get(customer_no)
            cylinder = None
            
            # Try to find cylinder by different identifiers
            for cyl in cylinder_lookup.values():
                if (cyl.get('serial_number') == cylinder_no or 
                    cyl.get('custom_id') == cylinder_no or
                    cyl.get('id') == cylinder_no):
                    cylinder = cyl
                    break
            
            if not customer:
                print(f"⚠️  Customer not found: {customer_no}")
                return False
            
            if not cylinder:
                print(f"⚠️  Cylinder not found: {cylinder_no}")
                return False
            
            # Update cylinder with rental information
            if return_date:
                # Cylinder was returned
                cylinder['status'] = 'Available'
                cylinder['location'] = 'Warehouse'
                cylinder['rented_to'] = None
                cylinder['rental_date'] = None
                cylinder['return_date'] = return_date
            else:
                # Cylinder is rented
                cylinder['status'] = 'Rented'
                cylinder['rented_to'] = customer['id']
                cylinder['rental_date'] = rental_date
                cylinder['location'] = customer.get('customer_address', 'Customer Location')
                cylinder['customer_name'] = customer.get('customer_name', '')
                cylinder['customer_phone'] = customer.get('customer_phone', '')
                cylinder['return_date'] = None
            
            # Update cylinder in database
            self.cylinder_model.update(cylinder['id'], cylinder)
            return True
            
        except Exception as e:
            print(f"❌ Error processing transaction: {e}")
            return False


def main():
    """Main function for command-line interface"""
    parser = argparse.ArgumentParser(
        description="Standalone Data Importer for Varasai Oxygen Cylinder Tracker",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python standalone_importer.py list_tables database.accdb
  python standalone_importer.py preview_table database.accdb Customers
  python standalone_importer.py import_customers database.accdb Customers
  python standalone_importer.py import_cylinders database.accdb Cylinders
  python standalone_importer.py import_transactions database.accdb Transactions
        """
    )
    
    parser.add_argument('command', choices=['list_tables', 'preview_table', 'import_customers', 'import_cylinders', 'import_transactions', 'show_summary'],
                       help='Command to execute')
    parser.add_argument('access_file', help='Path to MS Access database file (.accdb)')
    parser.add_argument('table_name', nargs='?', help='Table name (required for all commands except list_tables)')
    parser.add_argument('--limit', type=int, default=5, help='Number of rows to preview (default: 5)')
    
    args = parser.parse_args()
    
    # Validate arguments
    if args.command not in ['list_tables', 'show_summary'] and not args.table_name:
        parser.error(f"table_name is required for command '{args.command}'")
    
    if not os.path.exists(args.access_file):
        print(f"❌ Access database file not found: {args.access_file}")
        sys.exit(1)
    
    # Initialize importer
    importer = StandaloneImporter()
    
    # Execute command
    print(f"🚀 Varasai Oxygen - Standalone Data Importer")
    print(f"📁 Database: {args.access_file}")
    print("=" * 50)
    
    if args.command == 'list_tables':
        importer.list_tables(args.access_file)
    
    elif args.command == 'preview_table':
        importer.preview_table(args.access_file, args.table_name, args.limit)
    
    elif args.command == 'import_customers':
        importer.import_customers(args.access_file, args.table_name)
    
    elif args.command == 'import_cylinders':
        importer.import_cylinders(args.access_file, args.table_name)
    
    elif args.command == 'import_transactions':
        importer.import_transactions(args.access_file, args.table_name)
    
    elif args.command == 'show_summary':
        importer.show_current_data_summary()
    
    print("\n✨ Import process completed!")


if __name__ == '__main__':
    main()