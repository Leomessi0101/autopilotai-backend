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
# 🔥 STRICT AI CONTENT GENERATION
# =========================

def ai_generate_content_with_openai(
    template: str,
    ai_input: dict,
    username: str,
) -> Optional[dict]:

    if not _openai_client:
        return None

    raw_prompt = _clean_text(ai_input.get("raw_prompt"))
    if len(raw_prompt) < 10:
        return None

    city = _clean_text(ai_input.get("city"))
    business_name = username.replace("-", " ").title()

    SYSTEM = """
You generate REAL business websites.

Rules:
- No buzzwords
- No vague language
- No placeholders
- No AI mentions
- Write like this site will be published today
"""

    USER = f"""
Business name: {business_name}
Business type: {template}
City: {city}

Business description:
{raw_prompt}

STRICT OUTPUT REQUIREMENTS (JSON ONLY):

{{
  "hero": {{
    "headline": "",
    "subheadline": "",
    "cta_text": ""
  }},
  "services": {{
    "items": [
      {{ "title": "", "description": "" }},
      {{ "title": "", "description": "" }},
      {{ "title": "", "description": "" }}
    ]
  }},
  "trust": {{
    "items": ["", "", ""]
  }},
  "process": {{
    "steps": [
      {{ "title": "", "description": "" }},
      {{ "title": "", "description": "" }},
      {{ "title": "", "description": "" }}
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
    "address": "{city}"
  }}
}}

TONE:
- Clear
- Local
- Confident
- Simple
"""

    try:
        resp = _openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": SYSTEM},
                {"role": "user", "content": USER},
            ],
            temperature=0.5,
            max_tokens=900,
        )

        raw = (resp.choices[0].message.content or "").strip()
        data = _safe_json_loads(raw)

        if not isinstance(data, dict):
            return None

        return data

    except Exception:
        return None

# =========================
# FALLBACK CONTENT
# =========================

def build_default_content(template: str, ai_input: dict, username: str) -> dict:
    city = _clean_text(ai_input.get("city"))
    name = username.replace("-", " ").title()

    return {
        "hero": {
            "headline": name,
            "subheadline": f"Professional services in {city}" if city else "Professional services you can trust.",
            "cta_text": "Get started",
        },
        "services": {
            "items": [
                {"title": "Main service", "description": "Reliable and professional service."},
                {"title": "Fast response", "description": "Quick turnaround and clear communication."},
                {"title": "Trusted results", "description": "Focused on real outcomes."},
            ]
        },
        "trust": {
            "items": ["Local business", "Clear pricing", "Trusted quality"]
        },
        "process": {
            "steps": [
                {"title": "Contact", "description": "Reach out with your needs."},
                {"title": "Plan", "description": "We agree on next steps."},
                {"title": "Deliver", "description": "We get the job done."},
            ]
        },
        "cta": {
            "headline": "Ready to get started?",
            "subheadline": "Contact us today.",
            "button": "Contact",
        },
        "contact": {
            "phone": "",
            "email": "",
            "address": city,
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
    """
    Pricing rules:
    - free: 1 site, draft only, 1 page
    - starter: 1 site, published, 1 page
    - pro: 1 site, published, up to 3 pages
    """

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
