from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from app.utils.auth import get_current_user
from app.database.session import SessionLocal
from app.utils.usage import get_user_limit, reset_if_new_month

from app.ai.content_routes import generate_content_internal, ContentRequest
from app.ai.email_routes import generate_email_internal, EmailRequest
from app.ai.ads_routes import generate_ads_internal, AdRequest

router = APIRouter()


class GrowthPackRequest(BaseModel):
    prompt: str


@router.post("/growth-pack/generate")
def generate_growth_pack(
    data: GrowthPackRequest,
    user=Depends(get_current_user)
):
    db = SessionLocal()

    # ---- Reset month if needed ----
    reset_if_new_month(user)

    # ---- Check usage ONCE ----
    limit = get_user_limit(user.subscription_plan)
    used = user.used_generations or 0

    if limit is not None and used >= limit:
        raise HTTPException(status_code=403, detail="Usage limit reached")

    if not data.prompt.strip():
        raise HTTPException(status_code=400, detail="Prompt is required")

    # ---- Build request objects ----
    content_req = ContentRequest(prompt=data.prompt)
    email_req = EmailRequest(prompt=data.prompt)
    ads_req = AdRequest(prompt=data.prompt)

    # ---- Generate WITHOUT charging ----
    content = generate_content_internal(
        data=content_req,
        user=user,
        db=db,
        charge_usage=False
    )

    email = generate_email_internal(
        data=email_req,
        user=user,
        db=db,
        charge_usage=False
    )

    ads = generate_ads_internal(
        data=ads_req,
        user=user,
        db=db,
        charge_usage=False
    )

    # ---- Charge ONCE ----
    user.used_generations = (user.used_generations or 0) + 1
    db.add(user)
    db.commit()
    db.close()

    return {
        "content": content,
        "email": email,
        "ads": ads
    }
