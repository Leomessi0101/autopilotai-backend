from fastapi import APIRouter, HTTPException, Depends, Header, Body
from sqlalchemy.orm import Session
from jose import jwt
import os
import json

from openai import OpenAI

from app.database.session import SessionLocal
from app.database.models import User, Website

# ========================= CONFIG =========================

SECRET = os.getenv("JWT_SECRET", "supersecretkey")
ALGORITHM = "HS256"
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not OPENAI_API_KEY:
    raise RuntimeError("OPENAI_API_KEY is not set")

client = OpenAI(api_key=OPENAI_API_KEY)

router = APIRouter()

# ========================= DB =========================

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ========================= AUTH =========================

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
# SAVE WEBSITE CONTENT (UNCHANGED)
# ======================================================

@router.post("/api/websites/{username}/content")
def save_website_content(
    username: str,
    payload: dict = Body(...),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if user.subscription_plan == "free" and user.email != "test@user.com":
        raise HTTPException(
            status_code=403,
            detail="Website builder is available for paid plans only",
        )

    website = db.query(Website).filter(Website.username == username).first()
    if not website:
        raise HTTPException(status_code=404, detail="Website not found")

    if website.user_id != user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    if not isinstance(payload, dict):
        raise HTTPException(status_code=400, detail="Invalid payload")

    if "template" in payload and isinstance(payload["template"], str):
        website.template = payload["template"].strip()

    if "template_version" not in payload:
        payload["template_version"] = 1

    try:
        website.content_json = json.dumps(payload)
        db.commit()
        return {"ok": True, "username": username}
    except:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to save content")

# ======================================================
# AI WEBSITE GENERATOR (REAL AI)
# ======================================================

@router.post("/api/websites/{username}/ai-generate")
def ai_generate_website(
    username: str,
    payload: dict = Body(...),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    payload = {
      "business_name": "...",
      "description": "...",
      "goal": "get_leads | sell_online | bookings",
      "location": "optional"
    }
    """

    if user.subscription_plan == "free":
        raise HTTPException(
            status_code=403,
            detail="AI website generation is available for paid plans only",
        )

    website = db.query(Website).filter(Website.username == username).first()
    if not website:
        raise HTTPException(status_code=404, detail="Website not found")

    if website.user_id != user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    business_name = payload.get("business_name")
    description = payload.get("description")
    goal = payload.get("goal")
    location = payload.get("location", "")

    if not business_name or not description or not goal:
        raise HTTPException(status_code=400, detail="Missing required fields")

    prompt = f"""
You are an expert website designer and conversion copywriter.

Business:
- Name: {business_name}
- Description: {description}
- Goal: {goal}
- Location: {location}

Return VALID JSON ONLY with this exact structure:

{{
  "structure": {{
    "hero": {{
      "variant": "split_image | centered_text | image_background",
      "cta_style": "primary | secondary"
    }},
    "sections": [
      {{ "type": "features", "variant": "grid_3" }},
      {{ "type": "about", "variant": "image_left" }},
      {{ "type": "testimonials", "variant": "cards" }},
      {{ "type": "cta", "variant": "centered" }}
    ],
    "theme": {{
      "palette": "light | dark",
      "accent": "indigo | orange | emerald",
      "font": "inter"
    }},
    "footer": {{
      "variant": "minimal"
    }}
  }},
  "content": {{
    "template": "ai-generated",
    "template_version": 1,
    "hero_headline": "string",
    "hero_subheadline": "string",
    "cta_text": "string",
    "features": ["string", "string", "string"],
    "about_text": "string",
    "contact": {{
      "email": "placeholder@example.com",
      "phone": "",
      "address": ""
    }}
  }}
}}
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.6,
        )

        ai_json = json.loads(response.choices[0].message.content)

        website.ai_structure_json = json.dumps(ai_json["structure"])
        website.content_json = json.dumps(ai_json["content"])
        website.publish_status = "draft"

        db.commit()

        return {
            "ok": True,
            "username": username,
            "structure": ai_json["structure"],
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
