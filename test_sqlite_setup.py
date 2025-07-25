#!/usr/bin/env python3
"""
Test script to verify SQLite setup works correctly
"""
import os
import sys

def test_sqlite_setup():
    """Test SQLite database setup and basic operations"""
    try:
        print("🧪 Testing SQLite setup...")
        
        # Test app import
        from app_sqlite import app, db
        from sqlite_models import Customer, Cylinder, RentalHistory
        
        with app.app_context():
            # Test database creation
            db.create_all()
            print("✓ Database tables created successfully")
            
            # Test customer creation
            test_customer = Customer(
                id='TEST-001',
                customer_no='T001',
                customer_name='Test Customer',
                customer_email='test@example.com',
                customer_phone='1234567890'
            )
            db.session.add(test_customer)
            db.session.commit()
            print("✓ Test customer created")
            
            # Test customer retrieval
            retrieved = Customer.query.filter_by(customer_no='T001').first()
            if retrieved and retrieved.customer_name == 'Test Customer':
                print("✓ Customer retrieval works")
            else:
                print("❌ Customer retrieval failed")
                return False
            
            # Test cylinder creation
            test_cylinder = Cylinder(
                id='CYL-TEST-001',
                custom_id='T001',
                type='Medical Oxygen',
                size='40L',
                status='available'
            )
            db.session.add(test_cylinder)
            db.session.commit()
            print("✓ Test cylinder created")
            
            # Cleanup test data
            db.session.delete(test_customer)
            db.session.delete(test_cylinder)
            db.session.commit()
            print("✓ Test data cleaned up")
            
            print("\n🎉 SQLite setup test completed successfully!")
            print("Your app is ready for PythonAnywhere deployment!")
            return True
            
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = test_sqlite_setup()
    sys.exit(0 if success else 1)