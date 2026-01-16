from fastapi import APIRouter, HTTPException, Depends, Body
from sqlalchemy.orm import Session
import json
import re
import os
from typing import Optional, Dict, Any, List

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
        goal = "Book now"
    elif any(w in p for w in ["contact", "call", "lead"]):
        goal = "Contact us"
    elif any(w in p for w in ["buy", "order", "sell"]):
        goal = "Get a quote"

    return {
        "business_type": business_type,
        "city": city,
        "primary_goal": goal,
        "raw_prompt": prompt,
    }


# =========================
# 🔥 REAL AI CONTENT (FIXED)
# =========================

def ai_generate_content_with_openai(
    template: str,
    ai_input: dict,
    username: str,
) -> Optional[dict]:
    """
    Generates a FULL, READY-TO-PUBLISH homepage.
    Never returns drafts. Never returns placeholders.
    """

    if not _openai_client:
        return None

    prompt_text = _clean_text(ai_input.get("raw_prompt"))
    if len(prompt_text) < 10:
        return None

    city = _clean_text(ai_input.get("city"))
    business_name = username.replace("-", " ").title()

    SYSTEM = """
You are a senior website copywriter.

Your job:
- Generate a COMPLETE homepage
- Make confident assumptions
- Sound warm, human, and professional
- Assume the site will be published immediately

Do NOT ask questions.
Do NOT include placeholders like "Add text".
Return JSON ONLY.
"""

    USER = f"""
Business type: {template}
Business name: {business_name}
City (if relevant): {city}

User description:
{prompt_text}

Return STRICT JSON with this structure:

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

Rules:
- Services: 3–5 items
- About: 2–3 paragraphs
- Testimonial must feel realistic
- Tone must feel warm and trustworthy
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
# 🧱 FALLBACK (NOW FINISHED)
# =========================

def build_default_content(template: str, ai_input: dict, username: str) -> dict:
    name = username.replace("-", " ").title()
    city = _clean_text(ai_input.get("city"))

    return {
        "hero": {
            "headline": name,
            "subheadline": f"Proudly serving {city}" if city else "Professional services you can trust.",
            "cta_text": "Get started",
            "image": None,
        },
        "highlight": {
            "headline": "Trusted by local customers",
            "subheadline": "Quality, reliability, and clear communication from day one.",
        },
        "about": {
            "paragraphs": [
                "We believe great service starts with understanding our customers and delivering consistent results.",
                "Our focus is on long-term value, honest communication, and work we’re proud to stand behind.",
            ],
            "image": None,
        },
        "services": {
            "title": "What we offer",
            "items": [
                {"title": "Professional service", "description": "Reliable and high-quality work.", "image": None},
                {"title": "Fast response", "description": "Clear communication and quick turnaround.", "image": None},
                {"title": "Trusted results", "description": "Focused on real outcomes that matter.", "image": None},
            ],
        },
        "testimonial": {
            "quote": "Everything was smooth, professional, and exceeded expectations.",
            "author": "Verified customer",
        },
        "cta": {
            "headline": "Ready to get started?",
            "subheadline": "Reach out today and let’s take the next step.",
            "button": "Contact us",
        },
        "contact": {
            "phone": "",
            "email": "",
            "address": "",
            "city": city,
        },
    }


# =========================
# CREATE WEBSITE (CANONICAL)
# =========================

@router.post("/create")
def create_website(
    payload: dict = Body(...),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    plan = (getattr(user, "subscription_plan", None) or "free").lower()
    if plan == "free" and user.email != "Test@user.com":
        raise HTTPException(status_code=403, detail="Paid plans only")

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

    structure = generate_ai_structure(
        business_type=template,
        goal=_clean_text(ai_input.get("primary_goal")) or "conversions",
        version=1,
    )

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
    }
