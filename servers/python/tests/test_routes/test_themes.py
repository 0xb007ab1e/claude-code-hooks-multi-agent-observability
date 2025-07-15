"""
Comprehensive tests for FastAPI theme routes
"""
import pytest
from unittest.mock import patch, Mock


@pytest.mark.rest
def test_create_theme_success(test_client, sample_theme):
    """Test successful theme creation"""
    response = test_client.post("/api/themes", json=sample_theme)
    assert response.status_code == 201
    data = response.json()
    
    assert data["success"] is True
    assert data["id"] == sample_theme["id"]
    assert "message" in data


@pytest.mark.rest
def test_create_theme_duplicate_id(test_client, sample_theme):
    """Test theme creation with duplicate ID"""
    # Create theme first time
    response1 = test_client.post("/api/themes", json=sample_theme)
    assert response1.status_code == 201
    
    # Try to create same theme again
    response2 = test_client.post("/api/themes", json=sample_theme)
    assert response2.status_code == 400
    data = response2.json()
    assert data["success"] is False
    assert "already exists" in data["error"]


@pytest.mark.rest
def test_create_theme_invalid_colors(test_client, sample_theme):
    """Test theme creation with invalid color format"""
    sample_theme["colors"]["primary"] = "not-a-color"
    response = test_client.post("/api/themes", json=sample_theme)
    assert response.status_code == 400
    data = response.json()
    assert data["success"] is False


@pytest.mark.rest
def test_create_theme_missing_required_fields(test_client, sample_theme):
    """Test theme creation with missing required fields"""
    del sample_theme["id"]
    response = test_client.post("/api/themes", json=sample_theme)
    assert response.status_code == 400
    data = response.json()
    assert data["success"] is False
    assert "Invalid request body" in data["error"]


@pytest.mark.rest
def test_create_theme_missing_colors(test_client, sample_theme):
    """Test theme creation with missing colors"""
    del sample_theme["colors"]
    response = test_client.post("/api/themes", json=sample_theme)
    assert response.status_code == 400
    data = response.json()
    assert data["success"] is False


@pytest.mark.rest
def test_create_theme_invalid_json(test_client):
    """Test theme creation with invalid JSON"""
    response = test_client.post("/api/themes", data="invalid json")
    assert response.status_code == 422  # FastAPI validation error


@pytest.mark.rest
def test_create_theme_empty_body(test_client):
    """Test theme creation with empty body"""
    response = test_client.post("/api/themes", json={})
    assert response.status_code == 400
    data = response.json()
    assert data["success"] is False
    assert "Invalid request body" in data["error"]


@pytest.mark.rest
def test_get_theme_stats(test_client):
    """Test get theme statistics endpoint"""
    response = test_client.get("/api/themes/stats")
    assert response.status_code == 200
    data = response.json()
    
    assert data["success"] is True
    assert "data" in data
    assert "total" in data["data"]
    assert "public" in data["data"]
    assert "private" in data["data"]
    assert isinstance(data["data"]["total"], int)
    assert isinstance(data["data"]["public"], int)
    assert isinstance(data["data"]["private"], int)


@pytest.mark.rest
def test_search_themes_no_params(test_client):
    """Test search themes with no query parameters"""
    response = test_client.get("/api/themes")
    assert response.status_code == 200
    data = response.json()
    
    assert data["success"] is True
    assert "themes" in data
    assert isinstance(data["themes"], list)


@pytest.mark.rest
def test_search_themes_with_query(test_client, sample_theme):
    """Test search themes with query parameter"""
    # Create a theme first
    test_client.post("/api/themes", json=sample_theme)
    
    # Search for it
    response = test_client.get("/api/themes?query=test")
    assert response.status_code == 200
    data = response.json()
    
    assert data["success"] is True
    assert "themes" in data
    assert isinstance(data["themes"], list)


@pytest.mark.rest
def test_search_themes_public_filter(test_client, sample_theme):
    """Test search themes with public filter"""
    # Create a public theme
    sample_theme["isPublic"] = True
    test_client.post("/api/themes", json=sample_theme)
    
    # Search for public themes
    response = test_client.get("/api/themes?isPublic=true")
    assert response.status_code == 200
    data = response.json()
    
    assert data["success"] is True
    assert "themes" in data
    # All returned themes should be public
    for theme in data["themes"]:
        assert theme["isPublic"] is True


