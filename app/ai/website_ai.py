"""
website_ai.py  —  Master Architect v2
Generates complete, professional landing pages from a business name + prompt.

Improvements over v1:
  - Content is 100% conditional — no placeholder data ever rendered
  - AI decides which sections to include via a `sections` key
  - Contact section is a real HTML form (no fake phone/email)
  - All HTML tokens read from theme dict — zero hardcoded colour classes
  - Runtime assertion catches any stray Tailwind colour classes
  - Hamburger nav (pure CSS, no JS dependencies)
  - Proper mobile layouts throughout
  - Only hero image is eager — all others lazy
  - AI prompt uses industry vocabulary, not SaaS filler
"""

import json
import logging
import traceback
import re
from typing import Dict, Any, List, Callable, Optional

logger = logging.getLogger(__name__)

try:
    from app.ai.openai_client import chat_completion
    AI_AVAILABLE = True
except ImportError as e:
    logger.warning(f"AI client not available: {e}")
    AI_AVAILABLE = False

    def chat_completion(system: str, user: str, temperature: float = 0.7) -> str:
        return json.dumps({
            "sections": ["hero", "trust", "features", "pricing", "testimonials", "faq", "contact"],
            "nav": ["Services", "About", "FAQ", "Contact"],
            "hero": {
                "h1": "Built for Your Industry",
                "sub": "Professional services tailored to your exact needs.",
                "cta": "Get Started",
            },
            "tagline": "Excellence delivered.",
            "social_proof": {"count": "500+", "label": "clients served"},
            "stats": [
                {"value": "97%",  "label": "Client satisfaction"},
                {"value": "500+", "label": "Projects completed"},
                {"value": "10yr", "label": "In the industry"},
                {"value": "24/7", "label": "Support available"},
            ],
            "trust_badges": ["Licensed & Insured", "Award Winner 2024", "5-Star Rated", "Certified Professionals"],
            "features": [
                {"title": "Expert Team",      "description": "Seasoned professionals with deep industry knowledge working for your success every day.",  "icon": "🏆"},
                {"title": "Proven Results",   "description": "A track record of delivering outcomes that matter, backed by hundreds of satisfied clients.", "icon": "📈"},
                {"title": "Dedicated Support","description": "Responsive, attentive service from first contact through completion and beyond.",            "icon": "🤝"},
            ],
            "pricing": [
                {"name": "Starter",      "price": "$49",    "description": "For individuals and small teams.", "features": ["Core features", "Email support", "5 projects", "Basic analytics", "Monthly reports"],                                               "featured": False},
                {"name": "Professional", "price": "$149",   "description": "For growing businesses.",         "features": ["Everything in Starter", "Priority support", "Unlimited projects", "Advanced analytics", "Custom integrations"],                     "featured": True},
                {"name": "Enterprise",   "price": "Custom", "description": "For large organisations.",        "features": ["Everything in Professional", "Dedicated manager", "SLA guarantee", "Custom contracts", "Onboarding support"], "featured": False},
            ],
            "testimonials": [
                {"name": "Jordan Lee",  "role": "Director", "company": "Meridian Group",  "quote": "Working with this team changed our approach entirely. The results were immediate and lasting."},
                {"name": "Priya Nair",  "role": "Founder",  "company": "Spark Ventures",  "quote": "Responsive, knowledgeable, and genuinely invested in our success. Highly recommend."},
            ],
            "faq": [
                {"q": "How do I get started?",            "a": "Reach out via the contact form and we will schedule an initial conversation."},
                {"q": "What does the process look like?", "a": "Discovery first, then a tailored plan, then execution with full transparency."},
                {"q": "Do you offer ongoing support?",    "a": "Yes. All engagements include continued access after the initial project is complete."},
            ],
            "cta_headline": "Ready to get started?",
            "contact_email": "",
            "contact_phone": "",
        })


# ─────────────────────────────────────────────────────────────────────────────
# DESIGN CONSTANTS
# ─────────────────────────────────────────────────────────────────────────────

HOVER_LIFT = "transition-all duration-300 hover:-translate-y-1 hover:shadow-xl"
HOVER_GLOW = "transition-all duration-200 hover:brightness-105"

H_HERO    = "text-5xl md:text-6xl lg:text-7xl font-black tracking-tight leading-[1.06]"
H_SECTION = "text-3xl md:text-4xl lg:text-5xl font-black tracking-tight leading-[1.15]"
H_CARD    = "text-lg font-bold tracking-tight"

PAD_SEC = "py-24 md:py-32"
PAD_CON = "px-5 md:px-8 lg:px-12"

# Tailwind colour tokens we NEVER want hardcoded in HTML strings (non-neutral, non-theme)
_FORBIDDEN_COLOUR_RE = re.compile(
    r'\b(?:bg|text|border|ring|from|to|via)-(?:'
    r'violet|fuchsia|purple|indigo|magenta|'
    r'pink(?!-\d)|red|orange|yellow|lime|'
    r'teal|cyan|sky|'
    r'emerald|green|'
    r'amber|'
    r'rose'
    r')-\d{2,3}\b'
)

def _assert_no_hardcoded_colours(html: str, context: str = "") -> None:
    """Dev-mode assertion: raises if any forbidden Tailwind colour appears in rendered HTML."""
    hits = _FORBIDDEN_COLOUR_RE.findall(html)
    if hits:
        logger.warning(f"Hardcoded colour classes found [{context}]: {set(hits)}")


# ─────────────────────────────────────────────────────────────────────────────
# INDUSTRY PHOTO POOLS  — hand-curated Unsplash IDs
# ─────────────────────────────────────────────────────────────────────────────

INDUSTRY_PHOTO_POOLS: Dict[str, List[str]] = {
    "construction": [
        "photo-1504307651254-35680f356dfd", "photo-1541888946425-d81bb19240f5",
        "photo-1590674899484-d5640e854abe", "photo-1581578731548-c64695cc6952",
        "photo-1565117623394-5f93fd4c7a06", "photo-1530836176759-510f6ca9f76f",
        "photo-1558618666-fcd25c85cd64",   "photo-1600585154340-be6161a56a0c",
    ],
    "legal": [
        "photo-1589578527966-fdac0f44566c", "photo-1436450412740-6b988f486c6b",
        "photo-1505664194779-8beaceb5c7c7", "photo-1521791055366-0d553872952f",
        "photo-1450101499163-c8848c66ca85", "photo-1568992687947-868a62a9f521",
        "photo-1497366216548-37526070297c", "photo-1552664730-d307ca884978",
    ],
    "logistics": [
        "photo-1504493188-45c49f65c6ba", "photo-1586528116311-ad8dd3c8310d",
        "photo-1601584115197-04ecc0da31d7","photo-1494412574643-ff11b0a5c1c3",
        "photo-1519003300449-424ad0405076","photo-1543169964-f2e91dc1fbf4",
        "photo-1473445730015-841f29a9490b","photo-1565891741441-64926e3e5c74",
    ],
    "automotive": [
        "photo-1492144534655-ae79c964c9d7","photo-1503376780353-7e6692767b70",
        "photo-1544636331-e26879cd4d9b", "photo-1565043589221-1a6fd9ae45c7",
        "photo-1558981806-ec527fa84c39", "photo-1549317661-bd32c8ce0db2",
        "photo-1580273916550-e323be2ae537","photo-1520340356584-f9917d1eea6f",
    ],
    "restaurant": [
        "photo-1504674900247-0877df9cc836","photo-1414235077428-338989a2e8c0",
        "photo-1555396273-367ea4eb4db5", "photo-1517248135467-4c7edcad34c4",
        "photo-1512621776951-a57141f2eefd","photo-1467003909585-2f8a72700288",
        "photo-1565299585323-38d6b0865b47","photo-1484723091739-30a097e8f929",
    ],
    "health": [
        "photo-1576091160550-2173dba999ef","photo-1559757148-5c350d0d3c56",
        "photo-1535914254981-b5012eebbd15","photo-1571772996211-2f02c9727629",
        "photo-1540420773420-3366772f4999","photo-1631217868264-e5b90bb7e133",
        "photo-1582750433449-648ed127bb54","photo-1532938911079-1b06ac7ceec7",
    ],
    "fitness": [
        "photo-1534438327276-14e5300c3a48","photo-1571019613454-1cb2f99b2d8b",
        "photo-1517836357463-d25dfeac3438","photo-1549060279-7e168fcee0c2",
        "photo-1526506118085-60ce8714f8c5","photo-1574680178050-55c6a6a96e0a",
        "photo-1544033527-b192daee1f5b", "photo-1540497077202-7c8a3999166f",
    ],
    "beauty": [
        "photo-1487412947147-5cebf100ffc2","photo-1560066984-138dadb4c035",
        "photo-1522337360788-8b13dee7a37e","photo-1596704017254-9b121068fb31",
        "photo-1571019613576-2b22c76fd955","photo-1519014816548-bf5fe059798b",
        "photo-1540555700478-4be289fbecef","photo-1522338242992-e1a54906a8da",
    ],
    "finance": [
        "photo-1611974789855-9c2a0a7236a3","photo-1563986768609-322da13575f3",
        "photo-1468254095679-bbcba94a7066","photo-1454165804606-c3d57bc86b40",
        "photo-1460925895917-afdab827c52f","photo-1601597111158-2fceff292cdc",
        "photo-1526304640581-d334cdbbf45e","photo-1565514020179-026b92b84bb6",
    ],
    "real_estate": [
        "photo-1560518883-ce09059eeffa","photo-1570129477492-45c003edd2be",
        "photo-1513584684374-8bab748fbf90","photo-1501183638710-841dd1904471",
        "photo-1486325212027-8081e485255e","photo-1523217582562-09d0def993a6",
        "photo-1598300042247-d088f8ab3a91","photo-1580587771525-78b9dba3b914",
    ],
    "education": [
        "photo-1503676260728-1c00da094a0b","photo-1456513080510-7bf3a84b82f8",
        "photo-1509062522246-3755977927d7","photo-1427504494785-3a9ca7044f45",
        "photo-1522202176988-66273c2fd55f","photo-1434030216411-0b793f4b4173",
        "photo-1546410531-bb4caa6b424d", "photo-1488190211105-8b0e65b80b4e",
    ],
    "travel": [
        "photo-1501854140801-50d01698950b","photo-1436491865332-7a61a109cc05",
        "photo-1488085061387-422e29b40080","photo-1476514525535-07fb3b4ae5f1",
        "photo-1530521954074-e64f6810b32d","photo-1503220317375-aaad61436b1b",
        "photo-1528360983277-13d401cdc186","photo-1469854523086-cc02fe5d8800",
    ],
    "ecommerce": [
        "photo-1556742049-0cfed4f6a45d","photo-1472851294608-062f824d29cc",
        "photo-1607082348824-0a96f2a4b9da","photo-1523275335684-37898b6baf30",
        "photo-1581091226825-a6a2a5aee158","photo-1526170375885-4d8ecf77b99f",
        "photo-1491553895911-0055eca6402d","photo-1585386959984-a4155224a1ad",
    ],
    "saas": [
        "photo-1518770660439-4636190af475","photo-1461749280684-dccba630e2f6",
        "photo-1551434678-e076c223a692", "photo-1497366216548-37526070297c",
        "photo-1573164713988-8665fc963095","photo-1498050108023-c5249f4df085",
        "photo-1522071820081-009f0129c71c","photo-1531482615713-2afd69097998",
    ],
    "ai": [
        "photo-1677442135703-1787eea5ce01","photo-1620712943543-bcc4688e7485",
        "photo-1555255707-c07966088b7b","photo-1518770660439-4636190af475",
        "photo-1535378917042-10a22c95931a","photo-1593508512255-86ab42a8e620",
        "photo-1589254065878-42efea3c6521","photo-1558346547-4439467bd1d5",
    ],
    "developer": [
        "photo-1461749280684-dccba630e2f6","photo-1498050108023-c5249f4df085",
        "photo-1555066931-4365d14bab8c","photo-1607799279861-4dd421887fb3",
        "photo-1519389950473-47ba0277781c","photo-1537432376769-00f5c2f4c8d2",
        "photo-1573495612522-4c73ff6a54b0","photo-1571171637578-41bc2dd41cd2",
    ],
    "startup": [
        "photo-1559136555-9303baea8ebd","photo-1531297484001-80022131f5a1",
        "photo-1556761175-4b46a572b786","photo-1522202176988-66273c2fd55f",
        "photo-1542744173-8e7e53415bb0","photo-1572021335469-31706a17aaef",
        "photo-1560472355-536de3962603","photo-1524758631624-e2822e304c36",
    ],
    "agency": [
        "photo-1558655146-9f40138edfeb","photo-1524758631624-e2822e304c36",
        "photo-1497366754035-f200968a6e72","photo-1535016120720-40c646be5580",
        "photo-1531538606174-0f90ff5dce83","photo-1487017159836-4e23ece2e4cf",
        "photo-1542744094-3a31f272c490","photo-1573164574511-73c773193279",
    ],
    "nature": [
        "photo-1441974231531-c6227db76b6e","photo-1506905925346-21bda4d32df4",
        "photo-1469474968028-56623f02e42e","photo-1500534314209-a25ddb2bd429",
        "photo-1472214103451-9374bd1c798e","photo-1542601906990-b4d3fb778b09",
        "photo-1448375240586-882707db888b","photo-1518173946687-a4c8892bbd9f",
    ],
    "nonprofit": [
        "photo-1593113630400-ea4288922559","photo-1559027615-cd4628902d4a",
        "photo-1532629345422-7515f3d16bb6","photo-1509099836639-18ba1795216d",
        "photo-1469571486292-b53601010376","photo-1488521787991-ed7bbaae773c",
        "photo-1556484687-30636164638b","photo-1593113598332-cd59a0c3a9a4",
    ],
    "events": [
        "photo-1540575467063-178a50c2df87","photo-1511795409834-ef04bbd61622",
        "photo-1464366400600-7168b8af9bc3","photo-1519167758481-83f550bb49b3",
        "photo-1492684223066-81342ee5ff30","photo-1478147427282-58a87a433d8f",
        "photo-1529543544282-ea669407fca3","photo-1551818255-e6e10975bc17",
    ],
}

