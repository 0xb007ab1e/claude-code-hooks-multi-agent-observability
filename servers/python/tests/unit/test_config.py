import pytest
import os
from unittest.mock import patch
from config import Settings, validate_required_config


def test_settings_default_values(clean_env):
    """Test that Settings has correct default values."""
    settings = Settings()
    assert settings.PORT == 8090
    assert settings.HOST == "0.0.0.0"
    assert settings.DATABASE_PATH == "events.db"
    assert settings.CORS_ORIGINS == "*"
    assert settings.ENVIRONMENT == "development"
    assert settings.LOG_LEVEL == "info"


def test_settings_from_environment(clean_env):
    """Test that Settings reads from environment variables."""
    os.environ["PORT"] = "3000"
    os.environ["HOST"] = "localhost"
    os.environ["DATABASE_PATH"] = "/tmp/test.db"
    os.environ["CORS_ORIGINS"] = "https://example.com"
    os.environ["ENVIRONMENT"] = "production"
    os.environ["LOG_LEVEL"] = "debug"
    
    settings = Settings()
    assert settings.PORT == 3000
    assert settings.HOST == "localhost"
    assert settings.DATABASE_PATH == "/tmp/test.db"
    assert settings.CORS_ORIGINS == "https://example.com"
    assert settings.ENVIRONMENT == "production"
    assert settings.LOG_LEVEL == "debug"


def test_cors_origins_list_single_origin():
    """Test cors_origins_list property with single origin."""
    settings = Settings()
    settings.CORS_ORIGINS = "https://example.com"
    assert settings.cors_origins_list == ["https://example.com"]


def test_cors_origins_list_multiple_origins():
    """Test cors_origins_list property with multiple origins."""
    settings = Settings()
    settings.CORS_ORIGINS = "https://example.com, https://test.com"
    assert settings.cors_origins_list == ["https://example.com", "https://test.com"]


def test_cors_origins_list_wildcard():
    """Test cors_origins_list property with wildcard."""
    settings = Settings()
    settings.CORS_ORIGINS = "*"
    assert settings.cors_origins_list == ["*"]


def test_validate_required_config_development():
    """Test validate_required_config in development environment."""
    settings = Settings()
    settings.ENVIRONMENT = "development"
    
    # Should not raise any exception
    validate_required_config(settings)


def test_validate_required_config_production_success():
    """Test validate_required_config in production with valid config."""
    settings = Settings()
    settings.ENVIRONMENT = "production"
    settings.DATABASE_PATH = "/path/to/db"
    
    # Should not raise any exception
    validate_required_config(settings)


def test_validate_required_config_production_missing_database():
    """Test validate_required_config in production with missing database path."""
    settings = Settings()
    settings.ENVIRONMENT = "production"
    settings.DATABASE_PATH = None
    
    with pytest.raises(ValueError, match="Missing required environment variable: DATABASE_PATH"):
        validate_required_config(settings)


@pytest.mark.parametrize("env_var,value", [
    ("POSTGRES_URL", "postgresql://user:pass@localhost/db"),
    ("DATABASE_URL", "sqlite:///test.db"),
    ("DB_PASSWORD", "secret"),
    ("DB_HOST", "localhost"),
    ("DB_PORT", "5432"),
    ("DB_NAME", "testdb"),
    ("DB_USER", "testuser"),
    ("API_KEY", "secret-key"),
    ("JWT_SECRET", "jwt-secret"),
    ("RATE_LIMIT_WINDOW_MS", "60000"),
    ("RATE_LIMIT_MAX_REQUESTS", "1000"),
    ("WS_HEARTBEAT_INTERVAL", "60000")
])
def test_optional_environment_variables(clean_env, env_var, value):
    """Test that optional environment variables are handled correctly."""
    os.environ[env_var] = value
    settings = Settings()
    
    # Convert to appropriate type for numeric values
    if env_var in ["DB_PORT", "RATE_LIMIT_WINDOW_MS", "RATE_LIMIT_MAX_REQUESTS", "WS_HEARTBEAT_INTERVAL"]:
        expected_value = int(value)
    else:
        expected_value = value
    
    assert getattr(settings, env_var) == expected_value


