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
        raise HTTPException(422, "Missing details/prompt/text")

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

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system},
                {"role": "user",
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
"""}
            ]
        )

        output = (response.choices[0].message.content or "").strip()
        if not output:
            raise HTTPException(500, "OpenAI returned empty output")

        # -------- SAVE TO DB --------
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
