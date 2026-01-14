import random
import hashlib


# ======================================================
# LEGO CATALOG (APPROVED COMPONENTS ONLY)
# ======================================================

HERO_VARIANTS = [
    "split_image",
    "centered_text",
    "image_background",
    "minimal_left",
    "bold_typography",
    "visual_focus",
]

SECTION_VARIANTS = [
    {"type": "features", "variant": "grid_3"},
    {"type": "features", "variant": "icon_rows"},
    {"type": "about", "variant": "image_left"},
    {"type": "about", "variant": "image_right"},
    {"type": "testimonials", "variant": "cards"},
    {"type": "cta", "variant": "centered"},
    {"type": "gallery", "variant": "masonry"},
    {"type": "faq", "variant": "accordion"},
]

THEMES = [
    {"palette": "light", "accent": "indigo", "font": "inter"},
    {"palette": "light", "accent": "orange", "font": "inter"},
    {"palette": "dark", "accent": "emerald", "font": "inter"},
    {"palette": "dark", "accent": "indigo", "font": "inter"},
]

FOOTER_VARIANTS = [
    {"variant": "minimal"},
    {"variant": "centered"},
]


# ======================================================
# UTILS
# ======================================================

def stable_seed(*values: str) -> int:
    """
    Converts inputs into a stable deterministic seed.
    Same website → same structure forever.
    """
    raw = "|".join(values)
    h = hashlib.sha256(raw.encode()).hexdigest()
    return int(h[:8], 16)


def pick_n(rng: random.Random, items: list, n: int):
    items = items[:]
    rng.shuffle(items)
    return items[:n]


# ======================================================
# MAIN AI STRUCTURE GENERATOR
# ======================================================

def generate_ai_structure(
    business_type: str,
    goal: str = "conversion",
    version: int = 1,
):
    """
    Returns a FULL website layout structure.
    This is called ONCE per website.
    """

    rng = random.Random(
        stable_seed(business_type, goal, str(version))
    )

    hero = {
        "variant": rng.choice(HERO_VARIANTS),
        "cta_style": rng.choice(["primary", "secondary"]),
    }

    sections = []

    # Always start strong
    sections.append(
        rng.choice(
            [s for s in SECTION_VARIANTS if s["type"] == "features"]
        )
    )

    # Middle sections (2–4)
    middle_count = rng.randint(2, 4)
    middle_sections = pick_n(
        rng,
        [s for s in SECTION_VARIANTS if s["type"] not in ["features", "cta"]],
        middle_count,
    )
    sections.extend(middle_sections)

    # Always end with CTA
    sections.append({"type": "cta", "variant": "centered"})

    structure = {
        "version": version,
        "hero": hero,
        "sections": sections,
        "theme": rng.choice(THEMES),
        "footer": rng.choice(FOOTER_VARIANTS),
    }

    return structure
