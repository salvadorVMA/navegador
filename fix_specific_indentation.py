#!/usr/bin/env python3

import sys
import shutil
from datetime import datetime
import re

def backup_file(file_path):
    """Create a backup of the file before modifying it"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f"{file_path}.{timestamp}.bak"
    shutil.copy2(file_path, backup_path)
    print(f"✅ Created backup: {backup_path}")
    return backup_path

def fix_specific_indentation(file_path):
    """Fix the specific indentation issue in the process_agent_response function in the except block"""
    with open(file_path, 'r') as file:
        content = file.read()
    
    # Pattern to find the except block with the problematic function
    pattern = r"except Exception as e:\s+print\(f\"❌ Error importing required libraries: \{e\}\"\)\s+def process_agent_response\(agent_response, session_data, chat_data, user_message\):"
    
    match = re.search(pattern, content)
    if not match:
        print("❌ Could not find the problematic except block")
        return False
    
    # Let's just completely replace this with a proper solution
    # First, add a simple implementation in the except block
    new_except_block = """except Exception as e:
    print(f"❌ Error importing required libraries: {e}")
    # Define fallback functions for exception handling
    def process_agent_response(agent_response, session_data, chat_data, user_message):
        print(f"Warning: Using fallback process_agent_response due to import error")
        import dash
        return dash.no_update, dash.no_update, dash.no_update, dash.no_update, True
"""
    
    # Replace the problematic block with our fixed version
    fixed_content = content.replace(match.group(0), new_except_block)
    
    # Write the fixed content back
    with open(file_path, 'w') as file:
        file.write(fixed_content)
    
    print("✅ Successfully fixed the indentation issue in the except block")
    return True

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python fix_specific_indentation.py <file_path>")
        sys.exit(1)
    
    file_path = sys.argv[1]
    
    # Create a backup first
    backup_file(file_path)
    
    if fix_specific_indentation(file_path):
        print("✅ Fix applied successfully!")
        sys.exit(0)
    else:
        print("❌ Failed to apply fix.")
        sys.exit(1)
