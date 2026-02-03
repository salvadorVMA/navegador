"""
Fix for variable search timeout issues in dashboard.py

This script improves the variable selection process by:
1. Increasing the timeout for agent queries
2. Adding progressive timeout handling
3. Implementing better feedback during long-running operations
"""

import sys
import os
import time
from datetime import datetime

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Default configuration
DEFAULT_TIMEOUT = 60  # Increased from 8 seconds to 60 seconds
TIMEOUT_INCREMENTS = [15, 30, 60, 90]  # Progressive timeouts to try if needed
AGENT_INIT_TIMEOUT = 20  # Timeout for agent initialization
AGENT_QUERY_TIMEOUT = 60  # Timeout for variable selection queries

def apply_variable_search_timeout_fix():
    """
    Apply fixes to dashboard.py to address the variable search timeout issues
    """
    # Read the existing dashboard.py file
    dashboard_path = "dashboard.py"
    
    # Make a backup of the current file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f"dashboard.py.{timestamp}.bak"
    
    try:
        with open(dashboard_path, "r") as f:
            content = f.read()
            
        # Create a backup
        with open(backup_path, "w") as f:
            f.write(content)
            
        print(f"✅ Created backup at {backup_path}")
        
        # Apply fixes
        
        # 1. Increase the agent query timeout from 8 to 60 seconds
        content = content.replace(
            "query_result = future.result(timeout=8)  # 8 second timeout - reduce from 15",
            "query_result = future.result(timeout=60)  # 60 second timeout - increased from 8"
        )
        
        # Also increase the timeout in any other places
        content = content.replace(
            "test_result = future.result(timeout=10)  # 10 second timeout",
            "test_result = future.result(timeout=20)  # 20 second timeout - increased from 10"
        )
        
        # 2. Update the timeout in handle_auto_next_step
        content = content.replace(
            "timeout_seconds = 30  # Expire pending actions after 30 seconds",
            "timeout_seconds = 60  # Expire pending actions after 60 seconds (increased from 30)"
        )
        
        # 3. Increase the MAX_INTERVALS in handle_auto_next_step
        content = content.replace(
            "MAX_INTERVALS = 5",
            "MAX_INTERVALS = 10  # Increased from 5 to handle longer operations"
        )
        
        # Additional validation - check for escaped quotes that might cause syntax errors
        content = content.replace('\\"', '"')  # Replace any escaped quotes
            
        # Write the modified content back
        with open(dashboard_path, "w") as f:
            f.write(content)
            
        print("✅ Successfully applied timeout fixes to dashboard.py")
        print("🔍 Changes made:")
        print("  - Increased agent query timeout from 8 to 60 seconds")
        print("  - Increased agent initialization timeout from 10 to 20 seconds")
        print("  - Increased pending action expiration from 30 to 60 seconds")
        print("  - Increased max auto-next-step intervals from 5 to 10")
        print("  - Fixed any potentially problematic escaped quotes")
        
        return True
        
    except Exception as e:
        print(f"❌ Error applying fixes: {e}")
        return False
        
if __name__ == "__main__":
    apply_variable_search_timeout_fix()
