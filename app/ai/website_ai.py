import random
import json
import logging
import traceback
from typing import Dict, Any, List, Optional
from enum import Enum

# Set up logging for debugging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Try to import AI client, but fail gracefully
try:
    from app.ai.openai_client import chat_completion
    AI_AVAILABLE = True
except ImportError as e:
    logger.warning(f"AI client not available: {e}")
    AI_AVAILABLE = False
    
    def chat_completion(system: str, user: str, temperature: float = 0.7) -> str:
        """Fallback stub if OpenAI client isn't available"""
        return json.dumps({
            "nav": ["Features", "Pricing", "FAQ", "Contact"],
            "hero": {"h1": "Premium Solution", "sub": "Built for excellence", "cta": "Get Started"},
            "features": [
                {"title": "Feature One", "description": "World-class quality", "icon": "✨"},
                {"title": "Feature Two", "description": "Maximum impact", "icon": "🚀"},
                {"title": "Feature Three", "description": "Pure excellence", "icon": "💎"},
            ],
            "pricing": [
                {"name": "Starter", "price": "$29", "features": ["Feature A", "Feature B"], "featured": False},
                {"name": "Pro", "price": "$99", "features": ["Feature A", "Feature B", "Feature C"], "featured": True},
                {"name": "Enterprise", "price": "Custom", "features": ["All features"], "featured": False},
            ],
            "testimonials": [{"name": "Happy Client", "company": "Acme Corp", "quote": "Excellent service!"}],
            "faq": [{"q": "How does it work?", "a": "It's simple and powerful."}],
            "cta_text": "Ready to transform your business?",
            "unsplash_keywords": ["technology", "business", "modern", "startup", "premium"]
        })

# ============================================================================
# DESIGN SYSTEM: Elite Principles
# ============================================================================

class ColorMode(Enum):
    PROFESSIONAL_LIGHT = "pro_light"
    LUXURY_DARK = "luxury_dark"
    CLEAN_SLATE = "clean_slate"
    TECH_MIDNIGHT = "tech_midnight"
    WARM_CREAM = "warm_cream"

# Glass Morphism Foundations
GLASS_DARK = "backdrop-blur-3xl bg-gradient-to-br from-white/8 to-white/3 border border-white/15 rounded-2xl shadow-2xl"
GLASS_LIGHT = "backdrop-blur-3xl bg-gradient-to-br from-gray-50/90 to-gray-100/70 border border-gray-200/60 rounded-2xl shadow-lg"

# Hover Animations
HOVER_LIFT = "transition-all duration-500 ease-out hover:-translate-y-3 hover:shadow-2xl hover:border-opacity-100"
HOVER_GLOW = "transition-all duration-500 ease-out hover:shadow-lg hover:shadow-current/20"
HOVER_SCALE = "transition-transform duration-500 ease-out hover:scale-105"

# Typography: Elite Standards
HEADING_HERO = "text-7xl md:text-8xl font-black tracking-tighter leading-[1.1]"
HEADING_SECTION = "text-5xl md:text-6xl font-black tracking-tight leading-[1.15]"
HEADING_FEATURE = "text-2xl md:text-3xl font-bold tracking-tight"
HEADING_CARD = "text-xl font-bold"

# Spacing: Premium Breathing Room
PADDING_SECTION = "py-32 md:py-40"
PADDING_CONTAINER = "px-6 md:px-8 lg:px-12"

# Complete Theme Palette
THEMES = {
    "pro_light": {
        "id": "pro_light",
        "mode": "light",
        "bg": "bg-white",
        "bg_alt": "bg-gray-50",
        "text": "text-gray-950",
        "text_muted": "text-gray-600",
        "text_light": "text-gray-400",
        "primary": "blue",
        "primary_hex": "#2563eb",
        "grad": "from-blue-600 via-blue-500 to-cyan-500",
        "glass": GLASS_LIGHT,
        "accent": "indigo",
        "industries": ["saas", "tech", "finance", "consulting"]
    },
    "luxury_dark": {
        "id": "luxury_dark",
        "mode": "dark",
        "bg": "bg-slate-950",
        "bg_alt": "bg-slate-900",
        "text": "text-white",
        "text_muted": "text-gray-300",
        "text_light": "text-gray-500",
        "primary": "indigo",
        "primary_hex": "#6366f1",
        "grad": "from-indigo-500 via-purple-500 to-pink-500",
        "glass": GLASS_DARK,
        "accent": "purple",
        "industries": ["luxury", "fashion", "creative", "agency", "tech"]
    },
    "clean_slate": {
        "id": "clean_slate",
        "mode": "light",
        "bg": "bg-slate-50",
        "bg_alt": "bg-white",
        "text": "text-slate-900",
        "text_muted": "text-slate-600",
        "text_light": "text-slate-400",
        "primary": "emerald",
        "primary_hex": "#059669",
        "grad": "from-emerald-500 via-teal-500 to-cyan-500",
        "glass": GLASS_LIGHT,
        "accent": "teal",
        "industries": ["health", "wellness", "education", "nonprofit"]
    },
    "tech_midnight": {
        "id": "tech_midnight",
        "mode": "dark",
        "bg": "bg-gray-950",
        "bg_alt": "bg-gray-900",
        "text": "text-white",
        "text_muted": "text-gray-400",
        "text_light": "text-gray-600",
        "primary": "cyan",
        "primary_hex": "#06b6d4",
        "grad": "from-cyan-500 via-blue-500 to-purple-600",
        "glass": GLASS_DARK,
        "accent": "blue",
        "industries": ["ai", "blockchain", "software", "startup"]
    },
    "warm_cream": {
        "id": "warm_cream",
        "mode": "light",
        "bg": "bg-amber-50",
        "bg_alt": "bg-white",
        "text": "text-amber-950",
        "text_muted": "text-amber-700",
        "text_light": "text-amber-500",
        "primary": "amber",
        "primary_hex": "#d97706",
        "grad": "from-amber-500 via-orange-500 to-rose-500",
        "glass": GLASS_LIGHT,
        "accent": "orange",
        "industries": ["food", "ecommerce", "hospitality", "lifestyle"]
    }
}

