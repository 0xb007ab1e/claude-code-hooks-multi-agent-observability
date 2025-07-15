"""
Comprehensive tests for HookEvent model serialization and deserialization
"""
import pytest
import time
from pydantic import ValidationError
from src.models import HookEvent


@pytest.mark.model
def test_hook_event_minimal_required_data():
    """Test creating HookEvent with minimal required data"""
    minimal_event = {
        "source_app": "app",
        "session_id": "session",
        "hook_event_type": "type",
        "payload": {}
    }
    event = HookEvent(**minimal_event)
    assert event.source_app == "app"
    assert event.session_id == "session"
    assert event.hook_event_type == "type"
    assert event.payload == {}
    assert event.chat is None
    assert event.summary is None
    assert event.id is None
    assert event.timestamp is not None


@pytest.mark.model
def test_hook_event_with_optional_fields():
    """Test creating HookEvent with all optional fields"""
    full_event = {
        "id": 123,
        "source_app": "app",
        "session_id": "session",
        "hook_event_type": "type",
        "payload": {"key": "value"},
        "chat": [{"role": "user", "content": "msg"}],
        "summary": "summary",
        "timestamp": 1640995200000
    }
    event = HookEvent(**full_event)
    assert event.id == 123
    assert event.timestamp == 1640995200000
    assert event.chat == [{"role": "user", "content": "msg"}]
    assert event.summary == "summary"


@pytest.mark.model
def test_hook_event_auto_generates_timestamp():
    """Test that HookEvent auto-generates a timestamp if not provided"""
    before_time = int(time.time() * 1000)
    event = HookEvent(
        source_app="app",
        session_id="session",
        hook_event_type="type",
        payload={}
    )
    after_time = int(time.time() * 1000)
    
    assert event.timestamp is not None
    assert before_time <= event.timestamp <= after_time


@pytest.mark.model
def test_hook_event_preserves_provided_timestamp():
    """Test that HookEvent preserves provided timestamp"""
    custom_timestamp = 1640995200000
    event = HookEvent(
        source_app="app",
        session_id="session",
        hook_event_type="type",
        payload={},
        timestamp=custom_timestamp
    )
    assert event.timestamp == custom_timestamp


@pytest.mark.model
def test_hook_event_invalid_payload_type():
    """Test creating HookEvent with invalid payload type"""
    invalid_event = {
        "source_app": "app",
        "session_id": "session",
        "hook_event_type": "type",
        "payload": "invalid"  # Should be dict
    }
    with pytest.raises(ValidationError):
        HookEvent(**invalid_event)


@pytest.mark.model
def test_hook_event_missing_required_fields():
    """Test creating HookEvent with missing required fields"""
    # Missing source_app
    with pytest.raises(ValidationError):
        HookEvent(
            session_id="session",
            hook_event_type="type",
            payload={}
        )
    
    # Missing session_id
    with pytest.raises(ValidationError):
        HookEvent(
            source_app="app",
            hook_event_type="type",
            payload={}
        )
    
    # Missing hook_event_type
    with pytest.raises(ValidationError):
        HookEvent(
            source_app="app",
            session_id="session",
            payload={}
        )
    
    # Missing payload
    with pytest.raises(ValidationError):
        HookEvent(
            source_app="app",
            session_id="session",
            hook_event_type="type"
        )


@pytest.mark.model
def test_hook_event_empty_payload():
    """Test creating HookEvent with empty payload (should be valid)"""
    event = HookEvent(
        source_app="app",
        session_id="session",
        hook_event_type="type",
        payload={}
    )
    assert event.payload == {}


@pytest.mark.model
def test_hook_event_complex_payload():
    """Test creating HookEvent with complex nested payload"""
    complex_payload = {
        "nested": {
            "deeply": {
                "nested": {
                    "value": "deep_value",
                    "array": [1, 2, 3, {"nested_in_array": True}]
                }
            }
        },
        "array": [
            {"item": 1},
            {"item": 2, "details": ["a", "b", "c"]}
        ],
        "boolean": True,
        "null_value": None,
        "number": 42.5
    }
    
    event = HookEvent(
        source_app="app",
        session_id="session",
        hook_event_type="type",
        payload=complex_payload
    )
    assert event.payload == complex_payload


@pytest.mark.model
def test_hook_event_invalid_timestamp_type():
    """Test creating HookEvent with invalid timestamp type"""
    with pytest.raises(ValidationError):
        HookEvent(
            source_app="app",
            session_id="session",
            hook_event_type="type",
            payload={},
            timestamp="invalid"
        )


@pytest.mark.model
def test_hook_event_invalid_chat_type():
    """Test creating HookEvent with invalid chat type"""
    with pytest.raises(ValidationError):
        HookEvent(
            source_app="app",
            session_id="session",
            hook_event_type="type",
            payload={},
            chat="invalid"  # Should be list
        )


@pytest.mark.model
def test_hook_event_invalid_summary_type():
    """Test creating HookEvent with invalid summary type"""
    with pytest.raises(ValidationError):
        HookEvent(
            source_app="app",
            session_id="session",
            hook_event_type="type",
            payload={},
            summary=123  # Should be string
        )


@pytest.mark.model
def test_hook_event_invalid_id_type():
    """Test creating HookEvent with invalid ID type"""
    with pytest.raises(ValidationError):
        HookEvent(
            id="invalid",  # Should be int
            source_app="app",
            session_id="session",
            hook_event_type="type",
            payload={}
        )


