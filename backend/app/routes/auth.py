"""
Auth routes: register, login, me, logout.
"""
from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel, Field
from datetime import datetime

from app.database import get_db
from app.auth import hash_password, verify_password, create_access_token, get_current_user

router = APIRouter(prefix="/api/auth", tags=["auth"])


# ── Schemas ───────────────────────────────────────────────────────────────────

class RegisterRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=80)
    email: str = Field(..., min_length=5, max_length=200)
    password: str = Field(..., min_length=6, max_length=128)


class LoginRequest(BaseModel):
    email: str
    password: str


class AuthResponse(BaseModel):
    token: str
    user: dict


# ── POST /api/auth/register ───────────────────────────────────────────────────

@router.post("/register", response_model=None)
async def register(req: RegisterRequest):
    db = get_db()
    existing = await db["users"].find_one({"email": req.email.lower()})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    user_doc = {
        "name": req.name.strip(),
        "email": req.email.lower(),
        "password_hash": hash_password(req.password),
        "created_at": datetime.utcnow(),
        "favorites": [],
    }
    result = await db["users"].insert_one(user_doc)
    user_id = str(result.inserted_id)

    token = create_access_token({"sub": user_id, "email": req.email.lower(), "name": req.name.strip()})
    return {
        "token": token,
        "user": {"id": user_id, "name": req.name.strip(), "email": req.email.lower()}
    }


# ── POST /api/auth/login ──────────────────────────────────────────────────────

@router.post("/login", response_model=None)
async def login(req: LoginRequest):
    db = get_db()
    user = await db["users"].find_one({"email": req.email.lower()})
    if not user or not verify_password(req.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    user_id = str(user["_id"])
    token = create_access_token({"sub": user_id, "email": user["email"], "name": user["name"]})
    return {
        "token": token,
        "user": {"id": user_id, "name": user["name"], "email": user["email"]}
    }


# ── GET /api/auth/me ──────────────────────────────────────────────────────────

@router.get("/me")
async def me(current_user: dict = Depends(get_current_user)):
    return {
        "id": current_user.get("sub"),
        "name": current_user.get("name"),
        "email": current_user.get("email"),
    }


# ── POST /api/auth/logout ─────────────────────────────────────────────────────

@router.post("/logout")
async def logout():
    # JWT is stateless – client just deletes the token
    return {"message": "Logged out successfully"}
