import random
import hashlib
import json
from typing import Dict, Any, List

from app.ai.openai_client import chat_completion


# ======================================================
# ULTRA-MODERN DESIGN SYSTEMS
# ======================================================

DESIGN_SYSTEMS = [
    {
        "id": "glass_luxury",
        "name": "Glass Luxury",
        "base": "dark",
        "style": "glassmorphism cards with backdrop-blur-2xl, floating elements, gradient meshes, overlapping sections with -mt-20 to -mt-40, subtle borders, premium shadows with colored glows",
    },
    {
        "id": "flow_minimal",
        "name": "Flow Minimal",
        "base": "light",
        "style": "huge typography (text-7xl+), flowing sections blend seamlessly, generous white space, elegant transitions, no hard edges, organic shapes",
    },
    {
        "id": "vibrant_depth",
        "name": "Vibrant Depth",
        "base": "dark",
        "style": "bright gradient overlays, layered cards with transform hover effects, z-index depth, geometric background patterns, bold neon accents",
    },
    {
        "id": "elegant_serif",
        "name": "Elegant Serif",
        "base": "light",
        "style": "serif headings (font-serif), refined spacing, gold/champagne accents, soft shadows, luxury feel, subtle animations, organic curved dividers",
    },
    {
        "id": "sharp_modern",
        "name": "Sharp Modern",
        "base": "light",
        "style": "sharp edges, high contrast blacks and whites, asymmetric grid layouts, bold sans-serif, geometric shapes, minimal decoration, brutalist influence",
    },
]

COLOR_PALETTES = {
    "midnight_purple": {
        "name": "Midnight Purple",
        "primary": "from-purple-600 via-indigo-600 to-purple-700",
        "accent": "purple-500",
        "bg_dark": "from-purple-950 via-indigo-950 to-black",
        "bg_light": "from-purple-50 via-indigo-50 to-white",
        "glow": "purple-500/30",
    },
    "ocean_deep": {
        "name": "Ocean Deep",
        "primary": "from-cyan-500 via-blue-600 to-cyan-700",
        "accent": "cyan-400",
        "bg_dark": "from-cyan-950 via-blue-950 to-black",
        "bg_light": "from-cyan-50 via-blue-50 to-white",
        "glow": "cyan-500/30",
    },
    "sunset_fire": {
        "name": "Sunset Fire",
        "primary": "from-orange-500 via-rose-600 to-pink-600",
        "accent": "orange-500",
        "bg_dark": "from-orange-950 via-rose-950 to-black",
        "bg_light": "from-orange-50 via-rose-50 to-white",
        "glow": "orange-500/30",
    },
    "emerald_forest": {
        "name": "Emerald Forest",
        "primary": "from-emerald-600 via-teal-600 to-green-600",
        "accent": "emerald-500",
        "bg_dark": "from-emerald-950 via-teal-950 to-black",
        "bg_light": "from-emerald-50 via-teal-50 to-white",
        "glow": "emerald-500/30",
    },
    "slate_pro": {
        "name": "Slate Pro",
        "primary": "from-slate-700 via-gray-800 to-slate-900",
        "accent": "slate-600",
        "bg_dark": "from-black via-slate-950 to-gray-900",
        "bg_light": "from-white via-slate-50 to-gray-100",
        "glow": "slate-500/30",
    },
}


def stable_seed(*values: str) -> int:
    raw = "|".join([v or "" for v in values])
    return int(hashlib.sha256(raw.encode()).hexdigest()[:8], 16)


# ======================================================
# STRUCTURE GENERATION
# ======================================================

def generate_ai_structure(
    business_type: str,
    goal: str,
    version: int = 1,
    prompt: str = "",
):
    """
    Generates flowing, modern website structure.
    """
    bt = (business_type or "business").lower().strip()
    if bt not in ("restaurant", "business"):
        bt = "business"

    # Deterministic if prompt provided
    if prompt.strip():
        rng = random.Random(stable_seed(bt, goal or "", prompt, str(version)))
    else:
        rng = random.Random()

    # Pick design system
    design = rng.choice(DESIGN_SYSTEMS)
    
    # Pick color palette
    palette_key = rng.choice(list(COLOR_PALETTES.keys()))
    palette = COLOR_PALETTES[palette_key]

    # Core sections (always included)
    core = ["hero", "value_prop", "features", "social_proof", "cta"]
    
    # Optional sections
    optional = ["process", "pricing", "testimonials", "faq", "team", "contact"]
    
    # Pick 2-4 optional sections
    selected_optional = rng.sample(optional, rng.randint(2, 4))
    
    # Combine
    sections = core + selected_optional
    
    # Ensure contact is last if included
    if "contact" in sections:
        sections = [s for s in sections if s != "contact"] + ["contact"]
    
    # Limit to 7-9 sections for optimal flow
    sections = sections[:rng.randint(7, 9)]

    return {
        "sections": sections,
        "design": design,
        "palette": palette,
        "palette_key": palette_key,
        "html_mode": True,
        "modern_flow": True,
    }


