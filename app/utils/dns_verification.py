#dns

import asyncio
import logging
import os
from typing import Optional

import dns.resolver
import dns.exception

logger = logging.getLogger(__name__)

CNAME_TARGET = "proxy.autopilotai.dev"
A_RECORD_IP = os.getenv("SERVER_IP", "")

PUBLIC_RESOLVERS = ["8.8.8.8", "1.1.1.1", "9.9.9.9"]


class DNSVerificationResult:
    def __init__(self, verified: bool, method: Optional[str] = None,
                 resolved_value: Optional[str] = None, error: Optional[str] = None):
        self.verified = verified
        self.method = method
        self.resolved_value = resolved_value
        self.error = error


class DNSVerificationService:

    def _make_resolver(self) -> dns.resolver.Resolver:
        resolver = dns.resolver.Resolver()
        resolver.nameservers = PUBLIC_RESOLVERS
        resolver.timeout = 5
        resolver.lifetime = 10
        return resolver

    async def verify(self, domain: str) -> DNSVerificationResult:
        apex = domain.lower().removeprefix("www.")
        variants = [apex, f"www.{apex}"]

        loop = asyncio.get_event_loop()

        for variant in variants:
            result = await loop.run_in_executor(None, self._check_domain_sync, variant)
            if result.verified:
                return result

        return DNSVerificationResult(
            verified=False,
            error=(
                f"DNS not configured correctly. "
                f"Expected CNAME pointing to {CNAME_TARGET}. "
                f"DNS changes can take up to 48 hours to propagate."
            ),
        )

    def _check_domain_sync(self, domain: str) -> DNSVerificationResult:
        resolver = self._make_resolver()

        cname_result = self._check_cname(resolver, domain)
        if cname_result.verified:
            return cname_result

        a_result = self._check_a_record(resolver, domain)
        if a_result.verified:
            return a_result

        return cname_result

    def _check_cname(self, resolver, domain: str) -> DNSVerificationResult:
        try:
            answers = resolver.resolve(domain, "CNAME")
            for rdata in answers:
                cname_value = str(rdata.target).rstrip(".")
                if cname_value.lower() == CNAME_TARGET.lower():
                    return DNSVerificationResult(verified=True, method="cname", resolved_value=cname_value)
                else:
                    return DNSVerificationResult(
                        verified=False, resolved_value=cname_value,
                        error=f"CNAME points to {cname_value!r}, expected {CNAME_TARGET!r}"
                    )
        except dns.resolver.NXDOMAIN:
            return DNSVerificationResult(verified=False, error=f"Domain {domain} does not exist")
        except dns.resolver.NoAnswer:
            return DNSVerificationResult(verified=False, error=f"No CNAME record found for {domain}")
        except dns.exception.DNSException as e:
            return DNSVerificationResult(verified=False, error=f"DNS lookup failed: {e}")

    def _check_a_record(self, resolver, domain: str) -> DNSVerificationResult:
        try:
            answers = resolver.resolve(domain, "A")
            ips = [str(r) for r in answers]
            if A_RECORD_IP and A_RECORD_IP in ips:
                return DNSVerificationResult(verified=True, method="a_record", resolved_value=", ".join(ips))
            return DNSVerificationResult(verified=False, resolved_value=", ".join(ips),
                                         error=f"A record(s) {ips} don't match our server IP")
        except Exception:
            return DNSVerificationResult(verified=False, error="No A record found")

    def get_instructions(self, domain: str) -> dict:
        apex = domain.lower().removeprefix("www.")
        return {
            "domain": apex,
            "recommended": {
                "type": "CNAME",
                "name": "@",
                "value": CNAME_TARGET,
                "ttl": "Auto or 300",
                "note": "Use @ or leave the name field blank for root domain.",
            },
            "alternative": {
                "type": "A",
                "name": "@",
                "value": A_RECORD_IP or "Check Render dashboard for your server IP",
                "ttl": "Auto or 300",
                "note": "Use this if your DNS provider doesn't support CNAME on root domain.",
            },
            "www_record": {
                "type": "CNAME",
                "name": "www",
                "value": CNAME_TARGET,
                "ttl": "Auto or 300",
                "note": f"Also add this to support www.{apex}",
            },
            "propagation_note": (
                "DNS changes typically propagate within 15 minutes, "
                "but can take up to 48 hours in rare cases."
            ),
        }


dns_service = DNSVerificationService()