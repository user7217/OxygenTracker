# Fly.io Deployment Guide

This guide helps you deploy your Oxygen Cylinder Tracker to Fly.io with PostgreSQL database and data migration.

## Prerequisites

1. **Install flyctl** (Fly.io CLI):
   ```bash
   curl -L https://fly.io/install.sh | sh
   ```

2. **Create Fly.io account and login**:
   ```bash
   flyctl auth signup  # or flyctl auth login
   ```

## Quick Deployment

Run the automated deployment script:

```bash
./deploy_to_fly.sh
```

This script will:
- ✅ Create Fly.io app configuration
- ✅ Set up PostgreSQL database
- ✅ Configure environment variables
- ✅ Deploy your application
- ✅ Provide data migration instructions

## Manual Data Migration

After deployment, import your existing JSON data:

### Option 1: Automated Import Script
```bash
python3 fly_data_import.py your-app-name
```

### Option 2: Manual Upload
```bash
# SSH into your app
flyctl ssh console --app your-app-name

# Upload your data files (in another terminal)
flyctl ssh sftp --app your-app-name
# Upload customers.json, cylinders.json, etc. to /tmp/

# Back in SSH console, run migration
python3 migrate_data.py
```

## Post-Deployment Setup

1. **Visit your app**: `https://your-app-name.fly.dev`
2. **Create admin user**: Login with default credentials (admin/admin123)
3. **Update admin password**: Go to user management and change password
4. **Verify data**: Check that all customers and cylinders imported correctly

## Useful Commands

```bash
# Check app status
flyctl status --app your-app-name

# View logs
flyctl logs --app your-app-name

# SSH into app
flyctl ssh console --app your-app-name

# Scale app (if needed)
flyctl scale memory 1024 --app your-app-name

# Database management
flyctl postgres connect --app your-app-name-db
```

## Configuration Files Created

- `fly.toml` - Fly.io app configuration
- `Dockerfile` - Production container setup  
- `migrate_data.py` - Data migration script
- `.flyignore` - Files to exclude from deployment

## Environment Variables Set

- `DATABASE_URL` - PostgreSQL connection (auto-set)
- `FLASK_SECRET_KEY` - Session security
- `SESSION_SECRET` - Additional security
- `FLASK_ENV=production` - Production mode

## Troubleshooting

### App won't start
```bash
flyctl logs --app your-app-name
```

### Database connection issues
```bash
flyctl postgres connect --app your-app-name-db
```

### Data migration problems
```bash
flyctl ssh console --app your-app-name
# Check if data files exist in /tmp/
ls -la /tmp/
# Run migration with debugging
python3 -c "import migrate_data; migrate_data.migrate_json_data()"
```

### Memory issues
```bash
flyctl scale memory 1024 --app your-app-name
```

## Security Notes

- Default admin credentials: `admin` / `admin123`
- **IMPORTANT**: Change admin password immediately after first login
- All data is encrypted in transit and at rest
- PostgreSQL database includes automatic backups

## Cost Optimization

- App uses shared CPU with auto-stop/start
- Database uses minimal 1GB volume
- Expected monthly cost: ~$5-10 for small usage

## Support

If you encounter issues:
1. Check logs: `flyctl logs --app your-app-name`
2. Review Fly.io documentation: https://fly.io/docs/
3. Check database connectivity: `flyctl postgres connect --app your-app-name-db`

## Updating Your App

To deploy updates:
```bash
flyctl deploy --app your-app-name
```

The deployment script creates everything needed for a production-ready deployment!