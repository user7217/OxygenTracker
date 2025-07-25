#!/usr/bin/env python3
"""
Check if MySQL database exists and is accessible
"""
import MySQLdb
import sys

def check_mysql_database():
    """Check if MySQL database exists and is accessible"""
    try:
        print("🔍 Checking MySQL database setup...")
        
        # Connection parameters
        host = 'varasicyl.mysql.pythonanywhere-services.com'
        user = 'varasicyl'
        password = 'root@123'
        database = 'varasicyl$oxygen'
        
        print(f"Host: {host}")
        print(f"User: {user}")
        print(f"Database: {database}")
        
        # Test connection
        connection = MySQLdb.connect(
            host=host,
            user=user,
            passwd=password,
            db=database
        )
        
        cursor = connection.cursor()
        
        # Test basic query
        cursor.execute("SELECT VERSION()")
        version = cursor.fetchone()
        print(f"✓ Connected to MySQL {version[0]}")
        
        # Check existing tables
        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()
        print(f"✓ Found {len(tables)} existing tables")
        
        if tables:
            for table in tables:
                cursor.execute(f"SELECT COUNT(*) FROM {table[0]}")
                count = cursor.fetchone()
                print(f"  - {table[0]}: {count[0]} records")
        
        cursor.close()
        connection.close()
        
        print("\n🎉 MySQL database is accessible and ready!")
        return True
        
    except Exception as e:
        print(f"❌ Database check failed: {str(e)}")
        print("\nPossible issues:")
        print("1. Database 'varasicyl$oxygen' doesn't exist")
        print("2. Password 'root@123' is incorrect")
        print("3. Database permissions not set correctly")
        print("4. Need to create the database first in PythonAnywhere dashboard")
        return False

if __name__ == '__main__':
    success = check_mysql_database()
    sys.exit(0 if success else 1)