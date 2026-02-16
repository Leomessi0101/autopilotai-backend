import random
import json
import logging
import traceback
from typing import Dict, Any, List, Optional
from enum import Enum

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

try:
    from app.ai.openai_client import chat_completion
    AI_AVAILABLE = True
except ImportError as e:
    logger.warning(f"AI client not available: {e}")
    AI_AVAILABLE = False
    
    def chat_completion(system: str, user: str, temperature: float = 0.7) -> str:
        return json.dumps({
            "nav": ["Home", "About", "Contact"],
            "hero": {"h1": "Welcome", "sub": "Built with AI", "cta": "Learn More"},
            "content": [],
            "cta_text": "Get Started",
            "unsplash_keywords": ["professional"]
        })

# ============================================================================
# UNSPLASH IMAGE HELPER
# ============================================================================

def get_unsplash_image(keyword: str, index: int = 0, width: int = 800) -> str:
    """Generate unique Unsplash image URL with variety"""
    photo_ids = {
        "football": ["xzpxpQxR3L8", "1sJU0W-r8Dw", "5A2W5InI6aw", "n6W6cXlm_0M"],
        "sports": ["cAtzHUz7Z8g", "6PF6DaiWn48", "wVBffFe5vU4", "u3bF6L7D9t8"],
        "team": ["xyQd_jXWULI", "tV_rDYdjCFM", "JFUWe-K7B-0", "4Xpwy_5X1IA"],
        "restaurant": ["o-g04ejjcv8", "rDLW5IL_yDE", "7jTJkv6wvfg", "vRVHKwWLsToI"],
        "fitness": ["3f9wSAq5H5w", "1sJU0W-r8Dw", "cAtzHUz7Z8g", "5A2W5InI6aw"],
        "saas": ["l3N97FvodXw", "6PF6DaiWn48", "wVBffFe5vU4", "u3bF6L7D9t8"],
        "ecommerce": ["0X8tNUtn5gE", "1iYR-7XOF0A", "n6W6cXlm_0M", "3s7uNIw8bAA"],
        "default": ["xzpxpQxR3L8", "1sJU0W-r8Dw", "5A2W5InI6aw", "n6W6cXlm_0M"],
    }
    
    ids = photo_ids.get(keyword, photo_ids["default"])
    photo_id = ids[index % len(ids)]
    return f"https://images.unsplash.com/photo-{photo_id}?w={width}&auto=format&fit=crop&q=80&fm=webp"

# ============================================================================
# DESIGN SYSTEM
# ============================================================================

GLASS_DARK = "backdrop-blur-3xl bg-gradient-to-br from-white/8 to-white/3 border border-white/15 rounded-2xl shadow-2xl"
GLASS_LIGHT = "backdrop-blur-3xl bg-gradient-to-br from-gray-50/90 to-gray-100/70 border border-gray-200/60 rounded-2xl shadow-lg"

HOVER_LIFT = "transition-all duration-500 ease-out hover:-translate-y-3 hover:shadow-2xl"
HOVER_GLOW = "transition-all duration-500 ease-out hover:shadow-lg hover:shadow-current/20"

HEADING_HERO = "text-7xl md:text-8xl font-black tracking-tighter leading-[1.1]"
HEADING_SECTION = "text-5xl md:text-6xl font-black tracking-tight leading-[1.15]"
HEADING_FEATURE = "text-2xl md:text-3xl font-bold tracking-tight"

PADDING_SECTION = "py-32 md:py-40"
PADDING_CONTAINER = "px-6 md:px-8 lg:px-12"

