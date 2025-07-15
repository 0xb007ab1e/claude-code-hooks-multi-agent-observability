import pytest
import requests
from config.test_config import config

@pytest.mark.rest
def test_root_endpoint():
    """Test the root endpoint of the application."""
    response = requests.get(f"{config.server.base_url}/")
    assert response.status_code == 200
    response_data = response.json()
    assert response_data.get("message") == "Multi-Agent Observability Server"

@pytest.mark.rest
def test_event_endpoint():
    """Test sending an event to the /events endpoint."""
    response = requests.post(f"{config.server.base_url}/events", json={
        "source_app": "test",
        "session_id": "test-123",
        "hook_event_type": "PreToolUse",
        "payload": {
            "tool": "Bash",
            "command": "ls -la"
        }
    })
    assert response.status_code == 200
    # The server returns the saved event, not a message
    response_data = response.json()
    assert response_data.get("source_app") == "test"
    assert response_data.get("session_id") == "test-123"
    assert response_data.get("hook_event_type") == "PreToolUse"

@pytest.mark.rest
def test_recent_events_endpoint():
    """Test retrieving recent events from the /events/recent endpoint."""
    response = requests.get(f"{config.server.base_url}/events/recent")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

@pytest.mark.rest
def test_filter_options_endpoint():
    """Test retrieving filter options from the /events/filter-options endpoint."""
    response = requests.get(f"{config.server.base_url}/events/filter-options")
    assert response.status_code == 200
    response_data = response.json()
    assert "source_apps" in response_data
    assert "session_ids" in response_data
    assert "hook_event_types" in response_data
    assert isinstance(response_data["source_apps"], list)
    assert isinstance(response_data["session_ids"], list)
    assert isinstance(response_data["hook_event_types"], list)

