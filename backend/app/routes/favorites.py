"""
Favorites routes – stored in MongoDB.
Uses JWT auth if logged in, falls back to session_id header for anonymous users.
"""
from fastapi import APIRouter, Cookie, Response, Request
from typing import Optional
import uuid

from app.database import get_db
from app.models import FavoriteRequest
from app.auth import decode_token

router = APIRouter(prefix="/api/favorites", tags=["favorites"])


def _get_session_key(request: Request, session_id: Optional[str]) -> str:
    """Get a unique key — prefer JWT user id, fall back to session cookie, then new UUID."""
    # Try JWT token from Authorization header
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        payload = decode_token(auth[7:])
        if payload and payload.get("sub"):
            return f"user:{payload['sub']}"
    # Fall back to cookie-based session
    return session_id or str(uuid.uuid4())


@router.get("")
async def get_favorites(request: Request, session_id: Optional[str] = Cookie(default=None)):
    db = get_db()
    sid = _get_session_key(request, session_id)
    doc = await db["favorites"].find_one({"session_id": sid})
    formulas = doc.get("formulas", []) if doc else []

    materials = []
    async for m in db["materials"].find({"formula": {"$in": formulas}}, {"cif_content": 0}):
        m["_id"] = str(m["_id"])
        materials.append(m)

    return {"materials": materials, "session_id": sid}


@router.post("")
async def add_favorite(req: FavoriteRequest, request: Request, response: Response,
                       session_id: Optional[str] = Cookie(default=None)):
    db = get_db()
    sid = _get_session_key(request, session_id)
    # Set cookie for anonymous users
    if not sid.startswith("user:"):
        response.set_cookie("session_id", sid, max_age=30 * 24 * 3600,
                            samesite="none", secure=True)

    await db["favorites"].update_one(
        {"session_id": sid},
        {"$addToSet": {"formulas": req.formula}},
        upsert=True
    )
    return {"status": "added", "formula": req.formula, "session_id": sid}


@router.delete("/{formula}")
async def remove_favorite(formula: str, request: Request, response: Response,
                          session_id: Optional[str] = Cookie(default=None)):
    db = get_db()
    sid = _get_session_key(request, session_id)
    if not sid.startswith("user:"):
        response.set_cookie("session_id", sid, max_age=30 * 24 * 3600,
                            samesite="none", secure=True)

    await db["favorites"].update_one(
        {"session_id": sid},
        {"$pull": {"formulas": formula}}
    )
    return {"status": "removed", "formula": formula}
