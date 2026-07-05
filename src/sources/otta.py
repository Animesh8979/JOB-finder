"""Otta — curated tech jobs board.

Partner XML feed (https://www.otta.com/jobs.xml) — fully public, no API key needed.
"""
from __future__ import annotations

from typing import Any
from xml.etree import ElementTree as ET

from . import base
from .client import get_json

SOURCE_ID = "otta"
ENDPOINT = "https://www.otta.com/jobs.xml"


def fetch(query: str, limit: int, prefs: dict[str, Any]) -> list[dict[str, Any]]:
    import httpx
    h = {"User-Agent": "Mozilla/5.0 (OttaFeedReader/1.0)", "Accept": "application/xml,text/xml,*/*"}
    try:
        resp = httpx.get(ENDPOINT, headers=h, timeout=25.0, follow_redirects=True)
        if resp.status_code != 200:
            return []
    except Exception:
        return []
    try:
        root = ET.fromstring(resp.text)
    except Exception:
        return []
    out: list[dict[str, Any]] = []
    q = (query or "").lower()
    for item in root.findall(".//item"):
        title = (item.findtext("title") or "").strip()
        link = (item.findtext("link") or "").strip()
        desc = (item.findtext("description") or "").strip()
        if q and q not in (title + desc).lower():
            continue
        out.append(
            base.normalize(
                source=SOURCE_ID,
                source_job_id=link.rstrip("/").split("/")[-1] or link,
                title=title,
                company=_extract_company(title),
                location="Remote",
                url=link,
                apply_url=link,
                description=desc,
                posted_at=item.findtext("pubDate") or "",
            )
        )
        if len(out) >= limit:
            break
    return out


def _extract_company(title: str) -> str:
    """Otta titles are typically 'Role at Company'. Best-effort split."""
    if " at " in title:
        return title.split(" at ", 1)[1].strip()
    return ""
