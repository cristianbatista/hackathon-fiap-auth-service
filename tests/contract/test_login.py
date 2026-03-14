"""T021 — Contract tests for POST /auth/login and GET /auth/me."""
import uuid
from unittest.mock import MagicMock

import pytest


@pytest.fixture()
def client_with_user():
    from src.main import app
    from src.core.database import get_db
    from src.models.user import User
    from src.services.auth_service import hash_password

    user_id = uuid.uuid4()
    mock_user = User(
        nome="Test User",
        email="test@example.com",
        password_hash=hash_password("correct_password"),
    )
    mock_user.id = user_id

    mock_db = MagicMock()

    def mock_get_db():
        return mock_db

    app.dependency_overrides[get_db] = mock_get_db

    from fastapi.testclient import TestClient
    with TestClient(app) as c:
        yield c, mock_db, mock_user

    app.dependency_overrides.clear()


def test_login_valid_credentials_returns_200_with_token(client_with_user):
    test_client, mock_db, mock_user = client_with_user
    mock_db.query.return_value.filter.return_value.first.return_value = mock_user

    response = test_client.post(
        "/auth/login",
        json={"email": "test@example.com", "password": "correct_password"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert "expires_in" in data


def test_login_wrong_password_returns_401(client_with_user):
    test_client, mock_db, mock_user = client_with_user
    mock_db.query.return_value.filter.return_value.first.return_value = mock_user

    response = test_client.post(
        "/auth/login",
        json={"email": "test@example.com", "password": "wrong_password"},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid credentials"


def test_login_nonexistent_email_returns_401_same_message(client_with_user):
    test_client, mock_db, _ = client_with_user
    mock_db.query.return_value.filter.return_value.first.return_value = None

    response = test_client.post(
        "/auth/login",
        json={"email": "nobody@example.com", "password": "whatever"},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid credentials"


def test_get_me_with_valid_token_returns_200(client_with_user):
    from src.services.jwt_service import create_access_token

    test_client, mock_db, mock_user = client_with_user
    # mock db.query for get_current_user
    mock_db.query.return_value.filter.return_value.first.return_value = mock_user

    token = create_access_token(mock_user.id)
    response = test_client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert "email" in data
    assert "nome" in data


def test_get_me_without_token_returns_401(client_with_user):
    test_client, _, _ = client_with_user
    response = test_client.get("/auth/me")
    assert response.status_code == 401
