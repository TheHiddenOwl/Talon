import time
from typing import Any, Dict, List

from talon.transport.client import StealthClient
from talon.collectors.base import CollectorResult


class CertCollector:
    CRT_SH_URL = "https://crt.sh/"

    def __init__(self, client: StealthClient):
        self.client = client

    async def collect(self, domain: str) -> CollectorResult:
        start_time = time.monotonic()
        try:
            response = await self.client.get(
                self.CRT_SH_URL,
                params={"q": f"%.{domain}", "output": "json"},
            )
            duration_ms = int((time.monotonic() - start_time) * 1000)

            if response.status_code != 200:
                return CollectorResult(
                    data=[],
                    status_code=response.status_code,
                    duration_ms=duration_ms,
                    raw_response=response.text
                )

            from talon.parsers.json import JsonParser
            records = JsonParser.parse(response.text)
            if records is None:
                return CollectorResult(
                    data=[],
                    status_code=200,
                    duration_ms=duration_ms,
                    raw_response=response.text
                )

            seen = set()
            unique = []
            for record in records:
                name = record.get("name_value", "")
                if name not in seen:
                    seen.add(name)
                    unique.append({
                        "name": name,
                        "issuer": record.get("issuer_name"),
                        "not_before": record.get("not_before"),
                        "not_after": record.get("not_after"),
                    })

            return CollectorResult(
                data=unique,
                status_code=200,
                duration_ms=duration_ms,
                raw_response=response.text
            )
        except Exception as e:
            return CollectorResult(
                data=[],
                status_code=500,
                duration_ms=int((time.monotonic() - start_time) * 1000),
                error=str(e)
            )
