"""
Comprehensive tests for configuration precedence and validation
"""
import pytest
import os
from unittest.mock import patch
from src.config import Settings, validate_required_config


@pytest.mark.config
def test_config_defaults(clean_environment):
    """Test configuration with default values"""
    settings = Settings()
    assert settings.PORT == 8090
    assert settings.HOST == "0.0.0.0"
    assert settings.DATABASE_PATH == "events.db"
    assert settings.CORS_ORIGINS == "*"
    assert settings.LOG_LEVEL == "info"
    assert settings.ENVIRONMENT == "development"
    assert settings.RATE_LIMIT_WINDOW_MS == 900000
    assert settings.RATE_LIMIT_MAX_REQUESTS == 100
    assert settings.WS_HEARTBEAT_INTERVAL == 30000


@pytest.mark.config
def test_config_env_override_port(clean_environment):
    """Test PORT environment variable override"""
    os.environ["PORT"] = "9000"
    settings = Settings()
    assert settings.PORT == 9000


@pytest.mark.config
def test_config_env_override_host(clean_environment):
    """Test HOST environment variable override"""
    os.environ["HOST"] = "127.0.0.1"
    settings = Settings()
    assert settings.HOST == "127.0.0.1"


@pytest.mark.config
def test_config_env_override_database_path(clean_environment):
    """Test DATABASE_PATH environment variable override"""
    os.environ["DATABASE_PATH"] = "/custom/path/events.db"
    settings = Settings()
    assert settings.DATABASE_PATH == "/custom/path/events.db"


@pytest.mark.config
def test_config_env_override_cors_origins(clean_environment):
    """Test CORS_ORIGINS environment variable override"""
    os.environ["CORS_ORIGINS"] = "https://example.com"
    settings = Settings()
    assert settings.CORS_ORIGINS == "https://example.com"


@pytest.mark.config
def test_config_env_override_log_level(clean_environment):
    """Test LOG_LEVEL environment variable override"""
    os.environ["LOG_LEVEL"] = "debug"
    settings = Settings()
    assert settings.LOG_LEVEL == "debug"


@pytest.mark.config
def test_config_env_override_environment(clean_environment):
    """Test ENVIRONMENT environment variable override"""
    os.environ["ENVIRONMENT"] = "production"
    settings = Settings()
    assert settings.ENVIRONMENT == "production"


@pytest.mark.config
def test_config_cors_origins_single_domain(clean_environment):
    """Test CORS_ORIGINS with single domain"""
    os.environ["CORS_ORIGINS"] = "https://example.com"
    settings = Settings()
    assert settings.cors_origins_list == ["https://example.com"]


@pytest.mark.config
def test_config_cors_origins_multiple_domains(clean_environment):
    """Test CORS_ORIGINS with multiple domains"""
    os.environ["CORS_ORIGINS"] = "https://example.com,https://api.example.com,http://localhost:3000"
    settings = Settings()
    expected = ["https://example.com", "https://api.example.com", "http://localhost:3000"]
    assert settings.cors_origins_list == expected


@pytest.mark.config
def test_config_cors_origins_wildcard(clean_environment):
    """Test CORS_ORIGINS with wildcard"""
    os.environ["CORS_ORIGINS"] = "*"
    settings = Settings()
    assert settings.cors_origins_list == ["*"]


@pytest.mark.config
def test_config_cors_origins_with_whitespace(clean_environment):
    """Test CORS_ORIGINS with whitespace around domains"""
    os.environ["CORS_ORIGINS"] = "  https://example.com  , https://api.example.com  "
    settings = Settings()
    expected = ["https://example.com", "https://api.example.com"]
    assert settings.cors_origins_list == expected


