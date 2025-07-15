# Dynamic Port Management System

## Overview

The Dynamic Port Management System automatically assigns ports sequentially starting from a configurable base port, eliminating hard-coded port conflicts and simplifying service orchestration.

## Key Features

- **Sequential Port Assignment**: Ports are assigned sequentially starting from `BASE_PORT` (default: 4000)
- **Persistent Storage**: Port assignments are stored in `config/port_assignments.json`
- **Thread-Safe**: Uses locking mechanisms for concurrent access
- **Environment Integration**: Automatically generates environment variables
- **Docker Compose Support**: Generates compose-compatible environment files

## Port Assignment Rules

1. **Base Port**: First service gets `BASE_PORT` (4000)
2. **Sequential Assignment**: Each new service gets `BASE_PORT + n` where n increments
3. **Persistent Assignment**: Once assigned, services keep their ports until reset
4. **Next Available Tracking**: System tracks the next available port for new services

## Current Port Assignments

| Service        | Port | Purpose                    |
|---------------|------|----------------------------|
| http-server   | 4000 | Main HTTP Server          |
| postgres      | 4001 | PostgreSQL Database       |
| mongo         | 4002 | MongoDB Database          |
| redis         | 4003 | Redis Cache (future)      |
| elasticsearch | 4004 | Elasticsearch (future)    |
| grafana       | 4005 | Grafana Dashboard (future)|
| prometheus    | 4006 | Prometheus Metrics (future)|

**Next Available Port**: 4007

## Files and Configuration

### Core Files

- `config/port_manager.py` - Port management logic
- `config/port_assignments.json` - Persistent port storage
- `setup_ports.py` - Port management CLI tool

### Generated Files

- `.env` - Environment variables for Python applications
- `.env.compose` - Docker Compose environment variables
- `port_exports.sh` - Shell script for exporting variables

## Usage

### Initialize Port System

```bash
# Initialize port assignments and generate config files
python setup_ports.py init
```

### Check Current Status

```bash
# View current port assignments
python setup_ports.py status
```

### Export Environment Variables

```bash
# Generate shell export script
python setup_ports.py export

# Source the generated script
source ./port_exports.sh
```

### Reset All Assignments

```bash
# Reset all port assignments (use with caution)
python setup_ports.py reset
```

## Integration with Applications

### Python Applications

```python
from config.port_manager import get_port, assign_port

# Get assigned port for a service
http_port = get_port('http-server')

# Assign a new port
new_port = assign_port('my-service', 'My Service Description')
```

### Docker Compose

```yaml
version: '3.8'
services:
  postgres:
    image: postgres:15
    ports:
      - "${POSTGRES_PORT}:${POSTGRES_PORT}"
  
  mongo:
    image: mongo:7.0
    ports:
      - "${MONGO_PORT}:${MONGO_PORT}"
```

### Environment Variables

The system automatically generates these environment variables:

```bash
# Base configuration
BASE_PORT=4000
NEXT_PORT=4007

# Service-specific ports
HTTP_SERVER_PORT=4000
POSTGRES_PORT=4001
MONGO_PORT=4002
REDIS_PORT=4003
ELASTICSEARCH_PORT=4004
GRAFANA_PORT=4005
PROMETHEUS_PORT=4006
```

## Migration from Hard-coded Ports

### Before (Hard-coded)
```python
# Old approach
port = int(os.getenv("SERVER_PORT", "4000"))
postgres_port = int(os.getenv("POSTGRES_PORT", "5432"))
mongo_port = int(os.getenv("MONGO_PORT", "27017"))
```

### After (Dynamic)
```python
# New approach
from config.port_manager import get_port, assign_port

port = int(os.getenv("SERVER_PORT", str(get_port('http-server') or assign_port('http-server', 'Main HTTP Server'))))
postgres_port = int(os.getenv("POSTGRES_PORT", str(get_port('postgres') or assign_port('postgres', 'PostgreSQL Database'))))
mongo_port = int(os.getenv("MONGO_PORT", str(get_port('mongo') or assign_port('mongo', 'MongoDB Database'))))
```

## Benefits

1. **No Port Conflicts**: Sequential assignment prevents conflicts
2. **Easy Scaling**: Adding new services is automatic
3. **Environment Consistency**: Same port assignments across environments
4. **Documentation**: Built-in tracking of port purposes
5. **Docker Integration**: Seamless Docker Compose support

## Best Practices

1. **Initialize Once**: Run `python setup_ports.py init` when setting up the project
2. **Source Environment**: Always source `port_exports.sh` before running tests
3. **Use Descriptive Names**: Provide clear service names and purposes
4. **Version Control**: Commit `port_assignments.json` to maintain consistency
5. **Reset Carefully**: Only reset port assignments during major restructuring

## Troubleshooting

### Port Already in Use
```bash
# Check what's using a port
lsof -i :4000

# Kill process using port
kill -9 $(lsof -t -i:4000)
```

### Reset if Needed
```bash
# Reset all port assignments
python setup_ports.py reset

# Reinitialize
python setup_ports.py init
```

### Check Environment
```bash
# Verify environment variables are set
env | grep PORT

# Re-source if needed
source ./port_exports.sh
```

## Future Enhancements

- [ ] Port range validation
- [ ] Service health checking
- [ ] Automatic port conflict detection
- [ ] Integration with service discovery
- [ ] Load balancer configuration
- [ ] Monitoring and alerting

## API Reference

### PortManager Class

```python
class PortManager:
    def __init__(self, base_port: int = 4000)
    def assign_port(self, service_name: str, purpose: str = "") -> int
    def get_port(self, service_name: str) -> Optional[int]
    def release_port(self, service_name: str) -> bool
    def reset_assignments(self) -> None
    def export_env_vars(self) -> Dict[str, str]
```

### Convenience Functions

```python
def assign_port(service_name: str, purpose: str = "") -> int
def get_port(service_name: str) -> Optional[int]
def get_next_port() -> int
def reset_ports() -> None
def export_env_vars() -> Dict[str, str]
```

## Support

For issues or questions about the port management system:

1. Check current status: `python setup_ports.py status`
2. Review logs in `config/port_assignments.json`
3. Reset and reinitialize if needed
4. Consult this documentation for best practices
