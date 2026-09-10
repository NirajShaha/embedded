from datetime import datetime, timedelta, timezone
from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import InvalidTokenError
from pwdlib import PasswordHash

from app.config import settings
from app.prisma_client import db


password_hash = PasswordHash.recommended()

bearer_scheme = HTTPBearer(
    auto_error=False,
)


def hash_password(password: str) -> str:
    """Hash a password using the configured secure password hasher."""

    return password_hash.hash(password)


def verify_password(
    plain_password: str,
    hashed_password: str,
) -> bool:
    """Verify a plaintext password against a stored password hash."""

    try:
        return password_hash.verify(
            plain_password,
            hashed_password,
        )
    except Exception:
        return False


def create_access_token(
    *,
    user_id: int,
    username: str,
    role: str,
) -> str:
    """Create a signed JWT access token."""

    now = datetime.now(timezone.utc)

    expires_at = now + timedelta(
        minutes=settings.access_token_expire_minutes,
    )

    payload = {
        "sub": str(user_id),
        "username": username,
        "role": role,
        "iat": now,
        "exp": expires_at,
    }

    return jwt.encode(
        payload,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )


async def get_current_user(
    credentials: Annotated[
        HTTPAuthorizationCredentials | None,
        Depends(bearer_scheme),
    ],
):
    """Return the database user represented by a valid bearer token."""

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication required",
        headers={
            "WWW-Authenticate": "Bearer",
        },
    )

    if credentials is None:
        raise credentials_exception

    if credentials.scheme.lower() != "bearer":
        raise credentials_exception

    try:
        payload = jwt.decode(
            credentials.credentials,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )

        subject = payload.get("sub")

        if subject is None:
            raise credentials_exception

        user_id = int(subject)

    except (
        InvalidTokenError,
        ValueError,
        TypeError,
    ):
        raise credentials_exception

    user = await db.users.find_unique(
        where={
            "id": user_id,
        }
    )

    if user is None:
        raise credentials_exception

    if user.role not in {
        "ADMIN",
        "USER",
    }:
        raise credentials_exception

    return user


async def require_admin(
    current_user=Depends(get_current_user),
):
    """Allow only authenticated ADMIN users."""

    if current_user.role != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )

    return current_user