"""
Migrate local MongoDB to MongoDB Atlas.
Run: python migrate_to_atlas.py --atlas "mongodb+srv://crystext:PASSWORD@cluster0.xxx.mongodb.net"
"""
import asyncio, sys, os, argparse
sys.path.insert(0, os.path.dirname(__file__))
from motor.motor_asyncio import AsyncIOMotorClient
import logging

logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")
logger = logging.getLogger(__name__)

LOCAL_URL = "mongodb://localhost:27017"
DB_NAME   = "crystext"
BATCH     = 500


async def migrate(atlas_url: str):
    logger.info("Connecting to local MongoDB...")
    local  = AsyncIOMotorClient(LOCAL_URL)
    logger.info("Connecting to Atlas...")
    remote = AsyncIOMotorClient(atlas_url)

    local_db  = local[DB_NAME]
    remote_db = remote[DB_NAME]

    for col_name in ["materials", "users", "favorites"]:
        total = await local_db[col_name].count_documents({})
        if total == 0:
            logger.info(f"  {col_name}: empty, skipping")
            continue

        logger.info(f"  Migrating {col_name} ({total} docs)...")
        cursor = local_db[col_name].find({})
        batch, done = [], 0

        async for doc in cursor:
            doc.pop("_id", None)  # let Atlas generate new _id
            batch.append(doc)
            if len(batch) >= BATCH:
                await remote_db[col_name].insert_many(batch, ordered=False)
                done += len(batch)
                batch = []
                logger.info(f"    {done}/{total}")

        if batch:
            await remote_db[col_name].insert_many(batch, ordered=False)
            done += len(batch)

        logger.info(f"  {col_name}: {done} docs migrated ✓")

    # Recreate indexes on Atlas
    from pymongo import ASCENDING, TEXT
    await remote_db["materials"].create_index(
        [("formula", TEXT), ("name", TEXT), ("description", TEXT)],
        name="text_search"
    )
    await remote_db["materials"].create_index([("formula", ASCENDING)], unique=True)
    await remote_db["materials"].create_index([("crystal_system", ASCENDING)])
    logger.info("Indexes created on Atlas ✓")

    local.close()
    remote.close()
    logger.info("\nMigration complete!")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--atlas", required=True, help="Atlas connection string")
    args = parser.parse_args()
    asyncio.run(migrate(args.atlas))