def test_settings_type_conversion(clean_env):
    """Test that Settings correctly converts string environment variables to appropriate types."""
    os.environ["PORT"] = "9000"
    os.environ["DB_PORT"] = "3306"
    os.environ["RATE_LIMIT_WINDOW_MS"] = "300000"
    os.environ["RATE_LIMIT_MAX_REQUESTS"] = "50"
    os.environ["WS_HEARTBEAT_INTERVAL"] = "45000"
    
    settings = Settings()
    assert isinstance(settings.PORT, int)
    assert isinstance(settings.DB_PORT, int)
    assert isinstance(settings.RATE_LIMIT_WINDOW_MS, int)
    assert isinstance(settings.RATE_LIMIT_MAX_REQUESTS, int)
    assert isinstance(settings.WS_HEARTBEAT_INTERVAL, int)
    
    assert settings.PORT == 9000
    assert settings.DB_PORT == 3306
    assert settings.RATE_LIMIT_WINDOW_MS == 300000
    assert settings.RATE_LIMIT_MAX_REQUESTS == 50
    assert settings.WS_HEARTBEAT_INTERVAL == 45000


def test_settings_with_dotenv_file(clean_env, tmp_path):
    """Test that Settings loads from .env file."""
    env_file = tmp_path / ".env"
    env_file.write_text("PORT=4000\nHOST=0.0.0.0\nDATABASE_PATH=test.db\n")
    
    # Change to temp directory
    original_cwd = os.getcwd()
    os.chdir(tmp_path)
    
    try:
        settings = Settings()
        assert settings.PORT == 4000
        assert settings.HOST == "0.0.0.0"
        assert settings.DATABASE_PATH == "test.db"
    finally:
        os.chdir(original_cwd)


def test_cors_origins_with_spaces():
    """Test cors_origins_list properly handles spaces around commas."""
    settings = Settings()
    settings.CORS_ORIGINS = "https://example.com,  https://test.com  ,https://api.com"
    expected = ["https://example.com", "https://test.com", "https://api.com"]
    assert settings.cors_origins_list == expected


def test_validate_required_config_with_print_output(capsys):
    """Test that validate_required_config prints correct output."""
    settings = Settings()
    settings.ENVIRONMENT = "test"
    settings.PORT = 8080
    settings.DATABASE_PATH = "test.db"
    settings.CORS_ORIGINS = "*"
    
    validate_required_config(settings)
    
    captured = capsys.readouterr()
    assert "✅ Configuration loaded successfully" in captured.out
    assert "📦 Environment: test" in captured.out
    assert "🚀 Server will run on port: 8080" in captured.out
    assert "💾 Database path: test.db" in captured.out
    assert "🌐 CORS origins: *" in captured.out


def test_validate_required_config_with_multiple_cors_origins_output(capsys):
    """Test validate_required_config output with multiple CORS origins."""
    settings = Settings()
    settings.CORS_ORIGINS = "https://test.com,https://api.test.com"
    
    validate_required_config(settings)
    
    captured = capsys.readouterr()
    assert "🌐 CORS origins: https://test.com, https://api.test.com" in captured.out


@pytest.mark.parametrize("field_name,field_value", [
    ("POSTGRES_URL", None),
    ("DATABASE_URL", None),
    ("DB_PASSWORD", None),
    ("DB_HOST", None),
    ("DB_PORT", None),
    ("DB_NAME", None),
    ("DB_USER", None),
    ("API_KEY", None),
    ("JWT_SECRET", None)
])
def test_optional_fields_default_to_none(field_name, field_value):
    """Test that optional fields default to None."""
    settings = Settings()
    assert getattr(settings, field_name) == field_value


def test_settings_edge_case_empty_strings(clean_env):
    """Test Settings with empty string environment variables."""
    os.environ["CORS_ORIGINS"] = ""
    os.environ["DATABASE_PATH"] = ""
    os.environ["HOST"] = ""
    
    settings = Settings()
    # Empty strings should be preserved
    assert settings.CORS_ORIGINS == ""
    assert settings.DATABASE_PATH == ""
    assert settings.HOST == ""


def test_settings_boolean_like_strings(clean_env):
    """Test Settings with boolean-like string values."""
    # These should be treated as strings, not converted to booleans
    os.environ["CORS_ORIGINS"] = "true"
    os.environ["DATABASE_PATH"] = "false"
    
    settings = Settings()
    assert settings.CORS_ORIGINS == "true"
    assert settings.DATABASE_PATH == "false"
