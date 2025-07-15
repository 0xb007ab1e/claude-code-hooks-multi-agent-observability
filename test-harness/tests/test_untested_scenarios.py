import pytest
import requests
import threading
import asyncio
import websockets
from config.test_config import config

@pytest.mark.rest
def test_ratelimit_429():
    """Test rate limitation and receiving 429 status."""
    url = f"{config.server.base_url}/events"
    for _ in range(20):  # Simulate requests over the limit
        response = requests.post(url, json={
            "source_app": "test_ratelimit",
            "session_id": "test-rate-123",
            "hook_event_type": "PreToolUse",
            "payload": {"tool": "RateLimit_Test"}
        })
        if response.status_code == 429:
            break
    assert response.status_code == 429

@pytest.mark.asyncio
async def test_ws_broadcast_multiple_clients():
    """Test WebSocket broadcasting to multiple clients."""
    uri = f"{config.server.ws_url}/stream"
    async def listen(uri):
        async with websockets.connect(uri) as websocket:
            # Consume initial message
            await websocket.recv()
            # Listen for broadcast
            message = await websocket.recv()
            return message
    
    tasks = [asyncio.ensure_future(listen(uri)) for _ in range(5)]  # 5 clients
    await asyncio.sleep(1)  # Wait for all clients to connect

    # Send an event that should trigger a broadcast
    requests.post(f"{config.server.base_url}/events", json={
        "source_app": "test_ws_broadcast",
        "session_id": "ws-broadcast-123",
        "hook_event_type": "ToolUse",
        "payload": {"tool": "Test"}
    })
    results = await asyncio.gather(*tasks)
    assert all("ToolUse" in res for res in results)

@pytest.mark.asyncio
async def test_graceful_shutdown_with_clients():
    """Test server's graceful shutdown process while clients are connected."""
    uri = f"{config.server.ws_url}/stream"
    async with websockets.connect(uri) as websocket:
        await websocket.recv()  # Consume initial message
        # Trigger graceful shutdown
        shutdown_response = requests.post(f"{config.server.base_url}/shutdown")
        assert shutdown_response.status_code == 200
        try:
            await websocket.recv()  # Attempt to receive post-shutdown
        except websockets.exceptions.ConnectionClosed:
            pass  # Expect connection closed due to shutdown
