"""Builtin — tech-focused job board with public listings."""
from __future__ import annotations
from typing import Any
from . import base
from .client import get_json

SOURCE_ID = "builtin"
# Builtin exposes a JSON endpoint for job search
ENDPOINT = "https://builtin.com/api/job-board/jobs"

def fetch(query: str, limit: int, prefs: dict[str, Any]) -> list[dict[str, Any]]:
    """Fetch jobs from Builtin's public API."""
    params: dict[str, Any] = {"page": 1, "per_page": min(limit, 50)}
    if query:
        params["search"] = query
    
    try:
        data = get_json(ENDPOINT, params=params)
        jobs = data.get("jobs", []) if isinstance(data, dict) else []
    except Exception as e:
        print(f"Error fetching from builtin: {e}")
        return []
    
    out = []
    for j in jobs[:limit]:
        loc = j.get("location", "Remote")
        out.append(
            base.normalize(
                source=SOURCE_ID,
                source_job_id=str(j.get("id", "")),
                title=j.get("title", ""),
                company=j.get("company_name", ""),
                location=loc,
                url=j.get("url", ""),
                apply_url=j.get("apply_url") or j.get("url", ""),
                description=j.get("description", ""),
                tags=j.get("skills") or [],
                remote="remote" in loc.lower(),
                posted_at=j.get("published_date", ""),
                raw=j,
            )
        )
    return out
