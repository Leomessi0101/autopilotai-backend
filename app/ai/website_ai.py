"""
website_ai.py  —  AutopilotAI Master Generator v4
==========================================================
DESIGN PHILOSOPHY:
  - One continuous canvas. No hard section breaks, no alternating bg colors.
  - Every section bleeds into the next via spacing + subtle gradient overlays.
  - Typography-first: font choice defines the entire personality.
  - Each industry gets its OWN color system — never generic purple.
  - AI content is hyper-specific: wrong generic copy = reject and retry.
  - Pricing only rendered when AI returns real, populated pricing data.
  - Business name ALWAYS from self.name — never from prompt or AI copy.

CSS RULES (non-negotiable):
  - Zero Tailwind. Zero external CSS frameworks.
  - All colors via CSS custom properties on :root.
  - Google Fonts via <link> only.
  - Scripts are vanilla JS only, executed after injection.
"""

import json
import logging
import re
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

try:
    from app.ai.openai_client import chat_completion
    AI_AVAILABLE = True
except ImportError as e:
    logger.warning(f"AI client not available: {e}")
    AI_AVAILABLE = False

    def chat_completion(system: str, user: str, temperature: float = 0.7) -> str:
        return json.dumps(_generic_fallback_data())


# =============================================================================
# THEME SYSTEM
# Each theme is a complete design token set. No hardcoded hex anywhere in HTML.
# Industry → theme mapping is intentional and researched.
# =============================================================================

THEMES: Dict[str, Dict] = {

    # ── SLATE — Refined neutrals, corporate trust ─────────────────────────
    "slate": {
        "id": "slate", "mode": "light",
        "font_heading": "'Playfair Display', Georgia, serif",
        "font_body": "'DM Sans', -apple-system, sans-serif",
        "font_url": "https://fonts.googleapis.com/css2?family=Playfair+Display:wght@600;700;800&family=DM+Sans:opsz,wght@9..40,400;9..40,500;9..40,600&display=swap",
        "vars": {
            "--bg":        "#fafaf9",
            "--bg2":       "#f4f4f2",
            "--surface":   "#ffffff",
            "--border":    "#e5e3df",
            "--text":      "#1a1917",
            "--text2":     "#57534e",
            "--text3":     "#a8a29e",
            "--accent":    "#1c1917",
            "--accent2":   "#44403c",
            "--accent-r":  "28,25,23",
            "--cta":       "#1c1917",
            "--cta-text":  "#fafaf9",
            "--tag-bg":    "#f0efed",
            "--tag-text":  "#44403c",
            "--tag-border":"#ddd9d4",
            "--glow":      "rgba(28,25,23,0.04)",
            "--nav-bg":    "rgba(250,250,249,0.94)",
        },
    },

    # ── OCEAN — Deep trust, precision, finance/legal/SaaS ─────────────────
    "ocean": {
        "id": "ocean", "mode": "light",
        "font_heading": "'Sora', -apple-system, sans-serif",
        "font_body": "'Sora', -apple-system, sans-serif",
        "font_url": "https://fonts.googleapis.com/css2?family=Sora:wght@400;500;600;700;800&display=swap",
        "vars": {
            "--bg":        "#f8faff",
            "--bg2":       "#eef2ff",
            "--surface":   "#ffffff",
            "--border":    "#dde3f0",
            "--text":      "#0f1629",
            "--text2":     "#3d4a6b",
            "--text3":     "#8895b3",
            "--accent":    "#2355e8",
            "--accent2":   "#1a3ebf",
            "--accent-r":  "35,85,232",
            "--cta":       "#2355e8",
            "--cta-text":  "#ffffff",
            "--tag-bg":    "#eef2ff",
            "--tag-text":  "#2355e8",
            "--tag-border":"#c5d0f5",
            "--glow":      "rgba(35,85,232,0.06)",
            "--nav-bg":    "rgba(248,250,255,0.95)",
        },
    },

    # ── FOREST — Organic, wellness, health, nature ────────────────────────
    "forest": {
        "id": "forest", "mode": "light",
        "font_heading": "'Lora', Georgia, serif",
        "font_body": "'Plus Jakarta Sans', -apple-system, sans-serif",
        "font_url": "https://fonts.googleapis.com/css2?family=Lora:wght@500;600;700&family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap",
        "vars": {
            "--bg":        "#f9faf4",
            "--bg2":       "#f0f4e8",
            "--surface":   "#ffffff",
            "--border":    "#d8e4c4",
            "--text":      "#1a2612",
            "--text2":     "#3d5229",
            "--text3":     "#7a9260",
            "--accent":    "#2d6a2d",
            "--accent2":   "#1f4e1f",
            "--accent-r":  "45,106,45",
            "--cta":       "#2d6a2d",
            "--cta-text":  "#ffffff",
            "--tag-bg":    "#e8f0d8",
            "--tag-text":  "#2d6a2d",
            "--tag-border":"#c2d9a0",
            "--glow":      "rgba(45,106,45,0.06)",
            "--nav-bg":    "rgba(249,250,244,0.94)",
        },
    },

    # ── EMBER — Warm, food, hospitality, events ───────────────────────────
    "ember": {
        "id": "ember", "mode": "light",
        "font_heading": "'Cormorant Garamond', Georgia, serif",
        "font_body": "'Outfit', -apple-system, sans-serif",
        "font_url": "https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@500;600;700&family=Outfit:wght@400;500;600&display=swap",
        "vars": {
            "--bg":        "#fdf8f3",
            "--bg2":       "#f7ede0",
            "--surface":   "#fffcf9",
            "--border":    "#e8d5be",
            "--text":      "#1e130a",
            "--text2":     "#6b4423",
            "--text3":     "#b07a50",
            "--accent":    "#c2440f",
            "--accent2":   "#9e3508",
            "--accent-r":  "194,68,15",
            "--cta":       "#c2440f",
            "--cta-text":  "#ffffff",
            "--tag-bg":    "#fce8d8",
            "--tag-text":  "#9e3508",
            "--tag-border":"#e8c4a0",
            "--glow":      "rgba(194,68,15,0.06)",
            "--nav-bg":    "rgba(253,248,243,0.95)",
        },
    },

    # ── NOIR — Dark luxury, premium, beauty, high-end ─────────────────────
    "noir": {
        "id": "noir", "mode": "dark",
        "font_heading": "'Cormorant Garamond', Georgia, serif",
        "font_body": "'DM Sans', -apple-system, sans-serif",
        "font_url": "https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@400;500;600;700&family=DM+Sans:opsz,wght@9..40,400;9..40,500&display=swap",
        "vars": {
            "--bg":        "#0a0a09",
            "--bg2":       "#111110",
            "--surface":   "#161614",
            "--border":    "rgba(255,255,255,0.08)",
            "--text":      "#f5f0e8",
            "--text2":     "#a09880",
            "--text3":     "#5a5448",
            "--accent":    "#c9a96e",
            "--accent2":   "#a8884e",
            "--accent-r":  "201,169,110",
            "--cta":       "#c9a96e",
            "--cta-text":  "#0a0a09",
            "--tag-bg":    "rgba(201,169,110,0.08)",
            "--tag-text":  "#c9a96e",
            "--tag-border":"rgba(201,169,110,0.18)",
            "--glow":      "rgba(201,169,110,0.06)",
            "--nav-bg":    "rgba(10,10,9,0.92)",
        },
    },

    # ── VOID — Dark tech, SaaS, AI, developer tools ───────────────────────
    "void": {
        "id": "void", "mode": "dark",
        "font_heading": "'Space Grotesk', -apple-system, sans-serif",
        "font_body": "'Inter', -apple-system, sans-serif",
        "font_url": "https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;600;700&family=Inter:wght@400;500;600&display=swap",
        "vars": {
            "--bg":        "#060608",
            "--bg2":       "#0c0c10",
            "--surface":   "#10101a",
            "--border":    "rgba(120,120,255,0.10)",
            "--text":      "#e8e8f4",
            "--text2":     "#8888aa",
            "--text3":     "#444466",
            "--accent":    "#6c63ff",
            "--accent2":   "#4f46e5",
            "--accent-r":  "108,99,255",
            "--cta":       "#6c63ff",
            "--cta-text":  "#ffffff",
            "--tag-bg":    "rgba(108,99,255,0.10)",
            "--tag-text":  "#9d97ff",
            "--tag-border":"rgba(108,99,255,0.20)",
            "--glow":      "rgba(108,99,255,0.08)",
            "--nav-bg":    "rgba(6,6,8,0.92)",
        },
    },

    # ── STEEL — Industrial, construction, trades, automotive ──────────────
    "steel": {
        "id": "steel", "mode": "light",
        "font_heading": "'Barlow Condensed', -apple-system, sans-serif",
        "font_body": "'Barlow', -apple-system, sans-serif",
        "font_url": "https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@600;700;800&family=Barlow:wght@400;500;600&display=swap",
        "vars": {
            "--bg":        "#f7f8fa",
            "--bg2":       "#eceef2",
            "--surface":   "#ffffff",
            "--border":    "#d0d4dc",
            "--text":      "#111318",
            "--text2":     "#3a4050",
            "--text3":     "#8890a4",
            "--accent":    "#e84118",
            "--accent2":   "#c4310e",
            "--accent-r":  "232,65,24",
            "--cta":       "#e84118",
            "--cta-text":  "#ffffff",
            "--tag-bg":    "#fde8e4",
            "--tag-text":  "#c4310e",
            "--tag-border":"#f5c4bb",
            "--glow":      "rgba(232,65,24,0.05)",
            "--nav-bg":    "rgba(247,248,250,0.95)",
        },
    },

    # ── ROSE — Beauty, skincare, wellness spa ─────────────────────────────
    "rose": {
        "id": "rose", "mode": "light",
        "font_heading": "'Fraunces', Georgia, serif",
        "font_body": "'Jost', -apple-system, sans-serif",
        "font_url": "https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,600;9..144,700&family=Jost:wght@400;500;600&display=swap",
        "vars": {
            "--bg":        "#fdf8f8",
            "--bg2":       "#f9f0f0",
            "--surface":   "#ffffff",
            "--border":    "#f0d8d8",
            "--text":      "#1e0e0e",
            "--text2":     "#6b3a3a",
            "--text3":     "#b08080",
            "--accent":    "#b83c5a",
            "--accent2":   "#962e47",
            "--accent-r":  "184,60,90",
            "--cta":       "#b83c5a",
            "--cta-text":  "#ffffff",
            "--tag-bg":    "#fce8ec",
            "--tag-text":  "#962e47",
            "--tag-border":"#f0c0cc",
            "--glow":      "rgba(184,60,90,0.05)",
            "--nav-bg":    "rgba(253,248,248,0.95)",
        },
    },
}

# =============================================================================
# INDUSTRY → THEME MAPPING
# =============================================================================

INDUSTRY_THEME: Dict[str, str] = {
    "saas":         "void",
    "ai":           "void",
    "developer":    "void",
    "startup":      "void",
    "finance":      "ocean",
    "legal":        "slate",
    "real_estate":  "slate",
    "logistics":    "steel",
    "construction": "steel",
    "automotive":   "steel",
    "restaurant":   "ember",
    "food":         "ember",
    "events":       "ember",
    "travel":       "ember",
    "health":       "forest",
    "fitness":      "forest",
    "nature":       "forest",
    "nonprofit":    "forest",
    "education":    "ocean",
    "agency":       "noir",
    "luxury":       "noir",
    "beauty":       "rose",
    "ecommerce":    "ocean",
    "cleaning":     "forest",
}

# =============================================================================
# INDUSTRY DETECTION
# =============================================================================

INDUSTRY_KEYWORDS: Dict[str, List[str]] = {
    # Cleaning gets top priority — very specific keywords so it never misdetects
    "cleaning":     ["cleaning", "cleaner", "clean", "maid", "housekeeping", "janitor", "janitorial",
                     "spotless", "scrub", "vacuum", "dust", "mop", "sanitize", "disinfect",
                     "tidy", "sweep", "laundry", "windows cleaning", "deep clean", "spring clean",
                     "move out clean", "move in clean", "office cleaning", "commercial cleaning"],
    "construction": ["construction", "contractor", "builder", "renovation", "remodel", "plumbing",
                     "electrical", "roofing", "flooring", "masonry", "carpentry", "landscaping",
                     "painting", "hvac", "handyman", "concrete", "drywall", "framing", "tiling",
                     "deck", "fence", "waterproofing", "insulation", "general contractor"],
    "restaurant":   ["restaurant", "food", "cafe", "bakery", "catering", "cuisine", "dining",
                     "menu", "chef", "bar", "bistro", "eatery", "takeout", "delivery food",
                     "coffee shop", "pizzeria", "sushi", "burger", "taco", "brunch", "kitchen"],
    "health":       ["health", "medical", "wellness", "clinic", "doctor", "hospital", "therapy",
                     "nutrition", "physio", "chiropractic", "dentist", "mental health", "counseling",
                     "psychology", "psychiatry", "optometry", "dermatology", "pediatric"],
    "fitness":      ["fitness", "gym", "personal trainer", "workout", "yoga", "crossfit",
                     "athletics", "exercise", "pilates", "bootcamp", "martial arts", "boxing",
                     "swimming", "running", "cycling", "weight loss", "strength training"],
    "beauty":       ["beauty", "salon", "spa", "skincare", "cosmetic", "makeup", "aesthetics",
                     "bridal", "hair", "nail", "waxing", "lash", "brow", "facial", "massage",
                     "manicure", "pedicure", "barbershop", "tanning", "tattoo"],
    "saas":         ["software", "app", "platform", "cloud", "api", "saas", "dashboard",
                     "workflow", "automation", "crm", "subscription", "b2b software", "tool"],
    "ai":           ["artificial intelligence", "machine learning", "neural", "llm", "gpt",
                     "data science", "deep learning", "computer vision", "nlp", "ai model"],
    "developer":    ["developer", "engineer", "code", "open source", "github", "devtools",
                     "ide", "terminal", "cli", "programming", "web development", "mobile app"],
    "startup":      ["startup", "founder", "seed", "venture", "mvp", "launch", "pitch", "scale"],
    "finance":      ["finance", "banking", "investment", "crypto", "payment", "fintech",
                     "trading", "insurance", "wealth", "accounting", "tax", "advisor", "bookkeeping"],
    "legal":        ["law", "lawyer", "attorney", "legal", "firm", "counsel", "litigation",
                     "contract", "court", "compliance", "notary", "paralegal"],
    "real_estate":  ["real estate", "property", "realty", "housing", "apartment", "mortgage",
                     "agent", "broker", "home buying", "home selling", "rental"],
    "logistics":    ["logistics", "shipping", "freight", "delivery", "supply chain", "warehouse",
                     "trucking", "transport", "courier", "moving company", "relocation"],
    "automotive":   ["auto", "car", "vehicle", "mechanic", "garage", "dealership", "repair",
                     "tire", "bodywork", "detailing", "oil change", "transmission", "brake"],
    "events":       ["event", "wedding", "conference", "venue", "entertainment", "party",
                     "corporate event", "photography", "videography", "dj", "florist", "catering"],
    "travel":       ["travel", "hotel", "tour", "booking", "vacation", "resort", "hospitality",
                     "airbnb", "bed and breakfast", "tourism", "cruise"],
    "nature":       ["organic", "eco", "sustainable", "farm", "agriculture", "environment",
                     "garden", "zero waste", "green energy", "solar", "recycling"],
    "nonprofit":    ["nonprofit", "charity", "foundation", "ngo", "volunteer", "donation",
                     "cause", "community", "social impact", "humanitarian"],
    "education":    ["education", "course", "learn", "training", "school", "university",
                     "tutoring", "edtech", "bootcamp", "coaching", "mentoring", "workshop"],
    "agency":       ["agency", "design", "creative", "marketing", "brand", "advertising",
                     "studio", "media", "social media", "seo", "pr agency", "copywriting"],
    "luxury":       ["luxury", "high-end", "exclusive", "bespoke", "couture", "prestige",
                     "elite", "premium", "concierge", "vip"],
    "ecommerce":    ["shop", "store", "ecommerce", "e-commerce", "sell", "product", "cart",
                     "marketplace", "retail", "dropshipping", "merch"],
}

