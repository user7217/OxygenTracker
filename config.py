# Local Development Configuration
# This file contains settings specific to local development

import os
from datetime import timedelta

class Config:
    # Basic Flask config
    SECRET_KEY = os.environ.get('FLASK_SECRET_KEY') or 'dev-secret-key'
    SESSION_PERMANENT = False
    PERMANENT_SESSION_LIFETIME = timedelta(hours=24)
    
    # Database config (SQLite for local development)
    DATABASE_URL = os.environ.get('DATABASE_URL') or 'sqlite:///oxygen_tracker.db'
    
    # Development settings
    DEBUG = True
    TESTING = False
    
    # File upload settings
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    
    # Pagination
    ITEMS_PER_PAGE = 50
    
    # Backup settings
    BACKUP_DIRECTORY = 'backups'
    AUTO_BACKUP_INTERVAL = 14  # days
