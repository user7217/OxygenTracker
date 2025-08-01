# app.py - Flask application setup
import os
import logging
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix

# Configure logging for development debugging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Create SQLAlchemy base class
class Base(DeclarativeBase):
    pass

# Create SQLAlchemy instance
db = SQLAlchemy(model_class=Base)

# Create Flask application
app = Flask(__name__)

# Set secret key for sessions
app.secret_key = os.environ.get("SESSION_SECRET", "your-secret-key-here")

# Configure database
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}

# Initialize database with app
db.init_app(app)

# Configure ProxyFix for deployment environments
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Create tables within app context
with app.app_context():
    # Import models to ensure they're registered with SQLAlchemy
    import models
    
    # Create all tables
    db.create_all()
    logging.info("Database tables created successfully")

# Import routes after app and database setup to avoid circular imports
from routes import *

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)