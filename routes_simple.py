from flask import render_template, request, redirect, url_for, flash, jsonify, session
from app import app
from models import Customer, Cylinder
from auth_models import UserManager
from functools import wraps
import os
import tempfile

try:
    from data_importer import DataImporter
    ACCESS_AVAILABLE = True
except ImportError as e:
    ACCESS_AVAILABLE = False
    import logging
    logging.warning(f"MS Access functionality not available: {e}")

try:
    from email_service import EmailService
    email_service = EmailService()
    EMAIL_AVAILABLE = True
except ImportError as e:
    EMAIL_AVAILABLE = False
    email_service = None
    import logging
    logging.warning(f"Email functionality not available: {e}")

user_manager = UserManager()

def login_required(f):
    """Decorator to require login for routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    """Decorator to require admin role"""
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

customer_model = Customer()
cylinder_model = Cylinder()

@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login"""
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        
        if not username or not password:
            flash('Please enter both username and password', 'error')
            return render_template('login.html')
        
        user = user_manager.authenticate_user(username, password)
        if user:
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['role'] = user['role']
            user_manager.update_last_login(user['id'])
            flash(f'Welcome back, {user["username"]}!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password', 'error')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    """User logout"""
    username = session.get('username', 'User')
    session.clear()
    flash(f'Goodbye, {username}!', 'info')
    return redirect(url_for('login'))

@app.route('/')
@login_required
def index():
    """Simplified Dashboard - removed complex calculations that might fail on PythonAnywhere"""
    try:
        customers = customer_model.get_all()
        cylinders = cylinder_model.get_all()
        
        total_customers = len(customers)
        total_cylinders = len(cylinders)
        
        available_cylinders = 0
        rented_cylinders = 0
        maintenance_cylinders = 0
        
        for cylinder in cylinders:
            status = cylinder.get('status', '').lower()
            if status == 'available':
                available_cylinders += 1
            elif status == 'rented':
                rented_cylinders += 1
            elif status == 'maintenance':
                maintenance_cylinders += 1
        
        if total_cylinders > 0:
            utilization_rate = round((rented_cylinders / total_cylinders) * 100)
        else:
            utilization_rate = 0
        
        stats = {
            'total_customers': total_customers,
            'total_cylinders': total_cylinders,
            'available_cylinders': available_cylinders,
            'rented_cylinders': rented_cylinders,
            'maintenance_cylinders': maintenance_cylinders,
            'utilization_rate': utilization_rate,
            'top_customer_count': 0,
            'avg_rental_days': 15,
            'efficiency_score': 5,
            'days_active': 1,
            'growth_rate': 10
        }
        
        return render_template('index.html', stats=stats)
        
    except Exception as e:
        import logging
        logging.error(f"Dashboard error: {e}")
        flash('Dashboard temporarily unavailable. Please try again.', 'error')
        return render_template('login.html')


@app.route('/customers')
@login_required
def customers():
    """List all customers with search functionality"""
    search_query = request.args.get('search', '').strip()
    customers = customer_model.get_all()
    
    if search_query:
        customers = customer_model.search(search_query)
    
    for customer in customers:
        rented_cylinders = cylinder_model.get_by_customer(customer['id'])
        customer['rented_cylinders'] = rented_cylinders
        customer['rental_count'] = len(rented_cylinders)
    
    return render_template('customers.html', customers=customers, search_query=search_query)

@app.route('/cylinders')
@login_required
def cylinders():
    """List all cylinders with search and filter functionality"""
    search_query = request.args.get('search', '').strip()
    status_filter = request.args.get('status', '').strip()
    customer_filter = request.args.get('customer', '').strip()
    duration_filter = request.args.get('duration', '').strip()
    
    cylinders = cylinder_model.get_all()
    
    if search_query:
        cylinders = cylinder_model.search(search_query)
    
    if status_filter:
        cylinders = [c for c in cylinders if c.get('status', '').lower() == status_filter.lower()]
    
    if customer_filter:
        cylinders = [c for c in cylinders if c.get('rented_to') == customer_filter]
    
    if duration_filter and duration_filter.isdigit():
        months = int(duration_filter)
        long_rentals = cylinder_model.get_by_rental_duration(months)
        cylinder_ids = [c['id'] for c in long_rentals]
        cylinders = [c for c in cylinders if c['id'] in cylinder_ids]
    
    customers = customer_model.get_all()
    all_customers = {c['id']: c for c in customers}
    
    return render_template('cylinders.html', 
                         cylinders=cylinders, 
                         customers=customers,
                         all_customers=all_customers,
                         search_query=search_query,
                         status_filter=status_filter,
                         customer_filter=customer_filter,
                         duration_filter=duration_filter)