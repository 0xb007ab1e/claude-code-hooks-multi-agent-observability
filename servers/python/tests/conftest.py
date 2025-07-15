"""
Pytest configuration file for comprehensive test suite
"""
import pytest
import os
import sys
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient
from fastapi import WebSocket

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from main import create_app
from database import Database
from models import HookEvent, Theme, ThemeColors


@pytest.fixture
def test_client():
    """FastAPI TestClient fixture"""
    # Import here to avoid circular imports
    from database import Database
    import tempfile
    import os
    
    # Create temporary database for testing
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp_db_path = tmp.name
    
    # Monkey patch the global database instance
    test_db = Database(tmp_db_path)
    
    # Create app with test mode
    app = create_app(test_mode=True)
    
    # Patch the database instance in the app
    from services import ServiceContainer
    import main

    # Override the global container with a test-specific one
    test_container = ServiceContainer(test_db)
    original_container = main.container
    main.container = test_container

    try:
        yield TestClient(app)
    finally:
        # Restore original container
        main.container = original_container
        # Clean up
        try:
            os.unlink(tmp_db_path)
        except Exception as e:
            print(f"Error cleaning up test database: {e}")


@pytest.fixture
def in_memory_db():
    """Create in-memory SQLite database for testing"""
    # Create in-memory database
    db = Database(":memory:")
    
    # Verify tables were created using the database's connection
    conn = db._get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    print(f"Tables in database: {[table[0] for table in tables]}")
    
    yield db
    # Cleanup handled by memory disposal


@pytest.fixture
def sample_event():
    """Sample HookEvent data"""
    return {
        "source_app": "test_app",
        "session_id": "test_session_123",
        "hook_event_type": "PreToolUse",
        "payload": {
            "tool": "bash",
            "command": "ls -la",
            "args": ["--color=auto"]
        },
        "chat": [
            {"role": "user", "content": "List files"},
            {"role": "assistant", "content": "I'll list the files for you"}
        ],
        "summary": "User requested file listing"
    }


@pytest.fixture
def sample_theme():
    """Sample Theme data"""
    return {
        "id": "test_theme_123",
        "name": "test-theme",
        "displayName": "Test Theme",
        "description": "A test theme for unit testing",
        "colors": {
            "primary": "#007acc",
            "primaryHover": "#005a9e",
            "primaryLight": "#4da6d9",
            "primaryDark": "#004680",
            "bgPrimary": "#ffffff",
            "bgSecondary": "#f5f5f5",
            "bgTertiary": "#e5e5e5",
            "bgQuaternary": "#d0d0d0",
            "textPrimary": "#000000",
            "textSecondary": "#666666",
            "textTertiary": "#999999",
            "textQuaternary": "#cccccc",
            "borderPrimary": "#cccccc",
            "borderSecondary": "#e5e5e5",
            "borderTertiary": "#f0f0f0",
            "accentSuccess": "#28a745",
            "accentWarning": "#ffc107",
            "accentError": "#dc3545",
            "accentInfo": "#17a2b8",
            "shadow": "rgba(0, 0, 0, 0.1)",
            "shadowLg": "rgba(0, 0, 0, 0.2)",
            "hoverBg": "#f8f9fa",
            "activeBg": "#e9ecef",
            "focusRing": "#007acc"
        },
        "isPublic": True,
        "authorId": "test_author_123",
        "authorName": "Test Author",
        "createdAt": 1640995200000,  # 2022-01-01 00:00:00
        "updatedAt": 1640995200000,
        "tags": ["test", "theme", "blue"],
        "downloadCount": 0,
        "rating": None,
        "ratingCount": 0
    }


@pytest.fixture
def mock_websocket():
    """Mock WebSocket connection"""
    websocket = Mock(spec=WebSocket)
    websocket.accept = Mock()
    websocket.send_text = Mock()
    websocket.receive_text = Mock()
    return websocket


@pytest.fixture
def clean_environment():
    """Clean environment variables for testing"""
    # Store original values
    original_env = {}
    test_env_vars = [
        'PORT', 'HOST', 'DATABASE_PATH', 'CORS_ORIGINS', 'POSTGRES_URL',
        'DATABASE_URL', 'DB_PASSWORD', 'DB_HOST', 'DB_PORT', 'DB_NAME',
        'DB_USER', 'API_KEY', 'JWT_SECRET', 'RATE_LIMIT_WINDOW_MS',
        'RATE_LIMIT_MAX_REQUESTS', 'WS_HEARTBEAT_INTERVAL', 'LOG_LEVEL',
        'ENVIRONMENT'
    ]
    
    for var in test_env_vars:
        if var in os.environ:
            original_env[var] = os.environ[var]
            del os.environ[var]
    
    yield
    
    # Restore original values
    for var, value in original_env.items():
        os.environ[var] = value


