"""Test configuration for the language-agnostic test suite."""
import os
from dataclasses import dataclass
from typing import Dict, List, Optional
from dotenv import load_dotenv
from .port_manager import assign_port, get_port

load_dotenv()

@dataclass
class ServerConfig:
    """Configuration for the server under test."""
    host: str = os.getenv("SERVER_HOST", "localhost")
    port: int = int(os.getenv("SERVER_PORT", os.getenv("HTTP_SERVER_PORT", os.getenv("PORT", "8090"))))
    protocol: str = os.getenv("SERVER_PROTOCOL", "http")
    ws_protocol: str = os.getenv("WS_PROTOCOL", "ws")
    
    @property
    def base_url(self) -> str:
        return f"{self.protocol}://{self.host}:{self.port}"
    
    @property
    def ws_url(self) -> str:
        return f"{self.ws_protocol}://{self.host}:{self.port}"

@dataclass
class DatabaseConfig:
    """Configuration for database connections."""
    postgres_host: str = os.getenv("POSTGRES_HOST", "localhost")
    postgres_port: int = int(os.getenv("POSTGRES_PORT", str(assign_port("postgres", "PostgreSQL Database"))))
    postgres_db: str = os.getenv("POSTGRES_DB", "testdb")
    postgres_user: str = os.getenv("POSTGRES_USER", "user")
    postgres_password: str = os.getenv("POSTGRES_PASSWORD", "password")
    
    sqlite_path: str = os.getenv("SQLITE_PATH", "test.db")
    
    mongo_host: str = os.getenv("MONGO_HOST", "localhost")
    mongo_port: int = int(os.getenv("MONGO_PORT", str(assign_port("mongo", "MongoDB Database"))))
    mongo_db: str = os.getenv("MONGO_DB", "testdb")

from dataclasses import field

@dataclass
class TestConfig:
    """Main test configuration."""
    server: ServerConfig = field(default_factory=ServerConfig)
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    
    # Test timeouts
    request_timeout: int = int(os.getenv("REQUEST_TIMEOUT", "30"))
    websocket_timeout: int = int(os.getenv("WEBSOCKET_TIMEOUT", "30"))
    
    # Test data
    test_data_dir: str = os.getenv("TEST_DATA_DIR", "test-data")
    
    # Docker configuration
    docker_compose_file: str = os.getenv("DOCKER_COMPOSE_FILE", "../docker-compose.yml")
    server_image: str = os.getenv("SERVER_IMAGE", "your_server_image")
    
    # Expected API endpoints
    expected_endpoints: List[str] = field(default_factory=lambda: [
        "/",
        "/events",
        "/events/recent",
        "/events/filter-options",
        "/api/themes",
        "/api/themes/stats"
    ])
    
    # Expected WebSocket endpoints
    expected_ws_endpoints: List[str] = field(default_factory=lambda: [
        "/stream"
    ])

# Global test configuration instance
config = TestConfig()