@pytest.mark.model
def test_hook_event_serialization():
    """Test HookEvent serialization to dict"""
    event = HookEvent(
        id=123,
        source_app="app",
        session_id="session",
        hook_event_type="type",
        payload={"key": "value"},
        chat=[{"role": "user", "content": "msg"}],
        summary="summary",
        timestamp=1640995200000
    )
    
    serialized = event.dict()
    assert serialized["id"] == 123
    assert serialized["source_app"] == "app"
    assert serialized["session_id"] == "session"
    assert serialized["hook_event_type"] == "type"
    assert serialized["payload"] == {"key": "value"}
    assert serialized["chat"] == [{"role": "user", "content": "msg"}]
    assert serialized["summary"] == "summary"
    assert serialized["timestamp"] == 1640995200000


@pytest.mark.model
def test_hook_event_deserialization():
    """Test HookEvent deserialization from dict"""
    data = {
        "id": 123,
        "source_app": "app",
        "session_id": "session",
        "hook_event_type": "type",
        "payload": {"key": "value"},
        "chat": [{"role": "user", "content": "msg"}],
        "summary": "summary",
        "timestamp": 1640995200000
    }
    
    event = HookEvent(**data)
    assert event.id == 123
    assert event.source_app == "app"
    assert event.session_id == "session"
    assert event.hook_event_type == "type"
    assert event.payload == {"key": "value"}
    assert event.chat == [{"role": "user", "content": "msg"}]
    assert event.summary == "summary"
    assert event.timestamp == 1640995200000


@pytest.mark.model
def test_hook_event_roundtrip_serialization():
    """Test HookEvent roundtrip serialization/deserialization"""
    original_event = HookEvent(
        id=123,
        source_app="app",
        session_id="session",
        hook_event_type="type",
        payload={"key": "value", "nested": {"deep": "value"}},
        chat=[{"role": "user", "content": "msg"}],
        summary="summary",
        timestamp=1640995200000
    )
    
    # Serialize to dict
    serialized = original_event.dict()
    
    # Deserialize back to object
    deserialized_event = HookEvent(**serialized)
    
    # Should be identical
    assert deserialized_event.id == original_event.id
    assert deserialized_event.source_app == original_event.source_app
    assert deserialized_event.session_id == original_event.session_id
    assert deserialized_event.hook_event_type == original_event.hook_event_type
    assert deserialized_event.payload == original_event.payload
    assert deserialized_event.chat == original_event.chat
    assert deserialized_event.summary == original_event.summary
    assert deserialized_event.timestamp == original_event.timestamp


@pytest.mark.model
def test_hook_event_with_none_optional_fields():
    """Test HookEvent with explicitly None optional fields"""
    event = HookEvent(
        source_app="app",
        session_id="session",
        hook_event_type="type",
        payload={},
        id=None,
        chat=None,
        summary=None
    )
    assert event.id is None
    assert event.chat is None
    assert event.summary is None


@pytest.mark.model
def test_hook_event_empty_strings():
    """Test HookEvent with empty strings (should be valid)"""
    event = HookEvent(
        source_app="",
        session_id="",
        hook_event_type="",
        payload={}
    )
    assert event.source_app == ""
    assert event.session_id == ""
    assert event.hook_event_type == ""


@pytest.mark.model
def test_hook_event_large_payload():
    """Test HookEvent with large payload"""
    large_payload = {
        "large_string": "x" * 10000,
        "large_array": list(range(1000)),
        "large_object": {f"key_{i}": f"value_{i}" for i in range(100)}
    }
    
    event = HookEvent(
        source_app="app",
        session_id="session",
        hook_event_type="type",
        payload=large_payload
    )
    assert event.payload == large_payload


@pytest.mark.model
def test_hook_event_unicode_content():
    """Test HookEvent with Unicode content"""
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
    
    assert unicode_event.source_app == "应用程序"
    assert unicode_event.payload["message"] == "こんにちは世界"
    assert unicode_event.payload["emoji"] == "🚀🌟💫"
    assert unicode_event.summary == "Résumé avec des caractères spéciaux"


@pytest.mark.model
def test_hook_event_json_serialization():
    """Test HookEvent JSON serialization"""
    import json
    
    event = HookEvent(
        source_app="app",
        session_id="session",
        hook_event_type="type",
        payload={"key": "value"}
    )
    
    # Should be JSON serializable
    json_str = json.dumps(event.dict())
    assert isinstance(json_str, str)
    
    # Should be JSON deserializable
    parsed = json.loads(json_str)
    assert parsed["source_app"] == "app"
    assert parsed["payload"]["key"] == "value"


@pytest.mark.model
def test_hook_event_field_validation():
    """Test HookEvent field validation"""
    # Test that required fields cannot be None
    with pytest.raises(ValidationError):
        HookEvent(
            source_app=None,
            session_id="session",
            hook_event_type="type",
            payload={}
        )
    
    with pytest.raises(ValidationError):
        HookEvent(
            source_app="app",
            session_id=None,
            hook_event_type="type",
            payload={}
        )
    
    with pytest.raises(ValidationError):
        HookEvent(
            source_app="app",
            session_id="session",
            hook_event_type=None,
            payload={}
        )
    
    with pytest.raises(ValidationError):
        HookEvent(
            source_app="app",
            session_id="session",
            hook_event_type="type",
            payload=None
        )
