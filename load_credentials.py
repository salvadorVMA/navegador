#!/usr/bin/env python3
"""
Environment Loader for navegador Project
Loads credentials from Apple Keychain into environment variables
"""

import sys
import os

# Add current directory to path to import our modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from credentials_manager import SecureCredentialsManager

def load_credentials():
    """Load credentials from keychain to environment variables"""
    manager = SecureCredentialsManager()
    
    env_mapping = {
        'github-token': 'GITHUB_TOKEN',
        'ssh-key-path': 'SSH_PRIVATE_KEY_PATH',
        'azure-vm-key': 'AZURE_VM_KEY_PATH'
    }
    
    loaded_count = 0
    
    for account, env_var in env_mapping.items():
        credential = manager.retrieve_credential(account)
        if credential:
            os.environ[env_var] = credential
            loaded_count += 1
    
    return loaded_count

def get_github_token():
    """Get GitHub token from keychain or environment"""
    manager = SecureCredentialsManager()
    return os.environ.get('GITHUB_TOKEN') or manager.retrieve_credential('github-token')

def get_ssh_key_path():
    """Get SSH key path from keychain or environment"""
    manager = SecureCredentialsManager()
    return os.environ.get('SSH_PRIVATE_KEY_PATH') or manager.retrieve_credential('ssh-key-path')

def get_azure_vm_key():
    """Get Azure VM key path from keychain or environment"""
    manager = SecureCredentialsManager()
    return os.environ.get('AZURE_VM_KEY_PATH') or manager.retrieve_credential('azure-vm-key')

def main():
    """Command line interface"""
    if len(sys.argv) > 1 and sys.argv[1] == 'test':
        # Test mode - show what would be loaded
        print("🧪 Testing credential access...")
        
        github = get_github_token()
        ssh = get_ssh_key_path()
        azure = get_azure_vm_key()
        
        print(f"GitHub Token: {'✅ Found' if github else '❌ Not found'}")
        print(f"SSH Key: {'✅ Found' if ssh else '❌ Not found'}")
        print(f"Azure VM Key: {'✅ Found' if azure else '❌ Not found'}")
        
        if github:
            print(f"  GitHub: {github[:8]}...")
        if ssh:
            print(f"  SSH: {ssh}")
        if azure:
            print(f"  Azure: {azure}")
    
    else:
        # Load credentials to environment
        count = load_credentials()
        print(f"🔐 Loaded {count} credentials into environment variables")
        
        if count > 0:
            print("Environment variables set:")
            if os.environ.get('GITHUB_TOKEN'):
                print("  ✅ GITHUB_TOKEN")
            if os.environ.get('SSH_PRIVATE_KEY_PATH'):
                print("  ✅ SSH_PRIVATE_KEY_PATH")
            if os.environ.get('AZURE_VM_KEY_PATH'):
                print("  ✅ AZURE_VM_KEY_PATH")

if __name__ == "__main__":
    main()
