import json
import os
import uuid
import boto3

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Body
from sqlalchemy.orm import Session

from app.utils.auth import get_current_user
from app.database.session import SessionLocal
from app.database.models import Website

from app.ai.website_ai import generate_ai_structure  # your deterministic structure

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
# OPTIONAL: OpenAI (server-side)
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

def _call_openai_json(prompt: str, temperature: float = 0.6, max_tokens: int = 700):
    """
    Returns dict or None. NEVER throws outwards.
    """
    if not _openai_client:
        return None

    try:
        resp = _openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You output ONLY valid JSON. No markdown. No commentary."},
                {"role": "user", "content": prompt},
            ],
            temperature=temperature,
            max_tokens=max_tokens,
        )
        raw = (resp.choices[0].message.content or "").strip()
        data = _safe_json_loads(raw)
        if isinstance(data, dict):
            return data
        return None
    except Exception:
        return None

def _regen_prompt(section: str, template: str, tone: str, content: dict):
    """
    Generate a strict JSON patch for ONE section.
    Patch must be shape: { "<section>": { ... } }
    """
    business_name = _clean_text(content.get("business_name")) or "The business"
    hero = content.get("hero") or {}
    about = content.get("about") or {}
    city = _clean_text((content.get("location") or {}).get("city")) or _clean_text((content.get("contact") or {}).get("address"))

    tone_rules = {
        "warm": "Warm, friendly, human, inviting. Slightly playful but still professional.",
        "premium": "Premium, elegant, confident, minimal fluff. Sounds expensive and trustworthy.",
        "bold": "Bold, direct, high-energy. Strong claims (but not fake statistics).",
        "minimal": "Short, clean, simple. No marketing fluff. Just clear information.",
    }
    tone_line = tone_rules.get(tone, tone_rules["warm"])

    # We only regenerate copy + optional structure fields the renderer supports.
    # Images should remain optional nulls.
    schemas = {
        "highlight": """
Return:
{
  "highlight": {
    "headline": "one strong line",
    "subheadline": "one supporting line"
  }
}
""",
        "about": """
Return:
{
  "about": {
    "paragraphs": ["paragraph1", "paragraph2", "optional paragraph3"],
    "image": null
  }
}
""",
        "services": """
Return:
{
  "services": {
    "title": "Services",
    "items": [
      { "title": "Service 1", "description": "1 sentence", "image": null },
      { "title": "Service 2", "description": "1 sentence", "image": null },
      { "title": "Service 3", "description": "1 sentence", "image": null }
    ]
  }
}
""",
        "trust": """
Return:
{
  "trust": {
    "items": ["reason 1", "reason 2", "reason 3"]
  }
}
""",
        "process": """
Return:
{
  "process": {
    "steps": [
      { "title": "Step 1", "description": "short" },
      { "title": "Step 2", "description": "short" },
      { "title": "Step 3", "description": "short" }
    ]
  }
}
""",
        "testimonial": """
Return:
{
  "testimonial": {
    "quote": "A realistic short testimonial (no fake stats).",
    "author": "Name or 'Customer'"
  }
}
""",
        "faq": """
Return:
{
  "faq": {
    "items": [
      { "q": "Question 1?", "a": "Answer 1." },
      { "q": "Question 2?", "a": "Answer 2." },
      { "q": "Question 3?", "a": "Answer 3." }
    ]
  }
}
""",
        "cta": """
Return:
{
  "cta": {
    "headline": "CTA headline",
    "subheadline": "CTA subheadline",
    "button": "Button text"
  }
}
""",
        # Gallery is images only, so regen doesn't help much — but we can add suggestion text:
        "gallery": """
Return:
{
  "gallery": {
    "images": []
  }
}
""",
        # Contact should remain user-filled:
        "contact": """
Return:
{
  "contact": {
    "phone": "",
    "email": "",
    "address": ""
  }
}
""",
    }

    schema_hint = schemas.get(section)
    if not schema_hint:
        return None

    user_context = f"""
Business name: {business_name}
Template type: {template}
City hint (optional): {city}

Existing hero headline: {_clean_text(hero.get("headline"))}
Existing hero subheadline: {_clean_text(hero.get("subheadline"))}

Existing about (first paragraph if any): {_clean_text((about.get("paragraphs") or [""])[0] if isinstance(about.get("paragraphs"), list) else "")}
"""

    rules = f"""
You are generating copy for a website homepage section.

Tone: {tone_line}

Rules:
- Output ONLY valid JSON (no markdown).
- No placeholders like "Your Business Name".
- No fake stats, no fake awards.
- Keep it punchy and readable.
- Make it specific to the business based on the context.
"""

    return f"""{rules}

Context:
{user_context}

Generate ONLY the JSON patch for section "{section}".

{schema_hint}
""".strip()

def _merge_patch(content: dict, patch: dict):
    if not isinstance(content, dict):
        content = {}
    if not isinstance(patch, dict):
        return content
    # shallow merge patch keys
    for k, v in patch.items():
        content[k] = v
    return content

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
def get_restaurant_website(username: str, db: Session = Depends(get_db)):
    website = db.query(Website).filter(Website.username == username).first()

    if not website:
        raise HTTPException(status_code=404, detail="Website not found")

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
# ✅ REGENERATE SECTION (OWNER ONLY)
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

    # Always prefer DB content as source of truth
    try:
        db_content = json.loads(website.content_json) if website.content_json else {}
    except Exception:
        db_content = {}

    # If client sent content, merge it in (so regen reflects latest unsaved UI edits if any)
    if isinstance(current, dict):
        for k, v in current.items():
            db_content[k] = v

    template = (website.template or "business").lower()

    prompt = _regen_prompt(section=section, template=template, tone=tone, content=db_content)
    if not prompt:
        raise HTTPException(status_code=400, detail="Unknown section")

    patch = _call_openai_json(prompt, temperature=0.65, max_tokens=800)
    if not patch:
        # Fallback: do not break UX
        patch = {section: db_content.get(section) or {}}

    # Merge patch + persist
    merged = _merge_patch(db_content, patch)
    website.content_json = json.dumps(merged)
    db.commit()

    return {"ok": True, "patch": patch}
