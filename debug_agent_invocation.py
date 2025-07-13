#!/usr/bin/env python3
"""
Debug Agent Invocation Test

This script helps diagnose why agent invocation works in test but fails in real queries.
It tests:
1. Agent initialization
2. Checkpointer functionality
3. Different ways of constructing agent state
4. Thread ID management
5. Intent processing

Run with: python debug_agent_invocation.py
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
    from intent_classifier import intent_dict, _classify_intent
    from langchain_openai import ChatOpenAI

    MODULES_AVAILABLE = True
    print("✅ All required modules are available")
except ImportError as e:
    MODULES_AVAILABLE = False
    print(f"⚠️ Some required modules are not available: {e}")
    print("This script requires langchain, langchain-openai, etc.")
    sys.exit(1)

# Helper functions
def create_agent_config(thread_id: Optional[str] = None) -> Any:
    """Create a configuration dict for agent invocation with proper checkpointer config"""
    if thread_id is None:
        thread_id = f"chat_{int(time.time())}"
    
    # Create a proper config dict that will be compatible with RunnableConfig
    config_dict = {
        "configurable": {
            "thread_id": thread_id,
            "checkpoint_id": str(uuid.uuid4()),
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

def print_dict_diff(dict1, dict2, name1="Test", name2="Real"):
    """Print differences between two dictionaries"""
    print(f"\n--- Comparing {name1} vs {name2} ---")
    
    # Check keys in both dicts
    all_keys = set(dict1.keys()) | set(dict2.keys())
    
    for key in sorted(all_keys):
        if key not in dict1:
            print(f"Missing in {name1}: {key} = {dict2[key]}")
        elif key not in dict2:
            print(f"Missing in {name2}: {key} = {dict1[key]}")
        elif dict1[key] != dict2[key]:
            print(f"Different values for {key}:")
            print(f"  {name1}: {dict1[key]}")
            print(f"  {name2}: {dict2[key]}")
    
    if set(dict1.keys()) == set(dict2.keys()):
        print(f"Both {name1} and {name2} have the same keys")

def run_agent_test(agent, state, config, timeout=10, label="Test"):
    """Run a test with the agent and return result"""
    print(f"🔄 Running {label} with timeout {timeout}s...")
    print(f"   Intent: {state.get('intent', 'None')}")
    print(f"   State keys: {list(state.keys())}")
    
    start_time = time.time()
    
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future = executor.submit(agent.invoke, state, config=config)
        try:
            result = future.result(timeout=timeout)
            elapsed = time.time() - start_time
            print(f"✅ {label} successful after {elapsed:.2f}s")
            return {"success": True, "elapsed": elapsed, "result": result}
        except concurrent.futures.TimeoutError:
            elapsed = time.time() - start_time
            print(f"⚠️ {label} timed out after {elapsed:.2f}s")
            return {"success": False, "elapsed": elapsed, "error": "Timeout"}
        except Exception as e:
            elapsed = time.time() - start_time
            print(f"❌ {label} failed after {elapsed:.2f}s: {e}")
            traceback.print_exc()
            return {"success": False, "elapsed": elapsed, "error": str(e)}

def main():
    """Main test function"""
    print_section("Agent Initialization Test")
    
    # Initialize agent
    try:
        print("🔄 Creating agent with persistence...")
        agent = create_agent(enable_persistence=True)
        print("✅ Agent initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize agent: {e}")
        traceback.print_exc()
        return
    
    # Test 1: Test query with hardcoded state (similar to test_agent_async)
    print_section("Test 1: Hardcoded State (Test Query)")
    test_state = {
        "messages": [{"role": "user", "content": "What do Mexicans think about health?"}],
        "intent": "query_variable_database",
        "user_query": "What do Mexicans think about health?",
        "original_query": "What do Mexicans think about health?",
        "dataset": ["all"],
        "selected_variables": [],
        "analysis_type": "descriptive",
        "user_approved": False,
        "analysis_result": {}
    }
    
    # Create config without explicit thread_id (like in test_agent_async)
    test_config = create_agent_config()
    
    # Run test query
    test_result = run_agent_test(agent, test_state, test_config, 10, "Test Query")
    
    # Test 2: Real query with dynamically constructed state
    print_section("Test 2: Dynamically Constructed State (Real Query)")
    user_message = "What do Mexicans think about health?"
    
    # Attempt to classify intent
    try:
        llm = ChatOpenAI(model="gpt-4o-mini")
        intent = _classify_intent(user_message, intent_dict, llm)
        print(f"🎯 Classified intent: {intent}")
    except Exception as e:
        print(f"⚠️ Intent classification failed: {e}")
        intent = "query_variable_database"  # Fallback to hardcoded intent
    
    # Construct state like in handle_auto_next_step
    real_state = {
        "messages": [{"role": "user", "content": user_message}],
        "intent": intent,
        "user_query": user_message,
        "original_query": user_message,
        "dataset": ["ALL"],  # Note: "ALL" vs "all" in test
        "selected_variables": [],
        "analysis_type": "descriptive",
        "user_approved": False,
        "analysis_result": {},
        "language": "en"  # This is in real query but not in test
    }
    
    # Create config with explicit thread_id (like in handle_auto_next_step)
    thread_id = f"chat_{int(time.time())}"
    real_config = create_agent_config(thread_id)
    
    # Run real query
    real_result = run_agent_test(agent, real_state, real_config, 10, "Real Query")
    
    # Test 3: Modified real query with test parameters
    print_section("Test 3: Hybrid State (Test Query Format with Real Parameters)")
    
    # Use test state but with real query parameters
    hybrid_state = {
        "messages": [{"role": "user", "content": user_message}],
        "intent": "query_variable_database",  # Explicitly set to known working intent
        "user_query": user_message,
        "original_query": user_message,
        "dataset": ["all"],  # Using lowercase like in test
        "selected_variables": [],
        "analysis_type": "descriptive",
        "user_approved": False,
        "analysis_result": {}
        # No "language" field like in the test
    }
    
    # Use test config style
    hybrid_config = create_agent_config()
    
    # Run hybrid query
    hybrid_result = run_agent_test(agent, hybrid_state, hybrid_config, 10, "Hybrid Query")
    
    # Compare states and results
    print_section("State Comparison")
    print_dict_diff(test_state, real_state, "Test State", "Real State")
    
    print_section("Config Comparison")
    print(f"Test Config: {test_config}")
    print(f"Real Config: {real_config}")
    
    print_section("Result Analysis")
    
    # Compare success/failure
    if test_result["success"] and not real_result["success"]:
        print("✅ Successfully reproduced the issue: Test works but Real fails")
    elif test_result["success"] and real_result["success"]:
        print("⚠️ Both tests worked - issue not reproduced")
    elif not test_result["success"] and not real_result["success"]:
        print("⚠️ Both tests failed - agent may be completely broken")
    else:
        print("❓ Unexpected: Test failed but Real worked")
    
    # Check if the hybrid approach worked
    if hybrid_result["success"]:
        print("✅ Hybrid approach worked - problem is likely in state construction")
        if "intent" in hybrid_state and hybrid_state["intent"] == "query_variable_database":
            print("🔍 Key difference: hardcoded intent 'query_variable_database' vs dynamic intent")
    else:
        print("❌ Hybrid approach also failed")
    
    # Save detailed results for further analysis
    with open("agent_debug_results.json", "w") as f:
        json.dump({
            "test_state": test_state,
            "real_state": real_state,
            "hybrid_state": hybrid_state,
            "test_result": {k: v for k, v in test_result.items() if k != "result"},
            "real_result": {k: v for k, v in real_result.items() if k != "result"},
            "hybrid_result": {k: v for k, v in hybrid_result.items() if k != "result"}
        }, f, indent=2)
    
    print("\nDetailed results saved to agent_debug_results.json")

if __name__ == "__main__":
    main()
