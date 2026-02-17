import random
import json
import hashlib
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
        return "{}"  # Will be replaced by dynamic fallback


# ============================================================================
# DESIGN SYSTEM: Multi-Aesthetic Principles
# ============================================================================

class ColorMode(Enum):
    PROFESSIONAL_LIGHT = "pro_light"
    LUXURY_DARK = "luxury_dark"
    CLEAN_SLATE = "clean_slate"
    TECH_MIDNIGHT = "tech_midnight"
    WARM_CREAM = "warm_cream"
    BOLD_ELECTRIC = "bold_electric"
    EDITORIAL_MONO = "editorial_mono"
    NATURE_EARTHY = "nature_earthy"
    NEON_NOIR = "neon_noir"

# Glass Morphism Foundations
GLASS_DARK = "backdrop-blur-3xl bg-gradient-to-br from-white/8 to-white/3 border border-white/15 rounded-2xl shadow-2xl"
GLASS_LIGHT = "backdrop-blur-3xl bg-gradient-to-br from-gray-50/90 to-gray-100/70 border border-gray-200/60 rounded-2xl shadow-lg"
GLASS_BOLD = "bg-white/10 border-2 border-current rounded-xl shadow-xl"
GLASS_EDITORIAL = "bg-transparent border border-gray-900 rounded-none"

# Hover Animations
HOVER_LIFT = "transition-all duration-500 ease-out hover:-translate-y-3 hover:shadow-2xl hover:border-opacity-100"
HOVER_GLOW = "transition-all duration-500 ease-out hover:shadow-lg hover:shadow-current/20"
HOVER_SCALE = "transition-transform duration-500 ease-out hover:scale-105"
HOVER_SLIDE = "transition-all duration-300 ease-out hover:translate-x-2"

# Typography Systems - DIVERSE choices per aesthetic
FONT_STACKS = {
    "geometric":   ("'Space Grotesk', sans-serif", "https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;600;700;800&display=swap"),
    "editorial":   ("'Playfair Display', serif",   "https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;700;900&family=Source+Sans+3:wght@400;600&display=swap"),
    "brutalist":   ("'Bebas Neue', cursive",        "https://fonts.googleapis.com/css2?family=Bebas+Neue&family=IBM+Plex+Mono:wght@400;600&display=swap"),
    "modern_sans": ("'DM Sans', sans-serif",        "https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;700;900&display=swap"),
    "luxury":      ("'Cormorant Garamond', serif",  "https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@400;600;700&family=Jost:wght@300;400;500&display=swap"),
    "tech":        ("'JetBrains Mono', monospace",  "https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600;800&family=Inter:wght@400;600;700&display=swap"),
    "organic":     ("'Nunito', sans-serif",          "https://fonts.googleapis.com/css2?family=Nunito:wght@400;600;700;900&display=swap"),
    "sharp":       ("'Syne', sans-serif",            "https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&display=swap"),
}

# Heading scales
HEADING_HERO = "text-7xl md:text-8xl font-black tracking-tighter leading-[0.95]"
HEADING_HERO_EDITORIAL = "text-6xl md:text-8xl font-bold tracking-normal leading-[1.1]"
HEADING_HERO_BRUTALIST = "text-8xl md:text-[10rem] font-black tracking-tighter leading-none uppercase"
HEADING_SECTION = "text-5xl md:text-6xl font-black tracking-tight leading-[1.1]"
HEADING_FEATURE = "text-2xl md:text-3xl font-bold tracking-tight"
HEADING_CARD = "text-xl font-bold"

# Spacing
PADDING_SECTION = "py-32 md:py-40"
PADDING_SECTION_COMPACT = "py-20 md:py-28"
PADDING_CONTAINER = "px-6 md:px-8 lg:px-12"

# ============================================================================
# EXPANDED THEME PALETTE — 9 distinct looks
# ============================================================================

THEMES = {
    "pro_light": {
        "id": "pro_light", "mode": "light",
        "bg": "bg-white", "bg_alt": "bg-gray-50",
        "text": "text-gray-950", "text_muted": "text-gray-600", "text_light": "text-gray-400",
        "primary": "blue", "primary_hex": "#2563eb",
        "grad": "from-blue-600 via-blue-500 to-cyan-500",
        "btn_grad": "from-blue-600 to-blue-400",
        "glass": GLASS_LIGHT, "accent": "indigo",
        "font": "geometric",
        "card_border": "border border-gray-100",
        "industries": ["saas", "tech", "finance", "consulting"],
        "extra_css": "",
    },
    "luxury_dark": {
        "id": "luxury_dark", "mode": "dark",
        "bg": "bg-slate-950", "bg_alt": "bg-slate-900",
        "text": "text-white", "text_muted": "text-gray-300", "text_light": "text-gray-500",
        "primary": "indigo", "primary_hex": "#6366f1",
        "grad": "from-indigo-500 via-purple-500 to-pink-500",
        "btn_grad": "from-indigo-500 to-purple-600",
        "glass": GLASS_DARK, "accent": "purple",
        "font": "luxury",
        "card_border": "border border-white/10",
        "industries": ["luxury", "fashion", "creative", "agency", "tech"],
        "extra_css": "",
    },
    "clean_slate": {
        "id": "clean_slate", "mode": "light",
        "bg": "bg-slate-50", "bg_alt": "bg-white",
        "text": "text-slate-900", "text_muted": "text-slate-600", "text_light": "text-slate-400",
        "primary": "emerald", "primary_hex": "#059669",
        "grad": "from-emerald-500 via-teal-500 to-cyan-500",
        "btn_grad": "from-emerald-500 to-teal-500",
        "glass": GLASS_LIGHT, "accent": "teal",
        "font": "organic",
        "card_border": "border border-slate-100",
        "industries": ["health", "wellness", "education", "nonprofit"],
        "extra_css": "",
    },
    "tech_midnight": {
        "id": "tech_midnight", "mode": "dark",
        "bg": "bg-gray-950", "bg_alt": "bg-gray-900",
        "text": "text-white", "text_muted": "text-gray-400", "text_light": "text-gray-600",
        "primary": "cyan", "primary_hex": "#06b6d4",
        "grad": "from-cyan-500 via-blue-500 to-purple-600",
        "btn_grad": "from-cyan-400 to-blue-600",
        "glass": GLASS_DARK, "accent": "blue",
        "font": "tech",
        "card_border": "border border-cyan-900/50",
        "industries": ["ai", "blockchain", "software", "startup"],
        "extra_css": "body { background-image: radial-gradient(ellipse at 20% 50%, rgba(6,182,212,0.04) 0%, transparent 50%), radial-gradient(ellipse at 80% 20%, rgba(99,102,241,0.04) 0%, transparent 50%); }",
    },
    "warm_cream": {
        "id": "warm_cream", "mode": "light",
        "bg": "bg-amber-50", "bg_alt": "bg-white",
        "text": "text-amber-950", "text_muted": "text-amber-700", "text_light": "text-amber-400",
        "primary": "amber", "primary_hex": "#d97706",
        "grad": "from-amber-500 via-orange-500 to-rose-500",
        "btn_grad": "from-amber-500 to-orange-500",
        "glass": GLASS_LIGHT, "accent": "orange",
        "font": "modern_sans",
        "card_border": "border border-amber-100",
        "industries": ["food", "ecommerce", "hospitality", "lifestyle"],
        "extra_css": "",
    },
    "bold_electric": {
        "id": "bold_electric", "mode": "dark",
        "bg": "bg-zinc-950", "bg_alt": "bg-zinc-900",
        "text": "text-white", "text_muted": "text-zinc-300", "text_light": "text-zinc-500",
        "primary": "lime", "primary_hex": "#84cc16",
        "grad": "from-lime-400 via-green-400 to-emerald-500",
        "btn_grad": "from-lime-400 to-green-500",
        "glass": "bg-white/5 border-2 border-lime-400/30 rounded-xl shadow-xl shadow-lime-400/5",
        "accent": "lime",
        "font": "brutalist",
        "card_border": "border-2 border-lime-400/20",
        "industries": ["sports", "gaming", "fitness", "entertainment"],
        "extra_css": "body { background-image: repeating-linear-gradient(0deg, transparent, transparent 39px, rgba(132,204,22,0.03) 39px, rgba(132,204,22,0.03) 40px); }",
    },
    "editorial_mono": {
        "id": "editorial_mono", "mode": "light",
        "bg": "bg-stone-50", "bg_alt": "bg-white",
        "text": "text-stone-950", "text_muted": "text-stone-500", "text_light": "text-stone-400",
        "primary": "stone", "primary_hex": "#292524",
        "grad": "from-stone-800 via-stone-700 to-stone-600",
        "btn_grad": "from-stone-900 to-stone-700",
        "glass": "bg-white border border-stone-200 rounded-none shadow-sm",
        "accent": "red",
        "font": "editorial",
        "card_border": "border border-stone-200",
        "industries": ["media", "publishing", "design", "architecture", "law"],
        "extra_css": "",
    },
    "nature_earthy": {
        "id": "nature_earthy", "mode": "light",
        "bg": "bg-green-50", "bg_alt": "bg-white",
        "text": "text-green-950", "text_muted": "text-green-700", "text_light": "text-green-400",
        "primary": "green", "primary_hex": "#16a34a",
        "grad": "from-green-600 via-emerald-600 to-teal-600",
        "btn_grad": "from-green-600 to-emerald-500",
        "glass": "bg-white/70 backdrop-blur-xl border border-green-100 rounded-2xl shadow-lg",
        "accent": "teal",
        "font": "organic",
        "card_border": "border border-green-100",
        "industries": ["agriculture", "eco", "environment", "outdoors", "sustainability"],
        "extra_css": "",
    },
    "neon_noir": {
        "id": "neon_noir", "mode": "dark",
        "bg": "bg-black", "bg_alt": "bg-neutral-950",
        "text": "text-white", "text_muted": "text-neutral-400", "text_light": "text-neutral-600",
        "primary": "fuchsia", "primary_hex": "#d946ef",
        "grad": "from-fuchsia-500 via-violet-500 to-cyan-500",
        "btn_grad": "from-fuchsia-500 to-violet-600",
        "glass": "bg-white/5 border border-fuchsia-500/20 rounded-xl shadow-2xl shadow-fuchsia-900/20",
        "accent": "violet",
        "font": "sharp",
        "card_border": "border border-fuchsia-900/40",
        "industries": ["nightlife", "music", "entertainment", "cyberpunk", "nft", "crypto"],
        "extra_css": "body { background-image: radial-gradient(ellipse at 30% 30%, rgba(217,70,239,0.08) 0%, transparent 60%); }",
    },
}

