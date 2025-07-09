#!/bin/bash

# Git setup script for connecting to GitHub repository
# Repository: github.com/user7217/OxygenTracker

echo "🔧 Setting up Git connection to GitHub repository..."

# Configure Git user (you may need to update these)
echo "📝 Configuring Git user settings..."
git config user.name "user7217"
git config user.email "user7217@example.com"  # Update this with your actual email

# Add or update the remote origin
echo "🔗 Setting up remote repository..."
git remote remove origin 2>/dev/null || true  # Remove existing origin if it exists
git remote add origin https://github.com/user7217/OxygenTracker.git

# Check current status
echo "📊 Checking current Git status..."
git status

# Add all files
echo "📁 Adding all files to Git..."
git add .

# Create .gitignore if it doesn't exist
if [ ! -f .gitignore ]; then
    echo "📝 Creating .gitignore file..."
    cat > .gitignore << EOL
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
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

# Environment variables
.env
.venv
env/
venv/
ENV/
env.bak/
venv.bak/

# Data files (optional - uncomment if you don't want to track data)
# data/*.json

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
Thumbs.db

# Logs
*.log

# Temporary files
*.tmp
*.temp
EOL
fi

# Show what will be committed
echo "📋 Files to be committed:"
git diff --cached --name-only

# Commit changes
echo "💾 Committing changes..."
git commit -m "Add bulk cylinder management with text box input and touch-screen optimization

- Added cylinder management modal with text box input for bulk operations
- Implemented customer-wise filtering for rental tracking
- Added rental duration calculation with visual indicators
- Enhanced touch-screen optimization with larger fonts and buttons
- Improved card-based layout for better mobile interaction
- Added API endpoint for real-time rental data loading
- Support for both comma and line-separated cylinder ID input
- Comprehensive validation and error reporting for bulk operations"

echo "🚀 Ready to push to GitHub!"
echo ""
echo "To push your changes, run:"
echo "git push -u origin main"
echo ""
echo "Note: You'll need to authenticate with GitHub using either:"
echo "1. Personal Access Token (recommended)"
echo "2. SSH key"
echo ""
echo "If this is your first push to the repository, you may need to use:"
echo "git push -u origin main --force"
echo ""
echo "Setup complete! 🎉"