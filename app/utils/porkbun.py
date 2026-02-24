# Porkbun API Service
# Save to: C:\Users\Raidi\autopilotai-backend\app\utils\porkbun.py

import asyncio
import httpx
import logging
import os
from dataclasses import dataclass
from typing import Optional

logger = logging.getLogger(__name__)

PORKBUN_BASE = "https://api.porkbun.com/api/json/v3"

# All TLDs to search when user types a name
# Popular ones first, then international, then niche
ALL_TLDS = [
    # Most popular
    "com", "net", "org", "co", "io",
    # Tech / startup
    "dev", "app", "ai", "tech", "digital", "cloud", "software", "studio",
    # Business
    "shop", "store", "online", "business", "agency", "services", "solutions",
    # Creative
    "design", "media", "art", "photography",
    # Nordic / European
    "se", "no", "dk", "fi", "de", "fr", "nl", "es", "it", "pl",
    # English-speaking
    "uk", "ca", "au", "nz",
    # Other popular
    "me", "tv", "info", "xyz", "site", "web", "page",
]


@dataclass
class DomainAvailability:
    domain: str
    available: bool
    price_cents: int
    renewal_cents: int
    tld: str


@dataclass
class RegistrationResult:
    success: bool
    domain: str
    registrar_id: Optional[str] = None
    error: Optional[str] = None


class PorkbunError(Exception):
    pass


class PorkbunService:
    def __init__(self):
        self.api_key = os.getenv("PORKBUN_API_KEY", "")
        self.secret_key = os.getenv("PORKBUN_SECRET_KEY", "")

    @property
    def _auth(self):
        return {
            "apikey": self.api_key,
            "secretapikey": self.secret_key,
        }

    async def _post(self, endpoint: str, payload: dict = {}) -> dict:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{PORKBUN_BASE}/{endpoint}",
                json={**self._auth, **payload},
            )
            data = response.json()
            if data.get("status") != "SUCCESS":
                error_msg = data.get("message", "Unknown Porkbun error")
                logger.error(f"Porkbun error on {endpoint}: {error_msg} (HTTP {response.status_code})")
                raise PorkbunError(error_msg)
            return data

    async def check_domain(self, domain: str) -> DomainAvailability:
        """Check if a single domain is available and get its price."""
        tld = domain.split(".", 1)[-1]
        try:
            data = await self._post(f"domain/checkDomain/{domain}")
            response = data.get("response", {})

            available = response.get("avail", "no").lower() == "yes"

            price_str = response.get("price", response.get("regularPrice", "0"))
            renewal_str = (
                response.get("additional", {})
                .get("renewal", {})
                .get("price", price_str)
            )

            price_cents = int(float(price_str) * 100)
            renewal_cents = int(float(renewal_str) * 100)

            return DomainAvailability(
                domain=domain,
                available=available,
                price_cents=price_cents,
                renewal_cents=renewal_cents,
                tld=tld,
            )

        except PorkbunError:
            raise
        except Exception as e:
            logger.error(f"check_domain error for {domain}: {e}")
            raise PorkbunError(str(e))

    async def check_multiple_domains(self, base_name: str) -> list:
        """
        Search a base name across all TLDs in parallel.
        Returns available domains first, sorted by price.
        Unavailable domains shown after so users can see what's taken.
        """
        domains = [f"{base_name}.{tld}" for tld in ALL_TLDS]

        # Run all checks in parallel — much faster than sequential
        results = await asyncio.gather(
            *[self._safe_check(d) for d in domains],
            return_exceptions=False,  # _safe_check handles its own errors
        )

        # Filter out None (failed checks) 
        output = [r for r in results if r is not None]

        # Sort: available first, then by price ascending
        output.sort(key=lambda x: (not x.available, x.price_cents))

        return output

    async def _safe_check(self, domain: str) -> Optional[DomainAvailability]:
        """Check a domain safely — returns None instead of raising on error."""
        try:
            return await self.check_domain(domain)
        except Exception as e:
            logger.debug(f"Skipping {domain}: {e}")
            return None

    async def register_domain(self, domain: str, registrant: dict, years: int = 1) -> RegistrationResult:
        """Register a domain with Porkbun."""
        try:
            data = await self._post(f"domain/create/{domain}", {
                "years": str(years),
                "whoisPrivacy": "1",
                "autorenew": "1",
                **registrant,
            })
            return RegistrationResult(
                success=True,
                domain=domain,
                registrar_id=data.get("domain", domain),
            )
        except PorkbunError as e:
            return RegistrationResult(success=False, domain=domain, error=str(e))

    async def setup_autopilot_dns(self, domain: str) -> bool:
        """Configure DNS records to point to AutopilotAI proxy."""
        try:
            await self._clear_conflicting_records(domain)

            await self._post(f"dns/create/{domain}", {
                "name": "",
                "type": "CNAME",
                "content": "proxy.autopilotai.dev",
                "ttl": "300",
            })

            await self._post(f"dns/create/{domain}", {
                "name": "www",
                "type": "CNAME",
                "content": "proxy.autopilotai.dev",
                "ttl": "300",
            })

            return True
        except PorkbunError as e:
            logger.error(f"DNS setup failed for {domain}: {e}")
            return False

    async def _clear_conflicting_records(self, domain: str) -> None:
        """Remove existing A/CNAME records that would conflict."""
        try:
            data = await self._post(f"dns/retrieve/{domain}")
            records = data.get("records", [])
            deletions = []
            for record in records:
                if record["type"] in ("A", "CNAME", "ALIAS") and record.get("name", "") in ("", domain, f"www.{domain}"):
                    deletions.append(self._post(f"dns/delete/{domain}/{record['id']}"))
            if deletions:
                await asyncio.gather(*deletions, return_exceptions=True)
        except PorkbunError:
            pass

    async def renew_domain(self, domain: str, years: int = 1) -> bool:
        """Renew a domain registration."""
        try:
            await self._post(f"domain/renew/{domain}", {"years": str(years)})
            return True
        except PorkbunError as e:
            logger.error(f"Renewal failed for {domain}: {e}")
            return False


porkbun = PorkbunService()