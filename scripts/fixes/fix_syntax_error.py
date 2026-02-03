"""
Fix the syntax errors in dashboard.py
"""
import sys
import os
import re
import tokenize
import io

# Get the file path
dashboard_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'dashboard.py')

# Create a backup of the file
timestamp = __import__('datetime').datetime.now().strftime('%Y%m%d_%H%M%S')
backup_path = f"{dashboard_path}.{timestamp}.bak"
with open(dashboard_path, 'r') as src, open(backup_path, 'w') as dst:
    dst.write(src.read())
print(f"Created backup at {backup_path}")

# Read the file content
with open(dashboard_path, 'r') as f:
    content = f.read()

# Common patterns that cause syntax errors
fixes_applied = 0

# Fix 1: Look for missing newlines between statements
def fix_missing_newlines(content):
    # Fix missing newlines between return statements and following code
    patterns = [
        (r'return dash\.no_update, dash\.no_update, dash\.no_update, dash\.no_update, True(\w+)', 
         r'return dash.no_update, dash.no_update, dash.no_update, dash.no_update, True\n\n\1'),
        
        (r'return format_chat_history\(new_chat_data\), new_chat_data, "", session_data, True(\w+)',
         r'return format_chat_history(new_chat_data), new_chat_data, "", session_data, True\n\n\1'),
        
        # Function definition immediately after a statement without newline
        (r'}\)(\s*)def ', r'}\)\n\n\1def '),
        
        # Class definition immediately after a statement without newline
        (r'True(\s*)class ', r'True\n\n\1class '),
        
        # Missing newline between statements
        (r'\)(\s*)def ', r')\n\n\1def '),
        
        # Missing newline after print statement followed by def/class
        (r'print\([^)]+\)(\s*)(def|class) ', r'print(\1)\n\n\2 ')
    ]
    
    fixed_content = content
    fixes = 0
    
    for pattern, replacement in patterns:
        new_content = re.sub(pattern, replacement, fixed_content)
        if new_content != fixed_content:
            fixes += 1
            fixed_content = new_content
    
    return fixed_content, fixes

# Fix 2: Look for unterminated try blocks
def fix_unterminated_try_blocks(content):
    """Fix try blocks that don't have except or finally"""
    lines = content.split('\n')
    fixed_lines = []
    in_try_block = False
    try_indent = 0
    try_line = 0
    fixes = 0
    
    for i, line in enumerate(lines):
        stripped = line.lstrip()
        indent = len(line) - len(stripped)
        
        # Detect try block start
        if stripped.startswith('try:'):
            in_try_block = True
            try_indent = indent
            try_line = i
        
        # Detect except or finally (proper closure of try)
        if in_try_block and indent == try_indent:
            if stripped.startswith('except') or stripped.startswith('finally:'):
                in_try_block = False
        
        # If we're leaving a try block without except/finally, add an except
        if in_try_block and i > try_line and indent < try_indent and not stripped.startswith('#'):
            # Add an except block before this line
            except_line = ' ' * try_indent + 'except Exception as e:\n'
            except_line += ' ' * (try_indent + 4) + 'print(f"Error: {e}")\n'
            fixed_lines.append(except_line)
            in_try_block = False
            fixes += 1
        
        fixed_lines.append(line)
    
    # If we ended the file in a try block, add an except
    if in_try_block:
        except_line = ' ' * try_indent + 'except Exception as e:\n'
        except_line += ' ' * (try_indent + 4) + 'print(f"Error: {e}")'
        fixed_lines.append(except_line)
        fixes += 1
    
    return '\n'.join(fixed_lines), fixes

# Apply fixes
print("Applying syntax fixes...")

# Fix 1: Missing newlines
fixed_content, newline_fixes = fix_missing_newlines(content)
if newline_fixes > 0:
    print(f"✅ Fixed {newline_fixes} missing newline(s)")
    fixes_applied += newline_fixes

# Fix 2: Unterminated try blocks
fixed_content, try_fixes = fix_unterminated_try_blocks(fixed_content)
if try_fixes > 0:
    print(f"✅ Fixed {try_fixes} unterminated try block(s)")
    fixes_applied += try_fixes

# Write the fixed content back to the file
with open(dashboard_path, 'w') as f:
    f.write(fixed_content)

# Validate the file
try:
    with open(dashboard_path, 'r') as f:
        content = f.read()
    compile(content, dashboard_path, 'exec')
    print("✅ Syntax validation passed")
    print(f"Total fixes applied: {fixes_applied}")
except SyntaxError as e:
    print(f"❌ Syntax error still exists: {e}")
    print("Manual intervention required.")
    
    # Try to extract the problematic area
    lines = content.split('\n')
    lineno = e.lineno if hasattr(e, 'lineno') and e.lineno is not None else 0
    
    if lineno > 0:
        print("Specific line:", lines[lineno - 1])
        
        # Try to extract the problematic area (5 lines before and after)
        start_line = max(0, lineno - 6)
        end_line = min(len(lines) - 1, lineno + 5)
        
        print("\nContext (5 lines before and after):")
        for i in range(start_line, end_line + 1):
            prefix = ">" if i == lineno - 1 else " "
            print(f"{prefix} {i+1}: {lines[i]}")
    else:
        print("Could not determine exact line number of error.")
    
    # Ask if user wants to restore from backup
    if input("\nRestore from backup? (y/n): ").lower() == 'y':
        with open(backup_path, 'r') as src, open(dashboard_path, 'w') as dst:
            dst.write(src.read())
        print("Backup restored.")
    else:
        print("Keeping current changes. Manual fixes required.")
    
    sys.exit(1)
