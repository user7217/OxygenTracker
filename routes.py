from flask import render_template, request, redirect, url_for, flash, jsonify, session
from app import app
from models import Customer, Cylinder
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

# Data Import routes
@app.route('/import')
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
