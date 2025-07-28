"""
Clean SQLite Flask app for Varasai Oxygen Cylinder Tracker
Using SQLite database for simplicity and portability
"""
import os
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import json
import uuid
from functools import wraps

app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "your-secret-key-here")

DATABASE = 'oxygen_tracker.db'

def get_db_connection():
    """Get SQLite database connection"""
    try:
        connection = sqlite3.connect(DATABASE)
        connection.row_factory = sqlite3.Row  # This allows dict-like access
        return connection
    except Exception as e:
        print(f"Database connection error: {e}")
        return None

def init_sqlite_database():
    """Initialize SQLite database with tables"""
    connection = get_db_connection()
    if not connection:
        print("Failed to connect to SQLite database")
        return False
        
    try:
        cursor = connection.cursor()
        
        # Create customers table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS customers (
                id TEXT PRIMARY KEY,
                customer_no TEXT UNIQUE,
                customer_name TEXT NOT NULL,
                customer_email TEXT,
                customer_phone TEXT,
                customer_address TEXT,
                customer_city TEXT,
                customer_state TEXT,
                customer_apgst TEXT,
                customer_cst TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create cylinders table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS cylinders (
                id TEXT PRIMARY KEY,
                custom_id TEXT UNIQUE,
                serial_number TEXT,
                type TEXT DEFAULT 'Medical Oxygen',
                size TEXT DEFAULT '40L',
                status TEXT DEFAULT 'available',
                location TEXT DEFAULT 'Warehouse',
                pressure TEXT,
                last_inspection TEXT,
                next_inspection TEXT,
                notes TEXT,
                rented_to TEXT,
                customer_name TEXT,
                customer_email TEXT,
                customer_phone TEXT,
                customer_no TEXT,
                date_borrowed DATETIME,
                date_returned DATETIME,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create rental_history table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS rental_history (
                id TEXT PRIMARY KEY,
                customer_no TEXT,
                customer_name TEXT,
                cylinder_custom_id TEXT,
                cylinder_type TEXT,
                cylinder_size TEXT,
                dispatch_date DATETIME,
                return_date DATETIME,
                rental_days INTEGER DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create indexes
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_customer_no ON customers(customer_no)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_customer_name ON customers(customer_name)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_custom_id ON cylinders(custom_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_status ON cylinders(status)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_cylinder_customer_no ON cylinders(customer_no)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_rental_customer_no ON rental_history(customer_no)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_rental_cylinder_id ON rental_history(cylinder_custom_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_rental_dispatch_date ON rental_history(dispatch_date)')
        
        connection.commit()
        print("✓ SQLite database tables created successfully!")
        return True
        
    except Exception as e:
        print(f"Error initializing SQLite database: {e}")
        return False
    finally:
        connection.close()

# User management functions
def load_users():
    """Load users from users.json"""
    try:
        with open('users.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        # Create default admin user
        default_users = {
            "admin": {
                "id": "admin",
                "username": "admin", 
                "password_hash": generate_password_hash("admin123"),
                "role": "admin"
            }
        }
        save_users(default_users)
        return default_users

def save_users(users):
    """Save users to users.json"""
    with open('users.json', 'w') as f:
        json.dump(users, f, indent=2)

def authenticate_user(username, password):
    """Authenticate user login"""
    users = load_users()
    if username in users:
        user = users[username]
        if check_password_hash(user['password_hash'], password):
            return user
    return None

def login_required(f):
    """Decorator to require login for routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Routes
@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login"""
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = authenticate_user(username, password)
        if user:
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['role'] = user['role']
            flash(f'Welcome back, {user["username"]}!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password', 'error')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    """User logout"""
    session.clear()
    flash('You have been logged out', 'info')
    return redirect(url_for('login'))

@app.route('/')
@login_required
def index():
    """Dashboard"""
    connection = get_db_connection()
    if not connection:
        flash('Database connection error', 'error')
        return render_template('index.html', stats={'total_customers': 0, 'total_cylinders': 0, 'rented_cylinders': 0, 'available_cylinders': 0, 'maintenance_cylinders': 0})
    
    try:
        cursor = connection.cursor()
        
        # Get basic statistics
        cursor.execute('SELECT COUNT(*) as count FROM customers')
        result = cursor.fetchone()
        customer_count = result[0] if result else 0
        
        cursor.execute('SELECT COUNT(*) as count FROM cylinders')
        result = cursor.fetchone()
        cylinder_count = result[0] if result else 0
        
        cursor.execute("SELECT COUNT(*) as count FROM cylinders WHERE status = 'rented'")
        result = cursor.fetchone()
        rented_count = result[0] if result else 0
        
        available_count = cylinder_count - rented_count
        
        # Create stats object to match template expectations
        stats = {
            'total_customers': customer_count,
            'total_cylinders': cylinder_count,
            'rented_cylinders': rented_count,
            'available_cylinders': available_count,
            'maintenance_cylinders': 0  # Add this field for template compatibility
        }
        
        return render_template('index.html', stats=stats)
        
    except Exception as e:
        print(f"Error getting dashboard stats: {e}")
        stats = {'total_customers': 0, 'total_cylinders': 0, 'rented_cylinders': 0, 'available_cylinders': 0, 'maintenance_cylinders': 0}
        return render_template('index.html', stats=stats)
    finally:
        connection.close()

@app.route('/customers')
@login_required
def customers():
    """Customers page"""
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    per_page = request.args.get('per_page', 25, type=int)
    offset = (page - 1) * per_page
    
    connection = get_db_connection()
    if not connection:
        flash('Database connection error', 'error')
        return render_template('customers.html', customers=[], pagination={'total': 0, 'per_page': per_page, 'page': page, 'has_next': False, 'has_prev': False}, search_query=search)
    
    try:
        cursor = connection.cursor()
        
        # Build query with search (SQLite uses ? placeholders)
        if search:
            query = '''
                SELECT * FROM customers 
                WHERE customer_name LIKE ? OR customer_no LIKE ? OR customer_phone LIKE ?
                ORDER BY customer_name
                LIMIT ? OFFSET ?
            '''
            search_term = f'%{search}%'
            cursor.execute(query, (search_term, search_term, search_term, per_page, offset))
            customers_list = cursor.fetchall()
            
            count_query = '''
                SELECT COUNT(*) as total FROM customers 
                WHERE customer_name LIKE ? OR customer_no LIKE ? OR customer_phone LIKE ?
            '''
            cursor.execute(count_query, (search_term, search_term, search_term))
            result = cursor.fetchone()
            total = result[0] if result else 0
        else:
            query = 'SELECT * FROM customers ORDER BY customer_name LIMIT ? OFFSET ?'
            cursor.execute(query, (per_page, offset))
            customers_list = cursor.fetchall()
            
            cursor.execute('SELECT COUNT(*) as total FROM customers')
            result = cursor.fetchone()
            total = result[0] if result else 0
        
        # Create pagination info
        pagination = {
            'total': total,
            'per_page': per_page,
            'page': page,
            'has_next': offset + per_page < total,
            'has_prev': page > 1,
            'next_num': page + 1,
            'prev_num': page - 1
        }
        
        return render_template('customers.html', customers=customers_list, pagination=pagination, search_query=search)
        
    except Exception as e:
        print(f"Error getting customers: {e}")
        return render_template('customers.html', customers=[], pagination={'total': 0, 'per_page': per_page, 'page': page, 'has_next': False, 'has_prev': False}, search_query=search)
    finally:
        connection.close()

@app.route('/cylinders')
@login_required
def cylinders():
    """Cylinders page"""
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    status_filter = request.args.get('status', '')
    per_page = request.args.get('per_page', 25, type=int)
    offset = (page - 1) * per_page
    
    connection = get_db_connection()
    if not connection:
        flash('Database connection error', 'error')
        return render_template('cylinders.html', cylinders=[], pagination={'total': 0, 'per_page': per_page, 'page': page, 'has_next': False, 'has_prev': False}, search_query=search, status_filter=status_filter, customers=[])
    
    try:
        cursor = connection.cursor()
        
        # Build query with search and filters
        conditions = []
        params = []
        
        if search:
            conditions.append("(custom_id LIKE ? OR serial_number LIKE ? OR type LIKE ? OR location LIKE ?)")
            search_term = f'%{search}%'
            params.extend([search_term, search_term, search_term, search_term])
        
        if status_filter:
            conditions.append("status = ?")
            params.append(status_filter)
        
        where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""
        
        query = f'''
            SELECT * FROM cylinders 
            {where_clause}
            ORDER BY status DESC, date_borrowed DESC
            LIMIT ? OFFSET ?
        '''
        params.extend([per_page, offset])
        cursor.execute(query, params)
        cylinders_list = cursor.fetchall()
        
        # Get total count for pagination
        count_query = f'SELECT COUNT(*) as total FROM cylinders {where_clause}'
        count_params = params[:-2]  # Remove limit and offset
        cursor.execute(count_query, count_params)
        result = cursor.fetchone()
        total = result[0] if result else 0
        
        # Get customers for rental modal
        cursor.execute('SELECT * FROM customers ORDER BY customer_name')
        customers_list = cursor.fetchall()
        
        # Create pagination info
        pagination = {
            'total': total,
            'per_page': per_page,
            'page': page,
            'has_next': offset + per_page < total,
            'has_prev': page > 1,
            'next_num': page + 1,
            'prev_num': page - 1
        }
        
        return render_template('cylinders.html', 
                             cylinders=cylinders_list, 
                             pagination=pagination, 
                             search_query=search,
                             status_filter=status_filter,
                             customers=customers_list)
        
    except Exception as e:
        print(f"Error getting cylinders: {e}")
        return render_template('cylinders.html', cylinders=[], pagination={'total': 0, 'per_page': per_page, 'page': page, 'has_next': False, 'has_prev': False}, search_query=search, status_filter=status_filter, customers=[])
    finally:
        connection.close()

# Additional routes for template compatibility

@app.route('/customers/<customer_id>')
@login_required
def customer_details(customer_id):
    """Customer details page - placeholder"""
    flash('Customer details page not yet implemented', 'info')
    return redirect(url_for('customers'))

@app.route('/cylinders/<cylinder_id>')
@login_required
def cylinder_details(cylinder_id):
    """Cylinder details page - placeholder"""
    flash('Cylinder details page not yet implemented', 'info')
    return redirect(url_for('cylinders'))

@app.route('/customers/add', methods=['GET', 'POST'])
@login_required
def add_customer():
    """Add customer"""
    if request.method == 'POST':
        # Get form data
        customer_no = request.form.get('customer_no')
        customer_name = request.form.get('customer_name')
        customer_email = request.form.get('customer_email', '')
        customer_phone = request.form.get('customer_phone', '')
        customer_address = request.form.get('customer_address', '')
        customer_city = request.form.get('customer_city', '')
        customer_state = request.form.get('customer_state', '')
        customer_apgst = request.form.get('customer_apgst', '')
        customer_cst = request.form.get('customer_cst', '')
        
        if not customer_name:
            flash('Customer name is required', 'error')
            return render_template('add_customer.html')
        
        connection = get_db_connection()
        if not connection:
            flash('Database connection error', 'error')
            return render_template('add_customer.html')
        
        try:
            cursor = connection.cursor()
            customer_id = str(uuid.uuid4())
            
            cursor.execute('''
                INSERT INTO customers (id, customer_no, customer_name, customer_email, customer_phone,
                                     customer_address, customer_city, customer_state, customer_apgst, customer_cst)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (customer_id, customer_no, customer_name, customer_email, customer_phone,
                  customer_address, customer_city, customer_state, customer_apgst, customer_cst))
            
            connection.commit()
            flash(f'Customer {customer_name} added successfully!', 'success')
            return redirect(url_for('customers'))
            
        except Exception as e:
            print(f"Error adding customer: {e}")
            flash('Error adding customer', 'error')
            return render_template('add_customer.html')
        finally:
            connection.close()
    
    return render_template('add_customer.html')

@app.route('/cylinders/add', methods=['GET', 'POST'])
@login_required
def add_cylinder():
    """Add cylinder"""
    if request.method == 'POST':
        # Get form data
        custom_id = request.form.get('custom_id')
        serial_number = request.form.get('serial_number', '')
        cylinder_type = request.form.get('type', 'Medical Oxygen')
        size = request.form.get('size', '40L')
        status = request.form.get('status', 'available')
        location = request.form.get('location', 'Warehouse')
        pressure = request.form.get('pressure', '')
        notes = request.form.get('notes', '')
        
        if not custom_id:
            flash('Custom ID is required', 'error')
            return render_template('add_cylinder.html')
        
        connection = get_db_connection()
        if not connection:
            flash('Database connection error', 'error')
            return render_template('add_cylinder.html')
        
        try:
            cursor = connection.cursor()
            cylinder_id = str(uuid.uuid4())
            
            cursor.execute('''
                INSERT INTO cylinders (id, custom_id, serial_number, type, size, status, location, pressure, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (cylinder_id, custom_id, serial_number, cylinder_type, size, status, location, pressure, notes))
            
            connection.commit()
            flash(f'Cylinder {custom_id} added successfully!', 'success')
            return redirect(url_for('cylinders'))
            
        except Exception as e:
            print(f"Error adding cylinder: {e}")
            flash('Error adding cylinder', 'error')
            return render_template('add_cylinder.html')
        finally:
            connection.close()
    
    return render_template('add_cylinder.html')

@app.route('/customers/<customer_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_customer(customer_id):
    """Edit customer page - placeholder"""
    flash('Edit customer feature not yet implemented', 'info')
    return redirect(url_for('customers'))

@app.route('/cylinders/<cylinder_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_cylinder(cylinder_id):
    """Edit cylinder page - placeholder"""
    flash('Edit cylinder feature not yet implemented', 'info')
    return redirect(url_for('cylinders'))

@app.route('/customers/<customer_id>/delete', methods=['POST'])
@login_required
def delete_customer(customer_id):
    """Delete customer - placeholder"""
    flash('Delete customer feature not yet implemented', 'info')
    return redirect(url_for('customers'))

@app.route('/cylinders/<cylinder_id>/delete', methods=['POST'])
@login_required
def delete_cylinder(cylinder_id):
    """Delete cylinder - placeholder"""
    flash('Delete cylinder feature not yet implemented', 'info')
    return redirect(url_for('cylinders'))

@app.route('/rent_cylinder', methods=['POST'])
@login_required
def rent_cylinder():
    """Rent cylinder to customer"""
    cylinder_id = request.form.get('cylinder_id')
    customer_no = request.form.get('customer_no')
    
    if not cylinder_id or not customer_no:
        flash('Cylinder ID and Customer are required', 'error')
        return redirect(url_for('cylinders'))
    
    connection = get_db_connection()
    if not connection:
        flash('Database connection error', 'error')
        return redirect(url_for('cylinders'))
    
    try:
        cursor = connection.cursor()
        
        # Get customer details
        cursor.execute('SELECT * FROM customers WHERE customer_no = ?', (customer_no,))
        customer = cursor.fetchone()
        if not customer:
            flash('Customer not found', 'error')
            return redirect(url_for('cylinders'))
        
        # Update cylinder status
        cursor.execute('''
            UPDATE cylinders 
            SET status = 'rented', 
                location = 'Customer Site',
                rented_to = ?,
                customer_name = ?,
                customer_email = ?,
                customer_phone = ?,
                customer_no = ?,
                date_borrowed = datetime('now')
            WHERE id = ?
        ''', (customer_no, customer['customer_name'], customer['customer_email'], 
              customer['customer_phone'], customer_no, cylinder_id))
        
        connection.commit()
        flash('Cylinder rented successfully!', 'success')
        
    except Exception as e:
        print(f"Error renting cylinder: {e}")
        flash('Error renting cylinder', 'error')
    finally:
        connection.close()
    
    return redirect(url_for('cylinders'))

@app.route('/return_cylinder', methods=['POST'])
@login_required
def return_cylinder():
    """Return cylinder from customer"""
    cylinder_id = request.form.get('cylinder_id')
    
    if not cylinder_id:
        flash('Cylinder ID is required', 'error')
        return redirect(url_for('cylinders'))
    
    connection = get_db_connection()
    if not connection:
        flash('Database connection error', 'error')
        return redirect(url_for('cylinders'))
    
    try:
        cursor = connection.cursor()
        
        # Get cylinder details for rental history
        cursor.execute('SELECT * FROM cylinders WHERE id = ?', (cylinder_id,))
        cylinder = cursor.fetchone()
        if not cylinder:
            flash('Cylinder not found', 'error')
            return redirect(url_for('cylinders'))
        
        # Add to rental history if it was rented
        if cylinder['status'] == 'rented' and cylinder['date_borrowed']:
            history_id = str(uuid.uuid4())
            dispatch_date = datetime.fromisoformat(cylinder['date_borrowed'])
            return_date = datetime.now()
            rental_days = (return_date - dispatch_date).days
            
            cursor.execute('''
                INSERT INTO rental_history (id, customer_no, customer_name, cylinder_custom_id,
                                          cylinder_type, cylinder_size, dispatch_date, return_date, rental_days)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (history_id, cylinder['customer_no'], cylinder['customer_name'], 
                  cylinder['custom_id'], cylinder['type'], cylinder['size'],
                  dispatch_date, return_date, rental_days))
        
        # Update cylinder status back to available
        cursor.execute('''
            UPDATE cylinders 
            SET status = 'available',
                location = 'Warehouse',
                rented_to = NULL,
                customer_name = NULL,
                customer_email = NULL,
                customer_phone = NULL,
                customer_no = NULL,
                date_borrowed = NULL,
                date_returned = datetime('now')
            WHERE id = ?
        ''', (cylinder_id,))
        
        connection.commit()
        flash('Cylinder returned successfully!', 'success')
        
    except Exception as e:
        print(f"Error returning cylinder: {e}")
        flash('Error returning cylinder', 'error')
    finally:
        connection.close()
    
    return redirect(url_for('cylinders'))

# Data Import routes
@app.route('/import')
@login_required
def import_data():
    """Data import page"""
    return render_template('import_data.html')

@app.route('/import/access', methods=['GET', 'POST'])
@login_required
def import_access():
    """Import from Access database"""
    if request.method == 'POST':
        if 'access_file' not in request.files:
            flash('No file selected', 'error')
            return redirect(url_for('import_access'))
        
        file = request.files['access_file']
        if file.filename == '':
            flash('No file selected', 'error')
            return redirect(url_for('import_access'))
        
        if not file.filename.lower().endswith(('.mdb', '.accdb')):
            flash('Please upload a valid Access database file (.mdb or .accdb)', 'error')
            return redirect(url_for('import_access'))
        
        # Save the uploaded file
        import os
        upload_folder = 'uploads'
        if not os.path.exists(upload_folder):
            os.makedirs(upload_folder)
        
        filepath = os.path.join(upload_folder, file.filename)
        file.save(filepath)
        
        # Try to import the data
        try:
            from access_connector import AccessConnector
            connector = AccessConnector(filepath)
            tables = connector.get_tables()
            
            if not tables:
                flash('No tables found in the Access database', 'error')
                return redirect(url_for('import_access'))
            
            # Store file path in session for mapping page
            session['access_file_path'] = filepath
            session['access_tables'] = tables
            
            return render_template('import_mapping.html', tables=tables, filepath=filepath)
            
        except Exception as e:
            flash(f'Error reading Access database: {str(e)}', 'error')
            return redirect(url_for('import_access'))
    
    return render_template('import_access.html')

@app.route('/import/process', methods=['POST'])
@login_required
def process_import():
    """Process the import with field mapping"""
    if 'access_file_path' not in session:
        flash('No Access file found in session', 'error')
        return redirect(url_for('import_access'))
    
    filepath = session['access_file_path']
    table_name = request.form.get('table_name')
    import_type = request.form.get('import_type')  # customers or cylinders
    
    if not table_name or not import_type:
        flash('Table name and import type are required', 'error')
        return redirect(url_for('import_access'))
    
    try:
        from access_connector import AccessConnector
        connector = AccessConnector(filepath)
        data = connector.get_table_data(table_name)
        
        if not data:
            flash('No data found in the selected table', 'error')
            return redirect(url_for('import_access'))
        
        # Get field mappings from form
        field_mappings = {}
        for key in request.form:
            if key.startswith('mapping_'):
                source_field = key.replace('mapping_', '')
                target_field = request.form[key]
                if target_field:
                    field_mappings[source_field] = target_field
        
        # Import the data
        imported_count = 0
        connection = get_db_connection()
        if not connection:
            flash('Database connection error', 'error')
            return redirect(url_for('import_access'))
        
        try:
            cursor = connection.cursor()
            
            for row in data:
                try:
                    if import_type == 'customers':
                        imported_count += import_customer_row(cursor, row, field_mappings)
                    elif import_type == 'cylinders':
                        imported_count += import_cylinder_row(cursor, row, field_mappings)
                except Exception as e:
                    print(f"Error importing row: {e}")
                    continue
            
            connection.commit()
            flash(f'Successfully imported {imported_count} {import_type}!', 'success')
            
        except Exception as e:
            connection.rollback()
            flash(f'Error during import: {str(e)}', 'error')
        finally:
            connection.close()
            
        # Clean up session
        session.pop('access_file_path', None)
        session.pop('access_tables', None)
        
        return redirect(url_for('customers' if import_type == 'customers' else 'cylinders'))
        
    except Exception as e:
        flash(f'Error processing import: {str(e)}', 'error')
        return redirect(url_for('import_access'))

def import_customer_row(cursor, row, field_mappings):
    """Import a single customer row"""
    try:
        customer_data = {}
        for source_field, target_field in field_mappings.items():
            if source_field in row and row[source_field] is not None:
                customer_data[target_field] = str(row[source_field]).strip()
        
        if 'customer_name' not in customer_data or not customer_data['customer_name']:
            return 0  # Skip rows without customer name
        
        customer_id = str(uuid.uuid4())
        
        cursor.execute('''
            INSERT OR IGNORE INTO customers (id, customer_no, customer_name, customer_email, customer_phone,
                                   customer_address, customer_city, customer_state, customer_apgst, customer_cst)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            customer_id,
            customer_data.get('customer_no', ''),
            customer_data.get('customer_name', ''),
            customer_data.get('customer_email', ''),
            customer_data.get('customer_phone', ''),
            customer_data.get('customer_address', ''),
            customer_data.get('customer_city', ''),
            customer_data.get('customer_state', ''),
            customer_data.get('customer_apgst', ''),
            customer_data.get('customer_cst', '')
        ))
        
        return 1
    except Exception as e:
        print(f"Error importing customer row: {e}")
        return 0

def import_cylinder_row(cursor, row, field_mappings):
    """Import a single cylinder row"""
    try:
        cylinder_data = {}
        for source_field, target_field in field_mappings.items():
            if source_field in row and row[source_field] is not None:
                cylinder_data[target_field] = str(row[source_field]).strip()
        
        if 'custom_id' not in cylinder_data or not cylinder_data['custom_id']:
            return 0  # Skip rows without custom_id
        
        cylinder_id = str(uuid.uuid4())
        
        cursor.execute('''
            INSERT OR IGNORE INTO cylinders (id, custom_id, serial_number, type, size, status, location,
                                   pressure, notes, rented_to, customer_name, date_borrowed)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            cylinder_id,
            cylinder_data.get('custom_id', ''),
            cylinder_data.get('serial_number', ''),
            cylinder_data.get('type', 'Medical Oxygen'),
            cylinder_data.get('size', '40L'),
            cylinder_data.get('status', 'available'),
            cylinder_data.get('location', 'Warehouse'),
            cylinder_data.get('pressure', ''),
            cylinder_data.get('notes', ''),
            cylinder_data.get('rented_to', ''),
            cylinder_data.get('customer_name', ''),
            cylinder_data.get('date_borrowed', None)
        ))
        
        return 1
    except Exception as e:
        print(f"Error importing cylinder row: {e}")
        return 0

# Rental History and Reports routes
@app.route('/rental_history')
@login_required
def rental_history():
    """Rental history page"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 25, type=int)
    offset = (page - 1) * per_page
    
    connection = get_db_connection()
    if not connection:
        flash('Database connection error', 'error')
        return render_template('rental_history.html', history=[], pagination={'total': 0, 'per_page': per_page, 'page': page, 'has_next': False, 'has_prev': False})
    
    try:
        cursor = connection.cursor()
        
        # Get rental history with pagination
        cursor.execute('''
            SELECT * FROM rental_history 
            ORDER BY return_date DESC, dispatch_date DESC
            LIMIT ? OFFSET ?
        ''', (per_page, offset))
        history_list = cursor.fetchall()
        
        # Get total count
        cursor.execute('SELECT COUNT(*) as total FROM rental_history')
        result = cursor.fetchone()
        total = result[0] if result else 0
        
        # Create pagination info
        pagination = {
            'total': total,
            'per_page': per_page,
            'page': page,
            'has_next': offset + per_page < total,
            'has_prev': page > 1,
            'next_num': page + 1,
            'prev_num': page - 1
        }
        
        return render_template('rental_history.html', history=history_list, pagination=pagination)
        
    except Exception as e:
        print(f"Error getting rental history: {e}")
        return render_template('rental_history.html', history=[], pagination={'total': 0, 'per_page': per_page, 'page': page, 'has_next': False, 'has_prev': False})
    finally:
        connection.close()

if __name__ == '__main__':
    # Initialize database on startup
    init_sqlite_database()
    app.run(host='0.0.0.0', port=5000, debug=True)