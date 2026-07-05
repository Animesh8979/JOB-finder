"""CareerBuilder — public search page (no longer requires login for public listings)."""
from __future__ import annotations

from typing import Any
from urllib.parse import quote_plus

import httpx
from bs4 import BeautifulSoup

from . import base

SOURCE_ID = "careerbuilder"
ENDPOINT_TPL = "https://www.careerbuilder.com/jobs?keywords={q}&location=Remote"


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
    cards = soup.select("li.job-listing, .job-results li, article[data-job]")
    out: list[dict[str, Any]] = []
    for el in cards:
        a = el.select_one("a[href*='/job/']")
        if not a:
            continue
        href = a.get("href", "")
        title = a.get_text(strip=True)
        full = href if href.startswith("http") else f"https://www.careerbuilder.com{href}"
        out.append(
            base.normalize(
                source=SOURCE_ID,
                source_job_id=href,
                title=title,
                location="Remote",
                url=full,
                apply_url=full,
                description="",
            )
        )
        if len(out) >= limit:
            break
    return out
