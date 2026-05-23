import pytest
from talon.transport.headers import get_browser_headers, USER_AGENTS

def test_get_browser_headers_random():
    headers = get_browser_headers()
    assert "User-Agent" in headers
    assert headers["User-Agent"] in USER_AGENTS
    assert "Accept" in headers

def test_get_browser_headers_specific():
    ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0"
    headers = get_browser_headers(ua)
    assert headers["User-Agent"] == ua
    assert "Connection" in headers # Firefox specific
