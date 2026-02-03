#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Simple test script that doesn't rely on any other modules
"""

import os
import sys
import time

# Open a log file
log_file = open("test_agent.log", "w")
log_file.write("Test agent tracing script started\n")
log_file.flush()

# Test command line args
log_file.write(f"Command line args: {sys.argv}\n")
log_file.flush()

# Test basic imports
try:
    log_file.write("Importing modules...\n")
    log_file.flush()
    
    import traceback
    import json
    import argparse
    from datetime import datetime
    
    log_file.write("Basic modules imported successfully\n")
    log_file.flush()
    
    # Try importing the agent module
    log_file.write("Importing agent module...\n")
    log_file.flush()
    
    try:
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        import agent
        log_file.write(f"Agent module imported successfully. Available functions: {[f for f in dir(agent) if not f.startswith('_') and callable(getattr(agent, f))]}\n")
        log_file.flush()
        
        # Try creating an agent instance
        log_file.write("Creating agent instance...\n")
        log_file.flush()
        
        try:
            agent_instance = agent.create_agent(enable_persistence=True)
            log_file.write("Agent instance created successfully\n")
            log_file.flush()
            
            # Try invoking the agent
            log_file.write("Testing agent with a simple query...\n")
            log_file.flush()
            
            thread_id = f"test_{int(time.time())}"
            config = {"configurable": {"thread_id": thread_id, "callbacks": []}}
            input_state = {
                "messages": [{"type": "human", "content": "Hello"}],
                "metadata": {
                    "language": "en",
                    "dataset": ["ALL"],
                    "intent": "continue_conversation"
                }
            }
            
            try:
                log_file.write(f"Invoking agent with thread_id {thread_id}...\n")
                log_file.flush()
                
                response = agent_instance.invoke(input_state, config=config)
                log_file.write(f"Agent response received: {response}\n")
                log_file.flush()
                
                log_file.write("Test completed successfully\n")
                log_file.flush()
            except Exception as e:
                log_file.write(f"Error invoking agent: {e}\n")
                log_file.write(traceback.format_exc() + "\n")
                log_file.flush()
        except Exception as e:
            log_file.write(f"Error creating agent: {e}\n")
            log_file.write(traceback.format_exc() + "\n")
            log_file.flush()
    except Exception as e:
        log_file.write(f"Error importing agent module: {e}\n")
        log_file.write(traceback.format_exc() + "\n")
        log_file.flush()
except Exception as e:
    log_file.write(f"Error: {e}\n")
    log_file.flush()

# Close the log file
log_file.close()
