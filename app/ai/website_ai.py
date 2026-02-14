import random
import hashlib
import json
from typing import Dict, Any, List, Tuple

from app.ai.openai_client import chat_completion


# ======================================================
# THEME SYSTEM (for frontend dynamic colors)
# ======================================================

THEME_PALETTE_VALUES = ("light", "dark")
THEME_ACCENT_VALUES = ("indigo", "emerald", "orange", "neutral", "violet", "rose")
HERO_VARIANTS = ("split_image", "centered_text", "image_background", "minimal")
FOOTER_VARIANTS = ("minimal", "standard")

# Section presets by business type
SECTION_PRESETS: Dict[str, List[str]] = {
    "restaurant": ["hero", "about", "menu", "gallery", "contact"],
    "cafe": ["hero", "about", "menu", "testimonial", "contact"],
    "bar": ["hero", "about", "gallery", "contact"],
    "law": ["hero", "about", "services", "trust", "contact"],
    "clinic": ["hero", "about", "services", "process", "contact"],
    "salon": ["hero", "about", "services", "gallery", "testimonial", "contact"],
    "saas": ["hero", "features", "pricing", "cta", "contact"],
    "agency": ["hero", "about", "services", "portfolio", "testimonial", "contact"],
    "default": ["hero", "features", "social_proof", "cta"],
}

def _infer_business_type(prompt: str) -> str:
    p = (prompt or "").lower()
    if any(w in p for w in ["restaurant", "restaurants", "dining", "food", "pizza", "bistro"]):
        return "restaurant"
    if any(w in p for w in ["cafe", "coffee", "bakery"]):
        return "cafe"
    if any(w in p for w in ["bar", "pub", "brewery"]):
        return "bar"
    if any(w in p for w in ["law", "lawyer", "legal", "attorney"]):
        return "law"
    if any(w in p for w in ["clinic", "doctor", "medical", "health"]):
        return "clinic"
    if any(w in p for w in ["salon", "spa", "beauty", "hair"]):
        return "salon"
    if any(w in p for w in ["saas", "software", "app", "platform", "startup"]):
        return "saas"
    if any(w in p for w in ["agency", "marketing", "creative", "design studio"]):
        return "agency"
    return "default"


# ======================================================
# INTERNAL COLOR PALETTES (for HTML generation)
# ======================================================

COLOR_PALETTES = {
    "midnight_purple": {
        "name": "Midnight Purple",
        "primary": "from-indigo-500 to-purple-500",
        "accent": "indigo-500",
        "bg_dark": "from-purple-950 via-indigo-950 to-black",
        "bg_light": "from-purple-50 via-indigo-50 to-white",
        "glow": "indigo-500/30",
    },
    "ocean_deep": {
        "name": "Ocean Deep",
        "primary": "from-cyan-500 to-blue-500",
        "accent": "cyan-500",
        "bg_dark": "from-cyan-950 via-blue-950 to-black",
        "bg_light": "from-cyan-50 via-blue-50 to-white",
        "glow": "cyan-500/30",
    },
    "sunset_fire": {
        "name": "Sunset Fire",
        "primary": "from-orange-500 to-pink-500",
        "accent": "orange-500",
        "bg_dark": "from-orange-950 via-rose-950 to-black",
        "bg_light": "from-orange-50 via-rose-50 to-white",
        "glow": "orange-500/30",
    },
    "emerald_forest": {
        "name": "Emerald Forest",
        "primary": "from-emerald-600 to-teal-600",
        "accent": "emerald-500",
        "bg_dark": "from-emerald-950 via-teal-950 to-black",
        "bg_light": "from-emerald-50 via-teal-50 to-white",
        "glow": "emerald-500/30",
    },
    "slate_pro": {
        "name": "Slate Pro",
        "primary": "from-slate-700 to-gray-800",
        "accent": "slate-600",
        "bg_dark": "from-black via-slate-950 to-gray-900",
        "bg_light": "from-white via-slate-50 to-gray-100",
        "glow": "slate-500/30",
    },
}

