# db_models.py - PostgreSQL database models using SQLAlchemy
import os
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text, Boolean, ForeignKey, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid

# Database configuration
DATABASE_URL = os.environ.get('DATABASE_URL')
engine = create_engine(DATABASE_URL, pool_pre_ping=True, pool_recycle=300)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Customer(Base):
    """Customer model for PostgreSQL"""
    __tablename__ = 'customers'
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    customer_no = Column(String, unique=True, index=True)
    customer_name = Column(String, nullable=False, index=True)
    customer_email = Column(String)
    customer_phone = Column(String)
    customer_address = Column(Text)
    customer_city = Column(String)
    customer_state = Column(String)
    customer_apgst = Column(String)
    customer_cst = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    cylinders = relationship("Cylinder", back_populates="customer")
    rental_history = relationship("RentalHistory", back_populates="customer")

class Cylinder(Base):
    """Cylinder model for PostgreSQL"""
    __tablename__ = 'cylinders'
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    custom_id = Column(String, index=True)
    serial_number = Column(String, index=True)
    type = Column(String, default='Medical Oxygen')
    size = Column(String, default='40L')
    status = Column(String, default='available', index=True)
    location = Column(String, default='Warehouse')
    
    # Rental information
    rented_to = Column(String, ForeignKey('customers.id', ondelete='SET NULL'), index=True, nullable=True)
    customer_name = Column(String)
    customer_email = Column(String)
    customer_phone = Column(String)
    customer_no = Column(String)
    customer_city = Column(String)
    customer_state = Column(String)
    
    # Dates
    date_borrowed = Column(DateTime)
    rental_date = Column(DateTime)
    date_returned = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    customer = relationship("Customer", back_populates="cylinders")
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_cylinder_status_rented_to', 'status', 'rented_to'),
        Index('idx_cylinder_customer_no', 'customer_no'),
        Index('idx_cylinder_dates', 'date_borrowed', 'date_returned'),
    )

class RentalHistory(Base):
    """Rental history model for PostgreSQL"""
    __tablename__ = 'rental_history'
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Customer information
    customer_id = Column(String, ForeignKey('customers.id', ondelete='SET NULL'), index=True, nullable=True)
    customer_no = Column(String, index=True)
    customer_name = Column(String)
    customer_phone = Column(String)
    customer_email = Column(String)
    customer_address = Column(Text)
    customer_city = Column(String)
    customer_state = Column(String)
    
    # Cylinder information
    cylinder_id = Column(String)
    cylinder_no = Column(String, index=True)
    cylinder_custom_id = Column(String, index=True)
    cylinder_serial = Column(String)
    cylinder_type = Column(String)
    cylinder_size = Column(String)
    
    # Rental details
    dispatch_date = Column(DateTime, index=True)
    return_date = Column(DateTime, index=True)
    date_borrowed = Column(DateTime)
    date_returned = Column(DateTime)
    rental_days = Column(Integer)
    location = Column(String)
    status = Column(String, default='completed')
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    customer = relationship("Customer", back_populates="rental_history")
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_rental_customer_dates', 'customer_no', 'dispatch_date', 'return_date'),
        Index('idx_rental_cylinder_dates', 'cylinder_no', 'dispatch_date'),
        Index('idx_rental_status_dates', 'status', 'return_date'),
    )

def create_tables():
    """Create all database tables"""
    Base.metadata.create_all(bind=engine)

def get_db():
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_db_session():
    """Get database session for direct use"""
    return SessionLocal()