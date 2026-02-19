"""
website_ai.py  —  Master Architect v3
Self-contained HTML generator. Zero Tailwind CDN dependency.

WHY NO TAILWIND:
  The renderer injects HTML via .innerHTML into a div. Tailwind CDN scripts
  re-execute async and miss classes that were already parsed — causing purple
  browser-default link colours and broken layouts. Pure CSS with CSS custom
  properties is 100% reliable on injection.

WHAT'S NEW IN v3:
  - All styles are inline <style> blocks using CSS variables
  - Zero hardcoded colour values in HTML — all from theme CSS vars
  - Business name = self.name always (never the prompt text)
  - One continuous canvas — sections flow via spacing + gradient bands
  - Scroll-reveal via IntersectionObserver (8 lines of vanilla JS)
  - Testimonials: horizontal snap-scroll on mobile, grid on desktop
  - Contact = real form with conditional email/phone only
  - Sections chosen by AI — only relevant ones rendered
"""

import json
import logging
import re
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

try:
    from app.ai.openai_client import chat_completion
    AI_AVAILABLE = True
except ImportError as e:
    logger.warning(f"AI client not available: {e}")
    AI_AVAILABLE = False

    def chat_completion(system: str, user: str, temperature: float = 0.7) -> str:
        return json.dumps({
            "sections": ["hero", "trust", "features", "testimonials", "faq", "contact"],
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
                {"title": "Expert Team",       "description": "Seasoned professionals committed to results that actually move the needle for your business.", "icon": "◆"},
                {"title": "Proven Results",    "description": "Hundreds of successful engagements. We measure our success by yours.", "icon": "▲"},
                {"title": "Dedicated Support", "description": "A team that responds quickly and keeps you informed at every step.", "icon": "●"},
            ],
            "pricing": None,
            "testimonials": [
                {"name": "Jordan Lee",  "role": "Director", "company": "Meridian Group",
                 "quote": "Working with this team changed how we operate. Measurable results within the first month."},
                {"name": "Priya Nair",  "role": "Founder",  "company": "Spark Ventures",
                 "quote": "Responsive, knowledgeable, and genuinely invested in our success. Highly recommend."},
            ],
            "faq": [
                {"q": "How do I get started?",
                 "a": "Fill out the contact form and we will schedule an initial call to understand your needs."},
                {"q": "What does the process look like?",
                 "a": "Discovery first, then a tailored plan, then execution with full transparency at every stage."},
                {"q": "Do you offer ongoing support?",
                 "a": "Yes — all engagements include continued team access after the initial project is complete."},
            ],
            "cta_headline": "Ready to get started?",
            "contact_email": "",
            "contact_phone": "",
        })


# =============================================================================
# THEMES  — CSS custom properties only. No Tailwind, no hardcoded hex in HTML.
# =============================================================================

THEMES: Dict[str, Dict] = {
    "blue": {
        "id": "blue", "mode": "light",
        "font_family": "'Inter', -apple-system, BlinkMacSystemFont, sans-serif",
        "font_url": "https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap",
        "vars": {
            "--c-bg":           "#ffffff",
            "--c-bg2":          "#f8fafc",
            "--c-text":         "#0f172a",
            "--c-text2":        "#475569",
            "--c-text3":        "#94a3b8",
            "--c-accent":       "#2563eb",
            "--c-accent2":      "#1d4ed8",
            "--c-accent-rgb":   "37,99,235",
            "--c-border":       "#e2e8f0",
            "--c-card":         "#ffffff",
            "--c-card-border":  "#e2e8f0",
            "--c-nav":          "rgba(255,255,255,0.92)",
            "--c-badge-bg":     "#eff6ff",
            "--c-badge-text":   "#1e40af",
            "--c-badge-border": "#bfdbfe",
            "--c-input-bg":     "#f8fafc",
            "--c-input-border": "#e2e8f0",
            "--c-glow":         "rgba(37,99,235,0.07)",
        },
    },
    "slate": {
        "id": "slate", "mode": "light",
        "font_family": "'IBM Plex Sans', -apple-system, BlinkMacSystemFont, sans-serif",
        "font_url": "https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600;700&display=swap",
        "vars": {
            "--c-bg":           "#ffffff",
            "--c-bg2":          "#f8fafc",
            "--c-text":         "#0f172a",
            "--c-text2":        "#475569",
            "--c-text3":        "#94a3b8",
            "--c-accent":       "#334155",
            "--c-accent2":      "#1e293b",
            "--c-accent-rgb":   "51,65,85",
            "--c-border":       "#e2e8f0",
            "--c-card":         "#ffffff",
            "--c-card-border":  "#e2e8f0",
            "--c-nav":          "rgba(255,255,255,0.95)",
            "--c-badge-bg":     "#f1f5f9",
            "--c-badge-text":   "#334155",
            "--c-badge-border": "#cbd5e1",
            "--c-input-bg":     "#f8fafc",
            "--c-input-border": "#e2e8f0",
            "--c-glow":         "rgba(51,65,85,0.05)",
        },
    },
    "amber": {
        "id": "amber", "mode": "light",
        "font_family": "'DM Sans', -apple-system, BlinkMacSystemFont, sans-serif",
        "font_url": "https://fonts.googleapis.com/css2?family=DM+Sans:opsz,wght@9..40,400;9..40,500;9..40,700;9..40,800&display=swap",
        "vars": {
            "--c-bg":           "#fffbf2",
            "--c-bg2":          "#fff6e0",
            "--c-text":         "#1c0f00",
            "--c-text2":        "#6b4c1e",
            "--c-text3":        "#a07840",
            "--c-accent":       "#d97706",
            "--c-accent2":      "#b45309",
            "--c-accent-rgb":   "217,119,6",
            "--c-border":       "#fde68a",
            "--c-card":         "#ffffff",
            "--c-card-border":  "#fde68a",
            "--c-nav":          "rgba(255,251,242,0.94)",
            "--c-badge-bg":     "#fef3c7",
            "--c-badge-text":   "#92400e",
            "--c-badge-border": "#fde68a",
            "--c-input-bg":     "#fffbf2",
            "--c-input-border": "#fde68a",
            "--c-glow":         "rgba(217,119,6,0.07)",
        },
    },
    "green": {
        "id": "green", "mode": "light",
        "font_family": "'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif",
        "font_url": "https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap",
        "vars": {
            "--c-bg":           "#ffffff",
            "--c-bg2":          "#f0fdf4",
            "--c-text":         "#052e16",
            "--c-text2":        "#166534",
            "--c-text3":        "#4ade80",
            "--c-accent":       "#16a34a",
            "--c-accent2":      "#15803d",
            "--c-accent-rgb":   "22,163,74",
            "--c-border":       "#bbf7d0",
            "--c-card":         "#ffffff",
            "--c-card-border":  "#bbf7d0",
            "--c-nav":          "rgba(255,255,255,0.94)",
            "--c-badge-bg":     "#dcfce7",
            "--c-badge-text":   "#15803d",
            "--c-badge-border": "#86efac",
            "--c-input-bg":     "#f0fdf4",
            "--c-input-border": "#bbf7d0",
            "--c-glow":         "rgba(22,163,74,0.07)",
        },
    },
    "dark": {
        "id": "dark", "mode": "dark",
        "font_family": "'Space Grotesk', -apple-system, BlinkMacSystemFont, sans-serif",
        "font_url": "https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&display=swap",
        "vars": {
            "--c-bg":           "#080c10",
            "--c-bg2":          "#0d1117",
            "--c-text":         "#f0f6fc",
            "--c-text2":        "#8b949e",
            "--c-text3":        "#484f58",
            "--c-accent":       "#58a6ff",
            "--c-accent2":      "#1f6feb",
            "--c-accent-rgb":   "88,166,255",
            "--c-border":       "rgba(240,246,252,0.1)",
            "--c-card":         "#0d1117",
            "--c-card-border":  "rgba(240,246,252,0.08)",
            "--c-nav":          "rgba(8,12,16,0.90)",
            "--c-badge-bg":     "rgba(88,166,255,0.1)",
            "--c-badge-text":   "#58a6ff",
            "--c-badge-border": "rgba(88,166,255,0.2)",
            "--c-input-bg":     "#161b22",
            "--c-input-border": "rgba(240,246,252,0.1)",
            "--c-glow":         "rgba(88,166,255,0.08)",
        },
    },
    "rose": {
        "id": "rose", "mode": "dark",
        "font_family": "'Cormorant Garamond', Georgia, serif",
        "font_url": "https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@300;400;600;700&display=swap",
        "vars": {
            "--c-bg":           "#0d0508",
            "--c-bg2":          "#120609",
            "--c-text":         "#fdf2f4",
            "--c-text2":        "#d4a0aa",
            "--c-text3":        "#7a4a54",
            "--c-accent":       "#e11d48",
            "--c-accent2":      "#be123c",
            "--c-accent-rgb":   "225,29,72",
            "--c-border":       "rgba(225,29,72,0.15)",
            "--c-card":         "#120609",
            "--c-card-border":  "rgba(225,29,72,0.12)",
            "--c-nav":          "rgba(13,5,8,0.92)",
            "--c-badge-bg":     "rgba(225,29,72,0.08)",
            "--c-badge-text":   "#fda4af",
            "--c-badge-border": "rgba(225,29,72,0.2)",
            "--c-input-bg":     "#1a080d",
            "--c-input-border": "rgba(225,29,72,0.2)",
            "--c-glow":         "rgba(225,29,72,0.08)",
        },
    },
}

