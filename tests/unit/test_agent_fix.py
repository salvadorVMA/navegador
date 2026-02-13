"""
Test script to verify agent routing is working correctly
"""
import time
import json
import traceback
import concurrent.futures

# Import agent creation function
try:
    from agent import create_agent
    print("✅ Agent module imported successfully")
except ImportError as e:
    import pytest
    pytest.skip(f"Agent module not available: {e}", allow_module_level=True)

def create_agent_config(thread_id=None):
    """Create a configuration dict for agent invocation"""
    import time
    import uuid
    
    if thread_id is None:
        thread_id = f"test_{int(time.time())}"
    
    # Create a proper config dict that will be compatible with RunnableConfig
    config_dict = {
        "configurable": {
            "thread_id": thread_id,
            "checkpoint_id": str(uuid.uuid4()),
            "checkpoint_ns": "test_session"
        }
    }
    
    # Try to convert to RunnableConfig when available
    try:
        from langchain.schema.runnable import RunnableConfig
        return RunnableConfig(configurable=config_dict["configurable"])
    except Exception:
        # Fallback to dict if conversion fails
        return config_dict

def test_query_with_timeout(agent, query, intent="query_variable_database", timeout=15):
    """
    Test a specific query with timeout handling
    
    Args:
        agent: The agent to test
        query: The query string
        intent: The intent to set (default: query_variable_database)
        timeout: Maximum time to wait for response in seconds
        
    Returns:
        Tuple of (success, result_or_error)
    """
    print(f"\n🔍 Testing query: '{query}' with intent '{intent}'")
    
    # Create agent state for testing
    test_state = {
        "messages": [{"role": "user", "content": query}],
        "intent": intent,
        "user_query": query,
        "original_query": query,
        "dataset": ["all"],
        "selected_variables": [],
        "analysis_type": "descriptive",
        "user_approved": False,
        "analysis_result": {}
    }
    
    # Create a test config
    test_config = create_agent_config()
    
    # Measure timing
    start_time = time.time()
    
    # Use ThreadPoolExecutor to enforce timeout
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future = executor.submit(agent.invoke, test_state, config=test_config)
        try:
            # Wait for result with timeout
            result = future.result(timeout=timeout)
            elapsed = time.time() - start_time
            
            print(f"✅ Test successful! Response received in {elapsed:.2f} seconds")
            
            # Print basic result info
            if isinstance(result, dict):
                # Get the keys in the result
                print(f"  Result contains keys: {list(result.keys())}")
                
                # Check for messages
                if 'messages' in result and result['messages']:
                    last_message = result['messages'][-1]
                    if isinstance(last_message, dict) and 'content' in last_message:
                        content = last_message['content']
                        print(f"  Last message content: {content[:100]}...")
                    else:
                        print(f"  Last message: {str(last_message)[:100]}...")
                
                # Check for other important fields
                if 'selected_variables' in result:
                    print(f"  Selected variables: {result['selected_variables'][:5]}...")
                    
                if 'dataset' in result:
                    print(f"  Selected dataset: {result['dataset']}")
                    
                # Check for routing info
                print(f"  Final intent: {result.get('intent', 'Not set')}")
            else:
                print(f"  Result is not a dict: {type(result)}")
                
            return True, result
        
        except concurrent.futures.TimeoutError:
            elapsed = time.time() - start_time
            print(f"⚠️ Test timed out after {elapsed:.2f} seconds!")
            return False, f"Timeout after {elapsed:.2f}s"
        
        except Exception as e:
            elapsed = time.time() - start_time
            print(f"❌ Test failed with error: {str(e)}")
            traceback.print_exc()
            return False, str(e)

def main():
    """Main test function"""
    print("🚀 Creating agent...")
    try:
        # Create agent without persistence for testing
        agent = create_agent(enable_persistence=False)
        print("✅ Agent created successfully")
    except Exception as e:
        print(f"❌ Failed to create agent: {e}")
        traceback.print_exc()
        return

    # Test queries
    test_queries = [
        # Format: (query_text, expected_intent)
        ("Hello, what can you do?", "answer_general_questions"),
        ("What datasets do you have?", "answer_general_questions"),
        ("What do Mexicans think about health?", "query_variable_database"),
        ("qué piensan los mexicanos sobre la salud?", "query_variable_database"),
        ("Tell me about education variables", "query_variable_database"),
    ]
    
    results = []
    
    for query, intent in test_queries:
        success, result = test_query_with_timeout(agent, query, intent, timeout=20)
        results.append({
            "query": query,
            "intent": intent,
            "success": success,
            "result": str(result) if not isinstance(result, dict) else "See detailed output above"
        })
    
    # Print summary
    print("\n=== TEST SUMMARY ===")
    for i, r in enumerate(results):
        status = "✅ PASSED" if r["success"] else "❌ FAILED"
        print(f"{i+1}. {status} - '{r['query']}' ({r['intent']})")

if __name__ == "__main__":
    main()
