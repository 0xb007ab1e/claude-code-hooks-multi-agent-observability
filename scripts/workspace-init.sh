#!/bin/bash

# Workspace initialization script
# This script sets up the development environment

echo "🔧 Initializing workspace..."

# Get the directory of this script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
# Get the project root directory (parent of scripts)
PROJECT_ROOT="$( cd "$SCRIPT_DIR/.." && pwd )"

# Source environment variables
if [ -f "$PROJECT_ROOT/config/.env" ]; then
    echo "📄 Loading environment variables from $PROJECT_ROOT/config/.env"
    source "$PROJECT_ROOT/config/.env"
    echo "✅ Environment variables loaded"
else
    echo "⚠️  Warning: Environment file $PROJECT_ROOT/config/.env not found"
fi

echo "🎉 Workspace initialization complete!"
