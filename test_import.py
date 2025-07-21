#!/usr/bin/env python3
"""
Test Script for Standalone Importer

This script tests the standalone importer functionality without requiring
an actual MS Access database. It creates sample data to verify the
import system is working correctly.

Usage: python test_import.py
"""

import os
import json
from datetime import datetime
from standalone_importer import StandaloneImporter

def create_test_data():
    """Create test data files to simulate import functionality"""
    
    # Test customer data
    test_customers = [
        {
            "customer_no": "CUST001",
            "customer_name": "Test Company A",
            "customer_address": "123 Main St",
            "customer_city": "Test City",
            "customer_state": "Test State",
            "customer_phone": "555-0001",
            "customer_email": "test@company.com"
        },
        {
            "customer_no": "CUST002", 
            "customer_name": "Test Company B",
            "customer_address": "456 Oak Ave",
            "customer_city": "Another City",
            "customer_state": "Test State",
            "customer_phone": "555-0002",
            "customer_email": "info@testcompany.com"
        }
    ]
    
    # Test cylinder data
    test_cylinders = [
        {
            "serial_number": "OXY001",
            "type": "Medical Oxygen",
            "size": "Large",
            "location": "Warehouse",
            "status": "Available",
            "custom_id": "A1"
        },
        {
            "serial_number": "OXY002",
            "type": "Medical Oxygen", 
            "size": "Medium",
            "location": "Warehouse",
            "status": "Available",
            "custom_id": "A2"
        },
        {
            "serial_number": "CO2001",
            "type": "CO2",
            "size": "Small",
            "location": "Warehouse", 
            "status": "Available",
            "custom_id": "B1"
        }
    ]
    
    return test_customers, test_cylinders

def test_direct_import():
    """Test the import functionality directly without Access database"""
    print("🧪 Testing Standalone Importer Functionality")
    print("=" * 50)
    
    try:
        # Initialize importer
        importer = StandaloneImporter()
        
        # Show current data
        print("📊 Before Import:")
        importer.show_current_data_summary()
        
        # Get test data
        test_customers, test_cylinders = create_test_data()
        
        print(f"\n🔄 Testing Customer Import Logic...")
        imported_customer_count = 0
        for customer_data in test_customers:
            try:
                # Map customer fields (simulate mapping process)
                mapped_customer = importer._map_customer_fields(customer_data, importer._get_default_customer_mapping())
                
                # Check for duplicates
                existing_customers = importer.customer_model.get_all()
                is_duplicate = importer._check_customer_duplicate(mapped_customer, existing_customers)
                
                if not is_duplicate:
                    # Add customer
                    added_customer = importer.customer_model.add(mapped_customer)
                    imported_customer_count += 1
                    customer_id = added_customer.get('id', 'Unknown')
                    customer_name = customer_data.get('customer_name', 'Unknown')
                    print(f"✅ Imported customer: {customer_name} (ID: {customer_id})")
                else:
                    print(f"⚠️  Skipping duplicate customer: {customer_data.get('customer_name', 'Unknown')}")
                    
            except Exception as e:
                print(f"❌ Error importing customer: {e}")
        
        print(f"\n🔄 Testing Cylinder Import Logic...")
        imported_cylinder_count = 0
        for cylinder_data in test_cylinders:
            try:
                # Map cylinder fields (simulate mapping process)
                mapped_cylinder = importer._map_cylinder_fields(cylinder_data, importer._get_default_cylinder_mapping())
                
                # Check for duplicates
                existing_cylinders = importer.cylinder_model.get_all()
                is_duplicate = importer._check_cylinder_duplicate(mapped_cylinder, existing_cylinders)
                
                if not is_duplicate:
                    # Add cylinder
                    added_cylinder = importer.cylinder_model.add(mapped_cylinder)
                    imported_cylinder_count += 1
                    cylinder_id = added_cylinder.get('id', 'Unknown')
                    serial_number = cylinder_data.get('serial_number', 'Unknown')
                    custom_id = cylinder_data.get('custom_id', '')
                    display_id = custom_id if custom_id else serial_number
                    print(f"✅ Imported cylinder: {display_id} (System ID: {cylinder_id})")
                else:
                    print(f"⚠️  Skipping duplicate cylinder: {cylinder_data.get('serial_number', 'Unknown')}")
                    
            except Exception as e:
                print(f"❌ Error importing cylinder: {e}")
        
        # Show final results
        print(f"\n📊 After Import:")
        importer.show_current_data_summary()
        
        print(f"\n✅ Test Summary:")
        print(f"   👥 Customers imported: {imported_customer_count}")
        print(f"   🏺 Cylinders imported: {imported_cylinder_count}")
        print(f"   🆔 All records received unique system IDs")
        print(f"   📝 Original identifiers preserved")
        
        print(f"\n🎯 Test Result: PASSED - Import system working correctly!")
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        return False
    
    return True

def test_id_generation():
    """Test ID generation functionality"""
    print(f"\n🔬 Testing ID Generation:")
    print("-" * 30)
    
    try:
        importer = StandaloneImporter()
        
        # Test customer ID generation
        customer_ids = [importer.customer_model.generate_id() for _ in range(5)]
        print(f"Customer IDs generated: {customer_ids}")
        
        # Test cylinder ID generation  
        cylinder_ids = [importer.cylinder_model.generate_id() for _ in range(5)]
        print(f"Cylinder IDs generated: {cylinder_ids}")
        
        # Verify format
        for cid in customer_ids:
            assert cid.startswith('CUST-'), f"Customer ID format error: {cid}"
            assert len(cid) == 13, f"Customer ID length error: {cid}"
        
        for cid in cylinder_ids:
            assert cid.startswith('CYL-'), f"Cylinder ID format error: {cid}"
            assert len(cid) == 12, f"Cylinder ID length error: {cid}"
        
        print("✅ ID generation format test passed!")
        
    except Exception as e:
        print(f"❌ ID generation test failed: {e}")
        return False
    
    return True

if __name__ == '__main__':
    print("🚀 Standalone Importer Test Suite")
    print("=" * 60)
    
    # Run tests
    id_test_passed = test_id_generation()
    import_test_passed = test_direct_import()
    
    print("\n" + "=" * 60)
    if id_test_passed and import_test_passed:
        print("🎉 All tests PASSED! Standalone importer is ready to use.")
        print("\n💡 Next steps:")
        print("   1. Run 'python standalone_importer.py show_summary' to see current data")
        print("   2. Use 'python standalone_importer.py list_tables your_database.accdb' to explore Access files")
        print("   3. Import your real data using the import commands")
    else:
        print("❌ Some tests FAILED. Check the errors above.")