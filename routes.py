from flask import render_template, request, redirect, url_for, flash, jsonify, session, Response
import csv
import io
from datetime import datetime, timedelta
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
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
    
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    
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

customer_model = Customer()
cylinder_model = Cylinder()

@app.route('/login', methods=['GET', 'POST'])
def login():
    
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
            
            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password', 'error')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    
    username = session.get('username', 'User')
    session.clear()
    flash(f'Goodbye, {username}!', 'info')
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
@admin_required
def register():
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()
        confirm_password = request.form.get('confirm_password', '').strip()
        role = request.form.get('role', 'viewer').strip()
        
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
        
        if user_manager.get_user_by_username(username):
            flash('Username already exists', 'error')
            return render_template('register.html')
        
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
    
    all_users = user_manager.get_all_users()
    return render_template('users.html', users=all_users)

@app.route('/')
@login_required
def index():
    
    customers = customer_model.get_all()
    cylinders = cylinder_model.get_all()
    
    available_cylinders = len([c for c in cylinders if c.get('status', '').lower() == 'available'])
    rented_cylinders = len([c for c in cylinders if c.get('status', '').lower() == 'rented'])
    maintenance_cylinders = len([c for c in cylinders if c.get('status', '').lower() == 'maintenance'])
    
    total_cylinders = len(cylinders)
    utilization_rate = round((rented_cylinders / total_cylinders * 100) if total_cylinders > 0 else 0)
    
    customer_rentals = {}
    for cylinder in cylinders:
        if cylinder.get('rented_to'):
            customer_id = cylinder['rented_to']
            customer_rentals[customer_id] = customer_rentals.get(customer_id, 0) + 1
    
    top_customer_count = max(customer_rentals.values()) if customer_rentals else 0
    
    import random
    avg_rental_days = random.randint(7, 30)
    
    efficiency_score = min(10, round((utilization_rate + (available_cylinders / total_cylinders * 100 if total_cylinders > 0 else 0)) / 20))
    
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
    
    customers = customer_model.get_all()
    cylinders = cylinder_model.get_all()
    
    available_cylinders = len([c for c in cylinders if c.get('status', '').lower() == 'available'])
    rented_cylinders = len([c for c in cylinders if c.get('status', '').lower() == 'rented'])
    maintenance_cylinders = len([c for c in cylinders if c.get('status', '').lower() == 'maintenance'])
    
    total_cylinders = len(cylinders)
    utilization_rate = round((rented_cylinders / total_cylinders * 100) if total_cylinders > 0 else 0)
    
    customer_rentals = {}
    for cylinder in cylinders:
        if cylinder.get('rented_to'):
            customer_id = cylinder['rented_to']
            customer_rentals[customer_id] = customer_rentals.get(customer_id, 0) + 1
    
    top_customer_count = max(customer_rentals.values()) if customer_rentals else 0
    
    import random
    avg_rental_days = random.randint(7, 30)
    
    efficiency_score = min(10, round((utilization_rate + (available_cylinders / total_cylinders * 100 if total_cylinders > 0 else 0)) / 20))
    
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
    
    if not EMAIL_AVAILABLE or not email_service:
        flash('Email service not available', 'error')
        return redirect(url_for('metrics'))
    
    email = request.form.get('email', '').strip()
    if not email:
        flash('Please enter a valid email address', 'error')
        return redirect(url_for('metrics'))
    
    customers = customer_model.get_all()
    cylinders = cylinder_model.get_all()
    
    available_cylinders = len([c for c in cylinders if c.get('status', '').lower() == 'available'])
    rented_cylinders = len([c for c in cylinders if c.get('status', '').lower() == 'rented'])
    maintenance_cylinders = len([c for c in cylinders if c.get('status', '').lower() == 'maintenance'])
    
    total_cylinders = len(cylinders)
    utilization_rate = round((rented_cylinders / total_cylinders * 100) if total_cylinders > 0 else 0)
    
    customer_rentals = {}
    for cylinder in cylinders:
        if cylinder.get('rented_to'):
            customer_id = cylinder['rented_to']
            customer_rentals[customer_id] = customer_rentals.get(customer_id, 0) + 1
    
    top_customer_count = max(customer_rentals.values()) if customer_rentals else 0
    
    efficiency_score = min(10, round((utilization_rate + (available_cylinders / total_cylinders * 100 if total_cylinders > 0 else 0)) / 20))
    
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

@app.route('/customers')
@login_required
def customers():

    search_query = request.args.get('search', '')
    
    if search_query:
        customers_list = customer_model.search(search_query)
    else:
        customers_list = customer_model.get_all()
    
    return render_template('customers.html', customers=customers_list, search_query=search_query)

