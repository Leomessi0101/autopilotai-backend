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


# ======================================================
# INTERNAL GENERATOR (REUSABLE, OPTIONAL USAGE CHARGE)
# ======================================================
def generate_email_internal(
    data: EmailRequest,
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
            use_hashtags = False
            length_pref = "medium"
            creativity_level = 5
            cta_style = "balanced"
            brand_tone = ""
            writing_style = ""
            signature = ""
            company_name = ""
        profile = Dummy()

    # -------- INPUTS --------
    subject = (data.subject or "").strip()
    details = (data.details or data.prompt or data.text or "").strip()

    if not details:
        raise HTTPException(status_code=422, detail="Missing details/prompt/text")

    if not subject:
        subject = "Quick question"

    # -------- PERSONALITY RULES --------
    emoji_rule = "Use emojis only if natural and minimal." if profile.use_emojis else "Do NOT use emojis."
    length_rule = (
        "Keep this email short and concise."
        if profile.length_pref == "short"
        else "Balanced length with clarity."
        if profile.length_pref == "medium"
        else "More detailed email with depth."
    )

    cta_rule = {
        "soft": "Use a calm, friendly CTA.",
        "balanced": "Use a confident but non-pushy CTA.",
        "aggressive": "Use a strong direct CTA."
    }.get(profile.cta_style, "Balanced CTA.")

    creativity_rule = f"Creativity level: {profile.creativity_level}/10"

    tone_rule = (
        profile.brand_tone
        if profile.brand_tone
        else "Professional and confident tone."
    )

    writing_style_rule = (
        profile.writing_style
        if profile.writing_style
        else "Clear, direct writing style."
    )

    signature = profile.signature or ""
    company_name = profile.company_name or ""

    # -------- SYSTEM PROMPT --------
    system = (
        "You write FINAL, SEND-READY business emails.\n"
        "NO explanations. NO commentary.\n"
        "Output ONLY the email in this structure:\n\n"
        "Subject: <subject here>\n\n"
        "<email body>\n\n"
        "Rules:\n"
        f"- {emoji_rule}\n"
        f"- {length_rule}\n"
        f"- {cta_rule}\n"
        f"- {tone_rule}\n"
        f"- {writing_style_rule}\n"
        f"- {creativity_rule}\n\n"
        "Make it persuasive, professional, human sounding.\n"
        "Do NOT oversell. Respectful confidence.\n"
        "No hashtags.\n"
    )

    if not os.getenv("OPENAI_API_KEY"):
        raise HTTPException(
            status_code=503,
            detail="Email generation is not configured. Missing OPENAI_API_KEY."
        )
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system},
                {
                    "role": "user",
                    "content": f"""
Write this email.

SUBJECT IDEA:
{subject}

CONTEXT:
{details}

COMPANY (if relevant):
{company_name}

If appropriate, include this signature:
{signature}
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
        content_type="email",
        prompt=subject,
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
def generate_email(
    data: EmailRequest,
    user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    output = generate_email_internal(
        data=data,
        user=user,
        db=db,
        charge_usage=True
    )

    return {"output": output}