def detect_industry(text: str) -> str:
    tl = (text or "").lower()
    scores: Dict[str, int] = {}
    for ind, kws in INDUSTRY_KEYWORDS.items():
        score = 0
        for kw in kws:
            if kw in tl:
                # Multi-word keywords score higher — "deep clean" beats "clean"
                score += len(kw.split()) * 2
        scores[ind] = score
    best = max(scores, key=lambda k: scores[k])
    # Only use detected industry if score is meaningful
    return best if scores[best] > 0 else "construction"  # Default to something generic, not AI

# =============================================================================
# PHOTO SYSTEM — verified Unsplash photo IDs per industry
# Uses direct images.unsplash.com URLs which are stable and always work.
# IDs are manually curated and verified to match each industry.
# Each industry has 6+ photos so different slots get different images.
# =============================================================================

INDUSTRY_PHOTOS: Dict[str, List[str]] = {
    "cleaning":     [
        "photo-1581578731548-c64695cc6952",  # person cleaning surface
        "photo-1558618666-fcd25c85cd64",     # cleaning spray bottle
        "photo-1527515545081-5db817172677",  # clean bright kitchen
        "photo-1584820927498-cfe5211fd8bf",  # cleaning gloves
        "photo-1628177142898-93e36e4e3a50",  # mopping floor
        "photo-1563453392212-326f5e854473",  # vacuuming carpet
    ],
    "construction": [
        "photo-1504307651254-35680f356dfd",  # construction site workers
        "photo-1541888946425-d81bb19240f5",  # building frame structure
        "photo-1503387762-592deb58ef4e",     # architect plans blueprint
        "photo-1565117623394-5f93fd4c7a06",  # construction tools
        "photo-1487958449943-2429e8be8625",  # modern building exterior
        "photo-1530836176759-510f6ca9f76f",  # renovation interior
    ],
    "restaurant":   [
        "photo-1414235077428-338989a2e8c0",  # restaurant interior warm
        "photo-1555396273-367ea4eb4db5",     # plated food fine dining
        "photo-1517248135467-4c7edcad34c4",  # restaurant atmosphere
        "photo-1504674900247-0877df9cc836",  # food overhead shot
        "photo-1467003909585-2f8a72700288",  # coffee shop
        "photo-1424847651672-bf20a4b0982b",  # chef cooking
    ],
    "health":       [
        "photo-1576091160550-2173dba999ef",  # doctor consultation
        "photo-1519494026892-80bbd2d6fd0d",  # hospital corridor bright
        "photo-1571772996211-2f02c9727629",  # medical professional
        "photo-1631217868264-e5b90bb7e133",  # clinic interior modern
        "photo-1559757148-5c350d0d3c56",     # health wellness
        "photo-1582750433449-648ed127bb54",  # doctor smiling
    ],
    "fitness":      [
        "photo-1534438327276-14e5300c3a48",  # gym equipment
        "photo-1571019613454-1cb2f99b2d8b",  # personal trainer
        "photo-1549060279-7e168fcee0c2",     # workout session
        "photo-1517836357463-d25dfeac3438",  # weights gym
        "photo-1574680096145-d05b474e2155",  # fitness class
        "photo-1526506118085-60ce8714f8c5",  # running shoes
    ],
    "beauty":       [
        "photo-1560066984-138dadb4c035",     # salon interior
        "photo-1487412947147-5cebf100ffc2",  # makeup beauty
        "photo-1522337360788-8b13dee7a37e",  # spa treatment
        "photo-1571019613576-2b22c76fd955",  # skincare products
        "photo-1470259078422-826894b933aa",  # beauty portrait
        "photo-1453614512568-c4024d13c247",  # nail salon
    ],
    "legal":        [
        "photo-1589578527966-fdac0f44566c",  # law books desk
        "photo-1505664194779-8beaceb5c7c7",  # lawyer office
        "photo-1450101499163-c8848c66ca85",  # legal documents
        "photo-1521791055366-0d553872952f",  # handshake agreement
        "photo-1423592707957-3b212afa6733",  # justice scales
        "photo-1507679799987-c73779587ccf",  # professional suit
    ],
    "finance":      [
        "photo-1460925895917-afdab827c52f",  # finance charts
        "photo-1611974789855-9c2a0a7236a3",  # stock market
        "photo-1454165804606-c3d57bc86b40",  # business meeting
        "photo-1468254095679-bbcba94a7066",  # city financial district
        "photo-1579621970563-ebec7560ff3e",  # financial planning
        "photo-1559526324-593bc073d938",     # money investment
    ],
    "real_estate":  [
        "photo-1560518883-ce09059eeffa",     # modern house exterior
        "photo-1570129477492-45c003edd2be",  # beautiful home
        "photo-1501183638710-841dd1904471",  # interior living room
        "photo-1486325212027-8081e485255e",  # house for sale
        "photo-1512917774080-9991f1c4c750",  # luxury home
        "photo-1583608205776-bfd35f0d9f83",  # kitchen renovation
    ],
    "automotive":   [
        "photo-1492144534655-ae79c964c9d7",  # car detail shot
        "photo-1503376780353-7e6692767b70",  # car in garage
        "photo-1558618666-fcd25c85cd64",     # mechanic working
        "photo-1486262715619-67b85e0b08d3",  # car engine
        "photo-1568605117036-5fe5e7bab0b7",  # modern car
        "photo-1552519507-da3b142c6e3d",     # sports car
    ],
    "logistics":    [
        "photo-1586528116311-ad8dd3c8310d",  # warehouse
        "photo-1601584115197-04ecc0da31d7",  # delivery truck
        "photo-1494412574643-ff11b0a5c1c3",  # shipping containers
        "photo-1504493188-45c49f65c6ba",     # supply chain
        "photo-1530521954074-e64f6810b32d",  # logistics aerial
        "photo-1577705998148-6da4f3963bc8",  # packages sorting
    ],
    "events":       [
        "photo-1540575467063-178a50c2df87",  # event venue
        "photo-1511795409834-ef04bbd61622",  # conference room
        "photo-1464366400600-7168b8af9bc3",  # wedding reception
        "photo-1519167758481-83f550bb49b3",  # party celebration
        "photo-1505236858219-8359eb29e329",  # stage lights concert
        "photo-1472653431158-6364773b2a56",  # gala dinner
    ],
    "travel":       [
        "photo-1476514525535-07fb3b4ae5f1",  # travel destination
        "photo-1501854140801-50d01698950b",  # scenic landscape
        "photo-1488085061387-422e29b40080",  # hotel resort
        "photo-1530521954074-e64f6810b32d",  # aerial view travel
        "photo-1469474968028-56623f02e42e",  # nature travel
        "photo-1433838552652-f9a46b332c40",  # beach resort
    ],
    "education":    [
        "photo-1503676260728-1c00da094a0b",  # classroom
        "photo-1456513080510-7bf3a84b82f8",  # library books
        "photo-1522202176988-66273c2fd55f",  # students learning
        "photo-1434030216411-0b793f4b4173",  # studying laptop
        "photo-1524178232363-1fb2b075b655",  # lecture hall
        "photo-1509062522246-3755977927d7",  # chalkboard
    ],
    "saas":         [
        "photo-1551434678-e076c223a692",     # team working tech
        "photo-1497366216548-37526070297c",  # modern office
        "photo-1518770660439-4636190af475",  # circuit board tech
        "photo-1461749280684-dccba630e2f6",  # coding laptop
        "photo-1519389950473-47ba0277781c",  # tech workspace
        "photo-1531482615713-2afd69097998",  # team collaboration
    ],
    "ai":           [
        "photo-1620712943543-bcc4688e7485",  # AI concept
        "photo-1677442135703-1787eea5ce01",  # AI neural network
        "photo-1593508512255-86ab42a8e620",  # futuristic tech
        "photo-1518770660439-4636190af475",  # circuit board
        "photo-1485827404703-89b55fcc595e",  # robot technology
        "photo-1507146153580-69a1fe6d8aa1",  # data visualization
    ],
    "developer":    [
        "photo-1461749280684-dccba630e2f6",  # coding screen
        "photo-1498050108023-c5249f4df085",  # laptop code
        "photo-1555066931-4365d14bab8c",     # code dark screen
        "photo-1607799279861-4dd421887fb3",  # developer workspace
        "photo-1516116216624-53e697fedbea",  # multiple monitors
        "photo-1571171637578-41bc2dd41cd2",  # coding close up
    ],
    "agency":       [
        "photo-1497366754035-f200968a6e72",  # creative office
        "photo-1524758631624-e2822e304c36",  # design studio
        "photo-1542744173-8e7e53415bb0",     # whiteboard meeting
        "photo-1558655146-9f40138edfeb",     # creative team
        "photo-1522071820081-009f0129c71c",  # team brainstorm
        "photo-1600880292089-90a7e086ee0c",  # agency workspace
    ],
    "nature":       [
        "photo-1441974231531-c6227db76b6e",  # forest nature
        "photo-1469474968028-56623f02e42e",  # green landscape
        "photo-1518173946687-a4c8892bbd9f",  # organic farm
        "photo-1540979388789-6cee28a1cdc9",  # eco products
        "photo-1504309092620-4d0ec726efa4",  # sustainable garden
        "photo-1416879595882-3373a0480b5b",  # flowers nature
    ],
    "nonprofit":    [
        "photo-1488521787991-ed7bbaae773c",  # volunteers hands
        "photo-1593113630400-ea4288922559",  # community helping
        "photo-1532629345422-7515f3d16bb6",  # charity event
        "photo-1491438590914-bc09fcaaf77a",  # people community
        "photo-1469571486292-0ba58a3f068b",  # volunteer work
        "photo-1559027615-cd4628902d4a",     # donation charity
    ],
    "luxury":       [
        "photo-1519501025264-65ba15a82390",  # luxury interior
        "photo-1549298916-b41d501d3772",     # premium product
        "photo-1441984904996-e0b6ba687e04",  # luxury fashion
        "photo-1582719508461-905c673771fd",  # luxury hotel
        "photo-1567016432779-094069958ea5",  # penthouse view
        "photo-1617103996702-96ff29b1c467",  # fine dining luxury
    ],
    "startup":      [
        "photo-1553877522-43269d4ea984",     # startup team
        "photo-1497366811353-6870744d04b2",  # modern coworking
        "photo-1556761175-4b46a572b786",     # startup office
        "photo-1504384308090-c894fdcc538d",  # open office
        "photo-1600880292203-757bb62b4baf",  # team meeting
        "photo-1559136555-9303baea8ebd",     # entrepreneur laptop
    ],
    "ecommerce":    [
        "photo-1556742049-0cfed4f6a45d",     # online shopping
        "photo-1472851294608-062f824d29cc",  # retail store
        "photo-1523275335684-37898b6baf30",  # product watch
        "photo-1526170375885-4d8ecf77b99f",  # flatlay products
        "photo-1585386959984-a4155224a1ad",  # packaging delivery
        "photo-1491553895911-0055eca6402d",  # product display
    ],
}

_DEFAULT_PHOTOS = [
    "photo-1497366216548-37526070297c",  # office professional
    "photo-1454165804606-c3d57bc86b40",  # business meeting
    "photo-1522202176988-66273c2fd55f",  # people working
    "photo-1542744173-8e7e53415bb0",     # whiteboard collaboration
]

def _photo(industry: str, idx: int, w: int = 1200) -> str:
    """Return a verified Unsplash photo URL for the given industry and slot index."""
    pool = INDUSTRY_PHOTOS.get(industry, _DEFAULT_PHOTOS)
    pid  = pool[idx % len(pool)]
    return f"https://images.unsplash.com/{pid}?w={w}&auto=format&fit=crop&q=80"

