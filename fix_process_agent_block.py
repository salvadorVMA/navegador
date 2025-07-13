#!/usr/bin/env python3
"""
Fix missing function block in dashboard.py by replacing the broken 
process_agent_response function with the correct implementation
"""
import os
import re
import sys
import ast
import traceback
import shutil
from datetime import datetime

def check_syntax(content, path="<string>"):
    """Check if the Python content has valid syntax"""
    try:
        ast.parse(content)
        print(f"✅ Syntax check passed")
        return True
    except SyntaxError as e:
        print(f"❌ Syntax error at line {e.lineno}, column {e.offset}:")
        print(f"   {e.text.strip()}")
        print(f"   {' ' * (e.offset - 1)}^")
        print(f"   {e}")
        return False

def backup_file(file_path):
    """Create a backup of the file before modifying it"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f"{file_path}.{timestamp}.bak"
    shutil.copy2(file_path, backup_path)
    print(f"✅ Created backup: {backup_path}")
    return backup_path

def get_fixed_process_agent_function():
    """Get the correct process_agent_response function from fixed_process_agent.py"""
    fixed_file_path = "fixed_process_agent.py"
    if not os.path.exists(fixed_file_path):
        print(f"❌ Fixed function file not found: {fixed_file_path}")
        return None
    
    with open(fixed_file_path, 'r') as f:
        content = f.read()
    
    # Extract just the function definition and body
    pattern = r"(def process_agent_response\(agent_response, session_data, chat_data, user_message\):[\s\S]+?)(?=\n\n# |$)"
    match = re.search(pattern, content)
    if not match:
        print("❌ Could not find process_agent_response function in fixed_process_agent.py")
        return None
    
    return match.group(1)

def fix_missing_function_block():
    """Fix the missing function block in dashboard.py"""
    dashboard_path = 'dashboard.py'
    if not os.path.exists(dashboard_path):
        print(f"❌ Dashboard file not found: {dashboard_path}")
        return False
    
    # Get the fixed function
    fixed_function = get_fixed_process_agent_function()
    if not fixed_function:
        return False
    
    # Create backup
    backup_path = backup_file(dashboard_path)
    
    # Read the current file content
    with open(dashboard_path, 'r') as f:
        content = f.read()
    
    # Pattern to find the broken function
    pattern = r"def process_agent_response\(agent_response, session_data, chat_data, user_message\):\s+\"\"\"[\s\S]+?\"\"\"(?!\s+\S)"
    
    # Check if the pattern exists
    if not re.search(pattern, content):
        print("❌ Could not find the broken process_agent_response function signature in dashboard.py")
        return False
    
    # Replace the broken function with the fixed one
    fixed_content = re.sub(pattern, fixed_function, content)
    
    # Validate the fixed content
    if not check_syntax(fixed_content, dashboard_path):
        print("❌ Fixed content still has syntax errors, aborting!")
        return False
    
    # Write the fixed content back to the file
    with open(dashboard_path, 'w') as f:
        f.write(fixed_content)
    
    print(f"✅ Successfully fixed process_agent_response function in {dashboard_path}")
    print(f"✅ Backup saved to {backup_path}")
    return True

if __name__ == "__main__":
    print("🔧 Fixing missing function block in dashboard.py...")
    if fix_missing_function_block():
        print("\n✅ Fix applied successfully!")
    else:
        print("\n❌ Failed to apply fix.")
        sys.exit(1)
