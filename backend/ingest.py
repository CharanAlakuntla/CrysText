"""
Ingest script – scans dataset/cif_files, parses CIF files, and upserts into MongoDB.
Run from the backend/ directory:
    python ingest.py
"""
import asyncio
import os
import sys
import logging

sys.path.insert(0, os.path.dirname(__file__))

from motor.motor_asyncio import AsyncIOMotorClient
from app.config import settings
from app.cif_parser import scan_cif_folder
from app.ai_service import generate_material_summary

logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")
logger = logging.getLogger(__name__)


async def main():
    client = AsyncIOMotorClient(settings.mongodb_url)
    db = client[settings.mongodb_db]
    col = db["materials"]

    # Create indexes
    from pymongo import IndexModel, ASCENDING, TEXT
    await col.create_indexes([
        IndexModel([("formula", TEXT), ("name", TEXT), ("description", TEXT)]),
        IndexModel([("formula", ASCENDING)], unique=True),
        IndexModel([("crystal_system", ASCENDING)]),
    ])

    cif_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), settings.cif_folder))
    logger.info(f"Scanning CIF folder: {cif_dir}")

    materials = scan_cif_folder(cif_dir)
    logger.info(f"Parsed {len(materials)} materials")

    inserted = 0
    updated = 0
    for mat in materials:
        # Generate AI summary
        if not mat.get("ai_summary"):
            mat["ai_summary"] = await generate_material_summary(mat)

        result = await col.update_one(
            {"formula": mat["formula"]},
            {"$set": mat},
            upsert=True
        )
        if result.upserted_id:
            inserted += 1
        else:
            updated += 1

    logger.info(f"Done. Inserted: {inserted}, Updated: {updated}")
    client.close()


if __name__ == "__main__":
    asyncio.run(main())
