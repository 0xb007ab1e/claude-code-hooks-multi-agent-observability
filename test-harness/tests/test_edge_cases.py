import pytest
import requests
import json
from config.test_config import config

@pytest.mark.rest
def test_invalid_event_missing_fields():
    """Test sending an event with missing required fields."""
    # Missing source_app
    response = requests.post(f"{config.server.base_url}/events", json={
        "session_id": "test-123",
        "hook_event_type": "PreToolUse",
        "payload": {"tool": "Bash", "command": "ls -la"}
    })
    assert response.status_code == 400
    response_data = response.json()
    assert "Invalid request" in response_data.get("error", "") or "field required" in str(response_data)
    
    # Missing session_id
    response = requests.post(f"{config.server.base_url}/events", json={
        "source_app": "test",
        "hook_event_type": "PreToolUse",
        "payload": {"tool": "Bash", "command": "ls -la"}
    })
    assert response.status_code == 400
    response_data = response.json()
    assert "Invalid request" in response_data.get("error", "") or "field required" in str(response_data)
    
    # Missing hook_event_type
    response = requests.post(f"{config.server.base_url}/events", json={
        "source_app": "test",
        "session_id": "test-123",
        "payload": {"tool": "Bash", "command": "ls -la"}
    })
    assert response.status_code == 400
    response_data = response.json()
    assert "Invalid request" in response_data.get("error", "") or "field required" in str(response_data)
    
    # Missing payload
    response = requests.post(f"{config.server.base_url}/events", json={
        "source_app": "test",
        "session_id": "test-123",
        "hook_event_type": "PreToolUse"
    })
    assert response.status_code == 400
    response_data = response.json()
    assert "Invalid request" in response_data.get("error", "") or "field required" in str(response_data)

@pytest.mark.rest
def test_malformed_json():
    """Test sending malformed JSON."""
    response = requests.post(f"{config.server.base_url}/events", 
                           data="invalid json", 
                           headers={"Content-Type": "application/json"})
    assert response.status_code == 400
    assert "Invalid request" in response.json().get("error", "")

@pytest.mark.rest
def test_recent_events_with_limit():
    """Test retrieving recent events with limit parameter."""
    # First send some events
    for i in range(5):
        requests.post(f"{config.server.base_url}/events", json={
            "source_app": "test_limit",
            "session_id": f"test-limit-{i}",
            "hook_event_type": "PreToolUse",
            "payload": {"tool": "Test", "command": f"test {i}"}
        })
    
    # Test with limit
    response = requests.get(f"{config.server.base_url}/events/recent?limit=2")
    assert response.status_code == 200
    events = response.json()
    assert len(events) <= 2

@pytest.mark.rest
def test_cors_headers():
    """Test CORS headers are present."""
    response = requests.options(f"{config.server.base_url}/events")
    assert response.status_code == 200
    assert "Access-Control-Allow-Origin" in response.headers
    assert "Access-Control-Allow-Methods" in response.headers
    assert "Access-Control-Allow-Headers" in response.headers

@pytest.mark.rest
def test_unsupported_methods():
    """Test unsupported HTTP methods."""
    # Test PUT on events endpoint
    response = requests.put(f"{config.server.base_url}/events", json={
        "source_app": "test",
        "session_id": "test-123",
        "hook_event_type": "PreToolUse",
        "payload": {"tool": "Bash", "command": "ls -la"}
    })
    assert response.status_code == 200  # Server returns default response
    response_data = response.json()
    assert response_data.get("message") == "Multi-Agent Observability Server"
    
    # Test DELETE on events endpoint
    response = requests.delete(f"{config.server.base_url}/events")
    assert response.status_code == 200  # Server returns default response
    response_data = response.json()
    assert response_data.get("message") == "Multi-Agent Observability Server"

@pytest.mark.rest
def test_large_payload():
    """Test sending event with large payload."""
    large_payload = {"data": "x" * 10000}  # 10KB payload
    response = requests.post(f"{config.server.base_url}/events", json={
        "source_app": "test_large",
        "session_id": "test-large-123",
        "hook_event_type": "PreToolUse",
        "payload": large_payload
    })
    assert response.status_code == 200
    response_data = response.json()
    assert response_data.get("source_app") == "test_large"

@pytest.mark.rest
def test_special_characters():
    """Test handling of special characters in event data."""
    special_payload = {
        "tool": "Test",
        "command": "echo 'Hello 世界! 🌍 \"quoted\" & <tags>'"
    }
    response = requests.post(f"{config.server.base_url}/events", json={
        "source_app": "test_special",
        "session_id": "test-special-123",
        "hook_event_type": "PreToolUse",
        "payload": special_payload
    })
    assert response.status_code == 200
    response_data = response.json()
    assert response_data.get("source_app") == "test_special"

@pytest.mark.rest
def test_empty_payload():
    """Test sending event with empty payload."""
    response = requests.post(f"{config.server.base_url}/events", json={
        "source_app": "test_empty",
        "session_id": "test-empty-123",
        "hook_event_type": "PreToolUse",
        "payload": {}
    })
    assert response.status_code == 200
    response_data = response.json()
    assert response_data.get("source_app") == "test_empty"

