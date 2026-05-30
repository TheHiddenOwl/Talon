import pytest
from talon.transport.client import StealthClient
from talon.config import TalonConfig

@pytest.mark.live
@pytest.mark.asyncio
async def test_live_network_call():
    config = TalonConfig()
    async with StealthClient(config) as client:
        response = await client.get("https://web.archive.org/cdx/search/cdx?url=example.com&limit=1")
        assert response.status_code == 200
