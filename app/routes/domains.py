# Domains Router
# Save to: C:\Users\Raidi\autopilotai-backend\app\routes\domains.py

import asyncio
import logging
import os
import re
from typing import Optional

import stripe
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Header
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import text
from jose import jwt

from app.database.session import SessionLocal
from app.database.models import User
from app.utils.porkbun import porkbun
from app.utils.dns_verification import dns_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/domains", tags=["domains"])

stripe.api_key = os.getenv("STRIPE_SECRET_KEY", "")

SECRET = os.getenv("JWT_SECRET", "supersecretkey")
ALGORITHM = "HS256"
WORKER_SECRET = os.getenv("WORKER_SECRET", "")
MAX_DOMAINS_PER_USER = int(os.getenv("MAX_DOMAINS_PER_USER", "10"))
DOMAIN_MARKUP_PERCENT = float(os.getenv("DOMAIN_MARKUP_PERCENT", "30"))


# ─────────────────────────────────────────────────────────
# DATABASE
# ─────────────────────────────────────────────────────────

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ─────────────────────────────────────────────────────────
# AUTH
# ─────────────────────────────────────────────────────────

def get_current_user(Authorization: str = Header(None), db: Session = Depends(get_db)) -> User:
    if not Authorization:
        raise HTTPException(401, "Missing Authorization header")
    token = Authorization.replace("Bearer ", "")
    try:
        payload = jwt.decode(token, SECRET, algorithms=[ALGORITHM])
        user_id = payload["user_id"]
    except:
        raise HTTPException(401, "Invalid token")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(404, "User not found")
    return user


# ─────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────

DOMAIN_REGEX = re.compile(
    r"^(?:[a-zA-Z0-9](?:[a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}$"
)

def normalize_domain(domain: str) -> str:
    return domain.lower().strip().removeprefix("https://").removeprefix("http://").rstrip("/")

def validate_domain(domain: str) -> str:
    domain = normalize_domain(domain)
    if not DOMAIN_REGEX.match(domain):
        raise HTTPException(status_code=422, detail=f"Invalid domain: {domain!r}")
    if domain.endswith(".autopilotai.dev"):
        raise HTTPException(status_code=422, detail="Cannot use autopilotai.dev subdomains")
    return domain


# ─────────────────────────────────────────────────────────
# SCHEMAS
# ─────────────────────────────────────────────────────────

class ConnectDomainRequest(BaseModel):
    domain: str

class RegistrantInfo(BaseModel):
    first_name: str
    last_name: str
    email: str
    phone: str
    address1: str
    city: str
    state: str
    postal_code: str
    country: str = "US"

class PurchaseDomainRequest(BaseModel):
    domain: str
    registrant: RegistrantInfo
    years: int = 1
    stripe_payment_method_id: str


# ─────────────────────────────────────────────────────────
# 1. CONNECT AN EXISTING DOMAIN
# ─────────────────────────────────────────────────────────

