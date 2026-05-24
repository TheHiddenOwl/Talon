import asyncio
import concurrent.futures
import time
from typing import Any, Dict, List
from github import Github
from talon.collectors.base import CollectorResult

class GithubCollector:
    def __init__(self, api_key: str, dorks: List[str]):
        self.api_key = api_key
        self.dorks = dorks
        self.api = Github(api_key) if api_key else None
        self._executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)

    def __del__(self):
        self._executor.shutdown(wait=False)

    async def collect(self, domain: str) -> CollectorResult:
        if not self.api:
            return CollectorResult(data=[], status_code=401, error="Github API key not provided")

        start_time = time.monotonic()
        findings = []
        try:
            loop = asyncio.get_event_loop()
            for dork in self.dorks:
                query = f"{dork} {domain}"
                result = await loop.run_in_executor(
                    self._executor,
                    lambda: list(self.api.search_code(query)[:10])
                )
                for item in result:
                    findings.append({
                        "dork": dork,
                        "url": item.html_url,
                        "path": item.path,
                        "repository": item.repository.full_name
                    })

            duration_ms = int((time.monotonic() - start_time) * 1000)
            return CollectorResult(
                data=findings,
                status_code=200,
                duration_ms=duration_ms
            )
        except Exception as e:
            return CollectorResult(
                data=[],
                status_code=500,
                duration_ms=int((time.monotonic() - start_time) * 1000),
                error=str(e)
            )
