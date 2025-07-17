#!/usr/bin/env python3
"""
Enhanced local development server for Varasai Oxygen
Includes better error handling and debugging information
"""
import os
import sys
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def setup_environment():
    """Setup environment variables for local development"""
    os.environ.setdefault('SESSION_SECRET', 'local-dev-secret-key-12345')
    print("Environment configured for local development")

def create_required_directories():
    """Create required directories if they don't exist"""
    directories = ['data', 'static', 'templates']
    for directory in directories:
        if not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)
            print(f"Created directory: {directory}")

def check_dependencies():
    """Check if all required dependencies are available"""
    required_modules = ['flask', 'werkzeug']
    missing = []
    
    for module in required_modules:
        try:
            __import__(module)
            print(f"✓ {module} available")
        except ImportError:
            missing.append(module)
            print(f"✗ {module} missing")
    
    if missing:
        print(f"\nMissing dependencies: {', '.join(missing)}")
        print("Install with: pip install " + " ".join(missing))
        return False
    return True

def main():
    print("=== Varasai Oxygen Local Development Server ===")
    print(f"Starting at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Working directory: {os.getcwd()}")
    print()
    
    # Setup
    setup_environment()
    create_required_directories()
    
    if not check_dependencies():
        sys.exit(1)
    
    try:
        # Import and configure the app
        print("Importing Flask application...")
        from app import app
        
        print("Flask app imported successfully")
        print("Starting development server...")
        print("Access the application at: http://localhost:5000")
        print("Default login: admin / admin123")
        print()
        print("Press Ctrl+C to stop the server")
        print("=" * 50)
        
        # Run the development server
        app.run(
            host='127.0.0.1',  # Use localhost for local development
            port=5000,
            debug=True,
            use_reloader=True
        )
        
    except KeyboardInterrupt:
        print("\nServer stopped by user")
    except Exception as e:
        print(f"\nError starting server: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()