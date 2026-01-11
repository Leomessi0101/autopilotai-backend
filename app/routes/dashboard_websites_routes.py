from fastapi import APIRouter, HTTPException, Depends, Body
from sqlalchemy.orm import Session
import json
import re

from app.database.session import SessionLocal
from app.database.models import Website, User
from app.utils.auth import get_current_user

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
    # Initial content per template
    # -------------------------
    if template == "restaurant":
        content = {
            "template": "restaurant",
            "template_version": 1,
            "hero": {
                "headline": username,
                "subheadline": "",
                "image": None,
            },
            "menu": [],
            "contact": {"phone": "", "email": ""},
            "location": {"address": "", "city": ""},
            "hours": {"mon_fri": "11:00 – 22:00", "sat_sun": "12:00 – 23:00"},
        }
    else:  # business
        content = {
            "template": "business",
            "template_version": 1,
            "theme": "light",
            "hero": {
                "headline": "Your Business Name",
                "subheadline": "Short description of what you do",
                "image": None,
            },
            "about": {
                "title": "About Us",
                "text": "Write a short introduction about your business.",
            },
            "services": {
                "title": "Our Services",
                "items": [
                    {
                        "title": "Service One",
                        "description": "Describe your service.",
                    }
                ],
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