@pytest.mark.rest
def test_search_themes_private_filter(test_client, sample_theme):
    """Test search themes with private filter"""
    # Create a private theme
    sample_theme["isPublic"] = False
    test_client.post("/api/themes", json=sample_theme)
    
    # Search for private themes
    response = test_client.get("/api/themes?isPublic=false")
    assert response.status_code == 200
    data = response.json()
    
    assert data["success"] is True
    assert "themes" in data
    # All returned themes should be private
    for theme in data["themes"]:
        assert theme["isPublic"] is False


@pytest.mark.rest
def test_search_themes_author_filter(test_client, sample_theme):
    """Test search themes with author filter"""
    # Create a theme with specific author
    sample_theme["authorId"] = "specific_author"
    test_client.post("/api/themes", json=sample_theme)
    
    # Search by author
    response = test_client.get("/api/themes?authorId=specific_author")
    assert response.status_code == 200
    data = response.json()
    
    assert data["success"] is True
    assert "themes" in data
    # All returned themes should have the correct author
    for theme in data["themes"]:
        assert theme["authorId"] == "specific_author"


@pytest.mark.rest
def test_search_themes_sort_by_name(test_client):
    """Test search themes with name sorting"""
    response = test_client.get("/api/themes?sortBy=name&sortOrder=asc")
    assert response.status_code == 200
    data = response.json()
    
    assert data["success"] is True
    assert "themes" in data


@pytest.mark.rest
def test_search_themes_sort_by_created(test_client):
    """Test search themes with created date sorting"""
    response = test_client.get("/api/themes?sortBy=created&sortOrder=desc")
    assert response.status_code == 200
    data = response.json()
    
    assert data["success"] is True
    assert "themes" in data


@pytest.mark.rest
def test_search_themes_pagination(test_client):
    """Test search themes with pagination"""
    response = test_client.get("/api/themes?limit=5&offset=0")
    assert response.status_code == 200
    data = response.json()
    
    assert data["success"] is True
    assert "themes" in data
    assert len(data["themes"]) <= 5


@pytest.mark.rest
def test_search_themes_invalid_limit(test_client):
    """Test search themes with invalid limit"""
    response = test_client.get("/api/themes?limit=invalid")
    assert response.status_code == 422  # Validation error


@pytest.mark.rest
def test_search_themes_negative_limit(test_client):
    """Test search themes with negative limit"""
    response = test_client.get("/api/themes?limit=-1")
    assert response.status_code == 422  # Validation error


@pytest.mark.rest
def test_get_theme_by_id_exists(test_client, sample_theme):
    """Test get theme by ID when theme exists"""
    # Create theme first
    test_client.post("/api/themes", json=sample_theme)
    
    # Get theme by ID
    response = test_client.get(f"/api/themes/{sample_theme['id']}")
    assert response.status_code == 200
    data = response.json()
    
    assert data["success"] is True
    assert "theme" in data
    assert data["theme"]["id"] == sample_theme["id"]
    assert data["theme"]["name"] == sample_theme["name"]


@pytest.mark.rest
def test_get_theme_by_id_not_found(test_client):
    """Test get theme by ID when theme doesn't exist"""
    response = test_client.get("/api/themes/nonexistent_id")
    assert response.status_code == 404
    data = response.json()
    
    assert data["success"] is False
    assert "error" in data


@pytest.mark.rest
def test_get_theme_empty_id(test_client):
    """Test get theme with empty ID"""
    response = test_client.get("/api/themes/")
    assert response.status_code == 200  # Hits search endpoint instead
    data = response.json()
    assert data["success"] is True
    assert "themes" in data


@pytest.mark.rest
def test_get_theme_whitespace_id(test_client):
    """Test get theme with whitespace ID"""
    response = test_client.get("/api/themes/   ")
    assert response.status_code == 404
    data = response.json()
    assert data["success"] is False