@pytest.mark.config
def test_config_optional_postgres_config(clean_environment):
    """Test optional PostgreSQL configuration"""
    os.environ["POSTGRES_URL"] = "postgresql://user:pass@localhost:5432/db"
    os.environ["DATABASE_URL"] = "postgresql://user:pass@localhost:5432/db"
    os.environ["DB_PASSWORD"] = "secret"
    os.environ["DB_HOST"] = "localhost"
    os.environ["DB_PORT"] = "5432"
    os.environ["DB_NAME"] = "mydb"
    os.environ["DB_USER"] = "myuser"
    
    settings = Settings()
    assert settings.POSTGRES_URL == "postgresql://user:pass@localhost:5432/db"
    assert settings.DATABASE_URL == "postgresql://user:pass@localhost:5432/db"
    assert settings.DB_PASSWORD == "secret"
    assert settings.DB_HOST == "localhost"
    assert settings.DB_PORT == 5432
    assert settings.DB_NAME == "mydb"
    assert settings.DB_USER == "myuser"


@pytest.mark.config
def test_config_optional_auth_config(clean_environment):
    """Test optional authentication configuration"""
    os.environ["API_KEY"] = "secret-api-key"
    os.environ["JWT_SECRET"] = "jwt-secret-key"
    
    settings = Settings()
    assert settings.API_KEY == "secret-api-key"
    assert settings.JWT_SECRET == "jwt-secret-key"


@pytest.mark.config
def test_config_rate_limit_config(clean_environment):
    """Test rate limiting configuration"""
    os.environ["RATE_LIMIT_WINDOW_MS"] = "60000"  # 1 minute
    os.environ["RATE_LIMIT_MAX_REQUESTS"] = "50"
    
    settings = Settings()
    assert settings.RATE_LIMIT_WINDOW_MS == 60000
    assert settings.RATE_LIMIT_MAX_REQUESTS == 50


@pytest.mark.config
def test_config_websocket_config(clean_environment):
    """Test WebSocket configuration"""
    os.environ["WS_HEARTBEAT_INTERVAL"] = "60000"  # 1 minute
    
    settings = Settings()
    assert settings.WS_HEARTBEAT_INTERVAL == 60000


@pytest.mark.config
def test_config_all_env_vars_override(clean_environment):
    """Test that all environment variables override defaults"""
    env_vars = {
        "PORT": "9090",
        "HOST": "192.168.1.100",
        "DATABASE_PATH": "/tmp/test.db",
        "CORS_ORIGINS": "https://test.com,https://api.test.com",
        "POSTGRES_URL": "postgresql://test:test@localhost:5432/test",
        "DATABASE_URL": "sqlite:///test.db",
        "DB_PASSWORD": "testpass",
        "DB_HOST": "testhost",
        "DB_PORT": "5433",
        "DB_NAME": "testdb",
        "DB_USER": "testuser",
        "API_KEY": "test-api-key",
        "JWT_SECRET": "test-jwt-secret",
        "RATE_LIMIT_WINDOW_MS": "120000",
        "RATE_LIMIT_MAX_REQUESTS": "200",
        "WS_HEARTBEAT_INTERVAL": "45000",
        "LOG_LEVEL": "warning",
        "ENVIRONMENT": "test"
    }
    
    for key, value in env_vars.items():
        os.environ[key] = value
    
    settings = Settings()
    assert settings.PORT == 9090
    assert settings.HOST == "192.168.1.100"
    assert settings.DATABASE_PATH == "/tmp/test.db"
    assert settings.CORS_ORIGINS == "https://test.com,https://api.test.com"
    assert settings.POSTGRES_URL == "postgresql://test:test@localhost:5432/test"
    assert settings.DATABASE_URL == "sqlite:///test.db"
    assert settings.DB_PASSWORD == "testpass"
    assert settings.DB_HOST == "testhost"
    assert settings.DB_PORT == 5433
    assert settings.DB_NAME == "testdb"
    assert settings.DB_USER == "testuser"
    assert settings.API_KEY == "test-api-key"
    assert settings.JWT_SECRET == "test-jwt-secret"
    assert settings.RATE_LIMIT_WINDOW_MS == 120000
    assert settings.RATE_LIMIT_MAX_REQUESTS == 200
    assert settings.WS_HEARTBEAT_INTERVAL == 45000
    assert settings.LOG_LEVEL == "warning"
    assert settings.ENVIRONMENT == "test"


@pytest.mark.config
def test_production_config_validation_success(clean_environment):
    """Test production configuration validation with required variables"""
    os.environ["ENVIRONMENT"] = "production"
    os.environ["DATABASE_PATH"] = "/production/events.db"
    
    # Create fresh settings instance with the new environment
    settings = Settings()
    
    # Should not raise any errors
    validate_required_config(settings)


