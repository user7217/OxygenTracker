# Oxygen Cylinder Tracker

A comprehensive industrial gas cylinder management web application built with Flask and PostgreSQL.

## Features

### Core Functionality
- **Customer Management**: Complete CRUD operations with Access-compatible field structure
- **Cylinder Inventory**: Advanced tracking with rental status, custom IDs, and bulk operations
- **Rental Management**: Real-time tracking with duration calculation and history
- **Search & Filter**: Global search across customers and cylinders with advanced filtering
- **Bulk Operations**: Multi-cylinder dispatch and return operations
- **Data Export**: CSV and PDF reports for customers, cylinders, and rental activities

### User Management
- **Role-Based Access**: Admin, User, and Viewer roles with different permissions
- **Secure Authentication**: Werkzeug password hashing and session management
- **User Interface**: Clean, responsive Bootstrap 5 design with mobile optimization

### Data Management
- **PostgreSQL Database**: Robust data storage with SQLAlchemy ORM
- **Data Import**: MS Access database import functionality with field mapping
- **Backup System**: Automatic data archiving and backup capabilities
- **Performance**: Optimized queries with pagination for large datasets

## Quick Start

### Prerequisites
- Python 3.11+
- PostgreSQL database
- Render account (for deployment)

### Local Development
1. Clone the repository
2. Set environment variables:
   - `DATABASE_URL`: PostgreSQL connection string
   - `SESSION_SECRET`: Secure session key
3. Install dependencies: `pip install -r requirements.txt`
4. Run: `python main.py`

### Deployment to Render
1. Push code to GitHub repository
2. Create PostgreSQL database on Render
3. Create web service with configuration from `render.yaml`
4. Set environment variables in Render dashboard
5. Deploy automatically via GitHub integration

See `RENDER_DEPLOYMENT.md` for detailed deployment instructions.

## Project Structure

```
├── app.py                 # Flask application factory
├── main.py               # Application entry point
├── routes.py             # Route definitions and logic
├── db_models.py          # SQLAlchemy database models
├── db_service.py         # Database service layer
├── auth_models.py        # User authentication system
├── email_service.py      # Email functionality
├── templates/            # Jinja2 HTML templates
├── static/              # CSS, JS, and assets
├── data/                # JSON data files
└── render.yaml          # Render deployment configuration
```

## Technology Stack

- **Backend**: Flask, SQLAlchemy, PostgreSQL
- **Frontend**: Jinja2, Bootstrap 5, Bootstrap Icons
- **Deployment**: Render.com with PostgreSQL
- **Authentication**: Custom user management with role-based access
- **Reports**: ReportLab for PDF generation
- **Email**: SendGrid integration for notifications

## Database Schema

### Tables
- **customers**: Customer information and contact details
- **cylinders**: Cylinder inventory with rental tracking
- **rental_history**: Complete audit trail of all rental activities

### Key Features
- Foreign key relationships for data integrity
- Indexed fields for performance optimization
- JSON fields for flexible data storage
- Automatic timestamp tracking

## Security

- Environment variable protection for secrets
- SQL injection protection via ORM
- Secure password hashing with salt
- Session-based authentication
- Role-based access control

## Performance

- Database connection pooling
- Pagination for large datasets
- Optimized queries with proper indexing
- Automatic data archiving system
- Gunicorn WSGI server for production

## Contributing

1. Follow the coding standards in `replit.md`
2. Add comprehensive comments to new code
3. Test database operations thoroughly
4. Update documentation for new features
5. Ensure mobile responsiveness for UI changes

## License

Proprietary software for industrial gas cylinder management.

## Support

For deployment and configuration support, refer to:
- `RENDER_DEPLOYMENT.md` for deployment instructions
- Application logs for debugging information
- Database logs in Render PostgreSQL dashboard