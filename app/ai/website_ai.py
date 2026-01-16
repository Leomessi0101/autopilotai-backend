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
    ],
    "business": [
        ["about", "services", "cta"],
        ["services", "process", "testimonial", "cta"],
    ],
}

THEMES = [
    {"palette": "light", "accent": "indigo"},
    {"palette": "dark", "accent": "indigo"},
]

FOOTER_VARIANTS = [{"variant": "minimal"}, {"variant": "standard"}]


# ======================================================
# INTENT DETECTION (UNCHANGED)
# ======================================================

_RE_WORD = re.compile(r"[a-z0-9]+", re.I)

RESTAURANT_KEYWORDS = [
    "restaurant", "cafe", "pizza", "burger", "sushi", "thai", "italian",
]

BUSINESS_BUCKETS: List[Tuple[str, List[str], str]] = [
    ("car", ["car", "auto", "detailing", "dealership"], "Book a service"),
    ("gym", ["gym", "fitness", "training", "bjj", "boxing"], "Book a trial"),
    ("agency", ["agency", "marketing", "ads", "seo"], "Get a free audit"),
    ("tech", ["saas", "software", "app", "platform", "ai"], "Start free trial"),
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

    for bucket, keywords, default_goal in BUSINESS_BUCKETS:
        if any(k in combined for k in keywords):
            industry = bucket
            goal = default_goal
            break

    name = ai_input.get("business_name") or ""
    if not name and w:
        name = " ".join(word.title() for word in w[:2])

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
    rng = random.Random(stable_seed(business_type, goal, str(version)))

    return {
        "hero": {"variant": rng.choice(HERO_VARIANTS)},
        "sections": rng.choice(SECTION_SETS[business_type]),
        "theme": rng.choice(THEMES),
        "footer": rng.choice(FOOTER_VARIANTS),
    }


# ======================================================
# 🚀 REAL AI CONTENT GENERATION (NEW)
# ======================================================

CONTENT_SYSTEM_PROMPT = """
You are an expert website copywriter.

Generate a READY-TO-PUBLISH business website.
Do NOT ask questions.
Do NOT use placeholders.
Make confident assumptions.
Assume the user will publish immediately.
"""

CONTENT_USER_PROMPT = """
Business description:
{prompt}

Business name:
{business_name}

Primary goal:
{goal}

Industry:
{industry}

Return STRICT JSON ONLY with this shape:

{{
  "hero": {{
    "headline": "",
    "subheadline": "",
    "cta": ""
  }},
  "about": {{
    "paragraphs": []
  }},
  "services": {{
    "title": "",
    "items": [
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
  "cta": {{
    "headline": "",
    "subheadline": "",
    "button": ""
  }},
  "footer": {{
    "tagline": ""
  }}
}}
"""


def generate_publishable_content(intent: Dict[str, Any]) -> Dict[str, Any]:
    try:
        response = chat_completion(
            system=CONTENT_SYSTEM_PROMPT,
            user=CONTENT_USER_PROMPT.format(
                prompt=intent["raw_prompt"],
                business_name=intent["business_name"],
                goal=intent["primary_goal"],
                industry=intent["industry"],
            ),
            temperature=0.7,
        )
        return json.loads(response)
    except Exception:
        # Fallback (never blank)
        return {
            "hero": {
                "headline": intent["business_name"],
                "subheadline": "Professional services tailored to your needs.",
                "cta": intent["primary_goal"],
            },
            "about": {
                "paragraphs": [
                    "We help customers achieve real results with reliable, high-quality service.",
                    "Our focus is clarity, quality, and long-term value.",
                ]
            },
            "services": {
                "title": "Our services",
                "items": [
                    {"title": s, "description": "Delivered with care and expertise."}
                    for s in intent["services"]
                ],
            },
            "testimonial": {
                "quote": "Professional, reliable, and easy to work with.",
                "author": "Happy customer",
            },
            "cta": {
                "headline": "Ready to get started?",
                "subheadline": "Get in touch and take the next step.",
                "button": intent["primary_goal"],
            },
            "footer": {
                "tagline": f"{intent['business_name']} — built for results.",
            },
        }


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