@router.post("/connect")
def connect_domain(
    body: ConnectDomainRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    domain = validate_domain(body.domain)
    apex = domain.removeprefix("www.")

    existing = db.execute(
        text("SELECT id, user_id FROM custom_domains WHERE domain = :d OR apex_domain = :a"),
        {"d": domain, "a": apex},
    ).fetchone()

    if existing:
        if str(existing.user_id) == str(current_user.id):
            raise HTTPException(status_code=409, detail="You've already connected this domain")
        raise HTTPException(status_code=409, detail="This domain is already in use")

    count = db.execute(
        text("SELECT COUNT(*) FROM custom_domains WHERE user_id = :uid AND status != 'suspended'"),
        {"uid": current_user.id},
    ).scalar()

    if count >= MAX_DOMAINS_PER_USER:
        raise HTTPException(status_code=429, detail=f"Maximum of {MAX_DOMAINS_PER_USER} domains per account")

    result = db.execute(
        text("""
            INSERT INTO custom_domains (user_id, domain, apex_domain, status, source)
            VALUES (:uid, :domain, :apex, 'pending', 'connected')
            RETURNING id, created_at
        """),
        {"uid": current_user.id, "domain": domain, "apex": apex},
    ).fetchone()
    db.commit()

    instructions = dns_service.get_instructions(domain)

    return {
        "id": str(result.id),
        "domain": domain,
        "status": "pending",
        "source": "connected",
        "created_at": result.created_at,
        "dns_instructions": instructions,
    }


# ─────────────────────────────────────────────────────────
# 2. VERIFY DNS
# ─────────────────────────────────────────────────────────

@router.post("/connect/{domain_id}/verify")
def verify_domain_dns(
    domain_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    row = db.execute(
        text("SELECT * FROM custom_domains WHERE id = :id AND user_id = :uid"),
        {"id": domain_id, "uid": current_user.id},
    ).fetchone()

    if not row:
        raise HTTPException(status_code=404, detail="Domain not found")

    if row.status == "active":
        return {"verified": True, "status": "active", "method": row.verification_method}

    result = asyncio.run(dns_service.verify(row.domain))

    if result.verified:
        db.execute(
            text("""
                UPDATE custom_domains
                SET status = 'active',
                    verification_method = :method,
                    last_dns_value = :value,
                    verified_at = NOW(),
                    last_checked_at = NOW(),
                    check_failures = 0
                WHERE id = :id
            """),
            {"id": domain_id, "method": result.method, "value": result.resolved_value},
        )
        db.execute(
            text("""
                INSERT INTO domain_resolution_cache (domain, username, user_id)
                VALUES (:domain, :username, :uid)
                ON CONFLICT (domain) DO UPDATE
                SET username = :username, user_id = :uid, cached_at = NOW()
            """),
            {"domain": row.domain, "username": current_user.name, "uid": current_user.id},
        )
        db.commit()
        return {
            "verified": True,
            "status": "active",
            "method": result.method,
            "message": f"Domain verified! Your site is now live at {row.domain}",
        }
    else:
        db.execute(
            text("""
                UPDATE custom_domains
                SET last_checked_at = NOW(),
                    last_dns_value = :value,
                    check_failures = check_failures + 1
                WHERE id = :id
            """),
            {"id": domain_id, "value": result.resolved_value},
        )
        db.commit()
        return {
            "verified": False,
            "status": row.status,
            "error": result.error,
            "hint": "DNS changes can take up to 48 hours. Double-check your DNS provider settings.",
        }


# ─────────────────────────────────────────────────────────
# 3. INTERNAL: Domain Resolution (called by Cloudflare Worker)
# ─────────────────────────────────────────────────────────

@router.get("/resolve")
def resolve_domain(
    host: str,
    db: Session = Depends(get_db),
    x_worker_secret: str = Header(None),
):
    if x_worker_secret != WORKER_SECRET:
        raise HTTPException(status_code=403, detail="Forbidden")

    host = host.lower().strip().removeprefix("www.")

    cached = db.execute(
        text("SELECT username FROM domain_resolution_cache WHERE domain = :d"),
        {"d": host},
    ).fetchone()

    if cached:
        return {"username": cached.username, "source": "cache"}

    result = db.execute(
        text("""
            SELECT u.name as username
            FROM custom_domains cd
            JOIN users u ON u.id = cd.user_id
            WHERE (cd.domain = :host OR cd.apex_domain = :host)
              AND cd.status = 'active'
            LIMIT 1
        """),
        {"host": host},
    ).fetchone()

    if not result:
        raise HTTPException(status_code=404, detail="Domain not mapped")

    return {"username": result.username, "source": "db"}


# ─────────────────────────────────────────────────────────
# 4. DOMAIN SEARCH
# ─────────────────────────────────────────────────────────

@router.get("/search")
async def search_domains(
    q: str,
    current_user: User = Depends(get_current_user),
):
    q = q.lower().strip()

    if "." in q:
        domain = validate_domain(q)
        result = await porkbun.check_domain(domain)
        results = [result]
    else:
        results = await porkbun.check_multiple_domains(q)

    MARKUP = DOMAIN_MARKUP_PERCENT / 100

    return {
        "query": q,
        "results": [
            {
                "domain": r.domain,
                "available": r.available,
                "tld": r.tld,
                "display_price_cents": int(r.price_cents * (1 + MARKUP)),
                "renewal_price_cents": int(r.renewal_cents * (1 + MARKUP)),
                "display_price": f"${r.price_cents * (1 + MARKUP) / 100:.2f}",
                "popular": r.tld in ("com", "io", "co", "dev"),
            }
            for r in results
        ],
    }


# ─────────────────────────────────────────────────────────
# 5. PURCHASE A DOMAIN
# ─────────────────────────────────────────────────────────

@router.post("/purchase")
async def purchase_domain(
    body: PurchaseDomainRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    domain = validate_domain(body.domain)

    availability = await porkbun.check_domain(domain)
    if not availability.available:
        raise HTTPException(status_code=409, detail=f"{domain} is no longer available")

    MARKUP = DOMAIN_MARKUP_PERCENT / 100
    price_cents = int(availability.price_cents * (1 + MARKUP))
    renewal_cents = int(availability.renewal_cents * (1 + MARKUP))

    try:
        intent = stripe.PaymentIntent.create(
            amount=price_cents,
            currency="usd",
            payment_method=body.stripe_payment_method_id,
            confirm=True,
            automatic_payment_methods={"enabled": True, "allow_redirects": "never"},
            metadata={"type": "domain_purchase", "domain": domain, "user_id": str(current_user.id)},
            description=f"Domain registration: {domain} (1 year)",
        )
    except stripe.error.CardError as e:
        raise HTTPException(status_code=402, detail=f"Payment failed: {e.user_message}")
    except stripe.error.StripeError as e:
        raise HTTPException(status_code=500, detail="Payment processing error")

    if intent.status not in ("succeeded", "requires_capture"):
        raise HTTPException(status_code=402, detail="Payment not completed")

    registrant = body.registrant
    purchase_result = db.execute(
        text("""
            INSERT INTO domain_purchases (
                user_id, domain, tld,
                registrant_first_name, registrant_last_name, registrant_email,
                registrant_phone, registrant_address1, registrant_city,
                registrant_state, registrant_postal_code, registrant_country,
                purchase_price_cents, registrar_price_cents, renewal_price_cents,
                stripe_payment_intent_id, status
            ) VALUES (
                :uid, :domain, :tld,
                :first, :last, :email, :phone, :addr, :city, :state, :zip, :country,
                :price, :reg_price, :renewal, :intent_id, 'paid'
            ) RETURNING id
        """),
        {
            "uid": current_user.id, "domain": domain, "tld": domain.split(".")[-1],
            "first": registrant.first_name, "last": registrant.last_name,
            "email": registrant.email, "phone": registrant.phone,
            "addr": registrant.address1, "city": registrant.city,
            "state": registrant.state, "zip": registrant.postal_code,
            "country": registrant.country,
            "price": price_cents, "reg_price": availability.price_cents,
            "renewal": renewal_cents, "intent_id": intent.id,
        },
    ).fetchone()
    db.commit()

    background_tasks.add_task(
        _complete_domain_registration,
        purchase_id=str(purchase_result.id),
        domain=domain,
        user_id=str(current_user.id),
        username=current_user.name,
        registrant={
            "firstName": registrant.first_name, "lastName": registrant.last_name,
            "email": registrant.email, "phone": registrant.phone,
            "address1": registrant.address1, "city": registrant.city,
            "state": registrant.state, "postalCode": registrant.postal_code,
            "country": registrant.country,
        },
    )

    return {
        "purchase_id": str(purchase_result.id),
        "domain": domain,
        "status": "paid",
        "price_charged_cents": price_cents,
        "message": "Payment successful! Registering your domain now — usually under 60 seconds.",
    }


async def _complete_domain_registration(
    purchase_id: str, domain: str, user_id: str, username: str, registrant: dict,
):
    db = SessionLocal()
    try:
        reg_result = await porkbun.register_domain(domain, registrant)

        if not reg_result.success:
            db.execute(
                text("UPDATE domain_purchases SET status = 'failed' WHERE id = :id"),
                {"id": purchase_id}
            )
            db.commit()
            return

        db.execute(
            text("""
                UPDATE domain_purchases
                SET status = 'registered', registered_at = NOW(),
                    expires_at = NOW() + INTERVAL '1 year',
                    registrar_domain_id = :rid
                WHERE id = :id
            """),
            {"id": purchase_id, "rid": reg_result.registrar_id},
        )

        await porkbun.setup_autopilot_dns(domain)

        cd_result = db.execute(
            text("""
                INSERT INTO custom_domains
                    (user_id, domain, apex_domain, status, source, verification_method, verified_at)
                VALUES (:uid, :domain, :apex, 'active', 'purchased', 'cname', NOW())
                RETURNING id
            """),
            {"uid": user_id, "domain": domain, "apex": domain},
        ).fetchone()

        db.execute(
            text("UPDATE domain_purchases SET custom_domain_id = :cd WHERE id = :id"),
            {"cd": cd_result.id, "id": purchase_id},
        )

        db.execute(
            text("""
                INSERT INTO domain_resolution_cache (domain, username, user_id)
                VALUES (:domain, :username, :uid)
                ON CONFLICT (domain) DO UPDATE SET username = :username, cached_at = NOW()
            """),
            {"domain": domain, "username": username, "uid": user_id},
        )
        db.commit()
        logger.info(f"Domain {domain} registered and active for {username}")

    except Exception as e:
        logger.exception(f"Fatal error registering {domain}: {e}")
    finally:
        db.close()


# ─────────────────────────────────────────────────────────
# 6. LIST DOMAINS
# ─────────────────────────────────────────────────────────

@router.get("/")
def list_domains(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = db.execute(
        text("""
            SELECT cd.id, cd.domain, cd.status, cd.source,
                   cd.verified_at, cd.created_at,
                   dp.expires_at, dp.renewal_price_cents, dp.auto_renew
            FROM custom_domains cd
            LEFT JOIN domain_purchases dp ON dp.custom_domain_id = cd.id
            WHERE cd.user_id = :uid
            ORDER BY cd.created_at DESC
        """),
        {"uid": current_user.id},
    ).fetchall()

    return {"domains": [dict(r._mapping) for r in result]}


# ─────────────────────────────────────────────────────────
# 7. DELETE DOMAIN
# ─────────────────────────────────────────────────────────

@router.delete("/{domain_id}")
def delete_domain(
    domain_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    row = db.execute(
        text("SELECT domain FROM custom_domains WHERE id = :id AND user_id = :uid"),
        {"id": domain_id, "uid": current_user.id},
    ).fetchone()

    if not row:
        raise HTTPException(status_code=404, detail="Domain not found")

    db.execute(text("DELETE FROM custom_domains WHERE id = :id"), {"id": domain_id})
    db.execute(text("DELETE FROM domain_resolution_cache WHERE domain = :d"), {"d": row.domain})
    db.commit()

    return {"deleted": True, "domain": row.domain}


# ─────────────────────────────────────────────────────────
# 8. LIST PURCHASES
# ─────────────────────────────────────────────────────────

@router.get("/purchases")
def list_purchases(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = db.execute(
        text("""
            SELECT id, domain, status, purchase_price_cents, renewal_price_cents,
                   registered_at, expires_at, auto_renew, created_at
            FROM domain_purchases
            WHERE user_id = :uid
            ORDER BY created_at DESC
        """),
        {"uid": current_user.id},
    ).fetchall()

    return {"purchases": [dict(r._mapping) for r in result]}