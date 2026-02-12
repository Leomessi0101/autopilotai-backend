import random
import hashlib
import re
import json
from typing import Dict, Any, List, Tuple, Optional

from app.ai.openai_client import chat_completion


# ======================================================
# SECTION LIBRARY - Pre-built templates users can add
# ======================================================

SECTION_LIBRARY = {
    "testimonials": {
        "name": "Testimonials",
        "description": "Customer reviews and feedback",
        "category": "social_proof",
    },
    "pricing": {
        "name": "Pricing",
        "description": "Pricing plans and packages",
        "category": "conversion",
    },
    "team": {
        "name": "Team",
        "description": "Meet the team members",
        "category": "about",
    },
    "stats": {
        "name": "Statistics",
        "description": "Numbers and achievements",
        "category": "social_proof",
    },
    "newsletter": {
        "name": "Newsletter",
        "description": "Email signup form",
        "category": "conversion",
    },
    "brands": {
        "name": "Trusted By",
        "description": "Logo wall of clients/partners",
        "category": "social_proof",
    },
}

# ======================================================
# DESIGN STYLES - Multiple variations for same content
# ======================================================

DESIGN_STYLES = [
    {
        "id": "modern",
        "name": "Modern",
        "description": "Clean, minimalist, lots of white space",
        "characteristics": "large typography, subtle shadows, rounded corners, gradient accents",
    },
    {
        "id": "bold",
        "name": "Bold",
        "description": "High contrast, dramatic, eye-catching",
        "characteristics": "vibrant colors, sharp edges, strong typography, dark backgrounds",
    },
    {
        "id": "warm",
        "name": "Warm",
        "description": "Friendly, approachable, inviting",
        "characteristics": "warm colors, soft shadows, organic shapes, welcoming tone",
    },
    {
        "id": "minimal",
        "name": "Minimal",
        "description": "Ultra-clean, focused, distraction-free",
        "characteristics": "monochrome, lots of negative space, simple typography, no decorations",
    },
    {
        "id": "premium",
        "name": "Premium",
        "description": "Luxury, elegant, sophisticated",
        "characteristics": "elegant typography, gold accents, subtle animations, refined spacing",
    },
]

# ======================================================
# THEMES - Color palettes
# ======================================================

COLOR_THEMES = [
    {"id": "indigo", "name": "Indigo", "primary": "indigo-500", "dark": True},
    {"id": "emerald", "name": "Emerald", "primary": "emerald-500", "dark": False},
    {"id": "orange", "name": "Orange", "primary": "orange-500", "dark": False},
    {"id": "purple", "name": "Purple", "primary": "purple-500", "dark": True},
    {"id": "blue", "name": "Blue", "primary": "blue-500", "dark": False},
    {"id": "rose", "name": "Rose", "primary": "rose-500", "dark": False},
    {"id": "neutral", "name": "Neutral", "primary": "neutral-800", "dark": False},
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


# ======================================================
# ENHANCED STRUCTURE GENERATION
# ======================================================

def generate_ai_structure(
    business_type: str,
    goal: str,
    version: int = 1,
    prompt: str = "",
    style_preference: str = None,
):
    """
    Generates varied structure with design style support.
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
        if sections[-1] == "contact":
            sections.insert(-1, "cta")
        else:
            sections.append("cta")

    # Design style
    if style_preference and any(s["id"] == style_preference for s in DESIGN_STYLES):
        style = next(s for s in DESIGN_STYLES if s["id"] == style_preference)
    else:
        style = rng.choice(DESIGN_STYLES)

    # Color theme
    theme = rng.choice(COLOR_THEMES)

    return {
        "sections": sections,
        "style": {
            "id": style["id"],
            "name": style["name"],
            "characteristics": style["characteristics"],
        },
        "theme": {
            "id": theme["id"],
            "name": theme["name"],
            "primary": theme["primary"],
            "dark_mode": theme["dark"],
        },
        "html_mode": True,
        "animations_enabled": True,
    }


# ======================================================
# STYLE VARIATIONS GENERATOR
# ======================================================

def generate_style_variations(
    business_name: str,
    prompt: str,
    template: str,
    sections: List[str],
) -> List[Dict[str, Any]]:
    """
    Generates 3 different style variations of the same website.
    Returns list of complete website data with different designs.
    """
    variations = []
    
    # Pick 3 different styles
    styles_to_generate = random.sample(DESIGN_STYLES, min(3, len(DESIGN_STYLES)))
    
    for style in styles_to_generate:
        # Generate structure with this style
        structure = generate_ai_structure(
            business_type=template,
            goal="Get started",
            prompt=prompt,
            style_preference=style["id"],
        )
        
        # Generate HTML with this style
        html_data = generate_html_sections(
            business_name=business_name,
            prompt=prompt,
            template=template,
            sections=sections,
            structure=structure,
        )
        
        variations.append({
            "style": style,
            "structure": structure,
            "content": html_data,
        })
    
    return variations


# ======================================================
# AI HTML GENERATION WITH STYLE AWARENESS
# ======================================================

HTML_SYSTEM_PROMPT = """You are an expert web designer and developer specializing in creating beautiful, unique landing pages.

You generate complete HTML sections using Tailwind CSS classes. Each website should feel COMPLETELY DIFFERENT from others.

KEY RULES:
1. Return ONLY valid JSON (no markdown, no commentary)
2. Generate complete HTML with Tailwind classes for each section
3. Make each layout UNIQUE based on the design style provided
4. Use the theme palette and accent color provided
5. Be creative with layouts - vary everything based on style
6. Ensure mobile responsiveness with Tailwind's responsive classes
7. Never use placeholder text - generate real, business-specific copy
8. Include proper semantic HTML tags
9. Make it look PREMIUM and MODERN
10. DO NOT add any image placeholders - users will add images separately
11. Apply the design style characteristics consistently

DESIGN STYLE GUIDELINES:
- Modern: Clean, minimalist, large typography, subtle shadows, rounded-2xl corners, gradient accents
- Bold: High contrast, sharp edges (rounded-none or rounded-sm), vibrant colors, strong typography, dark backgrounds
- Warm: Warm colors (amber, orange hues), soft shadows, rounded-3xl corners, welcoming tone, gentle gradients
- Minimal: Monochrome, excessive negative space, simple sans-serif, no decorations, ultra-clean
- Premium: Elegant serif fonts mix, gold/silver accents, subtle animations, refined spacing, luxury feel

LAYOUT VARIETY TECHNIQUES:
- Vary grid columns: grid-cols-1, grid-cols-2, grid-cols-3, md:grid-cols-2, lg:grid-cols-3
- Mix alignments: items-start, items-center, items-end
- Different card styles based on style (sharp vs rounded)
- Varied spacing: gap-4, gap-6, gap-8, gap-10, gap-12
- Asymmetric layouts: split 2/3 and 1/3, or 1/2 and 1/2
- Different text alignments: text-left, text-center
- Varied padding: p-6, p-8, p-10, p-12
- Background variations: bg-white/5, bg-black/20, gradient backgrounds
"""

HTML_USER_PROMPT = """Business: {business_name}
Description: {prompt}
Type: {template}

DESIGN STYLE: {style_name}
Style Characteristics: {style_characteristics}

Theme: {theme_name}
Primary Color: {primary_color}
Dark Mode: {dark_mode}

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
  "seo": {{
    "meta_description": "compelling 150-160 char description",
    "keywords": ["keyword1", "keyword2", "keyword3"]
  }}
}}

