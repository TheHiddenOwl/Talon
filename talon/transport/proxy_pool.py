import itertools
import random
from typing import List, Optional


class ProxyPool:
    """Manages proxy rotation with round-robin or random strategies."""

    def __init__(self, proxies: List[str], strategy: str = "round_robin", rotate_every: int = 5):
        self.proxies = proxies.copy()
        self.strategy = strategy
        self.rotate_every = rotate_every
        self._request_count = 0
        self._cycle = itertools.cycle(self.proxies) if self.proxies else None
        self._current_proxy: Optional[str] = next(self._cycle) if self._cycle else None

    def get(self) -> Optional[str]:
        if not self.proxies:
            return None

        proxy = self._current_proxy
        self._request_count += 1
        if self._request_count % self.rotate_every == 0:
            self._rotate()

        return proxy

    def _rotate(self) -> None:
        if not self.proxies:
            self._current_proxy = None
            return

        if self.strategy == "random":
            self._current_proxy = random.choice(self.proxies)
        else:
            self._current_proxy = next(self._cycle)

    def mark_bad(self, proxy: str) -> None:
        """Remove a non-functional proxy from the pool."""
        if proxy in self.proxies:
            self.proxies.remove(proxy)
            if self.proxies:
                self._cycle = itertools.cycle(self.proxies)
                if self._current_proxy == proxy:
                    self._current_proxy = next(self._cycle)
            else:
                self._cycle = None
                self._current_proxy = None
