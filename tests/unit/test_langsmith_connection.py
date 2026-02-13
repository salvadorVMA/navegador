#!/usr/bin/env python3
"""
LangSmith Connection Test Script

This script tests your connection to LangSmith and verifies your API key is working.
Can be run directly or via pytest.
"""

import os
import sys
import traceback

import pytest


def check_env_var(var_name):
    """Check if environment variable is set and not empty"""
    value = os.environ.get(var_name, "")
    if not value:
        print(f"  {var_name} is not set!")
        return False
    else:
        masked_value = value[:4] + "..." + value[-4:] if len(value) > 8 else "***"
        print(f"  {var_name} is set: {masked_value}")
        return True


@pytest.mark.skipif(
    not (os.environ.get("LANGSMITH_API_KEY") or os.environ.get("LANGCHAIN_API_KEY")),
    reason="No LangSmith API key found (LANGSMITH_API_KEY or LANGCHAIN_API_KEY)"
)
def test_langsmith_connection():
    """Test that LangSmith connection works with current API key."""
    from langsmith.client import Client

    client = Client()
    projects = client.list_projects()
    project_count = len(list(projects))
    assert project_count >= 0, "Should be able to list projects"

    current_project = os.environ.get("LANGCHAIN_PROJECT", "default")
    print(f"Connected to LangSmith API ({project_count} projects, current: {current_project})")


if __name__ == '__main__':
    print("\n" + "=" * 70)
    print("LANGSMITH CONNECTION TEST")
    print("=" * 70 + "\n")

    print("Checking environment variables:")
    api_key_set = check_env_var("LANGSMITH_API_KEY") or check_env_var("LANGCHAIN_API_KEY")
    check_env_var("LANGCHAIN_PROJECT")
    check_env_var("LANGCHAIN_TRACING_V2")

    if not api_key_set:
        print("\nNo LangSmith API key found. Please set your API key:")
        print("export LANGSMITH_API_KEY=your_api_key")
        sys.exit(1)

    print("\nTesting LangSmith connection...")

    try:
        from langsmith.client import Client
        print("Successfully imported LangSmith client")
    except ImportError:
        print("Could not import LangSmith client")
        print("Try installing it with: pip install langsmith")
        sys.exit(1)

    try:
        client = Client()
        print("Successfully initialized LangSmith client")

        projects = client.list_projects()
        project_count = len(list(projects))
        print(f"Successfully connected to LangSmith API ({project_count} projects available)")

        current_project = os.environ.get("LANGCHAIN_PROJECT", "default")
        print(f"Current project: {current_project}")

        print("\nLangSmith connection test PASSED!")

    except Exception as e:
        print(f"Error connecting to LangSmith: {str(e)}")
        print("\nDetailed error:")
        traceback.print_exc()
        sys.exit(1)
