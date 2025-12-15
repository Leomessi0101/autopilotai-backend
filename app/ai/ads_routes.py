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
# accepts product/audience OR prompt/text
class AdRequest(BaseModel):
    product: str | None = None
    audience: str | None = None
    prompt: str | None = None
    text: str | None = None


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/generate")
def generate_ads(
    data: AdRequest,
    user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    product = (data.product or "").strip()
    audience = (data.audience or "").strip()
    prompt = (data.prompt or data.text or "").strip()

    if not prompt and (not product or not audience):
        raise HTTPException(422, "Provide prompt/text or product+audience")

    # HARD-LOCK: output finished ads only (no advice)
    system = (
        "You write HIGH-CONVERTING ad copy. "
        "You NEVER give advice, tips, explanations, or strategies. "
        "You ONLY output finished ad copy.\n\n"
        "Output format MUST be:\n"
        "AD 1:\nHeadline:\nPrimary text:\nCTA:\n\n"
        "AD 2:\nHeadline:\nPrimary text:\nCTA:\n\n"
        "AD 3:\nHeadline:\nPrimary text:\nCTA:\n\n"
        "Rules:\n"
        "- Strong hook in headline\n"
        "- Clear benefit + proof\n"
        "- Clear CTA\n"
        "- No commentary"
    )

    if not prompt:
        prompt = f"Create ads for {product} targeting {audience}."

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": prompt}
            ]
        )

        output = (response.choices[0].message.content or "").strip()
        if not output:
            raise HTTPException(500, "OpenAI returned empty output")

        # Save to My Work
        db.add(SavedContent(
            user_id=user.id,
            content_type="ad",
            prompt=prompt if (product == "" and audience == "") else f"{product} → {audience}",
            result=output,
        ))
        db.commit()

        return {"output": output}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"OpenAI error: {str(e)}")
