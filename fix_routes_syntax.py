#!/usr/bin/env python3
"""
Fix Routes File Syntax Errors
Comprehensively fixes all indentation and syntax issues in routes.py
"""

import re

def fix_routes_syntax():
    """Fix all syntax errors in routes.py file"""
    
    # Read the broken file
    with open('routes.py', 'r') as f:
        content = f.read()
    
    # Fix all malformed customer service blocks with regex
    # Pattern: with CustomerService() as customer_service:\n        customers, _
    # Replace with: with CustomerService() as customer_service:\n            customers, _
    
    # Fix pattern where customer service call has wrong indentation
    pattern1 = r'(\s+)with CustomerService\(\) as customer_service:\n(\s+)customers, _ = customer_service\.get_all\([^)]*\)\n(\s+)return'
    replacement1 = r'\1with CustomerService() as customer_service:\n\1    customers, _ = customer_service.get_all(page=1, per_page=10000)\n\3return'
    
    content = re.sub(pattern1, replacement1, content, flags=re.MULTILINE)
    
    # Also fix any remaining badly indented customer service calls
    lines = content.split('\n')
    fixed_lines = []
    
    i = 0
    while i < len(lines):
        line = lines[i]
        
        # Check for 'with CustomerService() as customer_service:' followed by bad indentation
        if 'with CustomerService() as customer_service:' in line:
            fixed_lines.append(line)
            i += 1
            
            # Check next line for customer service call
            if i < len(lines):
                next_line = lines[i]
                if 'customers, _ = customer_service.get_all' in next_line:
                    # Get indentation of 'with' line
                    with_indent = len(line) - len(line.lstrip())
                    # Add 4 spaces to that indentation
                    correct_indent = ' ' * (with_indent + 4)
                    # Fix the indentation
                    fixed_customer_line = correct_indent + next_line.strip()
                    fixed_lines.append(fixed_customer_line)
                    i += 1
                    continue
        
        fixed_lines.append(line)
        i += 1
    
    content = '\n'.join(fixed_lines)
    
    # Write the fixed content back
    with open('routes.py', 'w') as f:
        f.write(content)
    
    print("✓ Fixed routes.py syntax errors")

def test_syntax():
    """Test if the fixed file has valid Python syntax"""
    import ast
    
    try:
        with open('routes.py', 'r') as f:
            content = f.read()
        ast.parse(content)
        print("✅ routes.py syntax is now valid")
        return True
    except SyntaxError as e:
        print(f"❌ Syntax error still exists at line {e.lineno}: {e.msg}")
        return False

if __name__ == "__main__":
    print("🔧 Fixing routes.py syntax errors...")
    fix_routes_syntax()
    test_syntax()