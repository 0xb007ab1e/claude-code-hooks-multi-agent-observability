from typing import List, Optional
from pydantic import BaseSettings, Field
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Settings(BaseSettings):
    # Server configuration
    PORT: int = Field(default=8090, env='PORT')
    HOST: str = Field(default='0.0.0.0', env='HOST')

    # Database configuration
    DATABASE_PATH: str = Field(default='events.db', env='DATABASE_PATH')

    # CORS configuration
    CORS_ORIGINS: str = Field(default='*', env='CORS_ORIGINS')

    # Optional: Future PostgreSQL support
    POSTGRES_URL: Optional[str] = Field(default=None, env='POSTGRES_URL')

    # Alternative database connection variables
    DATABASE_URL: Optional[str] = Field(default=None, env='DATABASE_URL')
    DB_PASSWORD: Optional[str] = Field(default=None, env='DB_PASSWORD')
    DB_HOST: Optional[str] = Field(default=None, env='DB_HOST')
    DB_PORT: Optional[int] = Field(default=None, env='DB_PORT')
    DB_NAME: Optional[str] = Field(default=None, env='DB_NAME')
    DB_USER: Optional[str] = Field(default=None, env='DB_USER')

    # Optional: Authentication/API keys
    API_KEY: Optional[str] = Field(default=None, env='API_KEY')
    JWT_SECRET: Optional[str] = Field(default=None, env='JWT_SECRET')

    # Optional: Rate limiting
    RATE_LIMIT_WINDOW_MS: int = Field(default=900000, env='RATE_LIMIT_WINDOW_MS')  # 15 minutes
    RATE_LIMIT_MAX_REQUESTS: int = Field(default=100, env='RATE_LIMIT_MAX_REQUESTS')

    # Optional: WebSocket configuration
    WS_HEARTBEAT_INTERVAL: int = Field(default=30000, env='WS_HEARTBEAT_INTERVAL')  # 30 seconds

    # Optional: Logging level
    LOG_LEVEL: str = Field(default='info', env='LOG_LEVEL')

    # Environment
    ENVIRONMENT: str = Field(default='development', env='ENVIRONMENT')

    @property
    def cors_origins_list(self) -> List[str]:
        if self.CORS_ORIGINS == '*':
            return ['*']
        return [origin.strip() for origin in self.CORS_ORIGINS.split(',')]

    class Config:
        env_file = '.env'
        env_file_encoding = 'utf-8'


# Create settings instance
settings = Settings()


def validate_required_config(config_settings=None, silent=False):
    """Validate required configuration on startup"""
    # Use passed settings or global settings
    config = config_settings or settings

    required_in_production = ['DATABASE_PATH']

    if config.ENVIRONMENT == 'production':
        for key in required_in_production:
            if not getattr(config, key):
                raise ValueError(f"Missing required environment variable: {key}")

    if not silent:
        print('✅ Configuration loaded successfully')
        print(f'📦 Environment: {config.ENVIRONMENT}')
        print(f'🚀 Server will run on port: {config.PORT}')
        print(f'💾 Database path: {config.DATABASE_PATH}')
        print(f'🌐 CORS origins: {", ".join(config.cors_origins_list)}')

    return True
