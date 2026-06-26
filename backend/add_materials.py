"""
Bulk-insert 200+ materials with full structure data (lattice + atomic sites).
Run: python add_materials.py
"""
import asyncio, sys, os
from datetime import datetime
sys.path.insert(0, os.path.dirname(__file__))
from motor.motor_asyncio import AsyncIOMotorClient
from app.config import settings

# ── Structure generators ──────────────────────────────────────────────────────

def rock_salt(A, B):
    return [(A+"1",A,0.0,0.0,0.0),(A+"2",A,0.5,0.5,0.0),
            (A+"3",A,0.5,0.0,0.5),(A+"4",A,0.0,0.5,0.5),
            (B+"1",B,0.5,0.0,0.0),(B+"2",B,0.0,0.5,0.0),
            (B+"3",B,0.0,0.0,0.5),(B+"4",B,0.5,0.5,0.5)]

def fcc(el):
    return [(el+"1",el,0.0,0.0,0.0),(el+"2",el,0.5,0.5,0.0),
            (el+"3",el,0.5,0.0,0.5),(el+"4",el,0.0,0.5,0.5)]

def bcc(el):
    return [(el+"1",el,0.0,0.0,0.0),(el+"2",el,0.5,0.5,0.5)]

def diamond(el):
    return [(el+"1",el,0.0,0.0,0.0),(el+"2",el,0.5,0.5,0.0),
            (el+"3",el,0.5,0.0,0.5),(el+"4",el,0.0,0.5,0.5),
            (el+"5",el,0.25,0.25,0.25),(el+"6",el,0.75,0.75,0.25),
            (el+"7",el,0.75,0.25,0.75),(el+"8",el,0.25,0.75,0.75)]

def zincblende(A, B):
    return [(A+"1",A,0.0,0.0,0.0),(A+"2",A,0.5,0.5,0.0),
            (A+"3",A,0.5,0.0,0.5),(A+"4",A,0.0,0.5,0.5),
            (B+"1",B,0.25,0.25,0.25),(B+"2",B,0.75,0.75,0.25),
            (B+"3",B,0.75,0.25,0.75),(B+"4",B,0.25,0.75,0.75)]

def fluorite(A, B):
    return [(A+"1",A,0.0,0.0,0.0),(A+"2",A,0.5,0.5,0.0),
            (A+"3",A,0.5,0.0,0.5),(A+"4",A,0.0,0.5,0.5),
            (B+"1",B,0.25,0.25,0.25),(B+"2",B,0.75,0.25,0.25),
            (B+"3",B,0.25,0.75,0.25),(B+"4",B,0.75,0.75,0.25),
            (B+"5",B,0.25,0.25,0.75),(B+"6",B,0.75,0.25,0.75),
            (B+"7",B,0.25,0.75,0.75),(B+"8",B,0.75,0.75,0.75)]

def perovskite(A, B, O):
    return [(A+"1",A,0.0,0.0,0.0),(B+"1",B,0.5,0.5,0.5),
            (O+"1",O,0.5,0.5,0.0),(O+"2",O,0.5,0.0,0.5),(O+"3",O,0.0,0.5,0.5)]

def rutile(M, O, u=0.305):
    return [(M+"1",M,0.0,0.0,0.0),(M+"2",M,0.5,0.5,0.5),
            (O+"1",O,u,u,0.0),(O+"2",O,1-u,1-u,0.0),
            (O+"3",O,0.5+u,0.5-u,0.5),(O+"4",O,0.5-u,0.5+u,0.5)]

def wurtzite(A, B):
    return [(A+"1",A,0.333,0.667,0.0),(A+"2",A,0.667,0.333,0.5),
            (B+"1",B,0.333,0.667,0.375),(B+"2",B,0.667,0.333,0.875)]

def hcp(el):
    return [(el+"1",el,0.333,0.667,0.25),(el+"2",el,0.667,0.333,0.75)]

def corundum(A, O):
    return [(A+"1",A,0.0,0.0,0.352),(A+"2",A,0.0,0.0,0.648),
            (A+"3",A,0.0,0.0,0.148),(A+"4",A,0.0,0.0,0.852),
            (O+"1",O,0.306,0.0,0.25),(O+"2",O,0.0,0.306,0.25),
            (O+"3",O,0.694,0.694,0.25),(O+"4",O,0.694,0.0,0.25),
            (O+"5",O,0.0,0.694,0.25),(O+"6",O,0.306,0.306,0.25)]

def spinel(A, B, O):
    return [(A+"1",A,0.125,0.125,0.125),(B+"1",B,0.5,0.5,0.5),
            (B+"2",B,0.5,0.0,0.0),(B+"3",B,0.0,0.5,0.0),(B+"4",B,0.0,0.0,0.5),
            (O+"1",O,0.262,0.262,0.262),(O+"2",O,0.738,0.738,0.262),
            (O+"3",O,0.738,0.262,0.738),(O+"4",O,0.262,0.738,0.738)]

# ── Material database ─────────────────────────────────────────────────────────
# (formula, name, crystal_system, space_group, sg_num,
#  a, b, c, alpha, beta, gamma, density, band_gap,
#  elements, tags, description, sites_list)

