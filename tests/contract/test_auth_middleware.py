"""T028 — Contract tests for auth middleware and owner protection."""
import uuid
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def client():
    from src.main import app
    from src.core.database import get_db

    mock_db = MagicMock()
    app.dependency_overrides[get_db] = lambda: mock_db

    with TestClient(app) as c:
        yield c, mock_db

    app.dependency_overrides.clear()


def test_get_me_no_header_returns_401(client):
    test_client, _ = client
    response = test_client.get("/auth/me")
    assert response.status_code == 401


def test_get_me_forged_signature_returns_401(client):
    test_client, _ = client
    response = test_client.get(
        "/auth/me",
        headers={"Authorization": "Bearer forged.token.data"},
    )
    assert response.status_code == 401


def test_require_owner_different_user_raises_403():
    from fastapi import HTTPException
    from src.api.guard import require_owner
    from src.models.user import User

    owner_id = uuid.uuid4()
    other_id = uuid.uuid4()

    current_user = MagicMock(spec=User)
    current_user.id = other_id

    with pytest.raises(HTTPException) as exc_info:
        require_owner(resource_user_id=owner_id, current_user=current_user)

    assert exc_info.value.status_code == 403


def test_require_owner_same_user_does_not_raise():
    from src.api.guard import require_owner
    from src.models.user import User

    user_id = uuid.uuid4()
    current_user = MagicMock(spec=User)
    current_user.id = user_id

    # Should not raise
    require_owner(resource_user_id=user_id, current_user=current_user)


def test_expired_token_returns_401(client):
    from datetime import datetime, timedelta, timezone

    from jose import jwt as jose_jwt

    from src.core.config import settings
    from src.services.jwt_service import ALGORITHM

    test_client, mock_db = client
    expired_token = jose_jwt.encode(
        {
            "sub": str(uuid.uuid4()),
            "exp": datetime.now(timezone.utc) - timedelta(hours=1),
        },
        settings.jwt_secret,
        algorithm=ALGORITHM,
    )
    response = test_client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {expired_token}"},
    )
    assert response.status_code == 401
