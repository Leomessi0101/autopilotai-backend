import random
import hashlib
import re
import json
from typing import Dict, Any, List, Tuple, Optional

from app.ai.openai_client import chat_completion


# ======================================================
# STRUCTURE GENERATION (ENHANCED)
# ======================================================

THEMES = [
    {"palette": "light", "accent": "indigo"},
    {"palette": "light", "accent": "orange"},
    {"palette": "dark", "accent": "indigo"},
    {"palette": "dark", "accent": "emerald"},
    {"palette": "light", "accent": "neutral"},
    {"palette": "dark", "accent": "cyan"},
    {"palette": "midnight", "accent": "violet"},
    {"palette": "dark-soft", "accent": "amber"},
]

SECTION_POOL = [
    "hero", "highlight", "about", "services", "trust", "process", 
    "testimonial", "faq", "gallery", "cta", "contact", "location"
]


def stable_seed(*values: str) -> int:
    raw = "|".join([v or "" for v in values])
    return int(hashlib.sha256(raw.encode()).hexdigest()[:8], 16)


def _ensure_unique_keep_order(items: List[str]) -> List[str]:
    seen = set()
    out = []
    for x in items:
        if x not in seen:
            seen.add(x)
            out.append(x)
    return out


def generate_ai_structure(
    business_type: str,
    goal: str,
    version: int = 1,
    prompt: str = "",
):
    """
    Generates varied structure with HTML generation instructions.
    """
    bt = (business_type or "business").lower().strip()
    if bt not in ("restaurant", "business"):
        bt = "business"

    # Deterministic if prompt exists, random otherwise
    if (prompt or "").strip():
        rng = random.Random(stable_seed(bt, (goal or ""), (prompt or ""), str(version)))
    else:
        rng = random.Random()
        rng.seed(random.SystemRandom().randint(0, 2**31 - 1))

    # Pick sections (variety)
    if bt == "restaurant":
        base_count = rng.randint(6, 9)
        preferred = ["hero", "about", "services", "gallery", "testimonial", "cta", "contact"]
    else:
        base_count = rng.randint(5, 8)
        preferred = ["hero", "about", "services", "trust", "process", "cta", "contact"]

    # Add some random sections for variety
    available = [s for s in SECTION_POOL if s not in preferred]
    extra = rng.sample(available, min(2, len(available)))
    
    sections = _ensure_unique_keep_order(preferred + extra)[:base_count]
    
    # Ensure hero first, cta/contact last
    if "hero" in sections:
        sections = ["hero"] + [s for s in sections if s != "hero"]
    if "contact" in sections:
        sections = [s for s in sections if s != "contact"] + ["contact"]
    if "cta" in sections and "cta" != sections[-1]:
        sections = [s for s in sections if s != "cta"]
        # Insert CTA before contact
        if sections[-1] == "contact":
            sections.insert(-1, "cta")
        else:
            sections.append("cta")

    # Theme variety
    t = dict(rng.choice(THEMES))
    theme = {
        "palette": t.get("palette", "dark"),
        "accent": t.get("accent", "indigo"),
        "radius": rng.choice(["md", "lg", "xl"]),
        "density": rng.choice(["compact", "comfortable", "spacious"]),
        "style": rng.choice(["modern", "minimal", "bold", "warm"]),
    }

    return {
        "sections": sections,
        "theme": theme,
        "html_mode": True,  # Flag to indicate HTML generation
    }


# ======================================================
# AI HTML GENERATION PROMPT
# ======================================================

HTML_SYSTEM_PROMPT = """You are an expert web designer and developer specializing in creating beautiful, unique landing pages.

You generate complete HTML sections using Tailwind CSS classes. Each website should feel COMPLETELY DIFFERENT from others.

KEY RULES:
1. Return ONLY valid JSON (no markdown, no commentary)
2. Generate complete HTML with Tailwind classes for each section
3. Make each layout UNIQUE - vary spacing, grids, flex directions, alignments
4. Use the theme palette and accent color provided
5. Be creative with layouts - asymmetric grids, different card styles, varied typography
6. Ensure mobile responsiveness with Tailwind's responsive classes
7. Never use placeholder text - generate real, business-specific copy
8. Include proper semantic HTML tags
9. Make it look PREMIUM and MODERN
10. Each section should have a distinct visual style
11. DO NOT add any image placeholders - users will add images separately

LAYOUT VARIETY TECHNIQUES:
- Vary grid columns: grid-cols-1, grid-cols-2, grid-cols-3, md:grid-cols-2, lg:grid-cols-3
- Mix alignments: items-start, items-center, items-end
- Different card styles: rounded-lg, rounded-2xl, rounded-3xl
- Varied spacing: gap-4, gap-6, gap-8, gap-10, gap-12
- Asymmetric layouts: split 2/3 and 1/3, or 1/2 and 1/2
- Different text alignments: text-left, text-center
- Varied padding: p-6, p-8, p-10, p-12
- Background variations: bg-white/5, bg-black/20, gradient backgrounds
"""

