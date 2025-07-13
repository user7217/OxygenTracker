from flask import render_template, request, redirect, url_for, flash, jsonify, session
from app import app
from models import Customer, Cylinder
from auth_models import UserManager
from functools import wraps
import os
import tempfile

# Try to import Access functionality
try:
    from data_importer import DataImporter
    ACCESS_AVAILABLE = True
except ImportError as e:
    ACCESS_AVAILABLE = False
    import logging
    logging.warning(f"MS Access functionality not available: {e}")

# Try to import Email functionality
try:
    from email_service import EmailService
    email_service = EmailService()
    EMAIL_AVAILABLE = True
except ImportError as e:
    EMAIL_AVAILABLE = False
    email_service = None
    import logging
    logging.warning(f"Email functionality not available: {e}")

# Initialize user manager
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

# Initialize models
customer_model = Customer()
cylinder_model = Cylinder()

# Authentication routes
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
            session['role'] = user.get('role', 'user')
            
            flash(f'Welcome back, {user["username"]}!', 'success')
            
            # Redirect to next page if specified
            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password', 'error')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    """User logout"""
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
        role = request.form.get('role', 'user')
        
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
        
        try:
            new_user = user_manager.create_user(username, email, password, role)
            flash(f'User {username} created successfully', 'success')
            return redirect(url_for('users'))
        except ValueError as e:
            flash(str(e), 'error')
    
    return render_template('register.html')

@app.route('/users')
@admin_required
def users():
    """List all users (admin only)"""
    all_users = user_manager.get_all_users()
    return render_template('users.html', users=all_users)

@app.route('/')
@login_required
def index():
    """Dashboard showing overview with fun statistics"""
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
    """List all customers with search functionality"""

    search_query = request.args.get('search', '')
    
    if search_query:
        customers_list = customer_model.search(search_query)
    else:
        customers_list = customer_model.get_all()
    
    return render_template('customers.html', customers=customers_list, search_query=search_query)

@app.route('/customers/add', methods=['GET', 'POST'])
@login_required
def add_customer():
    """Add new customer"""
    if request.method == 'POST':
        # Validate required fields
        required_fields = ['name', 'email', 'phone', 'address']
        customer_data = {}
        
        for field in required_fields:
            value = request.form.get(field, '').strip()
            if not value:
                flash(f'{field.title()} is required', 'error')
                return render_template('add_customer.html')
            customer_data[field] = value
        
        # Add optional fields
        customer_data['company'] = request.form.get('company', '').strip()
        customer_data['notes'] = request.form.get('notes', '').strip()
        
        try:
            new_customer = customer_model.add(customer_data)
            flash(f'Customer {new_customer["name"]} added successfully with ID: {new_customer["id"]}', 'success')
            return redirect(url_for('customers'))
        except Exception as e:
            flash(f'Error adding customer: {str(e)}', 'error')
    
    return render_template('add_customer.html')

@app.route('/customers/edit/<customer_id>', methods=['GET', 'POST'])
@login_required
def edit_customer(customer_id):
    """Edit existing customer"""
    customer = customer_model.get_by_id(customer_id)
    if not customer:
        flash('Customer not found', 'error')
        return redirect(url_for('customers'))
    
    if request.method == 'POST':
        # Validate required fields
        required_fields = ['name', 'email', 'phone', 'address']
        customer_data = {}
        
        for field in required_fields:
            value = request.form.get(field, '').strip()
            if not value:
                flash(f'{field.title()} is required', 'error')
                return render_template('edit_customer.html', customer=customer)
            customer_data[field] = value
        
        # Add optional fields
        customer_data['company'] = request.form.get('company', '').strip()
        customer_data['notes'] = request.form.get('notes', '').strip()
        
        try:
            updated_customer = customer_model.update(customer_id, customer_data)
            if updated_customer:
                flash(f'Customer {updated_customer["name"]} updated successfully', 'success')
                return redirect(url_for('customers'))
            else:
                flash('Error updating customer', 'error')
        except Exception as e:
            flash(f'Error updating customer: {str(e)}', 'error')
    
    return render_template('edit_customer.html', customer=customer)

