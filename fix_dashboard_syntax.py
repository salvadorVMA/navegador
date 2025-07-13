#!/usr/bin/env python3

import sys
import ast
import traceback
from datetime import datetime
import shutil
import re

def backup_file(file_path):
    """Create a backup of the file before modifying it"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f"{file_path}.{timestamp}.bak"
    shutil.copy2(file_path, backup_path)
    print(f"✅ Created backup: {backup_path}")
    return backup_path

def find_syntax_errors(file_path):
    """Find all syntax errors in a Python file"""
    with open(file_path, 'r') as file:
        content = file.read()
    
    try:
        ast.parse(content)
        print(f"✅ No syntax errors found in {file_path}")
        return []
    except SyntaxError as e:
        print(f"❌ Syntax error in {file_path} at line {e.lineno}, column {e.offset}:")
        print(f"   {e.text.strip() if e.text else 'No text available'}")
        if e.offset:
            print(f"   {' ' * (e.offset - 1)}^")
        print(f"   {e}")
        
        # Return nearby lines for context
        lines = content.splitlines()
        start_line = max(0, e.lineno - 10)
        end_line = min(len(lines), e.lineno + 10)
        
        context = "\n".join([f"{i+1}: {line}" for i, line in enumerate(lines[start_line:end_line], start=start_line)])
        print(f"\nContext around error:\n{context}")
        
        return [(e.lineno, e.offset, str(e))]
    except Exception as e:
        print(f"❌ Error parsing {file_path}: {e}")
        traceback.print_exc()
        return []

def fix_unterminated_string(file_path, line_number):
    """Fix unterminated string literal by adding closing quotes"""
    with open(file_path, 'r') as file:
        lines = file.readlines()
    
    if line_number <= 0 or line_number > len(lines):
        print(f"❌ Invalid line number: {line_number}")
        return False
    
    line = lines[line_number - 1]
    if '"""' in line and line.count('"""') % 2 == 1:
        # Fix missing triple quotes
        lines[line_number - 1] = line + '"""\n'
        print(f"✅ Fixed unterminated triple quote at line {line_number}")
    elif '"' in line and line.count('"') % 2 == 1:
        # Fix missing double quotes
        lines[line_number - 1] = line.rstrip() + '"\n'
        print(f"✅ Fixed unterminated double quote at line {line_number}")
    elif "'" in line and line.count("'") % 2 == 1:
        # Fix missing single quotes
        lines[line_number - 1] = line.rstrip() + "'\n"
        print(f"✅ Fixed unterminated single quote at line {line_number}")
    else:
        print(f"❌ Could not determine quote type to fix at line {line_number}: {line.strip()}")
        return False
    
    # Write the fixed content back
    with open(file_path, 'w') as file:
        file.writelines(lines)
    
    return True

def fix_missing_function_block(file_path, line_number):
    """Fix missing function block by adding pass statement"""
    with open(file_path, 'r') as file:
        lines = file.readlines()
    
    if line_number <= 0 or line_number > len(lines):
        print(f"❌ Invalid line number: {line_number}")
        return False
    
    # Check if this is a function definition followed by a docstring
    if "def " in lines[line_number - 1] and line_number < len(lines) and '"""' in lines[line_number]:
        # Find the end of the docstring
        docstring_end = line_number
        while docstring_end < len(lines) and '"""' not in lines[docstring_end][lines[docstring_end].find('"""')+3:]:
            docstring_end += 1
        
        # If we found the end of the docstring and there's no code after it
        if docstring_end < len(lines) and not lines[docstring_end+1].strip():
            # Add pass statement with proper indentation
            indent = len(lines[line_number - 1]) - len(lines[line_number - 1].lstrip())
            lines.insert(docstring_end + 1, ' ' * indent + '    pass\n')
            print(f"✅ Added missing function body at line {docstring_end + 1}")
            
            # Write the fixed content back
            with open(file_path, 'w') as file:
                file.writelines(lines)
            return True
    
    print(f"❌ Could not fix missing function block at line {line_number}")
    return False

def replace_process_agent_function(file_path):
    """Replace the broken process_agent_response function with the fixed version"""
    try:
        # Get the fixed function
        fixed_file_path = "fixed_process_agent.py"
        with open(fixed_file_path, 'r') as f:
            fixed_content = f.read()
        
        # Extract just the function definition and body
        pattern = r"(def process_agent_response\(agent_response, session_data, chat_data, user_message\):[\s\S]+?)(?=\n\n# |$)"
        match = re.search(pattern, fixed_content)
        if not match:
            print("❌ Could not find process_agent_response function in fixed_process_agent.py")
            return False
        
        fixed_function = match.group(1)
        
        # Read the dashboard file
        with open(file_path, 'r') as f:
            content = f.read()
        
        # Find all occurrences of process_agent_response function
        pattern = r"def process_agent_response\(agent_response, session_data, chat_data, user_message\):[\s\S]+?(?=\n\ndef|\n\n@|\Z)"
        matches = list(re.finditer(pattern, content))
        
        if not matches:
            print("❌ Could not find process_agent_response function in dashboard.py")
            return False
        
        # Replace the last occurrence (which is likely the broken one)
        last_match = matches[-1]
        new_content = (
            content[:last_match.start()] + 
            fixed_function + 
            content[last_match.end():]
        )
        
        # Write the fixed content back
        with open(file_path, 'w') as f:
            f.write(new_content)
        
        print(f"✅ Replaced process_agent_response function in {file_path}")
        return True
    
    except Exception as e:
        print(f"❌ Error replacing function: {e}")
        traceback.print_exc()
        return False

def fix_syntax_errors(file_path):
    """Try to fix common syntax errors in a file"""
    # First create a backup
    backup_file(file_path)
    
    # Check for errors
    errors = find_syntax_errors(file_path)
    if not errors:
        return True
    
    # First try to replace the broken process_agent_response function
    print("\n🔧 Trying to replace process_agent_response function...")
    if replace_process_agent_function(file_path):
        # Check if that fixed it
        if not find_syntax_errors(file_path):
            print("✅ Successfully fixed all syntax errors!")
            return True
    
    # If that didn't work, try fixing unterminated strings
    for line_num, _, error_msg in errors:
        if "unterminated string literal" in error_msg:
            print(f"\n🔧 Trying to fix unterminated string at line {line_num}...")
            fix_unterminated_string(file_path, line_num)
        elif "expected an indented block" in error_msg:
            print(f"\n🔧 Trying to fix missing function block at line {line_num}...")
            fix_missing_function_block(file_path, line_num)
    
    # Check if all errors are fixed
    if not find_syntax_errors(file_path):
        print("✅ Successfully fixed all syntax errors!")
        return True
    else:
        print("⚠️ Some syntax errors still remain.")
        return False

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python fix_dashboard_syntax.py <file_path>")
        sys.exit(1)
    
    file_path = sys.argv[1]
    if fix_syntax_errors(file_path):
        sys.exit(0)
    else:
        sys.exit(1)
