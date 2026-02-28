from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.database.session import SessionLocal
from app.database.models import SavedContent, Profile, User
from app.utils.auth import get_current_user
from app.utils.usage import get_user_limit, reset_if_new_month
from openai import OpenAI
import os
import requests  # ← NEW: for BFL API calls + polling
import time     # ← NEW: for sleep in polling

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

    # ---------- BFL Flux IMAGE GENERATION ----------
    bfl_api_key = os.getenv("BFL_API_KEY")
    if not bfl_api_key:
        return {
            "output": output,
            "image": None,
            "error": "BFL API key not set in environment variables (BFL_API_KEY)."
        }

    # Model path from env (your klein model)
    model_path = os.getenv("FLUX_MODEL_ENDPOINT", "flux-2-klein-9b")
    base_url = "https://api.bfl.ai/v1"  # This is the correct BFL base – do NOT change to your full endpoint
    generate_url = f"{base_url}/{model_path.lstrip('/')}"

    # Better prompt for klein (fast model – keep it descriptive but not too long)
    visual_prompt = f"""
    Eye-catching social media marketing image, no text or words anywhere.
    Photorealistic or high-detail style, sharp focus, natural vibrant colors, cinematic lighting.
    Visually represent this post concept in an engaging way:
    {output[:900]}
    Professional composition, centered subject, appealing for Instagram/TikTok.
    """

    try:
        # Submit the generation request
        response = requests.post(
            generate_url,
            headers={
                "accept": "application/json",
                "x-key": bfl_api_key,
                "Content-Type": "application/json"
            },
            json={
                "prompt": visual_prompt,
                "width": 1024,
                "height": 1024,
                "num_inference_steps": 20,   # klein is optimized for fewer steps → fast
                "guidance_scale": 3.5,
                "output_format": "png",
                # "aspect_ratio": "1:1",  # optional if you want to force square
            },
            timeout=20
        )
        response.raise_for_status()
        task_data = response.json()

        polling_url = task_data.get("polling_url")
        if not polling_url:
            raise ValueError("No polling_url in BFL response – check API key or model availability.")

        # Poll for result
        start_time = time.time()
        image_url = None
        while time.time() - start_time < 90:  # timeout after ~1.5 min
            poll_resp = requests.get(
                polling_url,
                headers={"accept": "application/json"}
            )
            poll_resp.raise_for_status()
            poll_data = poll_resp.json()

            status = poll_data.get("status", "").lower()
            if status in ["done", "completed", "success"]:
                images = poll_data.get("result", {}).get("images", [])
                if images and images[0].get("url"):
                    image_url = images[0]["url"]
                    break
            elif status in ["failed", "error", "cancelled"]:
                error_msg = poll_data.get("error") or "Unknown error"
                raise ValueError(f"Generation failed: {error_msg}")

            time.sleep(1.5)  # poll every 1.5s – klein is fast

        if not image_url:
            raise TimeoutError("Timed out waiting for Flux image – try again or check BFL status.")

    except Exception as img_err:
        return {
            "output": output,
            "image": None,
            "error": f"Flux (klein) generation error: {str(img_err)}"
        }

    return {
        "output": output,
        "image": image_url,
        "error": None
    }