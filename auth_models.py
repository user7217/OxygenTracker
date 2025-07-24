# auth_models.py - User authentication and management
import json
import os
from werkzeug.security import generate_password_hash, check_password_hash
from typing import Dict, List, Optional
import uuid
from datetime import datetime

class UserManager:
    """User management system with file-based storage"""
    
    def __init__(self):
        self.data_file = 'data/users.json'
        self._ensure_data_file()
        self._create_default_admin()
    
    def _ensure_data_file(self):
        """Ensure the users data file exists"""
        os.makedirs('data', exist_ok=True)
        if not os.path.exists(self.data_file):
            with open(self.data_file, 'w') as f:
                json.dump([], f)
    
    def _load_users(self) -> List[Dict]:
        """Load users from file"""
        try:
            with open(self.data_file, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return []
    
    def _save_users(self, users: List[Dict]):
        """Save users to file"""
        with open(self.data_file, 'w') as f:
            json.dump(users, f, indent=2)
    
    def _create_default_admin(self):
        """Create default admin user if no users exist"""
        users = self._load_users()
        if not users:
            admin_user = {
                'id': str(uuid.uuid4()),
                'username': 'admin',
                'password_hash': generate_password_hash('admin123'),
                'role': 'admin',
                'created_at': datetime.now().isoformat()
            }
            users.append(admin_user)
            self._save_users(users)
    
    def authenticate(self, username: str, password: str) -> Optional[Dict]:
        """Authenticate user and return user data if valid"""
        users = self._load_users()
        for user in users:
            if user['username'] == username:
                if check_password_hash(user['password_hash'], password):
                    return user
        return None
    
    def get_user_by_id(self, user_id: str) -> Optional[Dict]:
        """Get user by ID"""
        users = self._load_users()
        for user in users:
            if user['id'] == user_id:
                return user
        return None
    
    def create_user(self, username: str, password: str, role: str = 'user') -> bool:
        """Create a new user"""
        users = self._load_users()
        
        # Check if username already exists
        if any(user['username'] == username for user in users):
            return False
        
        new_user = {
            'id': str(uuid.uuid4()),
            'username': username,
            'password_hash': generate_password_hash(password),
            'role': role,
            'created_at': datetime.now().isoformat()
        }
        
        users.append(new_user)
        self._save_users(users)
        return True
    
    def get_all_users(self) -> List[Dict]:
        """Get all users (without password hashes)"""
        users = self._load_users()
        return [{k: v for k, v in user.items() if k != 'password_hash'} for user in users]
    
    def delete_user(self, user_id: str) -> bool:
        """Delete a user by ID"""
        users = self._load_users()
        updated_users = [user for user in users if user['id'] != user_id]
        
        if len(updated_users) != len(users):
            self._save_users(updated_users)
            return True
        return False
    
    def update_user_role(self, user_id: str, new_role: str) -> bool:
        """Update user role"""
        users = self._load_users()
        for user in users:
            if user['id'] == user_id:
                user['role'] = new_role
                user['updated_at'] = datetime.now().isoformat()
                self._save_users(users)
                return True
        return False