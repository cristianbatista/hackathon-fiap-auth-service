"""T014 — Contract tests for POST /auth/register."""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch


@pytest.fixture()
def client():
    """TestClient with database dependency overridden."""
    from src.main import app
    from src.core.database import get_db

    mock_db = MagicMock()
    # No existing user by default
    mock_db.query.return_value.filter.return_value.first.return_value = None

    app.dependency_overrides[get_db] = lambda: mock_db
    with TestClient(app, raise_server_exceptions=True) as c:
        yield c, mock_db
    app.dependency_overrides.clear()


def test_register_success_returns_201(client):
    test_client, db = client
    payload = {"nome": "John Doe", "email": "john@example.com", "password": "secure123"}
    response = test_client.post("/auth/register", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert data["email"] == "john@example.com"
    assert "password" not in data
    assert "password_hash" not in data


def test_register_duplicate_email_returns_409(client):
    from src.models.user import User

    test_client, db = client
    existing = User(nome="Existing", email="dup@example.com", password_hash="h")
    db.query.return_value.filter.return_value.first.return_value = existing

    payload = {"nome": "Another", "email": "dup@example.com", "password": "secure123"}
    response = test_client.post("/auth/register", json=payload)
    assert response.status_code == 409


def test_register_short_password_returns_422(client):
    test_client, _ = client
    payload = {"nome": "User", "email": "u@example.com", "password": "short"}
    response = test_client.post("/auth/register", json=payload)
    assert response.status_code == 422


def test_register_missing_fields_returns_422(client):
    test_client, _ = client
    response = test_client.post("/auth/register", json={"email": "u@example.com"})
    assert response.status_code == 422


def test_register_invalid_email_returns_422(client):
    test_client, _ = client
    payload = {"nome": "User", "email": "not-an-email", "password": "secure123"}
    response = test_client.post("/auth/register", json=payload)
    assert response.status_code == 422
