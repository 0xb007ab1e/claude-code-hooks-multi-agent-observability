#!/usr/bin/env python3
"""
Demo script that shows the port allocation failure scenario.
This script binds to port 8092 and then shows how the container orchestrator detects it.
"""

import socket
import time
import threading
from container_orchestrator import ContainerOrchestrator

def bind_to_port(port):
    """Bind to a specific port to simulate a conflict."""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind(('0.0.0.0', port))
        sock.listen(1)
        print(f"✅ Successfully bound to port {port}")
        return sock
    except Exception as e:
        print(f"❌ Failed to bind to port {port}: {e}")
        return None

def demo_port_conflict():
    """Demonstrate the port conflict detection."""
    print("🎭 Port Conflict Detection Demo")
    print("=" * 50)
    
    # Bind to port 8092 to create a conflict
    port_to_block = 8092
    print(f"\n1. Binding to port {port_to_block} to simulate conflict...")
    sock = bind_to_port(port_to_block)
    
    if sock:
        try:
            print(f"2. Port {port_to_block} is now busy. Testing container orchestrator...")
            
            # Give the system a moment to register the port binding
            time.sleep(1)
            
            # Try to start containers
            orchestrator = ContainerOrchestrator()
            orchestrator.detect_runtime()
            
            print("3. Attempting to start containers (this should fail with detailed error)...")
            success = orchestrator.start_containers()
            
            if success:
                print("❌ Unexpected: Container start succeeded when it should have failed!")
            else:
                print("✅ Container start correctly failed with detailed port information")
                
        finally:
            print(f"4. Cleaning up: Closing socket on port {port_to_block}")
            sock.close()
            
            # Test again with port freed
            time.sleep(1)
            print("5. Testing again with port freed...")
            success = orchestrator.start_containers()
            if success:
                print("✅ Container start succeeded after port was freed")
                # Clean up containers
                orchestrator.cleanup()
            else:
                print("❌ Container start still failed after port was freed")
    else:
        print("❌ Could not bind to port for demo")

if __name__ == "__main__":
    demo_port_conflict()
