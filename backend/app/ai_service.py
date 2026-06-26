"""
AI service: calls Ollama (Llama3 / Mistral) to generate
scientific material descriptions.
Falls back to template-based summaries when Ollama is unavailable.
"""
import logging
import httpx
from app.config import settings

logger = logging.getLogger(__name__)


async def generate_material_summary(material: dict) -> str:
    """Generate an AI summary for a material. Returns a string."""
    formula = material.get("formula", "Unknown")
    name = material.get("name", formula)
    crystal_system = material.get("crystal_system", "unknown")
    space_group = material.get("space_group", "unknown")
    density = material.get("density")
    elements = material.get("elements", [])
    nsites = material.get("nsites", 0)

    prompt = f"""You are a materials science expert. Write a concise scientific summary (3-4 paragraphs) for the following material:

Material: {name} ({formula})
Crystal System: {crystal_system}
Space Group: {space_group}
Density: {f"{density:.3f} g/cm³" if density else "unknown"}
Elements: {", ".join(elements)}
Number of atoms in unit cell: {nsites}

Please cover:
1. Crystal structure and bonding
2. Key physical and electronic properties
3. Main applications and industrial uses
4. Any notable characteristics

Keep the language accessible but scientifically accurate."""

    # Try Ollama first
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{settings.ollama_url}/api/generate",
                json={
                    "model": settings.ollama_model,
                    "prompt": prompt,
                    "stream": False,
                },
            )
            if response.status_code == 200:
                data = response.json()
                return data.get("response", "").strip()
    except Exception as e:
        logger.warning(f"Ollama unavailable: {e}. Using template summary.")

    # Fallback: template-based summary
    return _template_summary(material)


def _template_summary(material: dict) -> str:
    formula = material.get("formula", "Unknown")
    name = material.get("name", formula)
    crystal_system = material.get("crystal_system", "unknown")
    space_group = material.get("space_group", "unknown")
    density = material.get("density")
    elements = material.get("elements", [])
    nsites = material.get("nsites", 0)
    lattice = material.get("lattice", {})

    density_str = f"{density:.3f} g/cm³" if density else "not determined"
    elements_str = ", ".join(elements) if elements else "unknown elements"
    vol_str = f"{lattice.get('volume', 0):.2f} Å³" if lattice else "unknown"

    summary = (
        f"{name} ({formula}) is a crystalline material belonging to the "
        f"{crystal_system} crystal system with space group {space_group}. "
        f"The unit cell contains {nsites} atomic site(s) with a volume of {vol_str} "
        f"and a calculated density of {density_str}.\n\n"
        f"The material is composed of {elements_str}. "
        f"Its crystal structure is characterized by periodic arrangement of atoms "
        f"that determines its fundamental physical and chemical properties, "
        f"including mechanical strength, thermal conductivity, and electronic behavior.\n\n"
        f"Materials of this type have broad applications in areas including "
        f"electronics, catalysis, structural engineering, and advanced coatings, "
        f"depending on their specific composition and structural properties. "
        f"The {crystal_system} symmetry imposes characteristic anisotropic behavior "
        f"across different crystallographic directions.\n\n"
        f"Further characterization through techniques such as X-ray diffraction (XRD), "
        f"electron microscopy, and spectroscopy can reveal detailed information about "
        f"defects, grain boundaries, and surface chemistry that influence real-world performance."
    )
    return summary
