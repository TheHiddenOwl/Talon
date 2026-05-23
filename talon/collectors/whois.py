import asyncio
import time
from typing import Any, Dict

import whois
from talon.collectors.base import CollectorResult


class WhoisCollector:
    async def collect(self, domain: str) -> CollectorResult:
        loop = asyncio.get_event_loop()
        start_time = time.monotonic()
        try:
            # whois.whois is blocking, run in executor
            result = await loop.run_in_executor(None, whois.whois, domain)
            duration_ms = int((time.monotonic() - start_time) * 1000)

            data = {
                "registrar": result.registrar,
                "creation_date": self._format_date(result.creation_date),
                "expiration_date": self._format_date(result.expiration_date),
                "name_servers": result.name_servers,
                "status": result.status,
                "emails": result.emails,
                "org": result.org,
                "country": result.country,
            }
            return CollectorResult(data=data, duration_ms=duration_ms)
        except Exception as e:
            return CollectorResult(
                data={"error": str(e)},
                duration_ms=int((time.monotonic() - start_time) * 1000),
                status_code=500,
                error=str(e)
            )

    def _format_date(self, dt: Any) -> str:
        if isinstance(dt, list):
            return [str(d) for d in dt]
        return str(dt)
