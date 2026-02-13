#!/usr/bin/env python3
"""
State Construction Test

This script focuses on diagnosing the mismatch between how agent state is constructed
in tests vs. real queries, particularly with the intent field.

The test runs several different variations of agent state construction to identify
which specific differences cause failures.
"""

import os
import sys
import time
import json
import traceback
import uuid
from typing import Dict, List, Any, Optional, Union, TypedDict, cast
import concurrent.futures

# Try importing required modules
try:
    import agent
    from langchain_openai import ChatOpenAI
except ImportError as e:
    import pytest
    pytest.skip(f"Required modules not available: {e}", allow_module_level=True)

# Replicate the exact function from dashboard.py to ensure compatibility
def create_agent_config(thread_id: Optional[str] = None) -> Any:
    """
    Create a configuration dict for agent invocation with proper checkpointer config
    
    Args:
        thread_id (Optional[str]): Optional thread ID. If None, a timestamp-based ID will be generated.
        
    Returns:
        Dict containing the required configurable keys for the LangGraph checkpointer
    """
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
    
    return config_dict

def print_header(title):
    """Print a nicely formatted header"""
    print(f"\n{'=' * 80}")
    print(f" {title}")
    print(f"{'=' * 80}\n")

def get_all_state_keys(state):
    """Get all keys from state dict recursively"""
    all_keys = set()
    
    def collect_keys(d, prefix=''):
        if isinstance(d, dict):
            for k, v in d.items():
                key = f"{prefix}.{k}" if prefix else k
                all_keys.add(key)
                collect_keys(v, key)
        elif isinstance(d, list) and d and isinstance(d[0], dict):
            for i, item in enumerate(d):
                collect_keys(item, f"{prefix}[{i}]")
    
    collect_keys(state)
    return sorted(list(all_keys))

def run_agent_with_state(state, config=None, timeout=60, description=""):
    """Run the agent with the given state and config"""
    print(f"🔄 Running agent with {description}...")
    print(f"   State keys: {list(state.keys())}")
    print(f"   Intent: {state.get('intent', 'None')}")
    
    start_time = time.time()
    
    try:
        # Match exactly how dashboard.py does it - create the agent first
        from agent import create_agent  # Import in this scope like dashboard.py does
        agent_instance = create_agent(enable_persistence=True)
        
        # Create a config using the same function as dashboard
        thread_id = None
        if config and isinstance(config, dict) and "configurable" in config:
            thread_id = config["configurable"].get("thread_id")
        agent_config = create_agent_config(thread_id)
        
        # Use ThreadPoolExecutor for timeout enforcement
        with concurrent.futures.ThreadPoolExecutor() as executor:
            # Match dashboard.py pattern exactly
            future = executor.submit(agent_instance.invoke, state, config=agent_config)
            try:
                result = future.result(timeout=timeout)
                elapsed = time.time() - start_time
                
                # Check if result has selected_variables
                if isinstance(result, dict) and "selected_variables" in result:
                    variables = result.get("selected_variables", [])
                    intent_result = result.get("intent", "unknown")
                    
                    if len(variables) > 0:
                        print(f"✅ Test SUCCEEDED in {elapsed:.2f}s")
                        print(f"   Final intent: {intent_result}")
                        print(f"   Selected {len(variables)} variables")
                        print(f"   Sample variables: {variables[:5]}")
                        
                        return {
                            "success": True, 
                            "elapsed": elapsed,
                            "intent": intent_result,
                            "selected_variables": variables[:10],
                            "state_keys": list(state.keys())
                        }
                    else:
                        print(f"❌ Test FAILED in {elapsed:.2f}s - No variables selected")
                        print(f"   Final intent: {intent_result}")
                        
                        return {
                            "success": False,
                            "elapsed": elapsed, 
                            "error": "No variables selected",
                            "intent": intent_result,
                            "state_keys": list(state.keys())
                        }
                else:
                    print(f"❌ Test FAILED in {elapsed:.2f}s - Unexpected result format")
                    print(f"   Result type: {type(result)}")
                    
                    return {
                        "success": False,
                        "elapsed": elapsed,
                        "error": f"Unexpected result format: {type(result)}",
                        "state_keys": list(state.keys())
                    }
                    
            except concurrent.futures.TimeoutError:
                print(f"⚠️ Test TIMED OUT after {timeout:.2f}s")
                
                return {
                    "success": False,
                    "elapsed": timeout,
                    "error": "Timeout",
                    "state_keys": list(state.keys())
                }
                
    except Exception as e:
        elapsed = time.time() - start_time
        print(f"❌ Test ERROR in {elapsed:.2f}s")
        print(f"   Error: {str(e)}")
        traceback.print_exc()
        
        return {
            "success": False,
            "elapsed": elapsed,
            "error": str(e),
            "exception": traceback.format_exc(),
            "state_keys": list(state.keys())
        }

