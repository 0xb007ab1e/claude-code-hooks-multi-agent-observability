#!/usr/bin/env python3
"""
Simple import test for the ports module.
"""

from utils import find_sequential_ports

print("Import successful!")
ports = find_sequential_ports(base=8500, count=2)
print(f"Found ports: {ports}")
