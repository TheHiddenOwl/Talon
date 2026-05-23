import pytest
from talon.transport.proxy_pool import ProxyPool

def test_proxy_pool_round_robin():
    proxies = ["p1", "p2", "p3"]
    pool = ProxyPool(proxies, strategy="round_robin", rotate_every=2)

    assert pool.get() == "p1"
    assert pool.get() == "p1"
    assert pool.get() == "p2"
    assert pool.get() == "p2"
    assert pool.get() == "p3"

def test_proxy_pool_mark_bad():
    proxies = ["p1", "p2"]
    pool = ProxyPool(proxies, strategy="round_robin", rotate_every=1)

    assert pool.get() == "p1"
    pool.mark_bad("p1")
    assert pool.get() == "p2"
    assert "p1" not in pool.proxies
