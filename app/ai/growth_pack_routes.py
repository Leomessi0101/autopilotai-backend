from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from app.utils.auth import get_current_user
from app.database.session import SessionLocal
from app.utils.usage import get_user_limit, reset_if_new_month
from app.database.models import SavedContent
from openai import OpenAI
import os

router = APIRouter()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


class GrowthPackRequest(BaseModel):
    prompt: str


@router.post("/growth-pack/generate")
def generate_growth_pack(
    data: GrowthPackRequest,
    user=Depends(get_current_user)
):
    db = SessionLocal()

    try:
        reset_if_new_month(user)

        limit = get_user_limit(user.subscription_plan)
        used = user.used_generations or 0

        if limit is not None and used >= limit:
            raise HTTPException(
                status_code=403,
                detail="Monthly generation limit reached. Please upgrade."
            )

        if not data.prompt.strip():
            raise HTTPException(status_code=400, detail="Prompt is required")

        system = (
            "You are a senior growth marketer.\n"
            "Generate THREE sections.\n"
            "NO explanations.\n\n"
            "FORMAT STRICTLY:\n\n"
            "=== SOCIAL POSTS ===\n"
            "5 high-quality social posts.\n\n"
            "=== EMAIL ===\n"
            "One persuasive business email.\n\n"
            "=== ADS ===\n"
            "3 ads with headline, primary text, CTA.\n"
        )

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": data.prompt},
            ]
        )

        output = response.choices[0].message.content.strip()
        if not output:
            raise HTTPException(500, "Empty AI response")

        # Split sections
        def extract(label):
            if label not in output:
                return ""
            return output.split(label)[1].split("===")[0].strip()

        social = extract("=== SOCIAL POSTS ===")
        email = extract("=== EMAIL ===")
        ads = extract("=== ADS ===")

        # Save as ONE grouped item
        db.add(SavedContent(
            user_id=user.id,
            content_type="growth_pack",
            prompt=data.prompt,
            result=output
        ))

        # Charge ONCE
        user.used_generations = (user.used_generations or 0) + 1
        db.add(user)
        db.commit()

        return {
            "content": social,
            "email": email,
            "ads": ads
        }

    finally:
        db.close()
