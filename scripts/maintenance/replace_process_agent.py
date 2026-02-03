#!/usr/bin/env python3
"""
Create a fixed version of process_agent_response and completely replace it in dashboard.py
"""
import os
import sys
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
    """Fix the dashboard.py file by completely using the fixed_process_agent.py content"""
    dashboard_path = 'dashboard.py'
    if not os.path.exists(dashboard_path):
        print(f"❌ File not found: {dashboard_path}")
        return False
    
    # Check if fixed_process_agent.py exists
    fixed_path = 'fixed_process_agent.py'
    if not os.path.exists(fixed_path):
        print(f"❌ File not found: {fixed_path}")
        return False
    
    # Create backup
    backup_path = backup_file(dashboard_path)
    
    # Read the fixed content
    with open(fixed_path, 'r') as f:
        fixed_content = f.read()
    
    # Extract just the function definition
    function_lines = []
    capture = False
    for line in fixed_content.split('\n'):
        if line.startswith('def process_agent_response'):
            capture = True
        if capture:
            function_lines.append(line)
    
    if not function_lines:
        print("❌ Could not find process_agent_response function in fixed_process_agent.py")
        return False
    
    fixed_function = '\n'.join(function_lines)
    
    # Read the dashboard.py file
    with open(dashboard_path, 'r') as f:
        dashboard_content = f.read()
    
    # Replace all content between "def process_agent_response" and the next function/class definition
    import re
    pattern = r'def process_agent_response\s*\([^)]*\):.*?(?=(^def|^class))'
    replacement = fixed_function + '\n\n'
    modified_content = re.sub(pattern, replacement, dashboard_content, flags=re.DOTALL | re.MULTILINE)
    
    # Write the modified content back to the file
    with open(dashboard_path, 'w') as f:
        f.write(modified_content)
    
    print(f"✅ Successfully replaced process_agent_response in {dashboard_path}")
    print(f"✅ Backup saved to {backup_path}")
    return True

if __name__ == "__main__":
    print("🔧 Fixing dashboard.py with fixed_process_agent.py...")
    if fix_dashboard():
        print("\n✅ Fix applied successfully!")
    else:
        print("\n❌ Failed to apply fix.")
