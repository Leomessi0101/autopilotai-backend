import random
import json
import hashlib
import logging
import traceback
from typing import Dict, Any, List, Optional, Callable
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
            "tagline": "Built for the bold.",
            "brand_voice": "professional",
            "features": [
                {"title": "Speed & Reliability", "description": "Industry-leading uptime with blazing performance.", "icon": "⚡"},
                {"title": "Seamless Integration", "description": "Connects with your existing stack in minutes.", "icon": "🔗"},
                {"title": "Powerful Analytics", "description": "Real-time insights to drive smarter decisions.", "icon": "📊"},
            ],
            "pricing": [
                {"name": "Starter", "price": "$29", "description": "Perfect for individuals.", "features": ["5 projects", "1GB storage", "Email support", "API access", "Monthly reports"], "featured": False},
                {"name": "Pro", "price": "$99", "description": "For growing teams.", "features": ["Unlimited projects", "50GB storage", "Priority support", "Advanced analytics", "Custom integrations"], "featured": True},
                {"name": "Enterprise", "price": "Custom", "description": "For large organisations.", "features": ["Everything in Pro", "Dedicated manager", "SLA guarantee", "Custom contracts", "On-premise option"], "featured": False},
            ],
            "testimonials": [
                {"name": "Sarah Chen", "role": "CEO", "company": "NexusCorp", "quote": "Completely transformed our workflow. We saved 20 hours per week."},
                {"name": "Marcus Webb", "role": "CTO", "company": "LaunchpadAI", "quote": "The best platform investment we've made. ROI was visible within weeks."},
            ],
            "faq": [
                {"q": "How quickly can I get started?", "a": "You'll be fully set up in under 10 minutes with our guided onboarding."},
                {"q": "What support do you provide?", "a": "All plans include email support. Pro and Enterprise get 24/7 priority access."},
                {"q": "Is there a free trial?", "a": "Yes — a full 14-day free trial, no credit card required."},
            ],
            "cta_text": "Ready to transform your business?",
            "unsplash_keywords": ["technology", "business", "modern", "team", "workspace"],
        })


# ============================================================================
# DESIGN SYSTEM
# ============================================================================

GLASS_DARK  = "backdrop-blur-2xl bg-gradient-to-br from-white/8 to-white/2 border border-white/12 shadow-2xl"
GLASS_LIGHT = "backdrop-blur-2xl bg-gradient-to-br from-white/80 to-gray-50/60 border border-gray-200/70 shadow-lg"

HOVER_LIFT  = "transition-all duration-500 ease-[cubic-bezier(0.34,1.56,0.64,1)] hover:-translate-y-2 hover:shadow-2xl"
HOVER_GLOW  = "transition-all duration-400 ease-out hover:shadow-lg hover:brightness-110"
HOVER_SCALE = "transition-transform duration-400 ease-out hover:scale-[1.03]"

HEADING_HERO     = "text-6xl md:text-7xl lg:text-8xl font-black tracking-tighter leading-[1.05]"
HEADING_HERO_ALT = "text-5xl md:text-6xl lg:text-7xl font-extrabold tracking-tight leading-[1.1]"
HEADING_SECTION  = "text-4xl md:text-5xl lg:text-6xl font-black tracking-tight leading-[1.15]"
HEADING_FEATURE  = "text-2xl md:text-3xl font-bold tracking-tight"
HEADING_CARD     = "text-xl font-bold tracking-tight"

PADDING_SECTION   = "py-28 md:py-36"
PADDING_SECTION_SM = "py-16 md:py-24"
PADDING_CONTAINER = "px-5 md:px-8 lg:px-12"

# ============================================================================
# 8 DISTINCT THEMES
# ============================================================================

THEMES = {
    "pro_light": {
        "id": "pro_light", "mode": "light",
        "bg": "bg-white", "bg_alt": "bg-slate-50",
        "text": "text-gray-950", "text_muted": "text-gray-600", "text_light": "text-gray-400",
        "primary": "blue", "primary_hex": "#2563eb",
        "grad": "from-blue-600 via-blue-500 to-cyan-400",
        "grad_subtle": "from-blue-50 to-cyan-50",
        "glass": GLASS_LIGHT, "accent": "cyan",
        "border": "border-gray-200",
        "nav_bg": "bg-white/90 border-b border-gray-100",
        "badge_style": "bg-blue-50 text-blue-700 border border-blue-200",
        "stat_color": "text-blue-600",
        "fonts": "'Plus Jakarta Sans', 'Inter', sans-serif",
        "font_url": "https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;600;700;800;900&display=swap",
    },
    "luxury_dark": {
        "id": "luxury_dark", "mode": "dark",
        "bg": "bg-[#0a0a0f]", "bg_alt": "bg-[#0f0f18]",
        "text": "text-white", "text_muted": "text-gray-300", "text_light": "text-gray-600",
        "primary": "violet", "primary_hex": "#7c3aed",
        "grad": "from-violet-600 via-purple-500 to-fuchsia-500",
        "grad_subtle": "from-violet-950/50 to-fuchsia-950/30",
        "glass": GLASS_DARK, "accent": "fuchsia",
        "border": "border-white/10",
        "nav_bg": "bg-black/70 border-b border-white/8",
        "badge_style": "bg-violet-950/60 text-violet-300 border border-violet-500/30",
        "stat_color": "text-fuchsia-400",
        "fonts": "'Syne', serif",
        "font_url": "https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&display=swap",
    },
    "clean_emerald": {
        "id": "clean_emerald", "mode": "light",
        "bg": "bg-[#f8fffe]", "bg_alt": "bg-white",
        "text": "text-slate-900", "text_muted": "text-slate-600", "text_light": "text-slate-400",
        "primary": "emerald", "primary_hex": "#059669",
        "grad": "from-emerald-500 via-teal-500 to-cyan-500",
        "grad_subtle": "from-emerald-50 to-teal-50",
        "glass": GLASS_LIGHT, "accent": "teal",
        "border": "border-emerald-100",
        "nav_bg": "bg-white/95 border-b border-emerald-100",
        "badge_style": "bg-emerald-50 text-emerald-700 border border-emerald-200",
        "stat_color": "text-emerald-600",
        "fonts": "'DM Sans', sans-serif",
        "font_url": "https://fonts.googleapis.com/css2?family=DM+Sans:opsz,wght@9..40,400;9..40,500;9..40,700;9..40,800&display=swap",
    },
    "tech_midnight": {
        "id": "tech_midnight", "mode": "dark",
        "bg": "bg-gray-950", "bg_alt": "bg-gray-900",
        "text": "text-white", "text_muted": "text-gray-400", "text_light": "text-gray-600",
        "primary": "cyan", "primary_hex": "#06b6d4",
        "grad": "from-cyan-500 via-blue-500 to-indigo-600",
        "grad_subtle": "from-cyan-950/40 to-indigo-950/40",
        "glass": GLASS_DARK, "accent": "blue",
        "border": "border-white/8",
        "nav_bg": "bg-gray-950/80 border-b border-white/8",
        "badge_style": "bg-cyan-950/50 text-cyan-400 border border-cyan-500/25",
        "stat_color": "text-cyan-400",
        "fonts": "'Space Grotesk', monospace",
        "font_url": "https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&display=swap",
    },
    "warm_amber": {
        "id": "warm_amber", "mode": "light",
        "bg": "bg-[#fffbf2]", "bg_alt": "bg-amber-50",
        "text": "text-amber-950", "text_muted": "text-amber-800", "text_light": "text-amber-500",
        "primary": "amber", "primary_hex": "#d97706",
        "grad": "from-amber-500 via-orange-500 to-rose-500",
        "grad_subtle": "from-amber-50 to-orange-50",
        "glass": GLASS_LIGHT, "accent": "orange",
        "border": "border-amber-200",
        "nav_bg": "bg-amber-50/90 border-b border-amber-200",
        "badge_style": "bg-amber-100 text-amber-800 border border-amber-300",
        "stat_color": "text-orange-600",
        "fonts": "'Fraunces', serif",
        "font_url": "https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,700;9..144,900&display=swap",
    },
    "midnight_rose": {
        "id": "midnight_rose", "mode": "dark",
        "bg": "bg-[#0d0508]", "bg_alt": "bg-[#130a0e]",
        "text": "text-rose-50", "text_muted": "text-rose-200/80", "text_light": "text-rose-400/60",
        "primary": "rose", "primary_hex": "#e11d48",
        "grad": "from-rose-500 via-pink-600 to-fuchsia-600",
        "grad_subtle": "from-rose-950/40 to-fuchsia-950/30",
        "glass": GLASS_DARK, "accent": "pink",
        "border": "border-rose-900/40",
        "nav_bg": "bg-[#0d0508]/80 border-b border-rose-900/30",
        "badge_style": "bg-rose-950/60 text-rose-300 border border-rose-500/20",
        "stat_color": "text-rose-400",
        "fonts": "'Cormorant Garamond', serif",
        "font_url": "https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@300;400;600;700&display=swap",
    },
    "slate_corporate": {
        "id": "slate_corporate", "mode": "light",
        "bg": "bg-slate-50", "bg_alt": "bg-white",
        "text": "text-slate-900", "text_muted": "text-slate-500", "text_light": "text-slate-400",
        "primary": "indigo", "primary_hex": "#4338ca",
        "grad": "from-indigo-600 via-indigo-500 to-blue-500",
        "grad_subtle": "from-indigo-50 to-blue-50",
        "glass": GLASS_LIGHT, "accent": "blue",
        "border": "border-slate-200",
        "nav_bg": "bg-white border-b border-slate-200",
        "badge_style": "bg-indigo-50 text-indigo-700 border border-indigo-200",
        "stat_color": "text-indigo-600",
        "fonts": "'IBM Plex Sans', sans-serif",
        "font_url": "https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600;700&display=swap",
    },
    "forest_green": {
        "id": "forest_green", "mode": "dark",
        "bg": "bg-[#050e08]", "bg_alt": "bg-[#081510]",
        "text": "text-green-50", "text_muted": "text-green-200/80", "text_light": "text-green-400/50",
        "primary": "green", "primary_hex": "#16a34a",
        "grad": "from-green-500 via-emerald-500 to-teal-500",
        "grad_subtle": "from-green-950/50 to-teal-950/30",
        "glass": GLASS_DARK, "accent": "teal",
        "border": "border-green-900/40",
        "nav_bg": "bg-[#050e08]/80 border-b border-green-900/30",
        "badge_style": "bg-green-950/60 text-green-300 border border-green-500/25",
        "stat_color": "text-green-400",
        "fonts": "'Cabin', sans-serif",
        "font_url": "https://fonts.googleapis.com/css2?family=Cabin:wght@400;600;700&display=swap",
    },
}


# ============================================================================
# DYNAMIC UNSPLASH IMAGE BUILDER
# ============================================================================