# ============================================================================
# UNSPLASH IMAGE ROUTING — keyword → real themed URLs
# ============================================================================

UNSPLASH_COLLECTIONS = {
    "saas":        ["photo-1551434678-e076c223a692", "photo-1460925895917-afdab827c52f", "photo-1498050108023-c5249f4df085"],
    "ai":          ["photo-1677442135703-1787eea5ce01", "photo-1620712943543-bcc4688e7485", "photo-1555255707-c07966088b7b"],
    "tech":        ["photo-1518770660439-4636190af475", "photo-1518770660439-4636190af475", "photo-1519389950473-47ba0277781c"],
    "finance":     ["photo-1611974789855-9c2a0a7236a3", "photo-1559526324-4b87b5e36e44", "photo-1551288049-bebda4e38f71"],
    "health":      ["photo-1576091160399-112ba8d25d1d", "photo-1559757148-5c350d0d3c56", "photo-1576091160550-2173dba999ef"],
    "fitness":     ["photo-1517836357463-d25dfeac3438", "photo-1534438327276-14e5300c3a48", "photo-1571019614242-c5c5dee9f50b"],
    "food":        ["photo-1504674900247-0877df9cc836", "photo-1490645935967-10de6ba17061", "photo-1565299624946-b28f40a0ae38"],
    "ecommerce":   ["photo-1472851294608-062f824d29cc", "photo-1607082348824-0a96f2a4b9da", "photo-1556742049-0cfed4f6a45d"],
    "education":   ["photo-1524178232363-1fb2b075b655", "photo-1503676260728-1c00da094a0b", "photo-1580582932707-520aed937b7b"],
    "agency":      ["photo-1552664730-d307ca884978", "photo-1497366216548-37526070297c", "photo-1497366811353-6870744d04b2"],
    "luxury":      ["photo-1441986300917-64674bd600d8", "photo-1549921296-3b0f9a35af35", "photo-1590247813693-5541d1c609fd"],
    "music":       ["photo-1511671782779-c97d3d27a1d4", "photo-1493225457124-a3eb161ffa5f", "photo-1598488035139-bdbb2231ce04"],
    "gaming":      ["photo-1542751371-adc38448a05e", "photo-1580327344181-c1163234e5a0", "photo-1598550476439-6a1f857f35e7"],
    "sports":      ["photo-1461896836934-ffe607ba8211", "photo-1517649763962-0c623066013b", "photo-1579952363873-27f3bade9f55"],
    "eco":         ["photo-1542601906990-b4d3fb778b09", "photo-1465146344425-f00d5f5c8f07", "photo-1518531933037-91b2f5f229cc"],
    "architecture":["photo-1486325212027-8081e485255e", "photo-1429497419816-9ca6fa03fd89", "photo-1459767129954-1b1c1f9b9ace"],
    "default":     ["photo-1552664730-d307ca884978", "photo-1497366811353-6870744d04b2", "photo-1560179707-f14e90ef3623"],
}

def get_unsplash_url(industry: str, index: int = 0, width: int = 800) -> str:
    """Return a varied, industry-appropriate Unsplash image URL."""
    collection = UNSPLASH_COLLECTIONS.get(industry, UNSPLASH_COLLECTIONS["default"])
    photo_id = collection[index % len(collection)]
    return f"https://images.unsplash.com/{photo_id}?w={width}&auto=format&fit=crop&q=80"


# ============================================================================
# INDUSTRY DETECTION — expanded keyword map
# ============================================================================

INDUSTRY_KEYWORDS = {
    "saas":         ["software", "app", "platform", "cloud", "api", "saas", "dashboard", "workflow", "automation"],
    "ai":           ["ai", "machine learning", "ml", "neural", "algorithm", "gpt", "llm", "data science", "artificial intelligence"],
    "ecommerce":    ["shop", "store", "ecommerce", "sell", "product", "retail", "marketplace", "inventory", "cart"],
    "health":       ["health", "medical", "wellness", "clinic", "doctor", "patient", "therapy", "mental health", "care"],
    "fitness":      ["fitness", "gym", "workout", "training", "coach", "sport", "exercise", "nutrition", "bodybuilding"],
    "finance":      ["finance", "banking", "investment", "crypto", "payment", "fintech", "insurance", "accounting", "tax"],
    "agency":       ["agency", "design", "creative", "marketing", "brand", "studio", "advertising", "campaign"],
    "education":    ["education", "course", "learn", "training", "school", "university", "tutoring", "edtech", "certification"],
    "luxury":       ["luxury", "premium", "high-end", "exclusive", "prestige", "elite", "bespoke", "concierge"],
    "food":         ["food", "restaurant", "cafe", "catering", "recipe", "cooking", "meal", "delivery", "kitchen", "bakery"],
    "music":        ["music", "band", "artist", "album", "concert", "streaming", "podcast", "audio", "record"],
    "gaming":       ["gaming", "game", "esports", "indie", "studio", "play", "rpg", "stream", "twitch"],
    "sports":       ["sports", "team", "athlete", "league", "coaching", "stadium", "competition"],
    "eco":          ["eco", "green", "sustainable", "environment", "organic", "renewable", "solar", "conservation"],
    "architecture": ["architecture", "design", "interior", "construction", "property", "real estate", "blueprint"],
    "media":        ["media", "news", "journalism", "publishing", "magazine", "editorial", "content", "blog"],
    "nft":          ["nft", "crypto", "web3", "blockchain", "token", "defi", "dao", "metaverse"],
    "nightlife":    ["nightclub", "bar", "club", "event", "party", "venue", "lounge", "entertainment"],
    "agriculture":  ["farm", "agriculture", "crop", "harvest", "rural", "field", "produce"],
}

def detect_industry(prompt: str) -> str:
    """Detect industry from prompt using expanded keyword map."""
    prompt_lower = (prompt or "").lower()
    scores = {}
    for industry, keywords in INDUSTRY_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in prompt_lower)
        if score:
            scores[industry] = score
    if scores:
        return max(scores, key=scores.get)
    return "tech"

# Map industries to themes
INDUSTRY_THEME_MAP = {
    "saas":         "pro_light",
    "ai":           "tech_midnight",
    "ecommerce":    "warm_cream",
    "health":       "clean_slate",
    "fitness":      "bold_electric",
    "finance":      "luxury_dark",
    "agency":       "luxury_dark",
    "education":    "clean_slate",
    "luxury":       "luxury_dark",
    "food":         "warm_cream",
    "music":        "neon_noir",
    "gaming":       "bold_electric",
    "sports":       "bold_electric",
    "eco":          "nature_earthy",
    "architecture": "editorial_mono",
    "media":        "editorial_mono",
    "nft":          "neon_noir",
    "nightlife":    "neon_noir",
    "agriculture":  "nature_earthy",
    "tech":         "pro_light",
}


# ============================================================================
# DYNAMIC FALLBACK CONTENT — prompt-driven, not generic
# ============================================================================

