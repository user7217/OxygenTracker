"""
Simple SQLite Flask app for Varasai Oxygen Cylinder Tracker
"""
import os
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import json

app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "your-secret-key-here")

# Database helper functions
def get_db_connection():
    """Get SQLite database connection"""
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_database():
    """Initialize database with tables if they don't exist"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
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
            created_at DATETIME,
            updated_at DATETIME
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
            created_at DATETIME,
            updated_at DATETIME
        )
    ''')
    
    conn.commit()
    conn.close()

# Initialize database
init_database()

# User management
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
    conn = get_db_connection()
    
    # Get basic statistics
    customer_count = conn.execute('SELECT COUNT(*) as count FROM customers').fetchone()['count']
    cylinder_count = conn.execute('SELECT COUNT(*) as count FROM cylinders').fetchone()['count']
    rented_count = conn.execute("SELECT COUNT(*) as count FROM cylinders WHERE status = 'rented'").fetchone()['count']
    available_count = cylinder_count - rented_count
    
    conn.close()
    
    return render_template('index.html', 
                         customer_count=customer_count,
                         cylinder_count=cylinder_count,
                         rented_count=rented_count,
                         available_count=available_count)

@app.route('/customers')
@login_required
def customers():
    """Customers page"""
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    per_page = 25
    offset = (page - 1) * per_page
    
    conn = get_db_connection()
    
    # Build query with search
    if search:
        query = '''
            SELECT * FROM customers 
            WHERE customer_name LIKE ? OR customer_no LIKE ? OR customer_phone LIKE ?
            ORDER BY customer_name
            LIMIT ? OFFSET ?
        '''
        search_term = f'%{search}%'
        customers = conn.execute(query, (search_term, search_term, search_term, per_page, offset)).fetchall()
        
        count_query = '''
            SELECT COUNT(*) as total FROM customers 
            WHERE customer_name LIKE ? OR customer_no LIKE ? OR customer_phone LIKE ?
        '''
        total = conn.execute(count_query, (search_term, search_term, search_term)).fetchone()['total']
    else:
        query = 'SELECT * FROM customers ORDER BY customer_name LIMIT ? OFFSET ?'
        customers = conn.execute(query, (per_page, offset)).fetchall()
        total = conn.execute('SELECT COUNT(*) as total FROM customers').fetchone()['total']
    
    conn.close()
    
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

@app.route('/cylinders')
@login_required
def cylinders():
    """Cylinders page"""
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    status_filter = request.args.get('status', '')
    per_page = 25
    offset = (page - 1) * per_page
    
    conn = get_db_connection()
    
    # Build query with filters
    where_clauses = []
    params = []
    
    if search:
        where_clauses.append('(custom_id LIKE ? OR serial_number LIKE ? OR customer_name LIKE ?)')
        search_term = f'%{search}%'
        params.extend([search_term, search_term, search_term])
    
    if status_filter:
        where_clauses.append('status = ?')
        params.append(status_filter)
    
    where_sql = ' AND '.join(where_clauses) if where_clauses else '1=1'
    
    query = f'''
        SELECT * FROM cylinders 
        WHERE {where_sql}
        ORDER BY 
            CASE WHEN status = 'rented' THEN 0 ELSE 1 END,
            custom_id
        LIMIT ? OFFSET ?
    '''
    params.extend([per_page, offset])
    cylinders = conn.execute(query, params).fetchall()
    
    # Count total
    count_query = f'SELECT COUNT(*) as total FROM cylinders WHERE {where_sql}'
    count_params = params[:-2]  # Remove LIMIT and OFFSET
    total = conn.execute(count_query, count_params).fetchone()['total']
    
    conn.close()
    
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

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)