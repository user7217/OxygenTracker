#!/usr/bin/env python3
"""
Test the MySQL app configuration to ensure SQLAlchemy is properly initialized
"""
import os

def test_mysql_app():
    """Test MySQL app initialization"""
    try:
        print("Testing MySQL app configuration...")
        
        # Set environment for testing
        os.environ['DATABASE_URL'] = 'mysql://varasicyl:root%40123@varasicyl.mysql.pythonanywhere-services.com/varasicyl$Oxygen'
        os.environ['SESSION_SECRET'] = 'test-secret-key'
        
        # Import app
        from app_mysql import app, db
        
        print("✓ App imported successfully")
        
        # Test app context
        with app.app_context():
            print("✓ App context works")
            
            # Import models
            from mysql_models import Customer, Cylinder, RentalHistory
            print("✓ Models imported successfully")
            
            # Test model definitions
            print(f"✓ Customer table: {Customer.__tablename__}")
            print(f"✓ Cylinder table: {Cylinder.__tablename__}")
            print(f"✓ RentalHistory table: {RentalHistory.__tablename__}")
            
            print("\n🎉 MySQL app configuration is correct!")
            print("The SQLAlchemy initialization is working properly.")
            
        return True
        
    except Exception as e:
        print(f"❌ Configuration error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    test_mysql_app()