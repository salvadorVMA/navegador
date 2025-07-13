#!/usr/bin/env python3
"""
Fix syntax error in the dashboard.py file
"""
import os
import re
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

def fix_syntax_error():
    """Fix the syntax error in dashboard.py"""
    dashboard_path = 'dashboard.py'
    if not os.path.exists(dashboard_path):
        print(f"❌ File not found: {dashboard_path}")
        return False
    
    # Create backup
    backup_path = backup_file(dashboard_path)
    
    # Read the current file content
    with open(dashboard_path, 'r') as f:
        content = f.read()
    
    # Fix the syntax error "prdef" -> "def"
    fixed_content = content.replace('prdef process_agent_response', 'def process_agent_response')
    
    # Write the fixed content back to the file
    with open(dashboard_path, 'w') as f:
        f.write(fixed_content)
    
    print(f"✅ Successfully fixed syntax error in {dashboard_path}")
    print(f"✅ Backup saved to {backup_path}")
    return True

if __name__ == "__main__":
    print("🔧 Fixing syntax error in dashboard.py...")
    if fix_syntax_error():
        print("\n✅ Fix applied successfully!")
    else:
        print("\n❌ Failed to apply fix.")
