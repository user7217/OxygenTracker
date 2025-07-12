# Fix Static Files on PythonAnywhere

## The Problem
After adding logo images, the dashboard doesn't show because static files (CSS, images, JS) aren't loading properly on PythonAnywhere.

## Quick Fix

### 1. Check Static Files Mapping
In PythonAnywhere Web tab → Static files section:
- **URL**: `/static/`
- **Directory**: `/home/yourusername/varasai-oxygen/static/`
- Replace `yourusername` with your actual username

### 2. Upload Logo Files
Make sure these files are in your static folder:
- `static/logo.jpg` (main logo)
- `static/favicon.ico` (browser icon)

### 3. Check File Permissions
In PythonAnywhere console:
```bash
cd ~/varasai-oxygen
ls -la static/
chmod 644 static/*
```

### 4. Alternative: Use CDN URLs
If static files still don't work, temporarily use online URLs by editing templates:

**In templates/base.html**, replace:
```html
<link rel="icon" href="{{ url_for('static', filename='favicon.ico') }}">
```
With:
```html
<link rel="icon" href="https://your-domain.com/favicon.ico">
```

**In templates/base.html and templates/index.html**, replace:
```html
<img src="{{ url_for('static', filename='logo.jpg') }}" alt="Varasai Oxygen">
```
With a temporary placeholder or upload logo to a free image host.

### 5. Test Without Images
Temporarily comment out logo references to test if the app works:

**In templates/index.html**, comment out:
```html
<!-- <img src="{{ url_for('static', filename='logo.jpg') }}" alt="Varasai Oxygen" height="120" class="mb-3"> -->
```

**In templates/base.html**, comment out:
```html
<!-- <img src="{{ url_for('static', filename='logo.jpg') }}" alt="Varasai Oxygen" height="60" class="me-2"> -->
```

### 6. Reload and Test
1. Save changes
2. Reload web app in PythonAnywhere Web tab
3. Test your site

## Debug Commands
```bash
# Check if files exist
ls -la ~/varasai-oxygen/static/

# Check file contents
file ~/varasai-oxygen/static/logo.jpg

# Test app without static files
cd ~/varasai-oxygen
python3.10 -c "from app import app; print('App works without static files')"
```

The app should work once static file mapping is correct or logo references are temporarily removed.