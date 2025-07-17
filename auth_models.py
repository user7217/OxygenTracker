"""
Varasai Oxygen Cylinder Tracker - Authentication Models

This module handles user authentication, authorization, and user management
for the Varasai Oxygen Cylinder Tracker application.

Key Features:
- Role-based access control (Admin, User, Viewer)
- Secure password hashing using Werkzeug
- Session management and user authentication
- Default admin user creation
- User CRUD operations with proper validation

Security Features:
- Password hashing using scrypt algorithm (Werkzeug default)
- Session-based authentication
- Role-based permission system
- Account activation/deactivation
- Login tracking and audit logs

Author: Development Team
Date: July 2025
Version: 2.0
"""

import json
import os
import uuid
import hashlib
from datetime import datetime
from typing import List, Dict, Optional
from werkzeug.security import generate_password_hash, check_password_hash

class UserManager:
    """
    User management for authentication and authorization
    
    This class handles all user-related operations including authentication,
    user creation, role management, and session handling. It implements a
    three-tier role system: Admin (full access), User (operations), and
    Viewer (read-only access).
    
    The system automatically creates a default admin user (admin/admin123)
    if no users exist in the system.
    
    Attributes:
        data_dir (str): Directory for data storage
        users_file (str): Path to users JSON file
    """
    
    def __init__(self):
        """
        Initialize UserManager with file setup and default admin creation
        
        Sets up the data directory, ensures users file exists, and creates
        a default admin user if the system is empty.
        """
        self.data_dir = "data"
        self.users_file = os.path.join(self.data_dir, "users.json")
        self._ensure_data_directory()
        self._ensure_users_file()
        self._create_default_admin()
    
    def _ensure_data_directory(self):
        """
        Create data directory if it doesn't exist
        
        Ensures the data directory exists for storing user data.
        Called automatically during initialization.
        """
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
    
    def _ensure_users_file(self):
        """
        Create users file with empty list if it doesn't exist
        
        Initializes the users.json file with an empty array if it doesn't exist.
        This prevents file not found errors during user operations.
        """
        if not os.path.exists(self.users_file):
            with open(self.users_file, 'w') as f:
                json.dump([], f)
    
    def _create_default_admin(self):
        """
        Create default admin user if no users exist
        
        Creates a default admin user with credentials:
        - Username: admin
        - Password: admin123
        - Role: admin
        - Email: admin@oxygentracker.com
        
        This ensures the system is always accessible even on fresh installations.
        """
        users = self.load_users()
        if not users:
            admin_user = {
                'id': f"USER-{str(uuid.uuid4())[:8].upper()}",
                'username': 'admin',
                'email': 'admin@oxygentracker.com',
                'password_hash': generate_password_hash('admin123'),
                'role': 'admin',
                'is_active': True,
                'created_at': datetime.now().isoformat(),
                'last_login': None
            }
            users.append(admin_user)
            self.save_users(users)
    
    def load_users(self) -> List[Dict]:
        """Load users from JSON file"""
        try:
            with open(self.users_file, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return []
    
    def save_users(self, users: List[Dict]):
        """Save users to JSON file"""
        with open(self.users_file, 'w') as f:
            json.dump(users, f, indent=2, default=str)
    
    def get_user_by_username(self, username: str) -> Optional[Dict]:
        """Get user by username"""
        users = self.load_users()
        for user in users:
            if user.get('username') == username:
                return user
        return None
    
    def get_user_by_id(self, user_id: str) -> Optional[Dict]:
        """Get user by ID"""
        users = self.load_users()
        for user in users:
            if user.get('id') == user_id:
                return user
        return None
    
    def authenticate_user(self, username: str, password: str) -> Optional[Dict]:
        """Authenticate user with username and password"""
        user = self.get_user_by_username(username)
        if user and user.get('is_active', True):
            if check_password_hash(user.get('password_hash', ''), password):
                # Update last login
                self.update_last_login(user['id'])
                return user
        return None
    
    def update_last_login(self, user_id: str):
        """Update user's last login timestamp"""
        users = self.load_users()
        for i, user in enumerate(users):
            if user.get('id') == user_id:
                users[i]['last_login'] = datetime.now().isoformat()
                self.save_users(users)
                break
    
    def create_user(self, username: str, email: str, password: str, role: str = 'user') -> Dict:
        """Create a new user"""
        users = self.load_users()
        
        # Check if username or email already exists
        for user in users:
            if user.get('username') == username:
                raise ValueError("Username already exists")
            if user.get('email') == email:
                raise ValueError("Email already exists")
        
        new_user = {
            'id': f"USER-{str(uuid.uuid4())[:8].upper()}",
            'username': username,
            'email': email,
            'password_hash': generate_password_hash(password),
            'role': role,
            'is_active': True,
            'created_at': datetime.now().isoformat(),
            'last_login': None
        }
        
        users.append(new_user)
        self.save_users(users)
        
        return new_user
    
    def get_all_users(self) -> List[Dict]:
        """Get all users (excluding password hashes)"""
        users = self.load_users()
        safe_users = []
        for user in users:
            safe_user = user.copy()
            safe_user.pop('password_hash', None)  # Remove password hash
            safe_users.append(safe_user)
        return safe_users
    
    def update_user(self, user_id: str, **kwargs) -> Optional[Dict]:
        """Update user information"""
        users = self.load_users()
        
        for i, user in enumerate(users):
            if user.get('id') == user_id:
                # Update allowed fields
                allowed_fields = ['email', 'role', 'is_active']
                for field, value in kwargs.items():
                    if field in allowed_fields:
                        users[i][field] = value
                
                # Handle password update separately
                if 'password' in kwargs:
                    users[i]['password_hash'] = generate_password_hash(kwargs['password'])
                
                self.save_users(users)
                
                # Return safe user data
                safe_user = users[i].copy()
                safe_user.pop('password_hash', None)
                return safe_user
        
        return None
    
    def delete_user(self, user_id: str) -> bool:
        """Delete a user"""
        users = self.load_users()
        
        for i, user in enumerate(users):
            if user.get('id') == user_id:
                # Don't allow deleting the last admin
                if user.get('role') == 'admin':
                    admin_count = sum(1 for u in users if u.get('role') == 'admin' and u.get('is_active'))
                    if admin_count <= 1:
                        raise ValueError("Cannot delete the last admin user")
                
                users.pop(i)
                self.save_users(users)
                return True
        
        return False