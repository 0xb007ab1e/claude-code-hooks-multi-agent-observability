#!/usr/bin/env python3
"""
Test to verify that all server configurations are set to use PORT environment variable
with fallback to 8090 as required by the task.
"""

import os
import re


def test_bun_config():
    """Test Bun server configuration"""
    config_path = "../servers/bun/src/config.ts"
    if not os.path.exists(config_path):
        print("❌ Bun server config not found")
        return False
    
    with open(config_path, 'r') as f:
        content = f.read()
    
    # Check if PORT default is set to 8090
    if "PORT: z.coerce.number().min(1).max(65535).default(8090)" in content:
        print("✅ Bun server config: PORT fallback is 8090")
        return True
    else:
        print("❌ Bun server config: PORT fallback is not 8090")
        return False


def test_node_config():
    """Test Node server configuration"""
    config_path = "../servers/node/src/config.ts"
    if not os.path.exists(config_path):
        print("❌ Node server config not found")
        return False
    
    with open(config_path, 'r') as f:
        content = f.read()
    
    # Check if PORT default is set to 8090
    if "PORT: z.coerce.number().min(1).max(65535).default(8090)" in content:
        print("✅ Node server config: PORT fallback is 8090")
        return True
    else:
        print("❌ Node server config: PORT fallback is not 8090")
        return False


def test_python_config():
    """Test Python server configuration"""
    config_path = "../servers/python/src/config.py"
    if not os.path.exists(config_path):
        print("❌ Python server config not found")
        return False
    
    with open(config_path, 'r') as f:
        content = f.read()
    
    # Check if PORT default is set to 8090
    if "PORT: int = Field(default=8090, env='PORT')" in content:
        print("✅ Python server config: PORT fallback is 8090")
        return True
    else:
        print("❌ Python server config: PORT fallback is not 8090")
        return False


def test_go_skeleton():
    """Test Go skeleton configuration"""
    config_path = "../skeleton-projects/gin/main.go"
    if not os.path.exists(config_path):
        print("❌ Go skeleton config not found")
        return False
    
    with open(config_path, 'r') as f:
        content = f.read()
    
    # Check if PORT default is set to 8090
    if 'port = "8090"' in content:
        print("✅ Go skeleton config: PORT fallback is 8090")
        return True
    else:
        print("❌ Go skeleton config: PORT fallback is not 8090")
        return False


def test_rust_skeleton():
    """Test Rust skeleton configuration"""
    config_path = "../skeleton-projects/axum/src/main.rs"
    if not os.path.exists(config_path):
        print("❌ Rust skeleton config not found")
        return False
    
    with open(config_path, 'r') as f:
        content = f.read()
    
    # Check if PORT default is set to 8090
    if '"8090".to_string()' in content:
        print("✅ Rust skeleton config: PORT fallback is 8090")
        return True
    else:
        print("❌ Rust skeleton config: PORT fallback is not 8090")
        return False


def test_dotnet_skeleton():
    """Test .NET skeleton configuration"""
    config_path = "../skeleton-projects/aspnet-core/Program.cs"
    if not os.path.exists(config_path):
        print("❌ .NET skeleton config not found")
        return False
    
    with open(config_path, 'r') as f:
        content = f.read()
    
    # Check if PORT default is set to 8090
    if '?? "8090"' in content:
        print("✅ .NET skeleton config: PORT fallback is 8090")
        return True
    else:
        print("❌ .NET skeleton config: PORT fallback is not 8090")
        return False


def main():
    print("=" * 70)
    print("🔍 Server Configuration Compliance Test")
    print("=" * 70)
    
    tests = [
        test_bun_config,
        test_node_config,
        test_python_config,
        test_go_skeleton,
        test_rust_skeleton,
        test_dotnet_skeleton
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print("\n" + "=" * 70)
    print(f"📊 Configuration Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All server configurations comply with PORT environment variable requirements!")
    else:
        print("❌ Some server configurations failed compliance tests.")
    
    return passed == total


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
