import random
import hashlib
import json
from typing import Dict, Any, List

from app.ai.openai_client import chat_completion


# ======================================================
# MODERN DESIGN SYSTEM
# ======================================================

DESIGN_SYSTEMS = [
    {
        "id": "premium_glass",
        "name": "Premium Glass",
        "base": "dark",
        "characteristics": "glassmorphism cards, backdrop blur, floating elements, overlapping sections, gradient meshes, no hard borders",
    },
    {
        "id": "minimal_flow",
        "name": "Minimal Flow",
        "base": "light",
        "characteristics": "huge typography, flowing sections with negative margins, subtle shadows, lots of white space, elegant transitions",
    },
    {
        "id": "vibrant_layers",
        "name": "Vibrant Layers",
        "base": "dark",
        "characteristics": "bright gradient overlays, layered cards with z-index, bold colors, geometric shapes, depth",
    },
    {
        "id": "elegant_luxury",
        "name": "Elegant Luxury",
        "base": "light",
        "characteristics": "serif headings, gold accents, refined spacing, subtle animations, luxury feel, organic curves",
    },
    {
        "id": "modern_brutalist",
        "name": "Modern Brutalist",
        "base": "light",
        "characteristics": "sharp edges, high contrast, asymmetric layouts, bold typography, monochrome with accent pops",
    },
]

COLOR_PALETTES = {
    "purple_dusk": {
        "primary": "from-purple-600 to-indigo-600",
        "accent": "purple-500",
        "bg_dark": "from-purple-950 via-indigo-950 to-black",
        "bg_light": "from-purple-50 via-indigo-50 to-white",
        "text_light": "purple-100",
        "text_dark": "purple-900",
    },
    "ocean_breeze": {
        "primary": "from-cyan-500 to-blue-600",
        "accent": "cyan-500",
        "bg_dark": "from-cyan-950 via-blue-950 to-black",
        "bg_light": "from-cyan-50 via-blue-50 to-white",
        "text_light": "cyan-100",
        "text_dark": "cyan-900",
    },
    "sunset_glow": {
        "primary": "from-orange-500 to-pink-600",
        "accent": "orange-500",
        "bg_dark": "from-orange-950 via-pink-950 to-black",
        "bg_light": "from-orange-50 via-pink-50 to-white",
        "text_light": "orange-100",
        "text_dark": "orange-900",
    },
    "forest_mist": {
        "primary": "from-emerald-600 to-teal-600",
        "accent": "emerald-500",
        "bg_dark": "from-emerald-950 via-teal-950 to-black",
        "bg_light": "from-emerald-50 via-teal-50 to-white",
        "text_light": "emerald-100",
        "text_dark": "emerald-900",
    },
    "monochrome_pro": {
        "primary": "from-gray-800 to-gray-900",
        "accent": "gray-700",
        "bg_dark": "from-black via-gray-950 to-gray-900",
        "bg_light": "from-white via-gray-50 to-gray-100",
        "text_light": "gray-100",
        "text_dark": "gray-900",
    },
}


def stable_seed(*values: str) -> int:
    raw = "|".join([v or "" for v in values])
    return int(hashlib.sha256(raw.encode()).hexdigest()[:8], 16)


# ======================================================
# STRUCTURE GENERATION - FLOWING DESIGN
# ======================================================

def generate_ai_structure(
    business_type: str,
    prompt: str = "",
    version: int = 1,
):
    """
    Generates structure optimized for flowing, modern designs.
    """
    # Deterministic or random
    if prompt.strip():
        rng = random.Random(stable_seed(business_type, prompt, str(version)))
    else:
        rng = random.Random()

    # Pick design system
    design_system = rng.choice(DESIGN_SYSTEMS)
    
    # Pick color palette
    palette_key = rng.choice(list(COLOR_PALETTES.keys()))
    palette = COLOR_PALETTES[palette_key]

    # Sections - always include hero, then 4-6 more
    core_sections = ["hero", "features", "showcase", "social_proof", "cta"]
    optional = ["process", "pricing", "team", "faq", "contact"]
    
    selected = core_sections + rng.sample(optional, rng.randint(2, 4))
    
    # Always end with contact for paid users
    if "contact" in selected:
        selected = [s for s in selected if s != "contact"] + ["contact"]
    
    return {
        "sections": selected[:7],  # Max 7 sections for clean flow
        "design_system": design_system,
        "palette": palette,
        "palette_name": palette_key,
        "html_mode": True,
        "modern_flow": True,
    }


