# Varasai Oxygen - Local Development Guide

## Quick Start

### Option 1: Using the enhanced runner
```bash
python run_local.py
```

### Option 2: Using the standard method
```bash
python main.py
```

### Option 3: Run diagnostics first
```bash
python test_local.py
```

## Access the Application

1. **Start the server** with one of the methods above
2. **Open your browser** and go to: `http://localhost:5000`
3. **Login page appears first** - this is normal!
4. **Use default credentials:**
   - Username: `admin`
   - Password: `admin123`
5. **Dashboard will appear** after successful login

## Common Issues & Solutions

### "Dashboard doesn't show up"
- **Cause**: The app redirects to login first (security feature)
- **Solution**: Complete the login process, then dashboard appears

### "Connection refused" or "Port already in use"
```bash
# Kill any existing processes on port 5000
lsof -ti:5000 | xargs kill -9
# Then restart the server
python main.py
```

### "Import errors" 
```bash
# Install missing dependencies
pip install flask werkzeug
```

### "Permission denied" errors
```bash
# Check directory permissions
chmod 755 data/
chmod 644 data/*.json
```

## Development Features

### Hot Reloading
- The server automatically restarts when you modify Python files
- Refresh your browser to see template changes

### Debug Mode
- Detailed error pages show in the browser
- Console shows request/response logs

### Data Persistence
- All data stored in JSON files in `data/` directory
- Easy to backup, reset, or transfer

## File Structure
```
varasai-oxygen/
├── main.py              # Main entry point
├── app.py               # Flask app configuration  
├── routes.py            # All URL routes
├── models.py            # Data models (Customer, Cylinder)
├── auth_models.py       # User authentication
├── templates/           # HTML templates
├── static/             # CSS, JS, images
└── data/               # JSON database files
```

## Default Login
- **Username**: admin
- **Password**: admin123
- **Role**: Administrator (full access)

## Next Steps After Login
1. **Dashboard**: Overview of your system
2. **Customers**: Add and manage customers  
3. **Cylinders**: Track oxygen cylinder inventory
4. **Bulk Operations**: Rent/return multiple cylinders
5. **Import Data**: Import from MS Access databases (optional)

## Need Help?
- Check the browser console for JavaScript errors
- Check the terminal for Python errors
- Use `python test_local.py` to diagnose issues