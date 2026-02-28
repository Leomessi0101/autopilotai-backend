from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.database.session import SessionLocal
from app.database.models import SavedContent, Profile, User
from app.utils.auth import get_current_user
from app.utils.usage import get_user_limit, reset_if_new_month
from openai import OpenAI
import os
import fal_client  # fal.ai SDK for Nano Banana 2

router = APIRouter()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

class AdRequest(BaseModel):
    platform: str | None = None
    objective: str | None = None
    product: str | None = None
    audience: str | None = None
    prompt: str | None = None
    text: str | None = None
    generate_image: bool = False               # NEW: toggle for image
    custom_visual: str | None = None           # NEW: e.g. "clean background, no people, vibrant colors"

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ======================================================
# INTERNAL GENERATOR (REUSABLE, OPTIONAL USAGE CHARGE)
# ======================================================
def generate_ads_internal(
    data: AdRequest,
    user,
    db: Session,
    charge_usage: bool = True
):
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
        raise HTTPException(status_code=422, detail="Provide prompt/text or product+audience")
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
    if not os.getenv("OPENAI_API_KEY"):
        raise HTTPException(
            status_code=503,
            detail="Ad generation is not configured. Missing OPENAI_API_KEY."
        )
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system},
                {
                    "role": "user",
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
"""
                }
            ]
        )
    except Exception as e:
        raise HTTPException(
            status_code=502,
            detail=f"AI service error: {getattr(e, 'message', str(e))}"
        ) from e
    output = (response.choices[0].message.content or "").strip()
    if not output:
        raise HTTPException(status_code=500, detail="OpenAI returned empty output")
    db.add(SavedContent(
        user_id=user.id,
        content_type="ad",
        prompt=f"{product} → {audience}",
        result=output
    ))
    if charge_usage:
        user_db.used_generations = (user_db.used_generations or 0) + 1
    db.commit()
    return output

# ======================================================
# PUBLIC ROUTE
# ======================================================
@router.post("/generate")
def generate_ads(
    data: AdRequest,
    user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    output = generate_ads_internal(
        data=data,
        user=user,
        db=db,
        charge_usage=True
    )

    if not data.generate_image:
        return {"output": output, "image": None, "error": None}

    # Paid check for image feature (reuse your paid logic)
    subscription_plan = user.subscription_plan  # assuming user has this from get_current_user
    if not (subscription_plan and subscription_plan.lower() != "free"):
        return {
            "output": output,
            "image": None,
            "error": "AI Image generation is only available for paid users. Upgrade your plan."
        }

    # ---------- NANO BANANA 2 IMAGE GENERATION via fal.ai ----------
    fal_api_key = os.getenv("FAL_API_KEY")
    if not fal_api_key:
        return {
            "output": output,
            "image": None,
            "error": "fal.ai API key not configured (env: FAL_API_KEY)."
        }

    # Ensure fal_client uses the key
    os.environ["FAL_KEY"] = fal_api_key

    # Refine visual prompt using GPT-4o-mini (optimized for Nano Banana)
    refine_system = """You are an expert prompt engineer for Nano Banana 2 (Gemini 3.1 Flash Image).
Output ONLY the final prompt text. No explanations.
Rules:
- Start with the main product/subject and action.
- Use natural, detailed, positive language.
- Emphasize clean, pristine, unmarked surfaces; blank/plain objects without labels, writing, letters, symbols, inscriptions or readable elements.
- Include sharp focus, natural/cinematic lighting, vibrant yet realistic colors, professional marketing composition.
- Merge the ad concept (headline + text + CTA) into a strong visual scene.
- Apply user custom requests exactly.
- Keep under 250 words.
- Avoid any negation words ('no', 'without') — describe what you WANT."""

    refine_user = f"""Ad concept to visualize (pick the strongest/most visual elements from the 3 ads):
{output}

User custom instructions: {data.custom_visual or 'none — create eye-catching product-focused marketing visual'}

Style: high-quality ad image for social media / search, photorealistic or detailed professional look, suitable for Facebook/Instagram/TikTok/Google ads. Everything must be pristine and completely free of any text, writing, letters, symbols or readable elements."""

    try:
        refine_resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": refine_system},
                {"role": "user", "content": refine_user}
            ],
            max_tokens=400,
            temperature=0.7
        )
        visual_prompt = refine_resp.choices[0].message.content.strip()
    except Exception:
        # Fallback if GPT refine fails
        visual_prompt = f"""
Professional marketing ad image with completely clean unmarked pristine surfaces.
Blank smooth backgrounds, plain objects without labels markings logos inscriptions writing letters symbols or readable elements.
Photorealistic style, sharp details, natural vibrant colors, cinematic lighting.
Eye-catching product-focused scene representing: {output[:1000]}
{data.custom_visual or ''}
        """.strip()

    try:
        result = fal_client.subscribe(
            "fal-ai/nano-banana-2",  # Current main text-to-image model ID (Gemini 3.1 Flash Image / Nano Banana 2)
            arguments={
                "prompt": visual_prompt,
                "num_images": 1,
                "aspect_ratio": "1:1",      # Square works well for most ads; change to "4:5" or "16:9" if needed
                "output_format": "png",
                "resolution": "1K"          # Balanced quality/speed; use "2K" for sharper if budget allows
            }
        )
        if "images" in result and result["images"]:
            image_url = result["images"][0]["url"]
        else:
            raise ValueError("No image generated")
    except Exception as img_err:
        return {
            "output": output,
            "image": None,
            "error": f"Image generation failed: {str(img_err)}"
        }

    return {
        "output": output,
        "image": image_url,
        "error": None
    }