INDUSTRY_KEYWORDS: Dict[str, List[str]] = {
    "saas":         ["software", "app", "platform", "cloud", "api", "saas", "dashboard", "workflow", "automation", "crm"],
    "ai":           ["ai", "artificial intelligence", "machine learning", "ml", "neural", "llm", "gpt", "data science"],
    "ecommerce":    ["shop", "store", "ecommerce", "e-commerce", "sell", "product", "cart", "marketplace", "retail"],
    "health":       ["health", "medical", "wellness", "clinic", "doctor", "hospital", "therapy", "nutrition", "physio"],
    "fitness":      ["fitness", "gym", "personal trainer", "workout", "yoga", "crossfit", "athletics", "exercise"],
    "finance":      ["finance", "banking", "investment", "crypto", "payment", "fintech", "trading", "insurance", "wealth", "accounting", "tax"],
    "agency":       ["agency", "design", "creative", "marketing", "brand", "advertising", "studio", "media"],
    "education":    ["education", "course", "learn", "training", "school", "university", "tutoring", "edtech", "bootcamp"],
    "luxury":       ["luxury", "high-end", "exclusive", "bespoke", "couture", "prestige", "elite"],
    "restaurant":   ["restaurant", "food", "cafe", "bakery", "catering", "cuisine", "dining", "menu", "chef", "bar", "bistro"],
    "beauty":       ["beauty", "salon", "spa", "skincare", "cosmetic", "makeup", "aesthetics", "bridal", "hair", "nail"],
    "real_estate":  ["real estate", "property", "realty", "housing", "apartment", "mortgage", "agent", "broker"],
    "travel":       ["travel", "hotel", "tour", "booking", "vacation", "resort", "hospitality"],
    "startup":      ["startup", "founder", "seed", "venture", "mvp", "launch", "pitch", "scale", "growth"],
    "developer":    ["developer", "engineer", "code", "open source", "github", "devtools", "ide", "terminal", "cli"],
    "nature":       ["organic", "eco", "sustainable", "farm", "agriculture", "environment", "garden", "zero waste"],
    "construction": ["construction", "contractor", "builder", "building", "renovation", "remodel", "plumbing", "electrical",
                     "roofing", "flooring", "masonry", "carpentry", "landscaping", "painting", "hvac", "handyman",
                     "general contractor", "home improvement", "concrete", "drywall", "framing", "trades"],
    "legal":        ["law", "lawyer", "attorney", "legal", "firm", "counsel", "litigation", "contract", "court", "compliance"],
    "logistics":    ["logistics", "shipping", "freight", "delivery", "supply chain", "warehouse", "trucking", "transport", "courier"],
    "automotive":   ["auto", "car", "vehicle", "mechanic", "garage", "dealership", "repair", "tire", "bodywork", "detailing"],
    "nonprofit":    ["nonprofit", "charity", "foundation", "ngo", "volunteer", "donation", "cause", "community"],
    "events":       ["event", "wedding", "conference", "venue", "entertainment", "party", "corporate event"],
}

INDUSTRY_THEME: Dict[str, str] = {
    "saas": "blue",       "ai": "dark",       "ecommerce": "amber",  "health": "green",
    "fitness": "green",   "finance": "blue",  "agency": "dark",      "education": "blue",
    "luxury": "rose",     "restaurant": "amber", "beauty": "rose",   "real_estate": "slate",
    "travel": "blue",     "startup": "dark",  "developer": "dark",   "nature": "green",
    "construction": "slate", "legal": "slate", "logistics": "slate", "automotive": "slate",
    "nonprofit": "green", "events": "amber",
}

INDUSTRY_PHOTOS: Dict[str, List[str]] = {
    "construction": ["photo-1504307651254-35680f356dfd", "photo-1541888946425-d81bb19240f5", "photo-1590674899484-d5640e854abe", "photo-1581578731548-c64695cc6952", "photo-1565117623394-5f93fd4c7a06", "photo-1530836176759-510f6ca9f76f"],
    "legal":        ["photo-1589578527966-fdac0f44566c", "photo-1436450412740-6b988f486c6b", "photo-1505664194779-8beaceb5c7c7", "photo-1521791055366-0d553872952f", "photo-1450101499163-c8848c66ca85", "photo-1568992687947-868a62a9f521"],
    "logistics":    ["photo-1504493188-45c49f65c6ba", "photo-1586528116311-ad8dd3c8310d", "photo-1601584115197-04ecc0da31d7", "photo-1494412574643-ff11b0a5c1c3", "photo-1519003300449-424ad0405076", "photo-1543169964-f2e91dc1fbf4"],
    "automotive":   ["photo-1492144534655-ae79c964c9d7", "photo-1503376780353-7e6692767b70", "photo-1544636331-e26879cd4d9b", "photo-1565043589221-1a6fd9ae45c7", "photo-1558981806-ec527fa84c39", "photo-1549317661-bd32c8ce0db2"],
    "restaurant":   ["photo-1504674900247-0877df9cc836", "photo-1414235077428-338989a2e8c0", "photo-1555396273-367ea4eb4db5", "photo-1517248135467-4c7edcad34c4", "photo-1512621776951-a57141f2eefd", "photo-1467003909585-2f8a72700288"],
    "health":       ["photo-1576091160550-2173dba999ef", "photo-1559757148-5c350d0d3c56", "photo-1535914254981-b5012eebbd15", "photo-1571772996211-2f02c9727629", "photo-1540420773420-3366772f4999", "photo-1631217868264-e5b90bb7e133"],
    "fitness":      ["photo-1534438327276-14e5300c3a48", "photo-1571019613454-1cb2f99b2d8b", "photo-1517836357463-d25dfeac3438", "photo-1549060279-7e168fcee0c2", "photo-1526506118085-60ce8714f8c5", "photo-1574680178050-55c6a6a96e0a"],
    "beauty":       ["photo-1487412947147-5cebf100ffc2", "photo-1560066984-138dadb4c035", "photo-1522337360788-8b13dee7a37e", "photo-1596704017254-9b121068fb31", "photo-1571019613576-2b22c76fd955", "photo-1519014816548-bf5fe059798b"],
    "finance":      ["photo-1611974789855-9c2a0a7236a3", "photo-1563986768609-322da13575f3", "photo-1468254095679-bbcba94a7066", "photo-1454165804606-c3d57bc86b40", "photo-1460925895917-afdab827c52f", "photo-1526304640581-d334cdbbf45e"],
    "real_estate":  ["photo-1560518883-ce09059eeffa", "photo-1570129477492-45c003edd2be", "photo-1513584684374-8bab748fbf90", "photo-1501183638710-841dd1904471", "photo-1486325212027-8081e485255e", "photo-1523217582562-09d0def993a6"],
    "education":    ["photo-1503676260728-1c00da094a0b", "photo-1456513080510-7bf3a84b82f8", "photo-1509062522246-3755977927d7", "photo-1427504494785-3a9ca7044f45", "photo-1522202176988-66273c2fd55f", "photo-1434030216411-0b793f4b4173"],
    "travel":       ["photo-1501854140801-50d01698950b", "photo-1436491865332-7a61a109cc05", "photo-1488085061387-422e29b40080", "photo-1476514525535-07fb3b4ae5f1", "photo-1530521954074-e64f6810b32d", "photo-1503220317375-aaad61436b1b"],
    "ecommerce":    ["photo-1556742049-0cfed4f6a45d", "photo-1472851294608-062f824d29cc", "photo-1607082348824-0a96f2a4b9da", "photo-1523275335684-37898b6baf30", "photo-1581091226825-a6a2a5aee158", "photo-1526170375885-4d8ecf77b99f"],
    "saas":         ["photo-1518770660439-4636190af475", "photo-1461749280684-dccba630e2f6", "photo-1551434678-e076c223a692", "photo-1497366216548-37526070297c", "photo-1573164713988-8665fc963095", "photo-1498050108023-c5249f4df085"],
    "ai":           ["photo-1677442135703-1787eea5ce01", "photo-1620712943543-bcc4688e7485", "photo-1555255707-c07966088b7b", "photo-1518770660439-4636190af475", "photo-1535378917042-10a22c95931a", "photo-1593508512255-86ab42a8e620"],
    "developer":    ["photo-1461749280684-dccba630e2f6", "photo-1498050108023-c5249f4df085", "photo-1555066931-4365d14bab8c", "photo-1607799279861-4dd421887fb3", "photo-1562813733-b31f71025d54", "photo-1504639725590-34d0984388bd"],
    "startup":      ["photo-1559136555-9303baea8ebd", "photo-1531297484001-80022131f5a1", "photo-1556761175-4b46a572b786", "photo-1522202176988-66273c2fd55f", "photo-1553484771-371a605b060b", "photo-1531973576160-7125cd663d86"],
    "agency":       ["photo-1558655146-9f40138edfeb", "photo-1524758631624-e2822e304c36", "photo-1497366754035-f200968a6e72", "photo-1535016120720-40c646be5580", "photo-1559028012-481c04fa702d", "photo-1542744173-8e7e53415bb0"],
    "nature":       ["photo-1441974231531-c6227db76b6e", "photo-1506905925346-21bda4d32df4", "photo-1469474968028-56623f02e42e", "photo-1500534314209-a25ddb2bd429", "photo-1518173946687-a4c8892bbd9f", "photo-1540979388789-6cee28a1cdc9"],
    "nonprofit":    ["photo-1593113630400-ea4288922559", "photo-1559027615-cd4628902d4a", "photo-1532629345422-7515f3d16bb6", "photo-1509099836639-18ba1795216d", "photo-1491438590914-bc09fcaaf77a", "photo-1488521787991-ed7bbaae773c"],
    "events":       ["photo-1540575467063-178a50c2df87", "photo-1511795409834-ef04bbd61622", "photo-1464366400600-7168b8af9bc3", "photo-1519167758481-83f550bb49b3", "photo-1529543544282-ea669407fca3", "photo-1505373877841-8d25f7d46678"],
}
_DEFAULT_PHOTOS = ["photo-1552664730-d307ca884978", "photo-1460925895917-afdab827c52f", "photo-1556742049-0cfed4f6a45d", "photo-1497366216548-37526070297c"]


def _photo_url(industry: str, idx: int, w: int = 1000) -> str:
    pool = INDUSTRY_PHOTOS.get(industry, _DEFAULT_PHOTOS)
    pid  = pool[idx % len(pool)]
    return f"https://images.unsplash.com/{pid}?w={w}&auto=format&fit=crop&q=80"


def detect_industry(text: str) -> str:
    tl = (text or "").lower()
    scores = {ind: sum(len(kw.split()) for kw in kws if kw in tl)
              for ind, kws in INDUSTRY_KEYWORDS.items()}
    best = max(scores, key=lambda k: scores[k])
    return best if scores[best] > 0 else "saas"


def select_theme(industry: str) -> Dict:
    return THEMES[INDUSTRY_THEME.get(industry, "blue")]


# =============================================================================
# BUSINESS NAME + CONTACT EXTRACTION
# =============================================================================

