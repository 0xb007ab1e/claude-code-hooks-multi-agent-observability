"""
Comprehensive tests for FastAPI health and catch-all routes
"""
import pytest


@pytest.mark.rest
def test_health_check(test_client):
    """Test the /health endpoint returns a healthy status"""
    response = test_client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "timestamp" in data


@pytest.mark.rest
def test_catch_all_get(test_client):
    """Test the catch-all handler with GET method"""
    response = test_client.get("/nonexistent")
    assert response.status_code == 200
    assert response.json() == {"message": "Multi-Agent Observability Server"}


@pytest.mark.rest
def test_catch_all_post(test_client):
    """Test the catch-all handler with POST method"""
    response = test_client.post("/nonexistent")
    assert response.status_code == 200
    assert response.json() == {"message": "Multi-Agent Observability Server"}


@pytest.mark.rest
def test_catch_all_unexpected_method(test_client):
    """Test the catch-all handler with an unexpected method"""
    response = test_client.delete("/nonexistent")
    assert response.status_code == 200
    assert response.json() == {"message": "Multi-Agent Observability Server"}


@pytest.mark.rest
def test_health_endpoint_format(test_client):
    """Ensure JSON response has correct format at /health"""
    response = test_client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, dict)
    assert "status" in data
    assert data["status"] == "healthy"
    assert "timestamp" in data


@pytest.mark.rest
@pytest.mark.error
def test_health_endpoint_with_server_error():
    """Simulate a server error for /health endpoint"""
    with patch('src.main.health_check') as mock_check:
        mock_check.side_effect = Exception("Intentional Error")
        response = test_client.get("/health")
        assert response.status_code == 500
        data = response.json()
        assert "error" in data
        assert data["error"] == "Internal server error"


@pytest.mark.rest
def test_health_check_ssl(test_client):
    """Test the /health endpoint over HTTPS"""
    response = test_client.get(f"https://{test_client.base_url}/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


@pytest.mark.rest
def test_catch_all_with_path_parameters(test_client):
    """Test catch-all handler with path parameters at /unknown/path"""
    response = test_client.get("/unknown/path")
    assert response.status_code == 200
    assert response.json() == {"message": "Multi-Agent Observability Server"}

