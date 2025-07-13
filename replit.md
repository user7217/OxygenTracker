# Oxygen Cylinder Tracker - System Architecture

## Overview

The Oxygen Cylinder Tracker is a web-based application built with Flask for managing oxygen cylinder inventory and customer relationships. The system provides functionality for tracking cylinders, managing customers, importing data from MS Access databases, and user authentication. It uses a file-based JSON storage system for simplicity and portability.

## System Architecture

### Frontend Architecture
- **Framework**: Server-side rendered HTML templates using Jinja2
- **UI Framework**: Bootstrap 5 with dark theme
- **Icons**: Bootstrap Icons
- **Responsive Design**: Mobile-first approach with responsive grid system
- **JavaScript**: Minimal client-side JavaScript, primarily for Bootstrap components

### Backend Architecture
- **Framework**: Flask (Python web framework)
- **Application Structure**: Modular design with separate files for routes, models, and utilities
- **Session Management**: Flask sessions with secret key configuration
- **Middleware**: ProxyFix for handling reverse proxy headers

### Data Storage Solutions
- **Primary Storage**: JSON files stored in local `data/` directory
- **Database Files**:
  - `customers.json`: Customer information
  - `cylinders.json`: Cylinder inventory data
  - `users.json`: User authentication data
- **File Structure**: Each model uses a JSONDatabase base class for consistent file operations

## Key Components

### Authentication System
- **User Management**: Custom UserManager class with role-based access control
- **Password Security**: Werkzeug password hashing (scrypt algorithm)
- **Session-based Authentication**: Login decorators for route protection
- **Default Admin**: Automatically creates admin user (admin/admin123)

### Data Models
- **JSONDatabase**: Base class for file-based data operations
- **Customer Model**: Manages customer information with unique ID generation
- **Cylinder Model**: Manages cylinder inventory with status tracking
- **User Model**: Handles user authentication and role management

### Data Import System
- **MS Access Integration**: AccessConnector class using pyodbc
- **Field Mapping**: Interactive field mapping interface for data import
- **Data Validation**: Duplicate checking and data transformation
- **Preview Functionality**: Table structure and data preview before import

### Route Structure
- **Authentication Routes**: Login, logout, user management
- **CRUD Operations**: Create, read, update, delete for customers and cylinders
- **Search Functionality**: Global search across customers and cylinders
- **Import Workflow**: Multi-step data import process

## Data Flow

### Authentication Flow
1. User accesses protected route
2. Login decorator checks session
3. UserManager validates user credentials
4. Session established with user ID and role
5. Role-based access control applied

### Data Management Flow
1. User submits form data via HTTP POST
2. Route handler validates input
3. Model class processes data with unique ID generation
4. JSONDatabase saves data to file
5. Success/error messages displayed via Flask flash messages

### Import Workflow
1. User uploads MS Access file
2. AccessConnector establishes database connection
3. System displays available tables
4. User selects table and target data type
5. Field mapping interface presented
6. User confirms field mappings
7. Data imported with duplicate checking
8. Import results displayed

## External Dependencies

### Required Python Packages
- **Flask**: Web framework
- **Werkzeug**: WSGI utilities and security
- **pyodbc**: MS Access database connectivity (optional)
- **pandas**: Data manipulation for imports (optional)

### Optional Dependencies
- MS Access driver installation required for import functionality
- Graceful degradation when dependencies unavailable

### Frontend Dependencies
- **Bootstrap 5**: CSS framework via CDN
- **Bootstrap Icons**: Icon library via CDN
- **Custom CSS**: Additional styling in static/style.css

## Deployment Strategy

### Local Development
- **Entry Point**: main.py runs Flask development server
- **Configuration**: Environment variables for session secrets
- **Debug Mode**: Enabled for development with hot reload

### Production Considerations
- **WSGI Server**: Designed for deployment with Gunicorn or uWSGI
- **Static Files**: Served via Flask in development, reverse proxy in production
- **Data Persistence**: JSON files provide simple backup and migration
- **Security**: Session secret should be set via environment variable

### File Structure Requirements
- `data/` directory must be writable for JSON file storage
- Templates and static files served from respective directories
- Import functionality requires temporary file storage

## Changelog
- July 13, 2025: Fixed blue box cylinder management modal in customers page - resolved JavaScript errors, customer ID extraction issues, and modal flickering problems. Modal now opens smoothly and allows proper cylinder rental/return operations.
- July 12, 2025: Fixed PythonAnywhere deployment issues with Flask url_for() configuration and static file handling. Updated WSGI configuration and app.py for proper URL building.
- July 12, 2025: Updated branding from "Oxygen Cylinder Tracker" to "Varasai Oxygen" with custom logo implementation in header navigation, favicon, and dashboard page
- July 9, 2025: Enhanced rental management system with comprehensive customer rental tracking, bulk cylinder operations, custom rental date selection, and detailed cylinder rental history modals in customer page
- July 9, 2025: Added bulk cylinder management with text box input, enhanced touch-screen optimization, automatic date tracking for borrowed/returned cylinders, default "Warehouse" location for new cylinders, customer selection dropdown for rented cylinders
- June 30, 2025: Initial setup

## GitHub Integration
- Repository: github.com/user7217/OxygenTracker
- Setup script: `./setup_git.sh` - Initial connection to GitHub
- Push script: `./push_to_github.sh` - Quick updates to repository

## User Preferences

Preferred communication style: Simple, everyday language.
Dashboard design: Clean and simple dashboard with core functionality only. Complex tools (bulk operations, barcode generator, calculator) removed. Metrics moved to separate dedicated tab for users who want detailed analytics.
Email functionality: SendGrid integration added for sending admin statistics reports via email. Accessible from metrics page for administrators.
Cylinder management: Enhanced with customer-wise filtering, rental tracking with start dates and duration calculation, touch-screen optimization with larger fonts and buttons for mobile/tablet use. Card-based layout for better touch interaction.
Data archiving: Automatic archiving system for old data (6+ months) to maintain performance. Admin-only feature with backup file creation.
Rental duration filtering: Added 1, 6, and 12 month filters to identify long-term rentals in cylinders view.