def main():
    """Run all state construction tests"""
    print_header("Agent State Construction Test")
    
    # Check if agent module is available
    if 'agent' not in sys.modules:
        print("❌ Could not import agent module. Make sure it's in the current directory.")
        return
    
    # Basic test query
    query = "What do Mexicans think about health?"
    
    # Different state variations to test
    test_states = [
        # Test 1: Minimal state (just messages)
        {
            "messages": [{"role": "user", "content": query}]
        },
        
        # Test 2: Messages with pre-determined intent
        {
            "messages": [{"role": "user", "content": query}],
            "intent": "query_variable_database"
        },
        
        # Test 3: Full test state (like test_agent_async)
        {
            "messages": [{"role": "user", "content": query}],
            "intent": "query_variable_database",
            "user_query": query,
            "original_query": query,
            "dataset": ["all"],
            "selected_variables": [],
            "analysis_type": "descriptive",
            "user_approved": False,
            "analysis_result": {}
        },
        
        # Test 4: Full real state (like handle_auto_next_step)
        {
            "messages": [{"role": "user", "content": query}],
            "intent": "query_variable_database",
            "user_query": query,
            "original_query": query,
            "dataset": ["ALL"],  # Note uppercase vs. lowercase
            "selected_variables": [],
            "analysis_type": "descriptive",
            "user_approved": False,
            "analysis_result": {},
            "language": "en"  # Extra field in real queries
        },
        
        # Test 5: No intent - forces agent to classify
        {
            "messages": [{"role": "user", "content": query}],
            "user_query": query,
            "original_query": query,
            "dataset": ["all"],
            "selected_variables": [],
            "analysis_type": "descriptive",
            "user_approved": False,
            "analysis_result": {}
        },
        
        # Test 6: Intent but lowercase dataset
        {
            "messages": [{"role": "user", "content": query}],
            "intent": "query_variable_database",
            "user_query": query,
            "original_query": query,
            "dataset": ["all"],  # lowercase
            "selected_variables": [],
            "analysis_type": "descriptive",
            "user_approved": False,
            "analysis_result": {},
            "language": "en"
        },
        
        # Test 7: Intent but uppercase dataset
        {
            "messages": [{"role": "user", "content": query}],
            "intent": "query_variable_database",
            "user_query": query,
            "original_query": query,
            "dataset": ["ALL"],  # uppercase
            "selected_variables": [],
            "analysis_type": "descriptive",
            "user_approved": False,
            "analysis_result": {},
            "language": "en"
        },
        
        # Test 8: No language field
        {
            "messages": [{"role": "user", "content": query}],
            "intent": "query_variable_database",
            "user_query": query,
            "original_query": query,
            "dataset": ["ALL"],
            "selected_variables": [],
            "analysis_type": "descriptive",
            "user_approved": False,
            "analysis_result": {}
            # No language field
        }
    ]
    
    # Run tests with different state constructions
    results = {}
    
    for i, state in enumerate(test_states, 1):
        description = f"Test {i}: "
        
        if "intent" not in state:
            description += "No intent (agent must classify)"
        else:
            description += f"With intent='{state['intent']}'"
            
        if "dataset" in state:
            description += f", dataset={state['dataset']}"
            
        if "language" in state:
            description += f", language='{state['language']}'"
        else:
            description += ", no language field"
        
        print_header(description)
        results[f"test_{i}"] = run_agent_with_state(state, description=description)
    
    # Create different thread IDs for config testing
    print_header("Testing Different Config Options")
    
    base_state = {
        "messages": [{"role": "user", "content": query}],
        "intent": "query_variable_database",
        "user_query": query,
        "original_query": query,
        "dataset": ["ALL"],
        "selected_variables": [],
        "analysis_type": "descriptive",
        "user_approved": False,
        "analysis_result": {}
    }
    
    # Test with different config options
    config_tests = [
        # Empty config
        {},
        
        # Config with thread_id only
        {"configurable": {"thread_id": f"test_{int(time.time())}"}},
        
        # Full test config
        {
            "configurable": {
                "thread_id": f"test_{int(time.time())}",
                "checkpoint_id": f"test_{int(time.time())}",
                "checkpoint_ns": "test_session"
            }
        }
    ]
    
    for i, config in enumerate(config_tests, 1):
        description = f"Config Test {i}: "
        if not config:
            description += "Empty config"
        elif "configurable" in config and "thread_id" in config["configurable"]:
            if "checkpoint_id" in config["configurable"]:
                description += "Full config with thread_id and checkpoint_id"
            else:
                description += "Config with thread_id only"
        
        print_header(description)
        results[f"config_test_{i}"] = run_agent_with_state(base_state, config=config, description=description)
    
    # Save results
    with open("state_construction_results.json", "w") as f:
        json.dump(results, f, indent=2)
    
    # Analysis
    print_header("Analysis")
    
    successful_tests = [k for k, v in results.items() if v.get("success", False)]
    failed_tests = [k for k, v in results.items() if not v.get("success", False)]
    
    print(f"Tests completed: {len(successful_tests)}/{len(results)} successful")
    print(f"Successful tests: {', '.join(successful_tests)}")
    print(f"Failed tests: {', '.join(failed_tests)}")
    
    # Look for patterns
    if successful_tests:
        print("\nSuccessful State Construction Patterns:")
        for test_id in successful_tests:
            test_result = results[test_id]
            print(f"- {test_id}: Intent={test_result.get('intent', 'None')}, Keys={test_result.get('state_keys', [])}")
    
    if failed_tests:
        print("\nFailed State Construction Patterns:")
        for test_id in failed_tests:
            test_result = results[test_id]
            print(f"- {test_id}: Error={test_result.get('error', 'None')}, Keys={test_result.get('state_keys', [])}")
    
    # Key differences
    print("\nKey state construction differences between success and failure:")
    
    if successful_tests and failed_tests:
        successful_keys = set()
        for test_id in successful_tests:
            successful_keys.update(results[test_id].get("state_keys", []))
            
        failed_keys = set()
        for test_id in failed_tests:
            failed_keys.update(results[test_id].get("state_keys", []))
        
        only_in_successful = successful_keys - failed_keys
        only_in_failed = failed_keys - successful_keys
        
        if only_in_successful:
            print(f"Keys only in successful tests: {sorted(list(only_in_successful))}")
        if only_in_failed:
            print(f"Keys only in failed tests: {sorted(list(only_in_failed))}")
    
    print(f"\nDetailed results saved to state_construction_results.json")
    
    # Generate recommended fix if patterns are clear
    generate_recommendations(results)