@app.route('/customers/delete/<customer_id>', methods=['POST'])
@login_required
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

# Cylinder routes
@app.route('/cylinders')
@login_required
def cylinders():
    """List all cylinders with search and filter functionality"""

    search_query = request.args.get('search', '')
    status_filter = request.args.get('status', '')
    customer_filter = request.args.get('customer', '')
    rental_duration_filter = request.args.get('rental_duration', '')
    
    cylinders_list = cylinder_model.get_all()
    
    # Apply search filter
    if search_query:
        cylinders_list = cylinder_model.search(search_query)
    
    # Apply status filter
    if status_filter:
        cylinders_list = [c for c in cylinders_list if c.get('status', '').lower() == status_filter.lower()]
    
    # Apply customer filter
    if customer_filter:
        cylinders_list = [c for c in cylinders_list if c.get('rented_to') == customer_filter]
    
    # Apply rental duration filter
    if rental_duration_filter:
        try:
            duration_months = int(rental_duration_filter)
            duration_days = duration_months * 30
            filtered_cylinders = []
            
            for cylinder in cylinders_list:
                if cylinder.get('status', '').lower() == 'rented':
                    rental_days = cylinder_model.get_rental_days(cylinder)
                    if rental_days >= duration_days:
                        filtered_cylinders.append(cylinder)
            
            cylinders_list = filtered_cylinders
        except ValueError:
            pass  # Ignore invalid duration values
    
    # Add rental days calculation for each cylinder
    for cylinder in cylinders_list:
        cylinder['rental_days'] = cylinder_model.get_rental_days(cylinder)
        # Customer name should already be stored in the cylinder data
        if not cylinder.get('customer_name') and cylinder.get('rented_to'):
            # Fallback: get customer name if not stored
            customer = customer_model.get_by_id(cylinder['rented_to'])
            cylinder['customer_name'] = customer.get('name', 'Unknown Customer') if customer else 'Unknown Customer'
    
    # Get all customers for the filter dropdown
    customers = customer_model.get_all()
    

    return render_template('cylinders.html', 
                         cylinders=cylinders_list, 
                         customers=customers,
                         search_query=search_query,
                         status_filter=status_filter,
                         customer_filter=customer_filter,
                         rental_duration_filter=rental_duration_filter)

@app.route('/cylinders/add', methods=['GET', 'POST'])
@login_required
def add_cylinder():
    """Add new cylinder"""
    if request.method == 'POST':
        # Validate required fields
        required_fields = ['serial_number', 'type', 'size', 'status', 'location']
        cylinder_data = {}
        
        for field in required_fields:
            value = request.form.get(field, '').strip()
            if not value:
                flash(f'{field.replace("_", " ").title()} is required', 'error')
                customers = customer_model.get_all()
                return render_template('add_cylinder.html', customers=customers)
            cylinder_data[field] = value
        
        # Add optional fields
        cylinder_data['custom_id'] = request.form.get('custom_id', '').strip()
        cylinder_data['pressure'] = request.form.get('pressure', '').strip()
        cylinder_data['last_inspection'] = request.form.get('last_inspection', '').strip()
        cylinder_data['next_inspection'] = request.form.get('next_inspection', '').strip()
        cylinder_data['notes'] = request.form.get('notes', '').strip()
        
        # Validate custom_id uniqueness if provided
        if cylinder_data['custom_id']:
            existing_cylinders = cylinder_model.get_all()
            for existing in existing_cylinders:
                if existing.get('custom_id') == cylinder_data['custom_id']:
                    flash(f'Custom ID "{cylinder_data["custom_id"]}" is already in use. Please choose a different one.', 'error')
                    customers = customer_model.get_all()
                    return render_template('add_cylinder.html', customers=customers)
        
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
            flash(f'Cylinder {new_cylinder["serial_number"]} added successfully with ID: {new_cylinder["id"]}', 'success')
            return redirect(url_for('cylinders'))
        except Exception as e:
            flash(f'Error adding cylinder: {str(e)}', 'error')
    
    # Get all customers for the dropdown and today's date
    customers = customer_model.get_all()
    from datetime import datetime
    today_date = datetime.now().strftime('%Y-%m-%d')
    return render_template('add_cylinder.html', customers=customers, today_date=today_date)

