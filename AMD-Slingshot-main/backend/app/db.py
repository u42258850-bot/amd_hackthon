from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo.server_api import ServerApi

from .config import settings


def _normalize_mongo_uri(value: str | None) -> str | None:
    if value is None:
        return None

    normalized = value.strip().strip('"').strip("'")
    if not normalized:
        return None

    if normalized.lower().startswith("mongo_uri="):
        normalized = normalized.split("=", 1)[1].strip()

    return normalized or None


mongo_uri = _normalize_mongo_uri(settings.mongo_uri)

mongo_client: AsyncIOMotorClient | None = None
database: AsyncIOMotorDatabase | None = None

if mongo_uri:
    mongo_client = AsyncIOMotorClient(mongo_uri, server_api=ServerApi("1"))
    database = mongo_client[settings.mongo_db_name]


def get_database() -> AsyncIOMotorDatabase | None:
    return database


async def ping_database() -> None:
    if mongo_client is None:
        return
    await mongo_client.admin.command("ping")
