#!/usr/bin/env python3
"""
Test script to verify the ThreadPoolExecutor implementation in handle_auto_next_step
"""
import time
import os
import sys
import importlib.util
import traceback

def check_implementation():
    """Check if ThreadPoolExecutor is properly implemented in handle_auto_next_step"""
    dashboard_path = 'dashboard.py'
    
    if not os.path.exists(dashboard_path):
        print(f"❌ Dashboard file not found: {dashboard_path}")
        return False
    
    # Read the file to check for ThreadPoolExecutor implementation
    with open(dashboard_path, 'r') as f:
        content = f.read()
    
    # Check for key implementation details
    checks = [
        ("ThreadPoolExecutor", "with concurrent.futures.ThreadPoolExecutor() as executor:", 
         "ThreadPoolExecutor is used for non-blocking agent invocation"),
        
        ("Future submission", "future = executor.submit(agent.invoke, agent_state, config=agent_config)", 
         "Agent invocation is properly submitted to ThreadPoolExecutor"),
        
        ("Timeout handling", "future.result(timeout=", 
         "Timeout is set for agent invocation"),
        
        ("TimeoutError exception", "except concurrent.futures.TimeoutError:", 
         "TimeoutError exception is caught"),
        
        ("Timeout message", "timeout_msg =", 
         "Timeout message is provided to user"),
        
        ("Process agent response", "return process_agent_response(agent_response, session_data, chat_data, user_message)", 
         "Agent response is processed correctly")
    ]
    
    passed = 0
    failed = 0
    
    print("===== Checking ThreadPoolExecutor Implementation =====\n")
    
    for check_name, check_text, description in checks:
        if check_text in content:
            print(f"✅ {check_name}: {description}")
            passed += 1
        else:
            print(f"❌ {check_name}: {description}")
            failed += 1
    
    print(f"\nResults: {passed} checks passed, {failed} checks failed")
    
    # Check specifically for handle_auto_next_step implementation
    if "def handle_auto_next_step" in content and "ThreadPoolExecutor" in content:
        print("\n✅ ThreadPoolExecutor is implemented in handle_auto_next_step function")
        
        # Try to find the AGENT_TIMEOUT value
        import re
        timeout_match = re.search(r'AGENT_TIMEOUT\s*=\s*(\d+(\.\d+)?)', content)
        if timeout_match:
            timeout_value = timeout_match.group(1)
            print(f"✅ AGENT_TIMEOUT is set to {timeout_value} seconds")
        else:
            print("⚠️ Could not determine AGENT_TIMEOUT value")
        
        return passed > 0 and failed == 0
    else:
        print("\n❌ ThreadPoolExecutor is NOT implemented in handle_auto_next_step function")
        return False

if __name__ == "__main__":
    try:
        success = check_implementation()
        if success:
            print("\n✅ ThreadPoolExecutor implementation looks good!")
            print("To fully test the implementation, run the dashboard and try a query that")
            print("might take longer than the timeout period.")
        else:
            print("\n❌ ThreadPoolExecutor implementation is incomplete or incorrect.")
            print("Please ensure all required components are implemented.")
        
    except Exception as e:
        print(f"\n❌ Error during test: {str(e)}")
        traceback.print_exc()
