"""T016 — Auth service: password hashing and user creation."""
from sqlalchemy.orm import Session

import bcrypt

from src.core.exceptions import UserAlreadyExistsError
from src.core.logging import get_logger
from src.models.user import User

logger = get_logger(__name__)


def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))


def create_user(db: Session, nome: str, email: str, password: str) -> User:
    normalized_email = email.lower()
    existing = db.query(User).filter(User.email == normalized_email).first()
    if existing:
        raise UserAlreadyExistsError(f"Email already registered: {normalized_email}")

    user = User(
        nome=nome,
        email=normalized_email,
        password_hash=hash_password(password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    logger.info("User created", extra={"email": normalized_email, "user_id": str(user.id)})
    return user


def authenticate_user(db: Session, email: str, password: str) -> User | None:
    """Returns user if credentials valid, else None."""
    normalized_email = email.lower()
    user = db.query(User).filter(User.email == normalized_email).first()
    if user is None or not verify_password(password, user.password_hash):
        return None
    return user
