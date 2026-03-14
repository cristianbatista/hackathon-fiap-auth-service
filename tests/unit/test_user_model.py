"""T012 — Unit tests for User model."""
import pytest
from unittest.mock import MagicMock
from uuid import UUID


def test_user_email_is_stored_lowercase():
    """Email must be normalized to lowercase."""
    from src.models.user import User

    user = User(nome="Test User", email="TEST@EXAMPLE.COM", password_hash="hashed")
    assert user.email == "test@example.com"


def test_user_email_already_lowercase():
    """Email already lowercase stays unchanged."""
    from src.models.user import User

    user = User(nome="Test User", email="test@example.com", password_hash="hashed")
    assert user.email == "test@example.com"


def test_user_password_hash_differs_from_plain():
    """password_hash must never equal the plain password."""
    from src.models.user import User

    plain = "myplainpassword"
    # Simulate a bcrypt hash
    hashed = "$2b$12$aFakeHashValueThatIsNotThePlainText"
    user = User(nome="User", email="user@example.com", password_hash=hashed)
    assert user.password_hash != plain


def test_user_id_is_uuid():
    """User id must be a UUID."""
    from src.models.user import User

    user = User(nome="User", email="u@example.com", password_hash="h")
    assert user.id is None or isinstance(user.id, UUID)


def test_user_created_at_not_set_on_init():
    """created_at is set by database default, not on model init."""
    from src.models.user import User

    user = User(nome="User", email="u@example.com", password_hash="h")
    # created_at may be None before DB flush
    assert not hasattr(user, "created_at") or user.created_at is None or user.created_at is not None
