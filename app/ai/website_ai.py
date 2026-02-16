import random
import hashlib
import json
from typing import Dict, Any, List, Tuple

from app.ai.openai_client import chat_completion

THEME_PALETTE_VALUES = ("light", "dark")
THEME_ACCENT_VALUES = ("indigo", "emerald", "orange", "neutral", "violet", "rose")
HERO_VARIANTS = ("split_image", "centered_text", "image_background", "minimal")
FOOTER_VARIANTS = ("minimal", "standard")

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

COLOR_PALETTES = {
    "midnight_purple": {"name": "Midnight Purple", "primary": "from-indigo-500 to-purple-500", "accent": "indigo-500", "bg_dark": "from-purple-950 via-indigo-950 to-black", "bg_light": "from-purple-50 via-indigo-50 to-white", "glow": "indigo-500/30"},
    "ocean_deep": {"name": "Ocean Deep", "primary": "from-cyan-500 to-blue-500", "accent": "cyan-500", "bg_dark": "from-cyan-950 via-blue-950 to-black", "bg_light": "from-cyan-50 via-blue-50 to-white", "glow": "cyan-500/30"},
    "sunset_fire": {"name": "Sunset Fire", "primary": "from-orange-500 to-pink-500", "accent": "orange-500", "bg_dark": "from-orange-950 via-rose-950 to-black", "bg_light": "from-orange-50 via-rose-50 to-white", "glow": "orange-500/30"},
    "emerald_forest": {"name": "Emerald Forest", "primary": "from-emerald-600 to-teal-600", "accent": "emerald-500", "bg_dark": "from-emerald-950 via-teal-950 to-black", "bg_light": "from-emerald-50 via-teal-50 to-white", "glow": "emerald-500/30"},
    "slate_pro": {"name": "Slate Pro", "primary": "from-slate-700 to-gray-800", "accent": "slate-600", "bg_dark": "from-black via-slate-950 to-gray-900", "bg_light": "from-white via-slate-50 to-gray-100", "glow": "slate-500/30"},
}

ACCENT_TO_PALETTE_KEY: Dict[str, str] = {"indigo": "midnight_purple", "emerald": "emerald_forest", "orange": "sunset_fire", "neutral": "slate_pro", "violet": "midnight_purple", "rose": "sunset_fire"}

def stable_seed(*values: str) -> int:
    raw = "|".join([v or "" for v in values])
    return int(hashlib.sha256(raw.encode()).hexdigest()[:8], 16)

def _choose_theme_and_variants(prompt: str, business_type: str, rng: random.Random) -> Tuple[str, str, str, str]:
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
    return {"theme": {"palette": palette_light_dark, "accent": accent}, "hero": {"variant": hero_variant}, "footer": {"variant": footer_variant}, "sections": section_list, "palette": palette, "palette_key": palette_key, "html_mode": True, "modern_flow": True}