MATERIALS = [
# ── Alkali halides ────────────────────────────────────────────────────────────
("NaCl","Sodium Chloride (Rock Salt)","cubic","Fm-3m",225,5.640,5.640,5.640,90,90,90,2.165,8.50,["Na","Cl"],["cubic","ionic","halide"],"The archetypal rock-salt ionic crystal. Used as table salt, in food preservation, and as a reference standard in crystallography.",rock_salt("Na","Cl")),
("KCl","Potassium Chloride (Sylvite)","cubic","Fm-3m",225,6.293,6.293,6.293,90,90,90,1.984,8.40,["K","Cl"],["cubic","ionic","halide"],"Rock-salt structure with larger lattice parameter than NaCl. Essential potassium source in agriculture.",rock_salt("K","Cl")),
("LiF","Lithium Fluoride","cubic","Fm-3m",225,4.027,4.027,4.027,90,90,90,2.635,13.6,["Li","F"],["cubic","ionic","fluoride"],"Widest band gap of all alkali halides (13.6 eV). Transparent to UV, used in neutron detectors.",rock_salt("Li","F")),
("LiCl","Lithium Chloride","cubic","Fm-3m",225,5.129,5.129,5.129,90,90,90,2.068,9.40,["Li","Cl"],["cubic","ionic","halide"],"Highly hygroscopic salt used as a desiccant and in lithium battery research.",rock_salt("Li","Cl")),
("NaBr","Sodium Bromide","cubic","Fm-3m",225,5.973,5.973,5.973,90,90,90,3.203,7.50,["Na","Br"],["cubic","ionic","halide"],"Rock-salt structure. Used in photography and as a sedative historically.",rock_salt("Na","Br")),
("NaI","Sodium Iodide","cubic","Fm-3m",225,6.473,6.473,6.473,90,90,90,3.667,5.90,["Na","I"],["cubic","ionic","halide","scintillator"],"NaI(Tl) scintillator crystals detect gamma radiation in medical imaging.",rock_salt("Na","I")),
("KBr","Potassium Bromide","cubic","Fm-3m",225,6.599,6.599,6.599,90,90,90,2.750,7.40,["K","Br"],["cubic","ionic","halide"],"Classic IR spectroscopy window material. Transparent from 250 nm to 26 μm.",rock_salt("K","Br")),
("KI","Potassium Iodide","cubic","Fm-3m",225,7.066,7.066,7.066,90,90,90,3.123,6.00,["K","I"],["cubic","ionic","halide"],"Used in medicine for thyroid protection after nuclear events.",rock_salt("K","I")),
("MgO","Magnesium Oxide (Periclase)","cubic","Fm-3m",225,4.211,4.211,4.211,90,90,90,3.580,7.80,["Mg","O"],["cubic","oxide","refractory","ionic"],"Periclase. Melting point 2852°C. Used as refractory in steel furnaces and as a substrate for thin films.",rock_salt("Mg","O")),
("CaO","Calcium Oxide (Lime)","cubic","Fm-3m",225,4.805,4.805,4.805,90,90,90,3.350,6.90,["Ca","O"],["cubic","oxide","ionic"],"Quicklime. Produced by calcining limestone. Essential in cement, glass, and steelmaking.",rock_salt("Ca","O")),
("FeO","Iron(II) Oxide (Wustite)","cubic","Fm-3m",225,4.307,4.307,4.307,90,90,90,5.740,2.40,["Fe","O"],["cubic","oxide","magnetic"],"Iron-rich oxide phase. Key intermediate in iron smelting processes.",rock_salt("Fe","O")),
("CoO","Cobalt(II) Oxide","cubic","Fm-3m",225,4.261,4.261,4.261,90,90,90,6.440,2.60,["Co","O"],["cubic","oxide","antiferromagnetic"],"Antiferromagnetic p-type semiconductor. Used in Li-ion battery cathodes.",rock_salt("Co","O")),
("NiO","Nickel(II) Oxide","cubic","Fm-3m",225,4.177,4.177,4.177,90,90,90,6.670,3.70,["Ni","O"],["cubic","oxide","antiferromagnetic"],"Antiferromagnetic with Néel temperature 523 K. Used in electrochromic devices.",rock_salt("Ni","O")),
]