@pytest.mark.rest
@pytest.mark.error
def test_create_theme_database_error(test_client, sample_theme):
    """Test theme creation with database error"""
    with patch('src.database.db.create_theme') as mock_create:
        mock_create.side_effect = Exception("Database error")
        response = test_client.post("/api/themes", json=sample_theme)
        assert response.status_code == 400
        data = response.json()
        assert data["success"] is False
        assert "Invalid request body" in data["error"]


@pytest.mark.rest
@pytest.mark.error
def test_get_theme_database_error(test_client):
    """Test get theme with database error"""
    with patch('src.database.db.get_theme_by_id') as mock_get:
        mock_get.side_effect = Exception("Database error")
        response = test_client.get("/api/themes/test_id")
        assert response.status_code == 500
        data = response.json()
        assert data["success"] is False
        assert "Internal server error" in data["error"]


@pytest.mark.rest
@pytest.mark.error
def test_search_themes_database_error(test_client):
    """Test search themes with database error"""
    with patch('src.database.db.search_themes') as mock_search:
        mock_search.side_effect = Exception("Database error")
        response = test_client.get("/api/themes")
        assert response.status_code == 500
        data = response.json()
        assert data["success"] is False
        assert "Internal server error" in data["error"]


@pytest.mark.rest
@pytest.mark.error
def test_get_theme_stats_database_error(test_client):
    """Test get theme stats with database error"""
    with patch('src.database.db') as mock_db:
        mock_db.side_effect = Exception("Database error")
        response = test_client.get("/api/themes/stats")
        assert response.status_code == 500
        data = response.json()
        assert data["success"] is False
        assert "Internal server error" in data["error"]


@pytest.mark.rest
def test_theme_with_optional_fields(test_client):
    """Test theme creation with optional fields"""
    theme_with_optional = {
        "id": "optional_theme",
        "name": "optional-theme",
        "displayName": "Optional Theme",
        "description": "Theme with optional fields",
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
        "authorId": "test_author",
        "authorName": "Test Author",
        "createdAt": 1640995200000,
        "updatedAt": 1640995200000,
        "tags": ["test", "optional"],
        "downloadCount": 42,
        "rating": 4.5,
        "ratingCount": 10
    }
    
    response = test_client.post("/api/themes", json=theme_with_optional)
    assert response.status_code == 201
    data = response.json()
    assert data["success"] is True


@pytest.mark.rest
def test_theme_without_optional_fields(test_client):
    """Test theme creation without optional fields"""
    minimal_theme = {
        "id": "minimal_theme",
        "name": "minimal-theme",
        "displayName": "Minimal Theme",
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
        "createdAt": 1640995200000,
        "updatedAt": 1640995200000,
        "tags": []
    }
    
    response = test_client.post("/api/themes", json=minimal_theme)
    assert response.status_code == 201
    data = response.json()
    assert data["success"] is True


@pytest.mark.rest
def test_search_themes_complex_query(test_client, sample_theme):
    """Test search themes with complex query parameters"""
    # Create a theme first
    test_client.post("/api/themes", json=sample_theme)
    
    # Complex search
    response = test_client.get(
        "/api/themes?query=test&isPublic=true&sortBy=name&sortOrder=asc&limit=10&offset=0"
    )
    assert response.status_code == 200
    data = response.json()
    
    assert data["success"] is True
    assert "themes" in data
    assert isinstance(data["themes"], list)


@pytest.mark.rest
def test_theme_id_validation(test_client, sample_theme):
    """Test theme ID validation"""
    # Test with special characters
    sample_theme["id"] = "theme-with-special-chars_123"
    response = test_client.post("/api/themes", json=sample_theme)
    assert response.status_code == 201
    
    # Test with empty ID
    sample_theme["id"] = ""
    response = test_client.post("/api/themes", json=sample_theme)
    assert response.status_code == 400


@pytest.mark.rest
def test_theme_name_validation(test_client, sample_theme):
    """Test theme name validation"""
    # Test with empty name
    sample_theme["name"] = ""
    response = test_client.post("/api/themes", json=sample_theme)
    assert response.status_code == 400
    
    # Test with very long name
    sample_theme["name"] = "a" * 1000
    response = test_client.post("/api/themes", json=sample_theme)
    # Should still work unless there's a specific length limit
    assert response.status_code in [201, 400]
