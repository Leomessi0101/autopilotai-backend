from fastapi import APIRouter, HTTPException, Depends
from app.utils.auth import get_current_user
from fastapi import Request
import stripe
import os
from sqlalchemy.orm import Session
from app.database.session import SessionLocal
from app.database.models import User

router = APIRouter()

stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")

PRICE_IDS = {
    "basic": os.getenv("PRICE_BASIC"),
    "growth": os.getenv("PRICE_GROWTH"),
    "pro": os.getenv("PRICE_PRO"),
}


@router.post("/create-checkout-session")
def create_checkout_session(
    plan: str,
    user=Depends(get_current_user),
):
    plan = plan.lower()

    if plan not in PRICE_IDS or not PRICE_IDS[plan]:
        raise HTTPException(400, "Invalid or missing price ID for plan")

    try:
        session = stripe.checkout.Session.create(
            mode="subscription",
            payment_method_types=["card"],
            line_items=[
                {
                    "price": PRICE_IDS[plan],
                    "quantity": 1,
                }
            ],
            success_url=f"{FRONTEND_URL}/dashboard?checkout=success",
            cancel_url=f"{FRONTEND_URL}/pricing?checkout=cancelled",
            customer_email=user.email,
            metadata={
                "user_id": str(user.id),
                "plan": plan,
            },
        )

        return {"checkout_url": session.url}

    except Exception as e:
        # 🔥 THIS IS THE IMPORTANT PART
        print("STRIPE ERROR:", str(e))
        raise HTTPException(500, "Stripe checkout failed")

@router.post("/webhook")
async def stripe_webhook(request: Request):
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    try:
        event = stripe.Webhook.construct_event(
            payload,
            sig_header,
            os.getenv("STRIPE_WEBHOOK_SECRET"),
        )
    except Exception as e:
        print("Webhook signature error:", e)
        raise HTTPException(400, "Invalid webhook signature")

    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]

        user_id = int(session["metadata"]["user_id"])
        plan = session["metadata"]["plan"]

        db: Session = SessionLocal()
        user = db.query(User).filter(User.id == user_id).first()

        if user:
            user.subscription_plan = plan

            # reset usage on upgrade
            user.used_generations = 0

            # OPTIONAL: save Stripe IDs for later
            user.stripe_customer_id = session.get("customer")
            user.stripe_subscription_id = session.get("subscription")

            db.commit()
            print(f"✅ User {user.id} upgraded to {plan}")

        db.close()

    return {"status": "ok"}