INDUSTRY_CONTENT_TEMPLATES = {
    "saas": {
        "hero": {"h1": "Ship Faster. Scale Further.", "sub": "The all-in-one platform that eliminates bottlenecks and lets your team focus on what matters.", "cta": "Start Free Trial"},
        "features": [
            {"title": "One-Click Deploy", "description": "Push to production in seconds with zero-config pipelines that just work, every time.", "icon": "⚡"},
            {"title": "Real-Time Analytics", "description": "See exactly what's happening with live dashboards that surface insights automatically.", "icon": "📊"},
            {"title": "Team Collaboration", "description": "Built-in workflows keep everyone aligned with comments, reviews, and shared workspaces.", "icon": "🤝"},
        ],
        "pricing": [
            {"name": "Starter", "price": "$29", "features": ["Up to 5 users", "10GB storage", "Basic analytics", "Email support", "API access"], "featured": False},
            {"name": "Growth", "price": "$99", "features": ["Up to 50 users", "100GB storage", "Advanced analytics", "Priority support", "Custom integrations"], "featured": True},
            {"name": "Enterprise", "price": "Custom", "features": ["Unlimited users", "Unlimited storage", "Dedicated support", "SSO & compliance", "SLA guarantee"], "featured": False},
        ],
        "cta_text": "Ready to move at the speed of your ideas?",
    },
    "ai": {
        "hero": {"h1": "Intelligence at Scale.", "sub": "Harness the power of machine learning to automate decisions, predict outcomes, and unlock hidden value.", "cta": "See a Demo"},
        "features": [
            {"title": "Predictive Models", "description": "Deploy custom ML models trained on your data — no PhD required.", "icon": "🧠"},
            {"title": "Natural Language", "description": "Let your team query data in plain English and get instant, accurate results.", "icon": "💬"},
            {"title": "Auto-Optimization", "description": "The system learns from outcomes and continuously improves every workflow.", "icon": "🔄"},
        ],
        "pricing": [
            {"name": "Explorer", "price": "$49", "features": ["1M API calls/mo", "3 model deployments", "Standard latency", "Community forum", "Basic monitoring"], "featured": False},
            {"name": "Pro", "price": "$199", "features": ["20M API calls/mo", "Unlimited deployments", "Low latency", "Dedicated support", "Advanced monitoring"], "featured": True},
            {"name": "Enterprise", "price": "Custom", "features": ["Unlimited calls", "On-prem option", "Sub-10ms latency", "24/7 SLA", "Custom training"], "featured": False},
        ],
        "cta_text": "The future runs on intelligence. Make yours.",
    },
    "health": {
        "hero": {"h1": "Better Care Starts Here.", "sub": "A modern health platform that puts patients first and gives clinicians the tools they need.", "cta": "Book a Consultation"},
        "features": [
            {"title": "Patient-Centered Records", "description": "Secure, interoperable health records accessible from any device, anytime.", "icon": "🏥"},
            {"title": "Telehealth Built-In", "description": "HD video consultations with automated scheduling and insurance billing.", "icon": "📱"},
            {"title": "Care Coordination", "description": "Seamlessly coordinate between specialists, labs, and pharmacies.", "icon": "🔗"},
        ],
        "pricing": [
            {"name": "Solo Practice", "price": "$79", "features": ["1 provider", "Unlimited patients", "Telehealth", "EHR integration", "HIPAA compliant"], "featured": False},
            {"name": "Group Practice", "price": "$249", "features": ["Up to 10 providers", "Unlimited patients", "Telehealth & billing", "Analytics", "Priority support"], "featured": True},
            {"name": "Health System", "price": "Custom", "features": ["Unlimited providers", "Custom integrations", "Dedicated CSM", "API access", "Compliance tools"], "featured": False},
        ],
        "cta_text": "Healthier patients. Happier clinicians. Better outcomes.",
    },
    "food": {
        "hero": {"h1": "Food That Tells a Story.", "sub": "From farm to table, we source the finest ingredients for an experience you'll never forget.", "cta": "Reserve a Table"},
        "features": [
            {"title": "Seasonal Menu", "description": "Our chefs craft new dishes every month using the freshest local and seasonal produce.", "icon": "🌿"},
            {"title": "Private Dining", "description": "Intimate spaces for celebrations, corporate events, and unforgettable evenings.", "icon": "🕯️"},
            {"title": "Artisan Drinks", "description": "Hand-selected wine list and craft cocktails created by our award-winning mixologist.", "icon": "🍷"},
        ],
        "pricing": [
            {"name": "Lunch Menu", "price": "$35", "features": ["3-course set menu", "Seasonal ingredients", "Non-alcoholic pairing", "Vegan options", "Reservation required"], "featured": False},
            {"name": "Dinner Menu", "price": "$85", "features": ["5-course tasting menu", "Premium ingredients", "Wine pairing option", "Chef's table available", "Private room option"], "featured": True},
            {"name": "Private Event", "price": "Custom", "features": ["Exclusive buyout", "Custom menu design", "Dedicated sommelier", "Event coordinator", "Full AV setup"], "featured": False},
        ],
        "cta_text": "Book your unforgettable dining experience.",
    },
    "fitness": {
        "hero": {"h1": "Train Harder. Recover Smarter.", "sub": "Elite coaching, cutting-edge facilities, and a community that pushes you to your best self.", "cta": "Start Your Journey"},
        "features": [
            {"title": "1-on-1 Coaching", "description": "Certified coaches who create programs tailored to your exact goals and schedule.", "icon": "💪"},
            {"title": "Performance Tracking", "description": "Real-time metrics for every session — strength, cardio, recovery, and progress.", "icon": "📈"},
            {"title": "Recovery Lab", "description": "Ice baths, infrared saunas, and massage therapy for peak physical recovery.", "icon": "🧊"},
        ],
        "pricing": [
            {"name": "Basic", "price": "$49", "features": ["Gym access", "Group classes", "App tracking", "Locker room", "Free parking"], "featured": False},
            {"name": "Elite", "price": "$149", "features": ["Gym access", "Group classes", "2 PT sessions/month", "Recovery lab", "Nutrition guide"], "featured": True},
            {"name": "Pro Athlete", "price": "$399", "features": ["Unlimited PT", "Custom program", "Full recovery access", "Performance testing", "Priority booking"], "featured": False},
        ],
        "cta_text": "Your strongest self is waiting.",
    },
    "agency": {
        "hero": {"h1": "We Build Brands That Move Markets.", "sub": "Strategy, design, and execution fused into campaigns that stop the scroll and drive results.", "cta": "See Our Work"},
        "features": [
            {"title": "Brand Strategy", "description": "Deep research and sharp positioning that makes your brand impossible to ignore.", "icon": "🎯"},
            {"title": "Creative Execution", "description": "Award-winning design and content production across every channel and format.", "icon": "✏️"},
            {"title": "Performance Media", "description": "Data-driven paid media that maximizes every dollar and compounds over time.", "icon": "📡"},
        ],
        "pricing": [
            {"name": "Sprint", "price": "$4,500", "features": ["Brand audit", "1 campaign", "Social content", "Monthly report", "Dedicated PM"], "featured": False},
            {"name": "Retainer", "price": "$12,000", "features": ["Full strategy", "Ongoing campaigns", "Content calendar", "Weekly reporting", "Creative team"], "featured": True},
            {"name": "Partnership", "price": "Custom", "features": ["Embedded team", "Unlimited output", "Equity alignment", "C-suite access", "Global reach"], "featured": False},
        ],
        "cta_text": "Ready to become the brand everyone talks about?",
    },
    "luxury": {
        "hero": {"h1": "Crafted for the Exceptional.", "sub": "Where artisanship meets exclusivity. Every detail considered. Nothing left to chance.", "cta": "Request Access"},
        "features": [
            {"title": "Bespoke Design", "description": "Each piece is made to order using materials hand-selected for you alone.", "icon": "💎"},
            {"title": "White-Glove Delivery", "description": "Personal courier service with real-time tracking and luxury unboxing experience.", "icon": "📦"},
            {"title": "Lifetime Concierge", "description": "Your dedicated concierge handles modifications, repairs, and special requests forever.", "icon": "🤵"},
        ],
        "pricing": [
            {"name": "Signature", "price": "$2,500", "features": ["Ready-made collection", "Monogramming", "Gift packaging", "1-year warranty", "Free returns"], "featured": False},
            {"name": "Bespoke", "price": "$8,500", "features": ["Custom design", "Material selection", "3 fittings", "Lifetime warranty", "Personal concierge"], "featured": True},
            {"name": "Estate", "price": "POA", "features": ["Family commission", "Exclusive materials", "Dedicated atelier", "Heritage certificate", "Private event access"], "featured": False},
        ],
        "cta_text": "Some things are worth waiting for.",
    },
    "eco": {
        "hero": {"h1": "Good for You. Good for Earth.", "sub": "Sustainable solutions built from the ground up — because the planet's health and your profits aren't opposites.", "cta": "Join the Movement"},
        "features": [
            {"title": "Carbon Neutral", "description": "Every product offsets more than it creates through our certified reforestation partners.", "icon": "🌱"},
            {"title": "Circular Design", "description": "Built to last and built to return — zero-waste lifecycle from day one.", "icon": "♻️"},
            {"title": "Transparency Report", "description": "Real-time supply chain data so you always know where your product comes from.", "icon": "🔍"},
        ],
        "pricing": [
            {"name": "Seed", "price": "$29", "features": ["1 product line", "Carbon tracking", "Basic reporting", "Community access", "Eco badge"], "featured": False},
            {"name": "Grove", "price": "$89", "features": ["5 product lines", "Full carbon offset", "Impact dashboard", "Partner network", "Verified certification"], "featured": True},
            {"name": "Forest", "price": "Custom", "features": ["Unlimited lines", "B-Corp support", "Dedicated analyst", "Supply audit", "White-label tools"], "featured": False},
        ],
        "cta_text": "The most important investment you'll make.",
    },
}

def get_dynamic_fallback(business_name: str, industry: str, prompt: str) -> Dict:
    """
    Build a fully dynamic fallback payload based on business name, industry, and prompt keywords.
    No two calls should produce the same output.
    """
    template = INDUSTRY_CONTENT_TEMPLATES.get(industry, INDUSTRY_CONTENT_TEMPLATES.get("saas", {}))

    # Personalize hero with business name
    hero_base = template.get("hero", {"h1": "Premium Solution", "sub": "Built for excellence", "cta": "Get Started"})
    hero = {
        "h1": hero_base["h1"],
        "sub": hero_base["sub"],
        "cta": hero_base["cta"],
    }

    # Vary nav items by industry type
    nav_map = {
        "food": ["Menu", "Events", "Reservations", "About", "Contact"],
        "fitness": ["Programs", "Coaches", "Pricing", "Results", "Join"],
        "agency": ["Work", "Services", "About", "Journal", "Contact"],
        "health": ["Services", "Providers", "Pricing", "Research", "Contact"],
        "ecommerce": ["Products", "Collections", "About", "Reviews", "Contact"],
        "luxury": ["Collections", "Bespoke", "Maison", "Stockists", "Contact"],
        "eco": ["Products", "Impact", "Certifications", "Blog", "Contact"],
        "music": ["Music", "Shows", "Merch", "Press", "Contact"],
        "gaming": ["Games", "Community", "Tournaments", "Press", "Contact"],
    }
    nav = nav_map.get(industry, ["Features", "Pricing", "FAQ", "About", "Contact"])

    features = template.get("features", [
        {"title": "Core Capability", "description": "Best-in-class performance and reliability.", "icon": "✨"},
        {"title": "Deep Integration", "description": "Connects with every tool in your stack.", "icon": "🔗"},
        {"title": "Expert Support", "description": "Real humans ready to help 24/7.", "icon": "💬"},
    ])

    pricing = template.get("pricing", [
        {"name": "Starter", "price": "$29", "features": ["Feature A", "Feature B", "Feature C", "Feature D", "Feature E"], "featured": False},
        {"name": "Pro", "price": "$99", "features": ["Everything in Starter", "Feature F", "Feature G", "Feature H", "Priority support"], "featured": True},
        {"name": "Enterprise", "price": "Custom", "features": ["Everything in Pro", "Dedicated account manager", "Custom integrations", "SLA guarantee", "Invoice billing"], "featured": False},
    ])

    testimonials = [
        {"name": "Sarah K.", "company": "Growth Co.", "quote": f"Switching to {business_name} was the best decision we made this year. Results speak for themselves."},
        {"name": "Marcus T.", "company": "Apex Ventures", "quote": f"{business_name} didn't just meet our expectations — they redefined what we thought was possible."},
    ]

    faq = [
        {"q": "How quickly can we get started?", "a": "Most customers are up and running within 24 hours. Our onboarding team walks you through every step."},
        {"q": "Is there a long-term commitment?", "a": "No contracts. You can upgrade, downgrade, or cancel at any time without penalties."},
        {"q": "What support is included?", "a": "Every plan includes access to our support team. Pro and Enterprise customers get priority response and a dedicated account manager."},
    ]

    cta_text = template.get("cta_text", f"Ready to experience what {business_name} can do for you?")

    # Image keywords for Unsplash routing
    unsplash_keywords = {
        "saas": ["technology", "software", "dashboard", "team", "office"],
        "ai": ["artificial intelligence", "data", "neural network", "technology", "future"],
        "food": ["food", "restaurant", "chef", "cuisine", "dining"],
        "fitness": ["fitness", "gym", "workout", "athlete", "sport"],
        "health": ["healthcare", "wellness", "medical", "doctor", "clinic"],
        "agency": ["creative", "design", "team", "office", "brainstorm"],
        "luxury": ["luxury", "premium", "exclusive", "high-end", "artisan"],
        "eco": ["nature", "sustainable", "green", "environment", "forest"],
        "music": ["music", "concert", "studio", "artist", "live"],
        "gaming": ["gaming", "esports", "controller", "digital", "stream"],
    }

    return {
        "nav": nav,
        "hero": hero,
        "features": features,
        "pricing": pricing,
        "testimonials": testimonials,
        "faq": faq,
        "cta_text": cta_text,
        "unsplash_keywords": unsplash_keywords.get(industry, ["technology", "business", "modern", "team", "office"]),
    }


