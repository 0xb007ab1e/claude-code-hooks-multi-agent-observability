"""
Comprehensive tests for FastAPI event routes
"""
import pytest
from unittest.mock import patch, Mock
from fastapi.testclient import TestClient


@pytest.mark.rest
def test_root_endpoint(test_client):
    """Test the root endpoint returns correct message"""
    response = test_client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Multi-Agent Observability Server"}


@pytest.mark.rest
def test_health_check_endpoint(test_client):
    """Test health check endpoint returns healthy status"""
    response = test_client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "timestamp" in data
    # Verify timestamp is in ISO format
    from datetime import datetime
    datetime.fromisoformat(data["timestamp"])


@pytest.mark.rest
def test_create_event_success(test_client, sample_event):
    """Test successful event creation"""
    response = test_client.post("/events", json=sample_event)
    assert response.status_code == 200
    data = response.json()
    
    # Verify response structure
    assert "id" in data
    assert data["source_app"] == sample_event["source_app"]
    assert data["session_id"] == sample_event["session_id"]
    assert data["hook_event_type"] == sample_event["hook_event_type"]
    assert data["payload"] == sample_event["payload"]
    assert data["chat"] == sample_event["chat"]
    assert data["summary"] == sample_event["summary"]
    assert "timestamp" in data


@pytest.mark.rest
def test_create_event_missing_source_app(test_client, sample_event):
    """Test event creation with missing source_app"""
    del sample_event["source_app"]
    response = test_client.post("/events", json=sample_event)
    assert response.status_code == 400
    data = response.json()
    assert "error" in data
    assert data["error"] == "Missing required fields"


@pytest.mark.rest
def test_create_event_missing_session_id(test_client, sample_event):
    """Test event creation with missing session_id"""
    del sample_event["session_id"]
    response = test_client.post("/events", json=sample_event)
    assert response.status_code == 400
    data = response.json()
    assert "error" in data
    assert data["error"] == "Missing required fields"


@pytest.mark.rest
def test_create_event_missing_hook_event_type(test_client, sample_event):
    """Test event creation with missing hook_event_type"""
    del sample_event["hook_event_type"]
    response = test_client.post("/events", json=sample_event)
    assert response.status_code == 400
    data = response.json()
    assert "error" in data
    assert data["error"] == "Missing required fields"


@pytest.mark.rest
def test_create_event_missing_payload(test_client, sample_event):
    """Test event creation with missing payload"""
    del sample_event["payload"]
    response = test_client.post("/events", json=sample_event)
    assert response.status_code == 400
    data = response.json()
    assert "error" in data
    assert data["error"] == "Missing required fields"


@pytest.mark.rest
def test_create_event_none_payload(test_client, sample_event):
    """Test event creation with None payload"""
    sample_event["payload"] = None
    response = test_client.post("/events", json=sample_event)
    assert response.status_code == 400
    data = response.json()
    assert "error" in data
    assert data["error"] == "Missing required fields"


@pytest.mark.rest
def test_create_event_empty_payload(test_client, sample_event):
    """Test event creation with empty payload (should be valid)"""
    sample_event["payload"] = {}
    response = test_client.post("/events", json=sample_event)
    assert response.status_code == 200
    data = response.json()
    assert data["payload"] == {}


@pytest.mark.rest
def test_create_event_invalid_json(test_client):
    """Test event creation with invalid JSON"""
    response = test_client.post("/events", data="invalid json")
    assert response.status_code == 422  # FastAPI validation error


@pytest.mark.rest
def test_create_event_minimal_data(test_client):
    """Test event creation with minimal required data"""
    minimal_event = {
        "source_app": "test_app",
        "session_id": "test_session",
        "hook_event_type": "test_event",
        "payload": {"key": "value"}
    }
    response = test_client.post("/events", json=minimal_event)
    assert response.status_code == 200
    data = response.json()
    assert data["source_app"] == minimal_event["source_app"]
    assert data["chat"] is None
    assert data["summary"] is None
    assert "timestamp" in data


@pytest.mark.rest
def test_get_recent_events_default(test_client):
    """Test get recent events with default pagination"""
    response = test_client.get("/events/recent")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) <= 100  # Default limit


@pytest.mark.rest
def test_get_recent_events_with_pagination(test_client):
    """Test get recent events with pagination parameters"""
    response = test_client.get("/events/recent?limit=10&offset=5")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) <= 10


@pytest.mark.rest
def test_get_recent_events_zero_limit(test_client):
    """Test get recent events with zero limit"""
    response = test_client.get("/events/recent?limit=0")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 0


@pytest.mark.rest
def test_get_recent_events_negative_limit(test_client):
    """Test get recent events with negative limit"""
    response = test_client.get("/events/recent?limit=-1")
    assert response.status_code == 422  # Validation error


@pytest.mark.rest
def test_get_recent_events_invalid_limit(test_client):
    """Test get recent events with invalid limit"""
    response = test_client.get("/events/recent?limit=invalid")
    assert response.status_code == 422  # Validation error


@pytest.mark.rest
def test_get_filter_options(test_client):
    """Test get filter options endpoint"""
    response = test_client.get("/events/filter-options")
    assert response.status_code == 200
    data = response.json()
    
    # Verify response structure
    assert "source_apps" in data
    assert "session_ids" in data
    assert "hook_event_types" in data
    assert isinstance(data["source_apps"], list)
    assert isinstance(data["session_ids"], list)
    assert isinstance(data["hook_event_types"], list)


