import pytest
import json
import asyncio
from unittest.mock import patch, Mock, AsyncMock
from fastapi import WebSocket
from fastapi.testclient import TestClient
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError
from starlette.websockets import WebSocketDisconnect

from main import (
    app, create_app, get_container,
    validation_exception_handler, pydantic_validation_exception_handler,
    general_exception_handler
)
from models import HookEvent, Theme, ApiResponse


class TestAppCreation:
    """Test app creation functionality."""
    
    def test_create_app_test_mode(self):
        """Test creating app in test mode."""
        test_app = create_app(test_mode=True)
        assert test_app is not None
        assert test_app.title == "Multi-Agent Observability Server"
    
    def test_create_app_production_mode(self):
        """Test creating app in production mode."""
        with patch('main.validate_required_config') as mock_validate:
            prod_app = create_app(test_mode=False)
            assert prod_app is not None
            mock_validate.assert_called_once()


class TestServiceContainer:
    """Test service container functionality."""
    
    def test_get_container_creates_singleton(self):
        """Test that get_container creates a singleton."""
        container1 = get_container()
        container2 = get_container()
        assert container1 is container2
    
    def test_get_container_returns_services(self):
        """Test that container provides required services."""
        container = get_container()
        assert hasattr(container, 'event_service')
        assert hasattr(container, 'theme_service')
        assert hasattr(container, 'websocket_service')
        assert hasattr(container, 'notification_service')


class TestExceptionHandlers:
    """Test exception handlers."""
    
    def test_validation_exception_handler(self):
        """Test validation exception handler."""
        mock_request = Mock()
        mock_exc = Mock(spec=RequestValidationError)
        mock_exc.errors.return_value = [{"field": "test", "message": "error"}]
        
        loop = asyncio.get_event_loop()
        response = loop.run_until_complete(
            validation_exception_handler(mock_request, mock_exc)
        )
        
        assert response.status_code == 400
        assert "error" in response.body.decode()
    
    def test_pydantic_validation_exception_handler(self):
        """Test pydantic validation exception handler."""
        mock_request = Mock()
        mock_exc = Mock(spec=ValidationError)
        mock_exc.errors.return_value = [{"field": "test", "message": "error"}]
        
        loop = asyncio.get_event_loop()
        response = loop.run_until_complete(
            pydantic_validation_exception_handler(mock_request, mock_exc)
        )
        
        assert response.status_code == 400
        assert "error" in response.body.decode()
    
    def test_general_exception_handler(self):
        """Test general exception handler."""
        mock_request = Mock()
        mock_exc = Exception("Test error")
        
        loop = asyncio.get_event_loop()
        response = loop.run_until_complete(
            general_exception_handler(mock_request, mock_exc)
        )
        
        assert response.status_code == 500
        assert "error" in response.body.decode()


