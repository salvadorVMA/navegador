"""
Helper module to load Anthropic test API key for agent development.

Usage in your agent code:
    from load_test_key import get_anthropic_key

    api_key = get_anthropic_key()
"""

import os
from pathlib import Path


def get_anthropic_key():
    """
    Load the Anthropic API key for testing.

    This function tries multiple sources in order:
    1. ANTHROPIC_TEST_KEY environment variable (set by setup-env.sh)
    2. ~/.anthropic_test_key file (created by setup-env.sh)
    3. ANTHROPIC_API_KEY environment variable (fallback)

    Returns:
        str: The API key

    Raises:
        ValueError: If no API key is found
    """
    # Try environment variable first
    key = os.environ.get('ANTHROPIC_TEST_KEY')
    if key:
        return key

    # Try loading from file
    key_file = Path.home() / '.anthropic_test_key'
    if key_file.exists():
        with open(key_file) as f:
            for line in f:
                if 'ANTHROPIC_TEST_KEY=' in line:
                    return line.split('=', 1)[1].strip().strip('"')

    # Fallback to direct env var (shouldn't happen in Codespaces)
    key = os.environ.get('ANTHROPIC_API_KEY')
    if key:
        return key

    raise ValueError(
        "No Anthropic API key found. Make sure ANTHROPIC_API_KEY is set "
        "in your Codespaces secrets."
    )


if __name__ == '__main__':
    # Test the function
    try:
        key = get_anthropic_key()
        print(f"✓ API key loaded successfully (starts with: {key[:15]}...)")
    except ValueError as e:
        print(f"✗ Error: {e}")
