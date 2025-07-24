# db_service.py - Database service layer for PostgreSQL operations
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
from sqlalchemy import func, and_, or_, desc, asc
from sqlalchemy.orm import Session
from db_models import get_db_session, Customer, Cylinder, RentalHistory
import uuid

class DatabaseService:
    """Service layer for database operations"""
    
    def __init__(self):
        self.db = get_db_session()
    
    def close(self):
        """Close database connection"""
        if self.db:
            try:
                self.db.close()
            except Exception as e:
                # Handle SSL connection closed errors gracefully
                print(f"Database close error (ignored): {e}")
                pass
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

class CustomerService(DatabaseService):
    """Customer database operations"""
    
    def get_all(self, search_query: str = None, page: int = 1, per_page: int = 25) -> Tuple[List[Customer], int]:
        """Get all customers with optional search and pagination"""
        query = self.db.query(Customer)
        
        if search_query:
            search_filter = or_(
                Customer.customer_name.ilike(f'%{search_query}%'),
                Customer.customer_no.ilike(f'%{search_query}%'),
                Customer.customer_phone.ilike(f'%{search_query}%'),
                Customer.customer_email.ilike(f'%{search_query}%'),
                Customer.customer_city.ilike(f'%{search_query}%')
            )
            query = query.filter(search_filter)
        
        total_count = query.count()
        
        # Apply pagination
        offset = (page - 1) * per_page
        customers = query.order_by(Customer.customer_name).offset(offset).limit(per_page).all()
        
        return customers, total_count
    
    def get_by_id(self, customer_id: str) -> Optional[Customer]:
        """Get customer by ID"""
        return self.db.query(Customer).filter(Customer.id == customer_id).first()
    
    def get_by_customer_no(self, customer_no: str) -> Optional[Customer]:
        """Get customer by customer number"""
        return self.db.query(Customer).filter(Customer.customer_no == customer_no).first()
    
    def create(self, customer_data: Dict) -> Customer:
        """Create new customer"""
        customer = Customer(
            id=str(uuid.uuid4()),
            customer_no=customer_data.get('customer_no', ''),
            customer_name=customer_data.get('customer_name', ''),
            customer_email=customer_data.get('customer_email', ''),
            customer_phone=customer_data.get('customer_phone', ''),
            customer_address=customer_data.get('customer_address', ''),
            customer_city=customer_data.get('customer_city', ''),
            customer_state=customer_data.get('customer_state', ''),
            customer_apgst=customer_data.get('customer_apgst', ''),
            customer_cst=customer_data.get('customer_cst', ''),
            created_at=datetime.utcnow()
        )
        
        self.db.add(customer)
        self.db.commit()
        return customer
    
    def update(self, customer_id: str, customer_data: Dict) -> bool:
        """Update customer"""
        customer = self.get_by_id(customer_id)
        if not customer:
            return False
        
        for key, value in customer_data.items():
            if hasattr(customer, key):
                setattr(customer, key, value)
        
        customer.updated_at = datetime.utcnow()
        self.db.commit()
        return True
    
    def delete(self, customer_id: str) -> bool:
        """Delete customer"""
        customer = self.get_by_id(customer_id)
        if not customer:
            return False
        
        self.db.delete(customer)
        self.db.commit()
        return True

