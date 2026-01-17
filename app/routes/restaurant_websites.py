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
# GET WEBSITE (PUBLIC, READ-ONLY)
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

    owner = db.query(User).filter(User.id == website.user_id).first()

    # Detect edit mode (owner only)
    edit_mode = request.query_params.get("edit") == "1"

    if not edit_mode:
        # PUBLIC ACCESS → enforce subscription
        if not owner or owner.subscription_plan is None:
            return {
                "suspended": True,
                "username": website.username,
            }

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
            content["hero"] = {**content.get("hero", {}), **payload["hero"]}

        if "contact" in payload and isinstance(payload["contact"], dict):
            content["contact"] = {**content.get("contact", {}), **payload["contact"]}

        if "location" in payload and isinstance(payload["location"], dict):
            content["location"] = {**content.get("location", {}), **payload["location"]}

        if "hours" in payload and isinstance(payload["hours"], dict):
            content["hours"] = {**content.get("hours", {}), **payload["hours"]}

        website.content_json = json.dumps(content)
        db.commit()

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

    return {"success": True}

# -------------------------
# SAVE WEBSITE CONTENT (OWNER ONLY) — GENERIC PATCH
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
        for k, v in payload.items():
            content[k] = v
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

# -------------------------
# SAVE AI CONTENT (OWNER ONLY)
# -------------------------
@router.post("/{username}/save")
def save_ai_content(
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
        website.content_json = json.dumps(payload)
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

    return {"success": True}

# -------------------------
# REGENERATE SECTION (OWNER ONLY)
# -------------------------
@router.post("/{username}/regenerate-section")
def regenerate_section(
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

    section = _clean_text(payload.get("section")).lower()
    tone = _clean_text(payload.get("tone")).lower() or "warm"
    current = payload.get("content")

    try:
        db_content = json.loads(website.content_json) if website.content_json else {}
    except Exception:
        db_content = {}

    if isinstance(current, dict):
        for k, v in current.items():
            db_content[k] = v

    template = (website.template or "business").lower()

    from app.ai.website_ai import generate_ai_structure  # safe local import

    prompt = None
    if _openai_client:
        from app.routes.restaurant_websites import _regen_prompt, _call_openai_json, _merge_patch
        prompt = _regen_prompt(section, template, tone, db_content)

    if not prompt:
        raise HTTPException(status_code=400, detail="Unknown section")

    patch = _call_openai_json(prompt, temperature=0.65, max_tokens=800)
    if not patch:
        patch = {section: db_content.get(section) or {}}

    merged = _merge_patch(db_content, patch)
    website.content_json = json.dumps(merged)
    db.commit()

    return {"ok": True, "patch": patch}
