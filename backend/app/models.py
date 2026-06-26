from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


# ── Lattice ──────────────────────────────────────────────────────────────────
class LatticeParameters(BaseModel):
    a: float
    b: float
    c: float
    alpha: float
    beta: float
    gamma: float
    volume: Optional[float] = None


# ── Atomic site ───────────────────────────────────────────────────────────────
class AtomicSite(BaseModel):
    label: str
    element: str
    x: float
    y: float
    z: float
    occupancy: float = 1.0


# ── Full material document ────────────────────────────────────────────────────
class Material(BaseModel):
    id: Optional[str] = Field(None, alias="_id")
    formula: str
    name: str
    crystal_system: Optional[str] = None
    space_group: Optional[str] = None
    space_group_number: Optional[int] = None
    density: Optional[float] = None
    band_gap: Optional[float] = None
    formation_energy: Optional[float] = None
    lattice: Optional[LatticeParameters] = None
    sites: Optional[List[AtomicSite]] = None
    elements: Optional[List[str]] = None
    nsites: Optional[int] = None
    description: Optional[str] = None
    ai_summary: Optional[str] = None
    cif_path: Optional[str] = None
    cif_content: Optional[str] = None
    tags: Optional[List[str]] = None
    properties: Optional[Dict[str, Any]] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True


# ── API request / response schemas ───────────────────────────────────────────
class SearchRequest(BaseModel):
    query: str
    limit: int = 20
    skip: int = 0
    crystal_system: Optional[str] = None
    elements: Optional[List[str]] = None


class SearchResponse(BaseModel):
    results: List[Dict[str, Any]]
    total: int
    query: str


class MaterialListResponse(BaseModel):
    materials: List[Dict[str, Any]]
    total: int
    page: int
    limit: int


class SimilarMaterialsResponse(BaseModel):
    materials: List[Dict[str, Any]]


class FavoriteRequest(BaseModel):
    formula: str


class CompareRequest(BaseModel):
    formulas: List[str]
