#!/bin/bash
#
# LangSmith Connection Test with .env Loading
#

set -e

# Script location
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
ENV_CHECKER="${SCRIPT_DIR}/check_env.py"
LANGSMITH_TEST="${SCRIPT_DIR}/test_langsmith_connection.py"

# Print banner
echo "======================================================="
echo "         LangSmith Connection Test (with .env)"
echo "======================================================="
echo

# Check if environment checker exists
if [ ! -f "$ENV_CHECKER" ]; then
    echo "Error: Environment checker script not found"
    exit 1
fi

# Run environment checker with the LangSmith test
python3 $ENV_CHECKER python3 $LANGSMITH_TEST
