#!/bin/bash

# Fly.io Deployment Script for Oxygen Cylinder Tracker
# This script automates the complete deployment process including database setup and data migration

set -e  # Exit on any error

echo "🚀 Starting Fly.io deployment for Oxygen Cylinder Tracker..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}✓${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

# Check if flyctl is installed
if ! command -v flyctl &> /dev/null; then
    print_error "flyctl is not installed. Please install it first:"
    echo "  curl -L https://fly.io/install.sh | sh"
    exit 1
fi

# Check if user is logged in to Fly.io
if ! flyctl auth whoami &> /dev/null; then
    print_error "You are not logged in to Fly.io. Please run: flyctl auth login"
    exit 1
fi

print_status "flyctl is installed and you are logged in"

# Get app name from user
read -p "Enter your Fly.io app name (e.g., my-oxygen-tracker): " APP_NAME

if [ -z "$APP_NAME" ]; then
    print_error "App name cannot be empty"
    exit 1
fi

# Create fly.toml configuration
print_status "Creating fly.toml configuration..."
cat > fly.toml << EOF
app = "${APP_NAME}"
primary_region = "iad"

[build]

[env]
  PORT = "8080"
  FLASK_ENV = "production"

[http_service]
  internal_port = 8080
  force_https = true
  auto_stop_machines = true
  auto_start_machines = true
  min_machines_running = 0
  processes = ["app"]

[[http_service.checks]]
  interval = "10s"
  grace_period = "5s"
  method = "GET"
  path = "/health"
  protocol = "http"
  timeout = "2s"
  tls_skip_verify = false

[[vm]]
  cpu_kind = "shared"
  cpus = 1
  memory_mb = 512
EOF

# Create Dockerfile optimized for production
print_status "Creating production Dockerfile..."
cat > Dockerfile << EOF
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    gcc \\
    libpq-dev \\
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY pyproject.toml uv.lock ./

# Install uv for faster package management
RUN pip install uv

# Install Python dependencies
RUN uv pip install --system -r pyproject.toml

# Copy application code
COPY . .

# Create non-root user
RUN useradd --create-home --shell /bin/bash app && chown -R app:app /app
USER app

# Health check endpoint
COPY health_check.py .

EXPOSE 8080

CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "2", "--timeout", "120", "main:app"]
EOF

# Create health check endpoint
print_status "Creating health check endpoint..."
cat > health_check.py << EOF
# Health check endpoint for Fly.io
from flask import jsonify
import sys
import os

# Add to main.py routes
def health_check():
    return jsonify({"status": "healthy", "service": "oxygen-tracker"}), 200
EOF

# Add health check to main.py if not exists
if ! grep -q "/health" main.py; then
    print_status "Adding health check endpoint to main.py..."
    cat >> main.py << EOF

# Health check endpoint for Fly.io monitoring
@app.route('/health')
def health():
    return {"status": "healthy", "service": "oxygen-tracker"}, 200
EOF
fi

# Create data migration script
print_status "Creating data migration script..."
cat > migrate_data.py << EOF
#!/usr/bin/env python3
"""
Data migration script for importing existing JSON data to PostgreSQL
Run this after deploying to import your existing data
"""

import os
import json
import sys
from datetime import datetime
import uuid
from db_models import get_db_session, Customer, Cylinder, RentalHistory

