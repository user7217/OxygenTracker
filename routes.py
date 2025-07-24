"""
Varasai Oxygen Cylinder Tracker - Flask Routes and Application Logic

Flask routes and application logic for the cylinder management system.

Features:
- Complete CRUD operations for customers and cylinders
- Advanced pagination system for large datasets (5000+ cylinders)
- Role-based access control (Admin, User, Viewer)
- Search and filtering capabilities
- Bulk cylinder operations and rental management
- Data import from MS Access databases
- CSV and PDF export functionality
- Transaction management for customer-cylinder relationships
- Responsive web interface with mobile optimization

Route Categories:
- Authentication: Login, logout, user management
- Dashboard: Main interface and metrics
- Customers: Customer management with Access-compatible fields
- Cylinders: Cylinder inventory with rental tracking and pagination
- Bulk Operations: Multi-cylinder rental/return operations
- Import/Export: Data migration and reporting
- Search: Global search across customers and cylinders
- Admin: User management and system administration

Author: Development Team
Date: July 2025
Version: 2.0
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
from app import app
from models_postgres import Customer, Cylinder
from auth_models import UserManager
from functools import wraps
import os
import tempfile

# Try to import Access functionality with graceful degradation
# MS Access import is optional - system works without it
try:
    from data_importer import DataImporter
    ACCESS_AVAILABLE = True
except ImportError as e:
    ACCESS_AVAILABLE = False
    import logging
    logging.warning(f"MS Access functionality not available: {e}")

# Try to import Email functionality with graceful degradation
# Email service is optional - system works without it
try:
    from email_service import EmailService
    email_service = EmailService()
    EMAIL_AVAILABLE = True
except ImportError as e:
    EMAIL_AVAILABLE = False
    email_service = None
    import logging
    logging.warning(f"Email functionality not available: {e}")

# Initialize user manager for authentication and authorization
user_manager = UserManager()

def login_required(f):
    """
    Decorator to require user authentication for routes
    
    This decorator ensures that only authenticated users can access protected routes.
    Redirects unauthenticated users to the login page with appropriate flash message.
    
    Args:
        f (function): The route function to protect
        
    Returns:
        function: Wrapped function with authentication check
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    """
    Decorator to require admin role for routes
    
    This decorator ensures that only users with admin role can access admin-only routes.
    Provides the highest level of access control for sensitive operations like user
    management, data exports, and system administration.
    
    Args:
        f (function): The route function to protect
        
    Returns:
        function: Wrapped function with admin role check
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page', 'error')
            return redirect(url_for('login'))
        
        user = user_manager.get_user_by_id(session['user_id'])
        if not user or user.get('role') != 'admin':
            flash('Admin access required', 'error')
            return redirect(url_for('index'))
        
        return f(*args, **kwargs)
    return decorated_function

def user_or_admin_required(f):
    """
    Decorator to require user or admin role (excludes viewers)
    
    This decorator allows access to users with 'user' or 'admin' roles while
    excluding viewers from operational functions like cylinder rental/return,
    bulk operations, and data modifications.
    
    Args:
        f (function): The route function to protect
        
    Returns:
        function: Wrapped function with user/admin role check
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page', 'error')
            return redirect(url_for('login'))
        
        user = user_manager.get_user_by_id(session['user_id'])
        if not user or user.get('role') not in ['admin', 'user']:
            flash('Insufficient permissions', 'error')
            return redirect(url_for('index'))
        
        return f(*args, **kwargs)
    return decorated_function

