#!/bin/bash
# VS Code Environment Setup for navegador
# Automatically loads credentials when VS Code starts

# Load credentials to environment variables
cd "/Users/salvadorVMA/Google Drive/01 Proyectos/2025/navegador"
python3 load_credentials.py >/dev/null 2>&1

# Export for VS Code integrated terminal
export GITHUB_TOKEN=$(python3 -c "from load_credentials import get_github_token; print(get_github_token() or '')" 2>/dev/null)
export SSH_PRIVATE_KEY_PATH=$(python3 -c "from load_credentials import get_ssh_key_path; print(get_ssh_key_path() or '')" 2>/dev/null)
export AZURE_VM_KEY_PATH=$(python3 -c "from load_credentials import get_azure_vm_key; print(get_azure_vm_key() or '')" 2>/dev/null)

echo "🔐 Credentials loaded for VS Code session"
