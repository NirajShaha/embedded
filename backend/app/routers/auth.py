from fastapi import APIRouter, Depends, HTTPException, status

from app.auth import (
    create_access_token,
    get_current_user,
    verify_password,
)
from app.prisma_client import db
from app.schemas import (
    AuthUserRead,
    LoginRequest,
    LoginResponse,
)


router = APIRouter(
    prefix="/auth",
    tags=["authentication"],
)


def _map_user(user) -> AuthUserRead:
    return AuthUserRead(
        id=int(user.id),
        username=user.username,
        role=user.role,
    )


@router.post(
    "/login",
    response_model=LoginResponse,
)
async def login(
    payload: LoginRequest,
):
    username = payload.username.strip()

    user = await db.users.find_unique(
        where={
            "username": username,
        }
    )

    if user is None or not verify_password(
        payload.password,
        user.password,
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={
                "WWW-Authenticate": "Bearer",
            },
        )

    access_token = create_access_token(
        user_id=int(user.id),
        username=user.username,
        role=user.role,
    )

    return LoginResponse(
        access_token=access_token,
        user=_map_user(user),
    )


@router.get(
    "/me",
    response_model=AuthUserRead,
)
async def get_me(
    current_user=Depends(get_current_user),
):
    return _map_user(current_user)