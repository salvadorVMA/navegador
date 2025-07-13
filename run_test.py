#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Simple test runner for the test_agent_tracing.py file
"""

import sys
import os
import time

# Add the current directory to the path to make imports work
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Print environment info
print(f"Python version: {sys.version}")
print(f"Current directory: {os.getcwd()}")

try:
    # Try importing
    import agent
    print(f"✅ Successfully imported agent module")
    print(f"Available functions in agent: {[f for f in dir(agent) if not f.startswith('_')]}")
except ImportError as e:
    print(f"❌ Failed to import agent module: {e}")

# Wait a bit to see the output
time.sleep(1)

try:
    # Run the test script with -n flag to disable LangSmith and a simple query
    cmd = f"{sys.executable} test_agent_tracing.py -n -q test"
    print(f"Running command: {cmd}")
    os.system(cmd)
except Exception as e:
    print(f"Error running script: {e}")

print("Script completed")