HTML_USER_PROMPT = """Business: {business_name}
Description: {prompt}
Type: {template}
Theme Palette: {palette}
Accent Color: {accent}
Style: {style}
Density: {density}

Sections to generate: {sections}

Generate a JSON object with this EXACT structure:
{{
  "business_name": "actual business name",
  "sections": {{
    "hero": {{
      "html": "<section>...complete HTML with Tailwind classes...</section>",
      "data": {{
        "headline": "...",
        "subheadline": "...",
        "cta_text": "..."
      }}
    }},
    "about": {{
      "html": "<section>...complete HTML with Tailwind classes...</section>",
      "data": {{
        "paragraphs": ["...", "..."]
      }}
    }}
    // ... for each section in the sections list
  }},
  "meta": {{
    "primary_color": "tailwind color class",
    "background_style": "description of background"
  }}
}}

IMPORTANT:
- Make each section visually DISTINCT
- Use {accent} as the primary accent (indigo-500, emerald-500, etc.)
- For {palette}="dark": use dark backgrounds (bg-black, bg-slate-900)
- For {palette}="light": use light backgrounds (bg-white, bg-gray-50)
- Vary the layout structure for each section
- Include the data object with editable content
- Use semantic HTML (section, article, div, h1-h6, p, etc.)
- Mobile-first responsive design
- NO placeholder text - make it specific to the business

Example hero variations:
1. Centered text with large heading
2. Split layout with text left, image placeholder right
3. Full-width background with overlay
4. Minimal with small centered content
5. Asymmetric with diagonal elements

Be creative and make EVERY website look different!
"""


def generate_html_sections(
    business_name: str,
    prompt: str,
    template: str,
    sections: List[str],
    theme: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Generates complete HTML for each section using AI.
    Returns a dict with section HTML and editable data.
    """
    try:
        response = chat_completion(
            system=HTML_SYSTEM_PROMPT,
            user=HTML_USER_PROMPT.format(
                business_name=business_name,
                prompt=prompt,
                template=template,
                sections=", ".join(sections),
                palette=theme.get("palette", "dark"),
                accent=theme.get("accent", "indigo"),
                style=theme.get("style", "modern"),
                density=theme.get("density", "comfortable"),
            ),
            temperature=0.9,  # Higher temperature for more variety
        )
        
        parsed = json.loads(response)
        
        # Validate structure
        if not isinstance(parsed, dict):
            raise ValueError("Invalid response structure")
        
        if "sections" not in parsed or not isinstance(parsed["sections"], dict):
            raise ValueError("Missing sections in response")
        
        return parsed
        
    except Exception as e:
        print(f"HTML generation failed: {str(e)}")
        # Return fallback structure
        return generate_fallback_html(business_name, sections, theme)


def generate_fallback_html(
    business_name: str,
    sections: List[str],
    theme: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Fallback HTML generator if AI fails.
    """
    palette = theme.get("palette", "dark")
    accent = theme.get("accent", "indigo")
    
    bg_class = "bg-black text-white" if palette == "dark" else "bg-white text-black"
    accent_class = f"bg-{accent}-500"
    
    fallback_sections = {}
    
    if "hero" in sections:
        fallback_sections["hero"] = {
            "html": f"""
                <section class="min-h-screen flex items-center justify-center {bg_class} px-6 py-20">
                    <div class="max-w-4xl mx-auto text-center">
                        <h1 class="text-5xl md:text-7xl font-bold tracking-tight mb-6">
                            {{{{headline}}}}
                        </h1>
                        <p class="text-xl md:text-2xl text-gray-400 mb-8">
                            {{{{subheadline}}}}
                        </p>
                        <button class="{accent_class} hover:opacity-90 text-white px-8 py-4 rounded-xl font-semibold text-lg transition">
                            {{{{cta_text}}}}
                        </button>
                    </div>
                </section>
            """,
            "data": {
                "headline": business_name,
                "subheadline": "Welcome to our website",
                "cta_text": "Get Started"
            }
        }
    
    # Add other fallback sections as needed...
    
    return {
        "business_name": business_name,
        "sections": fallback_sections,
        "meta": {
            "primary_color": accent,
            "background_style": palette
        }
    }


# ======================================================
# MAIN GENERATION FUNCTION
# ======================================================

def generate_ai_plan(ai_input: Dict[str, Any], version: int = 1) -> Dict[str, Any]:
    """
    Main entry point for AI website generation.
    Now generates complete HTML sections.
    """
    # Extract business info
    prompt = ai_input.get("prompt", "")
    business_name = ai_input.get("business_name", "")
    
    # Infer template
    template = "business"
    if any(word in prompt.lower() for word in ["restaurant", "cafe", "pizza", "burger", "food"]):
        template = "restaurant"
    
    # Generate structure
    structure = generate_ai_structure(
        business_type=template,
        goal=ai_input.get("primary_goal", "Get started"),
        version=version,
        prompt=prompt,
    )
    
    # Generate HTML sections
    html_data = generate_html_sections(
        business_name=business_name or "Your Business",
        prompt=prompt,
        template=template,
        sections=structure["sections"],
        theme=structure["theme"],
    )
    
    return {
        "template": template,
        "structure": structure,
        "content": html_data,
    }