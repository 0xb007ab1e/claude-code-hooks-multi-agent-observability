#!/usr/bin/env python3
"""
Test script to verify the new port allocation functionality.
"""

import sys
from utils.ports import check_sequential_port_block

def test_port_allocation():
    """Test the new port allocation functionality."""
    print("🧪 Testing Port Allocation with Pre-flight Check")
    print("=" * 60)
    
    # Test 1: Check available ports
    print("\n1. Testing available port block (assuming ports 8090-8092 are free):")
    result = check_sequential_port_block(base=8090, count=3)
    print(f"   Available: {result.available}")
    print(f"   Range: {result.requested_range[0]}-{result.requested_range[1]}")
    print(f"   Busy ports: {len(result.busy_ports)}")
    if result.error_message:
        print(f"   Error: {result.error_message}")
    
    # Test 2: Check busy ports (port 22 is usually busy for SSH)
    print("\n2. Testing busy port block (checking port 22 which is often busy):")
    result = check_sequential_port_block(base=22, count=3)
    print(f"   Available: {result.available}")
    print(f"   Range: {result.requested_range[0]}-{result.requested_range[1]}")
    print(f"   Busy ports: {len(result.busy_ports)}")
    if result.error_message:
        print(f"   Error: {result.error_message}")
    
    # Test 3: Test single port
    print("\n3. Testing single port availability:")
    result = check_sequential_port_block(base=8095, count=1)
    print(f"   Available: {result.available}")
    print(f"   Range: {result.requested_range[0]}-{result.requested_range[1]}")
    print(f"   Busy ports: {len(result.busy_ports)}")
    if result.error_message:
        print(f"   Error: {result.error_message}")
    
    # Test 4: Test invalid range
    print("\n4. Testing invalid port range (exceeds 65535):")
    result = check_sequential_port_block(base=65534, count=5)
    print(f"   Available: {result.available}")
    print(f"   Range: {result.requested_range[0]}-{result.requested_range[1]}")
    print(f"   Busy ports: {len(result.busy_ports)}")
    if result.error_message:
        print(f"   Error: {result.error_message}")

if __name__ == "__main__":
    test_port_allocation()
