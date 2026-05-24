import pytest
import respx
import httpx
from talon.transport.client import StealthClient
from talon.config import TalonConfig

@pytest.mark.asyncio
async def test_stealth_client_get():
    config = TalonConfig()
    async with StealthClient(config) as client:
        with respx.mock:
            respx.get("https://example.com/").mock(return_value=httpx.Response(200, text="ok"))
            response = await client.get("https://example.com/", use_curl=False)
            assert response.status_code == 200
            assert response.text == "ok"

@pytest.mark.asyncio
async def test_stealth_client_retry_on_429():
    config = TalonConfig()
    config.transport.max_retries = 2
    config.rate_limiting.backoff_factor = 0.1
    async with StealthClient(config) as client:
        with respx.mock:
            respx.get("https://example.com/").mock(side_effect=[
                httpx.Response(429),
                httpx.Response(200, text="success")
            ])
            response = await client.get("https://example.com/", use_curl=False)
            assert response.status_code == 200
            assert response.text == "success"
