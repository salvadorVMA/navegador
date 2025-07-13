#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Agent Conversation Test

This script demonstrates how to create a simple interactive conversation
with the agent, maintaining conversation state across multiple interactions.
"""

import os
import sys
import time
import json
import uuid
import traceback
from typing import Dict, List, Any, Optional
from datetime import datetime

# Add the directory to the Python path to find the agent module
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    # Import langchain components if available
    from langchain_core.runnables.config import RunnableConfig
except ImportError:
    print("⚠️ LangChain Core not installed - using dict config")
    RunnableConfig = None

def create_agent():
    """Create an agent instance with persistence enabled"""
    try:
        import agent
        print("Creating agent instance...")
        return agent.create_agent(enable_persistence=True)
    except Exception as e:
        print(f"Error creating agent: {e}")
        traceback.print_exc()
        return None

def create_thread_config(thread_id, callbacks=None):
    """Create a thread configuration for the agent"""
    if callbacks is None:
        callbacks = []
    
    if RunnableConfig:
        return RunnableConfig(
            configurable={
                "thread_id": thread_id,
                "callbacks": callbacks
            }
        )
    else:
        return {
            "configurable": {
                "thread_id": thread_id,
                "callbacks": callbacks
            }
        }

def process_agent_response(response):
    """Process and format agent response for display"""
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
        print(f"Error processing response: {e}")
        return str(response)

def get_intent_from_response(response):
    """Extract the intent from a response if available"""
    if isinstance(response, dict) and "intent" in response:
        return response["intent"]
    return None

def interactive_conversation():
    """Run an interactive conversation with the agent"""
    # Create the agent
    agent_instance = create_agent()
    if not agent_instance:
        print("Failed to create agent. Exiting.")
        return False
        
    # Create a thread ID for this conversation
    thread_id = f"interactive_{int(time.time())}"
    print(f"Starting conversation with thread_id: {thread_id}")
    print("-" * 60)
    
    # Create thread config
    config = create_thread_config(thread_id)
    
    # Interactive loop
    try:
        while True:
            # Get user input
            user_input = input("\nYou: ")
            
            # Exit condition
            if user_input.lower() in ("exit", "quit", "bye"):
                print("Ending conversation.")
                break
                
            # Create input state
            input_state = {
                "messages": [{"type": "human", "content": user_input}],
                "metadata": {
                    "language": "en",
                    "dataset": ["ALL"],
                    "intent": "continue_conversation"
                }
            }
            
            # Invoke agent
            print("\nAgent is thinking...")
            start_time = time.time()
            
            try:
                response = agent_instance.invoke(input_state, config=config)
                end_time = time.time()
                
                # Process response
                formatted_response = process_agent_response(response)
                intent = get_intent_from_response(response)
                
                # Display response
                print(f"\nAgent: {formatted_response}")
                print(f"\n[Response time: {end_time - start_time:.2f}s | Intent: {intent}]")
                
            except Exception as e:
                print(f"\nError: {e}")
                traceback.print_exc()
                
    except KeyboardInterrupt:
        print("\nConversation interrupted by user.")
    
    print("-" * 60)
    print("Conversation ended.")
    return True

def main():
    """Main function"""
    print("=" * 60)
    print("Interactive Agent Conversation")
    print("Type 'exit', 'quit', or 'bye' to end the conversation")
    print("=" * 60)
    
    success = interactive_conversation()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
