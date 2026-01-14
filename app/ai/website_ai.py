import random
import hashlib

# ======================================================
# ALLOWED FRONTEND SCHEMA (MUST MATCH aiStructure.ts)
# ======================================================

HERO_VARIANTS = [
    "split_image",
    "centered_text",
    "image_background",
    "minimal",
]

SECTION_SETS = {
    "restaurant": [
        ["trust", "services", "testimonial", "cta"],
        ["about", "services", "process", "cta"],
        ["services", "testimonial", "cta"],
    ],
    "business": [
        ["about", "services", "cta"],
        ["services", "process", "testimonial", "cta"],
        ["trust", "services", "cta"],
    ],
}

THEMES = [
    {"palette": "light", "accent": "indigo"},
    {"palette": "light", "accent": "orange"},
    {"palette": "dark", "accent": "emerald"},
    {"palette": "dark", "accent": "indigo"},
    {"palette": "light", "accent": "neutral"},
]

FOOTER_VARIANTS = [
    {"variant": "minimal"},
    {"variant": "standard"},
]


# ======================================================
# UTILS
# ======================================================

def stable_seed(*values: str) -> int:
    raw = "|".join(values)
    h = hashlib.sha256(raw.encode()).hexdigest()
    return int(h[:8], 16)


# ======================================================
# MAIN AI STRUCTURE GENERATOR
# ======================================================

def generate_ai_structure(
    business_type: str,
    goal: str = "conversions",
    version: int = 1,
):
    """
    Deterministic AI layout generator.
    SAME INPUT = SAME WEBSITE FOREVER.
    """

    rng = random.Random(
        stable_seed(business_type, goal, str(version))
    )

    hero = {
        "variant": rng.choice(HERO_VARIANTS),
    }

    section_presets = SECTION_SETS.get(
        business_type,
        SECTION_SETS["business"],
    )

    sections = rng.choice(section_presets)

    structure = {
        "hero": hero,
        "sections": sections,
        "theme": rng.choice(THEMES),
        "footer": rng.choice(FOOTER_VARIANTS),
    }

    return structure
