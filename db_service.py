# db_service.py - Database service layer for PostgreSQL operations
from typing import List, Dict, Optional, Tuple, Any
from datetime import datetime, timedelta
from sqlalchemy import func, and_, or_, desc, asc, case
from app import db
from models import Customer, Cylinder, RentalHistory
import uuid

class DatabaseService:
    """Service layer for database operations using Flask-SQLAlchemy"""
    
    def __init__(self):
        self.db = db.session
    
    def _ensure_connection(self):
        """Ensure database connection is alive, reconnect if needed"""
        try:
            # Test the connection with a simple query
            from sqlalchemy import text
            self.db.execute(text("SELECT 1"))
        except Exception as e:
            print(f"Database connection lost, reconnecting: {e}")
            try:
                self.db.rollback()
            except:
                pass
    
    def close(self):
        """Close database session"""
        try:
            self.db.commit()
        except Exception as e:
            self.db.rollback()
            print(f"Database close error: {e}")
    
    def __enter__(self):
        """Context manager entry"""
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

class CustomerService(DatabaseService):
    """Customer database operations"""
    
    def get_all(self, search_query: str = None, page: int = 1, per_page: int = 25) -> Tuple[List[Customer], int]:
        """Get all customers with optional search and pagination"""
        self._ensure_connection()
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
        
        # Apply pagination with optimized sorting
        offset = (page - 1) * per_page
        
        # Simple ordering by customer name for better performance
        # Join with cylinders only when needed for specific queries
        customers = query.order_by(Customer.customer_name).offset(offset).limit(per_page).all()
        
        return customers, total_count
    
    def get_by_id(self, customer_id: str) -> Optional[Customer]:
        """Get customer by ID"""
        self._ensure_connection()
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
            
            if rental_duration_filter == 'under_1':
                cutoff_date = current_date - timedelta(days=30)
                query = query.filter(and_(
                    Cylinder.status == 'rented',
                    Cylinder.date_borrowed >= cutoff_date
                ))
            elif rental_duration_filter == '1_to_3':
                start_date = current_date - timedelta(days=90)
                end_date = current_date - timedelta(days=30)
                query = query.filter(and_(
                    Cylinder.status == 'rented',
                    Cylinder.date_borrowed >= start_date,
                    Cylinder.date_borrowed < end_date
                ))
            elif rental_duration_filter == '3_to_6':
                start_date = current_date - timedelta(days=180)
                end_date = current_date - timedelta(days=90)
                query = query.filter(and_(
                    Cylinder.status == 'rented',
                    Cylinder.date_borrowed >= start_date,
                    Cylinder.date_borrowed < end_date
                ))
            elif rental_duration_filter == '6_to_12':
                start_date = current_date - timedelta(days=365)
                end_date = current_date - timedelta(days=180)
                query = query.filter(and_(
                    Cylinder.status == 'rented',
                    Cylinder.date_borrowed >= start_date,
                    Cylinder.date_borrowed < end_date
                ))
            elif rental_duration_filter == 'over_12':
                cutoff_date = current_date - timedelta(days=365)
                query = query.filter(and_(
                    Cylinder.status == 'rented',
                    Cylinder.date_borrowed < cutoff_date
                ))
        
        total_count = query.count()
        
        # Optimized sorting for performance
        offset = (page - 1) * per_page
        
        # Sort cylinders: rented first (by dispatch date descending - longest dispatch first)
        cylinders = query.order_by(
            case(
                (Cylinder.status == 'rented', 0),  # Rented cylinders first
                (Cylinder.status == 'dispatched', 0),  # Dispatched cylinders first (same priority as rented)
                (Cylinder.status == 'available', 1),  # Available cylinders second
                else_=2  # Others last (maintenance, etc.)
            ),
            # For rented/dispatched cylinders: sort by date_borrowed ascending (oldest dispatch = longest rental first)
            Cylinder.date_borrowed.asc().nulls_last(),
            # For available cylinders: sort by custom_id
            Cylinder.custom_id.asc().nulls_last()
        ).offset(offset).limit(per_page).all()
        
        # Convert SQLAlchemy objects to dictionaries for template compatibility
        cylinders_dict = []
        for cylinder in cylinders:
            cylinder_dict = {
                'id': cylinder.id,
                'custom_id': cylinder.custom_id or '',
                'serial_number': cylinder.serial_number or '',
                'type': cylinder.type or 'Medical Oxygen',
                'size': cylinder.size or '40L',
                'status': cylinder.status or 'available',
                'location': cylinder.location or 'Warehouse',
                'pressure': getattr(cylinder, 'pressure', ''),  # Safe access with default
                'last_inspection': getattr(cylinder, 'last_inspection', None),
                'next_inspection': getattr(cylinder, 'next_inspection', None),
                'notes': getattr(cylinder, 'notes', ''),
                'rented_to': cylinder.rented_to,
                'customer_name': cylinder.customer_name or '',
                'customer_no': cylinder.customer_no or '',
                'date_borrowed': cylinder.date_borrowed.isoformat() if cylinder.date_borrowed else '',
                'date_returned': cylinder.date_returned.isoformat() if cylinder.date_returned else '',
                'created_at': cylinder.created_at.isoformat() if cylinder.created_at else '',
                'updated_at': cylinder.updated_at.isoformat() if cylinder.updated_at else ''
            }
            
            # Format inspection dates safely
            if cylinder_dict['last_inspection'] and hasattr(cylinder_dict['last_inspection'], 'isoformat'):
                cylinder_dict['last_inspection'] = cylinder_dict['last_inspection'].isoformat()
            elif not cylinder_dict['last_inspection']:
                cylinder_dict['last_inspection'] = ''
                
            if cylinder_dict['next_inspection'] and hasattr(cylinder_dict['next_inspection'], 'isoformat'):
                cylinder_dict['next_inspection'] = cylinder_dict['next_inspection'].isoformat()
            elif not cylinder_dict['next_inspection']:
                cylinder_dict['next_inspection'] = ''
            
            # Calculate rental days for rented cylinders
            if cylinder.status == 'rented' and cylinder.date_borrowed:
                rental_days = (datetime.utcnow() - cylinder.date_borrowed).days
                cylinder_dict['rental_days'] = rental_days
                cylinder_dict['rental_months'] = rental_days // 30
            else:
                cylinder_dict['rental_days'] = 0
                cylinder_dict['rental_months'] = 0
                
            # Generate display ID
            cylinder_dict['display_id'] = cylinder.custom_id or cylinder.serial_number or f"ID-{cylinder.id[:8]}"
            
            cylinders_dict.append(cylinder_dict)
        
        return cylinders_dict, total_count
    
    def get_by_id(self, cylinder_id: str) -> Optional[Cylinder]:
        """Get cylinder by ID"""
        return self.db.query(Cylinder).filter(Cylinder.id == cylinder_id).first()
    
    def find_by_any_identifier(self, identifier: str) -> Optional[Dict]:
        """
        Find cylinder by any identifier (system ID, custom ID, or serial number).
        Returns a dictionary representation for compatibility.
        """
        if not identifier:
            return None
            
        # Try to find by custom_id first (most common use case)
        cylinder = self.db.query(Cylinder).filter(Cylinder.custom_id == identifier).first()
        
        # If not found, try by system ID
        if not cylinder:
            cylinder = self.db.query(Cylinder).filter(Cylinder.id == identifier).first()
        
        # If still not found, try by serial_number
        if not cylinder:
            cylinder = self.db.query(Cylinder).filter(Cylinder.serial_number == identifier).first()
        
        if not cylinder:
            return None
            
        # Convert to dictionary for compatibility
        return {
            'id': cylinder.id,
            'custom_id': cylinder.custom_id or '',
            'serial_number': cylinder.serial_number or '',
            'type': cylinder.type or 'Medical Oxygen',
            'size': cylinder.size or '40L',
            'status': cylinder.status or 'available',
            'location': cylinder.location or 'Warehouse',
            'pressure': getattr(cylinder, 'pressure', ''),
            'last_inspection': getattr(cylinder, 'last_inspection', None),
            'next_inspection': getattr(cylinder, 'next_inspection', None),
            'notes': getattr(cylinder, 'notes', ''),
            'rented_to': cylinder.rented_to,
            'customer_name': cylinder.customer_name or '',
            'customer_no': cylinder.customer_no or '',
            'date_borrowed': cylinder.date_borrowed.isoformat() if cylinder.date_borrowed else '',
            'date_returned': cylinder.date_returned.isoformat() if cylinder.date_returned else '',
            'created_at': cylinder.created_at.isoformat() if cylinder.created_at else '',
            'updated_at': cylinder.updated_at.isoformat() if cylinder.updated_at else ''
        }
    
    def get_by_customer(self, customer_id: str) -> List[Dict]:
        """Get cylinders rented/dispatched by customer, returning dictionaries"""
        cylinders = self.db.query(Cylinder).filter(
            and_(Cylinder.rented_to == customer_id, Cylinder.status.in_(['rented', 'dispatched']))
        ).all()
        
        # Convert to dictionaries for template compatibility
        cylinders_dict = []
        for cylinder in cylinders:
            cylinder_dict = {
                'id': cylinder.id,
                'custom_id': cylinder.custom_id or '',
                'serial_number': cylinder.serial_number or '',
                'type': cylinder.type or 'Medical Oxygen',
                'size': cylinder.size or '40L',
                'status': cylinder.status or 'rented',
                'location': cylinder.location or 'Warehouse',
                'pressure': getattr(cylinder, 'pressure', ''),
                'last_inspection': getattr(cylinder, 'last_inspection', ''),
                'next_inspection': getattr(cylinder, 'next_inspection', ''),
                'notes': getattr(cylinder, 'notes', ''),
                'rented_to': cylinder.rented_to,
                'customer_name': cylinder.customer_name or '',
                'customer_no': cylinder.customer_no or '',
                'date_borrowed': cylinder.date_borrowed.isoformat() if cylinder.date_borrowed else '',
                'date_returned': cylinder.date_returned.isoformat() if cylinder.date_returned else '',
                'created_at': cylinder.created_at.isoformat() if cylinder.created_at else '',
                'updated_at': cylinder.updated_at.isoformat() if cylinder.updated_at else ''
            }
            
            # Calculate rental days for active cylinders
            if cylinder.status == 'rented' and cylinder.date_borrowed:
                rental_days = (datetime.utcnow() - cylinder.date_borrowed).days
                cylinder_dict['rental_days'] = rental_days
                cylinder_dict['rental_months'] = rental_days // 30
            else:
                cylinder_dict['rental_days'] = 0
                cylinder_dict['rental_months'] = 0
                
            # Generate display ID
            cylinder_dict['display_id'] = cylinder.custom_id or cylinder.serial_number or f"ID-{cylinder.id[:8]}"
            
            cylinders_dict.append(cylinder_dict)
        
        return cylinders_dict
    
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
    
    def update_exact(self, cylinder_id: str, cylinder_data: Dict) -> bool:
        """Update cylinder with exact data preservation"""
        try:
            cylinder = self.db.query(Cylinder).filter(Cylinder.id == cylinder_id).first()
            if not cylinder:
                return False
            
            # Update all fields exactly as provided
            for field, value in cylinder_data.items():
                if hasattr(cylinder, field):
                    setattr(cylinder, field, value)
            
            self.db.commit()
            return True
        except Exception as e:
            self.db.rollback()
            print(f"Error updating cylinder: {e}")
            return False
    
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
        if not cylinder or cylinder.status.lower() != 'available':
            return False
        
        # Get customer info and extract data while in session
        customer_service = CustomerService()
        customer = customer_service.get_by_id(customer_id)
        
        if not customer:
            customer_service.close()
            return False
        
        # Extract all customer data while still in session to avoid DetachedInstanceError
        customer_data = {
            'customer_name': customer.customer_name if hasattr(customer, 'customer_name') else '',
            'customer_email': customer.customer_email if hasattr(customer, 'customer_email') else '',
            'customer_phone': customer.customer_phone if hasattr(customer, 'customer_phone') else '',
            'customer_no': customer.customer_no if hasattr(customer, 'customer_no') else '',
            'customer_city': customer.customer_city if hasattr(customer, 'customer_city') else '',
            'customer_state': customer.customer_state if hasattr(customer, 'customer_state') else '',
            'customer_address': customer.customer_address if hasattr(customer, 'customer_address') else ''
        }
        customer_service.close()
        
        # Update cylinder with rental info using extracted data  
        cylinder.status = 'dispatched'  # Use 'dispatched' as the primary rental status
        cylinder.rented_to = customer_id
        cylinder.customer_name = customer_data['customer_name']
        cylinder.customer_email = customer_data['customer_email']
        cylinder.customer_phone = customer_data['customer_phone']
        cylinder.customer_no = customer_data['customer_no']
        cylinder.customer_city = customer_data['customer_city']
        cylinder.customer_state = customer_data['customer_state']
        # Update location to customer's address or city
        location_parts = []
        if customer_data['customer_address']:
            location_parts.append(customer_data['customer_address'])
        if customer_data['customer_city']:
            location_parts.append(customer_data['customer_city'])
        if customer_data['customer_state']:
            location_parts.append(customer_data['customer_state'])
        
        cylinder.location = ', '.join(location_parts) if location_parts else 'Customer Location'
        
        if rental_date:
            try:
                # Parse rental_date and convert to datetime object
                if isinstance(rental_date, str):
                    if 'T' in rental_date:
                        cylinder.date_borrowed = datetime.fromisoformat(rental_date.replace('Z', '+00:00'))
                    else:
                        cylinder.date_borrowed = datetime.strptime(rental_date, '%Y-%m-%d')
                else:
                    cylinder.date_borrowed = rental_date
            except:
                cylinder.date_borrowed = datetime.utcnow()
        else:
            cylinder.date_borrowed = datetime.utcnow()
        
        cylinder.updated_at = datetime.utcnow()
        self.db.commit()
        return True
    
    def return_cylinder(self, cylinder_id: str, return_date: str = None) -> bool:
        """Return cylinder from rental"""
        self._ensure_connection()
        cylinder = self.get_by_id(cylinder_id)
        if not cylinder or cylinder.status.lower() not in ['rented', 'dispatched']:
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
                # Parse return_date and convert to datetime object
                if isinstance(return_date, str):
                    if 'T' in return_date:
                        cylinder.date_returned = datetime.fromisoformat(return_date.replace('Z', '+00:00'))
                    else:
                        cylinder.date_returned = datetime.strptime(return_date, '%Y-%m-%d')
                else:
                    cylinder.date_returned = return_date
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
        
        # Clear rental dates to prevent sorting issues
        cylinder.date_borrowed = None
        
        cylinder.updated_at = datetime.utcnow().isoformat()
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
        self._ensure_connection()
        
        query = self.db.query(RentalHistory)
        total_count = query.count()
        
        # For web interface, get larger chunks but still paginate for performance
        offset = (page - 1) * per_page
        history = query.order_by(desc(RentalHistory.return_date)).offset(offset).limit(per_page).all()
        
        return history, total_count
    
    def get_by_cylinder(self, cylinder_id: str) -> List[RentalHistory]:
        """Get rental history for a specific cylinder"""
        self._ensure_connection()
        
        history = self.db.query(RentalHistory).filter(
            RentalHistory.cylinder_no == cylinder_id
        ).order_by(desc(RentalHistory.return_date)).limit(10).all()
        
        return history
    
    def get_customer_history(self, customer_id: str) -> Dict:
        """Get customer's rental history split into active and past"""
        # Get customer to find customer_no for matching
        customer_service = CustomerService()
        customer = customer_service.get_by_id(customer_id)
        customer_service.close()
        
        if not customer:
            return {'active': [], 'past': []}
        
        # Get past rental history using both customer_id and customer_no for broader matching
        customer_no = getattr(customer, 'customer_no', '') if customer else ''
        past_rentals = self.db.query(RentalHistory).filter(
            or_(
                RentalHistory.customer_id == customer_id,
                RentalHistory.customer_no == customer_no
            )
        ).order_by(desc(RentalHistory.return_date)).limit(50).all()
    
    def get_customer_monthly_history(self, customer_id: str, year: int = None) -> Dict:
        """Get customer's rental history organized by month"""
        from datetime import datetime
        from collections import defaultdict
        import calendar
        
        # Get customer to find customer_no for matching
        customer_service = CustomerService()
        customer = customer_service.get_by_id(customer_id)
        customer_service.close()
        
        if not customer:
            return {'monthly_data': [], 'available_years': []}
        
        # Get all rental history for this customer
        customer_no = getattr(customer, 'customer_no', '') if customer else ''
        all_history = self.db.query(RentalHistory).filter(
            RentalHistory.customer_no == customer_no
        ).order_by(desc(RentalHistory.dispatch_date)).all()
        
        # Also get current active rentals
        cylinder_service = CylinderService()
        active_cylinders = cylinder_service.get_by_customer(customer_id)
        cylinder_service.close()
        
        # Organize by year and month
        monthly_data = defaultdict(lambda: {
            'dispatches': 0,
            'returns': 0,
            'transactions': [],
            'top_cylinders': [],
            'total_transactions': 0
        })
        
        available_years = set()
        
        # Process rental history
        for rental in all_history:
            if rental.dispatch_date:
                rental_year = rental.dispatch_date.year
                rental_month = rental.dispatch_date.month
                available_years.add(rental_year)
                
                if year is None or rental_year == year:
                    month_key = f"{rental_year}-{rental_month:02d}"
                    monthly_data[month_key]['dispatches'] += 1
                    monthly_data[month_key]['total_transactions'] += 1
                    
                    transaction_data = {
                        'date': rental.dispatch_date,
                        'cylinder_id': rental.cylinder_no,
                        'cylinder_no': rental.cylinder_no,
                        'cylinder_type': rental.cylinder_type,
                        'rental_date': rental.dispatch_date,
                        'return_date': rental.return_date
                    }
                    monthly_data[month_key]['transactions'].append(transaction_data)
                    
                    if rental.return_date:
                        return_year = rental.return_date.year
                        return_month = rental.return_date.month
                        return_month_key = f"{return_year}-{return_month:02d}"
                        
                        if year is None or return_year == year:
                            monthly_data[return_month_key]['returns'] += 1
                            if return_month_key != month_key:
                                monthly_data[return_month_key]['total_transactions'] += 1
                                monthly_data[return_month_key]['transactions'].append({
                                    'date': rental.return_date,
                                    'cylinder_id': rental.cylinder_no,
                                    'cylinder_no': rental.cylinder_no,
                                    'cylinder_type': rental.cylinder_type,
                                    'rental_date': rental.dispatch_date,
                                    'return_date': rental.return_date
                                })
        
        # Process active cylinders (count as dispatches for their rental month)
        for cylinder in active_cylinders:
            if cylinder.get('date_borrowed'):
                try:
                    if isinstance(cylinder['date_borrowed'], str):
                        rental_date = datetime.fromisoformat(cylinder['date_borrowed'].replace('Z', '+00:00'))
                    else:
                        rental_date = cylinder['date_borrowed']
                    
                    rental_year = rental_date.year
                    rental_month = rental_date.month
                    available_years.add(rental_year)
                    
                    if year is None or rental_year == year:
                        month_key = f"{rental_year}-{rental_month:02d}"
                        monthly_data[month_key]['dispatches'] += 1
                        monthly_data[month_key]['total_transactions'] += 1
                        
                        monthly_data[month_key]['transactions'].append({
                            'date': rental_date,
                            'cylinder_id': cylinder.get('display_id', cylinder.get('id')),
                            'cylinder_no': cylinder.get('custom_id'),
                            'cylinder_type': cylinder.get('type', 'O2'),
                            'rental_date': rental_date,
                            'return_date': None
                        })
                except:
                    pass  # Skip invalid date formats
        
        # Convert to sorted list with month names
        result_data = []
        for month_key in sorted(monthly_data.keys(), reverse=True):
            year_month = month_key.split('-')
            month_year = int(year_month[0])
            month_num = int(year_month[1])
            
            month_info = monthly_data[month_key]
            month_info.update({
                'year': month_year,
                'month': month_num,
                'month_name': calendar.month_name[month_num]
            })
            
            # Sort transactions by date
            month_info['transactions'].sort(key=lambda x: x['date'] or datetime.min, reverse=True)
            
            # Get top cylinders by frequency
            cylinder_counts = defaultdict(int)
            for trans in month_info['transactions']:
                cyl_id = trans['cylinder_id'] or trans['cylinder_no'] or 'Unknown'
                cylinder_counts[cyl_id] += 1
            
            month_info['top_cylinders'] = [
                {'display_id': cyl_id, 'count': count} 
                for cyl_id, count in sorted(cylinder_counts.items(), key=lambda x: x[1], reverse=True)
            ]
            
            result_data.append(month_info)
        
        return {
            'monthly_data': result_data,
            'available_years': sorted(available_years, reverse=True)
        }
        
        # Convert to dictionaries
        past_dict = []
        for rental in past_rentals:
            rental_dict = {
                'id': rental.id,
                'customer_name': rental.customer_name or '',
                'customer_no': rental.customer_no or '',
                'cylinder_custom_id': rental.cylinder_custom_id or '',
                'cylinder_type': rental.cylinder_type or '',
                'cylinder_size': rental.cylinder_size or '',
                'dispatch_date': rental.dispatch_date.isoformat() if rental.dispatch_date else '',
                'return_date': rental.return_date.isoformat() if rental.return_date else '',
                'rental_days': rental.rental_days or 0
            }
            past_dict.append(rental_dict)
        
        return {
            'active': [],  # Active rentals are handled by CylinderService
            'past': past_dict
        }
    
    def get_customer_history(self, customer_id: str) -> Dict[str, List]:
        """Get customer rental history (active and past)"""
        # Get active rentals
        cylinder_service = CylinderService()
        active_cylinders = cylinder_service.get_by_customer(customer_id)
        cylinder_service.close()
        
        # Get customer info for matching
        customer_service = CustomerService()
        customer = customer_service.get_by_id(customer_id)
        
        if not customer:
            customer_service.close()
            return {'active': [], 'past': []}
        
        # Extract customer_no before closing the session
        customer_no = getattr(customer, 'customer_no', '') if customer else ''
        customer_service.close()
        
        # Get past rentals from history (only completed rentals with return dates)
        past_rentals = self.db.query(RentalHistory).filter(
            and_(
                RentalHistory.customer_no == customer_no,
                RentalHistory.return_date.isnot(None)  # Only completed rentals
            )
        ).order_by(desc(RentalHistory.return_date)).all()
        
        print(f"DEBUG: Found {len(past_rentals)} past rentals for customer_no: {customer_no}")
        
        # Import Customer model for lookups
        from models import Customer
        
        # Convert past rentals to dictionaries for template compatibility
        past_dict = []
        for rental in past_rentals:
            # If customer_name is missing, try to get it from the customers table
            customer_name = rental.customer_name or ''
            if not customer_name and rental.customer_no:
                # Try to find customer name from customers table
                try:
                    customer_lookup = self.db.query(Customer).filter(
                        Customer.customer_no == rental.customer_no
                    ).first()
                    if customer_lookup:
                        customer_name = customer_lookup.customer_name or ''
                except:
                    pass
            
            # If still no customer name, use a placeholder based on customer_no
            if not customer_name and rental.customer_no:
                customer_name = f"Customer {rental.customer_no}"
            elif not customer_name:
                customer_name = "Unknown Customer"
            
            rental_dict = {
                'id': rental.id,
                'customer_name': customer_name,
                'customer_no': rental.customer_no or '',
                'cylinder_custom_id': rental.cylinder_custom_id or rental.cylinder_serial or '',
                'cylinder_serial': rental.cylinder_serial or '',
                'cylinder_type': rental.cylinder_type or '',
                'cylinder_size': rental.cylinder_size or '',
                'dispatch_date': rental.dispatch_date.isoformat() if rental.dispatch_date else '',
                'return_date': rental.return_date.isoformat() if rental.return_date else '',
                'rental_days': rental.rental_days or 0,
                'type': rental.cylinder_type or '',  # Template compatibility
                'size': rental.cylinder_size or '',   # Template compatibility
                'date_borrowed': rental.dispatch_date.isoformat() if rental.dispatch_date else '',  # Template compatibility
                'date_returned': rental.return_date.isoformat() if rental.return_date else ''  # Template compatibility
            }
            past_dict.append(rental_dict)
        
        return {
            'active': active_cylinders,
            'past': past_dict
        }
    
    def add_return_record(self, cylinder: Cylinder, return_date: str = None):
        """Add return record to history"""
        self._ensure_connection()
        
        if not return_date:
            return_date_dt = datetime.utcnow()
        else:
            try:
                return_date_dt = datetime.fromisoformat(return_date.replace('Z', '+00:00'))
            except:
                return_date_dt = datetime.utcnow()
        
        # Calculate rental days - simplified approach
        rental_days = 1  # Default to 1 day
        
        # Create history record matching the Render database schema exactly
        history_record = RentalHistory(
            customer_id=cylinder.rented_to or '',  # Add customer_id field
            customer_no=cylinder.customer_no or '',
            customer_name=cylinder.customer_name or '',
            customer_phone=cylinder.customer_phone or '',
            customer_email=cylinder.customer_email or '',  # Add customer_email field
            customer_address=cylinder.customer_address or '',
            customer_city=cylinder.customer_city or '',
            customer_state=cylinder.customer_state or '',
            cylinder_id=cylinder.id,  # Add cylinder_id field
            cylinder_no=cylinder.id,
            cylinder_custom_id=cylinder.custom_id or '',
            cylinder_serial=cylinder.serial_number or '',
            cylinder_type=cylinder.type or '',
            cylinder_size=cylinder.size or '',
            dispatch_date=cylinder.date_borrowed if cylinder.date_borrowed else return_date_dt,
            return_date=return_date_dt if return_date_dt else None,
            date_borrowed=cylinder.date_borrowed if cylinder.date_borrowed else return_date_dt,  # Add date_borrowed field
            date_returned=return_date_dt if return_date_dt else None,  # Add date_returned field
            rental_days=rental_days,
            location=cylinder.location or 'Unknown',  # Add location field
            status='completed'
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
    
    def create_history_record(self, history_data: Dict[str, Any]) -> RentalHistory:
        """Create a new rental history record"""
        self._ensure_connection()
        
        # Generate unique ID
        record_id = str(uuid.uuid4())
        
        # Create rental history record
        rental_history = RentalHistory(
            id=record_id,
            customer_no=history_data.get('customer_no', ''),
            customer_name=history_data.get('customer_name', ''),
            customer_phone=history_data.get('customer_phone', ''),
            customer_address=history_data.get('customer_address', ''),
            customer_city=history_data.get('customer_city', ''),
            customer_state=history_data.get('customer_state', ''),
            cylinder_no=history_data.get('cylinder_no', ''),
            cylinder_custom_id=history_data.get('cylinder_custom_id', ''),
            cylinder_serial=history_data.get('cylinder_serial', ''),
            cylinder_type=history_data.get('cylinder_type', ''),
            cylinder_size=history_data.get('cylinder_size', ''),
            dispatch_date=self._parse_date_string(history_data.get('dispatch_date', '')),
            return_date=self._parse_date_string(history_data.get('return_date', '')),
            rental_days=history_data.get('rental_days', 0),
            status=history_data.get('status', 'completed'),
            created_at=self._parse_date_string(history_data.get('created_at', datetime.now().isoformat()))
        )
        
        self.db.add(rental_history)
        self.db.commit()
        self.db.refresh(rental_history)
        
        return rental_history
    
    def _parse_date_string(self, date_str: str):
        """Parse date string to date object for dispatch_date/return_date or datetime for created_at"""
        if not date_str:
            return None
            
        try:
            # Handle ISO format with or without timezone
            if 'T' in date_str:
                if date_str.endswith('Z'):
                    date_str = date_str[:-1] + '+00:00'
                dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                # For created_at, return datetime; for dates, return date
                return dt
            else:
                # Handle date-only format - return as date
                return datetime.strptime(date_str, '%Y-%m-%d').date()
        except:
            return None