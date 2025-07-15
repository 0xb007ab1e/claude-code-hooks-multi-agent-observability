import pytest
import requests
from config.test_config import config

@pytest.mark.rest
def test_rate_limit_events():
    """Test to ensure the API enforces rate limits."""
    # Send requests up to the limit
    for _ in range(10):  # assuming the rate limit is 10 requests
        response = requests.post(f"{config.server.base_url}/events", json={
            "source_app": "rate_limit_test",
            "session_id": "rate-limit-123",
            "hook_event_type": "PreToolUse",
            "payload": {"tool": "Test", "command": "test"}
        })
        assert response.status_code in [200, 429]  # 200 for success, 429 for rate limit exceeded

    # Verify rate limit exceeded
    response = requests.post(f"{config.server.base_url}/events", json={
        "source_app": "rate_limit_test",
        "session_id": "rate-limit-123",
        "hook_event_type": "PreToolUse",
        "payload": {"tool": "Test", "command": "test"}
    })
    assert response.status_code == 429  # Rate limit should be exceeded

