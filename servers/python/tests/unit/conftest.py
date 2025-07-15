"""
Pytest configuration for unit tests
"""
import pytest
import os
import sys
import tempfile
import sqlite3
from unittest.mock import Mock, patch, MagicMock
from fastapi.testclient import TestClient
from fastapi import WebSocket
import time

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from main import create_app, get_container
from services import ServiceContainer
from database import Database
from models import HookEvent, Theme, ThemeColors
from config import Settings, settings


@pytest.fixture
def app():
    """Create FastAPI app fixture"""
    return create_app(test_mode=True)


@pytest.fixture
def client(app):
    """Create test client fixture"""
    return TestClient(app)


@pytest.fixture
def mock_db():
    """Create mock database fixture"""
    mock = Mock(spec=Database)
    mock.init_database = Mock()
    mock.insert_event = Mock()
    mock.get_recent_events = Mock(return_value=[])
    mock.get_filter_options = Mock()
    mock.get_event_count = Mock(return_value=0)
    mock.create_theme = Mock()
    mock.search_themes = Mock()
    mock.get_theme_by_id = Mock()
    return mock


@pytest.fixture
def temp_db():
    """Create temporary database fixture"""
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        db_path = tmp.name
    
    db = Database(db_path)
    yield db
    
    # Cleanup
    try:
        os.unlink(db_path)
    except:
        pass


@pytest.fixture
def in_memory_db():
    """Create in-memory database fixture"""
    db = Database(":memory:")
    return db


@pytest.fixture
def sample_hook_event():
    """Create sample HookEvent"""
    return HookEvent(
        id=1,
        source_app="test_app",
        session_id="test_session",
        hook_event_type="PreToolUse",
        payload={"tool": "bash", "command": "ls"},
        chat=[{"role": "user", "content": "test"}],
        summary="Test event",
        timestamp=1640995200000
    )


@pytest.fixture
def sample_theme():
    """Create sample Theme"""
    return Theme(
        id="test_theme",
        name="test-theme",
        displayName="Test Theme",
        description="A test theme",
        colors=ThemeColors(
            primary="#007acc",
            primaryHover="#005a9e",
            primaryLight="#4da6d9",
            primaryDark="#004680",
            bgPrimary="#ffffff",
            bgSecondary="#f5f5f5",
            bgTertiary="#e5e5e5",
            bgQuaternary="#d0d0d0",
            textPrimary="#000000",
            textSecondary="#666666",
            textTertiary="#999999",
            textQuaternary="#cccccc",
            borderPrimary="#cccccc",
            borderSecondary="#e5e5e5",
            borderTertiary="#f0f0f0",
            accentSuccess="#28a745",
            accentWarning="#ffc107",
            accentError="#dc3545",
            accentInfo="#17a2b8",
            shadow="rgba(0, 0, 0, 0.1)",
            shadowLg="rgba(0, 0, 0, 0.2)",
            hoverBg="#f8f9fa",
            activeBg="#e9ecef",
            focusRing="#007acc"
        ),
        isPublic=True,
        authorId="test_author",
        authorName="Test Author",
        createdAt=1640995200000,
        updatedAt=1640995200000,
        tags=["test", "theme"],
        downloadCount=0,
        rating=None,
        ratingCount=0
    )


@pytest.fixture
def mock_websocket():
    """Create mock WebSocket fixture"""
    websocket = Mock(spec=WebSocket)
    websocket.accept = Mock()
    websocket.send_text = Mock()
    websocket.receive_text = Mock()
    websocket.close = Mock()
    return websocket


@pytest.fixture
def mock_container(mock_db):
    """Create mock service container for testing"""
    container = ServiceContainer(mock_db)
    return container


@pytest.fixture
def clean_container():
    """Clean container state before/after test"""
    import main
    original_container = main.container
    main.container = None
    yield
    main.container = original_container


@pytest.fixture
def mock_settings():
    """Create mock settings fixture"""
    mock = Mock(spec=Settings)
    mock.PORT = 8090
    mock.HOST = "0.0.0.0"
    mock.DATABASE_PATH = "test.db"
    mock.CORS_ORIGINS = "*"
    mock.cors_origins_list = ["*"]
    mock.ENVIRONMENT = "test"
    mock.LOG_LEVEL = "info"
    return mock


@pytest.fixture
def clean_env():
    """Clean environment variables for testing"""
    original_env = os.environ.copy()
    
    # Clear relevant environment variables
    test_env_vars = [
        'PORT', 'HOST', 'DATABASE_PATH', 'CORS_ORIGINS', 'POSTGRES_URL',
        'DATABASE_URL', 'DB_PASSWORD', 'DB_HOST', 'DB_PORT', 'DB_NAME',
        'DB_USER', 'API_KEY', 'JWT_SECRET', 'RATE_LIMIT_WINDOW_MS',
        'RATE_LIMIT_MAX_REQUESTS', 'WS_HEARTBEAT_INTERVAL', 'LOG_LEVEL',
        'ENVIRONMENT'
    ]
    
    for var in test_env_vars:
        if var in os.environ:
            del os.environ[var]
    
    yield
    
    # Restore original environment
    os.environ.clear()
    os.environ.update(original_env)


@pytest.fixture
def mock_time():
    """Mock time.time for consistent timestamps"""
    with patch('time.time', return_value=1640995200.0):
        yield


@pytest.fixture
def mock_datetime():
    """Mock datetime for consistent timestamps"""
    with patch('datetime.datetime') as mock_dt:
        mock_dt.now.return_value.isoformat.return_value = "2022-01-01T00:00:00"
        yield mock_dt


@pytest.fixture
def mock_json():
    """Mock json module"""
    with patch('json.dumps') as mock_dumps:
        with patch('json.loads') as mock_loads:
            mock_dumps.return_value = '{"test": "data"}'
            mock_loads.return_value = {"test": "data"}
            yield {"dumps": mock_dumps, "loads": mock_loads}


@pytest.fixture
def mock_sqlite_error():
    """Mock sqlite3 errors"""
    with patch('sqlite3.connect') as mock_connect:
        mock_connect.side_effect = sqlite3.OperationalError("Database is locked")
        yield mock_connect


@pytest.fixture
def mock_logging():
    """Mock logging"""
    with patch('logging.getLogger') as mock_logger:
        logger = Mock()
        mock_logger.return_value = logger
        yield logger


@pytest.fixture(autouse=True)
def reset_database_module():
    """Reset database module state between tests"""
    # This ensures clean state for each test
    yield
    # Any cleanup can go here
