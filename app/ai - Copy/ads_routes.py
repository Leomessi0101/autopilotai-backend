from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from app.utils.auth import get_current_user
from app.utils.usage import reset_if_new_month, get_user_limit
from app.utils.profile_context import build_profile_context
from app.database.session import SessionLocal
from app.database.models import User
from openai import OpenAI
import os

router = APIRouter()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

class AdsRequest(BaseModel):
    prompt: str

@router.post("/generate")
def generate_ads(data: AdsRequest, user=Depends(get_current_user)):
    db = SessionLocal()

    try:
        reset_if_new_month(user)

        limit = get_user_limit(user.subscription_plan)
        if limit is not None and user.used_generations >= limit:
            raise HTTPException(402, "Monthly limit reached")

        db_user = db.query(User).filter(User.id == user.id).first()
        profile_context = build_profile_context(db_user.profile)

        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You create high-converting ad copy."},
                {"role": "system", "content": profile_context},
                {"role": "user", "content": data.prompt},
            ]
        )

        msg = completion.choices[0].message
        text = msg.content if msg and msg.content else "No ad copy generated."

        user.used_generations += 1
        db.commit()

        return {"result": text}

    except Exception as e:
        return {"error": f"AI Error: {str(e)}"}

    finally:
        db.close()
