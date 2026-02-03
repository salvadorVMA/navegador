#!/bin/bash
#
# Agent Testing Toolkit with .env Loading
# This script provides a simple interface for running various agent tests
# and ensures environment variables from .env are loaded
#

set -e

# Script location
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
ENV_CHECKER="${SCRIPT_DIR}/check_env.py"
ANALYZER_SCRIPT="${SCRIPT_DIR}/analyze_agent.sh"
TRACING_SCRIPT="${SCRIPT_DIR}/test_agent_tracing.py"

# ANSI color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
BOLD='\033[1m'
RESET='\033[0m'

# Print banner
print_banner() {
    echo -e "${BOLD}${BLUE}=======================================================${RESET}"
    echo -e "${BOLD}${BLUE}            Navegador Agent Testing Toolkit${RESET}"
    echo -e "${BOLD}${BLUE}=======================================================${RESET}"
    echo
}

# Show usage
show_usage() {
    echo -e "${BOLD}Usage:${RESET} $0 [command] [options]"
    echo
    echo -e "${BOLD}Commands:${RESET}"
    echo -e "  ${GREEN}analyze${RESET}    Run performance analysis on the agent"
    echo -e "  ${GREEN}trace${RESET}      Run agent with tracing enabled"
    echo -e "  ${GREEN}envcheck${RESET}   Check environment variables"
    echo -e "  ${GREEN}help${RESET}       Show this help message"
    echo
    echo -e "${BOLD}Examples:${RESET}"
    echo -e "  $0 analyze \"¿Qué opinan los mexicanos sobre la salud?\""
    echo -e "  $0 analyze --queries \"salud,deporte,educación\" --debug"
    echo -e "  $0 trace \"¿Qué opinan los mexicanos sobre la salud?\""
    echo -e "  $0 envcheck"
    echo
    echo -e "${BOLD}For more detailed documentation:${RESET}"
    echo -e "  - See ${CYAN}AGENT_ANALYZER_README.md${RESET} for analyzer options"
    echo -e "  - See ${CYAN}AGENT_TRACING_README.md${RESET} for tracing options"
    echo
}

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Error: Python 3 is required but not found${RESET}"
    exit 1
fi

# Check if environment checker exists
if [ ! -f "$ENV_CHECKER" ]; then
    echo -e "${RED}Error: Environment checker script not found at ${ENV_CHECKER}${RESET}"
    exit 1
fi

# No arguments provided
if [ $# -eq 0 ]; then
    print_banner
    show_usage
    exit 1
fi

# Parse command
COMMAND=$1
shift

# Process command
case $COMMAND in
    analyze)
        print_banner
        echo -e "${BOLD}${GREEN}Running Agent Performance Analysis${RESET}"
        echo -e "${YELLOW}Command:${RESET} ./analyze_agent.sh $@"
        echo
        python3 $ENV_CHECKER $ANALYZER_SCRIPT "$@"
        ;;
    trace)
        print_banner
        echo -e "${BOLD}${PURPLE}Running Agent with Tracing${RESET}"
        echo -e "${YELLOW}Command:${RESET} python test_agent_tracing.py $@"
        echo
        python3 $ENV_CHECKER python $TRACING_SCRIPT "$@"
        ;;
    envcheck)
        print_banner
        echo -e "${BOLD}${CYAN}Checking Environment Variables${RESET}"
        echo
        python3 $ENV_CHECKER
        ;;
    help)
        print_banner
        show_usage
        ;;
    *)
        echo -e "${RED}Unknown command: ${COMMAND}${RESET}"
        show_usage
        exit 1
        ;;
esac