THEMES = {
    "saas": {
        "id": "pro_light",
        "bg": "bg-white",
        "bg_alt": "bg-gray-50",
        "text": "text-gray-950",
        "text_muted": "text-gray-600",
        "primary": "blue",
        "grad": "from-blue-600 via-blue-500 to-cyan-500",
        "glass": GLASS_LIGHT,
    },
    "sports": {
        "id": "sports_dark",
        "bg": "bg-gray-950",
        "bg_alt": "bg-gray-900",
        "text": "text-white",
        "text_muted": "text-gray-300",
        "primary": "red",
        "grad": "from-red-600 via-red-500 to-orange-500",
        "glass": GLASS_DARK,
    },
    "restaurant": {
        "id": "warm_cream",
        "bg": "bg-amber-50",
        "bg_alt": "bg-white",
        "text": "text-amber-950",
        "text_muted": "text-amber-700",
        "primary": "amber",
        "grad": "from-amber-500 via-orange-500 to-rose-500",
        "glass": GLASS_LIGHT,
    },
    "fitness": {
        "id": "fitness_dark",
        "bg": "bg-slate-950",
        "bg_alt": "bg-slate-900",
        "text": "text-white",
        "text_muted": "text-gray-300",
        "primary": "green",
        "grad": "from-green-500 via-emerald-500 to-teal-500",
        "glass": GLASS_DARK,
    },
    "ecommerce": {
        "id": "ecom_dark",
        "bg": "bg-black",
        "bg_alt": "bg-gray-900",
        "text": "text-white",
        "text_muted": "text-gray-400",
        "primary": "purple",
        "grad": "from-purple-600 via-pink-500 to-red-500",
        "glass": GLASS_DARK,
    },
}

# ============================================================================
# INDUSTRY DETECTION
# ============================================================================

def detect_industry(prompt: str) -> str:
    """Detect industry from prompt"""
    prompt_lower = (prompt or "").lower()
    
    if any(word in prompt_lower for word in ["football", "soccer", "basketball", "baseball", "team", "sports", "league", "players", "coach", "game", "match"]):
        return "sports"
    elif any(word in prompt_lower for word in ["restaurant", "cafe", "pizza", "burger", "food", "chef", "menu", "dining"]):
        return "restaurant"
    elif any(word in prompt_lower for word in ["gym", "fitness", "trainer", "workout", "exercise", "health", "personal training"]):
        return "fitness"
    elif any(word in prompt_lower for word in ["shop", "store", "ecommerce", "sell", "product", "buy", "order"]):
        return "ecommerce"
    else:
        return "saas"

# ============================================================================
# INDUSTRY-SPECIFIC GENERATORS
# ============================================================================

