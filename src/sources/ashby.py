"""Ashby API source integration — modern ATS with public JSON endpoints."""
from __future__ import annotations

import time
from typing import Any, Optional
from . import base, client
from .adapter_base import SourceAdapter, CancellationToken

SOURCE_ID = "ashby"

# Default high-signal tech organizations hiring on Ashby
DEFAULT_ASHBY_BOARDS = [
    "linear",
    "retool",
    "ramp",
    "perplexity",
    "cursor",
    "anthropic",
    "resend",
    "temporal",
    "vapi",
    "quora",
]


class AshbyAdapter(SourceAdapter):
    @property
    def source_id(self) -> str:
        return SOURCE_ID

    def fetch(
        self,
        query: str,
        limit: int,
        prefs: dict[str, Any],
        cancel_token: Optional[CancellationToken] = None,
    ) -> list[dict[str, Any]]:
        return fetch(query, limit, prefs, cancel_token=cancel_token)


def fetch(
    query: str,
    limit: int,
    prefs: dict[str, Any],
    cancel_token: Optional[CancellationToken] = None,
) -> list[dict[str, Any]]:
    """Fetch jobs directly from Ashby job boards with compensation metadata."""
    configured_boards = prefs.get("ashby_boards") or []
    boards = configured_boards if configured_boards else DEFAULT_ASHBY_BOARDS

    jobs_out = []

    for board in boards:
        if cancel_token and cancel_token.is_cancelled():
            break

        if jobs_out:
            time.sleep(0.5)

        url = f"https://api.ashbyhq.com/posting-api/job-board/{board}"
        try:
            # Ashby POST supports {"includeCompensation": True} for raw salary ranges
            resp = None
            try:
                resp = client.post_json(url, json_data={"includeCompensation": True})
            except Exception:
                resp = client.get_json(url)

            if not resp or "jobs" not in resp:
                continue

            for j in resp["jobs"]:
                if cancel_token and cancel_token.is_cancelled():
                    break
                title = j.get("title", "")
                if query and query.lower() not in title.lower():
                    continue

                loc = j.get("location", "")
                remote = bool(
                    "remote" in (loc or "").lower()
                    or j.get("isRemote", False)
                    or (j.get("workplaceType") or "").lower() == "remote"
                )

                # Parse unredacted compensation brackets if exposed
                comp = j.get("compensation") or {}
                tier = comp.get("compensationTierSummary") or {}
                salary_min = tier.get("minAmount") or comp.get("minAmount")
                salary_max = tier.get("maxAmount") or comp.get("maxAmount")
                currency = tier.get("currency") or comp.get("currency") or "USD"

                normalized_job = base.normalize(
                    source=SOURCE_ID,
                    source_job_id=str(j.get("id", "")),
                    title=title,
                    company=j.get("organizationName", board.replace("-", " ").title()),
                    location=loc or "Remote",
                    url=j.get("jobUrl", ""),
                    apply_url=j.get("applyUrl") or j.get("jobUrl", ""),
                    description=j.get("descriptionPlain") or j.get("descriptionHtml", ""),
                    tags=[j.get("department", "")] if j.get("department") else [],
                    posted_at=j.get("publishedAt", ""),
                    remote=remote,
                    raw=j,
                )

                # Annotate salary directly into the raw payload for downstream processing
                if salary_min:
                    normalized_job["salary_min"] = float(salary_min)
                if salary_max:
                    normalized_job["salary_max"] = float(salary_max)
                if currency:
                    normalized_job["currency"] = str(currency)

                jobs_out.append(normalized_job)
                if len(jobs_out) >= limit:
                    return jobs_out

        except Exception as e:
            # Gracefully continue to next board if a slug fails
            continue

    return jobs_out
