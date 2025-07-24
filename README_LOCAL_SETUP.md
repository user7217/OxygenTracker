# Local Development Setup Guide

This guide helps you set up the Oxygen Cylinder Tracker for local development with automatic database creation and data importing.

## Quick Setup

### Option 1: Automated Setup (Recommended)

**Windows:**
```cmd
setup_local.bat
```

**Linux/macOS:**
```bash
./setup_local.sh
```

**Python (Any OS):**
```bash
python setup_local.py
```

### Option 2: Manual Setup

1. **Install dependencies:**
   ```bash
   pip install -r pyproject.toml
   ```

2. **Run setup:**
   ```bash
   python setup_local.py
   ```

## What the Setup Script Does

✅ **Checks Python version** (3.8+ required)  
✅ **Installs dependencies** (using uv if available, otherwise pip)  
✅ **Creates directories** (data, backups, templates, static, logs)  
✅ **Sets up environment** (.env file with secure secrets)  
✅ **Creates SQLite database** with all required tables  
✅ **Imports JSON data** from data/ directory automatically  
✅ **Creates admin user** (admin/admin123)  
✅ **Generates config files** for local development  

## Starting the Development Server

### Quick Start:
```bash
python start_dev.py
```

### Manual Start:
```bash
python main.py
```

## Data Import

The setup automatically imports data from these JSON files in the `data/` directory:

- `customers.json` - Customer information
- `cylinders.json` - Cylinder inventory
- `rental_history.json` - Historical rental transactions

### Data File Format Examples:

**customers.json:**
```json
[
  {
    "id": "unique-id",
    "customer_no": "C001",
    "customer_name": "John Doe",
    "customer_email": "john@example.com",
    "customer_phone": "555-0123",
    "customer_address": "123 Main St",
    "customer_city": "Anytown",
    "customer_state": "State"
  }
]
```

**cylinders.json:**
```json
[
  {
    "id": "unique-id",
    "custom_id": "A001",
    "serial_number": "SN123456",
    "type": "Medical Oxygen",
    "size": "40L",
    "status": "available",
    "location": "Warehouse"
  }
]
```

## Database Configuration

### SQLite (Default - Local Development)
- Database file: `oxygen_tracker.db`
- Connection: `sqlite:///oxygen_tracker.db`
- Automatic table creation
- No additional setup required

### PostgreSQL (Production)
Update `.env` file:
```
DATABASE_URL=postgresql://user:password@localhost:5432/oxygen_tracker
```

## Environment Variables

The setup creates a `.env` file with:

```
FLASK_SECRET_KEY=<randomly-generated>
SESSION_SECRET=<randomly-generated>
FLASK_ENV=development
DATABASE_URL=sqlite:///oxygen_tracker.db
```

## Default Admin User

- **Username:** admin
- **Password:** admin123
- **Role:** Administrator

**IMPORTANT:** Change the password immediately after first login!

## File Structure After Setup

```
oxygen-tracker/
├── data/                    # JSON data files (imported automatically)
├── backups/                 # Database backups
├── templates/               # HTML templates
├── static/                  # CSS, JS, images
├── logs/                    # Application logs
├── oxygen_tracker.db        # SQLite database
├── users.json              # User authentication file
├── .env                    # Environment variables
├── config.py               # Local configuration
└── setup_local.py          # Setup script
```

## Development Workflow

1. **Initial setup:**
   ```bash
   ./setup_local.sh  # or setup_local.bat on Windows
   ```

2. **Start development server:**
   ```bash
   python start_dev.py
   ```

3. **Access application:**
   - URL: http://localhost:5000
   - Login: admin/admin123

4. **Make changes and test:**
   - Files auto-reload on changes
   - Database persists between restarts

## Troubleshooting

### Python Version Issues
```bash
python --version  # Should be 3.8+
```

### Dependency Installation Fails
```bash
# Try upgrading pip first
pip install --upgrade pip
pip install -r pyproject.toml
```

### Database Issues
```bash
# Remove and recreate database
rm oxygen_tracker.db
python setup_local.py
```

### Permission Issues (Linux/macOS)
```bash
chmod +x setup_local.sh
chmod +x setup_local.py
```

### Port Already in Use
```bash
# Find and kill process using port 5000
lsof -ti:5000 | xargs kill -9  # macOS/Linux
netstat -ano | findstr :5000   # Windows
```

## Advanced Configuration

### Custom Database Location
Edit `.env`:
```
DATABASE_URL=sqlite:///path/to/custom.db
```

### Custom Port
Edit `start_dev.py` or set environment variable:
```
PORT=8080
```

### Debug Mode
Already enabled in development. To disable:
```python
app.run(debug=False)
```

## Data Migration from Production

To migrate data from a production PostgreSQL database:

1. **Export data from production:**
   ```sql
   COPY customers TO '/tmp/customers.csv' CSV HEADER;
   COPY cylinders TO '/tmp/cylinders.csv' CSV HEADER;
   ```

2. **Convert CSV to JSON** (create conversion script if needed)

3. **Place JSON files in data/ directory**

4. **Run setup script** to import automatically

## Performance Notes

- SQLite is suitable for development and small deployments
- For production, use PostgreSQL for better performance
- Database file grows with data - monitor size
- Regular backups are created automatically

## Security Notes

- Default secrets are randomly generated
- SQLite file should not be committed to version control
- Change admin password immediately
- Use environment variables for sensitive configuration

## Support

Common issues and solutions:

1. **"Module not found" errors:** Run `pip install -r pyproject.toml`
2. **"Permission denied" errors:** Check file permissions
3. **"Port in use" errors:** Kill existing processes or use different port
4. **Database corruption:** Delete `.db` file and run setup again

The setup script handles most common issues automatically and provides clear error messages for manual resolution.