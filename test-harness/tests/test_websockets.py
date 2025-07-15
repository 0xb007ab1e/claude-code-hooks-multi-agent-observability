import pytest
import asyncio
import websockets
import json
from config.test_config import config

@pytest.mark.websocket
@pytest.mark.asyncio
async def test_websocket_connection():
    """Test WebSocket connection establishment."""
    uri = f"{config.server.ws_url}/stream"
    async with websockets.connect(uri) as websocket:
        # Server sends initial events on connection
        response = await websocket.recv()
        response_data = json.loads(response)
        
        # Should receive initial events
        assert response_data.get("type") == "initial"
        assert "data" in response_data
        assert isinstance(response_data["data"], list)

@pytest.mark.websocket
@pytest.mark.asyncio
async def test_websocket_receives_events():
    """Test that WebSocket receives events when they are sent via REST API."""
    uri = f"{config.server.ws_url}/stream"
    async with websockets.connect(uri) as websocket:
        # Consume initial message
        await websocket.recv()
        
        # Send an event via REST API in the background
        import requests
        import threading
        
        def send_event():
            requests.post(f"{config.server.base_url}/events", json={
                "source_app": "websocket_test",
                "session_id": "ws-test-123",
                "hook_event_type": "PreToolUse",
                "payload": {"tool": "Test", "command": "test"}
            })
        
        # Start sending event in background
        thread = threading.Thread(target=send_event)
        thread.start()
        
        # Should receive the event via WebSocket
        response = await asyncio.wait_for(websocket.recv(), timeout=5)
        response_data = json.loads(response)
        
        assert response_data.get("type") == "event"
        assert response_data.get("data").get("source_app") == "websocket_test"
        assert response_data.get("data").get("session_id") == "ws-test-123"
        
        thread.join()

@pytest.mark.websocket
@pytest.mark.asyncio
async def test_websocket_multiple_clients_broadcast():
    """Test WebSocket broadcasting to multiple clients simultaneously."""
    uri = f"{config.server.ws_url}/stream"
    
    async def client_listener(client_id):
        async with websockets.connect(uri) as websocket:
            # Consume initial message
            await websocket.recv()
            
            # Wait for broadcast event
            response = await asyncio.wait_for(websocket.recv(), timeout=10)
            response_data = json.loads(response)
            
            return client_id, response_data
    
    # Start multiple clients
    num_clients = 3
    tasks = [asyncio.create_task(client_listener(i)) for i in range(num_clients)]
    
    # Wait a bit for all clients to connect
    await asyncio.sleep(1)
    
    # Send an event that should be broadcast to all clients
    import requests
    requests.post(f"{config.server.base_url}/events", json={
        "source_app": "multi_client_test",
        "session_id": "multi-client-123",
        "hook_event_type": "PreToolUse",
        "payload": {"tool": "MultiClientTest", "command": "broadcast test"}
    })
    
    # Wait for all clients to receive the broadcast
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # All clients should receive the same event
    successful_results = [r for r in results if not isinstance(r, Exception)]
    assert len(successful_results) == num_clients
    
    for client_id, response_data in successful_results:
        assert response_data.get("type") == "event"
        assert response_data.get("data").get("source_app") == "multi_client_test"
        assert response_data.get("data").get("session_id") == "multi-client-123"

@pytest.mark.websocket
@pytest.mark.asyncio
async def test_websocket_client_disconnect():
    """Test WebSocket client disconnection handling."""
    uri = f"{config.server.ws_url}/stream"
    
    async with websockets.connect(uri) as websocket:
        # Consume initial message
        await websocket.recv()
        
        # Send a message and expect response
        import requests
        requests.post(f"{config.server.base_url}/events", json={
            "source_app": "disconnect_test",
            "session_id": "disconnect-123",
            "hook_event_type": "PreToolUse",
            "payload": {"tool": "DisconnectTest"}
        })
        
        # Receive the event
        response = await asyncio.wait_for(websocket.recv(), timeout=5)
        response_data = json.loads(response)
        assert response_data.get("type") == "event"
        
        # Close connection explicitly
        await websocket.close()
        
        # Connection should be closed
        assert websocket.closed

@pytest.mark.websocket
@pytest.mark.asyncio
async def test_websocket_connection_timeout():
    """Test WebSocket connection timeout handling."""
    uri = f"{config.server.ws_url}/stream"
    
    try:
        async with websockets.connect(uri, timeout=1) as websocket:
            # Consume initial message
            await websocket.recv()
            
            # Keep connection alive for a while
            await asyncio.sleep(2)
            
            # Should still be connected
            assert not websocket.closed
            
    except asyncio.TimeoutError:
        # Connection timeout is acceptable
        pass
