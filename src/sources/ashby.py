"""Ashby API source integration — modern ATS with public JSON endpoints."""
import time
from typing import Any, Optional
from . import base, client
from .adapter_base import SourceAdapter, CancellationToken

SOURCE_ID = "ashby"

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
    """Fetch jobs from Ashby job boards configured in preferences."""
    boards = prefs.get("ashby_boards") or []
    if not boards:
        return []
    
    jobs_out = []
    
    for board in boards:
        if cancel_token and cancel_token.is_cancelled():
            break

        if jobs_out:
            time.sleep(1.0)
        
        url = f"https://api.ashbyhq.com/posting-api/job-board/{board}"
        try:
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
                remote = "remote" in loc.lower() or j.get("isRemote", False)
                
                jobs_out.append(base.normalize(
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
                    remote=bool(remote),
                    raw=j,
                ))
                if len(jobs_out) >= limit:
                    return jobs_out
                    
        except Exception as e:
            print(f"Error fetching from ashby board {board}: {e}")
    
    return jobs_out
