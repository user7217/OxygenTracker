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
    
    # Run database migrations for existing tables
    try:
        from sqlalchemy import text
        
        # Check if old cylinder_id column exists and remove it if it does
        result = db.session.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='cylinders' AND column_name='cylinder_id'
        """)).fetchone()
        
        if result:
            logging.info("Removing old cylinder_id column from cylinders table")
            # First drop the constraint if it exists
            try:
                db.session.execute(text("ALTER TABLE cylinders DROP CONSTRAINT IF EXISTS cylinders_cylinder_id_key"))
            except:
                pass
            # Then drop the column
            db.session.execute(text("ALTER TABLE cylinders DROP COLUMN cylinder_id"))
        
        # Fix rental_history table schema if needed
        rental_history_exists = db.session.execute(text("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_name='rental_history'
        """)).fetchone()
        
        if rental_history_exists:
            # Get current columns in rental_history
            rental_columns = db.session.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='rental_history'
            """)).fetchall()
            existing_columns = [row[0] for row in rental_columns]
            
            # Add missing columns to rental_history - updated for new format
            required_columns = [
                ('customer_no', 'VARCHAR'),
                ('customer_name', 'VARCHAR'),
                ('customer_phone', 'VARCHAR'),
                ('customer_address', 'VARCHAR'),
                ('customer_city', 'VARCHAR'),
                ('customer_state', 'VARCHAR'),
                ('cylinder_no', 'VARCHAR'),
                ('cylinder_custom_id', 'VARCHAR'),
                ('cylinder_serial', 'VARCHAR'),
                ('cylinder_type', 'VARCHAR'),
                ('cylinder_size', 'VARCHAR'),
                ('dispatch_date', 'DATE'),
                ('return_date', 'DATE'),
                ('rental_days', 'INTEGER'),
                ('status', 'VARCHAR'),
                ('created_at', 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP')
            ]
            
            for col_name, col_type in required_columns:
                if col_name not in existing_columns:
                    try:
                        db.session.execute(text(f"ALTER TABLE rental_history ADD COLUMN {col_name} {col_type}"))
                        logging.info(f"Added missing column {col_name} to rental_history")
                    except Exception as e:
                        logging.warning(f"Failed to add column {col_name}: {e}")
        
        # Check if customer_address column exists, if not add it
        result = db.session.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='cylinders' AND column_name='customer_address'
        """)).fetchone()
        
        if not result:
            logging.info("Adding missing customer_address column to cylinders table")
            db.session.execute(text("ALTER TABLE cylinders ADD COLUMN customer_address VARCHAR"))
            
        # Check for other missing columns that might be needed
        missing_columns = [
            ('customer_city', 'VARCHAR'),
            ('customer_state', 'VARCHAR'),
            ('customer_phone', 'VARCHAR'),
            ('date_returned', 'VARCHAR'),
            ('rental_date', 'VARCHAR'),
            ('date_borrowed', 'VARCHAR'),
            ('serial_number', 'VARCHAR'),
            ('pressure', 'VARCHAR'), 
            ('last_inspection', 'VARCHAR'),
            ('next_inspection', 'VARCHAR'),
            ('notes', 'TEXT'),
            ('customer_no', 'VARCHAR')
        ]
        
        for column_name, column_type in missing_columns:
            result = db.session.execute(text(f"""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='cylinders' AND column_name='{column_name}'
            """)).fetchone()
            
            if not result:
                logging.info(f"Adding missing {column_name} column to cylinders table")
                db.session.execute(text(f"ALTER TABLE cylinders ADD COLUMN {column_name} {column_type}"))
        
        db.session.commit()
        logging.info("Database migration completed successfully")
        
    except Exception as e:
        logging.warning(f"Database migration failed (might be normal for new deployments): {e}")
        db.session.rollback()
    
    logging.info("Database tables created successfully")

# Import routes after app and database setup to avoid circular imports
from routes import *

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)