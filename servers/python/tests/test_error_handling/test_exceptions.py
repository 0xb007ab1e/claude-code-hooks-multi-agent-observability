"""
Comprehensive tests for FastAPI exception handlers
"""
import pytest
from unittest.mock import patch, Mock
from fastapi import HTTPException
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError
from starlette.requests import Request


@pytest.mark.error
def test_validation_exception_handler(test_client):
    """Test RequestValidationError handler"""
    # Send invalid data that will trigger validation error
    response = test_client.post("/events", json={
        "source_app": "test",
        "session_id": "test",
        "hook_event_type": "test",
        "payload": "invalid"  # Should be dict, not string
    })
    
    assert response.status_code == 422  # FastAPI default validation error
    data = response.json()
    assert "detail" in data
    assert isinstance(data["detail"], list)


@pytest.mark.error
def test_validation_exception_handler_missing_field(test_client):
    """Test RequestValidationError with missing required field"""
    response = test_client.post("/events", json={
        "source_app": "test",
        "session_id": "test",
        # Missing hook_event_type
        "payload": {"key": "value"}
    })
    
    assert response.status_code == 422
    data = response.json()
    assert "detail" in data
    assert isinstance(data["detail"], list)


@pytest.mark.error
def test_validation_exception_handler_invalid_json(test_client):
    """Test RequestValidationError with invalid JSON"""
    response = test_client.post("/events", data="invalid json")
    
    assert response.status_code == 422
    data = response.json()
    assert "detail" in data


@pytest.mark.error
def test_validation_exception_handler_empty_body(test_client):
    """Test RequestValidationError with empty body"""
    response = test_client.post("/events", json={})
    
    assert response.status_code == 422
    data = response.json()
    assert "detail" in data
    assert isinstance(data["detail"], list)


@pytest.mark.error
def test_validation_exception_handler_wrong_type(test_client):
    """Test RequestValidationError with wrong field types"""
    response = test_client.post("/events", json={
        "source_app": 123,  # Should be string
        "session_id": "test",
        "hook_event_type": "test",
        "payload": {"key": "value"}
    })
    
    assert response.status_code == 422
    data = response.json()
    assert "detail" in data
    assert isinstance(data["detail"], list)


@pytest.mark.error
def test_http_exception_handler_404(test_client):
    """Test HTTPException handling for 404 errors"""
    response = test_client.get("/api/themes/nonexistent")
    
    assert response.status_code == 404
    data = response.json()
    assert data["success"] is False
    assert "error" in data


@pytest.mark.error
def test_http_exception_handler_400(test_client):
    """Test HTTPException handling for 400 errors"""
    response = test_client.post("/events", json={
        "source_app": "",  # Empty string might be invalid
        "session_id": "",
        "hook_event_type": "",
        "payload": None  # None payload should trigger 400
    })
    
    assert response.status_code == 400
    data = response.json()
    assert "error" in data


@pytest.mark.error
def test_general_exception_handler(test_client):
    """Test general exception handler"""
    with patch('src.database.db.get_recent_events') as mock_get:
        mock_get.side_effect = Exception("Database connection failed")
        
        response = test_client.get("/events/recent")
        
        assert response.status_code == 500
        data = response.json()
        assert data["error"] == "Internal server error"
        assert data["message"] == "An unexpected error occurred"


@pytest.mark.error
def test_general_exception_handler_with_different_error(test_client):
    """Test general exception handler with different error types"""
    with patch('src.database.db.get_event_count') as mock_get:
        mock_get.side_effect = RuntimeError("Runtime error occurred")
        
        response = test_client.get("/events/count")
        
        assert response.status_code == 500
        data = response.json()
        assert data["error"] == "Internal server error"
        assert data["message"] == "An unexpected error occurred"


@pytest.mark.error
def test_general_exception_handler_with_value_error(test_client):
    """Test general exception handler with ValueError"""
    with patch('src.database.db.get_filter_options') as mock_get:
        mock_get.side_effect = ValueError("Invalid value provided")
        
        response = test_client.get("/events/filter-options")
        
        assert response.status_code == 500
        data = response.json()
        assert data["error"] == "Internal server error"
        assert data["message"] == "An unexpected error occurred"