# ======================================================
# AI PROMPT FOR FLOWING, MODERN HTML
# ======================================================

MODERN_HTML_SYSTEM = """You are a world-class web designer creating ULTRA-MODERN, FLOWING websites.

Your designs must be:
- SEAMLESS: Sections blend and overlap, never feel "boxy"
- MODERN: Glassmorphism, gradients, blur effects, floating elements
- PREMIUM: Feels like a $10k+ custom website
- FLOWING: Elements overlap with negative margins, creating depth

KEY DESIGN PRINCIPLES:

1. OVERLAPPING SECTIONS
   - Use negative margins (e.g., -mt-32, -mt-48) to make sections overlap
   - Float cards over background sections
   - Create depth with z-index layering

2. GLASSMORPHISM
   - backdrop-blur-xl on cards
   - bg-white/10 or bg-black/10 with borders
   - Subtle shadows with colored glows

3. GRADIENT MESHES
   - Background gradients that blend sections
   - Use: bg-gradient-to-br from-[color] via-[color] to-[color]
   - Blur effects: blur-3xl on decorative orbs

4. FLOATING ELEMENTS
   - Cards that "float" over backgrounds
   - Rounded-3xl or rounded-2xl
   - Transform hover effects (hover:scale-105)

5. NO HARD BORDERS
   - Avoid solid borders between sections
   - Use gradients or blurs as dividers
   - Make background colors blend

6. TYPOGRAPHY
   - Huge hero text (text-7xl md:text-8xl)
   - Mix font weights creatively
   - Use gradient text (bg-clip-text text-transparent)

7. SPACING
   - Generous padding (py-24, py-32)
   - Let sections breathe
   - Use negative space strategically

STRUCTURE:
- Return ONLY valid JSON
- Each section gets: html (complete HTML), data (editable fields)
- Apply design system characteristics consistently
- Make it feel like ONE flowing page, not separate sections

DO NOT:
- Create boxy, separated sections
- Use boring layouts
- Add image placeholders
- Use placeholder text
"""

MODERN_HTML_USER = """Business: {business_name}
Description: {prompt}
Type: {business_type}

DESIGN SYSTEM: {design_system_name}
Characteristics: {design_characteristics}
Base: {design_base}

COLOR PALETTE: {palette_name}
{palette_json}

Sections to generate: {sections}

Generate JSON:
{{
  "business_name": "...",
  "sections": {{
    "hero": {{
      "html": "<section class='relative min-h-screen overflow-hidden'>...flowing, modern HTML...</section>",
      "data": {{ "headline": "...", "subheadline": "...", "cta": "..." }}
    }},
    ...for each section
  }},
  "seo": {{
    "title": "...",
    "description": "...",
    "keywords": ["..."]
  }}
}}

CRITICAL:
- Make sections OVERLAP and FLOW together
- Use the color palette variables provided
- Apply {design_system_name} style throughout
- Create visual hierarchy with z-index
- No boxy, separated sections
- Premium, modern, flowing design
- Real business copy (no placeholders)
"""


