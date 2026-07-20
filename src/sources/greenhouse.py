"""Greenhouse API source integration."""
import time
from typing import Any, Optional
from . import base, client
from .adapter_base import SourceAdapter, CancellationToken

class GreenhouseAdapter(SourceAdapter):
    @property
    def source_id(self) -> str:
        return "greenhouse"

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
    """Fetch jobs from Greenhouse APIs configured in preferences."""
    boards = prefs.get("greenhouse_boards") or []
    if not boards:
        return []
        
    jobs_out = []
    headers = {"Accept": "application/json"}
    
    for board in boards:
        if cancel_token and cancel_token.is_cancelled():
            break

        # Respectful delay between boards
        if jobs_out:
            time.sleep(1.0)
            
        url = f"https://boards-api.greenhouse.io/v1/boards/{board}/jobs"
        try:
            resp = client.get_json(url, headers=headers)
            if not resp or "jobs" not in resp:
                continue
                
            for j in resp["jobs"]:
                if cancel_token and cancel_token.is_cancelled():
                    break
                title = j.get("title", "")
                if query and query.lower() not in title.lower():
                    continue
                    
                loc = j.get("location", {}).get("name", "")
                remote = "remote" in loc.lower() or "anywhere" in loc.lower()
                
                jobs_out.append(base.normalize(
                    source="greenhouse",
                    source_job_id=str(j.get("internal_job_id") or j.get("id", "")),
                    title=title,
                    company=board.replace("-", " ").title(),
                    location=loc or "Remote",
                    url=j.get("absolute_url", ""),
                    apply_url=j.get("absolute_url", ""),
                    description="",  # Full JD can be fetched later
                    tags=[j.get("department", "")] if j.get("department") else [],
                    posted_at=j.get("updated_at", ""),
                    remote=remote,
                    raw=j,
                ))
                if len(jobs_out) >= limit:
                    return jobs_out
                    
        except Exception as e:
            print(f"Error fetching from greenhouse board {board}: {e}")
            
    return jobs_out
