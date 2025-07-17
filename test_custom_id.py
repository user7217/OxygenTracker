"""
Test script to verify custom ID functionality
"""

from models import Cylinder

def test_custom_id_functionality():
    """Test the custom ID feature"""
    print("Testing Custom ID Functionality")
    print("=" * 40)
    
    cylinder_model = Cylinder()
    
    test_cylinder = {
        'custom_id': 'A1',
        'serial_number': 'TEST001',
        'type': 'Medical Oxygen',
        'size': 'Large (20L)',
        'status': 'Available',
        'location': 'Warehouse',
        'pressure': '2000'
    }
    
    print("1. Adding cylinder with custom ID 'A1'...")
    new_cylinder = cylinder_model.add(test_cylinder)
    print(f"   ✓ Created cylinder: {new_cylinder['id']} with custom ID: {new_cylinder.get('custom_id', 'None')}")
    
    print("\n2. Finding cylinder by custom ID...")
    found_cylinder = cylinder_model.find_by_any_identifier('A1')
    if found_cylinder:
        print(f"   ✓ Found cylinder: {found_cylinder['serial_number']} using custom ID 'A1'")
    else:
        print("   ✗ Failed to find cylinder by custom ID")
    
    print("\n3. Finding cylinder by serial number...")
    found_by_serial = cylinder_model.find_by_any_identifier('TEST001')
    if found_by_serial:
        print(f"   ✓ Found cylinder: {found_by_serial['custom_id']} using serial number 'TEST001'")
    else:
        print("   ✗ Failed to find cylinder by serial number")
    
    print("\n4. Finding cylinder by system ID...")
    found_by_id = cylinder_model.find_by_any_identifier(new_cylinder['id'])
    if found_by_id:
        print(f"   ✓ Found cylinder using system ID: {found_by_id['id']}")
    else:
        print("   ✗ Failed to find cylinder by system ID")
    
    print("\n5. Testing case-insensitive search...")
    found_case_insensitive = cylinder_model.find_by_any_identifier('a1')
    if found_case_insensitive:
        print("   ✓ Case-insensitive search works correctly")
    else:
        print("   ✗ Case-insensitive search failed")
    
    print("\n" + "=" * 40)
    print("Custom ID functionality test complete!")

if __name__ == '__main__':
    test_custom_id_functionality()