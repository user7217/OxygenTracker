#!/usr/bin/env python3
"""
Rental Transactions Model
Handles completed rental transactions for the past 6 months
"""

import json
import os
from datetime import datetime, timedelta
from typing import List, Dict, Optional

class RentalTransactions:
    def __init__(self):
        self.data_file = 'data/rental_transactions.json'
        self.ensure_data_directory()
    
    def ensure_data_directory(self):
        """Ensure data directory exists"""
        os.makedirs('data', exist_ok=True)
        if not os.path.exists(self.data_file):
            with open(self.data_file, 'w') as f:
                json.dump([], f)
    
    def get_all(self) -> List[Dict]:
        """Get all rental transactions"""
        try:
            with open(self.data_file, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return []
    
    def get_by_customer(self, customer_no: str) -> List[Dict]:
        """Get rental transactions for a specific customer"""
        all_transactions = self.get_all()
        return [t for t in all_transactions if t.get('customer_no', '').upper() == customer_no.upper()]
    
    def get_recent_transactions(self, months: int = 6) -> List[Dict]:
        """Get transactions from the past X months"""
        cutoff_date = datetime.now() - timedelta(days=months * 30)
        all_transactions = self.get_all()
        
        recent = []
        for transaction in all_transactions:
            return_date = transaction.get('return_date', '')
            if return_date:
                try:
                    return_dt = datetime.strptime(return_date, '%Y-%m-%d')
                    if return_dt >= cutoff_date:
                        recent.append(transaction)
                except:
                    pass
        
        return recent
    
    def add_transaction(self, transaction: Dict) -> bool:
        """Add a single rental transaction"""
        try:
            transactions = self.get_all()
            
            # Generate ID if not provided
            if 'id' not in transaction:
                transaction['id'] = f"RT-{datetime.now().strftime('%Y%m%d%H%M%S')}-{len(transactions):04d}"
            
            # Set created timestamp
            transaction['created_at'] = datetime.now().isoformat()
            
            transactions.append(transaction)
            
            with open(self.data_file, 'w') as f:
                json.dump(transactions, f, indent=2)
            
            return True
        except Exception as e:
            print(f"Error adding transaction: {e}")
            return False
    
    def bulk_add_transactions(self, transactions: List[Dict]) -> int:
        """Add multiple rental transactions"""
        try:
            existing_transactions = self.get_all()
            
            # Add IDs and timestamps
            for i, transaction in enumerate(transactions):
                if 'id' not in transaction:
                    transaction['id'] = f"RT-{datetime.now().strftime('%Y%m%d%H%M%S')}-{len(existing_transactions) + i:04d}"
                transaction['created_at'] = datetime.now().isoformat()
            
            all_transactions = existing_transactions + transactions
            
            with open(self.data_file, 'w') as f:
                json.dump(all_transactions, f, indent=2)
            
            return len(transactions)
        except Exception as e:
            print(f"Error bulk adding transactions: {e}")
            return 0
    
    def clear_all(self):
        """Clear all rental transactions"""
        with open(self.data_file, 'w') as f:
            json.dump([], f)
    
    def get_customer_summary(self, customer_no: str) -> Dict:
        """Get rental summary for a customer"""
        transactions = self.get_by_customer(customer_no)
        
        total_rentals = len(transactions)
        active_rentals = len([t for t in transactions if not t.get('return_date')])
        returned_rentals = len([t for t in transactions if t.get('return_date')])
        
        # Calculate average rental duration
        durations = []
        for transaction in transactions:
            if transaction.get('dispatch_date') and transaction.get('return_date'):
                try:
                    dispatch = datetime.strptime(transaction['dispatch_date'], '%Y-%m-%d')
                    return_date = datetime.strptime(transaction['return_date'], '%Y-%m-%d')
                    duration = (return_date - dispatch).days
                    if duration > 0:
                        durations.append(duration)
                except:
                    pass
        
        avg_duration = sum(durations) / len(durations) if durations else 0
        
        return {
            'customer_no': customer_no,
            'total_rentals': total_rentals,
            'active_rentals': active_rentals,
            'returned_rentals': returned_rentals,
            'average_duration_days': round(avg_duration, 1),
            'recent_transactions': transactions[:5]  # Most recent 5
        }