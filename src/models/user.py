"""T015 — SQLAlchemy User model."""

import uuid
from datetime import UTC, datetime

from sqlalchemy import DateTime, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    nome: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False, index=True
    )
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )

    def __init__(self, **kwargs):
        if "id" not in kwargs or kwargs.get("id") is None:
            kwargs["id"] = uuid.uuid4()
        if "email" in kwargs:
            kwargs["email"] = kwargs["email"].lower()
        if "created_at" not in kwargs or kwargs.get("created_at") is None:
            kwargs["created_at"] = datetime.now(UTC)
        super().__init__(**kwargs)
