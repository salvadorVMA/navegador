#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Simple debug script to run the test_agent_tracing.py file with error output
"""

import os
import sys
import traceback
import subprocess

def run_test():
    """Run the test_agent_tracing.py script and capture errors"""
    cmd = [sys.executable, "test_agent_tracing.py", "-n", "-q", "test query"]
    
    try:
        # Run the script with real-time output
        print("===== Running test_agent_tracing.py =====")
        process = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=os.path.dirname(os.path.abspath(__file__))
        )
        
        # Print stdout
        print("\n===== STDOUT =====")
        print(process.stdout)
        
        # Print stderr
        print("\n===== STDERR =====")
        print(process.stderr)
        
        print(f"\nExit code: {process.returncode}")
    except Exception as e:
        print(f"Error running script: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    run_test()
