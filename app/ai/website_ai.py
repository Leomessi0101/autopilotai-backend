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

PADDING_SECTION    = "py-28 md:py-36"
PADDING_SECTION_SM = "py-16 md:py-24"
PADDING_CONTAINER  = "px-5 md:px-8 lg:px-12"


# ============================================================================
# INDUSTRY-DRIVEN IMAGE SYSTEM
# ============================================================================
# Each industry has its own dedicated photo pool. Images are selected
# deterministically by industry — no keyword fuzzy matching that can fail.
# Every photo ID has been manually verified to be appropriate for the industry.

INDUSTRY_PHOTO_POOLS: Dict[str, List[str]] = {
    "construction": [
        "photo-1504307651254-35680f356dfd",  # building under construction
        "photo-1541888946425-d81bb19240f5",  # workers on site
        "photo-1590674899484-d5640e854abe",  # crane / construction
        "photo-1581578731548-c64695cc6952",  # workers / hard hats
        "photo-1565117623394-5f93fd4c7a06",  # renovation / tools
        "photo-1530836176759-510f6ca9f76f",  # building exterior / modern
        "photo-1558618666-fcd25c85cd64",     # concrete / architecture
        "photo-1600585154340-be6161a56a0c",  # finished modern building
    ],
    "legal": [
        "photo-1589578527966-fdac0f44566c",  # law books / scales
        "photo-1436450412740-6b988f486c6b",  # courthouse / legal
        "photo-1505664194779-8beaceb5c7c7",  # professional office meeting
        "photo-1521791055366-0d553872952f",  # attorney / desk
        "photo-1450101499163-c8848c66ca85",  # contract / document signing
        "photo-1568992687947-868a62a9f521",  # professional office interior
        "photo-1497366216548-37526070297c",  # modern law office
        "photo-1552664730-d307ca884978",     # boardroom / professional
    ],
    "logistics": [
        "photo-1504493188-45c49f65c6ba",     # warehouse / logistics
        "photo-1586528116311-ad8dd3c8310d",  # shipping / cargo
        "photo-1601584115197-04ecc0da31d7",  # freight truck / delivery
        "photo-1494412574643-ff11b0a5c1c3",  # container port
        "photo-1519003300449-424ad0405076",  # forklift / warehouse
        "photo-1543169964-f2e91dc1fbf4",     # supply chain / boxes
        "photo-1473445730015-841f29a9490b",  # aerial shipping port
        "photo-1565891741441-64926e3e5c74",  # delivery van / courier
    ],
    "automotive": [
        "photo-1492144534655-ae79c964c9d7",  # sports car
        "photo-1503376780353-7e6692767b70",  # car detail
        "photo-1544636331-e26879cd4d9b",     # mechanic / garage
        "photo-1565043589221-1a6fd9ae45c7",  # auto repair shop
        "photo-1558981806-ec527fa84c39",     # car showroom
        "photo-1549317661-bd32c8ce0db2",     # car interior
        "photo-1580273916550-e323be2ae537",  # auto dealership exterior
        "photo-1520340356584-f9917d1eea6f",  # car maintenance / technician
    ],
    "restaurant": [
        "photo-1504674900247-0877df9cc836",  # food spread
        "photo-1414235077428-338989a2e8c0",  # restaurant interior
        "photo-1555396273-367ea4eb4db5",     # restaurant atmosphere
        "photo-1517248135467-4c7edcad34c4",  # dining room
        "photo-1512621776951-a57141f2eefd",  # healthy food
        "photo-1467003909585-2f8a72700288",  # chef cooking
        "photo-1565299585323-38d6b0865b47",  # pizza / food
        "photo-1484723091739-30a097e8f929",  # breakfast food
    ],
    "health": [
        "photo-1576091160550-2173dba999ef",  # medical / health
        "photo-1559757148-5c350d0d3c56",     # healthcare professional
        "photo-1535914254981-b5012eebbd15",  # hospital / clinic
        "photo-1571772996211-2f02c9727629",  # doctor / patient
        "photo-1540420773420-3366772f4999",  # wellness / nature
        "photo-1631217868264-e5b90bb7e133",  # medical equipment
        "photo-1582750433449-648ed127bb54",  # clinic interior
        "photo-1532938911079-1b06ac7ceec7",  # doctor consultation
    ],
    "fitness": [
        "photo-1534438327276-14e5300c3a48",  # gym interior
        "photo-1571019613454-1cb2f99b2d8b",  # fitness / workout
        "photo-1517836357463-d25dfeac3438",  # gym equipment
        "photo-1549060279-7e168fcee0c2",     # running / fitness
        "photo-1526506118085-60ce8714f8c5",  # weight training
        "photo-1574680178050-55c6a6a96e0a",  # yoga / exercise
        "photo-1544033527-b192daee1f5b",     # group fitness
        "photo-1540497077202-7c8a3999166f",  # fitness lifestyle
    ],
    "beauty": [
        "photo-1487412947147-5cebf100ffc2",  # beauty / cosmetics
        "photo-1560066984-138dadb4c035",     # salon / hair
        "photo-1522337360788-8b13dee7a37e",  # beauty treatment
        "photo-1596704017254-9b121068fb31",  # spa / wellness
        "photo-1571019613576-2b22c76fd955",  # skincare products
        "photo-1519014816548-bf5fe059798b",  # beauty studio
        "photo-1634449571010-02389ed0f9b0",  # nail / beauty
        "photo-1540555700478-4be289fbecef",  # spa interior
    ],
    "finance": [
        "photo-1611974789855-9c2a0a7236a3",  # trading / finance
        "photo-1563986768609-322da13575f3",  # financial planning
        "photo-1468254095679-bbcba94a7066",  # finance / business
        "photo-1454165804606-c3d57bc86b40",  # business meeting / finance
        "photo-1460925895917-afdab827c52f",  # financial charts
        "photo-1601597111158-2fceff292cdc",  # investment / growth
        "photo-1526304640581-d334cdbbf45e",  # wealth management
        "photo-1565514020179-026b92b84bb6",  # financial office
    ],
    "real_estate": [
        "photo-1560518883-ce09059eeffa",     # luxury home interior
        "photo-1570129477492-45c003edd2be",  # modern house exterior
        "photo-1513584684374-8bab748fbf90",  # apartment / urban
        "photo-1501183638710-841dd1904471",  # interior design
        "photo-1486325212027-8081e485255e",  # house for sale
        "photo-1523217582562-09d0def993a6",  # luxury property
        "photo-1598300042247-d088f8ab3a91",  # real estate sign / house
        "photo-1580587771525-78b9dba3b914",  # modern architecture
    ],
    "education": [
        "photo-1503676260728-1c00da094a0b",  # library / books
        "photo-1456513080510-7bf3a84b82f8",  # study / learning
        "photo-1509062522246-3755977927d7",  # classroom / teaching
        "photo-1427504494785-3a9ca7044f45",  # university / campus
        "photo-1522202176988-66273c2fd55f",  # students learning
        "photo-1434030216411-0b793f4b4173",  # online learning
        "photo-1546410531-bb4caa6b424d",     # graduation / success
        "photo-1488190211105-8b0e65b80b4e",  # student reading
    ],
    "travel": [
        "photo-1501854140801-50d01698950b",  # scenic landscape
        "photo-1436491865332-7a61a109cc05",  # airplane / travel
        "photo-1488085061387-422e29b40080",  # adventure / travel
        "photo-1476514525535-07fb3b4ae5f1",  # tropical beach
        "photo-1530521954074-e64f6810b32d",  # hotel / resort pool
        "photo-1503220317375-aaad61436b1b",  # travel destination
        "photo-1507003211169-0a1dd7228f2d",  # traveller
        "photo-1528360983277-13d401cdc186",  # city tourism
    ],
    "ecommerce": [
        "photo-1556742049-0cfed4f6a45d",     # shopping / ecommerce
        "photo-1472851294608-062f824d29cc",  # online shopping
        "photo-1607082348824-0a96f2a4b9da",  # packaging / products
        "photo-1523275335684-37898b6baf30",  # product photography
        "photo-1581091226825-a6a2a5aee158",  # delivery / packaging
        "photo-1526170375885-4d8ecf77b99f",  # product flat lay
        "photo-1491553895911-0055eca6402d",  # shoes / product
        "photo-1585386959984-a4155224a1ad",  # beauty product
    ],
    "saas": [
        "photo-1518770660439-4636190af475",  # technology / circuit
        "photo-1461749280684-dccba630e2f6",  # coding / development
        "photo-1550751827-4bd374c3f58b",     # cybersecurity / tech
        "photo-1551434678-e076c223a692",     # laptop / work
        "photo-1497366216548-37526070297c",  # modern office / tech
        "photo-1573164713988-8665fc963095",  # woman at computer
        "photo-1498050108023-c5249f4df085",  # laptop coding
        "photo-1522071820081-009f0129c71c",  # team collaboration
    ],
    "ai": [
        "photo-1677442135703-1787eea5ce01",  # AI / neural network
        "photo-1620712943543-bcc4688e7485",  # futuristic tech
        "photo-1555255707-c07966088b7b",     # AI visualization
        "photo-1518770660439-4636190af475",  # circuit board
        "photo-1535378917042-10a22c95931a",  # robot / AI
        "photo-1593508512255-86ab42a8e620",  # virtual reality
        "photo-1589254065878-42efea3c6521",  # AI / machine learning
        "photo-1558346547-4439467bd1d5",     # data visualization
    ],
    "developer": [
        "photo-1461749280684-dccba630e2f6",  # coding monitor
        "photo-1498050108023-c5249f4df085",  # laptop / code
        "photo-1555066931-4365d14bab8c",     # code on screen
        "photo-1607799279861-4dd421887fb3",  # developer workspace
        "photo-1519389950473-47ba0277781c",  # multiple monitors / dev
        "photo-1537432376769-00f5c2f4c8d2",  # terminal / command line
        "photo-1573495612522-4c73ff6a54b0",  # developer / tech
        "photo-1571171637578-41bc2dd41cd2",  # code IDE
    ],
    "startup": [
        "photo-1559136555-9303baea8ebd",     # startup culture
        "photo-1531297484001-80022131f5a1",  # modern workspace
        "photo-1556761175-4b46a572b786",     # startup team
        "photo-1522202176988-66273c2fd55f",  # team collaboration
        "photo-1542744173-8e7e53415bb0",     # team meeting
        "photo-1572021335469-31706a17aaef",  # modern office / startup
        "photo-1560472355-536de3962603",     # brainstorming
        "photo-1524758631624-e2822e304c36",  # modern coworking
    ],
    "agency": [
        "photo-1558655146-9f40138edfeb",     # creative agency
        "photo-1524758631624-e2822e304c36",  # creative workspace
        "photo-1497366754035-f200968a6e72",  # design studio
        "photo-1535016120720-40c646be5580",  # advertising / marketing
        "photo-1531538606174-0f90ff5dce83",  # creative team
        "photo-1487017159836-4e23ece2e4cf",  # laptop / creative
        "photo-1542744094-3a31f272c490",     # design workspace
        "photo-1573164574511-73c773193279",  # marketing meeting
    ],
    "luxury": [
        "photo-1518546305927-5a555bb7020d",  # luxury lifestyle
        "photo-1571266752045-a0f5cfb5efcb",  # luxury interior
        "photo-1602143407151-7111542de6e8",  # luxury product
        "photo-1545912452-8bbe7ae249df",     # luxury hotel
        "photo-1466978913421-dad2ebd01d17",  # champagne / luxury
        "photo-1582719508461-905c673771fd",  # luxury resort
        "photo-1523438885200-e635ba2c371e",  # luxury watch
        "photo-1549298916-b41d501d3772",     # luxury fashion
    ],
    "nature": [
        "photo-1441974231531-c6227db76b6e",  # forest / nature
        "photo-1506905925346-21bda4d32df4",  # mountains / nature
        "photo-1469474968028-56623f02e42e",  # scenic nature
        "photo-1500534314209-a25ddb2bd429",  # organic / sustainable
        "photo-1472214103451-9374bd1c798e",  # green fields
        "photo-1542601906990-b4d3fb778b09",  # nature / organic
        "photo-1448375240586-882707db888b",  # forest path
        "photo-1518173946687-a4c8892bbd9f",  # sunrise / nature
    ],
    "nonprofit": [
        "photo-1593113630400-ea4288922559",  # volunteers
        "photo-1559027615-cd4628902d4a",     # community / helping
        "photo-1532629345422-7515f3d16bb6",  # charity / giving
        "photo-1509099836639-18ba1795216d",  # community meeting
        "photo-1469571486292-b53601010376",  # people / community
        "photo-1488521787991-ed7bbaae773c",  # diversity / inclusion
        "photo-1556484687-30636164638b",     # volunteering
        "photo-1507003211169-0a1dd7228f2d",  # positive impact
    ],
    "events": [
        "photo-1540575467063-178a50c2df87",  # event / conference
        "photo-1511795409834-ef04bbd61622",  # party / celebration
        "photo-1464366400600-7168b8af9bc3",  # music / concert
        "photo-1519167758481-83f550bb49b3",  # wedding venue
        "photo-1492684223066-81342ee5ff30",  # live event
        "photo-1478147427282-58a87a433d8f",  # festival / outdoor
        "photo-1529543544282-ea669407fca3",  # corporate event
        "photo-1551818255-e6e10975bc17",     # wedding photography
    ],
}

