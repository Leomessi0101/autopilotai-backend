from fastapi import APIRouter, HTTPException, Depends, Body
from sqlalchemy.orm import Session
import json
import re
import os
from typing import Optional, Any, Dict

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
# AI INPUT ENRICHMENT
# =========================

def build_ai_brief(prompt: str) -> Dict[str, str]:
    """
    Turns a vague user prompt into a strong AI brief.
    No guessing later — we do it once, cleanly.
    """
    p = (prompt or "").lower()

    # Business type
    business_type = "business"
    if any(w in p for w in ["restaurant", "pizza", "burger", "cafe", "coffee", "food"]):
        business_type = "restaurant"

    # City extraction
    city = ""
    city_match = re.search(r"in ([a-zA-Z\s]{2,40})", prompt or "")
    if city_match:
        city = city_match.group(1).strip().title()

    # Primary goal
    goal = "Get inquiries"
    if any(w in p for w in ["book", "booking", "appointment"]):
        goal = "Get bookings"
    elif any(w in p for w in ["call", "contact", "phone"]):
        goal = "Get calls"
    elif any(w in p for w in ["buy", "order", "sell"]):
        goal = "Get quote requests"

    return {
        "business_type": business_type,
        "city": city,
        "goal": goal,
        "raw_prompt": prompt,
    }

# =========================
# AI CONTENT GENERATION
# =========================

def ai_generate_content_with_openai(
    ai_brief: dict,
    username: str,
    plan: str,
) -> Optional[dict]:
    """
    Generates a COMPLETE, publish-ready homepage.
    Output is strict JSON only.
    """

    if not _openai_client:
        return None

    business_name = username.replace("-", " ").title()
    city = ai_brief.get("city") or "the local area"
    goal = ai_brief.get("goal")
    business_type = ai_brief.get("business_type")

    SYSTEM = """
You are a senior conversion-focused website copywriter.

Rules:
- Write confident, specific copy
- Focus on benefits, not features
- Sound human, local, and trustworthy
- Assume the website will be published immediately
- Never ask questions
- Never use placeholders
- Return VALID JSON ONLY
"""

    USER = f"""
Business name: {business_name}
Business type: {business_type}
City: {city}
Primary goal: {goal}
Plan: {plan}

User description:
{ai_brief.get("raw_prompt")}

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
- Hero must clearly state the MAIN benefit
- Services must be outcome-driven
- CTA must match the primary goal
- Services: 3–5 items
- About: 2–3 paragraphs
- Testimonial must feel realistic
"""

    try:
        resp = _openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": SYSTEM},
                {"role": "user", "content": USER},
            ],
            temperature=0.6,
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
# FALLBACK CONTENT (SAFE)
# =========================

def build_default_content(ai_brief: dict, username: str) -> dict:
    name = username.replace("-", " ").title()
    city = ai_brief.get("city") or "your area"

    return {
        "hero": {
            "headline": f"{name} — trusted local {ai_brief.get('business_type')}",
            "subheadline": f"Helping customers in {city} with reliable, professional service.",
            "cta_text": "Get in touch",
            "image": None,
        },
        "highlight": {
            "headline": "Why customers choose us",
            "subheadline": "Clear communication, honest pricing, and results you can trust.",
        },
        "about": {
            "paragraphs": [
                "We focus on delivering real value and building long-term relationships with our customers.",
                "Our approach is simple: understand your needs, do the job right, and stand behind our work.",
            ],
            "image": None,
        },
        "services": {
            "title": "Our services",
            "items": [
                {"title": "Professional service", "description": "Done right from start to finish.", "image": None},
                {"title": "Fast response", "description": "Clear communication and quick turnaround.", "image": None},
                {"title": "Trusted results", "description": "Focused on outcomes that matter.", "image": None},
            ],
        },
        "testimonial": {
            "quote": "Professional, reliable, and easy to work with.",
            "author": "Local customer",
        },
        "cta": {
            "headline": "Ready to get started?",
            "subheadline": "Contact us today and let’s talk.",
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
# CREATE WEBSITE
# =========================

@router.post("/create")
def create_website(
    payload: dict = Body(...),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    plan = (user.subscription_plan or "free").lower()

    # One website per user
    if db.query(Website).filter(Website.user_id == user.id).count() >= 1:
        raise HTTPException(status_code=403, detail="Only one website allowed")

    username = (payload.get("username") or "").strip().lower()
    prompt = (payload.get("prompt") or "").strip()

    if not username:
        raise HTTPException(status_code=400, detail="Missing username")

    if db.query(Website).filter(Website.username == username).first():
        raise HTTPException(status_code=400, detail="Username already taken")

    ai_brief = build_ai_brief(prompt)
    template = ai_brief["business_type"]

    max_pages = 3 if plan == "pro" else 1

    structure = generate_ai_structure(
        business_type=template,
        goal=ai_brief["goal"],
        version=1,
    )

    structure["plan"] = {
        "name": plan,
        "max_pages": max_pages,
        "can_publish": plan in ("starter", "pro"),
    }

    content = (
        ai_generate_content_with_openai(ai_brief, username, plan)
        or build_default_content(ai_brief, username)
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
