import random
import hashlib
import json
from typing import Dict, Any, List

from app.ai.openai_client import chat_completion


# ======================================================
# DESIGN SYSTEMS & PALETTES
# ======================================================

DESIGN_SYSTEMS = [
    {"id": "glass_luxury", "name": "Glass Luxury", "base": "dark"},
    {"id": "flow_minimal", "name": "Flow Minimal", "base": "light"},
    {"id": "vibrant_depth", "name": "Vibrant Depth", "base": "dark"},
]

COLOR_PALETTES = {
    "midnight_purple": {
        "name": "Midnight Purple",
        "primary": "from-purple-600 via-indigo-600 to-purple-700",
        "accent": "purple-500",
        "bg_dark": "from-purple-950 via-indigo-950 to-black",
        "bg_light": "from-purple-50 via-indigo-50 to-white",
        "glow": "purple-500/30",
        "card_bg": "bg-white/5",
    },
    "ocean_deep": {
        "name": "Ocean Deep",
        "primary": "from-cyan-500 via-blue-600 to-cyan-700",
        "accent": "cyan-400",
        "bg_dark": "from-cyan-950 via-blue-950 to-black",
        "bg_light": "from-cyan-50 via-blue-50 to-white",
        "glow": "cyan-500/30",
        "card_bg": "bg-white/5",
    },
    "sunset_fire": {
        "name": "Sunset Fire",
        "primary": "from-orange-500 via-rose-600 to-pink-600",
        "accent": "orange-500",
        "bg_dark": "from-orange-950 via-rose-950 to-black",
        "bg_light": "from-orange-50 via-rose-50 to-white",
        "glow": "orange-500/30",
        "card_bg": "bg-white/5",
    },
    "emerald_forest": {
        "name": "Emerald Forest",
        "primary": "from-emerald-600 via-teal-600 to-green-600",
        "accent": "emerald-500",
        "bg_dark": "from-emerald-950 via-teal-950 to-black",
        "bg_light": "from-emerald-50 via-teal-50 to-white",
        "glow": "emerald-500/30",
        "card_bg": "bg-white/5",
    },
    "slate_pro": {
        "name": "Slate Pro",
        "primary": "from-slate-700 via-gray-800 to-slate-900",
        "accent": "slate-600",
        "bg_dark": "from-black via-slate-950 to-gray-900",
        "bg_light": "from-white via-slate-50 to-gray-100",
        "glow": "slate-500/30",
        "card_bg": "bg-white/5",
    },
}


def stable_seed(*values: str) -> int:
    raw = "|".join([v or "" for v in values])
    return int(hashlib.sha256(raw.encode()).hexdigest()[:8], 16)


# ======================================================
# STRUCTURE GENERATION
# ======================================================

def generate_ai_structure(business_type: str, goal: str, version: int = 1, prompt: str = ""):
    bt = (business_type or "business").lower().strip()
    if bt not in ("restaurant", "business"):
        bt = "business"

    if prompt.strip():
        rng = random.Random(stable_seed(bt, goal or "", prompt, str(version)))
    else:
        rng = random.Random()

    design = rng.choice(DESIGN_SYSTEMS)
    palette_key = rng.choice(list(COLOR_PALETTES.keys()))
    palette = COLOR_PALETTES[palette_key]

    sections = ["hero", "features", "social_proof", "cta"]

    return {
        "sections": sections,
        "design": design,
        "palette": palette,
        "palette_key": palette_key,
        "html_mode": True,
        "modern_flow": True,
    }


# ======================================================
# FLOWING, BLENDING SECTIONS (NO MORE BOXY!)
# ======================================================

