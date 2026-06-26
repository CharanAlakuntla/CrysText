"""
Ingest ExtXYZ files into MongoDB with smart sampling.
Handles large files (100k+ frames) by sampling unique compositions.

Run: python ingest_extxyz.py
     python ingest_extxyz.py --max-per-file 500 --folder ../dataset/cif_files
"""
import asyncio, sys, os, argparse, math, re
from datetime import datetime
from collections import defaultdict
sys.path.insert(0, os.path.dirname(__file__))
from motor.motor_asyncio import AsyncIOMotorClient
from app.config import settings
from app.ai_service import generate_material_summary
import logging

logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")
logger = logging.getLogger(__name__)

ATOMIC_MASS = {
    "H":1.008,"Li":6.941,"Be":9.012,"B":10.811,"C":12.011,"N":14.007,
    "O":15.999,"F":18.998,"Na":22.990,"Mg":24.305,"Al":26.982,"Si":28.086,
    "P":30.974,"S":32.065,"Cl":35.453,"K":39.098,"Ca":40.078,"Sc":44.956,
    "Ti":47.867,"V":50.942,"Cr":51.996,"Mn":54.938,"Fe":55.845,"Co":58.933,
    "Ni":58.693,"Cu":63.546,"Zn":65.380,"Ga":69.723,"Ge":72.640,"As":74.922,
    "Se":78.960,"Br":79.904,"Rb":85.468,"Sr":87.620,"Y":88.906,"Zr":91.224,
    "Nb":92.906,"Mo":95.960,"Ru":101.07,"Rh":102.91,"Pd":106.42,"Ag":107.87,
    "Cd":112.41,"In":114.82,"Sn":118.71,"Sb":121.76,"Te":127.60,"Cs":132.91,
    "Ba":137.33,"La":138.91,"Hf":178.49,"Ta":180.95,"W":183.84,"Re":186.21,
    "Os":190.23,"Ir":192.22,"Pt":195.08,"Au":196.97,"Hg":200.59,"Pb":207.20,
    "Bi":208.98,"U":238.03,
}


def _parse_info(line):
    info = {}
    for m in re.finditer(r'(\w+)\s*=\s*"([^"]+)"|(\w+)\s*=\s*(\S+)', line):
        if m.group(1):
            info[m.group(1)] = m.group(2)
        else:
            info[m.group(3)] = m.group(4)
    return info


def _lattice_params(s):
    try:
        v = [float(x) for x in s.split()]
        if len(v) != 9: return None
        a_v, b_v, c_v = v[0:3], v[3:6], v[6:9]
        def n(x): return math.sqrt(sum(i*i for i in x))
        def d(u,w): return sum(u[i]*w[i] for i in range(3))
        a,b,c = n(a_v),n(b_v),n(c_v)
        al = math.degrees(math.acos(max(-1,min(1,d(b_v,c_v)/(b*c)))))
        be = math.degrees(math.acos(max(-1,min(1,d(a_v,c_v)/(a*c)))))
        ga = math.degrees(math.acos(max(-1,min(1,d(a_v,b_v)/(a*b)))))
        vol = abs(a_v[0]*(b_v[1]*c_v[2]-b_v[2]*c_v[1])
                 -a_v[1]*(b_v[0]*c_v[2]-b_v[2]*c_v[0])
                 +a_v[2]*(b_v[0]*c_v[1]-b_v[1]*c_v[0]))
        return {"a":round(a,5),"b":round(b,5),"c":round(c,5),
                "alpha":round(al,3),"beta":round(be,3),"gamma":round(ga,3),
                "volume":round(vol,4),"_v":[a_v,b_v,c_v]}
    except: return None


def _frac(cart, vecs):
    """Convert Cartesian to fractional using matrix inversion."""
    try:
        import numpy as np
        # vecs = [a_vec, b_vec, c_vec] as rows → matrix M where M @ frac = cart
        M = np.array(vecs).T  # columns are lattice vectors
        frac = np.linalg.solve(M, np.array(cart))
        # Wrap to [0,1)
        frac = frac % 1.0
        return [round(float(f), 5) for f in frac]
    except Exception:
        # Fallback: simple normalization if numpy unavailable
        try:
            a, b, c = [sum(v[i]**2 for i in range(3))**0.5 for v in vecs]
            return [round(cart[0]/a % 1.0, 5),
                    round(cart[1]/b % 1.0, 5),
                    round(cart[2]/c % 1.0, 5)]
        except:
            return [0.0, 0.0, 0.0]


def _crystal_system(lat):
    a,b,c = lat["a"],lat["b"],lat["c"]
    al,be,ga = lat["alpha"],lat["beta"],lat["gamma"]
    def eq(x,y): return abs(x-y)<0.5
    def is90(x): return eq(x,90.0)
    def is120(x): return eq(x,120.0)
    if eq(a,b) and eq(b,c) and is90(al) and is90(be) and is90(ga): return "cubic"
    if eq(a,b) and is90(al) and is90(be) and is120(ga): return "hexagonal"
    if eq(a,b) and not eq(b,c) and is90(al) and is90(be) and is90(ga): return "tetragonal"
    if not eq(a,b) and not eq(b,c) and is90(al) and is90(be) and is90(ga): return "orthorhombic"
    if is90(al) and not is90(be) and is90(ga): return "monoclinic"
    return "triclinic"


