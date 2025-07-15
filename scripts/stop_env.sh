#!/bin/bash

# stop_env.sh - Unified development environment teardown
# Kills tmux session and background services

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get project root (parent of scripts directory)
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo -e "${BLUE}🛑 Stopping Claude Code Hooks Development Environment${NC}"
echo -e "${BLUE}=================================================${NC}"

# Function to kill tmux session
kill_tmux_session() {
    local session_name="claude-dev-env"
    
    echo -e "${BLUE}🔍 Checking for tmux session: $session_name${NC}"
    
    if tmux has-session -t "$session_name" 2>/dev/null; then
        echo -e "${YELLOW}⚡ Killing tmux session: $session_name${NC}"
        tmux kill-session -t "$session_name"
        echo -e "${GREEN}✅ Tmux session killed${NC}"
    else
        echo -e "${YELLOW}ℹ️  No tmux session '$session_name' found${NC}"
    fi
}

# Function to kill background services
kill_background_services() {
    echo -e "${BLUE}🔍 Stopping background services...${NC}"
    
    # Kill processes on common development ports
    local ports=(3000 4000 5173 8080 8081)
    
    for port in "${ports[@]}"; do
        local pid=$(lsof -ti :$port 2>/dev/null || true)
        if [ ! -z "$pid" ]; then
            echo -e "${YELLOW}⚡ Killing process on port $port (PID: $pid)${NC}"
            kill -9 "$pid" 2>/dev/null || true
            echo -e "${GREEN}✅ Process on port $port killed${NC}"
        fi
    done
    
    # Kill specific processes by name
    local processes=("bun" "node" "hooks-proxy" "superclaude-monitor")
    
    for process in "${processes[@]}"; do
        local pids=$(pgrep -f "$process" 2>/dev/null || true)
        if [ ! -z "$pids" ]; then
            echo -e "${YELLOW}⚡ Killing $process processes: $pids${NC}"
            pkill -f "$process" 2>/dev/null || true
            echo -e "${GREEN}✅ $process processes killed${NC}"
        fi
    done
}

# Function to clean up temporary files
cleanup_temp_files() {
    echo -e "${BLUE}🧹 Cleaning up temporary files...${NC}"
    
    # Clean up log files
    rm -f /tmp/claude-hooks-*.log 2>/dev/null || true
    
    # Clean up named pipes
    rm -f /tmp/claude-hooks-pipe 2>/dev/null || true
    
    # Clean up any lock files
    rm -f "$PROJECT_ROOT"/*.lock 2>/dev/null || true
    
    echo -e "${GREEN}✅ Temporary files cleaned up${NC}"
}

# Function to show running processes (for debugging)
show_remaining_processes() {
    echo -e "${BLUE}🔍 Checking for remaining processes...${NC}"
    
    # Check for any remaining processes on development ports
    local ports=(3000 4000 5173 8080 8081)
    local found_processes=false
    
    for port in "${ports[@]}"; do
        local pid=$(lsof -ti :$port 2>/dev/null || true)
        if [ ! -z "$pid" ]; then
            echo -e "${YELLOW}⚠️  Process still running on port $port (PID: $pid)${NC}"
            found_processes=true
        fi
    done
    
    # Check for tmux sessions
    if tmux list-sessions 2>/dev/null | grep -q "claude"; then
        echo -e "${YELLOW}⚠️  Claude-related tmux sessions still active:${NC}"
        tmux list-sessions 2>/dev/null | grep "claude" || true
        found_processes=true
    fi
    
    if [ "$found_processes" = false ]; then
        echo -e "${GREEN}✅ No remaining processes found${NC}"
    fi
}

# Function to show usage
show_usage() {
    echo -e "${BLUE}Usage: $0 [OPTIONS]${NC}"
    echo -e "  Options:"
    echo -e "    --force         Force kill all processes without confirmation"
    echo -e "    --check         Only check for running processes, don't kill"
    echo -e "    --help          Show this help message"
}

# Function to confirm action
confirm_action() {
    if [[ "$1" == "--force" ]]; then
        return 0
    fi
    
    echo -e "${YELLOW}Are you sure you want to stop all development services? (y/N)${NC}"
    read -r response
    case "$response" in
        [yY][eE][sS]|[yY])
            return 0
            ;;
        *)
            echo -e "${BLUE}Operation cancelled${NC}"
            exit 0
            ;;
    esac
}

# Main execution flow
main() {
    echo -e "${BLUE}📁 Project root: $PROJECT_ROOT${NC}"
    
    # Parse command line arguments
    case "$1" in
        --help)
            show_usage
            exit 0
            ;;
        --check)
            show_remaining_processes
            exit 0
            ;;
        --force)
            echo -e "${YELLOW}🔥 Force mode enabled${NC}"
            ;;
        *)
            confirm_action "$1"
            ;;
    esac
    
    # Stop all services
    kill_tmux_session
    kill_background_services
    cleanup_temp_files
    
    echo -e "${GREEN}🎉 Development environment stopped successfully!${NC}"
    echo -e "${BLUE}💡 Use './scripts/start_env.sh' to restart the environment${NC}"
    
    # Show any remaining processes
    show_remaining_processes
}

# Trap to handle interruption
trap 'echo -e "\n${YELLOW}🛑 Interrupted by user${NC}"; exit 1' INT

# Run main function with all arguments
main "$@"
