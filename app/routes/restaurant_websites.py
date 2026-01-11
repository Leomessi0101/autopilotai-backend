import json
import os
import uuid
import boto3
from fastapi import UploadFile, File

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from fastapi import Body

from app.utils.auth import get_current_user
from app.database.session import SessionLocal
from app.database.models import Website
from app.ai.restaurant_site_generator import generate_restaurant_website

router = APIRouter(prefix="/api/restaurants", tags=["Restaurant Websites"])


# -------------------------
# R2 CONFIG
# -------------------------
R2_BUCKET = os.getenv("R2_BUCKET_NAME")
R2_PUBLIC_BASE_URL = os.getenv("R2_PUBLIC_BASE_URL")
R2_ENDPOINT = os.getenv("R2_ENDPOINT")

r2 = boto3.client(
    "s3",
    endpoint_url=R2_ENDPOINT,
    aws_access_key_id=os.getenv("CLOUDFLARE_API_TOKEN"),
    aws_secret_access_key=os.getenv("CLOUDFLARE_API_TOKEN"),
    region_name="auto",
)


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
# GENERATE + SAVE WEBSITE
# -------------------------
@router.post("/generate")
def generate_restaurant_website_api(
    data: RestaurantWebsiteRequest,
    user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # 🔒 REQUIRE PAID PLAN (TEMP DEV BYPASS OPTIONAL)
    if user.subscription_plan == "free" and user.email != "321@123.com":
        raise HTTPException(
            status_code=403,
            detail="Only paid users can create a website."
        )

    # 🔒 USERNAME VALIDATION
    if not data.username.isalnum():
        raise HTTPException(
            status_code=400,
            detail="Username must be alphanumeric (no spaces or symbols)."
        )

    # 🔒 PREVENT OVERWRITE
    existing = db.query(Website).filter(
        Website.username == data.username
    ).first()

    if existing:
        raise HTTPException(
            status_code=409,
            detail="This website username is already taken."
        )

    # 🧠 AI GENERATION
    try:
        site_json = generate_restaurant_website({
            "name": data.name,
            "cuisine": data.cuisine,
            "city": data.city,
            "phone": data.phone,
            "email": data.email,
        })
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"AI generation failed: {str(e)}"
        )

    # 💾 SAVE TO DB (JSON → STRING)
    try:
        website = Website(
            username=data.username,
            template="restaurant",
            content_json=json.dumps(site_json),
            user_id=user.id
        )

        db.add(website)
        db.commit()
        db.refresh(website)
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Database save failed: {str(e)}"
        )

    return {
        "success": True,
        "username": website.username,
        "url": f"/r/{website.username}"
    }


# -------------------------
# GET WEBSITE (PUBLIC)
# -------------------------
@router.get("/{username}")
def get_restaurant_website(username: str, db: Session = Depends(get_db)):
    website = db.query(Website).filter(Website.username == username).first()

    if not website:
        raise HTTPException(status_code=404, detail="Website not found")

    return {
        "username": website.username,
        "template": website.template,
        "content_json": website.content_json,
        "user_id": website.user_id,
    }


# -------------------------
# SAVE MENU (OWNER ONLY)
# -------------------------
@router.post("/{username}/menu")
def save_menu(
    username: str,
    payload: dict = Body(...),
    user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    website = db.query(Website).filter(Website.username == username).first()

    if not website:
        raise HTTPException(status_code=404, detail="Website not found")

    if website.user_id != user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    try:
        content = json.loads(website.content_json)

        # ✅ ALWAYS save menu (existing behavior)
        if "menu" in payload:
            content["menu"] = payload["menu"]

        # ✅ NEW: persist hero data (banner image, etc.)
        if "hero" in payload:
            content["hero"] = {
                **content.get("hero", {}),
                **payload["hero"],
            }

        website.content_json = json.dumps(content)
        db.commit()

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

    return {"success": True}


# -------------------------
# UPLOAD IMAGE (OWNER ONLY)
# -------------------------
@router.post("/{username}/upload-image")
def upload_menu_image(
    username: str,
    file: UploadFile = File(...),
    user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    website = db.query(Website).filter(Website.username == username).first()

    if not website:
        raise HTTPException(status_code=404, detail="Website not found")

    if website.user_id != user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    ext = file.filename.split(".")[-1]
    key = f"menu-items/{username}/{uuid.uuid4()}.{ext}"

    try:
        r2.upload_fileobj(
            file.file,
            R2_BUCKET,
            key,
            ExtraArgs={"ContentType": file.content_type},
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return {
        "url": f"{R2_PUBLIC_BASE_URL}/{key}"
    }