class SaaSWebsite:
    """High-conversion SaaS website"""
    
    def __init__(self, business_name: str, prompt: str, theme: Dict):
        self.name = business_name
        self.prompt = prompt
        self.theme = theme
        self.data = self._get_ai_payload()
    
    def _get_ai_payload(self) -> Dict:
        if not AI_AVAILABLE:
            return {
                "nav": ["Features", "Pricing", "FAQ"],
                "hero": {"h1": "The Best Solution", "sub": "For your business", "cta": "Get Started Free"},
                "features": [
                    {"title": "Feature One", "description": "Amazing capability", "icon": "✨"},
                ],
                "pricing": [
                    {"name": "Starter", "price": "$29", "features": ["Feature A"], "featured": False},
                    {"name": "Pro", "price": "$99", "features": ["Feature A", "Feature B"], "featured": True},
                ],
            }
        
        system = "You are a SaaS marketing expert. Output ONLY valid JSON."
        user = f"""Create a SaaS website for '{self.name}'.
        Context: {self.prompt}
        
        Generate JSON with:
        - nav: ["Features", "Pricing", "FAQ", "Contact"]
        - hero: {{h1, sub, cta}}
        - features: array of 3 {{title, description, icon}}
        - pricing: array of 3 {{name, price, features: array of 5, featured: boolean}}
        - testimonials: array of 2 {{name, company, quote}}
        - faq: array of 3 {{q, a}}
        - cta_text: string
        """
        
        try:
            res = chat_completion(system=system, user=user, temperature=0.7)
            return json.loads(res.strip().replace("```json", "").replace("```", ""))
        except:
            return {}
    
    def build(self) -> str:
        """Build SaaS website"""
        return f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>{self.name}</title>
            <script src="https://cdn.tailwindcss.com"></script>
        </head>
        <body class="{self.theme['bg']} {self.theme['text']} min-h-screen">
            <!-- HEADER -->
            <header class="sticky top-0 z-50 {self.theme['bg']}/95 backdrop-blur border-b border-white/10">
                <div class="max-w-7xl mx-auto px-6 py-4 flex justify-between items-center">
                    <h1 class="text-2xl font-black">{self.name}</h1>
                    <a href="#" class="px-6 py-2 bg-gradient-to-r {self.theme['grad']} text-white rounded-lg font-bold">Start Free</a>
                </div>
            </header>

            <!-- HERO -->
            <section class="relative min-h-screen flex items-center justify-center {self.theme['bg_alt']}">
                <div class="max-w-5xl mx-auto px-6 text-center">
                    <h2 class="text-6xl md:text-8xl font-black mb-6">{self.data.get('hero', {}).get('h1', 'Powerful Solution')}</h2>
                    <p class="text-xl {self.theme['text_muted']} mb-12 max-w-2xl mx-auto">{self.data.get('hero', {}).get('sub', 'For your business')}</p>
                    <a href="#" class="inline-block px-10 py-5 bg-gradient-to-r {self.theme['grad']} text-white rounded-xl font-bold text-lg {HOVER_LIFT}">
                        {self.data.get('hero', {}).get('cta', 'Get Started')}
                    </a>
                </div>
            </section>

            <!-- FEATURES -->
            <section class="{self.theme['bg']} {PADDING_SECTION}">
                <div class="max-w-6xl mx-auto {PADDING_CONTAINER}">
                    <h2 class="text-5xl font-black mb-20 text-center">Why Choose Us</h2>
                    <div class="grid md:grid-cols-3 gap-8">
                        {chr(10).join([f'''
                        <div class="{self.theme['bg_alt']} p-10 rounded-2xl {HOVER_LIFT}">
                            <div class="text-5xl mb-6">{f.get('icon', '✨')}</div>
                            <h3 class="text-2xl font-bold mb-3">{f.get('title', 'Feature')}</h3>
                            <p class="{self.theme['text_muted']}">{f.get('description', 'Amazing feature')}</p>
                        </div>''' for f in self.data.get('features', [])])}
                    </div>
                </div>
            </section>

            <!-- PRICING -->
            <section class="{self.theme['bg_alt']} {PADDING_SECTION}">
                <div class="max-w-6xl mx-auto {PADDING_CONTAINER}">
                    <h2 class="text-5xl font-black mb-20 text-center">Simple Pricing</h2>
                    <div class="grid md:grid-cols-3 gap-8 max-w-5xl mx-auto">
                        {chr(10).join([f'''
                        <div class="p-10 rounded-2xl {self.theme['bg']}">
                            <h3 class="text-2xl font-bold mb-4">{p.get('name', 'Plan')}</h3>
                            <div class="text-4xl font-black mb-6">{p.get('price', '$0')}<span class="text-lg {self.theme['text_muted']}">/mo</span></div>
                            <ul class="space-y-3 mb-8">
                                {chr(10).join([f'<li class="{self.theme['text_muted']} text-sm">✓ {feat}</li>' for feat in p.get('features', [])])}
                            </ul>
                            <button class="w-full py-3 rounded-lg font-bold bg-gradient-to-r {self.theme['grad']} text-white">Get Started</button>
                        </div>''' for p in self.data.get('pricing', [])])}
                    </div>
                </div>
            </section>

            <!-- CTA -->
            <section class="{self.theme['bg']} {PADDING_SECTION} text-center">
                <h2 class="text-5xl font-black mb-8">Ready to get started?</h2>
                <a href="#" class="inline-block px-10 py-5 bg-gradient-to-r {self.theme['grad']} text-white rounded-xl font-bold text-lg {HOVER_LIFT}">
                    Start Free Today
                </a>
            </section>

            <!-- FOOTER -->
            <footer class="{self.theme['bg_alt']} border-t border-white/10 py-12">
                <div class="max-w-7xl mx-auto px-6 text-center {self.theme['text_muted']} text-sm">
                    <p>&copy; 2026 {self.name}. All rights reserved.</p>
                </div>
            </footer>
        </body>
        </html>
        """


class SportsTeamWebsite:
    """Dynamic sports team website"""
    
    def __init__(self, business_name: str, prompt: str, theme: Dict):
        self.name = business_name
        self.prompt = prompt
        self.theme = theme
        self.data = self._get_ai_payload()
    
    def _get_ai_payload(self) -> Dict:
        if not AI_AVAILABLE:
            return {
                "nav": ["Schedule", "Roster", "News", "Tickets"],
                "hero": {"h1": "Welcome to the Team", "sub": "Elite Athletes", "cta": "Get Tickets"},
            }
        
        system = "You are a sports team marketing expert. Output ONLY valid JSON."
        user = f"""Create a sports team website for '{self.name}'.
        Context: {self.prompt}
        
        Generate JSON with:
        - nav: ["Schedule", "Roster", "News", "Tickets"]
        - hero: {{h1, sub, cta}}
        - highlights: array of 3 {{title, description}}
        - news: array of 2 {{title, date, content}}
        - cta_text: string
        """
        
        try:
            res = chat_completion(system=system, user=user, temperature=0.7)
            return json.loads(res.strip().replace("```json", "").replace("```", ""))
        except:
            return {}
    
    def build(self) -> str:
        """Build sports team website"""
        return f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>{self.name}</title>
            <script src="https://cdn.tailwindcss.com"></script>
        </head>
        <body class="{self.theme['bg']} {self.theme['text']} min-h-screen">
            <!-- HEADER -->
            <header class="sticky top-0 z-50 {self.theme['bg']}/95 backdrop-blur border-b border-white/20">
                <div class="max-w-7xl mx-auto px-6 py-4 flex justify-between items-center">
                    <h1 class="text-3xl font-black tracking-tighter">{self.name}</h1>
                    <nav class="hidden md:flex gap-8 font-semibold">
                        <a href="#" class="hover:text-white transition">Schedule</a>
                        <a href="#" class="hover:text-white transition">Roster</a>
                        <a href="#" class="hover:text-white transition">News</a>
                    </nav>
                    <a href="#" class="px-6 py-2 bg-gradient-to-r {self.theme['grad']} text-white rounded-lg font-bold">Get Tickets</a>
                </div>
            </header>

            <!-- HERO - SPORTS SPECIFIC -->
            <section class="relative min-h-screen flex items-center justify-center overflow-hidden">
                <div class="absolute inset-0 opacity-40">
                    <div class="absolute top-0 left-0 w-96 h-96 bg-gradient-to-r {self.theme['grad']} blur-3xl"></div>
                </div>
                <div class="relative z-10 max-w-5xl mx-auto px-6 text-center">
                    <span class="inline-block mb-6 px-4 py-2 {self.theme['bg_alt']} rounded-full text-sm font-bold">🏆 Championship Team</span>
                    <h1 class="text-7xl md:text-9xl font-black mb-6 leading-tight">{self.data.get('hero', {}).get('h1', 'Elite Squad')}</h1>
                    <p class="text-2xl {self.theme['text_muted']} mb-12 max-w-2xl mx-auto">{self.data.get('hero', {}).get('sub', 'The best athletes')}</p>
                    <div class="flex flex-col sm:flex-row gap-4 justify-center">
                        <a href="#" class="px-10 py-5 bg-gradient-to-r {self.theme['grad']} text-white rounded-xl font-bold text-lg {HOVER_LIFT}">
                            {self.data.get('hero', {}).get('cta', 'Get Tickets')}
                        </a>
                        <a href="#" class="px-10 py-5 {self.theme['bg_alt']} rounded-xl font-bold text-lg {HOVER_LIFT}">
                            View Schedule →
                        </a>
                    </div>
                </div>
            </section>

            <!-- HIGHLIGHTS -->
            <section class="{self.theme['bg_alt']} {PADDING_SECTION}">
                <div class="max-w-6xl mx-auto {PADDING_CONTAINER}">
                    <h2 class="text-5xl font-black mb-20 text-center">Season Highlights</h2>
                    <div class="grid md:grid-cols-3 gap-8">
                        {chr(10).join([f'''
                        <div class="{self.theme['bg']} p-10 rounded-2xl border-2 border-white/10 {HOVER_LIFT}">
                            <h3 class="text-2xl font-black mb-4">{h.get('title', 'Match')}</h3>
                            <p class="{self.theme['text_muted']}">{h.get('description', 'Epic performance')}</p>
                        </div>''' for h in self.data.get('highlights', [])])}
                    </div>
                </div>
            </section>

            <!-- NEWS -->
            <section class="{self.theme['bg']} {PADDING_SECTION}">
                <div class="max-w-6xl mx-auto {PADDING_CONTAINER}">
                    <h2 class="text-5xl font-black mb-20 text-center">Latest News</h2>
                    <div class="grid md:grid-cols-2 gap-8 max-w-4xl mx-auto">
                        {chr(10).join([f'''
                        <article class="{self.theme['bg_alt']} p-8 rounded-2xl border border-white/10">
                            <p class="text-sm {self.theme['text_muted']} mb-3">{n.get('date', 'Today')}</p>
                            <h3 class="text-2xl font-bold mb-4">{n.get('title', 'News')}</h3>
                            <p class="{self.theme['text_muted']}">{n.get('content', 'Latest updates')}</p>
                        </article>''' for n in self.data.get('news', [])])}
                    </div>
                </div>
            </section>

            <!-- CTA -->
            <section class="bg-gradient-to-r {self.theme['grad']} {PADDING_SECTION} text-white text-center">
                <h2 class="text-5xl font-black mb-8">Support Your Team</h2>
                <p class="text-xl mb-8 max-w-2xl mx-auto opacity-90">Get tickets to the next match and be part of the action</p>
                <a href="#" class="inline-block px-10 py-5 bg-white text-current rounded-xl font-black text-lg {HOVER_LIFT}">
                    Buy Tickets Now
                </a>
            </section>

            <!-- FOOTER -->
            <footer class="{self.theme['bg_alt']} border-t border-white/10 py-12">
                <div class="max-w-7xl mx-auto px-6 text-center {self.theme['text_muted']} text-sm">
                    <p>&copy; 2026 {self.name}. All rights reserved.</p>
                </div>
            </footer>
        </body>
        </html>
        """


