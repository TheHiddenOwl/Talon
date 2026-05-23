import asyncio
import logging
from typing import Any, Dict, Optional
from urllib.parse import urlparse

import httpx
from curl_cffi.requests import AsyncSession

from talon.config import TalonConfig
from talon.core.rate_limiter import AdaptiveRateLimiter
from talon.transport.headers import get_browser_headers
from talon.transport.proxy_pool import ProxyPool

logger = logging.getLogger(__name__)

class StealthClient:
    """
    Async HTTP client with TLS fingerprint spoofing, header rotation,
    proxy support, and adaptive rate limiting.

    Now implements an async context manager for connection pooling.
    """

    def __init__(self, config: TalonConfig):
        self.config = config
        self.rate_limiter = AdaptiveRateLimiter(config.rate_limiting)
        self.proxy_pool = ProxyPool(
            proxies=self.config.proxy.pool if self.config.proxy.enabled else [],
            strategy=self.config.proxy.rotation_strategy,
            rotate_every=self.config.proxy.rotate_every_n_requests,
        )
        self._httpx_client: Optional[httpx.AsyncClient] = None
        self._curl_session: Optional[AsyncSession] = None

    async def __aenter__(self):
        self._httpx_client = httpx.AsyncClient(
            http2=self.config.transport.http2,
            verify=self.config.transport.verify_ssl,
            timeout=self.config.transport.timeout,
            limits=httpx.Limits(
                max_keepalive_connections=10,
                max_connections=20,
            ),
        )
        self._curl_session = AsyncSession(impersonate="chrome124")
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._httpx_client:
            await self._httpx_client.aclose()
        if self._curl_session:
            await self._curl_session.close()

    async def get(
        self,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        params: Optional[Dict[str, Any]] = None,
        use_curl: bool = True,
    ) -> httpx.Response | Any:
        domain = urlparse(url).netloc
        if not domain:
            domain = "default"

        logger.info(f"Requesting {url} — ensure you have authorization to scan {domain}")

        await self.rate_limiter.acquire(domain)

        merged_headers = get_browser_headers()
        if headers:
            merged_headers.update(headers)

        for attempt in range(self.config.transport.max_retries):
            proxy = self.proxy_pool.get()

            try:
                if use_curl:
                    response = await self._curl_get(url, merged_headers, params, proxy)
                else:
                    response = await self._httpx_get(url, merged_headers, params, proxy)

                if response.status_code in (429, 503):
                    await self.rate_limiter.backoff(domain)
                    wait_time = self.config.rate_limiting.backoff_factor ** attempt
                    await asyncio.sleep(wait_time)
                    continue

                await self.rate_limiter.reset_backoff(domain)
                return response

            except Exception as e:
                logger.error(f"Error during request to {url}: {e}")
                if proxy:
                    self.proxy_pool.mark_bad(proxy)
                if attempt == self.config.transport.max_retries - 1:
                    raise

        raise RuntimeError(f"All retries exhausted for {url}")

    async def _curl_get(self, url: str, headers: Dict[str, str], params: Optional[Dict[str, Any]], proxy: Optional[str]):
        if not self._curl_session:
            raise RuntimeError("StealthClient must be used as an async context manager")

        return await self._curl_session.get(
            url,
            headers=headers,
            params=params,
            proxy=proxy,
            timeout=self.config.transport.timeout,
        )

    async def _httpx_get(self, url: str, headers: Dict[str, str], params: Optional[Dict[str, Any]], proxy: Optional[str]):
        if not self._httpx_client:
            raise RuntimeError("StealthClient must be used as an async context manager")

        # httpx.AsyncClient handles proxies at init time, but for the ProxyPool to work
        # per-request, we might need to handle it differently if we want to rotate
        # while using the same client. However, httpx.AsyncClient doesn't support
        # 'proxy' on individual requests easily.

        # If rotation is required for httpx as well, we might need to recreate the client
        # OR use a more advanced proxy handler. For now, we'll use the one from init
        # or recreate if it changed.

        # Given the "Stealth" requirement, rotation is key.
        # But connection pooling is also key.

        # For now, let's keep it simple: use the pooled client without per-request proxy
        # override for httpx, as rotation is primarily handled via curl_session which
        # does support it.

        return await self._httpx_client.get(
            url,
            headers=headers,
            params=params,
        )
