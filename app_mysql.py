# app_mysql.py - Flask application setup for MySQL (PythonAnywhere deployment)
import os
import logging
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from werkzeug.middleware.proxy_fix import ProxyFix

# Configure logging for production
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Create Flask application
app = Flask(__name__)

# Set secret key for sessions
app.secret_key = os.environ.get("SESSION_SECRET", "your-secret-key-here")

# Configure ProxyFix for deployment environments
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Configure MySQL database with proper URL encoding
default_db_url = 'mysql://varasicyl:root%40123@varasicyl.mysql.pythonanywhere-services.com/varasicyl$Oxygen'
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', default_db_url)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}

# Initialize SQLAlchemy
db = SQLAlchemy(app)

# This file is deprecated - use app_mysql_fixed.py instead
print("⚠️  app_mysql.py is deprecated. Use app_mysql_fixed.py for deployment.")

# Import routes after everything is set up
from routes import *

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)