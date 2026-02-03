#!/usr/bin/env python3
"""
Secure Credentials Manager for navegador project
Manages only the specific credentials identified: GitHub token and SSH key path
"""

import subprocess
import os
import sys
from typing import Optional


class SecureCredentialsManager:
    """
    Minimal credentials manager for Apple Keychain
    Only manages GitHub token and SSH key path - no broad keychain access
    """
    
    def __init__(self):
        self.service_name = "navegador-project"
        # Expanded to include Azure and auto-detection
        self.allowed_accounts = {
            'github-token': 'GitHub Personal Access Token',
            'ssh-key-path': 'SSH Private Key File Path',
            'azure-vm-key': 'Azure VM Private Key Path'
        }
        
        # Auto-detection paths
        self.auto_detect_paths = {
            'env_file': '.env',
            'azure_key_file': os.path.expanduser('~/.ssh/azure_vm_key'),
            'ssh_dir': os.path.expanduser('~/.ssh')
        }
    
    def _validate_account(self, account: str) -> bool:
        """Validate that account is one of the allowed ones"""
        if account not in self.allowed_accounts:
            print(f"❌ Account '{account}' not allowed. Only: {list(self.allowed_accounts.keys())}")
            return False
        return True
    
    def auto_detect_credentials(self) -> dict:
        """
        Auto-detect credentials from known locations
        
        Returns:
            dict: Found credentials {account: value}
        """
        found_credentials = {}
        
        # Detect GitHub token from .env file
        env_path = self.auto_detect_paths['env_file']
        if os.path.exists(env_path):
            try:
                with open(env_path, 'r') as f:
                    for line in f:
                        if line.startswith('GITHUB_TOKEN='):
                            token = line.split('=', 1)[1].strip()
                            if token:
                                found_credentials['github-token'] = token
                                print(f"✅ Found GitHub token in {env_path}")
                            break
            except Exception as e:
                print(f"⚠️  Could not read {env_path}: {e}")
        
        # Detect Azure VM key
        azure_key_path = self.auto_detect_paths['azure_key_file']
        if os.path.exists(azure_key_path):
            found_credentials['azure-vm-key'] = azure_key_path
            print(f"✅ Found Azure VM key at {azure_key_path}")
        
        # Detect SSH key (look for common names)
        ssh_dir = self.auto_detect_paths['ssh_dir']
        if os.path.exists(ssh_dir):
            common_ssh_names = ['id_rsa', 'id_ed25519', 'id_ecdsa']
            for key_name in common_ssh_names:
                key_path = os.path.join(ssh_dir, key_name)
                if os.path.exists(key_path):
                    found_credentials['ssh-key-path'] = key_path
                    print(f"✅ Found SSH key at {key_path}")
                    break
        
        return found_credentials
    
    def store_credential(self, account: str, password: str) -> bool:
        """
        Store a credential in Apple Keychain (only allowed accounts)
        
        Args:
            account: Must be 'github-token' or 'ssh-key-path'
            password: The credential value to store
        
        Returns:
            bool: True if successful, False otherwise
        """
        if not self._validate_account(account):
            return False
            
        try:
            cmd = [
                'security', 'add-generic-password',
                '-s', self.service_name,
                '-a', account,
                '-w', password,
                '-U'  # Update if exists
            ]
            
            # Add human-readable label
            cmd.extend(['-l', self.allowed_accounts[account]])
            
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            print(f"✅ Stored {self.allowed_accounts[account]}")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to store {account}: {e.stderr}")
            return False
    
    def retrieve_credential(self, account: str) -> Optional[str]:
        """
        Retrieve a credential from Apple Keychain
        
        Args:
            account: Must be 'github-token' or 'ssh-key-path'
            
        Returns:
            str: The credential value, or None if not found
        """
        if not self._validate_account(account):
            return None
            
        try:
            cmd = [
                'security', 'find-generic-password',
                '-s', self.service_name,
                '-a', account,
                '-w'  # Return password only
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            credential = result.stdout.strip()
            return credential
            
        except subprocess.CalledProcessError:
            return None
    
    def setup_project_credentials(self) -> bool:
        """
        Interactive setup for project credentials with auto-detection
        
        Returns:
            bool: True if at least one credential was set up
        """
        print("🔐 Setting up navegador project credentials")
        print("=" * 50)
        
        # First, try auto-detection
        print("🔍 Auto-detecting credentials...")
        found_credentials = self.auto_detect_credentials()
        
        setup_count = 0
        
        if found_credentials:
            print(f"\n📋 Found {len(found_credentials)} credentials automatically")
            for account, credential in found_credentials.items():
                existing = self.retrieve_credential(account)
                if existing:
                    print(f"   ⚠️  {self.allowed_accounts[account]} already stored")
                    response = input(f"   Update with detected credential? (y/N): ").lower().strip()
                    if response != 'y':
                        continue
                
                if self.store_credential(account, credential):
                    setup_count += 1
                    print(f"   ✅ Stored {self.allowed_accounts[account]}")
        
        # Interactive setup for any missing credentials
        for account, description in self.allowed_accounts.items():
            if account in found_credentials:
                continue  # Already handled above
                
            print(f"\n📝 {description}:")
            
            # Check if already exists
            existing = self.retrieve_credential(account)
            if existing:
                masked = existing[:8] + "..." if len(existing) > 8 else existing
                print(f"   ✅ Already exists: {masked}")
                response = input("   Update? (y/N): ").lower().strip()
                if response != 'y':
                    continue
            
            # Get new credential
            if account == 'ssh-key-path':
                ssh_dir = self.auto_detect_paths['ssh_dir']
                if os.path.exists(ssh_dir):
                    ssh_files = [f for f in os.listdir(ssh_dir) 
                               if not f.endswith('.pub') and not f.startswith('.')]
                    if ssh_files:
                        print(f"   Found SSH keys: {', '.join(ssh_files[:3])}")
                        print(f"   Suggested: {ssh_dir}/id_rsa")
                
                credential = input("   SSH key file path: ").strip()
                if credential and not credential.startswith('/'):
                    credential = os.path.expanduser(f"~/.ssh/{credential}")
                    
                if credential and not os.path.exists(credential):
                    print(f"   ⚠️  File does not exist: {credential}")
                    continue
                    
            elif account == 'azure-vm-key':
                print(f"   Suggested: {self.auto_detect_paths['azure_key_file']}")
                credential = input("   Azure VM key file path: ").strip()
                if not credential:
                    credential = self.auto_detect_paths['azure_key_file']
                if credential and not credential.startswith('/'):
                    credential = os.path.expanduser(credential)
                    
                if credential and not os.path.exists(credential):
                    print(f"   ⚠️  File does not exist: {credential}")
                    continue
                    
            else:  # github-token
                print("   Enter your GitHub Personal Access Token:")
                credential = input("   Token: ").strip()
            
            if credential:
                if self.store_credential(account, credential):
                    setup_count += 1
            else:
                print("   Skipped.")
        
        print(f"\n📊 Set up {setup_count} credentials")
        return setup_count > 0
    
    def load_to_environment(self) -> int:
        """
        Load the managed credentials to environment variables
        
        Returns:
            int: Number of credentials loaded
        """
        env_mapping = {
            'github-token': 'GITHUB_TOKEN',
            'ssh-key-path': 'SSH_PRIVATE_KEY_PATH',
            'azure-vm-key': 'AZURE_VM_KEY_PATH'
        }
        
        loaded_count = 0
        
        for account, env_var in env_mapping.items():
            credential = self.retrieve_credential(account)
            if credential:
                os.environ[env_var] = credential
                print(f"✅ Loaded {env_var}")
                loaded_count += 1
        
        return loaded_count
    
    def status(self) -> dict:
        """
        Check status of managed credentials
        
        Returns:
            dict: Status of each credential
        """
        status_info = {}
        
        print("🔍 Credential Status:")
        print("-" * 30)
        
        for account, description in self.allowed_accounts.items():
            credential = self.retrieve_credential(account)
            if credential:
                masked = credential[:8] + "..." if len(credential) > 8 else credential
                status_info[account] = 'present'
                print(f"✅ {description}: {masked}")
            else:
                status_info[account] = 'missing'
                print(f"❌ {description}: Not found")
        
        return status_info


def main():
    """Command line interface for credentials management"""
    if len(sys.argv) < 2:
        print("Usage: python credentials_manager.py <command>")
        print("Commands:")
        print("  setup    - Interactive setup of credentials")
        print("  auto     - Auto-detect and save credentials")
        print("  status   - Check credential status")
        print("  load     - Load credentials to environment")
        return
    
    manager = SecureCredentialsManager()
    command = sys.argv[1].lower()
    
    if command == 'setup':
        manager.setup_project_credentials()
    elif command == 'auto':
        print("🔍 Auto-detecting and saving credentials...")
        found = manager.auto_detect_credentials()
        saved_count = 0
        for account, credential in found.items():
            if manager.store_credential(account, credential):
                saved_count += 1
        print(f"💾 Saved {saved_count} credentials to keychain")
    elif command == 'status':
        manager.status()
    elif command == 'load':
        count = manager.load_to_environment()
        print(f"Loaded {count} credentials to environment")
    else:
        print(f"Unknown command: {command}")


if __name__ == "__main__":
    main()
