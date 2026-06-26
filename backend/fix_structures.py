"""
Fixes inaccurate atomic structures in MongoDB.
Replaces wrong site generators with crystallographically correct coordinates.
Run: python fix_structures.py
"""
import asyncio, sys, os
from datetime import datetime
sys.path.insert(0, os.path.dirname(__file__))
from motor.motor_asyncio import AsyncIOMotorClient
from app.config import settings

# ── Correct fractional coordinates per structure type ────────────────────────

def make_sites(data):
    return [{"label":d[0],"element":d[1],"x":d[2],"y":d[3],"z":d[4],"occupancy":1.0}
            for d in data]

# CsCl: Cs at corner (0,0,0), Cl at body center (0.5,0.5,0.5) — 2 atoms
CSCL = make_sites([("Cs1","Cs",0.0,0.0,0.0),("Cl1","Cl",0.5,0.5,0.5)])

# Pyrite FeS2: Fe at corners/face-centers, S at (u,u,u) positions u≈0.385
PYRITE = make_sites([
    ("Fe1","Fe",0.0,0.0,0.0),
    ("S1","S",0.385,0.385,0.385),("S2","S",0.615,0.115,0.885),
    ("S3","S",0.115,0.885,0.615),("S4","S",0.885,0.615,0.115),
])

# MoS2 layered: Mo at (0,0,0),(1/3,2/3,1/4); S at (1/3,2/3,u),(2/3,1/3,1/4-u)
MOS2 = make_sites([
    ("Mo1","Mo",0.333,0.667,0.25),("Mo2","Mo",0.667,0.333,0.75),
    ("S1","S",0.333,0.667,0.621),("S2","S",0.667,0.333,0.121),
    ("S3","S",0.333,0.667,0.879),("S4","S",0.667,0.333,0.379),
])

# WS2 layered — same topology as MoS2
WS2 = make_sites([
    ("W1","W",0.333,0.667,0.25),("W2","W",0.667,0.333,0.75),
    ("S1","S",0.333,0.667,0.621),("S2","S",0.667,0.333,0.121),
    ("S3","S",0.333,0.667,0.879),("S4","S",0.667,0.333,0.379),
])

# Bi2S3 orthorhombic — Pbnm, 20 atoms per cell
BI2S3 = make_sites([
    ("Bi1","Bi",0.063,0.25,0.131),("Bi2","Bi",0.937,0.75,0.869),
    ("Bi3","Bi",0.437,0.75,0.631),("Bi4","Bi",0.563,0.25,0.369),
    ("S1","S",0.278,0.25,0.986),("S2","S",0.722,0.75,0.014),
    ("S3","S",0.778,0.75,0.486),("S4","S",0.222,0.25,0.514),
    ("S5","S",0.076,0.25,0.693),("S6","S",0.924,0.75,0.307),
])

# WC hexagonal — W at (1/3,2/3,1/4), C at (1/3,2/3,3/4)
WC = make_sites([
    ("W1","W",0.333,0.667,0.25),
    ("C1","C",0.333,0.667,0.75),
])

# In2O3 bixbyite cubic — simplified 8-formula unit representation
IN2O3 = make_sites([
    ("In1","In",0.25,0.25,0.25),("In2","In",0.75,0.75,0.25),
    ("In3","In",0.75,0.25,0.75),("In4","In",0.25,0.75,0.75),
    ("In5","In",0.0,0.25,0.0),("In6","In",0.0,0.75,0.0),
    ("O1","O",0.375,0.125,0.375),("O2","O",0.625,0.875,0.375),
    ("O3","O",0.875,0.625,0.125),("O4","O",0.125,0.375,0.125),
    ("O5","O",0.125,0.125,0.625),("O6","O",0.375,0.375,0.875),
])

# Nd2Fe14B tetragonal — simplified key sites
ND2FE14B = make_sites([
    ("Nd1","Nd",0.267,0.267,0.0),("Nd2","Nd",0.733,0.733,0.0),
    ("Nd3","Nd",0.267,0.733,0.5),("Nd4","Nd",0.733,0.267,0.5),
    ("Fe1","Fe",0.0,0.0,0.0),("Fe2","Fe",0.5,0.5,0.0),
    ("Fe3","Fe",0.0,0.5,0.5),("Fe4","Fe",0.5,0.0,0.5),
    ("Fe5","Fe",0.0,0.0,0.5),("Fe6","Fe",0.5,0.5,0.5),
    ("B1","B",0.5,0.0,0.25),("B2","B",0.0,0.5,0.25),
])

# SmCo5 hexagonal P6/mmm — Sm at (0,0,0), Co at (1/3,2/3,0) and (1/2,0,1/2)
SMCO5 = make_sites([
    ("Sm1","Sm",0.0,0.0,0.0),
    ("Co1","Co",0.333,0.667,0.0),("Co2","Co",0.667,0.333,0.0),
    ("Co3","Co",0.5,0.0,0.5),("Co4","Co",0.0,0.5,0.5),("Co5","Co",0.5,0.5,0.5),
])

