#!/usr/bin/env python3
"""
Test MySQL deployment configuration to ensure everything works together
"""
import os

def test_mysql_deployment():
    """Test the complete MySQL deployment setup"""
    print("🧪 Testing MySQL deployment configuration...")
    
    try:
        # Set environment variables
        os.environ['DATABASE_URL'] = 'mysql://varasicyl:root%40123@varasicyl.mysql.pythonanywhere-services.com/varasicyl$Oxygen'
        os.environ['SESSION_SECRET'] = 'test-secret-key-for-deployment'
        
        # Test app import
        print("1. Testing app import...")
        from app_mysql_fixed import app, db, Customer, Cylinder, RentalHistory
        print("   ✓ App and models imported successfully")
        
        # Test app context
        print("2. Testing app context...")
        with app.app_context():
            print("   ✓ App context works")
            
            # Test model definitions
            print("3. Testing model definitions...")
            print(f"   ✓ Customer table: {Customer.__tablename__}")
            print(f"   ✓ Cylinder table: {Cylinder.__tablename__}")
            print(f"   ✓ RentalHistory table: {RentalHistory.__tablename__}")
            
            # Test model methods
            print("4. Testing model methods...")
            
            # Create test instances (don't save to DB)
            test_customer = Customer(
                id='TEST_001',
                customer_name='Test Customer',
                customer_no='001'
            )
            customer_dict = test_customer.to_dict()
            print(f"   ✓ Customer.to_dict() works: {len(customer_dict)} fields")
            
            test_cylinder = Cylinder(
                id='CYL_TEST_001',
                custom_id='T001',
                type='Medical Oxygen',
                size='40L'
            )
            cylinder_dict = test_cylinder.to_dict()
            print(f"   ✓ Cylinder.to_dict() works: {len(cylinder_dict)} fields")
            
        # Test routes import
        print("5. Testing routes import...")
        from routes_mysql import login_required, admin_required
        print("   ✓ Routes imported successfully")
        
        # Test auth models
        print("6. Testing authentication...")
        from auth_models import UserManager
        user_manager = UserManager()
        print("   ✓ Authentication system ready")
        
        print("\n🎉 MySQL deployment configuration test PASSED!")
        print("✅ Ready for PythonAnywhere deployment")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Test FAILED: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = test_mysql_deployment()
    exit(0 if success else 1)