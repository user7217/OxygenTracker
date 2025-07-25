# PythonAnywhere Deployment Guide (SQLite - Free Account)

This guide helps you deploy your Oxygen Cylinder Tracker to PythonAnywhere using SQLite database with a free account.

## Prerequisites

1. **PythonAnywhere Account**: Sign up at https://www.pythonanywhere.com/ (free account works!)
2. **Git Repository**: Your code should be in a Git repository (GitHub, GitLab, etc.)

## Step 1: Upload Your Code

### Option A: Using Git (Recommended)
1. Open a **Bash console** from your PythonAnywhere dashboard
2. Clone your repository:
   ```bash
   cd ~
   git clone https://github.com/yourusername/your-repository.git mysite
   cd mysite
   ```

### Option B: Upload Files
1. Use the **Files** tab in PythonAnywhere dashboard
2. Upload all your project files to `/home/yourusername/mysite/`

## Step 2: Set Up SQLite Database

SQLite requires no setup - the database file will be created automatically when the app starts!

## Step 3: Install Dependencies

1. Open a **Bash console**
2. Navigate to your project and install dependencies:
   ```bash
   cd ~/mysite
   pip3.11 install --user -r requirements.txt
   ```

   If you don't have a requirements.txt, install manually:
   ```bash
   pip3.11 install --user flask flask-sqlalchemy werkzeug python-dotenv reportlab pandas openpyxl
   ```

## Step 4: Configure Database Connection

1. Create a `.env` file in your project root:
   ```bash
   cd ~/mysite
   nano .env
   ```

2. Add your database configuration:
   ```env
   DATABASE_URL=sqlite:///database.db
   SESSION_SECRET=your-very-secure-secret-key-here
   FLASK_ENV=production
   ```

## Step 5: Update WSGI Configuration

1. Go to **Web** tab in PythonAnywhere dashboard
2. Create a new web app (Python 3.11, Manual configuration)
3. Edit the WSGI file (`/var/www/yourusername_pythonanywhere_com_wsgi.py`):

   ```python
   import sys
   import os
   from dotenv import load_dotenv

   # Add your project directory to the Python path
   path = '/home/yourusername/mysite'
   if path not in sys.path:
       sys.path.append(path)

   # Load environment variables
   load_dotenv(os.path.join(path, '.env'))

   # Import your Flask application (SQLite version)
   from app_sqlite import app as application

   if __name__ == "__main__":
       application.run()
   ```

## Step 6: Configure Static Files

1. In **Web** tab, scroll to **Static files** section
2. Add static file mapping:
   - **URL**: `/static/`
   - **Directory**: `/home/yourusername/mysite/static/`

## Step 7: Initialize Database

1. Open a **Bash console**
2. Run database initialization:
   ```bash
   cd ~/mysite
   python3.11 -c "
   from app_sqlite import app, db
   with app.app_context():
       db.create_all()
       print('✓ SQLite database tables created successfully!')
   "
   ```

## Step 8: Import Your Data

If you have existing JSON data files, import them:

1. Upload your JSON data files to `/home/yourusername/mysite/data/`
2. Run the SQLite import script:
   ```bash
   cd ~/mysite
   python3.11 import_to_sqlite.py
   ```

## Step 9: Test Your Application

1. Go to **Web** tab and click **Reload** button
2. Visit your application: `https://yourusername.pythonanywhere.com`
3. Login with default credentials: `admin` / `admin123`
4. **IMPORTANT**: Change the admin password immediately!

## Step 10: Environment Variables (Alternative)

If you prefer not to use .env file, set environment variables in WSGI file:

```python
import sys
import os

# Add your project directory to the Python path
path = '/home/yourusername/mysite'
if path not in sys.path:
    sys.path.append(path)

# Set environment variables
os.environ['DATABASE_URL'] = 'postgresql://yourusername:yourpassword@yourusername-[number].postgres.pythonanywhere-services.com:10xxx/yourusername$databasename'
os.environ['SESSION_SECRET'] = 'your-very-secure-secret-key-here'
os.environ['FLASK_ENV'] = 'production'

# Import your Flask application
from app import app as application

if __name__ == "__main__":
    application.run()
```

## Troubleshooting

### Application Won't Start
1. Check **Error logs** in Web tab
2. Common issues:
   - Wrong paths in WSGI file
   - Missing dependencies
   - Database connection errors

### Database Connection Issues
1. Check if database.db file was created in your project folder
2. Verify SQLite permissions in your home directory
3. Ensure DATABASE_URL is set to sqlite:///database.db

### Import Errors
1. Check if all files are uploaded correctly
2. Verify Python path in WSGI file
3. Install missing dependencies

### Performance Issues
1. Optimize database queries
2. Consider upgrading to higher PythonAnywhere plan
3. Add database indexes for frequently searched fields

## Security Checklist

- [ ] Change default admin password
- [ ] Use secure SESSION_SECRET
- [ ] Enable HTTPS (automatic on PythonAnywhere)
- [ ] Regularly backup your database
- [ ] Keep dependencies updated

## Updating Your Application

To deploy updates:
1. Pull latest code: `git pull origin main`
2. Install new dependencies if any
3. Run database migrations if needed
4. Reload web app from Web tab

## Backup Strategy

1. **Database Backup**: Download the database.db file regularly via Files tab
2. **Code Backup**: Keep code in Git repository
3. **Data Export**: Regularly export data to JSON using Reports feature

## Support

For PythonAnywhere specific issues:
- Documentation: https://help.pythonanywhere.com/
- Forums: https://www.pythonanywhere.com/forums/
- Support: help@pythonanywhere.com

Your Oxygen Cylinder Tracker should now be running on PythonAnywhere!