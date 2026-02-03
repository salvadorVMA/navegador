#!/usr/bin/env python3
"""
Debug Agent Checkpointer Test

This script focuses specifically on testing the checkpointer functionality of the agent.
It verifies if the agent's checkpointer is correctly saving and retrieving state between invocations.

Run with: python debug_agent_checkpointer.py
"""

import os
import sys
import time
import json
import uuid
import traceback
from typing import Dict, Any, List, Optional
import concurrent.futures

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Attempt to import required modules
try:
    from langchain.schema.runnable import RunnableConfig
    from agent import create_agent, AgentState
    from langchain_openai import ChatOpenAI

    MODULES_AVAILABLE = True
    print("✅ All required modules are available")
except ImportError as e:
    MODULES_AVAILABLE = False
    print(f"⚠️ Some required modules are not available: {e}")
    print("This script requires langchain, langchain-openai, etc.")
    sys.exit(1)

def create_agent_config(thread_id: str, checkpoint_id: Optional[str] = None) -> Any:
    """Create a configuration dict for agent invocation with proper checkpointer config"""
    if checkpoint_id is None:
        checkpoint_id = str(uuid.uuid4())
    
    # Create a proper config dict that will be compatible with RunnableConfig
    config_dict = {
        "configurable": {
            "thread_id": thread_id,
            "checkpoint_id": checkpoint_id,
            "checkpoint_ns": "chat_session"
        }
    }
    
    # Return as RunnableConfig
    try:
        return RunnableConfig(configurable=config_dict["configurable"])
    except Exception:
        return config_dict

def print_section(title):
    """Print a section title with formatting"""
    print(f"\n{'=' * 80}")
    print(f"  {title}")
    print(f"{'=' * 80}\n")

def run_agent_with_timeout(agent, state, config, timeout=10):
    """Run agent with timeout and return result or error"""
    start_time = time.time()
    
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future = executor.submit(agent.invoke, state, config=config)
        try:
            result = future.result(timeout=timeout)
            elapsed = time.time() - start_time
            return {"success": True, "elapsed": elapsed, "result": result}
        except concurrent.futures.TimeoutError:
            elapsed = time.time() - start_time
            return {"success": False, "elapsed": elapsed, "error": "Timeout"}
        except Exception as e:
            elapsed = time.time() - start_time
            return {"success": False, "elapsed": elapsed, "error": str(e)}

