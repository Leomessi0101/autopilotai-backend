import random
import json
from typing import Dict, Any, List, Optional
from enum import Enum
from app.ai.openai_client import chat_completion

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
        return f"""
        <section id="hero" class="relative {theme['bg']} {PADDING_SECTION} overflow-hidden pt-32">
            <div class="container mx-auto {PADDING_CONTAINER}">
                <div class="grid lg:grid-cols-2 gap-16 lg:gap-20 items-center">
                    <div class="space-y-8">
                        <div class="space-y-6">
                            <span class="inline-block px-4 py-2 rounded-full {theme['glass']} text-sm font-semibold {theme['text']}">
                                ✨ Premium Experience
                            </span>
                            <h1 class="{HEADING_HERO} {theme['text']}">{data['hero']['h1']}</h1>
                        </div>
                        <p class="text-xl md:text-2xl {theme['text_muted']} leading-relaxed max-w-xl">{data['hero']['sub']}</p>
                        <div class="flex flex-col sm:flex-row gap-4 pt-4">
                            <a href="#contact" class="px-8 py-5 bg-gradient-to-r {theme['grad']} text-white rounded-full font-bold text-lg {HOVER_LIFT} inline-block text-center">
                                {data['hero']['cta']}
                            </a>
                            <a href="#features" class="px-8 py-5 {theme['glass']} {theme['text']} rounded-full font-bold {HOVER_GLOW} inline-block text-center">
                                Learn More →
                            </a>
                        </div>
                    </div>
                    <div class="relative h-[500px] md:h-[600px] rounded-3xl overflow-hidden">
                        <img src="{data.get('hero_image', 'https://images.unsplash.com/photo-1?w=800')}" 
                             alt="{data['hero']['h1']}" class="w-full h-full object-cover {HOVER_LIFT}" />
                        <div class="absolute inset-0 bg-gradient-to-t from-black/20 to-transparent"></div>
                    </div>
                </div>
            </div>
        </section>"""

    @staticmethod
    def centered_spotlight(theme: Dict, data: Dict) -> str:
        """Bold: Full-width centered with background video vibes"""
        return f"""
        <section id="hero" class="relative {theme['bg']} {PADDING_SECTION} overflow-hidden">
            <div class="absolute inset-0 opacity-30">
                <div class="absolute top-0 -left-1/4 w-96 h-96 bg-gradient-to-r {theme['grad']} rounded-full blur-3xl"></div>
                <div class="absolute bottom-0 -right-1/4 w-96 h-96 bg-gradient-to-l {theme['grad']} rounded-full blur-3xl"></div>
            </div>
            <div class="container mx-auto {PADDING_CONTAINER} relative z-10">
                <div class="max-w-4xl mx-auto text-center space-y-8">
                    <h1 class="{HEADING_HERO} {theme['text']} leading-none">{data['hero']['h1']}</h1>
                    <p class="text-2xl md:text-3xl {theme['text_muted']} font-light leading-relaxed">{data['hero']['sub']}</p>
                    <div class="flex flex-col sm:flex-row gap-4 justify-center pt-8">
                        <a href="#contact" class="px-10 py-6 bg-gradient-to-r {theme['grad']} text-white rounded-full font-bold text-lg {HOVER_LIFT} inline-block">
                            {data['hero']['cta']}
                        </a>
                        <a href="#features" class="px-10 py-6 {theme['glass']} {theme['text']} rounded-full font-bold {HOVER_GLOW} inline-block">
                            Explore
                        </a>
                    </div>
                </div>
            </div>
        </section>"""

    @staticmethod
    def asymmetric_wave(theme: Dict, data: Dict) -> str:
        """Modern: Asymmetric layout with gradient overlay"""
        return f"""
        <section id="hero" class="relative {theme['bg']} {PADDING_SECTION} overflow-hidden pt-40">
            <div class="container mx-auto {PADDING_CONTAINER}">
                <div class="grid lg:grid-cols-2 gap-12 items-center">
                    <div class="space-y-8 order-2 lg:order-1">
                        <h1 class="{HEADING_HERO} {theme['text']}">{data['hero']['h1']}</h1>
                        <div class="w-20 h-1.5 bg-gradient-to-r {theme['grad']} rounded-full"></div>
                        <p class="text-lg {theme['text_muted']} leading-relaxed">{data['hero']['sub']}</p>
                        <a href="#contact" class="inline-block px-8 py-5 bg-gradient-to-r {theme['grad']} text-white rounded-full font-bold {HOVER_LIFT}">
                            {data['hero']['cta']}
                        </a>
                    </div>
                    <div class="relative order-1 lg:order-2 h-96">
                        <div class="absolute inset-0 bg-gradient-to-br {theme['grad']} opacity-10 rounded-3xl blur-2xl"></div>
                        <img src="{data.get('hero_image', 'https://images.unsplash.com/photo-1?w=800')}" 
                             alt="hero" class="relative z-10 w-full h-full object-cover rounded-3xl {HOVER_LIFT}" />
                    </div>
                </div>
            </div>
        </section>"""


