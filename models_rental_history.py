# Rental History Model for Customer History Tracking
# This module handles customer rental history with active and past dispatch tracking

from datetime import datetime, timedelta
from typing import List, Dict, Optional
import json
import os

class RentalHistory:
    """Model for tracking customer rental history including past returns"""
    
    def __init__(self):
        self.db_file = os.path.join('data', 'rental_history.json')
        self._ensure_db_exists()
    
    def _ensure_db_exists(self):
        """Ensure rental history database file exists"""
        os.makedirs('data', exist_ok=True)
        if not os.path.exists(self.db_file):
            self._save_data([])
    
    def _load_data(self) -> List[Dict]:
        """Load rental history data from JSON file"""
        try:
            with open(self.db_file, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return []
    
    def _save_data(self, data: List[Dict]):
        """Save rental history data to JSON file"""
        with open(self.db_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def add_return_record(self, cylinder_data: Dict, customer_data: Dict, return_date: str = None):
        """Add a return record to history when a cylinder is returned"""
        if not return_date:
            return_date = datetime.now().isoformat()
        
        history_records = self._load_data()
        
        # Create return record
        return_record = {
            'id': f"return_{len(history_records) + 1}_{int(datetime.now().timestamp())}",
            'customer_id': customer_data.get('id', ''),
            'customer_name': customer_data.get('customer_name', '') or customer_data.get('name', ''),
            'customer_phone': customer_data.get('customer_phone', '') or customer_data.get('phone', ''),
            'customer_email': customer_data.get('customer_email', '') or customer_data.get('email', ''),
            'cylinder_id': cylinder_data.get('id', ''),
            'cylinder_custom_id': cylinder_data.get('custom_id', ''),
            'cylinder_serial': cylinder_data.get('serial_number', ''),
            'cylinder_type': cylinder_data.get('type', ''),
            'cylinder_size': cylinder_data.get('size', ''),
            'date_borrowed': cylinder_data.get('date_borrowed', '') or cylinder_data.get('rental_date', ''),
            'date_returned': return_date,
            'rental_days': self._calculate_rental_days(
                cylinder_data.get('date_borrowed', '') or cylinder_data.get('rental_date', ''),
                return_date
            ),
            'location': cylinder_data.get('location', ''),
            'created_at': datetime.now().isoformat()
        }
        
        history_records.append(return_record)
        self._save_data(history_records)
        return return_record
    
    def cleanup_old_records(self):
        """Remove rental history records older than 6 months automatically"""
        six_months_ago = datetime.now() - timedelta(days=180)
        cutoff_date = six_months_ago.isoformat()
        
        history_records = self._load_data()
        original_count = len(history_records)
        
        # Filter out records older than 6 months
        filtered_records = []
        for record in history_records:
            record_date = record.get('date_returned', record.get('created_at', ''))
            if record_date and record_date >= cutoff_date:
                filtered_records.append(record)
        
        # Save filtered data if any records were removed
        if len(filtered_records) != original_count:
            self._save_data(filtered_records)
            removed_count = original_count - len(filtered_records)
            return removed_count
        
        return 0
    
    def _calculate_rental_days(self, start_date: str, end_date: str) -> int:
        """Calculate rental days between two dates"""
        if not start_date or not end_date:
            return 0
        
        try:
            start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00').split('.')[0])
            end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00').split('.')[0])
            return max(0, (end_dt - start_dt).days)
        except:
            return 0
    
    def get_all_history(self) -> List[Dict]:
        """Get all rental history records"""
        return self._load_data()
    
    def get_customer_history(self, customer_id: str) -> Dict[str, List[Dict]]:
        """Get all rental history for a customer, separated by active and past"""
        from models import Cylinder
        
        cylinder_model = Cylinder()
        
        # Get active rentals (current cylinders rented to customer)
        active_cylinders = cylinder_model.get_by_customer(customer_id)
        
        # Add display information to active rentals
        for cylinder in active_cylinders:
            cylinder['rental_days'] = cylinder_model.get_rental_days(cylinder)
            cylinder['rental_months'] = cylinder_model.get_rental_months(cylinder)
            cylinder['display_id'] = cylinder_model.get_display_id(cylinder)
        
        # Get past rentals from history
        history_records = self._load_data()
        past_rentals = [r for r in history_records if r.get('customer_id') == customer_id]
        
        # Sort both lists by date
        active_cylinders.sort(key=lambda x: x.get('date_borrowed', ''), reverse=True)
        past_rentals.sort(key=lambda x: x.get('date_returned', ''), reverse=True)
        
        return {
            'active': active_cylinders,
            'past': past_rentals
        }
    
    def import_historical_data(self, historical_records: List[Dict], cutoff_months: int = 6):
        """Import historical rental data, excluding records older than cutoff"""
        cutoff_date = datetime.now() - timedelta(days=cutoff_months * 30)
        current_records = self._load_data()
        
        # Filter out old records during import
        valid_records = []
        skipped_count = 0
        
        for record in historical_records:
            try:
                return_date_str = record.get('date_returned', '')
                if return_date_str:
                    return_date = datetime.fromisoformat(return_date_str.replace('Z', '+00:00').split('.')[0])
                    if return_date >= cutoff_date:
                        valid_records.append(record)
                    else:
                        skipped_count += 1
                else:
                    # Include records without return date (still active)
                    valid_records.append(record)
            except:
                # Include records with parsing errors for manual review
                valid_records.append(record)
        
        # Merge with existing records (avoid duplicates)
        existing_ids = {r.get('id', '') for r in current_records}
        new_records = [r for r in valid_records if r.get('id', '') not in existing_ids]
        
        all_records = current_records + new_records
        self._save_data(all_records)
        
        return len(new_records), skipped_count
    
    def get_statistics(self) -> Dict:
        """Get rental history statistics"""
        history_records = self._load_data()
        
        if not history_records:
            return {
                'total_returns': 0,
                'avg_rental_days': 0,
                'total_rental_days': 0,
                'most_frequent_customer': None
            }
        
        total_returns = len(history_records)
        total_rental_days = sum(r.get('rental_days', 0) for r in history_records)
        avg_rental_days = total_rental_days // total_returns if total_returns > 0 else 0
        
        # Find most frequent customer
        customer_counts = {}
        for record in history_records:
            customer_name = record.get('customer_name', 'Unknown')
            customer_counts[customer_name] = customer_counts.get(customer_name, 0) + 1
        
        most_frequent_customer = max(customer_counts.items(), key=lambda x: x[1])[0] if customer_counts else None
        
        return {
            'total_returns': total_returns,
            'avg_rental_days': avg_rental_days,
            'total_rental_days': total_rental_days,
            'most_frequent_customer': most_frequent_customer,
            'customer_counts': customer_counts
        }