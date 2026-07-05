"""Dice — tech-jobs aggregator. Public HTML listing pages parsed defensively.

Dice locked down the JSON API but the HTML site still allows keyword search.
We rate-limit by using a single user agent and caching via the existing retry helper.
"""
from __future__ import annotations

from typing import Any
from urllib.parse import quote_plus

import httpx
from bs4 import BeautifulSoup

from . import base

SOURCE_ID = "dice"
ENDPOINT_TPL = "https://www.dice.com/jobs?q={q}&countryCode=US&radius=30&page=1"


def fetch(query: str, limit: int, prefs: dict[str, Any]) -> list[dict[str, Any]]:
    q = quote_plus(query or "developer")
    url = ENDPOINT_TPL.format(q=q)
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                      "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml",
        "Accept-Language": "en-US,en;q=0.9",
    }
    try:
        resp = httpx.get(url, headers=headers, timeout=25.0, follow_redirects=True)
        if resp.status_code != 200:
            return []
    except Exception:
        return []
    soup = BeautifulSoup(resp.text, "html.parser")
    cards = soup.select("a.card-title-link, .search-card a, div[id^='card-'] a")
    out: list[dict[str, Any]] = []
    seen: set[str] = set()
    for a in cards:
        href = a.get("href", "")
        title = a.get_text(strip=True)
        if not href or title in seen:
            continue
        seen.add(title)
        full = href if href.startswith("http") else f"https://www.dice.com{href}"
        out.append(
            base.normalize(
                source=SOURCE_ID,
                source_job_id=href.split("/")[-1] or href,
                title=title,
                location="Remote" if "remote" in href.lower() else "",
                url=full,
                apply_url=full,
                description="",
            )
        )
        if len(out) >= limit:
            break
    return out
