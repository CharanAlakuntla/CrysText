"""
ExtXYZ file parser for CrysText.
Supports standard ExtXYZ format used by ASE, GPAW, CASTEP, VASP outputs etc.

Format:
    Line 1: number of atoms
    Line 2: key=value pairs (Lattice, Properties, energy, etc.)
    Lines 3+: element  x  y  z  [extra columns]
"""
import os
import re
import math
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime

logger = logging.getLogger(__name__)


def _parse_comment_line(line: str) -> dict:
    """Parse the ExtXYZ comment line into a dict of key=value pairs."""
    info = {}
    # Match key="..." or key=value patterns
    pattern = r'(\w+)\s*=\s*"([^"]+)"|(\w+)\s*=\s*(\S+)'
    for m in re.finditer(pattern, line):
        if m.group(1):
            info[m.group(1)] = m.group(2)
        else:
            info[m.group(3)] = m.group(4)
    return info


def _lattice_to_params(lattice_str: str) -> Optional[dict]:
    """
    Convert Lattice="ax ay az bx by bz cx cy cz" to a/b/c/alpha/beta/gamma.
    Lattice vectors: a=(ax,ay,az), b=(bx,by,bz), c=(cx,cy,cz)
    """
    try:
        vals = [float(x) for x in lattice_str.split()]
        if len(vals) != 9:
            return None
        a_vec = vals[0:3]
        b_vec = vals[3:6]
        c_vec = vals[6:9]

        def norm(v): return math.sqrt(sum(x*x for x in v))
        def dot(u, v): return sum(u[i]*v[i] for i in range(3))

        a = norm(a_vec)
        b = norm(b_vec)
        c = norm(c_vec)
        alpha = math.degrees(math.acos(max(-1, min(1, dot(b_vec, c_vec) / (b * c)))))
        beta  = math.degrees(math.acos(max(-1, min(1, dot(a_vec, c_vec) / (a * c)))))
        gamma = math.degrees(math.acos(max(-1, min(1, dot(a_vec, b_vec) / (a * b)))))
        volume = abs(
            a_vec[0]*(b_vec[1]*c_vec[2] - b_vec[2]*c_vec[1]) -
            a_vec[1]*(b_vec[0]*c_vec[2] - b_vec[2]*c_vec[0]) +
            a_vec[2]*(b_vec[0]*c_vec[1] - b_vec[1]*c_vec[0])
        )
        return {
            "a": round(a, 6), "b": round(b, 6), "c": round(c, 6),
            "alpha": round(alpha, 4), "beta": round(beta, 4), "gamma": round(gamma, 4),
            "volume": round(volume, 4),
            "_vecs": [a_vec, b_vec, c_vec],
        }
    except Exception as e:
        logger.warning(f"Lattice parse failed: {e}")
        return None


def _cart_to_frac(cart: list, vecs: list) -> list:
    """Convert Cartesian coordinates to fractional using lattice vectors."""
    try:
        ax, ay, az = vecs[0]
        bx, by, bz = vecs[1]
        cx, cy, cz = vecs[2]
        x, y, z = cart

        # Solve [a|b|c] * frac = cart
        det = (ax*(by*cz - bz*cy) - ay*(bx*cz - bz*cx) + az*(bx*cy - by*cx))
        if abs(det) < 1e-10:
            return [0.0, 0.0, 0.0]
        fx = (x*(by*cz-bz*cy) - ay*(y*cz-z*cy) + az*(y*by-by*z)) / det
        fy = (ax*(y*cz-z*cy) - x*(bx*cz-bz*cx) + az*(bx*z-y*cx)) / det
        fz = (ax*(by*z-y*bz) - ay*(bx*z-x*bz) + x*(bx*by-by*bx)) / det
        return [round(fx % 1.0, 6), round(fy % 1.0, 6), round(fz % 1.0, 6)]
    except Exception:
        return [0.0, 0.0, 0.0]


