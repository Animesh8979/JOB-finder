"""Adzuna — free developer API (needs app_id + app_key). https://developer.adzuna.com/

Adzuna aggregates many boards. It has no strict "remote" flag, so we bias the search
toward remote roles and rely on the app's keyword filter + AI scoring afterwards.
"""
from __future__ import annotations

from typing import Any

from .. import config
from . import base
from .client import get_json

SOURCE_ID = "adzuna"


def fetch(query: str, limit: int, prefs: dict[str, Any]) -> list[dict[str, Any]]:
    app_id, app_key = config.adzuna_creds()
    if not (app_id and app_key):
        return []  # silently skip when not configured

    country = (prefs.get("adzuna_country") or "us").lower()
    url = f"https://api.adzuna.com/v1/api/jobs/{country}/search/1"
    params = {
        "app_id": app_id,
        "app_key": app_key,
        "results_per_page": min(limit, 50),
        "what": (query or "remote"),
        "what_or": "remote",
        "content-type": "application/json",
    }
    data = get_json(url, params=params)
    results = data.get("results", []) if isinstance(data, dict) else []
    out = []
    for j in results[:limit]:
        company = (j.get("company") or {}).get("display_name", "")
        location = (j.get("location") or {}).get("display_name", "Remote")
        out.append(
            base.normalize(
                source=SOURCE_ID,
                source_job_id=str(j.get("id", "")),
                title=j.get("title", ""),
                company=company,
                location=location or "Remote",
                url=j.get("redirect_url", ""),
                apply_url=j.get("redirect_url", ""),
                description=j.get("description", ""),
                tags=[(j.get("category") or {}).get("label", "")],
                salary_min=int(j["salary_min"]) if j.get("salary_min") else None,
                salary_max=int(j["salary_max"]) if j.get("salary_max") else None,
                posted_at=j.get("created", ""),
                raw=j,
            )
        )
    return out
