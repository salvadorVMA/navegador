#!/bin/bash
# navegador Project Credential Management
# Simple script to manage all credential operations

set -e  # Exit on any error

show_usage() {
    echo "🔐 navegador Project Credential Management"
    echo "========================================="
    echo "Usage: ./manage_credentials.sh <command>"
    echo ""
    echo "Commands:"
    echo "  setup      - Auto-detect and save credentials to keychain"
    echo "  status     - Check status of stored credentials"
    echo "  load       - Load credentials to environment variables"
    echo "  test       - Test credential access"
    echo "  git        - Configure git with secure credentials"
    echo "  clean      - Remove all stored credentials"
    echo "  help       - Show this help message"
    echo ""
    echo "Examples:"
    echo "  ./manage_credentials.sh setup    # First-time setup"
    echo "  ./manage_credentials.sh status   # Check what's stored"
    echo "  ./manage_credentials.sh test     # Test access"
}

case "${1:-help}" in
    "setup")
        echo "🚀 Setting up credentials..."
        python3 setup_credentials.py
        ;;
    
    "status")
        echo "📊 Checking credential status..."
        python3 credentials_manager.py status
        ;;
    
    "load")
        echo "🔄 Loading credentials to environment..."
        python3 load_credentials.py
        ;;
    
    "test")
        echo "🧪 Testing credential access..."
        python3 load_credentials.py test
        ;;
    
    "git")
        echo "🔧 Configuring git..."
        python3 configure_git.py
        ;;
    
    "clean")
        echo "🧹 Cleaning stored credentials..."
        echo "⚠️  This will remove all stored credentials from keychain"
        read -p "Are you sure? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            # Remove each credential
            security delete-generic-password -s "navegador-project" -a "github-token" 2>/dev/null || true
            security delete-generic-password -s "navegador-project" -a "ssh-key-path" 2>/dev/null || true
            security delete-generic-password -s "navegador-project" -a "azure-vm-key" 2>/dev/null || true
            echo "✅ Credentials removed from keychain"
        else
            echo "❌ Operation cancelled"
        fi
        ;;
    
    "auto"|"quick")
        echo "⚡ Quick auto-setup..."
        python3 credentials_manager.py auto
        ;;
    
    "help"|*)
        show_usage
        ;;
esac

# Reminder about VS Code integration
if [[ "$1" == "setup" ]] && [[ $? -eq 0 ]]; then
    echo ""
    echo "💡 For VS Code integration:"
    echo "   • Open navegador.code-workspace in VS Code"
    echo "   • Credentials auto-load when importing: from auto_credentials import GITHUB_TOKEN"
    echo "   • Use Cmd+Shift+P → 'Tasks: Run Task' → 'Load Credentials' if needed"
fi