# ======================================================
# ULTRA-MODERN HTML GENERATION
# ======================================================

ULTRA_MODERN_SYSTEM = """You are the world's best web designer creating ULTRA-PREMIUM, FLOWING websites.

Your designs are MASTERPIECES that look like they cost $50,000+.

CORE PRINCIPLES:

1. FLOWING SECTIONS (CRITICAL!)
   - Sections MUST overlap using negative margins (-mt-32, -mt-48)
   - Create depth with layering (z-10, z-20, z-30)
   - Blend backgrounds with gradients
   - NO hard separations between sections
   - Make it feel like ONE cohesive page

2. GLASSMORPHISM (for dark themes)
   - backdrop-blur-xl on all cards
   - bg-white/[0.05] to bg-white/[0.15] backgrounds
   - border border-white/10
   - Subtle shadows: shadow-2xl shadow-[color]/20

3. DEPTH & LAYERING
   - Floating cards over backgrounds
   - Overlapping elements create 3D effect
   - Use transform hover:scale-105
   - Gradient mesh backgrounds (blur-3xl orbs)

4. TYPOGRAPHY
   - Hero: text-7xl md:text-8xl lg:text-9xl
   - Mix font weights: from-thin to font-black
   - Gradient text: bg-gradient-to-r bg-clip-text text-transparent
   - Line height: leading-tight on huge text

5. SPACING
   - Generous: py-32, py-40, py-48 on sections
   - Overlap: -mt-32, -mt-40, -mt-48 to blend
   - Breathing room: max-w-7xl mx-auto px-6

6. BACKGROUNDS
   - Gradient meshes with animated orbs
   - Subtle grid patterns: opacity-[0.02]
   - Blend between sections with gradients
   - Use backdrop-blur on overlays

7. ANIMATIONS READY
   - Add data-animate attributes for scroll
   - Stagger delays: delay-100, delay-200, delay-300
   - Transform ready: hover:scale-105 transition-all

TECHNICAL:
- Return ONLY valid JSON
- Each section: { html: "...", data: {...} }
- NO image placeholders (users add later)
- NO generic text (make it specific to business)
- Mobile-first: use md: and lg: breakpoints
- Semantic HTML5

GOAL:
Make every website feel like a custom-designed masterpiece.
Users should think "This looks EXPENSIVE!"
"""

ULTRA_MODERN_USER = """Business: {business_name}
Description: {prompt}
Type: {business_type}

DESIGN SYSTEM: {design_name}
Style Rules: {design_style}
Base Theme: {design_base}

COLOR PALETTE: {palette_name}
Primary Gradient: {primary}
Accent: {accent}
Background: {background}
Glow Effect: {glow}

Sections to Create: {sections}

Generate this JSON structure:
{{
  "business_name": "{business_name}",
  "sections": {{
    "hero": {{
      "html": "<section class='relative min-h-screen ...'>FLOWING MODERN HTML</section>",
      "data": {{
        "headline": "Powerful headline",
        "subheadline": "Compelling subheadline",
        "cta": "Clear call-to-action"
      }}
    }},
    "value_prop": {{
      "html": "<section class='relative py-32 -mt-40 z-20 ...'>OVERLAPPING SECTION</section>",
      "data": {{
        "title": "Key benefit",
        "description": "Why this matters"
      }}
    }}
    ... for ALL sections in the list
  }},
  "seo": {{
    "title": "SEO-optimized title",
    "description": "Compelling meta description (155 chars)",
    "keywords": ["keyword1", "keyword2", "keyword3"]
  }}
}}

CRITICAL REQUIREMENTS:
✓ Sections MUST overlap with negative margins
✓ Use the exact color palette provided
✓ Apply design system style consistently
✓ NO boxy separated sections
✓ Create visual depth with layering
✓ Make it look EXPENSIVE
✓ Real business copy (no placeholders)
✓ Mobile responsive
✓ Ready for scroll animations

Make this a MASTERPIECE!
"""


