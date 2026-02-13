from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.database.session import SessionLocal
from app.database.models import SavedContent, Profile, User
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
            "- Casual bold tone\n"
            "- Emojis allowed\n"
            "- Max 2–4 short lines\n"
        )
    if platform == "twitter":
        return (
            "Format for X (Twitter)\n"
            "- Max 280 characters per post\n"
            "- Sharp hooks\n"
            "- No hashtags unless essential\n"
        )
    if platform == "linkedin":
        return (
            "Format for LinkedIn\n"
            "- Professional serious tone\n"
            "- Value focused\n"
            "- Line breaks for readability\n"
            "- No emojis or slang\n"
        )

    return (
        "Format for Instagram\n"
        "- Hook first line\n"
        "- Short readable flow\n"
        "- Emojis allowed\n"
        "- 6–12 relevant hashtags\n"
    )


def _is_paid_user(subscription_plan: str | None) -> bool:
    """AI image is only for paid plans (anything not 'free')."""
    plan = (subscription_plan or "free").lower()
    return plan != "free"


# ======================================================
# INTERNAL GENERATOR (REUSABLE, OPTIONAL USAGE CHARGE)
# ======================================================
def generate_content_internal(
    data: ContentRequest,
    user,
    db: Session,
    charge_usage: bool = True
):
    # Use user from THIS session so updates (reset, used_generations) commit correctly.
    user_db = db.query(User).filter(User.id == user.id).first()
    if not user_db:
        raise HTTPException(status_code=404, detail="User not found")

    reset_if_new_month(user_db)

    if charge_usage:
        limit = get_user_limit(user_db.subscription_plan)
        if limit is not None and (user_db.used_generations or 0) >= limit:
            raise HTTPException(
                status_code=403,
                detail="Monthly generation limit reached. Please upgrade your plan."
            )

    # ---------------- PROFILE LOAD (SAFE) ----------------
    profile = db.query(Profile).filter(Profile.user_id == user.id).first()

    if not profile:
        class Dummy:
            use_emojis = True
            use_hashtags = True
            length_pref = "medium"
            creativity_level = 5
            cta_style = "balanced"
        profile = Dummy()

    # ---------------- PROMPT LOGIC ----------------
    prompt = (data.topic or data.prompt or data.text or "").strip()
    if not prompt:
        raise HTTPException(status_code=422, detail="Missing topic/prompt/text")

    platform = (data.platform or "instagram").lower()

    # ---------------- AI BEHAVIOR RULES ----------------
    emoji_rule = "Use emojis naturally" if profile.use_emojis else "Do NOT use emojis"
    hashtag_rule = "Use strong relevant hashtags" if profile.use_hashtags else "Do NOT include hashtags"

    length_rule = {
        "short": "Keep each post very short and punchy.",
        "medium": "Keep posts balanced in length.",
        "long": "Write longer, detailed posts."
    }.get(profile.length_pref, "Balanced length.")

    cta_rule = {
        "soft": "Use soft and friendly CTA style.",
        "balanced": "Use confident but not pushy CTAs.",
        "aggressive": "Use extremely strong persuasive CTA style."
    }.get(profile.cta_style, "Balanced CTA style.")

    creativity_rule = f"Creativity intensity: {profile.creativity_level}/10"

    system_prompt = (
        "You generate READY-TO-POST social media content.\n"
        "Only output the posts. NO explanations.\n"
        "Output EXACTLY 5 posts.\n"
        "Separate posts clearly with spacing.\n\n"
        f"{platform_instructions(platform)}\n\n"
        f"{emoji_rule}\n"
        f"{hashtag_rule}\n"
        f"{length_rule}\n"
        f"{cta_rule}\n"
        f"{creativity_rule}"
    )

    # ---------- TEXT GENERATION ----------
    if not os.getenv("OPENAI_API_KEY"):
        raise HTTPException(
            status_code=503,
            detail="Content generation is not configured. Missing OPENAI_API_KEY."
        )
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Create 5 posts about:\n\n{prompt}"}
            ]
        )
    except Exception as e:
        raise HTTPException(
            status_code=502,
            detail=f"AI service error: {getattr(e, 'message', str(e))}"
        ) from e

    output = (response.choices[0].message.content or "").strip()
    if not output:
        raise HTTPException(status_code=500, detail="Empty AI response")

    db.add(SavedContent(
        user_id=user.id,
        content_type="content",
        prompt=f"{prompt} ({platform})",
        result=output
    ))

    if charge_usage:
        user_db.used_generations = (user_db.used_generations or 0) + 1

    db.commit()

    return output


# ======================================================
# PUBLIC ROUTE (UNCHANGED BEHAVIOR)
# ======================================================
@router.post("/generate")
def generate_content(
    data: ContentRequest,
    user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    output = generate_content_internal(
        data=data,
        user=user,
        db=db,
        charge_usage=True
    )

    # ---------- IF IMAGE TOGGLE OFF ----------
    if not data.generate_image:
        return {
            "output": output,
            "image": None,
            "error": None
        }

    # ---------- AI IMAGE: PAID USERS ONLY ----------
    if not _is_paid_user(user.subscription_plan):
        return {
            "output": output,
            "image": None,
            "error": "AI Image is only available for paid users. Upgrade to unlock images."
        }

    # ---------- PAID USER IMAGE ----------
    visual_prompt = f"""
    Create a high-quality, visually engaging marketing image.
    NO TEXT IN THE IMAGE.
    Represent the theme creatively.

    CONTENT THE IMAGE SHOULD REPRESENT:
    {output[:900]}
    """
    try:
        image_response = client.images.generate(
            model="dall-e-3",
            prompt=visual_prompt[:1000],
            size="1024x1024",
            quality="standard",
            n=1,
            response_format="url",
        )
    except Exception as img_err:
        return {
            "output": output,
            "image": None,
            "error": f"Image generation failed: {getattr(img_err, 'message', str(img_err))}"
        }

    image_url = None
    if image_response.data and len(image_response.data) > 0:
        first = image_response.data[0]
        if getattr(first, "url", None):
            image_url = first.url
        elif getattr(first, "b64_json", None):
            image_url = f"data:image/png;base64,{first.b64_json}"

    if not image_url:
        return {
            "output": output,
            "image": None,
            "error": "Image was requested but no image returned from AI."
        }

    return {
        "output": output,
        "image": image_url,
        "error": None
    }
