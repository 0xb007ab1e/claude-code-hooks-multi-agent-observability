# Start System Scripts

This directory contains startup scripts for launching services with dynamic port allocation.

## Files

### `start-system.sh` (Linux/macOS)
The main startup script that reads port assignments from `config/port_assignments.json` and exports them as environment variables.

**Requirements:**
- `jq` command-line JSON processor

**Usage:**
```bash
./scripts/start-system.sh
```

### `start-system-simple.sh` (Linux/macOS)
A simplified version that doesn't require `jq`. It uses environment variables if available, otherwise falls back to calculated defaults.

**Usage:**
```bash
./scripts/start-system-simple.sh
```

### `start-system.bat` (Windows)
Windows batch file equivalent that reads port assignments from JSON.

**Requirements:**
- `jq` for Windows

**Usage:**
```batch
scripts\start-system.bat
```

### `start-system.ps1` (Windows PowerShell)
PowerShell script for Windows that reads port assignments from JSON.

**Usage:**
```powershell
.\scripts\start-system.ps1
```

## Port Configuration

All scripts use the following port allocation strategy:

- **BASE_PORT**: Read from JSON file or defaults to 8090
- **CLIENT_PORT**: Calculated as BASE_PORT + 83
- **SERVICE_PORTS**: Read from `config/port_assignments.json`

## Environment Variables Exported

- `BASE_PORT`: Base port for calculations
- `CLIENT_PORT`: Client application port
- `HTTP_SERVER_PORT`: Main HTTP server port
- `POSTGRES_PORT`: PostgreSQL database port  
- `MONGO_PORT`: MongoDB database port
- `REDIS_PORT`: Redis cache port
- `ELASTICSEARCH_PORT`: Elasticsearch port
- `GRAFANA_PORT`: Grafana dashboard port
- `PROMETHEUS_PORT`: Prometheus metrics port
- `SERVER_PORT`: Alias for HTTP_SERVER_PORT
- `PORT`: Alias for HTTP_SERVER_PORT

## Integration with Port Management

These scripts integrate with the dynamic port management system:

1. **Initialize ports**: `python setup_ports.py init`
2. **Source environment**: `source ./port_exports.sh`
3. **Launch services**: `./scripts/start-system.sh`

## Custom Application Commands

Modify the scripts to add your specific application startup commands:

```bash
# Example additions to the scripts:
bun run app.js
npm start
docker-compose up
```

## Troubleshooting

If you encounter issues:

1. **Check jq installation**: `which jq` or `jq --version`
2. **Verify JSON file exists**: `ls -la config/port_assignments.json`
3. **Test port allocation**: `python setup_ports.py status`
4. **Use simple version**: Try `start-system-simple.sh` if jq is not available