def migrate_json_data():
    """Migrate data from JSON files to PostgreSQL"""
    db = get_db_session()
    
    # Check if data directory exists
    if not os.path.exists('data'):
        print("❌ No data directory found. Creating sample structure...")
        os.makedirs('data', exist_ok=True)
        return
    
    # Migrate customers
    customers_file = 'data/customers.json'
    if os.path.exists(customers_file):
        print("📋 Migrating customers...")
        with open(customers_file, 'r') as f:
            customers_data = json.load(f)
        
        for customer_data in customers_data:
            # Check if customer already exists
            existing = db.query(Customer).filter(Customer.customer_no == customer_data.get('customer_no')).first()
            if not existing:
                customer = Customer(
                    id=customer_data.get('id', str(uuid.uuid4())),
                    customer_no=customer_data.get('customer_no', ''),
                    customer_name=customer_data.get('customer_name', customer_data.get('name', '')),
                    customer_email=customer_data.get('customer_email', customer_data.get('email', '')),
                    customer_phone=customer_data.get('customer_phone', customer_data.get('phone', '')),
                    customer_address=customer_data.get('customer_address', customer_data.get('address', '')),
                    customer_city=customer_data.get('customer_city', customer_data.get('city', '')),
                    customer_state=customer_data.get('customer_state', customer_data.get('state', '')),
                    customer_apgst=customer_data.get('customer_apgst', ''),
                    customer_cst=customer_data.get('customer_cst', ''),
                    created_at=datetime.utcnow()
                )
                db.add(customer)
        
        db.commit()
        print(f"✅ Migrated {len(customers_data)} customers")
    
    # Migrate cylinders
    cylinders_file = 'data/cylinders.json'
    if os.path.exists(cylinders_file):
        print("🛢️ Migrating cylinders...")
        with open(cylinders_file, 'r') as f:
            cylinders_data = json.load(f)
        
        for cylinder_data in cylinders_data:
            # Check if cylinder already exists
            existing = db.query(Cylinder).filter(Cylinder.custom_id == cylinder_data.get('custom_id')).first()
            if not existing:
                cylinder = Cylinder(
                    id=cylinder_data.get('id', str(uuid.uuid4())),
                    custom_id=cylinder_data.get('custom_id', ''),
                    serial_number=cylinder_data.get('serial_number', ''),
                    type=cylinder_data.get('type', 'Medical Oxygen'),
                    size=cylinder_data.get('size', '40L'),
                    status=cylinder_data.get('status', 'available'),
                    location=cylinder_data.get('location', 'Warehouse'),
                    rented_to=cylinder_data.get('rented_to'),
                    customer_name=cylinder_data.get('customer_name', ''),
                    customer_email=cylinder_data.get('customer_email', ''),
                    customer_phone=cylinder_data.get('customer_phone', ''),
                    customer_no=cylinder_data.get('customer_no', ''),
                    customer_city=cylinder_data.get('customer_city', ''),
                    customer_state=cylinder_data.get('customer_state', ''),
                    date_borrowed=datetime.fromisoformat(cylinder_data['date_borrowed'].replace('Z', '+00:00')) if cylinder_data.get('date_borrowed') else None,
                    rental_date=datetime.fromisoformat(cylinder_data['rental_date'].replace('Z', '+00:00')) if cylinder_data.get('rental_date') else None,
                    date_returned=datetime.fromisoformat(cylinder_data['date_returned'].replace('Z', '+00:00')) if cylinder_data.get('date_returned') else None,
                    created_at=datetime.utcnow()
                )
                db.add(cylinder)
        
        db.commit()
        print(f"✅ Migrated {len(cylinders_data)} cylinders")
    
    # Migrate rental history if exists
    rental_file = 'data/rental_history.json'
    if os.path.exists(rental_file):
        print("📚 Migrating rental history...")
        with open(rental_file, 'r') as f:
            rental_data = json.load(f)
        
        for record in rental_data:
            existing = db.query(RentalHistory).filter(
                RentalHistory.cylinder_id == record.get('cylinder_id'),
                RentalHistory.customer_id == record.get('customer_id')
            ).first()
            
            if not existing:
                history = RentalHistory(
                    id=str(uuid.uuid4()),
                    cylinder_id=record.get('cylinder_id'),
                    customer_id=record.get('customer_id'),
                    customer_name=record.get('customer_name', ''),
                    customer_no=record.get('customer_no', ''),
                    cylinder_custom_id=record.get('cylinder_custom_id', ''),
                    rental_date=datetime.fromisoformat(record['rental_date'].replace('Z', '+00:00')) if record.get('rental_date') else datetime.utcnow(),
                    return_date=datetime.fromisoformat(record['return_date'].replace('Z', '+00:00')) if record.get('return_date') else None,
                    created_at=datetime.utcnow()
                )
                db.add(history)
        
        db.commit()
        print(f"✅ Migrated {len(rental_data)} rental history records")
    
    db.close()
    print("🎉 Data migration completed successfully!")

