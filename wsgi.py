#!/usr/bin/env python3
"""
WSGI configuration for PythonAnywhere deployment
Place this file in your PythonAnywhere web app configuration
"""
import sys
import os

# Add your project directory to the Python path
# Replace 'yourusername' with your actual PythonAnywhere username
# path = '/home/yourusername/varasai-oxygen'
# if path not in sys.path:
#     sys.path.insert(0, path)

# Set environment variables for production
os.environ.setdefault('SESSION_SECRET', 'pythonanywhere-production-secret-key-change-this')

# Configure Flask for PythonAnywhere
os.environ.setdefault('FLASK_ENV', 'production')

# Import your Flask application
from app import app as application

# Configure app for PythonAnywhere if not already set
if not hasattr(application, '_pythonanywhere_configured'):
    application.config.update({
        'SERVER_NAME': None,
        'APPLICATION_ROOT': '/',
        'PREFERRED_URL_SCHEME': 'https'
    })
    application._pythonanywhere_configured = True

# For debugging (remove in production)
if __name__ == "__main__":
    application.run(debug=False)