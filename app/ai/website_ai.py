import random
import hashlib
import re
import json
from typing import Dict, Any, List, Tuple

from app.ai.openai_client import chat_completion  # adjust if your helper is elsewhere


# ======================================================
# ALLOWED FRONTEND SCHEMA (MUST MATCH aiStructure.ts)
# ======================================================

HERO_VARIANTS = ["split_image", "centered_text", "image_background", "minimal"]

SECTION_SETS = {
    "restaurant": [
        ["about", "services", "testimonial", "cta"],
        ["services", "process", "testimonial", "cta"],
        ["trust", "services", "testimonial", "cta"],
        ["about", "trust", "services", "cta"],
    ],
    "business": [
        ["about", "services", "cta"],
        ["services", "process", "testimonial", "cta"],
        ["trust", "services", "cta"],
        ["about", "trust", "services", "testimonial", "cta"],
    ],
}

THEMES = [
    {"palette": "light", "accent": "indigo"},
    {"palette": "light", "accent": "orange"},
    {"palette": "dark", "accent": "indigo"},
    {"palette": "dark", "accent": "emerald"},
    {"palette": "light", "accent": "neutral"},
]

FOOTER_VARIANTS = [{"variant": "minimal"}, {"variant": "standard"}]


# ======================================================
# INTENT DETECTION (CHEAP + DETERMINISTIC)
# ======================================================

_RE_WORD = re.compile(r"[a-z0-9]+", re.I)

RESTAURANT_KEYWORDS = [
    "restaurant", "cafe", "pizza", "burger", "sushi", "thai", "italian", "menu", "dine-in", "takeaway", "delivery"
]

BUSINESS_BUCKETS: List[Tuple[str, List[str], str, List[str]]] = [
    (
        "car",
        ["car", "auto", "detailing", "dealership", "wrap", "tint", "ceramic", "polish", "used cars", "financing"],
        "Book a service",
        ["Interior & exterior detailing", "Paint correction & protection", "Quick turnaround"],
    ),
    (
        "gym",
        ["gym", "fitness", "training", "bjj", "boxing", "muay thai", "mma", "pt", "personal trainer"],
        "Book a trial",
        ["Beginner-friendly classes", "Personal coaching", "Flexible memberships"],
    ),
    (
        "agency",
        ["agency", "marketing", "ads", "seo", "branding", "content", "creative", "funnels"],
        "Get a free audit",
        ["Growth strategy", "Ads & creatives", "Landing pages that convert"],
    ),
    (
        "construction",
        ["construction", "builder", "renovation", "remodel", "plumbing", "electric", "roof", "handyman"],
        "Request a quote",
        ["On-site estimate", "Clear pricing", "Reliable workmanship"],
    ),
    (
        "beauty",
        ["salon", "barber", "hair", "nails", "spa", "massage", "lashes", "skincare"],
        "Book now",
        ["High-quality treatments", "Friendly atmosphere", "Easy booking"],
    ),
    (
        "professional",
        ["law", "lawyer", "attorney", "accounting", "tax", "consulting", "broker", "real estate"],
        "Schedule a consultation",
        ["Expert guidance", "Clear next steps", "Fast response"],
    ),
    (
        "tech",
        ["saas", "software", "app", "platform", "ai", "automation", "tool", "startup"],
        "Start free trial",
        ["Product overview", "Simple onboarding", "Fast support"],
    ),
]

GENERIC_SERVICES = ["Professional service", "Fast response", "Trusted quality"]


def _words(text: str) -> List[str]:
    return [w.lower() for w in _RE_WORD.findall(text or "")]


def infer_intent(ai_input: Dict[str, Any]) -> Dict[str, Any]:
    prompt = (ai_input.get("prompt") or "").strip()
    combined = prompt.lower()
    w = _words(prompt)

    template = "restaurant" if any(k in combined for k in RESTAURANT_KEYWORDS) else "business"

    industry = "generic"
    services = GENERIC_SERVICES[:]
    goal = "Get started"

    # pick first matching bucket (deterministic)
    for bucket, keywords, default_goal, default_services in BUSINESS_BUCKETS:
        if any(k in combined for k in keywords):
            industry = bucket
            goal = default_goal
            services = default_services[:]
            break

    name = (ai_input.get("business_name") or "").strip()
    if not name and w:
        name = " ".join(word.title() for word in w[:2])

    if template == "restaurant":
        if not services or services == GENERIC_SERVICES:
            services = ["Signature dishes", "Fresh ingredients", "Takeaway & dine-in"]
        if not goal:
            goal = "Reserve a table"

    return {
        "template": template,
        "industry": industry,
        "services": services,
        "primary_goal": goal,
        "business_name": name,
        "raw_prompt": prompt,
    }


