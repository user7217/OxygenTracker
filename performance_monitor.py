#!/usr/bin/env python3
"""
Performance monitoring utility for Oxygen Cylinder Tracker
Tracks database query performance and identifies bottlenecks
"""

import time
import logging
from functools import wraps
from datetime import datetime

# Set up performance logging
logging.basicConfig(level=logging.INFO)
performance_logger = logging.getLogger('performance')

class PerformanceMonitor:
    """Monitor database query performance"""
    
    def __init__(self):
        self.query_times = []
        self.slow_queries = []
        
    def log_query_time(self, query_name, execution_time):
        """Log query execution time"""
        self.query_times.append({
            'query': query_name,
            'time': execution_time,
            'timestamp': datetime.now()
        })
        
        # Log slow queries (over 1 second)
        if execution_time > 1.0:
            self.slow_queries.append({
                'query': query_name,
                'time': execution_time,
                'timestamp': datetime.now()
            })
            performance_logger.warning(f"SLOW QUERY: {query_name} took {execution_time:.2f}s")
        
    def get_performance_stats(self):
        """Get performance statistics"""
        if not self.query_times:
            return {
                'avg_time': 0,
                'total_queries': 0,
                'slow_queries': 0
            }
        
        total_time = sum(q['time'] for q in self.query_times)
        avg_time = total_time / len(self.query_times)
        
        return {
            'avg_time': avg_time,
            'total_queries': len(self.query_times),
            'slow_queries': len(self.slow_queries),
            'total_time': total_time
        }

# Global performance monitor instance
monitor = PerformanceMonitor()

def track_performance(query_name):
    """Decorator to track database query performance"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                execution_time = time.time() - start_time
                monitor.log_query_time(query_name, execution_time)
        return wrapper
    return decorator

def optimize_query_hints():
    """Provide query optimization hints"""
    stats = monitor.get_performance_stats()
    
    hints = []
    
    if stats['avg_time'] > 0.5:
        hints.append("Consider adding database indexes for frequently queried fields")
    
    if stats['slow_queries'] > 5:
        hints.append("Multiple slow queries detected - consider query optimization")
    
    if len(monitor.query_times) > 1000:
        hints.append("High query volume - consider implementing caching")
    
    return hints

def clear_performance_data():
    """Clear performance monitoring data"""
    monitor.query_times.clear()
    monitor.slow_queries.clear()
    performance_logger.info("Performance monitoring data cleared")