from __future__ import annotations

import re
from typing import Any, Dict, List
from urllib.parse import unquote, urlparse

import httpx


ALIEXPRESS_PATTERNS = [
    re.compile(r"https?://(?:www\.)?aliexpress\.com/[^\s\"'<>]+", re.IGNORECASE),
    re.compile(r"https?://(?:[a-z]+\.)?aliexpress\.us/[^\s\"'<>]+", re.IGNORECASE),
]

ENCODED_ALIEXPRESS_PATTERN = re.compile(
    r"https?%3A%2F%2F(?:www%2E)?aliexpress(?:%2Ecom|%2Eus)%2F[^\"'<> ]+",
    re.IGNORECASE,
)


async def resolve_source_url(source_url: str, source_hint: str) -> Dict[str, Any]:
    parsed = urlparse(source_url)
    host = (parsed.netloc or "").lower()
    warnings: List[str] = []

    if "aliexpress." in host:
        return {
            "resolved_url": source_url,
            "source_hint": "aliexpress",
            "resolver_mode": "direct",
            "warnings": warnings,
        }

    if source_hint == "aliexpress":
        return {
            "resolved_url": source_url,
            "source_hint": "aliexpress",
            "resolver_mode": "forced_direct",
            "warnings": warnings,
        }

    if "accio.com" not in host and source_hint != "accio":
        return {
            "resolved_url": source_url,
            "source_hint": source_hint or "unknown",
            "resolver_mode": "passthrough",
            "warnings": warnings,
        }

    html = await _fetch_html(source_url)
    resolved = _extract_aliexpress_url(html)
    if resolved:
        warnings.append("Resolved a supplier URL from the Accio page using best-effort HTML extraction.")
        return {
            "resolved_url": resolved,
            "source_hint": "aliexpress",
            "resolver_mode": "accio_best_effort",
            "warnings": warnings,
        }

    raise ValueError("Could not resolve a supplier URL from the Accio page. Please provide a direct supplier link.")


async def _fetch_html(source_url: str) -> str:
    async with httpx.AsyncClient(timeout=20, follow_redirects=True) as client:
        response = await client.get(source_url, headers={"User-Agent": "Mozilla/5.0"})
        response.raise_for_status()
        return response.text


def _extract_aliexpress_url(html: str) -> str:
    for pattern in ALIEXPRESS_PATTERNS:
        match = pattern.search(html)
        if match:
            return match.group(0)

    encoded = ENCODED_ALIEXPRESS_PATTERN.search(html)
    if encoded:
        return unquote(encoded.group(0))

    return ""
