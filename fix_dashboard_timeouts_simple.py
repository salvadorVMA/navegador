"""
Fix Dashboard Timeouts - Simple Version
======================================

This script applies fixes to the dashboard.py file to resolve timeout issues
with the variable search functionality. It uses a simpler approach to avoid
regex errors.
"""

import os
import datetime
import traceback

def create_backup(file_path):
    """Create a backup of the specified file"""
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f"{file_path}.{timestamp}.bak"
    
    try:
        with open(file_path, "r") as src_file:
            content = src_file.read()
            
        with open(backup_path, "w") as backup_file:
            backup_file.write(content)
            
        print(f"✅ Created backup at {backup_path}")
        return backup_path
    except Exception as e:
        print(f"❌ Failed to create backup: {e}")
        return None

def fix_dashboard_timeouts():
    """
    Apply timeout fixes to dashboard.py using string replacements
    """
    dashboard_path = "dashboard.py"
    
    # Check if file exists
    if not os.path.exists(dashboard_path):
        print(f"❌ Could not find {dashboard_path}")
        return False
    
    # Create backup
    backup_path = create_backup(dashboard_path)
    if not backup_path:
        print("❌ Failed to create backup, aborting")
        return False
    
    try:
        # Read file content
        with open(dashboard_path, "r") as f:
            content = f.read()
        
        # 1. Fix query timeout
        print("1. Fixing agent query timeout...")
        if "query_result = future.result(timeout=30)" in content:
            content = content.replace(
                "query_result = future.result(timeout=30)",
                "query_result = future.result(timeout=120)  # 120 second timeout (increased from 30)"
            )
            print("✅ Updated query timeout to 120s")
        else:
            print("⚠️ Could not find query timeout pattern")
        
        # 2. Fix test timeout
        print("2. Fixing agent test timeout...")
        if "test_result = future.result(timeout=20)" in content:
            content = content.replace(
                "test_result = future.result(timeout=20)",
                "test_result = future.result(timeout=60)  # 60 second timeout (increased from 20)"
            )
            print("✅ Updated test timeout to 60s")
        else:
            print("⚠️ Could not find test timeout pattern")
        
        # 3. Fix pending action timeout
        print("3. Fixing pending action timeout...")
        if "timeout_seconds = 60" in content:
            content = content.replace(
                "timeout_seconds = 60",
                "timeout_seconds = 180  # Expire pending actions after 180 seconds (increased from 60)"
            )
            print("✅ Updated pending action timeout to 180s")
        else:
            print("⚠️ Could not find pending action timeout pattern")
        
        # 4. Fix auto-next-step interval
        print("4. Fixing auto-next-step interval...")
        if "dcc.Interval(id='auto-next-step-interval', interval=1*1000," in content:
            content = content.replace(
                "dcc.Interval(id='auto-next-step-interval', interval=1*1000,",
                "dcc.Interval(id='auto-next-step-interval', interval=15*1000,  # 15 seconds interval (increased from 1)"
            )
            print("✅ Updated auto-next-step interval to 15s")
        else:
            print("⚠️ Could not find auto-next-step interval pattern")
        
        # 5. Fix timeout message
        print("5. Enhancing timeout message...")
        if "timeout_message = \"The query is taking longer than expected to process. Please wait while we continue searching for relevant variables...\"" in content:
            content = content.replace(
                "timeout_message = \"The query is taking longer than expected to process. Please wait while we continue searching for relevant variables...\"",
                "timeout_message = \"The variable search is taking longer than expected. Please wait while we continue processing your query... This may take up to 3 minutes for complex searches.\""
            )
            print("✅ Enhanced timeout message")
        else:
            print("⚠️ Could not find timeout message pattern")
        
        # Write updated content back to file
        with open(dashboard_path, "w") as f:
            f.write(content)
            
        print(f"\n✅ Successfully applied timeout fixes to {dashboard_path}")
        print(f"✅ Backup available at: {backup_path}")
        return True
        
    except Exception as e:
        print(f"❌ Error applying timeout fixes: {e}")
        traceback.print_exc()
        
        # Try to restore from backup
        try:
            if backup_path and os.path.exists(backup_path):
                with open(backup_path, "r") as backup_file:
                    original_content = backup_file.read()
                    
                with open(dashboard_path, "w") as dest_file:
                    dest_file.write(original_content)
                    
                print(f"✅ Restored original file from backup: {backup_path}")
        except Exception as restore_err:
            print(f"❌ Failed to restore from backup: {restore_err}")
            
        return False

if __name__ == "__main__":
    print("\n=======================================")
    print(" Fix Dashboard Timeouts - Simple Version")
    print("=======================================\n")
    
    success = fix_dashboard_timeouts()
    
    if success:
        print("\n✅ All timeout fixes successfully applied!")
        print("\nRestart the dashboard to apply the changes:")
        print("  python dashboard.py")
    else:
        print("\n❌ Failed to apply some fixes")
        print("Check the error messages above for details")
