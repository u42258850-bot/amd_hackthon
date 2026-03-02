from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo.server_api import ServerApi

from .config import settings


mongo_client: AsyncIOMotorClient | None = None
database: AsyncIOMotorDatabase | None = None

if settings.mongo_uri:
    mongo_client = AsyncIOMotorClient(settings.mongo_uri, server_api=ServerApi("1"))
    database = mongo_client[settings.mongo_db_name]


def get_database() -> AsyncIOMotorDatabase | None:
    return database


async def ping_database() -> None:
    if mongo_client is None:
        return
    await mongo_client.admin.command("ping")
