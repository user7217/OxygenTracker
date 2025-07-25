#!/usr/bin/env python3
"""
Local development runner for Oxygen Cylinder Tracker
Handles environment setup and starts the Flask development server
"""
import os
import sys
from pathlib import Path

def setup_environment():
    """Set up environment variables for local development"""
    
    # Default environment variables for local development
    default_env = {
        'DATABASE_URL': 'postgresql://postgres:password@localhost:5432/oxygen_tracker',
        'SESSION_SECRET': 'dev-secret-key-change-in-production',
        'PGHOST': 'localhost',
        'PGPORT': '5432',
        'PGDATABASE': 'oxygen_tracker',
        'PGUSER': 'postgres',
        'PGPASSWORD': 'password',
        'FLASK_ENV': 'development',
        'FLASK_DEBUG': '1'
    }
    
    # Load .env file if it exists
    env_file = Path('.env')
    if env_file.exists():
        print("Loading environment from .env file...")
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip()
    else:
        print("No .env file found, using default development settings...")
        print("Create a .env file with your database settings for custom configuration.")
        
    # Set default values for any missing environment variables
    for key, value in default_env.items():
        if key not in os.environ:
            os.environ[key] = value
    
    # Print current database configuration
    print(f"\nDatabase Configuration:")
    print(f"  HOST: {os.environ.get('PGHOST', 'localhost')}")
    print(f"  PORT: {os.environ.get('PGPORT', '5432')}")
    print(f"  DATABASE: {os.environ.get('PGDATABASE', 'oxygen_tracker')}")
    print(f"  USER: {os.environ.get('PGUSER', 'postgres')}")
    print(f"  URL: {os.environ.get('DATABASE_URL', 'Not set')}")
    print()

def check_dependencies():
    """Check if required packages are installed"""
    required_packages = [
        'flask',
        'flask_sqlalchemy', 
        'psycopg2',
        'werkzeug',
        'pandas',
        'reportlab'
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print("Missing required packages:")
        for package in missing_packages:
            print(f"  - {package}")
        print("\nInstall missing packages with:")
        print("pip install " + " ".join(missing_packages))
        return False
    
    return True

def test_database_connection():
    """Test PostgreSQL database connection"""
    try:
        import psycopg2
        
        # Get database connection parameters
        db_url = os.environ.get('DATABASE_URL')
        if db_url:
            # Parse DATABASE_URL
            from urllib.parse import urlparse
            parsed = urlparse(db_url)
            host = parsed.hostname
            port = parsed.port
            database = parsed.path[1:]  # Remove leading slash
            user = parsed.username
            password = parsed.password
        else:
            # Use individual environment variables
            host = os.environ.get('PGHOST', 'localhost')
            port = int(os.environ.get('PGPORT', 5432))
            database = os.environ.get('PGDATABASE', 'oxygen_tracker')
            user = os.environ.get('PGUSER', 'postgres')
            password = os.environ.get('PGPASSWORD', '')
        
        # Test connection
        conn = psycopg2.connect(
            host=host,
            port=port,
            database=database,
            user=user,
            password=password
        )
        conn.close()
        print("✓ Database connection successful!")
        return True
        
    except ImportError:
        print("✗ psycopg2 not installed. Install with: pip install psycopg2-binary")
        return False
    except Exception as e:
        print(f"✗ Database connection failed: {e}")
        print("\nTroubleshooting:")
        print("1. Ensure PostgreSQL is running")
        print("2. Check database credentials in .env file")
        print("3. Verify database exists: CREATE DATABASE oxygen_tracker;")
        return False

def main():
    """Main entry point for local development"""
    print("="*60)
    print("Oxygen Cylinder Tracker - Local Development Setup")
    print("="*60)
    
    # Setup environment
    setup_environment()
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Test database connection
    if not test_database_connection():
        print("\nContinuing anyway - you can fix database issues later...")
    
    print("\nStarting Flask development server...")
    print("Access the application at: http://localhost:5000")
    print("Default admin login: admin / admin123")
    print("\nPress Ctrl+C to stop the server")
    print("-"*60)
    
    # Import and run the Flask app
    try:
        from main import app
        app.run(host='127.0.0.1', port=5000, debug=True)
    except Exception as e:
        print(f"Error starting application: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()