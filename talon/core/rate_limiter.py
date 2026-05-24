import asyncio
import random
import time
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Dict

from talon.config import RateLimitConfig


@dataclass
class TokenBucket:
    capacity: float
    tokens: float = field(init=False)
    last_refill: float = field(init=False)
    rate: float = 1.0  # tokens per second

    def __post_init__(self):
        self.tokens = self.capacity
        self.last_refill = time.monotonic()

    def consume(self) -> float:
        """Returns wait time in seconds before a token is available."""
        now = time.monotonic()
        elapsed = now - self.last_refill
        self.tokens = min(self.capacity, self.tokens + elapsed * self.rate)
        self.last_refill = now

        if self.tokens >= 1:
            self.tokens -= 1
            return 0.0
        else:
            # Calculate how long to wait for 1 token
            wait_time = (1 - self.tokens) / self.rate
            return wait_time


class AdaptiveRateLimiter:
    """Per-domain adaptive rate limiter with token buckets and exponential backoff."""

    def __init__(self, config: RateLimitConfig):
        self.config = config
        self._buckets: Dict[str, TokenBucket] = defaultdict(
            lambda: TokenBucket(capacity=config.token_bucket_capacity)
        )
        self._backoff: Dict[str, float] = defaultdict(lambda: config.base_delay)
        self._lock = asyncio.Lock()

    async def acquire(self, domain: str) -> None:
        """
        NOTE: base_delay is applied to ALL requests including the first per domain.
        This is intentional — it simulates organic human latency before the initial
        request. Removing it would create a detectable "instant first request" pattern.
        Adjust base_delay in config to tune aggressiveness vs stealth.
        """
        async with self._lock:
            bucket = self._buckets[domain]
            wait = bucket.consume()

            base = self._backoff[domain]
            jitter = random.uniform(-self.config.jitter, self.config.jitter)
            total_wait = max(0.0, wait + base + jitter)

        if total_wait > 0:
            await asyncio.sleep(total_wait)

    async def backoff(self, domain: str) -> None:
        """Exponentially increase delay for a domain on rate-limit response."""
        async with self._lock:
            current = self._backoff[domain]
            self._backoff[domain] = min(
                current * self.config.backoff_factor,
                self.config.max_delay
            )

    async def reset_backoff(self, domain: str) -> None:
        async with self._lock:
            self._backoff[domain] = self.config.base_delay
