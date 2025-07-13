#!/usr/bin/env python3
"""
State Normalizer

This script provides functions to normalize agent state between test and real environments.
It ensures consistent state formatting regardless of where the agent is invoked from.
"""

import copy
import uuid
import time
from typing import Dict, Any, List, Union, Optional

def normalize_state(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalize an agent state to ensure consistent structure between test and real environments.
    
    This function ensures:
    1. All required fields are present
    2. Field values are in the expected format
    3. Case consistency for dataset values
    
    Args:
        state: The original agent state dictionary
        
    Returns:
        Dict[str, Any]: The normalized state with consistent structure
    """
    # Make a deep copy to avoid modifying the original
    normalized = copy.deepcopy(state)
    
    # Ensure messages field exists and is properly formatted
    if "messages" not in normalized:
        normalized["messages"] = []
    
    # Extract user query from messages if not present
    if "user_query" not in normalized and normalized.get("messages"):
        for msg in normalized["messages"]:
            if msg.get("role") == "user":
                normalized["user_query"] = msg.get("content", "")
                normalized["original_query"] = msg.get("content", "")
                break
    
    # Normalize dataset to uppercase
    if "dataset" in normalized:
        if isinstance(normalized["dataset"], list):
            normalized["dataset"] = [d.upper() if isinstance(d, str) else d for d in normalized["dataset"]]
        elif normalized["dataset"] is None:
            normalized["dataset"] = ["ALL"]
    else:
        normalized["dataset"] = ["ALL"]
    
    # Ensure other required fields exist
    if "selected_variables" not in normalized:
        normalized["selected_variables"] = []
    
    if "analysis_type" not in normalized:
        normalized["analysis_type"] = "descriptive"
    
    if "user_approved" not in normalized:
        normalized["user_approved"] = False
    
    if "analysis_result" not in normalized:
        normalized["analysis_result"] = {}
    
    # Add language if not present
    if "language" not in normalized:
        normalized["language"] = "en"
    
    return normalized

def normalize_config(config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Normalize agent config to ensure consistent structure.
    
    Args:
        config: The original config dictionary, or None
        
    Returns:
        Dict[str, Any]: The normalized config with consistent structure
    """
    if config is None:
        config = {}
    
    # Make a deep copy
    normalized = copy.deepcopy(config)
    
    # Ensure configurable field exists
    if "configurable" not in normalized:
        normalized["configurable"] = {}
    
    # Generate thread_id if not present
    if "thread_id" not in normalized["configurable"]:
        normalized["configurable"]["thread_id"] = f"chat_{int(time.time())}"
    
    # Generate checkpoint_id if not present
    if "checkpoint_id" not in normalized["configurable"]:
        normalized["configurable"]["checkpoint_id"] = str(uuid.uuid4())
    
    # Set checkpoint_ns if not present
    if "checkpoint_ns" not in normalized["configurable"]:
        normalized["configurable"]["checkpoint_ns"] = "chat_session"
    
    return normalized

def create_agent_state(
    user_message: str, 
    intent: Optional[str] = None,
    dataset: Optional[List[str]] = None,
    selected_variables: Optional[List[str]] = None,
    language: str = "en"
) -> Dict[str, Any]:
    """
    Create a normalized agent state from basic parameters.
    
    Args:
        user_message: The user's query text
        intent: Optional intent classification
        dataset: Optional list of datasets
        selected_variables: Optional list of selected variables
        language: Language code, defaults to "en"
        
    Returns:
        Dict[str, Any]: A properly formatted agent state
    """
    state = {
        "messages": [{"role": "user", "content": user_message}],
        "user_query": user_message,
        "original_query": user_message,
        "dataset": dataset or ["ALL"],
        "selected_variables": selected_variables or [],
        "analysis_type": "descriptive",
        "user_approved": False,
        "analysis_result": {},
        "language": language
    }
    
    # Add intent if provided
    if intent:
        state["intent"] = intent
    
    return normalize_state(state)

# Example usage
if __name__ == "__main__":
    # Test the normalization functions
    test_state = {
        "messages": [{"role": "user", "content": "What do Mexicans think about health?"}],
        "dataset": ["all"]  # lowercase
    }
    
    normalized = normalize_state(test_state)
    
    print("Original state:")
    print(test_state)
    print("\nNormalized state:")
    print(normalized)
    
    # Test creating a state from scratch
    new_state = create_agent_state(
        "What do Mexicans think about health?",
        intent="query_variable_database"
    )
    
    print("\nCreated state:")
    print(new_state)
