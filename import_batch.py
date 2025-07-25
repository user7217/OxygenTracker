#!/usr/bin/env python3
"""
Batch Import Script for Varasai Oxygen

This script provides an easy way to import all your data from an MS Access
database in the correct order with proper error handling and progress reporting.

Usage: python import_batch.py your_database.accdb

The script will:
1. Check current data status
2. List available tables 
3. Ask you to confirm table names
4. Import in the correct order (customers -> cylinders -> transactions)
5. Show final summary

Author: Development Team
Date: July 21, 2025
"""

import sys
import os
from standalone_importer import StandaloneImporter

def main():
    """Main batch import process"""
    
    if len(sys.argv) != 2:
        print("Usage: python import_batch.py your_database.accdb")
        print("\nThis script will guide you through importing all your data")
        print("from an MS Access database into the Varasai Oxygen system.")
        sys.exit(1)
    
    access_file = sys.argv[1]
    
    if not os.path.exists(access_file):
        print(f"❌ Access database file not found: {access_file}")
        sys.exit(1)
    
    print("🚀 Varasai Oxygen - Batch Data Import")
    print(f"📁 Database: {access_file}")
    print("=" * 60)
    
    importer = StandaloneImporter()
    
    # Step 1: Show current data status
    print("📊 Current Data Status:")
    print("-" * 30)
    importer.show_current_data_summary()
    
    # Step 2: List available tables
    print(f"\n📋 Available Tables in Database:")
    print("-" * 40)
    importer.list_tables(access_file)
    
    # Step 3: Get table names from user
    print(f"\n💬 Please specify table names for import:")
    print("-" * 45)
    
    customer_table = input("Customer table name (or press Enter to skip): ").strip()
    cylinder_table = input("Cylinder table name (or press Enter to skip): ").strip()
    transaction_table = input("Transaction table name (or press Enter to skip): ").strip()
    
    if not any([customer_table, cylinder_table, transaction_table]):
        print("⚠️  No tables specified. Nothing to import.")
        sys.exit(0)
    
    # Step 4: Confirm and import
    print(f"\n🔄 Import Plan:")
    print("-" * 20)
    if customer_table:
        print(f"   1. Import customers from: {customer_table}")
    if cylinder_table:
        print(f"   2. Import cylinders from: {cylinder_table}")
    if transaction_table:
        print(f"   3. Import transactions from: {transaction_table}")
    
    confirm = input(f"\n❓ Proceed with import? (y/N): ").strip().lower()
    if confirm != 'y' and confirm != 'yes':
        print("❌ Import cancelled by user.")
        sys.exit(0)
    
    print(f"\n🚀 Starting Import Process...")
    print("=" * 40)
    
    # Import in correct order
    success_count = 0
    total_operations = 0
    
    if customer_table:
        total_operations += 1
        print(f"\n👥 Step {total_operations}: Importing Customers...")
        print("-" * 35)
        try:
            importer.import_customers(access_file, customer_table)
            success_count += 1
        except Exception as e:
            print(f"❌ Customer import failed: {e}")
    
    if cylinder_table:
        total_operations += 1
        print(f"\n🏺 Step {total_operations}: Importing Cylinders...")
        print("-" * 35)
        try:
            importer.import_cylinders(access_file, cylinder_table)
            success_count += 1
        except Exception as e:
            print(f"❌ Cylinder import failed: {e}")
    
    if transaction_table:
        total_operations += 1
        print(f"\n🔗 Step {total_operations}: Importing Transactions...")
        print("-" * 40)
        try:
            importer.import_transactions(access_file, transaction_table)
            success_count += 1
        except Exception as e:
            print(f"❌ Transaction import failed: {e}")
    
    # Step 5: Final summary
    print("\n" + "=" * 60)
    print("📊 FINAL IMPORT SUMMARY")
    print("=" * 60)
    
    importer.show_current_data_summary()
    
    print(f"\n🎯 Import Results:")
    print(f"   ✅ Successful operations: {success_count}/{total_operations}")
    print(f"   🆔 All records received unique system IDs")
    print(f"   📝 Original identifiers preserved")
    
    if success_count == total_operations:
        print(f"\n🎉 Import completed successfully!")
        print(f"   Your data is now available in the Varasai Oxygen web application.")
    else:
        print(f"\n⚠️  Import completed with {total_operations - success_count} failures.")
        print(f"   Check the error messages above for details.")
        print(f"   You can re-run the import for failed tables.")
    
    print(f"\n💡 Next Steps:")
    print(f"   • Launch the web application to view your imported data")
    print(f"   • Use the bulk cylinder management features")
    print(f"   • Generate reports and manage rentals")

if __name__ == '__main__':
    main()