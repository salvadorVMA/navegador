#!/usr/bin/env python3
"""
Progressive Timeout Test

This script tests the agent with progressively longer timeouts to identify
the minimum timeout needed for successful database queries. This helps
determine if timeouts are the root cause of agent failures in production.

Run with: python test_agent_timeouts.py
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

# Timeouts to test (in seconds)
TIMEOUTS = [5, 10, 15, 30, 60, 120]

def create_agent_config(thread_id: Optional[str] = None) -> Any:
    """Create a configuration dict for agent invocation with proper checkpointer config"""
    if thread_id is None:
        thread_id = f"timeout_test_{int(time.time())}"
    
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

def run_agent_with_timeout(agent, state, config, timeout):
    """Run agent with specific timeout and return result"""
    print(f"🔄 Running test with {timeout}s timeout...")
    print(f"   Intent: {state.get('intent', 'None')}")
    print(f"   Query: {state.get('user_query', 'None')[:50]}...")
    
    start_time = time.time()
    
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future = executor.submit(agent.invoke, state, config=config)
        try:
            result = future.result(timeout=timeout)
            elapsed = time.time() - start_time
            print(f"✅ Test successful after {elapsed:.2f}s (within {timeout}s timeout)")
            return {"success": True, "elapsed": elapsed, "result": result, "timeout": timeout}
        except concurrent.futures.TimeoutError:
            elapsed = time.time() - start_time
            print(f"⚠️ Test timed out after {elapsed:.2f}s (hit {timeout}s limit)")
            return {"success": False, "elapsed": timeout, "error": "Timeout", "timeout": timeout}
        except Exception as e:
            elapsed = time.time() - start_time
            print(f"❌ Test failed after {elapsed:.2f}s: {e}")
            traceback.print_exc()
            return {"success": False, "elapsed": elapsed, "error": str(e), "timeout": timeout}

def test_progressive_timeouts():
    """Test agent with progressively longer timeouts"""
    print_section("Progressive Timeout Test")
    
    # Initialize agent
    try:
        print("🔄 Creating agent with persistence...")
        agent = create_agent(enable_persistence=True)
        print("✅ Agent initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize agent: {e}")
        traceback.print_exc()
        return
    
    # Test queries to use
    test_queries = [
        {
            "query": "What do Mexicans think about health?",
            "intent": "query_variable_database",
            "description": "Health Query"
        },
        {
            "query": "Tell me about education levels in Mexico",
            "intent": "query_variable_database",
            "description": "Education Query"
        },
        {
            "query": "Show me variables about corruption",
            "intent": "query_variable_database",
            "description": "Corruption Variables Query"
        }
    ]
    
    # Results for each query
    all_results = {}
    
    # Test each query with multiple timeouts
    for test in test_queries:
        query = test["query"]
        intent = test["intent"]
        description = test["description"]
        
        print_section(f"Testing: {description}")
        
        # Results for this query
        query_results = []
        
        # State for this test
        state = {
            "messages": [{"role": "user", "content": query}],
            "intent": intent,
            "user_query": query,
            "original_query": query,
            "dataset": ["all"],  # Use lowercase like in test_agent_async
            "selected_variables": [],
            "analysis_type": "descriptive",
            "user_approved": False,
            "analysis_result": {}
        }
        
        # Test with each timeout
        for timeout in TIMEOUTS:
            # Create a unique thread ID for each timeout test
            thread_id = f"timeout_{timeout}_{description.replace(' ', '_').lower()}_{int(time.time())}"
            config = create_agent_config(thread_id)
            
            # Run the test with this timeout
            result = run_agent_with_timeout(agent, state, config, timeout)
            
            # Add to results
            query_results.append(result)
            
            # Check if successful
            if result["success"]:
                # Count variables if available
                vars_count = 0
                if isinstance(result.get("result"), dict):
                    vars_count = len(result["result"].get("selected_variables", []))
                    
                print(f"✅ Found {vars_count} variables in {result['elapsed']:.2f}s")
                print(f"👍 Query succeeded with {timeout}s timeout - proceeding to next query")
                break
            else:
                print(f"❌ Query failed with {timeout}s timeout - trying longer timeout")
        
        # Store results for this query
        all_results[description] = query_results
    
    # Save detailed results for further analysis
    with open("timeout_test_results.json", "w") as f:
        json.dump(all_results, f, indent=2, default=str)
    
    print("\nDetailed results saved to timeout_test_results.json")
    
    # Summary
    print_section("Summary")
    for description, results in all_results.items():
        success = any(r["success"] for r in results)
        if success:
            # Find the first successful timeout
            successful_result = next(r for r in results if r["success"])
            print(f"✅ {description}: Succeeded with {successful_result['timeout']}s timeout in {successful_result['elapsed']:.2f}s")
            
            # Count variables if available
            if isinstance(successful_result.get("result"), dict):
                vars_count = len(successful_result["result"].get("selected_variables", []))
                print(f"   Found {vars_count} variables")
        else:
            print(f"❌ {description}: Failed with all timeouts up to {TIMEOUTS[-1]}s")
    
    # Overall recommendation
    successful_timeouts = []
    for description, results in all_results.items():
        for r in results:
            if r["success"]:
                successful_timeouts.append(r["elapsed"])
                break
    
    if successful_timeouts:
        avg_time = sum(successful_timeouts) / len(successful_timeouts)
        max_time = max(successful_timeouts)
        recommended = max(int(max_time * 1.5), int(avg_time * 2))
        
        print("\n📊 Statistics:")
        print(f"   Average successful query time: {avg_time:.2f}s")
        print(f"   Maximum successful query time: {max_time:.2f}s")
        print(f"\n👉 RECOMMENDATION: Set timeout to at least {recommended}s in production code")
        print(f"   This provides a safety margin above the longest observed successful query time")
    else:
        print("\n⚠️ No queries succeeded even with the longest timeout")
        print("   The issue may not be timeout-related")

if __name__ == "__main__":
    test_progressive_timeouts()
