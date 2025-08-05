"""
Auto-loading credential module for navegador project
Import this at the top of any Python script to automatically load credentials
"""

import os
import sys
from pathlib import Path

# Ensure we can import our credential modules
project_root = Path(__file__).parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

def auto_load_credentials():
    """Automatically load credentials from keychain to environment"""
    try:
        from load_credentials import load_credentials
        count = load_credentials()
        if count > 0:
            print(f"🔐 Auto-loaded {count} credentials from keychain")
        return count
    except ImportError:
        print("⚠️  Credential loading not available")
        return 0

def get_credentials():
    """Get all available credentials as a dictionary"""
    try:
        from load_credentials import get_github_token, get_ssh_key_path, get_azure_vm_key
        return {
            'github_token': get_github_token(),
            'ssh_key_path': get_ssh_key_path(),
            'azure_vm_key': get_azure_vm_key()
        }
    except ImportError:
        return {}

# Auto-load on import (can be disabled by setting SKIP_AUTO_LOAD=1)
if not os.environ.get('SKIP_AUTO_LOAD'):
    auto_load_credentials()

# Convenience exports
try:
    from load_credentials import get_github_token, get_ssh_key_path, get_azure_vm_key
    
    # Make credentials available as simple imports
    GITHUB_TOKEN = get_github_token()
    SSH_KEY_PATH = get_ssh_key_path() 
    AZURE_VM_KEY = get_azure_vm_key()
    
except ImportError:
    GITHUB_TOKEN = None
    SSH_KEY_PATH = None
    AZURE_VM_KEY = None

__all__ = [
    'auto_load_credentials',
    'get_credentials', 
    'get_github_token',
    'get_ssh_key_path',
    'get_azure_vm_key',
    'GITHUB_TOKEN',
    'SSH_KEY_PATH', 
    'AZURE_VM_KEY'
]
