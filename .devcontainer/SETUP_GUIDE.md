# Codespaces Setup Guide

This guide explains how to set up automatic Claude Code authentication in GitHub Codespaces.

## Setup Steps

### 1. Add GitHub Codespaces Secrets

Go to your repository: **Settings → Secrets and variables → Codespaces**

Add these two secrets:

#### Secret 1: `CLAUDE_CREDENTIALS_BASE64`
- **Description**: Claude Code authentication credentials (base64 encoded)
- **Value**: The base64 string provided by Claude Code

#### Secret 2: `ANTHROPIC_API_KEY` (optional - for your agent testing)
- **Description**: API key for testing your agent with Anthropic models
- **Value**: Your Anthropic API key from console.anthropic.com

### 2. Rebuild your Codespace

After adding the secrets:
- Open your Codespace
- Press `Cmd/Ctrl + Shift + P`
- Run: **"Codespaces: Rebuild Container"**

### 3. Verify Setup

After rebuild, Claude Code should automatically authenticate. Test it:

```bash
claude
```

You should NOT see any authentication errors.

## Using the API Key in Your Agent

The `ANTHROPIC_API_KEY` is kept separate from Claude Code to avoid conflicts.

### Option 1: Use the helper module (recommended)

```python
from .devcontainer.load_test_key import get_anthropic_key

api_key = get_anthropic_key()

# Use with Anthropic SDK
from anthropic import Anthropic
client = Anthropic(api_key=api_key)
```

### Option 2: Load manually from file

```python
import os
from pathlib import Path

key_file = Path.home() / '.anthropic_test_key'
if key_file.exists():
    with open(key_file) as f:
        for line in f:
            if 'ANTHROPIC_TEST_KEY=' in line:
                api_key = line.split('=', 1)[1].strip().strip('"')
```

### Option 3: Load inline when running

```bash
source ~/.anthropic_test_key && python your_agent.py
```

## How It Works

1. **Codespace starts** → secrets are available as environment variables
2. **postCreateCommand runs** → decodes and saves Claude credentials
3. **setup-env.sh runs** → moves ANTHROPIC_API_KEY to separate file
4. **Result**:
   - Claude Code uses claude.ai auth ✓
   - Your agent can load the API key from file ✓
   - No conflicts ✓

## Troubleshooting

### Still seeing auth conflict?

Check if the API key is in your environment:
```bash
env | grep ANTHROPIC_API_KEY
```

If found, unset it:
```bash
unset ANTHROPIC_API_KEY
```

### Claude Code authentication failed?

Verify credentials file exists:
```bash
cat ~/.claude/.credentials.json
```

If missing, the secret might not be set correctly. Check:
1. Is `CLAUDE_CREDENTIALS_BASE64` in your Codespaces secrets?
2. Did you rebuild the container after adding the secret?

### Can't load API key in agent?

Test the helper:
```bash
python .devcontainer/load_test_key.py
```

Should output: `✓ API key loaded successfully`
