#!/bin/bash
# Export port assignments to environment
# Source this file: source ./port_exports.sh

# Read port assignment from JSON file
CONFIG_FILE="config/port_assignments.json"

# Read base port from JSON, fallback to default
BASE_PORT=$(jq -r '.base_port' "$CONFIG_FILE" 2>/dev/null || echo "8090")
BASE_PORT=${BASE_PORT:-8090}

# Calculate client port
CLIENT_PORT=$((BASE_PORT+83))

# Export dynamic ports
export BASE_PORT
export CLIENT_PORT
export NEXT_PORT=$(jq -r '.next_port' "$CONFIG_FILE" 2>/dev/null || echo "$((BASE_PORT+7))")
export HTTP_SERVER_PORT=$(jq -r '.assignments."http-server".port' "$CONFIG_FILE" 2>/dev/null || echo "$BASE_PORT")
export POSTGRES_PORT=$(jq -r '.assignments."postgres".port' "$CONFIG_FILE" 2>/dev/null || echo "$((BASE_PORT+1))")
export MONGO_PORT=$(jq -r '.assignments."mongo".port' "$CONFIG_FILE" 2>/dev/null || echo "$((BASE_PORT+2))")
export REDIS_PORT=$(jq -r '.assignments."redis".port' "$CONFIG_FILE" 2>/dev/null || echo "$((BASE_PORT+3))")
export ELASTICSEARCH_PORT=$(jq -r '.assignments."elasticsearch".port' "$CONFIG_FILE" 2>/dev/null || echo "$((BASE_PORT+4))")
export GRAFANA_PORT=$(jq -r '.assignments."grafana".port' "$CONFIG_FILE" 2>/dev/null || echo "$((BASE_PORT+5))")
export PROMETHEUS_PORT=$(jq -r '.assignments."prometheus".port' "$CONFIG_FILE" 2>/dev/null || echo "$((BASE_PORT+6))")

# Additional alias for SERVER_PORT
export SERVER_PORT=$HTTP_SERVER_PORT
export PORT=$HTTP_SERVER_PORT

# Additional environment variables
export POSTGRES_HOST=localhost
export POSTGRES_DB=testdb
export POSTGRES_USER=user
export POSTGRES_PASSWORD=password
export MONGO_HOST=localhost
export MONGO_DB=testdb
export SQLITE_PATH=/tmp/test.db
export SERVER_HOST=localhost
export SERVER_PROTOCOL=http
export WS_PROTOCOL=ws

echo '🚪 Port assignments exported to environment'