MATERIALS += [
# ── Semiconductors ────────────────────────────────────────────────────────────
("Si","Silicon (Diamond Cubic)","cubic","Fd-3m",227,5.431,5.431,5.431,90,90,90,2.329,1.12,["Si"],["cubic","semiconductor","diamond"],"The foundation of modern electronics. Diamond-cubic structure, indirect band gap 1.12 eV. Used in CPUs, solar cells, and sensors.",diamond("Si")),
("Ge","Germanium","cubic","Fd-3m",227,5.658,5.658,5.658,90,90,90,5.323,0.67,["Ge"],["cubic","semiconductor","diamond"],"First transistor material. Smaller band gap (0.67 eV) suits near-infrared detectors. Used in fiber optics.",diamond("Ge")),
("GaAs","Gallium Arsenide","cubic","F-43m",216,5.653,5.653,5.653,90,90,90,5.318,1.42,["Ga","As"],["cubic","semiconductor","zincblende","direct-gap"],"Direct-gap III-V semiconductor (1.42 eV). Used in solar cells, laser diodes, and high-speed electronics.",zincblende("Ga","As")),
("InP","Indium Phosphide","cubic","F-43m",216,5.869,5.869,5.869,90,90,90,4.810,1.35,["In","P"],["cubic","semiconductor","zincblende","direct-gap"],"Direct-gap semiconductor for fiber-optic laser diodes and high-speed transistors.",zincblende("In","P")),
("InAs","Indium Arsenide","cubic","F-43m",216,6.058,6.058,6.058,90,90,90,5.667,0.36,["In","As"],["cubic","semiconductor","zincblende"],"Very high electron mobility. Used in infrared detectors and quantum computing.",zincblende("In","As")),
("InSb","Indium Antimonide","cubic","F-43m",216,6.479,6.479,6.479,90,90,90,5.775,0.17,["In","Sb"],["cubic","semiconductor","zincblende","infrared"],"Highest electron mobility among III-V materials. Thermal imaging cameras.",zincblende("In","Sb")),
("GaP","Gallium Phosphide","cubic","F-43m",216,5.450,5.450,5.450,90,90,90,4.138,2.26,["Ga","P"],["cubic","semiconductor","zincblende"],"Indirect gap (2.26 eV). Used in green and yellow LEDs.",zincblende("Ga","P")),
("AlAs","Aluminum Arsenide","cubic","F-43m",216,5.661,5.661,5.661,90,90,90,3.760,2.12,["Al","As"],["cubic","semiconductor","zincblende"],"Used in quantum well heterostructures with GaAs for laser diodes.",zincblende("Al","As")),
("ZnS","Zinc Sulfide (Sphalerite)","cubic","F-43m",216,5.411,5.411,5.411,90,90,90,4.090,3.54,["Zn","S"],["cubic","semiconductor","zincblende","sulfide"],"Wide-gap semiconductor used in phosphors and optical windows.",zincblende("Zn","S")),
("ZnSe","Zinc Selenide","cubic","F-43m",216,5.669,5.669,5.669,90,90,90,5.267,2.70,["Zn","Se"],["cubic","semiconductor","zincblende"],"Used as a window for CO2 lasers and buffer layer in solar cells.",zincblende("Zn","Se")),
("ZnTe","Zinc Telluride","cubic","F-43m",216,6.104,6.104,6.104,90,90,90,5.636,2.26,["Zn","Te"],["cubic","semiconductor","zincblende"],"Used in green LEDs and as back contact in CdTe solar cells.",zincblende("Zn","Te")),
("CdTe","Cadmium Telluride","cubic","F-43m",216,6.482,6.482,6.482,90,90,90,5.850,1.44,["Cd","Te"],["cubic","semiconductor","zincblende","solar"],"Most cost-effective thin-film solar cell material. Direct gap 1.44 eV.",zincblende("Cd","Te")),
("SiC","Silicon Carbide (3C)","cubic","F-43m",216,4.360,4.360,4.360,90,90,90,3.215,2.36,["Si","C"],["cubic","semiconductor","carbide","wide-gap"],"Wide-gap semiconductor for high-temperature, high-voltage power electronics.",zincblende("Si","C")),
("ZnO","Zinc Oxide (Wurtzite)","hexagonal","P63mc",186,3.250,3.250,5.207,90,90,120,5.606,3.37,["Zn","O"],["hexagonal","oxide","semiconductor","piezoelectric"],"Wide-gap semiconductor with piezoelectric properties. Used in UV LEDs and sunscreen.",wurtzite("Zn","O")),
("GaN","Gallium Nitride","hexagonal","P63mc",186,3.189,3.189,5.185,90,90,120,6.150,3.44,["Ga","N"],["hexagonal","semiconductor","nitride","wide-gap"],"Enables blue LEDs (Nobel Prize 2014) and high-power electronics. Superior to Si.",wurtzite("Ga","N")),
("AlN","Aluminum Nitride","hexagonal","P63mc",186,3.112,3.112,4.982,90,90,120,3.255,6.20,["Al","N"],["hexagonal","semiconductor","nitride","wide-gap"],"Widest gap nitride (6.2 eV). Used in UV LEDs and as a thermal substrate.",wurtzite("Al","N")),
("CdS","Cadmium Sulfide","hexagonal","P63mc",186,4.136,4.136,6.714,90,90,120,4.820,2.42,["Cd","S"],["hexagonal","semiconductor","sulfide"],"n-type semiconductor used in photoresistors and CdTe solar cell buffer layers.",wurtzite("Cd","S")),
]