# ============================================================================
# SECTION VARIANT LIBRARY: Multi-Style Components
# ============================================================================

class HeroVariant:
    """5 distinct hero styles for maximum visual variety."""

    @staticmethod
    def split_grid(theme: Dict, data: Dict, industry: str, font_css: str) -> str:
        """Classic: Text left, dynamic industry image right."""
        try:
            img_url = get_unsplash_url(industry, index=0, width=900)
            return f"""
            <section id="hero" class="relative {theme['bg']} {PADDING_SECTION} overflow-hidden pt-32">
                <div class="container mx-auto {PADDING_CONTAINER}">
                    <div class="grid lg:grid-cols-2 gap-16 lg:gap-20 items-center min-h-[70vh]">
                        <div class="space-y-8">
                            <div class="space-y-6">
                                <span class="inline-block px-4 py-2 rounded-full {theme['glass']} text-sm font-semibold {theme['text']} {theme['card_border']}">
                                    ✦ {data.get('hero', {}).get('cta', 'Get Started')}
                                </span>
                                <h1 class="{HEADING_HERO} {theme['text']}">{data.get('hero', {}).get('h1', 'Premium Solution')}</h1>
                            </div>
                            <p class="text-xl md:text-2xl {theme['text_muted']} leading-relaxed max-w-xl">{data.get('hero', {}).get('sub', 'Built for excellence')}</p>
                            <div class="flex flex-col sm:flex-row gap-4 pt-4">
                                <a href="#contact" class="px-8 py-5 bg-gradient-to-r {theme['btn_grad']} text-white rounded-full font-bold text-lg {HOVER_LIFT} inline-block text-center shadow-lg">
                                    {data.get('hero', {}).get('cta', 'Get Started')}
                                </a>
                                <a href="#features" class="px-8 py-5 {theme['glass']} {theme['text']} rounded-full font-bold {HOVER_GLOW} inline-block text-center {theme['card_border']}">
                                    Learn More →
                                </a>
                            </div>
                        </div>
                        <div class="relative h-[520px] md:h-[640px] rounded-3xl overflow-hidden shadow-2xl">
                            <img src="{img_url}" alt="hero" class="w-full h-full object-cover" loading="eager" />
                            <div class="absolute inset-0 bg-gradient-to-t from-black/30 to-transparent"></div>
                        </div>
                    </div>
                </div>
            </section>"""
        except Exception as e:
            logger.error(f"split_grid hero error: {e}")
            return f"<section id='hero' class='{theme['bg']} py-32'><div class='container mx-auto px-6'><h1>Welcome</h1></div></section>"

    @staticmethod
    def centered_spotlight(theme: Dict, data: Dict, industry: str, font_css: str) -> str:
        """Bold: Full-width centered with dramatic orb background."""
        try:
            return f"""
            <section id="hero" class="relative {theme['bg']} {PADDING_SECTION} overflow-hidden min-h-screen flex items-center">
                <div class="absolute inset-0 overflow-hidden pointer-events-none">
                    <div class="absolute top-1/4 left-1/2 -translate-x-1/2 w-[800px] h-[800px] bg-gradient-to-r {theme['grad']} rounded-full blur-3xl opacity-15"></div>
                    <div class="absolute bottom-0 right-0 w-96 h-96 bg-gradient-to-l {theme['grad']} rounded-full blur-3xl opacity-10"></div>
                </div>
                <div class="container mx-auto {PADDING_CONTAINER} relative z-10">
                    <div class="max-w-5xl mx-auto text-center space-y-10">
                        <div class="inline-flex items-center gap-2 px-5 py-2.5 {theme['glass']} {theme['card_border']} rounded-full text-sm font-medium {theme['text_muted']}">
                            <span class="w-2 h-2 rounded-full bg-gradient-to-r {theme['grad']} animate-pulse"></span>
                            Now available — explore what's possible
                        </div>
                        <h1 class="{HEADING_HERO} {theme['text']}">{data.get('hero', {}).get('h1', 'Premium Solution')}</h1>
                        <p class="text-2xl md:text-3xl {theme['text_muted']} font-light leading-relaxed max-w-3xl mx-auto">{data.get('hero', {}).get('sub', 'Built for excellence')}</p>
                        <div class="flex flex-col sm:flex-row gap-4 justify-center pt-4">
                            <a href="#contact" class="px-10 py-6 bg-gradient-to-r {theme['btn_grad']} text-white rounded-full font-bold text-lg {HOVER_LIFT} inline-block shadow-xl">
                                {data.get('hero', {}).get('cta', 'Get Started')}
                            </a>
                            <a href="#features" class="px-10 py-6 {theme['glass']} {theme['text']} rounded-full font-bold {HOVER_GLOW} inline-block {theme['card_border']}">
                                See How It Works
                            </a>
                        </div>
                    </div>
                </div>
            </section>"""
        except Exception as e:
            logger.error(f"centered_spotlight hero error: {e}")
            return f"<section id='hero' class='{theme['bg']} py-32'><div class='container mx-auto px-6 text-center'><h1>Welcome</h1></div></section>"

    @staticmethod
    def editorial_slash(theme: Dict, data: Dict, industry: str, font_css: str) -> str:
        """Editorial: Large typography with diagonal image crop."""
        try:
            img_url = get_unsplash_url(industry, index=1, width=1000)
            return f"""
            <section id="hero" class="relative {theme['bg']} overflow-hidden min-h-screen">
                <div class="absolute right-0 top-0 w-1/2 h-full">
                    <img src="{img_url}" alt="hero" class="w-full h-full object-cover" loading="eager" />
                    <div class="absolute inset-0 bg-gradient-to-r {theme['bg'].replace('bg-', 'from-').split(' ')[0]} via-transparent to-transparent"></div>
                </div>
                <div class="relative z-10 container mx-auto {PADDING_CONTAINER} min-h-screen flex items-center">
                    <div class="w-full lg:w-3/5 space-y-10 py-40">
                        <p class="text-sm font-bold uppercase tracking-[0.3em] {theme['text_muted']}">Est. 2024 · Premium</p>
                        <h1 class="{HEADING_HERO_EDITORIAL} {theme['text']}">{data.get('hero', {}).get('h1', 'Premium Solution')}</h1>
                        <div class="w-24 h-0.5 bg-gradient-to-r {theme['grad']}"></div>
                        <p class="text-xl {theme['text_muted']} leading-relaxed max-w-lg">{data.get('hero', {}).get('sub', 'Built for excellence')}</p>
                        <a href="#contact" class="inline-block px-10 py-5 bg-gradient-to-r {theme['btn_grad']} text-white font-bold text-lg {HOVER_LIFT} shadow-xl rounded-sm">
                            {data.get('hero', {}).get('cta', 'Get Started')} →
                        </a>
                    </div>
                </div>
            </section>"""
        except Exception as e:
            logger.error(f"editorial_slash hero error: {e}")
            return f"<section id='hero' class='{theme['bg']} py-32'><div class='container mx-auto px-6'><h1>Welcome</h1></div></section>"

    @staticmethod
    def brutalist_full(theme: Dict, data: Dict, industry: str, font_css: str) -> str:
        """Brutalist: Oversized type, raw grid, maximum impact."""
        try:
            img_url = get_unsplash_url(industry, index=2, width=600)
            return f"""
            <section id="hero" class="relative {theme['bg']} pt-32 pb-20 overflow-hidden border-b {theme['card_border']}">
                <div class="container mx-auto {PADDING_CONTAINER}">
                    <div class="mb-8">
                        <span class="text-xs font-mono uppercase tracking-[0.4em] {theme['text_muted']} border {theme['card_border']} px-4 py-2">
                            ◆ Featured
                        </span>
                    </div>
                    <div class="grid lg:grid-cols-12 gap-8 items-end">
                        <div class="lg:col-span-8 space-y-8">
                            <h1 class="{HEADING_HERO_BRUTALIST} {theme['text']} leading-none">
                                {data.get('hero', {}).get('h1', 'Premium Solution').upper()}
                            </h1>
                        </div>
                        <div class="lg:col-span-4 space-y-6">
                            <div class="h-px w-full bg-gradient-to-r {theme['grad']} opacity-60"></div>
                            <p class="text-lg {theme['text_muted']} leading-relaxed">{data.get('hero', {}).get('sub', 'Built for excellence')}</p>
                            <a href="#contact" class="inline-block px-8 py-5 bg-gradient-to-r {theme['btn_grad']} text-white font-black uppercase tracking-widest {HOVER_LIFT}">
                                {data.get('hero', {}).get('cta', 'Get Started')}
                            </a>
                        </div>
                    </div>
                    <div class="mt-16 h-[400px] md:h-[500px] overflow-hidden">
                        <img src="{img_url}" alt="hero" class="w-full h-full object-cover grayscale hover:grayscale-0 transition-all duration-700" loading="eager" />
                    </div>
                </div>
            </section>"""
        except Exception as e:
            logger.error(f"brutalist_full hero error: {e}")
            return f"<section id='hero' class='{theme['bg']} py-32'><div class='container mx-auto px-6'><h1>Welcome</h1></div></section>"

    @staticmethod
    def cinematic_overlay(theme: Dict, data: Dict, industry: str, font_css: str) -> str:
        """Cinematic: Full-screen image with text overlay and gradient veil."""
        try:
            img_url = get_unsplash_url(industry, index=0, width=1400)
            return f"""
            <section id="hero" class="relative min-h-screen flex items-center overflow-hidden">
                <div class="absolute inset-0">
                    <img src="{img_url}" alt="hero" class="w-full h-full object-cover" loading="eager" />
                    <div class="absolute inset-0 bg-gradient-to-r from-black/80 via-black/50 to-transparent"></div>
                    <div class="absolute inset-0 bg-gradient-to-t from-black/60 via-transparent to-transparent"></div>
                </div>
                <div class="relative z-10 container mx-auto {PADDING_CONTAINER}">
                    <div class="max-w-3xl space-y-8">
                        <p class="text-sm font-semibold uppercase tracking-[0.4em] text-white/60">Premium Experience</p>
                        <h1 class="{HEADING_HERO} text-white drop-shadow-2xl">{data.get('hero', {}).get('h1', 'Premium Solution')}</h1>
                        <p class="text-xl md:text-2xl text-white/80 leading-relaxed">{data.get('hero', {}).get('sub', 'Built for excellence')}</p>
                        <div class="flex flex-col sm:flex-row gap-4 pt-4">
                            <a href="#contact" class="px-10 py-6 bg-gradient-to-r {theme['btn_grad']} text-white rounded-full font-bold text-lg {HOVER_LIFT} inline-block shadow-2xl">
                                {data.get('hero', {}).get('cta', 'Get Started')}
                            </a>
                            <a href="#features" class="px-10 py-6 bg-white/10 backdrop-blur-xl text-white border border-white/20 rounded-full font-bold {HOVER_GLOW} inline-block">
                                Explore ↓
                            </a>
                        </div>
                    </div>
                </div>
            </section>"""
        except Exception as e:
            logger.error(f"cinematic_overlay hero error: {e}")
            return f"<section id='hero' class='{theme['bg']} py-32'><div class='container mx-auto px-6'><h1>Welcome</h1></div></section>"