# ============================================================================
# SECTION VARIANT LIBRARY: Multi-Style Components
# ============================================================================

class HeroVariant:
    """3 distinct hero styles for maximum visual variety"""
    
    @staticmethod
    def split_grid(theme: Dict, data: Dict) -> str:
        """Classic: Text left, image right in bold grid"""
        try:
            return f"""
            <section id="hero" class="relative {theme['bg']} {PADDING_SECTION} overflow-hidden pt-32">
                <div class="container mx-auto {PADDING_CONTAINER}">
                    <div class="grid lg:grid-cols-2 gap-16 lg:gap-20 items-center">
                        <div class="space-y-8">
                            <div class="space-y-6">
                                <span class="inline-block px-4 py-2 rounded-full {theme['glass']} text-sm font-semibold {theme['text']}">
                                    ✨ Premium Experience
                                </span>
                                <h1 class="{HEADING_HERO} {theme['text']}">{data.get('hero', {}).get('h1', 'Premium Solution')}</h1>
                            </div>
                            <p class="text-xl md:text-2xl {theme['text_muted']} leading-relaxed max-w-xl">{data.get('hero', {}).get('sub', 'Built for excellence')}</p>
                            <div class="flex flex-col sm:flex-row gap-4 pt-4">
                                <a href="#contact" class="px-8 py-5 bg-gradient-to-r {theme['grad']} text-white rounded-full font-bold text-lg {HOVER_LIFT} inline-block text-center">
                                    {data.get('hero', {}).get('cta', 'Get Started')}
                                </a>
                                <a href="#features" class="px-8 py-5 {theme['glass']} {theme['text']} rounded-full font-bold {HOVER_GLOW} inline-block text-center">
                                    Learn More →
                                </a>
                            </div>
                        </div>
                        <div class="relative h-[500px] md:h-[600px] rounded-3xl overflow-hidden bg-gradient-to-br {theme['grad']} opacity-10">
                            <img src="https://images.unsplash.com/photo-1552664730-d307ca884978?w=800&auto=format&fit=crop&q=80" 
                                 alt="hero" class="w-full h-full object-cover {HOVER_LIFT}" />
                            <div class="absolute inset-0 bg-gradient-to-t from-black/20 to-transparent"></div>
                        </div>
                    </div>
                </div>
            </section>"""
        except Exception as e:
            logger.error(f"Error rendering split_grid hero: {e}")
            return f"<section class='{theme['bg']} py-20'><div class='container mx-auto text-center'><h1>Hero Section</h1></div></section>"

    @staticmethod
    def centered_spotlight(theme: Dict, data: Dict) -> str:
        """Bold: Full-width centered with background video vibes"""
        try:
            return f"""
            <section id="hero" class="relative {theme['bg']} {PADDING_SECTION} overflow-hidden">
                <div class="absolute inset-0 opacity-30">
                    <div class="absolute top-0 -left-1/4 w-96 h-96 bg-gradient-to-r {theme['grad']} rounded-full blur-3xl"></div>
                    <div class="absolute bottom-0 -right-1/4 w-96 h-96 bg-gradient-to-l {theme['grad']} rounded-full blur-3xl"></div>
                </div>
                <div class="container mx-auto {PADDING_CONTAINER} relative z-10">
                    <div class="max-w-4xl mx-auto text-center space-y-8">
                        <h1 class="{HEADING_HERO} {theme['text']} leading-none">{data.get('hero', {}).get('h1', 'Premium Solution')}</h1>
                        <p class="text-2xl md:text-3xl {theme['text_muted']} font-light leading-relaxed">{data.get('hero', {}).get('sub', 'Built for excellence')}</p>
                        <div class="flex flex-col sm:flex-row gap-4 justify-center pt-8">
                            <a href="#contact" class="px-10 py-6 bg-gradient-to-r {theme['grad']} text-white rounded-full font-bold text-lg {HOVER_LIFT} inline-block">
                                {data.get('hero', {}).get('cta', 'Get Started')}
                            </a>
                            <a href="#features" class="px-10 py-6 {theme['glass']} {theme['text']} rounded-full font-bold {HOVER_GLOW} inline-block">
                                Explore
                            </a>
                        </div>
                    </div>
                </div>
            </section>"""
        except Exception as e:
            logger.error(f"Error rendering centered_spotlight hero: {e}")
            return f"<section class='{theme['bg']} py-20'><div class='container mx-auto text-center'><h1>Hero Section</h1></div></section>"

    @staticmethod
    def asymmetric_wave(theme: Dict, data: Dict) -> str:
        """Modern: Asymmetric layout with gradient overlay"""
        try:
            return f"""
            <section id="hero" class="relative {theme['bg']} {PADDING_SECTION} overflow-hidden pt-40">
                <div class="container mx-auto {PADDING_CONTAINER}">
                    <div class="grid lg:grid-cols-2 gap-12 items-center">
                        <div class="space-y-8 order-2 lg:order-1">
                            <h1 class="{HEADING_HERO} {theme['text']}">{data.get('hero', {}).get('h1', 'Premium Solution')}</h1>
                            <div class="w-20 h-1.5 bg-gradient-to-r {theme['grad']} rounded-full"></div>
                            <p class="text-lg {theme['text_muted']} leading-relaxed">{data.get('hero', {}).get('sub', 'Built for excellence')}</p>
                            <a href="#contact" class="inline-block px-8 py-5 bg-gradient-to-r {theme['grad']} text-white rounded-full font-bold {HOVER_LIFT}">
                                {data.get('hero', {}).get('cta', 'Get Started')}
                            </a>
                        </div>
                        <div class="relative order-1 lg:order-2 h-96">
                            <div class="absolute inset-0 bg-gradient-to-br {theme['grad']} opacity-10 rounded-3xl blur-2xl"></div>
                            <img src="https://images.unsplash.com/photo-1552664730-d307ca884978?w=600&auto=format&fit=crop&q=80" 
                                 alt="hero" class="relative z-10 w-full h-full object-cover rounded-3xl {HOVER_LIFT}" />
                        </div>
                    </div>
                </div>
            </section>"""
        except Exception as e:
            logger.error(f"Error rendering asymmetric_wave hero: {e}")
            return f"<section class='{theme['bg']} py-20'><div class='container mx-auto text-center'><h1>Hero Section</h1></div></section>"


