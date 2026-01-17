from fastapi import APIRouter, HTTPException, Request, Query
import stripe
import os
from sqlalchemy.orm import Session
from jose import jwt, JWTError

from app.database.session import SessionLocal
from app.database.models import User

router = APIRouter()

# -------------------- STRIPE CONFIG --------------------
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")

FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")

PRICE_IDS = {
    "starter": os.getenv("PRICE_STARTER"),
    "pro": os.getenv("PRICE_PRO"),
}

# -------------------- JWT CONFIG --------------------
SECRET_KEY = os.getenv("JWT_SECRET", "supersecretkey")
ALGORITHM = "HS256"


# -------------------- MANUAL AUTH --------------------
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
    plan: str = Query(...),
    request: Request = None,
):
    plan = plan.lower()

    if plan not in PRICE_IDS or not PRICE_IDS[plan]:
        raise HTTPException(status_code=400, detail="Invalid plan")

    user = get_current_user_from_request(request)

    try:
        session = stripe.checkout.Session.create(
            mode="subscription",
            payment_method_types=["card"],
            line_items=[{"price": PRICE_IDS[plan], "quantity": 1}],
            allow_promotion_codes=True,
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
        raise HTTPException(status_code=500, detail="Stripe checkout failed")


# -------------------- STRIPE WEBHOOK --------------------
@router.post("/webhook")
async def stripe_webhook(request: Request):
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, WEBHOOK_SECRET)
    except Exception as e:
        print("Webhook signature error:", e)
        raise HTTPException(status_code=400, detail="Invalid webhook signature")

    db: Session = SessionLocal()

    try:
        event_type = event["type"]
        data = event["data"]["object"]

        # -------------------- CHECKOUT COMPLETED --------------------
        if event_type == "checkout.session.completed":
            user_id = int(data["metadata"]["user_id"])
            plan = data["metadata"]["plan"]

            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                return {"status": "ok"}

            user.subscription_plan = plan
            user.stripe_customer_id = data.get("customer")
            user.stripe_subscription_id = data.get("subscription")
            user.used_generations = 0

            if plan == "starter":
                user.can_publish = True
                user.max_pages = 1
            elif plan == "pro":
                user.can_publish = True
                user.max_pages = 3

            db.commit()
            print(f"✅ User {user.id} subscribed to {plan}")

        # -------------------- SUBSCRIPTION UPDATED --------------------
        elif event_type == "customer.subscription.updated":
            subscription = data
            customer_id = subscription.get("customer")
            status = subscription.get("status")

            user = db.query(User).filter(
                User.stripe_customer_id == customer_id
            ).first()

            if user:
                if status in ["active", "trialing"]:
                    user.can_publish = True
                    db.commit()
                    print(f"ℹ️ Subscription active for user {user.id}")
                else:
                    user.can_publish = False
                    db.commit()
                    print(f"⚠️ Subscription paused for user {user.id}")

        # -------------------- SUBSCRIPTION DELETED --------------------
        elif event_type == "customer.subscription.deleted":
            customer_id = data.get("customer")

            user = db.query(User).filter(
                User.stripe_customer_id == customer_id
            ).first()

            if user:
                user.subscription_plan = "free"
                user.can_publish = False
                user.max_pages = 1
                user.stripe_subscription_id = None
                db.commit()
                print(f"❌ Subscription cancelled for user {user.id}")

        # -------------------- PAYMENT FAILED --------------------
        elif event_type == "invoice.payment_failed":
            customer_id = data.get("customer")

            user = db.query(User).filter(
                User.stripe_customer_id == customer_id
            ).first()

            if user:
                user.can_publish = False
                db.commit()
                print(f"❌ Payment failed — publishing disabled for user {user.id}")

        # -------------------- PAYMENT SUCCEEDED --------------------
        elif event_type == "invoice.payment_succeeded":
            customer_id = data.get("customer")

            user = db.query(User).filter(
                User.stripe_customer_id == customer_id
            ).first()

            if user and user.subscription_plan in ["starter", "pro"]:
                user.can_publish = True
                db.commit()
                print(f"✅ Payment recovered for user {user.id}")

    finally:
        db.close()

    return {"status": "ok"}


# -------------------- CUSTOMER BILLING PORTAL --------------------
@router.post("/customer-portal")
def create_customer_portal(request: Request):
    user = get_current_user_from_request(request)

    if not user.email:
        raise HTTPException(status_code=400, detail="No email on account")

    try:
        customers = stripe.Customer.list(email=user.email).data

        if customers:
            customer_id = customers[0].id
        else:
            customer = stripe.Customer.create(email=user.email)
            customer_id = customer.id

        session = stripe.billing_portal.Session.create(
            customer=customer_id,
            return_url=f"{FRONTEND_URL}/billing",
        )

        return {"url": session.url}

    except Exception as e:
        print("STRIPE PORTAL ERROR:", e)
        raise HTTPException(status_code=500, detail="Could not open billing portal")
