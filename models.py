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
        """Search customers by name, email, phone, address, company, and other fields"""
        customers = self.db.load_data()
        query = query.lower()
        
        results = []
        for customer in customers:
            # Search across multiple fields
            searchable_fields = [
                customer.get('name', ''),
                customer.get('email', ''),
                customer.get('phone', ''),
                customer.get('address', ''),
                customer.get('company', ''),
                customer.get('notes', ''),
                customer.get('id', '')
            ]
            
            # Check if query matches any field
            for field_value in searchable_fields:
                if query in str(field_value).lower():
                    results.append(customer)
                    break  # Avoid duplicates
        
        return results
    
    def archive_old_data(self, months_old: int = 6) -> Dict[str, int]:
        """Archive customer data older than specified months and create backup"""
        from datetime import datetime, timedelta
        import json
        import os
        
        cutoff_date = datetime.now() - timedelta(days=months_old * 30)
        customers = self.db.load_data()
        
        active_customers = []
        archived_customers = []
        
        for customer in customers:
            # Check if customer has old data and no recent activity
            created_at = customer.get('created_at')
            should_archive = False
            
            if created_at:
                try:
                    created_date = datetime.fromisoformat(created_at.replace('Z', '+00:00').split('.')[0])
                    if created_date < cutoff_date:
                        # Only archive customers without active rentals (checked by caller)
                        should_archive = True
                except:
                    pass
            
            if should_archive:
                archived_customers.append(customer)
            else:
                active_customers.append(customer)
        
        # Create archived data backup
        if archived_customers:
            self._ensure_data_directory()
            archive_filename = f"data/customers_archive_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            
            try:
                with open(archive_filename, 'w') as f:
                    json.dump(archived_customers, f, indent=2)
                
                # Update main data file with only active customers
                self.db.save_data(active_customers)
                
                return {
                    'archived_count': len(archived_customers),
                    'remaining_count': len(active_customers),
                    'archive_file': archive_filename
                }
            except Exception as e:
                return {
                    'error': f"Failed to create archive: {str(e)}",
                    'archived_count': 0,
                    'remaining_count': len(customers)
                }
        
        return {
            'archived_count': 0,
            'remaining_count': len(customers),
            'message': 'No data to archive'
        }

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
    
    def find_by_any_identifier(self, identifier: str) -> Optional[Dict]:
        """Find cylinder by any identifier: ID, custom_id, or serial_number"""
        cylinders = self.db.load_data()
        identifier = identifier.strip()
        
        for cylinder in cylinders:
            # Check system ID
            if cylinder.get('id') == identifier:
                return cylinder
            # Check custom ID (case-insensitive)
            if cylinder.get('custom_id') and cylinder.get('custom_id').lower() == identifier.lower():
                return cylinder
            # Check serial number (case-insensitive)
            if cylinder.get('serial_number') and cylinder.get('serial_number').lower() == identifier.lower():
                return cylinder
        
        return None
    
    def add(self, cylinder_data: Dict) -> Dict:
        """Add new cylinder"""
        from models import Customer
        from datetime import datetime
        cylinders = self.db.load_data()
        
        # Generate unique ID
        cylinder_data['id'] = self.generate_id()
        cylinder_data['created_at'] = datetime.now().isoformat()
        cylinder_data['updated_at'] = datetime.now().isoformat()
        
        # Ensure custom_id field exists (even if empty)
        if 'custom_id' not in cylinder_data:
            cylinder_data['custom_id'] = ''
        
        # If cylinder is being rented to a customer, store customer name
        if cylinder_data.get('rented_to'):
            customer_model = Customer()
            customer = customer_model.get_by_id(cylinder_data['rented_to'])
            if customer:
                cylinder_data['customer_name'] = customer.get('name', '')
                cylinder_data['customer_email'] = customer.get('email', '')
        else:
            # Initialize customer fields as empty
            cylinder_data['customer_name'] = ''
            cylinder_data['customer_email'] = ''
        
        cylinders.append(cylinder_data)
        self.db.save_data(cylinders)
        
        return cylinder_data
    
    def update(self, cylinder_id: str, cylinder_data: Dict) -> Optional[Dict]:
        """Update existing cylinder"""
        from models import Customer
        from datetime import datetime
        cylinders = self.db.load_data()
        
        for i, cylinder in enumerate(cylinders):
            if cylinder.get('id') == cylinder_id:
                # Preserve original ID and created_at
                cylinder_data['id'] = cylinder_id
                cylinder_data['created_at'] = cylinder.get('created_at')
                cylinder_data['updated_at'] = datetime.now().isoformat()
                
                # Ensure custom_id field exists (even if empty)
                if 'custom_id' not in cylinder_data:
                    cylinder_data['custom_id'] = ''
                
                # If cylinder is being rented to a customer, store customer name
                if cylinder_data.get('rented_to'):
                    customer_model = Customer()
                    customer = customer_model.get_by_id(cylinder_data['rented_to'])
                    if customer:
                        cylinder_data['customer_name'] = customer.get('name', '')
                        cylinder_data['customer_email'] = customer.get('email', '')
                else:
                    # Clear customer info if not rented
                    cylinder_data['customer_name'] = ''
                    cylinder_data['customer_email'] = ''
                
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
        """Search cylinders by serial number, type, status, location, and other fields"""
        cylinders = self.db.load_data()
        query = query.lower()
        
        results = []
        for cylinder in cylinders:
            # Search across multiple fields
            searchable_fields = [
                cylinder.get('serial_number', ''),
                cylinder.get('custom_id', ''),
                cylinder.get('type', ''),
                cylinder.get('status', ''),
                cylinder.get('location', ''),
                cylinder.get('size', ''),
                cylinder.get('pressure', ''),
                cylinder.get('notes', ''),
                cylinder.get('id', '')
            ]
            
            # Check if query matches any field
            for field_value in searchable_fields:
                if query in str(field_value).lower():
                    results.append(cylinder)
                    break  # Avoid duplicates
        
        return results
    
    def get_by_status(self, status: str) -> List[Dict]:
        """Get cylinders by status"""
        cylinders = self.db.load_data()
        return [c for c in cylinders if c.get('status', '').lower() == status.lower()]
    
    def get_by_customer(self, customer_id: str) -> List[Dict]:
        """Get all cylinders rented by a specific customer"""
        cylinders = self.db.load_data()
        return [c for c in cylinders if c.get('rented_to') == customer_id]
    
    def rent_cylinder(self, cylinder_id: str, customer_id: str, rental_date: str = None) -> bool:
        """Rent a cylinder to a customer with rental date"""
        from datetime import datetime
        from models import Customer
        
        cylinders = self.db.load_data()
        for cylinder in cylinders:
            if cylinder['id'] == cylinder_id:
                if cylinder.get('status', '').lower() != 'available':
                    return False
                
                # Get customer information
                customer_model = Customer()
                customer = customer_model.get_by_id(customer_id)
                if not customer:
                    return False
                
                cylinder['status'] = 'rented'
                cylinder['rented_to'] = customer_id
                cylinder['customer_name'] = customer.get('name', '')
                cylinder['customer_email'] = customer.get('email', '')
                cylinder['rental_date'] = rental_date or datetime.now().isoformat()
                cylinder['date_borrowed'] = rental_date or datetime.now().isoformat()
                # Clear any previous return date
                cylinder['date_returned'] = ''
                cylinder['updated_at'] = datetime.now().isoformat()
                self.db.save_data(cylinders)
                return True
        return False
    
    def return_cylinder(self, cylinder_id: str, return_date: str = None) -> bool:
        """Return a cylinder from rental with return date"""
        from datetime import datetime
        
        cylinders = self.db.load_data()
        for cylinder in cylinders:
            if cylinder['id'] == cylinder_id:
                cylinder['status'] = 'available'
                cylinder['date_returned'] = return_date or datetime.now().isoformat()
                cylinder['updated_at'] = datetime.now().isoformat()
                # Clear customer assignment but keep rental history for tracking
                cylinder['rented_to'] = ''
                cylinder['customer_name'] = ''
                cylinder['customer_email'] = ''
                cylinder['rental_date'] = ''
                self.db.save_data(cylinders)
                return True
        return False
    
    def get_rental_days(self, cylinder: Dict) -> int:
        """Calculate how many days a cylinder has been rented"""
        # Try to use date_borrowed first, then fall back to rental_date
        date_to_use = cylinder.get('date_borrowed') or cylinder.get('rental_date')
        if not date_to_use:
            return 0
        
        try:
            from datetime import datetime
            rental_date = datetime.fromisoformat(date_to_use.replace('Z', '+00:00').split('.')[0])
            return (datetime.now() - rental_date).days
        except:
            return 0
    
    def get_by_rental_duration(self, duration_months: int) -> List[Dict]:
        """Get cylinders rented for a specific duration or longer"""
        cylinders = self.db.load_data()
        results = []
        
        for cylinder in cylinders:
            if cylinder.get('status', '').lower() == 'rented' and cylinder.get('rental_date'):
                rental_days = self.get_rental_days(cylinder)
                duration_days = duration_months * 30  # Approximate months to days
                
                if rental_days >= duration_days:
                    results.append(cylinder)
        
        return results
    
    def archive_old_data(self, months_old: int = 6) -> Dict[str, int]:
        """Archive data older than specified months and create backup"""
        from datetime import datetime, timedelta
        import json
        import os
        
        cutoff_date = datetime.now() - timedelta(days=months_old * 30)
        cylinders = self.db.load_data()
        
        active_cylinders = []
        archived_cylinders = []
        
        for cylinder in cylinders:
            # Check if cylinder has old data
            created_at = cylinder.get('created_at')
            updated_at = cylinder.get('updated_at')
            rental_date = cylinder.get('rental_date')
            
            # Determine if cylinder should be archived
            should_archive = False
            
            # If cylinder is available and old
            if cylinder.get('status', '').lower() == 'available':
                if created_at:
                    try:
                        created_date = datetime.fromisoformat(created_at.replace('Z', '+00:00').split('.')[0])
                        if created_date < cutoff_date:
                            should_archive = True
                    except:
                        pass
            
            # If cylinder was returned long ago
            elif cylinder.get('status', '').lower() == 'available' and not rental_date:
                if updated_at:
                    try:
                        updated_date = datetime.fromisoformat(updated_at.replace('Z', '+00:00').split('.')[0])
                        if updated_date < cutoff_date:
                            should_archive = True
                    except:
                        pass
            
            if should_archive:
                archived_cylinders.append(cylinder)
            else:
                active_cylinders.append(cylinder)
        
        # Create archived data backup
        if archived_cylinders:
            self._ensure_data_directory()
            archive_filename = f"data/cylinders_archive_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            
            try:
                with open(archive_filename, 'w') as f:
                    json.dump(archived_cylinders, f, indent=2)
                
                # Update main data file with only active cylinders
                self.db.save_data(active_cylinders)
                
                return {
                    'archived_count': len(archived_cylinders),
                    'remaining_count': len(active_cylinders),
                    'archive_file': archive_filename
                }
            except Exception as e:
                return {
                    'error': f"Failed to create archive: {str(e)}",
                    'archived_count': 0,
                    'remaining_count': len(cylinders)
                }
        
        return {
            'archived_count': 0,
            'remaining_count': len(cylinders),
            'message': 'No data to archive'
        }
    
    def _ensure_data_directory(self):
        """Create data directory if it doesn't exist"""
        import os
        if not os.path.exists('data'):
            os.makedirs('data')
