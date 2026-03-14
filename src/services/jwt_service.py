"""T022 — JWT service: create and decode access tokens."""
import uuid
from datetime import datetime, timedelta, timezone

from jose import ExpiredSignatureError, JWTError, jwt

from src.core.config import settings
from src.core.exceptions import InvalidTokenError, TokenExpiredError

ALGORITHM = "HS256"


def create_access_token(user_id: uuid.UUID) -> str:
    now = datetime.now(timezone.utc)
    expire = now + timedelta(seconds=settings.jwt_expiry_seconds)
    payload = {
        "sub": str(user_id),
        "iat": now,
        "exp": expire,
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=ALGORITHM)


def decode_access_token(token: str) -> uuid.UUID:
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[ALGORITHM])
    except ExpiredSignatureError:
        raise TokenExpiredError("Token has expired")
    except JWTError:
        raise InvalidTokenError("Token is invalid")

    sub = payload.get("sub")
    if sub is None:
        raise InvalidTokenError("Token missing 'sub' claim")

    try:
        return uuid.UUID(sub)
    except ValueError:
        raise InvalidTokenError("Token 'sub' is not a valid UUID")
