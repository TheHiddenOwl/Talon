import time
import shodan
from typing import Any, Dict, List, Optional
from talon.collectors.base import CollectorResult

class ShodanCollector:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.api = shodan.Shodan(api_key) if api_key else None

    async def collect(self, domain: str) -> CollectorResult:
        if not self.api:
            return CollectorResult(data={}, status_code=401, error="Shodan API key not provided")

        start_time = time.monotonic()
        try:
            results = self.api.search(f'hostname:{domain}')
            duration_ms = int((time.monotonic() - start_time) * 1000)

            return CollectorResult(
                data=results,
                status_code=200,
                duration_ms=duration_ms
            )
        except Exception as e:
            return CollectorResult(
                data={},
                status_code=500,
                duration_ms=int((time.monotonic() - start_time) * 1000),
                error=str(e)
            )
