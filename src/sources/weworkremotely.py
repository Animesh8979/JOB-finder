"""WeWorkRemotely RSS feed integration."""
from typing import Any
try:
    import feedparser
except ImportError:
    feedparser = None
from . import base

def fetch(query: str, limit: int, prefs: dict[str, Any]) -> list[dict[str, Any]]:
    """Fetch jobs from WeWorkRemotely RSS feed."""
    if not feedparser:
        print("feedparser not installed. Skipping weworkremotely.")
        return []
        
    url = "https://weworkremotely.com/remote-jobs.rss"
    jobs_out = []
    
    try:
        feed = feedparser.parse(url)
        for entry in feed.entries:
            title_full = entry.get("title", "")
            
            # WWR format: "Company: Job Title"
            company = ""
            title = title_full
            if ": " in title_full:
                parts = title_full.split(": ", 1)
                company = parts[0].strip()
                title = parts[1].strip()
                
            if query and query.lower() not in title.lower():
                continue
                
            # WWR jobs are remote by default
            jobs_out.append(base.normalize(
                source="weworkremotely",
                source_job_id=entry.get("id") or entry.get("link", ""),
                title=title,
                company=company,
                location="Remote",
                url=entry.get("link", ""),
                apply_url=entry.get("link", ""),
                description=entry.get("summary", ""),
                posted_at=entry.get("published", ""),
                remote=True,
                raw={"entry_id": entry.get("id", "")},
            ))
            if len(jobs_out) >= limit:
                break
                
    except Exception as e:
        print(f"Error fetching from weworkremotely: {e}")
        
    return jobs_out
