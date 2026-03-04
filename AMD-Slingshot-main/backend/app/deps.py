import logging

from fastapi import Depends, Header, HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.config import settings
from app.db import get_database
from app.services.firebase_service import verify_firebase_token

_logger = logging.getLogger(__name__)

# Auth bypass is allowed when either:
#   1. ENVIRONMENT != production AND ALLOW_DEV_AUTH_BYPASS is True, OR
#   2. FIREBASE_SERVICE_ACCOUNT_JSON is NOT configured (no way to verify tokens)
_AUTH_BYPASS_ALLOWED = (
    (settings.environment != "production" and settings.allow_dev_auth_bypass)
    or not settings.firebase_service_account_json
)


async def get_current_user_id(
    authorization: str = Header(default=""),
    x_dev_user_id: str | None = Header(default=None),
) -> str:
    # Fast path: skip Firebase verification when bypass is allowed and
    # an X-Dev-User-Id header is provided.
    if _AUTH_BYPASS_ALLOWED and x_dev_user_id:
        return x_dev_user_id

    if not authorization.startswith("Bearer "):
        if _AUTH_BYPASS_ALLOWED and x_dev_user_id:
            return x_dev_user_id
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token")

    token = authorization.removeprefix("Bearer ").strip()
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid bearer token")

    try:
        decoded = verify_firebase_token(token)
        return str(decoded.get("uid"))
    except Exception as exc:  # noqa: BLE001
        _logger.warning("Firebase token verification failed: %s", exc)
        if _AUTH_BYPASS_ALLOWED and x_dev_user_id:
            return x_dev_user_id
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Firebase token") from exc


def get_db() -> AsyncIOMotorDatabase | None:
    return get_database()


DbDependency = Depends(get_db)
UserIdDependency = Depends(get_current_user_id)
