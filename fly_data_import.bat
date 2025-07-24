@echo off
:: Windows Data Import Script for Fly.io
:: This script helps upload and import JSON data to the deployed Fly.io app

echo 🚀 Starting data import to Fly.io...

:: Check if flyctl is installed
flyctl version >nul 2>&1
if errorlevel 1 (
    echo ❌ flyctl is not installed. Please install it first:
    echo    Visit: https://fly.io/docs/flyctl/install/
    pause
    exit /b 1
)

:: Get app name from user
set /p APP_NAME="Enter your Fly.io app name: "

if "%APP_NAME%"=="" (
    echo ❌ App name cannot be empty
    pause
    exit /b 1
)

:: Check if data directory exists
if not exist "data" (
    echo ❌ No data directory found. Please ensure your JSON data files are in a 'data' directory.
    pause
    exit /b 1
)

:: List data files
echo 📁 Found data files:
dir /b data\*.json

:: Create migration instructions
echo.
echo 📋 To complete the data import:
echo.
echo 1. SSH into your app:
echo    flyctl ssh console --app %APP_NAME%
echo.
echo 2. Create migration script on server:
echo    cat ^> migrate_data.py ^<^< 'EOF'
echo    [Copy the contents of migrate_data.py here]
echo    EOF
echo.
echo 3. Upload your JSON files (in another terminal):
echo    flyctl ssh sftp --app %APP_NAME%
echo    # Upload customers.json, cylinders.json, etc. to /tmp/
echo.
echo 4. Run migration:
echo    python3 migrate_data.py
echo.
echo 📝 Detailed instructions are in README_DEPLOYMENT.md
echo.
echo Press any key to continue...
pause >nul