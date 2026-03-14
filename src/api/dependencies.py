"""T025 / T030 — get_current_user dependency."""
import uuid

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from src.core.database import get_db
from src.core.exceptions import InvalidTokenError, TokenExpiredError
from src.core.logging import get_logger
from src.models.user import User
from src.services.jwt_service import decode_access_token

logger = get_logger(__name__)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login", auto_error=False)


def get_current_user(
    request: Request,
    token: str | None = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    trace_id = getattr(request.state, "trace_id", "")

    if not token:
        logger.warning("Token absent", extra={"trace_id": trace_id, "path": request.url.path})
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        user_id: uuid.UUID = decode_access_token(token)
    except TokenExpiredError:
        logger.warning("Token expired", extra={"trace_id": trace_id})
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except InvalidTokenError:
        logger.warning("Token invalid", extra={"trace_id": trace_id})
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        logger.warning("Token valid but user not found", extra={"trace_id": trace_id, "user_id": str(user_id)})
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user
