"""
Varasai Oxygen Cylinder Tracker - Main Application Entry Point

This is the main entry point for the Varasai Oxygen Cylinder Tracker application.
It imports the Flask app from the app module and starts the development server.

The application is configured to:
- Listen on all interfaces (0.0.0.0) for both local and remote access
- Use port 5000 as the default Flask port
- Run in debug mode for development with auto-reload functionality

Author: Development Team
Date: July 2025
Version: 2.0
"""

from app import app

if __name__ == '__main__':
    # Start the Flask development server
    # host='0.0.0.0' allows external connections for deployment
    # port=5000 is the standard Flask development port
    # debug=True enables hot reload and detailed error messages
    app.run(host='0.0.0.0', port=5000, debug=True)
