# Varasai Oxygen Cylinder Tracker - MySQL Edition

## Overview

Clean MySQL-only Flask application for oxygen cylinder rental management. Designed specifically for PythonAnywhere hosting with professional database backend.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Backend Architecture
- **Framework**: Flask with PyMySQL
- **Database**: MySQL only (removed all SQLite/PostgreSQL code)
- **Authentication**: Simple session-based login
- **File Structure**: Single app.py with all routes

### Core Features
1. **Customer Management**: List, search, and pagination
2. **Cylinder Tracking**: Inventory with status tracking
3. **Dashboard**: Overview with statistics
4. **Authentication**: admin/admin123 login

### MySQL Configuration
```python
MYSQL_CONFIG = {
    'host': os.environ.get('MYSQL_HOST', 'localhost'),
    'user': os.environ.get('MYSQL_USER', 'root'), 
    'password': os.environ.get('MYSQL_PASSWORD', ''),
    'database': os.environ.get('MYSQL_DATABASE', 'oxygen_tracker'),
    'charset': 'utf8mb4'
}
```

## Current Status

- **Database**: MySQL with complete table structure
- **Routes**: All template routes added (with placeholders for unimplemented features)
- **Templates**: Compatible with MySQL dictionary objects
- **Sample Data**: Available via sample_data.py for testing

## Changelog
- July 28, 2025: Complete refactor to MySQL-only architecture. Removed all SQLite, PostgreSQL, and duplicate database code. Consolidated into single app.py with MySQL backend. Added all missing routes for template compatibility, created sample_data.py for testing with realistic data. System now uses only MySQL with PyMySQL for better PythonAnywhere hosting compatibility.