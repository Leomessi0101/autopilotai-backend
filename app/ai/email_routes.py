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


class EmailRequest(BaseModel):
    subject: str | None = None
    details: str | None = None
    prompt: str | None = None
    text: str | None = None


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ---------- AI Personality Builder ----------
def build_email_behavior(profile: Profile | None):
    if not profile:
        return (
            "Email Tone & Behavior Rules:\n"
            "- Professional but friendly\n"
            "- Moderate creativity\n"
            "- Include a clear CTA\n"
            "- No emojis unless casual context\n"
            "- Keep length medium\n"
        )

    rules = "Email Tone & Behavior Rules:\n"

    # Creativity
    creativity = profile.creativity_level or 5
    if creativity <= 3:
        rules += "- Be formal, factual and direct.\n"
    elif creativity <= 7:
        rules += "- Balanced creativity – natural and engaging.\n"
    else:
        rules += "- Highly persuasive and engaging tone.\n"

    # Emojis
    if profile.use_emojis is False:
        rules += "- Do NOT use emojis.\n"

    # Length preference
    length = (profile.length_pref or "medium").lower()
    if length == "short":
        rules += "- Keep the email short and concise.\n"
    elif length == "long":
        rules += "- Provide more detailed messaging.\n"
    else:
        rules += "- Medium readable length.\n"

    # CTA style
    cta = (profile.cta_style or "soft").lower()
    if cta == "strong":
        rules += "- Use strong marketing-style CTA.\n"
    elif cta == "none":
        rules += "- No CTA unless essential.\n"
    else:
        rules += "- Use a gentle CTA.\n"

    return rules


@router.post("/generate")
def generate_email(
    data: EmailRequest,
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

    subject = (data.subject or "").strip()
    details = (data.details or data.prompt or data.text or "").strip()

    if not details:
        raise HTTPException(422, "Missing details/prompt/text")

    if not subject:
        subject = "Quick question"

    # ---------- Load Profile ----------
    profile = db.query(Profile).filter(Profile.user_id == user.id).first()
    behavior_rules = build_email_behavior(profile)

    system_prompt = (
        "You write FINAL, SEND-READY business emails.\n"
        "You NEVER explain.\n"
        "You NEVER talk about strategy.\n"
        "ONLY output:\n"
        "Subject line + Full email body.\n\n"
        f"{behavior_rules}"
    )

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": f"Write an email.\n\nSubject idea: {subject}\n\nContext:\n{details}"
                }
            ]
        )

        output = (response.choices[0].message.content or "").strip()
        if not output:
            raise HTTPException(500, "OpenAI returned empty output")

        db.add(SavedContent(
            user_id=user.id,
            content_type="email",
            prompt=subject,
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
