import random
import hashlib
import json
from typing import Dict, Any, List, Tuple

from app.ai.openai_client import chat_completion


# ======================================================
# FRONTEND CONTRACT: theme, hero, footer (ai_structure_json)
# ======================================================

THEME_PALETTE_VALUES = ("light", "dark")
THEME_ACCENT_VALUES = ("indigo", "emerald", "orange", "neutral", "violet", "rose")
HERO_VARIANTS = ("split_image", "centered_text", "image_background", "minimal")
FOOTER_VARIANTS = ("minimal", "standard")

# Section presets by business type — order and set vary so sites look different
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

# Keywords in prompt → business type for section choice
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
# DESIGN SYSTEMS & PALETTES (internal HTML generation)
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

# Map frontend theme.accent to internal palette key (for HTML class names / remapping)
ACCENT_TO_PALETTE_KEY: Dict[str, str] = {
    "indigo": "midnight_purple",
    "emerald": "emerald_forest",
    "orange": "sunset_fire",
    "neutral": "slate_pro",
    "violet": "midnight_purple",
    "rose": "sunset_fire",
}

# Map section keys (from structure.sections) to template type for fallback HTML
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
# STRUCTURE GENERATION (varied per business & prompt)
# ======================================================

def _choose_theme_and_variants(
    prompt: str, business_type: str, rng: random.Random
) -> Tuple[str, str, str, str]:
    """Returns (palette, accent, hero_variant, footer_variant)."""
    # Palette: bias by business type so sites look different
    dark_biased = business_type in ("restaurant", "bar", "agency")
    light_biased = business_type in ("clinic", "cafe", "law")
    if dark_biased and not light_biased:
        palette = "dark" if rng.random() < 0.7 else "light"
    elif light_biased and not dark_biased:
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

    # Infer section preset from prompt so structure fits the business
    inferred = _infer_business_type(seed_prompt)
    section_list = list(SECTION_PRESETS.get(inferred, SECTION_PRESETS["default"]))
    # Optional: shuffle or drop one for extra variety (keep order deterministic by seed)
    if rng.random() < 0.2 and len(section_list) > 3:
        section_list = section_list[:-1]  # sometimes one fewer section

    palette_light_dark, accent, hero_variant, footer_variant = _choose_theme_and_variants(
        seed_prompt, inferred, rng
    )

    # Internal: design + palette for HTML generation (derive from theme)
    palette_key = ACCENT_TO_PALETTE_KEY.get(accent, "midnight_purple")
    palette = COLOR_PALETTES[palette_key]
    design = next(
        (d for d in DESIGN_SYSTEMS if d["base"] == palette_light_dark),
        DESIGN_SYSTEMS[0],
    )

    return {
        # Frontend contract: theme, hero, footer, sections
        "theme": {
            "palette": palette_light_dark,
            "accent": accent,
        },
        "hero": {"variant": hero_variant},
        "footer": {"variant": footer_variant},
        "sections": section_list,
        # Internal (for generate_flowing_website / generate_html_sections)
        "design": design,
        "palette": palette,
        "palette_key": palette_key,
        "html_mode": True,
        "modern_flow": True,
    }


# ======================================================
# FLOWING, BLENDING SECTIONS (NO MORE BOXY!)
# ======================================================