class FeatureVariant:
    """4 distinct feature section designs."""

    @staticmethod
    def cards_grid(theme: Dict, features: List[Dict], industry: str) -> str:
        """Classic: 3-column icon card grid."""
        try:
            items = "".join([f"""
            <div class="{theme['glass']} {theme['card_border']} p-10 {HOVER_LIFT} flex flex-col gap-6">
                <div class="w-14 h-14 rounded-2xl bg-gradient-to-br {theme['grad']} flex items-center justify-center text-2xl shadow-lg flex-shrink-0">
                    {feat.get('icon', '✨')}
                </div>
                <div>
                    <h3 class="{HEADING_CARD} {theme['text']} mb-3">{feat.get('title', 'Feature')}</h3>
                    <p class="{theme['text_muted']} leading-relaxed text-sm">{feat.get('description', 'Premium feature')}</p>
                </div>
            </div>""" for feat in (features or [])])

            return f"""
            <section id="features" class="{theme['bg_alt']} {PADDING_SECTION}">
                <div class="container mx-auto {PADDING_CONTAINER}">
                    <div class="text-center mb-16 space-y-4">
                        <h2 class="{HEADING_SECTION} {theme['text']}">Built for Results</h2>
                        <p class="text-xl {theme['text_muted']} max-w-2xl mx-auto">Everything you need — nothing you don't.</p>
                    </div>
                    <div class="grid md:grid-cols-3 gap-8">
                        {items}
                    </div>
                </div>
            </section>"""
        except Exception as e:
            logger.error(f"cards_grid features error: {e}")
            return f"<section id='features' class='{theme['bg_alt']} py-20'><h2 class='text-center text-4xl font-bold'>Features</h2></section>"

    @staticmethod
    def alternating_blocks(theme: Dict, features: List[Dict], industry: str) -> str:
        """Rich: Alternating text + image blocks with real industry photos."""
        try:
            blocks = "".join([f"""
            <div class="grid lg:grid-cols-2 gap-12 lg:gap-20 items-center">
                <div class="space-y-6 {'order-2 lg:order-2' if i % 2 else 'order-2 lg:order-1'}">
                    <div class="w-12 h-12 bg-gradient-to-br {theme['grad']} rounded-xl flex items-center justify-center text-xl shadow-lg">
                        {feat.get('icon', '✨')}
                    </div>
                    <h3 class="{HEADING_FEATURE} {theme['text']}">{feat.get('title', 'Feature')}</h3>
                    <p class="text-lg {theme['text_muted']} leading-relaxed">{feat.get('description', 'Premium feature')}</p>
                    <a href="#contact" class="inline-flex items-center gap-2 text-sm font-semibold {theme['text']} {HOVER_SLIDE} opacity-70 hover:opacity-100">
                        Learn more <span>→</span>
                    </a>
                </div>
                <div class="h-96 rounded-3xl overflow-hidden shadow-xl {'order-1 lg:order-1' if i % 2 else 'order-1 lg:order-2'}">
                    <img src="{get_unsplash_url(industry, index=i, width=700)}" alt="{feat.get('title', 'Feature')}" class="w-full h-full object-cover {HOVER_SCALE}" loading="lazy" />
                </div>
            </div>""" for i, feat in enumerate(features or [])])

            return f"""
            <section id="features" class="{theme['bg']} {PADDING_SECTION}">
                <div class="container mx-auto {PADDING_CONTAINER}">
                    <h2 class="{HEADING_SECTION} {theme['text']} mb-4 text-center">Why Choose Us</h2>
                    <p class="text-xl {theme['text_muted']} text-center mb-24 max-w-2xl mx-auto">Every detail designed to give you the advantage.</p>
                    <div class="space-y-32">
                        {blocks}
                    </div>
                </div>
            </section>"""
        except Exception as e:
            logger.error(f"alternating_blocks features error: {e}")
            return f"<section id='features' class='{theme['bg']} py-20'><h2 class='text-center text-4xl font-bold'>Features</h2></section>"

    @staticmethod
    def showcase_grid(theme: Dict, features: List[Dict], industry: str) -> str:
        """Modern: Large cards with accent bar top."""
        try:
            items = "".join([f"""
            <div class="{theme['glass']} {theme['card_border']} rounded-3xl overflow-hidden {HOVER_LIFT} flex flex-col">
                <div class="h-1.5 bg-gradient-to-r {theme['grad']}"></div>
                <div class="p-10 flex flex-col flex-grow">
                    <div class="w-16 h-16 mb-8 rounded-2xl bg-gradient-to-br {theme['grad']} flex items-center justify-center text-3xl shadow-lg">
                        {feat.get('icon', '✨')}
                    </div>
                    <h3 class="text-2xl font-bold {theme['text']} mb-4">{feat.get('title', 'Feature')}</h3>
                    <p class="{theme['text_muted']} text-sm leading-relaxed flex-grow">{feat.get('description', 'Premium feature')}</p>
                    <div class="mt-8 pt-6 border-t {theme['card_border']}">
                        <a href="#contact" class="text-sm font-bold {theme['text']} hover:opacity-60 transition">
                            Explore →
                        </a>
                    </div>
                </div>
            </div>""" for feat in (features or [])])

            return f"""
            <section id="features" class="{theme['bg_alt']} {PADDING_SECTION}">
                <div class="container mx-auto {PADDING_CONTAINER}">
                    <h2 class="{HEADING_SECTION} {theme['text']} text-center mb-4">Our Solutions</h2>
                    <p class="text-xl {theme['text_muted']} text-center mb-20 max-w-2xl mx-auto">Powerful, flexible, and built to scale with you.</p>
                    <div class="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
                        {items}
                    </div>
                </div>
            </section>"""
        except Exception as e:
            logger.error(f"showcase_grid features error: {e}")
            return f"<section id='features' class='{theme['bg_alt']} py-20'><h2 class='text-center text-4xl font-bold'>Features</h2></section>"

    @staticmethod
    def numbered_list(theme: Dict, features: List[Dict], industry: str) -> str:
        """Editorial: Numbered feature rows for a refined, linear layout."""
        try:
            items = "".join([f"""
            <div class="grid md:grid-cols-12 gap-8 py-12 border-b {theme['card_border']} items-center group {HOVER_GLOW}">
                <div class="md:col-span-1 text-4xl font-black {theme['text_light']} group-hover:opacity-100 transition">
                    0{i+1}
                </div>
                <div class="md:col-span-1 text-3xl">
                    {feat.get('icon', '✨')}
                </div>
                <div class="md:col-span-5">
                    <h3 class="{HEADING_FEATURE} {theme['text']}">{feat.get('title', 'Feature')}</h3>
                </div>
                <div class="md:col-span-5">
                    <p class="{theme['text_muted']} leading-relaxed">{feat.get('description', '')}</p>
                </div>
            </div>""" for i, feat in enumerate(features or [])])

            return f"""
            <section id="features" class="{theme['bg']} {PADDING_SECTION}">
                <div class="container mx-auto {PADDING_CONTAINER}">
                    <div class="flex items-end justify-between mb-20 border-b-2 {theme['card_border']} pb-8">
                        <h2 class="{HEADING_SECTION} {theme['text']}">What We Do</h2>
                        <a href="#contact" class="text-sm font-bold {theme['text_muted']} {HOVER_SLIDE}">See all services →</a>
                    </div>
                    <div>
                        {items}
                    </div>
                </div>
            </section>"""
        except Exception as e:
            logger.error(f"numbered_list features error: {e}")
            return f"<section id='features' class='{theme['bg']} py-20'><h2 class='text-center text-4xl font-bold'>Features</h2></section>"


