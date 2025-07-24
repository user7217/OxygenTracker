@echo off
:: Local Development Setup Script for Oxygen Cylinder Tracker (Windows)
:: Automatically sets up the development environment and imports data

echo 🚀 Starting local development setup for Oxygen Cylinder Tracker...
echo.

:: Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python is not installed or not in PATH
    echo    Please install Python 3.8+ from https://python.org
    echo    Make sure to check "Add Python to PATH" during installation
    pause
    exit /b 1
)

:: Show Python version
for /f "tokens=*" %%i in ('python --version') do echo ✓ %%i found

:: Run the Python setup script
echo 🔄 Running Python setup script...
python setup_local.py

if errorlevel 1 (
    echo ❌ Setup failed. Check the error messages above.
    pause
    exit /b 1
)

echo.
echo ✅ Setup completed successfully!
echo.
echo 🌐 To start the development server:
echo    python main.py
echo.
echo 📖 Then open your browser to: http://localhost:5000
echo 🔑 Login with: admin / admin123
echo.
echo Press any key to continue...
pause >nul