def _industry_defaults(business_type: str, business_name: str) -> Dict[str, Dict[str, str]]:
    """Industry-appropriate hero, contact, and section copy — no generic 'send inquiry' for restaurants."""
    by_type: Dict[str, Dict[str, str]] = {
        "restaurant": {
            "hero_subheadline": f"Exceptional dining in an inviting atmosphere. Reserve your table and taste the difference.",
            "hero_cta": "Reserve a Table",
            "contact_headline": "Visit Us",
            "contact_subheadline": "We can't wait to welcome you. Reserve a table or stop by for a memorable experience.",
            "contact_cta": "Reserve a Table",
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
            "hero_cta": "Book an Appointment",
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
    defaults = by_type.get(business_type, {
        "hero_subheadline": f"Experience excellence with {business_name}. We deliver quality that exceeds expectations.",
        "hero_cta": "Get Started",
        "contact_headline": "Get in Touch",
        "contact_subheadline": "We'd love to hear from you. Reach out anytime.",
        "contact_cta": "Contact Us",
    })
    return defaults


def generate_flowing_website(
    business_name: str,
    prompt: str,
    sections: List[str],
    structure: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Premium, modern sections: gradient mesh backgrounds, smooth animations, hover states.
    Industry-appropriate copy (e.g. restaurant: Reserve a Table, not "send inquiry").
    """
    design = structure["design"]
    palette = structure["palette"]
    is_dark = design["base"] == "dark"
    inferred = _infer_business_type(prompt)
    industry = _industry_defaults(inferred, business_name)

    bg = palette["bg_dark"] if is_dark else palette["bg_light"]
    text = "text-white" if is_dark else "text-gray-900"
    text_muted = "text-gray-300" if is_dark else "text-gray-600"
    primary = palette["primary"]
    accent = palette["accent"]
    glow = palette["glow"]
    card_bg = palette["card_bg"]

    flowing_sections = {}

    # ============================================
    # HERO — Premium: gradient mesh, floating orbs, grain, strong typography
    # ============================================
    flowing_sections["hero"] = {
        "html": f"""
<section class="relative min-h-screen flex items-center justify-center overflow-hidden bg-gradient-to-br {bg}">
    <div class="absolute inset-0 overflow-hidden">
        <div class="absolute -top-[40%] -left-[20%] w-[90vw] h-[90vw] max-w-[1200px] max-h-[1200px] bg-gradient-to-r {primary} rounded-full blur-[120px] opacity-25 animate-pulse"></div>
        <div class="absolute -bottom-[30%] -right-[10%] w-[80vw] h-[80vw] max-w-[1000px] max-h-[1000px] bg-{accent} rounded-full blur-[100px] opacity-30" style="animation: pulse 4s ease-in-out infinite;"></div>
        <div class="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-gradient-to-r {primary} rounded-full blur-[80px] opacity-10"></div>
        <div class="absolute inset-0 bg-[radial-gradient(ellipse_80%_50%_at_50%_-20%,rgba(255,255,255,0.08),transparent)]"></div>
        <div class="absolute inset-0 opacity-[0.02]" style="background-image: url('data:image/svg+xml,%3Csvg viewBox=\\'0 0 256 256\\' xmlns=\\'http://www.w3.org/2000/svg\\'%3E%3Cfilter id=\\'noise\\'%3E%3CfeTurbulence type=\\'fractalNoise\\' baseFrequency=\\'0.9\\' numOctaves=\\'4\\' stitchTiles=\\'stitch\\'/%3E%3C/filter%3E%3Crect width=\\'100%25\\' height=\\'100%25\\' filter=\\'url(%23noise)\\'/%3E%3C/svg%3E');"></div>
    </div>
    <div class="relative z-10 max-w-7xl mx-auto px-6 text-center">
        <h1 class="text-5xl sm:text-6xl md:text-7xl lg:text-8xl xl:text-9xl font-bold {text} tracking-tight leading-[0.95] mb-8 transition-all duration-700" style="letter-spacing: -0.04em;">
            <span class="bg-gradient-to-r {primary} bg-clip-text text-transparent drop-shadow-sm">
                {{{{headline}}}}
            </span>
        </h1>
        <p class="text-lg sm:text-xl md:text-2xl {text_muted} max-w-2xl mx-auto mb-14 leading-relaxed transition-all duration-700 delay-100">
            {{{{subheadline}}}}
        </p>
        <div class="flex flex-col sm:flex-row items-center justify-center gap-4 transition-all duration-700 delay-200">
            <a href="#contact" class="group relative inline-flex items-center justify-center px-8 py-4 rounded-2xl font-semibold text-lg {text} bg-gradient-to-r {primary} overflow-hidden transition-all duration-300 hover:scale-[1.03] hover:shadow-2xl hover:shadow-{glow} focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-transparent">
                <span class="relative z-10">{{{{cta}}}}</span>
                <span class="absolute inset-0 bg-white/20 opacity-0 group-hover:opacity-100 transition-opacity duration-300"></span>
            </a>
        </div>
    </div>
    <div class="absolute bottom-8 left-1/2 -translate-x-1/2 z-10 flex flex-col items-center gap-2 opacity-70">
        <span class="text-sm {text_muted}">Scroll</span>
        <div class="w-6 h-10 rounded-full border-2 border-current {text_muted} flex justify-center pt-2"><div class="w-1 h-2 rounded-full bg-current animate-bounce"></div></div>
    </div>
    <div class="absolute bottom-0 left-0 right-0 h-40 bg-gradient-to-t from-black/60 to-transparent pointer-events-none"></div>
</section>
        """,
        "data": {
            "headline": business_name,
            "subheadline": industry["hero_subheadline"],
            "cta": industry["hero_cta"],
        },
    }

    # ============================================
    # FEATURES — Cards with hover lift, gradient borders, stagger feel
    # ============================================
    flowing_sections["features"] = {
        "html": f"""
<section class="relative -mt-24 z-20 py-28 bg-gradient-to-b from-transparent via-black/90 to-black">
    <div class="max-w-7xl mx-auto px-6">
        <div class="backdrop-blur-2xl {card_bg} border border-white/10 rounded-3xl p-12 md:p-16 mb-20 shadow-2xl transition-all duration-500 hover:border-white/20">
            <h2 class="text-4xl md:text-5xl lg:text-6xl font-bold {text} text-center mb-6 tracking-tight">
                {{{{title}}}}
            </h2>
            <p class="text-lg md:text-xl {text_muted} text-center max-w-2xl mx-auto leading-relaxed">
                {{{{subtitle}}}}
            </p>
        </div>
        <div class="grid md:grid-cols-3 gap-8 md:gap-10">
            <div class="group relative backdrop-blur-xl {card_bg} border border-white/10 rounded-3xl p-8 md:p-10 transition-all duration-500 hover:-translate-y-2 hover:border-white/20 hover:shadow-2xl hover:shadow-{glow}">
                <div class="absolute inset-0 rounded-3xl bg-gradient-to-r {primary} opacity-0 group-hover:opacity-10 transition-opacity duration-500"></div>
                <div class="relative w-14 h-14 md:w-16 md:h-16 bg-gradient-to-r {primary} rounded-2xl flex items-center justify-center mb-6 shadow-lg group-hover:scale-110 transition-transform duration-300">
                    <svg class="w-7 h-7 md:w-8 md:h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"/></svg>
                </div>
                <h3 class="relative text-xl md:text-2xl font-bold {text} mb-4">{{{{feature1_title}}}}</h3>
                <p class="relative {text_muted} leading-relaxed">{{{{feature1_desc}}}}</p>
            </div>
            <div class="group relative backdrop-blur-xl {card_bg} border border-white/10 rounded-3xl p-8 md:p-10 transition-all duration-500 hover:-translate-y-2 hover:border-white/20 hover:shadow-2xl hover:shadow-{glow}">
                <div class="absolute inset-0 rounded-3xl bg-gradient-to-r {primary} opacity-0 group-hover:opacity-10 transition-opacity duration-500"></div>
                <div class="relative w-14 h-14 md:w-16 md:h-16 bg-gradient-to-r {primary} rounded-2xl flex items-center justify-center mb-6 shadow-lg group-hover:scale-110 transition-transform duration-300">
                    <svg class="w-7 h-7 md:w-8 md:h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>
                </div>
                <h3 class="relative text-xl md:text-2xl font-bold {text} mb-4">{{{{feature2_title}}}}</h3>
                <p class="relative {text_muted} leading-relaxed">{{{{feature2_desc}}}}</p>
            </div>
            <div class="group relative backdrop-blur-xl {card_bg} border border-white/10 rounded-3xl p-8 md:p-10 transition-all duration-500 hover:-translate-y-2 hover:border-white/20 hover:shadow-2xl hover:shadow-{glow}">
                <div class="absolute inset-0 rounded-3xl bg-gradient-to-r {primary} opacity-0 group-hover:opacity-10 transition-opacity duration-500"></div>
                <div class="relative w-14 h-14 md:w-16 md:h-16 bg-gradient-to-r {primary} rounded-2xl flex items-center justify-center mb-6 shadow-lg group-hover:scale-110 transition-transform duration-300">
                    <svg class="w-7 h-7 md:w-8 md:h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 3v4M3 5h4M6 17v4m-2-2h4m5-16l2.286 6.857L21 12l-5.714 2.143L13 21l-2.286-6.857L5 12l5.714-2.143L13 3z"/></svg>
                </div>
                <h3 class="relative text-xl md:text-2xl font-bold {text} mb-4">{{{{feature3_title}}}}</h3>
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
            "feature1_desc": "Quick turnaround times without compromising on quality",
            "feature2_title": "Trusted by Thousands",
            "feature2_desc": "Join our community of satisfied customers",
            "feature3_title": "Premium Quality",
            "feature3_desc": "Best-in-class service at competitive prices",
        },
    }

    # ============================================
    # SOCIAL PROOF — Stats with gradient text and hover scale
    # ============================================
    flowing_sections["social_proof"] = {
        "html": f"""
<section class="relative py-28 md:py-36 overflow-hidden">
    <div class="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[800px] bg-gradient-to-r {primary} rounded-full blur-[150px] opacity-15"></div>
    <div class="relative z-10 max-w-7xl mx-auto px-6">
        <div class="text-center mb-16 md:mb-24">
            <h2 class="text-4xl md:text-5xl lg:text-6xl font-bold {text} mb-4 tracking-tight">
                {{{{title}}}}
            </h2>
            <p class="text-lg md:text-xl {text_muted} max-w-xl mx-auto">What people say about us</p>
        </div>
        <div class="grid md:grid-cols-3 gap-12 md:gap-16">
            <div class="text-center group transition-transform duration-300 hover:scale-105">
                <div class="text-5xl md:text-6xl lg:text-7xl font-bold bg-gradient-to-r {primary} bg-clip-text text-transparent mb-3 tabular-nums">
                    {{{{stat1_number}}}}
                </div>
                <p class="text-lg {text_muted}">{{{{stat1_label}}}}</p>
            </div>
            <div class="text-center group transition-transform duration-300 hover:scale-105">
                <div class="text-5xl md:text-6xl lg:text-7xl font-bold bg-gradient-to-r {primary} bg-clip-text text-transparent mb-3 tabular-nums">
                    {{{{stat2_number}}}}
                </div>
                <p class="text-lg {text_muted}">{{{{stat2_label}}}}</p>
            </div>
            <div class="text-center group transition-transform duration-300 hover:scale-105">
                <div class="text-5xl md:text-6xl lg:text-7xl font-bold bg-gradient-to-r {primary} bg-clip-text text-transparent mb-3 tabular-nums">
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

    # ============================================
    # CTA / CONTACT — Full-bleed gradient, one strong CTA
    # ============================================
    flowing_sections["cta"] = {
        "html": f"""
<section id="contact" class="relative py-32 md:py-44 overflow-hidden">
    <div class="absolute inset-0 bg-gradient-to-b from-black via-black/95 to-black"></div>
    <div class="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[min(100vw,1200px)] h-[800px] bg-gradient-to-r {primary} rounded-full blur-[140px] opacity-25"></div>
    <div class="relative z-10 max-w-4xl mx-auto px-6 text-center">
        <h2 class="text-4xl md:text-5xl lg:text-6xl xl:text-7xl font-bold {text} mb-6 tracking-tight leading-tight">
            {{{{headline}}}}
        </h2>
        <p class="text-lg md:text-xl {text_muted} mb-12 max-w-2xl mx-auto leading-relaxed">
            {{{{subheadline}}}}
        </p>
        <a href="#" class="group inline-flex items-center justify-center px-10 py-5 rounded-2xl font-semibold text-lg bg-gradient-to-r {primary} text-white overflow-hidden transition-all duration-300 hover:scale-[1.04] hover:shadow-2xl hover:shadow-{glow} focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-black">
            <span class="relative z-10">{{{{cta}}}}</span>
            <span class="absolute inset-0 bg-white/20 opacity-0 group-hover:opacity-100 transition-opacity duration-300"></span>
        </a>
    </div>
</section>
        """,
        "data": {
            "headline": "Ready to Get Started?",
            "subheadline": "Join thousands of satisfied customers and experience the difference",
            "cta": "Start Your Journey Today",
        },
    }

    # Build output sections: industry-appropriate copy (restaurant = Reserve a Table, not "send inquiry")
    template_to_data_defaults: Dict[str, Dict[str, Any]] = {
        "hero": {"headline": business_name, "subheadline": industry["hero_subheadline"], "cta": industry["hero_cta"]},
        "features": {"title": "Why Choose Us", "subtitle": "We provide exceptional service.", "feature1_title": "Quality", "feature1_desc": "Best-in-class.", "feature2_title": "Trusted", "feature2_desc": "Join our community.", "feature3_title": "Premium", "feature3_desc": "Competitive prices."},
        "social_proof": {"title": "Trusted Worldwide", "stat1_number": "10K+", "stat1_label": "Happy Customers", "stat2_number": "99%", "stat2_label": "Satisfaction", "stat3_number": "24/7", "stat3_label": "Support"},
        "cta": {"headline": industry["contact_headline"], "subheadline": industry["contact_subheadline"], "cta": industry["contact_cta"]},
    }
    section_data_overrides: Dict[str, Dict[str, str]] = {
        "about": {"title": "Our Story", "subtitle": f"Learn more about {business_name} and what makes us different.", "feature1_title": "Our Story", "feature1_desc": "Dedicated to excellence and our community.", "feature2_title": "Our Values", "feature2_desc": "Quality, integrity, and care in everything we do.", "feature3_title": "Our Mission", "feature3_desc": "Serving you with the best experience every time."},
        "menu": {"title": "Our Menu", "subtitle": "Fresh ingredients, bold flavors. Discover what we're serving.", "feature1_title": "Signature Dishes", "feature1_desc": "Chef favorites and customer classics.", "feature2_title": "Seasonal Picks", "feature2_desc": "Rotating selections with the best of the season.", "feature3_title": "Specials", "feature3_desc": "Limited-time offerings and today's highlights."},
        "services": {"title": "Our Services", "subtitle": "What we offer to help you succeed.", "feature1_title": "Service One", "feature1_desc": "Detailed description tailored to your needs.", "feature2_title": "Service Two", "feature2_desc": "Detailed description tailored to your needs.", "feature3_title": "Service Three", "feature3_desc": "Detailed description tailored to your needs."},
        "contact": {"headline": industry["contact_headline"], "subheadline": industry["contact_subheadline"], "cta": industry["contact_cta"]},
        "gallery": {"title": "Gallery", "stat1_number": "500+", "stat1_label": "Moments Captured", "stat2_number": "50+", "stat2_label": "Five-Star Reviews", "stat3_number": "100%", "stat3_label": "Passion"},
    }
    out_sections: Dict[str, Dict[str, Any]] = {}
    templates = {
        "hero": flowing_sections["hero"],
        "features": flowing_sections["features"],
        "social_proof": flowing_sections["social_proof"],
        "cta": flowing_sections["cta"],
    }
    for key in sections:
        template_key = SECTION_KEY_TO_TEMPLATE.get(key, "features")
        t = templates.get(template_key, flowing_sections["features"])
        base_data = dict(template_to_data_defaults.get(template_key, template_to_data_defaults["features"]))
        base_data.update(section_data_overrides.get(key, {}))
        out_sections[key] = {"html": t["html"], "data": base_data}

    return {
        "business_name": business_name,
        "sections": out_sections,
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
    """Try REAL AI, fallback if it fails. Output section keys must match structure['sections']."""
    design = structure["design"]
    palette = structure["palette"]
    sections = structure["sections"]
    theme = structure.get("theme") or {}
    accent_name = theme.get("accent", "indigo")
    palette_ld = theme.get("palette", design["base"])
    is_dark = (palette_ld == "dark") or (design["base"] == "dark")

    text_color = "text-white" if is_dark else "text-gray-900"
    text_muted = "text-gray-300" if is_dark else "text-gray-600"
    bg = palette["bg_dark"] if is_dark else palette["bg_light"]

    sections_list_str = ", ".join(sections)

    inferred_type = _infer_business_type(prompt)
    cta_rules = (
        "RESTAURANT/FOOD: Use CTAs like 'Reserve a Table', 'View Menu', 'Visit Us', 'Order Now'. NEVER 'Send us an inquiry', 'Request a quote', or 'Contact us for more info' as primary CTA. "
        if inferred_type in ("restaurant", "cafe", "bar")
        else "Use ONE clear, action-oriented CTA that fits the business (e.g. Book Appointment, Schedule Consultation, Start Free Trial). Never generic 'Contact Us' or 'Send inquiry' as the main button."
    )

    ai_prompt = f"""Create a PREMIUM, HIGH-VALUE website that gives an immediate "wow" impression. Modern, not old or corporate.

Business: {business_name}
Description: {prompt}

NON-NEGOTIABLE DESIGN QUALITY:
- MODERN: Use gradient backgrounds (bg-gradient-to-br, bg-gradient-to-r), backdrop-blur (backdrop-blur-xl, bg-white/5), rounded-3xl, generous spacing. Include at least one large gradient orb/blur in the background (e.g. absolute blob with blur-[100px] opacity-20).
- ANIMATIONS & DEPTH: Add transition-all duration-300 or duration-500, hover:scale-105 or hover:-translate-y-2, hover:shadow-2xl on buttons and cards. Use animate-pulse on background orbs. Make it feel alive.
- HIGH-VALUE COPY: Every line must feel premium and specific to THIS business. No generic "We deliver excellence" or "Get in touch". For restaurants: warm, inviting, food-focused. Subheadlines should sell the experience.

CTA RULES (critical):
{cta_rules}

Section keys you MUST output (each with "html" and "data"): {sections_list_str}

THEME: palette="{palette_ld}", accent="{accent_name}". Use {text_color} for main text, {text_muted} for secondary. Background gradient: {bg}. Primary: {palette['primary']}, accent: {palette['accent']}. Cards: backdrop-blur-xl bg-white/5 border border-white/10.

Return ONLY valid JSON (no markdown, no code block):
{{
  "business_name": "{business_name}",
  "sections": {{
    "hero": {{ "html": "<section class=\\"...\\">...</section>", "data": {{ "headline": "...", "subheadline": "...", "cta": "..." }} }},
    ... one entry for EACH of: {sections_list_str} ...
  }},
  "seo": {{ "title": "...", "description": "...", "keywords": [] }}
}}

- Hero: one headline, one subheadline, one primary CTA (e.g. Reserve a Table / Book Now / Start Free Trial).
- About/Menu/Services/Features: title, subtitle, feature1_title, feature1_desc, feature2_title, feature2_desc, feature3_title, feature3_desc.
- Gallery/Social proof/Testimonial: title, stat1_number, stat1_label, stat2_number, stat2_label, stat3_number, stat3_label.
- Contact/CTA: headline, subheadline, cta (single action button text).
Copy must be industry-appropriate and premium. No placeholders."""

    print(f"=== 🤖 Trying AI generation (theme: {palette_ld} / {accent_name}) ===")

    try:
        response = chat_completion(
            system="You are an expert premium web designer. Output ONLY valid JSON—no markdown or code fences. Every site must feel modern, high-value, with gradient backgrounds, smooth hover states, and industry-appropriate CTAs (e.g. restaurant: Reserve a Table, not 'Send inquiry'). Section keys must match the requested list exactly.",
            user=ai_prompt,
            temperature=0.85,
        )
        parsed = json.loads(response)

        if not parsed.get("sections"):
            raise ValueError("No sections in response")

        # Ensure we have every requested section; fill missing from fallback
        fallback = generate_flowing_website(business_name, prompt, sections, structure)
        for key in sections:
            if key not in parsed["sections"] and key in fallback["sections"]:
                parsed["sections"][key] = fallback["sections"][key]

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