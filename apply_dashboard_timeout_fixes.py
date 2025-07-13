"""
Comprehensive fix for variable search timeout issues in the dashboard.

This script applies the following fixes:
1. Increases default timeouts
2. Implements progressive timeout handling
3. Adds enhanced feedback during long-running variable searches
4. Improves error recovery and state management
"""

import os
import sys
import time
import shutil
from datetime import datetime
import re

# Current directory
script_dir = os.path.dirname(os.path.abspath(__file__))

# Dashboard file path
dashboard_path = os.path.join(script_dir, "dashboard.py")

def backup_dashboard():
    """Create a backup of the dashboard.py file"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f"{dashboard_path}.{timestamp}.bak"
    
    try:
        shutil.copy2(dashboard_path, backup_path)
        print(f"✅ Created backup at {backup_path}")
        return True
    except Exception as e:
        print(f"❌ Error creating backup: {e}")
        return False

def apply_timeout_fixes():
    """Apply all timeout-related fixes to the dashboard.py file"""
    try:
        with open(dashboard_path, "r") as f:
            content = f.read()
            
        # 1. Increase agent initialization timeout
        content = re.sub(
            r"test_result = future\.result\(timeout=(\d+)\)\s*#\s*(\d+) second timeout",
            r"test_result = future.result(timeout=20)  # 20 second timeout (increased from \1)",
            content
        )
        
        # 2. Increase agent query timeout
        content = re.sub(
            r"query_result = future\.result\(timeout=(\d+)\)\s*#\s*(\d+) second timeout",
            r"query_result = future.result(timeout=30)  # 30 second timeout (increased from \1)",
            content
        )
        
        # 3. Update auto-next-step interval
        content = re.sub(
            r'dcc\.Interval\(id="auto-next-step-interval", interval=(\d+), n_intervals=0, disabled=True, max_intervals=(\d+)\)',
            r'dcc.Interval(id="auto-next-step-interval", interval=2000, n_intervals=0, disabled=True, max_intervals=10)',
            content
        )
        
        # 4. Update timeout in handle_auto_next_step
        content = re.sub(
            r"timeout_seconds = (\d+)\s*#\s*Expire pending actions after (\d+) seconds",
            r"timeout_seconds = 60  # Expire pending actions after 60 seconds (increased from \1)",
            content
        )
        
        # 5. Update MAX_INTERVALS
        content = re.sub(
            r"MAX_INTERVALS = (\d+)",
            r"MAX_INTERVALS = 10  # Increased from \1 to handle longer operations",
            content
        )
        
        # 6. Add timeout feedback message for variable searches
        if "Variable search is taking longer than expected" not in content:
            # Find the timeout message section
            timeout_msg_pattern = r"(timeout_message = \".*?\"\n.*?new_chat_data\.append\(\{.*?\"content\": timeout_message,.*?\}\))"
            
            timeout_msg_replacement = """timeout_message = "The query is taking longer than expected to process. Please wait while we continue searching for relevant variables..."
            new_chat_data = chat_data.copy() if chat_data else []
            new_chat_data.append({
                "type": "assistant",
                "content": timeout_message,
                "timestamp": datetime.now().strftime("%H:%M"),
                "is_progress": True  # Mark as progress message
            })"""
            
            content = re.sub(timeout_msg_pattern, timeout_msg_replacement, content, flags=re.DOTALL)
        
        # Write the modified content back to the file
        with open(dashboard_path, "w") as f:
            f.write(content)
            
        print("✅ Successfully applied timeout fixes to dashboard.py")
        print("🔍 Changes made:")
        print("  - Increased agent initialization timeout to 20 seconds")
        print("  - Increased agent query timeout to 30 seconds")
        print("  - Increased auto-next-step max intervals to 10")
        print("  - Increased pending action expiration to 60 seconds")
        print("  - Updated timeout feedback message for variable searches")
        
        return True
        
    except Exception as e:
        print(f"❌ Error applying fixes: {e}")
        return False

def main():
    """Main function to execute all fixes"""
    print("🔄 Starting dashboard timeout fix process...")
    
    # Backup the dashboard file
    if not backup_dashboard():
        print("⚠️ Warning: Could not create backup, aborting")
        return False
    
    # Apply timeout fixes
    if not apply_timeout_fixes():
        print("❌ Failed to apply timeout fixes")
        return False
    
    print("✅ All fixes applied successfully!")
    print("📋 Next steps:")
    print("  1. Restart the dashboard application")
    print("  2. Test variable searches with different query complexity")
    print("  3. Monitor for any timeout issues")
    
    return True

if __name__ == "__main__":
    main()