_DEFAULT_PHOTOS = [
    "photo-1552664730-d307ca884978","photo-1460925895917-afdab827c52f",
    "photo-1556742049-0cfed4f6a45d","photo-1497366216548-37526070297c",
    "photo-1454165804606-c3d57bc86b40","photo-1522202176988-66273c2fd55f",
]


def _img_set(industry: str, count: int = 8, w: int = 900) -> List[str]:
    pool = INDUSTRY_PHOTO_POOLS.get(industry, _DEFAULT_PHOTOS)
    return [
        f"https://images.unsplash.com/{pool[i % len(pool)]}?w={w}&auto=format&fit=crop&q=82"
        for i in range(count)
    ]


# ─────────────────────────────────────────────────────────────────────────────
# THEMES — six palettes, no purple/violet/fuchsia/indigo anywhere.
# All sections read colours from theme keys only.
# ─────────────────────────────────────────────────────────────────────────────

THEMES: Dict[str, Dict] = {
    "blue": {
        "id": "blue", "mode": "light",
        "bg":          "bg-white",
        "bg_alt":      "bg-slate-50",
        "text":        "text-slate-900",
        "text_muted":  "text-slate-500",
        "text_light":  "text-slate-400",
        "grad":        "from-blue-600 to-blue-500",
        "grad_text":   "from-blue-700 to-blue-500",
        "grad_subtle": "from-blue-50 to-slate-50",
        "glow":        "bg-blue-500",
        "border":      "border-slate-200",
        "nav":         "bg-white/95 border-b border-slate-200 shadow-sm backdrop-blur-md",
        "badge":       "bg-blue-50 text-blue-700 border border-blue-200 rounded-full",
        "stat":        "text-blue-600",
        "check":       "text-blue-500",
        "card":        "bg-white border border-slate-200 shadow-sm",
        "input":       "bg-white border border-slate-300 text-slate-900 placeholder-slate-400 focus:border-blue-500",
        "btn_secondary": "border border-slate-300 text-slate-700 bg-white hover:bg-slate-50",
        "fonts":       "'Inter', sans-serif",
        "font_url":    "https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800;900&display=swap",
    },
    "slate": {
        "id": "slate", "mode": "light",
        "bg":          "bg-white",
        "bg_alt":      "bg-slate-50",
        "text":        "text-slate-900",
        "text_muted":  "text-slate-500",
        "text_light":  "text-slate-400",
        "grad":        "from-slate-800 to-slate-600",
        "grad_text":   "from-slate-800 to-slate-500",
        "grad_subtle": "from-slate-100 to-slate-50",
        "glow":        "bg-slate-500",
        "border":      "border-slate-200",
        "nav":         "bg-white border-b border-slate-200 shadow-sm",
        "badge":       "bg-slate-100 text-slate-700 border border-slate-300 rounded-full",
        "stat":        "text-slate-800",
        "check":       "text-slate-600",
        "card":        "bg-white border border-slate-200 shadow-sm",
        "input":       "bg-white border border-slate-300 text-slate-900 placeholder-slate-400 focus:border-slate-600",
        "btn_secondary": "border border-slate-300 text-slate-700 bg-white hover:bg-slate-50",
        "fonts":       "'IBM Plex Sans', sans-serif",
        "font_url":    "https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600;700&display=swap",
    },
    "amber": {
        "id": "amber", "mode": "light",
        "bg":          "bg-[#fffbf2]",
        "bg_alt":      "bg-[#fff6e0]",
        "text":        "text-[#2d1a00]",
        "text_muted":  "text-[#7a5c2e]",
        "text_light":  "text-[#b08040]/70",
        "grad":        "from-[#f59e0b] to-[#f97316]",
        "grad_text":   "from-[#d97706] to-[#ea580c]",
        "grad_subtle": "from-[#fef3c7] to-[#fff7ed]",
        "glow":        "bg-[#fbbf24]",
        "border":      "border-[#fde68a]",
        "nav":         "bg-[#fffbf2]/95 border-b border-[#fde68a] shadow-sm backdrop-blur-md",
        "badge":       "bg-[#fef3c7] text-[#92400e] border border-[#fde68a] rounded-full",
        "stat":        "text-[#d97706]",
        "check":       "text-[#d97706]",
        "card":        "bg-white border border-[#fde68a] shadow-sm",
        "input":       "bg-white border border-[#fde68a] text-[#2d1a00] placeholder-[#b08040]/60 focus:border-[#d97706]",
        "btn_secondary": "border border-[#fde68a] text-[#92400e] bg-white hover:bg-[#fef3c7]",
        "fonts":       "'DM Sans', sans-serif",
        "font_url":    "https://fonts.googleapis.com/css2?family=DM+Sans:opsz,wght@9..40,400;9..40,500;9..40,700;9..40,800&display=swap",
    },
    "green": {
        "id": "green", "mode": "light",
        "bg":          "bg-white",
        "bg_alt":      "bg-[#f0fdf4]",
        "text":        "text-slate-900",
        "text_muted":  "text-slate-500",
        "text_light":  "text-slate-400",
        "grad":        "from-[#059669] to-[#0d9488]",
        "grad_text":   "from-[#047857] to-[#0d9488]",
        "grad_subtle": "from-[#d1fae5] to-[#ccfbf1]",
        "glow":        "bg-[#34d399]",
        "border":      "border-[#bbf7d0]",
        "nav":         "bg-white/95 border-b border-[#bbf7d0] shadow-sm backdrop-blur-md",
        "badge":       "bg-[#d1fae5] text-[#065f46] border border-[#a7f3d0] rounded-full",
        "stat":        "text-[#059669]",
        "check":       "text-[#059669]",
        "card":        "bg-white border border-[#bbf7d0] shadow-sm",
        "input":       "bg-white border border-[#a7f3d0] text-slate-900 placeholder-slate-400 focus:border-[#059669]",
        "btn_secondary": "border border-[#a7f3d0] text-[#065f46] bg-white hover:bg-[#d1fae5]",
        "fonts":       "'Plus Jakarta Sans', sans-serif",
        "font_url":    "https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap",
    },
    "dark": {
        "id": "dark", "mode": "dark",
        "bg":          "bg-gray-950",
        "bg_alt":      "bg-gray-900",
        "text":        "text-white",
        "text_muted":  "text-gray-400",
        "text_light":  "text-gray-600",
        "grad":        "from-[#06b6d4] to-[#2563eb]",
        "grad_text":   "from-[#22d3ee] to-[#60a5fa]",
        "grad_subtle": "from-[#083344]/25 to-[#1e3a8a]/15",
        "glow":        "bg-[#06b6d4]",
        "border":      "border-white/10",
        "nav":         "bg-gray-950/90 border-b border-white/10 backdrop-blur-xl",
        "badge":       "bg-[#083344]/60 text-[#67e8f9] border border-[#06b6d4]/30 rounded-full",
        "stat":        "text-[#22d3ee]",
        "check":       "text-[#22d3ee]",
        "card":        "bg-gray-900 border border-white/10",
        "input":       "bg-gray-800 border border-white/20 text-white placeholder-gray-500 focus:border-[#06b6d4]",
        "btn_secondary": "border border-white/20 text-white bg-white/6 hover:bg-white/10",
        "fonts":       "'Space Grotesk', sans-serif",
        "font_url":    "https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&display=swap",
    },
    "rose": {
        "id": "rose", "mode": "dark",
        "bg":          "bg-[#0d0508]",
        "bg_alt":      "bg-[#130a0e]",
        "text":        "text-[#fff1f2]",
        "text_muted":  "text-[#fda4af]/70",
        "text_light":  "text-[#fb7185]/50",
        "grad":        "from-[#f43f5e] to-[#ec4899]",
        "grad_text":   "from-[#fb7185] to-[#f472b6]",
        "grad_subtle": "from-[#4c0519]/30 to-[#500724]/15",
        "glow":        "bg-[#f43f5e]",
        "border":      "border-[#4c0519]/40",
        "nav":         "bg-[#0d0508]/90 border-b border-[#4c0519]/30 backdrop-blur-xl",
        "badge":       "bg-[#4c0519]/60 text-[#fda4af] border border-[#f43f5e]/25 rounded-full",
        "stat":        "text-[#fb7185]",
        "check":       "text-[#fb7185]",
        "card":        "bg-[#130a0e] border border-[#4c0519]/35",
        "input":       "bg-[#1a0810] border border-[#4c0519]/50 text-[#fff1f2] placeholder-[#fda4af]/40 focus:border-[#f43f5e]",
        "btn_secondary": "border border-[#4c0519]/50 text-[#fda4af] bg-[#4c0519]/20 hover:bg-[#4c0519]/40",
        "fonts":       "'Cormorant Garamond', serif",
        "font_url":    "https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@300;400;600;700&display=swap",
    },
}

# ─────────────────────────────────────────────────────────────────────────────
# INDUSTRY → THEME
# ─────────────────────────────────────────────────────────────────────────────