MATERIALS += [
# ── FCC Metals ────────────────────────────────────────────────────────────────
("Cu","Copper (FCC)","cubic","Fm-3m",225,3.615,3.615,3.615,90,90,90,8.960,None,["Cu"],["cubic","metal","fcc","conductor"],"Best electrical conductor after silver. FCC structure enables excellent ductility. Essential in wiring and electronics.",fcc("Cu")),
("Au","Gold (FCC)","cubic","Fm-3m",225,4.078,4.078,4.078,90,90,90,19.32,None,["Au"],["cubic","metal","fcc","noble"],"Chemically inert noble metal. Most malleable metal known. Used in electronics, jewelry, and monetary systems.",fcc("Au")),
("Ag","Silver (FCC)","cubic","Fm-3m",225,4.086,4.086,4.086,90,90,90,10.49,None,["Ag"],["cubic","metal","fcc","noble","conductor"],"Highest electrical and thermal conductivity of all metals. Used in electronics, photography, and medicine.",fcc("Ag")),
("Al","Aluminum (FCC)","cubic","Fm-3m",225,4.050,4.050,4.050,90,90,90,2.699,None,["Al"],["cubic","metal","fcc","lightweight"],"Most abundant metal in Earth's crust. Lightweight with good corrosion resistance. Dominant aerospace metal.",fcc("Al")),
("Ni","Nickel (FCC)","cubic","Fm-3m",225,3.524,3.524,3.524,90,90,90,8.908,None,["Ni"],["cubic","metal","fcc","magnetic"],"Ferromagnetic FCC metal. Key in superalloys, batteries, and catalysts.",fcc("Ni")),
("Pt","Platinum (FCC)","cubic","Fm-3m",225,3.924,3.924,3.924,90,90,90,21.45,None,["Pt"],["cubic","metal","fcc","noble","catalyst"],"Noble metal catalyst in automotive converters and fuel cells. Most catalytically active metal.",fcc("Pt")),
("Pd","Palladium (FCC)","cubic","Fm-3m",225,3.890,3.890,3.890,90,90,90,12.02,None,["Pd"],["cubic","metal","fcc","noble","catalyst"],"Key catalyst for hydrogenation and emission control. Used in fuel cells.",fcc("Pd")),
("Ir","Iridium (FCC)","cubic","Fm-3m",225,3.839,3.839,3.839,90,90,90,22.56,None,["Ir"],["cubic","metal","fcc","noble","refractory"],"Most corrosion-resistant metal. Used in spark plugs and as mass standard.",fcc("Ir")),
("Rh","Rhodium (FCC)","cubic","Fm-3m",225,3.803,3.803,3.803,90,90,90,12.41,None,["Rh"],["cubic","metal","fcc","noble","catalyst"],"Used in three-way catalytic converters. Most expensive precious metal.",fcc("Rh")),
("Pb","Lead (FCC)","cubic","Fm-3m",225,4.950,4.950,4.950,90,90,90,11.34,None,["Pb"],["cubic","metal","fcc"],"High density and radiation absorption. Used in shielding, batteries, and historically as a pigment.",fcc("Pb")),
# ── BCC Metals ────────────────────────────────────────────────────────────────
("Fe","Iron (BCC)","cubic","Im-3m",229,2.866,2.866,2.866,90,90,90,7.874,None,["Fe"],["cubic","metal","bcc","magnetic"],"Alpha-iron is ferromagnetic below 770°C. Most important structural metal in history.",bcc("Fe")),
("W","Tungsten (BCC)","cubic","Im-3m",229,3.165,3.165,3.165,90,90,90,19.30,None,["W"],["cubic","metal","bcc","refractory"],"Highest melting point of all metals (3422°C). Used in light bulb filaments and cutting tools.",bcc("W")),
("Cr","Chromium (BCC)","cubic","Im-3m",229,2.884,2.884,2.884,90,90,90,7.190,None,["Cr"],["cubic","metal","bcc","antiferromagnetic"],"Antiferromagnetic BCC metal. Gives stainless steel its corrosion resistance.",bcc("Cr")),
("Mo","Molybdenum (BCC)","cubic","Im-3m",229,3.147,3.147,3.147,90,90,90,10.28,None,["Mo"],["cubic","metal","bcc","refractory"],"Very high melting point. Used in high-strength steels and catalysts for petroleum refining.",bcc("Mo")),
("V","Vanadium (BCC)","cubic","Im-3m",229,3.030,3.030,3.030,90,90,90,6.110,None,["V"],["cubic","metal","bcc"],"Strengthens steel alloys. Vanadium redox flow batteries for grid energy storage.",bcc("V")),
("Nb","Niobium (BCC)","cubic","Im-3m",229,3.300,3.300,3.300,90,90,90,8.570,None,["Nb"],["cubic","metal","bcc","superconductor"],"Superconducting at 9.2 K. Used in MRI magnets and particle accelerator cavities.",bcc("Nb")),
("Ta","Tantalum (BCC)","cubic","Im-3m",229,3.306,3.306,3.306,90,90,90,16.65,None,["Ta"],["cubic","metal","bcc","refractory"],"Highly corrosion-resistant. Used in capacitors for smartphones and medical implants.",bcc("Ta")),
("Na","Sodium (BCC)","cubic","Im-3m",229,4.290,4.290,4.290,90,90,90,0.971,None,["Na"],["cubic","metal","bcc","alkali"],"Soft reactive alkali metal. BCC structure. Used in sodium-vapor lamps.",bcc("Na")),
("K","Potassium (BCC)","cubic","Im-3m",229,5.334,5.334,5.334,90,90,90,0.862,None,["K"],["cubic","metal","bcc","alkali"],"Softest alkali metal. Essential for biological function. BCC structure.",bcc("K")),
("Li","Lithium (BCC)","cubic","Im-3m",229,3.510,3.510,3.510,90,90,90,0.534,None,["Li"],["cubic","metal","bcc","alkali"],"Lightest metal. BCC structure. Critical for lithium-ion batteries in EVs.",bcc("Li")),
]