class FeatureVariant:
    """3 distinct feature section designs"""
    
    @staticmethod
    def cards_grid(theme: Dict, features: List[Dict]) -> str:
        """Classic: 3-column card grid with icons"""
        try:
            items = "".join([f"""
            <div class="{theme['glass']} p-10 {HOVER_LIFT}">
                <div class="w-14 h-14 mb-6 rounded-xl bg-gradient-to-br {theme['grad']} flex items-center justify-center text-2xl">
                    {feat.get('icon', '✨')}
                </div>
                <h3 class="{HEADING_CARD} {theme['text']} mb-3">{feat.get('title', 'Feature')}</h3>
                <p class="{theme['text_muted']} leading-relaxed">{feat.get('description', 'Premium feature')}</p>
            </div>""" for feat in (features or [])])
            
            return f"""
            <section id="features" class="{theme['bg_alt']} {PADDING_SECTION}">
                <div class="container mx-auto {PADDING_CONTAINER}">
                    <div class="text-center mb-16 space-y-4">
                        <h2 class="{HEADING_SECTION} {theme['text']}">Powerful Features</h2>
                        <p class="text-xl {theme['text_muted']} max-w-2xl mx-auto">Everything you need to succeed</p>
                    </div>
                    <div class="grid md:grid-cols-3 gap-8">
                        {items}
                    </div>
                </div>
            </section>"""
        except Exception as e:
            logger.error(f"Error rendering cards_grid features: {e}")
            return f"<section id='features' class='{theme['bg_alt']} py-20'><div class='container mx-auto text-center'><h2>Features</h2></div></section>"

    @staticmethod
    def alternating_blocks(theme: Dict, features: List[Dict]) -> str:
        """Rich: Alternating text-image blocks"""
        try:
            blocks = "".join([f"""
            <div class="grid lg:grid-cols-2 gap-12 lg:gap-16 items-center {'lg:flex-row-reverse' if i % 2 else ''}">
                <div class="space-y-6 {'order-2' if i % 2 else ''}">
                    <div class="w-12 h-12 bg-gradient-to-br {theme['grad']} rounded-lg flex items-center justify-center text-xl">
                        {feat.get('icon', '✨')}
                    </div>
                    <h3 class="{HEADING_FEATURE} {theme['text']}">{feat.get('title', 'Feature')}</h3>
                    <p class="text-lg {theme['text_muted']} leading-relaxed">{feat.get('description', 'Premium feature')}</p>
                </div>
                <div class="h-80 rounded-2xl overflow-hidden bg-gray-300 {'order-1' if i % 2 else ''}">
                    <img src="https://images.unsplash.com/photo-1552664730-d307ca884978?w=600&auto=format&fit=crop&q=80" 
                         alt="{feat.get('title', 'Feature')}" class="w-full h-full object-cover" />
                </div>
            </div>""" for i, feat in enumerate(features or [])])
            
            return f"""
            <section id="features" class="{theme['bg']} {PADDING_SECTION}">
                <div class="container mx-auto {PADDING_CONTAINER}">
                    <h2 class="{HEADING_SECTION} {theme['text']} mb-20 text-center">Why Choose Us</h2>
                    <div class="space-y-32">
                        {blocks}
                    </div>
                </div>
            </section>"""
        except Exception as e:
            logger.error(f"Error rendering alternating_blocks features: {e}")
            return f"<section id='features' class='{theme['bg']} py-20'><div class='container mx-auto text-center'><h2>Features</h2></div></section>"

    @staticmethod
    def showcase_grid(theme: Dict, features: List[Dict]) -> str:
        """Modern: 2x2 or 3x2 grid"""
        try:
            items = "".join([f"""
            <div class="{theme['glass']} p-12 rounded-3xl {HOVER_LIFT} flex flex-col">
                <div class="w-16 h-16 mb-8 rounded-2xl bg-gradient-to-br {theme['grad']} flex items-center justify-center text-3xl">
                    {feat.get('icon', '✨')}
                </div>
                <h3 class="text-2xl font-bold {theme['text']} mb-4">{feat.get('title', 'Feature')}</h3>
                <p class="{theme['text_muted']} text-base leading-relaxed flex-grow">{feat.get('description', 'Premium feature')}</p>
                <div class="mt-6 pt-6 border-t border-white/10">
                    <a href="#contact" class="text-sm font-semibold {theme['text']} hover:opacity-70 transition">
                        Learn more →
                    </a>
                </div>
            </div>""" for feat in (features or [])])
            
            return f"""
            <section id="features" class="{theme['bg_alt']} {PADDING_SECTION}">
                <div class="container mx-auto {PADDING_CONTAINER}">
                    <h2 class="{HEADING_SECTION} {theme['text']} text-center mb-20">Featured Solutions</h2>
                    <div class="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
                        {items}
                    </div>
                </div>
            </section>"""
        except Exception as e:
            logger.error(f"Error rendering showcase_grid features: {e}")
            return f"<section id='features' class='{theme['bg_alt']} py-20'><div class='container mx-auto text-center'><h2>Features</h2></div></section>"


