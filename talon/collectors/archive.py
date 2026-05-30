import time
from typing import Any, Dict, List

from talon.transport.client import StealthClient
from talon.collectors.base import CollectorResult


class ArchiveCollector:
    CDX_API = "https://web.archive.org/cdx/search/cdx"

    def __init__(self, client: StealthClient, limit: int = 100):
        self.client = client
        self.limit = limit

    async def collect(self, domain: str) -> CollectorResult:
        start_time = time.monotonic()
        try:
            response = await self.client.get(
                self.CDX_API,
                params={
                    "url": f"*.{domain}",
                    "output": "json",
                    "fl": "timestamp,original,statuscode,mimetype",
                    "collapse": "urlkey",
                    "limit": self.limit,
                },
            )
            duration_ms = int((time.monotonic() - start_time) * 1000)

            if response.status_code != 200 or not response.text.strip():
                return CollectorResult(
                    data=[],
                    status_code=response.status_code,
                    duration_ms=duration_ms,
                    raw_response=response.text
                )

            from talon.parsers.json import JsonParser
            rows = JsonParser.parse(response.text)
            if rows is None or not rows:
                return CollectorResult(
                    data=[],
                    status_code=200,
                    duration_ms=duration_ms,
                    raw_response=response.text
                )

            keys = rows[0]
            data = [dict(zip(keys, row)) for row in rows[1:]]

            return CollectorResult(
                data=data,
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
