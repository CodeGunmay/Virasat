"""Security utilities for Virasat.

Handles password hashing, token creation, and authentication.
"""

import os
import secrets
from db.base import get_db
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any

import bcrypt
from fastapi import APIRouter, Body, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

# Security configuration - from environment variables in production
SECRET_KEY = os.getenv("VIRASAT_SECRET_KEY") or secrets.token_urlsafe(32)
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("VIRASAT_TOKEN_EXPIRE_MINUTES", "1440"))

# Bearer token scheme
bearer_scheme = HTTPBearer(auto_error=False)


def hash_password(password: str) -> str:
    """Hash a password using bcrypt.

    Uses bcrypt for password hashing. In production, this should
    be configured via environment variables or a secrets manager.
    """
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    try:
        return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
    except Exception:
        return False


def authenticate_user(email: str, password: str, db_session) -> Optional[dict]:
    """Authenticate a user by email and password.

    Queries the database for the user and verifies the password
    against the stored hash.
    """
    from db.models import User

    user = db_session.query(User).filter(User.email == email).first()
    if not user:
        return None

    if not verify_password(password, user.password_hash):
        return None

    # Return user info
    return {
        "id": user.id,
        "email": user.email,
        "role": user.role,
    }


def create_access_token(sub: str, role: str = "visitor", expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token.

    Args:
        sub: The subject (user identifier/email)
        role: The user role, included in token payload
        expires_delta: Optional timedelta for expiration

    Returns:
        Encoded JWT string
    """
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode = {"exp": expire, "sub": str(sub), "role": role}
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_token(token: str) -> Optional[Dict[str, Any]]:
    """Decode and validate a JWT token."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db_session = Depends(get_db),
) -> Optional[Dict[str, Any]]:
    """Get current user from JWT token in Authorization header.

    Validates the token and retrieves user information from the database.
    Returns None if the token is missing, invalid, or the user is not found.
    """
    if not credentials:
        return None

    token = credentials.credentials

    payload = decode_token(token)
    if payload is None:
        return None

    user_id: str = payload.get("sub")
    if user_id is None:
        return None

    # Look up the user from the database using db_session
    from db.models import User

    user = db_session.query(User).filter(User.email == user_id).first()
    if not user:
        return None

    # Return user info from database
    return {
        "id": user.id,
        "email": user.email,
        "role": user.role,
    }


AUTHENTICATED_ROLES = {"visitor", "contributor", "moderator"}


def require_user(current_user: Optional[Dict[str, Any]] = Depends(get_current_user)) -> Dict[str, Any]:
    if current_user is None:
        raise HTTPException(status_code=401, detail="Authentication required")
    return current_user


def check_role(required_role: str):
    """Dependency factory for role-based access control.

    Args:
        required_role: The minimum role required to access the endpoint.

    Returns:
        A dependency that checks the user's role.
    """

    def role_checker(current_user: Dict[str, Any] = Depends(get_current_user)) -> dict:
        if not current_user or current_user.get("role") != required_role:
            from fastapi import HTTPException
            raise HTTPException(
                status_code=403,
                detail=f"User requires role: {required_role}",
            )
        return current_user

    return role_checker