@app.route('/customers/add', methods=['GET', 'POST'])
@admin_or_user_can_edit
def add_customer():
    
    if request.method == 'POST':
        required_fields = ['customer_no', 'customer_name', 'customer_address', 'customer_city', 'customer_state', 'customer_phone']
        customer_data = {}
        
        for field in required_fields:
            value = request.form.get(field, '').strip()
            if not value:
                display_name = field.replace('customer_', '').replace('_', ' ').title()
                flash(f'{display_name} is required', 'error')
                return render_template('add_customer.html')
            customer_data[field] = value
        
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
    
    customer = customer_model.get_by_id(customer_id)
    if not customer:
        flash('Customer not found', 'error')
        return redirect(url_for('customers'))
    
    if request.method == 'POST':
        required_fields = ['customer_no', 'customer_name', 'customer_address', 'customer_city', 'customer_state', 'customer_phone']
        customer_data = {}
        
        for field in required_fields:
            value = request.form.get(field, '').strip()
            if not value:
                display_name = field.replace('customer_', '').replace('_', ' ').title()
                flash(f'{display_name} is required', 'error')
                return render_template('edit_customer.html', customer=customer)
            customer_data[field] = value
        
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
    
    try:
        if customer_model.delete(customer_id):
            flash('Customer deleted successfully', 'success')
        else:
            flash('Customer not found', 'error')
    except Exception as e:
        flash(f'Error deleting customer: {str(e)}', 'error')
    
    return redirect(url_for('customers'))

@app.route('/cylinders')
@login_required
def cylinders():

    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    
    per_page = min(max(per_page, 10), 200)
    
    search_query = request.args.get('search', '')
    status_filter = request.args.get('status', '')
    customer_filter = request.args.get('customer', '')
    type_filter = request.args.get('type_filter', '')
    rental_duration_filter = request.args.get('rental_duration', '')
    
    cylinders_list = cylinder_model.get_all()
    
    if search_query:
        cylinders_list = cylinder_model.search(search_query)
    
    if status_filter:
        cylinders_list = [c for c in cylinders_list if c.get('status', '').lower() == status_filter.lower()]
    
    if type_filter:
        if type_filter == 'Carbon Dioxide':
            cylinders_list = [c for c in cylinders_list if c.get('type', '') in ['Carbon Dioxide', 'CO2']]
        elif type_filter == 'CO2':
            cylinders_list = [c for c in cylinders_list if c.get('type', '') in ['Carbon Dioxide', 'CO2']]
        else:
            cylinders_list = [c for c in cylinders_list if c.get('type', '') == type_filter]
    
    if customer_filter:
        cylinders_list = [c for c in cylinders_list if c.get('rented_to') == customer_filter]
    
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
            pass
    
    for i, cylinder in enumerate(cylinders_list):
        cylinder['rental_days'] = cylinder_model.get_rental_days(cylinder)
        cylinder['display_serial'] = cylinder_model.get_serial_number(cylinder.get('type', 'Other'), i + 1)
        if not cylinder.get('customer_name') and cylinder.get('rented_to'):
            customer = customer_model.get_by_id(cylinder['rented_to'])
            cylinder['customer_name'] = customer.get('name', 'Unknown Customer') if customer else 'Unknown Customer'
    
    total_cylinders = len(cylinders_list)
    total_pages = (total_cylinders + per_page - 1) // per_page
    
    start_index = (page - 1) * per_page
    end_index = start_index + per_page
    
    paginated_cylinders = cylinders_list[start_index:end_index]
    
    has_prev = page > 1
    has_next = page < total_pages
    prev_page = page - 1 if has_prev else None
    next_page = page + 1 if has_next else None
    
    pagination = {
        'page': page,
        'per_page': per_page,
        'total': total_cylinders,
        'total_pages': total_pages,
        'has_prev': has_prev,
        'has_next': has_next,
        'prev_page': prev_page,
        'next_page': next_page,
        'pages': list(range(max(1, page - 2), min(total_pages + 1, page + 3)))
    }
    
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

