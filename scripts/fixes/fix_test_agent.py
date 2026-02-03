#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script to fix the test_agent_tracing.py file
"""

import re
import sys

def fix_file(filename):
    """Fix the test_agent_tracing.py file"""
    with open(filename, 'r') as f:
        content = f.read()
    
    # Fix the run_test_queries function
    run_test_queries_func = '''
def run_test_queries(queries=None, language="es", datasets=None, profiler=None):
    """Run a series of test queries through the agent"""
    if profiler is None:
        profiler = AgentProfiler()
    
    if queries is None:
        queries = DEFAULT_QUERIES
    
    # Ensure datasets is a list if provided
    if datasets and not isinstance(datasets, list):
        datasets = [datasets]
    
    for i, query in enumerate(queries):
        print(f"\\n[{i+1}/{len(queries)}] Testing query: '{query}'")
        profiler.profile_query(query, language=language, datasets=datasets)
    
    # Print summary stats
    profiler.print_summary()
    
    # Check LangSmith traces
    profiler.check_langsmith_traces()
    
    return profiler
'''
    
    # Fix the main function
    main_function = '''
def main():
    """Main function for running the agent tracing test"""
    import argparse
    
    # Create argument parser
    parser = argparse.ArgumentParser(description="Test the navigator agent with tracing")
    parser.add_argument("-q", "--query", nargs="+", help="Custom queries to test (can provide multiple)")
    parser.add_argument("-l", "--language", default="es", help="Language to use for queries (default: es)")
    parser.add_argument("-d", "--datasets", nargs="+", help="Datasets to query (default: ALL)")
    parser.add_argument("-n", "--no-langsmith", action="store_true", help="Disable LangSmith tracing")
    
    args = parser.parse_args()
    
    # Print header
    print("\\n" + "=" * 80)
    print("🔍 AGENT TRACING AND MONITORING TEST")
    print("=" * 80)
    
    # Setup LangSmith
    if not args.no_langsmith:
        langsmith_enabled = setup_langsmith()
        if langsmith_enabled:
            print("✅ LangSmith tracing enabled")
        else:
            print("⚠️ LangSmith tracing not enabled. Limited functionality available.")
    else:
        print("ℹ️ LangSmith tracing disabled by user")
        langsmith_enabled = False
    
    # Create profiler
    profiler = AgentProfiler()
    
    try:
        # Run queries
        if args.query:
            queries = args.query
            print(f"🔍 Running {len(queries)} custom queries from command line")
            run_test_queries(queries, profiler=profiler, language=args.language, datasets=args.datasets)
        else:
            print(f"🔍 Running {len(DEFAULT_QUERIES)} default test queries")
            run_test_queries(profiler=profiler)
    except KeyboardInterrupt:
        print("\\n⚠️ Test interrupted by user")
    except Exception as e:
        print(f"\\n❌ Error during testing: {e}")
        traceback.print_exc()
    finally:
        # Make sure to clean up resources
        print("\\n🧹 Cleaning up resources...")
        if profiler.agent_instance is not None:
            print("   Ensuring agent workflow is properly closed")
            # No explicit close method needed, Python's GC will handle it
'''
    
    # Find and replace the run_test_queries function
    pattern1 = r'def run_test_queries\([^)]*\):[\s\S]*?return profiler'
    content = re.sub(pattern1, run_test_queries_func.strip(), content)
    
    # Find and replace the main function
    pattern2 = r'def main\(\):[\s\S]*?run_test_queries\(profiler=profiler\)'
    content = re.sub(pattern2, main_function.strip(), content)
    
    # Fix the imports
    imports = '''
# First, check if we can import the required modules
try:
    import langsmith
    from langchain.schema.runnable import RunnableConfig
    from langchain_core.tracers.context import tracing_enabled
    from langchain_core.tracers.langchain import LangChainTracer
    from langchain_core.tracers.langsmith import LangSmithTracer
    has_langsmith = True
except ImportError:
    has_langsmith = False
    print("⚠️ LangSmith modules not available. Limited functionality will be used.")

# Import our own modules
try:
    # Add the current directory to the path to make imports work
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    
    # Import modules carefully with fallbacks
    try:
        import state_normalizer
    except ImportError:
        state_normalizer = None
        print("⚠️ Could not import state_normalizer module")
    
    try:
        import agent
    except ImportError:
        agent = None
        print("⚠️ Could not import agent module")
    
    try:
        from dashboard import create_agent_config
    except ImportError:
        create_agent_config = None
        print("⚠️ Could not import create_agent_config from dashboard")
        
    has_agent = agent is not None
except ImportError as e:
    has_agent = False
    agent = None
    state_normalizer = None
    create_agent_config = None
    print(f"⚠️ Could not import modules: {e}")
    traceback.print_exc()
'''
    
    # Replace imports section
    pattern3 = r'# First, check if we can import the required modu.*?traceback\.print_exc\(\)'
    content = re.sub(pattern3, imports.strip(), content, flags=re.DOTALL)
    
    with open(filename, 'w') as f:
        f.write(content)
    
    print(f"✅ Fixed {filename}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        filename = sys.argv[1]
    else:
        filename = "test_agent_tracing.py"
    
    fix_file(filename)
