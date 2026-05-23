# Talon: Stealthy Async OSINT Framework

Talon is a high-performance, stealth-first OSINT framework designed for comprehensive reconnaissance with a focus on evading detection and rate limiting.

## Core Features
- **Stealth-first architecture:** TLS fingerprint spoofing, realistic header rotation, and adaptive rate limiting.
- **Async Transport Layer:** Built on `asyncio` and `curl_cffi` for high concurrency and browser-like requests.
- **Modular Collectors:** DNS, WHOIS, Certificate Transparency, Web Archive, Shodan, GitHub, and more.
- **Adaptive Rate Limiting:** Per-domain token bucket rate limiting with exponential backoff.
- **Robust Storage:** SQLite storage with full provenance tracking for findings.

## Usage
Talon requires authorization to scan targets. Use the `--confirm-scope` flag to acknowledge you have permission.

```bash
talon scan example.com --confirm-scope
```