def generate_html_sections(
    business_name: str,
    prompt: str,
    business_type: str,
    structure: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Generates ultra-modern HTML sections.
    """
    design = structure["design"]
    palette = structure["palette"]
    sections = structure["sections"]

    try:
        response = chat_completion(
            system=ULTRA_MODERN_SYSTEM,
            user=ULTRA_MODERN_USER.format(
                business_name=business_name,
                prompt=prompt,
                business_type=business_type,
                design_name=design["name"],
                design_style=design["style"],
                design_base=design["base"],
                palette_name=palette["name"],
                primary=palette["primary"],
                accent=palette["accent"],
                background=palette["bg_dark" if design["base"] == "dark" else "bg_light"],
                glow=palette["glow"],
                sections=", ".join(sections),
            ),
            temperature=0.95,  # High creativity
        )

        parsed = json.loads(response)

        # Validate
        if not isinstance(parsed, dict) or "sections" not in parsed:
            raise ValueError("Invalid response structure")

        # Ensure SEO
        if "seo" not in parsed:
            parsed["seo"] = {
                "title": f"{business_name} - Professional {business_type}",
                "description": f"Discover {business_name}, your trusted partner for {business_type} services.",
                "keywords": [business_type, "professional", "quality", "trusted"],
            }

        return parsed

    except Exception as e:
        print(f"AI generation failed: {e}")
        return generate_premium_fallback(business_name, sections, structure)


def generate_premium_fallback(
    business_name: str,
    sections: List[str],
    structure: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Premium fallback if AI fails.
    """
    design = structure["design"]
    palette = structure["palette"]
    is_dark = design["base"] == "dark"

    bg = palette["bg_dark"] if is_dark else palette["bg_light"]
    text = "text-white" if is_dark else "text-black"
    primary = palette["primary"]
    accent = palette["accent"]
    glow = palette["glow"]

    fallback = {
        "business_name": business_name,
        "sections": {},
        "seo": {
            "title": f"{business_name}",
            "description": f"Welcome to {business_name}",
            "keywords": ["business", "professional"],
        },
    }

    # Hero section
    if "hero" in sections:
        fallback["sections"]["hero"] = {
            "html": f"""
<section class="relative min-h-screen flex items-center justify-center overflow-hidden bg-gradient-to-br {bg}">
    <div class="absolute inset-0 overflow-hidden">
        <div class="absolute top-1/4 left-1/4 w-[600px] h-[600px] bg-{accent} rounded-full blur-3xl opacity-20 animate-pulse"></div>
        <div class="absolute bottom-1/4 right-1/4 w-[600px] h-[600px] bg-gradient-to-r {primary} rounded-full blur-3xl opacity-20"></div>
        <div class="absolute inset-0 bg-[linear-gradient(rgba(255,255,255,0.02)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,0.02)_1px,transparent_1px)] bg-[size:64px_64px]"></div>
    </div>
    
    <div class="relative z-10 max-w-7xl mx-auto px-6 text-center">
        <h1 class="text-7xl md:text-8xl lg:text-9xl font-bold {text} tracking-tight leading-none mb-8">
            <span class="bg-gradient-to-r {primary} bg-clip-text text-transparent">
                {{{{headline}}}}
            </span>
        </h1>
        
        <p class="text-xl md:text-2xl {text} opacity-80 max-w-4xl mx-auto mb-12 leading-relaxed">
            {{{{subheadline}}}}
        </p>
        
        <button class="group relative px-10 py-5 bg-gradient-to-r {primary} text-white rounded-2xl font-semibold text-lg overflow-hidden transition-all hover:scale-105 hover:shadow-2xl shadow-{glow}">
            <span class="relative z-10">{{{{cta}}}}</span>
            <div class="absolute inset-0 bg-white/20 translate-y-full group-hover:translate-y-0 transition-transform"></div>
        </button>
    </div>
</section>
            """,
            "data": {
                "headline": business_name,
                "subheadline": "Your trusted partner for exceptional service and quality",
                "cta": "Get Started Today",
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
    Generates 3 alternative versions of text.
    """
    prompt = f"""Rewrite this text in {tone} tone. Generate 3 different versions.

Original: {original_text}
Context: {business_context}

Return ONLY a JSON array: ["version 1", "version 2", "version 3"]

Each version:
- {tone} tone
- Compelling and clear
- Different from others
- Maintains core message
"""

    try:
        response = chat_completion(
            system="Expert copywriter. Return only JSON arrays.",
            user=prompt,
            temperature=0.8,
        )
        
        alternatives = json.loads(response)
        return alternatives[:3] if isinstance(alternatives, list) and len(alternatives) >= 3 else [original_text] * 3
    except Exception:
        return [original_text] * 3


# ======================================================
# MAIN ENTRY POINT
# ======================================================

def generate_ai_plan(ai_input: Dict[str, Any], version: int = 1) -> Dict[str, Any]:
    """
    Main generation function.
    """
    prompt = ai_input.get("prompt", "")
    business_name = ai_input.get("business_name", "Your Business")
    goal = ai_input.get("primary_goal", "Get started")

    # Infer business type
    business_type = "business"
    prompt_lower = prompt.lower()
    if any(w in prompt_lower for w in ["restaurant", "cafe", "food", "pizza", "burger", "dining"]):
        business_type = "restaurant"

    # Generate structure
    structure = generate_ai_structure(
        business_type=business_type,
        goal=goal,
        version=version,
        prompt=prompt,
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