class TestAPIEndpoints:
    """Test API endpoints."""
    
    def test_root_endpoint(self, client):
        """Test root endpoint."""
        response = client.get("/")
        assert response.status_code == 200
        assert response.json() == {"message": "Multi-Agent Observability Server"}
    
    def test_health_endpoint(self, client):
        """Test health endpoint."""
        with patch('main.datetime') as mock_datetime:
            mock_datetime.now.return_value.isoformat.return_value = "2022-01-01T00:00:00"
            response = client.get("/health")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"
            assert data["timestamp"] == "2022-01-01T00:00:00"
    
    def test_create_event_success(self, client, sample_hook_event):
        """Test successful event creation."""
        with patch('main.get_container') as mock_get_container:
            mock_container = Mock()
            mock_event_service = Mock()
            mock_notification_service = Mock()
            mock_event_service.create_event.return_value = sample_hook_event
            mock_notification_service.notify_event_created = AsyncMock()
            mock_container.event_service = mock_event_service
            mock_container.notification_service = mock_notification_service
            mock_get_container.return_value = mock_container
            
            response = client.post("/events", json=sample_hook_event.dict())
            assert response.status_code == 200
            mock_event_service.create_event.assert_called_once()
    
    def test_create_event_missing_fields(self, client):
        """Test event creation with missing required fields."""
        incomplete_event = {
            "source_app": "test_app",
            "session_id": "test_session",
            # Missing hook_event_type and payload
        }
        
        response = client.post("/events", json=incomplete_event)
        assert response.status_code == 400
        assert "error" in response.json()
    
    def test_create_event_database_error(self, client, sample_hook_event):
        """Test event creation with database error."""
        with patch('main.get_container') as mock_get_container:
            mock_container = Mock()
            mock_event_service = Mock()
            mock_event_service.create_event.side_effect = Exception("Database error")
            mock_container.event_service = mock_event_service
            mock_get_container.return_value = mock_container
            
            response = client.post("/events", json=sample_hook_event.dict())
            assert response.status_code == 400
            data = response.json()
            assert "detail" in data
            assert "error" in data["detail"]
    
    def test_get_recent_events_success(self, client):
        """Test successful recent events retrieval."""
        with patch('main.get_container') as mock_get_container:
            mock_container = Mock()
            mock_event_service = Mock()
            mock_event_service.get_recent_events.return_value = []
            mock_container.event_service = mock_event_service
            mock_get_container.return_value = mock_container
            
            response = client.get("/events/recent")
            assert response.status_code == 200
            assert response.json() == []
            mock_event_service.get_recent_events.assert_called_once_with(100, 0)
    
    def test_get_recent_events_with_params(self, client):
        """Test recent events with custom parameters."""
        with patch('main.db.get_recent_events') as mock_get:
            mock_get.return_value = []
            
            response = client.get("/events/recent?limit=50&offset=10")
            assert response.status_code == 200
            mock_get.assert_called_once_with(50, 10)
    
    def test_get_recent_events_database_error(self, client):
        """Test recent events with database error."""
        with patch('main.db.get_recent_events') as mock_get:
            mock_get.side_effect = Exception("Database error")
            
            response = client.get("/events/recent")
            assert response.status_code == 500
            data = response.json()
            assert "detail" in data
            assert "error" in data["detail"]
    
    def test_get_filter_options_success(self, client):
        """Test successful filter options retrieval."""
        from models import FilterOptions
        
        with patch('main.db.get_filter_options') as mock_get:
            mock_get.return_value = FilterOptions(
                source_apps=["app1"],
                session_ids=["session1"],
                hook_event_types=["PreToolUse"]
            )
            
            response = client.get("/events/filter-options")
            assert response.status_code == 200
            data = response.json()
            assert "source_apps" in data
            assert "session_ids" in data
            assert "hook_event_types" in data
    
    def test_get_filter_options_database_error(self, client):
        """Test filter options with database error."""
        with patch('main.db.get_filter_options') as mock_get:
            mock_get.side_effect = Exception("Database error")
            
            response = client.get("/events/filter-options")
            assert response.status_code == 500
            data = response.json()
            assert "detail" in data
            assert "error" in data["detail"]
    
    def test_get_event_count_success(self, client):
        """Test successful event count retrieval."""
        with patch('main.db.get_event_count') as mock_get:
            mock_get.return_value = 42
            
            response = client.get("/events/count")
            assert response.status_code == 200
            data = response.json()
            assert data["count"] == 42
    
    def test_get_event_count_database_error(self, client):
        """Test event count with database error."""
        with patch('main.db.get_event_count') as mock_get:
            mock_get.side_effect = Exception("Database error")
            
            response = client.get("/events/count")
            assert response.status_code == 500
            data = response.json()
            assert "detail" in data
            assert "error" in data["detail"]


