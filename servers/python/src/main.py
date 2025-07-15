from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError
import logging
from datetime import datetime
from typing import List, Optional
import uvicorn
import os
import sys
from services import ServiceContainer

from models import HookEvent, FilterOptions, EventCount, HealthResponse, Theme, ThemeSearchQuery, ApiResponse
from database import Database
from config import settings, validate_required_config

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper()),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Multi-Agent Observability Server",
    description="FastAPI implementation of the multi-agent observability server",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors"""
    return JSONResponse(
        status_code=400,
        content={"error": "Invalid request", "message": "Validation failed", "details": exc.errors()}
    )


@app.exception_handler(ValidationError)
async def pydantic_validation_exception_handler(request: Request, exc: ValidationError):
    """Handle Pydantic validation errors"""
    return JSONResponse(
        status_code=400,
        content={"error": "Invalid request", "message": "Validation failed", "details": exc.errors()}
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "message": "An unexpected error occurred"}
    )


# Root endpoint
@app.get("/")
async def root():
    return {"message": "Multi-Agent Observability Server"}

# Health check endpoint


@app.get("/health", response_model=HealthResponse)
async def health_check():
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now().isoformat()
    )

# Events endpoints


@app.post("/events", response_model=HookEvent)
async def create_event(event: HookEvent):
    """Create a new event"""
    try:
        try:
            saved_event = get_container().event_service.create_event(event)
            await get_container().notification_service.notify_event_created(saved_event)
            return saved_event
        except ValueError as ve:
            raise HTTPException(status_code=400, detail={"error": str(ve)})
    except Exception as e:
        logger.error(f"Error creating event: {e}")
        raise HTTPException(
            status_code=400,
            detail={"error": "Invalid request", "message": str(e)}
        )


@app.get("/events/recent", response_model=List[HookEvent])
async def get_recent_events(limit: int = 100, offset: int = 0):
    """Get recent events with pagination support"""
    try:
        events = get_container().event_service.get_recent_events(limit, offset)
        return events
    except Exception as e:
        logger.error(f"Error getting recent events: {e}")
        raise HTTPException(
            status_code=500,
            detail={"error": "Internal server error", "message": str(e)}
        )


@app.get("/events/filter-options", response_model=FilterOptions)
async def get_filter_options():
    """Get available filter options"""
    try:
        options = get_container().event_service.get_filter_options()
        return options
    except Exception as e:
        logger.error(f"Error getting filter options: {e}")
        raise HTTPException(
            status_code=500,
            detail={"error": "Internal server error", "message": str(e)}
        )


@app.get("/events/count", response_model=EventCount)
async def get_event_count():
    """Get total event count"""
    try:
        count = get_container().event_service.get_event_count()
        return EventCount(count=count)
    except Exception as e:
        logger.error(f"Error getting event count: {e}")
        raise HTTPException(
            status_code=500,
            detail={"error": "Internal server error", "message": str(e)}
        )

# Global container - will be overridden during testing
container = None


def get_container():
    """Get the service container - allows injection for testing"""
    global container
    if container is None:
        container = ServiceContainer(Database())
    return container

# Theme endpoints


@app.post("/api/themes", response_model=ApiResponse, status_code=201)
async def create_theme(theme_data: dict):
    """Create a new theme"""
    try:
        # Convert dict to Theme object
        theme = Theme(**theme_data)
        result = get_container().theme_service.create_theme(theme)

        if result.success:
            return JSONResponse(
                status_code=201,
                content={
                    "success": result.success,
                    "id": result.data.id,
                    "message": result.message
                }
            )
        else:
            return JSONResponse(
                status_code=400,
                content=result.dict()
            )
    except Exception as e:
        logger.error(f"Error creating theme: {e}")
        return JSONResponse(
            status_code=400,
            content={
                "success": False,
                "error": "Invalid request body"
            }
        )


@app.get("/api/themes/stats")
async def get_theme_stats():
    """Get theme statistics"""
    try:
        # This is a placeholder - implement actual stats logic
        return {
            "success": True,
            "data": {
                "total": 0,
                "public": 0,
                "private": 0
            }
        }
    except Exception as e:
        logger.error(f"Error getting theme stats: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": "Internal server error"
            }
        )


@app.get("/api/themes")
async def search_themes(
    query: Optional[str] = None,
    isPublic: Optional[bool] = None,
    authorId: Optional[str] = None,
    sortBy: Optional[str] = None,
    sortOrder: Optional[str] = None,
    limit: Optional[int] = 10,
    offset: Optional[int] = 0
):
    """Search themes"""
    try:
        search_query = ThemeSearchQuery(
            query=query,
            isPublic=isPublic,
            authorId=authorId,
            sortBy=sortBy,
            sortOrder=sortOrder,
            limit=limit,
            offset=offset
        )

        result = get_container().theme_service.search_themes(search_query)

        if result.success:
            return {
                "success": result.success,
                "themes": result.data
            }
        else:
            return JSONResponse(
                status_code=400,
                content=result.dict()
            )
    except Exception as e:
        logger.error(f"Error searching themes: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": "Internal server error"
            }
        )


@app.get("/api/themes/{theme_id}")
async def get_theme(theme_id: str):
    """Get a specific theme"""
    try:
        if not theme_id:
            return JSONResponse(
                status_code=400,
                content={
                    "success": False,
                    "error": "Theme ID is required"
                }
            )

        result = get_container().theme_service.get_theme_by_id(theme_id)

        if result.success:
            return {
                "success": result.success,
                "theme": result.data
            }
        else:
            return JSONResponse(
                status_code=404,
                content=result.dict()
            )
    except Exception as e:
        logger.error(f"Error getting theme: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": "Internal server error"
            }
        )

# WebSocket endpoint for real-time events


@app.websocket("/stream")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time event streaming"""
    await websocket.accept()
    get_container().websocket_service.add_connection(websocket)
    try:
        # Send initial data
        await get_container().websocket_service.send_initial_data(websocket, get_container().event_service)

        # Keep connection alive and handle messages
        while True:
            try:
                message = await websocket.receive_text()
                logger.info(f"Received WebSocket message: {message}")
            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.error(f"WebSocket error: {e}")
                break
    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.error(f"WebSocket connection error: {e}")
    finally:
        get_container().websocket_service.remove_connection(websocket)

# Handle unsupported methods


@app.options("/events")
async def options_events():
    """Handle OPTIONS requests for events endpoint"""
    return JSONResponse(
        status_code=200,
        content={},
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET,HEAD,PUT,PATCH,POST,DELETE",
            "Access-Control-Allow-Headers": "Content-Type,Authorization"
        }
    )

# Catch-all handler for unsupported methods


@app.api_route("/{path:path}", methods=["POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS", "GET"])
async def catch_all(request: Request, path: str):
    """Catch-all handler for unsupported routes"""
    return {"message": "Multi-Agent Observability Server"}


def create_app(test_mode: bool = False):
    """Create and configure the FastAPI app"""
    if not test_mode:
        validate_required_config()

    return app


if __name__ == "__main__":
    # Check for test mode
    test_mode = "--test" in sys.argv

    # Create app
    app = create_app(test_mode=test_mode)

    # Run server
    port = int(os.getenv("PORT", settings.PORT))
    uvicorn.run(
        app,
        host=settings.HOST,
        port=port,
        log_level=settings.LOG_LEVEL.lower(),
        access_log=not test_mode
    )
