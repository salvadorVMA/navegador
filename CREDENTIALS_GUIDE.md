# 🔐 Secure Credentials Management for navegador

This secure credentials system manages GitHub token, SSH key, and Azure VM key using Apple Keychain through dedicated scripts.

## 🎯 What it manages
- **GitHub Personal Access Token** (from `.env` file)
- **SSH Private Key Path** (from `~/.ssh/`)
- **Azure VM Private Key Path** (from `~/.ssh/azure_vm_key`)

## 🚀 Quick Setup

### 1. One-Command Setup (Recommended)
```bash
./manage_credentials.sh setup
```

### 2. Alternative Commands
```bash
# Auto-detect and save
./manage_credentials.sh auto

# Check status
./manage_credentials.sh status

# Test access
./manage_credentials.sh test

# Configure git
./manage_credentials.sh git
```

## 📁 Available Scripts

| Script | Purpose |
|--------|---------|
| `manage_credentials.sh` | Main management interface |
| `setup_credentials.py` | Interactive setup with auto-detection |
| `load_credentials.py` | Load credentials to environment |
| `configure_git.py` | Configure git with secure credentials |
| `credentials_manager.py` | Core credential management |

## 🔄 Usage Examples

### Basic Setup
```bash
# First time setup
./manage_credentials.sh setup

# Check what's stored
./manage_credentials.sh status

# Test access
./manage_credentials.sh test
```

### Git Configuration
```bash
# Configure git to use secure credentials
./manage_credentials.sh git

# Show current git config
python configure_git.py show
```

### Environment Loading
```bash
# Load to environment variables
python load_credentials.py

# Test credential access
python load_credentials.py test
```

## 🔒 Security Features

✅ **Auto-Detection**: Finds credentials from known locations  
✅ **Limited Scope**: Only manages the 3 specific credentials  
✅ **No Notebook Logic**: Pure standalone scripts  
✅ **Codacy Verified**: All scripts pass security scans  
✅ **Apple Keychain**: Uses macOS native secure storage  

## 🛠 Command Reference

### Management Script (`./manage_credentials.sh`)
- `setup` - Auto-detect and save credentials
- `status` - Check credential status  
- `load` - Load credentials to environment
- `test` - Test credential access
- `git` - Configure git with credentials
- `clean` - Remove all stored credentials
- `help` - Show usage information

### Direct Python Scripts
- `python setup_credentials.py` - Interactive setup
- `python load_credentials.py` - Load to environment
- `python load_credentials.py test` - Test access
- `python configure_git.py` - Configure git
- `python credentials_manager.py auto` - Auto-detect
- `python credentials_manager.py status` - Check status

## 🔄 Environment Variables

When loaded, credentials are available as:
- `GITHUB_TOKEN` - Your GitHub Personal Access Token
- `SSH_PRIVATE_KEY_PATH` - Path to your SSH private key  
- `AZURE_VM_KEY_PATH` - Path to your Azure VM private key

## 🚨 Important Notes

1. **No Notebook Integration**: All credential logic is in standalone scripts
2. **Auto-Detection**: System finds GitHub token in `.env`, Azure key in `~/.ssh/azure_vm_key`
3. **Private Repos**: Since repos are private and low-key, credentials are auto-saved
4. **macOS Only**: Uses Apple Keychain - requires macOS

## 🔧 Troubleshooting

**Script Permission Error:**
```bash
chmod +x manage_credentials.sh
```

**Keychain Access Denied:**
- Go to System Preferences > Security & Privacy > Privacy
- Add Terminal.app if needed

**Credentials Not Found:**
```bash
./manage_credentials.sh setup  # Run setup first
```

**Git Configuration Issues:**
```bash
./manage_credentials.sh git    # Configure git
python configure_git.py show   # Check current config
```
