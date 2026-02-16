"""
Dashboard Websites Routes - FastAPI endpoints for AI website management
Integrates with Master Architect website_ai.py system
"""

import json
import logging
import os
import hashlib
import base64
from typing import Optional, Dict, Any
from datetime import datetime

from fastapi import APIRouter, HTTPException, Depends, Body, Query
from sqlalchemy.orm import Session

from app.database.session import SessionLocal
from app.database.models import Website, User
from app.utils.auth import get_current_user
from app.ai.website_ai import generate_ai_plan, rewrite_content, get_design_tokens

# ============================================================================
# LOGGING SETUP
# ============================================================================

logger = logging.getLogger(__name__)

# ============================================================================
# CONFIGURATION
# ============================================================================

WEBSITE_LIMITS = {
    "free": {"max_websites": 0, "can_publish": False, "custom_domain": False},
    "starter": {"max_websites": 1, "can_publish": True, "custom_domain": False},
    "pro": {"max_websites": 5, "can_publish": True, "custom_domain": True},
}

# ============================================================================
# ROUTER SETUP
# ============================================================================

router = APIRouter(
    prefix="/api/dashboard/websites",
    tags=["websites"],
    responses={
        400: {"description": "Bad request"},
        403: {"description": "Forbidden"},
        404: {"description": "Not found"},
        500: {"description": "Internal server error"},
    },
)

# ============================================================================
# DEPENDENCY INJECTION
# ============================================================================


