from fastapi import APIRouter, HTTPException, Depends, Body
from sqlalchemy.orm import Session
import json
import re
import os

from app.database.session import SessionLocal
from app.database.models import Website, User
from app.utils.auth import get_current_user

# OPTIONAL: OpenAI (safe to import even if key is missing)
try:
    from openai import OpenAI
    openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
except Exception:
    openai_client = None

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


def generate_ai_content_fallback(template: str, username: str, ai_input: dict):
    """
    Deterministic AI-style content (no OpenAI).
    Used as fallback and default behavior.
    """

    name = ai_input.get("business_name") or username.replace("-", " ").title()
    description = ai_input.get("description", "").strip()
    goal = ai_input.get("goal", "").strip()
    location = ai_input.get("location", "").strip()

    if template == "restaurant":
        return {
            "template": "restaurant",
            "template_version": 1,
            "hero": {
                "headline": name,
                "subheadline": description or "Great food, great atmosphere.",
                "image": None,
            },
            "menu": [],
            "contact": {"phone": "", "email": ""},
            "location": {"address": "", "city": location},
            "hours": {"mon_fri": "11:00 – 22:00", "sat_sun": "12:00 – 23:00"},
        }

    # business
    return {
        "template": "business",
        "template_version": 1,
        "theme": "light",
        "hero": {
            "headline": name,
            "subheadline": description or "We help clients achieve better results.",
            "image": None,
        },
        "about": {
            "title": f"About {name}",
            "text": description or "A short introduction to your business.",
        },
        "services": {
            "title": "Our Services",
            "items": [
                {
                    "title": goal or "Primary Service",
                    "description": "Describe what you offer and how it helps your customers.",
                }
            ],
        },
        "contact": {"phone": "", "email": ""},
    }


def generate_ai_content_openai(template: str, username: str, ai_input: dict):
    """
    Real OpenAI generation.
    If OpenAI fails for any reason, caller MUST fallback.
    """

    if not openai_client:
        raise RuntimeError("OpenAI not configured")

    system_prompt = (
        "You generate clean, professional website content. "
        "Return valid JSON only. No markdown. No explanations."
    )

    user_prompt = {
        "template": template,
        "username": username,
        "business_name": ai_input.get("business_name"),
        "description": ai_input.get("description"),
        "goal": ai_input.get("goal"),
        "location": ai_input.get("location"),
    }

    response = openai_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": f"Generate initial website content JSON for this input:\n{json.dumps(user_prompt)}",
            },
        ],
        temperature=0.7,
        max_tokens=700,
    )

    content = response.choices[0].message.content
    return json.loads(content)


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
    # Generate initial content
    # -------------------------
    content = None

    if ai_input:
        try:
            # Try real OpenAI first
            content = generate_ai_content_openai(template, username, ai_input)
        except Exception:
            # Always fallback safely
            content = generate_ai_content_fallback(template, username, ai_input)
    else:
        # Backward compatibility: old behavior
        content = generate_ai_content_fallback(template, username, {})

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