class PricingVariant:
    """3 distinct pricing layouts."""

    @staticmethod
    def tiered_cards(theme: Dict, tiers: List[Dict]) -> str:
        """Classic: 3 cards, middle featured."""
        try:
            cards = "".join([f"""
            <div class="{'bg-gradient-to-b ' + theme['grad'] + ' p-px rounded-3xl shadow-2xl' if tier.get('featured') else ''}">
                <div class="{'' if tier.get('featured') else theme['glass'] + ' ' + theme['card_border']} {'bg-' + theme['bg'].replace('bg-', '') + ' ' if tier.get('featured') else ''}rounded-3xl p-10 flex flex-col h-full {'bg-black/20 backdrop-blur-xl text-white' if tier.get('featured') else ''}">
                    {'<div class="text-xs font-bold uppercase tracking-[0.2em] mb-4 opacity-60">Most Popular</div>' if tier.get('featured') else '<div class="mb-10"></div>'}
                    <h3 class="{HEADING_CARD} {'' if tier.get('featured') else theme['text']} mb-2">{tier.get('name', 'Plan')}</h3>
                    <div class="mb-8 mt-4">
                        <span class="text-5xl font-black {'' if tier.get('featured') else theme['text']}">{tier.get('price', '$0')}</span>
                        <span class="{'opacity-60' if tier.get('featured') else theme['text_muted']}">/month</span>
                    </div>
                    <ul class="space-y-4 mb-10 flex-grow">
                        {chr(10).join([f'<li class="{"opacity-80" if tier.get("featured") else theme["text_muted"]} text-sm flex items-center gap-3"><span class="w-5 h-5 rounded-full bg-gradient-to-br {theme["grad"]} flex items-center justify-center text-white text-xs flex-shrink-0">✓</span>{feat}</li>' for feat in (tier.get('features', []) or [])])}
                    </ul>
                    <a href="#contact" class="block w-full py-4 text-center rounded-xl font-bold transition-all duration-300 {'bg-white text-gray-900 hover:bg-gray-100' if tier.get('featured') else 'bg-gradient-to-r ' + theme['btn_grad'] + ' text-white ' + HOVER_LIFT}">
                        Get Started
                    </a>
                </div>
            </div>""" for tier in (tiers or [])])

            return f"""
            <section id="pricing" class="{theme['bg_alt']} {PADDING_SECTION}">
                <div class="container mx-auto {PADDING_CONTAINER}">
                    <div class="text-center mb-16 space-y-4">
                        <h2 class="{HEADING_SECTION} {theme['text']}">Simple, Transparent Pricing</h2>
                        <p class="text-xl {theme['text_muted']}">Pay for what you need. Scale when you're ready.</p>
                    </div>
                    <div class="grid md:grid-cols-3 gap-6 max-w-6xl mx-auto items-stretch">
                        {cards}
                    </div>
                </div>
            </section>"""
        except Exception as e:
            logger.error(f"tiered_cards pricing error: {e}")
            return f"<section id='pricing' class='{theme['bg_alt']} py-20'><h2 class='text-center text-4xl font-bold'>Pricing</h2></section>"

    @staticmethod
    def comparison_table(theme: Dict, tiers: List[Dict]) -> str:
        """Enterprise: Feature comparison table."""
        try:
            tier_headers = "".join([f'<th class="{theme["text"]} font-bold text-right px-4 py-3 text-sm">{t.get("name", "Plan")}<br><span class="text-2xl font-black">{t.get("price", "Custom")}</span></th>' for t in (tiers or [])])
            all_features = []
            seen = set()
            for t in (tiers or []):
                for f in (t.get('features', []) or []):
                    if f not in seen:
                        all_features.append(f)
                        seen.add(f)

            feature_rows = "".join([f"""
            <tr class="border-b {theme['card_border']} hover:{theme['bg_alt'].replace('bg-', 'bg-')} transition">
                <td class="{theme['text']} py-4 pr-4 text-sm">{feat}</td>
                {chr(10).join([f'<td class="text-right px-4 py-4 text-sm"><span class="{"text-green-500 font-bold" if feat in (tiers[i].get("features", []) or []) else theme["text_light"]}">{"✓" if feat in (tiers[i].get("features", []) or []) else "—"}</span></td>' for i in range(len(tiers or []))])}
            </tr>""" for feat in all_features])

            return f"""
            <section id="pricing" class="{theme['bg']} {PADDING_SECTION}">
                <div class="container mx-auto {PADDING_CONTAINER}">
                    <h2 class="{HEADING_SECTION} {theme['text']} text-center mb-4">Compare Plans</h2>
                    <p class="text-xl {theme['text_muted']} text-center mb-16">Full transparency. No hidden fees.</p>
                    <div class="overflow-x-auto {theme['glass']} {theme['card_border']} p-8 rounded-3xl">
                        <table class="w-full">
                            <thead>
                                <tr class="border-b-2 {theme['card_border']}">
                                    <th class="{theme['text']} font-bold text-left pb-6 text-sm">Feature</th>
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
            logger.error(f"comparison_table pricing error: {e}")
            return f"<section id='pricing' class='{theme['bg']} py-20'><h2 class='text-center text-4xl font-bold'>Pricing</h2></section>"

    @staticmethod
    def two_option_split(theme: Dict, tiers: List[Dict]) -> str:
        """Clean: Two main options side by side — great for simpler offerings."""
        try:
            top_two = (tiers or [])[:2]
            cards = "".join([f"""
            <div class="{theme['glass']} {theme['card_border']} p-12 rounded-3xl {HOVER_LIFT} flex flex-col gap-8">
                <div>
                    <h3 class="text-3xl font-black {theme['text']}">{tier.get('name', 'Plan')}</h3>
                    <p class="text-6xl font-black {theme['text']} mt-4">{tier.get('price', '$0')}<span class="text-lg font-normal {theme['text_muted']}">/mo</span></p>
                </div>
                <ul class="space-y-3 flex-grow">
                    {chr(10).join([f'<li class="flex items-center gap-3 {theme["text_muted"]} text-sm"><span class="text-green-500">✓</span>{feat}</li>' for feat in (tier.get("features", []) or [])])}
                </ul>
                <a href="#contact" class="block py-5 text-center font-bold rounded-2xl bg-gradient-to-r {theme['btn_grad']} text-white {HOVER_LIFT} shadow-lg">
                    Get {tier.get('name', 'Started')}
                </a>
            </div>""" for tier in top_two])

            return f"""
            <section id="pricing" class="{theme['bg_alt']} {PADDING_SECTION}">
                <div class="container mx-auto {PADDING_CONTAINER}">
                    <h2 class="{HEADING_SECTION} {theme['text']} text-center mb-16">Your Plan</h2>
                    <div class="grid md:grid-cols-2 gap-8 max-w-4xl mx-auto">
                        {cards}
                    </div>
                    <p class="text-center {theme['text_muted']} mt-10 text-sm">Need something custom? <a href="#contact" class="{theme['text']} font-bold underline">Talk to us →</a></p>
                </div>
            </section>"""
        except Exception as e:
            logger.error(f"two_option_split pricing error: {e}")
            return f"<section id='pricing' class='{theme['bg_alt']} py-20'><h2 class='text-center text-4xl font-bold'>Pricing</h2></section>"


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
            self.industry = detect_industry(self.prompt)
            self.theme = self._select_theme()
            self.font_family, self.font_url = FONT_STACKS.get(self.theme.get("font", "geometric"), FONT_STACKS["geometric"])
            self.data = {}
            # Deterministic-but-varied seed based on name + prompt hash
            seed_str = f"{self.name}{self.prompt}{version}"
            self.seed = int(hashlib.md5(seed_str.encode()).hexdigest(), 16) % (2**32)
            random.seed(self.seed)
            logger.info(f"MasterArchitect initialized: {self.name}, industry: {self.industry}, theme: {self.theme['id']}, seed: {self.seed}")
        except Exception as e:
            logger.error(f"Error initializing MasterArchitect: {e}")
            self.name = business_name or "Business"
            self.prompt = prompt or ""
            self.version = version
            self.industry = "tech"
            self.theme = THEMES.get("pro_light", {})
            self.font_family, self.font_url = FONT_STACKS["geometric"]
            self.data = {}
            self.seed = 42

    def _select_theme(self) -> Dict:
        """Select theme based on industry."""
        try:
            theme_id = INDUSTRY_THEME_MAP.get(self.industry, "pro_light")
            return THEMES.get(theme_id, THEMES["pro_light"])
        except Exception as e:
            logger.warning(f"Error selecting theme: {e}")
            return THEMES.get("pro_light", {})

    def get_ai_payload(self) -> Dict:
        """Orchestrate single AI call to generate all website content."""
        try:
            system_msg = (
                "You are an elite Web Architect designing premium, conversion-optimized websites. "
                "Output ONLY valid JSON. No markdown, no preamble, no trailing text."
            )

            user_msg = f"""
Create premium, specific website content for '{self.name}'.
Business Context: {self.prompt}
Industry: {self.industry}

Generate a JSON object with EXACTLY these keys:
- nav: array of 5 short navigation link labels relevant to this business
- hero: {{h1: (bold, punchy headline under 8 words), sub: (compelling 1-2 sentence subtitle), cta: (action button text, 2-4 words)}}
- features: array of exactly 3 objects, each: {{title: (feature name), description: (2-sentence specific benefit), icon: (relevant emoji)}}
- pricing: array of exactly 3 objects: {{name, price (e.g. "$49" or "Custom"), features: array of 5 specific strings, featured: boolean (true only for middle)}}
- testimonials: array of 2 objects: {{name, company, quote (specific, not generic)}}
- faq: array of 3 objects: {{q, a}} — answer common objections specific to this business
- cta_text: one powerful closing sentence for the final CTA section
- unsplash_keywords: array of 5 relevant image search terms