# ======================================================
# DETERMINISTIC STRUCTURE
# ======================================================

def stable_seed(*values: str) -> int:
    raw = "|".join(values)
    return int(hashlib.sha256(raw.encode()).hexdigest()[:8], 16)


def generate_ai_structure(business_type: str, goal: str, version: int = 1):
    """
    Generates an intelligent page structure.
    AI decides:
    - which sections exist
    - how many sections are needed
    - visual theme + accent
    Deterministic: same input => same output
    """

    rng = random.Random(stable_seed(business_type, goal, str(version)))

    bt = (business_type or "business").lower()
    g = (goal or "").lower()

    # -------------------------------------------------
    # CORE SECTIONS (ALWAYS PRESENT)
    # -------------------------------------------------
    sections: list[str] = ["hero"]

    # CTA should exist, but may move to footer visually
    sections.append("cta")

    # -------------------------------------------------
    # GOAL-DRIVEN SECTIONS (HIGH PRIORITY)
    # -------------------------------------------------
    if any(w in g for w in ["lead", "contact", "quote", "call"]):
        sections += ["trust", "contact"]

    if any(w in g for w in ["book", "booking", "appointment", "reserve"]):
        sections += ["process", "contact"]

    if any(w in g for w in ["sell", "order", "buy", "pricing"]):
        sections += ["services", "faq"]

    # -------------------------------------------------
    # BUSINESS-TYPE SECTIONS (CONTEXT)
    # -------------------------------------------------
    if bt in ["restaurant", "cafe", "coffee", "food"]:
        sections += ["services", "gallery", "location"]

    elif bt in ["agency", "consultant", "coach"]:
        sections += ["about", "process", "testimonial"]

    elif bt in ["local service", "service", "plumbing", "cleaning", "electrician"]:
        sections += ["services", "trust", "faq"]

    elif bt in ["nonprofit", "charity", "community"]:
        sections += ["about", "highlight", "trust"]

    else:
        # generic business
        sections += ["about", "services"]

    # -------------------------------------------------
    # OPTIONAL SECTIONS (AI JUDGMENT, NOT RANDOM)
    # -------------------------------------------------
    optional_pool = [
        "testimonial",
        "faq",
        "process",
        "highlight",
        "gallery",
    ]

    # Score optional sections by relevance
    scored: list[tuple[str, int]] = []

    for sec in optional_pool:
        score = 0

        if sec == "testimonial" and "trust" in sections:
            score += 2

        if sec == "faq" and any(w in g for w in ["sell", "pricing", "order"]):
            score += 2

        if sec == "process" and any(w in g for w in ["book", "contact", "lead"]):
            score += 2

        if sec == "gallery" and bt in ["restaurant", "food", "creative"]:
            score += 2

        if sec == "highlight":
            score += 1  # generic value booster

        if score > 0:
            scored.append((sec, score))

    # Sort by relevance, stable + deterministic
    scored.sort(key=lambda x: (-x[1], x[0]))

    # Add at most 2 optional sections
    for sec, _ in scored[:2]:
        if sec not in sections:
            sections.append(sec)

    # -------------------------------------------------
    # CLEANUP + ORDER
    # -------------------------------------------------
    seen = set()
    ordered_sections: list[str] = []
    for s in sections:
        if s not in seen:
            seen.add(s)
            ordered_sections.append(s)

    # Hard cap (prevents bloated AI pages)
    MAX_SECTIONS = 7
    ordered_sections = ordered_sections[:MAX_SECTIONS]

    # -------------------------------------------------
    # VISUAL THEME (CRITICAL FIX)
    # -------------------------------------------------
    theme = {
        "palette": rng.choice(["dark", "dark-soft", "midnight"]),
        "accent": rng.choice(["indigo", "emerald", "cyan", "violet"]),
        "radius": "lg",
        "density": "comfortable",
    }

    # -------------------------------------------------
    # FINAL STRUCTURE
    # -------------------------------------------------
    return {
        "hero": {
            "variant": rng.choice(HERO_VARIANTS),
        },
        "sections": ordered_sections,
        "theme": theme,
        "footer": rng.choice(FOOTER_VARIANTS),
    }