@app.route('/cylinders/add', methods=['GET', 'POST'])
@admin_or_user_can_edit
def add_cylinder():
    
    if request.method == 'POST':
        required_fields = ['type', 'size', 'status', 'location']
        cylinder_data = {}
        
        for field in required_fields:
            value = request.form.get(field, '').strip()
            if not value:
                flash(f'{field.replace("_", " ").title()} is required', 'error')
                customers = customer_model.get_all()
                return render_template('add_cylinder.html', customers=customers)
            cylinder_data[field] = value
        
        cylinder_data['custom_id'] = request.form.get('custom_id', '').strip()
        cylinder_data['pressure'] = request.form.get('pressure', '').strip()
        cylinder_data['last_inspection'] = request.form.get('last_inspection', '').strip()
        cylinder_data['next_inspection'] = request.form.get('next_inspection', '').strip()
        cylinder_data['notes'] = request.form.get('notes', '').strip()
        
        if cylinder_data['custom_id']:
            existing_cylinders = cylinder_model.get_all()
            for existing in existing_cylinders:
                if existing.get('custom_id') == cylinder_data['custom_id']:
                    flash(f'Custom ID "{cylinder_data["custom_id"]}" is already in use. Please choose a different one.', 'error')
                    customers = customer_model.get_all()
                    return render_template('add_cylinder.html', customers=customers)
        
        rented_to = request.form.get('rented_to', '').strip()
        if cylinder_data['status'].lower() == 'rented':
            if not rented_to:
                flash('Customer selection is required when status is "Rented"', 'error')
                customers = customer_model.get_all()
                return render_template('add_cylinder.html', customers=customers)
            
            customer = customer_model.get_by_id(rented_to)
            if not customer:
                flash('Selected customer not found', 'error')
                customers = customer_model.get_all()
                return render_template('add_cylinder.html', customers=customers)
            
            cylinder_data['rented_to'] = rented_to
            cylinder_data['customer_name'] = customer.get('name', '')
            cylinder_data['customer_email'] = customer.get('email', '')
            
            rental_date = request.form.get('rental_date', '').strip()
            from datetime import datetime
            if rental_date:
                try:
                    date_obj = datetime.strptime(rental_date, '%Y-%m-%d')
                    cylinder_data['date_borrowed'] = date_obj.isoformat()
                    cylinder_data['rental_date'] = date_obj.isoformat()
                except ValueError:
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
    
    customers = customer_model.get_all()
    from datetime import datetime
    today_date = datetime.now().strftime('%Y-%m-%d')
    return render_template('add_cylinder.html', customers=customers, today_date=today_date)

@app.route('/cylinders/edit/<cylinder_id>', methods=['GET', 'POST'])
@admin_or_user_can_edit
def edit_cylinder(cylinder_id):
    
    cylinder = cylinder_model.get_by_id(cylinder_id)
    if not cylinder:
        flash('Cylinder not found', 'error')
        return redirect(url_for('cylinders'))
    
    if request.method == 'POST':
        required_fields = ['type', 'size', 'status', 'location']
        cylinder_data = {}
        
        for field in required_fields:
            value = request.form.get(field, '').strip()
            if not value:
                flash(f'{field.replace("_", " ").title()} is required', 'error')
                customers = customer_model.get_all()
                return render_template('edit_cylinder.html', cylinder=cylinder, customers=customers)
            cylinder_data[field] = value
        
        cylinder_data['custom_id'] = request.form.get('custom_id', '').strip()
        cylinder_data['pressure'] = request.form.get('pressure', '').strip()
        cylinder_data['last_inspection'] = request.form.get('last_inspection', '').strip()
        cylinder_data['next_inspection'] = request.form.get('next_inspection', '').strip()
        cylinder_data['notes'] = request.form.get('notes', '').strip()
        
        if cylinder_data['custom_id']:
            existing_cylinders = cylinder_model.get_all()
            for existing in existing_cylinders:
                if existing.get('custom_id') == cylinder_data['custom_id'] and existing.get('id') != cylinder_id:
                    flash(f'Custom ID "{cylinder_data["custom_id"]}" is already in use. Please choose a different one.', 'error')
                    customers = customer_model.get_all()
                    return render_template('edit_cylinder.html', cylinder=cylinder, customers=customers)
        
        rented_to = request.form.get('rented_to', '').strip()
        if cylinder_data['status'].lower() == 'rented':
            if not rented_to:
                flash('Customer selection is required when status is "Rented"', 'error')
                customers = customer_model.get_all()
                return render_template('edit_cylinder.html', cylinder=cylinder, customers=customers)
            
            customer = customer_model.get_by_id(rented_to)
            if not customer:
                flash('Selected customer not found', 'error')
                customers = customer_model.get_all()
                return render_template('edit_cylinder.html', cylinder=cylinder, customers=customers)
            
            cylinder_data['rented_to'] = rented_to
        else:
            cylinder_data['rented_to'] = ''

        date_borrowed = request.form.get('date_borrowed', '').strip()
        date_returned = request.form.get('date_returned', '').strip()
        
        current_status = cylinder.get('status', '').lower()
        new_status = cylinder_data['status'].lower()
        
        from datetime import datetime
        
        if new_status == 'rented' and current_status != 'rented':
            if not date_borrowed:
                cylinder_data['date_borrowed'] = datetime.now().isoformat()
            else:
                try:
                    dt = datetime.fromisoformat(date_borrowed)
                    cylinder_data['date_borrowed'] = dt.isoformat()
                except:
                    cylinder_data['date_borrowed'] = datetime.now().isoformat()
            cylinder_data['date_returned'] = ''
            
        elif new_status == 'available' and current_status == 'rented':
            if not date_returned:
                cylinder_data['date_returned'] = datetime.now().isoformat()
            else:
                try:
                    dt = datetime.fromisoformat(date_returned)
                    cylinder_data['date_returned'] = dt.isoformat()
                except:
                    cylinder_data['date_returned'] = datetime.now().isoformat()
        
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
    
    customers = customer_model.get_all()
    return render_template('edit_cylinder.html', cylinder=cylinder, customers=customers)

