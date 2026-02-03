"""
Global credential initialization for navegador project
This file can be added to Python's startup to make credentials always available
"""

import os
import sys
from pathlib import Path

def init_navegador_credentials():
    """Initialize navegador credentials globally"""
    # Find project root
    current_path = Path.cwd()
    
    # Look for navegador project markers
    project_markers = ['manage_credentials.sh', 'credentials_manager.py', '.env']
    project_root = None
    
    # Search upward for project root
    for parent in [current_path] + list(current_path.parents):
        if any((parent / marker).exists() for marker in project_markers):
            project_root = parent
            break
    
    if not project_root:
        return False
    
    # Add to Python path
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    
    # Try to load credentials
    try:
        sys.path.insert(0, str(project_root))
        from load_credentials import load_credentials, get_github_token, get_ssh_key_path, get_azure_vm_key
        
        # Load to environment
        count = load_credentials()
        
        # Make available as globals (optional)
        if count > 0:
            globals()['GITHUB_TOKEN'] = get_github_token()
            globals()['SSH_KEY_PATH'] = get_ssh_key_path()
            globals()['AZURE_VM_KEY'] = get_azure_vm_key()
            return True
            
    except ImportError:
        pass
    
    return False

# Auto-initialize if in navegador project
if init_navegador_credentials():
    print("🔐 navegador credentials auto-loaded globally")