def extract_business_name(raw: str, prompt: str):
    """
    Returns (name, cleaned_prompt).
    IMPORTANT: name is always the actual business name — never the prompt text.
    """
    raw, prompt = (raw or "").strip(), (prompt or "").strip()
    pl = prompt.lower()

    for indicator in ["the company name is ", "company name: ", "business name: ",
                      "we're called ", "it's called ", "my company is called ", "my business is called "]:
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
    desc_starters = ["we ", "our ", "a ", "an ", "the ", "i have", "i own", "i run", "this is", "it's a"]
    for s in desc_starters:
        if rl.startswith(s):
            return "", f"{raw}. {prompt}".strip(" .")

    prefixes = ["my company is called ", "my business is called ", "company name is ",
                "called ", "named ", "name is ", "it's called "]
    for p in prefixes:
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
        "construction": "BuildRight Group",  "legal": "Sterling Law",
        "finance": "Apex Capital",           "health": "Vitalis Health",
        "fitness": "Peak Fitness",           "restaurant": "The Kitchen",
        "beauty": "Lumiere Studio",          "ecommerce": "The Shop",
        "education": "Elevate Academy",      "real_estate": "Keystone Realty",
        "logistics": "Swift Logistics",      "automotive": "AutoPro",
        "events": "Premier Events",          "nonprofit": "Together Foundation",
        "nature": "Green Root",              "agency": "Creative Studio",
        "travel": "Voyage Co.",              "saas": "LaunchPad",
        "ai": "Neural",                      "developer": "DevBase",
        "startup": "Foundry",
    }.get(industry, "My Business")


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
# PAGE CSS — all styles, zero Tailwind, pure CSS variables
# =============================================================================

def _page_css(t: Dict) -> str:
    vars_css = "\n".join(f"  {k}: {v};" for k, v in t["vars"].items())
    return f"""<style>
*,*::before,*::after{{box-sizing:border-box;margin:0;padding:0}}
:root{{{vars_css}}}
html{{font-family:{t['font_family']};background:var(--c-bg);color:var(--c-text);scroll-behavior:smooth;-webkit-font-smoothing:antialiased}}
body{{background:var(--c-bg);color:var(--c-text);overflow-x:hidden}}
img{{display:block;max-width:100%}}
a{{color:inherit;text-decoration:none}}
button{{cursor:pointer;font-family:inherit;border:none;background:none}}
input,textarea,select{{font-family:inherit}}

/* Typography */
.t-hero{{font-size:clamp(2.5rem,6vw,5.5rem);font-weight:900;letter-spacing:-0.03em;line-height:1.05;color:var(--c-text)}}
.t-section{{font-size:clamp(1.9rem,3.5vw,3rem);font-weight:800;letter-spacing:-0.025em;line-height:1.12;color:var(--c-text)}}
.t-card{{font-size:1.05rem;font-weight:700;letter-spacing:-0.01em;color:var(--c-text)}}
.t-eyebrow{{display:block;font-size:0.68rem;font-weight:700;text-transform:uppercase;letter-spacing:0.2em;color:var(--c-accent);margin-bottom:0.85rem}}
.t-body{{font-size:1.05rem;line-height:1.7;color:var(--c-text2)}}
.t-small{{font-size:0.85rem;line-height:1.65;color:var(--c-text2)}}
.t-muted{{color:var(--c-text3)}}
.t-accent{{color:var(--c-accent)}}
.t-grad{{background:linear-gradient(135deg,var(--c-accent),var(--c-accent2));-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text}}

/* Layout */
.wrap{{width:100%;max-width:1160px;margin:0 auto;padding:0 1.5rem}}
@media(min-width:768px){{.wrap{{padding:0 2.5rem}}}}

/* Sections — ONE background, rhythm through spacing */
.sec{{position:relative;padding:6rem 0}}
.sec-sm{{position:relative;padding:3.5rem 0}}
.sec-hero{{position:relative;padding:7rem 0 5rem;min-height:90vh;display:flex;align-items:center}}
@media(max-width:767px){{
  .sec{{padding:4rem 0}}
  .sec-hero{{padding:5rem 0 3.5rem;min-height:auto}}
}}

/* Subtle band — a translucent tint to break monotony without bg colour change */
.sec-band::before{{content:'';position:absolute;inset:0;background:linear-gradient(180deg,transparent 0%,rgba(var(--c-accent-rgb),0.035) 35%,rgba(var(--c-accent-rgb),0.035) 65%,transparent 100%);pointer-events:none}}

/* Grid */
.g2{{display:grid;grid-template-columns:1fr;gap:2rem}}
.g3{{display:grid;grid-template-columns:1fr;gap:1.5rem}}
.g4{{display:grid;grid-template-columns:repeat(2,1fr);gap:1.25rem}}
@media(min-width:640px){{.g3{{grid-template-columns:repeat(2,1fr)}}}}
@media(min-width:900px){{
  .g2{{grid-template-columns:repeat(2,1fr)}}
  .g3{{grid-template-columns:repeat(3,1fr)}}
  .g4{{grid-template-columns:repeat(4,1fr)}}
}}
.ai{{align-items:center}}
.as{{align-items:start}}
.gap-xl{{gap:4rem}}

/* Utilities */
.rel{{position:relative}}
.z1{{position:relative;z-index:1}}
.tc{{text-align:center}}
.mx-auto{{margin-left:auto;margin-right:auto}}
.mw-sm{{max-width:34rem}}
.mw-md{{max-width:48rem}}
.mw-lg{{max-width:64rem}}
.mt1{{margin-top:0.5rem}}.mt2{{margin-top:1rem}}.mt3{{margin-top:1.5rem}}
.mt4{{margin-top:2rem}}.mt5{{margin-top:2.5rem}}.mt6{{margin-top:3rem}}
.mb1{{margin-bottom:0.5rem}}.mb2{{margin-bottom:1rem}}.mb3{{margin-bottom:1.5rem}}
.mb4{{margin-bottom:2rem}}.mb5{{margin-bottom:2.5rem}}.mb6{{margin-bottom:3rem}}
.flex{{display:flex}}.flex-col{{flex-direction:column}}.flex-wrap{{flex-wrap:wrap}}
.gap1{{gap:0.5rem}}.gap2{{gap:0.75rem}}.gap3{{gap:1rem}}.gap4{{gap:1.5rem}}.gap5{{gap:2rem}}
.w100{{width:100%}}

/* Nav */
.site-nav{{position:fixed;top:0;left:0;right:0;z-index:200;background:var(--c-nav);border-bottom:1px solid var(--c-border);backdrop-filter:blur(16px);-webkit-backdrop-filter:blur(16px)}}
.nav-in{{display:flex;align-items:center;justify-content:space-between;height:64px;padding:0 1.5rem;max-width:1160px;margin:0 auto}}
@media(min-width:768px){{.nav-in{{padding:0 2.5rem}}}}
.nav-logo{{font-size:1.1rem;font-weight:900;letter-spacing:-0.03em;color:var(--c-text)}}
.nav-links{{display:none;list-style:none;gap:2rem;align-items:center}}
@media(min-width:768px){{.nav-links{{display:flex}}}}
.nav-links a{{font-size:0.875rem;font-weight:500;color:var(--c-text2);transition:color 0.2s}}
.nav-links a:hover{{color:var(--c-text)}}
.nav-act{{display:flex;align-items:center;gap:1rem}}
.nav-cta{{background:var(--c-accent);color:#fff !important;font-size:0.85rem;font-weight:600;padding:0.45rem 1.15rem;border-radius:8px;transition:opacity 0.2s,transform 0.2s}}
.nav-cta:hover{{opacity:0.88;transform:translateY(-1px)}}
@media(max-width:767px){{.nav-cta{{display:none}}}}
.hamburger{{display:flex;flex-direction:column;gap:5px;padding:4px;cursor:pointer}}
@media(min-width:768px){{.hamburger{{display:none}}}}
.hamburger span{{display:block;width:22px;height:2px;background:var(--c-text);border-radius:2px}}
.nav-mob{{display:none;flex-direction:column;position:absolute;top:64px;left:0;right:0;background:var(--c-nav);border-bottom:1px solid var(--c-border);padding:0.75rem 1.5rem 1.25rem}}
.nav-mob.open{{display:flex}}
.nav-mob a{{padding:0.7rem 0;border-bottom:1px solid var(--c-border);font-size:0.9rem;font-weight:500;color:var(--c-text2)}}
.nav-mob a:last-child{{border-bottom:none;padding-top:1rem}}

/* Buttons */
.btn{{display:inline-block;font-weight:700;font-size:0.95rem;padding:0.85rem 2rem;border-radius:10px;transition:all 0.25s cubic-bezier(.16,1,.3,1);cursor:pointer;text-align:center}}
.btn-p{{background:var(--c-accent);color:#fff !important;border:2px solid var(--c-accent)}}
.btn-p:hover{{background:var(--c-accent2);border-color:var(--c-accent2);transform:translateY(-2px);box-shadow:0 8px 24px rgba(var(--c-accent-rgb),.28)}}
.btn-g{{background:transparent;color:var(--c-text) !important;border:2px solid var(--c-border)}}
.btn-g:hover{{border-color:var(--c-accent);color:var(--c-accent) !important}}
.btn-row{{display:flex;flex-wrap:wrap;gap:0.85rem;align-items:center}}

/* Cards */
.card{{background:var(--c-card);border:1px solid var(--c-card-border);border-radius:16px;box-shadow:0 1px 3px rgba(0,0,0,0.07),0 1px 2px rgba(0,0,0,0.04);transition:box-shadow 0.3s,transform 0.3s}}
.card:hover{{box-shadow:0 12px 40px rgba(var(--c-accent-rgb),.1),0 4px 12px rgba(0,0,0,0.06);transform:translateY(-3px)}}
.card-p{{padding:1.75rem}}
.card-plg{{padding:2.25rem}}

/* Feature icon */
.feat-icon{{width:48px;height:48px;border-radius:12px;display:flex;align-items:center;justify-content:center;font-size:1.3rem;background:linear-gradient(135deg,rgba(var(--c-accent-rgb),.12),rgba(var(--c-accent-rgb),.04));margin-bottom:1.1rem;flex-shrink:0}}

/* Badge / pill */
.badge{{display:inline-flex;align-items:center;gap:0.4rem;font-size:0.68rem;font-weight:700;text-transform:uppercase;letter-spacing:0.12em;padding:0.3rem 0.8rem;border-radius:999px;background:var(--c-badge-bg);color:var(--c-badge-text);border:1px solid var(--c-badge-border)}}
.bdot{{width:6px;height:6px;border-radius:50%;background:var(--c-accent);animation:bpulse 2s infinite}}
@keyframes bpulse{{0%,100%{{opacity:1}}50%{{opacity:.4}}}}

/* Stats */
.stat-val{{font-size:clamp(2rem,4vw,3.25rem);font-weight:900;letter-spacing:-0.04em;color:var(--c-accent);line-height:1}}
.stat-lbl{{font-size:0.78rem;color:var(--c-text2);margin-top:0.3rem;line-height:1.4}}

/* Images */
.img-frame{{border-radius:16px;overflow:hidden;box-shadow:0 20px 60px rgba(0,0,0,0.13)}}
.img-tall{{height:520px}}
.img-sq{{aspect-ratio:4/3}}
.img-wide{{aspect-ratio:16/9}}
.img-fill{{width:100%;height:100%;object-fit:cover;display:block}}
@media(max-width:767px){{.img-tall{{height:280px}}}}

/* Checklist */
.chklist{{list-style:none;display:flex;flex-direction:column;gap:0.55rem}}
.chk-item{{display:flex;align-items:flex-start;gap:0.6rem;font-size:0.875rem;color:var(--c-text2)}}
.chk-icon{{flex-shrink:0;width:16px;height:16px;margin-top:2px;color:var(--c-accent);font-weight:900;font-size:0.75rem;display:flex;align-items:center;justify-content:center}}

/* Stars */
.stars{{color:#f59e0b;font-size:0.875rem;letter-spacing:1px;margin-bottom:0.85rem}}

/* Avatar */
.avatar{{width:40px;height:40px;border-radius:50%;background:linear-gradient(135deg,var(--c-accent),var(--c-accent2));display:flex;align-items:center;justify-content:center;color:#fff;font-weight:800;font-size:0.9rem;flex-shrink:0}}

/* Form */
.form-label{{display:block;font-size:0.68rem;font-weight:700;text-transform:uppercase;letter-spacing:0.12em;color:var(--c-text2);margin-bottom:0.4rem}}
.form-input{{width:100%;padding:0.75rem 1rem;font-size:0.9rem;background:var(--c-input-bg);border:1px solid var(--c-input-border);border-radius:10px;color:var(--c-text);outline:none;transition:border-color 0.2s,box-shadow 0.2s}}
.form-input:focus{{border-color:var(--c-accent);box-shadow:0 0 0 3px rgba(var(--c-accent-rgb),.12)}}
.form-input::placeholder{{color:var(--c-text3)}}
textarea.form-input{{resize:none;min-height:130px}}
.form-row{{margin-bottom:1.1rem}}

/* FAQ */
details.faq{{border:1px solid var(--c-border);border-radius:12px;overflow:hidden;margin-bottom:0.6rem;background:var(--c-card)}}
details.faq>summary{{list-style:none;display:flex;justify-content:space-between;align-items:center;padding:1.1rem 1.4rem;cursor:pointer;font-weight:600;font-size:0.9rem;color:var(--c-text);user-select:none;gap:1rem}}
details.faq>summary::-webkit-details-marker{{display:none}}
.faq-icon{{flex-shrink:0;width:22px;height:22px;border:1px solid var(--c-border);border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:0.8rem;color:var(--c-text2);transition:transform 0.2s}}
details.faq[open]>.summary .faq-icon{{transform:rotate(45deg)}}
details.faq[open]>summary .faq-icon{{transform:rotate(45deg)}}
.faq-body{{padding:0 1.4rem 1.1rem;font-size:0.875rem;color:var(--c-text2);line-height:1.7;border-top:1px solid var(--c-border);padding-top:0.9rem}}

/* Testimonials scroll on mobile */
.testi-grid{{display:flex;gap:1rem;overflow-x:auto;scroll-snap-type:x mandatory;padding-bottom:0.5rem;scrollbar-width:none}}
.testi-grid::-webkit-scrollbar{{display:none}}
.testi-grid .card{{scroll-snap-align:start;flex-shrink:0;width:min(84vw,340px);display:flex;flex-direction:column}}
@media(min-width:768px){{
  .testi-grid{{display:grid;grid-template-columns:repeat(2,1fr);overflow:visible;scroll-snap-type:none}}
  .testi-grid .card{{width:auto}}
}}
@media(min-width:1024px){{.testi-grid{{grid-template-columns:repeat(3,1fr)}}}}

/* Separator */
.hr{{border:none;border-top:1px solid var(--c-border);margin:0}}

/* Ambient glow blobs — purely decorative, no layout impact */
.glow-blob{{position:absolute;border-radius:50%;filter:blur(80px);pointer-events:none;z-index:0;background:var(--c-glow)}}

/* Footer */
.site-footer{{border-top:1px solid var(--c-border);padding:4rem 0 2rem;background:var(--c-bg)}}

/* Scroll reveal */
.rv{{opacity:0;transform:translateY(20px);transition:opacity .7s cubic-bezier(.16,1,.3,1),transform .7s cubic-bezier(.16,1,.3,1)}}
.rv.in{{opacity:1;transform:none}}
.d1{{transition-delay:.1s}}.d2{{transition-delay:.2s}}.d3{{transition-delay:.3s}}.d4{{transition-delay:.4s}}
</style>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="{t['font_url']}">"""


