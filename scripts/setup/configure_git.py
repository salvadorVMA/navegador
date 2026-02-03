#!/usr/bin/env python3
"""
Git Configuration Script for navegador Project
Configures git to use secure credentials from Apple Keychain
"""

import sys
import os
import subprocess

# Add current directory to path to import our modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from credentials_manager import SecureCredentialsManager

def configure_git():
    """Configure git with secure credentials"""
    manager = SecureCredentialsManager()
    
    print("🔧 Configuring Git with secure credentials...")
    
    # Get GitHub token
    github_token = manager.retrieve_credential('github-token')
    if not github_token:
        print("❌ GitHub token not found in keychain")
        print("Run 'python setup_credentials.py' first")
        return False
    
    try:
        # Configure git to use macOS keychain
        subprocess.run(['git', 'config', '--global', 'credential.helper', 'osxkeychain'], check=True)
        print("✅ Git configured to use macOS Keychain")
        
        # Set up GitHub credentials for HTTPS
        github_url = f"https://{github_token}@github.com"
        print(f"✅ GitHub token configured")
        print(f"📝 For HTTPS cloning: git clone {github_url}/owner/repo.git")
        
        # Configure user info if not set
        try:
            subprocess.run(['git', 'config', '--global', 'user.name'], 
                         capture_output=True, check=True)
        except subprocess.CalledProcessError:
            # User name not set
            name = input("📝 Enter your Git user name: ").strip()
            if name:
                subprocess.run(['git', 'config', '--global', 'user.name', name], check=True)
                print(f"✅ Git user.name set to: {name}")
        
        try:
            subprocess.run(['git', 'config', '--global', 'user.email'], 
                         capture_output=True, check=True)
        except subprocess.CalledProcessError:
            # User email not set
            email = input("📧 Enter your Git user email: ").strip()
            if email:
                subprocess.run(['git', 'config', '--global', 'user.email', email], check=True)
                print(f"✅ Git user.email set to: {email}")
        
        print("\n🎉 Git configuration complete!")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to configure git: {e}")
        return False

def show_git_config():
    """Show current git configuration"""
    print("📋 Current Git Configuration:")
    print("-" * 30)
    
    configs = [
        'user.name',
        'user.email', 
        'credential.helper'
    ]
    
    for config in configs:
        try:
            result = subprocess.run(['git', 'config', '--global', config], 
                                  capture_output=True, text=True, check=True)
            value = result.stdout.strip()
            print(f"✅ {config}: {value}")
        except subprocess.CalledProcessError:
            print(f"❌ {config}: Not set")

def main():
    """Main function"""
    if len(sys.argv) > 1:
        if sys.argv[1] == 'show':
            show_git_config()
        elif sys.argv[1] == 'configure':
            configure_git()
        else:
            print("Usage: python configure_git.py [show|configure]")
    else:
        # Default action
        configure_git()

if __name__ == "__main__":
    main()