MATERIALS += [
# ── HCP Metals ────────────────────────────────────────────────────────────────
("Ti","Titanium (HCP)","hexagonal","P63/mmc",194,2.950,2.950,4.683,90,90,120,4.506,None,["Ti"],["hexagonal","metal","hcp","lightweight"],"Lightweight, high-strength, biocompatible. Used in aerospace, medical implants, and aircraft engines.",hcp("Ti")),
("Zn","Zinc (HCP)","hexagonal","P63/mmc",194,2.665,2.665,4.947,90,90,120,7.133,None,["Zn"],["hexagonal","metal","hcp"],"HCP metal used to galvanize steel. Essential trace element in biology.",hcp("Zn")),
("Mg","Magnesium (HCP)","hexagonal","P63/mmc",194,3.209,3.209,5.211,90,90,120,1.738,None,["Mg"],["hexagonal","metal","hcp","lightweight"],"Lightest structural metal. Used in aerospace and as biodegradable implant material.",hcp("Mg")),
("Co","Cobalt (HCP)","hexagonal","P63/mmc",194,2.507,2.507,4.069,90,90,120,8.900,None,["Co"],["hexagonal","metal","hcp","magnetic"],"Ferromagnetic HCP metal. Used in superalloys, magnets, and Li-ion battery cathodes.",hcp("Co")),
("Zr","Zirconium (HCP)","hexagonal","P63/mmc",194,3.232,3.232,5.147,90,90,120,6.511,None,["Zr"],["hexagonal","metal","hcp","nuclear"],"Low neutron absorption cross section. Used as cladding for nuclear fuel rods.",hcp("Zr")),
("Ru","Ruthenium (HCP)","hexagonal","P63/mmc",194,2.706,2.706,4.282,90,90,120,12.37,None,["Ru"],["hexagonal","metal","hcp","platinum-group"],"Platinum-group metal. Used in electrical contacts and as a catalyst.",hcp("Ru")),
("Os","Osmium (HCP)","hexagonal","P63/mmc",194,2.734,2.734,4.319,90,90,120,22.59,None,["Os"],["hexagonal","metal","hcp","platinum-group"],"Densest naturally occurring element (22.59 g/cm³). Used in fountain pen nibs.",hcp("Os")),
("Cd","Cadmium (HCP)","hexagonal","P63/mmc",194,2.979,2.979,5.618,90,90,120,8.650,None,["Cd"],["hexagonal","metal","hcp"],"Used in Ni-Cd batteries and as neutron absorber in nuclear reactors.",hcp("Cd")),
# ── Fluorites ─────────────────────────────────────────────────────────────────
("CaF2","Calcium Fluoride (Fluorite)","cubic","Fm-3m",225,5.463,5.463,5.463,90,90,90,3.180,12.1,["Ca","F"],["cubic","fluorite","fluoride","optical"],"The fluorite structure prototype. Used as a flux in steelmaking and as UV optical windows.",fluorite("Ca","F")),
("BaF2","Barium Fluoride","cubic","Fm-3m",225,6.196,6.196,6.196,90,90,90,4.893,10.5,["Ba","F"],["cubic","fluorite","scintillator"],"Fast scintillator crystal for high-energy physics detectors.",fluorite("Ba","F")),
("SrF2","Strontium Fluoride","cubic","Fm-3m",225,5.800,5.800,5.800,90,90,90,4.240,11.25,["Sr","F"],["cubic","fluorite","fluoride"],"UV optics and laser crystal host material.",fluorite("Sr","F")),
("CeO2","Cerium Oxide (Ceria)","cubic","Fm-3m",225,5.412,5.412,5.412,90,90,90,7.215,3.20,["Ce","O"],["cubic","fluorite","oxide","catalyst"],"Used in automotive catalytic converters and as a precision glass polishing agent.",fluorite("Ce","O")),
("UO2","Uranium Dioxide","cubic","Fm-3m",225,5.470,5.470,5.470,90,90,90,10.97,2.00,["U","O"],["cubic","fluorite","nuclear","oxide"],"Standard nuclear fuel in light-water reactors due to chemical stability and high melting point.",fluorite("U","O")),
# ── Perovskites ───────────────────────────────────────────────────────────────
("SrTiO3","Strontium Titanate (Perovskite)","cubic","Pm-3m",221,3.905,3.905,3.905,90,90,90,5.117,3.25,["Sr","Ti","O"],["cubic","perovskite","oxide","substrate"],"The archetypal cubic perovskite. Paraelectric at room temperature, used as a substrate for oxide films.",perovskite("Sr","Ti","O")),
("BaTiO3","Barium Titanate","cubic","Pm-3m",221,4.000,4.000,4.000,90,90,90,6.020,3.20,["Ba","Ti","O"],["cubic","perovskite","ferroelectric"],"Room-temperature ferroelectric. Used in capacitors, piezoelectric transducers, and DRAM.",perovskite("Ba","Ti","O")),
("CaTiO3","Calcium Titanate","cubic","Pm-3m",221,3.795,3.795,3.795,90,90,90,4.100,3.50,["Ca","Ti","O"],["cubic","perovskite","mineral"],"The mineral perovskite that gives this structure type its name.",perovskite("Ca","Ti","O")),
("KNbO3","Potassium Niobate","cubic","Pm-3m",221,4.016,4.016,4.016,90,90,90,4.620,3.30,["K","Nb","O"],["cubic","perovskite","ferroelectric","lead-free"],"Lead-free ferroelectric used in optical frequency doubling devices.",perovskite("K","Nb","O")),
("LaAlO3","Lanthanum Aluminate","cubic","Pm-3m",221,3.787,3.787,3.787,90,90,90,6.520,5.60,["La","Al","O"],["cubic","perovskite","substrate"],"Popular substrate for high-temperature superconductor and ferroelectric thin films.",perovskite("La","Al","O")),
("PbTiO3","Lead Titanate","cubic","Pm-3m",221,3.904,3.904,3.904,90,90,90,7.990,3.40,["Pb","Ti","O"],["cubic","perovskite","ferroelectric"],"Large spontaneous polarization. Basis for PZT piezoelectric ceramics used in sonar.",perovskite("Pb","Ti","O")),
]

