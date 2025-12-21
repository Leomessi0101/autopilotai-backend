from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.database.session import SessionLocal
from app.database.models import SavedContent
from app.utils.auth import get_current_user
from app.utils.usage import get_user_limit, reset_if_new_month
from openai import OpenAI
import os

router = APIRouter()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


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
    reset_if_new_month(user)

    limit = get_user_limit(user.subscription_plan)
    if limit is not None and user.used_generations >= limit:
        raise HTTPException(
            status_code=403,
            detail="Monthly generation limit reached. Please upgrade your plan."
        )

    product = (data.product or "").strip()
    audience = (data.audience or "").strip()
    prompt = (data.prompt or data.text or "").strip()

    if not prompt and (not product or not audience):
        raise HTTPException(422, "Provide prompt/text or product+audience")

    system = (
        "You write HIGH-CONVERTING ads.\n"
        "ONLY output ads.\n"
        "NO tips.\n\n"
        "Output format:\n\n"
        "AD 1:\nHeadline:\nPrimary text:\nCTA:\n\n"
        "AD 2:\nHeadline:\nPrimary text:\nCTA:\n\n"
        "AD 3:\nHeadline:\nPrimary text:\nCTA:"
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

        db.add(SavedContent(
            user_id=user.id,
            content_type="ad",
            prompt=prompt if (product == "" and audience == "") else f"{product} → {audience}",
            result=output
        ))

        # 🔢 SAFE USAGE UPDATE
        user.used_generations = (user.used_generations or 0) + 1
        db.add(user)
        db.commit()
        db.refresh(user)

        return {"output": output}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"OpenAI error: {str(e)}")
