"""Utility functions for better testability"""

from typing import Dict, Any, Optional
from datetime import datetime
import json
import logging

logger = logging.getLogger(__name__)


def create_error_response(error_type: str, message: str, status_code: int = 400) -> Dict[str, Any]:
    """Create standardized error response"""
    return {
        "error": error_type,
        "message": message,
        "timestamp": datetime.now().isoformat(),
        "status_code": status_code
    }


def create_success_response(data: Any, message: Optional[str] = None) -> Dict[str, Any]:
    """Create standardized success response"""
    response = {
        "success": True,
        "data": data,
        "timestamp": datetime.now().isoformat()
    }
    if message:
        response["message"] = message
    return response


def safe_json_dumps(obj: Any) -> str:
    """Safely convert object to JSON string"""
    try:
        return json.dumps(obj)
    except (TypeError, ValueError) as e:
        logger.error(f"JSON serialization error: {e}")
        return json.dumps({"error": "Serialization failed"})


def validate_pagination_params(limit: int, offset: int) -> tuple[int, int]:
    """Validate and normalize pagination parameters"""
    # Ensure limit is within reasonable bounds
    limit = max(1, min(limit, 1000))
    # Ensure offset is non-negative
    offset = max(0, offset)
    return limit, offset


def extract_websocket_message_data(message: str) -> Dict[str, Any]:
    """Extract data from WebSocket message safely"""
    try:
        return json.loads(message)
    except (json.JSONDecodeError, TypeError) as e:
        logger.warning(f"Invalid WebSocket message format: {e}")
        return {"error": "Invalid message format"}


def log_operation_metrics(operation: str, duration_ms: float, success: bool):
    """Log operation metrics for monitoring"""
    status = "success" if success else "failure"
    logger.info(f"Operation: {operation}, Duration: {duration_ms:.2f}ms, Status: {status}")
