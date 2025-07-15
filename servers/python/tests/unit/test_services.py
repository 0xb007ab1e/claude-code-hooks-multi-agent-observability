import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from fastapi import WebSocket

from services import EventService, ThemeService, WebSocketService, NotificationService, ServiceContainer
from database import Database
from models import HookEvent, Theme, ThemeColors, ThemeSearchQuery, ApiResponse


class TestEventService:
    """Test EventService functionality."""
    
    def test_create_event_success(self, mock_db, sample_hook_event):
        """Test successful event creation."""
        mock_db.insert_event.return_value = sample_hook_event
        service = EventService(mock_db)
        
        result = service.create_event(sample_hook_event)
        
        assert result == sample_hook_event
        mock_db.insert_event.assert_called_once_with(sample_hook_event)
    
    def test_create_event_validation_failure(self, mock_db):
        """Test event creation validation failure."""
        service = EventService(mock_db)
        invalid_event = HookEvent(
            source_app="",  # Empty source_app should fail validation
            session_id="test",
            hook_event_type="test",
            payload={"test": "data"}
        )
        
        with pytest.raises(ValueError, match="Missing required fields"):
            service.create_event(invalid_event)
    
    def test_get_recent_events(self, mock_db, sample_hook_event):
        """Test getting recent events."""
        mock_db.get_recent_events.return_value = [sample_hook_event]
        service = EventService(mock_db)
        
        result = service.get_recent_events(50, 10)
        
        assert result == [sample_hook_event]
        mock_db.get_recent_events.assert_called_once_with(50, 10)
    
    def test_get_filter_options(self, mock_db):
        """Test getting filter options."""
        from models import FilterOptions
        expected_options = FilterOptions(
            source_apps=["app1"],
            session_ids=["session1"],
            hook_event_types=["PreToolUse"]
        )
        mock_db.get_filter_options.return_value = expected_options
        service = EventService(mock_db)
        
        result = service.get_filter_options()
        
        assert result == expected_options
        mock_db.get_filter_options.assert_called_once()
    
    def test_get_event_count(self, mock_db):
        """Test getting event count."""
        mock_db.get_event_count.return_value = 42
        service = EventService(mock_db)
        
        result = service.get_event_count()
        
        assert result == 42
        mock_db.get_event_count.assert_called_once()
    
    def test_validate_event_valid(self, mock_db, sample_hook_event):
        """Test event validation with valid event."""
        service = EventService(mock_db)
        
        result = service._validate_event(sample_hook_event)
        
        assert result is True
    
    def test_validate_event_invalid(self, mock_db):
        """Test event validation with invalid event."""
        service = EventService(mock_db)
        invalid_event = HookEvent(
            source_app="",
            session_id="test",
            hook_event_type="test",
            payload={"test": "data"}
        )
        
        result = service._validate_event(invalid_event)
        
        assert result is False


class TestThemeService:
    """Test ThemeService functionality."""
    
    def test_create_theme(self, mock_db, sample_theme):
        """Test theme creation."""
        expected_response = ApiResponse(success=True, data=sample_theme)
        mock_db.create_theme.return_value = expected_response
        service = ThemeService(mock_db)
        
        result = service.create_theme(sample_theme)
        
        assert result == expected_response
        mock_db.create_theme.assert_called_once_with(sample_theme)
    
    def test_get_theme_by_id_success(self, mock_db, sample_theme):
        """Test successful theme retrieval by ID."""
        expected_response = ApiResponse(success=True, data=sample_theme)
        mock_db.get_theme_by_id.return_value = expected_response
        service = ThemeService(mock_db)
        
        result = service.get_theme_by_id("test_theme")
        
        assert result == expected_response
        mock_db.get_theme_by_id.assert_called_once_with("test_theme")
    
    def test_get_theme_by_id_empty_id(self, mock_db):
        """Test theme retrieval with empty ID."""
        service = ThemeService(mock_db)
        
        result = service.get_theme_by_id("")
        
        assert result.success is False
        assert result.error == "Theme ID is required"
        mock_db.get_theme_by_id.assert_not_called()
    
    def test_search_themes(self, mock_db):
        """Test theme search."""
        query = ThemeSearchQuery(query="test", limit=10)
        expected_response = ApiResponse(success=True, data=[])
        mock_db.search_themes.return_value = expected_response
        service = ThemeService(mock_db)
        
        result = service.search_themes(query)
        
        assert result == expected_response
        mock_db.search_themes.assert_called_once_with(query)
    
    def test_get_theme_stats(self, mock_db):
        """Test theme statistics retrieval."""
        service = ThemeService(mock_db)
        
        result = service.get_theme_stats()
        
        assert result == {"total": 0, "public": 0, "private": 0}