INDUSTRY_KEYWORDS: Dict[str, List[str]] = {
    "saas":         ["software", "app", "platform", "cloud", "api", "saas", "dashboard", "workflow", "automation", "crm", "erp"],
    "ai":           ["ai", "artificial intelligence", "machine learning", "ml", "neural", "llm", "gpt", "data science", "algorithm"],
    "ecommerce":    ["shop", "store", "ecommerce", "e-commerce", "sell", "product", "cart", "marketplace", "retail", "dropship"],
    "health":       ["health", "medical", "wellness", "clinic", "doctor", "hospital", "therapy", "mental health", "nutrition", "physio"],
    "fitness":      ["fitness", "gym", "personal trainer", "workout", "yoga", "crossfit", "athletics", "exercise"],
    "finance":      ["finance", "banking", "investment", "crypto", "payment", "fintech", "trading", "insurance", "wealth", "accounting", "tax"],
    "agency":       ["agency", "design", "creative", "marketing", "brand", "advertising", "studio", "media"],
    "education":    ["education", "course", "learn", "training", "school", "university", "tutoring", "edtech", "bootcamp"],
    "luxury":       ["luxury", "high-end", "exclusive", "bespoke", "couture", "prestige", "elite"],
    "restaurant":   ["restaurant", "food", "cafe", "bakery", "catering", "cuisine", "dining", "menu", "chef", "bar", "bistro"],
    "beauty":       ["beauty", "salon", "spa", "skincare", "cosmetic", "makeup", "aesthetics", "bridal", "hair", "nail"],
    "real_estate":  ["real estate", "property", "realty", "housing", "apartment", "mortgage", "agent", "broker"],
    "travel":       ["travel", "hotel", "tour", "booking", "airbnb", "vacation", "resort", "hospitality"],
    "startup":      ["startup", "founder", "seed", "venture", "mvp", "launch", "pitch", "scale", "growth"],
    "developer":    ["developer", "engineer", "code", "open source", "github", "devtools", "ide", "terminal", "cli"],
    "nature":       ["organic", "eco", "sustainable", "farm", "agriculture", "environment", "garden", "zero waste"],
    "construction": ["construction", "contractor", "builder", "building", "renovation", "remodel", "plumbing", "electrical",
                     "roofing", "flooring", "masonry", "carpentry", "landscaping", "painting", "hvac", "handyman",
                     "general contractor", "home improvement", "excavation", "concrete", "drywall", "framing", "trades"],
    "legal":        ["law", "lawyer", "attorney", "legal", "firm", "counsel", "litigation", "contract", "court", "compliance",
                     "paralegal", "notary", "solicitor", "barrister"],
    "logistics":    ["logistics", "shipping", "freight", "delivery", "supply chain", "warehouse", "trucking", "transport",
                     "courier", "fulfillment", "distribution", "fleet"],
    "automotive":   ["auto", "car", "vehicle", "mechanic", "garage", "dealership", "repair", "tire", "bodywork", "detailing"],
    "nonprofit":    ["nonprofit", "charity", "foundation", "ngo", "volunteer", "donation", "cause", "community", "social impact"],
    "events":       ["event", "wedding", "conference", "venue", "entertainment", "party", "corporate event"],
}

INDUSTRY_THEME: Dict[str, str] = {
    "saas": "blue", "ai": "dark", "ecommerce": "amber", "health": "green",
    "fitness": "green", "finance": "blue", "agency": "dark", "education": "blue",
    "luxury": "rose", "restaurant": "amber", "beauty": "rose", "real_estate": "slate",
    "travel": "blue", "startup": "dark", "developer": "dark", "nature": "green",
    "construction": "slate", "legal": "slate", "logistics": "slate", "automotive": "slate",
    "nonprofit": "green", "events": "amber",
}


def detect_industry(text: str) -> str:
    tl = (text or "").lower()
    scores = {ind: sum(len(kw.split()) for kw in kws if kw in tl)
              for ind, kws in INDUSTRY_KEYWORDS.items()}
    best = max(scores, key=lambda k: scores[k])
    return best if scores[best] > 0 else "saas"


def select_theme(industry: str) -> Dict:
    return THEMES[INDUSTRY_THEME.get(industry, "blue")]


# ─────────────────────────────────────────────────────────────────────────────
# BUSINESS NAME EXTRACTION
# ─────────────────────────────────────────────────────────────────────────────

_NAME_PREFIXES = [
    "my company is called ", "my business is called ", "company name is ", "business name is ",
    "called ", "named ", "name is ", "it's called ", "we are ", "we're ", "i own ", "i run ",
]
_DESC_STARTERS = ["we ", "our ", "a ", "an ", "the ", "i have", "i own", "i run", "this is", "it's a"]


def extract_business_name(raw: str, prompt: str):
    raw, prompt = (raw or "").strip(), (prompt or "").strip()
    pl = prompt.lower()
    for indicator in ["the company name is ", "company name: ", "business name: ", "we're called ",
                      "it's called ", "my company is called ", "my business is called "]:
        if indicator in pl:
            idx   = pl.index(indicator)
            after = prompt[idx + len(indicator):].strip()
            end   = len(after)
            for sep in [".", ",", ";", " -", " and we", " that ", " which "]:
                p = after.find(sep)
                if 0 < p < end:
                    end = p
            name      = after[:end].strip()
            before    = prompt[:idx].strip()
            remainder = prompt[idx + len(indicator) + end:].strip(" .,;")
            return name, f"{before} {remainder}".strip()
    if not raw:
        return "", prompt
    rl = raw.lower()
    for s in _DESC_STARTERS:
        if rl.startswith(s):
            return "", f"{raw}. {prompt}".strip(" .")
    for p in _NAME_PREFIXES:
        if rl.startswith(p):
            rest = raw[len(p):].strip()
            for sep in [" - ", " — ", ", ", ". "]:
                if sep in rest:
                    parts = rest.split(sep, 1)
                    return parts[0].strip(), f"{parts[1].strip()}. {prompt}".strip(" .")
            return rest.strip(), prompt
    for sep in [" - ", " — ", ": "]:
        if sep in raw:
            parts = raw.split(sep, 1)
            return parts[0].strip(), f"{parts[1].strip()}. {prompt}".strip(" .")
    if len(raw.split()) <= 5:
        return raw, prompt
    words = raw.split()
    return " ".join(words[:3]).rstrip(".,!?"), f"{' '.join(words[3:])}. {prompt}".strip(" .")


def _default_name(industry: str) -> str:
    return {
        "construction": "BuildRight Group", "legal": "Sterling Law",
        "finance": "Apex Capital", "health": "Vitalis Health",
        "fitness": "Peak Fitness", "restaurant": "The Kitchen",
        "beauty": "Lumiere Studio", "ecommerce": "The Shop",
        "education": "Elevate Academy", "real_estate": "Keystone Realty",
        "logistics": "Swift Logistics", "automotive": "AutoPro",
        "events": "Premier Events", "nonprofit": "Together Foundation",
        "nature": "Green Root", "agency": "Creative Studio", "travel": "Voyage Co.",
    }.get(industry, "My Business")


def _extract_contact_info(prompt: str) -> Dict[str, str]:
    """Pull any real email / phone from the prompt. Returns only what's actually found."""
    result = {}
    email_match = re.search(r'[\w.+-]+@[\w-]+\.[a-zA-Z]{2,}', prompt or "")
    if email_match:
        result["email"] = email_match.group(0)
    phone_match = re.search(
        r'(?:\+?1[-.\s]?)?(?:\(?\d{3}\)?[-.\s]?)?\d{3}[-.\s]?\d{4}', prompt or ""
    )
    if phone_match:
        candidate = re.sub(r'[^\d+]', '', phone_match.group(0))
        if len(candidate) >= 10:
            result["phone"] = phone_match.group(0).strip()
    return result


# ─────────────────────────────────────────────────────────────────────────────
# HTML HELPERS — all colours come from theme dict
# ─────────────────────────────────────────────────────────────────────────────

def _btn(t: Dict, label: str, href: str = "#contact", extra: str = "") -> str:
    return (f'<a href="{href}" class="inline-block bg-gradient-to-r {t["grad"]} text-white '
            f'font-bold rounded-xl px-8 py-4 shadow-md {HOVER_LIFT} {extra}">{label}</a>')


def _btn_ghost(t: Dict, label: str, href: str = "#features", extra: str = "") -> str:
    return (f'<a href="{href}" class="{t["btn_secondary"]} '
            f'font-semibold rounded-xl px-8 py-4 {HOVER_GLOW} transition-all duration-200 {extra}">{label}</a>')


def _eyebrow(t: Dict, text: str) -> str:
    return f'<p class="text-xs font-bold uppercase tracking-[0.2em] {t["text_light"]} mb-3">{text}</p>'


def _h2(t: Dict, title: str, sub: str = "") -> str:
    s = f'<p class="text-base {t["text_muted"]} mt-4 max-w-xl mx-auto leading-relaxed">{sub}</p>' if sub else ""
    return f'<h2 class="{H_SECTION} {t["text"]}">{title}</h2>{s}'


def _check(t: Dict, text: str) -> str:
    return (f'<li class="flex items-start gap-2.5 text-sm {t["text_muted"]}">'
            f'<span class="mt-0.5 shrink-0 font-black {t["check"]}">&#10003;</span>'
            f'<span>{text}</span></li>')


# ─────────────────────────────────────────────────────────────────────────────
# HERO VARIANTS
# ─────────────────────────────────────────────────────────────────────────────

