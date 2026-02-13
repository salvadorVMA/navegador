#!/usr/bin/env python3
"""
Fix Hardcoded Intent - Test Script

This script tests a patch that would fix the issue by using a hardcoded intent
for variable database queries instead of relying on dynamic intent classification.

Run with: python test_hardcoded_intent_fix.py
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
    import pytest
    pytest.skip(f"Required modules not available: {e}", allow_module_level=True)

def create_agent_config(thread_id: Optional[str] = None) -> Any:
    """Create a configuration dict for agent invocation with proper checkpointer config"""
    if thread_id is None:
        thread_id = f"test_fix_{int(time.time())}"
    
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

def run_agent_with_timeout(agent, state, config, timeout=10, label="Test"):
    """Run agent with timeout and return result"""
    print(f"🔄 Running {label} with timeout {timeout}s...")
    print(f"   Intent: {state.get('intent', 'None')}")
    
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

def simulate_handle_auto_next_step_fixed():
    """Simulate the handle_auto_next_step function with a hardcoded intent fix"""
    print_section("Simulating Fixed handle_auto_next_step")
    
    # Initialize agent
    try:
        print("🔄 Creating agent with persistence...")
        agent = create_agent(enable_persistence=True)
        print("✅ Agent initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize agent: {e}")
        traceback.print_exc()
        return
    
    # Test queries to simulate
    test_queries = [
        {
            "query": "What do Mexicans think about health?",
            "description": "Health Query"
        },
        {
            "query": "Tell me about education levels in Mexico",
            "description": "Education Query"
        },
        {
            "query": "Show me variables about corruption",
            "description": "Corruption Variables Query"
        }
    ]
    
    # Results storage
    results = []
    
    # Test each query with and without the fix
    for test in test_queries:
        query = test["query"]
        description = test["description"]
        
        print_section(f"Testing: {description}")
        
        # Create unique thread IDs for each test
        thread_id_before = f"before_fix_{int(time.time())}_{description.replace(' ', '_').lower()}"
        thread_id_after = f"after_fix_{int(time.time())}_{description.replace(' ', '_').lower()}"
        
        # Test 1: Original behavior (with dynamic intent)
        print("Running test with original behavior (dynamic intent)...")
        
        # Original behavior: try to detect intent
        try:
            from intent_classifier import intent_dict, _classify_intent
            llm = ChatOpenAI(model="gpt-4o-mini")
            classified_intent = _classify_intent(query, intent_dict, llm)
            print(f"🎯 Classified intent: {classified_intent}")
        except Exception as e:
            print(f"⚠️ Intent classification failed: {e}")
            classified_intent = "answer_general_questions"  # Default fallback
        
        # Create state like in handle_auto_next_step
        before_state = {
            "messages": [{"role": "user", "content": query}],
            "intent": classified_intent,  # Use classified intent
            "user_query": query,
            "original_query": query,
            "dataset": ["ALL"],
            "selected_variables": [],
            "analysis_type": "descriptive",
            "user_approved": False,
            "analysis_result": {},
            "language": "en"  # This is in real query but not in test
        }
        
        before_config = create_agent_config(thread_id_before)
        before_result = run_agent_with_timeout(
            agent, 
            before_state, 
            before_config, 
            10, 
            f"Original Behavior ({description})"
        )
        
        # Test 2: Fixed behavior (with hardcoded intent for queries)
        print("\nRunning test with fixed behavior (hardcoded intent)...")
        
        # NEW FIX: Check if query contains keywords suggesting variable search
        query_lower = query.lower()
        keywords = ["variable", "dataset", "data", "search", "find", "show me", "about", "opinion", "think"]
        
        # Simulate the fix: override intent for queries about variables
        if any(keyword in query_lower for keyword in keywords):
            print("📝 Query appears to be about variables - using hardcoded 'query_variable_database' intent")
            intent_to_use = "query_variable_database"
        else:
            print("📝 Using classified intent for non-variable query")
            intent_to_use = classified_intent
        
        # Create state with the fix
        after_state = {
            "messages": [{"role": "user", "content": query}],
            "intent": intent_to_use,  # Use hardcoded intent for variable queries
            "user_query": query,
            "original_query": query,
            "dataset": ["all"],  # Using lowercase like in test
            "selected_variables": [],
            "analysis_type": "descriptive",
            "user_approved": False,
            "analysis_result": {}
        }
        
        after_config = create_agent_config(thread_id_after)
        after_result = run_agent_with_timeout(
            agent, 
            after_state, 
            after_config, 
            10, 
            f"Fixed Behavior ({description})"
        )
        
        # Check if the fix worked
        if not before_result["success"] and after_result["success"]:
            print("\n✅ IMPROVEMENT: Fixed implementation succeeded where original failed")
            improvement = True
        elif before_result["success"] and after_result["success"]:
            print("\n✅ Both implementations worked for this query")
            improvement = False
        elif not before_result["success"] and not after_result["success"]:
            print("\n❌ Neither implementation worked for this query")
            improvement = False
        else:
            print("\n⚠️ Original worked but fixed version failed - unexpected")
            improvement = False
        
        # Check for variables in results
        before_vars = []
        after_vars = []
        
        if before_result["success"] and isinstance(before_result["result"], dict):
            before_vars = before_result["result"].get("selected_variables", [])
        
        if after_result["success"] and isinstance(after_result["result"], dict):
            after_vars = after_result["result"].get("selected_variables", [])
        
        print(f"\nVariables found - Before fix: {len(before_vars)}, After fix: {len(after_vars)}")
        
        # Store results for this test
        test_results = {
            "query": query,
            "description": description,
            "classified_intent": classified_intent,
            "override_intent": intent_to_use,
            "before_success": before_result["success"],
            "after_success": after_result["success"],
            "before_error": before_result.get("error", None),
            "after_error": after_result.get("error", None),
            "before_elapsed": before_result["elapsed"],
            "after_elapsed": after_result["elapsed"],
            "before_vars_count": len(before_vars),
            "after_vars_count": len(after_vars),
            "improvement": improvement
        }
        
        results.append(test_results)
    
    # Save detailed results for further analysis
    with open("intent_fix_results.json", "w") as f:
        json.dump(results, f, indent=2)
    
    print("\nDetailed results saved to intent_fix_results.json")
    
    # Summary
    print_section("Summary")
    before_successes = sum(1 for r in results if r["before_success"])
    after_successes = sum(1 for r in results if r["after_success"])
    improvements = sum(1 for r in results if r["improvement"])
    
    print(f"Original implementation: {before_successes}/{len(results)} successful")
    print(f"Fixed implementation: {after_successes}/{len(results)} successful")
    print(f"Improvements: {improvements}/{len(results)} queries")
    
    if after_successes > before_successes:
        print("\n✅ The fix improves the success rate of agent invocation")
        print("👉 RECOMMENDATION: Modify handle_auto_next_step to use hardcoded intent")
        print("   for queries that appear to be about variables or datasets.")
        
        print("\nSuggested code change:")
        print("```python")
        print("# In handle_auto_next_step function")
        print("# After getting user_message but before setting up agent_state")
        print("")
        print("# Check if query appears to be about variables/datasets")
        print("query_lower = user_message.lower()")
        print('keywords = ["variable", "dataset", "data", "search", "find", "show me", "about", "opinion", "think"]')
        print("if any(keyword in query_lower for keyword in keywords):")
        print('    # Override the intent to ensure proper handling')
        print('    agent_intent = "query_variable_database"')
        print("else:")
        print("    # Use the classified intent from session data")
        print('    agent_intent = session_data.get("intent", "")')
        print("")
        print("# Then use agent_intent in the agent_state")
        print("agent_state = {")
        print('    "intent": agent_intent,  # Use our determined intent')
        print("    # ... other fields ...")
        print("}")
        print("```")
    elif after_successes == before_successes:
        print("\n⚠️ The fix doesn't change the success rate")
        print("👉 The issue might be elsewhere in the code")
    else:
        print("\n❌ The fix appears to make things worse")

if __name__ == "__main__":
    simulate_handle_auto_next_step_fixed()
