from fastapi import APIRouter, HTTPException, Depends, Header, Body
from sqlalchemy.orm import Session
from jose import jwt
import os
import json

from app.database.session import SessionLocal
from app.database.models import User, Website

SECRET = os.getenv("JWT_SECRET", "supersecretkey")
ALGORITHM = "HS256"

router = APIRouter()


# ========================= DB =========================
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ========================= AUTH (Reusable) =========================
def get_current_user(
    Authorization: str = Header(None),
    db: Session = Depends(get_db),
):
    if not Authorization:
        raise HTTPException(status_code=401, detail="Missing Authorization header")

    token = Authorization.replace("Bearer ", "")

    try:
        payload = jwt.decode(token, SECRET, algorithms=[ALGORITHM])
        user_id = payload["user_id"]
    except:
        raise HTTPException(status_code=401, detail="Invalid token")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return user


# ======================================================
# SAVE WEBSITE CONTENT (OWNER ONLY)
# Universal endpoint for all templates.
# Replaces content_json entirely (clean, deterministic).
# ======================================================
@router.post("/api/websites/{username}/content")
def save_website_content(
    username: str,
    payload: dict = Body(...),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # --------------------------------------------------
    # 1) PAID USERS ONLY
    # --------------------------------------------------
    if user.subscription_plan == "free":
        raise HTTPException(
            status_code=403,
            detail="Website builder is available for paid plans only",
        )

    website = db.query(Website).filter(Website.username == username).first()
    if not website:
        raise HTTPException(status_code=404, detail="Website not found")

    # --------------------------------------------------
    # 2) OWNER CHECK
    # --------------------------------------------------
    if website.user_id != user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    # --------------------------------------------------
    # 3) MAX 1 WEBSITE PER USER
    # --------------------------------------------------
    site_count = (
        db.query(Website)
        .filter(Website.user_id == user.id)
        .count()
    )

    if site_count > 1:
        raise HTTPException(
            status_code=403,
            detail="Your plan allows only one website",
        )

    # --------------------------------------------------
    # 4) PAYLOAD VALIDATION (FLEXIBLE)
    # --------------------------------------------------
    if not isinstance(payload, dict):
        raise HTTPException(status_code=400, detail="Invalid payload")

    # Keep template column in sync if provided
    if (
        "template" in payload
        and isinstance(payload["template"], str)
        and payload["template"].strip()
    ):
        website.template = payload["template"].strip()

    # Ensure template_version always exists
    if "template_version" not in payload:
        payload["template_version"] = 1

    # --------------------------------------------------
    # 5) SAVE (REPLACE ENTIRE JSON)
    # --------------------------------------------------
    try:
        website.content_json = json.dumps(payload)
        db.commit()
        return {"ok": True, "username": username}
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to save content")
