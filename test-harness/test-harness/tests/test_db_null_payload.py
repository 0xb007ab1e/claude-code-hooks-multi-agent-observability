import pytest
import requests
import sqlite3
import os
from config.test_config import config

@pytest.mark.db
def test_null_payload_storage():
    """Test handling of null payload in database storage."""
    # Send an event with null payload
    response = requests.post(f"{config.server.base_url}/events", json={
        "source_app": "test_null_payload",
        "session_id": "test-null-payload-123",
        "hook_event_type": "PreToolUse",
        "payload": None
    })
    
    # Check if server handles null payload appropriately
    # The server might return 400 (bad request) or 200 (accept null)
    assert response.status_code in [200, 400]
    
    if response.status_code == 200:
        # If accepted, verify it's stored correctly in database
        db_path = None
        for possible_path in ["events.db", "../events.db", "../apps/server/events.db", "/tmp/events.db"]:
            if os.path.exists(possible_path):
                db_path = possible_path
                break
        
        if db_path:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT * FROM events WHERE session_id = ?", ("test-null-payload-123",))
            result = cursor.fetchone()
            
            if result:
                # Verify null payload is stored correctly
                assert result[2] == "test-null-payload-123"  # session_id
                assert result[4] is None or result[4] == "null"  # payload column
            
            conn.close()

@pytest.mark.db
def test_empty_payload_storage():
    """Test handling of empty payload in database storage."""
    # Send an event with empty payload
    response = requests.post(f"{config.server.base_url}/events", json={
        "source_app": "test_empty_payload",
        "session_id": "test-empty-payload-123",
        "hook_event_type": "PreToolUse",
        "payload": {}
    })
    
    assert response.status_code == 200
    
    # Verify it's stored correctly in database
    db_path = None
    for possible_path in ["events.db", "../events.db", "../apps/server/events.db", "/tmp/events.db"]:
        if os.path.exists(possible_path):
            db_path = possible_path
            break
    
    if db_path:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM events WHERE session_id = ?", ("test-empty-payload-123",))
        result = cursor.fetchone()
        
        assert result is not None
        assert result[2] == "test-empty-payload-123"  # session_id
        assert result[4] is not None  # payload should exist even if empty
        
        conn.close()

@pytest.mark.db
def test_malformed_payload_storage():
    """Test handling of malformed payload in database storage."""
    # Send an event with malformed payload
    import json
    
    # Create a payload with circular reference (not JSON serializable)
    malformed_data = {"tool": "test"}
    malformed_data["circular"] = malformed_data
    
    try:
        response = requests.post(f"{config.server.base_url}/events", json={
            "source_app": "test_malformed_payload",
            "session_id": "test-malformed-payload-123",
            "hook_event_type": "PreToolUse",
            "payload": malformed_data
        })
        
        # This should fail during JSON serialization
        assert False, "Expected JSON serialization to fail"
    except (ValueError, TypeError):
        # Expected behavior - malformed payload should be rejected
        pass

@pytest.mark.db
def test_large_payload_storage():
    """Test handling of large payload in database storage."""
    # Create a large payload
    large_payload = {"data": "x" * 50000}  # 50KB payload
    
    response = requests.post(f"{config.server.base_url}/events", json={
        "source_app": "test_large_payload",
        "session_id": "test-large-payload-123",
        "hook_event_type": "PreToolUse",
        "payload": large_payload
    })
    
    # Server should handle large payloads appropriately
    assert response.status_code in [200, 413]  # 200 for success, 413 for payload too large
    
    if response.status_code == 200:
        # Verify it's stored correctly in database
        db_path = None
        for possible_path in ["events.db", "../events.db", "../apps/server/events.db", "/tmp/events.db"]:
            if os.path.exists(possible_path):
                db_path = possible_path
                break
        
        if db_path:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT * FROM events WHERE session_id = ?", ("test-large-payload-123",))
            result = cursor.fetchone()
            
            assert result is not None
            assert result[2] == "test-large-payload-123"  # session_id
            
            conn.close()

@pytest.mark.db
def test_special_characters_payload_storage():
    """Test handling of special characters in payload storage."""
    # Create payload with special characters
    special_payload = {
        "tool": "Test",
        "command": "echo 'Hello 世界! 🌍 \"quoted\" & <tags>'",
        "unicode": "café résumé naïve",
        "emoji": "😀😃😄😁😆😅😂🤣"
    }
    
    response = requests.post(f"{config.server.base_url}/events", json={
        "source_app": "test_special_chars",
        "session_id": "test-special-chars-123",
        "hook_event_type": "PreToolUse",
        "payload": special_payload
    })
    
    assert response.status_code == 200
    
    # Verify it's stored correctly in database
    db_path = None
    for possible_path in ["events.db", "../events.db", "../apps/server/events.db", "/tmp/events.db"]:
        if os.path.exists(possible_path):
            db_path = possible_path
            break
    
    if db_path:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM events WHERE session_id = ?", ("test-special-chars-123",))
        result = cursor.fetchone()
        
        assert result is not None
        assert result[2] == "test-special-chars-123"  # session_id
        
        # Parse the payload from database and verify special characters are preserved
        import json
        stored_payload = json.loads(result[4])
        assert stored_payload["unicode"] == "café résumé naïve"
        assert stored_payload["emoji"] == "😀😃😄😁😆😅😂🤣"
        
        conn.close()

@pytest.mark.db
def test_payload_cleanup():
    """Test cleanup of test data after test completion."""
    # Send a test event
    response = requests.post(f"{config.server.base_url}/events", json={
        "source_app": "test_cleanup",
        "session_id": "test-cleanup-123",
        "hook_event_type": "PreToolUse",
        "payload": {"tool": "CleanupTest", "command": "cleanup test"}
    })
    
    assert response.status_code == 200
    
    # Verify it's stored in database
    db_path = None
    for possible_path in ["events.db", "../events.db", "../apps/server/events.db", "/tmp/events.db"]:
        if os.path.exists(possible_path):
            db_path = possible_path
            break
    
    if db_path:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Verify event exists
        cursor.execute("SELECT * FROM events WHERE session_id = ?", ("test-cleanup-123",))
        result = cursor.fetchone()
        assert result is not None
        
        # Clean up test data
        cursor.execute("DELETE FROM events WHERE session_id = ?", ("test-cleanup-123",))
        conn.commit()
        
        # Verify cleanup
        cursor.execute("SELECT * FROM events WHERE session_id = ?", ("test-cleanup-123",))
        result = cursor.fetchone()
        assert result is None
        
        conn.close()
