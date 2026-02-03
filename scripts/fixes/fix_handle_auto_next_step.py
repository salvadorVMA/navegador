#!/usr/bin/env python3
"""
Debug script to troubleshoot dashboard agent integration and find out why handle_auto_next_step
isn't invoking the agent properly.
"""
import os
import sys
import time
import inspect
import shutil
from datetime import datetime

def backup_file(file_path):
    """Create a backup of the file before modifying it"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f"{file_path}.{timestamp}.bak"
    shutil.copy2(file_path, backup_path)
    print(f"✅ Created backup: {backup_path}")
    return backup_path

def fix_dashboard():
    """Fix the dashboard.py file with a complete replacement of handle_auto_next_step function"""
    dashboard_path = 'dashboard.py'
    if not os.path.exists(dashboard_path):
        print(f"❌ File not found: {dashboard_path}")
        return False
        
    # Create backup
    backup_path = backup_file(dashboard_path)
    
    # Read the fixed implementation of handle_auto_next_step
    with open('fixed_handle_auto_next_step.py', 'r') as f:
        fixed_function = f.read()
    
    # Read the dashboard.py file
    with open(dashboard_path, 'r') as f:
        dashboard_content = f.read()
    
    # Find the start of the handle_auto_next_step function
    function_def = "def handle_auto_next_step(n_intervals, chat_data, session_data):"
    start_pos = dashboard_content.find(function_def)
    
    if start_pos < 0:
        print("❌ Could not find handle_auto_next_step function in dashboard.py")
        return False
    
    # Find the end of the function by finding the next def or class
    lines = dashboard_content[start_pos:].split("\n")
    end_line_idx = 0
    function_indentation = len(lines[0]) - len(lines[0].lstrip())
    
    for i, line in enumerate(lines[1:], 1):
        if line.strip() and len(line) - len(line.lstrip()) <= function_indentation:
            if line.lstrip().startswith("def ") or line.lstrip().startswith("class "):
                end_line_idx = i
                break
    
    if end_line_idx == 0:
        print("❌ Could not find the end of handle_auto_next_step function")
        return False
    
    # Calculate the position where the function ends
    end_pos = start_pos + sum(len(line) + 1 for line in lines[:end_line_idx])
    
    # Extract the function declaration line (@app.callback...)
    callback_start = dashboard_content.rfind("@app.callback", 0, start_pos)
    if callback_start < 0:
        print("❌ Could not find the @app.callback decorator for handle_auto_next_step")
        return False
    
    # Find the start of the function after the decorator
    decorator_lines = dashboard_content[callback_start:start_pos].split("\n")
    function_with_decorator = dashboard_content[callback_start:end_pos]
    
    # Now replace the entire function including decorator with our fixed version
    modified_content = dashboard_content.replace(function_with_decorator, fixed_function)
    
    # Write the modified content back to the file
    with open(dashboard_path, 'w') as f:
        f.write(modified_content)
    
    print(f"✅ Successfully fixed handle_auto_next_step function in {dashboard_path}")
    print(f"✅ Backup saved to {backup_path}")
    return True

if __name__ == "__main__":
    print("🔧 Fixing handle_auto_next_step in dashboard.py...")
    if fix_dashboard():
        print("\n✅ Fix applied successfully!")
        print("\n📋 To test the fix:")
        print("1. Run: python dashboard.py")
        print("2. Test with the query 'qué piensan los mexicanos sobre la salud?'\n")
    else:
        print("\n❌ Failed to apply fix.")