class PricingVariant:
    """2 distinct pricing layouts"""
    
    @staticmethod
    def tiered_cards(theme: Dict, tiers: List[Dict]) -> str:
        """Classic: 3 pricing cards"""
        try:
            cards = "".join([f"""
            <div class="{theme['glass']} p-10 rounded-3xl {HOVER_LIFT} flex flex-col">
                <h3 class="{HEADING_CARD} {theme['text']} mb-2">{tier.get('name', 'Plan')}</h3>
                <p class="{theme['text_light']} text-sm mb-8">{tier.get('description', '')}</p>
                <div class="mb-8">
                    <span class="text-5xl font-black {theme['text']}">{tier.get('price', '$0')}</span>
                    <span class="{theme['text_muted']}">/month</span>
                </div>
                <ul class="space-y-4 mb-10 flex-grow">
                    {chr(10).join([f'<li class="{theme['text_muted']} text-sm flex items-start"><span class="mr-3 mt-1">✓</span> {feat}</li>' for feat in (tier.get('features', []) or [])])}
                </ul>
                <button class="w-full py-4 px-6 rounded-xl font-bold transition-all {'bg-gradient-to-r ' + theme['grad'] + ' text-white' if tier.get('featured') else theme['glass'] + ' ' + theme['text']}">
                    Get Started
                </button>
            </div>""" for tier in (tiers or [])])
            
            return f"""
            <section id="pricing" class="{theme['bg_alt']} {PADDING_SECTION}">
                <div class="container mx-auto {PADDING_CONTAINER}">
                    <div class="text-center mb-16 space-y-4">
                        <h2 class="{HEADING_SECTION} {theme['text']}">Simple, Transparent Pricing</h2>
                        <p class="text-xl {theme['text_muted']}">Choose the perfect plan</p>
                    </div>
                    <div class="grid md:grid-cols-3 gap-8 max-w-6xl mx-auto">
                        {cards}
                    </div>
                </div>
            </section>"""
        except Exception as e:
            logger.error(f"Error rendering tiered_cards pricing: {e}")
            return f"<section id='pricing' class='{theme['bg_alt']} py-20'><div class='container mx-auto text-center'><h2>Pricing</h2></div></section>"

    @staticmethod
    def comparison_table(theme: Dict, tiers: List[Dict]) -> str:
        """Enterprise: Full comparison"""
        try:
            tier_headers = "".join([f'<th class="{theme['text']} font-bold text-right">{t.get("name", "Plan")}</th>' for t in (tiers or [])])
            all_features = set()
            for t in (tiers or []):
                all_features.update(t.get('features', []) or [])
            
            feature_rows = "".join([f"""
            <tr class="border-b border-white/10">
                <td class="{theme['text']} py-4">{feat}</td>
                {chr(10).join([f'<td class="text-right text-green-500 py-4">✓</td>' if feat in (tiers[i].get('features', []) or []) else f'<td class="text-right text-gray-400 py-4">−</td>' for i in range(len(tiers or []))])}
            </tr>""" for feat in all_features])
            
            return f"""
            <section id="pricing" class="{theme['bg']} {PADDING_SECTION}">
                <div class="container mx-auto {PADDING_CONTAINER}">
                    <h2 class="{HEADING_SECTION} {theme['text']} text-center mb-16">Detailed Comparison</h2>
                    <div class="overflow-x-auto {theme['glass']} p-8 rounded-3xl">
                        <table class="w-full">
                            <thead>
                                <tr class="border-b-2 border-white/20">
                                    <th class="{theme['text']} font-bold text-left pb-4">Features</th>
                                    {tier_headers}
                                </tr>
                            </thead>
                            <tbody>
                                {feature_rows}
                            </tbody>
                        </table>
                    </div>
                </div>
            </section>"""
        except Exception as e:
            logger.error(f"Error rendering comparison_table pricing: {e}")
            return f"<section id='pricing' class='{theme['bg']} py-20'><div class='container mx-auto text-center'><h2>Pricing</h2></div></section>"


# ============================================================================
# MASTER ARCHITECT: Main Generator
# ============================================================================

