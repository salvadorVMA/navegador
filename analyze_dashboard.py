#!/usr/bin/env python3
"""
Analyzer to find issues with the dashboard code
"""

import re
import os

def analyze_dashboard_code():
    """Analyze dashboard.py code for issues"""
    file_path = "dashboard.py"
    if not os.path.exists(file_path):
        print(f"File {file_path} not found")
        return
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Check for basic structure
    print(f"File size: {len(content)} bytes")
    
    # Find key functions
    functions = {
        'handle_auto_next_step': 0,
        'process_agent_response': 0,
        'get_agent_response': 0,
        'extract_agent_content': 0,
        'update_session_from_agent_response': 0
    }
    
    for func in functions:
        pattern = rf'def {func}\([^)]*\):'
        matches = re.findall(pattern, content)
        functions[func] = len(matches)
        print(f"Function {func}: {len(matches)} occurrences")
    
    # Check for duplicates
    duplicate_defs = [func for func, count in functions.items() if count > 1]
    if duplicate_defs:
        print(f"⚠️ Duplicate function definitions found: {', '.join(duplicate_defs)}")
    
    # Check for agent invocation code
    critical_code_snippets = [
        "agent_state = {",
        "thread_id = f\"chat_{int(time.time())}\"",
        "with concurrent.futures.ThreadPoolExecutor() as executor:",
        "agent_response = future.result(timeout=AGENT_TIMEOUT)",
        "return process_agent_response(agent_response, session_data, chat_data, user_message)"
    ]
    
    for snippet in critical_code_snippets:
        if snippet in content:
            print(f"✅ Found critical code: {snippet[:30]}...")
        else:
            print(f"❌ Missing critical code: {snippet}")
    
    # Check auto-next-step interval
    intervals = re.findall(r'dcc\.Interval\(id="auto-next-step-interval"', content)
    if intervals:
        print(f"✅ Found auto-next-step interval: {len(intervals)} occurrences")
        
        # Check if interval is enabled
        if "disabled=True" in content and "disabled=False" in content:
            print("✅ Interval can be both enabled and disabled")
        elif "disabled=True" in content:
            print("⚠️ Interval might always be disabled")
        elif "disabled=False" in content:
            print("⚠️ Interval might always be enabled")
    else:
        print("❌ Missing auto-next-step interval")
    
    # Check interval callback
    interval_callbacks = re.findall(r'\[Input\("auto-next-step-interval", "n_intervals"\)\]', content)
    if interval_callbacks:
        print(f"✅ Found interval callback: {len(interval_callbacks)} occurrences")
    else:
        print("❌ Missing interval callback")
    
    # Extract the handle_auto_next_step function content
    handle_func_match = re.search(r'def handle_auto_next_step\([^)]*\):(.*?)(?=def|\Z)', content, re.DOTALL)
    if handle_func_match:
        handle_func = handle_func_match.group(1)
        print("\nAnalyzing handle_auto_next_step function:")
        
        # Check if process_agent_response is called
        if "process_agent_response" in handle_func:
            print("✅ handle_auto_next_step calls process_agent_response")
        else:
            print("❌ handle_auto_next_step does NOT call process_agent_response")
        
        # Check if agent.invoke is called
        if "agent.invoke" in handle_func:
            print("✅ handle_auto_next_step calls agent.invoke")
        else:
            print("❌ handle_auto_next_step does NOT call agent.invoke")
        
        # Check for correct indentation in try blocks
        try_blocks = re.findall(r'(\s*)try:', handle_func)
        except_blocks = re.findall(r'(\s*)except', handle_func)
        if len(try_blocks) > len(except_blocks):
            print(f"⚠️ Possible unclosed try blocks: {len(try_blocks)} try vs {len(except_blocks)} except")
    else:
        print("❌ Could not extract handle_auto_next_step function for analysis")

if __name__ == "__main__":
    analyze_dashboard_code()