@pytest.mark.config
def test_production_config_validation_failure(clean_environment):
    """Test production configuration validation without required variables"""
    os.environ["ENVIRONMENT"] = "production"
    os.environ["DATABASE_PATH"] = ""  # Empty DATABASE_PATH should fail in production
    
    # Create fresh settings instance with the new environment
    settings = Settings()
    
    with pytest.raises(ValueError, match="Missing required environment variable: DATABASE_PATH"):
        validate_required_config(settings)


@pytest.mark.config
def test_development_config_lenient(clean_environment):
    """Test development configuration is lenient"""
    os.environ["ENVIRONMENT"] = "development"
    # DATABASE_PATH not required in development
    
    # Should not raise any errors
    validate_required_config()


@pytest.mark.config
def test_config_type_conversion(clean_environment):
    """Test that environment variables are properly converted to correct types"""
    os.environ["PORT"] = "8080"
    os.environ["DB_PORT"] = "5432"
    os.environ["RATE_LIMIT_WINDOW_MS"] = "300000"
    os.environ["RATE_LIMIT_MAX_REQUESTS"] = "75"
    os.environ["WS_HEARTBEAT_INTERVAL"] = "25000"
    
    settings = Settings()
    assert isinstance(settings.PORT, int)
    assert isinstance(settings.DB_PORT, int)
    assert isinstance(settings.RATE_LIMIT_WINDOW_MS, int)
    assert isinstance(settings.RATE_LIMIT_MAX_REQUESTS, int)
    assert isinstance(settings.WS_HEARTBEAT_INTERVAL, int)


@pytest.mark.config
def test_config_invalid_port_type(clean_environment):
    """Test invalid PORT type handling"""
    os.environ["PORT"] = "invalid"
    
    with pytest.raises(ValueError):
        Settings()


@pytest.mark.config
def test_config_invalid_db_port_type(clean_environment):
    """Test invalid DB_PORT type handling"""
    os.environ["DB_PORT"] = "invalid"
    
    with pytest.raises(ValueError):
        Settings()


@pytest.mark.config
def test_config_invalid_rate_limit_window_type(clean_environment):
    """Test invalid RATE_LIMIT_WINDOW_MS type handling"""
    os.environ["RATE_LIMIT_WINDOW_MS"] = "invalid"
    
    with pytest.raises(ValueError):
        Settings()


@pytest.mark.config
def test_config_invalid_rate_limit_max_type(clean_environment):
    """Test invalid RATE_LIMIT_MAX_REQUESTS type handling"""
    os.environ["RATE_LIMIT_MAX_REQUESTS"] = "invalid"
    
    with pytest.raises(ValueError):
        Settings()


@pytest.mark.config
def test_config_invalid_ws_heartbeat_type(clean_environment):
    """Test invalid WS_HEARTBEAT_INTERVAL type handling"""
    os.environ["WS_HEARTBEAT_INTERVAL"] = "invalid"
    
    with pytest.raises(ValueError):
        Settings()


@pytest.mark.config
def test_config_negative_port(clean_environment):
    """Test negative port number handling"""
    os.environ["PORT"] = "-1"
    
    # Pydantic should handle validation
    settings = Settings()
    assert settings.PORT == -1  # Pydantic allows negative integers by default


@pytest.mark.config
def test_config_zero_port(clean_environment):
    """Test zero port number"""
    os.environ["PORT"] = "0"
    
    settings = Settings()
    assert settings.PORT == 0


@pytest.mark.config
def test_config_large_port(clean_environment):
    """Test large port number"""
    os.environ["PORT"] = "65535"
    
    settings = Settings()
    assert settings.PORT == 65535


@pytest.mark.config
def test_config_empty_string_values(clean_environment):
    """Test empty string values"""
    os.environ["HOST"] = ""
    os.environ["DATABASE_PATH"] = ""
    os.environ["CORS_ORIGINS"] = ""
    
    settings = Settings()
    assert settings.HOST == ""
    assert settings.DATABASE_PATH == ""
    assert settings.CORS_ORIGINS == ""
    assert settings.cors_origins_list == [""]


