"""Authentication routes for Virasat.

Handles user registration, login, and role-based access.

Routes:
  POST /auth/register    - Register a new user
  POST /auth/login       - Login and receive access token
  GET  /auth/me          - Get current user info
  POST /auth/refresh     - Refresh access token
"""

from fastapi import APIRouter, Body, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from db.base import get_db
from db.models import User
from core.security import hash_password, create_access_token, authenticate_user, require_user


# Request models
class RegisterSchema(BaseModel):
    email: str = Field(min_length=5, max_length=254, pattern=r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
    password: str = Field(min_length=8, max_length=72)
    role: str = "visitor"


class LoginSchema(BaseModel):
    email: str = Field(min_length=1)
    password: str = Field(min_length=1)


router = APIRouter(tags=["auth"])


@router.post("/register", status_code=status.HTTP_201_CREATED, tags=["auth"])
async def register(
    schema: RegisterSchema = Body(...),
    db: Session = Depends(get_db),
) -> dict:
    """Register a new user.

    Roles allowed: visitor, contributor.
    Moderator role can only be assigned by existing moderators.
    Public registration must never grant administrative or moderator privileges.
    """
    # Check if user already exists
    existing = db.query(User).filter(User.email == schema.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )

    # Hash password and create user
    password_hash = hash_password(schema.password)

    # Restrict role assignment during public registration
    allowed_roles_for_public = {"visitor", "contributor"}
    if schema.role not in allowed_roles_for_public:
        role = "visitor"
    else:
        role = schema.role

    user = User(
        email=schema.email,
        password_hash=password_hash,
        role=role,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    # Create access token
    access_token = create_access_token(sub=user.email, role=user.role)

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {"id": user.id, "email": user.email, "role": user.role},
    }


@router.post("/login", tags=["auth"])
async def login(
    schema: LoginSchema = Body(...),
    db: Session = Depends(get_db),
) -> dict:
    """Login and receive access token.

    Validates email and password against the database.
    Returns JWT token on success.
    """
    user = authenticate_user(schema.email, schema.password, db)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(sub=user["email"], role=user["role"])

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {"id": user["id"], "email": user["email"], "role": user["role"]},
    }


@router.get("/me", tags=["auth"])
async def me(current_user: dict = Depends(require_user)) -> dict:
    """Get current user info.

    Uses JWT-based authentication with database-backed user retrieval.
    """
    return current_user


@router.post("/refresh", tags=["auth"])
async def refresh_token(current_user: dict = Depends(require_user)) -> dict:
    """Refresh access token.

    Uses JWT-based authentication with database-backed user retrieval.
    """
    from core.security import create_access_token

    access_token = create_access_token(
        sub=current_user.get("email", "anonymous"),
        role=current_user.get("role", "visitor"),
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
    }
