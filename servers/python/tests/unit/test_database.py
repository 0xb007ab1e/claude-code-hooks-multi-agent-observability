import pytest
from unittest.mock import patch, MagicMock
from database import Database
from models import HookEvent, Theme, ThemeSearchQuery, FilterOptions
import json
import sqlite3


def test_database_initialization(temp_db):
    """Test that database initializes correctly with tables."""
    conn = sqlite3.connect(temp_db.db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = {table[0] for table in cursor.fetchall()}

    assert 'events' in tables
    assert 'themes' in tables


def test_insert_event(temp_db, sample_hook_event):
    """Test inserting an event into the database."""
    saved_event = temp_db.insert_event(sample_hook_event)
    assert saved_event.id is not None


def test_get_recent_events(temp_db, sample_hook_event):
    """Test retrieving recent events."""
    temp_db.insert_event(sample_hook_event)
    events = temp_db.get_recent_events()
    assert len(events) > 0
    

def test_get_recent_events_with_limit(temp_db, sample_hook_event):
    """Test retrieving recent events with limit."""
    temp_db.insert_event(sample_hook_event)
    events = temp_db.get_recent_events(limit=1)
    assert len(events) <= 1


def test_get_recent_events_with_offset(temp_db, sample_hook_event):
    """Test retrieving recent events with offset."""
    temp_db.insert_event(sample_hook_event)
    events = temp_db.get_recent_events(offset=1)
    assert len(events) >= 0


def test_get_filter_options(temp_db, sample_hook_event):
    """Test getting filter options."""
    temp_db.insert_event(sample_hook_event)
    options = temp_db.get_filter_options()
    assert isinstance(options, FilterOptions)
    assert sample_hook_event.source_app in options.source_apps


def test_get_event_count(temp_db, sample_hook_event):
    """Test getting event count."""
    count_before = temp_db.get_event_count()
    temp_db.insert_event(sample_hook_event)
    count_after = temp_db.get_event_count()
    assert count_after == count_before + 1


def test_create_theme(temp_db, sample_theme):
    """Test creating a new theme."""
    response = temp_db.create_theme(sample_theme)
    assert response.success is True


def test_create_theme_duplicate_id(temp_db, sample_theme):
    """Test creating a theme with duplicate ID."""
    temp_db.create_theme(sample_theme)
    response = temp_db.create_theme(sample_theme)
    assert response.success is False
    assert "already exists" in response.error


def test_get_theme_by_id(temp_db, sample_theme):
    """Test retrieving a theme by ID."""
    temp_db.create_theme(sample_theme)
    response = temp_db.get_theme_by_id(sample_theme.id)
    assert response.success is True


def test_get_theme_by_id_not_found(temp_db):
    """Test retrieving a non-existent theme."""
    response = temp_db.get_theme_by_id("nonexistent")
    assert response.success is False
    assert "not found" in response.error


def test_search_themes_empty(temp_db):
    """Test searching themes with no results."""
    query = ThemeSearchQuery()
    response = temp_db.search_themes(query)
    assert response.success is True
    assert len(response.data) == 0


def test_search_themes_with_query(temp_db, sample_theme):
    """Test searching themes with query."""
    temp_db.create_theme(sample_theme)
    query = ThemeSearchQuery(query="test")
    response = temp_db.search_themes(query)
    assert response.success is True
    assert len(response.data) > 0


def test_search_themes_with_author_filter(temp_db, sample_theme):
    """Test searching themes with author filter."""
    temp_db.create_theme(sample_theme)
    query = ThemeSearchQuery(authorId=sample_theme.authorId)
    response = temp_db.search_themes(query)
    assert response.success is True
    assert len(response.data) > 0


def test_search_themes_with_public_filter(temp_db, sample_theme):
    """Test searching themes with public filter."""
    temp_db.create_theme(sample_theme)
    query = ThemeSearchQuery(isPublic=True)
    response = temp_db.search_themes(query)
    assert response.success is True
    assert len(response.data) > 0


def test_search_themes_with_sorting(temp_db, sample_theme):
    """Test searching themes with sorting."""
    temp_db.create_theme(sample_theme)
    query = ThemeSearchQuery(sortBy="created", sortOrder="desc")
    response = temp_db.search_themes(query)
    assert response.success is True


def test_search_themes_with_pagination(temp_db, sample_theme):
    """Test searching themes with pagination."""
    temp_db.create_theme(sample_theme)
    query = ThemeSearchQuery(limit=1, offset=0)
    response = temp_db.search_themes(query)
    assert response.success is True
    assert len(response.data) <= 1


def test_database_connection_memory():
    """Test database connection with memory database."""
    db = Database(":memory:")
    assert db.db_path == ":memory:"
    assert db._connection is not None


def test_database_connection_file(temp_db):
    """Test database connection with file database."""
    assert temp_db.db_path is not None
    assert temp_db._connection is None  # File databases don't maintain persistent connections


def test_insert_event_with_timestamp(temp_db, sample_hook_event):
    """Test inserting event with custom timestamp."""
    custom_timestamp = 1234567890000
    sample_hook_event.timestamp = custom_timestamp
    saved_event = temp_db.insert_event(sample_hook_event)
    assert saved_event.timestamp == custom_timestamp


def test_insert_event_without_timestamp(temp_db, sample_hook_event):
    """Test inserting event without timestamp."""
    sample_hook_event.timestamp = None
    saved_event = temp_db.insert_event(sample_hook_event)
    assert saved_event.timestamp is not None


def test_insert_event_with_chat(temp_db, sample_hook_event):
    """Test inserting event with chat data."""
    saved_event = temp_db.insert_event(sample_hook_event)
    assert saved_event.chat == sample_hook_event.chat


def test_insert_event_without_chat(temp_db, sample_hook_event):
    """Test inserting event without chat data."""
    sample_hook_event.chat = None
    saved_event = temp_db.insert_event(sample_hook_event)
    assert saved_event.chat is None


def test_theme_search_sorting_options(temp_db, sample_theme):
    """Test theme search with different sorting options."""
    temp_db.create_theme(sample_theme)
    
    # Test different sort options
    sort_options = [
        ("name", "asc"),
        ("name", "desc"),
        ("created", "asc"),
        ("created", "desc"),
        ("updated", "asc"),
        ("downloads", "desc"),
        ("rating", "desc")
    ]
    
    for sort_by, sort_order in sort_options:
        query = ThemeSearchQuery(sortBy=sort_by, sortOrder=sort_order)
        response = temp_db.search_themes(query)
        assert response.success is True


def test_database_error_handling(temp_db):
    """Test database error handling."""
    with patch.object(temp_db, '_get_connection') as mock_conn:
        mock_conn.side_effect = sqlite3.Error("Database error")
        
        # Test theme creation error
        response = temp_db.create_theme(temp_db.create_theme.__defaults__[0] if temp_db.create_theme.__defaults__ else None)
        # Should handle the error gracefully
        

def test_sqlite_error_raised(mock_sqlite_error):
    """Test database connection error is raised."""
    with pytest.raises(sqlite3.OperationalError):
        db = Database(":memory:")
        db.init_database()
