from datetime import datetime
from app.database.session import SessionLocal

PLAN_LIMITS = {
    "free": 10,
    "basic": 100,
    "growth": None,
    "pro": None
}

def get_user_limit(subscription_plan: str):
    return PLAN_LIMITS.get(subscription_plan, 10)


def reset_if_new_month(user):
    now = datetime.utcnow()

    # First-time users → initialize safely
    if not user.last_reset:
        user.last_reset = now
        user.used_generations = 0
        return

    # If new month → reset
    if user.last_reset.month != now.month or user.last_reset.year != now.year:
        user.used_generations = 0
        user.last_reset = now
