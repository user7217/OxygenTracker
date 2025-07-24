# Fly.io Deployment Guide for Windows

This guide helps you deploy your Oxygen Cylinder Tracker to Fly.io from Windows with PostgreSQL database and data migration.

## Prerequisites

1. **Install flyctl** (Fly.io CLI):
   - Download from: https://fly.io/docs/flyctl/install/
   - Or run in PowerShell: `iwr https://fly.io/install.ps1 -useb | iex`

2. **Create Fly.io account and login**:
   ```cmd
   flyctl auth signup
   # or
   flyctl auth login
   ```

3. **Ensure PowerShell is available** (usually pre-installed on Windows 10/11):
   - If not available, download from: https://github.com/PowerShell/PowerShell

## Quick Deployment

### Option 1: Using Batch File (Recommended)
```cmd
deploy_to_fly.bat
```

### Option 2: Using PowerShell Directly
```powershell
.\deploy_to_fly.ps1
```

### Option 3: With Parameters
```powershell
.\deploy_to_fly.ps1 -AppName "my-oxygen-tracker"
```

This script will:
- ✅ Create Fly.io app configuration
- ✅ Set up PostgreSQL database
- ✅ Configure environment variables
- ✅ Deploy your application
- ✅ Provide data migration instructions

## Manual Data Migration

After deployment, import your existing JSON data:

### Using Batch Helper
```cmd
fly_data_import.bat
```

### Manual Steps
1. **SSH into your app**:
   ```cmd
   flyctl ssh console --app your-app-name
   ```

2. **Upload data files** (in another command prompt):
   ```cmd
   flyctl ssh sftp --app your-app-name
   ```
   Upload `customers.json`, `cylinders.json`, etc. to `/tmp/`

3. **Run migration** (back in SSH console):
   ```bash
   python3 migrate_data.py
   ```

## Post-Deployment Setup

1. **Visit your app**: `https://your-app-name.fly.dev`
2. **Create admin user**: Login with default credentials (admin/admin123)
3. **Update admin password**: Go to user management and change password
4. **Verify data**: Check that all customers and cylinders imported correctly

## Useful Windows Commands

```cmd
:: Check app status
flyctl status --app your-app-name

:: View logs
flyctl logs --app your-app-name

:: SSH into app
flyctl ssh console --app your-app-name

:: Scale app (if needed)
flyctl scale memory 1024 --app your-app-name

:: Database management
flyctl postgres connect --app your-app-name-db
```

## Files Created by Deployment Script

- `fly.toml` - Fly.io app configuration
- `Dockerfile` - Production container setup  
- `migrate_data.py` - Data migration script
- `.flyignore` - Files to exclude from deployment
- `wsgi.py` - WSGI entry point (if not exists)
- `health_check.py` - Health check endpoint

## Environment Variables Set

- `DATABASE_URL` - PostgreSQL connection (auto-set by Fly.io)
- `FLASK_SECRET_KEY` - Session security (randomly generated)
- `SESSION_SECRET` - Additional security (randomly generated)
- `FLASK_ENV=production` - Production mode

## Windows-Specific Notes

### PowerShell Execution Policy
If you get execution policy errors:
```powershell
Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope CurrentUser
```

### File Encoding
All files are created with UTF-8 encoding to ensure compatibility.

### Path Separators
The scripts handle Windows path separators automatically.

## Troubleshooting

### Deployment Issues
```cmd
:: Check deployment logs
flyctl logs --app your-app-name

:: Check app status
flyctl status --app your-app-name
```

### PowerShell Issues
```powershell
# Check PowerShell version
$PSVersionTable.PSVersion

# Check execution policy
Get-ExecutionPolicy
```

### flyctl Issues
```cmd
:: Update flyctl
flyctl version update

:: Re-authenticate
flyctl auth login
```

### Data Migration Issues
1. **Check SSH connection**:
   ```cmd
   flyctl ssh console --app your-app-name
   ```

2. **Verify data files uploaded**:
   ```bash
   ls -la /tmp/
   ```

3. **Check Python environment**:
   ```bash
   python3 --version
   which python3
   ```

4. **Run migration with debugging**:
   ```bash
   python3 -c "import migrate_data; migrate_data.migrate_json_data()"
   ```

## Security Considerations

- Default admin credentials: `admin` / `admin123`
- **CRITICAL**: Change admin password immediately after first login
- All secrets are randomly generated during deployment
- Database connections are encrypted
- HTTPS is enforced automatically

## Cost Optimization

- App uses shared CPU with auto-stop/start capabilities
- Database uses minimal 1GB volume
- Expected monthly cost: ~$5-10 for small usage patterns

## Updating Your Deployed App

To deploy updates:
```cmd
flyctl deploy --app your-app-name
```

## Advanced Configuration

### Custom fly.toml
Edit `fly.toml` after initial deployment for custom settings:
- Memory allocation
- CPU configuration
- Regional deployment
- Custom domains

### Environment Variables
Add custom environment variables:
```cmd
flyctl secrets set CUSTOM_VAR="value" --app your-app-name
```

### Database Management
```cmd
:: Connect to database
flyctl postgres connect --app your-app-name-db

:: Create database backup
flyctl postgres backup --app your-app-name-db
```

## Support Resources

- **Fly.io Documentation**: https://fly.io/docs/
- **flyctl Reference**: https://fly.io/docs/flyctl/
- **PostgreSQL on Fly.io**: https://fly.io/docs/postgres/

## Common Windows Deployment Errors

### Error: "flyctl is not recognized"
**Solution**: Add flyctl to your PATH or reinstall using the official installer.

### Error: "PowerShell execution policy"
**Solution**: Run `Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope CurrentUser`

### Error: "Access denied" during file creation
**Solution**: Run Command Prompt or PowerShell as Administrator.

The deployment scripts handle all the complexity of setting up a production-ready Flask application on Fly.io with PostgreSQL!