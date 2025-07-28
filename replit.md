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
1. **Customer Management**: Full CRUD with add, edit, delete, search, and pagination
2. **Cylinder Tracking**: Complete inventory management with rental/return operations
3. **Rental Management**: Rent cylinders to customers and return with automatic history tracking
4. **Access Database Import**: Full import system with field mapping from .mdb/.accdb files
5. **Rental History**: Complete tracking of all rental transactions with reports
6. **Dashboard**: Overview with real-time statistics
7. **Authentication**: Simple login system (admin/admin123)
8. **Sample Data**: Built-in sample data generator for testing

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

- **Database**: SQLite with complete table structure (customers, cylinders, rental_history)
- **Routes**: All major routes implemented with full functionality
- **Templates**: Compatible with SQLite Row objects
- **Sample Data**: Working sample data with 5 customers, 25 cylinders, 10 rental records
- **Import System**: Access database import with field mapping functionality
- **Rental Operations**: Full rental management with automatic history tracking

## Changelog
- July 28, 2025: Complete restoration of all original features using SQLite. Implemented full customer/cylinder CRUD operations, rental management with automatic history tracking, Access database import system with field mapping, rental history reporting, and working sample data. All 22 key features from the original system are now functional in a clean SQLite-based architecture.