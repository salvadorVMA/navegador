"""
Debug Variable Search - Diagnostic Tool for Variable Search Performance
=======================================================================

This tool helps diagnose and fix performance issues in the variable search functionality
of the dashboard. It analyzes the current settings, tests different timeout values,
and provides recommendations for optimizing the search process.
"""

import sys
import os
import time
import traceback
from typing import Dict, List, Any, Optional

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

print("Variable Search Diagnostics")
print("==========================")
print("Starting diagnostics for variable search functionality...")

# Try importing required modules
try:
    # Test importing key modules
    import concurrent.futures
    import langchain
    from langchain.schema.runnable import RunnableConfig
    from state_normalizer import normalize_state, normalize_config, create_agent_state
    
    # Import agent module
    try:
        import agent
        print("✅ Successfully imported agent module")
    except ImportError:
        print("❌ Could not import agent module")
        sys.exit(1)
        
    # Try to import variable selection modules
    try:
        from variable_selector import _variable_selector, _database_selector
        from dataset_knowledge import rev_topic_dict, pregs_dict
        print(f"✅ Successfully imported variable selector modules")
    except ImportError as e:
        print(f"❌ Could not import variable selector modules: {e}")
        sys.exit(1)
        
    # Check for dashboard.py
    if not os.path.exists("dashboard.py"):
        print("❌ dashboard.py not found in current directory")
        sys.exit(1)
    
    print("\nEnvironment Setup:")
    print("-----------------")
    print(f"Python version: {sys.version}")
    print(f"Current directory: {os.getcwd()}")
    
    # Analyze dashboard.py timeout settings
    print("\nDashboard Timeout Settings:")
    print("-------------------------")
    with open("dashboard.py", "r") as f:
        dashboard_code = f.read()
        
    # Extract timeout values
    import re
    agent_timeout_match = re.search(r'future\.result\(timeout=(\d+)\)\s*#\s*(\d+)\s*second\s*timeout.*agent', dashboard_code)
    query_timeout_match = re.search(r'future\.result\(timeout=(\d+)\)\s*#\s*(\d+)\s*second\s*timeout.*query', dashboard_code)
    action_timeout_match = re.search(r'timeout_seconds\s*=\s*(\d+)\s*#\s*Expire\s*pending\s*actions', dashboard_code)
    
    agent_timeout = int(agent_timeout_match.group(1)) if agent_timeout_match else "Not found"
    query_timeout = int(query_timeout_match.group(1)) if query_timeout_match else "Not found"
    action_timeout = int(action_timeout_match.group(1)) if action_timeout_match else "Not found"
    
    print(f"Agent greeting test timeout: {agent_timeout} seconds")
    print(f"Agent query test timeout: {query_timeout} seconds")
    print(f"Pending action timeout: {action_timeout} seconds")
    
    # Analyze variable selection process
    print("\nVariable Selection Process:")
    print("-------------------------")
    
    # Start a test variable search
    print("\nStarting test variable search with query: 'politics'...")
    
    # Create a test agent state
    test_state = {
        "messages": [{"role": "user", "content": "politics"}],
        "intent": "query_variable_database",
        "user_query": "politics",
        "original_query": "politics",
        "dataset": ["ALL"],
        "selected_variables": [],
        "analysis_type": "descriptive",
        "user_approved": False,
        "analysis_result": {}
    }
    
    # Create a thread config for the test
    thread_id = f"test_{int(time.time())}"
    test_config = {
        "configurable": {
            "thread_id": thread_id
        }
    }
    
    # Initialize agent for testing
    print("Initializing agent for testing...")
    test_agent = agent.create_agent(with_persistence=True)
    
    # Test variable search with extended timeout
    print("Running variable search test with 120s timeout...")
    start_time = time.time()
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future = executor.submit(test_agent.invoke, test_state, test_config)
        try:
            result = future.result(timeout=120)  # Extended timeout for test
            elapsed = time.time() - start_time
            print(f"✅ Variable search completed in {elapsed:.2f} seconds")
            
            # Analyze result
            if isinstance(result, dict) and 'selected_variables' in result:
                selected_vars = result.get('selected_variables', [])
                dataset = result.get('dataset', [])
                print(f"   Selected dataset: {dataset}")
                print(f"   Selected variables: {len(selected_vars)} total")
                print(f"   First 5 variables: {selected_vars[:5]}")
                
                # Check messages
                if 'messages' in result:
                    msgs = result.get('messages', [])
                    if msgs and len(msgs) > 0:
                        last_msg = msgs[-1]
                        content = last_msg.get('content', '') if isinstance(last_msg, dict) else str(last_msg)
                        print(f"   Response summary: {content[:100]}...")
            else:
                print("❌ No variables selected in result")
                
        except concurrent.futures.TimeoutError:
            elapsed = time.time() - start_time
            print(f"❌ Variable search timed out after {elapsed:.2f} seconds")
            print("This indicates a deeper issue with the variable search process")
        except Exception as e:
            elapsed = time.time() - start_time
            print(f"❌ Variable search error after {elapsed:.2f} seconds: {e}")
            traceback.print_exc()
    
    # Recommendations based on analysis
    print("\nRecommendations:")
    print("--------------")
    
    # Recommend timeout values based on testing
    recommended_query_timeout = max(int(elapsed * 1.5) if 'elapsed' in locals() else 120, 60)
    recommended_action_timeout = max(int(elapsed * 2) if 'elapsed' in locals() else 180, 90)
    
    print(f"1. Increase agent query timeout to {recommended_query_timeout} seconds (currently {query_timeout})")
    print(f"2. Increase pending action timeout to {recommended_action_timeout} seconds (currently {action_timeout})")
    print("3. Implement progressive variable search to provide partial results")
    print("4. Add detailed logging during variable search to identify bottlenecks")
    print("5. Optimize ChromaDB query filtering to improve performance")
    
    # Provide code snippets for implementation
    print("\nCode Snippets for Implementation:")
    print("------------------------------")
    print("""
# 1. Update timeout values in dashboard.py:
                query_result = future.result(timeout={query_timeout})  # {query_timeout} second timeout (increased from {current_timeout})
                
# 2. Update action timeout in dashboard.py:
    timeout_seconds = {action_timeout}  # Expire pending actions after {action_timeout} seconds (increased from {current_timeout})
    
# 3. Add progressive variable search implementation in dashboard.py:
    def handle_auto_next_step(...):
        ...
        # Add progress tracking
        if pending_action and 'progress' in pending_action:
            progress = pending_action['progress']
            # Show progress updates in chat
            progress_message = f"Variable search {progress}% complete..."
            # Add to chat history
            ...
    """.format(
        query_timeout=recommended_query_timeout,
        action_timeout=recommended_action_timeout,
        current_timeout="30" if query_timeout == "Not found" else query_timeout
    ))
    
except Exception as e:
    print(f"❌ Diagnostics error: {e}")
    traceback.print_exc()
