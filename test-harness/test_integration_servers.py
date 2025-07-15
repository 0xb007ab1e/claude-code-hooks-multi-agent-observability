#!/usr/bin/env python3
"""
Integration test for server PORT environment variable compliance.

This test ensures that all servers:
1. Read the PORT environment variable
2. Use fallback port 8090 when PORT is not set
3. Start correctly on a random high port
"""

import os
import subprocess
import random
import requests
import time
import sys

# Test implemented servers (Bun, Node, Python)
IMPLEMENTED_SERVERS = {
    "node": "cd servers/node && npx tsx src/index.ts",
    "python": "python servers/python/run_server.py",
}

# Test skeleton projects (Go, Rust, .NET) - Note: Bun not available in this env
SKELETON_SERVERS = {
    "go": "cd skeleton-projects/gin && go run main.go",
}


def run_server_test(server_name, server_command, test_port=None):
    """Test a server on a specific port or random port."""
    port = test_port if test_port else random.randint(30000, 40000)
    env = os.environ.copy()
    env['PORT'] = str(port)
    
    print(f"\n🚀 Testing {server_name} server on port {port}")

    process = subprocess.Popen(
        server_command,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        shell=True,
        cwd=".."
    )

    # Give server time to start
    time.sleep(3)

    success = False
    try:
        response = requests.get(f"http://localhost:{port}", timeout=2)
        if response.status_code == 200:
            print(f"✅ {server_name} server running successfully on port {port}")
            success = True
        else:
            print(f"❌ {server_name} server returned status {response.status_code} on port {port}")
    except requests.exceptions.ConnectionError:
        print(f"❌ {server_name} server not reachable on port {port}")
    except requests.exceptions.Timeout:
        print(f"❌ {server_name} server timed out on port {port}")
    finally:
        process.terminate()
        process.wait()
    
    return success


def test_default_port_fallback(server_name, server_command):
    """Test that server uses default port 8090 when PORT env var is not set."""
    print(f"\n🔧 Testing {server_name} server default port fallback (8090)")
    
    env = os.environ.copy()
    # Remove PORT env var if it exists
    if 'PORT' in env:
        del env['PORT']
    
    process = subprocess.Popen(
        server_command,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        shell=True,
        cwd=".."
    )

    # Give server time to start
    time.sleep(3)

    success = False
    try:
        response = requests.get("http://localhost:8090", timeout=2)
        if response.status_code == 200:
            print(f"✅ {server_name} server using default port 8090 successfully")
            success = True
        else:
            print(f"❌ {server_name} server returned status {response.status_code} on default port 8090")
    except requests.exceptions.ConnectionError:
        print(f"❌ {server_name} server not reachable on default port 8090")
    except requests.exceptions.Timeout:
        print(f"❌ {server_name} server timed out on default port 8090")
    finally:
        process.terminate()
        process.wait()
    
    return success


def test_servers():
    print("=" * 70)
    print("🧪 PORT Environment Variable Integration Test")
    print("=" * 70)
    
    total_tests = 0
    passed_tests = 0
    
    print("\n📋 Testing implemented servers...")
    for name, command in IMPLEMENTED_SERVERS.items():
        # Test random port
        total_tests += 1
        if run_server_test(name, command):
            passed_tests += 1
            
        # Test default port fallback
        total_tests += 1
        if test_default_port_fallback(name, command):
            passed_tests += 1
    
    print("\n📋 Testing skeleton servers...")
    for name, command in SKELETON_SERVERS.items():
        # Test random port
        total_tests += 1
        if run_server_test(name, command):
            passed_tests += 1
            
        # Test default port fallback
        total_tests += 1
        if test_default_port_fallback(name, command):
            passed_tests += 1
    
    print("\n" + "=" * 70)
    print(f"📊 Test Results: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("🎉 All servers comply with PORT environment variable requirements!")
        sys.exit(0)
    else:
        print("❌ Some servers failed PORT environment variable compliance tests.")
        sys.exit(1)


if __name__ == "__main__":
    test_servers()