# Default fallback pool (professional/business)
_DEFAULT_PHOTO_POOL = [
    "photo-1552664730-d307ca884978",
    "photo-1460925895917-afdab827c52f",
    "photo-1556742049-0cfed4f6a45d",
    "photo-1497366216548-37526070297c",
    "photo-1454165804606-c3d57bc86b40",
    "photo-1522202176988-66273c2fd55f",
]


def _get_photo_pool(industry: str) -> List[str]:
    """Returns the correct photo pool for the given industry. Always returns a non-empty list."""
    return INDUSTRY_PHOTO_POOLS.get(industry, _DEFAULT_PHOTO_POOL)


def _get_industry_image_url(industry: str, index: int = 0, width: int = 900) -> str:
    """
    Get an Unsplash image URL directly from the industry photo pool.
    Bypasses all keyword matching — industry drives photo selection 100%.
    """
    pool = _get_photo_pool(industry)
    chosen = pool[index % len(pool)]
    return f"https://images.unsplash.com/{chosen}?w={width}&auto=format&fit=crop&q=82"


def _get_industry_image_set(industry: str, count: int = 6, width: int = 900) -> List[str]:
    """Get 'count' distinct images for the given industry, cycling the pool if needed."""
    pool = _get_photo_pool(industry)
    return [
        f"https://images.unsplash.com/{pool[i % len(pool)]}?w={width}&auto=format&fit=crop&q=82"
        for i in range(count)
    ]


# ============================================================================
# 8 DISTINCT THEMES
# ============================================================================
# IMPORTANT: Every theme key used inside render_* methods must be defined here.
# Adding a key here means ALL sections automatically pick it up — no per-section
# colour decisions, eliminating the "random purple" problem.

THEMES: Dict[str, Dict] = {
    "pro_light": {
        "id": "pro_light", "mode": "light",
        "bg":           "bg-white",
        "bg_alt":       "bg-slate-50",
        "bg_section":   "bg-blue-50/40",
        "text":         "text-gray-950",
        "text_muted":   "text-gray-500",
        "text_light":   "text-gray-400",
        "primary":      "blue",
        "primary_hex":  "#2563eb",
        "grad":         "from-blue-600 via-blue-500 to-cyan-400",
        "grad_text":    "from-blue-600 to-cyan-500",
        "grad_subtle":  "from-blue-50/80 to-cyan-50/60",
        "grad_cta_bg":  "from-blue-50/60 to-cyan-50/40",
        "glass":        GLASS_LIGHT,
        "accent":       "cyan",
        "border":       "border-gray-200",
        "border_strong":"border-gray-300",
        "nav_bg":       "bg-white/95 border-b border-gray-100 shadow-sm",
        "badge_style":  "bg-blue-50 text-blue-700 border border-blue-200",
        "stat_color":   "text-blue-600",
        "check_color":  "text-blue-500",
        "divider":      "divide-gray-100",
        "fonts":        "'Plus Jakarta Sans', 'Inter', sans-serif",
        "font_url":     "https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800;900&display=swap",
    },
    "luxury_dark": {
        "id": "luxury_dark", "mode": "dark",
        "bg":           "bg-[#0a0a0f]",
        "bg_alt":       "bg-[#0f0f18]",
        "bg_section":   "bg-[#12101f]",
        "text":         "text-white",
        "text_muted":   "text-gray-300",
        "text_light":   "text-gray-500",
        "primary":      "violet",
        "primary_hex":  "#7c3aed",
        "grad":         "from-violet-600 via-purple-500 to-fuchsia-500",
        "grad_text":    "from-violet-400 to-fuchsia-400",
        "grad_subtle":  "from-violet-950/50 to-fuchsia-950/30",
        "grad_cta_bg":  "from-violet-950/40 to-fuchsia-950/30",
        "glass":        GLASS_DARK,
        "accent":       "fuchsia",
        "border":       "border-white/10",
        "border_strong":"border-white/20",
        "nav_bg":       "bg-black/80 border-b border-white/8 backdrop-blur-xl",
        "badge_style":  "bg-violet-950/60 text-violet-300 border border-violet-500/30",
        "stat_color":   "text-fuchsia-400",
        "check_color":  "text-fuchsia-400",
        "divider":      "divide-white/8",
        "fonts":        "'Syne', sans-serif",
        "font_url":     "https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&display=swap",
    },
    "clean_emerald": {
        "id": "clean_emerald", "mode": "light",
        "bg":           "bg-[#f8fffe]",
        "bg_alt":       "bg-white",
        "bg_section":   "bg-emerald-50/50",
        "text":         "text-slate-900",
        "text_muted":   "text-slate-500",
        "text_light":   "text-slate-400",
        "primary":      "emerald",
        "primary_hex":  "#059669",
        "grad":         "from-emerald-500 via-teal-500 to-cyan-500",
        "grad_text":    "from-emerald-600 to-teal-500",
        "grad_subtle":  "from-emerald-50/80 to-teal-50/60",
        "grad_cta_bg":  "from-emerald-50/60 to-teal-50/40",
        "glass":        GLASS_LIGHT,
        "accent":       "teal",
        "border":       "border-emerald-100",
        "border_strong":"border-emerald-200",
        "nav_bg":       "bg-white/95 border-b border-emerald-100 shadow-sm",
        "badge_style":  "bg-emerald-50 text-emerald-700 border border-emerald-200",
        "stat_color":   "text-emerald-600",
        "check_color":  "text-emerald-500",
        "divider":      "divide-emerald-50",
        "fonts":        "'DM Sans', sans-serif",
        "font_url":     "https://fonts.googleapis.com/css2?family=DM+Sans:opsz,wght@9..40,400;9..40,500;9..40,700;9..40,800&display=swap",
    },
    "tech_midnight": {
        "id": "tech_midnight", "mode": "dark",
        "bg":           "bg-gray-950",
        "bg_alt":       "bg-gray-900",
        "bg_section":   "bg-[#0c1628]",
        "text":         "text-white",
        "text_muted":   "text-gray-400",
        "text_light":   "text-gray-600",
        "primary":      "cyan",
        "primary_hex":  "#06b6d4",
        "grad":         "from-cyan-500 via-blue-500 to-indigo-600",
        "grad_text":    "from-cyan-400 to-blue-400",
        "grad_subtle":  "from-cyan-950/40 to-indigo-950/40",
        "grad_cta_bg":  "from-cyan-950/30 to-indigo-950/30",
        "glass":        GLASS_DARK,
        "accent":       "blue",
        "border":       "border-white/8",
        "border_strong":"border-white/15",
        "nav_bg":       "bg-gray-950/90 border-b border-white/8 backdrop-blur-xl",
        "badge_style":  "bg-cyan-950/50 text-cyan-400 border border-cyan-500/25",
        "stat_color":   "text-cyan-400",
        "check_color":  "text-cyan-400",
        "divider":      "divide-white/8",
        "fonts":        "'Space Grotesk', sans-serif",
        "font_url":     "https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&display=swap",
    },
    "warm_amber": {
        "id": "warm_amber", "mode": "light",
        "bg":           "bg-[#fffbf2]",
        "bg_alt":       "bg-amber-50",
        "bg_section":   "bg-orange-50/50",
        "text":         "text-amber-950",
        "text_muted":   "text-amber-700",
        "text_light":   "text-amber-400",
        "primary":      "amber",
        "primary_hex":  "#d97706",
        "grad":         "from-amber-500 via-orange-500 to-rose-500",
        "grad_text":    "from-amber-600 to-orange-500",
        "grad_subtle":  "from-amber-50/80 to-orange-50/60",
        "grad_cta_bg":  "from-amber-50/60 to-orange-50/40",
        "glass":        GLASS_LIGHT,
        "accent":       "orange",
        "border":       "border-amber-200",
        "border_strong":"border-amber-300",
        "nav_bg":       "bg-[#fffbf2]/95 border-b border-amber-200 shadow-sm",
        "badge_style":  "bg-amber-100 text-amber-800 border border-amber-300",
        "stat_color":   "text-orange-600",
        "check_color":  "text-amber-500",
        "divider":      "divide-amber-100",
        "fonts":        "'Fraunces', serif",
        "font_url":     "https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,700;9..144,900&display=swap",
    },
    "midnight_rose": {
        "id": "midnight_rose", "mode": "dark",
        "bg":           "bg-[#0d0508]",
        "bg_alt":       "bg-[#130a0e]",
        "bg_section":   "bg-[#180c11]",
        "text":         "text-rose-50",
        "text_muted":   "text-rose-200/80",
        "text_light":   "text-rose-400/60",
        "primary":      "rose",
        "primary_hex":  "#e11d48",
        "grad":         "from-rose-500 via-pink-600 to-fuchsia-600",
        "grad_text":    "from-rose-400 to-pink-400",
        "grad_subtle":  "from-rose-950/40 to-fuchsia-950/30",
        "grad_cta_bg":  "from-rose-950/30 to-fuchsia-950/20",
        "glass":        GLASS_DARK,
        "accent":       "pink",
        "border":       "border-rose-900/40",
        "border_strong":"border-rose-700/40",
        "nav_bg":       "bg-[#0d0508]/90 border-b border-rose-900/30 backdrop-blur-xl",
        "badge_style":  "bg-rose-950/60 text-rose-300 border border-rose-500/20",
        "stat_color":   "text-rose-400",
        "check_color":  "text-rose-400",
        "divider":      "divide-rose-900/30",
        "fonts":        "'Cormorant Garamond', serif",
        "font_url":     "https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@300;400;600;700&display=swap",
    },
    "slate_corporate": {
        "id": "slate_corporate", "mode": "light",
        "bg":           "bg-white",
        "bg_alt":       "bg-slate-50",
        "bg_section":   "bg-indigo-50/30",
        "text":         "text-slate-900",
        "text_muted":   "text-slate-500",
        "text_light":   "text-slate-400",
        "primary":      "indigo",
        "primary_hex":  "#4338ca",
        "grad":         "from-indigo-700 via-indigo-600 to-blue-600",
        "grad_text":    "from-indigo-700 to-blue-600",
        "grad_subtle":  "from-indigo-50/80 to-blue-50/60",
        "grad_cta_bg":  "from-indigo-50/60 to-blue-50/40",
        "glass":        GLASS_LIGHT,
        "accent":       "blue",
        "border":       "border-slate-200",
        "border_strong":"border-slate-300",
        "nav_bg":       "bg-white border-b border-slate-200 shadow-sm",
        "badge_style":  "bg-indigo-50 text-indigo-700 border border-indigo-200",
        "stat_color":   "text-indigo-700",
        "check_color":  "text-indigo-600",
        "divider":      "divide-slate-100",
        "fonts":        "'IBM Plex Sans', sans-serif",
        "font_url":     "https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600;700&display=swap",
    },
    "forest_green": {
        "id": "forest_green", "mode": "dark",
        "bg":           "bg-[#050e08]",
        "bg_alt":       "bg-[#081510]",
        "bg_section":   "bg-[#0a1a0d]",
        "text":         "text-green-50",
        "text_muted":   "text-green-200/70",
        "text_light":   "text-green-400/50",
        "primary":      "green",
        "primary_hex":  "#16a34a",
        "grad":         "from-green-500 via-emerald-500 to-teal-500",
        "grad_text":    "from-green-400 to-emerald-400",
        "grad_subtle":  "from-green-950/50 to-teal-950/30",
        "grad_cta_bg":  "from-green-950/40 to-teal-950/30",
        "glass":        GLASS_DARK,
        "accent":       "teal",
        "border":       "border-green-900/40",
        "border_strong":"border-green-700/40",
        "nav_bg":       "bg-[#050e08]/90 border-b border-green-900/30 backdrop-blur-xl",
        "badge_style":  "bg-green-950/60 text-green-300 border border-green-500/25",
        "stat_color":   "text-green-400",
        "check_color":  "text-green-400",
        "divider":      "divide-green-900/30",
        "fonts":        "'Cabin', sans-serif",
        "font_url":     "https://fonts.googleapis.com/css2?family=Cabin:wght@400;600;700&display=swap",
    },
}


