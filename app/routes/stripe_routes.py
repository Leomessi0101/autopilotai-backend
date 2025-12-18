from fastapi import APIRouter, HTTPException, Request
import stripe
import os
from sqlalchemy.orm import Session
from app.database.session import SessionLocal
from app.database.models import User
from jose import jwt, JWTError

router = APIRouter()

# -------------------- STRIPE CONFIG --------------------
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")

FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")

PRICE_IDS = {
    "basic": os.getenv("PRICE_BASIC"),
    "growth": os.getenv("PRICE_GROWTH"),
    "pro": os.getenv("PRICE_PRO"),
}

# -------------------- JWT CONFIG --------------------
SECRET_KEY = os.getenv("JWT_SECRET", "supersecretkey")
ALGORITHM = "HS256"


# -------------------- MANUAL AUTH (BULLETPROOF) --------------------
def get_current_user_from_request(request: Request) -> User:
    auth_header = request.headers.get("authorization")

    if not auth_header or not auth_header.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Missing authorization header")

    token = auth_header.split(" ")[1]

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("user_id")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token payload")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

    db: Session = SessionLocal()
    user = db.query(User).filter(User.id == user_id).first()
    db.close()

    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    return user


# -------------------- CREATE CHECKOUT SESSION --------------------
@router.post("/create-checkout-session")
def create_checkout_session(
    plan: str,
    request: Request,
):
    plan = plan.lower()

    if plan not in PRICE_IDS or not PRICE_IDS[plan]:
        raise HTTPException(400, "Invalid or missing price ID for plan")

    # 🔐 MANUAL AUTH
    user = get_current_user_from_request(request)

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
        print("STRIPE ERROR:", str(e))
        raise HTTPException(500, "Stripe checkout failed")


# -------------------- STRIPE WEBHOOK --------------------
@router.post("/webhook")
async def stripe_webhook(request: Request):
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    try:
        event = stripe.Webhook.construct_event(
            payload,
            sig_header,
            WEBHOOK_SECRET,
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

            # -------------------- PLAN LIMITS --------------------
            if plan == "basic":
                user.monthly_limit = 100
            elif plan == "growth":
                user.monthly_limit = 500
            elif plan == "pro":
                user.monthly_limit = 1500

            user.used_generations = 0
            user.stripe_customer_id = session.get("customer")
            user.stripe_subscription_id = session.get("subscription")

            db.commit()
            print(f"✅ User {user.id} upgraded to {plan}")

        db.close()

    return {"status": "ok"}