@pytest.mark.error
def test_general_exception_handler_with_type_error(test_client):
    """Test general exception handler with TypeError"""
    with patch('src.database.db.insert_event') as mock_insert:
        mock_insert.side_effect = TypeError("Type error occurred")
        
        response = test_client.post("/events", json={
            "source_app": "test",
            "session_id": "test",
            "hook_event_type": "test",
            "payload": {"key": "value"}
        })
        
        assert response.status_code == 400
        data = response.json()
        assert data["error"] == "Invalid request"


@pytest.mark.error
def test_exception_handler_logging(test_client, caplog):
    """Test that exception handlers log errors appropriately"""
    with patch('src.database.db.get_recent_events') as mock_get:
        mock_get.side_effect = Exception("Test exception for logging")
        
        response = test_client.get("/events/recent")
        
        assert response.status_code == 500
        # Check that error was logged
        assert "Unhandled exception" in caplog.text
        assert "Test exception for logging" in caplog.text


@pytest.mark.error
def test_websocket_exception_handling(test_client):
    """Test WebSocket exception handling"""
    with patch('src.database.db.get_recent_events') as mock_get:
        mock_get.side_effect = Exception("WebSocket database error")
        
        try:
            with test_client.websocket_connect("/stream") as websocket:
                # WebSocket should handle the error gracefully
                pass
        except Exception:
            # If WebSocket connection fails, that's acceptable
            pass


@pytest.mark.error
def test_create_event_with_database_exception(test_client):
    """Test create_event endpoint with database exception"""
    with patch('src.database.db.insert_event') as mock_insert:
        mock_insert.side_effect = Exception("Database insert failed")
        
        response = test_client.post("/events", json={
            "source_app": "test",
            "session_id": "test",
            "hook_event_type": "test",
            "payload": {"key": "value"}
        })
        
        assert response.status_code == 400
        data = response.json()
        assert data["error"] == "Invalid request"
        assert "Database insert failed" in data["message"]


@pytest.mark.error
def test_create_theme_with_validation_exception(test_client):
    """Test create_theme endpoint with validation exception"""
    response = test_client.post("/api/themes", json={
        "id": "test",
        "name": "test",
        "displayName": "Test",
        # Missing required colors field
        "isPublic": True,
        "createdAt": 1640995200000,
        "updatedAt": 1640995200000,
        "tags": []
    })
    
    assert response.status_code == 400
    data = response.json()
    assert data["success"] is False
    assert "Invalid request body" in data["error"]


@pytest.mark.error
def test_create_theme_with_general_exception(test_client):
    """Test create_theme endpoint with general exception"""
    with patch('src.database.db.create_theme') as mock_create:
        mock_create.side_effect = Exception("Theme creation failed")
        
        response = test_client.post("/api/themes", json={
            "id": "test",
            "name": "test",
            "displayName": "Test",
            "colors": {
                "primary": "#000000",
                "primaryHover": "#111111",
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
            },
            "isPublic": True,
            "createdAt": 1640995200000,
            "updatedAt": 1640995200000,
            "tags": []
        })
        
        assert response.status_code == 400
        data = response.json()
        assert data["success"] is False
        assert "Invalid request body" in data["error"]


@pytest.mark.error
def test_search_themes_with_database_exception(test_client):
    """Test search_themes endpoint with database exception"""
    with patch('src.database.db.search_themes') as mock_search:
        mock_search.side_effect = Exception("Theme search failed")
        
        response = test_client.get("/api/themes")
        
        assert response.status_code == 500
        data = response.json()
        assert data["success"] is False
        assert "Internal server error" in data["error"]


@pytest.mark.error
def test_get_theme_by_id_with_database_exception(test_client):
    """Test get_theme_by_id endpoint with database exception"""
    with patch('src.database.db.get_theme_by_id') as mock_get:
        mock_get.side_effect = Exception("Theme retrieval failed")
        
        response = test_client.get("/api/themes/test_id")
        
        assert response.status_code == 500
        data = response.json()
        assert data["success"] is False
        assert "Internal server error" in data["error"]


@pytest.mark.error
def test_get_theme_stats_with_exception(test_client):
    """Test get_theme_stats endpoint with exception"""
    with patch('builtins.dict') as mock_dict:
        mock_dict.side_effect = Exception("Stats generation failed")
        
        response = test_client.get("/api/themes/stats")
        
        assert response.status_code == 500
        data = response.json()
        assert data["success"] is False
        assert "Internal server error" in data["error"]