@app.route('/cylinders/edit/<cylinder_id>', methods=['GET', 'POST'])
@login_required
def edit_cylinder(cylinder_id):
    """Edit existing cylinder"""
    cylinder = cylinder_model.get_by_id(cylinder_id)
    if not cylinder:
        flash('Cylinder not found', 'error')
        return redirect(url_for('cylinders'))
    
    if request.method == 'POST':
        # Validate required fields
        required_fields = ['serial_number', 'type', 'size', 'status', 'location']
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
                flash(f'Cylinder {updated_cylinder["serial_number"]} updated successfully', 'success')
                return redirect(url_for('cylinders'))
            else:
                flash('Error updating cylinder', 'error')
        except Exception as e:
            flash(f'Error updating cylinder: {str(e)}', 'error')
    
    # Get all customers for the dropdown
    customers = customer_model.get_all()
    return render_template('edit_cylinder.html', cylinder=cylinder, customers=customers)

@app.route('/cylinders/delete/<cylinder_id>', methods=['POST'])
@login_required
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
        # Save uploaded file temporarily
        temp_dir = tempfile.gettempdir()
        temp_path = os.path.join(temp_dir, f"temp_access_{file.filename}")
        file.save(temp_path)
        
        # Try to connect
        importer = DataImporter()
        if importer.connect_to_access(temp_path):
            # Store file path in session
            session['access_file_path'] = temp_path
            session['access_file_name'] = file.filename
            
            # Get available tables
            tables = importer.get_available_tables()
            importer.close_connection()
            
            if tables:
                flash(f'Successfully connected to {file.filename}. Found {len(tables)} tables.', 'success')
                return render_template('select_tables.html', tables=tables, filename=file.filename)
            else:
                flash('No tables found in the database', 'error')
                os.remove(temp_path)
                return redirect(url_for('import_data'))
        else:
            flash('Failed to connect to Access database. Please check the file format and try again.', 'error')
            os.remove(temp_path)
            return redirect(url_for('import_data'))
            
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
        
        # Get suggested field mapping
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
        
        # Execute import
        importer = DataImporter()
        if not importer.connect_to_access(session['access_file_path']):
            flash('Failed to reconnect to Access database', 'error')
            return redirect(url_for('import_data'))
        
        if import_type == 'customer':
            imported, skipped, errors = importer.import_customers(table_name, field_mapping, skip_duplicates)
            item_type = 'customers'
        elif import_type == 'cylinder':
            imported, skipped, errors = importer.import_cylinders(table_name, field_mapping, skip_duplicates)
            item_type = 'cylinders'
        else:
            flash('Invalid import type', 'error')
            return redirect(url_for('import_data'))
        
        importer.close_connection()
        
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
        
        # Clean up
        if os.path.exists(session['access_file_path']):
            os.remove(session['access_file_path'])
        session.pop('access_file_path', None)
        session.pop('access_file_name', None)
        
        # Redirect to appropriate page
        if import_type == 'customer':
            return redirect(url_for('customers'))
        else:
            return redirect(url_for('cylinders'))
        
    except Exception as e:
        flash(f'Error during import: {str(e)}', 'error')
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
@login_required
def rent_cylinder(cylinder_id):
    """Rent a cylinder to a customer"""
    customer_id = request.form.get('customer_id')
    rental_notes = request.form.get('rental_notes', '').strip()
    
    if not customer_id:
        flash('Please select a customer', 'error')
        return redirect(url_for('cylinders'))
    
    # Verify customer exists
    customer = customer_model.get_by_id(customer_id)
    if not customer:
        flash('Customer not found', 'error')
        return redirect(url_for('cylinders'))
    
    # Rent the cylinder (rental_notes parameter is no longer used in the updated function)
    if cylinder_model.rent_cylinder(cylinder_id, customer_id):
        flash(f'Cylinder rented to {customer["name"]} successfully', 'success')
    else:
        flash('Error renting cylinder', 'error')
    
    return redirect(url_for('cylinders'))

