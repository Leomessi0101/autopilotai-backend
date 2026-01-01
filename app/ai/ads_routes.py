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
    platform: str | None = None
    objective: str | None = None
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

    limit = get_user_limit(user.subscription_plan)
    if limit is not None and user.used_generations >= limit:
        raise HTTPException(
            status_code=403,
            detail="Monthly generation limit reached. Please upgrade your plan."
        )

    # -------- SAFE PROFILE LOAD --------
    profile = db.query(Profile).filter(Profile.user_id == user.id).first()

    if not profile:
        class Dummy:
            use_emojis = True
            use_hashtags = True
            length_pref = "medium"
            creativity_level = 5
            cta_style = "balanced"
            brand_tone = ""
            writing_style = ""
        profile = Dummy()

    platform = (data.platform or "meta").lower()
    objective = (data.objective or "Sales").strip()
    product = (data.product or "").strip()
    audience = (data.audience or "").strip()
    prompt = (data.prompt or data.text or "").strip()

    if not prompt and (not product or not audience):
        raise HTTPException(422, "Provide prompt/text or product+audience")

    if not prompt:
        prompt = f"Create ads for {product} targeting {audience} with objective {objective}."

    # ---------- PERSONALITY RULES ----------
    emoji_rule = "Emojis allowed when natural." if profile.use_emojis else "Do NOT use emojis."
    hashtag_rule = "Use relevant hashtags when logical." if profile.use_hashtags else "Do NOT use hashtags."
    length_rule = (
        "Very short punchy ad copy."
        if profile.length_pref == "short"
        else "Balanced ad length."
        if profile.length_pref == "medium"
        else "More detailed, persuasive ad copy."
    )

    cta_rule = {
        "soft": "Use gentle CTA wording.",
        "balanced": "Use confident but friendly CTA.",
        "aggressive": "Use strong, decisive CTA.",
    }.get(profile.cta_style, "Balanced CTA.")

    creativity_rule = f"Creativity level: {profile.creativity_level}/10"

    tone_rule = (
        profile.brand_tone
        if profile.brand_tone
        else "Confident, modern marketing tone."
    )

    writing_style_rule = (
        profile.writing_style
        if profile.writing_style
        else "Clear, persuasive writing style."
    )

    # ---------- PLATFORM LOGIC ----------
    platform_format = ""

    if platform == "meta":
        platform_format = (
            "Write Facebook + Instagram style ads.\n"
            "- Strong hook first line\n"
            "- Skimmable short sentences\n"
            "- Optional emojis if allowed\n"
            "- 1 CTA\n"
        )

    elif platform == "google":
        platform_format = (
            "Write Google Search Ads.\n"
            "- Short headlines\n"
            "- Compelling descriptions\n"
            "- Clear value clarity\n"
            "- 1 CTA phrase\n"
        )

    elif platform == "tiktok":
        platform_format = (
            "Write TikTok Ad captions.\n"
            "- Fast hook\n"
            "- Energetic language\n"
            "- Relatable tone\n"
        )

    # ---------- SYSTEM PROMPT ----------
    system = (
        "You generate HIGH-CONVERTING ads.\n"
        "Return ONLY ad content—no explanation.\n\n"
        "FORMAT STRICTLY:\n\n"
        "AD 1:\nHeadline:\nPrimary text:\nCTA:\n\n"
        "AD 2:\nHeadline:\nPrimary text:\nCTA:\n\n"
        "AD 3:\nHeadline:\nPrimary text:\nCTA:\n\n"
        "RULES:\n"
        f"- {emoji_rule}\n"
        f"- {hashtag_rule}\n"
        f"- {length_rule}\n"
        f"- {cta_rule}\n"
        f"- {tone_rule}\n"
        f"- {writing_style_rule}\n"
        f"- {creativity_rule}\n\n"
        f"{platform_format}"
    )

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system},
                {"role": "user",
                 "content": f"""
Create 3 ads.

OBJECTIVE:
{objective}

PRODUCT:
{product}

AUDIENCE:
{audience}

PROMPT:
{prompt}
"""}
            ]
        )

        output = (response.choices[0].message.content or "").strip()
        if not output:
            raise HTTPException(500, "OpenAI returned empty output")

        # Save to DB
        db.add(SavedContent(
            user_id=user.id,
            content_type="ad",
            prompt=f"{product} → {audience}",
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