REVEAL_JS = """<script>
(function(){
  var els=document.querySelectorAll('.rv');
  if(!els.length)return;
  if(window.IntersectionObserver){
    var io=new IntersectionObserver(function(entries){
      entries.forEach(function(e){if(e.isIntersecting){e.target.classList.add('in');io.unobserve(e.target);}});
    },{threshold:0.1});
    els.forEach(function(el){io.observe(el);});
  }else{
    els.forEach(function(el){el.classList.add('in');});
  }
  // Mobile nav
  var btn=document.getElementById('nav-btn');
  var mob=document.getElementById('nav-mob');
  if(btn&&mob){
    btn.addEventListener('click',function(){mob.classList.toggle('open');});
    mob.querySelectorAll('a').forEach(function(a){
      a.addEventListener('click',function(){mob.classList.remove('open');});
    });
  }
})();
</script>"""


# =============================================================================
# HTML PRIMITIVES
# =============================================================================

def _eyebrow(label: str) -> str:
    return f'<span class="t-eyebrow">{label}</span>'

def _h2(title: str, sub: str = "") -> str:
    sub_html = f'<p class="t-body mt2 mw-sm">{sub}</p>' if sub else ""
    return f'<h2 class="t-section">{title}</h2>{sub_html}'

def _btn(label: str, href: str = "#contact", style: str = "p") -> str:
    return f'<a href="{href}" class="btn btn-{style}">{label}</a>'

def _chk(text: str) -> str:
    return (f'<li class="chk-item">'
            f'<span class="chk-icon">✓</span>'
            f'<span>{text}</span></li>')

def _stars() -> str:
    return '<div class="stars">★★★★★</div>'


# =============================================================================
# NAV
# =============================================================================

def _build_nav(name: str, items: List[str], cta: str) -> str:
    li = "".join(
        f'<li><a href="#{it.lower().replace(" ","")}">{it}</a></li>'
        for it in items
    )
    mob = "".join(
        f'<a href="#{it.lower().replace(" ","")}">{it}</a>'
        for it in items
    ) + f'<a href="#contact" style="background:var(--c-accent);color:#fff !important;border-radius:8px;padding:0.7rem 0;margin-top:0.5rem;text-align:center;font-weight:700;">{cta}</a>'

    return f"""<nav class="site-nav">
  <div class="nav-in">
    <a href="#" class="nav-logo">{name}</a>
    <ul class="nav-links">{li}</ul>
    <div class="nav-act">
      <a href="#contact" class="nav-cta">{cta}</a>
      <button class="hamburger" id="nav-btn" aria-label="Menu">
        <span></span><span></span><span></span>
      </button>
    </div>
  </div>
  <div class="nav-mob" id="nav-mob">{mob}</div>
</nav>"""


# =============================================================================
# HERO VARIANTS
# =============================================================================

def _hero_split(name: str, d: Dict, industry: str) -> str:
    h     = d.get("hero", {})
    h1    = h.get("h1", f"Welcome to {name}")
    sub   = h.get("sub", "")
    cta   = h.get("cta", "Get Started")
    tag   = d.get("tagline", "")
    proof = d.get("social_proof") or {}
    img   = _photo_url(industry, 0, 1000)

    tag_html = f'<div class="badge mb3 rv"><span class="bdot"></span>{tag}</div>' if tag else ""

    proof_html = ""
    if proof.get("count") and proof.get("label"):
        avs = "".join(
            f'<div style="width:28px;height:28px;border-radius:50%;background:linear-gradient(135deg,var(--c-accent),var(--c-accent2));border:2px solid var(--c-bg);display:flex;align-items:center;justify-content:center;color:#fff;font-size:0.6rem;font-weight:800;margin-left:{"-6px" if i else "0"};">{chr(65+i)}</div>'
            for i in range(4)
        )
        proof_html = f"""<div class="flex ai gap3 mt4" style="border-top:1px solid var(--c-border);padding-top:1.25rem;flex-wrap:wrap;">
      <div class="flex ai">{avs}</div>
      <span class="t-small"><strong style="color:var(--c-accent)">{proof['count']}</strong> {proof['label']}</span>
    </div>"""

    return f"""<section class="sec-hero" style="padding-top:7rem;">
  <div class="glow-blob" style="width:600px;height:600px;top:-10%;right:-8%;opacity:0.8;"></div>
  <div class="glow-blob" style="width:300px;height:300px;bottom:5%;left:-5%;opacity:0.5;"></div>
  <div class="wrap z1">
    <div class="g2 ai gap-xl">
      <div class="rv" style="order:2;">
        {tag_html}
        <h1 class="t-hero">{h1}</h1>
        <p class="t-body mt3 mw-sm">{sub}</p>
        <div class="btn-row mt4">
          {_btn(cta, "#contact")}
          {_btn("See how it works →", "#features", "g")}
        </div>
        {proof_html}
      </div>
      <div class="rv d1" style="order:1;">
        <div class="img-frame img-tall" style="position:relative;">
          <div style="position:absolute;inset:-16px;background:radial-gradient(circle,var(--c-glow) 0%,transparent 70%);z-index:-1;"></div>
          <img src="{img}" alt="{name}" class="img-fill" loading="eager">
        </div>
      </div>
    </div>
  </div>
</section>"""


