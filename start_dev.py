#!/usr/bin/env python3
"""
Development Server Starter with Environment Loading
Automatically loads environment variables and starts the Flask development server
"""

import os
import sys
from pathlib import Path

def load_environment():
    """Load environment variables from .env file"""
    env_file = Path(".env")
    
    if env_file.exists():
        print("📁 Loading environment variables from .env file...")
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip()
        print("✓ Environment variables loaded")
    else:
        print("⚠ No .env file found, using default settings")

def check_database():
    """Check if database exists and is accessible"""
    db_url = os.environ.get('DATABASE_URL', 'sqlite:///oxygen_tracker.db')
    
    if db_url.startswith('sqlite:///'):
        db_file = db_url.replace('sqlite:///', '')
        if not os.path.exists(db_file):
            print(f"⚠ Database file not found: {db_file}")
            print("  Run setup_local.py first to create the database")
            return False
        else:
            print(f"✓ Database found: {db_file}")
    else:
        print(f"✓ Using database: {db_url}")
    
    return True

def check_users_file():
    """Check if users.json exists"""
    if not os.path.exists("users.json"):
        print("⚠ users.json not found")
        print("  Run setup_local.py first to create the admin user")
        return False
    else:
        print("✓ Users file found")
    return True

def start_development_server():
    """Start the Flask development server"""
    print("🚀 Starting Flask development server...")
    print("📖 Open your browser to: http://localhost:5000")
    print("🔑 Default login: admin / admin123")
    print("⏹️  Press Ctrl+C to stop the server")
    print()
    
    # Import and run the main application
    try:
        from main import app
        app.run(
            host='0.0.0.0',
            port=5000,
            debug=True,
            use_reloader=True,
            use_debugger=True
        )
    except ImportError as e:
        print(f"❌ Error importing main application: {e}")
        print("   Make sure all dependencies are installed")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        sys.exit(1)

def main():
    """Main function"""
    print("🔧 Preparing development environment...")
    print()
    
    # Load environment variables
    load_environment()
    
    # Check prerequisites
    if not check_database():
        print("\n💡 Tip: Run one of these setup commands first:")
        print("   python setup_local.py       (Python)")
        print("   ./setup_local.sh            (Linux/macOS)")
        print("   setup_local.bat             (Windows)")
        sys.exit(1)
    
    if not check_users_file():
        print("\n💡 Tip: Run setup_local.py to create the users file")
        sys.exit(1)
    
    print("✅ All prerequisites met")
    print()
    
    # Start the server
    start_development_server()

if __name__ == "__main__":
    main()