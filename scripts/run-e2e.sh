#!/bin/bash

echo "🚀 Starting E2E Test Suite"
echo "========================="

# Get the directory of this script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
# Get the project root directory (parent of scripts)
PROJECT_ROOT="$( cd "$SCRIPT_DIR/.." && pwd )"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

# Function to check if port is in use
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t > /dev/null 2>&1; then
        return 0  # Port is in use
    else
        return 1  # Port is free
    fi
}

# Function to wait for server to be ready
wait_for_server() {
    local max_attempts=30
    local attempt=0
    
    echo -e "${YELLOW}Waiting for server to be ready...${NC}"
    
    while [ $attempt -lt $max_attempts ]; do
        if curl -s -f http://localhost:4000/events/filter-options > /dev/null 2>&1; then
            echo -e "${GREEN}✅ Server is ready!${NC}"
            return 0
        fi
        attempt=$((attempt + 1))
        sleep 1
    done
    
    echo -e "${RED}❌ Server failed to start within ${max_attempts} seconds${NC}"
    return 1
}

# Function to cleanup processes
cleanup() {
    echo -e "\n${YELLOW}Cleaning up...${NC}"
    if [ ! -z "$SERVER_PID" ]; then
        kill $SERVER_PID 2>/dev/null
        wait $SERVER_PID 2>/dev/null
        echo -e "${GREEN}✅ Server stopped${NC}"
    fi
}

# Set up trap to cleanup on exit
trap cleanup EXIT

# Check if server is already running
if check_port 4000; then
    echo -e "${YELLOW}⚠️  Port 4000 is already in use. Attempting to stop existing server...${NC}"
    pkill -f "tsx.*src/index.ts" || true
    sleep 2
    
    if check_port 4000; then
        echo -e "${RED}❌ Failed to stop existing server. Please run './scripts/reset-system.sh' first.${NC}"
        exit 1
    fi
fi

# Start the Node server
echo -e "\n${GREEN}Starting Node server...${NC}"
cd "$PROJECT_ROOT/servers/node"
npm run dev > /dev/null 2>&1 &
SERVER_PID=$!

# Wait for server to be ready
if ! wait_for_server; then
    echo -e "${RED}❌ Server failed to start. Exiting.${NC}"
    exit 1
fi

# Run the Python test suite
echo -e "\n${GREEN}Running Python E2E tests...${NC}"
cd "$PROJECT_ROOT/test-harness"

# Load the test environment
if [ -f "test-env/bin/activate" ]; then
    source test-env/bin/activate
else
    echo -e "${RED}❌ Python test environment not found. Please set up the test environment first.${NC}"
    exit 1
fi

# Run the tests
python3 run_e2e_tests.py
TEST_EXIT_CODE=$?

# Report results
if [ $TEST_EXIT_CODE -eq 0 ]; then
    echo -e "\n${GREEN}✅ E2E tests completed successfully!${NC}"
else
    echo -e "\n${RED}❌ E2E tests failed with exit code $TEST_EXIT_CODE${NC}"
fi

exit $TEST_EXIT_CODE
