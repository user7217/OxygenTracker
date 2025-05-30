from flask import render_template, request, redirect, url_for, flash, jsonify
from app import app
from models import Customer, Cylinder

# Initialize models
customer_model = Customer()
cylinder_model = Cylinder()

@app.route('/')
def index():
    """Dashboard showing overview"""
    customers = customer_model.get_all()
    cylinders = cylinder_model.get_all()
    
    # Get cylinder status counts
    available_cylinders = len([c for c in cylinders if c.get('status', '').lower() == 'available'])
    rented_cylinders = len([c for c in cylinders if c.get('status', '').lower() == 'rented'])
    maintenance_cylinders = len([c for c in cylinders if c.get('status', '').lower() == 'maintenance'])
    
    stats = {
        'total_customers': len(customers),
        'total_cylinders': len(cylinders),
        'available_cylinders': available_cylinders,
        'rented_cylinders': rented_cylinders,
        'maintenance_cylinders': maintenance_cylinders
    }
    
    return render_template('index.html', stats=stats)

# Customer routes
@app.route('/customers')
def customers():
    """List all customers with search functionality"""
    search_query = request.args.get('search', '')
    
    if search_query:
        customers_list = customer_model.search(search_query)
    else:
        customers_list = customer_model.get_all()
    
    return render_template('customers.html', customers=customers_list, search_query=search_query)

@app.route('/customers/add', methods=['GET', 'POST'])
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
def cylinders():
    """List all cylinders with search and filter functionality"""
    search_query = request.args.get('search', '')
    status_filter = request.args.get('status', '')
    
    if search_query:
        cylinders_list = cylinder_model.search(search_query)
    elif status_filter:
        cylinders_list = cylinder_model.get_by_status(status_filter)
    else:
        cylinders_list = cylinder_model.get_all()
    
    return render_template('cylinders.html', 
                         cylinders=cylinders_list, 
                         search_query=search_query,
                         status_filter=status_filter)

@app.route('/cylinders/add', methods=['GET', 'POST'])
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
                return render_template('add_cylinder.html')
            cylinder_data[field] = value
        
        # Add optional fields
        cylinder_data['pressure'] = request.form.get('pressure', '').strip()
        cylinder_data['last_inspection'] = request.form.get('last_inspection', '').strip()
        cylinder_data['next_inspection'] = request.form.get('next_inspection', '').strip()
        cylinder_data['notes'] = request.form.get('notes', '').strip()
        
        try:
            new_cylinder = cylinder_model.add(cylinder_data)
            flash(f'Cylinder {new_cylinder["serial_number"]} added successfully with ID: {new_cylinder["id"]}', 'success')
            return redirect(url_for('cylinders'))
        except Exception as e:
            flash(f'Error adding cylinder: {str(e)}', 'error')
    
    return render_template('add_cylinder.html')

@app.route('/cylinders/edit/<cylinder_id>', methods=['GET', 'POST'])
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
                return render_template('edit_cylinder.html', cylinder=cylinder)
            cylinder_data[field] = value
        
        # Add optional fields
        cylinder_data['pressure'] = request.form.get('pressure', '').strip()
        cylinder_data['last_inspection'] = request.form.get('last_inspection', '').strip()
        cylinder_data['next_inspection'] = request.form.get('next_inspection', '').strip()
        cylinder_data['notes'] = request.form.get('notes', '').strip()
        
        try:
            updated_cylinder = cylinder_model.update(cylinder_id, cylinder_data)
            if updated_cylinder:
                flash(f'Cylinder {updated_cylinder["serial_number"]} updated successfully', 'success')
                return redirect(url_for('cylinders'))
            else:
                flash('Error updating cylinder', 'error')
        except Exception as e:
            flash(f'Error updating cylinder: {str(e)}', 'error')
    
    return render_template('edit_cylinder.html', cylinder=cylinder)

@app.route('/cylinders/delete/<cylinder_id>', methods=['POST'])
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
