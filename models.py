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
    """Cylinder model matching exact database structure"""
    __tablename__ = 'cylinders'
    
    # Primary fields - exact order and types matching database
    id = db.Column(db.String, primary_key=True)
    custom_id = db.Column(db.String, index=True)
    serial_number = db.Column(db.String, index=True)
    type = db.Column(db.String, index=True)
    size = db.Column(db.String)
    status = db.Column(db.String, default='available', index=True)
    location = db.Column(db.String, default='Warehouse')
    rented_to = db.Column(db.String, nullable=True)
    customer_name = db.Column(db.String)
    customer_email = db.Column(db.String)
    customer_phone = db.Column(db.String)
    customer_no = db.Column(db.String)
    customer_city = db.Column(db.String)
    customer_state = db.Column(db.String)
    date_borrowed = db.Column(db.DateTime)
    rental_date = db.Column(db.DateTime)
    date_returned = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    customer_address = db.Column(db.String)
    pressure = db.Column(db.String)
    last_inspection = db.Column(db.String)
    next_inspection = db.Column(db.String)
    notes = db.Column(db.Text)

class RentalHistory(db.Model):
    """Rental history model matching your JSON format"""
    __tablename__ = 'rental_history'
    
    # Fields matching your JSON structure
    id = db.Column(db.String, primary_key=True, default=lambda: f"RT-{datetime.now().strftime('%Y%m%d%H%M%S')}-{str(uuid.uuid4())[:4].upper()}")
    customer_no = db.Column(db.String, index=True)
    customer_name = db.Column(db.String)
    customer_phone = db.Column(db.String)
    customer_address = db.Column(db.String)
    customer_city = db.Column(db.String)
    customer_state = db.Column(db.String)
    cylinder_no = db.Column(db.String)
    cylinder_custom_id = db.Column(db.String)
    cylinder_serial = db.Column(db.String)
    cylinder_type = db.Column(db.String)
    cylinder_size = db.Column(db.String)
    dispatch_date = db.Column(db.Date)
    return_date = db.Column(db.Date)
    rental_days = db.Column(db.Integer)
    status = db.Column(db.String, default='completed')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)