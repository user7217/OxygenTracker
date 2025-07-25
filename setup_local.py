#!/usr/bin/env python3
"""
Local Development Setup Script for Oxygen Cylinder Tracker
Automatically sets up the development environment, database, and imports data
"""

import os
import sys
import json
import subprocess
import sqlite3
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
FLASK_SECRET_KEY={flask_secret}
SESSION_SECRET={session_secret}
FLASK_ENV=development
DATABASE_URL=sqlite:///oxygen_tracker.db
DEBUG=True
"""
        
        with open(env_file, 'w') as f:
            f.write(env_content)
        
        print_status("Environment file created with secure secrets")
    else:
        print_status("Environment file already exists")

def create_sqlite_database():
    """Create SQLite database for local development"""
    db_path = "oxygen_tracker.db"
    
    if os.path.exists(db_path):
        backup_path = f"oxygen_tracker_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
        shutil.copy2(db_path, backup_path)
        print_status(f"Existing database backed up to: {backup_path}")
    
    print_status("Creating SQLite database tables...")
    
    # Create database schema
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create customers table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS customers (
            id TEXT PRIMARY KEY,
            customer_no TEXT UNIQUE,
            customer_name TEXT NOT NULL,
            customer_email TEXT,
            customer_phone TEXT,
            customer_address TEXT,
            customer_city TEXT,
            customer_state TEXT,
            customer_apgst TEXT,
            customer_cst TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Create cylinders table with performance indexes
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS cylinders (
            id TEXT PRIMARY KEY,
            custom_id TEXT UNIQUE,
            serial_number TEXT,
            type TEXT DEFAULT 'Medical Oxygen',
            size TEXT DEFAULT '40L',
            status TEXT DEFAULT 'available',
            location TEXT DEFAULT 'Warehouse',
            rented_to TEXT,
            customer_name TEXT,
            customer_email TEXT,
            customer_phone TEXT,
            customer_no TEXT,
            customer_city TEXT,
            customer_state TEXT,
            date_borrowed TIMESTAMP,
            rental_date TIMESTAMP,
            date_returned TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (rented_to) REFERENCES customers (id)
        )
    """)
    
    # Create performance indexes
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_cylinders_status ON cylinders (status)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_cylinders_rented_to ON cylinders (rented_to)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_cylinders_custom_id ON cylinders (custom_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_cylinders_date_borrowed ON cylinders (date_borrowed)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_customers_name ON customers (customer_name)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_customers_no ON customers (customer_no)")
    
    # Create rental_history table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS rental_history (
            id TEXT PRIMARY KEY,
            cylinder_id TEXT,
            customer_id TEXT,
            customer_name TEXT,
            customer_no TEXT,
            cylinder_custom_id TEXT,
            rental_date TIMESTAMP,
            return_date TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (cylinder_id) REFERENCES cylinders (id),
            FOREIGN KEY (customer_id) REFERENCES customers (id)
        )
    """)
    
    conn.commit()
    conn.close()
    
    print_status("SQLite database created successfully")

def import_json_data():
    """Import data from JSON files in data directory"""
    data_dir = Path("data")
    
    if not data_dir.exists():
        print_warning("No data directory found, skipping data import")
        return
    
    json_files = list(data_dir.glob("*.json"))
    if not json_files:
        print_warning("No JSON files found in data directory")
        return
    
    print_status(f"Found {len(json_files)} JSON files to import")
    
    conn = sqlite3.connect("oxygen_tracker.db")
    cursor = conn.cursor()
    
    # Import customers
    customers_file = data_dir / "customers.json"
    if customers_file.exists():
        print_status("Importing customers...")
        with open(customers_file, 'r', encoding='utf-8') as f:
            customers_data = json.load(f)
        
        imported_count = 0
        for customer_data in customers_data:
            try:
                # Check if customer already exists
                cursor.execute("SELECT id FROM customers WHERE customer_no = ?", 
                             (customer_data.get('customer_no'),))
                if cursor.fetchone():
                    continue
                
                customer_id = customer_data.get('id', str(uuid.uuid4()))
                cursor.execute("""
                    INSERT INTO customers (
                        id, customer_no, customer_name, customer_email, customer_phone,
                        customer_address, customer_city, customer_state, customer_apgst, customer_cst
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    customer_id,
                    customer_data.get('customer_no', ''),
                    customer_data.get('customer_name', customer_data.get('name', '')),
                    customer_data.get('customer_email', customer_data.get('email', '')),
                    customer_data.get('customer_phone', customer_data.get('phone', '')),
                    customer_data.get('customer_address', customer_data.get('address', '')),
                    customer_data.get('customer_city', customer_data.get('city', '')),
                    customer_data.get('customer_state', customer_data.get('state', '')),
                    customer_data.get('customer_apgst', ''),
                    customer_data.get('customer_cst', '')
                ))
                imported_count += 1
            except Exception as e:
                print_warning(f"Error importing customer {customer_data.get('customer_name', 'Unknown')}: {e}")
        
        conn.commit()
        print_status(f"Imported {imported_count} customers")
    
    # Import cylinders
    cylinders_file = data_dir / "cylinders.json"
    if cylinders_file.exists():
        print_status("Importing cylinders...")
        with open(cylinders_file, 'r', encoding='utf-8') as f:
            cylinders_data = json.load(f)
        
        imported_count = 0
        for cylinder_data in cylinders_data:
            try:
                # Check if cylinder already exists
                cursor.execute("SELECT id FROM cylinders WHERE custom_id = ?", 
                             (cylinder_data.get('custom_id'),))
                if cursor.fetchone():
                    continue
                
                cylinder_id = cylinder_data.get('id', str(uuid.uuid4()))
                
                # Parse dates
                date_borrowed = None
                rental_date = None
                date_returned = None
                
                if cylinder_data.get('date_borrowed'):
                    try:
                        date_borrowed = cylinder_data['date_borrowed'].replace('Z', '+00:00')
                    except:
                        pass
                
                if cylinder_data.get('rental_date'):
                    try:
                        rental_date = cylinder_data['rental_date'].replace('Z', '+00:00')
                    except:
                        pass
                
                if cylinder_data.get('date_returned'):
                    try:
                        date_returned = cylinder_data['date_returned'].replace('Z', '+00:00')
                    except:
                        pass
                
                cursor.execute("""
                    INSERT INTO cylinders (
                        id, custom_id, serial_number, type, size, status, location,
                        rented_to, customer_name, customer_email, customer_phone,
                        customer_no, customer_city, customer_state,
                        date_borrowed, rental_date, date_returned
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    cylinder_id,
                    cylinder_data.get('custom_id', ''),
                    cylinder_data.get('serial_number', ''),
                    cylinder_data.get('type', 'Medical Oxygen'),
                    cylinder_data.get('size', '40L'),
                    cylinder_data.get('status', 'available'),
                    cylinder_data.get('location', 'Warehouse'),
                    cylinder_data.get('rented_to'),
                    cylinder_data.get('customer_name', ''),
                    cylinder_data.get('customer_email', ''),
                    cylinder_data.get('customer_phone', ''),
                    cylinder_data.get('customer_no', ''),
                    cylinder_data.get('customer_city', ''),
                    cylinder_data.get('customer_state', ''),
                    date_borrowed,
                    rental_date,
                    date_returned
                ))
                imported_count += 1
            except Exception as e:
                print_warning(f"Error importing cylinder {cylinder_data.get('custom_id', 'Unknown')}: {e}")
        
        conn.commit()
        print_status(f"Imported {imported_count} cylinders")
    
    # Import rental history
    rental_file = data_dir / "rental_history.json"
    if rental_file.exists():
        print_status("Importing rental history...")
        with open(rental_file, 'r', encoding='utf-8') as f:
            rental_data = json.load(f)
        
        imported_count = 0
        for record in rental_data:
            try:
                # Check if record already exists
                cursor.execute("""
                    SELECT id FROM rental_history 
                    WHERE cylinder_id = ? AND customer_id = ? AND rental_date = ?
                """, (record.get('cylinder_id'), record.get('customer_id'), 
                     record.get('rental_date', '').replace('Z', '+00:00')))
                if cursor.fetchone():
                    continue
                
                rental_date = None
                return_date = None
                
                if record.get('rental_date'):
                    try:
                        rental_date = record['rental_date'].replace('Z', '+00:00')
                    except:
                        pass
                
                if record.get('return_date'):
                    try:
                        return_date = record['return_date'].replace('Z', '+00:00')
                    except:
                        pass
                
                cursor.execute("""
                    INSERT INTO rental_history (
                        id, cylinder_id, customer_id, customer_name, customer_no,
                        cylinder_custom_id, rental_date, return_date
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    str(uuid.uuid4()),
                    record.get('cylinder_id'),
                    record.get('customer_id'),
                    record.get('customer_name', ''),
                    record.get('customer_no', ''),
                    record.get('cylinder_custom_id', ''),
                    rental_date,
                    return_date
                ))
                imported_count += 1
            except Exception as e:
                print_warning(f"Error importing rental record: {e}")
        
        conn.commit()
        print_status(f"Imported {imported_count} rental history records")
    
    conn.close()

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
    
    # Database config (SQLite for local development)
    DATABASE_URL = os.environ.get('DATABASE_URL') or 'sqlite:///oxygen_tracker.db'
    
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
    
    # Create database
    create_sqlite_database()
    
    # Import data
    import_json_data()
    
    # Create admin user
    create_admin_user()
    
    # Create local config
    create_local_config()
    
    print()
    print_status("🎉 Local setup completed successfully!")
    print()
    print("Next steps:")
    print("1. Start the development server: python main.py")
    print("2. Open your browser to: http://localhost:5000")
    print("3. Login with admin/admin123")
    print("4. Change the admin password immediately")
    print()
    print("Development database: oxygen_tracker.db")
    print("Environment config: .env")
    print("Users file: users.json")
    print()

if __name__ == "__main__":
    main()