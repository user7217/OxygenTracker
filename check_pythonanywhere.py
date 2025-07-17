#!/usr/bin/env python3
"""
Diagnostic script for PythonAnywhere deployment issues
Run this on PythonAnywhere to identify common problems
"""
import sys
import os

def check_python_version():
    print("=== Python Version ===")
    print(f"Python: {sys.version}")
    print(f"Python path: {sys.executable}")

def check_working_directory():
    print("\n=== Working Directory ===")
    print(f"Current directory: {os.getcwd()}")
    print("Files in current directory:")
    try:
        for item in sorted(os.listdir('.')):
            if os.path.isdir(item):
                print(f"  📁 {item}/")
            else:
                print(f"  📄 {item}")
    except Exception as e:
        print(f"Error listing files: {e}")

def check_flask_import():
    print("\n=== Flask Import Test ===")
    try:
        import flask
        print(f"✓ Flask {flask.__version__} imported successfully")
        
        try:
            from app import app
            print("✓ App imported successfully")
            
            print("Available routes:")
            with app.app_context():
                for rule in app.url_map.iter_rules():
                    print(f"  {rule.rule} -> {rule.endpoint}")
                    
        except Exception as e:
            print(f"✗ Error importing app: {e}")
            
    except ImportError as e:
        print(f"✗ Flask import failed: {e}")
        print("Install with: pip3.10 install --user flask")

def check_dependencies():
    print("\n=== Dependencies Check ===")
    required = ['flask', 'werkzeug']
    
    for package in required:
        try:
            module = __import__(package)
            version = getattr(module, '__version__', 'unknown')
            print(f"✓ {package} {version}")
        except ImportError:
            print(f"✗ {package} missing")

def check_data_directory():
    print("\n=== Data Directory ===")
    if os.path.exists('data'):
        print("✓ Data directory exists")
        try:
            files = os.listdir('data')
            for file in files:
                print(f"  📄 {file}")
        except Exception as e:
            print(f"Error reading data directory: {e}")
    else:
        print("✗ Data directory missing")
        print("Create with: mkdir -p data")

def check_static_files():
    print("\n=== Static Files ===")
    if os.path.exists('static'):
        print("✓ Static directory exists")
        try:
            files = os.listdir('static')
            for file in files:
                print(f"  📄 {file}")
        except Exception as e:
            print(f"Error reading static directory: {e}")
    else:
        print("✗ Static directory missing")

def check_templates():
    print("\n=== Templates ===")
    if os.path.exists('templates'):
        print("✓ Templates directory exists")
        try:
            files = os.listdir('templates')
            for file in files:
                print(f"  📄 {file}")
        except Exception as e:
            print(f"Error reading templates directory: {e}")
    else:
        print("✗ Templates directory missing")

def check_environment():
    print("\n=== Environment Variables ===")
    session_secret = os.environ.get('SESSION_SECRET')
    if session_secret:
        print("✓ SESSION_SECRET is set")
    else:
        print("✗ SESSION_SECRET not set")
        print("Add to WSGI file: os.environ['SESSION_SECRET'] = 'your-secret'")

def check_permissions():
    print("\n=== File Permissions ===")
    try:
        # Test write permission
        test_file = 'test_write.tmp'
        with open(test_file, 'w') as f:
            f.write('test')
        os.remove(test_file)
        print("✓ Write permissions OK")
    except Exception as e:
        print(f"✗ Write permission issue: {e}")

def main():
    print("=== PythonAnywhere Deployment Diagnostic ===")
    print("Run this script to check for common deployment issues\n")
    
    check_python_version()
    check_working_directory()
    check_flask_import()
    check_dependencies()
    check_data_directory()
    check_static_files()
    check_templates()
    check_environment()
    check_permissions()
    
    print("\n=== Summary ===")
    print("1. Fix any ✗ errors shown above")
    print("2. Configure WSGI file with correct paths")
    print("3. Add static file mapping in PythonAnywhere Web tab")
    print("4. Reload web app after changes")
    print("5. Check error logs if issues persist")

if __name__ == '__main__':
    main()