# ======================================================
# 🚀 REAL AI CONTENT GENERATION (WARM + FULL PAGE)
# ======================================================

CONTENT_SYSTEM_PROMPT = """
You are an expert conversion-focused website copywriter and creative director.

Generate a READY-TO-PUBLISH website content JSON.
Rules:
- Do NOT ask questions.
- Do NOT use placeholders (no "Add your...", no brackets).
- Make confident assumptions based on the business description.
- Write warm, human, industry-specific copy.
- Keep it simple, clear, and believable.
- Avoid hype. Sound like a real business.
- Output STRICT JSON only. No markdown. No commentary.
"""

# We intentionally include extra keys the renderer can choose to use:
# - trust, process, faq, highlight, audience
# - image_slots + optional per-section image objects (null if unused)
CONTENT_USER_PROMPT = """
Business description (free text):
{prompt}

Business name:
{business_name}

Template:
{template}

Industry bucket:
{industry}

Primary goal (CTA intent):
{goal}

Return STRICT JSON ONLY with this exact shape:

{{
  "business_name": "",
  "tagline": "",
  "hero": {{
    "headline": "",
    "subheadline": "",
    "cta_text": "",
    "image": null
  }},
  "highlight": {{
    "headline": "",
    "subheadline": ""
  }},
  "about": {{
    "title": "",
    "paragraphs": []
  }},
  "trust": {{
    "title": "",
    "items": []
  }},
  "services": {{
    "title": "",
    "items": [
      {{
        "title": "",
        "description": "",
        "image": null
      }}
    ]
  }},
  "process": {{
    "title": "",
    "steps": [
      {{
        "title": "",
        "description": ""
      }}
    ]
  }},
  "testimonial": {{
    "quote": "",
    "author": ""
  }},
  "faq": {{
    "title": "",
    "items": [
      {{
        "q": "",
        "a": ""
      }}
    ]
  }},
  "cta": {{
    "headline": "",
    "subheadline": "",
    "button": ""
  }},
  "contact": {{
    "phone": "",
    "email": "",
    "address": ""
  }},
  "footer": {{
    "tagline": ""
  }},
  "image_slots": [
    {{
      "id": "hero",
      "label": "Hero image",
      "recommended_prompt": "",
      "placement": "hero",
      "aspect_ratio": "16:9",
      "optional": true
    }}
  ],
  "ai_todos": []
}}

Important:
- contact fields MUST be empty strings.
- image fields MUST be either null or a string URL (but you can set them to null).
- image_slots should propose 3 to 8 good places for images for this business type.
- ai_todos should be short and practical (5 to 10 items max).
"""


