#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test script for agent with LangSmith tracing enabled
This script demonstrates how to create an agent with tracing enabled
and process a simple conversation with proper thread handling.
"""

import os
import sys
import time
import json
import traceback
import argparse
from datetime import datetime

# Import langsmith for tracing if available
try:
    from langsmith.client import Client as LangSmithClient
    from langsmith.schemas import Run as LangSmithRun
    LANGSMITH_AVAILABLE = True
except ImportError:
    print("⚠️ LangSmith packages not found - tracing will be limited")
    LANGSMITH_AVAILABLE = False
    LangSmithClient = None
    LangSmithRun = None

# Add LangChain tracing imports
from langchain_core.tracers import LangChainTracer
import langchain_core.callbacks.manager as langchain_manager
from langchain_core.runnables.config import RunnableConfig

# Set up basic logging to file
log_file = open("test_agent_tracing.log", "w")

def log(message):
    """Log message to both console and file"""
    print(message)
    log_file.write(f"{message}\n")
    log_file.flush()

def initialize_langsmith():
    """Initialize LangSmith client and tracing"""
    # Enable LangSmith tracing if API key is available
    os.environ["LANGSMITH_TRACING"] = "true"
    
    # Get LangSmith configuration
    api_key = os.getenv("LANGSMITH_API_KEY")
    project = os.getenv("LANGSMITH_PROJECT", "navegador-test")
    
    if not api_key:
        log("⚠️ LANGSMITH_API_KEY not set - tracing will be disabled")
        return None, None
    
    if not LANGSMITH_AVAILABLE:
        log("⚠️ LangSmith packages not installed - tracing will be disabled")
        return None, None
        
    try:
        # Initialize client and tracer
        if LangSmithClient:
            client = LangSmithClient(api_key=api_key)
            tracer = LangChainTracer(project_name=project)
            
            # Enable tracing v2
            os.environ["LANGCHAIN_TRACING_V2"] = "true"
            log(f"✅ LangSmith monitoring initialized for project: {project}")
            return client, tracer
        else:
            log("⚠️ LangSmith client not available")
            return None, None
    except Exception as e:
        log(f"❌ Error initializing LangSmith: {e}")
        return None, None

def process_agent_response(response):
    """Process and format agent response for display"""
    try:
        # Extract the last message if it's a list of messages
        if isinstance(response, dict) and "messages" in response:
            messages = response["messages"]
            if messages and len(messages) > 0:
                last_message = messages[-1]
                if isinstance(last_message, dict) and "content" in last_message:
                    return last_message["content"]
        
        # If it's a simple response with content
        if isinstance(response, dict) and "content" in response:
            return response["content"]
            
        # Fall back to string representation
        return str(response)
    except Exception as e:
        log(f"Error processing response: {e}")
        return str(response)

def create_thread_config(thread_id, callbacks=None):
    """Create a thread configuration for the agent"""
    if callbacks is None:
        callbacks = []
    
    # Use proper RunnableConfig structure
    config = RunnableConfig(
        configurable={
            "thread_id": thread_id,
            "callbacks": callbacks
        }
    )
    return config

def run_test():
    """Run the agent test with tracing"""
    log("Starting agent test with tracing")
    
    # Initialize LangSmith
    langsmith_client, tracer = initialize_langsmith()
    callbacks = [tracer] if tracer else []
    
    # Import agent module
    try:
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        import agent
        log(f"Agent module imported successfully. Functions: {[f for f in dir(agent) if not f.startswith('_') and callable(getattr(agent, f))][0:5]}...")
        
        # Create agent instance
        log("Creating agent instance with persistence enabled...")
        agent_instance = agent.create_agent(enable_persistence=True)
        log("Agent instance created successfully")
        
        # Create a test thread
        thread_id = f"test_{int(time.time())}"
        log(f"Created test thread ID: {thread_id}")
        
        # Set up thread config with tracing callbacks
        config = create_thread_config(thread_id, callbacks)
        
        # Create input state
        input_state = {
            "messages": [{"type": "human", "content": "Tell me about this dataset"}],
            "metadata": {
                "language": "en",
                "dataset": ["ALL"],
                "intent": "continue_conversation"
            }
        }
        
        # Invoke agent
        log(f"Invoking agent with thread_id {thread_id}...")
        start_time = time.time()
        response = agent_instance.invoke(input_state, config=config)
        end_time = time.time()
        
        # Process response
        formatted_response = process_agent_response(response)
        log(f"Response received in {end_time - start_time:.2f}s:")
        log(f"---\n{formatted_response}\n---")
        
        # If LangSmith is available, print trace URL
        if langsmith_client:
            log(f"View trace at: https://smith.langchain.com/projects/{os.getenv('LANGSMITH_PROJECT', 'navegador-test')}/traces")
        
        log("Test completed successfully")
        return True
    except Exception as e:
        log(f"❌ Error during agent test: {e}")
        log(traceback.format_exc())
        return False

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Test agent with LangSmith tracing")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose output")
    args = parser.parse_args()
    
    if args.verbose:
        log("Verbose mode enabled")
    
    success = run_test()
    log_file.close()
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
