# Standalone Data Import Guide

This guide explains how to use the standalone data importer to import data from MS Access databases into your Varasai Oxygen system.

## Requirements

Before using the importer, make sure you have:

1. **Python packages installed**: The same packages as the main application
   - `pyodbc` for MS Access connectivity
   - `pandas` for data processing
   - All other packages from the main application

2. **MS Access driver**: Install the Microsoft Access Database Engine
   - Download from Microsoft's website
   - Choose the version that matches your Python installation (32-bit or 64-bit)

3. **Data directory**: The `data/` folder should exist with your existing JSON files

## Basic Usage

### 0. Check Current Data

Before importing, you can see what data is already in your system:

```bash
python standalone_importer.py show_summary
```

This shows current customer and cylinder counts, plus cylinder status breakdown.

### 1. List Available Tables

First, see what tables are available in your Access database:

```bash
python standalone_importer.py list_tables your_database.accdb
```

This will show you all tables in the database file.

### 2. Preview Table Structure

Before importing, preview a table to understand its structure:

```bash
python standalone_importer.py preview_table your_database.accdb TableName
```

This shows the column names and first 5 rows of data.

### 3. Import Data

#### Import Customers
```bash
python standalone_importer.py import_customers your_database.accdb Customers
```

#### Import Cylinders  
```bash
python standalone_importer.py import_cylinders your_database.accdb Cylinders
```

#### Import Transactions (links customers to cylinders)
```bash
python standalone_importer.py import_transactions your_database.accdb Transactions
```

## Expected Table Structure

### Customer Table
Your Access table should have these columns (or similar):
- `customer_no` - Customer number/ID
- `customer_name` - Customer name
- `customer_address` - Address
- `customer_city` - City
- `customer_state` - State
- `customer_phone` - Phone number
- `customer_apgst` - AP GST number (optional)
- `customer_cst` - CST number (optional)
- `customer_email` - Email address (optional)

### Cylinder Table
Your Access table should have these columns (or similar):
- `serial_number` - Cylinder serial number
- `type` - Type (Medical Oxygen, CO2, etc.)
- `size` - Cylinder size
- `location` - Current location (defaults to "Warehouse")
- `status` - Status (defaults to "Available")
- `custom_id` - Custom ID (optional)

### Transaction Table
Your Access table should have these columns (or similar):
- `customer_no` - Customer number (must match customer table)
- `cylinder_no` - Cylinder serial number (must match cylinder table)
- `rental_date` - Date when cylinder was rented
- `return_date` - Date when cylinder was returned (leave empty if still rented)

## Import Process

The importer follows this process:

1. **Customers**: Import all customers, skip duplicates based on customer number, name, or phone
   - Each customer gets a unique system ID in format: `CUST-XXXXXXXX`
   - Original customer numbers are preserved in the `customer_no` field
   - System generates timestamps for created_at and updated_at

2. **Cylinders**: Import all cylinders, skip duplicates based on serial number or custom ID  
   - Each cylinder gets a unique system ID in format: `CYL-XXXXXXXX`
   - Original serial numbers are preserved in the `serial_number` field
   - Custom IDs are preserved in the `custom_id` field (if provided)
   - System generates timestamps for created_at and updated_at

3. **Transactions**: Link customers and cylinders based on the transaction data
   - Uses customer_no and cylinder serial numbers to find existing records
   - If `return_date` is empty: Cylinder stays "Rented" to customer
   - If `return_date` has value: Cylinder is "Available" at warehouse

## Field Mapping

If your Access database has different column names, you can modify the field mappings in the `import_config.json` file or directly in the `standalone_importer.py` script.

### Example: Different Column Names

If your Access database uses different column names like:
- `CustomerID` instead of `customer_no`
- `CustomerName` instead of `customer_name`
- `SerialNumber` instead of `serial_number`

You can modify the mapping functions in the script or use the alternative mapping in `import_config.json`.

## Examples

### Complete Import Process

1. **Check your database structure:**
```bash
python standalone_importer.py list_tables company_data.accdb
python standalone_importer.py preview_table company_data.accdb Customers
python standalone_importer.py preview_table company_data.accdb Cylinders
```

2. **Import in order:**
```bash
# Import customers first
python standalone_importer.py import_customers company_data.accdb Customers

# Import cylinders second
python standalone_importer.py import_cylinders company_data.accdb Cylinders

# Import transactions last (requires customers and cylinders to exist)
python standalone_importer.py import_transactions company_data.accdb Rentals
```

### Output Examples

The importer provides detailed feedback:

```
🚀 Varasai Oxygen - Standalone Data Importer
📁 Database: company_data.accdb
==================================================
🔄 Starting customer import from 'Customers'...
✅ Imported customer: ABC Company
✅ Imported customer: XYZ Industries  
⚠️  Skipping duplicate customer: ABC Company
❌ Error importing customer row: Missing required field

📊 Customer Import Summary:
   ✅ Successfully imported: 25
   ⚠️  Duplicates skipped: 3
   ❌ Errors: 1
```

## Troubleshooting

### Common Issues

1. **"Access database file not found"**
   - Check the file path is correct
   - Make sure the .accdb file exists

2. **"Failed to connect to Access database"**
   - Install Microsoft Access Database Engine
   - Make sure the driver matches your Python installation (32/64-bit)

3. **"Customer/Cylinder not found" during transaction import**
   - Import customers and cylinders before transactions
   - Check that customer_no and cylinder_no in transactions match existing records

4. **"Missing required field" errors**
   - Check your table structure matches expected format
   - Modify field mappings if column names are different

### Getting Help

If you encounter issues:
1. Use the preview function to check your table structure
2. Check the error messages for specific field or format issues
3. Verify your Access database driver installation
4. Make sure all required Python packages are installed

## Advanced Usage

### Custom Field Mapping

You can modify the field mapping by editing the functions in `standalone_importer.py`:

```python
def _get_default_customer_mapping(self) -> Dict[str, str]:
    return {
        'customer_no': 'YourCustomerIDField',
        'customer_name': 'YourCustomerNameField',
        # ... add your mappings
    }
```

### Batch Processing

You can create a batch script to import multiple tables:

```bash
#!/bin/bash
echo "Starting batch import..."
python standalone_importer.py import_customers database.accdb Customers
python standalone_importer.py import_cylinders database.accdb Cylinders  
python standalone_importer.py import_transactions database.accdb Transactions
echo "Batch import completed!"
```

## Testing the Importer

Before using with real data, you can test the importer functionality:

```bash
python test_import.py
```

This test script verifies that:
- ID generation works correctly (CUST-XXXXXXXX and CYL-XXXXXXXX formats)
- Customer and cylinder import logic functions properly
- Duplicate detection works as expected
- All timestamps and metadata are correctly generated

## Summary

This standalone importer gives you the same powerful import capabilities as the web interface, but in a command-line tool that you can use independently or integrate into your own workflows.

### Key Features:
- **Unique ID Generation**: Every customer gets CUST-XXXXXXXX, every cylinder gets CYL-XXXXXXXX
- **Duplicate Detection**: Prevents importing the same data twice
- **Preserve Original Data**: Your original customer numbers and serial numbers are preserved
- **Transaction Linking**: Links customers to cylinders based on rental transactions
- **Comprehensive Logging**: Shows exactly what was imported, skipped, or failed
- **Data Summary**: Shows current data status before and after imports

The importer handles all the same field mapping, validation, and relationship management as the web application, making it perfect for bulk imports, automated workflows, or when you prefer command-line tools.