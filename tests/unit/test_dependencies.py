"""T027 — Unit tests for get_current_user dependency."""
import uuid
from unittest.mock import MagicMock

import pytest


def _make_request(trace_id: str = "test-trace"):
    request = MagicMock()
    request.state.trace_id = trace_id
    request.url.path = "/auth/me"
    return request


def test_get_current_user_no_token_raises_401():
    from fastapi import HTTPException
    from src.api.dependencies import get_current_user

    db = MagicMock()
    request = _make_request()

    with pytest.raises(HTTPException) as exc_info:
        get_current_user(request=request, token=None, db=db)

    assert exc_info.value.status_code == 401


def test_get_current_user_expired_token_raises_401():
    from datetime import datetime, timedelta, timezone
    from fastapi import HTTPException
    from jose import jwt as jose_jwt
    from src.api.dependencies import get_current_user
    from src.core.config import settings
    from src.services.jwt_service import ALGORITHM

    db = MagicMock()
    request = _make_request()
    expired_token = jose_jwt.encode(
        {
            "sub": str(uuid.uuid4()),
            "exp": datetime.now(timezone.utc) - timedelta(hours=1),
        },
        settings.jwt_secret,
        algorithm=ALGORITHM,
    )

    with pytest.raises(HTTPException) as exc_info:
        get_current_user(request=request, token=expired_token, db=db)

    assert exc_info.value.status_code == 401


def test_get_current_user_invalid_signature_raises_401():
    from fastapi import HTTPException
    from src.api.dependencies import get_current_user

    db = MagicMock()
    request = _make_request()

    with pytest.raises(HTTPException) as exc_info:
        get_current_user(request=request, token="forged.token.value", db=db)

    assert exc_info.value.status_code == 401


def test_get_current_user_valid_token_returns_user():
    from src.api.dependencies import get_current_user
    from src.models.user import User
    from src.services.jwt_service import create_access_token

    user_id = uuid.uuid4()
    mock_user = MagicMock(spec=User)
    mock_user.id = user_id

    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = mock_user

    request = _make_request()
    token = create_access_token(user_id)

    result = get_current_user(request=request, token=token, db=db)
    assert result is mock_user
