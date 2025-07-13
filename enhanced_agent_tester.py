#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Enhanced testing script for agent with LangSmith tracing
This script provides an expanded testing framework with the following features:
- Customizable test queries
- Conversation history testing
- Performance metrics
- LangSmith integration (if available)
"""

import os
import sys
import time
import json
import uuid
import traceback
import argparse
from datetime import datetime
from typing import Dict, List, Any, Optional, Union

# Set up path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Initialize logging
LOG_FILE = "agent_test_results.log"
log_file = open(LOG_FILE, "w", encoding="utf-8")

def log(message):
    """Log message to both console and file"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    formatted_message = f"[{timestamp}] {message}"
    print(formatted_message)
    log_file.write(f"{formatted_message}\n")
    log_file.flush()

class AgentTester:
    """Class for testing the agent system with tracing and metrics"""
    
    def __init__(self, project_name="navegador-test", verbose=False):
        self.project_name = project_name
        self.verbose = verbose
        self.agent = None
        self.langsmith_client = None
        self.tracer = None
        self.callbacks = []
        
        # Initialize components
        self._initialize_tracing()
        self._initialize_agent()
        
    def _initialize_tracing(self):
        """Initialize LangSmith tracing if available"""
        # Try importing tracing components
        try:
            from langsmith.client import Client as LangSmithClient
            from langchain_core.tracers import LangChainTracer
            
            # Enable LangSmith tracing if API key is available
            os.environ["LANGSMITH_TRACING"] = "true"
            
            # Get LangSmith configuration
            api_key = os.getenv("LANGSMITH_API_KEY")
            
            if not api_key:
                log("⚠️ LANGSMITH_API_KEY not set - tracing will be disabled")
                return
                
            try:
                # Initialize client and tracer
                self.langsmith_client = LangSmithClient(api_key=api_key)
                self.tracer = LangChainTracer(project_name=self.project_name)
                self.callbacks = [self.tracer]
                
                # Enable tracing v2
                os.environ["LANGCHAIN_TRACING_V2"] = "true"
                log(f"✅ LangSmith monitoring initialized for project: {self.project_name}")
            except Exception as e:
                log(f"❌ Error initializing LangSmith client: {e}")
        except ImportError:
            log("⚠️ LangSmith packages not available - tracing will be disabled")
    
    def _initialize_agent(self):
        """Initialize agent instance"""
        try:
            import agent
            if self.verbose:
                log(f"Agent module imported.")
            
            # Create agent instance
            log("Creating agent instance with persistence enabled...")
            self.agent = agent.create_agent(enable_persistence=True)
            log("✅ Agent instance created successfully")
        except Exception as e:
            log(f"❌ Error initializing agent: {e}")
            log(traceback.format_exc())
    
    def create_thread_config(self, thread_id):
        """Create a thread configuration for the agent"""
        # Try importing RunnableConfig
        try:
            from langchain_core.runnables.config import RunnableConfig
            return RunnableConfig(
                configurable={
                    "thread_id": thread_id,
                    "callbacks": self.callbacks
                }
            )
        except ImportError:
            # Fallback to dict if RunnableConfig not available
            return {
                "configurable": {
                    "thread_id": thread_id,
                    "callbacks": self.callbacks
                }
            }
    
    def process_response(self, response):
        """Process and format agent response"""
        try:
            # Extract the last message if it's a list of messages
            if isinstance(response, dict) and "messages" in response:
                messages = response["messages"]
                if messages and len(messages) > 0:
                    last_message = messages[-1]
                    if hasattr(last_message, "content"):
                        return last_message.content
                    elif isinstance(last_message, dict) and "content" in last_message:
                        return last_message["content"]
            
            # If it's a simple response with content
            if isinstance(response, dict) and "content" in response:
                return response["content"]
                
            # Fall back to string representation
            return str(response)
        except Exception as e:
            log(f"Error processing response: {e}")
            return str(response)
    
    def run_single_query(self, query, thread_id=None, dataset=None, intent=None):
        """Run a single query against the agent"""
        if not self.agent:
            log("❌ Agent not initialized")
            return None
            
        # Create a thread ID if not provided
        if not thread_id:
            thread_id = f"test_{uuid.uuid4().hex[:8]}"
        
        # Set defaults
        if not dataset:
            dataset = ["ALL"]
        if not intent:
            intent = "continue_conversation"
            
        log(f"Testing query with thread_id {thread_id}: '{query}'")
        
        # Set up thread config
        config = self.create_thread_config(thread_id)
        
        # Create input state
        input_state = {
            "messages": [{"type": "human", "content": query}],
            "metadata": {
                "language": "en",
                "dataset": dataset,
                "intent": intent
            }
        }
        
        # Initialize timing
        start_time = time.time()
        
        try:
            # Invoke agent
            response = self.agent.invoke(input_state, config=config)
            end_time = time.time()
            response_time = end_time - start_time
            
            # Process response
            formatted_response = self.process_response(response)
            log(f"✅ Response received in {response_time:.2f}s")
            
            if self.verbose:
                log(f"Response content: {formatted_response}")
            
            return {
                "thread_id": thread_id,
                "query": query,
                "response": response,
                "formatted_response": formatted_response,
                "response_time": response_time,
                "success": True
            }
        except Exception as e:
            end_time = time.time()
            response_time = end_time - start_time
            log(f"❌ Error invoking agent: {e}")
            log(traceback.format_exc())
            return {
                "thread_id": thread_id,
                "query": query,
                "response": None,
                "formatted_response": f"Error: {str(e)}",
                "response_time": response_time,
                "success": False,
                "error": str(e)
            }
    
    def run_conversation(self, queries, thread_id=None, dataset=None):
        """Run a multi-turn conversation with the agent"""
        if not thread_id:
            thread_id = f"conv_{uuid.uuid4().hex[:8]}"
            
        log(f"Starting conversation test with thread_id {thread_id}")
        
        results = []
        for i, query in enumerate(queries):
            log(f"Turn {i+1}/{len(queries)}")
            result = self.run_single_query(query, thread_id, dataset)
            if result is not None:
                results.append(result)
            else:
                log("❌ Query failed with None result")
                continue
                
            # Add a small delay between turns to avoid rate limits
            if i < len(queries) - 1:
                time.sleep(0.5)
        
        # Calculate conversation metrics if we have results
        if results:
            success_rate = sum(1 for r in results if r["success"]) / len(results)
            avg_response_time = sum(r["response_time"] for r in results) / len(results)
            
            log(f"Conversation test completed: {success_rate*100:.1f}% success rate, {avg_response_time:.2f}s avg response time")
            
            return {
                "thread_id": thread_id,
                "turns": len(results),
                "results": results,
                "success_rate": success_rate,
                "avg_response_time": avg_response_time
            }
        else:
            log("❌ Conversation test failed: no valid responses")
            return {
                "thread_id": thread_id,
                "turns": 0,
                "results": [],
                "success_rate": 0,
                "avg_response_time": 0
            }
    
    def run_test_suite(self, test_cases=None):
        """Run a suite of predefined test cases"""
        if test_cases is None:
            # Default test cases
            test_cases = [
                {"query": "Tell me about this dataset", "expected_intent": "answer_general_questions"},
                {"query": "What variables can I analyze?", "expected_intent": "query_variable_database"},
                {"query": "I want to analyze education data", "expected_intent": "select_analysis_type"},
                {"query": "Run a descriptive analysis", "expected_intent": "confirm_and_run"}
            ]
        
        log(f"Running test suite with {len(test_cases)} test cases")
        
        results = []
        for i, test_case in enumerate(test_cases):
            query = test_case["query"]
            expected_intent = test_case.get("expected_intent")
            
            log(f"Test case {i+1}/{len(test_cases)}: '{query}'")
            result = self.run_single_query(query)
            
            if result is None:
                log("❌ Test case failed with None result")
                continue
                
            # Check if intent matched expected
            intent_matched = None
            try:
                if result["response"] and isinstance(result["response"], dict):
                    actual_intent = result["response"].get("intent")
                    intent_matched = actual_intent == expected_intent if expected_intent and actual_intent else None
                    
                    if expected_intent and self.verbose:
                        log(f"Intent check: expected={expected_intent}, actual={actual_intent}, matched={intent_matched}")
            except (KeyError, AttributeError):
                if self.verbose:
                    log("Could not extract intent from response")
                
            results.append({
                "test_case": test_case,
                "result": result,
                "intent_matched": intent_matched
            })
            
            # Add delay between tests
            if i < len(test_cases) - 1:
                time.sleep(1)
        
        # Calculate metrics if we have results
        if results:
            success_rate = sum(1 for r in results if r["result"]["success"]) / len(results)
            intent_matches = [r for r in results if r["intent_matched"] is True]
            intent_tests = [r for r in results if r["intent_matched"] is not None]
            intent_match_rate = len(intent_matches) / len(intent_tests) if intent_tests else None
            avg_response_time = sum(r["result"]["response_time"] for r in results) / len(results)
            
            log(f"Test suite completed:")
            log(f"- Success rate: {success_rate*100:.1f}%")
            if intent_match_rate is not None:
                log(f"- Intent match rate: {intent_match_rate*100:.1f}%")
            log(f"- Avg response time: {avg_response_time:.2f}s")
            
            return {
                "test_cases": len(results),
                "results": results,
                "success_rate": success_rate,
                "intent_match_rate": intent_match_rate,
                "avg_response_time": avg_response_time
            }
        else:
            log("❌ Test suite failed: no valid test results")
            return {
                "test_cases": 0,
                "results": [],
                "success_rate": 0,
                "intent_match_rate": None,
                "avg_response_time": 0
            }

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Enhanced agent testing with LangSmith tracing")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose output")
    parser.add_argument("--project", "-p", default="navegador-test", help="LangSmith project name")
    parser.add_argument("--query", "-q", help="Run a single query")
    parser.add_argument("--conversation", "-c", action="store_true", help="Run a conversation test")
    parser.add_argument("--suite", "-s", action="store_true", help="Run the test suite")
    args = parser.parse_args()
    
    log("Starting enhanced agent testing")
    
    # Create tester instance
    tester = AgentTester(project_name=args.project, verbose=args.verbose)
    
    # Run tests based on arguments
    if args.query:
        # Run a single query test
        result = tester.run_single_query(args.query)
        if result:
            log(f"Query test result: {result['formatted_response']}")
        else:
            log("❌ Query test failed")
    elif args.conversation:
        # Run a conversation test
        conversation = [
            "Tell me about this dataset",
            "What variables are available in education?",
            "Can you analyze education satisfaction?",
            "Run a descriptive analysis"
        ]
        result = tester.run_conversation(conversation)
        log(f"Conversation test completed with {result['turns']} turns")
    elif args.suite:
        # Run the test suite
        result = tester.run_test_suite()
        log(f"Test suite completed with {result['test_cases']} test cases")
    else:
        # Default: run a single standard query
        result = tester.run_single_query("Tell me about this dataset")
        if result:
            log(f"Default test result: {result['formatted_response']}")
        else:
            log("❌ Default test failed")
    
    # If LangSmith is available, print trace URL
    if tester.langsmith_client:
        log(f"View traces at: https://smith.langchain.com/projects/{args.project}/traces")
    
    log("Testing completed")
    log_file.close()
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
