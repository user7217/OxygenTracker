import json
import os
import uuid
from datetime import datetime
from typing import List, Dict, Optional

class JSONDatabase:
    
    def __init__(self, filename: str):
        self.filename = filename
        self.data_dir = "data"
        self.filepath = os.path.join(self.data_dir, filename)
        self._ensure_data_directory()
        self._ensure_file_exists()
    
    def _ensure_data_directory(self):
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
    
    def _ensure_file_exists(self):
        if not os.path.exists(self.filepath):
            with open(self.filepath, 'w') as f:
                json.dump([], f)
    
    def load_data(self) -> List[Dict]:
        try:
            with open(self.filepath, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return []
    
    def save_data(self, data: List[Dict]):
        with open(self.filepath, 'w') as f:
            json.dump(data, f, indent=2, default=str)

class Customer:
    
    def __init__(self):
        self.db = JSONDatabase("customers.json")
    
    def generate_id(self) -> str:
        return f"CUST-{str(uuid.uuid4())[:8].upper()}"
    
    def get_all(self) -> List[Dict]:
        return self.db.load_data()
    
    def get_by_id(self, customer_id: str) -> Optional[Dict]:
        customers = self.db.load_data()
        for customer in customers:
            if customer.get('id') == customer_id:
                return customer
        return None
    
    def add(self, customer_data: Dict) -> Dict:
        customers = self.db.load_data()
        
        customer_data['id'] = self.generate_id()
        customer_data['created_at'] = datetime.now().isoformat()
        customer_data['updated_at'] = datetime.now().isoformat()
        
        customers.append(customer_data)
        self.db.save_data(customers)
        
        return customer_data
    
    def update(self, customer_id: str, customer_data: Dict) -> Optional[Dict]:
        customers = self.db.load_data()
        
        for i, customer in enumerate(customers):
            if customer.get('id') == customer_id:
                customer_data['id'] = customer_id
                customer_data['created_at'] = customer.get('created_at')
                customer_data['updated_at'] = datetime.now().isoformat()
                
                customers[i] = customer_data
                self.db.save_data(customers)
                return customer_data
        
        return None
    
    def delete(self, customer_id: str) -> bool:
        customers = self.db.load_data()
        
        for i, customer in enumerate(customers):
            if customer.get('id') == customer_id:
                customers.pop(i)
                self.db.save_data(customers)
                return True
        
        return False
    
    def search(self, query: str) -> List[Dict]:
        customers = self.db.load_data()
        query = query.lower()
        
        results = []
        for customer in customers:
            searchable_fields = [
                customer.get('customer_no', ''),
                customer.get('customer_name', ''),
                customer.get('customer_address', ''),
                customer.get('customer_city', ''),
                customer.get('customer_state', ''),
                customer.get('customer_phone', ''),
                customer.get('customer_apgst', ''),
                customer.get('customer_cst', ''),
                customer.get('id', ''),
                customer.get('name', ''),
                customer.get('email', ''),
                customer.get('phone', ''),
                customer.get('address', ''),
                customer.get('company', ''),
                customer.get('notes', '')
            ]
            
            if any(query in field.lower() for field in searchable_fields):
                results.append(customer)
        
        return results

class Cylinder:
    
    def __init__(self):
        self.db = JSONDatabase("cylinders.json")
    
    def generate_id(self) -> str:
        return f"CYL-{str(uuid.uuid4())[:8].upper()}"
    
    def get_all(self) -> List[Dict]:
        return self.db.load_data()
    
    def get_by_id(self, cylinder_id: str) -> Optional[Dict]:
        cylinders = self.db.load_data()
        for cylinder in cylinders:
            if cylinder.get('id') == cylinder_id:
                return cylinder
        return None
    
    def get_by_custom_id(self, custom_id: str) -> Optional[Dict]:
        cylinders = self.db.load_data()
        for cylinder in cylinders:
            if cylinder.get('custom_id') == custom_id:
                return cylinder
        return None
    
    def add(self, cylinder_data: Dict) -> Dict:
        cylinders = self.db.load_data()
        
        cylinder_data['id'] = self.generate_id()
        cylinder_data['created_at'] = datetime.now().isoformat()
        cylinder_data['updated_at'] = datetime.now().isoformat()
        
        if 'status' not in cylinder_data:
            cylinder_data['status'] = 'available'
        
        cylinders.append(cylinder_data)
        self.db.save_data(cylinders)
        
        return cylinder_data
    
    def update(self, cylinder_id: str, cylinder_data: Dict) -> Optional[Dict]:
        cylinders = self.db.load_data()
        
        for i, cylinder in enumerate(cylinders):
            if cylinder.get('id') == cylinder_id:
                cylinder_data['id'] = cylinder_id
                cylinder_data['created_at'] = cylinder.get('created_at')
                cylinder_data['updated_at'] = datetime.now().isoformat()
                
                cylinders[i] = cylinder_data
                self.db.save_data(cylinders)
                return cylinder_data
        
        return None
    
    def delete(self, cylinder_id: str) -> bool:
        cylinders = self.db.load_data()
        
        for i, cylinder in enumerate(cylinders):
            if cylinder.get('id') == cylinder_id:
                cylinders.pop(i)
                self.db.save_data(cylinders)
                return True
        
        return False
    
    def rent_cylinder(self, cylinder_id: str, customer_id: str, rental_date: str = None) -> bool:
        cylinders = self.db.load_data()
        
        for i, cylinder in enumerate(cylinders):
            if cylinder.get('id') == cylinder_id:
                cylinders[i]['status'] = 'rented'
                cylinders[i]['rented_to'] = customer_id
                cylinders[i]['date_borrowed'] = rental_date or datetime.now().isoformat()
                cylinders[i]['date_returned'] = None
                cylinders[i]['updated_at'] = datetime.now().isoformat()
                
                self.db.save_data(cylinders)
                return True
        
        return False
    
    def rent_cylinder_with_location(self, cylinder_id: str, customer_id: str, customer_name: str, customer_address: str, rental_date: str = None) -> bool:
        cylinders = self.db.load_data()
        
        for i, cylinder in enumerate(cylinders):
            if cylinder.get('id') == cylinder_id:
                cylinders[i]['status'] = 'rented'
                cylinders[i]['rented_to'] = customer_id
                cylinders[i]['customer_name'] = customer_name
                cylinders[i]['location'] = customer_address
                cylinders[i]['date_borrowed'] = rental_date or datetime.now().isoformat()
                cylinders[i]['date_returned'] = None
                cylinders[i]['updated_at'] = datetime.now().isoformat()
                
                self.db.save_data(cylinders)
                return True
        
        return False
    
    def return_cylinder(self, cylinder_id: str) -> bool:
        cylinders = self.db.load_data()
        
        for i, cylinder in enumerate(cylinders):
            if cylinder.get('id') == cylinder_id:
                cylinders[i]['status'] = 'available'
                cylinders[i]['rented_to'] = None
                cylinders[i]['customer_name'] = None
                cylinders[i]['location'] = 'Warehouse'
                cylinders[i]['date_returned'] = datetime.now().isoformat()
                cylinders[i]['updated_at'] = datetime.now().isoformat()
                
                self.db.save_data(cylinders)
                return True
        
        return False
    
    def search(self, query: str) -> List[Dict]:
        cylinders = self.db.load_data()
        query = query.lower()
        
        results = []
        for cylinder in cylinders:
            searchable_fields = [
                cylinder.get('id', ''),
                cylinder.get('serial_number', ''),
                cylinder.get('custom_id', ''),
                cylinder.get('type', ''),
                cylinder.get('size', ''),
                cylinder.get('location', ''),
                cylinder.get('status', ''),
                cylinder.get('customer_name', ''),
                cylinder.get('notes', '')
            ]
            
            if any(query in field.lower() for field in searchable_fields):
                results.append(cylinder)
        
        return results
    
    def get_by_customer(self, customer_id: str) -> List[Dict]:
        cylinders = self.db.load_data()
        return [c for c in cylinders if c.get('rented_to') == customer_id]
    
    def get_serial_number(self, cylinder_type: str, sequence: int) -> str:
        type_prefixes = {
            'Medical Oxygen': 'OXY',
            'Industrial Oxygen': 'OXY',
            'Carbon Dioxide': 'CO2',
            'Argon': 'ARG',
            'Nitrogen': 'N2',
            'Compressed Air': 'AIR',
            'Other': 'GAS'
        }
        
        prefix = type_prefixes.get(cylinder_type, 'GAS')
        return f"{prefix}-{sequence:03d}"
    
    def get_rental_days(self, cylinder: Dict) -> int:
        if cylinder.get('status') == 'rented' and cylinder.get('date_borrowed'):
            try:
                borrowed_date = datetime.fromisoformat(cylinder['date_borrowed'].replace('Z', '+00:00'))
                return (datetime.now() - borrowed_date).days
            except ValueError:
                return 0
        return 0
    
    def get_cylinders_by_rental_duration(self, months: int) -> List[Dict]:
        cylinders = self.db.load_data()
        results = []
        
        for cylinder in cylinders:
            if cylinder.get('status') == 'rented':
                rental_days = self.get_rental_days(cylinder)
                if rental_days >= (months * 30):
                    results.append(cylinder)
        
        return results
    
    def get_by_type(self, cylinder_type: str) -> List[Dict]:
        cylinders = self.db.load_data()
        return [c for c in cylinders if c.get('type') == cylinder_type]
    
    def get_by_status(self, status: str) -> List[Dict]:
        cylinders = self.db.load_data()
        return [c for c in cylinders if c.get('status', '').lower() == status.lower()]
    
    def bulk_rent(self, cylinder_ids: List[str], customer_id: str, rental_date: str = None) -> Dict:
        successful = 0
        failed = []
        
        for cylinder_id in cylinder_ids:
            if self.rent_cylinder(cylinder_id, customer_id, rental_date):
                successful += 1
            else:
                failed.append(cylinder_id)
        
        return {
            'successful': successful,
            'failed': failed
        }
    
    def bulk_return(self, cylinder_ids: List[str]) -> Dict:
        successful = 0
        failed = []
        
        for cylinder_id in cylinder_ids:
            if self.return_cylinder(cylinder_id):
                successful += 1
            else:
                failed.append(cylinder_id)
        
        return {
            'successful': successful,
            'failed': failed
        }