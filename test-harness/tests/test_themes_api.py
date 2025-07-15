import pytest
import requests
import json
import uuid
from config.test_config import config

@pytest.mark.rest
def test_create_theme():
    """Test creating a new theme."""
    theme_data = {
        "name": f"test-theme-{uuid.uuid4()}",
        "displayName": "Test Theme",
        "description": "A test theme for e2e testing",
        "colors": {
            "primary": "#ff0000",
            "secondary": "#00ff00",
            "background": "#ffffff"
        },
        "isPublic": True,
        "authorId": "test-author",
        "authorName": "Test Author",
        "tags": ["test", "e2e"]
    }
    
    response = requests.post(f"{config.server.base_url}/api/themes", json=theme_data)
    assert response.status_code == 201
    response_data = response.json()
    assert response_data["success"] is True
    assert "id" in response_data
    
    return response_data["id"]

@pytest.mark.rest
def test_get_theme():
    """Test retrieving a specific theme."""
    # First create a theme
    theme_id = test_create_theme()
    
    # Then retrieve it
    response = requests.get(f"{config.server.base_url}/api/themes/{theme_id}")
    assert response.status_code == 200
    response_data = response.json()
    assert response_data["success"] is True
    assert response_data["theme"]["id"] == theme_id

@pytest.mark.rest
def test_search_themes():
    """Test searching themes."""
    response = requests.get(f"{config.server.base_url}/api/themes")
    assert response.status_code == 200
    response_data = response.json()
    assert "themes" in response_data
    assert isinstance(response_data["themes"], list)

@pytest.mark.rest
def test_update_theme():
    """Test updating a theme."""
    # First create a theme
    theme_id = test_create_theme()
    
    # Update it
    update_data = {
        "description": "Updated description",
        "colors": {
            "primary": "#0000ff",
            "secondary": "#ffff00",
            "background": "#000000"
        }
    }
    
    response = requests.put(f"{config.server.base_url}/api/themes/{theme_id}", json=update_data)
    assert response.status_code == 200
    response_data = response.json()
    assert response_data["success"] is True

@pytest.mark.rest
def test_delete_theme():
    """Test deleting a theme."""
    # First create a theme
    theme_id = test_create_theme()
    
    # Delete it
    response = requests.delete(f"{config.server.base_url}/api/themes/{theme_id}?authorId=test-author")
    assert response.status_code == 200
    response_data = response.json()
    assert response_data["success"] is True

@pytest.mark.rest
def test_export_theme():
    """Test exporting a theme."""
    # First create a theme
    theme_id = test_create_theme()
    
    # Export it
    response = requests.get(f"{config.server.base_url}/api/themes/{theme_id}/export")
    assert response.status_code == 200
    response_data = response.json()
    assert "theme" in response_data
    assert response_data["theme"]["id"] == theme_id

@pytest.mark.rest
def test_import_theme():
    """Test importing a theme."""
    # First create and export a theme
    theme_id = test_create_theme()
    export_response = requests.get(f"{config.server.base_url}/api/themes/{theme_id}/export")
    export_data = export_response.json()
    
    # Modify the import data to create a new theme
    import_data = export_data.copy()
    import_data["theme"]["name"] = f"imported-theme-{uuid.uuid4()}"
    import_data["theme"]["displayName"] = "Imported Theme"
    
    # Import it
    response = requests.post(f"{config.server.base_url}/api/themes/import?authorId=test-author", json=import_data)
    assert response.status_code == 201
    response_data = response.json()
    assert response_data["success"] is True

@pytest.mark.rest
def test_theme_stats():
    """Test getting theme statistics."""
    response = requests.get(f"{config.server.base_url}/api/themes/stats")
    assert response.status_code == 200
    response_data = response.json()
    assert "success" in response_data
    
@pytest.mark.rest
def test_theme_validation():
    """Test theme validation with invalid data."""
    # Test with missing required fields
    invalid_theme = {
        "name": "invalid-theme"
        # Missing required fields
    }
    
    response = requests.post(f"{config.server.base_url}/api/themes", json=invalid_theme)
    assert response.status_code == 400
    response_data = response.json()
    assert response_data["success"] is False
    
@pytest.mark.rest
def test_theme_not_found():
    """Test accessing non-existent theme."""
    response = requests.get(f"{config.server.base_url}/api/themes/non-existent-id")
    assert response.status_code == 404
    response_data = response.json()
    assert response_data["success"] is False
