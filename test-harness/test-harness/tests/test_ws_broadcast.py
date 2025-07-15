import pytest
import asyncio
import websockets
import json
import threading
import time
from config.test_config import config

@pytest.mark.websocket
@pytest.mark.asyncio
async def test_websocket_broadcast_to_multiple_clients():
    """Test WebSocket broadcasting to multiple clients."""
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
    
    # Wait for all clients to connect
    await asyncio.sleep(1)
    
    # Send a broadcast event
    import requests
    requests.post(f"{config.server.base_url}/events", json={
        "source_app": "broadcast_test",
        "session_id": "broadcast-test-123",
        "hook_event_type": "PreToolUse",
        "payload": {"tool": "BroadcastTest", "command": "broadcast test"}
    })
    
    # Verify all clients receive the broadcast
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    successful_results = [r for r in results if not isinstance(r, Exception)]
    assert len(successful_results) == num_clients
    
    for client_id, response_data in successful_results:
        assert response_data.get("type") == "event"
        assert response_data.get("data").get("source_app") == "broadcast_test"
        assert response_data.get("data").get("session_id") == "broadcast-test-123"

@pytest.mark.websocket
@pytest.mark.asyncio
async def test_websocket_broadcast_order():
    """Test WebSocket broadcasting maintains message order."""
    uri = f"{config.server.ws_url}/stream"
    
    async with websockets.connect(uri) as websocket:
        # Consume initial message
        await websocket.recv()
        
        # Send multiple events in rapid succession
        import requests
        for i in range(5):
            requests.post(f"{config.server.base_url}/events", json={
                "source_app": "order_test",
                "session_id": f"order-test-{i}",
                "hook_event_type": "PreToolUse",
                "payload": {"tool": "OrderTest", "command": f"order test {i}"}
            })
        
        # Collect all messages
        messages = []
        for _ in range(5):
            response = await asyncio.wait_for(websocket.recv(), timeout=10)
            response_data = json.loads(response)
            messages.append(response_data)
        
        # Verify messages are in order
        for i, message in enumerate(messages):
            assert message.get("data").get("session_id") == f"order-test-{i}"

@pytest.mark.websocket
@pytest.mark.asyncio
async def test_websocket_broadcast_filtering():
    """Test WebSocket broadcast filtering based on event type."""
    uri = f"{config.server.ws_url}/stream"
    
    async with websockets.connect(uri) as websocket:
        # Consume initial message
        await websocket.recv()
        
        # Send events with different types
        import requests
        requests.post(f"{config.server.base_url}/events", json={
            "source_app": "filter_test",
            "session_id": "filter-test-pre",
            "hook_event_type": "PreToolUse",
            "payload": {"tool": "FilterTest", "command": "pre tool use"}
        })
        
        requests.post(f"{config.server.base_url}/events", json={
            "source_app": "filter_test",
            "session_id": "filter-test-post",
            "hook_event_type": "PostToolUse",
            "payload": {"tool": "FilterTest", "result": "post tool use"}
        })
        
        # Collect messages
        messages = []
        for _ in range(2):
            response = await asyncio.wait_for(websocket.recv(), timeout=10)
            response_data = json.loads(response)
            messages.append(response_data)
        
        # Verify both messages received
        assert len(messages) == 2
        session_ids = [msg.get("data").get("session_id") for msg in messages]
        assert "filter-test-pre" in session_ids
        assert "filter-test-post" in session_ids

@pytest.mark.websocket
@pytest.mark.asyncio
async def test_websocket_broadcast_cleanup():
    """Test WebSocket broadcast cleanup after test completion."""
    uri = f"{config.server.ws_url}/stream"
    
    # Create and close connection
    async with websockets.connect(uri) as websocket:
        # Consume initial message
        await websocket.recv()
        
        # Send a test event
        import requests
        requests.post(f"{config.server.base_url}/events", json={
            "source_app": "cleanup_test",
            "session_id": "cleanup-test-123",
            "hook_event_type": "PreToolUse",
            "payload": {"tool": "CleanupTest", "command": "cleanup test"}
        })
        
        # Receive the event
        response = await asyncio.wait_for(websocket.recv(), timeout=10)
        response_data = json.loads(response)
        
        assert response_data.get("type") == "event"
        assert response_data.get("data").get("source_app") == "cleanup_test"
        
        # Connection should close cleanly
        await websocket.close()
        assert websocket.closed
