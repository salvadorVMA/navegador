#!/usr/bin/env python3
"""
Agent Performance Analyzer - Fixed Version

This script analyzes the performance of the Navegador agent, with a focus on
identifying bottlenecks and providing optimization recommendations.
"""

import os
import sys
import time
import argparse
import traceback
import threading
import atexit
from datetime import datetime

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Initialize logging
log_file = open("agent_analysis.log", "w", encoding="utf-8")
shutdown_event = threading.Event()

def log(message):
    """Log message to both console and file"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    formatted_message = f"[{timestamp}] {message}"
    print(formatted_message)
    log_file.write(f"{formatted_message}\n")
    log_file.flush()

def cleanup():
    """Clean up resources"""
    if log_file:
        log_file.close()

# Register cleanup function to run on exit
atexit.register(cleanup)

# Try to import optional dependencies
try:
    import psutil
    PSUTIL_AVAILABLE = True
    log("✅ psutil available - detailed resource monitoring enabled")
except ImportError:
    log("⚠️ psutil not installed - detailed resource monitoring disabled")
    PSUTIL_AVAILABLE = False

# Try to import LangSmith monitoring
try:
    from langsmith.client import Client as LangSmithClient
    from langchain_core.tracers import LangChainTracer
    LANGSMITH_AVAILABLE = True
    log("✅ LangSmith packages available")
except ImportError:
    log("⚠️ LangSmith packages not found - monitoring will be disabled")
    LANGSMITH_AVAILABLE = False

# Import agent with proper error handling
try:
    import agent
    log(f"✅ Successfully imported agent module")
except Exception as e:
    log(f"❌ Error importing agent module: {str(e)}")
    sys.exit(1)

def setup_langsmith():
    """Set up LangSmith monitoring"""
    # Check for API key in environment variables
    langsmith_api_key = os.environ.get("LANGSMITH_API_KEY") or os.environ.get("LANGCHAIN_API_KEY")
    langsmith_project = os.environ.get("LANGCHAIN_PROJECT", "navegador-analysis")
    
    if not langsmith_api_key:
        log("⚠️ No LangSmith API key found - monitoring disabled")
        return None
    
    if not LANGSMITH_AVAILABLE:
        log("⚠️ LangSmith packages not available - monitoring disabled")
        return None
    
    try:
        # Enable tracing
        os.environ["LANGCHAIN_TRACING_V2"] = "true"
        os.environ["LANGCHAIN_PROJECT"] = langsmith_project
        
        # Create client
        client = LangSmithClient(api_key=langsmith_api_key)
        log(f"✅ LangSmith monitoring initialized for project: {langsmith_project}")
        return client
    except Exception as e:
        log(f"❌ Error initializing LangSmith: {str(e)}")
        return None

def create_thread_config(thread_id=None):
    """Create a thread configuration for the agent"""
    if thread_id is None:
        thread_id = f"analysis_{int(time.time())}"
    
    # Create config
    config = {
        "configurable": {
            "thread_id": thread_id,
            "callbacks": []
        }
    }
    return config

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
    # Try to import state normalizer if available
    try:
        from state_normalizer import normalize_state
        
        # Create state
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
        
        # Normalize state
        normalized_state = normalize_state(state)
        log("✅ Created agent state using state normalizer")
        return normalized_state
        
    except ImportError:
        # Fallback state creation
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
        log("⚠️ Created fallback agent state (state_normalizer not available)")
        return state

def analyze_query(agent_instance, query, dataset=None, language="es", detailed=False):
    """Analyze a single query"""
    log("=" * 70)
    log(f"🔍 Analyzing query: '{query}'")
    
    # Create state and config
    state = create_test_state(query, dataset, language)
    thread_id = f"analysis_{int(time.time())}"
    config = create_thread_config(thread_id)
    
    # Start timing
    start_time = time.time()
    
    # Monitor resources if detailed mode and psutil available
    if detailed and PSUTIL_AVAILABLE:
        process = psutil.Process(os.getpid())
        mem_before = process.memory_info().rss / 1024 / 1024  # MB
        cpu_before = process.cpu_percent()
        log(f"📊 Initial resources - Memory: {mem_before:.2f} MB, CPU: {cpu_before}%")
    
    try:
        # Invoke agent
        log(f"🔄 Invoking agent with thread_id: {thread_id}")
        response = agent_instance.invoke(state, config=config)
        
        # Calculate timing
        elapsed = time.time() - start_time
        log(f"✅ Query processed in {elapsed:.2f} seconds")
        
        # Monitor resources if detailed mode
        if detailed and PSUTIL_AVAILABLE:
            mem_after = process.memory_info().rss / 1024 / 1024  # MB
            cpu_after = process.cpu_percent()
            mem_diff = mem_after - mem_before
            log(f"📊 Final resources - Memory: {mem_after:.2f} MB ({mem_diff:+.2f} MB), CPU: {cpu_after}%")
        
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
    parser.add_argument("--varselect", action="store_true", help="Only analyze variable selection")
    parser.add_argument("--detailed", action="store_true", help="Include detailed resource monitoring")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode with additional logging")
    
    args = parser.parse_args()
    
    # Set debug mode if requested
    if args.debug:
        log("🐛 Debug mode enabled")
    
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
    
    # Set up LangSmith
    langsmith_client = setup_langsmith()
    
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
            language=args.language,
            detailed=args.detailed
        )
        results.append(result)
    
    # Calculate overall statistics
    successful = sum(1 for r in results if r.get("success", False))
    if results:
        avg_time = sum(r["elapsed"] for r in results) / len(results)
        log(f"📊 Summary: {successful}/{len(results)} queries successful, average time: {avg_time:.2f}s")
    
    # Clean up
    log("✅ Analysis complete")
    cleanup()

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        log(f"❌ Unexpected error: {str(e)}")
        log(traceback.format_exc())
        sys.exit(1)
