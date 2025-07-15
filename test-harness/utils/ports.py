"""
Sequential port allocator utility module.

This module provides functionality to find sequential available ports on a host.
"""

import socket
import subprocess
import sys
from typing import List, Dict, Optional, Tuple, NamedTuple
from dataclasses import dataclass


def find_sequential_ports(base: int = 8090, count: int = 1, host: str = "0.0.0.0") -> List[int]:
    """
    Find sequential available ports starting from a base port.
    
    Args:
        base: Starting port number (default: 8090)
        count: Number of sequential ports to find (default: 1)
        host: Host address to bind to (default: "0.0.0.0")
    
    Returns:
        List of available sequential port numbers of length `count`
    
    Raises:
        ValueError: If count is less than 1
        RuntimeError: If unable to find the requested number of sequential ports
    """
    if count < 1:
        raise ValueError("Count must be at least 1")
    
    # Start searching from the base port
    current_port = base
    max_attempts = 1000  # Prevent infinite loops
    
    for _ in range(max_attempts):
        ports = []
        all_available = True
        
        # Check if we can bind to `count` sequential ports starting from current_port
        for i in range(count):
            port = current_port + i
            if _is_port_available(port, host):
                ports.append(port)
            else:
                all_available = False
                break
        
        if all_available and len(ports) == count:
            return ports
        
        # Move to next port and try again
        current_port += 1
        
        # Ensure we don't exceed valid port range
        if current_port + count - 1 > 65535:
            break
    
    raise RuntimeError(f"Unable to find {count} sequential available ports starting from {base}")


@dataclass
class PortInfo:
    """Information about a port."""
    port: int
    available: bool
    process_info: Optional[str] = None


@dataclass
class PortBlockCheckResult:
    """Result of checking a sequential port block."""
    available: bool
    requested_range: Tuple[int, int]  # (start, end) inclusive
    busy_ports: List[PortInfo]
    error_message: Optional[str] = None


def check_sequential_port_block(base: int, count: int, host: str = "0.0.0.0") -> PortBlockCheckResult:
    """
    Check if a sequential block of ports is available.
    
    This function performs a pre-flight check to verify that all ports in the
    requested sequential block are available. If any port is busy, it returns
    detailed information about which ports are in use and what processes are
    using them.
    
    Args:
        base: Starting port number
        count: Number of sequential ports to check
        host: Host address to bind to (default: "0.0.0.0")
    
    Returns:
        PortBlockCheckResult with availability status and detailed information
    """
    if count < 1:
        return PortBlockCheckResult(
            available=False,
            requested_range=(base, base + count - 1),
            busy_ports=[],
            error_message="Count must be at least 1"
        )
    
    end_port = base + count - 1
    if end_port > 65535:
        return PortBlockCheckResult(
            available=False,
            requested_range=(base, end_port),
            busy_ports=[],
            error_message=f"Port range {base}-{end_port} exceeds maximum port number 65535"
        )
    
    busy_ports = []
    
    # Check each port in the sequential block
    for i in range(count):
        port = base + i
        if not _is_port_available(port, host):
            process_info = _get_process_using_port(port)
            busy_ports.append(PortInfo(
                port=port,
                available=False,
                process_info=process_info
            ))
    
    available = len(busy_ports) == 0
    error_message = None
    
    if not available:
        busy_port_strs = []
        for port_info in busy_ports:
            if port_info.process_info:
                busy_port_strs.append(f"{port_info.port} already in use ({port_info.process_info})")
            else:
                busy_port_strs.append(f"{port_info.port} already in use")
        
        if count == 1:
            # Single port case
            port_desc = busy_port_strs[0]
            error_message = f"Port {base}: {port_desc.split(f'{base} ')[1]}"
        else:
            # Multiple ports case
            port_descriptions = []
            for port_str in busy_port_strs:
                # Extract the part after "already in use"
                parts = port_str.split(' already in use')
                if len(parts) == 2:
                    port_descriptions.append(parts[0] + ' already in use' + parts[1])
                else:
                    port_descriptions.append(port_str)
            
            error_message = f"Ports {base}-{end_port}: {', '.join(port_descriptions)}"
    
    return PortBlockCheckResult(
        available=available,
        requested_range=(base, end_port),
        busy_ports=busy_ports,
        error_message=error_message
    )


