import pytest
from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)

def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "FastAPI skeleton API is running!"}

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "timestamp" in data

def test_get_users_empty():
    response = client.get("/api/users")
    assert response.status_code == 200
    assert response.json() == []

def test_create_user():
    user_data = {"name": "John Doe", "email": "john@example.com"}
    response = client.post("/api/users", json=user_data)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "John Doe"
    assert data["email"] == "john@example.com"
    assert "id" in data

def test_get_user():
    # First create a user
    user_data = {"name": "Jane Doe", "email": "jane@example.com"}
    create_response = client.post("/api/users", json=user_data)
    user_id = create_response.json()["id"]
    
    # Then get the user
    response = client.get(f"/api/users/{user_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Jane Doe"
    assert data["email"] == "jane@example.com"

def test_get_nonexistent_user():
    response = client.get("/api/users/999")
    assert response.status_code == 404
    assert response.json() == {"detail": "User not found"}
