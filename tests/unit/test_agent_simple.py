#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Simple Agent Test Script

This script provides a simple way to test the agent and LangSmith integration without
complex performance analysis. It's more lightweight and has fewer dependencies.
"""

import os
import sys
import time
import traceback
from datetime import datetime

# Try to set up LangSmith environment
has_langsmith = False
try:
    # Check for either LANGSMITH_API_KEY (newer) or LANGCHAIN_API_KEY (older)
    langsmith_api_key = os.environ.get("LANGSMITH_API_KEY") or os.environ.get("LANGCHAIN_API_KEY")
    if langsmith_api_key:
        # Set project name
        project_name = os.environ.get("LANGCHAIN_PROJECT", "navegador-testing")
        os.environ["LANGCHAIN_PROJECT"] = project_name
        # Enable tracing
        os.environ["LANGCHAIN_TRACING_V2"] = "true"
        has_langsmith = True
        print(f"✅ LangSmith tracing enabled with project: {project_name}")
    else:
        print("⚠️ No LangSmith API key found. Please set LANGSMITH_API_KEY environment variable.")
        print("   You can get a key at https://smith.langchain.com/settings/api-keys")
except Exception as e:
    print(f"⚠️ Error setting up LangSmith: {e}")

# Test queries to run
DEFAULT_QUERIES = [
    "¿Qué opinan los mexicanos sobre la salud?",
    "Show me data about identity and values",
    "Analiza los datos sobre educación"
]

def run_test_query(query, agent_instance=None):
    """Run a single test query through the agent"""
    print(f"\n{'=' * 80}")
    print(f"🔍 Testing query: '{query}'")
    print(f"{'=' * 80}")
    
    # Try to get the agent if not provided
    if agent_instance is None:
        try:
            # Import agent module
            sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
            import agent
            if hasattr(agent, "get_agent"):
                agent_instance = agent.get_agent(persistence=True)
            elif hasattr(agent, "create_agent"):
                agent_instance = agent.create_agent()
            else:
                print("❌ Could not find agent creation function")
                return
        except Exception as e:
            print(f"❌ Error importing agent module: {e}")
            traceback.print_exc()
            return
    
    # Try to create agent config with LangSmith tracing
    thread_id = f"test_{int(time.time())}"
    config = None
    try:
        from dashboard import create_agent_config
        config = create_agent_config(thread_id)
        print("✅ Using create_agent_config from dashboard")
    except Exception:
        # Create a basic config
        config = {
            "configurable": {
                "thread_id": thread_id,
                "metadata": {
                    "test": True,
                    "timestamp": datetime.now().isoformat()
                }
            }
        }
        print("⚠️ Using fallback config (create_agent_config not found)")
    
    # Create a basic agent state
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
    
    # Try to use state_normalizer if available
    try:
        import state_normalizer
        if hasattr(state_normalizer, "create_agent_state"):
            state = state_normalizer.create_agent_state(
                user_message=query,
                intent="query_variable_database",
                dataset=["ALL"],
                selected_variables=[],
                language="es"
            )
            print("✅ Using state_normalizer")
    except Exception:
        print("⚠️ Using fallback state (state_normalizer not found)")
    
    # Run the query
    try:
        print(f"🕒 Starting at: {datetime.now().strftime('%H:%M:%S.%f')}")
        start_time = time.time()
        
        # Invoke the agent
        response = agent_instance.invoke(state, config=config)
        
        elapsed_time = time.time() - start_time
        print(f"✅ Response received after {elapsed_time:.2f} seconds")
        print(f"🕒 Completed at: {datetime.now().strftime('%H:%M:%S.%f')}")
        
        # Process response
        print("\n📋 Response analysis:")
        if isinstance(response, dict):
            # Check for path information
            if "path" in response:
                path = response.get("path", [])
                print(f"🛣️ Path taken: {' -> '.join(path)}")
            
            # Check for selected variables
            if "selected_variables" in response:
                variables = response["selected_variables"]
                print(f"📊 Selected {len(variables)} variables")
                
                # Show first few variables
                for i, var in enumerate(variables[:5]):
                    print(f"  • {var}")
                if len(variables) > 5:
                    print(f"  • ...and {len(variables) - 5} more")
            
            # Extract content from messages if available
            if "messages" in response and response["messages"]:
                messages = response["messages"]
                last_message = messages[-1]
                
                # Get content based on message type
                if isinstance(last_message, dict):
                    content = last_message.get("content", "")
                else:
                    content = getattr(last_message, "content", str(last_message))
                
                # Show a summary of the content
                content_summary = content[:200] + "..." if len(content) > 200 else content
                print(f"\n💬 Response content preview:\n{content_summary}")
        
        return response
    
    except Exception as e:
        print(f"❌ Error running query: {e}")
        traceback.print_exc()
        return None

def main():
    """Run test queries through the agent"""
    # Parse command line arguments
    queries = sys.argv[1:] if len(sys.argv) > 1 else DEFAULT_QUERIES
    
    print("\n" + "=" * 80)
    print("🤖 AGENT TESTING WITH LANGSMITH TRACING")
    print("=" * 80)
    
    # Check LangSmith setup
    if has_langsmith:
        print("✅ LangSmith tracing is enabled")
    else:
        print("⚠️ LangSmith tracing is NOT enabled")
    
    # Initialize agent once for all queries
    agent_instance = None
    try:
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        import agent
        if hasattr(agent, "get_agent"):
            print("🔄 Initializing agent...")
            start_time = time.time()
            agent_instance = agent.get_agent(persistence=True)
            print(f"✅ Agent initialized in {time.time() - start_time:.2f} seconds")
        elif hasattr(agent, "create_agent"):
            print("🔄 Initializing agent...")
            start_time = time.time()
            agent_instance = agent.create_agent()
            print(f"✅ Agent initialized in {time.time() - start_time:.2f} seconds")
    except Exception as e:
        print(f"⚠️ Could not initialize agent: {e}")
        # We'll try to initialize it in each query
    
    # Run queries
    results = []
    for i, query in enumerate(queries):
        print(f"\n[{i+1}/{len(queries)}] Testing query: '{query}'")
        result = run_test_query(query, agent_instance)
        results.append((query, result))
    
    # Print summary
    print("\n" + "=" * 80)
    print("📊 TEST SUMMARY")
    print("=" * 80)
    
    success_count = sum(1 for _, result in results if result is not None)
    print(f"✅ Successful queries: {success_count}/{len(results)}")
    
    # Print LangSmith URL if available
    if has_langsmith:
        project = os.environ.get("LANGCHAIN_PROJECT", "navegador-testing")
        print(f"🔗 View traces in LangSmith: https://smith.langchain.com/projects/{project}/runs")

if __name__ == "__main__":
    main()
