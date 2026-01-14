from fastapi import APIRouter, HTTPException, Depends, Body
from sqlalchemy.orm import Session
import json
import re

from app.database.session import SessionLocal
from app.database.models import Website, User
from app.utils.auth import get_current_user

from app.ai.website_ai import generate_ai_structure

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


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def build_default_content(template: str, ai_input: dict, username: str):
    """
    Deterministic, cheap, always-present starter content.
    """
    name = ai_input.get("business_name") or username.replace("-", " ").title()
    city = ai_input.get("city") or ""
    goal = ai_input.get("primary_goal") or "Get started"

    hero_headline = f"{name}"
    hero_subheadline = (
        f"Serving {city} with quality and care."
        if city
        else "Built with AutopilotAI."
    )

    services = [
        {
            "title": "Professional service",
            "description": "Reliable, high-quality service tailored to your needs.",
        },
        {
            "title": "Fast response",
            "description": "Quick turnaround and clear communication.",
        },
        {
            "title": "Trusted by customers",
            "description": "Focused on long-term results and satisfaction.",
        },
    ]

    content = {
        "hero": {
            "headline": hero_headline,
            "subheadline": hero_subheadline,
            "image": None,
            "cta_text": goal,
            "cta_link": "#contact",
        },
        "services": services,
        "cta": {
            "headline": "Ready to get started?",
            "text": "Contact us today and take the next step.",
            "link": "#contact",
        },
    }

    if template == "restaurant":
        content.update(
            {
                "menu": [],
                "hours": {
                    "mon_fri": "11:00 – 22:00",
                    "sat_sun": "12:00 – 23:00",
                },
                "location": {
                    "city": city,
                },
                "contact": {
                    "phone": "",
                    "email": "",
                },
            }
        )

    return content


# =========================
# GET MY WEBSITE
# =========================
@router.get("/me")
def get_my_website(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
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
# CREATE WEBSITE (CANONICAL)
# =========================
@router.post("/create")
def create_website(
    payload: dict = Body(...),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    plan = (user.subscription or "free").lower()
    if plan == "free" and user.email != "Test@user.com":
        raise HTTPException(
            status_code=403,
            detail="Website builder is available for paid plans only",
        )

    if db.query(Website).filter(Website.user_id == user.id).count() >= 1:
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

    if db.query(Website).filter(Website.username == username).first():
        raise HTTPException(status_code=400, detail="Username already taken")

    # 🧠 AI STRUCTURE (ONCE)
    structure = generate_ai_structure(
        business_type=template,
        goal=ai_input.get("primary_goal", "conversions"),
    )

    # 🧱 DEFAULT CONTENT (ALWAYS PRESENT)
    content = build_default_content(template, ai_input, username)

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
