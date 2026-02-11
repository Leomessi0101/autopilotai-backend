from fastapi import APIRouter, HTTPException, Depends, Body
from sqlalchemy.orm import Session
import json
import os
from typing import Any
import hashlib
import base64

from app.database.session import SessionLocal
from app.database.models import Website, User
from app.utils.auth import get_current_user

from app.ai.website_ai_premium import generate_ai_plan, rewrite_content

# =========================
# OPTIONAL: OpenAI
# =========================
try:
    from openai import OpenAI
    _openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
except Exception:
    _openai_client = None

router = APIRouter(prefix="/api/dashboard/websites")

# =========================
# HELPERS
# =========================

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _clean_text(v: Any) -> str:
    if v is None:
        return ""
    return str(v).strip()


# =========================
# CREATE WEBSITE (UPDATED FOR HTML GENERATION)
# =========================

@router.post("/create")
def create_website(
    payload: dict = Body(...),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    print("=== [AUTOPILOTAI] /api/dashboard/websites/create HIT ===")

    plan = (user.subscription_plan or "free").lower()

    # 1 site per user
    if db.query(Website).filter(Website.user_id == user.id).count() >= 1:
        raise HTTPException(status_code=403, detail="Only one website allowed")

    username = (payload.get("username") or "").strip().lower()
    prompt = (payload.get("prompt") or "").strip()

    if not username:
        raise HTTPException(status_code=400, detail="Missing username")

    if db.query(Website).filter(Website.username == username).first():
        raise HTTPException(status_code=400, detail="Username already taken")

    # --- HARD REQUIRE: AI must be configured ---
    if not _openai_client:
        print("=== [AUTOPILOTAI] OPENAI CLIENT NOT CONFIGURED ===")
        raise HTTPException(
            status_code=500,
            detail="OpenAI not configured on server (OPENAI_API_KEY missing).",
        )

    # --- Generate complete AI plan (structure + HTML content) ---
    print("=== [AUTOPILOTAI] GENERATING AI WEBSITE WITH HTML ===")
    
    try:
        ai_plan = generate_ai_plan(
            ai_input={
                "prompt": prompt,
                "business_name": username.replace("-", " ").title(),
                "primary_goal": "Get started",
            },
            version=1,
        )
    except Exception as e:
        print(f"=== [AUTOPILOTAI] AI GENERATION FAILED: {str(e)} ===")
        raise HTTPException(
            status_code=500,
            detail=f"AI generation failed: {str(e)}"
        )

    structure = ai_plan["structure"]
    content = ai_plan["content"]
    template = ai_plan["template"]

    max_pages = 3 if plan == "pro" else 1

    structure["plan"] = {
        "name": plan,
        "max_pages": max_pages,
        "can_publish": plan in ("starter", "pro"),
    }

    # Validate content has sections
    if not content.get("sections"):
        print("=== [AUTOPILOTAI] NO SECTIONS IN CONTENT ===")
        raise HTTPException(
            status_code=500,
            detail="AI generation failed: no sections generated"
        )

    publish_status = "published" if plan in ("starter", "pro") else "draft"

    site = Website(
        user_id=user.id,
        username=username,
        template=template,
        content_json=json.dumps(content),
        ai_structure_json=json.dumps(structure),
        publish_status=publish_status,
    )

    db.add(site)
    db.commit()

    print("=== [AUTOPILOTAI] WEBSITE CREATED OK ===", username)

    return {
        "ok": True,
        "username": username,
        "redirect": f"/r/{username}?edit=1",
        "plan": plan,
        "max_pages": max_pages,
        "published": plan in ("starter", "pro"),
        "debug_has_ai": True,
        "debug_business_name": content.get("business_name"),
        "debug_sections": list(content.get("sections", {}).keys()),
    }


# =========================
# CONTENT REWRITER
# =========================

@router.post("/{username}/rewrite")
def rewrite_content_endpoint(
    username: str,
    payload: dict = Body(...),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Generates alternative versions of text content.
    """
    site = db.query(Website).filter(Website.username == username).first()
    if not site:
        raise HTTPException(status_code=404, detail="Website not found")
    if site.user_id != user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    text = payload.get("text", "")
    tone = payload.get("tone", "professional")

    if not text:
        raise HTTPException(status_code=400, detail="Missing text")

    try:
        alternatives = rewrite_content(
            original_text=text,
            tone=tone,
            business_context=site.template or "business",
        )
        
        return {
            "ok": True,
            "alternatives": alternatives,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =========================
# STYLE VARIATIONS
# =========================

@router.post("/{username}/style-variations")
def get_style_variations(
    username: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Generates 3 different style variations of the current website.
    """
    site = db.query(Website).filter(Website.username == username).first()
    if not site:
        raise HTTPException(status_code=404, detail="Website not found")
    if site.user_id != user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    try:
        content = json.loads(site.content_json)
        structure = json.loads(site.ai_structure_json)
        
        business_name = content.get("business_name", username.replace("-", " ").title())
        prompt = "Generate variations"  # We don't have the original prompt
        
        variations = generate_style_variations(
            business_name=business_name,
            prompt=prompt,
            template=site.template or "business",
            sections=structure.get("sections", []),
        )
        
        return {
            "ok": True,
            "variations": variations,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =========================
# CUSTOM DOMAIN (CONNECT + VERIFY)
# =========================

def _normalize_host(host: str) -> str:
    h = (host or "").strip().lower()
    if ":" in h:
        h = h.split(":", 1)[0]
    if h.startswith("www."):
        h = h[4:]
    return h

def _domain_token_for_site(site: Website) -> str:
    """
    Deterministic token (no DB column needed).
    User adds TXT record:
      autopilotai-verify=<token>
    """
    raw = f"autopilotai:{site.id}:{site.user_id}:{site.username}"
    digest = hashlib.sha256(raw.encode("utf-8")).digest()
    return base64.urlsafe_b64encode(digest).decode("utf-8").rstrip("=")[:32]

@router.get("/{username}/domain/status")
def domain_status(
    username: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    site = db.query(Website).filter(Website.username == username).first()
    if not site:
        raise HTTPException(status_code=404, detail="Website not found")
    if site.user_id != user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    token = _domain_token_for_site(site)
    return {
        "ok": True,
        "custom_domain": site.custom_domain,
        "domain_verified": bool(site.domain_verified),
        "txt_name": "@",
        "txt_value": f"autopilotai-verify={token}",
    }

@router.post("/{username}/domain/set")
def set_custom_domain(
    username: str,
    payload: dict = Body(...),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    site = db.query(Website).filter(Website.username == username).first()
    if not site:
        raise HTTPException(status_code=404, detail="Website not found")
    if site.user_id != user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    domain = _normalize_host(payload.get("domain") or "")
    if not domain:
        raise HTTPException(status_code=400, detail="Missing domain")

    existing = db.query(Website).filter(Website.custom_domain == domain).first()
    if existing and existing.id != site.id:
        raise HTTPException(status_code=400, detail="Domain already in use")

    site.custom_domain = domain
    site.domain_verified = False
    db.commit()

    token = _domain_token_for_site(site)
    return {
        "ok": True,
        "custom_domain": site.custom_domain,
        "domain_verified": bool(site.domain_verified),
        "txt_name": "@",
        "txt_value": f"autopilotai-verify={token}",
        "next": "Add TXT record, then call /verify",
    }

@router.post("/{username}/domain/verify")
def verify_custom_domain(
    username: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    site = db.query(Website).filter(Website.username == username).first()
    if not site:
        raise HTTPException(status_code=404, detail="Website not found")
    if site.user_id != user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    if not site.custom_domain:
        raise HTTPException(status_code=400, detail="No custom_domain set")

    token = _domain_token_for_site(site)
    expected = f"autopilotai-verify={token}"

    try:
        import dns.resolver  # type: ignore
    except Exception:
        raise HTTPException(
            status_code=500,
            detail="dnspython missing. Install with: pip install dnspython",
        )

    try:
        answers = dns.resolver.resolve(site.custom_domain, "TXT")
        values = []
        for rdata in answers:
            parts = []
            for s in getattr(rdata, "strings", []):
                try:
                    parts.append(s.decode("utf-8"))
                except Exception:
                    pass
            txt = "".join(parts).strip()
            if txt:
                values.append(txt)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"TXT lookup failed: {str(e)}")

    if expected not in values:
        raise HTTPException(
            status_code=400,
            detail=f"TXT not found. Expected: {expected}",
        )

    site.domain_verified = True
    db.commit()

    return {"ok": True, "custom_domain": site.custom_domain, "domain_verified": True}