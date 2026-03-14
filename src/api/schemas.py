"""T017 / T023 — Pydantic schemas."""
import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, field_validator


# --- Registration ---

class RegisterRequest(BaseModel):
    nome: str = Field(..., min_length=1, max_length=255)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)


class UserResponse(BaseModel):
    id: uuid.UUID
    email: str
    nome: str
    created_at: datetime | None = None

    model_config = {"from_attributes": True}


# --- Login ---

class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=1)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
