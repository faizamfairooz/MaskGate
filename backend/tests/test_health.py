import pytest
from fastapi.testclient import TestClient
from app.main import app


client = TestClient(app)


def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "MaskGate API"


def test_health_check():
    response = client.get("/api/v1/health/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


def test_database_health():
    response = client.get("/api/v1/health/database")
    assert response.status_code in [200, 503]