def generate_html_sections(
    business_name: str,
    prompt: str,
    business_type: str,
    structure: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Generates modern, flowing HTML sections.
    """
    design_system = structure["design_system"]
    palette = structure["palette"]
    sections = structure["sections"]

    try:
        response = chat_completion(
            system=MODERN_HTML_SYSTEM,
            user=MODERN_HTML_USER.format(
                business_name=business_name,
                prompt=prompt,
                business_type=business_type,
                design_system_name=design_system["name"],
                design_characteristics=design_system["characteristics"],
                design_base=design_system["base"],
                palette_name=structure["palette_name"],
                palette_json=json.dumps(palette, indent=2),
                sections=", ".join(sections),
            ),
            temperature=0.95,  # High creativity
        )

        parsed = json.loads(response)

        if not isinstance(parsed, dict) or "sections" not in parsed:
            raise ValueError("Invalid response")

        # Ensure SEO
        if "seo" not in parsed:
            parsed["seo"] = {
                "title": f"{business_name} - Professional {business_type}",
                "description": f"{business_name} offers professional {business_type} services.",
                "keywords": [business_type, "professional", "quality"],
            }

        return parsed

    except Exception as e:
        print(f"AI generation failed: {e}")
        return generate_fallback_modern(business_name, sections, structure)


def generate_fallback_modern(
    business_name: str,
    sections: List[str],
    structure: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Fallback with modern design.
    """
    palette = structure["palette"]
    design = structure["design_system"]
    is_dark = design["base"] == "dark"

    bg_gradient = palette["bg_dark"] if is_dark else palette["bg_light"]
    text_color = "text-white" if is_dark else "text-black"
    accent = palette["accent"]

    fallback = {
        "business_name": business_name,
        "sections": {},
        "seo": {
            "title": f"{business_name}",
            "description": f"Welcome to {business_name}",
            "keywords": ["business", "professional"],
        },
    }

    if "hero" in sections:
        fallback["sections"]["hero"] = {
            "html": f"""
<section class="relative min-h-screen flex items-center justify-center overflow-hidden bg-gradient-to-br {bg_gradient}">
    <div class="absolute inset-0 overflow-hidden">
        <div class="absolute top-1/4 -left-1/4 w-96 h-96 bg-{accent} rounded-full blur-3xl opacity-20"></div>
        <div class="absolute bottom-1/4 -right-1/4 w-96 h-96 bg-{accent} rounded-full blur-3xl opacity-20"></div>
    </div>
    <div class="relative z-10 max-w-6xl mx-auto px-6 text-center">
        <h1 class="text-7xl md:text-8xl font-bold {text_color} tracking-tight mb-6 leading-none">
            {{{{headline}}}}
        </h1>
        <p class="text-xl md:text-2xl {text_color} opacity-70 max-w-3xl mx-auto mb-8">
            {{{{subheadline}}}}
        </p>
        <button class="px-8 py-4 bg-gradient-to-r {palette['primary']} text-white rounded-2xl font-semibold text-lg hover:scale-105 transition-transform shadow-xl">
            {{{{cta}}}}
        </button>
    </div>
</section>
            """,
            "data": {
                "headline": business_name,
                "subheadline": "Welcome to our website",
                "cta": "Get Started",
            },
        }

    return fallback


# ======================================================
# CONTENT REWRITER
# ======================================================

def rewrite_content(
    original_text: str,
    tone: str = "professional",
    business_context: str = "",
) -> List[str]:
    """
    Generates 3 alternatives.
    """
    prompt = f"""Rewrite this text in {tone} tone. Generate 3 versions.

Text: {original_text}
Context: {business_context}

Return JSON array: ["version 1", "version 2", "version 3"]

Make each:
- {tone} in tone
- Compelling and clear
- Different from each other
"""

    try:
        response = chat_completion(
            system="Expert copywriter. Return only JSON arrays.",
            user=prompt,
            temperature=0.8,
        )
        alternatives = json.loads(response)
        return alternatives[:3] if isinstance(alternatives, list) else [original_text] * 3
    except Exception:
        return [original_text] * 3


# ======================================================
# MAIN ENTRY
# ======================================================

def generate_ai_plan(ai_input: Dict[str, Any], version: int = 1) -> Dict[str, Any]:
    """
    Main generation function.
    """
    prompt = ai_input.get("prompt", "")
    business_name = ai_input.get("business_name", "Your Business")

    # Infer type
    business_type = "business"
    if any(w in prompt.lower() for w in ["restaurant", "cafe", "food", "pizza"]):
        business_type = "restaurant"

    # Generate structure
    structure = generate_ai_structure(
        business_type=business_type,
        prompt=prompt,
        version=version,
    )

    # Generate HTML
    content = generate_html_sections(
        business_name=business_name,
        prompt=prompt,
        business_type=business_type,
        structure=structure,
    )

    return {
        "template": business_type,
        "structure": structure,
        "content": content,
    }