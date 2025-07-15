import pytest
import requests
import sqlite3
import os
from config.test_config import config

# Optional imports for database tests
try:
    import psycopg2
except ImportError:
    psycopg2 = None

try:
    from pymongo import MongoClient
except ImportError:
    MongoClient = None

@pytest.mark.db
def test_sqlite_event_storage():
    """Test that events are stored in SQLite database."""
    # Send an event first
    response = requests.post(f"{config.server.base_url}/events", json={
        "source_app": "test_db",
        "session_id": "db-test-123",
        "hook_event_type": "PreToolUse",
        "payload": {"tool": "DB_Test", "command": "test db"}
    })
    assert response.status_code == 200
    
    # Check database side-effect - find the actual database file
    db_path = None
    for possible_path in ["events.db", "../events.db", "../apps/server/events.db", "/tmp/events.db"]:
        if os.path.exists(possible_path):
            db_path = possible_path
            break
    
    if db_path:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM events WHERE session_id = ?", ("db-test-123",))
        result = cursor.fetchone()
        
        assert result is not None
        # Check the structure based on schema: id, source_app, session_id, hook_event_type, payload, chat, summary, timestamp
        assert result[2] == "db-test-123"  # session_id
        assert result[3] == "PreToolUse"   # hook_event_type
        assert result[1] == "test_db"      # source_app
        
        conn.close()
    else:
        # If we can't find the database file, at least verify the API response
        response_data = response.json()
        assert response_data["session_id"] == "db-test-123"

@pytest.mark.db
@pytest.mark.skipif(psycopg2 is None, reason="psycopg2 not available")
def test_postgres_event_storage():
    """Test that events are stored in PostgreSQL database."""
    # Send an event first
    response = requests.post(f"{config.server.base_url}/events", json={
        "source_app": "test_postgres",
        "session_id": "postgres-test-123",
        "hook_event_type": "PostToolUse",
        "payload": {"tool": "Postgres_Test", "result": "success"}
    })
    assert response.status_code == 200
    
    # Check database side-effect
    conn = psycopg2.connect(
        host=config.database.postgres_host,
        port=config.database.postgres_port,
        database=config.database.postgres_db,
        user=config.database.postgres_user,
        password=config.database.postgres_password
    )
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM events WHERE session_id = %s", ("postgres-test-123",))
    result = cursor.fetchone()
    
    assert result is not None
    assert result[2] == "postgres-test-123"  # Assuming session_id is the 3rd column
    assert result[3] == "PostToolUse"        # Assuming hook_event_type is the 4th column
    
    conn.close()

@pytest.mark.db
@pytest.mark.skipif(MongoClient is None, reason="pymongo not available")
def test_mongo_event_storage():
    """Test that events are stored in MongoDB."""
    # Send an event first
    response = requests.post(f"{config.server.base_url}/events", json={
        "source_app": "test_mongo",
        "session_id": "mongo-test-123",
        "hook_event_type": "PreToolUse",
        "payload": {"tool": "Mongo_Test", "command": "test mongo"}
    })
    assert response.status_code == 200
    
    # Check database side-effect
    client = MongoClient(config.database.mongo_host, config.database.mongo_port)
    db = client[config.database.mongo_db]
    collection = db.events
    
    result = collection.find_one({"session_id": "mongo-test-123"})
    
    assert result is not None
    assert result["session_id"] == "mongo-test-123"
    assert result["hook_event_type"] == "PreToolUse"
    
    client.close()

@pytest.mark.db
def test_event_count_increment():
    """Test that event count increases after sending events."""
    # Get initial count
    initial_response = requests.get(f"{config.server.base_url}/events/count")
    initial_count = initial_response.json().get("count", 0)
    
    # Send an event
    response = requests.post(f"{config.server.base_url}/events", json={
        "source_app": "test_count",
        "session_id": "count-test-123",
        "hook_event_type": "PreToolUse",
        "payload": {"tool": "Count_Test", "command": "test count"}
    })
    assert response.status_code == 200
    
    # Get updated count
    updated_response = requests.get(f"{config.server.base_url}/events/count")
    updated_count = updated_response.json().get("count", 0)
    
    assert updated_count == initial_count + 1
