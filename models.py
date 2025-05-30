import json
import os
import uuid
from datetime import datetime
from typing import List, Dict, Optional

class JSONDatabase:
    """Base class for JSON database operations"""
    
    def __init__(self, filename: str):
        self.filename = filename
        self.data_dir = "data"
        self.filepath = os.path.join(self.data_dir, filename)
        self._ensure_data_directory()
        self._ensure_file_exists()
    
    def _ensure_data_directory(self):
        """Create data directory if it doesn't exist"""
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
    
    def _ensure_file_exists(self):
        """Create file with empty list if it doesn't exist"""
        if not os.path.exists(self.filepath):
            with open(self.filepath, 'w') as f:
                json.dump([], f)
    
    def load_data(self) -> List[Dict]:
        """Load data from JSON file"""
        try:
            with open(self.filepath, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return []
    
    def save_data(self, data: List[Dict]):
        """Save data to JSON file"""
        with open(self.filepath, 'w') as f:
            json.dump(data, f, indent=2, default=str)

class Customer:
    """Customer model for managing customer data"""
    
    def __init__(self):
        self.db = JSONDatabase("customers.json")
    
    def generate_id(self) -> str:
        """Generate unique customer ID"""
        return f"CUST-{str(uuid.uuid4())[:8].upper()}"
    
    def get_all(self) -> List[Dict]:
        """Get all customers"""
        return self.db.load_data()
    
    def get_by_id(self, customer_id: str) -> Optional[Dict]:
        """Get customer by ID"""
        customers = self.db.load_data()
        for customer in customers:
            if customer.get('id') == customer_id:
                return customer
        return None
    
    def add(self, customer_data: Dict) -> Dict:
        """Add new customer"""
        customers = self.db.load_data()
        
        # Generate unique ID
        customer_data['id'] = self.generate_id()
        customer_data['created_at'] = datetime.now().isoformat()
        customer_data['updated_at'] = datetime.now().isoformat()
        
        customers.append(customer_data)
        self.db.save_data(customers)
        
        return customer_data
    
    def update(self, customer_id: str, customer_data: Dict) -> Optional[Dict]:
        """Update existing customer"""
        customers = self.db.load_data()
        
        for i, customer in enumerate(customers):
            if customer.get('id') == customer_id:
                # Preserve original ID and created_at
                customer_data['id'] = customer_id
                customer_data['created_at'] = customer.get('created_at')
                customer_data['updated_at'] = datetime.now().isoformat()
                
                customers[i] = customer_data
                self.db.save_data(customers)
                return customer_data
        
        return None
    
    def delete(self, customer_id: str) -> bool:
        """Delete customer"""
        customers = self.db.load_data()
        
        for i, customer in enumerate(customers):
            if customer.get('id') == customer_id:
                customers.pop(i)
                self.db.save_data(customers)
                return True
        
        return False
    
    def search(self, query: str) -> List[Dict]:
        """Search customers by name, email, or phone"""
        customers = self.db.load_data()
        query = query.lower()
        
        results = []
        for customer in customers:
            if (query in customer.get('name', '').lower() or 
                query in customer.get('email', '').lower() or 
                query in customer.get('phone', '').lower()):
                results.append(customer)
        
        return results

class Cylinder:
    """Cylinder model for managing cylinder data"""
    
    def __init__(self):
        self.db = JSONDatabase("cylinders.json")
    
    def generate_id(self) -> str:
        """Generate unique cylinder ID"""
        return f"CYL-{str(uuid.uuid4())[:8].upper()}"
    
    def get_all(self) -> List[Dict]:
        """Get all cylinders"""
        return self.db.load_data()
    
    def get_by_id(self, cylinder_id: str) -> Optional[Dict]:
        """Get cylinder by ID"""
        cylinders = self.db.load_data()
        for cylinder in cylinders:
            if cylinder.get('id') == cylinder_id:
                return cylinder
        return None
    
    def add(self, cylinder_data: Dict) -> Dict:
        """Add new cylinder"""
        cylinders = self.db.load_data()
        
        # Generate unique ID
        cylinder_data['id'] = self.generate_id()
        cylinder_data['created_at'] = datetime.now().isoformat()
        cylinder_data['updated_at'] = datetime.now().isoformat()
        
        cylinders.append(cylinder_data)
        self.db.save_data(cylinders)
        
        return cylinder_data
    
    def update(self, cylinder_id: str, cylinder_data: Dict) -> Optional[Dict]:
        """Update existing cylinder"""
        cylinders = self.db.load_data()
        
        for i, cylinder in enumerate(cylinders):
            if cylinder.get('id') == cylinder_id:
                # Preserve original ID and created_at
                cylinder_data['id'] = cylinder_id
                cylinder_data['created_at'] = cylinder.get('created_at')
                cylinder_data['updated_at'] = datetime.now().isoformat()
                
                cylinders[i] = cylinder_data
                self.db.save_data(cylinders)
                return cylinder_data
        
        return None
    
    def delete(self, cylinder_id: str) -> bool:
        """Delete cylinder"""
        cylinders = self.db.load_data()
        
        for i, cylinder in enumerate(cylinders):
            if cylinder.get('id') == cylinder_id:
                cylinders.pop(i)
                self.db.save_data(cylinders)
                return True
        
        return False
    
    def search(self, query: str) -> List[Dict]:
        """Search cylinders by serial number, type, or status"""
        cylinders = self.db.load_data()
        query = query.lower()
        
        results = []
        for cylinder in cylinders:
            if (query in cylinder.get('serial_number', '').lower() or 
                query in cylinder.get('type', '').lower() or 
                query in cylinder.get('status', '').lower() or 
                query in cylinder.get('location', '').lower()):
                results.append(cylinder)
        
        return results
    
    def get_by_status(self, status: str) -> List[Dict]:
        """Get cylinders by status"""
        cylinders = self.db.load_data()
        return [c for c in cylinders if c.get('status', '').lower() == status.lower()]