def _industry_defaults(business_type: str, business_name: str) -> Dict[str, str]:
    by_type = {
        "restaurant": {"hero_subheadline": "Exceptional dining in an inviting atmosphere. Reserve your table and taste the difference.", "hero_cta": "Reserve a Table", "contact_headline": "Visit Us", "contact_subheadline": "We can't wait to welcome you. Reserve a table or stop by for a memorable experience.", "contact_cta": "Reserve Now"},
        "cafe": {"hero_subheadline": "Your neighborhood spot for great coffee and fresh bites. Come in and stay awhile.", "hero_cta": "View Menu", "contact_headline": "Find Us", "contact_subheadline": "Drop in for a coffee or message us for catering.", "contact_cta": "Get Directions"},
        "bar": {"hero_subheadline": "Where great drinks and good times meet. Join us for craft cocktails and a vibe like no other.", "hero_cta": "View Hours", "contact_headline": "Find Us", "contact_subheadline": "Reserve a booth or walk in — we're here for you.", "contact_cta": "Get Directions"},
        "law": {"hero_subheadline": "Trusted legal counsel when it matters most. Schedule a confidential consultation.", "hero_cta": "Schedule Consultation", "contact_headline": "Get in Touch", "contact_subheadline": "Reach out for a confidential discussion about your case.", "contact_cta": "Request a Call"},
        "clinic": {"hero_subheadline": "Quality care in a caring environment. Your health and comfort come first.", "hero_cta": "Book Appointment", "contact_headline": "Contact Us", "contact_subheadline": "Schedule a visit or ask us anything.", "contact_cta": "Book Now"},
        "salon": {"hero_subheadline": "Look and feel your best. Expert stylists and a relaxing experience await.", "hero_cta": "Book Appointment", "contact_headline": "Visit the Salon", "contact_subheadline": "Book your next appointment or drop by for a walk-in.", "contact_cta": "Book Now"},
        "saas": {"hero_subheadline": "Built to scale with you. Start free and upgrade when you're ready.", "hero_cta": "Start Free Trial", "contact_headline": "Let's Talk", "contact_subheadline": "Questions? Our team is here to help.", "contact_cta": "Contact Sales"},
        "agency": {"hero_subheadline": "Creative that drives results. Let's build your brand and grow your audience.", "hero_cta": "Start a Project", "contact_headline": "Work With Us", "contact_subheadline": "Tell us about your project and goals.", "contact_cta": "Get a Quote"},
    }
    return by_type.get(business_type, {"hero_subheadline": f"Experience excellence with {business_name}. We deliver quality that exceeds expectations.", "hero_cta": "Get Started", "contact_headline": "Get in Touch", "contact_subheadline": "We'd love to hear from you. Reach out anytime.", "contact_cta": "Contact Us"})