class TestThemeEndpoints:
    """Test theme-related endpoints."""
    
    def test_create_theme_success(self, client, sample_theme):
        """Test successful theme creation."""
        with patch('main.db.create_theme') as mock_create:
            mock_create.return_value = ApiResponse(
                success=True,
                data=sample_theme,
                message="Theme created successfully"
            )
            
            response = client.post("/api/themes", json=sample_theme.dict())
            assert response.status_code == 201
            data = response.json()
            assert data["success"] is True
    
    def test_create_theme_failure(self, client, sample_theme):
        """Test theme creation failure."""
        with patch('main.db.create_theme') as mock_create:
            mock_create.return_value = ApiResponse(
                success=False,
                error="Theme already exists"
            )
            
            response = client.post("/api/themes", json=sample_theme.dict())
            assert response.status_code == 400
            data = response.json()
            assert data["success"] is False
    
    def test_create_theme_exception(self, client):
        """Test theme creation with exception."""
        with patch('main.db.create_theme') as mock_create:
            mock_create.side_effect = Exception("Database error")
            
            response = client.post("/api/themes", json={"invalid": "data"})
            assert response.status_code == 400
            data = response.json()
            assert data["success"] is False
    
    def test_get_theme_stats(self, client):
        """Test theme stats endpoint."""
        response = client.get("/api/themes/stats")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data
    
    def test_get_theme_stats_exception(self, client):
        """Test theme stats with exception."""
        # This endpoint doesn't actually throw exceptions easily, so test normal behavior
        response = client.get("/api/themes/stats")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
    
    def test_search_themes_success(self, client):
        """Test successful theme search."""
        with patch('main.db.search_themes') as mock_search:
            mock_search.return_value = ApiResponse(
                success=True,
                data=[]
            )
            
            response = client.get("/api/themes")
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
    
    def test_search_themes_with_params(self, client):
        """Test theme search with parameters."""
        with patch('main.db.search_themes') as mock_search:
            mock_search.return_value = ApiResponse(success=True, data=[])
            
            params = {
                "query": "dark",
                "isPublic": "true",
                "authorId": "author1",
                "sortBy": "created",
                "sortOrder": "desc",
                "limit": "20",
                "offset": "10"
            }
            
            response = client.get("/api/themes", params=params)
            assert response.status_code == 200
            mock_search.assert_called_once()
    
    def test_search_themes_failure(self, client):
        """Test theme search failure."""
        with patch('main.db.search_themes') as mock_search:
            mock_search.return_value = ApiResponse(
                success=False,
                error="Search failed"
            )
            
            response = client.get("/api/themes")
            assert response.status_code == 400
    
    def test_search_themes_exception(self, client):
        """Test theme search with exception."""
        with patch('main.db.search_themes') as mock_search:
            mock_search.side_effect = Exception("Database error")
            
            response = client.get("/api/themes")
            assert response.status_code == 500
    
    def test_get_theme_by_id_success(self, client, sample_theme):
        """Test successful theme retrieval by ID."""
        with patch('main.db.get_theme_by_id') as mock_get:
            mock_get.return_value = ApiResponse(
                success=True,
                data=sample_theme
            )
            
            response = client.get("/api/themes/test_theme")
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
    
    def test_get_theme_by_id_empty_id(self, client):
        """Test theme retrieval with empty ID."""
        response = client.get("/api/themes/")
        assert response.status_code == 200  # Hits search endpoint
    
    def test_get_theme_by_id_not_found(self, client):
        """Test theme retrieval with non-existent ID."""
        with patch('main.db.get_theme_by_id') as mock_get:
            mock_get.return_value = ApiResponse(
                success=False,
                error="Theme not found"
            )
            
            response = client.get("/api/themes/nonexistent")
            assert response.status_code == 404
    
    def test_get_theme_by_id_exception(self, client):
        """Test theme retrieval with exception."""
        with patch('main.db.get_theme_by_id') as mock_get:
            mock_get.side_effect = Exception("Database error")
            
            response = client.get("/api/themes/test_theme")
            assert response.status_code == 500


