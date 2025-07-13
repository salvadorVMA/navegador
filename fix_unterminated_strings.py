#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Fix unterminated string literals in a file
"""

import re
import sys

def fix_unterminated_strings(filename):
    """Fix unterminated string literals in a file"""
    with open(filename, 'r') as f:
        lines = f.readlines()
    
    # Patterns to look for and fix
    patterns = [
        (r'print\("(\s*)', r'print("\n'),  # Fix print("
        (r'print\(f"(\s*)', r'print(f"\n'),  # Fix print(f"
    ]
    
    fixed_lines = []
    for line in lines:
        fixed_line = line
        for pattern, replacement in patterns:
            fixed_line = re.sub(pattern, replacement, fixed_line)
        fixed_lines.append(fixed_line)
    
    with open(filename, 'w') as f:
        f.writelines(fixed_lines)
    
    print(f"✅ Fixed unterminated strings in {filename}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        filename = sys.argv[1]
    else:
        filename = "test_agent_tracing.py"
    
    fix_unterminated_strings(filename)
