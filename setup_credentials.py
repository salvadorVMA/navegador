#!/usr/bin/env python3
"""
Setup Script for navegador Project Credentials
Automatically detects and securely stores GitHub token and Azure VM key
"""

import sys
import os

# Add current directory to path to import our modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from credentials_manager import SecureCredentialsManager

def main():
    print("🔐 navegador Project Credential Setup")
    print("=" * 50)
    print("This script will automatically detect and save:")
    print("  - GitHub token from .env file")
    print("  - Azure VM key from ~/.ssh/azure_vm_key") 
    print("  - SSH key from ~/.ssh/")
    print()
    
    # Initialize manager
    manager = SecureCredentialsManager()
    
    # Auto-detect credentials
    print("🔍 Scanning for credentials...")
    found_credentials = manager.auto_detect_credentials()
    
    if not found_credentials:
        print("❌ No credentials found automatically")
        print("Run 'python credentials_manager.py setup' for manual setup")
        return
    
    print(f"\n📋 Found {len(found_credentials)} credentials")
    
    # Confirm before saving
    response = input("\n💾 Save these credentials to Apple Keychain? (y/N): ").lower().strip()
    if response != 'y':
        print("⏹️  Setup cancelled")
        return
    
    # Save to keychain
    saved_count = 0
    for account, credential in found_credentials.items():
        if manager.store_credential(account, credential):
            saved_count += 1
    
    print(f"\n✅ Successfully saved {saved_count} credentials to Apple Keychain")
    print("\n🎉 Setup complete! Credentials are now available for:")
    print("  - VS Code notebooks")
    print("  - Terminal scripts")
    print("  - Git operations")
    
    # Show status
    print("\n📊 Final status:")
    manager.status()

if __name__ == "__main__":
    main()
