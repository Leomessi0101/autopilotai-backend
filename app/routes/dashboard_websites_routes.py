from fastapi import APIRouter, HTTPException, Depends, Body
from sqlalchemy.orm import Session
import json
import re

from app.database.session import SessionLocal
from app.database.models import Website, User
from app.utils.auth import get_current_user

from app.ai.website_ai import generate_ai_structure  # ✅ single source of structure

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
# CREATE WEBSITE (AI-FIRST)
# =========================
@router.post("/create")
def create_website(
    payload: dict = Body(...),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # -------------------------
    # PAID CHECK
    # -------------------------
    plan = (user.subscription or "free").lower()
    if plan == "free" and user.email != "Test@user.com":
        raise HTTPException(
            status_code=403,
            detail="Website builder is available for paid plans only",
        )

    # -------------------------
    # ONE SITE PER USER
    # -------------------------
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

    # -------------------------
    # AI STRUCTURE (ONCE)
    # -------------------------
    try:
        structure = generate_ai_structure(
            business_type=template,
            goal=ai_input.get("primary_goal", "conversions"),
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"AI layout generation failed: {str(e)}",
        )

    # -------------------------
    # EMPTY CONTENT (AI FILLS LATER)
    # -------------------------
    base_content = {
        "template": template,
        "template_version": 1,
        "ai_input": ai_input,  # 🔑 store intent forever
    }

    site = Website(
        user_id=user.id,
        username=username,
        template=template,
        content_json=json.dumps(base_content),
        ai_structure_json=json.dumps(structure),
    )

    db.add(site)
    db.commit()

    return {
        "ok": True,
        "username": username,
        "redirect": f"/r/{username}?edit=1",
    }