def _formula(counts):
    from math import gcd
    from functools import reduce
    g = reduce(gcd, counts.values())
    return "".join(
        el if (counts[el]//g)==1 else f"{el}{counts[el]//g}"
        for el in sorted(counts)
    )


def stream_frames(filepath, max_frames=None):
    """Stream frames from ExtXYZ file without loading entire file."""
    yielded = 0
    with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
        while True:
            if max_frames and yielded >= max_frames:
                break
            line1 = f.readline()
            if not line1:
                break
            line1 = line1.strip()
            if not line1.isdigit():
                continue
            n = int(line1)
            info_line = f.readline().strip()
            atom_lines = [f.readline() for _ in range(n)]
            yield n, info_line, atom_lines
            yielded += 1


def parse_frame(n, info_line, atom_lines):
    """Parse a single frame into a document dict."""
    info = _parse_info(info_line)
    lat = _lattice_params(info.get("Lattice","")) if "Lattice" in info else None
    vecs = lat.pop("_v") if lat and "_v" in lat else None

    counts = defaultdict(int)
    sites = []
    for aline in atom_lines:
        parts = aline.split()
        if len(parts) < 4: continue
        el = parts[0].capitalize()
        try:
            cx,cy,cz = float(parts[1]),float(parts[2]),float(parts[3])
        except: continue
        counts[el] += 1
        label = f"{el}{counts[el]}"
        fx,fy,fz = _frac([cx,cy,cz],vecs) if vecs else (cx,cy,cz)
        sites.append({"label":label,"element":el,
                      "x":fx,"y":fy,"z":fz,"occupancy":1.0})

    if not sites: return None

    formula = _formula(dict(counts))
    elements = sorted(counts.keys())
    cs = _crystal_system(lat) if lat else "unknown"

    density = None
    if lat and lat.get("volume",0) > 0:
        mass = sum(ATOMIC_MASS.get(el,50)*cnt for el,cnt in counts.items())
        density = round(mass / lat["volume"] * 1.66054, 4)

    energy = None
    for k in ("energy","Energy","total_energy","free_energy"):
        if k in info:
            try: energy = float(info[k]) / n; break
            except: pass

    bg = None
    for k in ("band_gap","bandgap","gap","Egap"):
        if k in info:
            try: bg = float(info[k]); break
            except: pass

    # Build a readable name from metadata
    config = info.get("config_type","")
    names_raw = info.get("names","")
    method = info.get("method","DFT")
    name_parts = [formula]
    if config and config not in ("disordered","default"):
        name_parts.append(config)
    name = " — ".join(name_parts)

    return {
        "formula": formula,
        "name": name,
        "crystal_system": cs,
        "space_group": info.get("spacegroup","Unknown"),
        "space_group_number": None,
        "density": density,
        "band_gap": bg,
        "formation_energy": energy,
        "lattice": lat,
        "sites": sites,
        "elements": elements,
        "nsites": len(sites),
        "description": (f"{formula} structure computed with {method}. "
                        f"{cs.capitalize()} crystal system, {len(sites)} atoms in unit cell."),
        "ai_summary": None,
        "cif_path": None,
        "cif_content": None,
        "tags": [cs, "extxyz", method.lower()] + [el.lower() for el in elements[:3]],
        "properties": {k:v for k,v in info.items()
                       if k not in ("Lattice","Properties","names")},
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    }


async def ingest_file(col, filepath, max_frames, seen_formulas):
    fname = os.path.basename(filepath)
    logger.info(f"Processing {fname} ...")

    inserted = updated = skipped = 0
    formula_count = defaultdict(int)

    for n, info_line, atom_lines in stream_frames(filepath, max_frames):
        doc = parse_frame(n, info_line, atom_lines)
        if not doc:
            skipped += 1
            continue

        base_formula = doc["formula"]
        formula_count[base_formula] += 1

        # Only keep first occurrence per formula per file
        # (avoids thousands of duplicates of the same composition)
        if base_formula in seen_formulas:
            continue
        seen_formulas.add(base_formula)

        try:
            result = await col.update_one(
                {"formula": doc["formula"]},
                {"$set": doc},
                upsert=True
            )
            if result.upserted_id:
                inserted += 1
            else:
                updated += 1
        except Exception as e:
            logger.warning(f"  Insert failed for {doc['formula']}: {e}")
            skipped += 1

    logger.info(f"  {fname}: inserted={inserted} updated={updated} skipped={skipped}")
    return inserted, updated


async def main(folder, max_per_file, total_target):
    client = AsyncIOMotorClient(settings.mongodb_url)
    db = client[settings.mongodb_db]
    col = db["materials"]

    files = [os.path.join(folder,f) for f in sorted(os.listdir(folder))
             if f.lower().endswith((".xyz",".extxyz"))]

    if not files:
        logger.error(f"No .xyz or .extxyz files found in {folder}")
        client.close()
        return

    logger.info(f"Found {len(files)} ExtXYZ files")
    logger.info(f"Max frames per file: {max_per_file} | Target unique formulas: {total_target}")

    seen_formulas = set()
    total_inserted = 0

    for fpath in files:
        if total_inserted >= total_target:
            logger.info(f"Reached target of {total_target} materials.")
            break
        ins, _ = await ingest_file(col, fpath, max_per_file, seen_formulas)
        total_inserted += ins

    total_in_db = await col.count_documents({})
    logger.info(f"\n{'='*50}")
    logger.info(f"New materials inserted: {total_inserted}")
    logger.info(f"Total materials in DB:  {total_in_db}")
    logger.info(f"Unique formulas seen:   {len(seen_formulas)}")
    client.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--folder", default=os.path.abspath(
        os.path.join(os.path.dirname(__file__), "../dataset/cif_files")))
    parser.add_argument("--max-per-file", type=int, default=50000,
                        help="Max frames to scan per file")
    parser.add_argument("--target", type=int, default=5000,
                        help="Target number of unique formulas to insert")
    args = parser.parse_args()
    asyncio.run(main(args.folder, args.max_per_file, args.target))
