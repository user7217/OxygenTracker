#!/usr/bin/env python3
"""
SQLite Cleanup Script for Oxygen Cylinder Tracker
Removes all SQLite databases and ensures PostgreSQL-only usage
"""

import os
import sys
import glob
import shutil
from pathlib import Path
from datetime import datetime

def print_status(message):
    """Print status message with checkmark"""
    print(f"✓ {message}")

def print_warning(message):
    """Print warning message"""
    print(f"⚠ {message}")

def print_error(message):
    """Print error message"""
    print(f"✗ {message}")

def remove_sqlite_files():
    """Remove all SQLite database files"""
    print_status("Searching for SQLite database files...")
    
    # Common SQLite file patterns
    sqlite_patterns = [
        "*.db",
        "*.sqlite",
        "*.sqlite3",
        "oxygen_tracker*.db",
        "oxygen_tracker*.sqlite*"
    ]
    
    removed_files = []
    backup_files = []
    
    for pattern in sqlite_patterns:
        files = glob.glob(pattern)
        for file_path in files:
            if os.path.exists(file_path):
                # Create backup before removal
                backup_name = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{os.path.basename(file_path)}"
                backup_path = os.path.join("backups", backup_name)
                
                # Ensure backups directory exists
                os.makedirs("backups", exist_ok=True)
                
                try:
                    shutil.copy2(file_path, backup_path)
                    backup_files.append(backup_path)
                    print_status(f"Backed up {file_path} to {backup_path}")
                except Exception as e:
                    print_warning(f"Could not backup {file_path}: {e}")
                
                # Remove original file
                try:
                    os.remove(file_path)
                    removed_files.append(file_path)
                    print_status(f"Removed SQLite file: {file_path}")
                except Exception as e:
                    print_error(f"Could not remove {file_path}: {e}")
    
    if not removed_files:
        print_status("No SQLite files found to remove")
    else:
        print_status(f"Removed {len(removed_files)} SQLite files")
        print_status(f"Created {len(backup_files)} backup files")
    
    return removed_files, backup_files

def clean_sqlite_references():
    """Remove SQLite references from configuration files"""
    print_status("Cleaning SQLite references from configuration files...")
    
    files_to_clean = [
        ".env",
        "config.py",
        ".env.example"
    ]
    
    cleaned_files = []
    
    for file_path in files_to_clean:
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r') as f:
                    content = f.read()
                
                original_content = content
                
                # Remove SQLite DATABASE_URL lines
                lines = content.split('\n')
                new_lines = []
                
                for line in lines:
                    if 'DATABASE_URL' in line and 'sqlite' in line.lower():
                        # Comment out SQLite references
                        if not line.strip().startswith('#'):
                            new_lines.append(f"# REMOVED SQLite reference: {line}")
                            print_status(f"Commented out SQLite reference in {file_path}")
                        else:
                            new_lines.append(line)
                    else:
                        new_lines.append(line)
                
                new_content = '\n'.join(new_lines)
                
                if new_content != original_content:
                    # Create backup
                    backup_path = f"{file_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                    shutil.copy2(file_path, backup_path)
                    
                    # Write cleaned content
                    with open(file_path, 'w') as f:
                        f.write(new_content)
                    
                    cleaned_files.append(file_path)
                    print_status(f"Cleaned SQLite references from {file_path}")
                    print_status(f"Backup created: {backup_path}")
                
            except Exception as e:
                print_error(f"Could not clean {file_path}: {e}")
    
    if not cleaned_files:
        print_status("No SQLite references found in configuration files")
    
    return cleaned_files

def verify_postgresql_config():
    """Verify PostgreSQL configuration"""
    print_status("Verifying PostgreSQL configuration...")
    
    # Check environment variable
    database_url = os.environ.get('DATABASE_URL')
    
    if not database_url:
        print_error("DATABASE_URL environment variable not set")
        return False
    
    if 'sqlite' in database_url.lower():
        print_error(f"DATABASE_URL still contains SQLite reference: {database_url}")
        return False
    
    if 'postgresql' in database_url.lower() or 'postgres' in database_url.lower():
        print_status(f"PostgreSQL database configured: {database_url.split('@')[0] + '@****' if '@' in database_url else database_url}")
        return True
    
    print_warning(f"DATABASE_URL format unclear: {database_url}")
    return False

