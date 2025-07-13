#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Fix the test_agent_tracing.py script to work with the agent.create_agent function
This will add a debug print statement to track execution flow
"""

import sys
import os
import time
import re

def add_debug_prints(file_path):
    """Add debug print statements to the test_agent_tracing.py file"""
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Add debug print to the main function
    content = content.replace(
        "def main():",
        "def main():\n    print('DEBUG: Starting test_agent_tracing.py...')"
    )
    
    # Add debug print to the _initialize_agent method
    content = content.replace(
        "def _initialize_agent(self):",
        "def _initialize_agent(self):\n        print('DEBUG: Initializing agent...')"
    )
    
    # Add debug print to the profile_query method
    content = content.replace(
        "def profile_query(self, query, language=\"es\", datasets=None, variables=None):",
        "def profile_query(self, query, language=\"es\", datasets=None, variables=None):\n        print(f'DEBUG: Profiling query: {query}')"
    )
    
    # Add debug print to the run_test_queries function
    content = content.replace(
        "def run_test_queries(queries=None, language=\"es\", datasets=None, profiler=None):",
        "def run_test_queries(queries=None, language=\"es\", datasets=None, profiler=None):\n    print('DEBUG: Running test queries...')"
    )
    
    # Write the modified content back to the file
    with open(file_path, 'w') as f:
        f.write(content)
    
    print(f"✅ Added debug print statements to {file_path}")

if __name__ == "__main__":
    script_path = sys.argv[1] if len(sys.argv) > 1 else "test_agent_tracing.py"
    add_debug_prints(script_path)