IMPORTANT:
- Apply the {style_name} style characteristics throughout
- Use {primary_color} as the primary accent color
- For dark_mode={dark_mode}: use dark backgrounds if True, light if False
- Make each section visually DISTINCT
- Vary the layout structure for each section
- Use semantic HTML
- Mobile-first responsive design
- NO placeholder text - make it specific to the business
- Generate compelling, conversion-focused copy
- Include SEO metadata
"""


def generate_html_sections(
    business_name: str,
    prompt: str,
    template: str,
    sections: List[str],
    structure: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Generates complete HTML for each section using AI with style awareness.
    """
    style = structure.get("style", {})
    theme = structure.get("theme", {})
    
    try:
        response = chat_completion(
            system=HTML_SYSTEM_PROMPT,
            user=HTML_USER_PROMPT.format(
                business_name=business_name,
                prompt=prompt,
                template=template,
                sections=", ".join(sections),
                style_name=style.get("name", "Modern"),
                style_characteristics=style.get("characteristics", "clean and minimal"),
                theme_name=theme.get("name", "Indigo"),
                primary_color=theme.get("primary", "indigo-500"),
                dark_mode=theme.get("dark_mode", True),
            ),
            temperature=0.9,
        )
        
        parsed = json.loads(response)
        
        if not isinstance(parsed, dict):
            raise ValueError("Invalid response structure")
        
        if "sections" not in parsed or not isinstance(parsed["sections"], dict):
            raise ValueError("Missing sections in response")
        
        # Add SEO if not present
        if "seo" not in parsed:
            parsed["seo"] = {
                "meta_description": f"{business_name} - Quality service you can trust.",
                "keywords": [template, "professional", "reliable"],
            }
        
        return parsed
        
    except Exception as e:
        print(f"HTML generation failed: {str(e)}")
        return generate_fallback_html(business_name, sections, structure)


def generate_fallback_html(
    business_name: str,
    sections: List[str],
    structure: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Fallback HTML generator if AI fails.
    """
    theme = structure.get("theme", {})
    primary = theme.get("primary", "indigo-500")
    is_dark = theme.get("dark_mode", True)
    
    bg_class = "bg-black text-white" if is_dark else "bg-white text-black"
    accent_class = f"bg-{primary}"
    
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
    
    return {
        "business_name": business_name,
        "sections": fallback_sections,
        "seo": {
            "meta_description": f"{business_name} - Quality service you can trust.",
            "keywords": ["business", "professional", "reliable"],
        }
    }


# ======================================================
# CONTENT REWRITER
# ======================================================

def rewrite_content(
    original_text: str,
    tone: str = "professional",
    business_context: str = "",
) -> List[str]:
    """
    Generates 3 alternative versions of text content.
    Tones: professional, casual, persuasive
    """
    prompt = f"""Rewrite this text in a {tone} tone. Generate 3 different versions.

Original text: {original_text}

Business context: {business_context}

Return ONLY a JSON array of 3 alternative versions:
["version 1", "version 2", "version 3"]

Each version should:
- Be {tone} in tone
- Maintain the core message
- Be slightly different from each other
- Be compelling and clear
"""

    try:
        response = chat_completion(
            system="You are an expert copywriter. Return only valid JSON arrays.",
            user=prompt,
            temperature=0.8,
        )
        
        alternatives = json.loads(response)
        
        if isinstance(alternatives, list) and len(alternatives) >= 3:
            return alternatives[:3]
        
        return [original_text] * 3
        
    except Exception:
        return [original_text] * 3


# ======================================================
# MAIN GENERATION FUNCTION
# ======================================================

def generate_ai_plan(ai_input: Dict[str, Any], version: int = 1) -> Dict[str, Any]:
    """
    Main entry point for AI website generation.
    Now generates complete HTML sections with style awareness.
    """
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
        structure=structure,
    )
    
    return {
        "template": template,
        "structure": structure,
        "content": html_data,
    }