class FeatureVariant:
    """3 distinct feature section designs"""
    
    @staticmethod
    def cards_grid(theme: Dict, features: List[Dict]) -> str:
        """Classic: 3-column card grid with icons"""
        items = "".join([f"""
        <div class="{theme['glass']} p-10 {HOVER_LIFT}">
            <div class="w-14 h-14 mb-6 rounded-xl bg-gradient-to-br {theme['grad']} flex items-center justify-center text-2xl">
                {feat.get('icon', '✨')}
            </div>
            <h3 class="{HEADING_CARD} {theme['text']} mb-3">{feat['title']}</h3>
            <p class="{theme['text_muted']} leading-relaxed">{feat['description']}</p>
        </div>""" for feat in features])
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

    @staticmethod
    def alternating_blocks(theme: Dict, features: List[Dict]) -> str:
        """Rich: Alternating text-image blocks (single feature per row)"""
        blocks = "".join([f"""
        <div class="grid lg:grid-cols-2 gap-12 lg:gap-16 items-center {'lg:flex-row-reverse' if i % 2 else ''}">
            <div class="space-y-6 {'order-2' if i % 2 else ''}">
                <div class="w-12 h-12 bg-gradient-to-br {theme['grad']} rounded-lg flex items-center justify-center text-xl">
                    {feat.get('icon', '✨')}
                </div>
                <h3 class="{HEADING_FEATURE} {theme['text']}">{feat['title']}</h3>
                <p class="text-lg {theme['text_muted']} leading-relaxed">{feat['description']}</p>
            </div>
            <div class="h-80 rounded-2xl overflow-hidden {'order-1' if i % 2 else ''}">
                <img src="https://images.unsplash.com/photo-{i}?w=600&auto=format" 
                     alt="{feat['title']}" class="w-full h-full object-cover" />
            </div>
        </div>""" for i, feat in enumerate(features)])
        return f"""
        <section id="features" class="{theme['bg']} {PADDING_SECTION}">
            <div class="container mx-auto {PADDING_CONTAINER}">
                <h2 class="{HEADING_SECTION} {theme['text']} mb-20 text-center">Why Choose Us</h2>
                <div class="space-y-32">
                    {blocks}
                </div>
            </div>
        </section>"""

    @staticmethod
    def showcase_grid(theme: Dict, features: List[Dict]) -> str:
        """Modern: 2x2 or 3x2 grid with larger cards and descriptions"""
        items = "".join([f"""
        <div class="{theme['glass']} p-12 rounded-3xl {HOVER_LIFT} flex flex-col">
            <div class="w-16 h-16 mb-8 rounded-2xl bg-gradient-to-br {theme['grad']} flex items-center justify-center text-3xl">
                {feat.get('icon', '✨')}
            </div>
            <h3 class="text-2xl font-bold {theme['text']} mb-4">{feat['title']}</h3>
            <p class="{theme['text_muted']} text-base leading-relaxed flex-grow">{feat['description']}</p>
            <div class="mt-6 pt-6 border-t border-white/10">
                <a href="#contact" class="text-sm font-semibold {theme['text']} hover:opacity-70 transition">
                    Learn more →
                </a>
            </div>
        </div>""" for feat in features])
        return f"""
        <section id="features" class="{theme['bg_alt']} {PADDING_SECTION}">
            <div class="container mx-auto {PADDING_CONTAINER}">
                <h2 class="{HEADING_SECTION} {theme['text']} text-center mb-20">Featured Solutions</h2>
                <div class="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
                    {items}
                </div>
            </div>
        </section>"""


