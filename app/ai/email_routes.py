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


# Backward-compatible payload:
# accepts subject/details OR prompt/text
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
    subject = (data.subject or "").strip()
    details = (data.details or data.prompt or data.text or "").strip()

    if not details:
        raise HTTPException(422, "Missing details/prompt/text")

    # HARD-LOCK: output the final email only (no tips)
    system = (
        "You write FINAL, SEND-READY business emails. "
        "You NEVER give advice, tips, explanations, or strategy. "
        "You ONLY output the email itself.\n\n"
        "Rules:\n"
        "- Start with a subject line: 'Subject: ...'\n"
        "- Then the email body.\n"
        "- Keep it clear, persuasive, and professional.\n"
        "- Include a concrete CTA.\n"
        "- No extra notes or commentary."
    )

    if not subject:
        subject = "Quick question"

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": f"Write an email.\n\nSubject idea: {subject}\n\nContext/details:\n{details}"}
            ]
        )

        output = (response.choices[0].message.content or "").strip()
        if not output:
            raise HTTPException(500, "OpenAI returned empty output")

        # Save to My Work
        db.add(SavedContent(
            user_id=user.id,
            content_type="email",
            prompt=subject,
            result=output,
        ))
        db.commit()

        return {"output": output}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"OpenAI error: {str(e)}")