ACCENT_TO_PALETTE_KEY: Dict[str, str] = {
    "indigo": "midnight_purple",
    "emerald": "emerald_forest",
    "orange": "sunset_fire",
    "neutral": "slate_pro",
    "violet": "midnight_purple",
    "rose": "sunset_fire",
}

SECTION_KEY_TO_TEMPLATE: Dict[str, str] = {
    "hero": "hero",
    "features": "features",
    "about": "features",
    "services": "features",
    "process": "features",
    "team": "features",
    "portfolio": "features",
    "menu": "features",
    "social_proof": "social_proof",
    "testimonial": "social_proof",
    "gallery": "social_proof",
    "trust": "social_proof",
    "cta": "cta",
    "contact": "cta",
    "location": "cta",
    "pricing": "features",
    "faq": "features",
}


def stable_seed(*values: str) -> int:
    raw = "|".join([v or "" for v in values])
    return int(hashlib.sha256(raw.encode()).hexdigest()[:8], 16)


# ======================================================
# STRUCTURE GENERATION
# ======================================================

def _choose_theme_and_variants(prompt: str, business_type: str, rng: random.Random) -> Tuple[str, str, str, str]:
    """Returns (palette, accent, hero_variant, footer_variant)."""
    dark_biased = business_type in ("restaurant", "bar", "agency")
    light_biased = business_type in ("clinic", "cafe", "law")
    
    if dark_biased:
        palette = "dark" if rng.random() < 0.7 else "light"
    elif light_biased:
        palette = "light" if rng.random() < 0.7 else "dark"
    else:
        palette = rng.choice(list(THEME_PALETTE_VALUES))
    
    accent = rng.choice(list(THEME_ACCENT_VALUES))
    hero_variant = rng.choice(list(HERO_VARIANTS))
    footer_variant = rng.choice(list(FOOTER_VARIANTS))
    
    return palette, accent, hero_variant, footer_variant


def generate_ai_structure(business_type: str, goal: str, version: int = 1, prompt: str = ""):
    bt = (business_type or "business").lower().strip()
    if bt not in ("restaurant", "business"):
        bt = "business"

    seed_prompt = (prompt or "").strip()
    if seed_prompt:
        rng = random.Random(stable_seed(bt, goal or "", seed_prompt, str(version)))
    else:
        rng = random.Random()

    inferred = _infer_business_type(seed_prompt)
    section_list = list(SECTION_PRESETS.get(inferred, SECTION_PRESETS["default"]))
    
    if rng.random() < 0.2 and len(section_list) > 3:
        section_list = section_list[:-1]

    palette_light_dark, accent, hero_variant, footer_variant = _choose_theme_and_variants(seed_prompt, inferred, rng)

    palette_key = ACCENT_TO_PALETTE_KEY.get(accent, "midnight_purple")
    palette = COLOR_PALETTES[palette_key]

    return {
        "theme": {"palette": palette_light_dark, "accent": accent},
        "hero": {"variant": hero_variant},
        "footer": {"variant": footer_variant},
        "sections": section_list,
        "palette": palette,
        "palette_key": palette_key,
        "html_mode": True,
        "modern_flow": True,
    }


# ======================================================
# INDUSTRY-SPECIFIC DEFAULTS
# ======================================================