def get_db():
    """Database session dependency"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_user_plan_limits(user: User) -> Dict[str, Any]:
    """Get plan limits for user"""
    plan = (user.subscription_plan or "free").lower()
    return WEBSITE_LIMITS.get(plan, WEBSITE_LIMITS["free"])


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================


def normalize_username(username: str) -> str:
    """Normalize and validate username"""
    normalized = (username or "").strip().lower()
    if not normalized or len(normalized) < 3:
        raise ValueError("Username must be at least 3 characters")
    if not all(c.isalnum() or c == "-" for c in normalized):
        raise ValueError("Username can only contain letters, numbers, and hyphens")
    return normalized


def normalize_domain(domain: str) -> str:
    """Normalize domain name"""
    normalized = (domain or "").strip().lower()
    if ":" in normalized:
        normalized = normalized.split(":", 1)[0]
    if normalized.startswith("www."):
        normalized = normalized[4:]
    return normalized


def generate_domain_token(site: Website) -> str:
    """Generate DNS verification token for domain"""
    raw = f"autopilotai:{site.id}:{site.user_id}:{site.username}"
    digest = hashlib.sha256(raw.encode("utf-8")).digest()
    return base64.urlsafe_b64encode(digest).decode("utf-8").rstrip("=")[:32]


def check_username_available(db: Session, username: str, exclude_site_id: Optional[int] = None) -> bool:
    """Check if username is available"""
    query = db.query(Website).filter(Website.username == username)
    if exclude_site_id:
        query = query.filter(Website.id != exclude_site_id)
    return query.first() is None


def check_domain_available(db: Session, domain: str, exclude_site_id: Optional[int] = None) -> bool:
    """Check if custom domain is available"""
    query = db.query(Website).filter(Website.custom_domain == domain)
    if exclude_site_id:
        query = query.filter(Website.id != exclude_site_id)
    return query.first() is None


def get_website_or_404(db: Session, username: str) -> Website:
    """Get website by username or raise 404"""
    site = db.query(Website).filter(Website.username == username).first()
    if not site:
        raise HTTPException(status_code=404, detail=f"Website '{username}' not found")
    return site


def authorize_website_access(site: Website, user: User):
    """Verify user owns the website"""
    if site.user_id != user.id:
        logger.warning(f"Unauthorized access attempt: user {user.id} accessing site {site.id}")
        raise HTTPException(
            status_code=403,
            detail="You do not have permission to access this website"
        )


def log_action(action: str, username: str, user_id: int, details: str = ""):
    """Log user action for audit trail"""
    logger.info(f"[{action}] user_id={user_id} username={username} {details}")


# ============================================================================
# CREATE WEBSITE
# ============================================================================


@router.post("/create", response_model=Dict[str, Any])
async def create_website(
    payload: Dict[str, Any] = Body(...),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Create a new AI-generated website using Master Architect system.
    
    Request body:
    {
        "username": "my-site",  # subdomain name (required)
        "prompt": "AI SaaS platform with analytics",  # business description (required)
        "name": "My Company"  # optional: override business name
    }
    """
    try:
        # ---- Input Validation ----
        username = payload.get("username", "").strip().lower()
        prompt = payload.get("prompt", "").strip()
        business_name = payload.get("name", "").strip() or username.replace("-", " ").title()

        if not username:
            raise HTTPException(status_code=400, detail="username is required")
        if not prompt:
            raise HTTPException(status_code=400, detail="prompt (business description) is required")

        # Validate username format
        try:
            username = normalize_username(username)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

        # ---- Plan Limits ----
        plan_limits = get_user_plan_limits(user)
        
        if not plan_limits["can_publish"]:
            raise HTTPException(
                status_code=403,
                detail=f"Website creation requires at least Starter plan (you have {user.subscription_plan or 'free'})"
            )

        existing_count = db.query(Website).filter(Website.user_id == user.id).count()
        if existing_count >= plan_limits["max_websites"]:
            raise HTTPException(
                status_code=403,
                detail=f"You have reached your limit of {plan_limits['max_websites']} website(s). Delete one to create another."
            )

        # ---- Check Availability ----
        if not check_username_available(db, username):
            raise HTTPException(status_code=409, detail=f"Username '{username}' is already taken")

        log_action("CREATE_WEBSITE_START", username, user.id)

        # ---- Generate Website with AI ----
        logger.info(f"Generating website for: {username} ({business_name})")
        
        try:
            ai_result = generate_ai_plan(
                ai_input={
                    "business_name": business_name,
                    "prompt": prompt,
                },
                version=1,
            )
        except Exception as e:
            logger.error(f"AI generation failed for {username}: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail=f"Website generation failed: {str(e)}"
            )

        # ---- Validate AI Output ----
        if ai_result.get("metadata", {}).get("status") == "error":
            error_msg = ai_result.get("metadata", {}).get("error", "Unknown error")
            logger.error(f"AI generation error for {username}: {error_msg}")
            raise HTTPException(status_code=500, detail=f"AI error: {error_msg}")

        html_content = ai_result.get("html", "")
        metadata = ai_result.get("metadata", {})
        
        if not html_content:
            raise HTTPException(status_code=500, detail="No HTML content generated")

        # ---- Create Database Record ----
        site = Website(
            user_id=user.id,
            username=username,
            template="master_architect_v1",
            html_content=html_content,
            content_json=json.dumps({
                "metadata": metadata,
                "prompt": prompt,
                "business_name": business_name,
            }),
            publish_status="published" if plan_limits["can_publish"] else "draft",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        db.add(site)
        db.commit()
        db.refresh(site)

        log_action("CREATE_WEBSITE_SUCCESS", username, user.id, f"theme={metadata.get('theme')} industry={metadata.get('industry')}")

        return {
            "ok": True,
            "status": "success",
            "data": {
                "website_id": site.id,
                "username": site.username,
                "theme": metadata.get("theme", "pro_light"),
                "industry": metadata.get("industry", "tech"),
                "template": "master_architect",
                "publish_status": site.publish_status,
                "created_at": site.created_at.isoformat() if site.created_at else None,
                "preview_url": f"/api/preview/{username}",
                "edit_url": f"/dashboard/websites/{username}/edit",
                "published_url": f"/r/{username}" if site.publish_status == "published" else None,
            },
            "message": f"Website '{username}' created successfully!",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error creating website: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


# ============================================================================
# GET WEBSITE (PREVIEW)
# ============================================================================


@router.get("/{username}", response_model=Dict[str, Any])
async def get_website(
    username: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get website details and HTML content"""
    try:
        username = normalize_username(username)
        site = get_website_or_404(db, username)
        authorize_website_access(site, user)

        content = json.loads(site.content_json) if site.content_json else {}

        return {
            "ok": True,
            "data": {
                "id": site.id,
                "username": site.username,
                "template": site.template,
                "html": site.html_content,
                "metadata": content.get("metadata", {}),
                "prompt": content.get("prompt", ""),
                "business_name": content.get("business_name", ""),
                "publish_status": site.publish_status,
                "custom_domain": site.custom_domain,
                "domain_verified": site.domain_verified,
                "created_at": site.created_at.isoformat() if site.created_at else None,
                "updated_at": site.updated_at.isoformat() if site.updated_at else None,
            },
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching website {username}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# UPDATE WEBSITE CONTENT
# ============================================================================


@router.put("/{username}", response_model=Dict[str, Any])
async def update_website(
    username: str,
    payload: Dict[str, Any] = Body(...),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Update website content and metadata.
    
    Request body:
    {
        "html": "<html>...</html>",  # optional: new HTML
        "metadata": {...},  # optional: update metadata
        "prompt": "Updated description",  # optional
        "business_name": "Updated Name"  # optional
    }
    """
    try:
        username = normalize_username(username)
        site = get_website_or_404(db, username)
        authorize_website_access(site, user)

        # Update content
        current_content = json.loads(site.content_json) if site.content_json else {}

        if "html" in payload and payload["html"]:
            site.html_content = payload["html"]

        if "metadata" in payload:
            current_content["metadata"] = {**current_content.get("metadata", {}), **payload["metadata"]}

        if "prompt" in payload:
            current_content["prompt"] = payload["prompt"]

        if "business_name" in payload:
            current_content["business_name"] = payload["business_name"]

        site.content_json = json.dumps(current_content)
        site.updated_at = datetime.utcnow()

        db.commit()

        log_action("UPDATE_WEBSITE", username, user.id)

        return {
            "ok": True,
            "status": "success",
            "message": "Website updated successfully",
            "updated_at": site.updated_at.isoformat(),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating website {username}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# REGENERATE WEBSITE
# ============================================================================


@router.post("/{username}/regenerate", response_model=Dict[str, Any])
async def regenerate_website(
    username: str,
    payload: Dict[str, Any] = Body(...),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Regenerate website with new or updated prompt.
    
    Request body:
    {
        "prompt": "New business description",  # required
        "keep_domains": true  # optional: keep custom domain settings
    }
    """
    try:
        username = normalize_username(username)
        prompt = payload.get("prompt", "").strip()

        if not prompt:
            raise HTTPException(status_code=400, detail="prompt is required")

        site = get_website_or_404(db, username)
        authorize_website_access(site, user)

        log_action("REGENERATE_WEBSITE_START", username, user.id)

        # Get current business name
        current_content = json.loads(site.content_json) if site.content_json else {}
        business_name = current_content.get("business_name", username.replace("-", " ").title())

        # Generate new website
        try:
            ai_result = generate_ai_plan(
                ai_input={
                    "business_name": business_name,
                    "prompt": prompt,
                },
                version=1,
            )
        except Exception as e:
            logger.error(f"Regeneration failed for {username}: {str(e)}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Regeneration failed: {str(e)}")

        if ai_result.get("metadata", {}).get("status") == "error":
            raise HTTPException(status_code=500, detail="AI generation error")

        html_content = ai_result.get("html", "")
        metadata = ai_result.get("metadata", {})

        if not html_content:
            raise HTTPException(status_code=500, detail="No HTML generated")

        # Update site
        site.html_content = html_content
        site.content_json = json.dumps({
            "metadata": metadata,
            "prompt": prompt,
            "business_name": business_name,
        })
        site.updated_at = datetime.utcnow()

        db.commit()

        log_action("REGENERATE_WEBSITE_SUCCESS", username, user.id)

        return {
            "ok": True,
            "status": "success",
            "message": "Website regenerated successfully",
            "data": {
                "theme": metadata.get("theme"),
                "industry": metadata.get("industry"),
                "updated_at": site.updated_at.isoformat(),
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error regenerating website {username}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# REWRITE CONTENT
# ============================================================================


@router.post("/{username}/rewrite", response_model=Dict[str, Any])
async def rewrite_text(
    username: str,
    payload: Dict[str, Any] = Body(...),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Generate alternative versions of text content.
    
    Request body:
    {
        "text": "Original text to rewrite",  # required
        "tone": "professional|casual|luxury|technical"  # optional, default: professional
    }
    """
    try:
        username = normalize_username(username)
        text = payload.get("text", "").strip()
        tone = payload.get("tone", "professional").lower()

        if not text:
            raise HTTPException(status_code=400, detail="text is required")

        if tone not in ["professional", "casual", "luxury", "technical"]:
            tone = "professional"

        site = get_website_or_404(db, username)
        authorize_website_access(site, user)

        current_content = json.loads(site.content_json) if site.content_json else {}
        business_context = current_content.get("prompt", "business")

        try:
            alternatives = rewrite_content(
                original_text=text,
                tone=tone,
                business_context=business_context,
            )
        except Exception as e:
            logger.warning(f"Rewrite failed for {username}: {str(e)}")
            alternatives = [text, text, text]  # Fallback

        return {
            "ok": True,
            "status": "success",
            "original": text,
            "alternatives": alternatives,
            "tone": tone,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error rewriting text for {username}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# PUBLISH/UNPUBLISH
# ============================================================================


@router.post("/{username}/publish", response_model=Dict[str, Any])
async def publish_website(
    username: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Publish website to public URL"""
    try:
        username = normalize_username(username)
        plan_limits = get_user_plan_limits(user)

        if not plan_limits["can_publish"]:
            raise HTTPException(
                status_code=403,
                detail="Publishing requires Starter or Pro plan"
            )

        site = get_website_or_404(db, username)
        authorize_website_access(site, user)

        site.publish_status = "published"
        site.updated_at = datetime.utcnow()
        db.commit()

        log_action("PUBLISH_WEBSITE", username, user.id)

        return {
            "ok": True,
            "status": "success",
            "message": f"Website published at /r/{username}",
            "url": f"/r/{username}",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error publishing {username}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{username}/unpublish", response_model=Dict[str, Any])
async def unpublish_website(
    username: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Unpublish website (make draft)"""
    try:
        username = normalize_username(username)
        site = get_website_or_404(db, username)
        authorize_website_access(site, user)

        site.publish_status = "draft"
        site.updated_at = datetime.utcnow()
        db.commit()

        log_action("UNPUBLISH_WEBSITE", username, user.id)

        return {
            "ok": True,
            "status": "success",
            "message": "Website unpublished",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error unpublishing {username}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# CUSTOM DOMAIN
# ============================================================================


@router.get("/{username}/domain/status", response_model=Dict[str, Any])
async def get_domain_status(
    username: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get custom domain status and verification token"""
    try:
        username = normalize_username(username)
        site = get_website_or_404(db, username)
        authorize_website_access(site, user)

        token = generate_domain_token(site)

        return {
            "ok": True,
            "data": {
                "custom_domain": site.custom_domain,
                "domain_verified": bool(site.domain_verified),
                "verification_method": "dns_txt",
                "dns_record": {
                    "name": "@",
                    "type": "TXT",
                    "value": f"autopilotai-verify={token}",
                },
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting domain status for {username}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{username}/domain/set", response_model=Dict[str, Any])
async def set_custom_domain(
    username: str,
    payload: Dict[str, Any] = Body(...),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Set custom domain for website.
    
    Request body:
    {
        "domain": "example.com"  # required
    }
    
    Requires Pro plan.
    """
    try:
        username = normalize_username(username)
        plan_limits = get_user_plan_limits(user)

        if not plan_limits["custom_domain"]:
            raise HTTPException(
                status_code=403,
                detail="Custom domains require Pro plan"
            )

        domain = normalize_domain(payload.get("domain", ""))
        if not domain or len(domain) < 3:
            raise HTTPException(status_code=400, detail="Valid domain is required")

        site = get_website_or_404(db, username)
        authorize_website_access(site, user)

        # Check availability
        if not check_domain_available(db, domain, exclude_site_id=site.id):
            raise HTTPException(status_code=409, detail=f"Domain '{domain}' is already in use")

        site.custom_domain = domain
        site.domain_verified = False
        site.updated_at = datetime.utcnow()
        db.commit()

        token = generate_domain_token(site)

        log_action("SET_CUSTOM_DOMAIN", username, user.id, f"domain={domain}")

        return {
            "ok": True,
            "status": "success",
            "message": f"Domain '{domain}' set. Add the TXT record below to verify.",
            "data": {
                "domain": domain,
                "verified": False,
                "dns_record": {
                    "name": "@",
                    "type": "TXT",
                    "value": f"autopilotai-verify={token}",
                },
                "instructions": "1. Add the TXT record to your domain's DNS settings\n2. Wait 24 hours for propagation\n3. Call /verify endpoint to confirm",
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error setting domain for {username}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{username}/domain/verify", response_model=Dict[str, Any])
async def verify_custom_domain(
    username: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Verify custom domain ownership via DNS TXT record"""
    try:
        username = normalize_username(username)
        site = get_website_or_404(db, username)
        authorize_website_access(site, user)

        if not site.custom_domain:
            raise HTTPException(status_code=400, detail="No custom domain set")

        token = generate_domain_token(site)
        expected = f"autopilotai-verify={token}"

        # Try DNS lookup
        try:
            import dns.resolver
            answers = dns.resolver.resolve(site.custom_domain, "TXT")
            txt_values = []

            for rdata in answers:
                for s in getattr(rdata, "strings", []):
                    try:
                        txt_values.append(s.decode("utf-8"))
                    except Exception:
                        pass

            if not any(expected in val for val in txt_values):
                raise HTTPException(
                    status_code=400,
                    detail=f"TXT record not found. Expected: {expected}. Found: {txt_values}"
                )

        except ImportError:
            raise HTTPException(
                status_code=500,
                detail="DNS verification unavailable. Please contact support."
            )
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"DNS lookup failed: {str(e)}")

        # Verified!
        site.domain_verified = True
        site.updated_at = datetime.utcnow()
        db.commit()

        log_action("VERIFY_DOMAIN_SUCCESS", username, user.id, f"domain={site.custom_domain}")

        return {
            "ok": True,
            "status": "success",
            "message": "Domain verified successfully!",
            "data": {
                "domain": site.custom_domain,
                "verified": True,
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error verifying domain for {username}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# DELETE WEBSITE
# ============================================================================


@router.delete("/{username}", response_model=Dict[str, Any])
async def delete_website(
    username: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete website permanently"""
    try:
        username = normalize_username(username)
        site = get_website_or_404(db, username)
        authorize_website_access(site, user)

        site_id = site.id
        db.delete(site)
        db.commit()

        log_action("DELETE_WEBSITE", username, user.id)

        return {
            "ok": True,
            "status": "success",
            "message": f"Website '{username}' deleted",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting {username}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# DESIGN TOKENS / UTILITIES
# ============================================================================


@router.get("/design/tokens", response_model=Dict[str, Any])
async def get_tokens(user: User = Depends(get_current_user)):
    """Get design system tokens (for frontend)"""
    try:
        tokens = get_design_tokens()
        return {
            "ok": True,
            "data": tokens,
        }
    except Exception as e:
        logger.error(f"Error fetching design tokens: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# LIST USER'S WEBSITES
# ============================================================================


@router.get("", response_model=Dict[str, Any])
async def list_websites(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List all websites owned by current user"""
    try:
        sites = db.query(Website).filter(Website.user_id == user.id).all()

        websites = []
        for site in sites:
            content = json.loads(site.content_json) if site.content_json else {}
            websites.append({
                "id": site.id,
                "username": site.username,
                "template": site.template,
                "theme": content.get("metadata", {}).get("theme", "pro_light"),
                "industry": content.get("metadata", {}).get("industry", "tech"),
                "business_name": content.get("business_name", site.username),
                "publish_status": site.publish_status,
                "custom_domain": site.custom_domain,
                "domain_verified": site.domain_verified,
                "created_at": site.created_at.isoformat() if site.created_at else None,
                "updated_at": site.updated_at.isoformat() if site.updated_at else None,
            })

        return {
            "ok": True,
            "data": {
                "websites": websites,
                "count": len(websites),
                "plan_limits": get_user_plan_limits(user),
            },
        }

    except Exception as e:
        logger.error(f"Error listing websites for user {user.id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))