# app_mysql_fixed.py - Flask application setup for MySQL (PythonAnywhere deployment)
import os
import logging
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from werkzeug.middleware.proxy_fix import ProxyFix
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean

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

# Define models directly in this file to avoid circular imports
class Customer(db.Model):
    """Customer model for MySQL database"""
    __tablename__ = 'customers'
    
    id = Column(String(50), primary_key=True)
    customer_no = Column(String(50), unique=True, index=True)
    customer_name = Column(String(200), nullable=False)
    customer_email = Column(String(200))
    customer_phone = Column(String(50))
    customer_address = Column(Text)
    customer_city = Column(String(100))
    customer_state = Column(String(100))
    customer_apgst = Column(String(50))
    customer_cst = Column(String(50))
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        """Convert customer to dictionary"""
        return {
            'id': self.id,
            'customer_no': self.customer_no,
            'customer_name': self.customer_name,
            'customer_email': self.customer_email,
            'customer_phone': self.customer_phone,
            'customer_address': self.customer_address,
            'customer_city': self.customer_city,
            'customer_state': self.customer_state,
            'customer_apgst': self.customer_apgst,
            'customer_cst': self.customer_cst,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class Cylinder(db.Model):
    """Cylinder model for MySQL database"""
    __tablename__ = 'cylinders'
    
    id = Column(String(50), primary_key=True)
    custom_id = Column(String(50), unique=True, index=True)
    serial_number = Column(String(100))
    type = Column(String(50), default='Medical Oxygen')
    size = Column(String(20), default='40L')
    status = Column(String(20), default='available')
    location = Column(String(200), default='Warehouse')
    pressure = Column(String(50))
    last_inspection = Column(String(50))
    next_inspection = Column(String(50))
    notes = Column(Text)
    
    # Rental information
    rented_to = Column(String(50))  # Customer ID
    customer_name = Column(String(200))
    customer_email = Column(String(200))
    customer_phone = Column(String(50))
    customer_no = Column(String(50))
    date_borrowed = Column(DateTime)
    date_returned = Column(DateTime)
    
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        """Convert cylinder to dictionary"""
        return {
            'id': self.id,
            'custom_id': self.custom_id,
            'serial_number': self.serial_number,
            'type': self.type,
            'size': self.size,
            'status': self.status,
            'location': self.location,
            'pressure': self.pressure,
            'last_inspection': self.last_inspection,
            'next_inspection': self.next_inspection,
            'notes': self.notes,
            'rented_to': self.rented_to,
            'customer_name': self.customer_name,
            'customer_email': self.customer_email,
            'customer_phone': self.customer_phone,
            'customer_no': self.customer_no,
            'date_borrowed': self.date_borrowed.isoformat() if self.date_borrowed else None,
            'date_returned': self.date_returned.isoformat() if self.date_returned else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class RentalHistory(db.Model):
    """Rental history model for MySQL database"""
    __tablename__ = 'rental_history'
    
    id = Column(String(50), primary_key=True)
    customer_no = Column(String(50))
    customer_name = Column(String(200))
    cylinder_custom_id = Column(String(50))
    cylinder_type = Column(String(50))
    cylinder_size = Column(String(20))
    dispatch_date = Column(DateTime)
    return_date = Column(DateTime)
    rental_days = Column(Integer, default=0)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        """Convert rental history to dictionary"""
        return {
            'id': self.id,
            'customer_no': self.customer_no,
            'customer_name': self.customer_name,
            'cylinder_custom_id': self.cylinder_custom_id,
            'cylinder_type': self.cylinder_type,
            'cylinder_size': self.cylinder_size,
            'dispatch_date': self.dispatch_date.isoformat() if self.dispatch_date else None,
            'return_date': self.return_date.isoformat() if self.return_date else None,
            'rental_days': self.rental_days,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

# Create tables when app starts
with app.app_context():
    try:
        db.create_all()
        print("✓ MySQL database tables created successfully!")
    except Exception as e:
        print(f"⚠️  Database connection will be established on PythonAnywhere: {str(e)}")

# Import routes after everything is set up
try:
    from routes_mysql import *
    print("✓ MySQL-compatible routes loaded successfully!")
except ImportError as e:
    print(f"⚠️  Routes will be imported on PythonAnywhere: {str(e)}")
    # Fallback to regular routes if needed
    try:
        from routes import *
        print("⚠️  Using fallback routes - may have database compatibility issues")
    except ImportError as e2:
        print(f"⚠️  No routes available: {str(e2)}")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)