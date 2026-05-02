import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database import SessionLocal, engine, Base

client = TestClient(app)

@pytest.fixture
def auth_token():
    client.post("/auth/register", json={
        "username": "roomuser",
        "email": "room@example.com",
        "password": "roompass123"
    })
    response = client.post("/auth/login", json={
        "username": "roomuser",
        "password": "roompass123"
    })
    return response.json()["access_token"]

def test_create_room(auth_token):
    response = client.post(
        "/rooms/",
        json={
            "name": "Conference Room A",
            "capacity": 10,
            "location": "Floor 1",
            "has_projector": True,
            "has_whiteboard": False
        },
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Conference Room A"
    assert data["capacity"] == 10

def test_get_rooms():
    response = client.get("/rooms/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)