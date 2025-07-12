#!/usr/bin/env python3
"""
Test script to diagnose local development issues with Varasai Oxygen
"""
import os
import sys
import traceback

def test_imports():
    """Test all imports"""
    print("Testing imports...")
    try:
        from app import app
        print("✓ Flask app imported successfully")
        
        from models import Customer, Cylinder
        print("✓ Models imported successfully")
        
        from auth_models import UserManager
        print("✓ Auth models imported successfully")
        
        return app
    except Exception as e:
        print(f"✗ Import error: {e}")
        traceback.print_exc()
        return None

def test_data_directory():
    """Test data directory and files"""
    print("\nTesting data directory...")
    
    if not os.path.exists('data'):
        print("✗ Data directory does not exist - creating it...")
        os.makedirs('data', exist_ok=True)
    else:
        print("✓ Data directory exists")
    
    # Check for required files
    files = ['customers.json', 'cylinders.json', 'users.json']
    for file in files:
        path = os.path.join('data', file)
        if os.path.exists(path):
            print(f"✓ {file} exists")
        else:
            print(f"✗ {file} missing - will be created on first use")

def test_default_user():
    """Test default admin user creation"""
    print("\nTesting default user...")
    try:
        from auth_models import UserManager
        user_manager = UserManager()
        admin_user = user_manager.get_user_by_username('admin')
        if admin_user:
            print("✓ Default admin user exists")
            print("  Username: admin")
            print("  Password: admin123")
        else:
            print("✗ Default admin user not found")
    except Exception as e:
        print(f"✗ Error checking user: {e}")

def test_flask_routes(app):
    """Test Flask routes"""
    print("\nTesting Flask routes...")
    if app:
        with app.app_context():
            print("Available routes:")
            for rule in app.url_map.iter_rules():
                methods = ', '.join(rule.methods - {'OPTIONS', 'HEAD'})
                print(f"  {rule.rule} [{methods}] -> {rule.endpoint}")

def test_static_files():
    """Test static files"""
    print("\nTesting static files...")
    static_files = ['logo.jpg']
    for file in static_files:
        path = os.path.join('static', file)
        if os.path.exists(path):
            print(f"✓ {file} exists")
        else:
            print(f"✗ {file} missing")

def test_templates():
    """Test template files"""
    print("\nTesting template files...")
    template_files = ['base.html', 'index.html', 'login.html']
    for file in template_files:
        path = os.path.join('templates', file)
        if os.path.exists(path):
            print(f"✓ {file} exists")
        else:
            print(f"✗ {file} missing")

def main():
    print("=== Varasai Oxygen Local Development Test ===")
    print(f"Python version: {sys.version}")
    print(f"Working directory: {os.getcwd()}")
    print()
    
    # Run tests
    app = test_imports()
    test_data_directory()
    test_default_user()
    test_flask_routes(app)
    test_static_files()
    test_templates()
    
    print("\n=== Quick Start Instructions ===")
    print("1. Run: python main.py")
    print("2. Open: http://localhost:5000")
    print("3. Login with: admin / admin123")
    print("4. If you see errors, check the console output above")
    
    print("\n=== Common Issues & Solutions ===")
    print("• Dashboard not showing: Check login status and user authentication")
    print("• Import errors: Ensure all dependencies are installed")
    print("• Port 5000 busy: Kill existing processes or use different port")
    print("• Permission errors: Check file/directory permissions")

if __name__ == '__main__':
    main()