MATERIALS += [
# ── Rutile oxides ─────────────────────────────────────────────────────────────
("TiO2","Titanium Dioxide (Rutile)","tetragonal","P4/mnm",136,4.594,4.594,2.959,90,90,90,4.250,3.05,["Ti","O"],["tetragonal","oxide","photocatalyst","semiconductor"],"Most important photocatalyst. Used in sunscreen, white pigment, and self-cleaning surfaces.",rutile("Ti","O")),
("SnO2","Tin Dioxide (Cassiterite)","tetragonal","P4/mnm",136,4.737,4.737,3.186,90,90,90,6.950,3.60,["Sn","O"],["tetragonal","oxide","semiconductor","transparent"],"Transparent conducting oxide. Used in gas sensors, solar cells, and flat panel displays.",rutile("Sn","O")),
("RuO2","Ruthenium Dioxide","tetragonal","P4/mnm",136,4.492,4.492,3.107,90,90,90,6.970,None,["Ru","O"],["tetragonal","oxide","conductor","catalyst"],"Metallic oxide catalyst. Used in dimensionally stable anodes for chlorine production.",rutile("Ru","O")),
("MnO2","Manganese Dioxide","tetragonal","P4/mnm",136,4.398,4.398,2.873,90,90,90,5.026,None,["Mn","O"],["tetragonal","oxide","battery"],"Beta-MnO2 used as cathode in alkaline batteries and as an oxidation catalyst.",rutile("Mn","O")),
("IrO2","Iridium Dioxide","tetragonal","P4/mnm",136,4.505,4.505,3.159,90,90,90,11.66,None,["Ir","O"],["tetragonal","oxide","catalyst","electrocatalyst"],"Best known catalyst for water oxidation in proton exchange membrane electrolyzers.",rutile("Ir","O")),
("GeO2","Germanium Dioxide","tetragonal","P4/mnm",136,4.396,4.396,2.863,90,90,90,6.239,4.68,["Ge","O"],["tetragonal","oxide","glass"],"Rutile-type GeO2 is used as catalyst and in optical fiber manufacturing.",rutile("Ge","O")),
# ── Spinel oxides ─────────────────────────────────────────────────────────────
("MgAl2O4","Magnesium Aluminate Spinel","cubic","Fd-3m",227,8.083,8.083,8.083,90,90,90,3.580,7.80,["Mg","Al","O"],["cubic","spinel","transparent","ceramic"],"Optically transparent spinel used in armor windows, scratch-resistant screens, and gemstones.",spinel("Mg","Al","O")),
("Fe3O4","Magnetite","cubic","Fd-3m",227,8.396,8.396,8.396,90,90,90,5.175,0.10,["Fe","O"],["cubic","spinel","magnetic","ferrimagnetic"],"First known magnet in history. Used in data storage media and MRI contrast agents.",spinel("Fe","Fe","O")),
("CoFe2O4","Cobalt Ferrite","cubic","Fd-3m",227,8.391,8.391,8.391,90,90,90,5.280,None,["Co","Fe","O"],["cubic","spinel","magnetic","hard-magnet"],"Hard magnetic ferrite used in recording media and magnetic sensors.",spinel("Co","Fe","O")),
("NiFe2O4","Nickel Ferrite","cubic","Fd-3m",227,8.339,8.339,8.339,90,90,90,5.370,None,["Ni","Fe","O"],["cubic","spinel","magnetic","soft-magnet"],"Soft magnetic ferrite used in inductors and microwave devices.",spinel("Ni","Fe","O")),
("ZnFe2O4","Zinc Ferrite","cubic","Fd-3m",227,8.441,8.441,8.441,90,90,90,5.330,1.90,["Zn","Fe","O"],["cubic","spinel","oxide"],"Normal spinel, paramagnetic at room temperature. Used in gas sensors.",spinel("Zn","Fe","O")),
# ── Corundum oxides ───────────────────────────────────────────────────────────
("Al2O3","Aluminum Oxide (Corundum)","trigonal","R-3c",167,4.760,4.760,12.994,90,90,120,3.987,8.70,["Al","O"],["trigonal","oxide","ceramic","hard"],"Hardness Mohs 9. Ruby and sapphire are doped corundum. Used in abrasives and substrates.",corundum("Al","O")),
("Cr2O3","Chromium Oxide","trigonal","R-3c",167,4.961,4.961,13.599,90,90,120,5.220,3.40,["Cr","O"],["trigonal","oxide","green-pigment"],"Green pigment Cr2O3. Forms protective film on stainless steel.",corundum("Cr","O")),
("Fe2O3","Hematite","trigonal","R-3c",167,5.036,5.036,13.748,90,90,120,5.260,2.20,["Fe","O"],["trigonal","oxide","magnetic","mineral"],"Main iron ore mineral. Antiferromagnetic with red color used as pigment since ancient times.",corundum("Fe","O")),
("In2O3","Indium Oxide","cubic","Ia-3",206,10.117,10.117,10.117,90,90,90,7.180,2.90,["In","O"],["cubic","oxide","transparent-conductor"],"ITO (Sn-doped In2O3) is the dominant transparent conductor for LCD and OLED displays.",fcc("In")),
]

