"""
Configuration module for the Python server with dynamic port management.
"""

import os
from typing import Optional


class Config:
    """Configuration settings for the Python server."""
    
    # Server configuration
    PORT: int = int(os.getenv("PORT", "8090"))
    HOST: str = "localhost"
    
    # Database configuration
    POSTGRES_HOST: str = os.getenv("POSTGRES_HOST", "localhost")
    POSTGRES_PORT: int = int(os.getenv("POSTGRES_PORT", "5432"))
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "testdb")
    POSTGRES_USER: str = os.getenv("POSTGRES_USER", "user")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "password")
    
    MONGO_HOST: str = os.getenv("MONGO_HOST", "localhost")
    MONGO_PORT: int = int(os.getenv("MONGO_PORT", "27017"))
    MONGO_DB: str = os.getenv("MONGO_DB", "testdb")
    MONGO_USER: Optional[str] = os.getenv("MONGO_USER")
    MONGO_PASSWORD: Optional[str] = os.getenv("MONGO_PASSWORD")
    
    # SQLite configuration
    SQLITE_PATH: str = os.getenv("SQLITE_PATH", "/tmp/test.db")
    
    # Additional server settings
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    
    @classmethod
    def get_postgres_connection_string(cls) -> str:
        """Get PostgreSQL connection string."""
        return f"postgresql://{cls.POSTGRES_USER}:{cls.POSTGRES_PASSWORD}@{cls.POSTGRES_HOST}:{cls.POSTGRES_PORT}/{cls.POSTGRES_DB}"
    
    @classmethod
    def get_mongo_connection_string(cls) -> str:
        """Get MongoDB connection string."""
        if cls.MONGO_USER and cls.MONGO_PASSWORD:
            return f"mongodb://{cls.MONGO_USER}:{cls.MONGO_PASSWORD}@{cls.MONGO_HOST}:{cls.MONGO_PORT}/{cls.MONGO_DB}"
        return f"mongodb://{cls.MONGO_HOST}:{cls.MONGO_PORT}/{cls.MONGO_DB}"
    
    @classmethod
    def print_config(cls):
        """Print current configuration (for debugging)."""
        print(f"Server Configuration:")
        print(f"  PORT: {cls.PORT}")
        print(f"  HOST: {cls.HOST}")
        print(f"  DEBUG: {cls.DEBUG}")
        print(f"Database Configuration:")
        print(f"  POSTGRES_HOST: {cls.POSTGRES_HOST}")
        print(f"  POSTGRES_PORT: {cls.POSTGRES_PORT}")
        print(f"  POSTGRES_DB: {cls.POSTGRES_DB}")
        print(f"  MONGO_HOST: {cls.MONGO_HOST}")
        print(f"  MONGO_PORT: {cls.MONGO_PORT}")
        print(f"  MONGO_DB: {cls.MONGO_DB}")
        print(f"  SQLITE_PATH: {cls.SQLITE_PATH}")


# Global configuration instance
config = Config()
