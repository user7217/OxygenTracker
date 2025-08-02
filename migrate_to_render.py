"""
Replit to Render Migration Tool
Export data from current Replit database and prepare for Render import
"""

import os
import json
import psycopg2
from datetime import datetime
from typing import Dict, List, Any
from db_service import CustomerService, CylinderService

class ReplitToRenderMigrator:
    """Export Replit data and prepare for Render import"""
    
    def __init__(self):
        self.replit_db_url = os.environ.get('DATABASE_URL')
        
    def export_all_data(self) -> Dict[str, Any]:
        """Export all data from current Replit database"""
        export_data = {
            'export_info': {
                'exported_at': datetime.now().isoformat(),
                'source': 'Replit',
                'destination': 'Render',
                'app_name': 'Varasicyl'
            },
            'customers': [],
            'cylinders': []
        }
        
        try:
            # Export customers
            with CustomerService() as customer_service:
                customers, _ = customer_service.get_all(page=1, per_page=100000)
                for customer in customers:
                    customer_dict = {
                        'id': customer.id if hasattr(customer, 'id') else customer.get('id'),
                        'customer_no': customer.customer_no if hasattr(customer, 'customer_no') else customer.get('customer_no'),
                        'customer_name': customer.customer_name if hasattr(customer, 'customer_name') else customer.get('customer_name'),
                        'customer_email': customer.customer_email if hasattr(customer, 'customer_email') else customer.get('customer_email'),
                        'customer_phone': customer.customer_phone if hasattr(customer, 'customer_phone') else customer.get('customer_phone'),
                        'customer_address': customer.customer_address if hasattr(customer, 'customer_address') else customer.get('customer_address'),
                        'customer_city': customer.customer_city if hasattr(customer, 'customer_city') else customer.get('customer_city'),
                        'customer_state': customer.customer_state if hasattr(customer, 'customer_state') else customer.get('customer_state'),
                        'created_at': str(customer.created_at) if hasattr(customer, 'created_at') and customer.created_at else customer.get('created_at', '')
                    }
                    export_data['customers'].append(customer_dict)
            
            # Export cylinders
            with CylinderService() as cylinder_service:
                cylinders, _ = cylinder_service.get_all(page=1, per_page=100000)
                for cylinder in cylinders:
                    cylinder_dict = cylinder_service.to_dict(cylinder)
                    export_data['cylinders'].append(cylinder_dict)
            
            export_data['stats'] = {
                'total_customers': len(export_data['customers']),
                'total_cylinders': len(export_data['cylinders']),
                'active_rentals': len([c for c in export_data['cylinders'] if c.get('status', '').lower() in ['rented', 'dispatched']])
            }
            
            return export_data
            
        except Exception as e:
            return {'error': f'Export failed: {str(e)}'}
    
    def create_render_migration_package(self) -> Dict[str, str]:
        """Create complete migration package for Render deployment"""
        try:
            # Export all data
            export_data = self.export_all_data()
            
            if 'error' in export_data:
                return export_data
            
            # Create migration files
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            migration_dir = f'render_migration_{timestamp}'
            os.makedirs(migration_dir, exist_ok=True)
            
            # 1. Full data export
            data_file = f'{migration_dir}/varasicyl_complete_data.json'
            with open(data_file, 'w') as f:
                json.dump(export_data, f, indent=2, default=str)
            
            # 2. Customers only export
            customers_file = f'{migration_dir}/customers_export.json'
            with open(customers_file, 'w') as f:
                json.dump(export_data['customers'], f, indent=2, default=str)
            
            # 3. Cylinders only export
            cylinders_file = f'{migration_dir}/cylinders_export.json'
            with open(cylinders_file, 'w') as f:
                json.dump(export_data['cylinders'], f, indent=2, default=str)
            
            # 4. Create migration instructions
            instructions_file = f'{migration_dir}/MIGRATION_INSTRUCTIONS.md'
            with open(instructions_file, 'w') as f:
                f.write(self._generate_migration_instructions(export_data['stats']))
            
            # 5. Create SQL backup (for direct database import)
            sql_file = f'{migration_dir}/database_backup.sql'
            self._create_sql_backup(sql_file, export_data)
            
            return {
                'success': True,
                'migration_dir': migration_dir,
                'files_created': [
                    'varasicyl_complete_data.json',
                    'customers_export.json', 
                    'cylinders_export.json',
                    'MIGRATION_INSTRUCTIONS.md',
                    'database_backup.sql'
                ],
                'stats': export_data['stats']
            }
            
        except Exception as e:
            return {'error': f'Migration package creation failed: {str(e)}'}
    
    def _generate_migration_instructions(self, stats: Dict) -> str:
        """Generate detailed migration instructions"""
        return f"""# Varasicyl Migration from Replit to Render

## Migration Summary
- **Total Customers:** {stats['total_customers']}
- **Total Cylinders:** {stats['total_cylinders']} 
- **Active Rentals:** {stats['active_rentals']}
- **Migration Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Migration Steps

### Option 1: JSON Import (Recommended)
1. Deploy Varasicyl to Render using the existing configuration
2. Access your Render deployment admin panel
3. Go to **Import JSON Data** page
4. Import in this order:
   - Upload `customers_export.json` first
   - Then upload `cylinders_export.json`
   - Or use `varasicyl_complete_data.json` for everything at once

### Option 2: Direct Database Import
1. Connect to your Render PostgreSQL database
2. Use the `database_backup.sql` file to restore data directly
3. Run: `psql $DATABASE_URL < database_backup.sql`

### Option 3: Direct DB Connection
1. In your Render Varasicyl deployment, go to **Direct DB Import**
2. Use this Replit DATABASE_URL as connection string
3. Map fields and import directly

## Post-Migration Verification
1. Check customer count matches: {stats['total_customers']}
2. Check cylinder count matches: {stats['total_cylinders']}
3. Verify active rentals: {stats['active_rentals']}
4. Test customer active dispatches display
5. Test bulk operations and reporting

## Files Included
- `varasicyl_complete_data.json` - Complete export (customers + cylinders)
- `customers_export.json` - Customers only
- `cylinders_export.json` - Cylinders only  
- `database_backup.sql` - SQL backup for direct database restore
- `MIGRATION_INSTRUCTIONS.md` - This file

## Important Notes
- All dispatched/rented cylinders include customer linking data
- Customer relationships are preserved in cylinder records
- Rental history and dates are maintained
- Status field supports both 'rented' and 'dispatched' values

## Support
- Use the JSON import method for easiest migration
- The smart update system will handle existing records
- Backup your Render database before import if you have existing data
"""
    
    def _create_sql_backup(self, sql_file: str, export_data: Dict) -> None:
        """Create SQL backup file for direct database restore"""
        with open(sql_file, 'w') as f:
            f.write("-- Varasicyl Database Backup for Render Migration\n")
            f.write(f"-- Generated: {datetime.now()}\n")
            f.write("-- Source: Replit\n\n")
            
            f.write("-- Clear existing data (uncomment if needed)\n")
            f.write("-- DELETE FROM rental_history;\n")
            f.write("-- DELETE FROM cylinders;\n") 
            f.write("-- DELETE FROM customers;\n\n")
            
            # Insert customers
            f.write("-- Insert Customers\n")
            for customer in export_data['customers']:
                values = []
                for field in ['customer_no', 'customer_name', 'customer_email', 'customer_phone', 
                            'customer_address', 'customer_city', 'customer_state']:
                    value = customer.get(field, '')
                    if value is None:
                        values.append('NULL')
                    else:
                        # Escape single quotes
                        escaped_value = str(value).replace("'", "''")
                        values.append(f"'{escaped_value}'")
                
                f.write(f"INSERT INTO customers (customer_no, customer_name, customer_email, customer_phone, customer_address, customer_city, customer_state, created_at) VALUES ({', '.join(values)}, NOW());\n")
            
            f.write("\n-- Insert Cylinders\n")
            for cylinder in export_data['cylinders']:
                # Build cylinder insert with proper field mapping
                fields = ['serial_number', 'custom_id', 'type', 'size', 'status', 'location', 
                         'pressure', 'date_borrowed', 'date_returned', 'customer_name', 
                         'customer_phone', 'customer_address']
                
                values = []
                for field in fields:
                    value = cylinder.get(field, '')
                    if value is None or value == '':
                        values.append('NULL')
                    else:
                        escaped_value = str(value).replace("'", "''")
                        values.append(f"'{escaped_value}'")
                
                # Add rented_to lookup if customer exists
                rented_to = 'NULL'
                if cylinder.get('customer_name'):
                    rented_to = f"(SELECT id FROM customers WHERE customer_name = '{cylinder.get('customer_name', '').replace(\"'\", \"''\")}' LIMIT 1)"
                
                values.append(rented_to)
                
                field_names = ', '.join(fields + ['rented_to'])
                f.write(f"INSERT INTO cylinders ({field_names}, created_at) VALUES ({', '.join(values)}, NOW());\n")
    
    def get_render_connection_info(self) -> Dict[str, str]:
        """Get information for connecting to Render database"""
        return {
            'current_replit_url': os.environ.get('DATABASE_URL', 'Not found'),
            'render_setup_instructions': """
For Render PostgreSQL setup:
1. Add PostgreSQL service in Render dashboard
2. Use these environment variables in your Render web service:
   - DATABASE_URL (automatically provided by Render PostgreSQL)
   - SESSION_SECRET (generate a random string)
3. Deploy your Varasicyl app to Render
4. Use the migration files to import your data
            """,
            'direct_import_option': 'Use Direct DB Import feature with your Replit DATABASE_URL'
        }