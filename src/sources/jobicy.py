"""Jobicy — free public remote-jobs API. https://jobicy.com/api/v2/remote-jobs"""
from __future__ import annotations

from typing import Any

from . import base
from .client import get_json

SOURCE_ID = "jobicy"
ENDPOINT = "https://jobicy.com/api/v2/remote-jobs"


def fetch(query: str, limit: int, prefs: dict[str, Any]) -> list[dict[str, Any]]:
    params: dict[str, Any] = {"count": min(limit, 50)}
    if query:
        params["tag"] = query
    data = get_json(ENDPOINT, params=params)
    jobs = data.get("jobs", []) if isinstance(data, dict) else []
    out = []
    for j in jobs[:limit]:
        out.append(
            base.normalize(
                source=SOURCE_ID,
                source_job_id=str(j.get("id", "")),
                title=j.get("jobTitle", ""),
                company=j.get("companyName", ""),
                location=j.get("jobGeo") or "Remote",
                url=j.get("url", ""),
                apply_url=j.get("url", ""),
                description=j.get("jobDescription") or j.get("jobExcerpt", ""),
                tags=(j.get("jobIndustry") or []) + (j.get("jobType") or []),
                salary_min=j.get("annualSalaryMin") or None,
                salary_max=j.get("annualSalaryMax") or None,
                currency=j.get("salaryCurrency", ""),
                posted_at=j.get("pubDate", ""),
                raw=j,
            )
        )
    return out
