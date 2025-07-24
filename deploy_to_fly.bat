@echo off
:: Fly.io Deployment Script for Oxygen Cylinder Tracker (Windows Batch)
:: This is a wrapper script that calls the PowerShell version

echo 🚀 Starting Fly.io deployment for Oxygen Cylinder Tracker...

:: Check if PowerShell is available
powershell -Command "Get-Host" >nul 2>&1
if errorlevel 1 (
    echo ❌ PowerShell is not available. Please ensure PowerShell is installed.
    echo    Download from: https://github.com/PowerShell/PowerShell
    pause
    exit /b 1
)

:: Check if flyctl is installed
flyctl version >nul 2>&1
if errorlevel 1 (
    echo ❌ flyctl is not installed. Please install it first:
    echo    Visit: https://fly.io/docs/flyctl/install/
    echo    Or run: iwr https://fly.io/install.ps1 -useb ^| iex
    pause
    exit /b 1
)

:: Get app name from user
set /p APP_NAME="Enter your Fly.io app name (e.g., my-oxygen-tracker): "

if "%APP_NAME%"=="" (
    echo ❌ App name cannot be empty
    pause
    exit /b 1
)

:: Run the PowerShell script
echo 🔄 Running PowerShell deployment script...
powershell -ExecutionPolicy Bypass -File "deploy_to_fly.ps1" -AppName "%APP_NAME%"

if errorlevel 1 (
    echo ❌ Deployment failed. Check the error messages above.
    pause
    exit /b 1
)

echo ✅ Deployment completed successfully!
echo.
echo 🌐 Your application is available at: https://%APP_NAME%.fly.dev
echo.
echo Press any key to continue...
pause >nul