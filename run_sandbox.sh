#!/bin/bash
# run_sandbox.sh - Quick start script for Claude1 sandbox

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Claude1 Sandbox - Quick Start${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Function to show usage
show_usage() {
    echo "Usage: ./run_sandbox.sh [command]"
    echo ""
    echo "Commands:"
    echo "  build       - Build the Claude1 container"
    echo "  start       - Start the sandbox container"
    echo "  stop        - Stop the sandbox container"
    echo "  test        - Run all tests"
    echo "  shell       - Open interactive shell"
    echo "  logs        - View container logs"
    echo "  clean       - Remove container and volumes"
    echo "  status      - Show container status"
    echo "  dashboard   - Start dashboard (port 8050)"
    echo ""
    echo "Examples:"
    echo "  ./run_sandbox.sh build      # First time setup"
    echo "  ./run_sandbox.sh test       # Run tests"
    echo "  ./run_sandbox.sh shell      # Interactive development"
    exit 1
}

# Check if docker is available
if ! command -v docker &> /dev/null; then
    echo -e "${RED}✗ Docker not found. Please install Docker first.${NC}"
    exit 1
fi

# Check if docker-compose is available
if ! command -v docker-compose &> /dev/null; then
    echo -e "${YELLOW}⚠ docker-compose not found. Using 'docker compose' instead.${NC}"
    DOCKER_COMPOSE="docker compose"
else
    DOCKER_COMPOSE="docker-compose"
fi

# Parse command
COMMAND=${1:-help}

case $COMMAND in
    build)
        echo -e "${GREEN}Building Claude1 container...${NC}"
        $DOCKER_COMPOSE -f docker-compose.claude1.yml build
        echo ""
        echo -e "${GREEN}✓ Build complete!${NC}"
        echo -e "${BLUE}Next: ./run_sandbox.sh test${NC}"
        ;;

    start)
        echo -e "${GREEN}Starting Claude1 container...${NC}"
        $DOCKER_COMPOSE -f docker-compose.claude1.yml up -d
        echo ""
        echo -e "${GREEN}✓ Container started!${NC}"
        echo -e "${BLUE}Use: ./run_sandbox.sh logs (to view logs)${NC}"
        echo -e "${BLUE}Use: ./run_sandbox.sh shell (for interactive shell)${NC}"
        ;;

    stop)
        echo -e "${YELLOW}Stopping Claude1 container...${NC}"
        $DOCKER_COMPOSE -f docker-compose.claude1.yml down
        echo -e "${GREEN}✓ Container stopped${NC}"
        ;;

    test)
        echo -e "${GREEN}Running tests in Claude1 sandbox...${NC}"
        echo ""

        # Start container if not running
        if ! docker ps | grep -q claude1; then
            echo -e "${YELLOW}Starting container...${NC}"
            $DOCKER_COMPOSE -f docker-compose.claude1.yml up -d
            sleep 3
        fi

        # Run tests
        docker exec -it claude1 bash -c "cd /sandbox/navegador && ./run_tests.sh"

        echo ""
        echo -e "${GREEN}✓ Tests completed${NC}"
        ;;

    shell)
        echo -e "${GREEN}Opening interactive shell in Claude1...${NC}"
        echo ""

        # Start container if not running
        if ! docker ps | grep -q claude1; then
            echo -e "${YELLOW}Starting container...${NC}"
            $DOCKER_COMPOSE -f docker-compose.claude1.yml up -d
            sleep 3
        fi

        docker exec -it claude1 bash -c "cd /sandbox/navegador && source /opt/conda/etc/profile.d/conda.sh && conda activate nvg_py13_env && exec bash"
        ;;

    logs)
        echo -e "${GREEN}Viewing Claude1 logs...${NC}"
        echo -e "${YELLOW}(Press Ctrl+C to exit)${NC}"
        echo ""
        docker logs -f claude1
        ;;

    clean)
        echo -e "${RED}⚠ This will remove the container and all data!${NC}"
        read -p "Are you sure? (yes/no): " confirm
        if [ "$confirm" = "yes" ]; then
            echo -e "${YELLOW}Cleaning up...${NC}"
            $DOCKER_COMPOSE -f docker-compose.claude1.yml down -v
            docker rmi navegador-claude1:latest 2>/dev/null || true
            echo -e "${GREEN}✓ Cleanup complete${NC}"
        else
            echo -e "${BLUE}Cancelled${NC}"
        fi
        ;;

    status)
        echo -e "${GREEN}Claude1 Container Status:${NC}"
        echo ""

        if docker ps | grep -q claude1; then
            echo -e "${GREEN}✓ Container is running${NC}"
            echo ""
            docker ps --filter "name=claude1" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
            echo ""
            echo -e "${BLUE}Volumes:${NC}"
            docker volume ls --filter "name=claude1" --format "table {{.Name}}\t{{.Driver}}"
        else
            echo -e "${YELLOW}⚠ Container is not running${NC}"
            echo -e "${BLUE}Use: ./run_sandbox.sh start${NC}"
        fi
        ;;

    dashboard)
        echo -e "${GREEN}Starting dashboard in Claude1...${NC}"
        echo ""

        # Start container if not running
        if ! docker ps | grep -q claude1; then
            echo -e "${YELLOW}Starting container...${NC}"
            $DOCKER_COMPOSE -f docker-compose.claude1.yml up -d
            sleep 3
        fi

        echo -e "${GREEN}✓ Starting dashboard on port 8050...${NC}"
        echo -e "${BLUE}Access at: http://localhost:8050${NC}"
        echo -e "${YELLOW}(Press Ctrl+C to stop)${NC}"
        echo ""

        docker exec -it claude1 bash -c "cd /sandbox/navegador && source /opt/conda/etc/profile.d/conda.sh && conda activate nvg_py13_env && python dashboard.py"
        ;;

    help|--help|-h)
        show_usage
        ;;

    *)
        echo -e "${RED}✗ Unknown command: $COMMAND${NC}"
        echo ""
        show_usage
        ;;
esac

exit 0