@pytest.mark.config
def test_config_whitespace_values(clean_environment):
    """Test whitespace values"""
    os.environ["HOST"] = "   "
    os.environ["DATABASE_PATH"] = "  "
    
    settings = Settings()
    assert settings.HOST == "   "
    assert settings.DATABASE_PATH == "  "


@pytest.mark.config
def test_config_case_sensitivity(clean_environment):
    """Test that environment variables are case sensitive"""
    os.environ["port"] = "9000"  # lowercase
    os.environ["PORT"] = "8080"  # uppercase
    
    settings = Settings()
    # Should use uppercase version
    assert settings.PORT == 8080


@pytest.mark.config
def test_config_boolean_like_strings(clean_environment):
    """Test boolean-like string values"""
    os.environ["ENVIRONMENT"] = "true"
    os.environ["LOG_LEVEL"] = "false"
    
    settings = Settings()
    # These should be treated as strings, not booleans
    assert settings.ENVIRONMENT == "true"
    assert settings.LOG_LEVEL == "false"


@pytest.mark.config
def test_config_unicode_values(clean_environment):
    """Test Unicode values in configuration"""
    os.environ["DATABASE_PATH"] = "/path/数据库/events.db"
    os.environ["CORS_ORIGINS"] = "https://测试.com"
    
    settings = Settings()
    assert settings.DATABASE_PATH == "/path/数据库/events.db"
    assert settings.CORS_ORIGINS == "https://测试.com"


@pytest.mark.config
def test_config_special_characters(clean_environment):
    """Test special characters in configuration"""
    os.environ["DATABASE_PATH"] = "/path/with spaces/events.db"
    os.environ["API_KEY"] = "key-with-special-chars!@#$%^&*()"
    
    settings = Settings()
    assert settings.DATABASE_PATH == "/path/with spaces/events.db"
    assert settings.API_KEY == "key-with-special-chars!@#$%^&*()"


@pytest.mark.config
def test_config_very_long_values(clean_environment):
    """Test very long configuration values"""
    long_value = "x" * 10000
    os.environ["DATABASE_PATH"] = long_value
    
    settings = Settings()
    assert settings.DATABASE_PATH == long_value


@pytest.mark.config
def test_config_validation_output(clean_environment, capsys):
    """Test configuration validation output"""
    os.environ["ENVIRONMENT"] = "test"
    os.environ["PORT"] = "8080"
    os.environ["DATABASE_PATH"] = "/test/events.db"
    os.environ["CORS_ORIGINS"] = "https://test.com"
    
    # Create new settings instance to pick up the environment changes
    test_settings = Settings()
    validate_required_config(test_settings)
    
    captured = capsys.readouterr()
    assert "✅ Configuration loaded successfully" in captured.out
    assert "📦 Environment: test" in captured.out
    assert "🚀 Server will run on port: 8080" in captured.out
    assert "💾 Database path: /test/events.db" in captured.out
    assert "🌐 CORS origins: https://test.com" in captured.out


@pytest.mark.config
def test_config_validation_multiple_cors_origins_output(clean_environment, capsys):
    """Test configuration validation output with multiple CORS origins"""
    os.environ["CORS_ORIGINS"] = "https://test.com,https://api.test.com"
    
    # Create new settings instance to pick up the environment changes
    test_settings = Settings()
    validate_required_config(test_settings)
    
    captured = capsys.readouterr()
    assert "🌐 CORS origins: https://test.com, https://api.test.com" in captured.out


@pytest.mark.config
def test_config_settings_instance_reuse():
    """Test that Settings instances work correctly"""
    settings1 = Settings()
    settings2 = Settings()
    
    # Both should have same default values
    assert settings1.PORT == settings2.PORT
    assert settings1.HOST == settings2.HOST
    assert settings1.DATABASE_PATH == settings2.DATABASE_PATH


@pytest.mark.config
def test_config_env_file_support(clean_environment):
    """Test that .env file support is configured"""
    settings = Settings()
    
    # Check that Config class has env_file set
    assert hasattr(settings.Config, 'env_file')
    assert settings.Config.env_file == '.env'
    assert settings.Config.env_file_encoding == 'utf-8'
