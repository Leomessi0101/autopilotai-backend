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
            "Format for TikTok captions:\n"
            "- Short punchy hooks\n"
            "- Casual bold tone\n"
            "- Emojis allowed\n"
            "- 2–4 short lines only\n"
        )
    if platform == "twitter":
        return (
            "Format for X (Twitter):\n"
            "- Max 280 characters per post\n"
            "- Strong hooks\n"
            "- No unnecessary hashtags\n"
        )
    if platform == "linkedin":
        return (
            "Format for LinkedIn:\n"
            "- Professional tone\n"
            "- Value-driven\n"
            "- Line breaks\n"
            "- No emojis\n"
        )

    return (
        "Format for Instagram:\n"
        "- Hook first line\n"
        "- 2–4 lines max\n"
        "- Emojis allowed\n"
        "- 6–12 relevant hashtags\n"
    )


def build_behavior_rules(profile: Profile | None):
    """
    Convert stored profile behavior into readable AI instructions.
    Handles defaults safely if profile doesn't exist or fields are null.
    """

    if not profile:
        return (
            "AI Behavior Rules:\n"
            "- Use a balanced tone\n"
            "- Normal creativity\n"
            "- Emojis allowed\n"
            "- Hashtags allowed\n"
            "- Medium length content\n"
            "- Soft marketing CTA\n"
        )

    rules = "AI Behavior Rules:\n"

    # Creativity
    creativity = profile.creativity_level or 5
    if creativity <= 3:
        rules += "- Keep creativity low. Be factual and direct.\n"
    elif creativity <= 7:
        rules += "- Medium creativity. Natural but not crazy.\n"
    else:
        rules += "- Very creative, engaging and bold.\n"

    # Emojis
    if profile.use_emojis == False:
        rules += "- DO NOT use emojis.\n"
    else:
        rules += "- Emojis allowed.\n"

    # Hashtags
    if profile.use_hashtags == False:
        rules += "- DO NOT include hashtags.\n"
    else:
        rules += "- Hashtags allowed where appropriate.\n"

    # Length
    length = (profile.length_pref or "medium").lower()
    if length == "short":
        rules += "- Keep responses short and punchy.\n"
    elif length == "long":
        rules += "- Provide longer, more detailed content.\n"
    else:
        rules += "- Medium length responses.\n"

    # CTA Style
    cta = (profile.cta_style or "soft").lower()
    if cta == "strong":
        rules += "- Use strong persuasive CTA.\n"
    elif cta == "none":
        rules += "- No marketing CTA.\n"
    else:
        rules += "- Use soft CTA tone.\n"

    return rules


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

    # ------------ LOAD USER PROFILE RULES ------------
    profile = db.query(Profile).filter(Profile.user_id == user.id).first()
    behavior_rules = build_behavior_rules(profile)

    system_prompt = (
        "You generate READY-TO-POST social media content.\n"
        "Do NOT give explanations.\n"
        "Do NOT talk about strategy.\n"
        "Only output final posts.\n\n"
        f"{behavior_rules}\n"
        "Output EXACTLY 5 posts.\n"
        "Separate each clearly.\n\n"
        f"{platform_instructions(platform)}"
    )

    try:
        # ---------- TEXT GENERATION ----------
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Create 5 posts to showcase: {prompt}"}
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

        # ---------- PAID USER → GENERATE IMAGE ----------
        visual_prompt = f"""
        Create a high-quality, visually engaging marketing image.
        No text in the image.
        It should visually represent the following content:

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
            try:
                base64_data = image_response.data[0].b64_json
                image_url = f"data:image/png;base64,{base64_data}"
            except:
                image_url = None

        if not image_url:
            raise HTTPException(500, "Image generated but OpenAI did not return an image URL.")

        return {
            "output": output,
            "image": image_url,
            "error": None
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"OpenAI error: {str(e)}")