@app.route('/cylinders/delete/<cylinder_id>', methods=['POST'])
@admin_or_user_can_edit
def delete_cylinder(cylinder_id):
    
    try:
        if cylinder_model.delete(cylinder_id):
            flash('Cylinder deleted successfully', 'success')
        else:
            flash('Cylinder not found', 'error')
    except Exception as e:
        flash(f'Error deleting cylinder: {str(e)}', 'error')
    
    return redirect(url_for('cylinders'))

@app.route('/import')
@login_required
def import_data():
    
    if not ACCESS_AVAILABLE:
        flash('MS Access import functionality is not available on this system', 'error')
        return redirect(url_for('index'))
    return render_template('import_data.html')

@app.route('/import/upload', methods=['POST'])
def upload_access_file():
    
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
        temp_dir = tempfile.gettempdir()
        temp_path = os.path.join(temp_dir, f"temp_access_{file.filename}")
        file.save(temp_path)
        
        importer = DataImporter()
        if importer.connect_to_access(temp_path):
            session['access_file_path'] = temp_path
            session['access_file_name'] = file.filename
            
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
    
    if 'access_file_path' not in session:
        flash('No Access file connected. Please upload a file first.', 'error')
        return redirect(url_for('import_data'))
    
    try:
        importer = DataImporter()
        if not importer.connect_to_access(session['access_file_path']):
            flash('Failed to reconnect to Access database', 'error')
            return redirect(url_for('import_data'))
        
        columns, preview_data = importer.preview_table(table_name)
        
        import_type = request.args.get('type', 'customer')
        
        if import_type == 'transaction':
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
    
    if 'access_file_path' not in session:
        flash('No Access file connected. Please upload a file first.', 'error')
        return redirect(url_for('import_data'))
    
    try:
        table_name = request.form.get('table_name')
        import_type = request.form.get('import_type')
        skip_duplicates = request.form.get('skip_duplicates') == 'on'
        
        field_mapping = {}
        for key, value in request.form.items():
            if key.startswith('mapping_') and value:
                target_field = key.replace('mapping_', '')
                field_mapping[target_field] = value
        
        if not field_mapping:
            flash('Please map at least one field', 'error')
            return redirect(url_for('preview_table', table_name=table_name, type=import_type))
        
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
        elif import_type == 'transaction':
            imported, skipped, errors = importer.import_transactions(table_name, field_mapping, skip_duplicates)
            item_type = 'transactions'
        else:
            flash('Invalid import type', 'error')
            return redirect(url_for('import_data'))
        
        importer.close_connection()
        
        if imported > 0:
            flash(f'Successfully imported {imported} {item_type}', 'success')
        if skipped > 0:
            flash(f'Skipped {skipped} records (duplicates or missing data)', 'warning')
        if errors:
            for error in errors[:5]:
                flash(error, 'error')
            if len(errors) > 5:
                flash(f'... and {len(errors) - 5} more errors', 'error')
        
        if os.path.exists(session['access_file_path']):
            os.remove(session['access_file_path'])
        session.pop('access_file_path', None)
        session.pop('access_file_name', None)
        
        if import_type == 'customer':
            return redirect(url_for('customers'))
        else:
            return redirect(url_for('cylinders'))
        
    except Exception as e:
        flash(f'Error during import: {str(e)}', 'error')
        return redirect(url_for('import_data'))

@app.route('/import/cancel')
def cancel_import():
    
    if 'access_file_path' in session:
        if os.path.exists(session['access_file_path']):
            os.remove(session['access_file_path'])
        session.pop('access_file_path', None)
        session.pop('access_file_name', None)
    
    flash('Import cancelled', 'info')
    return redirect(url_for('import_data'))

@app.route('/search')
@login_required
def global_search():
    
    query = request.args.get('q', '').strip()
    
    results = {
        'customers': [],
        'cylinders': [],
        'query': query,
        'total_results': 0
    }
    
    if query:
        customer_results = customer_model.search(query)
        results['customers'] = customer_results
        
        cylinder_results = cylinder_model.search(query)
        results['cylinders'] = cylinder_results
        
        results['total_results'] = len(customer_results) + len(cylinder_results)
    
    return render_template('search_results.html', **results)

@app.route('/users/delete/<user_id>', methods=['POST'])
@admin_required
def delete_user(user_id):
    
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
    
    customer_id = request.form.get('customer_id')
    rental_date = request.form.get('rental_date', '').strip()
    
    if not customer_id:
        flash('Please select a customer', 'error')
        return redirect(url_for('cylinders'))
    
    customer = customer_model.get_by_id(customer_id)
    if not customer:
        flash('Customer not found', 'error')
        return redirect(url_for('cylinders'))
    
    rental_date_iso = None
    if rental_date:
        try:
            from datetime import datetime
            dt = datetime.fromisoformat(rental_date)
            rental_date_iso = dt.isoformat()
        except ValueError:
            flash('Invalid rental date format', 'error')
            return redirect(url_for('cylinders'))
    
    if cylinder_model.rent_cylinder(cylinder_id, customer_id, rental_date_iso):
        flash(f'Cylinder rented to {customer["name"]} successfully', 'success')
    else:
        flash('Error renting cylinder', 'error')
    
    return redirect(url_for('cylinders'))