class CylinderService(DatabaseService):
    """Cylinder database operations"""
    
    def get_all(self, search_query: str = None, page: int = 1, per_page: int = 25, 
                filter_type: str = None, filter_status: str = None, 
                rental_duration_filter: str = None, customer_filter: str = None) -> Tuple[List[Cylinder], int]:
        """Get all cylinders with filters and pagination"""
        query = self.db.query(Cylinder)
        
        # Apply filters
        if search_query:
            search_filter = or_(
                Cylinder.custom_id.ilike(f'%{search_query}%'),
                Cylinder.serial_number.ilike(f'%{search_query}%'),
                Cylinder.customer_name.ilike(f'%{search_query}%'),
                Cylinder.customer_no.ilike(f'%{search_query}%')
            )
            query = query.filter(search_filter)
        
        if filter_type:
            query = query.filter(Cylinder.type == filter_type)
        
        if filter_status:
            query = query.filter(Cylinder.status == filter_status)
        
        if customer_filter:
            query = query.filter(Cylinder.rented_to == customer_filter)
        
        # Rental duration filter
        if rental_duration_filter and rental_duration_filter != 'all':
            current_date = datetime.utcnow()
            
            if rental_duration_filter == 'under_1_month':
                cutoff_date = current_date - timedelta(days=30)
                query = query.filter(and_(
                    Cylinder.status == 'rented',
                    Cylinder.date_borrowed >= cutoff_date
                ))
            elif rental_duration_filter == '1_to_3_months':
                start_date = current_date - timedelta(days=90)
                end_date = current_date - timedelta(days=30)
                query = query.filter(and_(
                    Cylinder.status == 'rented',
                    Cylinder.date_borrowed >= start_date,
                    Cylinder.date_borrowed < end_date
                ))
            elif rental_duration_filter == '3_to_6_months':
                start_date = current_date - timedelta(days=180)
                end_date = current_date - timedelta(days=90)
                query = query.filter(and_(
                    Cylinder.status == 'rented',
                    Cylinder.date_borrowed >= start_date,
                    Cylinder.date_borrowed < end_date
                ))
            elif rental_duration_filter == '6_to_12_months':
                start_date = current_date - timedelta(days=365)
                end_date = current_date - timedelta(days=180)
                query = query.filter(and_(
                    Cylinder.status == 'rented',
                    Cylinder.date_borrowed >= start_date,
                    Cylinder.date_borrowed < end_date
                ))
            elif rental_duration_filter == 'over_12_months':
                cutoff_date = current_date - timedelta(days=365)
                query = query.filter(and_(
                    Cylinder.status == 'rented',
                    Cylinder.date_borrowed < cutoff_date
                ))
        
        total_count = query.count()
        
        # Apply sorting - sort by rental days descending (longest rentals first)
        offset = (page - 1) * per_page
        cylinders = query.order_by(
            Cylinder.date_borrowed.asc().nulls_last()  # Oldest rental dates first = longest rentals
        ).offset(offset).limit(per_page).all()
        
        return cylinders, total_count
    
    def get_by_id(self, cylinder_id: str) -> Optional[Cylinder]:
        """Get cylinder by ID"""
        return self.db.query(Cylinder).filter(Cylinder.id == cylinder_id).first()
    
    def get_by_customer(self, customer_id: str) -> List[Cylinder]:
        """Get cylinders rented by customer"""
        return self.db.query(Cylinder).filter(
            and_(Cylinder.rented_to == customer_id, Cylinder.status == 'rented')
        ).all()
    
    def create(self, cylinder_data: Dict) -> Cylinder:
        """Create new cylinder"""
        cylinder = Cylinder(
            id=str(uuid.uuid4()),
            custom_id=cylinder_data.get('custom_id', ''),
            serial_number=cylinder_data.get('serial_number', ''),
            type=cylinder_data.get('type', 'Medical Oxygen'),
            size=cylinder_data.get('size', '40L'),
            status=cylinder_data.get('status', 'available'),
            location=cylinder_data.get('location', 'Warehouse'),
            created_at=datetime.utcnow()
        )
        
        self.db.add(cylinder)
        self.db.commit()
        return cylinder
    
    def update(self, cylinder_id: str, cylinder_data: Dict) -> bool:
        """Update cylinder"""
        cylinder = self.get_by_id(cylinder_id)
        if not cylinder:
            return False
        
        # Handle rented_to field - ensure it's None for empty values to avoid FK constraint violations
        if 'rented_to' in cylinder_data:
            rented_to = cylinder_data['rented_to']
            if rented_to == '' or rented_to is None or str(rented_to).strip() == '':
                cylinder_data['rented_to'] = None
        
        for key, value in cylinder_data.items():
            if hasattr(cylinder, key):
                setattr(cylinder, key, value)
        
        cylinder.updated_at = datetime.utcnow()
        
        try:
            self.db.commit()
            return True
        except Exception as e:
            self.db.rollback()
            print(f"Error updating cylinder: {e}")
            return False
    
    def rent_cylinder(self, cylinder_id: str, customer_id: str, rental_date: str = None) -> bool:
        """Rent cylinder to customer"""
        cylinder = self.get_by_id(cylinder_id)
        if not cylinder or cylinder.status != 'available':
            return False
        
        # Get customer info
        customer_service = CustomerService()
        customer = customer_service.get_by_id(customer_id)
        customer_service.close()
        
        if not customer:
            return False
        
        # Update cylinder with rental info
        cylinder.status = 'rented'
        cylinder.rented_to = customer_id
        cylinder.customer_name = customer.customer_name
        cylinder.customer_email = customer.customer_email
        cylinder.customer_phone = customer.customer_phone
        cylinder.customer_no = customer.customer_no
        cylinder.customer_city = customer.customer_city
        cylinder.customer_state = customer.customer_state
        cylinder.location = customer.customer_address or customer.customer_city
        
        if rental_date:
            try:
                cylinder.date_borrowed = datetime.fromisoformat(rental_date.replace('Z', '+00:00'))
                cylinder.rental_date = cylinder.date_borrowed
            except:
                cylinder.date_borrowed = datetime.utcnow()
                cylinder.rental_date = cylinder.date_borrowed
        else:
            cylinder.date_borrowed = datetime.utcnow()
            cylinder.rental_date = cylinder.date_borrowed
        
        cylinder.updated_at = datetime.utcnow()
        self.db.commit()
        return True
    
    def return_cylinder(self, cylinder_id: str, return_date: str = None) -> bool:
        """Return cylinder from rental"""
        cylinder = self.get_by_id(cylinder_id)
        if not cylinder or cylinder.status != 'rented':
            return False
        
        # Save to rental history before updating
        if cylinder.rented_to:
            history_service = RentalHistoryService()
            history_service.add_return_record(cylinder, return_date)
            history_service.close()
        
        # Update cylinder status
        cylinder.status = 'available'
        cylinder.location = 'Warehouse'
        
        if return_date:
            try:
                cylinder.date_returned = datetime.fromisoformat(return_date.replace('Z', '+00:00'))
            except:
                cylinder.date_returned = datetime.utcnow()
        else:
            cylinder.date_returned = datetime.utcnow()
        
        # Clear rental info (use None for foreign key to avoid constraint violation)
        cylinder.rented_to = None
        cylinder.customer_name = ''
        cylinder.customer_email = ''
        cylinder.customer_phone = ''
        cylinder.customer_no = ''
        cylinder.customer_city = ''
        cylinder.customer_state = ''
        
        cylinder.updated_at = datetime.utcnow()
        self.db.commit()
        return True
    
    def delete(self, cylinder_id: str) -> bool:
        """Delete cylinder"""
        cylinder = self.get_by_id(cylinder_id)
        if not cylinder:
            return False
        
        self.db.delete(cylinder)
        self.db.commit()
        return True