class RestaurantWebsite:
    """Appetizing restaurant website"""
    
    def __init__(self, business_name: str, prompt: str, theme: Dict):
        self.name = business_name
        self.prompt = prompt
        self.theme = theme
        self.data = self._get_ai_payload()
    
    def _get_ai_payload(self) -> Dict:
        if not AI_AVAILABLE:
            return {
                "nav": ["Menu", "Reservations", "About", "Contact"],
                "hero": {"h1": "Culinary Excellence", "sub": "Finest dining", "cta": "Reserve Now"},
            }
        
        system = "You are a restaurant marketing expert. Output ONLY valid JSON."
        user = f"""Create a restaurant website for '{self.name}'.
        Context: {self.prompt}
        
        Generate JSON with:
        - nav: ["Menu", "Reservations", "About", "Contact"]
        - hero: {{h1, sub, cta}}
        - specialties: array of 3 {{name, description, icon}}
        - cta_text: string
        """
        
        try:
            res = chat_completion(system=system, user=user, temperature=0.7)
            return json.loads(res.strip().replace("```json", "").replace("```", ""))
        except:
            return {}
    
    def build(self) -> str:
        """Build restaurant website"""
        return f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>{self.name}</title>
            <script src="https://cdn.tailwindcss.com"></script>
        </head>
        <body class="{self.theme['bg']} {self.theme['text']} min-h-screen">
            <!-- HEADER -->
            <header class="sticky top-0 z-50 {self.theme['bg']}/95 backdrop-blur border-b border-{self.theme['primary']}/20">
                <div class="max-w-7xl mx-auto px-6 py-4 flex justify-between items-center">
                    <h1 class="text-3xl font-black italic">{self.name}</h1>
                    <a href="#" class="px-6 py-2 bg-{self.theme['primary']}-600 text-white rounded-lg font-bold">Reserve</a>
                </div>
            </header>

            <!-- HERO - FOOD FOCUSED -->
            <section class="relative min-h-screen flex items-center justify-center {self.theme['bg_alt']}">
                <div class="absolute inset-0">
                    <img src="{get_unsplash_image('restaurant', 0, 1600)}" class="w-full h-full object-cover opacity-20" />
                </div>
                <div class="relative z-10 max-w-5xl mx-auto px-6 text-center">
                    <span class="inline-block mb-6 px-4 py-2 {self.theme['bg']} rounded-full text-sm font-bold">🍽️ Award Winning</span>
                    <h1 class="text-7xl md:text-8xl font-black mb-6">{self.data.get('hero', {}).get('h1', 'Fine Dining')}</h1>
                    <p class="text-2xl {self.theme['text_muted']} mb-12 max-w-2xl mx-auto">{self.data.get('hero', {}).get('sub', 'Exquisite cuisine')}</p>
                    <a href="#" class="inline-block px-10 py-5 bg-{self.theme['primary']}-600 text-white rounded-xl font-bold text-lg {HOVER_LIFT}">
                        {self.data.get('hero', {}).get('cta', 'Reserve Table')}
                    </a>
                </div>
            </section>

            <!-- SPECIALTIES -->
            <section class="{self.theme['bg']} {PADDING_SECTION}">
                <div class="max-w-6xl mx-auto {PADDING_CONTAINER}">
                    <h2 class="text-5xl font-black mb-20 text-center italic">House Specialties</h2>
                    <div class="grid md:grid-cols-3 gap-12">
                        {chr(10).join([f'''
                        <div class="text-center {HOVER_LIFT}">
                            <div class="text-6xl mb-6">{s.get('icon', '🍽️')}</div>
                            <h3 class="text-2xl font-bold mb-4 italic">{s.get('name', 'Dish')}</h3>
                            <p class="{self.theme['text_muted']}">{s.get('description', 'Delicious')}</p>
                        </div>''' for s in self.data.get('specialties', [])])}
                    </div>
                </div>
            </section>

            <!-- CTA -->
            <section class="bg-gradient-to-r {self.theme['grad']} {PADDING_SECTION} text-center text-white">
                <h2 class="text-5xl font-black mb-8 italic">Experience Culinary Magic</h2>
                <a href="#" class="inline-block px-10 py-5 bg-white text-current rounded-xl font-black text-lg {HOVER_LIFT}">
                    Make a Reservation
                </a>
            </section>

            <!-- FOOTER -->
            <footer class="{self.theme['bg_alt']} border-t border-white/10 py-12">
                <div class="max-w-7xl mx-auto px-6 text-center {self.theme['text_muted']} text-sm">
                    <p>&copy; 2026 {self.name}. All rights reserved.</p>
                </div>
            </footer>
        </body>
        </html>
        """


class FitnessWebsite:
    """High-energy fitness website"""
    
    def __init__(self, business_name: str, prompt: str, theme: Dict):
        self.name = business_name
        self.prompt = prompt
        self.theme = theme
        self.data = self._get_ai_payload()
    
    def _get_ai_payload(self) -> Dict:
        if not AI_AVAILABLE:
            return {
                "nav": ["Programs", "Classes", "Trainers", "Contact"],
                "hero": {"h1": "Transform Your Body", "sub": "Elite fitness training", "cta": "Start Free Trial"},
            }
        
        system = "You are a fitness marketing expert. Output ONLY valid JSON."
        user = f"""Create a fitness website for '{self.name}'.
        Context: {self.prompt}
        
        Generate JSON with:
        - nav: ["Programs", "Classes", "Trainers", "Contact"]
        - hero: {{h1, sub, cta}}
        - programs: array of 3 {{name, description, icon}}
        - cta_text: string
        """
        
        try:
            res = chat_completion(system=system, user=user, temperature=0.7)
            return json.loads(res.strip().replace("```json", "").replace("```", ""))
        except:
            return {}
    
    def build(self) -> str:
        """Build fitness website"""
        return f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>{self.name}</title>
            <script src="https://cdn.tailwindcss.com"></script>
        </head>
        <body class="{self.theme['bg']} {self.theme['text']} min-h-screen">
            <!-- HEADER -->
            <header class="sticky top-0 z-50 {self.theme['bg']}/95 backdrop-blur border-b border-white/10">
                <div class="max-w-7xl mx-auto px-6 py-4 flex justify-between items-center">
                    <h1 class="text-3xl font-black">{self.name}</h1>
                    <a href="#" class="px-6 py-2 bg-gradient-to-r {self.theme['grad']} text-white rounded-lg font-bold">Join Now</a>
                </div>
            </header>

            <!-- HERO - ENERGETIC -->
            <section class="relative min-h-screen flex items-center justify-center overflow-hidden {self.theme['bg_alt']}">
                <div class="absolute inset-0 opacity-30">
                    <div class="absolute top-0 left-0 w-96 h-96 bg-gradient-to-r {self.theme['grad']} blur-3xl"></div>
                </div>
                <div class="relative z-10 max-w-5xl mx-auto px-6 text-center">
                    <span class="inline-block mb-6 px-4 py-2 {self.theme['bg']} rounded-full text-sm font-bold">💪 GET RIPPED</span>
                    <h1 class="text-7xl md:text-9xl font-black mb-6 uppercase">{self.data.get('hero', {}).get('h1', 'Transform Now')}</h1>
                    <p class="text-2xl {self.theme['text_muted']} mb-12 max-w-2xl mx-auto">{self.data.get('hero', {}).get('sub', 'Elite training')}</p>
                    <a href="#" class="inline-block px-10 py-5 bg-gradient-to-r {self.theme['grad']} text-white rounded-xl font-black text-lg uppercase {HOVER_LIFT}">
                        {self.data.get('hero', {}).get('cta', 'Start Now')}
                    </a>
                </div>
            </section>

            <!-- PROGRAMS -->
            <section class="{self.theme['bg']} {PADDING_SECTION}">
                <div class="max-w-6xl mx-auto {PADDING_CONTAINER}">
                    <h2 class="text-5xl font-black mb-20 text-center uppercase">Training Programs</h2>
                    <div class="grid md:grid-cols-3 gap-8">
                        {chr(10).join([f'''
                        <div class="{self.theme['bg_alt']} p-10 rounded-2xl border-2 border-{self.theme['primary']}/50 {HOVER_LIFT}">
                            <div class="text-5xl mb-6">{p.get('icon', '🏋️')}</div>
                            <h3 class="text-2xl font-black mb-4 uppercase">{p.get('name', 'Program')}</h3>
                            <p class="{self.theme['text_muted']}">{p.get('description', 'Amazing results')}</p>
                        </div>''' for p in self.data.get('programs', [])])}
                    </div>
                </div>
            </section>

            <!-- CTA -->
            <section class="bg-gradient-to-r {self.theme['grad']} {PADDING_SECTION} text-white text-center">
                <h2 class="text-5xl font-black mb-8 uppercase">Your Transformation Starts Today</h2>
                <a href="#" class="inline-block px-10 py-5 bg-white text-{self.theme['primary']}-600 rounded-xl font-black text-lg uppercase {HOVER_LIFT}">
                    Claim Free Trial
                </a>
            </section>

            <!-- FOOTER -->
            <footer class="{self.theme['bg_alt']} border-t border-white/10 py-12">
                <div class="max-w-7xl mx-auto px-6 text-center {self.theme['text_muted']} text-sm">
                    <p>&copy; 2026 {self.name}. All rights reserved.</p>
                </div>
            </footer>
        </body>
        </html>
        """