@pytest.fixture
def mock_database_error():
    """Mock database connection error"""
    with patch('sqlite3.connect') as mock_connect:
        mock_connect.side_effect = Exception("Database connection failed")
        yield mock_connect


@pytest.fixture
def events_with_data(in_memory_db):
    """Database with sample event data"""
    # Insert sample events
    events = [
        HookEvent(
            source_app="app1",
            session_id="session1",
            hook_event_type="PreToolUse",
            payload={"tool": "bash", "command": "ls"},
            timestamp=1640995200000
        ),
        HookEvent(
            source_app="app2",
            session_id="session2",
            hook_event_type="PostToolUse",
            payload={"tool": "python", "result": "success"},
            timestamp=1640995260000
        ),
        HookEvent(
            source_app="app1",
            session_id="session1",
            hook_event_type="PreToolUse",
            payload={"tool": "git", "command": "status"},
            timestamp=1640995320000
        )
    ]
    
    for event in events:
        in_memory_db.insert_event(event)
    
    return in_memory_db


@pytest.fixture
def themes_with_data(in_memory_db):
    """Database with sample theme data"""
    themes = [
        Theme(
            id="theme1",
            name="dark-theme",
            displayName="Dark Theme",
            description="A dark theme",
            colors=ThemeColors(**{
                "primary": "#ffffff",
                "primaryHover": "#e0e0e0",
                "primaryLight": "#f5f5f5",
                "primaryDark": "#d0d0d0",
                "bgPrimary": "#000000",
                "bgSecondary": "#1a1a1a",
                "bgTertiary": "#333333",
                "bgQuaternary": "#4d4d4d",
                "textPrimary": "#ffffff",
                "textSecondary": "#cccccc",
                "textTertiary": "#999999",
                "textQuaternary": "#666666",
                "borderPrimary": "#666666",
                "borderSecondary": "#4d4d4d",
                "borderTertiary": "#333333",
                "accentSuccess": "#28a745",
                "accentWarning": "#ffc107",
                "accentError": "#dc3545",
                "accentInfo": "#17a2b8",
                "shadow": "rgba(255, 255, 255, 0.1)",
                "shadowLg": "rgba(255, 255, 255, 0.2)",
                "hoverBg": "#2a2a2a",
                "activeBg": "#404040",
                "focusRing": "#ffffff"
            }),
            isPublic=True,
            authorId="author1",
            authorName="Author One",
            createdAt=1640995200000,
            updatedAt=1640995200000,
            tags=["dark", "theme"],
            downloadCount=10,
            rating=4.5,
            ratingCount=2
        ),
        Theme(
            id="theme2",
            name="light-theme",
            displayName="Light Theme",
            description="A light theme",
            colors=ThemeColors(**{
                "primary": "#000000",
                "primaryHover": "#1a1a1a",
                "primaryLight": "#333333",
                "primaryDark": "#000000",
                "bgPrimary": "#ffffff",
                "bgSecondary": "#f8f9fa",
                "bgTertiary": "#e9ecef",
                "bgQuaternary": "#dee2e6",
                "textPrimary": "#000000",
                "textSecondary": "#333333",
                "textTertiary": "#666666",
                "textQuaternary": "#999999",
                "borderPrimary": "#cccccc",
                "borderSecondary": "#e5e5e5",
                "borderTertiary": "#f0f0f0",
                "accentSuccess": "#28a745",
                "accentWarning": "#ffc107",
                "accentError": "#dc3545",
                "accentInfo": "#17a2b8",
                "shadow": "rgba(0, 0, 0, 0.1)",
                "shadowLg": "rgba(0, 0, 0, 0.2)",
                "hoverBg": "#f8f9fa",
                "activeBg": "#e9ecef",
                "focusRing": "#000000"
            }),
            isPublic=False,
            authorId="author2",
            authorName="Author Two",
            createdAt=1640995260000,
            updatedAt=1640995260000,
            tags=["light", "theme"],
            downloadCount=5,
            rating=3.8,
            ratingCount=1
        )
    ]
    
    for theme in themes:
        in_memory_db.create_theme(theme)
    
    return in_memory_db


# Custom pytest markers
def pytest_configure(config):
    """Configure custom pytest markers"""
    config.addinivalue_line("markers", "rest: mark test as REST API test")
    config.addinivalue_line("markers", "websocket: mark test as WebSocket test")
    config.addinivalue_line("markers", "database: mark test as database test")
    config.addinivalue_line("markers", "config: mark test as configuration test")
    config.addinivalue_line("markers", "model: mark test as model test")
    config.addinivalue_line("markers", "error: mark test as error handling test")
    config.addinivalue_line("markers", "slow: mark test as slow running")
