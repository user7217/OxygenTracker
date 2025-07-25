"""
MySQL-compatible routes for PythonAnywhere deployment
This file imports models from app_mysql_fixed instead of models_postgres
"""

from flask import render_template, request, redirect, url_for, flash, jsonify, session, Response
import csv
import io
import os
import json
import shutil
import threading
import time
from datetime import datetime, timedelta
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors

# Import app and models from the MySQL fixed version
from app_mysql_fixed import app, db, Customer, Cylinder, RentalHistory
from auth_models import UserManager
from functools import wraps
import tempfile

# Initialize user manager for authentication and authorization
user_manager = UserManager()

# Try to import Access functionality with graceful degradation
ACCESS_AVAILABLE = False
try:
    from data_importer import DataImporter
    ACCESS_AVAILABLE = True
except ImportError as e:
    import logging
    logging.warning(f"MS Access functionality not available: {e}")

# Try to import Email functionality with graceful degradation
EMAIL_AVAILABLE = False
email_service = None
try:
    from email_service import EmailService
    email_service = EmailService()
    EMAIL_AVAILABLE = True
except ImportError as e:
    import logging
    logging.warning(f"Email functionality not available: {e}")

def login_required(f):
    """Decorator to require user authentication for routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    """Decorator to require admin role for routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page', 'error')
            return redirect(url_for('login'))
        
        user = user_manager.get_user_by_id(session['user_id'])
        if not user or user.get('role') != 'admin':
            flash('Admin access required', 'error')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function

