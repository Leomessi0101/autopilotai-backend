import random
import json
from typing import Dict, Any, List
from app.ai.openai_client import chat_completion

# --- GLOBAL DESIGN TOKENS ---
SHADOW_FLARE = "shadow-[0_0_50px_-12px_rgba(0,0,0,0.5)]"
GLASS_PANEL = "backdrop-blur-xl bg-white/5 border border-white/10"
HOVER_LIFT = "hover:-translate-y-2 hover:shadow-2xl transition-all duration-500 ease-out"

COLOR_THEMES = [
    {"name": "Midnight", "primary": "indigo-500", "grad": "from-indigo-600 to-violet-700", "bg": "bg-slate-950", "text": "text-white", "accent": "text-indigo-400"},
    {"name": "Obsidian", "primary": "orange-500", "grad": "from-orange-500 to-red-600", "bg": "bg-black", "text": "text-zinc-100", "accent": "text-orange-400"},
    {"name": "Nordic", "primary": "cyan-500", "grad": "from-cyan-500 to-blue-600", "bg": "bg-gray-950", "text": "text-slate-100", "accent": "text-cyan-400"},
]

class WebsiteArchitect:
    def __init__(self, business_name: str, prompt: str):
        self.business_name = business_name
        self.prompt = prompt
        self.theme = random.choice(COLOR_THEMES)
        self.links = {
            "home": "#top",
            "contact_email": "hello@autopilotai.dev", 
            "contact_phone": "+1234567890"
        }

    def get_ai_copy(self):
        system_msg = "You are an elite UX architect. Output ONLY valid JSON. No prose."
        user_msg = f"""
        Create a high-end website structure for '{self.business_name}'.
        Business Goal: {self.prompt}
        
        Required Data:
        1. Navigation: 4 logical links (e.g., Services, About, Pricing, Contact).
        2. Hero: Headline (8 words max), Subheadline, 2 CTAs.
        3. Features: 3 items with 'lucide' icon names and deep descriptions.
        4. Contact: A catchy 'Get in touch' headline.
        5. Keywords: 3 Unsplash keywords for high-end photography.
        
        JSON Format:
        {{
            "nav": ["link1", "link2", "link3", "link4"],
            "hero": {{"h1": "", "sub": "", "cta1": "", "cta2": ""}},
            "features": [{{"icon": "", "title": "", "text": ""}}],
            "img_keywords": ["k1", "k2", "k3"]
        }}
        """
        response = chat_completion(system=system_msg, user=user_msg, temperature=0.8)
        return json.loads(response.strip().replace("```json", "").replace("```", ""))

    def render_nav(self, nav_items):
        links = "".join([f'<li><a href="#{item.lower()}" class="hover:{self.theme["accent"]} transition-colors capitalize">{item}</a></li>' for item in nav_items])
        return f"""
        <nav class="fixed top-0 w-full z-50 {GLASS_PANEL} py-4">
            <div class="container mx-auto px-6 flex justify-between items-center">
                <a href="#top" class="text-2xl font-black tracking-tighter {self.theme['text']}">{self.business_name}</a>
                <ul class="hidden md:flex gap-8 {self.theme['text']} font-medium">
                    {links}
                </ul>
                <a href="#contact" class="px-6 py-2 bg-gradient-to-r {self.theme['grad']} text-white rounded-full text-sm font-bold {HOVER_LIFT}">
                    Get Started
                </a>
            </div>
        </nav>
        """

    def render_hero(self, data):
        img_url = f"https://images.unsplash.com/photo-1?auto=format&fit=crop&q=80&w=1600&q={data['img_keywords'][0]}"
        return f"""
        <section id="top" class="relative min-h-screen flex items-center overflow-hidden {self.theme['bg']}">
            <div class="absolute inset-0 z-0">
                <img src="{img_url}" class="w-full h-full object-cover opacity-40" alt="background" />
                <div class="absolute inset-0 bg-gradient-to-b from-transparent via-{self.theme['bg']}/80 to-{self.theme['bg']}"></div>
            </div>
            <div class="container mx-auto px-6 relative z-10 pt-20">
                <div class="max-w-4xl">
                    <h1 class="text-7xl md:text-9xl font-black {self.theme['text']} leading-none mb-8 animate-in fade-in slide-in-from-bottom-10 duration-1000">
                        {data['hero']['h1']}
                    </h1>
                    <p class="text-xl md:text-2xl text-gray-300 mb-12 max-w-2xl leading-relaxed">
                        {data['hero']['sub']}
                    </p>
                    <div class="flex flex-wrap gap-4">
                        <button class="px-10 py-5 bg-gradient-to-r {self.theme['grad']} text-white rounded-2xl font-bold text-lg {HOVER_LIFT}">
                            {data['hero']['cta1']}
                        </button>
                        <button class="px-10 py-5 {GLASS_PANEL} {self.theme['text']} rounded-2xl font-bold text-lg {HOVER_LIFT}">
                            {data['hero']['cta2']}
                        </button>
                    </div>
                </div>
            </div>
        </section>
        """

    def render_contact(self, h1):
        return f"""
        <section id="contact" class="py-32 {self.theme['bg']}">
            <div class="container mx-auto px-6">
                <div class="{GLASS_PANEL} rounded-[3rem] p-12 md:p-20 grid md:grid-cols-2 gap-16">
                    <div>
                        <h2 class="text-5xl font-bold {self.theme['text']} mb-6">{h1}</h2>
                        <p class="text-gray-400 text-lg mb-8">Reach out via email or phone. We usually respond within 2 hours.</p>
                        <div class="space-y-4">
                            <a href="mailto:{self.links['contact_email']}" class="flex items-center gap-4 {self.theme['text']} hover:{self.theme['accent']} transition-all">
                                <div class="w-12 h-12 rounded-full bg-white/10 flex items-center justify-center">📧</div>
                                {self.links['contact_email']}
                            </a>
                            <a href="tel:{self.links['contact_phone']}" class="flex items-center gap-4 {self.theme['text']} hover:{self.theme['accent']} transition-all">
                                <div class="w-12 h-12 rounded-full bg-white/10 flex items-center justify-center">📞</div>
                                {self.links['contact_phone']}
                            </a>
                        </div>
                    </div>
                    <form class="space-y-4">
                        <input type="text" placeholder="Your Name" class="w-full bg-white/5 border border-white/10 rounded-xl p-4 {self.theme['text']} focus:outline-none focus:border-{self.theme['primary']}" />
                        <input type="email" placeholder="Email Address" class="w-full bg-white/5 border border-white/10 rounded-xl p-4 {self.theme['text']} focus:outline-none focus:border-{self.theme['primary']}" />
                        <textarea placeholder="How can we help?" rows="4" class="w-full bg-white/5 border border-white/10 rounded-xl p-4 {self.theme['text']} focus:outline-none focus:border-{self.theme['primary']}"></textarea>
                        <button type="button" class="w-full py-4 bg-white text-black font-black rounded-xl hover:bg-gray-200 transition-colors">Send Message</button>
                    </form>
                </div>
            </div>
        </section>
        """

    def build(self):
        data = self.get_ai_copy()
        full_site = f"""
            <div class="smooth-scroll" style="scroll-behavior: smooth;">
                {self.render_nav(data['nav'])}
                {self.render_hero(data)}
                {self.render_contact("Let's Build Together")}
                <footer class="py-10 text-center text-gray-600 text-sm border-t border-white/5 {self.theme['bg']}">
                    © 2026 {self.business_name}. Built by AutopilotAI.
                </footer>
            </div>
        """
        return {"html": full_site, "meta": data}

# --- REQUIRED EXPORTS ---

def generate_ai_plan(ai_input: Dict[str, Any]) -> Dict[str, Any]:
    architect = WebsiteArchitect(
        business_name=ai_input.get("business_name", "Brand"),
        prompt=ai_input.get("prompt", "A modern business")
    )
    return {"content": architect.build()}

def rewrite_content(original_text: str, tone: str = "professional", business_context: str = "") -> List[str]:
    """Provides alternative phrasing for the AI Chatbox editor."""
    try:
        prompt_text = f"""Rewrite this marketing text in 3 different ways:
        Original: {original_text}
        Tone: {tone}
        Context: {business_context}
        Return ONLY a JSON array of strings: ["v1", "v2", "v3"]"""

        response = chat_completion(
            system="You are a professional copywriter. Output only valid JSON arrays.",
            user=prompt_text,
            temperature=0.8
        )
        
        clean_json = response.strip().replace("```json", "").replace("```", "")
        alternatives = json.loads(clean_json)
        
        return alternatives if isinstance(alternatives, list) else [original_text] * 3
    except Exception:
        return [original_text] * 3