def _generate_fallback_section(section_key: str, business_name: str, industry: Dict[str, str], palette: Dict[str, str], is_dark: bool) -> Dict[str, Any]:
    """Premium fallback section - only used if AI fails completely"""
    text = "text-white" if is_dark else "text-gray-900"
    text_muted = "text-gray-300" if is_dark else "text-gray-600"
    bg = palette["bg_dark"] if is_dark else palette["bg_light"]
    primary = palette["primary"]
    accent = palette["accent"]
    glow = palette["glow"]
    
    if section_key == "hero":
        html = f'''<section class="relative min-h-screen flex items-center justify-center overflow-hidden bg-gradient-to-br {bg}">
    <div class="absolute inset-0 overflow-hidden">
        <div class="absolute top-1/4 left-1/4 w-[1400px] h-[1400px] bg-{accent} rounded-full blur-[200px] opacity-20 animate-pulse"></div>
        <div class="absolute bottom-1/4 right-1/4 w-[1400px] h-[1400px] bg-gradient-to-r {primary} rounded-full blur-[200px] opacity-20 animate-pulse" style="animation-delay: 1.5s"></div>
        <div class="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[1000px] h-[1000px] bg-gradient-to-r {primary} rounded-full blur-[180px] opacity-15"></div>
        <div class="absolute inset-0 bg-[radial-gradient(ellipse_80%_50%_at_50%_-20%,rgba(255,255,255,0.1),transparent)]"></div>
    </div>
    <div class="relative z-10 max-w-7xl mx-auto px-6 text-center">
        <h1 class="text-6xl sm:text-7xl md:text-8xl lg:text-9xl font-bold {text} tracking-tight leading-[0.9] mb-10" style="letter-spacing: -0.05em;">
            <span class="bg-gradient-to-r {primary} bg-clip-text text-transparent drop-shadow-2xl">{{{{headline}}}}</span>
        </h1>
        <p class="text-xl sm:text-2xl md:text-3xl {text_muted} max-w-4xl mx-auto mb-14 leading-relaxed">{{{{subheadline}}}}</p>
        <button class="group relative px-12 py-6 bg-gradient-to-r {primary} text-white rounded-3xl font-bold text-xl overflow-hidden hover:scale-110 transition-all duration-500 shadow-2xl shadow-{glow}">
            <span class="relative z-10">{{{{cta}}}}</span>
            <div class="absolute inset-0 bg-white/30 translate-y-full group-hover:translate-y-0 transition-transform duration-500"></div>
        </button>
    </div>
    <div class="absolute bottom-10 left-1/2 -translate-x-1/2 z-10 flex flex-col items-center gap-3 opacity-60 hover:opacity-100 transition-opacity">
        <span class="text-sm {text_muted} font-medium">Scroll to explore</span>
        <div class="w-6 h-12 rounded-full border-2 border-current {text_muted} flex justify-center pt-2">
            <div class="w-1.5 h-3 rounded-full bg-current animate-bounce"></div>
        </div>
    </div>
</section>'''
        return {"html": html, "data": {"headline": business_name, "subheadline": industry.get("hero_subheadline", f"Welcome to {business_name}"), "cta": industry.get("hero_cta", "Get Started")}}
    
    elif section_key in ("features", "about", "services", "process", "menu", "pricing", "portfolio"):
        html = f'''<section class="relative py-40 overflow-hidden">
    <div class="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[1200px] h-[1200px] bg-gradient-to-r {primary} rounded-full blur-[200px] opacity-10"></div>
    <div class="relative z-10 max-w-7xl mx-auto px-6">
        <div class="backdrop-blur-3xl bg-white/5 border border-white/10 rounded-[40px] p-16 mb-20 shadow-2xl hover:border-white/20 hover:shadow-{glow} transition-all duration-700">
            <h2 class="text-5xl md:text-6xl lg:text-7xl font-bold {text} text-center mb-8 leading-tight">{{{{title}}}}</h2>
            <p class="text-2xl {text_muted} text-center max-w-3xl mx-auto leading-relaxed">{{{{subtitle}}}}</p>
        </div>
        <div class="grid md:grid-cols-3 gap-10">
            <div class="group backdrop-blur-2xl bg-white/5 border border-white/10 rounded-[40px] p-12 hover:-translate-y-4 hover:border-white/25 hover:shadow-2xl hover:shadow-{glow} transition-all duration-700">
                <div class="w-20 h-20 bg-gradient-to-br {primary} rounded-3xl flex items-center justify-center mb-8 shadow-xl group-hover:scale-125 group-hover:rotate-12 transition-all duration-700">
                    <svg class="w-10 h-10 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"/></svg>
                </div>
                <h3 class="text-3xl font-bold {text} mb-5">{{{{feature1_title}}}}</h3>
                <p class="text-lg {text_muted} leading-relaxed">{{{{feature1_desc}}}}</p>
            </div>
            <div class="group backdrop-blur-2xl bg-white/5 border border-white/10 rounded-[40px] p-12 hover:-translate-y-4 hover:border-white/25 hover:shadow-2xl hover:shadow-{glow} transition-all duration-700">
                <div class="w-20 h-20 bg-gradient-to-br {primary} rounded-3xl flex items-center justify-center mb-8 shadow-xl group-hover:scale-125 group-hover:rotate-12 transition-all duration-700">
                    <svg class="w-10 h-10 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>
                </div>
                <h3 class="text-3xl font-bold {text} mb-5">{{{{feature2_title}}}}</h3>
                <p class="text-lg {text_muted} leading-relaxed">{{{{feature2_desc}}}}</p>
            </div>
            <div class="group backdrop-blur-2xl bg-white/5 border border-white/10 rounded-[40px] p-12 hover:-translate-y-4 hover:border-white/25 hover:shadow-2xl hover:shadow-{glow} transition-all duration-700">
                <div class="w-20 h-20 bg-gradient-to-br {primary} rounded-3xl flex items-center justify-center mb-8 shadow-xl group-hover:scale-125 group-hover:rotate-12 transition-all duration-700">
                    <svg class="w-10 h-10 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 3v4M3 5h4M6 17v4m-2-2h4m5-16l2.286 6.857L21 12l-5.714 2.143L13 21l-2.286-6.857L5 12l5.714-2.143L13 3z"/></svg>
                </div>
                <h3 class="text-3xl font-bold {text} mb-5">{{{{feature3_title}}}}</h3>
                <p class="text-lg {text_muted} leading-relaxed">{{{{feature3_desc}}}}</p>
            </div>
        </div>
    </div>
</section>'''
        return {"html": html, "data": {"title": "What We Offer", "subtitle": "Exceptional service tailored to your needs", "feature1_title": "Expert Service", "feature1_desc": "Years of experience delivering excellence.", "feature2_title": "Proven Results", "feature2_desc": "Trusted by thousands who rely on us.", "feature3_title": "Premium Experience", "feature3_desc": "Best-in-class service that exceeds expectations."}}
    
    elif section_key in ("social_proof", "testimonial", "gallery", "trust"):
        html = f'''<section class="relative py-40 overflow-hidden">
    <div class="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[1400px] h-[1400px] bg-gradient-to-r {primary} rounded-full blur-[220px] opacity-20"></div>
    <div class="relative z-10 max-w-7xl mx-auto px-6">
        <div class="text-center mb-24">
            <h2 class="text-5xl md:text-6xl lg:text-7xl font-bold {text} mb-6">{{{{title}}}}</h2>
            <p class="text-2xl {text_muted}">Trusted by thousands worldwide</p>
        </div>
        <div class="grid md:grid-cols-3 gap-16">
            <div class="text-center group hover:scale-110 transition-transform duration-700">
                <div class="text-7xl md:text-8xl font-bold bg-gradient-to-br {primary} bg-clip-text text-transparent mb-4 group-hover:scale-125 transition-transform duration-700">{{{{stat1_number}}}}</div>
                <p class="text-xl {text_muted} font-medium">{{{{stat1_label}}}}</p>
            </div>
            <div class="text-center group hover:scale-110 transition-transform duration-700">
                <div class="text-7xl md:text-8xl font-bold bg-gradient-to-br {primary} bg-clip-text text-transparent mb-4 group-hover:scale-125 transition-transform duration-700">{{{{stat2_number}}}}</div>
                <p class="text-xl {text_muted} font-medium">{{{{stat2_label}}}}</p>
            </div>
            <div class="text-center group hover:scale-110 transition-transform duration-700">
                <div class="text-7xl md:text-8xl font-bold bg-gradient-to-br {primary} bg-clip-text text-transparent mb-4 group-hover:scale-125 transition-transform duration-700">{{{{stat3_number}}}}</div>
                <p class="text-xl {text_muted} font-medium">{{{{stat3_label}}}}</p>
            </div>
        </div>
    </div>
</section>'''
        return {"html": html, "data": {"title": "Proven Excellence", "stat1_number": "10K+", "stat1_label": "Happy Customers", "stat2_number": "99%", "stat2_label": "Satisfaction Rate", "stat3_number": "24/7", "stat3_label": "Always Available"}}
    
    else:  # cta, contact, location
        html = f'''<section class="relative py-48 overflow-hidden">
    <div class="absolute inset-0 bg-gradient-to-b from-black/50 via-black/70 to-black"></div>
    <div class="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[1600px] h-[1200px] bg-gradient-to-r {primary} rounded-full blur-[240px] opacity-30"></div>
    <div class="relative z-10 max-w-5xl mx-auto px-6 text-center">
        <h2 class="text-5xl md:text-7xl lg:text-8xl font-bold {text} mb-10 leading-tight">{{{{headline}}}}</h2>
        <p class="text-2xl md:text-3xl {text_muted} mb-16 max-w-3xl mx-auto leading-relaxed">{{{{subheadline}}}}</p>
        <button class="group px-16 py-8 bg-gradient-to-r {primary} text-white rounded-3xl font-bold text-2xl hover:scale-110 transition-all duration-700 shadow-2xl shadow-{glow}">
            <span class="relative z-10">{{{{cta}}}}</span>
        </button>
    </div>
</section>'''
        return {"html": html, "data": {"headline": industry.get("contact_headline", "Get in Touch"), "subheadline": industry.get("contact_subheadline", "Ready to get started? Contact us today."), "cta": industry.get("contact_cta", "Contact Us")}}