def _hero_centered(name: str, d: Dict, industry: str) -> str:
    h   = d.get("hero", {})
    h1  = h.get("h1", f"Welcome to {name}")
    sub = h.get("sub", "")
    cta = h.get("cta", "Discover")
    tag = d.get("tagline", "")
    img = _photo_url(industry, 0, 1200)

    tag_html = f'<p style="font-size:0.72rem;font-weight:700;text-transform:uppercase;letter-spacing:0.22em;color:var(--c-accent);margin-bottom:1.5rem;">— {tag} —</p>' if tag else ""

    return f"""<section class="sec-hero" style="min-height:92vh;background:linear-gradient(180deg,var(--c-bg2) 0%,var(--c-bg) 100%);">
  <div class="glow-blob" style="width:700px;height:700px;top:-15%;left:50%;transform:translateX(-50%);opacity:0.6;"></div>
  <div style="position:absolute;inset:0;overflow:hidden;pointer-events:none;">
    <img src="{img}" alt="" style="width:100%;height:100%;object-fit:cover;opacity:0.1;" loading="eager">
    <div style="position:absolute;inset:0;background:linear-gradient(to bottom,var(--c-bg2) 0%,rgba(255,255,255,0) 40%,rgba(255,255,255,0) 60%,var(--c-bg) 100%);"></div>
  </div>
  <div class="wrap z1 tc">
    <div class="rv mw-md mx-auto" style="padding:2rem 0;">
      {tag_html}
      <h1 class="t-hero">{h1}</h1>
      <p class="t-body mt3 mw-sm mx-auto">{sub}</p>
      <div class="btn-row mt5" style="justify-content:center;">
        {_btn(cta, "#contact")}
        {_btn("Learn more ↓", "#features", "g")}
      </div>
    </div>
  </div>
</section>"""


def _hero_stats(name: str, d: Dict, industry: str) -> str:
    h     = d.get("hero", {})
    h1    = h.get("h1", f"Welcome to {name}")
    sub   = h.get("sub", "")
    cta   = h.get("cta", "Get Started")
    stats = d.get("stats") or []
    img   = _photo_url(industry, 0, 1200)

    stat_items = ""
    if stats:
        stat_items = "".join(
            f'<div class="rv d{min(i+1,4)}" style="text-align:center;">'
            f'<div class="stat-val">{s.get("value","")}</div>'
            f'<div class="stat-lbl">{s.get("label","")}</div></div>'
            for i, s in enumerate(stats[:4])
        )
        stat_items = f'<div class="g4 mt6" style="border-top:1px solid var(--c-border);padding-top:2.5rem;">{stat_items}</div>'

    return f"""<section class="sec-hero" style="overflow:hidden;">
  <div class="glow-blob" style="width:700px;height:700px;top:-10%;right:-5%;opacity:0.7;"></div>
  <div style="position:absolute;top:0;right:0;width:48%;height:100%;overflow:hidden;pointer-events:none;">
    <img src="{img}" alt="" style="width:100%;height:100%;object-fit:cover;opacity:0.08;" loading="eager">
    <div style="position:absolute;inset:0;background:linear-gradient(to right,var(--c-bg) 0%,transparent 60%);"></div>
  </div>
  <div class="wrap z1">
    <div style="max-width:580px;" class="rv">
      <h1 class="t-hero">{h1}</h1>
      <p class="t-body mt3">{sub}</p>
      <div class="btn-row mt4">
        {_btn(cta, "#contact")}
        {_btn("See our work →", "#features", "g")}
      </div>
    </div>
    {stat_items}
  </div>
</section>"""


