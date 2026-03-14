"""Additional coverage tests for health endpoint, database, exceptions, and logging."""
import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient


def test_health_endpoint_returns_ok():
    from src.main import app
    with TestClient(app) as client:
        response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "auth-service"}


def test_get_db_yields_and_closes():
    """get_db generator yields a session and closes it."""
    from unittest.mock import MagicMock, patch
    from src.core import database as db_module

    mock_session = MagicMock()
    with patch.object(db_module, "SessionLocal", return_value=mock_session):
        gen = db_module.get_db()
        session = next(gen)
        assert session is mock_session
        try:
            next(gen)
        except StopIteration:
            pass
        mock_session.close.assert_called_once()


def test_get_db_closes_on_exception():
    """get_db closes session even when an exception occurs."""
    from unittest.mock import MagicMock, patch
    from src.core import database as db_module

    mock_session = MagicMock()
    with patch.object(db_module, "SessionLocal", return_value=mock_session):
        gen = db_module.get_db()
        next(gen)
        gen.close()
        mock_session.close.assert_called_once()


def test_unhandled_exception_returns_500():
    """Unhandled exception handler returns 500."""
    from src.main import app
    from src.api.auth_router import router

    # Inject a route that raises a generic exception
    @app.get("/test-crash-unique-path")
    def crash():
        raise RuntimeError("boom")

    with TestClient(app, raise_server_exceptions=False) as client:
        response = client.get("/test-crash-unique-path")
    assert response.status_code == 500

    # Cleanup the route
    app.routes.pop()


def test_jwt_decode_missing_sub_raises():
    from src.core.exceptions import InvalidTokenError
    from src.services.jwt_service import decode_access_token
    from src.core.config import settings
    from src.services.jwt_service import ALGORITHM
    from jose import jwt as jose_jwt
    from datetime import datetime, timedelta, timezone

    token_no_sub = jose_jwt.encode(
        {"exp": datetime.now(timezone.utc) + timedelta(minutes=5)},
        settings.jwt_secret,
        algorithm=ALGORITHM,
    )
    with pytest.raises(InvalidTokenError):
        decode_access_token(token_no_sub)


def test_jwt_decode_invalid_uuid_sub_raises():
    from src.core.exceptions import InvalidTokenError
    from src.services.jwt_service import decode_access_token
    from src.core.config import settings
    from src.services.jwt_service import ALGORITHM
    from jose import jwt as jose_jwt
    from datetime import datetime, timedelta, timezone

    token_bad_uuid = jose_jwt.encode(
        {"sub": "not-a-uuid", "exp": datetime.now(timezone.utc) + timedelta(minutes=5)},
        settings.jwt_secret,
        algorithm=ALGORITHM,
    )
    with pytest.raises(InvalidTokenError):
        decode_access_token(token_bad_uuid)


def test_get_current_user_user_not_found_returns_401():
    from fastapi import HTTPException
    from src.api.dependencies import get_current_user
    from src.services.jwt_service import create_access_token
    import uuid

    user_id = uuid.uuid4()
    token = create_access_token(user_id)

    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = None

    request = MagicMock()
    request.state.trace_id = "trace"
    request.url.path = "/auth/me"

    with pytest.raises(HTTPException) as exc_info:
        get_current_user(request=request, token=token, db=db)
    assert exc_info.value.status_code == 401


def test_get_logger_reuses_existing_handler():
    from src.core.logging import get_logger
    logger = get_logger("test.duplicate")
    logger2 = get_logger("test.duplicate")
    assert logger is logger2
