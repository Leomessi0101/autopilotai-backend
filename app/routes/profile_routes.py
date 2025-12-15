from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from app.utils.auth import get_current_user
from app.database.session import SessionLocal
from app.database.models import Profile, User

router = APIRouter()

class ProfileUpdate(BaseModel):
    full_name: str | None = None
    company_name: str | None = None
    company_website: str | None = None
    title: str | None = None
    brand_tone: str | None = None
    industry: str | None = None
    brand_description: str | None = None
    target_audience: str | None = None
    signature: str | None = None
    writing_style: str | None = None


# -----------------------------
# GET PROFILE
# -----------------------------
@router.get("/profile/me")
def get_profile(user: User = Depends(get_current_user)):
    db = SessionLocal()

    try:
        # IMPORTANT: reattach user to this session
        db_user = db.query(User).filter(User.id == user.id).first()

        if db_user is None:
            raise HTTPException(404, "User not found")

        profile = db_user.profile

        if profile is None:
            return {
                "full_name": "",
                "company_name": "",
                "company_website": "",
                "title": "",
                "brand_tone": "",
                "industry": "",
                "brand_description": "",
                "target_audience": "",
                "signature": "",
                "writing_style": "",
            }

        return {
            "full_name": profile.full_name or "",
            "company_name": profile.company_name or "",
            "company_website": profile.company_website or "",
            "title": profile.title or "",
            "brand_tone": profile.brand_tone or "",
            "industry": profile.industry or "",
            "brand_description": profile.brand_description or "",
            "target_audience": profile.target_audience or "",
            "signature": profile.signature or "",
            "writing_style": profile.writing_style or "",
        }

    finally:
        db.close()


# -----------------------------
# UPDATE PROFILE
# -----------------------------
@router.post("/profile/update")
def update_profile(data: ProfileUpdate, user: User = Depends(get_current_user)):
    db = SessionLocal()

    try:
        # IMPORTANT: reattach
        db_user = db.query(User).filter(User.id == user.id).first()

        if db_user is None:
            raise HTTPException(404, "User not found")

        profile = db_user.profile

        # Create if missing
        if profile is None:
            profile = Profile(
                user_id=db_user.id,
                full_name=data.full_name,
                company_name=data.company_name,
                company_website=data.company_website,
                title=data.title,
                brand_tone=data.brand_tone,
                industry=data.industry,
                brand_description=data.brand_description,
                target_audience=data.target_audience,
                signature=data.signature,
                writing_style=data.writing_style,
            )

            db.add(profile)
            db.commit()
            return {"message": "Profile created"}

        # Update existing
        profile.full_name = data.full_name
        profile.company_name = data.company_name
        profile.company_website = data.company_website
        profile.title = data.title
        profile.brand_tone = data.brand_tone
        profile.industry = data.industry
        profile.brand_description = data.brand_description
        profile.target_audience = data.target_audience
        profile.signature = data.signature
        profile.writing_style = data.writing_style

        db.commit()
        return {"message": "Profile updated"}

    finally:
        db.close()
