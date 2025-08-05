"""
Notebook Startup Script for navegador Project
Add this cell at the top of notebooks to automatically load credentials
"""

# Add project root to path and load credentials
import sys
import os
from pathlib import Path

# Add parent directory to path for notebook imports
notebook_dir = Path.cwd()
project_root = notebook_dir.parent if notebook_dir.name == 'notebooks' else notebook_dir
sys.path.insert(0, str(project_root))

# Auto-load credentials
try:
    from auto_credentials import GITHUB_TOKEN, SSH_KEY_PATH, AZURE_VM_KEY
    
    credentials_available = sum([
        bool(GITHUB_TOKEN),
        bool(SSH_KEY_PATH), 
        bool(AZURE_VM_KEY)
    ])
    
    if credentials_available > 0:
        print(f"🔐 {credentials_available} credentials loaded automatically")
        print("Available as: GITHUB_TOKEN, SSH_KEY_PATH, AZURE_VM_KEY")
    else:
        print("⚠️  No credentials found. Run: ../manage_credentials.sh setup")
        
except ImportError as e:
    print(f"⚠️  Could not load credentials: {e}")
    print("Make sure you're in the notebooks directory or run setup first")

# Also make them available as environment variables for subprocess calls
if 'auto_credentials' in sys.modules:
    from auto_credentials import auto_load_credentials
    auto_load_credentials()

print("✅ Notebook environment ready")
