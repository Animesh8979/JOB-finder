"""The Muse — public jobs API (no auth needed for read).

Docs: https://www.themuse.com/developers/api/v2
"""
from __future__ import annotations

from typing import Any
from urllib.parse import urlencode

from . import base
from .client import get_json

SOURCE_ID = "themuse"
ENDPOINT = "https://www.themuse.com/api/public/jobs"


def fetch(query: str, limit: int, prefs: dict[str, Any]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    page = 0
    while len(out) < limit and page < 5:
        params = {"page": page, "category": "Software Engineering", "level": "Mid Level"}
        if query:
            params["q"] = query
        url = f"{ENDPOINT}?{urlencode(params)}"
        try:
            data = get_json(url)
        except Exception:
            break
        rows = (data or {}).get("results") or (data or {}).get("jobs") or []
        if not rows:
            break
        for j in rows:
            if not isinstance(j, dict):
                continue
            refs = j.get("refs") or {}
            apply = refs.get("landing_page") or j.get("apply_url") or ""
            loc_name = ""
            locs = j.get("locations") or []
            if locs and isinstance(locs[0], dict):
                loc_name = locs[0].get("name", "Remote")
            company_name = ""
            comp = j.get("company") or {}
            if isinstance(comp, dict):
                company_name = comp.get("name", "")
            out.append(
                base.normalize(
                    source=SOURCE_ID,
                    source_job_id=str(j.get("id") or ""),
                    title=j.get("name") or "",
                    company=company_name,
                    location=loc_name or "Remote",
                    url=apply,
                    apply_url=apply,
                    description="\n".join(j.get("contents") or []) if isinstance(j.get("contents"), list) else j.get("contents", ""),
                    tags=j.get("categories") or [],
                    posted_at=j.get("publication_date") or "",
                    raw=j,
                )
            )
            if len(out) >= limit:
                break
        page += 1
    return out
