"""
Material routes: list, get by formula, search, similar, compare, favorites, PDF export, CIF download.
"""
from fastapi import APIRouter, HTTPException, Query, Depends
from fastapi.responses import StreamingResponse, JSONResponse
from typing import Optional, List
import io
import logging

from app.database import get_db
from app.models import SearchRequest, SearchResponse, MaterialListResponse, CompareRequest
from app.ai_service import generate_material_summary

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["materials"])


# ── helpers ──────────────────────────────────────────────────────────────────

def _clean(doc: dict) -> dict:
    """Convert ObjectId to str and remove raw CIF content for list views."""
    if doc is None:
        return {}
    if "_id" in doc:
        doc["_id"] = str(doc["_id"])
    return doc


def _clean_detail(doc: dict) -> dict:
    """Full detail – keep cif_content but stringify _id."""
    if doc is None:
        return {}
    if "_id" in doc:
        doc["_id"] = str(doc["_id"])
    return doc


def _strip_cif(doc: dict) -> dict:
    d = dict(doc)
    d.pop("cif_content", None)
    return d


# ── GET /api/materials ────────────────────────────────────────────────────────

@router.get("/materials", response_model=None)
async def list_materials(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    crystal_system: Optional[str] = None,
    element: Optional[str] = None,
    sort_by: Optional[str] = Query("formula", pattern="^(formula|name|density|crystal_system)$"),
):
    db = get_db()
    query: dict = {}
    if crystal_system:
        query["crystal_system"] = {"$regex": crystal_system, "$options": "i"}
    if element:
        query["elements"] = {"$in": [element]}

    skip = (page - 1) * limit
    cursor = db["materials"].find(query, {"cif_content": 0}).skip(skip).limit(limit).sort(sort_by or "formula", 1)
    docs = [_clean(d) async for d in cursor]
    total = await db["materials"].count_documents(query)

    return {"materials": docs, "total": total, "page": page, "limit": limit}


# ── GET /api/material/{formula} ───────────────────────────────────────────────

@router.get("/material/{formula}")
async def get_material(formula: str):
    db = get_db()
    doc = await db["materials"].find_one({"formula": {"$regex": f"^{formula}$", "$options": "i"}})
    if not doc:
        raise HTTPException(status_code=404, detail=f"Material '{formula}' not found")

    doc = _clean_detail(doc)

    # Generate AI summary on demand if missing
    if not doc.get("ai_summary"):
        summary = await generate_material_summary(doc)
        doc["ai_summary"] = summary
        await db["materials"].update_one({"formula": doc["formula"]}, {"$set": {"ai_summary": summary}})

    return doc


# ── POST /api/search ──────────────────────────────────────────────────────────

@router.post("/search", response_model=None)
async def search_materials(req: SearchRequest):
    db = get_db()
    query_str = req.query.strip()

    match_filter: dict = {}

    if query_str:
        # Support element symbol exactly (e.g. "Na", "Fe") and general regex
        match_filter["$or"] = [
            {"formula": {"$regex": query_str, "$options": "i"}},
            {"name": {"$regex": query_str, "$options": "i"}},
            {"elements": {"$in": [
                query_str,
                query_str.capitalize(),
                query_str.upper(),
            ]}},
            {"tags": {"$in": [query_str.lower()]}},
            {"crystal_system": {"$regex": query_str, "$options": "i"}},
            {"space_group": {"$regex": query_str, "$options": "i"}},
        ]

    if req.crystal_system:
        match_filter["crystal_system"] = {"$regex": req.crystal_system, "$options": "i"}
    if req.elements:
        match_filter["elements"] = {"$all": req.elements}

    projection = {"cif_content": 0}
    total = await db["materials"].count_documents(match_filter)
    cursor = (
        db["materials"]
        .find(match_filter, projection)
        .skip(req.skip)
        .limit(req.limit)
        .sort("formula", 1)
    )
    docs = [_clean(d) async for d in cursor]

    return {"results": docs, "total": total, "query": query_str}