if __name__ == "__main__":
    migrate_json_data()
EOF

# Create deployment preparation script
print_status "Creating deployment preparation..."
cat > prepare_deploy.py << EOF
#!/usr/bin/env python3
"""
Prepare application for production deployment
"""

import os
import shutil

def prepare_deployment():
    """Prepare the application for deployment"""
    
    # Create production wsgi.py if it doesn't exist
    if not os.path.exists('wsgi.py'):
        with open('wsgi.py', 'w') as f:
            f.write('''
from main import app

if __name__ == "__main__":
    app.run()
''')
    
    # Ensure required directories exist
    os.makedirs('data', exist_ok=True)
    os.makedirs('backups', exist_ok=True)
    os.makedirs('templates', exist_ok=True)
    os.makedirs('static', exist_ok=True)
    
    # Create .flyignore to exclude unnecessary files
    with open('.flyignore', 'w') as f:
        f.write('''
.git
.gitignore
*.md
*.log
__pycache__
.pytest_cache
.coverage
.env
*.pyc
*.pyo
*.pyd
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg
MANIFEST
backups/*.json
data/*.json.backup
*.db
''')
    
    print("✅ Deployment preparation completed")

if __name__ == "__main__":
    prepare_deployment()
EOF

print_status "Running deployment preparation..."
python3 prepare_deploy.py

# Initialize Fly.io app
print_status "Initializing Fly.io application..."
flyctl apps create $APP_NAME --yes || print_warning "App may already exist, continuing..."

# Create and attach PostgreSQL database
print_status "Creating PostgreSQL database..."
flyctl postgres create --name "${APP_NAME}-db" --region iad --initial-cluster-size 1 --vm-size shared-cpu-1x --volume-size 1 || print_warning "Database may already exist, continuing..."

print_status "Attaching database to application..."
flyctl postgres attach "${APP_NAME}-db" --app "$APP_NAME" || print_warning "Database may already be attached, continuing..."

# Set additional environment variables
print_status "Setting environment variables..."
flyctl secrets set FLASK_SECRET_KEY="$(openssl rand -hex 32)" --app "$APP_NAME"
flyctl secrets set SESSION_SECRET="$(openssl rand -hex 32)" --app "$APP_NAME"

# Deploy the application
print_status "Deploying application to Fly.io..."
flyctl deploy --app "$APP_NAME" --yes

# Wait for deployment to complete
print_status "Waiting for deployment to complete..."
sleep 10

# Run data migration
print_warning "To migrate your existing JSON data, run the following commands:"
echo ""
echo "  # Copy your data files to the deployed app"
echo "  flyctl ssh console --app $APP_NAME"
echo "  # Then in the SSH session:"
echo "  python3 migrate_data.py"
echo ""

# Display final information
print_status "Deployment completed successfully! 🎉"
echo ""
echo "🌐 Your application is available at: https://${APP_NAME}.fly.dev"
echo "📊 Monitor your app: flyctl status --app $APP_NAME"
echo "📋 View logs: flyctl logs --app $APP_NAME"
echo "🔧 SSH into app: flyctl ssh console --app $APP_NAME"
echo ""
echo "📁 To import your existing data:"
echo "   1. Copy your data/ directory to the deployed app"
echo "   2. SSH into the app: flyctl ssh console --app $APP_NAME"
echo "   3. Run: python3 migrate_data.py"
echo ""
print_status "Don't forget to set up your admin user after first login!"

# Update replit.md with deployment information
cat >> replit.md << EOF

## Fly.io Deployment
- App Name: ${APP_NAME}
- URL: https://${APP_NAME}.fly.dev
- Database: ${APP_NAME}-db (PostgreSQL)
- Deployment Date: $(date)
- Migration Script: migrate_data.py available for JSON data import
EOF

print_status "Deployment information added to replit.md"