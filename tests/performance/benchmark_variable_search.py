"""
Advanced timeout diagnostic for variable search.
This script performs a more detailed analysis of the variable search
process to identify specific bottlenecks and optimization opportunities.
"""

import os
import sys
import time
import json
import re
import traceback
from datetime import datetime
from typing import Dict, Any, List, Optional
import concurrent.futures
import importlib.util

# Add current directory to path for imports
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(script_dir)

# Check for required modules
REQUIRED_MODULES = [
    "agent", 
    "detailed_analysis_optimized", 
    "dataset_knowledge"
]

missing_modules = []
for module in REQUIRED_MODULES:
    if not os.path.exists(os.path.join(script_dir, f"{module}.py")):
        missing_modules.append(module)

if missing_modules:
    print(f"⚠️ Missing required modules: {', '.join(missing_modules)}")
    print("Please ensure all required modules are in the current directory.")
    sys.exit(1)

# Try to import key functions
try:
    # Import the variable selection function dynamically
    from detailed_analysis_optimized import benchmark_analysis_performance
    print("✅ Successfully imported benchmark_analysis_performance")
except ImportError as e:
    print(f"⚠️ Error importing benchmark_analysis_performance: {e}")
    print("Using alternative approach...")

def benchmark_variable_search(query: str, timeout: int = 60):
    """Benchmark the variable search process with detailed timing information"""
    print(f"🔄 Running variable search benchmark for query: '{query}'")
    print(f"⏱️ Timeout set to {timeout} seconds")
    
    start_time = time.time()
    results = {
        "query": query,
        "timeout": timeout,
        "start_time": datetime.now().isoformat(),
        "steps": [],
        "success": False,
        "error": None,
        "elapsed": 0,
        "bottlenecks": []
    }
    
    # Import modules dynamically for isolation
    try:
        # Step 1: Initialize agent
        step_start = time.time()
        results["steps"].append({
            "name": "initialize_agent",
            "start": step_start - start_time,
            "status": "running"
        })
        
        # Use a safer approach to get the agent module
        spec = importlib.util.spec_from_file_location("agent", os.path.join(script_dir, "agent.py"))
        agent_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(agent_module)
        
        # Create agent
        agent = agent_module.create_agent()
        
        # Record initialization time
        results["steps"][-1]["end"] = time.time() - start_time
        results["steps"][-1]["duration"] = results["steps"][-1]["end"] - results["steps"][-1]["start"]
        results["steps"][-1]["status"] = "success"
        print(f"✅ Agent initialized in {results['steps'][-1]['duration']:.2f}s")
        
        # Step 2: Prepare state for variable search
        step_start = time.time()
        results["steps"].append({
            "name": "prepare_state",
            "start": step_start - start_time,
            "status": "running"
        })
        
        # Create a basic state for the agent
        state = {
            "messages": [{"role": "user", "content": query}],
            "intent": "query_variable_database",
            "user_query": query,
            "original_query": query,
            "dataset": ["ALL"],
            "selected_variables": [],
            "analysis_type": "descriptive",
            "user_approved": False,
            "analysis_result": {},
            "language": "es"
        }
        
        # Create config for the agent
        config = {
            "configurable": {
                "thread_id": f"benchmark_{int(time.time())}",
                "checkpoint_id": f"benchmark_{int(time.time())}",
            }
        }
        
        # Record state preparation time
        results["steps"][-1]["end"] = time.time() - start_time
        results["steps"][-1]["duration"] = results["steps"][-1]["end"] - results["steps"][-1]["start"]
        results["steps"][-1]["status"] = "success"
        print(f"✅ State prepared in {results['steps'][-1]['duration']:.2f}s")
        
        # Step 3: Run agent with timeout
        step_start = time.time()
        results["steps"].append({
            "name": "run_agent",
            "start": step_start - start_time,
            "status": "running"
        })
        
        try:
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(agent.invoke, state, config=config)
                result = future.result(timeout=timeout)
                
                # Record successful run time
                results["steps"][-1]["end"] = time.time() - start_time
                results["steps"][-1]["duration"] = results["steps"][-1]["end"] - results["steps"][-1]["start"]
                results["steps"][-1]["status"] = "success"
                print(f"✅ Agent run completed in {results['steps'][-1]['duration']:.2f}s")
                
                # Check for selected variables
                if result and isinstance(result, dict) and "selected_variables" in result:
                    variables = result.get("selected_variables", [])
                    var_count = len(variables) if variables else 0
                    print(f"📊 Found {var_count} variables")
                    results["variables_count"] = var_count
                    results["success"] = var_count > 0
                    
                    # Add some sample variables to the results
                    if variables:
                        results["sample_variables"] = variables[:5]
                
        except concurrent.futures.TimeoutError:
            elapsed = time.time() - step_start
            results["steps"][-1]["end"] = time.time() - start_time
            results["steps"][-1]["duration"] = elapsed
            results["steps"][-1]["status"] = "timeout"
            results["error"] = f"Timeout after {elapsed:.2f}s"
            print(f"⚠️ Agent run timed out after {elapsed:.2f}s")
            results["bottlenecks"].append({
                "step": "run_agent",
                "reason": "timeout",
                "suggestion": "Increase the timeout or optimize the variable selection process"
            })
        
        except Exception as e:
            elapsed = time.time() - step_start
            results["steps"][-1]["end"] = time.time() - start_time
            results["steps"][-1]["duration"] = elapsed
            results["steps"][-1]["status"] = "error"
            results["error"] = str(e)
            print(f"❌ Agent run failed after {elapsed:.2f}s: {e}")
            print(traceback.format_exc())
            results["bottlenecks"].append({
                "step": "run_agent",
                "reason": "error",
                "suggestion": "Debug the agent invocation error"
            })
        
    except Exception as e:
        elapsed = time.time() - start_time
        results["error"] = str(e)
        print(f"❌ Benchmark failed: {e}")
        print(traceback.format_exc())
    
    # Calculate total elapsed time
    results["elapsed"] = time.time() - start_time
    print(f"🏁 Benchmark completed in {results['elapsed']:.2f}s")
    
    # Analyze results for bottlenecks
    if not results["bottlenecks"]:
        step_times = [(step["name"], step["duration"]) for step in results["steps"] if "duration" in step]
        if step_times:
            # Find the step with the longest duration
            slowest_step = max(step_times, key=lambda x: x[1])
            if slowest_step[1] > 5:  # If step takes more than 5 seconds
                results["bottlenecks"].append({
                    "step": slowest_step[0],
                    "reason": "slow_execution",
                    "duration": slowest_step[1],
                    "suggestion": f"Optimize the {slowest_step[0]} step which took {slowest_step[1]:.2f}s"
                })
    
    # Save results to file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    clean_query = re.sub(r'[^a-zA-Z0-9]', '_', query)[:20]
    filename = f"variable_search_benchmark_{clean_query}_{timestamp}.json"
    
    with open(filename, "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"📄 Results saved to {filename}")
    
    return results

if __name__ == "__main__":
    # Default query if none provided
    default_query = "health"
    
    if len(sys.argv) > 1:
        query = sys.argv[1]
    else:
        query = default_query
        print(f"No query provided, using default: '{default_query}'")
        print("Usage: python benchmark_variable_search.py \"your query here\"")
    
    # Run the benchmark
    benchmark_variable_search(query, timeout=60)
