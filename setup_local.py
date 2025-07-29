#!/usr/bin/env python3
"""
Local Development Setup Script for Oxygen Cylinder Tracker
Automatically sets up the development environment, database, and imports data
"""

import os
import sys
import json
import subprocess

from pathlib import Path
from datetime import datetime
import uuid
import shutil

def print_status(message):
    """Print status message with checkmark"""
    print(f"✓ {message}")

def print_warning(message):
    """Print warning message"""
    print(f"⚠ {message}")

def print_error(message):
    """Print error message"""
    print(f"✗ {message}")

def run_command(cmd, check=True, capture_output=False):
    """Run a shell command"""
    try:
        if capture_output:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, check=check)
            return result.stdout.strip()
        else:
            subprocess.run(cmd, shell=True, check=check)
            return True
    except subprocess.CalledProcessError as e:
        if check:
            print_error(f"Command failed: {cmd}")
            print_error(f"Error: {e}")
            return False
        return False

def check_python_version():
    """Check if Python version is compatible"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print_error(f"Python 3.8+ required, found {version.major}.{version.minor}")
        return False
    print_status(f"Python {version.major}.{version.minor}.{version.micro} found")
    return True

def install_dependencies():
    """Install Python dependencies"""
    print_status("Installing Python dependencies...")
    
    # Install dependencies from pyproject.toml
    dependencies = [
        "flask", "flask-login", "flask-sqlalchemy", "gunicorn", 
        "pandas", "psycopg2-binary", "pyodbc", "werkzeug", 
        "oauthlib", "sendgrid", "reportlab", "openpyxl", 
        "sqlalchemy", "email-validator"
    ]
    
    # Check if uv is available for faster installation
    if run_command("uv --version", check=False, capture_output=True):
        print_status("Using uv for faster package installation...")
        deps_str = " ".join(dependencies)
        return run_command(f"uv pip install {deps_str}")
    else:
        print_status("Using pip for package installation...")
        deps_str = " ".join(dependencies)
        return run_command(f"pip install {deps_str}")

def setup_directories():
    """Create necessary directories"""
    directories = ["data", "backups", "templates", "static", "logs"]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print_status(f"Created directory: {directory}")

def setup_environment():
    """Set up environment variables"""
    env_file = ".env"
    
    # Generate random secrets if .env doesn't exist
    if not os.path.exists(env_file):
        print_status("Creating .env file with secure secrets...")
        
        import secrets
        flask_secret = secrets.token_hex(32)
        session_secret = secrets.token_hex(32)
        
        env_content = f"""# Environment variables for local development
# IMPORTANT: This application requires PostgreSQL database
# Set DATABASE_URL to your PostgreSQL connection string
# Example: DATABASE_URL=postgresql://username:password@localhost:5432/oxygen_tracker

FLASK_SECRET_KEY={flask_secret}
SESSION_SECRET={session_secret}
FLASK_ENV=development
DEBUG=True

