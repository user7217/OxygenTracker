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

# Import your Flask application
from app import app as application

# For debugging (remove in production)
if __name__ == "__main__":
    application.run(debug=False)