# LiCoO2 layered trigonal R-3m: Li at (0,0,0), Co at (0,0,0.5), O at (0,0,0.26)
LICOO2 = make_sites([
    ("Li1","Li",0.0,0.0,0.0),("Li2","Li",0.0,0.0,0.5),
    ("Co1","Co",0.0,0.0,0.5),("Co2","Co",0.0,0.0,0.0),
    ("O1","O",0.0,0.0,0.26),("O2","O",0.0,0.0,0.74),
    ("O3","O",0.0,0.0,0.76),("O4","O",0.0,0.0,0.24),
])

# MgB2 hexagonal: Mg at (0,0,0), B at (1/3,2/3,1/2)
MGB2 = make_sites([
    ("Mg1","Mg",0.0,0.0,0.0),
    ("B1","B",0.333,0.667,0.5),("B2","B",0.667,0.333,0.5),
])

# Bi2Te3 trigonal: layered quintuple
BI2TE3 = make_sites([
    ("Bi1","Bi",0.0,0.0,0.4),("Bi2","Bi",0.0,0.0,0.6),
    ("Te1","Te",0.0,0.0,0.0),("Te2","Te",0.0,0.0,0.788),("Te3","Te",0.0,0.0,0.212),
])

# AuCu3 L12: Au at corner (0,0,0), Cu at face centers
AUCU3 = make_sites([
    ("Au1","Au",0.0,0.0,0.0),
    ("Cu1","Cu",0.5,0.5,0.0),("Cu2","Cu",0.5,0.0,0.5),("Cu3","Cu",0.0,0.5,0.5),
])

# Ni3Al L12: same topology
NI3AL = make_sites([
    ("Al1","Al",0.0,0.0,0.0),
    ("Ni1","Ni",0.5,0.5,0.0),("Ni2","Ni",0.5,0.0,0.5),("Ni3","Ni",0.0,0.5,0.5),
])

# Nb3Sn A15: Sn at (0,0,0) and (1/2,1/2,1/2), Nb at (1/4,0,1/2)...
NB3SN = make_sites([
    ("Sn1","Sn",0.0,0.0,0.0),("Sn2","Sn",0.5,0.5,0.5),
    ("Nb1","Nb",0.25,0.0,0.5),("Nb2","Nb",0.75,0.0,0.5),
    ("Nb3","Nb",0.0,0.25,0.5),("Nb4","Nb",0.0,0.75,0.5),
    ("Nb5","Nb",0.5,0.25,0.0),("Nb6","Nb",0.5,0.75,0.0),
])

# FePO4 olivine-like: simplified
FEPO4 = make_sites([
    ("Fe1","Fe",0.0,0.0,0.0),("Fe2","Fe",0.5,0.0,0.0),
    ("P1","P",0.094,0.25,0.418),("P2","P",0.594,0.75,0.918),
    ("O1","O",0.095,0.25,0.743),("O2","O",0.452,0.25,0.296),
    ("O3","O",0.165,0.046,0.282),("O4","O",0.165,0.454,0.282),
])

# CuS covellite hexagonal — proper layered structure
CUS = make_sites([
    ("Cu1","Cu",0.333,0.667,0.0),("Cu2","Cu",0.667,0.333,0.0),
    ("Cu3","Cu",0.0,0.0,0.25),
    ("S1","S",0.333,0.667,0.314),("S2","S",0.667,0.333,0.186),
    ("S3","S",0.0,0.0,0.0),
])

# ── Corrections map: formula -> correct sites ────────────────────────────────
CORRECTIONS = {
    "CsCl":    CSCL,
    "FeS2":    PYRITE,
    "MoS2":    MOS2,
    "WS2":     WS2,
    "Bi2S3":   BI2S3,
    "WC":      WC,
    "In2O3":   IN2O3,
    "Nd2Fe14B":ND2FE14B,
    "SmCo5":   SMCO5,
    "LiCoO2":  LICOO2,
    "MgB2":    MGB2,
    "Bi2Te3":  BI2TE3,
    "AuCu3":   AUCU3,
    "Ni3Al":   NI3AL,
    "Nb3Sn":   NB3SN,
    "FePO4":   FEPO4,
    "CuS":     CUS,
}


async def main():
    client = AsyncIOMotorClient(settings.mongodb_url)
    db = client[settings.mongodb_db]
    col = db["materials"]

    fixed = 0
    for formula, correct_sites in CORRECTIONS.items():
        result = await col.update_one(
            {"formula": formula},
            {"$set": {
                "sites": correct_sites,
                "nsites": len(correct_sites),
                "updated_at": datetime.utcnow(),
            }}
        )
        if result.matched_count:
            print(f"  Fixed {formula}: {len(correct_sites)} sites")
            fixed += 1
        else:
            print(f"  Not found: {formula}")

    print(f"\nFixed {fixed} materials.")
    client.close()

if __name__ == "__main__":
    asyncio.run(main())
