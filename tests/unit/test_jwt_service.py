"""T020 — Unit tests for jwt_service."""

import uuid
from datetime import UTC, datetime, timedelta

import pytest


def test_create_token_returns_string():
    from src.services.jwt_service import create_access_token

    user_id = uuid.uuid4()
    token = create_access_token(user_id)
    assert isinstance(token, str)
    assert len(token) > 0


def test_create_token_contains_sub_claim():
    from jose import jwt as jose_jwt

    from src.core.config import settings
    from src.services.jwt_service import ALGORITHM, create_access_token

    user_id = uuid.uuid4()
    token = create_access_token(user_id)
    payload = jose_jwt.decode(token, settings.jwt_secret, algorithms=[ALGORITHM])
    assert payload["sub"] == str(user_id)


def test_create_token_contains_exp_claim():
    from jose import jwt as jose_jwt

    from src.core.config import settings
    from src.services.jwt_service import ALGORITHM, create_access_token

    user_id = uuid.uuid4()
    token = create_access_token(user_id)
    payload = jose_jwt.decode(token, settings.jwt_secret, algorithms=[ALGORITHM])
    assert "exp" in payload


def test_decode_token_returns_correct_uuid():
    from src.services.jwt_service import create_access_token, decode_access_token

    user_id = uuid.uuid4()
    token = create_access_token(user_id)
    decoded = decode_access_token(token)
    assert decoded == user_id


def test_decode_token_expired_raises_TokenExpiredError():
    from jose import jwt as jose_jwt

    from src.core.config import settings
    from src.core.exceptions import TokenExpiredError
    from src.services.jwt_service import (
        ALGORITHM,
        decode_access_token,
    )

    user_id = uuid.uuid4()
    # Create token with past expiry
    expired_payload = {
        "sub": str(user_id),
        "iat": datetime.now(UTC) - timedelta(hours=2),
        "exp": datetime.now(UTC) - timedelta(hours=1),
    }
    expired_token = jose_jwt.encode(
        expired_payload, settings.jwt_secret, algorithm=ALGORITHM
    )

    with pytest.raises(TokenExpiredError):
        decode_access_token(expired_token)


def test_decode_token_invalid_signature_raises_InvalidTokenError():
    from src.core.exceptions import InvalidTokenError
    from src.services.jwt_service import decode_access_token

    with pytest.raises(InvalidTokenError):
        decode_access_token("this.is.not.a.valid.token")


def test_decode_token_wrong_secret_raises_InvalidTokenError():
    from datetime import timedelta

    from jose import jwt as jose_jwt

    from src.core.exceptions import InvalidTokenError
    from src.services.jwt_service import ALGORITHM, decode_access_token

    user_id = uuid.uuid4()
    bad_token = jose_jwt.encode(
        {"sub": str(user_id), "exp": datetime.now(UTC) + timedelta(minutes=5)},
        "wrong_secret",
        algorithm=ALGORITHM,
    )

    with pytest.raises(InvalidTokenError):
        decode_access_token(bad_token)
