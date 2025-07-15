#!/usr/bin/env python3
"""
Demo script showing usage of the ports module.
"""

from utils.ports import find_sequential_ports

if __name__ == "__main__":
    print("=== Sequential Port Allocator Demo ===")
    
    # Test 1: Find a single port
    print("\nTest 1: Find single port starting from 8090")
    ports = find_sequential_ports()
    print(f"Found port: {ports[0]}")
    
    # Test 2: Find multiple sequential ports
    print("\nTest 2: Find 3 sequential ports starting from 8100")
    ports = find_sequential_ports(base=8100, count=3)
    print(f"Found ports: {ports}")
    
    # Test 3: Find ports with different host
    print("\nTest 3: Find 2 ports on localhost")
    ports = find_sequential_ports(base=8200, count=2, host="127.0.0.1")
    print(f"Found ports: {ports}")
    
    # Test 4: Test with high port numbers
    print("\nTest 4: Find 2 ports starting from 60000")
    ports = find_sequential_ports(base=60000, count=2)
    print(f"Found ports: {ports}")
    
    print("\n=== Demo completed successfully! ===")
