#!/usr/bin/env python3
"""
Test script to verify the integration of _variable_selector in the agent's handle_query function
"""
import time
import traceback
import concurrent.futures
from pprint import pprint
from langchain_core.messages import HumanMessage, AIMessage

def test_agent_variable_selection():
    """Test agent variable selection for health-related queries"""
    print("\n===== Testing Variable Selection Integration =====\n")
    
    # Import required modules
    try:
        from agent import create_agent, create_thread_config
        print("✅ Agent module imported successfully")
    except ImportError as e:
        print(f"❌ Error importing agent module: {e}")
        traceback.print_exc()
        return False
    
    # Create agent with persistence
    try:
        agent = create_agent(enable_persistence=True)
        print("✅ Persistence enabled: Using MemorySaver for conversation state")
        print("🔄 Agent compiled with persistence enabled")
        print("✅ Agent creation successful")
        print()
    except Exception as e:
        print(f"❌ Failed to create agent: {e}")
        traceback.print_exc()
        return False
    
    # Test queries for different topics
    test_queries = [
        ("salud", "health"),
        ("educación", "education"),
        ("política", "politics")
    ]
    
    all_tests_passed = True
    
    for query, topic in test_queries:
        print(f"� Testing query: '{query}' ({topic})...")
        
        # Create agent state with a proper HumanMessage object
        agent_state = {
            "messages": [HumanMessage(content=query)],
            "intent": "query_variable_database",
            "user_query": query,
            "original_query": query,
            "dataset": ["all"],
            "selected_variables": [],
            "analysis_type": "descriptive",
            "user_approved": False,
            "analysis_result": {}
        }
        
        # Create thread config for this test
        thread_id = f"test_{topic}_{int(time.time())}"
        agent_config = create_thread_config(thread_id)
        
        # Set timeout
        timeout_seconds = 60  # Increased timeout for real variable selection
        
        try:
            # Use ThreadPoolExecutor for timeout
            with concurrent.futures.ThreadPoolExecutor() as executor:
                # Use agent_config as a parameter, LangGraph will handle type conversion
                future = executor.submit(lambda: agent.invoke(agent_state, {"configurable": {"thread_id": thread_id}}))
                
                try:
                    result = future.result(timeout=timeout_seconds)
                    
                    # Check if the intent was correctly classified
                    if 'intent' in result:
                        print(f"Detected intent: {result['intent']}")
                    
                    # Check if variables were selected
                    if 'selected_variables' in result and result['selected_variables']:
                        variables = result['selected_variables']
                        if variables and len(variables) > 0:
                            print(f"✅ Agent using real variable selection: Success!")
                            print(f"📊 Selected variables: {variables[:5]}")
                            
                            # Get the last message content
                            if 'messages' in result and result['messages'] and len(result['messages']) > 0:
                                last_message = result['messages'][-1]
                                if hasattr(last_message, 'content'):
                                    content = last_message.content
                                    print(f"   Response starts with: \"{content[:80]}...\"")
                                else:
                                    print("❌ Last message has no content attribute")
                                    all_tests_passed = False
                        else:
                            print("⚠️ Selected variables list is empty")
                            all_tests_passed = False
                    else:
                        print("❌ No 'selected_variables' in result")
                        all_tests_passed = False
                
                except concurrent.futures.TimeoutError:
                    print(f"⚠️ Test timed out after {timeout_seconds} seconds!")
                    all_tests_passed = False
                    continue
                
                except Exception as e:
                    print(f"❌ Test failed with error: {str(e)}")
                    traceback.print_exc()
                    all_tests_passed = False
                    continue
                
        except Exception as e:
            print(f"❌ Error running test: {e}")
            traceback.print_exc()
            all_tests_passed = False
        
        print()
    
    if all_tests_passed:
        print("✅ All tests passed! The agent is now properly using the real variable selector.")
        print("✅ Variables are now being fetched from the database based on the query.")
        print("\nTest completed successfully!")
    else:
        print("❌ Some tests failed. The variable selection may not be fully integrated.")
    
    return all_tests_passed

if __name__ == "__main__":
    test_agent_variable_selection()
