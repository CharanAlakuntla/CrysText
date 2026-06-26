"""
Favorites routes – stored in MongoDB favorites collection (session-based via cookie).
"""
from fastapi import APIRouter, HTTPException, Cookie, Response
from typing import Optional
import uuid

from app.database import get_db
from app.models import FavoriteRequest

router = APIRouter(prefix="/api/favorites", tags=["favorites"])


def _get_session(session_id: Optional[str]) -> str:
    return session_id or str(uuid.uuid4())


@router.get("")
async def get_favorites(session_id: Optional[str] = Cookie(default=None)):
    db = get_db()
    sid = _get_session(session_id)
    doc = await db["favorites"].find_one({"session_id": sid})
    formulas = doc.get("formulas", []) if doc else []

    # Fetch material details
    materials = []
    async for m in db["materials"].find({"formula": {"$in": formulas}}, {"cif_content": 0}):
        m["_id"] = str(m["_id"])
        materials.append(m)

    return {"materials": materials, "session_id": sid}


@router.post("")
async def add_favorite(req: FavoriteRequest, response: Response, session_id: Optional[str] = Cookie(default=None)):
    db = get_db()
    sid = _get_session(session_id)
    response.set_cookie("session_id", sid, max_age=30 * 24 * 3600, samesite="lax")

    await db["favorites"].update_one(
        {"session_id": sid},
        {"$addToSet": {"formulas": req.formula}},
        upsert=True
    )
    return {"status": "added", "formula": req.formula}


@router.delete("/{formula}")
async def remove_favorite(formula: str, response: Response, session_id: Optional[str] = Cookie(default=None)):
    db = get_db()
    sid = _get_session(session_id)
    response.set_cookie("session_id", sid, max_age=30 * 24 * 3600, samesite="lax")

    await db["favorites"].update_one(
        {"session_id": sid},
        {"$pull": {"formulas": formula}}
    )
    return {"status": "removed", "formula": formula}