class MasterArchitect:
    """
    Enterprise-grade website generator with industry-aware styling,
    section variants, professional defaults, and elite design principles.
    """
    
    def __init__(self, business_name: str, prompt: str, version: int = 1):
        try:
            self.name = business_name or "Business"
            self.prompt = prompt or ""
            self.version = version
            self.industry = self._detect_industry()
            self.theme = self._select_theme()
            self.data = {}
            logger.info(f"MasterArchitect initialized: {self.name}, industry: {self.industry}, theme: {self.theme['id']}")
        except Exception as e:
            logger.error(f"Error initializing MasterArchitect: {e}")
            self.name = business_name or "Business"
            self.prompt = prompt or ""
            self.version = version
            self.industry = "tech"
            self.theme = THEMES.get("pro_light", {})
            self.data = {}

    def _detect_industry(self) -> str:
        """Detect industry from prompt for smart variant selection"""
        try:
            prompt_lower = self.prompt.lower() if self.prompt else ""
            
            industry_keywords = {
                "saas": ["software", "app", "platform", "cloud", "api", "saas"],
                "ai": ["ai", "machine learning", "ml", "neural", "algorithm"],
                "ecommerce": ["shop", "store", "ecommerce", "sell", "product"],
                "health": ["health", "medical", "wellness", "fitness", "clinic", "doctor"],
                "finance": ["finance", "banking", "investment", "crypto", "payment"],
                "agency": ["agency", "design", "creative", "marketing", "brand"],
                "education": ["education", "course", "learn", "training", "school"],
                "luxury": ["luxury", "premium", "high-end", "exclusive"],
            }
            
            for industry, keywords in industry_keywords.items():
                if any(kw in prompt_lower for kw in keywords):
                    return industry
            
            return "tech"
        except Exception as e:
            logger.warning(f"Error detecting industry: {e}")
            return "tech"

    def _select_theme(self) -> Dict:
        """Select theme based on industry"""
        try:
            industry = self.industry
            
            theme_map = {
                "saas": "pro_light",
                "ai": "tech_midnight",
                "ecommerce": "warm_cream",
                "health": "clean_slate",
                "finance": "luxury_dark",
                "agency": "luxury_dark",
                "education": "clean_slate",
                "luxury": "luxury_dark",
            }
            
            theme_id = theme_map.get(industry, "pro_light")
            return THEMES.get(theme_id, THEMES.get("pro_light", {}))
        except Exception as e:
            logger.warning(f"Error selecting theme: {e}")
            return THEMES.get("pro_light", {})

    def get_ai_payload(self) -> Dict:
        """Orchestrate single AI call to generate all website content"""
        try:
            system_msg = "You are an elite Web Architect designing premium, conversion-optimized websites. Output ONLY valid JSON."
            
            user_msg = f"""
            Create premium website content for '{self.name}'.
            Business Context: {self.prompt}
            Industry: {self.industry}
            
            Generate JSON with:
            - nav: navigation menu items (array of strings)
            - hero: {{h1, sub (subtitle), cta}} 
            - features: array of 3-4 {{title, description, icon (emoji)}}
            - pricing: array of 3 {{name, price (e.g., "$99"), features: array of 5 strings, featured: boolean for middle one}}
            - testimonials: array of 2 {{name, company, quote}}
            - faq: array of 3 {{q, a}}
            - cta_text: main call-to-action text for footer
            - unsplash_keywords: array of 5 professional image search terms
            
            Make content specific, powerful, and conversion-focused. Use vivid language.
            """
            
            if not AI_AVAILABLE:
                logger.warning("AI client not available, using fallback payload")
                return self._get_fallback_payload()
            
            res = chat_completion(system=system_msg, user=user_msg, temperature=0.7)
            payload = json.loads(res.strip().replace("```json", "").replace("```", ""))
            logger.info(f"AI payload generated successfully for {self.name}")
            return payload
        except Exception as e:
            logger.error(f"Error getting AI payload: {e}\n{traceback.format_exc()}")
            return self._get_fallback_payload()

    def _get_fallback_payload(self) -> Dict:
        """Fallback structure if AI fails"""
        logger.info("Using fallback payload")
        return {
            "nav": ["Features", "Pricing", "FAQ", "Contact"],
            "hero": {"h1": f"Premium {self.name}", "sub": "Built for excellence", "cta": "Start Now"},
            "features": [
                {"title": "Feature One", "description": "Premium quality and reliability", "icon": "✨"},
                {"title": "Feature Two", "description": "World-class service and support", "icon": "🚀"},
                {"title": "Feature Three", "description": "Maximum impact and results", "icon": "💎"},
            ],
            "pricing": [
                {"name": "Starter", "price": "$29", "features": ["Feature A", "Feature B", "Feature C", "Feature D", "Feature E"], "featured": False},
                {"name": "Pro", "price": "$99", "features": ["Feature A", "Feature B", "Feature C", "Feature D", "Feature E"], "featured": True},
                {"name": "Enterprise", "price": "Custom", "features": ["All features", "Dedicated support", "Custom integrations", "Priority access", "24/7 support"], "featured": False},
            ],
            "testimonials": [
                {"name": "John Doe", "company": "Tech Corp", "quote": "Exceptional service!"},
                {"name": "Jane Smith", "company": "Innovation Inc", "quote": "Transformed our business!"}
            ],
            "faq": [
                {"q": "How does it work?", "a": "It's simple and powerful. Just sign up and start immediately."},
                {"q": "What support do you offer?", "a": "We offer 24/7 email and phone support for all plans."},
                {"q": "Can I cancel anytime?", "a": "Yes, no long-term contracts. Cancel anytime without penalties."}
            ],
            "cta_text": "Ready to transform your business?",
            "unsplash_keywords": ["technology", "business", "modern", "startup", "premium"]
        }

    def render_nav(self) -> str:
        """Fixed navigation with smooth scroll and professional styling"""
        try:
            nav_items = "".join([
                f'<li><a href="#{link.lower().replace(" ", "")}" class="hover:{self.theme.get('primary', 'blue')}-400 transition-colors duration-300 font-medium">{link}</a></li>'
                for link in (self.data.get('nav', []) or [])
            ])
            
            return f"""
            <nav class="fixed top-0 w-full z-50 {self.theme.get('glass', GLASS_LIGHT)} border-b border-white/10 py-5">
                <div class="container mx-auto {PADDING_CONTAINER} flex justify-between items-center">
                    <a href="#" class="text-2xl font-black tracking-tighter {self.theme.get('text', 'text-gray-900')}">{self.name}</a>
                    <ul class="hidden md:flex gap-10 text-sm">{nav_items}</ul>
                    <a href="#contact" class="px-6 py-3 bg-gradient-to-r {self.theme.get('grad', 'from-blue-600 to-blue-500')} text-white rounded-full font-bold text-sm {HOVER_LIFT}">
                        Get Started
                    </a>
                </div>
            </nav>"""
        except Exception as e:
            logger.error(f"Error rendering nav: {e}")
            return f"<nav class='fixed top-0 w-full z-50 bg-white border-b py-5'><div class='container mx-auto px-6'><a href='#' class='text-2xl font-bold'>{self.name}</a></div></nav>"

    def render_hero(self) -> str:
        """Select and render hero variant based on industry"""
        try:
            variants = [HeroVariant.split_grid, HeroVariant.centered_spotlight, HeroVariant.asymmetric_wave]
            
            if self.industry in ["luxury", "agency"]:
                variant_fn = HeroVariant.centered_spotlight
            elif self.industry in ["saas", "finance"]:
                variant_fn = HeroVariant.split_grid
            else:
                variant_fn = HeroVariant.asymmetric_wave
            
            return variant_fn(self.theme, self.data)
        except Exception as e:
            logger.error(f"Error rendering hero: {e}")
            return f"<section id='hero' class='{self.theme.get('bg', 'bg-white')} py-32'><div class='container mx-auto px-6 text-center'><h1 class='text-6xl font-bold'>Welcome</h1></div></section>"

    def render_features(self) -> str:
        """Select and render features variant based on industry"""
        try:
            if self.industry in ["ecommerce", "saas"]:
                variant_fn = FeatureVariant.cards_grid
            elif self.industry in ["agency", "luxury"]:
                variant_fn = FeatureVariant.showcase_grid
            else:
                variant_fn = FeatureVariant.alternating_blocks
            
            return variant_fn(self.theme, self.data.get('features', []))
        except Exception as e:
            logger.error(f"Error rendering features: {e}")
            return f"<section id='features' class='{self.theme.get('bg_alt', 'bg-gray-50')} py-20'><div class='container mx-auto px-6 text-center'><h2 class='text-4xl font-bold'>Features</h2></div></section>"

    def render_pricing(self) -> str:
        """Select and render pricing variant based on industry"""
        try:
            if self.industry in ["finance", "saas", "luxury"]:
                variant_fn = PricingVariant.comparison_table
            else:
                variant_fn = PricingVariant.tiered_cards
            
            return variant_fn(self.theme, self.data.get('pricing', []))
        except Exception as e:
            logger.error(f"Error rendering pricing: {e}")
            return f"<section id='pricing' class='{self.theme.get('bg_alt', 'bg-gray-50')} py-20'><div class='container mx-auto px-6 text-center'><h2 class='text-4xl font-bold'>Pricing</h2></div></section>"

    def render_testimonials(self) -> str:
        """Client testimonials with glassmorphism"""
        try:
            testimonials = self.data.get('testimonials', [])
            if not testimonials:
                return ""
            
            testimonial_cards = "".join([f"""
            <div class="{self.theme.get('glass', GLASS_LIGHT)} p-10 rounded-2xl {HOVER_LIFT}">
                <p class="{self.theme.get('text_muted', 'text-gray-600')} text-lg italic mb-6">"{t.get('quote', '')}"</p>
                <div>
                    <p class="{self.theme.get('text', 'text-gray-900')} font-bold">{t.get('name', 'Client')}</p>
                    <p class="{self.theme.get('text_light', 'text-gray-400')} text-sm">{t.get('company', 'Company')}</p>
                </div>
            </div>""" for t in testimonials])
            
            return f"""
            <section id="testimonials" class="{self.theme.get('bg_alt', 'bg-gray-50')} {PADDING_SECTION}">
                <div class="container mx-auto {PADDING_CONTAINER}">
                    <h2 class="{HEADING_SECTION} {self.theme.get('text', 'text-gray-900')} text-center mb-16">Trusted by Leaders</h2>
                    <div class="grid md:grid-cols-2 gap-8 max-w-4xl mx-auto">
                        {testimonial_cards}
                    </div>
                </div>
            </section>"""
        except Exception as e:
            logger.error(f"Error rendering testimonials: {e}")
            return ""

    def render_faq(self) -> str:
        """FAQ section with collapsible style"""
        try:
            faqs = self.data.get('faq', [])
            if not faqs:
                return ""
            
            faq_items = "".join([f"""
            <div class="{self.theme.get('glass', GLASS_LIGHT)} p-8 rounded-2xl group cursor-pointer {HOVER_GLOW}">
                <h3 class="{HEADING_FEATURE} {self.theme.get('text', 'text-gray-900')} mb-4 group-hover:opacity-80 transition">{faq.get('q', '')}</h3>
                <p class="{self.theme.get('text_muted', 'text-gray-600')} leading-relaxed">{faq.get('a', '')}</p>
            </div>""" for faq in faqs])
            
            return f"""
            <section id="faq" class="{self.theme.get('bg', 'bg-white')} {PADDING_SECTION}">
                <div class="container mx-auto {PADDING_CONTAINER}">
                    <h2 class="{HEADING_SECTION} {self.theme.get('text', 'text-gray-900')} text-center mb-16">Frequently Asked Questions</h2>
                    <div class="space-y-4 max-w-3xl mx-auto">
                        {faq_items}
                    </div>
                </div>
            </section>"""
        except Exception as e:
            logger.error(f"Error rendering FAQ: {e}")
            return ""

    def render_trust_cloud(self) -> str:
        """Logo cloud for social proof"""
        try:
            return f"""
            <section class="{self.theme.get('bg_alt', 'bg-gray-50')} py-16 border-t border-white/10">
                <div class="container mx-auto {PADDING_CONTAINER}">
                    <p class="{self.theme.get('text_light', 'text-gray-400')} text-sm text-center mb-8 uppercase tracking-widest">Trusted by innovative companies</p>
                    <div class="flex flex-wrap justify-center gap-8 opacity-60">
                        {chr(10).join([f'<span class="{self.theme.get('text_muted', 'text-gray-600')} font-bold text-lg">★ Brand {i+1}</span>' for i in range(5)])}
                    </div>
                </div>
            </section>"""
        except Exception as e:
            logger.error(f"Error rendering trust cloud: {e}")
            return ""

    def render_cta_section(self) -> str:
        """Final CTA section before footer"""
        try:
            cta_text = self.data.get('cta_text', 'Ready to get started?')
            return f"""
            <section id="contact" class="relative {self.theme.get('bg', 'bg-white')} {PADDING_SECTION} overflow-hidden">
                <div class="absolute inset-0 opacity-20">
                    <div class="absolute -top-1/2 -left-1/2 w-96 h-96 bg-gradient-to-r {self.theme.get('grad', 'from-blue-600 to-blue-500')} rounded-full blur-3xl"></div>
                </div>
                <div class="container mx-auto {PADDING_CONTAINER} relative z-10 text-center">
                    <h2 class="{HEADING_SECTION} {self.theme.get('text', 'text-gray-900')} mb-8">{cta_text}</h2>
                    <div class="flex flex-col sm:flex-row gap-4 justify-center">
                        <a href="mailto:info@example.com" class="px-10 py-6 bg-gradient-to-r {self.theme.get('grad', 'from-blue-600 to-blue-500')} text-white rounded-full font-bold {HOVER_LIFT}">
                            Schedule a Demo
                        </a>
                        <a href="tel:+1234567890" class="px-10 py-6 {self.theme.get('glass', GLASS_LIGHT)} {self.theme.get('text', 'text-gray-900')} rounded-full font-bold {HOVER_GLOW}">
                            +1 (234) 567-890
                        </a>
                    </div>
                </div>
            </section>"""
        except Exception as e:
            logger.error(f"Error rendering CTA section: {e}")
            return f"<section id='contact' class='{self.theme.get('bg', 'bg-white')} py-20'><div class='container mx-auto px-6 text-center'><h2 class='text-4xl font-bold'>Get Started</h2></div></section>"

    def render_footer(self) -> str:
        """Global professional footer"""
        try:
            nav_links = "".join([f'<li><a href="#{link.lower().replace(" ", "")}" class="{self.theme.get('text_muted', 'text-gray-600')} hover:{self.theme.get("primary", "blue")}-600 text-sm transition">{link}</a></li>' for link in (self.data.get('nav', []) or [])])
            
            return f"""
            <footer class="{self.theme.get('bg_alt', 'bg-gray-50')} border-t border-white/10 py-12">
                <div class="container mx-auto {PADDING_CONTAINER}">
                    <div class="grid md:grid-cols-4 gap-12 mb-12">
                        <div>
                            <h3 class="font-black text-lg {self.theme.get('text', 'text-gray-900')} mb-4">{self.name}</h3>
                            <p class="{self.theme.get('text_muted', 'text-gray-600')} text-sm">Premium solutions for modern businesses.</p>
                        </div>
                        <div>
                            <h4 class="font-bold {self.theme.get('text', 'text-gray-900')} mb-4">Product</h4>
                            <ul class="space-y-2">
                                {nav_links}
                            </ul>
                        </div>
                        <div>
                            <h4 class="font-bold {self.theme.get('text', 'text-gray-900')} mb-4">Company</h4>
                            <ul class="space-y-2 text-sm">
                                <li><a href="#" class="{self.theme.get('text_muted', 'text-gray-600')} hover:{self.theme.get("primary", "blue")}-600 transition">About</a></li>
                                <li><a href="#" class="{self.theme.get('text_muted', 'text-gray-600')} hover:{self.theme.get("primary", "blue")}-600 transition">Blog</a></li>
                                <li><a href="#" class="{self.theme.get('text_muted', 'text-gray-600')} hover:{self.theme.get("primary", "blue")}-600 transition">Careers</a></li>
                            </ul>
                        </div>
                        <div>
                            <h4 class="font-bold {self.theme.get('text', 'text-gray-900')} mb-4">Legal</h4>
                            <ul class="space-y-2 text-sm">
                                <li><a href="#" class="{self.theme.get('text_muted', 'text-gray-600')} hover:{self.theme.get("primary", "blue")}-600 transition">Privacy</a></li>
                                <li><a href="#" class="{self.theme.get('text_muted', 'text-gray-600')} hover:{self.theme.get("primary", "blue")}-600 transition">Terms</a></li>
                                <li><a href="mailto:legal@example.com" class="{self.theme.get('text_muted', 'text-gray-600')} hover:{self.theme.get("primary", "blue")}-600 transition">Contact</a></li>
                            </ul>
                        </div>
                    </div>
                    <div class="border-t border-white/10 pt-8 flex justify-between items-center">
                        <p class="{self.theme.get('text_light', 'text-gray-400')} text-sm">&copy; 2026 {self.name}. All rights reserved.</p>
                        <p class="{self.theme.get('text_light', 'text-gray-400')} text-sm">v{self.version}</p>
                    </div>
                </div>
            </footer>"""
        except Exception as e:
            logger.error(f"Error rendering footer: {e}")
            return f"<footer class='{self.theme.get('bg_alt', 'bg-gray-50')} py-8'><div class='container mx-auto px-6 text-center text-sm text-gray-600'>&copy; 2026. All rights reserved.</div></footer>"

    def build(self) -> Dict[str, Any]:
        """Assemble complete website with all sections"""
        try:
            self.data = self.get_ai_payload()
            
            sections = [
                self.render_nav(),
                self.render_hero(),
                self.render_features(),
                self.render_pricing(),
                self.render_testimonials(),
                self.render_faq(),
                self.render_trust_cloud(),
                self.render_cta_section(),
                self.render_footer(),
            ]
            
            html = f"""
            <!DOCTYPE html>
            <html lang="en" style="scroll-behavior: smooth;">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>{self.name} - Premium Solutions</title>
                <script src="https://cdn.tailwindcss.com"></script>
                <style>
                    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;900&display=swap');
                    * {{ font-family: 'Inter', sans-serif; }}
                    
                    @keyframes fadeInUp {{
                        from {{ opacity: 0; transform: translateY(20px); }}
                        to {{ opacity: 1; transform: translateY(0); }}
                    }}
                    
                    section {{ animation: fadeInUp 0.8s ease-out forwards; }}
                    section:nth-child(n+2) {{ animation-delay: 0.2s; }}
                </style>
            </head>
            <body class="{self.theme.get('bg', 'bg-white')} {self.theme.get('text', 'text-gray-900')}">
                {"".join(sections)}
            </body>
            </html>
            """
            
            logger.info(f"Website built successfully for {self.name}")
            return {
                "html": html,
                "metadata": {
                    "business_name": self.name,
                    "industry": self.industry,
                    "theme": self.theme.get('id', 'unknown'),
                    "version": self.version,
                    "status": "success"
                }
            }
        except Exception as e:
            logger.error(f"Error building website: {e}\n{traceback.format_exc()}")
            return {
                "html": f"<html><body><h1>Error</h1><p>{str(e)}</p></body></html>",
                "metadata": {
                    "business_name": self.name,
                    "industry": self.industry,
                    "theme": self.theme.get('id', 'unknown'),
                    "version": self.version,
                    "status": "error",
                    "error": str(e)
                }
            }