UNSPLASH_PHOTO_POOLS: Dict[str, List[str]] = {
    "technology":   ["photo-1518770660439-4636190af475", "photo-1461749280684-dccba630e2f6", "photo-1550751827-4bd374c3f58b"],
    "business":     ["photo-1507003211169-0a1dd7228f2d", "photo-1554224155-6726b3ff858f", "photo-1521791136064-7986c2920216"],
    "team":         ["photo-1522071820081-009f0129c71c", "photo-1517048676732-d65bc937f952", "photo-1600880292203-757bb62b4baf"],
    "workspace":    ["photo-1497366216548-37526070297c", "photo-1497366754035-f200968a6e72", "photo-1524758631624-e2822e304c36"],
    "startup":      ["photo-1559136555-9303baea8ebd", "photo-1531297484001-80022131f5a1", "photo-1556761175-4b46a572b786"],
    "food":         ["photo-1504674900247-0877df9cc836", "photo-1512621776951-a57141f2eefd", "photo-1567620905732-2d1ec7ab7445"],
    "restaurant":   ["photo-1414235077428-338989a2e8c0", "photo-1555396273-367ea4eb4db5", "photo-1517248135467-4c7edcad34c4"],
    "health":       ["photo-1576091160550-2173dba999ef", "photo-1559757148-5c350d0d3c56", "photo-1535914254981-b5012eebbd15"],
    "fitness":      ["photo-1534438327276-14e5300c3a48", "photo-1571019613454-1cb2f99b2d8b", "photo-1517836357463-d25dfeac3438"],
    "nature":       ["photo-1441974231531-c6227db76b6e", "photo-1506905925346-21bda4d32df4", "photo-1469474968028-56623f02e42e"],
    "fashion":      ["photo-1558769132-cb1aea458c5e", "photo-1490481651871-ab68de25d43d", "photo-1483985988355-763728e1935b"],
    "luxury":       ["photo-1518546305927-5a555bb7020d", "photo-1571266752045-a0f5cfb5efcb", "photo-1602143407151-7111542de6e8"],
    "finance":      ["photo-1611974789855-9c2a0a7236a3", "photo-1563986768609-322da13575f3", "photo-1468254095679-bbcba94a7066"],
    "education":    ["photo-1503676260728-1c00da094a0b", "photo-1456513080510-7bf3a84b82f8", "photo-1516979187457-637abb4f9353"],
    "ai":           ["photo-1677442135703-1787eea5ce01", "photo-1620712943543-bcc4688e7485", "photo-1555255707-c07966088b7b"],
    "minimal":      ["photo-1497215728101-856f4ea42174", "photo-1519389950473-47ba0277781c", "photo-1462826303086-329426d1aef5"],
    "construction": ["photo-1504307651254-35680f356dfd", "photo-1541888946425-d81bb19240f5", "photo-1590674899484-d5640e854abe",
                     "photo-1581578731548-c64695cc6952", "photo-1565117623394-5f93fd4c7a06"],
    "legal":        ["photo-1589578527966-fdac0f44566c", "photo-1436450412740-6b988f486c6b", "photo-1505664194779-8beaceb5c7c7"],
    "logistics":    ["photo-1504493188-45c49f65c6ba", "photo-1586528116311-ad8dd3c8310d", "photo-1601584115197-04ecc0da31d7"],
    "automotive":   ["photo-1492144534655-ae79c964c9d7", "photo-1503376780353-7e6692767b70", "photo-1544636331-e26879cd4d9b"],
    "events":       ["photo-1540575467063-178a50c2df87", "photo-1511795409834-ef04bbd61622", "photo-1464366400600-7168b8af9bc3"],
    "default":      ["photo-1552664730-d307ca884978", "photo-1460925895917-afdab827c52f", "photo-1556742049-0cfed4f6a45d"],
}

def _get_unsplash_url(keywords: List[str], width: int = 800, index: int = 0) -> str:
    pool: List[str] = []
    for kw in (keywords or []):
        kw_lower = kw.lower().strip()
        for topic, photos in UNSPLASH_PHOTO_POOLS.items():
            if topic in kw_lower or kw_lower in topic:
                pool.extend(photos)
    if not pool:
        pool = UNSPLASH_PHOTO_POOLS["default"]
    seen: set = set()
    unique_pool = [p for p in pool if not (p in seen or seen.add(p))]
    chosen = unique_pool[index % len(unique_pool)]
    return f"https://images.unsplash.com/{chosen}?w={width}&auto=format&fit=crop&q=80"

def _get_img_set(keywords: List[str], count: int = 6) -> List[str]:
    return [_get_unsplash_url(keywords, width=800, index=i) for i in range(count)]


# ============================================================================
# INDUSTRY DETECTION
# ============================================================================

INDUSTRY_KEYWORD_MAP: Dict[str, List[str]] = {
    "saas":         ["software", "app", "platform", "cloud", "api", "saas", "dashboard", "workflow", "automation", "crm", "erp"],
    "ai":           ["ai", "artificial intelligence", "machine learning", "ml", "neural", "algorithm", "gpt", "llm", "data science"],
    "ecommerce":    ["shop", "store", "ecommerce", "e-commerce", "sell", "product", "cart", "marketplace", "dropship", "retail"],
    "health":       ["health", "medical", "wellness", "fitness", "clinic", "doctor", "hospital", "therapy", "mental health", "nutrition"],
    "finance":      ["finance", "banking", "investment", "crypto", "payment", "fintech", "trading", "insurance", "wealth", "accounting", "tax"],
    "agency":       ["agency", "design", "creative", "marketing", "brand", "advertising", "studio", "production", "media"],
    "education":    ["education", "course", "learn", "training", "school", "university", "tutoring", "edtech", "bootcamp"],
    "luxury":       ["luxury", "premium", "high-end", "exclusive", "bespoke", "couture", "prestige", "elite"],
    "restaurant":   ["restaurant", "food", "cafe", "bakery", "catering", "cuisine", "dining", "menu", "chef", "bar", "bistro"],
    "beauty":       ["beauty", "salon", "spa", "skincare", "cosmetic", "makeup", "aesthetics", "bridal", "hair", "nail"],
    "real_estate":  ["real estate", "property", "realty", "housing", "apartment", "mortgage", "agent", "broker"],
    "travel":       ["travel", "hotel", "tour", "booking", "airbnb", "vacation", "resort", "hospitality"],
    "startup":      ["startup", "founder", "seed", "venture", "mvp", "launch", "pitch", "growth hacking", "scale"],
    "developer":    ["developer", "engineer", "code", "open source", "github", "devtools", "ide", "terminal", "cli"],
    "nature":       ["organic", "eco", "green", "sustainable", "farm", "agriculture", "environment", "garden"],
    # Trades & physical services
    "construction": ["construction", "contractor", "builder", "building", "renovation", "remodel", "plumbing", "electrical",
                     "roofing", "flooring", "masonry", "carpentry", "landscaping", "painting", "hvac", "handyman",
                     "general contractor", "home improvement", "commercial build", "civil engineering", "infrastructure",
                     "excavation", "concrete", "drywall", "framing", "welding", "trades"],
    "legal":        ["law", "lawyer", "attorney", "legal", "firm", "counsel", "litigation", "contract", "court", "compliance",
                     "paralegal", "notary", "solicitor", "barrister", "law office"],
    "logistics":    ["logistics", "shipping", "freight", "delivery", "supply chain", "warehouse", "trucking", "transport",
                     "courier", "fulfillment", "distribution", "fleet"],
    "automotive":   ["auto", "car", "vehicle", "mechanic", "garage", "dealership", "repair", "tire", "bodywork", "detailing"],
    "nonprofit":    ["nonprofit", "charity", "foundation", "ngo", "volunteer", "donation", "cause", "community", "social impact"],
    "events":       ["event", "wedding", "conference", "venue", "catering", "photography", "dj", "entertainment", "party", "corporate event"],
}

def detect_industry(prompt: str) -> str:
    prompt_lower = (prompt or "").lower()
    scores = {ind: 0 for ind in INDUSTRY_KEYWORD_MAP}
    for industry, keywords in INDUSTRY_KEYWORD_MAP.items():
        for kw in keywords:
            if kw in prompt_lower:
                scores[industry] += 1
    best = max(scores, key=lambda k: scores[k])
    return best if scores[best] > 0 else "saas"


# ============================================================================
# THEME SELECTION
# ============================================================================

INDUSTRY_THEME_MAP: Dict[str, str] = {
    "saas":         "pro_light",
    "ai":           "tech_midnight",
    "ecommerce":    "warm_amber",
    "health":       "clean_emerald",
    "finance":      "pro_light",          # professional blue — distinct from slate_corporate
    "agency":       "luxury_dark",
    "education":    "clean_emerald",
    "luxury":       "luxury_dark",
    "restaurant":   "warm_amber",
    "beauty":       "midnight_rose",
    "real_estate":  "slate_corporate",
    "travel":       "pro_light",
    "startup":      "tech_midnight",
    "developer":    "tech_midnight",
    "nature":       "forest_green",
    # Trades & physical services — always professional/corporate
    "construction": "slate_corporate",    # serious grey — distinct from finance blue
    "legal":        "slate_corporate",
    "logistics":    "slate_corporate",
    "automotive":   "slate_corporate",
    "nonprofit":    "clean_emerald",
    "events":       "warm_amber",
}

# Per-industry alternate themes (for same-industry diversity)
INDUSTRY_ALTERNATES: Dict[str, List[str]] = {
    "saas":         ["pro_light", "tech_midnight"],
    "agency":       ["luxury_dark", "midnight_rose"],
    "health":       ["clean_emerald", "pro_light"],
    "finance":      ["slate_corporate", "pro_light"],
    "startup":      ["tech_midnight", "luxury_dark"],
    "ecommerce":    ["warm_amber", "clean_emerald"],
    "construction": ["slate_corporate"],   # always professional, no alternates
    "legal":        ["slate_corporate"],
    "logistics":    ["slate_corporate", "pro_light"],
}

def select_theme(industry: str, seed: str = "") -> Dict:
    if seed and industry in INDUSTRY_ALTERNATES:
        alts = INDUSTRY_ALTERNATES[industry]
        idx = int(hashlib.md5(seed.encode()).hexdigest(), 16) % len(alts)
        theme_id = alts[idx]
    else:
        theme_id = INDUSTRY_THEME_MAP.get(industry, "pro_light")
    return THEMES.get(theme_id, THEMES["pro_light"])


# ============================================================================
# BUSINESS NAME EXTRACTION
# ============================================================================

# Phrases that signal "the name follows" vs "a description follows"
_NAME_PREFIXES = [
    "my company is called ", "my company is ", "my business is called ", "my business is ",
    "the company is called ", "the company is ", "company name is ", "business name is ",
    "called ", "named ", "name is ", "it's called ", "it is called ",
    "we are ", "we're ", "our company ", "our business ",
    "i have a company called ", "i have a business called ",
    "i own ", "i run ", "i started ",
]

_DESCRIPTION_STARTERS = [
    "we ", "our ", "a ", "an ", "the ", "i have", "i own", "i run",
    "this is", "it's a", "it is a",
]

