from __future__ import annotations

from fastapi import Depends, Header, HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.config import settings
from app.db import get_database
from app.services.firebase_service import verify_firebase_token


async def get_current_user_id(
    authorization: str = Header(default=""),
    x_dev_user_id: str | None = Header(default=None),
) -> str:
    # Fast path: when dev bypass is enabled and X-Dev-User-Id is provided,
    # skip Firebase verification entirely (don't even attempt the HTTP call).
    if (
        settings.environment != "production"
        and settings.allow_dev_auth_bypass
        and x_dev_user_id
    ):
        return x_dev_user_id

    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token")

    token = authorization.removeprefix("Bearer ").strip()
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid bearer token")

    try:
        decoded = verify_firebase_token(token)
        return str(decoded.get("uid"))
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Firebase token") from exc


def get_db() -> AsyncIOMotorDatabase | None:
    return get_database()


DbDependency = Depends(get_db)
UserIdDependency = Depends(get_current_user_id)
