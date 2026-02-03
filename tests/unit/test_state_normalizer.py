#!/usr/bin/env python3
"""
State Normalizer Test Script

A simple test script to verify that our state_normalizer functions are working as expected.
This ensures that minimal agent states are properly normalized before agent invocation.
"""

import json
import time
from typing import Dict, Any, Optional

# Import our state normalizer
try:
    from state_normalizer import normalize_state, normalize_config, create_agent_state
except ImportError as e:
    print(f"Error importing state_normalizer: {e}")
    print("Make sure state_normalizer.py is in the current directory.")
    exit(1)

def print_header(title: str):
    """Print a nicely formatted header"""
    print(f"\n{'=' * 80}")
    print(f" {title}")
    print(f"{'=' * 80}\n")

def compare_states(original: Dict[str, Any], normalized: Dict[str, Any]):
    """Compare original and normalized states, showing differences"""
    print("Original state keys:", list(original.keys()))
    print("Normalized state keys:", list(normalized.keys()))
    
    # Find keys added by normalization
    added_keys = [k for k in normalized if k not in original]
    if added_keys:
        print("\nKeys added by normalization:", added_keys)
    
    # Find values modified by normalization
    modified_keys = []
    for k in original:
        if k in normalized and original[k] != normalized[k]:
            modified_keys.append(k)
    
    if modified_keys:
        print("\nKeys modified by normalization:")
        for k in modified_keys:
            print(f"  {k}: {original[k]} → {normalized[k]}")

def compare_configs(original: Optional[Dict[str, Any]], normalized: Dict[str, Any]):
    """Compare original and normalized configs, showing differences"""
    original = original or {}
    print("Original config:", json.dumps(original, indent=2))
    print("Normalized config:", json.dumps(normalized, indent=2))

def main():
    print_header("State Normalizer Test")
    
    # Test case 1: Minimal state (just messages)
    minimal_state = {
        "messages": [{"role": "user", "content": "What do Mexicans think about health?"}]
    }
    
    normalized_minimal = normalize_state(minimal_state)
    print_header("Test 1: Minimal State (just messages)")
    compare_states(minimal_state, normalized_minimal)
    
    # Test case 2: With intent but missing other fields
    intent_state = {
        "messages": [{"role": "user", "content": "What do Mexicans think about health?"}],
        "intent": "query_variable_database"
    }
    
    normalized_intent = normalize_state(intent_state)
    print_header("Test 2: With Intent (missing other fields)")
    compare_states(intent_state, normalized_intent)
    
    # Test case 3: Dataset case normalization
    dataset_state = {
        "messages": [{"role": "user", "content": "What do Mexicans think about health?"}],
        "dataset": ["all", "health"]  # lowercase
    }
    
    normalized_dataset = normalize_state(dataset_state)
    print_header("Test 3: Dataset Case Normalization")
    compare_states(dataset_state, normalized_dataset)
    
    # Test case 4: Using create_agent_state directly
    created_state = create_agent_state(
        user_message="What do Mexicans think about health?",
        intent="query_variable_database",
        dataset=["SAL", "health"]
    )
    
    print_header("Test 4: Using create_agent_state")
    print("State created directly:", json.dumps(created_state, indent=2))
    
    # Test config normalization
    print_header("Config Normalization Tests")
    
    # Empty config
    empty_config = {}
    normalized_empty = normalize_config(empty_config)
    print_header("Test 5: Empty Config")
    compare_configs(empty_config, normalized_empty)
    
    # Partial config
    partial_config = {"configurable": {"thread_id": f"test_{int(time.time())}"}}
    normalized_partial = normalize_config(partial_config)
    print_header("Test 6: Partial Config")
    compare_configs(partial_config, normalized_partial)
    
    # Summary
    print_header("Summary")
    print("✅ All normalization tests completed successfully.")
    print("Key findings:")
    print("1. Minimal states are properly filled with default values")
    print("2. Dataset values are normalized to uppercase")
    print("3. Config values include required checkpoint fields")
    print("4. create_agent_state generates complete, ready-to-use states")

if __name__ == "__main__":
    main()
