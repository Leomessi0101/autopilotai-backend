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


def build_email_personality(profile: Profile | None) -> str:
    if not profile:
        return ""

    rules = []

    # --- Emojis ---
    if hasattr(profile, "use_emojis"):
        if profile.use_emojis:
            rules.append("You MAY use emojis when helpful but not childish.")
        else:
            rules.append("DO NOT use emojis anywhere.")

    # --- Hashtags (email usually none, but controlling anyway)
    if hasattr(profile, "use_hashtags"):
        if profile.use_hashtags:
            rules.append("Hashtags allowed only when appropriate.")
        else:
            rules.append("DO NOT use hashtags anywhere.")

    # --- Length preference ---
    if hasattr(profile, "length_pref"):
        if profile.length_pref == "short":
            rules.append("Keep the email concise and short.")
        elif profile.length_pref == "long":
            rules.append("Provide detailed, structured email content.")
        else:
            rules.append("Use a balanced medium length.")

    # --- Creativity ---
    if hasattr(profile, "creativity_level"):
        if profile.creativity_level <= 3:
            rules.append("Very professional, logical, minimal flair.")
        elif profile.creativity_level <= 7:
            rules.append("Balanced professionalism and personality.")
        else:
            rules.append("Creative, engaging, persuasive voice.")

    # --- CTA Style ---
    if hasattr(profile, "cta_style"):
        if profile.cta_style == "soft":
            rules.append("Use a soft and friendly call-to-action.")
        elif profile.cta_style == "aggressive":
            rules.append("Use a strong and direct call-to-action.")
        else:
            rules.append("Use a balanced professional CTA.")

    # --- Brand Tone ---
    if profile.brand_tone:
        rules.append(f"Brand tone: {profile.brand_tone}.")

    # --- Writing Style ---
    if profile.writing_style:
        rules.append(f"Preferred writing style: {profile.writing_style}.")

    # --- Signature ---
    if profile.signature:
        rules.append("Always end the email with this signature:\n" + profile.signature)

    return "\n".join(rules)


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

    profile = db.query(Profile).filter(Profile.user_id == user.id).first()

    personalization_rules = build_email_personality(profile)

    system = (
        "You write FINAL, SEND-READY business emails.\n"
        "You NEVER explain your writing.\n"
        "You ONLY output the email itself.\n\n"
        "Rules:\n"
        "- ALWAYS start with: Subject: ...\n"
        "- Then new line then full email body\n"
        "- Professional and persuasive\n"
        "- Clear structure\n"
        "- One clear CTA\n\n"
        f"{personalization_rules}"
    )

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system},
                {
                    "role": "user",
                    "content": f"Write this email:\n\nSubject idea: {subject}\n\nContext:\n{details}"
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