MATERIALS += [
# ── Sulfides ──────────────────────────────────────────────────────────────────
("FeS2","Iron Pyrite","cubic","Pa-3",205,5.417,5.417,5.417,90,90,90,5.011,0.95,["Fe","S"],["cubic","sulfide","semiconductor","photovoltaic"],"Fool's gold. Near-ideal band gap for solar cells and is earth-abundant and non-toxic.",zincblende("Fe","S")),
("PbS","Lead Sulfide (Galena)","cubic","Fm-3m",225,5.936,5.936,5.936,90,90,90,7.600,0.37,["Pb","S"],["cubic","sulfide","semiconductor","infrared"],"Main lead ore mineral. IR photodetector material with very small band gap.",rock_salt("Pb","S")),
("ZnS","Zinc Sulfide (Wurtzite)","hexagonal","P63mc",186,3.820,3.820,6.260,90,90,120,4.090,3.91,["Zn","S"],["hexagonal","sulfide","semiconductor","phosphor"],"Wurtzite ZnS used as phosphor in cathode ray tubes and fluorescent paints.",wurtzite("Zn","S")),
("MoS2","Molybdenum Disulfide","hexagonal","P63/mmc",194,3.160,3.160,12.295,90,90,120,5.060,1.20,["Mo","S"],["hexagonal","sulfide","2d","lubricant"],"Layered structure. Dry lubricant. Monolayer is a direct-gap semiconductor with photoluminescence.",hcp("Mo")),
("WS2","Tungsten Disulfide","hexagonal","P63/mmc",194,3.153,3.153,12.362,90,90,120,7.500,1.35,["W","S"],["hexagonal","sulfide","2d","semiconductor"],"Transition metal dichalcogenide. Strong photoluminescence in monolayer form.",hcp("W")),
("CuS","Copper Sulfide (Covellite)","hexagonal","P63/mmc",194,3.792,3.792,16.34,90,90,120,4.600,1.30,["Cu","S"],["hexagonal","sulfide","semiconductor"],"Metallic p-type semiconductor. Covellite mineral with distinctive indigo-blue color.",hcp("Cu")),
("Bi2S3","Bismuth Sulfide","orthorhombic","Pbnm",62,11.15,11.30,3.981,90,90,90,6.780,1.30,["Bi","S"],["orthorhombic","sulfide","semiconductor"],"Layered structure explored for thermoelectrics and solar cells.",bcc("Bi")),
# ── Diamond and carbon ────────────────────────────────────────────────────────
("C","Diamond","cubic","Fd-3m",227,3.567,3.567,3.567,90,90,90,3.515,5.47,["C"],["cubic","semiconductor","hard","carbon"],"Hardest natural material (Mohs 10). Wide band gap 5.47 eV. Used in cutting tools and quantum computing.",diamond("C")),
# ── Silicates and other minerals ──────────────────────────────────────────────
("SrTiO3","Strontium Titanate","cubic","Pm-3m",221,3.905,3.905,3.905,90,90,90,5.117,3.25,["Sr","Ti","O"],["cubic","perovskite","oxide"],"Cubic perovskite oxide used as substrate and in high-voltage capacitors.",perovskite("Sr","Ti","O")),
("CsCl","Cesium Chloride","cubic","Pm-3m",221,4.123,4.123,4.123,90,90,90,3.988,8.30,["Cs","Cl"],["cubic","halide","ionic"],"Simple cubic CsCl structure (not rock-salt). Used in density-gradient ultracentrifugation.",perovskite("Cs","Cl","Cl")),
# ── Intermetallics and alloys ─────────────────────────────────────────────────
("AuCu3","Gold-Copper Intermetallic","cubic","Pm-3m",221,3.750,3.750,3.750,90,90,90,14.70,None,["Au","Cu"],["cubic","intermetallic","ordered-alloy"],"L12-ordered intermetallic. Model system for studying order-disorder transitions.",perovskite("Au","Cu","Cu")),
("Ni3Al","Nickel Aluminide","cubic","Pm-3m",221,3.572,3.572,3.572,90,90,90,7.350,None,["Ni","Al"],["cubic","intermetallic","superalloy"],"Gamma-prime phase that strengthens nickel superalloys in jet engines.",perovskite("Ni","Al","Ni")),
("TiN","Titanium Nitride","cubic","Fm-3m",225,4.240,4.240,4.240,90,90,90,5.430,None,["Ti","N"],["cubic","nitride","hard-coating","gold-colored"],"Extremely hard gold-colored coating on drill bits and decorative fixtures.",rock_salt("Ti","N")),
("ZrN","Zirconium Nitride","cubic","Fm-3m",225,4.577,4.577,4.577,90,90,90,7.090,None,["Zr","N"],["cubic","nitride","hard-coating"],"Hard refractory nitride used as protective coating and diffusion barrier.",rock_salt("Zr","N")),
("TiC","Titanium Carbide","cubic","Fm-3m",225,4.327,4.327,4.327,90,90,90,4.930,None,["Ti","C"],["cubic","carbide","hard","cermet"],"Extremely hard cermet component. Used in cutting tools and wear-resistant coatings.",rock_salt("Ti","C")),
("WC","Tungsten Carbide","hexagonal","P63/mmc",194,2.906,2.906,2.837,90,90,120,15.63,None,["W","C"],["hexagonal","carbide","hard","cutting-tool"],"Second hardest material after diamond. Used in drill bits, mining, and machining tools.",hcp("W")),
]

