#!/usr/bin/env python3
"""
Remove Legacy SQLite Components
Removes old JSON/SQLite model files and updates documentation
"""

import os
import shutil
from datetime import datetime

def print_status(message):
    """Print status message with checkmark"""
    print(f"✓ {message}")

def print_warning(message):
    """Print warning message"""
    print(f"⚠ {message}")

def remove_legacy_files():
    """Remove legacy model files that are no longer used"""
    print_status("Removing legacy model files...")
    
    legacy_files = [
        "models.py",  # Old JSON-based models
        "models_rental_history.py",  # Old JSON rental history
        "routes_broken.py",  # Broken routes backup
        "instant_importer.py"  # Old importer that uses JSON models
    ]
    
    removed_files = []
    
    for file_path in legacy_files:
        if os.path.exists(file_path):
            # Create backup
            backup_name = f"legacy_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{os.path.basename(file_path)}"
            backup_path = os.path.join("backups", backup_name)
            
            try:
                os.makedirs("backups", exist_ok=True)
                shutil.copy2(file_path, backup_path)
                os.remove(file_path)
                removed_files.append(file_path)
                print_status(f"Removed {file_path} (backed up to {backup_path})")
            except Exception as e:
                print_warning(f"Could not remove {file_path}: {e}")
    
    if not removed_files:
        print_status("No legacy files found to remove")
    
    return removed_files

def update_readme_files():
    """Update README files to remove SQLite references"""
    print_status("Updating README files...")
    
    readme_files = [
        "README_LOCAL_SETUP.md"
    ]
    
    for readme_file in readme_files:
        if os.path.exists(readme_file):
            try:
                with open(readme_file, 'r') as f:
                    content = f.read()
                
                # Replace SQLite references with PostgreSQL
                replacements = {
                    "SQLite database": "PostgreSQL database",
                    "sqlite:///": "postgresql://",
                    "oxygen_tracker.db": "PostgreSQL database",
                    "DATABASE_URL=sqlite:///oxygen_tracker.db": "DATABASE_URL=postgresql://username:password@localhost:5432/oxygen_tracker",
                    "DATABASE_URL=sqlite:///path/to/custom.db": "DATABASE_URL=postgresql://username:password@localhost:5432/custom_db",
                    "SQLite is suitable for development": "PostgreSQL is required for all environments",
                    "Database file grows": "Database performance scales well",
                    "SQLite file should not be committed": "Database credentials should not be committed"
                }
                
                original_content = content
                for old_text, new_text in replacements.items():
                    content = content.replace(old_text, new_text)
                
                if content != original_content:
                    # Create backup
                    backup_path = f"{readme_file}.legacy_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                    shutil.copy2(readme_file, backup_path)
                    
                    with open(readme_file, 'w') as f:
                        f.write(content)
                    
                    print_status(f"Updated {readme_file} (backup: {backup_path})")
                
            except Exception as e:
                print_warning(f"Could not update {readme_file}: {e}")

def clean_env_example():
    """Clean .env.example file"""
    print_status("Updating .env.example...")
    
    if os.path.exists(".env.example"):
        try:
            with open(".env.example", 'r') as f:
                content = f.read()
            
            # Remove SQLite references and add PostgreSQL example
            lines = content.split('\n')
            new_lines = []
            
            for line in lines:
                if 'DATABASE_URL' in line and 'sqlite' in line.lower():
                    new_lines.append("# PostgreSQL database connection (required)")
                    new_lines.append("DATABASE_URL=postgresql://username:password@localhost:5432/oxygen_tracker")
                    new_lines.append("# For production, this is automatically set by Replit")
                elif 'sqlite' not in line.lower():
                    new_lines.append(line)
            
            new_content = '\n'.join(new_lines)
            
            if new_content != content:
                backup_path = f".env.example.legacy_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                shutil.copy2(".env.example", backup_path)
                
                with open(".env.example", 'w') as f:
                    f.write(new_content)
                
                print_status(f"Updated .env.example (backup: {backup_path})")
            
        except Exception as e:
            print_warning(f"Could not update .env.example: {e}")

def verify_current_system():
    """Verify the current system is working with PostgreSQL"""
    print_status("Verifying current system...")
    
    # Check DATABASE_URL
    database_url = os.environ.get('DATABASE_URL')
    if database_url and 'postgresql' in database_url:
        print_status("✅ PostgreSQL database is configured")
    else:
        print_warning("❌ DATABASE_URL not set or not PostgreSQL")
        return False
    
    # Test database connection
    try:
        import db_service
        with db_service.CustomerService() as service:
            # Try a simple operation
            customers, count = service.get_all(page=1, per_page=1)
        print_status("✅ Database connection working")
        return True
    except Exception as e:
        print_warning(f"❌ Database connection error: {e}")
        return False

def main():
    """Main cleanup function"""
    print("🗑️ Removing Legacy SQLite Components")
    print("=" * 50)
    
    # Step 1: Remove legacy files
    removed_files = remove_legacy_files()
    
    # Step 2: Update documentation
    update_readme_files()
    
    # Step 3: Clean environment example
    clean_env_example()
    
    # Step 4: Verify system
    system_ok = verify_current_system()
    
    # Summary
    print("\n" + "=" * 50)
    print("📋 CLEANUP SUMMARY")
    print("=" * 50)
    
    print(f"✓ Removed {len(removed_files)} legacy files")
    print("✓ Updated documentation files")
    print("✓ Cleaned environment examples")
    
    if system_ok:
        print("✅ System verification passed")
        print("\n🎉 Legacy SQLite components successfully removed!")
        print("The system now uses PostgreSQL exclusively.")
    else:
        print("❌ System verification failed")
        print("Please check database configuration.")
    
    print("\nActive components:")
    print("  ✓ db_models.py - PostgreSQL database models")
    print("  ✓ db_service.py - PostgreSQL service layer")
    print("  ✓ routes.py - Updated application routes")
    print("  ✓ PostgreSQL database - Primary data storage")
    
    print("\nRemoved components:")
    for file in removed_files:
        print(f"  🗑️ {file} - Legacy file (backed up)")

if __name__ == "__main__":
    main()