def generate_html_sections(business_name: str, prompt: str, business_type: str, structure: Dict[str, Any]) -> Dict[str, Any]:
    """AI-FIRST website generation. Creates completely custom HTML based on business description."""
    palette = structure["palette"]
    theme = structure.get("theme", {})
    sections = structure["sections"]
    is_dark = theme.get("palette", "dark") == "dark"
    inferred = _infer_business_type(prompt)
    industry = _industry_defaults(inferred, business_name)
    
    text_color = "text-white" if is_dark else "text-gray-900"
    text_muted = "text-gray-300" if is_dark else "text-gray-600"
    bg = palette["bg_dark"] if is_dark else palette["bg_light"]
    primary = palette["primary"]
    accent = palette["accent"]
    glow = palette["glow"]

    cta_guidance_map = {
        "restaurant": "Use CTAs like 'Reserve a Table', 'View Menu', 'Order Now'. NEVER generic 'Contact Us'.",
        "cafe": "Use CTAs like 'View Menu', 'Order Online', 'Visit Us'.",
        "bar": "Use CTAs like 'View Hours', 'Reserve a Booth', 'See Events'.",
        "law": "Use CTAs like 'Schedule Consultation', 'Get Legal Help', 'Speak to Attorney'.",
        "clinic": "Use CTAs like 'Book Appointment', 'Schedule Visit', 'Contact Clinic'.",
        "salon": "Use CTAs like 'Book Appointment', 'See Services', 'Book Now'.",
        "saas": "Use CTAs like 'Start Free Trial', 'Get Started', 'Sign Up Free'.",
        "agency": "Use CTAs like 'Start a Project', 'Get a Quote', 'Work With Us'.",
    }
    cta_guidance = cta_guidance_map.get(inferred, "Use clear, action-oriented CTAs relevant to the business.")
    sections_list = ", ".join(sections)

    # COMPREHENSIVE AI PROMPT FOR FULL CUSTOM GENERATION
    ai_prompt = f"""You are an elite web designer creating a COMPLETELY CUSTOM website. Read the business description carefully and generate UNIQUE HTML and content.

🎯 BUSINESS DETAILS:
Name: {business_name}
Description: {prompt}
Industry: {inferred}
Sections needed: {sections_list}

📐 CRITICAL DESIGN REQUIREMENTS (NON-NEGOTIABLE):

1. MASSIVE GRADIENT ORBS (1400-1600px):
   - Multiple orbs per section: w-[1400px] h-[1400px] or larger
   - Heavy blur: blur-[200px] to blur-[240px]
   - Animated: animate-pulse with staggered delays
   - Example: <div class="absolute top-1/4 left-1/4 w-[1400px] h-[1400px] bg-{accent} rounded-full blur-[200px] opacity-20 animate-pulse"></div>

2. GLASSMORPHISM EVERYWHERE:
   - Cards: backdrop-blur-2xl bg-white/5 border border-white/10 rounded-[40px]
   - Hover effects: hover:border-white/25 hover:shadow-2xl hover:shadow-{glow}
   - Smooth transitions: transition-all duration-700

3. DRAMATIC ANIMATIONS:
   - Hover lifts: hover:-translate-y-4
   - Icon rotations: group-hover:scale-125 group-hover:rotate-12
   - Button overlays: <div class="absolute inset-0 bg-white/30 opacity-0 group-hover:opacity-100 transition-opacity duration-700"></div>
   - Scale effects: hover:scale-110 transition-all duration-700

4. PREMIUM TYPOGRAPHY:
   - Hero headlines: text-6xl sm:text-7xl md:text-8xl lg:text-9xl font-bold
   - Tight tracking: tracking-tight style="letter-spacing: -0.05em;"
   - Section titles: text-5xl md:text-6xl lg:text-7xl
   - Generous spacing: mb-10, mb-16, py-40, py-48

5. THEME INTEGRATION (MUST USE EXACT CLASSES):
   - Background: bg-gradient-to-br {bg}
   - Text primary: {text_color}
   - Text secondary: {text_muted}
   - Gradient accents: {primary}
   - Solid accent: {accent}
   - Glow effects: shadow-{glow}

6. INDUSTRY-SPECIFIC CTAS:
   {cta_guidance}

🎨 CONTENT REQUIREMENTS:

1. READ THE BUSINESS DESCRIPTION CAREFULLY
   - Extract specific services/offerings mentioned
   - Reference unique features or location details
   - Make headlines SPECIFIC to this business
   - Use industry-appropriate language

2. SECTION-SPECIFIC CONTENT:
   - HERO: Dramatic headline with business name, compelling subheadline from description, strong CTA
   - FEATURES/ABOUT/SERVICES: Title + subtitle + 3 detailed feature cards with icons
   - SOCIAL PROOF/TESTIMONIAL: Title + 3 impressive stats with large numbers
   - CTA/CONTACT: Final call-to-action headline, subheadline, industry-appropriate CTA

3. AVOID GENERIC CONTENT:
   - NO "Why Choose Us" unless very specific
   - NO "Get Started" buttons for restaurants/clinics
   - NO vague "quality service" - be specific about what they offer

📦 OUTPUT FORMAT (STRICT JSON):

{{
  "business_name": "{business_name}",
  "sections": {{
    "hero": {{
      "html": "<section class='relative min-h-screen...'>COMPLETE CUSTOM HTML WITH GIANT ORBS</section>",
      "data": {{
        "headline": "SPECIFIC headline for {business_name}",
        "subheadline": "Based on: {prompt}",
        "cta": "Industry-appropriate CTA"
      }}
    }},
    "features": {{
      "html": "<section class='relative py-40...'>GLASSMORPHISM CARDS WITH ANIMATIONS</section>",
      "data": {{
        "title": "Custom title based on business",
        "subtitle": "Relevant subtitle",
        "feature1_title": "Specific feature from description",
        "feature1_desc": "Detailed description",
        "feature2_title": "...",
        "feature2_desc": "...",
        "feature3_title": "...",
        "feature3_desc": "..."
      }}
    }}
    ... (generate ALL sections: {sections_list})
  }},
  "seo": {{
    "title": "{business_name} - [Specific Value Prop]",
    "description": "Custom description based on business",
    "keywords": ["relevant", "keywords"]
  }}
}}

⚠️ VALIDATION CHECKLIST:
- [ ] All orbs are 1400px+ with blur-[200px]+
- [ ] All cards have backdrop-blur-2xl and glassmorphism
- [ ] All hover states have smooth 700ms transitions
- [ ] Hero headline is 9xl on desktop
- [ ] All content is SPECIFIC to the business description
- [ ] CTAs match the industry ({inferred})
- [ ] Every section in {sections_list} is included
- [ ] Output is valid JSON (no markdown, no code fences)

Generate a completely unique, visually stunning website that feels custom-built for this specific business."""

    print(f"\n{'='*60}")
    print(f"🤖 GENERATING AI WEBSITE")
    print(f"{'='*60}")
    print(f"Business: {business_name}")
    print(f"Industry: {inferred}")
    print(f"Theme: {theme.get('palette')} + {theme.get('accent')}")
    print(f"Sections: {sections_list}")
    print(f"Description: {prompt[:150]}...")
    print(f"{'='*60}\n")
    
    try:
        response = chat_completion(
            system="""You are an elite web designer specializing in creating completely custom, visually stunning websites. 

Your expertise:
- Generating UNIQUE layouts based on business descriptions
- Creating massive gradient orbs (1400px+) with heavy blur
- Implementing premium glassmorphism and animations
- Writing industry-specific, compelling copy
- Producing valid, clean JSON output

NEVER use generic templates. Every website should feel custom-built for that specific business.
ALWAYS use massive orbs (w-[1400px]), glassmorphism (backdrop-blur-2xl bg-white/5), and smooth animations (duration-700).
Output ONLY valid JSON with no markdown formatting.""",
            user=ai_prompt,
            temperature=0.95,  # High creativity for unique designs
        )
        
        # Clean response - remove any markdown formatting
        response = response.strip()
        if response.startswith("```json"):
            response = response[7:]
        if response.startswith("```"):
            response = response[3:]
        if response.endswith("```"):
            response = response[:-3]
        response = response.strip()
        
        parsed = json.loads(response)
        
        # Validation - ensure all sections present
        if not parsed.get("sections"):
            raise ValueError("AI response missing 'sections' key")
        
        missing_sections = []
        for key in sections:
            if key not in parsed["sections"]:
                missing_sections.append(key)
        
        if missing_sections:
            print(f"⚠️  AI missing sections: {missing_sections}")
            print("🔄 Generating fallback sections for missing parts...")
            for key in missing_sections:
                parsed["sections"][key] = _generate_fallback_section(key, business_name, industry, palette, is_dark)
        
        # Add SEO if missing
        if "seo" not in parsed:
            parsed["seo"] = {
                "title": f"{business_name} - {inferred.title()}",
                "description": f"Discover {business_name}. {prompt[:100]}",
                "keywords": [inferred, business_type, "premium"]
            }
        
        print(f"✅ AI SUCCESS!")
        print(f"   Generated {len(parsed['sections'])} unique sections")
        print(f"   Theme: {theme.get('palette')} + {theme.get('accent')}")
        print(f"{'='*60}\n")
        
        return parsed
        
    except json.JSONDecodeError as e:
        print(f"❌ AI JSON PARSE ERROR: {str(e)}")
        print(f"   Response preview: {response[:200] if 'response' in locals() else 'N/A'}...")
        print(f"🔄 Using premium fallback...")
        return _generate_complete_fallback(business_name, prompt, sections, structure, industry)
        
    except Exception as e:
        print(f"❌ AI GENERATION FAILED: {str(e)}")
        print(f"🔄 Using premium fallback...")
        return _generate_complete_fallback(business_name, prompt, sections, structure, industry)


