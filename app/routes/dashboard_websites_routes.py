from fastapi import APIRouter, HTTPException, Depends, Body
from sqlalchemy.orm import Session
import json
import re
import os
from typing import Optional, Any

from app.database.session import SessionLocal
from app.database.models import Website, User
from app.utils.auth import get_current_user

from app.ai.website_ai import generate_ai_structure

# =========================
# OPTIONAL: OpenAI
# =========================
try:
    from openai import OpenAI
    _openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
except Exception:
    _openai_client = None

router = APIRouter(prefix="/api/dashboard/websites")

# =========================
# HELPERS
# =========================

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def _clean_text(v: Any) -> str:
    if not v:
        return ""
    return str(v).strip()

def _safe_json_loads(s: str) -> Optional[dict]:
    try:
        return json.loads(s)
    except Exception:
        return None

# =========================
# AI-LITE INFERENCE
# =========================

def infer_ai_input_from_prompt(prompt: str) -> dict:
    p = (prompt or "").lower()

    business_type = "business"
    if any(w in p for w in ["restaurant", "pizza", "burger", "cafe", "coffee", "food"]):
        business_type = "restaurant"

    city = ""
    city_match = re.search(r"in ([a-zA-Z\s]{2,30})", prompt or "")
    if city_match:
        city = city_match.group(1).strip().title()

    goal = "Get started"
    if any(w in p for w in ["book", "booking", "appointment"]):
        goal = "Book an appointment"
    elif any(w in p for w in ["contact", "call", "lead"]):
        goal = "Contact us"
    elif any(w in p for w in ["buy", "order", "sell", "quote"]):
        goal = "Get a free quote"

    return {
        "business_type": business_type,
        "city": city,
        "primary_goal": goal,
        "raw_prompt": prompt,
    }

# =========================
# 🔥 REAL AI CONTENT (FULL FILL)
# =========================

def ai_generate_content_with_openai(
    template: str,
    ai_input: dict,
    username: str,
) -> Optional[dict]:
    """
    Generates a FULL homepage with NO placeholders.
    Every renderer section is filled.
    """

    if not _openai_client:
        return None

    prompt_text = _clean_text(ai_input.get("raw_prompt"))
    if len(prompt_text) < 10:
        return None

    city = _clean_text(ai_input.get("city"))
    business_name = username.replace("-", " ").title()
    goal = _clean_text(ai_input.get("primary_goal"))

    SYSTEM = """
You are a senior website copywriter.

Rules:
- Generate a COMPLETE homepage
- No placeholders like "Your Business Name"
- No generic filler sentences
- Make confident assumptions
- Write as if the site will be published immediately
- Output STRICT JSON only
"""

    USER = f"""
Business name: {business_name}
Business type: {template}
City: {city}
Primary goal: {goal}

User description:
{prompt_text}

Return JSON with ALL fields filled:

{{
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
    "paragraphs": ["", ""],
    "image": null
  }},
  "services": {{
    "title": "",
    "items": [
      {{ "title": "", "description": "", "image": null }},
      {{ "title": "", "description": "", "image": null }},
      {{ "title": "", "description": "", "image": null }}
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
  "contact": {{
    "phone": "",
    "email": "",
    "address": "",
    "city": "{city}"
  }}
}}

Guidelines:
- Hero headline = outcome + business type + city (if relevant)
- Highlight = trust + clarity
- About = 2 short, human paragraphs
- Services = outcome-focused, not features
- Testimonial must sound realistic (no stats)
- CTA must match the primary goal
"""

    try:
        resp = _openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": SYSTEM},
                {"role": "user", "content": USER},
            ],
            temperature=0.65,
            max_tokens=1200,
        )

        raw = (resp.choices[0].message.content or "").strip()
        data = _safe_json_loads(raw)

        if not isinstance(data, dict):
            return None

        return data

    except Exception:
        return None

# =========================
# 🧱 STRONG FALLBACK (NO PLACEHOLDERS)
# =========================

def build_default_content(template: str, ai_input: dict, username: str) -> dict:
    name = username.replace("-", " ").title()
    city = _clean_text(ai_input.get("city"))
    goal = _clean_text(ai_input.get("primary_goal")) or "Contact us"

    city_line = f" in {city}" if city else ""

    return {
        "hero": {
            "headline": f"{name}{city_line}",
            "subheadline": "Clear communication, honest service, and results you can trust.",
            "cta_text": goal,
            "image": None,
        },
        "highlight": {
            "headline": "Trusted by local customers",
            "subheadline": "We focus on clarity, reliability, and a great experience from start to finish.",
        },
        "about": {
            "paragraphs": [
                "We help customers make confident decisions by keeping things simple, transparent, and focused on real value.",
                "Every project is handled with care, clear communication, and attention to detail.",
            ],
            "image": None,
        },
        "services": {
            "title": "What we offer",
            "items": [
                {
                    "title": "Professional service",
                    "description": "Reliable, high-quality work tailored to your needs.",
                    "image": None,
                },
                {
                    "title": "Clear communication",
                    "description": "You always know what’s happening and what to expect.",
                    "image": None,
                },
                {
                    "title": "Results that matter",
                    "description": "Focused on outcomes, not unnecessary complexity.",
                    "image": None,
                },
            ],
        },
        "testimonial": {
            "quote": "Everything was smooth, professional, and easy from start to finish.",
            "author": "Local customer",
        },
        "cta": {
            "headline": "Ready to take the next step?",
            "subheadline": "Get in touch today and let’s talk.",
            "button": goal,
        },
        "contact": {
            "phone": "",
            "email": "",
            "address": "",
            "city": city,
        },
    }

# =========================
# CREATE WEBSITE
# =========================

@router.post("/create")
def create_website(
    payload: dict = Body(...),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    plan = (user.subscription_plan or "free").lower()

    if db.query(Website).filter(Website.user_id == user.id).count() >= 1:
        raise HTTPException(status_code=403, detail="Only one website allowed")

    username = (payload.get("username") or "").strip().lower()
    prompt = (payload.get("prompt") or "").strip()

    if not username:
        raise HTTPException(status_code=400, detail="Missing username")

    if db.query(Website).filter(Website.username == username).first():
        raise HTTPException(status_code=400, detail="Username already taken")

    ai_input = infer_ai_input_from_prompt(prompt)
    template = ai_input["business_type"]

    max_pages = 3 if plan == "pro" else 1

    structure = generate_ai_structure(
        business_type=template,
        goal=_clean_text(ai_input.get("primary_goal")) or "conversions",
        version=1,
    )

    structure["plan"] = {
        "name": plan,
        "max_pages": max_pages,
        "can_publish": plan in ("starter", "pro"),
    }

    content = (
        ai_generate_content_with_openai(template, ai_input, username)
        or build_default_content(template, ai_input, username)
    )

    site = Website(
        user_id=user.id,
        username=username,
        template=template,
        content_json=json.dumps(content),
        ai_structure_json=json.dumps(structure),
    )

    db.add(site)
    db.commit()

    return {
        "ok": True,
        "username": username,
        "redirect": f"/r/{username}?edit=1",
        "plan": plan,
        "max_pages": max_pages,
        "published": plan in ("starter", "pro"),
    }
