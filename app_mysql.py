"""
MySQL Flask app for Varasai Oxygen Cylinder Tracker
Clean implementation using MySQL database with PyMySQL
"""
import os
import pymysql
from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import json

app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "your-secret-key-here")

# MySQL configuration
MYSQL_CONFIG = {
    'host': os.environ.get('MYSQL_HOST', 'localhost'),
    'user': os.environ.get('MYSQL_USER', 'root'),
    'password': os.environ.get('MYSQL_PASSWORD', ''),
    'database': os.environ.get('MYSQL_DATABASE', 'oxygen_tracker'),
    'charset': 'utf8mb4',
    'cursorclass': pymysql.cursors.DictCursor
}

def get_db_connection():
    """Get MySQL database connection"""
    try:
        connection = pymysql.connect(**MYSQL_CONFIG)
        return connection
    except Exception as e:
        print(f"Database connection error: {e}")
        return None

def init_mysql_database():
    """Initialize MySQL database with tables"""
    connection = get_db_connection()
    if not connection:
        print("Failed to connect to MySQL database")
        return False
        
    try:
        cursor = connection.cursor()
        
        # Create database if it doesn't exist
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {MYSQL_CONFIG['database']}")
        cursor.execute(f"USE {MYSQL_CONFIG['database']}")
        
        # Create customers table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS customers (
                id VARCHAR(50) PRIMARY KEY,
                customer_no VARCHAR(50) UNIQUE,
                customer_name VARCHAR(200) NOT NULL,
                customer_email VARCHAR(200),
                customer_phone VARCHAR(50),
                customer_address TEXT,
                customer_city VARCHAR(100),
                customer_state VARCHAR(100),
                customer_apgst VARCHAR(50),
                customer_cst VARCHAR(50),
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                INDEX idx_customer_no (customer_no),
                INDEX idx_customer_name (customer_name)
            )
        ''')
        
        # Create cylinders table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS cylinders (
                id VARCHAR(50) PRIMARY KEY,
                custom_id VARCHAR(50) UNIQUE,
                serial_number VARCHAR(100),
                type VARCHAR(50) DEFAULT 'Medical Oxygen',
                size VARCHAR(20) DEFAULT '40L',
                status VARCHAR(20) DEFAULT 'available',
                location VARCHAR(200) DEFAULT 'Warehouse',
                pressure VARCHAR(50),
                last_inspection VARCHAR(50),
                next_inspection VARCHAR(50),
                notes TEXT,
                rented_to VARCHAR(50),
                customer_name VARCHAR(200),
                customer_email VARCHAR(200),
                customer_phone VARCHAR(50),
                customer_no VARCHAR(50),
                date_borrowed DATETIME,
                date_returned DATETIME,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                INDEX idx_custom_id (custom_id),
                INDEX idx_status (status),
                INDEX idx_customer_no (customer_no)
            )
        ''')
        
        # Create rental_history table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS rental_history (
                id VARCHAR(50) PRIMARY KEY,
                customer_no VARCHAR(50),
                customer_name VARCHAR(200),
                cylinder_custom_id VARCHAR(50),
                cylinder_type VARCHAR(50),
                cylinder_size VARCHAR(20),
                dispatch_date DATETIME,
                return_date DATETIME,
                rental_days INT DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_customer_no (customer_no),
                INDEX idx_cylinder_id (cylinder_custom_id),
                INDEX idx_dispatch_date (dispatch_date)
            )
        ''')
        
        connection.commit()
        print("✓ MySQL database tables created successfully!")
        return True
        
    except Exception as e:
        print(f"Error initializing MySQL database: {e}")
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
    """Authenticate user credentials"""
    users = load_users()
    user = users.get(username)
    if user and check_password_hash(user['password_hash'], password):
        return user
    return None

# Authentication decorator
def login_required(f):
    """Decorator to require login for routes"""
    from functools import wraps
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
        return render_template('login.html')
    
    try:
        cursor = connection.cursor()
        
        # Get basic statistics
        cursor.execute('SELECT COUNT(*) as count FROM customers')
        customer_count = cursor.fetchone()['count']
        
        cursor.execute('SELECT COUNT(*) as count FROM cylinders')
        cylinder_count = cursor.fetchone()['count']
        
        cursor.execute("SELECT COUNT(*) as count FROM cylinders WHERE status = 'rented'")
        rented_count = cursor.fetchone()['count']
        
        available_count = cylinder_count - rented_count
        
        return render_template('index.html', 
                             customer_count=customer_count,
                             cylinder_count=cylinder_count,
                             rented_count=rented_count,
                             available_count=available_count)
                             
    except Exception as e:
        flash(f'Error loading dashboard: {e}', 'error')
        return render_template('index.html', 
                             customer_count=0,
                             cylinder_count=0,
                             rented_count=0,
                             available_count=0)
    finally:
        connection.close()

@app.route('/customers')
@login_required
def customers():
    """Customers page"""
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    per_page = 25
    offset = (page - 1) * per_page
    
    connection = get_db_connection()
    if not connection:
        flash('Database connection error', 'error')
        return render_template('customers.html', customers=[], total=0, page=1, total_pages=1, has_prev=False, has_next=False)
    
    try:
        cursor = connection.cursor()
        
        # Build query with search
        if search:
            query = '''
                SELECT * FROM customers 
                WHERE customer_name LIKE %s OR customer_no LIKE %s OR customer_phone LIKE %s
                ORDER BY customer_name
                LIMIT %s OFFSET %s
            '''
            search_term = f'%{search}%'
            cursor.execute(query, (search_term, search_term, search_term, per_page, offset))
            customers = cursor.fetchall()
            
            cursor.execute('''
                SELECT COUNT(*) as total FROM customers 
                WHERE customer_name LIKE %s OR customer_no LIKE %s OR customer_phone LIKE %s
            ''', (search_term, search_term, search_term))
            total = cursor.fetchone()['total']
        else:
            cursor.execute('SELECT * FROM customers ORDER BY customer_name LIMIT %s OFFSET %s', (per_page, offset))
            customers = cursor.fetchall()
            
            cursor.execute('SELECT COUNT(*) as total FROM customers')
            total = cursor.fetchone()['total']
        
        # Calculate pagination
        total_pages = (total + per_page - 1) // per_page
        has_prev = page > 1
        has_next = page < total_pages
        
        return render_template('customers.html',
                             customers=customers,
                             page=page,
                             total_pages=total_pages,
                             has_prev=has_prev,
                             has_next=has_next,
                             search=search,
                             total=total)
                             
    except Exception as e:
        flash(f'Error loading customers: {e}', 'error')
        return render_template('customers.html', customers=[], total=0, page=1, total_pages=1, has_prev=False, has_next=False)
    finally:
        connection.close()

@app.route('/cylinders')
@login_required
def cylinders():
    """Cylinders page"""
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    status_filter = request.args.get('status', '')
    per_page = 25
    offset = (page - 1) * per_page
    
    connection = get_db_connection()
    if not connection:
        flash('Database connection error', 'error')
        return render_template('cylinders.html', cylinders=[], total=0, page=1, total_pages=1, has_prev=False, has_next=False)
    
    try:
        cursor = connection.cursor()
        
        # Build query with filters
        where_clauses = []
        params = []
        
        if search:
            where_clauses.append('(custom_id LIKE %s OR serial_number LIKE %s OR customer_name LIKE %s)')
            search_term = f'%{search}%'
            params.extend([search_term, search_term, search_term])
        
        if status_filter:
            where_clauses.append('status = %s')
            params.append(status_filter)
        
        where_sql = ' AND '.join(where_clauses) if where_clauses else '1=1'
        
        query = f'''
            SELECT * FROM cylinders 
            WHERE {where_sql}
            ORDER BY 
                CASE WHEN status = 'rented' THEN 0 ELSE 1 END,
                custom_id
            LIMIT %s OFFSET %s
        '''
        params.extend([per_page, offset])
        cursor.execute(query, params)
        cylinders = cursor.fetchall()
        
        # Count total
        count_query = f'SELECT COUNT(*) as total FROM cylinders WHERE {where_sql}'
        count_params = params[:-2]  # Remove LIMIT and OFFSET
        cursor.execute(count_query, count_params)
        total = cursor.fetchone()['total']
        
        # Calculate pagination
        total_pages = (total + per_page - 1) // per_page
        has_prev = page > 1
        has_next = page < total_pages
        
        return render_template('cylinders.html',
                             cylinders=cylinders,
                             page=page,
                             total_pages=total_pages,
                             has_prev=has_prev,
                             has_next=has_next,
                             search=search,
                             status_filter=status_filter,
                             total=total)
                             
    except Exception as e:
        flash(f'Error loading cylinders: {e}', 'error')
        return render_template('cylinders.html', cylinders=[], total=0, page=1, total_pages=1, has_prev=False, has_next=False)
    finally:
        connection.close()

# Initialize database on startup
if __name__ == '__main__':
    init_mysql_database()
    app.run(debug=True, host='0.0.0.0', port=5000)
else:
    # Initialize when imported
    init_mysql_database()