class PricingVariant:
    """2 distinct pricing layouts"""
    
    @staticmethod
    def tiered_cards(theme: Dict, tiers: List[Dict]) -> str:
        """Classic: 3 pricing cards with highlight"""
        cards = "".join([f"""
        <div class="{theme['glass']} p-10 rounded-3xl {HOVER_LIFT} flex flex-col {'border-2 border-gradient-to-r ' + theme['grad'] if tier.get('featured') else ''}">
            <h3 class="{HEADING_CARD} {theme['text']} mb-2">{tier['name']}</h3>
            <p class="{theme['text_light']} text-sm mb-8">{tier.get('description', '')}</p>
            <div class="mb-8">
                <span class="text-5xl font-black {theme['text']}">{tier['price']}</span>
                <span class="{theme['text_muted']}">/month</span>
            </div>
            <ul class="space-y-4 mb-10 flex-grow">
                {chr(10).join([f'<li class="{theme['text_muted']} text-sm flex items-start"><span class="mr-3 mt-1">✓</span> {feat}</li>' for feat in tier['features']])}
            </ul>
            <button class="w-full py-4 px-6 rounded-xl font-bold transition-all {'bg-gradient-to-r ' + theme['grad'] + ' text-white' if tier.get('featured') else theme['glass'] + ' ' + theme['text']}">
                Get Started
            </button>
        </div>""" for tier in tiers])
        return f"""
        <section id="pricing" class="{theme['bg_alt']} {PADDING_SECTION}">
            <div class="container mx-auto {PADDING_CONTAINER}">
                <div class="text-center mb-16 space-y-4">
                    <h2 class="{HEADING_SECTION} {theme['text']}">Simple, Transparent Pricing</h2>
                    <p class="text-xl {theme['text_muted']}">Choose the perfect plan for your needs</p>
                </div>
                <div class="grid md:grid-cols-3 gap-8 max-w-6xl mx-auto">
                    {cards}
                </div>
            </div>
        </section>"""

    @staticmethod
    def comparison_table(theme: Dict, tiers: List[Dict]) -> str:
        """Enterprise: Full comparison with feature matrix"""
        tier_headers = "".join([f'<th class="{theme['text']} font-bold text-right">{t["name"]}</th>' for t in tiers])
        feature_rows = "".join([f"""
        <tr class="border-b border-white/10">
            <td class="{theme['text']} py-4">{feat}</td>
            {chr(10).join([f'<td class="text-right text-green-500 py-4">✓</td>' if feat in tiers[i].get('features', []) else f'<td class="text-right text-gray-400 py-4">−</td>' for i in range(len(tiers))])}
        </tr>""" for feat in set([f for t in tiers for f in t.get('features', [])])])
        
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


# ============================================================================
# MASTER ARCHITECT: Main Generator
# ============================================================================

