#!/usr/bin/env python3

import sys
import re
import ast
import shutil
from datetime import datetime

def backup_file(file_path):
    """Create a backup of the file before modifying it"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f"{file_path}.{timestamp}.bak"
    shutil.copy2(file_path, backup_path)
    print(f"✅ Created backup: {backup_path}")
    return backup_path

def find_indentation_issues(file_content):
    """Find functions with indentation issues"""
    issues = []
    lines = file_content.splitlines()
    
    for i, line in enumerate(lines):
        if "def " in line and line.strip().startswith("def ") and i+1 < len(lines):
            next_line = lines[i+1]
            if '"""' in next_line and not next_line.strip().startswith('"""'):
                # This is likely an indentation issue with a docstring
                issues.append(i)
    
    return issues

def fix_all_indentation_issues(file_path):
    """Fix all indentation issues in the file"""
    with open(file_path, 'r') as file:
        content = file.read()
    
    # Find all indentation issues
    issues = find_indentation_issues(content)
    if not issues:
        print("✅ No indentation issues found")
        return True
    
    print(f"🔍 Found {len(issues)} indentation issues")
    
    # Fix each issue by adding proper indentation to docstrings
    lines = content.splitlines()
    for line_idx in issues:
        # Get the indentation of the function
        func_line = lines[line_idx]
        indentation = len(func_line) - len(func_line.lstrip())
        
        # Add proper indentation (4 spaces) to all lines until the docstring ends
        i = line_idx + 1
        while i < len(lines) and '"""' not in lines[i][lines[i].find('"""')+3:]:
            # Add indentation only if it's not already properly indented
            if not lines[i].startswith(' ' * (indentation + 4)):
                lines[i] = ' ' * (indentation + 4) + lines[i].lstrip()
            i += 1
        
        # Fix the closing """ if needed
        if i < len(lines) and not lines[i].startswith(' ' * (indentation + 4)):
            lines[i] = ' ' * (indentation + 4) + lines[i].lstrip()
    
    # Write the fixed content back
    with open(file_path, 'w') as file:
        file.write('\n'.join(lines))
    
    # Verify the fix worked by checking syntax
    try:
        with open(file_path, 'r') as file:
            fixed_content = file.read()
        ast.parse(fixed_content)
        print("✅ All indentation issues fixed successfully")
        return True
    except SyntaxError as e:
        print(f"❌ Syntax error still exists at line {e.lineno}, column {e.offset}: {e}")
        print(f"   {e.text.strip() if e.text else ''}")
        return False

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python fix_all_indentation.py <file_path>")
        sys.exit(1)
    
    file_path = sys.argv[1]
    
    # Create a backup first
    backup_file(file_path)
    
    if fix_all_indentation_issues(file_path):
        print("✅ All fixes applied successfully!")
        sys.exit(0)
    else:
        print("❌ Failed to apply all fixes.")
        sys.exit(1)
