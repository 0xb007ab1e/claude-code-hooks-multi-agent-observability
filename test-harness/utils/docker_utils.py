"""Docker utilities for managing test containers."""
import docker
import subprocess
import time
import requests
from typing import Optional, Dict, Any
from config.test_config import config

class DockerManager:
    """Manages Docker containers for testing."""
    
    def __init__(self):
        self.client = docker.from_env()
        self.containers = {}
    
    def start_services(self, compose_file: str = None) -> bool:
        """Start services using docker-compose."""
        compose_file = compose_file or config.docker_compose_file
        
        try:
            # Start services
            result = subprocess.run([
                "docker-compose", "-f", compose_file, "up", "-d"
            ], capture_output=True, text=True)
            
            if result.returncode != 0:
                print(f"Failed to start services: {result.stderr}")
                return False
            
            # Wait for services to be ready
            return self.wait_for_services()
            
        except Exception as e:
            print(f"Error starting services: {e}")
            return False
    
    def stop_services(self, compose_file: str = None) -> bool:
        """Stop services using docker-compose."""
        compose_file = compose_file or config.docker_compose_file
        
        try:
            result = subprocess.run([
                "docker-compose", "-f", compose_file, "down"
            ], capture_output=True, text=True)
            
            return result.returncode == 0
            
        except Exception as e:
            print(f"Error stopping services: {e}")
            return False
    
    def wait_for_services(self, timeout: int = 60) -> bool:
        """Wait for services to be ready."""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                # Check if server is responding
                response = requests.get(f"{config.server.base_url}/health", timeout=5)
                if response.status_code == 200:
                    return True
            except requests.exceptions.RequestException:
                pass
            
            time.sleep(2)
        
        return False
    
    def run_container(self, image: str, **kwargs) -> Optional[docker.models.containers.Container]:
        """Run a single container."""
        try:
            container = self.client.containers.run(image, detach=True, **kwargs)
            self.containers[container.id] = container
            return container
        except Exception as e:
            print(f"Error running container: {e}")
            return None
    
    def stop_container(self, container_id: str) -> bool:
        """Stop a specific container."""
        try:
            if container_id in self.containers:
                container = self.containers[container_id]
                container.stop()
                container.remove()
                del self.containers[container_id]
                return True
        except Exception as e:
            print(f"Error stopping container: {e}")
        return False
    
    def cleanup(self):
        """Clean up all managed containers."""
        for container_id in list(self.containers.keys()):
            self.stop_container(container_id)
    
    def get_container_logs(self, container_id: str) -> str:
        """Get logs from a container."""
        try:
            if container_id in self.containers:
                container = self.containers[container_id]
                return container.logs().decode('utf-8')
        except Exception as e:
            print(f"Error getting logs: {e}")
        return ""
    
    def build_image(self, dockerfile_path: str, tag: str) -> bool:
        """Build a Docker image."""
        try:
            image, logs = self.client.images.build(
                path=dockerfile_path,
                tag=tag,
                rm=True
            )
            return True
        except Exception as e:
            print(f"Error building image: {e}")
            return False

# Global Docker manager instance
docker_manager = DockerManager()
