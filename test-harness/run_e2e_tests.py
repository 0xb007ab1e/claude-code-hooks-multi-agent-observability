#!/usr/bin/env python3
"""
Comprehensive E2E Test Runner for Multi-Agent Observability System
This script runs all tests and generates comprehensive reports.
"""

import os
import sys
import subprocess
import time
import json
import argparse
from datetime import datetime
from typing import Dict, List, Optional, Any
import requests
from config.test_config import config

# Docker utilities are optional
try:
    from utils.docker_utils import docker_manager
    DOCKER_AVAILABLE = True
except Exception as e:
    print(f"Docker utilities not available: {e}")
    DOCKER_AVAILABLE = False
    docker_manager = None

def read_orchestrator_config() -> Dict[str, Any]:
    """Read orchestrator-exported environment variables and port assignments."""
    orchestrator_config = {}
    
    # Try to read from JSON config file first
    port_config_file = "config/port_assignments.json"
    if os.path.exists(port_config_file):
        try:
            with open(port_config_file, 'r') as f:
                port_data = json.load(f)
                orchestrator_config.update(port_data)
                print(f"📋 Loaded port assignments from {port_config_file}")
        except Exception as e:
            print(f"⚠️  Failed to read port assignments: {e}")
    
    # Read from environment variables (these override JSON)
    env_ports = {
        'server_port': os.getenv('HTTP_SERVER_PORT', os.getenv('SERVER_PORT', os.getenv('PORT'))),
        'postgres_port': os.getenv('POSTGRES_PORT'),
        'mongo_port': os.getenv('MONGO_PORT'),
        'base_port': os.getenv('BASE_PORT'),
        'redis_port': os.getenv('REDIS_PORT'),
        'elasticsearch_port': os.getenv('ELASTICSEARCH_PORT'),
        'grafana_port': os.getenv('GRAFANA_PORT'),
        'prometheus_port': os.getenv('PROMETHEUS_PORT'),
    }
    
    # Only add environment variables that are actually set
    for key, value in env_ports.items():
        if value is not None:
            orchestrator_config[key] = value
    
    # Additional environment variables for database connections
    env_vars = {
        'postgres_host': os.getenv('POSTGRES_HOST'),
        'postgres_db': os.getenv('POSTGRES_DB'),
        'postgres_user': os.getenv('POSTGRES_USER'),
        'postgres_password': os.getenv('POSTGRES_PASSWORD'),
        'mongo_host': os.getenv('MONGO_HOST'),
        'mongo_db': os.getenv('MONGO_DB'),
        'mongo_user': os.getenv('MONGO_USER'),
        'mongo_password': os.getenv('MONGO_PASSWORD'),
        'sqlite_path': os.getenv('SQLITE_PATH'),
        'server_host': os.getenv('SERVER_HOST'),
        'server_protocol': os.getenv('SERVER_PROTOCOL'),
        'ws_protocol': os.getenv('WS_PROTOCOL'),
    }
    
    for key, value in env_vars.items():
        if value is not None:
            orchestrator_config[key] = value
    
    return orchestrator_config

