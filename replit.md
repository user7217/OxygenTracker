# Oxygen Cylinder Tracker - Compressed replit.md

## Overview

The Oxygen Cylinder Tracker is a web-based application built with Flask for managing oxygen cylinder inventory and customer relationships. It provides functionality for tracking cylinders, managing customers, importing data from MS Access databases, and user authentication. The system's primary vision is to offer a robust and portable solution for inventory management, focusing on efficiency and user-friendliness.

## User Preferences

Preferred communication style: Simple, everyday language.
Code style: Add comprehensive comments to all code files going forward for better maintainability and understanding.
Dashboard design: Clean and simple dashboard with core functionality only. Complex tools (bulk operations, barcode generator, calculator) removed. Metrics moved to separate dedicated tab for users who want detailed analytics.
Email functionality: SendGrid integration added for sending admin statistics reports via email. Accessible from metrics page for administrators.
Cylinder management: Enhanced with customer-wise filtering, rental tracking with start dates and duration calculation, touch-screen optimization with larger fonts and buttons for mobile/tablet use. Card-based layout for better touch interaction.
Data archiving: Automatic archiving system for old data (6+ months) to maintain performance. Admin-only feature with backup file creation.
Rental duration filtering: Added 1, 6, and 12 month filters to identify long-term rentals in cylinders view.
Data import: Email is optional for customers, location defaults to "Warehouse" for cylinders, status defaults to "Available" for cylinders when importing from Access databases.
Deployment preference: Render.com platform with PostgreSQL hosting for production deployment. All local setup files removed in favor of cloud deployment configuration.

## System Architecture

### Frontend
- **Framework**: Jinja2 (server-side rendered HTML)
- **UI Framework**: Bootstrap 5 (dark theme, responsive design)
- **Icons**: Bootstrap Icons
- **JavaScript**: Minimal client-side for Bootstrap components

### Backend
- **Framework**: Flask (Python)
- **Application Structure**: Modular design (routes, models, utilities)
- **Session Management**: Flask sessions with secret key
- **Middleware**: ProxyFix for reverse proxy headers

### Data Storage
- **Primary Storage**: PostgreSQL database exclusively.
    - Tables: `customers`, `cylinders`, `rental_history`
- **Authentication**: `users.json` for user authentication only.
- **ORM**: SQLAlchemy with service layer architecture.
- **Environment**: Requires `DATABASE_URL` environment variable.

### Deployment
- **Platform**: Render.com with PostgreSQL hosting
- **Configuration**: `render.yaml`, `Procfile`, `runtime.txt`
- **Dependencies**: Managed via `pyproject.toml` and `requirements.txt`
- **Database**: PostgreSQL on Render with automatic SSL and backups

### Key Features
- **Authentication**: Custom `UserManager` with role-based access control (Admin, User, Viewer), Werkzeug password hashing (scrypt), session-based authentication.
- **Data Models**: SQLAlchemy models for Customers, Cylinders, Rental History.
- **Data Import**: MS Access integration via `pyodbc`, interactive field mapping, data validation, import preview. Supports customer, cylinder, transaction, and 6-month completed rental history imports.
- **CRUD Operations**: For customers and cylinders.
- **Search**: Global search.
- **Reporting**: CSV and PDF export for customers, cylinders, and rental activities.
- **Bulk Operations**: Bulk cylinder dispatch/return, custom ID support for cylinders, comprehensive data reset with backup, automatic backup system.
- **UI/UX**: Table-based cylinder view, responsive mobile navigation (hamburger menu), consistent terminology (`dispatch/dispatched`), dynamic serial number generation based on cylinder type.
- **Cylinder Management**: Rental tracking with calculated duration, type-specific serial numbers, custom date selection for rent/return, pagination for large datasets.
- **Customer Data**: Updated structure to match Access database (e.g., `customer_no`, `customer_name`, `customer_address`).
- **Role-Based Permissions**: Admin (full access), User (rental/return, bulk management), Viewer (read-only).

## External Dependencies

### Python Packages
- Flask
- Werkzeug
- pyodbc (optional, for MS Access import)
- pandas (optional, for imports)

### Frontend Libraries
- Bootstrap 5 (via CDN)
- Bootstrap Icons (via CDN)
- Custom CSS (`static/style.css`)

### Other
- MS Access driver (for import functionality)
- PostgreSQL database
- SendGrid (for email statistics reports)