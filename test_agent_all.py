#!/usr/bin/env python3
"""
Agent Invocation Test Runner

This script runs all three debug tests and summarizes the results to provide 
a comprehensive diagnosis of the agent invocation issues.

Run with: python test_agent_all.py
"""

import os
import sys
import subprocess
import time
import json
from typing import List, Dict, Any

def print_section(title):
    """Print a section title with formatting"""
    print(f"\n{'=' * 80}")
    print(f"  {title}")
    print(f"{'=' * 80}\n")

def run_test(script_name: str) -> int:
    """Run a test script and return the exit code"""
    print_section(f"Running {script_name}")
    try:
        result = subprocess.run(
            ["python", script_name],
            check=False,
            text=True
        )
        return result.returncode
    except Exception as e:
        print(f"Error running {script_name}: {e}")
        return 1

def analyze_results():
    """Analyze all test results and provide a consolidated diagnosis"""
    print_section("Analyzing Results")
    
    results_files = {
        "agent_debug_results.json": False,
        "checkpointer_debug_results.json": False,
        "intent_debug_results.json": False
    }
    
    combined_results = {}
    
    # Check which result files exist
    for file in results_files:
        if os.path.exists(file):
            results_files[file] = True
            print(f"✅ Found {file}")
            try:
                with open(file, 'r') as f:
                    try:
                        combined_results[file] = json.load(f)
                    except json.JSONDecodeError as e:
                        print(f"❌ Error loading {file}: {e}")
                        print(f"   Running fix_json_results.py may resolve this issue")
                        combined_results[file] = {}
            except Exception as e:
                print(f"❌ Error accessing {file}: {e}")
        else:
            print(f"❌ {file} not found")
    
    # If no results files, can't analyze
    if not any(results_files.values()):
        print("❌ No results files found. Tests may have failed to run.")
        return
    
    # Initialize findings
    findings = []
    
    # Analyze agent_debug_results.json
    if results_files["agent_debug_results.json"] and "agent_debug_results.json" in combined_results:
        results = combined_results["agent_debug_results.json"]
        
        # Check if test query worked but real query failed
        if "test_result" in results and "real_result" in results:
            if results["test_result"].get("success", False) and not results["real_result"].get("success", False):
                findings.append("✅ Successfully reproduced the issue: Test query works but real query fails")
                
                # Check if hybrid approach worked
                if "hybrid_result" in results and results["hybrid_result"].get("success", False):
                    findings.append("🔍 Key finding: Using hardcoded state like the test fixes the issue")
            elif results["test_result"].get("success", False) and results["real_result"].get("success", False):
                findings.append("⚠️ Both test and real queries worked in isolation - issue may be environment-specific")
    
    # Analyze checkpointer_debug_results.json
    if results_files["checkpointer_debug_results.json"] and "checkpointer_debug_results.json" in combined_results:
        results = combined_results["checkpointer_debug_results.json"]
        
        result1_success = results.get("result1", {}).get("success", False)
        result2_success = results.get("result2", {}).get("success", False)
        result3_success = results.get("result3", {}).get("success", False)
        
        if result1_success and result2_success:
            findings.append("✅ Checkpointer correctly persists state between invocations")
        else:
            findings.append("❌ Checkpointer may be failing to persist state between invocations")
        
        # Check if variables were selected
        if "selected_variables_count" in results and results["selected_variables_count"] > 0:
            findings.append(f"✅ Query successfully selected {results['selected_variables_count']} variables")
        else:
            findings.append("❌ No variables were selected - query functionality may be broken")
    
    # Analyze intent_debug_results.json
    if results_files["intent_debug_results.json"] and "intent_debug_results.json" in combined_results:
        results = combined_results["intent_debug_results.json"]
        
        if isinstance(results, list) and len(results) > 0:
            classified_successes = sum(1 for r in results if r.get("classified_success", False))
            hardcoded_successes = sum(1 for r in results if r.get("hardcoded_success", False))
            
            if classified_successes < hardcoded_successes:
                findings.append("🔍 Key finding: Hardcoded intents work better than classified ones")
                findings.append("👉 The issue is likely with intent classification in real queries")
            elif classified_successes == hardcoded_successes == len(results):
                findings.append("✅ All intent tests passed regardless of classification method")
            else:
                findings.append(f"⚠️ Mixed results: {classified_successes}/{len(results)} classified intents worked, {hardcoded_successes}/{len(results)} hardcoded intents worked")
    
    # Print all findings
    print_section("Findings")
    if findings:
        for i, finding in enumerate(findings, 1):
            print(f"{i}. {finding}")
    else:
        print("No clear findings from the test results")
    
    # Final diagnosis
    print_section("Diagnosis")
    
    if any("Key finding" in finding for finding in findings):
        print("The issue appears to be:")
        
        if any("intent classification" in finding.lower() for finding in findings):
            print("1. Intent classification is not working correctly in real queries.")
            print("   While the test uses a hardcoded 'query_variable_database' intent,")
            print("   real queries rely on the intent classifier which may return incorrect intents.")
            print("\nRecommended fix: Ensure intent classification returns the correct intent,")
            print("or modify handle_auto_next_step to use a hardcoded intent for known query types.")
        
        if any("hardcoded state" in finding.lower() for finding in findings):
            print("2. The state construction differs between test and real queries.")
            print("   Test uses a simpler state with minimal fields, while real queries")
            print("   use more complex state that might contain incompatible values.")
            print("\nRecommended fix: Make the real query state construction match the test state more closely.")
        
        if any("checkpointer" in finding.lower() for finding in findings):
            print("3. There may be issues with the checkpointer's persistence between invocations.")
            print("   Test queries create a fresh state each time, while real queries might")
            print("   be affected by previously persisted state.")
            print("\nRecommended fix: Consider disabling persistence for user queries or")
            print("ensure proper thread/checkpoint ID management.")
    else:
        print("Based on the available results, no clear diagnosis can be made.")
        print("Consider running the tests individually and checking their outputs for more details.")
    
    print("\nThe most likely explanation is that there's a mismatch between how agent state")
    print("is constructed in tests vs. real queries, particularly with the intent field.")

def main():
    """Run all agent tests and consolidate results"""
    print_section("Agent Invocation Test Suite")
    print("This script will run multiple tests to diagnose agent invocation issues.")
    
    test_scripts = [
        "debug_agent_invocation.py",
        "debug_agent_checkpointer.py",
        "debug_agent_intent.py"
    ]
    
    results = {}
    
    for script in test_scripts:
        start_time = time.time()
        exit_code = run_test(script)
        elapsed = time.time() - start_time
        
        results[script] = {
            "exit_code": exit_code,
            "elapsed": elapsed,
            "success": exit_code == 0
        }
        
        print(f"{'✅ Passed' if exit_code == 0 else '❌ Failed'} {script} in {elapsed:.1f}s")
    
    # Analyze all results
    analyze_results()
    
    # Final summary
    print_section("Summary")
    success_count = sum(1 for r in results.values() if r["success"])
    print(f"Tests completed: {success_count}/{len(test_scripts)} successful")
    
    for script, result in results.items():
        status = "✅ Passed" if result["success"] else "❌ Failed"
        print(f"{status} {script} in {result['elapsed']:.1f}s")

if __name__ == "__main__":
    main()
