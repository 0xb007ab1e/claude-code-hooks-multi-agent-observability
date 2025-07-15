#!/bin/bash

# start_env.sh - Unified development environment launcher
# Activates venv, exports .env variables, and runs launch_dev_env.py

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get project root (parent of scripts directory)
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_PATH="$PROJECT_ROOT/venv"
ENV_FILE="$PROJECT_ROOT/.env"

echo -e "${BLUE}🚀 Starting Claude Code Hooks Development Environment${NC}"
echo -e "${BLUE}=================================================${NC}"

# Function to check if virtual environment exists
check_venv() {
    if [ ! -d "$VENV_PATH" ]; then
        echo -e "${YELLOW}📦 Virtual environment not found. Creating...${NC}"
        python3 -m venv "$VENV_PATH"
        echo -e "${GREEN}✅ Virtual environment created at $VENV_PATH${NC}"
    else
        echo -e "${GREEN}📦 Using existing virtual environment: $VENV_PATH${NC}"
    fi
}

# Function to activate virtual environment
activate_venv() {
    if [ -f "$VENV_PATH/bin/activate" ]; then
        echo -e "${BLUE}🔧 Activating virtual environment...${NC}"
        source "$VENV_PATH/bin/activate"
        echo -e "${GREEN}✅ Virtual environment activated${NC}"
    else
        echo -e "${RED}❌ Virtual environment activation script not found${NC}"
        exit 1
    fi
}

# Function to export environment variables from .env file
export_env_vars() {
    if [ -f "$ENV_FILE" ]; then
        echo -e "${BLUE}🔧 Loading environment variables from .env...${NC}"
        # Export variables from .env file, ignoring comments and empty lines
        set -o allexport
        source "$ENV_FILE"
        set +o allexport
        echo -e "${GREEN}✅ Environment variables loaded${NC}"
    else
        echo -e "${YELLOW}⚠️  .env file not found at $ENV_FILE${NC}"
        echo -e "${YELLOW}   You may need to create one from .env.sample${NC}"
        if [ -f "$PROJECT_ROOT/.env.sample" ]; then
            echo -e "${YELLOW}   Run: cp .env.sample .env${NC}"
        fi
    fi
}

# Function to run the Python launcher
run_launcher() {
    echo -e "${BLUE}🎯 Running Python development environment launcher...${NC}"
    cd "$PROJECT_ROOT"
    
    # Check if launch_dev_env.py exists
    if [ ! -f "scripts/launch_dev_env.py" ]; then
        echo -e "${RED}❌ launch_dev_env.py not found in scripts directory${NC}"
        exit 1
    fi
    
    # Run the Python launcher
    python scripts/launch_dev_env.py "$@"
}

# Function to show usage
show_usage() {
    echo -e "${BLUE}Usage: $0 [OPTIONS]${NC}"
    echo -e "  Options are passed through to launch_dev_env.py:"
    echo -e "    --no-tmux        Skip tmux session creation"
    echo -e "    --config-only    Only create configuration files"
    echo -e "    --install-deps   Install dependencies and exit"
    echo -e "    --help          Show this help message"
}

# Parse command line arguments
if [[ "$1" == "--help" ]]; then
    show_usage
    exit 0
fi

# Main execution flow
main() {
    echo -e "${BLUE}📁 Project root: $PROJECT_ROOT${NC}"
    
    # Check and create virtual environment
    check_venv
    
    # Activate virtual environment
    activate_venv
    
    # Export environment variables
    export_env_vars
    
    # Run the Python launcher with all passed arguments
    run_launcher "$@"
}

# Trap to handle interruption
trap 'echo -e "\n${YELLOW}🛑 Interrupted by user${NC}"; exit 1' INT

# Run main function with all arguments
main "$@"
