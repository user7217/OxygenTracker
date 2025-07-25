#!/usr/bin/env python3
"""
Simple test to check if MySQL credentials and database exist
This script tests the connection details for PythonAnywhere
"""
import os

def test_database_url():
    """Test the database URL format and connection"""
    print("🔧 Testing MySQL connection for PythonAnywhere...")
    
    # Your MySQL connection details
    username = "varasicyl"
    password = "root@123"
    host = "varasicyl.mysql.pythonanywhere-services.com"
    database = "varasicyl$Oxygen"
    
    # URL encode the password (@ becomes %40)
    encoded_password = password.replace("@", "%40")
    
    database_url = f"mysql://{username}:{encoded_password}@{host}/{database}"
    
    print(f"Username: {username}")
    print(f"Host: {host}")
    print(f"Database: {database}")
    print(f"Database URL: {database_url}")
    
    print("\n📋 Steps to deploy on PythonAnywhere:")
    print("1. Make sure database 'varasicyl$Oxygen' exists in PythonAnywhere Databases tab")
    print("2. Upload all files to /home/varasicyl/mysite/")
    print("3. Install dependencies: pip3.11 install --user flask flask-sqlalchemy mysqlclient")
    print("4. Create web app pointing to app_mysql.py")
    print("5. Update WSGI file with the provided configuration")
    print("6. Set static files mapping to /home/varasicyl/mysite/static/")
    print("7. Reload web app")
    
    print("\n⚠️  Important notes:")
    print("- This error occurs because you're running locally (Replit) trying to connect to remote MySQL")
    print("- The connection will work correctly when deployed on PythonAnywhere")
    print("- Local development should use SQLite or local database")
    
    return database_url

if __name__ == '__main__':
    db_url = test_database_url()
    print(f"\n✅ Database URL for PythonAnywhere: {db_url}")