class E2ETestRunner:
    """End-to-end test runner for the multi-agent observability system."""
    
    def __init__(self, server_image: str = None, branch: str = None):
        self.server_image = server_image
        self.branch = branch
        self.results = {}
        self.start_time = None
        self.end_time = None
        self.orchestrator_config = read_orchestrator_config()
        
    def wait_for_server(self, max_wait: int = 60) -> bool:
        """Wait for the server to be ready."""
        print(f"Waiting for server at {config.server.base_url}...")
        start_time = time.time()
        
        while time.time() - start_time < max_wait:
            try:
                response = requests.get(config.server.base_url, timeout=5)
                if response.status_code == 200:
                    print("✅ Server is ready!")
                    return True
            except requests.exceptions.RequestException:
                pass
            time.sleep(2)
        
        print("❌ Server failed to start within timeout")
        return False
    
    def run_test_suite(self, test_pattern: str = None) -> Dict:
        """Run a specific test suite."""
        cmd = ["python", "-m", "pytest"]
        
        if test_pattern:
            cmd.extend([test_pattern])
        else:
            cmd.extend(["tests/"])
        
        cmd.extend([
            "-v", 
            "--tb=short",
            "--html=reports/report.html",
            "--self-contained-html",
            "--json-report",
            "--json-report-file=reports/report.json"
        ])
        
        print(f"Running: {' '.join(cmd)}")
        
        start_time = time.time()
        result = subprocess.run(cmd, capture_output=True, text=True)
        end_time = time.time()
        
        return {
            "command": " ".join(cmd),
            "return_code": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "duration": end_time - start_time,
            "success": result.returncode == 0
        }
    
    def run_all_tests(self) -> Dict:
        """Run all test suites."""
        print("🚀 Starting comprehensive E2E test run...")
        self.start_time = datetime.now()
        
        # Test suites to run
        test_suites = [
            ("REST API Tests", "tests/test_rest_api.py"),
            ("WebSocket Tests", "tests/test_websockets.py"),
            ("Database Tests", "tests/test_database.py"),
            ("Edge Case Tests", "tests/test_edge_cases.py"),
            ("Integration Tests", "tests/")  # Run all tests
        ]
        
        results = {}
        
        for suite_name, test_pattern in test_suites:
            print(f"\n📋 Running {suite_name}...")
            results[suite_name] = self.run_test_suite(test_pattern)
            
            if results[suite_name]["success"]:
                print(f"✅ {suite_name} passed")
            else:
                print(f"❌ {suite_name} failed")
                
        self.end_time = datetime.now()
        self.results = results
        
        return results
    
    def generate_summary_report(self) -> Dict:
        """Generate a summary report of all test results."""
        total_tests = 0
        passed_tests = 0
        failed_tests = 0
        total_duration = 0
        
        for suite_name, result in self.results.items():
            total_duration += result["duration"]
            if result["success"]:
                passed_tests += 1
            else:
                failed_tests += 1
            total_tests += 1
        
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        summary = {
            "timestamp": self.start_time.isoformat() if self.start_time else None,
            "duration": total_duration,
            "total_suites": total_tests,
            "passed_suites": passed_tests,
            "failed_suites": failed_tests,
            "success_rate": success_rate,
            "server_image": self.server_image,
            "branch": self.branch,
            "results": self.results
        }
        
        return summary
    
    def save_results(self, filename: str = None):
        """Save test results to file."""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"reports/e2e_results_{timestamp}.json"
        
        os.makedirs("reports", exist_ok=True)
        
        summary = self.generate_summary_report()
        
        with open(filename, 'w') as f:
            json.dump(summary, f, indent=2)
        
        print(f"📊 Results saved to {filename}")
        
        return filename
    
    def print_summary(self):
        """Print a summary of test results."""
        summary = self.generate_summary_report()
        
        print("\n" + "="*60)
        print("🎯 E2E Test Summary")
        print("="*60)
        print(f"⏱️  Duration: {summary['duration']:.2f}s")
        print(f"📊 Total Suites: {summary['total_suites']}")
        print(f"✅ Passed: {summary['passed_suites']}")
        print(f"❌ Failed: {summary['failed_suites']}")
        print(f"📈 Success Rate: {summary['success_rate']:.1f}%")
        
        if summary['server_image']:
            print(f"🐳 Server Image: {summary['server_image']}")
        if summary['branch']:
            print(f"🌿 Branch: {summary['branch']}")
        
        print("\n📋 Suite Results:")
        for suite_name, result in summary['results'].items():
            status = "✅ PASS" if result['success'] else "❌ FAIL"
            print(f"  {status} {suite_name} ({result['duration']:.2f}s)")
        
        print("="*60)
        
        return summary['success_rate'] == 100.0
    
    def display_orchestrator_config(self):
        """Display the orchestrator configuration."""
        print("\n🔧 Orchestrator Configuration:")
        print("="*40)
        
        if self.orchestrator_config:
            for key, value in self.orchestrator_config.items():
                print(f"  {key}: {value}")
        else:
            print("  No orchestrator configuration found")
        
        print("\n🌐 Current Test Configuration:")
        print(f"  Server URL: {config.server.base_url}")
        print(f"  WebSocket URL: {config.server.ws_url}")
        print(f"  PostgreSQL: {config.database.postgres_host}:{config.database.postgres_port}")
        print(f"  MongoDB: {config.database.mongo_host}:{config.database.mongo_port}")
        print(f"  SQLite: {config.database.sqlite_path}")
        print("="*40)

def main():
    parser = argparse.ArgumentParser(description="Run E2E tests for multi-agent observability system")
    parser.add_argument("--server-image", help="Docker image for server")
    parser.add_argument("--branch", help="Git branch being tested")
    parser.add_argument("--test-pattern", help="Specific test pattern to run")
    parser.add_argument("--output", help="Output file for results")
    parser.add_argument("--no-wait", action="store_true", help="Don't wait for server to be ready")
    
    args = parser.parse_args()
    
    runner = E2ETestRunner(server_image=args.server_image, branch=args.branch)
    
    # Display orchestrator configuration
    runner.display_orchestrator_config()
    
    # Wait for server to be ready unless --no-wait is specified
    if not args.no_wait:
        if not runner.wait_for_server():
            print("❌ Server not ready, exiting")
            sys.exit(1)
    
    # Run tests
    if args.test_pattern:
        print(f"Running specific test pattern: {args.test_pattern}")
        result = runner.run_test_suite(args.test_pattern)
        success = result["success"]
    else:
        runner.run_all_tests()
        success = runner.print_summary()
    
    # Save results
    runner.save_results(args.output)
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