def extract_business_name(raw_name: str, prompt: str) -> tuple[str, str]:
    """
    Extracts business name from EITHER the business_name field OR the prompt text.
    
    Handles:
    - business_name="", prompt="The company name is BuildRight. We do roofing."
    - business_name="i have a construction company", prompt="..."
    - business_name="BuildRight LLC", prompt="..."
    
    Returns (clean_name, augmented_prompt)
    """
    raw = (raw_name or "").strip()
    prompt_text = (prompt or "").strip()
    
    # STEP 1: Check if prompt contains explicit name declaration
    prompt_lower = prompt_text.lower()
    name_indicators = [
        "the company name is ", "the business name is ", "our company name is ",
        "company name: ", "business name: ", "we're called ", "we are called ",
        "it's called ", "it is called ", "my company is called ", "my business is called ",
    ]
    
    for indicator in name_indicators:
        if indicator in prompt_lower:
            idx = prompt_lower.index(indicator)
            after = prompt_text[idx + len(indicator):].strip()
            # Extract name until first terminator
            name_end = len(after)
            for sep in [".", ",", ";", " -", " and we", " that ", " which "]:
                pos = after.find(sep)
                if pos > 0 and pos < name_end:
                    name_end = pos
            name_from_prompt = after[:name_end].strip()
            # Remove the declaration from prompt
            before = prompt_text[:idx].strip()
            remainder = prompt_text[idx + len(indicator) + name_end:].strip(" .,;")
            cleaned_prompt = f"{before} {remainder}".strip()
            logger.info(f"Extracted name from prompt: '{name_from_prompt}'")
            return name_from_prompt, cleaned_prompt
    
    # STEP 2: If no prompt name, parse business_name field
    if not raw:
        return "", prompt_text  # Will derive later
    
    raw_lower = raw.lower()
    
    # Description starters → no explicit name
    for starter in _DESCRIPTION_STARTERS:
        if raw_lower.startswith(starter):
            combined = f"{raw}. {prompt_text}".strip(" .")
            return "", combined
    
    # "called X" or "named X" prefixes
    for prefix in _NAME_PREFIXES:
        if raw_lower.startswith(prefix):
            remainder = raw[len(prefix):].strip()
            for sep in [" - ", " — ", ", ", ". "]:
                if sep in remainder:
                    parts = remainder.split(sep, 1)
                    return parts[0].strip(), f"{parts[1].strip()}. {prompt_text}".strip(" .")
            return remainder.strip(), prompt_text
    
    # Separators
    for sep in [" - ", " — ", ": ", ", we ", ". we "]:
        if sep in raw:
            parts = raw.split(sep, 1)
            return parts[0].strip(), f"{parts[1].strip()}. {prompt_text}".strip(" .")
    
    # Short clean name
    if len(raw.split()) <= 5:
        return raw, prompt_text
    
    # Long — split
    words = raw.split()
    name = " ".join(words[:3]).rstrip(".,!?")
    overflow = " ".join(words[3:])
    return name, f"{overflow}. {prompt_text}".strip(" .")


def derive_name_from_prompt(prompt: str, industry: str) -> str:
    """Last-resort: generate a plausible business name from the industry."""
    industry_defaults = {
        "construction": "BuildRight Group",
        "legal":        "Sterling Law",
        "finance":      "Apex Capital",
        "health":       "Vitalis Health",
        "restaurant":   "The Kitchen",
        "beauty":       "Lumière Studio",
        "ecommerce":    "The Shop",
        "education":    "Elevate Academy",
        "real_estate":  "Keystone Realty",
        "logistics":    "Swift Logistics",
        "automotive":   "AutoPro",
        "events":       "Premier Events",
        "nonprofit":    "Together Foundation",
        "nature":       "Green Root",
        "agency":       "Creative Studio",
        "travel":       "Voyage Co.",
    }
    return industry_defaults.get(industry, "My Business")


# ============================================================================
# HERO VARIANTS
# ============================================================================

