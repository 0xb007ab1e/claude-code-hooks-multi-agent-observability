#!/bin/bash

# =============================================================================
# CROSS-PLATFORM ENVIRONMENT VARIABLE LOADER (Shell/Bash)
# =============================================================================
# This script loads environment variables from the centralized .env file
# and exports them for use by any stack/application in the repository.
#
# Usage:
#   source config/env-helpers/load-env.sh
#   source config/env-helpers/load-env.sh /path/to/custom/.env
#
# Author: Centralized Configuration Management System
# =============================================================================

# Set script options for safety
set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to validate required variables
validate_required_vars() {
    local missing_vars=()
    
    # Check required variables
    required_vars=(
        "ANTHROPIC_API_KEY"
        "OPENAI_API_KEY"
        "ELEVENLABS_API_KEY"
        "PORT"
        "NODE_ENV"
    )
    
    for var in "${required_vars[@]}"; do
        if [[ -z "${!var:-}" ]]; then
            missing_vars+=("$var")
        fi
    done
    
    if [[ ${#missing_vars[@]} -gt 0 ]]; then
        print_error "Missing required environment variables:"
        for var in "${missing_vars[@]}"; do
            echo "  - $var"
        done
        return 1
    fi
    
    return 0
}

# Function to set default values
set_defaults() {
    # Set default values for optional variables
    export ANTHROPIC_MODEL="${ANTHROPIC_MODEL:-claude-3-5-haiku-20241022}"
    export OPENAI_MODEL="${OPENAI_MODEL:-gpt-4.1-nano}"
    export OPENAI_TTS_MODEL="${OPENAI_TTS_MODEL:-gpt-4o-mini-tts}"
    export OPENAI_TTS_VOICE="${OPENAI_TTS_VOICE:-nova}"
    export ELEVENLABS_MODEL="${ELEVENLABS_MODEL:-eleven_turbo_v2_5}"
    export ELEVENLABS_VOICE_ID="${ELEVENLABS_VOICE_ID:-WejK3H1m7MI9CHnIjW9K}"
    export ENGINEER_NAME="${ENGINEER_NAME:-Dan}"
    export DATABASE_PATH="${DATABASE_PATH:-events.db}"
    export CORS_ORIGINS="${CORS_ORIGINS:-*}"
    export RATE_LIMIT_WINDOW_MS="${RATE_LIMIT_WINDOW_MS:-900000}"
    export RATE_LIMIT_MAX_REQUESTS="${RATE_LIMIT_MAX_REQUESTS:-100}"
    export WS_HEARTBEAT_INTERVAL="${WS_HEARTBEAT_INTERVAL:-30000}"
    export LOG_LEVEL="${LOG_LEVEL:-info}"
    export CLAUDE_HOOKS_LOG_DIR="${CLAUDE_HOOKS_LOG_DIR:-logs}"
    export VITE_MAX_EVENTS_TO_DISPLAY="${VITE_MAX_EVENTS_TO_DISPLAY:-100}"
    export VITE_WEBSOCKET_URL="${VITE_WEBSOCKET_URL:-ws://localhost:4000/stream}"
    export DB_HOST="${DB_HOST:-localhost}"
    export DB_PORT="${DB_PORT:-5432}"
    export DB_NAME="${DB_NAME:-observability}"
    export COMPOSE_PROJECT_NAME="${COMPOSE_PROJECT_NAME:-observability}"
    export DOCKER_NETWORK_NAME="${DOCKER_NETWORK_NAME:-observability-network}"
    export DEV_MODE="${DEV_MODE:-true}"
    export DEBUG_MODE="${DEBUG_MODE:-false}"
    export VERBOSE_LOGGING="${VERBOSE_LOGGING:-false}"
    export HOT_RELOAD="${HOT_RELOAD:-true}"
    export WATCH_FILES="${WATCH_FILES:-true}"
    
    # Stack-specific port defaults
    export GO_PORT="${GO_PORT:-4001}"
    export PYTHON_PORT="${PYTHON_PORT:-4002}"
    export RUST_PORT="${RUST_PORT:-4003}"
    export DOTNET_PORT="${DOTNET_PORT:-4004}"
}

# Function to load environment variables from .env file
load_env_file() {
    local env_file="$1"
    
    if [[ ! -f "$env_file" ]]; then
        print_error "Environment file not found: $env_file"
        return 1
    fi
    
    print_info "Loading environment variables from: $env_file"
    
    # Load variables from .env file
    while IFS='=' read -r key value; do
        # Skip empty lines and comments
        [[ -z "$key" || "$key" =~ ^[[:space:]]*# ]] && continue
        
        # Remove leading/trailing whitespace
        key=$(echo "$key" | xargs)
        value=$(echo "$value" | xargs)
        
        # Remove quotes if present
        value=$(echo "$value" | sed -e 's/^"//' -e 's/"$//' -e "s/^'//" -e "s/'$//")
        
        # Export the variable
        export "$key"="$value"
    done < "$env_file"
    
    return 0
}

# Function to print loaded environment summary
print_env_summary() {
    print_info "Environment Summary:"
    echo "  NODE_ENV: ${NODE_ENV}"
    echo "  PORT: ${PORT}"
    echo "  DATABASE_PATH: ${DATABASE_PATH}"
    echo "  LOG_LEVEL: ${LOG_LEVEL}"
    echo "  CORS_ORIGINS: ${CORS_ORIGINS}"
    
    # Check if API keys are set (without exposing them)
    if [[ -n "${ANTHROPIC_API_KEY:-}" ]]; then
        echo "  ANTHROPIC_API_KEY: ✓ Set"
    else
        echo "  ANTHROPIC_API_KEY: ✗ Not set"
    fi
    
    if [[ -n "${OPENAI_API_KEY:-}" ]]; then
        echo "  OPENAI_API_KEY: ✓ Set"
    else
        echo "  OPENAI_API_KEY: ✗ Not set"
    fi
    
    if [[ -n "${ELEVENLABS_API_KEY:-}" ]]; then
        echo "  ELEVENLABS_API_KEY: ✓ Set"
    else
        echo "  ELEVENLABS_API_KEY: ✗ Not set"
    fi
}

# Main function
main() {
    # Determine the root directory (where this script is located)
    local script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    local repo_root="$(cd "$script_dir/../.." && pwd)"
    
    # Determine .env file path
    local env_file="${1:-$repo_root/.env}"
    
    # If .env doesn't exist, try .env.example
    if [[ ! -f "$env_file" ]]; then
        local example_file="$repo_root/.env.example"
        if [[ -f "$example_file" ]]; then
            print_warning ".env file not found, using .env.example"
            print_warning "Please copy .env.example to .env and configure your values"
            env_file="$example_file"
        else
            print_error "No .env or .env.example file found in: $repo_root"
            return 1
        fi
    fi
    
    # Load environment variables
    if load_env_file "$env_file"; then
        set_defaults
        
        # Validate required variables
        if validate_required_vars; then
            print_success "Environment variables loaded successfully"
            print_env_summary
        else
            print_error "Environment validation failed"
            return 1
        fi
    else
        print_error "Failed to load environment file"
        return 1
    fi
}

# Only run main if script is being sourced (not executed)
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    print_error "This script should be sourced, not executed directly"
    print_info "Usage: source config/env-helpers/load-env.sh"
    exit 1
fi

# Run main function
main "$@"
