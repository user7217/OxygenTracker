#!/usr/bin/env python3
"""
PostgreSQL-Only Verification Script
Scans codebase to ensure no SQLite references remain
"""

import os
import glob
from pathlib import Path

def scan_for_sqlite_references():
    """Scan all Python files for SQLite references"""
    print("🔍 Scanning codebase for SQLite references...")
    
    # File patterns to scan
    file_patterns = [
        "*.py",
        "*.md",
        "*.txt",
        "*.env*",
        "*.conf*"
    ]
    
    # SQLite keywords to search for
    sqlite_keywords = [
        "sqlite",
        "SQLite", 
        "SQLITE",
        "sqlite3",
        ".db",
        "sqlite:///"
    ]
    
    found_references = []
    
    for pattern in file_patterns:
        files = glob.glob(pattern, recursive=True)
        files.extend(glob.glob(f"**/{pattern}", recursive=True))
        
        for file_path in files:
            # Skip this verification script itself
            if file_path.endswith('verify_postgresql_only.py'):
                continue
                
            # Skip backup files
            if '.backup_' in file_path:
                continue
                
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    
                for keyword in sqlite_keywords:
                    if keyword in content:
                        # Get line numbers
                        lines = content.split('\n')
                        line_numbers = []
                        for i, line in enumerate(lines, 1):
                            if keyword in line:
                                line_numbers.append((i, line.strip()))
                        
                        if line_numbers:
                            found_references.append({
                                'file': file_path,
                                'keyword': keyword,
                                'occurrences': line_numbers
                            })
                            
            except Exception as e:
                print(f"Warning: Could not scan {file_path}: {e}")
    
    return found_references

def check_database_configuration():
    """Check current database configuration"""
    print("🔧 Checking database configuration...")
    
    database_url = os.environ.get('DATABASE_URL')
    
    if not database_url:
        print("❌ DATABASE_URL not set")
        return False
    
    if 'sqlite' in database_url.lower():
        print(f"❌ DATABASE_URL contains SQLite: {database_url}")
        return False
    
    if 'postgresql' in database_url.lower() or 'postgres' in database_url.lower():
        print(f"✅ PostgreSQL configured: {database_url.split('@')[0] + '@****' if '@' in database_url else database_url}")
        return True
    
    print(f"⚠️ Unknown database type: {database_url}")
    return False

def test_database_models():
    """Test that database models load correctly with PostgreSQL"""
    print("📦 Testing database models...")
    
    try:
        # Test db_models import
        import db_models
        print("✅ db_models imported successfully")
        
        # Test that PostgreSQL is enforced
        if hasattr(db_models, 'DATABASE_URL'):
            db_url = db_models.DATABASE_URL
            if 'postgresql' in db_url.lower():
                print("✅ db_models configured for PostgreSQL")
            else:
                print(f"❌ db_models has unexpected database: {db_url}")
                return False
        
        # Test db_service import
        import db_service
        print("✅ db_service imported successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing models: {e}")
        return False

def main():
    """Main verification function"""
    print("🚀 PostgreSQL-Only Verification")
    print("=" * 50)
    
    # Step 1: Scan for SQLite references
    references = scan_for_sqlite_references()
    
    if references:
        print(f"\n❌ Found {len(references)} files with SQLite references:")
        for ref in references:
            print(f"\n📄 {ref['file']} (keyword: '{ref['keyword']}')")
            for line_num, line in ref['occurrences'][:3]:  # Show first 3 occurrences
                print(f"   Line {line_num}: {line}")
            if len(ref['occurrences']) > 3:
                print(f"   ... and {len(ref['occurrences']) - 3} more")
    else:
        print("\n✅ No SQLite references found in codebase")
    
    # Step 2: Check database configuration
    print("\n" + "=" * 50)
    db_config_ok = check_database_configuration()
    
    # Step 3: Test database models
    print("\n" + "=" * 50)
    models_ok = test_database_models()
    
    # Summary
    print("\n" + "=" * 50)
    print("📋 VERIFICATION SUMMARY")
    print("=" * 50)
    
    if not references and db_config_ok and models_ok:
        print("🎉 VERIFICATION PASSED!")
        print("✅ System is fully configured for PostgreSQL-only usage")
        print("✅ No SQLite references found")
        print("✅ Database configuration is correct")
        print("✅ Models load successfully")
    else:
        print("⚠️ VERIFICATION ISSUES FOUND:")
        if references:
            print(f"❌ {len(references)} files contain SQLite references")
        if not db_config_ok:
            print("❌ Database configuration needs attention")
        if not models_ok:
            print("❌ Database models have issues")
    
    print("\nFor local development setup, see: SQLITE_MIGRATION_GUIDE.md")
    print("For production deployment, DATABASE_URL is automatically configured.")

if __name__ == "__main__":
    main()