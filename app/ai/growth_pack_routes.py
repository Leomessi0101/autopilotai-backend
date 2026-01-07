from fastapi import APIRouter, Depends, HTTPException
from app.utils.auth import get_current_user
from app.database.session import SessionLocal
from app.utils.usage import get_user_limit, reset_if_new_month

# Import the actual generator functions
from app.ai.content_routes import generate_content_internal
from app.ai.email_routes import generate_email_internal
from app.ai.ads_routes import generate_ads_internal

router = APIRouter()


@router.post("/growth-pack/generate")
def generate_growth_pack(
    payload: dict,
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

    prompt = payload.get("prompt")
    if not prompt:
        raise HTTPException(status_code=400, detail="Prompt is required")

    # ---- Generate without charging ----
    content = generate_content_internal(
        prompt=prompt,
        user=user,
        charge_usage=False
    )

    email = generate_email_internal(
        prompt=prompt,
        user=user,
        charge_usage=False
    )

    ads = generate_ads_internal(
        prompt=prompt,
        user=user,
        charge_usage=False
    )

    # ---- Charge ONCE ----
    user.used_generations = (user.used_generations or 0) + 1
    db.add(user)
    db.commit()

    return {
        "content": content,
        "email": email,
        "ads": ads
    }
