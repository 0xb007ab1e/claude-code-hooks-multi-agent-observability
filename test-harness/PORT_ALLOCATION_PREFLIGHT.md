# Port Allocation Pre-flight Check System

## Overview

This document describes the enhanced port allocation system that implements a pre-flight "sequential block availability" check. The system ensures that all required ports in a sequential block are available before attempting to start containers, providing detailed error messages when ports are in use.

## Key Features

### 1. Pre-flight Port Block Check
- **Function**: `check_sequential_port_block(base, count, host)`
- **Purpose**: Verifies that all ports in a sequential block are available before allocation
- **Returns**: Detailed information about port availability and conflicts

### 2. Process Identification
- **Capability**: Identifies which processes are using busy ports
- **Cross-platform**: Works on Linux, macOS, and Windows
- **Tools used**: `lsof`, `netstat`, `ss` on Unix; `netstat` + `tasklist` on Windows

### 3. Detailed Error Messages
- **Format**: Shows exactly which ports are busy and what processes are using them
- **Examples**:
  - `❌ Ports 8090-8094: 8092 already in use (process xyz). Aborting.`
  - `❌ Port 8090: already in use (process nginx (PID 1234))`

### 4. Clean Abort on Conflict
- **Behavior**: When any port in the required block is busy, the system aborts immediately
- **No fallback**: Unlike the original system, this doesn't try to find alternative ports
- **Clean exit**: Provides clear error messages and exits gracefully

## Implementation Details

### Core Components

#### 1. `PortInfo` Class
```python
@dataclass
class PortInfo:
    port: int
    available: bool
    process_info: Optional[str] = None
```

#### 2. `PortBlockCheckResult` Class
```python
@dataclass
class PortBlockCheckResult:
    available: bool
    requested_range: Tuple[int, int]  # (start, end) inclusive
    busy_ports: List[PortInfo]
    error_message: Optional[str] = None
```

#### 3. Main Check Function
```python
def check_sequential_port_block(base: int, count: int, host: str = "0.0.0.0") -> PortBlockCheckResult:
```

### Integration with Container Orchestrator

The `ContainerOrchestrator` class has been updated to use the new pre-flight check:

```python
def _allocate_ports(self):
    """Allocate sequential ports for all services with pre-flight check"""
    services = ['app', 'postgres', 'mongo']
    base_port = 8090
    count = len(services)
    
    # Perform pre-flight check
    check_result = check_sequential_port_block(base=base_port, count=count)
    
    if check_result.available:
        # Use the ports directly
        allocated_ports = list(range(base_port, base_port + count))
        # ... create port mapping
    else:
        # Display error and abort
        print(f"❌ {check_result.error_message}. Aborting.")
        raise RuntimeError(check_result.error_message)
```

## Usage Examples

### Basic Usage
```python
from utils.ports import check_sequential_port_block

# Check if ports 8090-8092 are available
result = check_sequential_port_block(base=8090, count=3)

if result.available:
    print("✅ All ports available!")
else:
    print(f"❌ {result.error_message}")
```

### Container Orchestrator Usage
```bash
# This will now perform pre-flight check and abort if any port is busy
python container_orchestrator.py start
```

## Error Message Examples

### Single Port Conflict
```
❌ Port 8090: already in use (process nginx (PID 1234))
```

### Multiple Port Conflicts
```
❌ Ports 8090-8092: 8090 already in use (process nginx (PID 1234)), 8092 already in use (process python (PID 5678))
```

### Process Information Variations
- **With process name and PID**: `process nginx (PID 1234)`
- **With PID only**: `process PID 1234`
- **Unknown process**: `unknown process`

## Benefits

1. **Early Detection**: Conflicts are detected before any containers are started
2. **Clear Diagnostics**: Users know exactly which ports are busy and why
3. **Predictable Behavior**: System always aborts on conflict rather than trying workarounds
4. **Process Information**: Users can identify and stop conflicting processes if needed
5. **Clean Exit**: No partial container states or cleanup required

## Testing

### Test Scripts
- `test_port_allocation.py`: Basic functionality tests
- `demo_port_conflict.py`: Demonstrates conflict detection

### Test Scenarios
1. **Available ports**: Should succeed with port allocation
2. **Busy ports**: Should fail with detailed error messages
3. **Invalid ranges**: Should handle edge cases (e.g., exceeding 65535)
4. **Process identification**: Should identify processes using busy ports

## Cross-Platform Compatibility

The system uses different approaches for process identification:

### Linux/macOS
1. **Primary**: `lsof -i :PORT -P -n`
2. **Fallback 1**: `netstat -tulpn`
3. **Fallback 2**: `ss -tulpn`

### Windows
1. **Primary**: `netstat -ano`
2. **Process lookup**: `tasklist /FI "PID eq {pid}" /FO CSV`

## Configuration

The system is configured to check the standard port range starting at 8090:
- **Base port**: 8090
- **Port count**: 3 (for app, postgres, mongo)
- **Port range**: 8090-8092

This can be modified in the `_allocate_ports()` method of `ContainerOrchestrator`.
