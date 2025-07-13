#!/usr/bin/env python3
"""
Create a completely new version of dashboard.py with debugging information
"""

import os
import sys
import shutil
import ast
from datetime import datetime

def backup_file(file_path):
    """Create a backup of the file before modifying it"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f"{file_path}.{timestamp}.bak"
    shutil.copy2(file_path, backup_path)
    print(f"✅ Created backup: {backup_path}")
    return backup_path

def create_debug_dashboard():
    """Create a debug version of dashboard.py"""
    dashboard_path = 'dashboard.py'
    if not os.path.exists(dashboard_path):
        print(f"❌ File not found: {dashboard_path}")
        return False
    
    debug_path = 'debug_dashboard.py'
    
    # Create backup
    backup_path = backup_file(dashboard_path)
    
    # Simple debugging version that just initializes and prints debug info
    debug_content = '''"""
Debug version of dashboard.py that just initializes and shows if the agent works
"""
import os
import sys
import time
import traceback
from datetime import datetime

print("🔄 Starting debug dashboard...")

try:
    print("🔄 Importing required packages...")
    import dash
    from dash import dcc, html, Input, Output, State, callback, ctx
    import dash_bootstrap_components as dbc
    import concurrent.futures
    import threading
    import uuid
    
    print("✅ Basic imports successful")
    
    try:
        print("🔄 Trying to import agent...")
        from agent import create_agent
        print("✅ Agent module imported")
        
        # Try creating an agent
        print("🔄 Creating agent...")
        agent = create_agent(enable_persistence=True)
        print("✅ Agent created")
        
        # Test agent with a simple query
        print("🔄 Testing agent with a simple greeting...")
        state = {
            "messages": [{"role": "user", "content": "Hello"}],
            "intent": "answer_general_questions",
            "user_query": "Hello",
            "original_query": "Hello",
            "dataset": ["ALL"],
            "selected_variables": [],
            "analysis_type": "descriptive",
            "user_approved": False,
            "analysis_result": {}
        }
        
        thread_id = f"chat_{int(time.time())}"
        config = {"configurable": {"thread_id": thread_id}}
        
        print("🔄 Invoking agent...")
        try:
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(agent.invoke, state, config=config)
                response = future.result(timeout=10)
                print(f"✅ Agent response type: {type(response)}")
                print(f"✅ Agent response: {response}")
        except Exception as e:
            print(f"❌ Error invoking agent: {e}")
            traceback.print_exc()
        
        # Test with health query
        print("🔄 Testing agent with health query...")
        health_query = "qué piensan los mexicanos sobre la salud?"
        health_state = {
            "messages": [{"role": "user", "content": health_query}],
            "intent": "query_variable_database",
            "user_query": health_query,
            "original_query": health_query,
            "dataset": ["ALL"],
            "selected_variables": [],
            "analysis_type": "descriptive",
            "user_approved": False,
            "analysis_result": {}
        }
        
        thread_id = f"chat_{int(time.time())}"
        config = {"configurable": {"thread_id": thread_id}}
        
        print("🔄 Invoking agent with health query...")
        try:
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(agent.invoke, health_state, config=config)
                response = future.result(timeout=15)
                print(f"✅ Health query response type: {type(response)}")
                if hasattr(response, 'keys'):
                    print(f"✅ Response keys: {list(response.keys())}")
                content = None
                if hasattr(response, 'messages'):
                    msgs = response.messages
                    if msgs and len(msgs) > 0:
                        last_msg = msgs[-1]
                        if hasattr(last_msg, 'content'):
                            content = last_msg.content
                print(f"✅ Content: {content[:100] if content else 'None'}...")
        except Exception as e:
            print(f"❌ Error with health query: {e}")
            traceback.print_exc()
        
    except ImportError as e:
        print(f"❌ Could not import agent module: {e}")
    except Exception as e:
        print(f"❌ Error creating agent: {e}")
        traceback.print_exc()
    
    print("✅ Debug complete")
    
except Exception as e:
    print(f"❌ Critical error: {e}")
    traceback.print_exc()

print("🏁 Debug dashboard finished")
'''
    
    # Write the debug content to the file
    with open(debug_path, 'w') as f:
        f.write(debug_content)
    
    print(f"✅ Successfully created debug dashboard in {debug_path}")
    print(f"✅ Original dashboard backed up to {backup_path}")
    return True

if __name__ == "__main__":
    print("🔧 Creating debug dashboard...")
    if create_debug_dashboard():
        print("\n✅ Debug dashboard created successfully!")
        print("\n📋 To test the agent:")
        print("1. Run: python debug_dashboard.py")
        print("2. The script will test both a simple greeting and a health-related query\n")
    else:
        print("\n❌ Failed to create debug dashboard.")
