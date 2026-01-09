from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.utils.auth import get_current_user
from app.database.session import SessionLocal
from app.ai.restaurant_site_generator import generate_restaurant_website

router = APIRouter(prefix="/api/restaurants", tags=["Restaurant Websites"])


# -------------------------
# DB DEPENDENCY
# -------------------------
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# -------------------------
# REQUEST MODEL
# -------------------------
class RestaurantWebsiteRequest(BaseModel):
    username: str
    name: str
    cuisine: str
    city: str
    phone: str
    email: str | None = None


# -------------------------
# GENERATE WEBSITE (PAID USERS ONLY)
# -------------------------
@router.post("/generate")
def generate_restaurant_website_api(
    data: RestaurantWebsiteRequest,
    user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # 🔒 REQUIRE PAID PLAN
    if user.subscription_plan == "free":
        raise HTTPException(
            status_code=403,
            detail="Only paid users can create a website."
        )

    # 🔒 BASIC USERNAME VALIDATION
    if not data.username.isalnum():
        raise HTTPException(
            status_code=400,
            detail="Username must be alphanumeric (no spaces or symbols)."
        )

    # 🧠 AI GENERATION
    site_json = generate_restaurant_website({
        "name": data.name,
        "cuisine": data.cuisine,
        "city": data.city,
        "phone": data.phone,
        "email": data.email,
    })

    return {
        "username": data.username,
        "template": "restaurant",
        "content_json": site_json
    }