def _get_process_using_port(port: int) -> Optional[str]:
    """
    Get information about the process using a specific port.
    
    Args:
        port: Port number to check
    
    Returns:
        String with process information, or None if unable to determine
    """
    try:
        # Try different approaches based on the operating system
        if sys.platform.startswith('linux') or sys.platform.startswith('darwin'):
            # Try lsof first (most detailed)
            try:
                result = subprocess.run(
                    ['lsof', '-i', f':{port}', '-P', '-n'],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if result.returncode == 0 and result.stdout.strip():
                    lines = result.stdout.strip().split('\n')
                    if len(lines) > 1:  # Skip header line
                        process_line = lines[1]
                        parts = process_line.split()
                        if len(parts) >= 2:
                            process_name = parts[0]
                            pid = parts[1]
                            return f"process {process_name} (PID {pid})"
            except (subprocess.TimeoutExpired, FileNotFoundError):
                pass
            
            # Try netstat as fallback
            try:
                result = subprocess.run(
                    ['netstat', '-tulpn'],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if result.returncode == 0:
                    for line in result.stdout.split('\n'):
                        if f':{port} ' in line:
                            parts = line.split()
                            if len(parts) >= 7 and parts[6] != '-':
                                process_info = parts[6]
                                if '/' in process_info:
                                    pid, name = process_info.split('/', 1)
                                    return f"process {name} (PID {pid})"
                                else:
                                    return f"process {process_info}"
            except (subprocess.TimeoutExpired, FileNotFoundError):
                pass
            
            # Try ss as another fallback
            try:
                result = subprocess.run(
                    ['ss', '-tulpn'],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if result.returncode == 0:
                    for line in result.stdout.split('\n'):
                        if f':{port} ' in line:
                            parts = line.split()
                            if len(parts) >= 7 and 'users:' in parts[6]:
                                # Extract process info from ss output
                                users_part = parts[6]
                                if '(("' in users_part and '",pid=' in users_part:
                                    try:
                                        start = users_part.find('(("') + 3
                                        end = users_part.find('",pid=')
                                        if start < end:
                                            process_name = users_part[start:end]
                                            pid_start = users_part.find('pid=') + 4
                                            pid_end = users_part.find(',', pid_start)
                                            if pid_end == -1:
                                                pid_end = users_part.find(')', pid_start)
                                            if pid_start < pid_end:
                                                pid = users_part[pid_start:pid_end]
                                                return f"process {process_name} (PID {pid})"
                                    except (ValueError, IndexError):
                                        pass
            except (subprocess.TimeoutExpired, FileNotFoundError):
                pass
        
        elif sys.platform.startswith('win'):
            # Windows: try netstat
            try:
                result = subprocess.run(
                    ['netstat', '-ano'],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if result.returncode == 0:
                    for line in result.stdout.split('\n'):
                        if f':{port} ' in line and 'LISTENING' in line:
                            parts = line.split()
                            if len(parts) >= 5:
                                pid = parts[4]
                                # Try to get process name from PID
                                try:
                                    tasklist_result = subprocess.run(
                                        ['tasklist', '/FI', f'PID eq {pid}', '/FO', 'CSV'],
                                        capture_output=True,
                                        text=True,
                                        timeout=5
                                    )
                                    if tasklist_result.returncode == 0:
                                        lines = tasklist_result.stdout.strip().split('\n')
                                        if len(lines) >= 2:
                                            process_line = lines[1]
                                            # Parse CSV format
                                            if process_line.startswith('"'):
                                                process_name = process_line.split('"')[1]
                                                return f"process {process_name} (PID {pid})"
                                except (subprocess.TimeoutExpired, FileNotFoundError):
                                    pass
                                return f"process PID {pid}"
            except (subprocess.TimeoutExpired, FileNotFoundError):
                pass
        
        # Generic fallback - just indicate something is using the port
        return "unknown process"
    
    except Exception:
        return "unknown process"


def _is_port_available(port: int, host: str) -> bool:
    """
    Check if a port is available for binding.
    
    Args:
        port: Port number to check
        host: Host address to bind to
    
    Returns:
        True if port is available, False otherwise
    """
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.bind((host, port))
            return True
    except (socket.error, OSError):
        return False
