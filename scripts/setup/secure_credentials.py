"""
VS Code Integration for Secure Credentials
Import this module to automatically load credentials from Apple Keychain
"""

import os
import sys
from pathlib import Path

# Add the project root to path if needed
project_root = Path(__file__).parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

try:
    from credentials_manager import SecureCredentialsManager
    
    # Initialize the credentials manager
    _credentials = SecureCredentialsManager()
    
    # Automatically load credentials when imported
    loaded_count = _credentials.load_to_environment()
    
    if loaded_count > 0:
        print(f"🔐 Loaded {loaded_count} credentials from Apple Keychain")
    
    # Make the manager available for manual operations
    credentials = _credentials
    
    # Convenience functions
    def get_github_token():
        """Get GitHub token from environment or keychain"""
        return os.environ.get('GITHUB_TOKEN') or _credentials.retrieve_credential('github-token')
    
    def get_ssh_key_path():
        """Get SSH key path from environment or keychain"""
        return os.environ.get('SSH_PRIVATE_KEY_PATH') or _credentials.retrieve_credential('ssh-key-path')
    
    def get_azure_vm_key():
        """Get Azure VM key path from environment or keychain"""
        return os.environ.get('AZURE_VM_KEY_PATH') or _credentials.retrieve_credential('azure-vm-key')
    
    def setup_credentials():
        """Run interactive credential setup"""
        return _credentials.setup_project_credentials()
    
    def auto_setup_credentials():
        """Auto-detect and save credentials"""
        found = _credentials.auto_detect_credentials()
        saved_count = 0
        for account, credential in found.items():
            if _credentials.store_credential(account, credential):
                saved_count += 1
        return saved_count
    
    def credential_status():
        """Check credential status"""
        return _credentials.status()

except ImportError as e:
    print(f"⚠️  Could not import credentials manager: {e}")
    credentials = None

# Fallback functions when credentials manager not available
def _get_github_token_fallback():
    return os.environ.get('GITHUB_TOKEN')

def _get_ssh_key_path_fallback():
    return os.environ.get('SSH_PRIVATE_KEY_PATH')

def _get_azure_vm_key_fallback():
    return os.environ.get('AZURE_VM_KEY_PATH')

def _setup_credentials_fallback():
    print("❌ Credentials manager not available")
    return False

def _auto_setup_credentials_fallback():
    print("❌ Credentials manager not available")
    return 0

def _credential_status_fallback():
    print("❌ Credentials manager not available")
    return {}

# Set functions based on availability
if credentials is None:
    get_github_token = _get_github_token_fallback
    get_ssh_key_path = _get_ssh_key_path_fallback
    get_azure_vm_key = _get_azure_vm_key_fallback
    setup_credentials = _setup_credentials_fallback
    auto_setup_credentials = _auto_setup_credentials_fallback
    credential_status = _credential_status_fallback

# Auto-export for easy imports
__all__ = [
    'credentials',
    'get_github_token', 
    'get_ssh_key_path',
    'get_azure_vm_key',
    'setup_credentials',
    'auto_setup_credentials',
    'credential_status'
]
