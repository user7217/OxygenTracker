# Local Development Setup Guide

## Prerequisites

1. **Python 3.8+** installed on your system
2. **PostgreSQL** database server running locally
3. **Git** (optional, for cloning)

## Step 1: Clone or Download the Project

```bash
git clone https://github.com/user7217/OxygenTracker.git
cd OxygenTracker
```

Or download and extract the project files.

## Step 2: Install Python Dependencies

```bash
# Create virtual environment (recommended)
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install required packages
pip install flask flask-sqlalchemy psycopg2-binary gunicorn werkzeug pandas reportlab
```

## Step 3: Set up PostgreSQL Database

1. **Install PostgreSQL** if not already installed:
   - Windows: Download from https://www.postgresql.org/download/windows/
   - macOS: `brew install postgresql` or download from website
   - Linux: `sudo apt-get install postgresql postgresql-contrib`

2. **Create a database:**
   ```bash
   # Connect to PostgreSQL
   psql -U postgres
   
   # Create database
   CREATE DATABASE oxygen_tracker;
   
   # Create user (optional)
   CREATE USER oxygen_user WITH PASSWORD 'your_password';
   GRANT ALL PRIVILEGES ON DATABASE oxygen_tracker TO oxygen_user;
   
   # Exit
   \q
   ```

## Step 4: Configure Environment Variables

Create a `.env` file in the project root:

```bash
# Database connection
DATABASE_URL=postgresql://postgres:your_password@localhost:5432/oxygen_tracker

# Or if you created a specific user:
# DATABASE_URL=postgresql://oxygen_user:your_password@localhost:5432/oxygen_tracker

# Session secret (generate a random string)
SESSION_SECRET=your-secret-key-here-make-it-long-and-random

# PostgreSQL individual settings (optional)
PGHOST=localhost
PGPORT=5432
PGDATABASE=oxygen_tracker
PGUSER=postgres
PGPASSWORD=your_password
```

## Step 5: Run the Application

### Option 1: Using Flask Development Server
```bash
python main.py
```

### Option 2: Using Gunicorn (Production-like)
```bash
gunicorn --bind 127.0.0.1:5000 --reload main:app
```

The application will be available at: http://localhost:5000

## Step 6: Import Your Existing Data (Optional)

### Option A: Import from JSON Files
If you have existing JSON data files (customers.json, cylinders.json, etc.):

```bash
# Run the JSON import utility
python import_from_json.py
```

This will automatically import your existing data into PostgreSQL.

### Option B: Import from Access Database
Use the Import tab in the web interface if you have existing Access database files.

## Step 7: Initial Setup

1. **Login with default admin account:**
   - Username: `admin`
   - Password: `admin123`

2. **Change the admin password** immediately after first login

## Database Migration

The application will automatically create all necessary PostgreSQL tables on first run. Your data structure includes:

- **Customers table**: Customer information with new field structure
- **Cylinders table**: Cylinder inventory with rental tracking
- **Rental History table**: Completed rental transactions
- **Users table**: Authentication (still uses JSON files)

## Troubleshooting

### Database Connection Issues
- Ensure PostgreSQL service is running
- Check your DATABASE_URL format
- Verify database credentials
- Make sure the database exists

### Import Issues
- MS Access import requires `pyodbc` and Access drivers
- On Windows: Install Microsoft Access Database Engine
- On Linux/macOS: Access import may not be available

### Port Already in Use
```bash
# Find process using port 5000
lsof -i :5000  # macOS/Linux
netstat -ano | findstr :5000  # Windows

# Kill the process or use a different port
gunicorn --bind 127.0.0.1:8000 --reload main:app
```

## File Structure

```
OxygenTracker/
├── main.py              # Application entry point
├── app.py               # Flask app configuration
├── routes.py            # All application routes
├── models_postgres.py   # PostgreSQL data models
├── db_models.py         # SQLAlchemy models
├── db_service.py        # Database service layer
├── auth_models.py       # User authentication (JSON)
├── templates/           # HTML templates
├── static/              # CSS, JS, images
├── data/                # JSON files (users only)
└── requirements.txt     # Python dependencies
```

## Production Deployment

For production deployment, consider:
- Using environment variables for all secrets
- Setting up SSL/TLS certificates
- Using a production WSGI server like Gunicorn with nginx
- Regular database backups
- Monitoring and logging