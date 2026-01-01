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
        raise HTTPException(422, "Missing topic/prompt/text")

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

    try:
        # ---------- TEXT GENERATION ----------
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Create 5 posts about:\n\n{prompt}"}
            ]
        )

        output = response.choices[0].message.content.strip()
        if not output:
            raise HTTPException(500, "Empty AI response")

        # Save text always
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

        # ---------- IF IMAGE TOGGLE OFF ----------
        if not data.generate_image:
            return {
                "output": output,
                "image": None,
                "error": None
            }

        # ---------- IF USER IS FREE ----------
        if user.subscription_plan == "free":
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
            image_url = None

        if not image_url:
            try:
                base64_data = image_response.data[0].b64_json
                image_url = f"data:image/png;base64,{base64_data}"
            except:
                image_url = None

        if not image_url:
            raise HTTPException(500, "Image generated but no image returned from OpenAI.")

        return {
            "output": output,
            "image": image_url,
            "error": None
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"OpenAI error: {str(e)}")
