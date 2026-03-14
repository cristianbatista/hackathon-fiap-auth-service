"""T013 — Unit tests for auth_service functions."""
import pytest
from unittest.mock import MagicMock, patch
from uuid import uuid4


def test_hash_password_produces_bcrypt_hash():
    """hash_password must return a bcrypt hash starting with $2b$."""
    from src.services.auth_service import hash_password

    result = hash_password("mysecretpassword")
    assert result.startswith("$2b$") or result.startswith("$2a$")
    assert result != "mysecretpassword"


def test_verify_password_correct():
    """verify_password must return True for matching plain+hash."""
    from src.services.auth_service import hash_password, verify_password

    plain = "correctpassword"
    hashed = hash_password(plain)
    assert verify_password(plain, hashed) is True


def test_verify_password_wrong():
    """verify_password must return False for wrong password."""
    from src.services.auth_service import hash_password, verify_password

    hashed = hash_password("correctpassword")
    assert verify_password("wrongpassword", hashed) is False


def test_create_user_raises_if_email_exists():
    """create_user raises UserAlreadyExistsError if email already taken."""
    from src.core.exceptions import UserAlreadyExistsError
    from src.services.auth_service import create_user
    from src.models.user import User

    db = MagicMock()
    existing_user = User(nome="Existing", email="taken@example.com", password_hash="h")
    db.query.return_value.filter.return_value.first.return_value = existing_user

    with pytest.raises(UserAlreadyExistsError):
        create_user(db, nome="New", email="taken@example.com", password="password123")


def test_create_user_normalizes_email_to_lowercase():
    """create_user normalizes email to lowercase before storing."""
    from src.services.auth_service import create_user

    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = None

    created_user = create_user(db, nome="User", email="USER@EXAMPLE.COM", password="pass1234")

    db.add.assert_called_once()
    added = db.add.call_args[0][0]
    assert added.email == "user@example.com"


def test_create_user_stores_hash_not_plain():
    """create_user must store a hashed password, never the plain text."""
    from src.services.auth_service import create_user

    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = None
    plain = "plainpassword"

    create_user(db, nome="User", email="u@example.com", password=plain)

    added = db.add.call_args[0][0]
    assert added.password_hash != plain
    assert added.password_hash.startswith("$2b$") or added.password_hash.startswith("$2a$")
