from datetime import datetime
from app.database.session import SessionLocal

# FINAL LIMITS:
# free   -> 10 generations/month
# basic  -> 100 generations/month
# growth -> unlimited
# pro    -> unlimited

PLAN_LIMITS = {
    "free": 10,
    "basic": 100,
    "growth": None,   # Unlimited
    "pro": None       # Unlimited
}


def get_user_limit(subscription_plan: str):
    """
    Returns the monthly generation limit for the given subscription.
    None = unlimited
    """
    return PLAN_LIMITS.get(subscription_plan, 10)  # fallback = Free plan


def reset_if_new_month(user):
    """
    Resets the user's used_generations if a new month has started.
    """
    now = datetime.utcnow()

    # If user has never been reset, force initial value
    if not user.last_reset:
        user.last_reset = now
        user.used_generations = 0
        return

    # Different month = reset
    if user.last_reset.month != now.month or user.last_reset.year != now.year:
        user.used_generations = 0
        user.last_reset = now