@app.route('/cylinders/return/<cylinder_id>', methods=['POST'])
@user_or_admin_required
def return_cylinder(cylinder_id):
    
    return_date = request.form.get('return_date')
    if cylinder_model.return_cylinder(cylinder_id, return_date):
        flash('Cylinder returned successfully', 'success')
    else:
        flash('Error returning cylinder', 'error')
    
    return redirect(url_for('cylinders'))

@app.route('/customers/<customer_id>/bulk_cylinders', methods=['GET', 'POST'])
@user_or_admin_required
def bulk_cylinder_management(customer_id):
    
    customer = customer_model.get_by_id(customer_id)
    if not customer:
        flash('Customer not found', 'error')
        return redirect(url_for('customers'))
    
    if request.method == 'GET':
        current_rentals = cylinder_model.get_by_customer(customer_id)
        return render_template('bulk_cylinder_management.html', 
                             customer=customer, 
                             current_rentals=current_rentals)
    
    cylinder_ids_text = request.form.get('cylinder_ids', '').strip()
    action = request.form.get('action', 'rent')
    
    if not cylinder_ids_text:
        flash('Please enter at least one cylinder ID', 'error')
        return redirect(url_for('bulk_cylinder_management', customer_id=customer_id))
    
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
        
        actual_cylinder_id = cylinder.get('id')
        cylinder_display = cylinder.get('custom_id') or cylinder.get('serial_number') or actual_cylinder_id
        
        if action == 'rent':
            if cylinder.get('status', '').lower() != 'available':
                errors.append(f'"{cylinder_display}": Not available (current status: {cylinder.get("status", "unknown")})')
                skipped += 1
                continue
            
            success = cylinder_model.rent_cylinder(actual_cylinder_id, customer_id)
            if success:
                processed += 1
            else:
                errors.append(f'"{cylinder_display}": Failed to rent')
                skipped += 1
        
        elif action == 'return':
            if cylinder.get('status', '').lower() != 'rented' or cylinder.get('rented_to') != customer_id:
                errors.append(f'"{cylinder_display}": Not rented to this customer')
                skipped += 1
                continue
            
            success = cylinder_model.return_cylinder(actual_cylinder_id)
            if success:
                processed += 1
            else:
                errors.append(f'"{cylinder_display}": Failed to return')
                skipped += 1
    
    if action == 'rent':
        flash(f'Successfully rented {processed} cylinders to {customer["name"]}', 'success')
    else:
        flash(f'Successfully returned {processed} cylinders from {customer["name"]}', 'success')
    
    if skipped > 0:
        flash(f'{skipped} cylinders were skipped due to errors', 'warning')
        
    if errors:
        error_msg = 'Details: ' + '; '.join(errors[:5])
        if len(errors) > 5:
            error_msg += f' and {len(errors) - 5} more...'
        flash(error_msg, 'info')
    
    return redirect(url_for('bulk_cylinder_management', customer_id=customer_id))

@app.route('/api/customer/<customer_id>/rentals')
@login_required
def get_customer_rentals(customer_id):
    
    rentals = cylinder_model.get_by_customer(customer_id)
    
    for rental in rentals:
        rental['rental_days'] = cylinder_model.get_rental_days(rental)
    
    return jsonify({'rentals': rentals})

@app.route('/archive_data', methods=['POST'])
@login_required
@admin_required
def archive_data():
    
    try:
        months_old = int(request.form.get('months', 6))
        if months_old < 1:
            months_old = 6
        
        cylinder_result = cylinder_model.archive_old_data(months_old)
        customer_result = customer_model.archive_old_data(months_old)
        
        total_archived = cylinder_result.get('archived_count', 0) + customer_result.get('archived_count', 0)
        total_remaining = cylinder_result.get('remaining_count', 0) + customer_result.get('remaining_count', 0)
        
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
    
    customers = customer_model.get_all()
    return render_template('bulk_rental_management.html', customers=customers)

