from fastapi import APIRouter, HTTPException, Depends, Body
from sqlalchemy.orm import Session
import json
import re
import os

from app.database.session import SessionLocal
from app.database.models import Website, User
from app.utils.auth import get_current_user

# =========================
# DEV SETTINGS
# =========================
DEV_EMAIL = "Test@user.com"  # 👈 CHANGE TO YOUR EMAIL

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
def _validate_username(username: str):
    if not re.match(r"^[a-z0-9\-]{3,30}$", username):
        raise HTTPException(
            status_code=400,
            detail="Username must be 3–30 chars, lowercase letters, numbers or hyphens only",
        )


def _ai_generate_website_text(template: str, ai_input: dict):
    """
    Uses OpenAI to generate website copy.
    If OpenAI fails or key missing, returns None.
    """

    if not _openai_client:
        return None

    business_name = ai_input.get("business_name", "").strip()
    description = ai_input.get("short_description", "").strip()
    primary_goal = ai_input.get("primary_goal", "").strip()
    city = ai_input.get("city", "").strip()

    if not business_name:
        return None

    prompt = f"""
You are generating website copy for a {template} website.

Business name: {business_name}
Description: {description}
City: {city}
Primary goal: {primary_goal}

Return JSON ONLY in this format:

{{
  "hero_headline": "...",
  "hero_subheadline": "...",
  "about_text": "...",
  "services": [
    {{ "title": "...", "description": "..." }},
    {{ "title": "...", "description": "..." }}
  ]
}}

Tone:
- Professional
- Clean
- Conversion-focused
- Short and clear
"""

    try:
        response = _openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You generate clean website copy."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.7,
            max_tokens=500,
        )

        raw = response.choices[0].message.content
        return json.loads(raw)

    except Exception:
        return None


# =========================
# GET MY WEBSITE
# =========================
@router.get("/me")
def get_my_website(
    user: User = Depends(get_current_user),
    db: Session = Depends(SessionLocal),
):
    site = db.query(Website).filter(Website.user_id == user.id).first()

    if not site:
        return {"exists": False}

    return {
        "exists": True,
        "username": site.username,
        "template": site.template,
    }


# =========================
# CREATE WEBSITE
# =========================
@router.post("/create")
def create_website(
    payload: dict = Body(...),
    user: User = Depends(get_current_user),
    db: Session = Depends(SessionLocal),
):
    # -------------------------
    # Paid users only (DEV BYPASS)
    # -------------------------
    if (user.subscription_plan or "free") == "free" and user.email != DEV_EMAIL:
        raise HTTPException(
            status_code=403,
            detail="Upgrade your plan to create a website",
        )

    # -------------------------
    # Max 1 site per user (DEV BYPASS)
    # -------------------------
    existing_count = (
        db.query(Website)
        .filter(Website.user_id == user.id)
        .count()
    )
    if existing_count >= 1 and user.email != DEV_EMAIL:
        raise HTTPException(
            status_code=403,
            detail="Your plan allows only one website",
        )

    username = payload.get("username", "").strip().lower()
    template = payload.get("template", "").strip()
    ai_input = payload.get("ai_input") or {}

    if not username or not template:
        raise HTTPException(status_code=400, detail="Missing username or template")

    _validate_username(username)

    if template not in ("restaurant", "business"):
        raise HTTPException(status_code=400, detail="Invalid template")

    # -------------------------
    # Unique username
    # -------------------------
    if db.query(Website).filter(Website.username == username).first():
        raise HTTPException(status_code=400, detail="Username already taken")

    # -------------------------
    # AI generation (optional)
    # -------------------------
    ai_content = _ai_generate_website_text(template, ai_input)

    # -------------------------
    # Initial content per template
    # -------------------------
    if template == "restaurant":
        content = {
            "template": "restaurant",
            "template_version": 1,
            "hero": {
                "headline": ai_content["hero_headline"] if ai_content else username,
                "subheadline": ai_content["hero_subheadline"] if ai_content else "",
                "image": None,
            },
            "menu": [],
            "contact": {"phone": "", "email": ""},
            "location": {
                "address": "",
                "city": ai_input.get("city", ""),
            },
            "hours": {"mon_fri": "11:00 – 22:00", "sat_sun": "12:00 – 23:00"},
        }

    else:  # business
        content = {
            "template": "business",
            "template_version": 1,
            "theme": "light",
            "hero": {
                "headline": ai_content["hero_headline"] if ai_content else "Your Business",
                "subheadline": ai_content["hero_subheadline"] if ai_content else "",
                "image": None,
            },
            "about": {
                "title": "About Us",
                "text": ai_content["about_text"] if ai_content else "",
            },
            "services": {
                "title": "Our Services",
                "items": ai_content["services"] if ai_content else [],
            },
            "contact": {"phone": "", "email": ""},
        }

    # -------------------------
    # Create website
    # -------------------------
    site = Website(
        user_id=user.id,
        username=username,
        template=template,
        content_json=json.dumps(content),
    )

    db.add(site)
    db.commit()
    db.refresh(site)

    return {
        "ok": True,
        "username": username,
        "redirect": f"/r/{username}?edit=1",
    }
