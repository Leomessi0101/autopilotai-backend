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


@dataclass
class DomainAvailability:
    domain: str
    available: bool
    price_cents: int      # registrar's wholesale price
    renewal_cents: int    # registrar's wholesale renewal
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
                logger.error(f"Porkbun API error on {endpoint}: {error_msg} (HTTP {response.status_code})")
                raise PorkbunError(error_msg)
            return data

    async def check_domain(self, domain: str) -> DomainAvailability:
        """Check if a single domain is available and get its price."""
        tld = domain.split(".", 1)[-1]
        try:
            # Correct endpoint: pricing/get/{tld} for price, then check availability
            # First get pricing for the TLD
            pricing_data = await self._post(f"pricing/get/{tld}")
            pricing = pricing_data.get("pricing", {})

            # registration price (string like "9.73")
            reg_price_str = pricing.get("registration", "0")
            renewal_price_str = pricing.get("renewal", reg_price_str)

            price_cents = int(float(reg_price_str) * 100)
            renewal_cents = int(float(renewal_price_str) * 100)

            # Now check if this specific domain is available
            avail_data = await self._post("domain/checkAndGetSingleDomainPrice", {"domain": domain})
            # If we get here without exception, domain is available
            # Some porkbun responses include price in the availability check
            if "price" in avail_data:
                price_cents = int(float(avail_data["price"]) * 100)

            return DomainAvailability(
                domain=domain,
                available=True,
                price_cents=price_cents,
                renewal_cents=renewal_cents,
                tld=tld,
            )

        except PorkbunError as e:
            err = str(e).lower()
            # If error mentions "invalid domain" or "not available" = taken
            if any(x in err for x in ["invalid domain", "not available", "already", "taken", "registered"]):
                return DomainAvailability(
                    domain=domain,
                    available=False,
                    price_cents=0,
                    renewal_cents=0,
                    tld=tld,
                )
            # Otherwise re-raise
            raise

    async def get_tld_pricing(self, tld: str) -> tuple[int, int]:
        """Get wholesale registration and renewal price for a TLD in cents."""
        try:
            data = await self._post(f"pricing/get/{tld}")
            pricing = data.get("pricing", {})
            reg = int(float(pricing.get("registration", "0")) * 100)
            renewal = int(float(pricing.get("renewal", "0")) * 100)
            return reg, renewal
        except Exception:
            return 0, 0

    async def check_multiple_domains(self, base_name: str) -> list:
        """Search a base name across multiple TLDs."""
        tlds = ["com", "io", "co", "dev", "net", "org", "app", "ai"]
        domains = [f"{base_name}.{tld}" for tld in tlds]

        results = await asyncio.gather(
            *[self.check_domain(d) for d in domains],
            return_exceptions=True,
        )

        output = []
        for r in results:
            if isinstance(r, DomainAvailability):
                output.append(r)
            else:
                logger.warning(f"Domain check failed: {r}")

        # Sort: available first, then by price
        output.sort(key=lambda x: (not x.available, x.price_cents))
        return output

    async def register_domain(self, domain: str, registrant: dict, years: int = 1) -> RegistrationResult:
        """Register a domain with Porkbun."""
        try:
            data = await self._post("domain/create", {
                "domain": domain,
                "years": str(years),
                "whoisPrivacy": "1",
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

            # Root CNAME
            await self._post(f"dns/create/{domain}", {
                "name": "",
                "type": "CNAME",
                "content": "proxy.autopilotai.dev",
                "ttl": "300",
            })

            # www CNAME
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
        """Remove any existing A/CNAME records that would conflict."""
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
            pass  # If retrieval fails, just continue

    async def renew_domain(self, domain: str, years: int = 1) -> bool:
        """Renew a domain registration."""
        try:
            await self._post(f"domain/renew/{domain}", {"years": str(years)})
            return True
        except PorkbunError as e:
            logger.error(f"Renewal failed for {domain}: {e}")
            return False


porkbun = PorkbunService()