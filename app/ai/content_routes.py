from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.database.session import SessionLocal
from app.database.models import SavedContent
from app.utils.auth import get_current_user
from openai import OpenAI
import os

router = APIRouter()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


class ContentRequest(BaseModel):
    topic: str | None = None
    prompt: str | None = None
    text: str | None = None
    platform: str | None = None  # NEW (optional)


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
            "- Value-driven hooks\n"
            "- Line breaks for readability\n"
            "- No emojis or slang\n"
        )

    # default: Instagram
    return (
        "Format for Instagram.\n"
        "- Strong hook in first line\n"
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
    prompt = (data.topic or data.prompt or data.text or "").strip()
    if not prompt:
        raise HTTPException(422, "Missing topic/prompt/text")

    platform = (data.platform or "instagram").lower()

    system_prompt = (
        "You generate READY-TO-POST social media content.\n"
        "You NEVER give advice, tips, explanations, or strategies.\n"
        "You ONLY output finished posts.\n\n"
        "Output EXACTLY 5 posts.\n"
        "Each post must be clearly separated.\n"
        "No commentary. No explanations.\n\n"
        f"{platform_instructions(platform)}"
    )

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": f"Create 5 posts to showcase: {prompt}"
                }
            ]
        )

        output = response.choices[0].message.content.strip()

        if not output:
            raise HTTPException(500, "Empty AI response")

        db.add(SavedContent(
            user_id=user.id,
            content_type="content",
            prompt=f"{prompt} ({platform})",
            result=output
        ))
        db.commit()

        return {"output": output}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"OpenAI error: {str(e)}")
