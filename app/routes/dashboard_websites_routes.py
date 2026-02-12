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
from app.ai.website_ai import generate_ai_plan, rewrite_content

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
# CREATE WEBSITE
# =========================

@router.post("/create")
def create_website(
    payload: dict = Body(...),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Creates a new AI-generated website with ultra-modern flowing design.
    """
    print("=== [AUTOPILOTAI] Creating new website ===")

    plan = (user.subscription_plan or "free").lower()

    # Check limit (1 site per user)
    existing_count = db.query(Website).filter(Website.user_id == user.id).count()
    if existing_count >= 1:
        raise HTTPException(
            status_code=403,
            detail="You already have a website. Delete it first to create a new one.",
        )

    username = (payload.get("username") or "").strip().lower()
    prompt = (payload.get("prompt") or "").strip()

    if not username:
        raise HTTPException(status_code=400, detail="Username is required")

    if not prompt:
        raise HTTPException(status_code=400, detail="Business description is required")

    # Check username availability
    if db.query(Website).filter(Website.username == username).first():
        raise HTTPException(status_code=400, detail="Username already taken")

    # Require OpenAI
    if not _openai_client:
        raise HTTPException(
            status_code=500,
            detail="AI service not configured. Please contact support.",
        )

    # Generate AI website
    print(f"=== [AUTOPILOTAI] Generating AI website for: {username} ===")
    
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
        print(f"=== [AUTOPILOTAI] AI generation failed: {str(e)} ===")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate website: {str(e)}",
        )

    structure = ai_plan["structure"]
    content = ai_plan["content"]
    template = ai_plan["template"]

    # Validate
    if not content.get("sections"):
        raise HTTPException(
            status_code=500,
            detail="AI generation failed: no sections created",
        )

    # Plan settings
    max_pages = 3 if plan == "pro" else 1
    can_publish = plan in ("starter", "pro")

    structure["plan"] = {
        "name": plan,
        "max_pages": max_pages,
        "can_publish": can_publish,
    }

    publish_status = "published" if can_publish else "draft"

    # Create website record
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
    db.refresh(site)

    print(f"=== [AUTOPILOTAI] Website created successfully: {username} ===")

    return {
        "ok": True,
        "username": username,
        "redirect": f"/r/{username}?edit=1",
        "plan": plan,
        "can_publish": can_publish,
        "design": structure.get("design", {}).get("name", "Modern"),
        "palette": structure.get("palette", {}).get("name", "Purple"),
    }


# =========================
# SAVE WEBSITE
# =========================

@router.post("/{username}/save")
def save_website(
    username: str,
    payload: dict = Body(...),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Saves website content updates.
    """
    site = db.query(Website).filter(Website.username == username).first()
    
    if not site:
        raise HTTPException(status_code=404, detail="Website not found")
    
    if site.user_id != user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    try:
        # Update content
        site.content_json = json.dumps(payload)
        db.commit()
        
        return {"ok": True, "message": "Saved successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =========================
# CONTENT REWRITER
# =========================

@router.post("/{username}/rewrite")
def rewrite_text(
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
        raise HTTPException(status_code=400, detail="Text is required")

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
# DELETE WEBSITE
# =========================

@router.delete("/{username}")
def delete_website(
    username: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Deletes a website.
    """
    site = db.query(Website).filter(Website.username == username).first()
    
    if not site:
        raise HTTPException(status_code=404, detail="Website not found")
    
    if site.user_id != user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    db.delete(site)
    db.commit()

    return {"ok": True, "message": "Website deleted successfully"}


# =========================
# CUSTOM DOMAIN
# =========================

def _normalize_host(host: str) -> str:
    """Normalize domain name."""
    h = (host or "").strip().lower()
    if ":" in h:
        h = h.split(":", 1)[0]
    if h.startswith("www."):
        h = h[4:]
    return h


def _domain_token_for_site(site: Website) -> str:
    """Generate verification token for domain."""
    raw = f"autopilotai:{site.id}:{site.user_id}:{site.username}"
    digest = hashlib.sha256(raw.encode("utf-8")).digest()
    return base64.urlsafe_b64encode(digest).decode("utf-8").rstrip("=")[:32]


@router.get("/{username}/domain/status")
def domain_status(
    username: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get custom domain status.
    """
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
    """
    Set custom domain (requires Pro plan).
    """
    site = db.query(Website).filter(Website.username == username).first()
    
    if not site:
        raise HTTPException(status_code=404, detail="Website not found")
    
    if site.user_id != user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    # Check plan
    if user.subscription_plan not in ("pro",):
        raise HTTPException(
            status_code=403,
            detail="Custom domains require Pro plan",
        )

    domain = _normalize_host(payload.get("domain") or "")
    
    if not domain:
        raise HTTPException(status_code=400, detail="Domain is required")

    # Check if domain is already taken
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
        "domain_verified": False,
        "txt_name": "@",
        "txt_value": f"autopilotai-verify={token}",
        "instructions": "Add this TXT record to your domain's DNS, then verify.",
    }


@router.post("/{username}/domain/verify")
def verify_custom_domain(
    username: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Verify custom domain ownership via DNS TXT record.
    """
    site = db.query(Website).filter(Website.username == username).first()
    
    if not site:
        raise HTTPException(status_code=404, detail="Website not found")
    
    if site.user_id != user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    if not site.custom_domain:
        raise HTTPException(status_code=400, detail="No custom domain set")

    token = _domain_token_for_site(site)
    expected = f"autopilotai-verify={token}"

    try:
        import dns.resolver
    except ImportError:
        raise HTTPException(
            status_code=500,
            detail="DNS verification not available. Please contact support.",
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
        raise HTTPException(
            status_code=400,
            detail=f"DNS lookup failed: {str(e)}. Make sure you added the TXT record.",
        )

    if expected not in values:
        raise HTTPException(
            status_code=400,
            detail=f"TXT record not found. Expected: {expected}",
        )

    # Verified!
    site.domain_verified = True
    db.commit()

    return {
        "ok": True,
        "custom_domain": site.custom_domain,
        "domain_verified": True,
        "message": "Domain verified successfully!",
    }


# =========================
# PUBLISH WEBSITE
# =========================

@router.post("/{username}/publish")
def publish_website(
    username: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Publish website (requires paid plan).
    """
    site = db.query(Website).filter(Website.username == username).first()
    
    if not site:
        raise HTTPException(status_code=404, detail="Website not found")
    
    if site.user_id != user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    # Check plan
    if user.subscription_plan not in ("starter", "pro"):
        raise HTTPException(
            status_code=403,
            detail="Publishing requires Starter or Pro plan",
        )

    site.publish_status = "published"
    db.commit()

    return {
        "ok": True,
        "message": "Website published successfully!",
        "url": f"https://autopilotai.app/r/{username}",
    }