# ── GET /api/suggestions ──────────────────────────────────────────────────────

@router.get("/suggestions")
async def get_suggestions(q: str = Query(..., min_length=1)):
    db = get_db()
    # Search anywhere in formula or name (remove ^ anchor so mid-word matches work)
    regex = {"$regex": q, "$options": "i"}
    cursor = db["materials"].find(
        {"$or": [
            {"formula": regex},
            {"name": regex},
            {"elements": {"$in": [q.capitalize(), q.upper(), q.lower()]}},
        ]},
        {"formula": 1, "name": 1, "crystal_system": 1, "_id": 0}
    ).limit(10)
    results = [{"formula": d["formula"], "name": d.get("name", d["formula"]), "crystal_system": d.get("crystal_system", "")} async for d in cursor]
    return results


# ── GET /api/similar/{formula} ────────────────────────────────────────────────

@router.get("/similar/{formula}")
async def get_similar(formula: str, limit: int = Query(4, ge=1, le=10)):
    db = get_db()
    source = await db["materials"].find_one({"formula": {"$regex": f"^{formula}$", "$options": "i"}})
    if not source:
        raise HTTPException(status_code=404, detail="Material not found")

    crystal_system = source.get("crystal_system")
    elements = source.get("elements", [])

    cursor = db["materials"].find(
        {
            "formula": {"$ne": source["formula"]},
            "$or": [
                {"crystal_system": crystal_system},
                {"elements": {"$in": elements}},
            ],
        },
        {"cif_content": 0}
    ).limit(limit)

    docs = [_clean(d) async for d in cursor]
    return {"materials": docs}


# ── POST /api/compare ─────────────────────────────────────────────────────────

@router.post("/compare")
async def compare_materials(req: CompareRequest):
    db = get_db()
    results = []
    for f in req.formulas:
        doc = await db["materials"].find_one(
            {"formula": {"$regex": f"^{f}$", "$options": "i"}},
            {"cif_content": 0}
        )
        if doc:
            results.append(_clean(doc))
    return {"materials": results}


# ── GET /api/download/cif/{formula} ──────────────────────────────────────────

@router.get("/download/cif/{formula}")
async def download_cif(formula: str):
    db = get_db()
    doc = await db["materials"].find_one({"formula": {"$regex": f"^{formula}$", "$options": "i"}})
    if not doc:
        raise HTTPException(status_code=404, detail="Material not found")

    # Use stored CIF content if available
    if doc.get("cif_content"):
        content = doc["cif_content"].encode("utf-8")
    else:
        # Generate CIF from stored structure data
        content = _generate_cif(doc).encode("utf-8")

    return StreamingResponse(
        io.BytesIO(content),
        media_type="chemical/x-cif",
        headers={"Content-Disposition": f"attachment; filename={formula}.cif"}
    )


def _generate_cif(doc: dict) -> str:
    """Generate a minimal valid CIF file from stored material data."""
    formula = doc.get("formula", "Unknown")
    lat = doc.get("lattice") or {}
    sites = doc.get("sites") or []
    sg = doc.get("space_group", "P 1")
    cs = doc.get("crystal_system", "triclinic")

    lines = [
        f"data_{formula}",
        "",
        f"_cell_length_a                  {lat.get('a', 5.0):.6f}",
        f"_cell_length_b                  {lat.get('b', 5.0):.6f}",
        f"_cell_length_c                  {lat.get('c', 5.0):.6f}",
        f"_cell_angle_alpha               {lat.get('alpha', 90.0):.4f}",
        f"_cell_angle_beta                {lat.get('beta', 90.0):.4f}",
        f"_cell_angle_gamma               {lat.get('gamma', 90.0):.4f}",
        f"_cell_volume                    {lat.get('volume', 0.0):.4f}",
        "",
        f"_symmetry_space_group_name_H-M  '{sg}'",
        f"_symmetry_cell_setting          {cs}",
        "",
        "loop_",
        "_atom_site_label",
        "_atom_site_type_symbol",
        "_atom_site_fract_x",
        "_atom_site_fract_y",
        "_atom_site_fract_z",
        "_atom_site_occupancy",
    ]

    for site in sites:
        label = site.get("label", site.get("element", "X"))
        el = site.get("element", "X")
        x = site.get("x", 0.0)
        y = site.get("y", 0.0)
        z = site.get("z", 0.0)
        occ = site.get("occupancy", 1.0)
        lines.append(f"{label:<6s}  {el:<4s}  {x:.6f}  {y:.6f}  {z:.6f}  {occ:.4f}")

    return "\n".join(lines) + "\n"


