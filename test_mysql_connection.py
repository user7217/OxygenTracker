#!/usr/bin/env python3
"""
Test MySQL connection for PythonAnywhere deployment
"""
import os
import sys

def test_mysql_connection():
    """Test MySQL database connection"""
    try:
        print("🧪 Testing MySQL connection...")
        
        # Set the database URL
        database_url = 'mysql://varasicyl:root%40123@varasicyl.mysql.pythonanywhere-services.com/varasicyl$oxygen'
        os.environ['DATABASE_URL'] = database_url
        
        # Test app import and connection
        from app_mysql import app, db
        from mysql_models import Customer, Cylinder, RentalHistory
        
        with app.app_context():
            # Test database connection
            result = db.engine.execute('SELECT 1')
            print("✓ MySQL connection successful")
            
            # Test table creation
            db.create_all()
            print("✓ Database tables created/verified")
            
            # Test basic query
            customer_count = Customer.query.count()
            cylinder_count = Cylinder.query.count()
            print(f"✓ Current data: {customer_count} customers, {cylinder_count} cylinders")
            
            print("\n🎉 MySQL connection test completed successfully!")
            print("Your app is ready for PythonAnywhere deployment!")
            return True
            
    except Exception as e:
        print(f"❌ Connection test failed: {str(e)}")
        print("\nTroubleshooting tips:")
        print("1. Verify database name: varasicyl$oxygen exists in PythonAnywhere")
        print("2. Check password is correct: root@123")
        print("3. Ensure database is accessible from your account")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = test_mysql_connection()
    sys.exit(0 if success else 1)