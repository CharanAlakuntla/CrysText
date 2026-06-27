"""
CIF file parser using pymatgen.
Extracts structure metadata and atomic coordinates.
"""
import os
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime

logger = logging.getLogger(__name__)


def parse_cif_file(cif_path: str) -> Optional[Dict[str, Any]]:
    """Parse a CIF file and return a material document dict."""
    try:
        from pymatgen.core import Structure
        from pymatgen.symmetry.analyzer import SpacegroupAnalyzer
        structure = Structure.from_file(cif_path)
        analyzer = SpacegroupAnalyzer(structure)
        sym_structure = analyzer.get_symmetrized_structure()

        # Basic info
        formula = structure.composition.reduced_formula
        lattice = structure.lattice

        # Space group
        try:
            sg_symbol = analyzer.get_space_group_symbol()
            sg_number = analyzer.get_space_group_number()
            crystal_system = analyzer.get_crystal_system()
        except Exception:
            sg_symbol = "Unknown"
            sg_number = None
            crystal_system = "Unknown"

        # Density
        try:
            density = round(structure.density, 4)
        except Exception:
            density = None

        # Atomic sites
        sites = []
        for site in structure.sites:
            sites.append({
                "label": str(site.specie),
                "element": str(site.specie.symbol),
                "x": round(site.frac_coords[0], 6),
                "y": round(site.frac_coords[1], 6),
                "z": round(site.frac_coords[2], 6),
                "occupancy": 1.0,
            })

        # Elements list
        elements = list({str(sp.symbol) for sp in structure.composition.elements})

        # Read raw CIF content
        with open(cif_path, "r", encoding="utf-8", errors="ignore") as f:
            cif_content = f.read()

        # Build a human-friendly name from formula
        name = _formula_to_name(formula)

        doc = {
            "formula": formula,
            "name": name,
            "crystal_system": crystal_system,
            "space_group": sg_symbol,
            "space_group_number": sg_number,
            "density": density,
            "band_gap": None,        # populated separately if available
            "formation_energy": None,
            "lattice": {
                "a": round(lattice.a, 6),
                "b": round(lattice.b, 6),
                "c": round(lattice.c, 6),
                "alpha": round(lattice.alpha, 4),
                "beta": round(lattice.beta, 4),
                "gamma": round(lattice.gamma, 4),
                "volume": round(lattice.volume, 4),
            },
            "sites": sites,
            "elements": elements,
            "nsites": len(sites),
            "description": None,
            "ai_summary": None,
            "cif_path": os.path.basename(cif_path),
            "cif_content": cif_content,
            "tags": _generate_tags(formula, crystal_system, elements),
            "properties": {},
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }
        return doc

    except Exception as e:
        logger.error(f"Failed to parse {cif_path}: {e}")
        return None


def scan_cif_folder(folder_path: str) -> List[Dict[str, Any]]:
    """Scan a folder for CIF files and return list of parsed documents."""
    materials = []
    if not os.path.isdir(folder_path):
        logger.warning(f"CIF folder not found: {folder_path}")
        return materials

    cif_files = [f for f in os.listdir(folder_path) if f.lower().endswith(".cif")]
    logger.info(f"Found {len(cif_files)} CIF files in {folder_path}")

    for fname in cif_files:
        path = os.path.join(folder_path, fname)
        doc = parse_cif_file(path)
        if doc:
            materials.append(doc)
            logger.info(f"Parsed: {doc['formula']} from {fname}")
        else:
            logger.warning(f"Skipped: {fname}")

    return materials


def _formula_to_name(formula: str) -> str:
    """Map common formulas to material names."""
    name_map = {
        "NaCl": "Sodium Chloride (Rock Salt)",
        "KCl": "Potassium Chloride (Sylvite)",
        "CaF2": "Calcium Fluoride (Fluorite)",
        "MgO": "Magnesium Oxide (Periclase)",
        "SiO2": "Silicon Dioxide (Quartz)",
        "TiO2": "Titanium Dioxide (Rutile)",
        "Fe2O3": "Iron(III) Oxide (Hematite)",
        "Al2O3": "Aluminum Oxide (Corundum)",
        "ZnS": "Zinc Sulfide (Sphalerite)",
        "GaAs": "Gallium Arsenide",
        "Si": "Silicon (Diamond Cubic)",
        "Ge": "Germanium",
        "C": "Carbon (Diamond)",
        "Al": "Aluminum (FCC)",
        "Cu": "Copper (FCC)",
        "Au": "Gold (FCC)",
        "Ag": "Silver (FCC)",
        "Fe": "Iron (BCC)",
        "Cr": "Chromium (BCC)",
        "W": "Tungsten (BCC)",
        "SrTiO3": "Strontium Titanate (Perovskite)",
        "CsCl": "Cesium Chloride",
        "FeS2": "Iron Disulfide (Pyrite)",
        "LiFePO4": "Lithium Iron Phosphate (Olivine)",
    }
    return name_map.get(formula, formula)


def _generate_tags(formula: str, crystal_system: str, elements: List[str]) -> List[str]:
    tags = []
    if crystal_system:
        tags.append(crystal_system.lower())
    # Metal / ceramic / semiconductor heuristics
    metals = {"Fe", "Cu", "Al", "Au", "Ag", "Cr", "W", "Ti", "Ni", "Co"}
    if any(e in metals for e in elements):
        tags.append("metal")
    if "Si" in elements or "Ge" in elements or "GaAs" in formula:
        tags.append("semiconductor")
    if "O" in elements:
        tags.append("oxide")
    if "S" in elements:
        tags.append("sulfide")
    if "N" in elements:
        tags.append("nitride")
    return tags