# ============================================================================
# PUBLIC API
# ============================================================================

def generate_ai_plan(ai_input: Dict[str, Any], version: int = 1, **kwargs) -> Dict[str, Any]:
    """
    Main entry point for website generation.
    
    Args:
        ai_input: {"business_name": str, "prompt": str}
        version: API version for future compatibility
        **kwargs: Additional configuration (reserved)
    
    Returns:
        Complete website data with HTML and metadata
    """
    try:
        business_name = ai_input.get("business_name", "Business")
        prompt = ai_input.get("prompt", "")
        
        logger.info(f"generate_ai_plan called: business_name={business_name}")
        
        architect = MasterArchitect(business_name, prompt, version=version)
        result = architect.build()
        
        logger.info(f"Website generation completed for {business_name}")
        return result
    except Exception as e:
        logger.error(f"Error in generate_ai_plan: {e}\n{traceback.format_exc()}")
        return {
            "html": f"<html><body><h1>Error</h1><p>{str(e)}</p></body></html>",
            "metadata": {
                "business_name": ai_input.get("business_name", "Unknown"),
                "status": "error",
                "error": str(e)
            }
        }


def rewrite_content(original_text: str, tone: str = "professional", business_context: str = "") -> List[str]:
    """
    AI-powered content rewriting with fallback.
    """
    try:
        if not AI_AVAILABLE:
            return [original_text] * 3
        
        system = "You are a world-class copywriter. Output ONLY valid JSON."
        user = f"Rewrite '{original_text}' exactly 3 times in {tone} tone. Context: {business_context}. Output JSON array: ['version1', 'version2', 'version3']"
        
        res = chat_completion(system=system, user=user, temperature=0.8)
        result = json.loads(res.strip().replace("```json", "").replace("```", ""))
        return result if isinstance(result, list) and len(result) >= 3 else [original_text] * 3
    except Exception as e:
        logger.warning(f"Error rewriting content: {e}")
        return [original_text] * 3


def get_design_tokens() -> Dict[str, Any]:
    """Export design tokens for external use"""
    return {
        "themes": THEMES,
        "spacing": {"section": PADDING_SECTION, "container": PADDING_CONTAINER},
        "typography": {
            "hero": HEADING_HERO,
            "section": HEADING_SECTION,
            "feature": HEADING_FEATURE,
            "card": HEADING_CARD,
        },
        "animations": {
            "hover_lift": HOVER_LIFT,
            "hover_glow": HOVER_GLOW,
            "hover_scale": HOVER_SCALE,
        },
        "glass": {"dark": GLASS_DARK, "light": GLASS_LIGHT},
    }