class RentalHistoryService(DatabaseService):
    """Rental history database operations"""
    
    def get_all(self, page: int = 1, per_page: int = 1000) -> Tuple[List[RentalHistory], int]:
        """Get all rental history with pagination"""
        query = self.db.query(RentalHistory)
        total_count = query.count()
        
        # For web interface, get larger chunks but still paginate for performance
        offset = (page - 1) * per_page
        history = query.order_by(desc(RentalHistory.return_date)).offset(offset).limit(per_page).all()
        
        return history, total_count
    
    def get_customer_history(self, customer_id: str) -> Dict[str, List]:
        """Get customer rental history (active and past)"""
        # Get active rentals
        cylinder_service = CylinderService()
        active_cylinders = cylinder_service.get_by_customer(customer_id)
        cylinder_service.close()
        
        # Get customer info for matching
        customer_service = CustomerService()
        customer = customer_service.get_by_id(customer_id)
        customer_service.close()
        
        if not customer:
            return {'active': [], 'past': []}
        
        # Get past rentals from history
        past_rentals = self.db.query(RentalHistory).filter(
            or_(
                RentalHistory.customer_id == customer_id,
                RentalHistory.customer_no == customer.customer_no
            )
        ).order_by(desc(RentalHistory.return_date)).all()
        
        return {
            'active': active_cylinders,
            'past': past_rentals
        }
    
    def add_return_record(self, cylinder: Cylinder, return_date: str = None):
        """Add return record to history"""
        if not return_date:
            return_date_dt = datetime.utcnow()
        else:
            try:
                return_date_dt = datetime.fromisoformat(return_date.replace('Z', '+00:00'))
            except:
                return_date_dt = datetime.utcnow()
        
        # Calculate rental days
        rental_days = 0
        if cylinder.date_borrowed:
            rental_days = max(0, (return_date_dt - cylinder.date_borrowed).days)
        
        history_record = RentalHistory(
            id=str(uuid.uuid4()),
            customer_id=cylinder.rented_to,
            customer_no=cylinder.customer_no,
            customer_name=cylinder.customer_name,
            customer_phone=cylinder.customer_phone,
            customer_email=cylinder.customer_email,
            customer_city=cylinder.customer_city,
            customer_state=cylinder.customer_state,
            cylinder_id=cylinder.id,
            cylinder_custom_id=cylinder.custom_id,
            cylinder_serial=cylinder.serial_number,
            cylinder_type=cylinder.type,
            cylinder_size=cylinder.size,
            dispatch_date=cylinder.date_borrowed,
            return_date=return_date_dt,
            date_borrowed=cylinder.date_borrowed,
            date_returned=return_date_dt,
            rental_days=rental_days,
            location=cylinder.location,
            status='completed',
            created_at=datetime.utcnow()
        )
        
        self.db.add(history_record)
        self.db.commit()
        return history_record
    
    def cleanup_old_records(self) -> int:
        """Remove records older than 6 months"""
        six_months_ago = datetime.utcnow() - timedelta(days=180)
        
        old_records = self.db.query(RentalHistory).filter(
            RentalHistory.return_date < six_months_ago
        )
        
        count = old_records.count()
        old_records.delete()
        self.db.commit()
        
        return count