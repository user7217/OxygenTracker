#!/usr/bin/env python3
"""
Fix MySQL URL format for PythonAnywhere deployment
Test different URL formats to find what works
"""

def test_mysql_urls():
    """Test different MySQL URL formats"""
    print("Testing MySQL URL formats for PythonAnywhere...")
    
    # Your database details
    username = "varasicyl"
    password = "root@123"
    host = "varasicyl.mysql.pythonanywhere-services.com"
    database = "varasicyl$Oxygen"
    
    # Different URL format options
    url_formats = [
        # PyMySQL driver (recommended for PythonAnywhere)
        f"mysql+pymysql://{username}:{password}@{host}/{database}",
        
        # URL encoded @ symbol
        f"mysql+pymysql://{username}:root%40123@{host}/{database}",
        
        # Alternative encoding
        f"mysql+pymysql://{username}:{'root@123'.replace('@', '%40')}@{host}/{database}",
        
        # MySQLdb driver (original)
        f"mysql://{username}:root%40123@{host}/{database}",
    ]
    
    print("\nURL format options:")
    for i, url in enumerate(url_formats, 1):
        print(f"{i}. {url}")
    
    print("\n🔧 Recommended for PythonAnywhere:")
    print("Use PyMySQL driver instead of MySQLdb")
    print("Install: pip3.11 install --user PyMySQL")
    
    return url_formats[0]  # Return the recommended format

if __name__ == '__main__':
    recommended_url = test_mysql_urls()
    print(f"\n✅ Recommended URL: {recommended_url}")