class HeroVariant:

    @staticmethod
    def split_grid(theme: Dict, data: Dict, images: List[str]) -> str:
        img = images[0] if images else _get_unsplash_url(["business"])
        badge = data.get("tagline", "Premium Experience")
        try:
            return f"""
            <section id="hero" class="relative {theme['bg']} overflow-hidden pt-40 pb-28">
                <div class="absolute top-0 right-0 w-1/2 h-full pointer-events-none">
                    <div class="absolute inset-0 bg-gradient-to-l {theme['grad_subtle']} opacity-60"></div>
                </div>
                <div class="container mx-auto {PADDING_CONTAINER} relative z-10">
                    <div class="grid lg:grid-cols-2 gap-16 items-center">
                        <div class="space-y-8">
                            <span class="inline-flex items-center gap-2 px-4 py-2 rounded-full text-xs font-semibold uppercase tracking-widest {theme['badge_style']}">
                                <span class="w-1.5 h-1.5 rounded-full bg-current animate-pulse"></span>
                                {badge}
                            </span>
                            <h1 class="{HEADING_HERO} {theme['text']}">{data.get('hero', {}).get('h1', 'Premium Solution')}</h1>
                            <p class="text-lg md:text-xl {theme['text_muted']} leading-relaxed max-w-lg">{data.get('hero', {}).get('sub', 'Built for excellence')}</p>
                            <div class="flex flex-wrap gap-4 pt-2">
                                <a href="#contact" class="px-8 py-4 bg-gradient-to-r {theme['grad']} text-white rounded-xl font-bold {HOVER_LIFT} shadow-lg">
                                    {data.get('hero', {}).get('cta', 'Get Started')}
                                </a>
                                <a href="#features" class="{theme['glass']} {theme['text']} px-8 py-4 rounded-xl font-semibold border {theme['border']} {HOVER_GLOW}">
                                    See how it works →
                                </a>
                            </div>
                            <div class="flex items-center gap-3 pt-2">
                                <div class="flex -space-x-2">
                                    <div class="w-8 h-8 rounded-full bg-gradient-to-br {theme['grad']} border-2 border-white opacity-80"></div>
                                    <div class="w-8 h-8 rounded-full bg-gradient-to-br {theme['grad']} border-2 border-white opacity-80"></div>
                                    <div class="w-8 h-8 rounded-full bg-gradient-to-br {theme['grad']} border-2 border-white opacity-80"></div>
                                    <div class="w-8 h-8 rounded-full bg-gradient-to-br {theme['grad']} border-2 border-white opacity-80"></div>
                                </div>
                                <span class="text-sm {theme['text_muted']}">Join <span class="font-bold {theme['stat_color']}">2,400+</span> businesses already growing</span>
                            </div>
                        </div>
                        <div class="relative h-[420px] md:h-[520px]">
                            <div class="absolute -inset-4 bg-gradient-to-br {theme['grad']} opacity-15 blur-2xl rounded-3xl"></div>
                            <img src="{img}" alt="hero visual" class="relative z-10 w-full h-full object-cover rounded-2xl {HOVER_SCALE}" loading="eager" />
                        </div>
                    </div>
                </div>
            </section>"""
        except Exception as e:
            logger.error(f"split_grid hero error: {e}")
            return f"<section id='hero' class='{theme['bg']} py-32'><h1 class='{theme['text']} text-5xl font-bold text-center'>Hero</h1></section>"

    @staticmethod
    def centered_spotlight(theme: Dict, data: Dict, images: List[str]) -> str:
        img = images[0] if images else _get_unsplash_url(["luxury"])
        try:
            return f"""
            <section id="hero" class="relative {theme['bg']} overflow-hidden min-h-screen flex items-center">
                <div class="absolute inset-0 pointer-events-none overflow-hidden">
                    <div class="absolute top-1/4 left-1/2 -translate-x-1/2 w-[600px] h-[600px] bg-gradient-to-r {theme['grad']} opacity-[0.12] blur-[100px] rounded-full"></div>
                    <div class="absolute bottom-0 left-0 w-64 h-64 bg-gradient-to-r {theme['grad']} opacity-[0.08] blur-3xl rounded-full"></div>
                </div>
                <div class="absolute inset-0">
                    <img src="{img}" alt="" class="w-full h-full object-cover opacity-10" loading="eager" />
                </div>
                <div class="container mx-auto {PADDING_CONTAINER} relative z-10 text-center py-40">
                    <div class="max-w-4xl mx-auto space-y-8">
                        <p class="text-sm font-semibold uppercase tracking-[0.25em] {theme['text_muted']}">{data.get('tagline', '— Premium Experience —')}</p>
                        <h1 class="{HEADING_HERO} {theme['text']}">{data.get('hero', {}).get('h1', 'Premium Solution')}</h1>
                        <p class="text-xl md:text-2xl {theme['text_muted']} font-light leading-relaxed max-w-2xl mx-auto">{data.get('hero', {}).get('sub', 'Built for excellence')}</p>
                        <div class="flex flex-col sm:flex-row gap-4 justify-center pt-4">
                            <a href="#contact" class="px-10 py-5 bg-gradient-to-r {theme['grad']} text-white rounded-full font-bold text-lg {HOVER_LIFT} shadow-2xl">
                                {data.get('hero', {}).get('cta', 'Get Started')}
                            </a>
                            <a href="#features" class="{theme['glass']} {theme['text']} px-10 py-5 rounded-full font-semibold border {theme['border']} {HOVER_GLOW}">
                                Discover More ↓
                            </a>
                        </div>
                    </div>
                </div>
            </section>"""
        except Exception as e:
            logger.error(f"centered_spotlight hero error: {e}")
            return f"<section id='hero' class='{theme['bg']} py-32'><h1 class='{theme['text']} text-5xl font-bold text-center'>Hero</h1></section>"

    @staticmethod
    def editorial_large(theme: Dict, data: Dict, images: List[str]) -> str:
        img = images[0] if images else _get_unsplash_url(["modern"])
        h1 = data.get('hero', {}).get('h1', 'Premium Solution')
        words = h1.split()
        mid = max(1, len(words) // 2)
        line1 = " ".join(words[:mid])
        line2 = " ".join(words[mid:])
        try:
            return f"""
            <section id="hero" class="relative {theme['bg']} overflow-hidden pt-36 pb-20">
                <div class="container mx-auto {PADDING_CONTAINER}">
                    <div class="mb-10">
                        <h1 class="font-black tracking-tighter leading-[1.05] text-[clamp(3rem,8vw,7rem)] {theme['text']}">
                            <span class="block">{line1}</span>
                            <span class="block bg-gradient-to-r {theme['grad']} bg-clip-text text-transparent">{line2}</span>
                        </h1>
                    </div>
                    <div class="grid lg:grid-cols-5 gap-12 items-end">
                        <div class="lg:col-span-3 h-[400px] md:h-[500px] overflow-hidden rounded-2xl relative">
                            <img src="{img}" alt="editorial" class="w-full h-full object-cover" loading="eager" />
                        </div>
                        <div class="lg:col-span-2 space-y-6">
                            <p class="text-base md:text-lg {theme['text_muted']} leading-relaxed">{data.get('hero', {}).get('sub', 'Built for excellence')}</p>
                            <a href="#contact" class="inline-block px-8 py-5 bg-gradient-to-r {theme['grad']} text-white rounded-xl font-bold {HOVER_LIFT}">
                                {data.get('hero', {}).get('cta', 'Start Now')} →
                            </a>
                            <div class="pt-4 border-t {theme['border']}">
                                <p class="text-xs {theme['text_light']} uppercase tracking-widest mb-3">Trusted by</p>
                                <p class="text-2xl font-black {theme['stat_color']}">2,400+ businesses</p>
                            </div>
                        </div>
                    </div>
                </div>
            </section>"""
        except Exception as e:
            logger.error(f"editorial_large hero error: {e}")
            return f"<section id='hero' class='{theme['bg']} py-32'><h1 class='{theme['text']} text-5xl font-bold text-center'>Hero</h1></section>"

    @staticmethod
    def stats_hero(theme: Dict, data: Dict, images: List[str]) -> str:
        img = images[0] if images else _get_unsplash_url(["business", "finance"])
        try:
            return f"""
            <section id="hero" class="relative {theme['bg']} overflow-hidden pt-36 pb-24">
                <div class="absolute top-0 right-0 w-1/2 h-full pointer-events-none">
                    <img src="{img}" alt="" class="w-full h-full object-cover opacity-10" loading="eager" />
                </div>
                <div class="container mx-auto {PADDING_CONTAINER} relative z-10">
                    <div class="max-w-3xl space-y-8">
                        <h1 class="{HEADING_HERO_ALT} {theme['text']}">{data.get('hero', {}).get('h1', 'Premium Solution')}</h1>
                        <p class="text-lg {theme['text_muted']} leading-relaxed max-w-xl">{data.get('hero', {}).get('sub', 'Built for excellence')}</p>
                        <a href="#contact" class="inline-block px-8 py-4 bg-gradient-to-r {theme['grad']} text-white rounded-lg font-bold {HOVER_LIFT} shadow-lg">
                            {data.get('hero', {}).get('cta', 'Request Demo')}
                        </a>
                    </div>
                    <div class="grid grid-cols-2 md:grid-cols-4 gap-6 mt-16 pt-12 border-t {theme['border']}">
                        <div><p class="text-4xl font-black {theme['stat_color']}">98%</p><p class="text-sm {theme['text_muted']} mt-1">Client satisfaction</p></div>
                        <div><p class="text-4xl font-black {theme['stat_color']}">2.4k</p><p class="text-sm {theme['text_muted']} mt-1">Active customers</p></div>
                        <div><p class="text-4xl font-black {theme['stat_color']}">$2B</p><p class="text-sm {theme['text_muted']} mt-1">Managed annually</p></div>
                        <div><p class="text-4xl font-black {theme['stat_color']}">24/7</p><p class="text-sm {theme['text_muted']} mt-1">Expert support</p></div>
                    </div>
                </div>
            </section>"""
        except Exception as e:
            logger.error(f"stats_hero error: {e}")
            return f"<section id='hero' class='{theme['bg']} py-32'><h1 class='{theme['text']} text-5xl font-bold text-center'>Hero</h1></section>"


# ============================================================================
# FEATURE VARIANTS
# ============================================================================

class FeatureVariant:

    @staticmethod
    def cards_grid(theme: Dict, features: List[Dict], images: List[str]) -> str:
        items = "".join([f"""
        <div class="{theme['glass']} border {theme['border']} p-8 rounded-2xl {HOVER_LIFT}">
            <div class="w-12 h-12 mb-5 rounded-xl bg-gradient-to-br {theme['grad']} flex items-center justify-center text-xl shadow-md">
                {feat.get('icon', '✨')}
            </div>
            <h3 class="{HEADING_CARD} {theme['text']} mb-2">{feat.get('title', 'Feature')}</h3>
            <p class="{theme['text_muted']} text-sm leading-relaxed">{feat.get('description', '')}</p>
        </div>""" for feat in (features or [])])
        try:
            return f"""
            <section id="features" class="{theme['bg_alt']} {PADDING_SECTION}">
                <div class="container mx-auto {PADDING_CONTAINER}">
                    <div class="text-center mb-14 space-y-3">
                        <p class="text-xs font-semibold uppercase tracking-widest {theme['text_light']}">What we offer</p>
                        <h2 class="{HEADING_SECTION} {theme['text']}">Powerful Features</h2>
                        <p class="text-lg {theme['text_muted']} max-w-xl mx-auto">Everything you need, nothing you don't.</p>
                    </div>
                    <div class="grid sm:grid-cols-2 lg:grid-cols-3 gap-6">{items}</div>
                </div>
            </section>"""
        except Exception as e:
            logger.error(f"cards_grid error: {e}")
            return f"<section id='features' class='{theme['bg_alt']} py-20'><h2 class='text-center text-4xl font-bold'>Features</h2></section>"

    @staticmethod
    def alternating_blocks(theme: Dict, features: List[Dict], images: List[str]) -> str:
        blocks = "".join([f"""
        <div class="grid lg:grid-cols-2 gap-12 items-center">
            <div class="space-y-5 {'order-2 lg:order-2' if i % 2 else ''}">
                <span class="text-3xl">{feat.get('icon', '✨')}</span>
                <h3 class="{HEADING_FEATURE} {theme['text']}">{feat.get('title', 'Feature')}</h3>
                <p class="text-base {theme['text_muted']} leading-relaxed">{feat.get('description', '')}</p>
                <a href="#contact" class="inline-flex items-center gap-2 text-sm font-semibold {theme['stat_color']}">
                    Learn more <span>→</span>
                </a>
            </div>
            <div class="h-72 md:h-80 rounded-2xl overflow-hidden relative {'order-1 lg:order-1' if i % 2 else ''}">
                <img src="{images[i % len(images)] if images else ''}" alt="{feat.get('title', '')}" class="w-full h-full object-cover {HOVER_SCALE}" loading="lazy" />
                <div class="absolute inset-0 bg-gradient-to-br {theme['grad']} opacity-10 mix-blend-multiply"></div>
            </div>
        </div>""" for i, feat in enumerate(features or [])])
        try:
            return f"""
            <section id="features" class="{theme['bg']} {PADDING_SECTION}">
                <div class="container mx-auto {PADDING_CONTAINER}">
                    <h2 class="{HEADING_SECTION} {theme['text']} text-center mb-20">Why It Works</h2>
                    <div class="space-y-24">{blocks}</div>
                </div>
            </section>"""
        except Exception as e:
            logger.error(f"alternating_blocks error: {e}")
            return f"<section id='features' class='{theme['bg']} py-20'><h2 class='text-center text-4xl font-bold'>Features</h2></section>"

    @staticmethod
    def showcase_bento(theme: Dict, features: List[Dict], images: List[str]) -> str:
        feats = (features or [])[:4]
        first = feats[0] if feats else {}
        rest = feats[1:]
        rest_items = "".join([f"""
        <div class="{theme['glass']} border {theme['border']} p-6 rounded-2xl {HOVER_LIFT}">
            <span class="text-2xl">{f.get('icon', '✨')}</span>
            <h3 class="text-lg font-bold {theme['text']} mt-3 mb-2">{f.get('title', 'Feature')}</h3>
            <p class="text-sm {theme['text_muted']} leading-relaxed">{f.get('description', '')}</p>
        </div>""" for f in rest])
        try:
            return f"""
            <section id="features" class="{theme['bg_alt']} {PADDING_SECTION}">
                <div class="container mx-auto {PADDING_CONTAINER}">
                    <h2 class="{HEADING_SECTION} {theme['text']} text-center mb-14">What Makes Us Different</h2>
                    <div class="grid lg:grid-cols-3 gap-5">
                        <div class="{theme['glass']} border {theme['border']} p-10 rounded-2xl lg:col-span-2 {HOVER_LIFT} relative overflow-hidden">
                            <div class="absolute top-0 right-0 w-48 h-48 bg-gradient-to-br {theme['grad']} opacity-10 blur-2xl rounded-full"></div>
                            <span class="text-4xl">{first.get('icon', '✨')}</span>
                            <h3 class="{HEADING_FEATURE} {theme['text']} mt-4 mb-3">{first.get('title', 'Feature')}</h3>
                            <p class="{theme['text_muted']} leading-relaxed">{first.get('description', '')}</p>
                        </div>
                        <div class="space-y-5">{rest_items}</div>
                    </div>
                </div>
            </section>"""
        except Exception as e:
            logger.error(f"showcase_bento error: {e}")
            return f"<section id='features' class='{theme['bg_alt']} py-20'><h2 class='text-center text-4xl font-bold'>Features</h2></section>"

    @staticmethod
    def icon_list(theme: Dict, features: List[Dict], images: List[str]) -> str:
        items = "".join([f"""
        <div class="flex gap-6 items-start p-6 rounded-xl border {theme['border']} {HOVER_GLOW} transition-colors">
            <div class="w-10 h-10 shrink-0 rounded-full bg-gradient-to-br {theme['grad']} flex items-center justify-center text-white font-bold text-sm shadow">
                {str(i+1).zfill(2)}
            </div>
            <div>
                <h3 class="font-bold text-lg {theme['text']} mb-1">{feat.get('title', 'Feature')}</h3>
                <p class="text-sm {theme['text_muted']} leading-relaxed">{feat.get('description', '')}</p>
            </div>
        </div>""" for i, feat in enumerate(features or [])])
        img = images[0] if images else _get_unsplash_url(["professional", "business"])
        try:
            return f"""
            <section id="features" class="{theme['bg']} {PADDING_SECTION}">
                <div class="container mx-auto {PADDING_CONTAINER}">
                    <div class="grid lg:grid-cols-2 gap-16 items-center">
                        <div>
                            <p class="text-xs font-semibold uppercase tracking-widest {theme['text_light']} mb-4">How it works</p>
                            <h2 class="{HEADING_SECTION} {theme['text']} mb-10">Built for Real Results</h2>
                            <div class="space-y-3">{items}</div>
                        </div>
                        <div class="h-[480px] rounded-2xl overflow-hidden relative">
                            <img src="{img}" alt="features" class="w-full h-full object-cover" loading="lazy" />
                        </div>
                    </div>
                </div>
            </section>"""
        except Exception as e:
            logger.error(f"icon_list error: {e}")
            return f"<section id='features' class='{theme['bg']} py-20'><h2 class='text-center text-4xl font-bold'>Features</h2></section>"


# ============================================================================
# PRICING VARIANTS
# ============================================================================

class PricingVariant:

    @staticmethod
    def tiered_cards(theme: Dict, tiers: List[Dict]) -> str:
        def card(tier: Dict) -> str:
            featured = tier.get('featured', False)
            feats = "".join([f"""
            <li class="flex items-start gap-2 text-sm {theme['text_muted']}">
                <span class="mt-0.5 {theme['stat_color']} shrink-0">✓</span>
                <span>{f}</span>
            </li>""" for f in (tier.get('features', []) or [])])
            border_class = f"border-2" if featured else f"border {theme['border']}"
            return f"""
            <div class="{theme['glass']} {border_class} rounded-2xl p-8 {HOVER_LIFT} flex flex-col relative overflow-hidden">
                {'<div class="absolute top-4 right-4 px-3 py-1 bg-gradient-to-r ' + theme["grad"] + ' text-white text-xs font-bold rounded-full">Most Popular</div>' if featured else ''}
                <h3 class="text-lg font-bold {theme['text']} mb-1">{tier.get('name', 'Plan')}</h3>
                <p class="text-xs {theme['text_light']} mb-6">{tier.get('description', '')}</p>
                <div class="mb-6">
                    <span class="text-5xl font-black {theme['text']}">{tier.get('price', '$0')}</span>
                    <span class="text-sm {theme['text_muted']}"> /month</span>
                </div>
                <ul class="space-y-3 mb-8 flex-grow">{feats}</ul>
                <button class="w-full py-3.5 rounded-xl font-bold transition-all {'bg-gradient-to-r ' + theme['grad'] + ' text-white shadow-lg ' + HOVER_LIFT if featured else theme['glass'] + ' ' + theme['text'] + ' border ' + theme['border']}">
                    Get Started
                </button>
            </div>"""
        try:
            cards = "".join([card(t) for t in (tiers or [])])
            return f"""
            <section id="pricing" class="{theme['bg_alt']} {PADDING_SECTION}">
                <div class="container mx-auto {PADDING_CONTAINER}">
                    <div class="text-center mb-14 space-y-3">
                        <p class="text-xs font-semibold uppercase tracking-widest {theme['text_light']}">Pricing</p>
                        <h2 class="{HEADING_SECTION} {theme['text']}">Simple, Honest Pricing</h2>
                        <p class="text-lg {theme['text_muted']}">No hidden fees. Cancel anytime.</p>
                    </div>
                    <div class="grid md:grid-cols-3 gap-6 max-w-5xl mx-auto">{cards}</div>
                </div>
            </section>"""
        except Exception as e:
            logger.error(f"tiered_cards error: {e}")
            return f"<section id='pricing' class='{theme['bg_alt']} py-20'><h2 class='text-center text-4xl font-bold'>Pricing</h2></section>"

    @staticmethod
    def two_column_highlight(theme: Dict, tiers: List[Dict]) -> str:
        tiers = tiers or []
        simple = tiers[0] if tiers else {}
        pro = tiers[1] if len(tiers) > 1 else {}
        def feat_list(tier: Dict) -> str:
            return "".join([f'<li class="flex items-center gap-2 text-sm">{theme["stat_color"]}</span>{f}</li>' for f in (tier.get('features', []) or [])])
        try:
            return f"""
            <section id="pricing" class="{theme['bg']} {PADDING_SECTION}">
                <div class="container mx-auto {PADDING_CONTAINER}">
                    <h2 class="{HEADING_SECTION} {theme['text']} text-center mb-14">Choose Your Plan</h2>
                    <div class="grid md:grid-cols-2 gap-6 max-w-4xl mx-auto">
                        <div class="{theme['glass']} border {theme['border']} p-10 rounded-2xl">
                            <h3 class="text-xl font-bold {theme['text']} mb-2">{simple.get('name', 'Starter')}</h3>
                            <p class="text-5xl font-black {theme['text']} my-5">{simple.get('price', 'Free')}</p>
                            <ul class="space-y-2 mb-8 {theme['text_muted']}">{feat_list(simple)}</ul>
                            <button class="{theme['glass']} {theme['text']} border {theme['border']} w-full py-3 rounded-xl font-bold">Get Started</button>
                        </div>
                        <div class="bg-gradient-to-br {theme['grad']} p-10 rounded-2xl text-white relative overflow-hidden {HOVER_LIFT} shadow-2xl">
                            <div class="absolute top-0 right-0 w-32 h-32 bg-white/10 blur-2xl rounded-full"></div>
                            <span class="px-3 py-1 bg-white/20 text-white text-xs font-bold rounded-full">RECOMMENDED</span>
                            <h3 class="text-xl font-bold mt-4 mb-2">{pro.get('name', 'Pro')}</h3>
                            <p class="text-5xl font-black my-5">{pro.get('price', '$99')}</p>
                            <ul class="space-y-2 mb-8">{feat_list(pro)}</ul>
                            <button class="bg-white text-gray-900 w-full py-3 rounded-xl font-bold hover:bg-gray-100 transition">Upgrade Now</button>
                        </div>
                    </div>
                </div>
            </section>"""
        except Exception as e:
            logger.error(f"two_column_highlight error: {e}")
            return f"<section id='pricing' class='{theme['bg']} py-20'><h2 class='text-center text-4xl font-bold'>Pricing</h2></section>"

    @staticmethod
    def project_based(theme: Dict, tiers: List[Dict]) -> str:
        """
        For construction, trades, legal, logistics — no monthly tiers.
        Shows service packages with 'Get a Quote' CTAs instead of prices.
        The 'tiers' list is reused as service packages (name + features).
        """
        tiers = tiers or []
        icons = ["🏗️", "🔨", "🏢"]
        try:
            cards = "".join([f"""
            <div class="{theme['glass']} border {theme['border']} p-8 rounded-2xl {HOVER_LIFT} flex flex-col">
                <div class="text-3xl mb-4">{icons[i % len(icons)]}</div>
                <h3 class="text-xl font-bold {theme['text']} mb-2">{t.get('name', 'Package')}</h3>
                <p class="text-sm {theme['text_muted']} mb-6 leading-relaxed">{t.get('description', '')}</p>
                <ul class="space-y-2 mb-8 flex-grow">
                    {"".join([f'<li class="flex items-start gap-2 text-sm {theme["text_muted"]}"><span class="mt-0.5 {theme["stat_color"]} shrink-0">✓</span><span>{f}</span></li>' for f in (t.get("features", []) or [])])}
                </ul>
                <a href="#contact" class="w-full py-3 text-center rounded-xl font-bold border {theme['border']} {theme['text']} {theme['glass']} {HOVER_GLOW}">
                    Get a Quote →
                </a>
            </div>""" for i, t in enumerate(tiers)])

            return f"""
            <section id="pricing" class="{theme['bg_alt']} {PADDING_SECTION}">
                <div class="container mx-auto {PADDING_CONTAINER}">
                    <div class="text-center mb-14 space-y-3">
                        <p class="text-xs font-semibold uppercase tracking-widest {theme['text_light']}">Our Services</p>
                        <h2 class="{HEADING_SECTION} {theme['text']}">What We Offer</h2>
                        <p class="text-lg {theme['text_muted']}">Every project is unique. Contact us for a custom quote.</p>
                    </div>
                    <div class="grid md:grid-cols-3 gap-6 max-w-5xl mx-auto mb-12">{cards}</div>
                    <!-- CTA strip -->
                    <div class="{theme['glass']} border {theme['border']} rounded-2xl p-8 max-w-2xl mx-auto text-center">
                        <p class="text-lg font-semibold {theme['text']} mb-2">Not sure which service fits?</p>
                        <p class="text-sm {theme['text_muted']} mb-6">We'll assess your needs and give you a transparent, no-obligation quote.</p>
                        <a href="#contact" class="inline-block px-8 py-4 bg-gradient-to-r {theme['grad']} text-white rounded-xl font-bold {HOVER_LIFT} shadow-lg">
                            Request a Free Estimate
                        </a>
                    </div>
                </div>
            </section>"""
        except Exception as e:
            logger.error(f"project_based pricing error: {e}")
            return f"<section id='pricing' class='{theme['bg_alt']} py-20'><h2 class='text-center text-4xl font-bold'>Services</h2></section>"

    @staticmethod
    def services_list(theme: Dict, tiers: List[Dict]) -> str:
        """
        For legal, consulting, nonprofits — horizontal service rows with
        'Schedule a Consultation' as the CTA instead of a Buy button.
        """
        tiers = tiers or []
        try:
            rows = "".join([f"""
            <div class="grid md:grid-cols-3 gap-6 items-center py-8 border-b {theme['border']}">
                <div>
                    <h3 class="text-lg font-bold {theme['text']}">{t.get('name', 'Service')}</h3>
                    <p class="text-sm {theme['text_muted']} mt-1">{t.get('description', '')}</p>
                </div>
                <ul class="space-y-1 md:col-span-1">
                    {"".join([f'<li class="flex items-center gap-2 text-sm {theme["text_muted"]}"><span class="{theme["stat_color"]}">✓</span>{f}</li>' for f in (t.get("features", []) or [])[:3]])}
                </ul>
                <div class="text-right">
                    <a href="#contact" class="inline-block px-6 py-3 bg-gradient-to-r {theme['grad']} text-white rounded-lg font-semibold text-sm {HOVER_LIFT}">
                        Book Consultation
                    </a>
                </div>
            </div>""" for t in tiers])

            return f"""
            <section id="pricing" class="{theme['bg']} {PADDING_SECTION}">
                <div class="container mx-auto {PADDING_CONTAINER}">
                    <div class="mb-12">
                        <p class="text-xs font-semibold uppercase tracking-widest {theme['text_light']} mb-3">Our Services</p>
                        <h2 class="{HEADING_SECTION} {theme['text']}">How We Can Help</h2>
                        <p class="text-lg {theme['text_muted']} mt-4 max-w-xl">All engagements begin with a complimentary consultation to understand your needs.</p>
                    </div>
                    <div class="divide-y {theme['border']}">{rows}</div>
                    <div class="mt-10 text-center">
                        <a href="#contact" class="inline-block px-10 py-5 bg-gradient-to-r {theme['grad']} text-white rounded-xl font-bold {HOVER_LIFT} shadow-xl">
                            Schedule Your Free Consultation
                        </a>
                    </div>
                </div>
            </section>"""
        except Exception as e:
            logger.error(f"services_list pricing error: {e}")
            return f"<section id='pricing' class='{theme['bg']} py-20'><h2 class='text-center text-4xl font-bold'>Services</h2></section>"


# ============================================================================
# MASTER ARCHITECT
# ============================================================================

class MasterArchitect:

    def __init__(self, business_name: str, prompt: str, version: int = 1):
        raw_name = (business_name or "").strip()
        raw_prompt = (prompt or "").strip()

        # Step 1: extract the real name and recover any description overflow
        clean_name, clean_prompt = extract_business_name(raw_name, raw_prompt)

        # Step 2: detect industry early (needed for name fallback)
        self.industry = detect_industry(clean_prompt or raw_prompt)

        # Step 3: if name is still empty, derive a placeholder from industry
        if not clean_name:
            clean_name = derive_name_from_prompt(clean_prompt, self.industry)
            logger.info(f"No explicit business name found; derived: '{clean_name}'")

        self.name = clean_name
        self.prompt = clean_prompt
        self.version = version
        self.seed = f"{self.name}::{self.prompt}"
        self.theme = select_theme(self.industry, seed=self.seed)
        self.data: Dict = {}
        self.images: List[str] = []
        logger.info(f"MasterArchitect: name='{self.name}', industry={self.industry}, theme={self.theme['id']}")

    def get_ai_payload(self) -> Dict:
        # Determine what kind of "pricing" makes sense for this industry
        project_based_industries = {"construction", "logistics", "automotive", "events"}
        services_industries      = {"legal", "nonprofit"}
        no_price_industries      = project_based_industries | services_industries

        if self.industry in project_based_industries:
            pricing_instruction = """  "pricing": [   // 3 service PACKAGES (not monthly tiers — this is a project/trade business)
    // Do NOT use monthly prices. Instead describe what each package covers.
    // Use names like "Small Projects", "Commercial Work", "Enterprise Contracts"
    // Set "price" to "Get a Quote" or "From $X,XXX" — realistic for this trade
    {"name": "...", "price": "From $X,XXX", "description": "1 sentence about scope", "features": ["...", "...", "...", "...", "..."], "featured": false},
    {"name": "...", "price": "From $X,XXX", "description": "1 sentence about scope", "features": ["...", "...", "...", "...", "..."], "featured": true},
    {"name": "...", "price": "Get a Quote", "description": "1 sentence about scope", "features": ["...", "...", "...", "...", "..."], "featured": false}
  ],"""
        elif self.industry in services_industries:
            pricing_instruction = """  "pricing": [   // 3 service OFFERINGS (no monthly pricing — this is a professional service)
    // Use names like "Initial Consultation", "Ongoing Retainer", "Full Representation"
    // Set "price" to "Complimentary" / "From $X/hr" / "Custom Engagement"
    {"name": "...", "price": "Complimentary", "description": "1 sentence", "features": ["...", "...", "...", "...", "..."], "featured": false},
    {"name": "...", "price": "From $X/hr", "description": "1 sentence", "features": ["...", "...", "...", "...", "..."], "featured": true},
    {"name": "...", "price": "Custom", "description": "1 sentence", "features": ["...", "...", "...", "...", "..."], "featured": false}
  ],"""
        else:
            pricing_instruction = """  "pricing": [   // 3 pricing tiers realistic for this industry
    {"name": "...", "price": "$X", "description": "1 sentence", "features": ["...", "...", "...", "...", "..."], "featured": false},
    {"name": "...", "price": "$X", "description": "1 sentence", "features": ["...", "...", "...", "...", "..."], "featured": true},
    {"name": "...", "price": "Custom", "description": "1 sentence", "features": ["...", "...", "...", "...", "..."], "featured": false}
  ],"""

        system_msg = (
            "You are an elite conversion copywriter and brand strategist. "
            "Generate SPECIFIC, vivid, industry-tailored website content. "
            "Avoid all generic filler phrases. Output ONLY valid JSON — no markdown, no prose."
        )
        user_msg = f"""Create website content for '{self.name}'.
Business description: {self.prompt}
Detected industry: {self.industry}

CRITICAL RULES:
- Write headlines SPECIFIC to this exact business — not generic SaaS copy
- Use the business's actual domain language (construction = builds, delivers, installs; legal = advises, represents, protects)
- Features must reflect what THIS business actually does, not generic tech features
- Tone must match the industry: formal for legal, direct for construction, warm for food, bold for startups

Return ONLY this JSON (no backticks, no preamble):
{{
  "nav": ["string", "string", "string", "string"],
  "hero": {{
    "h1": "max 8 words, punchy headline specific to this business",
    "sub": "1 sentence value proposition using this industry's language",
    "cta": "action verb + short phrase appropriate for this industry"
  }},
  "tagline": "2-5 word brand slogan",
  "brand_voice": "one word: professional|bold|warm|playful|luxurious|technical",
  "features": [
    {{"title": "...", "description": "2 sentence description specific to what this business actually does", "icon": "emoji"}}
  ],
{pricing_instruction}
  "testimonials": [
    {{"name": "...", "role": "...", "company": "...", "quote": "specific 1-2 sentence testimonial about real results"}}
  ],
  "faq": [
    {{"q": "...", "a": "..."}}
  ],
  "cta_text": "closing CTA headline appropriate for this industry",
  "unsplash_keywords": ["keyword1", "keyword2", "keyword3", "keyword4", "keyword5"]
}}"""
        if not AI_AVAILABLE:
            logger.warning("AI client unavailable; using fallback")
            return self._get_fallback_payload()
        try:
            res = chat_completion(system=system_msg, user=user_msg, temperature=0.75)
            cleaned = res.strip().replace("```json", "").replace("```", "").strip()
            payload = json.loads(cleaned)
            
            # CRITICAL: Sanitize AI response to prevent theme leaks
            payload = self._sanitize_ai_payload(payload)
            
            logger.info("AI payload generated successfully")
            return payload
        except Exception as e:
            logger.error(f"AI payload error: {e}")
            return self._get_fallback_payload()
    
    def _sanitize_ai_payload(self, payload: Dict) -> Dict:
        """
        Clean AI-generated content to prevent theme leaks and ensure consistency.
        
        Issues this catches:
        1. Wrong unsplash_keywords (e.g. AI returns 'luxury spa' for construction)
        2. Color mentions in text ('our purple logo', 'blue website')
        3. Generic SaaS language for non-SaaS businesses
        """
        # Fix 1: Validate unsplash_keywords match the industry
        keywords = payload.get('unsplash_keywords', [])
        if keywords:
            # Check if keywords are completely off-industry
            kw_text = " ".join(keywords).lower()
            industry_kw = " ".join(INDUSTRY_KEYWORD_MAP.get(self.industry, [])).lower()
            
            # If there's < 10% overlap, replace with industry defaults
            overlap = sum(1 for word in keywords if any(ind in word.lower() or word.lower() in ind for ind in INDUSTRY_KEYWORD_MAP.get(self.industry, [])))
            if overlap == 0:
                logger.warning(f"AI returned off-industry keywords {keywords} for {self.industry}; fixing")
                payload['unsplash_keywords'] = self._get_default_keywords()
        else:
            payload['unsplash_keywords'] = self._get_default_keywords()
        
        # Fix 2: Strip color mentions from all text content to prevent theme leaks
        # (e.g. "our vibrant purple brand" would inject purple into a grey theme)
        color_words = ['purple', 'violet', 'fuchsia', 'rose', 'pink', 'blue', 'cyan', 'indigo',
                       'amber', 'orange', 'emerald', 'teal', 'green', 'slate', 'gray']
        
        def strip_colors(text: str) -> str:
            if not isinstance(text, str):
                return text
            for color in color_words:
                # Remove phrases like "purple brand", "blue logo", but preserve "blueberry" or "violet flowers"
                text = text.replace(f"{color} brand", "distinctive brand")
                text = text.replace(f"{color} logo", "unique logo")
                text = text.replace(f"{color} website", "modern website")
                text = text.replace(f"{color} design", "custom design")
            return text
        
        # Apply to all text fields
        if 'hero' in payload:
            for key in ['h1', 'sub', 'cta']:
                if key in payload['hero']:
                    payload['hero'][key] = strip_colors(payload['hero'][key])
        
        if 'tagline' in payload:
            payload['tagline'] = strip_colors(payload['tagline'])
        
        if 'features' in payload:
            for feat in payload['features']:
                if 'title' in feat:
                    feat['title'] = strip_colors(feat['title'])
                if 'description' in feat:
                    feat['description'] = strip_colors(feat['description'])
        
        if 'testimonials' in payload:
            for t in payload['testimonials']:
                if 'quote' in t:
                    t['quote'] = strip_colors(t['quote'])
        
        if 'faq' in payload:
            for faq in payload['faq']:
                if 'q' in faq:
                    faq['q'] = strip_colors(faq['q'])
                if 'a' in faq:
                    faq['a'] = strip_colors(faq['a'])
        
        if 'cta_text' in payload:
            payload['cta_text'] = strip_colors(payload['cta_text'])
        
        return payload
    
    def _get_default_keywords(self) -> List[str]:
        """Return safe, industry-appropriate unsplash keywords"""
        defaults = {
            "construction": ["construction", "building", "contractor", "architecture", "renovation"],
            "legal": ["legal", "law", "professional", "office", "business"],
            "finance": ["finance", "business", "professional", "office", "investment"],
            "health": ["health", "wellness", "medical", "fitness", "clinic"],
            "restaurant": ["food", "restaurant", "dining", "chef", "cuisine"],
            "beauty": ["beauty", "spa", "wellness", "aesthetic", "luxury"],
            "ecommerce": ["shop", "retail", "product", "ecommerce", "store"],
            "saas": ["technology", "business", "software", "modern", "team"],
            "agency": ["creative", "design", "studio", "brand", "marketing"],
            "real_estate": ["property", "real estate", "architecture", "modern", "home"],
            "logistics": ["logistics", "shipping", "warehouse", "transport", "business"],
            "automotive": ["auto", "car", "vehicle", "mechanic", "garage"],
            "events": ["event", "celebration", "venue", "party", "wedding"],
            "nonprofit": ["community", "nonprofit", "people", "volunteer", "charity"],
            "nature": ["nature", "organic", "farm", "green", "sustainable"],
            "education": ["education", "learning", "school", "training", "students"],
            "travel": ["travel", "hotel", "vacation", "destination", "tourism"],
            "luxury": ["luxury", "premium", "elegant", "exclusive", "high-end"],
            "ai": ["technology", "ai", "data", "innovation", "futuristic"],
            "developer": ["code", "developer", "technology", "software", "programming"],
            "startup": ["startup", "innovation", "technology", "entrepreneurship", "modern"],
        }
        return defaults.get(self.industry, ["business", "professional", "modern", "team", "office"])

    def _get_fallback_payload(self) -> Dict:
        """Industry-aware fallback when AI is unavailable"""
        
        # Industry-specific defaults
        if self.industry == "construction":
            return {
                "nav": ["Services", "Projects", "About", "Contact"],
                "hero": {"h1": f"Professional {self.industry.title()} Services", "sub": "Quality craftsmanship. On time, on budget.", "cta": "Request a Quote"},
                "tagline": "Built to last.",
                "brand_voice": "professional",
                "features": [
                    {"title": "Licensed & Insured", "description": "Fully licensed contractors with comprehensive insurance coverage for your peace of mind.", "icon": "🛡️"},
                    {"title": "Quality Workmanship", "description": "Skilled tradespeople delivering superior results on every project, large or small.", "icon": "🔨"},
                    {"title": "Transparent Pricing", "description": "Detailed estimates with no hidden fees. You'll know exactly what to expect.", "icon": "📋"},
                ],
                "pricing": [
                    {"name": "Residential", "price": "Get a Quote", "description": "Home renovations and repairs", "features": ["Kitchen & bathroom remodels", "Roofing & siding", "Flooring installation", "Painting", "Minor repairs"], "featured": False},
                    {"name": "Commercial", "price": "Get a Quote", "description": "Business construction projects", "features": ["Office build-outs", "Retail spaces", "Warehouse work", "ADA compliance", "Ongoing maintenance"], "featured": True},
                    {"name": "Emergency", "price": "24/7 Available", "description": "Urgent repair services", "features": ["Storm damage", "Water damage mitigation", "Structural issues", "Same-day service", "Direct insurance billing"], "featured": False},
                ],
                "testimonials": [
                    {"name": "Michael Torres", "role": "Homeowner", "company": "Brooklyn, NY", "quote": "They completely renovated our kitchen on schedule and within budget. Excellent craftsmanship."},
                    {"name": "Lisa Chen", "role": "Property Manager", "company": "Manhattan", "quote": "We've used them for 5+ years across multiple properties. Always reliable and professional."},
                ],
                "faq": [
                    {"q": "Are you licensed and insured?", "a": "Yes, we carry full licensing and comprehensive liability and workers' compensation insurance."},
                    {"q": "Do you offer free estimates?", "a": "Absolutely. We provide detailed, no-obligation estimates for all projects."},
                    {"q": "What's your typical timeline?", "a": "It varies by project scope, but we'll give you a clear timeline upfront and keep you updated throughout."},
                ],
                "cta_text": "Ready to start your project?",
                "unsplash_keywords": ["construction", "building", "contractor", "renovation", "architecture"],
            }
        
        elif self.industry == "legal":
            return {
                "nav": ["Practice Areas", "Our Team", "Resources", "Contact"],
                "hero": {"h1": f"Trusted Legal Counsel", "sub": "Protecting your interests with expertise and integrity.", "cta": "Schedule Consultation"},
                "tagline": "Your advocate.",
                "brand_voice": "professional",
                "features": [
                    {"title": "Experienced Attorneys", "description": "Decades of combined experience across multiple practice areas. We know the law.", "icon": "⚖️"},
                    {"title": "Client-Focused Approach", "description": "Your goals are our priority. We listen, strategize, and fight for your best outcome.", "icon": "🤝"},
                    {"title": "Clear Communication", "description": "No legal jargon. We explain your options in plain English so you can make informed decisions.", "icon": "💬"},
                ],
                "pricing": [
                    {"name": "Initial Consultation", "price": "Complimentary", "description": "30-minute case review", "features": ["Case assessment", "Legal options overview", "Fee structure discussion", "No obligation", "Confidential"], "featured": False},
                    {"name": "Hourly Representation", "price": "From $300/hr", "description": "Pay as you go", "features": ["Experienced attorneys", "Flexible engagement", "Detailed billing", "Case strategy", "Court representation"], "featured": True},
                    {"name": "Flat Fee Services", "price": "Custom", "description": "Fixed-price matters", "features": ["Contract review", "Business formation", "Estate planning", "Trademark filing", "Predictable costs"], "featured": False},
                ],
                "testimonials": [
                    {"name": "Robert Kim", "role": "CEO", "company": "TechStart Inc", "quote": "They guided us through a complex acquisition with skill and professionalism. Couldn't recommend them more highly."},
                    {"name": "Jennifer Adams", "role": "Client", "company": "Chicago, IL", "quote": "After years of frustration with my previous attorney, their team resolved my case in months. Exceptional service."},
                ],
                "faq": [
                    {"q": "What practice areas do you cover?", "a": "We handle corporate law, employment matters, real estate transactions, and civil litigation."},
                    {"q": "How do consultations work?", "a": "We offer a complimentary 30-minute consultation to assess your case and discuss how we can help."},
                    {"q": "Do you take contingency cases?", "a": "It depends on the matter. We'll discuss fee arrangements during your consultation."},
                ],
                "cta_text": "Need legal guidance?",
                "unsplash_keywords": ["legal", "law", "attorney", "professional", "office"],
            }
        
        elif self.industry in ["restaurant", "food"]:
            return {
                "nav": ["Menu", "About", "Catering", "Contact"],
                "hero": {"h1": f"Authentic Flavors", "sub": "Made fresh daily with locally-sourced ingredients.", "cta": "View Menu"},
                "tagline": "Taste the difference.",
                "brand_voice": "warm",
                "features": [
                    {"title": "Fresh Ingredients", "description": "We source locally whenever possible and prepare everything fresh in-house daily.", "icon": "🥗"},
                    {"title": "Family Recipes", "description": "Passed down through generations, our recipes bring authentic flavor to every dish.", "icon": "👨‍🍳"},
                    {"title": "Warm Atmosphere", "description": "Cozy dining room perfect for date nights, family dinners, or celebrations.", "icon": "🏡"},
                ],
                "pricing": [
                    {"name": "Lunch", "price": "$15-25", "description": "Daily specials", "features": ["Soup & salad combos", "Sandwiches", "Light entrees", "Fresh bread", "Quick service"], "featured": False},
                    {"name": "Dinner", "price": "$25-45", "description": "Full menu", "features": ["Signature entrees", "Pasta dishes", "Fresh seafood", "Wine pairings", "Desserts"], "featured": True},
                    {"name": "Catering", "price": "Custom", "description": "Events & parties", "features": ["Corporate events", "Family gatherings", "Drop-off or full service", "Customizable menus", "Dietary accommodations"], "featured": False},
                ],
                "testimonials": [
                    {"name": "Maria Gonzalez", "role": "Local Resident", "company": "Yelp Elite", "quote": "Best Italian food outside of Italy! The pasta is always perfectly cooked and the portions are generous."},
                    {"name": "David Park", "role": "Food Blogger", "company": "NYC Eats", "quote": "A hidden gem. Everything is made with love and you can taste it in every bite."},
                ],
                "faq": [
                    {"q": "Do you take reservations?", "a": "Yes, we recommend reservations for dinner, especially on weekends. Walk-ins are always welcome for lunch."},
                    {"q": "Can you accommodate dietary restrictions?", "a": "Absolutely. We offer vegetarian, vegan, and gluten-free options. Just let us know when ordering."},
                    {"q": "Do you offer takeout?", "a": "Yes, full menu available for takeout and we also partner with major delivery services."},
                ],
                "cta_text": "Come taste the difference",
                "unsplash_keywords": ["food", "restaurant", "dining", "cuisine", "chef"],
            }
        
        # Default SaaS-style fallback for tech industries
        return {
            "nav": ["Features", "Pricing", "FAQ", "Contact"],
            "hero": {"h1": f"Welcome to {self.name}", "sub": "Premium solutions built for your needs.", "cta": "Get Started"},
            "tagline": "Built for the bold.",
            "brand_voice": "professional",
            "features": [
                {"title": "Speed & Reliability", "description": "Industry-leading uptime with blazing performance. Never miss a beat.", "icon": "⚡"},
                {"title": "Seamless Integration", "description": "Connects with your existing stack in minutes. No dev required.", "icon": "🔗"},
                {"title": "Powerful Analytics", "description": "Real-time insights to drive smarter decisions every day.", "icon": "📊"},
            ],
            "pricing": [
                {"name": "Starter", "price": "$29", "description": "Perfect for individuals.", "features": ["5 projects", "1GB storage", "Email support", "API access", "Monthly reports"], "featured": False},
                {"name": "Pro", "price": "$99", "description": "For growing teams.", "features": ["Unlimited projects", "50GB storage", "Priority support", "Advanced analytics", "Custom integrations"], "featured": True},
                {"name": "Enterprise", "price": "Custom", "description": "For large organisations.", "features": ["Everything in Pro", "Dedicated manager", "SLA guarantee", "Custom contracts", "On-premise option"], "featured": False},
            ],
            "testimonials": [
                {"name": "Sarah Chen", "role": "CEO", "company": "NexusCorp", "quote": "Completely transformed our workflow. We saved 20 hours per week."},
                {"name": "Marcus Webb", "role": "CTO", "company": "LaunchpadAI", "quote": "The best platform investment we've made. ROI was visible within weeks."},
            ],
            "faq": [
                {"q": "How quickly can I get started?", "a": "You'll be fully set up in under 10 minutes with our guided onboarding."},
                {"q": "What support do you provide?", "a": "All plans include email support. Pro and Enterprise get 24/7 priority access."},
                {"q": "Is there a free trial?", "a": "Yes — a full 14-day free trial, no credit card required."},
            ],
            "cta_text": f"Ready to take {self.name} to the next level?",
            "unsplash_keywords": ["technology", "business", "modern", "team", "workspace"],
        }

    def _pick_hero_variant(self) -> Callable:
        mapping = {
            "luxury":       HeroVariant.centered_spotlight,
            "agency":       HeroVariant.centered_spotlight,
            "beauty":       HeroVariant.centered_spotlight,
            "finance":      HeroVariant.stats_hero,
            "real_estate":  HeroVariant.stats_hero,
            "legal":        HeroVariant.stats_hero,
            "saas":         HeroVariant.split_grid,
            "ecommerce":    HeroVariant.editorial_large,
            "restaurant":   HeroVariant.editorial_large,
            "education":    HeroVariant.split_grid,
            "developer":    HeroVariant.split_grid,
            # Trades: split with a strong job-site photo
            "construction": HeroVariant.split_grid,
            "logistics":    HeroVariant.stats_hero,
            "automotive":   HeroVariant.split_grid,
            "events":       HeroVariant.editorial_large,
            "nonprofit":    HeroVariant.centered_spotlight,
        }
        default_pool = [HeroVariant.split_grid, HeroVariant.centered_spotlight, HeroVariant.editorial_large]
        if self.industry in mapping:
            return mapping[self.industry]
        idx = int(hashlib.md5(self.seed.encode()).hexdigest(), 16) % len(default_pool)
        return default_pool[idx]

    def _pick_feature_variant(self) -> Callable:
        mapping = {
            "luxury":       FeatureVariant.showcase_bento,
            "agency":       FeatureVariant.showcase_bento,
            "beauty":       FeatureVariant.showcase_bento,
            "finance":      FeatureVariant.icon_list,
            "real_estate":  FeatureVariant.icon_list,
            "legal":        FeatureVariant.icon_list,
            "health":       FeatureVariant.alternating_blocks,
            "travel":       FeatureVariant.alternating_blocks,
            "restaurant":   FeatureVariant.alternating_blocks,
            "saas":         FeatureVariant.cards_grid,
            "ecommerce":    FeatureVariant.cards_grid,
            "developer":    FeatureVariant.cards_grid,
            # Trades: alternating blocks shows real job-site photos per service
            "construction": FeatureVariant.alternating_blocks,
            "logistics":    FeatureVariant.icon_list,
            "automotive":   FeatureVariant.alternating_blocks,
            "events":       FeatureVariant.showcase_bento,
            "nonprofit":    FeatureVariant.alternating_blocks,
        }
        default_pool = [FeatureVariant.cards_grid, FeatureVariant.showcase_bento, FeatureVariant.alternating_blocks]
        if self.industry in mapping:
            return mapping[self.industry]
        idx = int(hashlib.md5((self.seed + "features").encode()).hexdigest(), 16) % len(default_pool)
        return default_pool[idx]

    def _pick_pricing_variant(self) -> Callable:
        # Physical trades and project-based work — no monthly tiers, quote-driven
        project_industries = {"construction", "logistics", "automotive", "events"}
        # Professional services — consultation-based, no visible prices
        services_industries = {"legal", "nonprofit"}
        # Luxury/premium — two bold columns
        premium_industries  = {"luxury", "agency", "beauty", "finance", "real_estate"}

        if self.industry in project_industries:
            return PricingVariant.project_based
        if self.industry in services_industries:
            return PricingVariant.services_list
        if self.industry in premium_industries:
            return PricingVariant.two_column_highlight
        return PricingVariant.tiered_cards

    def render_nav(self) -> str:
        nav_items = "".join([
            f'<li><a href="#{link.lower().replace(" ", "")}" class="{self.theme["text_muted"]} hover:{self.theme["primary"]}-500 transition-colors duration-200 text-sm font-medium">{link}</a></li>'
            for link in (self.data.get('nav', []) or [])
        ])
        try:
            return f"""
            <nav class="fixed top-0 w-full z-50 {self.theme['nav_bg']} backdrop-blur-xl py-4">
                <div class="container mx-auto {PADDING_CONTAINER} flex justify-between items-center">
                    <a href="#" class="text-xl font-black tracking-tight {self.theme['text']}">{self.name}</a>
                    <ul class="hidden md:flex gap-8">{nav_items}</ul>
                    <a href="#contact" class="px-5 py-2.5 bg-gradient-to-r {self.theme['grad']} text-white rounded-lg font-semibold text-sm {HOVER_LIFT} shadow-md">
                        {self.data.get('hero', {}).get('cta', 'Get Started')}
                    </a>
                </div>
            </nav>"""
        except Exception as e:
            logger.error(f"nav error: {e}")
            return f"<nav class='fixed top-0 w-full z-50 bg-white/90 backdrop-blur py-4 border-b'><div class='container mx-auto px-6'><a href='#' class='text-xl font-bold'>{self.name}</a></div></nav>"

    def render_hero(self) -> str:
        try:
            return self._pick_hero_variant()(self.theme, self.data, self.images)
        except Exception as e:
            logger.error(f"hero error: {e}")
            return f"<section id='hero' class='{self.theme['bg']} py-32'><div class='container mx-auto px-6 text-center'><h1 class='{self.theme['text']} text-5xl font-bold'>Welcome</h1></div></section>"

    def render_features(self) -> str:
        try:
            return self._pick_feature_variant()(self.theme, self.data.get('features', []), self.images)
        except Exception as e:
            logger.error(f"features error: {e}")
            return f"<section id='features' class='{self.theme['bg_alt']} py-20'><h2 class='{self.theme['text']} text-4xl font-bold text-center'>Features</h2></section>"

    def render_pricing(self) -> str:
        try:
            return self._pick_pricing_variant()(self.theme, self.data.get('pricing', []))
        except Exception as e:
            logger.error(f"pricing error: {e}")
            return f"<section id='pricing' class='{self.theme['bg_alt']} py-20'><h2 class='{self.theme['text']} text-4xl font-bold text-center'>Pricing</h2></section>"

    def render_testimonials(self) -> str:
        testimonials = self.data.get('testimonials', [])
        if not testimonials:
            return ""
        cards = "".join([f"""
        <div class="{self.theme['glass']} border {self.theme['border']} p-8 rounded-2xl {HOVER_LIFT}">
            <div class="flex gap-1 mb-4">{''.join(['<span class="text-amber-400 text-sm">★</span>' for _ in range(5)])}</div>
            <p class="{self.theme['text_muted']} text-base italic leading-relaxed mb-6">"{t.get('quote', '')}"</p>
            <div class="flex items-center gap-3">
                <div class="w-10 h-10 rounded-full bg-gradient-to-br {self.theme['grad']} flex items-center justify-center text-white font-bold text-sm">
                    {t.get('name', 'C')[0]}
                </div>
                <div>
                    <p class="{self.theme['text']} font-bold text-sm">{t.get('name', 'Client')}</p>
                    <p class="{self.theme['text_light']} text-xs">{t.get('role', '')} · {t.get('company', 'Company')}</p>
                </div>
            </div>
        </div>""" for t in testimonials])
        try:
            return f"""
            <section id="testimonials" class="{self.theme['bg']} {PADDING_SECTION}">
                <div class="container mx-auto {PADDING_CONTAINER}">
                    <div class="text-center mb-12">
                        <p class="text-xs font-semibold uppercase tracking-widest {self.theme['text_light']} mb-3">Testimonials</p>
                        <h2 class="{HEADING_SECTION} {self.theme['text']}">Trusted by Leaders</h2>
                    </div>
                    <div class="grid md:grid-cols-2 gap-6 max-w-4xl mx-auto">{cards}</div>
                </div>
            </section>"""
        except Exception as e:
            logger.error(f"testimonials error: {e}")
            return ""

    def render_faq(self) -> str:
        faqs = self.data.get('faq', [])
        if not faqs:
            return ""
        items = "".join([f"""
        <details class="{self.theme['glass']} border {self.theme['border']} rounded-xl overflow-hidden group">
            <summary class="flex justify-between items-center p-6 cursor-pointer font-semibold {self.theme['text']} list-none hover:opacity-80 transition">
                {faq.get('q', '')}
                <span class="ml-4 shrink-0 w-5 h-5 rounded-full border {self.theme['border']} flex items-center justify-center text-xs group-open:rotate-45 transition-transform duration-300">+</span>
            </summary>
            <div class="px-6 pb-6">
                <p class="{self.theme['text_muted']} text-sm leading-relaxed">{faq.get('a', '')}</p>
            </div>
        </details>""" for faq in faqs])
        try:
            return f"""
            <section id="faq" class="{self.theme['bg_alt']} {PADDING_SECTION}">
                <div class="container mx-auto {PADDING_CONTAINER}">
                    <h2 class="{HEADING_SECTION} {self.theme['text']} text-center mb-10">Frequently Asked</h2>
                    <div class="space-y-3 max-w-2xl mx-auto">{items}</div>
                </div>
            </section>"""
        except Exception as e:
            logger.error(f"faq error: {e}")
            return ""

    def render_trust_band(self) -> str:
        industry_trust = {
            "finance":    ["SOC 2 Certified", "256-bit Encryption", "GDPR Compliant", "FINRA Member", "ISO 27001"],
            "health":     ["HIPAA Compliant", "FDA Registered", "ISO 13485", "ADA Accessible", "HITRUST CSF"],
            "saas":       ["SOC 2 Type II", "99.99% Uptime SLA", "GDPR Ready", "24/7 Monitoring", "Zero-downtime deploys"],
            "ecommerce":  ["PCI-DSS Compliant", "SSL Secured", "Money-back Guarantee", "Trusted Reviews", "Secure Checkout"],
            "education":  ["FERPA Compliant", "COPPA Safe", "Accredited Provider", "ADA Accessible", "Secure Platform"],
            "developer":  ["SOC 2 Type II", "Open Source Core", "99.9% Uptime", "GDPR Ready", "Enterprise SLA"],
            "restaurant": ["Health Inspected ✓", "Locally Sourced", "5-Star Rated", "Est. 2018", "Award Winning"],
        }
        badges = industry_trust.get(self.industry, ["ISO 9001", "SOC 2", "GDPR Compliant", "256-bit SSL", "Award Winner 2024"])
        badge_html = "".join([f'<span class="px-3 py-1.5 rounded-full text-xs font-semibold {self.theme["badge_style"]}">{b}</span>' for b in badges])
        try:
            return f"""
            <div class="{self.theme['bg_alt']} border-y {self.theme['border']} py-8">
                <div class="container mx-auto {PADDING_CONTAINER}">
                    <div class="flex flex-wrap items-center justify-center gap-3">
                        <span class="text-xs {self.theme['text_light']} uppercase tracking-widest mr-4">Verified &amp; Trusted</span>
                        {badge_html}
                    </div>
                </div>
            </div>"""
        except Exception as e:
            logger.error(f"trust band error: {e}")
            return ""

    def render_cta_section(self) -> str:
        cta_text = self.data.get('cta_text', 'Ready to get started?')
        img = self.images[2] if len(self.images) > 2 else _get_unsplash_url(["business", "team"])
        try:
            return f"""
            <section id="contact" class="relative {self.theme['bg']} {PADDING_SECTION} overflow-hidden">
                <div class="absolute inset-0">
                    <img src="{img}" alt="" class="w-full h-full object-cover opacity-[0.07]" loading="lazy" />
                </div>
                <div class="absolute inset-0 bg-gradient-to-br {self.theme['grad_subtle']} opacity-40"></div>
                <div class="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[500px] h-[500px] bg-gradient-to-r {self.theme['grad']} opacity-10 blur-[80px] rounded-full"></div>
                <div class="container mx-auto {PADDING_CONTAINER} relative z-10 text-center">
                    <h2 class="{HEADING_SECTION} {self.theme['text']} mb-6">{cta_text}</h2>
                    <p class="text-lg {self.theme['text_muted']} mb-10 max-w-xl mx-auto">{self.data.get('hero', {}).get('sub', '')}</p>
                    <div class="flex flex-col sm:flex-row gap-4 justify-center">
                        <a href="mailto:hello@{self.name.lower().replace(' ', '')}.com" class="px-10 py-5 bg-gradient-to-r {self.theme['grad']} text-white rounded-xl font-bold {HOVER_LIFT} shadow-2xl">
                            Book a Demo
                        </a>
                        <a href="tel:+12345678900" class="{self.theme['glass']} border {self.theme['border']} {self.theme['text']} px-10 py-5 rounded-xl font-bold {HOVER_GLOW}">
                            Talk to Sales
                        </a>
                    </div>
                </div>
            </section>"""
        except Exception as e:
            logger.error(f"cta error: {e}")
            return f"<section id='contact' class='{self.theme['bg']} py-24 text-center'><h2 class='{self.theme['text']} text-4xl font-bold'>Get In Touch</h2></section>"

    def render_footer(self) -> str:
        nav_links = "".join([
            f'<li><a href="#{link.lower().replace(" ", "")}" class="{self.theme["text_muted"]} hover:opacity-70 text-sm transition">{link}</a></li>'
            for link in (self.data.get('nav', []) or [])
        ])
        try:
            return f"""
            <footer class="{self.theme['bg_alt']} border-t {self.theme['border']} py-14">
                <div class="container mx-auto {PADDING_CONTAINER}">
                    <div class="grid md:grid-cols-4 gap-10 mb-10">
                        <div class="md:col-span-2">
                            <h3 class="font-black text-xl {self.theme['text']} mb-3">{self.name}</h3>
                            <p class="{self.theme['text_muted']} text-sm max-w-xs leading-relaxed">{self.data.get('hero', {}).get('sub', 'Premium solutions for modern businesses.')}</p>
                            <p class="text-xs {self.theme['text_light']} mt-4 italic">{self.data.get('tagline', '')}</p>
                        </div>
                        <div>
                            <h4 class="font-bold text-sm {self.theme['text']} mb-4 uppercase tracking-widest">Navigation</h4>
                            <ul class="space-y-2">{nav_links}</ul>
                        </div>
                        <div>
                            <h4 class="font-bold text-sm {self.theme['text']} mb-4 uppercase tracking-widest">Legal</h4>
                            <ul class="space-y-2 text-sm">
                                <li><a href="#" class="{self.theme['text_muted']} hover:opacity-70 transition">Privacy Policy</a></li>
                                <li><a href="#" class="{self.theme['text_muted']} hover:opacity-70 transition">Terms of Service</a></li>
                                <li><a href="mailto:hello@example.com" class="{self.theme['text_muted']} hover:opacity-70 transition">Contact</a></li>
                            </ul>
                        </div>
                    </div>
                    <div class="border-t {self.theme['border']} pt-6 flex flex-col md:flex-row justify-between items-center gap-4">
                        <p class="{self.theme['text_light']} text-xs">&copy; 2026 {self.name}. All rights reserved.</p>
                        <p class="{self.theme['text_light']} text-xs">v{self.version}</p>
                    </div>
                </div>
            </footer>"""
        except Exception as e:
            logger.error(f"footer error: {e}")
            return f"<footer class='py-8 text-center text-sm text-gray-500'>&copy; 2026 {self.name}</footer>"

    def build(self) -> Dict[str, Any]:
        try:
            self.data = self.get_ai_payload()
            keywords = self.data.get('unsplash_keywords', ['business', 'team', 'modern'])
            self.images = _get_img_set(keywords, count=6)

            sections = [
                self.render_nav(),
                self.render_hero(),
                self.render_trust_band(),
                self.render_features(),
                self.render_pricing(),
                self.render_testimonials(),
                self.render_faq(),
                self.render_cta_section(),
                self.render_footer(),
            ]

            animations_css = """
                @keyframes fadeInUp {
                    from { opacity: 0; transform: translateY(24px); }
                    to   { opacity: 1; transform: translateY(0); }
                }
                @keyframes floatY {
                    0%, 100% { transform: translateY(0); }
                    50%       { transform: translateY(-10px); }
                }
                section > .container { animation: fadeInUp 0.8s ease-out; }
                details > summary::-webkit-details-marker { display: none; }
            """

            html = f"""<!DOCTYPE html>
<html lang="en" style="scroll-behavior: smooth;">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{self.name}</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link rel="stylesheet" href="{self.theme['font_url']}">
    <style>
        *, *::before, *::after {{ box-sizing: border-box; }}
        body {{ font-family: {self.theme['fonts']}; }}
        {animations_css}
    </style>
</head>
<body class="{self.theme['bg']} {self.theme['text']}">
    {"".join(sections)}
</body>
</html>"""

            logger.info(f"Website built: {self.name}, industry={self.industry}, theme={self.theme['id']}")
            return {
                "html": html,
                "metadata": {
                    "business_name": self.name,
                    "industry": self.industry,
                    "theme": self.theme["id"],
                    "version": self.version,
                    "hero_variant": self._pick_hero_variant().__name__,
                    "feature_variant": self._pick_feature_variant().__name__,
                    "status": "success",
                }
            }
        except Exception as e:
            logger.error(f"Build error: {e}\n{traceback.format_exc()}")
            return {
                "html": f"<html><body><h1>Build Error</h1><p>{e}</p></body></html>",
                "metadata": {"status": "error", "error": str(e)}
            }


# ============================================================================
# PUBLIC API
# ============================================================================

def generate_ai_plan(ai_input: Dict[str, Any], version: int = 1, **kwargs) -> Dict[str, Any]:
    """
    Main entry point for website generation.
    Args:
        ai_input: {"business_name": str, "prompt": str}
        version:  API version
    Returns:
        {"html": str, "metadata": dict}
    """
    try:
        business_name = ai_input.get("business_name", "Business")
        prompt = ai_input.get("prompt", "")
        logger.info(f"generate_ai_plan: business_name={business_name}")
        architect = MasterArchitect(business_name, prompt, version=version)
        return architect.build()
    except Exception as e:
        logger.error(f"generate_ai_plan error: {e}\n{traceback.format_exc()}")
        return {
            "html": f"<html><body><h1>Error</h1><p>{e}</p></body></html>",
            "metadata": {"status": "error", "error": str(e)}
        }


def rewrite_content(original_text: str, tone: str = "professional", business_context: str = "") -> List[str]:
    """Return 3 rewrites of original_text using AI, with fallback."""
    if not AI_AVAILABLE:
        return [original_text] * 3
    try:
        system = "You are a world-class copywriter. Output ONLY valid JSON — no preamble."
        user = (
            f"Rewrite this text exactly 3 times in a '{tone}' tone for context: '{business_context}'.\n"
            f"Text: '{original_text}'\n"
            f'Output a JSON array: ["version1", "version2", "version3"]'
        )
        res = chat_completion(system=system, user=user, temperature=0.8)
        result = json.loads(res.strip().replace("```json", "").replace("```", ""))
        return result if isinstance(result, list) and len(result) >= 3 else [original_text] * 3
    except Exception as e:
        logger.warning(f"rewrite_content error: {e}")
        return [original_text] * 3


def get_design_tokens() -> Dict[str, Any]:
    """Export design tokens for external consumption."""
    return {
        "themes": THEMES,
        "spacing": {"section": PADDING_SECTION, "container": PADDING_CONTAINER},
        "typography": {
            "hero": HEADING_HERO,
            "hero_alt": HEADING_HERO_ALT,
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