def _generate_complete_fallback(business_name: str, prompt: str, sections: List[str], structure: Dict[str, Any], industry: Dict[str, str]) -> Dict[str, Any]:
    """Generate complete fallback website when AI totally fails."""
    palette = structure["palette"]
    theme = structure.get("theme", {})
    is_dark = theme.get("palette", "dark") == "dark"
    
    out_sections = {}
    for section_key in sections:
        out_sections[section_key] = _generate_fallback_section(section_key, business_name, industry, palette, is_dark)
    
    return {
        "business_name": business_name,
        "sections": out_sections,
        "seo": {
            "title": f"{business_name} - Professional Services",
            "description": f"Discover {business_name}. {prompt[:100]}",
            "keywords": ["professional", "quality", "premium"],
        },
    }

def rewrite_content(original_text: str, tone: str = "professional", business_context: str = "") -> List[str]:
    """Generate alternative versions of content with AI."""
    try:
        prompt_text = f"""Rewrite this text in 3 different ways:

Original: {original_text}
Tone: {tone}
Context: {business_context}

Return ONLY a JSON array: ["version1", "version2", "version3"]
Each version should maintain the same meaning but with different phrasing."""

        response = chat_completion(
            system="You are a professional copywriter. Output only valid JSON arrays with no markdown formatting.",
            user=prompt_text,
            temperature=0.8
        )
        
        # Clean response
        response = response.strip()
        if response.startswith("```json"):
            response = response[7:]
        if response.startswith("```"):
            response = response[3:]
        if response.endswith("```"):
            response = response[:-3]
        response = response.strip()
        
        alternatives = json.loads(response)
        
        if isinstance(alternatives, list) and len(alternatives) >= 3:
            return alternatives[:3]
        else:
            return [original_text] * 3
            
    except Exception as e:
        print(f"Content rewrite failed: {e}")
        return [original_text] * 3


def generate_ai_plan(ai_input: Dict[str, Any], version: int = 1) -> Dict[str, Any]:
    """Main entry point for AI website generation."""
    prompt = ai_input.get("prompt", "")
    business_name = ai_input.get("business_name", "Your Business")
    goal = ai_input.get("primary_goal", "Get started")

    business_type = "business"
    if any(w in prompt.lower() for w in ["restaurant", "cafe", "food", "pizza"]):
        business_type = "restaurant"

    # Generate structure (theme, sections)
    structure = generate_ai_structure(business_type, goal, version, prompt)
    
    # Generate content with AI (or fallback)
    content = generate_html_sections(business_name, prompt, business_type, structure)

    return {
        "template": business_type,
        "structure": structure,
        "content": content
    }