#!/usr/bin/env python3
"""
Environment Variable Checker and Loader for LangSmith

This script helps load environment variables from .env files and verifies
they're properly set for LangSmith tools.
"""

import os
import sys
import subprocess
from pathlib import Path

# Try to import dotenv - install if not available
try:
    from dotenv import load_dotenv
    HAS_DOTENV = True
except ImportError:
    HAS_DOTENV = False
    print("python-dotenv not installed. Installing now...")
    subprocess.run([sys.executable, "-m", "pip", "install", "python-dotenv"], check=True)
    from dotenv import load_dotenv

# Define required environment variables
REQUIRED_VARS = [
    "LANGSMITH_API_KEY",
    "LANGCHAIN_TRACING_V2",
]

OPTIONAL_VARS = [
    "LANGCHAIN_PROJECT",
    "LANGCHAIN_ENDPOINT",
    "LANGCHAIN_API_KEY"  # Old name, included for compatibility
]

def find_dotenv_files():
    """Find .env files in the current directory and parent directories"""
    current_dir = Path.cwd()
    env_files = []
    
    # Check the current directory
    env_file = current_dir / ".env"
    if env_file.exists():
        env_files.append(env_file)
    
    # Check parent directories (up to 3 levels)
    parent = current_dir.parent
    for _ in range(3):  # Check up to 3 parent directories
        env_file = parent / ".env"
        if env_file.exists():
            env_files.append(env_file)
        parent = parent.parent
        
    return env_files

def check_env_vars():
    """Check if required environment variables are set"""
    missing_vars = []
    for var in REQUIRED_VARS:
        if not os.environ.get(var):
            missing_vars.append(var)
    
    return missing_vars

def load_env_files(env_files):
    """Load environment variables from .env files"""
    results = []
    for env_file in env_files:
        success = load_dotenv(env_file, override=True)
        results.append((env_file, success))
    return results

def print_environment_status():
    """Print the status of environment variables"""
    print("\n" + "=" * 70)
    print("🔍 LANGSMITH ENVIRONMENT CHECK")
    print("=" * 70 + "\n")
    
    # Check required variables
    print("Required variables:")
    all_required_set = True
    for var in REQUIRED_VARS:
        value = os.environ.get(var, "")
        if value:
            masked_value = value[:4] + "..." + value[-4:] if len(value) > 8 else "***"
            print(f"✅ {var} = {masked_value}")
        else:
            print(f"❌ {var} is not set!")
            all_required_set = False
    
    # Check optional variables
    print("\nOptional variables:")
    for var in OPTIONAL_VARS:
        value = os.environ.get(var, "")
        if value:
            masked_value = value[:4] + "..." + value[-4:] if len(value) > 8 else "***"
            print(f"✅ {var} = {masked_value}")
        else:
            print(f"ℹ️ {var} is not set (optional)")
    
    return all_required_set

def export_environment():
    """Print export commands for environment variables"""
    print("\nTo ensure your environment variables are set correctly, run:")
    print("\n```bash")
    
    api_key = os.environ.get("LANGSMITH_API_KEY", os.environ.get("LANGCHAIN_API_KEY", "your_api_key_here"))
    project = os.environ.get("LANGCHAIN_PROJECT", "navegador-testing")
    
    print(f"export LANGSMITH_API_KEY={api_key}")
    print(f"export LANGCHAIN_PROJECT={project}")
    print("export LANGCHAIN_TRACING_V2=true")
    print("```")

def main():
    # Find .env files
    env_files = find_dotenv_files()
    
    if env_files:
        print(f"Found {len(env_files)} .env file(s):")
        for file in env_files:
            print(f"  - {file}")
        
        # Load environment variables from .env files
        load_results = load_env_files(env_files)
        for file, success in load_results:
            status = "✅ Loaded" if success else "❌ Failed to load"
            print(f"{status} environment variables from {file}")
    else:
        print("No .env files found in the current directory or parent directories.")
    
    # Check environment variables
    all_set = print_environment_status()
    
    if not all_set:
        print("\n⚠️ Some required environment variables are not set!")
        export_environment()
        
        print("\nTo fix the issue:")
        print("1. Use the export commands above to set the variables in your terminal")
        print("2. Create or update your .env file with the correct values")
        print("3. Make sure your script loads the .env file correctly using python-dotenv")
        
        return False
    else:
        print("\n✅ All required environment variables are set!")
        return True

if __name__ == "__main__":
    success = main()
    
    if len(sys.argv) > 1 and success:
        # If arguments provided and environment is good, run the specified command
        command = sys.argv[1:]
        print(f"\n🔄 Running command: {' '.join(command)}")
        subprocess.run(command)
    elif not success:
        sys.exit(1)