def _industry_defaults(business_type: str, business_name: str) -> Dict[str, str]:
    by_type: Dict[str, Dict[str, str]] = {
        "restaurant": {
            "hero_subheadline": f"Exceptional dining in an inviting atmosphere. Reserve your table and taste the difference.",
            "hero_cta": "Reserve a Table",
            "contact_headline": "Visit Us",
            "contact_subheadline": "We can't wait to welcome you. Reserve a table or stop by for a memorable experience.",
            "contact_cta": "Reserve Now",
        },
        "cafe": {
            "hero_subheadline": f"Your neighborhood spot for great coffee and fresh bites. Come in and stay awhile.",
            "hero_cta": "View Menu",
            "contact_headline": "Find Us",
            "contact_subheadline": "Drop in for a coffee or message us for catering.",
            "contact_cta": "Get Directions",
        },
        "bar": {
            "hero_subheadline": f"Where great drinks and good times meet. Join us for craft cocktails and a vibe like no other.",
            "hero_cta": "View Hours",
            "contact_headline": "Find Us",
            "contact_subheadline": "Reserve a booth or walk in — we're here for you.",
            "contact_cta": "Get Directions",
        },
        "law": {
            "hero_subheadline": f"Trusted legal counsel when it matters most. Schedule a confidential consultation.",
            "hero_cta": "Schedule Consultation",
            "contact_headline": "Get in Touch",
            "contact_subheadline": "Reach out for a confidential discussion about your case.",
            "contact_cta": "Request a Call",
        },
        "clinic": {
            "hero_subheadline": f"Quality care in a caring environment. Your health and comfort come first.",
            "hero_cta": "Book Appointment",
            "contact_headline": "Contact Us",
            "contact_subheadline": "Schedule a visit or ask us anything.",
            "contact_cta": "Book Now",
        },
        "salon": {
            "hero_subheadline": f"Look and feel your best. Expert stylists and a relaxing experience await.",
            "hero_cta": "Book Appointment",
            "contact_headline": "Visit the Salon",
            "contact_subheadline": "Book your next appointment or drop by for a walk-in.",
            "contact_cta": "Book Now",
        },
        "saas": {
            "hero_subheadline": f"Built to scale with you. Start free and upgrade when you're ready.",
            "hero_cta": "Start Free Trial",
            "contact_headline": "Let's Talk",
            "contact_subheadline": "Questions? Our team is here to help.",
            "contact_cta": "Contact Sales",
        },
        "agency": {
            "hero_subheadline": f"Creative that drives results. Let's build your brand and grow your audience.",
            "hero_cta": "Start a Project",
            "contact_headline": "Work With Us",
            "contact_subheadline": "Tell us about your project and goals.",
            "contact_cta": "Get a Quote",
        },
    }
    return by_type.get(business_type, {
        "hero_subheadline": f"Experience excellence with {business_name}. We deliver quality that exceeds expectations.",
        "hero_cta": "Get Started",
        "contact_headline": "Get in Touch",
        "contact_subheadline": "We'd love to hear from you. Reach out anytime.",
        "contact_cta": "Contact Us",
    })


# ======================================================
# ULTRA-PREMIUM WEBSITE GENERATION
# ======================================================