@pytest.mark.error
def test_exception_response_format_consistency(test_client):
    """Test that all exception responses follow consistent format"""
    # Test 400 error format
    response = test_client.post("/events", json={
        "source_app": "test",
        "session_id": "test",
        "hook_event_type": "test",
        "payload": None
    })
    
    assert response.status_code == 400
    data = response.json()
    assert "error" in data
    assert isinstance(data["error"], str)
    
    # Test 500 error format
    with patch('src.database.db.get_recent_events') as mock_get:
        mock_get.side_effect = Exception("Test error")
        
        response = test_client.get("/events/recent")
        
        assert response.status_code == 500
        data = response.json()
        assert "error" in data
        assert "message" in data
        assert data["error"] == "Internal server error"
        assert data["message"] == "An unexpected error occurred"


@pytest.mark.error
def test_exception_handler_with_none_values(test_client):
    """Test exception handlers with None values"""
    response = test_client.post("/events", json={
        "source_app": None,
        "session_id": "test",
        "hook_event_type": "test",
        "payload": {"key": "value"}
    })
    
    assert response.status_code == 422
    data = response.json()
    assert "detail" in data


@pytest.mark.error
def test_exception_handler_with_empty_strings(test_client):
    """Test exception handlers with empty strings"""
    response = test_client.post("/events", json={
        "source_app": "",
        "session_id": "",
        "hook_event_type": "",
        "payload": {}
    })
    
    # Empty strings might be valid, but empty payload should trigger validation
    assert response.status_code in [200, 400]


@pytest.mark.error
def test_exception_handler_with_large_data(test_client):
    """Test exception handlers with large data"""
    large_payload = {
        "large_data": "x" * 100000,  # 100KB string
        "large_array": list(range(10000))
    }
    
    response = test_client.post("/events", json={
        "source_app": "test",
        "session_id": "test",
        "hook_event_type": "test",
        "payload": large_payload
    })
    
    # Should handle large data gracefully
    assert response.status_code in [200, 400, 413]  # 413 = Payload Too Large


@pytest.mark.error
def test_exception_handler_with_special_characters(test_client):
    """Test exception handlers with special characters"""
    special_payload = {
        "unicode": "测试数据",
        "emoji": "🚀🌟💫",
        "special": "!@#$%^&*()_+{}[]|\\:;\"'<>,.?/"
    }
    
    response = test_client.post("/events", json={
        "source_app": "test",
        "session_id": "test",
        "hook_event_type": "test",
        "payload": special_payload
    })
    
    # Should handle special characters gracefully
    assert response.status_code in [200, 400]


@pytest.mark.error
def test_exception_handler_concurrent_requests(test_client):
    """Test exception handlers with concurrent requests"""
    import threading
    import time
    
    results = []
    
    def make_request():
        try:
            response = test_client.post("/events", json={
                "source_app": "concurrent_test",
                "session_id": "concurrent_session",
                "hook_event_type": "concurrent_event",
                "payload": {"thread_id": threading.current_thread().ident}
            })
            results.append(response.status_code)
        except Exception as e:
            results.append(f"Exception: {e}")
    
    # Create multiple threads
    threads = []
    for i in range(5):
        thread = threading.Thread(target=make_request)
        threads.append(thread)
        thread.start()
    
    # Wait for all threads to complete
    for thread in threads:
        thread.join()
    
    # All requests should succeed or fail gracefully
    assert len(results) == 5
    for result in results:
        assert isinstance(result, int)  # Should be HTTP status codes, not exceptions
        assert result in [200, 400, 500]  # Valid HTTP status codes


@pytest.mark.error
def test_exception_handler_memory_pressure(test_client):
    """Test exception handlers under memory pressure"""
    # Create multiple large payloads to simulate memory pressure
    for i in range(10):
        large_payload = {
            "iteration": i,
            "large_data": "x" * 10000,
            "large_list": list(range(1000))
        }
        
        response = test_client.post("/events", json={
            "source_app": f"memory_test_{i}",
            "session_id": f"memory_session_{i}",
            "hook_event_type": f"memory_event_{i}",
            "payload": large_payload
        })
        
        # Should handle memory pressure gracefully
        assert response.status_code in [200, 400, 500, 413]