def update_documentation():
    """Update documentation to reflect PostgreSQL-only usage"""
    print_status("Updating documentation...")
    
    # Update README files if they exist
    readme_files = [
        "README.md",
        "README_LOCAL_SETUP.md",
        "LOCAL_SETUP.md"
    ]
    
    for readme_file in readme_files:
        if os.path.exists(readme_file):
            try:
                with open(readme_file, 'r') as f:
                    content = f.read()
                
                # Add PostgreSQL-only notice
                if 'PostgreSQL-only' not in content:
                    notice = """
## Database Requirements

**IMPORTANT: This application now requires PostgreSQL database only.**

SQLite support has been completely removed to ensure data consistency and avoid compatibility issues.

### Local Development Setup
1. Install PostgreSQL locally or use a cloud database
2. Set DATABASE_URL environment variable in .env file
3. Example: `DATABASE_URL=postgresql://username:password@localhost:5432/oxygen_tracker`

"""
                    
                    # Insert after title
                    lines = content.split('\n')
                    if lines and lines[0].startswith('#'):
                        lines.insert(1, notice)
                        new_content = '\n'.join(lines)
                        
                        # Create backup
                        backup_path = f"{readme_file}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                        shutil.copy2(readme_file, backup_path)
                        
                        with open(readme_file, 'w') as f:
                            f.write(new_content)
                        
                        print_status(f"Updated {readme_file} with PostgreSQL-only notice")
                        print_status(f"Backup created: {backup_path}")
                
            except Exception as e:
                print_error(f"Could not update {readme_file}: {e}")

def create_migration_guide():
    """Create a migration guide for users"""
    guide_content = """# SQLite to PostgreSQL Migration Guide

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
"""
    
    try:
        with open("SQLITE_MIGRATION_GUIDE.md", "w") as f:
            f.write(guide_content)
        print_status("Created migration guide: SQLITE_MIGRATION_GUIDE.md")
    except Exception as e:
        print_error(f"Could not create migration guide: {e}")

def main():
    """Main cleanup function"""
    print("🧹 SQLite Cleanup Script for Oxygen Cylinder Tracker")
    print("This script will remove all SQLite databases and ensure PostgreSQL-only usage")
    print()
    
    # Create backups directory
    os.makedirs("backups", exist_ok=True)
    
    # Step 1: Remove SQLite files
    removed_files, backup_files = remove_sqlite_files()
    
    # Step 2: Clean configuration files
    cleaned_files = clean_sqlite_references()
    
    # Step 3: Verify PostgreSQL configuration
    postgres_ok = verify_postgresql_config()
    
    # Step 4: Update documentation
    update_documentation()
    
    # Step 5: Create migration guide
    create_migration_guide()
    
    # Summary
    print()
    print("🎉 Cleanup completed!")
    print()
    print("Summary:")
    print(f"  • Removed {len(removed_files)} SQLite files")
    print(f"  • Created {len(backup_files)} backup files")
    print(f"  • Cleaned {len(cleaned_files)} configuration files")
    print(f"  • PostgreSQL configuration: {'✓ OK' if postgres_ok else '✗ Needs attention'}")
    print()
    
    if backup_files:
        print("Backup files created:")
        for backup in backup_files:
            print(f"  • {backup}")
        print()
    
    if not postgres_ok:
        print("⚠ ACTION REQUIRED:")
        print("  1. Set DATABASE_URL environment variable to PostgreSQL connection string")
        print("  2. Example: DATABASE_URL=postgresql://username:password@localhost:5432/oxygen_tracker")
        print("  3. Restart the application")
        print()
    else:
        print("✅ System is now configured for PostgreSQL-only usage!")
        print()
    
    print("Next steps:")
    print("  1. Review SQLITE_MIGRATION_GUIDE.md for detailed instructions")
    print("  2. Test application functionality")
    print("  3. Import any existing data using the web interface")
    print("  4. Remove backup files when no longer needed")

if __name__ == "__main__":
    main()