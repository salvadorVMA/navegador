#!/usr/bin/env python3
"""
Test script to verify the integration of the agent's variable selection with the dashboard
"""
import time
import traceback
import concurrent.futures
import json
from pprint import pprint

def test_dashboard_agent_integration():
    """Test the integration between the dashboard and agent for variable selection"""
    print("\n===== Testing Dashboard-Agent Integration =====\n")
    
    # Import required modules
    try:
        from dashboard import handle_auto_next_step
        from agent import create_agent
        import dash
        print("✅ Required modules imported successfully")
    except ImportError as e:
        print(f"❌ Error importing modules: {e}")
        traceback.print_exc()
        return False
    
    print("\n🔄 Creating test session and chat data...")
    
    # Create mock session and chat data
    chat_data = [
        {"type": "user", "content": "qué piensan los mexicanos sobre la salud?", "timestamp": time.strftime("%H:%M")}
    ]
    
    session_data = {
        "pending_main_action": {
            "action_type": "process_user_message",
            "user_message": "qué piensan los mexicanos sobre la salud?",
            "created_at": time.time(),
            "processed": False
        },
        "language": "es",
        "datasets": ["all"],
        "variables": []
    }
    
    print("✅ Test data created")
    
    try:
        print("\n🔄 Simulating handle_auto_next_step with health query...")
        
        # Call handle_auto_next_step with our test data
        # Since we can't directly use Dash callbacks outside a Dash app,
        # we'll extract the core functionality and simulate it
        
        # Get user message from pending action
        pending_action = session_data.get("pending_main_action", {})
        user_message = pending_action.get('user_message', '')
        
        print(f"📝 User message: '{user_message}'")
        
        # Create the agent
        agent = create_agent(enable_persistence=True)
        
        # Set up agent state
        agent_state = {
            "messages": [{"role": "user", "content": user_message}],
            "intent": "",
            "user_query": user_message,
            "original_query": user_message,
            "dataset": session_data.get("datasets", ["ALL"]),
            "selected_variables": session_data.get("variables", []),
            "analysis_type": "descriptive",
            "user_approved": False,
            "analysis_result": {},
            "language": session_data.get('language', 'es')
        }
        
        # Create thread config
        thread_id = f"test_dashboard_{int(time.time())}"
        agent_config = {"configurable": {"thread_id": thread_id}}
        
        # Set timeout
        timeout_seconds = 60
        
        print(f"⏱️ Invoking agent with {timeout_seconds}s timeout...")
        start_time = time.time()
        
        # Use ThreadPoolExecutor for timeout
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(lambda: agent.invoke(agent_state, agent_config))
            
            try:
                # Wait for result with timeout
                agent_response = future.result(timeout=timeout_seconds)
                elapsed = time.time() - start_time
                print(f"✅ Agent response received in {elapsed:.2f} seconds")
                
                # Check for variable selection
                if 'selected_variables' in agent_response and agent_response['selected_variables']:
                    variables = agent_response['selected_variables']
                    print(f"✅ Variables selected: {variables[:5]}...")
                    
                    # Check the last message for response content
                    if 'messages' in agent_response and agent_response['messages']:
                        last_message = agent_response['messages'][-1]
                        if hasattr(last_message, 'content'):
                            content = last_message.content
                            print(f"📝 Response content: \"{content[:100]}...\"")
                        
                    # Verify the integration is working properly
                    if any("SAL" in var for var in variables):
                        print("\n✅ SUCCESS: Health-related variables were correctly selected from the database")
                        return True
                    else:
                        print("\n⚠️ Variables were selected, but they don't appear to be health-related")
                        print(f"Selected variables: {variables}")
                        return False
                else:
                    print("❌ No variables were selected by the agent")
                    print(f"Response keys: {list(agent_response.keys())}")
                    return False
                    
            except concurrent.futures.TimeoutError:
                elapsed = time.time() - start_time
                print(f"❌ Agent timed out after {elapsed:.2f} seconds")
                return False
                
            except Exception as e:
                print(f"❌ Error during agent invocation: {str(e)}")
                traceback.print_exc()
                return False
    
    except Exception as e:
        print(f"❌ Error during test: {str(e)}")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_dashboard_agent_integration()
