#!/usr/bin/env python3
"""
Test runner for all server PORT environment variable compliance tests.
This script runs both the configuration compliance test and the integration test.
"""

import subprocess
import sys
import os

def run_test(test_name, test_script):
    """Run a test script and return success status."""
    print(f"🏃 Running {test_name}...")
    print("=" * 60)
    
    try:
        result = subprocess.run([sys.executable, test_script], 
                              capture_output=False, 
                              text=True, 
                              cwd=os.path.dirname(os.path.abspath(__file__)))
        
        if result.returncode == 0:
            print(f"✅ {test_name} PASSED")
            return True
        else:
            print(f"❌ {test_name} FAILED")
            return False
            
    except Exception as e:
        print(f"❌ {test_name} ERROR: {e}")
        return False

def main():
    print("🧪 Server PORT Environment Variable - All Tests")
    print("=" * 60)
    
    tests = [
        ("Configuration Compliance Test", "test_server_config_compliance.py"),
        ("Integration Test", "test_integration_servers.py")
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_script in tests:
        if run_test(test_name, test_script):
            passed += 1
        print()  # Add spacing between tests
    
    print("=" * 60)
    print(f"📊 Final Results: {passed}/{total} test suites passed")
    
    if passed == total:
        print("🎉 All tests passed! Server PORT compliance verified.")
        return True
    else:
        print("❌ Some tests failed. Please review the output above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