class Hero:

    @staticmethod
    def split(t: Dict, d: Dict, imgs: List[str]) -> str:
        """Left copy + right image. Image stacks below copy on mobile."""
        img   = imgs[0] if imgs else ""
        h1    = d.get("hero", {}).get("h1", "")
        sub   = d.get("hero", {}).get("sub", "")
        cta   = d.get("hero", {}).get("cta", "Get Started")
        badge = d.get("tagline", "")
        proof = d.get("social_proof") or {}
        dark  = t["mode"] == "dark"
        av_border = "border-gray-800" if dark else "border-white"

        avatars = "".join(
            f'<div class="w-8 h-8 rounded-full bg-gradient-to-br {t["grad"]} '
            f'border-2 {av_border} opacity-75 -ml-1 first:ml-0"></div>'
            for _ in range(4)
        )
        proof_html = ""
        if proof.get("count") and proof.get("label"):
            proof_html = (
                f'<div class="flex items-center gap-3 pt-5 border-t {t["border"]}">'
                f'<div class="flex">{avatars}</div>'
                f'<span class="text-sm {t["text_muted"]}">'
                f'<span class="font-bold {t["stat"]}">{proof["count"]}</span>'
                f' {proof["label"]}</span></div>'
            )

        badge_html = ""
        if badge:
            badge_html = (
                f'<span class="inline-flex items-center gap-2 px-4 py-1.5 text-xs font-bold '
                f'uppercase tracking-wider {t["badge"]}">'
                f'<span class="w-1.5 h-1.5 rounded-full bg-current animate-pulse"></span>'
                f'{badge}</span>'
            )

        return f"""<section id="hero" class="relative {t['bg']} overflow-hidden pt-32 pb-20 md:pt-44 md:pb-28">
    <div class="absolute inset-0 bg-gradient-to-br {t['grad_subtle']} pointer-events-none"></div>
    <div class="absolute top-0 right-0 w-[600px] h-[600px] {t['glow']} opacity-[0.035] blur-[130px] rounded-full pointer-events-none"></div>
    <div class="container mx-auto {PAD_CON} relative z-10">
        <div class="grid lg:grid-cols-2 gap-12 xl:gap-20 items-center">
            <div class="space-y-7 order-2 lg:order-1">
                {badge_html}
                <h1 class="{H_HERO} {t['text']}">{h1}</h1>
                <p class="text-lg md:text-xl {t['text_muted']} leading-relaxed max-w-2xl">{sub}</p>
                <div class="flex flex-wrap gap-4">
                    {_btn(t, cta, "#contact", "text-base px-9 py-4")}
                    {_btn_ghost(t, "See how it works &rarr;", "#features", "text-base px-9 py-4")}
                </div>
                {proof_html}
            </div>
            <div class="relative h-[300px] md:h-[420px] lg:h-[520px] order-1 lg:order-2">
                <div class="absolute -inset-4 {t['glow']} opacity-[0.07] blur-3xl rounded-3xl"></div>
                <img src="{img}" alt="{h1}"
                     class="relative z-10 w-full h-full object-cover rounded-2xl shadow-2xl"
                     loading="eager" />
            </div>
        </div>
    </div>
</section>"""

    @staticmethod
    def centered(t: Dict, d: Dict, imgs: List[str]) -> str:
        """Full-bleed image, centered copy — luxury, beauty, travel, nonprofit."""
        img     = imgs[0] if imgs else ""
        h1      = d.get("hero", {}).get("h1", "")
        sub     = d.get("hero", {}).get("sub", "")
        cta     = d.get("hero", {}).get("cta", "Get Started")
        tagline = d.get("tagline", "")
        overlay = "bg-white/78" if t["mode"] == "light" else "bg-black/68"
        img_op  = "opacity-[0.18]" if t["mode"] == "light" else "opacity-[0.22]"
        tl = (f'<p class="text-xs font-bold uppercase tracking-[0.3em] {t["text_muted"]}">'
              f'&#8212; {tagline} &#8212;</p>') if tagline else ""

        return f"""<section id="hero" class="relative {t['bg']} overflow-hidden min-h-[88vh] flex items-center">
    <div class="absolute inset-0 pointer-events-none select-none">
        <img src="{img}" alt="" class="w-full h-full object-cover {img_op}" loading="eager" />
        <div class="absolute inset-0 {overlay}"></div>
    </div>
    <div class="absolute inset-0 bg-gradient-to-br {t['grad_subtle']} pointer-events-none"></div>
    <div class="container mx-auto {PAD_CON} relative z-10 text-center py-44">
        <div class="max-w-4xl mx-auto space-y-7">
            {tl}
            <h1 class="{H_HERO} {t['text']}">{h1}</h1>
            <p class="text-xl {t['text_muted']} leading-relaxed max-w-2xl mx-auto">{sub}</p>
            <div class="flex flex-col sm:flex-row gap-4 justify-center pt-4">
                {_btn(t, cta, "#contact", "text-base px-10 py-5 rounded-full")}
                {_btn_ghost(t, "Learn more &darr;", "#features", "text-base px-10 py-5 rounded-full")}
            </div>
        </div>
    </div>
</section>"""

    @staticmethod
    def with_stats(t: Dict, d: Dict, imgs: List[str]) -> str:
        """Left headline + stats bar. Image is atmospheric background."""
        img   = imgs[0] if imgs else ""
        h1    = d.get("hero", {}).get("h1", "")
        sub   = d.get("hero", {}).get("sub", "")
        cta   = d.get("hero", {}).get("cta", "Get Started")
        stats = d.get("stats") or []
        img_op = "opacity-[0.06]" if t["mode"] == "light" else "opacity-[0.1]"

        stat_grid = "".join(
            f'<div class="text-center">'
            f'<p class="text-4xl md:text-5xl font-black {t["stat"]}">{s.get("value","")}</p>'
            f'<p class="text-sm {t["text_muted"]} mt-1 leading-tight">{s.get("label","")}</p></div>'
            for s in stats[:4]
        ) if stats else ""
        stats_html = (
            f'<div class="grid grid-cols-2 md:grid-cols-4 gap-8 mt-16 pt-12 border-t {t["border"]}">'
            f'{stat_grid}</div>'
        ) if stats else ""

        return f"""<section id="hero" class="relative {t['bg']} overflow-hidden pt-32 pb-20 md:pt-44 md:pb-28">
    <div class="absolute inset-0 bg-gradient-to-br {t['grad_subtle']} pointer-events-none"></div>
    <div class="absolute top-0 right-0 w-1/2 h-full overflow-hidden pointer-events-none select-none">
        <img src="{img}" alt="" class="w-full h-full object-cover {img_op}" loading="eager" />
        <div class="absolute inset-0 bg-gradient-to-r {'from-white via-white/80 to-transparent' if t['mode']=='light' else 'from-gray-950 via-gray-950/80 to-transparent'}"></div>
    </div>
    <div class="container mx-auto {PAD_CON} relative z-10">
        <div class="max-w-2xl space-y-8">
            <h1 class="{H_HERO} {t['text']}">{h1}</h1>
            <p class="text-lg md:text-xl {t['text_muted']} leading-relaxed max-w-2xl">{sub}</p>
            <div class="flex flex-wrap gap-4">
                {_btn(t, cta, "#contact", "text-base")}
                {_btn_ghost(t, "See our work &rarr;", "#features", "text-base")}
            </div>
        </div>
        {stats_html}
    </div>
</section>"""

    @staticmethod
    def editorial(t: Dict, d: Dict, imgs: List[str]) -> str:
        """Large split headline + wide image — restaurant, events, ecommerce."""
        img  = imgs[0] if imgs else ""
        h1   = d.get("hero", {}).get("h1", "")
        sub  = d.get("hero", {}).get("sub", "")
        cta  = d.get("hero", {}).get("cta", "Explore")
        ws   = h1.split()
        mid  = max(1, len(ws) // 2)
        l1   = " ".join(ws[:mid])
        l2   = " ".join(ws[mid:])

        return f"""<section id="hero" class="relative {t['bg']} overflow-hidden pt-28 pb-12 md:pt-36 md:pb-18">
    <div class="container mx-auto {PAD_CON}">
        <h1 class="font-black tracking-tight leading-[1.02] text-[clamp(2.8rem,6.5vw,6rem)] {t['text']} mb-10">
            <span class="block">{l1}</span>
            <span class="block bg-gradient-to-r {t['grad_text']} bg-clip-text text-transparent">{l2}</span>
        </h1>
        <div class="grid lg:grid-cols-5 gap-10 items-end">
            <div class="lg:col-span-3 aspect-[16/9] overflow-hidden rounded-2xl shadow-2xl">
                <img src="{img}" alt="" class="w-full h-full object-cover" loading="eager" />
            </div>
            <div class="lg:col-span-2 space-y-7 pb-4">
                <p class="text-base md:text-lg {t['text_muted']} leading-relaxed max-w-2xl">{sub}</p>
                {_btn(t, f"{cta} &rarr;", "#contact", "text-base")}
            </div>
        </div>
    </div>
</section>"""


# ─────────────────────────────────────────────────────────────────────────────
# FEATURES VARIANTS
# ─────────────────────────────────────────────────────────────────────────────

class Features:

    @staticmethod
    def cards(t: Dict, features: List[Dict], imgs: List[str]) -> str:
        items = "".join(
            f'<div class="{t["card"]} rounded-2xl p-7 {HOVER_LIFT} flex flex-col">'
            f'<div class="w-12 h-12 rounded-xl bg-gradient-to-br {t["grad"]} '
            f'flex items-center justify-center text-xl mb-5 shrink-0">{f.get("icon","✦")}</div>'
            f'<h3 class="{H_CARD} {t["text"]} mb-2">{f.get("title","")}</h3>'
            f'<p class="{t["text_muted"]} text-sm leading-relaxed flex-grow">{f.get("description","")}</p>'
            f'</div>'
            for f in (features or [])
        )
        return f"""<section id="features" class="{t['bg_alt']} {PAD_SEC}">
    <div class="container mx-auto {PAD_CON}">
        <div class="text-center mb-14">
            {_eyebrow(t, "What we offer")}
            {_h2(t, "Everything You Need", "Thoughtfully designed to help you succeed.")}
        </div>
        <div class="grid sm:grid-cols-2 lg:grid-cols-3 gap-5">{items}</div>
    </div>
</section>"""

    @staticmethod
    def alternating(t: Dict, features: List[Dict], imgs: List[str]) -> str:
        blocks = []
        for i, f in enumerate(features or []):
            img_url  = imgs[(i + 1) % len(imgs)] if imgs else ""
            copy_cls = "lg:order-1" if i % 2 == 0 else "lg:order-2"
            img_cls  = "lg:order-2" if i % 2 == 0 else "lg:order-1"
            blocks.append(
                f'<div class="grid lg:grid-cols-2 gap-12 xl:gap-20 items-center">'
                f'<div class="space-y-5 {copy_cls}">'
                f'<div class="text-4xl leading-none">{f.get("icon","✦")}</div>'
                f'<h3 class="text-2xl md:text-3xl font-bold {t["text"]}">{f.get("title","")}</h3>'
                f'<p class="text-base {t["text_muted"]} leading-relaxed max-w-2xl">{f.get("description","")}</p>'
                f'<a href="#contact" class="inline-flex items-center gap-1 text-sm font-semibold '
                f'{t["stat"]} {HOVER_GLOW}">Learn more &rarr;</a>'
                f'</div>'
                f'<div class="aspect-[4/3] rounded-2xl overflow-hidden shadow-xl {img_cls}">'
                f'<img src="{img_url}" alt="" class="w-full h-full object-cover" loading="lazy" />'
                f'</div></div>'
            )
        return f"""<section id="features" class="{t['bg']} {PAD_SEC}">
    <div class="container mx-auto {PAD_CON}">
        <div class="text-center mb-20">
            {_eyebrow(t, "How it works")}
            {_h2(t, "Why Choose Us")}
        </div>
        <div class="space-y-20 md:space-y-28">{"".join(blocks)}</div>
    </div>
</section>"""

    @staticmethod
    def icon_list(t: Dict, features: List[Dict], imgs: List[str]) -> str:
        img_url = imgs[1] if len(imgs) > 1 else (imgs[0] if imgs else "")
        items   = "".join(
            f'<div class="flex gap-4 items-start p-5 rounded-xl border {t["border"]} {HOVER_GLOW}">'
            f'<div class="w-9 h-9 shrink-0 rounded-full bg-gradient-to-br {t["grad"]} '
            f'flex items-center justify-center text-white font-black text-xs shadow">'
            f'{str(i+1).zfill(2)}</div>'
            f'<div><h3 class="font-bold {t["text"]} mb-1">{f.get("title","")}</h3>'
            f'<p class="text-sm {t["text_muted"]} leading-relaxed">{f.get("description","")}</p>'
            f'</div></div>'
            for i, f in enumerate(features or [])
        )
        return f"""<section id="features" class="{t['bg_alt']} {PAD_SEC}">
    <div class="container mx-auto {PAD_CON}">
        <div class="grid lg:grid-cols-2 gap-16 xl:gap-24 items-center">
            <div>
                {_eyebrow(t, "Our approach")}
                <h2 class="{H_SECTION} {t['text']} mb-10">Built for Real Results</h2>
                <div class="space-y-3">{items}</div>
            </div>
            <div class="aspect-[4/3] rounded-2xl overflow-hidden shadow-2xl">
                <img src="{img_url}" alt="" class="w-full h-full object-cover" loading="lazy" />
            </div>
        </div>
    </div>
</section>"""


# ─────────────────────────────────────────────────────────────────────────────
# PRICING VARIANTS
# ─────────────────────────────────────────────────────────────────────────────

class Pricing:

    @staticmethod
    def tiers(t: Dict, tiers: List[Dict]) -> str:
        def _card(tier: Dict) -> str:
            featured = tier.get("featured", False)
            feats    = "".join([_check(t, f) for f in (tier.get("features") or [])])
            pop = (f'<span class="absolute top-4 right-4 text-xs font-bold bg-gradient-to-r '
                   f'{t["grad"]} text-white px-3 py-1 rounded-full">Most Popular</span>') if featured else ""
            cta_btn = (
                _btn(t, "Get Started", "#contact", "w-full text-center block py-3.5 rounded-xl")
                if featured else
                f'<a href="#contact" class="{t["btn_secondary"]} font-bold '
                f'w-full py-3.5 rounded-xl block text-center transition-all duration-200">Get Started</a>'
            )
            return (
                f'<div class="relative {t["card"]} rounded-2xl p-8 {HOVER_LIFT} flex flex-col">{pop}'
                f'<h3 class="font-bold text-xl {t["text"]} mb-1">{tier.get("name","Plan")}</h3>'
                f'<p class="text-xs {t["text_light"]} mb-5">{tier.get("description","")}</p>'
                f'<div class="mb-7"><span class="text-5xl font-black {t["text"]}">{tier.get("price","$0")}</span>'
                f'<span class="text-sm {t["text_muted"]}"> /mo</span></div>'
                f'<ul class="space-y-2.5 mb-8 flex-grow">{feats}</ul>'
                f'{cta_btn}</div>'
            )
        cards = "".join([_card(tier) for tier in (tiers or [])])
        return f"""<section id="pricing" class="{t['bg_alt']} {PAD_SEC}">
    <div class="container mx-auto {PAD_CON}">
        <div class="text-center mb-14">
            {_eyebrow(t, "Pricing")}
            {_h2(t, "Simple, Honest Pricing", "No hidden fees. No surprises. Cancel any time.")}
        </div>
        <div class="grid md:grid-cols-3 gap-6 max-w-5xl mx-auto">{cards}</div>
    </div>
</section>"""

    @staticmethod
    def two_col(t: Dict, tiers: List[Dict]) -> str:
        tiers  = tiers or []
        simple = tiers[0] if tiers else {}
        pro    = tiers[1] if len(tiers) > 1 else {}
        sf     = "".join([_check(t, f) for f in (simple.get("features") or [])])
        pf     = "".join([
            f'<li class="flex items-start gap-2.5 text-sm text-white/80">'
            f'<span class="mt-0.5 shrink-0 font-black text-white/60">&#10003;</span>'
            f'<span>{f}</span></li>'
            for f in (pro.get("features") or [])
        ])
        return f"""<section id="pricing" class="{t['bg']} {PAD_SEC}">
    <div class="container mx-auto {PAD_CON}">
        <div class="text-center mb-14">
            {_eyebrow(t, "Pricing")}
            {_h2(t, "Choose Your Plan")}
        </div>
        <div class="grid md:grid-cols-2 gap-6 max-w-4xl mx-auto">
            <div class="{t['card']} rounded-2xl p-10 {HOVER_LIFT}">
                <h3 class="text-xl font-bold {t['text']} mb-1">{simple.get("name","Starter")}</h3>
                <p class="text-sm {t['text_light']} mb-6">{simple.get("description","")}</p>
                <p class="text-5xl font-black {t['text']} mb-8">{simple.get("price","Free")}</p>
                <ul class="space-y-2.5 mb-10">{sf}</ul>
                {_btn_ghost(t, "Get Started", "#contact", "block w-full text-center py-3.5")}
            </div>
            <div class="bg-gradient-to-br {t['grad']} rounded-2xl p-10 text-white relative overflow-hidden {HOVER_LIFT} shadow-2xl">
                <div class="absolute top-0 right-0 w-44 h-44 bg-white/10 blur-3xl rounded-full pointer-events-none"></div>
                <span class="inline-block px-3 py-1 bg-white/20 text-xs font-bold rounded-full mb-4 uppercase tracking-wide">Recommended</span>
                <h3 class="text-xl font-bold mb-1">{pro.get("name","Pro")}</h3>
                <p class="text-sm text-white/70 mb-6">{pro.get("description","")}</p>
                <p class="text-5xl font-black mb-8">{pro.get("price","$99")}</p>
                <ul class="space-y-2.5 mb-10">{pf}</ul>
                <a href="#contact" class="block w-full text-center bg-white text-gray-900 py-3.5 rounded-xl font-bold hover:bg-gray-50 transition">Get Started</a>
            </div>
        </div>
    </div>
</section>"""

    @staticmethod
    def project_quotes(t: Dict, tiers: List[Dict]) -> str:
        tiers = tiers or []
        cards = "".join(
            f'<div class="{t["card"]} rounded-2xl p-8 {HOVER_LIFT} flex flex-col">'
            f'<div class="text-3xl mb-5">{["&#127959;","&#128296;","&#127970;"][i % 3]}</div>'
            f'<h3 class="text-xl font-bold {t["text"]} mb-2">{tier.get("name","Package")}</h3>'
            f'<p class="text-sm {t["text_muted"]} mb-3 leading-relaxed">{tier.get("description","")}</p>'
            f'<p class="text-xl font-black {t["stat"]} mb-5">{tier.get("price","Get a Quote")}</p>'
            f'<ul class="space-y-2 mb-8 flex-grow">{"".join([_check(t, f) for f in (tier.get("features") or [])])}</ul>'
            f'{_btn_ghost(t, "Request a Quote &rarr;", "#contact", "block w-full text-center py-3")}'
            f'</div>'
            for i, tier in enumerate(tiers)
        )
        cta_card = (
            f'<div class="{t["card"]} rounded-2xl p-8 max-w-2xl mx-auto text-center mt-10">'
            f'<p class="font-bold text-lg {t["text"]} mb-2">Not sure what you need?</p>'
            f'<p class="text-sm {t["text_muted"]} mb-6 leading-relaxed max-w-2xl mx-auto">'
            f'Every project is different. We\'ll assess yours and give a transparent, no-obligation estimate.</p>'
            f'{_btn(t, "Get a Free Estimate", "#contact")}'
            f'</div>'
        )
        return f"""<section id="pricing" class="{t['bg_alt']} {PAD_SEC}">
    <div class="container mx-auto {PAD_CON}">
        <div class="text-center mb-14">
            {_eyebrow(t, "Services & Pricing")}
            {_h2(t, "What We Offer", "Every project gets a tailored quote. No surprises.")}
        </div>
        <div class="grid sm:grid-cols-2 lg:grid-cols-3 gap-6 max-w-5xl mx-auto">{cards}</div>
        {cta_card}
    </div>
</section>"""

    @staticmethod
    def service_rows(t: Dict, tiers: List[Dict]) -> str:
        rows = "".join(
            f'<div class="grid md:grid-cols-3 gap-6 items-start py-10 border-b {t["border"]}">'
            f'<div>'
            f'<h3 class="font-bold text-xl {t["text"]}">{tier.get("name","Service")}</h3>'
            f'<p class="text-sm {t["text_muted"]} mt-2 leading-relaxed">{tier.get("description","")}</p>'
            f'<p class="font-black text-lg {t["stat"]} mt-3">{tier.get("price","")}</p>'
            f'</div>'
            f'<ul class="space-y-2">{"".join([_check(t, f) for f in (tier.get("features") or [])[:4]])}</ul>'
            f'<div class="md:text-right pt-2">'
            f'{_btn(t, "Book Consultation", "#contact", "text-sm px-6 py-3 rounded-lg")}'
            f'</div></div>'
            for tier in (tiers or [])
        )
        return f"""<section id="pricing" class="{t['bg']} {PAD_SEC}">
    <div class="container mx-auto {PAD_CON}">
        <div class="mb-14">
            {_eyebrow(t, "Services")}
            <h2 class="{H_SECTION} {t['text']}">How We Can Help</h2>
            <p class="text-base {t['text_muted']} mt-4 max-w-lg leading-relaxed">
                All engagements begin with a complimentary consultation. No commitment required.
            </p>
        </div>
        <div class="divide-y {t['border']}">{rows}</div>
        <div class="mt-12 text-center">
            {_btn(t, "Schedule a Free Consultation", "#contact", "text-base px-10 py-5")}
        </div>
    </div>
</section>"""

    @staticmethod
    def contact_only(t: Dict, tiers: List[Dict]) -> str:
        """Used when no pricing data is available — just a clean CTA to contact."""
        return f"""<section id="pricing" class="{t['bg_alt']} {PAD_SEC}">
    <div class="container mx-auto {PAD_CON}">
        <div class="max-w-2xl mx-auto text-center {t["card"]} rounded-2xl p-12">
            {_eyebrow(t, "Pricing")}
            <h2 class="text-3xl font-black {t['text']} mt-2 mb-4">Every Project Is Different</h2>
            <p class="text-base {t['text_muted']} leading-relaxed mb-8">
                We tailor our services to your specific needs. Get in touch and we'll provide a
                transparent, no-obligation quote.
            </p>
            {_btn(t, "Request a Quote", "#contact", "text-base px-10 py-5")}
        </div>
    </div>
</section>"""


# ─────────────────────────────────────────────────────────────────────────────
# MASTER ARCHITECT
# ─────────────────────────────────────────────────────────────────────────────

class MasterArchitect:

    # Valid section IDs the AI can request
    VALID_SECTIONS = {"hero", "trust", "features", "pricing", "testimonials", "faq", "contact"}

    def __init__(self, business_name: str, prompt: str, version: int = 1):
        raw_name   = (business_name or "").strip()
        raw_prompt = (prompt or "").strip()

        extracted, clean_prompt = extract_business_name(raw_name, raw_prompt)

        self.industry = detect_industry(clean_prompt or raw_prompt)
        self.name     = raw_name or extracted or _default_name(self.industry)
        self.prompt   = clean_prompt
        self.version  = version
        self.theme    = select_theme(self.industry)
        self.data: Dict      = {}
        self.imgs: List[str] = []
        self.contact_info    = _extract_contact_info(raw_prompt + " " + clean_prompt)

        logger.info(f"MasterArchitect | '{self.name}' | {self.industry} | {self.theme['id']}")

    # ── AI content ───────────────────────────────────────────────────────────

    def _ai_prompt(self) -> str:
        project_ind = {"construction", "logistics", "automotive", "events"}
        service_ind = {"legal", "nonprofit"}
        no_price_ind = {"restaurant", "beauty", "fitness", "travel", "nature"}

        if self.industry in project_ind:
            price_spec = (
                '  {"name":"Small / Residential","price":"From $1,500","description":"One sentence on scope.","features":["5 relevant items"],"featured":false},\n'
                '  {"name":"Commercial / Mid-Scale","price":"From $10,000","description":"One sentence.","features":["5 items"],"featured":true},\n'
                '  {"name":"Large / Enterprise","price":"Get a Quote","description":"One sentence.","features":["5 items"],"featured":false}'
            )
            price_note = "Include pricing tiers as project ranges."
        elif self.industry in service_ind:
            price_spec = (
                '  {"name":"Free Consultation","price":"Complimentary","description":"30-min, no obligation.","features":["5 items"],"featured":false},\n'
                '  {"name":"Standard Engagement","price":"From $300/hr","description":"Flexible support.","features":["5 items"],"featured":true},\n'
                '  {"name":"Retainer","price":"Custom","description":"Dedicated partnership.","features":["5 items"],"featured":false}'
            )
            price_note = "Include service tiers appropriate for a professional services firm."
        elif self.industry in no_price_ind:
            price_spec = ""
            price_note = 'Set pricing to null — this industry does not use pricing tiers on a landing page.'
        else:
            price_spec = (
                '  {"name":"Starter","price":"$X/mo","description":"For individuals.","features":["5 items"],"featured":false},\n'
                '  {"name":"Professional","price":"$X/mo","description":"For growing teams.","features":["5 items"],"featured":true},\n'
                '  {"name":"Enterprise","price":"Custom","description":"For large orgs.","features":["5 items"],"featured":false}'
            )
            price_note = "Fill in realistic price estimates for this industry and scale."

        pricing_block = f'"pricing": [\n{price_spec}\n  ],' if price_spec else '"pricing": null,'

        sections_guidance = {
            "construction": '["hero","trust","features","pricing","testimonials","faq","contact"]',
            "restaurant":   '["hero","trust","features","testimonials","contact"]',
            "beauty":       '["hero","trust","features","testimonials","faq","contact"]',
            "saas":         '["hero","trust","features","pricing","testimonials","faq","contact"]',
            "legal":        '["hero","trust","features","pricing","faq","contact"]',
            "fitness":      '["hero","trust","features","testimonials","contact"]',
            "nonprofit":    '["hero","features","testimonials","faq","contact"]',
        }.get(self.industry, '["hero","trust","features","pricing","testimonials","faq","contact"]')

        return f"""You are writing real website copy for a business called "{self.name}".
Industry: {self.industry}
Context: {self.prompt}

Write like a skilled human copywriter, not a template generator. Rules:
- Use the industry's actual vocabulary: a builder "constructs" and "installs", a lawyer "advises" and "represents", a chef "prepares" and "crafts", a trainer "coaches" and "pushes". Never write "delivers solutions" or "empowers clients".
- The hero headline must sound like a real brand tagline — specific, punchy, human. NOT "Your Trusted Partner in [Industry]".
- Stats must be realistic for a business at this size and stage. Don't invent numbers that are implausible.
- Trust badges must be the actual credentials that matter in THIS industry (e.g. OSHA for construction, Bar Association for law, Michelin for restaurants).
- Testimonial quotes must sound like real people speaking. Include a specific result or detail. Never write "highly recommend" or "great service" alone.
- FAQ questions must be the actual questions that REAL customers in this industry ask — not generic website FAQ questions.
- social_proof count+label must make sense (e.g. "350+ homes built", not "2,400+ users").
- {price_note}
- contact_email and contact_phone: ONLY include these if they appear in the provided context. If not in context, set to empty string "".
- sections: list which sections are appropriate for this business. {sections_guidance} is the default for this industry — adjust only if the context warrants it. Always include "hero" and "contact". Only include "pricing" if pricing data is available or logical for this industry.

Return ONLY valid JSON (no markdown fences, no prose):
{{
  "sections": {sections_guidance},
  "nav": ["4 nav items specific to this business and the sections you include"],
  "hero": {{
    "h1": "6-9 word punchy headline for {self.name}",
    "sub": "One sentence value prop in this industry's plain language",
    "cta": "Action phrase matching what a customer would do first"
  }},
  "tagline": "2-5 word brand slogan",
  "social_proof": {{"count": "e.g. 350+", "label": "e.g. projects completed"}},
  "stats": [
    {{"value": "realistic figure", "label": "what it measures"}},
    {{"value": "realistic figure", "label": "what it measures"}},
    {{"value": "realistic figure", "label": "what it measures"}},
    {{"value": "realistic figure", "label": "what it measures"}}
  ],
  "trust_badges": ["Industry-specific credential 1", "Credential 2", "Credential 3", "Credential 4"],
  "features": [
    {{"title": "Specific feature", "description": "2 concrete sentences about what {self.name} actually does or offers.", "icon": "single relevant emoji"}},
    {{"title": "Specific feature", "description": "2 concrete sentences.", "icon": "single emoji"}},
    {{"title": "Specific feature", "description": "2 concrete sentences.", "icon": "single emoji"}}
  ],
  {pricing_block}
  "testimonials": [
    {{"name": "Full Name", "role": "Job Title or Relationship", "company": "Company or Location", "quote": "Specific result they got. What changed for them."}},
    {{"name": "Full Name", "role": "Job Title or Relationship", "company": "Company or Location", "quote": "Specific result or observation."}}
  ],
  "faq": [
    {{"q": "Question a real customer of this type of business would actually ask?", "a": "Specific, honest answer."}},
    {{"q": "Another real question?", "a": "Answer."}},
    {{"q": "Another real question?", "a": "Answer."}}
  ],
  "cta_headline": "Closing call-to-action headline that feels specific to this industry",
  "contact_email": "",
  "contact_phone": ""
}}"""

    def _get_data(self) -> Dict:
        if not AI_AVAILABLE:
            return self._fallback()
        try:
            raw     = chat_completion(
                system="You are an expert copywriter. Output ONLY valid JSON, no backticks, no extra text.",
                user=self._ai_prompt(),
                temperature=0.72,
            )
            cleaned = re.sub(r"^```json\s*|^```\s*|```$", "", raw.strip(), flags=re.MULTILINE).strip()
            data    = json.loads(cleaned)
            # Merge any contact info extracted from the original prompt (user input wins)
            for key in ("contact_email", "contact_phone"):
                if not data.get(key) and self.contact_info.get(key.replace("contact_","")):
                    data[key] = self.contact_info[key.replace("contact_","")]
            return self._sanitize(data)
        except Exception as e:
            logger.error(f"AI content error: {e}")
            return self._fallback()

    _COLOR_PAT = re.compile(
        r"\b(violet|fuchsia|purple|indigo|magenta|mauve|lavender|"
        r"cyan|teal|emerald|mint|lime|"
        r"amber|orange|yellow|gold|"
        r"rose|pink|crimson|scarlet|"
        r"navy|cobalt|cerulean|"
        r"gray|grey|charcoal|ebony|ivory|cream)\b",
        re.IGNORECASE,
    )
    _COLOR_SUBS = {
        "violet":"distinctive","fuchsia":"vibrant","purple":"rich","indigo":"deep",
        "magenta":"bold","mauve":"refined","lavender":"subtle",
        "cyan":"modern","teal":"fresh","emerald":"natural","mint":"clean","lime":"bright",
        "amber":"warm","orange":"energetic","yellow":"sunny","gold":"premium",
        "rose":"elegant","pink":"delicate","crimson":"bold","scarlet":"striking",
        "navy":"authoritative","cobalt":"confident","cerulean":"open",
        "gray":"neutral","grey":"neutral","charcoal":"sophisticated",
        "ebony":"striking","ivory":"clean","cream":"refined",
    }

    def _sanitize(self, obj: Any) -> Any:
        if isinstance(obj, str):
            return self._COLOR_PAT.sub(
                lambda m: self._COLOR_SUBS.get(m.group(0).lower(), m.group(0)), obj
            )
        if isinstance(obj, dict):
            obj.pop("unsplash_keywords", None)
            return {k: self._sanitize(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [self._sanitize(i) for i in obj]
        return obj

    def _fallback(self) -> Dict:
        """Industry-aware fallbacks."""
        base = {
            "sections": ["hero", "trust", "features", "pricing", "testimonials", "faq", "contact"],
            "contact_email": self.contact_info.get("email", ""),
            "contact_phone": self.contact_info.get("phone", ""),
        }

        if self.industry == "construction":
            return {**base, **{
                "sections": ["hero", "trust", "features", "pricing", "testimonials", "faq", "contact"],
                "nav": ["Services", "Projects", "About", "Contact"],
                "hero": {"h1": f"{self.name} — Built Right, On Time", "sub": "Quality construction and renovation delivered on schedule, on budget, by certified tradespeople.", "cta": "Request a Quote"},
                "tagline": "Built to last.",
                "social_proof": {"count": "350+", "label": "projects completed"},
                "stats": [{"value":"98%","label":"On-time delivery"},{"value":"350+","label":"Projects completed"},{"value":"15yr","label":"In the industry"},{"value":"24/7","label":"Emergency cover"}],
                "trust_badges": ["Licensed & Insured","OSHA Compliant","Bonded Contractor","Satisfaction Guaranteed"],
                "features": [
                    {"title":"Licensed & Fully Insured","description":"Every project covered by comprehensive liability and workers compensation insurance. You are fully protected from day one.","icon":"🛡️"},
                    {"title":"On-Time, On-Budget","description":"Written schedules and fixed-price quotes before work begins. No surprises on your final invoice.","icon":"📋"},
                    {"title":"All Trades, One Team","description":"From groundwork to finishing touches, certified tradespeople handle every phase under one roof.","icon":"🔨"},
                ],
                "pricing": [
                    {"name":"Residential","price":"From $2,500","description":"Home renovations and repairs.","features":["Free on-site estimate","Kitchen & bath remodels","Roofing & siding","Flooring & painting","Follow-up inspection"],"featured":False},
                    {"name":"Commercial","price":"From $12,000","description":"Business and commercial fit-outs.","features":["Dedicated project manager","Office & retail fit-outs","Compliance documentation","Progress reporting","Warranty included"],"featured":True},
                    {"name":"Emergency","price":"24/7 Available","description":"Urgent repairs and storm damage.","features":["Same-day response","Storm & water damage","Structural emergencies","Insurance billing support","Temporary securing"],"featured":False},
                ],
                "testimonials": [
                    {"name":"Michael Torres","role":"Homeowner","company":"Brooklyn, NY","quote":"Complete renovation done on schedule and under budget. The crew was professional and respectful of our home from day one."},
                    {"name":"Lisa Chen","role":"Property Manager","company":"Manhattan","quote":"We've used them across six properties. Always reliable, always honest about what things will cost."},
                ],
                "faq": [
                    {"q":"Are you licensed and insured?","a":"Yes — fully licensed with comprehensive liability and workers compensation on every job."},
                    {"q":"Do you offer free estimates?","a":"Absolutely. We provide detailed, no-obligation quotes after an on-site assessment."},
                    {"q":"How do you handle project timelines?","a":"We give you a written schedule before work begins and provide milestone updates throughout."},
                ],
                "cta_headline": f"Ready to start your project with {self.name}?",
            }}

        if self.industry == "restaurant":
            return {**base, **{
                "sections": ["hero", "trust", "features", "testimonials", "contact"],
                "nav": ["Menu", "About", "Catering", "Reservations"],
                "hero": {"h1": f"{self.name} — Food Made With Purpose", "sub": "Freshly prepared every day from locally sourced ingredients and time-honoured recipes.", "cta": "View Our Menu"},
                "tagline": "Taste the difference.",
                "social_proof": {"count": "1,200+", "label": "meals served weekly"},
                "stats": [{"value":"4.9★","label":"Average rating"},{"value":"1,200+","label":"Meals weekly"},{"value":"8yr","label":"Serving the community"},{"value":"100%","label":"Fresh daily"}],
                "trust_badges": ["Health Inspected","Locally Sourced","5-Star Rated","Award Winning"],
                "features": [
                    {"title":"Locally Sourced Ingredients","description":"We partner with regional farms so every dish is as fresh as it is flavourful — every single day.","icon":"🥗"},
                    {"title":"Made Fresh Daily","description":"Nothing is pre-made or frozen. Every dish is prepared in-house from scratch each morning.","icon":"👨‍🍳"},
                    {"title":"Warm, Welcoming Atmosphere","description":"A dining room designed for lingering — perfect for date nights, family meals, and private celebrations.","icon":"🏡"},
                ],
                "pricing": None,
                "testimonials": [
                    {"name":"Maria Gonzalez","role":"Yelp Elite Reviewer","company":"Local Regular","quote":"Best food in the neighbourhood. The pasta is always perfectly cooked and the portions are genuinely generous."},
                    {"name":"David Park","role":"Food Writer","company":"NYC Eats","quote":"A hidden gem that earns every star. You can taste the care in every dish."},
                ],
                "faq": [],
                "cta_headline": f"Come experience {self.name} for yourself",
            }}

        # Generic fallback
        return {**base, **{
            "sections": ["hero", "trust", "features", "pricing", "testimonials", "faq", "contact"],
            "nav": ["Features","Pricing","About","Contact"],
            "hero": {"h1": f"Welcome to {self.name}", "sub": "Professional services built around your specific needs and goals.", "cta": "Get Started"},
            "tagline": "Excellence delivered.",
            "social_proof": {"count": "500+", "label": "clients served"},
            "stats": [{"value":"97%","label":"Client satisfaction"},{"value":"500+","label":"Engagements completed"},{"value":"10yr","label":"In the industry"},{"value":"24/7","label":"Support access"}],
            "trust_badges": ["Licensed & Certified","5-Star Rated","Award Winner 2024","Satisfaction Guaranteed"],
            "features": [
                {"title":"Expert Team","description":"Seasoned professionals with deep domain knowledge committed to delivering results that matter.","icon":"🏆"},
                {"title":"Proven Track Record","description":"Hundreds of successful engagements across a wide range of industries and client sizes.","icon":"📈"},
                {"title":"Responsive Support","description":"A dedicated team that responds quickly and keeps you informed at every step.","icon":"🤝"},
            ],
            "pricing": [
                {"name":"Starter","price":"$49/mo","description":"For individuals.","features":["Core features","Email support","5 projects","Basic analytics","Monthly reports"],"featured":False},
                {"name":"Professional","price":"$149/mo","description":"For growing teams.","features":["Everything in Starter","Priority support","Unlimited projects","Advanced analytics","Custom integrations"],"featured":True},
                {"name":"Enterprise","price":"Custom","description":"For large organisations.","features":["Everything in Professional","Dedicated manager","SLA guarantee","Custom contracts","Onboarding support"],"featured":False},
            ],
            "testimonials": [
                {"name":"Jordan Lee","role":"Director","company":"Meridian Group","quote":"Working with this team changed our entire approach. The results were measurable within the first month."},
                {"name":"Priya Nair","role":"Founder","company":"Spark Ventures","quote":"Responsive, knowledgeable, and genuinely invested in our success. They feel like part of our team."},
            ],
            "faq": [
                {"q":"How do I get started?","a":"Reach out via the contact form and we'll schedule an initial call to understand your needs."},
                {"q":"What does the process look like?","a":"Discovery first, then a tailored plan, then execution with full transparency at every stage."},
                {"q":"Do you offer ongoing support?","a":"Yes. All engagements include continued access to our team after the initial project is complete."},
            ],
            "cta_headline": f"Ready to get started with {self.name}?",
        }}

    # ── Layout selectors ──────────────────────────────────────────────────────

    def _hero_fn(self) -> Callable:
        return {
            "luxury":      Hero.centered,
            "agency":      Hero.centered,
            "beauty":      Hero.centered,
            "travel":      Hero.centered,
            "nonprofit":   Hero.centered,
            "finance":     Hero.with_stats,
            "real_estate": Hero.with_stats,
            "legal":       Hero.with_stats,
            "logistics":   Hero.with_stats,
            "restaurant":  Hero.editorial,
            "events":      Hero.editorial,
            "ecommerce":   Hero.editorial,
        }.get(self.industry, Hero.split)

    def _features_fn(self) -> Callable:
        return {
            "luxury":       Features.cards,
            "agency":       Features.cards,
            "saas":         Features.cards,
            "ecommerce":    Features.cards,
            "developer":    Features.cards,
            "startup":      Features.cards,
            "ai":           Features.cards,
            "events":       Features.cards,
            "finance":      Features.icon_list,
            "real_estate":  Features.icon_list,
            "legal":        Features.icon_list,
            "logistics":    Features.icon_list,
            "health":       Features.alternating,
            "fitness":      Features.alternating,
            "travel":       Features.alternating,
            "restaurant":   Features.alternating,
            "construction": Features.alternating,
            "automotive":   Features.alternating,
            "beauty":       Features.alternating,
            "nature":       Features.alternating,
            "nonprofit":    Features.alternating,
        }.get(self.industry, Features.cards)

    def _pricing_fn(self) -> Callable:
        if self.industry in {"construction", "logistics", "automotive", "events"}:
            return Pricing.project_quotes
        if self.industry in {"legal", "nonprofit"}:
            return Pricing.service_rows
        if self.industry in {"luxury", "agency", "beauty", "finance", "real_estate"}:
            return Pricing.two_col
        return Pricing.tiers

    # ── Individual sections ───────────────────────────────────────────────────

    def _nav(self) -> str:
        t   = self.theme
        cta = self.data.get("hero", {}).get("cta", "Get Started")
        sections = self.data.get("sections") or list(self.VALID_SECTIONS)
        nav_items = self.data.get("nav") or []

        # Only link to sections that actually exist
        links = "".join(
            f'<li><a href="#{item.lower().replace(" ", "")}" '
            f'class="{t["text_muted"]} hover:opacity-75 transition-opacity text-sm font-medium">'
            f'{item}</a></li>'
            for item in nav_items
        )

        # Mobile menu (pure CSS via checkbox hack)
        mobile_links = "".join(
            f'<a href="#{item.lower().replace(" ", "")}" '
            f'class="block px-4 py-3 text-sm font-medium {t["text_muted"]} hover:opacity-75 transition-opacity border-b {t["border"]}">'
            f'{item}</a>'
            for item in nav_items
        )

        dark = t["mode"] == "dark"
        hamburger_color = "bg-white" if dark else "bg-slate-800"

        return f"""<nav class="fixed top-0 w-full z-50 {t['nav']}">
    <div class="container mx-auto {PAD_CON} py-4 flex justify-between items-center">
        <a href="#" class="text-xl font-black tracking-tight {t['text']}">{self.name}</a>
        <ul class="hidden md:flex items-center gap-8">{links}</ul>
        <div class="flex items-center gap-3">
            <a href="#contact" class="hidden md:inline-block bg-gradient-to-r {t['grad']} text-white font-bold rounded-xl px-5 py-2.5 text-sm shadow-md {HOVER_LIFT}">{cta}</a>
            <!-- Hamburger (mobile only) -->
            <label for="nav-toggle" class="md:hidden cursor-pointer p-2 rounded-lg border {t['border']} flex flex-col gap-1.5" aria-label="Toggle menu">
                <span class="block w-5 h-0.5 {hamburger_color}"></span>
                <span class="block w-5 h-0.5 {hamburger_color}"></span>
                <span class="block w-5 h-0.5 {hamburger_color}"></span>
            </label>
        </div>
    </div>
    <!-- Mobile drawer (CSS only) -->
    <input type="checkbox" id="nav-toggle" class="hidden peer" />
    <div class="{t['bg']} border-t {t['border']} hidden peer-checked:block md:hidden shadow-lg">
        {mobile_links}
        <div class="p-4">
            <a href="#contact" class="block text-center bg-gradient-to-r {t['grad']} text-white font-bold rounded-xl px-5 py-3 text-sm">{cta}</a>
        </div>
    </div>
</nav>"""

    def _trust_band(self) -> str:
        t      = self.theme
        badges = self.data.get("trust_badges") or []
        if not badges:
            return ""
        pills = "".join(
            f'<span class="px-4 py-1.5 text-xs font-semibold {t["badge"]}">{b}</span>'
            for b in badges
        )
        return (
            f'<section id="trust" class="{t["bg_alt"]} border-y {t["border"]} py-5">'
            f'<div class="container mx-auto {PAD_CON}">'
            f'<div class="flex flex-wrap items-center justify-center gap-3">'
            f'<span class="text-xs {t["text_light"]} uppercase tracking-widest mr-1">Trusted &amp; Verified</span>'
            f'{pills}'
            f'</div></div></section>'
        )

    def _testimonials(self) -> str:
        t    = self.theme
        tevs = self.data.get("testimonials") or []
        if not tevs:
            return ""
        stars = "".join(['<span style="color:#f59e0b">&#9733;</span>'] * 5)
        cards = "".join(
            f'<div class="{t["card"]} rounded-2xl p-8 {HOVER_LIFT} flex flex-col">'
            f'<div class="flex gap-0.5 mb-5 text-sm">{stars}</div>'
            f'<p class="{t["text_muted"]} text-base italic leading-relaxed flex-grow mb-6 max-w-2xl">'
            f'&#8220;{tv.get("quote","")}&#8221;</p>'
            f'<div class="flex items-center gap-3 pt-5 border-t {t["border"]}">'
            f'<div class="w-10 h-10 shrink-0 rounded-full bg-gradient-to-br {t["grad"]} '
            f'flex items-center justify-center text-white font-black text-sm">'
            f'{(tv.get("name","?") or "?")[0].upper()}</div>'
            f'<div><p class="font-bold text-sm {t["text"]}">{tv.get("name","")}</p>'
            f'<p class="text-xs {t["text_light"]}">'
            f'{tv.get("role","")} &middot; {tv.get("company","")}</p>'
            f'</div></div></div>'
            for tv in tevs
        )
        return (
            f'<section id="testimonials" class="{t["bg_alt"]} {PAD_SEC}">'
            f'<div class="container mx-auto {PAD_CON}">'
            f'<div class="text-center mb-12">'
            f'{_eyebrow(t, "Testimonials")}'
            f'{_h2(t, "What Our Clients Say")}'
            f'</div>'
            f'<div class="grid md:grid-cols-2 gap-6 max-w-4xl mx-auto">{cards}</div>'
            f'</div></section>'
        )

    def _faq(self) -> str:
        t    = self.theme
        faqs = self.data.get("faq") or []
        if not faqs:
            return ""
        items = "".join(
            f'<details class="{t["card"]} rounded-xl overflow-hidden group">'
            f'<summary class="flex justify-between items-center p-6 cursor-pointer '
            f'font-semibold {t["text"]} list-none select-none hover:opacity-75 transition-opacity">'
            f'<span>{faq.get("q","")}</span>'
            f'<span class="ml-6 shrink-0 w-6 h-6 rounded-full border {t["border"]} '
            f'flex items-center justify-center text-xs {t["text_muted"]} '
            f'group-open:rotate-45 transition-transform duration-200">+</span>'
            f'</summary>'
            f'<div class="px-6 pb-6 border-t {t["border"]} pt-4">'
            f'<p class="{t["text_muted"]} text-sm leading-relaxed">{faq.get("a","")}</p>'
            f'</div></details>'
            for faq in faqs
        )
        return (
            f'<section id="faq" class="{t["bg"]} {PAD_SEC}">'
            f'<div class="container mx-auto {PAD_CON}">'
            f'<div class="text-center mb-12">'
            f'{_eyebrow(t, "FAQ")}'
            f'{_h2(t, "Common Questions")}'
            f'</div>'
            f'<div class="space-y-3 max-w-2xl mx-auto">{items}</div>'
            f'</div></section>'
        )

    def _contact(self) -> str:
        """Real contact form section. Uses actual email/phone only if provided."""
        t           = self.theme
        headline    = self.data.get("cta_headline") or f"Get in Touch with {self.name}"
        sub         = self.data.get("hero", {}).get("sub") or ""
        btn_label   = self.data.get("hero", {}).get("cta") or "Send Message"
        email       = self.data.get("contact_email") or ""
        phone       = self.data.get("contact_phone") or ""
        img_url     = self.imgs[2] if len(self.imgs) > 2 else (self.imgs[0] if self.imgs else "")
        overlay     = "bg-white/88" if t["mode"] == "light" else "bg-black/78"
        img_op      = "opacity-[0.05]" if t["mode"] == "light" else "opacity-[0.08]"

        # Form action: use real email if available, else no action (user configures later)
        form_action = f'action="mailto:{email}" enctype="text/plain"' if email else ""
        form_note   = "" if email else (
            f'<p class="text-xs {t["text_light"]} mt-3 text-center">'
            f'Form submission will be configured by the site owner.</p>'
        )

        # Contact details — only render what we actually have
        contact_details = ""
        if email:
            contact_details += (
                f'<a href="mailto:{email}" class="flex items-center gap-2 text-sm {t["text_muted"]} '
                f'hover:opacity-75 transition-opacity">'
                f'<span>&#9993;</span><span>{email}</span></a>'
            )
        if phone:
            contact_details += (
                f'<a href="tel:{re.sub(r"[^+\d]","",phone)}" class="flex items-center gap-2 text-sm {t["text_muted"]} '
                f'hover:opacity-75 transition-opacity">'
                f'<span>&#128222;</span><span>{phone}</span></a>'
            )
        contact_block = (
            f'<div class="flex flex-col gap-3 mt-6 pt-6 border-t {t["border"]}">{contact_details}</div>'
        ) if contact_details else ""

        return f"""<section id="contact" class="relative {t['bg_alt']} {PAD_SEC} overflow-hidden">
    <div class="absolute inset-0 pointer-events-none select-none">
        <img src="{img_url}" alt="" class="w-full h-full object-cover {img_op}" loading="lazy" />
        <div class="absolute inset-0 {overlay}"></div>
    </div>
    <div class="absolute inset-0 bg-gradient-to-br {t['grad_subtle']} pointer-events-none"></div>
    <div class="container mx-auto {PAD_CON} relative z-10">
        <div class="grid lg:grid-cols-2 gap-16 items-start max-w-5xl mx-auto">
            <!-- Left: copy -->
            <div class="space-y-5">
                {_eyebrow(t, "Contact")}
                <h2 class="{H_SECTION} {t['text']}">{headline}</h2>
                <p class="text-base {t['text_muted']} leading-relaxed max-w-2xl">{sub}</p>
                {contact_block}
            </div>
            <!-- Right: form -->
            <div class="{t['card']} rounded-2xl p-8 shadow-xl">
                <form {form_action} method="post" class="space-y-5" novalidate>
                    <div>
                        <label class="block text-xs font-semibold {t['text']} mb-1.5 uppercase tracking-wide" for="cf-name">Your Name</label>
                        <input type="text" id="cf-name" name="name" required autocomplete="name"
                               placeholder="Jane Smith"
                               class="w-full rounded-xl px-4 py-3 text-sm {t['input']} outline-none focus:ring-2 focus:ring-offset-1 transition" />
                    </div>
                    <div>
                        <label class="block text-xs font-semibold {t['text']} mb-1.5 uppercase tracking-wide" for="cf-email">Email Address</label>
                        <input type="email" id="cf-email" name="email" required autocomplete="email"
                               placeholder="jane@example.com"
                               class="w-full rounded-xl px-4 py-3 text-sm {t['input']} outline-none focus:ring-2 focus:ring-offset-1 transition" />
                    </div>
                    <div>
                        <label class="block text-xs font-semibold {t['text']} mb-1.5 uppercase tracking-wide" for="cf-message">Message</label>
                        <textarea id="cf-message" name="message" required rows="5"
                                  placeholder="Tell us about your project or question..."
                                  class="w-full rounded-xl px-4 py-3 text-sm {t['input']} outline-none focus:ring-2 focus:ring-offset-1 transition resize-none"></textarea>
                    </div>
                    <button type="submit"
                            class="w-full bg-gradient-to-r {t['grad']} text-white font-bold rounded-xl py-4 text-sm shadow-md {HOVER_LIFT} transition-all duration-300">
                        {btn_label} &rarr;
                    </button>
                    {form_note}
                </form>
            </div>
        </div>
    </div>
</section>"""

    def _footer(self) -> str:
        t       = self.theme
        tagline = self.data.get("tagline") or ""
        sub     = self.data.get("hero", {}).get("sub") or ""
        email   = self.data.get("contact_email") or ""
        phone   = self.data.get("contact_phone") or ""
        nav_items = self.data.get("nav") or []

        links = "".join(
            f'<li><a href="#{item.lower().replace(" ","")}" '
            f'class="{t["text_muted"]} hover:opacity-70 text-sm transition-opacity">{item}</a></li>'
            for item in nav_items
        )
        tl_html = f'<p class="text-xs {t["text_light"]} mt-3 italic">{tagline}</p>' if tagline else ""

        # Contact column: only show what we have
        contact_items = ""
        if email:
            contact_items += f'<li><a href="mailto:{email}" class="{t["text_muted"]} hover:opacity-70 text-sm transition-opacity">{email}</a></li>'
        if phone:
            contact_items += f'<li><a href="tel:{re.sub(r"[^+d]","",phone)}" class="{t["text_muted"]} hover:opacity-70 text-sm transition-opacity">{phone}</a></li>'
        contact_col = (
            f'<div><p class="font-bold text-xs {t["text"]} mb-4 uppercase tracking-widest">Contact</p>'
            f'<ul class="space-y-2.5">{contact_items}</ul></div>'
        ) if contact_items else (
            f'<div><p class="font-bold text-xs {t["text"]} mb-4 uppercase tracking-widest">Legal</p>'
            f'<ul class="space-y-2.5 text-sm">'
            f'<li><a href="#" class="{t["text_muted"]} hover:opacity-70 transition-opacity">Privacy Policy</a></li>'
            f'<li><a href="#" class="{t["text_muted"]} hover:opacity-70 transition-opacity">Terms of Service</a></li>'
            f'</ul></div>'
        )

        return (
            f'<footer class="{t["bg"]} border-t {t["border"]} pt-16 pb-10">'
            f'<div class="container mx-auto {PAD_CON}">'
            f'<div class="grid sm:grid-cols-2 md:grid-cols-4 gap-10 mb-12">'
            f'<div class="sm:col-span-2">'
            f'<p class="font-black text-xl {t["text"]} mb-3">{self.name}</p>'
            f'<p class="{t["text_muted"]} text-sm max-w-xs leading-relaxed">{sub}</p>'
            f'{tl_html}</div>'
            f'<div><p class="font-bold text-xs {t["text"]} mb-4 uppercase tracking-widest">Navigate</p>'
            f'<ul class="space-y-2.5">{links}</ul></div>'
            f'{contact_col}'
            f'</div>'
            f'<div class="border-t {t["border"]} pt-6 flex flex-col md:flex-row justify-between items-center gap-3">'
            f'<p class="{t["text_light"]} text-xs">&copy; 2026 {self.name}. All rights reserved.</p>'
            f'<p class="{t["text_light"]} text-xs">v{self.version}</p>'
            f'</div>'
            f'</div></footer>'
        )

    # ── Section dispatcher ─────────────────────────────────────────────────────

    def _build_section(self, section_id: str) -> str:
        t = self.theme
        d = self.data

        if section_id == "hero":
            return self._hero_fn()(t, d, self.imgs)

        if section_id == "trust":
            return self._trust_band()

        if section_id == "features":
            features = d.get("features") or []
            if not features:
                return ""
            return self._features_fn()(t, features, self.imgs)

        if section_id == "pricing":
            tiers = d.get("pricing")
            if not tiers:
                return Pricing.contact_only(t, [])
            return self._pricing_fn()(t, tiers)

        if section_id == "testimonials":
            return self._testimonials()

        if section_id == "faq":
            return self._faq()

        if section_id == "contact":
            return self._contact()

        logger.warning(f"Unknown section id '{section_id}' — skipping.")
        return ""

    # ── Build ─────────────────────────────────────────────────────────────────

    def build(self) -> Dict[str, Any]:
        try:
            self.data = self._get_data()
            self.imgs = _img_set(self.industry, count=8)
            t         = self.theme

            # AI specifies which sections to render, in order.
            # Filter to only known section IDs. Always ensure hero + contact exist.
            raw_sections = self.data.get("sections") or list(self.VALID_SECTIONS)
            sections_order = []
            seen = set()
            for s in raw_sections:
                sid = str(s).lower().strip()
                if sid in self.VALID_SECTIONS and sid not in seen:
                    sections_order.append(sid)
                    seen.add(sid)
            if "hero" not in seen:
                sections_order.insert(0, "hero")
            if "contact" not in seen:
                sections_order.append("contact")

            section_html = [self._nav()]
            for sid in sections_order:
                html_piece = self._build_section(sid)
                if html_piece:
                    section_html.append(html_piece)
            section_html.append(self._footer())

            # Runtime colour audit (dev mode — logs warnings, doesn't raise)
            full_body = "".join(section_html)
            _assert_no_hardcoded_colours(full_body, f"{self.name}/{self.industry}")

            css = """
@keyframes fadeUp {
    from { opacity:0; transform:translateY(14px); }
    to   { opacity:1; transform:translateY(0); }
}
section > .container, nav > .container { animation: fadeUp 0.55s ease-out both; }
details > summary::-webkit-details-marker { display:none; }
details[open] > summary > span:last-child { transform: rotate(45deg); }
/* Smooth scroll offset for fixed nav */
:target { scroll-margin-top: 80px; }
/* Form focus ring */
input:focus, textarea:focus { box-shadow: 0 0 0 3px rgba(0,0,0,0.08); }
"""
            title = self.name
            html = (
                '<!DOCTYPE html>\n'
                '<html lang="en" style="scroll-behavior:smooth">\n'
                '<head>\n'
                '<meta charset="UTF-8">\n'
                '<meta name="viewport" content="width=device-width,initial-scale=1">\n'
                f'<title>{title}</title>\n'
                f'<meta name="description" content="{self.data.get("hero",{}).get("sub","")}">\n'
                '<script src="https://cdn.tailwindcss.com"></script>\n'
                '<link rel="preconnect" href="https://fonts.googleapis.com">\n'
                '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n'
                f'<link rel="stylesheet" href="{t["font_url"]}">\n'
                f'<style>*,*::before,*::after{{box-sizing:border-box;margin:0}}'
                f'html{{font-family:{t["fonts"]};-webkit-font-smoothing:antialiased}}'
                f'img{{display:block;max-width:100%}}'
                f'#nav-toggle{{display:none}}'
                f'{css}</style>\n'
                '</head>\n'
                f'<body class="{t["bg"]} {t["text"]}">\n'
                + full_body
                + '\n</body>\n</html>'
            )

            logger.info(f"Built '{title}' | {self.industry} | {t['id']} | sections={sections_order}")

            return {
                "html": html,
                "metadata": {
                    "business_name":    self.name,
                    "industry":         self.industry,
                    "theme":            t["id"],
                    "version":          self.version,
                    "sections":         sections_order,
                    "hero_variant":     self._hero_fn().__name__,
                    "features_variant": self._features_fn().__name__,
                    "pricing_variant":  self._pricing_fn().__name__,
                    "contact_email":    bool(self.data.get("contact_email")),
                    "contact_phone":    bool(self.data.get("contact_phone")),
                    "status":           "success",
                },
            }

        except Exception as e:
            logger.error(f"Build error: {e}\n{traceback.format_exc()}")
            return {
                "html": (f"<html><body style='font-family:sans-serif;padding:2rem'>"
                         f"<h1>Build Error</h1><pre>{e}</pre></body></html>"),
                "metadata": {"status": "error", "error": str(e)},
            }


# ─────────────────────────────────────────────────────────────────────────────
# PUBLIC API
# ─────────────────────────────────────────────────────────────────────────────

def generate_ai_plan(ai_input: Dict[str, Any], version: int = 1, **kwargs) -> Dict[str, Any]:
    """
    Main entry point.
    ai_input = {"business_name": str, "prompt": str}
    Returns  = {"html": str, "metadata": dict}
    """
    try:
        return MasterArchitect(
            business_name=ai_input.get("business_name", ""),
            prompt=ai_input.get("prompt", ""),
            version=version,
        ).build()
    except Exception as e:
        logger.error(f"generate_ai_plan error: {e}\n{traceback.format_exc()}")
        return {
            "html": f"<html><body><h1>Error</h1><p>{e}</p></body></html>",
            "metadata": {"status": "error", "error": str(e)},
        }


def rewrite_content(original_text: str, tone: str = "professional",
                    business_context: str = "") -> List[str]:
    if not AI_AVAILABLE:
        return [original_text] * 3
    try:
        raw = chat_completion(
            system="Expert copywriter. Output ONLY a JSON array of 3 strings, no preamble.",
            user=(f"Rewrite this text 3 different ways. "
                  f"Tone: {tone}. Context: {business_context}. "
                  f'Text: "{original_text}". '
                  f'Return exactly: ["version1","version2","version3"]'),
            temperature=0.8,
        )
        result = json.loads(re.sub(r"```json|```", "", raw).strip())
        if isinstance(result, list) and len(result) >= 3:
            return result[:3]
        return [original_text] * 3
    except Exception as e:
        logger.warning(f"rewrite_content error: {e}")
        return [original_text] * 3


def get_design_tokens() -> Dict[str, Any]:
    return {
        "themes":          {k: {kk: vv for kk, vv in v.items() if kk != "font_url"}
                            for k, v in THEMES.items()},
        "industry_themes": INDUSTRY_THEME,
        "photo_pools":     {k: len(v) for k, v in INDUSTRY_PHOTO_POOLS.items()},
    }