"""T018 / T024 / T026 — Auth router."""

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from src.api.dependencies import get_current_user
from src.api.schemas import LoginRequest, RegisterRequest, TokenResponse, UserResponse
from src.core.config import settings
from src.core.database import get_db
from src.core.exceptions import UserAlreadyExistsError
from src.core.logging import get_logger
from src.models.user import User
from src.services.auth_service import authenticate_user, create_user
from src.services.jwt_service import create_access_token

logger = get_logger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED
)
def register(payload: RegisterRequest, request: Request, db: Session = Depends(get_db)):
    trace_id = getattr(request.state, "trace_id", "")
    try:
        user = create_user(
            db, nome=payload.nome, email=payload.email, password=payload.password
        )
    except UserAlreadyExistsError:
        logger.warning(
            "Register failed — email already exists", extra={"trace_id": trace_id}
        )
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Email already registered"
        ) from None
    logger.info(
        "User registered",
        extra={"trace_id": trace_id, "user_id": str(user.id), "email": user.email},
    )
    return user


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, request: Request, db: Session = Depends(get_db)):
    trace_id = getattr(request.state, "trace_id", "")
    user = authenticate_user(db, email=payload.email, password=payload.password)
    if user is None:
        logger.warning(
            "Login failed — invalid credentials",
            extra={"trace_id": trace_id, "email": payload.email},
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = create_access_token(user_id=user.id)
    logger.info(
        "Login successful",
        extra={"trace_id": trace_id, "user_id": str(user.id)},
    )
    return TokenResponse(
        access_token=token,
        expires_in=settings.jwt_expiry_seconds,
    )


@router.get("/me", response_model=UserResponse)
def me(current_user: User = Depends(get_current_user)):
    return current_user
