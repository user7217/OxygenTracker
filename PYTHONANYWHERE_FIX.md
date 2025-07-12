# QUICK FIX for PythonAnywhere Dashboard Issue

## The Problem
Dashboard doesn't load due to `url_for()` configuration issues with static files.

## The Solution
Update your WSGI file with this exact configuration:

### Step 1: Update WSGI File
In PythonAnywhere Web tab → WSGI configuration file, replace with:

```python
import sys
import os

# Replace 'yourusername' with YOUR actual username
path = '/home/yourusername/varasai-oxygen'
if path not in sys.path:
    sys.path.insert(0, path)

# Set environment variables
os.environ['SESSION_SECRET'] = 'your-secret-key-here'
os.environ['FLASK_ENV'] = 'production'

# Import Flask app
from app import app as application

# Fix PythonAnywhere URL building issues
application.config.update({
    'SERVER_NAME': None,
    'APPLICATION_ROOT': '/',
    'PREFERRED_URL_SCHEME': 'https'
})
```

### Step 2: Reload Web App
Click the green "Reload" button in Web tab.

### Step 3: Test
Visit your site: `yourusername.pythonanywhere.com`

## If Still Not Working

### Alternative: Remove Logo Temporarily
If the above doesn't work, temporarily disable logos by renaming the index template:

In PythonAnywhere Files tab:
1. Rename `templates/index.html` to `templates/index_with_logo.html`
2. Rename `templates/index_no_logo.html` to `templates/index.html`
3. Reload web app

This will show the dashboard without logos while you fix the static files.

## Common Issues

### Wrong Username in Path
- Make sure you replace `yourusername` with your actual PythonAnywhere username
- Path should be exactly: `/home/YOURUSERNAME/varasai-oxygen`

### Missing Static File Mapping
In Web tab → Static files section:
- URL: `/static/`
- Directory: `/home/yourusername/varasai-oxygen/static/`

### Still Getting Errors?
Check error logs in Web tab → Error log and look for specific error messages.

The dashboard should work immediately after applying the WSGI configuration fix.