#!/usr/bin/env python3
"""
Enhanced Agent Test Script

This script runs comprehensive tests to validate that the agent works correctly
with the improved timeout settings and retry mechanism.
"""

import time
import json
import os
import sys
from datetime import datetime

# Try importing required modules
try:
    from langchain_openai import ChatOpenAI
    import agent
except ImportError:
    print("⚠️ Required modules not found. Please ensure you have the necessary dependencies.")
    sys.exit(1)

def print_header(title):
    """Print a nicely formatted header"""
    print(f"\n{'=' * 80}")
    print(f" {title}")
    print(f"{'=' * 80}\n")

def run_test_with_realistic_query():
    """Run a test with a realistic query (only user message)"""
    print_header("TEST 1: Realistic Query (User Message Only)")
    
    start_time = time.time()
    
    # Create minimal state with just the user message (most realistic)
    query_state = {
        "messages": [{"role": "user", "content": "What do Mexicans think about health?"}]
    }
    
    # Default config
    config = {}
    
    print("🔄 Running agent with realistic query state...")
    
    try:
        # Invoke agent with just the user message
        result = agent.invoke(query_state, config)
        
        # Check for success
        if isinstance(result, dict) and "selected_variables" in result:
            variables = result.get("selected_variables", [])
            intent = result.get("intent", "unknown")
            
            success = len(variables) > 0 and intent == "query_variable_database"
            
            if success:
                print(f"✅ Realistic query SUCCEEDED in {time.time() - start_time:.2f}s")
                print(f"   Intent: {intent}")
                print(f"   Selected {len(variables)} variables")
                print(f"   Sample variables: {variables[:5]}")
            else:
                print(f"❌ Realistic query FAILED in {time.time() - start_time:.2f}s")
                print(f"   Intent: {intent}")
                print(f"   Selected variables: {variables}")
            
            return {
                "success": success,
                "elapsed": time.time() - start_time,
                "intent": intent,
                "selected_variables": variables[:5] if variables else []
            }
        else:
            print(f"❌ Realistic query FAILED in {time.time() - start_time:.2f}s")
            print(f"   Unexpected result type: {type(result)}")
            return {
                "success": False,
                "elapsed": time.time() - start_time,
                "error": f"Unexpected result type: {type(result)}"
            }
    except Exception as e:
        print(f"❌ Realistic query ERROR in {time.time() - start_time:.2f}s")
        print(f"   Error: {str(e)}")
        return {
            "success": False,
            "elapsed": time.time() - start_time,
            "error": str(e)
        }

def run_test_with_predefined_intent():
    """Run a test with a pre-defined intent"""
    print_header("TEST 2: Pre-defined Intent Query")
    
    start_time = time.time()
    
    # Create state with pre-defined intent (like in test_agent_async)
    query_state = {
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
    
    # Default config
    config = {}
    
    print("🔄 Running agent with pre-defined intent state...")
    
    try:
        # Invoke agent with pre-defined intent
        result = agent.invoke(query_state, config)
        
        # Check for success
        if isinstance(result, dict) and "selected_variables" in result:
            variables = result.get("selected_variables", [])
            intent = result.get("intent", "unknown")
            
            success = len(variables) > 0 and intent == "query_variable_database"
            
            if success:
                print(f"✅ Pre-defined intent query SUCCEEDED in {time.time() - start_time:.2f}s")
                print(f"   Intent: {intent}")
                print(f"   Selected {len(variables)} variables")
                print(f"   Sample variables: {variables[:5]}")
            else:
                print(f"❌ Pre-defined intent query FAILED in {time.time() - start_time:.2f}s")
                print(f"   Intent: {intent}")
                print(f"   Selected variables: {variables}")
            
            return {
                "success": success,
                "elapsed": time.time() - start_time,
                "intent": intent,
                "selected_variables": variables[:5] if variables else []
            }
        else:
            print(f"❌ Pre-defined intent query FAILED in {time.time() - start_time:.2f}s")
            print(f"   Unexpected result type: {type(result)}")
            return {
                "success": False,
                "elapsed": time.time() - start_time,
                "error": f"Unexpected result type: {type(result)}"
            }
    except Exception as e:
        print(f"❌ Pre-defined intent query ERROR in {time.time() - start_time:.2f}s")
        print(f"   Error: {str(e)}")
        return {
            "success": False,
            "elapsed": time.time() - start_time,
            "error": str(e)
        }

def check_retries():
    """Test the retry mechanism"""
    print_header("TEST 3: Retry Mechanism")
    
    print("🔄 Creating ChatOpenAI instance with deliberate bad API key...")
    
    # Store original API key if any
    original_key = os.environ.get("OPENAI_API_KEY", "")
    
    try:
        # Set a deliberate bad API key to trigger retries
        os.environ["OPENAI_API_KEY"] = "sk-BadKeyToTriggerRetry"
        
        # Create ChatOpenAI with max_retries=3
        llm = ChatOpenAI(model="gpt-4o", max_retries=3)
        
        start_time = time.time()
        
        print("🔄 Testing API call with retries (this will fail but should retry 3 times)...")
        
        try:
            # This should fail but retry 3 times
            result = llm.invoke("Test message")
            print("❓ Unexpected success - API call didn't fail")
            retry_success = False
            retry_count = 0
        except Exception as e:
            error_str = str(e)
            elapsed = time.time() - start_time
            
            print(f"❌ Expected error after {elapsed:.2f}s: {error_str[:100]}...")
            
            # Try to determine if retries happened based on timing
            # Each retry would add ~1s of delay, so if elapsed > 3s, likely retried
            retry_count = int(elapsed / 1)
            retry_success = retry_count >= 3
            
            if retry_success:
                print(f"✅ Retry mechanism worked! Approximate retries: {retry_count}")
            else:
                print(f"⚠️ Retry mechanism might not have worked. Elapsed time suggests ~{retry_count} attempts.")
        
        return {
            "success": retry_success,
            "retry_count": retry_count,
            "elapsed": time.time() - start_time
        }
    finally:
        # Restore original API key
        if original_key:
            os.environ["OPENAI_API_KEY"] = original_key
        else:
            del os.environ["OPENAI_API_KEY"]

def main():
    """Run all enhanced tests"""
    print_header("Enhanced Agent Tests")
    
    # Check if agent module is available
    if 'agent' not in sys.modules:
        print("❌ Could not import agent module. Make sure it's in the current directory.")
        return
    
    # Run tests
    results = {}
    
    # Test 1: Realistic query
    results["realistic_query"] = run_test_with_realistic_query()
    
    # Test 2: Pre-defined intent
    results["predefined_intent"] = run_test_with_predefined_intent()
    
    # Test 3: Retry mechanism
    results["retry_mechanism"] = check_retries()
    
    # Save results
    with open("enhanced_test_results.json", "w") as f:
        json.dump(results, f, indent=2)
    
    print_header("Test Summary")
    
    # Print summary
    success_count = sum(1 for r in results.values() if r.get("success", False))
    print(f"Tests completed: {success_count}/{len(results)} successful")
    
    for test_name, result in results.items():
        success = result.get("success", False)
        status = "✅ Passed" if success else "❌ Failed"
        print(f"{status} {test_name} in {result.get('elapsed', 0):.2f}s")
    
    print(f"\nDetailed results saved to enhanced_test_results.json")

if __name__ == "__main__":
    main()
