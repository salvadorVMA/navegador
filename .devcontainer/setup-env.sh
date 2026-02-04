#!/bin/bash
# Setup script to configure environment for Claude Code and agent development

# Unset ANTHROPIC_API_KEY from shell environment to avoid conflicts with Claude Code
# The key is still available in the Codespace and can be loaded by your agent code
if [ -n "$ANTHROPIC_API_KEY" ]; then
    # Save it to a secure file for your agent to use
    echo "export ANTHROPIC_TEST_KEY=\"$ANTHROPIC_API_KEY\"" > ~/.anthropic_test_key
    chmod 600 ~/.anthropic_test_key

    # Remove from current shell
    unset ANTHROPIC_API_KEY

    # Remove from bash profile to prevent future conflicts
    sed -i '/ANTHROPIC_API_KEY/d' ~/.bashrc 2>/dev/null || true
fi

echo "Environment configured: Claude Code will use claude.ai auth, your agent can load ANTHROPIC_TEST_KEY"
