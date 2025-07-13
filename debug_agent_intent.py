#!/usr/bin/env python3
"""
Debug Agent Intent Test

This script focuses on testing how the agent handles different intents.
It verifies if the issue is related to intent classification and routing.

Run with: python debug_agent_intent.py
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

# Global variables
TIMEOUT = 60  # Default timeout in seconds for database queries

def create_agent_config(thread_id: Optional[str] = None) -> Any:
    """Create a configuration dict for agent invocation with proper checkpointer config"""
    if thread_id is None:
        thread_id = f"intent_test_{int(time.time())}"
    
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

def run_agent_test(agent, state, config, timeout=TIMEOUT, label="Test"):
    """Run a test with the agent and return result"""
    print(f"🔄 Running {label} with timeout {timeout}s...")
    print(f"   Intent: {state.get('intent', 'None')}")
    print(f"   Query: {state.get('user_query', 'None')[:50]}...")
    print(f"   Dataset: {state.get('dataset', [])}")
    
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

def test_intent_handling():
    """Test how the agent handles different intents"""
    print_section("Intent Handling Test")
    
    # Initialize agent
    try:
        print("🔄 Creating agent with persistence...")
        agent = create_agent(enable_persistence=True)
        print("✅ Agent initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize agent: {e}")
        traceback.print_exc()
        return
    
    # Test queries
    test_queries = [
        {
            "query": "What do Mexicans think about health?",
            "expected_intent": "query_variable_database",
            "description": "Health Query"
        },
        {
            "query": "Tell me about education levels in Mexico",
            "expected_intent": "query_variable_database",
            "description": "Education Query"
        },
        {
            "query": "Show me variables about corruption",
            "expected_intent": "query_variable_database",
            "description": "Corruption Variables Query"
        },
        {
            "query": "What is this project about?",
            "expected_intent": "answer_general_questions",
            "description": "General Question"
        }
    ]
    
    # Results storage
    results = []
    
    # Create LLM for intent classification
    llm = ChatOpenAI(model="gpt-4o-mini")
    
    # Test each query with both classified and hardcoded intents
    for test in test_queries:
        query = test["query"]
        expected_intent = test["expected_intent"]
        description = test["description"]
        
        print_section(f"Testing: {description}")
        
        # First classify the intent
        try:
            classified_intent = _classify_intent(query, intent_dict, llm)
            print(f"🎯 Classified intent: {classified_intent} (expected: {expected_intent})")
        except Exception as e:
            print(f"⚠️ Intent classification failed: {e}")
            classified_intent = "answer_general_questions"  # Default fallback
        
        # Create thread ID for this test
        thread_id = f"intent_test_{int(time.time())}_{description.replace(' ', '_').lower()}"
        
        # Test 1: With classified intent
        classified_state = {
            "messages": [{"role": "user", "content": query}],
            "intent": classified_intent,
            "user_query": query,
            "original_query": query,
            "dataset": ["ALL"],
            "selected_variables": [],
            "analysis_type": "descriptive",
            "user_approved": False,
            "analysis_result": {},
            "language": "en"
        }
        
        classified_config = create_agent_config(f"{thread_id}_classified")
        classified_result = run_agent_test(
            agent, 
            classified_state, 
            classified_config, 
            TIMEOUT, 
            f"{description} (Classified Intent: {classified_intent})"
        )
        
        # Test 2: With hardcoded intent
        hardcoded_state = {
            "messages": [{"role": "user", "content": query}],
            "intent": expected_intent,  # Use the expected intent
            "user_query": query,
            "original_query": query,
            "dataset": ["all"],  # Use lowercase like in test_agent_async
            "selected_variables": [],
            "analysis_type": "descriptive",
            "user_approved": False,
            "analysis_result": {}
        }
        
        hardcoded_config = create_agent_config(f"{thread_id}_hardcoded")
        hardcoded_result = run_agent_test(
            agent, 
            hardcoded_state, 
            hardcoded_config, 
            TIMEOUT, 
            f"{description} (Hardcoded Intent: {expected_intent})"
        )
        
        # Check results
        if classified_result["success"] != hardcoded_result["success"]:
            if classified_result["success"]:
                print(f"⚠️ Interesting: Classified intent worked but hardcoded intent failed")
            else:
                print(f"⚠️ Interesting: Hardcoded intent worked but classified intent failed")
                print(f"👉 This suggests the issue is with intent classification")
        elif not classified_result["success"] and not hardcoded_result["success"]:
            print(f"❌ Both approaches failed for this query")
            if "Timeout" in classified_result.get("error", "") or "Timeout" in hardcoded_result.get("error", ""):
                print(f"⏱️ Timeout detected - database query may need more time")
                print(f"   Consider increasing TIMEOUT value (currently {TIMEOUT}s)")
        else:
            print(f"✅ Both approaches worked for this query")
        
        # Check for variables in results
        if classified_result["success"]:
            result = classified_result["result"]
            if isinstance(result, dict):
                vars_count = len(result.get("selected_variables", []))
                if vars_count > 0:
                    print(f"✅ Classified intent found {vars_count} variables")
                else:
                    print(f"⚠️ Classified intent didn't find any variables")
        
        if hardcoded_result["success"]:
            result = hardcoded_result["result"]
            if isinstance(result, dict):
                vars_count = len(result.get("selected_variables", []))
                if vars_count > 0:
                    print(f"✅ Hardcoded intent found {vars_count} variables")
                else:
                    print(f"⚠️ Hardcoded intent didn't find any variables")
        
        # Store results for this test
        test_results = {
            "query": query,
            "expected_intent": expected_intent,
            "classified_intent": classified_intent,
            "classified_success": classified_result["success"],
            "hardcoded_success": hardcoded_result["success"],
            "classified_error": classified_result.get("error", None),
            "hardcoded_error": hardcoded_result.get("error", None),
            "classified_elapsed": classified_result["elapsed"],
            "hardcoded_elapsed": hardcoded_result["elapsed"],
        }
        
        if classified_result["success"] and isinstance(classified_result["result"], dict):
            test_results["classified_vars_count"] = len(classified_result["result"].get("selected_variables", []))
        
        if hardcoded_result["success"] and isinstance(hardcoded_result["result"], dict):
            test_results["hardcoded_vars_count"] = len(hardcoded_result["result"].get("selected_variables", []))
        
        results.append(test_results)
    
    # Save detailed results for further analysis
    with open("intent_debug_results.json", "w") as f:
        json.dump(results, f, indent=2)
    
    print("\nDetailed results saved to intent_debug_results.json")
    
    # Summary
    print_section("Summary")
    classified_successes = sum(1 for r in results if r["classified_success"])
    hardcoded_successes = sum(1 for r in results if r["hardcoded_success"])
    
    print(f"Classified intent tests: {classified_successes}/{len(results)} successful")
    print(f"Hardcoded intent tests: {hardcoded_successes}/{len(results)} successful")
    
    if classified_successes < hardcoded_successes:
        print("\n👉 CONCLUSION: The issue is likely with intent classification.")
        print("   When intents are hardcoded, more queries succeed.")
    elif classified_successes > hardcoded_successes:
        print("\n👉 CONCLUSION: Unexpectedly, classified intents work better than hardcoded ones.")
    else:
        if classified_successes == len(results):
            print("\n👉 CONCLUSION: All tests passed - intent handling appears to work correctly.")
            print("   The issue might be elsewhere in the real application.")
        else:
            print("\n👉 CONCLUSION: Both approaches have the same success rate.")
            print("   The issue might be with specific query types or other factors.")

if __name__ == "__main__":
    test_intent_handling()
