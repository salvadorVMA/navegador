#!/usr/bin/env python3
import re
import sys

def fix_datetime_import(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()
    
    # Add from datetime import datetime at the top of the file
    if 'from datetime import datetime' not in content:
        # Find the first import statement
        import_match = re.search(r'^import', content, re.MULTILINE)
        if import_match:
            pos = import_match.start()
            content = content[:pos] + 'from datetime import datetime\n' + content[pos:]
    
    # Replace all datetime.datetime.now() with datetime.now()
    content = content.replace('datetime.datetime.now()', 'datetime.now()')
    
    # Write back to the file
    with open(file_path, 'w', encoding='utf-8') as file:
        file.write(content)
    
    print("Fixed datetime imports and usages")
    return True

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python fix_datetime.py <file_path>")
        sys.exit(1)
        
    file_path = sys.argv[1]
    fix_datetime_import(file_path)
