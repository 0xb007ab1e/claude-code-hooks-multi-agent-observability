#!/usr/bin/env python3
"""
Container orchestration script that supports Docker, Podman, and other OCI-compatible runtimes.
Detects available container runtime and manages test environment containers.
"""

import os
import sys
import subprocess
import json
import time
import signal
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path
from config.port_manager import assign_port, get_port, export_env_vars
from utils import find_sequential_ports, check_sequential_port_block

@dataclass
class ContainerRuntime:
    """Container runtime configuration"""
    name: str
    command: str
    compose_command: str
    available: bool = False
    version: str = ""

class ContainerOrchestrator:
    """Manages containerized test environments across different runtimes"""
    
    def __init__(self):
        self.runtime: Optional[ContainerRuntime] = None
        self.containers: List[str] = []
        self.compose_file = "docker-compose.test.yml"
        self.project_name = "test-env"
        self.ports: Dict[str, int] = {}
        
    def detect_runtime(self) -> ContainerRuntime:
        """Detect available container runtime"""
        runtimes = [
            ContainerRuntime("podman", "podman", "podman-compose"),
            ContainerRuntime("docker", "docker", "docker-compose"),
            ContainerRuntime("nerdctl", "nerdctl", "nerdctl compose"),
            ContainerRuntime("buildah", "buildah", "buildah-compose"),
        ]
        
        for runtime in runtimes:
            if self._check_runtime_available(runtime):
                self.runtime = runtime
                print(f"✅ Using container runtime: {runtime.name} (version: {runtime.version})")
                return runtime
        
        raise RuntimeError("No compatible container runtime found. Please install Docker, Podman, or another OCI-compatible runtime.")
    
    def _check_runtime_available(self, runtime: ContainerRuntime) -> bool:
        """Check if a specific runtime is available"""
        try:
            result = subprocess.run([runtime.command, "--version"], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                runtime.available = True
                runtime.version = result.stdout.strip()
                
                # Check if compose is available
                if runtime.name == "podman":
                    # Try podman-compose first, then fallback to docker-compose
                    compose_available = (
                        self._check_command_available("podman-compose") or 
                        self._check_command_available("docker-compose")
                    )
                    if not compose_available:
                        runtime.compose_command = "podman"  # Use podman play kube as fallback
                elif runtime.name == "docker":
                    if not self._check_command_available("docker-compose"):
                        runtime.compose_command = "docker compose"  # Use built-in compose
                
                return True
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
        return False
    
    def _check_command_available(self, command: str) -> bool:
        """Check if a command is available in PATH"""
        try:
            subprocess.run([command, "--version"], 
                          capture_output=True, timeout=5)
            return True
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False
    
    def create_podman_compose_file(self) -> str:
        """Create a podman-compatible compose file with allocated ports"""
        postgres_port = self.ports.get('postgres', 5432)
        mongo_port = self.ports.get('mongo', 27017)
        
        compose_content = f"""version: '3.8'

services:
  postgres:
    image: docker.io/postgres:15
    container_name: test-postgres
    environment:
      POSTGRES_DB: testdb
      POSTGRES_USER: user
      POSTGRES_PASSWORD: password
      POSTGRES_HOST_AUTH_METHOD: trust
    ports:
      - "{postgres_port}:{postgres_port}"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./init-db.sql:/docker-entrypoint-initdb.d/init-db.sql
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U user -d testdb"]
      interval: 10s
      timeout: 5s
      retries: 5

  mongo:
    image: docker.io/mongo:7.0
    container_name: test-mongo
    environment:
      MONGO_INITDB_ROOT_USERNAME: user
      MONGO_INITDB_ROOT_PASSWORD: password
      MONGO_INITDB_DATABASE: testdb
    ports:
      - "{mongo_port}:{mongo_port}"
    volumes:
      - mongo_data:/data/db
    healthcheck:
      test: ["CMD", "mongosh", "--eval", "db.adminCommand('ping')"]
      interval: 10s
      timeout: 5s
      retries: 5

volumes:
  postgres_data:
  mongo_data:
"""
        
        podman_compose_file = "podman-compose.test.yml"
        with open(podman_compose_file, 'w') as f:
            f.write(compose_content)
        
        return podman_compose_file
    
    def start_containers(self) -> bool:
        """Start test environment containers"""
        if not self.runtime:
            self.detect_runtime()
        
        try:
            # Allocate sequential ports before starting containers
            self._allocate_ports()
            
            if self.runtime.name == "podman":
                return self._start_podman_containers()
            else:
                return self._start_compose_containers()
        except Exception as e:
            print(f"❌ Failed to start containers: {e}")
            return False
    
    def _allocate_ports(self):
        """Allocate sequential ports for all services with pre-flight check"""
        # Define services that need ports
        services = ['app', 'postgres', 'mongo']
        base_port = 8090
        count = len(services)
        
        try:
            # Perform pre-flight check on the preferred port block
            check_result = check_sequential_port_block(base=base_port, count=count)
            
            if check_result.available:
                # Preferred port block is available, use it directly
                allocated_ports = list(range(base_port, base_port + count))
                
                # Create port mapping
                self.ports = {}
                for i, service in enumerate(services):
                    self.ports[service] = allocated_ports[i]
                
                print(f"✅ Allocated sequential ports: {self.ports}")
                return
            else:
                # Port block is not available, display detailed error and abort
                print(f"❌ {check_result.error_message}. Aborting.")
                raise RuntimeError(check_result.error_message)
                
        except Exception as e:
            if "already in use" in str(e):
                # This is our custom error message with process info
                print(f"❌ Port allocation failed: {e}")
                raise RuntimeError(f"Unable to allocate sequential ports: {e}")
            else:
                # Some other error, try to find alternative ports
                print(f"⚠️  Pre-flight check failed: {e}")
                print("🔄 Attempting to find alternative sequential ports...")
                
                try:
                    # Fallback to the original find_sequential_ports function
                    allocated_ports = find_sequential_ports(base=base_port, count=count)
                    
                    # Create port mapping
                    self.ports = {}
                    for i, service in enumerate(services):
                        self.ports[service] = allocated_ports[i]
                    
                    print(f"✅ Allocated alternative sequential ports: {self.ports}")
                    
                except Exception as fallback_e:
                    print(f"❌ Port allocation failed: {fallback_e}")
                    raise RuntimeError(f"Unable to allocate sequential ports: {fallback_e}")
    
    def _start_podman_containers(self) -> bool:
        """Start containers using Podman"""
        try:
            # Check if containers already exist and are running
            if self._check_containers_exist():
                print("✅ Containers already exist and are running")
                return True
            
            # Clean up any existing containers first
            self._cleanup_existing_containers()
            
            # Use allocated ports
            postgres_port = self.ports['postgres']
            mongo_port = self.ports['mongo']
            
            # Create a pod for the test environment
            pod_cmd = [
                "podman", "pod", "create", 
                "--name", self.project_name,
                "-p", f"{postgres_port}:{postgres_port}",
                "-p", f"{mongo_port}:{mongo_port}"
            ]
            
            result = subprocess.run(pod_cmd, capture_output=True, text=True)
            if result.returncode != 0 and "already exists" not in result.stderr:
                print(f"❌ Failed to create pod: {result.stderr}")
                return False
            
            # Start PostgreSQL container
            postgres_cmd = [
                "podman", "run", "-d",
                "--name", "test-postgres",
                "--pod", self.project_name,
                "-e", "POSTGRES_DB=testdb",
                "-e", "POSTGRES_USER=user", 
                "-e", "POSTGRES_PASSWORD=password",
                "-e", "POSTGRES_HOST_AUTH_METHOD=trust",
                "-v", f"{os.getcwd()}/init-db.sql:/docker-entrypoint-initdb.d/init-db.sql:Z",
                "docker.io/postgres:15"
            ]
            
            result = subprocess.run(postgres_cmd, capture_output=True, text=True)
            if result.returncode != 0:
                print(f"❌ Failed to start PostgreSQL: {result.stderr}")
                return False
            
            self.containers.append("test-postgres")
            
            # Start MongoDB container
            mongo_cmd = [
                "podman", "run", "-d",
                "--name", "test-mongo",
                "--pod", self.project_name,
                "-e", "MONGO_INITDB_ROOT_USERNAME=user",
                "-e", "MONGO_INITDB_ROOT_PASSWORD=password",
                "-e", "MONGO_INITDB_DATABASE=testdb",
                "docker.io/mongo:7.0"
            ]
            
            result = subprocess.run(mongo_cmd, capture_output=True, text=True)
            if result.returncode != 0:
                print(f"❌ Failed to start MongoDB: {result.stderr}")
                return False
            
            self.containers.append("test-mongo")
            
            print("✅ Containers started successfully with Podman")
            return True
            
        except Exception as e:
            print(f"❌ Error starting Podman containers: {e}")
            return False
    
    def _start_compose_containers(self) -> bool:
        """Start containers using compose"""
        try:
            if self.runtime.name == "podman":
                compose_file = self.create_podman_compose_file()
                self.compose_file = compose_file
            
            # Use appropriate compose command
            compose_cmd = self.runtime.compose_command.split()
            
            # Set up environment variables with allocated ports
            env = os.environ.copy()
            env.update(self._get_port_env_vars())
            
            # Build and start containers
            cmd = compose_cmd + ["-f", self.compose_file, "up", "--build", "-d"]
            
            print(f"Running: {' '.join(cmd)}")
            print(f"Port environment variables: {self._get_port_env_vars()}")
            result = subprocess.run(cmd, capture_output=True, text=True, env=env)
            
            if result.returncode != 0:
                print(f"❌ Compose failed: {result.stderr}")
                return False
            
            print("✅ Containers started successfully with compose")
            return True
            
        except Exception as e:
            print(f"❌ Error starting compose containers: {e}")
            return False
    
    def _get_port_env_vars(self) -> Dict[str, str]:
        """Get environment variables for port mapping"""
        env_vars = {}
        for service, port in self.ports.items():
            env_var_name = f"{service.upper()}_PORT"
            env_vars[env_var_name] = str(port)
        
        # Add HTTP_SERVER_PORT for the test harness
        if 'app' in self.ports:
            env_vars['HTTP_SERVER_PORT'] = str(self.ports['app'])
        
        return env_vars
    
    def wait_for_containers(self, timeout: int = 120) -> bool:
        """Wait for containers to be healthy"""
        print("⏳ Waiting for containers to be ready...")
        
        start_time = time.time()
        while time.time() - start_time < timeout:
            if self._check_postgres_health() and self._check_mongo_health():
                print("✅ All containers are healthy")
                return True
            
            time.sleep(5)
            print("⏳ Still waiting...")
        
        print("❌ Containers failed to become healthy within timeout")
        return False
    
    def _check_postgres_health(self) -> bool:
        """Check if PostgreSQL is ready"""
        try:
            cmd = [
                self.runtime.command, "exec", "test-postgres",
                "pg_isready", "-U", "user", "-d", "testdb"
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            return result.returncode == 0
        except:
            return False
    
    def _check_mongo_health(self) -> bool:
        """Check if MongoDB is ready"""
        try:
            cmd = [
                self.runtime.command, "exec", "test-mongo",
                "mongosh", "--eval", "db.adminCommand('ping')"
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            return result.returncode == 0
        except:
            return False
    
    def _check_containers_exist(self) -> bool:
        """Check if required containers exist and are running"""
        try:
            # Check if containers exist
            result = subprocess.run([
                self.runtime.command, "ps", "--format", "{{.Names}}"
            ], capture_output=True, text=True)
            
            if result.returncode != 0:
                return False
            
            running_containers = result.stdout.strip().split('\n')
            required_containers = ["test-postgres", "test-mongo"]
            
            for container in required_containers:
                if container not in running_containers:
                    return False
            
            # Check if containers are healthy
            return self._check_postgres_health() and self._check_mongo_health()
            
        except Exception:
            return False
    
    def _cleanup_existing_containers(self):
        """Clean up any existing containers with the same names"""
        try:
            containers_to_remove = ["test-postgres", "test-mongo"]
            
            for container in containers_to_remove:
                # Stop container
                subprocess.run([
                    self.runtime.command, "stop", container
                ], capture_output=True)
                
                # Remove container
                subprocess.run([
                    self.runtime.command, "rm", container
                ], capture_output=True)
            
            # Remove pod if it exists
            subprocess.run([
                self.runtime.command, "pod", "rm", self.project_name
            ], capture_output=True)
            
            print("🧹 Cleaned up existing containers")
            
        except Exception as e:
            print(f"⚠️  Error during cleanup: {e}")
    
    def run_tests(self) -> Tuple[bool, str]:
        """Run the E2E tests"""
        print("🚀 Running E2E tests...")
        
        # Set environment variables for database connections
        env = os.environ.copy()
        
        # Use allocated ports
        postgres_port = self.ports.get('postgres', 5432)
        mongo_port = self.ports.get('mongo', 27017)
        
        env.update({
            'POSTGRES_HOST': 'localhost',
            'POSTGRES_PORT': str(postgres_port),
            'POSTGRES_DB': 'testdb',
            'POSTGRES_USER': 'user',
            'POSTGRES_PASSWORD': 'password',
            'MONGO_HOST': 'localhost',
            'MONGO_PORT': str(mongo_port),
            'MONGO_DB': 'testdb',
            'SQLITE_PATH': '/tmp/test.db'
        })
        
        # Add allocated port assignments to environment
        env.update(self._get_port_env_vars())
        
        # Run the E2E test suite
        cmd = ["python", "run_e2e_tests.py"]
        result = subprocess.run(cmd, capture_output=True, text=True, env=env)
        
        success = result.returncode == 0
        output = result.stdout + result.stderr
        
        return success, output
    
    def cleanup(self):
        """Clean up containers and resources"""
        print("🧹 Cleaning up containers...")
        
        try:
            if self.runtime.name == "podman":
                # Stop and remove containers
                for container in self.containers:
                    subprocess.run([
                        "podman", "stop", container
                    ], capture_output=True)
                    subprocess.run([
                        "podman", "rm", container
                    ], capture_output=True)
                
                # Remove pod
                subprocess.run([
                    "podman", "pod", "rm", self.project_name
                ], capture_output=True)
            else:
                # Use compose to stop and remove
                compose_cmd = self.runtime.compose_command.split()
                cmd = compose_cmd + ["-f", self.compose_file, "down", "-v"]
                subprocess.run(cmd, capture_output=True)
        
        except Exception as e:
            print(f"⚠️  Error during cleanup: {e}")
        
        print("✅ Cleanup completed")
    
    def run_full_test_cycle(self) -> bool:
        """Run the complete test cycle"""
        success = False
        
        try:
            # Detect runtime
            self.detect_runtime()
            
            # Start containers
            if not self.start_containers():
                return False
            
            # Wait for containers to be ready
            if not self.wait_for_containers():
                return False
            
            # Run tests
            test_success, test_output = self.run_tests()
            print(test_output)
            
            success = test_success
            
        except KeyboardInterrupt:
            print("\n⚠️  Test interrupted by user")
        except Exception as e:
            print(f"❌ Test cycle failed: {e}")
        finally:
            # Always cleanup
            self.cleanup()
        
        return success


def signal_handler(signum, frame):
    """Handle interrupt signals"""
    print(f"\n⚠️  Received signal {signum}, cleaning up...")
    sys.exit(1)


def main():
    """Main entry point"""
    # Setup signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    orchestrator = ContainerOrchestrator()
    
    if len(sys.argv) > 1:
        action = sys.argv[1]
        
        if action == "start":
            orchestrator.detect_runtime()
            success = orchestrator.start_containers() and orchestrator.wait_for_containers()
            sys.exit(0 if success else 1)
        
        elif action == "stop":
            orchestrator.detect_runtime()
            orchestrator.cleanup()
            sys.exit(0)
        
        elif action == "test":
            success = orchestrator.run_full_test_cycle()
            sys.exit(0 if success else 1)
        
        elif action == "runtime":
            try:
                runtime = orchestrator.detect_runtime()
                print(f"Detected runtime: {runtime.name} {runtime.version}")
                sys.exit(0)
            except RuntimeError as e:
                print(f"❌ {e}")
                sys.exit(1)
        
        else:
            print(f"Unknown action: {action}")
            sys.exit(1)
    
    else:
        # Default: run full test cycle
        success = orchestrator.run_full_test_cycle()
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