def role_required(*allowed_roles):
    """Decorator to require specific roles for routes"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                flash('Please log in to access this page', 'error')
                return redirect(url_for('login'))
            
            user = user_manager.get_user_by_id(session['user_id'])
            if not user or user.get('role') not in allowed_roles:
                flash('Insufficient permissions', 'error')
                return redirect(url_for('dashboard'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

@app.route('/')
def index():
    """Home page - redirect to dashboard if logged in, otherwise show login"""
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login page and authentication"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = user_manager.authenticate(username, password)
        if user:
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['user_role'] = user.get('role', 'user')
            flash(f'Welcome back, {user["username"]}!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password', 'error')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    """User logout and session cleanup"""
    username = session.get('username', 'User')
    session.clear()
    flash(f'Goodbye, {username}!', 'info')
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    """Main dashboard with system overview and quick statistics"""
    try:
        # Get current user info for display
        user = user_manager.get_user_by_id(session.get('user_id'))
        user_role = user.get('role', 'user') if user else 'user'
        
        # Get basic statistics from database
        total_customers = db.session.query(Customer).count()
        total_cylinders = db.session.query(Cylinder).count()
        rented_cylinders = db.session.query(Cylinder).filter_by(status='rented').count()
        available_cylinders = total_cylinders - rented_cylinders
        
        return render_template('dashboard.html',
                             total_customers=total_customers,
                             total_cylinders=total_cylinders,
                             rented_cylinders=rented_cylinders,
                             available_cylinders=available_cylinders,
                             user_role=user_role)
    except Exception as e:
        # Graceful fallback if database is not accessible
        return render_template('dashboard.html',
                             total_customers=0,
                             total_cylinders=0,
                             rented_cylinders=0,
                             available_cylinders=0,
                             user_role='user',
                             db_error=str(e))

@app.route('/customers')
@login_required
def customers():
    """Display all customers with search and pagination"""
    try:
        search_query = request.args.get('search', '').strip()
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 25, type=int)
        
        # Build query
        query = db.session.query(Customer)
        
        if search_query:
            query = query.filter(
                db.or_(
                    Customer.customer_name.ilike(f'%{search_query}%'),
                    Customer.customer_no.ilike(f'%{search_query}%'),
                    Customer.customer_phone.ilike(f'%{search_query}%'),
                    Customer.customer_email.ilike(f'%{search_query}%')
                )
            )
        
        # Paginate results
        customers_paginated = query.paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return render_template('customers.html',
                             customers=customers_paginated.items,
                             pagination=customers_paginated,
                             search_query=search_query,
                             per_page=per_page)
    except Exception as e:
        flash(f'Database error: {str(e)}', 'error')
        return render_template('customers.html', customers=[], search_query='')

@app.route('/cylinders')
@login_required
def cylinders():
    """Display all cylinders with search, filtering, and pagination"""
    try:
        search_query = request.args.get('search', '').strip()
        status_filter = request.args.get('status', '')
        type_filter = request.args.get('type', '')
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 25, type=int)
        
        # Build query
        query = db.session.query(Cylinder)
        
        if search_query:
            query = query.filter(
                db.or_(
                    Cylinder.custom_id.ilike(f'%{search_query}%'),
                    Cylinder.serial_number.ilike(f'%{search_query}%'),
                    Cylinder.customer_name.ilike(f'%{search_query}%')
                )
            )
        
        if status_filter:
            query = query.filter(Cylinder.status == status_filter)
            
        if type_filter:
            query = query.filter(Cylinder.type == type_filter)
        
        # Order by rental status (rented first) then by date
        query = query.order_by(
            db.case((Cylinder.status == 'rented', 0), else_=1),
            Cylinder.date_borrowed.desc().nullslast()
        )
        
        # Paginate results
        cylinders_paginated = query.paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return render_template('cylinders.html',
                             cylinders=cylinders_paginated.items,
                             pagination=cylinders_paginated,
                             search_query=search_query,
                             status_filter=status_filter,
                             type_filter=type_filter,
                             per_page=per_page)
    except Exception as e:
        flash(f'Database error: {str(e)}', 'error')
        return render_template('cylinders.html', cylinders=[], search_query='')

# Add basic customer and cylinder management routes
@app.route('/add_customer', methods=['GET', 'POST'])
@role_required('admin', 'user')
def add_customer():
    """Add new customer"""
    if request.method == 'POST':
        try:
            customer = Customer(
                id=f"CUST_{int(datetime.now().timestamp())}",
                customer_no=request.form.get('customer_no', ''),
                customer_name=request.form.get('customer_name', ''),
                customer_email=request.form.get('customer_email', ''),
                customer_phone=request.form.get('customer_phone', ''),
                customer_address=request.form.get('customer_address', ''),
                customer_city=request.form.get('customer_city', ''),
                customer_state=request.form.get('customer_state', ''),
                customer_apgst=request.form.get('customer_apgst', ''),
                customer_cst=request.form.get('customer_cst', '')
            )
            db.session.add(customer)
            db.session.commit()
            flash('Customer added successfully!', 'success')
            return redirect(url_for('customers'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding customer: {str(e)}', 'error')
    
    return render_template('add_customer.html')

@app.route('/add_cylinder', methods=['GET', 'POST'])
@role_required('admin', 'user')
def add_cylinder():
    """Add new cylinder"""
    if request.method == 'POST':
        try:
            cylinder = Cylinder(
                id=f"CYL_{int(datetime.now().timestamp())}",
                custom_id=request.form.get('custom_id', ''),
                serial_number=request.form.get('serial_number', ''),
                type=request.form.get('type', 'Medical Oxygen'),
                size=request.form.get('size', '40L'),
                status='available',
                location='Warehouse',
                pressure=request.form.get('pressure', ''),
                notes=request.form.get('notes', '')
            )
            db.session.add(cylinder)
            db.session.commit()
            flash('Cylinder added successfully!', 'success')
            return redirect(url_for('cylinders'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding cylinder: {str(e)}', 'error')
    
    # Get customers for dropdown
    try:
        customers_list = db.session.query(Customer).order_by(Customer.customer_name).all()
    except:
        customers_list = []
    
    return render_template('add_cylinder.html', customers=customers_list)

# Error handlers
@app.errorhandler(404)
def page_not_found(e):
    """Handle 404 errors"""
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    """Handle 500 errors"""
    return render_template('500.html'), 500

if __name__ == '__main__':
    app.run(debug=True)