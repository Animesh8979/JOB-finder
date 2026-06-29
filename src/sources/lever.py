"""Lever API source integration."""
import time
from typing import Any
from . import base, client

def fetch(query: str, limit: int, prefs: dict[str, Any]) -> list[dict[str, Any]]:
    """Fetch jobs from Lever APIs configured in preferences."""
    boards = prefs.get("lever_boards") or []
    if not boards:
        return []
        
    jobs_out = []
    
    for board in boards:
        if jobs_out:
            time.sleep(1.0)
            
        url = f"https://api.lever.co/v0/postings/{board}?mode=json"
        try:
            resp = client.get_json(url)
            if not resp or not isinstance(resp, list):
                continue
                
            for j in resp:
                title = j.get("text", "")
                if query and query.lower() not in title.lower():
                    continue
                    
                loc = j.get("categories", {}).get("location", "")
                remote = "remote" in loc.lower() or "anywhere" in loc.lower()
                
                jobs_out.append(base.normalize(
                    source="lever",
                    source_job_id=str(j.get("id", "")),
                    title=title,
                    company=board.replace("-", " ").title(),
                    location=loc or "Remote",
                    url=j.get("hostedUrl", ""),
                    apply_url=j.get("hostedUrl", ""),
                    description=j.get("descriptionPlain", ""),
                    tags=[j.get("categories", {}).get("team", "")] if j.get("categories", {}).get("team") else [],
                    posted_at=client.iso_from_unix(j.get("createdAt")) if j.get("createdAt") else "",
                    remote=remote,
                    raw=j,
                ))
                if len(jobs_out) >= limit:
                    return jobs_out
                    
        except Exception as e:
            print(f"Error fetching from lever board {board}: {e}")
            
    return jobs_out