def _coerce_content_minimums(intent: Dict[str, Any], content: Dict[str, Any]) -> Dict[str, Any]:
    """
    Ensure no critical keys are missing / wrong type.
    Keeps older/newer model output safe.
    """
    bn = (content.get("business_name") or "").strip() or (intent.get("business_name") or "").strip() or "Your Business"
    goal = (intent.get("primary_goal") or "Get started").strip()

    # Basic structure
    content.setdefault("business_name", bn)
    content.setdefault("tagline", "")

    content.setdefault("hero", {})
    content["hero"].setdefault("headline", bn)
    content["hero"].setdefault("subheadline", "A simple, reliable solution for customers who want it done right.")
    content["hero"].setdefault("cta_text", goal)
    if "image" not in content["hero"]:
        content["hero"]["image"] = None

    content.setdefault("highlight", {})
    content["highlight"].setdefault("headline", "Simple, fast, and done right.")
    content["highlight"].setdefault("subheadline", "Clear communication, quality work, and a great experience end-to-end.")

    content.setdefault("about", {})
    content["about"].setdefault("title", "About")
    if not isinstance(content["about"].get("paragraphs"), list):
        content["about"]["paragraphs"] = []
    if len(content["about"]["paragraphs"]) == 0:
        content["about"]["paragraphs"] = [
            "We focus on doing the basics extremely well: quality work, clear pricing, and a smooth experience.",
            "From the first message to the final result, we keep things simple, honest, and dependable.",
        ]

    content.setdefault("trust", {})
    content["trust"].setdefault("title", "Why choose us")
    if not isinstance(content["trust"].get("items"), list) or len(content["trust"]["items"]) == 0:
        content["trust"]["items"] = [
            "Fast response and clear next steps",
            "Quality you can see and feel",
            "No surprises — just honest work",
        ]

    content.setdefault("services", {})
    content["services"].setdefault("title", "Services")
    if not isinstance(content["services"].get("items"), list) or len(content["services"]["items"]) == 0:
        content["services"]["items"] = [
            {"title": s, "description": "Delivered with care and attention to detail.", "image": None}
            for s in (intent.get("services") or GENERIC_SERVICES)
        ]
    else:
        # ensure service items have image key
        for it in content["services"]["items"]:
            if isinstance(it, dict) and "image" not in it:
                it["image"] = None

    content.setdefault("process", {})
    content["process"].setdefault("title", "How it works")
    if not isinstance(content["process"].get("steps"), list) or len(content["process"]["steps"]) == 0:
        content["process"]["steps"] = [
            {"title": "Reach out", "description": "Send a short message about what you need."},
            {"title": "Get a plan", "description": "We reply with clear options and next steps."},
            {"title": "Get it done", "description": "We deliver quickly, cleanly, and professionally."},
        ]

    content.setdefault("testimonial", {})
    content["testimonial"].setdefault("quote", "“Professional, fast, and easy to work with.”")
    content["testimonial"].setdefault("author", "Happy customer")

    content.setdefault("faq", {})
    content["faq"].setdefault("title", "FAQ")
    if not isinstance(content["faq"].get("items"), list) or len(content["faq"]["items"]) == 0:
        content["faq"]["items"] = [
            {"q": "How fast can I get started?", "a": "Usually the same day — send a message and we’ll take it from there."},
            {"q": "Do you offer flexible options?", "a": "Yes. We tailor it to what you actually need, without overcomplicating things."},
            {"q": "Can I make changes later?", "a": "Absolutely. You can update details anytime."},
        ]

    content.setdefault("cta", {})
    content["cta"].setdefault("headline", "Ready to get started?")
    content["cta"].setdefault("subheadline", "Send a message and we’ll respond quickly with the next step.")
    content["cta"].setdefault("button", goal)

    # Contact MUST be empty strings
    content.setdefault("contact", {})
    content["contact"]["phone"] = ""
    content["contact"]["email"] = ""
    content["contact"]["address"] = ""

    content.setdefault("footer", {})
    content["footer"].setdefault("tagline", f"{bn} — built for results.")

    # Image slots
    slots = content.get("image_slots")
    if not isinstance(slots, list) or len(slots) == 0:
        content["image_slots"] = [
            {
                "id": "hero",
                "label": "Hero image",
                "recommended_prompt": f"high quality photo that fits {intent.get('raw_prompt','').strip()}",
                "placement": "hero",
                "aspect_ratio": "16:9",
                "optional": True,
            },
            {
                "id": "about",
                "label": "About image",
                "recommended_prompt": "warm, authentic photo of the team or the workspace",
                "placement": "about",
                "aspect_ratio": "4:3",
                "optional": True,
            },
            {
                "id": "services_1",
                "label": "Service image 1",
                "recommended_prompt": "high quality photo showing the service in action",
                "placement": "services",
                "aspect_ratio": "1:1",
                "optional": True,
            },
        ]

    # Todos
    todos = content.get("ai_todos")
    if not isinstance(todos, list):
        todos = []
    if len(todos) == 0:
        content["ai_todos"] = [
            "Add phone number",
            "Add email address",
            "Add address or city",
            "Add 1–3 real photos",
            "Tweak the hero headline to match your exact offer",
        ]
    else:
        content["ai_todos"] = [str(t) for t in todos][:10]

    return content


