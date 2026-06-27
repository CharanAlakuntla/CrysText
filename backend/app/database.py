from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import IndexModel, ASCENDING, TEXT
from app.config import settings
import logging

logger = logging.getLogger(__name__)

client: AsyncIOMotorClient = None
db = None


async def connect_db():
    global client, db
    import certifi
    # Use certifi CA bundle for Atlas SSL compatibility
    client = AsyncIOMotorClient(
        settings.mongodb_url,
        tlsCAFile=certifi.where(),
        serverSelectionTimeoutMS=30000,
        connectTimeoutMS=30000,
        socketTimeoutMS=30000,
    )
    db = client[settings.mongodb_db]
    # Test connection before proceeding
    await client.admin.command("ping")
    await create_indexes()
    logger.info(f"Connected to MongoDB: {settings.mongodb_db}")


async def close_db():
    global client
    if client:
        client.close()
        logger.info("Disconnected from MongoDB")


async def create_indexes():
    """Create text and field indexes for fast search. Drops conflicting indexes first."""
    materials = db["materials"]

    # Drop any existing text index (there can only be one per collection)
    try:
        existing = await materials.index_information()
        for idx_name, idx_info in existing.items():
            key_types = [v for _, v in idx_info.get("key", [])]
            if "text" in key_types:
                await materials.drop_index(idx_name)
                logger.info(f"Dropped old text index: {idx_name}")
    except Exception as e:
        logger.warning(f"Could not inspect/drop old indexes: {e}")

    # Recreate indexes
    try:
        await materials.create_index(
            [("formula", TEXT), ("name", TEXT), ("description", TEXT)],
            name="text_search"
        )
    except Exception as e:
        logger.warning(f"Text index creation skipped: {e}")

    try:
        await materials.create_index([("formula", ASCENDING)], unique=True)
    except Exception as e:
        logger.warning(f"Formula unique index skipped: {e}")

    await materials.create_index([("crystal_system", ASCENDING)])
    await materials.create_index([("space_group", ASCENDING)])
    logger.info("MongoDB indexes ready")


def get_db():
    return db
