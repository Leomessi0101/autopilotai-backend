import json
import os
import uuid
import boto3

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Body, Request
from sqlalchemy.orm import Session
from jose import jwt

from app.utils.auth import get_current_user
from app.database.session import SessionLocal
from app.database.models import Website, User
from app.routes.stripe_routes import SECRET_KEY

from app.ai.website_ai import generate_ai_structure  # deterministic structure

router = APIRouter(prefix="/api/restaurants", tags=["Restaurant Websites"])

# ✅ domains router (used by Next.js middleware)
domains_router = APIRouter(prefix="/api/domains", tags=["Domains"])

# -------------------------
# R2 CONFIG
# -------------------------
R2_BUCKET = os.getenv("R2_BUCKET_NAME")
R2_PUBLIC_BASE_URL = os.getenv("R2_PUBLIC_BASE_URL")
R2_ENDPOINT = os.getenv("R2_ENDPOINT")

r2 = boto3.client(
    "s3",
    endpoint_url=R2_ENDPOINT,
    aws_access_key_id="12345678901234567890123456789012",       # ✅ hardcoded 32 chars
    aws_secret_access_key="12345678901234567890123456789012",   # ✅ hardcoded 32 chars
    aws_session_token=os.getenv("R2_SESSION_TOKEN") or os.getenv("CLOUDFLARE_API_TOKEN"),
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

def _normalize_host(host: str) -> str:
    h = (host or "").strip().lower()
    if ":" in h:
        h = h.split(":", 1)[0]
    if h.startswith("www."):
        h = h[4:]
    return h

# -------------------------
# ✅ RESOLVE DOMAIN -> USERNAME (for middleware.ts)
# -------------------------
@domains_router.get("/resolve")
def resolve_domain(
    host: str,
    db: Session = Depends(get_db),
):
    """
    Returns: { "username": "<username>" }
    Used by Next.js middleware to rewrite custom domains to /r/[username].

    Only returns results for domains that are VERIFIED.
    """
    normalized = _normalize_host(host)
    if not normalized:
        raise HTTPException(status_code=400, detail="Missing host")

    website = (
        db.query(Website)
        .filter(Website.custom_domain == normalized)
        .filter(Website.domain_verified == True)  # noqa: E712
        .first()
    )

    if not website:
        raise HTTPException(status_code=404, detail="Domain not found")

    return {"username": website.username}

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
# GET WEBSITE (PUBLIC / OWNER)
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

    # -------------------------
    # OWNER DETECTION (JWT)
    # -------------------------
    is_owner = False
    auth_header = request.headers.get("authorization")

    if auth_header and auth_header.lower().startswith("bearer "):
        token = auth_header.split(" ")[1]
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            is_owner = payload.get("user_id") == website.user_id
        except Exception:
            pass

    # -------------------------
    # PUBLIC ACCESS → ENFORCE SUBSCRIPTION
    # -------------------------
    if not is_owner:
        if not owner or not owner.subscription_plan:
            return {
                "suspended": True,
                "username": website.username,
            }

    # -------------------------
    # LAZY BACKFILL AI STRUCTURE
    # -------------------------
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

    section = (payload.get("section") or "").lower()

    try:
        current = json.loads(website.content_json or "{}")
    except Exception:
        current = {}

    # 🔒 SAFE FALLBACK: no AI yet, just return existing section
    if section not in current:
        return {"ok": True, "patch": {}}

    return {
        "ok": True,
        "patch": {
            section: current.get(section)
        },
    }
