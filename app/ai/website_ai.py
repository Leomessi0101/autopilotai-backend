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
    """AI generates EVERYTHING from scratch - NO TEMPLATES"""
    pal = structure["palette"]
    theme = structure.get("theme", {})
    sections = structure["sections"]
    is_dark = theme.get("palette", "dark") == "dark"
    inferred = _infer_business_type(prompt)
    
    tc = "text-white" if is_dark else "text-gray-900"
    tm = "text-gray-300" if is_dark else "text-gray-600"
    bg = pal["bg_dark"] if is_dark else pal["bg_light"]
    pr = pal["primary"]
    ac = pal["accent"]
    gl = pal["glow"]

    ai_prompt = f"""Create a COMPLETELY CUSTOM website for this business.

BUSINESS: {business_name}
FULL DESCRIPTION: {prompt}
INDUSTRY: {inferred}
SECTIONS NEEDED: {", ".join(sections)}

YOUR JOB: Generate COMPLETE unique HTML + content for EACH section from scratch.

VISUAL REQUIREMENTS:
- Huge gradient orbs: w-[1400px] h-[1400px] blur-[200px] opacity-20 animate-pulse
- Glassmorphism: backdrop-blur-3xl bg-white/5 border border-white/10 rounded-[40px]
- Animations: hover:-translate-y-4 hover:shadow-2xl transition-all duration-700
- Typography: text-9xl for hero, text-7xl for sections

THEME (use exact classes):
BG: bg-gradient-to-br {bg}
Text: {tc} headlines, {tm} body
Gradient: bg-gradient-to-r {pr}
Accent: {ac}
Glow: shadow-{gl}

CONTENT RULES:
1. READ THE DESCRIPTION - extract their actual services/features
2. Make headlines SPECIFIC to {business_name}
3. Use details from description in all copy
4. Industry CTAs (not generic "Get Started")

OUTPUT (pure JSON):
{{
  "business_name": "{business_name}",
  "sections": {{
    "hero": {{"html": "<section>COMPLETE CUSTOM HTML</section>", "data": {{"headline": "...", "subheadline": "...", "cta": "..."}}}},
    ... (all sections: {", ".join(sections)})
  }},
  "seo": {{"title": "...", "description": "...", "keywords": []}}
}}"""

    print(f"\n🤖 GENERATING AI WEBSITE: {business_name} ({inferred})\n")
    
    try:
        resp = chat_completion(
            system="Expert web designer. Create UNIQUE custom websites from scratch based on business descriptions. Output valid JSON only.",
            user=ai_prompt,
            temperature=0.95
        )
        
        # Clean JSON
        resp = resp.strip().replace("```json", "").replace("```", "").strip()
        parsed = json.loads(resp)
        
        if not parsed.get("sections"):
            raise ValueError("Missing sections")
        
        # Fill any missing sections by asking AI again
        for sec in sections:
            if sec not in parsed["sections"]:
                print(f"⚠️ Re-generating missing: {sec}")
                sec_resp = chat_completion(
                    system="Generate section",
                    user=f"Create {sec} section for {business_name} ({prompt[:100]}). Theme: {tc}, {pr}. Return JSON: {{\"html\": \"...\", \"data\": {{}}}}",
                    temperature=0.9
                )
                parsed["sections"][sec] = json.loads(sec_resp.strip().replace("```", ""))
        
        if not parsed.get("seo"):
            parsed["seo"] = {"title": business_name, "description": prompt[:150], "keywords": [inferred]}
        
        print(f"✅ SUCCESS! {len(parsed['sections'])} sections\n")
        return parsed
        
    except Exception as e:
        print(f"❌ FAILED: {e}\n")
        # Minimal emergency fallback
        return {
            "business_name": business_name,
            "sections": {s: {"html": f"<section class='py-40 {tc}'><div class='max-w-7xl mx-auto px-6'><h2 class='text-7xl font-bold mb-6'>{s.title()}</h2><p class='{tm}'>Content for {business_name}</p></div></section>", "data": {}} for s in sections},
            "seo": {"title": business_name, "description": prompt[:100], "keywords": [inferred]}
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