IMPORTANT: Make ALL content specific to '{self.name}' and '{self.prompt}'. Do NOT use generic filler text.
            """

            if not AI_AVAILABLE:
                logger.warning("AI client not available, using dynamic fallback payload")
                return get_dynamic_fallback(self.name, self.industry, self.prompt)

            res = chat_completion(system=system_msg, user=user_msg, temperature=0.8)
            cleaned = res.strip().replace("```json", "").replace("```", "").strip()
            payload = json.loads(cleaned)
            logger.info(f"AI payload generated successfully for {self.name}")
            return payload
        except json.JSONDecodeError as e:
            logger.error(f"JSON parse error in AI payload: {e}")
            return get_dynamic_fallback(self.name, self.industry, self.prompt)
        except Exception as e:
            logger.error(f"Error getting AI payload: {e}\n{traceback.format_exc()}")
            return get_dynamic_fallback(self.name, self.industry, self.prompt)

    # ------------------------------------------------------------------
    # Section renderers
    # ------------------------------------------------------------------

    def render_nav(self) -> str:
        """Fixed navigation with smooth scroll and professional styling."""
        try:
            nav_items = "".join([
                f'<li><a href="#{link.lower().replace(" ", "").replace("/", "")}" class="{self.theme.get("text_muted")} hover:{self.theme.get("text", "text-gray-900").replace("text-", "")} transition-colors duration-300 font-medium text-sm">{link}</a></li>'
                for link in (self.data.get('nav', []) or [])
            ])
            mode_class = "border-white/10" if self.theme.get("mode") == "dark" else "border-gray-200/60"

            return f"""
            <nav class="fixed top-0 w-full z-50 {self.theme.get('glass')} border-b {mode_class} py-4">
                <div class="container mx-auto {PADDING_CONTAINER} flex justify-between items-center gap-8">
                    <a href="#" class="text-2xl font-black tracking-tighter {self.theme.get('text')} flex-shrink-0">{self.name}</a>
                    <ul class="hidden md:flex gap-8">{nav_items}</ul>
                    <a href="#contact" class="flex-shrink-0 px-6 py-3 bg-gradient-to-r {self.theme.get('btn_grad')} text-white rounded-full font-bold text-sm {HOVER_LIFT} shadow-lg">
                        {self.data.get('hero', {}).get('cta', 'Get Started')}
                    </a>
                </div>
            </nav>"""
        except Exception as e:
            logger.error(f"Error rendering nav: {e}")
            return f"<nav class='fixed top-0 w-full z-50 bg-white border-b py-4'><div class='container mx-auto px-6 flex justify-between items-center'><a href='#' class='text-2xl font-bold'>{self.name}</a></div></nav>"

    def render_hero(self) -> str:
        """Select hero variant based on industry and theme."""
        try:
            # Deterministic but varied selection
            HERO_MAP = {
                "luxury":       HeroVariant.cinematic_overlay,
                "food":         HeroVariant.cinematic_overlay,
                "fitness":      HeroVariant.cinematic_overlay,
                "agency":       HeroVariant.editorial_slash,
                "media":        HeroVariant.editorial_slash,
                "architecture": HeroVariant.editorial_slash,
                "gaming":       HeroVariant.brutalist_full,
                "sports":       HeroVariant.brutalist_full,
                "music":        HeroVariant.brutalist_full,
                "nft":          HeroVariant.centered_spotlight,
                "ai":           HeroVariant.centered_spotlight,
                "saas":         HeroVariant.split_grid,
                "finance":      HeroVariant.split_grid,
                "health":       HeroVariant.split_grid,
            }
            variant_fn = HERO_MAP.get(self.industry, HeroVariant.split_grid)
            return variant_fn(self.theme, self.data, self.industry, self.font_url)
        except Exception as e:
            logger.error(f"Error rendering hero: {e}")
            return f"<section id='hero' class='{self.theme.get('bg')} py-32'><div class='container mx-auto px-6 text-center'><h1 class='text-6xl font-bold'>{self.name}</h1></div></section>"

    def render_features(self) -> str:
        """Select feature variant based on industry."""
        try:
            FEATURE_MAP = {
                "ecommerce":    FeatureVariant.showcase_grid,
                "saas":         FeatureVariant.cards_grid,
                "agency":       FeatureVariant.numbered_list,
                "media":        FeatureVariant.numbered_list,
                "architecture": FeatureVariant.numbered_list,
                "luxury":       FeatureVariant.alternating_blocks,
                "food":         FeatureVariant.alternating_blocks,
                "health":       FeatureVariant.alternating_blocks,
                "eco":          FeatureVariant.alternating_blocks,
                "gaming":       FeatureVariant.showcase_grid,
                "sports":       FeatureVariant.showcase_grid,
                "fitness":      FeatureVariant.showcase_grid,
            }
            variant_fn = FEATURE_MAP.get(self.industry, FeatureVariant.cards_grid)
            return variant_fn(self.theme, self.data.get('features', []), self.industry)
        except Exception as e:
            logger.error(f"Error rendering features: {e}")
            return f"<section id='features' class='{self.theme.get('bg_alt')} py-20'><h2 class='text-center text-4xl font-bold'>Features</h2></section>"

    def render_pricing(self) -> str:
        """Select pricing variant based on industry."""
        try:
            PRICING_MAP = {
                "finance":   PricingVariant.comparison_table,
                "saas":      PricingVariant.comparison_table,
                "ai":        PricingVariant.comparison_table,
                "food":      PricingVariant.two_option_split,
                "fitness":   PricingVariant.two_option_split,
                "luxury":    PricingVariant.two_option_split,
            }
            variant_fn = PRICING_MAP.get(self.industry, PricingVariant.tiered_cards)
            return variant_fn(self.theme, self.data.get('pricing', []))
        except Exception as e:
            logger.error(f"Error rendering pricing: {e}")
            return f"<section id='pricing' class='{self.theme.get('bg_alt')} py-20'><h2 class='text-center text-4xl font-bold'>Pricing</h2></section>"

    def render_testimonials(self) -> str:
        """Client testimonials with glassmorphism cards."""
        try:
            testimonials = self.data.get('testimonials', [])
            if not testimonials:
                return ""

            testimonial_cards = "".join([f"""
            <div class="{self.theme.get('glass')} {self.theme.get('card_border')} p-10 rounded-2xl {HOVER_LIFT} flex flex-col gap-6">
                <div class="flex gap-1">
                    {''.join(['<span class="text-amber-400">★</span>'] * 5)}
                </div>
                <p class="{self.theme.get('text')} text-lg leading-relaxed">"{t.get('quote', '')}"</p>
                <div class="flex items-center gap-4 mt-auto pt-4 border-t {self.theme.get('card_border')}">
                    <div class="w-10 h-10 rounded-full bg-gradient-to-br {self.theme.get('grad')} flex items-center justify-center text-white font-bold text-sm flex-shrink-0">
                        {t.get('name', 'C')[0].upper()}
                    </div>
                    <div>
                        <p class="{self.theme.get('text')} font-bold text-sm">{t.get('name', 'Client')}</p>
                        <p class="{self.theme.get('text_light')} text-xs">{t.get('company', 'Company')}</p>
                    </div>
                </div>
            </div>""" for t in testimonials])

            return f"""
            <section id="testimonials" class="{self.theme.get('bg_alt')} {PADDING_SECTION}">
                <div class="container mx-auto {PADDING_CONTAINER}">
                    <h2 class="{HEADING_SECTION} {self.theme.get('text')} text-center mb-4">What People Say</h2>
                    <p class="text-xl {self.theme.get('text_muted')} text-center mb-16">Real results from real customers.</p>
                    <div class="grid md:grid-cols-2 gap-8 max-w-4xl mx-auto">
                        {testimonial_cards}
                    </div>
                </div>
            </section>"""
        except Exception as e:
            logger.error(f"Error rendering testimonials: {e}")
            return ""

    def render_faq(self) -> str:
        """FAQ section with clean accordion-style cards."""
        try:
            faqs = self.data.get('faq', [])
            if not faqs:
                return ""

            faq_items = "".join([f"""
            <div class="{self.theme.get('glass')} {self.theme.get('card_border')} p-8 rounded-2xl {HOVER_GLOW} group cursor-pointer">
                <div class="flex items-start justify-between gap-4">
                    <h3 class="text-lg font-bold {self.theme.get('text')} leading-snug">{faq.get('q', '')}</h3>
                    <span class="{self.theme.get('text_light')} text-xl font-light flex-shrink-0">+</span>
                </div>
                <p class="{self.theme.get('text_muted')} leading-relaxed mt-4 text-sm">{faq.get('a', '')}</p>
            </div>""" for faq in faqs])

            return f"""
            <section id="faq" class="{self.theme.get('bg')} {PADDING_SECTION}">
                <div class="container mx-auto {PADDING_CONTAINER}">
                    <div class="max-w-3xl mx-auto">
                        <h2 class="{HEADING_SECTION} {self.theme.get('text')} text-center mb-4">Common Questions</h2>
                        <p class="text-xl {self.theme.get('text_muted')} text-center mb-16">Everything you need to know before you start.</p>
                        <div class="space-y-4">
                            {faq_items}
                        </div>
                    </div>
                </div>
            </section>"""
        except Exception as e:
            logger.error(f"Error rendering FAQ: {e}")
            return ""

    def render_trust_cloud(self) -> str:
        """Social proof / logo cloud."""
        try:
            brand_names = ["TechCorp", "Nexus Group", "Atlas Co.", "Vertex Inc.", "Luminary"]
            brands_html = "".join([f'<span class="{self.theme.get("text_muted")} font-bold text-sm tracking-wide opacity-50 hover:opacity-80 transition">✦ {b}</span>' for b in brand_names])
            return f"""
            <section class="{self.theme.get('bg_alt')} py-16 border-t border-b {self.theme.get('card_border')}">
                <div class="container mx-auto {PADDING_CONTAINER}">
                    <p class="{self.theme.get('text_light')} text-xs text-center mb-8 uppercase tracking-[0.3em]">Trusted by innovative companies worldwide</p>
                    <div class="flex flex-wrap justify-center gap-8 md:gap-16">
                        {brands_html}
                    </div>
                </div>
            </section>"""
        except Exception as e:
            logger.error(f"Error rendering trust cloud: {e}")
            return ""

    def render_cta_section(self) -> str:
        """Final CTA before footer."""
        try:
            cta_text = self.data.get('cta_text', f'Ready to experience {self.name}?')
            return f"""
            <section id="contact" class="relative {self.theme.get('bg')} {PADDING_SECTION} overflow-hidden">
                <div class="absolute inset-0 pointer-events-none overflow-hidden">
                    <div class="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-gradient-to-r {self.theme.get('grad')} rounded-full blur-3xl opacity-10"></div>
                </div>
                <div class="container mx-auto {PADDING_CONTAINER} relative z-10 text-center">
                    <h2 class="{HEADING_SECTION} {self.theme.get('text')} mb-6 max-w-3xl mx-auto">{cta_text}</h2>
                    <p class="text-xl {self.theme.get('text_muted')} mb-12 max-w-xl mx-auto">Join the businesses already winning with {self.name}.</p>
                    <div class="flex flex-col sm:flex-row gap-4 justify-center">
                        <a href="mailto:info@example.com" class="px-10 py-6 bg-gradient-to-r {self.theme.get('btn_grad')} text-white rounded-full font-bold text-lg {HOVER_LIFT} shadow-xl">
                            {self.data.get('hero', {}).get('cta', 'Get Started')}
                        </a>
                        <a href="tel:+1234567890" class="px-10 py-6 {self.theme.get('glass')} {self.theme.get('card_border')} {self.theme.get('text')} rounded-full font-bold {HOVER_GLOW}">
                            Book a Call →
                        </a>
                    </div>
                </div>
            </section>"""
        except Exception as e:
            logger.error(f"Error rendering CTA: {e}")
            return f"<section id='contact' class='{self.theme.get('bg')} py-20 text-center'><h2 class='text-4xl font-bold'>Get Started</h2></section>"

    def render_footer(self) -> str:
        """Professional multi-column footer."""
        try:
            nav_links = "".join([
                f'<li><a href="#{link.lower().replace(" ", "").replace("/", "")}" class="{self.theme.get("text_muted")} hover:{self.theme.get("text", "text-gray-900").replace("text-", "")} text-sm transition">{link}</a></li>'
                for link in (self.data.get('nav', []) or [])
            ])

            return f"""
            <footer class="{self.theme.get('bg_alt')} border-t {self.theme.get('card_border')} py-16">
                <div class="container mx-auto {PADDING_CONTAINER}">
                    <div class="grid md:grid-cols-4 gap-12 mb-12">
                        <div class="md:col-span-1">
                            <h3 class="font-black text-xl {self.theme.get('text')} mb-4 tracking-tight">{self.name}</h3>
                            <p class="{self.theme.get('text_muted')} text-sm leading-relaxed">Premium solutions for businesses that demand the best.</p>
                        </div>
                        <div>
                            <h4 class="font-bold text-sm uppercase tracking-widest {self.theme.get('text')} mb-5 opacity-60">Product</h4>
                            <ul class="space-y-3">{nav_links}</ul>
                        </div>
                        <div>
                            <h4 class="font-bold text-sm uppercase tracking-widest {self.theme.get('text')} mb-5 opacity-60">Company</h4>
                            <ul class="space-y-3 text-sm">
                                <li><a href="#" class="{self.theme.get('text_muted')} hover:{self.theme.get('text', 'text-gray-900').replace('text-', '')} transition">About Us</a></li>
                                <li><a href="#" class="{self.theme.get('text_muted')} hover:{self.theme.get('text', 'text-gray-900').replace('text-', '')} transition">Blog</a></li>
                                <li><a href="#" class="{self.theme.get('text_muted')} hover:{self.theme.get('text', 'text-gray-900').replace('text-', '')} transition">Careers</a></li>
                            </ul>
                        </div>
                        <div>
                            <h4 class="font-bold text-sm uppercase tracking-widest {self.theme.get('text')} mb-5 opacity-60">Legal</h4>
                            <ul class="space-y-3 text-sm">
                                <li><a href="#" class="{self.theme.get('text_muted')} transition">Privacy Policy</a></li>
                                <li><a href="#" class="{self.theme.get('text_muted')} transition">Terms of Service</a></li>
                                <li><a href="mailto:hello@example.com" class="{self.theme.get('text_muted')} transition">hello@example.com</a></li>
                            </ul>
                        </div>
                    </div>
                    <div class="border-t {self.theme.get('card_border')} pt-8 flex flex-col md:flex-row justify-between items-center gap-4">
                        <p class="{self.theme.get('text_light')} text-sm">&copy; 2026 {self.name}. All rights reserved.</p>
                        <p class="{self.theme.get('text_light')} text-xs font-mono">v{self.version} · {self.theme.get('id')} · {self.industry}</p>
                    </div>
                </div>
            </footer>"""
        except Exception as e:
            logger.error(f"Error rendering footer: {e}")
            return f"<footer class='{self.theme.get('bg_alt')} py-8'><div class='container mx-auto px-6 text-center text-sm'>&copy; 2026 {self.name}.</div></footer>"

    def build(self) -> Dict[str, Any]:
        """Assemble complete website with all sections."""
        try:
            self.data = self.get_ai_payload()

            sections = [
                self.render_nav(),
                self.render_hero(),
                self.render_trust_cloud(),
                self.render_features(),
                self.render_pricing(),
                self.render_testimonials(),
                self.render_faq(),
                self.render_cta_section(),
                self.render_footer(),
            ]

            extra_css = self.theme.get("extra_css", "")

            html = f"""<!DOCTYPE html>