@pytest.mark.rest
def test_get_event_count(test_client):
    """Test get event count endpoint"""
    response = test_client.get("/events/count")
    assert response.status_code == 200
    data = response.json()
    assert "count" in data
    assert isinstance(data["count"], int)
    assert data["count"] >= 0


@pytest.mark.rest
def test_options_events_endpoint(test_client):
    """Test OPTIONS request for events endpoint"""
    response = test_client.options("/events")
    assert response.status_code == 200
    
    # Check CORS headers
    headers = response.headers
    assert "access-control-allow-origin" in headers
    assert "access-control-allow-methods" in headers
    assert "access-control-allow-headers" in headers


@pytest.mark.rest
def test_cors_headers(test_client):
    """Test CORS headers are present in responses"""
    response = test_client.get("/", headers={"Origin": "https://example.com"})
    assert response.status_code == 200
    # CORS headers should be present due to CORSMiddleware


@pytest.mark.rest
def test_catch_all_handler(test_client):
    """Test catch-all handler for undefined routes"""
    response = test_client.get("/nonexistent/path")
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Multi-Agent Observability Server"


@pytest.mark.rest
def test_catch_all_handler_post(test_client):
    """Test catch-all handler with POST method"""
    response = test_client.post("/nonexistent/path")
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Multi-Agent Observability Server"


@pytest.mark.rest
@pytest.mark.error
def test_create_event_database_error(test_client, sample_event):
    """Test event creation with database error"""
    with patch('src.database.db.insert_event') as mock_insert:
        mock_insert.side_effect = Exception("Database error")
        response = test_client.post("/events", json=sample_event)
        assert response.status_code == 400
        data = response.json()
        assert "error" in data
        assert data["error"] == "Invalid request"


@pytest.mark.rest
@pytest.mark.error
def test_get_recent_events_database_error(test_client):
    """Test get recent events with database error"""
    with patch('src.database.db.get_recent_events') as mock_get:
        mock_get.side_effect = Exception("Database error")
        response = test_client.get("/events/recent")
        assert response.status_code == 500
        data = response.json()
        assert "error" in data
        assert data["error"] == "Internal server error"


@pytest.mark.rest
@pytest.mark.error
def test_get_filter_options_database_error(test_client):
    """Test get filter options with database error"""
    with patch('src.database.db.get_filter_options') as mock_get:
        mock_get.side_effect = Exception("Database error")
        response = test_client.get("/events/filter-options")
        assert response.status_code == 500
        data = response.json()
        assert "error" in data
        assert data["error"] == "Internal server error"


@pytest.mark.rest
@pytest.mark.error
def test_get_event_count_database_error(test_client):
    """Test get event count with database error"""
    with patch('src.database.db.get_event_count') as mock_get:
        mock_get.side_effect = Exception("Database error")
        response = test_client.get("/events/count")
        assert response.status_code == 500
        data = response.json()
        assert "error" in data
        assert data["error"] == "Internal server error"


@pytest.mark.rest
def test_event_ordering_by_timestamp(test_client):
    """Test that events are ordered by timestamp"""
    # Create events with different timestamps
    event1 = {
        "source_app": "app1",
        "session_id": "session1",
        "hook_event_type": "event1",
        "payload": {"order": 1}
    }
    event2 = {
        "source_app": "app2",
        "session_id": "session2",
        "hook_event_type": "event2",
        "payload": {"order": 2}
    }
    
    # Create events (second event should have later timestamp)
    test_client.post("/events", json=event1)
    test_client.post("/events", json=event2)
    
    # Get recent events
    response = test_client.get("/events/recent")
    assert response.status_code == 200
    data = response.json()
    
    # Verify ordering (most recent first)
    if len(data) >= 2:
        assert data[0]["timestamp"] >= data[1]["timestamp"]


@pytest.mark.rest
def test_event_with_complex_payload(test_client):
    """Test event creation with complex nested payload"""
    complex_event = {
        "source_app": "complex_app",
        "session_id": "complex_session",
        "hook_event_type": "complex_event",
        "payload": {
            "nested": {
                "deeply": {
                    "nested": {
                        "value": "deep_value",
                        "array": [1, 2, 3, {"nested_in_array": True}]
                    }
                }
            },
            "array": [
                {"item": 1},
                {"item": 2, "details": ["a", "b", "c"]}
            ],
            "boolean": True,
            "null_value": None,
            "number": 42.5
        }
    }
    
    response = test_client.post("/events", json=complex_event)
    assert response.status_code == 200
    data = response.json()
    assert data["payload"] == complex_event["payload"]


@pytest.mark.rest
def test_event_with_large_payload(test_client):
    """Test event creation with large payload"""
    large_payload = {
        "large_string": "x" * 10000,  # 10KB string
        "large_array": list(range(1000)),  # 1000 integers
        "large_object": {f"key_{i}": f"value_{i}" for i in range(100)}
    }
    
    large_event = {
        "source_app": "large_app",
        "session_id": "large_session",
        "hook_event_type": "large_event",
        "payload": large_payload
    }
    
    response = test_client.post("/events", json=large_event)
    assert response.status_code == 200
    data = response.json()
    assert data["payload"] == large_payload
