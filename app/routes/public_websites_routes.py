"""
Public API routes for serving published websites
No authentication required - anyone can view published websites
"""

import json
import logging
from typing import Dict, Any
from fastapi import APIRouter, HTTPException
from sqlalchemy.orm import Session
from app.database.session import SessionLocal
from app.database.models import Website

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/public/websites", tags=["public-websites"])


@router.get("/{username}", response_model=Dict[str, Any])
async def get_public_website(username: str):
    """
    Get published website by username (PUBLIC endpoint, no authentication required)
    Only published websites are visible to the public.
    """
    db = SessionLocal()
    try:
        username = (username or "").strip().lower()
        
        if not username or len(username) < 3:
            raise HTTPException(status_code=400, detail="Invalid username format")
        
        logger.info(f"Public website request: {username}")
        
        site = db.query(Website).filter(Website.username == username).first()
        
        if not site:
            logger.warning(f"Website not found: {username}")
            raise HTTPException(
                status_code=404,
                detail=f"Website '{username}' not found"
            )
        
        # Only published websites are publicly visible
        if site.publish_status != "published":
            logger.warning(f"Website not published: {username}")
            raise HTTPException(
                status_code=403,
                detail="This website is private"
            )
        
        try:
            content = json.loads(site.content_json) if site.content_json else {}
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON in content_json for {username}")
            content = {}
        
        logger.info(f"Serving published website: {username}")
        
        return {
            "ok": True,
            "data": {
                "id": site.id,
                "username": site.username,
                "template": site.template,
                "html": site.html_content or "",
                "metadata": content.get("metadata", {}),
                "prompt": content.get("prompt", ""),
                "business_name": content.get("business_name", ""),
                "publish_status": site.publish_status,
                "custom_domain": site.custom_domain,
                "domain_verified": site.domain_verified,
                "created_at": site.created_at.isoformat() if site.created_at else None,
                "updated_at": site.updated_at.isoformat() if site.updated_at else None,
            }
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching website {username}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")
    finally:
        db.close()


@router.get("/{username}/preview", response_model=Dict[str, Any])
async def preview_website(username: str):
    """
    Preview a website (draft or published)
    Use ?edit=1 in the frontend to access this for draft websites
    """
    db = SessionLocal()
    try:
        username = (username or "").strip().lower()
        
        if not username or len(username) < 3:
            raise HTTPException(status_code=400, detail="Invalid username format")
        
        site = db.query(Website).filter(Website.username == username).first()
        
        if not site:
            raise HTTPException(status_code=404, detail="Website not found")
        
        try:
            content = json.loads(site.content_json) if site.content_json else {}
        except json.JSONDecodeError:
            content = {}
        
        logger.info(f"Previewing website: {username}")
        
        return {
            "ok": True,
            "data": {
                "id": site.id,
                "username": site.username,
                "template": site.template,
                "html": site.html_content or "",
                "metadata": content.get("metadata", {}),
                "prompt": content.get("prompt", ""),
                "business_name": content.get("business_name", ""),
                "publish_status": site.publish_status,
                "custom_domain": site.custom_domain,
                "domain_verified": site.domain_verified,
                "created_at": site.created_at.isoformat() if site.created_at else None,
                "updated_at": site.updated_at.isoformat() if site.updated_at else None,
            }
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error previewing website {username}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")
    finally:
        db.close()