<html lang="en" style="scroll-behavior: smooth;">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{self.name} — Official Site</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="{self.font_url}" rel="stylesheet">
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        * {{ font-family: {self.font_family}; }}
        
        {extra_css}
        
        @keyframes fadeInUp {{
            from {{ opacity: 0; transform: translateY(24px); }}
            to   {{ opacity: 1; transform: translateY(0); }}
        }}
        @keyframes fadeInLeft {{
            from {{ opacity: 0; transform: translateX(-24px); }}
            to   {{ opacity: 1; transform: translateX(0); }}
        }}
        
        #hero {{ animation: fadeInUp 0.9s ease-out forwards; }}
        #features {{ animation: fadeInUp 0.9s 0.15s ease-out both; }}
        #pricing  {{ animation: fadeInUp 0.9s 0.3s  ease-out both; }}
        
        html {{ scroll-behavior: smooth; }}
        
        ::-webkit-scrollbar {{ width: 6px; }}
        ::-webkit-scrollbar-track {{ background: transparent; }}
        ::-webkit-scrollbar-thumb {{ background: linear-gradient(to bottom, {self.theme.get('primary_hex', '#6366f1')}, transparent); border-radius: 999px; }}
    </style>
</head>
<body class="{self.theme.get('bg')} {self.theme.get('text')} antialiased">
    {"".join(sections)}
</body>
</html>"""

            logger.info(f"Website built successfully for {self.name} [{self.industry}/{self.theme.get('id')}]")
            return {
                "html": html,
                "metadata": {
                    "business_name": self.name,
                    "industry": self.industry,
                    "theme": self.theme.get('id', 'unknown'),
                    "font": self.theme.get("font", "geometric"),
                    "version": self.version,
                    "status": "success",
                }
            }
        except Exception as e:
            logger.error(f"Error building website: {e}\n{traceback.format_exc()}")
            return {
                "html": f"<html><body><h1>Build Error</h1><pre>{str(e)}</pre></body></html>",
                "metadata": {
                    "business_name": self.name,
                    "industry": self.industry,
                    "theme": self.theme.get('id', 'unknown'),
                    "version": self.version,
                    "status": "error",
                    "error": str(e),
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
        version:  API version for future compatibility
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

        logger.info(f"Website generation completed for {business_name} — theme: {result['metadata'].get('theme')}, industry: {result['metadata'].get('industry')}")
        return result
    except Exception as e:
        logger.error(f"Error in generate_ai_plan: {e}\n{traceback.format_exc()}")
        return {
            "html": f"<html><body><h1>Error</h1><p>{str(e)}</p></body></html>",
            "metadata": {
                "business_name": ai_input.get("business_name", "Unknown"),
                "status": "error",
                "error": str(e),
            }
        }


def rewrite_content(original_text: str, tone: str = "professional", business_context: str = "") -> List[str]:
    """AI-powered content rewriting with fallback."""
    try:
        if not AI_AVAILABLE:
            return [original_text] * 3

        system = "You are a world-class copywriter. Output ONLY valid JSON array."
        user = (
            f"Rewrite '{original_text}' exactly 3 times in {tone} tone for context: {business_context}. "
            f"Output JSON array: [\"version1\", \"version2\", \"version3\"]"
        )

        res = chat_completion(system=system, user=user, temperature=0.8)
        result = json.loads(res.strip().replace("```json", "").replace("```", ""))
        return result if isinstance(result, list) and len(result) >= 3 else [original_text] * 3
    except Exception as e:
        logger.warning(f"Error rewriting content: {e}")
        return [original_text] * 3


def get_design_tokens() -> Dict[str, Any]:
    """Export design tokens for external use."""
    return {
        "themes": THEMES,
        "spacing": {"section": PADDING_SECTION, "container": PADDING_CONTAINER},
        "typography": {
            "hero": HEADING_HERO,
            "section": HEADING_SECTION,
            "feature": HEADING_FEATURE,
            "card": HEADING_CARD,
            "fonts": FONT_STACKS,
        },
        "animations": {
            "hover_lift":  HOVER_LIFT,
            "hover_glow":  HOVER_GLOW,
            "hover_scale": HOVER_SCALE,
            "hover_slide": HOVER_SLIDE,
        },
        "glass": {"dark": GLASS_DARK, "light": GLASS_LIGHT},
        "industry_theme_map": INDUSTRY_THEME_MAP,
        "industry_keywords": INDUSTRY_KEYWORDS,
    }