#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test the agent.create_agent function directly.

This is a script-style test. Run directly: python test_agent_directly.py
For pytest: use test_agent_workflow.py instead.
"""

import os
import sys
import time
import traceback

import pytest

pytestmark = pytest.mark.skip(reason="Script-style test, run directly with python")


if __name__ == '__main__':
    # Add the current directory to the path to make imports work
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

    print("Testing agent module...")

    try:
        # Import the agent module
        import agent
        print(f"Successfully imported agent module")
        print(f"Available functions: {[f for f in dir(agent) if not f.startswith('_') and callable(getattr(agent, f))]}")

        # Try to create an agent instance
        print("\nCreating agent with create_agent()...")
        start_time = time.time()
        try:
            agent_instance = agent.create_agent(enable_persistence=True)
            elapsed = time.time() - start_time
            print(f"Agent created in {elapsed:.2f} seconds")
            print(f"Agent type: {type(agent_instance)}")
        except Exception as e:
            print(f"Error creating agent with enable_persistence=True: {e}")
            print("\nTrying again without parameters...")
            try:
                agent_instance = agent.create_agent()
                elapsed = time.time() - start_time
                print(f"Agent created in {elapsed:.2f} seconds")
                print(f"Agent type: {type(agent_instance)}")
            except Exception as e:
                print(f"Error creating agent without parameters: {e}")
                traceback.print_exc()
        # Try a simple query
        if 'agent_instance' in locals():
            print("\nTesting agent with a simple query...")
            try:
                thread_id = f"test_{int(time.time())}"
                print(f"Using thread_id: {thread_id}")

                config = {
                    "configurable": {
                        "thread_id": thread_id,
                        "callbacks": []
                    }
                }

                input_state = {
                    "messages": [{"type": "human", "content": "Hello"}],
                    "metadata": {
                        "language": "en",
                        "dataset": ["ALL"],
                        "intent": "continue_conversation"
                    }
                }

                print(f"Input state: {input_state}")
                print(f"Config: {config}")

                response = agent_instance.invoke(input_state, config=config)
                print(f"Agent response received")
                print(f"Response type: {type(response)}")
                print(f"Response content: {response}")
            except Exception as e:
                print(f"Error invoking agent: {e}")
                traceback.print_exc()

    except ImportError as e:
        print(f"Failed to import agent module: {e}")
        traceback.print_exc()
    except Exception as e:
        print(f"Unexpected error: {e}")
        traceback.print_exc()

    print("\nTest completed")
