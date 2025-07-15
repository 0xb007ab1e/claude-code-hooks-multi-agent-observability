#!/bin/bash

# Simple startup script without jq dependency
# Uses environment variables or defaults

# Set base port with fallback
BASE_PORT=${BASE_PORT:-8090}
CLIENT_PORT=$((BASE_PORT+83))

# Export dynamic ports
export BASE_PORT
export CLIENT_PORT

# Use environment variables if available, otherwise use calculated defaults
export HTTP_SERVER_PORT=${HTTP_SERVER_PORT:-$BASE_PORT}
export POSTGRES_PORT=${POSTGRES_PORT:-$((BASE_PORT+1))}
export MONGO_PORT=${MONGO_PORT:-$((BASE_PORT+2))}
export REDIS_PORT=${REDIS_PORT:-$((BASE_PORT+3))}
export ELASTICSEARCH_PORT=${ELASTICSEARCH_PORT:-$((BASE_PORT+4))}
export GRAFANA_PORT=${GRAFANA_PORT:-$((BASE_PORT+5))}
export PROMETHEUS_PORT=${PROMETHEUS_PORT:-$((BASE_PORT+6))}

# Additional aliases
export SERVER_PORT=$HTTP_SERVER_PORT
export PORT=$HTTP_SERVER_PORT

# Print assigned ports
echo "BASE_PORT: $BASE_PORT"
echo "CLIENT_PORT: $CLIENT_PORT"
echo "HTTP_SERVER_PORT: $HTTP_SERVER_PORT"

echo 'Launching the services...'
# Add the command to start your application here, for example:
# bun run app.js
# npm start
