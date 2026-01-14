from fastapi import APIRouter, HTTPException, Depends, Body
from sqlalchemy.orm import Session
import json
import re
import os

from app.database.session import SessionLocal
from app.database.models import Website, User
from app.utils.auth import get_current_user

# ======================================================
# DEBUG CONFIRMATION (DO NOT REMOVE YET)
# ======================================================
print("🔥 dashboard_websites_routes.py LOADED")

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

        return json.loads(response.choices[0].message.content)
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
# CREATE WEBSITE (UNLOCKED)
# =========================
@router.post("/create")
def create_website(
    payload: dict = Body(...),
    user: User = Depends(get_current_user),
    db: Session = Depends(SessionLocal),
):
    # 🔥 ALL PAYWALLS REMOVED — DEV MODE
    username = payload.get("username", "").strip().lower()
    template = payload.get("template", "").strip()
    ai_input = payload.get("ai_input") or {}

    if not username or not template:
        raise HTTPException(status_code=400, detail="Missing username or template")

    _validate_username(username)

    if template not in ("restaurant", "business", "ai-generated"):
        raise HTTPException(status_code=400, detail="Invalid template")

    # username must still be unique
    if db.query(Website).filter(Website.username == username).first():
        raise HTTPException(status_code=400, detail="Username already taken")

    ai_content = _ai_generate_website_text(template, ai_input)

    # =========================
    # BUILD CONTENT
    # =========================
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
            "location": {"address": "", "city": ai_input.get("city", "")},
            "hours": {"mon_fri": "11:00 – 22:00", "sat_sun": "12:00 – 23:00"},
        }

    else:
        content = {
            "template": "ai-generated",
            "template_version": 1,
            "hero_headline": ai_content["hero_headline"] if ai_content else "Your Business",
            "hero_subheadline": ai_content["hero_subheadline"] if ai_content else "",
            "cta_text": "Get started",
            "features": [
                "Fast setup",
                "AI generated",
                "Mobile ready",
            ],
            "about_text": ai_content["about_text"] if ai_content else "",
            "contact": {"phone": "", "email": ""},
        }

    # =========================
    # SAVE WEBSITE
    # =========================
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
