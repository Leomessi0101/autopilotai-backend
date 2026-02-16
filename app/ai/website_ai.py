import random
import json
from typing import Dict, Any, List
from app.ai.openai_client import chat_completion

# --- DESIGN TOKENS ---
GLASS_DARK = "backdrop-blur-xl bg-white/5 border border-white/10 text-white"
GLASS_LIGHT = "backdrop-blur-xl bg-gray-50/80 border border-gray-200 text-gray-900"
HOVER_TRANSITION = "transition-all duration-500 ease-in-out hover:-translate-y-2 hover:shadow-2xl"

# --- THEME ENGINE ---
THEMES = [
    {"id": "pro_light", "mode": "light", "bg": "bg-white", "text": "text-gray-900", "muted": "text-gray-600", "primary": "blue-600", "grad": "from-blue-600 to-indigo-600", "panel": GLASS_LIGHT},
    {"id": "luxury_dark", "mode": "dark", "bg": "bg-slate-950", "text": "text-white", "muted": "text-gray-400", "primary": "indigo-500", "grad": "from-indigo-500 to-purple-600", "panel": GLASS_DARK},
    {"id": "clean_slate", "mode": "light", "bg": "bg-slate-50", "text": "text-slate-900", "muted": "text-slate-600", "primary": "emerald-600", "grad": "from-emerald-600 to-teal-600", "panel": GLASS_LIGHT}
]

class UltimateGenerator:
    def __init__(self, business_name: str, prompt: str):
        self.name = business_name
        self.prompt = prompt
        # Logic: If prompt contains "medical", "law", or "clean", lean towards Light Mode.
        self.theme = random.choice(THEMES)
        self.data = {}

    def get_ai_payload(self):
        """One massive AI call to plan the entire site content at once."""
        system_msg = "You are a world-class Web Architect. Output ONLY valid JSON."
        user_msg = f"""
        Plan a premium website for '{self.name}'. Context: {self.prompt}
        Generate content for: Hero, Features (3), Pricing (3 tiers), FAQ (3), Testimonials (2).
        Use Lucide icon names. Suggest 5 Unsplash keywords for professional imagery.
        
        JSON structure:
        {{
          "nav": ["Services", "Pricing", "FAQ", "Contact"],
          "hero": {{"h1": "", "sub": "", "cta": ""}},
          "features": [{{"icon": "", "t": "", "d": ""}}],
          "pricing": [{{"plan": "", "price": "", "feats": []}}],
          "testimonials": [{{"name": "", "quote": ""}}],
          "faq": [{{"q": "", "a": ""}}],
          "img_kw": []
        }}
        """
        res = chat_completion(system=system_msg, user=user_msg, temperature=0.7)
        return json.loads(res.strip().replace("```json", "").replace("```", ""))

    def render_nav(self):
        links = "".join([f'<li><a href="#{l.lower()}" class="hover:text-{self.theme["primary"]} transition-colors">{l}</a></li>' for l in self.data['nav']])
        return f"""
        <nav class="fixed top-0 w-full z-50 {self.theme['panel']} py-4 border-b">
            <div class="container mx-auto px-6 flex justify-between items-center">
                <a href="#" class="text-2xl font-black tracking-tighter">{self.name}</a>
                <ul class="hidden md:flex gap-8 font-medium">{links}</ul>
                <a href="#contact" class="px-6 py-2 bg-gradient-to-r {self.theme['grad']} text-white rounded-full font-bold">Start Now</a>
            </div>
        </nav>"""

    def render_hero(self):
        img = f"https://images.unsplash.com/photo-1?auto=format&fit=crop&q=80&w=1200&keywords={self.data['img_kw'][0]}"
        return f"""
        <section class="relative min-h-screen flex items-center {self.theme['bg']} pt-20">
            <div class="container mx-auto px-6 grid lg:grid-cols-2 gap-12 relative z-10">
                <div>
                    <h1 class="text-6xl md:text-8xl font-black {self.theme['text']} leading-tight mb-6">{self.data['hero']['h1']}</h1>
                    <p class="text-xl {self.theme['muted']} mb-10">{self.data['hero']['sub']}</p>
                    <a href="#pricing" class="inline-block px-10 py-5 bg-gradient-to-r {self.theme['grad']} text-white rounded-2xl font-bold text-lg {HOVER_TRANSITION}">{self.data['hero']['cta']}</a>
                </div>
                <div class="relative"><img src="{img}" class="rounded-[2rem] shadow-2xl border" alt="hero"/></div>
            </div>
        </section>"""

    def render_features(self):
        items = "".join([f"""
            <div class="{self.theme['panel']} p-8 rounded-3xl {HOVER_TRANSITION}">
                <div class="w-12 h-12 mb-6 rounded-xl bg-{self.theme['primary']}/10 flex items-center justify-center text-2xl">✨</div>
                <h3 class="text-2xl font-bold mb-4">{f['t']}</h3>
                <p class="{self.theme['muted']}">{f['d']}</p>
            </div>""" for f in self.data['features']])
        return f'<section id="services" class="py-24 {self.theme["bg"]}"><div class="container mx-auto px-6 grid md:grid-cols-3 gap-8">{items}</div></section>'

    def render_pricing(self):
        tiers = "".join([f"""
            <div class="{self.theme['panel']} p-10 rounded-[2.5rem] border hover:border-{self.theme['primary']} transition-all">
                <h3 class="text-xl font-bold mb-2">{t['plan']}</h3>
                <div class="text-4xl font-black mb-6">{t['price']}</div>
                <ul class="space-y-4 mb-8">{"".join([f'<li class="text-sm opacity-80">✓ {feat}</li>' for feat in t['feats']])}</ul>
                <button class="w-full py-4 rounded-xl bg-{self.theme['primary']} text-white font-bold">Select Plan</button>
            </div>""" for t in self.data['pricing']])
        return f'<section id="pricing" class="py-24 {self.theme["bg"]}"><div class="container mx-auto px-6 grid md:grid-cols-3 gap-8">{tiers}</div></section>'

    def build(self):
        self.data = self.get_ai_payload()
        sections = [self.render_nav(), self.render_hero(), self.render_features(), self.render_pricing()]
        return {"html": f'<div class="{self.theme["bg"]} min-h-screen font-sans" style="scroll-behavior: smooth;">' + "".join(sections) + "</div>"}

# --- EXPORTS ---

def generate_ai_plan(ai_input: Dict[str, Any], version: int = 1, **kwargs) -> Dict[str, Any]:
    gen = UltimateGenerator(ai_input.get("business_name", "Business"), ai_input.get("prompt", ""))
    result = gen.build()
    return {
        "template": "ultimate",
        "structure": {"sections": ["nav", "hero", "features", "pricing", "contact"]},
        "content": result
    }

def rewrite_content(original_text: str, tone: str = "professional", business_context: str = "") -> List[str]:
    try:
        res = chat_completion(system="Copywriter API. JSON only.", user=f"Rewrite '{original_text}' 3 times in {tone} tone. JSON array.", temperature=0.8)
        return json.loads(res.strip().replace("```json", "").replace("```", ""))
    except: return [original_text] * 3