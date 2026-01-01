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


@router.post("/generate")
def generate_ads(
    data: AdRequest,
    user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    reset_if_new_month(user)

    # ---------- LIMIT CHECK ----------
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

    # ---------------------------------
    # LOAD USER AI PERSONALITY
    # ---------------------------------
    profile: Profile = user.profile

    if not profile:
        emoji_rule = "Do not use emojis."
        hashtag_rule = "Do not include hashtags."
        length_rule = "Balanced length ads."
        cta_rule = "Use a persuasive CTA."
        tone_rule = "Professional confident tone."
        creativity = 5
    else:
        emoji_rule = (
            "Do NOT use emojis."
            if not profile.use_emojis
            else "Emojis may be used sparingly only when appropriate."
        )

        hashtag_rule = (
            "Do NOT include hashtags."
            if not profile.use_hashtags
            else "Include relevant tasteful hashtags when natural."
        )

        length_map = {
            "short": "Keep each ad short and punchy.",
            "medium": "Balanced engaging ad length.",
            "long": "Write longer persuasive ad copy with depth."
        }
        length_rule = length_map.get(profile.length_pref, "Balanced length ads.")

        cta_map = {
            "soft": "Use a soft friendly CTA.",
            "balanced": "Use a confident persuasive CTA.",
            "aggressive": "Use a strong direct CTA to drive conversion."
        }
        cta_rule = cta_map.get(profile.cta_style, "Use a persuasive CTA.")

        tone_rule = (
            f"Match this writing style if available: '{profile.writing_style}'. "
            f"If blank, default to confident marketing tone."
        )

        creativity = profile.creativity_level or 5

    # ---------------------------------
    # SYSTEM PROMPT
    # ---------------------------------
    system = f"""
You write HIGH CONVERTING FACEBOOK / INSTAGRAM / SOCIAL MEDIA ADS.
You ONLY output ads. No tips. No explanations.

You must ALWAYS output EXACTLY 3 ads.

Each ad must have:
AD X:
Headline:
Body:
CTA:

PERSONALITY RULES:
- {emoji_rule}
- {hashtag_rule}
- {length_rule}
- {tone_rule}
- {cta_rule}
- Creativity level (1–10): {creativity}

General rules:
- Compelling hook immediately
- Emotional + logical persuasion
- Clear benefits
- Human, not robotic
"""

    if not prompt:
        prompt = f"Create ads for {product} targeting {audience}."

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

        # ---------- SAVE ----------
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
