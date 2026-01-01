from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.database.session import SessionLocal
from app.database.models import SavedContent, Profile
from app.utils.auth import get_current_user
from app.utils.usage import get_user_limit, reset_if_new_month
from openai import OpenAI
import os

router = APIRouter()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


class AdRequest(BaseModel):
    product: str | None = None
    audience: str | None = None
    prompt: str | None = None
    text: str | None = None


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ---------- AI Personality Builder ----------
def build_ad_behavior(profile: Profile | None):
    if not profile:
        return (
            "Ad Behavior Rules:\n"
            "- High converting tone\n"
            "- Clear benefit driven language\n"
            "- Medium creativity\n"
            "- Use CTA\n"
            "- Emojis allowed\n"
        )

    rules = "Ad Behavior Rules:\n"

    # Creativity
    creativity = profile.creativity_level or 5
    if creativity <= 3:
        rules += "- Keep creativity low. Direct, benefit-focused.\n"
    elif creativity <= 7:
        rules += "- Balanced creativity. Engaging but clear.\n"
    else:
        rules += "- Bold, emotionally engaging creative ad tone.\n"

    # Emojis
    if profile.use_emojis is False:
        rules += "- Do NOT use emojis.\n"
    else:
        rules += "- Emojis allowed if platform appropriate.\n"

    # Length preference
    length = (profile.length_pref or "medium").lower()
    if length == "short":
        rules += "- Prefer short punchy ad text.\n"
    elif length == "long":
        rules += "- Allowed to write longer persuasive copy.\n"
    else:
        rules += "- Medium length ad copy.\n"

    # CTA style
    cta = (profile.cta_style or "soft").lower()
    if cta == "strong":
        rules += "- Use strong CTA like BUY NOW / SIGN UP TODAY.\n"
    elif cta == "none":
        rules += "- Avoid marketing CTA.\n"
    else:
        rules += "- Use softer CTA like Learn More / Check It Out.\n"

    return rules


@router.post("/generate")
def generate_ads(
    data: AdRequest,
    user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    reset_if_new_month(user)

    limit = get_user_limit(user.subscription_plan)
    if limit is not None and user.used_generations >= limit:
        raise HTTPException(
            status_code=403,
            detail="Monthly generation limit reached. Please upgrade your plan."
        )

    product = (data.product or "").strip()
    audience = (data.audience or "").strip()
    prompt = (data.prompt or data.text or "").strip()

    if not prompt and (not product or not audience):
        raise HTTPException(422, "Provide prompt/text or product+audience")

    if not prompt:
        prompt = f"Create ads for {product} targeting {audience}."

    # ---------- LOAD PROFILE ----------
    profile = db.query(Profile).filter(Profile.user_id == user.id).first()
    behavior_rules = build_ad_behavior(profile)

    system = (
        "You write FINAL, READY-TO-USE, HIGH-CONVERTING ADS.\n"
        "No explanations. No tips. No commentary.\n\n"
        f"{behavior_rules}\n"
        "Output EXACTLY 3 ads:\n\n"
        "AD 1:\nHeadline:\nPrimary text:\nCTA:\n\n"
        "AD 2:\nHeadline:\nPrimary text:\nCTA:\n\n"
        "AD 3:\nHeadline:\nPrimary text:\nCTA:"
    )

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": prompt}
            ]
        )

        output = (response.choices[0].message.content or "").strip()
        if not output:
            raise HTTPException(500, "OpenAI returned empty output")

        db.add(SavedContent(
            user_id=user.id,
            content_type="ad",
            prompt=prompt if (product == "" and audience == "") else f"{product} → {audience}",
            result=output
        ))

        user.used_generations = (user.used_generations or 0) + 1
        db.add(user)
        db.commit()
        db.refresh(user)

        return {"output": output}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"OpenAI error: {str(e)}")