def admin_or_user_can_edit(f):
    """
    Decorator for routes that require admin access for data modification
    
    This decorator restricts access to admin-only operations like adding,
    editing, or deleting customers and cylinders. Users can only perform
    rental/return operations but cannot modify core data.
    
    Args:
        f (function): The route function to protect
        
    Returns:
        function: Wrapped function with admin-only access check
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page', 'error')
            return redirect(url_for('login'))
        
        user = user_manager.get_user_by_id(session['user_id'])
        if not user or user.get('role') != 'admin':
            flash('Only administrators can add/edit/delete customers and cylinders', 'error')
            return redirect(url_for('index'))
        
        return f(*args, **kwargs)
    return decorated_function

# Initialize data models for business logic operations
customer_model = Customer()
cylinder_model = Cylinder()

# ============================================================================
# AUTHENTICATION ROUTES
# ============================================================================

@app.route('/login', methods=['GET', 'POST'])
def login():
    """
    User authentication and session management
    
    Handles user login with username/password authentication. Creates secure
    session with user ID, username, and role information. Supports redirect
    to requested page after successful login.
    
    GET: Display login form
    POST: Process login credentials and create session
    
    Returns:
        GET: Login template
        POST: Redirect to dashboard or requested page on success, login form on failure
    """
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        
        # Validate required fields
        if not username or not password:
            flash('Please enter both username and password', 'error')
            return render_template('login.html')
        
        # Authenticate user credentials
        user = user_manager.authenticate(username, password)
        if user:
            # Create secure session
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['role'] = user.get('role', 'user')
            
            flash(f'Welcome back, {user["username"]}!', 'success')
            
            # Handle redirect to originally requested page
            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password', 'error')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    """
    User logout and session cleanup
    
    Clears all session data and redirects to login page with farewell message.
    Ensures complete session cleanup for security.
    
    Returns:
        Redirect to login page with logout message
    """
    username = session.get('username', 'User')
    session.clear()
    flash(f'Goodbye, {username}!', 'info')
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
@admin_required
def register():
    """User registration (admin only)"""
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()
        confirm_password = request.form.get('confirm_password', '').strip()
        role = request.form.get('role', 'viewer').strip()
        
        # Validation
        if not all([username, email, password, confirm_password]):
            flash('All fields are required', 'error')
            return render_template('register.html')
        
        if password != confirm_password:
            flash('Passwords do not match', 'error')
            return render_template('register.html')
        
        if len(password) < 6:
            flash('Password must be at least 6 characters long', 'error')
            return render_template('register.html')
        
        if role not in ['admin', 'user', 'viewer']:
            flash('Invalid role selected', 'error')
            return render_template('register.html')
        
        # Check if user already exists
        if user_manager.get_user_by_username(username):
            flash('Username already exists', 'error')
            return render_template('register.html')
        
        # Check if email already exists
        users = user_manager.get_all_users()
        if any(u.get('email') == email for u in users):
            flash('Email already registered', 'error')
            return render_template('register.html')
        
        try:
            new_user = user_manager.create_user(username, email, password, role)
            flash(f'User {username} created successfully with role: {role}', 'success')
            return redirect(url_for('users'))
        except Exception as e:
            flash(f'Error creating user: {str(e)}', 'error')
    
    return render_template('register.html')

@app.route('/users')
@admin_required
def users():
    """List all users (admin only)"""
    all_users = user_manager.get_all_users()
    return render_template('users.html', users=all_users)

# ============================================================================
# DASHBOARD AND MAIN ROUTES
# ============================================================================

@app.route('/')
@login_required
def index():
    """
    Main dashboard with system overview and statistics
    
    Displays comprehensive system statistics including cylinder inventory,
    customer counts, utilization rates, and operational metrics. Provides
    quick access to key system information for all user roles.
    
    Features:
    - Total customers and cylinders count
    - Cylinder status breakdown (available, rented, maintenance)
    - Utilization rate calculation
    - System efficiency metrics
    - Growth rate and operational days
    - Role-based information display
    
    Returns:
        Dashboard template with comprehensive system statistics
    """
    customers, _ = customer_model.get_all()
    cylinders, _ = cylinder_model.get_all()
    
    # Calculate cylinder status distribution
    available_cylinders = len([c for c in cylinders if c.get('status', '').lower() == 'available'])
    rented_cylinders = len([c for c in cylinders if c.get('status', '').lower() == 'rented'])
    maintenance_cylinders = len([c for c in cylinders if c.get('status', '').lower() == 'maintenance'])
    
    # Calculate fun metrics
    total_cylinders = len(cylinders)
    utilization_rate = round((rented_cylinders / total_cylinders * 100) if total_cylinders > 0 else 0)
    
    # Find top customer (most rentals)
    customer_rentals = {}
    for cylinder in cylinders:
        if cylinder.get('rented_to'):
            customer_id = cylinder['rented_to']
            customer_rentals[customer_id] = customer_rentals.get(customer_id, 0) + 1
    
    top_customer_count = max(customer_rentals.values()) if customer_rentals else 0
    
    # Calculate average rental days (mock data)
    import random
    avg_rental_days = random.randint(7, 30)
    
    # Calculate efficiency score (based on utilization and availability)
    efficiency_score = min(10, round((utilization_rate + (available_cylinders / total_cylinders * 100 if total_cylinders > 0 else 0)) / 20))
    
    # Days since first customer/cylinder
    from datetime import datetime
    import json
    import os
    
    days_active = 1
    try:
        if os.path.exists('data/customers.json'):
            with open('data/customers.json', 'r') as f:
                customer_data = json.load(f)
                if customer_data:
                    oldest_date = min([c.get('created_at', datetime.now().isoformat()) for c in customer_data])
                    if oldest_date:
                        from datetime import datetime
                        oldest = datetime.fromisoformat(oldest_date.replace('Z', '+00:00').split('.')[0])
                        days_active = (datetime.now() - oldest).days + 1
    except:
        pass
    
    # Growth rate (mock calculation)
    growth_rate = random.randint(5, 25)
    
    stats = {
        'total_customers': len(customers),
        'total_cylinders': total_cylinders,
        'available_cylinders': available_cylinders,
        'rented_cylinders': rented_cylinders,
        'maintenance_cylinders': maintenance_cylinders,
        'utilization_rate': utilization_rate,
        'top_customer_count': top_customer_count,
        'avg_rental_days': avg_rental_days,
        'efficiency_score': efficiency_score,
        'days_active': days_active,
        'growth_rate': growth_rate
    }
    
    return render_template('index.html', stats=stats)

@app.route('/metrics')
@login_required
def metrics():
    """Metrics and analytics page"""
    customers = customer_model.get_all()
    cylinders = cylinder_model.get_all()
    
    # Get cylinder status counts
    available_cylinders = len([c for c in cylinders if c.get('status', '').lower() == 'available'])
    rented_cylinders = len([c for c in cylinders if c.get('status', '').lower() == 'rented'])
    maintenance_cylinders = len([c for c in cylinders if c.get('status', '').lower() == 'maintenance'])
    
    # Calculate fun metrics
    total_cylinders = len(cylinders)
    utilization_rate = round((rented_cylinders / total_cylinders * 100) if total_cylinders > 0 else 0)
    
    # Find top customer (most rentals)
    customer_rentals = {}
    for cylinder in cylinders:
        if cylinder.get('rented_to'):
            customer_id = cylinder['rented_to']
            customer_rentals[customer_id] = customer_rentals.get(customer_id, 0) + 1
    
    top_customer_count = max(customer_rentals.values()) if customer_rentals else 0
    
    # Calculate average rental days (mock data)
    import random
    avg_rental_days = random.randint(7, 30)
    
    # Calculate efficiency score (based on utilization and availability)
    efficiency_score = min(10, round((utilization_rate + (available_cylinders / total_cylinders * 100 if total_cylinders > 0 else 0)) / 20))
    
    # Days since first customer/cylinder
    from datetime import datetime
    import json
    import os
    
    days_active = 1
    try:
        if os.path.exists('data/customers.json'):
            with open('data/customers.json', 'r') as f:
                customer_data = json.load(f)
                if customer_data:
                    oldest_date = min([c.get('created_at', datetime.now().isoformat()) for c in customer_data])
                    if oldest_date:
                        from datetime import datetime
                        oldest = datetime.fromisoformat(oldest_date.replace('Z', '+00:00').split('.')[0])
                        days_active = (datetime.now() - oldest).days + 1
    except:
        pass
    
    # Growth rate (mock calculation)
    growth_rate = random.randint(5, 25)
    
    stats = {
        'total_customers': len(customers),
        'total_cylinders': total_cylinders,
        'available_cylinders': available_cylinders,
        'rented_cylinders': rented_cylinders,
        'maintenance_cylinders': maintenance_cylinders,
        'utilization_rate': utilization_rate,
        'top_customer_count': top_customer_count,
        'avg_rental_days': avg_rental_days,
        'efficiency_score': efficiency_score,
        'days_active': days_active,
        'growth_rate': growth_rate
    }
    
    return render_template('metrics.html', stats=stats)

@app.route('/send_admin_stats', methods=['POST'])
@login_required
@admin_required
def send_admin_stats():
    """Send admin statistics via email"""
    if not EMAIL_AVAILABLE or not email_service:
        flash('Email service not available', 'error')
        return redirect(url_for('metrics'))
    
    email = request.form.get('email', '').strip()
    if not email:
        flash('Please enter a valid email address', 'error')
        return redirect(url_for('metrics'))
    
    # Get current stats
    customers = customer_model.get_all()
    cylinders = cylinder_model.get_all()
    
    # Get cylinder status counts
    available_cylinders = len([c for c in cylinders if c.get('status', '').lower() == 'available'])
    rented_cylinders = len([c for c in cylinders if c.get('status', '').lower() == 'rented'])
    maintenance_cylinders = len([c for c in cylinders if c.get('status', '').lower() == 'maintenance'])
    
    # Calculate metrics
    total_cylinders = len(cylinders)
    utilization_rate = round((rented_cylinders / total_cylinders * 100) if total_cylinders > 0 else 0)
    
    # Find top customer (most rentals)
    customer_rentals = {}
    for cylinder in cylinders:
        if cylinder.get('rented_to'):
            customer_id = cylinder['rented_to']
            customer_rentals[customer_id] = customer_rentals.get(customer_id, 0) + 1
    
    top_customer_count = max(customer_rentals.values()) if customer_rentals else 0
    
    # Calculate efficiency score (based on utilization and availability)
    efficiency_score = min(10, round((utilization_rate + (available_cylinders / total_cylinders * 100 if total_cylinders > 0 else 0)) / 20))
    
    # Days since first customer/cylinder
    from datetime import datetime
    import json
    
    days_active = 1
    try:
        if os.path.exists('data/customers.json'):
            with open('data/customers.json', 'r') as f:
                customer_data = json.load(f)
                if customer_data:
                    oldest_date = min([c.get('created_at', datetime.now().isoformat()) for c in customer_data])
                    if oldest_date:
                        oldest = datetime.fromisoformat(oldest_date.replace('Z', '+00:00').split('.')[0])
                        days_active = (datetime.now() - oldest).days + 1
    except:
        pass
    
    stats = {
        'total_customers': len(customers),
        'total_cylinders': total_cylinders,
        'available_cylinders': available_cylinders,
        'rented_cylinders': rented_cylinders,
        'maintenance_cylinders': maintenance_cylinders,
        'utilization_rate': utilization_rate,
        'top_customer_count': top_customer_count,
        'efficiency_score': efficiency_score,
        'days_active': days_active
    }
    
    # Send email
    success = email_service.send_admin_stats(email, stats)
    
    if success:
        flash(f'Statistics sent successfully to {email}', 'success')
    else:
        flash('Failed to send email. Please check your email configuration.', 'error')
    
    return redirect(url_for('metrics'))

@app.route('/test_email', methods=['POST'])
@login_required
@admin_required
def test_email():
    """Send a test email to verify configuration"""
    if not EMAIL_AVAILABLE or not email_service:
        flash('Email service not available', 'error')
        return redirect(url_for('metrics'))
    
    email = request.form.get('test_email', '').strip()
    if not email:
        flash('Please enter a valid email address', 'error')
        return redirect(url_for('metrics'))
    
    success = email_service.send_test_email(email)
    
    if success:
        flash(f'Test email sent successfully to {email}', 'success')
    else:
        flash('Failed to send test email. Please check your email configuration.', 'error')
    
    return redirect(url_for('metrics'))

# Customer routes
@app.route('/customers')
@login_required
def customers():
    """Display all customers with search functionality and pagination"""
    customer_model = Customer()
    cylinder_model = Cylinder()

    search_query = request.args.get('search', '')
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 25))
    
    if search_query:
        customers_list, total_customers = customer_model.get_all(search_query, page, per_page)
    else:
        customers_list, total_customers = customer_model.get_all(page=page, per_page=per_page)
    
    # Add rental count for each customer and sort by number of rentals (descending)
    all_cylinders, _ = cylinder_model.get_all()
    for customer in customers_list:
        # Count rented cylinders for this customer
        rented_cylinders = [c for c in all_cylinders if c.get('rented_to') == customer['id']]
        
        # Add rental days calculation for each cylinder
        for cylinder in rented_cylinders:
            cylinder['rental_days'] = cylinder_model.get_rental_days(cylinder)
            cylinder['serial_number'] = cylinder.get('serial_number') or cylinder_model.get_serial_number(cylinder.get('type', 'Other'), 1)
        
        customer['rented_cylinders'] = rented_cylinders
        customer['rental_count'] = len(rented_cylinders)
    
    # Sort customers by rental count in descending order
    customers_list.sort(key=lambda x: x.get('rental_count', 0), reverse=True)
    
    # Pagination (already handled by PostgreSQL)
    customers_paginated = customers_list
    
    # Calculate pagination info
    total_pages = (total_customers + per_page - 1) // per_page
    has_prev = page > 1
    has_next = page < total_pages
    
    pagination_info = {
        'page': page,
        'per_page': per_page,
        'total': total_customers,
        'total_pages': total_pages,
        'has_prev': has_prev,
        'has_next': has_next,
        'prev_num': page - 1 if has_prev else None,
        'next_num': page + 1 if has_next else None,
        'start_index': ((page - 1) * per_page) + 1 if customers_paginated else 0,
        'end_index': min(page * per_page, total_customers)
    }
    
    return render_template('customers.html', 
                          customers=customers_paginated, 
                          search_query=search_query,
                          pagination=pagination_info)

@app.route('/customer/<customer_id>/details')
@login_required
def customer_details(customer_id):
    """Display detailed information for a specific customer with rental history tabs"""
    customer_model = Customer()
    
    customer = customer_model.get_by_id(customer_id)
    if not customer:
        flash('Customer not found', 'error')
        return redirect(url_for('customers'))
    
    # Get rental history (active and past)
    from db_service import RentalHistoryService
    with RentalHistoryService() as service:
        history_data = service.get_customer_history(customer_id)
    
    # Get tab parameter
    tab = request.args.get('tab', 'active')
    
    # Get pagination parameters
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 25))
    
    # Select data based on tab
    if tab == 'past':
        cylinders_data = history_data['past']
    else:
        cylinders_data = history_data['active']
    
    # Pagination
    total_cylinders = len(cylinders_data)
    start = (page - 1) * per_page
    end = start + per_page
    cylinders_paginated = cylinders_data[start:end]
    
    # Calculate pagination info
    total_pages = (total_cylinders + per_page - 1) // per_page
    has_prev = page > 1
    has_next = page < total_pages
    
    pagination_info = {
        'page': page,
        'per_page': per_page,
        'total': total_cylinders,
        'total_pages': total_pages,
        'has_prev': has_prev,
        'has_next': has_next,
        'prev_num': page - 1 if has_prev else None,
        'next_num': page + 1 if has_next else None,
        'start_index': start + 1 if cylinders_paginated else 0,
        'end_index': min(end, total_cylinders)
    }
    
    # Calculate summary statistics
    active_count = len(history_data['active'])
    past_count = len(history_data['past'])
    
    if tab == 'active' and history_data['active']:
        avg_rental_days = sum(c.get('rental_days', 0) for c in history_data['active']) // active_count
        long_term_count = len([c for c in history_data['active'] if c.get('rental_days', 0) > 90])
    elif tab == 'past' and history_data['past']:
        avg_rental_days = sum(c.get('rental_days', 0) for c in history_data['past']) // past_count
        long_term_count = len([c for c in history_data['past'] if c.get('rental_days', 0) > 90])
    else:
        avg_rental_days = 0
        long_term_count = 0
    
    return render_template('customer_details.html', 
                         customer=customer, 
                         cylinders_data=cylinders_paginated,
                         active_count=active_count,
                         past_count=past_count,
                         current_tab=tab,
                         avg_rental_days=avg_rental_days,
                         long_term_count=long_term_count,
                         pagination=pagination_info)

@app.route('/customers/add', methods=['GET', 'POST'])
@admin_or_user_can_edit
def add_customer():
    """Add new customer"""
    if request.method == 'POST':
        # Validate required fields for new customer structure
        # Required: customer_no, customer_name, customer_address, customer_city, customer_state, customer_phone
        # Optional: customer_apgst, customer_cst
        required_fields = ['customer_no', 'customer_name', 'customer_address', 'customer_city', 'customer_state', 'customer_phone']
        customer_data = {}
        
        for field in required_fields:
            value = request.form.get(field, '').strip()
            if not value:
                # Create user-friendly field names for error messages
                display_name = field.replace('customer_', '').replace('_', ' ').title()
                flash(f'{display_name} is required', 'error')
                return render_template('add_customer.html')
            customer_data[field] = value
        
        # Add optional fields
        customer_data['customer_apgst'] = request.form.get('customer_apgst', '').strip()
        customer_data['customer_cst'] = request.form.get('customer_cst', '').strip()
        
        try:
            new_customer = customer_model.add(customer_data)
            flash(f'Customer {new_customer["customer_name"]} added successfully with ID: {new_customer["id"]}', 'success')
            return redirect(url_for('customers'))
        except Exception as e:
            flash(f'Error adding customer: {str(e)}', 'error')
    
    return render_template('add_customer.html')

@app.route('/customers/edit/<customer_id>', methods=['GET', 'POST'])
@admin_or_user_can_edit
def edit_customer(customer_id):
    """Edit existing customer"""
    customer = customer_model.get_by_id(customer_id)
    if not customer:
        flash('Customer not found', 'error')
        return redirect(url_for('customers'))
    
    if request.method == 'POST':
        # Validate required fields for new customer structure
        # Required: customer_no, customer_name, customer_address, customer_city, customer_state, customer_phone
        # Optional: customer_apgst, customer_cst
        required_fields = ['customer_no', 'customer_name', 'customer_address', 'customer_city', 'customer_state', 'customer_phone']
        customer_data = {}
        
        for field in required_fields:
            value = request.form.get(field, '').strip()
            if not value:
                # Create user-friendly field names for error messages
                display_name = field.replace('customer_', '').replace('_', ' ').title()
                flash(f'{display_name} is required', 'error')
                return render_template('edit_customer.html', customer=customer)
            customer_data[field] = value
        
        # Add optional fields
        customer_data['customer_apgst'] = request.form.get('customer_apgst', '').strip()
        customer_data['customer_cst'] = request.form.get('customer_cst', '').strip()
        
        try:
            updated_customer = customer_model.update(customer_id, customer_data)
            if updated_customer:
                flash(f'Customer {updated_customer["customer_name"]} updated successfully', 'success')
                return redirect(url_for('customers'))
            else:
                flash('Error updating customer', 'error')
        except Exception as e:
            flash(f'Error updating customer: {str(e)}', 'error')
    
    return render_template('edit_customer.html', customer=customer)

@app.route('/customers/delete/<customer_id>', methods=['POST'])
@admin_or_user_can_edit
def delete_customer(customer_id):
    """Delete customer"""
    try:
        if customer_model.delete(customer_id):
            flash('Customer deleted successfully', 'success')
        else:
            flash('Customer not found', 'error')
    except Exception as e:
        flash(f'Error deleting customer: {str(e)}', 'error')
    
    return redirect(url_for('customers'))

# Rental History routes
@app.route('/rental_history')
@login_required
def rental_history():
    """Display rental history with automatic cleanup of old records"""
    # Auto-cleanup records older than 6 months
    from db_service import RentalHistoryService
    with RentalHistoryService() as service:
        removed_count = service.cleanup_old_records()
    
    if removed_count > 0:
        flash(f'Automatically removed {removed_count} records older than 6 months', 'info')
    
    # Get pagination parameters
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    
    # Limit per_page to reasonable values
    per_page = min(max(per_page, 10), 200)
    
    search_query = request.args.get('search', '')
    customer_filter = request.args.get('customer', '')
    
    # Use RentalHistory service to get return records
    with RentalHistoryService() as service:
        all_transactions, _ = service.get_all()  # Get all rental history records
    
    # Convert SQLAlchemy objects to dicts for filtering
    transaction_dicts = []
    for t in all_transactions:
        if hasattr(t, 'customer_name'):  # SQLAlchemy object
            transaction_dicts.append({
                'customer_name': t.customer_name or '',
                'cylinder_custom_id': t.cylinder_custom_id or '',
                'customer_no': t.customer_no or '',
                'return_date': t.return_date.isoformat() if t.return_date else '',
                'dispatch_date': t.dispatch_date.isoformat() if t.dispatch_date else '',
                'rental_days': t.rental_days or 0,
                'cylinder_type': t.cylinder_type or '',
                'cylinder_size': t.cylinder_size or '',
                'customer_phone': t.customer_phone or '',
                'customer_address': t.customer_address or '',
                'location': t.location or ''
            })
        else:  # Already a dict
            transaction_dicts.append(t)
    
    all_transactions = transaction_dicts
    
    # Apply search filter
    if search_query:
        all_transactions = [t for t in all_transactions 
                          if search_query.lower() in t.get('customer_name', '').lower() or
                             search_query.lower() in t.get('cylinder_custom_id', '').lower() or
                             search_query.lower() in t.get('customer_no', '').lower()]
    
    # Apply customer filter  
    if customer_filter:
        all_transactions = [t for t in all_transactions 
                          if t.get('customer_no', '').upper() == customer_filter.upper()]
    
    # Sort by return date (most recent first)
    all_transactions.sort(key=lambda x: x.get('return_date', '') or x.get('date_returned', ''), reverse=True)
    
    # Calculate pagination
    total_transactions = len(all_transactions)
    start = (page - 1) * per_page
    end = start + per_page
    transactions_paginated = all_transactions[start:end]
    
    # Calculate pagination info
    total_pages = (total_transactions + per_page - 1) // per_page
    has_prev = page > 1
    has_next = page < total_pages
    
    pagination_info = {
        'page': page,
        'per_page': per_page,
        'total': total_transactions,
        'total_pages': total_pages,
        'has_prev': has_prev,
        'has_next': has_next,
        'prev_num': page - 1 if has_prev else None,
        'next_num': page + 1 if has_next else None,
        'start_index': start + 1 if transactions_paginated else 0,
        'end_index': min(end, total_transactions)
    }
    
    # Get unique customers for filter dropdown
    unique_customers = list(set((t.get('customer_no', ''), t.get('customer_name', '')) 
                               for t in all_transactions if t.get('customer_no')))
    unique_customers.sort(key=lambda x: x[1])  # Sort by customer name
    
    return render_template('rental_history.html',
                         transactions=transactions_paginated,
                         pagination=pagination_info,
                         search_query=search_query,
                         customer_filter=customer_filter,
                         unique_customers=unique_customers,
                         total_transactions=total_transactions)

# Cylinder routes
@app.route('/cylinders')
@login_required
def cylinders():
    """List all cylinders with search, filter functionality, and pagination"""

    # Get pagination parameters
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)  # Default 50 cylinders per page
    
    # Limit per_page to reasonable values
    per_page = min(max(per_page, 10), 200)  # Between 10 and 200 items per page
    
    search_query = request.args.get('search', '')
    status_filter = request.args.get('status', '')
    customer_filter = request.args.get('customer', '')
    type_filter = request.args.get('type_filter', '')
    rental_duration_filter = request.args.get('rental_duration', '')
    
    # Get all cylinders with search and pagination using PostgreSQL
    cylinders_list, total_cylinders = cylinder_model.get_all(
        search_query=search_query,
        page=page,
        per_page=per_page,
        filter_type=type_filter,
        filter_status=status_filter,
        rental_duration_filter=rental_duration_filter
    )
    
    # PostgreSQL model already returns dictionaries with calculated fields
    paginated_cylinders = cylinders_list
    
    # Calculate pagination info
    total_pages = (total_cylinders + per_page - 1) // per_page
    has_prev = page > 1
    has_next = page < total_pages
    prev_page = page - 1 if has_prev else None
    next_page = page + 1 if has_next else None
    
    # Create pagination object for template
    pagination = {
        'page': page,
        'per_page': per_page,
        'total': total_cylinders,
        'total_pages': total_pages,
        'has_prev': has_prev,
        'has_next': has_next,
        'prev_page': prev_page,
        'next_page': next_page,
        'pages': list(range(max(1, page - 2), min(total_pages + 1, page + 3)))  # Show 5 pages around current
    }
    
    # Get all customers for the filter dropdown
    customers = customer_model.get_all()

    return render_template('cylinders.html', 
                         cylinders=paginated_cylinders, 
                         customers=customers,
                         search_query=search_query,
                         status_filter=status_filter,
                         customer_filter=customer_filter,
                         type_filter=type_filter,
                         pagination=pagination,
                         rental_duration_filter=rental_duration_filter,
                         cylinder_model=cylinder_model)

@app.route('/cylinders/<cylinder_id>/details')
@login_required
def cylinder_details(cylinder_id):
    """Display detailed information for a specific cylinder"""
    cylinder = cylinder_model.get_by_id(cylinder_id)
    if not cylinder:
        flash('Cylinder not found', 'error')
        return redirect(url_for('cylinders'))
    
    # Add display ID (custom_id if available, otherwise generated serial)
    cylinder['display_serial'] = cylinder_model.get_display_id(cylinder)
    
    # Add rental days calculation
    cylinder['rental_days'] = cylinder_model.get_rental_days(cylinder)
    cylinder['rental_months'] = cylinder['rental_days'] // 30
    
    # Get customer info if cylinder is rented
    if cylinder.get('rented_to'):
        customer = customer_model.get_by_id(cylinder['rented_to'])
        if customer:
            cylinder['customer_name'] = customer.get('customer_name') or customer.get('name', 'Unknown Customer')
            cylinder['customer_phone'] = customer.get('customer_phone') or customer.get('phone', 'N/A')
    
    return render_template('cylinder_details.html', cylinder=cylinder)

@app.route('/cylinders/add', methods=['GET', 'POST'])
@admin_or_user_can_edit
def add_cylinder():
    """Add new cylinder"""
    if request.method == 'POST':
        # Validate required fields - custom_id is now REQUIRED
        required_fields = ['custom_id', 'type', 'size', 'status', 'location']
        cylinder_data = {}
        
        for field in required_fields:
            value = request.form.get(field, '').strip()
            if not value:
                field_display = 'ID' if field == 'custom_id' else field.replace('_', ' ').title()
                flash(f'{field_display} is required', 'error')
                customers = customer_model.get_all()
                return render_template('add_cylinder.html', customers=customers, today_date=datetime.now().strftime('%Y-%m-%d'))
            cylinder_data[field] = value
        
        # Add optional fields - serial number is now optional
        # (No need to set custom_id here since it's now in required_fields)
        cylinder_data['pressure'] = request.form.get('pressure', '').strip()
        cylinder_data['last_inspection'] = request.form.get('last_inspection', '').strip()
        cylinder_data['next_inspection'] = request.form.get('next_inspection', '').strip()
        cylinder_data['notes'] = request.form.get('notes', '').strip()
        
        # Validate custom_id uniqueness (now required)
        existing_cylinders = cylinder_model.get_all()
        for existing in existing_cylinders:
            if existing.get('custom_id') == cylinder_data['custom_id']:
                flash(f'ID "{cylinder_data["custom_id"]}" is already in use. Please choose a different one.', 'error')
                customers = customer_model.get_all()
                return render_template('add_cylinder.html', customers=customers, today_date=datetime.now().strftime('%Y-%m-%d'))
        
        # Handle customer assignment for rented cylinders
        rented_to = request.form.get('rented_to', '').strip()
        if cylinder_data['status'].lower() == 'rented':
            if not rented_to:
                flash('Customer selection is required when status is "Rented"', 'error')
                customers = customer_model.get_all()
                return render_template('add_cylinder.html', customers=customers)
            
            # Verify customer exists
            customer = customer_model.get_by_id(rented_to)
            if not customer:
                flash('Selected customer not found', 'error')
                customers = customer_model.get_all()
                return render_template('add_cylinder.html', customers=customers)
            
            cylinder_data['rented_to'] = rented_to
            cylinder_data['customer_name'] = customer.get('name', '')
            cylinder_data['customer_email'] = customer.get('email', '')
            
            # Handle rental date from form or use current date
            rental_date = request.form.get('rental_date', '').strip()
            from datetime import datetime
            if rental_date:
                # Convert date string to ISO format
                try:
                    date_obj = datetime.strptime(rental_date, '%Y-%m-%d')
                    cylinder_data['date_borrowed'] = date_obj.isoformat()
                    cylinder_data['rental_date'] = date_obj.isoformat()
                except ValueError:
                    # Fallback to current date if invalid format
                    cylinder_data['date_borrowed'] = datetime.now().isoformat()
                    cylinder_data['rental_date'] = datetime.now().isoformat()
            else:
                cylinder_data['date_borrowed'] = datetime.now().isoformat()
                cylinder_data['rental_date'] = datetime.now().isoformat()
        
        try:
            new_cylinder = cylinder_model.add(cylinder_data)
            flash(f'Cylinder added successfully with ID: {new_cylinder["id"]}', 'success')
            return redirect(url_for('cylinders'))
        except Exception as e:
            flash(f'Error adding cylinder: {str(e)}', 'error')
    
    # Get all customers for the dropdown and today's date
    customers = customer_model.get_all()
    from datetime import datetime
    today_date = datetime.now().strftime('%Y-%m-%d')
    return render_template('add_cylinder.html', customers=customers, today_date=today_date)

@app.route('/cylinders/edit/<cylinder_id>', methods=['GET', 'POST'])
@admin_or_user_can_edit
def edit_cylinder(cylinder_id):
    """Edit existing cylinder"""
    cylinder = cylinder_model.get_by_id(cylinder_id)
    if not cylinder:
        flash('Cylinder not found', 'error')
        return redirect(url_for('cylinders'))
    
    if request.method == 'POST':
        # Validate required fields
        required_fields = ['type', 'size', 'status', 'location']
        cylinder_data = {}
        
        for field in required_fields:
            value = request.form.get(field, '').strip()
            if not value:
                flash(f'{field.replace("_", " ").title()} is required', 'error')
                customers = customer_model.get_all()
                return render_template('edit_cylinder.html', cylinder=cylinder, customers=customers)
            cylinder_data[field] = value
        
        # Add optional fields
        cylinder_data['custom_id'] = request.form.get('custom_id', '').strip()
        cylinder_data['pressure'] = request.form.get('pressure', '').strip()
        cylinder_data['last_inspection'] = request.form.get('last_inspection', '').strip()
        cylinder_data['next_inspection'] = request.form.get('next_inspection', '').strip()
        cylinder_data['notes'] = request.form.get('notes', '').strip()
        
        # Validate custom_id uniqueness if provided and different from current
        if cylinder_data['custom_id']:
            existing_cylinders = cylinder_model.get_all()
            for existing in existing_cylinders:
                if existing.get('custom_id') == cylinder_data['custom_id'] and existing.get('id') != cylinder_id:
                    flash(f'Custom ID "{cylinder_data["custom_id"]}" is already in use. Please choose a different one.', 'error')
                    customers = customer_model.get_all()
                    return render_template('edit_cylinder.html', cylinder=cylinder, customers=customers)
        
        # Handle customer assignment for rented cylinders
        rented_to = request.form.get('rented_to', '').strip()
        if cylinder_data['status'].lower() == 'rented':
            if not rented_to:
                flash('Customer selection is required when status is "Rented"', 'error')
                customers = customer_model.get_all()
                return render_template('edit_cylinder.html', cylinder=cylinder, customers=customers)
            
            # Verify customer exists
            customer = customer_model.get_by_id(rented_to)
            if not customer:
                flash('Selected customer not found', 'error')
                customers = customer_model.get_all()
                return render_template('edit_cylinder.html', cylinder=cylinder, customers=customers)
            
            cylinder_data['rented_to'] = rented_to
        else:
            # Clear customer assignment if not rented
            cylinder_data['rented_to'] = ''

        # Handle date tracking fields
        date_borrowed = request.form.get('date_borrowed', '').strip()
        date_returned = request.form.get('date_returned', '').strip()
        
        # Get current status and new status
        current_status = cylinder.get('status', '').lower()
        new_status = cylinder_data['status'].lower()
        
        # Auto-set dates based on status changes
        from datetime import datetime
        
        # If status is changing to 'rented', set date_borrowed
        if new_status == 'rented' and current_status != 'rented':
            if not date_borrowed:
                cylinder_data['date_borrowed'] = datetime.now().isoformat()
            else:
                # Convert datetime-local format to ISO format
                try:
                    dt = datetime.fromisoformat(date_borrowed)
                    cylinder_data['date_borrowed'] = dt.isoformat()
                except:
                    cylinder_data['date_borrowed'] = datetime.now().isoformat()
            # Clear return date when renting
            cylinder_data['date_returned'] = ''
            
        # If status is changing to 'available' from 'rented', set date_returned
        elif new_status == 'available' and current_status == 'rented':
            if not date_returned:
                cylinder_data['date_returned'] = datetime.now().isoformat()
            else:
                # Convert datetime-local format to ISO format
                try:
                    dt = datetime.fromisoformat(date_returned)
                    cylinder_data['date_returned'] = dt.isoformat()
                except:
                    cylinder_data['date_returned'] = datetime.now().isoformat()
        
        # If manually setting dates, convert them to proper format
        else:
            if date_borrowed:
                try:
                    dt = datetime.fromisoformat(date_borrowed)
                    cylinder_data['date_borrowed'] = dt.isoformat()
                except:
                    pass
            if date_returned:
                try:
                    dt = datetime.fromisoformat(date_returned)
                    cylinder_data['date_returned'] = dt.isoformat()
                except:
                    pass
        
        try:
            updated_cylinder = cylinder_model.update(cylinder_id, cylinder_data)
            if updated_cylinder:
                display_id = cylinder_model.get_display_id(updated_cylinder)
                flash(f'Cylinder {display_id} updated successfully', 'success')
                return redirect(url_for('cylinders'))
            else:
                flash('Error updating cylinder', 'error')
        except Exception as e:
            flash(f'Error updating cylinder: {str(e)}', 'error')
    
    # Get all customers for the dropdown and add display ID
    customers = customer_model.get_all()
    cylinder['display_serial'] = cylinder_model.get_display_id(cylinder)
    return render_template('edit_cylinder.html', cylinder=cylinder, customers=customers)

@app.route('/cylinders/delete/<cylinder_id>', methods=['POST'])
@admin_or_user_can_edit
def delete_cylinder(cylinder_id):
    """Delete cylinder"""
    try:
        if cylinder_model.delete(cylinder_id):
            flash('Cylinder deleted successfully', 'success')
        else:
            flash('Cylinder not found', 'error')
    except Exception as e:
        flash(f'Error deleting cylinder: {str(e)}', 'error')
    
    return redirect(url_for('cylinders'))

# Data Import routes
@app.route('/import')
@login_required
def import_data():
    """Data import dashboard"""
    if not ACCESS_AVAILABLE:
        flash('MS Access import functionality is not available on this system', 'error')
        return redirect(url_for('index'))
    return render_template('import_data.html')

@app.route('/import/upload', methods=['POST'])
def upload_access_file():
    """Upload and connect to Access database"""
    if not ACCESS_AVAILABLE:
        flash('MS Access import functionality is not available', 'error')
        return redirect(url_for('index'))
    
    if 'access_file' not in request.files:
        flash('No file selected', 'error')
        return redirect(url_for('import_data'))
    
    file = request.files['access_file']
    if file.filename == '':
        flash('No file selected', 'error')
        return redirect(url_for('import_data'))
    
    if not file.filename.lower().endswith(('.mdb', '.accdb')):
        flash('Please select a valid Access database file (.mdb or .accdb)', 'error')
        return redirect(url_for('import_data'))
    
    try:
        # Save uploaded file temporarily with unique name to avoid conflicts
        import time
        timestamp = str(int(time.time()))
        temp_dir = tempfile.gettempdir()
        temp_path = os.path.join(temp_dir, f"temp_access_db{timestamp}.mdb")
        file.save(temp_path)
        
        # Try to connect
        importer = DataImporter()
        try:
            if importer.connect_to_access(temp_path):
                # Store file path in session
                session['access_file_path'] = temp_path
                session['access_file_name'] = file.filename
                
                # Get available tables
                tables = importer.get_available_tables()
                
                if tables:
                    flash(f'Successfully connected to {file.filename}. Found {len(tables)} tables.', 'success')
                    return render_template('select_tables.html', tables=tables, filename=file.filename)
                else:
                    flash('No tables found in the database', 'error')
                    return redirect(url_for('import_data'))
            else:
                flash('Failed to connect to Access database. Please check the file format and try again.', 'error')
                return redirect(url_for('import_data'))
        finally:
            # Always close connection to release file locks
            importer.close_connection()
            
    except Exception as e:
        flash(f'Error processing file: {str(e)}', 'error')
        if 'temp_path' in locals() and os.path.exists(temp_path):
            os.remove(temp_path)
        return redirect(url_for('import_data'))

@app.route('/import/preview/<table_name>')
def preview_table(table_name):
    """Preview table data and set up field mapping"""
    if 'access_file_path' not in session:
        flash('No Access file connected. Please upload a file first.', 'error')
        return redirect(url_for('import_data'))
    
    try:
        importer = DataImporter()
        if not importer.connect_to_access(session['access_file_path']):
            flash('Failed to reconnect to Access database', 'error')
            return redirect(url_for('import_data'))
        
        # Get table structure and preview data
        columns, preview_data = importer.preview_table(table_name)
        
        # Determine import type based on user selection
        import_type = request.args.get('type', 'customer')
        
        # Get suggested field mapping based on import type
        if import_type == 'transaction' or import_type == 'rental_history':
            suggested_mapping = importer.suggest_transaction_field_mapping(table_name)
        else:
            suggested_mapping = importer.suggest_field_mapping(table_name, import_type)
        
        importer.close_connection()
        
        return render_template('map_fields.html', 
                             table_name=table_name,
                             columns=columns,
                             preview_data=preview_data,
                             import_type=import_type,
                             suggested_mapping=suggested_mapping,
                             filename=session.get('access_file_name', 'Unknown'))
        
    except Exception as e:
        flash(f'Error previewing table: {str(e)}', 'error')
        return redirect(url_for('import_data'))

@app.route('/import/execute', methods=['POST'])
def execute_import():
    """Execute the data import"""
    if 'access_file_path' not in session:
        flash('No Access file connected. Please upload a file first.', 'error')
        return redirect(url_for('import_data'))
    
    try:
        table_name = request.form.get('table_name')
        import_type = request.form.get('import_type')
        skip_duplicates = request.form.get('skip_duplicates') == 'on'
        
        # Build field mapping from form data
        field_mapping = {}
        for key, value in request.form.items():
            if key.startswith('mapping_') and value:
                target_field = key.replace('mapping_', '')
                field_mapping[target_field] = value
        
        if not field_mapping:
            flash('Please map at least one field', 'error')
            return redirect(url_for('preview_table', table_name=table_name, type=import_type))
        
        # Execute instant import - no DataImporter needed
        from instant_importer import InstantImporter
        instant_importer = InstantImporter()
        
        print(f"🚀 Starting INSTANT {import_type.upper()} import...")
        imported, skipped, errors = instant_importer.instant_import(
            session['access_file_path'], 
            table_name, 
            field_mapping,
            import_type
        )
        
        if import_type == 'customer':
            item_type = 'customers'
        elif import_type == 'cylinder':
            item_type = 'cylinders'
        elif import_type == 'transaction':
            item_type = 'transactions'
        elif import_type == 'rental_history':
            item_type = 'rental history records'
        else:
            flash('Invalid import type', 'error')
            return redirect(url_for('import_data'))
        
        # Clean up temp file with retry logic for Windows
        temp_file_path = session.get('access_file_path')
        if temp_file_path and os.path.exists(temp_file_path):
            max_retries = 5
            for attempt in range(max_retries):
                try:
                    import time
                    time.sleep(0.2)  # Small delay to let file handles close
                    os.remove(temp_file_path)
                    print(f"Successfully removed temporary file: {temp_file_path}")
                    break
                except PermissionError as pe:
                    if attempt == max_retries - 1:
                        print(f"Warning: Could not remove temp file after {max_retries} attempts: {pe}")
                    else:
                        time.sleep(1)  # Wait longer between retries
                except Exception as e:
                    print(f"Warning: Error removing temp file: {e}")
                    break
        
        session.pop('access_file_path', None)
        session.pop('access_file_name', None)
        
        # Show results
        if imported > 0:
            flash(f'Successfully imported {imported} {item_type}', 'success')
        if skipped > 0:
            flash(f'Skipped {skipped} records (duplicates or missing data)', 'warning')
        if errors:
            for error in errors[:5]:  # Show first 5 errors
                flash(error, 'error')
            if len(errors) > 5:
                flash(f'... and {len(errors) - 5} more errors', 'error')
        
        # Show instant completion
        flash(f'🚀 INSTANT IMPORT COMPLETE! Processed {imported:,} {item_type} with zero overhead', 'success')
        
        # Redirect to appropriate page
        if import_type == 'customer':
            return redirect(url_for('customers'))
        elif import_type == 'rental_history':
            return redirect(url_for('rental_history'))
        else:
            return redirect(url_for('cylinders'))
        
    except Exception as e:
        flash(f'Error during import: {str(e)}', 'error')
        # Clean up on error
        temp_file_path = session.get('access_file_path')
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.remove(temp_file_path)
            except:
                pass
        session.pop('access_file_path', None)
        session.pop('access_file_name', None)
        return redirect(url_for('import_data'))

@app.route('/import/cancel')
def cancel_import():
    """Cancel import and clean up"""
    if 'access_file_path' in session:
        if os.path.exists(session['access_file_path']):
            os.remove(session['access_file_path'])
        session.pop('access_file_path', None)
        session.pop('access_file_name', None)
    
    flash('Import cancelled', 'info')
    return redirect(url_for('import_data'))

# Global Search route
@app.route('/search')
@login_required
def global_search():
    """Global search across customers and cylinders"""
    query = request.args.get('q', '').strip()
    
    results = {
        'customers': [],
        'cylinders': [],
        'query': query,
        'total_results': 0
    }
    
    if query:
        # Search customers
        customer_results = customer_model.search(query)
        results['customers'] = customer_results
        
        # Search cylinders
        cylinder_results = cylinder_model.search(query)
        results['cylinders'] = cylinder_results
        
        results['total_results'] = len(customer_results) + len(cylinder_results)
    
    return render_template('search_results.html', **results)

@app.route('/users/delete/<user_id>', methods=['POST'])
@admin_required
def delete_user(user_id):
    """Delete user (admin only)"""
    try:
        if user_manager.delete_user(user_id):
            flash('User deleted successfully', 'success')
        else:
            flash('User not found', 'error')
    except ValueError as e:
        flash(str(e), 'error')
    except Exception as e:
        flash(f'Error deleting user: {str(e)}', 'error')
    
    return redirect(url_for('users'))

@app.route('/cylinders/rent/<cylinder_id>', methods=['POST'])
@user_or_admin_required
def rent_cylinder(cylinder_id):
    """Rent a cylinder to a customer"""
    customer_id = request.form.get('customer_id')
    rental_date = request.form.get('rental_date', '').strip()
    
    if not customer_id:
        flash('Please select a customer', 'error')
        return redirect(url_for('cylinders'))
    
    # Verify customer exists
    customer = customer_model.get_by_id(customer_id)
    if not customer:
        flash('Customer not found', 'error')
        return redirect(url_for('cylinders'))
    
    # Convert rental_date to ISO format if provided
    rental_date_iso = None
    if rental_date:
        try:
            from datetime import datetime
            # Parse datetime-local format (YYYY-MM-DDTHH:MM) and convert to ISO
            dt = datetime.fromisoformat(rental_date)
            rental_date_iso = dt.isoformat()
        except ValueError:
            flash('Invalid rental date format', 'error')
            return redirect(url_for('cylinders'))
    
    # Get cylinder for display
    cylinder = cylinder_model.get_by_id(cylinder_id)
    display_id = cylinder_model.get_display_id(cylinder) if cylinder else 'Unknown'
    
    # Rent the cylinder with optional rental date
    if cylinder_model.rent_cylinder(cylinder_id, customer_id, rental_date_iso):
        flash(f'Cylinder {display_id} rented to {customer.get("customer_name") or customer.get("name", "customer")} successfully', 'success')
    else:
        flash(f'Error renting cylinder {display_id}', 'error')
    
    return redirect(url_for('cylinders'))

@app.route('/cylinders/return/<cylinder_id>', methods=['POST'])
@user_or_admin_required
def return_cylinder(cylinder_id):
    """Return a cylinder from rental"""
    return_date = request.form.get('return_date')
    if cylinder_model.return_cylinder(cylinder_id, return_date):
        flash('Cylinder returned successfully', 'success')
    else:
        flash('Error returning cylinder', 'error')
    
    return redirect(url_for('cylinders'))

@app.route('/cylinder/<cylinder_id>/return/customer/<customer_id>', methods=['POST'])
@user_or_admin_required
def return_cylinder_custom(cylinder_id, customer_id):
    """Return cylinder with custom date from customer details page"""
    return_date = request.form.get('return_date', datetime.now().strftime('%Y-%m-%d'))
    
    if cylinder_model.return_cylinder(cylinder_id, return_date):
        flash(f'Cylinder returned successfully on {return_date}', 'success')
    else:
        flash('Failed to return cylinder', 'error')
    
    return redirect(url_for('customer_details', customer_id=customer_id, tab='active'))

@app.route('/customers/<customer_id>/bulk_cylinders', methods=['GET', 'POST'])
@user_or_admin_required
def bulk_cylinder_management(customer_id):
    """Bulk cylinder rental/return management"""
    customer = customer_model.get_by_id(customer_id)
    if not customer:
        flash('Customer not found', 'error')
        return redirect(url_for('customers'))
    
    if request.method == 'GET':
        # Get current rentals for this customer
        current_rentals = cylinder_model.get_by_customer(customer_id)
        return render_template('bulk_cylinder_management.html', 
                             customer=customer, 
                             current_rentals=current_rentals)
    
    cylinder_ids_text = request.form.get('cylinder_ids', '').strip()
    action = request.form.get('action', 'rent')
    date = request.form.get('date', '').strip()
    
    if not cylinder_ids_text:
        flash('Please enter at least one cylinder ID', 'error')
        return redirect(url_for('bulk_cylinder_management', customer_id=customer_id))
    
    if not date:
        flash('Please select a date', 'error')
        return redirect(url_for('bulk_cylinder_management', customer_id=customer_id))
    
    # Parse cylinder IDs from text (support both comma-separated and line-separated)
    cylinder_ids = []
    for line in cylinder_ids_text.replace(',', '\n').split('\n'):
        cylinder_id = line.strip()
        if cylinder_id:
            cylinder_ids.append(cylinder_id)
    
    if not cylinder_ids:
        flash('No valid cylinder IDs found', 'error')
        return redirect(url_for('bulk_cylinder_management', customer_id=customer_id))
    
    processed = 0
    skipped = 0
    errors = []
    
    for cylinder_id in cylinder_ids:
        cylinder = cylinder_model.find_by_any_identifier(cylinder_id)
        
        if not cylinder:
            errors.append(f'"{cylinder_id}": Not found in database')
            skipped += 1
            continue
        
        # Use the actual system ID for operations
        actual_cylinder_id = cylinder.get('id')
        cylinder_display = cylinder.get('custom_id') or cylinder.get('serial_number') or actual_cylinder_id
        
        if action == 'rent':
            # Check if cylinder is available
            if cylinder.get('status', '').lower() != 'available':
                errors.append(f'"{cylinder_display}": Not available (current status: {cylinder.get("status", "unknown")})')
                skipped += 1
                continue
            
            # Rent the cylinder with custom date
            # Convert date from YYYY-MM-DD to datetime ISO format
            rental_datetime = f"{date}T00:00:00"
            success = cylinder_model.rent_cylinder(actual_cylinder_id, customer_id, rental_datetime)
            if success:
                processed += 1
            else:
                errors.append(f'"{cylinder_display}": Failed to dispatch')
                skipped += 1
        
        elif action == 'return':
            # Check if cylinder is rented to this customer
            if cylinder.get('status', '').lower() != 'rented' or cylinder.get('rented_to') != customer_id:
                errors.append(f'"{cylinder_display}": Not rented to this customer')
                skipped += 1
                continue
            
            # Return the cylinder with custom date
            # Convert date from YYYY-MM-DD to datetime ISO format
            return_datetime = f"{date}T00:00:00"
            success = cylinder_model.return_cylinder(actual_cylinder_id, return_datetime)
            if success:
                processed += 1
            else:
                errors.append(f'"{cylinder_display}": Failed to return')
                skipped += 1
    
    # Create summary message
    customer_name = customer.get('customer_name') or customer.get('name', 'Unknown Customer')
    if action == 'rent':
        flash(f'Successfully dispatched {processed} cylinders to {customer_name}', 'success')
    else:
        flash(f'Successfully returned {processed} cylinders from {customer["name"]}', 'success')
    
    if skipped > 0:
        flash(f'{skipped} cylinders were skipped due to errors', 'warning')
        
    # Show detailed errors if any
    if errors:
        error_msg = 'Details: ' + '; '.join(errors[:5])  # Show first 5 errors
        if len(errors) > 5:
            error_msg += f' and {len(errors) - 5} more...'
        flash(error_msg, 'info')
    
    return redirect(url_for('bulk_cylinder_management', customer_id=customer_id))

@app.route('/api/customer/<customer_id>/rentals')
@login_required
def get_customer_rentals(customer_id):
    """API endpoint to get current rentals for a customer"""
    rentals = cylinder_model.get_by_customer(customer_id)
    
    # Add rental days calculation
    for rental in rentals:
        rental['rental_days'] = cylinder_model.get_rental_days(rental)
    
    return jsonify({'rentals': rentals})

@app.route('/archive_data', methods=['POST'])
@login_required
@admin_required
def archive_data():
    """Archive old data (admin only)"""
    try:
        months_old = int(request.form.get('months', 6))
        if months_old < 1:
            months_old = 6
        
        # Archive both cylinder and customer data
        cylinder_result = cylinder_model.archive_old_data(months_old)
        customer_result = customer_model.archive_old_data(months_old)
        
        # Combine results
        total_archived = cylinder_result.get('archived_count', 0) + customer_result.get('archived_count', 0)
        total_remaining = cylinder_result.get('remaining_count', 0) + customer_result.get('remaining_count', 0)
        
        # Check for errors
        if 'error' in cylinder_result or 'error' in customer_result:
            errors = []
            if 'error' in cylinder_result:
                errors.append(f"Cylinders: {cylinder_result['error']}")
            if 'error' in customer_result:
                errors.append(f"Customers: {customer_result['error']}")
            flash(f'Archive failed: {"; ".join(errors)}', 'error')
        elif total_archived > 0:
            archive_files = []
            if cylinder_result.get('archived_count', 0) > 0:
                archive_files.append(cylinder_result.get('archive_file', ''))
            if customer_result.get('archived_count', 0) > 0:
                archive_files.append(customer_result.get('archive_file', ''))
            
            flash(f'Successfully archived {total_archived} old records ({cylinder_result.get("archived_count", 0)} cylinders, {customer_result.get("archived_count", 0)} customers). Archives saved.', 'success')
        else:
            flash('No old data found to archive', 'info')
        

        
    except ValueError:
        flash('Invalid months value provided', 'error')
    except Exception as e:
        flash(f'Error during archiving: {str(e)}', 'error')
    
    return redirect(url_for('cylinders'))

@app.route('/bulk_rental_management')
@login_required
def bulk_rental_management():
    """Dedicated page for bulk cylinder rental management"""
    customers = customer_model.get_all()
    cylinders = cylinder_model.get_all()
    
    # Add customer names to cylinders for display
    for cylinder in cylinders:
        if cylinder.get('rented_to'):
            customer = customer_model.get_by_id(cylinder['rented_to'])
            if customer:
                cylinder['customer_name'] = customer.get('customer_name') or customer.get('name') or 'Unknown Customer'
    
    return render_template('bulk_rental_management.html', customers=customers, cylinders=cylinders)

@app.route('/bulk_rental_management/process', methods=['POST'])
@login_required
def process_bulk_rental():
    """Process bulk cylinder rental/return operations"""
    customer_id = request.form.get('customer_id', '').strip()
    action = request.form.get('action', 'rent')
    date = request.form.get('date', '').strip()
    cylinder_ids_text = request.form.get('cylinder_ids', '').strip()
    
    if not customer_id:
        flash('Please select a customer', 'error')
        return redirect(url_for('bulk_rental_management'))
    
    customer = customer_model.get_by_id(customer_id)
    if not customer:
        flash('Customer not found', 'error')
        return redirect(url_for('bulk_rental_management'))
    
    if not cylinder_ids_text:
        flash('Please enter at least one cylinder ID', 'error')
        return redirect(url_for('bulk_rental_management'))
    
    if not date:
        flash('Please select a date', 'error')
        return redirect(url_for('bulk_rental_management'))
    
    # Parse cylinder IDs from text (support both comma-separated and line-separated)
    cylinder_ids = []
    for line in cylinder_ids_text.replace(',', '\n').split('\n'):
        cylinder_id = line.strip()
        if cylinder_id:
            cylinder_ids.append(cylinder_id)
    
    if not cylinder_ids:
        flash('No valid cylinder IDs found', 'error')
        return redirect(url_for('bulk_rental_management'))
    
    processed = 0
    skipped = 0
    errors = []
    success_cylinders = []
    
    for cylinder_id in cylinder_ids:
        cylinder = cylinder_model.get_by_id(cylinder_id)
        
        if not cylinder:
            errors.append(f'Cylinder {cylinder_id}: Not found in database')
            skipped += 1
            continue
        
        if action == 'rent':
            # Check if cylinder is available
            if cylinder.get('status', '').lower() != 'available':
                errors.append(f'Cylinder {cylinder_id}: Not available (current status: {cylinder.get("status", "unknown")})')
                skipped += 1
                continue
            
            # Rent the cylinder with custom date
            # Convert date from YYYY-MM-DD to datetime ISO format
            rental_datetime = f"{date}T00:00:00"
            success = cylinder_model.rent_cylinder(cylinder_id, customer_id, rental_datetime)
            if success:
                processed += 1
                success_cylinders.append(cylinder_id)
            else:
                errors.append(f'Cylinder {cylinder_id}: Failed to dispatch')
                skipped += 1
        
        elif action == 'return':
            # Check if cylinder is rented to this customer
            if cylinder.get('status', '').lower() != 'rented' or cylinder.get('rented_to') != customer_id:
                errors.append(f'Cylinder {cylinder_id}: Not rented to this customer')
                skipped += 1
                continue
            
            # Return the cylinder with custom date
            # Convert date from YYYY-MM-DD to datetime ISO format  
            return_datetime = f"{date}T00:00:00"
            success = cylinder_model.return_cylinder(cylinder_id, return_datetime)
            if success:
                processed += 1
                success_cylinders.append(cylinder_id)
            else:
                errors.append(f'Cylinder {cylinder_id}: Failed to return')
                skipped += 1
    
    # Create summary message
    customer_name = customer.get('customer_name') or customer.get('name', 'Unknown Customer')
    if action == 'rent':
        if processed > 0:
            flash(f'Successfully dispatched {processed} cylinders ({", ".join(success_cylinders[:5])}{", ..." if len(success_cylinders) > 5 else ""}) to {customer_name}', 'success')
    else:
        if processed > 0:
            flash(f'Successfully returned {processed} cylinders ({", ".join(success_cylinders[:5])}{", ..." if len(success_cylinders) > 5 else ""}) from {customer_name}', 'success')
    
    if skipped > 0:
        flash(f'{skipped} cylinders were skipped due to errors', 'warning')
        
    # Show detailed errors if any
    if errors:
        error_msg = 'Details: ' + '; '.join(errors[:5])  # Show first 5 errors
        if len(errors) > 5:
            error_msg += f' and {len(errors) - 5} more...'
        flash(error_msg, 'info')
    
    return redirect(url_for('bulk_rental_management'))

@app.route('/customers/<customer_id>/active_dispatches')
@login_required
def customer_active_dispatches(customer_id):
    """View active dispatches for a specific customer with pagination"""
    customer_model = Customer()
    cylinder_model = Cylinder()
    
    # Get customer details
    customer = customer_model.get_by_id(customer_id)
    if not customer:
        flash('Customer not found', 'error')
        return redirect(url_for('customers'))
    
    # Get pagination parameters
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 25))
    
    # Get all cylinders rented to this customer
    cylinders = cylinder_model.get_all()
    customer_cylinders = [c for c in cylinders if c.get('rented_to') == customer_id]
    
    # Add rental days and display IDs for each cylinder
    for cylinder in customer_cylinders:
        cylinder['rental_days'] = cylinder_model.get_rental_days(cylinder)
        cylinder['display_id'] = cylinder_model.get_display_id(cylinder)
        cylinder['rental_months'] = cylinder['rental_days'] // 30
    
    # Sort by rental days (longest first)
    customer_cylinders.sort(key=lambda x: x.get('rental_days', 0), reverse=True)
    
    # Pagination
    total_cylinders = len(customer_cylinders)
    start = (page - 1) * per_page
    end = start + per_page
    cylinders_paginated = customer_cylinders[start:end]
    
    # Calculate pagination info
    total_pages = (total_cylinders + per_page - 1) // per_page
    has_prev = page > 1
    has_next = page < total_pages
    
    pagination_info = {
        'page': page,
        'per_page': per_page,
        'total': total_cylinders,
        'total_pages': total_pages,
        'has_prev': has_prev,
        'has_next': has_next,
        'prev_num': page - 1 if has_prev else None,
        'next_num': page + 1 if has_next else None,
        'start_index': start + 1 if cylinders_paginated else 0,
        'end_index': min(end, total_cylinders)
    }
    
    return render_template('customer_active_dispatches.html', 
                          customer=customer, 
                          customer_cylinders=cylinders_paginated,
                          pagination=pagination_info)

# Reports routes
@app.route('/reports')
@login_required
def reports():
    """Data reports and export page"""
    customer_model = Customer()
    cylinder_model = Cylinder()
    
    # Get current stats
    customers = customer_model.get_all()
    cylinders = cylinder_model.get_all()
    
    # Calculate stats
    active_rentals = len([c for c in cylinders if c.get('status', '').lower() == 'rented'])
    
    # Add rental count for sorting customers
    for customer in customers:
        rented_cylinders = [c for c in cylinders if c.get('rented_to') == customer['id']]
        customer['rental_count'] = len(rented_cylinders)
    
    # Sort customers by rental count descending
    customers.sort(key=lambda x: x.get('rental_count', 0), reverse=True)
    
    stats = {
        'total_customers': len(customers),
        'total_cylinders': len(cylinders),
        'active_rentals': active_rentals
    }
    
    return render_template('reports.html', stats=stats, customers=customers)

@app.route('/export/customers.csv')
@login_required
def export_customers_csv():
    """Export all customers to CSV"""
    customer_model = Customer()
    customers = customer_model.get_all()
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write headers
    writer.writerow(['ID', 'Customer No', 'Name', 'Email', 'Phone', 'Address', 'City', 'State', 'APGST', 'CST', 'Created At', 'Updated At', 'Notes'])
    
    # Write customer data
    for customer in customers:
        writer.writerow([
            customer.get('id', ''),
            customer.get('customer_no', ''),
            customer.get('customer_name', '') or customer.get('name', ''),
            customer.get('customer_email', '') or customer.get('email', ''),
            customer.get('customer_phone', '') or customer.get('phone', ''),
            customer.get('customer_address', '') or customer.get('address', ''),
            customer.get('customer_city', ''),
            customer.get('customer_state', ''),
            customer.get('customer_apgst', ''),
            customer.get('customer_cst', ''),
            customer.get('created_at', ''),
            customer.get('updated_at', ''),
            customer.get('notes', '')
        ])
    
    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': f'attachment; filename=customers_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'}
    )

@app.route('/export/cylinders.csv')
@login_required
def export_cylinders_csv():
    """Export all cylinders to CSV"""
    cylinder_model = Cylinder()
    cylinders = cylinder_model.get_all()
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write headers
    writer.writerow(['ID', 'Serial Number', 'Type', 'Size', 'Status', 'Location', 
                    'Pressure', 'Last Inspection', 'Next Inspection', 'Customer Name',
                    'Date Borrowed', 'Date Returned', 'Notes'])
    
    # Write cylinder data
    for cylinder in cylinders:
        display_id = cylinder_model.get_display_id(cylinder)
        
        # Format dispatch and return dates properly
        dispatch_date = cylinder.get('date_borrowed', '') or cylinder.get('rental_date', '')
        if dispatch_date and len(dispatch_date) >= 10:
            dispatch_date = dispatch_date[:10]  # Extract YYYY-MM-DD part
        
        return_date = cylinder.get('date_returned', '')
        if return_date and len(return_date) >= 10:
            return_date = return_date[:10]  # Extract YYYY-MM-DD part
        
        writer.writerow([
            display_id,
            cylinder.get('serial_number', ''),
            cylinder.get('type', ''),
            cylinder.get('size', ''),
            cylinder.get('status', ''),
            cylinder.get('location', ''),
            cylinder.get('pressure', ''),
            cylinder.get('last_inspection', ''),
            cylinder.get('next_inspection', ''),
            cylinder.get('customer_name', ''),
            dispatch_date,
            return_date,
            cylinder.get('notes', '')
        ])
    
    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': f'attachment; filename=cylinders_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'}
    )

@app.route('/export/rental-activities.csv')
@login_required
def export_rental_activities_csv():
    """Export rental activities to CSV"""
    cylinder_model = Cylinder()
    customer_model = Customer()
    cylinders = cylinder_model.get_all()
    customers = customer_model.get_all()
    
    # Create customer lookup
    customer_lookup = {c['id']: c for c in customers}
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write headers
    writer.writerow(['Cylinder ID', 'Serial Number', 'Type', 
                    'Customer Name', 'Customer Email', 'Date Borrowed', 'Date Returned', 
                    'Status', 'Rental Days'])
    
    # Write rental data
    for cylinder in cylinders:
        if cylinder.get('rented_to') or cylinder.get('date_borrowed'):
            customer = customer_lookup.get(cylinder.get('rented_to', ''), {})
            rental_days = cylinder_model.get_rental_days(cylinder)
            display_id = cylinder_model.get_display_id(cylinder)
            
            # Format dispatch and return dates properly
            dispatch_date = cylinder.get('date_borrowed', '') or cylinder.get('rental_date', '')
            if dispatch_date and len(dispatch_date) >= 10:
                dispatch_date = dispatch_date[:10]  # Extract YYYY-MM-DD part
            
            return_date = cylinder.get('date_returned', '')
            if return_date and len(return_date) >= 10:
                return_date = return_date[:10]  # Extract YYYY-MM-DD part
            
            writer.writerow([
                display_id,
                cylinder.get('serial_number', ''),
                cylinder.get('type', ''),
                customer.get('customer_name', '') or customer.get('name', ''),
                customer.get('customer_email', '') or customer.get('email', ''),
                dispatch_date,
                return_date,
                cylinder.get('status', ''),
                rental_days
            ])
    
    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': f'attachment; filename=rental_activities_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'}
    )

@app.route('/export/complete-data.csv')
@login_required
def export_complete_data_csv():
    """Export complete database to CSV"""
    customer_model = Customer()
    cylinder_model = Cylinder()
    customers = customer_model.get_all()
    cylinders = cylinder_model.get_all()
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write a complete report with all data
    writer.writerow(['=== COMPLETE DATABASE EXPORT ==='])
    writer.writerow(['Export Date:', datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
    writer.writerow(['Total Customers:', len(customers)])
    writer.writerow(['Total Cylinders:', len(cylinders)])
    writer.writerow([])
    
    # Customers section
    writer.writerow(['=== CUSTOMERS ==='])
    writer.writerow(['ID', 'Customer No', 'Name', 'Email', 'Phone', 'Address', 'City', 'State', 'APGST', 'CST', 'Created At', 'Notes'])
    for customer in customers:
        writer.writerow([
            customer.get('id', ''),
            customer.get('customer_no', ''),
            customer.get('customer_name', '') or customer.get('name', ''),
            customer.get('customer_email', '') or customer.get('email', ''),
            customer.get('customer_phone', '') or customer.get('phone', ''),
            customer.get('customer_address', '') or customer.get('address', ''),
            customer.get('customer_city', ''),
            customer.get('customer_state', ''),
            customer.get('customer_apgst', ''),
            customer.get('customer_cst', ''),
            customer.get('created_at', ''),
            customer.get('notes', '')
        ])
    
    writer.writerow([])
    
    # Cylinders section
    writer.writerow(['=== CYLINDERS ==='])
    writer.writerow(['ID', 'Serial Number', 'Type', 'Size', 'Status', 'Location', 
                    'Pressure', 'Customer Name', 'Date Borrowed', 'Rental Days'])
    for cylinder in cylinders:
        rental_days = cylinder_model.get_rental_days(cylinder)
        display_id = cylinder_model.get_display_id(cylinder)
        # Format dispatch date properly
        dispatch_date = cylinder.get('date_borrowed', '') or cylinder.get('rental_date', '')
        if dispatch_date and len(dispatch_date) >= 10:
            dispatch_date = dispatch_date[:10]  # Extract YYYY-MM-DD part
        
        writer.writerow([
            display_id,
            cylinder.get('serial_number', ''),
            cylinder.get('type', ''),
            cylinder.get('size', ''),
            cylinder.get('status', ''),
            cylinder.get('location', ''),
            cylinder.get('pressure', ''),
            cylinder.get('customer_name', ''),
            dispatch_date,
            rental_days
        ])
    
    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': f'attachment; filename=complete_database_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'}
    )

@app.route('/export/customer-report', methods=['POST'])
@login_required
def export_customer_report():
    """Export individual customer report with dispatched cylinders sorted by rental days"""
    customer_id = request.form.get('customer_id')
    export_format = request.form.get('export_format', 'csv')
    
    if not customer_id:
        flash('Please select a customer', 'error')
        return redirect(url_for('reports'))
    
    customer_model = Customer()
    cylinder_model = Cylinder()
    
    # Get customer details
    customer = customer_model.get_by_id(customer_id)
    if not customer:
        flash('Customer not found', 'error')
        return redirect(url_for('reports'))
    
    # Get all cylinders dispatched to this customer
    all_cylinders = cylinder_model.get_all()
    customer_cylinders = [c for c in all_cylinders if c.get('rented_to') == customer_id]
    
    # Add rental days and sort by descending rental days
    for cylinder in customer_cylinders:
        cylinder['rental_days'] = cylinder_model.get_rental_days(cylinder)
    
    # Sort by rental days descending (longest rentals first)
    customer_cylinders.sort(key=lambda x: x.get('rental_days', 0), reverse=True)
    
    customer_name = customer.get('customer_name') or customer.get('name', 'Unknown Customer')
    safe_filename = customer_name.replace(' ', '_').replace('/', '_')
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    if export_format == 'pdf':
        return export_customer_pdf(customer, customer_cylinders, safe_filename, timestamp)
    else:  # Default to CSV
        return export_customer_csv(customer, customer_cylinders, safe_filename, timestamp)

def export_customer_csv(customer, customer_cylinders, safe_filename, timestamp):
    """Export customer report as CSV"""
    output = io.StringIO()
    writer = csv.writer(output)
    
    customer_name = customer.get('customer_name') or customer.get('name', 'Unknown Customer')
    
    # Customer details header
    writer.writerow([f'=== CUSTOMER REPORT: {customer_name} ==='])
    writer.writerow(['Generated:', datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
    writer.writerow([])
    
    # Customer information
    writer.writerow(['=== CUSTOMER DETAILS ==='])
    writer.writerow(['Customer No:', customer.get('customer_no', '')])
    writer.writerow(['Name:', customer_name])
    writer.writerow(['Phone:', customer.get('customer_phone') or customer.get('phone', '')])
    writer.writerow(['Email:', customer.get('customer_email') or customer.get('email', '')])
    writer.writerow(['Address:', customer.get('customer_address') or customer.get('address', '')])
    writer.writerow(['City:', customer.get('customer_city', '')])
    writer.writerow(['State:', customer.get('customer_state', '')])
    writer.writerow(['Total Dispatched Cylinders:', len(customer_cylinders)])
    writer.writerow([])
    
    # Dispatched cylinders sorted by rental days
    writer.writerow(['=== DISPATCHED CYLINDERS (Sorted by Days Dispatched - Longest First) ==='])
    writer.writerow(['ID', 'Serial Number', 'Type', 'Size', 'Status', 
                    'Date Dispatched', 'Days Dispatched', 'Location', 'Pressure'])
    
    cylinder_model = Cylinder()
    for cylinder in customer_cylinders:
        display_id = cylinder_model.get_display_id(cylinder)
        # Format dispatch date properly
        dispatch_date = cylinder.get('date_borrowed', '') or cylinder.get('rental_date', '')
        if dispatch_date and len(dispatch_date) >= 10:
            dispatch_date = dispatch_date[:10]  # Extract YYYY-MM-DD part
        
        writer.writerow([
            display_id,
            cylinder.get('serial_number', ''),
            cylinder.get('type', ''),
            cylinder.get('size', ''),
            cylinder.get('status', ''),
            dispatch_date,
            cylinder.get('rental_days', 0),
            cylinder.get('location', ''),
            cylinder.get('pressure', '')
        ])
    
    # Summary statistics
    writer.writerow([])
    writer.writerow(['=== SUMMARY STATISTICS ==='])
    if customer_cylinders:
        total_days = sum(c.get('rental_days', 0) for c in customer_cylinders)
        avg_days = total_days // len(customer_cylinders) if customer_cylinders else 0
        longest_rental = max(c.get('rental_days', 0) for c in customer_cylinders)
        long_term_count = len([c for c in customer_cylinders if c.get('rental_days', 0) > 90])
        
        writer.writerow(['Total Cylinders:', len(customer_cylinders)])
        writer.writerow(['Average Days Dispatched:', avg_days])
        writer.writerow(['Longest Dispatch (Days):', longest_rental])
        writer.writerow(['Long-term Dispatches (90+ days):', long_term_count])
    else:
        writer.writerow(['No cylinders currently dispatched to this customer'])
    
    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': f'attachment; filename=customer_report_{safe_filename}_{timestamp}.csv'}
    )



def export_customer_pdf(customer, customer_cylinders, safe_filename, timestamp):
    """Export customer report as PDF"""
    try:
        from reportlab.lib.pagesizes import letter, A4
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib import colors
        from reportlab.lib.units import inch
        import io
        
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=18)
        
        # Build story
        story = []
        styles = getSampleStyleSheet()
        
        # Title
        customer_name = customer.get('customer_name') or customer.get('name', 'Unknown Customer')
        title_style = ParagraphStyle('CustomTitle', parent=styles['Heading1'], fontSize=18, spaceAfter=30)
        story.append(Paragraph(f"Customer Report: {customer_name}", title_style))
        story.append(Paragraph(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles['Normal']))
        story.append(Spacer(1, 20))
        
        # Customer Details
        story.append(Paragraph("Customer Details", styles['Heading2']))
        customer_data = [
            ['Customer No:', customer.get('customer_no', '')],
            ['Name:', customer_name],
            ['Phone:', customer.get('customer_phone') or customer.get('phone', '')],
            ['Email:', customer.get('customer_email') or customer.get('email', '')],
            ['Address:', customer.get('customer_address') or customer.get('address', '')],
            ['City:', customer.get('customer_city', '')],
            ['State:', customer.get('customer_state', '')],
            ['Total Dispatched Cylinders:', str(len(customer_cylinders))]
        ]
        
        customer_table = Table(customer_data, colWidths=[2*inch, 4*inch])
        customer_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('BACKGROUND', (1, 0), (1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        story.append(customer_table)
        story.append(Spacer(1, 20))
        
        # Dispatched Cylinders
        if customer_cylinders:
            story.append(Paragraph("Dispatched Cylinders (Sorted by Days Dispatched)", styles['Heading2']))
            
            cylinder_data = [['ID', 'Type', 'Size', 'Days Dispatched', 'Date Dispatched']]
            cylinder_model = Cylinder()
            for cylinder in customer_cylinders:
                display_id = cylinder_model.get_display_id(cylinder)
                cylinder_data.append([
                    str(display_id),
                    str(cylinder.get('type', '')),
                    str(cylinder.get('size', '')),
                    str(cylinder.get('rental_days', 0)),
                    str(cylinder.get('date_borrowed', ''))
                ])
            
            cylinder_table = Table(cylinder_data, colWidths=[1*inch, 1.5*inch, 1.2*inch, 1.5*inch, 1.8*inch])
            cylinder_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            story.append(cylinder_table)
            story.append(Spacer(1, 20))
            
            # Summary Statistics
            story.append(Paragraph("Summary Statistics", styles['Heading2']))
            total_days = sum(c.get('rental_days', 0) for c in customer_cylinders)
            avg_days = total_days // len(customer_cylinders) if customer_cylinders else 0
            longest_rental = max(c.get('rental_days', 0) for c in customer_cylinders)
            long_term_count = len([c for c in customer_cylinders if c.get('rental_days', 0) > 90])
            
            summary_data = [
                ['Total Cylinders:', str(len(customer_cylinders))],
                ['Average Days Dispatched:', str(avg_days)],
                ['Longest Dispatch (Days):', str(longest_rental)],
                ['Long-term Dispatches (90+ days):', str(long_term_count)]
            ]
            
            summary_table = Table(summary_data, colWidths=[3*inch, 2*inch])
            summary_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
                ('BACKGROUND', (1, 0), (1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            story.append(summary_table)
        else:
            story.append(Paragraph("No cylinders currently dispatched to this customer", styles['Normal']))
        
        # Build PDF
        doc.build(story)
        buffer.seek(0)
        
        return Response(
            buffer.getvalue(),
            mimetype='application/pdf',
            headers={'Content-Disposition': f'attachment; filename=customer_report_{safe_filename}_{timestamp}.pdf'}
        )
    
    except ImportError:
        flash('PDF generation not available. Please use CSV format.', 'error')
        return redirect(url_for('reports'))

# Data Management Routes
@app.route('/admin/reset-data')
@login_required
def reset_data_page():
    """Show data reset confirmation page"""
    user_manager = UserManager()
    user = user_manager.get_user_by_id(session['user_id'])
    
    # Only admins can reset data
    if not user or user.get('role') != 'admin':
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('index'))
    
    # Get current data counts
    customer_model = Customer()
    cylinder_model = Cylinder()
    customers = customer_model.get_all()
    cylinders = cylinder_model.get_all()
    
    stats = {
        'total_customers': len(customers),
        'total_cylinders': len(cylinders),
        'active_rentals': len([c for c in cylinders if c.get('status', '').lower() == 'rented'])
    }
    
    return render_template('admin/reset_data.html', stats=stats)

@app.route('/admin/reset-data/confirm', methods=['POST'])
@login_required
def reset_data_confirm():
    """Reset all customer and cylinder data with backup"""
    user_manager = UserManager()
    user = user_manager.get_user_by_id(session['user_id'])
    
    # Only admins can reset data
    if not user or user.get('role') != 'admin':
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('index'))
    
    confirmation = request.form.get('confirmation')
    if confirmation != 'RESET ALL DATA':
        flash('Confirmation text does not match. Data not reset.', 'error')
        return redirect(url_for('reset_data_page'))
    
    try:
        # Create backup before reset
        backup_created = create_manual_backup('before_reset')
        
        if backup_created:
            # Reset customer data
            customer_model = Customer()
            customer_model.db.save_data([])
            
            # Reset cylinder data
            cylinder_model = Cylinder()
            cylinder_model.db.save_data([])
            
            flash('All customer and cylinder data has been reset successfully. Backup created before reset.', 'success')
        else:
            flash('Failed to create backup. Data reset cancelled for safety.', 'error')
            
    except Exception as e:
        flash(f'Error during data reset: {str(e)}', 'error')
    
    return redirect(url_for('index'))

@app.route('/admin/backup-data')
@login_required
def manual_backup():
    """Create manual backup of all data"""
    user_manager = UserManager()
    user = user_manager.get_user_by_id(session['user_id'])
    
    # Only admins can create backups
    if not user or user.get('role') != 'admin':
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('index'))
    
    try:
        backup_created = create_manual_backup('manual')
        if backup_created:
            flash('Manual backup created successfully.', 'success')
        else:
            flash('Failed to create backup.', 'error')
    except Exception as e:
        flash(f'Error creating backup: {str(e)}', 'error')
    
    return redirect(url_for('index'))

def create_manual_backup(backup_type='manual'):
    """Create backup of all data files"""
    try:
        # Create backups directory if it doesn't exist
        backup_dir = 'backups'
        if not os.path.exists(backup_dir):
            os.makedirs(backup_dir)
        
        # Create timestamped backup directory
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_subdir = os.path.join(backup_dir, f'{backup_type}_backup_{timestamp}')
        os.makedirs(backup_subdir)
        
        # Backup data files
        data_files = ['customers.json', 'cylinders.json', 'users.json']
        for file in data_files:
            src_path = os.path.join('data', file)
            if os.path.exists(src_path):
                dst_path = os.path.join(backup_subdir, file)
                shutil.copy2(src_path, dst_path)
        
        # Create backup info file
        info_file = os.path.join(backup_subdir, 'backup_info.json')
        backup_info = {
            'backup_type': backup_type,
            'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'files_backed_up': data_files,
            'system': 'Varasai Oxygen'
        }
        with open(info_file, 'w') as f:
            json.dump(backup_info, f, indent=2)
        
        return True
    except Exception as e:
        print(f"Backup creation failed: {str(e)}")
        return False

# Auto-backup system
class AutoBackupManager:
    """Manages automatic backup system"""
    
    def __init__(self):
        self.backup_interval = 14 * 24 * 60 * 60  # 2 weeks in seconds
        self.last_backup_file = 'data/last_backup.json'
        self.running = False
        self.thread = None
    
    def start_auto_backup(self):
        """Start the automatic backup system"""
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self._backup_loop, daemon=True)
            self.thread.start()
    
    def stop_auto_backup(self):
        """Stop the automatic backup system"""
        self.running = False
    
    def _backup_loop(self):
        """Main backup loop running in background"""
        while self.running:
            try:
                if self._should_create_backup():
                    self._create_auto_backup()
                # Check every hour
                time.sleep(3600)
            except Exception as e:
                print(f"Auto-backup error: {str(e)}")
                time.sleep(3600)  # Wait an hour before trying again
    
    def _should_create_backup(self):
        """Check if backup should be created"""
        try:
            if not os.path.exists(self.last_backup_file):
                return True
            
            with open(self.last_backup_file, 'r') as f:
                last_backup_info = json.load(f)
            
            last_backup_time = datetime.strptime(
                last_backup_info['last_backup'], 
                '%Y-%m-%d %H:%M:%S'
            )
            
            time_since_backup = datetime.now() - last_backup_time
            return time_since_backup.total_seconds() >= self.backup_interval
            
        except Exception:
            return True  # If can't read file, assume backup needed
    
    def _create_auto_backup(self):
        """Create automatic backup"""
        try:
            backup_created = create_manual_backup('auto')
            if backup_created:
                # Update last backup time
                backup_info = {
                    'last_backup': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'backup_type': 'automatic',
                    'next_backup': (datetime.now() + timedelta(days=14)).strftime('%Y-%m-%d %H:%M:%S')
                }
                
                # Ensure data directory exists
                if not os.path.exists('data'):
                    os.makedirs('data')
                
                with open(self.last_backup_file, 'w') as f:
                    json.dump(backup_info, f, indent=2)
                
                print(f"Auto-backup created successfully at {datetime.now()}")
        except Exception as e:
            print(f"Auto-backup failed: {str(e)}")

# Initialize auto-backup system
auto_backup_manager = AutoBackupManager()

# Start auto-backup when app starts (using app context)
def initialize_auto_backup():
    """Initialize automatic backup system"""
    auto_backup_manager.start_auto_backup()

# Initialize auto-backup at import time
with app.app_context():
    initialize_auto_backup()

# PDF Export Routes
@app.route('/export/customers.pdf')
@login_required
def export_customers_pdf():
    """Export all customers to PDF"""
    customer_model = Customer()
    customers = customer_model.get_all()
    
    # Create PDF buffer
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, 
                           rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=18)
    
    # Container for the PDF elements
    story = []
    styles = getSampleStyleSheet()
    
    # Title
    title = Paragraph("Varasai Oxygen - Customer Report", styles['Title'])
    story.append(title)
    story.append(Spacer(1, 12))
    
    # Date and summary
    date_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    date_para = Paragraph(f"Generated on: {date_str}", styles['Normal'])
    story.append(date_para)
    
    summary_para = Paragraph(f"Total Customers: {len(customers)}", styles['Normal'])
    story.append(summary_para)
    story.append(Spacer(1, 12))
    
    # Customer table
    if customers:
        data = [['Customer No', 'Name', 'Email', 'Phone', 'Address', 'City', 'State']]
        for customer in customers:
            data.append([
                customer.get('customer_no', '')[:15],
                (customer.get('customer_name', '') or customer.get('name', ''))[:25],  # Truncate long names
                (customer.get('customer_email', '') or customer.get('email', ''))[:30],
                (customer.get('customer_phone', '') or customer.get('phone', ''))[:15],
                (customer.get('customer_address', '') or customer.get('address', ''))[:25],
                customer.get('customer_city', '')[:15],
                customer.get('customer_state', '')[:10]
            ])
        
        table = Table(data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        story.append(table)
    
    # Build PDF
    doc.build(story)
    buffer.seek(0)
    
    return Response(
        buffer.getvalue(),
        mimetype='application/pdf',
        headers={'Content-Disposition': f'attachment; filename=customers_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf'}
    )

@app.route('/export/cylinders.pdf')
@login_required
def export_cylinders_pdf():
    """Export all cylinders to PDF"""
    cylinder_model = Cylinder()
    cylinders = cylinder_model.get_all()
    
    # Create PDF buffer
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter,
                           rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=18)
    
    # Container for the PDF elements
    story = []
    styles = getSampleStyleSheet()
    
    # Title
    title = Paragraph("Varasai Oxygen - Cylinder Inventory Report", styles['Title'])
    story.append(title)
    story.append(Spacer(1, 12))
    
    # Date and summary
    date_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    date_para = Paragraph(f"Generated on: {date_str}", styles['Normal'])
    story.append(date_para)
    
    summary_para = Paragraph(f"Total Cylinders: {len(cylinders)}", styles['Normal'])
    story.append(summary_para)
    
    # Status breakdown
    status_counts = {}
    for cylinder in cylinders:
        status = cylinder.get('status', 'Unknown')
        status_counts[status] = status_counts.get(status, 0) + 1
    
    status_text = " | ".join([f"{status}: {count}" for status, count in status_counts.items()])
    status_para = Paragraph(f"Status Breakdown: {status_text}", styles['Normal'])
    story.append(status_para)
    story.append(Spacer(1, 12))
    
    # Cylinder table
    if cylinders:
        data = [['ID', 'Type', 'Size', 'Status', 'Location', 'Customer']]
        for cylinder in cylinders:
            # Use custom ID if available, otherwise fallback to generated serial
            display_id = cylinder_model.get_display_id(cylinder)
            
            data.append([
                display_id[:15],
                cylinder.get('type', '')[:15],
                cylinder.get('size', '')[:12],
                cylinder.get('status', '')[:10],
                cylinder.get('location', '')[:15],
                cylinder.get('customer_name', '')[:15]
            ])
        
        table = Table(data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        story.append(table)
    
    # Build PDF
    doc.build(story)
    buffer.seek(0)
    
    return Response(
        buffer.getvalue(),
        mimetype='application/pdf',
        headers={'Content-Disposition': f'attachment; filename=cylinders_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf'}
    )

@app.route('/export/rental-activities.pdf')
@login_required
def export_rental_activities_pdf():
    """Export rental activities to PDF"""
    cylinder_model = Cylinder()
    customer_model = Customer()
    cylinders = cylinder_model.get_all()
    customers = customer_model.get_all()
    
    # Create customer lookup
    customer_lookup = {c['id']: c for c in customers}
    
    # Filter cylinders with rental history
    rental_cylinders = [c for c in cylinders if c.get('rented_to') or c.get('date_borrowed')]
    
    # Create PDF buffer
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter,
                           rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=18)
    
    # Container for the PDF elements
    story = []
    styles = getSampleStyleSheet()
    
    # Title
    title = Paragraph("Varasai Oxygen - Rental Activities Report", styles['Title'])
    story.append(title)
    story.append(Spacer(1, 12))
    
    # Date and summary
    date_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    date_para = Paragraph(f"Generated on: {date_str}", styles['Normal'])
    story.append(date_para)
    
    summary_para = Paragraph(f"Total Rental Activities: {len(rental_cylinders)}", styles['Normal'])
    story.append(summary_para)
    story.append(Spacer(1, 12))
    
    # Rental activities table
    if rental_cylinders:
        data = [['Cylinder', 'Type', 'Customer', 'Date Borrowed', 'Status', 'Days']]
        for i, cylinder in enumerate(rental_cylinders):
            customer = customer_lookup.get(cylinder.get('rented_to', ''), {})
            rental_days = cylinder_model.get_rental_days(cylinder)
            
            # Generate display serial number
            cylinder_type = cylinder.get('type', 'Other')
            display_serial = cylinder_model.get_serial_number(cylinder_type, i + 1)
            
            date_borrowed = cylinder.get('date_borrowed', '')
            if date_borrowed:
                try:
                    date_obj = datetime.fromisoformat(date_borrowed.replace('Z', '+00:00'))
                    date_borrowed = date_obj.strftime('%Y-%m-%d')
                except:
                    pass
            
            data.append([
                display_serial,
                cylinder.get('type', '')[:12],
                (customer.get('customer_name', '') or customer.get('name', ''))[:15],
                date_borrowed[:10],
                cylinder.get('status', '')[:10],
                str(rental_days)
            ])
        
        table = Table(data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        story.append(table)
    
    # Build PDF
    doc.build(story)
    buffer.seek(0)
    
    return Response(
        buffer.getvalue(),
        mimetype='application/pdf',
        headers={'Content-Disposition': f'attachment; filename=rental_activities_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf'}
    )


@app.route('/export/rental_history')
@login_required
def export_rental_history():
    """Export complete rental history to Excel"""
    import io
    from openpyxl import Workbook
    from db_service import RentalHistoryService
    
    try:
        with RentalHistoryService() as service:
            all_history, _ = service.get_all()  # Get all history
        
        workbook = Workbook()
        
        # Create separate sheets for active and past rentals
        active_sheet = workbook.active
        active_sheet.title = "Active Rentals"
        past_sheet = workbook.create_sheet("Past Rentals")
        
        # Headers
        headers = [
            'Customer No', 'Customer Name', 'Customer Phone', 'Customer Address',
            'Cylinder ID', 'Cylinder Type', 'Cylinder Size', 
            'Dispatch Date', 'Return Date', 'Rental Days'
        ]
        
        # Active rentals sheet
        for col, header in enumerate(headers, 1):
            active_sheet.cell(row=1, column=col, value=header)
        
        row = 2
        for record in all_history['active']:
            active_sheet.cell(row=row, column=1, value=record.get('customer_no', ''))
            active_sheet.cell(row=row, column=2, value=record.get('customer_name', ''))
            active_sheet.cell(row=row, column=3, value=record.get('customer_phone', ''))
            active_sheet.cell(row=row, column=4, value=record.get('customer_address', ''))
            active_sheet.cell(row=row, column=5, value=record.get('cylinder_custom_id', '') or record.get('cylinder_serial', ''))
            active_sheet.cell(row=row, column=6, value=record.get('cylinder_type', ''))
            active_sheet.cell(row=row, column=7, value=record.get('cylinder_size', ''))
            active_sheet.cell(row=row, column=8, value=record.get('date_borrowed', '')[:10] if record.get('date_borrowed') else '')
            active_sheet.cell(row=row, column=9, value='')  # No return date for active
            active_sheet.cell(row=row, column=10, value=record.get('rental_days', 0))
            row += 1
        
        # Past rentals sheet
        for col, header in enumerate(headers, 1):
            past_sheet.cell(row=1, column=col, value=header)
        
        row = 2
        for record in all_history['past']:
            past_sheet.cell(row=row, column=1, value=record.get('customer_no', ''))
            past_sheet.cell(row=row, column=2, value=record.get('customer_name', ''))
            past_sheet.cell(row=row, column=3, value=record.get('customer_phone', ''))
            past_sheet.cell(row=row, column=4, value=record.get('customer_address', ''))
            past_sheet.cell(row=row, column=5, value=record.get('cylinder_custom_id', '') or record.get('cylinder_serial', ''))
            past_sheet.cell(row=row, column=6, value=record.get('cylinder_type', ''))
            past_sheet.cell(row=row, column=7, value=record.get('cylinder_size', ''))
            past_sheet.cell(row=row, column=8, value=record.get('date_borrowed', '')[:10] if record.get('date_borrowed') else '')
            past_sheet.cell(row=row, column=9, value=record.get('date_returned', '')[:10] if record.get('date_returned') else '')
            past_sheet.cell(row=row, column=10, value=record.get('rental_days', 0))
            row += 1
        
        # Save to memory
        output = io.BytesIO()
        workbook.save(output)
        output.seek(0)
        
        filename = f"rental_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        
        return send_file(
            output,
            as_attachment=True,
            download_name=filename,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        
    except Exception as e:
        flash(f'Error exporting rental history: {str(e)}', 'error')
        return redirect(url_for('reports'))
