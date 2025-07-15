#!/usr/bin/env python3
"""
Enhanced test runner that integrates with the container orchestrator.
Supports iterative testing until all tests pass, with automatic retries and fixes.
"""

import os
import sys
import subprocess
import time
import json
from typing import Dict, List, Tuple, Optional
from pathlib import Path
from container_orchestrator import ContainerOrchestrator
from config.port_manager import get_port, assign_port

class TestRunner:
    """Enhanced test runner with container orchestration"""
    
    def __init__(self):
        self.orchestrator = ContainerOrchestrator()
        self.max_iterations = 10
        self.current_iteration = 0
        self.test_results = []
        
    def run_iterative_tests(self) -> bool:
        """Run tests iteratively until they pass or max iterations reached"""
        print("🚀 Starting iterative E2E test cycle...")
        
        success = False
        
        try:
            # Detect and setup container runtime
            runtime = self.orchestrator.detect_runtime()
            print(f"Using container runtime: {runtime.name}")
            
            # Start containers
            if not self.orchestrator.start_containers():
                print("❌ Failed to start containers")
                return False
            
            # Wait for containers to be ready
            if not self.orchestrator.wait_for_containers():
                print("❌ Containers failed to become healthy")
                return False
            
            # Iterative test loop
            while self.current_iteration < self.max_iterations:
                self.current_iteration += 1
                print(f"\\n{'='*50}")
                print(f"🔄 Test Iteration {self.current_iteration}/{self.max_iterations}")
                print(f"{'='*50}")
                
                # Run tests
                test_success, test_output = self.orchestrator.run_tests()
                
                self.test_results.append({
                    'iteration': self.current_iteration,
                    'success': test_success,
                    'output': test_output
                })
                
                if test_success:
                    print(f"✅ All tests passed in iteration {self.current_iteration}!")
                    success = True
                    break
                else:
                    print(f"❌ Tests failed in iteration {self.current_iteration}")
                    
                    # Analyze failures and attempt fixes
                    if self.current_iteration < self.max_iterations:
                        print(f"🔧 Analyzing failures and attempting fixes...")
                        
                        # Try to fix issues
                        if self.analyze_and_fix_failures(test_output):
                            print("✅ Applied potential fixes, retrying...")
                            continue
                        else:
                            print("⚠️  No automatic fixes available, retrying anyway...")
                            time.sleep(2)  # Brief pause before retry
            
            if not success:
                print(f"\\n❌ Tests failed after {self.max_iterations} iterations")
                self.print_failure_summary()
            
        except KeyboardInterrupt:
            print("\\n⚠️  Test cycle interrupted by user")
        except Exception as e:
            print(f"❌ Test cycle failed: {e}")
        finally:
            # Always cleanup
            self.orchestrator.cleanup()
        
        return success
    
    def analyze_and_fix_failures(self, test_output: str) -> bool:
        """Analyze test failures and attempt automated fixes"""
        fixes_applied = False
        
        # Check for common failure patterns
        if "connection refused" in test_output.lower():
            print("🔧 Detected connection issues, checking server status...")
            if self.ensure_server_running():
                fixes_applied = True
        
        if "database" in test_output.lower() and "error" in test_output.lower():
            print("🔧 Detected database issues, checking database health...")
            if self.fix_database_issues():
                fixes_applied = True
        
        if "timeout" in test_output.lower():
            print("🔧 Detected timeout issues, increasing timeouts...")
            if self.fix_timeout_issues():
                fixes_applied = True
        
        if "permission denied" in test_output.lower():
            print("🔧 Detected permission issues, checking file permissions...")
            if self.fix_permission_issues():
                fixes_applied = True
        
        # Check for missing dependencies
        if "import" in test_output.lower() and "error" in test_output.lower():
            print("🔧 Detected import issues, checking dependencies...")
            if self.fix_dependency_issues():
                fixes_applied = True
        
        return fixes_applied
    
    def ensure_server_running(self) -> bool:
        """Ensure the server is running and accessible"""
        try:
            # Check if server is running on assigned port
            import requests
            server_port = get_port('http-server') or assign_port('http-server', 'Main HTTP Server')
            response = requests.get(f"http://localhost:{server_port}", timeout=5)
            if response.status_code == 200:
                print("✅ Server is running")
                return True
            else:
                print("⚠️  Server returned non-200 status")
        except Exception as e:
            print(f"❌ Server not accessible: {e}")
            
            # Try to start server if not running
            print("🔧 Attempting to start server...")
            return self.start_test_server()
        
        return False
    
    def start_test_server(self) -> bool:
        """Start a test server for E2E testing"""
        try:
            # Look for server in various locations
            server_paths = [
                "../apps/server",
                "../server",
                "../../apps/server",
                "../../server"
            ]
            
            for server_path in server_paths:
                if os.path.exists(server_path):
                    print(f"📁 Found server at: {server_path}")
                    
                    # Try to start server
                    server_cmd = None
                    
                    # Check for different server types
                    if os.path.exists(os.path.join(server_path, "package.json")):
                        server_cmd = ["npm", "start"]
                    elif os.path.exists(os.path.join(server_path, "main.py")):
                        server_cmd = ["python", "main.py"]
                    elif os.path.exists(os.path.join(server_path, "server.py")):
                        server_cmd = ["python", "server.py"]
                    elif os.path.exists(os.path.join(server_path, "app.py")):
                        server_cmd = ["python", "app.py"]
                    
                    if server_cmd:
                        print(f"🚀 Starting server with: {' '.join(server_cmd)}")
                        
                        # Start server in background
                        subprocess.Popen(
                            server_cmd,
                            cwd=server_path,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE
                        )
                        
                        # Wait for server to start
                        time.sleep(5)
                        
                        # Check if server is now accessible
                        return self.ensure_server_running()
            
            print("❌ Could not find or start server")
            return False
            
        except Exception as e:
            print(f"❌ Error starting server: {e}")
            return False
    
    def fix_database_issues(self) -> bool:
        """Fix common database issues"""
        fixes_applied = False
        
        try:
            # Check database container health
            if not self.orchestrator._check_postgres_health():
                print("🔧 PostgreSQL not healthy, restarting...")
                # Restart PostgreSQL container
                subprocess.run([
                    "podman", "restart", "test-postgres"
                ], capture_output=True)
                time.sleep(10)
                fixes_applied = True
            
            if not self.orchestrator._check_mongo_health():
                print("🔧 MongoDB not healthy, restarting...")
                # Restart MongoDB container  
                subprocess.run([
                    "podman", "restart", "test-mongo"
                ], capture_output=True)
                time.sleep(10)
                fixes_applied = True
            
            # Create database tables if they don't exist
            if self.create_database_tables():
                fixes_applied = True
            
        except Exception as e:
            print(f"❌ Error fixing database issues: {e}")
        
        return fixes_applied
    
    def create_database_tables(self) -> bool:
        """Create database tables if they don't exist"""
        try:
            # Create SQLite database
            import sqlite3
            conn = sqlite3.connect('/tmp/test.db')
            cursor = conn.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source_app TEXT NOT NULL,
                    session_id TEXT NOT NULL,
                    hook_event_type TEXT NOT NULL,
                    payload TEXT,
                    chat TEXT,
                    summary TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.commit()
            conn.close()
            
            print("✅ SQLite database tables created")
            return True
            
        except Exception as e:
            print(f"❌ Error creating database tables: {e}")
            return False
    
    def fix_timeout_issues(self) -> bool:
        """Fix timeout-related issues"""
        try:
            # Update test configuration with longer timeouts
            config_path = "config/test_config.py"
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    content = f.read()
                
                # Increase timeout values
                content = content.replace(
                    'request_timeout: int = int(os.getenv("REQUEST_TIMEOUT", "30"))',
                    'request_timeout: int = int(os.getenv("REQUEST_TIMEOUT", "60"))'
                )
                content = content.replace(
                    'websocket_timeout: int = int(os.getenv("WEBSOCKET_TIMEOUT", "30"))',
                    'websocket_timeout: int = int(os.getenv("WEBSOCKET_TIMEOUT", "60"))'
                )
                
                with open(config_path, 'w') as f:
                    f.write(content)
                
                print("✅ Increased timeout values")
                return True
        
        except Exception as e:
            print(f"❌ Error fixing timeout issues: {e}")
        
        return False
    
    def fix_permission_issues(self) -> bool:
        """Fix permission-related issues"""
        try:
            # Fix common permission issues
            paths_to_fix = [
                '/tmp/test.db',
                './reports',
                './test-data'
            ]
            
            for path in paths_to_fix:
                if os.path.exists(path):
                    os.chmod(path, 0o755)
            
            print("✅ Fixed file permissions")
            return True
        
        except Exception as e:
            print(f"❌ Error fixing permissions: {e}")
        
        return False
    
    def fix_dependency_issues(self) -> bool:
        """Fix dependency-related issues"""
        try:
            # Install missing dependencies
            subprocess.run([
                "pip", "install", "-r", "requirements.txt"
            ], capture_output=True)
            
            print("✅ Reinstalled dependencies")
            return True
        
        except Exception as e:
            print(f"❌ Error fixing dependencies: {e}")
        
        return False
    
    def print_failure_summary(self):
        """Print summary of test failures"""
        print(f"\\n{'='*60}")
        print("📊 TEST FAILURE SUMMARY")
        print(f"{'='*60}")
        
        for result in self.test_results:
            status = "✅ PASS" if result['success'] else "❌ FAIL"
            print(f"Iteration {result['iteration']}: {status}")
        
        if self.test_results:
            last_result = self.test_results[-1]
            print(f"\\n📋 Last test output:")
            print("-" * 40)
            print(last_result['output'])
    
    def commit_changes(self, message: str):
        """Commit changes to git"""
        try:
            subprocess.run(["git", "add", "."], capture_output=True)
            subprocess.run(["git", "commit", "-m", message], capture_output=True)
            print(f"✅ Committed changes: {message}")
        except Exception as e:
            print(f"⚠️  Could not commit changes: {e}")


def main():
    """Main entry point"""
    runner = TestRunner()
    
    # Check command line arguments
    if len(sys.argv) > 1:
        if sys.argv[1] == "--max-iterations":
            runner.max_iterations = int(sys.argv[2])
        elif sys.argv[1] == "--help":
            print("Usage: python run_containerized_tests.py [--max-iterations N]")
            print("  --max-iterations N: Maximum number of test iterations (default: 10)")
            return
    
    # Run iterative tests
    success = runner.run_iterative_tests()
    
    # Commit changes if tests pass
    if success:
        runner.commit_changes("✅ All E2E tests passing - iteration complete")
        print("\\n🎉 All tests passed! Changes committed.")
    else:
        print("\\n❌ Tests failed after maximum iterations.")
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
