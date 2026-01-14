import json
import os
import uuid
import boto3

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Body
from sqlalchemy.orm import Session

from app.utils.auth import get_current_user
from app.database.session import SessionLocal
from app.database.models import Website

from app.ai.website_ai import generate_ai_structure  # canonical AI layout

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
# DISABLED: LEGACY GENERATE
# -------------------------
@router.post("/generate")
def generate_restaurant_website_api():
    """
    ❌ Disabled.
    Website creation is now handled exclusively via:
    POST /api/dashboard/websites/create
    """
    raise HTTPException(
        status_code=410,
        detail="Website generation has moved. Use the dashboard flow.",
    )


# -------------------------
# GET WEBSITE (PUBLIC, READ-ONLY)
# -------------------------
@router.get("/{username}")
def get_restaurant_website(username: str, db: Session = Depends(get_db)):
    website = db.query(Website).filter(Website.username == username).first()

    if not website:
        raise HTTPException(status_code=404, detail="Website not found")

    # --------------------------------------------------
    # 🧠 AI STRUCTURE (LAZY BACKFILL, SAFE)
    # --------------------------------------------------
    if website.ai_structure_json is None:
        try:
            structure = generate_ai_structure(
                business_type=website.template or "business",
                goal="conversions",
            )
            website.ai_structure_json = json.dumps(structure)
            db.commit()
        except Exception:
            # do not block rendering if structure fails
            pass

    return {
        "username": website.username,
        "template": website.template,
        "content_json": website.content_json,
        "ai_structure_json": website.ai_structure_json,
        "user_id": website.user_id,
    }


# -------------------------
# SAVE WEBSITE CONTENT (OWNER ONLY)
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

        if "menu" in payload:
            content["menu"] = payload["menu"]

        if "hero" in payload and isinstance(payload["hero"], dict):
            content["hero"] = {
                **content.get("hero", {}),
                **payload["hero"],
            }

        if "contact" in payload and isinstance(payload["contact"], dict):
            content["contact"] = {
                **content.get("contact", {}),
                **payload["contact"],
            }

        if "location" in payload and isinstance(payload["location"], dict):
            content["location"] = {
                **content.get("location", {}),
                **payload["location"],
            }

        if "hours" in payload and isinstance(payload["hours"], dict):
            content["hours"] = {
                **content.get("hours", {}),
                **payload["hours"],
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

    return {"url": f"{R2_PUBLIC_BASE_URL}/{key}"}
