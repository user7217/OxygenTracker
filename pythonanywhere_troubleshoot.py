#!/usr/bin/env python3
"""
PythonAnywhere troubleshooting script to check common deployment issues
"""
import os
import sys

def check_deployment():
    """Check common PythonAnywhere deployment issues"""
    print("🔍 PythonAnywhere Deployment Troubleshooting\n")
    
    issues_found = []
    
    # 1. Check if we're using the right files
    print("1. Checking file structure...")
    required_files = [
        'app_mysql_fixed.py',
        'routes_mysql.py', 
        'wsgi.py',
        'auth_models.py'
    ]
    
    for file in required_files:
        if os.path.exists(file):
            print(f"   ✓ {file} exists")
        else:
            print(f"   ❌ {file} missing")
            issues_found.append(f"Missing file: {file}")
    
    # 2. Check WSGI configuration
    print("\n2. Checking WSGI configuration...")
    try:
        with open('wsgi.py', 'r') as f:
            wsgi_content = f.read()
            if 'app_mysql_fixed' in wsgi_content:
                print("   ✓ WSGI points to app_mysql_fixed")
            else:
                print("   ❌ WSGI not pointing to app_mysql_fixed")
                issues_found.append("WSGI configuration incorrect")
    except FileNotFoundError:
        print("   ❌ wsgi.py not found")
        issues_found.append("Missing wsgi.py file")
    
    # 3. Check database URL format
    print("\n3. Checking database configuration...")
    expected_db_url = "mysql://varasicyl:root%40123@varasicyl.mysql.pythonanywhere-services.com/varasicyl$Oxygen"
    
    if 'wsgi.py' in locals() or os.path.exists('wsgi.py'):
        try:
            with open('wsgi.py', 'r') as f:
                content = f.read()
                if expected_db_url in content:
                    print("   ✓ Database URL correctly configured")
                else:
                    print("   ❌ Database URL might be incorrect")
                    issues_found.append("Database URL configuration issue")
        except:
            pass
    
    # 4. Check for common import issues
    print("\n4. Checking for import issues...")
    try:
        # This will fail locally but shows what imports are being attempted
        os.environ['DATABASE_URL'] = expected_db_url
        os.environ['SESSION_SECRET'] = 'test-key'
        
        print("   Testing imports (will fail locally due to MySQL driver)...")
        try:
            from app_mysql_fixed import app
            print("   ✓ app_mysql_fixed imports successfully")
        except ModuleNotFoundError as e:
            if 'MySQLdb' in str(e):
                print("   ✓ Expected MySQL driver error (normal on local)")
            else:
                print(f"   ❌ Unexpected import error: {e}")
                issues_found.append(f"Import error: {e}")
        except Exception as e:
            print(f"   ❌ App initialization error: {e}")
            issues_found.append(f"App error: {e}")
            
    except Exception as e:
        print(f"   ❌ General error: {e}")
        issues_found.append(f"General error: {e}")
    
    # 5. Summary and recommendations
    print("\n" + "="*50)
    if not issues_found:
        print("✅ No obvious issues found in local files")
        print("\nPossible PythonAnywhere issues:")
        print("1. Database 'varasicyl$Oxygen' doesn't exist")
        print("2. Database password is incorrect")
        print("3. Missing Python dependencies")
        print("4. WSGI file path incorrect")
        print("5. Static files not configured")
    else:
        print("❌ Issues found:")
        for issue in issues_found:
            print(f"   - {issue}")
    
    print("\n🔧 Next steps:")
    print("1. Check PythonAnywhere error logs in Web tab")
    print("2. Verify database exists: varasicyl$Oxygen")
    print("3. Test database connection manually")
    print("4. Check all dependencies are installed")
    print("5. Verify WSGI file points to correct location")

if __name__ == '__main__':
    check_deployment()