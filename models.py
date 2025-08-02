# models.py - Flask-SQLAlchemy models for Varasicyl
from datetime import datetime
from app import db
import uuid

class Customer(db.Model):
    """Customer model using Flask-SQLAlchemy"""
    __tablename__ = 'customers'
    
    id = db.Column(db.String, primary_key=True, default=lambda: str(uuid.uuid4()))
    customer_no = db.Column(db.String, unique=True, index=True)
    customer_name = db.Column(db.String, nullable=False, index=True)
    customer_email = db.Column(db.String)
    customer_phone = db.Column(db.String)
    customer_address = db.Column(db.Text)
    customer_city = db.Column(db.String)
    customer_state = db.Column(db.String)
    customer_apgst = db.Column(db.String)
    customer_cst = db.Column(db.String)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Note: No direct relationship to cylinders since they use string references

class Cylinder(db.Model):
    """Cylinder model matching exact JSON data structure"""
    __tablename__ = 'cylinders'
    
    # Primary fields matching your JSON structure exactly
    id = db.Column(db.String, primary_key=True)  # Uses your CYL-* format directly
    custom_id = db.Column(db.String, index=True)  # Your cylinder identifier like "35254"
    type = db.Column(db.String, index=True)  # "O2", etc.
    size = db.Column(db.String)  # "7", "7.2", etc.
    location = db.Column(db.String, default='Warehouse')  # Location like "Nellore"
    status = db.Column(db.String, default='Available', index=True)  # "Available" or "rented"
    created_at = db.Column(db.String)  # Store as string to match JSON format
    updated_at = db.Column(db.String)  # Store as string to match JSON format
    
    # Customer fields for rented cylinders
    customer_name = db.Column(db.String)  # "VAPL", etc.
    customer_email = db.Column(db.String)  # Usually empty ""
    customer_phone = db.Column(db.String)  # "0.0" or actual phone
    customer_address = db.Column(db.String)  # Customer address
    customer_city = db.Column(db.String)  # "Nellore", etc.
    customer_state = db.Column(db.String)  # "Andhra Pradesh", etc.
    
    # Rental tracking fields
    rented_to = db.Column(db.String, nullable=True)  # "CUST-3514E7AB" format
    date_returned = db.Column(db.String)  # Store as string, empty when still rented
    rental_date = db.Column(db.String)  # "2007-04-22" format
    date_borrowed = db.Column(db.String)  # "2007-04-22" format
    
    # Additional fields for compatibility (not in your JSON but needed by code)
    serial_number = db.Column(db.String, index=True)  # For backward compatibility
    pressure = db.Column(db.String)  # For pressure tracking
    last_inspection = db.Column(db.String)  # Store as string for consistency
    next_inspection = db.Column(db.String)  # Store as string for consistency
    notes = db.Column(db.Text)  # For additional notes
    customer_no = db.Column(db.String)  # For customer number linkage

class RentalHistory(db.Model):
    """Rental history model using Flask-SQLAlchemy"""
    __tablename__ = 'rental_history'
    
    id = db.Column(db.String, primary_key=True, default=lambda: str(uuid.uuid4()))
    cylinder_id = db.Column(db.String, nullable=False, index=True)
    cylinder_custom_id = db.Column(db.String)
    cylinder_type = db.Column(db.String)
    cylinder_size = db.Column(db.String)
    customer_id = db.Column(db.String, nullable=False, index=True)
    customer_name = db.Column(db.String)
    customer_no = db.Column(db.String, index=True)
    customer_email = db.Column(db.String)
    customer_phone = db.Column(db.String)
    customer_city = db.Column(db.String)
    customer_state = db.Column(db.String)
    customer_address = db.Column(db.Text)
    cylinder_no = db.Column(db.String)
    cylinder_serial = db.Column(db.String)
    dispatch_date = db.Column(db.DateTime)
    return_date = db.Column(db.DateTime, index=True)
    date_borrowed = db.Column(db.DateTime)
    date_returned = db.Column(db.DateTime)
    status = db.Column(db.String)
    rental_days = db.Column(db.Integer)
    location = db.Column(db.String)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)