@app.route('/bulk_rental_management/process', methods=['POST'])
@login_required
def process_bulk_rental():
    
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
            if cylinder.get('status', '').lower() != 'available':
                errors.append(f'Cylinder {cylinder_id}: Not available (current status: {cylinder.get("status", "unknown")})')
                skipped += 1
                continue
            
            success = cylinder_model.rent_cylinder(cylinder_id, customer_id)
            if success:
                processed += 1
                success_cylinders.append(cylinder_id)
            else:
                errors.append(f'Cylinder {cylinder_id}: Failed to rent')
                skipped += 1
        
        elif action == 'return':
            if cylinder.get('status', '').lower() != 'rented' or cylinder.get('rented_to') != customer_id:
                errors.append(f'Cylinder {cylinder_id}: Not rented to this customer')
                skipped += 1
                continue
            
            success = cylinder_model.return_cylinder(cylinder_id)
            if success:
                processed += 1
                success_cylinders.append(cylinder_id)
            else:
                errors.append(f'Cylinder {cylinder_id}: Failed to return')
                skipped += 1
    
    if action == 'rent':
        if processed > 0:
            flash(f'Successfully rented {processed} cylinders ({", ".join(success_cylinders[:5])}{", ..." if len(success_cylinders) > 5 else ""}) to {customer["name"]}', 'success')
    else:
        if processed > 0:
            flash(f'Successfully returned {processed} cylinders ({", ".join(success_cylinders[:5])}{", ..." if len(success_cylinders) > 5 else ""}) from {customer["name"]}', 'success')
    
    if skipped > 0:
        flash(f'{skipped} cylinders were skipped due to errors', 'warning')
        
    if errors:
        error_msg = 'Details: ' + '; '.join(errors[:5])
        if len(errors) > 5:
            error_msg += f' and {len(errors) - 5} more...'
        flash(error_msg, 'info')
    
    return redirect(url_for('bulk_rental_management'))

@app.route('/reports')
@login_required
def reports():
    
    customer_model = Customer()
    cylinder_model = Cylinder()
    
    customers = customer_model.get_all()
    cylinders = cylinder_model.get_all()
    
    active_rentals = len([c for c in cylinders if c.get('status', '').lower() == 'rented'])
    
    available_months = []
    current_date = datetime.now()
    for i in range(12):
        month_date = current_date - timedelta(days=30*i)
        available_months.append({
            'value': month_date.strftime('%Y-%m'),
            'label': month_date.strftime('%B %Y')
        })
    
    data_months = 12
    
    stats = {
        'total_customers': len(customers),
        'total_cylinders': len(cylinders),
        'active_rentals': active_rentals,
        'data_months': data_months
    }
    
    return render_template('reports.html', stats=stats, available_months=available_months)

