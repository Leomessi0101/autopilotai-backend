from fastapi import APIRouter, Depends
from app.utils.auth import get_current_user
from app.utils.usage import get_user_limit, reset_if_new_month
from app.database.session import SessionLocal

router = APIRouter()

@router.get("/usage")
def get_usage(user=Depends(get_current_user)):
    db = SessionLocal()

    # Reset month if needed
    reset_if_new_month(user)
    db.add(user)
    db.commit()
    db.refresh(user)

    limit = get_user_limit(user.subscription_plan)

    # SAFETY: Always return integers
    used = user.used_generations if user.used_generations is not None else 0

    return {
        "used": int(used),
        "limit": limit,               # None is OK for unlimited
        "remaining": None if limit is None else max(limit - used, 0),
        "unlimited": limit is None
    }