def _hero_editorial(name: str, d: Dict, industry: str) -> str:
    h   = d.get("hero", {})
    h1  = h.get("h1", f"Welcome to {name}")
    sub = h.get("sub", "")
    cta = h.get("cta", "Explore")
    img = _photo_url(industry, 0, 1200)
    ws  = h1.split()
    mid = max(1, len(ws) // 2)
    l1, l2 = " ".join(ws[:mid]), " ".join(ws[mid:]) or ws[-1]

    return f"""<section class="sec" style="padding-top:7rem;">
  <div class="glow-blob" style="width:500px;height:500px;top:-5%;right:-8%;opacity:0.7;"></div>
  <div class="wrap z1">
    <h1 class="rv" style="font-size:clamp(2.8rem,6.5vw,6rem);font-weight:900;letter-spacing:-0.035em;line-height:1.02;margin-bottom:2.5rem;">
      <span style="display:block;color:var(--c-text);">{l1}</span>
      <span class="t-grad" style="display:block;">{l2}</span>
    </h1>
    <div class="g2 ai gap-xl">
      <div class="img-frame img-wide rv">
        <img src="{img}" alt="{name}" class="img-fill" loading="eager">
      </div>
      <div class="rv d2">
        <p class="t-body mb4">{sub}</p>
        {_btn(f"{cta} →", "#contact")}
      </div>
    </div>
  </div>
</section>"""


# =============================================================================
# TRUST BAND
# =============================================================================

def _build_trust(badges: List[str]) -> str:
    if not badges:
        return ""
    pills = "".join(f'<span class="badge">{b}</span>' for b in badges)
    return f"""<div class="sec-sm" style="border-top:1px solid var(--c-border);border-bottom:1px solid var(--c-border);">
  <div class="wrap">
    <div class="rv flex flex-wrap ai" style="justify-content:center;gap:0.75rem;">
      <span style="font-size:0.68rem;font-weight:700;text-transform:uppercase;letter-spacing:0.15em;color:var(--c-text3);margin-right:0.25rem;">Certified</span>
      {pills}
    </div>
  </div>
</div>"""


# =============================================================================
# FEATURES VARIANTS
# =============================================================================

def _feat_cards(features: List[Dict]) -> str:
    cards = "".join(
        f"""<div class="card card-p rv d{min(i+1,4)}">
      <div class="feat-icon">{f.get("icon","◆")}</div>
      <h3 class="t-card mb1">{f.get("title","")}</h3>
      <p class="t-small">{f.get("description","")}</p>
    </div>"""
        for i, f in enumerate(features or [])
    )
    return f"""<section class="sec sec-band" id="features">
  <div class="wrap">
    <div class="tc mb6 rv">
      {_eyebrow("What We Offer")}
      {_h2("Everything You Need", "Crafted to help your business move forward.")}
    </div>
    <div class="g3">{cards}</div>
  </div>
</section>"""


def _feat_alternating(features: List[Dict], industry: str) -> str:
    blocks = []
    for i, f in enumerate(features or []):
        img   = _photo_url(industry, i + 1, 900)
        rev   = "direction:row-reverse;" if i % 2 != 0 else ""
        blocks.append(f"""<div class="g2 ai gap-xl" style="{rev}margin-bottom:5rem;">
      <div class="rv">
        <div style="font-size:2.5rem;line-height:1;margin-bottom:1rem;">{f.get("icon","◆")}</div>
        <h3 class="t-section" style="font-size:1.65rem;margin-bottom:1rem;">{f.get("title","")}</h3>
        <p class="t-body">{f.get("description","")}</p>
        <a href="#contact" class="btn btn-g" style="margin-top:1.5rem;font-size:0.875rem;padding:0.6rem 1.25rem;">Learn more →</a>
      </div>
      <div class="img-frame img-sq rv d1">
        <img src="{img}" alt="" class="img-fill" loading="lazy">
      </div>
    </div>""")
    return f"""<section class="sec" id="features">
  <div class="wrap">
    <div class="tc mb6 rv">
      {_eyebrow("How It Works")}
      {_h2("Why Choose Us")}
    </div>
    {"".join(blocks)}
  </div>
</section>"""


def _feat_icon_list(features: List[Dict], industry: str) -> str:
    img   = _photo_url(industry, 1, 900)
    items = "".join(
        f"""<div class="rv d{min(i+1,4)}" style="display:flex;gap:1rem;align-items:flex-start;padding:1rem;border:1px solid var(--c-border);border-radius:12px;margin-bottom:0.75rem;background:var(--c-card);">
      <div style="min-width:36px;height:36px;border-radius:50%;background:linear-gradient(135deg,var(--c-accent),var(--c-accent2));display:flex;align-items:center;justify-content:center;color:#fff;font-weight:800;font-size:0.72rem;flex-shrink:0;">{str(i+1).zfill(2)}</div>
      <div>
        <h3 class="t-card mb1">{f.get("title","")}</h3>
        <p class="t-small">{f.get("description","")}</p>
      </div>
    </div>"""
        for i, f in enumerate(features or [])
    )
    return f"""<section class="sec sec-band" id="features">
  <div class="wrap">
    <div class="g2 ai gap-xl">
      <div class="rv">
        {_eyebrow("Our Approach")}
        <h2 class="t-section mb5">Built for Real Results</h2>
        {items}
      </div>
      <div class="img-frame img-tall rv d2">
        <img src="{img}" alt="" class="img-fill" loading="lazy">
      </div>
    </div>
  </div>
</section>"""


# =============================================================================
# PRICING VARIANTS
# =============================================================================

def _price_tiers(tiers: List[Dict]) -> str:
    def _one(tier: Dict, idx: int) -> str:
        feat = tier.get("featured", False)
        fs   = "background:linear-gradient(135deg,var(--c-accent),var(--c-accent2));border-color:transparent;" if feat else ""
        tc   = "color:#fff;" if feat else "color:var(--c-text2);"
        pc   = "color:#fff;" if feat else "color:var(--c-text);"
        cc   = "color:#fff;" if feat else "color:var(--c-accent);"
        pop  = '<span style="position:absolute;top:1rem;right:1rem;font-size:0.62rem;font-weight:700;background:rgba(255,255,255,0.22);color:#fff;padding:0.2rem 0.6rem;border-radius:999px;text-transform:uppercase;letter-spacing:0.1em;">Popular</span>' if feat else ""
        cta_style = "display:block;text-align:center;margin-top:1.5rem;padding:0.85rem;border-radius:10px;font-weight:700;font-size:0.9rem;"
        cta_html  = (
            f'<a href="#contact" style="{cta_style}background:#fff;color:var(--c-accent);">Get Started</a>'
            if feat else
            f'<a href="#contact" class="btn btn-g" style="{cta_style}width:100%;">{tier.get("cta","Get Started")}</a>'
        )
        rows = "".join(
            f'<li class="chk-item"><span class="chk-icon" style="{cc}">✓</span><span style="{tc}">{f}</span></li>'
            for f in (tier.get("features") or [])
        )
        return f"""<div class="card card-p rv d{min(idx+1,4)}" style="position:relative;display:flex;flex-direction:column;{fs}">
      {pop}
      <h3 style="font-weight:700;font-size:1.1rem;margin-bottom:0.25rem;{pc}">{tier.get("name","Plan")}</h3>
      <p style="font-size:0.8rem;margin-bottom:1.25rem;{tc}">{tier.get("description","")}</p>
      <div style="margin-bottom:1.5rem;">
        <span style="font-size:2.75rem;font-weight:900;letter-spacing:-0.04em;{pc}">{tier.get("price","$0")}</span>
        <span style="font-size:0.78rem;{tc}"> /mo</span>
      </div>
      <ul class="chklist" style="flex:1;">{rows}</ul>
      {cta_html}
    </div>"""
    cards = "".join(_one(t, i) for i, t in enumerate(tiers or []))
    return f"""<section class="sec" id="pricing">
  <div class="wrap">
    <div class="tc mb6 rv">
      {_eyebrow("Pricing")}
      {_h2("Simple, Honest Pricing", "No hidden fees. Cancel any time.")}
    </div>
    <div class="g3 mw-lg mx-auto">{cards}</div>
  </div>
</section>"""


def _price_project(tiers: List[Dict]) -> str:
    cards = "".join(
        f"""<div class="card card-p rv d{min(i+1,4)}" style="display:flex;flex-direction:column;">
      <h3 class="t-card mb1">{t.get("name","Package")}</h3>
      <p class="t-small mb3">{t.get("description","")}</p>
      <p style="font-size:1.3rem;font-weight:800;color:var(--c-accent);margin-bottom:1rem;">{t.get("price","Get a Quote")}</p>
      <ul class="chklist" style="flex:1;margin-bottom:1.5rem;">{"".join(_chk(f) for f in (t.get("features") or []))}</ul>
      {_btn("Request a Quote →", "#contact", "g")}
    </div>"""
        for i, t in enumerate(tiers or [])
    )
    return f"""<section class="sec sec-band" id="pricing">
  <div class="wrap">
    <div class="mb6 rv">
      {_eyebrow("Services & Pricing")}
      {_h2("What We Offer", "Every project gets a tailored estimate. No surprises.")}
    </div>
    <div class="g3">{cards}</div>
    <div class="card card-plg tc rv mt4 mw-sm mx-auto">
      <h3 class="t-card mb2">Not sure what you need?</h3>
      <p class="t-small mb4">We'll assess your project and provide a transparent, no-obligation quote.</p>
      {_btn("Get a Free Estimate", "#contact")}
    </div>
  </div>
</section>"""


def _price_service_rows(tiers: List[Dict]) -> str:
    rows = "".join(
        f"""<div class="rv" style="padding:2rem 0;border-bottom:1px solid var(--c-border);">
      <div class="g2 as" style="gap:2rem;">
        <div>
          <h3 class="t-card mb1">{t.get("name","Service")}</h3>
          <p class="t-small mt1">{t.get("description","")}</p>
          <p style="font-size:1.1rem;font-weight:800;color:var(--c-accent);margin-top:0.5rem;">{t.get("price","")}</p>
        </div>
        <div>
          <ul class="chklist">{"".join(_chk(f) for f in (t.get("features") or [])[:4])}</ul>
          <div style="margin-top:1.25rem;">{_btn("Book a Consultation", "#contact")}</div>
        </div>
      </div>
    </div>"""
        for t in (tiers or [])
    )
    return f"""<section class="sec" id="pricing">
  <div class="wrap">
    <div class="mb6 rv">
      {_eyebrow("Services")}
      <h2 class="t-section">How We Can Help</h2>
      <p class="t-body mt2 mw-sm">All engagements begin with a complimentary consultation.</p>
    </div>
    {rows}
    <div class="tc mt5 rv">{_btn("Schedule a Free Consultation", "#contact")}</div>
  </div>
</section>"""


def _price_contact_only() -> str:
    return f"""<section class="sec sec-band" id="pricing">
  <div class="wrap">
    <div class="card card-plg tc mw-sm mx-auto rv">
      {_eyebrow("Pricing")}
      <h2 class="t-section mt1 mb3">Every Project Is Different</h2>
      <p class="t-body mb5">We tailor our approach to your specific needs. Get in touch for a transparent, no-obligation quote.</p>
      {_btn("Request a Quote", "#contact")}
    </div>
  </div>
</section>"""


def _chk(text: str) -> str:
    return f'<li class="chk-item"><span class="chk-icon">✓</span><span>{text}</span></li>'


# =============================================================================
# TESTIMONIALS
# =============================================================================

def _build_testimonials(tevs: List[Dict]) -> str:
    if not tevs:
        return ""
    cards = "".join(
        f"""<div class="card card-p rv d{min(i+1,4)}" style="display:flex;flex-direction:column;">
      {_stars()}
      <p class="t-small" style="font-style:italic;flex:1;margin-bottom:1.25rem;">"{tv.get("quote","")}"</p>
      <div style="display:flex;align-items:center;gap:0.75rem;border-top:1px solid var(--c-border);padding-top:1rem;">
        <div class="avatar">{(tv.get("name","?") or "?")[0].upper()}</div>
        <div>
          <p style="font-weight:700;font-size:0.875rem;color:var(--c-text);">{tv.get("name","")}</p>
          <p style="font-size:0.75rem;color:var(--c-text3);">{tv.get("role","")} · {tv.get("company","")}</p>
        </div>
      </div>
    </div>"""
        for i, tv in enumerate(tevs)
    )
    return f"""<section class="sec sec-band" id="testimonials">
  <div class="wrap">
    <div class="tc mb6 rv">
      {_eyebrow("Testimonials")}
      {_h2("What Our Clients Say")}
    </div>
    <div class="testi-grid" style="max-width:960px;margin:0 auto;">{cards}</div>
  </div>
</section>"""


# =============================================================================
# FAQ
# =============================================================================

def _build_faq(faqs: List[Dict]) -> str:
    if not faqs:
        return ""
    items = "".join(
        f"""<details class="faq rv d{min(i+1,4)}">
      <summary>{faq.get("q","")}<span class="faq-icon">+</span></summary>
      <div class="faq-body">{faq.get("a","")}</div>
    </details>"""
        for i, faq in enumerate(faqs)
    )
    return f"""<section class="sec-sm" id="faq" style="padding-top:5rem;padding-bottom:5rem;">
  <div class="wrap">
    <div class="tc mb5 rv">
      {_eyebrow("FAQ")}
      {_h2("Common Questions")}
    </div>
    <div style="max-width:640px;margin:0 auto;">{items}</div>
  </div>
</section>"""


# =============================================================================
# CONTACT
# =============================================================================

def _build_contact(name: str, d: Dict, email: str, phone: str, industry: str) -> str:
    headline = d.get("cta_headline") or "Get in Touch"
    sub      = d.get("hero", {}).get("sub") or ""
    btn_lbl  = d.get("hero", {}).get("cta") or "Send Message"
    img      = _photo_url(industry, 2, 1000)

    form_attr = f'action="mailto:{email}" enctype="text/plain"' if email else ""
    form_note = "" if email else '<p style="font-size:0.68rem;color:var(--c-text3);text-align:center;margin-top:0.75rem;">Form submission will be configured by the site owner.</p>'

    contact_items = ""
    if email:
        contact_items += f'<a href="mailto:{email}" style="display:flex;align-items:center;gap:0.5rem;font-size:0.875rem;color:var(--c-text2);">✉ {email}</a>'
    if phone:
        safe = re.sub(r'[^\d+]', '', phone)
        contact_items += f'<a href="tel:{safe}" style="display:flex;align-items:center;gap:0.5rem;font-size:0.875rem;color:var(--c-text2);">☎ {phone}</a>'
    contact_block = f'<div style="display:flex;flex-direction:column;gap:0.75rem;border-top:1px solid var(--c-border);padding-top:1rem;margin-top:1.5rem;">{contact_items}</div>' if contact_items else ""

    return f"""<section class="sec" id="contact" style="background:linear-gradient(180deg,var(--c-bg) 0%,var(--c-bg2) 100%);overflow:hidden;padding-top:6rem;padding-bottom:6rem;">
  <div class="glow-blob" style="width:600px;height:600px;top:50%;right:-10%;transform:translateY(-50%);opacity:0.6;"></div>
  <div style="position:absolute;inset:0;pointer-events:none;overflow:hidden;">
    <img src="{img}" alt="" style="width:100%;height:100%;object-fit:cover;opacity:0.04;" loading="lazy">
  </div>
  <div class="wrap z1">
    <div class="g2 as gap-xl">
      <div class="rv">
        {_eyebrow("Get in Touch")}
        <h2 class="t-section mt1">{headline}</h2>
        <p class="t-body mt3 mw-sm">{sub}</p>
        {contact_block}
      </div>
      <div class="card card-plg rv d1" style="margin-top:-1rem;">
        <form {form_attr} method="post" novalidate>
          <div class="form-row">
            <label class="form-label" for="cf-n">Your Name</label>
            <input class="form-input" type="text" id="cf-n" name="name" placeholder="Jane Smith" required autocomplete="name">
          </div>
          <div class="form-row">
            <label class="form-label" for="cf-e">Email Address</label>
            <input class="form-input" type="email" id="cf-e" name="email" placeholder="jane@example.com" required autocomplete="email">
          </div>
          <div class="form-row">
            <label class="form-label" for="cf-m">Message</label>
            <textarea class="form-input" id="cf-m" name="message" placeholder="Tell us about your project..." required></textarea>
          </div>
          <button type="submit" class="btn btn-p" style="width:100%;text-align:center;">{btn_lbl} →</button>
          {form_note}
        </form>
      </div>
    </div>
  </div>
</section>"""


# =============================================================================
# FOOTER
# =============================================================================

def _build_footer(name: str, d: Dict, nav_items: List[str], email: str, phone: str, ver: int) -> str:
    tag = d.get("tagline", "")
    sub = d.get("hero", {}).get("sub", "")
    nav_html = "".join(
        f'<li style="margin-bottom:0.45rem;"><a href="#{it.lower().replace(" ","")}" style="font-size:0.875rem;color:var(--c-text2);">{it}</a></li>'
        for it in nav_items
    )
    contact_html = ""
    if email:
        contact_html += f'<li style="margin-bottom:0.45rem;"><a href="mailto:{email}" style="font-size:0.875rem;color:var(--c-text2);">{email}</a></li>'
    if phone:
        contact_html += f'<li style="margin-bottom:0.45rem;"><a href="tel:{re.sub(chr(91)+r"^+\d"+chr(93),"",phone)}" style="font-size:0.875rem;color:var(--c-text2);">{phone}</a></li>'
    if not contact_html:
        contact_html = f'<li><a href="#contact" style="font-size:0.875rem;color:var(--c-text2);">Contact Us</a></li>'

    return f"""<footer class="site-footer">
  <div class="wrap">
    <div style="display:grid;grid-template-columns:2fr 1fr 1fr;gap:2.5rem;margin-bottom:3rem;flex-wrap:wrap;">
      <div>
        <div style="font-size:1.1rem;font-weight:900;letter-spacing:-0.03em;color:var(--c-text);margin-bottom:0.75rem;">{name}</div>
        <p style="font-size:0.875rem;color:var(--c-text2);max-width:260px;line-height:1.6;">{sub}</p>
        {f'<p style="font-size:0.75rem;color:var(--c-text3);margin-top:0.5rem;font-style:italic;">{tag}</p>' if tag else ""}
      </div>
      <div>
        <p style="font-size:0.65rem;font-weight:700;text-transform:uppercase;letter-spacing:0.15em;color:var(--c-text3);margin-bottom:1rem;">Navigate</p>
        <ul style="list-style:none;">{nav_html}</ul>
      </div>
      <div>
        <p style="font-size:0.65rem;font-weight:700;text-transform:uppercase;letter-spacing:0.15em;color:var(--c-text3);margin-bottom:1rem;">Contact</p>
        <ul style="list-style:none;">{contact_html}</ul>
      </div>
    </div>
    <div style="border-top:1px solid var(--c-border);padding-top:1.5rem;display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:0.5rem;">
      <p style="font-size:0.75rem;color:var(--c-text3);">© 2026 {name}. All rights reserved.</p>
      <p style="font-size:0.75rem;color:var(--c-text3);">v{ver}</p>
    </div>
  </div>
</footer>
<style>
@media(max-width:639px){{
  .site-footer .wrap>div:first-child{{grid-template-columns:1fr;}}
}}
</style>"""


# =============================================================================
# MASTER ARCHITECT
# =============================================================================

class MasterArchitect:

    VALID = {"hero", "trust", "features", "pricing", "testimonials", "faq", "contact"}

    def __init__(self, business_name: str, prompt: str, version: int = 1):
        raw  = (business_name or "").strip()
        prmt = (prompt or "").strip()

        extracted, clean = extract_business_name(raw, prmt)

        self.industry = detect_industry(clean or prmt)
        # CRITICAL — self.name is ALWAYS the actual business name, never prompt text
        self.name     = raw or extracted or _default_name(self.industry)
        self.prompt   = clean or prmt
        self.version  = version
        self.theme    = select_theme(self.industry)
        self.data: Dict   = {}
        self.contacts     = _extract_contact(prmt + " " + clean)

        logger.info(f"Architect | '{self.name}' | {self.industry} | {self.theme['id']}")

    # ── Section/variant selectors ─────────────────────────────────────────────

    def _hero_variant(self) -> str:
        return {
            "luxury": "centered", "agency": "centered", "beauty": "centered",
            "travel": "centered", "nonprofit": "centered",
            "finance": "stats",   "real_estate": "stats", "legal": "stats",
            "logistics": "stats", "construction": "stats",
            "restaurant": "editorial", "events": "editorial", "ecommerce": "editorial",
        }.get(self.industry, "split")

    def _feat_variant(self) -> str:
        return {
            "finance": "icon_list",   "real_estate": "icon_list",
            "legal": "icon_list",     "logistics": "icon_list",
            "construction": "icon_list",
            "saas": "cards",          "ecommerce": "cards",
            "developer": "cards",     "startup": "cards",
            "ai": "cards",            "events": "cards",
            "agency": "cards",        "luxury": "cards",
        }.get(self.industry, "alternating")

    def _price_variant(self) -> str:
        if self.industry in {"construction", "logistics", "automotive", "events"}:
            return "project"
        if self.industry in {"legal", "nonprofit"}:
            return "service_rows"
        if self.industry in {"luxury", "agency", "beauty", "finance", "real_estate",
                             "restaurant", "fitness", "travel", "nature"}:
            return "contact_only"
        return "tiers"

    # ── AI prompt ─────────────────────────────────────────────────────────────

    def _build_prompt(self) -> str:
        no_price  = {"restaurant","beauty","fitness","travel","nature","events","luxury","agency","beauty"}
        project   = {"construction","logistics","automotive"}
        service   = {"legal","nonprofit"}

        if self.industry in no_price:
            pricing = '"pricing": null,'
            pnote   = "pricing is null — this industry doesn't list prices on landing pages."
        elif self.industry in project:
            pricing = '"pricing": [{"name":"Basic","price":"From $X","description":"Entry scope.","features":["Item 1","Item 2","Item 3","Item 4","Item 5"],"featured":false},{"name":"Standard","price":"From $X","description":"Mid scope.","features":["Item 1","Item 2","Item 3","Item 4","Item 5"],"featured":true},{"name":"Large/Emergency","price":"Custom","description":"Complex scope.","features":["Item 1","Item 2","Item 3","Item 4","Item 5"],"featured":false}],'
            pnote   = "Use realistic price ranges for this industry. Replace $X with real figures."
        elif self.industry in service:
            pricing = '"pricing": [{"name":"Consultation","price":"Complimentary","description":"30-min intro call.","features":["Item 1","Item 2","Item 3","Item 4","Item 5"],"featured":false},{"name":"Engagement","price":"From $X/hr","description":"Project work.","features":["Item 1","Item 2","Item 3","Item 4","Item 5"],"featured":true},{"name":"Retainer","price":"Custom/mo","description":"Ongoing.","features":["Item 1","Item 2","Item 3","Item 4","Item 5"],"featured":false}],'
            pnote   = "Fill in realistic rates for this professional services firm."
        else:
            pricing = '"pricing": [{"name":"Starter","price":"$X/mo","description":"For individuals.","features":["Item 1","Item 2","Item 3","Item 4","Item 5"],"featured":false},{"name":"Pro","price":"$X/mo","description":"For growing teams.","features":["Item 1","Item 2","Item 3","Item 4","Item 5"],"featured":true},{"name":"Enterprise","price":"Custom","description":"For large orgs.","features":["Item 1","Item 2","Item 3","Item 4","Item 5"],"featured":false}],'
            pnote   = "Fill in realistic SaaS prices for this market."

        default_sections = {
            "construction": '["hero","trust","features","pricing","testimonials","faq","contact"]',
            "restaurant":   '["hero","trust","features","testimonials","contact"]',
            "beauty":       '["hero","trust","features","testimonials","faq","contact"]',
            "legal":        '["hero","trust","features","pricing","faq","contact"]',
            "nonprofit":    '["hero","features","testimonials","faq","contact"]',
            "fitness":      '["hero","trust","features","testimonials","faq","contact"]',
        }.get(self.industry, '["hero","trust","features","pricing","testimonials","faq","contact"]')

        return f"""Write landing page copy for "{self.name}", a {self.industry} business.
Context: {self.prompt}

RULES (non-negotiable):
1. Tone: skilled human copywriter. Industry-specific language only.
   Construction → "builds, installs, delivers" NOT "empowers/solutions"
   Legal → "advises, represents, counsels"
   Restaurant → "crafts, prepares, serves"
   Fitness → "trains, coaches, transforms"
2. Hero h1: a real brand tagline, 5-9 words max. NOT "Your Trusted Partner in X".
3. Stats: realistic for a real business this size. No exaggeration.
4. Trust badges: actual industry credentials (OSHA, Bar Association, etc.)
5. Testimonials: specific outcome + real-sounding names. NOT "great service!"
6. FAQ: questions real customers of THIS exact industry ask, with honest answers.
7. {pnote}
8. contact_email/contact_phone: only fill if explicitly given in context. Otherwise "".

Return ONLY valid JSON. No markdown code fences, no explanatory text, no comments:
{{
  "sections": {default_sections},
  "nav": ["4 nav labels matching section anchors"],
  "hero": {{
    "h1": "Real tagline for {self.name} (5–9 words)",
    "sub": "One-sentence value prop in plain language (max 20 words)",
    "cta": "Action label (e.g. Request a Quote / Book a Table / Start Free Trial)"
  }},
  "tagline": "2–4 word brand slogan",
  "social_proof": {{"count": "e.g. 350+", "label": "e.g. homes renovated"}},
  "stats": [
    {{"value": "figure", "label": "what it is"}},
    {{"value": "figure", "label": "what it is"}},
    {{"value": "figure", "label": "what it is"}},
    {{"value": "figure", "label": "what it is"}}
  ],
  "trust_badges": ["Real cred 1","Real cred 2","Real cred 3","Real cred 4"],
  "features": [
    {{"title": "Specific benefit", "description": "2 concrete sentences about what {self.name} does.", "icon": "1 emoji"}},
    {{"title": "Specific benefit", "description": "2 concrete sentences.", "icon": "1 emoji"}},
    {{"title": "Specific benefit", "description": "2 concrete sentences.", "icon": "1 emoji"}}
  ],
  {pricing}
  "testimonials": [
    {{"name": "Full Name", "role": "Job Title", "company": "Company or City", "quote": "Specific result, max 2 sentences."}},
    {{"name": "Full Name", "role": "Job Title", "company": "Company or City", "quote": "Specific result."}}
  ],
  "faq": [
    {{"q": "Real question?", "a": "Honest answer."}},
    {{"q": "Real question?", "a": "Answer."}},
    {{"q": "Real question?", "a": "Answer."}}
  ],
  "cta_headline": "Industry-specific closing headline",
  "contact_email": "",
  "contact_phone": ""
}}"""

    # ── Data fetching ─────────────────────────────────────────────────────────

    def _get_data(self) -> Dict:
        if not AI_AVAILABLE:
            return self._fallback()
        try:
            raw     = chat_completion(
                system="You are an expert copywriter. Return ONLY valid JSON. No markdown, no backticks, no commentary.",
                user=self._build_prompt(),
                temperature=0.72,
            )
            cleaned = re.sub(r'^```(?:json)?\s*|```\s*$', '', raw.strip(), flags=re.MULTILINE).strip()
            data    = json.loads(cleaned)
            if not data.get("contact_email") and self.contacts.get("email"):
                data["contact_email"] = self.contacts["email"]
            if not data.get("contact_phone") and self.contacts.get("phone"):
                data["contact_phone"] = self.contacts["phone"]
            return data
        except Exception as e:
            logger.error(f"AI data error: {e}")
            return self._fallback()

    def _fallback(self) -> Dict:
        base = {
            "contact_email": self.contacts.get("email", ""),
            "contact_phone": self.contacts.get("phone", ""),
        }
        if self.industry == "construction":
            return {**base,
                "sections": ["hero","trust","features","pricing","testimonials","faq","contact"],
                "nav": ["Services","Projects","About","Contact"],
                "hero": {"h1": f"{self.name} — Built Right, On Time", "sub": "Quality construction and renovation by certified tradespeople, delivered on schedule.", "cta": "Request a Quote"},
                "tagline": "Built to last.",
                "social_proof": {"count": "350+", "label": "projects completed"},
                "stats": [{"value":"98%","label":"On-time delivery"},{"value":"350+","label":"Projects"},{"value":"15yr","label":"Experience"},{"value":"24/7","label":"Emergency"}],
                "trust_badges": ["Licensed & Insured","OSHA Compliant","Bonded","Satisfaction Guaranteed"],
                "features": [
                    {"title":"Licensed & Fully Insured","description":"Every project carries comprehensive liability and workers compensation coverage. You are protected from day one.","icon":"🛡️"},
                    {"title":"On-Time, On-Budget","description":"Fixed-price quotes and written schedules before work starts. No surprise charges on your final invoice.","icon":"📋"},
                    {"title":"All Trades Under One Roof","description":"From groundwork to finishing, certified tradespeople handle every phase so you only deal with one team.","icon":"🔨"},
                ],
                "pricing": [
                    {"name":"Residential","price":"From $2,500","description":"Home renovations and repairs.","features":["Free on-site estimate","Kitchen & bath remodels","Roofing & siding","Flooring & painting","Post-job inspection"],"featured":False},
                    {"name":"Commercial","price":"From $12,000","description":"Business fit-outs.","features":["Dedicated project manager","Office & retail fit-outs","Compliance documentation","Progress reporting","2-year warranty"],"featured":True},
                    {"name":"Emergency","price":"24/7 Response","description":"Urgent repairs.","features":["Same-day response","Storm & water damage","Structural emergencies","Insurance billing","Temporary securing"],"featured":False},
                ],
                "testimonials": [
                    {"name":"Michael Torres","role":"Homeowner","company":"Brooklyn, NY","quote":"Full kitchen renovation done in three weeks, under budget. The crew was professional every single day."},
                    {"name":"Lisa Chen","role":"Property Manager","company":"Manhattan","quote":"We use them across six buildings. Always reliable, always honest about what things cost."},
                ],
                "faq": [
                    {"q":"Are you licensed and insured?","a":"Yes — fully licensed, bonded, and carrying comprehensive liability and workers compensation on every job."},
                    {"q":"Do you provide free estimates?","a":"Yes. We visit the site, assess the scope, and provide a detailed written quote at no cost."},
                    {"q":"How do you handle project timelines?","a":"We issue a written schedule before work begins and send progress updates at each milestone."},
                ],
                "cta_headline": f"Start your project with {self.name}",
            }
        return {**base,
            "sections": ["hero","trust","features","testimonials","faq","contact"],
            "nav": ["Services","About","FAQ","Contact"],
            "hero": {"h1": f"Welcome to {self.name}", "sub": "Professional services built around your exact needs.", "cta": "Get Started"},
            "tagline": "Excellence delivered.",
            "social_proof": {"count": "500+", "label": "clients served"},
            "stats": [{"value":"97%","label":"Satisfaction"},{"value":"500+","label":"Completed"},{"value":"10yr","label":"Experience"},{"value":"24/7","label":"Support"}],
            "trust_badges": ["Certified","Award Winner 2024","5-Star Rated","Trusted"],
            "features": [
                {"title":"Expert Team","description":"Seasoned professionals with deep domain knowledge committed to results that move the needle.","icon":"◆"},
                {"title":"Proven Results","description":"Hundreds of successful engagements across a wide range of industries and client types.","icon":"▲"},
                {"title":"Dedicated Support","description":"A team that responds quickly and keeps you informed at every step of the process.","icon":"●"},
            ],
            "pricing": None,
            "testimonials": [
                {"name":"Jordan Lee","role":"Director","company":"Meridian Group","quote":"Results were measurable within the first month. Genuinely changed how we operate."},
                {"name":"Priya Nair","role":"Founder","company":"Spark Ventures","quote":"Responsive, knowledgeable, and invested in our success. Highly recommend."},
            ],
            "faq": [
                {"q":"How do I get started?","a":"Fill out the contact form and we'll schedule an initial call to understand your needs."},
                {"q":"What does the process look like?","a":"Discovery first, then a tailored plan, then execution with full transparency."},
                {"q":"Do you offer ongoing support?","a":"Yes — all engagements include continued access to our team after the project is complete."},
            ],
            "cta_headline": f"Ready to work with {self.name}?",
        }

    # ── Main build ─────────────────────────────────────────────────────────────

    def build(self) -> Dict[str, Any]:
        try:
            d    = self._get_data()
            self.data = d
            t    = self.theme
            name = self.name   # ALWAYS self.name — never d["hero"]["h1"] or prompt

            email = d.get("contact_email", "")
            phone = d.get("contact_phone", "")

            # Determine section order
            raw_secs = d.get("sections") or list(self.VALID)
            ordered, seen = [], set()
            for s in raw_secs:
                sid = str(s).lower().strip()
                if sid in self.VALID and sid not in seen:
                    ordered.append(sid); seen.add(sid)
            if "hero"    not in seen: ordered.insert(0, "hero")
            if "contact" not in seen: ordered.append("contact")

            nav_items = d.get("nav") or ["Services","About","FAQ","Contact"]
            cta_lbl   = d.get("hero", {}).get("cta", "Get Started")

            # Build each section
            parts = [_build_nav(name, nav_items, cta_lbl)]

            for sid in ordered:
                html = ""
                if sid == "hero":
                    v = self._hero_variant()
                    if v == "centered":   html = _hero_centered(name, d, self.industry)
                    elif v == "stats":    html = _hero_stats(name, d, self.industry)
                    elif v == "editorial":html = _hero_editorial(name, d, self.industry)
                    else:                 html = _hero_split(name, d, self.industry)

                elif sid == "trust":
                    html = _build_trust(d.get("trust_badges") or [])

                elif sid == "features":
                    feats = d.get("features") or []
                    if feats:
                        v = self._feat_variant()
                        if v == "icon_list":    html = _feat_icon_list(feats, self.industry)
                        elif v == "alternating":html = _feat_alternating(feats, self.industry)
                        else:                   html = _feat_cards(feats)

                elif sid == "pricing":
                    tiers = d.get("pricing")
                    if tiers:
                        v = self._price_variant()
                        if v == "project":       html = _price_project(tiers)
                        elif v == "service_rows":html = _price_service_rows(tiers)
                        else:                    html = _price_tiers(tiers)
                    else:
                        html = _price_contact_only()

                elif sid == "testimonials":
                    html = _build_testimonials(d.get("testimonials") or [])

                elif sid == "faq":
                    html = _build_faq(d.get("faq") or [])

                elif sid == "contact":
                    html = _build_contact(name, d, email, phone, self.industry)

                if html:
                    parts.append(html)

            parts.append(_build_footer(name, d, nav_items, email, phone, self.version))

            body = "\n".join(parts)

            # Final HTML — note: NO <head> or <title> here.
            # The renderer injects this into a div, so head tags are stripped.
            # Business name / page title is set by the calling route.
            css_block = _page_css(t)
            page = f"""{css_block}
<div style="padding-top:64px;">
{body}
{REVEAL_JS}
</div>"""

            meta = {
                "business_name": name,
                "industry":      self.industry,
                "theme":         t["id"],
                "version":       self.version,
                "sections":      ordered,
                "hero_variant":  self._hero_variant(),
                "feat_variant":  self._feat_variant(),
                "price_variant": self._price_variant(),
                "has_email":     bool(email),
                "has_phone":     bool(phone),
                "status":        "success",
            }
            logger.info(f"Built '{name}' | {self.industry} | {t['id']} | {ordered}")
            return {"html": page, "metadata": meta}

        except Exception as e:
            logger.error(f"Build error: {e}", exc_info=True)
            return {
                "html": f'<div style="padding:2rem;font-family:sans-serif;color:#ef4444;">Build failed: {e}</div>',
                "metadata": {"status": "error", "error": str(e)},
            }


# =============================================================================
# PUBLIC API  (matches existing route calls)
# =============================================================================

def generate_ai_plan(ai_input: Dict[str, Any], version: int = 1) -> Dict[str, Any]:
    """
    Main entry point used by dashboard_websites_routes.py:
        generate_ai_plan(ai_input={"business_name": ..., "prompt": ...}, version=1)
    Returns {"html": str, "metadata": dict}
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
            user=f"""Rewrite this text in 3 different {tone} variations.
Business context: {business_context}
Original: {original_text}
Return: ["variation1","variation2","variation3"]""",
            temperature=0.8,
        )
        cleaned = re.sub(r'^```(?:json)?\s*|```\s*$', '', raw.strip(), flags=re.MULTILINE).strip()
        result  = json.loads(cleaned)
        if isinstance(result, list):
            return result[:3]
    except Exception:
        pass
    return [original_text, original_text, original_text]


def get_design_tokens(theme_id: str = "blue") -> Dict[str, Any]:
    """Return CSS variable map for a theme — used by the editor."""
    t = THEMES.get(theme_id, THEMES["blue"])
    return {
        "theme_id":    t["id"],
        "mode":        t["mode"],
        "font_family": t["font_family"],
        "css_vars":    t["vars"],
    }