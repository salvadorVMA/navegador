#!/usr/bin/env python3
"""
LangSmith Connection Test Script

This script tests your connection to LangSmith and verifies your API key is working.
"""

import os
import sys
import traceback

# Function to check if environment variable is set
def check_env_var(var_name):
    """Check if environment variable is set and not empty"""
    value = os.environ.get(var_name, "")
    if not value:
        print(f"❌ {var_name} is not set!")
        return False
    else:
        masked_value = value[:4] + "..." + value[-4:] if len(value) > 8 else "***"
        print(f"✅ {var_name} is set: {masked_value}")
        return True

# Print header
print("\n" + "=" * 70)
print("🔍 LANGSMITH CONNECTION TEST")
print("=" * 70 + "\n")

# Check environment variables
print("Checking environment variables:")
api_key_set = check_env_var("LANGSMITH_API_KEY") or check_env_var("LANGCHAIN_API_KEY")
project_set = check_env_var("LANGCHAIN_PROJECT")
tracing_set = check_env_var("LANGCHAIN_TRACING_V2")

if not api_key_set:
    print("\n⚠️ No LangSmith API key found. Please set your API key:")
    print("export LANGSMITH_API_KEY=your_api_key")
    sys.exit(1)

print("\nTesting LangSmith connection...")

# Try importing the LangSmith client
try:
    from langsmith.client import Client
    print("✅ Successfully imported LangSmith client")
except ImportError:
    print("❌ Could not import LangSmith client")
    print("Try installing it with: pip install langsmith")
    sys.exit(1)

# Try to initialize the client and connect to LangSmith
try:
    client = Client()
    print("✅ Successfully initialized LangSmith client")
    
    # Try to list projects to verify API key works
    projects = client.list_projects()
    project_count = len(list(projects))
    print(f"✅ Successfully connected to LangSmith API ({project_count} projects available)")
    
    # Show current project
    current_project = os.environ.get("LANGCHAIN_PROJECT", "default")
    print(f"📊 Current project: {current_project}")
    
    # Print success message
    print("\n✅ LangSmith connection test PASSED!")
    print(f"✅ You can access your runs at: https://smith.langchain.com/projects/{current_project}/runs")
    
except Exception as e:
    print(f"❌ Error connecting to LangSmith: {str(e)}")
    print("\nDetailed error:")
    traceback.print_exc()
    
    print("\n⚠️ Troubleshooting tips:")
    print("1. Verify your API key at https://smith.langchain.com/settings/api-keys")
    print("2. Make sure you can access https://smith.langchain.com/ in your browser")
    print("3. Check if your internet connection has any firewall restrictions")
    print("4. Verify you have the latest version of langsmith: pip install --upgrade langsmith")
    sys.exit(1)
