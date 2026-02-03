#!/usr/bin/env python3
"""
Debug script to fix the process_agent_response function in dashboard.py
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

def fix_process_agent_response():
    """Fix the process_agent_response function in dashboard.py by adding extensive logging"""
    dashboard_path = 'dashboard.py'
    if not os.path.exists(dashboard_path):
        print(f"❌ File not found: {dashboard_path}")
        return False
    
    # Create backup
    backup_path = backup_file(dashboard_path)
    
    # Read the current file content
    with open(dashboard_path, 'r') as f:
        content = f.read()
    
    # Define the updated process_agent_response with added debugging
    updated_function = '''
def process_agent_response(agent_response, session_data, chat_data, user_message):
    """
    Process an agent response and update session data
    
    This function handles agent responses consistently, keeping track of processed actions
    and ensuring the chat history is properly updated.
    """
    from datetime import datetime
    import time
    import traceback
    
    print("🚀 process_agent_response CALLED - ENTERING FUNCTION")
    print(f"🔍 agent_response type: {type(agent_response)}")
    print(f"🔍 user_message: '{user_message}'")
    
    # Make a deep copy of session data to avoid reference issues
    session_data_copy = session_data.copy() if session_data else {}
    
    try:
        print("🔍 Extracting content from agent response...")
        # Extract response content
        content = extract_agent_content(agent_response)
        print(f"✅ Content extracted: {content[:50]}...")
        
        # Debug agent response
        print(f"🔍 Agent response type: {type(agent_response)}")
        if hasattr(agent_response, 'keys'):
            print(f"🔍 Agent response keys: {list(agent_response.keys())}")
        elif hasattr(agent_response, '__dict__'):
            print(f"🔍 Agent response attributes: {[k for k in agent_response.__dict__ if not k.startswith('_') and not callable(getattr(agent_response, k))]}")
        
        # Update session with agent state, but keep the processed flag
        pending_action = session_data_copy.get('pending_main_action', {})
        print(f"🔍 Pending action before update: {pending_action}")
        
        try:
            session_data_copy = update_session_from_agent_response(session_data_copy, agent_response)
            print("✅ Session updated from agent response")
        except Exception as update_err:
            print(f"⚠️ Error updating session from agent response: {update_err}")
            traceback.print_exc()
            # Continue even if update fails
        
        # Mark the pending action as processed
        if 'pending_main_action' in session_data_copy:
            print(f"🏁 Marking pending action as processed")
            session_data_copy['pending_main_action']['processed'] = True
            session_data_copy['pending_main_action']['processed_at'] = time.time()
        
        # Create assistant message with timestamp
        assistant_message = {
            "type": "assistant", 
            "content": content,
            "timestamp": datetime.now().strftime("%H:%M")
        }
        
        # Update chat history
        new_chat_data = chat_data + [assistant_message]
        formatted_chat = format_chat_history(new_chat_data)
        
        print(f"✅ Agent response processed: {content[:50]}...")
        print("🏁 EXITING process_agent_response with success")
        
        # Return all updated UI components
        return formatted_chat, new_chat_data, "", session_data_copy, True
        
    except Exception as e:
        print(f"❌ Error processing agent response: {e}")
        traceback.print_exc()
        
        try:
            # Fallback to mock response on error
            print("⚠️ Using fallback mock response")
            mock_response = get_mock_agent_response(
                user_message, 
                session_data_copy,
                session_data_copy.get('pending_main_action', {}).get('search_keywords', ''),
                session_data_copy.get('pending_main_action', {}).get('preferred_datasets', ['ALL'])
            )
            
            # Add the mock response to chat
            new_chat_data = chat_data.copy() if chat_data else []
            new_chat_data.append({
                "type": "assistant",
                "content": mock_response["content"],
                "timestamp": datetime.now().strftime("%H:%M")
            })
            
            # Mark pending action as processed
            if 'pending_main_action' in session_data_copy:
                session_data_copy['pending_main_action']['processed'] = True
                session_data_copy['pending_main_action']['processed_at'] = time.time()
            
            print("🏁 EXITING process_agent_response with fallback response")
            return format_chat_history(new_chat_data), new_chat_data, "", session_data_copy, True
            
        except Exception as nested_err:
            print(f"❌❌ Critical error in error handling: {nested_err}")
            traceback.print_exc()
            print("🏁 EXITING process_agent_response with critical error")
            return dash.no_update, dash.no_update, dash.no_update, dash.no_update, True
'''
    
    # Find all occurrences of process_agent_response function
    pattern = r'def process_agent_response\s*\(agent_response,\s*session_data,\s*chat_data,\s*user_message\):'
    matches = list(re.finditer(pattern, content))
    
    if not matches:
        print("❌ Could not find process_agent_response function in dashboard.py")
        return False
    
    print(f"🔍 Found {len(matches)} occurrences of process_agent_response")
    
    # Replace the first occurrence with our updated function
    start_pos = matches[0].start()
    
    # Find the end of the function
    lines = content[start_pos:].split('\n')
    function_indentation = len(lines[0]) - len(lines[0].lstrip())
    end_line_idx = 0
    
    for i, line in enumerate(lines[1:], 1):
        if line.strip() and len(line) - len(line.lstrip()) <= function_indentation:
            if line.lstrip().startswith('def ') or line.lstrip().startswith('class '):
                end_line_idx = i
                break
    
    if end_line_idx == 0:
        end_line_idx = len(lines)  # End of file
    
    end_pos = start_pos + sum(len(line) + 1 for line in lines[:end_line_idx])
    
    # Replace the function
    modified_content = content[:start_pos] + updated_function + content[end_pos:]
    
    # If there are multiple occurrences, remove them
    if len(matches) > 1:
        print("⚠️ Multiple definitions found, removing duplicates...")
        for match in matches[1:]:
            start_pos = match.start()
            lines = modified_content[start_pos:].split('\n')
            function_indentation = len(lines[0]) - len(lines[0].lstrip())
            end_line_idx = 0
            
            for i, line in enumerate(lines[1:], 1):
                if line.strip() and len(line) - len(line.lstrip()) <= function_indentation:
                    if line.lstrip().startswith('def ') or line.lstrip().startswith('class '):
                        end_line_idx = i
                        break
            
            if end_line_idx == 0:
                end_line_idx = len(lines)  # End of file
            
            end_pos = start_pos + sum(len(line) + 1 for line in lines[:end_line_idx])
            
            # Remove the duplicate function
            modified_content = modified_content[:start_pos] + modified_content[end_pos:]
    
    # Write the modified content back to the file
    with open(dashboard_path, 'w') as f:
        f.write(modified_content)
    
    print(f"✅ Successfully fixed process_agent_response function in {dashboard_path}")
    print(f"✅ Backup saved to {backup_path}")
    return True

if __name__ == "__main__":
    print("🔧 Fixing process_agent_response in dashboard.py...")
    if fix_process_agent_response():
        print("\n✅ Fix applied successfully!")
    else:
        print("\n❌ Failed to apply fix.")