def generate_recommendations(results):
    """Generate recommendations based on test results"""
    print_header("Recommendations")
    
    successful_tests = [k for k, v in results.items() if v.get("success", False)]
    failed_tests = [k for k, v in results.items() if not v.get("success", False)]
    
    if not successful_tests:
        print("❌ All tests failed - unable to generate recommendations")
        return
    
    if not failed_tests:
        print("✅ All tests succeeded - no recommendations needed")
        return
    
    # Extract patterns from successful tests
    has_intent = all("intent" in results[test_id].get("state_keys", []) for test_id in successful_tests)
    has_language = all("language" in results[test_id].get("state_keys", []) for test_id in successful_tests)
    
    # Look at dataset values
    dataset_values = []
    for test_id in successful_tests:
        state_keys = results[test_id].get("state_keys", [])
        if "dataset" in state_keys:
            test_num = int(test_id.split('_')[1])
            if test_num <= 8:  # Only check the state construction tests
                dataset = results[test_id].get("dataset", ["unknown"])
                dataset_values.append(str(dataset))
    
    # Generate recommendations
    print("Based on the test results, here are the recommended changes:")
    
    if has_intent:
        print("\n1. Ensure all agent invocations include the 'intent' field:")
        print("   ```python")
        print("   # In dashboard.py - handle_auto_next_step")
        print("   agent_state = {")
        print("       \"messages\": [{\"role\": \"user\", \"content\": user_message}],")
        print("       \"intent\": classified_intent,  # Make sure this is set correctly")
        print("       # other fields...")
        print("   }")
        print("   ```")
    
    if dataset_values and all(d.upper() in dataset_values for d in dataset_values):
        print("\n2. Use UPPERCASE for dataset values:")
        print("   ```python")
        print("   # In dashboard.py - handle_auto_next_step")
        print("   agent_state = {")
        print("       # other fields...")
        print("       \"dataset\": preferred_datasets or session_data.get(\"datasets\", [\"ALL\"]),  # Use ALL (uppercase)")
        print("       # other fields...")
        print("   }")
        print("   ```")
    
    if has_language:
        print("\n3. Always include the 'language' field:")
        print("   ```python")
        print("   # In dashboard.py - handle_auto_next_step")
        print("   agent_state = {")
        print("       # other fields...")
        print("       \"language\": session_data.get('language', 'en')")
        print("   }")
        print("   ```")
    
    print("\n4. Use consistent config for all invocations:")
    print("   ```python")
    print("   # In dashboard.py - handle_auto_next_step")
    print("   thread_id = f\"chat_{int(time.time())}\"")
    print("   agent_config = {")
    print("       \"configurable\": {")
    print("           \"thread_id\": thread_id,")
    print("           \"checkpoint_id\": str(uuid.uuid4()),")
    print("           \"checkpoint_ns\": \"chat_session\"")
    print("       }")
    print("   }")
    print("   ```")
    
    print("\nImplementing these changes should ensure consistency between test and real query invocations.")

if __name__ == "__main__":
    main()