# =============================================================================
# CSS ENGINE — generates the complete stylesheet from theme tokens
# =============================================================================

def _build_css(t: Dict) -> str:
    vars_block = "\n".join(f"  {k}: {v};" for k, v in t["vars"].items())
    is_dark    = t["mode"] == "dark"
    
    shadow_sm  = "0 1px 3px rgba(0,0,0,0.08), 0 1px 2px rgba(0,0,0,0.05)" if not is_dark else "0 1px 3px rgba(0,0,0,0.4)"
    shadow_md  = "0 4px 16px rgba(0,0,0,0.08), 0 1px 4px rgba(0,0,0,0.04)" if not is_dark else "0 4px 16px rgba(0,0,0,0.5)"
    shadow_lg  = "0 20px 60px rgba(0,0,0,0.10), 0 4px 16px rgba(0,0,0,0.06)" if not is_dark else "0 20px 60px rgba(0,0,0,0.6)"

    return f"""<style>
/* ── Reset & base ── */
*,*::before,*::after{{box-sizing:border-box;margin:0;padding:0}}
:root{{
{vars_block}
}}
html{{
  font-family:{t['font_body']};
  background:var(--bg);
  color:var(--text);
  scroll-behavior:smooth;
  -webkit-font-smoothing:antialiased;
  -moz-osx-font-smoothing:grayscale;
}}
body{{background:var(--bg);color:var(--text);overflow-x:hidden;line-height:1.6}}
img{{display:block;max-width:100%;height:auto}}
a{{color:inherit;text-decoration:none}}
button,input,textarea,select{{font-family:inherit}}
button{{cursor:pointer;border:none;background:none}}

/* ── Typography ── */
.h-display{{
  font-family:{t['font_heading']};
  font-size:clamp(2.8rem,6vw,5.5rem);
  font-weight:700;
  letter-spacing:-0.03em;
  line-height:1.06;
  color:var(--text);
}}
.h-section{{
  font-family:{t['font_heading']};
  font-size:clamp(2rem,3.5vw,3rem);
  font-weight:700;
  letter-spacing:-0.025em;
  line-height:1.15;
  color:var(--text);
}}
.h-card{{
  font-family:{t['font_heading']};
  font-size:1.1rem;
  font-weight:600;
  letter-spacing:-0.01em;
  color:var(--text);
  line-height:1.3;
}}
.eyebrow{{
  display:inline-block;
  font-size:0.65rem;
  font-weight:700;
  text-transform:uppercase;
  letter-spacing:0.2em;
  color:var(--accent);
  margin-bottom:1rem;
}}
.body-lg{{font-size:1.125rem;line-height:1.72;color:var(--text2)}}
.body-md{{font-size:0.9875rem;line-height:1.68;color:var(--text2)}}
.body-sm{{font-size:0.85rem;line-height:1.65;color:var(--text2)}}

/* ── Layout ── */
.wrap{{width:100%;max-width:1140px;margin:0 auto;padding:0 1.5rem}}
@media(min-width:768px){{.wrap{{padding:0 2.5rem}}}}

/* All sections share ONE background — flow is achieved via spacing only */
.sec{{position:relative;padding:6rem 0}}
.sec-hero{{position:relative;padding:5rem 0 4rem}}
.sec-sm{{position:relative;padding:3.5rem 0}}
@media(min-width:768px){{
  .sec{{padding:8rem 0}}
  .sec-hero{{padding:7rem 0 5rem;min-height:88vh;display:flex;align-items:center}}
}}
@media(max-width:767px){{
  .sec{{padding:4.5rem 0}}
  .sec-hero{{padding:4rem 0 3rem;min-height:auto}}
}}

/* Subtle band — pure overlay tint, never a hard bg change */
.band::before{{
  content:'';
  position:absolute;
  inset:0;
  background:linear-gradient(180deg,
    transparent 0%,
    rgba(var(--accent-r),0.028) 30%,
    rgba(var(--accent-r),0.028) 70%,
    transparent 100%
  );
  pointer-events:none;
}}

/* ── Grid ── */
.g2{{display:grid;grid-template-columns:1fr;gap:2rem}}
.g3{{display:grid;grid-template-columns:1fr;gap:1.5rem}}
.g4{{display:grid;grid-template-columns:repeat(2,1fr);gap:1.25rem}}
@media(min-width:600px){{.g3{{grid-template-columns:repeat(2,1fr)}}}}
@media(min-width:900px){{
  .g2{{grid-template-columns:1fr 1fr;gap:3rem}}
  .g3{{grid-template-columns:repeat(3,1fr)}}
  .g4{{grid-template-columns:repeat(4,1fr)}}
}}
.ai{{align-items:center}}
.gap-xl{{gap:5rem}}

/* ── Utilities ── */
.tc{{text-align:center}}
.rel{{position:relative}}
.z1{{position:relative;z-index:1}}
.mx-auto{{margin-left:auto;margin-right:auto}}
.mw-xs{{max-width:28rem}}
.mw-sm{{max-width:36rem}}
.mw-md{{max-width:50rem}}
.mw-lg{{max-width:68rem}}
.flex{{display:flex}}.flex-col{{flex-direction:column}}.flex-wrap{{flex-wrap:wrap}}
.gap1{{gap:0.5rem}}.gap2{{gap:0.75rem}}.gap3{{gap:1rem}}.gap4{{gap:1.5rem}}.gap5{{gap:2rem}}
.ai-c{{align-items:center}}
.mt1{{margin-top:0.5rem}}.mt2{{margin-top:1rem}}.mt3{{margin-top:1.5rem}}
.mt4{{margin-top:2rem}}.mt5{{margin-top:2.5rem}}.mt6{{margin-top:3rem}}
.mb1{{margin-bottom:0.5rem}}.mb2{{margin-bottom:1rem}}.mb3{{margin-bottom:1.5rem}}
.mb4{{margin-bottom:2rem}}.mb5{{margin-bottom:2.5rem}}

/* ── Ambient glow blobs — decorative only ── */
.blob{{position:absolute;border-radius:50%;filter:blur(90px);pointer-events:none;z-index:0;background:var(--glow)}}

/* ── Navigation ── */
.site-nav{{
  position:fixed;top:0;left:0;right:0;z-index:200;
  background:var(--nav-bg);
  border-bottom:1px solid var(--border);
  backdrop-filter:blur(20px);
  -webkit-backdrop-filter:blur(20px);
}}
.nav-inner{{
  display:flex;align-items:center;justify-content:space-between;
  height:64px;padding:0 1.5rem;max-width:1140px;margin:0 auto;
}}
@media(min-width:768px){{.nav-inner{{padding:0 2.5rem}}}}
.nav-logo{{
  font-family:{t['font_heading']};
  font-size:1.15rem;font-weight:700;
  letter-spacing:-0.02em;color:var(--text);
}}
.nav-links{{display:none;list-style:none;gap:2rem;align-items:center}}
@media(min-width:768px){{.nav-links{{display:flex}}}}
.nav-links a{{font-size:0.85rem;font-weight:500;color:var(--text2);transition:color 0.2s}}
.nav-links a:hover{{color:var(--text)}}
.nav-cta{{
  display:none;
  background:var(--cta);color:var(--cta-text) !important;
  font-size:0.82rem;font-weight:600;
  padding:0.5rem 1.2rem;border-radius:8px;
  transition:opacity 0.2s,transform 0.15s;
}}
.nav-cta:hover{{opacity:0.88;transform:translateY(-1px)}}
@media(min-width:768px){{.nav-cta{{display:inline-block}}}}
.hamburger{{display:flex;flex-direction:column;gap:5px;padding:6px;cursor:pointer}}
@media(min-width:768px){{.hamburger{{display:none}}}}
.hamburger span{{display:block;width:20px;height:2px;background:var(--text);border-radius:2px;transition:all 0.25s}}
.mob-menu{{
  display:none;flex-direction:column;
  position:absolute;top:64px;left:0;right:0;
  background:var(--nav-bg);border-bottom:1px solid var(--border);
  padding:0.75rem 1.5rem 1.25rem;
  backdrop-filter:blur(20px);
}}
.mob-menu.open{{display:flex}}
.mob-menu a{{
  padding:0.75rem 0;border-bottom:1px solid var(--border);
  font-size:0.9rem;font-weight:500;color:var(--text2);
}}
.mob-menu a:last-child{{border-bottom:none;color:var(--cta) !important;font-weight:700;padding-top:1rem}}

/* ── Buttons ── */
.btn{{
  display:inline-flex;align-items:center;gap:0.5rem;
  font-weight:600;font-size:0.95rem;
  padding:0.85rem 2rem;border-radius:10px;
  transition:all 0.22s cubic-bezier(.16,1,.3,1);
  cursor:pointer;text-align:center;white-space:nowrap;
}}
.btn-primary{{
  background:var(--cta);color:var(--cta-text) !important;
  border:2px solid var(--cta);
}}
.btn-primary:hover{{
  opacity:0.88;transform:translateY(-2px);
  box-shadow:0 8px 24px rgba(var(--accent-r),0.25);
}}
.btn-outline{{
  background:transparent;
  color:var(--text) !important;
  border:2px solid var(--border);
}}
.btn-outline:hover{{border-color:var(--accent);color:var(--accent) !important}}
.btn-row{{display:flex;flex-wrap:wrap;gap:0.85rem;align-items:center}}

/* ── Cards ── */
.card{{
  background:var(--surface);
  border:1px solid var(--border);
  border-radius:16px;
  box-shadow:{shadow_sm};
  transition:box-shadow 0.3s,transform 0.3s;
}}
.card:hover{{
  box-shadow:{shadow_lg};
  transform:translateY(-3px);
}}
.card-p{{padding:1.75rem}}
.card-plg{{padding:2.25rem}}

/* ── Tag / badge ── */
.tag{{
  display:inline-flex;align-items:center;gap:0.4rem;
  font-size:0.68rem;font-weight:700;
  text-transform:uppercase;letter-spacing:0.12em;
  padding:0.28rem 0.8rem;border-radius:999px;
  background:var(--tag-bg);color:var(--tag-text);
  border:1px solid var(--tag-border);
}}
.tag-dot{{
  width:6px;height:6px;border-radius:50%;
  background:var(--accent);
  animation:pulse 2.2s infinite;
}}
@keyframes pulse{{0%,100%{{opacity:1}}50%{{opacity:.35}}}}

/* ── Feature icon ── */
.feat-icon{{
  width:48px;height:48px;border-radius:12px;
  display:flex;align-items:center;justify-content:center;
  font-size:1.4rem;flex-shrink:0;margin-bottom:1rem;
  background:linear-gradient(135deg,rgba(var(--accent-r),.10),rgba(var(--accent-r),.03));
  border:1px solid rgba(var(--accent-r),.08);
}}

/* ── Stats ── */
.stat-num{{
  font-family:{t['font_heading']};
  font-size:clamp(2rem,4vw,3rem);
  font-weight:700;
  letter-spacing:-0.04em;
  color:var(--accent);
  line-height:1;
}}
.stat-label{{font-size:0.78rem;color:var(--text3);margin-top:0.3rem}}

/* ── Testimonials ── */
.testi-grid{{display:flex;gap:1.25rem;overflow-x:auto;scroll-snap-type:x mandatory;padding-bottom:0.5rem;scrollbar-width:none}}
.testi-grid::-webkit-scrollbar{{display:none}}
.testi-grid .card{{scroll-snap-align:start;flex-shrink:0;width:min(82vw,330px)}}
@media(min-width:720px){{
  .testi-grid{{display:grid;grid-template-columns:repeat(2,1fr);overflow:visible}}
  .testi-grid .card{{width:auto}}
}}
@media(min-width:1024px){{.testi-grid{{grid-template-columns:repeat(3,1fr)}}}}

/* ── Stars ── */
.stars{{color:#f59e0b;font-size:0.875rem;letter-spacing:2px;margin-bottom:0.85rem}}

/* ── Avatar ── */
.avatar{{
  width:40px;height:40px;border-radius:50%;flex-shrink:0;
  background:linear-gradient(135deg,var(--accent),var(--accent2));
  display:flex;align-items:center;justify-content:center;
  color:var(--cta-text);font-weight:700;font-size:0.85rem;
}}

/* ── Checklist ── */
.chk-list{{list-style:none;display:flex;flex-direction:column;gap:0.6rem}}
.chk-item{{display:flex;align-items:flex-start;gap:0.65rem;font-size:0.875rem;color:var(--text2)}}
.chk-mark{{
  flex-shrink:0;width:16px;height:16px;
  margin-top:2px;color:var(--accent);
  font-weight:800;font-size:0.7rem;
  display:flex;align-items:center;justify-content:center;
}}

/* ── Images ── */
.img-wrap{{border-radius:18px;overflow:hidden;box-shadow:{shadow_lg}}}
.img-fill{{width:100%;height:100%;object-fit:cover;display:block}}
.img-tall{{height:480px}}
.img-mid{{aspect-ratio:4/3}}
@media(max-width:767px){{.img-tall{{height:260px}}}}

/* ── FAQ ── */
details.faq-item{{border:1px solid var(--border);border-radius:12px;overflow:hidden;margin-bottom:0.5rem;background:var(--surface)}}
details.faq-item>summary{{
  list-style:none;display:flex;justify-content:space-between;align-items:center;
  padding:1.1rem 1.4rem;cursor:pointer;
  font-weight:600;font-size:0.9rem;color:var(--text);
  user-select:none;gap:1rem;
}}
details.faq-item>summary::-webkit-details-marker{{display:none}}
.faq-toggle{{
  flex-shrink:0;width:22px;height:22px;
  border:1px solid var(--border);border-radius:50%;
  display:flex;align-items:center;justify-content:center;
  font-size:0.9rem;color:var(--text3);transition:transform 0.2s;
}}
details.faq-item[open]>summary .faq-toggle{{transform:rotate(45deg);color:var(--accent)}}
.faq-answer{{padding:0 1.4rem 1.1rem;font-size:0.875rem;color:var(--text2);line-height:1.7;border-top:1px solid var(--border);padding-top:0.85rem}}

/* ── Contact form ── */
.form-label{{display:block;font-size:0.68rem;font-weight:700;text-transform:uppercase;letter-spacing:0.14em;color:var(--text3);margin-bottom:0.4rem}}
.form-input{{
  width:100%;padding:0.8rem 1rem;font-size:0.9rem;
  background:var(--bg);border:1px solid var(--border);
  border-radius:10px;color:var(--text);outline:none;
  transition:border-color 0.2s,box-shadow 0.2s;
}}
.form-input:focus{{border-color:var(--accent);box-shadow:0 0 0 3px rgba(var(--accent-r),.10)}}
.form-input::placeholder{{color:var(--text3)}}
textarea.form-input{{resize:none;min-height:120px}}
.form-row{{margin-bottom:1.1rem}}

/* ── Footer ── */
.site-footer{{border-top:1px solid var(--border);padding:4rem 0 2.5rem;background:var(--bg)}}

/* ── Scroll reveal ── */
.rv{{opacity:0;transform:translateY(18px);transition:opacity .65s cubic-bezier(.16,1,.3,1),transform .65s cubic-bezier(.16,1,.3,1)}}
.rv.in{{opacity:1;transform:none}}
.d1{{transition-delay:.08s}}.d2{{transition-delay:.16s}}.d3{{transition-delay:.24s}}.d4{{transition-delay:.32s}}
</style>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="{t['font_url']}">"""


