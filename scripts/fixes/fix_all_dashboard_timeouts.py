"""
Dashboard Timeout Comprehensive Fix
==================================

This script applies a comprehensive set of fixes to all timeout-related issues
in the dashboard application, ensuring reliable operation for all queries.

It addresses:
1. Variable search timeouts
2. Agent query timeouts
3. Analysis timeouts
4. Progress reporting improvements
"""

import os
import sys
import re
import datetime
import traceback
from typing import Dict, Any, List, Optional

def create_backup(file_path: str) -> Optional[str]:
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

def fix_all_dashboard_timeouts() -> bool:
    """
    Apply comprehensive timeout fixes to dashboard.py
    
    This addresses all known timeout issues in the dashboard application.
    
    Returns:
        True if successful, False otherwise
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
        
        # 1. Fix agent query timeouts
        print("1. Fixing agent query timeouts...")
        content = re.sub(
            r'(query_result\s*=\s*future\.result\()timeout=30(\))',
            r'\1timeout=120\2  # 120 second timeout (increased from 30)',
            content
        )
        content = re.sub(
            r'(test_result\s*=\s*future\.result\()timeout=20(\))',
            r'\1timeout=60\2  # 60 second timeout (increased from 20)',
            content
        )
        
        # 2. Fix pending action timeout
        print("2. Fixing pending action timeout...")
        content = re.sub(
            r'(timeout_seconds\s*=\s*)60(\s*#.*)',
            r'\1180\2 (increased from 60)',
            content
        )
        
        # 3. Fix auto-next-step interval
        print("3. Fixing auto-next-step interval...")
        content = re.sub(
            r'(dcc\.Interval\(id=[\'\"]auto-next-step-interval[\'\"],\s*interval=)1(\*1000,)',
            r'\115\2  # 15 seconds interval (increased from 1)',
            content
        )
        
        # 4. Fix max intervals constant
        print("4. Fixing max intervals constant...")
        if "MAX_INTERVALS = 300" in content:
            content = content.replace(
                "MAX_INTERVALS = 300",
                "MAX_INTERVALS = 100  # Reduced from 300 since interval is now 15s (total time: 1500s)"
            )
        
        # 5. Enhance timeout messages
        print("5. Enhancing timeout messages...")
        timeout_message_pattern = r'timeout_message\s*=\s*"The query is taking longer than expected to process\. Please wait while we continue searching for relevant variables\.\.\."'
        enhanced_message = 'timeout_message = "The variable search is taking longer than expected. Please wait while we continue processing your query... This may take up to 3 minutes for complex searches."'
        
        if re.search(timeout_message_pattern, content):
            content = re.sub(timeout_message_pattern, enhanced_message, content)
            print("✅ Enhanced timeout message")
        else:
            print("⚠️ Could not find timeout message pattern")
        
        # 6. Add progress reporting improvements
        print("6. Adding progress reporting improvements...")
        handle_auto_next_step_pattern = r"def handle_auto_next_step\("
        progress_reporting_code = """    # Add progress reporting if available
    if pending_action and 'progress' in pending_action:
        progress = pending_action['progress']
        if progress > 0 and not processed:
            # Show progress updates for long-running operations
            progress_message = f"Search progress: {progress}% complete..."
            new_chat_data = chat_data.copy() if chat_data else []
            # Only add if last message wasn't also a progress message
            add_progress = True
            if new_chat_data and len(new_chat_data) > 0:
                last_msg = new_chat_data[-1]
                if last_msg.get('is_progress') and 'progress' in last_msg.get('content', ''):
                    # Update the existing progress message instead
                    new_chat_data[-1]['content'] = progress_message
                    add_progress = False
                    
            if add_progress:
                new_chat_data.append({
                    "type": "assistant",
                    "content": progress_message,
                    "timestamp": datetime.now().strftime("%H:%M"),
                    "is_progress": True
                })
            return format_chat_history(new_chat_data), new_chat_data, "", session_data, False
    """
        
        # Look for a suitable insertion point for progress reporting
        if "# Skip if the action has already been processed" in content:
            insert_pos = content.find("# Skip if the action has already been processed")
            insert_pos = content.find("\n", insert_pos) + 1
            
            # Check if we already added this code
            if "# Add progress reporting if available" not in content:
                content_lines = content.split("\n")
                indentation = "    "  # Default indentation
                
                # Find the indentation at insertion point
                for line in content_lines:
                    if "# Skip if the action has already been processed" in line:
                        indentation = line[:line.find("#")]
                        break
                
                # Indent the progress reporting code
                indented_code = "\n".join(indentation + line for line in progress_reporting_code.strip().split("\n"))
                
                # Insert the code
                content = content[:insert_pos] + indented_code + "\n" + content[insert_pos:]
                print("✅ Added progress reporting improvements")
            else:
                print("✅ Progress reporting already present")
        else:
            print("⚠️ Could not find insertion point for progress reporting")
        
        # Write updated content back to file
        with open(dashboard_path, "w") as f:
            f.write(content)
            
        print(f"\n✅ Successfully applied all timeout fixes to {dashboard_path}")
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
    print("\n================================================")
    print(" Dashboard Timeout Comprehensive Fix")
    print("================================================\n")
    
    try:
        success = fix_all_dashboard_timeouts()
        
        if success:
            print("\n✅ All timeout fixes successfully applied!")
            print("\nRestart the dashboard to apply the changes:")
            print("  python dashboard.py")
        else:
            print("\n❌ Failed to apply some fixes")
            print("Check the error messages above for details")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n❌ Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        traceback.print_exc()
        sys.exit(1)