# ============================================================================
# INDUSTRY DETECTION
# ============================================================================

INDUSTRY_KEYWORD_MAP: Dict[str, List[str]] = {
    "saas":         ["software", "app", "platform", "cloud", "api", "saas", "dashboard", "workflow", "automation", "crm", "erp"],
    "ai":           ["ai", "artificial intelligence", "machine learning", "ml", "neural", "algorithm", "gpt", "llm", "data science"],
    "ecommerce":    ["shop", "store", "ecommerce", "e-commerce", "sell", "product", "cart", "marketplace", "dropship", "retail"],
    "health":       ["health", "medical", "wellness", "clinic", "doctor", "hospital", "therapy", "mental health", "nutrition", "physio"],
    "fitness":      ["fitness", "gym", "personal trainer", "workout", "yoga", "crossfit", "athletics", "exercise"],
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
    scores: Dict[str, int] = {ind: 0 for ind in INDUSTRY_KEYWORD_MAP}
    for industry, keywords in INDUSTRY_KEYWORD_MAP.items():
        for kw in keywords:
            if kw in prompt_lower:
                scores[industry] += len(kw.split())  # weight multi-word matches higher
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
    "fitness":      "clean_emerald",
    "finance":      "slate_corporate",
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
    "construction": "slate_corporate",
    "legal":        "slate_corporate",
    "logistics":    "slate_corporate",
    "automotive":   "slate_corporate",
    "nonprofit":    "clean_emerald",
    "events":       "warm_amber",
}

