"""T029 — require_owner guard helper."""

import uuid

from fastapi import HTTPException, status

from src.models.user import User


def require_owner(resource_user_id: uuid.UUID, current_user: User) -> None:
    """Raise 403 if current_user is not the owner of the resource."""
    if resource_user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: you do not own this resource",
        )
