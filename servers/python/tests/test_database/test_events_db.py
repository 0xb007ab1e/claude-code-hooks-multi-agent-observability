"""
Comprehensive tests for database event operations
"""
import pytest
from unittest.mock import patch, Mock
import sqlite3
import json
from src.database import Database
from src.models import HookEvent


@pytest.mark.database
def test_database_init_creates_tables(in_memory_db):
    """Test that database initialization creates all required tables"""
    # Check that tables exist using the database's connection
    conn = in_memory_db._get_connection()
    cursor = conn.cursor()
    
    # Check events table
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='events'")
    assert cursor.fetchone() is not None
    
    # Check themes table
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='themes'")
    assert cursor.fetchone() is not None


@pytest.mark.database
def test_database_init_creates_indexes(in_memory_db):
    """Test that database initialization creates indexes"""
    conn = in_memory_db._get_connection()
    cursor = conn.cursor()
    
    # Check that indexes exist
    cursor.execute("SELECT name FROM sqlite_master WHERE type='index'")
    indexes = {row[0] for row in cursor.fetchall()}
    
    expected_indexes = {
        'idx_events_timestamp',
        'idx_events_source_app', 
        'idx_events_session_id',
        'idx_events_hook_event_type',
        'idx_themes_name',
        'idx_themes_author',
        'idx_themes_public'
    }
    
    # Check that all expected indexes exist
    for index in expected_indexes:
        assert index in indexes