# ── GET /api/export/pdf/{formula} ────────────────────────────────────────────

@router.get("/export/pdf/{formula}")
async def export_pdf(formula: str):
    db = get_db()
    doc = await db["materials"].find_one(
        {"formula": {"$regex": f"^{formula}$", "$options": "i"}},
        {"cif_content": 0}
    )
    if not doc:
        raise HTTPException(status_code=404, detail="Material not found")

    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        from reportlab.lib import colors
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle

        buf = io.BytesIO()
        doc_pdf = SimpleDocTemplate(buf, pagesize=letter, topMargin=0.75 * inch)
        styles = getSampleStyleSheet()
        story = []

        title_style = ParagraphStyle("title", parent=styles["Title"], fontSize=20, textColor=colors.HexColor("#6366f1"))
        story.append(Paragraph(f"{doc.get('name', doc['formula'])}", title_style))
        story.append(Paragraph(f"Formula: {doc['formula']}", styles["Heading2"]))
        story.append(Spacer(1, 0.2 * inch))

        # Properties table
        lattice = doc.get("lattice") or {}
        table_data = [
            ["Property", "Value"],
            ["Crystal System", doc.get("crystal_system", "—")],
            ["Space Group", doc.get("space_group", "—")],
            ["Density (g/cm³)", str(doc.get("density") or "—")],
            ["Band Gap (eV)", str(doc.get("band_gap") or "—")],
            ["Formation Energy", str(doc.get("formation_energy") or "—")],
            ["No. of Sites", str(doc.get("nsites") or "—")],
            ["a (Å)", str(lattice.get("a") or "—")],
            ["b (Å)", str(lattice.get("b") or "—")],
            ["c (Å)", str(lattice.get("c") or "—")],
            ["α (°)", str(lattice.get("alpha") or "—")],
            ["β (°)", str(lattice.get("beta") or "—")],
            ["γ (°)", str(lattice.get("gamma") or "—")],
            ["Volume (Å³)", str(lattice.get("volume") or "—")],
        ]
        t = Table(table_data, colWidths=[2.5 * inch, 3 * inch])
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#6366f1")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f0f0ff")]),
            ("FONTSIZE", (0, 0), (-1, -1), 10),
        ]))
        story.append(t)
        story.append(Spacer(1, 0.3 * inch))

        if doc.get("ai_summary"):
            story.append(Paragraph("AI Summary", styles["Heading2"]))
            story.append(Paragraph(doc["ai_summary"].replace("\n", "<br/>"), styles["Normal"]))

        doc_pdf.build(story)
        buf.seek(0)
        return StreamingResponse(
            buf,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={formula}_report.pdf"}
        )
    except Exception as e:
        logger.error(f"PDF generation error: {e}")
        raise HTTPException(status_code=500, detail="PDF generation failed")


# ── GET /api/stats ────────────────────────────────────────────────────────────

@router.get("/stats")
async def get_stats():
    db = get_db()
    total = await db["materials"].count_documents({})
    pipeline = [{"$group": {"_id": "$crystal_system", "count": {"$sum": 1}}}]
    cs_dist = {d["_id"]: d["count"] async for d in db["materials"].aggregate(pipeline)}
    return {"total_materials": total, "crystal_system_distribution": cs_dist}


# ── GET /api/elements ─────────────────────────────────────────────────────────

@router.get("/elements")
async def get_elements():
    db = get_db()
    elements = await db["materials"].distinct("elements")
    return sorted(elements)
