# Ports Module

A reusable sequential port allocator utility for finding available ports on a host.

## Overview

The `ports.py` module provides functionality to find sequential available ports on a host system. This is useful for orchestrator scripts and build-time templating that need to dynamically allocate ports for services.

## API

### `find_sequential_ports(base: int = 8090, count: int = 1, host: str = "0.0.0.0") -> List[int]`

Finds sequential available ports starting from a base port.

**Parameters:**
- `base`: Starting port number (default: 8090)
- `count`: Number of sequential ports to find (default: 1)
- `host`: Host address to bind to (default: "0.0.0.0")

**Returns:**
- List of available sequential port numbers of length `count`

**Raises:**
- `ValueError`: If count is less than 1
- `RuntimeError`: If unable to find the requested number of sequential ports

## Usage Examples

```python
from utils.ports import find_sequential_ports

# Find a single port starting from 8090
ports = find_sequential_ports()
print(f"Found port: {ports[0]}")

# Find 3 sequential ports starting from 8100
ports = find_sequential_ports(base=8100, count=3)
print(f"Found ports: {ports}")  # e.g., [8100, 8101, 8102]

# Find ports on localhost
ports = find_sequential_ports(base=8200, count=2, host="127.0.0.1")
print(f"Found ports: {ports}")  # e.g., [8200, 8201]
```

## Import

The module can be imported in multiple ways:

```python
# Direct import
from utils.ports import find_sequential_ports

# Package import
from utils import find_sequential_ports
```

## Implementation Details

- Uses `socket.socket()` with `bind()` to test port availability
- Properly closes sockets after testing
- Handles port range boundaries (max port 65535)
- Skips sequences where not all ports are available
- Implements safeguards against infinite loops

## Testing

Run the unit tests:

```bash
python -m pytest test_ports.py -v
# or
python test_ports.py
```

The test suite includes:
- Basic functionality tests
- Edge cases (invalid parameters, port boundaries)
- Real socket integration tests
- Concurrent access tests
- Mock-based error condition tests

## Thread Safety

The module is designed to work correctly under concurrent access, as demonstrated by the concurrent port allocation tests.
