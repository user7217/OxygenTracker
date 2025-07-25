# Varasai Oxygen Cylinder Tracker

A high-performance Flask web application for industrial gas cylinder management, featuring advanced deployment automation and cross-platform setup tools.

## Quick Start

### Local Development Setup

**Windows:**
```cmd
setup_local.bat
```

**Linux/macOS:**
```bash
./setup_local.sh
```

**Then start the server:**
```bash
python start_dev.py
```

Open http://localhost:5000 and login with `admin`/`admin123`

### Cloud Deployment

**Deploy to Fly.io:**
```bash
./deploy_to_fly.sh
```

**Windows users:**
```cmd
deploy_to_fly.bat
```

## Features

- **Customer Management**: Complete customer database with Access-compatible fields
- **Cylinder Tracking**: Advanced inventory management with rental history
- **Bulk Operations**: Multi-cylinder rental/return operations
- **Data Import**: MS Access database import functionality
- **Role-Based Access**: Admin, User, and Viewer roles
- **Export Options**: CSV and PDF reports
- **Mobile Optimized**: Responsive design for tablets and phones
- **Performance Optimized**: Handles 5000+ cylinders efficiently

## Technology Stack

- **Backend**: Flask, SQLAlchemy, PostgreSQL
- **Frontend**: Bootstrap 5, Jinja2 templates
- **Database**: PostgreSQL (production), SQLite (development)
- **Deployment**: Fly.io with automated scripts
- **Performance**: Optimized queries with database indexes

## Project Structure

```
oxygen-tracker/
├── app.py                  # Flask application configuration
├── main.py                 # Application entry point
├── routes.py               # All route handlers
├── auth_models.py          # User authentication
├── db_models.py            # Database models (PostgreSQL)
├── db_service.py           # Database service layer
├── models_postgres.py      # Legacy PostgreSQL models
├── instant_importer.py     # Data import utilities
├── setup_local.*           # Local development setup
├── deploy_to_fly.*         # Cloud deployment scripts
├── start_dev.py            # Development server starter
├── templates/              # HTML templates
├── static/                 # CSS, JS, images
└── data/                   # JSON data files
```

## Quick Operations

### Add Customer
Navigate to Customers → Add Customer

### Track Cylinders
Navigate to Cylinders → View all inventory with search and filters

### Bulk Operations
Customer Details → Bulk Cylinder Management

### Generate Reports
Reports → Export customers, cylinders, or rental data

### Import Data
Import → Upload MS Access database files

## Performance Features

- Database indexing on frequently queried fields
- Optimized sorting algorithms
- Paginated results for large datasets
- Simplified queries for better response times
- Performance monitoring built-in

## Security

- Role-based access control
- Secure password hashing
- Session management
- Environment variable configuration
- Production-ready security headers

## Support

- Default admin user: `admin` / `admin123` (change immediately)
- Local database: SQLite file `oxygen_tracker.db`
- Production database: PostgreSQL on Fly.io
- Logs available in application console

For detailed setup instructions, see README_LOCAL_SETUP.md

## License

Proprietary - Varasai Oxygen Management System