import pytest
from unittest.mock import AsyncMock, patch
from talon.collectors.dns import DnsCollector
from talon.config import DnsConfig

@pytest.mark.asyncio
async def test_dns_collect_success():
    config = DnsConfig(record_types=["A", "MX"])
    collector = DnsCollector(config)

    # Mock the resolver's resolve method
    with patch.object(collector.resolver, 'resolve', new_callable=AsyncMock) as mock_resolve:
        def side_effect(domain, rtype):
            if rtype == "A":
                mock_answer = ["1.2.3.4"]
                return mock_answer
            if rtype == "MX":
                mock_answer = ["10 mail.example.com."]
                return mock_answer
            return []

        mock_resolve.side_effect = side_effect

        result = await collector.collect("example.com")

        assert result.data["A"] == ["1.2.3.4"]
        assert result.data["MX"] == ["10 mail.example.com."]
        assert result.duration_ms >= 0

@pytest.mark.asyncio
async def test_dns_collect_failure():
    config = DnsConfig(record_types=["A"])
    collector = DnsCollector(config)

    with patch.object(collector.resolver, 'resolve', new_callable=AsyncMock) as mock_resolve:
        mock_resolve.side_effect = Exception("DNS Error")

        result = await collector.collect("example.com")

        assert result.data["A"] == []
