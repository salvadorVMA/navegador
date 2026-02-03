#!/bin/bash
# 
# Agent Performance Analysis Wrapper
# This script is a simple wrapper around the agent performance analyzer
# that handles errors and provides a cleaner interface.
#

set -e

# Script location
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
SIMPLE_SCRIPT="${SCRIPT_DIR}/analyze_agent_performance_simple.py"

# Check if simple script exists
if [ ! -f "$SIMPLE_SCRIPT" ]; then
    echo "❌ Error: Simple analyzer script not found at ${SIMPLE_SCRIPT}"
    exit 1
fi

# Make script executable
chmod +x "$SIMPLE_SCRIPT"

# Print banner
echo "======================================================="
echo "Navegador Agent Performance Analyzer"
echo "======================================================="
echo

# Check if query was provided
if [ $# -eq 0 ]; then
    echo "Usage: $0 \"<query>\" [options]"
    echo
    echo "Options:"
    echo "  --debug      Enable debug mode"
    echo "  --queries    Comma-separated list of queries"
    echo "  --datasets   Comma-separated list of datasets"
    echo "  --language   Query language (default: es)"
    echo
    echo "Example: $0 \"¿Qué opinan los mexicanos sobre la salud?\""
    echo "Example: $0 --queries \"salud,deporte,educación\" --debug"
    exit 1
fi

# Run the script with all arguments
echo "🔄 Starting analysis..."
echo

python "$SIMPLE_SCRIPT" "$@"

# Exit with the status of the Python script
exit $?