REVEAL_JS = """<script>
(function(){
  var els = document.querySelectorAll('.rv');
  if (!els.length) return;
  if (window.IntersectionObserver) {
    var io = new IntersectionObserver(function(entries) {
      entries.forEach(function(e) {
        if (e.isIntersecting) { e.target.classList.add('in'); io.unobserve(e.target); }
      });
    }, { threshold: 0.08 });
    els.forEach(function(el) { io.observe(el); });
  } else {
    els.forEach(function(el) { el.classList.add('in'); });
  }
  // Mobile nav toggle
  var btn = document.getElementById('nav-toggle');
  var mob = document.getElementById('mob-menu');
  if (btn && mob) {
    btn.addEventListener('click', function() { mob.classList.toggle('open'); });
    mob.querySelectorAll('a').forEach(function(a) {
      a.addEventListener('click', function() { mob.classList.remove('open'); });
    });
  }
})();
</script>"""

# =============================================================================
# HTML PRIMITIVES
# =============================================================================

def _eyebrow(text: str) -> str:
    return f'<span class="eyebrow">{text}</span>'

def _section_header(eyebrow: str, title: str, sub: str = "", center: bool = True) -> str:
    cls  = "tc mb5 rv" if center else "mb5 rv"
    sub_html = f'<p class="body-lg mt3 mw-sm{"  mx-auto" if center else ""}">{sub}</p>' if sub else ""
    return f'<div class="{cls}">{_eyebrow(eyebrow)}<h2 class="h-section">{title}</h2>{sub_html}</div>'

def _btn(label: str, href: str = "#contact", variant: str = "primary", extra: str = "") -> str:
    return f'<a href="{href}" class="btn btn-{variant}" {extra}>{label}</a>'

def _chk(text: str) -> str:
    return f'<li class="chk-item"><span class="chk-mark">✓</span><span>{text}</span></li>'

def _stars() -> str:
    return '<div class="stars">★★★★★</div>'

# =============================================================================
# NAV
# =============================================================================

def _nav(name: str, links: List[str], cta: str) -> str:
    li_items = "".join(
        f'<li><a href="#{l.lower().replace(" ", "-")}">{l}</a></li>'
        for l in links
    )
    mob_links = "".join(
        f'<a href="#{l.lower().replace(" ", "-")}">{l}</a>'
        for l in links
    )
    mob_links += f'<a href="#contact">{cta}</a>'
    return f"""<nav class="site-nav">
  <div class="nav-inner">
    <a href="#" class="nav-logo">{name}</a>
    <ul class="nav-links">{li_items}</ul>
    <div style="display:flex;align-items:center;gap:1rem;">
      <a href="#contact" class="nav-cta">{cta}</a>
      <button class="hamburger" id="nav-toggle" aria-label="Menu">
        <span></span><span></span><span></span>
      </button>
    </div>
  </div>
  <div class="mob-menu" id="mob-menu">{mob_links}</div>
</nav>"""

# =============================================================================
# HERO SECTION — 4 variants chosen by industry
# =============================================================================

def _hero_split(name: str, d: Dict, ind: str) -> str:
    """Standard split — text left, image right. Most industries."""
    h     = d.get("hero", {})
    proof = d.get("social_proof") or {}
    img   = _photo(ind, 0, 1100)

    proof_html = ""
    if proof.get("count") and proof.get("label"):
        avs = "".join(
            f'<div style="width:26px;height:26px;border-radius:50%;background:linear-gradient(135deg,var(--accent),var(--accent2));border:2px solid var(--bg);display:flex;align-items:center;justify-content:center;color:var(--cta-text);font-size:0.58rem;font-weight:800;{"margin-left:-7px" if i else ""};">{chr(65+i)}</div>'
            for i in range(4)
        )
        proof_html = f"""<div class="flex ai-c gap3 mt4" style="padding-top:1.25rem;border-top:1px solid var(--border);">
      <div class="flex">{avs}</div>
      <span class="body-sm"><strong style="color:var(--accent)">{proof['count']}</strong> {proof['label']}</span>
    </div>"""

    return f"""<section class="sec-hero" style="padding-top:5.5rem;">
  <div class="blob" style="width:500px;height:500px;top:-15%;right:-8%;opacity:0.7;"></div>
  <div class="wrap z1">
    <div class="g2 ai gap-xl">
      <div class="rv">
        {_eyebrow(d.get("tagline", ""))}
        <h1 class="h-display mt2">{h.get("h1", f"Welcome to {name}")}</h1>
        <p class="body-lg mt4 mw-sm">{h.get("sub", "")}</p>
        <div class="btn-row mt5">
          {_btn(h.get("cta", "Get Started"), "#contact")}
          {_btn("Learn more ↓", "#features", "outline")}
        </div>
        {proof_html}
      </div>
      <div class="rv d1">
        <div class="img-wrap img-tall" style="position:relative;">
          <div style="position:absolute;inset:-20px;background:radial-gradient(circle,var(--glow) 0%,transparent 65%);z-index:-1;border-radius:50%;"></div>
          <img src="{img}" alt="{name}" class="img-fill" loading="eager">
        </div>
      </div>
    </div>
  </div>
</section>"""


