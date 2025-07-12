# PythonAnywhere Deployment Guide for Varasai Oxygen

## Step-by-Step Deployment

### 1. Upload Your Code
```bash
# In PythonAnywhere console, clone or upload your code
cd ~
git clone <your-repo-url> varasai-oxygen
# OR upload files manually via Files tab
```

### 2. Install Dependencies
```bash
# In PythonAnywhere console
cd ~/varasai-oxygen
pip3.10 install --user Flask==3.0.0 Werkzeug==3.0.1
# Add other dependencies as needed
```

### 3. Create Directories
```bash
mkdir -p ~/varasai-oxygen/data
mkdir -p ~/varasai-oxygen/static
mkdir -p ~/varasai-oxygen/templates
```

### 4. Web App Configuration

#### A. In PythonAnywhere Web tab:
1. **Create new web app**
2. **Choose "Manual configuration"**
3. **Select Python 3.10**

#### B. Configure WSGI file:
- Go to Web tab → Code section → WSGI configuration file
- Replace content with:

```python
import sys
import os

# Replace 'yourusername' with your actual username
path = '/home/yourusername/varasai-oxygen'
if path not in sys.path:
    sys.path.insert(0, path)

# Set environment variable
os.environ['SESSION_SECRET'] = 'your-secret-key-here'

# Import Flask app
from app import app as application
```

#### C. Set Static Files:
- In Web tab → Static files section
- Add mapping:
  - **URL**: `/static/`
  - **Directory**: `/home/yourusername/varasai-oxygen/static/`

### 5. Common PythonAnywhere Issues & Solutions

#### Issue: "Dashboard doesn't show"
**Cause**: Path or import issues
**Solution**:
```python
# In WSGI file, ensure correct path
import sys
import os
path = '/home/YOURUSERNAME/varasai-oxygen'  # Replace YOURUSERNAME
if path not in sys.path:
    sys.path.insert(0, path)
```

#### Issue: "500 Internal Server Error"
**Cause**: Missing dependencies or path issues
**Solution**:
1. Check error logs in Web tab → Error Log
2. Install missing packages:
```bash
pip3.10 install --user flask werkzeug
```

#### Issue: "Static files not loading"
**Cause**: Static file mapping not configured
**Solution**: Add static file mapping in Web tab

#### Issue: "Session/login issues"
**Cause**: Missing SESSION_SECRET
**Solution**: Add to WSGI file:
```python
os.environ['SESSION_SECRET'] = 'your-unique-secret-key'
```

### 6. File Permissions
```bash
# In PythonAnywhere console
cd ~/varasai-oxygen
chmod 755 data/
chmod 644 data/*.json  # If files exist
```

### 7. Testing

#### A. Check imports:
```bash
# In PythonAnywhere console
cd ~/varasai-oxygen
python3.10 -c "from app import app; print('App imported successfully')"
```

#### B. Test routes:
```bash
python3.10 -c "
from app import app
with app.app_context():
    for rule in app.url_map.iter_rules():
        print(f'{rule.rule} -> {rule.endpoint}')
"
```

### 8. Debugging Tips

#### Check Error Logs:
- Web tab → Error log
- Look for Python import errors or path issues

#### Test in Console:
```bash
cd ~/varasai-oxygen
python3.10 test_local.py  # If you uploaded the test script
```

#### Common Error Messages:

**"No module named 'app'"**
- Fix: Check WSGI file path configuration

**"No module named 'flask'"**
- Fix: `pip3.10 install --user flask`

**"TemplateNotFound"**
- Fix: Check templates directory exists and has correct permissions

### 9. Production Checklist

- [ ] WSGI file configured with correct path
- [ ] Static files mapping added
- [ ] SESSION_SECRET environment variable set
- [ ] All dependencies installed
- [ ] data/ directory created with proper permissions
- [ ] Error logs checked for issues
- [ ] Test login with admin/admin123

### 10. Default Login
After successful deployment:
- **URL**: your-username.pythonanywhere.com
- **Username**: admin
- **Password**: admin123

### 11. Troubleshooting Commands

```bash
# Check current directory
pwd

# List files
ls -la

# Check Python path
python3.10 -c "import sys; print(sys.path)"

# Test app import
python3.10 -c "from app import app; print('Success')"

# Check installed packages
pip3.10 list --user | grep -i flask
```

## Need Help?
1. Check PythonAnywhere error logs first
2. Test imports in console
3. Verify file paths in WSGI configuration
4. Ensure all dependencies are installed with `--user` flag