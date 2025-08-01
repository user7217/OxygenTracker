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
    
    # Relationships
    cylinders = db.relationship("Cylinder", back_populates="customer", lazy='dynamic')

class Cylinder(db.Model):
    """Cylinder model using Flask-SQLAlchemy"""
    __tablename__ = 'cylinders'
    
    id = db.Column(db.String, primary_key=True, default=lambda: str(uuid.uuid4()))
    cylinder_id = db.Column(db.String, unique=True, nullable=False, index=True)
    custom_id = db.Column(db.String, index=True)
    type = db.Column(db.String, index=True)
    size = db.Column(db.String)
    status = db.Column(db.String, default='available', index=True)
    location = db.Column(db.String, default='Warehouse')
    rented_to = db.Column(db.String, db.ForeignKey('customers.id'), nullable=True)
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
    
    # Relationships
    customer = db.relationship("Customer", back_populates="cylinders")

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
    rental_date = db.Column(db.DateTime, index=True)
    dispatch_date = db.Column(db.DateTime)
    return_date = db.Column(db.DateTime, index=True)
    rental_days = db.Column(db.Integer)
    location = db.Column(db.String)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Indexes for better query performance
    __table_args__ = (
        db.Index('idx_rental_customer', 'customer_id'),
        db.Index('idx_rental_cylinder', 'cylinder_id'),
        db.Index('idx_rental_dates', 'rental_date', 'return_date'),
        db.Index('idx_customer_no', 'customer_no'),
    )