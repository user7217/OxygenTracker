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

# Configure MySQL database
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'mysql://user:password@localhost/database')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}

# Initialize SQLAlchemy
db = SQLAlchemy(app)

# Import models and create tables
from mysql_models import Customer, Cylinder, RentalHistory

with app.app_context():
    db.create_all()
    print("✓ MySQL database tables created successfully!")

# Import routes after app and db setup
from routes import *

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)