import asyncio
import time
from typing import Dict, List

import dns.asyncresolver
import dns.exception

from talon.config import DnsConfig
from talon.collectors.base import CollectorResult


class DnsCollector:
    def __init__(self, config: DnsConfig):
        self.config = config
        self.resolver = dns.asyncresolver.Resolver()
        self.resolver.nameservers = config.resolvers

    async def collect(self, domain: str) -> CollectorResult:
        start_time = time.monotonic()
        results = {}
        tasks = {
            rtype: self._query(domain, rtype)
            for rtype in self.config.record_types
        }
        responses = await asyncio.gather(*tasks.values(), return_exceptions=True)
        for rtype, response in zip(tasks.keys(), responses):
            if isinstance(response, Exception):
                results[rtype] = []
            else:
                results[rtype] = response

        duration_ms = int((time.monotonic() - start_time) * 1000)
        return CollectorResult(data=results, duration_ms=duration_ms)

    async def _query(self, domain: str, record_type: str) -> List[str]:
        try:
            answer = await self.resolver.resolve(domain, record_type)
            return [str(r) for r in answer]
        except (dns.exception.DNSException, Exception):
            return []