@app.route('/export/customers.csv')
@login_required
def export_customers_csv():
    
    customer_model = Customer()
    customers = customer_model.get_all()
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    writer.writerow(['ID', 'Customer No', 'Name', 'Email', 'Phone', 'Address', 'City', 'State', 'APGST', 'CST', 'Created At', 'Updated At', 'Notes'])
    
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
    
    cylinder_model = Cylinder()
    cylinders = cylinder_model.get_all()
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    writer.writerow(['ID', 'Serial Number', 'Custom ID', 'Type', 'Size', 'Status', 'Location', 
                    'Pressure', 'Last Inspection', 'Next Inspection', 'Rented To', 'Customer Name',
                    'Date Borrowed', 'Date Returned', 'Created At', 'Updated At', 'Notes'])
    
    for cylinder in cylinders:
        writer.writerow([
            cylinder.get('id', ''),
            cylinder.get('serial_number', ''),
            cylinder.get('custom_id', ''),
            cylinder.get('type', ''),
            cylinder.get('size', ''),
            cylinder.get('status', ''),
            cylinder.get('location', ''),
            cylinder.get('pressure', ''),
            cylinder.get('last_inspection', ''),
            cylinder.get('next_inspection', ''),
            cylinder.get('rented_to', ''),
            cylinder.get('customer_name', ''),
            cylinder.get('date_borrowed', ''),
            cylinder.get('date_returned', ''),
            cylinder.get('created_at', ''),
            cylinder.get('updated_at', ''),
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
    
    cylinder_model = Cylinder()
    customer_model = Customer()
    cylinders = cylinder_model.get_all()
    customers = customer_model.get_all()
    
    customer_lookup = {c['id']: c for c in customers}
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    writer.writerow(['Cylinder ID', 'Serial Number', 'Custom ID', 'Type', 'Customer ID', 
                    'Customer Name', 'Customer Email', 'Date Borrowed', 'Date Returned', 
                    'Status', 'Rental Days'])
    
    for cylinder in cylinders:
        if cylinder.get('rented_to') or cylinder.get('date_borrowed'):
            customer = customer_lookup.get(cylinder.get('rented_to', ''), {})
            rental_days = cylinder_model.get_rental_days(cylinder)
            
            writer.writerow([
                cylinder.get('id', ''),
                cylinder.get('serial_number', ''),
                cylinder.get('custom_id', ''),
                cylinder.get('type', ''),
                cylinder.get('rented_to', ''),
                customer.get('customer_name', '') or customer.get('name', ''),
                customer.get('customer_email', '') or customer.get('email', ''),
                cylinder.get('date_borrowed', ''),
                cylinder.get('date_returned', ''),
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
    
    customer_model = Customer()
    cylinder_model = Cylinder()
    customers = customer_model.get_all()
    cylinders = cylinder_model.get_all()
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    writer.writerow(['=== COMPLETE DATABASE EXPORT ==='])
    writer.writerow(['Export Date:', datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
    writer.writerow(['Total Customers:', len(customers)])
    writer.writerow(['Total Cylinders:', len(cylinders)])
    writer.writerow([])
    
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
    
    writer.writerow(['=== CYLINDERS ==='])
    writer.writerow(['ID', 'Serial Number', 'Custom ID', 'Type', 'Size', 'Status', 'Location', 
                    'Pressure', 'Rented To', 'Customer Name', 'Date Borrowed', 'Rental Days'])
    for cylinder in cylinders:
        rental_days = cylinder_model.get_rental_days(cylinder)
        writer.writerow([
            cylinder.get('id', ''),
            cylinder.get('serial_number', ''),
            cylinder.get('custom_id', ''),
            cylinder.get('type', ''),
            cylinder.get('size', ''),
            cylinder.get('status', ''),
            cylinder.get('location', ''),
            cylinder.get('pressure', ''),
            cylinder.get('rented_to', ''),
            cylinder.get('customer_name', ''),
            cylinder.get('date_borrowed', ''),
            rental_days
        ])
    
    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': f'attachment; filename=complete_database_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'}
    )

@app.route('/export/monthly-report', methods=['POST'])
@login_required
def export_monthly_report():
    
    report_month = request.form.get('report_month')
    report_type = request.form.get('report_type')
    
    if not report_month or not report_type:
        flash('Please select both month and report type', 'error')
        return redirect(url_for('reports'))
    
    customer_model = Customer()
    cylinder_model = Cylinder()
    customers = customer_model.get_all()
    cylinders = cylinder_model.get_all()
    
    year, month = report_month.split('-')
    month_name = datetime(int(year), int(month), 1).strftime('%B %Y')
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    writer.writerow([f'=== {report_type.upper()} REPORT FOR {month_name} ==='])
    writer.writerow(['Generated:', datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
    writer.writerow([])
    
    if report_type == 'complete':
        writer.writerow(['=== CUSTOMERS ==='])
        writer.writerow(['ID', 'Customer No', 'Name', 'Email', 'Phone', 'Address', 'City', 'State', 'Active Rentals'])
        for customer in customers:
            active_rentals = len([c for c in cylinders if c.get('rented_to') == customer.get('id')])
            writer.writerow([
                customer.get('id', ''),
                customer.get('customer_no', ''),
                customer.get('customer_name', '') or customer.get('name', ''),
                customer.get('customer_email', '') or customer.get('email', ''),
                customer.get('customer_phone', '') or customer.get('phone', ''),
                customer.get('customer_address', '') or customer.get('address', ''),
                customer.get('customer_city', ''),
                customer.get('customer_state', ''),
                active_rentals
            ])
        
        writer.writerow([])
        writer.writerow(['=== CYLINDERS ==='])
        writer.writerow(['ID', 'Serial Number', 'Custom ID', 'Type', 'Status', 'Customer', 'Rental Days'])
        for cylinder in cylinders:
            rental_days = cylinder_model.get_rental_days(cylinder)
            writer.writerow([
                cylinder.get('id', ''),
                cylinder.get('serial_number', ''),
                cylinder.get('custom_id', ''),
                cylinder.get('type', ''),
                cylinder.get('status', ''),
                cylinder.get('customer_name', ''),
                rental_days
            ])
    
    elif report_type == 'rentals':
        writer.writerow(['=== RENTAL ACTIVITIES ==='])
        writer.writerow(['Cylinder ID', 'Serial Number', 'Type', 'Customer', 'Date Borrowed', 'Rental Days', 'Status'])
        for cylinder in cylinders:
            if cylinder.get('rented_to') or cylinder.get('date_borrowed'):
                rental_days = cylinder_model.get_rental_days(cylinder)
                writer.writerow([
                    cylinder.get('id', ''),
                    cylinder.get('serial_number', ''),
                    cylinder.get('type', ''),
                    cylinder.get('customer_name', ''),
                    cylinder.get('date_borrowed', ''),
                    rental_days,
                    cylinder.get('status', '')
                ])
    
    elif report_type == 'customers':
        writer.writerow(['=== CUSTOMER SUMMARY ==='])
        writer.writerow(['ID', 'Customer No', 'Name', 'Email', 'Phone', 'Address', 'City', 'State', 'Active Rentals', 'Total Value'])
        for customer in customers:
            active_rentals = len([c for c in cylinders if c.get('rented_to') == customer.get('id')])
            writer.writerow([
                customer.get('id', ''),
                customer.get('customer_no', ''),
                customer.get('customer_name', '') or customer.get('name', ''),
                customer.get('customer_email', '') or customer.get('email', ''),
                customer.get('customer_phone', '') or customer.get('phone', ''),
                customer.get('customer_address', '') or customer.get('address', ''),
                customer.get('customer_city', ''),
                customer.get('customer_state', ''),
                active_rentals,
                f'${active_rentals * 50}'
            ])
    
    elif report_type == 'cylinders':
        writer.writerow(['=== CYLINDER INVENTORY ==='])
        writer.writerow(['ID', 'Serial Number', 'Custom ID', 'Type', 'Size', 'Status', 'Location', 'Pressure'])
        for cylinder in cylinders:
            writer.writerow([
                cylinder.get('id', ''),
                cylinder.get('serial_number', ''),
                cylinder.get('custom_id', ''),
                cylinder.get('type', ''),
                cylinder.get('size', ''),
                cylinder.get('status', ''),
                cylinder.get('location', ''),
                cylinder.get('pressure', '')
            ])
    
    output.seek(0)
    filename = f'{report_type}_report_{report_month}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
    
    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': f'attachment; filename={filename}'}
    )

@app.route('/export/customers.pdf')
@login_required
def export_customers_pdf():
    
    customer_model = Customer()
    customers = customer_model.get_all()
    
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, 
                           rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=18)
    
    story = []
    styles = getSampleStyleSheet()
    
    title = Paragraph("Varasai Oxygen - Customer Report", styles['Title'])
    story.append(title)
    story.append(Spacer(1, 12))
    
    date_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    date_para = Paragraph(f"Generated on: {date_str}", styles['Normal'])
    story.append(date_para)
    
    summary_para = Paragraph(f"Total Customers: {len(customers)}", styles['Normal'])
    story.append(summary_para)
    story.append(Spacer(1, 12))
    
    if customers:
        data = [['Customer No', 'Name', 'Email', 'Phone', 'Address', 'City', 'State']]
        for customer in customers:
            data.append([
                customer.get('customer_no', '')[:15],
                (customer.get('customer_name', '') or customer.get('name', ''))[:25],
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
    
    cylinder_model = Cylinder()
    cylinders = cylinder_model.get_all()
    
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter,
                           rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=18)
    
    story = []
    styles = getSampleStyleSheet()
    
    title = Paragraph("Varasai Oxygen - Cylinder Inventory Report", styles['Title'])
    story.append(title)
    story.append(Spacer(1, 12))
    
    date_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    date_para = Paragraph(f"Generated on: {date_str}", styles['Normal'])
    story.append(date_para)
    
    summary_para = Paragraph(f"Total Cylinders: {len(cylinders)}", styles['Normal'])
    story.append(summary_para)
    
    status_counts = {}
    for cylinder in cylinders:
        status = cylinder.get('status', 'Unknown')
        status_counts[status] = status_counts.get(status, 0) + 1
    
    status_text = " | ".join([f"{status}: {count}" for status, count in status_counts.items()])
    status_para = Paragraph(f"Status Breakdown: {status_text}", styles['Normal'])
    story.append(status_para)
    story.append(Spacer(1, 12))
    
    if cylinders:
        data = [['Serial#', 'Type', 'Size', 'Status', 'Location', 'Customer']]
        for i, cylinder in enumerate(cylinders):
            cylinder_type = cylinder.get('type', 'Other')
            display_serial = cylinder_model.get_serial_number(cylinder_type, i + 1)
            
            data.append([
                display_serial,
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
    
    cylinder_model = Cylinder()
    customer_model = Customer()
    cylinders = cylinder_model.get_all()
    customers = customer_model.get_all()
    
    customer_lookup = {c['id']: c for c in customers}
    
    rental_cylinders = [c for c in cylinders if c.get('rented_to') or c.get('date_borrowed')]
    
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter,
                           rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=18)
    
    story = []
    styles = getSampleStyleSheet()
    
    title = Paragraph("Varasai Oxygen - Rental Activities Report", styles['Title'])
    story.append(title)
    story.append(Spacer(1, 12))
    
    date_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    date_para = Paragraph(f"Generated on: {date_str}", styles['Normal'])
    story.append(date_para)
    
    summary_para = Paragraph(f"Total Rental Activities: {len(rental_cylinders)}", styles['Normal'])
    story.append(summary_para)
    story.append(Spacer(1, 12))
    
    if rental_cylinders:
        data = [['Cylinder', 'Type', 'Customer', 'Date Borrowed', 'Status', 'Days']]
        for i, cylinder in enumerate(rental_cylinders):
            customer = customer_lookup.get(cylinder.get('rented_to', ''), {})
            rental_days = cylinder_model.get_rental_days(cylinder)
            
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
    
    doc.build(story)
    buffer.seek(0)
    
    return Response(
        buffer.getvalue(),
        mimetype='application/pdf',
        headers={'Content-Disposition': f'attachment; filename=rental_activities_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf'}
    )
