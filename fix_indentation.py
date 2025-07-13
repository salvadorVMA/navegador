#!/usr/bin/env python3

import sys
import re
import shutil
from datetime import datetime

def backup_file(file_path):
    """Create a backup of the file before modifying it"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f"{file_path}.{timestamp}.bak"
    shutil.copy2(file_path, backup_path)
    print(f"✅ Created backup: {backup_path}")
    return backup_path

def fix_indentation_issue(file_path):
    """Fix the indentation issue in the process_agent_response function"""
    with open(file_path, 'r') as file:
        lines = file.readlines()
    
    # Find the broken function
    function_start = -1
    for i, line in enumerate(lines):
        if "def process_agent_response(agent_response, session_data, chat_data, user_message):" in line:
            function_start = i
            break
    
    if function_start == -1:
        print("❌ Could not find the process_agent_response function")
        return False
    
    print(f"✅ Found process_agent_response at line {function_start + 1}")
    
    # Remove the existing broken function
    # We'll continue removing lines until we find a new function definition or the end of the file
    function_end = function_start + 1
    while function_end < len(lines):
        if lines[function_end].strip().startswith("def ") or lines[function_end].strip().startswith("@"):
            break
        function_end += 1
    
    # Get the fixed function from fixed_process_agent.py
    with open("fixed_process_agent.py", 'r') as file:
        fixed_content = file.read()
    
    # Extract the fixed function definition
    match = re.search(r"def process_agent_response\(.*?\):.*?(?=\n\n# |$)", fixed_content, re.DOTALL)
    if not match:
        print("❌ Could not extract process_agent_response function from fixed_process_agent.py")
        return False
    
    fixed_function = match.group(0)
    
    # Replace the broken function with the fixed one
    new_lines = lines[:function_start] + [fixed_function + "\n\n"] + lines[function_end:]
    
    # Write the fixed content
    with open(file_path, 'w') as file:
        file.writelines(new_lines)
    
    print(f"✅ Successfully replaced the broken function")
    return True

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python fix_indentation.py <file_path>")
        sys.exit(1)
    
    file_path = sys.argv[1]
    
    # Create a backup first
    backup_file(file_path)
    
    if fix_indentation_issue(file_path):
        print("✅ Fix applied successfully!")
        sys.exit(0)
    else:
        print("❌ Failed to apply fix.")
        sys.exit(1)
