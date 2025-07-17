#!/usr/bin/env python3
"""
Agent Performance Analyzer - Simplified Version

A simplified version of the agent performance analyzer with minimal dependencies
and better error handling.
"""

import os
import sys
import time
import argparse
import traceback
from datetime import datetime
import atexit

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Initialize logging
log_file_path = "agent_analysis.log"
log_file = open(log_file_path, "w", encoding="utf-8")

def log(message):
    """Log message to both console and file"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    formatted_message = f"[{timestamp}] {message}"
    print(formatted_message)
    log_file.write(f"{formatted_message}\n")
    log_file.flush()

def cleanup():
    """Clean up resources"""
    global log_file
    if log_file:
        log_file.close()
        log_file = None

# Register cleanup function to run on exit
atexit.register(cleanup)

# Try to import agent
try:
    import agent
    log(f"✅ Successfully imported agent module")
except Exception as e:
    log(f"❌ Error importing agent module: {str(e)}")
    sys.exit(1)

def create_thread_config(thread_id=None):
    """Create a thread configuration for the agent"""
    if thread_id is None:
        thread_id = f"analysis_{int(time.time())}"
    
    # Create config
    return {
        "configurable": {
            "thread_id": thread_id,
            "callbacks": []
        }
    }

def create_agent_instance():
    """Create an agent instance with persistence enabled"""
    try:
        log("🔄 Creating agent instance...")
        start_time = time.time()
        agent_instance = agent.create_agent(enable_persistence=True)
        elapsed = time.time() - start_time
        log(f"✅ Agent instance created successfully in {elapsed:.2f}s")
        return agent_instance
    except Exception as e:
        log(f"❌ Error creating agent: {str(e)}")
        log(traceback.format_exc())
        return None

def create_test_state(query, dataset=None, language="es"):
    """Create a test state for the agent"""
    # Create basic state
    state = {
        "messages": [{"type": "human", "content": query}],
        "user_query": query,
        "original_query": query,
        "intent": "query_variable_database",
        "dataset": dataset or ["ALL"],
        "selected_variables": [],
        "analysis_type": "descriptive",
        "user_approved": False,
        "analysis_result": {}
    }
    return state

def analyze_query(agent_instance, query, dataset=None, language="es"):
    """Analyze a single query"""
    log("=" * 70)
    log(f"🔍 Analyzing query: '{query}'")
    
    # Create state and config
    state = create_test_state(query, dataset, language)
    thread_id = f"analysis_{int(time.time())}"
    config = create_thread_config(thread_id)
    
    # Start timing
    start_time = time.time()
    
    try:
        # Invoke agent
        log(f"🔄 Invoking agent with thread_id: {thread_id}")
        response = agent_instance.invoke(state, config=config)
        
        # Calculate timing
        elapsed = time.time() - start_time
        log(f"✅ Query processed in {elapsed:.2f} seconds")
        
        # Check selected variables
        selected_vars = []
        if isinstance(response, dict) and "selected_variables" in response:
            selected_vars = response["selected_variables"]
            log(f"📋 Selected {len(selected_vars)} variables")
            if selected_vars and len(selected_vars) > 0:
                sample = selected_vars[:3]
                log(f"📋 Sample variables: {', '.join(sample)}")
        
        return {
            "success": True,
            "elapsed": elapsed,
            "response": response
        }
    
    except Exception as e:
        elapsed = time.time() - start_time
        log(f"❌ Error processing query: {str(e)}")
        log(traceback.format_exc())
        return {
            "success": False,
            "elapsed": elapsed,
            "error": str(e),
            "traceback": traceback.format_exc()
        }

def main():
    """Main entry point"""
    # Parse arguments
    parser = argparse.ArgumentParser(description="Analyze agent performance")
    parser.add_argument("query", nargs="?", help="Query to analyze")
    parser.add_argument("--queries", help="Comma-separated list of queries to analyze")
    parser.add_argument("--datasets", help="Comma-separated list of datasets to use")
    parser.add_argument("--language", default="es", help="Language for queries (default: es)")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode with additional logging")
    
    args = parser.parse_args()
    
    # Set debug mode if requested
    if args.debug:
        log("🐛 Debug mode enabled")
        log(f"💾 Logs will be written to {os.path.abspath(log_file_path)}")
    
    # Get queries from arguments
    queries = []
    if args.query:
        queries.append(args.query)
    if args.queries:
        queries.extend([q.strip() for q in args.queries.split(",")])
    
    # Default queries if none provided
    if not queries:
        default_queries = [
            "¿Qué opinan los mexicanos sobre la salud?",
            "deporte",
            "educación"
        ]
        log(f"⚠️ No queries provided, using default queries: {', '.join(default_queries)}")
        queries = default_queries
    
    # Parse datasets if provided
    datasets = None
    if args.datasets:
        datasets = [d.strip().upper() for d in args.datasets.split(",")]
        log(f"📊 Using datasets: {datasets}")
    
    # Create agent instance
    agent_instance = create_agent_instance()
    if not agent_instance:
        log("❌ Failed to create agent instance. Exiting.")
        sys.exit(1)
    
    # Process each query
    results = []
    for i, query in enumerate(queries):
        log(f"🔄 Processing query {i+1}/{len(queries)}: '{query}'")
        result = analyze_query(
            agent_instance=agent_instance,
            query=query,
            dataset=datasets,
            language=args.language
        )
        results.append(result)
        
        # Small delay between queries
        if i < len(queries) - 1:
            time.sleep(1)
    
    # Calculate overall statistics
    successful = sum(1 for r in results if r.get("success", False))
    if results:
        avg_time = sum(r["elapsed"] for r in results) / len(results)
        log(f"📊 Summary: {successful}/{len(results)} queries successful, average time: {avg_time:.2f}s")
    
    # Clean up
    log("✅ Analysis complete")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        log("\n⚠️ Analysis interrupted by user")
    except Exception as e:
        log(f"❌ Unexpected error: {str(e)}")
        log(traceback.format_exc())
    finally:
        cleanup()
