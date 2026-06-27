"""
CrysText FastAPI application entry point.
"""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import connect_db, close_db
from app.routes.materials import router as materials_router
from app.routes.favorites import router as favorites_router
from app.routes.auth import router as auth_router

logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(name)s  %(message)s")
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        await connect_db()
    except Exception as e:
        logger.error(f"MongoDB connection failed on startup: {e}. App will start anyway.")
    yield
    await close_db()


app = FastAPI(
    title="CrysText API",
    description="AI-powered materials informatics platform",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(materials_router)
app.include_router(favorites_router)
app.include_router(auth_router)


@app.get("/health")
async def health():
    return {"status": "ok", "version": "1.0.0"}