def generate_premium_website(business_name: str, prompt: str, sections: List[str], structure: Dict[str, Any]) -> Dict[str, Any]:
    """
    MAXIMUM QUALITY: Huge gradient orbs, animations, glassmorphism, industry-appropriate copy.
    """
    palette = structure["palette"]
    theme = structure.get("theme", {})
    is_dark = theme.get("palette", "dark") == "dark"
    inferred = _infer_business_type(prompt)
    industry = _industry_defaults(inferred, business_name)

    bg = palette["bg_dark"] if is_dark else palette["bg_light"]
    text = "text-white" if is_dark else "text-gray-900"
    text_muted = "text-gray-300" if is_dark else "text-gray-600"
    primary = palette["primary"]
    accent = palette["accent"]
    glow = palette["glow"]

    flowing_sections = {}

    # HERO - ULTRA PREMIUM with MASSIVE orbs
    flowing_sections["hero"] = {
        "html": f"""
<section class="relative min-h-screen flex items-center justify-center overflow-hidden bg-gradient-to-br {bg}">
    <!-- MASSIVE ANIMATED GRADIENT ORBS -->
    <div class="absolute inset-0 overflow-hidden">
        <div class="absolute top-1/4 left-1/4 w-[800px] h-[800px] bg-{accent} rounded-full blur-3xl opacity-20 animate-pulse"></div>
        <div class="absolute bottom-1/4 right-1/4 w-[800px] h-[800px] bg-gradient-to-r {primary} rounded-full blur-3xl opacity-20 animate-pulse" style="animation-delay: 1s"></div>
        <div class="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-gradient-to-r {primary} rounded-full blur-[100px] opacity-10"></div>
        <!-- Radial gradient overlay -->
        <div class="absolute inset-0 bg-[radial-gradient(ellipse_80%_50%_at_50%_-20%,rgba(255,255,255,0.08),transparent)]"></div>
        <!-- Film grain texture -->
        <div class="absolute inset-0 opacity-[0.02]" style="background-image: url('data:image/svg+xml,%3Csvg viewBox=\\'0 0 256 256\\' xmlns=\\'http://www.w3.org/2000/svg\\'%3E%3Cfilter id=\\'noise\\'%3E%3CfeTurbulence type=\\'fractalNoise\\' baseFrequency=\\'0.9\\' numOctaves=\\'4\\' stitchTiles=\\'stitch\\'/%3E%3C/filter%3E%3Crect width=\\'100%25\\' height=\\'100%25\\' filter=\\'url(%23noise)\\'/%3E%3C/svg%3E');"></div>
    </div>
    
    <div class="relative z-10 max-w-7xl mx-auto px-6 text-center">
        <h1 class="text-5xl sm:text-6xl md:text-7xl lg:text-8xl xl:text-9xl font-bold {text} tracking-tight leading-[0.95] mb-8" style="letter-spacing: -0.04em;">
            <span class="bg-gradient-to-r {primary} bg-clip-text text-transparent drop-shadow-sm">
                {{{{headline}}}}
            </span>
        </h1>
        
        <p class="text-lg sm:text-xl md:text-2xl {text_muted} max-w-3xl mx-auto mb-12 leading-relaxed">
            {{{{subheadline}}}}
        </p>
        
        <button class="group relative px-10 py-5 bg-gradient-to-r {primary} text-white rounded-2xl font-bold text-lg overflow-hidden hover:scale-105 transition-all duration-300 shadow-2xl shadow-{glow}">
            <span class="relative z-10">{{{{cta}}}}</span>
            <div class="absolute inset-0 bg-white/20 translate-y-full group-hover:translate-y-0 transition-transform duration-300"></div>
        </button>
    </div>
    
    <!-- Scroll indicator -->
    <div class="absolute bottom-8 left-1/2 -translate-x-1/2 z-10 flex flex-col items-center gap-2 opacity-70">
        <span class="text-sm {text_muted}">Scroll</span>
        <div class="w-6 h-10 rounded-full border-2 border-current {text_muted} flex justify-center pt-2">
            <div class="w-1 h-2 rounded-full bg-current animate-bounce"></div>
        </div>
    </div>
</section>
        """,
        "data": {
            "headline": business_name,
            "subheadline": industry["hero_subheadline"],
            "cta": industry["hero_cta"],
        },
    }

    # FEATURES - Glassmorphism with hover lift
    flowing_sections["features"] = {
        "html": f"""
<section class="relative -mt-24 z-20 py-32 bg-gradient-to-b from-transparent via-black/90 to-black">
    <div class="max-w-7xl mx-auto px-6">
        <div class="backdrop-blur-2xl bg-white/5 border border-white/10 rounded-3xl p-12 mb-16 shadow-2xl hover:border-white/20 transition-all duration-500">
            <h2 class="text-4xl md:text-5xl lg:text-6xl font-bold {text} text-center mb-6">
                {{{{title}}}}
            </h2>
            <p class="text-xl {text_muted} text-center max-w-2xl mx-auto">
                {{{{subtitle}}}}
            </p>
        </div>
        
        <div class="grid md:grid-cols-3 gap-8">
            <div class="group relative backdrop-blur-xl bg-white/5 border border-white/10 rounded-3xl p-10 hover:-translate-y-2 hover:border-white/20 hover:shadow-2xl hover:shadow-{glow} transition-all duration-500">
                <div class="absolute inset-0 rounded-3xl bg-gradient-to-r {primary} opacity-0 group-hover:opacity-10 transition-opacity duration-500"></div>
                <div class="relative w-16 h-16 bg-gradient-to-r {primary} rounded-2xl flex items-center justify-center mb-6 shadow-lg group-hover:scale-110 transition-transform duration-300">
                    <svg class="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"/></svg>
                </div>
                <h3 class="relative text-2xl font-bold {text} mb-4">{{{{feature1_title}}}}</h3>
                <p class="relative {text_muted} leading-relaxed">{{{{feature1_desc}}}}</p>
            </div>
            
            <div class="group relative backdrop-blur-xl bg-white/5 border border-white/10 rounded-3xl p-10 hover:-translate-y-2 hover:border-white/20 hover:shadow-2xl hover:shadow-{glow} transition-all duration-500">
                <div class="absolute inset-0 rounded-3xl bg-gradient-to-r {primary} opacity-0 group-hover:opacity-10 transition-opacity duration-500"></div>
                <div class="relative w-16 h-16 bg-gradient-to-r {primary} rounded-2xl flex items-center justify-center mb-6 shadow-lg group-hover:scale-110 transition-transform duration-300">
                    <svg class="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>
                </div>
                <h3 class="relative text-2xl font-bold {text} mb-4">{{{{feature2_title}}}}</h3>
                <p class="relative {text_muted} leading-relaxed">{{{{feature2_desc}}}}</p>
            </div>
            
            <div class="group relative backdrop-blur-xl bg-white/5 border border-white/10 rounded-3xl p-10 hover:-translate-y-2 hover:border-white/20 hover:shadow-2xl hover:shadow-{glow} transition-all duration-500">
                <div class="absolute inset-0 rounded-3xl bg-gradient-to-r {primary} opacity-0 group-hover:opacity-10 transition-opacity duration-500"></div>
                <div class="relative w-16 h-16 bg-gradient-to-r {primary} rounded-2xl flex items-center justify-center mb-6 shadow-lg group-hover:scale-110 transition-transform duration-300">
                    <svg class="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 3v4M3 5h4M6 17v4m-2-2h4m5-16l2.286 6.857L21 12l-5.714 2.143L13 21l-2.286-6.857L5 12l5.714-2.143L13 3z"/></svg>
                </div>
                <h3 class="relative text-2xl font-bold {text} mb-4">{{{{feature3_title}}}}</h3>
                <p class="relative {text_muted} leading-relaxed">{{{{feature3_desc}}}}</p>
            </div>
        </div>
    </div>
</section>
        """,
        "data": {
            "title": "Why Choose Us",
            "subtitle": "We provide exceptional service backed by years of experience",
            "feature1_title": "Lightning Fast",
            "feature1_desc": "Quick turnaround times without compromising on quality or attention to detail.",
            "feature2_title": "Trusted by Thousands",
            "feature2_desc": "Join our community of satisfied customers who trust our proven expertise.",
            "feature3_title": "Premium Quality",
            "feature3_desc": "Best-in-class service at competitive prices. Excellence is our standard.",
        },
    }

    # SOCIAL PROOF - Gradient numbers with hover scale
    flowing_sections["social_proof"] = {
        "html": f"""
<section class="relative py-32 overflow-hidden">
    <div class="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[800px] bg-gradient-to-r {primary} rounded-full blur-[150px] opacity-15"></div>
    
    <div class="relative z-10 max-w-7xl mx-auto px-6">
        <div class="text-center mb-20">
            <h2 class="text-4xl md:text-5xl lg:text-6xl font-bold {text} mb-4">
                {{{{title}}}}
            </h2>
            <p class="text-xl {text_muted}">What people say about us</p>
        </div>
        
        <div class="grid md:grid-cols-3 gap-12">
            <div class="text-center group hover:scale-105 transition-transform duration-300">
                <div class="text-6xl md:text-7xl font-bold bg-gradient-to-r {primary} bg-clip-text text-transparent mb-3">
                    {{{{stat1_number}}}}
                </div>
                <p class="text-lg {text_muted}">{{{{stat1_label}}}}</p>
            </div>
            
            <div class="text-center group hover:scale-105 transition-transform duration-300">
                <div class="text-6xl md:text-7xl font-bold bg-gradient-to-r {primary} bg-clip-text text-transparent mb-3">
                    {{{{stat2_number}}}}
                </div>
                <p class="text-lg {text_muted}">{{{{stat2_label}}}}</p>
            </div>
            
            <div class="text-center group hover:scale-105 transition-transform duration-300">
                <div class="text-6xl md:text-7xl font-bold bg-gradient-to-r {primary} bg-clip-text text-transparent mb-3">
                    {{{{stat3_number}}}}
                </div>
                <p class="text-lg {text_muted}">{{{{stat3_label}}}}</p>
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

    # CTA - Final section with industry CTAs
    flowing_sections["cta"] = {
        "html": f"""
<section id="contact" class="relative py-40 overflow-hidden">
    <div class="absolute inset-0 bg-gradient-to-b from-black via-black/95 to-black"></div>
    <div class="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[1000px] h-[800px] bg-gradient-to-r {primary} rounded-full blur-[140px] opacity-25"></div>
    
    <div class="relative z-10 max-w-4xl mx-auto px-6 text-center">
        <h2 class="text-4xl md:text-6xl lg:text-7xl font-bold {text} mb-6 leading-tight">
            {{{{headline}}}}
        </h2>
        <p class="text-xl {text_muted} mb-12 max-w-2xl mx-auto leading-relaxed">
            {{{{subheadline}}}}
        </p>
        <button class="group px-12 py-6 bg-gradient-to-r {primary} text-white rounded-2xl font-bold text-xl hover:scale-105 transition-all duration-300 shadow-2xl shadow-{glow}">
            <span class="relative z-10">{{{{cta}}}}</span>
            <div class="absolute inset-0 bg-white/20 opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
        </button>
    </div>
</section>
        """,
        "data": {
            "headline": industry["contact_headline"],
            "subheadline": industry["contact_subheadline"],
            "cta": industry["contact_cta"],
        },
    }

    # Map sections to templates
    template_defaults = {
        "hero": flowing_sections["hero"]["data"],
        "features": flowing_sections["features"]["data"],
        "social_proof": flowing_sections["social_proof"]["data"],
        "cta": flowing_sections["cta"]["data"],
    }

    section_overrides = {
        "about": {"title": "Our Story", "subtitle": f"Learn more about {business_name} and what makes us different.", "feature1_title": "Our Story", "feature1_desc": "Dedicated to excellence.", "feature2_title": "Our Values", "feature2_desc": "Quality and care.", "feature3_title": "Our Mission", "feature3_desc": "Serving you with the best."},
        "menu": {"title": "Our Menu", "subtitle": "Fresh ingredients, bold flavors.", "feature1_title": "Signature Dishes", "feature1_desc": "Chef favorites and classics.", "feature2_title": "Seasonal Picks", "feature2_desc": "Best of the season.", "feature3_title": "Specials", "feature3_desc": "Limited-time offerings."},
        "contact": {"headline": industry["contact_headline"], "subheadline": industry["contact_subheadline"], "cta": industry["contact_cta"]},
    }

    out_sections = {}
    for key in sections:
        template_key = SECTION_KEY_TO_TEMPLATE.get(key, "features")
        template = flowing_sections.get(template_key, flowing_sections["features"])
        base_data = dict(template_defaults.get(template_key, template_defaults["features"]))
        base_data.update(section_overrides.get(key, {}))
        out_sections[key] = {"html": template["html"], "data": base_data}

    return {
        "business_name": business_name,
        "sections": out_sections,
        "seo": {
            "title": f"{business_name} - Professional Services",
            "description": f"Discover {business_name}, your trusted partner.",
            "keywords": ["professional", "quality", "trusted"],
        },
    }


# ======================================================
# MAIN FUNCTIONS
# ======================================================

def generate_html_sections(business_name: str, prompt: str, business_type: str, structure: Dict[str, Any]) -> Dict[str, Any]:
    """Always use premium fallback for guaranteed quality."""
    sections = structure["sections"]
    return generate_premium_website(business_name, prompt, sections, structure)


def rewrite_content(original_text: str, tone: str = "professional", business_context: str = "") -> List[str]:
    try:
        prompt_text = f"Rewrite: {original_text}\nTone: {tone}\nReturn JSON: [\"v1\", \"v2\", \"v3\"]"
        response = chat_completion(system="Copywriter. JSON only.", user=prompt_text, temperature=0.8)
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