# SQLite to PostgreSQL Migration Guide

This application has been updated to use PostgreSQL exclusively. SQLite support has been completely removed.

## Why This Change?

- **Data Consistency**: Eliminates schema mismatches between development and production
- **Performance**: Better handling of concurrent operations
- **Features**: Full support for advanced database features
- **Reliability**: Robust connection handling and error recovery

## What Was Removed

✓ All SQLite database files (.db, .sqlite files)
✓ SQLite fallback configuration
✓ Mixed database support code
✓ Local development SQLite setup

## Migration Steps

### 1. For New Installations
- Install PostgreSQL locally or use cloud database
- Set DATABASE_URL environment variable
- Run normal setup process

### 2. For Existing Data Migration
If you had existing SQLite data, it has been backed up in the `backups/` directory.

To migrate your data:
1. Start the application with PostgreSQL configured
2. Use the Import Data feature in the web interface
3. Import your backed up JSON data files from `data/` directory
4. Or use the `import_from_json.py` script

### 3. Local Development
```bash
# Set up PostgreSQL locally
# Ubuntu/Debian:
sudo apt-get install postgresql postgresql-contrib

# macOS:
brew install postgresql

# Create database
sudo -u postgres createdb oxygen_tracker

# Set environment variable in .env
DATABASE_URL=postgresql://username:password@localhost:5432/oxygen_tracker
```

### 4. Cloud Database Options
- **Neon**: Free PostgreSQL database (recommended for development)
- **Supabase**: Free tier with PostgreSQL
- **Railway**: PostgreSQL hosting
- **DigitalOcean**: Managed PostgreSQL

## Environment Variables

Required in .env file:
```
DATABASE_URL=postgresql://username:password@host:port/database_name
SESSION_SECRET=your-secret-key
```

## Verification

After setup, verify your configuration:
```bash
python -c "import os; print('PostgreSQL configured:' if os.environ.get('DATABASE_URL', '').startswith('postgresql') else 'Configuration needed')"
```

## Support

If you encounter issues:
1. Verify PostgreSQL is running and accessible
2. Check DATABASE_URL format
3. Ensure database exists and permissions are correct
4. Check application logs for connection errors

## Data Recovery

Your original SQLite data has been backed up to:
- Database files: `backups/backup_YYYYMMDD_HHMMSS_*.db`
- JSON exports: `data/*.json` (if available)

Use these backups if you need to recover any data.
