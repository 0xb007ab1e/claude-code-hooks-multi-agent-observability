#!/bin/bash

# Read port assignment from JSON file
CONFIG_FILE="config/port_assignments.json"
BASE_PORT=$(jq -r '.base_port' "$CONFIG_FILE")

# Fallback to default if not set
BASE_PORT=${BASE_PORT:-8090}
CLIENT_PORT=$((BASE_PORT+83))

# Export dynamic ports
export BASE_PORT
export CLIENT_PORT
export HTTP_SERVER_PORT=$(jq -r '.assignments."http-server".port' "$CONFIG_FILE")
export POSTGRES_PORT=$(jq -r '.assignments."postgres".port' "$CONFIG_FILE")
export MONGO_PORT=$(jq -r '.assignments."mongo".port' "$CONFIG_FILE")

# Print assigned ports
echo "BASE_PORT: $BASE_PORT"
echo "CLIENT_PORT: $CLIENT_PORT"
echo "HTTP_SERVER_PORT: $HTTP_SERVER_PORT"

echo 'Launching the services...'
# Add the command to start your application here, for example:
# bun run app.js
# npm start

