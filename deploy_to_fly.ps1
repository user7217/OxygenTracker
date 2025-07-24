# Fly.io Deployment Script for Oxygen Cylinder Tracker (Windows PowerShell)
# This script automates the complete deployment process including database setup and data migration

param(
    [string]$AppName = ""
)

# Enable strict mode
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

Write-Host "🚀 Starting Fly.io deployment for Oxygen Cylinder Tracker..." -ForegroundColor Green

# Function to print colored output
function Write-Status {
    param([string]$Message)
    Write-Host "✓ $Message" -ForegroundColor Green
}

function Write-Warning {
    param([string]$Message)
    Write-Host "⚠ $Message" -ForegroundColor Yellow
}

function Write-Error {
    param([string]$Message)
    Write-Host "✗ $Message" -ForegroundColor Red
}

# Check if flyctl is installed
try {
    $null = Get-Command flyctl -ErrorAction Stop
    Write-Status "flyctl is installed"
} catch {
    Write-Error "flyctl is not installed. Please install it first:"
    Write-Host "  Visit: https://fly.io/docs/flyctl/install/" -ForegroundColor Cyan
    Write-Host "  Or run: iwr https://fly.io/install.ps1 -useb | iex" -ForegroundColor Cyan
    exit 1
}

# Check if user is logged in to Fly.io
try {
    $null = flyctl auth whoami 2>$null
    Write-Status "You are logged in to Fly.io"
} catch {
    Write-Error "You are not logged in to Fly.io. Please run: flyctl auth login"
    exit 1
}

# Get app name from user if not provided
if (-not $AppName) {
    $AppName = Read-Host "Enter your Fly.io app name (e.g., my-oxygen-tracker)"
}

if (-not $AppName) {
    Write-Error "App name cannot be empty"
    exit 1
}

# Create fly.toml configuration
Write-Status "Creating fly.toml configuration..."
$flyTomlContent = @"
app = "$AppName"
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
"@

$flyTomlContent | Out-File -FilePath "fly.toml" -Encoding UTF8

# Create Dockerfile optimized for production
Write-Status "Creating production Dockerfile..."
$dockerfileContent = @"
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
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
"@

$dockerfileContent | Out-File -FilePath "Dockerfile" -Encoding UTF8

# Create health check endpoint
Write-Status "Creating health check endpoint..."
$healthCheckContent = @"
# Health check endpoint for Fly.io
from flask import jsonify
import sys
import os

# Add to main.py routes
def health_check():
    return jsonify({"status": "healthy", "service": "oxygen-tracker"}), 200
"@

$healthCheckContent | Out-File -FilePath "health_check.py" -Encoding UTF8

# Add health check to main.py if not exists
$mainPyContent = Get-Content "main.py" -Raw -ErrorAction SilentlyContinue
if ($mainPyContent -and $mainPyContent -notmatch "/health") {
    Write-Status "Adding health check endpoint to main.py..."
    $healthEndpoint = @"

# Health check endpoint for Fly.io monitoring
@app.route('/health')
def health():
    return {"status": "healthy", "service": "oxygen-tracker"}, 200
"@
    Add-Content -Path "main.py" -Value $healthEndpoint
}

# Create data migration script
Write-Status "Creating data migration script..."
$migrationScript = @"
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
"@

$migrationScript | Out-File -FilePath "migrate_data.py" -Encoding UTF8

# Create deployment preparation
Write-Status "Creating deployment preparation..."

# Ensure required directories exist
@("data", "backups", "templates", "static") | ForEach-Object {
    if (-not (Test-Path $_)) {
        New-Item -ItemType Directory -Path $_ -Force | Out-Null
    }
}

# Create wsgi.py if it doesn't exist
if (-not (Test-Path "wsgi.py")) {
    $wsgiContent = @"
from main import app

if __name__ == "__main__":
    app.run()
"@
    $wsgiContent | Out-File -FilePath "wsgi.py" -Encoding UTF8
}

# Create .flyignore
$flyIgnoreContent = @"
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
"@

$flyIgnoreContent | Out-File -FilePath ".flyignore" -Encoding UTF8

# Initialize Fly.io app
Write-Status "Initializing Fly.io application..."
try {
    flyctl apps create $AppName --yes 2>$null
} catch {
    Write-Warning "App may already exist, continuing..."
}

# Create and attach PostgreSQL database
Write-Status "Creating PostgreSQL database..."
try {
    flyctl postgres create --name "$AppName-db" --region iad --initial-cluster-size 1 --vm-size shared-cpu-1x --volume-size 1 2>$null
} catch {
    Write-Warning "Database may already exist, continuing..."
}

Write-Status "Attaching database to application..."
try {
    flyctl postgres attach "$AppName-db" --app $AppName 2>$null
} catch {
    Write-Warning "Database may already be attached, continuing..."
}

# Generate random secrets
$FlaskSecret = -join ((1..32) | ForEach {'{0:X}' -f (Get-Random -Max 16)})
$SessionSecret = -join ((1..32) | ForEach {'{0:X}' -f (Get-Random -Max 16)})

# Set environment variables
Write-Status "Setting environment variables..."
flyctl secrets set FLASK_SECRET_KEY="$FlaskSecret" --app $AppName
flyctl secrets set SESSION_SECRET="$SessionSecret" --app $AppName

# Deploy the application
Write-Status "Deploying application to Fly.io..."
flyctl deploy --app $AppName --yes

# Wait for deployment to complete
Write-Status "Waiting for deployment to complete..."
Start-Sleep -Seconds 10

# Display final information
Write-Status "Deployment completed successfully! 🎉"
Write-Host ""
Write-Host "🌐 Your application is available at: https://$AppName.fly.dev" -ForegroundColor Cyan
Write-Host "📊 Monitor your app: flyctl status --app $AppName" -ForegroundColor Cyan
Write-Host "📋 View logs: flyctl logs --app $AppName" -ForegroundColor Cyan
Write-Host "🔧 SSH into app: flyctl ssh console --app $AppName" -ForegroundColor Cyan
Write-Host ""
Write-Host "📁 To import your existing data:" -ForegroundColor Yellow
Write-Host "   1. Copy your data/ directory to the deployed app" -ForegroundColor Yellow
Write-Host "   2. SSH into the app: flyctl ssh console --app $AppName" -ForegroundColor Yellow
Write-Host "   3. Run: python3 migrate_data.py" -ForegroundColor Yellow
Write-Host ""
Write-Status "Don't forget to set up your admin user after first login!"

# Update replit.md with deployment information
$deploymentInfo = @"

## Fly.io Deployment
- App Name: $AppName
- URL: https://$AppName.fly.dev
- Database: $AppName-db (PostgreSQL)
- Deployment Date: $(Get-Date)
- Migration Script: migrate_data.py available for JSON data import
"@

Add-Content -Path "replit.md" -Value $deploymentInfo

Write-Status "Deployment information added to replit.md"