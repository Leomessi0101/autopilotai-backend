import json
import os
import uuid
import boto3

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Body, Request
from sqlalchemy.orm import Session

from app.utils.auth import get_current_user
from app.database.session import SessionLocal
from app.database.models import Website, User

from app.ai.website_ai import generate_ai_structure  # deterministic structure

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
# OPTIONAL: OpenAI
# -------------------------
try:
    from openai import OpenAI
    _openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
except Exception:
    _openai_client = None

# -------------------------
# DB DEPENDENCY
# -------------------------
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def _safe_json_loads(s: str):
    try:
        return json.loads(s)
    except Exception:
        return None

def _clean_text(v):
    if v is None:
        return ""
    return str(v).strip()

# -------------------------
# DISABLED: LEGACY GENERATE
# -------------------------
@router.post("/generate")
def generate_restaurant_website_api():
    raise HTTPException(
        status_code=410,
        detail="Website generation has moved. Use the dashboard flow.",
    )

# -------------------------
# GET WEBSITE (PUBLIC / OWNER PREVIEW)
# -------------------------
@router.get("/{username}")
def get_restaurant_website(
    username: str,
    request: Request,
    db: Session = Depends(get_db),
):
    website = db.query(Website).filter(Website.username == username).first()
    if not website:
        raise HTTPException(status_code=404, detail="Website not found")

    # Detect owner (optional auth)
    owner_user = None
    try:
        owner_user = get_current_user(request)
    except Exception:
        pass

    is_owner = owner_user and owner_user.id == website.user_id
    edit_mode = request.query_params.get("edit") == "1"

    # -------------------------
    # PUBLISHING ENFORCEMENT
    # -------------------------
    if not is_owner:
        if website.publish_status != "published":
            raise HTTPException(
                status_code=403,
                detail="This website is not published yet",
            )

    # Lazy backfill AI structure
    if website.ai_structure_json is None:
        try:
            structure = generate_ai_structure(
                business_type=website.template or "business",
                goal="conversions",
            )
            website.ai_structure_json = json.dumps(structure)
            db.commit()
        except Exception:
            pass

    return {
        "username": website.username,
        "template": website.template,
        "content_json": website.content_json,
        "ai_structure_json": website.ai_structure_json,
        "user_id": website.user_id,
        "edit_mode": bool(is_owner and edit_mode),
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
        if "hero" in payload:
            content["hero"] = {**content.get("hero", {}), **payload["hero"]}
        if "contact" in payload:
            content["contact"] = {**content.get("contact", {}), **payload["contact"]}
        if "location" in payload:
            content["location"] = {**content.get("location", {}), **payload["location"]}
        if "hours" in payload:
            content["hours"] = {**content.get("hours", {}), **payload["hours"]}

        website.content_json = json.dumps(content)
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

    return {"success": True}

# -------------------------
# GENERIC CONTENT SAVE (OWNER)
# -------------------------
@router.post("/{username}/content")
def save_content(
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
        content = json.loads(website.content_json) if website.content_json else {}
        content.update(payload)
        website.content_json = json.dumps(content)
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

    return {"success": True}

# -------------------------
# IMAGE UPLOAD (OWNER)
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