def generate_publishable_content(intent: Dict[str, Any]) -> Dict[str, Any]:
    try:
        response = chat_completion(
            system=CONTENT_SYSTEM_PROMPT,
            user=CONTENT_USER_PROMPT.format(
                prompt=intent["raw_prompt"],
                business_name=intent["business_name"],
                goal=intent["primary_goal"],
                industry=intent["industry"],
                template=intent["template"],
            ),
            temperature=0.8,
        )
        parsed = json.loads(response)
        return _coerce_content_minimums(intent, parsed)
    except Exception:
        # Fallback (never blank, still warm)
        bn = (intent.get("business_name") or "Your Business").strip() or "Your Business"
        goal = (intent.get("primary_goal") or "Get started").strip() or "Get started"

        fallback = {
            "business_name": bn,
            "tagline": "Simple, reliable service — done right.",
            "hero": {
                "headline": bn,
                "subheadline": "Clear communication, quality work, and a smooth experience from start to finish.",
                "cta_text": goal,
                "image": None,
            },
            "highlight": {
                "headline": "Warm service. Real results.",
                "subheadline": "We keep it simple — and we deliver what we promise.",
            },
            "about": {
                "title": "About",
                "paragraphs": [
                    "We focus on what customers actually want: a clear plan, great quality, and zero hassle.",
                    "Whether it’s your first time or you’ve tried other options before, we make the process easy.",
                ],
            },
            "trust": {
                "title": "Why choose us",
                "items": [
                    "Fast response and clear next steps",
                    "Quality you can see and feel",
                    "Honest pricing and no surprises",
                ],
            },
            "services": {
                "title": "Services",
                "items": [
                    {"title": s, "description": "Delivered with care and attention to detail.", "image": None}
                    for s in (intent.get("services") or GENERIC_SERVICES)
                ],
            },
            "process": {
                "title": "How it works",
                "steps": [
                    {"title": "Reach out", "description": "Send a short message about what you need."},
                    {"title": "Get a plan", "description": "We reply with clear options and next steps."},
                    {"title": "Get it done", "description": "We deliver quickly, cleanly, and professionally."},
                ],
            },
            "testimonial": {
                "quote": "“Professional, fast, and easy to work with.”",
                "author": "Happy customer",
            },
            "faq": {
                "title": "FAQ",
                "items": [
                    {"q": "How fast can I get started?", "a": "Usually the same day — send a message and we’ll take it from there."},
                    {"q": "Do you offer flexible options?", "a": "Yes. We tailor it to what you actually need, without overcomplicating things."},
                    {"q": "Can I update the site later?", "a": "Absolutely — you can edit anytime."},
                ],
            },
            "cta": {
                "headline": "Ready to get started?",
                "subheadline": "Send a message and we’ll respond quickly with the next step.",
                "button": goal,
            },
            "contact": {"phone": "", "email": "", "address": ""},
            "footer": {"tagline": f"{bn} — built for results."},
            "image_slots": [
                {
                    "id": "hero",
                    "label": "Hero image",
                    "recommended_prompt": "high quality hero photo that fits the business",
                    "placement": "hero",
                    "aspect_ratio": "16:9",
                    "optional": True,
                },
                {
                    "id": "about",
                    "label": "About image",
                    "recommended_prompt": "warm photo of team, workspace, or product",
                    "placement": "about",
                    "aspect_ratio": "4:3",
                    "optional": True,
                },
                {
                    "id": "services_1",
                    "label": "Service image 1",
                    "recommended_prompt": "photo showing the service in action",
                    "placement": "services",
                    "aspect_ratio": "1:1",
                    "optional": True,
                },
            ],
            "ai_todos": [
                "Add phone number",
                "Add email address",
                "Add address or city",
                "Add 1–3 real photos",
            ],
        }

        return _coerce_content_minimums(intent, fallback)


# ======================================================
# ONE STOP ENTRY (USED BY DASHBOARD)
# ======================================================

def generate_ai_plan(ai_input: Dict[str, Any], version: int = 1) -> Dict[str, Any]:
    intent = infer_intent(ai_input)

    structure = generate_ai_structure(
        business_type=intent["template"],
        goal=intent["primary_goal"],
        version=version,
    )

    content = generate_publishable_content(intent)

    return {
        "template": intent["template"],
        "intent": intent,
        "structure": structure,
        "content": content,
    }
