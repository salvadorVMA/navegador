#!/usr/bin/env python3
"""
Debug script to add logging statements to dashboard.py
"""
import sys
import os

def add_debug_logging():
    file_path = 'dashboard.py'
    with open(file_path, 'r') as f:
        content = f.read()

    # Add debugging to process_agent_response function
    content = content.replace('print(f"✅ Agent response processed: {content[:50]}...")', 
                           'print(f"✅✅✅ Agent response processed at {time.time()}: {content[:50]}...")')

    # Add debugging to handle_auto_next_step
    content = content.replace('# First try to use the agent if available', 
                           '# First try to use the agent if available\n        print("🚀🚀🚀 Attempting to use the agent now!")')
    
    content = content.replace('agent_response = future.result(timeout=AGENT_TIMEOUT)', 
                           'print("⏳⏳⏳ Waiting for agent response...")\n                        agent_response = future.result(timeout=AGENT_TIMEOUT)')
    
    content = content.replace('return process_agent_response(agent_response, session_data, chat_data, user_message)', 
                           'print("🎯🎯🎯 Got agent response, calling process_agent_response")\n                        return process_agent_response(agent_response, session_data, chat_data, user_message)')

    # Save to a new file for testing
    with open('dashboard_debug.py', 'w') as f:
        f.write(content)
    print('Created dashboard_debug.py with additional debugging output')

if __name__ == "__main__":
    add_debug_logging()
