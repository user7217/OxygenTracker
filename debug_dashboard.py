
import sys
import os

def test_dashboard_route():
    print("=== Testing Dashboard Route ===")
    try:
        from app import app
        from models import Customer, Cylinder
        
        with app.app_context():
            print("✓ App context created")
            
            customer_model = Customer()
            cylinder_model = Cylinder()
            print("✓ Models imported")
            
            customers = customer_model.get_all()
            cylinders = cylinder_model.get_all()
            print(f"✓ Loaded {len(customers)} customers, {len(cylinders)} cylinders")
            
            available_cylinders = len([c for c in cylinders if c.get('status', '').lower() == 'available'])
            rented_cylinders = len([c for c in cylinders if c.get('status', '').lower() == 'rented'])
            maintenance_cylinders = len([c for c in cylinders if c.get('status', '').lower() == 'maintenance'])
            print(f"✓ Statistics: {available_cylinders} available, {rented_cylinders} rented, {maintenance_cylinders} maintenance")
            
            total_cylinders = len(cylinders)
            utilization_rate = round((rented_cylinders / total_cylinders * 100) if total_cylinders > 0 else 0)
            print(f"✓ Utilization rate: {utilization_rate}%")
            
            print("✓ Dashboard logic test passed")
            
    except Exception as e:
        print(f"✗ Dashboard test failed: {e}")
        import traceback
        traceback.print_exc()

def test_template_rendering():
    print("\n=== Testing Template Rendering ===")
    try:
        from app import app
        from flask import render_template
        
        with app.app_context():
            stats = {
                'total_customers': 0,
                'total_cylinders': 0,
                'available_cylinders': 0,
                'rented_cylinders': 0,
                'maintenance_cylinders': 0,
                'utilization_rate': 0,
                'efficiency_score': 5,
                'avg_rental_days': 15,
                'days_active': 1,
                'top_customer_count': 0,
                'growth_rate': 10
            }
            
            html = render_template('index.html', stats=stats)
            print("✓ Template rendered successfully")
            print(f"✓ HTML length: {len(html)} characters")
            
    except Exception as e:
        print(f"✗ Template rendering failed: {e}")
        import traceback
        traceback.print_exc()

def test_json_data_access():
    print("\n=== Testing JSON Data Access ===")
    try:
        import json
        
        if os.path.exists('data/customers.json'):
            with open('data/customers.json', 'r') as f:
                customers = json.load(f)
            print(f"✓ customers.json loaded: {len(customers)} records")
        else:
            print("! customers.json doesn't exist (will be created)")
            
        if os.path.exists('data/cylinders.json'):
            with open('data/cylinders.json', 'r') as f:
                cylinders = json.load(f)
            print(f"✓ cylinders.json loaded: {len(cylinders)} records")
        else:
            print("! cylinders.json doesn't exist (will be created)")
            
    except Exception as e:
        print(f"✗ JSON data access failed: {e}")

def test_imports():
    print("\n=== Testing Specific Imports ===")
    modules_to_test = [
        'datetime',
        'random',
        'json',
        'os'
    ]
    
    for module in modules_to_test:
        try:
            __import__(module)
            print(f"✓ {module}")
        except ImportError as e:
            print(f"✗ {module}: {e}")

def main():
    print("=== Dashboard Debug Tool for PythonAnywhere ===")
    print("Run this to identify why dashboard isn't loading\n")
    
    test_imports()
    test_json_data_access()
    test_dashboard_route()
    test_template_rendering()
    
    print("\n=== Recommendations ===")
    print("1. If all tests pass, check PythonAnywhere error logs")
    print("2. If template rendering fails, check templates/index.html")
    print("3. If data access fails, check data directory permissions")
    print("4. If imports fail, install missing packages")

if __name__ == '__main__':
    main()