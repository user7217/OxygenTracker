# PythonAnywhere Deployment Checklist

## Quick Deployment Steps for varasicyl account

### ✅ Step 1: Database Setup
1. Go to PythonAnywhere **Databases** tab
2. Create MySQL database named: `varasicyl$Oxygen`
3. Set password: `root@123` (or confirm current password)
4. Note the connection details

### ✅ Step 2: Upload Code
**Option A: Git Clone (Recommended)**
```bash
cd ~
git clone https://github.com/yourusername/your-repo.git mysite
cd mysite
```

**Option B: File Upload**
- Upload all project files to `/home/varasicyl/mysite/`

### ✅ Step 3: Install Dependencies
```bash
cd ~/mysite
pip3.11 install --user flask flask-sqlalchemy mysqlclient werkzeug python-dotenv reportlab pandas openpyxl
```

### ✅ Step 4: Create Web App
1. Go to **Web** tab
2. Create new web app
3. Choose **Python 3.11**
4. Select **Manual configuration**

### ✅ Step 5: Configure WSGI
Edit WSGI file (`/var/www/varasicyl_pythonanywhere_com_wsgi.py`):

```python
import sys
import os

# Add your project directory to the Python path
path = '/home/varasicyl/mysite'
if path not in sys.path:
    sys.path.append(path)

# Set environment variables for production
os.environ['SESSION_SECRET'] = 'your-production-secret-key-here'
os.environ['FLASK_ENV'] = 'production'
os.environ['DATABASE_URL'] = 'mysql://varasicyl:root%40123@varasicyl.mysql.pythonanywhere-services.com/varasicyl$Oxygen'

# Import your Flask application
from app_mysql_fixed import app as application

if __name__ == "__main__":
    application.run()
```

### ✅ Step 6: Configure Static Files
In **Web** tab, add static file mapping:
- **URL**: `/static/`
- **Directory**: `/home/varasicyl/mysite/static/`

### ✅ Step 7: Initialize Database
```bash
cd ~/mysite
python3.11 -c "
from app_mysql_fixed import app, db
with app.app_context():
    db.create_all()
    print('✓ Database tables created!')
"
```

### ✅ Step 8: Import Data (if you have existing data)
```bash
cd ~/mysite
python3.11 import_to_mysql_fixed.py
```

### ✅ Step 9: Test Deployment
1. **Reload** web app from Web tab
2. Visit: `https://varasicyl.pythonanywhere.com`
3. Login with: `admin` / `admin123`
4. **Change admin password immediately!**

## 🚨 Important Notes

- The MySQL connection error you saw is normal when running locally
- The app will connect correctly when deployed on PythonAnywhere
- Always use encoded password in URL: `root@123` becomes `root%40123`
- Make sure database `varasicyl$Oxygen` exists before deployment

## 📞 Troubleshooting

**If app won't start:**
- Check error logs in Web tab
- Verify all dependencies are installed
- Confirm database exists and password is correct

**If database connection fails:**
- Test connection: `mysql -u varasicyl -p -h varasicyl.mysql.pythonanywhere-services.com varasicyl$Oxygen`
- Verify password is exactly: `root@123`
- Check database name is exactly: `varasicyl$Oxygen`

**If static files don't load:**
- Check static files mapping in Web tab
- Verify path: `/home/varasicyl/mysite/static/`

Your app should be live at: **https://varasicyl.pythonanywhere.com**