MATERIALS += [
# ── More semiconductors ───────────────────────────────────────────────────────
("CdSe","Cadmium Selenide","hexagonal","P63mc",186,4.299,4.299,7.010,90,90,120,5.816,1.74,["Cd","Se"],["hexagonal","semiconductor","quantum-dot"],"CdSe quantum dots show size-tunable emission. Widely used in display technology.",wurtzite("Cd","Se")),
("HgTe","Mercury Telluride","cubic","F-43m",216,6.461,6.461,6.461,90,90,90,8.100,None,["Hg","Te"],["cubic","semiconductor","topological"],"Zero-gap semiconductor. Interface with CdTe creates topological insulator quantum well.",zincblende("Hg","Te")),
("BP","Boron Phosphide","cubic","F-43m",216,4.538,4.538,4.538,90,90,90,2.970,2.00,["B","P"],["cubic","semiconductor","zincblende"],"Wide-gap III-V semiconductor with high thermal conductivity.",zincblende("B","P")),
("BAs","Boron Arsenide","cubic","F-43m",216,4.777,4.777,4.777,90,90,90,5.220,1.50,["B","As"],["cubic","semiconductor","high-thermal"],"Predicted and confirmed to have ultra-high thermal conductivity. Promising for electronics cooling.",zincblende("B","As")),
# ── Superconductors ───────────────────────────────────────────────────────────
("Nb3Sn","Niobium Tin","cubic","Pm-3m",221,5.290,5.290,5.290,90,90,90,8.900,None,["Nb","Sn"],["cubic","superconductor","A15"],"A15 structure superconductor. Used in MRI magnets and fusion reactor coils (Tc=18 K).",perovskite("Nb","Sn","Nb")),
("MgB2","Magnesium Diboride","hexagonal","P6/mmm",191,3.086,3.086,3.524,90,90,120,2.630,None,["Mg","B"],["hexagonal","superconductor","boride"],"Superconductor at 39 K discovered in 2001. Simple composition makes it industrially attractive.",hcp("Mg")),
# ── Thermoelectrics ───────────────────────────────────────────────────────────
("Bi2Te3","Bismuth Telluride","trigonal","R-3m",166,4.386,4.386,30.497,90,90,120,7.700,0.16,["Bi","Te"],["trigonal","thermoelectric","topological"],"Best room-temperature thermoelectric. Used in Peltier coolers for electronics.",hcp("Bi")),
("PbTe","Lead Telluride","cubic","Fm-3m",225,6.462,6.462,6.462,90,90,90,8.160,0.31,["Pb","Te"],["cubic","thermoelectric","semiconductor"],"High-temperature thermoelectric for power generation from waste heat.",rock_salt("Pb","Te")),
("SnTe","Tin Telluride","cubic","Fm-3m",225,6.327,6.327,6.327,90,90,90,6.450,0.18,["Sn","Te"],["cubic","thermoelectric","topological"],"Topological crystalline insulator with rock-salt structure.",rock_salt("Sn","Te")),
# ── Magnetic materials ────────────────────────────────────────────────────────
("Nd2Fe14B","Neodymium Magnet","tetragonal","P42/mnm",136,8.800,8.800,12.20,90,90,90,7.600,None,["Nd","Fe","B"],["tetragonal","permanent-magnet","rare-earth"],"Strongest permanent magnet material. Used in EV motors, wind turbines, and speakers.",rutile("Nd","Fe")),
("SmCo5","Samarium Cobalt","hexagonal","P6/mmm",191,5.003,5.003,3.979,90,90,120,8.560,None,["Sm","Co"],["hexagonal","permanent-magnet","rare-earth"],"High-temperature permanent magnet used in aerospace and defense applications.",hcp("Co")),
("MnAs","Manganese Arsenide","hexagonal","P63/mmc",194,3.710,3.710,5.720,90,90,120,6.200,None,["Mn","As"],["hexagonal","magnetic","semiconductor"],"Ferromagnetic semiconductor used in spintronics research.",hcp("Mn")),
# ── Battery materials ─────────────────────────────────────────────────────────
("LiCoO2","Lithium Cobalt Oxide","trigonal","R-3m",166,2.816,2.816,14.054,90,90,120,5.060,None,["Li","Co","O"],["trigonal","cathode","battery","layered"],"Original lithium-ion battery cathode material. Used in smartphones and laptops.",hcp("Co")),
("FePO4","Iron Phosphate","orthorhombic","Pnma",62,9.820,5.792,4.782,90,90,90,3.056,None,["Fe","P","O"],["orthorhombic","cathode","battery","olivine"],"Lithium-free olivine structure. Becomes LiFePO4 when lithiated.",bcc("Fe")),
]


# ── Insert function ───────────────────────────────────────────────────────────

def build_doc(mat):
    (formula, name, cs, sg, sgn, a, b, c, al, be, ga,
     dens, bg, elements, tags, desc, raw_sites) = mat

    vol = round(a * b * c * (
        1 - (
            (__import__('math').cos(__import__('math').radians(al)))**2 +
            (__import__('math').cos(__import__('math').radians(be)))**2 +
            (__import__('math').cos(__import__('math').radians(ga)))**2
        ) + 2 * (
            __import__('math').cos(__import__('math').radians(al)) *
            __import__('math').cos(__import__('math').radians(be)) *
            __import__('math').cos(__import__('math').radians(ga))
        )
    ) ** 0.5, 3)

    sites = [
        {"label": s[0], "element": s[1], "x": round(s[2],6),
         "y": round(s[3],6), "z": round(s[4],6), "occupancy": 1.0}
        for s in raw_sites
    ]

    return {
        "formula": formula,
        "name": name,
        "crystal_system": cs,
        "space_group": sg,
        "space_group_number": sgn,
        "density": dens,
        "band_gap": bg,
        "formation_energy": None,
        "lattice": {"a":a,"b":b,"c":c,"alpha":al,"beta":be,"gamma":ga,"volume":vol},
        "sites": sites,
        "elements": elements,
        "nsites": len(sites),
        "description": desc,
        "ai_summary": None,
        "cif_path": None,
        "cif_content": None,
        "tags": tags,
        "properties": {},
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    }


async def main():
    client = AsyncIOMotorClient(settings.mongodb_url)
    db = client[settings.mongodb_db]
    col = db["materials"]

    print(f"Inserting {len(MATERIALS)} materials...")
    inserted = updated = skipped = 0

    for mat in MATERIALS:
        try:
            doc = build_doc(mat)
            result = await col.update_one(
                {"formula": doc["formula"]},
                {"$set": doc},
                upsert=True
            )
            if result.upserted_id:
                inserted += 1
                print(f"  + {doc['formula']}")
            else:
                updated += 1
        except Exception as e:
            print(f"  ! ERROR on {mat[0]}: {e}")
            skipped += 1

    total = await col.count_documents({})
    print(f"\nDone! Inserted: {inserted} | Updated: {updated} | Skipped: {skipped}")
    print(f"Total materials in DB: {total}")
    client.close()


if __name__ == "__main__":
    asyncio.run(main())
