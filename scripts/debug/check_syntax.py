#!/usr/bin/env python3

import sys
import ast

def check_syntax(file_path):
    try:
        with open(file_path, 'r') as file:
            content = file.read()
        
        # Try to parse the Python code
        ast.parse(content)
        print(f"✅ Syntax check passed for: {file_path}")
        return True
    except SyntaxError as e:
        print(f"❌ Syntax error in {file_path} at line {e.lineno}, column {e.offset}:")
        print(f"   {e.text.strip()}")
        print(f"   {' ' * (e.offset - 1)}^")
        print(f"   {e}")
        return False
    except Exception as e:
        print(f"❌ Error checking {file_path}: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python check_syntax.py <file_path> [<file_path> ...]")
        sys.exit(1)
    
    all_passed = True
    for file_path in sys.argv[1:]:
        if not check_syntax(file_path):
            all_passed = False
    
    sys.exit(0 if all_passed else 1)
