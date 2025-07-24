#!/bin/bash

# Local Development Setup Script for Oxygen Cylinder Tracker (Linux/macOS)
# Automatically sets up the development environment and imports data

set -e  # Exit on any error

echo "🚀 Starting local development setup for Oxygen Cylinder Tracker..."
echo

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${GREEN}✓${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    if ! command -v python &> /dev/null; then
        print_error "Python is not installed"
        echo "Please install Python 3.8+ from https://python.org"
        exit 1
    else
        PYTHON_CMD="python"
    fi
else
    PYTHON_CMD="python3"
fi

# Check Python version
PYTHON_VERSION=$($PYTHON_CMD --version 2>&1)
print_status "$PYTHON_VERSION found"

# Make setup script executable
chmod +x setup_local.py

# Run the Python setup script
echo "🔄 Running Python setup script..."
$PYTHON_CMD setup_local.py

if [ $? -eq 0 ]; then
    echo
    print_status "Setup completed successfully!"
    echo
    echo "🌐 To start the development server:"
    echo "   $PYTHON_CMD main.py"
    echo
    echo "📖 Then open your browser to: http://localhost:5000"
    echo "🔑 Login with: admin / admin123"
    echo
else
    print_error "Setup failed. Check the error messages above."
    exit 1
fi