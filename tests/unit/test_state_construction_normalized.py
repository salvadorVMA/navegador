#!/usr/bin/env python3
"""
Normalized State Construction Test

This script tests agent invocation with normalized state using our state_normalizer utility.
It performs the same tests as test_state_construction.py but ensures all states are properly normalized.
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
    import state_normalizer  # Import our state normalizer
except ImportError as e:
    print(f"⚠️ Required modules not found: {e}. Please ensure you have the necessary dependencies.")
    sys.exit(1)

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
    
    # Use state_normalizer to normalize the state
    normalized_state = state_normalizer.normalize_state(state)
    
    print(f"   Original state keys: {list(state.keys())}")
    print(f"   Normalized state keys: {list(normalized_state.keys())}")
    print(f"   Intent: {normalized_state.get('intent', 'None')}")
    
    start_time = time.time()
    
    try:
        # Match exactly how dashboard.py does it - create the agent first
        from agent import create_agent  # Import in this scope like dashboard.py does
        agent_instance = create_agent(enable_persistence=True)
        
        # Use state_normalizer to create a normalized config
        agent_config = state_normalizer.normalize_config(config)
        
        # Use ThreadPoolExecutor for timeout enforcement
        with concurrent.futures.ThreadPoolExecutor() as executor:
            # Match dashboard.py pattern with normalized state and config
            future = executor.submit(agent_instance.invoke, normalized_state, config=agent_config)
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
                            "state_keys": list(normalized_state.keys())
                        }
                    else:
                        print(f"❌ Test FAILED in {elapsed:.2f}s - No variables selected")
                        print(f"   Final intent: {intent_result}")
                        
                        return {
                            "success": False,
                            "elapsed": elapsed, 
                            "error": "No variables selected",
                            "intent": intent_result,
                            "state_keys": list(normalized_state.keys())
                        }
                else:
                    print(f"❌ Test FAILED in {elapsed:.2f}s - Unexpected result format")
                    print(f"   Result type: {type(result)}")
                    
                    return {
                        "success": False,
                        "elapsed": elapsed,
                        "error": f"Unexpected result format: {type(result)}",
                        "state_keys": list(normalized_state.keys())
                    }
                    
            except concurrent.futures.TimeoutError:
                print(f"⚠️ Test TIMED OUT after {timeout:.2f}s")
                
                return {
                    "success": False,
                    "elapsed": timeout,
                    "error": "Timeout",
                    "state_keys": list(normalized_state.keys())
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
            "state_keys": list(normalized_state.keys())
        }

def main():
    """Run all state construction tests"""
    print_header("Agent Normalized State Construction Test")
    
    # Check if agent module is available
    if 'agent' not in sys.modules:
        print("❌ Could not import agent module. Make sure it's in the current directory.")
        return
    
    # Check if state_normalizer module is available
    if 'state_normalizer' not in sys.modules:
        print("❌ Could not import state_normalizer module. Make sure it's in the current directory.")
        return
        
    # Basic test query
    query = "What do Mexicans think about health?"
    
    # Different state variations to test
    test_states = [
        # Test 1: Minimal state (just messages) - will be normalized by state_normalizer
        {
            "messages": [{"role": "user", "content": query}]
        },
        
        # Test 2: Messages with pre-determined intent - will be normalized by state_normalizer
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
        
        # Test 4: Create state using state_normalizer directly
        state_normalizer.create_agent_state(
            user_message=query,
            intent="query_variable_database"
        )
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
            description += ", no language field (will be added by normalizer)"
        
        if i == 4:
            description = "Test 4: Using state_normalizer.create_agent_state directly"
        
        print_header(description)
        results[f"test_{i}"] = run_agent_with_state(state, description=description)
    
    # Create different thread IDs for config testing
    print_header("Testing Different Config Options (Normalized)")
    
    # Use state_normalizer to create a base state
    base_state = state_normalizer.create_agent_state(
        user_message=query,
        intent="query_variable_database"
    )
    
    # Test with different config options
    config_tests = [
        # Empty config (will be normalized)
        {},
        
        # Config with thread_id only (will be normalized)
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
            description += "Empty config (will be normalized)"
        elif "configurable" in config and "thread_id" in config["configurable"]:
            if "checkpoint_id" in config["configurable"]:
                description += "Full config with thread_id and checkpoint_id"
            else:
                description += "Config with thread_id only (will be normalized)"
        
        print_header(description)
        results[f"config_test_{i}"] = run_agent_with_state(base_state, config=config, description=description)
    
    # Save results
    with open("state_construction_normalized_results.json", "w") as f:
        json.dump(results, f, indent=2)
    
    # Analysis
    print_header("Analysis")
    
    successful_tests = [k for k, v in results.items() if v.get("success", False)]
    failed_tests = [k for k, v in results.items() if not v.get("success", False)]
    
    print(f"Tests completed: {len(successful_tests)}/{len(results)} successful")
    print(f"Successful tests: {', '.join(successful_tests)}")
    print(f"Failed tests: {', '.join(failed_tests)}")
    
    print(f"\nDetailed results saved to state_construction_normalized_results.json")
    
    print_header("Conclusion")
    
    if len(successful_tests) == len(results):
        print("✅ All tests passed! The state_normalizer is working properly.")
        print("Key findings:")
        print("1. The state_normalizer successfully normalizes all state variations")
        print("2. Minimal states (just messages) now work correctly when normalized")
        print("3. Config normalization ensures consistent thread_id and checkpoint handling")
    else:
        print(f"❌ {len(failed_tests)}/{len(results)} tests still failed. Further investigation needed.")

if __name__ == "__main__":
    main()
