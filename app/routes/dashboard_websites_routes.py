from fastapi import APIRouter, HTTPException, Depends, Body
from sqlalchemy.orm import Session
import json
import re
import os

from openai import OpenAI

from app.database.session import SessionLocal
from app.database.models import Website, User
from app.utils.auth import get_current_user

router = APIRouter(prefix="/api/dashboard/websites")

# =========================
# OPENAI CLIENT
# =========================
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# =========================
# HELPERS
# =========================
def _validate_username(username: str):
    if not re.match(r"^[a-z0-9\-]{3,30}$", username):
        raise HTTPException(
            status_code=400,
            detail="Username must be 3–30 chars, lowercase letters, numbers or hyphens only",
        )


def generate_ai_content_openai(template: str, username: str, ai_input: dict):
    """
    Generate initial website content using OpenAI.
    Falls back safely if anything goes wrong.
    """

    name = ai_input.get("business_name") or username.replace("-", " ").title()
    description = ai_input.get("description", "")
    goal = ai_input.get("goal", "")
    location = ai_input.get("location", "")

    system_prompt = (
        "You generate structured JSON content for websites. "
        "Return ONLY valid JSON. No markdown. No explanation."
    )

    if template == "restaurant":
        user_prompt = f"""
Generate initial website content for a restaurant.

Business name: {name}
Description: {description}
Location: {location}
Goal: {goal}

JSON structure:
{{
  "template": "restaurant",
  "template_version": 1,
  "hero": {{
    "headline": "...",
    "subheadline": "...",
    "image": null
  }},
  "menu": [],
  "contact": {{ "phone": "", "email": "" }},
  "location": {{ "address": "", "city": "{location}" }},
  "hours": {{ "mon_fri": "11:00 – 22:00", "sat_sun": "12:00 – 23:00" }}
}}
"""
    else:
        user_prompt = f"""
Generate initial website content for a business website.

Business name: {name}
Description: {description}
Location: {location}
Goal: {goal}

JSON structure:
{{
  "template": "business",
  "template_version": 1,
  "theme": "light",
  "hero": {{
    "headline": "...",
    "subheadline": "...",
    "image": null
  }},
  "about": {{
    "title": "About {name}",
    "text": "..."
  }},
  "services": {{
    "title": "Our Services",
    "items": [
      {{
        "title": "...",
        "description": "..."
      }}
    ]
  }},
  "contact": {{ "phone": "", "email": "" }}
}}
"""

    try:
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.6,
        )

        content = response.choices[0].message.content
        parsed = json.loads(content)

        # Safety check
        if not isinstance(parsed, dict):
            raise ValueError("Invalid AI response")

        return parsed

    except Exception:
        # Safe fallback (never break creation)
        if template == "restaurant":
            return {
                "template": "restaurant",
                "template_version": 1,
                "hero": {
                    "headline": name,
                    "subheadline": description or "Fresh food. Great atmosphere.",
                    "image": None,
                },
                "menu": [],
                "contact": {"phone": "", "email": ""},
                "location": {"address": "", "city": location},
                "hours": {"mon_fri": "11:00 – 22:00", "sat_sun": "12:00 – 23:00"},
            }

        return {
            "template": "business",
            "template_version": 1,
            "theme": "light",
            "hero": {
                "headline": name,
                "subheadline": description or "Helping clients achieve better results.",
                "image": None,
            },
            "about": {
                "title": f"About {name}",
                "text": description or "Short description of what we do.",
            },
            "services": {
                "title": "Our Services",
                "items": [
                    {
                        "title": goal or "Primary Service",
                        "description": "Describe what you offer and how it helps.",
                    }
                ],
            },
            "contact": {"phone": "", "email": ""},
        }


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
    # Paid users only
    # -------------------------
    if (user.subscription_plan or "free") == "free":
        raise HTTPException(
            status_code=403,
            detail="Upgrade your plan to create a website",
        )

    # -------------------------
    # Max 1 site per user
    # -------------------------
    existing_count = (
        db.query(Website)
        .filter(Website.user_id == user.id)
        .count()
    )
    if existing_count >= 1:
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
    # AI-GENERATED INITIAL CONTENT
    # -------------------------
    content = generate_ai_content_openai(template, username, ai_input)

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
