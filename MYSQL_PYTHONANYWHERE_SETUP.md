# MySQL Setup for PythonAnywhere Deployment

This guide explains how to set up your Oxygen Cylinder Tracker with MySQL on PythonAnywhere.

## Overview

The application has been migrated to use MySQL instead of SQLite for better PythonAnywhere compatibility. The main files are:

- `app_mysql_clean.py` - Clean MySQL Flask application
- `migrate_sqlite_to_mysql.py` - Migration script from SQLite to MySQL
- `main.py` - Updated to use MySQL app

## PythonAnywhere MySQL Setup

### Step 1: Create MySQL Database on PythonAnywhere

1. **Login to PythonAnywhere Console**
   - Go to your PythonAnywhere dashboard
   - Click on "Tasks" → "Database"

2. **Create Database**
   ```bash
   # In PythonAnywhere console
   mysql -u yourusername -p
   CREATE DATABASE yourusername$oxygen_tracker;
   exit
   ```

3. **Note Your MySQL Credentials**
   - Host: `yourusername.mysql.pythonanywhere-services.com`
   - Username: `yourusername`
   - Password: Your MySQL password
   - Database: `yourusername$oxygen_tracker`

### Step 2: Configure Environment Variables

Create a `.env` file with your MySQL credentials:

```bash
# MySQL Configuration for PythonAnywhere
MYSQL_HOST=yourusername.mysql.pythonanywhere-services.com
MYSQL_USER=yourusername
MYSQL_PASSWORD=your_mysql_password
MYSQL_DATABASE=yourusername$oxygen_tracker
SESSION_SECRET=your-secret-key-here
```

### Step 3: Upload Files to PythonAnywhere

Upload these key files to your PythonAnywhere account:

```
/home/yourusername/mysite/
├── app_mysql_clean.py          # Main Flask application
├── main.py                     # Entry point
├── migrate_sqlite_to_mysql.py  # Migration script
├── templates/                  # All template files
├── static/                     # Static files
├── users.json                  # User authentication
├── database.db                 # Your SQLite database (for migration)
└── .env                        # Environment variables
```

### Step 4: Run Migration

```bash
# In PythonAnywhere console, navigate to your app directory
cd /home/yourusername/mysite/

# Run the migration script
python3.10 migrate_sqlite_to_mysql.py
```

Expected output:
```
🚀 Starting SQLite to MySQL migration...
📋 Configuration:
   • MySQL Host: yourusername.mysql.pythonanywhere-services.com
   • MySQL Database: yourusername$oxygen_tracker
   • MySQL User: yourusername

🔧 Initializing MySQL database...
✅ MySQL database tables created successfully!
📊 Migrating customers...
✅ Migrated 249 customers
📊 Migrating cylinders...
✅ Migrated 6774 cylinders
📊 Migrating rental history...
✅ Migrated 10000 rental history records

🎉 Migration completed successfully!
📈 Summary:
   • 249 customers migrated
   • 6774 cylinders migrated
   • 10000 rental history records migrated
```

### Step 5: Configure WSGI

Update your WSGI configuration file (`/var/www/yourusername_pythonanywhere_com_wsgi.py`):

```python
import sys
import os

# Add your project directory to sys.path
project_home = '/home/yourusername/mysite'
if project_home not in sys.path:
    sys.path = [project_home] + sys.path

# Load environment variables
def load_environment():
    env_file = os.path.join(project_home, '.env')
    if os.path.exists(env_file):
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ.setdefault(key.strip(), value.strip())

load_environment()

from main import app as application
```

### Step 6: Test Your Application

1. **Reload your web app** in PythonAnywhere dashboard
2. **Visit your site**: `https://yourusername.pythonanywhere.com`
3. **Login with**: `admin` / `admin123`
4. **Verify data migration**: Check customers and cylinders pages

## Key Benefits of MySQL

- **Better Performance**: Optimized for larger datasets
- **Concurrent Access**: Multiple users can access simultaneously
- **Backup Support**: PythonAnywhere provides MySQL backup tools
- **Scaling**: Easy to upgrade to larger MySQL plans
- **Professional**: Industry-standard database solution

## Application Features

Your migrated application includes:

✅ **Complete Data Migration**: All 249 customers, 6,774 cylinders, and 10,000 rental records
✅ **User Authentication**: Admin login system
✅ **Customer Management**: View and search customers
✅ **Cylinder Tracking**: Full inventory management
✅ **Rental History**: Complete transaction records
✅ **Responsive Design**: Works on desktop and mobile
✅ **Search & Filters**: Find data quickly
✅ **Pagination**: Handle large datasets efficiently

## Troubleshooting

### Connection Issues
```python
# Test MySQL connection in PythonAnywhere console
import pymysql

config = {
    'host': 'yourusername.mysql.pythonanywhere-services.com',
    'user': 'yourusername',
    'password': 'your_password',
    'database': 'yourusername$oxygen_tracker'
}

try:
    conn = pymysql.connect(**config)
    print("✅ MySQL connection successful!")
    conn.close()
except Exception as e:
    print(f"❌ Connection failed: {e}")
```

### Database Issues
```bash
# Check if tables exist
mysql -u yourusername -p yourusername$oxygen_tracker
SHOW TABLES;
SELECT COUNT(*) FROM customers;
SELECT COUNT(*) FROM cylinders;
```

## Support

- **PythonAnywhere Help**: https://help.pythonanywhere.com/
- **MySQL Documentation**: https://dev.mysql.com/doc/
- **Application Issues**: Check the error logs in PythonAnywhere dashboard

Your oxygen cylinder tracker is now ready for professional MySQL-based hosting on PythonAnywhere!