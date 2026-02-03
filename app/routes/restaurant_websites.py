import json
import os

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Body, Request
from sqlalchemy.orm import Session
from jose import jwt

from app.utils.auth import get_current_user
from app.database.session import SessionLocal
from app.database.models import Website, User


router = APIRouter(prefix="/api/restaurants", tags=["Restaurant Websites"])

# ✅ domains router (used by Next.js middleware)
domains_router = APIRouter(prefix="/api/domains", tags=["Domains"])


# -------------------------
# OPTIONAL: OpenAI (unused here, safe to keep)
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


def _normalize_host(host: str) -> str:
    h = (host or "").strip().lower()
    if ":" in h:
        h = h.split(":", 1)[0]
    if h.startswith("www."):
        h = h[4:]
    return h


def _get_jwt_secret() -> str:
    """
    Keep this consistent with whatever you use to sign tokens.
    Your get_current_user() already works, so this is ONLY for
    public GET owner-detection (optional).
    """
    return os.getenv("JWT_SECRET") or os.getenv("SECRET_KEY") or os.getenv("JWT_SECRET_KEY") or "supersecretkey"


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
    # OWNER DETECTION (JWT, optional)
    # -------------------------
    is_owner = False
    auth_header = request.headers.get("authorization") or request.headers.get("Authorization")

    if auth_header and auth_header.lower().startswith("bearer "):
        token = auth_header.split(" ", 1)[1].strip()
        try:
            payload = jwt.decode(token, _get_jwt_secret(), algorithms=["HS256"])
            is_owner = payload.get("user_id") == website.user_id
        except Exception:
            is_owner = False

    # -------------------------
    # PUBLIC ACCESS → ENFORCE SUBSCRIPTION
    # If viewer is NOT owner and owner has no plan -> suspend public view
    # -------------------------
    if not is_owner:
        if not owner or not getattr(owner, "subscription_plan", None):
            return {
                "suspended": True,
                "username": website.username,
            }

    # -------------------------
    # ✅ ALWAYS RETURN WEBSITE DATA (THIS WAS MISSING BEFORE)
    # -------------------------
    return {
        "suspended": False,
        "username": website.username,
        "template": website.template,
        "user_id": website.user_id,
        "ai_structure_json": website.ai_structure_json,
        "content_json": website.content_json,
        "custom_domain": website.custom_domain,
        "domain_verified": getattr(website, "domain_verified", None),
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
        content = _safe_json_loads(website.content_json or "") or {}

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
        content = _safe_json_loads(website.content_json or "") or {}
        for k, v in payload.items():
            content[k] = v
        website.content_json = json.dumps(content)
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

    return {"success": True}


# -------------------------
# UPLOAD IMAGE (OWNER ONLY) — uses Cloudflare Worker
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

    worker_url = (os.getenv("R2_UPLOAD_WORKER_URL") or "").strip().rstrip("/")
    upload_token = (os.getenv("R2_UPLOAD_WORKER_TOKEN") or "").strip()

    if not worker_url or not upload_token:
        raise HTTPException(
            status_code=500,
            detail="Upload worker not configured (missing R2_UPLOAD_WORKER_URL or R2_UPLOAD_WORKER_TOKEN)",
        )

    try:
        import requests
    except Exception:
        raise HTTPException(status_code=500, detail="requests not installed on server")

    # read file bytes
    try:
        data = file.file.read()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to read file: {str(e)}")

    # base64 encode for worker JSON
    import base64
    file_b64 = base64.b64encode(data).decode("utf-8")

    payload = {
        "username": username,
        "filename": file.filename or "upload.bin",
        "contentType": file.content_type or "application/octet-stream",
        "fileBase64": file_b64,
    }

    try:
        resp = requests.post(
            f"{worker_url}/upload",
            json=payload,
            headers={"Authorization": f"Bearer {upload_token}"},
            timeout=60,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload worker request failed: {str(e)}")

    if resp.status_code != 200:
        try:
            detail = resp.json()
        except Exception:
            detail = resp.text
        raise HTTPException(status_code=500, detail={"worker_status": resp.status_code, "worker_error": detail})

    try:
        out = resp.json()
    except Exception:
        raise HTTPException(status_code=500, detail="Worker returned invalid JSON")

    url = out.get("url")
    if not url:
        raise HTTPException(status_code=500, detail="Worker response missing url")

    return {"url": url}


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
# REGENERATE SECTION (OWNER ONLY) — stub / safe
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

    if section not in current:
        return {"ok": True, "patch": {}}

    return {"ok": True, "patch": {section: current.get(section)}}
