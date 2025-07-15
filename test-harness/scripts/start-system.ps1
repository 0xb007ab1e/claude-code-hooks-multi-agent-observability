# PowerShell script to start system with dynamic ports

# Read port assignment from JSON file
$CONFIG_FILE = "config/port_assignments.json"

# Read configuration
$config = Get-Content $CONFIG_FILE | ConvertFrom-Json
$BASE_PORT = $config.base_port

# Fallback to default if not set
if (-not $BASE_PORT) {
    $BASE_PORT = 8090
}

# Calculate client port
$CLIENT_PORT = $BASE_PORT + 83

# Export dynamic ports
$env:BASE_PORT = $BASE_PORT
$env:CLIENT_PORT = $CLIENT_PORT
$env:HTTP_SERVER_PORT = $config.assignments."http-server".port
$env:POSTGRES_PORT = $config.assignments."postgres".port
$env:MONGO_PORT = $config.assignments."mongo".port

# Print assigned ports
Write-Host "BASE_PORT: $BASE_PORT"
Write-Host "CLIENT_PORT: $CLIENT_PORT"
Write-Host "HTTP_SERVER_PORT: $($env:HTTP_SERVER_PORT)"

Write-Host "Launching the services..."
# Add the command to start your application here, for example:
# bun run app.js
# npm start
