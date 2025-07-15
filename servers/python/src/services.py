from typing import List, Set, Dict, Any
import json
import logging
from fastapi import WebSocket
from models import HookEvent, FilterOptions, Theme, ThemeSearchQuery, ApiResponse
from database import Database

logger = logging.getLogger(__name__)


class EventService:
    """Service for handling event-related operations"""

    def __init__(self, database: Database):
        self.database = database

    def create_event(self, event: HookEvent) -> HookEvent:
        """Create a new event with validation"""
        if not self._validate_event(event):
            raise ValueError("Missing required fields")
        return self.database.insert_event(event)

    def get_recent_events(self, limit: int = 100, offset: int = 0) -> List[HookEvent]:
        """Get recent events with pagination"""
        return self.database.get_recent_events(limit, offset)

    def get_filter_options(self) -> FilterOptions:
        """Get available filter options"""
        return self.database.get_filter_options()

    def get_event_count(self) -> int:
        """Get total event count"""
        return self.database.get_event_count()

    def _validate_event(self, event: HookEvent) -> bool:
        """Validate event has required fields"""
        return bool(
            event.source_app and
            event.session_id and
            event.hook_event_type and
            event.payload is not None
        )


class ThemeService:
    """Service for handling theme-related operations"""

    def __init__(self, database: Database):
        self.database = database

    def create_theme(self, theme: Theme) -> ApiResponse:
        """Create a new theme"""
        return self.database.create_theme(theme)

    def get_theme_by_id(self, theme_id: str) -> ApiResponse:
        """Get theme by ID"""
        if not theme_id:
            return ApiResponse(
                success=False,
                error="Theme ID is required"
            )
        return self.database.get_theme_by_id(theme_id)

    def search_themes(self, query: ThemeSearchQuery) -> ApiResponse:
        """Search themes"""
        return self.database.search_themes(query)

    def get_theme_stats(self) -> Dict[str, Any]:
        """Get theme statistics"""
        # Placeholder implementation
        return {
            "total": 0,
            "public": 0,
            "private": 0
        }


class WebSocketService:
    """Service for managing WebSocket connections and broadcasting"""

    def __init__(self):
        self.connections: Set[WebSocket] = set()

    def add_connection(self, websocket: WebSocket):
        """Add a WebSocket connection"""
        self.connections.add(websocket)

    def remove_connection(self, websocket: WebSocket):
        """Remove a WebSocket connection"""
        self.connections.discard(websocket)

    async def broadcast_message(self, message: Dict[str, Any]):
        """Broadcast message to all connected WebSocket clients"""
        if not self.connections:
            return

        # Create a copy of connections to avoid modification during iteration
        connections_copy = self.connections.copy()

        for websocket in connections_copy:
            try:
                await websocket.send_text(json.dumps(message))
            except Exception as e:
                logger.warning(f"Failed to send message to WebSocket: {e}")
                # Remove disconnected websocket
                self.connections.discard(websocket)

    async def send_initial_data(self, websocket: WebSocket, event_service: EventService):
        """Send initial data to a new WebSocket connection"""
        try:
            recent_events = event_service.get_recent_events(50, 0)
            await websocket.send_text(json.dumps({
                "type": "initial",
                "data": [event.dict() for event in recent_events]
            }))
        except Exception as e:
            logger.error(f"Failed to send initial data: {e}")
            raise


class NotificationService:
    """Service for handling event notifications"""

    def __init__(self, websocket_service: WebSocketService):
        self.websocket_service = websocket_service

    async def notify_event_created(self, event: HookEvent):
        """Notify all clients about a new event"""
        await self.websocket_service.broadcast_message({
            "type": "event",
            "data": event.dict()
        })


class ServiceContainer:
    """Container for dependency injection"""

    def __init__(self, database: Database):
        self.database = database
        self.event_service = EventService(database)
        self.theme_service = ThemeService(database)
        self.websocket_service = WebSocketService()
        self.notification_service = NotificationService(self.websocket_service)