def _infer_crystal_system(lattice: dict) -> str:
    a, b, c = lattice["a"], lattice["b"], lattice["c"]
    al, be, ga = lattice["alpha"], lattice["beta"], lattice["gamma"]

    def eq(x, y, tol=0.5): return abs(x - y) < tol
    def is90(x): return eq(x, 90.0)
    def is120(x): return eq(x, 120.0)

    if eq(a, b) and eq(b, c) and is90(al) and is90(be) and is90(ga):
        return "cubic"
    if eq(a, b) and is90(al) and is90(be) and is120(ga):
        return "hexagonal"
    if eq(a, b) and not eq(b, c) and is90(al) and is90(be) and is90(ga):
        return "tetragonal"
    if not eq(a, b) and not eq(b, c) and is90(al) and is90(be) and is90(ga):
        return "orthorhombic"
    if is90(al) and not is90(be) and is90(ga):
        return "monoclinic"
    if eq(a, b) and is90(al) and is90(be) and is120(ga):
        return "trigonal"
    return "triclinic"


def _formula_from_elements(element_counts: dict) -> str:
    """Build reduced formula like Fe2O3 from element counts."""
    from math import gcd
    from functools import reduce

    counts = list(element_counts.values())
    g = reduce(gcd, counts)
    parts = []
    for el, cnt in sorted(element_counts.items()):
        reduced = cnt // g
        parts.append(el if reduced == 1 else f"{el}{reduced}")
    return "".join(parts)


def _density(mass_amu: float, volume_A3: float) -> Optional[float]:
    """g/cm³ from total mass in amu and volume in Å³."""
    if volume_A3 <= 0:
        return None
    # 1 amu/Å³ = 1.66054 g/cm³
    return round(mass_amu / volume_A3 * 1.66054, 4)


# Atomic masses (amu) for density calculation
ATOMIC_MASS = {
    "H":1.008,"He":4.003,"Li":6.941,"Be":9.012,"B":10.811,"C":12.011,
    "N":14.007,"O":15.999,"F":18.998,"Ne":20.180,"Na":22.990,"Mg":24.305,
    "Al":26.982,"Si":28.086,"P":30.974,"S":32.065,"Cl":35.453,"Ar":39.948,
    "K":39.098,"Ca":40.078,"Sc":44.956,"Ti":47.867,"V":50.942,"Cr":51.996,
    "Mn":54.938,"Fe":55.845,"Co":58.933,"Ni":58.693,"Cu":63.546,"Zn":65.380,
    "Ga":69.723,"Ge":72.640,"As":74.922,"Se":78.960,"Br":79.904,"Kr":83.798,
    "Rb":85.468,"Sr":87.620,"Y":88.906,"Zr":91.224,"Nb":92.906,"Mo":95.960,
    "Ru":101.07,"Rh":102.91,"Pd":106.42,"Ag":107.87,"Cd":112.41,"In":114.82,
    "Sn":118.71,"Sb":121.76,"Te":127.60,"I":126.90,"Cs":132.91,"Ba":137.33,
    "La":138.91,"Ce":140.12,"Hf":178.49,"Ta":180.95,"W":183.84,"Re":186.21,
    "Os":190.23,"Ir":192.22,"Pt":195.08,"Au":196.97,"Hg":200.59,"Pb":207.20,
    "Bi":208.98,"U":238.03,"Th":232.04,
}


