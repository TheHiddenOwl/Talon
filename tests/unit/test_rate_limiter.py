import asyncio
import pytest
import time
from talon.core.rate_limiter import AdaptiveRateLimiter
from talon.config import RateLimitConfig

@pytest.mark.asyncio
async def test_rate_limiter_basic():
    config = RateLimitConfig(base_delay=0.1, jitter=0, token_bucket_capacity=1)
    limiter = AdaptiveRateLimiter(config)

    start = time.monotonic()
    await limiter.acquire("example.com") # 1st: immediate (consumes token)
    await limiter.acquire("example.com") # 2nd: waits base_delay
    end = time.monotonic()

    assert end - start >= 0.1

@pytest.mark.asyncio
async def test_rate_limiter_backoff():
    config = RateLimitConfig(base_delay=0.1, jitter=0, backoff_factor=2.0)
    limiter = AdaptiveRateLimiter(config)

    await limiter.backoff("example.com") # 0.1 * 2 = 0.2

    start = time.monotonic()
    await limiter.acquire("example.com")
    end = time.monotonic()

    assert end - start >= 0.2