def _hero_centered(name: str, d: Dict, ind: str) -> str:
    """Centered editorial hero — luxury, beauty, agency."""
    h   = d.get("hero", {})
    img = _photo(ind, 0, 1400)
    ws  = h.get("h1", f"Welcome to {name}").split()
    mid = max(1, len(ws) // 2)
    l1  = " ".join(ws[:mid])
    l2  = " ".join(ws[mid:]) or ws[-1]

    return f"""<section class="sec-hero" style="min-height:92vh;overflow:hidden;padding-top:0;">
  <div style="position:absolute;inset:0;">
    <img src="{img}" alt="" style="width:100%;height:100%;object-fit:cover;opacity:{'0.15' if 'dark' in d.get('_theme_mode','') else '0.12'};" loading="eager">
    <div style="position:absolute;inset:0;background:linear-gradient(180deg,var(--bg) 0%,transparent 40%,transparent 60%,var(--bg) 100%);"></div>
    <div style="position:absolute;inset:0;background:radial-gradient(ellipse 80% 60% at 50% 50%,var(--glow),transparent);"></div>
  </div>
  <div class="wrap z1 tc" style="padding-top:9rem;padding-bottom:6rem;">
    <div class="rv mw-md mx-auto">
      {_eyebrow(d.get("tagline", ""))}
      <h1 style="font-family:{name};font-size:clamp(3rem,7vw,6.5rem);font-weight:700;letter-spacing:-0.035em;line-height:1.04;color:var(--text);margin-top:0.75rem;">
        <span style="display:block;">{l1}</span>
        <span style="display:block;color:var(--accent);">{l2}</span>
      </h1>
      <p class="body-lg mt4 mw-sm mx-auto">{h.get("sub", "")}</p>
      <div class="btn-row mt5" style="justify-content:center;">
        {_btn(h.get("cta", "Discover"), "#contact")}
        {_btn("Our story →", "#features", "outline")}
      </div>
    </div>
  </div>
</section>"""


def _hero_stats(name: str, d: Dict, ind: str) -> str:
    """Stats-heavy hero — construction, legal, finance, logistics."""
    h     = d.get("hero", {})
    stats = d.get("stats") or []
    img   = _photo(ind, 0, 1200)

    stat_html = ""
    if stats:
        items = "".join(
            f'<div class="rv d{min(i+1,4)}" style="text-align:center;">'
            f'<div class="stat-num">{s.get("value","")}</div>'
            f'<div class="stat-label">{s.get("label","")}</div></div>'
            for i, s in enumerate(stats[:4])
        )
        stat_html = f'<div class="g4 mt6" style="padding-top:2.5rem;border-top:1px solid var(--border);">{items}</div>'

    return f"""<section class="sec-hero" style="overflow:hidden;padding-top:5.5rem;">
  <div class="blob" style="width:600px;height:600px;top:-5%;right:-5%;opacity:0.6;"></div>
  <div style="position:absolute;top:0;right:0;width:40%;height:100%;overflow:hidden;pointer-events:none;">
    <img src="{img}" alt="" style="width:100%;height:100%;object-fit:cover;opacity:0.07;" loading="eager">
    <div style="position:absolute;inset:0;background:linear-gradient(to right,var(--bg) 0%,transparent 55%);"></div>
  </div>
  <div class="wrap z1">
    <div style="max-width:560px;" class="rv">
      {_eyebrow(d.get("tagline", ""))}
      <h1 class="h-display mt2">{h.get("h1", f"Welcome to {name}")}</h1>
      <p class="body-lg mt4">{h.get("sub", "")}</p>
      <div class="btn-row mt5">
        {_btn(h.get("cta", "Get Started"), "#contact")}
        {_btn("Our work →", "#features", "outline")}
      </div>
    </div>
    {stat_html}
  </div>
</section>"""


def _hero_restaurant(name: str, d: Dict, ind: str) -> str:
    """Full-bleed cinematic hero — restaurants, travel, events."""
    h   = d.get("hero", {})
    img = _photo(ind, 0, 1400)

    return f"""<section style="position:relative;min-height:90vh;display:flex;align-items:center;overflow:hidden;padding-top:64px;">
  <div style="position:absolute;inset:0;">
    <img src="{img}" alt="{name}" style="width:100%;height:100%;object-fit:cover;" loading="eager">
    <div style="position:absolute;inset:0;background:linear-gradient(135deg,rgba(0,0,0,0.72) 0%,rgba(0,0,0,0.25) 100%);"></div>
  </div>
  <div class="wrap z1" style="padding-top:3rem;padding-bottom:3rem;">
    <div class="rv" style="max-width:580px;">
      <span style="display:inline-block;font-size:0.65rem;font-weight:700;text-transform:uppercase;letter-spacing:0.2em;color:rgba(255,255,255,0.7);margin-bottom:1.25rem;">{d.get("tagline","")}</span>
      <h1 style="font-family:inherit;font-size:clamp(3rem,6vw,5rem);font-weight:700;letter-spacing:-0.03em;line-height:1.06;color:#ffffff;margin-bottom:1.5rem;">{h.get("h1", f"Welcome to {name}")}</h1>
      <p style="font-size:1.1rem;color:rgba(255,255,255,0.8);line-height:1.7;margin-bottom:2.5rem;max-width:440px;">{h.get("sub","")}</p>
      <div class="btn-row">
        <a href="#contact" style="display:inline-flex;align-items:center;gap:0.5rem;background:#ffffff;color:#111 !important;font-weight:700;font-size:0.95rem;padding:0.85rem 2rem;border-radius:10px;transition:all 0.2s;">{h.get("cta","Reserve a Table")}</a>
        <a href="#features" style="display:inline-flex;align-items:center;gap:0.5rem;background:transparent;color:#ffffff !important;border:2px solid rgba(255,255,255,0.35);font-weight:600;font-size:0.9rem;padding:0.8rem 1.75rem;border-radius:10px;transition:all 0.2s;">See the menu ↓</a>
      </div>
    </div>
  </div>
</section>"""

# =============================================================================
# TRUST BAND
# =============================================================================

def _trust_band(badges: List[str]) -> str:
    if not badges:
        return ""
    pills = "".join(f'<span class="tag">{b}</span>' for b in badges[:6])
    return f"""<div class="sec-sm" style="border-top:1px solid var(--border);border-bottom:1px solid var(--border);">
  <div class="wrap">
    <div class="rv flex flex-wrap ai-c" style="justify-content:center;gap:0.7rem;">
      <span style="font-size:0.65rem;font-weight:700;text-transform:uppercase;letter-spacing:0.18em;color:var(--text3);margin-right:0.35rem;">Trusted</span>
      {pills}
    </div>
  </div>
</div>"""

def _hero_minimal(name: str, d: Dict, ind: str) -> str:
    """Typography-first minimal hero — no image, pure text with accent line. Clean services, consulting."""
    h     = d.get("hero", {})
    stats = d.get("stats") or []
    stat_html = ""
    if stats:
        items = "".join(
            f'<div class="rv d{min(i+1,4)}">'
            f'<div class="stat-num">{s.get("value","")}</div>'
            f'<div class="stat-label">{s.get("label","")}</div></div>'
            for i, s in enumerate(stats[:4])
        )
        stat_html = f'<div class="g4 mt6" style="padding-top:2.5rem;border-top:1px solid var(--border);">{items}</div>'

    return f"""<section class="sec-hero" style="padding-top:6rem;padding-bottom:4rem;min-height:70vh;display:flex;align-items:center;">
  <div class="blob" style="width:700px;height:400px;top:10%;left:-10%;opacity:0.5;"></div>
  <div class="wrap z1">
    <div style="max-width:700px;" class="rv">
      <div style="display:flex;align-items:center;gap:0.75rem;margin-bottom:1.5rem;">
        <div style="width:40px;height:3px;background:var(--accent);border-radius:2px;"></div>
        <span style="font-size:0.7rem;font-weight:700;text-transform:uppercase;letter-spacing:0.2em;color:var(--accent);">{d.get("tagline","")}</span>
      </div>
      <h1 class="h-display">{h.get("h1", f"Welcome to {name}")}</h1>
      <p class="body-lg mt4" style="max-width:520px;">{h.get("sub","")}</p>
      <div class="btn-row mt5">
        {_btn(h.get("cta","Get Started"), "#contact")}
        {_btn("See our work →", "#features", "outline")}
      </div>
    </div>
    {stat_html}
  </div>
</section>"""


def _hero_image_left(name: str, d: Dict, ind: str) -> str:
    """Image on left, text on right — reversal of split for variety."""
    h     = d.get("hero", {})
    img   = _photo(ind, 0, 1100)
    proof = d.get("social_proof") or {}

    proof_html = ""
    if proof.get("count") and proof.get("label"):
        proof_html = f'<div class="flex ai-c gap3 mt4" style="padding-top:1.25rem;border-top:1px solid var(--border);"><span class="body-sm"><strong style="color:var(--accent)">{proof["count"]}</strong> {proof["label"]}</span></div>'

    return f"""<section class="sec-hero" style="padding-top:5.5rem;overflow:hidden;">
  <div class="blob" style="width:500px;height:500px;top:-10%;left:-8%;opacity:0.6;"></div>
  <div class="wrap z1">
    <div class="g2 ai gap-xl">
      <div class="rv">
        <div class="img-wrap img-tall" style="position:relative;">
          <img src="{img}" alt="{name}" class="img-fill" loading="eager">
          <div style="position:absolute;bottom:1.5rem;left:1.5rem;background:var(--surface);border:1px solid var(--border);border-radius:12px;padding:0.9rem 1.2rem;backdrop-filter:blur(10px);">
            <div style="font-size:0.65rem;font-weight:700;text-transform:uppercase;letter-spacing:0.15em;color:var(--text3);margin-bottom:0.25rem;">Est. reputation</div>
            <div style="display:flex;gap:2px;">{("⭐" * 5)}</div>
          </div>
        </div>
      </div>
      <div class="rv d1">
        {_eyebrow(d.get("tagline",""))}
        <h1 class="h-display mt2">{h.get("h1", f"Welcome to {name}")}</h1>
        <p class="body-lg mt4 mw-sm">{h.get("sub","")}</p>
        <div class="btn-row mt5">
          {_btn(h.get("cta","Get Started"), "#contact")}
          {_btn("Learn more ↓", "#features", "outline")}
        </div>
        {proof_html}
      </div>
    </div>
  </div>
</section>"""


def _hero_bold_bg(name: str, d: Dict, ind: str) -> str:
    """Bold accent-colored left panel with text, photo fills right half — striking for trades/services."""
    h   = d.get("hero", {})
    img = _photo(ind, 0, 900)

    return f"""<section style="min-height:88vh;display:grid;grid-template-columns:1fr 1fr;overflow:hidden;padding-top:64px;">
  <div style="background:var(--accent);display:flex;align-items:center;padding:4rem 3rem 4rem 4rem;position:relative;overflow:hidden;">
    <div style="position:absolute;top:-80px;right:-80px;width:300px;height:300px;border-radius:50%;background:rgba(255,255,255,0.06);"></div>
    <div style="position:absolute;bottom:-60px;left:-60px;width:200px;height:200px;border-radius:50%;background:rgba(255,255,255,0.04);"></div>
    <div class="rv" style="position:relative;z-index:1;">
      <span style="display:inline-block;font-size:0.65rem;font-weight:700;text-transform:uppercase;letter-spacing:0.2em;color:rgba(255,255,255,0.65);margin-bottom:1.25rem;">{d.get("tagline","")}</span>
      <h1 style="font-size:clamp(2.2rem,4vw,4rem);font-weight:800;letter-spacing:-0.03em;line-height:1.06;color:#ffffff;margin-bottom:1.5rem;">{h.get("h1", f"Welcome to {name}")}</h1>
      <p style="font-size:1.05rem;color:rgba(255,255,255,0.82);line-height:1.7;margin-bottom:2.5rem;max-width:380px;">{h.get("sub","")}</p>
      <div class="btn-row">
        <a href="#contact" style="display:inline-flex;align-items:center;background:#ffffff;color:var(--accent) !important;font-weight:800;font-size:0.95rem;padding:0.9rem 2rem;border-radius:10px;transition:all 0.2s;">{h.get("cta","Get Started")}</a>
        <a href="#features" style="display:inline-flex;align-items:center;background:transparent;color:rgba(255,255,255,0.85) !important;border:2px solid rgba(255,255,255,0.3);font-weight:600;font-size:0.9rem;padding:0.85rem 1.75rem;border-radius:10px;transition:all 0.2s;">How it works ↓</a>
      </div>
    </div>
  </div>
  <div style="overflow:hidden;">
    <img src="{img}" alt="{name}" style="width:100%;height:100%;object-fit:cover;display:block;" loading="eager">
  </div>
  <style>@media(max-width:767px){{section[style*="grid-template-columns:1fr 1fr"]{{grid-template-columns:1fr!important}}section[style*="grid-template-columns:1fr 1fr"]>div:last-child{{height:280px}}}}</style>
</section>"""


def _hero_video_style(name: str, d: Dict, ind: str) -> str:
    """Full-bleed image with a floating card overlay — modern editorial feel."""
    h   = d.get("hero", {})
    img = _photo(ind, 0, 1500)
    img2 = _photo(ind, 1, 600)

    return f"""<section style="position:relative;min-height:88vh;overflow:hidden;padding-top:64px;">
  <img src="{img}" alt="" style="position:absolute;inset:0;width:100%;height:100%;object-fit:cover;" loading="eager">
  <div style="position:absolute;inset:0;background:linear-gradient(120deg,rgba(0,0,0,0.75) 0%,rgba(0,0,0,0.2) 60%,rgba(0,0,0,0.05) 100%);"></div>
  <div class="wrap z1" style="padding-top:4rem;padding-bottom:4rem;min-height:calc(88vh - 64px);display:flex;align-items:center;">
    <div style="max-width:560px;" class="rv">
      <span style="display:inline-block;font-size:0.65rem;font-weight:700;text-transform:uppercase;letter-spacing:0.2em;color:rgba(255,255,255,0.65);margin-bottom:1.25rem;">{d.get("tagline","")}</span>
      <h1 style="font-size:clamp(2.8rem,5.5vw,5rem);font-weight:800;letter-spacing:-0.03em;line-height:1.06;color:#ffffff;margin-bottom:1.5rem;">{h.get("h1",f"Welcome to {name}")}</h1>
      <p style="font-size:1.1rem;color:rgba(255,255,255,0.82);line-height:1.7;margin-bottom:2.5rem;max-width:440px;">{h.get("sub","")}</p>
      <div class="btn-row">
        <a href="#contact" style="display:inline-flex;align-items:center;background:var(--cta);color:var(--cta-text) !important;font-weight:700;font-size:0.95rem;padding:0.9rem 2rem;border-radius:10px;">{h.get("cta","Get Started")}</a>
        <a href="#features" style="display:inline-flex;align-items:center;background:rgba(255,255,255,0.12);backdrop-filter:blur(8px);color:#fff !important;border:1px solid rgba(255,255,255,0.25);font-weight:600;font-size:0.9rem;padding:0.85rem 1.75rem;border-radius:10px;">Learn more ↓</a>
      </div>
    </div>
    <div style="position:absolute;bottom:2.5rem;right:2.5rem;width:260px;border-radius:16px;overflow:hidden;box-shadow:0 25px 60px rgba(0,0,0,0.4);display:none;" class="rv d2">
      <img src="{img2}" alt="" style="width:100%;height:160px;object-fit:cover;display:block;" loading="lazy">
      <div style="background:rgba(255,255,255,0.96);padding:1rem 1.25rem;">
        <p style="font-size:0.72rem;font-weight:700;text-transform:uppercase;letter-spacing:0.12em;color:var(--accent);margin-bottom:0.3rem;">Why choose us</p>
        <p style="font-size:0.875rem;font-weight:600;color:#111;line-height:1.4;">{name} — trusted by locals</p>
      </div>
    </div>
  </div>
  <style>@media(min-width:900px){{section[style*="min-height:88vh"] .rv.d2{{display:block!important}}}}</style>
</section>"""

def _feat_cards(feats: List[Dict]) -> str:
    cards = "".join(
        f"""<div class="card card-p rv d{min(i+1,4)}">
      <div class="feat-icon">{f.get("icon","◆")}</div>
      <h3 class="h-card mb2">{f.get("title","")}</h3>
      <p class="body-sm">{f.get("description","")}</p>
    </div>"""
        for i, f in enumerate(feats)
    )
    return f"""<section class="sec band" id="features">
  <div class="wrap">
    {_section_header("What We Offer", "Built Around Your Needs", "Every service is designed around real outcomes, not generic promises.")}
    <div class="g3">{cards}</div>
  </div>
</section>"""


def _feat_alternating(feats: List[Dict], ind: str) -> str:
    blocks = []
    for i, f in enumerate(feats[:3]):
        rev  = "direction:row-reverse;" if i % 2 != 0 else ""
        img  = _photo(ind, i + 1, 900)
        blocks.append(f"""<div class="g2 ai rv" style="{rev}margin-bottom:5rem;gap:3.5rem;">
      <div>
        <div style="font-size:2rem;margin-bottom:1rem;line-height:1;">{f.get("icon","◆")}</div>
        <h3 class="h-section" style="font-size:clamp(1.5rem,2.5vw,2rem);margin-bottom:1rem;">{f.get("title","")}</h3>
        <p class="body-lg">{f.get("description","")}</p>
        <a href="#contact" class="btn btn-outline mt4" style="font-size:0.875rem;padding:0.65rem 1.4rem;">Learn more →</a>
      </div>
      <div class="img-wrap img-mid rv d1">
        <img src="{img}" alt="" class="img-fill" loading="lazy">
      </div>
    </div>""")
    return f"""<section class="sec" id="features">
  <div class="wrap">
    {_section_header("How We Work", "Results-Driven, Every Time", "", center=False)}
    {"".join(blocks)}
  </div>
</section>"""


def _feat_icon_list(feats: List[Dict], ind: str) -> str:
    img   = _photo(ind, 1, 900)
    items = "".join(
        f"""<div class="rv d{min(i+1,4)}" style="display:flex;gap:1rem;align-items:flex-start;padding:1.1rem;border:1px solid var(--border);border-radius:12px;background:var(--surface);margin-bottom:0.65rem;">
      <div style="min-width:34px;height:34px;border-radius:50%;background:linear-gradient(135deg,var(--accent),var(--accent2));display:flex;align-items:center;justify-content:center;color:var(--cta-text);font-weight:800;font-size:0.7rem;flex-shrink:0;">{str(i+1).zfill(2)}</div>
      <div>
        <h3 class="h-card mb1">{f.get("title","")}</h3>
        <p class="body-sm">{f.get("description","")}</p>
      </div>
    </div>"""
        for i, f in enumerate(feats)
    )
    return f"""<section class="sec band" id="features">
  <div class="wrap">
    <div class="g2 ai gap-xl">
      <div class="rv">
        {_eyebrow("Our Approach")}
        <h2 class="h-section mt2 mb5">The Way We Deliver</h2>
        {items}
      </div>
      <div class="img-wrap img-tall rv d2">
        <img src="{img}" alt="" class="img-fill" loading="lazy">
      </div>
    </div>
  </div>
</section>"""


def _feat_big_numbers(feats: List[Dict]) -> str:
    """Feature section with large numbered steps — great for process-oriented businesses."""
    cards = "".join(
        f"""<div class="rv d{min(i+1,4)}" style="display:flex;gap:1.5rem;align-items:flex-start;padding:2rem 0;border-bottom:1px solid var(--border);">
      <span style="font-size:3.5rem;font-weight:900;line-height:1;color:rgba(var(--accent-r),0.12);min-width:70px;letter-spacing:-0.05em;">{str(i+1).zfill(2)}</span>
      <div>
        <div style="font-size:1.3rem;margin-bottom:0.5rem;">{f.get("icon","◆")}</div>
        <h3 class="h-card mb2">{f.get("title","")}</h3>
        <p class="body-sm">{f.get("description","")}</p>
      </div>
    </div>"""
        for i, f in enumerate(feats)
    )
    return f"""<section class="sec" id="features">
  <div class="wrap">
    <div class="g2 gap-xl" style="align-items:start;">
      <div class="rv">
        {_eyebrow("Our Services")}
        <h2 class="h-section mt2">Everything you need, handled.</h2>
        <p class="body-lg mt3 mw-sm">We take care of the details so you don't have to.</p>
        <a href="#contact" class="btn btn-primary mt5">Get in touch →</a>
      </div>
      <div>{cards}</div>
    </div>
  </div>
</section>"""


def _feat_checklist_split(feats: List[Dict], ind: str) -> str:
    """Simple checklist on left, image right — clean and scannable for service businesses."""
    img   = _photo(ind, 1, 900)
    items = "".join(
        f"""<div class="rv d{min(i+1,4)}" style="display:flex;gap:1rem;align-items:flex-start;margin-bottom:1.25rem;">
      <div style="width:22px;height:22px;border-radius:50%;background:linear-gradient(135deg,var(--accent),var(--accent2));display:flex;align-items:center;justify-content:center;color:var(--cta-text);font-size:0.65rem;font-weight:900;flex-shrink:0;margin-top:2px;">✓</div>
      <div>
        <p style="font-weight:700;font-size:0.95rem;color:var(--text);margin-bottom:0.2rem;">{f.get("title","")}</p>
        <p class="body-sm">{f.get("description","")}</p>
      </div>
    </div>"""
        for i, f in enumerate(feats)
    )
    return f"""<section class="sec band" id="features">
  <div class="wrap">
    <div class="g2 ai gap-xl">
      <div class="rv">
        {_eyebrow("What We Offer")}
        <h2 class="h-section mt2 mb5">Why clients choose us</h2>
        {items}
        <a href="#contact" class="btn btn-primary mt4">{_btn("Book Now", "#contact")}</a>
      </div>
      <div class="rv d2">
        <div class="img-wrap img-tall">
          <img src="{img}" alt="" class="img-fill" loading="lazy">
        </div>
      </div>
    </div>
  </div>
</section>"""


def _feat_three_columns_icons(feats: List[Dict]) -> str:
    """Three equal columns with large emoji icons — bold and modern, great for SaaS/agency."""
    cards = "".join(
        f"""<div class="rv d{min(i+1,4)}" style="text-align:center;padding:2.5rem 1.5rem;">
      <div style="font-size:2.5rem;margin-bottom:1.25rem;">{f.get("icon","◆")}</div>
      <h3 class="h-card mb3">{f.get("title","")}</h3>
      <p class="body-sm">{f.get("description","")}</p>
    </div>"""
        for i, f in enumerate(feats)
    )
    return f"""<section class="sec" id="features">
  <div class="wrap">
    {_section_header("Features", "Built for results", "No fluff. No bloat. Just what works.")}
    <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:0;border:1px solid var(--border);border-radius:16px;overflow:hidden;">
      {cards.replace('<div class="rv', '<div class="rv" style="border-right:1px solid var(--border);').rstrip()}
    </div>
  </div>
</section>"""


# =============================================================================
# PROCESS / HOW IT WORKS — new section type
# =============================================================================

def _process_steps(d: Dict) -> str:
    """Horizontal step-by-step process — how the service works."""
    feats = d.get("features") or []
    if not feats:
        return ""
    steps = feats[:4]
    items = "".join(
        f"""<div class="rv d{min(i+1,4)}" style="flex:1;min-width:180px;text-align:center;padding:0 1rem;position:relative;">
      {"" if i == 0 else '<div style="position:absolute;top:20px;left:-50%;width:100%;height:2px;background:linear-gradient(to right,var(--accent),rgba(var(--accent-r),0.2));z-index:0;"></div>'}
      <div style="width:44px;height:44px;border-radius:50%;background:var(--accent);color:var(--cta-text);display:flex;align-items:center;justify-content:center;font-weight:800;font-size:0.9rem;margin:0 auto 1rem;position:relative;z-index:1;">{i+1}</div>
      <h4 style="font-weight:700;font-size:0.9rem;color:var(--text);margin-bottom:0.5rem;">{s.get("title","")}</h4>
      <p style="font-size:0.78rem;color:var(--text2);line-height:1.55;">{(s.get("description","") or "")[:90]}...</p>
    </div>"""
        for i, s in enumerate(steps)
    )
    return f"""<section class="sec-sm band" id="process" style="padding:5rem 0;">
  <div class="wrap">
    {_section_header("How It Works", "Simple from start to finish", "Getting started takes less than a minute.")}
    <div style="display:flex;flex-wrap:wrap;gap:1.5rem;justify-content:center;position:relative;">
      {items}
    </div>
  </div>
</section>"""


# =============================================================================
# PHOTO GALLERY — new section type
# =============================================================================

def _gallery(ind: str, name: str) -> str:
    """Asymmetric masonry-style photo grid — great for service businesses, restaurants, beauty."""
    imgs = [_photo(ind, i, 800) for i in range(5)]
    return f"""<section class="sec-sm" id="gallery" style="padding:4rem 0;overflow:hidden;">
  <div class="wrap">
    {_section_header("Our Work", "Results speak for themselves", "", center=True)}
    <div style="display:grid;grid-template-columns:repeat(3,1fr);grid-template-rows:200px 200px;gap:0.75rem;border-radius:16px;overflow:hidden;">
      <div style="grid-column:1/2;grid-row:1/3;overflow:hidden;border-radius:12px;" class="rv">
        <img src="{imgs[0]}" alt="{name} gallery" style="width:100%;height:100%;object-fit:cover;display:block;transition:transform 0.5s;" onmouseover="this.style.transform='scale(1.04)'" onmouseout="this.style.transform='scale(1)'">
      </div>
      <div style="overflow:hidden;border-radius:12px;" class="rv d1">
        <img src="{imgs[1]}" alt="" style="width:100%;height:100%;object-fit:cover;display:block;transition:transform 0.5s;" onmouseover="this.style.transform='scale(1.04)'" onmouseout="this.style.transform='scale(1)'">
      </div>
      <div style="overflow:hidden;border-radius:12px;" class="rv d2">
        <img src="{imgs[2]}" alt="" style="width:100%;height:100%;object-fit:cover;display:block;transition:transform 0.5s;" onmouseover="this.style.transform='scale(1.04)'" onmouseout="this.style.transform='scale(1)'">
      </div>
      <div style="overflow:hidden;border-radius:12px;" class="rv d1">
        <img src="{imgs[3]}" alt="" style="width:100%;height:100%;object-fit:cover;display:block;transition:transform 0.5s;" onmouseover="this.style.transform='scale(1.04)'" onmouseout="this.style.transform='scale(1)'">
      </div>
      <div style="overflow:hidden;border-radius:12px;" class="rv d2">
        <img src="{imgs[4]}" alt="" style="width:100%;height:100%;object-fit:cover;display:block;transition:transform 0.5s;" onmouseover="this.style.transform='scale(1.04)'" onmouseout="this.style.transform='scale(1)'">
      </div>
    </div>
    <p style="text-align:center;margin-top:1.5rem;font-size:0.8rem;color:var(--text3);">See our latest projects and results</p>
  </div>
</section>"""

def _price_tiers(tiers: List[Dict]) -> str:
    def _tier(t: Dict, idx: int) -> str:
        featured = t.get("featured", False)
        bg_style = "background:linear-gradient(135deg,var(--accent),var(--accent2));border-color:transparent;" if featured else ""
        tc = "color:rgba(255,255,255,0.85);" if featured else "color:var(--text2);"
        pc = "color:#fff;" if featured else "color:var(--text);"
        pop = '<span style="position:absolute;top:1rem;right:1rem;font-size:0.6rem;font-weight:700;background:rgba(255,255,255,0.2);color:#fff;padding:0.2rem 0.6rem;border-radius:999px;text-transform:uppercase;letter-spacing:0.1em;">Popular</span>' if featured else ""
        rows = "".join(
            f'<li class="chk-item"><span class="chk-mark" style="{"color:#fff;" if featured else ""}">✓</span><span style="{tc}">{f}</span></li>'
            for f in (t.get("features") or [])
        )
        cta_style = (
            "display:block;text-align:center;margin-top:1.5rem;padding:0.85rem;border-radius:10px;font-weight:700;font-size:0.9rem;background:rgba(255,255,255,0.18);color:#fff !important;transition:background 0.2s;"
            if featured else
            "display:block;text-align:center;margin-top:1.5rem;padding:0.85rem;border-radius:10px;font-weight:700;font-size:0.9rem;border:1.5px solid var(--border);color:var(--text) !important;transition:all 0.2s;"
        )
        return f"""<div class="card card-p rv d{min(idx+1,4)}" style="position:relative;display:flex;flex-direction:column;{bg_style}">
      {pop}
      <h3 style="font-weight:700;font-size:1rem;margin-bottom:0.25rem;{pc}">{t.get("name","Plan")}</h3>
      <p style="font-size:0.78rem;margin-bottom:1.25rem;{tc}">{t.get("description","")}</p>
      <div style="margin-bottom:1.5rem;">
        <span style="font-family:inherit;font-size:2.5rem;font-weight:800;letter-spacing:-0.04em;{pc}">{t.get("price","")}</span>
        <span style="font-size:0.75rem;{tc}"> /mo</span>
      </div>
      <ul class="chk-list" style="flex:1;">{rows}</ul>
      <a href="#contact" style="{cta_style}">{t.get("cta","Get Started")}</a>
    </div>"""
    cards = "".join(_tier(t, i) for i, t in enumerate(tiers))
    return f"""<section class="sec" id="pricing">
  <div class="wrap">
    {_section_header("Pricing", "Simple, Transparent Pricing", "No hidden fees. No long-term contracts. Cancel anytime.")}
    <div class="g3 mw-lg mx-auto">{cards}</div>
  </div>
</section>"""


def _price_project(tiers: List[Dict]) -> str:
    cards = "".join(
        f"""<div class="card card-p rv d{min(i+1,4)}" style="display:flex;flex-direction:column;">
      <h3 class="h-card mb2">{t.get("name","Package")}</h3>
      <p class="body-sm mb3">{t.get("description","")}</p>
      <p style="font-size:1.25rem;font-weight:800;color:var(--accent);margin-bottom:1.25rem;">{t.get("price","")}</p>
      <ul class="chk-list" style="flex:1;margin-bottom:1.5rem;">{"".join(_chk(f) for f in (t.get("features") or []))}</ul>
      {_btn("Request a Quote", "#contact", "outline")}
    </div>"""
        for i, t in enumerate(tiers)
    )
    return f"""<section class="sec band" id="pricing">
  <div class="wrap">
    {_section_header("Services & Pricing", "Project-Based Pricing", "Every job is different. We give transparent quotes before any work begins.")}
    <div class="g3">{cards}</div>
    <div class="card card-plg tc rv mt5 mw-sm mx-auto">
      <h3 class="h-card mb2">Not sure what you need?</h3>
      <p class="body-sm mb4">Tell us about your project and we'll give you a detailed, no-obligation quote within 24 hours.</p>
      {_btn("Get a Free Estimate", "#contact")}
    </div>
  </div>
</section>"""


def _price_contact_cta() -> str:
    """Shown when pricing is null — never shows empty/placeholder pricing."""
    return f"""<section class="sec" id="pricing">
  <div class="wrap">
    <div class="card card-plg tc mw-sm mx-auto rv" style="background:linear-gradient(135deg,rgba(var(--accent-r),0.04),rgba(var(--accent-r),0.01));">
      {_eyebrow("Pricing")}
      <h2 class="h-section mt2 mb3">Tailored to Your Project</h2>
      <p class="body-lg mb5">Every engagement is different, so we don't use one-size-fits-all pricing. Reach out for a transparent, no-obligation quote.</p>
      {_btn("Request a Quote", "#contact")}
    </div>
  </div>
</section>"""

# =============================================================================
# TESTIMONIALS
# =============================================================================

def _testimonials(tevs: List[Dict]) -> str:
    if not tevs:
        return ""
    cards = "".join(
        f"""<div class="card card-p rv d{min(i+1,4)}" style="display:flex;flex-direction:column;">
      {_stars()}
      <p class="body-sm" style="font-style:italic;flex:1;margin-bottom:1.25rem;">"{tv.get("quote","")}"</p>
      <div style="display:flex;align-items:center;gap:0.75rem;border-top:1px solid var(--border);padding-top:1rem;">
        <div class="avatar">{(tv.get("name","?") or "?")[0].upper()}</div>
        <div>
          <p style="font-weight:700;font-size:0.875rem;color:var(--text);">{tv.get("name","")}</p>
          <p style="font-size:0.73rem;color:var(--text3);">{tv.get("role","")} · {tv.get("company","")}</p>
        </div>
      </div>
    </div>"""
        for i, tv in enumerate(tevs)
    )
    return f"""<section class="sec band" id="testimonials">
  <div class="wrap">
    {_section_header("Testimonials", "What Clients Say")}
    <div class="testi-grid">{cards}</div>
  </div>
</section>"""

def _testimonials_featured(tevs: List[Dict]) -> str:
    """Large featured quote up top with smaller cards below — more editorial."""
    if not tevs:
        return ""
    featured = tevs[0]
    rest     = tevs[1:]
    rest_cards = "".join(
        f"""<div class="card card-p rv d{min(i+1,4)}" style="display:flex;flex-direction:column;">
      {_stars()}
      <p class="body-sm" style="font-style:italic;flex:1;margin-bottom:1rem;">"{tv.get("quote","")}"</p>
      <div style="display:flex;align-items:center;gap:0.6rem;border-top:1px solid var(--border);padding-top:0.85rem;">
        <div class="avatar">{(tv.get("name","?") or "?")[0].upper()}</div>
        <div>
          <p style="font-weight:700;font-size:0.8rem;color:var(--text);">{tv.get("name","")}</p>
          <p style="font-size:0.7rem;color:var(--text3);">{tv.get("role","")} · {tv.get("company","")}</p>
        </div>
      </div>
    </div>"""
        for i, tv in enumerate(rest)
    )
    return f"""<section class="sec band" id="testimonials">
  <div class="wrap">
    {_section_header("Testimonials", "What Clients Say")}
    <div class="card card-plg rv" style="margin-bottom:1.5rem;position:relative;overflow:hidden;">
      <div style="position:absolute;top:-0.5rem;left:1.5rem;font-size:7rem;line-height:1;color:var(--accent);opacity:0.08;font-family:Georgia,serif;pointer-events:none;">"</div>
      <div style="position:relative;z-index:1;">
        {_stars()}
        <p style="font-size:1.25rem;line-height:1.65;color:var(--text);font-style:italic;margin-bottom:1.5rem;max-width:680px;">"{featured.get("quote","")}"</p>
        <div style="display:flex;align-items:center;gap:0.85rem;">
          <div class="avatar" style="width:48px;height:48px;font-size:1rem;">{(featured.get("name","?") or "?")[0].upper()}</div>
          <div>
            <p style="font-weight:700;color:var(--text);">{featured.get("name","")}</p>
            <p style="font-size:0.8rem;color:var(--text3);">{featured.get("role","")} · {featured.get("company","")}</p>
          </div>
        </div>
      </div>
    </div>
    {f'<div class="testi-grid">{rest_cards}</div>' if rest_cards else ""}
  </div>
</section>"""


def _faq_two_col(faqs: List[Dict]) -> str:
    """Two-column FAQ layout — more scannable for longer FAQ lists."""
    if not faqs or len(faqs) < 3:
        return _faq(faqs)
    mid   = (len(faqs) + 1) // 2
    col1  = faqs[:mid]
    col2  = faqs[mid:]
    def _item(faq: Dict, i: int) -> str:
        return f"""<details class="faq-item rv d{min(i+1,3)}">
      <summary>{faq.get("q","")}<span class="faq-toggle">+</span></summary>
      <div class="faq-answer">{faq.get("a","")}</div>
    </details>"""
    c1 = "".join(_item(f, i) for i, f in enumerate(col1))
    c2 = "".join(_item(f, i) for i, f in enumerate(col2))
    return f"""<section class="sec-sm" id="faq" style="padding:5rem 0;">
  <div class="wrap">
    {_section_header("FAQ", "Common Questions")}
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:0.75rem 2rem;">
      <div>{c1}</div>
      <div>{c2}</div>
    </div>
  </div>
  <style>@media(max-width:767px){{section[id="faq"] .wrap>div:last-child{{grid-template-columns:1fr!important}}}}</style>
</section>"""


# =============================================================================
# FAQ
# =============================================================================

def _faq(faqs: List[Dict]) -> str:
    if not faqs:
        return ""
    items = "".join(
        f"""<details class="faq-item rv d{min(i+1,4)}">
      <summary>{faq.get("q","")}<span class="faq-toggle">+</span></summary>
      <div class="faq-answer">{faq.get("a","")}</div>
    </details>"""
        for i, faq in enumerate(faqs)
    )
    return f"""<section class="sec-sm" id="faq" style="padding-top:5rem;padding-bottom:5rem;">
  <div class="wrap">
    {_section_header("FAQ", "Common Questions")}
    <div style="max-width:640px;margin:0 auto;">{items}</div>
  </div>
</section>"""

# =============================================================================
# CONTACT
# =============================================================================

def _contact(name: str, d: Dict, email: str, phone: str, ind: str) -> str:
    headline = d.get("cta_headline") or f"Work with {name}"
    sub      = d.get("hero", {}).get("sub") or "We'd love to hear about your project."
    cta      = d.get("hero", {}).get("cta") or "Send Message"
    img      = _photo(ind, 2, 1000)

    form_attr   = f'action="mailto:{email}" enctype="text/plain"' if email else ""
    form_note   = "" if email else '<p style="font-size:0.68rem;color:var(--text3);margin-top:0.75rem;text-align:center;">We\'ll set up form delivery — for now, use the phone or email above.</p>'

    contact_items = ""
    if email:
        contact_items += f'<a href="mailto:{email}" style="display:flex;align-items:center;gap:0.5rem;font-size:0.875rem;color:var(--text2);">✉ {email}</a>'
    if phone:
        safe = re.sub(r'[^\d+]', '', phone)
        contact_items += f'<a href="tel:{safe}" style="display:flex;align-items:center;gap:0.5rem;font-size:0.875rem;color:var(--text2);">☎ {phone}</a>'
    contact_block = f'<div style="display:flex;flex-direction:column;gap:0.75rem;border-top:1px solid var(--border);padding-top:1.25rem;margin-top:1.5rem;">{contact_items}</div>' if contact_items else ""

    return f"""<section class="sec" id="contact" style="overflow:hidden;">
  <div class="blob" style="width:500px;height:500px;top:50%;right:-8%;transform:translateY(-50%);opacity:0.5;"></div>
  <div style="position:absolute;inset:0;pointer-events:none;overflow:hidden;">
    <img src="{img}" alt="" style="width:100%;height:100%;object-fit:cover;opacity:0.03;" loading="lazy">
  </div>
  <div class="wrap z1">
    <div class="g2 gap-xl" style="align-items:start;">
      <div class="rv">
        {_eyebrow("Get in Touch")}
        <h2 class="h-section mt2">{headline}</h2>
        <p class="body-lg mt3 mw-sm">{sub}</p>
        {contact_block}
      </div>
      <div class="card card-plg rv d1">
        <form {form_attr} method="post" novalidate>
          <div class="form-row">
            <label class="form-label" for="cf-name">Your Name</label>
            <input class="form-input" type="text" id="cf-name" name="name" placeholder="Jane Smith" required autocomplete="name">
          </div>
          <div class="form-row">
            <label class="form-label" for="cf-email">Email Address</label>
            <input class="form-input" type="email" id="cf-email" name="email" placeholder="jane@example.com" required autocomplete="email">
          </div>
          <div class="form-row">
            <label class="form-label" for="cf-msg">Message</label>
            <textarea class="form-input" id="cf-msg" name="message" placeholder="Tell us about your project..." required></textarea>
          </div>
          <button type="submit" class="btn btn-primary" style="width:100%;justify-content:center;">{cta} →</button>
          {form_note}
        </form>
      </div>
    </div>
  </div>
</section>"""

# =============================================================================
# FOOTER
# =============================================================================

def _footer(name: str, d: Dict, nav_links: List[str], email: str, phone: str) -> str:
    sub  = d.get("hero", {}).get("sub", "")
    tag  = d.get("tagline", "")
    year = 2026

    nav_html = "".join(
        f'<li style="margin-bottom:0.4rem;"><a href="#{l.lower().replace(" ","-")}" style="font-size:0.875rem;color:var(--text2);">{l}</a></li>'
        for l in nav_links
    )
    contact_html = ""
    if email:
        contact_html += f'<li style="margin-bottom:0.4rem;"><a href="mailto:{email}" style="font-size:0.875rem;color:var(--text2);">{email}</a></li>'
    if phone:
        contact_html += f'<li style="margin-bottom:0.4rem;"><span style="font-size:0.875rem;color:var(--text2);">{phone}</span></li>'
    if not contact_html:
        contact_html = '<li><a href="#contact" style="font-size:0.875rem;color:var(--text2);">Contact Us</a></li>'

    return f"""<footer class="site-footer">
  <div class="wrap">
    <div style="display:grid;grid-template-columns:2fr 1fr 1fr;gap:3rem;margin-bottom:3rem;">
      <div>
        <div style="font-size:1.1rem;font-weight:700;letter-spacing:-0.02em;color:var(--text);margin-bottom:0.75rem;">{name}</div>
        <p style="font-size:0.875rem;color:var(--text2);max-width:240px;line-height:1.6;">{sub}</p>
        {f'<p style="font-size:0.75rem;color:var(--text3);margin-top:0.5rem;font-style:italic;">{tag}</p>' if tag else ""}
      </div>
      <div>
        <p style="font-size:0.62rem;font-weight:700;text-transform:uppercase;letter-spacing:0.16em;color:var(--text3);margin-bottom:1rem;">Pages</p>
        <ul style="list-style:none;">{nav_html}</ul>
      </div>
      <div>
        <p style="font-size:0.62rem;font-weight:700;text-transform:uppercase;letter-spacing:0.16em;color:var(--text3);margin-bottom:1rem;">Contact</p>
        <ul style="list-style:none;">{contact_html}</ul>
      </div>
    </div>
    <div style="border-top:1px solid var(--border);padding-top:1.5rem;display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:0.5rem;">
      <p style="font-size:0.75rem;color:var(--text3);">© {year} {name}. All rights reserved.</p>
      <p style="font-size:0.75rem;color:var(--text3);">Built with AutopilotAI</p>
    </div>
  </div>
</footer>
<style>@media(max-width:639px){{.site-footer .wrap>div:first-child{{grid-template-columns:1fr!important}}}}</style>"""

# =============================================================================
# AI PROMPT — hyper-specific, structured to prevent generic output
# =============================================================================

def _build_ai_prompt(name: str, prompt: str, industry: str) -> str:
    """
    Constructs a prompt that forces specific, relevant, non-generic output.
    The key insight: give the AI concrete constraints so it can't fall back on
    boilerplate like 'We empower businesses' or irrelevant pricing tiers.
    """

    # Check if user explicitly says pricing is quote/visit-based — force null
    prompt_lower = prompt.lower()
    user_wants_no_price = any(phrase in prompt_lower for phrase in [
        "price after", "prices after", "pricing after", "quote after",
        "decided after", "based on visit", "after visit", "after assessment",
        "free quote", "free estimate", "custom quote", "contact for price",
        "price on request", "call for price", "varies", "depends on",
        "per job", "by quote", "get a quote",
    ])

    # Industry-specific pricing guidance
    no_price_industries   = {"restaurant", "beauty", "fitness", "travel", "nature", "events", "luxury", "agency"}
    project_industries    = {"construction", "logistics", "automotive", "events", "cleaning"}
    service_industries    = {"legal", "nonprofit", "health", "real_estate"}

    if user_wants_no_price or industry in no_price_industries or industry in project_industries:
        pricing_schema = '"pricing": null'
        pricing_note   = (
            "pricing MUST be null — either the user said prices are determined after a visit/assessment, "
            "or this industry does not list prices on landing pages. Do NOT invent any prices whatsoever."
        )
    elif industry in service_industries:
        pricing_schema = '''"pricing": [
    {"name": "Consultation", "price": "Complimentary", "description": "Initial meeting.", "features": ["item","item","item","item","item"], "featured": false},
    {"name": "Standard", "price": "From $X/hr", "description": "Core service.", "features": ["item","item","item","item","item"], "featured": true},
    {"name": "Retainer", "price": "Custom/mo", "description": "Ongoing engagement.", "features": ["item","item","item","item","item"], "featured": false}
  ]'''
        pricing_note   = f"Use real market rates for {industry} in this region."
    else:
        pricing_schema = '''"pricing": [
    {"name": "Starter", "price": "$XX/mo", "description": "For individuals.", "features": ["item","item","item","item","item"], "featured": false},
    {"name": "Pro", "price": "$XX/mo", "description": "For growing teams.", "features": ["item","item","item","item","item"], "featured": true},
    {"name": "Enterprise", "price": "Custom", "description": "For large orgs.", "features": ["item","item","item","item","item"], "featured": false}
  ]'''
        pricing_note   = "Use realistic SaaS pricing for this market and product."

    return f"""You are writing landing page copy for a real business. Be a skilled copywriter — specific, authentic, industry-appropriate.

BUSINESS NAME: {name}
INDUSTRY: {industry}
DESCRIPTION: {prompt}

CRITICAL RULES — violating any of these makes the output useless:
1. hero.h1 must be a real brand tagline (5-9 words). NOT "Empowering Businesses" or "Your Trusted Partner". Think: what would a great ad agency write for this exact company?
2. Features must describe EXACTLY what this business does — not generic "Expert Team / Proven Results / Dedicated Support".
3. Testimonials must contain a SPECIFIC outcome, not "Great service!". Example: "Our kitchen renovation was done in 3 weeks under budget."
4. FAQ must be questions REAL customers of THIS specific business ask. Not "How do I get started?"
5. Trust badges must be REAL credentials for this industry (OSHA, Bar Association, Michelin, etc.).
6. Stats must be plausible for a real business this size. Don't invent fantasy numbers.
7. {pricing_note}
8. contact_email and contact_phone: ONLY fill if the description explicitly provides them. Otherwise leave as "".
9. Do NOT use the word "empower", "leverage", "seamless", "cutting-edge", "solutions", or "synergy".

Return ONLY valid JSON. No markdown fences, no comments, no explanation:
{{
  "sections": ["hero","trust","features",{"'pricing'," if industry not in no_price_industries else ""}"testimonials","faq","contact"],
  "nav": ["label1","label2","label3","label4"],
  "hero": {{
    "h1": "Specific tagline for {name} — 5 to 9 words",
    "sub": "One concrete sentence about what {name} does and who it helps. Max 22 words.",
    "cta": "Action verb + context (e.g. Request a Quote / Book a Table / Start Free Trial)"
  }},
  "tagline": "2-4 word brand slogan",
  "social_proof": {{"count": "e.g. 350+", "label": "e.g. kitchens renovated"}},
  "stats": [
    {{"value": "figure", "label": "what it measures"}},
    {{"value": "figure", "label": "what it measures"}},
    {{"value": "figure", "label": "what it measures"}},
    {{"value": "figure", "label": "what it measures"}}
  ],
  "trust_badges": ["Real credential 1", "Real credential 2", "Real credential 3", "Real credential 4"],
  "features": [
    {{"title": "Specific service or benefit", "description": "2 concrete sentences. What does {name} actually do? Who does it help and how?", "icon": "single emoji"}},
    {{"title": "Specific service or benefit", "description": "2 concrete sentences.", "icon": "single emoji"}},
    {{"title": "Specific service or benefit", "description": "2 concrete sentences.", "icon": "single emoji"}}
  ],
  {pricing_schema},
  "testimonials": [
    {{"name": "Full Name", "role": "Job Title", "company": "Company or City, State", "quote": "Specific result with measurable outcome. Max 2 sentences."}},
    {{"name": "Full Name", "role": "Job Title", "company": "Company or City, State", "quote": "Specific result."}}
  ],
  "faq": [
    {{"q": "Real customer question?", "a": "Direct, honest answer."}},
    {{"q": "Real customer question?", "a": "Direct answer."}},
    {{"q": "Real customer question?", "a": "Direct answer."}}
  ],
  "cta_headline": "Specific closing CTA for {name}",
  "contact_email": "",
  "contact_phone": ""
}}"""

# =============================================================================
# CONTACT EXTRACTION
# =============================================================================

def _extract_contact(text: str) -> Dict[str, str]:
    result = {}
    m = re.search(r'[\w.+-]+@[\w-]+\.[a-zA-Z]{2,}', text or "")
    if m:
        result["email"] = m.group(0)
    m = re.search(r'(?:\+?1[-.\s]?)?(?:\(?\d{3}\)?[-.\s]?)?\d{3}[-.\s]?\d{4}', text or "")
    if m:
        digits = re.sub(r'[^\d+]', '', m.group(0))
        if len(digits) >= 10:
            result["phone"] = m.group(0).strip()
    return result

# =============================================================================
# FALLBACK DATA — only used when AI is unavailable
# =============================================================================

def _generic_fallback_data() -> Dict:
    return {
        "sections": ["hero","trust","features","testimonials","faq","contact"],
        "nav": ["Services","About","FAQ","Contact"],
        "hero": {"h1": "Built for Your Business", "sub": "Professional services delivered with precision and care.", "cta": "Get Started"},
        "tagline": "Results you can trust.",
        "social_proof": {"count": "200+", "label": "clients served"},
        "stats": [{"value":"97%","label":"Client satisfaction"},{"value":"200+","label":"Projects"},{"value":"8yr","label":"Experience"},{"value":"24h","label":"Response time"}],
        "trust_badges": ["Licensed & Insured","5-Star Rated","Award Winner 2024","Certified Professional"],
        "features": [
            {"title":"Deep Expertise","description":"Years of hands-on experience means we understand the nuances of your industry and anticipate problems before they arise.","icon":"◆"},
            {"title":"Clear Communication","description":"You'll always know where your project stands. We send updates at every milestone and respond to questions within 24 hours.","icon":"▲"},
            {"title":"Quality Guaranteed","description":"We stand behind our work. If something isn't right, we fix it — no arguments, no extra charges.","icon":"●"},
        ],
        "pricing": None,
        "testimonials": [
            {"name":"Jordan Lee","role":"Director","company":"Meridian Group","quote":"Genuinely one of the best experiences we've had with a service provider. Results showed up within the first month."},
            {"name":"Priya Nair","role":"Founder","company":"Spark Ventures","quote":"Responsive, knowledgeable, and they actually care about the outcome. Highly recommend."},
        ],
        "faq": [
            {"q":"How do we get started?","a":"Fill out the contact form below. We'll respond within 24 hours to schedule an initial conversation."},
            {"q":"What does your process look like?","a":"We start with a discovery session to understand your goals, then build a tailored plan before any work begins."},
            {"q":"Do you offer ongoing support?","a":"Yes — all engagements include continued access to our team after the initial project wraps up."},
        ],
        "cta_headline": "Ready to get started?",
        "contact_email": "",
        "contact_phone": "",
    }

# =============================================================================
# MASTER ARCHITECT — orchestrates everything
# =============================================================================

VALID_SECTIONS = {"hero","trust","features","pricing","testimonials","faq","contact"}

class MasterArchitect:

    def __init__(self, business_name: str, prompt: str, version: int = 1):
        self.name     = (business_name or "").strip() or "My Business"
        self.prompt   = (prompt or "").strip()
        self.version  = version
        self.industry = detect_industry(self.prompt)
        self.theme    = THEMES.get(INDUSTRY_THEME.get(self.industry, "ocean"), THEMES["ocean"])
        self.contacts = _extract_contact(self.prompt)
        # Deterministic variety seed — same business always gets same layout,
        # but different business names get different layout picks
        self._seed    = sum(ord(c) for c in self.name) % 10
        logger.info(f"MasterArchitect | name='{self.name}' | industry={self.industry} | theme={self.theme['id']} | seed={self._seed}")

    # ── Variant selectors ─────────────────────────────────────────────────────

    def _hero_variant(self) -> str:
        # Full-bleed cinematic — restaurants, travel, events
        if self.industry in {"restaurant", "travel", "events"}:
            return ["restaurant", "video_style"][self._seed % 2]
        # Editorial centered — luxury, beauty, agency
        if self.industry in {"luxury", "beauty", "agency"}:
            return ["centered", "video_style"][self._seed % 2]
        # Stats-heavy — trust-first industries
        if self.industry in {"construction", "legal", "finance", "logistics", "real_estate", "cleaning"}:
            return ["stats", "bold_bg", "minimal"][self._seed % 3]
        # Tech/SaaS — modern, minimal
        if self.industry in {"saas", "ai", "developer", "startup", "ecommerce", "education"}:
            return ["split", "minimal", "image_left"][self._seed % 3]
        # Default — rotate through all non-cinematic variants
        return ["split", "image_left", "minimal", "stats"][self._seed % 4]

    def _feat_variant(self) -> str:
        if self.industry in {"construction", "legal", "logistics", "real_estate", "cleaning", "automotive"}:
            return ["icon_list", "checklist_split", "big_numbers"][self._seed % 3]
        if self.industry in {"saas", "developer", "ai", "startup"}:
            return ["cards", "three_columns", "big_numbers"][self._seed % 3]
        if self.industry in {"restaurant", "beauty", "events", "travel", "luxury"}:
            return ["alternating", "checklist_split"][self._seed % 2]
        if self.industry in {"finance", "health", "education", "nonprofit"}:
            return ["icon_list", "big_numbers", "alternating"][self._seed % 3]
        return ["cards", "alternating", "icon_list", "checklist_split"][self._seed % 4]

    def _testi_variant(self) -> str:
        return ["grid", "featured"][self._seed % 2]

    def _faq_variant(self) -> str:
        return ["single", "two_col"][self._seed % 2]
        if not tiers:
            return "none"
        if self.industry in {"construction", "logistics", "automotive", "events", "cleaning"}:
            return "project"
        return "tiers"

    def _extra_sections(self, d: Dict) -> Dict[str, str]:
        """Generate optional extra sections based on industry + seed."""
        extras = {}
        # Process steps — great for service businesses
        if self.industry in {"cleaning", "construction", "health", "legal", "logistics",
                              "automotive", "saas", "education", "finance", "real_estate"}:
            if self._seed % 2 == 0:
                extras["process"] = _process_steps(d)
        # Gallery — visual industries benefit a lot
        if self.industry in {"restaurant", "beauty", "construction", "cleaning",
                              "events", "travel", "fitness", "real_estate", "agency"}:
            if self._seed % 3 != 0:  # show 2 out of 3 times
                extras["gallery"] = _gallery(self.industry, self.name)
        return extras

    # ── Data fetching ─────────────────────────────────────────────────────────

    def _get_data(self) -> Dict:
        if not AI_AVAILABLE:
            logger.warning("AI unavailable, using fallback data")
            return {**_generic_fallback_data(), **self.contacts}

        try:
            raw     = chat_completion(
                system=(
                    "You are an expert copywriter. Your output is consumed by a JSON parser — "
                    "return ONLY valid JSON. No markdown fences, no backticks, no comments, no explanation text."
                ),
                user=_build_ai_prompt(self.name, self.prompt, self.industry),
                temperature=0.70,
            )
            cleaned = re.sub(r'^```(?:json)?\s*|```\s*$', '', raw.strip(), flags=re.MULTILINE).strip()
            data    = json.loads(cleaned)

            # Merge contact info from prompt if AI didn't find it
            if not data.get("contact_email") and self.contacts.get("email"):
                data["contact_email"] = self.contacts["email"]
            if not data.get("contact_phone") and self.contacts.get("phone"):
                data["contact_phone"] = self.contacts["phone"]

            return data

        except json.JSONDecodeError as e:
            logger.error(f"JSON parse failed: {e}")
            return {**_generic_fallback_data(), "contact_email": self.contacts.get("email",""), "contact_phone": self.contacts.get("phone","")}
        except Exception as e:
            logger.error(f"AI call failed: {e}", exc_info=True)
            return {**_generic_fallback_data(), "contact_email": self.contacts.get("email",""), "contact_phone": self.contacts.get("phone","")}

    # ── Build ─────────────────────────────────────────────────────────────────

    def build(self) -> Dict[str, Any]:
        try:
            d     = self._get_data()
            t     = self.theme
            name  = self.name

            email = d.get("contact_email", "")
            phone = d.get("contact_phone", "")

            raw_secs = d.get("sections") or list(VALID_SECTIONS)
            ordered, seen = [], set()
            for s in raw_secs:
                sid = str(s).lower().strip()
                if sid in VALID_SECTIONS and sid not in seen:
                    ordered.append(sid)
                    seen.add(sid)
            if "hero"    not in seen: ordered.insert(0, "hero")
            if "contact" not in seen: ordered.append("contact")

            nav_items = d.get("nav") or ["Services","About","FAQ","Contact"]
            cta_label = d.get("hero", {}).get("cta", "Get Started")

            hero_v  = self._hero_variant()
            feat_v  = self._feat_variant()
            testi_v = self._testi_variant()
            faq_v   = self._faq_variant()
            extras  = self._extra_sections(d)

            parts = [_nav(name, nav_items, cta_label)]

            for sid in ordered:
                html = ""

                if sid == "hero":
                    if   hero_v == "restaurant":  html = _hero_restaurant(name, d, self.industry)
                    elif hero_v == "centered":    html = _hero_centered(name, d, self.industry)
                    elif hero_v == "stats":       html = _hero_stats(name, d, self.industry)
                    elif hero_v == "minimal":     html = _hero_minimal(name, d, self.industry)
                    elif hero_v == "image_left":  html = _hero_image_left(name, d, self.industry)
                    elif hero_v == "bold_bg":     html = _hero_bold_bg(name, d, self.industry)
                    elif hero_v == "video_style": html = _hero_video_style(name, d, self.industry)
                    else:                         html = _hero_split(name, d, self.industry)

                    # Inject process steps right after hero for eligible industries
                    if "process" in extras:
                        html += extras.pop("process")

                elif sid == "trust":
                    html = _trust_band(d.get("trust_badges") or [])

                elif sid == "features":
                    feats = d.get("features") or []
                    if feats:
                        if   feat_v == "icon_list":       html = _feat_icon_list(feats, self.industry)
                        elif feat_v == "alternating":     html = _feat_alternating(feats, self.industry)
                        elif feat_v == "big_numbers":     html = _feat_big_numbers(feats)
                        elif feat_v == "checklist_split": html = _feat_checklist_split(feats, self.industry)
                        elif feat_v == "three_columns":   html = _feat_three_columns_icons(feats)
                        else:                             html = _feat_cards(feats)

                    # Inject gallery after features for visual industries
                    if "gallery" in extras:
                        html += extras.pop("gallery")

                elif sid == "pricing":
                    tiers = d.get("pricing")
                    if isinstance(tiers, list) and len(tiers) > 0:
                        v = self._price_variant(tiers)
                        if v == "project": html = _price_project(tiers)
                        else:              html = _price_tiers(tiers)
                    elif tiers is None:
                        html = _price_contact_cta()

                elif sid == "testimonials":
                    tevs = d.get("testimonials") or []
                    if testi_v == "featured":
                        html = _testimonials_featured(tevs)
                    else:
                        html = _testimonials(tevs)

                elif sid == "faq":
                    faqs = d.get("faq") or []
                    if faq_v == "two_col":
                        html = _faq_two_col(faqs)
                    else:
                        html = _faq(faqs)

                elif sid == "contact":
                    html = _contact(name, d, email, phone, self.industry)

                if html:
                    parts.append(html)

            parts.append(_footer(name, d, nav_items, email, phone))

            body_html = "\n".join(parts)
            css_block = _build_css(t)

            page = f"""{css_block}
<div style="padding-top:64px;">
{body_html}
{REVEAL_JS}
</div>"""

            metadata = {
                "business_name": name,
                "industry":      self.industry,
                "theme":         t["id"],
                "version":       self.version,
                "sections":      ordered,
                "hero_variant":  hero_v,
                "feat_variant":  feat_v,
                "seed":          self._seed,
                "has_email":     bool(email),
                "has_phone":     bool(phone),
                "status":        "success",
            }

            logger.info(f"Built | '{name}' | {self.industry} | {t['id']} | hero={hero_v} | feat={feat_v} | seed={self._seed}")
            return {"html": page, "metadata": metadata}

        except Exception as e:
            logger.error(f"Build error: {e}", exc_info=True)
            return {
                "html": f'<div style="padding:3rem;font-family:sans-serif;color:#ef4444;text-align:center;"><h2>Build failed</h2><p style="margin-top:0.5rem;font-size:0.875rem;">{e}</p></div>',
                "metadata": {"status": "error", "error": str(e)},
            }

# =============================================================================
# PUBLIC API
# =============================================================================

def generate_ai_plan(ai_input: Dict[str, Any], version: int = 1) -> Dict[str, Any]:
    """
    Entry point called by dashboard_websites_routes.py:
        generate_ai_plan(ai_input={"business_name": "Apex Fitness", "prompt": "..."}, version=1)

    business_name → MasterArchitect.name → shown in nav, footer, headings
    prompt        → AI copy generation only — NEVER shown as a display name
    """
    arch = MasterArchitect(
        business_name=ai_input.get("business_name", ""),
        prompt=ai_input.get("prompt", ""),
        version=version,
    )
    return arch.build()


def rewrite_content(original_text: str, tone: str = "professional",
                    business_context: str = "") -> List[str]:
    """Generate tone variants for the inline editor."""
    if not AI_AVAILABLE:
        return [original_text, original_text, original_text]
    try:
        raw = chat_completion(
            system="Return ONLY a JSON array of 3 strings. No markdown, no extra text.",
            user=f"Rewrite in 3 {tone} variations.\nContext: {business_context}\nOriginal: {original_text}\nReturn: [\"v1\",\"v2\",\"v3\"]",
            temperature=0.8,
        )
        cleaned = re.sub(r'^```(?:json)?\s*|```\s*$', '', raw.strip(), flags=re.MULTILINE).strip()
        result  = json.loads(cleaned)
        if isinstance(result, list):
            return result[:3]
    except Exception:
        pass
    return [original_text, original_text, original_text]


def get_design_tokens(theme_id: str = "ocean") -> Dict[str, Any]:
    """Return CSS variable map for a theme — used by the editor."""
    t = THEMES.get(theme_id, THEMES["ocean"])
    return {"theme_id": t["id"], "mode": t["mode"], "css_vars": t["vars"]}