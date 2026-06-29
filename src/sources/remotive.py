"""Remotive — free public remote-jobs API. https://remotive.com/api/remote-jobs"""
from __future__ import annotations

from typing import Any

from . import base
from .client import get_json

SOURCE_ID = "remotive"
ENDPOINT = "https://remotive.com/api/remote-jobs"


def fetch(query: str, limit: int, prefs: dict[str, Any]) -> list[dict[str, Any]]:
    params: dict[str, Any] = {"limit": limit}
    if query:
        params["search"] = query
    data = get_json(ENDPOINT, params=params)
    jobs = data.get("jobs", []) if isinstance(data, dict) else []
    out = []
    for j in jobs[:limit]:
        out.append(
            base.normalize(
                source=SOURCE_ID,
                source_job_id=str(j.get("id", "")),
                title=j.get("title", ""),
                company=j.get("company_name", ""),
                location=j.get("candidate_required_location") or "Remote",
                url=j.get("url", ""),
                apply_url=j.get("url", ""),
                description=j.get("description", ""),
                tags=(j.get("tags") or []) + ([j["category"]] if j.get("category") else []),
                posted_at=j.get("publication_date", ""),
                raw=j,
            )
        )
    return out