# ============================================================================
# MAIN GENERATOR
# ============================================================================

class MasterArchitect:
    def __init__(self, business_name: str, prompt: str, version: int = 1):
        self.name = business_name
        self.prompt = prompt
        self.version = version
        self.industry = detect_industry(prompt)
        self.theme = THEMES.get(self.industry, THEMES["saas"])
        logger.info(f"Industry: {self.industry}, Theme: {self.theme['id']}")
    
    def build(self) -> Dict[str, Any]:
        """Build website based on industry"""
        
        if self.industry == "sports":
            site = SportsTeamWebsite(self.name, self.prompt, self.theme)
        elif self.industry == "restaurant":
            site = RestaurantWebsite(self.name, self.prompt, self.theme)
        elif self.industry == "fitness":
            site = FitnessWebsite(self.name, self.prompt, self.theme)
        else:
            site = SaaSWebsite(self.name, self.prompt, self.theme)
        
        html = site.build()
        
        return {
            "html": html,
            "metadata": {
                "business_name": self.name,
                "industry": self.industry,
                "theme": self.theme['id'],
                "version": self.version,
                "status": "success"
            }
        }


def generate_ai_plan(ai_input: Dict[str, Any], version: int = 1, **kwargs) -> Dict[str, Any]:
    """Main entry point"""
    try:
        business_name = ai_input.get("business_name", "Business")
        prompt = ai_input.get("prompt", "")
        
        architect = MasterArchitect(business_name, prompt, version=version)
        return architect.build()
    except Exception as e:
        logger.error(f"Error: {e}\n{traceback.format_exc()}")
        return {
            "html": f"<html><body><h1>Error</h1><p>{str(e)}</p></body></html>",
            "metadata": {"status": "error", "error": str(e)}
        }


def rewrite_content(original_text: str, tone: str = "professional", business_context: str = "") -> List[str]:
    """Rewrite content"""
    try:
        if not AI_AVAILABLE:
            return [original_text] * 3
        
        system = "You are a copywriter. Output ONLY valid JSON."
        user = f"Rewrite '{original_text}' 3 times in {tone} tone. Output: ['v1', 'v2', 'v3']"
        
        res = chat_completion(system=system, user=user, temperature=0.8)
        result = json.loads(res.strip().replace("```json", "").replace("```", ""))
        return result if isinstance(result, list) and len(result) >= 3 else [original_text] * 3
    except:
        return [original_text] * 3


def get_design_tokens() -> Dict[str, Any]:
    """Export design tokens"""
    return {"themes": THEMES}