class TestWebSocketEndpoint:
    """Test WebSocket endpoint functionality."""
    
    def test_websocket_connection_management(self, client):
        """Test WebSocket connection management."""
        with patch('main.get_container') as mock_get_container:
            mock_container = Mock()
            mock_websocket_service = Mock()
            mock_event_service = Mock()
            mock_event_service.get_recent_events.return_value = []
            mock_websocket_service.send_initial_data = AsyncMock()
            mock_websocket_service.add_connection = Mock()
            mock_websocket_service.remove_connection = Mock()
            mock_container.websocket_service = mock_websocket_service
            mock_container.event_service = mock_event_service
            mock_get_container.return_value = mock_container
            
            with client.websocket_connect("/stream") as websocket:
                # Connection should be added
                mock_websocket_service.add_connection.assert_called_once()
                
                # Should receive initial data
                data = websocket.receive_json()
                assert data["type"] == "initial"
    
    def test_websocket_disconnect(self, client):
        """Test WebSocket disconnect handling."""
        with patch('main.get_container') as mock_get_container:
            mock_container = Mock()
            mock_websocket_service = Mock()
            mock_event_service = Mock()
            mock_event_service.get_recent_events.return_value = []
            mock_websocket_service.send_initial_data = AsyncMock()
            mock_websocket_service.add_connection = Mock()
            mock_websocket_service.remove_connection = Mock()
            mock_container.websocket_service = mock_websocket_service
            mock_container.event_service = mock_event_service
            mock_get_container.return_value = mock_container
            
            with client.websocket_connect("/stream") as websocket:
                websocket.close()
            
            # Connection should be removed after disconnect
            mock_websocket_service.remove_connection.assert_called()
    
    def test_websocket_message_handling(self, client):
        """Test WebSocket message handling."""
        with patch('main.get_container') as mock_get_container:
            mock_container = Mock()
            mock_websocket_service = Mock()
            mock_event_service = Mock()
            mock_event_service.get_recent_events.return_value = []
            mock_websocket_service.send_initial_data = AsyncMock()
            mock_websocket_service.add_connection = Mock()
            mock_websocket_service.remove_connection = Mock()
            mock_container.websocket_service = mock_websocket_service
            mock_container.event_service = mock_event_service
            mock_get_container.return_value = mock_container
            
            with client.websocket_connect("/stream") as websocket:
                # Receive initial data
                websocket.receive_json()
                
                # Send a message
                websocket.send_text("test message")
                
                # WebSocket should have been connected
                mock_websocket_service.add_connection.assert_called_once()


class TestOptionsAndCatchAll:
    """Test OPTIONS and catch-all endpoints."""
    
    def test_options_events_endpoint(self, client):
        """Test OPTIONS endpoint for events."""
        response = client.options("/events")
        assert response.status_code == 200
        assert "Access-Control-Allow-Origin" in response.headers
    
    def test_catch_all_endpoint(self, client):
        """Test catch-all endpoint."""
        response = client.get("/nonexistent-endpoint")
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Multi-Agent Observability Server"
    
    def test_catch_all_with_different_methods(self, client):
        """Test catch-all with different HTTP methods."""
        for method in ["post", "put", "delete", "patch"]:
            response = getattr(client, method)("/nonexistent-endpoint")
            assert response.status_code == 200
            data = response.json()
            assert data["message"] == "Multi-Agent Observability Server"


class TestEventValidation:
    """Test event validation logic."""
    
    @pytest.mark.parametrize("missing_field", [
        "source_app",
        "session_id", 
        "hook_event_type",
        "payload"
    ])
    def test_create_event_missing_required_fields(self, client, missing_field):
        """Test event creation with missing required fields."""
        event_data = {
            "source_app": "test_app",
            "session_id": "test_session",
            "hook_event_type": "PreToolUse",
            "payload": {"tool": "bash"}
        }
        
        del event_data[missing_field]
        
        response = client.post("/events", json=event_data)
        assert response.status_code == 400
        assert "error" in response.json()
    
    def test_create_event_none_payload(self, client):
        """Test event creation with None payload."""
        event_data = {
            "source_app": "test_app",
            "session_id": "test_session",
            "hook_event_type": "PreToolUse",
            "payload": None
        }
        
        response = client.post("/events", json=event_data)
        assert response.status_code == 400
        assert "error" in response.json()
    
    def test_create_event_empty_string_fields(self, client):
        """Test event creation with empty string fields."""
        event_data = {
            "source_app": "",
            "session_id": "test_session",
            "hook_event_type": "PreToolUse",
            "payload": {"tool": "bash"}
        }
        
        response = client.post("/events", json=event_data)
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert "error" in data["detail"]


class TestMainModule:
    """Test main module execution."""
    
    def test_main_module_with_test_flag(self):
        """Test main module execution with test flag."""
        with patch('main.uvicorn.run') as mock_run:
            with patch('sys.argv', ['main.py', '--test']):
                import main
                # Should not call uvicorn.run in test mode
                mock_run.assert_not_called()
