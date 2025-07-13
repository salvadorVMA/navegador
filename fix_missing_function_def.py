#!/usr/bin/env python3

import sys
import shutil
import re
from datetime import datetime

def backup_file(file_path):
    """Create a backup of the file before modifying it"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f"{file_path}.{timestamp}.bak"
    shutil.copy2(file_path, backup_path)
    print(f"✅ Created backup: {backup_path}")
    return backup_path

def fix_process_agent_response_body(file_path):
    """Fix the specific issue with process_agent_response body not being in a function"""
    with open(file_path, 'r') as file:
        content = file.read()
    
    # Find where we need to insert the function definition
    pattern = r"return dash.no_update, dash.no_update, dash.no_update, dash.no_update, True\s+\"\"\"\s+Process an agent response and update session data"
    match = re.search(pattern, content)
    
    if not match:
        print("❌ Could not find the place to insert function definition")
        return False
    
    # Split the content at the match position
    position = match.start() + len("return dash.no_update, dash.no_update, dash.no_update, dash.no_update, True")
    first_part = content[:position]
    second_part = content[position:]
    
    # Insert the function definition
    fixed_content = first_part + "\n\n# Correctly defined process_agent_response function\ndef process_agent_response(agent_response, session_data, chat_data, user_message):" + second_part
    
    # Write the fixed content back
    with open(file_path, 'w') as file:
        file.write(fixed_content)
    
    print("✅ Successfully added missing function definition")
    return True

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python fix_missing_function_def.py <file_path>")
        sys.exit(1)
    
    file_path = sys.argv[1]
    
    # Create a backup first
    backup_file(file_path)
    
    if fix_process_agent_response_body(file_path):
        print("✅ Fix applied successfully!")
        sys.exit(0)
    else:
        print("❌ Failed to apply fix.")
        sys.exit(1)