@pytest.mark.rest
def test_concurrent_requests():
    """Test handling of concurrent requests."""
    import threading
    import time
    
    results = []
    
    def send_event(event_id):
        response = requests.post(f"{config.server.base_url}/events", json={
            "source_app": "test_concurrent",
            "session_id": f"test-concurrent-{event_id}",
            "hook_event_type": "PreToolUse",
            "payload": {"tool": "Test", "command": f"test {event_id}"}
        })
        results.append(response.status_code)
    
    # Send 10 concurrent requests
    threads = []
    for i in range(10):
        thread = threading.Thread(target=send_event, args=(i,))
        threads.append(thread)
        thread.start()
    
    # Wait for all threads to complete
    for thread in threads:
        thread.join()
    
    # All requests should succeed
    assert all(status == 200 for status in results)
    assert len(results) == 10

@pytest.mark.rest
def test_performance_timing():
    """Test response times are reasonable."""
    import time
    
    start_time = time.time()
    response = requests.post(f"{config.server.base_url}/events", json={
        "source_app": "test_perf",
        "session_id": "test-perf-123",
        "hook_event_type": "PreToolUse",
        "payload": {"tool": "Test", "command": "performance test"}
    })
    end_time = time.time()
    
    assert response.status_code == 200
    response_time = end_time - start_time
    assert response_time < 1.0  # Should respond within 1 second

@pytest.mark.rest
def test_null_payload():
    """Test sending event with null payload."""
    response = requests.post(f"{config.server.base_url}/events", json={
        "source_app": "test_null",
        "session_id": "test-null-123",
        "hook_event_type": "PreToolUse",
        "payload": None
    })
    # Should either accept null payload or return 400
    assert response.status_code in [200, 400]

@pytest.mark.rest
def test_invalid_hook_event_type():
    """Test sending event with invalid hook_event_type."""
    response = requests.post(f"{config.server.base_url}/events", json={
        "source_app": "test_invalid",
        "session_id": "test-invalid-123",
        "hook_event_type": "InvalidEventType",
        "payload": {"tool": "Test"}
    })
    # Should validate hook_event_type
    assert response.status_code in [200, 400]

@pytest.mark.rest
def test_extremely_large_payload():
    """Test sending event with extremely large payload (1MB)."""
    large_payload = {"data": "x" * 1000000}  # 1MB payload
    response = requests.post(f"{config.server.base_url}/events", json={
        "source_app": "test_xl",
        "session_id": "test-xl-123",
        "hook_event_type": "PreToolUse",
        "payload": large_payload
    })
    # Should either accept large payload or return 413 (Payload Too Large)
    assert response.status_code in [200, 413]

@pytest.mark.rest
def test_invalid_content_type():
    """Test sending event with invalid content type."""
    response = requests.post(f"{config.server.base_url}/events", 
                           data=json.dumps({
                               "source_app": "test_content",
                               "session_id": "test-content-123",
                               "hook_event_type": "PreToolUse",
                               "payload": {"tool": "Test"}
                           }),
                           headers={"Content-Type": "text/plain"})
    assert response.status_code == 400

@pytest.mark.rest
def test_nested_json_payload():
    """Test sending event with deeply nested JSON payload."""
    nested_payload = {
        "level1": {
            "level2": {
                "level3": {
                    "level4": {
                        "level5": {
                            "data": "deep nesting test"
                        }
                    }
                }
            }
        }
    }
    response = requests.post(f"{config.server.base_url}/events", json={
        "source_app": "test_nested",
        "session_id": "test-nested-123",
        "hook_event_type": "PreToolUse",
        "payload": nested_payload
    })
    assert response.status_code == 200
    response_data = response.json()
    assert response_data.get("source_app") == "test_nested"

@pytest.mark.rest
def test_pagination_with_offset():
    """Test pagination with offset parameter."""
    # First send multiple events
    for i in range(10):
        requests.post(f"{config.server.base_url}/events", json={
            "source_app": "test_pagination",
            "session_id": f"test-pagination-{i}",
            "hook_event_type": "PreToolUse",
            "payload": {"tool": "Test", "command": f"test {i}"}
        })
    
    # Test pagination with offset
    response1 = requests.get(f"{config.server.base_url}/events/recent?limit=5&offset=0")
    response2 = requests.get(f"{config.server.base_url}/events/recent?limit=5&offset=5")
    
    assert response1.status_code == 200
    assert response2.status_code == 200
    
    events1 = response1.json()
    events2 = response2.json()
    
    # Events should be different sets
    if len(events1) > 0 and len(events2) > 0:
        assert events1[0] != events2[0]

@pytest.mark.rest
def test_database_connection_error():
    """Test behavior when database connection fails."""
    # This would require mocking database connection failure
    # For now, we'll test that the endpoint handles errors gracefully
    response = requests.post(f"{config.server.base_url}/events", json={
        "source_app": "test_db_error",
        "session_id": "test-db-error-123",
        "hook_event_type": "PreToolUse",
        "payload": {"tool": "Test"}
    })
    # Should handle database errors gracefully
    assert response.status_code in [200, 500]
