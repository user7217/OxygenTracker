#!/usr/bin/env python3
"""
Database Reset Utility for Varasai Oxygen System

This script provides functionality to completely wipe customer and cylinder databases.
Use with caution - this action cannot be undone!

Usage:
    python reset_database.py --customers    # Reset only customers
    python reset_database.py --cylinders    # Reset only cylinders  
    python reset_database.py --all          # Reset both databases
    python reset_database.py --backup       # Create backup before reset
"""

import json
import os
import sys
import argparse
from datetime import datetime
from typing import Dict, List


class DatabaseResetter:
    """Utility class for resetting database files safely"""
    
    def __init__(self):
        """Initialize the database resetter"""
        self.data_dir = "data"
        self.customers_file = os.path.join(self.data_dir, "customers.json")
        self.cylinders_file = os.path.join(self.data_dir, "cylinders.json")
        self.users_file = os.path.join(self.data_dir, "users.json")
        
        # Ensure data directory exists
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
    
    def create_backup(self, backup_customers: bool = True, backup_cylinders: bool = True) -> Dict[str, str]:
        """
        Create backup files before resetting
        Returns dictionary with backup file paths
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_files = {}
        
        if backup_customers and os.path.exists(self.customers_file):
            backup_path = os.path.join(self.data_dir, f"customers_backup_{timestamp}.json")
            try:
                with open(self.customers_file, 'r') as source:
                    with open(backup_path, 'w') as backup:
                        backup.write(source.read())
                backup_files['customers'] = backup_path
                print(f"✓ Customer backup created: {backup_path}")
            except Exception as e:
                print(f"⚠ Failed to backup customers: {e}")
        
        if backup_cylinders and os.path.exists(self.cylinders_file):
            backup_path = os.path.join(self.data_dir, f"cylinders_backup_{timestamp}.json")
            try:
                with open(self.cylinders_file, 'r') as source:
                    with open(backup_path, 'w') as backup:
                        backup.write(source.read())
                backup_files['cylinders'] = backup_path
                print(f"✓ Cylinder backup created: {backup_path}")
            except Exception as e:
                print(f"⚠ Failed to backup cylinders: {e}")
        
        return backup_files
    
    def reset_customers(self, create_backup: bool = True) -> bool:
        """
        Reset the customers database to empty state
        Optionally creates backup before reset
        """
        try:
            if create_backup:
                self.create_backup(backup_customers=True, backup_cylinders=False)
            
            # Write empty customer database
            empty_customers = []
            with open(self.customers_file, 'w') as f:
                json.dump(empty_customers, f, indent=2)
            
            print(f"✓ Customer database reset successfully")
            print(f"  File: {self.customers_file}")
            print(f"  Records removed: All customer data cleared")
            return True
            
        except Exception as e:
            print(f"✗ Failed to reset customers database: {e}")
            return False
    
    def reset_cylinders(self, create_backup: bool = True) -> bool:
        """
        Reset the cylinders database to empty state
        Optionally creates backup before reset
        """
        try:
            if create_backup:
                self.create_backup(backup_customers=False, backup_cylinders=True)
            
            # Write empty cylinder database
            empty_cylinders = []
            with open(self.cylinders_file, 'w') as f:
                json.dump(empty_cylinders, f, indent=2)
            
            print(f"✓ Cylinder database reset successfully")
            print(f"  File: {self.cylinders_file}")
            print(f"  Records removed: All cylinder data cleared")
            return True
            
        except Exception as e:
            print(f"✗ Failed to reset cylinders database: {e}")
            return False
    
    def reset_all(self, create_backup: bool = True) -> bool:
        """
        Reset both customer and cylinder databases
        Optionally creates backup before reset
        """
        try:
            if create_backup:
                self.create_backup(backup_customers=True, backup_cylinders=True)
            
            success = True
            success &= self.reset_customers(create_backup=False)  # Backup already created
            success &= self.reset_cylinders(create_backup=False)  # Backup already created
            
            if success:
                print(f"\n✓ Complete database reset successful!")
                print(f"  Both customer and cylinder databases have been cleared")
            else:
                print(f"\n⚠ Database reset completed with some errors")
            
            return success
            
        except Exception as e:
            print(f"✗ Failed to reset databases: {e}")
            return False
    
    def get_database_stats(self) -> Dict[str, int]:
        """Get current database statistics"""
        stats = {}
        
        try:
            if os.path.exists(self.customers_file):
                with open(self.customers_file, 'r') as f:
                    customers = json.load(f)
                    stats['customers'] = len(customers)
            else:
                stats['customers'] = 0
        except:
            stats['customers'] = 0
        
        try:
            if os.path.exists(self.cylinders_file):
                with open(self.cylinders_file, 'r') as f:
                    cylinders = json.load(f)
                    stats['cylinders'] = len(cylinders)
            else:
                stats['cylinders'] = 0
        except:
            stats['cylinders'] = 0
        
        return stats
    
    def show_database_info(self):
        """Display current database information"""
        stats = self.get_database_stats()
        
        print("═" * 50)
        print("DATABASE STATUS")
        print("═" * 50)
        print(f"Customers: {stats['customers']} records")
        print(f"Cylinders: {stats['cylinders']} records")
        print(f"Data directory: {os.path.abspath(self.data_dir)}")
        print("═" * 50)


def main():
    """Main function for command line usage"""
    parser = argparse.ArgumentParser(
        description='Reset Varasai Oxygen database files',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python reset_database.py --all --backup      Reset everything with backup
  python reset_database.py --customers         Reset only customers (with backup)
  python reset_database.py --cylinders         Reset only cylinders (with backup)
  python reset_database.py --info              Show database information
        """
    )
    
    parser.add_argument('--customers', action='store_true', 
                       help='Reset customers database')
    parser.add_argument('--cylinders', action='store_true', 
                       help='Reset cylinders database')
    parser.add_argument('--all', action='store_true', 
                       help='Reset both databases')
    parser.add_argument('--backup', action='store_true', 
                       help='Create backup before reset (default: True)')
    parser.add_argument('--no-backup', action='store_true', 
                       help='Skip backup creation')
    parser.add_argument('--info', action='store_true', 
                       help='Show database information only')
    parser.add_argument('--force', action='store_true', 
                       help='Skip confirmation prompts')
    
    args = parser.parse_args()
    
    resetter = DatabaseResetter()
    
    # Show info if requested
    if args.info:
        resetter.show_database_info()
        return
    
    # Show current status
    resetter.show_database_info()
    
    # Determine what to reset
    reset_customers = args.customers or args.all
    reset_cylinders = args.cylinders or args.all
    
    if not reset_customers and not reset_cylinders:
        print("\nNo reset option specified. Use --help for usage information.")
        return
    
    # Determine backup setting
    create_backup = not args.no_backup
    
    # Show what will be done
    print("\nPLANNED ACTIONS:")
    if reset_customers:
        print("• Reset customers database")
    if reset_cylinders:
        print("• Reset cylinders database")
    if create_backup:
        print("• Create backup files before reset")
    
    # Confirmation unless forced
    if not args.force:
        print(f"\n⚠ WARNING: This will permanently delete data!")
        if create_backup:
            print("✓ Backup files will be created for safety")
        else:
            print("✗ NO BACKUP will be created")
        
        response = input("\nProceed with reset? (type 'yes' to confirm): ")
        if response.lower() != 'yes':
            print("Reset cancelled.")
            return
    
    # Perform reset operations
    print(f"\nStarting database reset...")
    success = True
    
    if args.all:
        success = resetter.reset_all(create_backup)
    else:
        if reset_customers:
            success &= resetter.reset_customers(create_backup)
        if reset_cylinders:
            success &= resetter.reset_cylinders(create_backup)
    
    # Show final status
    print(f"\n" + "═" * 50)
    if success:
        print("DATABASE RESET COMPLETED SUCCESSFULLY")
        resetter.show_database_info()
    else:
        print("DATABASE RESET COMPLETED WITH ERRORS")
        print("Check the error messages above for details")
    print("═" * 50)


if __name__ == "__main__":
    main()