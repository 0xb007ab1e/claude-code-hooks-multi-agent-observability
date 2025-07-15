import pytest
from pydantic import ValidationError
from models import HookEvent, Theme, ThemeColors, FilterOptions, EventCount, HealthResponse, ThemeSearchQuery, ApiResponse
import time


def test_hook_event_creation():
    """Test HookEvent model creation."""
    event = HookEvent(
        source_app="test_app",
        session_id="test_session",
        hook_event_type="PreToolUse",
        payload={"tool": "bash"}
    )
    assert event.source_app == "test_app"
    assert event.session_id == "test_session"
    assert event.hook_event_type == "PreToolUse"
    assert event.payload == {"tool": "bash"}


def test_hook_event_timestamp_default():
    """Test that HookEvent has a default timestamp."""
    event = HookEvent(
        source_app="test_app",
        session_id="test_session",
        hook_event_type="PreToolUse",
        payload={"tool": "bash"}
    )
    assert event.timestamp is not None
    assert event.timestamp > 0


def test_hook_event_validation_required_fields():
    """Test that HookEvent requires certain fields."""
    with pytest.raises(ValidationError):
        HookEvent(
            source_app="test_app",
            session_id="test_session",
            # Missing hook_event_type
            payload={"tool": "bash"}
        )


def test_theme_colors_creation():
    """Test ThemeColors model creation."""
    colors = ThemeColors(
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
    )
    assert colors.primary == "#007acc"
    assert colors.bgPrimary == "#ffffff"


def test_theme_creation():
    """Test Theme model creation."""
    colors = ThemeColors(
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
    )
    
    theme = Theme(
        id="test_theme",
        name="test-theme",
        displayName="Test Theme",
        colors=colors,
        isPublic=True,
        createdAt=1640995200000,
        updatedAt=1640995200000,
        tags=["test"]
    )
    assert theme.id == "test_theme"
    assert theme.name == "test-theme"
    assert theme.isPublic is True


def test_filter_options_creation():
    """Test FilterOptions model creation."""
    options = FilterOptions(
        source_apps=["app1", "app2"],
        session_ids=["session1", "session2"],
        hook_event_types=["PreToolUse", "PostToolUse"]
    )
    assert "app1" in options.source_apps
    assert "session1" in options.session_ids
    assert "PreToolUse" in options.hook_event_types


def test_event_count_creation():
    """Test EventCount model creation."""
    count = EventCount(count=42)
    assert count.count == 42


def test_health_response_creation():
    """Test HealthResponse model creation."""
    response = HealthResponse(
        status="healthy",
        timestamp="2022-01-01T00:00:00"
    )
    assert response.status == "healthy"
    assert response.timestamp == "2022-01-01T00:00:00"


def test_theme_search_query_defaults():
    """Test ThemeSearchQuery model with default values."""
    query = ThemeSearchQuery()
    assert query.sortBy == "name"
    assert query.sortOrder == "asc"
    assert query.limit == 10
    assert query.offset == 0


def test_theme_search_query_with_values():
    """Test ThemeSearchQuery model with specific values."""
    query = ThemeSearchQuery(
        query="dark",
        tags=["dark", "theme"],
        authorId="author1",
        isPublic=True,
        sortBy="created",
        sortOrder="desc",
        limit=20,
        offset=10
    )
    assert query.query == "dark"
    assert query.tags == ["dark", "theme"]
    assert query.authorId == "author1"
    assert query.isPublic is True
    assert query.sortBy == "created"
    assert query.sortOrder == "desc"
    assert query.limit == 20
    assert query.offset == 10


def test_api_response_success():
    """Test ApiResponse model for success case."""
    response = ApiResponse(
        success=True,
        data={"id": "test"},
        message="Success"
    )
    assert response.success is True
    assert response.data == {"id": "test"}
    assert response.message == "Success"


def test_api_response_error():
    """Test ApiResponse model for error case."""
    response = ApiResponse(
        success=False,
        error="Something went wrong"
    )
    assert response.success is False
    assert response.error == "Something went wrong"


@pytest.mark.parametrize("field,value", [
    ("source_app", ""),
    ("session_id", ""),
    ("hook_event_type", ""),
    ("payload", {})
])
def test_hook_event_edge_cases(field, value):
    """Test HookEvent with edge case values."""
    data = {
        "source_app": "test_app",
        "session_id": "test_session",
        "hook_event_type": "PreToolUse",
        "payload": {"tool": "bash"}
    }
    data[field] = value
    
    event = HookEvent(**data)
    assert getattr(event, field) == value


@pytest.mark.parametrize("rating,rating_count", [
    (None, 0),
    (4.5, 10),
    (0.0, 1),
    (5.0, 100)
])
def test_theme_rating_variations(rating, rating_count):
    """Test Theme with different rating variations."""
    colors = ThemeColors(
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
    )
    
    theme = Theme(
        id="test_theme",
        name="test-theme",
        displayName="Test Theme",
        colors=colors,
        isPublic=True,
        createdAt=1640995200000,
        updatedAt=1640995200000,
        tags=["test"],
        rating=rating,
        ratingCount=rating_count
    )
    assert theme.rating == rating
    assert theme.ratingCount == rating_count


def test_hook_event_optional_fields():
    """Test HookEvent with optional fields."""
    event = HookEvent(
        source_app="test_app",
        session_id="test_session",
        hook_event_type="PreToolUse",
        payload={"tool": "bash"},
        chat=[{"role": "user", "content": "hello"}],
        summary="Test summary"
    )
    assert event.chat == [{"role": "user", "content": "hello"}]
    assert event.summary == "Test summary"


def test_theme_optional_fields():
    """Test Theme with optional fields."""
    colors = ThemeColors(
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
    )
    
    theme = Theme(
        id="test_theme",
        name="test-theme",
        displayName="Test Theme",
        colors=colors,
        isPublic=True,
        createdAt=1640995200000,
        updatedAt=1640995200000,
        tags=["test"],
        description="Test description",
        authorId="author1",
        authorName="Author One",
        downloadCount=10
    )
    assert theme.description == "Test description"
    assert theme.authorId == "author1"
    assert theme.authorName == "Author One"
    assert theme.downloadCount == 10