def parse_extxyz_file(filepath: str) -> List[Dict[str, Any]]:
    """
    Parse an ExtXYZ file. Returns list of material documents (one per frame).
    """
    results = []
    try:
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()
    except Exception as e:
        logger.error(f"Cannot read {filepath}: {e}")
        return results

    i = 0
    frame_idx = 0
    filename = os.path.basename(filepath)
    stem = os.path.splitext(filename)[0]

    while i < len(lines):
        try:
            # Line 1: number of atoms
            n_atoms = int(lines[i].strip())
            if n_atoms <= 0:
                i += 1
                continue

            # Line 2: comment / info
            info_line = lines[i + 1].strip() if i + 1 < len(lines) else ""
            info = _parse_comment_line(info_line)

            # Parse lattice
            lattice = None
            vecs = None
            if "Lattice" in info:
                lattice = _lattice_to_params(info["Lattice"])
                if lattice:
                    vecs = lattice.pop("_vecs")

            # Parse atom lines
            element_counts: Dict[str, int] = {}
            sites = []
            for j in range(n_atoms):
                atom_line = lines[i + 2 + j].split() if i + 2 + j < len(lines) else []
                if len(atom_line) < 4:
                    continue
                el = atom_line[0].capitalize()
                try:
                    cx, cy, cz = float(atom_line[1]), float(atom_line[2]), float(atom_line[3])
                except ValueError:
                    continue

                element_counts[el] = element_counts.get(el, 0) + 1
                label = f"{el}{element_counts[el]}"

                # Convert Cartesian → fractional if lattice available
                if vecs:
                    fx, fy, fz = _cart_to_frac([cx, cy, cz], vecs)
                else:
                    fx, fy, fz = cx, cy, cz

                sites.append({"label": label, "element": el,
                               "x": fx, "y": fy, "z": fz, "occupancy": 1.0})

            if not sites:
                i += 2 + n_atoms
                frame_idx += 1
                continue

            # Build formula
            formula = _formula_from_elements(element_counts)
            elements = sorted(element_counts.keys())

            # Crystal system
            crystal_system = _infer_crystal_system(lattice) if lattice else "unknown"

            # Density
            density = None
            if lattice and lattice.get("volume"):
                total_mass = sum(
                    ATOMIC_MASS.get(el, 50) * cnt
                    for el, cnt in element_counts.items()
                )
                density = _density(total_mass, lattice["volume"])

            # Energy / band gap from info
            energy = None
            for key in ("energy", "Energy", "total_energy", "free_energy"):
                if key in info:
                    try:
                        energy = float(info[key]) / n_atoms  # per atom
                    except Exception:
                        pass
                    break

            band_gap = None
            for key in ("band_gap", "bandgap", "gap", "Egap"):
                if key in info:
                    try:
                        band_gap = float(info[key])
                    except Exception:
                        pass
                    break

            # Name: use config key, filename, or formula
            name = info.get("config_type", info.get("name", stem))
            if frame_idx > 0:
                name = f"{name} (frame {frame_idx})"

            doc = {
                "formula": formula,
                "name": name,
                "crystal_system": crystal_system,
                "space_group": info.get("spacegroup", info.get("space_group", "Unknown")),
                "space_group_number": None,
                "density": density,
                "band_gap": band_gap,
                "formation_energy": energy,
                "lattice": lattice,
                "sites": sites,
                "elements": elements,
                "nsites": len(sites),
                "description": f"Imported from {filename}. Crystal system: {crystal_system}.",
                "ai_summary": None,
                "cif_path": filename,
                "cif_content": None,
                "tags": [crystal_system, "extxyz"] + [el.lower() for el in elements[:3]],
                "properties": {k: v for k, v in info.items()
                               if k not in ("Lattice", "Properties")},
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
            }
            results.append(doc)
            i += 2 + n_atoms
            frame_idx += 1

        except Exception as e:
            logger.warning(f"Frame {frame_idx} in {filepath} failed: {e}")
            i += 1
            frame_idx += 1

    return results


def scan_extxyz_folder(folder: str) -> List[Dict[str, Any]]:
    """Scan folder for .xyz and .extxyz files and parse all frames."""
    all_docs = []
    if not os.path.isdir(folder):
        return all_docs

    files = [f for f in os.listdir(folder)
             if f.lower().endswith((".xyz", ".extxyz"))]
    logger.info(f"Found {len(files)} ExtXYZ files in {folder}")

    for fname in files:
        path = os.path.join(folder, fname)
        docs = parse_extxyz_file(path)
        logger.info(f"  {fname}: {len(docs)} frames parsed")
        all_docs.extend(docs)

    return all_docs
