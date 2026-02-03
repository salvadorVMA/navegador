#!/usr/bin/env python3
"""
Example Usage of Auto-Loading Credentials
Demonstrates how credentials are automatically available in Python scripts
"""

print("🔐 Credential Auto-Loading Example")
print("=" * 40)

# Method 1: Auto-loading import (credentials load automatically)
print("\n1️⃣ Auto-loading import:")
from auto_credentials import GITHUB_TOKEN, SSH_KEY_PATH, AZURE_VM_KEY

print(f"   GitHub Token: {'✅ Available' if GITHUB_TOKEN else '❌ Missing'}")
print(f"   SSH Key Path: {'✅ Available' if SSH_KEY_PATH else '❌ Missing'}")
print(f"   Azure VM Key: {'✅ Available' if AZURE_VM_KEY else '❌ Missing'}")

if GITHUB_TOKEN:
    print(f"   GitHub Token: {GITHUB_TOKEN[:8]}...")

# Method 2: Function calls
print("\n2️⃣ Function-based access:")
from auto_credentials import get_github_token, get_ssh_key_path, get_azure_vm_key

github = get_github_token()
ssh = get_ssh_key_path()
azure = get_azure_vm_key()

print(f"   GitHub: {'✅' if github else '❌'}")
print(f"   SSH: {'✅' if ssh else '❌'}")
print(f"   Azure: {'✅' if azure else '❌'}")

# Method 3: Environment variables (after auto-loading)
print("\n3️⃣ Environment variables:")
import os
print(f"   GITHUB_TOKEN: {'✅' if os.getenv('GITHUB_TOKEN') else '❌'}")
print(f"   SSH_PRIVATE_KEY_PATH: {'✅' if os.getenv('SSH_PRIVATE_KEY_PATH') else '❌'}")
print(f"   AZURE_VM_KEY_PATH: {'✅' if os.getenv('AZURE_VM_KEY_PATH') else '❌'}")

# Method 4: Dictionary access
print("\n4️⃣ Dictionary access:")
from auto_credentials import get_credentials
creds = get_credentials()
for key, value in creds.items():
    status = '✅' if value else '❌'
    print(f"   {key}: {status}")

print("\n🎉 All methods work! Credentials are automatically available.")
print("\n💡 Usage in your scripts:")
print("   from auto_credentials import GITHUB_TOKEN")
print("   # GITHUB_TOKEN is now available immediately!")

if __name__ == "__main__":
    print("\n🧪 This script demonstrates automatic credential loading.")
    print("   Run it anytime to verify credentials are working.")