def generate_flowing_website(
    business_name: str,
    prompt: str,
    sections: List[str],
    structure: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Creates sections that FLOW and BLEND seamlessly.
    Uses negative margins, overlapping elements, gradient transitions.
    """
    design = structure["design"]
    palette = structure["palette"]
    is_dark = design["base"] == "dark"

    bg = palette["bg_dark"] if is_dark else palette["bg_light"]
    text = "text-white" if is_dark else "text-black"
    text_muted = "text-gray-400" if is_dark else "text-gray-600"
    primary = palette["primary"]
    accent = palette["accent"]
    glow = palette["glow"]
    card_bg = palette["card_bg"]

    flowing_sections = {}

    # ============================================
    # HERO - Full screen with animated background
    # ============================================
    flowing_sections["hero"] = {
        "html": f"""
<section class="relative min-h-screen flex items-center justify-center overflow-hidden bg-gradient-to-br {bg}">
    <!-- Animated background orbs -->
    <div class="absolute inset-0 overflow-hidden">
        <div class="absolute top-1/4 left-1/4 w-[800px] h-[800px] bg-{accent} rounded-full blur-3xl opacity-20 animate-pulse"></div>
        <div class="absolute bottom-1/4 right-1/4 w-[800px] h-[800px] bg-gradient-to-r {primary} rounded-full blur-3xl opacity-20 animate-pulse" style="animation-delay: 1s"></div>
        <div class="absolute inset-0 bg-[linear-gradient(rgba(255,255,255,0.02)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,0.02)_1px,transparent_1px)] bg-[size:64px_64px]"></div>
    </div>
    
    <div class="relative z-10 max-w-7xl mx-auto px-6 text-center">
        <h1 class="text-6xl md:text-8xl lg:text-9xl font-bold {text} tracking-tight leading-none mb-8 animate-fadeIn">
            <span class="bg-gradient-to-r {primary} bg-clip-text text-transparent">
                {{{{headline}}}}
            </span>
        </h1>
        
        <p class="text-xl md:text-2xl {text_muted} max-w-4xl mx-auto mb-12 leading-relaxed animate-fadeIn" style="animation-delay: 0.2s">
            {{{{subheadline}}}}
        </p>
        
        <button class="group relative px-10 py-5 bg-gradient-to-r {primary} text-white rounded-2xl font-semibold text-lg overflow-hidden transition-all hover:scale-105 hover:shadow-2xl shadow-{glow} animate-fadeIn" style="animation-delay: 0.4s">
            <span class="relative z-10">{{{{cta}}}}</span>
            <div class="absolute inset-0 bg-white/20 translate-y-full group-hover:translate-y-0 transition-transform duration-300"></div>
        </button>
    </div>
    
    <!-- Gradient fade to next section -->
    <div class="absolute bottom-0 left-0 right-0 h-32 bg-gradient-to-t from-black/50 to-transparent"></div>
</section>
        """,
        "data": {
            "headline": business_name,
            "subheadline": f"Experience excellence with {business_name}. We deliver quality service that exceeds expectations.",
            "cta": "Get Started Today",
        },
    }

    # ============================================
    # FEATURES - OVERLAPS hero with -mt-32
    # ============================================
    flowing_sections["features"] = {
        "html": f"""
<section class="relative -mt-32 z-20 py-24 bg-gradient-to-b from-transparent via-black/80 to-black">
    <div class="max-w-7xl mx-auto px-6">
        <!-- Floating header card -->
        <div class="backdrop-blur-2xl {card_bg} border border-white/10 rounded-3xl p-12 mb-16 shadow-2xl shadow-{glow}">
            <h2 class="text-4xl md:text-6xl font-bold {text} text-center mb-6">
                {{{{title}}}}
            </h2>
            <p class="text-xl {text_muted} text-center max-w-3xl mx-auto">
                {{{{subtitle}}}}
            </p>
        </div>
        
        <!-- Feature cards with stagger animation -->
        <div class="grid md:grid-cols-3 gap-8">
            <div class="backdrop-blur-xl {card_bg} border border-white/10 rounded-3xl p-8 hover:scale-105 hover:border-white/20 transition-all duration-300 group">
                <div class="w-16 h-16 bg-gradient-to-r {primary} rounded-2xl flex items-center justify-center mb-6 shadow-lg shadow-{glow} group-hover:scale-110 transition-transform">
                    <svg class="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"/>
                    </svg>
                </div>
                <h3 class="text-2xl font-bold {text} mb-4">{{{{feature1_title}}}}</h3>
                <p class="{text_muted} leading-relaxed">{{{{feature1_desc}}}}</p>
            </div>
            
            <div class="backdrop-blur-xl {card_bg} border border-white/10 rounded-3xl p-8 hover:scale-105 hover:border-white/20 transition-all duration-300 group" style="animation-delay: 0.1s">
                <div class="w-16 h-16 bg-gradient-to-r {primary} rounded-2xl flex items-center justify-center mb-6 shadow-lg shadow-{glow} group-hover:scale-110 transition-transform">
                    <svg class="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/>
                    </svg>
                </div>
                <h3 class="text-2xl font-bold {text} mb-4">{{{{feature2_title}}}}</h3>
                <p class="{text_muted} leading-relaxed">{{{{feature2_desc}}}}</p>
            </div>
            
            <div class="backdrop-blur-xl {card_bg} border border-white/10 rounded-3xl p-8 hover:scale-105 hover:border-white/20 transition-all duration-300 group" style="animation-delay: 0.2s">
                <div class="w-16 h-16 bg-gradient-to-r {primary} rounded-2xl flex items-center justify-center mb-6 shadow-lg shadow-{glow} group-hover:scale-110 transition-transform">
                    <svg class="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 3v4M3 5h4M6 17v4m-2-2h4m5-16l2.286 6.857L21 12l-5.714 2.143L13 21l-2.286-6.857L5 12l5.714-2.143L13 3z"/>
                    </svg>
                </div>
                <h3 class="text-2xl font-bold {text} mb-4">{{{{feature3_title}}}}</h3>
                <p class="{text_muted} leading-relaxed">{{{{feature3_desc}}}}</p>
            </div>
        </div>
    </div>
</section>
        """,
        "data": {
            "title": "Why Choose Us",
            "subtitle": "We provide exceptional service backed by years of experience",
            "feature1_title": "Lightning Fast",
            "feature1_desc": "Quick turnaround times without compromising on quality",
            "feature2_title": "Trusted by Thousands",
            "feature2_desc": "Join our community of satisfied customers",
            "feature3_title": "Premium Quality",
            "feature3_desc": "Best-in-class service at competitive prices",
        },
    }

    # ============================================
    # SOCIAL PROOF - Seamless transition
    # ============================================
    flowing_sections["social_proof"] = {
        "html": f"""
<section class="relative py-32 bg-gradient-to-b from-black to-black/80">
    <!-- Decorative gradient orb -->
    <div class="absolute top-0 left-1/2 -translate-x-1/2 w-[600px] h-[600px] bg-gradient-to-r {primary} rounded-full blur-3xl opacity-10"></div>
    
    <div class="relative z-10 max-w-7xl mx-auto px-6">
        <div class="text-center mb-20">
            <h2 class="text-4xl md:text-6xl font-bold {text} mb-6">
                {{{{title}}}}
            </h2>
            <p class="text-xl {text_muted}">Join thousands of happy customers</p>
        </div>
        
        <div class="grid md:grid-cols-3 gap-12">
            <div class="text-center group">
                <div class="text-6xl md:text-7xl font-bold bg-gradient-to-r {primary} bg-clip-text text-transparent mb-4 group-hover:scale-110 transition-transform">
                    {{{{stat1_number}}}}
                </div>
                <p class="text-xl {text_muted}">{{{{stat1_label}}}}</p>
            </div>
            
            <div class="text-center group">
                <div class="text-6xl md:text-7xl font-bold bg-gradient-to-r {primary} bg-clip-text text-transparent mb-4 group-hover:scale-110 transition-transform">
                    {{{{stat2_number}}}}
                </div>
                <p class="text-xl {text_muted}">{{{{stat2_label}}}}</p>
            </div>
            
            <div class="text-center group">
                <div class="text-6xl md:text-7xl font-bold bg-gradient-to-r {primary} bg-clip-text text-transparent mb-4 group-hover:scale-110 transition-transform">
                    {{{{stat3_number}}}}
                </div>
                <p class="text-xl {text_muted}">{{{{stat3_label}}}}</p>
            </div>
        </div>
    </div>
</section>
        """,
        "data": {
            "title": "Trusted Worldwide",
            "stat1_number": "10K+",
            "stat1_label": "Happy Customers",
            "stat2_number": "99%",
            "stat2_label": "Satisfaction Rate",
            "stat3_number": "24/7",
            "stat3_label": "Support Available",
        },
    }

    # ============================================
    # CTA - Final section with gradient fade
    # ============================================
    flowing_sections["cta"] = {
        "html": f"""
<section class="relative py-40 bg-gradient-to-b from-black/80 via-black to-{bg.split()[0].replace('from-', '')}">
    <!-- Background gradient orbs -->
    <div class="absolute inset-0 overflow-hidden">
        <div class="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[1000px] h-[1000px] bg-gradient-to-r {primary} rounded-full blur-3xl opacity-20"></div>
    </div>
    
    <div class="relative z-10 max-w-5xl mx-auto px-6 text-center">
        <h2 class="text-5xl md:text-7xl font-bold {text} mb-8">
            {{{{headline}}}}
        </h2>
        <p class="text-2xl {text_muted} mb-12 max-w-3xl mx-auto leading-relaxed">
            {{{{subheadline}}}}
        </p>
        <button class="group px-12 py-6 bg-gradient-to-r {primary} text-white rounded-2xl font-bold text-xl hover:scale-105 transition-all shadow-2xl shadow-{glow} relative overflow-hidden">
            <span class="relative z-10">{{{{cta}}}}</span>
            <div class="absolute inset-0 bg-white/20 translate-x-full group-hover:translate-x-0 transition-transform duration-300"></div>
        </button>
    </div>
</section>
        """,
        "data": {
            "headline": "Ready to Get Started?",
            "subheadline": "Join thousands of satisfied customers and experience the difference",
            "cta": "Start Your Journey Today",
        },
    }

    return {
        "business_name": business_name,
        "sections": flowing_sections,
        "seo": {
            "title": f"{business_name} - Professional Services",
            "description": f"Discover {business_name}, your trusted partner for professional services.",
            "keywords": ["professional", "quality", "trusted", "service"],
        },
    }


# ======================================================
# MAIN FUNCTIONS
# ======================================================

def generate_html_sections(business_name: str, prompt: str, business_type: str, structure: Dict[str, Any]) -> Dict[str, Any]:
    """Try REAL AI, fallback if it fails."""
    design = structure["design"]
    palette = structure["palette"]
    sections = structure["sections"]

    ai_prompt = f"""Create a flowing website for: {business_name}

Description: {prompt}
Style: {design['name']}  
Colors: {palette['name']} - Primary: {palette['primary']}, Accent: {palette['accent']}

Generate JSON:
{{
  "business_name": "{business_name}",
  "sections": {{
    "hero": {{"html": "<section class='relative min-h-screen bg-gradient-to-br...'>HTML</section>", "data": {{"headline": "...", "subheadline": "...", "cta": "..."}}}},
    "features": {{"html": "<section class='relative -mt-32 z-20...'>OVERLAPPING HTML</section>", "data": {{"title": "...", "feature1_title": "...", "feature1_desc": "...", "feature2_title": "...", "feature2_desc": "...", "feature3_title": "...", "feature3_desc": "..."}}}},
    "social_proof": {{"html": "<section class='py-32...'>STATS</section>", "data": {{"title": "...", "stat1_number": "...", "stat1_label": "...", "stat2_number": "...", "stat2_label": "...", "stat3_number": "...", "stat3_label": "..."}}}},
    "cta": {{"html": "<section class='py-40...'>CTA</section>", "data": {{"headline": "...", "subheadline": "...", "cta": "..."}}}}
  }}
}}

CRITICAL: Sections MUST overlap with -mt-32. Use exact color classes. Real business copy."""

    print("=== 🤖 Trying AI generation ===")
    
    try:
        response = chat_completion(
            system="Expert web designer. Return ONLY JSON. Make sections OVERLAP.",
            user=ai_prompt,
            temperature=0.9,
        )
        
        parsed = json.loads(response)
        
        if not parsed.get("sections") or len(parsed["sections"]) < 3:
            raise ValueError("Invalid response")
        
        if "seo" not in parsed:
            parsed["seo"] = {"title": f"{business_name}", "description": f"{business_name}", "keywords": [business_type]}
        
        print(f"=== ✅ AI SUCCESS! {len(parsed['sections'])} sections ===")
        return parsed
        
    except Exception as e:
        print(f"=== ⚠️ AI failed: {e} - Using fallback ===")
        return generate_flowing_website(business_name, prompt, sections, structure)


def rewrite_content(original_text: str, tone: str = "professional", business_context: str = "") -> List[str]:
    try:
        prompt = f"Rewrite: {original_text}\nTone: {tone}\nReturn JSON: [\"v1\", \"v2\", \"v3\"]"
        response = chat_completion(system="Copywriter. JSON only.", user=prompt, temperature=0.8)
        alternatives = json.loads(response)
        return alternatives[:3] if isinstance(alternatives, list) else [original_text] * 3
    except:
        return [original_text] * 3


def generate_ai_plan(ai_input: Dict[str, Any], version: int = 1) -> Dict[str, Any]:
    prompt = ai_input.get("prompt", "")
    business_name = ai_input.get("business_name", "Your Business")
    goal = ai_input.get("primary_goal", "Get started")

    business_type = "business"
    if any(w in prompt.lower() for w in ["restaurant", "cafe", "food", "pizza"]):
        business_type = "restaurant"

    structure = generate_ai_structure(business_type, goal, version, prompt)
    content = generate_html_sections(business_name, prompt, business_type, structure)

    return {"template": business_type, "structure": structure, "content": content}