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


class ContentRequest(BaseModel):
    topic: str | None = None
    prompt: str | None = None
    text: str | None = None
    platform: str | None = None
    generate_image: bool = False


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def platform_instructions(platform: str) -> str:
    platform = platform.lower()

    if platform == "tiktok":
        return (
            "Format for TikTok captions.\n"
            "- Short punchy hooks\n"
            "- Casual, bold tone\n"
            "- Emojis allowed\n"
            "- Max 2–4 lines per post\n"
        )
    if platform == "twitter":
        return (
            "Format for X (Twitter).\n"
            "- Max 280 characters per post\n"
            "- Sharp hooks\n"
            "- No hashtags unless essential\n"
        )
    if platform == "linkedin":
        return (
            "Format for LinkedIn.\n"
            "- Professional tone\n"
            "- Value-driven\n"
            "- Line breaks for readability\n"
            "- No emojis or slang\n"
        )

    return (
        "Format for Instagram.\n"
        "- Strong hook first line\n"
        "- 2–4 short lines\n"
        "- Emojis allowed\n"
        "- 6–12 relevant hashtags\n"
    )


@router.post("/generate")
def generate_content(
    data: ContentRequest,
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

    prompt = (data.topic or data.prompt or data.text or "").strip()
    if not prompt:
        raise HTTPException(422, "Missing topic/prompt/text")

    platform = (data.platform or "instagram").lower()

    # ==========================
    # GET USER PERSONALITY PREFS
    # ==========================
    profile: Profile = user.profile

    # If somehow no profile exists → SAFE DEFAULTS
    if not profile:
        emoji_rule = "Emojis allowed."
        hashtag_rule = "Use relevant hashtags."
        length_text = "Balanced length."
        cta_text = "Balanced CTA."
        creativity = 5
    else:
        emoji_rule = "Do NOT use emojis." if not profile.use_emojis else "Emojis allowed where natural."
        hashtag_rule = "Do NOT use hashtags." if not profile.use_hashtags else "Use relevant hashtags."
        length_map = {
            "short": "Keep posts short and punchy.",
            "medium": "Use balanced length with substance.",
            "long": "Write longer, detailed posts."
        }
        cta_map = {
            "soft": "Use soft friendly CTA.",
            "balanced": "Use balanced persuasive CTA.",
            "aggressive": "Use strong direct CTA."
        }

        length_text = length_map.get(profile.length_pref, "Balanced length.")
        cta_text = cta_map.get(profile.cta_style, "Balanced CTA.")
        creativity = profile.creativity_level or 5

    system_prompt = f"""
You generate READY-TO-POST social media content.
Never explain. Never give tips. Never comment.
ONLY output final posts.

User AI Preferences:
- {emoji_rule}
- {hashtag_rule}
- {length_text}
- {cta_text}
- Creativity level (1–10): {creativity}

Output EXACTLY 5 posts.
Each post must be clearly separated.

{platform_instructions(platform)}
"""

    try:
        # ---------- TEXT ----------
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Create social posts about: {prompt}"}
            ]
        )

        output = response.choices[0].message.content.strip()
        if not output:
            raise HTTPException(500, "Empty AI response")

        # ---------- SAVE TEXT ----------
        db.add(SavedContent(
            user_id=user.id,
            content_type="content",
            prompt=f"{prompt} ({platform})",
            result=output
        ))

        user.used_generations = (user.used_generations or 0) + 1
        db.add(user)
        db.commit()
        db.refresh(user)

        # ---------- IF IMAGE OFF ----------
        if not data.generate_image:
            return {
                "output": output,
                "image": None,
                "error": None
            }

        # ---------- FREE USERS CAN'T USE ----------
        if user.subscription_plan == "free":
            return {
                "output": output,
                "image": None,
                "error": "AI Image is only available for paid users. Upgrade to unlock images."
            }

        # ---------- GENERATE IMAGE ----------
        visual_prompt = f"""
Create a high-quality visually engaging marketing image.
Do NOT include text.
Represent the vibe of this content:

{output[:900]}
"""

        image_response = client.images.generate(
            model="gpt-image-1",
            prompt=visual_prompt,
            size="1024x1024",
            response_format="url"
        )

        image_url = None
        try:
            image_url = image_response.data[0].url
        except:
            pass

        if not image_url:
            raise HTTPException(500, "Image generated but OpenAI returned no URL")

        return {
            "output": output,
            "image": image_url,
            "error": None
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"OpenAI error: {str(e)}")
