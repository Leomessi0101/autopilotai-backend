from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from app.utils.auth import get_current_user
from app.database.session import SessionLocal
from app.database.models import Profile, User

router = APIRouter()


class ProfileUpdate(BaseModel):
    # Existing
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

    # NEW Personality settings
    use_emojis: bool | None = True
    use_hashtags: bool | None = True
    length_pref: str | None = "medium"
    creativity_level: int | None = 5
    cta_style: str | None = "balanced"


# -----------------------------
# GET PROFILE
# -----------------------------
@router.get("/profile/me")
def get_profile(user: User = Depends(get_current_user)):
    db = SessionLocal()

    try:
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

                "use_emojis": True,
                "use_hashtags": True,
                "length_pref": "medium",
                "creativity_level": 5,
                "cta_style": "balanced",
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

            "use_emojis": profile.use_emojis if profile.use_emojis is not None else True,
            "use_hashtags": profile.use_hashtags if profile.use_hashtags is not None else True,
            "length_pref": profile.length_pref or "medium",
            "creativity_level": profile.creativity_level or 5,
            "cta_style": profile.cta_style or "balanced",
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
        db_user = db.query(User).filter(User.id == user.id).first()

        if db_user is None:
            raise HTTPException(404, "User not found")

        profile = db_user.profile

        # Create profile if missing
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

                use_emojis=data.use_emojis if data.use_emojis is not None else True,
                use_hashtags=data.use_hashtags if data.use_hashtags is not None else True,
                length_pref=data.length_pref or "medium",
                creativity_level=data.creativity_level or 5,
                cta_style=data.cta_style or "balanced",
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

        profile.use_emojis = data.use_emojis
        profile.use_hashtags = data.use_hashtags
        profile.length_pref = data.length_pref
        profile.creativity_level = data.creativity_level
        profile.cta_style = data.cta_style

        db.commit()
        return {"message": "Profile updated"}

    finally:
        db.close()