@app.route('/cylinders/return/<cylinder_id>', methods=['POST'])
@login_required
def return_cylinder(cylinder_id):
    """Return a cylinder from rental"""
    return_date = request.form.get('return_date')
    if cylinder_model.return_cylinder(cylinder_id, return_date):
        flash('Cylinder returned successfully', 'success')
    else:
        flash('Error returning cylinder', 'error')
    
    return redirect(url_for('cylinders'))

@app.route('/customers/<customer_id>/bulk_cylinders', methods=['GET', 'POST'])
@login_required
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
    
    if not cylinder_ids_text:
        flash('Please enter at least one cylinder ID', 'error')
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
            
            # Rent the cylinder
            success = cylinder_model.rent_cylinder(actual_cylinder_id, customer_id)
            if success:
                processed += 1
            else:
                errors.append(f'"{cylinder_display}": Failed to rent')
                skipped += 1
        
        elif action == 'return':
            # Check if cylinder is rented to this customer
            if cylinder.get('status', '').lower() != 'rented' or cylinder.get('rented_to') != customer_id:
                errors.append(f'"{cylinder_display}": Not rented to this customer')
                skipped += 1
                continue
            
            # Return the cylinder
            success = cylinder_model.return_cylinder(actual_cylinder_id)
            if success:
                processed += 1
            else:
                errors.append(f'"{cylinder_display}": Failed to return')
                skipped += 1
    
    # Create summary message
    if action == 'rent':
        flash(f'Successfully rented {processed} cylinders to {customer["name"]}', 'success')
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
    return render_template('bulk_rental_management.html', customers=customers)

@app.route('/bulk_rental_management/process', methods=['POST'])
@login_required
def process_bulk_rental():
    """Process bulk cylinder rental/return operations"""
    customer_id = request.form.get('customer_id', '').strip()
    action = request.form.get('action', 'rent')
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
            
            # Rent the cylinder
            success = cylinder_model.rent_cylinder(cylinder_id, customer_id)
            if success:
                processed += 1
                success_cylinders.append(cylinder_id)
            else:
                errors.append(f'Cylinder {cylinder_id}: Failed to rent')
                skipped += 1
        
        elif action == 'return':
            # Check if cylinder is rented to this customer
            if cylinder.get('status', '').lower() != 'rented' or cylinder.get('rented_to') != customer_id:
                errors.append(f'Cylinder {cylinder_id}: Not rented to this customer')
                skipped += 1
                continue
            
            # Return the cylinder
            success = cylinder_model.return_cylinder(cylinder_id)
            if success:
                processed += 1
                success_cylinders.append(cylinder_id)
            else:
                errors.append(f'Cylinder {cylinder_id}: Failed to return')
                skipped += 1
    
    # Create summary message
    if action == 'rent':
        if processed > 0:
            flash(f'Successfully rented {processed} cylinders ({", ".join(success_cylinders[:5])}{", ..." if len(success_cylinders) > 5 else ""}) to {customer["name"]}', 'success')
    else:
        if processed > 0:
            flash(f'Successfully returned {processed} cylinders ({", ".join(success_cylinders[:5])}{", ..." if len(success_cylinders) > 5 else ""}) from {customer["name"]}', 'success')
    
    if skipped > 0:
        flash(f'{skipped} cylinders were skipped due to errors', 'warning')
        
    # Show detailed errors if any
    if errors:
        error_msg = 'Details: ' + '; '.join(errors[:5])  # Show first 5 errors
        if len(errors) > 5:
            error_msg += f' and {len(errors) - 5} more...'
        flash(error_msg, 'info')
    
    return redirect(url_for('bulk_rental_management'))