# PostgreSQL connection required - uncomment and configure:
# DATABASE_URL=postgresql://username:password@localhost:5432/oxygen_tracker
"""
        
        with open(env_file, 'w') as f:
            f.write(env_content)
        
        print_status("Environment file created with secure secrets")
        print_warning("You must set DATABASE_URL to a PostgreSQL connection string")
    else:
        print_status("Environment file already exists")

def check_postgresql_setup():
    """Check PostgreSQL database setup and configuration"""
    print_status("Checking PostgreSQL database configuration...")
    
    # Check if DATABASE_URL is set
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        print_error("DATABASE_URL environment variable not set")
        print_warning("This application requires PostgreSQL database")
        print_warning("Please set DATABASE_URL in your .env file")
        print_warning("Example: DATABASE_URL=postgresql://username:password@localhost:5432/oxygen_tracker")
        return False
    
    if database_url.startswith('sqlite:'):
        print_error("SQLite databases are no longer supported")
        print_warning("This application requires PostgreSQL for data consistency")
        print_warning("Please update DATABASE_URL to use PostgreSQL")
        return False
    
    print_status(f"PostgreSQL database configured: {database_url.split('@')[0] + '@****' if '@' in database_url else database_url}")
    
    # Test database connection
    try:
        import psycopg2
        from urllib.parse import urlparse
        
        result = urlparse(database_url)
        conn = psycopg2.connect(
            database=result.path[1:],
            user=result.username,
            password=result.password,
            host=result.hostname,
            port=result.port
        )
        conn.close()
        print_status("Database connection test successful")
        return True
    except ImportError:
        print_warning("psycopg2 not installed - database connection cannot be tested")
        print_warning("Install with: pip install psycopg2-binary")
        return True  # Continue setup, will be tested at runtime
    except Exception as e:
        print_error(f"Database connection failed: {e}")
        print_warning("Please verify your PostgreSQL database is running and accessible")
        return False


def check_data_migration():
    """Check if data migration is needed from JSON files"""
    data_dir = Path("data")
    
    if not data_dir.exists():
        print_status("No data directory found - fresh installation")
        return
    
    json_files = list(data_dir.glob("*.json"))
    if not json_files:
        print_status("No JSON files found for migration")
        return
    
    print_status(f"Found {len(json_files)} JSON files available for migration")
    print_warning("To migrate existing JSON data to PostgreSQL:")
    print_warning("1. Ensure your PostgreSQL database is running")
    print_warning("2. Use the web application's Import Data feature")
    print_warning("3. Or use the import_from_json.py script")
    print_warning("4. JSON files will be automatically imported to PostgreSQL")

def create_admin_user():
    """Create default admin user in users.json"""
    users_file = "users.json"
    
    if os.path.exists(users_file):
        print_status("Users file already exists")
        return
    
    print_status("Creating default admin user...")
    
    from werkzeug.security import generate_password_hash
    
    admin_user = {
        "admin": {
            "id": str(uuid.uuid4()),
            "username": "admin",
            "password_hash": generate_password_hash("admin123"),
            "email": "admin@example.com",
            "role": "admin",
            "created_at": datetime.utcnow().isoformat()
        }
    }
    
    with open(users_file, 'w') as f:
        json.dump(admin_user, f, indent=2)
    
    print_status("Default admin user created (admin/admin123)")

def create_local_config():
    """Create local development configuration"""
    config_content = """# Local Development Configuration
# This file contains settings specific to local development

import os
from datetime import timedelta

class Config:
    # Basic Flask config
    SECRET_KEY = os.environ.get('FLASK_SECRET_KEY') or 'dev-secret-key'
    SESSION_PERMANENT = False
    PERMANENT_SESSION_LIFETIME = timedelta(hours=24)
    
    # Database config (PostgreSQL required)
    DATABASE_URL = os.environ.get('DATABASE_URL')
    
    # Development settings
    DEBUG = True
    TESTING = False
    
    # File upload settings
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    
    # Pagination
    ITEMS_PER_PAGE = 50
    
    # Backup settings
    BACKUP_DIRECTORY = 'backups'
    AUTO_BACKUP_INTERVAL = 14  # days
"""
    
    with open("config.py", "w") as f:
        f.write(config_content)
    
    print_status("Local configuration file created")

def main():
    """Main setup function"""
    print("🚀 Starting local development setup for Oxygen Cylinder Tracker...")
    print("⚠ IMPORTANT: This application now requires PostgreSQL database")
    print()
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Set up directories
    setup_directories()
    
    # Set up environment
    setup_environment()
    
    # Install dependencies
    if not install_dependencies():
        print_error("Failed to install dependencies")
        sys.exit(1)
    
    # Load environment variables
    from pathlib import Path
    env_file = Path(".env")
    if env_file.exists():
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip()
    
    # Check PostgreSQL setup
    if not check_postgresql_setup():
        print_error("PostgreSQL database setup failed")
        print_warning("Please configure DATABASE_URL in your .env file")
        sys.exit(1)
    
    # Check for data migration needs
    check_data_migration()
    
    # Create admin user
    create_admin_user()
    
    # Create local config
    create_local_config()
    
    print()
    print_status("🎉 Local setup completed successfully!")
    print()
    print("Next steps:")
    print("1. Ensure PostgreSQL database is running and accessible")
    print("2. Start the development server: python main.py")
    print("3. Open your browser to: http://localhost:5000")
    print("4. Login with admin/admin123")
    print("5. Change the admin password immediately")
    print("6. Use Import Data feature to migrate any existing JSON data")
    print()
    print("Database: PostgreSQL (see DATABASE_URL in .env)")
    print("Environment config: .env")
    print("Users file: users.json")
    print()

if __name__ == "__main__":
    main()