@pytest.mark.database
def test_database_init_idempotent(in_memory_db):
    """Test that database initialization is idempotent"""
    # Initialize again - should not raise errors
    in_memory_db.init_database()
    
    # Tables should still exist
    with sqlite3.connect(in_memory_db.db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = {row[0] for row in cursor.fetchall()}
        assert 'events' in tables
        assert 'themes' in tables


@pytest.mark.database
def test_insert_event_success(in_memory_db):
    """Test successful event insertion"""
    event = HookEvent(
        source_app="test_app",
        session_id="test_session",
        hook_event_type="test_event",
        payload={"key": "value"}
    )
    
    saved_event = in_memory_db.insert_event(event)
    
    # Should have generated ID
    assert saved_event.id is not None
    assert saved_event.id > 0
    
    # Should preserve all fields
    assert saved_event.source_app == event.source_app
    assert saved_event.session_id == event.session_id
    assert saved_event.hook_event_type == event.hook_event_type
    assert saved_event.payload == event.payload
    assert saved_event.timestamp is not None


@pytest.mark.database
def test_insert_event_auto_timestamp(in_memory_db):
    """Test that event insertion auto-generates timestamp"""
    event = HookEvent(
        source_app="test_app",
        session_id="test_session",
        hook_event_type="test_event",
        payload={"key": "value"}
    )
    # Don't set timestamp
    event.timestamp = None
    
    saved_event = in_memory_db.insert_event(event)
    
    # Should have auto-generated timestamp
    assert saved_event.timestamp is not None
    assert saved_event.timestamp > 0


@pytest.mark.database
def test_insert_event_preserve_timestamp(in_memory_db):
    """Test that event insertion preserves provided timestamp"""
    custom_timestamp = 1640995200000
    event = HookEvent(
        source_app="test_app",
        session_id="test_session",
        hook_event_type="test_event",
        payload={"key": "value"},
        timestamp=custom_timestamp
    )
    
    saved_event = in_memory_db.insert_event(event)
    
    # Should preserve provided timestamp
    assert saved_event.timestamp == custom_timestamp


@pytest.mark.database
def test_insert_event_with_chat_and_summary(in_memory_db):
    """Test event insertion with chat and summary"""
    event = HookEvent(
        source_app="test_app",
        session_id="test_session",
        hook_event_type="test_event",
        payload={"key": "value"},
        chat=[{"role": "user", "content": "Hello"}],
        summary="Test summary"
    )
    
    saved_event = in_memory_db.insert_event(event)
    
    # Should preserve chat and summary
    assert saved_event.chat == event.chat
    assert saved_event.summary == event.summary


@pytest.mark.database
def test_insert_event_complex_payload(in_memory_db):
    """Test event insertion with complex payload"""
    complex_payload = {
        "nested": {
            "deeply": {
                "nested": ["value1", "value2", {"key": "value"}]
            }
        },
        "array": [1, 2, 3],
        "boolean": True,
        "null": None
    }
    
    event = HookEvent(
        source_app="test_app",
        session_id="test_session",
        hook_event_type="test_event",
        payload=complex_payload
    )
    
    saved_event = in_memory_db.insert_event(event)
    
    # Should preserve complex payload structure
    assert saved_event.payload == complex_payload


@pytest.mark.database
def test_get_recent_events_empty_db(in_memory_db):
    """Test get_recent_events from empty database"""
    events = in_memory_db.get_recent_events(10, 0)
    assert events == []


@pytest.mark.database
def test_get_recent_events_ordering(in_memory_db):
    """Test that recent events are returned in timestamp DESC order"""
    # Insert events with different timestamps
    event1 = HookEvent(
        source_app="app1",
        session_id="session1",
        hook_event_type="event1",
        payload={"order": 1},
        timestamp=1640995200000
    )
    event2 = HookEvent(
        source_app="app2",
        session_id="session2",
        hook_event_type="event2",
        payload={"order": 2},
        timestamp=1640995260000  # Later timestamp
    )
    event3 = HookEvent(
        source_app="app3",
        session_id="session3",
        hook_event_type="event3",
        payload={"order": 3},
        timestamp=1640995230000  # Middle timestamp
    )
    
    in_memory_db.insert_event(event1)
    in_memory_db.insert_event(event2)
    in_memory_db.insert_event(event3)
    
    events = in_memory_db.get_recent_events(10, 0)
    
    # Should be ordered by timestamp DESC
    assert len(events) == 3
    assert events[0].timestamp == 1640995260000  # Most recent
    assert events[1].timestamp == 1640995230000  # Middle
    assert events[2].timestamp == 1640995200000  # Oldest


@pytest.mark.database
def test_get_recent_events_pagination(in_memory_db):
    """Test get_recent_events with pagination"""
    # Insert multiple events
    for i in range(10):
        event = HookEvent(
            source_app=f"app_{i}",
            session_id=f"session_{i}",
            hook_event_type=f"event_{i}",
            payload={"index": i},
            timestamp=1640995200000 + i * 1000
        )
        in_memory_db.insert_event(event)
    
    # Test pagination
    page1 = in_memory_db.get_recent_events(3, 0)
    page2 = in_memory_db.get_recent_events(3, 3)
    page3 = in_memory_db.get_recent_events(3, 6)
    
    assert len(page1) == 3
    assert len(page2) == 3
    assert len(page3) == 3
    
    # Should not overlap
    page1_ids = {event.id for event in page1}
    page2_ids = {event.id for event in page2}
    page3_ids = {event.id for event in page3}
    
    assert page1_ids.isdisjoint(page2_ids)
    assert page2_ids.isdisjoint(page3_ids)
    assert page1_ids.isdisjoint(page3_ids)


@pytest.mark.database
def test_get_recent_events_limit_zero(in_memory_db):
    """Test get_recent_events with limit 0"""
    # Insert some events
    for i in range(5):
        event = HookEvent(
            source_app=f"app_{i}",
            session_id=f"session_{i}",
            hook_event_type=f"event_{i}",
            payload={"index": i}
        )
        in_memory_db.insert_event(event)
    
    events = in_memory_db.get_recent_events(0, 0)
    assert events == []


@pytest.mark.database
def test_get_recent_events_large_offset(in_memory_db):
    """Test get_recent_events with offset larger than available events"""
    # Insert few events
    for i in range(3):
        event = HookEvent(
            source_app=f"app_{i}",
            session_id=f"session_{i}",
            hook_event_type=f"event_{i}",
            payload={"index": i}
        )
        in_memory_db.insert_event(event)
    
    events = in_memory_db.get_recent_events(10, 100)
    assert events == []


@pytest.mark.database
def test_get_filter_options_empty_db(in_memory_db):
    """Test get_filter_options from empty database"""
    options = in_memory_db.get_filter_options()
    
    assert options.source_apps == []
    assert options.session_ids == []
    assert options.hook_event_types == []


@pytest.mark.database
def test_get_filter_options_populated(in_memory_db):
    """Test get_filter_options with populated database"""
    # Insert events with different values
    events = [
        HookEvent(
            source_app="app1",
            session_id="session1",
            hook_event_type="type1",
            payload={"key": "value1"}
        ),
        HookEvent(
            source_app="app2",
            session_id="session1",  # Same session
            hook_event_type="type2",
            payload={"key": "value2"}
        ),
        HookEvent(
            source_app="app1",  # Same app
            session_id="session2",
            hook_event_type="type1",  # Same type
            payload={"key": "value3"}
        )
    ]
    
    for event in events:
        in_memory_db.insert_event(event)
    
    options = in_memory_db.get_filter_options()
    
    # Should contain unique values, sorted
    assert sorted(options.source_apps) == ["app1", "app2"]
    assert sorted(options.session_ids) == ["session1", "session2"]
    assert sorted(options.hook_event_types) == ["type1", "type2"]


@pytest.mark.database
def test_get_filter_options_duplicates(in_memory_db):
    """Test that get_filter_options returns unique values"""
    # Insert events with duplicate values
    for i in range(3):
        event = HookEvent(
            source_app="duplicate_app",
            session_id="duplicate_session",
            hook_event_type="duplicate_type",
            payload={"index": i}
        )
        in_memory_db.insert_event(event)
    
    options = in_memory_db.get_filter_options()
    
    # Should return unique values only
    assert options.source_apps == ["duplicate_app"]
    assert options.session_ids == ["duplicate_session"]
    assert options.hook_event_types == ["duplicate_type"]


@pytest.mark.database
def test_get_event_count_empty(in_memory_db):
    """Test get_event_count from empty database"""
    count = in_memory_db.get_event_count()
    assert count == 0


@pytest.mark.database
def test_get_event_count_populated(in_memory_db):
    """Test get_event_count with populated database"""
    # Insert multiple events
    for i in range(5):
        event = HookEvent(
            source_app=f"app_{i}",
            session_id=f"session_{i}",
            hook_event_type=f"event_{i}",
            payload={"index": i}
        )
        in_memory_db.insert_event(event)
    
    count = in_memory_db.get_event_count()
    assert count == 5


@pytest.mark.database
def test_get_event_count_after_insertion(in_memory_db):
    """Test that event count increases after insertions"""
    initial_count = in_memory_db.get_event_count()
    assert initial_count == 0
    
    # Insert event
    event = HookEvent(
        source_app="test_app",
        session_id="test_session",
        hook_event_type="test_event",
        payload={"key": "value"}
    )
    in_memory_db.insert_event(event)
    
    new_count = in_memory_db.get_event_count()
    assert new_count == initial_count + 1


@pytest.mark.database
@pytest.mark.error
def test_database_connection_error():
    """Test database connection error handling"""
    with patch('sqlite3.connect') as mock_connect:
        mock_connect.side_effect = sqlite3.Error("Connection failed")
        
        # Should raise the database error
        with pytest.raises(sqlite3.Error):
            Database(":memory:")


@pytest.mark.database
@pytest.mark.error
def test_insert_event_database_error(in_memory_db):
    """Test insert_event with database error"""
    event = HookEvent(
        source_app="test_app",
        session_id="test_session",
        hook_event_type="test_event",
        payload={"key": "value"}
    )
    
    with patch.object(in_memory_db, 'db_path', '/invalid/path/events.db'):
        with pytest.raises(sqlite3.Error):
            in_memory_db.insert_event(event)


@pytest.mark.database
@pytest.mark.error
def test_get_recent_events_database_error(in_memory_db):
    """Test get_recent_events with database error"""
    with patch.object(in_memory_db, 'db_path', '/invalid/path/events.db'):
        with pytest.raises(sqlite3.Error):
            in_memory_db.get_recent_events(10, 0)


@pytest.mark.database
@pytest.mark.error
def test_get_filter_options_database_error(in_memory_db):
    """Test get_filter_options with database error"""
    with patch.object(in_memory_db, 'db_path', '/invalid/path/events.db'):
        with pytest.raises(sqlite3.Error):
            in_memory_db.get_filter_options()


@pytest.mark.database
@pytest.mark.error
def test_get_event_count_database_error(in_memory_db):
    """Test get_event_count with database error"""
    with patch.object(in_memory_db, 'db_path', '/invalid/path/events.db'):
        with pytest.raises(sqlite3.Error):
            in_memory_db.get_event_count()


@pytest.mark.database
@pytest.mark.error
def test_insert_event_json_serialization_error(in_memory_db):
    """Test insert_event with JSON serialization error"""
    # Create event with non-serializable payload
    event = HookEvent(
        source_app="test_app",
        session_id="test_session",
        hook_event_type="test_event",
        payload={"func": lambda x: x}  # Non-serializable function
    )
    
    with pytest.raises(TypeError):
        in_memory_db.insert_event(event)


@pytest.mark.database
def test_database_constraint_violation(in_memory_db):
    """Test database constraint handling"""
    # Try to insert event with NULL required field via raw SQL
    with sqlite3.connect(in_memory_db.db_path) as conn:
        cursor = conn.cursor()
        
        # This should fail due to NOT NULL constraint
        with pytest.raises(sqlite3.IntegrityError):
            cursor.execute(
                "INSERT INTO events (source_app, session_id, hook_event_type, payload, timestamp) VALUES (?, ?, ?, ?, ?)",
                (None, "session", "type", "{}", 1640995200000)
            )


@pytest.mark.database
def test_database_with_unicode_data(in_memory_db):
    """Test database operations with Unicode data"""
    unicode_event = HookEvent(
        source_app="应用程序",
        session_id="会话_123",
        hook_event_type="事件类型",
        payload={
            "message": "こんにちは世界",
            "emoji": "🚀🌟💫",
            "special_chars": "áéíóú ñ ç"
        },
        summary="Résumé avec des caractères spéciaux"
    )
    
    # Should handle Unicode correctly
    saved_event = in_memory_db.insert_event(unicode_event)
    
    assert saved_event.source_app == "应用程序"
    assert saved_event.payload["message"] == "こんにちは世界"
    assert saved_event.payload["emoji"] == "🚀🌟💫"
    assert saved_event.summary == "Résumé avec des caractères spéciaux"
    
    # Should be retrievable
    events = in_memory_db.get_recent_events(10, 0)
    assert len(events) == 1
    assert events[0].source_app == "应用程序"


@pytest.mark.database
def test_database_with_large_payload(in_memory_db):
    """Test database operations with large payload"""
    large_payload = {
        "large_string": "x" * 10000,
        "large_array": list(range(1000)),
        "large_object": {f"key_{i}": f"value_{i}" for i in range(100)}
    }
    
    event = HookEvent(
        source_app="test_app",
        session_id="test_session",
        hook_event_type="test_event",
        payload=large_payload
    )
    
    # Should handle large data
    saved_event = in_memory_db.insert_event(event)
    assert saved_event.payload == large_payload
    
    # Should be retrievable
    events = in_memory_db.get_recent_events(10, 0)
    assert len(events) == 1
    assert events[0].payload == large_payload


@pytest.mark.database
def test_database_concurrent_access(in_memory_db):
    """Test database concurrent access patterns"""
    import threading
    import time
    
    results = []
    errors = []
    
    def insert_events(thread_id):
        try:
            for i in range(10):
                event = HookEvent(
                    source_app=f"app_{thread_id}",
                    session_id=f"session_{thread_id}_{i}",
                    hook_event_type=f"event_{thread_id}_{i}",
                    payload={"thread": thread_id, "index": i}
                )
                saved_event = in_memory_db.insert_event(event)
                results.append(saved_event.id)
                time.sleep(0.01)  # Small delay to simulate real usage
        except Exception as e:
            errors.append(e)
    
    # Create multiple threads
    threads = []
    for i in range(3):
        thread = threading.Thread(target=insert_events, args=(i,))
        threads.append(thread)
        thread.start()
    
    # Wait for all threads to complete
    for thread in threads:
        thread.join()
    
    # Check results
    assert len(errors) == 0, f"Errors occurred: {errors}"
    assert len(results) == 30  # 3 threads * 10 events each
    
    # All IDs should be unique
    assert len(set(results)) == len(results)
    
    # Check total count
    total_count = in_memory_db.get_event_count()
    assert total_count == 30


@pytest.mark.database
def test_database_table_schema(in_memory_db):
    """Test that database tables have correct schema"""
    with sqlite3.connect(in_memory_db.db_path) as conn:
        cursor = conn.cursor()
        
        # Check events table schema
        cursor.execute("PRAGMA table_info(events)")
        events_columns = {row[1]: row[2] for row in cursor.fetchall()}
        
        expected_events_columns = {
            'id': 'INTEGER',
            'source_app': 'TEXT',
            'session_id': 'TEXT',
            'hook_event_type': 'TEXT',
            'payload': 'TEXT',
            'chat': 'TEXT',
            'summary': 'TEXT',
            'timestamp': 'INTEGER'
        }
        
        for col_name, col_type in expected_events_columns.items():
            assert col_name in events_columns
            assert events_columns[col_name] == col_type


@pytest.mark.database
def test_database_json_deserialization(in_memory_db):
    """Test JSON deserialization in database retrieval"""
    complex_chat = [
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "Hi there!"},
        {"role": "user", "content": "How are you?"}
    ]
    
    event = HookEvent(
        source_app="test_app",
        session_id="test_session",
        hook_event_type="test_event",
        payload={"nested": {"key": "value"}},
        chat=complex_chat
    )
    
    in_memory_db.insert_event(event)
    
    # Retrieve and verify deserialization
    events = in_memory_db.get_recent_events(10, 0)
    assert len(events) == 1
    
    retrieved_event = events[0]
    assert retrieved_event.payload == {"nested": {"key": "value"}}
    assert retrieved_event.chat == complex_chat


@pytest.mark.database
def test_database_null_handling(in_memory_db):
    """Test database NULL value handling"""
    event = HookEvent(
        source_app="test_app",
        session_id="test_session",
        hook_event_type="test_event",
        payload={"key": None},  # NULL value in payload
        chat=None,
        summary=None
    )
    
    saved_event = in_memory_db.insert_event(event)
    
    # Should handle NULL values correctly
    assert saved_event.payload == {"key": None}
    assert saved_event.chat is None
    assert saved_event.summary is None
    
    # Should be retrievable
    events = in_memory_db.get_recent_events(10, 0)
    assert len(events) == 1
    assert events[0].chat is None
    assert events[0].summary is None
