from fastapi import APIRouter, Depends
from app.utils.auth import get_current_user
from app.utils.usage import get_user_limit

router = APIRouter()

@router.get("/usage")
def get_usage(user=Depends(get_current_user)):
    """
    Returns the user's usage + limit for the dashboard.
    """
    limit = get_user_limit(user.subscription_plan)
    used = user.used_generations

    return {
        "used": used,
        "limit": limit
    }