class MasterArchitect:
    """
    Enterprise-grade website generator with industry-aware styling,
    section variants, professional defaults, and elite design principles.
    """
    
    def __init__(self, business_name: str, prompt: str, version: int = 1):
        self.name = business_name
        self.prompt = prompt
        self.version = version
        self.industry = self._detect_industry()
        self.theme = self._select_theme()
        self.data = {}
        self.hero_variant = None
        self.feature_variant = None
        self.pricing_variant = None

    def _detect_industry(self) -> str:
        """Detect industry from prompt for smart variant selection"""
        prompt_lower = self.prompt.lower()
        
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

    def _select_theme(self) -> Dict:
        """Select theme based on industry"""
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
        return THEMES[theme_id]

    def get_ai_payload(self) -> Dict:
        """Orchestrate single AI call to generate all website content"""
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
        
        JSON:
        """
        
        try:
            res = chat_completion(system=system_msg, user=user_msg, temperature=0.7)
            return json.loads(res.strip().replace("```json", "").replace("```", ""))
        except Exception as e:
            return self._get_fallback_payload()

    def _get_fallback_payload(self) -> Dict:
        """Fallback structure if AI fails"""
        return {
            "nav": ["Features", "Pricing", "FAQ", "Contact"],
            "hero": {"h1": f"Premium {self.name}", "sub": "Built for excellence", "cta": "Start Now"},
            "features": [
                {"title": "Feature One", "description": "Premium quality", "icon": "✨"},
                {"title": "Feature Two", "description": "World-class service", "icon": "🚀"},
                {"title": "Feature Three", "description": "Maximum impact", "icon": "💎"},
            ],
            "pricing": [
                {"name": "Starter", "price": "$29", "features": ["Feature A", "Feature B"], "featured": False},
                {"name": "Pro", "price": "$99", "features": ["Feature A", "Feature B", "Feature C"], "featured": True},
                {"name": "Enterprise", "price": "Custom", "features": ["All features", "Support"], "featured": False},
            ],
            "testimonials": [{"name": "Client", "company": "Company", "quote": "Great service!"}],
            "faq": [{"q": "How does it work?", "a": "It's simple and powerful."}],
            "cta_text": "Ready to transform your business?",
            "unsplash_keywords": ["technology", "business", "modern", "startup", "premium"]
        }

    def render_nav(self) -> str:
        """Fixed navigation with smooth scroll and professional styling"""
        nav_items = "".join([
            f'<li><a href="#{link.lower().replace(" ", "")}" class="hover:{self.theme['primary']}-400 transition-colors duration-300 font-medium">{link}</a></li>'
            for link in self.data['nav']
        ])
        
        return f"""
        <nav class="fixed top-0 w-full z-50 {self.theme['glass']} border-b border-white/10 py-5">
            <div class="container mx-auto {PADDING_CONTAINER} flex justify-between items-center">
                <a href="#" class="text-2xl font-black tracking-tighter {self.theme['text']}">{self.name}</a>
                <ul class="hidden md:flex gap-10 text-sm">{nav_items}</ul>
                <a href="#contact" class="px-6 py-3 bg-gradient-to-r {self.theme['grad']} text-white rounded-full font-bold text-sm {HOVER_LIFT}">
                    Get Started
                </a>
            </div>
        </nav>"""

    def render_hero(self) -> str:
        """Select and render hero variant based on industry"""
        variants = [HeroVariant.split_grid, HeroVariant.centered_spotlight, HeroVariant.asymmetric_wave]
        
        # Smart selection: luxury/creative industries use centered, tech uses split, others use asymmetric
        if self.industry in ["luxury", "agency"]:
            variant_fn = HeroVariant.centered_spotlight
        elif self.industry in ["saas", "finance"]:
            variant_fn = HeroVariant.split_grid
        else:
            variant_fn = HeroVariant.asymmetric_wave
        
        return variant_fn(self.theme, self.data)

    def render_features(self) -> str:
        """Select and render features variant based on industry"""
        variants = [FeatureVariant.cards_grid, FeatureVariant.alternating_blocks, FeatureVariant.showcase_grid]
        
        # Smart selection
        if self.industry in ["ecommerce", "saas"]:
            variant_fn = FeatureVariant.cards_grid
        elif self.industry in ["agency", "luxury"]:
            variant_fn = FeatureVariant.showcase_grid
        else:
            variant_fn = FeatureVariant.alternating_blocks
        
        return variant_fn(self.theme, self.data['features'])

    def render_pricing(self) -> str:
        """Select and render pricing variant based on industry"""
        if self.industry in ["finance", "saas", "luxury"]:
            variant_fn = PricingVariant.comparison_table
        else:
            variant_fn = PricingVariant.tiered_cards
        
        return variant_fn(self.theme, self.data['pricing'])

    def render_testimonials(self) -> str:
        """Client testimonials with glassmorphism"""
        testimonials = "".join([f"""
        <div class="{self.theme['glass']} p-10 rounded-2xl {HOVER_LIFT}">
            <p class="{self.theme['text_muted']} text-lg italic mb-6">"{t['quote']}"</p>
            <div>
                <p class="{self.theme['text']} font-bold">{t['name']}</p>
                <p class="{self.theme['text_light']} text-sm">{t.get('company', 'Client')}</p>
            </div>
        </div>""" for t in self.data.get('testimonials', [])])
        
        if not testimonials:
            return ""
        
        return f"""
        <section id="testimonials" class="{self.theme['bg_alt']} {PADDING_SECTION}">
            <div class="container mx-auto {PADDING_CONTAINER}">
                <h2 class="{HEADING_SECTION} {self.theme['text']} text-center mb-16">Trusted by Leaders</h2>
                <div class="grid md:grid-cols-2 gap-8 max-w-4xl mx-auto">
                    {testimonials}
                </div>
            </div>
        </section>"""

    def render_faq(self) -> str:
        """FAQ section with collapsible style"""
        faqs = "".join([f"""
        <div class="{self.theme['glass']} p-8 rounded-2xl group cursor-pointer {HOVER_GLOW}">
            <h3 class="{HEADING_FEATURE} {self.theme['text']} mb-4 group-hover:opacity-80 transition">{faq['q']}</h3>
            <p class="{self.theme['text_muted']} leading-relaxed">{faq['a']}</p>
        </div>""" for faq in self.data.get('faq', [])])
        
        if not faqs:
            return ""
        
        return f"""
        <section id="faq" class="{self.theme['bg']} {PADDING_SECTION}">
            <div class="container mx-auto {PADDING_CONTAINER}">
                <h2 class="{HEADING_SECTION} {self.theme['text']} text-center mb-16">Frequently Asked Questions</h2>
                <div class="space-y-4 max-w-3xl mx-auto">
                    {faqs}
                </div>
            </div>
        </section>"""

    def render_trust_cloud(self) -> str:
        """Logo cloud for social proof"""
        return f"""
        <section class="{self.theme['bg_alt']} py-16 border-t border-white/10">
            <div class="container mx-auto {PADDING_CONTAINER}">
                <p class="{self.theme['text_light']} text-sm text-center mb-8 uppercase tracking-widest">Trusted by innovative companies</p>
                <div class="flex flex-wrap justify-center gap-8 opacity-60">
                    {chr(10).join([f'<span class="{self.theme['text_muted']} font-bold text-lg">★ Brand {i+1}</span>' for i in range(5)])}
                </div>
            </div>
        </section>"""

    def render_cta_section(self) -> str:
        """Final CTA section before footer"""
        return f"""
        <section id="contact" class="relative {self.theme['bg']} {PADDING_SECTION} overflow-hidden">
            <div class="absolute inset-0 opacity-20">
                <div class="absolute -top-1/2 -left-1/2 w-96 h-96 bg-gradient-to-r {self.theme['grad']} rounded-full blur-3xl"></div>
            </div>
            <div class="container mx-auto {PADDING_CONTAINER} relative z-10 text-center">
                <h2 class="{HEADING_SECTION} {self.theme['text']} mb-8">{self.data.get('cta_text', 'Ready to get started?')}</h2>
                <div class="flex flex-col sm:flex-row gap-4 justify-center">
                    <a href="mailto:info@example.com" class="px-10 py-6 bg-gradient-to-r {self.theme['grad']} text-white rounded-full font-bold {HOVER_LIFT}">
                        Schedule a Demo
                    </a>
                    <a href="tel:+1234567890" class="px-10 py-6 {self.theme['glass']} {self.theme['text']} rounded-full font-bold {HOVER_GLOW}">
                        +1 (234) 567-890
                    </a>
                </div>
            </div>
        </section>"""

    def render_footer(self) -> str:
        """Global professional footer"""
        return f"""
        <footer class="{self.theme['bg_alt']} border-t border-white/10 py-12">
            <div class="container mx-auto {PADDING_CONTAINER}">
                <div class="grid md:grid-cols-4 gap-12 mb-12">
                    <div>
                        <h3 class="font-black text-lg {self.theme['text']} mb-4">{self.name}</h3>
                        <p class="{self.theme['text_muted']} text-sm">Premium solutions for modern businesses.</p>
                    </div>
                    <div>
                        <h4 class="font-bold {self.theme['text']} mb-4">Product</h4>
                        <ul class="space-y-2">
                            {chr(10).join([f'<li><a href="#{link.lower().replace(" ", "")}" class="{self.theme['text_muted']} hover:{self.theme["primary"]}-600 text-sm transition">{link}</a></li>' for link in self.data.get('nav', [])])}
                        </ul>
                    </div>
                    <div>
                        <h4 class="font-bold {self.theme['text']} mb-4">Company</h4>
                        <ul class="space-y-2 text-sm">
                            <li><a href="#" class="{self.theme['text_muted']} hover:{self.theme['primary']}-600 transition">About</a></li>
                            <li><a href="#" class="{self.theme['text_muted']} hover:{self.theme['primary']}-600 transition">Blog</a></li>
                            <li><a href="#" class="{self.theme['text_muted']} hover:{self.theme['primary']}-600 transition">Careers</a></li>
                        </ul>
                    </div>
                    <div>
                        <h4 class="font-bold {self.theme['text']} mb-4">Legal</h4>
                        <ul class="space-y-2 text-sm">
                            <li><a href="#" class="{self.theme['text_muted']} hover:{self.theme['primary']}-600 transition">Privacy</a></li>
                            <li><a href="#" class="{self.theme['text_muted']} hover:{self.theme['primary']}-600 transition">Terms</a></li>
                            <li><a href="mailto:legal@example.com" class="{self.theme['text_muted']} hover:{self.theme['primary']}-600 transition">Contact</a></li>
                        </ul>
                    </div>
                </div>
                <div class="border-t border-white/10 pt-8 flex justify-between items-center">
                    <p class="{self.theme['text_light']} text-sm">&copy; 2026 {self.name}. All rights reserved.</p>
                    <p class="{self.theme['text_light']} text-sm">v{self.version}</p>
                </div>
            </div>
        </footer>"""

    def build(self) -> Dict[str, Any]:
        """Assemble complete website with all sections"""
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
                
                /* Smooth animations */
                @keyframes fadeInUp {{
                    from {{ opacity: 0; transform: translateY(20px); }}
                    to {{ opacity: 1; transform: translateY(0); }}
                }}
                
                section {{ animation: fadeInUp 0.8s ease-out forwards; }}
                section:nth-child(n+2) {{ animation-delay: 0.2s; }}
            </style>
        </head>
        <body class="{self.theme['bg']} {self.theme['text']}">
            {"".join(sections)}
        </body>
        </html>
        """
        
        return {
            "html": html,
            "metadata": {
                "business_name": self.name,
                "industry": self.industry,
                "theme": self.theme['id'],
                "version": self.version,
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
    business_name = ai_input.get("business_name", "Business")
    prompt = ai_input.get("prompt", "")
    
    architect = MasterArchitect(business_name, prompt, version=version)
    return architect.build()


def rewrite_content(original_text: str, tone: str = "professional", business_context: str = "") -> List[str]:
    """
    AI-powered content rewriting with fallback.
    
    Args:
        original_text: Text to rewrite
        tone: Desired tone (professional, casual, luxury, technical)
        business_context: Context for better rewrites
    
    Returns:
        List of 3 rewritten variations
    """
    try:
        system = "You are a world-class copywriter. Output ONLY valid JSON."
        user = f"Rewrite '{original_text}' exactly 3 times in {tone} tone. Context: {business_context}. Output JSON array: ['version1', 'version2', 'version3']"
        
        res = chat_completion(system=system, user=user, temperature=0.8)
        return json.loads(res.strip().replace("```json", "").replace("```", ""))
    except:
        return [
            original_text,
            original_text.replace("the ", "the premium "),
            original_text.replace(".", " — delivered with excellence.")
        ]


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