INDUSTRY_ALTERNATES: Dict[str, List[str]] = {
    "saas":         ["pro_light", "tech_midnight"],
    "agency":       ["luxury_dark", "midnight_rose"],
    "health":       ["clean_emerald", "pro_light"],
    "fitness":      ["clean_emerald", "tech_midnight"],
    "finance":      ["slate_corporate", "pro_light"],
    "startup":      ["tech_midnight", "luxury_dark"],
    "ecommerce":    ["warm_amber", "clean_emerald"],
    "construction": ["slate_corporate"],
    "legal":        ["slate_corporate"],
    "logistics":    ["slate_corporate", "pro_light"],
    "real_estate":  ["slate_corporate", "pro_light"],
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

def extract_business_name(raw_name: str, prompt: str) -> tuple:
    raw = (raw_name or "").strip()
    prompt_text = (prompt or "").strip()

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
            name_end = len(after)
            for sep in [".", ",", ";", " -", " and we", " that ", " which "]:
                pos = after.find(sep)
                if pos > 0 and pos < name_end:
                    name_end = pos
            name_from_prompt = after[:name_end].strip()
            before = prompt_text[:idx].strip()
            remainder = prompt_text[idx + len(indicator) + name_end:].strip(" .,;")
            cleaned_prompt = f"{before} {remainder}".strip()
            return name_from_prompt, cleaned_prompt

    if not raw:
        return "", prompt_text

    raw_lower = raw.lower()
    for starter in _DESCRIPTION_STARTERS:
        if raw_lower.startswith(starter):
            combined = f"{raw}. {prompt_text}".strip(" .")
            return "", combined

    for prefix in _NAME_PREFIXES:
        if raw_lower.startswith(prefix):
            remainder = raw[len(prefix):].strip()
            for sep in [" - ", " — ", ", ", ". "]:
                if sep in remainder:
                    parts = remainder.split(sep, 1)
                    return parts[0].strip(), f"{parts[1].strip()}. {prompt_text}".strip(" .")
            return remainder.strip(), prompt_text

    for sep in [" - ", " — ", ": ", ", we ", ". we "]:
        if sep in raw:
            parts = raw.split(sep, 1)
            return parts[0].strip(), f"{parts[1].strip()}. {prompt_text}".strip(" .")

    if len(raw.split()) <= 5:
        return raw, prompt_text

    words = raw.split()
    name = " ".join(words[:3]).rstrip(".,!?")
    overflow = " ".join(words[3:])
    return name, f"{overflow}. {prompt_text}".strip(" .")


def derive_name_from_prompt(prompt: str, industry: str) -> str:
    industry_defaults = {
        "construction": "BuildRight Group",
        "legal":        "Sterling Law",
        "finance":      "Apex Capital",
        "health":       "Vitalis Health",
        "fitness":      "Apex Fitness",
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
# SHARED SECTION HELPERS
# ============================================================================

def _gradient_btn(theme: Dict, text: str, href: str = "#contact", extra_classes: str = "") -> str:
    """Primary CTA button — always uses theme gradient."""
    return (
        f'<a href="{href}" class="inline-block px-8 py-4 bg-gradient-to-r {theme["grad"]} '
        f'text-white rounded-xl font-bold shadow-lg {HOVER_LIFT} {extra_classes}">{text}</a>'
    )

def _ghost_btn(theme: Dict, text: str, href: str = "#features", extra_classes: str = "") -> str:
    """Secondary ghost/outline button — uses theme glass + border."""
    return (
        f'<a href="{href}" class="{theme["glass"]} border {theme["border"]} {theme["text"]} '
        f'px-8 py-4 rounded-xl font-semibold {HOVER_GLOW} {extra_classes}">{text}</a>'
    )

def _section_label(theme: Dict, text: str) -> str:
    return f'<p class="text-xs font-semibold uppercase tracking-[0.2em] {theme["text_light"]} mb-4">{text}</p>'

def _section_heading(theme: Dict, text: str, subtext: str = "") -> str:
    sub_html = f'<p class="text-lg {theme["text_muted"]} mt-4 max-w-2xl mx-auto leading-relaxed">{subtext}</p>' if subtext else ""
    return f'<h2 class="{HEADING_SECTION} {theme["text"]}">{text}</h2>{sub_html}'

def _gradient_text(theme: Dict, text: str) -> str:
    return f'<span class="bg-gradient-to-r {theme["grad_text"]} bg-clip-text text-transparent">{text}</span>'


# ============================================================================
# HERO VARIANTS
# ============================================================================

class HeroVariant:

    @staticmethod
    def split_grid(theme: Dict, data: Dict, images: List[str]) -> str:
        img = images[0] if images else ""
        badge = data.get("tagline", "Premium Experience")
        h1 = data.get("hero", {}).get("h1", "Premium Solution")
        sub = data.get("hero", {}).get("sub", "Built for excellence")
        cta = data.get("hero", {}).get("cta", "Get Started")
        mode_overlay = "bg-gradient-to-l" if theme["mode"] == "light" else "bg-gradient-to-l"
        try:
            return f"""
            <section id="hero" class="relative {theme['bg']} overflow-hidden pt-32 pb-24 md:pt-40 md:pb-32">
                <!-- Background atmosphere -->
                <div class="absolute top-0 right-0 w-1/2 h-full pointer-events-none select-none">
                    <div class="absolute inset-0 {mode_overlay} {theme['grad_subtle']} opacity-70 z-10"></div>
                </div>
                <!-- Glow blob -->
                <div class="absolute top-20 right-1/4 w-96 h-96 bg-gradient-to-r {theme['grad']} opacity-[0.06] blur-[120px] rounded-full pointer-events-none"></div>

                <div class="container mx-auto {PADDING_CONTAINER} relative z-10">
                    <div class="grid lg:grid-cols-2 gap-14 xl:gap-20 items-center">
                        <!-- Copy -->
                        <div class="space-y-7">
                            <div class="inline-flex items-center gap-2 px-4 py-2 rounded-full text-xs font-semibold uppercase tracking-widest {theme['badge_style']}">
                                <span class="w-1.5 h-1.5 rounded-full bg-current animate-pulse"></span>
                                {badge}
                            </div>
                            <h1 class="{HEADING_HERO} {theme['text']}">{h1}</h1>
                            <p class="text-lg md:text-xl {theme['text_muted']} leading-relaxed max-w-lg">{sub}</p>
                            <div class="flex flex-wrap gap-4 pt-2">
                                {_gradient_btn(theme, cta, "#contact", "text-base px-9 py-4")}
                                {_ghost_btn(theme, "See how it works →", "#features", "text-base px-9 py-4")}
                            </div>
                            <!-- Social proof -->
                            <div class="flex items-center gap-3 pt-4 border-t {theme['border']}">
                                <div class="flex -space-x-2">
                                    {''.join([f'<div class="w-8 h-8 rounded-full bg-gradient-to-br {theme["grad"]} border-2 border-white/30 opacity-80"></div>' for _ in range(4)])}
                                </div>
                                <span class="text-sm {theme['text_muted']}">Join <span class="font-bold {theme['stat_color']}">2,400+</span> businesses already growing</span>
                            </div>
                        </div>
                        <!-- Image -->
                        <div class="relative h-[400px] md:h-[500px] xl:h-[560px]">
                            <div class="absolute -inset-4 bg-gradient-to-br {theme['grad']} opacity-[0.12] blur-3xl rounded-3xl"></div>
                            <img src="{img}" alt="hero visual"
                                 class="relative z-10 w-full h-full object-cover rounded-2xl shadow-2xl"
                                 loading="eager" />
                            <!-- Corner accent -->
                            <div class="absolute -bottom-4 -right-4 w-24 h-24 bg-gradient-to-br {theme['grad']} opacity-40 rounded-2xl blur-2xl"></div>
                        </div>
                    </div>
                </div>
            </section>"""
        except Exception as e:
            logger.error(f"split_grid hero error: {e}")
            return f"<section id='hero' class='{theme['bg']} py-32'><h1 class='{theme['text']} text-5xl font-bold text-center'>Welcome</h1></section>"

    @staticmethod
    def centered_spotlight(theme: Dict, data: Dict, images: List[str]) -> str:
        img = images[0] if images else ""
        h1 = data.get("hero", {}).get("h1", "Premium Solution")
        sub = data.get("hero", {}).get("sub", "Built for excellence")
        cta = data.get("hero", {}).get("cta", "Get Started")
        tagline = data.get("tagline", "")
        try:
            return f"""
            <section id="hero" class="relative {theme['bg']} overflow-hidden min-h-[90vh] flex items-center">
                <!-- Full-bleed background image -->
                <div class="absolute inset-0 select-none pointer-events-none">
                    <img src="{img}" alt="" class="w-full h-full object-cover {'opacity-10' if theme['mode'] == 'light' else 'opacity-15'}" loading="eager" />
                    <div class="absolute inset-0 {'bg-white/70' if theme['mode'] == 'light' else 'bg-black/60'}"></div>
                </div>
                <!-- Glow orbs -->
                <div class="absolute top-1/3 left-1/2 -translate-x-1/2 w-[700px] h-[700px] bg-gradient-to-r {theme['grad']} opacity-[0.08] blur-[120px] rounded-full pointer-events-none"></div>
                <div class="absolute bottom-0 right-0 w-80 h-80 bg-gradient-to-r {theme['grad']} opacity-[0.06] blur-[80px] rounded-full pointer-events-none"></div>

                <div class="container mx-auto {PADDING_CONTAINER} relative z-10 text-center py-36 md:py-48">
                    <div class="max-w-4xl mx-auto space-y-8">
                        {f'<p class="text-xs font-semibold uppercase tracking-[0.3em] {theme["text_muted"]}">— {tagline} —</p>' if tagline else ''}
                        <h1 class="{HEADING_HERO} {theme['text']}">{h1}</h1>
                        <p class="text-xl md:text-2xl {theme['text_muted']} font-light leading-relaxed max-w-2xl mx-auto">{sub}</p>
                        <div class="flex flex-col sm:flex-row gap-4 justify-center pt-6">
                            {_gradient_btn(theme, cta, "#contact", "text-base px-10 py-5 rounded-full shadow-2xl")}
                            {_ghost_btn(theme, "Discover More ↓", "#features", "text-base px-10 py-5 rounded-full")}
                        </div>
                    </div>
                </div>
            </section>"""
        except Exception as e:
            logger.error(f"centered_spotlight hero error: {e}")
            return f"<section id='hero' class='{theme['bg']} py-32'><h1 class='{theme['text']} text-5xl font-bold text-center'>Welcome</h1></section>"

    @staticmethod
    def editorial_large(theme: Dict, data: Dict, images: List[str]) -> str:
        img = images[0] if images else ""
        h1 = data.get("hero", {}).get("h1", "Premium Solution")
        sub = data.get("hero", {}).get("sub", "Built for excellence")
        cta = data.get("hero", {}).get("cta", "Start Now")
        words = h1.split()
        mid = max(1, len(words) // 2)
        line1 = " ".join(words[:mid])
        line2 = " ".join(words[mid:])
        try:
            return f"""
            <section id="hero" class="relative {theme['bg']} overflow-hidden pt-28 md:pt-36 pb-16 md:pb-24">
                <div class="container mx-auto {PADDING_CONTAINER}">
                    <!-- Big editorial headline -->
                    <div class="mb-10">
                        <h1 class="font-black tracking-tighter leading-[1.02] text-[clamp(3rem,7vw,6.5rem)] {theme['text']}">
                            <span class="block">{line1}</span>
                            <span class="block bg-gradient-to-r {theme['grad_text']} bg-clip-text text-transparent">{line2}</span>
                        </h1>
                    </div>
                    <!-- Image + copy side-by-side -->
                    <div class="grid lg:grid-cols-5 gap-10 xl:gap-16 items-end">
                        <div class="lg:col-span-3 h-[380px] md:h-[480px] overflow-hidden rounded-2xl relative shadow-2xl">
                            <img src="{img}" alt="hero" class="w-full h-full object-cover" loading="eager" />
                            <div class="absolute inset-0 bg-gradient-to-t from-black/30 to-transparent"></div>
                        </div>
                        <div class="lg:col-span-2 space-y-7 pb-4">
                            <p class="text-base md:text-lg {theme['text_muted']} leading-relaxed">{sub}</p>
                            {_gradient_btn(theme, f"{cta} →", "#contact", "text-base")}
                            <div class="pt-6 border-t {theme['border']}">
                                <p class="text-xs {theme['text_light']} uppercase tracking-widest mb-2">Trusted by</p>
                                <p class="text-2xl font-black {theme['stat_color']}">2,400+ businesses</p>
                            </div>
                        </div>
                    </div>
                </div>
            </section>"""
        except Exception as e:
            logger.error(f"editorial_large hero error: {e}")
            return f"<section id='hero' class='{theme['bg']} py-32'><h1 class='{theme['text']} text-5xl font-bold text-center'>Welcome</h1></section>"

    @staticmethod
    def stats_hero(theme: Dict, data: Dict, images: List[str]) -> str:
        img = images[0] if images else ""
        h1 = data.get("hero", {}).get("h1", "Premium Solution")
        sub = data.get("hero", {}).get("sub", "Built for excellence")
        cta = data.get("hero", {}).get("cta", "Request Demo")
        try:
            return f"""
            <section id="hero" class="relative {theme['bg']} overflow-hidden pt-32 md:pt-44 pb-20 md:pb-28">
                <!-- Muted background image -->
                <div class="absolute top-0 right-0 w-1/2 h-full pointer-events-none select-none overflow-hidden">
                    <img src="{img}" alt="" class="w-full h-full object-cover {'opacity-[0.08]' if theme['mode'] == 'light' else 'opacity-[0.12]'}" loading="eager" />
                    <div class="absolute inset-0 bg-gradient-to-r {theme['bg']} via-transparent to-transparent opacity-80"></div>
                </div>
                <!-- Glow -->
                <div class="absolute top-1/2 right-1/4 w-96 h-96 bg-gradient-to-r {theme['grad']} opacity-[0.05] blur-[100px] rounded-full pointer-events-none"></div>

                <div class="container mx-auto {PADDING_CONTAINER} relative z-10">
                    <div class="max-w-3xl space-y-8">
                        <h1 class="{HEADING_HERO_ALT} {theme['text']}">{h1}</h1>
                        <p class="text-lg md:text-xl {theme['text_muted']} leading-relaxed max-w-xl">{sub}</p>
                        <div class="flex flex-wrap gap-4 pt-2">
                            {_gradient_btn(theme, cta, "#contact", "text-base")}
                            {_ghost_btn(theme, "See our work →", "#features", "text-base")}
                        </div>
                    </div>

                    <!-- Stats bar -->
                    <div class="grid grid-cols-2 md:grid-cols-4 gap-6 mt-16 md:mt-20 pt-10 border-t {theme['border']}">
                        <div class="space-y-1">
                            <p class="text-4xl md:text-5xl font-black {theme['stat_color']}">98%</p>
                            <p class="text-sm {theme['text_muted']}">Client satisfaction</p>
                        </div>
                        <div class="space-y-1">
                            <p class="text-4xl md:text-5xl font-black {theme['stat_color']}">2.4k+</p>
                            <p class="text-sm {theme['text_muted']}">Active clients</p>
                        </div>
                        <div class="space-y-1">
                            <p class="text-4xl md:text-5xl font-black {theme['stat_color']}">15yr</p>
                            <p class="text-sm {theme['text_muted']}">Industry experience</p>
                        </div>
                        <div class="space-y-1">
                            <p class="text-4xl md:text-5xl font-black {theme['stat_color']}">24/7</p>
                            <p class="text-sm {theme['text_muted']}">Expert support</p>
                        </div>
                    </div>
                </div>
            </section>"""
        except Exception as e:
            logger.error(f"stats_hero error: {e}")
            return f"<section id='hero' class='{theme['bg']} py-32'><h1 class='{theme['text']} text-5xl font-bold text-center'>Welcome</h1></section>"


# ============================================================================
# FEATURE VARIANTS
# ============================================================================

class FeatureVariant:

    @staticmethod
    def cards_grid(theme: Dict, features: List[Dict], images: List[str]) -> str:
        items = "".join([f"""
        <div class="{theme['glass']} border {theme['border']} p-8 rounded-2xl {HOVER_LIFT} flex flex-col">
            <div class="w-12 h-12 mb-5 rounded-xl bg-gradient-to-br {theme['grad']} flex items-center justify-center text-xl shadow-md shrink-0">
                {feat.get('icon', '✨')}
            </div>
            <h3 class="{HEADING_CARD} {theme['text']} mb-3">{feat.get('title', 'Feature')}</h3>
            <p class="{theme['text_muted']} text-sm leading-relaxed flex-grow">{feat.get('description', '')}</p>
        </div>""" for feat in (features or [])])
        try:
            return f"""
            <section id="features" class="{theme['bg_alt']} {PADDING_SECTION}">
                <div class="container mx-auto {PADDING_CONTAINER}">
                    <div class="text-center mb-14 space-y-3">
                        {_section_label(theme, "What we offer")}
                        {_section_heading(theme, "Powerful Features", "Everything you need, nothing you don't.")}
                    </div>
                    <div class="grid sm:grid-cols-2 lg:grid-cols-3 gap-6">{items}</div>
                </div>
            </section>"""
        except Exception as e:
            logger.error(f"cards_grid error: {e}")
            return f"<section id='features' class='{theme['bg_alt']} py-20'><h2 class='text-center text-4xl font-bold {theme['text']}'>Features</h2></section>"

    @staticmethod
    def alternating_blocks(theme: Dict, features: List[Dict], images: List[str]) -> str:
        blocks = []
        for i, feat in enumerate(features or []):
            img_url = images[i % len(images)] if images else ""
            # Alternate layout: even = image right, odd = image left
            copy_order = "lg:order-1" if i % 2 == 0 else "lg:order-2"
            img_order  = "lg:order-2" if i % 2 == 0 else "lg:order-1"
            blocks.append(f"""
            <div class="grid lg:grid-cols-2 gap-12 xl:gap-20 items-center">
                <div class="space-y-6 {copy_order}">
                    <div class="w-14 h-14 rounded-2xl bg-gradient-to-br {theme['grad']} flex items-center justify-center text-2xl shadow-lg">
                        {feat.get('icon', '✨')}
                    </div>
                    <h3 class="{HEADING_FEATURE} {theme['text']}">{feat.get('title', 'Feature')}</h3>
                    <p class="text-base md:text-lg {theme['text_muted']} leading-relaxed">{feat.get('description', '')}</p>
                    <a href="#contact" class="inline-flex items-center gap-2 text-sm font-semibold {theme['stat_color']} {HOVER_GLOW}">
                        Learn more <span>→</span>
                    </a>
                </div>
                <div class="h-72 md:h-[360px] rounded-2xl overflow-hidden relative shadow-xl {img_order}">
                    <img src="{img_url}" alt="{feat.get('title', '')}" class="w-full h-full object-cover {HOVER_SCALE}" loading="lazy" />
                    <div class="absolute inset-0 bg-gradient-to-br {theme['grad']} opacity-[0.08]"></div>
                </div>
            </div>""")
        try:
            return f"""
            <section id="features" class="{theme['bg']} {PADDING_SECTION}">
                <div class="container mx-auto {PADDING_CONTAINER}">
                    <div class="text-center mb-20">
                        {_section_label(theme, "How it works")}
                        {_section_heading(theme, "Why It Works")}
                    </div>
                    <div class="space-y-20 md:space-y-28">{"".join(blocks)}</div>
                </div>
            </section>"""
        except Exception as e:
            logger.error(f"alternating_blocks error: {e}")
            return f"<section id='features' class='{theme['bg']} py-20'><h2 class='text-center text-4xl font-bold {theme['text']}'>Features</h2></section>"

    @staticmethod
    def showcase_bento(theme: Dict, features: List[Dict], images: List[str]) -> str:
        feats = (features or [])[:4]
        first = feats[0] if feats else {}
        rest  = feats[1:]
        rest_items = "".join([f"""
        <div class="{theme['glass']} border {theme['border']} p-6 rounded-2xl {HOVER_LIFT} flex flex-col">
            <span class="text-2xl mb-3">{f.get('icon', '✨')}</span>
            <h3 class="text-lg font-bold {theme['text']} mb-2">{f.get('title', 'Feature')}</h3>
            <p class="text-sm {theme['text_muted']} leading-relaxed flex-grow">{f.get('description', '')}</p>
        </div>""" for f in rest])
        try:
            return f"""
            <section id="features" class="{theme['bg_alt']} {PADDING_SECTION}">
                <div class="container mx-auto {PADDING_CONTAINER}">
                    <div class="text-center mb-14">
                        {_section_label(theme, "What sets us apart")}
                        {_section_heading(theme, "Built Different")}
                    </div>
                    <div class="grid lg:grid-cols-3 gap-5">
                        <!-- Large hero feature -->
                        <div class="{theme['glass']} border {theme['border']} p-10 rounded-2xl lg:col-span-2 {HOVER_LIFT} relative overflow-hidden">
                            <div class="absolute top-0 right-0 w-64 h-64 bg-gradient-to-br {theme['grad']} opacity-[0.08] blur-3xl rounded-full pointer-events-none"></div>
                            <span class="text-4xl mb-5 block">{first.get('icon', '✨')}</span>
                            <h3 class="{HEADING_FEATURE} {theme['text']} mb-4">{first.get('title', 'Feature')}</h3>
                            <p class="{theme['text_muted']} leading-relaxed text-base">{first.get('description', '')}</p>
                        </div>
                        <!-- Smaller features stacked -->
                        <div class="space-y-5">{rest_items}</div>
                    </div>
                </div>
            </section>"""
        except Exception as e:
            logger.error(f"showcase_bento error: {e}")
            return f"<section id='features' class='{theme['bg_alt']} py-20'><h2 class='text-center text-4xl font-bold {theme['text']}'>Features</h2></section>"

    @staticmethod
    def icon_list(theme: Dict, features: List[Dict], images: List[str]) -> str:
        items = "".join([f"""
        <div class="flex gap-5 items-start p-6 rounded-xl border {theme['border']} {HOVER_GLOW} transition-all">
            <div class="w-10 h-10 shrink-0 rounded-full bg-gradient-to-br {theme['grad']} flex items-center justify-center text-white font-bold text-sm shadow-md">
                {str(i + 1).zfill(2)}
            </div>
            <div>
                <h3 class="font-bold text-lg {theme['text']} mb-1">{feat.get('title', 'Feature')}</h3>
                <p class="text-sm {theme['text_muted']} leading-relaxed">{feat.get('description', '')}</p>
            </div>
        </div>""" for i, feat in enumerate(features or [])])
        img_url = images[0] if images else ""
        try:
            return f"""
            <section id="features" class="{theme['bg']} {PADDING_SECTION}">
                <div class="container mx-auto {PADDING_CONTAINER}">
                    <div class="grid lg:grid-cols-2 gap-16 xl:gap-24 items-center">
                        <div>
                            {_section_label(theme, "How it works")}
                            <h2 class="{HEADING_SECTION} {theme['text']} mb-10">Built for Real Results</h2>
                            <div class="space-y-3">{items}</div>
                        </div>
                        <div class="h-[500px] rounded-2xl overflow-hidden relative shadow-2xl">
                            <img src="{img_url}" alt="features visual" class="w-full h-full object-cover" loading="lazy" />
                            <div class="absolute inset-0 bg-gradient-to-br {theme['grad']} opacity-[0.06]"></div>
                        </div>
                    </div>
                </div>
            </section>"""
        except Exception as e:
            logger.error(f"icon_list error: {e}")
            return f"<section id='features' class='{theme['bg']} py-20'><h2 class='text-center text-4xl font-bold {theme['text']}'>Features</h2></section>"


# ============================================================================
# PRICING VARIANTS
# ============================================================================

class PricingVariant:

    @staticmethod
    def tiered_cards(theme: Dict, tiers: List[Dict]) -> str:
        def card(tier: Dict) -> str:
            featured = tier.get("featured", False)
            feats_html = "".join([f"""
            <li class="flex items-start gap-2.5 text-sm {theme['text_muted']}">
                <span class="mt-0.5 {theme['check_color']} shrink-0 font-bold">✓</span>
                <span>{f}</span>
            </li>""" for f in (tier.get("features", []) or [])])
            card_base = f"{theme['glass']} rounded-2xl p-8 {HOVER_LIFT} flex flex-col relative overflow-hidden"
            border = f"border-2 border-gradient-to-b {theme['grad']}" if featured else f"border {theme['border']}"
            popular_badge = (
                f'<div class="absolute top-5 right-5 px-3 py-1 bg-gradient-to-r {theme["grad"]} '
                f'text-white text-xs font-bold rounded-full shadow-md">Most Popular</div>'
                if featured else ""
            )
            btn = (
                f'<a href="#contact" class="w-full py-3.5 text-center rounded-xl font-bold bg-gradient-to-r {theme["grad"]} text-white shadow-lg {HOVER_LIFT}">Get Started</a>'
                if featured else
                f'<a href="#contact" class="w-full py-3.5 text-center rounded-xl font-bold {theme["glass"]} {theme["text"]} border {theme["border"]} {HOVER_GLOW}">Get Started</a>'
            )
            glow = f'<div class="absolute top-0 right-0 w-40 h-40 bg-gradient-to-br {theme["grad"]} opacity-[0.08] blur-2xl rounded-full pointer-events-none"></div>' if featured else ""
            return f"""
            <div class="{card_base} {border}">
                {popular_badge}{glow}
                <div class="mb-6">
                    <h3 class="text-lg font-bold {theme['text']} mb-1">{tier.get('name', 'Plan')}</h3>
                    <p class="text-xs {theme['text_light']}">{tier.get('description', '')}</p>
                </div>
                <div class="mb-7">
                    <span class="text-5xl font-black {theme['text']}">{tier.get('price', '$0')}</span>
                    <span class="text-sm {theme['text_muted']}"> /month</span>
                </div>
                <ul class="space-y-3 mb-8 flex-grow">{feats_html}</ul>
                {btn}
            </div>"""

        try:
            cards_html = "".join([card(t) for t in (tiers or [])])
            return f"""
            <section id="pricing" class="{theme['bg_alt']} {PADDING_SECTION}">
                <div class="container mx-auto {PADDING_CONTAINER}">
                    <div class="text-center mb-14">
                        {_section_label(theme, "Pricing")}
                        {_section_heading(theme, "Simple, Honest Pricing", "No hidden fees. Cancel anytime.")}
                    </div>
                    <div class="grid md:grid-cols-3 gap-6 max-w-5xl mx-auto">{cards_html}</div>
                </div>
            </section>"""
        except Exception as e:
            logger.error(f"tiered_cards error: {e}")
            return f"<section id='pricing' class='{theme['bg_alt']} py-20'><h2 class='text-center text-4xl font-bold {theme['text']}'>Pricing</h2></section>"

    @staticmethod
    def two_column_highlight(theme: Dict, tiers: List[Dict]) -> str:
        tiers = tiers or []
        simple = tiers[0] if tiers else {}
        pro    = tiers[1] if len(tiers) > 1 else {}

        def feat_list_ghost(tier: Dict) -> str:
            return "".join([
                f'<li class="flex items-center gap-2 text-sm {theme["text_muted"]}"><span class="{theme["check_color"]}">✓</span> {f}</li>'
                for f in (tier.get("features", []) or [])
            ])

        def feat_list_white(tier: Dict) -> str:
            return "".join([
                f'<li class="flex items-center gap-2 text-sm text-white/80"><span class="text-white/60">✓</span> {f}</li>'
                for f in (tier.get("features", []) or [])
            ])

        try:
            return f"""
            <section id="pricing" class="{theme['bg']} {PADDING_SECTION}">
                <div class="container mx-auto {PADDING_CONTAINER}">
                    <div class="text-center mb-14">
                        {_section_label(theme, "Pricing")}
                        {_section_heading(theme, "Choose Your Plan")}
                    </div>
                    <div class="grid md:grid-cols-2 gap-6 max-w-4xl mx-auto">
                        <!-- Simple plan -->
                        <div class="{theme['glass']} border {theme['border']} p-10 rounded-2xl {HOVER_LIFT}">
                            <h3 class="text-xl font-bold {theme['text']} mb-1">{simple.get('name', 'Starter')}</h3>
                            <p class="text-sm {theme['text_light']} mb-6">{simple.get('description', '')}</p>
                            <p class="text-5xl font-black {theme['text']} mb-8">{simple.get('price', 'Free')}</p>
                            <ul class="space-y-2.5 mb-10">{feat_list_ghost(simple)}</ul>
                            <a href="#contact" class="{theme['glass']} {theme['text']} border {theme['border']} w-full py-3.5 rounded-xl font-bold block text-center {HOVER_GLOW}">Get Started</a>
                        </div>
                        <!-- Featured plan -->
                        <div class="bg-gradient-to-br {theme['grad']} p-10 rounded-2xl text-white relative overflow-hidden {HOVER_LIFT} shadow-2xl">
                            <div class="absolute top-0 right-0 w-40 h-40 bg-white/10 blur-2xl rounded-full pointer-events-none"></div>
                            <span class="inline-block px-3 py-1 bg-white/20 text-white text-xs font-bold rounded-full mb-4">RECOMMENDED</span>
                            <h3 class="text-xl font-bold mb-1">{pro.get('name', 'Pro')}</h3>
                            <p class="text-sm text-white/70 mb-6">{pro.get('description', '')}</p>
                            <p class="text-5xl font-black mb-8">{pro.get('price', '$99')}</p>
                            <ul class="space-y-2.5 mb-10">{feat_list_white(pro)}</ul>
                            <a href="#contact" class="bg-white text-gray-900 w-full py-3.5 rounded-xl font-bold block text-center hover:bg-gray-100 transition">Upgrade Now</a>
                        </div>
                    </div>
                </div>
            </section>"""
        except Exception as e:
            logger.error(f"two_column_highlight error: {e}")
            return f"<section id='pricing' class='{theme['bg']} py-20'><h2 class='text-center text-4xl font-bold {theme['text']}'>Pricing</h2></section>"

    @staticmethod
    def project_based(theme: Dict, tiers: List[Dict]) -> str:
        tiers = tiers or []
        icons = ["🏗️", "🔨", "🏢"]
        cards_html = "".join([f"""
        <div class="{theme['glass']} border {theme['border']} p-8 rounded-2xl {HOVER_LIFT} flex flex-col">
            <div class="text-3xl mb-5">{icons[i % len(icons)]}</div>
            <h3 class="text-xl font-bold {theme['text']} mb-2">{t.get('name', 'Package')}</h3>
            <p class="text-sm {theme['text_muted']} mb-5 leading-relaxed">{t.get('description', '')}</p>
            <div class="mb-5">
                <span class="text-2xl font-black {theme['stat_color']}">{t.get('price', 'Get a Quote')}</span>
            </div>
            <ul class="space-y-2.5 mb-8 flex-grow">
                {"".join([f'<li class=\"flex items-start gap-2 text-sm {theme[\"text_muted\"]}\"><span class=\"mt-0.5 {theme[\"check_color\"]} shrink-0 font-bold\">✓</span><span>{f}</span></li>' for f in (t.get('features', []) or [])])}
            </ul>
            <a href="#contact" class="w-full py-3.5 text-center rounded-xl font-semibold border {theme['border']} {theme['text']} {theme['glass']} {HOVER_GLOW} block">
                Request a Quote →
            </a>
        </div>""" for i, t in enumerate(tiers)])

        try:
            return f"""
            <section id="pricing" class="{theme['bg_alt']} {PADDING_SECTION}">
                <div class="container mx-auto {PADDING_CONTAINER}">
                    <div class="text-center mb-14">
                        {_section_label(theme, "Our Services")}
                        {_section_heading(theme, "What We Offer", "Every project is unique. Contact us for a custom quote tailored to your needs.")}
                    </div>
                    <div class="grid md:grid-cols-3 gap-6 max-w-5xl mx-auto mb-12">{cards_html}</div>
                    <!-- CTA strip -->
                    <div class="{theme['glass']} border {theme['border_strong']} rounded-2xl p-8 md:p-10 max-w-2xl mx-auto text-center">
                        <p class="text-lg font-semibold {theme['text']} mb-2">Not sure which service fits?</p>
                        <p class="text-sm {theme['text_muted']} mb-6 leading-relaxed">We'll assess your project and provide a transparent, no-obligation estimate.</p>
                        {_gradient_btn(theme, "Request a Free Estimate", "#contact")}
                    </div>
                </div>
            </section>"""
        except Exception as e:
            logger.error(f"project_based pricing error: {e}")
            return f"<section id='pricing' class='{theme['bg_alt']} py-20'><h2 class='text-center text-4xl font-bold {theme['text']}'>Services</h2></section>"

    @staticmethod
    def services_list(theme: Dict, tiers: List[Dict]) -> str:
        tiers = tiers or []
        rows = "".join([f"""
        <div class="grid md:grid-cols-3 gap-6 items-center py-8">
            <div>
                <h3 class="text-lg font-bold {theme['text']}">{t.get('name', 'Service')}</h3>
                <p class="text-sm {theme['text_muted']} mt-1 leading-relaxed">{t.get('description', '')}</p>
            </div>
            <ul class="space-y-1.5">
                {"".join([f'<li class=\"flex items-center gap-2 text-sm {theme[\"text_muted\"]}\"><span class=\"{theme[\"check_color\"]} font-bold\">✓</span>{f}</li>' for f in (t.get('features', []) or [])[:4]])}
            </ul>
            <div class="md:text-right">
                <span class="text-lg font-black {theme['stat_color']} block mb-3">{t.get('price', 'Custom')}</span>
                <a href="#contact" class="inline-block px-6 py-3 bg-gradient-to-r {theme['grad']} text-white rounded-lg font-semibold text-sm {HOVER_LIFT}">
                    Book Consultation
                </a>
            </div>
        </div>""" for t in tiers])

        try:
            return f"""
            <section id="pricing" class="{theme['bg']} {PADDING_SECTION}">
                <div class="container mx-auto {PADDING_CONTAINER}">
                    <div class="mb-12">
                        {_section_label(theme, "Our Services")}
                        <h2 class="{HEADING_SECTION} {theme['text']}">How We Can Help</h2>
                        <p class="text-lg {theme['text_muted']} mt-4 max-w-xl leading-relaxed">All engagements begin with a complimentary consultation to understand your needs.</p>
                    </div>
                    <div class="divide-y {theme['divider']}">{rows}</div>
                    <div class="mt-12 text-center">
                        {_gradient_btn(theme, "Schedule Your Free Consultation", "#contact", "text-base px-10 py-5")}
                    </div>
                </div>
            </section>"""
        except Exception as e:
            logger.error(f"services_list pricing error: {e}")
            return f"<section id='pricing' class='{theme['bg']} py-20'><h2 class='text-center text-4xl font-bold {theme['text']}'>Services</h2></section>"


# ============================================================================
# MASTER ARCHITECT
# ============================================================================

class MasterArchitect:

    def __init__(self, business_name: str, prompt: str, version: int = 1):
        raw_name   = (business_name or "").strip()
        raw_prompt = (prompt or "").strip()

        clean_name, clean_prompt = extract_business_name(raw_name, raw_prompt)
        self.industry = detect_industry(clean_prompt or raw_prompt)

        if not clean_name:
            clean_name = derive_name_from_prompt(clean_prompt, self.industry)
            logger.info(f"No explicit business name found; derived: '{clean_name}'")

        self.name    = clean_name
        self.prompt  = clean_prompt
        self.version = version
        self.seed    = f"{self.name}::{self.prompt}"
        self.theme   = select_theme(self.industry, seed=self.seed)
        self.data:   Dict = {}
        self.images: List[str] = []
        logger.info(f"MasterArchitect: name='{self.name}', industry={self.industry}, theme={self.theme['id']}")

    # ── AI payload ──────────────────────────────────────────────────────────

    def get_ai_payload(self) -> Dict:
        project_based_industries = {"construction", "logistics", "automotive", "events"}
        services_industries      = {"legal", "nonprofit"}

        if self.industry in project_based_industries:
            pricing_instruction = """  "pricing": [
    {"name": "Small Projects",      "price": "From $2,500",  "description": "Residential or small-scope work.", "features": ["Free on-site estimate", "Licensed & insured crew", "Quality materials", "Timeline guarantee", "Follow-up inspection"], "featured": false},
    {"name": "Commercial Work",     "price": "From $15,000", "description": "Mid-to-large commercial scopes.",  "features": ["Dedicated project manager", "Full compliance documentation", "Progress reporting", "Safety-first practices", "Warranty included"], "featured": true},
    {"name": "Enterprise Contracts","price": "Get a Quote",  "description": "Major infrastructure projects.",   "features": ["Multi-site capability", "Custom SLA", "Procurement support", "Executive liaison", "Post-project maintenance"], "featured": false}
  ],"""
        elif self.industry in services_industries:
            pricing_instruction = """  "pricing": [
    {"name": "Initial Consultation","price": "Complimentary","description": "30-minute case review with no obligation.", "features": ["Case assessment", "Legal options overview", "Fee structure discussion", "Written summary", "Confidential"], "featured": false},
    {"name": "Standard Engagement", "price": "From $300/hr", "description": "Ongoing legal support as required.",       "features": ["Experienced attorneys", "Flexible hours", "Detailed billing", "Case strategy", "Court representation"], "featured": true},
    {"name": "Retainer Agreement",  "price": "Custom",       "description": "Dedicated counsel for your organisation.", "features": ["Priority access", "Monthly strategy sessions", "Document review", "Risk management", "Flat-rate predictability"], "featured": false}
  ],"""
        else:
            pricing_instruction = """  "pricing": [
    {"name": "Starter",    "price": "$29",    "description": "For individuals getting started.", "features": ["Core feature set", "Up to 5 projects", "Email support", "API access", "Monthly reporting"], "featured": false},
    {"name": "Pro",        "price": "$99",    "description": "For growing teams.",               "features": ["Everything in Starter", "Unlimited projects", "Priority support", "Advanced analytics", "Custom integrations"], "featured": true},
    {"name": "Enterprise", "price": "Custom", "description": "For large organisations.",         "features": ["Everything in Pro", "Dedicated account manager", "SLA guarantee", "Custom contracts", "On-premise option"], "featured": false}
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
- Do NOT mention any colours in your text output

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
  "cta_text": "closing CTA headline appropriate for this industry"
}}"""

        if not AI_AVAILABLE:
            logger.warning("AI client unavailable; using fallback")
            return self._get_fallback_payload()
        try:
            res = chat_completion(system=system_msg, user=user_msg, temperature=0.75)
            cleaned = res.strip().replace("```json", "").replace("```", "").strip()
            payload = json.loads(cleaned)
            payload = self._sanitize_ai_payload(payload)
            logger.info("AI payload generated successfully")
            return payload
        except Exception as e:
            logger.error(f"AI payload error: {e}")
            return self._get_fallback_payload()

    def _sanitize_ai_payload(self, payload: Dict) -> Dict:
        """Remove colour mentions and other theme leaks from AI-generated text."""
        color_substitutions = {
            "purple": "distinctive", "violet": "distinctive", "fuchsia": "vibrant",
            "rose": "bold", "pink": "elegant", "blue": "professional",
            "cyan": "modern", "indigo": "authoritative", "amber": "warm",
            "orange": "energetic", "emerald": "fresh", "teal": "clean",
            "green": "sustainable", "slate": "refined", "gray": "neutral",
            "grey": "neutral",
        }

        def strip_colors(text: str) -> str:
            if not isinstance(text, str):
                return text
            text_lower = text.lower()
            for color, replacement in color_substitutions.items():
                for suffix in [" brand", " logo", " website", " design", " palette", " scheme", " theme"]:
                    bad = color + suffix
                    if bad in text_lower:
                        # Find case-insensitive and replace
                        import re
                        text = re.sub(re.escape(bad), f"{replacement}{suffix}", text, flags=re.IGNORECASE)
            return text

        def sanitize_dict(d: Any) -> Any:
            if isinstance(d, str):
                return strip_colors(d)
            if isinstance(d, dict):
                return {k: sanitize_dict(v) for k, v in d.items()}
            if isinstance(d, list):
                return [sanitize_dict(item) for item in d]
            return d

        # Remove unsplash_keywords from AI payload — we derive images from industry directly
        payload.pop("unsplash_keywords", None)

        return sanitize_dict(payload)

    def _get_fallback_payload(self) -> Dict:
        """Industry-aware fallback when AI is unavailable."""
        if self.industry == "construction":
            return {
                "nav": ["Services", "Projects", "About", "Contact"],
                "hero": {"h1": "Built Right, On Time", "sub": "Quality construction and renovation with transparent pricing and guaranteed workmanship.", "cta": "Request a Quote"},
                "tagline": "Built to last.",
                "brand_voice": "professional",
                "features": [
                    {"title": "Licensed & Fully Insured", "description": "Every project is covered by comprehensive liability and workers' compensation insurance. You're protected.", "icon": "🛡️"},
                    {"title": "On-Time, On-Budget Delivery", "description": "We provide detailed project timelines and stick to them. No surprise invoices, ever.", "icon": "📋"},
                    {"title": "Skilled Trades Under One Roof", "description": "From groundwork to finishing, our certified tradespeople handle every phase of your project.", "icon": "🔨"},
                ],
                "pricing": [
                    {"name": "Residential", "price": "From $2,500", "description": "Home renovations and repairs.", "features": ["Free on-site estimate", "Kitchen & bath remodels", "Roofing & siding", "Flooring & painting", "Follow-up inspection"], "featured": False},
                    {"name": "Commercial", "price": "From $15,000", "description": "Business construction projects.", "features": ["Dedicated project manager", "Office & retail fit-outs", "Compliance documentation", "Progress reporting", "Warranty included"], "featured": True},
                    {"name": "Emergency", "price": "24/7 Available", "description": "Urgent repair services.", "features": ["Storm & water damage", "Structural emergencies", "Same-day response", "Insurance billing", "Temporary securing"], "featured": False},
                ],
                "testimonials": [
                    {"name": "Michael Torres", "role": "Homeowner", "company": "Brooklyn, NY", "quote": "Complete kitchen renovation done on schedule and under budget. The crew was professional from day one."},
                    {"name": "Lisa Chen", "role": "Property Manager", "company": "Manhattan Properties", "quote": "We've used them across six properties for three years. Consistent, reliable, and always honest about costs."},
                ],
                "faq": [
                    {"q": "Are you licensed and insured?", "a": "Yes — fully licensed with comprehensive liability and workers' compensation insurance on every project."},
                    {"q": "Do you offer free estimates?", "a": "Absolutely. We provide detailed, no-obligation estimates after an on-site assessment."},
                    {"q": "How do you handle project timelines?", "a": "We provide a written schedule before work begins and update you at each milestone."},
                ],
                "cta_text": "Ready to start your project?",
            }
        if self.industry == "legal":
            return {
                "nav": ["Practice Areas", "Our Team", "Resources", "Contact"],
                "hero": {"h1": "Trusted Counsel. Real Results.", "sub": "Protecting your interests with strategic legal expertise and decades of courtroom experience.", "cta": "Schedule a Consultation"},
                "tagline": "Your advocate.",
                "brand_voice": "professional",
                "features": [
                    {"title": "Experienced Litigators", "description": "Decades of combined courtroom and transactional experience across multiple practice areas.", "icon": "⚖️"},
                    {"title": "Client-First Approach", "description": "We listen before we advise. Your goals shape every strategy we build on your behalf.", "icon": "🤝"},
                    {"title": "Plain-English Guidance", "description": "We explain your legal options clearly so you can make informed decisions with confidence.", "icon": "💬"},
                ],
                "pricing": [
                    {"name": "Free Consultation", "price": "Complimentary", "description": "30-minute case review.", "features": ["Case assessment", "Legal options overview", "Fee structure discussion", "No obligation", "Confidential"], "featured": False},
                    {"name": "Hourly Representation", "price": "From $350/hr", "description": "Flexible legal support.", "features": ["Experienced attorneys", "Detailed billing", "Case strategy sessions", "Court representation", "Document preparation"], "featured": True},
                    {"name": "Retainer Agreement", "price": "Custom", "description": "Ongoing legal partnership.", "features": ["Priority access", "Monthly strategy sessions", "Contract & risk review", "Regulatory compliance", "Predictable costs"], "featured": False},
                ],
                "testimonials": [
                    {"name": "Robert Kim", "role": "CEO", "company": "TechStart Inc.", "quote": "They guided us through a complex acquisition with skill and calm. I'd trust them with any matter."},
                    {"name": "Jennifer Adams", "role": "Private Client", "company": "Chicago, IL", "quote": "After years of frustration, their team resolved my case in four months. Exceptional communication throughout."},
                ],
                "faq": [
                    {"q": "What practice areas do you cover?", "a": "Corporate law, employment disputes, real estate transactions, estate planning, and civil litigation."},
                    {"q": "How does the free consultation work?", "a": "A 30-minute confidential session to assess your situation and explain how we can help."},
                    {"q": "Do you take contingency cases?", "a": "For select personal injury and employment matters, yes. We'll discuss fee arrangements at consultation."},
                ],
                "cta_text": "Ready to protect what matters most?",
            }
        if self.industry in ("restaurant", "food"):
            return {
                "nav": ["Menu", "About", "Catering", "Contact"],
                "hero": {"h1": "Food Made With Purpose", "sub": "Freshly prepared every day with locally sourced ingredients and recipes passed down through generations.", "cta": "View Our Menu"},
                "tagline": "Taste the difference.",
                "brand_voice": "warm",
                "features": [
                    {"title": "Locally Sourced Ingredients", "description": "We partner with regional farms and suppliers to bring you the freshest produce every single day.", "icon": "🥗"},
                    {"title": "Made Fresh Daily", "description": "Nothing is pre-made or frozen. Every dish is prepared in-house from scratch to order.", "icon": "👨‍🍳"},
                    {"title": "Warm, Welcoming Atmosphere", "description": "A dining room designed for lingering — perfect for date nights, family dinners, and celebrations.", "icon": "🏡"},
                ],
                "pricing": [
                    {"name": "Lunch", "price": "$15–$25", "description": "Daily specials & light plates.", "features": ["Soup & salad combos", "Artisan sandwiches", "Fresh-baked bread", "Seasonal specials", "Quick counter service"], "featured": False},
                    {"name": "Dinner", "price": "$28–$48", "description": "Full à la carte menu.", "features": ["Signature entrées", "House-made pasta", "Fresh seafood daily", "Curated wine list", "Seasonal desserts"], "featured": True},
                    {"name": "Catering", "price": "Custom", "description": "Events & private dining.", "features": ["Corporate events", "Family celebrations", "Drop-off or full service", "Custom menus", "Dietary accommodations"], "featured": False},
                ],
                "testimonials": [
                    {"name": "Maria Gonzalez", "role": "Local Resident", "company": "Yelp Elite", "quote": "Best food in the neighbourhood by a mile. The pasta is perfectly cooked and the portions are generous."},
                    {"name": "David Park", "role": "Food Blogger", "company": "NYC Eats", "quote": "A hidden gem. Everything is made with real care and you can taste it in every bite."},
                ],
                "faq": [
                    {"q": "Do you take reservations?", "a": "Yes — we recommend booking for dinner, especially weekends. Walk-ins always welcome for lunch."},
                    {"q": "Can you accommodate dietary restrictions?", "a": "Absolutely. Vegetarian, vegan, and gluten-free options are available on the full menu."},
                    {"q": "Do you offer takeout or delivery?", "a": "Full menu available for takeout. We also partner with major delivery platforms."},
                ],
                "cta_text": "Come taste the difference",
            }
        # Default SaaS-style fallback
        return {
            "nav": ["Features", "Pricing", "FAQ", "Contact"],
            "hero": {"h1": f"Welcome to {self.name}", "sub": "Premium solutions built for your exact needs.", "cta": "Get Started Free"},
            "tagline": "Built for the bold.",
            "brand_voice": "professional",
            "features": [
                {"title": "Speed & Reliability", "description": "Industry-leading uptime with blazing performance. Your operations never stop.", "icon": "⚡"},
                {"title": "Seamless Integration", "description": "Connects with your existing stack in minutes. No developer required.", "icon": "🔗"},
                {"title": "Powerful Analytics", "description": "Real-time insights that surface what matters so you can act faster.", "icon": "📊"},
            ],
            "pricing": [
                {"name": "Starter", "price": "$29", "description": "For individuals getting started.", "features": ["5 projects", "1 GB storage", "Email support", "API access", "Monthly reports"], "featured": False},
                {"name": "Pro", "price": "$99", "description": "For growing teams.", "features": ["Unlimited projects", "50 GB storage", "Priority support", "Advanced analytics", "Custom integrations"], "featured": True},
                {"name": "Enterprise", "price": "Custom", "description": "For large organisations.", "features": ["Everything in Pro", "Dedicated manager", "SLA guarantee", "Custom contracts", "On-premise option"], "featured": False},
            ],
            "testimonials": [
                {"name": "Sarah Chen", "role": "CEO", "company": "NexusCorp", "quote": "Completely transformed our workflow. We reclaimed 20 hours per week across the team."},
                {"name": "Marcus Webb", "role": "CTO", "company": "LaunchpadAI", "quote": "The best platform investment we've made. ROI was measurable within the first month."},
            ],
            "faq": [
                {"q": "How quickly can I get started?", "a": "You'll be fully set up in under 10 minutes with our guided onboarding flow."},
                {"q": "What support do you provide?", "a": "All plans include email support. Pro and Enterprise receive 24/7 priority access."},
                {"q": "Is there a free trial?", "a": "Yes — 14 days free, no credit card required."},
            ],
            "cta_text": f"Ready to take {self.name} to the next level?",
        }

    # ── Variant pickers ──────────────────────────────────────────────────────

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
            "construction": HeroVariant.split_grid,
            "logistics":    HeroVariant.stats_hero,
            "automotive":   HeroVariant.split_grid,
            "events":       HeroVariant.editorial_large,
            "nonprofit":    HeroVariant.centered_spotlight,
            "fitness":      HeroVariant.split_grid,
            "health":       HeroVariant.split_grid,
            "travel":       HeroVariant.centered_spotlight,
            "startup":      HeroVariant.split_grid,
            "ai":           HeroVariant.split_grid,
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
            "fitness":      FeatureVariant.alternating_blocks,
            "travel":       FeatureVariant.alternating_blocks,
            "restaurant":   FeatureVariant.alternating_blocks,
            "saas":         FeatureVariant.cards_grid,
            "ecommerce":    FeatureVariant.cards_grid,
            "developer":    FeatureVariant.cards_grid,
            "construction": FeatureVariant.alternating_blocks,
            "logistics":    FeatureVariant.icon_list,
            "automotive":   FeatureVariant.alternating_blocks,
            "events":       FeatureVariant.showcase_bento,
            "nonprofit":    FeatureVariant.alternating_blocks,
            "startup":      FeatureVariant.cards_grid,
            "ai":           FeatureVariant.cards_grid,
        }
        default_pool = [FeatureVariant.cards_grid, FeatureVariant.showcase_bento, FeatureVariant.alternating_blocks]
        if self.industry in mapping:
            return mapping[self.industry]
        idx = int(hashlib.md5((self.seed + "features").encode()).hexdigest(), 16) % len(default_pool)
        return default_pool[idx]

    def _pick_pricing_variant(self) -> Callable:
        project_industries  = {"construction", "logistics", "automotive", "events"}
        services_industries = {"legal", "nonprofit"}
        premium_industries  = {"luxury", "agency", "beauty", "finance", "real_estate"}
        if self.industry in project_industries:
            return PricingVariant.project_based
        if self.industry in services_industries:
            return PricingVariant.services_list
        if self.industry in premium_industries:
            return PricingVariant.two_column_highlight
        return PricingVariant.tiered_cards

    # ── Section renderers ────────────────────────────────────────────────────

    def render_nav(self) -> str:
        nav_items = "".join([
            f'<li><a href="#{link.lower().replace(" ", "")}" '
            f'class="{self.theme["text_muted"]} hover:opacity-80 transition-opacity duration-200 text-sm font-medium">'
            f'{link}</a></li>'
            for link in (self.data.get("nav", []) or [])
        ])
        cta = self.data.get("hero", {}).get("cta", "Get Started")
        try:
            return f"""
            <nav class="fixed top-0 w-full z-50 {self.theme['nav_bg']} backdrop-blur-xl">
                <div class="container mx-auto {PADDING_CONTAINER} py-4 flex justify-between items-center">
                    <a href="#" class="text-xl font-black tracking-tight {self.theme['text']}">{self.name}</a>
                    <ul class="hidden md:flex items-center gap-8">{nav_items}</ul>
                    {_gradient_btn(self.theme, cta, "#contact", "text-sm px-5 py-2.5 rounded-lg")}
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

    def render_trust_band(self) -> str:
        industry_trust = {
            "finance":      ["SOC 2 Certified", "256-bit Encryption", "GDPR Compliant", "FINRA Member", "ISO 27001"],
            "health":       ["HIPAA Compliant", "FDA Registered", "ISO 13485", "ADA Accessible", "HITRUST CSF"],
            "saas":         ["SOC 2 Type II", "99.99% Uptime SLA", "GDPR Ready", "24/7 Monitoring", "Zero-downtime deploys"],
            "ecommerce":    ["PCI-DSS Compliant", "SSL Secured", "Money-back Guarantee", "4.9★ Rated", "Secure Checkout"],
            "education":    ["FERPA Compliant", "COPPA Safe", "Accredited Provider", "ADA Accessible", "Secure Platform"],
            "developer":    ["SOC 2 Type II", "Open Source Core", "99.9% Uptime", "GDPR Ready", "Enterprise SLA"],
            "restaurant":   ["Health Inspected ✓", "Locally Sourced", "5-Star Rated", "Est. 2018", "Award Winning"],
            "construction": ["Licensed & Insured", "Bonded Contractor", "OSHA Compliant", "15yr Track Record", "Satisfaction Guaranteed"],
            "legal":        ["State Bar Certified", "ABA Members", "Client Confidential", "Peer Rated AV®", "15+ Years Experience"],
            "logistics":    ["ISO 9001 Certified", "DOT Compliant", "Insured Freight", "Real-time Tracking", "99.7% On-time"],
            "automotive":   ["ASE Certified", "Licensed & Bonded", "OEM Parts", "Warranty Included", "BBB Accredited"],
            "beauty":       ["Licensed Professionals", "Health & Safety Certified", "Award Winning", "Premium Products", "5-Star Rated"],
            "fitness":      ["Certified Trainers", "Safety Inspected", "Insurance Covered", "Results Guaranteed", "5-Star Rated"],
        }
        badges = industry_trust.get(
            self.industry,
            ["ISO 9001", "SOC 2", "GDPR Compliant", "256-bit SSL", "Award Winner 2024"]
        )
        badge_html = "".join([
            f'<span class="px-4 py-1.5 rounded-full text-xs font-semibold {self.theme["badge_style"]}">{b}</span>'
            for b in badges
        ])
        try:
            return f"""
            <div class="{self.theme['bg_alt']} border-y {self.theme['border']} py-6">
                <div class="container mx-auto {PADDING_CONTAINER}">
                    <div class="flex flex-wrap items-center justify-center gap-3">
                        <span class="text-xs {self.theme['text_light']} uppercase tracking-widest mr-2">Verified &amp; Trusted</span>
                        {badge_html}
                    </div>
                </div>
            </div>"""
        except Exception as e:
            logger.error(f"trust band error: {e}")
            return ""

    def render_features(self) -> str:
        try:
            return self._pick_feature_variant()(self.theme, self.data.get("features", []), self.images)
        except Exception as e:
            logger.error(f"features error: {e}")
            return f"<section id='features' class='{self.theme['bg_alt']} py-20'><h2 class='{self.theme['text']} text-4xl font-bold text-center'>Features</h2></section>"

    def render_pricing(self) -> str:
        try:
            return self._pick_pricing_variant()(self.theme, self.data.get("pricing", []))
        except Exception as e:
            logger.error(f"pricing error: {e}")
            return f"<section id='pricing' class='{self.theme['bg_alt']} py-20'><h2 class='{self.theme['text']} text-4xl font-bold text-center'>Pricing</h2></section>"

    def render_testimonials(self) -> str:
        testimonials = self.data.get("testimonials", [])
        if not testimonials:
            return ""
        cards = "".join([f"""
        <div class="{self.theme['glass']} border {self.theme['border']} p-8 rounded-2xl {HOVER_LIFT} flex flex-col">
            <div class="flex gap-0.5 mb-5">
                {''.join(['<span class="text-amber-400 text-sm">★</span>' for _ in range(5)])}
            </div>
            <p class="{self.theme['text_muted']} text-base italic leading-relaxed mb-6 flex-grow">
                "{t.get('quote', '')}"
            </p>
            <div class="flex items-center gap-3 pt-5 border-t {self.theme['border']}">
                <div class="w-10 h-10 rounded-full bg-gradient-to-br {self.theme['grad']} flex items-center justify-center text-white font-bold text-sm shrink-0">
                    {(t.get('name', 'C') or 'C')[0].upper()}
                </div>
                <div>
                    <p class="{self.theme['text']} font-bold text-sm">{t.get('name', 'Client')}</p>
                    <p class="{self.theme['text_light']} text-xs">{t.get('role', '')} · {t.get('company', '')}</p>
                </div>
            </div>
        </div>""" for t in testimonials])
        try:
            return f"""
            <section id="testimonials" class="{self.theme['bg_section']} {PADDING_SECTION}">
                <div class="container mx-auto {PADDING_CONTAINER}">
                    <div class="text-center mb-12">
                        {_section_label(self.theme, "Testimonials")}
                        {_section_heading(self.theme, "Trusted by Leaders")}
                    </div>
                    <div class="grid md:grid-cols-2 gap-6 max-w-4xl mx-auto">{cards}</div>
                </div>
            </section>"""
        except Exception as e:
            logger.error(f"testimonials error: {e}")
            return ""

    def render_faq(self) -> str:
        faqs = self.data.get("faq", [])
        if not faqs:
            return ""
        items = "".join([f"""
        <details class="{self.theme['glass']} border {self.theme['border']} rounded-xl overflow-hidden group">
            <summary class="flex justify-between items-center p-6 cursor-pointer font-semibold {self.theme['text']} list-none hover:opacity-80 transition-opacity">
                <span>{faq.get('q', '')}</span>
                <span class="ml-6 shrink-0 w-6 h-6 rounded-full border {self.theme['border_strong']} flex items-center justify-center text-xs {self.theme['text_muted']} group-open:rotate-45 transition-transform duration-300">+</span>
            </summary>
            <div class="px-6 pb-6 border-t {self.theme['border']} pt-4">
                <p class="{self.theme['text_muted']} text-sm leading-relaxed">{faq.get('a', '')}</p>
            </div>
        </details>""" for faq in faqs])
        try:
            return f"""
            <section id="faq" class="{self.theme['bg_alt']} {PADDING_SECTION}">
                <div class="container mx-auto {PADDING_CONTAINER}">
                    <div class="text-center mb-12">
                        {_section_label(self.theme, "FAQ")}
                        {_section_heading(self.theme, "Common Questions")}
                    </div>
                    <div class="space-y-3 max-w-2xl mx-auto">{items}</div>
                </div>
            </section>"""
        except Exception as e:
            logger.error(f"faq error: {e}")
            return ""

    def render_cta_section(self) -> str:
        cta_text = self.data.get("cta_text", "Ready to get started?")
        sub      = self.data.get("hero", {}).get("sub", "")
        img_url  = self.images[2] if len(self.images) > 2 else self.images[0] if self.images else ""
        cta_label = self.data.get("hero", {}).get("cta", "Get Started")
        try:
            return f"""
            <section id="contact" class="relative {self.theme['bg']} {PADDING_SECTION} overflow-hidden">
                <!-- Background image overlay -->
                <div class="absolute inset-0 pointer-events-none">
                    <img src="{img_url}" alt="" class="w-full h-full object-cover {'opacity-[0.05]' if self.theme['mode'] == 'light' else 'opacity-[0.08]'}" loading="lazy" />
                    <div class="absolute inset-0 {'bg-white/80' if self.theme['mode'] == 'light' else 'bg-black/70'}"></div>
                </div>
                <!-- Gradient tint -->
                <div class="absolute inset-0 bg-gradient-to-br {self.theme['grad_cta_bg']} pointer-events-none"></div>
                <!-- Glow -->
                <div class="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-gradient-to-r {self.theme['grad']} opacity-[0.07] blur-[100px] rounded-full pointer-events-none"></div>

                <div class="container mx-auto {PADDING_CONTAINER} relative z-10 text-center">
                    <div class="max-w-3xl mx-auto space-y-6">
                        <h2 class="{HEADING_SECTION} {self.theme['text']}">{cta_text}</h2>
                        {f'<p class="text-lg {self.theme[\"text_muted\"]} leading-relaxed">{sub}</p>' if sub else ''}
                        <div class="flex flex-col sm:flex-row gap-4 justify-center pt-4">
                            {_gradient_btn(self.theme, cta_label, f"mailto:hello@{self.name.lower().replace(' ', '')}.com", "text-base px-10 py-5")}
                            <a href="tel:+10000000000" class="{self.theme['glass']} border {self.theme['border']} {self.theme['text']} px-10 py-5 rounded-xl font-bold {HOVER_GLOW} text-base">
                                📞 Call Us
                            </a>
                        </div>
                    </div>
                </div>
            </section>"""
        except Exception as e:
            logger.error(f"cta error: {e}")
            return f"<section id='contact' class='{self.theme['bg']} py-24 text-center'><h2 class='{self.theme['text']} text-4xl font-bold'>Get In Touch</h2></section>"

    def render_footer(self) -> str:
        nav_links = "".join([
            f'<li><a href="#{link.lower().replace(" ", "")}" class="{self.theme["text_muted"]} hover:opacity-70 text-sm transition-opacity">{link}</a></li>'
            for link in (self.data.get("nav", []) or [])
        ])
        tagline = self.data.get("tagline", "")
        sub     = self.data.get("hero", {}).get("sub", "Premium solutions for modern businesses.")
        try:
            return f"""
            <footer class="{self.theme['bg_alt']} border-t {self.theme['border']} pt-16 pb-10">
                <div class="container mx-auto {PADDING_CONTAINER}">
                    <div class="grid md:grid-cols-4 gap-10 mb-12">
                        <!-- Brand -->
                        <div class="md:col-span-2">
                            <h3 class="font-black text-xl {self.theme['text']} mb-3">{self.name}</h3>
                            <p class="{self.theme['text_muted']} text-sm max-w-xs leading-relaxed">{sub}</p>
                            {f'<p class="text-xs {self.theme["text_light"]} mt-4 italic">{tagline}</p>' if tagline else ''}
                        </div>
                        <!-- Navigation -->
                        <div>
                            <h4 class="font-bold text-xs {self.theme['text']} mb-4 uppercase tracking-widest">Navigation</h4>
                            <ul class="space-y-2.5">{nav_links}</ul>
                        </div>
                        <!-- Legal -->
                        <div>
                            <h4 class="font-bold text-xs {self.theme['text']} mb-4 uppercase tracking-widest">Legal</h4>
                            <ul class="space-y-2.5 text-sm">
                                <li><a href="#" class="{self.theme['text_muted']} hover:opacity-70 transition-opacity">Privacy Policy</a></li>
                                <li><a href="#" class="{self.theme['text_muted']} hover:opacity-70 transition-opacity">Terms of Service</a></li>
                                <li><a href="mailto:hello@example.com" class="{self.theme['text_muted']} hover:opacity-70 transition-opacity">Contact Us</a></li>
                            </ul>
                        </div>
                    </div>
                    <!-- Bottom bar -->
                    <div class="border-t {self.theme['border']} pt-6 flex flex-col md:flex-row justify-between items-center gap-3">
                        <p class="{self.theme['text_light']} text-xs">&copy; 2026 {self.name}. All rights reserved.</p>
                        <p class="{self.theme['text_light']} text-xs">v{self.version}</p>
                    </div>
                </div>
            </footer>"""
        except Exception as e:
            logger.error(f"footer error: {e}")
            return f"<footer class='py-8 text-center text-sm text-gray-500'>&copy; 2026 {self.name}</footer>"

    # ── Main build ───────────────────────────────────────────────────────────

    def build(self) -> Dict[str, Any]:
        try:
            self.data   = self.get_ai_payload()
            # Images are now driven 100% by industry — no AI keyword dependency
            self.images = _get_industry_image_set(self.industry, count=8)

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
                    from { opacity: 0; transform: translateY(20px); }
                    to   { opacity: 1; transform: translateY(0); }
                }
                .container { animation: fadeInUp 0.7s ease-out both; }
                details > summary::-webkit-details-marker { display: none; }
                html { scroll-behavior: smooth; }

                /* Intersection observer fade-in via CSS animation-play-state */
                @media (prefers-reduced-motion: no-preference) {
                    section { view-timeline: --section block; }
                }
            """

            html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{self.name}</title>
    <meta name="description" content="{self.data.get('hero', {}).get('sub', '')}">
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link rel="stylesheet" href="{self.theme['font_url']}">
    <style>
        *, *::before, *::after {{ box-sizing: border-box; margin: 0; }}
        body {{ font-family: {self.theme['fonts']}; -webkit-font-smoothing: antialiased; }}
        img {{ display: block; max-width: 100%; }}
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
                    "business_name":    self.name,
                    "industry":         self.industry,
                    "theme":            self.theme["id"],
                    "version":          self.version,
                    "hero_variant":     self._pick_hero_variant().__name__,
                    "feature_variant":  self._pick_feature_variant().__name__,
                    "pricing_variant":  self._pick_pricing_variant().__name__,
                    "status":           "success",
                }
            }
        except Exception as e:
            logger.error(f"Build error: {e}\n{traceback.format_exc()}")
            return {
                "html": f"<html><body style='font-family:sans-serif;padding:2rem'><h1>Build Error</h1><pre>{e}</pre></body></html>",
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
        version:  API version integer

    Returns:
        {"html": str, "metadata": dict}
    """
    try:
        business_name = ai_input.get("business_name", "Business")
        prompt        = ai_input.get("prompt", "")
        logger.info(f"generate_ai_plan: business_name={business_name!r}")
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
        user   = (
            f"Rewrite this text exactly 3 times in a '{tone}' tone for context: '{business_context}'.\n"
            f"Text: '{original_text}'\n"
            f'Output a JSON array: ["version1", "version2", "version3"]'
        )
        res    = chat_completion(system=system, user=user, temperature=0.8)
        result = json.loads(res.strip().replace("```json", "").replace("```", ""))
        return result if isinstance(result, list) and len(result) >= 3 else [original_text] * 3
    except Exception as e:
        logger.warning(f"rewrite_content error: {e}")
        return [original_text] * 3


def get_design_tokens() -> Dict[str, Any]:
    """Export design tokens for external consumption."""
    return {
        "themes":      THEMES,
        "spacing":     {"section": PADDING_SECTION, "container": PADDING_CONTAINER},
        "typography":  {
            "hero":     HEADING_HERO,
            "hero_alt": HEADING_HERO_ALT,
            "section":  HEADING_SECTION,
            "feature":  HEADING_FEATURE,
            "card":     HEADING_CARD,
        },
        "animations":  {"hover_lift": HOVER_LIFT, "hover_glow": HOVER_GLOW, "hover_scale": HOVER_SCALE},
        "industry_pools": {k: len(v) for k, v in INDUSTRY_PHOTO_POOLS.items()},
    }