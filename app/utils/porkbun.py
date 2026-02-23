"""
Porkbun API Service
Save this file to: C:\Users\Raidi\autopilotai-backend\app\utils\porkbun.py
"""

import asyncio
import httpx
import logging
import os
from typing import Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)

PORKBUN_BASE = "https://api.porkbun.com/api/json/v3"


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
            response.raise_for_status()
            data = response.json()

            if data.get("status") != "SUCCESS":
                error_msg = data.get("message", "Unknown Porkbun error")
                logger.error(f"Porkbun API error on {endpoint}: {error_msg}")
                raise PorkbunError(error_msg)

            return data

    async def check_domain(self, domain: str) -> DomainAvailability:
        try:
            data = await self._post(
                "domain/checkAndGetSingleDomainPrice",
                {"domain": domain}
            )
            tld = domain.split(".", 1)[-1]
            price_float = float(data.get("price", "0"))
            renewal_float = float(data.get("renewalPrice", price_float))

            return DomainAvailability(
                domain=domain,
                available=True,
                price_cents=int(price_float * 100),
                renewal_cents=int(renewal_float * 100),
                tld=tld,
            )
        except PorkbunError as e:
            if "not available" in str(e).lower() or "unavailable" in str(e).lower():
                tld = domain.split(".", 1)[-1]
                return DomainAvailability(
                    domain=domain,
                    available=False,
                    price_cents=0,
                    renewal_cents=0,
                    tld=tld,
                )
            raise

    async def check_multiple_domains(self, base_name: str) -> list:
        tlds = ["com", "io", "co", "dev", "net", "org", "app", "ai"]
        domains = [f"{base_name}.{tld}" for tld in tlds]

        results = []
        checks = await asyncio.gather(
            *[self.check_domain(d) for d in domains],
            return_exceptions=True,
        )

        for result in checks:
            if isinstance(result, DomainAvailability):
                results.append(result)

        results.sort(key=lambda x: (not x.available, x.price_cents))
        return results

    async def register_domain(self, domain: str, registrant: dict, years: int = 1) -> RegistrationResult:
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
        try:
            await self._clear_dns_records(domain)

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

    async def _clear_dns_records(self, domain: str) -> None:
        try:
            data = await self._post(f"dns/retrieve/{domain}")
            records = data.get("records", [])

            deletions = []
            for record in records:
                if record["type"] in ("A", "CNAME", "ALIAS") and record["name"] in ("", domain, f"www.{domain}"):
                    deletions.append(self._post(f"dns/delete/{domain}/{record['id']}"))

            if deletions:
                await asyncio.gather(*deletions, return_exceptions=True)
        except PorkbunError:
            pass


class PorkbunError(Exception):
    pass


porkbun = PorkbunService()