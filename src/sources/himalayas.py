"""Himalayas — free public remote-jobs API (no auth). https://himalayas.app/jobs/api"""
from __future__ import annotations

from typing import Any

from . import base
from .client import get_json, iso_from_unix

SOURCE_ID = "himalayas"
ENDPOINT = "https://himalayas.app/jobs/api"


def _loc(j: dict[str, Any]) -> str:
    restr = j.get("locationRestrictions") or j.get("locations") or []
    if isinstance(restr, list) and restr:
        return ", ".join(map(str, restr))
    return "Remote"


def fetch(query: str, limit: int, prefs: dict[str, Any]) -> list[dict[str, Any]]:
    data = get_json(ENDPOINT, params={"limit": limit})
    jobs = data.get("jobs", []) if isinstance(data, dict) else []
    out = []
    for j in jobs[:limit]:
        link = j.get("applicationLink") or j.get("url") or ""
        out.append(
            base.normalize(
                source=SOURCE_ID,
                source_job_id=str(j.get("guid") or link),
                title=j.get("title", ""),
                company=j.get("companyName") or j.get("company", ""),
                location=_loc(j),
                url=link,
                apply_url=link,
                description=j.get("description") or j.get("excerpt", ""),
                tags=(j.get("categories") or []) + (j.get("seniority") or []),
                salary_min=j.get("minSalary") or None,
                salary_max=j.get("maxSalary") or None,
                posted_at=iso_from_unix(j.get("pubDate")) if j.get("pubDate") else "",
                raw=j,
            )
        )
    return out