class TestWebSocketService:
    """Test WebSocketService functionality."""
    
    def test_add_connection(self, mock_websocket):
        """Test adding WebSocket connection."""
        service = WebSocketService()
        
        service.add_connection(mock_websocket)
        
        assert mock_websocket in service.connections
    
    def test_remove_connection(self, mock_websocket):
        """Test removing WebSocket connection."""
        service = WebSocketService()
        service.add_connection(mock_websocket)
        
        service.remove_connection(mock_websocket)
        
        assert mock_websocket not in service.connections
    
    def test_broadcast_message_empty_connections(self):
        """Test broadcasting with no connections."""
        service = WebSocketService()
        
        # Should not raise error
        loop = asyncio.get_event_loop()
        loop.run_until_complete(service.broadcast_message({"test": "data"}))
    
    def test_broadcast_message_with_connections(self, mock_websocket):
        """Test broadcasting with active connections."""
        service = WebSocketService()
        service.add_connection(mock_websocket)
        mock_websocket.send_text = AsyncMock()
        
        message = {"type": "test", "data": "test_data"}
        
        loop = asyncio.get_event_loop()
        loop.run_until_complete(service.broadcast_message(message))
        
        mock_websocket.send_text.assert_called_once_with('{"type": "test", "data": "test_data"}')
    
    def test_broadcast_message_with_failed_connection(self, mock_websocket):
        """Test broadcasting removes failed connections."""
        service = WebSocketService()
        service.add_connection(mock_websocket)
        mock_websocket.send_text = AsyncMock(side_effect=Exception("Connection failed"))
        
        message = {"type": "test", "data": "test_data"}
        
        loop = asyncio.get_event_loop()
        loop.run_until_complete(service.broadcast_message(message))
        
        # Connection should be removed
        assert mock_websocket not in service.connections
    
    def test_send_initial_data_success(self, mock_websocket, sample_hook_event):
        """Test sending initial data successfully."""
        service = WebSocketService()
        mock_event_service = Mock()
        mock_event_service.get_recent_events.return_value = [sample_hook_event]
        mock_websocket.send_text = AsyncMock()
        
        loop = asyncio.get_event_loop()
        loop.run_until_complete(service.send_initial_data(mock_websocket, mock_event_service))
        
        mock_event_service.get_recent_events.assert_called_once_with(50, 0)
        mock_websocket.send_text.assert_called_once()
    
    def test_send_initial_data_failure(self, mock_websocket):
        """Test sending initial data with failure."""
        service = WebSocketService()
        mock_event_service = Mock()
        mock_event_service.get_recent_events.side_effect = Exception("Database error")
        
        loop = asyncio.get_event_loop()
        
        with pytest.raises(Exception, match="Database error"):
            loop.run_until_complete(service.send_initial_data(mock_websocket, mock_event_service))


class TestNotificationService:
    """Test NotificationService functionality."""
    
    def test_notify_event_created(self, sample_hook_event):
        """Test event creation notification."""
        mock_websocket_service = Mock()
        mock_websocket_service.broadcast_message = AsyncMock()
        service = NotificationService(mock_websocket_service)
        
        loop = asyncio.get_event_loop()
        loop.run_until_complete(service.notify_event_created(sample_hook_event))
        
        expected_message = {
            "type": "event",
            "data": sample_hook_event.dict()
        }
        mock_websocket_service.broadcast_message.assert_called_once_with(expected_message)


class TestServiceContainer:
    """Test ServiceContainer functionality."""
    
    def test_container_initialization(self, mock_db):
        """Test service container initialization."""
        container = ServiceContainer(mock_db)
        
        assert container.database == mock_db
        assert isinstance(container.event_service, EventService)
        assert isinstance(container.theme_service, ThemeService)
        assert isinstance(container.websocket_service, WebSocketService)
        assert isinstance(container.notification_service, NotificationService)
        assert container.event_service.database == mock_db
        assert container.theme_service.database == mock_db
        assert container.notification_service.websocket_service == container.websocket_service
