"""Wellfound (formerly AngelList) — startup jobs.

Public RSS feed per tag. https://wellfound.com — note: requires scraping in many
cases; we use the public RSS variants here where available.
"""
from __future__ import annotations

from typing import Any
from urllib.parse import quote_plus

from . import base
from .client import get_json

SOURCE_ID = "wellfound"


def fetch(query: str, limit: int, prefs: dict[str, Any]) -> list[dict[str, Any]]:
    """Best-effort Wellfront startup jobs. Falls back to empty list if API gated."""
    out: list[dict[str, Any]] = []
    tag = quote_plus((query or "software").split()[0])
    url = f"https://wellfound.com/api/jobs?tag={tag}&limit={limit}"
    try:
        data = get_json(url)
        rows = data.get("jobs") if isinstance(data, dict) else data
        if not isinstance(rows, list):
            return out
        for j in rows[:limit]:
            if not isinstance(j, dict):
                continue
            out.append(
                base.normalize(
                    source=SOURCE_ID,
                    source_job_id=str(j.get("id") or j.get("slug") or ""),
                    title=j.get("title") or j.get("name") or "",
                    company=j.get("company") or (j.get("startup") or {}).get("name", ""),
                    location=j.get("location") or "Remote",
                    url=j.get("url") or j.get("apply_url") or "",
                    apply_url=j.get("apply_url") or j.get("url") or "",
                    description=j.get("description") or "",
                    tags=j.get("tags") or [],
                    posted_at=j.get("created_at") or "",
                    raw=j,
                )
            )
    except Exception:
        # Wellfound is heavily auth-walled — silently returning empty is acceptable.
        return []
    return out