def test_checkpointer_persistence():
    """Test if the agent's checkpointer persists state between invocations"""
    print_section("Checkpointer Persistence Test")
    
    # Initialize agent
    try:
        print("🔄 Creating agent with persistence...")
        agent = create_agent(enable_persistence=True)
        print("✅ Agent initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize agent: {e}")
        traceback.print_exc()
        return
    
    # Create a unique thread ID for this test series
    thread_id = f"checkpointer_test_{int(time.time())}"
    print(f"🧵 Using thread ID: {thread_id}")
    
    # First invocation: Initialize the state
    print("\n1️⃣ First invocation: Initialize state")
    
    initial_state = {
        "messages": [{"role": "user", "content": "Hello"}],
        "intent": "answer_general_questions",
        "user_query": "Hello",
        "original_query": "Hello",
        "dataset": ["all"],
        "selected_variables": [],
        "analysis_type": "descriptive",
        "user_approved": False,
        "analysis_result": {}
    }
    
    initial_config = create_agent_config(thread_id)
    print(f"Initial config: {initial_config}")
    
    result1 = run_agent_with_timeout(agent, initial_state, initial_config, 10)
    
    if not result1["success"]:
        print(f"❌ First invocation failed: {result1.get('error', 'Unknown error')}")
        return
    
    print(f"✅ First invocation successful ({result1['elapsed']:.2f}s)")
    
    # Check for response in first invocation
    first_response = None
    if isinstance(result1["result"], dict) and "messages" in result1["result"]:
        messages = result1["result"]["messages"]
        if messages and len(messages) > 1:  # Should have at least the user message and a response
            if isinstance(messages[-1], dict):
                first_response = messages[-1].get("content", "")
            else:
                first_response = str(messages[-1])
        
    if first_response:
        print(f"First response: {first_response[:100]}...")
    else:
        print("⚠️ No response found in first invocation result")
    
    # Wait briefly to ensure state is saved
    print("\nWaiting 2 seconds to ensure state is saved...")
    time.sleep(2)
    
    # Second invocation: Check if state persists
    print("\n2️⃣ Second invocation: Check state persistence")
    
    follow_up_state = {
        "messages": [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": first_response or ""},
            {"role": "user", "content": "What do Mexicans think about health?"}
        ],
        "intent": "query_variable_database",
        "user_query": "What do Mexicans think about health?",
        "original_query": "What do Mexicans think about health?",
        "dataset": ["all"],
        "selected_variables": [],
        "analysis_type": "descriptive",
        "user_approved": False,
        "analysis_result": {}
    }
    
    # Use same thread_id but new checkpoint_id
    follow_up_config = create_agent_config(thread_id)
    print(f"Follow-up config: {follow_up_config}")
    
    result2 = run_agent_with_timeout(agent, follow_up_state, follow_up_config, 10)
    
    if not result2["success"]:
        print(f"❌ Second invocation failed: {result2.get('error', 'Unknown error')}")
        return
    
    print(f"✅ Second invocation successful ({result2['elapsed']:.2f}s)")
    
    # Check for response in second invocation
    second_response = None
    if isinstance(result2["result"], dict) and "messages" in result2["result"]:
        messages = result2["result"]["messages"]
        if messages and len(messages) > 3:  # Should have initial messages plus response
            if isinstance(messages[-1], dict):
                second_response = messages[-1].get("content", "")
            else:
                second_response = str(messages[-1])
    
    if second_response:
        print(f"Second response: {second_response[:100]}...")
    else:
        print("⚠️ No response found in second invocation result")
    
    # Check if selected_variables field was updated (indication of successful query)
    selected_vars = result2["result"].get("selected_variables", []) if isinstance(result2["result"], dict) else []
    if selected_vars:
        print(f"✅ Found {len(selected_vars)} selected variables in result")
        print(f"Sample variables: {selected_vars[:5]}")
    else:
        print("❌ No selected variables in result - query may have failed")
    
    # Third invocation: Use minimal state to test if checkpointer fills in the gaps
    print("\n3️⃣ Third invocation: Minimal state with checkpointer retrieval")
    
    minimal_state = {
        "messages": [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": first_response or ""},
            {"role": "user", "content": "What do Mexicans think about health?"},
            {"role": "assistant", "content": second_response or ""},
            {"role": "user", "content": "Show me more variables about education"}
        ],
        "intent": "query_variable_database"
        # Intentionally missing other fields to test if checkpointer provides them
    }
    
    minimal_config = create_agent_config(thread_id)
    print(f"Minimal config: {minimal_config}")
    
    result3 = run_agent_with_timeout(agent, minimal_state, minimal_config, 10)
    
    if not result3["success"]:
        print(f"❌ Third invocation failed: {result3.get('error', 'Unknown error')}")
    else:
        print(f"✅ Third invocation successful ({result3['elapsed']:.2f}s)")
        
        # Check if we got a proper response
        third_response = None
        if isinstance(result3["result"], dict) and "messages" in result3["result"]:
            messages = result3["result"]["messages"]
            if messages and len(messages) > 5:  # Should have all previous messages plus response
                if isinstance(messages[-1], dict):
                    third_response = messages[-1].get("content", "")
                else:
                    third_response = str(messages[-1])
        
        if third_response:
            print(f"Third response: {third_response[:100]}...")
        else:
            print("⚠️ No response found in third invocation result")
    
    # Initialize third_response for safety
    third_response = None
    if result3["success"] and "result" in result3:
        if isinstance(result3["result"], dict) and "messages" in result3["result"]:
            messages = result3["result"]["messages"]
            if messages and len(messages) > 5:
                if isinstance(messages[-1], dict):
                    third_response = messages[-1].get("content", "")
                else:
                    third_response = str(messages[-1])
    
    # Save detailed results for further analysis
    results = {
        "thread_id": thread_id,
        "initial_state": initial_state,
        "follow_up_state": follow_up_state,
        "minimal_state": minimal_state,
        "result1": {k: v for k, v in result1.items() if k != "result"},
        "result2": {k: v for k, v in result2.items() if k != "result"},
        "result3": {k: v for k, v in result3.items() if k != "result"},
        "first_response_sample": first_response[:100] if first_response else None,
        "second_response_sample": second_response[:100] if second_response else None,
        "third_response_sample": third_response[:100] if third_response else None,
        "selected_variables_count": len(selected_vars),
        "selected_variables_sample": selected_vars[:5] if selected_vars else []
    }
    
    with open("checkpointer_debug_results.json", "w") as f:
        json.dump(results, f, indent=2)
    
    print("\nDetailed results saved to checkpointer_debug_results.json")
    
    # Summary
    print_section("Summary")
    if result1["success"] and result2["success"] and result3["success"]:
        print("✅ All tests passed - checkpointer appears to be working correctly")
    elif result1["success"] and result2["success"] and not result3["success"]:
        print("⚠️ Partial success - checkpointer works with complete state but fails with minimal state")
    elif result1["success"] and not result2["success"]:
        print("❌ Checkpointer failed - state not persisting between invocations")
    else:
        print("❌ Test inconclusive - first invocation failed")

if __name__ == "__main__":
    test_checkpointer_persistence()
