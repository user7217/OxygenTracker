# models_postgres.py - PostgreSQL-backed models replacing JSON storage
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
from db_service import CustomerService, CylinderService, RentalHistoryService
from db_models import get_db_session

class Customer:
    """Customer model using PostgreSQL backend"""
    
    def __init__(self):
        pass
    
    def get_all(self, search_query: str = None, page: int = 1, per_page: int = 25) -> Tuple[List[Dict], int]:
        """Get all customers with search and pagination"""
        with CustomerService() as service:
            customers, total_count = service.get_all(search_query, page, per_page)
            return [self._to_dict(c) for c in customers], total_count
    
    def get_by_id(self, customer_id: str) -> Optional[Dict]:
        """Get customer by ID"""
        with CustomerService() as service:
            customer = service.get_by_id(customer_id)
            return self._to_dict(customer) if customer else None
    
    def add_customer(self, customer_data: Dict) -> str:
        """Add new customer and return ID"""
        with CustomerService() as service:
            customer = service.create(customer_data)
            return customer.id
    
    def update_customer(self, customer_id: str, customer_data: Dict) -> bool:
        """Update customer"""
        with CustomerService() as service:
            return service.update(customer_id, customer_data)
    
    def delete_customer(self, customer_id: str) -> bool:
        """Delete customer"""
        with CustomerService() as service:
            return service.delete(customer_id)
    
    def _to_dict(self, customer) -> Dict:
        """Convert SQLAlchemy object to dictionary"""
        if not customer:
            return {}
        
        return {
            'id': customer.id,
            'customer_no': customer.customer_no or '',
            'customer_name': customer.customer_name or '',
            'customer_email': customer.customer_email or '',
            'customer_phone': customer.customer_phone or '',
            'customer_address': customer.customer_address or '',
            'customer_city': customer.customer_city or '',
            'customer_state': customer.customer_state or '',
            'customer_apgst': customer.customer_apgst or '',
            'customer_cst': customer.customer_cst or '',
            'created_at': customer.created_at.isoformat() if customer.created_at else '',
            'updated_at': customer.updated_at.isoformat() if customer.updated_at else '',
            # Legacy field mappings for compatibility
            'name': customer.customer_name or '',
            'email': customer.customer_email or '',
            'phone': customer.customer_phone or '',
            'address': customer.customer_address or '',
            'city': customer.customer_city or '',
            'state': customer.customer_state or ''
        }

class Cylinder:
    """Cylinder model using PostgreSQL backend"""
    
    def __init__(self):
        pass
    
    def get_all(self, search_query: str = None, page: int = 1, per_page: int = 25,
                         filter_type: str = None, filter_status: str = None,
                         rental_duration_filter: str = None, customer_filter: str = None) -> Tuple[List[Dict], int]:
        """Get all cylinders with filters and pagination"""
        with CylinderService() as service:
            cylinders, total_count = service.get_all(
                search_query, page, per_page, filter_type, 
                filter_status, rental_duration_filter, customer_filter
            )
            return [self._to_dict(c) for c in cylinders], total_count
    
    def get_by_id(self, cylinder_id: str) -> Optional[Dict]:
        """Get cylinder by ID"""
        with CylinderService() as service:
            cylinder = service.get_by_id(cylinder_id)
            return self._to_dict(cylinder) if cylinder else None
    
    def get_by_customer(self, customer_id: str) -> List[Dict]:
        """Get cylinders rented by customer"""
        with CylinderService() as service:
            cylinders = service.get_by_customer(customer_id)
            return [self._to_dict(c) for c in cylinders]
    
    def add_cylinder(self, cylinder_data: Dict) -> str:
        """Add new cylinder and return ID"""
        with CylinderService() as service:
            cylinder = service.create(cylinder_data)
            return cylinder.id
    
    def update_cylinder(self, cylinder_id: str, cylinder_data: Dict) -> bool:
        """Update cylinder"""
        with CylinderService() as service:
            return service.update(cylinder_id, cylinder_data)
    
    def rent_cylinder(self, cylinder_id: str, customer_id: str, rental_date: str = None) -> bool:
        """Rent cylinder to customer"""
        with CylinderService() as service:
            return service.rent_cylinder(cylinder_id, customer_id, rental_date)
    
    def return_cylinder(self, cylinder_id: str, return_date: str = None) -> bool:
        """Return cylinder from rental"""
        with CylinderService() as service:
            return service.return_cylinder(cylinder_id, return_date)
    
    def delete_cylinder(self, cylinder_id: str) -> bool:
        """Delete cylinder"""
        with CylinderService() as service:
            return service.delete(cylinder_id)
    
    def get_display_id(self, cylinder) -> str:
        """Get display ID for cylinder (custom_id or serial_number)"""
        if isinstance(cylinder, dict):
            return cylinder.get('custom_id') or cylinder.get('serial_number') or 'Unknown'
        elif hasattr(cylinder, 'custom_id'):
            return cylinder.custom_id or cylinder.serial_number or 'Unknown'
        else:
            return 'Unknown'
    
    def get_rental_days(self, cylinder) -> int:
        """Calculate rental days for a cylinder"""
        if isinstance(cylinder, dict):
            date_borrowed = cylinder.get('date_borrowed')
        elif hasattr(cylinder, 'date_borrowed'):
            date_borrowed = cylinder.date_borrowed
        else:
            return 0
            
        if not date_borrowed:
            return 0
        
        # Convert to datetime if it's a string
        if isinstance(date_borrowed, str):
            try:
                date_borrowed = datetime.fromisoformat(date_borrowed.replace('Z', '+00:00'))
            except:
                return 0
        
        return (datetime.utcnow() - date_borrowed).days
    
    def get_rental_months(self, cylinder) -> int:
        """Calculate rental months for a cylinder"""
        days = self.get_rental_days(cylinder)
        return max(0, days // 30)
    
    def _to_dict(self, cylinder) -> Dict:
        """Convert SQLAlchemy object to dictionary"""
        if not cylinder:
            return {}
        
        # Calculate rental information
        rental_days = self.get_rental_days(cylinder)
        rental_months = self.get_rental_months(cylinder)
        display_id = self.get_display_id(cylinder)
        
        return {
            'id': cylinder.id,
            'custom_id': cylinder.custom_id or '',
            'serial_number': cylinder.serial_number or '',
            'type': cylinder.type or 'Medical Oxygen',
            'size': cylinder.size or '40L',
            'status': cylinder.status or 'available',
            'location': cylinder.location or 'Warehouse',
            'rented_to': cylinder.rented_to or '',
            'customer_name': cylinder.customer_name or '',
            'customer_email': cylinder.customer_email or '',
            'customer_phone': cylinder.customer_phone or '',
            'customer_no': cylinder.customer_no or '',
            'customer_city': cylinder.customer_city or '',
            'customer_state': cylinder.customer_state or '',
            'date_borrowed': cylinder.date_borrowed.isoformat() if cylinder.date_borrowed else '',
            'rental_date': cylinder.rental_date.isoformat() if cylinder.rental_date else '',
            'date_returned': cylinder.date_returned.isoformat() if cylinder.date_returned else '',
            'created_at': cylinder.created_at.isoformat() if cylinder.created_at else '',
            'updated_at': cylinder.updated_at.isoformat() if cylinder.updated_at else '',
            # Calculated fields
            'rental_days': rental_days,
            'rental_months': rental_months,
            'display_id': display_id
        }