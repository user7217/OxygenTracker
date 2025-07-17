"""
Varasai Oxygen Cylinder Tracker - Flask Application Configuration

This module handles the core Flask application setup and configuration.
It creates the Flask app instance, configures security settings, logging,
and deployment-specific configurations for both local and production environments.

Key Features:
- Flask application initialization with security configurations
- ProxyFix middleware for handling reverse proxy headers (needed for PythonAnywhere)
- Logging configuration for debugging and monitoring
- Environment-based configuration for different deployment scenarios
- Session management with secure secret key handling

Author: Development Team
Date: July 2025
Version: 2.0
"""

import os
import logging
from flask import Flask
from werkzeug.middleware.proxy_fix import ProxyFix

# Configure logging for debugging and monitoring
# DEBUG level provides detailed information for development
logging.basicConfig(level=logging.DEBUG)

# Create the Flask application instance
app = Flask(__name__)

# Session security configuration
# Uses environment variable for production, fallback for development
# SESSION_SECRET should be set in production for security
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key-change-in-production")

# ProxyFix middleware configuration for reverse proxy deployments
# x_proto=1: Trust X-Forwarded-Proto header (for HTTPS detection)
# x_host=1: Trust X-Forwarded-Host header (for correct URL generation)
# This is essential for PythonAnywhere and similar hosting platforms
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Deployment-specific configuration
# These settings ensure the app works correctly in different environments
app.config['SERVER_NAME'] = None  # Let Flask auto-detect server name
app.config['APPLICATION_ROOT'] = '/'  # Application root path
app.config['PREFERRED_URL_SCHEME'] = 'https'  # Prefer HTTPS for URL generation

# Import routes after app creation to avoid circular imports
# This pattern ensures the app instance is available when routes are defined
from routes import *
