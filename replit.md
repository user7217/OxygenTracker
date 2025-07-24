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
- **Primary Storage**: PostgreSQL database for all operational data
- **Database Tables**:
  - `customers`: Customer information with new field structure
  - `cylinders`: Cylinder inventory data with rental tracking
  - `rental_history`: Completed rental transactions
- **Authentication**: JSON file (`users.json`) for user authentication only
- **File Structure**: SQLAlchemy models with service layer architecture

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
- July 24, 2025: Completed full migration from JSON to PostgreSQL database. Migrated 249 customers, 6774 cylinders, and rental history data. Removed all JSON data files except users.json for authentication. Fixed customer table sorting by active dispatches, optimized performance by reducing queries from 10K to 5K records, fixed foreign key constraints for cylinder returns, and improved cylinder sorting by rental duration. Added comprehensive JSON import utility for easy data migration. System now fully PostgreSQL-based with significant performance improvements.
- July 24, 2025: Created dedicated Rental History system for 6-month completed transactions. Added new rental_history import type in instant importer that specifically imports completed transactions (with return dates) from the past 6 months. Created separate rental transactions model and dedicated rental history page with search/filter capabilities. Simplified transaction importer to focus on basic customer-cylinder linking. Added rental history navigation link in main menu. System now supports four import types: customers, cylinders, transactions (linking), and rental_history (6-month completed rentals).
- July 23, 2025: Updated rental duration filters in cylinder table to use clearer time ranges: "Under 1 Month", "1-3 Months", "3-6 Months", "6-12 Months", and "Over 12 Months" instead of minimum thresholds. Removed date filtering from transaction imports to process ALL historical data instead of past year only. Fixed AccessConnector database connection errors by properly using cursor objects instead of connection objects. Enhanced instant import system to handle complete historical datasets without any date restrictions.
- July 22, 2025: Fixed critical Access database connector indentation errors that prevented application startup. Enhanced transaction import to handle large datasets (292k+ rows) by increasing error threshold from 1000 to 5000, adding 50% skip limit to prevent endless processing, and implementing comprehensive error reporting with detailed statistics. Made cylinder type and size optional during imports with intelligent defaults (Medical Oxygen, 40L) to reduce import failures and improve data flexibility. Updated field mapping interface to show optional status for type and size fields.
- July 21, 2025: Updated both standalone importer and main web application to require custom ID (renamed from "custom_id" to just "id") for cylinders while making serial number optional. This change affects both MS Access import functionality and manual cylinder creation/editing forms. Custom IDs like "A1", "B2", "001" are now mandatory for easier bulk operations, while manufacturer serial numbers are preserved when available but not required. Updated all templates, routes, validation logic, and import documentation to reflect new requirements.
- July 21, 2025: Added comprehensive data management system with complete data reset functionality for admin users and automatic backup system. Reset feature requires confirmation text "RESET ALL DATA" and creates backup before deletion. Auto-backup system runs every 2 weeks in background thread, creating timestamped backups in backups/ directory. Manual backup option available for admins. All backup and reset functions are admin-only with proper security checks. Admin navigation menu expanded with "Create Backup" and "Reset Data" options in both desktop and mobile views.
- July 20, 2025: Major UI cleanup and terminology standardization: removed system-generated ID display from frontend while preserving backend functionality, changed all "Custom ID" references to "ID" throughout templates, removed serial number column from cylinders table keeping only ID column that shows custom ID or serial number, eliminated all blue highlights replacing with clean black text styling, replaced location column with customer name column for better visibility, updated all frontend terminology from "rental/rented" to "dispatch/dispatched" while maintaining backend compatibility, and streamlined bulk cylinder management page by removing cylinders table section and adding custom date picker functionality with dynamic labeling.
- July 19, 2025: Enhanced bulk cylinder management page with comprehensive redesign: moved cylinders list to top showing all cylinder information in table format, relocated dispatch/return form below cylinders list, added custom date picker for both dispatch and return operations, changed "rental" terminology to "dispatched" throughout frontend while maintaining backend compatibility, updated customer dropdown to use new field structure (customer_name, customer_phone), added JavaScript for dynamic date label switching, and integrated custom date handling in backend processing for accurate date tracking.
- July 17, 2025: Fixed rental duration filtering system to use accurate month calculations instead of approximate 30-day conversions. Added get_rental_months() method for proper month-based filtering. Updated cylinder display to show both months and days for rental duration clarity. Improved filter dropdown labels to show exact day equivalents. Changed badge colors to use month-based thresholds (3+ months warning, 6+ months danger). Updated all export functions to use new customer field names (customer_no, customer_name, customer_email, customer_phone, customer_address, customer_city, customer_state, customer_apgst, customer_cst) for both CSV and PDF exports with backward compatibility.
- July 17, 2025: Implemented pagination system for cylinders page to handle 5000+ cylinders efficiently. Added configurable items per page (25, 50, 100, 200), navigation controls with previous/next buttons, page number display, and item count information. Pagination preserves all search filters and sorting options for seamless user experience. Significantly improves loading performance for large datasets.
- July 17, 2025: Enhanced transaction import system with comprehensive cylinder and customer relationship management. Transaction imports now automatically update cylinder locations to customer addresses, handle rental status based on return date presence, and maintain complete customer information on cylinders. Added rent_cylinder_with_location method for full address tracking. System intelligently determines rental status: if return_date is empty, cylinder remains "rented" with customer location; if return_date exists, cylinder is returned to "available" status at warehouse. All customer fields (name, phone, address, city, state) are tracked on rented cylinders.
- July 17, 2025: Implemented transaction import system for linking customers and cylinders via foreign keys. Added comprehensive transaction import functionality using customer_no and cylinder_no as foreign keys to establish relationships between customers and cylinders. Transaction imports support rental/return operations with automatic status updates and date tracking. Updated field mapping interface to support transaction data imports alongside customer and cylinder data.
- July 17, 2025: Updated customer data structure to match Access database format with new required fields (customer_no, customer_name, customer_address, customer_city, customer_state, customer_phone) and optional fields (customer_apgst, customer_cst). Migrated existing customer data to new structure with backup preservation. Updated customer templates and forms to display and collect new fields.
- July 17, 2025: Made email optional for customers in both import and manual entry. Set default location to "Warehouse" and status to "Available" for cylinders during Access import. Reduced required fields for imports to improve flexibility. Added user preference for comprehensive code commenting.
- July 16, 2025: Added responsive mobile navigation with hamburger menu for mobile devices. Mobile navigation includes collapsible menu with all navigation items, mobile-optimized search functionality, user info display with role badges, and admin options for user management. Desktop layout remains unchanged while mobile users get a clean, touch-friendly hamburger menu experience.
- July 16, 2025: Implemented comprehensive three-tier role-based permission system: Admin (full access including user management, data exports, CRUD operations), User (cylinder rental/return operations and bulk management), and Viewer (read-only access to all data). Updated all templates to hide inappropriate buttons and menu items based on user roles. Navigation automatically adapts to show role-appropriate options with Reports and Import tools restricted to admins only.
- July 16, 2025: Added comprehensive PDF export system to complement existing CSV exports. Users can now export customers, cylinders, and rental activities in professional PDF format with formatted tables, company branding, and status breakdowns. PDF reports feature clean layouts with proper headers, date stamps, and organized data presentation. Both CSV and PDF options are available side-by-side in the Reports section for maximum flexibility.
- July 16, 2025: Enhanced cylinder type system with type-specific serial numbers. Added rental date picker to rent cylinder modal for consistent date tracking. Updated cylinder types to include "Carbon Dioxide" alongside existing options. Serial numbers now dynamically generate with appropriate prefixes: OXY-001 (Oxygen), CO2-001 (Carbon Dioxide), ARG-001 (Argon), N2-001 (Nitrogen), AIR-001 (Compressed Air), GAS-001 (Other). Removed serial number field from add/edit cylinder forms since serial numbers are display-only and generated dynamically. Both rent and return operations now support custom date selection.
- July 15, 2025: Added comprehensive data export system with separate Reports tab. Users can now export customers, cylinders, rental activities, and complete database to CSV files. Monthly reports available with different report types (complete, rentals, customers, cylinders). All exports include timestamps and proper CSV formatting for Excel compatibility.
- July 15, 2025: Added cylinder type sorting feature with CO2, Argon, and other gas types. Users can now filter cylinders by type (Medical Oxygen, Industrial Oxygen, CO2, Argon, Nitrogen, Compressed Air) in the cylinders page. Also implemented dynamic serial number generation (OXY-001, OXY-002, etc.) that displays clean sequential numbers without storing them in the database.
- July 15, 2025: Changed cylinders page from card-based layout to table-based list format similar to customers page. Users can now see all cylinder information in a clean, organized table with better data visibility and actions grouped in button groups.
- July 13, 2025: Added custom cylinder ID feature for easier bulk operations. Users can now set memorable custom IDs (like "A1", "B2", "001") when creating or editing cylinders. Bulk rental system now accepts system IDs, custom IDs, or serial numbers, making it much easier to perform bulk operations without memorizing system-generated IDs.
- July 13, 2025: Fixed blue box cylinder management modal flickering issue by replacing modal approach with dedicated page. Cylinder management now opens on a separate page (/customers/{id}/bulk_cylinders) with no modals, animations, or JavaScript interactions - completely eliminating flickering problems. Page shows current rentals and provides clean form for bulk operations.
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
Code style: Add comprehensive comments to all code files going forward for better maintainability and understanding.
Dashboard design: Clean and simple dashboard with core functionality only. Complex tools (bulk operations, barcode generator, calculator) removed. Metrics moved to separate dedicated tab for users who want detailed analytics.
Email functionality: SendGrid integration added for sending admin statistics reports via email. Accessible from metrics page for administrators.
Cylinder management: Enhanced with customer-wise filtering, rental tracking with start dates and duration calculation, touch-screen optimization with larger fonts and buttons for mobile/tablet use. Card-based layout for better touch interaction.
Data archiving: Automatic archiving system for old data (6+ months) to maintain performance. Admin-only feature with backup file creation.
Rental duration filtering: Added 1, 6, and 12 month filters to identify long-term rentals in cylinders view.
Data import: Email is optional for customers, location defaults to "Warehouse" for cylinders, status defaults to "Available" for cylinders when importing from Access databases.