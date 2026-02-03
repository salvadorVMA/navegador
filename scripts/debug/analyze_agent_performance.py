#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Agent Performance Analysis Tool

This script focuses on analyzing the specific performance bottlenecks in the agent's workflow,
with detailed timing for each component and comparison with expected durations.
"""

import os
import sys
import time
import json
import argparse
from datetime import datetime
from typing import Dict, Any, List, Optional
import traceback
import threading
import pprint

# First, check if we can import the required modules
try:
    import langsmith
    from langchain.schema.runnable import RunnableConfig
    has_langsmith = True
except ImportError:
    has_langsmith = False
    print("⚠️ LangSmith modules not available. Limited functionality will be used.")

# Import our own modules - with better error handling for each module
has_agent = False
has_state_normalizer = False
has_variable_selector = False
has_dashboard = False

# Add the current directory to the path to make imports work
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Try to import agent module
try:
    import agent
    has_agent = True
except ImportError as e:
    print(f"⚠️ Could not import agent module: {e}")

# Try to import state_normalizer
try:
    import state_normalizer
    has_state_normalizer = True
except ImportError as e:
    print(f"⚠️ Could not import state_normalizer module: {e}")

# Try to import dashboard functions
try:
    from dashboard import create_agent_config
    has_dashboard = True
except ImportError as e:
    print(f"⚠️ Could not import dashboard functions: {e}")

# Try to import variable_selector
try:
    import variable_selector
    has_variable_selector = True
except ImportError as e:
    print(f"⚠️ Could not import variable_selector module: {e}")

# Print overall import status
if has_agent and has_state_normalizer and has_dashboard:
    print("✅ Successfully imported all core modules")
else:
    print("⚠️ Some modules could not be imported. Functionality will be limited.")

# Constants for performance analysis
EXPECTED_TIMINGS = {
    "intent_detection": 1.0,      # Expected time for intent detection in seconds
    "variable_selection": 5.0,    # Expected time for variable selection in seconds
    "retrieval": 1.0,             # Expected time for retrieval in seconds
    "grading": 10.0,              # Expected time for grading in seconds
    "analysis": 5.0,              # Expected time for analysis in seconds
    "response_generation": 3.0,   # Expected time for response generation in seconds
}

# Define colors for console output
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'

def colorize(text, color):
    """Add color to text for console output"""
    return f"{color}{text}{Colors.END}"

class TimedContext:
    """Context manager for timing operations"""
    
    def __init__(self, name, expected_time=None, threshold_factor=2.0, parent=None):
        """Initialize with operation name and expected time"""
        self.name = name
        self.expected_time = expected_time  # Expected time in seconds
        self.threshold_factor = threshold_factor  # Multiplier for expected time to mark as slow
        self.parent = parent
        self.start_time = None
        self.end_time = None
        self.duration = None
        self.metadata = {}
        self.sub_operations = []
    
    def __enter__(self):
        """Start timing"""
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """End timing and calculate duration"""
        self.end_time = time.time()
        if self.start_time is not None:
            self.duration = self.end_time - self.start_time
        else:
            self.duration = 0
        
        # Check if operation is slow
        is_slow = False
        if self.expected_time:
            is_slow = self.duration > (self.expected_time * self.threshold_factor)
        
        # Format status message
        if exc_type:
            status = colorize("ERROR", Colors.RED)
            message = str(exc_val)
        elif is_slow:
            status = colorize("SLOW", Colors.YELLOW)
            message = f"{self.duration:.2f}s (expected < {self.expected_time:.2f}s)"
        else:
            status = colorize("OK", Colors.GREEN)
            message = f"{self.duration:.2f}s"
        
        # Print status message
        indent = "  " * self._get_depth()
        operation_name = colorize(self.name, Colors.BOLD)
        print(f"{indent}🕒 {operation_name}: {status} - {message}")
        
        # If it's slow and a root operation, suggest improvements
        if is_slow and not self.parent:
            self._suggest_improvements()
        
        # Add to parent's sub-operations
        if self.parent:
            self.parent.sub_operations.append(self)
    
    def _get_depth(self):
        """Get the depth of this operation in the hierarchy"""
        depth = 0
        parent = self.parent
        while parent:
            depth += 1
            parent = parent.parent
        return depth
    
    def add_metadata(self, key, value):
        """Add metadata to the operation"""
        self.metadata[key] = value
    
    def _suggest_improvements(self):
        """Suggest improvements for slow operations"""
        if self.name == "variable_selection":
            print(colorize("  💡 Suggestion: Variable selection is slow. Consider:", Colors.CYAN))
            print("     - Optimizing the ChromaDB query filtering")
            print("     - Reducing batch size for grading")
            print("     - Caching common query results")
        elif self.name == "grading":
            print(colorize("  💡 Suggestion: Grading is slow. Consider:", Colors.CYAN))
            print("     - Using a smaller model for initial filtering")
            print("     - Implementing parallel processing for grading")
            print("     - Pre-filtering variables before expensive grading")
        elif self.name == "retrieval":
            print(colorize("  💡 Suggestion: Retrieval is slow. Consider:", Colors.CYAN))
            print("     - Optimizing the ChromaDB index")
            print("     - Adding more specific filtering by metadata")
            print("     - Using approximate nearest neighbors")

class AgentPerformanceAnalyzer:
    """Analyze the performance of the agent"""
    
    def __init__(self, verbose=True):
        """Initialize the analyzer"""
        self.agent_instance = None
        self.verbose = verbose
        self.langsmith_available = has_langsmith
        self.runs = []
        self.current_run = {}
        self.timing_data = {}
        
        # Initialize the agent
        self._initialize_agent()
    
    def _initialize_agent(self):
        """Initialize the agent from the agent module"""
        if not has_agent:
            print("⚠️ Agent module not available. Cannot initialize agent.")
            return
        
        try:
            print("🔄 Initializing agent...")
            start_time = time.time()
            
            # Check if the get_agent function exists in the agent module
            if hasattr(agent, "get_agent"):
                self.agent_instance = agent.get_agent(persistence=True)
            elif hasattr(agent, "create_agent"):
                self.agent_instance = agent.create_agent(persistence=True)
            elif hasattr(agent, "get_navigator_agent"):
                self.agent_instance = agent.get_navigator_agent(persistence=True)
            else:
                print("⚠️ Could not find get_agent or create_agent function in agent module")
                return
            
            elapsed = time.time() - start_time
            print(f"✅ Agent initialized in {elapsed:.2f} seconds")
        except Exception as e:
            print(f"❌ Error initializing agent: {e}")
            traceback.print_exc()
            self.agent_instance = None
    
    def analyze_query(self, query, language="es", datasets=None, detailed=True):
        """Analyze the performance of a single query"""
        if not self.agent_instance:
            print("❌ Agent not initialized. Cannot analyze query.")
            return None
        
        print("\n" + "=" * 80)
        print(colorize(f"📊 PERFORMANCE ANALYSIS: '{query}'", Colors.HEADER + Colors.BOLD))
        print("=" * 80)
        
        thread_id = f"perf_{int(time.time())}"
        
        # Create the agent state
        try:
            # Use state_normalizer when available
            try:
                with TimedContext("state_creation", expected_time=0.2) as ctx:
                    agent_state = state_normalizer.create_agent_state(
                        user_message=query,
                        intent="query_variable_database",
                        dataset=datasets or ["ALL"],
                        selected_variables=[],
                        language=language
                    )
                    ctx.add_metadata("state_size", len(str(agent_state)))
            except Exception as e:
                print(f"⚠️ Error using state_normalizer: {e}")
                # Fallback to manual creation
                agent_state = {
                    "messages": [{"role": "user", "content": query}],
                    "intent": "query_variable_database",
                    "user_query": query,
                    "original_query": query,
                    "dataset": datasets or ["ALL"],
                    "selected_variables": [],
                    "analysis_type": "descriptive",
                    "user_approved": False,
                    "analysis_result": {},
                    "language": language
                }
            
            # Create a special config with tracing enabled
            agent_config = self._create_analysis_config(thread_id)
            
            # Add background monitoring if detailed analysis is requested
            monitor_thread = None
            monitor_data = {"running": True, "data": {}}
            if detailed:
                monitor_thread = threading.Thread(
                    target=self._monitor_resources, 
                    args=(monitor_data,)
                )
                monitor_thread.daemon = True
                monitor_thread.start()
            
            # Invoke the agent with timing
            with TimedContext("agent_invoke", expected_time=30.0) as parent_ctx:
                # Track the start time for overall timing
                overall_start = time.time()
                
                # Invoke the agent
                agent_response = self.agent_instance.invoke(agent_state, config=agent_config)
                
                # Calculate overall duration
                overall_duration = time.time() - overall_start
                parent_ctx.add_metadata("total_time", overall_duration)
            
            # Stop the monitoring thread
            if detailed and monitor_thread:
                monitor_data["running"] = False
                monitor_thread.join(timeout=1.0)
            
            # Process the response
            self._analyze_response(agent_response, query, overall_duration)
            
            # Return the agent response for further analysis
            return agent_response
            
        except Exception as e:
            print(f"❌ Error analyzing query: {e}")
            traceback.print_exc()
            return None
    
    def _create_analysis_config(self, thread_id):
        """Create a special config for performance analysis"""
        # Create base config
        if has_dashboard and 'create_agent_config' in globals():
            try:
                base_config = create_agent_config(thread_id)
            except Exception as e:
                print(f"⚠️ Error using create_agent_config: {e}")
                # Fallback to basic config
                base_config = {
                    "configurable": {
                        "thread_id": thread_id,
                        "metadata": {}
                    }
                }
        else:
            # Create a simple config if dashboard function isn't available
            base_config = {
                "configurable": {
                    "thread_id": thread_id,
                    "metadata": {}
                }
            }
        
        # Add performance analysis metadata
        if hasattr(base_config, "configurable"):
            # It's a RunnableConfig
            configurable = base_config.configurable
        else:
            # It's a dict
            configurable = base_config.get("configurable", {})
        
        # Add metadata for tracking
        configurable.update({
            "metadata": {
                "performance_analysis": True,
                "timestamp": datetime.now().isoformat(),
                "thread_id": thread_id
            }
        })
        
        # Return as RunnableConfig if langchain is available
        try:
            from langchain.schema.runnable import RunnableConfig
            return RunnableConfig(configurable=configurable)
        except ImportError:
            return {"configurable": configurable}
    
    def _monitor_resources(self, shared_data):
        """Monitor system resources during agent execution"""
        try:
            import psutil
        except ImportError:
            print("⚠️ psutil not available, cannot monitor system resources")
            return
        
        # Initialize data
        process = psutil.Process(os.getpid())
        measurements = []
        start_time = time.time()
        
        # Collect data every 0.5 seconds
        while shared_data["running"]:
            try:
                cpu_percent = process.cpu_percent(interval=0.5)
                memory_info = process.memory_info()
                
                measurements.append({
                    "timestamp": time.time() - start_time,
                    "cpu_percent": cpu_percent,
                    "memory_rss": memory_info.rss / (1024 * 1024),  # MB
                    "memory_vms": memory_info.vms / (1024 * 1024)   # MB
                })
            except:
                # Ignore errors during measurement
                pass
            
            # Don't measure too frequently
            time.sleep(0.5)
        
        # Store measurements in shared data
        shared_data["data"]["measurements"] = measurements
        
        # Calculate statistics
        if measurements:
            shared_data["data"]["avg_cpu"] = sum(m["cpu_percent"] for m in measurements) / len(measurements)
            shared_data["data"]["max_cpu"] = max(m["cpu_percent"] for m in measurements)
            shared_data["data"]["avg_memory"] = sum(m["memory_rss"] for m in measurements) / len(measurements)
            shared_data["data"]["max_memory"] = max(m["memory_rss"] for m in measurements)
            
            print(f"\n📊 Resource Usage:")
            print(f"  • Average CPU: {shared_data['data']['avg_cpu']:.1f}%")
            print(f"  • Maximum CPU: {shared_data['data']['max_cpu']:.1f}%")
            print(f"  • Average Memory: {shared_data['data']['avg_memory']:.1f} MB")
            print(f"  • Maximum Memory: {shared_data['data']['max_memory']:.1f} MB")
    
    def _analyze_response(self, agent_response, query, duration):
        """Analyze the agent response for performance insights"""
        print("\n📋 Response Analysis:")
        
        # Check if we have a valid response
        if not agent_response:
            print("❌ No response received from agent")
            return
        
        # Extract and analyze paths
        if isinstance(agent_response, dict) and "path" in agent_response:
            path = agent_response.get("path", [])
            print(f"🛣️ Path taken: {' → '.join(path)}")
            
            # Check if we're using the variable selection path
            if "detect_intent" in path and "handle_query" in path:
                print(f"✅ Standard variable selection path detected")
                
                # Extract analytics if available
                if "analytics" in agent_response:
                    analytics = agent_response.get("analytics", {})
                    
                    # Print timings for different stages
                    if "variable_selection_time" in analytics:
                        var_time = analytics["variable_selection_time"]
                        var_percent = (var_time / duration) * 100 if duration else 0
                        print(f"⏱️ Variable selection: {var_time:.2f}s ({var_percent:.1f}% of total)")
                        
                        # Flag if variable selection is taking too long
                        if var_time > EXPECTED_TIMINGS["variable_selection"] * 2:
                            print(colorize("  ⚠️ Variable selection is unusually slow!", Colors.YELLOW))
                    
                    # Print other analytics
                    if "total_variables_retrieved" in analytics:
                        print(f"📊 Variables retrieved: {analytics['total_variables_retrieved']}")
                    if "selected_variables_count" in analytics:
                        print(f"📊 Variables selected: {analytics['selected_variables_count']}")
        
        # Check if we have selected variables
        if isinstance(agent_response, dict) and "selected_variables" in agent_response:
            variables = agent_response["selected_variables"]
            print(f"📋 Selected {len(variables)} variables")
            
            # Print first few variables
            if variables:
                for i, var in enumerate(variables[:5]):
                    print(f"  • {var}")
                if len(variables) > 5:
                    print(f"  • ...and {len(variables) - 5} more")
        
        # Performance suggestion based on total time
        print(f"\n⏱️ Total processing time: {duration:.2f} seconds")
        if duration > 30.0:
            print(colorize("  ⚠️ Query processing is very slow!", Colors.YELLOW))
            print(colorize("  💡 Possible optimizations:", Colors.CYAN))
            print("     - Check variable selection process for bottlenecks")
            print("     - Consider using a more efficient retrieval strategy")
            print("     - Check if external API calls are causing delays")
            print("     - Consider implementing caching for similar queries")
        elif duration > 15.0:
            print(colorize("  ⚠️ Query processing is somewhat slow", Colors.YELLOW))
            print(colorize("  💡 Consider implementing caching for faster responses", Colors.CYAN))
        else:
            print(colorize("  ✅ Query processing time is acceptable", Colors.GREEN))
    
    def analyze_variable_selection(self, query, language="es", datasets=None):
        """Specifically analyze the variable selection component"""
        # Check if we can access the variable selection functionality
        has_select_variables = False
        select_variables_func = None
        documents_query_func = None
        
        print("\n" + "=" * 80)
        print(colorize(f"🔍 VARIABLE SELECTION ANALYSIS: '{query}'", Colors.HEADER + Colors.BOLD))
        print("=" * 80)
        
        # Try to locate the select_variables function
        try:
            if has_agent and hasattr(agent, "select_variables"):
                select_variables_func = agent.select_variables
                has_select_variables = True
            else:
                # Look for it in other likely places
                print("⚠️ select_variables not found in agent module, checking alternatives...")
                
                # Try variable_selector module if available
                if has_variable_selector and hasattr(variable_selector, "select_variables"):
                    select_variables_func = variable_selector.select_variables
                    has_select_variables = True
                elif has_variable_selector and hasattr(variable_selector, "select_variables_for_query"):
                    select_variables_func = variable_selector.select_variables_for_query
                    has_select_variables = True
        except Exception as e:
            print(f"⚠️ Could not locate select_variables function: {e}")
        
        # Try to locate the get_documents_for_query function
        try:
            if has_variable_selector and hasattr(variable_selector, "get_documents_for_query"):
                documents_query_func = variable_selector.get_documents_for_query
            elif has_variable_selector and hasattr(variable_selector, "retrieve_documents"):
                documents_query_func = variable_selector.retrieve_documents
        except Exception as e:
            print(f"⚠️ Could not locate document retrieval function: {e}")
        
        if not has_select_variables:
            print("❌ Could not find variable selection function. Analysis aborted.")
            return
        
        try:
            # Create a root timing context
            with TimedContext("variable_selection", expected_time=EXPECTED_TIMINGS["variable_selection"]) as ctx:
                # Track the query embedding time
                with TimedContext("query_embedding", expected_time=0.5, parent=ctx) as embed_ctx:
                    # Embedding happens in get_documents_for_query
                    pass  # The timing will be captured in the retrieval step
                
                # Track the retrieval time if we have access to the retrieval function
                if documents_query_func:
                    with TimedContext("retrieval", expected_time=EXPECTED_TIMINGS["retrieval"], parent=ctx) as retrieval_ctx:
                        # This will capture the ChromaDB query time
                        try:
                            print("🔍 Running retrieval test...")
                            # Run retrieval directly
                            try:
                                results = documents_query_func(
                                    query, 
                                    topics=datasets or ["ALL"],
                                    return_all_types=True
                                )
                            except TypeError:
                                # Try alternative argument format
                                results = documents_query_func(
                                    query, 
                                    datasets or ["ALL"],
                                    True
                                )
                            
                            # Save metadata about retrieval
                            if results:
                                retrieval_ctx.add_metadata("result_count", len(results))
                                retrieval_ctx.add_metadata("topics", datasets or ["ALL"])
                        except Exception as e:
                            print(f"❌ Error in retrieval: {e}")
                else:
                    print("⚠️ Document retrieval function not found, skipping retrieval analysis")
                
                # Track the variable selection time (includes grading)
                with TimedContext("variable_selection_complete", expected_time=EXPECTED_TIMINGS["grading"], parent=ctx) as grading_ctx:
                    # Run variable selection 
                    print("🔍 Running variable selection with grading...")
                    
                    # Call the variable selection function with appropriate parameters
                    try:
                        selected_vars = select_variables_func(query, datasets or ["ALL"], language)
                    except TypeError:
                        # Try with just the query
                        try:
                            selected_vars = select_variables_func(query)
                        except Exception as e:
                            print(f"❌ Error calling select_variables with reduced parameters: {e}")
                            selected_vars = []
                    
                    # Save metadata
                    if selected_vars:
                        grading_ctx.add_metadata("selected_count", len(selected_vars))
                        
                        # Print the selected variables
                        print(f"\n📋 Selected {len(selected_vars)} variables:")
                        for i, var in enumerate(selected_vars[:5]):
                            print(f"  • {var}")
                        if len(selected_vars) > 5:
                            print(f"  • ...and {len(selected_vars) - 5} more")
        
        except Exception as e:
            print(f"❌ Error in variable selection analysis: {e}")
            traceback.print_exc()
    
    def generate_optimization_report(self):
        """Generate a detailed optimization report based on all analyses"""
        if not self.runs:
            print("❌ No runs recorded. Cannot generate optimization report.")
            return
        
        print("\n" + "=" * 80)
        print(colorize(f"📈 OPTIMIZATION OPPORTUNITIES", Colors.HEADER + Colors.BOLD))
        print("=" * 80)
        
        # Calculate overall statistics
        avg_duration = sum(run.get("duration", 0) for run in self.runs) / len(self.runs)
        
        print(f"Based on {len(self.runs)} analyzed queries (avg {avg_duration:.2f}s):")
        
        # Check if variable selection is a bottleneck
        var_times = [run.get("analytics", {}).get("variable_selection_time", 0) for run in self.runs]
        if var_times:
            avg_var_time = sum(var_times) / len(var_times)
            var_percent = (avg_var_time / avg_duration) * 100 if avg_duration else 0
            
            if var_percent > 70:
                print(colorize("\n🔴 HIGH PRIORITY: Variable Selection Optimization", Colors.RED + Colors.BOLD))
                print(f"Variable selection takes {avg_var_time:.2f}s on average ({var_percent:.1f}% of total time)")
                print("Recommendations:")
                print("1. Implement caching for similar queries")
                print("2. Use a smaller model for initial variable filtering")
                print("3. Optimize ChromaDB queries with better filtering")
                print("4. Consider using parallel processing for grading")
            elif var_percent > 40:
                print(colorize("\n🟠 MEDIUM PRIORITY: Variable Selection Improvement", Colors.YELLOW + Colors.BOLD))
                print(f"Variable selection takes {avg_var_time:.2f}s on average ({var_percent:.1f}% of total time)")
                print("Recommendations:")
                print("1. Pre-filter variables before expensive grading")
                print("2. Consider batch processing for similar queries")
        
        # Check if retrieval is a bottleneck
        if any("retrieval_time" in run.get("analytics", {}) for run in self.runs):
            retrieval_times = [run.get("analytics", {}).get("retrieval_time", 0) for run in self.runs 
                               if "retrieval_time" in run.get("analytics", {})]
            if retrieval_times:
                avg_retrieval = sum(retrieval_times) / len(retrieval_times)
                if avg_retrieval > EXPECTED_TIMINGS["retrieval"]:
                    print(colorize("\n🟠 MEDIUM PRIORITY: Retrieval Optimization", Colors.YELLOW + Colors.BOLD))
                    print(f"Retrieval takes {avg_retrieval:.2f}s on average")
                    print("Recommendations:")
                    print("1. Optimize ChromaDB index settings")
                    print("2. Add more specific metadata filtering")
                    print("3. Consider using approximate nearest neighbors")
        
        # Provide general performance recommendations
        print(colorize("\n🟢 GENERAL RECOMMENDATIONS", Colors.GREEN + Colors.BOLD))
        print("1. Add more detailed logging to identify specific bottlenecks")
        print("2. Use LangSmith to trace specific operations in detail")
        print("3. Implement progress indicators for long-running operations")
        print("4. Consider implementing an asynchronous API for better UI responsiveness")

def main():
    """Main function for the performance analyzer"""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Agent Performance Analysis Tool")
    parser.add_argument("query", nargs="?", help="Query to analyze")
    parser.add_argument("--queries", "-q", help="Run multiple queries separated by commas")
    parser.add_argument("--datasets", "-d", help="Datasets to use, comma-separated")
    parser.add_argument("--language", "-l", default="es", help="Language to use (default: es)")
    parser.add_argument("--varselect", "-v", action="store_true", help="Specifically analyze variable selection")
    parser.add_argument("--detailed", action="store_true", help="Run detailed analysis with resource monitoring")
    args = parser.parse_args()
    
    # Print header
    print("\n" + "=" * 80)
    print(colorize("🔍 AGENT PERFORMANCE ANALYSIS", Colors.HEADER + Colors.BOLD))
    print("=" * 80)
    
    # Create analyzer
    analyzer = AgentPerformanceAnalyzer()
    
    # Process datasets
    datasets = args.datasets.split(",") if args.datasets else None
    
    # Run the appropriate analysis
    if args.varselect:
        # Run variable selection analysis
        if args.query:
            analyzer.analyze_variable_selection(args.query, args.language, datasets)
        elif args.queries:
            for query in args.queries.split(","):
                analyzer.analyze_variable_selection(query.strip(), args.language, datasets)
        else:
            print("❌ No query provided. Please specify a query with --query.")
    else:
        # Run full agent analysis
        if args.query:
            analyzer.analyze_query(args.query, args.language, datasets, args.detailed)
        elif args.queries:
            for query in args.queries.split(","):
                analyzer.analyze_query(query.strip(), args.language, datasets, args.detailed)
        else:
            print("❌ No query provided. Please specify a query with --query.")
    
    # Generate optimization report
    analyzer.generate_optimization_report()

if __name__ == "__main__":
    main()
